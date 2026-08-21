VIDEHA SEARCH ALL — COMMON FILES FOR BOTH MAIN HOSTS
Apply this folder to BOTH:
  1) videha-ejournal/videha GitHub repository root
  2) Videha server httpdocs
Merge folders, replace same-name files, do NOT delete destination-only files.

Filter/source map:
- All: main Videha + historical archive facets + dual Quiz + Book/Audio/Panji/Thesaurus summaries + ordinary Sadeha + ordinary root user-site + GitHub PDF catalogue.
- Author / Title / Issue / Year / Prose / Poetry / Research: main indexed Videha plus the applicable historical archive facets.
- Book: complete pothi.htm listing.
- Audio/Video: complete Audio_Video.htm listing.
- Panji: videha-sadeha/panji-shards JSON backend.
- Thesaurus / Dictionary: root data/manifest.json/chunks PLUS lexical/dictionary quiz matches from BOTH Quiz Pagefind repositories. Non-dictionary quizzes are rejected from this filter.
- Quiz: both videha-quiz/pagefind/ and root pagefind-quiz/.
- Archive: archive.org catalogue + GitHub videha-ejournal PDF catalogue.

The lexical quiz extension is client-side and reuses the two existing Quiz Pagefind indexes; it does not create another large server-side index.
