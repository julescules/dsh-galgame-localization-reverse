# Delphi/DirectDraw fixed-slot localization and portable runtime

Use this reference for legacy Delphi visual novels whose story text lives in a fixed-slot binary container while names, system UI, menus, and image-baked text are owned by separate executable or bitmap resources. It also covers DirectDraw child-window input problems and registry-to-portable launch wrappers.

## 1. Prove the full fixed-slot region

Do not define a catalog with a language-character whitelist. Valid slots can contain punctuation-only timing text, circled state markers, one-character labels, or runtime tags. Establish membership structurally: prove the container entry, aligned slot width, encoding, terminator, zero padding, bounded contiguous region or verified index table, and compare every old catalog offset against the immutable baseline.

Require a zero-mutation rebuild with an identical hash. For a 96-byte UTF-16LE slot, the normal hard capacity is 47 UTF-16 code units plus NUL unless the engine proves another convention. Count UTF-16 units, not Python characters or displayed glyphs. Use `scripts/vn_slot_qa.py` to scan a proven region and compare original/rebuilt containers.

When a structural rescan expands the catalog, rebuild ordinal slices and context fields. Invalidate old totals, candidate builds, and reports bound to the incomplete catalog. Freeze markers such as `@c(...)`, `@n(...)`, `@w(...)`, and `①`-`⑳`; preserve their sequence unless tracing proves they are visible prose.

## 2. Keep text ownership separate

Map ownership instead of treating story replacement as complete localization:

| Layer | Typical resource | Typical ownership |
|---|---|---|
| Container slots | UTF-16LE fixed slots | dialogue, narration, dynamic names |
| Executable tables | CP932/ANSI ranges | fixed names, short system messages |
| Delphi DFM in `RT_RCDATA` | binary form, often CP932 ANSI | captions, settings, popup and save/load items |
| PE `RT_STRING` | UTF-16LE resources | standard buttons, warnings, VCL messages |
| Bitmap entries | BMP or engine-native image | title, maps, galleries, dates, credits, signs |

Use exact offsets and hashes for executable tables. Garbled names often identify a CP932 table decoded through the wrong code page. Do not repair layout by padding names. When a translated menu label becomes inert, preserve the object, command ID, event handler, and submenu structure and change only its proven text owner.

## 3. Validate translation and layout

Select batches by explicit ID and state, not by an empty translation field. Verify ID uniqueness, exact ordinal slice, frozen source, marker sequence, capacity and terminator, absence of replacement characters, and old-translation match before semantic patches. Review adjacent slots for split sentences, grammar, negation, subject/object direction, pronouns, titles, and repeated terminology.

## 4. Patch fixed-size bitmap resources

Inventory every entry and every state: normal, selected, hover, pressed, disabled, and transition. Preserve entry index and byte length, dimensions, bit depth, stride, pixel offset, palette, transparency key, sprite coordinates, borders, gradients, state order, and untouched pixels. For paired frames, reconstruct the full canvas, edit once, then cut at the exact original boundary. Treat two branches changing one entry as a conflict. Static geometry is not runtime proof; test menus, maps, galleries, dates, save/load, and credits in-game.

## 5. Repair VCL menus without breaking commands

Enumerate the window tree and prove the VCL object, owner thread, handler or virtual `Click` path for each popup item. Keep execution on the UI thread and distinguish positioning from dispatch. Synthetic mouse messages or blind `WM_COMMAND` calls can make a menu visible while commands remain inert. Prefer the proven item `Click` path after the original popup-preparation callback.

Save/load captions may be dynamically populated. Preserve slot dates, locations, and registration state. Center modal forms relative to the real draw rectangle. Acceptance covers title Load, story right-click, Save, Load, Settings, Return to title, Exit, cancellation, repeated open/close, and nested modal attempts.

## 6. Build a portable launcher

Resolve paths from the launcher directory and never embed build-machine paths. When an install-directory registry value is required: snapshot key/value existence and types; write the launcher directory immediately before launch; use it as working directory; wait for game/helpers; restore prior values/types exactly or remove newly created values; verify restoration on normal and failed exits.

Keep saves local only after proving engine behavior and exclude saves from patch ownership. Scan payloads for absolute build paths, inspect PE runtime imports, and verify a move/rename launch. A temporary registry shim is portable only when it leaves no persistent state. State the tested Windows/runtime scope rather than claiming universal compatibility.

## 7. Reject display scaling that breaks input

Outer-window size does not prove DirectDraw render scaling. `TForm1` may fill the desktop while `TDXDraw` keeps its original size, creating borders and input offsets. Record parent/child rectangles and active DPI. A wrapper's child-window mode may deliberately avoid upscaling; forcing it off can scale pixels while desynchronizing hit testing.

Reject a candidate if title buttons, story/choices, right-click menu, save/load slots, settings/modals, redraw, or clean exit fails. Black borders are acceptable when sharp moderate scaling is preferred. Never describe a borderless parent as working fullscreen while the draw child remains unscaled.

## 8. Finalize and clean derived versions

Separate runnable release from source/evidence. Keeping one game version permits removing superseded runnable candidates, not original media, catalogs, translations, tools, or logs. Before deletion, enumerate complete executable-plus-container trees, resolve every target within the project root, measure free space, and record protected hashes.

The final directory should have one obvious relative-path launcher, concise usage/compatibility notes, and a hash manifest. Preserve source elsewhere, remove stale probes from player payload, and verify move/rename launch, saves, registry rollback, and all menu paths.
