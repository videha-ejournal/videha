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
 header='<header class="videha-migration-header"><div>VIDEHA ISSN 2229-547X · First Maithili Fortnightly eJournal · Since 2000 · <a href="https://www.videha.co.in/">www.videha.co.in</a></div><h2>विदेह — प्रथम मैथिली पाक्षिक ई पत्रिका</h2><nav><a href="https://x.com/videha">Twitter / X</a> · <a href="https://www.facebook.com/groups/videha/">Facebook</a> · <a href="https://videha-ejournal.github.io/videha/archive.htm">Archive</a> · <a href="https://videha-ejournal.github.io/videha/index.htm">नूतन अंक</a> · <a href="https://videha-ejournal.github.io/videha/videha.htm">पुरान अंक</a> · <a href="https://videha-ejournal.github.io/videha/pothi.htm">पोथी</a> · <a href="https://videha-ejournal.github.io/videha/Audio_Video.htm">दृश्य-श्रव्य</a> · <a href="https://videha-ejournal.github.io/videha/femcorner.htm">स्त्री कोना</a> · <a href="https://videha-ejournal.github.io/videha/gajenthakur.htm">Parallel History</a> · <a href="https://videha-ejournal.github.io/videha/gajendra-thakur-samagra.htm">गजेन्द्र ठाकुर समग्र</a></nav></header>'
 if 'class="videha-migration-header"' in s: s=re.sub(r'<header class="videha-migration-header">.*?</header>',header,s,count=1,flags=re.S)
 else: s=s.replace('<body>', '<body>'+header,1)
 footer='<footer class="videha-migration-footer"><strong>Videha — First Maithili Fortnightly eJournal · ISSN 2229-547X</strong><br><a href="https://videha-ejournal.github.io/videha/index.htm">विदेह प्रथम मैथिली पाक्षिक ई पत्रिका</a> · <a href="https://videha-ejournal.github.io/videha/index.htm#">⇧</a><br>नव विदेह अंक — मासमे दू बेर · <a href="https://groups.google.com/g/videha">ई-पत्र सदस्यता</a> · <a href="https://videha-ejournal.github.io/videha/videha-rss.xml">RSS feed</a> · <a href="https://videha-ejournal.github.io/videha/videha-doi.htm">DOI · Zenodo · Scholarly Preservation</a><br>Primary: <a href="https://www.videha.co.in/">www.videha.co.in</a> · GitHub mirror: <a href="https://videha-ejournal.github.io/videha/">videha-ejournal.github.io/videha</a> · Digital Research Archive: <a href="https://videha-ejournal.github.io/mithila-vajji-anga/">mithila-vajji-anga</a> · <a href="https://github.com/videha-ejournal">GitHub research network</a></footer>'
 if 'class="videha-migration-footer"' in s: s=re.sub(r'<footer class="videha-migration-footer">.*?</footer>',footer,s,count=1,flags=re.S)
 else: s=s.replace('</body>',footer+'</body>',1)
 p.write_text(s,encoding='utf8'); changed+=1
print({'changed':changed,'missing':missing})
