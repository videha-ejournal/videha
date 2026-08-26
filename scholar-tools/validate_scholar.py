#!/usr/bin/env python3
from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[1]
required=("citation_title","citation_author","citation_publication_date","citation_journal_title","citation_issn","citation_issue")
errors=[]; checked=0
for p in (ROOT/"research").rglob("*.htm"):
    if p.name=="index.htm": continue
    checked+=1; s=p.read_text(encoding="utf-8",errors="ignore")
    for meta in required:
        if not re.search(r'<meta\s+name=["\']'+re.escape(meta)+r'["\']\s+content=["\'][^"\']+',s,re.I): errors.append(f"{p.relative_to(ROOT)}: missing {meta}")
    if 'rel="canonical"' not in s: errors.append(f"{p.relative_to(ROOT)}: missing canonical")
    if 'application/ld+json' not in s: errors.append(f"{p.relative_to(ROOT)}: missing JSON-LD")
    if "2229-547X" not in s: errors.append(f"{p.relative_to(ROOT)}: missing ISSN")
if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"Scholar validation OK: {checked} article pages checked")
