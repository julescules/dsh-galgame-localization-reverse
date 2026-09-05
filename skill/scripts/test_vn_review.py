import unittest
from vn_review import apply_review


class ReviewTests(unittest.TestCase):
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
