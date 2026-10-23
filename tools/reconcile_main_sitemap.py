import re
from pathlib import Path
from html import escape
main=Path('sitemap.xml'); research=Path('research/sitemap.xml')
def urls(p): return re.findall(r'<loc>(.*?)</loc>',p.read_text(encoding='utf-8'))
all_urls=list(dict.fromkeys(urls(main)+urls(research)))
body='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+escape(u)+'</loc></url>' for u in all_urls)+'</urlset>\n'
main.write_text(body,encoding='utf-8'); print(len(all_urls))
