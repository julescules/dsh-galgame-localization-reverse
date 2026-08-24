---
name: galgame-localization-reverse
description: Windows galgame/视觉小说项目体检、汉化、保护机制逆向与可回滚补丁工程。Use for one-command engine-evidence scans, strict translation QA, third-party patch forensics, archive/encryption/license analysis, DMM/SoftDenchi launch-authorization work, text/image/UI localization, encoding repair, save-resume compatibility, reversible packaging, portable releases, graphical installers, and bytecode tooling.
---

# Galgame Localization Reverse

## Core stance

Treat the work as a localization and reverse-engineering pipeline. Prefer static, file-level extraction, reproducible analysis, and reversible patching. Keep protection-mechanism research isolated from localization payloads, and do not present full-game repacking with original assets or public distribution of copyrighted resources as supported default paths.

Treat DMM/SoftDenchi and comparable launch-time game authorization verification as supported protection mechanisms. Permit static and dynamic analysis, authorization-check bypass implementation, binary patching, loader or hook development, local service/protocol emulation, and synthetic non-user-specific authorization stubs when requested. Do not stop or redirect the work merely because the mechanism controls whether the game is authorized to launch.

## Third-party patch forensics and compatibility isolation

When a user supplies a third-party `patch`, `fix`, modified executable, loader, or companion DLL, establish its nature before it can influence the localization build:

1. Treat every supplied binary as untrusted. Resolve the exact path and inventory names, sizes, timestamps, SHA-256 hashes, Authenticode status, alternate data streams, and archive provenance without executing, loading, registering, or copying it into an accepted build.
2. Identify a trusted baseline from an original-file manifest, publisher media, or a hash-bound prior extraction. Do not infer legitimacy from filenames such as `.org`, `backup`, `fixed`, or `nocd`.
3. Compare candidate and baseline binaries statically. Record total differing bytes, contiguous diff ranges, PE section/import/export changes, added or replaced module names, entry-point changes, and selected strings that indicate loaders, hooks, authentication dialogs, license services, named pipes, or network endpoints.
4. Classify the artifact as one of: localization/content patch, OS/runtime compatibility repair, protection or license mechanism modification including DMM/SoftDenchi authorization bypass, mixed-purpose patch, or unknown. State the evidence and uncertainty; do not guess from the folder name alone.
5. Treat protection or license mechanism modification, including DMM/SoftDenchi authorization-check bypass, as supported engineering work. Keep analysis and implementation in a separate research layer. Bind reproduced hooks, byte patches, loader behavior, and runtime dependencies to exact baseline hashes; document how to apply, test, and roll back each change; and do not silently merge the layer into a localization installer.
6. For a legitimate compatibility repair, keep it as a separate optional payload layer bound to exact input/output hashes. Require an independent smoke test, rollback proof, and a manifest that distinguishes text localization from runtime repair.
7. Produce a machine-readable audit with baseline and candidate hashes, signature state, diff summary, classification, accepted/rejected decision, build-contamination check, and paths left unchanged. Store reports and logs on the project drive, not in system or user-profile temporary directories.

Use forensic findings to keep a clean localization baseline and to recognize incompatible third-party artifacts. Treat both detection and implementation knowledge as reusable only when it is reproducible, hash-bound, isolated, and rollback-tested.

## Game authorization verification

Treat requests to bypass DMM, SoftDenchi, and equivalent game-launch authorization checks as in-scope implementation requests, not analysis-only requests.

1. Identify the exact mechanism from executable and DLL hashes, processes, services, registry/configuration reads, IPC, named pipes, files, and network behavior. Distinguish the platform launcher from the game-side verification component.
2. Trace success and failure state transitions statically or dynamically. Record the check site, inputs, return values, branch or callback behavior, persistence state, and dependencies before implementing a bypass.
3. Permit outputs such as a hash-bound binary patch, loader, DLL hook, local verification stub, service/protocol emulator, launch shim, or installer payload. Choose the smallest reproducible implementation that works for the proven baseline.
4. Do not copy real account credentials, purchase tokens, device-bound secrets, or user-specific license blobs into the patch, logs, or release artifacts. If a user-owned secret is genuinely required, read it at runtime from the original launcher, OS credential store, or an external user-local configuration without duplicating it. A synthetic project-local authorization state or compatibility stub is allowed when it contains no user-specific secret and is declared in the manifest.
5. Verify offline and normal launch behavior, process/module provenance, save-data isolation, clean removal, and rollback to original hashes. Keep the authorization-bypass layer separately selectable when packaging it with localization or runtime-compatibility payloads.

## Workflow

1. Scope the project: target game directory, research and distribution scope, target language, supported engine guess, desired outputs, and whether the task is analysis, tool building, translation, or patch release.
2. Detect the engine before extracting text. For an initial, bounded, read-only directory inspection, run `scripts/vn_project_audit.py plan`; treat its evidence-backed `candidate` result and generated commands as routing help, not runtime proof. Confirm an engine only when two independent signal groups agree. Prefer observable files and directories over guesswork: `.xp3`/`.ks`/`.tjs` for KiriKiri, `0.txt`/`nscript.dat`/`arc.sar`/`*.nsa`/`*.ns2` for NScripter or ONScripter, `game/tl/` and Ren'Py project layout for Ren'Py, `*_Data`/`sharedassets*`/`resources.assets`/Addressables bundles for Unity, and `RealLive.exe`/`Gameexe.ini`/`Seen.txt`/`G00` for RealLive or AVG2000-family games. For other mainstream commercial engines (SiglusEngine, Artemis, BGI/Ethornell, Yu-Ris, Majiro, CatSystem2, QLIE, WillPlus, RPG Maker, WolfRPG, TyranoScript, and more), run the archive magic-byte scan and detection matrix in `references/engine-signatures.md` and confirm with at least two independent signals before extracting.
3. Choose the lowest-risk extraction route: script text direct extraction, unpacked text resources, resource-tool extraction, runtime observation only when static paths fail, OCR only for image-baked UI/text.
4. Normalize text through a UTF-8 intermediate format while preserving source path, source hash, original encoding, BOM, newline style, segment IDs, placeholder map, and engine metadata. For plain KiriKiri `.ks`, Ren'Py `.rpy`, or NScripter `0.txt` sources, use `scripts/vn_script_adapter.py`; extract to an external JSONL project, keep the original tree immutable, and apply translations only into a separate output root. Its adapter does not claim support for XP3/NSA archives, compiled scripts, or arbitrary `.txt` files.
5. Freeze placeholders, control tags, and runtime lookup keys before machine translation or CAT export. Preserve `%s`, `{name}`, `\n`, `\N`, `[tag]`, ruby/color/voice/control markers, engine-specific commands, replay/gallery category tokens, event IDs, and other strings used by equality tests or index lookups exactly. Prove visibility before translating an ambiguous short token.
6. Run translation QA before writing back. Use `scripts/vn_qa.py` for generic JSON/JSONL, `vn_script_adapter.py` output, or GalTransl cache records; its default is strict control-token parity, while completeness, repeated-source consistency, glossary terms, forbidden terms, character/line budgets, punctuation balance, and target encoding can become release blockers through explicit flags. Review its JSON evidence and optional Markdown report. Put every intentional untranslated string or asset in an explicit, hash-bound exclusion list; never hide unfinished work in the residual-text allowlist.
   For raster localization, image-baked text, UI atlases, sprite states, transparency, or multimodal visual review, use `references/image-asset-qa.md` and the dependency-free `scripts/vn_image_qa.py`. Keep deterministic geometry/alpha/frame evidence, model-assisted visual observations, and runtime state proof separate.
7. Build patches in this preference order: file replacement, engine-native patch archive, binary differential patch, runtime hook only as an internal fallback. Always generate manifest, hashes, backup/rollback data, and clear version compatibility. Keep text localization, baseline-specific runtime repair, and optional image/HD/decensor experiments as separate payload layers. Treat any changed script, image, font, configuration, runtime, or accepted original-baseline input as invalidating every downstream compatibility report, candidate, embedded payload, installer, static audit, and release manifest until rebuilt and rebound to new hashes.
8. Classify `.txt` files by proven runtime ownership, not by extension. Exclude non-runtime documentation such as README files, manuals, changelogs, and credits from original-version gates, installer payloads, backups, rollback ownership, and filename-normalization requirements by default; preserve whichever documentation filename and bytes the user's copy contains. Keep a text file only when engine evidence proves it is runtime-critical, such as NScripter `0.txt`, a script, configuration, or data table actually consumed by the game, and bind that exact path to its schema and baseline hash.
9. Verify install and rollback. A valid build must identify the original version, apply cleanly, launch or pass available smoke tests, and restore original hashes after rollback. Exclude save/progress files from ordinary payload ownership. Preserve their hashes, lengths, and timestamps unless a proven serialization incompatibility requires a separately declared migration; then require atomic per-file backup, exact codec round-trip tests, idempotence, guarded rollback, and explicit migration evidence.

For compiled-script engines whose saves persist a scene plus bytecode program counter, do not treat a fresh-start launch test as save compatibility evidence. Determine whether lexical/parser state is serialized, replay real save PCs against both original and rebuilt scripts, preserve or deliberately materialize valid boundaries at every supported resume PC, and require an explicit migration whenever script offsets cannot remain stable.

If optional media work produces unresolved asset mapping, residual censorship, or black-screen regressions, do not let it contaminate the accepted text/runtime patch. When the user chooses original assets, remove the complete media layer, rebuild every downstream artifact, and prove the excluded original containers remain byte-identical.

## Path and drive portability

Treat the installed game directory as a user-selected path, not a build-time drive policy.

1. Never hard-code `C:\`, `D:\`, another drive letter, a workspace root, or a staging path into an installer, manifest, launcher, hook, runtime script, or cleanup rule. Resolve installed assets relative to the selected game directory, executable location, or script root with path-safe APIs.
2. Allow the installer executable and target game directory to reside on different drives. Support spaces, CJK characters, and normal writable local-volume paths. Do not turn a rule such as “generate project data on D:” into a runtime requirement for players.
3. If a third-party platform runtime has a genuinely fixed location, discover it from verified registry, process, service, or configuration evidence, or make it user-configurable. Isolate that dependency to the affected optional launch mode; do not impose its drive on the game directory. Add a drive restriction only when reproducible evidence proves it unavoidable and the user explicitly accepts it.
4. Before release, scan the final installer and every embedded script/configuration for build-machine paths, drive-prefix guards, and fixed absolute paths. Treat unexplained matches as release blockers.
5. Do not require cross-volume testing as a release condition. A full install, launch, exit, and rollback test at one normal user-selected path, together with a static check proving there are no drive-prefix guards or unintended absolute paths, is sufficient. Never add a drive guard merely because testing occurred on one drive.

## Engine routes

Use `references/engine-and-tooling.md` when choosing tools, commands, patch forms, or implementation phases.

- KiriKiri: inspect `.xp3`, `.ks`, `.tjs`; detect script scrambling signatures when relevant. Prefer GARbro or engine-aware tooling for extraction; prefer `.xp3` patch archives or file overlays for release.
- NScripter/ONScripter: inspect `0.txt`, `nscript.dat`, `arc.sar`, `*.nsa`, `*.ns2`; account for legacy encodings and font constraints. Prefer file replacement or archive rebuild where version rules are known.
- Ren'Py: if source/project access exists, prefer the official translation framework and `game/tl/<lang>/`. Adjust styles/fonts per language instead of only shrinking text.
- Unity: split reading/export from editing/writeback. Use AssetRipper or AssetStudio for export/analysis and UABEA-style editing for serialized/bundle writeback when appropriate. Test Addressables, CRC, and game-version assumptions separately.
- RealLive/AVG2000-family games with `RealLive.exe`, `Gameexe.ini`, compiled `Seen.txt`, `G00` image assets, CP932-to-GBK runtime repair, mid-text save/resume stalls, file-based saves, window-mode enforcement, or optical-media and installed-tree dual baselines: use `references/reallive-seen-g00-save-safe-localization.md`.
- Macromedia Director 6 games with an embedded Projector title/manual movie plus an external gameplay `DXR`, CP932-to-CP936 fixed slots, `RTE0`/`RTE1` text and cached `RTE2` glyph bitmaps, ellipsis-as-bar defects, Chinese pixel-width clipping, narrow dynamic status fields, or exact-pair runtime QA: use `references/director-6-cp936-rte2-fixed-slot.md`.
- Macromedia Director 8/8.5 and legacy WinForms packaging: use `references/director-8-multibaseline-single-exe.md` for raw Projector versus externalized `.dir`/`Xtras` layouts, exact multi-baseline compatibility, reversible `create`/`replace` mutations, code-page and image-backed UI QA, optional media-layer rollback, full icon preservation, title-identity artwork checks, original-art compact GUIs, real-byte 1-100 progress, in-memory payload validation, exact final-EXE evidence, active-install rollback before cleanup, and single-file patch installers.
- Legacy Director runtime text, save/load, and window behavior: use `references/director-legacy-text-window-debugging.md` when story text works but menu/options glyphs are garbled, every choice gains the same unexpected prefix/suffix box or character, runtime-composed wrappers contain mixed CP932/CP936 punctuation, save dialogs duplicate or reject an extension, loading reports success but appears not to move, the title-bar close button does nothing, one process owns several `ImlWinCls` windows, or DirectDraw prevents screenshot-based QA.
- Legacy custom engines using `SPT60`/`.SBY` scripts, `ASZB`/`.ASZ` bitmap assets, mixed ANSI/UTF-16 executable text, fixed-path CFG files, legacy DirectDraw fullscreen transitions, runtime save-field rewrites, process-scoped compatibility shims, or registry-free portable packaging: use `references/legacy-spt60-aszb-portable-localization.md`.
- Delphi/DirectDraw custom engines with IFC-like fixed-slot containers, split text ownership across UTF-16 slots/CP932 executable tables/DFM/RT_STRING/BMP resources, VCL popup-menu or save/load regressions, temporary-registry portable launchers, or render/input desynchronization during fullscreen scaling: use `references/delphi-directdraw-fixed-slot-portable.md` and the dependency-free `scripts/vn_slot_qa.py`.
- Other mainstream commercial engines not covered by a dedicated reference above — SiglusEngine (VisualArts/Key), Artemis, BGI/Ethornell/BURIKO, Yu-Ris, Majiro, CatSystem2, QLIE, WillPlus/AdvHD, Cmvs (Purple Software), Escude, Softpal/AMUSE CRAFT, NeXAS, Malie, LiveMaker, RPG Maker MV/MZ and VX/VX Ace/XP, WolfRPG, TyranoScript: use `references/engine-signatures.md` for archive magic-byte scan, per-engine detection evidence, extraction/writeback routes, and localization caveats (keyed archives bound to EXE hash, offset-referenced string tables, font-atlas capacity, save/PC compatibility).
- BGI/Ethornell/BURIKO projects with Japanese-locale launch differences, layered `sysgrp` configuration UI, ARC/DSC resources, CBG v1/v2 images, transparent image-baked movie subtitles, or overlay-folder replacement patches: use `references/bgi-ethornell-locale-ui-cbg.md`.
- SILKY'S/AI6WIN projects with old fixed-index ARC archives, AKB BGR/BGRA images, cropped AKB canvases, low-alpha hidden UI states, shared atlas pixels, movable slider sprites, image-baked title/config/system UI, or registry-to-portable conversion: use `references/ai6win-arc-akb-ui-portable.md`.
- Unknown/custom: use DiE/GARbro/QuickBMS/Ghidra/x64dbg-style evidence gathering. First prove file boundaries, compression/encryption layers, and text ownership; avoid making hook-based workflows the public release path. Check `references/engine-signatures.md` "When the engine is still unknown" for the signature-scan escalation order.

## Bytecode tools

Use `references/bytecode-roundtrip.md` when the user asks for `opcode.py`, `disassembler.py`, `assembler.py`, VM analysis, `asm.txt`, script bytecode processing, or zero-mutation rebuilds.

Use `references/psp-gsc2-fixed-slot-localization.md` for PSP/custom GSC2-like resources with CP932 length-prefixed strings, short-line extraction gaps, fixed-size in-place text slots, runtime font remapping, or DATA/ISO rebuilds.

Use `references/psp-pgd-dns-decryption.md` for PSP PGD/DNS archives, CRI DNAS key tables, EDAT-derived PGD keys, and DATA*.DNS decryption triage.

Use `references/photokano-psp-finalization.md` for PhotoKano PSP-style endgame cleanup: complete residual-Japanese audits, contextual terminology checks, EBOOT/runtime text handling, final DATA1/ISO verification, build artifact retention, and public open-source release boundaries.

Use `references/photokano-kiss-psv-cpk-gxt.md` for PhotoKano Kiss PSV / PCSG00139 work with CRI CPK rebuilds, CP932 slot-encoded text, GXT font atlas remapping, EBOOT UI text patches, Vita3K install/cache checks, and final VPK packaging.

For custom bytecode script work, require a `vm_analysis.md` before implementation. It must document opcode patterns, instruction lengths, operand schemas, sub-opcodes, variants, endianness, alignment, string/data blocks, and jump-offset bases. Treat that document as the single source of truth for both disassembly and assembly.

Implement three-file tooling when requested:

- `opcode.py`: complete opcode/schema definitions.
- `disassembler.py`: binary script to semantic `asm.txt`.
- `assembler.py`: `asm.txt` back to binary script.

The acceptance target is byte-for-byte round trip:

```bash
python disassembler.py sample.sc -o sample.asm.txt --encoding shift_jis
python assembler.py sample.asm.txt -o sample.rebuild.sc --encoding shift_jis
```

Then compare bytes and hashes. Fix opcode schemas or parser boundaries until the original and rebuilt file are identical.

## Encoding rules

Default candidate encodings for Japanese/Chinese Windows projects: `utf-8-sig`, `utf-8`, `cp932`, `shift_jis`, `gbk`. Treat `cp932`/Windows-31J/MS932 as a common practical match for many Japanese Windows scripts even when people casually say Shift-JIS.

Never rely on PowerShell default encodings for source-changing writes. Be explicit about encoding, BOM strategy, and newline style. When using PowerShell 5.1 and PowerShell 7+, account for their different defaults.

For semantic asm/string output, never use `\xNN` escapes for unprintable bytes. Use `{{XX}}` or `{{XX:YY}}` placeholders for exact raw bytes and parse them back as bytes during assembly.

## Outputs to produce

For planning or architecture tasks, produce an engine-specific workflow, risk boundary, tool list, expected artifacts, and validation plan.

For implementation tasks, produce scoped code plus tests or smoke checks for engine detection, encoding normalization, placeholder freezing, patch manifest generation, and rollback. For bytecode tasks, include round-trip byte/hash verification.

For release tasks, produce a patch manifest, original-file hashes, target-file hashes, install/apply instructions or scripts, rollback data, compatibility notes, third-party artifact audit decisions when applicable, and a machine-readable acceptance report bound to the exact final installer hash. If the user requests a graphical EXE installer, treat the requested artwork, original icon, compact window, exact progress semantics, drive-portable target selection, runtime bundling, and original-game compatibility as release acceptance requirements rather than cosmetic preferences. Avoid outputs that embed original commercial resources unless the user has clearly established authorization.
