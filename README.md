# dsh-galgame-localization-reverse

[中文](README.zh.md) | English

> [!IMPORTANT]
> Unofficial community plugin. Independently developed and maintained; not reviewed or endorsed by DeepSeek.

A packaged DeepSeek Harness skill for evidence-driven Windows galgame and visual-novel localization.

![Engine evidence to reversible release](docs/demo.svg)

## What it does

- detects 25+ visual-novel engine families from files, signatures, and runtime evidence;
- routes text, image, archive, bytecode, font, and encoding work to focused references;
- preserves placeholders, control codes, source hashes, save compatibility, and rollback paths;
- includes `vn_qa.py` for placeholder/encoding gates;
- includes `vn_patch.py` for hash-bound file replacement, verification, and rollback;
- includes dependency-free `vn_image_qa.py` for PNG/APNG, JPEG, GIF, and BMP inventory plus geometry, alpha, frame-count, and hash comparison;
- includes dependency-free `vn_slot_qa.py` for fixed-slot layout, terminator, padding, control-marker, zero-mutation, and outside-region checks;
- covers AI6WIN, BGI/Ethornell, Director, RealLive, Delphi/DirectDraw, PSP/Vita workflows, and custom engines.

## Install

```powershell
dsh plugin --profile web add github:julescules/dsh-galgame-localization-reverse#v0.3.0
dsh --profile web --dump-config
```

Restart DSH after installation. The bundled provider registers `galgame-localization-reverse` with `ctx.skills` and exposes its references and scripts through `resourceBase`.

## Use

Ask DSH to use `galgame-localization-reverse`, then provide the game directory and goal. The workflow starts with read-only inventory and engine evidence before selecting an extraction or writeback route.

```text
Use galgame-localization-reverse to identify this engine, build a text-owner map,
and propose a reversible localization workflow for D:\Games\Example.
```

## Built-in utilities

```powershell
python -X utf8 skill\scripts\vn_qa.py --selftest
python -X utf8 skill\scripts\vn_patch.py --selftest
python -X utf8 skill\scripts\vn_image_qa.py --selftest
python -X utf8 skill\scripts\vn_slot_qa.py --selftest

# Compare original and localized raster trees.
python -X utf8 skill\scripts\vn_image_qa.py compare D:\project\original\images D:\project\working\images -o D:\project\logs\image-qa.json

# Prove a UTF-16LE fixed-slot rebuild changed only the declared region.
python -X utf8 skill\scripts\vn_slot_qa.py compare D:\project\original\Data.ifc D:\project\working\Data.ifc --offset 0x1000 --slot-size 96 --count 100 -o D:\project\logs\slot-qa.json
```

The repository contains no game assets, decrypted archives, credentials, or title-specific keys. Public releases should contain tooling, manifests, documentation, and differential or replacement patches only.

## Verified

- official packaged Skill Provider shape: `inject = ['skills']` and `ctx.skills.registerProvider`;
- official `dsh.bundle.patch` install path;
- frontmatter removal and resource-base resolution;
- direct-reference integrity across the skill bundle;
- Node provider tests plus all four Python utility self-tests;
- package allowlist and public-content scan.
- real `@deepseek-ai/dsh@0.1.1-rc.2` profile installation and config composition with clean host-peer resolution.

```powershell
npm run check
npm pack --dry-run
```

## Limits

- Engine formats and binary constants remain title/version specific until proven against exact hashes.
- Static validation does not replace runtime UI, save/load, audio, and rollback tests.
- DeepSeek Harness is in developer preview; pin a reviewed plugin release.

## License

[MIT](LICENSE)
