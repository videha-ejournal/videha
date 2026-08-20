(function(){
"use strict";const $=id=>document.getElementById(id),inp=$('pubZip'),run=$('pubRun'),st=$('pubStatus'),rep=$('pubReport'),bar=document.querySelector('#pubProg span'),downloads=$('pubDownloads');let bytes=null;
const enc=fflate.strToU8,dec=fflate.strFromU8;
function norm(p){p=p.replace(/\\/g,'/').replace(/^\.\//,'');const parts=p.split('/');if(parts.length>1&&parts[0]&&!/\./.test(parts[0])&&parts.slice(1).some(x=>/\.(?:htm|html)$/i.test(x)))return parts.slice(1).join('/');return p}
function findKey(files,re){return Object.keys(files).find(x=>re.test(x))}
function currentIssue(files){const k=findKey(files,/(^|\/)index\.htm$/i);if(!k)return null;const t=dec(files[k]);let m=t.match(/issue-number-square[^>]*>\s*([०-९0-9]{1,4})/i)||t.match(/विदेह\s+अंक\s*([०-९0-9]{1,4})/i);return m?parseInt(VidehaCore.devaNum(m[1]),10):null}
function histMax(files){let max=0;Object.keys(files).forEach(k=>{const m=k.match(/search-documents\/videha-(\d+)\.html$/i);if(m)max=Math.max(max,+m[1])});return max}
function has(files,re){return !!findKey(files,re)}
function blobLink(label,name,u8){const a=document.createElement('a');a.className='vds-btn primary';a.textContent=label;a.download=name;a.href=URL.createObjectURL(new Blob([u8],{type:'application/zip'}));a.addEventListener('click',()=>setTimeout(()=>URL.revokeObjectURL(a.href),5000),{once:true});downloads.appendChild(a)}
function checklist(cur,hist,checks){return `VIDEHA PUBLISHER CHECKLIST\nGenerated: ${new Date().toISOString()}\nCurrent issue detected: ${cur??'?'}\nHistorical generated corpus through: ${hist??'?'}\nExpected relation current = historical + 1: ${cur&&hist&&cur===hist+1?'PASS':'CHECK'}\n\nSearch URL rule\n- ordinary/current/static result => current host\n- search-documents historical result => https://videha-ejournal.github.io/videha/search-documents/...\n\nChecks\n${checks.map(c=>`${c.ok?'PASS':'CHECK'}  ${c.name}${c.note?' — '+c.note:''}`).join('\n')}\n\nAfter GitHub upload/push, allow the included Build Videha Universal Search Action to regenerate Pagefind.\nAfter server upload, run the existing Videha RSS updater if this issue is ready for publication.\n`}
function patchJson(files,path,obj){files[path]=enc(JSON.stringify(obj,null,2))}
inp.onchange=async()=>{const f=inp.files[0];if(!f)return;bytes=new Uint8Array(await f.arrayBuffer());const mb=f.size/1048576;st.textContent=`${f.name} · ${mb.toFixed(1)} MB ready${mb>150?' · Large full-corpus ZIP: desktop/RAM-heavy; routine issue updates should use the smaller source/update ZIP and let GitHub Actions rebuild Pagefind.':''}`;run.disabled=false;downloads.innerHTML=''};
run.onclick=()=>{if(!bytes)return;run.disabled=true;downloads.innerHTML='';bar.style.width='3%';st.textContent='ZIP खोलल जा रहल अछि…';setTimeout(()=>{try{
 let raw=fflate.unzipSync(bytes),files={};for(const [k,v] of Object.entries(raw))files[norm(k)]=v;bar.style.width='28%';const cur=currentIssue(files),hist=histMax(files);
 const checks=[
  {name:'index.htm',ok:has(files,/(^|\/)index\.htm$/i)},
  {name:'Universal Search',ok:has(files,/(^|\/)videha-universal-search\.htm$/i)},
  {name:'Site Auditor / Editor',ok:has(files,/(^|\/)videha-site-auditor\.htm$/i)||has(files,/(^|\/)videha-editor-studio\.html$/i)},
  {name:'sitemap.xml',ok:has(files,/(^|\/)sitemap\.xml$/i)},
  {name:'RSS XML',ok:has(files,/(^|\/)videha-rss\.xml$/i),note:'existing RSS updater may regenerate after upload'},
  {name:'Pagefind full index',ok:has(files,/^pagefind\//i),note:'required in GitHub package, intentionally absent from SERVER'},
  {name:'Historical search-documents',ok:hist>0,note:hist?`through ${hist}`:'not found'},
  {name:'Issue continuity',ok:!!(cur&&hist&&cur===hist+1),note:cur&&hist?`${cur} vs ${hist}`:'unable to compare'},
  {name:'Digital Archive core',ok:has(files,/(^|\/)assets\/js\/videha-core\.js$/i)},
 ];
 const server={},github={};let dropped=0;for(const [k,v] of Object.entries(files)){if(!k||k.endsWith('/'))continue;github[k]=v;if(/^(?:pagefind|search-documents|\.github|\.git|tools)\//i.test(k)){dropped+=v.length;continue}server[k]=v}
 const dep={generated:new Date().toISOString(),currentIssue:cur,historicalThrough:hist,searchRule:{ordinary:'current host',historical:'https://videha-ejournal.github.io/videha/search-documents/'},serverExcluded:['pagefind/','search-documents/','.github/','.git/','tools/']};
 patchJson(server,'data/publisher-output.json',dep);patchJson(github,'data/publisher-output.json',dep);
 // Keep archive manifest currentIssue synchronized when present; do not fabricate archive entries.
 for(const fset of [server,github]){if(fset['data/videha-archive-manifest.json']){try{const j=JSON.parse(dec(fset['data/videha-archive-manifest.json']));j.currentIssue=cur;j.archiveMaxVideha=hist;fset['data/videha-archive-manifest.json']=enc(JSON.stringify(j))}catch(e){}}}
 const note=checklist(cur,hist,checks);server['VIDEHA-PUBLISH-CHECKLIST.txt']=enc(note);github['VIDEHA-PUBLISH-CHECKLIST.txt']=enc(note);
 bar.style.width='52%';st.textContent='SERVER ZIP बनि रहल अछि…';const sz=fflate.zipSync(server,{level:6});bar.style.width='76%';st.textContent='GITHUB ZIP बनि रहल अछि…';const gz=fflate.zipSync(github,{level:6});bar.style.width='100%';
 rep.innerHTML=`<p><strong>Current issue:</strong> ${cur||'?'} · <strong>Historical through:</strong> ${hist||'?'}</p><p><strong>Continuity:</strong> ${cur&&hist&&cur===hist+1?'<span class="vds-good">PASS</span>':'<span class="vds-warn">CHECK</span>'}</p><p>SERVER सँ ${(dropped/1048576).toFixed(1)} MB uncompressed heavy generated material हटाओल गेल।</p><table class="vds-table"><tbody>${checks.map(c=>`<tr><td class="${c.ok?'vds-good':'vds-warn'}">${c.ok?'PASS':'CHECK'}</td><td>${VidehaCore.escapeHTML(c.name)}</td><td>${VidehaCore.escapeHTML(c.note||'')}</td></tr>`).join('')}</tbody></table>`;
 blobLink('VIDEHA_SERVER ZIP',`VIDEHA_SERVER_${cur||'build'}.zip`,sz);blobLink('VIDEHA_GITHUB ZIP',`VIDEHA_GITHUB_${cur||'build'}.zip`,gz);st.textContent='दुनू deployment package तैयार। नीचे अलग-अलग download करू।'
 }catch(e){st.textContent='Publisher error: '+e.message;console.error(e)}finally{run.disabled=false}},30)};
})();
