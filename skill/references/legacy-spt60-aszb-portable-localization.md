# Legacy SPT60/SBY and ASZB Portable Localization

## When to use this route

Use this route for a legacy Windows visual novel that presents several of these signals:

- `SBY` script files, especially files with an `SPT60`-like signature.
- `PIC/*.ASZ` or `ASZB` bitmap containers.
- Separate `MUS`, `PCM`, and `VOICE` resource trees.
- A small binary CFG file and a custom PE executable rather than a known modern engine layout.
- Story text, menu text, save-page text, and image-backed labels that fail in different ways.
- A request for installer-free, registry-free, movable-folder operation.

Treat these signals as routing evidence, not a format specification. Re-prove every signature, record marker, offset, code page, compression parameter, and path limit for each title and version.

## Freeze immutable media and extract without installing

1. Inventory the supplied archive, disc image, executable, and existing game trees. Record path, size, SHA-256, timestamp, PE structure, and provenance before executing anything.
2. Keep the original archive and disc image immutable. Extract into a project-owned directory on the project drive and create a complete relative-path manifest.
3. Prefer static InstallShield, ISO, or archive extraction. Do not run the installer merely to obtain payload files.
4. Separate these baselines:
   - original media;
   - original extracted resources;
   - original runtime payload;
   - localized working outputs;
   - accepted release;
   - rollback evidence.
5. Bind every downstream tool to exact input hashes. Reject an input that only has a convincing filename such as `.original`, `.bak`, `fixed`, or `repaired`.

## Discover the SPT60/SBY record model

1. Confirm the file signature, mode bytes, record markers, terminators, pointer fields, and scan boundaries from multiple files. Do not assume the values observed in another title.
2. Identify text slots structurally. Preserve for every slot:
   - relative file path and source-file hash;
   - stable record or segment ID;
   - marker, payload, and terminator offsets;
   - original slot hash and raw bytes;
   - strict source decoding and decoded text;
   - byte capacity;
   - control-code template and any explicit override reason.
3. Extract every structurally valid slot before applying language filters. A kana-only filter misses CP932 punctuation, full-width spaces, ellipses, brackets, and other byte sequences that can become mojibake after the runtime switches to a Chinese code page.
4. Classify pure controls, ASCII-safe records, technical keys, and intentionally untranslated records with an explicit allowlist. Do not make the extraction filter double as the residual-text allowlist.
5. When inheriting a language-filtered catalog, regenerate a full structural catalog and diff the two catalogs by stable record ID. Classify omitted records into target-byte-identical no-ops and source-to-target byte-different records. Require strict target encoding, exact slot length, no NUL or control-template drift, and an independent verifier proving that the final write set is exactly the byte-different class.

## Map every visible text owner

Do not assume one screen has one text source. Build an ownership map that covers:

- fixed-slot SBY story and command text;
- ANSI C strings in the executable;
- PE `MENU`, `STRINGTABLE`, dialog, and other UTF-16 resources;
- text rendered into ASZ bitmaps;
- save-index files, initial save seeds, and other serialized display data;
- CFG diagnostics, install checks, and error messages.

Use screenshots, whole-tree byte searches, PE resource enumeration, cross-references, and isolated runtime substitutions to prove ownership. When story text is correct but a speaker name, menu item, or save page is garbled, investigate the other surfaces instead of repeatedly rewriting SBY.

## Normalize and audit mixed encodings

1. Use UTF-8 for project intermediates, but preserve the proven source and target encoding for each runtime surface.
2. Decode Japanese script bytes strictly as CP932 when evidence supports it. Encode localized runtime text using the exact path the executable consumes, often the current Windows ACP rather than a single engine-wide encoding.
3. Re-encode punctuation and symbols even when the Unicode glyph looks identical. CP932 and CP936/GBK can assign different bytes to visually identical characters.
4. Audit all of these categories:
   - residual kana and Japanese-only text;
   - CP932-only byte sequences;
   - target-encoding failures;
   - pure punctuation and full-width-space slots;
   - save indexes and initial save data;
   - every executable and image-backed UI surface.
5. Distinguish a true visible residual from unreachable metadata or a technical lookup key. Require evidence before excluding it.

## Prove screenshot mojibake from raw bytes before patching rendering

1. Transcribe the exact visible mojibake and locate candidate slots by stable record ID, file, marker or payload offset, and raw bytes.
2. Decode the same payload under the proven source code page and the live target ACP. Treat a match as strong only when the source decode yields the intended text and the target-ACP decode reproduces the screenshot exactly.
3. Trace the executable's multibyte path, such as `_setmbcp`, `GetACP`, `_mbctype`, or the actual text API, and record the live ACP.
4. If an omitted or unconverted data slot fully explains the screenshot, rebuild that data layer and verify its exact diff set. Do not add a font, renderer, or executable patch without separate evidence.

## Write fixed slots transactionally

Until pointers, jumps, and relocations are fully understood, keep SBY replacements in place and within the original byte capacity.

1. Freeze control codes as stable placeholders before translation. Restore them only after validating count, order, and allowed overrides.
2. Measure the target encoding in bytes, not characters. Never truncate a multibyte character or silently drop a control.
3. Keep records physically separate unless the VM control flow proves that they can be merged.
4. Complete a full preflight before creating an output tree:
   - exact input inventory and file hashes;
   - unique segment IDs;
   - marker and terminator integrity;
   - original slot hashes;
   - no overlapping write ranges;
   - strict target encoding;
   - replacement capacity;
   - placeholder preservation.
5. Write to a new tree. On any preflight failure, create no partial SBY output.
6. Require these tests:
   - source-encoding zero-mutation round trip is byte-identical;
   - a bounded target-encoding single-slot probe succeeds;
   - short slot, oversized text, missing control, reordered control, stale hash, and overlapping-range cases are rejected transactionally.
7. Use an independent verifier that does not import the builder's parsing or writeback implementation. Reparse the originals, reconstruct control templates, compare all bytes outside declared slots, verify lengths and terminators, and compute a deterministic output-tree hash.

## Preserve context during translation review

1. Review in source-file and physical-slot order with adjacent context.
2. Do not treat adjacent slots as one writable sentence unless their control flow is proven.
3. Display source text, target text, target byte count, capacity, controls, terminology, and neighboring records together.
4. Resolve over-capacity translations by reviewed rewriting. Never auto-truncate.
5. Require QA for complete IDs, duplicate or unknown IDs, terminology, target encoding, placeholders, residual Japanese, byte capacity, and representative in-game screenshots.

## Decode and rebuild ASZB image text

1. Prove the container header, metadata fields, decoded size, compression stream, BMP layout, dimensions, bit depth, palette, and padding before editing.
2. First pass a zero-mutation cycle: original ASZ to decoded bitmap, rebuild, decode again, and compare pixels and structural metadata.
3. Render translated labels without changing dimensions, color mode, palette, or unexplained metadata.
4. Do not equate decoder acceptance with engine compatibility. A literal-only LZSS stream can be structurally valid and independently reversible yet still hang or exceed assumptions in a legacy runtime.
5. Document the compression dialect before implementing the encoder: flag-bit order, ring-buffer size and initial position, initial dictionary bytes, overlap-copy semantics, distance base, minimum and maximum match lengths, stream/end marker, compressed-size fields, and runtime input-size limits. Compare literal/match ratios and token-distance distributions with original assets instead of accepting any theoretically legal stream.
6. Prefer a deterministic encoder that emits real back-references when the format supports them. Audit compression tokens, declared sizes, maximum token bounds, and decoded output independently.
7. Require both static and dynamic acceptance:
   - independent decode equality;
   - container and stream-structure checks;
   - original-size visual QA;
   - real engine load, window response, and CPU/progress observation at every image-heavy stage.

## Build executable localization as hash-gated layers

Separate runtime changes into auditable stages such as:

- registry/install-check bypass;
- font and code-page behavior;
- title and custom menu text;
- PE resource tables;
- remaining ANSI/UTF-16 UI text.

For each stage, pin the exact input hash, expected old bytes or resource values, declared diff set, output hash, and zero undeclared changes. Rebuild the full chain after any upstream script, image, font, executable, or configuration input changes. Start from a trusted original every time; never stack new work onto whichever active EXE currently launches.

Prove the actual glyph path from imports, call sites, and runtime behavior. A font name or charset constant observed in one title is not a reusable default.

## Diagnose display-mode and cached-surface failures

Do not treat bypassing a legacy 16-bpp startup check as proof that the rendering path is compatible. A title can start on a 32-bpp desktop yet lose image-backed controls only after entering exclusive fullscreen.

1. Trace `DirectDrawCreate`, `SetCooperativeLevel`, `SetDisplayMode`, `CreateSurface`, pixel-format queries, color keys, `Blt` or `BltFast`, and every fullscreen-toggle path.
2. Record which primary, back, offscreen, and cached UI surfaces are created before the toggle and which are recreated afterward. A long-lived 32-bpp menu surface copied into a newly created 16-bpp fullscreen surface can explain disappearing buttons while unrelated backgrounds continue to render.
3. Use screen ownership to narrow the fault: distinguish image-backed labels, live GDI text, video surfaces, and background blits before changing code.
4. Build the smallest hash-gated compatibility layer that makes the proven surfaces agree. Pin the input hash, old bytes, context, declared diff, output hash, and preservation of every prior executable layer. Rediscover the correct display mode for each title; never copy a bit depth or patch offset from another build.
5. Keep cooperative level, display mode, primary/backbuffer caps, and flip or blit behavior internally consistent. Do not leave a hybrid state by disabling only one transition.
6. Verify the exact launched path and EXE hash, the engine's internal window/fullscreen flag when available, live display mode, process responsiveness, visual control visibility, clean exit, desktop-mode restoration, and recent crash state.

## Recover from executable contamination

If active executables mutate unexpectedly:

1. Stop build and runtime testing. Do not promote any active copy.
2. Compare trusted and suspect PE files by size, hash, section count, entry point, `SizeOfImage`, RWX sections, overlays, and embedded PE signatures.
3. Treat an antivirus-repaired file as untrusted unless it exactly matches a known-good hash.
4. Preserve archive or hash-bound original baselines and rebuild only by replaying the verified patch chain.
5. Before materializing a clean build, use a non-executed hash canary and protection-state checks to confirm that unexpected writes have stopped.
6. After rebuilding, sample the EXE hash and PE structure over time and scan the release directory.
7. In the launcher, normalize the final game path, reject unexpected reparse points, and open the game EXE for read with no write/delete sharing. Calculate length and SHA-256 on that same handle, record file identity when the platform exposes it, and keep the handle open across configuration rebinding, process creation, and child exit. Pin the expected hash in a trusted launcher/build input rather than accepting only package self-reporting. This closes the ordinary hash-check-to-execution replacement window.

Describe the structural contamination pattern generically unless an authoritative product result or separate forensic analysis establishes a specific malware family.

## Remove registry dependence and rebind the CFG path

1. Prove whether the game merely reads an install key and refuses missing state, or actually writes registration data. Use both static API/call-site evidence and narrow before/after registry snapshots.
2. Patch the smallest proven install-check branch into the original success path. Do not create fake machine-wide installation state when a local runtime decision is sufficient.
3. Test the process working directory. Many legacy engines resolve `PIC`, `SBY`, audio, and save files relative to cwd.
4. Discover absolute paths in a binary CFG through original-versus-runtime diffs. Confirm the field boundaries, terminator, padding, and encoding; do not patch the first matching path string blindly.
5. If a neutral relative seed such as `.` launches but the engine rewrites an absolute path on exit, treat it as a seed only. Rebind the field from the launcher's own directory before every launch.
6. Have the launcher set both its process cwd and the child's `WorkingDirectory` to the game root.
7. Encode the root with the current Windows ACP using strict round-trip validation. Test and declare the supported ACP matrix, especially CP932, CP936, and UTF-8 ACP 65001. Fail closed when the engine's byte-oriented path semantics have not been proven for the active ACP. Derive the byte limit from the proven CFG slot and runtime evidence.
8. Update CFG atomically with a same-directory temporary file, flushed write, atomic replacement, readback validation, and rollback on failure.
9. Make the launcher the documented entry point. Direct execution of the game EXE bypasses rebinding and integrity gates.

## Scope proven compatibility shims to the launched process

1. Prove the minimum compatibility layer required by the exact executable and Windows behavior. Treat every layer name as title- and build-specific evidence, not a portable default.
2. Prefer a launcher-local environment scope: use `setlocal`, set `__COMPAT_LAYER` only for the child process, change cwd to `%~dp0`, and launch the relative game executable. Do not create a permanent user or machine environment variable merely to carry a compatibility shim.
3. Snapshot the exact executable path in HKCU and HKLM AppCompat `Layers` views before, during, and after testing. Windows Program Compatibility Assistant can create a path-specific value after a crash or failed run even when the package itself never writes the registry.
4. Remove only an exact, resolved test-path value whose baseline and provenance were recorded. Use a fresh candidate path when stale path-specific compatibility state would contaminate an A/B test.
5. Distinguish an inherited process environment from persistent registry state in both the acceptance report and user documentation. Require the final candidate to leave no unexpected game or AppCompat values.

## Treat runtime-written saves as a separate localization surface

1. Compare three hash-bound states: the original seed, the clean localized seed, and copies captured after confirmation and after clean exit. Static seed QA alone does not prove that the engine preserves localized names or labels.
2. Trace the runtime write path and its length, truncation, and padding rules, including functions such as `GetWindowTextA`, `lstrcpynA`, fixed-width copies, and serialized length fields.
3. Audit padding bytes under the live target code page. For example, the CP932 full-width space bytes `81 40` are not the CP936 full-width space bytes `A1 A1`; a Japanese padding constant can become a visible extra glyph after a Chinese save is rewritten.
4. When evidence proves two independent owners, fix both layers: normalize the pristine localized seed and patch the runtime padding or serialization constant through a separate hash-gated executable stage. Verify that the second patch preserves all earlier display, code-page, and portable layers.
5. Test short user-entered values as well as the supplied default. Verify field lengths, terminators, raw bytes, rendered text, post-exit persistence, and the absence of the source padding sequence.
6. Run these tests only on disposable candidate copies. Preserve each post-run save as evidence before restoring a hash-bound seed, and never overwrite a user's live save with a release seed.

## Build and verify the portable package

1. Build into a new same-volume `.building` directory. Reject source/output overlap and any reparse point.
2. Compare the source manifest inventory and actual source inventory in both directions before copying.
3. Read each source file once for the build snapshot, then use that same byte buffer for size, hash, and output write where practical.
4. Store only normalized relative paths in the release manifest. Reject absolute paths, `..`, case-colliding entries, unexpected files, and build-machine path leakage.
5. Pin launcher and game hashes outside self-reported package metadata.
6. Distinguish immutable resources from mutable CFG, save, and index files. Support:
   - `seal` mode for the pristine release seed;
   - `runtime` mode for an installed/moved copy whose declared mutable files have changed.
7. Define each mutable path with an existence policy, allowed add/remove behavior, size bounds, and format-specific structural checks. Runtime verification must not merely skip hashes for arbitrary mutable files.
8. Require the verifier to accept an external expected manifest SHA-256. Write its report outside the package with exclusive creation.
9. Hash and parse one manifest byte snapshot, then verify that the on-disk manifest is unchanged before completion.
10. After the full inventory and every payload hash pass, atomically rename `.building` to the final directory.
11. After sealing the accepted directory, test every distributed archive with its native integrity command and compare its normalized inventory with the accepted directory in both directions. Require zero missing or extra paths and compare every file's uncompressed size plus CRC32 or a stronger extracted-file hash. Record the archive hash and prove that its embedded release manifest is the expected one. Archive integrity alone does not prove that packaging omitted nothing.

## Reconcile source-media size with installed payload

1. Inventory every archive and disc layer separately, including nested archives, recovery records, container overhead, installers, and independent bonus discs.
2. Derive the official minimum and full-install payload from static installer scripts or manifests instead of treating total source-media size as the required runtime size.
3. Identify the normal runtime resource route and any command-line-only or diagnostic alternatives. Classify duplicate uncompressed media, bonus content, and alternate codecs as optional layers only when evidence supports it.
4. Compare required resource trees by normalized relative path in both directions. Hash unchanged files and require every localized difference to belong to a declared manifest set.
5. Report separate completeness scopes for the playable main-game payload, the official full install, and a collector package containing optional or bonus media.

## Perform a real A/B move test

Before trusting any A/B observation, bind each screenshot, dialog, and runtime note to capture time, PID, full process path, package root or candidate hash, and window title. Label or close the baseline before launching the localized candidate when practical. Never modify one candidate from evidence produced by another running copy.

Legacy DirectDraw windows can reject modern window-capture APIs, and a desktop fallback can capture a different foreground application. Reject any image that is not bound to the target window. When pixel capture is unavailable, record the limitation and combine independent evidence: exact PID/path/hash, read-only internal mode state where justified, `EnumDisplaySettings`, responsiveness, crash logs, before/after file and registry snapshots, and explicit user visual confirmation. Do not relabel this as automated pixel proof.

1. Test at a normal path and at a path containing CJK characters and spaces that remains strictly encodable by the current ACP.
2. Move the entire directory from A to B; do not simulate portability by editing only CFG or copying selected files.
3. At each location verify:
   - launcher and child executable paths;
   - cwd and resource loading;
   - automatic CFG rebinding;
   - Chinese story, menu, save, and bitmap UI;
   - BGM, PCM effects, and voice playback while their resource hashes remain unchanged;
   - process responsiveness and clean exit;
   - narrow registry snapshots;
   - added, removed, immutable-changed, and declared-mutable files.
4. Run move tests on a disposable release copy. Never restore release seeds over a user's live save directory. Move B back to A, restore only the test copy's seed CFG, save, and index data from hash-bound sources, then require a byte-identical final seal.
5. Same-volume A-to-B-to-A proves directory mobility. If the explicit product requirement includes drive-letter changes and an approved test volume is available, add a cross-volume whole-directory test; do not turn it into an unconditional gate for unrelated releases.
6. Report the evidence boundary honestly. A successful movable-folder and no-registry test is not proof of execution on a second computer. Record remaining dependencies such as target Windows versions, legacy DirectDraw behavior, fonts, ACP compatibility, and any launcher runtime.

## Emit machine-readable evidence

Keep these artifacts as relative-path UTF-8 JSON, JSONL, or TSV where practical:

- text-owner map with surface, source path, encoding, lookup/render path, and proof;
- SBY catalog and writeback manifest with stable IDs, offsets, capacities, controls, and hashes;
- ASZ codec schema and asset manifest with dimensions, palette, metadata, codec dialect, and round-trip/runtime status;
- CFG schema with discovered field offsets, encoding, terminator, padding, and safe byte limit;
- staged PE patch manifest with input/output hashes and declared diff ranges;
- portable inventory with immutable and per-path mutable policies;
- acceptance report containing seal/runtime state, A/B paths, process paths, registry scope, file diffs, UI/audio observations, and remaining compatibility boundaries.

For every actual mutation or cleanup, append an operation log with time, objective, commands or tool versions, changed/deleted/retained paths, logical bytes, volume free-space delta, failures, verification hashes, and next action.

## Clean finished-project byproducts

Build a reverse dependency graph from the accepted release back to immutable inputs. Retain the canonical input, builder, manifest, output, and verifier evidence for every stage in that graph. Delete superseded sibling outputs only after proving that no retained builder or verifier references them. Remove nested archive duplicates only when immutable source media, the trusted extracted baseline, and equivalence hashes remain available. After cleanup, reverify the accepted directory, its distributed archive, and the trusted original baseline.

After the final release is sealed, retain:

- immutable original media and trusted rollback baselines;
- translation and human-review sources;
- deterministic extraction, build, and verification tools;
- the accepted localized SBY, ASZ, and executable stage needed to reproduce the release;
- final manifest, hashes, smoke/move evidence, security evidence, and operation logs.

Delete only an explicit, resolved, non-reparse whitelist of obsolete items such as full runtime probe clones, failed candidates, replaced patch stages, superseded localized assets, compiler caches, temporary directories, and invalid screenshots. Record logical bytes removed and actual volume free-space change separately. Re-hash the final release and trusted baseline after cleanup.

## Values that must be rediscovered

Never copy these values from a prior title without proof:

- SPT60 signature variants, modes, markers, control grammar, slot counts, and file counts;
- ASZB header length, metadata meaning, dictionary size, and compatible compression strategy;
- CFG size, path offset, slot length, terminator, padding, and conservative path limit;
- registry keys, bypass offsets, patch-stage count, PE offsets, and stage hashes;
- font face, charset, text APIs, and code-page assumptions;
- DirectDraw surface lifetimes, fullscreen bit depth, cooperative mode, and display-mode patch sites;
- compatibility-layer names, AppCompat paths, and Program Compatibility Assistant behavior;
- save-field offsets, serialized lengths, runtime padding ownership, and target-code-page padding bytes;
- localized image count, save-slot count, index record size, and mutable-file list;
- launcher framework or runtime dependency;
- any malware-family name inferred only from structural similarity.

## Acceptance checklist

- Original media and extracted baselines are immutable and hash-bound.
- All visible text surfaces have a proven owner.
- Full-slot extraction includes punctuation-only records.
- Fixed-slot writeback is transactional and independently verified.
- Target text passes byte-capacity, control, encoding, terminology, and residual audits.
- Localized ASZ files pass independent decode and real-runtime loading tests.
- The executable is rebuilt from a trusted original through exact hash-gated layers.
- Windowed/fullscreen surface compatibility is proved dynamically, including visual controls and desktop restoration.
- Registry-free behavior and CFG field discovery are supported by before/after evidence.
- Any compatibility shim is process-scoped, and exact AppCompat paths remain clean after exit.
- Localized save seeds and runtime-rewritten saves preserve target-encoding lengths, padding, and display text.
- The launcher owns cwd, CFG rebinding, strict path encoding, and same-handle executable validation.
- The manifest uses relative paths and separates seal from runtime mutable state.
- A-to-B-to-A movement, registry, process, resource, and final-seal tests pass.
- BGM, PCM, and voice play at both test locations without resource mutation.
- Move testing and seed restoration occur only on a disposable release copy, never over live user saves.
- Obsolete probes and candidates are removed without deleting originals, sources, rollback, tools, or final evidence.
