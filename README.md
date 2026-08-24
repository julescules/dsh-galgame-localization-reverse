# Galgame Doctor for DeepSeek Harness

[中文](README.zh.md) | English

> [!IMPORTANT]
> Unofficial community plugin. Independently developed and maintained; not reviewed or endorsed by DeepSeek.

Audit first, localize second. Give DeepSeek Harness a visual-novel folder and get an evidence-backed engine candidate, risky files, encoding clues, strict translation QA, and a safe next step. The audit is offline and read-only; only report paths outside the audited tree are written.

![Synthetic terminal example: read-only engine audit and strict translation QA](docs/demo.svg)

## Start in 30 seconds

```powershell
dsh plugin --profile web add github:julescules/dsh-galgame-localization-reverse#v0.4.0
```

Restart DSH, then ask:

```text
Use galgame-localization-reverse to audit D:\Games\Example read-only.
Show the engine evidence, localization risks, and the safest next step.
```

No API key is required. The plugin contains no game assets, decrypted archives, credentials, or title-specific keys.

## What you get

### One-command project audit

`vn_project_audit.py` inventories a bounded set of files and reports:

- engine candidates with confidence, signal groups, and concrete path evidence;
- script, archive, image, font, and executable candidates;
- bounded encoding samples and CJK-path-safe relative paths;
- a cautious classification of `candidate`, `weak-candidate`, or `unknown`;
- the reference, existing ecosystem tool, and verification step to try next.

The classification is routing evidence, not a claim that static inspection proves runtime behavior.

```powershell
python -X utf8 skill\scripts\vn_project_audit.py scan D:\Games\Example `
  --json D:\project\logs\project-audit.json `
  --markdown D:\project\logs\project-audit.md
```

### Strict translation preflight

`vn_qa.py` now rejects missing, added, or reordered control tokens by default. It also reports empty translations, source-identical targets, residual Japanese, and target-encoding failures. Generic JSON/JSONL and GalTransl cache fields are supported without third-party packages.

```powershell
python -X utf8 skill\scripts\vn_qa.py check-jsonl D:\project\translations.jsonl `
  --encoding gbk --require-complete `
  --report D:\project\logs\translation-qa.json `
  --markdown D:\project\logs\translation-qa.md
```

An intentionally broken synthetic fixture produces a concise failure report:

```text
FAIL  2 blockers · 3 segments
E control-token-added  scene01:2  added [wait]
E empty-translation    scene01:3  translation required
```

### Release evidence, not another translator

The bundled workflow also provides:

- `vn_patch.py` — hash-bound file replacement, verification, backup, and rollback;
- `vn_image_qa.py` — PNG/APNG, JPEG, GIF, and BMP geometry/alpha/frame comparison;
- `vn_slot_qa.py` — fixed-slot terminator, padding, marker, and outside-region checks;
- focused routes for AI6WIN, BGI/Ethornell, Director, RealLive, Delphi/DirectDraw, PSP/Vita, Ren'Py, KiriKiri, and custom engines.

GalTransl, VNTextPatch, GARbro, LunaTranslator, and engine-specific tools can handle translation or extraction. Galgame Doctor complements them by deciding what the project appears to be, checking their text output, and preserving release evidence.

## Try the synthetic examples

```powershell
python -X utf8 skill\scripts\vn_project_audit.py scan examples\synthetic-project\game `
  --json test_outputs\synthetic-audit.json `
  --markdown test_outputs\synthetic-audit.md

python -X utf8 skill\scripts\vn_qa.py check-jsonl examples\translations.jsonl `
  --encoding gbk --require-complete `
  --report test_outputs\translation-qa.json `
  --markdown test_outputs\translation-qa.md
```

All example text is synthetic and redistributable.

## DSH integration

The bundle uses the official packaged Skill Provider shape:

- `inject = ['skills']`;
- `ctx.skills.registerProvider(...)`;
- directory `resourceBase` for on-demand references and scripts;
- the official `dsh.bundle.patch` install path.

The registered name remains `galgame-localization-reverse`, so existing prompts continue to work.

## Verify the package

[![CI](https://github.com/julescules/dsh-galgame-localization-reverse/actions/workflows/ci.yml/badge.svg)](https://github.com/julescules/dsh-galgame-localization-reverse/actions/workflows/ci.yml)

```powershell
npm run check
npm pack --dry-run
```

The check runs provider tests plus deterministic self-tests for the project audit and all bundled QA/patch utilities.

## Limits

- Engine formats and binary constants remain title/version specific until proven against exact hashes.
- Static audit and QA do not replace a zero-mutation round trip or in-game UI, save/load, audio, and rollback tests.
- Residual Japanese can be intentional; review each finding or maintain an explicit exclusion instead of silently weakening the gate.
- DeepSeek Harness is in developer preview; pin a reviewed plugin release.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md) for contribution and reporting guidance.

## License

[MIT](LICENSE)
