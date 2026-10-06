from pathlib import Path
from docx import Document
from html import escape

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(r"C:\Users\DELL\Documents\Github_VIDEHA_SADEHA_PDF_DOCX\VIDEHA_SADEHA_DOC_DOCX\VIDEHA_DOCX\Videha 444_450")
OUT = ROOT / "search-documents" / "videha-450.html"

def main():
    paras = []
    for name in ("Videha_450_1_PrintReady.docx", "Videha_450_2_PrintReady.docx"):
        paras.extend(p.text.strip() for p in Document(SRC / name).paragraphs if p.text.strip())
    body = "\n".join(f"<p>{escape(p)}</p>" for p in paras)
    page = f'''<!doctype html><html lang="mai"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>विदेह अंक ४५० · Videha Issue 450</title><meta data-pagefind-meta="title" content="विदेह अंक ४५० · Videha Issue 450"><meta data-pagefind-filter="publication[content]" content="VIDEHA"><meta data-pagefind-filter="issue[content]" content="450"><style>body{{max-width:78rem;margin:auto;padding:1.2rem;font:18px/1.65 Georgia,"Noto Serif Devanagari",serif;color:#241a14}}header{{border-bottom:2px solid #8a2f21;margin-bottom:1.5rem}}h1{{color:#7b241c}}.source{{background:#f7efe5;padding:.9rem;border-radius:.4rem}}a{{color:#7b241c}}p{{white-space:pre-wrap}}</style></head><body data-pagefind-body><header><h1>विदेह अंक ४५० · Videha Issue 450</h1><p class="source"><strong>Publication:</strong> VIDEHA · <strong>Issue:</strong> 450 · 15 सितम्बर 2026<br><a href="https://archive.org/download/videha-2026/Videha%20450.pdf">मूल PDF खोलू · Open original PDF at Internet Archive</a></p></header><main>{body}</main></body></html>'''
    OUT.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT} from {len(paras)} paragraphs")

if __name__ == "__main__":
    main()
