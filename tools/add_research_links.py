from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'research/index.htm'; s=p.read_text(encoding='utf-8'); marker='<div class="videha-a11y-bar videha-ai-standalone"';
if 'videha-scholar-research-book.html' not in s: s=s.replace(marker,'<p><a href="https://www.videha.co.in/research/videha-scholar-research-book.html">शोध-लेखक समग्र अध्ययन · Further HTML book article</a></p>'+marker,1); p.write_text(s,encoding='utf-8')
p=root/'gajendra-thakur-samagra.htm'; s=p.read_text(encoding='utf-8'); marker='<div class="gt-strip">गजेन्द्र ठाकुर समग्र</div>'
if 'videha-scholar-research-book.html' not in s: s=s.replace(marker,marker+'<p class="gt-refresh"><a href="https://www.videha.co.in/research/videha-scholar-research-book.html">शोध-सूची समग्र अध्ययन · Further HTML book article</a></p>',1); p.write_text(s,encoding='utf-8')
print('research links added')
