#!/usr/bin/env python3
"""Append-only synchronizer for the historic Videha Scholar Research Book.

research/data/articles.json is the canonical article inventory.  This script never
rebuilds the Book page: it preserves the existing publication shell and existing
rows, appends only inventory records that are missing, and refreshes count/provenance
metadata.  If the historic Book structure cannot be recognised safely, it aborts.
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

# Stable Book-specific interface markers.  The exact historical page is the source
# of truth; we deliberately do not guess how its translator labels itself.
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
        return "; ".join(v for x in value if (v := as_text(x)))
    if isinstance(value, dict):
        for key in ("name", "title", "label", "value"):
            if value.get(key):
                return as_text(value[key])
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def canonical_path(value: str) -> str:
    value = unquote(as_text(value)).replace("\\", "/").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        value = unquote(parsed.path)
    value = value.split("#", 1)[0].split("?", 1)[0].lstrip("/")
    if value.startswith("videha/"):
        value = value[len("videha/"):]
    if value.startswith("research/"):
        return str(PurePosixPath(value))
    if value.endswith((".htm", ".html")):
        return str(PurePosixPath("research") / PurePosixPath(value))
    return ""


def href_path(href: str) -> str:
    href = html.unescape(href).strip()
    if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
        return ""
    parsed = urlparse(href)
    if parsed.scheme and parsed.netloc:
        host = parsed.netloc.casefold()
        if host not in {"www.videha.co.in", "videha.co.in", "videha-ejournal.github.io"}:
            return ""
        path = unquote(parsed.path).lstrip("/")
        if host == "videha-ejournal.github.io" and path.startswith("videha/"):
            path = path[len("videha/"):]
        return canonical_path(path)
    return canonical_path(href)


def load_inventory():
    raw = SOURCE.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    articles = payload.get("articles")
    if not isinstance(articles, list):
        raise SystemExit("articles.json has no articles list")
    declared = payload.get("count")
    if declared is not None and int(declared) != len(articles):
        raise SystemExit(f"Inventory count mismatch: declared={declared}, actual={len(articles)}")
    paths = [canonical_path(a.get("path", "")) for a in articles]
    if any(not p for p in paths):
        raise SystemExit("Every inventory article must have a research/*.htm(l) path")
    if len(paths) != len(set(paths)):
        raise SystemExit("Duplicate article paths in canonical inventory")
    return raw, articles, paths


def assert_shell(text: str) -> None:
    missing = [m for m in SHELL_MARKERS if m not in text]
    if missing:
        raise SystemExit("Historic Research Book shell is not intact: " + ", ".join(missing))


def split_tbody(text: str):
    matches = list(re.finditer(r"(?is)<tbody\b[^>]*>.*?</tbody>", text))
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one Book tbody; found {len(matches)}")
    m = matches[0]
    block = m.group(0)
    open_end = block.find(">") + 1
    return text[:m.start()], block[:open_end], block[open_end:-len("</tbody>")], "</tbody>", text[m.end():]


def row_blocks(tbody: str) -> list[str]:
    return re.findall(r"(?is)<tr\b[^>]*>.*?</tr>", tbody)


def inventory_paths_in(text: str, inventory: set[str]) -> set[str]:
    found: set[str] = set()
    for href in re.findall(r"(?is)\bhref\s*=\s*[\"']([^\"']+)[\"']", text):
        p = href_path(href)
        if p in inventory:
            found.add(p)
    return found


def strip_tags(fragment: str) -> str:
    fragment = re.sub(r"(?is)<script\b.*?</script>|<style\b.*?</style>", "", fragment)
    fragment = re.sub(r"(?is)<[^>]+>", " ", fragment)
    return " ".join(html.unescape(fragment).split())


def headers(prefix: str) -> list[str]:
    return [strip_tags(x) for x in re.findall(r"(?is)<th\b[^>]*>(.*?)</th>", prefix)]


def classify(label: str, i: int, n: int) -> str:
    x = label.casefold()
    if any(k in x for k in ("क्रम", "serial", "no.")) or (i == 0 and n >= 2): return "number"
    if any(k in x for k in ("लेखक", "author")): return "author"
    if any(k in x for k in ("शीर्षक", "title")): return "title"
    if any(k in x for k in ("विधा", "genre")): return "genre"
    if any(k in x for k in ("भाषा", "language")): return "language"
    if any(k in x for k in ("अंक", "issue", "तिथि", "date")): return "issue"
    if any(k in x for k in ("वर्गीकरण", "classification", "category", "विषय")): return "classification"
    if any(k in x for k in ("सूचक", "keyword")): return "keywords"
    if any(k in x for k in ("लिंक", "link", "पाठ", "source", "mirror", "मिरर")) or i == n - 1: return "links"
    return "unknown"


def value(article, kind: str, number: int, path: str) -> str:
    title = as_text(article.get("title")) or Path(path).stem
    author = as_text(article.get("authors")) or as_text(article.get("author"))
    if kind == "number": return str(number)
    if kind == "author": return html.escape(author)
    if kind == "title": return html.escape(title)
    if kind == "genre": return html.escape(as_text(article.get("genre")))
    if kind == "language": return html.escape(as_text(article.get("language")))
    if kind == "issue":
        return html.escape(" · ".join(v for v in (as_text(article.get("issue")), as_text(article.get("date"))) if v))
    if kind == "classification": return html.escape(as_text(article.get("classification")))
    if kind == "keywords": return html.escape(as_text(article.get("keywords")))
    if kind == "links":
        encoded = quote(path, safe="/")
        return (f'<a href="{html.escape(OFFICIAL + encoded, quote=True)}">VIDEHA</a> · '
                f'<a href="{html.escape(MIRROR + encoded, quote=True)}">GitHub</a>')
    return ""


def render_row(article, number: int, path: str, labels: list[str]) -> str:
    kinds = [classify(label, i, len(labels)) for i, label in enumerate(labels)]
    if not {"author", "title", "links"}.issubset(kinds):
        raise SystemExit(f"Cannot safely map historic Book columns: {labels!r}")
    searchable = " ".join(filter(None, [
        as_text(article.get("author")), as_text(article.get("authors")), as_text(article.get("title")),
        as_text(article.get("genre")), as_text(article.get("language")), as_text(article.get("issue")),
        as_text(article.get("date")), as_text(article.get("classification")), as_text(article.get("keywords")),
    ])).casefold()
    cells = []
    for kind in kinds:
        cls = {"number": ' class="n"', "title": ' class="title"', "links": ' class="links"'}.get(kind, "")
        cells.append(f"<td{cls}>{value(article, kind, number, path)}</td>")
    return (f'\n<tr data-search="{html.escape(searchable, quote=True)}" '
            f'data-source-path="{html.escape(path, quote=True)}">' + "".join(cells) + "</tr>")


def language_counts(articles) -> dict[str, int]:
    out = {label: 0 for label, _ in LANGUAGE_LABELS}
    for article in articles:
        raw = as_text(article.get("language")).casefold()
        for label, aliases in LANGUAGE_LABELS:
            if any(alias.casefold() in raw for alias in aliases):
                out[label] += 1
                break
    return out


def refresh_outside(text: str, old_count: int, new_count: int, raw: bytes, articles) -> str:
    # Only the known corpus/status representations are changed.  Interface markup is untouched.
    text = re.sub(rf"(?<!\d){old_count}(?!\d)", str(new_count), text)
    deva = str.maketrans("0123456789", "०१२३४५६७८९")
    text = text.replace(str(old_count).translate(deva), str(new_count).translate(deva))
    counts = language_counts(articles)
    status = (f"अन्तिम सत्यापित कॉर्पस : {new_count} लेख"
              f" · बज्जिका {counts['बज्जिका']} · अंग्रेजी {counts['अंग्रेजी']}"
              f" · मैथिली {counts['मैथिली']} · संस्कृत {counts['संस्कृत']}"
              f" · ठेठी-अंगिका {counts['ठेठी-अंगिका']}")
    text = re.sub(
        r"अन्तिम सत्यापित कॉर्पस\s*:\s*\d+\s*लेख(?:\s*·\s*बज्जिका\s*\d+)?(?:\s*·\s*अंग्रेजी\s*\d+)?(?:\s*·\s*मैथिली\s*\d+)?(?:\s*·\s*संस्कृत\s*\d+)?(?:\s*·\s*ठेठी-अंगिका\s*\d+)?",
        status, text, count=1)
    text = re.sub(r'("numberOfItems"\s*:\s*)\d+', rf"\g<1>{new_count}", text)
    source_sha = hashlib.sha256(raw).hexdigest()
    provenance = (f'<meta name="videha-article-source" content="research/data/articles.json">\n'
                  f'<meta name="videha-article-source-sha256" content="{source_sha}">\n'
                  f'<meta name="videha-article-count" content="{new_count}">')
    text = re.sub(
        r'(?is)\s*<meta\s+name=["\']videha-article-source["\'][^>]*>\s*<meta\s+name=["\']videha-article-source-sha256["\'][^>]*>\s*<meta\s+name=["\']videha-article-count["\'][^>]*>',
        "\n" + provenance, text, count=1)
    if 'name="videha-article-source"' not in text and "name='videha-article-source'" not in text:
        text = re.sub(r"(?i)</head>", provenance + "\n</head>", text, count=1)
    return text


def synchronize(text: str):
    assert_shell(text)
    raw, articles, paths = load_inventory()
    inventory = set(paths)
    prefix, tbody_open, tbody, tbody_close, suffix = split_tbody(text)
    rows = row_blocks(tbody)
    old_count = len(rows)
    if old_count > len(articles):
        raise SystemExit(f"Refusing destructive sync: Book={old_count}, inventory={len(articles)}")
    found = inventory_paths_in(tbody, inventory)
    if len(found) != old_count:
        raise SystemExit(f"Cannot identify every historic article row safely: rows={old_count}, matched={len(found)}")
    missing = [(a, p) for a, p in zip(articles, paths) if p not in found]
    if old_count + len(missing) != len(articles):
        raise SystemExit("Append-only reconciliation failed")
    labels = headers(prefix)
    if not labels:
        raise SystemExit("Historic Book table headers not found")
    additions = "".join(render_row(a, old_count + i, p, labels) for i, (a, p) in enumerate(missing, 1))
    new_prefix = refresh_outside(prefix, old_count, len(articles), raw, articles)
    new_suffix = refresh_outside(suffix, old_count, len(articles), raw, articles)
    return new_prefix + tbody_open + tbody + additions + tbody_close + new_suffix, missing, old_count


def verify(text: str) -> None:
    assert_shell(text)
    raw, articles, paths = load_inventory()
    inventory = set(paths)
    prefix, _, tbody, _, suffix = split_tbody(text)
    rows = row_blocks(tbody)
    if len(rows) != len(articles):
        raise SystemExit(f"Book row mismatch: inventory={len(articles)}, book={len(rows)}")
    found = inventory_paths_in(tbody, inventory)
    if found != inventory:
        raise SystemExit(f"Book path mismatch: missing={len(inventory-found)}, matched={len(found)}")
    outside = prefix + suffix
    source_sha = hashlib.sha256(raw).hexdigest()
    required = (
        '<meta name="videha-article-source" content="research/data/articles.json">',
        f'<meta name="videha-article-source-sha256" content="{source_sha}">',
        f'<meta name="videha-article-count" content="{len(articles)}">',
    )
    missing = [x for x in required if x not in outside]
    if missing:
        raise SystemExit(f"Book provenance mismatch: {missing}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    current = OUTPUT.read_text(encoding="utf-8")
    if args.check:
        verify(current)
        _, articles, _ = load_inventory()
        print(f"Research Book verified: {len(articles)} canonical articles; historic shell intact")
        return
    rendered, missing, old_count = synchronize(current)
    verify(rendered)
    if rendered != current:
        OUTPUT.write_text(rendered, encoding="utf-8")
    _, articles, _ = load_inventory()
    print(f"SOURCE_COUNT={len(articles)}")
    print(f"EXISTING_ROWS={old_count}")
    print(f"MISSING_BEFORE={len(missing)}")
    for article, path in missing:
        print("APPENDED:", path, "::", as_text(article.get("title")), "::", as_text(article.get("authors")) or as_text(article.get("author")))
    print(f"FINAL_ROWS={len(articles)}")


if __name__ == "__main__":
    main()
