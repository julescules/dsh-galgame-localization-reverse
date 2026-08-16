# SILKY'S/AI6WIN ARC, AKB UI, and Portable Releases

Use this reference for SILKY'S/AI6WIN games whose UI is image-baked in `layer.arc`, especially when static PNG previews look correct but hover, disabled, pressed, slider, or startup states fail at runtime.

## Establish the archive variant

Do not assume every archive called `*.arc` uses the same SILKY'S layout. Confirm the index from bytes and a known implementation.

For the older AI6WIN variant, expect:

- a file count;
- fixed-size index records;
- a `0x104`-byte obfuscated name field;
- three big-endian 32-bit fields describing offsets and sizes;
- per-entry compressed or stored payloads.

Prove a zero-mutation round trip before replacing content. Preserve the exact packed bytes of unchanged entries. When the engine accepts stored payloads where packed and unpacked sizes match, use that for deterministic replacements instead of inventing a new compressor. Verify entry count, names, offsets, unpacked hashes, and unchanged-payload identity after every rebuild.

## Preserve AKB structure

Treat AKB as an image container plus runtime layout metadata, not as a generic bitmap.

1. Decode and record the original header, pixel format, full dimensions, channel order, canvas rectangle, and compression mode.
2. Re-encode from the original AKB template. Preserve header fields and canvas coordinates exactly.
3. Encode only the declared canvas crop when the original payload stores a sub-rectangle. Do not silently expand a cropped AKB to the full PNG.
4. Preserve BGR24 versus BGRA32. A startup card can be BGR24 while UI atlases use BGRA32.
5. Decode the rebuilt AKB and compare rendered pixels with the intended PNG before packing the ARC.

A full-size PNG can look correct while the engine clips it because the AKB canvas is smaller. Keep every visible glyph inside the template canvas with a measured safety margin.

## Audit every atlas state

Do not infer state count from what is visible on a white image viewer. Inspect RGBA values and composite each atlas column or row over gray and over a representative game background.

Low-alpha white hover states can appear blank on white. Translate normal, hover, selected, pressed/transition, and disabled states separately. Enumerate state cells from alpha/color evidence and runtime behavior; do not skip a transparent-looking column.

Some AI6WIN atlases share or overlap pixels between unrelated controls. A compact display-button bank can overlap ON/OFF labels and slider-handle sprites. Therefore:

- never clear a whole guessed cell until its runtime crop is proven;
- preserve native borders, gradients, alpha, and shared pixels;
- erase only the measured glyph band or glyph mask;
- restore dynamic sprite regions from the pristine source after text edits;
- keep transition-only shared rows blank rather than drawing into a region owned by another control.

If rebuilding a button frame causes stacked frames, floating labels, or duplicated borders at runtime, revert to the original pixels and replace only the glyph region.

### Measure each control family independently

Do not assume one atlas uses a uniform row height or cell grid. A single AI6WIN image can place several control families side by side with different state dimensions. For example, per-character `ON/OFF` buttons may use four `70x27` cells while `ALL ON/ALL OFF/RETURN` buttons in the same top strip use four `118x36` cells. Treating both families as 36-pixel rows makes the engine crop adjacent states, producing half glyphs, narrow hover bars, and text that jumps vertically.

Before drawing:

1. Detect the rounded-frame boundaries, separator pixels, alpha transitions, and repeated state colors for each x-range.
2. Record a state table per control family: x-range, y-range, width, height, alpha behavior, and runtime meaning.
3. Composite every cell independently over black, white, and gray; a low-alpha fourth state can look blank in one viewer but still appear during mouse movement.
4. Preserve each family's original state count and coordinates exactly when re-encoding the AKB.

To remove text without flattening the native button, clear only the interior glyph band. For each scanline, sample untouched pixels near the left and right interior edges and interpolate between them. Leave the rounded border, bottom shadow, gradient, and native alpha untouched. Draw the replacement using visible CJK bounds inside an inset safe box, and match the original state's alpha: normal, white, selected purple, and low-alpha transition states must not all become opaque.

Verify the atlas at native scale and enlarged nearest-neighbor scale. Then test every small and large button at runtime in normal, selected, hover, mouse-down, and mouse-leave transitions. A correct static normal state is not sufficient evidence.

## Render CJK by visible bounds

Font baselines are not reliable for tightly packed CJK atlases. `anchor="mm"` can visually place Chinese too low even when the mathematical center is correct.

Measure the rendered glyph bounding box and place that visible box inside the safe band:

```python
bounds = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
w = bounds[2] - bounds[0]
h = bounds[3] - bounds[1]
x = (left + right - w) / 2 - bounds[0]
y = (top + bottom - h) / 2 - bounds[1]
draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke)
```

Inspect antialias and stroke spill outside the intended band. A selected Japanese glyph can extend several pixels into the preceding state; remove both the light body and dark halo. If a color mask leaves fragments, clear the complete proven spill band while retaining its separator line.

## Validate runtime behavior, not screenshots alone

Exercise every state that can select a different atlas frame:

- title menu normal and mouse hover;
- config buttons normal, hover, selected, disabled, and transition;
- toggles both on and off;
- sliders at left, middle, and right, including hover and drag;
- startup notices through their complete display lifetime;
- save/load, history, confirmation, gallery, and music/voice pages.

Do not draw a fixed knob into a main-panel background to repair a missing slider. First compare the original behavior. Disabled speed sliders may intentionally hide their knob until the corresponding toggle is enabled.

Capture the real output at the game's physical resolution. On DPI-scaled Windows desktops, make the capture process DPI-aware before reading window coordinates; otherwise a 1920x1080 game can be captured as 1536x864 and important bottom rows can be missed.

## Build a drive-independent portable release

Treat build location and player install location separately. The working project may live on one drive, but the finished game must use relative paths and run from any normal local drive.

1. Inventory runtime files and distinguish archives, executable, INI/config, saves, manuals, uninstallers, old backups, loose patch-source PNGs, and build artifacts.
2. Inspect INI/config and executable strings for absolute paths. Prefer archive names relative to the executable directory.
3. Check the exact historical registry key. Do not keep a registry-import batch merely because an old release included one. Test whether the current executable actually requires it.
4. Stage only runtime-required files in a clean project-side directory. Exclude uninstall metadata, Japanese executables, original-archive backups, old patch notes, probes, and developer tools.
5. Preserve user saves separately. For a distributable clean build, ship an empty save directory; for a personal migration build, copy saves only when explicitly intended and record their hashes.
6. Launch from at least one clean alternate path with spaces and CJK characters. Change the test directory name or location without editing the INI. Verify launch, title hover, config interaction, save creation, exit, and relaunch.
7. Scan the final tree for build-machine drive prefixes and absolute project paths. A hit in documentation can be acceptable when declared; a hit in runtime configuration or launcher code is a blocker.
8. Produce a manifest with relative paths, sizes, SHA-256 hashes, source/candidate hashes, excluded files, save policy, registry result, and rollback instructions.

Do not impose a drive letter. If legacy registry discovery is genuinely required, provide an optional relative-path launcher or per-user registration step and verify cleanup; do not require administrative HKLM writes unless runtime evidence proves no safer option works.
