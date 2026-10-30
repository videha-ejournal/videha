from pathlib import Path
import re

ROOT = Path('.')
controls = '''<div class="videha-language-links" data-pagefind-ignore="all" aria-label="भाषा · Language"><a href="#" data-videha-lang="mai">मैथिली</a> · <a href="#" data-videha-lang="en">English</a></div><div class="videha-a11y-bar videha-ai-standalone" role="region" aria-label="सुनू, अनुवाद आ सहायक तकनीक" data-pagefind-ignore="all"><button type="button" id="videha-tts-toggle" class="videha-tts-btn">🔊 सुनू · Listen</button><button type="button" id="videha-tts-stop" class="videha-tts-btn" hidden>⏹ रोकू</button><span id="videha-tts-status" class="videha-sr-only" role="status"></span><a href="https://videha-ejournal.github.io/videha/videha-language-studio.htm">Translate with AI (ए.आइ. द्वारा अनुवाद करू)</a> · <a href="https://videha-ejournal.github.io/videha/videha-accessibility.htm">सहायक तकनीक · Assistive Tech</a></div>'''
scripts = '<script src="https://videha-ejournal.github.io/videha/assets/js/videha-tts.js" defer></script><script src="https://videha-ejournal.github.io/videha/assets/js/videha-translate.js" defer></script><script src="https://videha-ejournal.github.io/videha/assets/js/videha-access.js" defer></script>'
footer = '<footer class="videha-copyright-footer">© Gajendra Thakur, Editor, Videha, First Maithili Fortnightly eJournal · <a href="https://www.videha.co.in/">www.videha.co.in</a> · <a href="https://videha-ejournal.github.io/videha/">GitHub mirror</a></footer>'
for p in ROOT.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in {'.htm','.html'} or '.git' in p.parts or '_pagefind_build' in p.parts or p.parent == ROOT:
        continue
    s = p.read_text(encoding='utf8', errors='ignore')
    if 'videha-language-links' not in s:
        s = s.replace('</body>', controls + scripts + footer + '</body>', 1)
    elif 'videha-copyright-footer' not in s:
        s = s.replace('</body>', footer + '</body>', 1)
    p.write_text(s, encoding='utf8')
