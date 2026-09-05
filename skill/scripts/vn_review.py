#!/usr/bin/env python3
"""Import explicitly reviewed translation-memory CSV rows into a separate catalog."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from vn_translation_memory import _load_records, _id, _write_jsonl
from vn_qa import verify_placeholders


def apply_review(records, rows, expected_hash, encoding=None):
    output = [dict(row) for row in records]
    index = {}
    for n, record in enumerate(output, 1):
        key = _id(record, 'segment_id', n)
        if key in index:
            raise ValueError('duplicate segment ID in catalog')
        index[key] = record
    seen = set()
    applied = 0
    for row in rows:
        if row.get('current_sha256') != expected_hash:
            raise ValueError('review CSV belongs to a different current catalog')
        key = row.get('segment_id')
        if key not in index or key in seen:
            raise ValueError('unknown or duplicate review segment ID')
        seen.add(key)
        target = row.get('reviewed_target', '')
        if not target.strip():
            continue
        record = index[key]
        source = record.get('source')
        if not isinstance(source, str) or not verify_placeholders(source, target)['ok']:
            raise ValueError(f'placeholder mismatch: {key}')
        if record.get('target') and record['target'] != target:
            raise ValueError(f'existing translation differs: {key}')
        if encoding:
            target.encode(encoding, errors='strict')
        record['target'] = target
        applied += 1
    return output, applied


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current', required=True, help='Exact original current catalog used by migrate')
    parser.add_argument('--review-csv', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--encoding', help='Optional target encoding, e.g. cp932 or gbk')
    args = parser.parse_args()
    current = Path(args.current).resolve(strict=True)
    review = Path(args.review_csv).resolve(strict=True)
    output = Path(args.output).resolve()
    if output in {current, review} or output.exists():
        raise ValueError('output must be a new path distinct from inputs')
    digest = hashlib.sha256(current.read_bytes()).hexdigest()
    with review.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if not {'current_sha256', 'segment_id', 'reviewed_target'} <= set(reader.fieldnames or []):
            raise ValueError('missing required review CSV columns')
        records, count = apply_review(_load_records(current), list(reader), digest, args.encoding)
    _write_jsonl(output, records, force=False)
    print(json.dumps({'schema': 'vn-review-import/v1', 'applied': count, 'current_sha256': digest, 'review_sha256': hashlib.sha256(review.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, LookupError) as error:
        raise SystemExit(f'ERROR: {error}')
