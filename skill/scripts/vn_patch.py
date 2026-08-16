#!/usr/bin/env python3
"""Hash-bound, reversible file-replacement patch tool for VN localization.

Implements the release/rollback discipline in galgame-localization-reverse/
SKILL.md without embedding original commercial resources: a patch is a payload
of replacement/added files plus a manifest that binds every file to exact
original and new SHA-256 hashes. Apply refuses to run against the wrong
baseline, backs up every replaced file, verifies each write, and records a
rollback map that restores original hashes byte-for-byte.

This is the safest release form (file replacement/overlay). For loose-file
engines it is a complete solution; for archive engines, use it on the rebuilt
loose files or pair it with an engine-native repack, still hash-bound.

Commands:
    build    --game-dir G --payload P --out PKG
    apply    --pkg PKG --game-dir G [--force-add]
    verify   --pkg PKG --game-dir G
    rollback --pkg PKG --game-dir G
    --selftest

Manifest/report schemas: references/manifest-and-audit-schema.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import PurePosixPath
from typing import Any

MANIFEST_VERSION = 1


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel_files(root: str) -> list[str]:
    """Return POSIX-style relative paths of every file under root."""
    out = []
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            out.append(rel)
    return sorted(out)


def _safe_rel(rel: str) -> str:
    """Reject absolute paths, drive letters, and parent-directory escapes."""
    p = PurePosixPath(rel)
    if p.is_absolute() or ":" in rel or ".." in p.parts:
        raise ValueError(f"unsafe relative path in payload/manifest: {rel!r}")
    return rel


def _under(root: str, rel: str) -> str:
    return os.path.join(root, _safe_rel(rel).replace("/", os.sep))


def build(game_dir: str, payload: str, out_pkg: str) -> dict[str, Any]:
    files_dir = os.path.join(out_pkg, "files")
    os.makedirs(files_dir, exist_ok=True)
    entries = []
    for rel in rel_files(payload):
        _safe_rel(rel)
        src = _under(payload, rel)
        new_sha = sha256_file(src)
        new_size = os.path.getsize(src)
        target = _under(game_dir, rel)
        if os.path.isfile(target):
            action = "replace"
            orig_sha: str | None = sha256_file(target)
            orig_size: int | None = os.path.getsize(target)
        else:
            action = "add"
            orig_sha, orig_size = None, None
        dst = _under(files_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        entries.append({
            "rel": rel, "action": action,
            "original_sha256": orig_sha, "original_size": orig_size,
            "new_sha256": new_sha, "new_size": new_size,
        })
    manifest = {
        "tool": "vn_patch.py",
        "manifest_version": MANIFEST_VERSION,
        "note": "hash-bound file-replacement patch; original hashes are the "
                "baseline gate. Do not apply to a game whose files differ.",
        "entries": entries,
    }
    with open(os.path.join(out_pkg, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    return manifest


def _load_manifest(pkg: str) -> dict[str, Any]:
    with open(os.path.join(pkg, "manifest.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def _classify(game_dir: str, e: dict[str, Any]) -> str:
    """State of a single game file relative to a manifest entry."""
    target = _under(game_dir, e["rel"])
    exists = os.path.isfile(target)
    cur = sha256_file(target) if exists else None
    if cur == e["new_sha256"]:
        return "applied"
    if e["action"] == "replace" and cur == e["original_sha256"]:
        return "clean"
    if e["action"] == "add" and not exists:
        return "clean"
    return "drift"  # unknown/modified/wrong baseline


def verify(pkg: str, game_dir: str) -> dict[str, Any]:
    man = _load_manifest(pkg)
    states = {e["rel"]: _classify(game_dir, e) for e in man["entries"]}
    counts: dict[str, int] = {}
    for s in states.values():
        counts[s] = counts.get(s, 0) + 1
    if all(s == "applied" for s in states.values()):
        overall = "APPLIED"
    elif all(s == "clean" for s in states.values()):
        overall = "CLEAN"
    else:
        overall = "MIXED/DRIFT"
    return {"overall": overall, "counts": counts, "states": states}


def apply(pkg: str, game_dir: str, force_add: bool = False) -> dict[str, Any]:
    man = _load_manifest(pkg)
    backup_dir = os.path.join(pkg, "backup")
    # --- Preflight: prove the baseline before mutating anything. ---
    problems = []
    for e in man["entries"]:
        target = _under(game_dir, e["rel"])
        if e["action"] == "replace":
            if not os.path.isfile(target):
                problems.append(f"missing original for replace: {e['rel']}")
            elif sha256_file(target) != e["original_sha256"]:
                problems.append(f"baseline mismatch (wrong version?): {e['rel']}")
        elif e["action"] == "add" and os.path.isfile(target) and not force_add:
            problems.append(f"add-target already exists: {e['rel']} (use --force-add)")
    if problems:
        return {"status": "ABORTED", "reason": "preflight failed", "problems": problems}

    # --- Mutate, backing up and verifying each write; roll back on any error. ---
    rollback_entries: list[dict[str, Any]] = []
    done: list[tuple[str, str]] = []  # (rel, action) applied so far
    try:
        for e in man["entries"]:
            rel = e["rel"]
            target = _under(game_dir, rel)
            payload_file = _under(os.path.join(pkg, "files"), rel)
            if e["action"] == "replace":
                bpath = _under(backup_dir, rel)
                os.makedirs(os.path.dirname(bpath), exist_ok=True)
                shutil.copy2(target, bpath)
                rollback_entries.append({
                    "rel": rel, "action": "replace",
                    "backup": os.path.relpath(bpath, pkg).replace(os.sep, "/"),
                    "original_sha256": e["original_sha256"],
                    "new_sha256": e["new_sha256"],
                })
            else:
                rollback_entries.append({
                    "rel": rel, "action": "add",
                    "new_sha256": e["new_sha256"],
                })
            os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
            shutil.copy2(payload_file, target)
            written = sha256_file(target)
            if written != e["new_sha256"]:
                raise IOError(f"post-write hash mismatch: {rel}")
            done.append((rel, e["action"]))
    except Exception as exc:  # noqa: BLE001 - best-effort auto-rollback
        _emergency_rollback(pkg, game_dir, rollback_entries)
        return {"status": "FAILED", "reason": str(exc),
                "rolled_back": [r for r, _ in done]}

    with open(os.path.join(pkg, "rollback.json"), "w", encoding="utf-8") as fh:
        json.dump({"entries": rollback_entries}, fh, ensure_ascii=False, indent=2)
    return {"status": "APPLIED", "files": len(rollback_entries)}


def _emergency_rollback(pkg: str, game_dir: str, entries: list[dict[str, Any]]) -> None:
    for e in reversed(entries):
        target = _under(game_dir, e["rel"])
        if e["action"] == "replace":
            bpath = os.path.join(pkg, e["backup"].replace("/", os.sep))
            if os.path.isfile(bpath):
                shutil.copy2(bpath, target)
        elif e["action"] == "add" and os.path.isfile(target):
            os.remove(target)


def rollback(pkg: str, game_dir: str) -> dict[str, Any]:
    rpath = os.path.join(pkg, "rollback.json")
    if not os.path.isfile(rpath):
        return {"status": "NO_ROLLBACK", "reason": "apply was never run"}
    with open(rpath, "r", encoding="utf-8") as fh:
        entries = json.load(fh)["entries"]
    restored, added_removed, problems = [], [], []
    for e in reversed(entries):
        rel = e["rel"]
        target = _under(game_dir, rel)
        if e["action"] == "replace":
            bpath = os.path.join(pkg, e["backup"].replace("/", os.sep))
            if not os.path.isfile(bpath):
                problems.append(f"backup missing: {rel}")
                continue
            shutil.copy2(bpath, target)
            if sha256_file(target) != e["original_sha256"]:
                problems.append(f"restored hash mismatch: {rel}")
            else:
                restored.append(rel)
        else:  # add: only remove if it still matches what we wrote
            if os.path.isfile(target):
                if sha256_file(target) == e["new_sha256"]:
                    os.remove(target)
                    added_removed.append(rel)
                else:
                    problems.append(f"added file changed since apply, kept: {rel}")
    status = "ROLLED_BACK" if not problems else "PARTIAL"
    return {"status": status, "restored": restored,
            "added_removed": added_removed, "problems": problems}


def _selftest() -> int:
    root = tempfile.mkdtemp(prefix="vnpatch_")
    try:
        game = os.path.join(root, "game")
        payload = os.path.join(root, "payload")
        pkg = os.path.join(root, "pkg")
        os.makedirs(os.path.join(game, "scripts"))
        os.makedirs(os.path.join(game, "data"))
        os.makedirs(os.path.join(payload, "scripts"))
        # Original runtime file (to be replaced), an untouched file, a new file.
        with open(os.path.join(game, "scripts", "0.txt"), "wb") as f:
            f.write("これはテスト".encode("cp932"))
        with open(os.path.join(game, "data", "keep.bin"), "wb") as f:
            f.write(b"\x00\x01\x02untouched")
        keep_hash = sha256_file(os.path.join(game, "data", "keep.bin"))
        with open(os.path.join(payload, "scripts", "0.txt"), "wb") as f:
            f.write("这是测试".encode("gbk"))
        with open(os.path.join(payload, "readme_zh.txt"), "wb") as f:
            f.write("汉化说明".encode("utf-8"))
        orig_hash = sha256_file(os.path.join(game, "scripts", "0.txt"))

        man = build(game, payload, pkg)
        acts = {e["rel"]: e["action"] for e in man["entries"]}
        assert acts["scripts/0.txt"] == "replace" and acts["readme_zh.txt"] == "add", acts

        assert verify(pkg, game)["overall"] == "CLEAN"
        res = apply(pkg, game)
        assert res["status"] == "APPLIED", res
        # Replaced file now holds translated bytes; new file exists; keep.bin untouched.
        assert open(os.path.join(game, "scripts", "0.txt"), "rb").read() == "这是测试".encode("gbk")
        assert os.path.isfile(os.path.join(game, "readme_zh.txt"))
        assert sha256_file(os.path.join(game, "data", "keep.bin")) == keep_hash
        assert verify(pkg, game)["overall"] == "APPLIED"

        rb = rollback(pkg, game)
        assert rb["status"] == "ROLLED_BACK", rb
        assert sha256_file(os.path.join(game, "scripts", "0.txt")) == orig_hash
        assert not os.path.isfile(os.path.join(game, "readme_zh.txt"))
        assert verify(pkg, game)["overall"] == "CLEAN"

        # Wrong-baseline guard: tamper the original, apply must abort, no mutation.
        with open(os.path.join(game, "scripts", "0.txt"), "wb") as f:
            f.write(b"tampered different version")
        tam_hash = sha256_file(os.path.join(game, "scripts", "0.txt"))
        res2 = apply(pkg, game)
        assert res2["status"] == "ABORTED", res2
        assert sha256_file(os.path.join(game, "scripts", "0.txt")) == tam_hash  # untouched
        print("selftest OK")
        return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Hash-bound reversible VN patch tool.")
    sub = ap.add_subparsers(dest="cmd")
    for name in ("build", "apply", "verify", "rollback"):
        sp = sub.add_parser(name)
        if name == "build":
            sp.add_argument("--game-dir", required=True)
            sp.add_argument("--payload", required=True)
            sp.add_argument("--out", required=True, dest="out_pkg")
        else:
            sp.add_argument("--pkg", required=True)
            sp.add_argument("--game-dir", required=True)
            if name == "apply":
                sp.add_argument("--force-add", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest()
    if args.cmd == "build":
        man = build(args.game_dir, args.payload, args.out_pkg)
        print(f"built {len(man['entries'])} entries -> {args.out_pkg}")
        return 0
    if args.cmd == "apply":
        res = apply(args.pkg, args.game_dir, args.force_add)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res["status"] == "APPLIED" else 1
    if args.cmd == "verify":
        res = verify(args.pkg, args.game_dir)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "rollback":
        res = rollback(args.pkg, args.game_dir)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res["status"] == "ROLLED_BACK" else 1
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
