(function () {
  "use strict";

  const $ = id => document.getElementById(id);
  const authorSearch = $("authorSearch"), searchPublication = $("searchPublication"), findAuthor = $("findAuthor");
  const searchStatus = $("searchStatus"), searchResults = $("searchResults"), form = $("certificateForm");
  const authorName = $("authorName"), articleTitle = $("articleTitle"), publicationName = $("publicationName");
  const issueNumber = $("issueNumber"), versionField = $("versionField"), issueVersion = $("issueVersion");
  const certificateDate = $("certificateDate"), matchSummary = $("matchSummary"), formStatus = $("formStatus");
  const sheet = $("certificateSheet"), emptyMessage = $("emptyMessage"), certificateContent = $("certificateContent");
  const printCertificate = $("printCertificate");

  const GH_ROOT = "https://videha-ejournal.github.io/videha/";
  const PF_CANDIDATES = [new URL("pagefind/pagefind.js", document.baseURI).href, GH_ROOT + "pagefind/pagefind.js"];
  const PUBLICATION_CANDIDATES = [new URL("data/videha-author-publications.json", document.baseURI).href, GH_ROOT + "data/videha-author-publications.json"];
  let pagefindPromise = null, publicationPromise = null, selected = null, lastMatches = [];

  const esc = value => String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
  const plain = value => String(value || "").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
  const deva = value => String(value).replace(/[0-9]/g, digit => "०१२३४५६७८९"[+digit]);
  const norm = value => String(value || "").normalize("NFKC").toLocaleLowerCase()
    .replace(/[\u200b-\u200d\ufeff]/g, "").replace(/[.'’‘“”"(),:;\-–—/\\|]+/g, " ").replace(/\s+/g, " ").trim();
  const searchableName = value => norm(value).replace(/^(?:डॉ|डा|आचार्य|पं|प्रो|dr|doctor|prof|professor)\s+/i, "");

  function setStatus(element, text, kind = "") {
    element.textContent = text;
    element.className = "vpc-status" + (kind ? " " + kind : "");
  }

  function outputFor(publication, issue, version) {
    if (publication === "VIDEHA") return `videha-${String(issue).padStart(3, "0")}.html`;
    return +issue === 5 ? `sadeha-005-version-${version || 1}.html` : `sadeha-${String(issue).padStart(3, "0")}.html`;
  }

  function canonicalRecord(publication, issue, version) {
    return GH_ROOT + "search-documents/" + outputFor(publication, issue, version);
  }

  function parseResult(data) {
    const url = String(data.url || "");
    const match = url.match(/search-documents\/(videha|sadeha)-(\d+)(?:-version-([12]))?\.html/i);
    if (!match) return null;
    const publication = match[1].toUpperCase(), issue = +match[2], version = match[3] || "";
    return {
      pub: publication, issue, version, output: match[0].split("/").pop(),
      url: canonicalRecord(publication, issue, version),
      title: plain(data.meta?.title) || `${publication} — ${issue}`,
      excerpt: plain(data.excerpt || data.plain_excerpt || ""), verifiedWork: false
    };
  }

  async function loadFirst(candidates, unavailableMessage) {
    let error;
    for (const url of candidates) {
      try {
        const response = await fetch(url, { cache: "no-cache" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      } catch (caught) { error = caught; }
    }
    throw error || new Error(unavailableMessage);
  }

  async function getPublications() {
    if (!publicationPromise) publicationPromise = loadFirst(PUBLICATION_CANDIDATES, "Author-publication index unavailable");
    return publicationPromise;
  }

  async function getPagefind() {
    if (!pagefindPromise) pagefindPromise = (async () => {
      let error;
      for (const url of PF_CANDIDATES) {
        try { const pagefind = await import(url); await pagefind.init(); return pagefind; }
        catch (caught) { error = caught; }
      }
      throw error || new Error("Pagefind unavailable");
    })();
    return pagefindPromise;
  }

  function matchScore(author, query) {
    const full = norm(author), name = searchableName(author), needle = searchableName(query);
    if (!needle) return 0;
    if (full === norm(query) || name === needle) return 100;
    if (name.startsWith(needle)) return 80;
    if (name.includes(needle)) return 65;
    const tokens = needle.split(" ").filter(Boolean);
    return tokens.length && tokens.every(token => name.includes(token)) ? 50 : 0;
  }

  async function publicationMatches(query, scope) {
    if (scope === "SADEHA") return [];
    const data = await getPublications(), matches = [];
    for (const record of data.records || []) {
      const score = matchScore(record.author, query);
      if (!score) continue;
      matches.push({
        pub: record.publication || "VIDEHA", issue: +record.issue, version: record.version || "",
        output: outputFor(record.publication || "VIDEHA", record.issue, record.version || ""),
        url: record.researchUrl || record.archiveUrl || canonicalRecord("VIDEHA", record.issue, ""),
        archiveUrl: record.archiveUrl, authorLabel: record.author, workTitle: record.title,
        title: record.title, excerpt: `${record.author} · अंक ${deva(record.issue)}${record.section ? " · " + record.section : ""}`,
        verifiedWork: true, indexed: true, score
      });
    }
    return matches.sort((a, b) => b.score - a.score || b.issue - a.issue || a.title.localeCompare(b.title)).slice(0, 240);
  }

  async function pagefindMatches(query, scope) {
    const pagefind = await getPagefind(), options = scope ? { filters: { publication: scope } } : {};
    const found = await pagefind.search(query, options);
    const rows = await Promise.all((found.results || []).slice(0, 100).map(result => result.data()));
    return rows.map(parseResult).filter(Boolean);
  }

  async function archiveMatches(query, scope) {
    let exact = [], videhaFallback = [], sadehaFallback = [];
    if (scope !== "SADEHA") {
      try { exact = await publicationMatches(query, scope); } catch (error) { console.warn(error); }
      try { videhaFallback = await pagefindMatches(query, "VIDEHA"); } catch (error) { console.warn(error); }
    }
    if (scope !== "VIDEHA") {
      try { sadehaFallback = await pagefindMatches(query, "SADEHA"); } catch (error) { console.warn(error); }
    }
    return exact.concat(videhaFallback, sadehaFallback);
  }

  function resultKey(item) {
    return item.verifiedWork
      ? [item.pub, item.issue, item.version, norm(item.authorLabel), norm(item.workTitle)].join("|")
      : [item.pub, item.issue, item.version, "issue"].join("|");
  }

  function renderMatches(matches) {
    searchResults.innerHTML = "";
    lastMatches = matches;
    for (const [index, item] of matches.entries()) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "vpc-result";
      button.dataset.index = index;
      button.innerHTML = `<strong>${esc(item.title)}</strong><span class="badge">${esc(item.pub)} ${esc(item.issue)}</span><small>${esc(item.excerpt || "Author-name match in searchable issue text")}</small>`;
      button.addEventListener("click", () => selectMatch(index, button));
      searchResults.appendChild(button);
    }
  }

  function selectMatch(index, button) {
    const item = lastMatches[index];
    if (!item) return;
    selected = item;
    authorName.value = item.authorLabel || authorName.value.trim() || authorSearch.value.trim();
    if (item.workTitle) articleTitle.value = item.workTitle;
    publicationName.value = item.pub;
    issueNumber.value = item.issue;
    issueVersion.value = item.version || "1";
    updateVersion();
    searchResults.querySelectorAll(".vpc-result").forEach(result => result.classList.remove("selected"));
    button.classList.add("selected");
    matchSummary.className = "vpc-match verified";
    matchSummary.textContent = item.verifiedWork
      ? `लेखक आ रचना अभिलेखसँ मिलल · Exact author–work archive match: ${item.title}`
      : `अंकक अभिलेख मिलान चयनित · Issue-level archive match selected: ${item.title}`;
    setStatus(formStatus, item.verifiedWork
      ? "लेखक, शीर्षक आ अंक स्वतः भरल गेल। Declaration स्वीकार करू। · Author, title and issue filled from the archive."
      : "रचनाक शीर्षक भरि declaration स्वीकार करू। · Enter the work title and accept the declaration.", "good");
  }

  function selectionStillMatches() {
    if (!selected) return false;
    const version = publicationName.value === "SADEHA" && +issueNumber.value === 5 ? issueVersion.value : "";
    if (selected.pub !== publicationName.value || selected.issue !== +issueNumber.value || (selected.version || "") !== version) return false;
    if (!selected.verifiedWork) return true;
    return norm(selected.authorLabel) === norm(authorName.value) && norm(selected.workTitle) === norm(articleTitle.value);
  }

  function clearMatchIfChanged() {
    if (!selected || selectionStillMatches()) return;
    selected = null;
    searchResults.querySelectorAll(".vpc-result").forEach(result => result.classList.remove("selected"));
    matchSummary.className = "vpc-match";
    matchSummary.textContent = "विवरण बदलल गेल; प्रमाणपत्र लेखकक स्व-घोषणा पर बनत। · Details changed; certificate will use the author’s declaration.";
  }

  function updateVersion() {
    const show = publicationName.value === "SADEHA" && String(issueNumber.value) === "5";
    versionField.hidden = !show;
    issueVersion.required = show;
    if (!show) issueVersion.value = "1";
    clearMatchIfChanged();
  }

  async function search() {
    const query = authorSearch.value.trim();
    if (query.length < 2) {
      setStatus(searchStatus, "कम-सँ-कम दू अक्षर लिखू · Enter at least two characters.", "error");
      authorSearch.focus(); return;
    }
    findAuthor.disabled = true; searchResults.innerHTML = "";
    setStatus(searchStatus, "लेखक–रचना अभिलेख खोजल जा रहल अछि… · Searching author–work records…");
    try {
      const found = await archiveMatches(query, searchPublication.value), seen = new Set(), matches = [];
      for (const item of found) { const key = resultKey(item); if (!seen.has(key)) { seen.add(key); matches.push(item); } }
      renderMatches(matches);
      authorName.value = authorName.value || query;
      if (matches.length) setStatus(searchStatus, `${matches.length} matching work/issue record${matches.length === 1 ? "" : "s"} भेटल। सही रचना चुनू · Select the correct work.`, "good");
      else setStatus(searchStatus, "सीधा मिलान नहि भेटल। वर्तनी जाँचू वा manual details भरू। · No direct match; check spelling or use manual entry.", "error");
    } catch (error) {
      console.error(error);
      setStatus(searchStatus, "Search index उपलब्ध नहि अछि। Manual self-certification उपलब्ध अछि। · Archive search unavailable; manual entry remains available.", "error");
    } finally { findAuthor.disabled = false; }
  }

  async function referenceId(parts) {
    const raw = parts.join("|").normalize("NFKC");
    try {
      const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(raw));
      return "VSC-" + [...new Uint8Array(digest)].slice(0, 6).map(value => value.toString(16).padStart(2, "0")).join("").toUpperCase();
    } catch (error) {
      let hash = 2166136261; for (const char of raw) hash = Math.imul(hash ^ char.charCodeAt(0), 16777619);
      return "VSC-" + (hash >>> 0).toString(16).toUpperCase().padStart(8, "0");
    }
  }

  function formatDate(value) {
    const date = new Date(value + "T12:00:00");
    return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "long", year: "numeric" }).format(date);
  }

  async function generate(event) {
    event.preventDefault(); formStatus.className = "vpc-status";
    if (!form.reportValidity()) return setStatus(formStatus, "सभ आवश्यक विवरण भरू आ declaration स्वीकार करू। · Complete all required fields and accept the declaration.", "error");
    const author = authorName.value.trim(), title = articleTitle.value.trim(), pub = publicationName.value, issue = +issueNumber.value;
    const version = pub === "SADEHA" && issue === 5 ? issueVersion.value : "", date = certificateDate.value;
    if (!author || !title || !issue) return setStatus(formStatus, "लेखक, शीर्षक आ अंक आवश्यक अछि। · Author, title and issue are required.", "error");
    const matched = selectionStillMatches(), exactWork = matched && selected.verifiedWork;
    const record = matched ? selected.url : canonicalRecord(pub, issue, version);
    const id = await referenceId([author, title, pub, issue, version, date]);
    const issueLabel = pub === "VIDEHA" ? `VIDEHA — Issue ${issue} / अंक ${deva(issue)}` : `SADEHA — ${issue}${version ? `, Version ${version}` : ""}`;
    $("certAuthor").textContent = author; $("certArticle").textContent = `“${title}”`; $("certIssue").textContent = issueLabel;
    $("certMatch").textContent = exactWork
      ? "लेखक आ रचनाक शीर्षक एहि अंकक structured archive record सँ मिलल · Author and work title matched an article-level archive record"
      : matched ? "लेखक-नाम एहि searchable अंकसँ मिलल · Author name matched this searchable issue"
        : "लेखक द्वारा भरल स्व-घोषित प्रकाशन विवरण · Publication details self-declared by the author";
    $("certDate").textContent = formatDate(date); $("certId").textContent = id; $("certSignature").textContent = author;
    $("certSource").href = record; $("certSource").textContent = exactWork && selected.url.includes("/research/") ? "Open Research Article" : "Open publication record";
    sheet.classList.remove("is-empty"); emptyMessage.hidden = true; certificateContent.hidden = false; printCertificate.disabled = false;
    setStatus(formStatus, "प्रमाणपत्र तैयार। Preview जाँचि Print · Save PDF दबाउ। · Certificate generated; review it before printing.", "good");
    sheet.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function resetAll() {
    form.reset(); authorSearch.value = ""; searchPublication.value = ""; searchResults.innerHTML = ""; selected = null; lastMatches = [];
    certificateDate.value = new Date().toISOString().slice(0, 10); versionField.hidden = true; issueVersion.required = false;
    matchSummary.className = "vpc-match"; matchSummary.textContent = "अभिलेख मिलान एखन चयनित नहि अछि · No archive match selected.";
    sheet.classList.add("is-empty"); emptyMessage.hidden = false; certificateContent.hidden = true; printCertificate.disabled = true;
    setStatus(searchStatus, "नाम लिखि Search दबाउ। Manual entry is also available below."); setStatus(formStatus, "");
  }

  certificateDate.value = new Date().toISOString().slice(0, 10);
  findAuthor.addEventListener("click", search);
  authorSearch.addEventListener("keydown", event => { if (event.key === "Enter") { event.preventDefault(); search(); } });
  publicationName.addEventListener("change", updateVersion); issueNumber.addEventListener("input", updateVersion);
  issueVersion.addEventListener("change", clearMatchIfChanged); authorName.addEventListener("input", clearMatchIfChanged);
  articleTitle.addEventListener("input", clearMatchIfChanged); form.addEventListener("submit", generate);
  $("resetCertificate").addEventListener("click", resetAll); printCertificate.addEventListener("click", () => window.print());
})();
