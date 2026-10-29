from pathlib import Path
root=Path('.')
changed=0
for p in root.rglob('*.html'):
 if any(x in {'.git','node_modules'} for x in p.parts): continue
 s=p.read_text(encoding='utf8',errors='ignore')
 if 'assets/css/videha.css' in s or 'assets/css/videha-studio.css' in s: continue
 rel='/'.join(['..']*len(p.parent.relative_to(root).parts)) or '.'
 css=f'{rel}/assets/css/videha.css'
 s=s.replace('</head>',f'<link rel="stylesheet" href="{css}"></head>',1)
 if '<meta name="viewport"' not in s: s=s.replace('<head>','<head><meta name="viewport" content="width=device-width,initial-scale=1">',1)
 header='<header class="videha-unified-header"><a href="https://videha-ejournal.github.io/videha/">VIDEHA · प्रथम मैथिली पाक्षिक eJournal</a><nav><a href="https://videha-ejournal.github.io/videha/research/index.htm">Research</a> · <a href="https://videha-ejournal.github.io/videha/videha-archive-explorer.html">Archive</a></nav></header>'
 footer='<footer class="videha-unified-footer"><a href="https://videha-ejournal.github.io/videha/">VIDEHA Home</a> · ISSN 2229-547X</footer>'
 if 'class="videha-unified-header"' not in s: s=s.replace('<body>','<body>'+header,1)
 if 'class="videha-unified-footer"' not in s: s=s.replace('</body>',footer+'</body>',1)
 p.write_text(s,encoding='utf8');changed+=1
print('migrated',changed)
