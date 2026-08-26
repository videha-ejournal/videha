#!/usr/bin/env python3
"""Summarize the complete Videha article inventory by Scholar classification."""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'research'/'data'/'article-inventory.json'
out=ROOT/'research'/'data'/'candidate-summary.json'
data=json.loads(src.read_text(encoding='utf-8'))
rows=[r for r in data.get('rows',[]) if r.get('scholar_candidate')]
counts=Counter(r.get('classification','unclassified') for r in rows)
strong=[]; weak=[]
for r in rows:
    item={k:r.get(k) for k in ('issue','publication_date','section','author','title','page_start','page_end','body_chars','classification','signals','source_path','source_url')}
    if r.get('classification')!='references-present' and int(r.get('body_chars') or 0)>=1800:
        strong.append(item)
    else:
        weak.append(item)
strong.sort(key=lambda r:(r['classification'] or '',r['publication_date'] or '',r['issue'] or '',r['section'] or ''))
weak.sort(key=lambda r:(-(int(r.get('body_chars') or 0)),r['issue'] or ''))
payload={
    'issue_files_scanned':data.get('issue_files_scanned'),
    'article_entries_inventoried':data.get('article_entries_inventoried'),
    'scholar_candidates':len(rows),
    'classification_counts':dict(sorted(counts.items())),
    'strong_title_based_with_body':len(strong),
    'strong_candidates':strong,
    'weak_or_body_missing_candidates':weak,
}
out.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
print(f"Videha candidate summary: {len(rows)} candidates; {len(strong)} strong title-based candidates with >=1800 body chars")
