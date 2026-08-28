<?php
/* Videha Research gateway. Deploy this small directory to httpdocs/research/.
 * Heavy generated data remains in GitHub; videha.co.in supplies stable URLs.
 */
declare(strict_types=1);
const RAW_BASE = 'https://raw.githubusercontent.com/videha-ejournal/videha/main/research/';
const PAGES_BASE = 'https://videha-ejournal.github.io/videha/research/';
const CACHE_TTL = 900;

function safe_rel(string $rel): ?string {
    $rel = ltrim($rel, '/');
    if ($rel === '' || strlen($rel) > 240) return null;
    if (str_contains($rel, '..') || !preg_match('~^[A-Za-z0-9_\-./%\x{0900}-\x{097F}]+$~u', $rel)) return null;
    return $rel;
}
function remote_url(string $rel): string {
    return RAW_BASE . implode('/', array_map(static fn(string $part): string => rawurlencode(rawurldecode($part)), explode('/', $rel)));
}
function fetch_remote(string $rel): array {
    $url = remote_url($rel);
    $ctx = stream_context_create(['http'=>['timeout'=>12,'user_agent'=>'VidehaResearchGateway/1.0']]);
    $data = @file_get_contents($url, false, $ctx);
    $status = null;
    foreach (($http_response_header ?? []) as $header) {
        if (preg_match('~^HTTP/\S+\s+(\d{3})~i', $header, $m)) $status = (int)$m[1];
    }
    return ['data'=>$data === false ? null : $data, 'status'=>$status];
}
/* Only the generated index is cached on disk (currently under 200 KB).
 * Article HTML/PDF is never written to the low-space Videha server. */
function fetch_index(): ?string {
    $dir = __DIR__ . '/cache';
    $cache = $dir . '/research-index.cache';
    if (is_file($cache) && time() - filemtime($cache) < CACHE_TTL) return file_get_contents($cache) ?: null;
    $remote = fetch_remote('index.htm');
    if ($remote['data'] !== null) {
        if (!is_dir($dir)) @mkdir($dir, 0755, true);
        @file_put_contents($cache, $remote['data'], LOCK_EX);
        return $remote['data'];
    }
    return is_file($cache) ? (file_get_contents($cache) ?: null) : null;
}
function not_found(): never { http_response_code(404); header('Content-Type: text/html; charset=utf-8'); echo '<!doctype html><html><head><meta charset="utf-8"><title>Research resource not found</title></head><body><h1>Research resource not found</h1><p><a href="/research/">Return to the Videha Research Index</a></p></body></html>'; exit; }
function github_fallback(string $rel = ''): never {
    header('Cache-Control: no-store');
    $encoded = $rel === '' ? '' : implode('/', array_map(static fn(string $part): string => rawurlencode(rawurldecode($part)), explode('/', $rel)));
    header('Location: ' . PAGES_BASE . $encoded, true, 302);
    exit;
}

$path = $_GET['path'] ?? '';
if ($path === '') {
    $page = fetch_index();
    if ($page === null) github_fallback();
    header('Content-Type: text/html; charset=utf-8');
    header('Cache-Control: public, max-age=600, stale-if-error=86400');
    header('X-Videha-Source: github-index-cache');
    echo $page; exit;
}
$path = safe_rel($path); if ($path === null) not_found();
if ($path === 'sitemap.xml') {
    $remote=fetch_remote($path);
    if ($remote['data']===null) { if ($remote['status']===404) not_found(); github_fallback($path); }
    header('Content-Type: application/xml; charset=utf-8'); header('Cache-Control: public, max-age=600'); echo $remote['data']; exit;
}
if (preg_match('~\.pdf$~i',$path)) github_fallback($path);
if (!preg_match('~\.html?$~i',$path)) not_found();
$remote=fetch_remote($path);
if ($remote['data']===null) { if ($remote['status']===404) not_found(); github_fallback($path); }
header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: public, max-age=600, stale-if-error=86400');
header('X-Videha-Source: github-stream');
echo $remote['data'];
