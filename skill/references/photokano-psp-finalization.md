# PhotoKano PSP Finalization Notes

Use this reference when a PSP visual novel localization has moved from extraction and translation into final package QA, cleanup, and release preparation. It captures the working lessons from the PhotoKano PSP Simplified Chinese completion pass.

## Final Text Completion

- Treat the UTF-8 translation ledger as the semantic source of truth, but verify the patched binary output separately. Slot remapping and CP932-compatible glyph reuse can make byte-level scans look Japanese even when display text is Chinese.
- Audit three layers independently: DATA text resources, EBOOT/BOOT runtime strings, and image-baked UI atlases. Do not assume one layer owns every visible string.
- Use contextual terminology checks before global replacements. For example, distinguish a literal nickname from a heroine's deliberate line reading; only change the translation when the source/context proves it is a terminology drift.
- Keep name/personality/save/return confirm prompts short when they are fixed-slot runtime strings. Prefer compact forms such as `是` and `否` when layout and slot length are tight.

## Runtime And Image UI

- When runtime prompts render through an encoded font map, fix the text source and mapping before editing images.
- If image labels become less readable after localization and the user prefers the original icon art, revert or avoid those image-label edits and focus on runtime text completion.
- For UI atlas work, keep background, decorative layers, alpha, palette/index mode, and button geometry intact. Redraw only the text layer unless there is clear evidence that the base image itself is wrong.

## Final Build Verification

Before declaring a build final, regenerate from clean original inputs:

1. Build DATA1 from a clean `DATA1.ORIGINAL.DNS`.
2. Verify the combined DATA1 patch and require changed bytes outside declared ranges to be `0`.
3. Patch the ISO by file replacement or raw extent replacement.
4. Verify ISO replacement and require byte changes outside the replaced file extent to be `0`.
5. Hash the final ISO and write a release manifest with source hashes, target hashes, target list, and validation pass names.
6. Keep one canonical final release directory with the final ISO, hash, manifest, user-facing notes, and small supporting evidence.

Useful final pass names from the PhotoKano run:

- `PASS_BM_FINAL_TEXT_RESIDUAL_AUDIT`
- `PASS_BM_DARLING_DATCHAN_CONTEXT_AUDIT`
- `PASS_BM_ISO_SYSTEM_AUDIT`
- `PASS_COMBINED_DATA1_STATIC`
- `PASS_ISO_FILE_REPLACEMENT`

## Cleanup And Retention

Use a retention policy before deleting generated artifacts:

- Keep: original package, clean original DATA files, final ISO, final hash, final manifest, final DATA1 candidate, final verify JSON, source tools, translation masters, operation logs, and a small evidence bundle.
- Delete: old failed ISOs, old candidate DATA files, probe folders, preview screenshots, font/image trial folders, Python caches, replay snapshots superseded by named final masters, and regenerated compressed/script intermediate directories.
- Move rather than delete loose one-off helper scripts if they may contain unique translation context.
- Log cleanup with before/after free space, exact deleted paths or a deletion-plan JSON, preserved paths, and verification that final/original artifacts still exist.

## Public Repository Boundary

For public release, prefer a repository that contains tooling, docs, manifests, checksums, build instructions, and optionally binary-differential patch instructions. Do not publish the full original ISO, rebuilt ISO, decrypted DATA files, extracted commercial assets, or full copyrighted script dumps.

If a reference project is available, mirror its user-facing structure rather than its exact assets: requirements, patch/apply instructions, checksums, troubleshooting, credits, and support notes. Keep the legal and technical boundary explicit in `.gitignore` and release docs.
