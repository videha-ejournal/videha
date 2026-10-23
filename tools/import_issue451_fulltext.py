from pathlib import Path
from urllib.request import urlopen, Request
from html.parser import HTMLParser
import re, html
class Body(HTMLParser):
 def __init__(self): super().__init__(); self.on=False; self.parts=[]
 def handle_starttag(self,t,a):
  if t=='body': self.on=True
 def handle_endtag(self,t):
  if t=='body': self.on=False
 def handle_data(self,d):
  if self.on and d.strip(): self.parts.append(d.strip())
items=[('new_page_126.htm','हितनाथ झा','मैथिली साहित्यमे तारानाथ झा एवं हुनक परिवारक योगदान'),('new_page_128.htm','कल्पना झा',"मैथिली साहित्यमे श्रीकान्त ठाकुर 'विद्यालंकार' एवं हुनक परिवारक योगदान"),('new_page_105.htm','प्रीति कुमारी','समकालीन भारतीय साहित्य पत्रिका अंक - २४६ वर्ष -४७, मास जुलाई-अगस्त २०२६'),('new_page_112.htm','प्रणव कुमार झा','प्लास्टिकक बढ़ैत उपयोग, कचरा प्रबंधनक संकट आ विकल्पक खोज'),('new_page_130.htm','आचार्य रामानंद मंडल','गोस्वामी बनाम ब्राह्मण/ मिथक बनाम चमत्कार')]
for fn,author,title in items:
 src='https://www.videha.co.in/'+fn; data=urlopen(Request(src,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read().decode('utf-8','ignore'); b=Body(); b.feed(data); text=' '.join(b.parts); text=re.sub(r'\s+',' ',html.unescape(text)).strip()
 out=Path('research/2026/451')/fn; old=out.read_text(encoding='utf-8'); head=old[:old.lower().find('<body>')+6]; tail='</body></html>'
 body=f'<main data-pagefind-body><p><a href="../../index.htm">विदेह शोध-सूची</a> · <a href="{src}">मूल लेख</a></p><h1>{html.escape(title)}</h1><p><strong>लेखक:</strong> {html.escape(author)} · <strong>Videha अंक ४५१ · 1 October 2026</strong></p><article><p>{html.escape(text)}</p></article></main>'
 out.write_text(head+body+tail,encoding='utf-8'); print(fn,len(text))
