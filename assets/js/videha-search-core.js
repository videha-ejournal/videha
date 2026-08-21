(function(g){"use strict";
let pfPromise=null,pfSource="",quickPromise=null;
const STOP=new Set(("ke ki ka ko se me mein mai chhathi chhathi chhathin chhi achhi achhai chha chhai hai hain ho what who whom whose is are was were be been being the a an tell about please and or of to in on for with के की केर केँ कोन छथि अछि छैक छथिन छै छी छियै में मे सँ स पर आ वा अथवा एक ई ओ से हुनकर ओकर तकर सेहो किएक कहू बताउ बताऊ").split(/\s+/));
const SOURCE_BUCKETS=[
  {key:"current",label:"CURRENT ISSUE नूतन अंक",cap:3},
  {key:"parallel",label:"PARALLEL HISTORY / समानान्तर इतिहास",cap:3},
  {key:"archive",label:"VIDEHA ARCHIVE / विदेह पुरान अंक",cap:4},
  {key:"sadeha",label:"SADEHA ARCHIVE / सदेह",cap:3},
  {key:"site",label:"VIDEHA SITE / स्थायी पृष्ठ",cap:4}
];
const candidates=()=>[{u:"./pagefind/pagefind.js",source:"local"},{u:VidehaCore.GITHUB+"pagefind/pagefind.js",source:"github"}];
function timeout(p,ms,label){return Promise.race([p,new Promise((_,rej)=>setTimeout(()=>rej(new Error(label||"Timed out")),ms))])}
function norm(s){return String(s||"").toLocaleLowerCase().replace(/[“”"'`´’‘?!.:,;()\[\]{}\/\\|—–_-]+/g," ").replace(/\s+/g," ").trim()}
function terms(q){const a=(norm(q).match(/[a-z0-9\u0900-\u097f]+/g)||[]).filter(t=>t.length>1&&!STOP.has(t));return [...new Set(a)]}
const ENTITY_ALIASES={
  "vidyapati":["विद्यापति","vidyapati"],
  "vidyapathi":["विद्यापति","vidyapati"],
  "विद्यापति":["विद्यापति","vidyapati"],
  "gangesh":["गंगेश","gangesh","gangesha","gangesa"],
  "gangesha":["गंगेश","gangesh","gangesha","gangesa"],
  "gangesa":["गंगेश","gangesh","gangesha","gangesa"],
  "गंगेश":["गंगेश","gangesh","gangesha","gangesa"]
};
function queryVariants(q){
  const ts=terms(q);
  if(!ts.length)return [norm(q)].filter(Boolean);
  const base=ts.join(" "),out=[];
  const add=x=>{x=String(x||"").trim();if(x&&!out.includes(x))out.push(x)};
  add(base);
  if(ts.length===1&&ENTITY_ALIASES[ts[0]])ENTITY_ALIASES[ts[0]].forEach(add);
  return out;
}
function queryForSearch(q){return queryVariants(q)[0]||norm(q)}
function cleanText(s){return String(s||"").replace(/<[^>]+>/g," ").replace(/\/\*.*?\*\//gs," ").replace(/\b(?:font-family|background|border-radius|box-shadow|linear-gradient|!important)\b[^।.!?]{0,180}/gi," ").replace(/\s+/g," ").trim()}
function context(text,q,max){text=cleanText(text);const ts=terms(q),low=norm(text),n=max||700;let i=-1;for(const t of ts){i=low.indexOf(t);if(i>=0)break}if(i<0)return text.slice(0,n);const start=Math.max(0,i-Math.floor(n*.34)),end=Math.min(text.length,start+n);return(start?"…":"")+text.slice(start,end)+(end<text.length?"…":"")}

/* Lightweight JSON is fallback-only. The normal path on BOTH hosts is the same full Pagefind corpus. */
async function loadQuick(){
  if(!quickPromise)quickPromise=(async()=>{
    const bases=[VidehaCore.GITHUB+"videha-search-index.json","./videha-search-index.json",VidehaCore.PRIMARY+"videha-search-index.json"];
    for(const u of bases){try{const r=await timeout(fetch(u,{cache:"no-store",mode:"cors"}),6500,"Quick index timeout");if(r.ok){const j=await r.json();return j.entries||j||[]}}catch(e){}}
    return[];
  })();
  return quickPromise;
}
async function quickSearch(q,limit){
  try{
    const arr=await loadQuick(),ts=terms(q);if(!ts.length)return[];
    const phrase=ts.join(" "),scored=[];
    for(const e of arr){
      const title=norm(e.t),author=norm(e.a),short=norm(e.s),full=norm(e.x);let score=0,matched=0;
      if(phrase&&phrase.length>2){if(title.includes(phrase))score+=90;if(author.includes(phrase))score+=80;if(short.includes(phrase))score+=45;if(full.includes(phrase))score+=30}
      for(const t of ts){let hit=false;if(title.includes(t)){score+=30;hit=true}if(author.includes(t)){score+=26;hit=true}if(short.includes(t)){score+=14;hit=true}if(full.includes(t)){const c=Math.min(6,full.split(t).length-1);score+=8+c*2;hit=true}if(hit)matched++}
      if(matched&&score>0){score+=matched===ts.length?25:0;scored.push({e,score})}
    }
    scored.sort((a,b)=>b.score-a.score);
    return scored.slice(0,limit||20).map(({e,score})=>({url:VidehaCore.resolveSearchUrl(e.f),meta:{title:e.t||e.f,author:e.a||"",category:e.c||"",year:e.y||"",issue:e.i||"",source:"VIDEHA SITE / स्थायी पृष्ठ"},plain_excerpt:context(e.x||e.s||"",q,720),_fallback:true,_quick:true,_rankScore:score}));
  }catch(e){return[]}
}

async function pagefind(){
  if(!pfPromise)pfPromise=(async()=>{
    let last;
    for(const c of candidates()){
      try{
        const mod=await timeout(import(c.u),10000,"Pagefind module timeout");
        let pf=mod;
        if(mod.createInstance){const base=c.u.replace(/pagefind\.js(?:[?#].*)?$/i,"");pf=mod.createInstance({basePath:base,noWorker:c.source==="github"&&VidehaCore.hostMode()!=="github"})}
        await timeout(pf.init(),10000,"Pagefind init timeout");pfSource=c.source;return pf;
      }catch(e){last=e}
    }
    throw last||new Error("Pagefind unavailable");
  })().catch(e=>{pfPromise=null;throw e});
  return pfPromise;
}
function urlKey(u){return String(u||"").replace(/[?#].*$/,'').replace(/^https?:\/\/(?:www\.)?videha\.co\.in\//i,'').replace(/^https?:\/\/videha-ejournal\.github\.io\/videha\//i,'').replace(/^\/+/,"")}
function sourceKey(r){
  const u=urlKey(r.url),s=norm(r.meta&&r.meta.source||"");
  if(/^search-documents\/videha-/i.test(u)||s.includes("videha archive"))return"archive";
  if(/^search-documents\/sadeha-/i.test(u)||s.includes("sadeha archive"))return"sadeha";
  if(s.includes("current issue"))return"current";
  if(s.includes("parallel history")||/^gajenthakur\.htm$/i.test(u)||/^new_page_(?:[1-9]|[1-9][0-9]|100)\.htm$/i.test(u)&&s.includes("parallel"))return"parallel";
  return"site";
}
function scoreRow(r,q){
  const ts=terms(q),phrase=ts.join(" "),title=norm(r.meta&&r.meta.title||""),author=norm(r.meta&&r.meta.author||""),ex=norm(r.plain_excerpt||r.excerpt||"");let score=Number(r._pfScore||0)*10;
  if(phrase){if(title===phrase)score+=150;if(title.includes(phrase))score+=90;if(author.includes(phrase))score+=85;if(ex.includes(phrase))score+=35}
  for(const t of ts){if(title.includes(t))score+=35;if(author.includes(t))score+=32;if(ex.includes(t))score+=10}
  const k=sourceKey(r);if(k==="current")score+=5;else if(k==="parallel")score+=4;else if(k==="archive")score+=3;else if(k==="sadeha")score+=2;
  return score;
}
function dedupeRows(rows){
  const by=new Map();
  for(const r of rows){const k=urlKey(r.url);if(!k)continue;const old=by.get(k);if(!old||Number(r._rankScore||0)>Number(old._rankScore||0))by.set(k,r)}
  return [...by.values()];
}
function diversify(rows,limit){
  const lim=limit||20,sorted=[...rows].sort((a,b)=>Number(b._rankScore||0)-Number(a._rankScore||0));
  const cap=Object.fromEntries(SOURCE_BUCKETS.map(x=>[x.key,x.cap])),used={},out=[],deferred=[];
  for(const r of sorted){const k=sourceKey(r);used[k]=used[k]||0;if((used[k]||0)<(cap[k]||4)){out.push(r);used[k]++;}else deferred.push(r);if(out.length>=lim)break}
  if(out.length<lim){for(const r of deferred){if(out.includes(r))continue;out.push(r);if(out.length>=lim)break}}
  return out;
}
async function fetchData(result,sq,bucket){
  const d=await timeout(result.data(),8000,"Pagefind result timeout");
  const row={...d,url:VidehaCore.resolveSearchUrl(d.url),plain_excerpt:cleanText(d.plain_excerpt||d.excerpt||""),_pagefindSource:pfSource,_searchQuery:sq,_bucket:bucket,_pfScore:Number(result.score||0)};
  row._rankScore=scoreRow(row,sq);
  return row;
}
async function searchOne(pf,sq,opts,bucket){
  try{
    const po={...(opts||{})},take=po._take||20;delete po._take;
    const found=await timeout(pf.search(sq,po),12000,"Pagefind search timeout"),raw=(found.results||[]).slice(0,take);
    return await Promise.all(raw.map(r=>fetchData(r,sq,bucket)));
  }catch(e){return[]}
}
async function deepSearch(q,opts){
  const limit=opts.limit||20,pf=await pagefind(),variants=queryVariants(q),all=[];
  for(const sq of variants){
    /* General + source-specific searches run together, so the low-cost server does not pay six serial waits. */
    const baseFilters={...(opts.filters||{})},jobs=[searchOne(pf,sq,{filters:Object.keys(baseFilters).length?baseFilters:undefined,_take:Math.max(30,limit*4)},"all")];
    /* If the caller itself selected a source filter, respect it instead of broadening the query. */
    if(!Object.prototype.hasOwnProperty.call(baseFilters,"source")){
      for(const b of SOURCE_BUCKETS)jobs.push(searchOne(pf,sq,{filters:{...baseFilters,source:b.label},_take:Math.max(8,b.cap*3)},b.key));
    }
    const groups=await Promise.all(jobs);for(const group of groups)all.push(...group);
  }
  const dedup=dedupeRows(all);
  for(const r of dedup)r._rankScore=scoreRow(r,q);
  return diversify(dedup,limit);
}
async function search(q,opts){
  opts=opts||{};const limit=opts.limit||20;
  /* SAME primary engine on GitHub and videha.co.in: full Pagefind corpus. */
  try{const deep=await deepSearch(q,{...opts,limit});if(deep.length)return deep}catch(e){}
  /* Only if Pagefind is unavailable do we fall back to the light index. */
  const fallback=[];for(const sq of queryVariants(q))fallback.push(...await quickSearch(sq,Math.max(limit,20)));
  const dedup=dedupeRows(fallback);for(const r of dedup)r._rankScore=scoreRow(r,q);return diversify(dedup,limit);
}
async function filters(){try{return await timeout((await pagefind()).filters(),8000,"Pagefind filters timeout")}catch(e){return{}}}
g.VidehaSearch={search,filters,pagefind,quickSearch,terms,queryForSearch,queryVariants,cleanText,sourceKey,source:()=>pfSource};
})(window);
