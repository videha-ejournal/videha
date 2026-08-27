#!/usr/bin/env python3
"""Find unresolved probable legacy author/title reversals confirmed by Sadeha.

Review-only: never publishes or rewrites metadata. Decisions already recorded in
scholar-data/sadeha-swapped-review-decisions.json are retained as resolved history
and removed from the unresolved queue.
"""
from __future__ import annotations
import json, re
from pathlib import Path
from extract_explicit_research import SourceParser
ROOT=Path(__file__).resolve().parents[1]
INV=ROOT/"research"/"data"/"article-inventory.json"
OUT=ROOT/"research"/"data"/"sadeha-swapped-metadata-review.json"
DEC=ROOT/"scholar-data"/"sadeha-swapped-review-decisions.json"
PUNCT=re.compile(r"[\s\-–—:;,.()\[\]{}'\"’‘“”।!?/\\|]+")
TITLE_SIGNALS=("संरचना","साहित्य","रंगकर्म","इतिहास","संस्कृति","भाषा","व्याकरण","आलोचना","समीक्षा","विमर्श","अध्ययन","अनुशीलन","नाटक","उपन्यास","कथा","समाज","मिथिला","मैथिली","लोकगीत","लोक गीत","संस्कार गीत","परिवर्तन","परम्परा","परंपरा","गाथा","चित्रकला","लोककला","research","study","history","criticism","literature","language")
NON_ARTICLE_SIGNALS=("कविता","गीत १","गजल १","बाल गीत","समाचार","साक्षात्कार")
NAME_PREFIXES=("डा","डॉ","प्रो","प्रोफेसर","आचार्य","पं","पं.","श्री","श्रीमती","कवि","लेखक","लेखिका")
def norm(s): return PUNCT.sub("",(s or "").lower())
def plain(s): return re.sub(r"\s+"," ",s or "").strip(" .:-–—")
def looks_name(s):
 s=plain(s); low=s.lower(); words=s.split()
 return 3<=len(s)<=90 and not any(c in s for c in "/|।?!") and not any(x.lower() in low for x in TITLE_SIGNALS) and 1<=len(words)<=9 and (len(words)>=2 or low.startswith(tuple(x.lower() for x in NAME_PREFIXES)))
def looks_title(s):
 s=plain(s); low=s.lower()
 return 10<=len(s)<=300 and not low.startswith(tuple(x.lower() for x in NAME_PREFIXES)) and any(x.lower() in low for x in TITLE_SIGNALS)
def decisions():
 if not DEC.exists(): return {}
 d=json.loads(DEC.read_text(encoding="utf-8")); return {(str(int(str(x.get("issue") or 0))),str(x.get("section") or "")):x for x in d.get("decisions",[])}
def sadeha_docs():
 out=[]
 for p in sorted((ROOT/"search-documents").glob("sadeha-*.html")):
  q=SourceParser();
  try:q.feed(p.read_text(encoding="utf-8",errors="ignore"))
  except Exception:pass
  out.append((p.relative_to(ROOT).as_posix(),norm(q.text())))
 return out
def main():
 rows=json.loads(INV.read_text(encoding="utf-8")).get("rows",[]); docs=sadeha_docs(); dec=decisions(); unresolved=[]; resolved=[]; seen=set()
 for row in rows:
  issue=str(row.get("issue") or ""); section=str(row.get("section") or "")
  if section.startswith("3."): continue
  pa=plain(str(row.get("author") or "")); pt=plain(str(row.get("title") or ""))
  if any(x.lower() in pa.lower() for x in NON_ARTICLE_SIGNALS) or not (looks_title(pa) and looks_name(pt)): continue
  na,nt=norm(pt),norm(pa); evidence=None
  for path,text in docs:
   pos=text.find(nt)
   if pos>=0 and na in text[max(0,pos-2200):min(len(text),pos+len(nt)+2200)]: evidence=path; break
  if not evidence: continue
  key=(issue,section,nt,na)
  if key in seen: continue
  seen.add(key)
  rec={"issue":issue,"section":section,"parsed_author":pa,"parsed_title":pt,"proposed_author_for_review":pt,"proposed_title_for_review":pa,"sadeha_evidence":evidence,"body_chars_current_parse":row.get("body_chars")}
  d=dec.get((issue,section))
  if d:
   rec.update({"status":"resolved","decision":d.get("decision"),"decision_reason":d.get("reason")}); resolved.append(rec)
  else:
   rec.update({"status":"editorial-review-only","note":"Verify original Videha heading/body before metadata override or publication."}); unresolved.append(rec)
 unresolved.sort(key=lambda x:(int(x["issue"] or 0),x["section"])); resolved.sort(key=lambda x:(int(x["issue"] or 0),x["section"]))
 payload={"sadeha_html_sources":len(docs),"probable_swapped_metadata_records":len(unresolved)+len(resolved),"resolved_editorially":len(resolved),"unresolved_editorial_queue":len(unresolved),"publication_effect":"none; decisions drive separate explicit promotion whitelist","rows":unresolved,"resolved":resolved}
 OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
 print(f"Sadeha legacy metadata review: {len(resolved)} resolved; {len(unresolved)} unresolved; publication effect handled only by explicit promotion whitelist")
if __name__=="__main__": main()
