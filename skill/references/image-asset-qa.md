# Image asset QA and multimodal review

Use this route for image-baked text, UI atlases, sprite-state sheets, menus, title screens, transparent overlays, animated GIF/APNG assets, or any localization layer that replaces raster files.

## Evidence boundary

Treat model vision as a review aid, not proof of runtime geometry or alpha correctness. Keep three evidence classes separate:

1. deterministic file facts: path, hash, format, dimensions, bit depth, transparency capability, animation frame count;
2. visual review: untranslated text, clipping, contrast, alignment, state consistency, and obvious artifacts;
3. runtime proof: the engine loads the asset and every normal/hover/pressed/selected/disabled state renders at the expected coordinates.

A visually convincing screenshot does not replace deterministic geometry checks or runtime state coverage.

## Inventory and comparison

The bundled `scripts/vn_image_qa.py` is dependency-free and understands PNG/APNG, JPEG, GIF, and BMP metadata.

Create an immutable original inventory before editing:

```powershell
python -X utf8 scripts\vn_image_qa.py inventory D:\project\original\images -o D:\project\logs\original-images.json
```

Compare the localized tree against the original:

```powershell
python -X utf8 scripts\vn_image_qa.py compare D:\project\original\images D:\project\working\localized-images -o D:\project\logs\image-qa.json
```

The comparison fails on missing assets, unreadable images, format changes, geometry changes, alpha loss, or animation-frame changes. Extra and byte-identical assets are warnings. Use `--allow-missing` only when the payload is an explicitly documented sparse overlay; do not use it to hide incomplete localization.

The tool intentionally does not decode engine-native containers such as AKB, CBG, G00, GXT, ASZB, or proprietary atlases. Convert those through the proven engine-specific round trip first, then compare the decoded raster stage and separately verify the rebuilt native container.

## Visual and runtime review

- Preserve the original canvas, sprite grid, control-family grouping, border pixels, alpha, gradients, and every runtime state unless the engine contract proves a change is safe.
- Review at native scale and nearest-neighbor magnification. Do not use a smoothed preview to approve pixel geometry.
- For multimodal model review, provide paired original/localized crops with the asset path and expected state. Ask for specific observations, not a generic quality score.
- Re-run the deterministic comparison after every accepted visual edit. A changed image invalidates downstream container hashes, patch manifests, installer payloads, and screenshots.
- Exercise normal, hover, pressed, selected, disabled, transition, and leave states in the real engine where those states exist.

Store inventories, comparison reports, screenshots, and runtime notes under the project logs or QA directory. Bind the accepted report hash to the release manifest.
