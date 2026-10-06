"""Curate Issue 450 research articles from the supplied print-ready DOCX.

The issue has 51 prose TOC entries.  This deliberately promotes the two
documentary/literary-history studies (1.1, 1.2) and the 41 entries explicitly
marked ``शोध आलेख`` (1.11–1.51); creative prose, satire, reviews and poetry
remain in the general archive.
"""
from pathlib import Path
from docx import Document
import html, json, re

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(r"C:\Users\DELL\Documents\Github_VIDEHA_SADEHA_PDF_DOCX\VIDEHA_SADEHA_DOC_DOCX\VIDEHA_DOCX\Videha 444_450\Videha_450_2_PrintReady.docx")
OUT = ROOT / "scholar-data" / "articles"
DEV = "०१२३४५६७८९"
TRANS = str.maketrans(DEV, "0123456789")

def ascii_num(s):
    return int(str(s).translate(TRANS))

def slugify(s):
    s = re.sub(r"[^0-9A-Za-z\u0900-\u097F]+", "-", s).strip("-").lower()
    return s[:120] or "issue-450-research"

def main():
    paragraphs = [p.text.strip() for p in Document(SRC).paragraphs]
    heading_re = re.compile(r"^१\.(\d+)\.\s*(.*)$")
    headings = []
    for i, text in enumerate(paragraphs):
        m = heading_re.match(text)
        if m:
            headings.append((i, int(m.group(1)), m.group(2).strip()))
    # First occurrence is the TOC; the second is the article body heading.
    by_no = {}
    for i, no, text in headings:
        by_no.setdefault(no, []).append((i, text))
    selected = [1, 2] + list(range(11, 52))
    toc = {}
    for i, no, text in headings:
        if i >= 90 or no not in selected or no in toc:
            continue
        pm = re.search(r"([०-९0-9]+)\s*$", text)
        toc[no] = ascii_num(pm.group(1)) if pm else None
    ordered = [(i, no, text) for i, no, text in headings if no in selected and len(by_no[no]) >= 2 and (i, text) == by_no[no][1]]
    made = 0
    OUT.mkdir(parents=True, exist_ok=True)
    for pos, (start, no, label) in enumerate(ordered):
        end = next((i for i, n, _ in headings if i > start), len(paragraphs))
        block = [x for x in paragraphs[start:end] if x]
        m = re.match(r"^(.*?)\s*-\s*(.*)$", label)
        author = m.group(1).strip() if m else "गजेन्द्र ठाकुर"
        title = m.group(2).strip() if m else label
        title = re.sub(r"\s*-\s*शोध आलेख\s*$", "", title).strip()
        page_start = toc.get(no)
        next_pages = toc.get(no + 1)
        page_end = next_pages - 1 if page_start and next_pages else None
        rec = {
            "title": title,
            "authors": [author],
            "publication_date": "2026-09-15",
            "year": "2026",
            "issue": "450",
            "language": "mai",
            "keywords": ["Maithili literary history", "Mithila studies", "literary criticism", "research article"],
            "classification": "Maithili literary criticism; research article",
            "page_start": page_start,
            "page_end": page_end,
            "source_url": "https://archive.org/download/videha-2026/Videha%20450.pdf",
            "full_text_html": "".join(f"<p>{html.escape(x)}</p>" for x in block[1:]),
            "slug": slugify(title),
        }
        out = OUT / f"issue-450-{no:02d}-{rec['slug'][:80]}.json"
        out.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        made += 1
    print(f"created {made} Issue 450 curated manifests")

if __name__ == "__main__":
    main()
