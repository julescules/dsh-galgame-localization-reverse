# PhotoKano Kiss PSV CPK/GXT Lessons

Use this reference for PhotoKano Kiss PSV / PCSG00139 style localization tasks where text, font pages, CRI CPK archives, Vita3K installs, and VPK packaging all interact.

## Non-negotiable checks

- Treat original VPK/CPK/EBOOT files as read-only inputs. Generate patched packages separately.
- Do not patch compressed CRILAYLA members in place when the archive reader reports decoded-size errors. Rebuild the whole `00_GMV.cpk` and read it back.
- Do not apply offsets from an extracted `eboot.bin.elf` CSV directly to a raw VPK `eboot.bin`. Prove which binary the offsets target before writing.
- Use UTF-8 shell/Python settings on Windows, and explicitly decode Japanese script bytes as CP932/Windows-31J when that is what the game uses.
- Keep generated VPKs, CPKs, probes, extract-verify outputs, and logs under the project directory, not Desktop/Downloads/temp roots.

## Text and font mapping workflow

1. Trace a visual bug from screenshot to resource ID, offset, original Japanese, target Chinese, slot-encoded string, and CP932 bytes.
2. For each target character, record the slot character, CP932 hex, font resource ID, atlas cell coordinates, and mapping method.
3. Distinguish these cases before editing:
   - text bytes are wrong,
   - slot mapping is wrong,
   - the runtime reads a different atlas cell,
   - the glyph is correct but visually inconsistent because it reused an original protected CJK glyph.
4. For PSV font work, do not copy PSP page numbers or offsets blindly. Rebuild evidence from PSV slot maps, runtime cell order, and GXT page coordinates.
5. Preserve characters used by name input, EBOOT UI, and original CJK slots unless evidence shows they can be repurposed safely.
6. When protected original glyphs look too heavy, too small, or stylistically different, add only the confirmed characters to a problem-glyph redraw list and rebuild from the current candidate.

Example evidence pattern:

```text
Resource: 00_GMV/ID06604
Offset: 0x00001330
Source: 「よかった、新体操始めて…」
Target: 「幸好开始学艺术体操了…」
Slot decode: 「幸好謂始学樺栢体操了…」
Finding: 幸 used protected_identity_unmodified at ID10256 x=800 y=288, so redraw the glyph rather than changing text.
```

## Image UI and GXT rules

- Decode the original GXT to PNG, edit only the intended cells, and re-encode with the original GXT as the template.
- Avoid broad alpha erases on shared atlases. Broad clearing can remove graph pieces, icons, cursor assets, or adjacent UI cells.
- When replacing image-baked Japanese text, erase the original text region without covering icons, numbers, or neighboring UI elements. Match the original cell/crop constraints instead of placing a full-size freeform label.
- For atlas cells that the runtime crops tightly, tune the text rectangle inside the cell rather than expanding the cell.
- Save decoded previews/checker previews for final-version evidence, but clean old previews after the final build is accepted.

## Build and verification workflow

1. Generate a new versioned candidate tree from the current accepted tree.
2. Rebuild full `00_GMV.cpk`; do not splice compressed members.
3. Extract the rebuilt CPK and verify the expected member count. For this project, the acceptance check was `10294/10294` with no missing IDs.
4. Compare key resource hashes between the candidate tree and readback extraction, including affected script IDs, affected GXT image IDs, and affected font IDs.
5. Keep localized EBOOT and localized CPK together. If a user reinstalls the original game, verify the installed `eboot.bin` hash again before packaging.
6. Package VPK from the verified install/app tree with:
   - correct top-level entries,
   - no `.bak` entries,
   - no Zip64,
   - embedded CPK/EBOOT hashes recorded.
7. Install to the active Vita3K data path and clear title-specific shader/cache folders before asking for visual retests.

## Finalization and cleanup

- Keep the final VPK, original package, final candidate tree, final QA reports, scripts, translation memory, and operation logs.
- After the user declares a final version, delete superseded VPKs, superseded candidate trees, old install backups, old probes, and old QA previews by whitelist.
- Log every build and cleanup with: timestamp, target, commands, changed paths, deleted/kept content, hashes, freed space, verification, and remaining risks.
- Cross-check free space after cleanup with both `Get-PSDrive` and `Win32_LogicalDisk` when available.
