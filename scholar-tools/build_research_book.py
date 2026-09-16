#!/usr/bin/env python3
"""Build the Videha Scholar Research Book from the canonical article inventory.

The single source of truth is research/data/articles.json.  This script must not
maintain a second paper count or a hand-written list of papers.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research" / "data" / "articles.json"
OUTPUT = ROOT / "research" / "videha-scholar-research-book.html"
DEVANAGARI = str.maketrans("0123456789", "०१२३४५६७८९")


def as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(as_text(item) for item in value if as_text(item))
    if isinstance(value, dict):
        for key in ("name", "title", "label", "value"):
            if value.get(key):
                return as_text(value[key])
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def devanagari_number(value) -> str:
    return str(value).translate(DEVANAGARI)


def issue_number(value):
    text = as_text(value).translate(str.maketrans("०१२३४५६७८९", "0123456789"))
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None


def article_href(path: str) -> str:
    path = path.replace("\\", "/").lstrip("/")
    return path[len("research/"):] if path.startswith("research/") else path


def load_source():
    raw = SOURCE.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    articles = payload.get("articles")
    if not isinstance(articles, list):
        raise SystemExit("research/data/articles.json must contain an 'articles' list")
    paths = [as_text(a.get("path")) for a in articles]
    if any(not path for path in paths):
        raise SystemExit("Every article inventory record must have a non-empty path")
    if len(paths) != len(set(paths)):
        raise SystemExit("Duplicate article paths found in research/data/articles.json")
    return raw, articles


def render() -> str:
    raw, articles = load_source()
    count = len(articles)
    source_sha = hashlib.sha256(raw).hexdigest()
    languages = Counter(as_text(a.get("language")) or "Unspecified" for a in articles)
    issues = [n for n in (issue_number(a.get("issue")) for a in articles) if n is not None]
    issue_range = f"{min(issues)}–{max(issues)}" if issues else "—"
    issue_range_deva = (
        f"{devanagari_number(min(issues))}–{devanagari_number(max(issues))}" if issues else "—"
    )

    lang_labels = {
        "Maithili (Devanagari)": "मैथिली",
        "Maithili": "मैथिली",
        "English": "अंग्रेज़ी",
    }
    badges = [f'<span class="badge">कुल शोध-लेख: <strong>{count}</strong></span>']
    for lang, total in sorted(languages.items(), key=lambda kv: (-kv[1], kv[0])):
        badges.append(
            f'<span class="badge">{html.escape(lang_labels.get(lang, lang))}: '
            f'<strong>{total}</strong></span>'
        )
    badges.append(f'<span class="badge">अंक: <strong>{html.escape(issue_range_deva)}</strong></span>')

    rows = []
    for idx, article in enumerate(articles, start=1):
        path = as_text(article.get("path"))
        href = article_href(path)
        title = as_text(article.get("title")) or Path(path).stem
        english_title = as_text(article.get("english_title"))
        authors = as_text(article.get("authors")) or as_text(article.get("author"))
        issue = as_text(article.get("issue"))
        language = as_text(article.get("language")) or "Unspecified"
        keywords = as_text(article.get("keywords"))
        secondary = f'<div class="english-title">{html.escape(english_title)}</div>' if english_title and english_title != title else ""
        rows.append(
            '<tr data-lang="{lang}" data-source-path="{source}">'
            '<td>{idx}</td>'
            '<td><a href="{href}">{title}</a>{secondary}</td>'
            '<td class="author">{authors}</td>'
            '<td class="hide-sm">{issue}</td>'
            '<td class="lang">{language}</td>'
            '<td class="kw">{keywords}</td>'
            '</tr>'.format(
                lang=html.escape(language, quote=True),
                source=html.escape(path, quote=True),
                idx=idx,
                href=html.escape(href, quote=True),
                title=html.escape(title),
                secondary=secondary,
                authors=html.escape(authors),
                issue=html.escape(issue),
                language=html.escape(language),
                keywords=html.escape(keywords),
            )
        )

    jsonld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "विदेह रिसर्च स्कॉलर—संयुक्त अनुसन्धान पुस्तक",
        "url": "https://www.videha.co.in/research/videha-scholar-research-book.html",
        "numberOfItems": count,
        "isPartOf": {
            "@type": "Periodical",
            "name": "VIDEHA — First Maithili Fortnightly e Journal",
            "alternateName": "विदेह प्रथम मैथिली पाक्षिक ई-पत्रिका",
            "issn": "2229-547X",
            "url": "https://www.videha.co.in/",
        },
    }
    jsonld_text = json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))

    return f'''<!doctype html>
<html lang="mai-Deva">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>विदेह रिसर्च स्कॉलर—अनुसन्धान पुस्तक | अंक {html.escape(issue_range_deva)} | {count} शोध-लेख | Videha Scholar</title>
<meta name="description" content="विदेह ई-पत्रिकाक रिसर्च स्कॉलर संस्करणक संयुक्त अनुसन्धान पुस्तक—अंक {html.escape(issue_range_deva)}, कुल {count} शोध-लेख। शीर्षक, लेखक, अंक तथा विषय-सूचक शब्दक आधार पर खोज योग्य।">
<link rel="canonical" href="https://www.videha.co.in/research/videha-scholar-research-book.html">
<meta name="videha-article-source" content="research/data/articles.json">
<meta name="videha-article-source-sha256" content="{source_sha}">
<meta name="videha-article-count" content="{count}">
<script type="application/ld+json" id="videha-scholarly-identity">{jsonld_text}</script>
<style>
:root{{--accent:#a11;--ink:#1d1d1f;--muted:#5f6470;--line:#d8dbe2;--soft:#f8f5ef}}
*{{box-sizing:border-box}}
body{{font-family:"Noto Serif Devanagari","Noto Sans Devanagari",serif;line-height:1.65;margin:0;color:var(--ink);background:#fff}}
a{{color:#831515}}
header{{padding:24px 18px 16px;background:linear-gradient(120deg,#fff 0%,#fff8ee 100%);border-bottom:1px solid var(--line)}}
header>div,main{{max-width:1180px;margin:auto}}
h1{{margin:.2rem 0;font-size:clamp(1.55rem,3vw,2.35rem)}}
.muted{{color:var(--muted)}}
main{{padding:20px 18px 40px}}
.summary{{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px}}
.badge{{display:inline-block;padding:5px 10px;border:1px solid var(--line);border-radius:999px;background:var(--soft)}}
.tools{{display:grid;grid-template-columns:minmax(220px,1fr) minmax(180px,260px);gap:10px;margin:0 0 12px}}
.tools label{{font-weight:700}}
.tools input,.tools select{{width:100%;font:inherit;padding:9px 10px;border:1px solid #aeb3bd;border-radius:6px;background:#fff}}
.status{{margin:8px 0 14px;color:var(--muted)}}
.table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:8px}}
table{{width:100%;border-collapse:collapse;min-width:850px}}
th,td{{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left}}
th{{position:sticky;top:0;background:#fbfaf7;z-index:1}}
tbody tr:nth-child(even){{background:#fcfcfc}}
.english-title{{font-size:.9em;color:var(--muted)}}
.author{{min-width:150px}}.lang{{min-width:130px}}.kw{{min-width:220px}}
footer{{max-width:1180px;margin:auto;padding:0 18px 34px;color:var(--muted)}}
@media(max-width:720px){{.tools{{grid-template-columns:1fr}}.hide-sm{{display:none}}}}
</style>
</head>
<body>
<!-- GENERATED BY scholar-tools/build_research_book.py FROM research/data/articles.json. DO NOT EDIT MANUALLY. -->
<header><div>
<h1>विदेह रिसर्च स्कॉलर—संयुक्त अनुसन्धान पुस्तक</h1>
<p>VIDEHA — First Maithili Fortnightly e Journal · ISSN 2229-547X · Since 2000</p>
<p class="muted">ई पन्ना <code>research/data/articles.json</code> सँ स्वतः बनैत अछि। स्रोत-सूची बदलिते शोध-पुस्तकक सूची आ गणना सेहो ओही स्रोतसँ बदलैत अछि।</p>
</div></header>
<main>
<div class="summary">{''.join(badges)}</div>
<div class="tools">
<label>खोज<input id="q" type="search" placeholder="शीर्षक, लेखक, अंक, भाषा वा सूचक शब्द" autocomplete="off"></label>
<label>भाषा<select id="lang"><option value="">सभ भाषा</option>{''.join(f'<option value="{html.escape(lang, quote=True)}">{html.escape(lang_labels.get(lang, lang))} ({total})</option>' for lang,total in sorted(languages.items(), key=lambda kv:(-kv[1],kv[0])))}</select></label>
</div>
<p class="status">देखाइत शोध-लेख: <strong id="visible-count">{count}</strong> / {count} · स्रोत SHA-256: <code>{source_sha[:12]}…</code></p>
<div class="table-wrap"><table id="papers">
<thead><tr><th>#</th><th>शीर्षक</th><th>लेखक</th><th class="hide-sm">अंक</th><th>भाषा</th><th>सूचक शब्द</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table></div>
</main>
<footer>© Gajendra Thakur, Editor — Videha eJournal · <a href="../research/index.htm">Videha Scholar Research</a></footer>
<script>
const rows=[...document.querySelectorAll('#papers tbody tr')];
const q=document.getElementById('q');
const lang=document.getElementById('lang');
const visible=document.getElementById('visible-count');
function filterRows(){{
  const needle=q.value.trim().toLocaleLowerCase();
  const wanted=lang.value;
  let n=0;
  for(const row of rows){{
    const okText=!needle || row.textContent.toLocaleLowerCase().includes(needle);
    const okLang=!wanted || row.dataset.lang===wanted;
    row.hidden=!(okText&&okLang);
    if(!row.hidden)n++;
  }}
  visible.textContent=n;
}}
q.addEventListener('input',filterRows);
lang.addEventListener('change',filterRows);
</script>
</body>
</html>
'''


def verify(rendered: str) -> None:
    raw, articles = load_source()
    count = len(articles)
    source_sha = hashlib.sha256(raw).hexdigest()
    if f'<meta name="videha-article-count" content="{count}">' not in rendered:
        raise SystemExit("Research Book count metadata is not aligned with articles.json")
    if f'<meta name="videha-article-source-sha256" content="{source_sha}">' not in rendered:
        raise SystemExit("Research Book source hash is not aligned with articles.json")
    expected_paths = [as_text(a.get("path")) for a in articles]
    actual_paths = []
    marker = 'data-source-path="'
    pos = 0
    while True:
        start = rendered.find(marker, pos)
        if start < 0:
            break
        start += len(marker)
        end = rendered.find('"', start)
        actual_paths.append(html.unescape(rendered[start:end]))
        pos = end + 1
    if actual_paths != expected_paths:
        raise SystemExit(
            f"Research Book rows differ from articles.json: expected {len(expected_paths)}, got {len(actual_paths)}"
        )
    if f'कुल शोध-लेख: <strong>{count}</strong>' not in rendered:
        raise SystemExit("Visible Research Book count is not aligned with articles.json")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if the committed book differs from the inventory-generated result")
    args = parser.parse_args()
    expected = render()
    verify(expected)
    if args.check:
        if not OUTPUT.exists():
            raise SystemExit(f"Missing generated Research Book: {OUTPUT}")
        current = OUTPUT.read_text(encoding="utf-8")
        verify(current)
        if current != expected:
            raise SystemExit("research/videha-scholar-research-book.html is stale; regenerate it from articles.json")
        _, articles = load_source()
        print(f"Research Book source alignment verified: {len(articles)} articles")
        return
    OUTPUT.write_text(expected, encoding="utf-8")
    _, articles = load_source()
    print(f"Generated {OUTPUT.relative_to(ROOT)} from research/data/articles.json: {len(articles)} articles")


if __name__ == "__main__":
    main()
