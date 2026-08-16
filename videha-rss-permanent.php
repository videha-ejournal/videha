<?php
/**
 * Videha RSS Generator
 * --------------------
 * Place this file in the same public folder as:
 *   index.htm
 *   videha-rss.xml
 *
 * Modes:
 * 1) Cron / command line: php /full/path/videha-rss-permanent.php
 * 2) Browser fallback: https://www.videha.co.in/videha-rss-permanent.php?key=YOUR_KEY
 *
 * The script reads the current issue block from index.htm, builds/updates
 * videha-rss.xml and keeps recent previous issue items. This version writes directly
 * to the existing RSS file, so it does not need permission to create lock/temp files.
 */

declare(strict_types=1);

// ------------------------- CONFIGURATION -------------------------
const VIDEHA_SOURCE_FILE = 'index.htm';
const VIDEHA_RSS_FILE    = 'videha-rss.xml';
const VIDEHA_BASE_URL    = 'https://www.videha.co.in/';
const VIDEHA_RSS_URL     = 'https://www.videha.co.in/videha-rss.xml';
const VIDEHA_MAX_ITEMS   = 24; // about one year of twice-monthly issues

// Keep this key private. It is required only when running the script in a browser.
const VIDEHA_BROWSER_KEY = 'VhRSS-54e0432e2fade4fad2a8c56bf4322053bfbf98bc';

const VIDEHA_EDITOR_EMAIL = 'editorial.staff.videha@zohomail.in';
const VIDEHA_EDITOR_NAME  = 'Gajendra Thakur';
// ----------------------------------------------------------------

function out(string $message, int $status = 200)
{
    if (PHP_SAPI !== 'cli') {
        http_response_code($status);
        header('Content-Type: text/plain; charset=UTF-8');
        header('X-Robots-Tag: noindex, nofollow, noarchive');
        header('Cache-Control: no-store, max-age=0');
    }
    echo $message . ((substr($message, -1) === "\n") ? '' : "\n");
    exit;
}

function fail(string $message, int $status = 500)
{
    out("Videha RSS update FAILED: " . $message, $status);
}

function normalize_space(string $text): string
{
    $text = html_entity_decode($text, ENT_QUOTES | ENT_HTML5, 'UTF-8');
    $text = preg_replace('/[\x{00A0}\s]+/u', ' ', $text) ?? $text;
    return trim($text);
}

function devanagari_to_ascii(string $text): string
{
    return strtr($text, [
        '०'=>'0','१'=>'1','२'=>'2','३'=>'3','४'=>'4',
        '५'=>'5','६'=>'6','७'=>'7','८'=>'8','९'=>'9'
    ]);
}

function xml_escape(string $text): string
{
    return htmlspecialchars($text, ENT_XML1 | ENT_QUOTES, 'UTF-8');
}

function cdata_safe(string $text): string
{
    return str_replace(']]>', ']]]]><![CDATA[>', $text);
}

function absolute_url(string $href): ?string
{
    $href = trim(html_entity_decode($href, ENT_QUOTES | ENT_HTML5, 'UTF-8'));
    if ($href === '' || substr($href, 0, 1) === '#' || preg_match('/^(javascript|mailto|tel):/i', $href)) {
        return null;
    }
    if (preg_match('~^https?://~i', $href)) {
        return $href;
    }
    if (substr($href, 0, 2) === '//') {
        return 'https:' . $href;
    }
    if (substr($href, 0, 1) === '/') {
        return rtrim(VIDEHA_BASE_URL, '/') . $href;
    }
    return VIDEHA_BASE_URL . ltrim($href, './');
}

function parse_issue_date(string $issueTitle): array
{
    // Expected examples: [०१ अगस्त २०२६], [15 August 2026]
    $ascii = devanagari_to_ascii($issueTitle);
    if (!preg_match('/\[?\s*(\d{1,2})\s+([^\d\]\[]+)\s+(\d{4})\s*\]?/u', $ascii, $m)) {
        return [time(), date('Y-m-d')];
    }

    $day = (int)$m[1];
    $monthWord = strtolower(trim($m[2]));
    $year = (int)$m[3];

    $months = [
        'जनवरी'=>1, 'january'=>1,
        'फरवरी'=>2, 'february'=>2,
        'मार्च'=>3, 'march'=>3,
        'अप्रैल'=>4, 'अप्रेल'=>4, 'april'=>4,
        'मई'=>5, 'may'=>5,
        'जून'=>6, 'june'=>6,
        'जुलाई'=>7, 'july'=>7,
        'अगस्त'=>8, 'august'=>8,
        'सितम्बर'=>9, 'सितंबर'=>9, 'september'=>9,
        'अक्टूबर'=>10, 'october'=>10,
        'नवम्बर'=>11, 'नवंबर'=>11, 'november'=>11,
        'दिसम्बर'=>12, 'दिसंबर'=>12, 'december'=>12,
    ];

    $month = $months[$monthWord] ?? null;
    if (!$month || !checkdate($month, $day, $year)) {
        return [time(), date('Y-m-d')];
    }

    $dt = new DateTimeImmutable(sprintf('%04d-%02d-%02d 00:00:00', $year, $month, $day), new DateTimeZone('Asia/Kolkata'));
    return [$dt->getTimestamp(), $dt->format('Y-m-d')];
}

function find_current_issue_with_dom(string $html): ?array
{
    if (!class_exists('DOMDocument')) {
        return null;
    }

    libxml_use_internal_errors(true);
    $dom = new DOMDocument();
    $loaded = $dom->loadHTML('<?xml encoding="UTF-8">' . $html, LIBXML_NOWARNING | LIBXML_NOERROR);
    libxml_clear_errors();
    if (!$loaded) {
        return null;
    }

    $xp = new DOMXPath($dom);
    $blocks = $xp->query('//*[contains(concat(" ", normalize-space(@class), " "), " videha-current-issue ")]');
    if (!$blocks || $blocks->length === 0) {
        return null;
    }

    $block = $blocks->item(0);
    if (!$block) {
        return null;
    }

    $titleNodes = $xp->query('.//h2[1]', $block);
    $numberNodes = $xp->query('.//*[contains(concat(" ", normalize-space(@class), " "), " issue-number-square ")][1]', $block);
    $titleNode = ($titleNodes && $titleNodes->length) ? $titleNodes->item(0) : null;
    $numberNode = ($numberNodes && $numberNodes->length) ? $numberNodes->item(0) : null;

    $title = $titleNode ? normalize_space($titleNode->textContent) : '';
    $number = $numberNode ? normalize_space($numberNode->textContent) : '';
    if ($title === '' && $number !== '') {
        $title = 'विदेह अंक ' . $number;
    }
    if ($title === '') {
        return null;
    }

    $links = [];
    $seen = [];
    $nodes = $xp->query('.//a[@href]', $block);
    if ($nodes) {
        foreach ($nodes as $a) {
            /** @var DOMElement $a */
            $href = absolute_url($a->getAttribute('href'));
            $text = normalize_space($a->textContent);
            if (!$href || $text === '') {
                continue;
            }
            $key = $href . "\n" . $text;
            if (isset($seen[$key])) {
                continue;
            }
            $seen[$key] = true;
            $links[] = ['href' => $href, 'title' => $text];
        }
    }

    return ['title' => $title, 'number' => $number, 'links' => $links];
}

function find_current_issue_fallback(string $html): ?array
{
    // Conservative fallback for hosts where PHP DOM is unavailable.
    if (!preg_match('/<div\b[^>]*class=["\'][^"\']*videha-current-issue[^"\']*["\'][^>]*>(.*?)(?=<!--\s*Archive-style|<style\b[^>]*id=["\']videha-numbered-archive-style)/is', $html, $bm)) {
        return null;
    }
    $block = $bm[1];

    $title = '';
    if (preg_match('/<h2\b[^>]*>(.*?)<\/h2>/is', $block, $tm)) {
        $title = normalize_space(strip_tags($tm[1]));
    }
    $number = '';
    if (preg_match('/class=["\'][^"\']*issue-number-square[^"\']*["\'][^>]*>(.*?)<\/div>/is', $block, $nm)) {
        $number = normalize_space(strip_tags($nm[1]));
    }
    if ($title === '' && $number !== '') {
        $title = 'विदेह अंक ' . $number;
    }
    if ($title === '') {
        return null;
    }

    $links = [];
    $seen = [];
    if (preg_match_all('/<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)<\/a>/is', $block, $am, PREG_SET_ORDER)) {
        foreach ($am as $a) {
            $href = absolute_url($a[1]);
            $text = normalize_space(strip_tags($a[2]));
            if (!$href || $text === '') {
                continue;
            }
            $key = $href . "\n" . $text;
            if (isset($seen[$key])) {
                continue;
            }
            $seen[$key] = true;
            $links[] = ['href' => $href, 'title' => $text];
        }
    }

    return ['title' => $title, 'number' => $number, 'links' => $links];
}

function extract_existing_items(string $xml): array
{
    $items = [];
    if ($xml === '') {
        return $items;
    }
    if (preg_match_all('/<item>.*?<\/item>/si', $xml, $m)) {
        $items = $m[0];
    }
    return $items;
}

function extract_guid(string $itemXml): string
{
    if (preg_match('/<guid\b[^>]*>(.*?)<\/guid>/si', $itemXml, $m)) {
        return html_entity_decode(strip_tags($m[1]), ENT_QUOTES | ENT_XML1, 'UTF-8');
    }
    return '';
}

function build_item(array $issue): array
{
    $issueNumberAscii = preg_replace('/\D+/', '', devanagari_to_ascii((string)$issue['number'])) ?: '';
    [$timestamp, $isoDate] = parse_issue_date((string)$issue['title']);

    $issueUrl = VIDEHA_BASE_URL . 'index.htm';
    $anchor = 'issue-' . ($issueNumberAscii !== '' ? $issueNumberAscii : $isoDate) . '-' . $isoDate;
    $guid = $issueUrl . '#' . $anchor;

    $list = '';
    foreach ($issue['links'] as $link) {
        $list .= '<li><a href="' . htmlspecialchars($link['href'], ENT_QUOTES | ENT_HTML5, 'UTF-8') . '">' .
                 htmlspecialchars($link['title'], ENT_QUOTES | ENT_HTML5, 'UTF-8') . '</a></li>';
    }

    $description = '<p>Videha — First Maithili Fortnightly eJournal · ISSN 2229-547X.</p>';
    if ($list !== '') {
        $description .= '<p>Current issue contents:</p><ul>' . $list . '</ul>';
    }

    $xml = "<item>\n";
    $xml .= '<title>' . xml_escape((string)$issue['title']) . "</title>\n";
    $xml .= '<link>' . xml_escape($issueUrl) . "</link>\n";
    $xml .= '<guid isPermaLink="true">' . xml_escape($guid) . "</guid>\n";
    $pub = (new DateTimeImmutable('@' . $timestamp))->setTimezone(new DateTimeZone('Asia/Kolkata'));
    $xml .= '<pubDate>' . $pub->format('D, d M Y H:i:s O') . "</pubDate>\n";
    $xml .= '<description><![CDATA[' . cdata_safe($description) . "]]></description>\n";
    $xml .= "</item>";

    return ['guid' => $guid, 'xml' => $xml, 'date' => $isoDate];
}

function build_feed(array $currentItem, array $existingItems): string
{
    $items = [$currentItem['xml']];
    $seen = [$currentItem['guid'] => true];

    foreach ($existingItems as $itemXml) {
        $guid = extract_guid($itemXml);
        if ($guid !== '' && isset($seen[$guid])) {
            continue; // current issue replaces an older copy of the same issue
        }
        if ($guid !== '') {
            $seen[$guid] = true;
        }
        $items[] = trim($itemXml);
        if (count($items) >= VIDEHA_MAX_ITEMS) {
            break;
        }
    }

    $now = new DateTimeImmutable('now', new DateTimeZone('Asia/Kolkata'));
    $editor = VIDEHA_EDITOR_EMAIL . ' (' . VIDEHA_EDITOR_NAME . ')';

    $feed  = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
    $feed .= "<rss version=\"2.0\" xmlns:atom=\"http://www.w3.org/2005/Atom\">\n<channel>\n";
    $feed .= '<title>Videha — New Issue · विदेह नूतन अंक</title>' . "\n";
    $feed .= '<link>' . xml_escape(VIDEHA_BASE_URL) . "</link>\n";
    $feed .= '<atom:link href="' . xml_escape(VIDEHA_RSS_URL) . '" rel="self" type="application/rss+xml"/>' . "\n";
    $feed .= '<description>New Videha Issue — twice monthly · विदेह प्रथम मैथिली पाक्षिक ई-पत्रिका · ISSN 2229-547X</description>' . "\n";
    $feed .= '<language>mai</language>' . "\n";
    $feed .= '<managingEditor>' . xml_escape($editor) . "</managingEditor>\n";
    $feed .= '<webMaster>' . xml_escape(VIDEHA_EDITOR_EMAIL . ' (Videha)') . "</webMaster>\n";
    $feed .= '<lastBuildDate>' . $now->format('D, d M Y H:i:s O') . "</lastBuildDate>\n";
    $feed .= '<ttl>720</ttl>' . "\n";
    $feed .= implode("\n", $items) . "\n";
    $feed .= "</channel>\n</rss>\n";

    return $feed;
}

// Browser mode is protected. CLI/Cron mode runs without the browser key.
if (PHP_SAPI !== 'cli') {
    $key = isset($_GET['key']) ? (string)$_GET['key'] : '';
    if (!hash_equals(VIDEHA_BROWSER_KEY, $key)) {
        fail('unauthorized browser request.', 403);
    }
}

$baseDir = __DIR__;
$sourcePath = $baseDir . DIRECTORY_SEPARATOR . VIDEHA_SOURCE_FILE;
$rssPath = $baseDir . DIRECTORY_SEPARATOR . VIDEHA_RSS_FILE;

if (!is_file($sourcePath) || !is_readable($sourcePath)) {
    fail('cannot read ' . VIDEHA_SOURCE_FILE . '. Put the generator in the same folder as index.htm.');
}

$html = file_get_contents($sourcePath);
if ($html === false || trim($html) === '') {
    fail(VIDEHA_SOURCE_FILE . ' is empty or unreadable.');
}

$issue = find_current_issue_with_dom($html) ?? find_current_issue_fallback($html);
if (!$issue) {
    fail('the current issue block could not be found in ' . VIDEHA_SOURCE_FILE . '.');
}
if (empty($issue['links'])) {
    fail('current issue found, but no issue contents links were found. RSS was NOT changed.');
}

$current = build_item($issue);
$oldXml = is_file($rssPath) ? (string)file_get_contents($rssPath) : '';
$existingItems = extract_existing_items($oldXml);
$newXml = build_feed($current, $existingItems);

// Validate generated XML if DOM is available.
if (class_exists('DOMDocument')) {
    libxml_use_internal_errors(true);
    $test = new DOMDocument();
    $ok = $test->loadXML($newXml, LIBXML_NOWARNING | LIBXML_NOERROR);
    libxml_clear_errors();
    if (!$ok) {
        fail('generated XML did not pass XML validation. RSS was NOT changed.');
    }
}

// Rediff/shared-hosting compatible write path:
// do not create lock or temporary files; lock the existing RSS file itself.
if (!is_file($rssPath)) {
    fail(VIDEHA_RSS_FILE . ' does not exist. Upload the existing XML file first; this server mode does not create new files.');
}

$handle = @fopen($rssPath, 'c+');
if (!$handle) {
    fail('cannot open ' . VIDEHA_RSS_FILE . ' for writing. Check that the existing XML file is writable by PHP.');
}
if (!@flock($handle, LOCK_EX)) {
    fclose($handle);
    fail('cannot lock the existing ' . VIDEHA_RSS_FILE . ' for update.');
}

// Only truncate after the complete replacement XML has been built and validated above.
if (!@ftruncate($handle, 0) || !@rewind($handle)) {
    @flock($handle, LOCK_UN);
    fclose($handle);
    fail('cannot prepare the existing ' . VIDEHA_RSS_FILE . ' for update. Check file write permission.');
}

$total = strlen($newXml);
$written = 0;
while ($written < $total) {
    $n = @fwrite($handle, substr($newXml, $written));
    if ($n === false || $n === 0) {
        @flock($handle, LOCK_UN);
        fclose($handle);
        fail('could not write the complete RSS XML. Check file write permission.');
    }
    $written += $n;
}
@fflush($handle);
@flock($handle, LOCK_UN);
fclose($handle);

$title = (string)$issue['title'];
$count = count($issue['links']);
out("Videha RSS updated successfully.\nIssue: {$title}\nContents links: {$count}\nRSS: " . VIDEHA_RSS_URL);
