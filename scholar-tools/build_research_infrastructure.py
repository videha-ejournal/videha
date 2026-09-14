#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = "https://www.videha.co.in/"
MIRROR = "https://videha-ejournal.github.io/videha/"
GITHUB_ORG = "https://github.com/videha-ejournal"
ISSN = "2229-547X"
EDITOR = "Gajendra Thakur"
RELEASE_DATE = "2026-09-14"
RELEASE_TAG = "research-2026.09.14"
RELEASE_ID = f"urn:videha:research-archive:{RELEASE_DATE}"
ISBN_AUTHORITY = "https://videha-ejournal.github.io/gajendra-preeti/isbn/"

EXCLUDED_DIRS = {".git", "node_modules", "_site", ".venv", "venv"}
GENERATED_PREFIXES = ("research/", "tei/", "iiif/")
IIIF_IMAGES = [
    "1_AshtbhujGanesh_Korth2_ShivMandir_Singhia_Bisfi.jpg",
    "1_BhagwatiGirija_Phulhar2_Kali_Uchchaith.jpg",
    "1_DeviKali_Korth2_Temple_Gosauni_Sthal_Korth.jpg",
]

DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
MONTHS = {
    "जनवरी": "01", "फरवरी": "02", "मार्च": "03", "अप्रैल": "04", "मई": "05", "जून": "06",
    "जुलाई": "07", "अगस्त": "08", "सितम्बर": "09", "सितंबर": "09", "अक्टूबर": "10",
    "नवम्बर": "11", "नवंबर": "11", "दिसम्बर": "12", "दिसंबर": "12",
}


def web_path(rel: str) -> str:
    return quote(rel.replace(os.sep, "/"), safe="/._-~()[]")


def current_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def strip_tags(value: str) -> str:
    value = re.sub(r"<script\b[\s\S]*?</script>", " ", value, flags=re.I)
    value = re.sub(r"<style\b[\s\S]*?</style>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def title_from_html(text: str, fallback: str) -> str:
    m = re.search(r"<title[^>]*>([\s\S]*?)</title>", text, re.I)
    return strip_tags(m.group(1)) if m else fallback


def issue_from_html(text: str):
    plain = strip_tags(text)
    m = re.search(r"विदेह\s+अंक\s+([०-९0-9]+)\s*\[\s*([०-९0-9]{1,2})\s+([^\s\]]+)\s+([०-९0-9]{4})\s*\]", plain)
    if not m:
        return None
    number = m.group(1).translate(DEVANAGARI_DIGITS)
    day = m.group(2).translate(DEVANAGARI_DIGITS).zfill(2)
    month = MONTHS.get(m.group(3))
    year = m.group(4).translate(DEVANAGARI_DIGITS)
    return {"number": number, "date": f"{year}-{month}-{day}" if month else None}


def set_meta(text: str, name: str, content: str) -> str:
    tag = f'<meta name="{name}" content="{html.escape(content, quote=True)}">'
    pattern = re.compile(rf"<meta\s+[^>]*name=[\"']{re.escape(name)}[\"'][^>]*>", re.I)
    if pattern.search(text):
        return pattern.sub(tag, text, count=1)
    return text.replace("</head>", tag + "\n</head>", 1)


def set_canonical(text: str, url: str) -> str:
    tag = f'<link rel="canonical" href="{html.escape(url, quote=True)}">'
    pattern = re.compile(r"<link\s+[^>]*rel=[\"']canonical[\"'][^>]*>", re.I)
    if pattern.search(text):
        return pattern.sub(tag, text, count=1)
    return text.replace("</head>", tag + "\n</head>", 1)


def set_description(text: str, title: str) -> str:
    description = f"{title}. Videha — First Maithili Fortnightly eJournal, ISSN {ISSN}; scholarly publication and digital research archive."
    m = re.search(r"<meta\s+[^>]*name=[\"']description[\"'][^>]*content=[\"']([^\"']*)[\"'][^>]*>", text, re.I)
    if m and m.group(1).strip():
        return text
    return set_meta(text, "description", description[:300])


def inject_jsonld(text: str, rel: str, title: str, canonical: str) -> str:
    mirror_url = MIRROR + web_path(rel)
    periodical = {
        "@type": "Periodical",
        "name": "Videha",
        "alternateName": "विदेह प्रथम मैथिली पाक्षिक ई-पत्रिका",
        "issn": ISSN,
        "url": OFFICIAL,
        "sameAs": [MIRROR, GITHUB_ORG],
        "editor": {"@type": "Person", "name": EDITOR},
    }
    obj = {
        "@context": "https://schema.org",
        "@type": "CollectionPage" if rel.startswith(GENERATED_PREFIXES) else "WebPage",
        "name": title,
        "url": canonical,
        "sameAs": mirror_url if canonical != mirror_url else OFFICIAL + web_path(rel),
        "inLanguage": "mai",
        "isPartOf": periodical,
        "publisher": periodical,
    }
    if rel in {"index.htm", "index.html"}:
        issue = issue_from_html(text)
        if issue:
            main_entity = {
                "@type": "PublicationIssue",
                "name": title,
                "issueNumber": issue["number"],
                "isPartOf": periodical,
                "url": canonical,
            }
            if issue.get("date"):
                main_entity["datePublished"] = issue["date"]
            obj["mainEntity"] = main_entity
    script = '<script type="application/ld+json" id="videha-scholarly-identity">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "</script>"
    pattern = re.compile(r"<script\s+[^>]*id=[\"']videha-scholarly-identity[\"'][^>]*>[\s\S]*?</script>", re.I)
    if pattern.search(text):
        return pattern.sub(script, text, count=1)
    return text.replace("</head>", script + "\n</head>", 1)


def html_files():
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".htm", ".html"}:
            continue
        if any(part in EXCLUDED_DIRS for part in p.relative_to(ROOT).parts):
            continue
        yield p


def patch_html_pages():
    changed = 0
    total = 0
    for p in html_files():
        rel = p.relative_to(ROOT).as_posix()
        text = p.read_text(encoding="utf-8", errors="ignore")
        if "</head>" not in text.lower():
            continue
        total += 1
        title = title_from_html(text, p.stem)
        canonical = (MIRROR if rel.startswith(GENERATED_PREFIXES) else OFFICIAL) + web_path(rel)
        new = set_canonical(text, canonical)
        new = set_description(new, title)
        new = set_meta(new, "citation_journal_title", "Videha")
        new = set_meta(new, "citation_issn", ISSN)
        new = set_meta(new, "DC.publisher", "Videha — First Maithili Fortnightly eJournal")
        new = set_meta(new, "DC.identifier", canonical)
        new = set_meta(new, "videha_github_mirror", MIRROR)
        new = set_meta(new, "videha_digital_research_archives", GITHUB_ORG)
        new = inject_jsonld(new, rel, title, canonical)
        if new != text:
            p.write_text(new, encoding="utf-8")
            changed += 1
    return total, changed


def git_dates(paths):
    wanted = set(paths)
    dates = {}
    try:
        raw = subprocess.check_output(
            ["git", "log", "--format=@@%cs", "--name-only", "--no-renames", "--diff-filter=AM"],
            cwd=ROOT, text=True, errors="ignore",
        )
        current = None
        for line in raw.splitlines():
            if line.startswith("@@"):
                current = line[2:].strip()
            elif current and line in wanted and line not in dates:
                dates[line] = current
                if len(dates) == len(wanted):
                    break
    except Exception:
        pass
    return dates


def build_sitemaps(paths):
    dates = git_dates(paths)
    def render(base):
        rows = []
        for rel in sorted(paths):
            url = base + web_path(rel)
            lm = dates.get(rel)
            last = f"<lastmod>{lm}</lastmod>" if lm else ""
            rows.append(f"  <url><loc>{html.escape(url)}</loc>{last}</url>")
        return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(rows) + "\n</urlset>\n"
    (ROOT / "sitemap.xml").write_text(render(MIRROR), encoding="utf-8")
    research = ROOT / "research"
    research.mkdir(exist_ok=True)
    (research / "sitemap-official.xml").write_text(render(OFFICIAL), encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {MIRROR}sitemap.xml\n", encoding="utf-8")


class RSSListParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.in_li = False
        self.href = None
        self.buf = []
    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self.in_li = True; self.href = None; self.buf = []
        if self.in_li and tag == "a":
            self.href = dict(attrs).get("href")
    def handle_data(self, data):
        if self.in_li:
            self.buf.append(data)
    def handle_endtag(self, tag):
        if tag == "li" and self.in_li:
            label = re.sub(r"\s+", " ", "".join(self.buf)).strip()
            if label:
                self.items.append((label, self.href))
            self.in_li = False


def build_tei():
    rss = ROOT / "videha-rss.xml"
    if not rss.exists():
        return None
    tree = ET.parse(rss)
    item = tree.find("./channel/item")
    if item is None:
        return None
    title = item.findtext("title") or "Videha issue"
    issue = re.search(r"अंक\s+([०-९0-9]+)", title)
    issue_no = issue.group(1).translate(DEVANAGARI_DIGITS) if issue else "current"
    desc = item.findtext("description") or ""
    parser = RSSListParser(); parser.feed(desc)
    TEI = "http://www.tei-c.org/ns/1.0"
    ET.register_namespace("", TEI)
    tei = ET.Element(f"{{{TEI}}}TEI")
    header = ET.SubElement(tei, f"{{{TEI}}}teiHeader")
    file_desc = ET.SubElement(header, f"{{{TEI}}}fileDesc")
    title_stmt = ET.SubElement(file_desc, f"{{{TEI}}}titleStmt")
    ET.SubElement(title_stmt, f"{{{TEI}}}title").text = title
    ET.SubElement(title_stmt, f"{{{TEI}}}editor").text = EDITOR
    pub = ET.SubElement(file_desc, f"{{{TEI}}}publicationStmt")
    ET.SubElement(pub, f"{{{TEI}}}publisher").text = "Videha — First Maithili Fortnightly eJournal"
    ET.SubElement(pub, f"{{{TEI}}}idno", {"type": "ISSN"}).text = ISSN
    ET.SubElement(pub, f"{{{TEI}}}idno", {"type": "URI"}).text = OFFICIAL
    availability = ET.SubElement(pub, f"{{{TEI}}}availability")
    ET.SubElement(availability, f"{{{TEI}}}p").text = "Rights follow the source item notices; no blanket licence is asserted by this TEI representation."
    source = ET.SubElement(file_desc, f"{{{TEI}}}sourceDesc")
    ET.SubElement(source, f"{{{TEI}}}p").text = "Generated from Videha RSS/current-issue metadata and links."
    text = ET.SubElement(tei, f"{{{TEI}}}text")
    body = ET.SubElement(text, f"{{{TEI}}}body")
    div = ET.SubElement(body, f"{{{TEI}}}div", {"type": "issue", "n": issue_no})
    ET.SubElement(div, f"{{{TEI}}}head").text = title
    list_bibl = ET.SubElement(div, f"{{{TEI}}}listBibl")
    for label, href in parser.items:
        bibl = ET.SubElement(list_bibl, f"{{{TEI}}}bibl")
        ET.SubElement(bibl, f"{{{TEI}}}title").text = label
        if href:
            ET.SubElement(bibl, f"{{{TEI}}}ref", {"target": href}).text = href
    out = ROOT / "tei"; out.mkdir(exist_ok=True)
    xml = ET.tostring(tei, encoding="unicode", xml_declaration=False)
    content = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml + "\n"
    (out / "current-issue.xml").write_text(content, encoding="utf-8")
    if issue_no != "current":
        (out / f"videha-issue-{issue_no}.xml").write_text(content, encoding="utf-8")
    return issue_no


def jpeg_size(path: Path):
    data = path.read_bytes()
    i = 2
    if data[:2] != b"\xff\xd8":
        return None
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1; continue
        marker = data[i + 1]
        i += 2
        if marker in {0xD8, 0xD9}:
            continue
        if i + 2 > len(data):
            break
        length = int.from_bytes(data[i:i+2], "big")
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            if i + 7 <= len(data):
                h = int.from_bytes(data[i+3:i+5], "big")
                w = int.from_bytes(data[i+5:i+7], "big")
                return w, h
        i += max(length, 2)
    return None


def build_iiif():
    base_dir = ROOT / "iiif" / "manifests"; base_dir.mkdir(parents=True, exist_ok=True)
    manifests = []
    for filename in IIIF_IMAGES:
        p = ROOT / filename
        if not p.exists():
            continue
        dims = jpeg_size(p)
        if not dims:
            continue
        w, h = dims
        slug = re.sub(r"[^a-z0-9]+", "-", p.stem.lower()).strip("-")
        mid = MIRROR + f"iiif/manifests/{slug}.json"
        image_url = MIRROR + web_path(filename)
        canvas_id = mid + "/canvas/1"
        manifest = {
            "@context": "http://iiif.io/api/presentation/3/context.json",
            "id": mid,
            "type": "Manifest",
            "label": {"en": [p.stem.replace("_", " ")], "mai": [p.stem.replace("_", " ")]},
            "summary": {"en": ["Videha digital heritage image from the Mithila research archive."], "mai": ["विदेह मिथिला शोध-अभिलेखक डिजिटल धरोहर चित्र।"]},
            "requiredStatement": {"label": {"en": ["Rights"]}, "value": {"en": ["See source/item notice; no blanket licence asserted."]}},
            "homepage": [{"id": OFFICIAL + web_path(filename), "type": "Text", "label": {"en": ["Videha source"]}, "format": "text/html"}],
            "items": [{
                "id": canvas_id, "type": "Canvas", "height": h, "width": w,
                "items": [{"id": canvas_id + "/page/1", "type": "AnnotationPage", "items": [{
                    "id": canvas_id + "/annotation/1", "type": "Annotation", "motivation": "painting",
                    "body": {"id": image_url, "type": "Image", "format": "image/jpeg", "height": h, "width": w},
                    "target": canvas_id,
                }]}],
            }],
        }
        (base_dir / f"{slug}.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifests.append({"id": mid, "type": "Manifest", "label": manifest["label"]})
    coll = {
        "@context": "http://iiif.io/api/presentation/3/context.json",
        "id": MIRROR + "iiif/collection.json", "type": "Collection",
        "label": {"en": ["Videha Mithila Digital Heritage Pilot"], "mai": ["विदेह मिथिला डिजिटल धरोहर पायलट"]},
        "items": manifests,
    }
    (ROOT / "iiif" / "collection.json").write_text(json.dumps(coll, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(manifests)


def build_authority_and_release():
    research = ROOT / "research"; research.mkdir(exist_ok=True)
    sha = current_sha()
    policy = {
        "name": "Videha Citation & Data Authority",
        "officialPublication": OFFICIAL,
        "githubMirror": MIRROR,
        "issn": ISSN,
        "editor": EDITOR,
        "digitalResearchArchives": GITHUB_ORG,
        "isbnAuthority": ISBN_AUTHORITY,
        "roles": {
            "official": "Authoritative publication site",
            "mirror": "Resilient GitHub mirror and searchable research access",
            "archives": "Versioned digital research archives, data, software and preservation manifests",
        },
        "rights": "Rights follow item-level source notices; no blanket licence is inferred or asserted.",
        "preferredJournalCitation": f"Videha — First Maithili Fortnightly eJournal. ISSN {ISSN}. {OFFICIAL}",
        "releaseIdentifier": RELEASE_ID,
        "releaseTag": RELEASE_TAG,
        "sourceCommit": sha,
    }
    (research / "citation-data-authority.json").write_text(json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    body = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Videha Citation &amp; Data Authority</title><meta name="description" content="Authoritative citation, identifier, mirror, ISBN and research-data policy for Videha, ISSN {ISSN}."><link rel="canonical" href="{MIRROR}research/citation-data-authority.html"></head><body><main><h1>Videha Citation &amp; Data Authority</h1><p><strong>Videha — First Maithili Fortnightly eJournal · ISSN {ISSN}</strong></p><p>Authoritative publication: <a href="{OFFICIAL}">{OFFICIAL}</a><br>GitHub mirror: <a href="{MIRROR}">{MIRROR}</a><br>Digital Research Archives: <a href="{GITHUB_ORG}">{GITHUB_ORG}</a><br>Editor: {EDITOR}</p><h2>Repository roles</h2><p>The official Videha site is the authoritative publication. The GitHub Pages site is its resilient mirror and research-access layer. GitHub repositories are the versioned Digital Research Archives for data, software, preservation metadata and scholarly derivatives.</p><h2>Preferred journal citation</h2><p>Videha — First Maithili Fortnightly eJournal. ISSN {ISSN}. <a href="{OFFICIAL}">{OFFICIAL}</a>.</p><h2>Books and ISBNs</h2><p>Use the <a href="{ISBN_AUTHORITY}">authoritative 293-ISBN registry</a>; explicit editor corrections take precedence over older conflicting lists.</p><h2>Research releases and persistence</h2><p>Release identifier: <code>{RELEASE_ID}</code>. Git tag: <code>{RELEASE_TAG}</code>. Source commit: <code>{sha}</code>. DOI-ready metadata are supplied in <code>.zenodo.json</code>, <code>CITATION.cff</code> and <code>codemeta.json</code>. A DOI is not claimed unless an external DOI registrar actually mints one.</p><h2>Preservation</h2><p>SHA-256 fixity manifests, TEI P5 issue metadata and IIIF Presentation 3 manifests are maintained in this repository. Rights follow item-level source notices; no blanket licence is asserted.</p></main></body></html>'''
    (research / "citation-data-authority.html").write_text(body, encoding="utf-8")
    release = {"identifier": RELEASE_ID, "tag": RELEASE_TAG, "date": RELEASE_DATE, "commit": sha, "title": "Videha Digital Research Archives scholarly infrastructure release", "issn": ISSN, "official": OFFICIAL, "mirror": MIRROR, "archive": GITHUB_ORG}
    (research / "release-metadata.json").write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    citation = f'''cff-version: 1.2.0\nmessage: "If you use the Videha Digital Research Archives, cite this repository and the underlying Videha publication."\ntitle: "Videha Digital Research Archives"\ntype: dataset\nauthors:\n  - family-names: "Thakur"\n    given-names: "Gajendra"\nversion: "{RELEASE_DATE}"\ndate-released: "{RELEASE_DATE}"\nurl: "{GITHUB_ORG}"\nidentifiers:\n  - type: other\n    value: "ISSN {ISSN}"\n    description: "Videha journal ISSN"\n  - type: other\n    value: "{RELEASE_ID}"\n    description: "Videha research-release URN"\n'''
    (ROOT / "CITATION.cff").write_text(citation, encoding="utf-8")
    zenodo = {"title": "Videha Digital Research Archives", "upload_type": "dataset", "description": f"Versioned research and preservation layer for Videha — First Maithili Fortnightly eJournal, ISSN {ISSN}.", "creators": [{"name": "Thakur, Gajendra"}], "keywords": ["Maithili", "Mithila", "Vajji", "Anga", "digital humanities", "Videha"], "notes": "Rights follow item-level source notices; no blanket licence is asserted."}
    (ROOT / ".zenodo.json").write_text(json.dumps(zenodo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    codemeta = {"@context": "https://doi.org/10.5063/schema/codemeta-2.0", "@type": "Dataset", "name": "Videha Digital Research Archives", "identifier": RELEASE_ID, "datePublished": RELEASE_DATE, "author": [{"@type": "Person", "givenName": "Gajendra", "familyName": "Thakur"}], "url": GITHUB_ORG, "isPartOf": {"@type": "Periodical", "name": "Videha", "issn": ISSN, "url": OFFICIAL}}
    (ROOT / "codemeta.json").write_text(json.dumps(codemeta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_fixity():
    include = [ROOT / "index.htm", ROOT / "videha-rss.xml", ROOT / "sitemap.xml", ROOT / "robots.txt", ROOT / "CITATION.cff", ROOT / ".zenodo.json", ROOT / "codemeta.json"]
    for dirname in ["research", "tei", "iiif"]:
        d = ROOT / dirname
        if d.exists():
            include.extend(p for p in d.rglob("*") if p.is_file() and p.name != "fixity-manifest.json")
    records = []
    for p in sorted(set(include)):
        if not p.exists():
            continue
        data = p.read_bytes()
        records.append({"path": p.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    manifest = {"algorithm": "SHA-256", "generated": RELEASE_DATE, "releaseIdentifier": RELEASE_ID, "sourceCommit": current_sha(), "files": records}
    out = ROOT / "research" / "fixity-manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(records)


def main():
    build_authority_and_release()
    issue = build_tei()
    iiif_count = build_iiif()
    total, changed = patch_html_pages()
    paths = [p.relative_to(ROOT).as_posix() for p in html_files()]
    build_sitemaps(paths)
    fixity_count = build_fixity()
    print(f"Videha research infrastructure built: {total} HTML pages scanned, {changed} metadata updates; TEI issue={issue}; IIIF manifests={iiif_count}; fixity files={fixity_count}.")

if __name__ == "__main__":
    main()
