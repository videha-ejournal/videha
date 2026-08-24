#!/usr/bin/env node

import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const root = process.cwd();
const siteRoot = path.resolve(root, "_pagefind_build");
const audit = JSON.parse(await readFile(path.join(root, "document-search-audit.json"), "utf8"));
const fixture = JSON.parse(await readFile(path.join(root, "data", "document-search-smoke.json"), "utf8"));
const pagefindPath = path.join(root, "_pagefind_build", "pagefind", "pagefind.js");
const pagefind = await import(pathToFileURL(pagefindPath).href);

function require(condition, message) {
  if (!condition) throw new Error(message);
}

async function dataFor(results, limit = 20) {
  return Promise.all(results.slice(0, limit).map((result) => result.data()));
}

async function startStaticServer() {
  const server = createServer(async (request, response) => {
    try {
      const url = new URL(request.url || "/", "http://127.0.0.1/");
      const relative = decodeURIComponent(url.pathname).replace(/^\/+/, "");
      const filename = path.resolve(siteRoot, relative);
      require(filename.startsWith(`${siteRoot}${path.sep}`), "Refusing a path outside the Pagefind staging site");
      response.statusCode = 200;
      response.end(await readFile(filename));
    } catch (error) {
      response.statusCode = error?.code === "ENOENT" ? 404 : 500;
      response.end("Not found");
    }
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const address = server.address();
  return { server, baseUrl: new URL(`http://127.0.0.1:${address.port}/`) };
}

const externalBase = process.argv[2] ? new URL(process.argv[2]) : null;
const local = externalBase ? null : await startStaticServer();
const baseUrl = externalBase || local.baseUrl;

try {
  pagefind.options({ basePath: new URL("pagefind/", baseUrl).href });
  await pagefind.init();

  const filters = await pagefind.filters();
  require(filters.publication?.VIDEHA === audit.stats.videha_pdfs, "Pagefind VIDEHA count differs from the audit");
  require(filters.publication?.SADEHA === audit.stats.sadeha_pdfs, "Pagefind SADEHA count differs from the audit");
  require(filters.version?.["1"] === 1 && filters.version?.["2"] === 1, "Sadeha 5 Version filters must each contain one page");

  const sadeha = await pagefind.search(null, { filters: { publication: "SADEHA", issue: "5", version: "2" } });
  const sadehaData = await dataFor(sadeha.results);
  require(sadeha.results.length === 1, "Sadeha 5 Version 2 filter did not return exactly one result");
  require(sadehaData[0]?.url.endsWith("/search-documents/sadeha-005-version-2.html"), "Sadeha 5 Version 2 returned the wrong page");
  require(sadehaData[0]?.meta?.title === "SADEHA — 5, Version 2", "Sadeha 5 Version 2 title is incorrect");

  const latest = String(audit.latest_videha_issue);
  const videha = await pagefind.search(null, { filters: { publication: "VIDEHA", issue: latest } });
  const videhaData = await dataFor(videha.results);
  require(videha.results.length === 1, `Latest VIDEHA issue ${latest} did not return exactly one generated result`);
  require(videhaData[0]?.url.endsWith(`/search-documents/videha-${latest.padStart(3, "0")}.html`), "Latest VIDEHA issue returned the wrong page");

  const ocr = await pagefind.search(fixture.ocr.query);
  const ocrData = await dataFor(ocr.results, 50);
  require(ocrData.some((result) => result.url.endsWith(`/search-documents/${fixture.ocr.expected_output}`)), "OCR-derived phrase did not return its expected page");

  const existing = await pagefind.search(fixture.existing_html.query);
  const existingData = await dataFor(existing.results, 50);
  require(existingData.some((result) => result.url.endsWith(`/${fixture.existing_html.expected_output}`)), "Existing canonical HTML search result was not preserved");

  const certificate = await pagefind.search("Self-Certified Publication Certificate");
  const certificateData = await dataFor(certificate.results, 50);
  require(certificateData.some((result) => result.url.endsWith("/publication-certificate.html")), "Publication-certificate widget is missing from Pagefind");

  console.log(
    `Pagefind smoke tests passed: ${filters.publication.VIDEHA} VIDEHA, ` +
    `${filters.publication.SADEHA} SADEHA, naming/filters correct, OCR, existing HTML, and certificate widget searchable.`
  );
} finally {
  if (local) await new Promise((resolve, reject) => local.server.close((error) => error ? reject(error) : resolve()));
}
