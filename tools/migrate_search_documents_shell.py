from pathlib import Path
import re
root=Path('search-documents'); changed=0
for p in root.glob('videha-*.html'):
 s=p.read_text(encoding='utf8',errors='ignore')
 if 'assets/css/videha.css' not in s:
  s=s.replace('</head>','<link rel="stylesheet" href="../assets/css/videha.css"></head>',1)
 if '<meta name="viewport"' not in s:
  s=s.replace('<head>','<head><meta name="viewport" content="width=device-width,initial-scale=1">',1)
 if 'class="videha-search-header"' not in s:
  h='<header class="videha-search-header"><a href="https://videha-ejournal.github.io/videha/">VIDEHA · प्रथम मैथिली पाक्षिक eJournal</a><nav><a href="../research/index.htm">Research Index</a> · <a href="../videha-archive-explorer.html">Archive Explorer</a></nav></header>'
  s=s.replace('<body>', '<body>'+h,1)
 if 'class="videha-search-footer"' not in s:
  f='<footer class="videha-search-footer"><a href="https://videha-ejournal.github.io/videha/">VIDEHA Home</a> · <a href="../research/index.htm">Research Index</a> · ISSN 2229-547X</footer>'
  s=s.replace('</body>',f+'</body>',1)
 p.write_text(s,encoding='utf8');changed+=1
print('migrated',changed)
