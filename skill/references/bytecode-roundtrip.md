# Bytecode Round-Trip Reference

Read this file when implementing or reviewing script bytecode tooling for a galgame/visual novel VM: `vm_analysis.md`, `opcode.py`, `disassembler.py`, `assembler.py`, semantic `asm.txt`, and zero-mutation rebuild validation.

## Deliverables

For a custom script VM, produce:

- `vm_analysis.md`: VM and instruction-set analysis document.
- `opcode.py`: opcode and operand schema definitions.
- `disassembler.py`: binary script to semantic `asm.txt`.
- `assembler.py`: `asm.txt` to binary script.
- `asm.txt`: example semantic disassembly output.

The design target is exact byte-for-byte reconstruction after disassemble then assemble.

## Pre-disassembly VM analysis

Do not begin tool implementation from a few visible strings. First build `vm_analysis.md` as the single source of truth.

Required sections:

- VM architecture: stack/register style, address space, execution model.
- Instruction decoding flow: opcode boundaries, fixed/variable lengths, endianness, alignment.
- Opcode length/format table.
- Operand schemas: `imm8`, `imm16`, `imm32`, `rel_offset`, `abs_addr`, `reg`, `strref`, `sub_opcode`, variable-length blobs.
- Sub-opcode definitions and all legal subcodes.
- Variants where one opcode has different operand formats or semantics.
- Jump/call/return semantics and offset base: instruction start, instruction end, or VM PC.
- String/data block formats and pointer tables.
- Compression/encryption/container transforms required by the target format.
- Unknown-opcode correction log.

If an opcode is not defined, first check whether the previous instruction length was wrong. Many false opcodes are operands created by boundary drift.

## Opcode schema

`opcode.py` must be importable by both tools. Keep the schema structured, not string-parsed.

Example shape:

```python
OPCODES = {
    0x01: {
        "mnemonic": "LOAD",
        "length": 3,
        "operands": [
            {"type": "reg", "bits": 4},
            {"type": "imm16", "endian": "little"},
        ],
        "sub_opcodes": {},
    },
    0x10: {
        "mnemonic": "CALL",
        "length": 5,
        "operands": [
            {"type": "sub_opcode", "bits": 8},
            {"type": "rel_offset", "bits": 32, "base": "instruction_end"},
        ],
        "sub_opcodes": {
            0x00: "PRINT_TEXT",
            0x01: "PLAY_SOUND",
            0x02: "SET_FLAG",
        },
    },
}
```

For variable-length instructions, make the length rule explicit as a function or declarative rule that the disassembler and assembler both use.

## Disassembler requirements

CLI:

```bash
python disassembler.py <input_script> [-o <output_asm>] [--encoding <codec>]
```

Drag/drop behavior on Windows:

- Dropping a binary script onto `disassembler.py` should use that path as input.
- If `-o` is not provided, write `<input_basename>.asm.txt` next to the input file.

Behavior:

- Parse from file start to end without unaccounted byte gaps.
- Use `opcode.py` as the only opcode truth source.
- Stop on unknown opcode and report the exact offset.
- Handle variable-length opcodes and sub-opcodes through the schema.
- Emit labels for all jump/call targets.
- Render non-instruction data blocks through pseudo-instructions, not invisible bytes.
- Put the selected encoding in the `asm.txt` header comment.

Do not use regex to scrape text directly from binary files. All text extraction must come from the decoded structure.

## Semantic asm format

`asm.txt` is a semantic text view, not a hex dump.

Rules:

- One record per line.
- Labels are `label_name:` with no indentation.
- Insert a blank line before every label except the first label if desired.
- Instructions may be indented for readability.
- Use `;` comments only for semantic notes.
- Never place raw hex-dump comments like `; 00 01 FF`.
- Never use `\xNN` escapes in strings.
- Use `{{XX}}` or `{{XX:YY}}` placeholders for exact raw bytes inside strings.
- Use `.byte`, `.word`, etc. for data definitions where numeric data is semantically appropriate.

Example:

```text
; script entry, encoding: shift_jis

loc_00000000:
    LOAD    R1, 0x1234
    CALL.PRINT_TEXT    loc_00001000

loc_00001000:
    .string "こんにちは{{00}}ワールド"   ; zero-terminated string

loc_00001010:
    .byte 0x01, 0x02
```

## Encoding and placeholders

The disassembler uses `--encoding` to decode string bytes. If bytes cannot be decoded or should not be emitted as printable text, emit placeholders.

The assembler parses placeholders before encoding boundaries:

- `{{00}}` means byte `0x00`.
- `{{FF:01}}` means bytes `0xFF 0x01`.
- Placeholder parsing must not introduce extra characters.
- Invalid placeholders must produce a hard error.

Candidate encodings:

- `utf-8`
- `utf-8-sig`
- `cp932`
- `shift_jis`
- `gbk`

If no encoding is provided, choose an explicit default and record it in the output header. Do not rely on platform defaults.

## Assembler requirements

CLI:

```bash
python assembler.py <input_asm.txt> [-o <output_bin>] [--encoding <codec>]
```

Drag/drop behavior on Windows:

- Dropping `asm.txt` onto `assembler.py` should use that path as input.
- If `-o` is not provided, write `<input_basename>.rebuild` next to the asm file.

Behavior:

- Parse labels, instructions, pseudo-instructions, data definitions, comments, and blank lines.
- Encode instructions from `opcode.py`, including sub-opcodes and variants.
- Resolve labels in at least two passes.
- Compute jump offsets with the exact base defined in `vm_analysis.md`.
- Encode strings with the selected encoding, splicing placeholder bytes directly.
- Reconstruct all data blocks, padding, pointers, and tables.
- Stop with clear errors for invalid instructions, operand overflow, unresolved labels, or invalid placeholders.

## Compression/encryption/container layers

If the target script has a compression, encryption, or container layer:

- Document the transform in `vm_analysis.md`.
- Make disassembly present the decoded clean byte-stream view.
- Make assembly reapply the transform if exact original container reconstruction is required.
- Include transform parameters in logs and tests.

If the layer implements rights control or license enforcement, document its detection points, state transitions, key or token inputs, transform boundaries, and exact round-trip behavior. Keep the implementation isolated from localization payloads and require hash-bound tests plus rollback evidence.

## Zero-mutation validation

Run:

```bash
python disassembler.py sample.sc -o sample.asm.txt --encoding shift_jis
python assembler.py sample.asm.txt -o sample.rebuild.sc --encoding shift_jis
```

Then compare:

```bash
cmp sample.sc sample.rebuild.sc
sha256sum sample.sc sample.rebuild.sc
```

On Windows without GNU tools, compare bytes and hashes with PowerShell:

```powershell
if (-not ((Get-FileHash sample.sc -Algorithm SHA256).Hash -eq (Get-FileHash sample.rebuild.sc -Algorithm SHA256).Hash)) {
    throw "round-trip hash mismatch"
}
```

A passing tool has no byte differences. If validation fails, fix in this order:

1. Instruction boundary or variable-length rule.
2. Sub-opcode/variant routing.
3. Jump offset base or label relocation.
4. String terminator or placeholder handling.
5. Data block, padding, pointer table, or alignment reconstruction.
6. Compression/encryption/container transform.

## Test checklist

Add focused tests when implementing:

- Unknown opcode reports exact offset.
- Variable-length instruction is split correctly.
- Sub-opcode emits the right mnemonic and round-trips.
- Jump target label relocates when string length changes.
- `{{00}}` and `{{FF:01}}` produce exact bytes.
- `\xNN` is not emitted in `asm.txt`.
- Comments cannot smuggle raw hex dumps if the format checker enforces that rule.
- Encoding metadata is read from CLI or asm header.
- Drag/drop path behavior works with `sys.argv`.
- Original and rebuilt sample hashes match.
