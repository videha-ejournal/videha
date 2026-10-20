from docx import Document
import re
p=r'C:\Users\DELL\Documents\Github_VIDEHA_SADEHA_PDF_DOCX\VIDEHA_SADEHA_DOC_DOCX\VIDEHA_DOCX\Videha 444_451\Videha_451_2.docx'
d=Document(p)
ranges=[(951,2053),(2053,2862),(2862,3125),(3125,4289),(4289,6174),(6174,6858)]
for a,b in ranges:
 print('RANGE',a,b)
 for i in range(a,b):
  t=' '.join(d.paragraphs[i].text.split())
  if len(t)<300 and (re.match(r'^[०-९0-9]+[.)]',t) or re.match(r'^[०-९0-9]+\\.[०-९0-9]+',t)):
   print(i,t)
