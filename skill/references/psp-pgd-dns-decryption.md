# PSP PGD/DNS Decryption Triage

Use this reference for local PSP localization and reverse-engineering work involving `.DNS` or PGD-encrypted archives, including PhotoKano/ULJS00378-style `DATA*.DNS` files. Keep decryption artifacts reproducible and hash-bound; do not use the workflow for full-game redistribution or public release of original assets.

## First checks

- Identify PGD containers by the magic bytes `00 50 47 44`.
- Parse the PGD header before trying keys. Useful early fields are:
  - `version` at `+0x04`.
  - `drm_type` or header mode at `+0x08`.
- `drm_type == 1` generally follows the non-fuse PGD path with cipher and MAC type 1.
- `drm_type != 1` generally follows the type 2 or fuse path.
- Do not assume keys from adjacent DATA files apply to a new file. Some games keep explicit keys only for specific archives and use EDAT-derived PGD keys elsewhere.

## Explicit CRI DNAS key path

Some PSP games load specific `.DNS` files through game-provided CRI DNAS keys, usually visible near path strings and a call shaped like:

```text
sceIoIoctl(fd, 0x04100001, key_ptr, 16, NULL, 0)
```

Confirm this path by finding both the file path and the ioctl/key setup. Record proven per-archive keys only in the private project manifest; do not hard-code title-specific keys in reusable tooling or public documentation. If the target archive is not present in the path/key table, stop brute-forcing default ASCII keys and check the EDAT-derived PGD path.

## EDAT-derived PGD key path

The PSP amctrl/PGD model can derive a version key (`vkey`) from the PGD header itself. Primary implementation references are PPSSPP `sceIo.cpp` and `ext/libkirk/amctrl.c`, plus JPCSP's PGD routines when a second implementation is useful.

The practical model:

1. Run the PGD open flow with a null explicit key.
2. Derive `vkey` from the PGD header using MAC `0x80` / MAC `0x70` and the fixed DNAS key family:
   - `drmDNASKey1` when `pgd_flag & 2`.
   - `drmDNASKey2` when `pgd_flag & 1`.
3. Decrypt the PGD descriptor.
4. Treat descriptor bytes `[0:16]` as the data key (`dkey`).
5. Read descriptor metadata:
   - `+0x14`: `data_size`
   - `+0x18`: `block_size`
   - `+0x1c`: `data_offset`
6. Decrypt payload blocks with `dkey` as the header key and `vkey` as the version key. The block seed is `(block_offset >> 4)`.

For user-facing notes, report the derived `vkey` as the archive key. Do not mistake the descriptor `dkey` for the archive key when the file used the EDAT-derived path.

## Evidence record template

Keep sample-specific values in a private, hash-bound report rather than reusable code:

```text
input_file: <relative archive path>
input_sha256: <sha256>
key_source: explicit-table | edat-derived
derived_vkey: <redacted in public reports>
mac_0x80: pass | fail
pgd_mode: <mode>
data_size: <hex and decimal>
block_size: <hex and decimal>
data_offset: <hex and decimal>
output_sha256: <sha256>
```

Run project helpers with project-relative or parameterized paths, for example:

```powershell
python .\tools\decrypt_pgd.py .\original\DATA.DNS -o .\working\decrypted\DATA.bin
```

A decrypted output need not begin with a naked `CPK` or `PSMF` header. Treat a valid PGD MAC plus sane descriptor and block results as evidence for PGD-layer success only, then analyze the inner format separately. Do not treat random magic-looking hits inside high-entropy data as proof of the next container format.

## Validation checklist

- The PGD magic and header fields must parse cleanly before decryption.
- MAC `0x80` must pass for the EDAT-derived path.
- The decrypted descriptor must yield sane `data_size`, `block_size`, and `data_offset` values.
- Known explicit keys should be tried only after confirming path/key-table evidence.
- If EBOOT/BOOT is not plaintext ELF, do not rely on direct string search alone. Use emulator source behavior, PRX-aware analysis, and observed ioctl setup instead.
- GitHub translation projects such as PhotoKano-Kiss may help with text workflow and asset expectations, but do not assume a Vita/enhanced-edition project contains PSP archive keys.
- Record input and output hashes with every successful layer so later extraction steps can be reproduced exactly.
