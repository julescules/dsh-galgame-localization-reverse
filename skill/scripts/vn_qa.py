#!/usr/bin/env python3
"""Localization QA: placeholder freezing/verification + encoding round-trip.

Implements the two safety gates that galgame-localization-reverse/SKILL.md
requires before any writeback:

  1. Placeholder preservation == 100%. Every control token, printf spec,
     named variable, engine tag, and raw-byte placeholder present in the
     source must survive in the translation.
  2. Encoding round-trip. Every non-placeholder character in the translation
     must be encodable in the target codec (e.g. gbk/cp932), or the repack
     will corrupt or drop it.

The intermediate format is JSON Lines; each record needs at least
`source` and `target`. See references/manifest-and-audit-schema.md.

Usage:
    python vn_qa.py placeholders --text "..."
    python vn_qa.py verify --src "..." --tgt "..."
    python vn_qa.py check-jsonl records.jsonl --encoding gbk [--report out.json]
    python vn_qa.py --selftest
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from typing import Any


# Placeholder grammar for Japanese/Chinese Windows VN projects.
# Order matters: raw-byte {{..}} and named {..} are matched before bare braces,
# and printf specs before a lone '%'. Tune per engine as needed.
PLACEHOLDER_PATTERNS = [
    r"\{\{[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2})?\}\}",  # raw bytes {{FF}} / {{00:01}}
    r"%[0-9]+\$[-+ #0]*[0-9]*(?:\.[0-9]+)?[diouxXeEfgGcspn%]",  # positional %1$s
    r"%[-+ #0]*[0-9*]*(?:\.[0-9*]+)?[diouxXeEfgGcspn%]",        # printf %03d %s
    r"\{[A-Za-z_][\w.]*\}",   # named {name} {hero.name}
    r"\{[0-9]+\}",            # indexed {0} {12}
    r"\[[^\[\]\n]{0,40}\]",   # engine tags [ruby] [color=#fff] [r] [wait]
    r"\\[nNtr\\]",            # control escapes \n \N \t \r \\
]
_PH_RE = re.compile("|".join(f"(?:{p})" for p in PLACEHOLDER_PATTERNS))


def extract_placeholders(text: str) -> list[str]:
    """Return placeholders in left-to-right order (duplicates preserved)."""
    return [m.group(0) for m in _PH_RE.finditer(text)]


def strip_placeholders(text: str) -> str:
    """Remove placeholders so only translatable characters remain."""
    return _PH_RE.sub("", text)


def verify_placeholders(src: str, tgt: str) -> dict[str, Any]:
    """Compare source vs target placeholder multisets and order."""
    src_list = extract_placeholders(src)
    tgt_list = extract_placeholders(tgt)
    src_c, tgt_c = Counter(src_list), Counter(tgt_list)
    missing = list((src_c - tgt_c).elements())  # in source, dropped in target
    added = list((tgt_c - src_c).elements())     # only in target (often a bug)
    reordered = (src_c == tgt_c) and (src_list != tgt_list)
    return {
        "ok": not missing,          # 100% preservation = nothing dropped
        "missing": missing,
        "added": added,
        "reordered": reordered,
        "source_placeholders": src_list,
        "target_placeholders": tgt_list,
    }


def check_encoding(text: str, encoding: str) -> dict[str, Any]:
    """Check whether translatable chars survive the target codec round-trip."""
    body = strip_placeholders(text)
    try:
        body.encode(encoding)
        return {"ok": True, "encoding": encoding, "unencodable": []}
    except UnicodeEncodeError:
        bad: Counter[str] = Counter()
        for ch in body:
            try:
                ch.encode(encoding)
            except UnicodeEncodeError:
                bad[ch] += 1
        return {
            "ok": False,
            "encoding": encoding,
            "unencodable": [{"char": c, "codepoint": f"U+{ord(c):04X}", "count": n}
                            for c, n in bad.most_common()],
        }


def check_jsonl(path: str, encoding: str | None) -> dict[str, Any]:
    total = 0
    ph_fail = 0
    enc_fail = 0
    failures: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            src = rec.get("source", "")
            tgt = rec.get("target", "")
            if not tgt:
                continue  # untranslated segment: nothing to verify yet
            total += 1
            rid = rec.get("segment_id", lineno)
            ph = verify_placeholders(src, tgt)
            enc = check_encoding(tgt, encoding) if encoding else {"ok": True}
            if not ph["ok"] or not enc["ok"]:
                if not ph["ok"]:
                    ph_fail += 1
                if not enc["ok"]:
                    enc_fail += 1
                failures.append({
                    "segment_id": rid,
                    "placeholder": {k: ph[k] for k in ("missing", "added", "reordered")},
                    "encoding": enc if not enc.get("ok", True) else None,
                })
    return {
        "checked": total,
        "placeholder_failures": ph_fail,
        "encoding_failures": enc_fail,
        "passed": total - len(failures),
        "failures": failures,
        "gate": "PASS" if not failures else "FAIL",
    }


def _selftest() -> int:
    # Placeholder extraction covers each grammar branch.
    assert extract_placeholders(r"hi %s %03d {name} [ruby] \n {{FF}} {{0A:1B}} %1$s") == \
        ["%s", "%03d", "{name}", "[ruby]", r"\n", "{{FF}}", "{{0A:1B}}", "%1$s"]
    # Dropped placeholder is caught (raw string: literal backslash-n token).
    r = verify_placeholders(r"hello %s\n", "你好")
    assert r["ok"] is False and "%s" in r["missing"] and r"\n" in r["missing"], r
    # Full preservation passes.
    r = verify_placeholders(r"[name]says %s\n", r"[name]说 %s\n")
    assert r["ok"] is True and not r["missing"] and not r["added"], r
    # Extra placeholder in target is flagged (added) but does not drop source.
    r = verify_placeholders("%s", "%s %d")
    assert r["ok"] is True and r["added"] == ["%d"], r
    # Reorder detected when multiset equal but order differs.
    r = verify_placeholders("%s %d", "%d %s")
    assert r["reordered"] is True, r
    # Encoding gate: emoji cannot be encoded in gbk; ph is ignored.
    e = check_encoding("正常文本 %s", "gbk")
    assert e["ok"] is True, e
    e = check_encoding("héllo 😀 %s", "gbk")
    assert e["ok"] is False and any(x["char"] == "😀" for x in e["unencodable"]), e
    # cp932 cannot encode a simplified-only char like 你 -> caught.
    e = check_encoding("你好", "cp932")
    assert e["ok"] is False, e
    print("selftest OK")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Localization placeholder + encoding QA.")
    sub = ap.add_subparsers(dest="cmd")

    p1 = sub.add_parser("placeholders", help="list placeholders in a string")
    p1.add_argument("--text", required=True)

    p2 = sub.add_parser("verify", help="verify placeholder preservation src->tgt")
    p2.add_argument("--src", required=True)
    p2.add_argument("--tgt", required=True)

    p3 = sub.add_parser("check-jsonl", help="run both gates over a JSONL project file")
    p3.add_argument("path")
    p3.add_argument("--encoding", help="target codec, e.g. gbk / cp932 / utf-8")
    p3.add_argument("--report", help="write full JSON report to this path")

    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest()
    if args.cmd == "placeholders":
        for ph in extract_placeholders(args.text):
            print(ph)
        return 0
    if args.cmd == "verify":
        res = verify_placeholders(args.src, args.tgt)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res["ok"] else 1
    if args.cmd == "check-jsonl":
        rep = check_jsonl(args.path, args.encoding)
        if args.report:
            with open(args.report, "w", encoding="utf-8") as fh:
                json.dump(rep, fh, ensure_ascii=False, indent=2)
        print(f"gate={rep['gate']} checked={rep['checked']} "
              f"placeholder_failures={rep['placeholder_failures']} "
              f"encoding_failures={rep['encoding_failures']}")
        return 0 if rep["gate"] == "PASS" else 1
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
