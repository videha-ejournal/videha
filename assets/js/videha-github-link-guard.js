(function(g){
"use strict";
const GH_ROOT="https://videha-ejournal.github.io/";
const GH_MAIN=GH_ROOT+"videha/";
const PROJECTS=new Set(["videha-quiz","videha-sadeha","videha-ejournal"]);
const SAFE_SCHEME=/^(?:mailto:|tel:|javascript:|data:|blob:|#)/i;
const ALLOWED_ABS_HOST=/^(?:videha-ejournal\.github\.io|(?:www\.)?videha\.co\.in)$/i;

function decodePath(path){
  try{return decodeURIComponent(String(path||""));}catch(e){return String(path||"");}
}
function encodePath(path){
  return String(path||"").split("/").map((p,i)=>i===0?"":encodeURIComponent(p)).join("/")
    .replace(/%3A/gi,":").replace(/%40/gi,"@");
}
function canonicalize(raw, base){
  raw=String(raw||"").trim();
  if(!raw||SAFE_SCHEME.test(raw))return "";
  const explicitAbs=/^https?:\/\//i.test(raw);
  let u;
  try{u=new URL(raw,base||((typeof document!=="undefined"&&document.baseURI)||GH_MAIN));}
  catch(e){return "";}
  if(explicitAbs&&!ALLOWED_ABS_HOST.test(u.hostname))return "";

  const decoded=decodePath(u.pathname).replace(/\\/g,"/");
  const parts=decoded.split("/").filter(Boolean);
  const low=parts.map(x=>x.toLowerCase());

  for(const project of PROJECTS){
    const at=low.indexOf(project);
    if(at>=0){
      const rest=parts.slice(at);
      return GH_ROOT+rest.map(encodeURIComponent).join("/")+u.search+u.hash;
    }
  }

  const sd=low.indexOf("search-documents");
  if(sd>=0){
    const rest=parts.slice(sd);
    return GH_MAIN+rest.map(encodeURIComponent).join("/")+u.search+u.hash;
  }
  return "";
}

function fixAnchor(a){
  if(!a||!a.getAttribute)return;
  const raw=a.getAttribute("href");
  if(!raw)return;
  const c=canonicalize(raw,(typeof document!=="undefined"?document.baseURI:undefined));
  if(c&&a.href!==c)a.setAttribute("href",c);
}
function scan(root){
  if(!root||typeof root.querySelectorAll!=="function")return;
  if(root.matches&&root.matches("a[href]"))fixAnchor(root);
  root.querySelectorAll("a[href]").forEach(fixAnchor);
}
function nearestAnchor(node){
  if(!node)return null;
  if(node.closest)return node.closest("a[href]");
  return null;
}
function install(){
  scan(document);
  if(typeof MutationObserver!=="undefined"){
    const mo=new MutationObserver(ms=>{
      for(const m of ms){
        if(m.type==="attributes"&&m.target&&m.target.matches&&m.target.matches("a[href]"))fixAnchor(m.target);
        for(const n of m.addedNodes||[])if(n.nodeType===1)scan(n);
      }
    });
    mo.observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:["href"]});
  }
  ["pointerdown","mousedown","touchstart","click","auxclick","contextmenu"].forEach(type=>{
    document.addEventListener(type,e=>fixAnchor(nearestAnchor(e.target)),true);
  });
}
g.VidehaGitHubLinkGuard={canonicalize,fixAnchor,scan};
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});
else install();
})(window);
