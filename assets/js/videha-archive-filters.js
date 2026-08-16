/* VIDEHA_ARCHIVE_FILTERS_20260810
   Non-destructive client-side filters for the existing Videha archive collections.
   No archive entry is deleted, moved, or rewritten. */
(function () {
  'use strict';

  function normaliseDigits(value) {
    var dev = '०१२३४५६७८९';
    return String(value || '').replace(/[०-९]/g, function (d) { return String(dev.indexOf(d)); });
  }

  function textOf(el) {
    return normaliseDigits((el.textContent || '') + ' ' + Array.prototype.map.call(el.querySelectorAll('a[href]'), function (a) {
      return a.getAttribute('href') || '';
    }).join(' ')).toLowerCase();
  }

  function hasScript(haystack, script) {
    if (!script) return true;
    var tests = {
      devanagari: ['देवनागरी', 'devanagari'],
      tirhuta: ['मिथिलाक्षर', 'तिरहुता', 'tirhuta', 'mithilakshar'],
      braille: ['ब्रेल', 'braille'],
      ipa: [' ipa ', '/ipa', 'ipa/'],
      kaithi: ['कैथी', 'kaithi']
    };
    return (tests[script] || []).some(function (term) { return haystack.indexOf(term) !== -1; });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var box = document.getElementById('videha-archive-filters');
    if (!box) return;

    var yearSelect = document.getElementById('videha-filter-year');
    var issueInput = document.getElementById('videha-filter-issue');
    var scriptSelect = document.getElementById('videha-filter-script');
    var pdfBox = document.getElementById('videha-filter-pdf');
    var audioBox = document.getElementById('videha-filter-audio');
    var specialBox = document.getElementById('videha-filter-special');
    var resetButton = document.getElementById('videha-filter-reset');
    var status = document.getElementById('videha-filter-status');

    var sections = Array.prototype.filter.call(document.querySelectorAll('details.vacc'), function (details) {
      return !!details.querySelector('.vrow');
    });

    var years = [];
    sections.forEach(function (details) {
      var summary = details.querySelector('summary.vacc-head');
      var summaryText = normaliseDigits(summary ? summary.textContent : '');
      var match = summaryText.match(/(?:वर्ष|Year)\s*(20\d{2})/i);
      var year = match ? match[1] : '';
      details.dataset.videhaFilterYear = year;
      details.dataset.videhaFilterSpecialSection = /(?:विशेषांक|special\s*issues?)/i.test(summaryText) ? '1' : '0';
      details.dataset.videhaOriginalOpen = details.open ? '1' : '0';
      if (year && years.indexOf(year) === -1) years.push(year);
    });

    years.sort(function (a, b) { return Number(b) - Number(a); });
    years.forEach(function (year) {
      var opt = document.createElement('option');
      opt.value = year;
      opt.textContent = year;
      yearSelect.appendChild(opt);
    });

    function issueMatches(row, issue) {
      if (!issue) return true;
      var n = normaliseDigits(issue).replace(/\D+/g, '');
      if (!n) return true;
      var label = row.querySelector('.vrow-num');
      var t = normaliseDigits(label ? label.textContent : row.textContent);
      var re = new RegExp('(?:अंक|issue)\\s*' + n + '(?!\\d)', 'i');
      return re.test(t);
    }

    function applyFilters() {
      var year = yearSelect.value;
      var issue = normaliseDigits(issueInput.value).trim();
      var script = scriptSelect.value;
      var pdfOnly = pdfBox.checked;
      var audioOnly = audioBox.checked;
      var specialOnly = specialBox.checked;
      var active = !!(year || issue || script || pdfOnly || audioOnly || specialOnly);
      var visibleRows = 0;

      sections.forEach(function (details) {
        var sectionYear = details.dataset.videhaFilterYear || '';
        var yearMatch = !year || sectionYear === year;
        var specialSection = details.dataset.videhaFilterSpecialSection === '1';
        var rows = Array.prototype.slice.call(details.querySelectorAll('.vrow'));
        var detailMatches = 0;

        rows.forEach(function (row) {
          var hay = ' ' + textOf(row) + ' ';
          var hrefs = Array.prototype.map.call(row.querySelectorAll('a[href]'), function (a) {
            return (a.getAttribute('href') || '').toLowerCase();
          });
          var matches = yearMatch &&
            issueMatches(row, issue) &&
            hasScript(hay, script) &&
            (!pdfOnly || hrefs.some(function (h) { return /(?:\.pdf(?:[?#]|$)|\/pdf(?:[/?#]|$))/.test(h); }) || /\bpdf\b/i.test(hay)) &&
            (!audioOnly || hrefs.some(function (h) { return /\.(?:mp3|m4a|wav|ogg|flac)(?:[?#]|$)/.test(h); }) || /(?:ऑडियो|audio)/i.test(hay)) &&
            (!specialOnly || specialSection || /(?:विशेषांक|special\s*issue)/i.test(hay));

          row.style.display = matches ? '' : 'none';
          if (matches) {
            detailMatches += 1;
            visibleRows += 1;
          }
        });

        details.style.display = (!active || detailMatches > 0) ? '' : 'none';
        if (active && detailMatches > 0) details.open = true;
      });

      status.textContent = active ? (visibleRows + ' matching archive entr' + (visibleRows === 1 ? 'y' : 'ies')) : '';
    }

    function resetFilters() {
      yearSelect.value = '';
      issueInput.value = '';
      scriptSelect.value = '';
      pdfBox.checked = false;
      audioBox.checked = false;
      specialBox.checked = false;
      sections.forEach(function (details) {
        details.style.display = '';
        details.open = details.dataset.videhaOriginalOpen === '1';
        Array.prototype.forEach.call(details.querySelectorAll('.vrow'), function (row) { row.style.display = ''; });
      });
      status.textContent = '';
    }

    [yearSelect, issueInput, scriptSelect, pdfBox, audioBox, specialBox].forEach(function (el) {
      el.addEventListener(el === issueInput ? 'input' : 'change', applyFilters);
    });
    resetButton.addEventListener('click', resetFilters);
  });
}());
