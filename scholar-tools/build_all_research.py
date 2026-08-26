#!/usr/bin/env python3
"""Build Videha Scholar layer from curated records plus safe corpus-wide extraction."""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

import build_research as base
from extract_explicit_research import extract_explicit_records
from extract_promoted_sections import load_promoted

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
DATA = RESEARCH / "data"


def norm_title(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip().lower()
    return re.sub(r"[\s\-–—:;,.()\[\]'\"’‘“”]+", "", s)


def record_key(rec: dict) -> tuple[str, str]:
    return str(rec.get("issue") or ""), norm_title(str(rec.get("title") or ""))


def is_false_explicit_label(title: str) -> bool:
    """Reject substring collisions such as 'शोध पत्रिका' ≠ 'शोध पत्र'."""
    return bool(re.search(r"शोध\s*[-–—]?\s*पत्रिका", title or "", re.I))


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)

    candidates = base.scan_legacy()
    raw_auto_records, explicit_review, extraction_summary = extract_explicit_records(ROOT)
    false_explicit = [r for r in raw_auto_records if is_false_explicit_label(str(r.get("title") or ""))]
    auto_records = [r for r in raw_auto_records if not is_false_explicit_label(str(r.get("title") or ""))]
    promoted_records, promotion_review = load_promoted(ROOT)
    curated = base.load_curated()

    # Deterministic explicit extraction is followed by an editor-controlled
    # retrospective whitelist. Hand-curated manifests always override either one.
    merged: dict[tuple[str, str], dict] = {}
    for rec in auto_records:
        merged[record_key(rec)] = rec
    for rec in promoted_records:
        merged[record_key(rec)] = rec
    for rec in curated:
        merged[record_key(rec)] = rec

    articles = []
    build_errors = []
    for rec in sorted(
        merged.values(),
        key=lambda r: (
            str(r.get("publication_date") or ""),
            str(r.get("issue") or ""),
            str(r.get("title") or ""),
        ),
    ):
        try:
            articles.append(base.render_article(rec))
        except Exception as exc:
            build_errors.append({
                "manifest": rec.get("_manifest"),
                "auto_source": rec.get("_auto_source"),
                "issue": rec.get("issue"),
                "title": rec.get("title"),
                "error": str(exc),
            })

    extraction_summary["explicit_articles_detected_raw"] = len(raw_auto_records)
    extraction_summary["explicit_false_positive_filtered"] = len(false_explicit)
    extraction_summary["explicit_articles_publishable"] = len(auto_records)
    extraction_summary["promoted_sections_requested"] = len(promoted_records) + len(promotion_review)
    extraction_summary["promoted_sections_publishable"] = len(promoted_records)
    extraction_summary["promoted_sections_review"] = len(promotion_review)
    extraction_summary["curated_manifests"] = len(curated)
    extraction_summary["published_after_all_overrides"] = len(articles)
    extraction_summary["build_errors"] = len(build_errors)

    false_explicit_review = []
    for rec in false_explicit:
        held = dict(rec)
        held["status"] = "review"
        held["reasons"] = ["automatic explicit-label false positive: title contains 'शोध पत्रिका', not an article-level 'शोध पत्र' label"]
        false_explicit_review.append(held)

    review_payload = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "summary": extraction_summary,
        "explicit_review": explicit_review + false_explicit_review,
        "promotion_review": promotion_review,
        "build_errors": build_errors,
    }
    (DATA / "explicit-research-review.json").write_text(
        json.dumps(review_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    payload = {
        "journal": base.CFG["journal_title"],
        "issn": base.CFG["issn"],
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "extraction_summary": extraction_summary,
        "articles": articles,
        "candidates": candidates,
    }
    (DATA / "articles.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    base.write_index(articles, candidates)
    base.write_sitemap(articles)

    print(
        "Videha Scholar full-corpus build: "
        f"{extraction_summary['issue_files_scanned']} issue HTML files scanned; "
        f"{len(articles)} published articles; "
        f"{len(explicit_review) + len(false_explicit_review)} explicit items held for review; "
        f"{len(promoted_records)} editor-approved retrospective sections resolved; "
        f"{len(promotion_review)} promoted sections held for review; "
        f"{len(candidates)} broader retrospective candidates"
    )
    if build_errors:
        print(f"WARNING: {len(build_errors)} records failed rendering; see research/data/explicit-research-review.json")


if __name__ == "__main__":
    main()
