#!/usr/bin/env python3
"""Resolve Sadeha-discovered originals into canonical Videha Scholar records."""
from __future__ import annotations

import json
import re
from pathlib import Path

from extract_explicit_research import (
    SourceParser, article_body, body_to_html, parse_issue_date, parse_toc_entries,
    slugify, source_pdf,
)
from extract_audit_sections import issue_path, sane_author, sane_title, classification_label

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "research" / "data" / "sadeha-crossmap.json"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def load_sadeha_records() -> tuple[list[dict], list[dict]]:
    if not MAP.exists():
        return [], [{"reason": "Sadeha cross-map missing"}]
    rows = json.loads(MAP.read_text(encoding="utf-8")).get("publishable", [])
    records, review = [], []
    for row in rows:
        issue = str(row.get("issue") or "")
        section = str(row.get("section") or "")
        path = issue_path(issue)
        if not path:
            review.append({"issue": issue, "section": section, "reason": "original Videha source not found"})
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        parser = SourceParser()
        try:
            parser.feed(raw)
        except Exception:
            pass
        text = parser.text()
        toc, floor = parse_toc_entries(text)
        idx = next((i for i, x in enumerate(toc) if str(x.get("section") or "") == section), None)
        if idx is None:
            review.append({"issue": issue, "section": section, "reason": "original section not resolved"})
            continue
        item = toc[idx]
        author = norm(str(item.get("author") or ""))
        title = norm(str(item.get("title") or ""))
        if not sane_author(author) or not sane_title(title):
            review.append({"issue": issue, "section": section, "reason": "source author/title failed integrity guard"})
            continue
        body = article_body(text, toc, idx, floor)
        compact = len(re.sub(r"\s+", "", body))
        if compact < 1800 or compact > 180000:
            review.append({"issue": issue, "section": section, "body_chars": compact, "reason": "body outside safe range"})
            continue
        date = parse_issue_date(text, issue)
        if not date:
            review.append({"issue": issue, "section": section, "reason": "publication date not recovered"})
            continue
        cls = str(row.get("classification") or "references-present").split("+")[0]
        records.append({
            "title": title,
            "authors": [author],
            "publication_date": date,
            "year": date[:4],
            "issue": issue,
            "classification": classification_label(cls),
            "language": "mai",
            "slug": slugify(title),
            "page_start": item.get("page_start"),
            "page_end": item.get("page_end"),
            "source_url": source_pdf(parser, issue),
            "full_text_html": body_to_html(body),
            "_auto_source": path.relative_to(ROOT).as_posix(),
            "_auto_section": section,
            "_promotion": "Sadeha rediscovery of original Videha scholarly article",
            "_sadeha_evidence": row.get("sadeha_source"),
        })
    return records, review


if __name__ == "__main__":
    r, q = load_sadeha_records()
    print(json.dumps({"publishable": len(r), "held": len(q), "records": r, "review": q}, ensure_ascii=False, indent=2))
