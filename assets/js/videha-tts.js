/* ============================================================================
   Videha · Maithili (Devanagari) Text-to-Speech
   Built-in, free Web Speech API (SpeechSynthesis). No external service.
   WCAG-minded: keyboard operable, ARIA-labelled, live status announcements,
   reads the main article aloud, with Play/Pause + Stop.
   Voice preference: Maithili (mai) -> Hindi (hi-IN/hi) -> India English -> default.
   ============================================================================ */
(function () {
  "use strict";

  var synth = window.speechSynthesis;
  var toggleBtn = document.getElementById("videha-tts-toggle");
  var stopBtn   = document.getElementById("videha-tts-stop");
  var status    = document.getElementById("videha-tts-status");
  if (!toggleBtn) return;

  // Graceful degradation: no speech support -> announce and disable.
  if (!synth || typeof SpeechSynthesisUtterance === "undefined") {
    toggleBtn.disabled = true;
    toggleBtn.setAttribute("aria-disabled", "true");
    toggleBtn.title = " श्रव्य सुविधा एहि ब्राउज़रमे उपलब्ध नहि अछि · Speech not supported in this browser";
    return;
  }

  var labelEl = toggleBtn.querySelector(".videha-tts-label");
  var chunks = [];
  var idx = 0;
  var state = "idle"; // idle | playing | paused
  var chosenVoice = null;

  // ---- pick the best available voice for Maithili / Devanagari ----
  function pickVoice() {
    var voices = synth.getVoices() || [];
    if (!voices.length) return null;
    var byLang = function (re) {
      for (var i = 0; i < voices.length; i++) {
        if (re.test(voices[i].lang || "") || re.test(voices[i].name || "")) return voices[i];
      }
      return null;
    };
    return byLang(/^mai/i)               // Maithili
        || byLang(/maithili/i)
        || byLang(/^hi[-_]?in/i)         // Hindi (India) — renders Devanagari well
        || byLang(/^hi\b/i)
        || byLang(/hindi/i)
        || byLang(/^(ne|bn|sa)/i)        // Nepali/Bengali/Sanskrit Devanagari fallbacks
        || byLang(/^en[-_]?in/i)         // India English
        || voices[0];
  }
  function ensureVoice() {
    if (!chosenVoice) chosenVoice = pickVoice();
    return chosenVoice;
  }
  if (synth.onvoiceschanged !== undefined) {
    synth.onvoiceschanged = function () { chosenVoice = pickVoice(); };
  }
  ensureVoice();

  // ---- collect the readable main content (skip chrome) ----
  var SKIP = [
    "videha-topbar", "videha-utilbar", "videha-nav", "videha-a11y-bar",
    "videha-skip", "grayBox", "videha-refresh-note", "videha-tirhuta-img"
  ];
  function skipped(node) {
    var el = node;
    while (el && el !== document.body) {
      if (el.nodeType === 1) {
        var tag = el.tagName;
        if (tag === "SCRIPT" || tag === "STYLE" || tag === "NOSCRIPT") return true;
        if (el.getAttribute && el.getAttribute("aria-hidden") === "true") return true;
        var cls = " " + (el.className && el.className.baseVal !== undefined
                          ? el.className.baseVal : (el.className || "")) + " ";
        for (var i = 0; i < SKIP.length; i++) {
          if (cls.indexOf(" " + SKIP[i] + " ") > -1) return true;
        }
      }
      el = el.parentNode;
    }
    return false;
  }

  function collectText() {
    var root = document.querySelector("[data-videha-read]") ||
               document.querySelector("main") || document.body;
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        if (!n.nodeValue || !n.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        if (skipped(n.parentNode)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var parts = [], t;
    while ((t = walker.nextNode())) parts.push(t.nodeValue.trim());
    return parts.join(" ").replace(/\s+/g, " ").trim();
  }

  // chunk by sentence (Devanagari danda etc.) so long pages read fully
  function toChunks(text) {
    var raw = text.split(/(?<=[\u0964\u0965।!?.;:])\s+/);
    var out = [], buf = "";
    for (var i = 0; i < raw.length; i++) {
      if ((buf + " " + raw[i]).length > 220 && buf) { out.push(buf); buf = raw[i]; }
      else { buf = buf ? buf + " " + raw[i] : raw[i]; }
    }
    if (buf) out.push(buf);
    return out.filter(Boolean);
  }

  function announce(msg) { if (status) status.textContent = msg; }

  function setUI(s) {
    state = s;
    if (s === "playing") {
      toggleBtn.setAttribute("aria-pressed", "true");
      if (labelEl) labelEl.textContent = "रोकू · Pause";
      toggleBtn.setAttribute("aria-label", "वाचन रोकू · Pause reading");
      if (stopBtn) stopBtn.hidden = false;
    } else if (s === "paused") {
      toggleBtn.setAttribute("aria-pressed", "false");
      if (labelEl) labelEl.textContent = "आगू · Resume";
      toggleBtn.setAttribute("aria-label", "वाचन आगू बढ़ाउ · Resume reading");
    } else { // idle
      toggleBtn.setAttribute("aria-pressed", "false");
      if (labelEl) labelEl.textContent = "सुनू · Listen";
      toggleBtn.setAttribute("aria-label", "ई पृष्ठ सुनू · Listen to this page");
      if (stopBtn) stopBtn.hidden = true;
    }
  }

  function speakFrom(i) {
    if (i >= chunks.length) { stopAll(); announce("वाचन समाप्त · Finished reading"); return; }
    idx = i;
    var u = new SpeechSynthesisUtterance(chunks[i]);
    var v = ensureVoice();
    if (v) u.voice = v;
    u.lang = (v && v.lang) ? v.lang : "hi-IN";
    u.rate = 0.95; u.pitch = 1; u.volume = 1;
    u.onend = function () { if (state === "playing") speakFrom(idx + 1); };
    u.onerror = function () { if (state === "playing") speakFrom(idx + 1); };
    synth.speak(u);
  }

  function startReading() {
    synth.cancel();
    chunks = toChunks(collectText());
    if (!chunks.length) { announce("पढ़बाक लेल किछु नहि भेटल · Nothing to read"); return; }
    setUI("playing");
    announce("वाचन प्रारंभ · Reading the page aloud");
    speakFrom(0);
  }
  function stopAll() {
    synth.cancel();
    idx = 0; chunks = [];
    setUI("idle");
  }

  toggleBtn.addEventListener("click", function () {
    if (state === "idle") { startReading(); }
    else if (state === "playing") { synth.pause(); setUI("paused"); announce("वाचन रुकल · Paused"); }
    else if (state === "paused") { synth.resume(); setUI("playing"); announce("वाचन आगू · Resumed"); }
  });

  if (stopBtn) {
    stopBtn.addEventListener("click", function () {
      stopAll(); announce("वाचन रुकल · Stopped"); toggleBtn.focus();
    });
  }

  // Stop speech if the user leaves the page (some browsers keep it running)
  window.addEventListener("beforeunload", function () { try { synth.cancel(); } catch (e) {} });
  setUI("idle");
})();

/* Videha universal-search result URL normalizer — 2026-08-18.
   Canonical/current/static results stay on the reader's current host;
   GitHub-only search-documents always open on GitHub Pages. */
(function () {
  'use strict';
  var GH_HOST = 'videha-ejournal.github.io';
  var GH_BASE = '/videha/';
  var VIDEHA_HOSTS = { 'videha.co.in': true, 'www.videha.co.in': true };

  function resultUrl(raw) {
    if (!raw || typeof raw !== 'string') return raw;
    if (/^(?:#|mailto:|tel:|javascript:|data:)/i.test(raw)) return raw;
    try {
      var u = new URL(raw, window.location.href);
      var known = (u.hostname === window.location.hostname ||
                   u.hostname === GH_HOST || VIDEHA_HOSTS[u.hostname]);
      if (!known) return raw;
      var path = u.pathname || '/';
      if (path.indexOf(GH_BASE) === 0) path = path.slice(GH_BASE.length);
      else path = path.replace(/^\/+/, '');
      if (!path) path = 'index.htm';
      var suffix = (u.search || '') + (u.hash || '');
      if (path.indexOf('search-documents/') === 0) {
        return 'https://' + GH_HOST + GH_BASE + path + suffix;
      }
      if (window.location.hostname === GH_HOST) return GH_BASE + path + suffix;
      if (VIDEHA_HOSTS[window.location.hostname]) return '/' + path + suffix;
      return raw;
    } catch (e) { return raw; }
  }

  function rewrite(root) {
    if (!root || root.nodeType !== 1) return;
    var links = [];
    if (root.matches && root.matches('.vus-result a, .vus-hit a')) links.push(root);
    if (root.querySelectorAll) {
      var found = root.querySelectorAll('.vus-result a, .vus-hit a');
      for (var i = 0; i < found.length; i++) links.push(found[i]);
    }
    for (var j = 0; j < links.length; j++) {
      var a = links[j], oldHref = a.getAttribute('href') || '';
      var newHref = resultUrl(oldHref);
      if (newHref && newHref !== oldHref) a.setAttribute('href', newHref);
      var li = a.closest ? a.closest('.vus-result') : null;
      var shown = li && li.querySelector ? li.querySelector('.vus-url') : null;
      if (shown && newHref) shown.textContent = newHref;
    }
  }

  function start() {
    rewrite(document.documentElement);
    if (!window.MutationObserver) return;
    new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i++) {
        var nodes = mutations[i].addedNodes || [];
        for (var j = 0; j < nodes.length; j++) rewrite(nodes[j]);
      }
    }).observe(document.documentElement, { childList: true, subtree: true });
  }

  window.videhaSearchResultUrl = resultUrl;
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
}());

