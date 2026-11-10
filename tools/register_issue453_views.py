from pathlib import Path
import json,html
root=Path('.')
d=json.loads((root/'research/data/articles.json').read_text(encoding='utf8'))
a=[x for x in d['articles'] if str(x.get('issue'))=='453']
p=root/'research/index.htm'; s=p.read_text(encoding='utf8')
if 'data-issue="453"' not in s:
 cards=''.join(f'<article class="research-card" data-issue="453" data-language="{html.escape(x.get("language","mai"))}" data-search="{html.escape(x["title"]+" "+x["authors"][0]+" 453",quote=True)}"><h2><a href="{x["url"]}">{html.escape(x["title"])}</a></h2><p>{html.escape(x["authors"][0])} · <a href="https://videha-ejournal.github.io/videha/videha-archive-explorer.html?issue=453">अंक 453</a> · {html.escape(x["classification"])}</p></article>' for x in a)
 s=s.replace('<main id="videha-main">','<main id="videha-main">'+cards,1)
 s=s.replace('970 लेख</strong>','993 लेख</strong>',1)
 p.write_text(s,encoding='utf8')
print('registered',len(a))
