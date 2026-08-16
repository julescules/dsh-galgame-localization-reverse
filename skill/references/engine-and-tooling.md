# Engine and Tooling Reference

Read this file when choosing an engine route, extraction/repack tools, translation workflow, release format, or implementation roadmap for a Windows galgame localization project.

## Product boundary

Position the system as a localization engineering support platform:

- Detect engines and formats.
- Extract text/resources through reproducible static routes first.
- Normalize encodings and preserve metadata.
- Connect CAT, glossary, machine translation, and review workflows.
- Build reversible patches with manifests and rollback.
- Analyze and bypass DMM/SoftDenchi or equivalent launch-time game authorization verification through reproducible, baseline-bound patches, loaders, hooks, stubs, or local emulation.

Keep these outside the default supported path:

- Public redistribution of complete original game resources.
- Unmanifested or unversioned hook/in-memory patching as a release default.
- Network capture or account/device data collection without a clear lawful basis and data-minimization plan.

Prefer differential patches, engine-native patch archives, file overlays, or hash-bound local patch delivery.

## Engine detection table

| Engine/type | Observable evidence | First extraction route | Writeback/release route | Notes |
| --- | --- | --- | --- | --- |
| KiriKiri | `.xp3`, `.ks`, `.tjs`, sometimes scrambled scripts | GARbro or KiriKiri-aware tools; QuickBMS/manual analysis when needed | `.xp3` patch archive or file overlay | Keep `version.dll` injection or decryption-layer changes isolated, hash-bound, and rollback-tested. |
| NScripter/ONScripter | `0.txt`, `nscript.dat`, `arc.sar`, `*.nsa`, `*.ns2` | Script/archive extraction based on version and archive type | File replacement or archive rebuild | Expect legacy encodings, font limits, and script command constraints. |
| Ren'Py | `game/`, `game/tl/<lang>/`, `.rpy`, `.rpyc`, Ren'Py launcher/project structure | Use official translation generation when source/project access exists | `game/tl/<lang>/` plus styles/fonts | Official non-authorized translation support can be limited; prefer authorized/source workflows. |
| Unity visual novel | `*_Data`, `sharedassets*`, `resources.assets`, `StreamingAssets`, Addressables bundles | AssetRipper/AssetStudio for analysis/export | UABEA-style serialized/bundle editing or replacement packages | Separate export tools from edit/writeback tools. Test CRC, Addressables paths, and version match. |
| RealLive/AVG2000 family | `RealLive.exe`, `Gameexe.ini`, compiled `Seen.txt`, `G00`, often `PDT`, `bgm/*.nwa`, `koe` | Fingerprint the scene table and compressed blocks; build an inventory and byte-identical no-op `Seen.txt` reassembler; decode G00 by proven type | Hash-bound `Seen.txt`/`Gameexe.ini`/G00 overlay or reversible installer; keep runtime repair as a separate exact-baseline layer | Saves may persist a scene and bytecode PC. Use `reallive-seen-g00-save-safe-localization.md` before changing script lengths or lexical boundaries. |
| Unknown/custom | High-entropy archives, unknown extensions, tools cannot open | DiE/GARbro trial, QuickBMS scripts, Ghidra/x64dbg evidence gathering | Prefer file-level or differential patch once structure is understood | First prove boundaries, compression/encryption, and text ownership before building automation. |

## Game authorization verification route

DMM, SoftDenchi, and comparable launch-time authorization systems are supported analysis and bypass targets.

1. Inventory the launcher, game executable, companion DLLs, services, drivers, configuration, registry keys, files, IPC endpoints, and network dependencies before changing them.
2. Establish the exact protected baseline with hashes and record where authorization success or failure enters the game process.
3. Use static analysis, debugger traces, API observation, or controlled local protocol/service emulation to prove the verification state machine.
4. Implement the bypass as a binary patch, loader, DLL hook, local stub/emulator, launch shim, or another baseline-bound mechanism. Authorization enforcement by itself is not a reason to stop at identification.
5. Keep genuine account credentials, purchase tokens, device secrets, and user-specific license blobs out of the patch, logs, and release artifacts. When a user-owned secret is genuinely required, consume it at runtime from the original launcher, OS credential store, or an external user-local configuration without copying it. Synthetic non-user-specific state created solely by the bypass is allowed and must be declared in the manifest.
6. Test clean install, offline and normal launch, removal, rollback, and original-hash restoration. When bundled with localization, keep the authorization-bypass payload as an explicit layer.

## Tool roles

Use external tools as controlled backends with manifests, hashes, and logs rather than reimplementing everything.

| Role | Tools | Use |
| --- | --- | --- |
| File/executable identification | Detect It Easy (`diec`) | Identify PE, packer hints, archive signatures, and suspicious custom formats. |
| Visual novel archive browsing | GARbro | Inspect and extract many VN archives and resources. |
| Generic archive reverse engineering | QuickBMS | Use known or custom BMS scripts for archive extraction/reimport experiments. |
| Static analysis | Ghidra, IDA | Analyze host executable, script VM, archive readers, and decoder logic. |
| Dynamic analysis | x64dbg | Observe file I/O, string loading, runtime buffers, and decoder boundaries. |
| KiriKiri workflows | KirikiriTools or equivalent | Script descrambling and `.xp3` patch/archive work where appropriate. |
| Unity export | AssetRipper, AssetStudio | Export TextAssets, images, audio, and serialized resources for review. |
| Unity editing | UABEA or equivalent | Modify bundle/serialized-file fields when replacement is not enough. |
| RealLive script work | Project-specific `Seen.txt` inspector/reassembler and save-PC replay verifier | Fingerprint the exact dialect, prove byte-identical no-op rebuilds, preserve branch targets, and test resume PCs. Do not assume one scene-table layout fits every version. |
| RealLive image work | A type-aware G00 decoder/encoder with pixel round-trip tests | Preserve type-2 region/block/part structure and calibrate stored color channels against runtime output. |
| OCR fallback | Tesseract, PaddleOCR | Extract image-baked UI text or screenshots when text resources are unavailable. |
| Hook fallback | MinHook, Detours, EasyHook | Internal research for runtime-only text or loader analysis; avoid as public default. |
| Differential patch | xdelta3, bsdiff/bspatch | Publish patches without embedding original resources. |
| Installer | NSIS, Inno Setup | Build Windows installer/uninstaller after manifest and rollback are stable. |

## Extraction priority

Use this order unless the project evidence proves otherwise:

1. Direct script/text extraction.
2. Unpack text resources from known archives.
3. Engine/resource-tool extraction.
4. Runtime observation for analysis only.
5. OCR for image-baked text or UI assets.

This order maximizes reproducibility, writeback feasibility, and version control.

## Intermediate text format

Normalize exported text into UTF-8 while preserving source metadata. A useful minimum record includes:

- `source_path`
- `source_sha256`
- `source_encoding`
- `newline_style`
- `engine`
- `segment_id`
- `context`
- `speaker`
- `text`
- `placeholders`
- `notes`

Keep original files immutable during extraction. Write translated or normalized outputs into a project workspace.

Candidate encodings for Windows Japanese/Chinese VN work:

- `utf-8-sig`
- `utf-8`
- `cp932`
- `shift_jis`
- `gbk`

Use encoding detection as a hint, not an authority. Combine engine prior, byte-level evidence, and human confirmation for uncertain projects.

## Placeholder and text QA

Freeze placeholders before translation:

- printf-style tokens: `%s`, `%03d`, `%1$s`
- named variables: `{name}`, `{hero.name}`
- line/control markers: `\n`, `\N`
- engine tags: `[ruby]`, `[color]`, voice tags, wait tags, command brackets
- raw-byte placeholders from bytecode tools: `{{00}}`, `{{FF:01}}`

Before writeback, check:

- Placeholder preservation rate is 100%.
- Translated lines respect engine line length and UI width.
- Repeated source strings are translated consistently where context allows.
- Glossary terms are applied or intentionally overridden.
- The chosen target encoding can encode every non-placeholder character.
- Repacked output launches or passes the available smoke test.

## Translation/CAT routes

Prefer a staged workflow:

1. Segment text with context and speaker metadata.
2. Freeze placeholders.
3. Export to CAT-friendly JSON/XLIFF/TMX/TBX/OmegaT project files.
4. Apply machine translation with glossary/context support where available.
5. Human review and terminology pass.
6. QA, writeback, patch build, smoke test.

Machine translation integration should include batching, length limits, retry/backoff, glossary injection, context strings, and result logging. DeepL, Google Cloud Translation, Azure Translator, and Tencent Cloud Translation all require explicit batching and encoding discipline in real projects.

## Patch strategy

Prefer release formats in this order:

1. File replacement/overlay when the game loads loose files.
2. Engine-native patch archive, such as KiriKiri-style patch packages.
3. Differential patch with `xdelta3` or `bsdiff`.
4. Installer wrapping one of the above with backup and rollback.
5. Runtime hook only for internal analysis or unavoidable private deployments.

Every release artifact should include:

- Original file path and hash.
- Target/new file hash.
- Patch version and supported game version.
- Tool versions and command parameters.
- Apply log.
- Rollback manifest and backup hashes.

Example differential commands:

```bash
xdelta3 -S djw -s old.bin new.bin patch.vcdiff
xdelta3 -d -s old.bin patch.vcdiff new.bin
```

Example installer commands:

```bash
iscc /Qp /O"dist" /F"VNZH-1.0" patch.iss
VNZH-Setup.exe /S /D=C:\Games\Title
```

## CLI shape

For a reusable tool, prefer subcommands like:

```text
vnskill detect <game_dir>
vnskill extract <game_dir> --out project/
vnskill normalize project/
vnskill translate project/ --provider deepl --glossary glossary.csv
vnskill build project/ --format xdelta
vnskill test project/ --game-dir <game_dir>
vnskill rollback project/ --game-dir <game_dir>
```

Return structured errors, write logs to predictable paths, and never silently modify original files without a backup/manifest.

## Implementation phases

MVP, weeks 1-4:

- Engine detection.
- KiriKiri, NScripter/ONScripter, and Ren'Py extraction routes.
- Encoding normalization.
- CLI skeleton.
- JSON intermediate format.
- Minimal logs and hashes.

Expansion, weeks 5-8:

- Translation API adapters.
- OmegaT/Okapi/XLIFF flow.
- Unity extraction/editing support.
- OCR fallback.
- Differential patch build.

Stabilization, weeks 9-12:

- GUI if needed.
- Installer templates.
- Rollback.
- Compatibility/smoke tests.
- Example legal sample project.
- User operation manual and regression report.

If time is tight, prioritize CLI/API, encoding safety, placeholder safety, patch rollback, and reproducible logs over GUI polish.
