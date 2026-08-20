(function(){
"use strict";
const $=id=>document.getElementById(id), inp=$('docFiles'), out=$('docReport'), status=$('docStatus'), merged=$('docMerged'), nav=$('docNav');
let docs=[], chapterBlocks=[]; const W='http://schemas.openxmlformats.org/wordprocessingml/2006/main';
const escXml=s=>String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
function val(el){return el?(el.getAttributeNS(W,'val')||el.getAttribute('w:val')||el.getAttribute('val')||''):''}
function paraRecords(xml){
  const d=new DOMParser().parseFromString(xml,'application/xml');
  return [...d.getElementsByTagNameNS('*','p')].map((p,idx)=>{
    const text=[...p.getElementsByTagNameNS('*','t')].map(t=>t.textContent).join('');
    const ps=p.getElementsByTagNameNS('*','pStyle')[0], style=val(ps)||'';
    const heading=/^heading\s*[1-9]/i.test(style)||/^(?:अध्याय|Chapter|PART|खण्ड|खंड)\b/i.test(text.trim());
    const hm=style.match(/heading\s*([1-9])/i); return {idx,text,style,heading,level:hm?+hm[1]:(heading?1:0)};
  }).filter(p=>p.text.trim());
}
function textStats(paras){const text=paras.map(p=>p.text).join('\n\n');return {text,words:(text.match(/[\p{L}\p{N}]+/gu)||[]).length,chars:text.length}}
function exactDuplicates(paras){const m=new Map();paras.forEach((p,i)=>{const k=p.text.toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').replace(/\s+/g,' ').trim();if(k.length>40){const a=m.get(k)||[];a.push(i+1);m.set(k,a)}});return [...m.entries()].filter(([,a])=>a.length>1).map(([text,at])=>({text:text.slice(0,130),at}))}
function countNotes(z,path,tag){if(!z[path])return 0;const x=fflate.strFromU8(z[path]);return (x.match(new RegExp('<w:'+tag+'\\b','g'))||[]).length}
async function readFile(f){
 const ext=(f.name.split('.').pop()||'').toLowerCase();
 if(ext==='docx'){
   const bytes=new Uint8Array(await f.arrayBuffer()), z=fflate.unzipSync(bytes), key=Object.keys(z).find(k=>/word\/document\.xml$/i.test(k)); if(!key)throw Error('word/document.xml नहि भेटल');
   const xml=fflate.strFromU8(z[key]), paras=paraRecords(xml), st=textStats(paras), styles={};paras.forEach(p=>styles[p.style||'(Normal/implicit)']=(styles[p.style||'(Normal/implicit)']||0)+1);
   const docPr=(xml.match(/<(?:wp:)?docPr\b/g)||[]).length, alt=(xml.match(/<(?:wp:)?docPr\b[^>]*(?:descr|title)=["'][^"']+["']/g)||[]).length;
   return {name:f.name,ext,paras,xml,zip:z,docKey:key,...st,tables:(xml.match(/<w:tbl\b/g)||[]).length,images:Object.keys(z).filter(k=>/^word\/media\//i.test(k)).length,footnotes:Math.max(0,countNotes(z,'word/footnotes.xml','footnote')-2),endnotes:Math.max(0,countNotes(z,'word/endnotes.xml','endnote')-2),hyperlinks:(xml.match(/<w:hyperlink\b/g)||[]).length,superscripts:(xml.match(/w:vertAlign[^>]+w:val=["']superscript/gi)||[]).length,headings:paras.filter(p=>p.heading),duplicates:exactDuplicates(paras),styles,missingAlt:Math.max(0,docPr-alt)};
 }
 let raw=await f.text(), text=raw;
 if(ext==='html'||ext==='htm'){const d=new DOMParser().parseFromString(raw,'text/html');text=d.body.innerText||d.body.textContent||''}
 const pp=text.split(/\n\s*\n/).map((x,i)=>({idx:i,text:x.trim(),style:'',heading:/^(?:अध्याय|Chapter|PART|खण्ड|खंड)\b/i.test(x.trim()),level:1})).filter(x=>x.text), st=textStats(pp);
 return {name:f.name,ext,paras:pp,xml:raw,...st,tables:ext.match(/html?/) ? (raw.match(/<table\b/gi)||[]).length:0,images:ext.match(/html?/) ? (raw.match(/<img\b/gi)||[]).length:0,footnotes:0,endnotes:0,hyperlinks:ext.match(/html?/) ? (raw.match(/<a\b/gi)||[]).length:0,superscripts:ext.match(/html?/) ? (raw.match(/<sup\b/gi)||[]).length:0,headings:pp.filter(p=>p.heading),duplicates:exactDuplicates(pp),styles:{'(plain)':pp.length},missingAlt:0};
}
function rebuildMerged(){merged.value=docs.filter(d=>!d.error).map(d=>`===== ${d.name} =====\n\n${d.paras.map(p=>p.text).join('\n\n')}`).join('\n\n');buildChapters();renderNav()}
function moveDoc(i,delta){const j=i+delta;if(j<0||j>=docs.length)return;[docs[i],docs[j]]=[docs[j],docs[i]];renderReport();rebuildMerged()}
function renderReport(){
 const rows=docs.map((d,i)=>d.error?`<tr><td>${VidehaCore.escapeHTML(d.name)}</td><td colspan="10" class="vds-bad">${VidehaCore.escapeHTML(d.error)}</td></tr>`:`<tr><td><button class="vds-btn" data-move="${i},-1" aria-label="Move up">↑</button><button class="vds-btn" data-move="${i},1" aria-label="Move down">↓</button> ${VidehaCore.escapeHTML(d.name)}</td><td>${d.words}</td><td>${d.paras.length}</td><td>${d.headings.length}</td><td>${d.tables}</td><td>${d.images}</td><td>${d.footnotes+d.endnotes}</td><td>${d.superscripts}</td><td>${d.hyperlinks}</td><td>${d.duplicates.length}</td><td>${d.missingAlt}</td></tr>`).join('');
 out.innerHTML=`<table class="vds-table"><thead><tr><th>File / order</th><th>Words</th><th>Paras</th><th>Headings</th><th>Tables</th><th>Images</th><th>Notes</th><th>Sup</th><th>Links</th><th>Dup</th><th>Missing alt*</th></tr></thead><tbody>${rows}</tbody></table>`;
 out.querySelectorAll('[data-move]').forEach(b=>b.onclick=()=>{const [i,d]=b.dataset.move.split(',').map(Number);moveDoc(i,d)})
}
function buildChapters(){
 const lines=merged.value.split(/\n/), blocks=[];let cur={title:'आरम्भ · Beginning',lines:[]};
 for(const line of lines){if(/^(?:अध्याय|Chapter|PART|खण्ड|खंड)\b/i.test(line.trim())&&cur.lines.length){blocks.push(cur);cur={title:line.trim(),lines:[line]}}else cur.lines.push(line)}
 if(cur.lines.length)blocks.push(cur);chapterBlocks=blocks;
}
function renderNav(){
 const heads=[];docs.forEach((d,di)=>d.headings.forEach(h=>heads.push({doc:d.name,text:h.text,level:h.level||1}))); const shown=heads.slice(0,250);
 nav.innerHTML=`<p><strong>${heads.length} heading/chapter labels</strong></p><ol class="vds-list">${shown.map(h=>`<li style="margin-left:${Math.max(0,h.level-1)*12}px"><span class="vds-badge">${VidehaCore.escapeHTML(h.doc)}</span> ${VidehaCore.escapeHTML(h.text)}</li>`).join('')}</ol>${heads.length>shown.length?'<p>…</p>':''}`;
 $('chapterOrder').innerHTML=chapterBlocks.map((c,i)=>`<li><button class="vds-btn" data-cmove="${i},-1">↑</button><button class="vds-btn" data-cmove="${i},1">↓</button> ${VidehaCore.escapeHTML(c.title)}</li>`).join('');
 $('chapterOrder').querySelectorAll('[data-cmove]').forEach(b=>b.onclick=()=>{const [i,d]=b.dataset.cmove.split(',').map(Number),j=i+d;if(j<0||j>=chapterBlocks.length)return;[chapterBlocks[i],chapterBlocks[j]]=[chapterBlocks[j],chapterBlocks[i]];merged.value=chapterBlocks.map(x=>x.lines.join('\n')).join('\n');buildChapters();renderNav()})
}
function detailedAudit(){
 const req=$('requiredSections').value.split(/[,;\n]+/).map(s=>s.trim()).filter(Boolean), all=merged.value, missing=req.filter(x=>!all.toLocaleLowerCase().includes(x.toLocaleLowerCase()));
 const target=$('docTarget').value, paras=all.split(/\n\s*\n/).map(x=>x.trim()).filter(x=>x.length>30), untranslated=[];
 for(const p of paras){const lat=(p.match(/[A-Za-z]/g)||[]).length,dev=(p.match(/[\u0900-\u097f]/g)||[]).length,total=lat+dev;if(total<20)continue;if(target==='mai'&&lat/total>.72)untranslated.push(p.slice(0,170));if(target==='en'&&dev/total>.72)untranslated.push(p.slice(0,170))}
 const bib=/\b(?:Bibliography|References)\b|(?:ग्रन्थसूची|ग्रंथसूची|सन्दर्भ|संदर्भ)/i.test(all);
 const styleTotals={};docs.filter(d=>!d.error).forEach(d=>Object.entries(d.styles||{}).forEach(([k,v])=>styleTotals[k]=(styleTotals[k]||0)+v));const styles=Object.entries(styleTotals).sort((a,b)=>b[1]-a[1]).slice(0,12);
 $('docDeep').innerHTML=`<h3>Deep audit</h3><p><strong>Required sections:</strong> ${missing.length?'<span class="vds-bad">missing '+missing.map(VidehaCore.escapeHTML).join(', ')+'</span>':'<span class="vds-good">all detected</span>'}</p><p><strong>Bibliography/reference heading:</strong> ${bib?'detected':'not detected'}</p><p><strong>Possible untranslated passages (${target==='mai'?'Latin-heavy':'Devanagari-heavy'}):</strong> ${untranslated.length}</p>${untranslated.length?'<details><summary>देखू</summary><ol>'+untranslated.slice(0,50).map(x=>`<li>${VidehaCore.escapeHTML(x)}</li>`).join('')+'</ol></details>':''}<p><strong>Paragraph style distribution:</strong> ${styles.map(([k,v])=>`<span class="vds-badge">${VidehaCore.escapeHTML(k)} ${v}</span>`).join(' ')}</p><p class="vds-help">Style distribution helps detect inconsistent formatting; semantic correctness still needs editorial review.</p>`;
}
function dedup(){const ps=merged.value.split(/\n\s*\n/),seen=new Set(),kept=[];for(const p of ps){const k=p.trim().toLowerCase().replace(/\s+/g,' ');if(!k||!seen.has(k)){kept.push(p);if(k)seen.add(k)}}merged.value=kept.join('\n\n');buildChapters();renderNav();status.textContent='Exact normalized duplicate paragraphs workspace copy मे हटाओल गेल; source files अपरिवर्तित।'}
function mergedParas(){return merged.value.split(/\n\s*\n/).map(x=>x.trim()).filter(Boolean)}
function minimalDocxFiles(documentXml){
 const E=fflate.strToU8;
 const contentTypes='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>';
 const packageRels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>';
 const docRels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>';
 const styles=`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="${W}"><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style><w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/></w:pPr><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style></w:styles>`;
 return {'[Content_Types].xml':E(contentTypes),'_rels/.rels':E(packageRels),'word/document.xml':E(documentXml),'word/styles.xml':E(styles),'word/_rels/document.xml.rels':E(docRels)}
}
function exportDocx(){
 const ps=mergedParas(), six=$('docSixNine').checked;let sect=six?'<w:sectPr><w:pgSz w:w="8640" w:h="12960"/><w:pgMar w:top="720" w:right="720" w:bottom="720" w:left="900" w:gutter="360"/></w:sectPr>':'<w:sectPr/>';
 const body=ps.map(t=>{const isH=/^(?:अध्याय|Chapter|PART|खण्ड|खंड)\b/i.test(t);return `<w:p>${isH?'<w:pPr><w:pStyle w:val="Heading1"/></w:pPr>':''}<w:r><w:t xml:space="preserve">${escXml(t)}</w:t></w:r></w:p>`}).join('')+sect;
 const xml=`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="${W}"><w:body>${body}</w:body></w:document>`;
 const z=minimalDocxFiles(xml);
 VidehaCore.download(six?'videha-merged-6x9.docx':'videha-merged.docx',fflate.zipSync(z,{level:6}),'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
 status.textContent='Text-safe merged DOCX export तैयार। Original images/complex formatting merge export मे जानि-बुझि कऽ नहि मिलाओल गेल।';
}
function exportHtml(printNow){const six=$('docSixNine').checked, ps=mergedParas(), body=ps.map(t=>/^(?:अध्याय|Chapter|PART|खण्ड|खंड)\b/i.test(t)?`<h2>${VidehaCore.escapeHTML(t)}</h2>`:`<p>${VidehaCore.escapeHTML(t).replace(/\n/g,'<br>')}</p>`).join(''), css=`body{font-family:Georgia,'Noto Serif Devanagari',serif;line-height:1.6;max-width:${six?'5.0in':'48rem'};margin:auto}p{text-align:justify} @page{size:${six?'6in 9in':'auto'};margin:${six?'.55in .55in .6in .72in':'18mm'}}`;const h=`<!doctype html><html lang="mai"><meta charset="utf-8"><title>VIDEHA merged document</title><style>${css}</style><body>${body}</body></html>`;if(!printNow){VidehaCore.download(six?'videha-merged-6x9.html':'videha-merged.html',h,'text/html;charset=utf-8');return}const w=window.open('','_blank');w.document.write(h+'<script>onload=()=>setTimeout(()=>print(),200)<\/script>');w.document.close()}
inp.onchange=async()=>{docs=[];out.innerHTML='';merged.value='';const fs=[...inp.files];if(!fs.length)return;status.textContent='दस्तावेज browser मे पढ़ल जा रहल अछि…';for(const f of fs){try{docs.push(await readFile(f))}catch(e){docs.push({name:f.name,error:e.message})}}renderReport();rebuildMerged();const ok=docs.filter(d=>!d.error);status.textContent=`${ok.length}/${docs.length} दस्तावेज local browser मे पढ़ल गेल। Manuscript server पर upload नहि भेल।`;detailedAudit()};
$('docAudit').onclick=detailedAudit;$('docDedup').onclick=dedup;$('docTxt').onclick=()=>VidehaCore.download('videha-merged-document.txt',merged.value,'text/plain;charset=utf-8');$('docHtml').onclick=()=>exportHtml(false);$('docDocx').onclick=exportDocx;$('docPdf').onclick=()=>exportHtml(true);
})();
