#!/usr/bin/env python3
"""Build Videha's additive Google-Scholar-facing research layer.

Legacy issue pages are *classified* but never blindly republished as a single
article.  Article pages are generated only from curated JSON records under
scholar-data/articles/.  This prevents a multi-author issue page from being
misrepresented as one paper while still producing a retrospective candidate
queue automatically.
"""
from __future__ import annotations
import datetime as dt, html, json, re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "scholar-tools/config.json").read_text(encoding="utf-8"))
TEMPLATE = (ROOT / "templates/scholar-article.html").read_text(encoding="utf-8")
RESEARCH = ROOT / "research"
DATA = RESEARCH / "data"
CURATED = ROOT / "scholar-data" / "articles"

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.text=[]; self.title=[]; self.in_title=False
    def handle_starttag(self, tag, attrs):
        if tag.lower()=="title": self.in_title=True
    def handle_endtag(self, tag):
        if tag.lower()=="title": self.in_title=False
    def handle_data(self, data):
        self.text.append(data)
        if self.in_title: self.title.append(data)

def norm(s): return re.sub(r"\s+", " ", s or "").strip()
def esc_attr(s): return html.escape(str(s or ""), quote=True)
def slugify(s):
    s=norm(s).lower(); s=re.sub(r"[^\w\u0900-\u097f-]+", "-", s, flags=re.UNICODE)
    return s.strip("-")[:100] or "article"

def classify(text):
    low=text.lower(); score=0; hits=[]; excluded=[]; special=[]
    for term in CFG["explicit_research_terms"]:
        if term.lower() in low: score+=100; hits.append(term)
    for term in CFG["priority_terms"]:
        if term.lower() in low: score+=45; hits.append(term)
    for term in CFG["secondary_terms"]:
        if term.lower() in low: score+=20; hits.append(term)
    for term in CFG["reference_terms"]:
        if term.lower() in low: score+=25; hits.append(term)
    for term in CFG["exclude_terms"]:
        if term.lower() in low: excluded.append(term)
    for term in CFG["book_database_terms"]:
        if term.lower() in low: special.append(term)
    if len(text) < CFG["minimum_text_chars"]: score-=35
    treatment="candidate"
    if special: treatment="different-discovery-strategy"
    elif excluded and score < 100: treatment="exclude"
    elif score < 45: treatment="not-prioritized"
    return score, sorted(set(hits)), sorted(set(excluded)), sorted(set(special)), treatment

def infer_issue_year(path, title, text):
    joined=f"{path.name} {title} {text[:1200]}"
    years=re.findall(r"(?:19|20)\d{2}", joined); year=years[0] if years else "unknown"
    patterns=[r"(?:अंक|issue)\s*[-:#–—]?\s*([0-9०-९]{1,4})", r"(?:issue|ank)[-_ ]?([0-9]{1,4})"]
    issue="unknown"
    for p in patterns:
        m=re.search(p, joined, re.I)
        if m: issue=m.group(1); break
    return year, issue

def scan_legacy():
    rows=[]
    skip={"research","templates","scholar-tools","scholar-data","server-integration",".git","node_modules"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".htm",".html"}: continue
        if any(part in skip for part in path.parts): continue
        try:
            if path.stat().st_size > 5_000_000: continue
            raw=path.read_text(encoding="utf-8", errors="ignore")
        except OSError: continue
        p=TextParser()
        try: p.feed(raw)
        except Exception: pass
        text=norm(" ".join(p.text)); title=norm(" ".join(p.title)) or path.stem
        score,hits,excluded,special,treatment=classify(text)
        if score < 20 and treatment not in {"different-discovery-strategy"}: continue
        year,issue=infer_issue_year(path,title,text)
        rows.append({"source_path":path.relative_to(ROOT).as_posix(),"source_url":f"{CFG['site_url']}/{quote(path.relative_to(ROOT).as_posix())}","page_title":title[:300],"year":year,"issue":issue,"score":score,"matched_terms":hits,"excluded_terms":excluded,"special_terms":special,"treatment":treatment,"note":"Legacy-page candidate only; article boundary and author/title metadata require validation before Scholar publication."})
    return sorted(rows,key=lambda r:(-r["score"],r["source_path"]))

def load_curated():
    if not CURATED.exists(): return []
    out=[]
    for p in sorted(CURATED.glob("*.json")):
        try:
            rec=json.loads(p.read_text(encoding="utf-8")); rec["_manifest"]=p.name; out.append(rec)
        except Exception as e: print(f"Invalid manifest {p}: {e}")
    return out

def render_article(rec):
    required=["title","authors","publication_date","issue","full_text_html","source_url"]
    missing=[k for k in required if not rec.get(k)]
    if missing: raise ValueError(f"{rec.get('_manifest','record')}: missing {', '.join(missing)}")
    year=str(rec.get("year") or str(rec["publication_date"])[:4]); issue=str(rec["issue"])
    slug=rec.get("slug") or slugify(rec["title"]); rel=f"{year}/{issue}/{slug}.htm"
    canonical=f"{CFG['research_base']}/{rel}"; pdf_rel=f"{year}/{issue}/{slug}.pdf"; pdf_path=RESEARCH/pdf_rel
    authors=rec["authors"] if isinstance(rec["authors"],list) else [rec["authors"]]
    authors=[norm(a) for a in authors if norm(a)]
    citation_authors="\n".join(f'<meta name="citation_author" content="{esc_attr(a)}">' for a in authors)
    vol=rec.get("volume"); citation_volume=f'<meta name="citation_volume" content="{esc_attr(vol)}">' if vol else ""
    citation_pdf=f'<meta name="citation_pdf_url" content="{CFG["research_base"]}/{pdf_rel}">' if pdf_path.exists() else ""
    abstract=rec.get("abstract_html") or "<p>Abstract forthcoming.</p>"; abstract_text=norm(re.sub(r"<[^>]+>"," ",abstract))
    jsonld={"@context":"https://schema.org","@type":"ScholarlyArticle","headline":rec["title"],"author":[{"@type":"Person","name":a} for a in authors],"datePublished":rec["publication_date"],"isPartOf":{"@type":"Periodical","name":CFG["journal_title"],"issn":CFG["issn"]},"url":canonical,"inLanguage":rec.get("language","mai"),"keywords":rec.get("keywords",[]),"sameAs":rec["source_url"]}
    if pdf_path.exists(): jsonld["encoding"]={"@type":"MediaObject","contentUrl":f"{CFG['research_base']}/{pdf_rel}","encodingFormat":"application/pdf"}
    keywords=rec.get("keywords",[]); keywords=", ".join(keywords) if isinstance(keywords,list) else str(keywords)
    refs=rec.get("references_html") or "<p>References are included in the article text where supplied by the author.</p>"
    english_title=rec.get("english_title"); english_title=f"<p><strong>English title:</strong> {html.escape(english_title)}</p>" if english_title else ""
    standard=f"{'; '.join(authors)}. “{rec['title']}.” {CFG['journal_title']}, issue {issue}, {rec['publication_date']}. {canonical}"
    pdf_link=f' · <a href="{CFG["research_base"]}/{pdf_rel}">PDF</a>' if pdf_path.exists() else ""
    vals={"TITLE":html.escape(rec["title"]),"TITLE_ATTR":esc_attr(rec["title"]),"CANONICAL_URL":canonical,"CITATION_AUTHORS":citation_authors,"DATE":esc_attr(rec["publication_date"]),"ISSUE":esc_attr(issue),"CITATION_VOLUME":citation_volume,"CITATION_PDF":citation_pdf,"ABSTRACT_ATTR":esc_attr(abstract_text[:500]),"JSON_LD":json.dumps(jsonld,ensure_ascii=False).replace("</","<\\/"),"AUTHORS_VISIBLE":html.escape(", ".join(authors)),"DATE_VISIBLE":html.escape(str(rec["publication_date"])),"ENGLISH_TITLE":english_title,"ABSTRACT":abstract,"KEYWORDS":html.escape(keywords),"FULL_TEXT":rec["full_text_html"],"REFERENCES":refs,"STANDARD_CITATION":html.escape(standard),"SOURCE_URL":esc_attr(rec["source_url"]),"PDF_LINK":pdf_link}
    page=TEMPLATE
    for k,v in vals.items(): page=page.replace("{{"+k+"}}",str(v))
    out=RESEARCH/rel; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(page,encoding="utf-8")
    return {"title":rec["title"],"english_title":rec.get("english_title"),"authors":authors,"publication_date":rec["publication_date"],"year":year,"issue":issue,"keywords":rec.get("keywords",[]),"classification":rec.get("classification","research article"),"url":canonical,"pdf_url":f"{CFG['research_base']}/{pdf_rel}" if pdf_path.exists() else None,"source_url":rec["source_url"],"path":rel}

def write_index(articles,candidates):
    cards=[]
    for a in sorted(articles,key=lambda x:x["publication_date"],reverse=True):
        cards.append(f'<article><h2><a href="{html.escape(a["url"])}">{html.escape(a["title"])}</a></h2><p>{html.escape(", ".join(a["authors"]))} · {html.escape(str(a["publication_date"]))} · अंक {html.escape(a["issue"])}</p><p>{html.escape(a["classification"])}</p></article>')
    body="\n".join(cards) or '<p>No curated Scholar articles have been published yet. The retrospective candidate catalogue is being generated from the historical archive.</p>'
    page=f'''<!doctype html><html lang="mai"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Videha Research Index</title><link rel="canonical" href="{CFG['research_base']}/"><style>body{{font-family:Georgia,'Noto Serif Devanagari',serif;max-width:960px;margin:auto;padding:2rem;line-height:1.65;color:#171717}}header{{border-bottom:3px solid #8b1a1a}}article{{padding:1rem 0;border-bottom:1px solid #ddd}}a{{color:#7d1414}}</style></head><body><header><h1>विदेह शोध-सूची · Videha Research Index</h1><p>{CFG['journal_title']} · ISSN {CFG['issn']}</p><p>Scholar-facing index of research, linguistics, criticism with references, history, culture, ethnography, folklore and related academic material.</p></header><main>{body}</main><footer><p>Retrospective candidates detected: {len(candidates)}. Only validated article-level records are published as Scholar pages.</p><p><a href="{CFG['site_url']}/">Videha home</a></p></footer></body></html>'''
    (RESEARCH/"index.htm").write_text(page,encoding="utf-8")

def write_sitemap(articles):
    urls=[CFG["research_base"]+"/"]+[a["url"] for a in articles]
    xml='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+"\n".join(f"  <url><loc>{html.escape(u)}</loc></url>" for u in urls)+"\n</urlset>\n"
    (RESEARCH/"sitemap.xml").write_text(xml,encoding="utf-8")

def main():
    DATA.mkdir(parents=True,exist_ok=True)
    candidates=scan_legacy(); articles=[]
    for rec in load_curated():
        try: articles.append(render_article(rec))
        except Exception as e: print(f"Skipped {rec.get('_manifest')}: {e}")
    payload={"journal":CFG["journal_title"],"issn":CFG["issn"],"generated":dt.datetime.now(dt.timezone.utc).isoformat(),"articles":articles,"candidates":candidates}
    (DATA/"articles.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    write_index(articles,candidates); write_sitemap(articles)
    print(f"Videha Scholar build: {len(articles)} published articles; {len(candidates)} retrospective candidates")

if __name__=="__main__": main()
