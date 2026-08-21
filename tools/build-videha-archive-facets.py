#!/usr/bin/env python3
from pathlib import Path
import re, html, json, sys

ROOT=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
SEARCH=ROOT/'search-documents'
OUT=Path(sys.argv[2] if len(sys.argv)>2 else ROOT/'data'/'videha-archive-facets.json').resolve()
DEV=str.maketrans('०१२३४५६७८९','0123456789')
START=[r'(?:ऐ|एहि|अइ|ई)\s*अंक\s*मे?\s*(?:अछि|छै)',r'अंकमे\s*अछि',r'अनुक्रम(?:णिका)?',r'\bContents\b']
STOP=[r'भाषापाक\s+रचना-लेखन',r'विदेह\s+मैथिली\s+पोथी\s+डाउनलोड',r'VIDEHA\s+MAITHILI\s+BOOKS',r'विदेह\s+ई-पत्रिकाक\s+सभटा\s+पुरान\s+अंक',r'Join official Videha',r'विदेह\s+आर\.एस\.एस',r'Go to the link below for download of old issues',r'VIDEHA ARCHIVE\s+विदेह']
ALIASES={
 'Prose':[r'\bगद्य\b',r'\bProse\b'],
 'Poetry':[r'\bपद्य\b',r'\bPoetry\b'],
 'Research':[r'\bशोध\b',r'\bResearch\b',r'आलोचना',r'समीक्षा',r'विमर्श',r'अनुशीलन',r'परिचर्चा'],
 'Book':[r'\bपोथी\b',r'\bBook\b',r'पुस्तक'],
 'Audio/Video':[r'श्रव्य',r'दृश्य',r'\bAudio\b',r'\bVideo\b',r'नाट्य',r'नाटक']
}
NUM=r'[०-९0-9]+'
PREFIX=re.compile(r'^\s*'+NUM+r'(?:\s*[.।]\s*'+NUM+r')*\s*[.।:)\-]?\s*')
SPLIT=re.compile(r'\s+(?='+NUM+r'(?:\s*[.।]\s*'+NUM+r')*\s*[.।:)])')

def main_html(raw):
 m=re.search(r'<main\b[^>]*>(.*?)</main>',raw,re.I|re.S); return m.group(1) if m else raw

def lines_from(raw):
 s=re.sub(r'(?i)<br\s*/?>','\n',raw); s=re.sub(r'(?i)</(?:p|div|li|h[1-6]|tr|section)>','\n',s); s=re.sub(r'<[^>]+>',' ',s); s=html.unescape(s).replace('\r','')
 return [re.sub(r'[\t ]+',' ',x).strip() for x in s.split('\n') if re.sub(r'[\t ]+',' ',x).strip()]

def toc_slice(lines):
 start=0
 for i,line in enumerate(lines[:240]):
  if any(re.search(p,line,re.I) for p in START): start=i; break
 end=min(len(lines),start+220)
 for j in range(start+1,min(len(lines),start+260)):
  if any(re.search(p,lines[j],re.I) for p in STOP): end=j; break
 return lines[start:end]

def meta(raw,key,default=''):
 m=re.search(r'data-pagefind-meta="'+re.escape(key)+r'"\s+content="([^"]*)"',raw,re.I); return html.unescape(m.group(1)) if m else default

def issue(raw,p):
 m=re.search(r'data-pagefind-filter="issue"\s+content="(\d+)"',raw,re.I)
 if m:return int(m.group(1))
 m=re.search(r'(\d+)',p.stem); return int(m.group(1)) if m else None

def year(lines):
 head=' '.join(lines[:90]).translate(DEV); m=re.search(r'(?<!\d)((?:19|20)\d{2})(?!\d)',head); return int(m.group(1)) if m else None

def cat_text(toc):
 out={}; heads=[]
 for i,line in enumerate(toc):
  if re.search(r'(^|\s)[०-९0-9]{1,2}\s*[.।:-]?\s*गद्य\b|^\s*(?:गद्य|Prose)\b',line,re.I): heads.append((i,'Prose'))
  if re.search(r'(^|\s)[०-९0-9]{1,2}\s*[.।:-]?\s*पद्य\b|^\s*(?:पद्य|Poetry)\b',line,re.I): heads.append((i,'Poetry'))
 heads=sorted(set(heads))
 for n,(i,cat) in enumerate(heads):
  j=heads[n+1][0] if n+1<len(heads) else min(len(toc),i+55)
  block=' '.join(toc[i:j])[:2600]
  if block: out[cat]=(out.get(cat,'')+' '+block).strip()
 for cat in ('Research','Book','Audio/Video'):
  bits=[]
  for i,line in enumerate(toc):
   if any(re.search(p,line,re.I) for p in ALIASES[cat]):
    for k in range(max(0,i-1),min(len(toc),i+2)):
     if toc[k] not in bits: bits.append(toc[k])
  txt=' '.join(bits)[:2200]
  if txt: out[cat]=txt
 return out

def authors_titles(toc):
 aa=[];tt=[]
 for line in toc:
  for seg in SPLIT.split(line):
   s=PREFIX.sub('',seg).strip(' .।:;-–—')
   if not s or len(s)>500: continue
   s=re.sub(r'^(?:गद्य|पद्य|Prose|Poetry)\b\s*','',s,flags=re.I).strip(' .।:;-–—')
   if not s: continue
   m=re.match(r'^(.{2,100}?)[\-–—]\s*(.{2,})$',s)
   if m:
    a=re.sub(r'\s+',' ',m.group(1)).strip(' .।:;'); t=re.sub(r'\s+',' ',m.group(2)).strip()
    if 1<=len(a.split())<=12 and len(a)<=100: aa.append(a)
    if 2<=len(t)<=350: tt.append(t)
   else:
    s2=re.sub(r'\s+',' ',s)
    if 1<=len(s2.split())<=10 and len(s2)<=90 and not re.search(r'अंक|वर्ष|मास|ISSN|https?://|www\.',s2,re.I): aa.append(s2)
 def uniq(xs):
  seen=set();out=[]
  for x in xs:
   k=x.casefold()
   if k not in seen:seen.add(k);out.append(x)
  return out
 return uniq(aa),uniq(tt)

entries=[]
for p in sorted(SEARCH.glob('*.html')):
 if not (p.name.startswith('videha-') or p.name.startswith('sadeha-')): continue
 raw=p.read_text('utf-8',errors='replace'); lines=lines_from(main_html(raw)); toc=toc_slice(lines); aa,tt=authors_titles(toc)
 title=meta(raw,'title') or re.sub(r'<[^>]+>',' ',re.search(r'<title>(.*?)</title>',raw,re.I|re.S).group(1) if re.search(r'<title>(.*?)</title>',raw,re.I|re.S) else p.stem).strip()
 pub=meta(raw,'publication') or ('SADEHA' if p.name.startswith('sadeha-') else 'VIDEHA')
 entries.append({'f':'search-documents/'+p.name,'t':title,'p':pub,'i':issue(raw,p),'y':year(lines),
 'a':(' · '.join(aa))[:1800],'tt':(' · '.join(tt))[:1800],'c':cat_text(toc)})
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'version':2,'count':len(entries),'entries':entries},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print(f'Wrote {len(entries)} archive facet rows to {OUT} ({OUT.stat().st_size} bytes)')
