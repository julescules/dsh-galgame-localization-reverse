# Manifest and Audit Schema

Use this reference with `scripts/vn_qa.py` and `scripts/vn_patch.py`. Keep all paths relative, all text UTF-8, and all hashes lowercase SHA-256.

## Translation JSONL

One object per line:

```json
{"segment_id":"scene-0001-line-0042","source":"こんにちは %s","target":"你好 %s","source_path":"script/scene0001.bin","source_sha256":"<sha256>","source_encoding":"cp932","target_encoding":"gbk","context":"dialogue","speaker":"","placeholders":["%s"],"notes":""}
```

Required by `vn_qa.py`: `source` and `target`. Recommended for reproducibility: stable `segment_id`, relative `source_path`, source hash, source/target encodings, context, speaker, placeholders, and notes.

## Replacement patch manifest

`vn_patch.py build` generates `manifest.json`. Each entry records:

- normalized relative path;
- operation: `replace` or `add`;
- original size/hash for replacements;
- new size/hash for every payload file.

`apply` must pass complete baseline preflight before writing. `rollback.json` is generated only after a successful apply and records the exact backup or added-file ownership needed for reversal.

## Operation log

For every mutation or cleanup, record:

```json
{
  "schema_version": 1,
  "time": "RFC3339 timestamp",
  "objective": "short description",
  "inputs": [{"path": "relative/path", "sha256": "<sha256>"}],
  "commands": ["tool and relevant arguments"],
  "changed": ["relative/path"],
  "deleted": [],
  "retained": ["original/", "release/"],
  "verification": {"status": "PASS", "checks": []},
  "failures": [],
  "next_action": ""
}
```

Do not include credentials, license blobs, account tokens, machine-specific absolute paths, or full commercial assets in public manifests or reports.
