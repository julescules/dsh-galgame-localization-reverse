# Legacy Director Runtime Text and Window Debugging

Use this reference for Macromedia Director-era Windows games where localization is already installed but a narrow runtime defect remains: one menu or option is garbled, the title-bar close button is ignored, or visual automation cannot observe the DirectDraw surface.

## Start from runtime evidence

Do not classify every garbled menu as a missing font. Capture all of the following before changing the hook:

1. The exact game PID and executable path.
2. The drawing API, byte count, and a bounded hex sample from the failing string.
3. The converted UTF-16 code units produced by the current hook.
4. The loaded text modules and the exact modules whose IAT entries were patched.
5. Every PID-owned top-level window: handle, class, title, visibility, style, rectangle, and process main-window handle.

Story text and option text can use the same GDI API but carry different byte conventions. Conversely, they can carry the same encoding but use different APIs or Xtras. The log must distinguish these cases.

## Mixed CP936 text with preserved CP932 punctuation

A common localization artifact is a Chinese CP936 payload wrapped in punctuation bytes copied unchanged from the Japanese source. For example:

```text
81 79  B4 D3 CD B7 BF AA CA BC  81 7A
^^^^^  ^^^^^^^^^^^^^^^^^^^^^^^  ^^^^^
CP932  CP936 Chinese payload    CP932
【                               】
```

Decoding the whole sequence as CP936 corrupts the two wrapper characters even though the Chinese payload is valid. The correct Unicode result for this example is:

```text
3010 4ECE 5934 5F00 59CB 3011
【      从   头   开   始    】
```

Do not install a broad byte-pair replacement table merely because `0x81xx` resembles CP932 punctuation. The same pairs can be legal GBK extension characters. Prefer a structure-bound rule such as:

- exact opening pair at the start;
- exact closing pair at the end;
- CP936-decodable payload in between;
- conversion enabled only in the hash-bound localized runtime layer.

Leave the normal CP936 path unchanged when the complete structure is absent. Log when the mixed wrapper rule fires, including byte length and the resulting UTF-16 sample.

## Audit runtime-composed choice decorations separately

A clean translated catalog is not proof that a displayed choice is clean. Director/Lingo code can concatenate a shared opening marker, the translated choice payload, and a shared closing marker at runtime. If every option acquires the same two bad characters, trace the shared builder before changing individual translations, fonts, or images.

For a CP936-localized runtime, this exact cross-code-page signature is especially diagnostic:

```text
meaning  CP932 bytes  decoded as CP936  correct CP936 bytes
【       81 79        亂                A1 BE
】       81 7A        亃                A1 BF
```

Use the following regression workflow:

1. Enumerate every choice-producing command and every `role=choice` catalog entry. Record both the builder-block count and the visible-choice count so a two-line scene is not mistaken for the whole defect.
2. Locate the wrapper literals in the owning script resources. A raw byte hit is only a lead: parse it as a literal operand or prove through a runtime composition log that the choice builder owns it before patching. When the Director container preserves both source (`CASt`) and compiled (`Lscr`) forms, keep them coherent by patching the exact resource-local occurrences in both.
3. Bind the patch to an accepted input SHA-256, require the exact old occurrence count, preserve byte length, and reject unknown baselines. Never replace every matching `0x81xx` pair across the container.
4. Reparse the rebuilt Director container and require its reconstructed bytes and resource map to match the patched artifact. In the audited wrapper slots/resources, require zero old CP932 literals and the exact expected number of CP936 literals; do not turn this target-local assertion into a container-wide byte replacement.
5. For every catalog choice, simulate the final runtime composition `opening + translation + closing`, encode and decode it through the target code page, and fail on replacement characters, known mojibake sentinels, residual Japanese, or a round-trip mismatch.

Do not remove the decoration or hand-edit each translated choice merely to hide the symptom. Fix the shared owner once, then rebuild every downstream portable release, manifest, embedded payload, installer, checksum, and acceptance report. A direct post-build container patch is acceptable only when it is hash-bound, occurrence-count-gated, equal-length, independently reparsed, and included in the downstream hash chain.

Keep three QA layers distinct:

- catalog QA: translation, terminology, speaker, placeholders, and target encoding;
- runtime-composition QA: wrappers, prefixes, counters, lookup tokens, and other strings appended by script code;
- rendered-UI QA: image-baked labels, fonts, clipping, layout, and the actual DirectDraw surface when trustworthy capture is available.

When a user reports the same visible artifact more than once, preserve its exact byte signature and affected builder/catalog counts as a named regression fixture. A later release must pass that fixture even when ordinary story-text QA was already green.

## Treat save filters and load restoration as functional data

Do not use visual padding rules on strings consumed by FileIO, path, extension, archive, or lookup APIs. A Director `setFilterMask` value such as `Description(*.sln),*.sln` must end at the final ASCII wildcard. A fullwidth space appended to satisfy a fixed byte slot becomes part of the wildcard and can produce a visible doubled extension, an invisible trailing character, or a later suffix check failure.

For fixed-length localization of a save filter:

1. Parse and patch every executable copy, commonly both `CASt` source and `Lscr` literal data. Bind each site to an exact input/resource hash and unique resource-local context.
2. Put any required equal-length punctuation or spacing in the human-readable description before the comma. Never pad after the machine pattern.
3. Require the final bytes to equal the intended ASCII suffix exactly, for example `2A 2E 73 6C 6E` for `*.sln`; reject trailing `20`, fullwidth space, NUL-in-pattern, or any other byte.
4. Reparse the rebuilt container and require the old filter count to be zero, the new count to match all declared copies, resource lengths to remain stable, and non-target resource changes to be zero.
5. Test actual save, overwrite, and load dialogs on a disposable game copy. Record the returned filename, Unicode name, raw suffix bytes, file length, and SHA-256. Merely opening and cancelling a dialog is not save/load acceptance.

When loading says it succeeded but the scene appears unchanged, do not immediately patch FileIO or rewrite the load handler. Use this sequence:

1. Hash the exact running `EXE`, main movie, script cast, and selected save from the process directory. A launcher that verifies only the Projector while checking casts merely for existence can silently run a mixed old/new installation; bind every mutable core file in the launcher or collect all hashes before diagnosis.
2. Reject zero-byte and synthetic sentinel files as evidence. Distinguish real player saves from automation probes by provenance, nonzero length, codec validation, and decrypted schema.
3. Decrypt a real save with the proven codec, require a byte-perfect decrypt/encrypt round trip, then record its scene/member, counter or program position, graphic, replay token, and route flags. Confirm that the referenced member still exists and the counter is in range.
4. Trace the complete runtime restoration chain, not just file selection: parsed state replacement, intermediary score marker, final gameplay marker, and the behavior or frame event that reloads the script member and counter. Compare the corresponding `Lscr`, `VWLB`/labels, `VWSC`/score, behavior association, and external-cast identity against the accepted baseline.
5. Perform a real `save or known-good load -> advance to a different text position -> load -> restore` test. Record before/after story IDs, counters, exact dialogue text, and screenshots when capture is trustworthy. The same background or character CG may span many counters, so an unchanged picture is not proof that load failed; compare text/counter state.
6. If a valid save restores the expected text/counter, leave the load control flow unchanged and classify the earlier report using the measured evidence: same-CG false negative, wrong game copy, mixed core files, empty/corrupt save, or another selected file. Only modify bytecode after a valid save demonstrably fails the traced state transition.

Keep save/progress files outside installer payload and rollback ownership throughout these tests. Preserve their bytes and metadata unless a separately proven, atomic migration is required.

## Separate replay metadata from visible labels

A replay, gallery, backlog, or scene catalog can become empty even when every event record and save flag still exists. Director scripts often compare serialized category strings with hard-coded CP932 lookup tokens before consulting the save data. If localization translates those internal tokens, every entry is filtered out before its visible label is built.

Audit the complete registration and filtering path before editing save files:

1. Count event-control records and preserve their ordering and IDs.
2. Trace the catalog builder's exact equality tests, `findPos` keys, category tokens, and event prefixes.
3. Compare localized serialized metadata with the script's hard-coded byte strings.
4. Restore internal lookup tokens to their original bytes while retaining the translated display title.
5. Require unchanged non-target serialized strings and independently reparse the rebuilt cast.

When entries return but a prefix still renders as mojibake, treat that as a separate visible-text defect. Reproduce the screenshot from the stored bytes under both code pages—for example, CP932 fullwidth colon `81 46` becomes `丗` under CP936—then patch only the owning resource-local literal to an equal-length CP936 form. Handle locked placeholders the same way. Do not globally replace byte pairs: the same bytes may belong to internal tokens or unrelated resources. Prove the exact old/new occurrence counts, changed resource set, and non-target byte count.

## Hook the proven rendering route

For Director 8/8.5, text may pass through `IML32.dll`, `Text Asset.x32`, `TextXtra.x32`, or `Font Xtra.x32`. Patch only modules and APIs shown by imports or runtime logs.

If the failing string never appears in the hook log:

1. Enumerate PE imports for `TextOutA/W`, `ExtTextOutA/W`, `DrawTextA/W`, `DrawTextExA/W`, `TabbedTextOutA/W`, and text-measurement APIs.
2. Check whether the responsible Xtra loads after a one-shot module snapshot.
3. Patch late-loaded modules through a bounded loader/notification route or a low-frequency module monitor.
4. Hook rendering and measurement consistently when layout depends on byte versus wide-character counts.

If the exact failing bytes already appear in `ExtTextOutA`, do not add unrelated drawing hooks. Fix the decoder and prove the new UTF-16 output with a dedicated 32-bit probe.

## Multiple Director windows and a dead close button

Old Projectors can expose several same-process `ImlWinCls` top-level windows. The window with the user-facing title or close box may not be the process main window. A click can therefore produce `WM_SYSCOMMAND/SC_CLOSE` on an inner window that Director ignores, while posting `WM_CLOSE` to the canonical `main` window exits normally.

Establish this before subclassing:

1. Enumerate all PID-bound `ImlWinCls` windows and record titles/handles.
2. Confirm the process main-window handle and title.
3. Use a non-destructive process close test to prove that its `WM_CLOSE` path exits and allows launch helpers to clean up.
4. Reject any candidate handle from another PID or class.

A narrow bridge can then subclass only same-process `ImlWinCls` windows:

```text
SC_CLOSE on any bridged window
    -> locate same-PID ImlWinCls titled "main"
    -> show a localized Yes/No confirmation with No as the default
    -> on Yes, PostMessage(target, WM_CLOSE)
    -> on No or dialog close, keep the game running
    -> consume the original SC_CLOSE

WM_CLOSE on a non-main bridged window
    -> apply the same confirmation before forwarding

WM_CLOSE on the canonical main window
    -> call the original window procedure
```

Do not equate “the close button exits now” with correct UX. If the game previously used an exit prompt elsewhere, preserve that expectation at the title bar. Guard the dialog with an interlocked one-at-a-time flag so repeated close messages cannot open stacked prompts. Log accepted and cancelled outcomes separately.

Keep the original window procedure per HWND, prevent duplicate subclassing, bound the table, and log source/target handles. Remove the HWND/original-procedure entry after calling the original procedure for `WM_NCDESTROY`; also prune invalid or reused HWNDs before installing a new subclass. Otherwise a long Director session that recreates windows can exhaust a small table or skip a reused handle. A monitor may be needed because Director can create or replace windows after injection; a 250 ms same-process enumeration is sufficient for legacy UI without polling aggressively.

## QA when DirectDraw screenshots fail

Some old DirectDraw windows reject modern capture with errors such as interface-not-supported `0x80004002`. Do not claim a visual pass when observation failed, and do not compensate with blind mouse automation.

Use layered evidence instead:

- accessibility/window metadata for title bars and close controls;
- hook logs for raw bytes, conversion route, UTF-16 output, and selected font;
- a 32-bit probe that draws the exact failing byte sequence through the real DLL hook;
- a probe with two `ImlWinCls` windows that first simulates No and proves the main window stays open, then simulates Yes and requires the main window to receive `WM_CLOSE`;
- an actual game launch proving hook injection, window subclass installation, clean process exit, helper exit, runtime artifact cleanup, and exact rollback hashes.

Keep visual confirmation as a clearly named remaining manual check if no trustworthy capture path exists. The byte-level and lifecycle tests are still valuable, but they are not a screenshot substitute.

## Release invalidation and acceptance

A runtime-hook change invalidates the hook hash in the launch script, payload manifest, embedded ZIP, installer EXE, acceptance report, and release checksum. Rebuild all downstream artifacts.

Do not let a reproducible package specification depend on a live user-game `main.bin` that the launch script intentionally deletes, or on a modified launcher that exists only in the active install. Freeze hash-bound metadata/reference inputs under a versioned build-input directory on the project drive. These reference files are build evidence, not release payloads unless the manifest explicitly declares them.

Treat manifest-listed runtime temporary directories as owned cleanup roots. During rollback, recursively delete only those resolved whitelist paths, retry transient `IOException`/access failures, and fail rollback if any listed directory remains. Restoring original game files while leaving extracted Xtras is not an exact rollback and must not be reported as success.

Minimum acceptance depends on the layer actually changed:

- For a mixed-string or choice-wrapper-only fix, require the expected UTF-16/CP936 composition for every affected catalog item, exact target-local old/new literal counts, an independent Director-container reparse, and unchanged non-target bytes/resources.
- If a window-close bridge or rendering hook changed, additionally require the close probe to prove cancel-keeps-open and confirm-exits, release destroyed-window subclass slots, and leave no process; require an actual launch to prove hook injection, clean exit, helper exit, and hash-matched runtime cleanup.
- If the installer or embedded payload changed, require installer self-test against the final embedded payload, exact 1-100 install/verify/rollback progress, the expected installed hashes, and rollback to an exact original full-game fixture tree.
- If an authorization adapter is part of the accepted scope, require the real game to start without the targeted platform authorization popup and keep that adapter's evidence separate from localization-only acceptance.

Store probes, logs, manifests, and QA fixtures under versioned project directories on the project drive. After rollback proof, delete duplicate full-game test copies when their evidence has been preserved; retain the current installer, source, manifest, checksums, and the smallest necessary rollback evidence.
