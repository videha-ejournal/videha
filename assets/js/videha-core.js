(function(g){"use strict";
const PRIMARY="https://www.videha.co.in/", GITHUB="https://videha-ejournal.github.io/videha/";
const GH_PATH="/videha/";
function hostMode(){const h=location.hostname.toLowerCase();if(h.endsWith("github.io"))return"github";if(h==="www.videha.co.in"||h==="videha.co.in")return"primary";return"local"}
function stripKnownPath(path){path=String(path||"").replace(/^https?:\/\/[^/]+/i,"");path=path.split(/[?#]/)[0];if(path.startsWith(GH_PATH))path=path.slice(GH_PATH.length);else path=path.replace(/^\/+/,"");return path}
function isHistorical(u){return /(?:^|\/)search-documents\//i.test(String(u||""))}
function isExternal(u){return /^(?:mailto:|tel:|javascript:|data:|blob:|#)/i.test(String(u||""))||(/^https?:\/\//i.test(String(u||""))&&!/(?:videha\.co\.in|videha-ejournal\.github\.io)/i.test(String(u||"")))}
function resolveSearchUrl(u){u=String(u||"").trim();if(!u)return u;if(isExternal(u))return u;let suffix="";const sm=u.match(/([?#].*)$/);if(sm)suffix=sm[1];let p=stripKnownPath(u);if(isHistorical(p))return GITHUB+p.replace(/^\/+/,"")+suffix;const mode=hostMode();if(mode==="github")return GITHUB+p.replace(/^\/+/,"")+suffix;if(mode==="primary")return PRIMARY+p.replace(/^\/+/,"")+suffix;return u}
function toolUrl(file,heavy){file=String(file||"").replace(/^\/+/,"");if(heavy&&hostMode()==="primary")return GITHUB+file;return resolveSearchUrl(file)}
function lowData(){try{return localStorage.getItem("videha.lowData")==="1"}catch(e){return false}}
function setLowData(v){try{localStorage.setItem("videha.lowData",v?"1":"0")}catch(e){}document.documentElement.classList.toggle("vds-low-data",!!v);g.dispatchEvent(new CustomEvent("videha:lowdata",{detail:{enabled:!!v}}))}
function initLowData(){setLowData(lowData());document.querySelectorAll("[data-vds-lowdata]").forEach(b=>{b.setAttribute("aria-pressed",lowData()?"true":"false");b.addEventListener("click",()=>{const n=!lowData();setLowData(n);b.setAttribute("aria-pressed",n?"true":"false");b.textContent=n?"हल्का मोड: चालू · Low Data: ON":"हल्का मोड · Low Data"})})}
function escapeHTML(s){return String(s==null?"":s).replace(/[&<>\"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'\"':"&quot;","'":"&#39;"}[c]))}
function download(name,data,type){const b=data instanceof Blob?data:new Blob([data],{type:type||"application/octet-stream"});const a=document.createElement("a");a.href=URL.createObjectURL(b);a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1200)}
function readText(file){return file.text?file.text():new Response(file).text()}
function devaNum(s){return String(s||"").replace(/[०-९]/g,d=>"०१२३४५६७८९".indexOf(d))}
function toDeva(n){return String(n).replace(/[0-9]/g,d=>"०१२३४५६७८९"[+d])}
function baseHead(){return {mode:hostMode(),primary:PRIMARY,github:GITHUB}}
g.VidehaCore={PRIMARY,GITHUB,hostMode,resolveSearchUrl,toolUrl,isHistorical,lowData,setLowData,escapeHTML,download,readText,devaNum,toDeva,baseHead};
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",initLowData);else initLowData();
})(window);