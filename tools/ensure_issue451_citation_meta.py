from pathlib import Path
for p in Path('research/2026/451').glob('*.htm'):
 s=p.read_text(encoding='utf-8')
 if 'citation_journal_title' not in s:
  tags='<meta name="citation_journal_title" content="Videha"><meta name="citation_issn" content="2229-547X">'
  s=s.replace('</head>',tags+'</head>',1)
 p.write_text(s,encoding='utf-8')
print('checked',len(list(Path('research/2026/451').glob('*.htm'))))
