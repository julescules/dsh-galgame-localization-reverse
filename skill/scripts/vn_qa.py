#!/usr/bin/env python3
"""Dependency-free translation preflight for visual-novel JSON/JSONL records."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "vn-translation-qa/v2"
PLACEHOLDER_PATTERNS = [
    r"\{\{[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2})?\}\}",
    r"%[0-9]+\$[-+ #0]*[0-9]*(?:\.[0-9]+)?[diouxXeEfgGcspn%]",
    r"%[-+ #0]*[0-9*]*(?:\.[0-9*]+)?[diouxXeEfgGcspn%]",
    r"\{/?[A-Za-z_][^{}\n]{0,80}\}",
    r"\{[0-9]+\}",
    r"\[[^\[\]\n]{0,80}\]",
    r"\\[nNtr\\]",
]
_PH_RE = re.compile("|".join(f"(?:{item})" for item in PLACEHOLDER_PATTERNS))
_JAPANESE_RE = re.compile(r"[\u3040-\u30ff]")
_ZERO_WIDTH_RE = re.compile("[\u200b\u200c\u200d\ufeff]")


def extract_placeholders(text: str) -> list[str]:
    return [match.group(0) for match in _PH_RE.finditer(text)]


def strip_placeholders(text: str) -> str:
    return _PH_RE.sub("", text)


def verify_placeholders(src: str, tgt: str, *, allow_added: bool = False, allow_reordered: bool = False) -> dict[str, Any]:
    src_list = extract_placeholders(src)
    tgt_list = extract_placeholders(tgt)
    src_counter, tgt_counter = Counter(src_list), Counter(tgt_list)
    missing = list((src_counter - tgt_counter).elements())
    added = list((tgt_counter - src_counter).elements())
    reordered = src_counter == tgt_counter and src_list != tgt_list
    ok = not missing and (allow_added or not added) and (allow_reordered or not reordered)
    return {
        "ok": ok,
        "missing": missing,
        "added": added,
        "reordered": reordered,
        "source_placeholders": src_list,
        "target_placeholders": tgt_list,
    }


def check_encoding(text: str, encoding: str) -> dict[str, Any]:
    body = strip_placeholders(text)
    try:
        body.encode(encoding)
        return {"ok": True, "encoding": encoding, "unencodable": []}
    except UnicodeEncodeError:
        bad: Counter[str] = Counter()
        for character in body:
            try:
                character.encode(encoding)
            except UnicodeEncodeError:
                bad[character] += 1
        return {
            "ok": False,
            "encoding": encoding,
            "unencodable": [
                {"char": character, "codepoint": f"U+{ord(character):04X}", "count": count}
                for character, count in bad.most_common()
            ],
        }


def _records_from_json(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("records", "items", "data", "translations"):
            if isinstance(value.get(key), list):
                return [item for item in value[key] if isinstance(item, dict)]
        if all(isinstance(item, dict) for item in value.values()):
            return [dict(item, _record_key=key) for key, item in value.items()]
    raise ValueError("JSON input must be a record list or an object containing records/items/data/translations")


def load_records(path_value: str) -> list[dict[str, Any]]:
    path = Path(path_value)
    if path.suffix.casefold() in {".jsonl", ".ndjson"}:
        records = []
        with path.open("r", encoding="utf-8-sig") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"line {line_number} is not a JSON object")
                records.append(value)
        return records
    with path.open("r", encoding="utf-8-sig") as handle:
        return _records_from_json(json.load(handle))


def _string(value: Any) -> str:
    return value if isinstance(value, str) else ""


def adapt_record(record: dict[str, Any], index: int, *, input_format: str, source_field: str, target_field: str, id_field: str) -> tuple[str, str, Any]:
    selected = input_format
    if selected == "auto":
        selected = "galtransl" if "pre_jp" in record else "generic"
    if selected == "galtransl":
        src = _string(record.get("pre_jp") or record.get("post_jp") or record.get(source_field))
        tgt = _string(record.get("proofread_zh") or record.get("pre_zh") or record.get("post_zh") or record.get(target_field))
        record_id = record.get(id_field, record.get("index", record.get("key", record.get("_record_key", index))))
        return src, tgt, record_id
    return _string(record.get(source_field)), _string(record.get(target_field)), record.get(id_field, record.get("_record_key", index))


def check_records(
    records: Iterable[dict[str, Any]],
    *,
    encoding: str | None = None,
    require_complete: bool = False,
    reject_japanese: bool = False,
    require_translated: bool = False,
    allow_added: bool = False,
    allow_reordered: bool = False,
    input_format: str = "auto",
    source_field: str = "source",
    target_field: str = "target",
    id_field: str = "segment_id",
) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    total = 0
    completed = 0
    for index, record in enumerate(records, 1):
        total += 1
        src, tgt, record_id = adapt_record(record, index, input_format=input_format, source_field=source_field, target_field=target_field, id_field=id_field)
        issues: list[dict[str, Any]] = []
        advisory: list[dict[str, Any]] = []
        if not tgt.strip():
            counts["empty_translation"] += 1
            item = {"code": "empty-translation", "message": "translation is empty"}
            (issues if require_complete else advisory).append(item)
        else:
            completed += 1
            placeholders = verify_placeholders(src, tgt, allow_added=allow_added, allow_reordered=allow_reordered)
            if placeholders["missing"]:
                issues.append({"code": "control-token-missing", "message": "source control tokens are missing", "tokens": placeholders["missing"]})
                counts["control_token_missing"] += 1
            if placeholders["added"] and not allow_added:
                issues.append({"code": "control-token-added", "message": "target introduces control tokens", "tokens": placeholders["added"]})
                counts["control_token_added"] += 1
            if placeholders["reordered"] and not allow_reordered:
                issues.append({"code": "control-token-reordered", "message": "control-token order changed", "tokens": placeholders["target_placeholders"]})
                counts["control_token_reordered"] += 1
            if encoding:
                encoding_result = check_encoding(tgt, encoding)
                if not encoding_result["ok"]:
                    issues.append({"code": "encoding", "message": f"target is not encodable as {encoding}", "detail": encoding_result["unencodable"]})
                    counts["encoding"] += 1
            if src.strip() and src.strip() == tgt.strip():
                counts["unchanged_source"] += 1
                item = {"code": "unchanged-source", "message": "target is identical to source"}
                (issues if require_translated else advisory).append(item)
            residual = sorted(set(_JAPANESE_RE.findall(strip_placeholders(tgt))))
            if residual:
                counts["residual_japanese"] += 1
                item = {"code": "residual-japanese", "message": "target contains hiragana or katakana", "characters": residual[:40]}
                (issues if reject_japanese else advisory).append(item)
            zero_width = sorted(set(_ZERO_WIDTH_RE.findall(tgt)))
            if zero_width:
                issues.append({"code": "zero-width-character", "message": "target contains invisible zero-width characters", "codepoints": [f"U+{ord(item):04X}" for item in zero_width]})
                counts["zero_width_character"] += 1
        if issues:
            failures.append({"segment_id": record_id, "issues": issues})
        if advisory:
            warnings.append({"segment_id": record_id, "issues": advisory})
    return {
        "schema": SCHEMA_VERSION,
        "gate": "FAIL" if failures else "PASS",
        "total_records": total,
        "completed": completed,
        "pending": total - completed,
        "failed_records": len(failures),
        "warning_records": len(warnings),
        "counts": dict(sorted(counts.items())),
        "policy": {
            "strict_control_tokens": True,
            "allow_added": allow_added,
            "allow_reordered": allow_reordered,
            "require_complete": require_complete,
            "reject_japanese": reject_japanese,
            "require_translated": require_translated,
            "encoding": encoding,
        },
        "failures": failures,
        "warnings": warnings,
    }


def check_jsonl(path: str, encoding: str | None, **options: Any) -> dict[str, Any]:
    """Compatibility entry point; now accepts JSON as well as JSONL."""
    return check_records(load_records(path), encoding=encoding, **options)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# VN translation QA",
        "",
        f"- Gate: **{report['gate']}**",
        f"- Records: **{report['total_records']}**",
        f"- Completed: **{report['completed']}**",
        f"- Pending: **{report['pending']}**",
        f"- Failed records: **{report['failed_records']}**",
        f"- Warning records: **{report['warning_records']}**",
        "",
    ]
    if report["failures"]:
        lines.extend(["## Blockers", ""])
        for failure in report["failures"]:
            for issue in failure["issues"]:
                detail = issue.get("tokens") or issue.get("characters") or issue.get("codepoints") or ""
                lines.append(f"- `{failure['segment_id']}` **{issue['code']}** — {issue['message']}{f' — `{detail}`' if detail else ''}")
        lines.append("")
    if report["warnings"]:
        lines.extend(["## Review warnings", ""])
        for warning in report["warnings"]:
            for issue in warning["issues"]:
                lines.append(f"- `{warning['segment_id']}` **{issue['code']}** — {issue['message']}")
        lines.append("")
    lines.extend(["## Policy", "", "```json", json.dumps(report["policy"], ensure_ascii=False, indent=2), "```", ""])
    return "\n".join(lines)


def _write(path_value: str, text: str) -> None:
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _selftest() -> int:
    assert extract_placeholders(r"hi %s %03d {name} [ruby] \n {{FF}} %1$s") == ["%s", "%03d", "{name}", "[ruby]", r"\n", "{{FF}}", "%1$s"]
    missing = verify_placeholders(r"hello %s\n", "你好")
    assert not missing["ok"] and "%s" in missing["missing"] and r"\n" in missing["missing"]
    added = verify_placeholders("%s", "%s %d")
    assert not added["ok"] and added["added"] == ["%d"]
    reordered = verify_placeholders("%s %d", "%d %s")
    assert not reordered["ok"] and reordered["reordered"]
    assert verify_placeholders("%s %d", "%d %s", allow_reordered=True)["ok"]
    assert check_encoding("正常文本 %s", "gbk")["ok"]
    assert not check_encoding("héllo 😀 %s", "gbk")["ok"]
    report = check_records([
        {"segment_id": "ok", "source": "Hello %s", "target": "你好 %s"},
        {"segment_id": "added", "source": "Hello", "target": "你好 [wait]"},
        {"segment_id": "empty", "source": "Next", "target": ""},
    ], require_complete=True)
    assert report["gate"] == "FAIL" and report["pending"] == 1 and report["failed_records"] == 2, report
    gal = check_records([{"index": 7, "pre_jp": "名前 %s", "proofread_zh": "名字 %s"}], input_format="galtransl")
    assert gal["gate"] == "PASS", gal
    print("selftest OK")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Strict visual-novel translation QA.")
    parser.add_argument("--selftest", action="store_true")
    sub = parser.add_subparsers(dest="command")
    placeholders = sub.add_parser("placeholders")
    placeholders.add_argument("--text", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--src", required=True)
    verify.add_argument("--tgt", required=True)
    for name in ("check", "check-jsonl"):
        check = sub.add_parser(name, help="check generic JSON/JSONL or GalTransl cache records")
        check.add_argument("path")
        check.add_argument("--encoding")
        check.add_argument("--format", choices=("auto", "generic", "galtransl"), default="auto")
        check.add_argument("--source-field", default="source")
        check.add_argument("--target-field", default="target")
        check.add_argument("--id-field", default="segment_id")
        check.add_argument("--require-complete", action="store_true")
        check.add_argument("--reject-japanese", action="store_true")
        check.add_argument("--require-translated", action="store_true")
        check.add_argument("--allow-added", action="store_true")
        check.add_argument("--allow-reordered", action="store_true")
        check.add_argument("--report", help="write JSON report")
        check.add_argument("--markdown", help="write Markdown report")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    if args.command == "placeholders":
        print("\n".join(extract_placeholders(args.text)))
        return 0
    if args.command == "verify":
        result = verify_placeholders(args.src, args.tgt)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1
    if args.command in {"check", "check-jsonl"}:
        report = check_jsonl(
            args.path,
            args.encoding,
            require_complete=args.require_complete,
            reject_japanese=args.reject_japanese,
            require_translated=args.require_translated,
            allow_added=args.allow_added,
            allow_reordered=args.allow_reordered,
            input_format=args.format,
            source_field=args.source_field,
            target_field=args.target_field,
            id_field=args.id_field,
        )
        if args.report:
            _write(args.report, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        if args.markdown:
            _write(args.markdown, render_markdown(report))
        print(f"gate={report['gate']} records={report['total_records']} completed={report['completed']} pending={report['pending']} failures={report['failed_records']} warnings={report['warning_records']}")
        return 0 if report["gate"] == "PASS" else 1
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
