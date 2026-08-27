#!/usr/bin/env python3
"""Find probable author/title reversals in legacy Videha metadata using Sadeha evidence.

This is review-only. It never publishes or rewrites metadata. Older Videha TOCs often
use Title — Author rather than Author — Title; the generic parser can therefore store
the fields backwards. A Sadeha compilation containing both strings close together is
useful independent evidence for editorial recovery.
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
    "कथा", "समाज", "मिथिला", "मैथिली", "research", "study", "history",
)
NAME_PREFIXES = ("डा", "डॉ", "प्रो", "आचार्य", "पं", "श्री", "श्रीमती", "कवि")


def norm(s: str) -> str:
    return PUNCT.sub("", (s or "").lower())


def plain(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip(" .:-–—")


def looks_name(s: str) -> bool:
    s = plain(s)
    if not 3 <= len(s) <= 80 or any(ch in s for ch in "/|।?!"):
        return False
    words = s.split()
    if not 1 <= len(words) <= 8:
        return False
    if any(sig.lower() in s.lower() for sig in TITLE_SIGNALS):
        return False
    return len(words) >= 2 or s.startswith(NAME_PREFIXES)


def looks_title(s: str) -> bool:
    s = plain(s)
    if len(s) < 10 or len(s) > 260:
        return False
    low = s.lower()
    return any(x.lower() in low for x in TITLE_SIGNALS) or len(s.split()) >= 4


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
        parsed_author = plain(str(row.get("author") or ""))
        parsed_title = plain(str(row.get("title") or ""))
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
        key = (str(row.get("issue") or ""), str(row.get("section") or ""), nt, na)
        if key in seen:
            continue
        seen.add(key)
        found.append({
            "issue": str(row.get("issue") or ""),
            "section": str(row.get("section") or ""),
            "parsed_author": parsed_author,
            "parsed_title": parsed_title,
            "proposed_author_for_review": parsed_title,
            "proposed_title_for_review": parsed_author,
            "sadeha_evidence": evidence,
            "body_chars_current_parse": row.get("body_chars"),
            "status": "editorial-review-only",
            "note": "Probable legacy Title–Author reversal; verify the original Videha heading/body before any metadata override or Scholar publication."
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
    print(f"Sadeha legacy metadata review: {len(found)} probable author/title reversals; publication effect 0")


if __name__ == "__main__":
    main()
