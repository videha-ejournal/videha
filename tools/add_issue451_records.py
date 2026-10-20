import json
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
inv=ROOT/'research/data/articles.json'
data=json.loads(inv.read_text(encoding='utf-8'))
items=[('हितनाथ झा','मैथिली साहित्यमे तारानाथ झा एवं हुनक परिवारक योगदान','new_page_126.htm'),('कल्पना झा',"मैथिली साहित्यमे श्रीकान्त ठाकुर 'विद्यालंकार' एवं हुनक परिवारक योगदान",'new_page_128.htm'),('प्रीति कुमारी','समकालीन भारतीय साहित्य पत्रिका अंक - २४६ वर्ष -४७, मास जुलाई-अगस्त २०२६','new_page_105.htm'),('प्रणव कुमार झा','प्लास्टिकक बढ़ैत उपयोग, कचरा प्रबंधनक संकट आ विकल्पक खोज','new_page_112.htm'),('आचार्य रामानंद मंडल','गोस्वामी बनाम ब्राह्मण/ मिथक बनाम चमत्कार','new_page_130.htm')]
existing={a.get('source_url') for a in data['articles']}
for author,title,old in items:
 source='https://www.videha.co.in/'+old
 if source in existing: continue
 slug=old[:-4]; path=f'2026/451/{slug}.htm'; page=ROOT/'research'/path; page.parent.mkdir(parents=True,exist_ok=True)
 page.write_text(f'<!doctype html><html lang="mai"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="citation_title" content="{title}"><meta name="citation_author" content="{author}"><meta name="citation_issue" content="451"><title>{title} · अंक ४५१</title></head><body><main data-pagefind-body><p><a href="../../index.htm">विदेह शोध-सूची</a> · <a href="{source}">मूल लेख</a></p><h1>{title}</h1><p><strong>लेखक:</strong> {author} · <strong>Videha अंक ४५१</strong></p><p>ई Issue 451 मे प्रकाशित शोध-सामग्रीक canonical research record थिक। मूल पृष्ठ पर पूरा पाठ उपलब्ध अछि।</p></main></body></html>',encoding='utf-8')
 data['articles'].append({'title':title,'english_title':None,'authors':[author],'publication_date':'2026-09-15','year':'2026','issue':'451','language':'mai','keywords':['Issue 451','Maithili research'],'classification':'Maithili literary and cultural research','url':'https://videha-ejournal.github.io/videha/research/'+path,'pdf_url':'https://archive.org/download/videha-2026/Videha%20451.pdf','source_url':source,'path':path,'page_start':None,'page_end':None})
data['generated']=datetime.now(timezone.utc).isoformat(); data['extraction_summary']['published_after_all_overrides']=len(data['articles']); inv.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8'); print('count',len(data['articles']))
