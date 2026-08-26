# Videha Scholar article manifests

This directory is the controlled publication queue for the Scholar-facing layer.
Historical Videha HTML pages are automatically classified by `scholar-tools/build_research.py`, but a legacy multi-item issue page is never blindly published as one Scholar article.

Place one UTF-8 JSON file per validated scholarly article in `scholar-data/articles/`.

Required fields:

```json
{
  "title": "Maithili article title",
  "english_title": "English title where available",
  "authors": ["Author name"],
  "publication_date": "2026-08-15",
  "year": "2026",
  "issue": "448",
  "classification": "Original research paper",
  "language": "mai",
  "keywords": ["Mithila", "Maithili"],
  "abstract_html": "<p>Maithili / English abstract.</p>",
  "full_text_html": "<p>Complete article text...</p>",
  "references_html": "<ol><li>...</li></ol>",
  "source_url": "https://www.videha.co.in/original-issue-page.htm"
}
```

Optional: `slug`, `volume`. PDFs use the same slug and live beside the generated HTML under `research/YYYY/ISSUE/`.

## Classification policy

Highest priority: original research and explicit `शोध आलेख`; linguistics; literary criticism with references; history/cultural research; ethnography/folklore. Academic review essays and conference/seminar papers are conditional. Critical editions require a scholarly introduction. Editorials, ordinary book reviews, interviews, fiction, poetry, drama, announcements and quizzes are not Scholar priorities. Dictionaries/thesauri/WordNet and full scholarly books use separate discovery strategies.

The public canonical identity remains `https://www.videha.co.in/research/...`; GitHub is the heavy-data source of truth.
