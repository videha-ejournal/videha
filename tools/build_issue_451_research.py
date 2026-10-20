from pathlib import Path
from docx import Document
from html import escape
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(r"C:\Users\DELL\Documents\Github_VIDEHA_SADEHA_PDF_DOCX\VIDEHA_SADEHA_DOC_DOCX\VIDEHA_DOCX\Videha 444_451\Videha_451_2.docx")
OUT = ROOT / "research" / "2026" / "451"
SECTIONS = [
    (951, 2053, "गजेन्द्र ठाकुर — नित नवल वृषेश चन्द्र लाल", "gajendra-thakur-nit-naval-vrishesh-chandra-lal"),
    (2053, 2862, "गजेन्द्र ठाकुर — नित नवल कमला चौधरी", "gajendra-thakur-nit-naval-kamla-chaudhary"),
    (2862, 3125, "गजेन्द्र ठाकुर — नित नवल ललिता झा", "gajendra-thakur-nit-naval-lalita-jha"),
    (3125, 4289, "गजेन्द्र ठाकुर — नित नवल वीरेन्द्र मल्लिक", "gajendra-thakur-nit-naval-virendra-mallick"),
    (4289, 6174, "गजेन्द्र ठाकुर — नित नवल योगानन्द झा", "gajendra-thakur-nit-naval-yoganand-jha"),
    (6174, 6858, "गजेन्द्र ठाकुर — नित नवल कुणाल", "gajendra-thakur-nit-naval-kunal"),
]

def main():
    paras = Document(SRC).paragraphs
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for start, end, title, slug in SECTIONS:
        items = [p.text.strip() for p in paras[start:end] if p.text.strip()]
        # Preserve long research installments as separate, navigable pages.
        chunks = [items[i:i+350] for i in range(0, len(items), 350)]
        for n, chunk in enumerate(chunks, 1):
            suffix = f"-{n}" if len(chunks) > 1 else ""
            name = f"{slug}{suffix}.htm"
            body = "\n".join(f"<p>{escape(x)}</p>" for x in chunk)
            page = f'''<!doctype html><html lang="mai"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="citation_title" content="{escape(title)}"><meta name="citation_author" content="Gajendra Thakur"><meta name="citation_journal_title" content="Videha"><meta name="citation_issn" content="2229-547X"><meta name="citation_issue" content="451"><title>{escape(title)} · अंक ४५१</title><link rel="stylesheet" href="../../../assets/css/videha-research.css"></head><body data-pagefind-body><main><p><a href="../../index.htm">विदेह शोध-सूची</a> · <a href="https://archive.org/download/videha-2026/Videha%20451.pdf">मूल PDF</a></p><h1>{escape(title)}</h1><p><strong>Videha Issue 451 · Research article continuation {n}</strong></p>{body}</main></body></html>'''
            (OUT / name).write_text(page, encoding="utf-8")
            written.append(name)
    print(f"Wrote {len(written)} Issue 451 research pages")

if __name__ == "__main__":
    main()
