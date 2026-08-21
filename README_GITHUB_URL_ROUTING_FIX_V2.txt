VIDEHA Search All — GitHub URL Routing Fix V2 (2026-08-21)

UPLOAD THE SAME CONTENTS TO BOTH:
1) videha-ejournal/videha repository root
2) Videha primary server httpdocs root
Merge folders and replace same-name files. Do not delete unrelated files.

Reason for V2:
Some embedded Search-All pages do not load videha-core.js, so the earlier renderer fallback could leave already-absolute malformed GitHub URLs unchanged.

V2 fixes URL routing independently at three layers:
- every embedded Search-All widget (167 HTML/HTM files)
- Quiz source adapter
- federated Sadeha/root/PDF source adapter

Canonical GitHub namespaces:
- https://videha-ejournal.github.io/videha-quiz/
- https://videha-ejournal.github.io/videha-sadeha/
- https://videha-ejournal.github.io/videha-ejournal/
- https://videha-ejournal.github.io/  (root user-site files)
- https://videha-ejournal.github.io/videha/search-documents/ (generated historical Videha/Sadeha search documents)

Example enforced mapping:
VIDEHA_001_440.htm from the videha-quiz Pagefind source always opens as:
https://videha-ejournal.github.io/videha-quiz/VIDEHA_001_440.htm
regardless of whether its raw Pagefind URL is relative, primary-host-prefixed, or accidentally nested under /videha/.
