#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ISSN = "2229-547X"
OFFICIAL = "https://www.videha.co.in/"
MIRROR = "https://videha-ejournal.github.io/videha/"
EXCLUDED = {".git", "node_modules", "_site", ".venv", "venv"}


def pages():
    out = []
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".htm", ".html"} and not any(x in EXCLUDED for x in p.relative_to(ROOT).parts):
            text = p.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"</head\s*>", text, re.I):
                out.append((p, text))
    return out


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    all_pages = pages()
    require(all_pages, "No HTML pages discovered")
    urls = []
    for p, text in all_pages:
        rel = p.relative_to(ROOT).as_posix()
        canonical = re.search(r'<link\s+[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', text, re.I)
        desc = re.search(r'<meta\s+[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)', text, re.I)
        require(canonical, f"Missing canonical: {rel}")
        require(desc and desc.group(1).strip(), f"Missing/empty description: {rel}")
        require(f'name="citation_issn" content="{ISSN}"' in text, f"Missing citation ISSN: {rel}")
        require('id="videha-scholarly-identity"' in text, f"Missing scholarly JSON-LD: {rel}")
        expected_base = MIRROR if rel.startswith(("research/", "tei/", "iiif/")) else OFFICIAL
        require(canonical.group(1).startswith(expected_base), f"Wrong canonical role for {rel}: {canonical.group(1)}")
        urls.append(MIRROR + rel)

    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    locs = re.findall(r"<loc>(.*?)</loc>", sitemap)
    require(len(locs) == len(all_pages), f"Sitemap/page count mismatch: {len(locs)} != {len(all_pages)}")
    require(len(locs) == len(set(locs)), "Duplicate sitemap URLs")
    require(all(u.startswith(MIRROR) for u in locs), "Mirror sitemap contains non-mirror URL")
    require((ROOT / "robots.txt").read_text(encoding="utf-8").find(MIRROR + "sitemap.xml") >= 0, "robots.txt lacks sitemap")

    authority = json.loads((ROOT / "research" / "citation-data-authority.json").read_text(encoding="utf-8"))
    require(authority["issn"] == ISSN, "Authority ISSN mismatch")
    require(authority["officialPublication"] == OFFICIAL, "Authority official URL mismatch")
    require(authority["githubMirror"] == MIRROR, "Authority mirror mismatch")
    require("no blanket licence" in authority["rights"].lower(), "Rights caution missing")
    require((ROOT / "CITATION.cff").exists() and (ROOT / ".zenodo.json").exists() and (ROOT / "codemeta.json").exists(), "DOI/citation readiness files missing")

    tei = ROOT / "tei" / "current-issue.xml"
    require(tei.exists(), "TEI current issue missing")
    tei_root = ET.parse(tei).getroot()
    require(ISSN in "".join(tei_root.itertext()), "TEI lacks ISSN")

    coll = json.loads((ROOT / "iiif" / "collection.json").read_text(encoding="utf-8"))
    require(coll.get("type") == "Collection", "IIIF collection type invalid")
    require(len(coll.get("items", [])) >= 1, "IIIF pilot has no manifests")
    for item in coll["items"]:
        mf = ROOT / item["id"].replace(MIRROR, "")
        require(mf.exists(), f"IIIF manifest missing: {mf}")
        data = json.loads(mf.read_text(encoding="utf-8"))
        require(data.get("type") == "Manifest" and data.get("items"), f"IIIF manifest invalid: {mf}")

    fixity_path = ROOT / "research" / "fixity-manifest.json"
    fixity = json.loads(fixity_path.read_text(encoding="utf-8"))
    require(fixity.get("algorithm") == "SHA-256", "Fixity algorithm is not SHA-256")
    require(len(fixity.get("files", [])) >= 8, "Fixity manifest unexpectedly small")
    for rec in fixity["files"]:
        p = ROOT / rec["path"]
        require(p.exists(), f"Fixity file missing: {rec['path']}")
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        require(digest == rec["sha256"], f"Fixity mismatch: {rec['path']}")
        require(p.stat().st_size == rec["bytes"], f"Size mismatch: {rec['path']}")

    official_sitemap = (ROOT / "research" / "sitemap-official.xml").read_text(encoding="utf-8")
    require(OFFICIAL in official_sitemap, "Official-site sitemap artifact missing official URLs")
    print(f"Videha scholarly infrastructure PASS: {len(all_pages)} HTML pages metadata-complete; sitemap aligned; TEI valid; {len(coll['items'])} IIIF manifests; {len(fixity['files'])} SHA-256 fixity records; citation/DOI-ready authority present.")

if __name__ == "__main__":
    main()
