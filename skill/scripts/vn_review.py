#!/usr/bin/env python3
"""Import explicitly reviewed translation-memory CSV rows into a separate catalog."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from vn_translation_memory import _load_records, _id, _write_jsonl
from vn_qa import verify_placeholders


def apply_review(records, rows, expected_hash, encoding=None, row_numbers=None):
    output = [dict(row) for row in records]
    index = {}
    for n, record in enumerate(output, 1):
        key = _id(record, 'segment_id', n)
        if key in index:
            raise ValueError('duplicate segment ID in catalog')
        index[key] = record
    seen = set()
    applied = 0
    for offset, row in enumerate(rows):
        line = row_numbers[offset] if row_numbers is not None else offset + 2
        prefix = f'CSV row {line}: '
        if None in row or any(value is None for value in row.values()):
            raise ValueError(prefix + 'malformed CSV row: missing or extra cells')
        if row.get('current_sha256') != expected_hash:
            raise ValueError(prefix + 'review CSV belongs to a different current catalog')
        key = row.get('segment_id')
        if key not in index or key in seen:
            raise ValueError(prefix + 'unknown or duplicate review segment ID')
        seen.add(key)
        target = row.get('reviewed_target', '')
        if not isinstance(target, str):
            raise ValueError(prefix + 'reviewed_target must be text')
        if not target.strip():
            continue
        record = index[key]
        source = record.get('source')
        if not isinstance(source, str) or not verify_placeholders(source, target)['ok']:
            raise ValueError(prefix + f'placeholder mismatch: {key}')
        if record.get('target') and record['target'] != target:
            raise ValueError(prefix + f'existing translation differs: {key}')
        if encoding:
            try:
                target.encode(encoding, errors='strict')
            except UnicodeEncodeError as error:
                raise ValueError(prefix + f'target cannot be encoded as {encoding}') from error
        record['target'] = target
        applied += 1
    return output, applied


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current', required=True, help='Exact original current catalog used by migrate')
    parser.add_argument('--review-csv', required=True)
    parser.add_argument('--output', help='New output catalog; required unless --dry-run is used')
    parser.add_argument('--dry-run', action='store_true', help='Validate every row and print counts without writing a catalog')
    parser.add_argument('--encoding', help='Optional target encoding, e.g. cp932 or gbk')
    args = parser.parse_args()
    if not args.dry_run and not args.output:
        parser.error('--output is required unless --dry-run is used')
    if args.dry_run and args.output:
        parser.error('--dry-run does not accept --output')
    current = Path(args.current).resolve(strict=True)
    review = Path(args.review_csv).resolve(strict=True)
    output = Path(args.output).resolve() if args.output else None
    if output is not None and (output in {current, review} or output.exists()):
        raise ValueError('output must be a new path distinct from inputs')
    digest = hashlib.sha256(current.read_bytes()).hexdigest()
    with review.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.reader(handle, strict=True)
        fields = next(reader, [])
        if len(fields) != len(set(fields)):
            raise ValueError('duplicate CSV column names')
        if not {'current_sha256', 'segment_id', 'reviewed_target'} <= set(fields):
            raise ValueError('missing required review CSV columns')
        rows, row_numbers = [], []
        while True:
            line = reader.line_num + 1
            try:
                cells = next(reader)
            except StopIteration:
                break
            except csv.Error as error:
                raise ValueError(f'CSV row {line}: {error}') from error
            if not cells:
                continue
            if len(cells) != len(fields):
                raise ValueError(f'CSV row {line}: malformed CSV row: missing or extra cells')
            rows.append(dict(zip(fields, cells)))
            row_numbers.append(line)
        records, count = apply_review(_load_records(current), rows, digest, args.encoding, row_numbers)
    if output is not None:
        _write_jsonl(output, records, force=False)
    print(json.dumps({'schema': 'vn-review-import/v1', 'dry_run': args.dry_run, 'applied': 0 if args.dry_run else count, 'ready': count, 'pending': len(rows) - count, 'review_rows': len(rows), 'catalog_records': len(records), 'current_sha256': digest, 'review_sha256': hashlib.sha256(review.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, LookupError, csv.Error) as error:
        raise SystemExit(f'ERROR: {error}')
