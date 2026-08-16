# Engine Signature and Detection Matrix

Read this file to identify a Windows galgame/visual novel engine from on-disk evidence when the target is **not** one of the engines already covered by a dedicated reference (KiriKiri, NScripter/ONScripter, Ren'Py, Unity, RealLive/AVG2000, Director, SPT60/ASZB). It expands the detection table in `SKILL.md` to the wider set of mainstream commercial VN engines.

## How to use this file

1. Detect before extracting. Prefer observable files, archive magic bytes, and executable/DLL names over guesswork. Never infer an engine from folder names alone.
2. Confirm with at least two independent signals: an archive magic byte plus a script signature, or an engine EXE/DLL name plus a config file layout.
3. Once identified, pick the lowest-risk extraction route from the `Extraction route` column, and keep protection/authorization work in a separate research layer exactly as `SKILL.md` requires.
4. If nothing matches, fall back to the `Unknown/custom` route in `SKILL.md`: prove file boundaries, compression/encryption layers, and text ownership with DiE/GARbro/QuickBMS/Ghidra before building automation.

Tool names below (GARbro, GARbro-derived scripts, QuickBMS, engine-specific extractors) are analysis backends. Bind every extraction and repack to exact input/output hashes, keep originals immutable, and prefer file-overlay or differential patches over full repacks, as in `SKILL.md` and `engine-and-tooling.md`.

## Archive magic-byte quick scan

Run a raw header scan across the game directory before committing to an engine guess. Common leading signatures:

| Bytes / ASCII magic | Likely engine/format | Notes |
| --- | --- | --- |
| `XP3\r\n \n\x1a` | KiriKiri `.xp3` | See KiriKiri route in `SKILL.md`. |
| `YPF\x00` | Yu-Ris `.ypf` archive | Scripts are `.ybn` with `YSTB`. |
| `PackFile` / `FilePackVer3.0` | QLIE `.pack` | Version string embedded near header/footer. |
| `ESC-ARC1` / `ESC-ARC2` | Escude `.bin` archive | Two archive generations. |
| `BURIKO` / `BurikoCompiledScriptVer1.00` | BGI/Ethornell/BURIKO | Signature lives in compiled script blob. |
| `MajiroArcV1.000` / `MajiroArcV2.000` / `MajiroArcV3.000` | Majiro `.arc` | Script objects: `MajiroObjX1.000`. |
| `KIF` / `CatScene` | CatSystem2 `.int` / `.cst` | `CatScene` marks compiled scene scripts. |
| `PACK` / `GAMEDAT PAC` | Softpal / AMUSE CRAFT `.pac` | Also seen in NeXAS. |
| `pf6`/`pf8`/`.pfs` header | Artemis `.pfs` | Also `root.pfs`, `root.pfs.000`. |
| `LIVEMAKER` / `LiveMaker` in EXE | LiveMaker/LiveNovel | Self-extracting EXE, `.lsb` scripts. |
| `RGSSAD` (`.rgssad`/`.rgss2a`/`.rgss3a`) | RPG Maker XP/VX/VX Ace | RGSS runtime DLL present. |
| `DX` archive + `GuruguruSMF4.dll` | WolfRPG | `Data/*.wolf` game archives. |
| `Scene.pck` + `Gameexe.dat` | SiglusEngine | VisualArts/Key modern engine. |

Absence of a known magic does not prove a custom engine — many archives are keyed/obfuscated. Cross-check the executable, DLLs, and script folders too.

## Engine detection matrix

| Engine | Observable evidence | Script/text location | Extraction route | Writeback/release route | Localization notes |
| --- | --- | --- | --- | --- | --- |
| **SiglusEngine** (VisualArts/Key, post-RealLive) | `SiglusEngine.exe`, `Scene.pck`, `Gameexe.dat`, `.g00`/`.omv` assets, `Scene.pck.txt`? no | Compressed script blobs inside `Scene.pck` | SiglusExtract-class tool to split `Scene.pck`; decode string tables | Rebuild `Scene.pck` with exact record layout, or overlay if loose scenes supported | Wide CJK support but fixed string tables; freeze index/label keys and re-pack with identical record count. Test save compatibility — Siglus saves persist scene state. |
| **Artemis** | `.pfs`/`root.pfs(.000)`, `.ast` scripts, `System/`, engine EXE named per game | `.ast` text scripts (human-readable) | GARbro or `.pfs` extractor; `.ast` is near-plaintext | File overlay of edited `.ast`, or rebuild `.pfs` | One of the friendliest engines; scripts are readable. Preserve control tags and speaker markup exactly. |
| **BGI / Ethornell / BURIKO** (Overflow etc.) | `data*.arc`, `BGI.exe`/`Buriko\`, `_bp` scripts, `BurikoCompiledScriptVer1.00` | Compiled script blobs in `.arc` (offset-indexed strings) | GARbro / ethornell extractor (`exkifint`-class); many builds keyed | Patch string table in place preserving offsets, or rebuild `.arc` | Strings are offset-referenced — changing length shifts the table; prefer fixed-slot or full table rebuild with recomputed offsets. |
| **Yu-Ris (YU-RIS)** | `.ypf` (`YPF\x00`), `.ybn` scripts (`YSTB`), `ysbin`, `pac/` | `.ybn` compiled scripts + string pools | GARbro / YU-RIS tool; parse `YSTB` blocks | Repack `.ypf`, or overlay loose files where supported | Version-sensitive `.ybn` format; confirm exact YSTB version before writeback. |
| **Majiro** | `MajiroArcV*` `.arc`, scripts `MajiroObjX1.000`, engine EXE with "majiro" | Compiled `.mjo` objects, string tables | GARbro + majiro toolchain (disasm/asm) | Reassemble `.mjo` with matching opcodes, repack `.arc` | Bytecode engine — use the `bytecode-roundtrip.md` discipline (opcode/disasm/asm + byte-exact round trip). |
| **CatSystem2 (CS2)** | `.int` archives (`KIF`), `.cst` (`CatScene`), `.fes`, `.anz` images | `.cst` compiled scene scripts | GARbro / cs2 tools; decompress `.cst` | Recompile `.cst` or overlay; repack `.int` | Scene scripts carry choice/label indices — freeze them. Font atlas may need glyph remap for Chinese. |
| **QLIE** | `.pack` (`FilePackVer3.0`/`PackFile`), `GameData/`, key file | Scripts inside `.pack`, often keyed | GARbro (needs key extraction from EXE); QuickBMS variants | Repack `.pack` with correct key/version | Encryption key derived from the executable — bind analysis to the exact EXE hash. |
| **WillPlus / AdvHD / AdvPlayer** | `Rio.arc`, `.arc` (`PackFile`), `.ws2`/`.wsc` scripts, `AdvHD.exe` | `.ws2`/`.wsc` scripted text | GARbro / willplus tools | Overlay edited scripts or rebuild `.arc` | Common in modern commercial VNs. Preserve `@`/`\` control codes and ruby markup. |
| **Cmvs (Purple Software)** | `.cpz` archives, `Cmvs*.exe`, `.mc`/script blobs | Keyed script blobs in `.cpz` | GARbro (`.cpz` v1/v2), key from EXE | Repack `.cpz` matching version | Multiple `.cpz` versions with different keys; identify version precisely. |
| **Escude** | `.bin` (`ESC-ARC1/2`), `list.bin`, engine EXE | Script blobs + `list.bin` index | GARbro / escude tools | Rebuild `.bin` preserving `list.bin` index | Two archive generations; keep the index consistent with repacked entries. |
| **Softpal / AMUSE CRAFT / Unicorn-A** | `.pac` (`PACK`/`GAMEDAT PAC`), `System/`, engine EXE | Script + text resources in `.pac` | GARbro | Repack `.pac` or overlay | Shared-heritage family; verify sub-variant. |
| **NeXAS (Giga)** | `.pac` archives, `SDATA`, `NeXAS`/engine EXE | Script/text in `.pac` | GARbro / NeXAS tools | Repack `.pac` | Uses LZSS-class compression; validate decompressor round-trip. |
| **Malie / Malie@ (light, ωstar)** | `.lib`/`.libp` archives, `.dat`, Malie EXE | Script blobs inside `.lib` | GARbro (keyed variants) | Repack `.lib` matching key/version | Some titles keyed per product; bind to EXE hash. |
| **LiveMaker / LiveNovel** | Self-extracting EXE, `.lsb` scripts, `LiveMaker` strings | `.lsb` compiled scripts | livemaker python lib / LiveMaker tools | Recompile `.lsb`, repack EXE data | `.lsb` is a structured bytecode; use round-trip discipline. Text often embedded with rich formatting nodes. |
| **RPG Maker MV/MZ** | `Game.exe` (NW.js), `www/`(MV) or root `js/`+`data/`(MZ), `package.json`, `.rpgmvp`/`.png_` | `data/*.json` (Actors, Items, Map*, CommonEvents, System) | Direct JSON edit; decrypt `.rpgmvp` if encrypted (key in `System.json`) | Overwrite `data/*.json`; re-encrypt images if needed | Plaintext JSON — very translation-friendly. Use Translator++-class flow. Freeze `\V[n]`, `\N[n]`, `\C[n]`, `\.`, `\|` escapes. |
| **RPG Maker VX / VX Ace / XP** | `Game.exe`, `RGSS*.dll`, `Game.rgssad`/`.rgss2a`/`.rgss3a`, `Data/*.rvdata2`/`.rxdata` | Marshal-serialized `Data/*` (Ruby Marshal) | RPG Maker Decrypter to unpack RGSSAD; parse Marshal | Repack RGSSAD or run loose (`Data/` extracted) | Text lives in Marshal objects — use Translator++ or a Ruby Marshal parser. Preserve control codes as MV/MZ. |
| **WolfRPG (Wolf RPG Editor)** | `Game.exe`, `GuruguruSMF4.dll`, `Data/*.wolf`, `.mps` maps, `DataBase*.dat` | Maps `.mps`, `DataBase`, `CommonEvent.dat` | WolfDec/DXExtract to unpack `.wolf`; wolf tools to parse | Repack or run loose | Encrypted `.wolf` needs the correct decrypt key/version. Text in maps and DB; watch fixed-width command args. |
| **TyranoScript / TyranoBuilder** | `data/scenario/*.ks`, `tyrano/`, `index.html`, NW.js `Game.exe` | `.ks` KAG-style scenario scripts (plaintext) | Direct edit of `.ks` | Overwrite `.ks` in place | HTML5/JS engine — scripts are plaintext. Preserve `[tag]` macros and `&exp` expressions. |

## Cross-cutting rules

- **Bytecode engines** (Majiro, LiveMaker, and any custom VM) require the `bytecode-roundtrip.md` workflow: build `vm_analysis.md` first, implement `opcode.py`/`disassembler.py`/`assembler.py`, and prove a byte-for-byte round trip before editing text.
- **Keyed archives** (QLIE, Cmvs, Malie, some KiriKiri/WolfRPG) derive their key from the executable or a key file. Bind extraction/repack to the exact EXE/key hash; a game update that changes the key invalidates every downstream artifact.
- **Offset-referenced string tables** (BGI/Ethornell, some Siglus/CatSystem2) break when a translated string changes length. Either keep fixed slots or rebuild the whole table with recomputed offsets and pointers, then verify in-engine.
- **Font/glyph capacity**: Japanese engines frequently ship a font atlas or codepage-limited renderer. Confirm the target Chinese characters render before committing translation; plan glyph-atlas remap or font substitution where needed, and keep it as a separate payload layer.
- **Save/resume**: engines that persist scene + program-counter state (Siglus, RealLive-family, bytecode VMs) can break saves when script offsets move. Follow the compiled-script save rule in `SKILL.md`: replay real save PCs against original and rebuilt scripts, and require an explicit migration if offsets cannot stay stable.
- **Encoding**: default candidates remain `utf-8-sig`, `utf-8`, `cp932`, `shift_jis`, `gbk`. Treat `cp932`/MS932 as the practical match for most Japanese Windows scripts.

## When the engine is still unknown

If no signature, EXE/DLL name, or script layout matches:

1. Run Detect It Easy on the main EXE and any custom DLLs for packer/compiler hints and embedded engine strings.
2. Open the largest archives in GARbro; if it recognizes the format it will name the engine.
3. Header-scan archives for the magic bytes above and any ASCII version strings near the header/footer.
4. If archives are opaque, use QuickBMS trial scripts or Ghidra/x64dbg on the archive-reader routine to recover the container format before any writeback.
5. Only after boundaries, compression/encryption, and text ownership are proven, build project-specific extraction — and keep it hash-bound, reproducible, and reversible.
