#!/usr/bin/env python3
"""Extract editor-approved retrospective Videha sections into Scholar records.

The whitelists in scholar-data/promoted-sections.json and
scholar-data/sadeha-promoted-sections.json are editorially controlled. This module
never guesses promotions: it only resolves those exact issue/section pairs, and it
rejects records whose source metadata/body cannot be recovered. Sadeha remains
*discovery evidence* only; rendered citation identity always comes from the original
Videha issue.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from extract_explicit_research import (
    SourceParser,
    article_body,
    body_to_html,
    parse_issue_date,
    parse_toc_entries,
    slugify,
    source_pdf,
)


def _issue_path(root: Path, issue: str) -> Path | None:
    docs = root / "search-documents"
    for name in (f"videha-{int(issue):03d}.html", f"videha-{int(issue)}.html", f"videha-{int(issue)}.htm"):
        p = docs / name
        if p.exists():
            return p
    return None


def _load_specs(root: Path) -> list[dict]:
    specs: list[dict] = []
    for filename, source in (
        ("promoted-sections.json", "editor-approved retrospective section"),
        ("sadeha-promoted-sections.json", "editor-approved Sadeha rediscovery"),
    ):
        path = root / "scholar-data" / filename
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        for row in data:
            if isinstance(row, dict):
                rec = dict(row)
                rec["_promotion_source"] = source
                specs.append(rec)
    return specs


def load_promoted(root: Path) -> tuple[list[dict], list[dict]]:
    specs = _load_specs(root)
    records: list[dict] = []
    review: list[dict] = []

    for spec in specs:
        issue = str(int(str(spec.get("issue") or "0")))
        section = str(spec.get("section") or "").strip()
        classification = str(spec.get("classification") or "Scholarly article").strip()
        try:
            min_body_chars = int(spec.get("min_body_chars", 1800))
        except (TypeError, ValueError):
            min_body_chars = 1800
        min_body_chars = max(1, min_body_chars)

        path = _issue_path(root, issue)
        if not path:
            review.append({"issue": issue, "section": section, "reason": "issue file not found"})
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
            review.append({"issue": issue, "section": section, "reason": "section not found in issue TOC"})
            continue

        item = toc[idx]
        author_override = str(spec.get("author_override") or "").strip()
        title_override = str(spec.get("title_override") or "").strip()
        author = author_override or item.get("author")
        title = title_override or item.get("title")
        if not author or not title:
            review.append({"issue": issue, "section": section, "reason": "author/title could not be recovered"})
            continue

        body = article_body(text, toc, idx, floor)
        compact = len(re.sub(r"\s+", "", body))
        if compact < min_body_chars:
            review.append({
                "issue": issue,
                "section": section,
                "author": author,
                "title": title,
                "body_chars": compact,
                "min_body_chars": min_body_chars,
                "reason": f"body below {min_body_chars}-character publication threshold",
            })
            continue

        date = parse_issue_date(text, issue)
        if not date:
            review.append({"issue": issue, "section": section, "reason": "publication date not recovered"})
            continue

        records.append({
            "title": title,
            "authors": [author],
            "publication_date": date,
            "year": date[:4],
            "issue": issue,
            "classification": classification,
            "language": "mai",
            "slug": slugify(title),
            "page_start": item.get("page_start"),
            "page_end": item.get("page_end"),
            "source_url": source_pdf(parser, issue),
            "full_text_html": body_to_html(body),
            "_auto_source": path.relative_to(root).as_posix(),
            "_auto_section": section,
            "_promotion": spec.get("_promotion_source") or "editor-approved retrospective section",
            "_sadeha_evidence": spec.get("sadeha_evidence"),
            "_metadata_override": bool(author_override or title_override),
        })

    return records, review


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parents[1]
    records, review = load_promoted(ROOT)
    print(json.dumps({"published": records, "review": review}, ensure_ascii=False, indent=2))
