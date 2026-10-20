import re
from pathlib import Path
p=Path('research/index.htm'); s=p.read_text(encoding='utf-8')
cards=re.findall(r'<article class="research-card" data-issue="451"[\s\S]*?</article>',s)
if cards:
 for c in cards: s=s.replace(c,'',1)
 marker='<main id="videha-main">'
 s=s.replace(marker,marker+''.join(cards),1)
 p.write_text(s,encoding='utf-8')
 print('moved',len(cards))
