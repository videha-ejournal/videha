#!/usr/bin/env python3
"""Add the minted Videha archive-release DOIs to every published research paper.

This is intentionally idempotent. Generated article pages and the small set of
legacy-preserved research pages are both covered, so a Scholar rebuild cannot
leave the archive/preservation links inconsistent across the corpus.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
START = "<!-- VIDEHA_ARCHIVE_RELEASES_START -->"
END = "<!-- VIDEHA_ARCHIVE_RELEASES_END -->"

BLOCK = f'''{START}
<section id="videha-archive-releases" class="citation" aria-labelledby="videha-archive-releases-title" data-pagefind-ignore="all">
<h2 id="videha-archive-releases-title">Videha Digital Research Archives — preserved releases</h2>
<p><strong>All eight archive releases are published and their DOIs are minted.</strong></p>
<ul>
<li><strong>gajendra-preeti</strong> — <a href="https://doi.org/10.5281/zenodo.22754971" rel="external">10.5281/zenodo.22754971</a></li>
<li><strong>mithila-vajji-anga</strong> — <a href="https://doi.org/10.5281/zenodo.22754977" rel="external">10.5281/zenodo.22754977</a></li>
<li><strong>videha</strong> — <a href="https://doi.org/10.5281/zenodo.22754996" rel="external">10.5281/zenodo.22754996</a></li>
<li><strong>videha-ejournal</strong> — <a href="https://doi.org/10.5281/zenodo.22755007" rel="external">10.5281/zenodo.22755007</a></li>
<li><strong>videha-ejournal.github.io</strong> — <a href="https://doi.org/10.5281/zenodo.22755014" rel="external">10.5281/zenodo.22755014</a></li>
<li><strong>videha-literature-festival</strong> — <a href="https://doi.org/10.5281/zenodo.22755018" rel="external">10.5281/zenodo.22755018</a></li>
<li><strong>videha-quiz</strong> — <a href="https://doi.org/10.5281/zenodo.22755026" rel="external">10.5281/zenodo.22755026</a></li>
<li><strong>videha-sadeha</strong> — <a href="https://doi.org/10.5281/zenodo.22755033" rel="external">10.5281/zenodo.22755033</a></li>
</ul>
</section>
{END}'''

BLOCK_RE = re.compile(
    re.escape(START) + r".*?" + re.escape(END),
    flags=re.S,
)


def update_page(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="strict")
    if START in text and END in text:
        new_text, replacements = BLOCK_RE.subn(BLOCK, text, count=1)
        status = "replaced" if replacements and new_text != text else "current"
    else:
        anchor = "</main>" if "</main>" in text else "</body>"
        if anchor not in text:
            raise ValueError(f"No </main> or </body> insertion point: {path}")
        new_text = text.replace(anchor, BLOCK + "\n" + anchor, 1)
        status = "added"
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
    return status


def main() -> None:
    pages = sorted(RESEARCH.glob("[0-9][0-9][0-9][0-9]/*/*.htm"))
    stats = {"added": 0, "replaced": 0, "current": 0}
    for page in pages:
        stats[update_page(page)] += 1

    print(
        "Videha archive DOI links: "
        f"{len(pages)} research papers checked; "
        f"{stats['added']} added; {stats['replaced']} replaced; "
        f"{stats['current']} already current."
    )
    if len(pages) != 839:
        raise SystemExit(
            f"Expected 839 published research papers, found {len(pages)}; "
            "refusing silent partial coverage."
        )


if __name__ == "__main__":
    main()
