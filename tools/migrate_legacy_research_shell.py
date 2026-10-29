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
 header='<header class="videha-migration-header"><a href="https://videha-ejournal.github.io/videha/">VIDEHA Digital Archive & Editorial Studio</a><nav><a href="https://videha-ejournal.github.io/videha/research/index.htm">Research Articles</a> · <a href="https://videha-ejournal.github.io/videha/videha-digital-archive.html">अभिलेख</a> · <a href="https://videha-ejournal.github.io/videha/videha-chatbot.html">Ask Videha</a> · <a href="https://videha-ejournal.github.io/videha/videha-publisher.html">Publisher</a> · <a href="https://videha-ejournal.github.io/videha/publication-certificate.html">Author Certificate</a> · <a href="https://videha-ejournal.github.io/videha/Audio_Video.htm">Audio/Video</a></nav></header>'
 if 'class="videha-migration-header"' in s: s=re.sub(r'<header class="videha-migration-header">.*?</header>',header,s,count=1,flags=re.S)
 else: s=s.replace('<body>', '<body>'+header,1)
 footer='<footer class="videha-migration-footer"><a href="https://videha-ejournal.github.io/videha/">VIDEHA Home</a> · <a href="https://videha-ejournal.github.io/videha/research/index.htm">Research Index</a> · <a href="https://videha-ejournal.github.io/videha/videha-archive-explorer.html">Archive Explorer</a> · ISSN 2229-547X</footer>'
 if 'class="videha-migration-footer"' in s: s=re.sub(r'<footer class="videha-migration-footer">.*?</footer>',footer,s,count=1,flags=re.S)
 else: s=s.replace('</body>',footer+'</body>',1)
 p.write_text(s,encoding='utf8'); changed+=1
print({'changed':changed,'missing':missing})
