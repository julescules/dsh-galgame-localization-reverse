# Synthetic Galgame Doctor examples

These files are original, minimal fixtures. They contain no commercial game assets or title-specific data.

From the repository root:

```powershell
python -X utf8 skill\scripts\vn_project_audit.py plan examples\synthetic-project\game `
  --json test_outputs\synthetic-audit.json `
  --markdown test_outputs\synthetic-audit.md

python -X utf8 skill\scripts\vn_qa.py check-jsonl examples\translations.jsonl `
  --encoding gbk --require-complete --glossary examples\glossary.json `
  --report test_outputs\translation-qa.json `
  --markdown test_outputs\translation-qa.md
```

Extract the source-script fixtures without touching them:

```powershell
python -X utf8 skill\scripts\vn_script_adapter.py extract examples\synthetic-project\game `
  --engine kirikiri --output test_outputs\kirikiri.jsonl
python -X utf8 skill\scripts\vn_script_adapter.py extract examples\script-adapters\renpy `
  --engine renpy --output test_outputs\renpy.jsonl
python -X utf8 skill\scripts\vn_script_adapter.py extract examples\script-adapters\nscripter `
  --engine nscripter --output test_outputs\nscripter.jsonl
```

The project scan should identify KiriKiri as an evidence-backed candidate. The translation fixture intentionally fails: one record adds a control tag and another is empty. It is useful for testing CI failure output and report rendering.

Migrate translations after a script update without overwriting either input:

```powershell
python -X utf8 skill\scripts\vn_translation_memory.py migrate `
  --current examples\translation-memory\current.jsonl `
  --previous examples\translation-memory\previous.jsonl `
  --previous examples\translation-memory\previous-hotfix.jsonl `
  --output test_outputs\translation-memory\migrated.jsonl `
  --report test_outputs\translation-memory\report.json `
  --markdown test_outputs\translation-memory\report.md `
  --review-csv test_outputs\translation-memory\review.csv
```

Repeat `--previous` when several old releases contain reviewed work. The two history fixtures reuse one exact ID/source pair and two relocated exact sources. The near match remains review-only. The report includes every input SHA-256, and the CSV contains the pending/review queue.
