(function(g){"use strict";
const PRIMARY="https://www.videha.co.in/";
const GITHUB="https://videha-ejournal.github.io/videha/";
const RESEARCH="https://videha-ejournal.github.io/mithila-vajji-anga/";
const GH_ORG="https://github.com/videha-ejournal";
const ISSN="2229-547X";
const GH_ROOT="https://videha-ejournal.github.io/";
const GH_PATH="/videha/";
const GH_PROJECTS=["videha-quiz","videha-sadeha","videha-ejournal"];
function hostMode(){const h=location.hostname.toLowerCase();if(h.endsWith("github.io"))return"github";if(h==="www.videha.co.in"||h==="videha.co.in")return"primary";return"local";}
function splitSuffix(u){const s=String(u||"");const m=s.match(/([?#].*)$/);return m?[s.slice(0,-m[1].length),m[1]]:[s,""];}
function canonicalGitHubUrl(u){const raw=String(u||"").trim();if(!raw)return"";let[x,suffix]=splitSuffix(raw);if(/^https?:\/\/videha-ejournal\.github\.io\//i.test(x)){x=x.replace(/^https?:\/\/videha-ejournal\.github\.io\/videha\/(videha-(?:quiz|sadeha|ejournal)\/)/i,GH_ROOT+"$1");return x+suffix;}const primaryProject=x.match(/^https?:\/\/(?:www\.)?videha\.co\.in\/(videha-(?:quiz|sadeha|ejournal)\/.*)$/i);if(primaryProject)return GH_ROOT+primaryProject[1]+suffix;let rel=x.replace(/^\.?\/+/,"");rel=rel.replace(/^videha\/(videha-(?:quiz|sadeha|ejournal)\/)/i,"$1");if(GH_PROJECTS.some(p=>rel.toLowerCase().startsWith(p+"/")))return GH_ROOT+rel+suffix;return"";}
function stripKnownPath(path){path=String(path||"").replace(/^https?:\/\/[^/]+/i,"");path=path.split(/[?#]/)[0];if(path.startsWith(GH_PATH))path=path.slice(GH_PATH.length);else path=path.replace(/^\/+/,"");return path;}
function isHistorical(u){return /(?:^|\/)search-documents\//i.test(String(u||""));}
function isExternal(u){return /^(?:mailto:|tel:|javascript:|data:|blob:|#)/i.test(String(u||""))||(/^https?:\/\//i.test(String(u||""))&&!/(?:videha\.co\.in|videha-ejournal\.github\.io)/i.test(String(u||"")));}
function resolveSearchUrl(u){u=String(u||"").trim();if(!u)return u;const gh=canonicalGitHubUrl(u);if(gh)return gh;if(isExternal(u))return u;let suffix="";const sm=u.match(/([?#].*)$/);if(sm)suffix=sm[1];const p=stripKnownPath(u);if(isHistorical(p))return GITHUB+p.replace(/^\/+/,"")+suffix;const mode=hostMode();if(mode==="github")return GITHUB+p.replace(/^\/+/,"")+suffix;if(mode==="primary")return PRIMARY+p.replace(/^\/+/,"")+suffix;return u;}
function toolUrl(file,heavy){file=String(file||"").replace(/^\/+/,"");if(heavy&&hostMode()==="primary")return GITHUB+file;return resolveSearchUrl(file);}
function lowData(){try{return localStorage.getItem("videha.lowData")==="1"}catch(e){return false}}
function setLowData(v){try{localStorage.setItem("videha.lowData",v?"1":"0")}catch(e){}document.documentElement.classList.toggle("vds-low-data",!!v);g.dispatchEvent(new CustomEvent("videha:lowdata",{detail:{enabled:!!v}}));}
function initLowData(){setLowData(lowData());document.querySelectorAll("[data-vds-lowdata]").forEach(b=>{b.setAttribute("aria-pressed",lowData()?"true":"false");b.addEventListener("click",()=>{const n=!lowData();setLowData(n);b.setAttribute("aria-pressed",n?"true":"false");b.textContent=n?"हल्का मोड: चालू · Low Data: ON":"हल्का मोड · Low Data";});});}
function ensureMeta(name,content){let m=document.head&&document.head.querySelector('meta[name="'+name+'"]');if(!m&&document.head){m=document.createElement("meta");m.setAttribute("name",name);document.head.appendChild(m);}if(m)m.setAttribute("content",content);}
function appendIdentityText(parent,text){const span=document.createElement("span");span.textContent=text;parent.appendChild(span);}
function appendIdentityLink(parent,label,url){const span=document.createElement("span");if(label)span.appendChild(document.createTextNode(label+" "));const a=document.createElement("a");a.href=url;a.textContent=url;a.rel="home";span.appendChild(a);parent.appendChild(span);}
function initScholarlyIdentity(){
  ensureMeta("citation_journal_title","Videha — First Maithili Fortnightly eJournal");
  ensureMeta("citation_issn",ISSN);
  ensureMeta("citation_website_url",PRIMARY);
  ensureMeta("citation_mirror_url",GITHUB);
  ensureMeta("citation_research_archive_url",RESEARCH);
  ensureMeta("citation_archive_network_url",GH_ORG);
  ensureMeta("DC.identifier","ISSN "+ISSN);
  ensureMeta("DC.publisher","Videha — First Maithili Fortnightly eJournal");
  if(!document.body||document.querySelector('[data-videha-scholarly-identity="true"]'))return;
  const aside=document.createElement("aside");
  aside.setAttribute("data-videha-scholarly-identity","true");
  aside.setAttribute("aria-label","Videha publication and research archive identity");
  aside.style.cssText="display:flex;flex-wrap:wrap;justify-content:center;gap:.3rem .55rem;margin:0;padding:.6rem 1rem;border-top:1px solid #d8cfc0;background:#fff8e6;color:#2c2924;font:700 12px/1.5 system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;text-align:center;overflow-wrap:anywhere";
  appendIdentityText(aside,"Videha — First Maithili Fortnightly eJournal");
  appendIdentityText(aside,"ISSN "+ISSN);
  appendIdentityLink(aside,"Primary:",PRIMARY);
  appendIdentityLink(aside,"GitHub mirror:",GITHUB);
  appendIdentityLink(aside,"Digital Research Archive:",RESEARCH);
  appendIdentityLink(aside,"GitHub research network:",GH_ORG);
  aside.querySelectorAll("a").forEach(a=>{a.style.color="#174c7d";a.style.textDecoration="underline";a.style.textUnderlineOffset="2px";});
  document.body.appendChild(aside);
}
function escapeHTML(s){return String(s==null?"":s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function download(name,data,type){const b=data instanceof Blob?data:new Blob([data],{type:type||"application/octet-stream"});const a=document.createElement("a");a.href=URL.createObjectURL(b);a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1200);}
function readText(file){return file.text?file.text():new Response(file).text();}
function devaNum(s){return String(s||"").replace(/[०-९]/g,d=>"०१२३४५६७८९".indexOf(d));}
function toDeva(n){return String(n).replace(/[0-9]/g,d=>"०१२३४५६७८९"[+d]);}
function baseHead(){return{mode:hostMode(),primary:PRIMARY,github:GITHUB,research:RESEARCH,issn:ISSN};}
function init(){initLowData();initScholarlyIdentity();}
g.VidehaCore={PRIMARY,GITHUB,RESEARCH,GH_ORG,ISSN,GH_ROOT,hostMode,resolveSearchUrl,canonicalGitHubUrl,toolUrl,isHistorical,lowData,setLowData,escapeHTML,download,readText,devaNum,toDeva,baseHead,initScholarlyIdentity};
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})(window);
