# Videha/Sadeha document search corpus

`build-document-search.py` creates the GitHub-only `search-documents/` pages
from the local PDF and Word archive. The PDF filenames define the 485 logical
documents: Videha 1 through the latest consecutive issue, plus Sadeha 1–37
with only Sadeha 5 having Version 1 and Version 2.

Matching DOC/DOCX components are combined with their PDF and emitted once.
Native Word text is preferred. Embedded images and PDF pages with little native
text are OCRed when Tesseract with Hindi and English models is available. Cache
data is local and ignored by Git; the generated HTML and audit JSON are committed.

Example (PowerShell):

```powershell
python tools/build-document-search.py `
  C:\Users\DELL\Documents\Github_VIDEHA_SADEHA_PDF_DOCX `
  --tesseract "C:\Program Files\Tesseract-OCR\tesseract.exe" `
  --tessdata C:\path\to\tessdata
```

The existing Pagefind preparation workflow includes both `.htm` and `.html`, so
all canonical site pages remain searchable and `search-documents/` is added to
the same index. Do not upload `search-documents/` or `pagefind/` to Rediff; the
canonical site pages and lightweight `videha-search-index.json` remain the
Rediff upload set.
