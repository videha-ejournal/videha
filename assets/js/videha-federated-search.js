(function(){
'use strict';
const PF_SOURCES=[
  {id:'sadeha',label:'Videha Sadeha',base:'https://videha-ejournal.github.io/videha-sadeha/',index:'https://videha-ejournal.github.io/videha-sadeha/pagefind-videha-search/'},
  {id:'root',label:'Videha GitHub Library',base:'https://videha-ejournal.github.io/',index:'https://videha-ejournal.github.io/pagefind-videha-search/'}
];
const PDF_CATALOGS=[
  {id:'ejournal-pdf',label:'Videha eJournal PDF',base:'https://videha-ejournal.github.io/videha-ejournal/',url:'https://videha-ejournal.github.io/videha-ejournal/data/videha-pdf-catalog.json'},
  {id:'sadeha-pdf',label:'Videha Sadeha PDF',base:'https://videha-ejournal.github.io/videha-sadeha/',url:'https://videha-ejournal.github.io/videha-sadeha/data/sadeha-pdf-catalog.json'}
];
const instances=new Map();
const pdfPromises=new Map();
function norm(s){return String(s||'').normalize('NFC').toLowerCase().replace(/[\u200c\u200d]/g,'').replace(/[^\p{L}\p{N}]+/gu,' ').replace(/\s+/g,' ').trim();}
function variants(q){
  try{if(window.VidehaSearch&&typeof VidehaSearch.queryVariants==='function')return VidehaSearch.queryVariants(q).filter(Boolean);}
  catch(e){}
  return [String(q||'').trim()].filter(Boolean);
}
function timeout(p,ms,fallback){return Promise.race([p,new Promise(r=>setTimeout(()=>r(fallback),ms))]);}
function absolute(src,u){
  /* The source declaration is authoritative. Never trust a Pagefind URL to carry
     the correct host/project prefix: rebuild it from src.base. */
  let raw=String(u||'').trim();if(!raw)return src.base;
  let suffix='';const sm=raw.match(/([?#].*)$/);if(sm){suffix=sm[1];raw=raw.slice(0,-sm[1].length);}
  let path=raw;
  if(/^https?:\/\//i.test(raw)){try{path=new URL(raw).pathname;}catch(e){path=raw;}}
  path=String(path||'').replace(/\\/g,'/').replace(/^\.?\/+/, '');
  try{path=decodeURIComponent(path);}catch(e){}
  const bu=new URL(src.base),project=bu.pathname.replace(/^\/+|\/+$/g,'');
  const parts=path.split('/').filter(Boolean);
  if(project){
    const lp=project.toLowerCase();let at=-1;
    for(let i=0;i<parts.length;i++)if(parts[i].toLowerCase()===lp){at=i;break;}
    if(at>=0)path=parts.slice(at+1).join('/');
    else path=parts.join('/').replace(/^videha\//i,'');
  }else{
    path=parts.join('/').replace(/^videha\//i,'');
  }
  return src.base+path+suffix;
}
async function getPf(src){
  if(!instances.has(src.id))instances.set(src.id,(async()=>{
    const mod=await import(src.index+'pagefind.js');let pf=mod;
    if(mod.createInstance)pf=mod.createInstance({basePath:src.index,noWorker:true});
    await pf.init();return pf;
  })().catch(e=>{instances.delete(src.id);throw e;}));
  return instances.get(src.id);
}
async function searchOne(src,q,limit){
  try{
    const pf=await getPf(src),out=new Map();
    for(const term of variants(q)){
      const found=await pf.search(term),raw=found.results||[];
      const rows=await Promise.all(raw.slice(0,Math.max(24,limit||24)).map(r=>r.data()));
      for(const row of rows){
        const url=absolute(src,row.url),key=url.replace(/[?#].*$/,'');
        if(!out.has(key))out.set(key,{...row,url,_federated:true,_source:src.label,_externalBase:src.base,_xscript:term!==q});
      }
    }
    return [...out.values()].slice(0,limit||40);
  }catch(e){return[];}
}
function merge(groups,limit){const out=[],seen=new Set();let i=0;while(out.length<(limit||80)){let added=false;for(const g of groups){const r=(g||[])[i];if(!r)continue;added=true;const k=String(r.url||'').replace(/[?#].*$/,'');if(k&&!seen.has(k)){seen.add(k);out.push(r);if(out.length>=(limit||80))break;}}if(!added)break;i++;}return out;}
async function loadPdf(src){if(!pdfPromises.has(src.id))pdfPromises.set(src.id,fetch(src.url,{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('PDF catalog '+src.id+' '+r.status);return r.json();}).catch(e=>{pdfPromises.delete(src.id);throw e;}));return pdfPromises.get(src.id);}
function pdfScore(e,q){const forms=variants(q).map(norm).filter(Boolean),text=norm([e.title,e.name,e.path].join(' '));let s=0;for(const f of forms){if(!f)continue;if(text===f)s=Math.max(s,500);else if(text.startsWith(f))s=Math.max(s,350);else if(text.includes(f))s=Math.max(s,220);else{const ts=f.split(' ').filter(Boolean);if(ts.length&&ts.every(t=>text.includes(t)))s=Math.max(s,160);}}return s;}
async function searchPdf(q,limit){const groups=await Promise.all(PDF_CATALOGS.map(async src=>{try{const cat=await loadPdf(src),arr=Array.isArray(cat)?cat:(cat.items||[]),hits=[];for(const e of arr){const score=pdfScore(e,q);if(!score)continue;hits.push({score,url:e.url||(src.base+String(e.path||'').replace(/^\/+/,'')),meta:{title:e.title||e.name||e.path||'Videha PDF'},plain_excerpt:(e.path||e.name||'')+' · '+src.label+' archive',excerpt:'',_federated:true,_pdfRepo:true,_source:src.label,_externalBase:src.base});}hits.sort((a,b)=>b.score-a.score||String(a.meta.title).localeCompare(String(b.meta.title)));return hits.slice(0,Math.max(20,limit||40));}catch(e){return[];}}));const out=[],seen=new Set();for(const g of groups){for(const r of g){const k=norm((r.meta&&r.meta.title)||'')+'|'+norm((r.url||'').split('/').pop()||'');if(k&&seen.has(k))continue;if(k)seen.add(k);out.push(r);}}out.sort((a,b)=>(b.score||0)-(a.score||0)||String(a.meta&&a.meta.title||'').localeCompare(String(b.meta&&b.meta.title||'')));return out.slice(0,limit||40);}
async function searchAll(q,limitEach){const groups=await Promise.all(PF_SOURCES.map(s=>timeout(searchOne(s,q,limitEach||20),5500,[])));const pdf=await timeout(searchPdf(q,Math.max(6,limitEach||10)),4500,[]);return merge(groups.concat([pdf]),Math.max(30,(limitEach||20)*PF_SOURCES.length+10));}
window.VidehaFederatedSearch={searchAll,searchPdf,searchOne,sources:PF_SOURCES,pdfCatalogs:PDF_CATALOGS};
})();
