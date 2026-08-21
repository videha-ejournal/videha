(function(){"use strict";
const form=document.getElementById("askForm"),q=document.getElementById("askQ"),out=document.getElementById("askOut"),status=document.getElementById("askStatus"),mode=document.getElementById("askMode"),btn=form&&form.querySelector('button[type="submit"]');
let lastTerms=[];
const BAD=/(skip to main|ctrl\s*\+\s*f5|refresh|font-family|background:|border-radius|box-shadow|!important|linear-gradient|editorial reading skin|paris review register|new yorker|videha issn 2229-547x)/i;
function clean(s){return VidehaSearch.cleanText(s).replace(/^.*?(?=(?:[\u0900-\u097fA-Za-z]{3,}))/,'').trim()}
function sourceLabel(e){const u=e.url||"";if(/\/search-documents\/videha-/i.test(u))return"VIDEHA ARCHIVE";if(/\/search-documents\/sadeha-/i.test(u))return"SADEHA ARCHIVE";const s=String(e.source||"");return s||"VIDEHA SITE"}
function sourceHTML(ev){return '<details class="vds-card" open><summary><strong>मूल स्रोत · Sources ('+VidehaCore.toDeva(ev.length)+')</strong></summary><ol class="vds-results">'+ev.map(e=>`<li class="vds-result"><a href="${VidehaCore.escapeHTML(e.url)}">${VidehaCore.escapeHTML(e.title)}</a>${e.author?` <span class="vds-badge">${VidehaCore.escapeHTML(e.author)}</span>`:""} <span class="vds-badge">${VidehaCore.escapeHTML(sourceLabel(e))}</span><div class="vds-url">${VidehaCore.escapeHTML(e.url)}</div><p>${VidehaCore.escapeHTML(e.text)}</p></li>`).join("")+'</ol></details>'}
function sentenceCandidates(ev,query){const ts=VidehaSearch.terms(query),rows=[];for(const e of ev){const text=clean(e.text),parts=text.replace(/([।!?])\s+/g,"$1\n").replace(/\.\s+/g,".\n").split(/\n+/);for(let s of parts){s=s.trim();if(s.length<35||s.length>520||BAD.test(s))continue;const low=s.toLocaleLowerCase();let score=0;for(const t of ts){if(low.includes(t)){score+=10;score+=Math.min(4,low.split(t).length-1)*2}}if(/(?:जन्म|कवि|लेखक|रचना|ग्रन्थ|poet|writer|born|author)/i.test(s))score+=2;if(score>0)rows.push({s,score,url:e.url})}}rows.sort((a,b)=>b.score-a.score||a.s.length-b.s.length);const seen=new Set(),res=[];for(const r of rows){const k=r.s.toLocaleLowerCase().replace(/\W+/g,' ').slice(0,140);if(seen.has(k))continue;seen.add(k);res.push(r);if(res.length===3)break}return res}
function archiveAnswer(ev,query){const cand=sentenceCandidates(ev,query);if(cand.length)return cand.map(x=>x.s).join(" ");const first=ev.map(x=>clean(x.text)).find(x=>x&&!BAD.test(x));return first?first.slice(0,900):"विदेह अभिलेखमे सम्बन्धित स्रोत भेटल, मुदा साफ उत्तर-वाक्य निकालल नहि जा सकल। नीचे मूल स्रोत देखू।"}
function followupQuery(query){const ts=VidehaSearch.terms(query);if(ts.length<=1&&lastTerms.length&&/(हुनकर|ओकर|आओर|more|his|her|their|then|सेहो|फेर)/i.test(query))return query+" "+lastTerms.join(" ");if(ts.length)lastTerms=ts.slice(0,5);return query}
async function run(){
  const raw=q.value.trim();if(!raw){status.textContent="प्रश्न लिखू · Please enter a question.";q.focus();return}
  const query=followupQuery(raw),effective=VidehaSearch.queryForSearch?VidehaSearch.queryForSearch(query):query;
  if(btn)btn.disabled=true;status.textContent="मुख्य खोज-शब्द: "+effective+" · सम्पूर्ण विदेह–सदेह corpus मे खोजल जा रहल अछि…";out.innerHTML='<div class="vds-callout">Ask Videha unified search काम कऽ रहल अछि…</div>';
  try{
    /* No host-specific preferQuick: both websites now use the SAME complete Pagefind corpus. */
    const rows=await VidehaSearch.search(query,{limit:10});
    if(!rows.length){status.textContent="विदेह अभिलेखमे पर्याप्त स्रोत नहि भेटल।";out.innerHTML='<div class="vds-callout">एहि प्रश्न लेल indexed Videha corpus मे पर्याप्त स्रोत नहि भेटल। <a href="videha-universal-search.htm">Universal Search खोलू</a>।</div>';return}
    const evidence=rows.map((r,i)=>({n:i+1,title:r.meta?.title||r.url,url:r.url,author:r.meta?.author||"",source:r.meta?.source||"",text:clean(r.plain_excerpt||r.excerpt||"")})).filter(e=>e.text&&!BAD.test(e.text));
    if(mode&&mode.value==="sources"){status.textContent="मुख्य खोज-शब्द: "+effective+" · "+rows.length+" unified स्रोत भेटल";out.innerHTML=sourceHTML(evidence);return}
    const baseAnswer=archiveAnswer(evidence.length?evidence:rows.map((r,i)=>({n:i+1,title:r.meta?.title||r.url,url:r.url,author:r.meta?.author||"",source:r.meta?.source||"",text:clean(r.plain_excerpt||r.excerpt||"")})),effective);
    status.textContent="मुख्य खोज-शब्द: "+effective+" · "+evidence.length+" unified स्रोत";out.innerHTML=`<div class="vds-callout"><strong>उत्तर · Answer from complete Videha archive</strong><p>${VidehaCore.escapeHTML(baseAnswer)}</p></div>`+sourceHTML(evidence);
  }catch(e){console.error("Ask Videha error",e);status.textContent="Ask Videha engine error — कृपया फेर प्रयास करू।";out.innerHTML='<div class="vds-callout">तकनीकी समस्या आयल। <a href="videha-universal-search.htm">Universal Search</a> एखन उपयोग करू।</div>'}
  finally{if(btn)btn.disabled=false}
}
if(form)form.addEventListener("submit",e=>{e.preventDefault();run()});
})();
