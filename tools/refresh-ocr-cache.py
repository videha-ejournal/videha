#!/usr/bin/env python3
"""Re-run cached OCR candidates in parallel and store text/confidence JSON.

This is useful after adding or updating Tesseract language/configuration files.
It operates only on the ignored `.search-cache` artifacts produced by
`build-document-search.py`; source documents and public HTML are untouched.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def clean_text(value: str) -> str:
    value = re.sub(r"[ \t\f\v]+", " ", value or "")
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def recognize(task, tesseract: Path, tessdata: Path):
    record, image = task
    old = {}
    try:
        old = json.loads(record.read_text(encoding="utf-8"))
    except Exception:
        pass
    cmd = [str(tesseract), str(image), "stdout", "-l", "hin+eng", "--psm", "6",
           "--tessdata-dir", str(tessdata), "tsv"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                          encoding="utf-8", errors="replace", timeout=300)
    words, confs = [], []
    if proc.returncode == 0:
        for line in proc.stdout.splitlines()[1:]:
            cols = line.split("\t", 11)
            if len(cols) < 12 or not cols[11].strip():
                continue
            words.append(cols[11].strip())
            try:
                conf = float(cols[10])
                if conf >= 0:
                    confs.append(conf)
            except ValueError:
                pass
    old.update({
        "text": clean_text(" ".join(words)),
        "confidence": (sum(confs) / len(confs) if confs else None),
        "error": "" if proc.returncode == 0 else proc.stderr[-1000:],
    })
    record.write_text(json.dumps(old, ensure_ascii=False), encoding="utf-8")
    return bool(old["text"]), len(old["text"]), old["confidence"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", type=Path, default=Path(".search-cache"))
    ap.add_argument("--tesseract", type=Path, required=True)
    ap.add_argument("--tessdata", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    cache = args.cache.resolve()
    image_by_stem = {p.stem: p for p in (cache / "images").glob("*") if p.is_file()}
    tasks = []
    missing = []
    for record in (cache / "ocr").glob("*.json"):
        image = image_by_stem.get(record.stem)
        (tasks if image else missing).append((record, image) if image else str(record))
    for record in (cache / "ocr-pages").glob("*.json"):
        image = cache / "pdf-pages" / record.stem / "page.png"
        (tasks if image.exists() else missing).append((record, image) if image.exists() else str(record))
    print(f"OCR tasks: {len(tasks)}; missing cached images: {len(missing)}", flush=True)
    with_text = chars = completed = 0
    confidences = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(recognize, task, args.tesseract.resolve(), args.tessdata.resolve()) for task in tasks]
        for future in as_completed(futures):
            completed += 1
            try:
                has_text, count, confidence = future.result()
                with_text += int(has_text); chars += count
                if confidence is not None:
                    confidences.append(confidence)
            except Exception as exc:
                print(f"OCR task failed: {exc}", flush=True)
            if completed % 100 == 0:
                print(f"Refreshed {completed}/{len(tasks)}", flush=True)
    print(json.dumps({
        "tasks": len(tasks), "missing_images": len(missing), "records_with_text": with_text,
        "ocr_characters": chars,
        "mean_confidence": (sum(confidences) / len(confidences) if confidences else None),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
