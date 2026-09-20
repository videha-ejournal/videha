#!/usr/bin/env python3
"""Audit every canonical Videha Scholar article page for missing or stub content."""
from __future__ import annotations
import argparse, html, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INV=ROOT/"research/data/articles.json"
OUT=ROOT/"research/data/stub-audit.json"
STUB_MARKERS=(
    "मूल पूर्ण पाठ:",
    "full text forthcoming",
    "content forthcoming",
    "placeholder",
    "source-linked scholar page",
    "article text will be added",
)

def plain_article(text:str)->str:
    m=re.search(r"(?is)<article\b[^>]*>(.*?)</article>", text)
    if not m:
        return ""
    body=re.sub(r"(?is)<script\b.*?</script>|<style\b.*?</style>", " ", m.group(1))
    body=re.sub(r"(?is)<[^>]+>", " ", body)
    return " ".join(html.unescape(body).split())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--fail-on-stub", action="store_true")
    args=ap.parse_args()
    payload=json.loads(INV.read_text(encoding="utf-8"))
    articles=payload.get("articles") or []
    definite=[]
    short_review=[]
    checked=[]
    for rec in articles:
        rel=str(rec.get("path") or "")
        p=ROOT/"research"/rel
        row={"path":rel,"title":rec.get("title"),"issue":rec.get("issue")}
        if not p.exists():
            row["reason"]="missing HTML file"
            definite.append(row); continue
        raw=p.read_text(encoding="utf-8",errors="ignore")
        body=plain_article(raw)
        compact=len(re.sub(r"\s+","",body))
        row["body_chars"]=compact
        low=body.casefold()
        marker=next((x for x in STUB_MARKERS if x.casefold() in low),None)
        if not re.search(r"(?is)<article\b",raw):
            row["reason"]="missing <article> body"
            definite.append(row)
        elif compact < 300:
            row["reason"]="article body below 300 non-space characters"
            definite.append(row)
        elif marker:
            row["reason"]=f"stub marker: {marker}"
            definite.append(row)
        elif compact < 1200:
            row["reason"]="short article body below 1200 non-space characters; manual review recommended"
            short_review.append(row)
        checked.append(row)
    report={
        "canonical_count":len(articles),
        "checked_html":len(checked),
        "definite_stub_count":len(definite),
        "short_review_count":len(short_review),
        "definite_stubs":definite,
        "short_review":short_review,
    }
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if args.fail_on_stub and definite:
        raise SystemExit(f"Definite stub/missing article pages found: {len(definite)}")

if __name__=="__main__":
    main()
