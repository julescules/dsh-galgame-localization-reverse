# Director 8/8.5 multi-baseline localization and single-EXE patches

Use this reference for legacy Windows visual novels built with Macromedia Director 8 or 8.5, especially when one supported copy is a self-contained Projector while another already uses an external movie, source-mode marker, and `Xtras` directory.

## Contents

1. Prove the runtime shape first
2. Keep localization data separate from runtime compatibility
3. Use exact, unique baseline matching
4. Represent both replacement and creation
5. Director text, font, UI, and save QA
6. Build a reproducible single-file Windows installer
7. Acceptance tests
8. Release and cleanup policy
9. Failure lessons

## 1. Prove the runtime shape first

Inventory the target without changing it. Hash all version-defining files and record the complete runtime layout.

Common evidence includes:

- a Projector executable plus `.dcr`, `.cct`, media, or script-resource files;
- an external `.dir` movie, `Xtras/*.x32`, an INI file, or a source-mode marker;
- the same data files paired with executables of different sizes or hashes;
- a raw release that launches without an external `.dir`, while a localized build requires one.

Treat these as different source baselines, not as a single version with an optional marker. If an installer rejects a raw release because the external movie is absent, do not merely relax the marker check. Determine whether the localized runtime must externalize the movie and supply the matching Xtras/configuration as a baseline-specific adapter.

An Xtra embedded in a Projector can be a Director wrapper such as `XtraFILE`, not a directly loadable PE. When externalizing it, unwrap and validate the resulting x86 `MZ/PE` file, length, and hash rather than renaming the embedded blob.

Launch with the game directory as the working directory because playlists and media commonly use relative paths. Director 8.5 also has ANSI-path failure modes: when a Chinese path correlates with a black screen, perform a controlled Chinese-path versus short ASCII-path A/B test before declaring the cause or imposing an ASCII-path requirement.

### Proven extraction route and its limits

A successful Director 8.5 route was:

1. separate any outer wrapper from the nested Director Projector;
2. parse the Projector/APPL resource map to extract the embedded startup movie and Xtra blobs;
3. use ProjectorRays to decompile the embedded movie to `.dir` and casts such as `.dcr`/`.cct` to inspectable `.dir`/`.cst` forms;
4. unwrap each RIFF `XtraFILE` zlib payload and require a valid x86 `MZ/PE` result;
5. generate a report containing input/output lengths and hashes, then launch-test the complete set rather than testing Xtras individually.

Use a short ASCII workspace on the non-system drive for old Director tools. ProjectorRays 0.2.0 was observed to reject a Chinese output path and to misdecode a few Japanese member-directory names even though the important Lingo/JSON output remained usable.

Source every runtime adapter from the same authorized build or from a baseline whose exact compatibility has been proven. Never borrow an unrelated `.dir` or Xtra set merely because the filenames match. ProjectorRays and DirectorCastRipper are valuable extraction/inspection tools, but they are not a general Director cast compiler; prove the writeback or round-trip route separately.

### Proven constrained writeback patterns

For uncompressed `XFIR` Director files, a resource-aware fixed-length patcher is safer than an assumed general compiler:

- parse `mmap`, `KEY*`, `CAS*`, `Fmap`, `STXT`, `XMED`, and related chunk boundaries;
- patch only an exact expected input hash and refuse in-place output or overwrite;
- keep file length, chunk lengths, resource IDs, and the resource map unchanged;
- require each intended slot to match exactly once;
- reparse the output, verify the expected output hash, and prove every byte difference is confined to declared resource ranges.

This worked for shorter ASCII font aliases in existing `Fmap` slots, equal-byte-length CP932-to-GBK `STXT` replacements, and narrowly scoped `XMED` layout fields. It is not permission to make arbitrary variable-length edits. When a replacement does not fit, use a proven resource rebuild or an engine-supported external text route instead of shifting unknown chunk offsets.

For image-backed UI, export members for translation, patch through a resource-specific importer, then re-export the final cast and require manifest/hash plus pixel-level round-trip checks for every changed member. For encrypted or transformed external scripts, first require a zero-mutation byte-identical decode/encode round trip; when a verified source-mode switch exists, external plaintext scripts can be a lower-risk localization path.

Record the exact tool version, command line, input/output hashes, and machine-readable report schema for every extraction or writeback step. Keep project-specific scripts with the build source; the reference describes acceptance properties, not a universal Director compiler.

## 2. Keep localization data separate from runtime compatibility

Model the patch in two required layers and one optional layer:

- `common payload`: final localized scripts, cast resources, UI assets, executable/resource changes shared by every supported baseline;
- `runtime adapter`: files needed only to transform a specific baseline into the runtime shape expected by the common payload.
- `optional media layer`: independently selectable HD, restoration, decensor, or large image-container changes that are not required for translated text or runtime compatibility.

A raw Projector adapter may replace its runtime INI and create an external movie, source-mode marker, and `Xtras` files. A baseline that already has that layout may need no adapter mutations.

Do not package user-specific save files, account credentials, genuine license blobs, purchase tokens, device secrets, or unrelated user state. Never place save/progress patterns such as `*.dat`, `*.sav`, or `*.osv` into cleanup or rollback ownership merely by extension or historical filename. If an identically named runtime configuration file is truly patch-owned, bind that one exact path to a documented schema and baseline hash instead of using a wildcard. If a user-owned secret is genuinely required, read it at runtime from the original launcher, OS credential store, or an external user-local configuration without duplicating it in the package or logs. A DMM/SoftDenchi or equivalent authorization bypass may package a project-local loader, hook, compatibility stub, service/protocol emulator, launch shim, or synthetic non-user-specific authorization state when it is declared in the manifest and bound to exact baseline hashes. Classify runtime configuration and synthetic bypass state separately from user state.

Classify text files by runtime ownership rather than the `.txt` suffix. A README, manual, changelog, credits file, or other non-runtime document is not a version-defining game-core input: leave it out of source detection, payload, backup, rollback, cleanup ownership, and ASCII-filename normalization unless concrete engine access proves otherwise. Preserve the user's original documentation name, bytes, timestamps, and attributes through verify, install, failed install, upgrade, and rollback. This exclusion is not a wildcard for all text files: retain and hash-bind engine-consumed scripts or configuration such as NScripter `0.txt` when runtime evidence establishes ownership.

Never use an experimental media layer as the only carrier for required text/runtime changes. Track its asset IDs, container slots, input/output hashes, and black/blank-frame counts separately. When mapping is wrong, pixels remain censored, or the game black-screens, fail that layer without invalidating an otherwise working localization. If the user decides to use the original images, remove every media mutation and derived mapping table from the runtime payload, rebuild the installer, and assert the original large data containers remain unchanged during install and launch.

Treat “sharper at the original resolution,” “upscale,” “restoration,” and “decensor” as different scopes. Do not infer permission for one from another. A user decision to stop HD or decensor work becomes a hard packaging exclusion.

## 3. Use exact, unique baseline matching

For every supported baseline, store exact SHA-256 and length for enough files to distinguish it. Detection should return exactly one of:

- one source baseline;
- the already-installed final state;
- unsupported or mixed state.

Reject zero matches, multiple matches, partial installs, and mixtures of source/final files. Never choose a baseline because one filename exists.

A verify-only action must remain read-only: it may report the detected baseline and planned mutations, but must not create a backup or change target hashes.

The installed-state test must verify both layers:

```text
installed = all common final hashes match
            AND selected baseline's runtime final hashes match
```

Keep the manifest deterministic: normalized relative paths, explicit operation type, original/final length and hash, and a stable order.

## 4. Represent both replacement and creation

Legacy-runtime adapters often create files that did not exist in the raw game. A replacement-only backup model cannot safely roll these back.

Use a manifest schema with fields equivalent to:

```json
{
  "schemaVersion": 2,
  "sourceBaselineId": "raw-projector",
  "status": "backup_complete",
  "createdDirectories": ["Xtras"],
  "files": [
    {
      "path": "GAME.INI",
      "operation": "replace",
      "existedBefore": true,
      "backupRelativePath": "original/GAME.INI",
      "originalSha256": "...",
      "installedSha256": "..."
    },
    {
      "path": "GAME.dir",
      "operation": "create",
      "existedBefore": false,
      "backupRelativePath": null,
      "installedSha256": "..."
    }
  ]
}
```

Rollback rules:

- `replace`: restore the backed-up original and verify its hash;
- `create`: delete only when the current file still matches the installed hash;
- conflict: preserve the changed file, or move it to a clearly named conflict copy only in an explicit force mode;
- created directories: remove only when empty;
- never infer deletion solely from a filename.
- save/progress files: keep them outside ordinary patch ownership. Leave their bytes and timestamps unchanged unless a proven format incompatibility requires a separately declared, reversible migration; never treat a wildcard save extension as permission to rewrite or delete user state.
- a portable localized tree that matches the payload hashes but lacks the exact `active_state.json` and per-file original backups is not an installed state. Detect it explicitly and fail closed with a precise explanation; never synthesize rollback metadata or treat localized payload files as originals.
- restoring such a stateless portable tree requires an authorized original source or a reverse delta containing the missing original bytes. Measure and report the real delta/package size before promising a compact self-contained rollback; keep the small installer contract when the reverse data would materially increase the package.

Use a durable state transition such as:

```text
backup_complete -> installed_and_verified -> rollback_complete_and_verified
```

On an installation error, restore completed mutations in reverse order and record a distinct failure state such as `install_failed_auto_rollback_verified`; do not relabel an incomplete operation as installed.

Automatic rollback selection must consider only `installed_and_verified` records for the exact target path. A failed or incomplete backup must never become the default rollback candidate.

## 5. Director text, font, and UI QA

Normalize editable text through UTF-8, but preserve the engine's required output encoding, line endings, delimiters, and control bytes. For Japanese/Chinese Windows builds, explicitly test `cp932` and `gbk`/`cp936`; never trust the PowerShell console default.

For PowerShell 5.1 scripts containing non-ASCII literals, write UTF-8 with BOM and launch the known `powershell.exe` path. Set console output to UTF-8 for diagnostics, but do not mistake console encoding for the game's resource encoding.

Director games may split visible text among script resources, cast members, bitmap UI, and executable/window resources. Audit all of them:

- dialogue and choice text;
- main menu, save/load, CG/recollection, settings, back/exit labels;
- title-bar/version resources;
- bitmap-baked Japanese and cast-member text;
- residual kana and mojibake after repacking.

Preserve control tags and byte structure. After every rebuild, check glyph coverage, baseline position, clipping, line wrap, choice-box width, and every affected UI screen. Once dialogue layout is accepted, freeze its known-good font size and vertical offset while fixing unrelated UI.

### Prove mojibake from the owning bytes

When a localized runtime displays mojibake, locate the exact stored byte sequence before changing fonts or repainting the dialog. Decode the same bytes under the expected source code page and the candidate runtime code page. If the incorrect decode reproduces the on-screen mojibake exactly, record that as causal evidence and patch the owning resource rather than the screenshot symptom.

Search for every structured copy of the string. Director casts can keep executable Lingo data and metadata/index copies, such as `Lscr` data plus an `ILS`-like copy. Do not assume the first match is the only runtime-relevant match. For constrained fixed-layout patches:

- require an exact input hash and declared resource ranges;
- require the replacement to have the same encoded byte length;
- record the expected old and new match counts;
- reparse the result and require the old-byte count to be zero and the new-byte count to equal the expected count;
- prove that no byte outside the declared resources changed.

Treat `Lscr`, `ILS`, and the number of copies as observations, not universal constants. If equal-length replacement is impossible, use a proven resource rebuild instead of shifting unknown offsets.

Trace every visible choice or backlog string through all ownership layers. A Director title can combine external translated source files, `STXT` defaults, and `XMED` field-layout metadata; fixing only the external string leaves the cast default or runtime charset wrong. Reparse `mmap`/`KEY*` associations, patch only the named resources, and independently read back each layer.

Do not infer a Windows charset from an `STXT` style tail. Values such as big-endian font ID `0x8002` belong to the cast font map and must remain byte-exact unless the font mapping itself is the target. In textual `XMED` records, `PG_CHARSET` may instead appear as encoded decimal digits: prove the field grammar, then change the complete value (for example, `80` for Shift-JIS to `86` for GB2312) and verify the surrounding record, rather than blindly replacing raw byte `0x80` with `0x86`.

### Treat image-backed UI as stateful binary data

Treat importer fidelity and asset correctness as separate gates. A byte-confined write plus exact decode/re-export proves that the importer preserved the supplied image; it does not prove that the supplied image has a clean background, distinct interaction states, readable typography, or correct scaled rendering.

Create a member/state inventory before editing bitmap UI. Map each normal, hover, pressed, selected, and disabled state to its member ID, visible rectangle, source hash, and translation policy. Record intentional exclusions, such as a user-approved English title menu or a proper name that must remain unchanged, and verify those members against their frozen source pixels after every rebuild.

Do not erase source text with a row or column median when glyphs occupy most of the sampling region; the text can contaminate the estimator and become horizontal or vertical bands in the final button. Prefer a clean source background, a paired state with the same frame, reconstruction confined to the original text box, or retention of readable original text when that is the approved policy. Require every translated glyph to stay inside the original frame and audit the frame for residual Japanese rather than judging only the new text layer.

Compare visible RGBA pixels, the alpha plane, and hidden RGB under fully transparent pixels separately. Legacy Director scaling or filtering can leak nonzero RGB from pixels whose alpha is zero as colored edge fringes. Normalize hidden RGB only when the target renderer demonstrates the problem, then verify that visible pixels and alpha remain unchanged.

When the approved policy is “use the original menu image,” do not recreate it from a PNG export, repaint it, normalize transparent pixels, or recompress it as a substitute for restoration. Start from a pristine container or copy the original `BITD`/`DTIB` resource slot by section ID. Require the original payload, chunk header, slot interval, and `mmap` entry to be byte-exact in the rebuilt container, and require zero changes outside the separately declared localized members.

For translated button labels, derive the glyph treatment from the original state instead of choosing an approximate fill and outline. Measure the original text core, antialias ramp, outline colors, and glyph bounds; repair only the original text box; preserve the frame, alpha plane, and pixels outside a tight glyph mask. Compare color counts or histograms as well as visual contact sheets, then confirm the same style in a Stage capture.

For fixed-slot `BITD`/PackBits imports, require all of the following:

- the encoded payload for every member fits its original slot capacity;
- the intended member count matches exactly, including every interaction state;
- all byte differences stay inside the declared target resources;
- in-memory decode and final re-export reproduce the approved pixels;
- a real Stage capture confirms clipping, state changes, scaling, and absence of source-language residue.

### Separate asset sharpness, Stage scaling, and translucent overlays

When localized bitmap text looks foggy, do not keep repainting the glyphs until the rendering layer is identified. Test three causes independently:

- compare the decoded source member with the final re-export at native resolution to detect importer or asset blur;
- measure the real Stage client area and process DPI awareness to detect Windows bitmap scaling;
- inspect message-window blend, ink, alpha, and hidden RGB to detect a translucent overlay softening otherwise sharp text.

For pixel-art or binary-edged UI, preserve the native member dimensions, disable resampling, and prefer an embedded System-DPI-aware manifest while keeping the Director client at its authored size. Require an actual Stage capture at 100% scale; a sharp PNG or exact `BITD` readback alone does not prove sharp runtime rendering. If the approved title menu is the original English artwork, restore its raw source slots byte-for-byte instead of attempting a visual recreation.

### Treat close-button handling as a script/Xtra state machine

If the title-bar X is inert while an in-game Exit button works, trace `exitLock`, `startquitmsg()`, the `quitMsg` Xtra, the global lock tested by the Lingo `quitmsg` handler, and every assignment to that lock. Do not replace the workflow with a hard process kill or simply disable graceful cleanup.

For a fixed-layout compiled `Lscr` repair:

1. identify the exact handler, compiled offset, opcode, operand, and target global from a `.lasm` dump;
2. cross-check the opcode grammar against ProjectorRays or another primary implementation;
3. patch through the `mmap` section plus resource-local offset, never an unbound whole-file offset;
4. require a unique instruction context, exact input/resource hashes, unchanged container length, and only the declared byte difference;
5. dump the patched cast again and require the semantic line to show the intended value;
6. test `X -> No` for process survival, then `X -> Yes` for graceful save and exit.

### Make `value()` save text DBCS-safe

Legacy Director games often serialize a property list with `string()` and reconstruct it with `value()`. Audit the serialized bytes under the player's actual Windows ANSI code page, not only under CP932. A quoted field containing arbitrary cipher bytes can be valid in Japanese Windows yet malformed in CP936: a lead byte immediately before `0x22` can consume the closing quote and make `value()` return `VOID`.

Use these rules:

1. Decrypt a failing save with the exact engine/Xtra codec and prove a byte-perfect decrypt-encrypt round trip before interpreting fields. Do not blame translated words or filenames until their byte sequence is found inside the serialized plaintext.
2. Enumerate every dynamic quoted field. Check strict decoding and lead/trail-byte boundaries for CP932 and the target ACP; include probes whose final high byte is followed by the closing quote. Protection/checksum fields deserve the same audit as visible text.
3. Never place arbitrary binary output directly inside a quoted `string(proplist)` value. Serialize it as ASCII decimal, hexadecimal, or Base64, or omit it and recompute it after loading. Preserve the original validation semantics rather than disabling the check.
4. Patch new saves and migrate old saves together. Locate a unique schema-bound field anchor, decode only that field with the proven inner codec, require the replacement to satisfy a narrow invariant such as ASCII digits, then re-encode the outer container.
5. Make migration atomic and idempotent. Back up each original save outside the game directory with original/migrated hashes and metadata; skip already-safe values; reject ambiguous anchors, invalid checksums, reparse points, or unexpected codecs. On rollback, restore only when the current hash still equals the recorded migrated hash so later player progress is never overwritten.
6. Test manual save, quick save, preview/list parsing, manual load, quick load, install failure recovery, repeated installation, and rollback. Keep runtime saves excluded from the core version manifest even when a separate migration ledger owns only the exact files it changed.

When a patched isolated copy behaves differently from the user's game, hash the exact directory and executable the user launched before changing the logic again. A successful isolated deployment is not evidence that the live target received the new cast.

### Gate compressed Afterburner GDATA writeback separately

Director `XFIR/FGDC` casts with `Fver`/`Fcdr`, compressed resource streams, and `ABMP` metadata are not covered by an uncompressed `imap/mmap` fixed-slot patcher. Before editing them, prove a non-sensitive single-member round trip:

- resolve member -> `CAS*` -> `KEY*` -> `BITD`/`ALFA` ownership;
- decode the outer compression and inner PackBits planes and compare them with the clean export;
- recompress with recorded zlib parameters and require the compressed length to stay fixed for a fixed-slot probe;
- materialize an isolated full-size candidate, reparse every resource, and prove non-target byte changes are zero;
- delete the large materialized probe after compact hashes and reparse evidence are saved.

This gate proves only same-dimension, same-slot replacement. A 2x/4x asset changes dimensions, pitch, resource lengths, compressed sizes, and `ABMP` offsets; require a complete variable-length Afterburner rebuilder or keep the upscale external/realtime. Do not label a white alpha `MASK` or a mosaic-shaped overlay as uncensored source pixels. First test whether aligned frames or layers contain exact missing RGB; if exact and partial recovery counts are zero, describe later reconstruction as inferred/redrawn rather than restored.

## 6. Build a reproducible single-file Windows installer

A practical legacy-game patch can be a C# WinForms executable compiled with the installed .NET Framework compiler. Embed:

- one deterministic ZIP containing the patch engine and payload;
- the ZIP SHA-256 as a resource or build constant;
- the game's original icon with `/win32icon`;
- version metadata that distinguishes patch version from installer revision.

### Treat the requested installer experience as a release contract

When the user asks for a graphical EXE package, default to these acceptance requirements unless explicitly changed:

- double-click opens a native installer form; quiet CLI actions remain available for automated testing;
- keep the window compact while showing a baseline-bound original game image without crop or distortion;
- compile with the original game's complete icon resource set, not a generic or single-frame substitute;
- provide target browse, original verification, install, rollback, and exit controls;
- drive the visible progress bar from real processed bytes and, when requested, emit every integer from 1 through 100;
- accept only a hash-proven original baseline and show a clear unsupported/mixed-state error before target writes;
- bundle the replacement Projector, Xtras, fonts, and other authorized runtime pieces needed to make that baseline launch, and declare every remaining external dependency;
- when the user prohibits C-drive output, keep builds, payload staging, fixtures, traces, screenshots, logs, rollback data, and child-process `TEMP`/`TMP` on the selected non-system drive;
- record Authenticode status. Distinguish an unsigned “unknown publisher” prompt from a missing runtime error.

Original artwork in the form is not authorization to change the game's image payload. Embed only the approved installer asset and keep optional HD/decensor content outside the accepted payload unless separately requested and validated.

Keep that distinction visible in the compiled GUI too. A reusable installer engine revision such as `r3` may remain in the window title or product metadata, but the prominent patch label must match the embedded payload version. Render the exact final EXE and reject stale labels such as a previous `v3` title on a `v4.1` payload, even when installation and rollback tests pass.

### Bind visible release artwork to the exact game identity

Do not select a banner, title image, or installer background only because its filename is nearby, its dimensions fit, or it resembles the same series. Legacy Director trees can contain assets from a predecessor, related title, launcher, or reused cast. Inspect the actual pixels and visible title, then bind the approved asset to its exact game identity, source path or member ID, byte length, hash, format, dimensions, and decoded-pixel hash.

Render the exact canonical EXE and inspect the title glyphs, subtitle, version label, controls, crop, and contrast. Reverse-extract the embedded artwork and require it to match the approved input. A resource self-test can prove that the wrong image was embedded intact; it cannot prove that the image belongs to the target game. Treat an identity mismatch as a release-blocking asset error, replace the build input, and rebuild the EXE rather than patching the promoted binary.

The wrapper should:

1. validate its embedded ZIP before extraction;
2. reject absolute paths and `..` traversal in ZIP entries;
3. extract work files under a project/support directory on the user's chosen non-system drive;
4. run a package self-test before touching the game;
5. invoke the patch engine by absolute path;
6. expose GUI actions for version check, install, rollback, and exit;
7. expose quiet CLI actions for automated verification;
8. keep durable backups/logs outside ephemeral work directories;
9. remove transient extraction directories on success and handled failure.

Prefer reading a deterministic embedded ZIP directly from the EXE resource when the installer engine can stream entries safely. This eliminates an avoidable extraction tree. Still validate the whole ZIP hash before target writes, reject duplicate/case-colliding names plus absolute or traversal paths, validate each entry length/hash, and compute the full progress denominator before mutation. If a child runtime really extracts temporary modules, bind `TEMP` and `TMP` to a named directory under the game/support root and verify its module provenance during launch.

If an authorized build uses original game artwork as the installer background, bind it to the source baseline, relative path, byte length, file hash, format, dimensions, and decoded pixel hash. Preserve aspect ratio and controls' safe areas. If the image is embedded, reverse-extract it from the canonical EXE and require byte equality or, when the compiler legitimately transforms it, decoded-pixel equality. Capture the compiled GUI and check crop, scaling, text contrast, and control occlusion rather than accepting the source image alone. Treat the artwork as a deliberate release asset, not an untracked convenience copy.

Preserve the original Windows icon as a resource set, not merely as the one frame selected by the shell. Parse `RT_GROUP_ICON` and every referenced `RT_ICON`, reconstruct the complete ICO while retaining frame order and raw image bytes, and store group ID/language, dimensions, bit depth, resource hashes, and decoded pixel hashes in a manifest. `ExtractAssociatedIcon()` is useful as a secondary visual check but is not a complete extractor because it commonly returns one selected frame. Compile with `/win32icon`, then reverse-extract the final installer and require every frame—and preferably the complete ICO hash—to match the approved source.

Drive install and rollback progress from actual processed bytes, never from a timer. Define the denominator deterministically for each action and phase, use an integer type large enough for the full payload, compute the total before mutation, and keep completed bytes monotonic. Always require final progress `100` and `completedBytes == totalBytes` at successful completion; a failed or cancelled action must never emit `100`.

When the product contract promises every positive integer from `1` through `100`, emit every crossed threshold even when one file crosses several percentages. Then require first positive progress `1`, presence of `50`, final progress `100`, and no missing positive percentage for both install and rollback. A UI that permits throttled or skipped percentage labels need not satisfy this optional coverage rule, but its reported percentages must still be derived from the byte counters. Preserve a TSV or JSON trace with action, sequence, phase, relative path, completed bytes, total bytes, and percentage, then hash the trace.

Compute the denominator separately for each action and detected state. Source verification, installed verification without a backup, installation with source reads/staging/backups/final verification, and rollback from installed or recovery states do not necessarily process the same bytes. Enumerate every counted phase before mutation, then require the final phase to satisfy `completedBytes == totalBytes`. A bar that reaches `100` using a shared or stale denominator is a failed candidate even when file hashes happen to pass.

Do not promote an infrastructure-only build after its embedded runtime becomes stale. Mark icon-only, GUI-only, or packaging probes as non-final, rebuild from the current runtime manifest, and repeat package self-test plus install/rollback acceptance.

Do not inherit release evidence from an earlier EXE merely because the builder and assets are unchanged. Every canonical installer hash must have its own background extraction or pixel proof, full icon reverse-extraction, install and rollback progress traces, package self-test, and final-EXE fixture cycle. Link those artifact hashes from the release manifest or acceptance report.

Do not rely on `%TEMP%` when the project must avoid the system drive. Set `TEMP` and `TMP` for child processes to an explicit work directory on the target/support drive.

PowerShell 5.1 can silently corrupt non-ASCII release filenames when a build script containing Chinese/Japanese literals is saved without a BOM. Save such scripts as UTF-8 with BOM or construct critical names from Unicode code points, then enumerate the release directory and compare the exact expected filename before promotion. A correctly functioning EXE with a mojibake filename is a failed candidate, not an acceptable alias.

Useful CLI shape:

```text
Patch.exe --action verify   --target <game> --support-root <dir> --quiet
Patch.exe --action install  --target <game> --support-root <dir> --quiet
Patch.exe --action rollback --target <game> --support-root <dir> --quiet
```

When invoking PowerShell through encoded commands, capture stdout, stderr, and exit code independently. PowerShell may emit CLIXML on native redirection paths; sanitize it only for display and keep the raw log for diagnosis.

## 7. Acceptance tests

Label every report with its evidence scope and the exact installer size/hash, payload/build manifest hash, target baseline, action actually executed, timestamps, exit code, and linked trace/report hashes. Keep `fixture install-and-rollback`, `real-target install`, and `real-target rollback` as distinct claims. The existence of a rollback-state file proves rollback readiness, not that a real-target rollback was executed.

For every supported baseline, use a disposable fixture and complete this cycle:

1. verify source baseline and planned mutation count;
2. install;
3. verify every final hash and installed state;
4. launch long enough to enumerate windows and detect immediate failure;
5. rollback;
6. verify original hashes and absence of adapter-created files;
7. confirm save, account-credential, genuine-license, and unrelated user-state hashes never changed; verify declared synthetic project-local bypass state separately.

Assert that step 1 created no backup and changed no target file.

Maintain a small compatibility matrix covering Projector version, startup movie hash, runtime configuration, Xtra-set hash manifest, common-payload version, and launch result. A successful extraction plus one brief launch is evidence, but not enough to declare cross-baseline runtime compatibility.

Run the cycle both through the patch scripts and through the final EXE. Also test:

- one deliberately modified baseline file;
- a mixed or partial installation;
- a corrupted embedded package or payload file;
- rollback with a user-modified created file;
- GUI smoke tests, version/icon metadata, and clean process exit.

For the exact final EXE hash, additionally require:

- self-test of the embedded manifest, payload ZIP hash, file count, artwork hash/dimensions, and installer metadata;
- reverse extraction of the complete embedded payload plus artwork and icon set, with hash comparison to the approved build inputs;
- a read-only verify against the real unmodified original, proving file count/bytes/key hashes are unchanged and no backup/state directory was created;
- a full-copy fixture install, installed-state verify, real launcher start, rollback, and byte/hash restoration;
- loaded-module provenance during launch: non-Windows runtime modules must come from the game/support directory or an explicitly declared dependency;
- exact 1-100 trace validation for every action covered by that contract, including first `1`, present `50`, final `100`, monotonic completed bytes, and `completed == total`;
- negative probes for a modified original file, a user-modified installed file during rollback, and a corrupted embedded ZIP. Each must fail closed without damaging the canonical EXE or original target.

If packaging acceptance intentionally omits a new game launch because the exact payload already has a separate runtime acceptance, label the final-EXE report `game_was_not_launched` and link the earlier result by exact installed-file or payload hashes. Do not convert inherited payload evidence into a claim that the canonical EXE was launch-tested. The exact final EXE must still complete self-test, source verify, fixture install, installed-hash verification, rollback, negative probes, resource reverse-extraction, and GUI rendering.

If the Windows screen-capture/control backend fails, do not continue with blind clicks. Prove that the real final EXE opens, then use a read-only native WinForms render or equivalent deterministic layout render to inspect crop, overlap, contrast, labels, progress, and buttons. Record the capture limitation separately; do not mislabel the offline render as a screenshot of the running final process.

Old Director processes can expose an outer Projector window and a separate Stage window. Enumerate all top-level windows owned by the process ID instead of trusting only `MainWindowTitle`. Confirm the expected localized title and absence of error dialogs.

Do not capture the title screen after a fixed sleep when the game has a splash, movie, or variable initialization delay. Poll a stable visual marker, window state, or known title-member pixel with a timeout, then capture the title and at least one interactive dialog. Close only the process tree started by the test and require no leftover process or new crash dump.

After the disposable fixture passes, run a separately logged real-target acceptance when the user has authorized installation. If an older localized release is installed and no formally tested direct-upgrade graph exists, preserve its current core files and rollback state, use its verified rollback path to return to a known original baseline, verify the original hashes, and only then install the new release. Recheck final core hashes, translated source-file counts, progress semantics, rollback-state existence, process exit, selected visual screens, and crash-dump state in the real directory. Do not claim a real-target rollback unless it was separately executed and its restored hashes were recorded.

DirectDraw-era games can appear black in ordinary screenshots even while the Stage renders correctly. Treat screenshot capture as supporting evidence, not the sole launch verdict; combine process responsiveness, window enumeration, title checks, crash-dump checks, and a brief manual visual check when available.

## 8. Release and cleanup policy

Assign every build an explicit lifecycle role such as `validation-candidate`, `NOT_FINAL`, `canonical`, or `rollback-only`. Build into a new directory and never overwrite the last-known-good release. Promote one installer to `canonical` only after the evidence bound to that exact EXE passes; then perform a delete/keep audit instead of allowing directories named `final` or old probes to accumulate indefinitely.

### Restore active installations before pruning support data

When the user wants a finished project reduced to only the original game directory and canonical installer, do not assume a directory named `original` or `gimai` is currently at the source baseline. Inventory and hash it first. If the target is installed and an installer-owned backup/support root exists:

1. relocate the canonical installer outside any worktree scheduled for deletion and verify its size/hash before and after the move;
2. run read-only verification against the exact target and support root, and snapshot all excluded save/runtime-state files with hashes and metadata;
3. use the matching canonical installer to roll back, then verify every patch-owned baseline hash, absence of every `create` path, and a second source-state verification;
4. prove excluded user/runtime state remains byte- and metadata-exact;
5. delete the support root and worktree only after rollback succeeds, then rehash the retained game tree and installer.

Distinguish a pristine immutable baseline from an original program/resource core that also contains preserved user state. Do not delete a changed save/configuration file or an extra runtime log merely to force the historical baseline file count unless the user explicitly requests a byte-identical reset. If the baseline manifest or operation log lives inside a worktree that will be deleted, finish the baseline comparison and write the cleanup evidence to a retained project-drive log outside that root first.

Keep:

- one canonical final installer in the release directory;
- installer source, runtime package, manifests, original icon, and build script;
- final dual-baseline, negative, GUI, launch, and rollback reports;
- the active installation's rollback support directory;
- translation sources and unique extraction/rebuild tooling.

Apply a `current successful release + necessary rollback release` retention rule. Keep the previous installer/runtime only when it is still needed to recover an installed prior state or to provide a unique validated comparison; an icon-only or superseded probe is not a rollback release. Full disposable fixtures may be removed after promotion when their compact reports, progress traces, hashes, and key screenshots remain sufficient to reproduce the acceptance claim.

Delete after validation:

- duplicate convenience copies of the installer;
- old loose patch folders and ZIPs superseded by the final EXE;
- failed release candidates and full-game test fixtures;
- probe copies, embedded-ZIP staging files, build duplicates, and empty temp folders.

Before deletion, hash the canonical release, list every delete/keep path, and prove each recursive target remains inside the intended project root. After deletion, re-check release count and hash, active-game files, rollback status, running processes, and free-space change. Record all results in the project operation log.

Report both the logical size of the deletion whitelist and the actual free-space increase on the volume. Compression, hard links, sparse files, and allocation granularity can make those numbers differ; neither should be silently substituted for the other.

Old Director extraction trees can contain deep or misdecoded member names that make PowerShell 5.1 `Get-ChildItem -Recurse` or ordinary deletion fail partway. Switch to a long-path-aware read-only enumeration instead of repeating the failed traversal. Before deletion, resolve the top-level target, require it to be a non-reparse direct child of the intended project root, and compare it against the keep list. Then use the `\\?\` path with a single-tree .NET deletion; if attributes block it, clear attributes only inside that validated tree and retry. Record that the fallback was used, verify the top-level target is absent, and never widen the cleanup scope to a parent or sibling.

## 9. Failure lessons

- A missing marker is evidence of a different runtime shape, not permission to bypass validation.
- A successful file copy is not a successful install; final hashes and launch behavior must both pass.
- Created adapter files require first-class rollback metadata.
- Runtime INI/source-mode files are baseline-specific system inputs, not generic user preferences.
- A single EXE is still reproducible only when the embedded payload, build script, and manifest remain available.
- Keep active rollback data even when cleaning every obsolete installer and game fixture.
- Exact reproduction of a dialog's mojibake under the wrong code page is stronger evidence than changing fonts by trial and error.
- Alpha zero does not make hidden RGB irrelevant in every legacy renderer; verify scaled output before dismissing edge colors.
- A correct normal-state button does not validate its hover, pressed, selected, or disabled siblings.
- A shell-visible icon does not prove that every source icon frame survived compilation; reverse-extract and compare the resource set.
- A progress bar that reaches 100 is not byte-accurate unless monotonic byte totals and every required percentage threshold also pass.
- A translated/runtime patch can remain valid after an HD or decensor route is abandoned only when the optional media layer is fully removed and original container hashes are re-proven.
- An EXE that launches on the build machine is not “runtime independent” until loaded non-Windows modules resolve from the packaged game/support tree and undeclared external dependencies are zero.
- PowerShell filename mojibake is a release failure even when the file content is correct; verify the exact Unicode name after compilation.
- A GUI automation capture failure is not permission for blind interaction; use real-process launch evidence plus an explicitly labeled offline layout render.
- `NotSigned` can cause an unknown-publisher prompt but is not a missing game runtime. Report signing and runtime dependency status independently.
- A hash-perfect embedded banner can still belong to the wrong game; verify visible title identity in the rendered canonical EXE.
- Deleting an active support root before a verified rollback can destroy the only exact restoration path; restore first, prune second.
- A restored original core may legitimately differ from an immutable baseline through explicitly excluded user state; report the exception instead of deleting it for cosmetic file-count equality.
