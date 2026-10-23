import json
import re
from pathlib import Path
d=json.loads(Path('research/data/articles.json').read_text(encoding='utf8'))
missing=[]; bad=[]; invalid=[]
for a in d['articles']:
 p=Path('research')/a['path']
 if not p.exists(): missing.append((a['path'],'file')); continue
 s=p.read_text(encoding='utf8',errors='ignore')
 req=['application/ld+json','canonical','citation_title','citation_author','citation_journal_title','citation_issn']
 m=[x for x in req if x not in s]
 if m: bad.append((a['path'],m))
 for block in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',s,re.S|re.I):
  try: json.loads(block)
  except Exception as e: invalid.append((a['path'],str(e)))
print('manifest',len(d['articles']),'missing_files',len(missing),'metadata_failures',len(bad))
print('invalid_jsonld',len(invalid))
for x in bad[:50]: print(x)
