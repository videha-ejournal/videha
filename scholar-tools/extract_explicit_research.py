#!/usr/bin/env python3
"""Conservatively extract explicitly labelled research articles from Videha issue HTML.

The source corpus lives under search-documents/. Automatic publication occurs only
when issue date, author/title, page range, article boundary and substantial body
text are all recoverable. Anything ambiguous is held for review.
"""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from pathlib import Path

DEV = str.maketrans("०१२३४५६७८९", "0123456789")
MONTHS = {
    "जनवरी": 1, "फरवरी": 2, "फ़रवरी": 2, "मार्च": 3,
    "अप्रैल": 4, "अप्रेल": 4, "मई": 5, "जून": 6, "जुलाई": 7,
    "अगस्त": 8, "सितम्बर": 9, "सितंबर": 9, "अक्टूबर": 10,
    "नवम्बर": 11, "नवंबर": 11, "दिसम्बर": 12, "दिसंबर": 12,
}
EXPLICIT_TERMS = (
    "शोध आलेख", "शोध-आलेख", "शोधपत्र", "शोध पत्र",
    "research paper", "research article",
)
TOC_RE = re.compile(
    r"(?m)^\s*([0-9०-९]+\.[0-9०-९]+)\.\s*(.*?)\s*"
    r"(?:\(\s*पृष्ठ|\[\s*pages?)\s*([0-9०-९]+)"
    r"(?:\s*[-–—]\s*([0-9०-९]+))?\s*(?:\)|\])\s*$",
    re.I,
)
DATE_RE = re.compile(
    r"([0-9०-९]{1,2})\s+"
    r"(जनवरी|फरवरी|फ़रवरी|मार्च|अप्रैल|अप्रेल|मई|जून|जुलाई|अगस्त|"
    r"सितम्बर|सितंबर|अक्टूबर|नवम्बर|नवंबर|दिसम्बर|दिसंबर)\s+"
    r"([0-9०-९]{4})",
    re.I,
)


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


def slugify(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip().lower()
    s = re.sub(r"[^\w\u0900-\u097f-]+", "-", s, flags=re.UNICODE)
    return s.strip("-")[:100] or "article"


def _iso_date(m: re.Match) -> str | None:
    d = int(latin_digits(m.group(1)))
    y = int(latin_digits(m.group(3)))
    month = MONTHS.get(m.group(2))
    if month and 1 <= d <= 31 and 2000 <= y <= 2100:
        return f"{y:04d}-{month:02d}-{d:02d}"
    return None


def parse_issue_date(text: str, issue: str) -> str | None:
    """Recover the issue publication date, not dates from the standardized history header."""
    target = str(int(latin_digits(issue)))
    front = text[:120000]

    # Best evidence: the same line names this issue and carries a date.
    for line in front.splitlines():
        line_ascii = latin_digits(line)
        if not re.search(rf"(?<!\d){re.escape(target)}(?!\d)", line_ascii):
            continue
        if not ("अंक" in line or re.search(r"\b(?:VIDEHA|issue)\b", line, re.I)):
            continue
        m = DATE_RE.search(line)
        if m:
            iso = _iso_date(m)
            if iso:
                return iso

    # Second-best evidence: date very near an issue-number expression.
    for m in DATE_RE.finditer(front):
        lo = max(0, m.start() - 180)
        hi = min(len(front), m.end() + 180)
        nearby = latin_digits(front[lo:hi])
        patterns = [
            rf"(?:अंक|issue|VIDEHA)\D{{0,45}}{re.escape(target)}(?!\d)",
            rf"(?<!\d){re.escape(target)}\D{{0,45}}(?:अंक|issue)",
        ]
        if any(re.search(p, nearby, re.I) for p in patterns):
            iso = _iso_date(m)
            if iso:
                return iso
    return None


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
    low = title.lower()
    return any(t.lower() in low for t in EXPLICIT_TERMS)


def source_pdf(parser: SourceParser, issue: str) -> str:
    for href, txt in parser.hrefs:
        if "original pdf" in txt.lower() or ("archive.org" in href and href.lower().endswith(".pdf")):
            return html.unescape(href)
    return f"https://archive.org/download/VidehaAndSadeha/Videha%20{issue}.pdf"


def parse_toc_entries(text: str) -> tuple[list[dict], int]:
    """Return the issue-front TOC only and the position where article bodies begin."""
    marker = text.find("ऐ अंकमे अछि")
    if marker < 0:
        marker = text.find("अनुक्रम")
    if marker < 0:
        marker = 0

    window_end = min(len(text), marker + 120000)
    preliminary = list(TOC_RE.finditer(text, marker, window_end))
    if not preliminary:
        return [], marker

    # The first TOC section repeats when the actual article body starts. Stop there,
    # so numbered/page-like material much later in a large issue cannot pollute the TOC.
    first_sec = preliminary[0].group(1)
    first_body_re = re.compile(rf"(?m)^\s*{re.escape(first_sec)}\.\s*")
    first_body = first_body_re.search(text, preliminary[0].end())
    body_floor = first_body.start() if first_body else max(m.end() for m in preliminary)

    matches = [m for m in preliminary if m.start() < body_floor]
    toc: list[dict] = []
    for m in matches:
        section, label, p1, p2 = m.groups()
        author, title = split_author_title(label)
        toc.append({
            "section": latin_digits(section),
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

    for _ in range(5):
        if not lines:
            break
        x = re.sub(r"\s+", " ", lines[0]).strip()
        x_cmp = re.sub(r"[\s.'\"’‘“”:-]+", "", x)
        probes = [
            re.sub(r"[\s.'\"’‘“”:-]+", "", section + "." + author + "-" + title),
            re.sub(r"[\s.'\"’‘“”:-]+", "", author),
            re.sub(r"[\s.'\"’‘“”:-]+", "", title),
        ]
        if any(x_cmp == p for p in probes):
            lines.pop(0)
            continue
        break

    cut = None
    for i, line in enumerate(lines):
        if re.search(r"अपन\s+मंतव्य", line):
            cut = i
            break
    if cut is not None:
        lines = lines[:cut]

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
    chunks = []
    for p in paras:
        safe = html.escape(p, quote=False).replace("\n", "<br>")
        chunks.append(f"<p>{safe}</p>")
    return "".join(chunks)


def extract_issue(path: Path, root: Path | None = None) -> tuple[list[dict], list[dict]]:
    m_issue = re.search(r"videha-(\d{1,4})\.html?$", path.name, re.I)
    if not m_issue:
        return [], []
    issue = str(int(m_issue.group(1)))
    raw = path.read_text(encoding="utf-8", errors="ignore")
    parser = SourceParser()
    try:
        parser.feed(raw)
    except Exception:
        pass
    text = parser.text()
    date = parse_issue_date(text, issue)
    pdf = source_pdf(parser, issue)
    toc, body_floor = parse_toc_entries(text)
    if not toc:
        return [], []

    published: list[dict] = []
    review: list[dict] = []
    source_path = path.relative_to(root).as_posix() if root else path.as_posix()

    for idx, item in enumerate(toc):
        title = item.get("title") or ""
        if not explicit(title):
            continue
        reasons: list[str] = []
        if not date:
            reasons.append("publication date not recovered")
        if not item.get("author") or not title:
            reasons.append("author/title split failed")

        body_marker = re.compile(rf"(?m)^\s*{re.escape(item['section_source'])}\.\s*")
        bm = body_marker.search(text, body_floor)
        body_start = bm.start() if bm else None
        if body_start is None:
            reasons.append("article body heading not found after contents")

        body_end = None
        if body_start is not None:
            for nxt in toc[idx + 1:]:
                nm = re.compile(rf"(?m)^\s*{re.escape(nxt['section_source'])}\.\s*").search(text, body_start + 1)
                if nm:
                    body_end = nm.start()
                    break
            if body_end is None:
                body_end = len(text)

        body = ""
        if body_start is not None and body_end is not None and item.get("author") and title:
            body = clean_body(text[body_start:body_end], item["section_source"], item["author"], title)
            if len(re.sub(r"\s+", "", body)) < 800:
                reasons.append("article body too short for safe publication")
            if re.search(r"(?m)^\s*[0-9०-९]+\.[0-9०-९]+\.\s*", body[200:]):
                reasons.append("possible next-article heading inside extracted body")

        base = {
            "issue": issue,
            "source_path": source_path,
            "section": item["section"],
            "author": item.get("author"),
            "title": title or item["label"],
            "publication_date": date,
            "page_start": item["page_start"],
            "page_end": item["page_end"],
            "source_url": pdf,
        }
        if reasons:
            base["status"] = "review"
            base["reasons"] = reasons
            review.append(base)
            continue

        published.append({
            "title": title,
            "authors": [item["author"]],
            "publication_date": date,
            "year": date[:4],
            "issue": issue,
            "classification": "Research article (source-labelled शोध आलेख)",
            "language": "mai",
            "slug": slugify(re.sub(r"\s*\([^)]*शोध[^)]*\)\s*", "", title, flags=re.I)),
            "page_start": item["page_start"],
            "page_end": item["page_end"],
            "source_url": pdf,
            "full_text_html": body_to_html(body),
            "_auto_source": source_path,
            "_auto_section": item["section"],
        })

    return published, review


def issue_files(docs: Path) -> list[Path]:
    files = set(docs.glob("videha-*.html")) | set(docs.glob("videha-*.htm"))
    return sorted(files, key=lambda p: p.name.lower())


def extract_explicit_records(root: Path) -> tuple[list[dict], list[dict], dict]:
    docs = root / "search-documents"
    records: list[dict] = []
    review: list[dict] = []
    files = issue_files(docs) if docs.exists() else []
    for path in files:
        try:
            pub, rev = extract_issue(path, root=root)
            records.extend(pub)
            review.extend(rev)
        except Exception as e:
            review.append({
                "source_path": path.relative_to(root).as_posix(),
                "status": "review",
                "reasons": [f"extractor exception: {e}"],
            })

    dedup: dict[tuple, dict] = {}
    for r in records:
        key = (str(r.get("issue")), r.get("title"), tuple(r.get("authors") or []))
        dedup[key] = r
    records = sorted(dedup.values(), key=lambda r: (r["publication_date"], int(r["issue"]), r["title"]))
    summary = {
        "issue_files_scanned": len(files),
        "explicit_articles_publishable": len(records),
        "explicit_articles_review": len(review),
    }
    return records, review, summary


if __name__ == "__main__":
    import json
    ROOT = Path(__file__).resolve().parents[1]
    records, review, summary = extract_explicit_records(ROOT)
    print(json.dumps({"summary": summary, "published": records, "review": review}, ensure_ascii=False, indent=2))
