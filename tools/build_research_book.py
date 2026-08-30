import json, html, re
from pathlib import Path
from collections import defaultdict
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'research/data/articles.json').read_text(encoding='utf-8'))['articles']
HTML=ROOT/'research/videha-scholar-research-book.html'; DOCX=ROOT/'research/Videha-Scholar-Research-Book.docx'
def auth(a): return ' / '.join(a.get('authors') or ['अज्ञात लेखक'])
def sortkey(a): return re.sub(r'^(डॉ\.?|डाॅ\.?|प्रो\.?|आचार्य|श्री|श्रीमती|पं\.?|पण्डित)\s*','',auth(a),flags=re.I).casefold()
def genre(a): return (a.get('classification') or 'अन्य शोध').split(';')[0].strip()
def pages(a): return f"{a.get('page_start')}–{a.get('page_end')}" if a.get('page_start') and a.get('page_end') else '—'
def date(a): return a.get('publication_date') or '—'
def issue(a): return 'अंक '+str(a.get('issue','—'))
def esc(s): return html.escape(str(s or ''),quote=True)
rows=sorted(DATA,key=lambda a:(sortkey(a),(a.get('title') or '').casefold())); groups=defaultdict(list)
for a in DATA: groups[genre(a)].append(a)
parts=['<!doctype html><html lang="mai"><head><meta charset="utf-8"><title>विदेह शोध-लेख : अंक १ सँ ४४७ धरि</title><style>@page{size:letter;margin:18mm}body{font-family:"Noto Serif Devanagari","Nirmala UI",serif;color:#18212b;line-height:1.5}h1{color:#163a5f}h2{color:#1f4d78;border-bottom:1px solid #b9c8d8}p{font-size:12px;text-align:justify}.note{background:#f1f5f8;border-left:4px solid #2e74b5;padding:10px}table{border-collapse:collapse;width:100%;font-size:8.5px;page-break-inside:auto}thead{display:table-header-group}tr{page-break-inside:avoid}th,td{border:1px solid #b7c4d1;padding:4px;vertical-align:top}th{background:#e8eef5;color:#173b5f}a{color:#155a8a;text-decoration:none}</style></head><body>']
parts.append(f'<h1>विदेह शोध-लेख : अंक १ सँ ४४७ धरि</h1><p>अन्तिम सत्यापित कॉर्पस : {len(DATA)} लेख · मैथिली {sum(a.get("language")=="mai" for a in DATA)} · अंग्रेजी {sum(a.get("language")=="en" for a in DATA)} · संस्कृत {sum(a.get("language")=="sa" for a in DATA)}</p>')
parts.append('<div class="note"><b>सम्पादकीय टिप्पणी।</b> एहि सूचीमे पूरा शोध, इतिहास, आलोचना, भाषा-विज्ञान, समाज-अध्ययन अथवा सांस्कृतिक अनुशीलनबला सामग्री राखल गेल अछि। कथा, कविता, सूचना आ मात्र अनुवादकेँ स्वतन्त्र शोध-लेख नहि गनल गेल अछि।</div><h2>परिचय आ पद्धति</h2><p>विदेहक शोध-संसार मिथिला, मैथिली, संस्कृत, इतिहास, लोक-संस्कृति, नाटक, दलित-विमर्श, नारी-विमर्श, चिकित्सा-मानविकी, पर्यावरण, पञ्जी-परम्परा आ नव्य-न्याय धरि पसरेल अछि। भाषा-निर्धारण वास्तविक लेख-पाठक आधारपर कएल गेल अछि।</p>')
def hrow(n,a): return '<tr><td>%s</td><td>%s</td><td><a href="%s">%s</a></td><td>%s</td><td>%s</td><td>%s · %s</td><td>%s</td><td>%s</td></tr>'%(n,esc(auth(a)),esc(a.get('url')),esc(a.get('title')),esc(genre(a)),esc(a.get('language')),esc(issue(a)),esc(date(a)),esc(a.get('classification') or '—'),esc(pages(a)))
parts.append('<h2>अनुलग्नक १ : लेखकानुक्रमेण सम्पूर्ण सूची</h2><table><thead><tr><th>क्रम</th><th>लेखक</th><th>लेख</th><th>विधा</th><th>भाषा</th><th>अंक · तिथि</th><th>वर्गीकरण</th><th>पृष्ठ</th></tr></thead><tbody>')
for i,a in enumerate(rows,1): parts.append(hrow(i,a))
parts.append('</tbody></table><h2>अनुलग्नक २ : विधावार सम्पूर्ण सूची</h2>')
for g in sorted(groups,key=str.casefold):
 parts.append(f'<h3>{esc(g)} ({len(groups[g])})</h3><table><thead><tr><th>क्रम</th><th>लेखक</th><th>लेख</th><th>भाषा</th><th>अंक · तिथि</th><th>वर्गीकरण</th><th>पृष्ठ</th></tr></thead><tbody>')
 for i,a in enumerate(sorted(groups[g],key=lambda x:(sortkey(x),(x.get('title') or '').casefold())),1): parts.append('<tr><td>%d</td><td>%s</td><td><a href="%s">%s</a></td><td>%s</td><td>%s · %s</td><td>%s</td><td>%s</td></tr>'%(i,esc(auth(a)),esc(a.get('url')),esc(a.get('title')),esc(a.get('language')),esc(issue(a)),esc(date(a)),esc(a.get('classification') or '—'),esc(pages(a))))
 parts.append('</tbody></table>')
HTML.write_text(''.join(parts+['</body></html>']),encoding='utf-8')

def cell(c,text,bold=False,size=7):
 c.text='';p=c.paragraphs[0];p.paragraph_format.space_after=Pt(0);r=p.add_run(str(text));r.bold=bold;r.font.name='Noto Serif Devanagari';r.font.size=Pt(size)
def shade(c):
 sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E8EEF5');c._tc.get_or_add_tcPr().append(sh)
def table(doc,headers,data):
 t=doc.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.style='Table Grid';t.autofit=False
 for j,h in enumerate(headers): cell(t.rows[0].cells[j],h,True);shade(t.rows[0].cells[j])
 for row in data:
  cells=t.add_row().cells
  for j,v in enumerate(row): cell(cells[j],v)
doc=Document();s=doc.sections[0];s.page_width=Inches(8);s.page_height=Inches(11);s.top_margin=Inches(.75);s.bottom_margin=Inches(.75);s.left_margin=Inches(.9);s.right_margin=Inches(.75);s.gutter=Inches(.3)
doc.styles['Normal'].font.name='Noto Serif Devanagari';doc.styles['Normal'].font.size=Pt(10);doc.styles['Normal'].paragraph_format.space_after=Pt(5)
p=doc.add_paragraph();p.style='Title';p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.add_run('विदेह शोध-लेख : अंक १ सँ ४४७ धरि')
doc.add_paragraph(f'अन्तिम सत्यापित कॉर्पस : {len(DATA)} लेख · मैथिली {sum(a.get("language")=="mai" for a in DATA)} · अंग्रेजी {sum(a.get("language")=="en" for a in DATA)} · संस्कृत {sum(a.get("language")=="sa" for a in DATA)}').alignment=WD_ALIGN_PARAGRAPH.CENTER
doc.add_heading('१. परिचय आ पद्धति',1);doc.add_paragraph('विदेहक शोध-संसार मिथिला, मैथिली, संस्कृत, इतिहास, लोक-संस्कृति, नाटक, दलित-विमर्श, नारी-विमर्श, चिकित्सा-मानविकी, पर्यावरण, पञ्जी-परम्परा आ नव्य-न्याय धरि पसरेल अछि। भाषा-निर्धारण वास्तविक लेख-पाठक आधारपर कएल गेल अछि।')
doc.add_heading('अनुलग्नक १ : लेखकानुक्रमेण सम्पूर्ण सूची',1);table(doc,['क्रम','लेखक','लेख','विधा','भाषा','अंक · तिथि','वर्गीकरण','पृष्ठ'],[[i,auth(a),a.get('title'),genre(a),a.get('language'),f'{issue(a)} · {date(a)}',a.get('classification') or '—',pages(a)] for i,a in enumerate(rows,1)])
doc.add_heading('अनुलग्नक २ : विधावार सम्पूर्ण सूची',1)
for g in sorted(groups,key=str.casefold):
 doc.add_heading(f'{g} ({len(groups[g])})',2);table(doc,['क्रम','लेखक','लेख','भाषा','अंक · तिथि','वर्गीकरण','पृष्ठ'],[[i,auth(a),a.get('title'),a.get('language'),f'{issue(a)} · {date(a)}',a.get('classification') or '—',pages(a)] for i,a in enumerate(sorted(groups[g],key=lambda x:(sortkey(x),(x.get('title') or '').casefold())),1)])
doc.save(DOCX);print('created',HTML,DOCX,len(DATA))
