#!/usr/bin/env python3
"""Inventory and compare localized raster assets without third-party packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}


def _png(data: bytes) -> dict:
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) < 33:
        raise ValueError("invalid PNG signature or truncated IHDR")
    width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
    offset = 8
    chunks: list[tuple[bytes, bytes]] = []
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("truncated PNG chunk")
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        chunks.append((kind, payload))
        offset = end
        if kind == b"IEND":
            break
    chunk_names = {kind for kind, _ in chunks}
    frame_payload = next((payload for kind, payload in chunks if kind == b"acTL"), None)
    frames = struct.unpack(">I", frame_payload[:4])[0] if frame_payload and len(frame_payload) >= 4 else 1
    return {
        "format": "PNG",
        "width": width,
        "height": height,
        "bitDepth": bit_depth,
        "alpha": color_type in {4, 6} or b"tRNS" in chunk_names,
        "animated": b"acTL" in chunk_names,
        "frames": frames,
    }


def _skip_gif_subblocks(data: bytes, offset: int) -> int:
    while offset < len(data):
        size = data[offset]
        offset += 1
        if size == 0:
            return offset
        offset += size
        if offset > len(data):
            raise ValueError("truncated GIF sub-block")
    raise ValueError("unterminated GIF sub-block")


def _gif(data: bytes) -> dict:
    if len(data) < 13 or data[:6] not in {b"GIF87a", b"GIF89a"}:
        raise ValueError("invalid GIF header")
    width, height = struct.unpack("<HH", data[6:10])
    packed = data[10]
    offset = 13 + (3 * (2 ** ((packed & 0x07) + 1)) if packed & 0x80 else 0)
    frames = 0
    transparency = False
    while offset < len(data):
        marker = data[offset]
        offset += 1
        if marker == 0x3B:
            break
        if marker == 0x2C:
            if offset + 9 > len(data):
                raise ValueError("truncated GIF image descriptor")
            image_packed = data[offset + 8]
            offset += 9
            if image_packed & 0x80:
                offset += 3 * (2 ** ((image_packed & 0x07) + 1))
            if offset >= len(data):
                raise ValueError("truncated GIF image data")
            offset += 1
            offset = _skip_gif_subblocks(data, offset)
            frames += 1
            continue
        if marker == 0x21:
            if offset >= len(data):
                raise ValueError("truncated GIF extension")
            label = data[offset]
            offset += 1
            if label == 0xF9:
                if offset + 6 > len(data) or data[offset] != 4:
                    raise ValueError("invalid GIF graphic control extension")
                transparency = transparency or bool(data[offset + 1] & 0x01)
                offset += 6
            else:
                offset = _skip_gif_subblocks(data, offset)
            continue
        raise ValueError(f"unknown GIF marker 0x{marker:02x}")
    return {
        "format": "GIF",
        "width": width,
        "height": height,
        "bitDepth": (packed & 0x07) + 1,
        "alpha": transparency,
        "animated": frames > 1,
        "frames": frames,
    }


def _jpeg(data: bytes) -> dict:
    if len(data) < 4 or not data.startswith(b"\xff\xd8"):
        raise ValueError("invalid JPEG signature")
    offset = 2
    sof = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while offset + 4 <= len(data):
        while offset < len(data) and data[offset] != 0xFF:
            offset += 1
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(data):
            break
        length = struct.unpack(">H", data[offset : offset + 2])[0]
        if length < 2 or offset + length > len(data):
            raise ValueError("truncated JPEG segment")
        if marker in sof:
            if length < 8:
                raise ValueError("truncated JPEG SOF")
            bit_depth = data[offset + 2]
            height, width = struct.unpack(">HH", data[offset + 3 : offset + 7])
            return {"format": "JPEG", "width": width, "height": height, "bitDepth": bit_depth, "alpha": False, "animated": False, "frames": 1}
        offset += length
    raise ValueError("JPEG dimensions not found")


def _bmp(data: bytes) -> dict:
    if len(data) < 30 or not data.startswith(b"BM"):
        raise ValueError("invalid BMP header")
    dib_size = struct.unpack("<I", data[14:18])[0]
    if dib_size == 12:
        width, height, _planes, bit_depth = struct.unpack("<HHHH", data[18:26])
    elif dib_size >= 40 and len(data) >= 54:
        width, signed_height, _planes, bit_depth = struct.unpack("<iiHH", data[18:30])
        height = abs(signed_height)
    else:
        raise ValueError("unsupported BMP DIB header")
    return {"format": "BMP", "width": width, "height": height, "bitDepth": bit_depth, "alpha": bit_depth == 32, "animated": False, "frames": 1}


def probe_bytes(data: bytes, suffix: str) -> dict:
    suffix = suffix.lower()
    if suffix == ".png":
        return _png(data)
    if suffix == ".gif":
        return _gif(data)
    if suffix in {".jpg", ".jpeg"}:
        return _jpeg(data)
    if suffix == ".bmp":
        return _bmp(data)
    raise ValueError(f"unsupported image extension: {suffix}")


def probe_file(path: Path, root: Path) -> dict:
    data = path.read_bytes()
    record = {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    try:
        record.update(probe_bytes(data, path.suffix))
    except ValueError as error:
        record["error"] = str(error)
    return record


def inventory(root: Path) -> list[dict]:
    if not root.is_dir():
        raise ValueError(f"image root is not a directory: {root}")
    paths = sorted((path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS), key=lambda path: path.as_posix().casefold())
    return [probe_file(path, root) for path in paths]


def compare_records(original: list[dict], localized: list[dict], allow_missing: bool = False) -> dict:
    before = {item["path"].casefold(): item for item in original}
    after = {item["path"].casefold(): item for item in localized}
    findings: list[dict] = []

    def add(severity: str, finding_id: str, path: str, message: str) -> None:
        findings.append({"severity": severity, "id": finding_id, "path": path, "message": message})

    for key in sorted(before.keys() | after.keys()):
        source = before.get(key)
        target = after.get(key)
        display = (source or target)["path"]
        if source is None:
            add("WARN", "extra-localized-asset", display, "localized tree contains an asset with no original counterpart")
            continue
        if target is None:
            add("WARN" if allow_missing else "FAIL", "missing-localized-asset", display, "localized tree is missing an original asset")
            continue
        if source.get("error") or target.get("error"):
            add("FAIL", "unreadable-image", display, f"original={source.get('error')!r}; localized={target.get('error')!r}")
            continue
        if source["format"] != target["format"]:
            add("FAIL", "format-changed", display, f"{source['format']} -> {target['format']}")
        if (source["width"], source["height"]) != (target["width"], target["height"]):
            add("FAIL", "geometry-changed", display, f"{source['width']}x{source['height']} -> {target['width']}x{target['height']}")
        if source["alpha"] and not target["alpha"]:
            add("FAIL", "alpha-lost", display, "localized asset removed an alpha/transparency channel")
        if source["frames"] != target["frames"]:
            add("FAIL", "frame-count-changed", display, f"{source['frames']} -> {target['frames']}")
        if source["sha256"] == target["sha256"]:
            add("WARN", "unchanged-asset", display, "localized asset is byte-identical to the original")

    failures = sum(item["severity"] == "FAIL" for item in findings)
    warnings = sum(item["severity"] == "WARN" for item in findings)
    return {
        "schema": "vn-image-qa/v1",
        "status": "FAIL" if failures else "PASS",
        "summary": {"original": len(original), "localized": len(localized), "failures": failures, "warnings": warnings},
        "findings": findings,
        "original": original,
        "localized": localized,
    }


def _write_result(result: object, output: Path | None) -> None:
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if output is None:
        sys.stdout.write(text)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="\n")


def _png_fixture(width: int, height: int, alpha: bool = True, animated: bool = False) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    color_type = 6 if alpha else 2
    result = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0))
    if animated:
        result += chunk(b"acTL", struct.pack(">II", 2, 0))
    return result + chunk(b"IEND", b"")


def selftest() -> None:
    source_data = _png_fixture(320, 180, alpha=True, animated=True)
    target_data = _png_fixture(640, 360, alpha=False, animated=False)
    source = {"path": "ui/title.png", "bytes": len(source_data), "sha256": hashlib.sha256(source_data).hexdigest(), **probe_bytes(source_data, ".png")}
    target = {"path": "ui/title.png", "bytes": len(target_data), "sha256": hashlib.sha256(target_data).hexdigest(), **probe_bytes(target_data, ".png")}
    report = compare_records([source], [target])
    ids = {item["id"] for item in report["findings"]}
    assert report["status"] == "FAIL"
    assert {"geometry-changed", "alpha-lost", "frame-count-changed"} <= ids
    assert compare_records([source], [dict(source)])["status"] == "PASS"
    print("selftest OK")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="run deterministic in-memory checks")
    subparsers = parser.add_subparsers(dest="command")
    inventory_parser = subparsers.add_parser("inventory", help="write a JSON inventory for one image tree")
    inventory_parser.add_argument("root", type=Path)
    inventory_parser.add_argument("-o", "--output", type=Path)
    compare_parser = subparsers.add_parser("compare", help="compare original and localized image trees")
    compare_parser.add_argument("original", type=Path)
    compare_parser.add_argument("localized", type=Path)
    compare_parser.add_argument("-o", "--output", type=Path)
    compare_parser.add_argument("--allow-missing", action="store_true", help="downgrade missing localized assets to warnings")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.selftest:
        selftest()
        return 0
    try:
        if args.command == "inventory":
            records = inventory(args.root.resolve())
            _write_result({"schema": "vn-image-inventory/v1", "root": str(args.root.resolve()), "count": len(records), "assets": records}, args.output)
            return 0 if all("error" not in item for item in records) else 1
        if args.command == "compare":
            report = compare_records(inventory(args.original.resolve()), inventory(args.localized.resolve()), args.allow_missing)
            _write_result(report, args.output)
            return 0 if report["status"] == "PASS" else 1
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    build_parser().print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
