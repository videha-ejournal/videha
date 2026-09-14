#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
MONTHS = {
    "जनवरी": "01", "फरवरी": "02", "मार्च": "03", "अप्रैल": "04", "मई": "05", "जून": "06",
    "जुलाई": "07", "अगस्त": "08", "सितम्बर": "09", "सितंबर": "09", "अक्टूबर": "10",
    "नवम्बर": "11", "नवंबर": "11", "दिसम्बर": "12", "दिसंबर": "12",
}


def strip_tags(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def parse_issue(text: str):
    plain = strip_tags(text)
    m = re.search(r"विदेह\s+अंक\s+([०-९0-9]+)\s*\[\s*([०-९0-9]{1,2})\s+([^\s\]]+)\s+([०-९0-9]{4})\s*\]", plain)
    if not m:
        raise SystemExit("Could not find current Videha issue marker in index.htm")
    number_ascii = m.group(1).translate(DIGITS)
    day = m.group(2).translate(DIGITS).zfill(2)
    month = MONTHS.get(m.group(3))
    year = m.group(4).translate(DIGITS)
    if not month:
        raise SystemExit(f"Unknown current-issue month: {m.group(3)}")
    return {
        "issueNumber": int(number_ascii),
        "issueNumberDevanagari": m.group(1),
        "issueDate": f"{year}-{month}-{day}",
        "issueDateDisplay": f"{m.group(2)} {m.group(3)} {m.group(4)}",
    }


def main():
    issue = parse_issue((ROOT / "index.htm").read_text(encoding="utf-8", errors="ignore"))
    manifest = {
        "schemaVersion": 1,
        "publication": "Videha — First Maithili Fortnightly eJournal",
        "publicationMaithili": "विदेह प्रथम मैथिली पाक्षिक ई-पत्रिका",
        "issn": "2229-547X",
        **issue,
        "sourcePage": "https://videha-ejournal.github.io/videha/",
        "canonicalSite": "https://www.videha.co.in/",
        "githubMirror": "https://videha-ejournal.github.io/videha/",
        "status": "published",
        "note": "Generated from the source-controlled mirror index. Main-site parity is verified independently and must not be inferred from this manifest."
    }
    path = ROOT / "current-issue.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print({"currentIssue": issue["issueNumber"], "date": issue["issueDate"], "manifest": str(path)})


if __name__ == "__main__":
    main()
