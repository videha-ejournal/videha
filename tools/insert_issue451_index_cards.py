import json, html
from pathlib import Path
p=Path('research/index.htm'); s=p.read_text(encoding='utf-8')
d=json.loads(Path('research/data/articles.json').read_text(encoding='utf-8'))
items=[x for x in d['articles'] if x.get('issue')=='451']
if 'data-issue="451"' not in s:
 cards=''.join(f'<article class="research-card" data-issue="451" data-language="{x["language"]}" data-search="{html.escape(x["title"]+" "+" ".join(x["authors"])+" 451",quote=True)}"><h2><a href="{x["url"]}">{html.escape(x["title"])}</a></h2><p>{html.escape(x["authors"][0])} · अंक 451 · {html.escape(x["classification"])}</p></article>' for x in items)
 s=s.replace('<p id="research-empty"',cards+'<p id="research-empty"',1)
 p.write_text(s,encoding='utf-8'); print('cards',len(items))
