"""Repair generated pages whose article wrapper contains a TOC/preamble."""
from pathlib import Path
import html, re, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scholar-tools"))
from extract_explicit_research import SourceParser, parse_toc_entries, article_body, body_to_html

ROOT = Path(__file__).resolve().parents[1]
def norm(s): return re.sub(r"\s+", "", html.unescape(s or "")).lower()

def repair_pages(root=ROOT):
    repaired = 0
    for page in root.joinpath("research").glob("20??/*/*.htm"):
        m = re.search(r"research/(?:\d{4})/(\d+)/", page.as_posix())
        if not m: continue
        issue = int(m.group(1)); src = root / "search-documents" / f"videha-{issue:03d}.html"
        if not src.exists(): src = root / "search-documents" / f"videha-{issue}.html"
        if not src.exists(): continue
        s = page.read_text(encoding="utf-8", errors="ignore")
        hm = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
        if not hm: continue
        title = re.sub(r"<[^>]+>", " ", html.unescape(hm.group(1)))
        p = SourceParser(); p.feed(src.read_text(encoding="utf-8", errors="ignore")); text = p.text()
        toc, _ = parse_toc_entries(text)
        matches = [i for i,x in enumerate(toc) if norm(x.get("title")) == norm(title) or norm(x.get("title")) in norm(title)]
        if not matches: continue
        i = matches[0]; item=toc[i]; body=article_body(text,toc,i,item.get("toc_end",0))
        if not body or len(re.sub(r"\s+", "", body)) < 500: continue
        new_article = "<article>" + body_to_html(body) + "</article>"
        old = re.search(r"<article[^>]*>.*?</article>", s, re.S)
        if old and old.group(0) != new_article and (re.search(r"(?:पद्य|गद्य)\s+[०-९0-9]+\.", html.unescape(re.sub('<[^>]+>',' ',old.group(0))[:500])) or norm(item.get('title')) not in norm(html.unescape(re.sub('<[^>]+>',' ',old.group(0))[:1200]))):
            page.write_text(s[:old.start()] + new_article + s[old.end():], encoding="utf-8")
            repaired += 1
    return repaired
def main(): print(f"Repaired {repair_pages()} article pages")
if __name__ == "__main__": main()
