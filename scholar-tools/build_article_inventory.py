#!/usr/bin/env python3
"""Create a complete article-level inventory from every Videha issue TOC.

Unlike the Scholar candidate list, this file intentionally inventories all recoverable
TOC entries so no potentially scholarly item disappears because its title lacks a
particular keyword. It is an editorial discovery dataset, not a publication list.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from extract_explicit_research import (
    SourceParser, article_body, issue_files, parse_issue_date, parse_toc_entries, source_pdf,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "data" / "article-inventory.json"

FICTION = ["कथा", "कहानी", "लघुकथा", "उपन्यास", "नाटक", "प्रहसन"]
POETRY = ["कविता", "गजल", "हाइकू", "गीत", "पद्य"]
NON_SCHOLARLY = ["साक्षात्कार", "भेंटवार्ता", "समाचार", "घोषणा", "सम्पादकीय", "संपादकीय", "पाठकीय मन्तव्य", "टिप्पणी", "प्रश्नोत्तरी", "quiz", "ई-लर्निङ्ग", "e-learning"]
SCHOLAR_TITLE = {
    "research-explicit": ["शोध आलेख", "शोध-आलेख", "शोधपत्र", "शोध पत्र", "research paper", "research article"],
    "linguistics": ["भाषाविज्ञान", "भाषा विज्ञान", "भाषा-विज्ञान", "भाषाशास्त्र", "भाषा-शास्त्र", "व्याकरण", "linguistic", "phonology", "morphology", "syntax"],
    "literary-history": ["साहित्यक इतिहास", "साहित्य इतिहास", "साहित्यमे", "साहित्य मे", "साहित्यिक योगदान", "परिवारक योगदान"],
    "history": ["इतिहास", "ऐतिहासिक", "history", "पञ्जी", "पंजी"],
    "folklore-ethnography": ["लोक साहित्य", "लोक-साहित्य", "लोकसंस्कृति", "लोक-संस्कृति", "नृविज्ञान", "नृवंश", "ethnography", "folklore", "लोककथा", "लोकगीत"],
    "culture-art": ["मिथिला चित्रकला", "चित्रकला", "सांस्कृतिक", "संस्कृति", "लोककला"],
    "criticism": ["आलोचना", "समालोचना", "तात्विक विश्लेषण", "विश्लेषण", "आलोचनात्मक", "विमर्श", "critical study", "criticism"],
    "academic-review": ["समीक्षा आलेख", "शोध-समीक्षा", "review essay"],
    "conference-seminar": ["seminar paper", "conference paper", "सेमिनार", "संगोष्ठी"],
    "critical-edition": ["critical edition", "आलोचनात्मक संस्करण", "सम्पादित पाठ", "संपादित पाठ"],
}
REFERENCE_TERMS = ["सन्दर्भ", "संदर्भ", "ग्रन्थसूची", "ग्रंथसूची", "bibliography", "references", "works cited"]


def hits(text: str, terms: list[str]) -> list[str]:
    low = (text or "").lower()
    return [x for x in terms if x.lower() in low]


def classify(title: str, body: str, section: str) -> tuple[str, list[str], bool]:
    negative = hits(title, FICTION + POETRY + NON_SCHOLARLY)
    if negative:
        return "non-scholar-priority", negative, False
    signals: list[str] = []
    classes: list[str] = []
    for cls, terms in SCHOLAR_TITLE.items():
        h = hits(title, terms)
        if h:
            classes.append(cls)
            signals += h
    refs = hits(body, REFERENCE_TERMS)
    if refs:
        signals += refs
    if classes:
        cls = classes[0] if len(classes) == 1 else "+".join(classes)
        return cls, sorted(set(signals)), True
    # Section 3 is normally poetry in Videha; do not promote body-only reference hits there.
    if refs and not section.startswith("3."):
        return "references-present", sorted(set(refs)), True
    return "unclassified", [], False


def scan_issue(path: Path, issue_override: str | None = None) -> list[dict]:
    m = re.search(r"videha-(\d{1,4})\.html?$", path.name, re.I)
    if not m and not issue_override:
        return []
    issue = str(int(issue_override or m.group(1)))
    raw = path.read_text(encoding="utf-8", errors="ignore")
    parser = SourceParser()
    try:
        parser.feed(raw)
    except Exception:
        pass
    text = parser.text()
    toc, floor = parse_toc_entries(text)
    date = parse_issue_date(text, issue)
    pdf = source_pdf(parser, issue)
    rows = []
    for idx, item in enumerate(toc):
        author, title = item.get("author"), item.get("title")
        if not author or not title:
            continue
        body = article_body(text, toc, idx, floor)
        cls, signals, scholar_candidate = classify(title, body, item["section"])
        rows.append({
            "issue": issue,
            "publication_date": date,
            "section": item["section"],
            "author": author,
            "title": title,
            "page_start": item["page_start"],
            "page_end": item["page_end"],
            "body_chars": len(body),
            "classification": cls,
            "signals": signals,
            "scholar_candidate": scholar_candidate,
            "source_path": path.relative_to(ROOT).as_posix(),
            "source_url": pdf,
        })
    return rows


def current_index_issue(path: Path) -> str | None:
    """Return the live index.htm issue so forthcoming issues enter the inventory immediately."""
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8", errors="ignore")
    trans = str.maketrans("०१२३४५६७८९", "0123456789")
    patterns = [
        r'issue-number-square[^>]*>\s*([०-९0-9]{1,4})\s*<',
        r'विदेह\s+अंक\s*([०-९0-9]{1,4})',
        r'Current\s+Issue\s*[:#-]?\s*([०-९0-9]{1,4})',
    ]
    for pattern in patterns:
        match = re.search(pattern, raw, re.I | re.S)
        if match:
            return str(int(match.group(1).translate(trans)))
    return None


def main() -> None:
    files = issue_files(ROOT / "search-documents")
    rows: list[dict] = []
    errors: list[dict] = []
    for path in files:
        try:
            rows.extend(scan_issue(path))
        except Exception as exc:
            errors.append({"source_path": path.relative_to(ROOT).as_posix(), "error": str(exc)})
    live_issue = current_index_issue(ROOT / "index.htm")
    archived_issues = {str(int(r["issue"])) for r in rows}
    live_included = bool(live_issue and live_issue not in archived_issues)
    if live_included:
        try:
            rows.extend(scan_issue(ROOT / "index.htm", live_issue))
        except Exception as exc:
            errors.append({"source_path": "index.htm", "error": str(exc)})
    rows.sort(key=lambda r: (int(r["issue"]), r["section"]))
    candidates = [r for r in rows if r["scholar_candidate"]]
    payload = {
        "issue_files_scanned": len(files),
        "current_index_issue": live_issue,
        "current_index_included": live_included,
        "article_entries_inventoried": len(rows),
        "scholar_candidates": len(candidates),
        "parse_errors": errors,
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Videha article inventory: {len(files)} issue files; {len(rows)} article entries; "
        f"{len(candidates)} Scholar candidates; {len(errors)} parse errors"
    )


if __name__ == "__main__":
    main()
