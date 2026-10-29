import json,html
from pathlib import Path
d=json.loads(Path('research/data/articles.json').read_text(encoding='utf8')); a=[x for x in d['articles'] if x.get('issue')=='452']
p=Path('research/index.htm');s=p.read_text(encoding='utf8')
if 'data-issue="452"' not in s:
 cards=''.join(f'<article class="research-card" data-issue="452" data-language="mai" data-search="{html.escape(x["title"]+" "+x["authors"][0]+" 452",quote=True)}"><h2><a href="{x["url"]}">{html.escape(x["title"])}</a></h2><p>{html.escape(x["authors"][0])} · <a href="https://videha-ejournal.github.io/videha/videha-archive-explorer.html?issue=452">अंक 452</a> · {html.escape(x["classification"])}</p></article>' for x in a);s=s.replace('<main id="videha-main">','<main id="videha-main">'+cards,1)
p.write_text(s,encoding='utf8')
p=Path('research/videha-scholar-research-book.html');s=p.read_text(encoding='utf8').replace('923 लेख','970 लेख').replace('मैथिली 867','मैथिली 914')
if 'अंक ४५२ · शोध-लेख' not in s:
 links=''.join(f'<li><a href="{x["url"]}">{html.escape(x["title"])}</a> · {html.escape(x["authors"][0])}</li>' for x in a);s=s.replace('<div class="home-strip">','<h2>अंक ४५२ · शोध-लेख</h2><ul>'+links+'</ul><div class="home-strip">',1)
p.write_text(s,encoding='utf8');print(len(a))
