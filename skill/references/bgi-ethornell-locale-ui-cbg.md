# BGI/Ethornell locale, layered UI, and CBG workflow

Use this reference for BGI/Ethornell/BURIKO projects where launch behavior depends on Windows locale, UI is assembled from multiple `sysgrp` layers, or subtitles and labels are baked into CBG images.

## Locale and code-page diagnosis

- Treat system locale, locale emulation, executable code-page handling, and localized runtime encoding as separate variables.
- Do not make Japanese-locale launch a prerequisite for a finished Chinese localization. Prefer converting or repairing the localized runtime so it supports the target Chinese encoding or Unicode without locale emulation when the engine permits it.
- When testing an original Japanese baseline or an intermediate build whose encoding conversion is incomplete, reproduce its proven launch method before blaming a new image or script override. A crash from ordinary launch is not evidence against the payload when the same baseline also requires Japanese locale or locale emulation.
- Record the exact launch condition with each result: native system locale, locale-emulator profile, compatibility launcher, or target-language runtime. Do not silently compare results obtained under different conditions.
- Verify the final Chinese build under its intended no-transfer launch path. Use the original Japanese-locale route only as a diagnostic control unless the release explicitly retains that dependency.

## Layered configuration UI

1. Inventory every state variant, not only the first image: normal, hover, pressed, disabled, and shared `990`/header layers.
2. Render transparent previews, but treat them as structural evidence only. The engine may composite a lower control layer, a foreground pane, and a higher label/header layer in a different order than the files suggest.
3. If text looks correct in PNG but only its outline or fragments appear in game, inspect occlusion and layer order before changing fonts or alpha. Move labels to a proven higher layer when a foreground pane covers the lower layer.
4. When an old highlight or separator crosses localized text, redraw the whole compact button or badge after clearing the original state artwork. Do not merely paint glyphs over a baked state stripe.
5. Keep rebuilt labels compact. Prefer transparent glyphs with a controlled outline or a small UI-native pill; avoid large opaque rectangles on full-page transparent overlays.
6. Test at least one screenshot for every state family. Bind each accepted screenshot to the deployed file hashes so a static preview cannot be mistaken for runtime proof.

## Locating image-baked subtitles

1. Search decoded scripts for the visible phrase using explicit CP932, UTF-8, and UTF-16LE byte sequences. If the exact phrase is absent, do not conclude that the text is missing from the game.
2. Search script resources for nearby asset identifiers and presentation macros. BGI projects may call a background movie plus separate transparent CBG subtitle layers.
3. Enumerate ARC members and inspect real signatures. A media filename can contain DSC-compressed MPEG data, while raw signature scans may find only uncompressed members.
4. Decode representative keyframes from each candidate family before performing a full batch. Build labeled contact sheets and compare font color, outline, screen coordinates, and timing indices with the runtime screenshot.
5. Treat an exact visual match between screenshot text and a named transparent keyframe as stronger ownership evidence than a fuzzy OCR guess.

## CBG replacement and verification

- Preserve width, height, alpha geometry, placement, and resource name. Keep the original ARC untouched when the engine accepts an overlay-folder resource with the member name.
- Decode CBG v2 for editing. If the available encoder writes CBG v1, do not assume compatibility solely because the engine family supports both versions; perform a decoder round trip and a runtime load test.
- For PNG → CBG → PNG validation, require identical dimensions and alpha bytes. Composite both images over white and black backgrounds; record maximum and mean RGB deltas. A one-level RGB quantization difference can be acceptable when alpha is identical and runtime loading succeeds.
- Verify candidate and deployed SHA-256 hashes. Add new overrides without inventing an old backup; back up only pre-existing override files.
- If an old C# encoder must be built with a legacy compiler, make minimal syntax-only downgrades before changing algorithms. Stop after repeated toolchain incompatibilities and switch to a deterministic Python port or another existing decoder/encoder.

## Cleanup and retention

- Before cleanup, list exact delete and keep roots and resolve every target under the project workspace.
- Delete extracted movie probes, duplicate decoded CBG directories, contact sheets, failed audit outputs, and failed compiler intermediates after their conclusions are captured in a log.
- Keep original archives, accepted overlay files, the current release candidate, one necessary rollback point per active change, source render/decoder tools, manifests, hashes, and operation logs.
- Measure reclaimed space and verify accepted files and original archives still exist after cleanup.
