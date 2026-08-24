#!/usr/bin/env python3
"""Build GitHub-only searchable HTML from the local Videha/Sadeha archive.

The canonical PDF names define logical documents. Matching Word components are
combined with each PDF so Pagefind receives one searchable copy, not a PDF and
Word duplicate. Word text is preferred; PDF text fills gaps. Embedded document
images and low-text PDF pages can be OCRed with Tesseract (Hindi + English).
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.parse
import zipfile
from collections import defaultdict
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

DEVANAGARI_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")
WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
ARCHIVE_ITEM = "VidehaAndSadeha"


def digits_devanagari(value: int) -> str:
    return str(value).translate(DEVANAGARI_DIGITS)


def clean_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value or "")
    value = value.replace("\x00", " ").replace("\r", "\n")
    value = re.sub(r"[ \t\f\v]+", " ", value)
    value = re.sub(r"\n[ \t]+", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def command_path(name: str, explicit: str | None = None) -> str | None:
    if explicit and Path(explicit).exists():
        return str(Path(explicit))
    return shutil.which(name)


def parse_identity(path: Path):
    stem = path.stem
    m = re.match(r"(?i)^videha\s*[_ -]?(\d{1,3})(?:\D.*)?$", stem)
    if m:
        return ("videha", int(m.group(1)), None)
    m = re.match(r"(?i)^sadeha\s*[_ -]?(\d{1,2})(?:\s*[_ -]?v(?:ersion)?\s*([12]))?$", stem)
    if m:
        issue = int(m.group(1)); version = int(m.group(2)) if m.group(2) else None
        return ("sadeha", issue, version)
    return None


def discover_canonical_pdfs(pdf_root: Path):
    docs = {}
    for path in sorted(pdf_root.glob("*.pdf")):
        key = parse_identity(path)
        if not key:
            continue
        if key[0] == "sadeha" and key[1] == 5 and key[2] is None:
            raise RuntimeError(f"Sadeha 5 PDF must say v1 or v2: {path.name}")
        if key in docs:
            raise RuntimeError(f"Duplicate canonical PDF identity {key}: {path} and {docs[key]}")
        docs[key] = path
    return docs


def word_identity(path: Path, sadeha_root: Path):
    low = path.stem.lower()
    if "videha" in low:
        m = re.search(r"(?i)videha\s*[_ -]?(\d{1,3})", path.stem)
        if m:
            return ("videha", int(m.group(1)), None)
    try:
        rel = path.relative_to(sadeha_root)
    except ValueError:
        return None
    parts = [p.lower() for p in rel.parts[:-1]]
    if "sadeha_1_2" in parts:
        return ("sadeha", 1, None)
    if "sadeha_2_2" in parts:
        return ("sadeha", 2, None)
    m = re.match(r"(?i)prelim[_ -]?(\d{1,2})(?:[_ -]?v([12]))?$", path.stem)
    if m:
        issue = int(m.group(1)); version = int(m.group(2)) if m.group(2) else None
        if issue == 5 and version is None:
            version = 2
        return ("sadeha", issue, version)
    m = re.match(r"(?i)sadeha[_ -]?(\d{1,2})(?:[_ -]?v([12]))?(?:[_ -][12])?$", path.stem)
    if m:
        issue = int(m.group(1)); version = int(m.group(2)) if m.group(2) else None
        if issue == 5 and version is None:
            version = 1
        return ("sadeha", issue, version)
    return None


def discover_sources(doc_root: Path, canonical):
    sadeha_root = doc_root / "SADEHA_DOCX"
    by_key = defaultdict(list)
    unpaired = []
    for path in sorted(doc_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".doc", ".docx", ".pdf"}:
            continue
        key = word_identity(path, sadeha_root)
        if key in canonical:
            by_key[key].append(path)
        else:
            unpaired.append(path)
    return by_key, unpaired


def convert_docs(paths, cache: Path, soffice: str | None, force=False):
    converted = {}
    doc_paths = [p for p in paths if p.suffix.lower() == ".doc"]
    if doc_paths and not soffice:
        return converted, list(doc_paths)
    groups = defaultdict(list)
    for path in doc_paths:
        token = hashlib.sha1(str(path.parent).encode("utf-8")).hexdigest()[:12]
        groups[token].append(path)
    failures = []
    for token, members in groups.items():
        outdir = cache / "converted" / token
        outdir.mkdir(parents=True, exist_ok=True)
        pending = []
        for path in members:
            out = outdir / (path.stem + ".docx")
            if not force and out.exists() and out.stat().st_mtime_ns >= path.stat().st_mtime_ns:
                converted[path] = out
            else:
                pending.append(path)
        for start in range(0, len(pending), 35):
            batch = pending[start:start + 35]
            cmd = [soffice, "--headless", "--convert-to", "docx", "--outdir", str(outdir)] + [str(p) for p in batch]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=900)
            if proc.returncode:
                failures.extend(batch)
            for path in batch:
                out = outdir / (path.stem + ".docx")
                if out.exists():
                    converted[path] = out
                elif path not in failures:
                    failures.append(path)
    return converted, failures


def extract_docx(path: Path):
    """Return visible Word text plus embedded image payloads."""
    from lxml import etree
    paragraphs = []
    media = []
    with zipfile.ZipFile(path) as zf:
        xml_names = [n for n in zf.namelist() if re.match(r"word/(document|header\d+|footer\d+)\.xml$", n)]
        for name in xml_names:
            try:
                root = etree.fromstring(zf.read(name))
            except Exception:
                continue
            for para in root.iter(WORD_NS + "p"):
                parts = []
                for node in para.iter():
                    if node.tag == WORD_NS + "t" and node.text:
                        parts.append(node.text)
                    elif node.tag in {WORD_NS + "tab"}:
                        parts.append("\t")
                    elif node.tag in {WORD_NS + "br", WORD_NS + "cr"}:
                        parts.append("\n")
                line = clean_text("".join(parts))
                if line:
                    paragraphs.append(line)
        for name in zf.namelist():
            if name.startswith("word/media/") and not name.endswith("/"):
                try:
                    media.append((name, zf.read(name)))
                except Exception:
                    pass
    return clean_text("\n".join(paragraphs)), media


def tesseract_tsv(image: Path, tesseract: str, tessdata: str | None):
    cmd = [tesseract, str(image), "stdout", "-l", "hin+eng", "--psm", "6"]
    if tessdata:
        cmd += ["--tessdata-dir", tessdata]
    cmd += ["tsv"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                          encoding="utf-8", errors="replace", timeout=240)
    if proc.returncode:
        return "", None, proc.stderr[-500:]
    words, confs = [], []
    for line in proc.stdout.splitlines()[1:]:
        cols = line.split("\t", 11)
        if len(cols) < 12:
            continue
        word = cols[11].strip()
        if not word:
            continue
        words.append(word)
        try:
            conf = float(cols[10])
            if conf >= 0:
                confs.append(conf)
        except ValueError:
            pass
    return clean_text(" ".join(words)), (sum(confs) / len(confs) if confs else None), ""


def ocr_image_bytes(data: bytes, suffix: str, cache: Path, tesseract: str | None,
                    tessdata: str | None, stats, force=False):
    digest = hashlib.sha256(data).hexdigest()
    record = cache / "ocr" / (digest + ".json")
    if record.exists() and not force:
        try:
            cached = json.loads(record.read_text(encoding="utf-8"))
            stats["ocr_cache_hits"] += 1
            stats["embedded_images_seen"] += 1
            stats["embedded_images_candidates"] += 1
            stats["embedded_images_ocr"] += 1
            if cached.get("text"):
                stats["embedded_images_with_text"] += 1
            return cached
        except Exception:
            pass
    record.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache / "images" / (digest + (suffix if suffix.startswith(".") else ".png"))
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(data)
    try:
        with Image.open(tmp) as im:
            width, height = im.size
    except Exception:
        return {"text": "", "confidence": None, "width": 0, "height": 0, "error": "unsupported image"}
    stats["embedded_images_seen"] += 1
    if len(data) < 8000 or width * height < 120000 or width < 300 or height < 120:
        stats["embedded_images_skipped_small"] += 1
        return {"text": "", "confidence": None, "width": width, "height": height, "error": "small/decorative"}
    stats["embedded_images_candidates"] += 1
    if not tesseract:
        return {"text": "", "confidence": None, "width": width, "height": height, "error": "tesseract unavailable"}
    text, confidence, error = tesseract_tsv(tmp, tesseract, tessdata)
    result = {"text": text, "confidence": confidence, "width": width, "height": height, "error": error}
    record.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    stats["embedded_images_ocr"] += 1
    if text:
        stats["embedded_images_with_text"] += 1
    return result


def extract_pdf(path: Path, need_full_text: bool, cache: Path, pdftoppm: str | None,
                tesseract: str | None, tessdata: str | None, stats, force=False):
    """Inspect every page; OCR low-text pages that contain raster images."""
    pieces, ocr_pieces = [], []
    try:
        reader = PdfReader(str(path), strict=False)
    except Exception as exc:
        return "", [], {"error": str(exc), "pages": 0, "native_chars": 0, "ocr_pages": 0}
    info = {"error": "", "pages": len(reader.pages), "native_chars": 0, "low_text_pages": 0, "ocr_pages": 0}
    stats["pdf_pages"] += len(reader.pages)
    for idx, page in enumerate(reader.pages):
        try:
            native = clean_text(page.extract_text() or "")
        except Exception:
            native = ""
        info["native_chars"] += len(native)
        stats["pdf_native_chars"] += len(native)
        if need_full_text and native:
            pieces.append(native)
        if len(native) >= 100:
            continue
        try:
            has_image = bool(page.images)
        except Exception:
            has_image = True
        if not has_image:
            continue
        info["low_text_pages"] += 1
        stats["pdf_low_text_image_pages"] += 1
        digest = hashlib.sha256((sha256(path) + f":{idx}").encode()).hexdigest()
        record = cache / "ocr-pages" / (digest + ".json")
        if record.exists() and not force:
            result = json.loads(record.read_text(encoding="utf-8"))
            stats["ocr_cache_hits"] += 1
        elif pdftoppm and tesseract:
            render_dir = cache / "pdf-pages" / digest
            render_dir.mkdir(parents=True, exist_ok=True)
            prefix = render_dir / "page"
            cmd = [pdftoppm, "-f", str(idx + 1), "-l", str(idx + 1), "-r", "180", "-png", "-singlefile", str(path), str(prefix)]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
            image = prefix.with_suffix(".png")
            if proc.returncode == 0 and image.exists():
                text, confidence, error = tesseract_tsv(image, tesseract, tessdata)
                result = {"text": text, "confidence": confidence, "error": error}
            else:
                result = {"text": "", "confidence": None, "error": "PDF render failed"}
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        else:
            result = {"text": "", "confidence": None, "error": "OCR tools unavailable"}
        info["ocr_pages"] += 1
        stats["pdf_pages_ocr"] += 1
        text = clean_text(result.get("text", ""))
        if text:
            stats["pdf_ocr_pages_with_text"] += 1
            ocr_pieces.append(text)
    return clean_text("\n\n".join(pieces)), ocr_pieces, info


def title_for(key):
    pub, issue, version = key
    if pub == "videha":
        return f"VIDEHA — Issue {issue} / अंक {digits_devanagari(issue)}"
    if version:
        return f"SADEHA — {issue}, Version {version}"
    return f"SADEHA — {issue}"


def output_name(key):
    pub, issue, version = key
    tail = f"-version-{version}" if version else ""
    return f"{pub}-{issue:03d}{tail}.html"


def archive_url(pdf: Path):
    return f"https://archive.org/download/{ARCHIVE_ITEM}/{urllib.parse.quote(pdf.name)}"


def render_html(key, pdf: Path, text: str, source_names, extraction_note: str):
    pub, issue, version = key
    title = title_for(key)
    body = "\n".join(f"<p>{html.escape(p)}</p>" for p in re.split(r"\n{2,}", text) if p.strip())
    source = archive_url(pdf)
    version_meta = f'<meta data-pagefind-filter="version[content]" content="{version}">' if version else ""
    return f'''<!doctype html>
<html lang="mai-Deva">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="robots" content="index,follow">
<meta data-pagefind-meta="title" content="{html.escape(title, quote=True)}">
<meta data-pagefind-meta="publication" content="{pub.upper()}">
<meta data-pagefind-filter="publication[content]" content="{pub.upper()}">
<meta data-pagefind-filter="issue[content]" content="{issue}">
<meta data-pagefind-filter="videha_type[content]" content="Archive document">
{version_meta}
<style>body{{max-width:78rem;margin:auto;padding:1.2rem;font:18px/1.65 Georgia,"Noto Serif Devanagari",serif;color:#241a14}}header{{border-bottom:2px solid #8a2f21;margin-bottom:1.5rem}}h1{{color:#7b241c}}.source{{background:#f7efe5;padding:.9rem;border-radius:.4rem}}main p{{white-space:pre-wrap}}a{{color:#7b241c}}</style>
</head>
<body>
<header><h1>{html.escape(title)}</h1><p class="source"><strong>Publication:</strong> {pub.upper()} · <strong>Issue:</strong> {issue}{' · <strong>Version:</strong> '+str(version) if version else ''}<br><a href="{html.escape(source, quote=True)}">Open original PDF at Internet Archive</a></p></header>
<main data-pagefind-body>
{body}
</main>
<footer data-pagefind-ignore="all"><p>Search transcription built from paired local source files: {html.escape(', '.join(source_names))}. {html.escape(extraction_note)}</p></footer>
</body></html>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=Path, help="Github_VIDEHA_SADEHA_PDF_DOCX folder")
    parser.add_argument("--output", type=Path, default=Path("search-documents"))
    parser.add_argument("--cache", type=Path, default=Path(".search-cache"))
    parser.add_argument("--report", type=Path, default=Path("document-search-audit.json"))
    parser.add_argument("--no-ocr", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--tesseract")
    parser.add_argument("--tessdata", type=Path)
    parser.add_argument("--pdftoppm")
    args = parser.parse_args()

    started = time.time()
    corpus = args.corpus.resolve()
    pdf_root = corpus / "VIDEHA_SADEHA_PDF"
    doc_root = corpus / "VIDEHA_SADEHA_DOC_DOCX"
    if not pdf_root.is_dir() or not doc_root.is_dir():
        parser.error("corpus must contain VIDEHA_SADEHA_PDF and VIDEHA_SADEHA_DOC_DOCX")
    canonical = discover_canonical_pdfs(pdf_root)
    expected_v = {i for i in range(1, max(k[1] for k in canonical if k[0] == "videha") + 1)}
    found_v = {k[1] for k in canonical if k[0] == "videha"}
    found_s = {k[1] for k in canonical if k[0] == "sadeha"}
    if expected_v != found_v:
        raise RuntimeError(f"Videha PDF sequence has gaps: {sorted(expected_v - found_v)}")
    if found_s != set(range(1, 38)) or len([k for k in canonical if k[0] == "sadeha"]) != 38:
        raise RuntimeError("Expected Sadeha 1-37 and exactly two Sadeha 5 versions (38 PDFs)")
    if {k[2] for k in canonical if k[:2] == ("sadeha", 5)} != {1, 2}:
        raise RuntimeError("Sadeha 5 must be Version 1 and Version 2")

    sources, unpaired = discover_sources(doc_root, canonical)
    all_sources = [p for members in sources.values() for p in members]
    soffice = command_path("soffice") or command_path("libreoffice")
    converted, conversion_failures = convert_docs(all_sources, args.cache.resolve(), soffice, args.force)
    tesseract = None if args.no_ocr else command_path("tesseract", args.tesseract)
    pdftoppm = None if args.no_ocr else command_path("pdftoppm", args.pdftoppm)
    tessdata = str(args.tessdata.resolve()) if args.tessdata else None

    stats = defaultdict(int)
    stats["canonical_pdfs"] = len(canonical)
    stats["videha_pdfs"] = len([k for k in canonical if k[0] == "videha"])
    stats["sadeha_pdfs"] = len([k for k in canonical if k[0] == "sadeha"])
    stats["paired_documents"] = len([k for k in canonical if sources.get(k)])
    stats["pdf_only_documents"] = len(canonical) - stats["paired_documents"]
    stats["word_source_files"] = len([p for p in all_sources if p.suffix.lower() in {".doc", ".docx"}])
    stats["supplemental_pdf_files"] = len([p for p in all_sources if p.suffix.lower() == ".pdf"])
    stats["doc_converted"] = len(converted)
    stats["doc_conversion_failures"] = len(conversion_failures)

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    expected_outputs = set()
    document_rows = []
    for ordinal, key in enumerate(sorted(canonical), 1):
        pdf = canonical[key]
        native_parts, ocr_parts, source_names = [], [], []
        image_confidences = []
        for source_path in sources.get(key, []):
            source_names.append(source_path.name)
            if source_path.suffix.lower() == ".pdf":
                continue
            docx = source_path if source_path.suffix.lower() == ".docx" else converted.get(source_path)
            if not docx:
                continue
            try:
                doc_text, media = extract_docx(docx)
            except Exception:
                stats["docx_read_failures"] += 1
                continue
            if doc_text:
                native_parts.append(doc_text)
                stats["word_native_chars"] += len(doc_text)
            seen_media = set()
            for media_name, data in media:
                digest = hashlib.sha256(data).hexdigest()
                if digest in seen_media:
                    continue
                seen_media.add(digest)
                result = ocr_image_bytes(data, Path(media_name).suffix, args.cache.resolve(), tesseract, tessdata, stats, args.force)
                if result.get("text"):
                    ocr_parts.append(result["text"])
                    if result.get("confidence") is not None:
                        image_confidences.append(result["confidence"])
        need_pdf_text = len(clean_text("\n".join(native_parts))) < 500
        pdf_text, pdf_ocr, pdf_info = extract_pdf(pdf, need_pdf_text, args.cache.resolve(), pdftoppm,
                                                   tesseract, tessdata, stats, args.force)
        if pdf_text:
            native_parts.append(pdf_text)
        ocr_parts.extend(pdf_ocr)
        # Avoid repeated OCR/native blocks from split documents while retaining order.
        blocks, seen = [], set()
        for block in native_parts + ocr_parts:
            cleaned = clean_text(block)
            if not cleaned:
                continue
            marker = hashlib.sha1(cleaned.encode("utf-8")).hexdigest()
            if marker not in seen:
                seen.add(marker); blocks.append(cleaned)
        combined = clean_text("\n\n".join(blocks))
        if not combined:
            stats["documents_without_text"] += 1
        stats["generated_text_chars"] += len(combined)
        out = output / output_name(key)
        expected_outputs.add(out.name)
        label_sources = source_names or [pdf.name]
        note = "Native Word text preferred; PDF text and OCR added where needed."
        out.write_text(render_html(key, pdf, combined, label_sources, note), encoding="utf-8", newline="\n")
        document_rows.append({
            "key": list(key), "label": title_for(key), "output": out.name, "pdf": pdf.name,
            "source_count": len(sources.get(key, [])), "native_chars": sum(len(x) for x in native_parts),
            "ocr_chars": sum(len(x) for x in ocr_parts), "total_chars": len(combined),
            "pdf_pages": pdf_info["pages"], "pdf_low_text_pages": pdf_info.get("low_text_pages", 0),
            "pdf_ocr_pages": pdf_info.get("ocr_pages", 0),
            "image_ocr_mean_confidence": (sum(image_confidences) / len(image_confidences) if image_confidences else None),
        })
        if ordinal % 25 == 0:
            print(f"Built {ordinal}/{len(canonical)} documents", flush=True)
    stale = []
    for path in output.glob("*.html"):
        if path.name not in expected_outputs:
            path.unlink(); stale.append(path.name)
    stats["generated_html_files"] = len(expected_outputs)
    stats["generated_html_bytes"] = sum((output / name).stat().st_size for name in expected_outputs)
    stats["stale_outputs_removed"] = len(stale)
    stats["unpaired_source_files"] = len(unpaired)
    embedded_records = []
    pdf_page_records = []
    for record in (args.cache.resolve() / "ocr").glob("*.json"):
        try: embedded_records.append(json.loads(record.read_text(encoding="utf-8")))
        except Exception: pass
    for record in (args.cache.resolve() / "ocr-pages").glob("*.json"):
        try: pdf_page_records.append(json.loads(record.read_text(encoding="utf-8")))
        except Exception: pass
    stats["unique_embedded_ocr_records"] = len(embedded_records)
    stats["unique_embedded_ocr_with_text"] = sum(bool(r.get("text")) for r in embedded_records)
    stats["unique_pdf_page_ocr_records"] = len(pdf_page_records)
    stats["unique_pdf_page_ocr_with_text"] = sum(bool(r.get("text")) for r in pdf_page_records)
    stats["ocr_characters"] = sum(len(r.get("text", "")) for r in embedded_records + pdf_page_records)
    confidences = [r["confidence"] for r in embedded_records + pdf_page_records if r.get("confidence") is not None]
    stats["ocr_mean_confidence"] = (sum(confidences) / len(confidences) if confidences else None)

    report = {
        "schema": 1,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(time.time() - started, 2),
        "corpus": str(corpus),
        "latest_videha_issue": max(found_v),
        "sadeha_rule": "Sadeha 1-37; only Sadeha 5 has Version 1 and Version 2",
        "tools": {"soffice": soffice, "tesseract": tesseract, "tessdata": tessdata, "pdftoppm": pdftoppm},
        "stats": dict(stats),
        "conversion_failures": [str(p) for p in conversion_failures],
        "unpaired_sources": [str(p) for p in unpaired],
        "stale_outputs_removed": stale,
        "documents": document_rows,
    }
    args.report.resolve().write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps({"latest_videha_issue": report["latest_videha_issue"], "stats": dict(stats)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
