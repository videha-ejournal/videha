from pathlib import Path
from docx import Document
from html import escape

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(r"C:\Users\DELL\Documents\Github_VIDEHA_SADEHA_PDF_DOCX\VIDEHA_SADEHA_DOC_DOCX\VIDEHA_DOCX\Videha 444_451")
OUT = ROOT / "search-documents" / "videha-451.html"

def main():
    paras = []
    for name in ("Videha_451_1.docx", "Videha_451_2.docx"):
        paras.extend(p.text.strip() for p in Document(SRC / name).paragraphs if p.text.strip())
    body = "\n".join(f"<p>{escape(p)}</p>" for p in paras)
    page = f'''<!doctype html><html lang="mai"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="citation_issn" content="2229-547X"><title>विदेह अंक ४५१ · Videha Issue 451</title><meta data-pagefind-meta="title" content="विदेह अंक ४५१ · Videha Issue 451"><meta data-pagefind-filter="publication[content]" content="VIDEHA"><meta data-pagefind-filter="issue[content]" content="451"><style>body{{max-width:78rem;margin:auto;padding:1.2rem;font:18px/1.65 Georgia,"Noto Serif Devanagari",serif;color:#241a14}}h1{{color:#7b241c}}a{{color:#7b241c}}p{{white-space:pre-wrap}}</style></head><body data-pagefind-body><main><h1>विदेह अंक ४५१ · Videha Issue 451</h1><p><a href="https://archive.org/download/videha-2026/Videha%20451.pdf">मूल PDF खोलू · Open original PDF</a></p>{body}</main></body></html>'''
    OUT.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT} from {len(paras)} paragraphs")

if __name__ == "__main__": main()
