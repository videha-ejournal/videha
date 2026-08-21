VIDEHA — GLOBAL GITHUB LINK GUARD FIX
Date: 2026-08-21

UPLOAD THE SAME CONTENTS TO BOTH:
1. videha-ejournal/videha repository root
2. Videha primary server httpdocs root

This fix is deliberately independent of Search-All/Pagefind routing.
It normalizes every anchor on the page, including anchors inserted later by JavaScript.

Forced GitHub namespaces:
- videha-quiz      -> https://videha-ejournal.github.io/videha-quiz/
- videha-sadeha    -> https://videha-ejournal.github.io/videha-sadeha/
- videha-ejournal  -> https://videha-ejournal.github.io/videha-ejournal/
- search-documents -> https://videha-ejournal.github.io/videha/search-documents/

The guard runs:
- on initial DOM content
- on dynamically inserted/changed anchors via MutationObserver
- immediately before pointer/click/aux-click/context-menu navigation

HTML pages patched: 165
Verification files intentionally not altered: google7d0b1633a9939d34.html, pinterest-40f05.html

Exact test:
https://www.videha.co.in/videha-quiz/VIDEHA_001_440.htm
and
https://videha-ejournal.github.io/videha/videha-quiz/VIDEHA_001_440.htm
both normalize to:
https://videha-ejournal.github.io/videha-quiz/VIDEHA_001_440.htm
