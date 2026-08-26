#!/usr/bin/env python3
"""Write compact diagnostics for known Videha article-boundary edge cases."""
from __future__ import annotations
import json, re
from pathlib import Path
from extract_explicit_research import SourceParser, parse_toc_entries, latin_digits

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research'/'data'/'extractor-diagnostics.json'
TARGETS={'438':'2.5','447':'2.18'}
rows=[]
for issue, wanted in TARGETS.items():
    path=ROOT/'search-documents'/f'videha-{issue}.html'
    raw=path.read_text(encoding='utf-8',errors='ignore')
    p=SourceParser()
    try:p.feed(raw)
    except Exception:pass
    text=p.text(); toc,floor=parse_toc_entries(text)
    item=next((x for x in toc if x['section']==wanted),None)
    d={'issue':issue,'wanted_section':wanted,'body_floor':floor,'toc_count':len(toc)}
    if item:
        d.update({'section_source':item['section_source'],'title':item.get('title'),'author':item.get('author')})
        sec=item['section_source']
        pats=[
            re.compile(rf'(?m)^\s*{re.escape(sec)}\.\s*'),
            re.compile(rf'(?m)^\s*{re.escape(latin_digits(sec))}\.\s*'),
        ]
        occ=[]
        for pi,pat in enumerate(pats):
            for m in pat.finditer(text):
                if len(occ)>=20:break
                occ.append({'pattern':pi,'pos':m.start(),'after_floor':m.start()>=floor,'snippet':text[m.start():m.start()+220].replace('\n',' ')})
        if item.get('title'):
            t=item['title']; start=0; title_occ=[]
            while True:
                pos=text.find(t,start)
                if pos<0:break
                title_occ.append({'pos':pos,'after_floor':pos>=floor,'snippet':text[max(0,pos-80):pos+len(t)+180].replace('\n',' ')})
                start=pos+1
                if len(title_occ)>=12:break
            d['title_occurrences']=title_occ
        d['section_occurrences']=occ
    rows.append(d)
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
print('Boundary diagnostics written for issues 438 and 447')
