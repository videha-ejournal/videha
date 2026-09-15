#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {".git", "node_modules", "_site", ".venv", "venv"}
SUFFIXES = {".htm", ".html"}
NON_PAGE_FILES = {
    "google7d0b1633a9939d34.html",
    "universal-search-embed-snippet.html",
}

ICON_LINK_RE = re.compile(
    r"<link\b(?=[^>]*\brel\s*=\s*[\"'][^\"']*(?:icon|apple-touch-icon)[^\"']*[\"'])[^>]*>\s*",
    re.I,
)
HEAD_CLOSE_RE = re.compile(r"</head\s*>", re.I)
HEAD_OPEN_RE = re.compile(r"<head\b[^>]*>", re.I)
HTML_OPEN_RE = re.compile(r"<html\b[^>]*>", re.I)


def is_non_page(rel: Path) -> bool:
    posix = rel.as_posix()
    if posix in NON_PAGE_FILES:
        return True
    if rel.name.lower() == "real_x.htm" and rel.parts and rel.parts[0].lower() == "photogallery":
        return True
    return False


def html_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUFFIXES:
            continue
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in rel.parts) or is_non_page(rel):
            continue
        yield path


def favicon_block(path: Path) -> str:
    rel = path.relative_to(ROOT)
    depth = len(rel.parent.parts)
    prefix = "../" * depth
    return (
        f'<link rel="shortcut icon" type="image/x-icon" href="{prefix}assets/img/favicon.ico">\n'
        f'<link rel="icon" type="image/png" sizes="256x256" href="{prefix}assets/img/favicon.png">\n'
        f'<link rel="apple-touch-icon" sizes="180x180" href="{prefix}assets/img/apple-touch-icon.png">'
    )


def expected_hrefs(path: Path) -> tuple[str, str, str]:
    rel = path.relative_to(ROOT)
    prefix = "../" * len(rel.parent.parts)
    return (
        f'{prefix}assets/img/favicon.ico',
        f'{prefix}assets/img/favicon.png',
        f'{prefix}assets/img/apple-touch-icon.png',
    )


def inject(text: str, path: Path) -> tuple[str, bool]:
    block = favicon_block(path)
    cleaned = ICON_LINK_RE.sub("", text)

    m = HEAD_CLOSE_RE.search(cleaned)
    if m:
        new = cleaned[:m.start()] + block + "\n" + cleaned[m.start():]
        return new, new != text

    m = HEAD_OPEN_RE.search(cleaned)
    if m:
        new = cleaned[:m.end()] + "\n" + block + cleaned[m.end():]
        return new, new != text

    m = HTML_OPEN_RE.search(cleaned)
    if m:
        new = cleaned[:m.end()] + "\n<head>\n" + block + "\n</head>" + cleaned[m.end():]
        return new, new != text

    return text, False


def validate(path: Path, text: str) -> list[str]:
    problems = []
    hrefs = expected_hrefs(path)
    for href in hrefs:
        if f'href="{href}"' not in text and f"href='{href}'" not in text:
            problems.append(f"missing {href}")
    if len(re.findall(r"rel=[\"'](?:shortcut icon|icon|apple-touch-icon)[\"']", text, re.I)) < 3:
        problems.append("missing standard favicon link set")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Ensure Videha favicon links on every real HTML/HTM page.")
    parser.add_argument("--check", action="store_true", help="Validate only; do not modify files.")
    args = parser.parse_args()

    assets = [
        ROOT / "assets/img/favicon.ico",
        ROOT / "assets/img/favicon.png",
        ROOT / "assets/img/apple-touch-icon.png",
    ]
    missing_assets = [str(p.relative_to(ROOT)) for p in assets if not p.exists()]
    if missing_assets:
        raise SystemExit(f"Missing favicon assets: {missing_assets}")

    scanned = changed = skipped = 0
    failures: list[str] = []
    for path in html_files():
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        if args.check:
            problems = validate(path, text)
            if problems:
                failures.append(f"{path.relative_to(ROOT)}: {', '.join(problems)}")
            continue

        new, did_change = inject(text, path)
        if did_change:
            path.write_text(new, encoding="utf-8")
            changed += 1
        elif not (HEAD_CLOSE_RE.search(text) or HEAD_OPEN_RE.search(text) or HTML_OPEN_RE.search(text)):
            skipped += 1

    if args.check and failures:
        preview = "\n".join(failures[:50])
        extra = f"\n... and {len(failures)-50} more" if len(failures) > 50 else ""
        raise SystemExit(f"Favicon validation failed on {len(failures)} pages:\n{preview}{extra}")

    mode = "validated" if args.check else "updated"
    print(f"Videha favicons {mode}: scanned={scanned}, changed={changed}, skipped={skipped}, failures={len(failures)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
