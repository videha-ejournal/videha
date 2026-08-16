<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:s="http://www.sitemaps.org/schemas/sitemap/0.9"
  xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <xsl:output method="html" encoding="UTF-8" indent="yes"
    doctype-system="about:legacy-compat"/>

  <xsl:template match="/">
    <html lang="mai">
      <head>
        <meta charset="UTF-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title>विदेह · Sitemap — First Maithili Fortnightly eJournal</title>
        <style>
          :root{ --crimson:#8B1A1A; --crimson-d:#6f1414; --gold:#c49a3c;
                 --cream:#FAF6EE; --cream2:#f3ead7; --ink:#2b211c; --line:#e4d3a8; }
          *{ box-sizing:border-box; }
          body{ margin:0; background:var(--cream); color:var(--ink);
                font:15px/1.6 "Noto Serif Devanagari","Segoe UI",system-ui,serif; }
          .wrap{ max-width:1080px; margin:0 auto; padding:0 16px 56px; }
          header.hd{ background:linear-gradient(135deg,var(--crimson),var(--crimson-d));
                color:var(--cream); padding:30px 24px; border-bottom:4px solid var(--gold); }
          header.hd .wrap{ padding-bottom:0; }
          .eyebrow{ letter-spacing:.18em; text-transform:uppercase; font-size:12px;
                color:var(--gold); margin:0 0 6px; }
          h1{ margin:0; font-size:30px; }
          h1 .deva{ color:var(--cream); }
          .sub{ margin:8px 0 0; opacity:.92; font-size:14px; }
          .stats{ display:flex; flex-wrap:wrap; gap:14px; margin:22px 0 8px; }
          .chip{ background:#fff; border:1px solid var(--line); border-left:4px solid var(--crimson);
                border-radius:8px; padding:12px 18px; box-shadow:0 1px 2px rgba(0,0,0,.05); }
          .chip b{ display:block; font-size:26px; color:var(--crimson); line-height:1.1; }
          .chip span{ font-size:12px; letter-spacing:.04em; color:#6b5d52; }
          table{ width:100%; border-collapse:collapse; margin-top:14px; background:#fff;
                border:1px solid var(--line); border-radius:10px; overflow:hidden; }
          thead th{ background:var(--cream2); color:var(--crimson-d); text-align:left;
                font-size:12px; letter-spacing:.06em; text-transform:uppercase;
                padding:12px 14px; border-bottom:2px solid var(--gold); }
          tbody td{ padding:11px 14px; border-bottom:1px solid #f0e7d4; vertical-align:top; }
          tbody tr:nth-child(even){ background:#fffdf8; }
          tbody tr:hover{ background:#fdf6e6; }
          td.idx{ color:#b7a98f; font-variant-numeric:tabular-nums; width:46px; }
          a{ color:var(--crimson); text-decoration:none; word-break:break-all; }
          a:hover{ text-decoration:underline; }
          .pill{ display:inline-block; font-size:12px; padding:2px 9px; border-radius:999px;
                background:var(--cream2); border:1px solid var(--line); color:#6b5d52; }
          .prio{ font-variant-numeric:tabular-nums; font-weight:600; color:var(--crimson); }
          .imgs{ color:var(--gold); font-weight:600; }
          footer{ margin-top:26px; font-size:12.5px; color:#7c6e62; text-align:center; }
          @media(max-width:640px){ .hide-sm{ display:none; } h1{ font-size:24px; } }
        </style>
      </head>
      <body>
        <header class="hd">
          <div class="wrap">
            <p class="eyebrow">विदेह · ISSN 2229-547X · Since 2000</p>
            <h1><span class="deva">विदेह</span> — XML Sitemap</h1>
            <p class="sub">प्रथम मैथिली पाक्षिक ई पत्रिका · First Maithili Fortnightly eJournal ·
              <a style="color:var(--gold)" href="https://www.videha.co.in/">www.videha.co.in</a></p>
          </div>
        </header>
        <div class="wrap">
          <div class="stats">
            <div class="chip"><b><xsl:value-of select="count(s:urlset/s:url)"/></b>
              <span>PAGES · पृष्ठ</span></div>
            <div class="chip"><b><xsl:value-of select="count(s:urlset/s:url/image:image)"/></b>
              <span>INDEXED IMAGES · छवि</span></div>
          </div>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>URL</th>
                <th class="hide-sm">Last modified</th>
                <th class="hide-sm">Frequency</th>
                <th>Priority</th>
                <th class="hide-sm">Images</th>
              </tr>
            </thead>
            <tbody>
              <xsl:for-each select="s:urlset/s:url">
                <tr>
                  <td class="idx"><xsl:value-of select="position()"/></td>
                  <td><a href="{s:loc}"><xsl:value-of select="s:loc"/></a></td>
                  <td class="hide-sm"><xsl:value-of select="s:lastmod"/></td>
                  <td class="hide-sm"><span class="pill"><xsl:value-of select="s:changefreq"/></span></td>
                  <td class="prio"><xsl:value-of select="s:priority"/></td>
                  <td class="hide-sm imgs">
                    <xsl:if test="count(image:image) &gt; 0"><xsl:value-of select="count(image:image)"/></xsl:if>
                    <xsl:if test="count(image:image) = 0">—</xsl:if>
                  </td>
                </tr>
              </xsl:for-each>
            </tbody>
          </table>
          <footer>
            Generated for search engines · Sitemaps protocol 0.9 with Google Image extension.
            This styled view is for humans; crawlers read the raw XML.
          </footer>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
