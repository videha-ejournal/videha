#!/usr/bin/env python3
"""Static smoke tests for the author publication-certificate widget."""

from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "publication-certificate.html"
CSS = ROOT / "assets" / "css" / "videha-certificate.css"
JS = ROOT / "assets" / "js" / "videha-certificate.js"
QR = [ROOT / "assets" / "img" / "qr-videha-primary.png", ROOT / "assets" / "img" / "qr-videha-github.png"]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def png_size(path):
    data = path.read_bytes()
    require(data[:8] == b"\x89PNG\r\n\x1a\n", f"Invalid PNG: {path.name}")
    return struct.unpack(">II", data[16:24])


def main():
    html = PAGE.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    for required in ["ISSN 2229-547X", "SELF-CERTIFIED", "authorDeclaration", "certificateSheet", "qr-videha-primary.png", "qr-videha-github.png", "https://www.videha.co.in/", "https://videha-ejournal.github.io/videha/"]:
        require(required in html, f"Certificate page is missing {required}")
    for required in ["@media print", "size:A4 landscape", ".vpc-qr-card"]:
        require(required in css, f"Certificate CSS is missing {required}")
    for required in ["PF_CANDIDATES", "KNOWLEDGE_CANDIDATES", "filters:{publication", "canonicalRecord", "window.print()", "self-cert"]:
        require(required.lower() in js.lower(), f"Certificate JavaScript is missing {required}")
    for path in QR:
        width, height = png_size(path)
        require(width == height and width >= 400, f"QR image is too small: {path.name} {width}x{height}")
    print("Publication-certificate widget validation passed: page, print CSS, archive lookup, declaration, and both QR assets present.")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, ValueError) as exc:
        print(f"Publication-certificate validation FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
