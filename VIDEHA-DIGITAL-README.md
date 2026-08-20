# VIDEHA Digital Archive & Editorial Studio — integrated 15-module build

Generated: 20 August 2026

## Search host rule (preserved and made explicit)
1. Ordinary/current/static Videha result opens on the host where the search is being used.
   - on www.videha.co.in -> https://www.videha.co.in/<same-path>
   - on GitHub Pages -> https://videha-ejournal.github.io/videha/<same-path>
2. Generated historical `search-documents/...` results always open on GitHub from either host.
3. If the low-cost Videha server has no local `pagefind/`, search automatically imports the GitHub Pagefind bundle.

## Integrated modules / layers
1. Existing Videha preservation layer — existing HTML/HTM, URLs and tools retained.
2. `videha-digital-archive.html` — Digital Archive home/dashboard.
3. Existing Universal Search upgraded with central host-aware result resolver on all search-enabled root pages.
4. `videha-archive-explorer.html` — Videha/Sadeha historical explorer.
5. `videha-chatbot.html` — Ask Videha source-grounded conversational search.
6. Chatbot dual mode — always-working extractive/search mode + optional generative PHP bridge with automatic fallback.
7. `videha-editor-studio.html` — existing robust Site Auditor integrated as Editorial Studio.
8. `videha-publisher.html` — site ZIP audit, issue continuity check, SERVER/GITHUB package split and deployment checklist.
9. `videha-language-studio.html` — parallel multilingual editor, paragraph alignment, permanent rules, CSV/HTML export; existing translator/converter integrated.
10. `videha-document-studio.html` — DOCX/HTML/TXT local audit; headings/chapters, tables, images, notes, superscripts, duplicates, missing sections, untranslated checks, reorder, DOCX/HTML/TXT and 6×9 Print/PDF workflow.
11. `videha-knowledge-graph.html` — static author/name → issue/file relationships generated from numbered TOC metadata.
12. Shared technical framework — `assets/js/videha-core.js`, generated JSON manifests, GitHub build hook.
13. Accessibility — skip links, keyboard-native controls, semantic labels, responsive/reflow layout, reduced-motion compatibility; existing Listen/Stop and accessibility work preserved.
14. Low-data mode — opt-in UI flag; no archive prefetch and heavy search corpus remains GitHub-hosted.
15. Dual deployment/build system — lightweight `VIDEHA_SERVER` and full `VIDEHA_GITHUB`, with GitHub Action metadata/Pagefind refresh.

## Current corpus state detected
- Current web issue: 448
- Historical generated Videha search documents: through issue 447
- Sadeha searchable documents: 38 (Sadeha 5 Version 1 and Version 2 are separate documents)

## Optional generative Ask Videha
`api/ask-videha.php` works in source-grounded fallback mode without a paid AI configuration. For a generative endpoint, copy `api/videha-ai-config.example.php` to `api/videha-ai-config.php` on the PHP server and fill a compatible endpoint/key/model. Do not put the API key in GitHub or browser JavaScript.

## Long Document Studio note
The merged DOCX export is intentionally text-safe: it preserves/reorders paragraph text and can create 6×9 page geometry, but does not pretend to losslessly combine incompatible images, Word fields or complex footnote formatting from multiple source DOCX files. Those elements are inventoried in the audit so editorial decisions remain explicit.
