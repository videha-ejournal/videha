VIDEHA Search All — GitHub URL routing correction — 2026-08-21

Upload/merge this SAME package into:
1) videha-ejournal/videha repository root
2) Videha server httpdocs root
Replace same-name files; do not delete other files.

Corrected invariant:
- https://videha-ejournal.github.io/videha-quiz/... stays on /videha-quiz/ on BOTH hosts.
- https://videha-ejournal.github.io/videha-sadeha/... stays on /videha-sadeha/ on BOTH hosts.
- https://videha-ejournal.github.io/videha-ejournal/... stays on /videha-ejournal/ on BOTH hosts.
- https://videha-ejournal.github.io/<root-file> stays at the GitHub user-site root.
- https://videha-ejournal.github.io/videha/search-documents/... stays on GitHub historical archive.
- Only genuinely relative ordinary mirrored Videha pages remain host-aware.

The resolver also repairs already-malformed paths such as:
- https://videha-ejournal.github.io/videha/videha-quiz/X -> https://videha-ejournal.github.io/videha-quiz/X
- https://www.videha.co.in/videha-quiz/X -> https://videha-ejournal.github.io/videha-quiz/X
