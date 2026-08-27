/* ============================================================
   Videha — Free AI Translate Tool
   Adds a "Translate with AI (ए.आइ. द्वारा अनुवाद करू)" button
   beside the Listen (सुनू) button in the accessibility bar.
   Fully self-contained: injects its own button, panel and CSS.
   Translation is done free of cost through the Google AI
   translation proxy (translate.goog) — no API key required.
   (c) Gajendra Thakur, Editor — Videha eJournal
   ============================================================ */
(function () {
  'use strict';

  /* Archive/search pages opt into a compact self-hosted toolbar. Capture the
     executing script now because document.currentScript is null inside init(). */
  var scriptElement = document.currentScript;
  var standalone = !!(scriptElement && scriptElement.hasAttribute('data-videha-translate-standalone'));

  /* Group 1 — the same 23 languages as the Videha 23-language
     transliterator (new_page_101.htm), all supported by the free
     Google AI translator. Group 2 — major world languages. */
  var LANG_GROUPS = [
    ['भारतीय भाषा · Indian languages (23)', [
      ['as',       'অসমীয়া · Assamese'],
      ['bn',       'বাংলা · Bengali'],
      ['brx',      'बड़ो · Bodo'],
      ['doi',      'डोगरी · Dogri'],
      ['en',       'English · अंग्रेजी'],
      ['gu',       'ગુજરાતી · Gujarati'],
      ['hi',       'हिन्दी · Hindi'],
      ['kn',       'ಕನ್ನಡ · Kannada'],
      ['ks',       'کٲشُر · Kashmiri'],
      ['gom',      'कोंकणी · Konkani'],
      ['mai',      'मैथिली · Maithili (मूल भाषा)'],
      ['ml',       'മലയാളം · Malayalam'],
      ['mni-Mtei', 'ꯃꯩꯇꯩꯂꯣꯟ · Manipuri (Meiteilon)'],
      ['mr',       'मराठी · Marathi'],
      ['ne',       'नेपाली · Nepali'],
      ['or',       'ଓଡ଼ିଆ · Odia'],
      ['pa',       'ਪੰਜਾਬੀ · Punjabi'],
      ['sa',       'संस्कृतम् · Sanskrit'],
      ['sat',      'ᱥᱟᱱᱛᱟᱲᱤ · Santhali'],
      ['sd',       'سنڌي · Sindhi'],
      ['ta',       'தமிழ் · Tamil'],
      ['te',       'తెలుగు · Telugu'],
      ['ur',       'اردو · Urdu']
    ]],
    ['विश्व भाषा · World languages', [
      ['zh-CN', '中文（普通话）· Mandarin Chinese'],
      ['yue',   '粵語 · Cantonese'],
      ['fa',    'فارسی · Persian'],
      ['iw',    'עברית · Hebrew'],
      ['bo',    'བོད་སྐད་ · Tibetan'],
      ['si',    'සිංහල · Sinhala'],
      ['es',    'Español · Spanish'],
      ['fr',    'Français · French'],
      ['de',    'Deutsch · German'],
      ['pt',    'Português · Portuguese'],
      ['it',    'Italiano · Italian'],
      ['ru',    'Русский · Russian'],
      ['ar',    'العربية · Arabic'],
      ['ja',    '日本語 · Japanese'],
      ['ko',    '한국어 · Korean'],
      ['id',    'Bahasa Indonesia'],
      ['th',    'ไทย · Thai'],
      ['tr',    'Türkçe · Turkish']
    ]]
  ];

  var LIVE_HOST = 'www.videha.co.in';

  function injectStyles() {
    if (document.getElementById('videha-ai-style')) return;
    var css = '' +
      '.videha-ai-btn{display:inline-flex;align-items:center;gap:6px;margin-left:8px;' +
        'padding:6px 12px;border:1px solid #c49a3c;border-radius:20px;cursor:pointer;' +
        'background:#FAF6EE;color:#8B1A1A;font-family:"Noto Sans Devanagari","Mangal",sans-serif;' +
        'font-size:14px;line-height:1.4;font-weight:600;}' +
      '.videha-ai-btn:hover,.videha-ai-btn:focus-visible{background:#8B1A1A;color:#FAF6EE;border-color:#8B1A1A;}' +
      '.videha-ai-btn .videha-ai-ic{font-size:15px;line-height:1;}' +
      '.videha-ai-wrap{position:relative;display:inline-block;}' +
      '.videha-ai-panel{position:absolute;top:calc(100% + 8px);left:0;z-index:9500;' +
        'min-width:270px;max-width:92vw;background:#FAF6EE;border:1px solid #c49a3c;' +
        'border-radius:10px;box-shadow:0 6px 24px rgba(0,0,0,.22);padding:12px 14px;' +
        'font-family:"Noto Sans Devanagari","Mangal",sans-serif;}' +
      '.videha-ai-panel[hidden]{display:none;}' +
      '.videha-ai-panel h4{margin:0 0 8px;font-size:14px;color:#8B1A1A;font-weight:700;}' +
      '.videha-ai-srcrow{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:0 0 10px;}' +
      '.videha-ai-srclab{font-size:12px;color:#6a5a3a;font-weight:600;margin-right:2px;}' +
      '.videha-ai-src{padding:3px 10px;border:1px solid #c49a3c;border-radius:14px;background:#fff;color:#6a5a3a;cursor:pointer;font-size:12px;font-weight:600;font-family:inherit;}' +
      '.videha-ai-src-on{background:#c49a3c;color:#fff;}' +
      '.videha-ai-quick{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;}' +
      '.videha-ai-quick button{padding:5px 12px;border:1px solid #8B1A1A;border-radius:16px;' +
        'background:#fff;color:#8B1A1A;cursor:pointer;font-size:13px;font-weight:600;' +
        'font-family:inherit;}' +
      '.videha-ai-quick button:hover,.videha-ai-quick button:focus-visible{background:#8B1A1A;color:#fff;}' +
      '.videha-ai-selrow{display:flex;gap:6px;align-items:center;}' +
      '.videha-ai-panel select{flex:1;min-width:0;padding:5px 6px;border:1px solid #c49a3c;' +
        'border-radius:6px;background:#fff;color:#333;font-size:13px;font-family:inherit;}' +
      '.videha-ai-go{padding:5px 14px;border:0;border-radius:16px;background:#8B1A1A;' +
        'color:#fff;cursor:pointer;font-size:13px;font-weight:700;font-family:inherit;}' +
      '.videha-ai-go:hover,.videha-ai-go:focus-visible{background:#6B1212;}' +
      '.videha-ai-note{margin:9px 0 0;font-size:11.5px;color:#6a5a3a;line-height:1.55;}' +
      '.videha-ai-standalone{display:flex;align-items:center;flex-wrap:wrap;gap:8px;' +
        'margin:0 0 16px;padding:10px 12px;border:1px solid #d8cfc0;border-radius:8px;' +
        'background:#faf6ee;position:relative;z-index:20;}' +
      '.videha-ai-standalone .videha-tts-btn{display:inline-flex;align-items:center;gap:6px;' +
        'padding:6px 12px;border:1px solid #c49a3c;border-radius:20px;cursor:pointer;' +
        'background:#faf6ee;color:#8b1a1a;font:600 14px/1.4 "Noto Sans Devanagari","Mangal",sans-serif;}' +
      '.videha-ai-standalone .videha-tts-btn:hover,.videha-ai-standalone .videha-tts-btn:focus-visible{' +
        'background:#8b1a1a;color:#faf6ee;border-color:#8b1a1a;}' +
      '.videha-ai-standalone .videha-sr-only{position:absolute;width:1px;height:1px;margin:-1px;' +
        'padding:0;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0;}' +
      '.videha-ai-standalone .videha-ai-btn{margin-left:0;}' +
      '@media (max-width:600px){.videha-ai-lab-mai{display:none;}' +
        '.videha-ai-btn{font-size:13px;padding:5px 10px;}}';
    var st = document.createElement('style');
    st.id = 'videha-ai-style';
    st.textContent = css;
    document.head.appendChild(st);
  }

  /* Build the free Google AI translation proxy URL for the current page.
     Source language defaults to 'auto' so English/mixed pages translate
     correctly; the user can pin मैथिली or English from the panel. */
  function translatedUrl(lang, src) {
    src = src || 'auto';
    var proto = location.protocol;
    var host, path;
    if (proto === 'http:' || proto === 'https:') {
      host = location.hostname;
      path = location.pathname + location.search;
    } else {
      /* Local preview (file://) — point to the live website copy */
      host = LIVE_HOST;
      var localPath = location.pathname.replace(/\\/g, '/');
      var archiveAt = localPath.lastIndexOf('/search-documents/');
      path = archiveAt >= 0 ? localPath.slice(archiveAt) : '/' + (localPath.split('/').pop() || 'index.htm');
    }
    var gHost = host.replace(/-/g, '--').replace(/\./g, '-') + '.translate.goog';
    var sep = path.indexOf('?') === -1 ? '?' : '&';
    return 'https://' + gHost + path + sep +
      '_x_tr_sl=' + encodeURIComponent(src) +
      '&_x_tr_tl=' + encodeURIComponent(lang) +
      '&_x_tr_hl=' + encodeURIComponent(lang) + '&_x_tr_pto=wapp';
  }

  var currentSrc = 'auto';

  function openTranslation(lang) {
    var w = window.open(translatedUrl(lang, currentSrc), '_blank', 'noopener');
    if (!w) location.href = translatedUrl(lang, currentSrc);
  }

  function buildPanel() {
    var panel = document.createElement('div');
    panel.className = 'videha-ai-panel';
    panel.id = 'videha-ai-panel';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', 'अनुवादक भाषा चुनू · Choose translation language');
    panel.hidden = true;

    var h = document.createElement('h4');
    h.textContent = 'कोन भाषामे अनुवाद करी? · Translate into:';
    panel.appendChild(h);

    /* Source language: auto-detect (default) / मैथिली / English */
    var srow = document.createElement('div');
    srow.className = 'videha-ai-srcrow';
    var slab = document.createElement('span');
    slab.className = 'videha-ai-srclab';
    slab.textContent = 'पृष्ठक मूल भाषा · Page language:';
    srow.appendChild(slab);
    [['auto', 'स्वतः · Auto'], ['mai', 'मैथिली'], ['en', 'English']].forEach(function (s, k) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'videha-ai-src' + (k === 0 ? ' videha-ai-src-on' : '');
      b.textContent = s[1];
      b.setAttribute('aria-pressed', k === 0 ? 'true' : 'false');
      b.addEventListener('click', function () {
        currentSrc = s[0];
        srow.querySelectorAll('.videha-ai-src').forEach(function (x) {
          x.classList.remove('videha-ai-src-on');
          x.setAttribute('aria-pressed', 'false');
        });
        b.classList.add('videha-ai-src-on');
        b.setAttribute('aria-pressed', 'true');
      });
      srow.appendChild(b);
    });
    panel.appendChild(srow);

    var quick = document.createElement('div');
    quick.className = 'videha-ai-quick';
    [['hi', 'हिन्दी'], ['en', 'English'], ['bn', 'বাংলা'], ['ne', 'नेपाली']].forEach(function (q) {
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = q[1];
      b.addEventListener('click', function () { openTranslation(q[0]); });
      quick.appendChild(b);
    });
    panel.appendChild(quick);

    var row = document.createElement('div');
    row.className = 'videha-ai-selrow';
    var sel = document.createElement('select');
    sel.setAttribute('aria-label', 'आन भाषा · Other languages');
    LANG_GROUPS.forEach(function (g) {
      var og = document.createElement('optgroup');
      og.label = g[0];
      g[1].forEach(function (l) {
        var o = document.createElement('option');
        o.value = l[0];
        o.textContent = l[1];
        og.appendChild(o);
      });
      sel.appendChild(og);
    });
    var go = document.createElement('button');
    go.type = 'button';
    go.className = 'videha-ai-go';
    go.textContent = 'अनुवाद करू';
    go.addEventListener('click', function () { openTranslation(sel.value); });
    row.appendChild(sel);
    row.appendChild(go);
    panel.appendChild(row);

    var note = document.createElement('p');
    note.className = 'videha-ai-note';
    note.textContent = 'निःशुल्क ए.आइ. अनुवाद नव टैबमे खुजत। पृष्ठक भाषा स्वतः चिन्हल जाइत अछि; ए.आइ. अनुवादमे किछु त्रुटि सम्भव।';
    panel.appendChild(note);

    return panel;
  }

  function init() {
    var bar = document.querySelector('.videha-a11y-bar');
    if (!bar && standalone) {
      bar = document.createElement('div');
      bar.className = 'videha-a11y-bar videha-ai-standalone';
      bar.setAttribute('aria-label', 'Page translation');
      bar.setAttribute('data-pagefind-ignore', 'all');
      var header = document.querySelector('header');
      if (header) header.appendChild(bar);
      else document.body.insertBefore(bar, document.body.firstChild);
    }
    if (!bar || document.getElementById('videha-ai-translate')) return;
    injectStyles();

    var wrap = document.createElement('span');
    wrap.className = 'videha-ai-wrap';

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'videha-ai-translate';
    btn.className = 'videha-tts-btn videha-ai-btn';
    btn.setAttribute('aria-haspopup', 'dialog');
    btn.setAttribute('aria-expanded', 'false');
    btn.setAttribute('aria-controls', 'videha-ai-panel');
    btn.setAttribute('aria-label', 'Translate with AI · ए.आइ. द्वारा अनुवाद करू');
    btn.title = 'Translate with AI (ए.आइ. द्वारा अनुवाद करू)';
    btn.innerHTML =
      '<span class="videha-ai-ic" aria-hidden="true">🌐</span>' +
      '<span class="videha-ai-lab-en">Translate with AI</span>' +
      '<span class="videha-ai-lab-mai">(ए.आइ. द्वारा अनुवाद करू)</span>';

    var panel = buildPanel();

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = panel.hidden;
      panel.hidden = !open;
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (open) {
        var f = panel.querySelector('button, select');
        if (f) f.focus();
      }
    });

    document.addEventListener('click', function (e) {
      if (!panel.hidden && !wrap.contains(e.target)) {
        panel.hidden = true;
        btn.setAttribute('aria-expanded', 'false');
      }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !panel.hidden) {
        panel.hidden = true;
        btn.setAttribute('aria-expanded', 'false');
        btn.focus();
      }
    });

    wrap.appendChild(btn);
    wrap.appendChild(panel);

    /* Place beside the Listen button (after the Stop button) */
    var stop = bar.querySelector('#videha-tts-stop');
    var toggle = bar.querySelector('#videha-tts-toggle');
    if (stop && stop.nextSibling) bar.insertBefore(wrap, stop.nextSibling);
    else if (stop) bar.appendChild(wrap);
    else if (toggle && toggle.nextSibling) bar.insertBefore(wrap, toggle.nextSibling);
    else bar.appendChild(wrap);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
