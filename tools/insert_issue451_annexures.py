import json, html
from pathlib import Path
p=Path('research/videha-scholar-research-book.html'); s=p.read_text(encoding='utf-8')
d=json.loads(Path('research/data/articles.json').read_text(encoding='utf-8'))
a=[x for x in d['articles'] if x.get('issue')=='451']
rows=''.join(f'<tr><td>{i}</td><td>{html.escape(x["authors"][0])}</td><td><a href="{x["url"]}">{html.escape(x["title"])}</a></td><td>{html.escape(x["classification"])}</td><td>अंक 451</td></tr>' for i,x in enumerate(a,1))
def block(id_,label):
 return f'<h2 id="{id_}">अंक ४५१ · {label} २५ शोध-लेख</h2><table><thead><tr><th>क्रम</th><th>लेखक</th><th>लेख</th><th>विधा</th><th>अंक</th></tr></thead><tbody>{rows}</tbody></table>'
if 'id="issue-451-author"' not in s:
 s=s.replace('<h2>अनुलग्नक १ : लेखकानुक्रमेण सम्पूर्ण सूची</h2>',block('issue-451-author','लेखकानुक्रमेण')+'<h2>अनुलग्नक १ : लेखकानुक्रमेण सम्पूर्ण सूची</h2>',1)
if 'id="issue-451-genre"' not in s:
 s=s.replace('<h2>अनुलग्नक २ : विधावार सम्पूर्ण सूची</h2>',block('issue-451-genre','विधावार')+'<h2>अनुलग्नक २ : विधावार सम्पूर्ण सूची</h2>',1)
s=s.replace('918 लेख','923 लेख')
p.write_text(s,encoding='utf-8'); print('inserted',len(a))
