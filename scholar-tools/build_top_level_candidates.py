#!/usr/bin/env python3
"""Discover scholarly-looking legacy top-level Videha sections for review only.

Some older issues place substantial scholarly material under top-level labels such
as "8. ..." instead of ordinary x.y article entries. These records must not be
lost, but their author/title order and body boundaries are too heterogeneous for
automatic Scholar publication. This script therefore creates a discovery queue
only; it never creates article pages.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from extract_explicit_research import SourceParser, issue_files, parse_issue_date, source_pdf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "data" / "top-level-section-candidates.json"
DEV = str.maketrans("०१२३४५६७८९", "0123456789")
TOP_RE = re.compile(r"(?m)^\s*([1-9१-९])\.\s*(.+?)\s*$")
TERMS = [
    "शोध", "अनुसन्धान", "अनुसंधान", "भाषाविज्ञान", "भाषा विज्ञान", "भाषाशास्त्र",
    "व्याकरण", "ध्वनिविमर्श", "ध्वनिविज्ञान", "इतिहास", "ऐतिहासिक", "पञ्जी", "पंजी",
    "नृविज्ञान", "नृवंश", "लोक साहित्य", "लोक-साहित्य", "लोकसंस्कृति", "लोक-संस्कृति",
    "मिथिला चित्रकला", "समीक्षा आलेख", "आलोचना", "समालोचना", "critical edition",
    "research", "linguistic", "phonology", "morphology", "syntax", "history", "ethnography",
    "folklore", "bibliography", "references",
]
GENERIC = {
    "गद्य", "पद्य", "संपादकीय", "सम्पादकीय", "मिथिला कला-संगीत", "बालानां कृते",
    "गद्य-पद्य भारती", "अनुक्रम",
}


def matched(label: str) -> list[str]:
    low = label.lower()
    return sorted({t for t in TERMS if t.lower() in low})


def main() -> None:
    rows = []
    files = issue_files(ROOT / "search-documents")
    for path in files:
        m = re.search(r"videha-(\d{1,4})\.html?$", path.name, re.I)
        if not m:
            continue
        issue = str(int(m.group(1)))
        raw = path.read_text(encoding="utf-8", errors="ignore")
        parser = SourceParser()
        try:
            parser.feed(raw)
        except Exception:
            pass
        text = parser.text()
        marker = text.find("ऐ अंकमे अछि")
        if marker < 0:
            marker = text.find("अनुक्रम")
        marker = max(marker, 0)
        # TOCs occur near the front. Limiting the discovery window avoids treating
        # numbered headings deep inside article bodies as issue-level sections.
        window = text[marker:min(len(text), marker + 50000)]
        seen = set()
        for mt in TOP_RE.finditer(window):
            sec = mt.group(1).translate(DEV)
            label = re.sub(r"\s+", " ", mt.group(2)).strip()
            if not label or label in GENERIC:
                continue
            signals = matched(label)
            if not signals:
                continue
            key = (sec, label)
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "issue": issue,
                "publication_date": parse_issue_date(text, issue),
                "section": sec,
                "label": label,
                "signals": signals,
                "status": "manual-boundary-review",
                "reason": "Top-level legacy section: author/title ordering and article boundary require manual validation before any Scholar publication.",
                "source_path": path.relative_to(ROOT).as_posix(),
                "source_url": source_pdf(parser, issue),
            })
    rows.sort(key=lambda r: (int(r["issue"]), int(r["section"]), r["label"]))
    payload = {
        "issue_files_scanned": len(files),
        "top_level_scholarly_candidates": len(rows),
        "publication_policy": "review-only; never auto-published",
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Videha top-level scholarly discovery: {len(files)} issues scanned; {len(rows)} review-only candidates")


if __name__ == "__main__":
    main()
