/* ============================================================
   Videha — Assistive Technology Panel (सहायक तकनीक)  v2
   Third control beside Listen (सुनू) and Translate with AI.
   Supports multiple assistive-technology families:
     • Screen readers (NVDA/JAWS/TalkBack/VoiceOver): landmarks,
       lang, alt repair, ARIA states, live announcements
     • Magnification / low vision: text size 80–200%, hover
       magnifier, 7:1 high-contrast schemes (WCAG 1.4.6 AAA)
     • Colour-vision: grayscale / inverted colour filters
     • Voice control (speech input): Maithili/Hindi voice
       commands via Web Speech API
     • Motor & switch access: large 44px+ targets (WCAG 2.5.8),
       large cursor, fully keyboard operable (2.1.3 AAA)
     • Cognitive / dyslexia / low literacy: reader view,
       spacing (1.4.12), readable width & no justify (1.4.8 AAA),
       reading guide, stop motion (2.3.3 AAA), link highlight
     • Speech output: speak selected text; page TTS via सुनू
     • Braille: one-tap link to the Videha Devanagari↔Braille
       script converter
   Focus appearance per WCAG 2.4.13 AAA. Preferences persist
   across pages via localStorage.
   (c) Gajendra Thakur, Editor — Videha eJournal
   ============================================================ */
(function () {
  'use strict';

  var KEY = 'videhaA11yPrefs';
  var accessScript = document.currentScript;
  var converterUrl = accessScript && accessScript.src
    ? new URL('../../script-converter.html', accessScript.src).href
    : new URL('script-converter.html', document.baseURI).href;

  var defaults = {
    scale: 100,      /* font size % : 80–200 */
    contrast: 'off', /* off | dark | light */
    filter: 'off',   /* off | gray | invert */
    spacing: false,
    width: false,
    links: false,
    noimg: false,
    guide: false,
    nomotion: false,
    hovmag: false,   /* hover magnifier */
    bigtgt: false,   /* large targets */
    bigcur: false,   /* large cursor */
    reader: false,   /* reader view */
    speaksel: false, /* speak selected text */
    srmode: false    /* built-in screen reader: keyboard reading cursor */
    /* voice control is session-only (microphone), never persisted */
  };

  function load() {
    try {
      var p = JSON.parse(localStorage.getItem(KEY) || '{}');
      var o = {};
      for (var k in defaults) o[k] = (k in p) ? p[k] : defaults[k];
      return o;
    } catch (e) { return JSON.parse(JSON.stringify(defaults)); }
  }
  function save(p) {
    try { localStorage.setItem(KEY, JSON.stringify(p)); } catch (e) {}
  }

  var prefs = load();
  var guideEl = null;
  var readerHidden = [];
  var voiceOn = false;
  var rec = null;

  var CUR = 'url("data:image/svg+xml;utf8,' + encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" viewBox="0 0 44 44">' +
    '<path d="M6 3 L6 33 L14 26 L20 40 L26 37 L20 24 L30 23 Z" fill="black" stroke="white" stroke-width="2.5"/></svg>'
  ) + '") 6 3, auto';

  /* ---------- global stylesheet ---------- */
  function injectStyles() {
    if (document.getElementById('videha-access-style')) return;
    var css = '' +
    '.videha-acc-btn{display:inline-flex;align-items:center;gap:6px;margin-left:8px;' +
      'padding:6px 12px;border:1px solid #c49a3c;border-radius:20px;cursor:pointer;' +
      'background:#FAF6EE;color:#8B1A1A;font-family:"Noto Sans Devanagari","Mangal",sans-serif;' +
      'font-size:14px;line-height:1.4;font-weight:600;}' +
    '.videha-acc-btn:hover,.videha-acc-btn:focus-visible{background:#8B1A1A;color:#FAF6EE;border-color:#8B1A1A;}' +
    '.videha-acc-wrap{position:relative;display:inline-block;}' +
    '.videha-acc-panel{position:absolute;top:calc(100% + 8px);left:0;z-index:9600;' +
      'width:352px;max-width:94vw;max-height:72vh;overflow-y:auto;background:#FAF6EE;' +
      'border:1px solid #c49a3c;border-radius:10px;box-shadow:0 6px 24px rgba(0,0,0,.22);' +
      'padding:14px 16px;font-family:"Noto Sans Devanagari","Mangal",sans-serif;color:#232019;}' +
    '.videha-acc-panel[hidden]{display:none;}' +
    '.videha-acc-panel h4{margin:0 0 10px;font-size:15px;color:#8B1A1A;font-weight:700;}' +
    '.videha-acc-panel h5{margin:12px 0 7px;font-size:12.5px;color:#a67c28;font-weight:700;' +
      'letter-spacing:.04em;border-bottom:1px solid #e6d6b0;padding-bottom:3px;}' +
    '.videha-acc-row{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:0 0 8px;}' +
    '.videha-acc-lab{font-size:13.5px;font-weight:600;flex:1;}' +
    '.videha-acc-seg{display:flex;gap:5px;align-items:center;}' +
    '.videha-acc-panel button.videha-acc-t{padding:4px 11px;border:1px solid #8B1A1A;border-radius:14px;' +
      'background:#fff;color:#8B1A1A;cursor:pointer;font-size:13px;font-weight:700;font-family:inherit;min-width:40px;}' +
    '.videha-acc-panel button.videha-acc-t[aria-pressed="true"]{background:#8B1A1A;color:#fff;}' +
    '.videha-acc-panel button.videha-acc-t:focus-visible{outline:3px solid #1F2A44;outline-offset:2px;}' +
    '.videha-acc-scaleval{min-width:52px;text-align:center;font-weight:700;font-size:13px;color:#6a5a3a;}' +
    '.videha-acc-reset{margin-top:8px;width:100%;padding:7px 0;border:0;border-radius:16px;' +
      'background:#c49a3c;color:#fff;cursor:pointer;font-size:13.5px;font-weight:700;font-family:inherit;}' +
    '.videha-acc-reset:hover,.videha-acc-reset:focus-visible{background:#a67c28;}' +
    '.videha-acc-note{margin:9px 0 0;font-size:11.5px;color:#6a5a3a;line-height:1.6;}' +
    '.videha-sr-only-acc{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;' +
      'clip:rect(0 0 0 0);white-space:nowrap;border:0;}' +
    '@media (max-width:600px){.videha-acc-lab-txt{display:none;}.videha-acc-btn{font-size:13px;padding:5px 10px;}}' +

    /* focus appearance (WCAG 2.4.13) */
    'html.videha-acc-on :focus-visible{outline:3px solid #1F2A44 !important;outline-offset:2px !important;}' +
    'html.videha-hc-dark.videha-acc-on :focus-visible{outline-color:#FFD34D !important;}' +

    /* text scaling */
    'html.videha-scale body{font-size:calc(1em * var(--videha-scale,1)) !important;}' +

    /* high contrast */
    'html.videha-hc-dark, html.videha-hc-dark body{background:#000 !important;color:#FFEE99 !important;}' +
    'html.videha-hc-dark body *{background-color:#000 !important;color:#FFEE99 !important;' +
      'border-color:#FFD34D !important;text-shadow:none !important;box-shadow:none !important;}' +
    'html.videha-hc-dark a, html.videha-hc-dark a *{color:#7FD8FF !important;text-decoration:underline !important;}' +
    'html.videha-hc-dark img{filter:brightness(.9) contrast(1.1);}' +
    'html.videha-hc-light, html.videha-hc-light body{background:#FFFFFF !important;color:#111111 !important;}' +
    'html.videha-hc-light body *{background-color:#FFFFFF !important;color:#111111 !important;' +
      'border-color:#111111 !important;text-shadow:none !important;box-shadow:none !important;}' +
    'html.videha-hc-light a, html.videha-hc-light a *{color:#0000CC !important;text-decoration:underline !important;}' +

    /* colour-vision filters */
    'html.videha-gray body{filter:grayscale(1) !important;}' +
    'html.videha-invert body{filter:invert(1) hue-rotate(180deg) !important;background:#111 !important;}' +

    /* spacing */
    'html.videha-space body, html.videha-space body p, html.videha-space body li, html.videha-space body td,' +
    'html.videha-space body div, html.videha-space body span{line-height:2 !important;' +
      'letter-spacing:.12em !important;word-spacing:.16em !important;}' +
    'html.videha-space body p{margin-bottom:2em !important;}' +

    /* readable measure */
    'html.videha-width body p, html.videha-width body li{max-width:70ch !important;' +
      'text-align:left !important;margin-left:auto;margin-right:auto;}' +

    /* link visibility */
    'html.videha-links a{text-decoration:underline !important;text-underline-offset:2px;' +
      'background:#FFF3C4 !important;color:#5A1010 !important;font-weight:700 !important;}' +
    'html.videha-hc-dark.videha-links a{background:#333300 !important;color:#7FD8FF !important;}' +

    /* hide images */
    'html.videha-noimg img, html.videha-noimg svg, html.videha-noimg video, html.videha-noimg iframe' +
      '{visibility:hidden !important;}' +

    /* stop motion */
    'html.videha-still *, html.videha-still *::before, html.videha-still *::after{' +
      'animation:none !important;transition:none !important;scroll-behavior:auto !important;}' +

    /* reading guide */
    '#videha-read-guide{position:fixed;left:0;right:0;height:3.2em;pointer-events:none;z-index:9550;' +
      'background:rgba(196,154,60,.18);border-top:2px solid #8B1A1A;border-bottom:2px solid #8B1A1A;' +
      'transform:translateY(-50%);}' +
    'html.videha-hc-dark #videha-read-guide{background:rgba(255,211,77,.16);border-color:#FFD34D;}' +

    /* hover magnifier (low vision) */
    'html.videha-hovmag main p:hover, html.videha-hovmag [role="main"] p:hover,' +
    'html.videha-hovmag main li:hover, html.videha-hovmag [role="main"] li:hover{' +
      'font-size:1.45em !important;line-height:1.9 !important;background:#FFFBE8 !important;' +
      'outline:2px solid #c49a3c;}' +
    'html.videha-hc-dark.videha-hovmag main p:hover, html.videha-hc-dark.videha-hovmag [role="main"] p:hover{' +
      'background:#1a1a00 !important;}' +

    /* large targets (motor / switch access, WCAG 2.5.8) */
    'html.videha-bigtgt body a, html.videha-bigtgt body button, html.videha-bigtgt body input,' +
    'html.videha-bigtgt body select, html.videha-bigtgt body [role="button"]{' +
      'min-height:44px !important;min-width:44px !important;padding:10px 14px !important;' +
      'font-size:1.08em !important;display:inline-flex;align-items:center;}' +

    /* large cursor */
    'html.videha-bigcur, html.videha-bigcur body, html.videha-bigcur body *{cursor:' + CUR + ' !important;}' +

    /* built-in screen reader cursor + chip */
    '.videha-sr-cursor{outline:4px solid #c49a3c !important;outline-offset:2px;background:rgba(196,154,60,.18) !important;}' +
    'html.videha-hc-dark .videha-sr-cursor{outline-color:#FFD34D !important;background:rgba(255,211,77,.14) !important;}' +
    '#videha-sr-chip{position:fixed;left:14px;bottom:14px;z-index:9700;background:#1F2A44;color:#fff;'+
      'padding:8px 14px;border-radius:20px;font-family:"Noto Sans Devanagari","Mangal",sans-serif;'+
      'font-size:13px;font-weight:700;box-shadow:0 4px 14px rgba(0,0,0,.3);}' +
    /* voice-control on-air chip */
    '#videha-voice-chip{position:fixed;right:14px;bottom:14px;z-index:9700;background:#8B1A1A;color:#fff;' +
      'padding:8px 14px;border-radius:20px;font-family:"Noto Sans Devanagari","Mangal",sans-serif;' +
      'font-size:13px;font-weight:700;box-shadow:0 4px 14px rgba(0,0,0,.3);}';
    var st = document.createElement('style');
    st.id = 'videha-access-style';
    st.textContent = css;
    document.head.appendChild(st);
  }

  /* ---------- apply preferences ---------- */
  function apply() {
    var root = document.documentElement;
    root.classList.add('videha-acc-on');
    root.style.setProperty('--videha-scale', String(prefs.scale / 100));
    root.classList.toggle('videha-scale', prefs.scale !== 100);
    root.classList.toggle('videha-hc-dark', prefs.contrast === 'dark');
    root.classList.toggle('videha-hc-light', prefs.contrast === 'light');
    root.classList.toggle('videha-gray', prefs.filter === 'gray');
    root.classList.toggle('videha-invert', prefs.filter === 'invert');
    root.classList.toggle('videha-space', !!prefs.spacing);
    root.classList.toggle('videha-width', !!prefs.width);
    root.classList.toggle('videha-links', !!prefs.links);
    root.classList.toggle('videha-noimg', !!prefs.noimg);
    root.classList.toggle('videha-still', !!prefs.nomotion);
    root.classList.toggle('videha-hovmag', !!prefs.hovmag);
    root.classList.toggle('videha-bigtgt', !!prefs.bigtgt);
    root.classList.toggle('videha-bigcur', !!prefs.bigcur);
    setGuide(!!prefs.guide);
    setReader(!!prefs.reader);
    setSpeakSel(!!prefs.speaksel);
    setSrMode(!!prefs.srmode);
    save(prefs);
  }

  /* ---------- reading guide ---------- */
  function setGuide(on) {
    if (on && !guideEl) {
      guideEl = document.createElement('div');
      guideEl.id = 'videha-read-guide';
      guideEl.setAttribute('aria-hidden', 'true');
      guideEl.style.top = '40%';
      document.body.appendChild(guideEl);
      document.addEventListener('mousemove', moveGuide);
      document.addEventListener('touchmove', moveGuideTouch, {passive: true});
    } else if (!on && guideEl) {
      document.removeEventListener('mousemove', moveGuide);
      document.removeEventListener('touchmove', moveGuideTouch);
      guideEl.remove();
      guideEl = null;
    }
  }
  function moveGuide(e) { if (guideEl) guideEl.style.top = e.clientY + 'px'; }
  function moveGuideTouch(e) {
    if (guideEl && e.touches && e.touches[0]) guideEl.style.top = e.touches[0].clientY + 'px';
  }

  /* ---------- reader view (cognitive) ---------- */
  function setReader(on) {
    if (on && !readerHidden.length) {
      var main = document.querySelector('main,[role="main"]');
      if (!main) return;
      var keep = new Set();
      var el = main;
      while (el) { keep.add(el); el = el.parentElement; }
      var bar = document.querySelector('.videha-a11y-bar');
      el = bar;
      while (el) { keep.add(el); el = el.parentElement; }
      var kids = document.body.children;
      for (var i = 0; i < kids.length; i++) {
        var k = kids[i];
        if (keep.has(k) || k.id === 'videha-read-guide' || k.id === 'videha-voice-chip' ||
            k.tagName === 'SCRIPT' || k.tagName === 'STYLE' ||
            k.classList.contains('videha-sr-only-acc')) continue;
        if (k.contains(main) || (bar && k.contains(bar))) continue;
        if (k.style.display !== 'none') {
          readerHidden.push([k, k.style.display]);
          k.style.display = 'none';
        }
      }
    } else if (!on && readerHidden.length) {
      readerHidden.forEach(function (pair) { pair[0].style.display = pair[1]; });
      readerHidden = [];
    }
  }

  /* ---------- speech output: speak selection ---------- */
  function pickVoice() {
    var synth = window.speechSynthesis;
    if (!synth) return null;
    var voices = synth.getVoices() || [];
    function byLang(re) {
      for (var i = 0; i < voices.length; i++) {
        if (re.test(voices[i].lang || '') || re.test(voices[i].name || '')) return voices[i];
      }
      return null;
    }
    return byLang(/^mai/i) || byLang(/maithili/i) || byLang(/^hi[-_]?in/i) ||
           byLang(/^hi\b/i) || byLang(/hindi/i) || byLang(/^en[-_]?in/i) || null;
  }
  function speakText(t) {
    var synth = window.speechSynthesis;
    if (!synth || typeof SpeechSynthesisUtterance === 'undefined' || !t) return;
    synth.cancel();
    var u = new SpeechSynthesisUtterance(t.slice(0, 4000));
    var v = pickVoice();
    if (v) u.voice = v;
    u.lang = (v && v.lang) || 'hi-IN';
    u.rate = 0.95;
    synth.speak(u);
  }
  function selHandler() {
    setTimeout(function () {
      var s = String(window.getSelection ? window.getSelection() : '').trim();
      if (s && s.length > 1) speakText(s);
    }, 120);
  }
  function setSpeakSel(on) {
    document.removeEventListener('mouseup', selHandler);
    document.removeEventListener('keyup', selHandler);
    if (on) {
      document.addEventListener('mouseup', selHandler);
      document.addEventListener('keyup', selHandler);
    } else if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  }

  /* ---------- built-in screen reader (keyboard reading cursor) ---------- */
  var srBlocks = [], srIdx = -1, srCur = null;
  function srLabel(el) {
    var t = el.tagName, pre = '';
    if (/^H[1-6]$/.test(t)) pre = 'शीर्षक स्तर ' + t.charAt(1) + '। ';
    else if (t === 'LI') pre = 'सूची। ';
    else if (t === 'A') pre = 'लिंक। ';
    else if (t === 'BUTTON') pre = 'बटन। ';
    else if (t === 'TD' || t === 'TH') pre = 'तालिका। ';
    return pre + (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 600);
  }
  function srCollect() {
    var main = document.querySelector('main,[role="main"]') || document.body;
    srBlocks = Array.prototype.slice.call(
      main.querySelectorAll('h1,h2,h3,h4,h5,h6,p,li,td,th,blockquote')
    ).filter(function (e) {
      return (e.textContent || '').trim().length > 1 && !e.closest('.videha-acc-panel');
    });
  }
  function srClear() {
    if (srCur) { srCur.classList.remove('videha-sr-cursor'); srCur = null; }
  }
  function srGo(idx) {
    if (!srBlocks.length) srCollect();
    if (!srBlocks.length) return;
    srIdx = Math.max(0, Math.min(srBlocks.length - 1, idx));
    srClear();
    srCur = srBlocks[srIdx];
    srCur.classList.add('videha-sr-cursor');
    try { srCur.scrollIntoView({block: 'center'}); }
    catch (e) { try { srCur.scrollIntoView(); } catch (e2) {} }
    var msg = srLabel(srCur);
    speakText(msg);
    announce(msg.slice(0, 200));
  }
  function srNextHeading(dir) {
    if (!srBlocks.length) srCollect();
    var i = srIdx;
    while (true) {
      i += dir;
      if (i < 0 || i >= srBlocks.length) return;
      if (/^H[1-6]$/.test(srBlocks[i].tagName)) { srGo(i); return; }
    }
  }
  function srKey(e) {
    if (!prefs.srmode) return;
    var tg = e.target;
    if (tg && /^(INPUT|TEXTAREA|SELECT)$/.test(tg.tagName)) return;
    var panel = document.getElementById('videha-acc-panel');
    if (panel && !panel.hidden && panel.contains(tg)) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); srGo(srIdx + 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); srGo(srIdx - 1); }
    else if (e.key === 'h' || e.key === 'H') { e.preventDefault(); srNextHeading(1); }
    else if (e.key === 'g' || e.key === 'G') { e.preventDefault(); srNextHeading(-1); }
  }
  function srFocus(e) {
    if (!prefs.srmode) return;
    var el = e.target;
    if (!el || !el.tagName) return;
    if (/^(A|BUTTON|INPUT|SELECT|TEXTAREA)$/.test(el.tagName)) {
      var lb = el.getAttribute('aria-label') || (el.textContent || '').trim() || el.value || '';
      if (lb) speakText((el.tagName === 'A' ? 'लिंक। ' : el.tagName === 'BUTTON' ? 'बटन। ' : '') + lb.slice(0, 300));
    }
  }
  function srChip(on) {
    var c = document.getElementById('videha-sr-chip');
    if (on && !c) {
      c = document.createElement('div');
      c.id = 'videha-sr-chip';
      c.setAttribute('role', 'status');
      c.textContent = '⌨ वाचक चालू — ↓/↑ आगाँ-पाछाँ · H शीर्षक · Tab लिंक';
      document.body.appendChild(c);
    } else if (!on && c) c.remove();
  }
  function setSrMode(on) {
    document.removeEventListener('keydown', srKey, true);
    document.removeEventListener('focusin', srFocus);
    if (on) {
      srCollect();
      document.addEventListener('keydown', srKey, true);
      document.addEventListener('focusin', srFocus);
      srChip(true);
    } else {
      srChip(false);
      srClear();
      srIdx = -1;
      if (window.speechSynthesis) window.speechSynthesis.cancel();
    }
  }

  /* ---------- voice control (speech input) ---------- */
  function voiceChip(on) {
    var c = document.getElementById('videha-voice-chip');
    if (on && !c) {
      c = document.createElement('div');
      c.id = 'videha-voice-chip';
      c.setAttribute('role', 'status');
      c.textContent = '🎤 सुनि रहल छी… ("ऊपर", "नीचाँ", "सुनाउ", "रोकू")';
      document.body.appendChild(c);
    } else if (!on && c) c.remove();
  }
  function handleCommand(t) {
    t = (t || '').toLowerCase();
    function has(re) { return re.test(t); }
    if (has(/शीर्ष|सबसे ऊपर|\btop\b/)) window.scrollTo({top: 0});
    else if (has(/अंत|सबसे नीच|\bbottom\b|\bend\b/)) window.scrollTo({top: document.body.scrollHeight});
    else if (has(/ऊपर|उपर|\bup\b/)) window.scrollBy({top: -420});
    else if (has(/नीच|नीचे|niche|\bdown\b/)) window.scrollBy({top: 420});
    else if (has(/रोक|रुक|\bstop\b|बंद|बन्द/)) {
      var sb = document.getElementById('videha-tts-stop');
      if (sb && !sb.hidden) sb.click();
      if (window.speechSynthesis) window.speechSynthesis.cancel();
    }
    else if (has(/सुना|पढ़|पढ|\bread\b|\blisten\b/)) {
      var tb = document.getElementById('videha-tts-toggle');
      if (tb) tb.click();
    }
    else if (has(/अनुवाद|translate/)) {
      var ab = document.getElementById('videha-ai-translate');
      if (ab) ab.click();
    }
  }
  function setVoice(on, btn) {
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (on) {
      if (!SR) {
        announce('एहि ब्राउज़रमे आवाज-नियंत्रण उपलब्ध नहि · Voice control not supported in this browser');
        if (btn) { btn.setAttribute('aria-pressed', 'false'); btn.textContent = 'चालू'; }
        return;
      }
      try {
        rec = new SR();
        rec.lang = 'hi-IN';
        rec.continuous = true;
        rec.interimResults = false;
        rec.onresult = function (e) {
          var r = e.results[e.results.length - 1];
          if (r && r[0]) handleCommand(r[0].transcript);
        };
        rec.onend = function () {
          if (voiceOn) { try { rec.start(); } catch (er) {} }
        };
        rec.onerror = function (e) {
          if (e && (e.error === 'not-allowed' || e.error === 'service-not-allowed')) {
            voiceOn = false; voiceChip(false);
            if (btn) { btn.setAttribute('aria-pressed', 'false'); btn.textContent = 'चालू'; }
            announce('माइक्रोफोनक अनुमति नहि भेटल · Microphone permission denied');
          }
        };
        rec.start();
        voiceOn = true;
        voiceChip(true);
        announce('आवाज-नियंत्रण चालू। कहू: ऊपर, नीचाँ, शीर्ष, अंत, सुनाउ, रोकू, अनुवाद');
      } catch (e) { voiceOn = false; }
    } else {
      voiceOn = false;
      voiceChip(false);
      if (rec) { try { rec.stop(); } catch (e) {} rec = null; }
      announce('आवाज-नियंत्रण बन्द');
    }
  }

  /* ---------- automatic screen-reader repairs ---------- */
  function autoRepair() {
    var root = document.documentElement;
    if (!root.getAttribute('lang')) root.setAttribute('lang', 'mai');
    if (!document.querySelector('main,[role="main"]')) {
      var cand = document.querySelector('.videha-main-content, #main, .main, body > table, body > div');
      if (cand) cand.setAttribute('role', 'main');
    }
    var imgs = document.getElementsByTagName('img');
    for (var i = 0; i < imgs.length; i++) {
      if (!imgs[i].hasAttribute('alt')) imgs[i].setAttribute('alt', '');
    }
  }

  /* ---------- live announcements ---------- */
  var live;
  function announce(msg) {
    if (!live) {
      live = document.createElement('span');
      live.className = 'videha-sr-only-acc';
      live.setAttribute('role', 'status');
      live.setAttribute('aria-live', 'polite');
      document.body.appendChild(live);
    }
    live.textContent = '';
    setTimeout(function () { live.textContent = msg; }, 60);
  }

  /* ---------- panel helpers ---------- */
  function section(panel, txt) {
    var h = document.createElement('h5');
    h.textContent = txt;
    panel.appendChild(h);
  }
  function segRow(label, buttons) {
    var row = document.createElement('div');
    row.className = 'videha-acc-row';
    var lab = document.createElement('span');
    lab.className = 'videha-acc-lab';
    lab.textContent = label;
    row.appendChild(lab);
    var seg = document.createElement('div');
    seg.className = 'videha-acc-seg';
    buttons.forEach(function (b) { seg.appendChild(b); });
    row.appendChild(seg);
    return row;
  }
  function tbtn(text, aria, onclick) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'videha-acc-t';
    b.textContent = text;
    b.setAttribute('aria-label', aria);
    b.setAttribute('aria-pressed', 'false');
    b.addEventListener('click', onclick);
    return b;
  }

  /* ---------- panel ---------- */
  function buildPanel() {
    var panel = document.createElement('div');
    panel.className = 'videha-acc-panel';
    panel.id = 'videha-acc-panel';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', 'सहायक तकनीक सेटिंग · Assistive technology settings');
    panel.hidden = true;

    var h = document.createElement('h4');
    h.textContent = 'सहायक तकनीक · Assistive Tech (WCAG AAA)';
    panel.appendChild(h);

    var toggles = [];
    function toggle(label, aria, key, msgOn, msgOff) {
      var b = tbtn('चालू', aria, function () {
        prefs[key] = !prefs[key]; apply();
        b.setAttribute('aria-pressed', prefs[key] ? 'true' : 'false');
        b.textContent = prefs[key] ? 'बन्द करू' : 'चालू';
        announce(prefs[key] ? msgOn : msgOff);
      });
      if (prefs[key]) { b.setAttribute('aria-pressed', 'true'); b.textContent = 'बन्द करू'; }
      panel.appendChild(segRow(label, [b]));
      toggles.push([b, key]);
      return b;
    }

    /* ===== स्क्रीन-रीडर · Screen reader ===== */
    section(panel, 'स्क्रीन-रीडर · Screen reader');

    toggle('अन्तर्निहित वाचक · Built-in reader',
      'कीबोर्डसँ पढ़ू: नीचाँ-ऊपर तीरसँ आगाँ-पाछाँ, H सँ अगिला शीर्षक · Keyboard reading cursor: arrows move, H next heading',
      'srmode', 'अन्तर्निहित वाचक चालू। नीचाँ तीर दबाउ', 'अन्तर्निहित वाचक बन्द');

    var rd = tbtn('पढ़ू', 'सम्पूर्ण पृष्ठ आरम्भसँ सुनू · Read the whole page aloud', function () {
      var tb = document.getElementById('videha-tts-toggle');
      if (tb) tb.click();
      announce('पूरा पृष्ठ पढ़ल जा रहल अछि');
    });
    panel.appendChild(segRow('पूरा पृष्ठ सुनू · Read full page', [rd]));

    var nv = tbtn('NVDA', 'NVDA निःशुल्क स्क्रीन-रीडर डाउनलोड करू · Download the free NVDA screen reader', function () {
      var w = window.open('https://www.nvaccess.org/download/', '_blank', 'noopener');
      if (!w) location.href = 'https://www.nvaccess.org/download/';
    });
    panel.appendChild(segRow('निःशुल्क स्क्रीन-रीडर · Free download', [nv]));

    var osn = document.createElement('p');
    osn.className = 'videha-acc-note';
    osn.style.margin = '2px 0 6px';
    osn.textContent = 'प्रणालीक निज वाचक: Windows Narrator (Ctrl+⊞+Enter) · Android TalkBack · iPhone VoiceOver — ई साइट सभसँ पूर्ण-संगत अछि।';
    panel.appendChild(osn);

    /* ===== दृष्टि · Vision ===== */
    section(panel, 'दृष्टि · Vision (low vision / colour-blind)');

    var scaleVal = document.createElement('span');
    scaleVal.className = 'videha-acc-scaleval';
    scaleVal.setAttribute('aria-hidden', 'true');
    function showScale() { scaleVal.textContent = prefs.scale + '%'; }
    var minus = tbtn('A−', 'अक्षर छोट करू · Decrease text size', function () {
      prefs.scale = Math.max(80, prefs.scale - 10); apply(); showScale();
      announce('अक्षर आकार ' + prefs.scale + ' प्रतिशत');
    });
    var plus = tbtn('A+', 'अक्षर पैघ करू · Increase text size', function () {
      prefs.scale = Math.min(200, prefs.scale + 10); apply(); showScale();
      announce('अक्षर आकार ' + prefs.scale + ' प्रतिशत');
    });
    showScale();
    var srow = document.createElement('div');
    srow.className = 'videha-acc-row';
    var slab = document.createElement('span');
    slab.className = 'videha-acc-lab';
    slab.textContent = 'अक्षर आकार · Text size';
    srow.appendChild(slab);
    var sseg = document.createElement('div');
    sseg.className = 'videha-acc-seg';
    sseg.appendChild(minus); sseg.appendChild(scaleVal); sseg.appendChild(plus);
    srow.appendChild(sseg);
    panel.appendChild(srow);

    var cOff, cDark, cLight;
    function setContrast(mode) {
      prefs.contrast = mode; apply();
      [cOff, cDark, cLight].forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
      (mode === 'dark' ? cDark : mode === 'light' ? cLight : cOff).setAttribute('aria-pressed', 'true');
      announce(mode === 'off' ? 'सामान्य रंग' : 'उच्च कोन्ट्रास्ट चालू');
    }
    cOff = tbtn('सामान्य', 'सामान्य रंग · Normal colours', function () { setContrast('off'); });
    cDark = tbtn('कारी', 'कारी पृष्ठभूमि, पीयर अक्षर · Yellow on black, 7:1', function () { setContrast('dark'); });
    cLight = tbtn('उज्जर', 'उज्जर पृष्ठभूमि, कारी अक्षर · Black on white, 7:1', function () { setContrast('light'); });
    panel.appendChild(segRow('उच्च कोन्ट्रास्ट · Contrast', [cOff, cDark, cLight]));

    var fOff, fGray, fInv;
    function setFilter(mode) {
      prefs.filter = mode; apply();
      [fOff, fGray, fInv].forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
      (mode === 'gray' ? fGray : mode === 'invert' ? fInv : fOff).setAttribute('aria-pressed', 'true');
      announce(mode === 'off' ? 'रंग सामान्य' : mode === 'gray' ? 'धूसर रंग चालू' : 'उल्टा रंग चालू');
    }
    fOff = tbtn('सामान्य', 'सामान्य रंग · Normal', function () { setFilter('off'); });
    fGray = tbtn('धूसर', 'धूसर (grayscale) · For colour-vision needs', function () { setFilter('gray'); });
    fInv = tbtn('उल्टा', 'उल्टा रंग (invert) · Inverted colours', function () { setFilter('invert'); });
    panel.appendChild(segRow('रंग-दृष्टि · Colour filter', [fOff, fGray, fInv]));

    toggle('अनुच्छेद-आवर्धक · Hover magnify', 'जाहि अनुच्छेदपर pointer, से पैघ · Magnify paragraph under pointer', 'hovmag', 'आवर्धक चालू', 'आवर्धक बन्द');
    toggle('चित्र छिपाउ · Hide images', 'सभ चित्र छिपाउ · Hide all images', 'noimg', 'चित्र छिपाओल गेल', 'चित्र देखाओल गेल');

    /* ===== वाणी · Voice & speech ===== */
    section(panel, 'वाणी · Voice control & speech');

    var vBtn = tbtn('चालू', 'आवाजसँ पृष्ठ चलाउ (माइक चाही) · Voice commands, needs microphone', function () {
      var turnOn = !voiceOn;
      vBtn.setAttribute('aria-pressed', turnOn ? 'true' : 'false');
      vBtn.textContent = turnOn ? 'बन्द करू' : 'चालू';
      setVoice(turnOn, vBtn);
    });
    panel.appendChild(segRow('आवाजसँ चलाउ · Voice commands', [vBtn]));

    toggle('चुनल पाठ सुनू · Speak selection', 'जे पाठ चुनब से बाजल जाएत · Selected text is read aloud', 'speaksel', 'चुनल पाठ बाजत', 'चुनल पाठ बाजब बन्द');

    /* ===== गति · Motor & switch ===== */
    section(panel, 'गति-सहायता · Motor & switch access');
    toggle('पैघ बटन-लिंक · Large targets', 'सभ बटन आ लिंक ४४px सँ पैघ · All targets 44px or larger', 'bigtgt', 'पैघ लक्ष्य चालू', 'पैघ लक्ष्य बन्द');
    toggle('पैघ cursor · Large cursor', 'पैघ माउस-cursor · Large mouse cursor', 'bigcur', 'पैघ cursor चालू', 'पैघ cursor बन्द');

    /* ===== पठन · Reading & cognitive ===== */
    section(panel, 'पठन-सहायता · Reading, dyslexia & cognitive');
    toggle('पाठ-मात्र दृश्य · Reader view', 'मात्र मुख्य पाठ देखाउ · Show main text only', 'reader', 'पाठ-मात्र दृश्य चालू', 'पूर्ण पृष्ठ');
    toggle('पंक्ति-अन्तर बेसी · Spacing', 'पंक्ति, अक्षर आ शब्द अन्तर बढ़ाउ · Increase spacing', 'spacing', 'अन्तर बढ़ाओल गेल', 'अन्तर सामान्य');
    toggle('सुपाठ्य चौड़ाइ · Readable width', 'पंक्ति ७० अक्षर धरि, justification बन्द', 'width', 'सुपाठ्य चौड़ाइ चालू', 'सुपाठ्य चौड़ाइ बन्द');
    toggle('लिंक उजागर · Highlight links', 'सभ लिंक रेखांकित आ उजागर', 'links', 'लिंक उजागर चालू', 'लिंक उजागर बन्द');
    toggle('पठन-रेखा · Reading guide', 'पठन-रेखा pointer-संग चलत', 'guide', 'पठन-रेखा चालू', 'पठन-रेखा बन्द');
    toggle('गति रोकू · Stop motion', 'सभ एनिमेशन रोकू', 'nomotion', 'गति रोकल गेल', 'गति सामान्य');

    /* ===== ब्रेल · Braille ===== */
    section(panel, 'ब्रेल · Braille');
    var br = tbtn('खोलू', 'विदेहक देवनागरी-ब्रेल परिवर्तक खोलू · Open the Videha Devanagari–Braille converter', function () {
      var w = window.open(converterUrl, '_blank', 'noopener');
      if (!w) location.href = converterUrl;
    });
    panel.appendChild(segRow('देवनागरी ↔ ब्रेल परिवर्तक', [br]));

    /* reset */
    var reset = document.createElement('button');
    reset.type = 'button';
    reset.className = 'videha-acc-reset';
    reset.textContent = 'सभ सेटिंग reset करू · Reset all';
    reset.addEventListener('click', function () {
      prefs = JSON.parse(JSON.stringify(defaults)); apply(); showScale();
      setContrast('off'); setFilter('off');
      if (voiceOn) { setVoice(false, vBtn); }
      vBtn.setAttribute('aria-pressed', 'false'); vBtn.textContent = 'चालू';
      toggles.forEach(function (pair) {
        pair[0].setAttribute('aria-pressed', 'false');
        pair[0].textContent = 'चालू';
      });
      announce('सभ सेटिंग सामान्य कएल गेल');
    });
    panel.appendChild(reset);

    var note = document.createElement('p');
    note.className = 'videha-acc-note';
    note.textContent = 'ई सेटिंग सभ पृष्ठपर सुरक्षित रहत। स्क्रीन-रीडर (अन्तर्निहित + NVDA/JAWS/TalkBack/VoiceOver), स्विच-एक्सेस, आवाज-नियंत्रण, आवर्धक आ ब्रेल — सभ सहायक तकनीकक हेतु।';
    panel.appendChild(note);

    setTimeout(function () { setContrast(prefs.contrast); setFilter(prefs.filter); }, 0);

    return panel;
  }

  /* ---------- init ---------- */
  function init() {
    injectStyles();
    autoRepair();
    apply();

    var bar = document.querySelector('.videha-a11y-bar');
    if (!bar || document.getElementById('videha-acc-toggle')) return;

    var wrap = document.createElement('span');
    wrap.className = 'videha-acc-wrap';

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'videha-acc-toggle';
    btn.className = 'videha-tts-btn videha-acc-btn';
    btn.setAttribute('aria-haspopup', 'dialog');
    btn.setAttribute('aria-expanded', 'false');
    btn.setAttribute('aria-controls', 'videha-acc-panel');
    btn.setAttribute('aria-label', 'सहायक तकनीक: स्क्रीन-रीडर, आवाज-नियंत्रण, आवर्धक, ब्रेल आदि · Assistive technologies: screen reader, voice control, magnifier, braille and more');
    btn.title = 'सहायक तकनीक · Assistive Tech (WCAG 2.2 accessibility tools)';
    btn.innerHTML =
      '<span class="videha-ai-ic" aria-hidden="true">♿</span>' +
      '<span>सहायक तकनीक</span>' +
      '<span class="videha-acc-lab-txt">· Assistive Tech</span>';

    var panel = buildPanel();

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = panel.hidden;
      panel.hidden = !open;
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (open) {
        var f = panel.querySelector('button');
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
    bar.appendChild(wrap);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();


/* Videha WCAG 2.2 baseline semantics — additive */
(function(){
  'use strict';

  function associatedLabel(el){
    if (!el) return false;
    if (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby')) return true;
    if (el.closest && el.closest('label')) return true;
    if (el.id) {
      try { if (document.querySelector('label[for="' + CSS.escape(el.id) + '"]')) return true; }
      catch(e) { if (document.querySelector('label[for="' + el.id.replace(/"/g,'\\"') + '"]')) return true; }
    }
    return false;
  }

  function humanId(id){
    return String(id || '').replace(/^videha[-_]?/i,'').replace(/[-_]+/g,' ').trim();
  }

  function repairNames(){
    var ctrls=document.querySelectorAll('input:not([type="hidden"]),select,textarea,button');
    for(var i=0;i<ctrls.length;i++){
      var el=ctrls[i];
      if (associatedLabel(el)) continue;
      if (el.tagName==='BUTTON' && el.textContent.trim()) continue;
      if (el.tagName==='INPUT' && /^(submit|reset|button)$/i.test(el.type||'') && el.value) continue;
      var n=(el.getAttribute('placeholder')||el.getAttribute('title')||humanId(el.id)||'').trim();
      if(n) el.setAttribute('aria-label',n);
    }
  }

  function repairNav(){
    var navs=document.querySelectorAll('nav.videha-nav');
    for(var n=0;n<navs.length;n++){
      var nav=navs[n];
      if(!nav.getAttribute('aria-label')) nav.setAttribute('aria-label','मुख्य नेविगेशन · Main navigation');
      var panel=nav.querySelector('.videha-nav-inner');
      var btn=nav.querySelector('.videha-nav-toggle');
      if(!panel || !btn) continue;
      if(!panel.id) panel.id='videha-primary-nav' + (n ? '-' + (n+1) : '');
      btn.setAttribute('aria-controls',panel.id);
      btn.setAttribute('aria-expanded',panel.classList.contains('open')?'true':'false');
      if((btn.getAttribute('aria-label')||'').toLowerCase()==='menu') btn.setAttribute('aria-label','मेनू · Menu');
      (function(b,p){
        b.addEventListener('click',function(){
          window.requestAnimationFrame(function(){
            b.setAttribute('aria-expanded',p.classList.contains('open')?'true':'false');
          });
        });
        nav.addEventListener('keydown',function(e){
          if(e.key==='Escape' && p.classList.contains('open')){
            p.classList.remove('open');
            b.setAttribute('aria-expanded','false');
            b.focus();
          }
        });
      })(btn,panel);
    }
  }

  function repairBackTop(){
    var a=document.querySelector('#videha-back-top a');
    if(a && !a.getAttribute('aria-label')) a.setAttribute('aria-label','पृष्ठक शीर्षपर जाउ · Back to top');
  }

  function init(){repairNames();repairNav();repairBackTop();}
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init);
  else init();
})();

/* Videha WCAG 2.2 keyboard repair for legacy onclick controls */
(function(){
  'use strict';
  function init(){
    var nodes=document.querySelectorAll('[onclick]');
    for(var i=0;i<nodes.length;i++){
      var el=nodes[i], tag=el.tagName;
      if(/^(A|BUTTON|INPUT|SELECT|TEXTAREA|SUMMARY)$/.test(tag)) continue;
      if(el.classList && el.classList.contains('adv-modal-bg')) continue;
      if(!el.hasAttribute('tabindex')) el.setAttribute('tabindex','0');
      if(tag!=='TH' && !el.getAttribute('role')) el.setAttribute('role','button');
      if(!el.getAttribute('aria-label')){
        var txt=(el.textContent||'').replace(/\s+/g,' ').trim();
        if(txt) el.setAttribute('aria-label',txt.substring(0,220));
      }
      (function(x){
        x.addEventListener('keydown',function(e){
          if(e.key==='Enter' || e.key===' '){
            e.preventDefault();
            x.click();
          }
        });
      })(el);

      var oc=el.getAttribute('onclick')||'';
      var m=oc.match(/toggleSection\(['\"]([^'\"]+)['\"]\)/);
      if(m){
        var panel=document.getElementById('cards-'+m[1]);
        if(panel){
          el.setAttribute('aria-controls',panel.id);
          el.setAttribute('aria-expanded',panel.style.display==='none'?'false':'true');
          (function(x,p){x.addEventListener('click',function(){
            window.requestAnimationFrame(function(){x.setAttribute('aria-expanded',p.style.display==='none'?'false':'true');});
          });})(el,panel);
        }
      }
    }
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init); else init();
})();
