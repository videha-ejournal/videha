<?php
/* Videha Research sitemap gateway.
 * Deploy beside index.php in httpdocs/research/.
 * This avoids relying on Apache .htaccess for the sitemap on Plesk/nginx setups.
 */
declare(strict_types=1);
const RAW_SITEMAP = 'https://raw.githubusercontent.com/videha-ejournal/videha/main/research/sitemap.xml';
const CACHE_TTL = 900;

$cacheDir = __DIR__ . '/cache';
if (!is_dir($cacheDir)) @mkdir($cacheDir, 0755, true);
$cache = $cacheDir . '/sitemap.xml.cache';

$data = null;
if (is_file($cache) && time() - filemtime($cache) < CACHE_TTL) {
    $data = file_get_contents($cache) ?: null;
}
if ($data === null) {
    $ctx = stream_context_create(['http' => ['timeout' => 12, 'user_agent' => 'VidehaResearchGateway/1.0']]);
    $remote = @file_get_contents(RAW_SITEMAP, false, $ctx);
    if ($remote !== false) {
        $data = $remote;
        @file_put_contents($cache, $remote, LOCK_EX);
    } elseif (is_file($cache)) {
        $data = file_get_contents($cache) ?: null;
    }
}

if ($data === null) {
    http_response_code(503);
    header('Content-Type: text/plain; charset=utf-8');
    echo 'Videha research sitemap temporarily unavailable.';
    exit;
}

header('Content-Type: application/xml; charset=utf-8');
header('X-Content-Type-Options: nosniff');
echo $data;
