# RealLive / AVG2000 Seen, G00, and Save-Safe Localization

Use this reference for RealLive or AVG2000-family Windows games that expose `RealLive.exe`, `Gameexe.ini`, compiled `Seen.txt`, `G00` images, file-based saves, or related `PDT`, `NWA`, `koe`, and movie assets. The rules below were validated while localizing a legacy RealLive title, but every binary constant and opcode meaning remains dialect-specific until proven on the exact target hash.

## Contents

- [Fingerprint the exact dialect](#fingerprint-the-exact-dialect)
- [Build a trustworthy Seen pipeline](#build-a-trustworthy-seen-pipeline)
- [Separate CP932 parsing from GBK output](#separate-cp932-parsing-from-gbk-output)
- [Patch native system UI by ownership](#patch-native-system-ui-by-ownership)
- [Diagnose and repair mid-text save resumes](#diagnose-and-repair-mid-text-save-resumes)
- [Localize G00 UI without breaking its layout](#localize-g00-ui-without-breaking-its-layout)
- [Prove window and registry behavior at runtime](#prove-window-and-registry-behavior-at-runtime)
- [Package optical and installed baselines transactionally](#package-optical-and-installed-baselines-transactionally)
- [Run release gates and clean up](#run-release-gates-and-clean-up)
- [Remember the recurring failure patterns](#remember-the-recurring-failure-patterns)

## Fingerprint the exact dialect

1. Inventory names, sizes, timestamps, and SHA-256 hashes before opening or rewriting anything. Treat these as useful RealLive-family signals rather than universal requirements:
   - `RealLive.exe`
   - `Gameexe.ini`
   - `Seen.txt`
   - `G00/*.g00`
   - `PDT`, `bgm/*.nwa`, `koe`, `MOV`, or similarly named media roots
2. Prove which executable and game tree the launcher actually uses. Similar Japanese, portable, localized, and test directories can make a correct patch appear ineffective when the user launches another copy.
3. Fingerprint `Seen.txt` instead of assuming a public format description matches. A known dialect used a 10,000-entry scene table followed by compressed scene blocks, scene headers, dramatis-personae records, kidoku/entrypoint metadata, control records, and branch pointers; another build may differ.
4. Derive the populated scene set, header sizes, codec, and element grammar from the input. Do not hard-code the scenario count from the main game into a bonus or another edition.
5. Determine the actual encoding and runtime owner of every string-bearing file. Original script/config strings are often CP932, while a localized runtime may consume GBK/CP936, but the filename alone does not prove either.
6. Keep profile-specific constants, expected counts, source hashes, and exclusions in a versioned manifest. Do not embed one title's hashes or counts in generic engine logic.

Before changing content, write a runtime-ownership matrix for at least: narration/dialogue, choices, speaker names, system strings, native dialogs, image UI, window behavior, launcher behavior, registry access, and save serialization. Route each symptom to its proven owner instead of treating every visible string as one text channel.

## Build a trustworthy Seen pipeline

### Establish the reader and writer

1. Parse the scene table, locate each populated compressed block, decompress it, and describe every header and script element before translating.
2. Make an inventory record carry at least:
   - target file and source hash
   - scene number and stable record ID
   - decompressed script offset
   - original bytes and byte length
   - original encoding and target encoding
   - speaker/context
   - element kind and control metadata
3. Write a no-op reassembler first. Require byte-for-byte identity with the input before trusting a translated rebuild. If the compressor is nondeterministic, require identical decompressed blocks plus an explicitly documented container-only difference; prefer deterministic output when possible.
4. Run a one-scene ASCII probe and a one-scene target-encoding probe before a full rebuild. Prove that table offsets, decompression, and element walking still work.
5. Do not start duplicate writers because an outer shell timed out. Inspect the active process, partial report, output timestamp, and final hash before deciding that a long-running rebuild failed.

### Preserve structure and control flow

1. Preserve scene headers, line and kidoku tables, ruby records, entrypoints, `SeenEnd`, padding, and control elements unless their schema is documented and deliberately rebuilt.
2. Treat full-width `SeenEnd` markers and trailing padding as protected binary structure, not translatable text.
3. Audit every discovered jump, branch, and gosub target. Require every new target to land on an exact parsed element boundary, not merely inside the scene range.
4. Require unchanged scene blocks to remain byte-identical after decompression. For changed blocks, record old/new decompressed lengths, compressed lengths, table offsets, element boundaries, and branch-target validation.
5. Teach the validator which structural changes are intentional. Prove the declared transformation first, subtract only those gated differences, and then require every remaining element, pointer, branch target, and non-target byte to match. Do not reject a valid repair merely because it deliberately materializes an additional boundary.
6. Keep source and target parsers separate when the encoding changes. A validator that sends target GBK bytes back through the original CP932 DBCS walker can invent false unterminated-string errors.

### Handle speaker tables separately

Some dialects store dramatis-personae names in the scene header rather than ordinary dialogue elements.

1. Preserve entry count and order.
2. Rebuild each documented length field, raw name bytes, terminator, and alignment exactly.
3. Update only proven header offsets.
4. Validate names through their own inventory and report; do not assume that a complete dialogue inventory includes them.

## Separate CP932 parsing from GBK output

1. Normalize translation data to UTF-8, but preserve the exact original CP932 bytes and the exact target GBK/CP936 bytes in the inventory.
2. Mark replacement byte ranges. Do not let a CP932 lead-byte classifier walk through a range already encoded as GBK. In one failure, a valid GBK trail sequence was mistaken for Shift-JIS and swallowed the closing quote.
3. Bind `Gameexe.ini` replacements to original offsets, bytes, and source hashes. Decode the original branch with its proven source encoding and validate the localized branch with its proven target encoding.
4. Patch all runtime DBCS paths that actually consume localized text, including text production, helper routines, ruby, draw, measurement, wrapping, backlog, and redraw. A correct font or one patched renderer is not sufficient when another path still advances through bytes as CP932.
5. Use a target-language charset and font route only after the byte stream is correct. Classify symptoms before changing fonts:
   - missing glyph boxes usually indicate font or charset coverage;
   - random CJK/mojibake usually indicates wrong decoding or code page;
   - literal `?` usually means an earlier lossy conversion already destroyed the source byte.
6. Run every PowerShell and Python text operation with explicit UTF-8 console output plus explicit file encodings. Use `python -X utf8` for project tooling and never trust the default Windows console decoder for Japanese paths or reports.

## Patch native system UI by ownership

RealLive system dialogs can come from several independent owners: compiled script, `Gameexe.ini`, G00 artwork, PE dialog resources, and fixed ANSI strings inside the executable.

1. Identify the owner of each visible string before editing. A garbled save dialog or exit prompt is not automatically part of `Seen.txt`.
2. Parse both classic `DLGTEMPLATE` and `DLGTEMPLATEEX` UTF-16 resources structurally. Rebuild controls inside the allocated resource size, zero-pad the unused tail, and verify the resource boundary.
3. Do not replace dialog captions by padding individual UTF-16 strings in place unless field boundaries are proven. A longer label can overwrite the following font-name field even when the whole resource still fits.
4. Patch fixed ANSI strings outside dialog resources separately with exact input bytes, length gates, and output hashes.
5. Keep an explicit exclusion for any intentionally unmodified diagnostic-only string, but do not use exclusions to hide player-visible unfinished localization.

## Diagnose and repair mid-text save resumes

### Recognize a logical parser stall

A save can load its background and current line yet stop progressing without crashing. A visible literal `#` at the line end is especially useful evidence in a RealLive dialect whose command marker is byte `0x23`.

Do not classify this as a corrupt save or frozen process until checking:

- process responsiveness and window message handling;
- Windows application/crash events;
- saved scene and program counter;
- bytecode bytes around the resume PC;
- parser state when starting at that PC.

One proven dialect serialized a dialogue element as:

```text
22 <GBK text> 22 23
^              ^  ^
quote          quote command marker
```

The save stored a scene plus a PC one byte after the opening quote, but did not serialize the active quote state. On reload, the closing quote became a new opening quote, the `0x23` command marker was consumed as literal `#`, and later commands disappeared. This explains a responsive logical stall without an OS crash.

### Forensically locate real save PCs

1. Back up `SAVEDATA` before experiments while preserving file bytes, attributes, creation time, and last-write time.
2. Map the visible line back to its translation record, scene, and decompressed local offset.
3. Decode save files in memory first. Search candidate aligned scene/PC fields by requiring:
   - a valid populated scene;
   - a PC within that scene's decompressed script range;
   - agreement with any saved bytecode snapshot or nearby prefix;
   - repeatable results across multiple saves.
4. Do not hard-code one save-field offset until the codec and record schema are proven.
5. Replay the lexical/parser walk from the exact PC against both the original and rebuilt `Seen.txt`. Record the first boundary, stop marker, unterminated state, and failure offset.

### Preserve PCs or declare a migration

The safest compatibility repair keeps every decompressed scene-local length and offset stable. In the proven dialect, a top-level comma byte `0x2C` was established as a zero-width separator, which allowed an equal-length lexical guard:

```text
22 <text> 22  ->  2C <text> 2C
"text"         ,text,
```

This made `element_start + 1` a valid text-output boundary after reload without moving later PCs. Treat this only as a dialect-specific technique:

1. Prove the comma's parser and rendering semantics on the exact executable and script version.
2. Apply it only to eligible narration/dialogue elements. Keep choices, system strings, name records, and control-bearing strings quoted unless separately proven safe.
3. Gate every changed outer byte by scene, record ID, original bytes, and source hash.
4. Permit same-length semantic corrections only when they preserve the exact byte count. If a correction changes length, either reject it from the save-compatible patch or ship an explicit versioned save migration.

Require the save-PC regression report to prove:

- every decompressed scene-local length and all original offsets remain unchanged;
- all original element boundaries remain valid;
- every supported mid-text resume PC is a newly valid text boundary where necessary;
- all branch targets still land on exact boundaries;
- only declared guard bytes and declared equal-length corrections changed;
- unchanged scenes remain byte-identical;
- replay of the old script reproduces the failure while replay of the repaired script stops exactly before the expected command marker.

Compare offsets in decompressed scene-local address space. A different compressed `Seen.txt` size does not by itself prove that save PCs moved, and an unchanged compressed size does not prove that lexical resume state is safe.

### Treat native save fingerprints as a separate contract

Stable scene-local offsets and equal-length edits are still insufficient when the native loader fingerprints code around the saved PC. One verified RealLive build stored the scene/PC together with a normalized 32-byte bytecode fingerprint, then searched for that fingerprint within roughly `PC ± 511` bytes on load. When the search failed, the engine could restore the background and line state but leave the interpreter PC at zero and stopped, which looked like a frozen load without an OS hang.

1. Reverse the exact executable's save and load routines. Prove the fingerprint length, normalization, search window, stack-frame handling, and failure state from the target hash; do not generalize the values above to another build without evidence.
2. Extract every supported save's main scene/PC and active nested frames. Compare the exact normalized fingerprint against original, current localized, and candidate scripts.
3. Require a matrix that records, for each frame, the stored PC, original match, current match, candidate match, matched offset, and first mismatching byte.
4. If a same-length semantic correction breaks a fingerprint, revert or rework that correction even when all later offsets and branch targets remain unchanged. Treat compatibility at the loader's fingerprint level as the release gate.
5. Preserve the user's save directory byte-for-byte during analysis and installer tests. A copied save used as a fixture is not permission to rewrite the live save.

Finish with an actual game test whenever possible: load an affected old save, advance, save again, exit, restart, and reload. If desktop automation is unavailable, record the dynamic test as manually pending; do not convert static evidence into a claimed UI pass.

## Localize G00 UI without breaking its layout

1. Detect the G00 subtype before editing. A project can contain simple RGB format-0 assets and segmented RGBA type-2 assets with region, block, part, and placement records.
2. Preserve the type-2 region/block/part structure when re-encoding. Require a pixel-exact decode of the rebuilt asset to match the intended edited pixels, and require every declared non-target pixel to remain identical.
3. Calibrate stored channels against runtime output. Some type-2 rendering paths display red and blue differently from a generic RGBA preview, so a correct editor preview can still be wrong in game.
4. For date/weekday graphics, edit only the intended weekday rows. Preserve digits, separators, and underlines. Match the original visual language with controlled glyph width, a thin outline, and restrained translucency; avoid solving legibility with an oversized font or broad Gaussian glow.
5. Patch the complete asset family, not only the asset visible in one screenshot. Hash-audit non-target UI assets to prove they did not change.
6. Inspect the manual, flags, and scenario logic before declaring a button or gallery missing. RealLive titles may unlock album/replay/order modes later, and a portrait-toggle button may update only on the next message rather than the current frame.

For gallery replay errors whose missing filename is assembled dynamically, audit the selector data flow before adding files. In one verified title, names followed a pattern like `LOFC1 + selector + 091`; an error for `LOFC1091.pdt` meant the selector was empty, while several plausible real assets such as `LOFC11091` and `LOFC13091` already existed. A blind alias would hide state corruption and could display the wrong event.

1. Find the gallery menu scene, every replay farcall target, and every dynamic filename construction site.
2. Prove that the selector variables are initialized to non-empty values on every path before the first control transfer. Compare original and localized call signatures and target sets.
3. Distinguish a normal gallery-entry path from replay reached through an old save, modified flags, or a partial patch state.
4. Do not inject length-changing bytecode guards merely to suppress the dialog when save compatibility is required. Such guards move later PCs and can fix one symptom while breaking resume fingerprints. Prefer a state-correct repair or leave the guard as an explicitly unshipped plan.

## Prove window and registry behavior at runtime

### Window mode

1. Treat `Gameexe.ini` screen-mode values as dialect-specific. In one final tested profile, `#INIT_SCREENMODE=1` selected windowed mode and `#ALT_ENTER_USE=0` disabled the toggle, but earlier assumptions and saved state obscured the result.
2. Verify a title bar, client dimensions, Alt+Enter behavior, restart behavior, and behavior after loading an existing save. Do not declare success from a config diff alone.
3. If config is insufficient, implement a separate exact-hash runtime force-window patch and keep it distinguishable from the text payload.
4. Launch relative to the game directory, such as through `%~dp0`; scan the launcher and final installer for build-drive paths.

### Registry-free behavior

1. Do not infer registry-free operation merely because saves live in files.
2. Snapshot relevant registry branches before and after, or capture exact registry operations with Process Monitor.
3. If a settings-write helper must be disabled, patch it as a separate exact-hash runtime layer while preserving required reads and file saves. Verify clean rollback.
4. Compare normalized before/after trees and keys owned by the target process. Do not delete an entire pre-existing vendor root or unrelated keys.
5. When the release is declared registry-free, require the patch installer itself to create no uninstall entry, patch-state key, vendor key, or other registry value in any mode, including HDD in-place install, copy-install, verify, and restore. Keep patch state in a manifest-bound file marker under the selected game directory and require a zero-diff registry acceptance report for installer-owned writes.

## Package optical and installed baselines transactionally

### Define baseline profiles

1. Support each proven original layout as its own exact profile, for example:
   - an installed retail-disc tree retaining `RealLive.exe`;
   - a previously prepared portable/no-registry tree with a renamed executable.
2. Detect profiles through hashes and identity anchors, not through a registry entry or a guessed folder name.
3. Permit alternative original hashes only when each alternative is declared in the manifest and converges to the same verified localized payload.
4. Map profile-specific executable names to a logical engine path such as `@ENGINE`, while retaining the exact source filename, input hash, output filename, and restore filename inside each profile.

### Support read-only media

1. Offer a copy-then-patch mode for ISO or optical media. Copy only a whitelist of runtime files and directories into a user-selected writable game directory.
2. Exclude setup programs, DirectX redistributables, test utilities, unrelated bonuses, and `SAVEDATA` unless evidence proves they are runtime requirements.
3. Never run the publisher setup or write installation registry keys in the copy mode.
4. Patch an existing writable HDD installation in place when it matches a supported baseline.
5. Quote drive roots safely in Windows command lines; prefer a normalized form such as `E:\.` when a trailing backslash could escape the closing quote.

### Make install, upgrade, and restore explicit

1. Back up every installer-owned file transactionally before replacement. Exclude save data from payload ownership and compare save hashes, lengths, attributes, and timestamps before and after each operation.
2. Bind a restore marker to patch ID, patch version, status, input profile, payload-manifest hash, touched-file count, and actual engine filename. Do not treat any marker with a familiar ID as proof that the installed payload matches the current version.
3. For a live upgrade, use the old installer to restore its own version, verify the original baseline and removal of the old marker, then install and verify the new version. Keep the old installer until this migration path passes.
4. Distinguish `ALREADY_LOCALIZED` from a newly successful install. A CLI may return exit code `0` for both; require a machine-readable report whose operation result is exactly `code=OK` when testing a fresh install or upgrade.
5. For a GUI-subsystem installer invoked from PowerShell, use `Start-Process -Wait -PassThru` and inspect its `ExitCode`; do not trust `$LASTEXITCODE`.
6. If the caller times out while an independent installer continues, inspect the process, last progress record, final report, and target hashes before retrying. Prevent duplicate copy/install workers.
7. Make progress monotonic from 1 through 100. Emit 100 only after target commit and final verification succeed; byte-copy completion alone is not installation completion.
8. Separate core-payload validity from installer-owned auxiliary files. A modified launcher or readme is user data once its hash no longer matches the marker; restore should preserve it while removing only exact owned copies.
9. Treat a valid committed current-version marker plus an exact restore tree as the commit signal. Never infer "interrupted upgrade" merely because a live Seen/G00/core file no longer matches; that mismatch may be a user's later modification. Auto-rollback only when the live old marker, old payload, auxiliary files, and isolated upgrade backup all match the proven pre-upgrade state. Otherwise stop without writing and retain evidence.
10. Walk `SAVEDATA` with an explicit stack. Reject each directory and file reparse point before descending or hashing; `Directory.GetFiles(..., AllDirectories)` can traverse a junction before validation and can miss an empty junction.
11. Fail closed when the installer cannot inspect a same-name running process. Swallowing a `MainModule` access error can permit writes while the game is active.
12. Design transaction names for legacy .NET path limits. Use short stage prefixes and short random sibling temp names; never append a GUID-sized suffix to an already long preserved filename. Calculate the peak path after moving the complete patch/backup tree, and exercise the same path during reverse rollback. A forward copy that fits can still leave rollback or cleanup over 260 characters.

Run this acceptance matrix before release:

- portable-original install, verify, and restore;
- retail-original install, verify, and restore, including read-only file attributes;
- actual mounted ISO or optical copy-install, verify, excluded-file audit, and restore behavior;
- previous-release to current-release live migration;
- save-data invariance across every case.

Label evidence by layer: structure/save-PC simulation, installer transaction, real-directory migration, and actual in-game interaction. Preserve `NOT_RUN` or `MANUAL_PENDING` for any missing dynamic step; never let three static layers of `PASS` imply that a user actually clicked load and advanced successfully.

## Run release gates and clean up

Bind the final build to evidence, not just a successful compiler exit:

1. Gate exact source hashes and lengths.
2. Bind Seen structure, translation, G00 pixel, system-UI, and save-PC QA report hashes into the payload manifest.
3. Rehash every embedded resource after compiling the installer.
4. Rehash source inputs again after compilation to close the time-of-check/time-of-use gap.
5. Scan the final executable, scripts, and configs for absolute build paths and unexplained drive prefixes.
6. Scan the exact final installer hash and record the result.
7. Verify the exact final release path, hash, payload count, manifest identity, and rollback route.
8. Make report formats self-describing. Match extensions to content (`.json`, `.jsonl`, `.tsv`) and include a schema/version field so later audits do not parse a TSV file merely because it was named `.json`.

Any change to `Seen.txt`, a G00 asset, `Gameexe.ini`, the runtime executable, or an accepted original profile invalidates downstream save-PC reports, payload manifests, embedded resources, installers, static audits, and final release manifests. Rebuild and rebind all affected artifacts before cleanup.

Before cleanup, publish explicit keep/delete lists. Preserve:

- the final installer and checksum;
- one complete playable localized game tree;
- original media or an immutable original baseline;
- translation sources, build tools, manifests, and QA reports;
- rollback inputs and save backups;
- the current successful build and only the necessary rollback version.

Delete only proven project-generated leftovers: superseded candidates after migration succeeds, test clones, stale extraction/rebuild directories, caches, and duplicate complete game trees. Verify afterward that exactly one retained playable tree contains the engine executable plus its required media roots. Never run a cleanup script whose whitelist or release identity still targets an older version.

## Remember the recurring failure patterns

- **Hard-coded scene count:** a tool validated one edition but produced hundreds of false errors on another. Derive the scene set from the file and keep per-profile expectations outside generic logic.
- **Source parser reused on target bytes:** CP932 DBCS rules swallowed a valid GBK trail byte or closing quote. Mark target ranges and validate with the target grammar/encoding.
- **Protected trailer parsed as dialogue:** `SeenEnd` and padding were treated as text. Exclude proven structural records before decoding.
- **Config-only window claim:** saved state or runtime code overrode an apparently correct `Gameexe.ini`. Verify the live window after restart and save load.
- **Wrong tree launched:** multiple similar directories made fixes appear missing. Trace the executable path and keep one complete release tree.
- **Shell timeout mistaken for build failure:** a writer or installer kept running and a retry created duplicate work. Check process/report/output state first.
- **Desktop automation unavailable:** static and parser evidence remained valid, but the in-game test was not complete. Mark the manual test pending instead of claiming success.
- **Brittle PowerShell display pipeline:** `foreach { ... } | Format-Table` can raise an empty-pipe parse error in Windows PowerShell. Collect objects into an array or list, then sort and format them.
