#!/usr/bin/env python3
"""Resolve legacy top-level Videha scholarly audit rows into article records.

Only explicit, name-like heading bylines are accepted. Ambiguous category labels,
serial headings without authors, composite multi-item headings, and dash collisions
remain in review. No author is inferred from surrounding issues or prose.
"""
from __future__ import annotations

import html as htmlmod
import json
import re
from pathlib import Path

from extract_explicit_research import SourceParser, body_to_html, parse_issue_date, slugify, source_pdf

ROOT = Path(__file__).resolve().parents[1]
DEV = str.maketrans("०१२३४५६७८९", "0123456789")
GENERIC = re.compile(r"^\s*(?:शोध\s*लेख|शोध\s*आलेख|आलोचना|समालोचना|इतिहास|समीक्षा)\s*[:.]?\s*$", re.I)
NEGATIVE = ["कथा", "कहानी", "उपन्यास", "नाटक", "प्रहसन", "कविता", "गजल", "गीत", "व्यंग्य", "साक्षात्कार", "समाचार", "सम्पादकीय", "संपादकीय"]
AUTHOR_BAD = [
    "इतिहास", "शोध", "पंजी", "पञ्जी", "प्रबंध", "भाषा", "मैथिली", "साहित्य",
    "संस्कृति", "समीक्षा", "आलोचना", "समालोचना", "बोध", "प्रयोग", "संहिता",
    "लेख", "अंक", "पृष्ठ", "पृ.", "संदर्भ", "सन्दर्भ", "वचन", "भाग", "शीर्षक",
    "केर", "क ", "आगाँ", "आँगा",
]
TITLE_SENTENCE_BAD = ["अहाँ", "हमरा", "हम ", "छी", "अछि", "रहल छी", "देखू", "कहलहुँ"]
LIST_MARKER = re.compile(r"(?:^|\s)[०-९0-9]{1,2}\s*[.)]\s*")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", htmlmod.unescape(s or "")).strip()


def issue_path(issue: str) -> Path | None:
    docs = ROOT / "search-documents"
    for name in (f"videha-{int(issue):03d}.html", f"videha-{int(issue)}.html", f"videha-{int(issue)}.htm"):
        p = docs / name
        if p.exists():
            return p
    return None


def clean_author(s: str) -> str:
    s = norm(s)
    s = re.sub(r"^[०-९0-9]+\s*[.)-]?\s*", "", s)
    return s.strip(" :-–—")


def sane_author(s: str | None) -> bool:
    if not s:
        return False
    s = clean_author(s)
    words = s.split()
    if len(s) < 3 or len(s) > 90 or len(words) < 2 or len(words) > 10:
        return False
    low = s.lower()
    if any(x.lower() in low for x in AUTHOR_BAD):
        return False
    if re.search(r"[।!?/\\]", s) or re.search(r"https?://|www\.", low):
        return False
    if len(re.findall(r"[,;:]", s)) > 1:
        return False
    return True


def sane_title(s: str | None) -> bool:
    if not s:
        return False
    s = norm(s)
    if len(s) < 5 or len(s) > 240:
        return False
    low = s.lower()
    if any(x.lower() in low for x in NEGATIVE):
        return False
    if any(x.lower() in low for x in TITLE_SENTENCE_BAD) and len(s) > 80:
        return False
    # Old TOCs sometimes concatenate several entries into one line. Reject titles
    # containing two or more numbered list markers rather than publishing a bundle.
    if len(LIST_MARKER.findall(s)) >= 2:
        return False
    # Also reject embedded second-item markers common in OCR-joined headings.
    if re.search(r"(?:^|\s)[२2]\s*[.)]\s*", s) and re.search(r"(?:^|\s)[१1]\s*[.)]\s*", s):
        return False
    return True


def split_author_title(label: str) -> tuple[str | None, str | None]:
    label = norm(label)
    label = re.sub(r"^(?:शोध\s*लेख|शोध\s*आलेख|आलोचना|समालोचना|समीक्षा)\s*[:.-]\s*", "", label, flags=re.I)
    candidates = []
    for pat in (r"\s+[–—-]\s+", r"-"):
        m = re.search(pat, label)
        if m:
            candidates.append((label[:m.start()], label[m.end():]))
    for left, right in candidates:
        left, right = clean_author(left), norm(right)
        if sane_author(left) and sane_title(right):
            return left, right
    return None, None


def body_segment(text: str, section: str, label: str) -> tuple[str, int] | None:
    sec_pat = re.escape(section)
    label_key = norm(label)[:80]
    starts = []
    for m in re.finditer(rf"(?m)^\s*{sec_pat}\s*\.\s*(.+?)\s*$", text):
        line = norm(m.group(1))
        if label_key and (label_key in line or line[:80] in label_key):
            starts.append(m)
    if not starts:
        for m in re.finditer(re.escape(norm(label)), text):
            starts.append(m)
    top_re = re.compile(r"(?m)^\s*[1-9१-९]\s*\.\s+.+$")
    best = None
    for m in starts:
        start = m.end()
        nxt = top_re.search(text, start)
        end = nxt.start() if nxt else len(text)
        seg = text[start:end].strip()
        compact = len(re.sub(r"\s+", "", seg))
        if 1800 <= compact <= 180000 and (best is None or compact > best[1]):
            best = (seg, compact)
    return best


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
    records, review, published_keys = [], [], set()
    seen = set()
    for row in rows:
        issue = str(int(str(row.get("issue") or "0")))
        section = str(row.get("section") or "").translate(DEV).strip()
        label = norm(str(row.get("label") or ""))
        if not label or GENERIC.match(label) or len(label) > 320:
            continue
        low = label.lower()
        if any(x.lower() in low for x in NEGATIVE):
            continue
        key = (issue, section, label)
        if key in seen:
            continue
        seen.add(key)
        author, title = split_author_title(label)
        if not sane_author(author) or not sane_title(title):
            review.append({"issue": issue, "section": section, "label": label, "reason": "explicit name-like author/title not recoverable from heading"})
            continue
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
        date = parse_issue_date(text, issue)
        if not date:
            review.append({"issue": issue, "section": section, "label": label, "reason": "publication date not recovered"})
            continue
        title = norm(title)
        author = clean_author(author or "")
        rec_key = (issue, title.lower())
        if rec_key in published_keys:
            continue
        published_keys.add(rec_key)
        records.append({
            "title": title,
            "authors": [author],
            "publication_date": date,
            "year": date[:4],
            "issue": issue,
            "classification": class_label(list(row.get("signals") or [])),
            "language": "mai",
            "slug": slugify(title),
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
