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
from extract_audit_sections import load_audit_records
from extract_top_level_audit import load_top_level_records

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
DATA = RESEARCH / "data"


def norm_title(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip().lower()
    return re.sub(r"[\s\-–—:;,.()\[\]'\"’‘“”]+", "", s)


def record_key(rec: dict) -> tuple[str, str]:
    return str(rec.get("issue") or ""), norm_title(str(rec.get("title") or ""))


def is_false_explicit_label(title: str) -> bool:
    return bool(re.search(r"शोध\s*[-–—]?\s*पत्रिका", title or "", re.I))


def clean_generated_article_pages() -> int:
    removed = 0
    for path in RESEARCH.glob("[0-9][0-9][0-9][0-9]/*/*.htm"):
        if path.is_file():
            path.unlink()
            removed += 1
    return removed


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    candidates = base.scan_legacy()
    raw_auto_records, explicit_review, extraction_summary = extract_explicit_records(ROOT)
    false_explicit = [r for r in raw_auto_records if is_false_explicit_label(str(r.get("title") or ""))]
    auto_records = [r for r in raw_auto_records if not is_false_explicit_label(str(r.get("title") or ""))]
    audit_records, audit_review = load_audit_records()
    top_records, top_review = load_top_level_records()
    promoted_records, promotion_review = load_promoted(ROOT)
    curated = base.load_curated()

    # Merge priority: explicit -> resolved audit queues -> editor whitelist -> curated.
    merged: dict[tuple[str, str], dict] = {}
    for layer in (auto_records, audit_records, top_records, promoted_records, curated):
        for rec in layer:
            merged[record_key(rec)] = rec

    stale_pages_removed = clean_generated_article_pages()
    articles, build_errors = [], []
    for rec in sorted(merged.values(), key=lambda r: (str(r.get("publication_date") or ""), str(r.get("issue") or ""), str(r.get("title") or ""))):
        try:
            articles.append(base.render_article(rec))
        except Exception as exc:
            build_errors.append({
                "manifest": rec.get("_manifest"), "auto_source": rec.get("_auto_source"),
                "issue": rec.get("issue"), "title": rec.get("title"), "error": str(exc),
            })

    extraction_summary.update({
        "explicit_articles_detected_raw": len(raw_auto_records),
        "explicit_false_positive_filtered": len(false_explicit),
        "explicit_articles_publishable": len(auto_records),
        "audit_queue_publishable": len(audit_records),
        "audit_queue_held": len(audit_review),
        "top_level_audit_publishable": len(top_records),
        "top_level_audit_held": len(top_review),
        "promoted_sections_requested": len(promoted_records) + len(promotion_review),
        "promoted_sections_publishable": len(promoted_records),
        "promoted_sections_review": len(promotion_review),
        "curated_manifests": len(curated),
        "published_after_all_overrides": len(articles),
        "stale_generated_pages_removed_before_render": stale_pages_removed,
        "build_errors": len(build_errors),
    })

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
        "audit_review": audit_review,
        "top_level_review": top_review,
        "promotion_review": promotion_review,
        "build_errors": build_errors,
    }
    (DATA / "explicit-research-review.json").write_text(json.dumps(review_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    payload = {
        "journal": base.CFG["journal_title"], "issn": base.CFG["issn"],
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "extraction_summary": extraction_summary, "articles": articles, "candidates": candidates,
    }
    (DATA / "articles.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    base.write_index(articles, candidates)
    base.write_sitemap(articles)

    print(
        "Videha Scholar full-corpus build: "
        f"{extraction_summary['issue_files_scanned']} issues; {len(articles)} published HTML articles; "
        f"{len(audit_records)} section-audit pages; {len(top_records)} top-level-audit pages; "
        f"{len(audit_review) + len(top_review)} audit items held by integrity guards; "
        f"{len(promoted_records)} editor-approved sections; {len(build_errors)} build errors"
    )


if __name__ == "__main__":
    main()
