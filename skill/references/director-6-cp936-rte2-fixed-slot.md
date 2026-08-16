# Director 6 CP936 fixed-slot and RTE2 localization

Use this reference for Macromedia Director 6 Windows games where a Projector executable owns an embedded startup/title/manual movie, an external `DXR` owns gameplay, Japanese CP932 text must become Chinese CP936/GBK, and visible text may be split across whichever `Lscr`, `STXT`, `RTE0`, `RTE1`, cached `RTE2`, or `BITD` resources actually exist.

## Contents

1. Map runtime ownership
2. Keep the executable and movie as an exact pair
3. Build a slot-authority catalog
4. Diagnose punctuation as bytes and glyphs
5. Rebuild cached RTE2 text deliberately
6. Measure rendered width, not only bytes
7. Treat dynamic status fields as composed layouts
8. Rebuild downstream layers from a clean base
9. Automate Director input and capture conservatively
10. Require layered acceptance

## 1. Map runtime ownership

Do not assume the external main movie owns every visible screen. A Director 6 Projector can embed a separate `XFIR`/`RIFX` movie containing the splash, title buttons, manual pages, parameter diagrams, and introduction while an external `DXR` owns the gameplay menu and story.

Before translating:

1. Hash the original Projector, external movies/casts, large media container, icon, Xtras, and source image or ISO.
2. Locate and parse any embedded `XFIR`/`RIFX` movie instead of treating the PE as an opaque launcher.
3. Inventory visible ownership by screen: Projector resources, external movie resources, Lingo literals, text casts, bitmap members, and runtime-composed strings.
4. Record resource ID, chunk type, offset, length, source bytes, source encoding, and member/script association for every accepted target.
5. Keep the source media and extracted source tree read-only; build every candidate in a new project-drive directory.

When the movie is embedded inside a PE, freeze the PE prefix and the embedded-container offset and declared length. After patching, extract or rebase the embedded movie again and reparse it independently; a valid PE alone does not prove a valid Director resource map.

A translated story movie does not prove that the title, manual, or introduction is translated. Conversely, a translated Projector shell does not prove that the external gameplay movie is compatible.

## 2. Keep the executable and movie as an exact pair

Treat the patched Projector and patched main movie as one runtime tuple. Bind their lengths and SHA-256 hashes in every fixture, package, report, and launcher check.

A mixed probe can produce a misleading combination:

- Chinese title or system graphics from the patched executable;
- Japanese cached menu glyphs from the original `RTE2` resources;
- CP932 story bytes decoded under a Chinese system code page and rendered as Chinese-looking mojibake.

Do not diagnose such a screen as a new font failure until the exact running executable path, working directory, Projector hash, external movie hash, and media/Xtra set are confirmed. Label every deliberately mixed fixture `NOT_DELIVERABLE` and close it after evidence collection.

Launch with the game directory as the working directory. Old Director relative movie and Xtra lookup can otherwise select missing or unintended components.

## 3. Build a slot-authority catalog

Normalize editable text through UTF-8, but keep a machine-readable authority row for every runtime slot. Include at least:

- stable slot ID and duplicate-group ID;
- owning file, script/member, resource type, and resource-local offset;
- source text, CP932 bytes, and slot capacity;
- target text, strict CP936/GBK bytes, and actual encoded length;
- semantic role: visible story, visible field, runtime wrapper, internal lookup token, path/filter, or control value;
- review status and translation provenance.

Freeze internal keys, member names, callback names, `go` targets, list sentinels, file masks, extensions, and equality-tested tokens. Prove visibility before translating an ambiguous short field.

For fixed slots, reject unencodable text and overflow before any output write. A shorter replacement is safe only when the owning parser's terminator, length field, or fixed record grammar is proven. Do not pad a typewriter or per-byte display string with spaces merely to reach the old length: the display loop can count those bytes and introduce a long pause. When the loop requires exact length, manually rewrite the sentence to the required encoded size and preserve its NUL/control structure.

Preserve resource-specific grammar instead of treating every hit as a raw byte slot. For a compiled Lingo literal, verify its actual length-prefix rule and trailing NUL; for `STXT`, preserve the header, style runs, line separators, and unrelated bytes; update paired `RTE0`/`RTE1` copies only when the parsed member map proves that both exist and own the same visible field.

Require duplicate source groups to remain consistent unless a recorded context exception explains the divergence. Re-run the entire catalog whenever a translation source changes.

## 4. Diagnose punctuation as bytes and glyphs

Legacy Director text can be valid GBK yet still render one punctuation mark as a vertical bar, box, or unrelated glyph because the active font cache lacks the expected glyph or the renderer interprets it differently.

First distinguish two visually similar failures. A repeatable standalone glyph at every ellipsis position points to punctuation/font ownership. A thin vertical remnant only at the right edge of long lines can be the final Chinese glyph clipped by the field and belongs to the pixel-width workflow instead.

When an ellipsis is proven wrong:

1. Locate the exact owning literal and encoded bytes.
2. Confirm that the screenshot symptom is reproduced by that slot and font, not by a runtime wrapper.
3. Replace U+2026 runs with a tested ASCII convention such as `...` or `......` when the authored font path renders ASCII reliably.
4. Re-run strict GBK, fixed-slot budget, duplicate consistency, and pixel-width checks.
5. Rebuild every derived manifest and binary; do not patch only the screenshot-visible occurrence.

Do not generalize one punctuation failure into a global CP932-to-CP936 byte-pair replacement. Japanese quotation marks, fullwidth punctuation, and GBK extension characters can share misleading byte patterns. Patch only resource-local, role-proven occurrences and retain exact old/new counts.

## 5. Rebuild cached RTE2 text deliberately

Director 6 can keep editable text/style data in `RTE0` and/or `RTE1` while drawing a cached glyph bitmap from `RTE2`. The exact tag set varies between the embedded Projector movie and external casts. Updating only the string can therefore leave Japanese menu text, missing Chinese glyphs, or unreadable cached output.

Use this sequence:

1. Parse the actual resource graph and map each visible text cast to the `RTE0`, `RTE1`, and `RTE2` resources that are present, plus original canvas geometry. Never synthesize a missing tag merely because another container used it.
2. Implement a canonical `RTE2` decoder and encoder, then require every untouched original resource to decode and re-encode byte-identically.
3. Render the intended Chinese text using an installed CJK font at the proven size. Select fonts per role; a bold sans face can suit very small menu cells while a serif CJK face can remain clearer for larger fields.
4. Preserve canvas dimensions, line placement, field geometry, and any non-target style bytes. Require every intended glyph bounding box to remain inside the original canvas.
5. If a new bitmap cannot fit the old chunk at a readable size, reject the tempting smaller-font workaround. Append replacement chunks using the alignment proven for that container, update the existing `mmap` entries to their new offsets and lengths, and update every affected container-size field. Do not add or delete map entries unless a separate rebuild proves that operation.
6. Keep old unreferenced chunks byte-exact as rollback evidence when appending is the proven low-risk route.

After writing, require aligned, unique, non-overlapping chunks; matching tags, declared lengths, and `mmap` entries; canonical decode/re-encode of every new chunk; zero out-of-whitelist changes in the original file region; and an independent ProjectorRays or equivalent reparse.

Static reparse proves container structure, not in-game readability. Keep runtime acceptance separate.

## 6. Measure rendered width, not only bytes

Encoded byte length and rendered pixel width are independent constraints. A GBK sentence can fit its CP932 byte slot and still clip at the right edge or expose a stray final stroke because old Director wrapping is unreliable for continuous Chinese text.

Measure every dynamic line through the target ANSI rendering route. On Windows, prefer `CreateFontA` plus `GetTextExtentPointA` with the exact target bytes, font face, size, weight, and device context used for calibration. Do not substitute a different renderer such as .NET `TextRenderer` without proving equivalent metrics. Compare the measured width with the decoded field or cast width, then establish a conservative safe limit from an actual Stage sample.

For every over-limit line:

- reopen the Japanese source and surrounding context;
- shorten the Chinese manually instead of globally shrinking the font;
- preserve meaning, speaker, placeholders, and duplicate-group consistency;
- recheck strict GBK, slot bytes, measured width, and the final compiled resource.

Measure ending evaluations, status messages, and other alternate-size fields separately. Do not reuse a 20 px story threshold for a 12 px menu or 14 px summary field.

For bitmap-backed buttons and diagrams, validate encoded capacity and pixels separately: export, render or import, decode again, inspect every interaction state, and require the glyph box to remain within the original frame. When `BITD` uses PackBits or multiple planes, preserve untouched planes and geometry, require a legal encode/decode round trip, and reject meaningless padding used only to fill a compressed slot.

## 7. Treat dynamic status fields as composed layouts

A narrow field may combine a script label, separator, number, percent sign, and cached initial member. Translating the label in only one place can make the value disappear or overflow even when the static screenshot looks acceptable.

Trace the complete composition and enumerate representative and maximum values, including zero, one-digit, two-digit, and `100%` states. Patch all owning copies together: the runtime label literal, any initial text member, and any cached `RTE2` bitmap.

When the Chinese label cannot fit without harming the value, prefer a tested shorter label or compact ASCII abbreviation over deleting the value or shrinking the entire panel. Derive the abbreviation from the game's semantics; do not copy a label from another title. Preserve the field geometry and known-good font size unless the layout resource itself is deliberately in scope. Verify the final maximum string inside the real frame.

## 8. Rebuild downstream layers from a clean base

Use a deterministic chain:

```text
immutable original
  -> catalog-authorized fixed-slot text patch
  -> resource-derived font/cache rebuild
  -> paired runtime fixture
  -> portable release
```

Bind every step to its exact input file hash, upstream report hash, translation-source hashes, and resource payload hashes. A one-line edit inside an `Lscr` resource legitimately changes the hash of the whole resource; rebind that resource only after parsing the new clean-base output.

Never continue appending to a stale previous candidate after translation, punctuation, layout, font, or field text changes. Recompile from the immutable original, then regenerate `RTE2`, reports, fixtures, and release manifests. Make hash mismatches fail before creating the candidate, preview, report, or log, and keep a negative test proving this fail-closed behavior.

After each build, reparse from disk and compare:

- expected target count and zero old target occurrences;
- changed-resource whitelist and byte-diff ranges;
- fixed file prefix and non-target resources;
- container sizes, map offsets, alignment, and overlap;
- declared output hash and actual output hash.

## 9. Automate Director input and capture conservatively

Director distinguishes `mouseDown` and `mouseUp`. A handler can change frames on button-down, allowing the later button-up to hit a sprite on the new frame and look like an automatic branch. Before automation, release all mouse buttons, park the pointer at a proven neutral Stage coordinate, wait for the expected frame to stabilize, and send a new complete click only after the transition.

Do not hard-code desktop coordinates. Opt the helper into physical-pixel DPI awareness before reading window rectangles, capturing, or clicking; otherwise 125% scaling can mix logical `GetWindowRect` coordinates with physical screen pixels.

Serialize launch, focus, capture, pointer movement, and click operations. Require one exact-path game process and stop input immediately on an unexplained state transition. A file named `title.png` is not title evidence unless its pixels are inspected; record actual screen identity and mark miscaptures or unexpected transitions `NOT_VALIDATION`.

If DirectDraw capture fails, leave visual confirmation explicitly incomplete and retain supporting process, window, byte-readback, resource-preview, and reparse evidence. Do not replace the missing Stage observation with blind clicks.

## 10. Require layered acceptance

Static acceptance:

- original and source-media hashes unchanged;
- catalog coverage, strict encoding, slot budgets, duplicate consistency, and prohibited-character checks pass;
- all changed Director resources reparse and round-trip as required;
- non-target bytes/resources remain unchanged;
- translated Projector and main movie reports bind the exact final hashes.

Runtime acceptance on one integrated fixture:

- exact Projector and movie pair is present before launch;
- process path and working directory are correct and the process remains responsive;
- title, manual, introduction, menu, date, story text, dynamic status fields, and maximum-width values are readable and unclipped;
- no residual Japanese or mojibake appears in the screens actually exercised;
- the documented graceful exit path works and leaves no residual process;
- fixture and original hashes remain unchanged after the test.

Record a user's manual playtest as a distinct evidence source. It can close a stated manual-check requirement, but it must not be relabelled as a screenshot or automated assertion that was never captured.

Package acceptance:

- ship only the accepted pair plus proven original dependencies;
- include hashes, build reports, usage notes, and an explicit runtime-acceptance report;
- scan for build-machine absolute paths and stale candidate hashes;
- preserve the immutable original, current successful build, translation sources, tools, and necessary rollback evidence;
- delete failed full-game fixtures only after their compact evidence is retained and an exact delete/keep list is approved.

Never promote a container-only parse, a single-component probe, or a wrongly labelled screenshot into integrated runtime acceptance.
