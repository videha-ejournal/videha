#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

INDEX = Path("index.htm")
OUTPUT = Path("videha-rss.xml")
BASE = "https://www.videha.co.in/index.htm"
FEED = "https://www.videha.co.in/videha-rss.xml"

DEV = str.maketrans("०१२३४५६७८९", "0123456789")
MONTHS = {
    "जनवरी": 1, "फरवरी": 2, "मार्च": 3, "अप्रैल": 4, "मई": 5, "जून": 6,
    "जुलाई": 7, "अगस्त": 8, "सितम्बर": 9, "सितंबर": 9, "अक्टूबर": 10,
    "नवम्बर": 11, "नवंबर": 11, "दिसम्बर": 12, "दिसंबर": 12,
}


def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


class CurrentIssueParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_current = False
        self.depth = 0
        self.class_stack: list[set[str]] = []
        self.issue_number_parts: list[str] = []
        self.h2_depth = 0
        self.title_parts: list[str] = []
        self.anchor_href: str | None = None
        self.anchor_parts: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_d = dict(attrs)
        classes = set(attrs_d.get("class", "").split())
        if tag == "div":
            if not self.in_current and "videha-current-issue" in classes:
                self.in_current = True
                self.depth = 1
                self.class_stack = [classes]
                return
            if self.in_current:
                self.depth += 1
                self.class_stack.append(classes)
        elif self.in_current and tag == "h2":
            self.h2_depth += 1
        elif self.in_current and tag == "a":
            self.anchor_href = attrs_d.get("href")
            self.anchor_parts = []

    def handle_endtag(self, tag: str) -> None:
        if not self.in_current:
            return
        if tag == "a" and self.anchor_href is not None:
            text = clean_text("".join(self.anchor_parts))
            if text:
                self.links.append((urljoin(BASE, self.anchor_href), text))
            self.anchor_href = None
            self.anchor_parts = []
        elif tag == "h2" and self.h2_depth:
            self.h2_depth -= 1
        elif tag == "div":
            self.depth -= 1
            if self.class_stack:
                self.class_stack.pop()
            if self.depth == 0:
                self.in_current = False

    def handle_data(self, data: str) -> None:
        if not self.in_current:
            return
        if self.anchor_href is not None:
            self.anchor_parts.append(data)
        if self.h2_depth:
            self.title_parts.append(data)
        if self.class_stack and "issue-number-square" in self.class_stack[-1]:
            self.issue_number_parts.append(data)


text = INDEX.read_text(encoding="utf-8", errors="replace")
parser = CurrentIssueParser()
parser.feed(text)

issue_number_dev = clean_text("".join(parser.issue_number_parts))
title = clean_text("".join(parser.title_parts))
if not issue_number_dev or not title:
    raise SystemExit("Could not detect the current Videha issue in index.htm")

issue_number = issue_number_dev.translate(DEV)
if not issue_number.isdigit():
    raise SystemExit(f"Invalid issue number: {issue_number_dev}")

m = re.search(r"\[\s*([०-९0-9]{1,2})\s+([^\s\]]+)\s+([०-९0-9]{4})\s*\]", title)
if m:
    day = int(m.group(1).translate(DEV))
    month_name = m.group(2)
    year = int(m.group(3).translate(DEV))
    month = MONTHS.get(month_name)
else:
    day = month = year = None

ist = timezone(timedelta(hours=5, minutes=30))
now = datetime.now(ist)
if day and month and year:
    published = datetime(year, month, day, 0, 0, 0, tzinfo=ist)
    date_slug = f"{year:04d}-{month:02d}-{day:02d}"
else:
    published = now
    date_slug = now.strftime("%Y-%m-%d")

guid = f"{BASE}#issue-{issue_number}-{date_slug}"
items_html = "".join(
    f'<li><a href="{html.escape(url, quote=True)}">{html.escape(label)}</a></li>'
    for url, label in parser.links
)
description = (
    "<p>Videha — First Maithili Fortnightly eJournal · ISSN 2229-547X.</p>"
    "<p>Current issue contents:</p><ul>" + items_html + "</ul>"
)

xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
<title>Videha — New Issue · विदेह नूतन अंक</title>
<link>https://www.videha.co.in/</link>
<atom:link href="{FEED}" rel="self" type="application/rss+xml"/>
<description>New Videha Issue — twice monthly · विदेह प्रथम मैथिली पाक्षिक ई-पत्रिका · ISSN 2229-547X</description>
<language>mai</language>
<managingEditor>editorial.staff.videha@zohomail.in (Gajendra Thakur)</managingEditor>
<webMaster>editorial.staff.videha@zohomail.in (Videha)</webMaster>
<lastBuildDate>{format_datetime(now)}</lastBuildDate>
<ttl>720</ttl>
<item>
<title>{html.escape(title)}</title>
<link>{BASE}</link>
<guid isPermaLink="true">{guid}</guid>
<pubDate>{format_datetime(published)}</pubDate>
<description><![CDATA[{description}]]></description>
</item>
</channel>
</rss>
'''

OUTPUT.write_text(xml, encoding="utf-8")
print(f"Generated {OUTPUT} for issue {issue_number_dev}: {title}")
print(f"Included {len(parser.links)} current-issue links.")
