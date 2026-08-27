#!/usr/bin/env python3
"""Fail fast when the committed document-search corpus is incomplete or malformed."""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "search-documents"
AUDIT = ROOT / "document-search-audit.json"
FIXTURE = ROOT / "data" / "document-search-smoke.json"
TRANSLATOR = ROOT / "assets" / "js" / "videha-translate.js"
ACCESS = ROOT / "assets" / "js" / "videha-access.js"
INDEX = ROOT / "index.htm"
FORBIDDEN = re.compile(r"TEXT\s+NOT\s+EXTRACTABLE|OCR\s+NEEDED", re.IGNORECASE)


def fail(message: str) -> None:
    raise AssertionError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def expected_sadeha_files() -> set[str]:
    names = {f"sadeha-{issue:03d}.html" for issue in range(1, 38) if issue != 5}
    names.update({"sadeha-005-version-1.html", "sadeha-005-version-2.html"})
    return names


def expected_title(filename: str) -> str:
    videha = re.fullmatch(r"videha-(\d{3,}).html", filename)
    if videha:
        issue = int(videha.group(1))
        deva = str(issue).translate(str.maketrans("0123456789", "०१२३४५६७८९"))
        return f"VIDEHA — Issue {issue} / अंक {deva}"
    versioned = re.fullmatch(r"sadeha-005-version-([12]).html", filename)
    if versioned:
        return f"SADEHA — 5, Version {versioned.group(1)}"
    sadeha = re.fullmatch(r"sadeha-(\d{3}).html", filename)
    if sadeha:
        return f"SADEHA — {int(sadeha.group(1))}"
    fail(f"Unexpected generated filename: {filename}")
    return ""


def main() -> int:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    stats = audit["stats"]
    documents = audit["documents"]
    latest = int(audit["latest_videha_issue"])

    require(latest > 0, "latest_videha_issue must be positive")
    require(stats["videha_pdfs"] == latest, "VIDEHA issues must be consecutive from 1 through latest")
    require(stats["sadeha_pdfs"] == 38, "SADEHA must contain 38 files: issues 1–37 plus issue 5 Version 2")
    require(stats["canonical_pdfs"] == stats["videha_pdfs"] + stats["sadeha_pdfs"], "Canonical PDF total is inconsistent")
    require(stats["generated_html_files"] == stats["canonical_pdfs"], "One generated page is required per canonical PDF")
    require(len(documents) == stats["canonical_pdfs"], "Audit document count is inconsistent")

    expected_videha = {f"videha-{issue:03d}.html" for issue in range(1, latest + 1)}
    expected_sadeha = expected_sadeha_files()
    expected_files = expected_videha | expected_sadeha
    actual_paths = sorted(OUTPUT.glob("*.html"))
    actual_files = {path.name for path in actual_paths}
    require(actual_files == expected_files, f"Generated filename mismatch; missing={sorted(expected_files-actual_files)}, extra={sorted(actual_files-expected_files)}")

    audit_outputs = [doc["output"] for doc in documents]
    require(len(audit_outputs) == len(set(audit_outputs)), "Duplicate outputs exist in the audit")
    require(set(audit_outputs) == actual_files, "Audit outputs do not match generated files")
    require(sum(bool(doc["source_count"]) for doc in documents) == stats["paired_documents"], "Paired-document count is inconsistent")
    require(sum(not doc["source_count"] for doc in documents) == stats["pdf_only_documents"], "PDF-only count is inconsistent")
    require(stats["paired_documents"] + stats["pdf_only_documents"] == stats["canonical_pdfs"], "Pair coverage does not cover every document")
    require(not audit["conversion_failures"] and stats["doc_conversion_failures"] == 0, "DOC conversion failures are present")
    require(not audit["unpaired_sources"] and stats["unpaired_source_files"] == 0, "Unpaired source files are present")

    total_bytes = 0
    translator_js = TRANSLATOR.read_text(encoding="utf-8")
    language_block = translator_js.split("var LANG_GROUPS =", 1)[1].split("var LIVE_HOST", 1)[0]
    language_count = len(re.findall(r"\[\s*'[A-Za-z-]+'\s*,\s*'", language_block))
    require(language_count == 41, f"Expected 41 translator languages, found {language_count}")
    require("data-videha-translate-standalone" in translator_js, "Translator lacks archive-page standalone mode")
    index_html = INDEX.read_text(encoding="utf-8")
    access_js = ACCESS.read_text(encoding="utf-8")
    require('assets/js/videha-translate.js?v=20260827' in index_html, "index.htm does not load the current 41-language translator")
    require('assets/js/videha-access.js?v=20260827' in index_html, "index.htm does not load the current assistive-technology panel")
    require("../../script-converter.html" in access_js, "Assistive panel does not resolve the Braille converter from archive pages")
    for path in actual_paths:
        raw = path.read_text(encoding="utf-8")
        total_bytes += path.stat().st_size
        title = expected_title(path.name)
        require(f"<title>{html.escape(title)}</title>" in raw, f"Incorrect title in {path.name}")
        publication = "VIDEHA" if path.name.startswith("videha-") else "SADEHA"
        require(f'data-pagefind-filter="publication[content]" content="{publication}"' in raw, f"Missing publication filter in {path.name}")
        require('data-pagefind-filter="issue[content]"' in raw, f"Missing issue filter in {path.name}")
        require('data-pagefind-filter="videha_type[content]" content="Archive document"' in raw, f"Missing archive type filter in {path.name}")
        require("<main data-pagefind-body>" in raw, f"Missing Pagefind body in {path.name}")
        require('../assets/js/videha-translate.js?v=20260827' in raw, f"Missing 41-language translator in {path.name}")
        require('data-videha-translate-standalone' in raw, f"Missing standalone translator hook in {path.name}")
        require('../assets/js/videha-tts.js?v=20260818-hostfix2' in raw, f"Missing Listen script in {path.name}")
        require('../assets/js/videha-access.js?v=20260827' in raw, f"Missing assistive-technology script in {path.name}")
        require(raw.count('id="videha-tts-toggle"') == 1, f"Missing or duplicate Listen control in {path.name}")
        require(raw.count('id="videha-tts-stop"') == 1, f"Missing or duplicate Stop control in {path.name}")
        require(raw.count('id="videha-tts-status"') == 1, f"Missing or duplicate speech status in {path.name}")
        require(not FORBIDDEN.search(raw), f"Forbidden public placeholder in {path.name}")
        if "version" in path.name:
            version = path.stem[-1]
            require(f'data-pagefind-filter="version[content]" content="{version}"' in raw, f"Missing version filter in {path.name}")
        else:
            require('data-pagefind-filter="version[content]"' not in raw, f"Unexpected version filter in {path.name}")

    require(total_bytes == stats["generated_html_bytes"], "Generated HTML byte total differs from the audit")
    require(all(doc["total_chars"] > 0 for doc in documents), "An empty searchable document exists")

    require(stats["ocr_characters"] > 0, "OCR contributed no searchable text")
    require(any(doc["ocr_chars"] > 0 for doc in documents), "No logical document records OCR text")
    require(0 < stats["ocr_mean_confidence"] <= 100, "OCR confidence is outside the expected range")
    require(stats["unique_embedded_ocr_with_text"] <= stats["unique_embedded_ocr_records"], "Embedded OCR coverage is inconsistent")
    require(stats["unique_pdf_page_ocr_with_text"] <= stats["unique_pdf_page_ocr_records"], "PDF-page OCR coverage is inconsistent")
    require(stats["pdf_pages_ocr"] == stats["pdf_low_text_image_pages"], "A low-text PDF page was not sent through OCR")

    ocr_output = OUTPUT / fixture["ocr"]["expected_output"]
    require(ocr_output.name in actual_files, "OCR smoke-test output is missing")
    require(fixture["ocr"]["query"] in html.unescape(ocr_output.read_text(encoding="utf-8")), "OCR smoke-test phrase is missing from its generated page")

    print(
        "Document-search validation passed: "
        f"{stats['canonical_pdfs']} pages "
        f"({stats['videha_pdfs']} VIDEHA + {stats['sadeha_pdfs']} SADEHA), "
        f"{stats['paired_documents']} paired, {stats['pdf_only_documents']} PDF-only, "
        f"{stats['ocr_characters']} unique OCR characters; Listen, 41-language translation, and assistive controls present."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Document-search validation FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
