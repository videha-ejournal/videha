from pathlib import Path
import json, html, re
root=Path('research/2026/451')
for p in root.glob('*.htm'):
 s=p.read_text(encoding='utf-8')
 title=re.search(r'<title>(.*?)</title>',s,re.S)
 title=html.unescape(title.group(1).split(' ·')[0]) if title else p.stem
 author=re.search(r'<meta name="citation_author" content="([^"]*)"',s)
 author=html.unescape(author.group(1)) if author else 'गजेन्द्र ठाकुर'
 canonical='https://videha-ejournal.github.io/videha/research/2026/451/'+p.name
 tags=f'<meta name="citation_publication_date" content="2026-09-15"><link rel="canonical" href="{canonical}"><script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@type':'ScholarlyArticle','headline':title,'author':{'@type':'Person','name':author},'datePublished':'2026-09-15','isPartOf':{'@type':'Periodical','name':'Videha','issn':'2229-547X'},'url':canonical},ensure_ascii=False,separators=(',',':'))+'</script>'
 if 'citation_publication_date' not in s: s=s.replace('</head>',tags+'</head>',1)
 p.write_text(s,encoding='utf-8')
for p in [Path('research/index.htm'),Path('research/videha-scholar-research-book.html'),Path('research/data/articles.json')]:
 s=p.read_text(encoding='utf-8').replace('gajendra-thakur-nit-naval-lalita-jha-1.htm','gajendra-thakur-nit-naval-lalita-jha.htm')
 p.write_text(s,encoding='utf-8')
print('metadata fixed',len(list(root.glob('*.htm'))))
