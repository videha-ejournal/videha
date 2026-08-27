#!/usr/bin/env python3
"""VIDEHA Digital Archive metadata builder (stdlib only).

Regenerates archive, knowledge-graph and deployment manifests from the repo.
Designed for GitHub Actions and local use; no third-party Python packages.
"""
from pathlib import Path
import json,re,datetime,html,collections

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'; DATA.mkdir(exist_ok=True)
DEVA='०१२३४५६७८९'; TRANS=str.maketrans(DEVA,'0123456789')
PRIMARY='https://www.videha.co.in/'
GITHUB='https://videha-ejournal.github.io/videha/'

def digits(s): return str(s or '').translate(TRANS)
def strip_html(s):
    s=re.sub(r'(?i)<(?:br\s*/?|/p|/div|/li|/h[1-6])\s*>','\n',s)
    s=re.sub(r'(?s)<script\b.*?</script>|<style\b.*?</style>',' ',s,flags=re.I)
    s=re.sub(r'(?s)<[^>]+>',' ',s)
    return html.unescape(s).replace('\r','')
def clean(s): return re.sub(r'[ \t\f\v]+',' ',s or '').strip()
def attr(text,tag,attrname):
    m=re.search(fr'(?is)<{tag}\b[^>]*\b{attrname}\s*=\s*["\']([^"\']+)',text)
    return html.unescape(m.group(1)).strip() if m else ''
def title_of(text,default):
    m=re.search(r'(?is)<title[^>]*>(.*?)</title>',text)
    return clean(strip_html(m.group(1))) if m else default

def current_issue():
    p=ROOT/'index.htm'
    if not p.exists(): return None
    t=p.read_text(encoding='utf-8',errors='replace')
    patterns=[
      r'(?is)<div\b[^>]*class=["\'][^"\']*issue-number-square[^"\']*["\'][^>]*>\s*([०-९0-9]{1,4})\s*</div>',
      r'विदेह\s+अंक\s*([०-९0-9]{1,4})',
      r'Current\s+Issue\s*[:#-]?\s*([०-९0-9]{1,4})'
    ]
    for pat in patterns:
        m=re.search(pat,t,re.I)
        if m:
            try:return int(digits(m.group(1)))
            except:pass
    return None

MONTHS_MAI=['जनवरी','फरवरी','मार्च','अप्रैल','मई','जून','जुलाई','अगस्त','सितम्बर','अक्टूबर','नवम्बर','दिसम्बर']
def to_deva(s): return str(s).translate(str.maketrans('0123456789',DEVA))
def videha_issue_date(issue):
    """Deterministic fortnightly calendar anchored at Issue 1 = 01 Jan 2008."""
    if not issue or issue < 1: return ('',None,'')
    zero=issue-1; year=2008+zero//24; slot=zero%24; month=slot//2+1; day=1 if slot%2==0 else 15
    iso=f"{year:04d}-{month:02d}-{day:02d}"
    display=f"{to_deva(f'{day:02d}')} {MONTHS_MAI[month-1]} {to_deva(year)}"
    return display,year,iso

archive=[]
for p in sorted((ROOT/'search-documents').glob('*.html')):
    t=p.read_text(encoding='utf-8',errors='replace')
    title=title_of(t,p.stem)
    pub='SADEHA' if p.name.startswith('sadeha-') else 'VIDEHA'
    im=re.search(r'(?:Issue|अंक)\s*([0-9०-९]+)',title,re.I)
    issue=int(digits(im.group(1))) if im else None
    # SADEHA filenames are authoritative for series number; Sadeha 5 has Version 1 and Version 2.
    if pub=='SADEHA':
        sm=re.match(r'sadeha-(\d{3})(?:-version-(\d+))?$',p.stem,re.I)
        if sm:
            issue=int(sm.group(1)); ver=int(sm.group(2)) if sm.group(2) else None
        else: ver=None
    else:
        vm=re.search(r'version-(\d+)',p.stem,re.I); ver=int(vm.group(1)) if vm else None
    href=attr(t,'a','href')
    # Never infer a publication year from arbitrary OCR/body text.
    if pub=='VIDEHA' and issue:
        date,year,date_iso=videha_issue_date(issue)
    else:
        date,year,date_iso='',None,''
    archive.append({'publication':pub,'issue':issue,'version':ver,'title':title,'file':'search-documents/'+p.name,'source':href,'date':date,'dateISO':date_iso,'year':year})

# Lightweight page metadata (fallback/search/category navigation)
entries=[]
idx=ROOT/'videha-search-index.json'
if idx.exists():
    try:
      j=json.loads(idx.read_text(encoding='utf-8'))
      for e in j.get('entries',j if isinstance(j,list) else []):
        f=e.get('f','')
        if not f or f.startswith('_vti_') or '/_vti_' in f or f.startswith('pagefind/') or f.startswith('search-documents/'):continue
        entries.append({k:e.get(k,'') for k in ('f','t','a','c','y','i','s')})
    except Exception as exc: print('warning: search-index metadata skipped:',exc)

now=datetime.datetime.now(datetime.timezone.utc).isoformat()
cur=current_issue()
maxv=max((x['issue'] or 0 for x in archive if x['publication']=='VIDEHA'),default=0)
sadeha=sum(1 for x in archive if x['publication']=='SADEHA')
manifest={'generated':now,'currentIssue':cur,'archiveMaxVideha':maxv,'archiveSadehaDocuments':sadeha,'archive':archive,'pages':entries,'hosts':{'primary':PRIMARY,'github':GITHUB,'historical':'github'}}
(DATA/'videha-archive-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':')),encoding='utf-8')

# High-precision navigational author/name labels from numbered TOC lines.
# This is deliberately not presented as an authority-controlled identity file.
prefix=re.compile(r'^\s*[०-९0-9]+(?:\s*[.।]\s*[०-९0-9]+)+[.)।]?\s*(.{2,90}?)\s*[-–—]\s*(.{2,180})')
noise=['APPENDIX','VIDEHA','विदेह अंक','अनुक्रम','पद्य','गद्य','POETRY','PROSE','शोध','RESEARCH','DOCUMENTARY','उपन्यास','कथा','कविता','नाटक','गजल','ग़ज़ल','गीत','पोथी','डायरी','समीक्षा','विमर्श','अध्ययन','निबन्ध','निबंध','पत्र','सम्पादकीय','संपादकीय','साक्षात्कार','रिपोर्ट','रिपोर्ताज','चित्र','प्रहसन','व्याकरण','साहित्य','इतिहास','दर्शन','अनुवाद']
dev_tokens=['झा','ठाकुर','मंडल','मण्डल','मिश्र','राय','रॉय','यादव','चौधरी','कापड़ि','कापड़ि','कामत','पासवान','सिंह','दास','शर्मा','शरण','कुमार','कुमारी','देवी','कर्ण','राउत','महतो','साहु','साह','लाल','नाथ','प्रसाद','मनु','मनुज','अनचिन्हार','अमात्य','वियोगी','बटोही','भारद्वाज','कश्यप','सफी','रेणु','सुमन','राज','शास्त्री','शास्‍त्री','खरबंदा','पौड्याल','उत्पल','वर्मा','मल्लिक','मलिक','कान्त','कांत']
lat=re.compile(r'\b(?:Jha|Thakur|Yadav|Yadava|Mandal|Mishra|Singh|Kumar|Kumari|Roy|Rai|Das|Sharma|Choudhary|Chaudhary|Karn|Paswan|Kamat|Verma|Poudyal|Suman|Pathak|Bihari|Manuj|Anchinhar)\b',re.I)
role=re.compile(r'^(?:डॉ\.?|डा\.?|Dr\.?|आचार्य|पं\.?|प्रो\.?|Prof\.?|कवि|लेखक)\s*',re.I)
names=collections.defaultdict(lambda:{'issues':set(),'files':set(),'examples':[]})
def accept_name(c):
    if not (3<=len(c)<=52) or any(n.lower() in c.lower() for n in noise) or any(ch in c for ch in '[]()/='):return False
    if re.search(r'[0-9०-९]|https?|www\.',c,re.I):return False
    haslat=bool(re.search(r'[A-Za-z]',c));hasdev=bool(re.search(r'[\u0900-\u097f]',c))
    if haslat and hasdev:return False
    return any(t in c for t in dev_tokens) or bool(lat.search(c))
def extract_names(text,issue,file):
    raw=strip_html(text[:200000])
    for line in raw.splitlines():
      line=clean(line);m=prefix.match(line)
      if not m:continue
      c=re.sub(r'^[\-–—:;,.\s]+','',m.group(1));c=re.sub(r'^[०-९0-9]+[.)।:-]*\s*','',c);c=role.sub('',c).strip(" '‘’\"“”ँंः -–—")
      if not accept_name(c):continue
      d=names[c];d['issues'].add(issue);d['files'].add(file)
      ex=clean(m.group(2))[:140]
      if ex and len(d['examples'])<3:d['examples'].append(ex)
for x in archive:
    if x['publication']!='VIDEHA':continue
    p=ROOT/x['file']
    try:extract_names(p.read_text(encoding='utf-8',errors='replace'),x['issue'],x['file'])
    except Exception:pass
if (ROOT/'index.htm').exists():extract_names((ROOT/'index.htm').read_text(encoding='utf-8',errors='replace'),cur,'index.htm')
authors=[]
for n,d in sorted(names.items(),key=lambda kv:kv[0].casefold()):
    issues=sorted(i for i in d['issues'] if i)
    years=sorted({videha_issue_date(i)[1] for i in issues if videha_issue_date(i)[1]})
    files=sorted(d['files'])
    authors.append({'name':n,'issues':issues,'years':years,'files':files,'categories':{'Archive TOC':len(files)},'examples':d['examples'],'source':'numbered TOC label extraction'})
cats=collections.Counter((e.get('c') or 'other') for e in entries)
knowledge={'generated':now,'authors':authors,'categories':dict(cats),'note':'High-precision navigational author/name labels automatically extracted from numbered Videha TOC lines; not an authority-controlled identity file.','archive':{'videha':maxv,'currentIssue':cur,'sadehaDocuments':sadeha}}
(DATA/'videha-knowledge-graph.json').write_text(json.dumps(knowledge,ensure_ascii=False,separators=(',',':')),encoding='utf-8')

# Article-level author/title relationships for the publication-certificate finder.
# The inventory is rebuilt from every archived issue and the live index.htm before
# this script runs in CI. Validated Scholar pages are merged as preferred direct URLs.
def publication_key(issue,author,title):
    def norm(value):
        value=str(value or '').casefold().replace('\u200c','').replace('\u200d','')
        return re.sub(r'[^\w\u0900-\u097f]+',' ',value,flags=re.UNICODE).strip()
    return (str(int(issue)) if str(issue).isdigit() else str(issue),norm(author),norm(title))

publication_records=[]; publication_seen={}
inventory_path=ROOT/'research'/'data'/'article-inventory.json'
if inventory_path.exists():
    try:
      inventory=json.loads(inventory_path.read_text(encoding='utf-8'))
      for row in inventory.get('rows',[]):
        issue=str(row.get('issue') or '').strip(); author=clean(row.get('author')); work=clean(row.get('title'))
        if not issue.isdigit() or not author or not work:continue
        source_path=str(row.get('source_path') or f"search-documents/videha-{int(issue):03d}.html")
        archive_url=PRIMARY if source_path=='index.htm' else GITHUB+source_path
        record={'publication':'VIDEHA','issue':int(issue),'version':'','author':author,'title':work,'section':str(row.get('section') or ''),'archiveUrl':archive_url}
        source_url=str(row.get('source_url') or '').strip()
        if source_url:record['sourceUrl']=source_url
        key=publication_key(issue,author,work)
        if key in publication_seen:continue
        publication_seen[key]=len(publication_records);publication_records.append(record)
    except Exception as exc:print('warning: article inventory skipped:',exc)

scholar_path=ROOT/'research'/'data'/'articles.json'
if scholar_path.exists():
    try:
      scholar=json.loads(scholar_path.read_text(encoding='utf-8'))
      for article in scholar.get('articles',scholar if isinstance(scholar,list) else []):
        issue=str(article.get('issue') or '').strip();work=clean(article.get('title'));research_url=str(article.get('url') or '').strip()
        for author in article.get('authors') or []:
          author=clean(author);key=publication_key(issue,author,work)
          if not issue.isdigit() or not author or not work:continue
          if key in publication_seen:
            if research_url:publication_records[publication_seen[key]]['researchUrl']=research_url
          else:
            record={'publication':'VIDEHA','issue':int(issue),'version':'','author':author,'title':work,'section':'','archiveUrl':GITHUB+f"search-documents/videha-{int(issue):03d}.html"}
            if research_url:record['researchUrl']=research_url
            source_url=str(article.get('source_url') or '').strip()
            if source_url:record['sourceUrl']=source_url
            publication_seen[key]=len(publication_records);publication_records.append(record)
    except Exception as exc:print('warning: Scholar publication merge skipped:',exc)
publication_records.sort(key=lambda x:(x['author'].casefold(),-x['issue'],x['title'].casefold()))
publication_index={'generated':now,'count':len(publication_records),'source':'Automatically rebuilt from archived issue TOCs, the live current issue, and validated Videha Scholar metadata. Historical parsing may be incomplete; manual self-certification remains available.','records':publication_records}
(DATA/'videha-author-publications.json').write_text(json.dumps(publication_index,ensure_ascii=False,separators=(',',':')),encoding='utf-8')

deploy={'generated':now,'strategy':{'videha.co.in':{'role':'canonical lightweight publication site','exclude':['pagefind/**','search-documents/**','.github/**','tools/**'],'ordinarySearchResults':'https://www.videha.co.in/<same-path>','historicalSearchResults':GITHUB+'search-documents/<file>'},'github':{'role':'full static archive/search/studio fallback','include':'full package','ordinarySearchResults':GITHUB+'<same-path>','historicalSearchResults':GITHUB+'search-documents/<file>'}},'currentIssue':cur,'historicalThrough':maxv}
(DATA/'videha-deployment.json').write_text(json.dumps(deploy,ensure_ascii=False,indent=2),encoding='utf-8')
print('current',cur,'historical',maxv,'sadeha docs',sadeha,'pages',len(entries),'author labels',len(authors),'author-publications',len(publication_records))
