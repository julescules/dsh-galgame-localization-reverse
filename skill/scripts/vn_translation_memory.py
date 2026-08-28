#!/usr/bin/env python3
"""Deterministic translation-memory merge for iterative VN localization.

Only exact, placeholder-safe matches are applied automatically. Fuzzy matches
are suggestions for review and never populate the target field.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable

from vn_qa import verify_placeholders


SCHEMA_VERSION = "vn-translation-memory/v1"


def _load_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.casefold() in {".jsonl", ".ndjson"}:
        records = []
        with path.open("r", encoding="utf-8-sig") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"line {line_number} in {path} is not an object")
                records.append(value)
        return records
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("records", "items", "data", "translations"):
            if isinstance(value.get(key), list):
                return [item for item in value[key] if isinstance(item, dict)]
    raise ValueError(f"{path} must contain a record list or JSONL objects")


def _text(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    return value if isinstance(value, str) else ""


def _id(record: dict[str, Any], field: str, index: int) -> str:
    value = record.get(field)
    return str(value) if value not in (None, "") else f"#index:{index}"


def _translated(record: dict[str, Any], source_field: str, target_field: str) -> bool:
    source, target = _text(record, source_field), _text(record, target_field)
    return bool(target and target != source)


def _safe_target(source: str, targets: Iterable[str]) -> tuple[str | None, str | None]:
    unique = sorted({target for target in targets if target})
    if not unique:
        return None, "no translated target"
    if len(unique) != 1:
        return None, "conflicting targets for the same exact source"
    target = unique[0]
    placeholder = verify_placeholders(source, target)
    if not placeholder["ok"]:
        return None, "placeholder mismatch in previous translation"
    return target, None


def merge_records(
    current: list[dict[str, Any]],
    previous: list[dict[str, Any]],
    *,
    source_field: str = "source",
    target_field: str = "target",
    id_field: str = "segment_id",
    fuzzy_threshold: float = 0.86,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not 0.0 <= fuzzy_threshold <= 1.0:
        raise ValueError("fuzzy threshold must be between 0 and 1")

    current_ids: set[str] = set()
    previous_ids_by_object: dict[int, str] = {}
    previous_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    previous_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    translated_previous = []
    for index, record in enumerate(previous, 1):
        record_id = _id(record, id_field, index)
        previous_ids_by_object[id(record)] = record_id
        previous_by_id[record_id].append(record)
        source = _text(record, source_field)
        if source:
            previous_by_source[source].append(record)
        if source and _translated(record, source_field, target_field):
            translated_previous.append((record_id, source, _text(record, target_field)))

    merged: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    counts = {
        "kept_current": 0,
        "reused_by_id": 0,
        "reused_by_source": 0,
        "suggestions": 0,
        "conflicts": 0,
        "pending": 0,
    }

    for index, original in enumerate(current, 1):
        record = dict(original)
        record_id = _id(record, id_field, index)
        if record_id in current_ids:
            raise ValueError(f"duplicate current segment id: {record_id}")
        current_ids.add(record_id)
        source = _text(record, source_field)
        if not source:
            raise ValueError(f"current record {record_id} has no source text")
        current_target = _text(record, target_field)
        detail: dict[str, Any] = {"segment_id": record_id}

        if current_target:
            counts["kept_current"] += 1
            detail["decision"] = "kept-current"
            if not verify_placeholders(source, current_target)["ok"]:
                detail["warning"] = "current target has a placeholder mismatch; run strict QA"
            details.append(detail)
            merged.append(record)
            continue

        same_id = [item for item in previous_by_id.get(record_id, []) if _text(item, source_field) == source and _translated(item, source_field, target_field)]
        if same_id:
            target, conflict = _safe_target(source, (_text(item, target_field) for item in same_id))
            if target is not None:
                record[target_field] = target
                counts["reused_by_id"] += 1
                detail.update({"decision": "reused-exact-id", "previous_segment_id": record_id})
                details.append(detail)
                merged.append(record)
                continue
            detail.update({"decision": "conflict", "reason": conflict})

        exact_source = [item for item in previous_by_source.get(source, []) if _translated(item, source_field, target_field)]
        if exact_source and detail.get("decision") != "conflict":
            target, conflict = _safe_target(source, (_text(item, target_field) for item in exact_source))
            if target is not None:
                record[target_field] = target
                counts["reused_by_source"] += 1
                detail.update({
                    "decision": "reused-exact-source",
                    "previous_segment_ids": sorted({previous_ids_by_object[id(item)] for item in exact_source}),
                })
                details.append(detail)
                merged.append(record)
                continue
            detail.update({"decision": "conflict", "reason": conflict})

        if detail.get("decision") == "conflict":
            counts["conflicts"] += 1
            counts["pending"] += 1
            details.append(detail)
            merged.append(record)
            continue

        best: tuple[float, str, str, str] | None = None
        for previous_id, previous_source, previous_target in translated_previous:
            ratio = SequenceMatcher(None, source, previous_source, autojunk=False).ratio()
            candidate = (ratio, previous_id, previous_source, previous_target)
            if best is None or candidate > best:
                best = candidate
        if best is not None and best[0] >= fuzzy_threshold:
            placeholder = verify_placeholders(source, best[3])
            detail.update({
                "decision": "review-suggestion",
                "similarity": round(best[0], 6),
                "previous_segment_id": best[1],
                "previous_source": best[2],
                "suggested_target": best[3],
                "placeholder_compatible": placeholder["ok"],
            })
            counts["suggestions"] += 1
        else:
            detail["decision"] = "pending"
        counts["pending"] += 1
        details.append(detail)
        merged.append(record)

    report = {
        "schema": SCHEMA_VERSION,
        "status": "PASS" if counts["conflicts"] == 0 else "REVIEW",
        "current_records": len(current),
        "previous_records": len(previous),
        **counts,
        "fuzzy_threshold": fuzzy_threshold,
        "policy": "Only exact ID/source matches with one placeholder-safe target are auto-reused; fuzzy matches are review-only.",
        "details": details,
    }
    return merged, report


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]], *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"output exists; use --force to replace it: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _write_text(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"output exists; use --force to replace it: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Translation memory merge",
        "",
        f"- Status: **{report['status']}**",
        f"- Current / previous: {report['current_records']} / {report['previous_records']}",
        f"- Reused by ID / source: {report['reused_by_id']} / {report['reused_by_source']}",
        f"- Kept current: {report['kept_current']}",
        f"- Suggestions / conflicts / pending: {report['suggestions']} / {report['conflicts']} / {report['pending']}",
        "",
        "Fuzzy suggestions are never applied automatically. Run strict translation QA on the merged JSONL before writeback.",
    ]
    review = [item for item in report["details"] if item["decision"] in {"conflict", "review-suggestion"}]
    if review:
        lines.extend(["", "## Review queue", ""])
        for item in review:
            extra = item.get("reason") or f"similarity={item.get('similarity')} previous={item.get('previous_segment_id')}"
            lines.append(f"- `{item['segment_id']}`: {item['decision']} — {extra}")
    return "\n".join(lines) + "\n"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _selftest() -> int:
    current = [
        {"segment_id": "a", "source": "こんにちは {name}", "target": ""},
        {"segment_id": "b", "source": "新しい行", "target": ""},
        {"segment_id": "c", "source": "少し変わった", "target": ""},
        {"segment_id": "d", "source": "競合", "target": ""},
        {"segment_id": "e", "source": "破損 {name}", "target": ""},
        {"segment_id": "f", "source": "既存", "target": "已有"},
    ]
    previous = [
        {"segment_id": "a", "source": "こんにちは {name}", "target": "你好 {name}"},
        {"segment_id": "old-b", "source": "新しい行", "target": "新行"},
        {"segment_id": "old-c", "source": "少し変わる", "target": "略有变化"},
        {"segment_id": "d1", "source": "競合", "target": "甲"},
        {"segment_id": "d2", "source": "競合", "target": "乙"},
        {"segment_id": "e", "source": "破損 {name}", "target": "损坏"},
    ]
    merged, report = merge_records(current, previous, fuzzy_threshold=0.7)
    assert merged[0]["target"] == "你好 {name}"
    assert merged[1]["target"] == "新行"
    assert merged[2]["target"] == ""
    assert merged[5]["target"] == "已有"
    assert report["reused_by_id"] == 1 and report["reused_by_source"] == 1
    assert report["suggestions"] >= 1 and report["conflicts"] == 2 and report["kept_current"] == 1
    with tempfile.TemporaryDirectory(prefix="vn-tm-") as temp_value:
        temp = Path(temp_value)
        output, report_path = temp / "merged.jsonl", temp / "report.json"
        _write_jsonl(output, merged, force=False)
        report["inputs"] = {"current_sha256": "fixture", "previous_sha256": "fixture"}
        _write_text(report_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n", force=False)
        assert len(_load_records(output)) == len(current)
        assert json.loads(report_path.read_text(encoding="utf-8"))["schema"] == SCHEMA_VERSION
    print("selftest OK")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Merge a previous VN translation into a newly extracted catalog without auto-applying fuzzy matches.")
    parser.add_argument("--selftest", action="store_true")
    sub = parser.add_subparsers(dest="command")
    migrate = sub.add_parser("migrate")
    migrate.add_argument("--current", required=True)
    migrate.add_argument("--previous", required=True)
    migrate.add_argument("--output", required=True)
    migrate.add_argument("--report", required=True)
    migrate.add_argument("--markdown")
    migrate.add_argument("--source-field", default="source")
    migrate.add_argument("--target-field", default="target")
    migrate.add_argument("--id-field", default="segment_id")
    migrate.add_argument("--fuzzy-threshold", type=float, default=0.86)
    migrate.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    if args.command != "migrate":
        parser.error("choose migrate or --selftest")

    current_path, previous_path = Path(args.current).resolve(strict=True), Path(args.previous).resolve(strict=True)
    output_path, report_path = Path(args.output).resolve(strict=False), Path(args.report).resolve(strict=False)
    markdown_path = Path(args.markdown).resolve(strict=False) if args.markdown else None
    protected = {current_path, previous_path}
    if output_path in protected or report_path in protected or markdown_path in protected:
        raise ValueError("outputs must not overwrite either input catalog")
    if len({str(item) for item in (output_path, report_path, markdown_path) if item is not None}) < (3 if markdown_path else 2):
        raise ValueError("output, report, and markdown paths must be distinct")
    if not args.force:
        existing = [path for path in (output_path, report_path, markdown_path) if path is not None and path.exists()]
        if existing:
            raise FileExistsError(f"output exists; use --force to replace it: {existing[0]}")

    current, previous = _load_records(current_path), _load_records(previous_path)
    merged, report = merge_records(
        current,
        previous,
        source_field=args.source_field,
        target_field=args.target_field,
        id_field=args.id_field,
        fuzzy_threshold=args.fuzzy_threshold,
    )
    report["inputs"] = {
        "current": str(current_path),
        "current_sha256": _sha256(current_path),
        "previous": str(previous_path),
        "previous_sha256": _sha256(previous_path),
    }
    _write_jsonl(output_path, merged, force=args.force)
    _write_text(report_path, json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", force=args.force)
    if markdown_path is not None:
        _write_text(markdown_path, _markdown(report), force=args.force)
    print(json.dumps({key: report[key] for key in ("schema", "status", "reused_by_id", "reused_by_source", "suggestions", "conflicts", "pending")}, ensure_ascii=False))
    return 0 if report["conflicts"] == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (FileExistsError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2)
