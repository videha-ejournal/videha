#!/usr/bin/env python3
"""Conservatively extract explicitly labelled research articles from Videha issues."""
from __future__ import annotations

import hashlib
import html
import re
from html.parser import HTMLParser
from pathlib import Path

DEV = str.maketrans("०१२३४५६७८९", "0123456789")
EXPLICIT_TERMS = (
    "शोध आलेख", "शोध-आलेख", "शोधपत्र", "शोध पत्र",
    "research paper", "research article",
)
# Videha's TOC typography changed over time. Recent issues commonly use
# “(पृष्ठ 12-18)”; older issues use “(पृ. 12-18)” or “[पृ. 12-18]”.
TOC_RE = re.compile(
    r"(?m)^\s*([0-9०-९]+\.[0-9०-९]+)\.\s*(.*?)\s*"
    r"(?:\(\s*(?:पृष्ठ|पृ\.?)|\[\s*(?:pages?|पृष्ठ|पृ\.?))\s*([0-9०-९]+)"
    r"(?:\s*[-–—]\s*([0-9०-९]+))?\s*(?:\)|\])\s*$",
    re.I,
)
# Still older issues may list simple article entries without any page range.
# This fallback is intentionally narrow: only standalone x.y entries are
# accepted. Composite labels such as 2.2.1....2.... are rejected below.
TOC_SIMPLE_RE = re.compile(r"(?m)^\s*([0-9०-९]+\.[0-9०-९]+)\.\s*(.+?)\s*$")


class SourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.hrefs: list[tuple[str, str]] = []
        self._href: str | None = None
        self._link_text: list[str] = []

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t in {"p", "div", "section", "article", "li", "h1", "h2", "h3", "h4", "h5", "h6", "br", "tr"}:
            self.parts.append("\n")
        if t == "a":
            self._href = dict(attrs).get("href")
            self._link_text = []

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in {"p", "div", "section", "article", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr"}:
            self.parts.append("\n")
        if t == "a" and self._href:
            self.hrefs.append((self._href, "".join(self._link_text).strip()))
            self._href = None
            self._link_text = []

    def handle_data(self, data):
        self.parts.append(data)
        if self._href is not None:
            self._link_text.append(data)

    def text(self) -> str:
        s = "".join(self.parts).replace("\r\n", "\n").replace("\r", "\n")
        s = re.sub(r"[ \t\u00a0]+", " ", s)
        s = re.sub(r"\n[ \t]+", "\n", s)
        s = re.sub(r"\n{3,}", "\n\n", s)
        return s.strip()


def latin_digits(s: str) -> str:
    return (s or "").translate(DEV)


def derived_issue_date(issue: str) -> str | None:
    """Videha issue 1 = 2008-01-01; issues appear on the 1st and 15th monthly."""
    try:
        n = int(latin_digits(issue))
    except Exception:
        return None
    if n < 1:
        return None
    half_index = (2008 * 24) + (n - 1)
    year, rem = divmod(half_index, 24)
    month = rem // 2 + 1
    day = 1 if rem % 2 == 0 else 15
    return f"{year:04d}-{month:02d}-{day:02d}"


def parse_issue_date(text: str, issue: str) -> str | None:
    return derived_issue_date(issue)


def _truncate_utf8(s: str, max_bytes: int) -> str:
    out: list[str] = []
    used = 0
    for ch in s:
        n = len(ch.encode("utf-8"))
        if used + n > max_bytes:
            break
        out.append(ch)
        used += n
    return "".join(out).rstrip("-")


def slugify(s: str) -> str:
    """Readable, deterministic slug that is safe under 255-byte filename limits."""
    original = re.sub(r"\s+", " ", s or "").strip().lower()
    slug = re.sub(r"[^\w\u0900-\u097f-]+", "-", original, flags=re.UNICODE).strip("-") or "article"
    if len(slug.encode("utf-8")) <= 180:
        return slug
    digest = hashlib.sha1(original.encode("utf-8")).hexdigest()[:10]
    prefix = _truncate_utf8(slug, 160)
    return f"{prefix}-{digest}" if prefix else f"article-{digest}"


def split_author_title(label: str) -> tuple[str | None, str | None]:
    cleaned = re.sub(r"\s+", " ", html.unescape(label)).strip()
    parts = re.split(r"\s*[-–—]\s*", cleaned, maxsplit=1)
    if len(parts) != 2:
        return None, None
    author, title = (p.strip(" .") for p in parts)
    if len(author) < 2 or len(title) < 3:
        return None, None
    return author, title


def explicit(title: str) -> bool:
    low = (title or "").lower()
    return any(t.lower() in low for t in EXPLICIT_TERMS)


def source_pdf(parser: SourceParser, issue: str) -> str:
    for href, txt in parser.hrefs:
        if "original pdf" in txt.lower() or ("archive.org" in href and href.lower().endswith(".pdf")):
            return html.unescape(href)
    return f"https://archive.org/download/VidehaAndSadeha/Videha%20{issue}.pdf"


def _marker(text: str) -> int:
    marker = text.find("ऐ अंकमे अछि")
    if marker < 0:
        marker = text.find("अनुक्रम")
    return max(marker, 0)


def _simple_toc(text: str, marker: int, window_end: int) -> tuple[list[dict], int]:
    prelim = list(TOC_SIMPLE_RE.finditer(text, marker, window_end))
    if not prelim:
        return [], marker
    # Find the first plausible standalone Author-Title entry, excluding composite
    # sublists whose label starts with another numeric marker (e.g. 1.Author...).
    usable = []
    for m in prelim:
        label = re.sub(r"\s+", " ", m.group(2)).strip()
        if re.match(r"^[0-9०-९]+\s*\.", label):
            continue
        author, title = split_author_title(label)
        if author and title:
            usable.append(m)
    if not usable:
        return [], marker

    first_sec = usable[0].group(1)
    sec_re = re.compile(rf"(?m)^\s*{re.escape(first_sec)}\.\s*")
    repeats = list(sec_re.finditer(text, usable[0].end(), min(len(text), window_end + 100000)))
    body_floor = repeats[0].start() if repeats else max(m.end() for m in usable)

    seen: set[str] = set()
    toc: list[dict] = []
    for m in usable:
        if m.start() >= body_floor:
            continue
        section, label = m.groups()
        sec_latin = latin_digits(section)
        if sec_latin in seen:
            continue
        seen.add(sec_latin)
        author, title = split_author_title(label)
        if not author or not title:
            continue
        toc.append({
            "section": sec_latin,
            "section_source": section,
            "label": label.strip(),
            "author": author,
            "title": title,
            "page_start": "",
            "page_end": "",
            "toc_start": m.start(),
            "toc_end": m.end(),
        })
    return toc, body_floor


def parse_toc_entries(text: str) -> tuple[list[dict], int]:
    """Parse Videha TOCs across current and legacy page-range conventions."""
    marker = _marker(text)
    window_end = min(len(text), marker + 140000)
    prelim = list(TOC_RE.finditer(text, marker, window_end))
    if not prelim:
        return _simple_toc(text, marker, window_end)

    first_sec = prelim[0].group(1)
    sec_re = re.compile(rf"(?m)^\s*{re.escape(first_sec)}\.\s*")
    repeats = list(sec_re.finditer(text, prelim[0].end(), min(len(text), window_end + 100000)))
    body_floor = repeats[0].start() if repeats else max(m.end() for m in prelim)

    toc_matches = [m for m in prelim if m.start() < body_floor]
    seen: set[str] = set()
    toc: list[dict] = []
    for m in toc_matches:
        section, label, p1, p2 = m.groups()
        sec_latin = latin_digits(section)
        if sec_latin in seen:
            continue
        seen.add(sec_latin)
        author, title = split_author_title(label)
        toc.append({
            "section": sec_latin,
            "section_source": section,
            "label": label.strip(),
            "author": author,
            "title": title,
            "page_start": latin_digits(p1),
            "page_end": latin_digits(p2 or p1),
            "toc_start": m.start(),
            "toc_end": m.end(),
        })
    return toc, body_floor


def clean_body(segment: str, section: str, author: str, title: str) -> str:
    lines = [x.strip() for x in segment.splitlines()]
    while lines and not lines[0]:
        lines.pop(0)
    for _ in range(8):
        if not lines:
            break
        x = re.sub(r"\s+", " ", lines[0]).strip()
        x_cmp = re.sub(r"[\s.'\"’‘“”:\-\[\]]+", "", x)
        probes = [
            re.sub(r"[\s.'\"’‘“”:\-\[\]]+", "", section + "." + author + "-" + title),
            re.sub(r"[\s.'\"’‘“”:\-\[\]]+", "", author),
            re.sub(r"[\s.'\"’‘“”:\-\[\]]+", "", title),
        ]
        if any(x_cmp == p for p in probes):
            lines.pop(0)
        else:
            break
    for i, line in enumerate(lines):
        if re.search(r"अपन\s+मंतव्य", line):
            lines = lines[:i]
            break
    out: list[str] = []
    blank = False
    for line in lines:
        if not line:
            if out and not blank:
                out.append("")
            blank = True
        else:
            out.append(line)
            blank = False
    return "\n".join(out).strip()


def body_to_html(body: str) -> str:
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    return "".join(f"<p>{html.escape(p, quote=False).replace(chr(10), '<br>')}</p>" for p in paras)


def _section_occurrences(text: str, section_source: str, floor: int) -> list[re.Match]:
    pat = re.compile(rf"(?m)^\s*{re.escape(section_source)}\.\s*")
    return list(pat.finditer(text, floor))


def _next_section_position(text: str, toc: list[dict], idx: int, start: int) -> int:
    positions: list[int] = []
    for nxt in toc[idx + 1:]:
        pat = re.compile(rf"(?m)^\s*{re.escape(nxt['section_source'])}\.\s*")
        m = pat.search(text, start + 1)
        if m:
            positions.append(m.start())
    return min(positions) if positions else len(text)


def locate_article_body(text: str, toc: list[dict], idx: int, body_floor: int) -> tuple[int, int] | None:
    item = toc[idx]
    occurrences = _section_occurrences(text, item["section_source"], body_floor)
    if not occurrences:
        return None
    scored: list[tuple[int, int, int]] = []
    author = item.get("author") or ""
    title = item.get("title") or ""
    for m in occurrences:
        start = m.start()
        end = _next_section_position(text, toc, idx, start)
        if end <= start:
            continue
        segment = text[start:end]
        compact = len(re.sub(r"\s+", "", segment))
        head = re.sub(r"\s+", " ", segment[:1600])
        score = min(compact, 20000)
        if compact < 500:
            score -= 20000
        if title and title[:40] in head:
            score += 5000
        if author and author in head:
            score += 2500
        if re.search(r"(?m)^\s*[0-9०-९]+\.[0-9०-९]+\.\s*", segment[120:700]):
            score -= 12000
        scored.append((score, start, end))
    if not scored:
        return None
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    score, start, end = scored[0]
    if score < 0:
        return None
    return start, end


def article_body(text: str, toc: list[dict], idx: int, body_floor: int) -> str:
    item = toc[idx]
    bounds = locate_article_body(text, toc, idx, body_floor)
    if not bounds or not item.get("author") or not item.get("title"):
        return ""
    start, end = bounds
    return clean_body(text[start:end], item["section_source"], item["author"], item["title"])


def extract_issue(path: Path, root: Path | None = None) -> tuple[list[dict], list[dict]]:
    mi = re.search(r"videha-(\d{1,4})\.html?$", path.name, re.I)
    if not mi:
        return [], []
    issue = str(int(mi.group(1)))
    raw = path.read_text(encoding="utf-8", errors="ignore")
    parser = SourceParser()
    try:
        parser.feed(raw)
    except Exception:
        pass
    text = parser.text()
    date = parse_issue_date(text, issue)
    pdf = source_pdf(parser, issue)
    toc, floor = parse_toc_entries(text)
    if not toc:
        return [], []
    source_path = path.relative_to(root).as_posix() if root else path.as_posix()
    published, review = [], []
    for idx, item in enumerate(toc):
        title = item.get("title") or ""
        if not explicit(title):
            continue
        reasons: list[str] = []
        if not date:
            reasons.append("publication date not recovered")
        if not item.get("author") or not title:
            reasons.append("author/title split failed")
        body = article_body(text, toc, idx, floor) if item.get("author") and title else ""
        if len(re.sub(r"\s+", "", body)) < 800:
            reasons.append("article body too short for safe publication")
        base = {
            "issue": issue, "source_path": source_path, "section": item["section"],
            "author": item.get("author"), "title": title or item["label"],
            "publication_date": date, "page_start": item["page_start"],
            "page_end": item["page_end"], "source_url": pdf,
        }
        if reasons:
            base.update(status="review", reasons=reasons)
            review.append(base)
            continue
        published.append({
            "title": title, "authors": [item["author"]], "publication_date": date,
            "year": date[:4], "issue": issue,
            "classification": "Research article (source-labelled शोध आलेख)",
            "language": "mai",
            "slug": slugify(re.sub(r"\s*\([^)]*शोध[^)]*\)\s*", "", title, flags=re.I)),
            "page_start": item["page_start"], "page_end": item["page_end"],
            "source_url": pdf, "full_text_html": body_to_html(body),
            "_auto_source": source_path, "_auto_section": item["section"],
        })
    return published, review


def issue_files(docs: Path) -> list[Path]:
    files = set(docs.glob("videha-*.html")) | set(docs.glob("videha-*.htm"))
    return sorted(files, key=lambda p: p.name.lower())


def extract_explicit_records(root: Path) -> tuple[list[dict], list[dict], dict]:
    docs = root / "search-documents"
    files = issue_files(docs) if docs.exists() else []
    records, review = [], []
    for path in files:
        try:
            pub, rev = extract_issue(path, root=root)
            records.extend(pub)
            review.extend(rev)
        except Exception as e:
            review.append({"source_path": path.relative_to(root).as_posix(), "status": "review", "reasons": [f"extractor exception: {e}"]})
    dedup: dict[tuple, dict] = {}
    for r in records:
        dedup[(str(r.get("issue")), r.get("title"), tuple(r.get("authors") or []))] = r
    records = sorted(dedup.values(), key=lambda r: (r["publication_date"], int(r["issue"]), r["title"]))
    return records, review, {
        "issue_files_scanned": len(files),
        "explicit_articles_publishable": len(records),
        "explicit_articles_review": len(review),
    }


if __name__ == "__main__":
    import json
    ROOT = Path(__file__).resolve().parents[1]
    records, review, summary = extract_explicit_records(ROOT)
    print(json.dumps({"summary": summary, "published": records, "review": review}, ensure_ascii=False, indent=2))
