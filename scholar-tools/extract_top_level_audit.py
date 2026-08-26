#!/usr/bin/env python3
"""Resolve legacy top-level Videha scholarly audit rows into article records.

Top-level legacy TOCs are heterogeneous. This resolver publishes only when:
- a non-generic scholarly label is present;
- author/title are explicit in the label or in the immediate body heading;
- a bounded body between this heading and the next top-level heading is recoverable;
- body length and metadata pass integrity guards.
Anything else stays in the hold report. No authorship is inferred across issues.
"""
from __future__ import annotations

import html as htmlmod
import json
import re
from pathlib import Path

from extract_explicit_research import SourceParser, body_to_html, parse_issue_date, slugify, source_pdf

ROOT = Path(__file__).resolve().parents[1]
DEV = str.maketrans("०१२३४५६७८९", "0123456789")
GENERIC = re.compile(r"^\s*(?:शोध\s*लेख|आलोचना|समालोचना|इतिहास|समीक्षा)\s*[:.]?\s*$", re.I)
NEGATIVE = ["कथा", "कहानी", "उपन्यास", "नाटक", "प्रहसन", "कविता", "गजल", "गीत", "व्यंग्य", "साक्षात्कार", "समाचार", "सम्पादकीय", "संपादकीय"]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", htmlmod.unescape(s or "")).strip()


def issue_path(issue: str) -> Path | None:
    docs = ROOT / "search-documents"
    for name in (f"videha-{int(issue):03d}.html", f"videha-{int(issue)}.html", f"videha-{int(issue)}.htm"):
        p = docs / name
        if p.exists():
            return p
    return None


def split_author_title(label: str) -> tuple[str | None, str | None]:
    label = norm(label)
    # Strip leading category marker without treating it as author.
    label = re.sub(r"^(?:शोध\s*लेख|शोध\s*आलेख|आलोचना|समालोचना|समीक्षा)\s*[:.-]\s*", "", label, flags=re.I)
    for sep in (" - ", "-", "–", "—"):
        if sep in label:
            left, right = [norm(x) for x in label.split(sep, 1)]
            if 2 <= len(left) <= 100 and 5 <= len(right) <= 420 and len(left.split()) <= 14:
                if not re.search(r"[।!?]", left):
                    return left, right
    return None, None


def sane_author(s: str | None) -> bool:
    if not s:
        return False
    s = norm(s)
    return 2 <= len(s) <= 100 and len(s.split()) <= 14 and not re.search(r"[।!?]", s)


def sane_title(s: str | None) -> bool:
    if not s:
        return False
    s = norm(s)
    if len(s) < 5 or len(s) > 420:
        return False
    low = s.lower()
    return not any(x.lower() in low for x in NEGATIVE)


def body_segment(text: str, section: str, label: str) -> tuple[str, int] | None:
    sec_pat = re.escape(section)
    # Find exact/sufficient label occurrences; the last viable occurrence is normally body.
    label_key = norm(label)[:80]
    starts = []
    for m in re.finditer(rf"(?m)^\s*{sec_pat}\s*\.\s*(.+?)\s*$", text):
        line = norm(m.group(1))
        if label_key and (label_key in line or line[:80] in label_key):
            starts.append(m)
    if not starts:
        # Some body headings omit the numeric prefix; use exact label occurrence after the TOC.
        for m in re.finditer(re.escape(norm(label)), text):
            starts.append(m)
    if not starts:
        return None
    top_re = re.compile(r"(?m)^\s*[1-9१-९]\s*\.\s+.+$")
    best = None
    for m in starts:
        start = m.end()
        nxt = top_re.search(text, start)
        end = nxt.start() if nxt else len(text)
        seg = text[start:end].strip()
        compact = len(re.sub(r"\s+", "", seg))
        if 1800 <= compact <= 180000:
            if best is None or compact > best[1]:
                best = (seg, compact)
    return best


def immediate_byline(body: str, label: str) -> tuple[str | None, str | None]:
    lines = [norm(x) for x in body.splitlines() if norm(x)][:12]
    cleaned_label = norm(label)
    # Common body pattern: author on one line, title on next/repeated line.
    for i, line in enumerate(lines[:8]):
        if sane_author(line):
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            if sane_title(next_line) and (next_line in cleaned_label or cleaned_label in next_line or len(next_line) > 15):
                return line, next_line
    return None, None


def class_label(signals: list[str]) -> str:
    s = " ".join(signals).lower()
    if "भाष" in s or "lingu" in s or "phon" in s or "व्याकरण" in s:
        return "Linguistics article"
    if "इतिहास" in s or "history" in s or "पञ्जी" in s or "पंजी" in s:
        return "History / cultural history article"
    if "लोक" in s or "ethn" in s or "folklore" in s:
        return "Folklore / ethnography article"
    if "आलोचना" in s or "समालोचना" in s or "critical" in s:
        return "Literary criticism article"
    if "शोध" in s or "research" in s:
        return "Research article"
    return "Scholarly article"


def load_top_level_records() -> tuple[list[dict], list[dict]]:
    p = ROOT / "research" / "data" / "top-level-section-candidates.json"
    if not p.exists():
        return [], [{"reason": "top-level audit catalogue missing"}]
    rows = json.loads(p.read_text(encoding="utf-8")).get("rows", [])
    records, review = [], []
    seen = set()
    for row in rows:
        issue = str(int(str(row.get("issue") or "0")))
        section = str(row.get("section") or "").translate(DEV).strip()
        label = norm(str(row.get("label") or ""))
        if not label or GENERIC.match(label) or len(label) > 420:
            continue
        low = label.lower()
        if any(x.lower() in low for x in NEGATIVE):
            continue
        key = (issue, section, label)
        if key in seen:
            continue
        seen.add(key)
        path = issue_path(issue)
        if not path:
            review.append({"issue": issue, "section": section, "label": label, "reason": "issue source missing"})
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        parser = SourceParser()
        try:
            parser.feed(raw)
        except Exception:
            pass
        text = parser.text()
        resolved = body_segment(text, section, label)
        if not resolved:
            review.append({"issue": issue, "section": section, "label": label, "reason": "bounded body not recovered"})
            continue
        body, compact = resolved
        author, title = split_author_title(label)
        if not sane_author(author) or not sane_title(title):
            body_author, body_title = immediate_byline(body, label)
            author = author if sane_author(author) else body_author
            title = title if sane_title(title) else body_title
        if not sane_author(author) or not sane_title(title):
            review.append({"issue": issue, "section": section, "label": label, "body_chars": compact, "reason": "explicit author/title not recoverable"})
            continue
        date = parse_issue_date(text, issue)
        if not date:
            review.append({"issue": issue, "section": section, "label": label, "reason": "publication date not recovered"})
            continue
        rec_key = (issue, norm(title).lower())
        if rec_key in {(r["issue"], norm(r["title"]).lower()) for r in records}:
            continue
        records.append({
            "title": norm(title),
            "authors": [norm(author)],
            "publication_date": date,
            "year": date[:4],
            "issue": issue,
            "classification": class_label(list(row.get("signals") or [])),
            "language": "mai",
            "slug": slugify(norm(title)),
            "page_start": None,
            "page_end": None,
            "source_url": source_pdf(parser, issue),
            "full_text_html": body_to_html(body),
            "_auto_source": path.relative_to(ROOT).as_posix(),
            "_auto_section": section,
            "_promotion": "resolved legacy top-level audit publication",
        })
    return records, review


if __name__ == "__main__":
    r, q = load_top_level_records()
    print(json.dumps({"publishable": len(r), "held": len(q), "records": r, "review": q}, ensure_ascii=False, indent=2))
