#!/usr/bin/env python3
"""Synchronize the Videha Scholar Research Book with the canonical article inventory.

The Research Book HTML is a hand-designed publication shell. This updater preserves
that shell. It only appends missing inventory rows, refreshes corpus/provenance counts,
and verifies that the Book-specific interface is still present.

It deliberately refuses to rebuild, delete, reorder, or replace existing rows.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research" / "data" / "articles.json"
OUTPUT = ROOT / "research" / "videha-scholar-research-book.html"

OFFICIAL = "https://www.videha.co.in/"
MIRROR = "https://videha-ejournal.github.io/videha/"

SHELL_MARKERS = (
    "विदेह Scholar अनुसन्धान पुस्तक",
    "🔊 सुनू · Listen",
    "GitHub Home",
    'class="back-top"',
    'id="book-search"',
)

LANGUAGE_LABELS = (
    ("बज्जिका", ("bajjika", "बज्जिका")),
    ("अंग्रेजी", ("english", "अंग्रेजी", "अंग्रेज़ी")),
    ("मैथिली", ("maithili", "मैथिली")),
    ("संस्कृत", ("sanskrit", "संस्कृत")),
    ("ठेठी-अंगिका", ("thethi-angika", "thethi angika", "ठेठी-अंगिका", "ठेठी अंगिका")),
)


def as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(part for item in value if (part := as_text(item)))
    if isinstance(value, dict):
        for key in ("name", "title", "label", "value"):
            if value.get(key):
                return as_text(value[key])
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def canonical_inventory_path(value: str) -> str:
    path = unquote(as_text(value)).replace("\\", "/").strip()
    if not path:
        return ""
    parsed = urlparse(path)
    if parsed.scheme and parsed.netloc:
        path = unquote(parsed.path)
    path = path.split("#", 1)[0].split("?", 1)[0].lstrip("/")
    if path.startswith("videha/"):
        path = path[len("videha/"):]
    if path.startswith("research/"):
        return str(PurePosixPath(path))
    if path.endswith((".htm", ".html")):
        return str(PurePosixPath("research") / PurePosixPath(path))
    return ""


def normalize_href(href: str) -> str:
    href = html.unescape(href).strip()
    if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
        return ""
    parsed = urlparse(href)
    if parsed.scheme and parsed.netloc:
        host = parsed.netloc.lower()
        if host not in {
            "www.videha.co.in",
            "videha.co.in",
            "videha-ejournal.github.io",
        }:
            return ""
        path = unquote(parsed.path).lstrip("/")
        if host == "videha-ejournal.github.io" and path.startswith("videha/"):
            path = path[len("videha/"):]
        return canonical_inventory_path(path)
    return canonical_inventory_path(href)


def load_source():
    raw = SOURCE.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    articles = payload.get("articles")
    if not isinstance(articles, list):
        raise SystemExit("research/data/articles.json must contain an 'articles' list")
    declared = payload.get("count")
    if declared is not None and int(declared) != len(articles):
        raise SystemExit(
            f"Inventory count mismatch: declared={declared}, actual={len(articles)}"
        )
    paths = [canonical_inventory_path(a.get("path", "")) for a in articles]
    if any(not path for path in paths):
        raise SystemExit("Every article inventory record must have a valid research/*.htm(l) path")
    if len(paths) != len(set(paths)):
        raise SystemExit("Duplicate article paths found in research/data/articles.json")
    return raw, articles, paths


def assert_shell(text: str) -> None:
    missing = [marker for marker in SHELL_MARKERS if marker not in text]
    has_translation = bool(
        re.search(r"(41\s*(?:language|भाषा)|translat|अनुवाद|भाषा\s*(?:चुनू|चयन))", text, re.I)
    )
    if not has_translation:
        missing.append("41-language/translation interface")
    if missing:
        raise SystemExit(
            "Refusing to modify Research Book because its historic shell is missing: "
            + ", ".join(missing)
        )


def split_tbody(text: str):
    matches = list(re.finditer(r"(?is)<tbody\b[^>]*>.*?</tbody>", text))
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one Research Book <tbody>; found {len(matches)}")
    m = matches[0]
    block = m.group(0)
    open_end = block.find(">") + 1
    return (
        text[: m.start()],
        block[:open_end],
        block[open_end:-len("</tbody>")],
        "</tbody>",
        text[m.end():],
    )


def row_blocks(tbody_inner: str):
    return re.findall(r"(?is)<tr\b[^>]*>.*?</tr>", tbody_inner)


def inventory_paths_in_book(text: str, inventory_set: set[str]) -> set[str]:
    found = set()
    for href in re.findall(r"(?is)\bhref\s*=\s*[\"']([^\"']+)[\"']", text):
        path = normalize_href(href)
        if path in inventory_set:
            found.add(path)
    return found


def strip_tags(fragment: str) -> str:
    fragment = re.sub(r"(?is)<script\b.*?</script>|<style\b.*?</style>", "", fragment)
    fragment = re.sub(r"(?is)<[^>]+>", " ", fragment)
    return " ".join(html.unescape(fragment).split())


def header_labels(prefix: str) -> list[str]:
    heads = re.findall(r"(?is)<th\b[^>]*>(.*?)</th>", prefix)
    return [strip_tags(h).strip() for h in heads]


def language_counts(articles) -> dict[str, int]:
    out = {label: 0 for label, _ in LANGUAGE_LABELS}
    for article in articles:
        raw = as_text(article.get("language")).casefold()
        for label, aliases in LANGUAGE_LABELS:
            if any(alias.casefold() in raw for alias in aliases):
                out[label] += 1
                break
    return out


def render_links(path: str) -> str:
    encoded = quote(path, safe="/")
    official = OFFICIAL + encoded
    mirror = MIRROR + encoded
    return (
        f'<a href="{html.escape(official, quote=True)}">VIDEHA</a> · '
        f'<a href="{html.escape(mirror, quote=True)}">GitHub</a>'
    )


def article_value(article, kind: str, index: int, path: str) -> str:
    title = as_text(article.get("title")) or Path(path).stem
    author = as_text(article.get("authors")) or as_text(article.get("author"))
    genre = as_text(article.get("genre"))
    language = as_text(article.get("language"))
    issue = as_text(article.get("issue"))
    date = as_text(article.get("date"))
    classification = as_text(article.get("classification"))
    keywords = as_text(article.get("keywords"))

    if kind == "number":
        return str(index)
    if kind == "author":
        return html.escape(author)
    if kind == "title":
        return html.escape(title)
    if kind == "genre":
        return html.escape(genre)
    if kind == "language":
        return html.escape(language)
    if kind == "issue":
        value = " · ".join(v for v in (issue, date) if v)
        return html.escape(value)
    if kind == "classification":
        return html.escape(classification)
    if kind == "keywords":
        return html.escape(keywords)
    if kind == "links":
        return render_links(path)
    return ""


def classify_header(label: str, position: int, total: int) -> str:
    x = label.casefold()
    if any(k in x for k in ("क्रम", "#", "no.", "serial")) or (position == 0 and total >= 2):
        return "number"
    if any(k in x for k in ("लेखक", "author")):
        return "author"
    if any(k in x for k in ("शीर्षक", "title")):
        return "title"
    if any(k in x for k in ("विधा", "genre")):
        return "genre"
    if any(k in x for k in ("भाषा", "language")):
        return "language"
    if any(k in x for k in ("अंक", "issue", "तिथि", "date")):
        return "issue"
    if any(k in x for k in ("वर्गीकरण", "classification", "category", "विषय")):
        return "classification"
    if any(k in x for k in ("सूचक", "keyword")):
        return "keywords"
    if any(k in x for k in ("लिंक", "link", "पाठ", "source", "mirror", "मिरर")):
        return "links"
    if position == total - 1:
        return "links"
    return "unknown"


def render_row(article, index: int, path: str, labels: list[str]) -> str:
    kinds = [classify_header(label, i, len(labels)) for i, label in enumerate(labels)]
    if "title" not in kinds or "author" not in kinds or "links" not in kinds:
        raise SystemExit(f"Cannot safely map historic Book columns: headers={labels!r}")
    searchable = " ".join(
        filter(
            None,
            (
                as_text(article.get("author")),
                as_text(article.get("authors")),
                as_text(article.get("title")),
                as_text(article.get("genre")),
                as_text(article.get("language")),
                as_text(article.get("issue")),
                as_text(article.get("date")),
                as_text(article.get("classification")),
                as_text(article.get("keywords")),
            ),
        )
    )
    cells = []
    for kind in kinds:
        cls = {
            "number": ' class="n"',
            "title": ' class="title"',
            "links": ' class="links"',
        }.get(kind, "")
        cells.append(f"<td{cls}>{article_value(article, kind, index, path)}</td>")
    return (
        f'\n<tr data-search="{html.escape(searchable.casefold(), quote=True)}" '
        f'data-source-path="{html.escape(path, quote=True)}">'
        + "".join(cells)
        + "</tr>"
    )


def update_status_and_provenance(outside: str, old_count: int, new_count: int, raw: bytes, articles) -> str:
    source_sha = hashlib.sha256(raw).hexdigest()

    outside = re.sub(rf"(?<!\d){old_count}(?!\d)", str(new_count), outside)
    deva = str.maketrans("0123456789", "०१२३४५६७८९")
    outside = outside.replace(str(old_count).translate(deva), str(new_count).translate(deva))

    counts = language_counts(articles)
    status = (
        f"अन्तिम सत्यापित कॉर्पस : {new_count} लेख"
        f" · बज्जिका {counts['बज्जिका']}"
        f" · अंग्रेजी {counts['अंग्रेजी']}"
        f" · मैथिली {counts['मैथिली']}"
        f" · संस्कृत {counts['संस्कृत']}"
        f" · ठेठी-अंगिका {counts['ठेठी-अंगिका']}"
    )
    outside = re.sub(
        r"अन्तिम सत्यापित कॉर्पस\s*:\s*\d+\s*लेख"
        r"(?:\s*·\s*बज्जिका\s*\d+)?"
        r"(?:\s*·\s*अंग्रेजी\s*\d+)?"
        r"(?:\s*·\s*मैथिली\s*\d+)?"
        r"(?:\s*·\s*संस्कृत\s*\d+)?"
        r"(?:\s*·\s*ठेठी-अंगिका\s*\d+)?",
        status,
        outside,
        count=1,
    )
    outside = re.sub(
        r'("numberOfItems"\s*:\s*)\d+',
        rf"\g<1>{new_count}",
        outside,
    )

    provenance = (
        f'<meta name="videha-article-source" content="research/data/articles.json">\n'
        f'<meta name="videha-article-source-sha256" content="{source_sha}">\n'
        f'<meta name="videha-article-count" content="{new_count}">'
    )
    outside = re.sub(
        r'(?is)\s*<meta\s+name=["\']videha-article-source["\'][^>]*>\s*'
        r'<meta\s+name=["\']videha-article-source-sha256["\'][^>]*>\s*'
        r'<meta\s+name=["\']videha-article-count["\'][^>]*>',
        "\n" + provenance,
        outside,
        count=1,
    )
    if 'name="videha-article-source"' not in outside and "name='videha-article-source'" not in outside:
        outside = re.sub(r"(?i)</head>", provenance + "\n</head>", outside, count=1)
    return outside


def synchronize(text: str):
    assert_shell(text)
    raw, articles, inventory_paths = load_source()
    inventory_set = set(inventory_paths)

    prefix, tbody_open, tbody_inner, tbody_close, suffix = split_tbody(text)
    rows = row_blocks(tbody_inner)
    old_count = len(rows)
    if old_count > len(articles):
        raise SystemExit(
            f"Refusing destructive sync: Book has {old_count} rows but inventory has {len(articles)}"
        )

    found = inventory_paths_in_book(tbody_inner, inventory_set)
    if len(found) != old_count:
        raise SystemExit(
            "Cannot safely identify every historic article row: "
            f"rows={old_count}, inventory-linked rows={len(found)}"
        )

    missing = [(a, p) for a, p in zip(articles, inventory_paths) if p not in found]
    if len(found) + len(missing) != len(articles):
        raise SystemExit("Inventory/Book path reconciliation failed")

    labels = header_labels(prefix)
    if not labels:
        raise SystemExit("Historic Research Book table headers were not found")
    expected_final = old_count + len(missing)
    if expected_final != len(articles):
        raise SystemExit(
            f"Append-only reconciliation mismatch: {old_count}+{len(missing)} != {len(articles)}"
        )

    additions = []
    for offset, (article, path) in enumerate(missing, start=1):
        additions.append(render_row(article, old_count + offset, path, labels))
    new_tbody_inner = tbody_inner + "".join(additions)

    new_prefix = update_status_and_provenance(prefix, old_count, len(articles), raw, articles)
    new_suffix = update_status_and_provenance(suffix, old_count, len(articles), raw, articles)
    rendered = new_prefix + tbody_open + new_tbody_inner + tbody_close + new_suffix
    return rendered, missing, old_count


def verify(text: str) -> None:
    assert_shell(text)
    raw, articles, inventory_paths = load_source()
    inventory_set = set(inventory_paths)
    prefix, _, tbody_inner, _, suffix = split_tbody(text)
    rows = row_blocks(tbody_inner)
    if len(rows) != len(articles):
        raise SystemExit(f"Research Book row mismatch: inventory={len(articles)}, book={len(rows)}")
    found = inventory_paths_in_book(tbody_inner, inventory_set)
    if found != inventory_set:
        missing = sorted(inventory_set - found)
        extra = sorted(found - inventory_set)
        raise SystemExit(
            f"Research Book path mismatch: missing={missing[:5]}, extra={extra[:5]}"
        )
    source_sha = hashlib.sha256(raw).hexdigest()
    outside = prefix + suffix
    expected = (
        '<meta name="videha-article-source" content="research/data/articles.json">',
        f'<meta name="videha-article-source-sha256" content="{source_sha}">',
        f'<meta name="videha-article-count" content="{len(articles)}">',
    )
    absent = [marker for marker in expected if marker not in outside]
    if absent:
        raise SystemExit(f"Research Book provenance mismatch: {absent}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if not OUTPUT.exists():
        raise SystemExit(f"Missing Research Book: {OUTPUT}")
    current = OUTPUT.read_text(encoding="utf-8")

    if args.check:
        verify(current)
        _, articles, _ = load_source()
        print(f"Research Book shell + inventory alignment verified: {len(articles)} articles")
        return

    rendered, missing, old_count = synchronize(current)
    verify(rendered)
    if rendered != current:
        OUTPUT.write_text(rendered, encoding="utf-8")
    _, articles, _ = load_source()
    print(f"SOURCE_COUNT={len(articles)}")
    print(f"EXISTING_ROWS={old_count}")
    print(f"MISSING_BEFORE={len(missing)}")
    for article, path in missing:
        print(
            "APPENDED:",
            path,
            "::",
            as_text(article.get("title")),
            "::",
            as_text(article.get("authors")) or as_text(article.get("author")),
        )
    print(f"FINAL_ROWS={len(articles)}")


if __name__ == "__main__":
    main()
