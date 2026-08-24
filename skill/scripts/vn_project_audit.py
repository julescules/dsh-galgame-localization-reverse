#!/usr/bin/env python3
"""Read-only visual-novel project inventory and engine-evidence report.

The scanner never opens archives and never changes the input tree.  It records
bounded metadata and small encoding probes, then writes JSON/Markdown only when
the caller explicitly supplies report paths.
"""
from __future__ import annotations

import argparse
import codecs
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "vn-project-audit/v2"
SCRIPT_EXTENSIONS = {".ks", ".tjs", ".rpy", ".rpyc", ".txt", ".scn", ".mes", ".mjo", ".ss", ".json"}
ARCHIVE_EXTENSIONS = {".xp3", ".nsa", ".ns2", ".sar", ".arc", ".pfs", ".pac", ".dat", ".cpk"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".g00", ".gxt", ".akb", ".cbg"}
FONT_EXTENSIONS = {".ttf", ".otf", ".ttc", ".woff", ".woff2"}
EXECUTABLE_EXTENSIONS = {".exe", ".dll"}


@dataclass(frozen=True)
class EngineRule:
    name: str
    reference: str
    tool_hint: str
    signals: tuple[tuple[str, tuple[str, ...]], ...]


ENGINE_RULES = (
    EngineRule("KiriKiri", "references/engine-and-tooling.md", "GARbro or VNTextPatch after a zero-mutation proof", (
        ("startup", ("startup.tjs", "system/startup.tjs")),
        ("scenario", ("*.ks", "scenario/*.ks")),
        ("archive", ("*.xp3",)),
    )),
    EngineRule("Ren'Py", "references/engine-and-tooling.md", "Ren'Py launcher and generated tl/ files", (
        ("project", ("game/script.rpy", "game/options.rpy", "renpy/common/*")),
        ("script", ("*.rpy", "game/*.rpy", "game/tl/*")),
        ("runtime", ("renpy/*.py", "lib/*/python*")),
    )),
    EngineRule("NScripter/ONScripter", "references/engine-and-tooling.md", "ONScripter tools or VNTextPatch", (
        ("entry", ("0.txt", "nscript.dat")),
        ("archive", ("arc.sar", "*.nsa", "*.ns2")),
        ("runtime", ("onscripter*.exe", "nscripter*.exe")),
    )),
    EngineRule("RealLive/AVG2000", "references/reallive-seen-g00-save-safe-localization.md", "rlBabel/VNTextPatch only after exact-version validation", (
        ("runtime", ("reallive.exe",)),
        ("config", ("gameexe.ini", "seen.txt")),
        ("assets", ("g00/*", "*.g00")),
    )),
    EngineRule("Unity", "references/engine-and-tooling.md", "AssetRipper/UABEA with a title-specific round trip", (
        ("player", ("unityplayer.dll",)),
        ("data", ("*_data/globalgamemanagers", "*_data/resources.assets", "*_data/sharedassets*")),
        ("managed", ("*_data/managed/assembly-csharp.dll",)),
    )),
    EngineRule("BGI/Ethornell", "references/bgi-ethornell-locale-ui-cbg.md", "GARbro or proven BURIKO tooling", (
        ("runtime", ("bgiframe*.dll", "bgi*.exe")),
        ("archive", ("*.arc",)),
        ("script", ("*.scn", "*.s*")),
    )),
    EngineRule("SiglusEngine", "references/engine-and-tooling.md", "SiglusExtract or title-specific tooling", (
        ("runtime", ("siglusengine.exe",)),
        ("config", ("gameexe.ini",)),
        ("archive", ("*.pck", "*.dat")),
    )),
    EngineRule("Majiro", "references/engine-and-tooling.md", "majiro tools after bytecode round-trip validation", (
        ("runtime", ("majiro*.exe",)),
        ("archive", ("*.arc",)),
        ("script", ("*.mjo",)),
    )),
    EngineRule("TyranoScript", "references/engine-and-tooling.md", "TyranoScript project tools", (
        ("project", ("tyrano/tyrano.base.js", "data/system/config.tjs")),
        ("scenario", ("data/scenario/*.ks",)),
        ("runtime", ("nw.dll", "package.json")),
    )),
)

ADAPTER_ENGINES = {
    "KiriKiri": ("kirikiri", "*.ks"),
    "Ren'Py": ("renpy", "*.rpy"),
    "NScripter/ONScripter": ("nscripter", "0.txt"),
}


def _norm(value: str) -> str:
    return value.replace("\\", "/").strip("/").casefold()


def _glob_match(path_value: str, pattern: str) -> bool:
    from fnmatch import fnmatchcase
    path_norm = _norm(path_value)
    pattern_norm = _norm(pattern)
    return fnmatchcase(path_norm, pattern_norm) or fnmatchcase(path_norm.rsplit("/", 1)[-1], pattern_norm)


def detect_engines(relative_paths: Iterable[str]) -> list[dict[str, Any]]:
    paths = sorted({_norm(item) for item in relative_paths if item})
    results: list[dict[str, Any]] = []
    for rule in ENGINE_RULES:
        evidence: list[dict[str, str]] = []
        groups: set[str] = set()
        for group, patterns in rule.signals:
            matches = sorted({path_value for path_value in paths for pattern in patterns if _glob_match(path_value, pattern)})
            if not matches:
                continue
            groups.add(group)
            for match in matches[:5]:
                evidence.append({"signal_group": group, "path": match})
        if not groups:
            continue
        count = len(groups)
        confidence = min(0.95, 0.40 + 0.18 * count)
        results.append({
            "engine": rule.name,
            "classification": "candidate" if count >= 2 else "weak-candidate",
            "confidence": round(confidence, 2),
            "signal_groups": sorted(groups),
            "evidence": evidence,
            "reference": rule.reference,
            "tool_hint": rule.tool_hint,
        })
    return sorted(results, key=lambda item: (-item["confidence"], item["engine"]))


def inventory_tree(root: Path, max_files: int) -> tuple[list[dict[str, Any]], list[str]]:
    entries: list[dict[str, Any]] = []
    warnings: list[str] = []
    root_resolved = root.resolve(strict=True)
    for current, dirs, files in os.walk(root_resolved, followlinks=False):
        current_path = Path(current)
        kept_dirs = []
        for dirname in sorted(dirs, key=str.casefold):
            candidate = current_path / dirname
            if candidate.is_symlink():
                warnings.append(f"directory link not traversed: {candidate.relative_to(root_resolved).as_posix()}")
            else:
                kept_dirs.append(dirname)
        dirs[:] = kept_dirs
        for filename in sorted(files, key=str.casefold):
            candidate = current_path / filename
            if len(entries) >= max_files:
                warnings.append(f"file inventory truncated at max_files={max_files}")
                return entries, warnings
            try:
                stat = candidate.stat(follow_symlinks=False)
            except OSError as exc:
                warnings.append(f"metadata unreadable: {candidate.relative_to(root_resolved).as_posix()}: {exc.__class__.__name__}")
                continue
            entries.append({
                "path": candidate.relative_to(root_resolved).as_posix(),
                "size": stat.st_size,
                "extension": candidate.suffix.casefold(),
                "is_link": candidate.is_symlink(),
            })
    return entries, warnings


def _category(extension: str) -> str | None:
    if extension in SCRIPT_EXTENSIONS:
        return "scripts"
    if extension in ARCHIVE_EXTENSIONS:
        return "archives"
    if extension in IMAGE_EXTENSIONS:
        return "images"
    if extension in FONT_EXTENSIONS:
        return "fonts"
    if extension in EXECUTABLE_EXTENSIONS:
        return "executables"
    return None


def summarize_inventory(entries: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[str]] = {key: [] for key in ("scripts", "archives", "images", "fonts", "executables")}
    extensions: Counter[str] = Counter()
    for entry in entries:
        extension = entry["extension"] or "(none)"
        extensions[extension] += 1
        category = _category(entry["extension"])
        if category:
            grouped[category].append(entry["path"])
    return {
        "files": len(entries),
        "bytes": sum(entry["size"] for entry in entries),
        "extensions": [{"extension": ext, "count": count} for ext, count in extensions.most_common(20)],
        "categories": {key: {"count": len(values), "examples": values[:12]} for key, values in grouped.items()},
    }


def probe_encodings(root: Path, entries: list[dict[str, Any]], max_samples: int, sample_bytes: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for entry in entries:
        if len(results) >= max_samples:
            break
        if entry["extension"] not in SCRIPT_EXTENSIONS or entry["is_link"] or entry["size"] > 8 * 1024 * 1024:
            continue
        target = root / Path(entry["path"])
        try:
            with target.open("rb") as handle:
                data = handle.read(sample_bytes)
        except OSError as exc:
            results.append({"path": entry["path"], "error": exc.__class__.__name__})
            continue
        bom = "none"
        if data.startswith(codecs.BOM_UTF8):
            bom = "utf-8-sig"
        elif data.startswith(codecs.BOM_UTF16_LE):
            bom = "utf-16-le"
        elif data.startswith(codecs.BOM_UTF16_BE):
            bom = "utf-16-be"
        decodable = []
        for encoding in ("utf-8", "cp932", "gbk", "utf-16-le"):
            try:
                data.decode(encoding, errors="strict")
                decodable.append(encoding)
            except UnicodeError:
                pass
        results.append({"path": entry["path"], "sampled_bytes": len(data), "bom": bom, "decodable_as": decodable})
    return results


def build_report(root: Path, *, max_files: int = 20000, max_encoding_samples: int = 20, sample_bytes: int = 65536) -> dict[str, Any]:
    if max_files < 1 or max_encoding_samples < 0 or sample_bytes < 1:
        raise ValueError("scan bounds must be positive")
    root_resolved = root.resolve(strict=True)
    if not root_resolved.is_dir():
        raise NotADirectoryError(str(root))
    entries, warnings = inventory_tree(root_resolved, max_files)
    engines = detect_engines(entry["path"] for entry in entries)
    top = engines[0] if engines else None
    if top and top["classification"] == "candidate":
        next_step = f"Treat {top['engine']} as a candidate and prove a zero-mutation extraction/rebuild before localization."
    elif top:
        next_step = "Evidence is insufficient: collect a second independent signal group before choosing an extractor."
    else:
        next_step = "No supported engine candidate was found; inspect executable imports, archive magic, and runtime ownership manually."
    report = {
        "schema": SCHEMA_VERSION,
        "mode": "read-only",
        "root": str(root_resolved),
        "input_files_changed": 0,
        "inventory": summarize_inventory(entries),
        "engine_candidates": engines,
        "encoding_probes": probe_encodings(root_resolved, entries, max_encoding_samples, sample_bytes),
        "warnings": warnings,
        "next_step": next_step,
        "limitations": [
            "Static paths are routing evidence, not proof of runtime engine ownership.",
            "Encoding probes only report strict decodability of bounded byte samples.",
            "Archives are not opened and game resources are not uploaded or modified.",
        ],
    }
    report["localization_plan"] = build_localization_plan(report)
    return report


def build_localization_plan(report: dict[str, Any]) -> dict[str, Any]:
    candidates = report.get("engine_candidates", [])
    top = candidates[0] if candidates else None
    engine = top["engine"] if top else "Unknown"
    proven = bool(top and top["classification"] == "candidate")
    commands = [
        "python -X utf8 skill/scripts/vn_project_audit.py scan <GAME_DIR> --json <REPORT_DIR>/audit.json --markdown <REPORT_DIR>/audit.md",
    ]
    route = "Collect a second independent engine signal before extraction."
    if engine in ADAPTER_ENGINES:
        adapter, pattern = ADAPTER_ENGINES[engine]
        route = f"Use the lossless {engine} source-script adapter for {pattern}; archives and compiled scripts stay out of scope."
        commands.extend([
            f"python -X utf8 skill/scripts/vn_script_adapter.py extract <GAME_DIR> --engine {adapter} --output <PROJECT_DIR>/translations.jsonl",
            "python -X utf8 skill/scripts/vn_qa.py check <PROJECT_DIR>/translations.jsonl --require-complete --glossary <PROJECT_DIR>/glossary.json --report <REPORT_DIR>/translation-qa.json",
            "python -X utf8 skill/scripts/vn_script_adapter.py apply <GAME_DIR> <PROJECT_DIR>/translations.jsonl --output-root <PROJECT_DIR>/rebuilt",
        ])
    elif top:
        route = top["tool_hint"]
    return {
        "schema": "vn-localization-plan/v1",
        "mode": "advisory-read-only",
        "engine": engine,
        "evidence_status": "candidate-with-two-signal-groups" if proven else "insufficient-static-evidence",
        "route": route,
        "commands": commands,
        "release_gates": [
            "zero-mutation extraction/rebuild proof",
            "strict control-token and terminology QA",
            "target-encoding and font/UI capacity check",
            "runtime UI plus save/load/audio smoke test",
            "hash-bound install and rollback verification",
        ],
        "risks": [
            "Static engine evidence is not runtime ownership proof.",
            "Compiled or encrypted scripts need an engine-specific round trip before translation.",
            "Any source, font, image, or runtime change invalidates downstream release evidence.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Galgame project audit",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Mode: **{report['mode']}**",
        f"- Root: `{report['root']}`",
        f"- Files inventoried: **{report['inventory']['files']}**",
        f"- Input files changed: **{report['input_files_changed']}**",
        "",
        "## Engine evidence",
        "",
    ]
    candidates = report["engine_candidates"]
    if not candidates:
        lines.append("No supported engine candidate was found.")
    for item in candidates:
        lines.extend([
            f"### {item['engine']} — {item['classification']} ({item['confidence']:.2f})",
            "",
            f"Signal groups: {', '.join(item['signal_groups'])}",
            "",
        ])
        for evidence in item["evidence"]:
            lines.append(f"- `{evidence['signal_group']}`: `{evidence['path']}`")
        lines.extend(["", f"Next tool hint: {item['tool_hint']}", ""])
    lines.extend(["## Inventory", ""])
    for name, value in report["inventory"]["categories"].items():
        examples = ", ".join(f"`{item}`" for item in value["examples"]) or "none"
        lines.append(f"- {name}: **{value['count']}**; examples: {examples}")
    lines.extend(["", "## Recommended next step", "", report["next_step"], "", "## Limits", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    if report["warnings"]:
        lines.extend(["", "## Scan warnings", ""])
        lines.extend(f"- {item}" for item in report["warnings"])
    plan = report["localization_plan"]
    lines.extend(["", "## Localization plan", "", f"- Engine: **{plan['engine']}**", f"- Evidence: `{plan['evidence_status']}`", f"- Route: {plan['route']}", "", "### Suggested commands", ""])
    lines.extend(f"- `{item}`" for item in plan["commands"])
    lines.extend(["", "### Release gates", ""])
    lines.extend(f"- {item}" for item in plan["release_gates"])
    return "\n".join(lines) + "\n"


def _write_text(path_value: str, text: str) -> None:
    target = Path(path_value)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def _assert_report_outside_input(path_value: str | None, root: Path) -> None:
    if not path_value:
        return
    target = Path(path_value).resolve(strict=False)
    if target == root or root in target.parents:
        raise ValueError(f"report output must be outside the audited input tree: {target}")


def _selftest() -> int:
    paths = ["startup.tjs", "scenario/scene01.ks", "data.xp3", "game.exe"]
    candidates = detect_engines(paths)
    assert candidates and candidates[0]["engine"] == "KiriKiri", candidates
    assert candidates[0]["classification"] == "candidate", candidates[0]
    assert len(candidates[0]["signal_groups"]) == 3, candidates[0]
    weak = detect_engines(["startup.tjs"])
    assert weak[0]["classification"] == "weak-candidate", weak
    assert detect_engines(["readme.md"]) == []
    synthetic = {"engine_candidates": candidates}
    plan = build_localization_plan(synthetic)
    assert plan["engine"] == "KiriKiri" and "vn_script_adapter.py extract" in " ".join(plan["commands"]), plan
    print("selftest OK")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Read-only Galgame project evidence audit.")
    parser.add_argument("--selftest", action="store_true")
    sub = parser.add_subparsers(dest="command")
    for name in ("scan", "plan"):
        scan = sub.add_parser(name, help="scan one game directory and produce evidence plus an advisory localization plan")
        scan.add_argument("root")
        scan.add_argument("--json", dest="json_path", help="write JSON report")
        scan.add_argument("--markdown", help="write Markdown report")
        scan.add_argument("--max-files", type=int, default=20000)
        scan.add_argument("--max-encoding-samples", type=int, default=20)
        scan.add_argument("--sample-bytes", type=int, default=65536)
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    if args.command not in {"scan", "plan"}:
        parser.print_help()
        return 2
    root = Path(args.root).resolve(strict=True)
    _assert_report_outside_input(args.json_path, root)
    _assert_report_outside_input(args.markdown, root)
    report = build_report(root, max_files=args.max_files, max_encoding_samples=args.max_encoding_samples, sample_bytes=args.sample_bytes)
    if args.json_path:
        _write_text(args.json_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if args.markdown:
        _write_text(args.markdown, render_markdown(report))
    top = report["engine_candidates"][0] if report["engine_candidates"] else None
    label = f"{top['engine']} {top['classification']} confidence={top['confidence']:.2f}" if top else "unknown"
    print(f"mode=read-only files={report['inventory']['files']} engine={label} input_files_changed=0")
    print(f"next={report['next_step']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
