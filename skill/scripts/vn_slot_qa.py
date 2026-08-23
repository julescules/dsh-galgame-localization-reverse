#!/usr/bin/env python3
"""Read-only QA for contiguous fixed-size text slots in VN containers.

Examples:
  python -X utf8 vn_slot_qa.py scan Data.ifc --offset 4096 --slot-size 96 --count 100 --encoding utf-16le
  python -X utf8 vn_slot_qa.py compare original.ifc rebuilt.ifc --offset 4096 --slot-size 96 --count 100 --encoding utf-16le -o slot-qa.json
  python -X utf8 vn_slot_qa.py --selftest
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


CONTROL_RE = re.compile(r"@[A-Za-z]\([^)]*\)|[①-⑳]")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _payload_and_padding(raw: bytes, encoding: str) -> tuple[bytes, bytes, list[str]]:
    errors: list[str] = []
    normalized = encoding.lower().replace("_", "-")
    if normalized in {"utf-16", "utf-16le", "utf-16-le", "utf-16be", "utf-16-be"}:
        terminator = next((pos for pos in range(0, len(raw) - 1, 2)
                           if raw[pos:pos + 2] == b"\x00\x00"), None)
        if terminator is None:
            return raw, b"", ["missing-aligned-utf16-nul"]
        payload, padding = raw[:terminator], raw[terminator + 2:]
    else:
        terminator = raw.find(b"\x00")
        if terminator < 0:
            return raw, b"", ["missing-nul"]
        payload, padding = raw[:terminator], raw[terminator + 1:]
    if any(padding):
        errors.append("nonzero-padding")
    return payload, padding, errors


def parse_slots(data: bytes, offset: int, slot_size: int, count: int,
                encoding: str) -> dict[str, Any]:
    errors: list[str] = []
    if offset < 0 or slot_size <= 0 or count <= 0:
        errors.append("invalid-layout")
    region_end = offset + slot_size * count
    if region_end > len(data):
        errors.append("region-out-of-bounds")

    slots: list[dict[str, Any]] = []
    if not errors:
        for index in range(count):
            start = offset + index * slot_size
            raw = data[start:start + slot_size]
            payload, _padding, slot_errors = _payload_and_padding(raw, encoding)
            try:
                text = payload.decode(encoding, errors="strict")
            except (UnicodeDecodeError, LookupError) as exc:
                text = ""
                slot_errors.append(f"decode-error:{exc.__class__.__name__}")
            is_utf16 = encoding.lower().replace("_", "-").startswith("utf-16")
            slots.append({
                "index": index,
                "offset": start,
                "slotSize": slot_size,
                "usedBytes": len(payload),
                "capacity": slot_size // 2 - 1 if is_utf16 else slot_size - 1,
                "capacityUnit": "utf16-code-units" if is_utf16 else "bytes",
                "text": text,
                "controlMarkers": CONTROL_RE.findall(text),
                "rawSha256": sha256(raw),
                "valid": not slot_errors,
                "errors": slot_errors,
            })

    invalid = sum(not slot["valid"] for slot in slots)
    return {
        "schema": "vn-fixed-slot-scan/v1",
        "status": "PASS" if not errors and not invalid else "FAIL",
        "fileSha256": sha256(data),
        "fileSize": len(data),
        "layout": {"offset": offset, "slotSize": slot_size, "count": count,
                   "encoding": encoding, "regionEnd": region_end},
        "invalidSlots": invalid,
        "errors": errors,
        "slots": slots,
    }


def compare_data(original: bytes, rebuilt: bytes, offset: int, slot_size: int,
                 count: int, encoding: str) -> dict[str, Any]:
    old = parse_slots(original, offset, slot_size, count, encoding)
    new = parse_slots(rebuilt, offset, slot_size, count, encoding)
    region_end = offset + slot_size * count
    failures: list[dict[str, Any]] = []

    if len(original) != len(rebuilt):
        failures.append({"id": "file-size-changed", "original": len(original), "rebuilt": len(rebuilt)})
    if old["status"] != "PASS":
        failures.append({"id": "original-layout-invalid", "errors": old["errors"], "invalidSlots": old["invalidSlots"]})
    if new["status"] != "PASS":
        failures.append({"id": "rebuilt-layout-invalid", "errors": new["errors"], "invalidSlots": new["invalidSlots"]})
    if len(original) >= region_end and len(rebuilt) >= region_end:
        if original[:offset] != rebuilt[:offset] or original[region_end:] != rebuilt[region_end:]:
            failures.append({"id": "outside-slot-region-changed"})

    changed_slots: list[int] = []
    for before, after in zip(old["slots"], new["slots"]):
        if before["rawSha256"] != after["rawSha256"]:
            changed_slots.append(before["index"])
        if before["controlMarkers"] != after["controlMarkers"]:
            failures.append({
                "id": "control-marker-sequence-changed",
                "slot": before["index"],
                "original": before["controlMarkers"],
                "rebuilt": after["controlMarkers"],
            })

    return {
        "schema": "vn-fixed-slot-compare/v1",
        "status": "PASS" if not failures else "FAIL",
        "zeroMutationIdentical": original == rebuilt,
        "originalSha256": sha256(original),
        "rebuiltSha256": sha256(rebuilt),
        "changedSlots": changed_slots,
        "failures": failures,
        "originalScan": old,
        "rebuiltScan": new,
    }


def _emit(report: dict[str, Any], output: str | None) -> None:
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if output:
        destination = Path(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(rendered)


def _fixture(texts: list[str], slot_size: int = 16, encoding: str = "utf-16le") -> bytes:
    result = bytearray(b"HEAD")
    terminator = b"\x00\x00" if encoding.startswith("utf-16") else b"\x00"
    for text in texts:
        encoded = text.encode(encoding)
        raw = encoded + terminator
        assert len(raw) <= slot_size
        result.extend(raw.ljust(slot_size, b"\x00"))
    result.extend(b"TAIL")
    return bytes(result)


def _selftest() -> int:
    original = _fixture(["甲@c(1)", "②乙"])
    scan = parse_slots(original, 4, 16, 2, "utf-16le")
    assert scan["status"] == "PASS" and scan["slots"][0]["controlMarkers"] == ["@c(1)"], scan
    assert compare_data(original, original, 4, 16, 2, "utf-16le")["zeroMutationIdentical"] is True
    translated = _fixture(["丙@c(1)", "②丁"])
    comparison = compare_data(original, translated, 4, 16, 2, "utf-16le")
    assert comparison["status"] == "PASS" and comparison["changedSlots"] == [0, 1], comparison
    marker_loss = _fixture(["甲", "②乙"])
    assert compare_data(original, marker_loss, 4, 16, 2, "utf-16le")["status"] == "FAIL"
    outside = b"FAIL" + original[4:]
    assert any(x["id"] == "outside-slot-region-changed"
               for x in compare_data(original, outside, 4, 16, 2, "utf-16le")["failures"])
    corrupt = bytearray(original)
    corrupt[4 + 14] = 1
    assert parse_slots(bytes(corrupt), 4, 16, 2, "utf-16le")["status"] == "FAIL"
    print("selftest OK")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return _selftest()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("scan", "compare"):
        command = sub.add_parser(name)
        command.add_argument("files", nargs=1 if name == "scan" else 2)
        command.add_argument("--offset", type=lambda x: int(x, 0), required=True)
        command.add_argument("--slot-size", type=lambda x: int(x, 0), required=True)
        command.add_argument("--count", type=lambda x: int(x, 0), required=True)
        command.add_argument("--encoding", default="utf-16le")
        command.add_argument("-o", "--output")
    args = parser.parse_args()
    payloads = [Path(item).read_bytes() for item in args.files]
    report = (parse_slots(payloads[0], args.offset, args.slot_size, args.count, args.encoding)
              if args.command == "scan" else
              compare_data(payloads[0], payloads[1], args.offset, args.slot_size, args.count, args.encoding))
    _emit(report, args.output)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
