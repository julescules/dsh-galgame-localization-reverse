import unittest
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from vn_review import apply_review


class ReviewTests(unittest.TestCase):
    def test_cli_preflight_and_import_preserve_sources(self):
        with tempfile.TemporaryDirectory(prefix='vn-review-') as folder:
            root = Path(folder)
            current, review, output = root / 'current.jsonl', root / 'review.csv', root / 'out.jsonl'
            current.write_text(json.dumps({'segment_id': 'a', 'source': 'Hi {name}', 'target': ''}) + '\n', encoding='utf-8')
            digest = hashlib.sha256(current.read_bytes()).hexdigest()
            with review.open('w', encoding='utf-8-sig', newline='') as handle:
                writer = csv.writer(handle)
                writer.writerow(['current_sha256', 'segment_id', 'reviewed_target'])
                writer.writerow([digest, 'a', '你好 {name}'])
            originals = (current.read_bytes(), review.read_bytes())
            command = [sys.executable, '-B', '-X', 'utf8', str(Path(__file__).with_name('vn_review.py')), '--current', str(current), '--review-csv', str(review)]
            dry = subprocess.run(command + ['--dry-run', '--encoding', 'gbk'], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(dry.returncode, 0, dry.stderr)
            report = json.loads(dry.stdout)
            self.assertTrue(report['dry_run'])
            self.assertEqual((report['applied'], report['ready'], report['pending']), (0, 1, 0))
            self.assertEqual(set(root.iterdir()), {current, review})
            imported = subprocess.run(command + ['--output', str(output)], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(imported.returncode, 0, imported.stderr)
            self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['target'], '你好 {name}')
            self.assertEqual((current.read_bytes(), review.read_bytes()), originals)
            collision = subprocess.run(command + ['--output', str(output)], capture_output=True, text=True, encoding='utf-8')
            self.assertNotEqual(collision.returncode, 0)
            bad_encoding = subprocess.run(command + ['--dry-run', '--encoding', 'ascii'], capture_output=True, text=True, encoding='utf-8')
            self.assertNotEqual(bad_encoding.returncode, 0)
            review.write_text('current_sha256,segment_id,reviewed_target\n"unterminated', encoding='utf-8')
            malformed = subprocess.run(command + ['--dry-run'], capture_output=True, text=True, encoding='utf-8')
            self.assertNotEqual(malformed.returncode, 0)
            self.assertNotIn('Traceback', malformed.stderr)

    def test_malformed_rows_are_rejected(self):
        records = [{'segment_id': 'a', 'source': 'Hi', 'target': ''}]
        for row in [{'current_sha256': 'hash', 'segment_id': 'a', 'reviewed_target': None}, {'current_sha256': 'hash', 'segment_id': 'a', 'reviewed_target': '你好', None: ['extra']}]:
            with self.assertRaisesRegex(ValueError, 'malformed CSV'):
                apply_review(records, [row], 'hash')

    def test_review_is_explicit_and_preserves_inputs(self):
        records = [{'segment_id': 'a', 'source': 'Hi {name}', 'target': ''}]
        rows = [{'current_sha256': 'hash', 'segment_id': 'a', 'reviewed_target': '你好 {name}'}]
        output, count = apply_review(records, rows, 'hash', 'gbk')
        self.assertEqual(count, 1)
        self.assertEqual(records[0]['target'], '')
        self.assertEqual(output[0]['target'], '你好 {name}')
        rows[0]['reviewed_target'] = ''
        self.assertEqual(apply_review(records, rows, 'hash')[1], 0)

    def test_reject_stale_duplicate_unknown_and_broken_tokens(self):
        records = [{'segment_id': 'a', 'source': 'Hi {name}', 'target': ''}]
        row = {'current_sha256': 'hash', 'segment_id': 'a', 'reviewed_target': '你好 {name}'}
        for rows in [[dict(row, current_sha256='old')], [row, row], [dict(row, segment_id='b')], [dict(row, reviewed_target='你好')]]:
            with self.assertRaises(ValueError):
                apply_review(records, rows, 'hash')


if __name__ == '__main__':
    unittest.main()
