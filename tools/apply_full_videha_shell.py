from pathlib import Path
import re
header='<header class="videha-full-header"><div>VIDEHA ISSN 2229-547X · First Maithili Fortnightly eJournal · Since 2000 · <a href="https://www.videha.co.in/">www.videha.co.in</a></div><h2>विदेह — प्रथम मैथिली पाक्षिक ई पत्रिका</h2><nav><a href="https://x.com/videha">Twitter / X</a> · <a href="https://www.facebook.com/groups/videha/">Facebook</a> · <a href="https://videha-ejournal.github.io/videha/archive.htm">Archive</a> · <a href="https://videha-ejournal.github.io/videha/index.htm">नूतन अंक</a> · <a href="https://videha-ejournal.github.io/videha/videha.htm">पुरान अंक</a> · <a href="https://videha-ejournal.github.io/videha/pothi.htm">पोथी</a> · <a href="https://videha-ejournal.github.io/videha/Audio_Video.htm">दृश्य-श्रव्य</a> · <a href="https://videha-ejournal.github.io/videha/femcorner.htm">स्त्री कोना</a> · <a href="https://videha-ejournal.github.io/videha/gajenthakur.htm">Parallel History</a> · <a href="https://videha-ejournal.github.io/videha/gajendra-thakur-samagra.htm">गजेन्द्र ठाकुर समग्र</a></nav></header>'
footer='<footer class="videha-full-footer"><strong>Videha — First Maithili Fortnightly eJournal · ISSN 2229-547X</strong><br><a href="https://videha-ejournal.github.io/videha/index.htm">विदेह प्रथम मैथिली पाक्षिक ई पत्रिका</a> · <a href="https://videha-ejournal.github.io/videha/index.htm#">⇧</a><br>नव विदेह अंक — मासमे दू बेर · <a href="https://groups.google.com/g/videha">ई-पत्र सदस्यता</a> · <a href="https://videha-ejournal.github.io/videha/videha-rss.xml">RSS feed</a> · <a href="https://videha-ejournal.github.io/videha/videha-doi.htm">DOI · Zenodo</a><br>Primary: <a href="https://www.videha.co.in/">www.videha.co.in</a> · GitHub mirror: <a href="https://videha-ejournal.github.io/videha/">videha-ejournal.github.io/videha</a> · <a href="https://github.com/videha-ejournal">GitHub research network</a></footer>'
changed=0
for p in Path('.').rglob('*'):
 if not p.is_file() or p.suffix.lower() not in {'.htm','.html'} or '.git' in p.parts or '_pagefind_build' in p.parts: continue
 if p.name in {'google7d0b1633a9939d34.html','universal-search-embed-snippet.html'}: continue
 s=p.read_text(encoding='utf8',errors='ignore')
 if 'videha-full-header' in s: continue
 s=re.sub(r'<header class="(?:videha-migration|videha-search|videha-unified)-header">.*?</header>',header,s,count=1,flags=re.S)
 s=re.sub(r'<footer class="(?:videha-migration|videha-search|videha-unified)-footer">.*?</footer>',footer,s,count=1,flags=re.S)
 if '<header class="videha-full-header">' not in s and '<body>' in s: s=s.replace('<body>','<body>'+header,1)
 if '<footer class="videha-full-footer">' not in s and '</body>' in s: s=s.replace('</body>',footer+'</body>',1)
 p.write_text(s,encoding='utf8');changed+=1
print('updated',changed)
