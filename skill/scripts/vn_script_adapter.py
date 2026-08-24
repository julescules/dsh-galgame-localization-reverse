#!/usr/bin/env python3
"""Lossless text-script extraction and guarded apply for common VN engines.

Supported adapters intentionally cover source scripts only: KiriKiri .ks,
Ren'Py .rpy, and NScripter/ONScripter 0.txt-style text. Archives and compiled
scripts remain outside this tool's contract.
"""
from __future__ import annotations

import argparse
import codecs
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "vn-script-adapter/v1"
ENGINE_EXTENSIONS = {"kirikiri": {".ks"}, "renpy": {".rpy"}, "nscripter": {".txt"}}
JP_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
RENPY_QUOTED_RE = re.compile(r'^(?P<prefix>\s*(?:(?:[A-Za-z_][\w.]*)\s+|old\s+|new\s+)?)"(?P<text>(?:\\.|[^"\\])*)"(?P<suffix>\s*(?:#.*)?)$')


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _encoding(data: bytes, requested: str) -> tuple[str, bytes, str]:
    if requested != "auto":
        encoding = requested
        bom = ""
        payload = data
        if encoding == "utf-8-sig" and data.startswith(codecs.BOM_UTF8):
            payload, bom = data[len(codecs.BOM_UTF8):], "utf-8"
        return encoding, payload, bom
    if data.startswith(codecs.BOM_UTF8):
        return "utf-8-sig", data[len(codecs.BOM_UTF8):], "utf-8"
    if data.startswith(codecs.BOM_UTF16_LE):
        return "utf-16-le", data[len(codecs.BOM_UTF16_LE):], "utf-16-le"
    if data.startswith(codecs.BOM_UTF16_BE):
        return "utf-16-be", data[len(codecs.BOM_UTF16_BE):], "utf-16-be"
    for candidate in ("utf-8", "cp932", "gbk"):
        try:
            data.decode(candidate, errors="strict")
            return candidate, data, ""
        except UnicodeError:
            continue
    raise UnicodeError("script is not strictly decodable as utf-8, cp932, or gbk")


def _decode(path: Path, requested: str) -> tuple[str, str, str]:
    data = path.read_bytes()
    encoding, payload, bom = _encoding(data, requested)
    codec = "utf-8" if encoding == "utf-8-sig" else encoding
    return payload.decode(codec, errors="strict"), encoding, bom


def _encode(text: str, encoding: str, bom: str) -> bytes:
    codec = "utf-8" if encoding == "utf-8-sig" else encoding
    payload = text.encode(codec, errors="strict")
    if bom == "utf-8":
        return codecs.BOM_UTF8 + payload
    if bom == "utf-16-le":
        return codecs.BOM_UTF16_LE + payload
    if bom == "utf-16-be":
        return codecs.BOM_UTF16_BE + payload
    return payload


def _line_body(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith(("\r", "\n")):
        return line[:-1], line[-1]
    return line, ""


def _has_unescaped_quote(text: str) -> bool:
    for index, character in enumerate(text):
        if character != '"':
            continue
        backslashes = 0
        cursor = index - 1
        while cursor >= 0 and text[cursor] == "\\":
            backslashes += 1
            cursor -= 1
        if backslashes % 2 == 0:
            return True
    return False


def _segment(engine: str, body: str) -> tuple[int, int] | None:
    stripped = body.strip()
    if not stripped:
        return None
    if engine == "renpy":
        match = RENPY_QUOTED_RE.match(body)
        return match.span("text") if match else None
    if engine == "kirikiri":
        if stripped.startswith((";", "*", "@")) or (stripped.startswith("[") and stripped.endswith("]")):
            return None
        start = len(body) - len(body.lstrip())
        end = len(body.rstrip())
        return (start, end) if end > start else None
    if engine == "nscripter":
        if stripped.startswith((";", "*", "@")) or not JP_RE.search(stripped):
            return None
        start = len(body) - len(body.lstrip())
        end = len(body.rstrip())
        return (start, end) if end > start else None
    raise ValueError(f"unsupported engine: {engine}")


def _files(root: Path, engine: str) -> list[Path]:
    if root.is_file():
        return [root]
    extensions = ENGINE_EXTENSIONS[engine]
    result = []
    for candidate in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if candidate.is_symlink() or not candidate.is_file() or candidate.suffix.casefold() not in extensions:
            continue
        if engine == "nscripter" and candidate.name.casefold() != "0.txt":
            continue
        result.append(candidate)
    return result


def extract_records(root: Path, engine: str, encoding: str = "auto") -> list[dict[str, Any]]:
    root = root.resolve(strict=True)
    base = root.parent if root.is_file() else root
    records: list[dict[str, Any]] = []
    for path in _files(root, engine):
        text, selected_encoding, bom = _decode(path, encoding)
        relative = path.relative_to(base).as_posix()
        for line_number, line in enumerate(text.splitlines(keepends=True), 1):
            body, newline = _line_body(line)
            span = _segment(engine, body)
            if not span:
                continue
            start, end = span
            source = body[start:end]
            records.append({
                "schema": SCHEMA_VERSION,
                "segment_id": f"{relative}:{line_number}",
                "engine": engine,
                "path": relative,
                "line": line_number,
                "source": source,
                "target": "",
                "source_sha256": _sha(source),
                "line_sha256": _sha(body),
                "prefix": body[:start],
                "suffix": body[end:],
                "encoding": selected_encoding,
                "bom": bom,
                "newline": newline.replace("\r", "\\r").replace("\n", "\\n"),
            })
    return records


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"translation line {line_number} is not an object")
            records.append(value)
    return records


def apply_records(source_root: Path, translations: Iterable[dict[str, Any]], output_root: Path, *, allow_empty: bool = False) -> dict[str, Any]:
    source_root = source_root.resolve(strict=True)
    output_root = output_root.resolve(strict=False)
    if output_root == source_root or source_root in output_root.parents:
        raise ValueError("output root must be outside the immutable source tree")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in translations:
        relative = str(record.get("path", ""))
        candidate = Path(relative)
        if not relative or candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(f"unsafe translation path: {relative!r}")
        grouped.setdefault(relative, []).append(record)
    written = []
    applied = 0
    for relative, records in sorted(grouped.items()):
        source = (source_root / Path(relative)).resolve(strict=True)
        if source_root not in source.parents or source.is_symlink() or not source.is_file():
            raise ValueError(f"source escaped root or is not a regular file: {source}")
        encodings = {str(item.get("encoding", "")) for item in records}
        if len(encodings) != 1:
            raise ValueError(f"mixed or missing encodings for {relative}")
        text, detected, bom = _decode(source, encodings.pop())
        if detected != records[0].get("encoding") or bom != records[0].get("bom", ""):
            raise ValueError(f"encoding or BOM drift for {relative}")
        lines = text.splitlines(keepends=True)
        for record in sorted(records, key=lambda item: int(item["line"]), reverse=True):
            index = int(record["line"]) - 1
            if index < 0 or index >= len(lines):
                raise ValueError(f"line no longer exists: {record.get('segment_id')}")
            body, newline = _line_body(lines[index])
            source_text = str(record.get("source", ""))
            expected = str(record.get("prefix", "")) + source_text + str(record.get("suffix", ""))
            if _sha(source_text) != record.get("source_sha256") or _sha(body) != record.get("line_sha256") or body != expected:
                raise ValueError(f"source drift: {record.get('segment_id')}")
            target = record.get("target")
            if not isinstance(target, str) or (not target and not allow_empty):
                raise ValueError(f"translation is empty: {record.get('segment_id')}")
            if "\r" in target or "\n" in target:
                raise ValueError(f"multiline target is unsupported by the v1 line adapter: {record.get('segment_id')}")
            if record.get("engine") == "renpy" and _has_unescaped_quote(target):
                raise ValueError(f"Ren'Py target contains an unescaped quote: {record.get('segment_id')}")
            lines[index] = str(record.get("prefix", "")) + target + str(record.get("suffix", "")) + newline
            applied += 1
        destination = (output_root / Path(relative)).resolve(strict=False)
        if output_root != destination and output_root not in destination.parents:
            raise ValueError(f"output escaped root: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(_encode("".join(lines), detected, bom))
        written.append(relative)
    return {"schema": SCHEMA_VERSION, "status": "APPLIED", "segments": applied, "files": written, "source_files_changed": 0}


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _outside(path: Path, root: Path) -> None:
    resolved = path.resolve(strict=False)
    root = root.resolve(strict=True)
    if resolved == root or root in resolved.parents:
        raise ValueError("generated output must be outside the source tree")


def _selftest() -> int:
    assert _segment("kirikiri", "  こんにちは[wait]") == (2, 13)
    assert _segment("kirikiri", "@bg storage=room") is None
    assert _segment("renpy", '    e "Hello {name}\\n"') == (7, 21)
    assert _segment("nscripter", "彼女「こんにちは」") == (0, 9)
    assert _segment("nscripter", "bg room.jpg") is None
    assert _has_unescaped_quote('say \\"hello\\"') is False
    assert _has_unescaped_quote('say "hello"') is True
    with tempfile.TemporaryDirectory(prefix="vn-script-adapter-") as temp_value:
        temp = Path(temp_value)
        source = temp / "source"
        output = temp / "output"
        source.mkdir()
        original = codecs.BOM_UTF8 + "*start\r\nこんにちは[wait]\r\n".encode("utf-8")
        (source / "scene.ks").write_bytes(original)
        records = extract_records(source, "kirikiri")
        assert len(records) == 1 and records[0]["encoding"] == "utf-8-sig" and records[0]["newline"] == "\\r\\n", records
        records[0]["target"] = records[0]["source"]
        result = apply_records(source, records, output)
        assert result["source_files_changed"] == 0 and (output / "scene.ks").read_bytes() == original, result
        assert (source / "scene.ks").read_bytes() == original
    print("selftest OK")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Lossless source-script adapter for KiriKiri, Ren'Py, and NScripter.")
    parser.add_argument("--selftest", action="store_true")
    sub = parser.add_subparsers(dest="command")
    extract = sub.add_parser("extract")
    extract.add_argument("source")
    extract.add_argument("--engine", choices=tuple(ENGINE_EXTENSIONS), required=True)
    extract.add_argument("--encoding", default="auto")
    extract.add_argument("--output", required=True)
    apply = sub.add_parser("apply")
    apply.add_argument("source_root")
    apply.add_argument("translations")
    apply.add_argument("--output-root", required=True)
    apply.add_argument("--allow-empty", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    if args.command == "extract":
        source = Path(args.source)
        output = Path(args.output)
        _outside(output, source)
        records = extract_records(source, args.engine, args.encoding)
        _write_jsonl(output, records)
        print(f"schema={SCHEMA_VERSION} engine={args.engine} records={len(records)} source_files_changed=0")
        return 0
    if args.command == "apply":
        report = apply_records(Path(args.source_root), _load_jsonl(Path(args.translations)), Path(args.output_root), allow_empty=args.allow_empty)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
