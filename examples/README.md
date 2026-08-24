# Synthetic Galgame Doctor examples

These files are original, minimal fixtures. They contain no commercial game assets or title-specific data.

From the repository root:

```powershell
python -X utf8 skill\scripts\vn_project_audit.py scan examples\synthetic-project\game `
  --json test_outputs\synthetic-audit.json `
  --markdown test_outputs\synthetic-audit.md

python -X utf8 skill\scripts\vn_qa.py check-jsonl examples\translations.jsonl `
  --encoding gbk --require-complete `
  --report test_outputs\translation-qa.json `
  --markdown test_outputs\translation-qa.md
```

The project scan should identify KiriKiri as an evidence-backed candidate. The translation fixture intentionally fails: one record adds a control tag and another is empty. It is useful for testing CI failure output and report rendering.
