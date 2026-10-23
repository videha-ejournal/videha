import json, html
from pathlib import Path
d=json.loads(Path('research/data/articles.json').read_text(encoding='utf-8'))
urls=['https://www.videha.co.in/research/','https://www.videha.co.in/research/videha-scholar-research-book.html']+[a['url'].replace('https://videha-ejournal.github.io/videha','https://www.videha.co.in') for a in d['articles']]
urls=list(dict.fromkeys(urls)); body='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+html.escape(u)+'</loc></url>' for u in urls)+'</urlset>\n'
Path('research/sitemap.xml').write_text(body,encoding='utf-8'); print(len(urls))
