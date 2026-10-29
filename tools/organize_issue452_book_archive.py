import json,html,re
from pathlib import Path
root=Path('.')
d=json.loads((root/'research/data/articles.json').read_text(encoding='utf8')); a=[x for x in d['articles'] if x.get('issue')=='452']
p=root/'research/videha-scholar-research-book.html'; s=p.read_text(encoding='utf8')
s=re.sub(r'<h2>अंक ४५२ · शोध-लेख</h2><ul>.*?</ul>','',s,flags=re.S)
rows=''.join(f'<tr><td>{i}</td><td>{html.escape(x["authors"][0])}</td><td><a href="{x["url"]}">{html.escape(x["title"])}</a></td><td>{html.escape(x["classification"])}</td><td>अंक 452</td></tr>' for i,x in enumerate(sorted(a,key=lambda x:x['authors'][0]),1))
block='<h2 id="issue-452-author">अंक ४५२ · लेखकानुक्रमेण ४७ शोध-लेख</h2><table><thead><tr><th>क्रम</th><th>लेखक</th><th>लेख</th><th>विधा</th><th>अंक</th></tr></thead><tbody>'+rows+'</tbody></table>'
s=s.replace('<h2>अनुलग्नक १ : लेखकानुक्रमेण सम्पूर्ण सूची</h2>',block+'<h2>अनुलग्नक १ : लेखकानुक्रमेण सम्पूर्ण सूची</h2>',1)
g=''.join(f'<tr><td>{i}</td><td>{html.escape(x["classification"])}</td><td><a href="{x["url"]}">{html.escape(x["title"])}</a></td><td>{html.escape(x["authors"][0])}</td></tr>' for i,x in enumerate(sorted(a,key=lambda x:x['classification']),1))
block2='<h2 id="issue-452-genre">अंक ४५२ · विधावार ४७ शोध-लेख</h2><table><thead><tr><th>क्रम</th><th>विधा</th><th>लेख</th><th>लेखक</th></tr></thead><tbody>'+g+'</tbody></table>'
s=s.replace('<h2>अनुलग्नक २ : विधावार सम्पूर्ण सूची</h2>',block2+'<h2>अनुलग्नक २ : विधावार सम्पूर्ण सूची</h2>',1);p.write_text(s,encoding='utf8')
m=root/'data/videha-archive-manifest.json';md=json.loads(m.read_text(encoding='utf8'))
if not any(x.get('issue')==452 and x.get('publication')=='VIDEHA' for x in md['archive']): md['archive'].append({'publication':'VIDEHA','issue':452,'version':None,'title':'विदेह अंक ४५२ · Videha Issue 452','file':'search-documents/videha-452.html','source':'https://archive.org/download/videha-2026/Videha%20452.pdf','date':'१५ अक्टूबर २०२६','dateISO':'2026-10-15','year':2026})
m.write_text(json.dumps(md,ensure_ascii=False,indent=2),encoding='utf8');print(len(a))
