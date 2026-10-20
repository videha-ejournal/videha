import json
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'research/data/articles.json'; d=json.loads(p.read_text(encoding='utf-8'))
groups={'kamla-chaudhary':('कमला चौधरी','नित नवल कमला चौधरी',3),'kunal':('कुणाल','नित नवल कुणाल',2),'lalita-jha':('ललिता झा','नित नवल ललिता झा',1),'virendra-mallick':('वीरेन्द्र मल्लिक','नित नवल वीरेन्द्र मल्लिक',4),'vrishesh-chandra-lal':('वृषेश चन्द्र लाल','नित नवल वृषेश चन्द्र लाल',4),'yoganand-jha':('योगानन्द झा','नित नवल योगानन्द झा',6)}
existing={a.get('path') for a in d['articles']}
for slug,(author,title,n) in groups.items():
 for i in range(1,n+1):
  path=f'2026/451/gajendra-thakur-nit-naval-{slug}-{i}.htm'
  if path in existing: continue
  d['articles'].append({'title':f'{title} · शोध-लेख {i}','english_title':None,'authors':['गजेन्द्र ठाकुर'],'publication_date':'2026-09-15','year':'2026','issue':'451','language':'mai','keywords':['Issue 451',title],'classification':'Maithili literary criticism and research','url':'https://videha-ejournal.github.io/videha/research/'+path,'pdf_url':'https://archive.org/download/videha-2026/Videha%20451.pdf','source_url':'https://videha-ejournal.github.io/videha/research/'+path,'path':path,'page_start':None,'page_end':None})
d['generated']=datetime.now(timezone.utc).isoformat(); d['extraction_summary']['published_after_all_overrides']=len(d['articles']); p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8'); print(len(d['articles']))
