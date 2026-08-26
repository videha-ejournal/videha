#!/usr/bin/env python3
"""Build Videha Scholar layer from curated records plus safe corpus-wide extraction."""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

import build_research as base
from extract_explicit_research import extract_explicit_records

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
DATA = RESEARCH / "data"


def norm_title(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip().lower()
    return re.sub(r"[\s\-–—:;,.()\[\]'\"’‘“”]+", "", s)


def record_key(rec: dict) -> tuple[str, str]:
    return str(rec.get("issue") or ""), norm_title(str(rec.get("title") or ""))


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)

    candidates = base.scan_legacy()
    auto_records, review, extraction_summary = extract_explicit_records(ROOT)
    curated = base.load_curated()

    # Start with deterministic corpus extraction; hand-curated manifests override
    # an auto record with the same issue/title so editorial corrections always win.
    merged: dict[tuple[str, str], dict] = {}
    for rec in auto_records:
        merged[record_key(rec)] = rec
    for rec in curated:
        merged[record_key(rec)] = rec

    articles = []
    build_errors = []
    for rec in sorted(merged.values(), key=lambda r: (str(r.get("publication_date") or ""), str(r.get("issue") or ""), str(r.get("title") or ""))):
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

    extraction_summary["curated_manifests"] = len(curated)
    extraction_summary["published_after_curated_override"] = len(articles)
    extraction_summary["build_errors"] = len(build_errors)

    review_payload = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "summary": extraction_summary,
        "review": review,
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
        f"{len(review)} explicit items held for review; "
        f"{len(candidates)} broader retrospective candidates"
    )
    if build_errors:
        print(f"WARNING: {len(build_errors)} records failed rendering; see research/data/explicit-research-review.json")


if __name__ == "__main__":
    main()
