#!/usr/bin/env python3
"""Prepare a temporary Videha HTML corpus for Pagefind.
Source pages stay untouched. The temporary copy receives search-only metadata/filters.
Both legacy .htm and newer .html pages are included.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import html, re, shutil, sys

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
DST = Path(sys.argv[2] if len(sys.argv) > 2 else '_pagefind_build').resolve()
EXCLUDE = {'pagefind', '_pagefind_build', '.git', 'node_modules'}
DEV = str.maketrans('०१२३४५६७८९', '0123456789')

class Anchors(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self._href=None; self._parts=[]
    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            self._href = dict(attrs).get('href'); self._parts=[]
    def handle_data(self, data):
        if self._href is not None: self._parts.append(data)
    def handle_endtag(self, tag):
        if tag.lower() == 'a' and self._href is not None:
            self.rows.append((self._href, re.sub(r'\s+', ' ', ''.join(self._parts)).strip()))
            self._href=None; self._parts=[]

def read(p):
    try: return p.read_text(encoding='utf-8', errors='replace')
    except Exception: return ''

def normalize_rel(base_path, href):
    h = html.unescape(href or '').strip()
    if not h or h.startswith(('#','mailto:','tel:','javascript:','data:')): return None
    u = urlsplit(h)
    if u.scheme or u.netloc: return None
    raw = unquote(u.path)
    if not raw: return None
    if raw.startswith('/videha/'): raw = raw[len('/videha/'):]
    elif raw.startswith('/'): raw = raw[1:]
    parts = []
    virtual = list(Path(base_path).parent.parts) + raw.replace('\\','/').split('/')
    for bit in virtual:
        if bit in ('', '.'): continue
        if bit == '..':
            if parts: parts.pop()
        else: parts.append(bit)
    return '/'.join(parts)

def anchors_from(rel):
    p=SRC/rel
    if not p.exists(): return []
    a=Anchors()
    try: a.feed(read(p))
    except Exception: pass
    out=[]
    for href,label in a.rows:
        t=normalize_rel(rel,href)
        if t and t.lower().endswith(('.htm','.html')): out.append((t,label))
    return out

def anchors_from_text(base_rel, raw):
    a=Anchors()
    try: a.feed(raw)
    except Exception: pass
    out=[]
    for href,label in a.rows:
        t=normalize_rel(base_rel,href)
        if t and t.lower().endswith(('.htm','.html')): out.append((t,label))
    return out

def clean_label(label):
    s=re.sub(r'\s+',' ',label or '').strip()
    # remove article numbering like २.१५., 1.2., ४४८ etc. only when followed by text
    s=re.sub(r'^[०-९0-9]+(?:\s*[.।:-]\s*[०-९0-9]+)*\s*[.।:-]?\s*(?=[^०-९0-9])','',s).strip()
    return s

def split_author_title(label):
    s=clean_label(label)
    if not s: return None, None
    # Videha listing convention is commonly “Author- Title”.
    m=re.match(r'^(.{2,90}?)[\-–—]\s+(.{2,})$',s)
    if not m: m=re.match(r'^(.{2,90}?)[\-–—](.{3,})$',s)
    if m:
        a=re.sub(r'\s+',' ',m.group(1)).strip(' .:;।')
        t=re.sub(r'\s+',' ',m.group(2)).strip()
        # avoid treating long sentence fragments as an author name
        if 1 <= len(a.split()) <= 10 and len(a) <= 90: return a,t
    return None,s

hub_types={
 'prose.htm':'Prose','verse.htm':'Poetry','discovery.htm':'Research','investigation.htm':'Research',
 'gajenthakur.htm':'Research','pothi.htm':'Book','Audio_Video.htm':'Audio/Video',
 'panji-mool-index.html':'Panji','maithili-thesaurus.html':'Thesaurus',
 'maithili-translator.html':'Dictionary'
}
inbound={}; labels={}; authors={}

def remember(target,label,typ=None):
    if typ: inbound.setdefault(target,set()).add(typ)
    a,t=split_author_title(label)
    if t and len(t)>2:
        # Prefer richer listing labels, but do not let generic navigation titles replace article titles.
        old=labels.get(target,'')
        if (a and not split_author_title(old)[0]) or (not old) or (len(t)>len(old) and len(t)<260): labels[target]=t
    if a: authors.setdefault(target,set()).add(a)

for hub,typ in hub_types.items():
    inbound.setdefault(hub,set()).add(typ)
    for target,label in anchors_from(hub): remember(target,label,typ)

# Current issue: only links inside the live issue block are current-issue articles.
# The same canonical filenames are reused fortnightly, so issue/year must be inherited
# dynamically from index.htm rather than hardcoded.
index_raw=read(SRC/'index.htm')
current_issue=None; current_year=None; current_targets=set()
m=re.search(r'issue-number-square[^>]*>\s*([०-९0-9]{1,4})',index_raw,re.I)
if m: current_issue=int(m.group(1).translate(DEV))
# Prefer the date/year adjacent to the live issue number, not copyright/navigation years.
if m:
    near=re.sub(r'<[^>]+>',' ',html.unescape(index_raw[m.start():m.start()+5000])).translate(DEV)
    ym=re.search(r'(?<!\d)((?:19|20)\d{2})(?!\d)',near)
    if ym: current_year=int(ym.group(1))
# The current issue block is explicitly delimited in the canonical index page.
cm=re.search(r'<!--\s*Current Issue Block\s*-->(.*?)(?:<!--\s*Archive-style paired numbered tabs\s*-->|<h2[^>]*>\s*पेटार\s*/\s*Archive)',index_raw,re.I|re.S)
current_block=cm.group(1) if cm else ''
for target,label in anchors_from_text('index.htm',current_block):
    current_targets.add(target); remember(target,label,None)
# The landing page itself is also part of the live issue.
current_targets.add('index.htm')

# Parallel History is a permanent 100-part series, distinct from the live issue.
parallel_targets=set()
for target,label in anchors_from('gajenthakur.htm'):
    if re.fullmatch(r'new_page_(?:[1-9]|[1-9][0-9]|100)\.htm',target,re.I):
        parallel_targets.add(target); remember(target,label,'Research')
parallel_targets.add('gajenthakur.htm')

# Keep general index-page links as title/author hints only after current links are captured.
for target,label in anchors_from('index.htm'):
    if target not in current_targets: remember(target,label,None)

# eLearning: mark links that explicitly look like quizzes and preserve listing titles/authors.
for target,label in anchors_from('videha-elearning.htm'):
    remember(target,label,'Quiz' if ('quiz' in target.lower() or 'syllabus' in target.lower() or re.search(r'quiz|क्विज|प्रश्नोत्तरी',label,re.I)) else None)

def classify(rel, raw):
    types=set(inbound.get(rel,set())); low=rel.lower()
    # Prefer repository structure and hub-link provenance. Body-text keyword classification
    # is intentionally avoided because Videha navigation repeats tool names on many pages.
    if 'quiz' in low or 'syllabus' in low: types.add('Quiz')
    if 'panji' in low: types.add('Panji')
    if 'thesaurus' in low: types.add('Thesaurus')
    if 'dictionary' in low or 'translator' in low: types.add('Dictionary')
    if 'audio' in low or 'video' in low: types.add('Audio/Video')
    if low=='prose.htm': types.add('Prose')
    if low=='verse.htm': types.add('Poetry')
    if low in ('discovery.htm','investigation.htm','gajenthakur.htm'): types.add('Research')
    if low=='pothi.htm': types.add('Book')
    return sorted(types)

def meta_tags(rel, raw):
    plain=re.sub(r'<[^>]+>',' ',raw).translate(DEV)
    tags=[]
    for typ in classify(rel,raw):
        tags.append(f'<meta data-pagefind-filter="videha_type[content]" content="{html.escape(typ,quote=True)}">')

    # Search-result source heading. This metadata lives only in the temporary
    # Pagefind corpus; canonical public HTML remains unchanged/lightweight.
    source_label=None
    if rel in current_targets:
        source_label='CURRENT ISSUE नूतन अंक'
    elif rel in parallel_targets:
        source_label='PARALLEL HISTORY / समानान्तर इतिहास'
    elif rel.startswith('search-documents/videha-'):
        source_label='VIDEHA ARCHIVE / विदेह पुरान अंक'
    elif rel.startswith('search-documents/sadeha-'):
        source_label='SADEHA ARCHIVE / सदेह'
    else:
        source_label='VIDEHA SITE / स्थायी पृष्ठ'
    tags.append(f'<meta data-pagefind-meta="source[content]" content="{html.escape(source_label,quote=True)}">')
    tags.append(f'<meta data-pagefind-filter="source[content]" content="{html.escape(source_label,quote=True)}">')

    # Prefix result titles for the two special live/permanent series so the
    # existing embedded UI shows the requested heading without heavier JS.
    if rel in current_targets:
        base=labels.get(rel,'')
        if rel=='index.htm':
            base=(f'VIDEHA Issue {current_issue} / विदेह अंक {current_issue}' if current_issue else 'VIDEHA')
        title=f'CURRENT ISSUE नूतन अंक — {base}' if base else 'CURRENT ISSUE नूतन अंक'
        tags.append(f'<meta data-pagefind-meta="title[content]" content="{html.escape(title,quote=True)}">')
    elif rel in parallel_targets:
        part=labels.get(rel,'')
        title=f'PARALLEL HISTORY / समानान्तर इतिहास — {part}' if part else 'PARALLEL HISTORY / समानान्तर इतिहास'
        tags.append(f'<meta data-pagefind-meta="title[content]" content="{html.escape(title,quote=True)}">')
    elif rel in labels and rel not in hub_types and rel != 'index.htm':
        tags.append(f'<meta data-pagefind-meta="title[content]" content="{html.escape(labels[rel],quote=True)}">')
    if rel in authors and rel not in hub_types and rel != 'index.htm':
        # metadata is one display value; filters can carry every discovered author value.
        display=sorted(authors[rel],key=len)[0]
        tags.append(f'<meta data-pagefind-meta="author[content]" content="{html.escape(display,quote=True)}">')
        for a in sorted(authors[rel]):
            tags.append(f'<meta data-pagefind-filter="author[content]" content="{html.escape(a,quote=True)}">')
    # Generated archive pages already carry authoritative issue/publication metadata
    # from build-document-search.py. Do not add heuristic issue/year values to them.
    if rel.startswith('search-documents/'):
        return '\n'.join(tags)

    # Issue/year filters use the page's leading/current-issue context rather than every
    # historical year/issue mentioned in long navigation and copyright blocks.
    # Current article pages inherit these values from index.htm because their own
    # bodies intentionally keep stable filenames and may contain older years.
    issue=current_issue if rel in current_targets else None; issue_pos=None
    m=None if issue is not None else re.search(r'issue-number-square[^>]*>\s*([०-९0-9]{1,4})',raw,re.I)
    if m:
        issue=int(m.group(1).translate(DEV)); issue_pos=m.start()
    elif issue is None:
        visible_head=re.sub(r'<[^>]+>',' ',html.unescape(raw[:30000])).translate(DEV)
        m=re.search(r'(?:विदेह\s*)?अंक\s*([0-9]{1,4})',visible_head,re.I)
        if m: issue=int(m.group(1))
    if issue: tags.append(f'<meta data-pagefind-filter="issue[content]" content="{issue}">')
    if rel in current_targets and current_year:
        tags.append(f'<meta data-pagefind-filter="year[content]" content="{current_year}">')
    else:
        year_source=raw[issue_pos:issue_pos+7000] if issue_pos is not None else raw[:30000]
        head_plain=re.sub(r'<[^>]+>',' ',html.unescape(year_source)).translate(DEV)
        years=re.findall(r'(?<!\d)((?:19|20)\d{2})(?!\d)',head_plain)
        if years: tags.append(f'<meta data-pagefind-filter="year[content]" content="{years[0]}">')
    return '\n'.join(tags)

if DST.exists(): shutil.rmtree(DST)
DST.mkdir(parents=True)
count=0
for p in SRC.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in ('.htm','.html'): continue
    rel=p.relative_to(SRC)
    if any(part in EXCLUDE for part in rel.parts): continue
    if rel.name=='videha-site-auditor.html': continue
    raw=read(p)
    # Keep the index unified: many legacy Videha pages predate consistent language tags.
    if re.search(r'<html\b',raw,re.I):
        if re.search(r'<html\b[^>]*\blang\s*=',raw,re.I):
            raw=re.sub(r'(<html\b[^>]*\blang\s*=\s*["\'])[^"\']*(["\'])',r'\1mai\2',raw,count=1,flags=re.I)
        else: raw=re.sub(r'<html\b','<html lang="mai"',raw,count=1,flags=re.I)
    # Pagefind treats data-pagefind-body as a site-wide opt-in: once any page uses it,
    # pages without it are excluded. Generated archive pages already use the marker
    # on <main>; add it to <body> only in these temporary copies for canonical pages.
    # Public/canonical source HTML remains untouched.
    if 'data-pagefind-body' not in raw and re.search(r'<body\b', raw, re.I):
        raw=re.sub(r'<body\b', '<body data-pagefind-body', raw, count=1, flags=re.I)

    m=meta_tags(rel.as_posix(),raw)
    if m:
        if re.search(r'</head\s*>',raw,re.I): raw=re.sub(r'</head\s*>',m+'\n</head>',raw,count=1,flags=re.I)
        else: raw=m+'\n'+raw
    dest=DST/rel; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_text(raw,encoding='utf-8'); count+=1
print(f'Prepared {count} HTML/HTM files for Pagefind at {DST}')
print(f'Current issue: {current_issue or "unknown"}; year: {current_year or "unknown"}; current pages: {len(current_targets)}')
print(f'Parallel History pages: {len(parallel_targets)}')
print(f'Article title metadata: {len(labels)} pages; author metadata: {len(authors)} pages')
