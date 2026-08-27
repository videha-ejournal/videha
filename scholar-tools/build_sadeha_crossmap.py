#!/usr/bin/env python3
"""Deep-map every Sadeha search HTML source to original Videha article records.

Sadeha volumes are thematic/parallel compilations and often reprint Videha material.
This script treats all search-documents/sadeha-*.html files as discovery evidence,
not as competing citation identities. Exact/high-confidence author+title matches are
mapped back to the original Videha issue/section metadata.

For automatic Scholar publication, Sadeha evidence must confirm a *positive scholarly
class*. A generic body-only `references-present` signal is retained for review but is
never sufficient by itself; this prevents reportage, announcements, interviews and
creative prose with incidental reference words from becoming Scholar pages.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from extract_explicit_research import SourceParser
from extract_audit_sections import decision_map, sane_author, sane_title

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "data" / "sadeha-crossmap.json"
INV = ROOT / "research" / "data" / "article-inventory.json"
ARTICLES = ROOT / "research" / "data" / "articles.json"

PUNCT = re.compile(r"[\s\-–—:;,.()\[\]{}'\"’‘“”।!?/\\|]+")
SAFE_AUTO_CLASSES = {
    "research-explicit", "linguistics", "literary-history", "history",
    "folklore-ethnography", "culture-art", "criticism", "academic-review",
    "conference-seminar", "critical-edition",
}


def norm(s: str) -> str:
    return PUNCT.sub("", (s or "").lower())


def sadeha_files() -> list[Path]:
    return sorted((ROOT / "search-documents").glob("sadeha-*.html"))


def read_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    p = SourceParser()
    try:
        p.feed(raw)
    except Exception:
        pass
    return p.text()


def existing_keys() -> set[tuple[str, str]]:
    if not ARTICLES.exists():
        return set()
    data = json.loads(ARTICLES.read_text(encoding="utf-8"))
    return {(str(x.get("issue") or ""), norm(str(x.get("title") or ""))) for x in data.get("articles", [])}


def main() -> None:
    if not INV.exists():
        raise SystemExit("article-inventory.json missing; run build_article_inventory.py first")
    inv = json.loads(INV.read_text(encoding="utf-8")).get("rows", [])
    files = sadeha_files()
    if len(files) != 38:
        print(f"WARNING: expected 38 Sadeha HTML sources, found {len(files)}")

    docs = []
    for path in files:
        text = read_text(path)
        docs.append({"path": path.relative_to(ROOT).as_posix(), "chars": len(text), "norm": norm(text)})

    decisions = decision_map()
    published = existing_keys()
    matches = []
    matched_rows: set[tuple[str, str, str]] = set()

    candidates = []
    for row in inv:
        title = str(row.get("title") or "")
        author = str(row.get("author") or "")
        nt, na = norm(title), norm(author)
        if len(nt) < 12 or len(na) < 3 or not sane_author(author) or not sane_title(title):
            continue
        candidates.append((row, nt, na))

    for doc in docs:
        body = doc["norm"]
        for row, nt, na in candidates:
            pos = body.find(nt)
            if pos < 0:
                continue
            lo, hi = max(0, pos - 2500), min(len(body), pos + len(nt) + 2500)
            nearby = body[lo:hi]
            strength = "author-title" if na in nearby else "title-only"
            issue = str(row.get("issue") or "")
            section = str(row.get("section") or "")
            key = (issue, section, nt)
            if key in matched_rows and strength == "title-only":
                continue
            matched_rows.add(key)
            cls = str(row.get("classification") or "")
            base_cls = cls.split("+")[0]
            decision = decisions.get((issue, section), "")
            already = (issue, nt) in published
            base_integrity = (
                strength == "author-title"
                and bool(row.get("scholar_candidate"))
                and 1800 <= int(row.get("body_chars") or 0) <= 180000
                and not decision.startswith("exclude") and decision != "hold"
                and not already
            )
            publishable = base_integrity and base_cls in SAFE_AUTO_CLASSES
            reviewable = base_integrity and not publishable
            matches.append({
                "sadeha_source": doc["path"], "match_strength": strength,
                "issue": issue, "section": section, "author": row.get("author"),
                "title": row.get("title"), "classification": cls,
                "body_chars": row.get("body_chars"), "already_published": already,
                "review_decision": decision or None,
                "publishable_discovery": publishable,
                "reviewable_discovery": reviewable,
                "eligibility_note": (
                    "positive scholarly class confirmed by Sadeha author+title match"
                    if publishable else
                    "Sadeha match retained for editorial review; generic references-present signal alone is insufficient"
                    if reviewable else None
                ),
            })

    best: dict[tuple[str, str, str], dict] = {}
    for m in matches:
        k = (m["issue"], m["section"], norm(str(m["title"])))
        cur = best.get(k)
        if cur is None or (cur["match_strength"] == "title-only" and m["match_strength"] == "author-title"):
            best[k] = m
    uniq = sorted(best.values(), key=lambda x: (int(x["issue"] or 0), x["section"], str(x["title"])))
    publishable = [x for x in uniq if x["publishable_discovery"]]
    reviewable = [x for x in uniq if x.get("reviewable_discovery")]
    payload = {
        "sadeha_html_sources": len(files),
        "source_files": [{"path": d["path"], "text_chars": d["chars"]} for d in docs],
        "videha_inventory_rows_considered": len(inv),
        "unique_videha_articles_matched": len(uniq),
        "author_title_matches": sum(1 for x in uniq if x["match_strength"] == "author-title"),
        "title_only_matches": sum(1 for x in uniq if x["match_strength"] == "title-only"),
        "already_published_matches": sum(1 for x in uniq if x["already_published"]),
        "new_scholarly_discoveries_publishable": len(publishable),
        "new_matches_requiring_editorial_review": len(reviewable),
        "publishable": publishable,
        "reviewable": reviewable,
        "matches": uniq,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Sadeha deep map: {len(files)} HTML sources; {len(uniq)} unique Videha article matches; "
        f"{len(publishable)} positive-class Scholar discoveries; {len(reviewable)} review-only matches"
    )


if __name__ == "__main__":
    main()
