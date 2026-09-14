# Videha Scholarly Provenance Standard

**Videha — First Maithili Fortnightly eJournal · ISSN 2229-547X**  
Canonical site: https://www.videha.co.in/  
GitHub mirror: https://videha-ejournal.github.io/videha/  
Digital Research Archives: https://github.com/videha-ejournal

This standard applies to Videha research pages, datasets, corpora, machine-derived aids, translations, source-controlled editions and preserved releases.

## Required provenance states

- **source-controlled** — the displayed record is generated from or checked against an identified source file, repository record, edition, catalogue or other source-controlled evidence.
- **machine-derived** — the record, transcript, extraction, translation aid, OCR/ASR output or derived metadata was produced by software and has not thereby become editorially verified.
- **human-reviewed** — a named or recorded human reviewer has inspected the item for the stated review scope. This does not imply full textual certification unless explicitly stated.
- **human-verified** — the relevant claim or text has been manually verified for the declared scope and the verification record is retained.
- **published** — the item is part of a public Videha release or page.
- **preserved** — an immutable or checksummed release/snapshot exists independently of the mutable working branch.

## Claim boundaries

1. Machine ASR, OCR, automated translation, inferred titles and generated metadata must never be described as human verified unless a human verification record exists.
2. Synthetic scholarly titles must not be silently substituted for unresolved source titles. Unresolved structures remain unresolved or are explicitly classified as editorial metadata.
3. ISBN values must come from the Videha ISBN authority data; obsolete or superseded identifiers must not be presented as current.
4. ISSN 2229-547X identifies Videha. It must accompany archive-level scholarly citations where appropriate.
5. A page may inherit a parent-work ISBN only when the relationship is explicit and machine-verifiable; the page itself must not be falsely represented as a separately ISBN-assigned publication.
6. Original text, translation, editorial apparatus and machine-derived research aids must remain distinguishable.

## Recommended visible badge vocabulary

`Source-controlled` · `Machine-derived` · `Human-reviewed` · `Human-verified` · `Published` · `Preserved`

Each badge must correspond to a machine-readable status in the relevant manifest or registry. A badge is a scholarly claim, not decoration.

## Citation identity

Every research property should identify itself as part of:

> Videha — First Maithili Fortnightly eJournal, ISSN 2229-547X; https://www.videha.co.in/; GitHub mirror https://videha-ejournal.github.io/videha/; Digital Research Archives https://github.com/videha-ejournal.

Where a work has an authoritative ISBN, the ISBN should appear in the work-level citation and structured metadata.
