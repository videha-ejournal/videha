#!/usr/bin/env python3
"""Resolve hardened Videha audit-queue sections into Scholar article records.

This expands the dedicated Scholar layer beyond the editor whitelist, while keeping
strict source-integrity guards:
- only article-level TOC entries with recoverable author/title/date/body;
- excludes fiction/poetry/editorial/news/interviews and ledger exclusions/holds;
- excludes section-3 poetry, short bodies, oversized legacy boundaries and malformed
  author/title pairs;
- never invents abstract, keywords, references, pages, date or authorship.

The hardened review catalogue is generated earlier in the workflow and is the
source of candidate issue/section pairs.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from extract_explicit_research import (
    SourceParser, article_body, body_to_html, parse_issue_date, parse_toc_entries,
    slugify, source_pdf,
)

APPROVED_CLASSES = {
    "research-explicit", "linguistics", "literary-history", "history",
    "folklore-ethnography", "culture-art", "criticism", "academic-review",
    "conference-seminar", "critical-edition", "references-present",
}
NEGATIVE_TITLE = [
    "कथा", "कहानी", "लघुकथा", "उपन्यास", "नाटक", "प्रहसन", "कविता", "गजल",
    "हाइकू", "गीत", "पद्य", "साक्षात्कार", "भेंटवार्ता", "समाचार", "घोषणा",
    "सम्पादकीय", "संपादकीय", "व्यंग्य", "हास्य", "प्रश्नोत्तरी", "quiz", "ई-लर्निङ्ग",
]
ROOT = Path(__file__).resolve().parents[1]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def decision_map() -> dict[tuple[str, str], str]:
    p = ROOT / "scholar-data" / "review-decisions.json"
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    out = {}
    for d in data.get("decisions", []):
        issue = str(int(str(d.get("issue") or "0")))
        section = str(d.get("section") or "").strip()
        if section:
            out[(issue, section)] = str(d.get("decision") or "").lower()
    return out


def already_promoted() -> set[tuple[str, str]]:
    p = ROOT / "scholar-data" / "promoted-sections.json"
    if not p.exists():
        return set()
    specs = json.loads(p.read_text(encoding="utf-8"))
    return {(str(int(str(x.get("issue") or "0"))), str(x.get("section") or "").strip()) for x in specs}


def issue_path(issue: str) -> Path | None:
    docs = ROOT / "search-documents"
    for name in (f"videha-{int(issue):03d}.html", f"videha-{int(issue)}.html", f"videha-{int(issue)}.htm"):
        p = docs / name
        if p.exists():
            return p
    return None


def sane_author(author: str) -> bool:
    author = norm(author)
    if not author or len(author) > 120 or len(author.split()) > 14:
        return False
    if re.search(r"[।!?]", author):
        return False
    if any(x in author.lower() for x in ("पृष्ठ", "पृ.", "http", "www.")):
        return False
    return True


def sane_title(title: str) -> bool:
    title = norm(title)
    if len(title) < 5 or len(title) > 420:
        return False
    low = title.lower()
    if any(x.lower() in low for x in NEGATIVE_TITLE):
        return False
    if "शोध पत्रिका" in low or "शोध-पत्रिका" in low:
        return False
    return True


def classification_label(cls: str) -> str:
    labels = {
        "research-explicit": "Research article",
        "linguistics": "Linguistics article",
        "literary-history": "Literary history article",
        "history": "History / cultural history article",
        "folklore-ethnography": "Folklore / ethnography article",
        "culture-art": "Culture / art studies article",
        "criticism": "Literary criticism article",
        "academic-review": "Academic review essay",
        "conference-seminar": "Conference / seminar paper",
        "critical-edition": "Critical-edition study",
        "references-present": "Referenced scholarly article",
    }
    return labels.get(cls.split("+")[0], "Scholarly article")


def load_audit_records() -> tuple[list[dict], list[dict]]:
    cat = ROOT / "research" / "data" / "section-candidates.json"
    if not cat.exists():
        return [], [{"reason": "hardened section catalogue missing"}]
    rows = json.loads(cat.read_text(encoding="utf-8")).get("rows", [])
    decisions = decision_map()
    promoted = already_promoted()
    records, review = [], []

    for row in rows:
        issue = str(int(str(row.get("issue") or "0")))
        section = str(row.get("section") or "").strip()
        key = (issue, section)
        if not section or key in promoted:
            continue
        decision = decisions.get(key, "")
        if decision.startswith("exclude") or decision == "hold":
            review.append({"issue": issue, "section": section, "reason": f"review ledger: {decision}"})
            continue
        if section.startswith("3."):
            continue
        status = str(row.get("status") or "")
        if status == "excluded":
            continue
        negatives = set(row.get("negative_signals") or [])
        if negatives & {"short-body", "insufficient-body-for-high-confidence", "legacy-boundary-oversize", "explicit-non-scholar-title"}:
            review.append({"issue": issue, "section": section, "reason": ", ".join(sorted(negatives))})
            continue
        cls = str(row.get("content_class") or "other")
        base_cls = cls.split("+")[0]
        if base_cls not in APPROVED_CLASSES and cls not in APPROVED_CLASSES:
            continue
        author, title = norm(str(row.get("author") or "")), norm(str(row.get("title") or ""))
        if not sane_author(author) or not sane_title(title):
            review.append({"issue": issue, "section": section, "author": author, "title": title, "reason": "malformed author/title"})
            continue
        path = issue_path(issue)
        if not path:
            review.append({"issue": issue, "section": section, "reason": "issue source not found"})
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        parser = SourceParser()
        try:
            parser.feed(raw)
        except Exception:
            pass
        text = parser.text()
        toc, floor = parse_toc_entries(text)
        idx = next((i for i, x in enumerate(toc) if x.get("section") == section), None)
        if idx is None:
            review.append({"issue": issue, "section": section, "reason": "section not resolved in source TOC"})
            continue
        item = toc[idx]
        # Use source-parsed metadata rather than catalogue copies.
        src_author, src_title = norm(str(item.get("author") or "")), norm(str(item.get("title") or ""))
        if not sane_author(src_author) or not sane_title(src_title):
            review.append({"issue": issue, "section": section, "reason": "source author/title failed integrity guard"})
            continue
        body = article_body(text, toc, idx, floor)
        compact = len(re.sub(r"\s+", "", body))
        if compact < 1800 or compact > 180000:
            review.append({"issue": issue, "section": section, "body_chars": compact, "reason": "body outside 1800–180000 character safe range"})
            continue
        date = parse_issue_date(text, issue)
        if not date:
            review.append({"issue": issue, "section": section, "reason": "publication date not recovered"})
            continue
        records.append({
            "title": src_title,
            "authors": [src_author],
            "publication_date": date,
            "year": date[:4],
            "issue": issue,
            "classification": classification_label(base_cls),
            "language": "mai",
            "slug": slugify(src_title),
            "page_start": item.get("page_start"),
            "page_end": item.get("page_end"),
            "source_url": source_pdf(parser, issue),
            "full_text_html": body_to_html(body),
            "_auto_source": path.relative_to(ROOT).as_posix(),
            "_auto_section": section,
            "_promotion": "hardened audit-queue publication",
        })
    return records, review


if __name__ == "__main__":
    r, q = load_audit_records()
    print(json.dumps({"publishable": len(r), "held": len(q), "records": r, "review": q}, ensure_ascii=False, indent=2))
