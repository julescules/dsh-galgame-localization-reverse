# PSP GSC2-style fixed-slot localization

Use this route only after proving the structure on multiple real offsets. `GSC2` is not a universal public format contract; different titles may use different containers or script layouts.

## Prove text ownership

For a candidate string at offset `S`, inspect bytes before and after it. A common verified pattern is:

```text
[u32 little-endian byte length][CP932 bytes][00]
```

The length normally excludes the NUL. Confirm it on long dialogue, short reactions, choices, names, control-tagged lines, aligned and unaligned offsets. Do not infer the format from one string.

## Completeness audit

Legacy extractors often impose a minimum length and silently omit short reactions, choices, names, sound effects, or single-kanji labels. Build the source master from the proven binary structure, then compare by `(relative file path, byte offset, exact source)` against any previous plan.

A robust scanner should require:

- plausible length bounds;
- exact NUL termination;
- strict CP932 decode and byte-identical encode round trip;
- no unexpected controls or private-use characters;
- overlapping prefix search so adjacent zero bytes do not hide candidates;
- resource-blob filters for repeated decoded ideographs, halfwidth noise, and pixel-like payloads.

Keep three result classes: known exact match, new candidate, and known-source mismatch. Review plan-only rows separately; never merge them automatically. Freeze a source-only TSV plus a JSON report and hashes.

## Translation ledger

Do not trust a non-empty legacy `translation` column. Inherit only explicitly reviewed records. Keep:

- a row master keyed by file and offset;
- a unique-source view for translation memory;
- immutable source text and source byte length;
- independent reviewed patch ledgers with reviewer, date, scope, notes, and authorized replacements.
- a machine-readable terminology table plus a human-readable terminology note for names, nicknames, honorific variants, titles, place names, item names, food/menu terms, and recurring jokes.

Treat the machine-readable terminology table as the QA authority: keep `source_form` unique, trim fields, and scan only translation fields for banned translated terms. On Windows, if PowerShell display or search results look garbled, re-check terms and duplicates through an explicit UTF-8 path such as Python or Unicode-escaped search patterns before adding new entries.

Exact-source reuse is a suggestion, not automatic approval. Short Japanese reactions such as `え`, `はぁ`, and `そう` are context-sensitive. Before scoped reuse, inspect adjacent dialogue, restrict file IDs, and assert the expected occurrence count.

When a literal title sounds unnatural in the target language, verify the original context and record the semantic rendering in the terminology notes. Do not propagate a bad literal nickname just because it appears mechanically consistent.

## Fixed-slot QA

Before binary writeback, enforce:

- exact placeholder/control-tag sequence;
- unchanged newline count where layout is fixed;
- encoded translation length not exceeding the original CP932 slot;
- strict encoding with no truncation, quote stripping, or replacement characters;
- only declared text-slot bytes changed and total file size unchanged.

When Simplified Chinese is rendered through remapped CP932 slots, a conservative preflight is ASCII = 1 byte and every other character = 2 bytes. The final authority is the actual slot encoder output.

For placeholder plus honorific patterns such as `\p01君`, prefer a glossary rule that preserves the placeholder and gives a normal rendering, for example `\p01同学`. If the fixed slot cannot fit the honorific, shorten the surrounding title text (for example to `\p01`) only after recording the exception in the terminology notes; never move, split, translate, or delete the placeholder itself.

## Runtime font mapping

Do not assume character-table row order equals the runtime glyph cell. If the renderer indexes Shift-JIS/CP932 space mathematically, derive cells from the encoded byte ordinal and prove page boundaries with runtime probes. Protect all source characters and already-used direct display cells before allocating replacement glyph slots. Treat duplicate or ambiguous CP932 byte entries as unsafe until probed.

## Container and ISO rebuild

Rebuild from a clean original DATA/container on every candidate. Verify decompressed target equality, physical allocation limits, untouched table entries, and zero changes outside declared ranges. Patch the ISO only with an equal-length extent replacement, record hashes and a manifest, and keep rollback data.

Static success is not runtime acceptance. Test dialogue, short reactions, choices, control tags, line wrapping, auto/skip, font color/alpha, newly allocated glyphs, and previously passing scenes.

## Parallel translation discipline

Use subagents or external translators only when the user explicitly authorizes that workflow. Treat their output as draft text, not reviewed localization. The main agent must re-open the source context, check terminology, repair fixed-slot length failures, preserve controls/newlines, apply all patch ledgers from the clean base, and update the handoff notes only after full QA passes.

For long scripts, split work by explicit, non-overlapping file IDs, offsets, or 1-based batch entry ranges. In practice, 40-entry chunks are more reliable than assigning a whole 90-150+ entry script to one worker. Each worker should write a uniquely named patch ledger and must not touch the master TSV, terminology, docs, binary assets, or ISO. If an unassigned patch appears, treat it as a draft: rename or isolate it to avoid numbering conflicts, then verify coverage, controls, newlines, fixed-slot length, and terminology before including it. Before final apply, the main agent should verify expected vs seen entries, missing/extra/duplicate offsets, control-tag counts, and newline counts. On Windows/PowerShell, write banned-term or terminology QA checks with Unicode escapes when console code pages may corrupt Chinese/Japanese literals.

Structural QA is not enough for parallel drafts. The main agent should run a terminology drift pass for names, nicknames, honorifics, places, items, and recurring jokes before generating the official patch. If a worker uses a plausible but non-glossary rendering, keep the draft for traceability and apply a main-agent override ledger rather than silently editing the source context.

For mirrored scripts, require full source-sequence equality, not just similar counts or similar dialogue. Generate the mirror only from the reviewed primary script, keep per-file offsets from the target batch, and record the mirror relationship in the reviewed draft or patch notes.

If two scripts are mostly but not completely identical, do not mark the target as a mirror. Build a `source -> reviewed translation` map only from the already reviewed primary script, assert that each reused source has exactly one reviewed translation, and translate every target-only, near-match, shortened, or stutter-variant source independently.

When a worker stalls, first check whether its patch file already exists. If the assigned patch is missing and the main agent must take over, interrupt that worker before writing the same patch name. If another script looks like a mirror of an already reviewed script, reuse only entries whose source text matches exactly; near-matches or shortened variants must be translated and checked independently. After every accepted batch, add new names, nicknames, food terms, place names, item names, and recurring joke renderings to both the machine-readable terminology table and the human-readable notes.
