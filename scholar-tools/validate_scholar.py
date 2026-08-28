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
    for control in ("videha-tts-toggle","videha-tts-stop","videha-tts-status"):
        if f'id="{control}"' not in s: errors.append(f"{p.relative_to(ROOT)}: missing {control}")
    for script in ("videha-tts.js","videha-translate.js","videha-access.js"):
        if s.count(script) != 1: errors.append(f"{p.relative_to(ROOT)}: expected one {script}")
    if '<main id="videha-main">' not in s: errors.append(f"{p.relative_to(ROOT)}: missing readable main landmark")
index=(ROOT/"research/index.htm").read_text(encoding="utf-8",errors="ignore")
cards=len(re.findall(r'class="research-card"',index))
if cards != checked: errors.append(f"research/index.htm: {cards} cards for {checked} article pages")
for marker in ('id="research-search"','id="research-language"','id="research-count"','videha-tts.js','videha-translate.js','videha-access.js'):
    if marker not in index: errors.append(f"research/index.htm: missing {marker}")
if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"Scholar validation OK: {checked} article pages checked")
