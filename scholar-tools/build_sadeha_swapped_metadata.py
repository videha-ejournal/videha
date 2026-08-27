#!/usr/bin/env python3
"""Find probable author/title reversals in legacy Videha metadata using Sadeha evidence.

Review-only: this never publishes or rewrites metadata. Older Videha TOCs sometimes
use Title — Author instead of Author — Title. The detector therefore requires the
parsed author field itself to carry unmistakable title/topic signals and the parsed
title field to look like a personal byline. This deliberately favors precision over
recall so normal multi-word author names are not mis-flagged.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from extract_explicit_research import SourceParser

ROOT = Path(__file__).resolve().parents[1]
INV = ROOT / "research" / "data" / "article-inventory.json"
OUT = ROOT / "research" / "data" / "sadeha-swapped-metadata-review.json"
PUNCT = re.compile(r"[\s\-–—:;,.()\[\]{}'\"’‘“”।!?/\\|]+")
TITLE_SIGNALS = (
    "संरचना", "साहित्य", "रंगकर्म", "इतिहास", "संस्कृति", "भाषा", "व्याकरण",
    "आलोचना", "समीक्षा", "विमर्श", "अध्ययन", "अनुशीलन", "नाटक", "उपन्यास",
    "कथा", "समाज", "मिथिला", "मैथिली", "लोकगीत", "लोक गीत", "संस्कार गीत",
    "परिवर्तन", "परम्परा", "परंपरा", "गाथा", "चित्रकला", "लोककला", "research",
    "study", "history", "criticism", "literature", "language",
)
NON_ARTICLE_SIGNALS = ("कविता", "गीत १", "गजल १", "बाल गीत", "समाचार", "साक्षात्कार")
NAME_PREFIXES = ("डा", "डॉ", "प्रो", "प्रोफेसर", "आचार्य", "पं", "पं.", "श्री", "श्रीमती", "कवि", "लेखक", "लेखिका")


def norm(s: str) -> str:
    return PUNCT.sub("", (s or "").lower())


def plain(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip(" .:-–—")


def looks_name(s: str) -> bool:
    s = plain(s)
    if not 3 <= len(s) <= 90 or any(ch in s for ch in "/|।?!"):
        return False
    low = s.lower()
    if any(sig.lower() in low for sig in TITLE_SIGNALS):
        return False
    words = s.split()
    if not 1 <= len(words) <= 9:
        return False
    # Byline labels such as “लेखिका - विभा रानी” are still name-like.
    return len(words) >= 2 or low.startswith(tuple(x.lower() for x in NAME_PREFIXES))


def looks_title(s: str) -> bool:
    s = plain(s)
    if len(s) < 10 or len(s) > 300:
        return False
    low = s.lower()
    if low.startswith(tuple(x.lower() for x in NAME_PREFIXES)):
        return False
    # Require an actual subject/title signal. Mere word count is not enough.
    return any(x.lower() in low for x in TITLE_SIGNALS)


def read_sadeha() -> list[tuple[str, str]]:
    out = []
    for p in sorted((ROOT / "search-documents").glob("sadeha-*.html")):
        raw = p.read_text(encoding="utf-8", errors="ignore")
        parser = SourceParser()
        try:
            parser.feed(raw)
        except Exception:
            pass
        out.append((p.relative_to(ROOT).as_posix(), norm(parser.text())))
    return out


def main() -> None:
    rows = json.loads(INV.read_text(encoding="utf-8")).get("rows", [])
    docs = read_sadeha()
    found = []
    seen = set()
    for row in rows:
        section = str(row.get("section") or "")
        # Section 3 is overwhelmingly creative/poetry in Videha; do not generate a
        # metadata-reversal Scholar queue from it.
        if section.startswith("3."):
            continue
        parsed_author = plain(str(row.get("author") or ""))
        parsed_title = plain(str(row.get("title") or ""))
        if any(x.lower() in parsed_author.lower() for x in NON_ARTICLE_SIGNALS):
            continue
        if not (looks_title(parsed_author) and looks_name(parsed_title)):
            continue
        na, nt = norm(parsed_title), norm(parsed_author)
        if len(na) < 3 or len(nt) < 10:
            continue
        evidence = None
        for path, text in docs:
            pos = text.find(nt)
            if pos < 0:
                continue
            near = text[max(0, pos - 2200): min(len(text), pos + len(nt) + 2200)]
            if na in near:
                evidence = path
                break
        if not evidence:
            continue
        key = (str(row.get("issue") or ""), section, nt, na)
        if key in seen:
            continue
        seen.add(key)
        found.append({
            "issue": str(row.get("issue") or ""),
            "section": section,
            "parsed_author": parsed_author,
            "parsed_title": parsed_title,
            "proposed_author_for_review": parsed_title,
            "proposed_title_for_review": parsed_author,
            "sadeha_evidence": evidence,
            "body_chars_current_parse": row.get("body_chars"),
            "status": "editorial-review-only",
            "note": "High-precision probable legacy Title–Author reversal; verify original Videha heading/body before any metadata override or Scholar publication."
        })
    found.sort(key=lambda x: (int(x["issue"] or 0), x["section"]))
    payload = {
        "sadeha_html_sources": len(docs),
        "probable_swapped_metadata_records": len(found),
        "publication_effect": "none; review-only",
        "rows": found,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Sadeha legacy metadata review: {len(found)} high-precision probable author/title reversals; publication effect 0")


if __name__ == "__main__":
    main()
