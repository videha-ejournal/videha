# Videha Google Scholar / Research Index deployment

## Architecture

- Heavy source, retrospective classification output, article HTML and PDFs: GitHub repository `videha-ejournal/videha`.
- Public bibliographic identity: `https://www.videha.co.in/research/`.
- Plesk/Videha server: lightweight PHP gateway only; it fetches the generated GitHub corpus and caches resources for 15 minutes.
- Existing Videha pages and navigation are not replaced or removed.

## 1. Build on GitHub

The workflow `.github/workflows/build-scholar.yml` runs `scholar-tools/build_research.py` and then `scholar-tools/validate_scholar.py`.

The retrospective scan identifies likely scholarly legacy pages and stores them in `research/data/articles.json` as `candidates`. It deliberately does not turn a multi-item historical issue page into a fake single article. Validated article-level records are supplied as one JSON manifest per paper under `scholar-data/articles/` and are generated as individual Scholar HTML pages.

## 2. Plesk deployment

Copy only the contents of:

`server-integration/research/`

to:

`httpdocs/research/`

The directory needs PHP and Apache rewrite support. Allow PHP to create `httpdocs/research/cache/`; no historical corpus needs to be uploaded to Plesk.

Public URLs then remain stable Videha URLs, for example:

- `https://www.videha.co.in/research/`
- `https://www.videha.co.in/research/2026/448/article-slug.htm`
- `https://www.videha.co.in/research/2026/448/article-slug.pdf`
- `https://www.videha.co.in/research/sitemap.xml`

## 3. Sitemap and robots

After the gateway is live, add this sitemap to the main sitemap index or robots file:

`Sitemap: https://www.videha.co.in/research/sitemap.xml`

Do not block `/research/` in robots.txt.

## 4. Metadata contract

Every generated research article has a canonical Videha URL and these Google-Scholar-compatible tags when applicable:

- `citation_title`
- one or more `citation_author`
- `citation_publication_date`
- `citation_journal_title`
- `citation_issn`
- `citation_volume` when available
- `citation_issue`
- `citation_pdf_url` when an individual PDF exists

It also carries `ScholarlyArticle` JSON-LD, visible journal/ISSN information, abstract, keywords, complete article text, references, a suggested citation, and a link to the original Videha issue.

## 5. Adding a new शोध आलेख

1. Preserve the normal Videha issue publication unchanged.
2. Create one manifest under `scholar-data/articles/` using `scholar-data/README.md`.
3. Commit it to `main`.
4. The workflow generates the canonical `/research/YYYY/ISSUE/slug.htm` page and updates `research/data/articles.json` and `research/sitemap.xml`.
5. If an individual PDF is supplied at the matching generated path, the article receives `citation_pdf_url` automatically.

## 6. Retrospective policy

Priority: explicit शोध/शोध आलेख/अनुसन्धान/अन्वेषण; linguistics and grammar; history/cultural research; ethnography/folklore; पञ्जी; Mithila painting; substantial referenced criticism. Secondary material is held for review. Poetry, stories, drama, routine editorial/news, interviews and e-learning/quiz material are not Scholar article targets. Dictionaries/thesauri/WordNet and full books use separate discovery strategies.

Google Scholar inclusion itself is controlled by Google; this layer makes Videha bibliographically and technically legible but does not guarantee indexing.
