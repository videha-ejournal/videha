from pathlib import Path
skip={'google7d0b1633a9939d34.html','universal-search-embed-snippet.html'}
changed=0
for p in Path('.').rglob('*'):
 if not p.is_file() or p.suffix.lower() not in {'.htm','.html'} or '.git' in p.parts or '_pagefind_build' in p.parts or p.name in skip: continue
 s=p.read_text(encoding='utf8',errors='ignore')
 if 'assets/css/videha.css' in s or 'assets/css/videha-studio.css' in s: continue
 rel='/'.join(['..']*len(p.parent.parts)) or '.'
 s=s.replace('</head>',f'<link rel="stylesheet" href="{rel}/assets/css/videha.css"></head>',1)
 if '<meta name="viewport"' not in s: s=s.replace('<head>','<head><meta name="viewport" content="width=device-width,initial-scale=1">',1)
 h='<header class="videha-unified-header"><a href="https://videha-ejournal.github.io/videha/">VIDEHA Digital Archive & Editorial Studio</a><nav><a href="https://videha-ejournal.github.io/videha/research/index.htm">Research Articles</a> · <a href="https://videha-ejournal.github.io/videha/videha-digital-archive.html">अभिलेख</a> · <a href="https://videha-ejournal.github.io/videha/videha-chatbot.html">Ask Videha</a> · <a href="https://videha-ejournal.github.io/videha/videha-publisher.html">Publisher</a> · <a href="https://videha-ejournal.github.io/videha/publication-certificate.html">Author Certificate</a></nav></header>'
 f='<footer class="videha-unified-footer"><a href="https://videha-ejournal.github.io/videha/">VIDEHA Home</a> · ISSN 2229-547X</footer>'
 if 'videha-unified-header' not in s: s=s.replace('<body>','<body>'+h,1)
 if 'videha-unified-footer' not in s: s=s.replace('</body>',f+'</body>',1)
 p.write_text(s,encoding='utf8');changed+=1
print('migrated',changed)
