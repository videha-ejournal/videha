VIDEHA Search All Roman/Devanagari Fix

Merge this package into BOTH github/videha and the Videha server httpdocs.
Do not delete destination folders. Replace same-name files.

Fix: Roman/IAST queries are searched as original Roman plus generated Devanagari variants across the SAME Pagefind corpus.
Examples: shantilakshmi includes शान्तिलक्ष्मी; vidyapati includes विद्यापति; gangesh includes गंगेश; ramanand includes रमानन्द.
Approved URL routing is unchanged: mirrored pages use current host; search-documents/* always resolves to GitHub.
