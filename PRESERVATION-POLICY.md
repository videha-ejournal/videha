# Videha Digital Research Preservation Policy

**Videha — First Maithili Fortnightly eJournal · ISSN 2229-547X**

Videha research outputs should remain independently citable, recoverable and auditable even when working branches or interfaces change.

## Release model

For each major dataset, corpus or scholarly archive release, preserve as many of the following as are applicable:

1. a source-control commit or signed/referenced tag;
2. a GitHub Release or immutable release asset set;
3. a manifest recording record counts, source provenance, software/runtime versions and claim boundaries;
4. `SHA256SUMS` or equivalent cryptographic checksums for released files;
5. a human-readable release note describing scope and known limitations;
6. an independent preservation copy when legally and technically possible, such as Archive.org;
7. persistent citation metadata (CFF/BibTeX/RIS/JSON-LD) and ISBN/ISSN identifiers where applicable.

## Source and derivative separation

Original/source-controlled files must not be overwritten by OCR, ASR, translation, normalized metadata or other derivatives. Derived outputs should identify their source and transformation status.

## Machine-derived corpora

Machine ASR/OCR completion means computational coverage, not publisher verification. Preservation manifests must retain fields such as `humanVerified`, `editorialReview`, model/runtime identity and any known no-speech or unresolved cases.

## ISBN and publication identity

Authoritative ISBN values are publication identifiers and must remain attached to the correct work/edition. ISSN 2229-547X identifies Videha and should accompany archive-level citation metadata.

## Recommended long-term enhancements

- Create versioned release tags for major research datasets.
- Deposit stable release packages in an independent repository when possible.
- For manuscript/facsimile collections, publish IIIF Presentation manifests where image rights permit.
- For datasets intended for formal academic citation, register a DOI through a suitable repository or DataCite-integrated service. DOI registration requires an external authorized account and is not to be simulated in metadata.

## Recovery principle

A release is considered preservation-ready only when its public representation can be reconstructed from source-controlled data plus documented build/transformation steps, without relying on undocumented local state.
