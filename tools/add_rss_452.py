from pathlib import Path
p=Path('search-documents/videha-452.html'); s=p.read_text(encoding='utf8')
s=s.replace('</h1>','</h1><p><a href="https://www.videha.co.in/videha-rss.xml">Videha RSS</a></p>',1)
p.write_text(s,encoding='utf8')
