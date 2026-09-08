from pathlib import Path
from docx import Document
import json,re,html
ROOT=Path(__file__).resolve().parents[1]; SRC=Path(r"C:\Users\DELL\Documents\00_01_VIDEHA_001_444_Sadeha_01_37\VIDEHA_448_DOC_PDF\Devanagari\Videha 448_2.docx"); OUT=ROOT/'scholar-data'/'articles'; OUT.mkdir(parents=True,exist_ok=True)
DEV='०१२३४५६७८९'
def deva(n): return ''.join(DEV[int(c)] for c in str(n))
SELECT=[f'२.{deva(i)}.' for i in range(1,30)]
def main():
 p=[x.text.strip() for x in Document(SRC).paragraphs if x.text.strip()]; made=0
 for sec in SELECT:
  inds=[i for i,x in enumerate(p) if x.startswith(sec)]
  if len(inds)<2: continue
  i=inds[1]; j=next((k for k in range(i+1,len(p)) if re.match(r'^२\.[0-९]+\.',p[k]) or re.match(r'^३\.[0-९]+\.',p[k])),len(p)); block=p[i:j]
  label=block[0]; m=re.match(r'^२\.[0-९]+\.\s*(.*?)\s*-\s*(.+)$',label); author=(m.group(1).strip() if m else 'गजेन्द्र ठाकुर'); title=(m.group(2).strip() if m else label)
  slug=re.sub(r'[^0-9A-Za-z\u0900-\u097F]+','-',title).strip('-').lower()[:120]; lang='bajjika' if 'बज्जिका' in title else ('angika' if 'अंगिका' in title or 'ठेठी' in title else 'mai'); rec={'title':title,'authors':[author],'publication_date':'2026-08-15','year':'2026','issue':'448','language':lang,'keywords':['Ramanand Jha Raman','Maithili literary history','Mithila studies'],'classification':f'{lang} literary history and criticism','page_start':None,'page_end':None,'source_url':'https://archive.org/download/VidehaAndSadeha/Videha%20448.pdf','full_text_html':''.join('<p>'+html.escape(x)+'</p>' for x in block[1:]),'slug':slug}
  (OUT/f'issue-448-{slug[:40]}.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8'); made+=1
 print('created',made,'Issue 448 curated manifests')
if __name__=='__main__': main()
