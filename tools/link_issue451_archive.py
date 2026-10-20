from pathlib import Path
p=Path('research/index.htm'); s=p.read_text(encoding='utf-8')
s=s.replace(' · अंक 451 ·',' · <a href="https://videha-ejournal.github.io/videha/videha-archive-explorer.html?issue=451">अंक 451</a> ·')
p.write_text(s,encoding='utf-8')
