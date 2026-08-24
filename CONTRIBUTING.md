# Contributing

Contributions should solve a reproducible visual-novel localization problem while keeping the public package small, inspectable, and reversible.

## Before opening a pull request

1. Base the change on observable file or runtime evidence. Keep confirmed facts, hypotheses, and unresolved questions separate.
2. Add a synthetic fixture or deterministic self-test. Do not commit commercial game files, decrypted archives, credentials, title-specific keys, license data, saves, or private user paths.
3. Keep inspection and QA commands read-only by default. Any mutation must be explicit, hash-bound, verified, and reversible.
4. Preserve UTF-8 and test paths containing spaces and CJK characters.
5. Run:

```powershell
npm run check
npm pack --dry-run
python -X utf8 path\to\skill-creator\scripts\quick_validate.py skill
```

Use the matching `quick_validate.py` from your own Skill tooling for the last command.

## Scope

Adapters and evidence layers that complement GalTransl, VNTextPatch, GARbro, and engine-specific tools are welcome. A second general-purpose translator, OCR stack, runtime hook framework, or archive suite needs a demonstrated gap before it belongs here.
