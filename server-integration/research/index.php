<?php
/* Videha Research gateway. Deploy this small directory to httpdocs/research/.
 * Heavy generated data remains in GitHub; videha.co.in supplies stable URLs.
 */
declare(strict_types=1);
const RAW_BASE = 'https://raw.githubusercontent.com/videha-ejournal/videha/main/research/';
const CACHE_TTL = 900;

function safe_rel(string $rel): ?string {
    $rel = ltrim($rel, '/');
    if ($rel === '' || strlen($rel) > 240) return null;
    if (str_contains($rel, '..') || !preg_match('~^[A-Za-z0-9_\-./%\x{0900}-\x{097F}]+$~u', $rel)) return null;
    return $rel;
}
function fetch_cached(string $rel): ?string {
    $safe = safe_rel($rel); if ($safe === null) return null;
    $dir = __DIR__ . '/cache'; if (!is_dir($dir)) @mkdir($dir, 0755, true);
    $cache = $dir . '/' . hash('sha256', $safe) . '.cache';
    if (is_file($cache) && time() - filemtime($cache) < CACHE_TTL) return file_get_contents($cache) ?: null;
    $url = RAW_BASE . str_replace('%2F','/',rawurlencode($safe));
    $url = preg_replace('~%2F~i','/',$url);
    $ctx = stream_context_create(['http'=>['timeout'=>12,'user_agent'=>'VidehaResearchGateway/1.0']]);
    $data = @file_get_contents($url, false, $ctx);
    if ($data !== false) { @file_put_contents($cache, $data, LOCK_EX); return $data; }
    if (is_file($cache)) return file_get_contents($cache) ?: null;
    return null;
}
function not_found(): never { http_response_code(404); header('Content-Type: text/plain; charset=utf-8'); echo 'Videha research resource not found.'; exit; }

$path = $_GET['path'] ?? '';
if ($path === '') {
    $json = fetch_cached('data/articles.json');
    if ($json === null) not_found();
    $data = json_decode($json, true); $articles = $data['articles'] ?? [];
    header('Content-Type: text/html; charset=utf-8');
    ?><!doctype html><html lang="mai"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>विदेह शोध-सूची · Videha Research Index</title><link rel="canonical" href="https://www.videha.co.in/research/"><style>body{font-family:Georgia,'Noto Serif Devanagari',serif;max-width:960px;margin:auto;padding:2rem;line-height:1.65;color:#171717}header{border-bottom:3px solid #8b1a1a}article{padding:1rem 0;border-bottom:1px solid #ddd}a{color:#7d1414}</style></head><body><header><h1>विदेह शोध-सूची · Videha Research Index</h1><p>Videha — First Maithili Fortnightly eJournal · ISSN 2229-547X</p></header><main><?php
    if (!$articles) echo '<p>Retrospective research indexing is being built from the Videha archive.</p>';
    foreach ($articles as $a) { $u=htmlspecialchars($a['url']??'#',ENT_QUOTES,'UTF-8'); $t=htmlspecialchars($a['title']??'',ENT_QUOTES,'UTF-8'); $au=htmlspecialchars(implode(', ',$a['authors']??[]),ENT_QUOTES,'UTF-8'); $d=htmlspecialchars((string)($a['publication_date']??''),ENT_QUOTES,'UTF-8'); $i=htmlspecialchars((string)($a['issue']??''),ENT_QUOTES,'UTF-8'); echo "<article><h2><a href=\"$u\">$t</a></h2><p>$au · $d · अंक $i</p></article>"; }
    ?></main><footer><p><a href="https://www.videha.co.in/">विदेह मुख्य पृष्ठ</a></p></footer></body></html><?php exit;
}
$path = safe_rel($path); if ($path === null) not_found();
if ($path === 'sitemap.xml') { $data=fetch_cached('sitemap.xml'); if ($data===null) not_found(); header('Content-Type: application/xml; charset=utf-8'); echo $data; exit; }
if (preg_match('~\.pdf$~i',$path)) { $data=fetch_cached($path); if ($data===null) not_found(); header('Content-Type: application/pdf'); header('Content-Disposition: inline'); echo $data; exit; }
if (!preg_match('~\.html?$~i',$path)) not_found();
$data=fetch_cached($path); if ($data===null) not_found(); header('Content-Type: text/html; charset=utf-8'); echo $data;
