# Videha document-search audit

Validated locally on 24 August 2026 against:

- Site repository: `C:\Users\DELL\Documents\github\videha`
- Source corpus: `C:\Users\DELL\Documents\Github_VIDEHA_SADEHA_PDF_DOCX`
- Machine-readable build record: `document-search-audit.json`

## Result

The GitHub-only document-search corpus is complete for the available canonical PDFs. It adds one searchable HTML page per logical PDF publication, keeps the existing site HTML searchable, and leaves the public search widget's local Pagefind, GitHub Pagefind, and compact JSON fallback order unchanged.

The current site metadata is detected dynamically. During validation the canonical site HTML identified issue 448 as current, while the available PDF/DOC corpus ended at issue 447. The generated archive therefore correctly ends at 447 without hardcoding the site's current issue.

## Corpus coverage and pairing

| Measure | Result |
| --- | ---: |
| Canonical PDFs | 485 |
| VIDEHA PDFs | 447 (issues 1–447, consecutive) |
| SADEHA PDFs | 38 (issues 1–37; issue 5 has Version 1 and Version 2) |
| Word source files | 714 (383 DOC + 331 DOCX) |
| Supplemental PDFs used as sources | 4 |
| Logical documents paired with native Word/source material | 447 |
| Paired SADEHA documents | 38 of 38 |
| Paired VIDEHA documents | 409 of 447 |
| PDF-only logical documents | 38, all VIDEHA |
| Unpaired source files | 0 |
| DOC conversion failures | 0 |

The PDF-only VIDEHA issues are 96, 232–267, and 308. PDF and Word counterparts are combined into one logical search page, so paired files do not create duplicate results.

## Generated HTML

| Measure | Result |
| --- | ---: |
| Generated pages | 485 |
| VIDEHA pages | 447 |
| SADEHA pages | 38 |
| Total generated size | 289,856,281 bytes (276.43 MiB) |
| Searchable text | 140,471,351 characters |
| Smallest/largest page text | 3,846 / 7,080,525 characters |
| Empty pages | 0 |
| Largest individual HTML file | 7,175,880 bytes (`videha-237.html`) |

Labels were checked explicitly. The only two versioned files are `SADEHA — 5, Version 1` and `SADEHA — 5, Version 2`; no SADEHA label uses “Volume”. `VIDEHA — Issue 447 / अंक ४४७` is derived from the source issue number. No public `TEXT NOT EXTRACTABLE`, `OCR NEEDED`, or equivalent placeholder is emitted.

## Native text and OCR coverage

| Measure | Result |
| --- | ---: |
| Native Word text read | 96,087,943 characters |
| PDF pages examined | 106,718 |
| Native PDF text read | 169,170,036 characters |
| Embedded images examined | 25,731 |
| Small/decorative embedded images skipped | 20,705 |
| Unique embedded-image OCR records | 3,936 |
| Embedded OCR records with text | 3,602 (91.5%) |
| Low-text/image-only PDF pages OCR-processed | 1,928 |
| PDF OCR records with text | 1,777 (92.2%) |
| Unique OCR characters added | 2,657,866 |
| Logical documents receiving OCR text | 396 of 485 |
| Mean OCR confidence | 48.76 |

OCR used Hindi/Devanagari plus English recognition. Native Word text remains preferred; PDF extraction and OCR supplement it for missing, image-only, advertisement/flyer, and handwritten material. The OCR cache is retained locally under the ignored `.search-cache` directory so subsequent refreshes do not repeat completed work.

## Pagefind and widget behavior

The production workflow still prepares all repository HTM/HTML and builds Pagefind 1.5.2. The tested staging build found 666 files and indexed 662 pages: all 485 generated archive pages plus 177 complete existing site pages. Four pre-existing non-document fragments have no outer `<html>` element and remain excluded by Pagefind: the Google verification fragment, two `photogallery/.../real_x.htm` fragments, and the reusable search embed snippet.

The staged Pagefind bundle contains 1,389 files and is 143,100,861 bytes (136.47 MiB). It indexed 1,002,882 words and seven filters. Filter counts verify exactly 447 VIDEHA and 38 SADEHA generated pages; the Version 1 and Version 2 filters each resolve to one page.

Live local tests passed:

- Publication + issue + version filters resolve only `SADEHA — 5, Version 2`.
- Publication + issue filters resolve only `VIDEHA — Issue 447 / अंक ४४७`.
- An existing-site query returns canonical pages such as `investigation.htm`.
- An OCR-only phrase returns the generated `VIDEHA — Issue 368 / अंक ३६८` page.

The widget was not rewritten. It still attempts `./pagefind/pagefind.js` first, then the GitHub Pages Pagefind URL. If Pagefind is unavailable or returns no scoped result, it retains the phonetic/cross-script JSON fallback. That fallback currently has 653 entries and is 2,623,982 bytes (2.50 MiB). Archive.org PDF lookup remains available through the existing `VidehaAndSadeha` catalog.

Generated `search-documents/` pages and rebuilt `pagefind/` assets are intended for GitHub Pages only. The canonical hand-authored HTM/HTML remains the single set shared with Rediff/Videha, whose deployment stays light and continues to use the small local fallback plus GitHub Pagefind when available.

## Remaining limitations

- The PDF/DOC corpus is one issue behind the current site metadata (447 versus 448). A future corpus refresh will add issue 448 automatically when its canonical PDF/source files are present.
- OCR makes image and handwritten material discoverable, but the mean confidence is modest; exact quotations from OCR text should be checked against the source scan.
- Pagefind reports that Maithili (`mai`) has no stemming support. Exact tokens and the widget's existing cross-script/phonetic expansion work, but inflected-root matching is not stemmed.
- The four HTML-less fragments noted above are not content pages and are not indexed. All complete existing HTML pages remain indexed.
