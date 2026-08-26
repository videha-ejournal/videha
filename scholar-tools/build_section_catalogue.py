#!/usr/bin/env python3
"""Build a conservative article-section-level scholarly catalogue for all Videha issues.

This catalogue is a screening layer, not automatic publication. It ranks individual
articles while keeping fiction, poetry, drama, ordinary reviews and ambiguous
material out of the Scholar publication set.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from extract_explicit_research import (
    SourceParser, clean_body, issue_files, parse_issue_date, parse_toc_entries, source_pdf,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "data" / "section-candidates.json"

PRIORITY_TITLE = {
    "linguistics": [
        "भाषाविज्ञान", "भाषा विज्ञान", "भाषा-विज्ञान", "भाषाशास्त्र", "भाषा-शास्त्र",
        "व्याकरण", "phonology", "morphology", "syntax", "linguistic",
    ],
    "history": ["इतिहास", "ऐतिहासिक", "history", "पञ्जी", "पंजी"],
    "ethnography-folklore": [
        "लोक साहित्य", "लोक-साहित्य", "लोकसंस्कृति", "लोक-संस्कृति", "नृविज्ञान",
        "नृवंश", "ethnography", "folklore", "लोककथा", "लोकगीत",
    ],
    "culture-art": ["मिथिला चित्रकला", "चित्रकला", "सांस्कृतिक", "संस्कृति", "लोककला"],
}
SECONDARY_TITLE = {
    "literary-criticism": [
        "आलोचना", "समालोचना", "तात्विक विश्लेषण", "विश्लेषण", "आलोचनात्मक",
        "critical study", "criticism",
    ],
    "academic-review": ["समीक्षा आलेख", "review essay"],
    "conference-seminar": ["seminar paper", "conference paper", "सेमिनार", "संगोष्ठी"],
    "critical-edition": ["critical edition", "आलोचनात्मक संस्करण", "सम्पादित पाठ", "संपादित पाठ"],
}
REFERENCE_TERMS = ["सन्दर्भ", "संदर्भ", "ग्रन्थसूची", "ग्रंथसूची", "bibliography", "references", "works cited"]
ACADEMIC_TERMS = ["शोध", "अनुसन्धान", "अनुसंधान", "अध्ययन", "पद्धति", "परिकल्पना", "विश्वविद्यालय", "research", "methodology"]
EXCLUDE_TITLE = [
    "कविता", "कथा", "कहानी", "लघुकथा", "उपन्यास", "नाटक", "प्रहसन", "गजल", "हाइकू",
    "गीत", "साक्षात्कार", "भेंटवार्ता", "समाचार", "घोषणा", "सम्पादकीय", "संपादकीय",
    "quiz", "प्रश्नोत्तरी", "ई-लर्निङ्ग", "e-learning", "श्रद्धांजलि", "पाठकीय मन्तव्य", "टिप्पणी",
]
LOW_PRIORITY_REVIEW = ["पोथी समीक्षा", "पुस्तक समीक्षा", "book review", "एक पोथी", "पोथी चर्चा", "अवलोकन"]


def contains_any(text: str, terms: list[str]) -> list[str]:
    low = (text or "").lower()
    return [t for t in terms if t.lower() in low]


def classify_section(title: str, body: str) -> tuple[int, str, list[str], list[str]]:
    score = 0
    signals: list[str] = []
    negatives: list[str] = []
    content_class = "other"

    explicit = contains_any(title, ["शोध आलेख", "शोध-आलेख", "शोधपत्र", "शोध पत्र", "research paper", "research article"])
    if explicit:
        score += 120
        signals += explicit
        content_class = "research-article"

    for cls, terms in PRIORITY_TITLE.items():
        hits = contains_any(title, terms)
        if hits:
            score += 70
            signals += hits
            if content_class == "other":
                content_class = cls

    for cls, terms in SECONDARY_TITLE.items():
        hits = contains_any(title, terms)
        if hits:
            score += 45
            signals += hits
            if content_class == "other":
                content_class = cls

    refs = contains_any(body, REFERENCE_TERMS)
    if refs:
        score += 40
        signals += refs

    academics = contains_any(body[:16000], ACADEMIC_TERMS)
    if academics:
        score += min(30, 8 * len(academics))
        signals += academics

    compact_len = len(re.sub(r"\s+", "", body))
    if compact_len >= 5000:
        score += 20
    elif compact_len >= 2500:
        score += 12
    elif compact_len < 900:
        score -= 50
        negatives.append("short-body")

    excluded = contains_any(title, EXCLUDE_TITLE)
    if excluded:
        score -= 150
        negatives += excluded

    low_review = contains_any(title, LOW_PRIORITY_REVIEW)
    if low_review and not refs:
        score -= 50
        negatives += low_review

    # Body-only academic words are weak evidence. Without a scholarly title class,
    # explicit research label or references, do not let them create a candidate alone.
    if content_class == "other" and not refs:
        score = min(score, 30)

    return score, content_class, sorted(set(signals)), sorted(set(negatives))


def extract_body(text: str, toc: list[dict], idx: int, floor: int) -> str:
    item = toc[idx]
    sm = re.compile(rf"(?m)^\s*{re.escape(item['section_source'])}\.\s*").search(text, floor)
    if not sm:
        return ""
    start = sm.start()
    end = len(text)
    for nxt in toc[idx + 1:]:
        nm = re.compile(rf"(?m)^\s*{re.escape(nxt['section_source'])}\.\s*").search(text, start + 1)
        if nm:
            end = nm.start()
            break
    if not item.get("author") or not item.get("title"):
        return ""
    return clean_body(text[start:end], item["section_source"], item["author"], item["title"])


def scan_issue(path: Path) -> list[dict]:
    mi = re.search(r"videha-(\d{1,4})\.html?$", path.name, re.I)
    if not mi:
        return []
    issue = str(int(mi.group(1)))
    raw = path.read_text(encoding="utf-8", errors="ignore")
    parser = SourceParser()
    try:
        parser.feed(raw)
    except Exception:
        pass
    text = parser.text()
    date = parse_issue_date(text, issue)
    pdf = source_pdf(parser, issue)
    toc, floor = parse_toc_entries(text)
    if not toc:
        return []

    out = []
    for idx, item in enumerate(toc):
        if not item.get("author") or not item.get("title"):
            continue
        body = extract_body(text, toc, idx, floor)
        score, cls, signals, negatives = classify_section(item["title"], body)
        if score < 35:
            continue
        status = "high-confidence-review" if score >= 100 and not negatives and date and len(body) >= 900 else "review"
        out.append({
            "issue": issue,
            "publication_date": date,
            "section": item["section"],
            "author": item["author"],
            "title": item["title"],
            "page_start": item["page_start"],
            "page_end": item["page_end"],
            "content_class": cls,
            "score": score,
            "signals": signals,
            "negative_signals": negatives,
            "status": status,
            "body_chars": len(body),
            "source_path": path.relative_to(ROOT).as_posix(),
            "source_url": pdf,
        })
    return out


def main() -> None:
    rows = []
    files = issue_files(ROOT / "search-documents")
    for path in files:
        try:
            rows.extend(scan_issue(path))
        except Exception as exc:
            rows.append({
                "source_path": path.relative_to(ROOT).as_posix(),
                "status": "scan-error", "error": str(exc), "score": -1,
            })
    rows.sort(key=lambda r: (
        -int(r.get("score", -1)),
        int(r.get("issue", 999999)) if str(r.get("issue", "")).isdigit() else 999999,
        str(r.get("title", "")),
    ))
    payload = {
        "issue_files_scanned": len(files),
        "candidate_sections": sum(1 for r in rows if r.get("score", -1) >= 0),
        "high_confidence_review": sum(1 for r in rows if r.get("status") == "high-confidence-review"),
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Videha section catalogue: {len(files)} issue files scanned; "
        f"{payload['candidate_sections']} scholarly section candidates; "
        f"{payload['high_confidence_review']} high-confidence review items"
    )


if __name__ == "__main__":
    main()
