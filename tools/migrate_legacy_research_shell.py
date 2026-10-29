import json,re
from pathlib import Path
root=Path('.')
d=json.loads((root/'research/data/articles.json').read_text(encoding='utf8'))
changed=0; missing=0
for a in d['articles']:
 p=root/'research'/a['path']
 if not p.exists(): missing+=1; continue
 s=p.read_text(encoding='utf8',errors='ignore')
 if 'assets/css/videha.css' not in s:
  s=s.replace('</head>','<link rel="stylesheet" href="../../../assets/css/videha.css"></head>',1)
 if '<meta name="viewport"' not in s:
  s=s.replace('<head>','<head><meta name="viewport" content="width=device-width,initial-scale=1">',1)
 if 'class="videha-migration-header"' not in s:
  header='<header class="videha-migration-header"><a href="https://videha-ejournal.github.io/videha/">VIDEHA · प्रथम मैथिली पाक्षिक eJournal</a><nav><a href="../../index.htm">शोध-सूची</a> · <a href="https://videha-ejournal.github.io/videha/videha-archive-explorer.html?issue='+str(a.get('issue',''))+'">अंक '+str(a.get('issue',''))+'</a></nav></header>'
  s=s.replace('<body>', '<body>'+header,1)
 if 'class="videha-migration-footer"' not in s:
  footer='<footer class="videha-migration-footer"><a href="https://videha-ejournal.github.io/videha/">VIDEHA Home</a> · <a href="../../index.htm">Research Index</a> · ISSN 2229-547X</footer>'
  s=s.replace('</body>',footer+'</body>',1)
 p.write_text(s,encoding='utf8'); changed+=1
print({'changed':changed,'missing':missing})
