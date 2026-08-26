#!/usr/bin/env python3
"""Harden Videha Scholar section-candidate statuses after catalogue generation.

This is deliberately conservative. It never auto-publishes a section. It only
prevents false high-confidence rankings caused by legacy boundary spillover,
non-scholarly genres, incidental academic words, or ambiguous author/title splits.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "research" / "data" / "section-candidates.json"

NON_SCHOLARLY_TITLE = [
    "व्यंग्य", "हास्य", "परिहास", "कथा", "कहानी", "लघुकथा", "उपन्यास",
    "नाटक", "प्रहसन", "कविता", "गजल", "गीत", "साक्षात्कार", "भेंटवार्ता",
    "सम्पादकीय", "संपादकीय", "श्रद्धांजलि", "संस्मरण",
]
ANALYTICAL_TITLE = [
    "शोध", "अध्ययन", "विश्लेषण", "विमर्श", "आलोचना", "समालोचना",
    "इतिहास", "ऐतिहासिक", "भाषाविज्ञान", "भाषाशास्त्र", "व्याकरण",
    "research", "study", "analysis", "history", "linguistic", "phonology",
]
REFERENCE_SIGNALS = {"सन्दर्भ", "संदर्भ", "ग्रन्थसूची", "ग्रंथसूची", "bibliography", "references", "works cited"}
PRIMARY_CLASSES = {"research-article", "linguistics", "history", "ethnography-folklore"}
SECONDARY_CLASSES = {"culture-art", "literary-criticism", "academic-review", "conference-seminar", "critical-edition"}


def has_any(text: str, terms: list[str]) -> bool:
    low = (text or "").lower()
    return any(t.lower() in low for t in terms)


def add_negative(row: dict, value: str) -> None:
    vals = list(row.get("negative_signals") or [])
    if value not in vals:
        vals.append(value)
    row["negative_signals"] = sorted(vals)


def main() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    rows = data.get("rows", [])

    for row in rows:
        if row.get("status") == "scan-error":
            continue
        title = str(row.get("title") or "")
        author = str(row.get("author") or "")
        cls = str(row.get("content_class") or "other")
        body_chars = int(row.get("body_chars") or 0)
        page_start = str(row.get("page_start") or "").strip()
        signals = set(row.get("signals") or [])

        if has_any(title, NON_SCHOLARLY_TITLE):
            add_negative(row, "non-scholarly-title")
            row["status"] = "exclude"
            continue

        if not page_start and body_chars > 120000:
            add_negative(row, "legacy-boundary-oversize")
            row["status"] = "review"

        if author.endswith(":") or ("विशेष" in author and len(author.split()) <= 5):
            add_negative(row, "author-title-split-ambiguous")
            row["status"] = "review"

        if body_chars < 1800:
            add_negative(row, "insufficient-body-for-high-confidence")
            if row.get("status") != "exclude":
                row["status"] = "review"
            continue

        # Recompute high-confidence conservatively. Primary scholarly title classes
        # can qualify from a strong title + substantial body. Secondary classes
        # additionally need an analytical title and a reference signal.
        negatives = set(row.get("negative_signals") or [])
        if negatives:
            if row.get("status") != "exclude":
                row["status"] = "review"
            continue

        if cls in PRIMARY_CLASSES and has_any(title, ANALYTICAL_TITLE):
            row["status"] = "high-confidence-review"
        elif cls in SECONDARY_CLASSES and has_any(title, ANALYTICAL_TITLE) and bool(signals & REFERENCE_SIGNALS):
            row["status"] = "high-confidence-review"
        else:
            row["status"] = "review"

    data["candidate_sections"] = sum(1 for r in rows if r.get("status") not in {"scan-error", "exclude"})
    data["high_confidence_review"] = sum(1 for r in rows if r.get("status") == "high-confidence-review")
    data["excluded_by_hardening"] = sum(1 for r in rows if r.get("status") == "exclude")
    data["legacy_boundary_oversize"] = sum(
        1 for r in rows if "legacy-boundary-oversize" in (r.get("negative_signals") or [])
    )
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        "Videha section catalogue QA: "
        f"{data['candidate_sections']} reviewable; "
        f"{data['high_confidence_review']} high-confidence; "
        f"{data['excluded_by_hardening']} excluded; "
        f"{data['legacy_boundary_oversize']} legacy oversize boundaries flagged"
    )


if __name__ == "__main__":
    main()
