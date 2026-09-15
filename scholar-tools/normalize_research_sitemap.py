#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
MIRROR = "https://videha-ejournal.github.io/videha/"
OFFICIAL = "https://www.videha.co.in/"
EXCLUDED = {".git", "node_modules", "_site", ".venv", "venv"}
NON_READER_PAGES = {
    "google7d0b1633a9939d34.html",
    "pinterest-40f05.html",
    "templates/scholar-article.html",
    "universal-search-embed-snippet.html",
}


def real_pages():
    out = set()
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".htm", ".html"}:
            continue
        rel = p.relative_to(ROOT).as_posix()
        if any(part in EXCLUDED for part in p.relative_to(ROOT).parts):
            continue
        if rel in NON_READER_PAGES:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"</head\s*>", text, re.I):
            out.add(rel)
    return out


def filter_sitemap(path: Path, base: str, allowed: set[str]):
    text = path.read_text(encoding="utf-8")
    kept: dict[str, str] = {}
    for block in re.findall(r"\s*<url>[\s\S]*?</url>", text):
        m = re.search(r"<loc>(.*?)</loc>", block)
        if not m:
            continue
        loc = m.group(1).replace("&amp;", "&")
        if not loc.startswith(base):
            continue
        rel = unquote(loc[len(base):])
        if rel in allowed:
            kept[rel] = loc

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for rel in sorted(kept, key=lambda x: (x.casefold(), x)):
        lines.append(f"  <url><loc>{html.escape(kept[rel], quote=False)}</loc></url>")
    lines.append("</urlset>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(kept)


def refresh_fixity():
    path = ROOT / "research" / "fixity-manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for rec in data.get("files", []):
        p = ROOT / rec["path"]
        if not p.exists():
            continue
        raw = p.read_bytes()
        rec["sha256"] = hashlib.sha256(raw).hexdigest()
        rec["bytes"] = len(raw)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    allowed = real_pages()
    mirror_count = filter_sitemap(ROOT / "sitemap.xml", MIRROR, allowed)
    official_count = filter_sitemap(ROOT / "research" / "sitemap-official.xml", OFFICIAL, allowed)
    if mirror_count != len(allowed) or official_count != len(allowed):
        raise SystemExit(f"Sitemap normalization mismatch: pages={len(allowed)} mirror={mirror_count} official={official_count}")
    refresh_fixity()
    print(
        f"Research sitemap normalization PASS: {len(allowed)} real reader-facing HTML pages; "
        "verification/template/helper pages excluded; duplicate URLs and blanket lastmod values removed; fixity refreshed."
    )


if __name__ == "__main__":
    main()
