let lastSig=''; let allEvents=[]; let curFilter='ai';
const IC_BADGE='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M14 9h4M14 13h4M6 16h12"/></svg>';
const IC_CPU='<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/></svg>';
const IC_CHK='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px"><polyline points="20 6 9 17 4 12"/></svg>';
function bar(score, rec){const c=rec?'linear-gradient(90deg,#22C55E,#16A34A)':'linear-gradient(90deg,#FBBF24,#D97706)';
  return `<div class="meter"><div class="bar" style="width:${Math.round(score*100)}%;background:${c}"></div></div>`;}
function card(e){
  const face = e.has_face ? `<img class="face" src="/face/${e.id}" title="FACEID">` : '';
  const pill = {new:'p-new',sent:'p-sent',dismiss:'p-dismiss'}[e.status]||'p-new';
  const pillTxt = {new:'kutilmoqda',sent:'AI tasdiqladi',dismiss:'AI rad etdi'}[e.status]||e.status;
  const recTag = e.ai_recommend ? `<span class="rectag">${IC_CPU} AI tavsiya qildi</span>`
                                : '<span class="rectag low">past ishonch</span>';
  let acts='';
  if(e.status==='new'){acts=`<div class="acts">
     <button class="btn sm" onclick="act('/events/${e.id}/send','Tasdiqlandi')">${IC_CHK} Tasdiqlash</button>
     <button class="btn sm ghost" onclick="act('/events/${e.id}/dismiss','Rad etildi')">Rad etish</button></div>`;}
  return `<div class="ev"><div class="imgwrap"><img class="snap" src="/snap/${e.id}">${face}</div>
    <div class="b"><div class="top"><span class="cam">${e.camera_name}</span><span class="tm">${e.ts}</span></div>
    <div class="rsn">${e.reason||''}</div>
    <div class="scorerow"><span>AI ishonch</span><b>${Math.round(e.ai_score*100)}% ${e.ai_recommend?'✓':''}</b></div>
    ${bar(e.ai_score,e.ai_recommend)}
    ${recTag}
    <div class="idrow">${IC_BADGE} ${e.identity}</div>
    <span class="pill ${pill}">${pillTxt}</span>${acts}</div></div>`;
}
function applyFilter(evs){
  if(curFilter==='ai') return evs.filter(e=>e.ai_recommend);
  if(curFilter==='new') return evs.filter(e=>e.status==='new');
  if(curFilter==='sent') return evs.filter(e=>e.status==='sent');
  return evs;
}
function render(){
  const evs=applyFilter(allEvents);
  const sig=curFilter+'|'+JSON.stringify(evs.map(e=>[e.id,e.status]));
  if(sig===lastSig) return; lastSig=sig;
  const empt={ai:'AI hozircha yuqori ishonchli (tavsiya qilingan) hodisa topmadi.',
              new:'Kutilayotgan hodisa yo\'q.',sent:'Tasdiqlangan hodisa yo\'q.',
              all:'Hali shubhali hodisa yo\'q.<br>Kamera qo\'shing — kuzatuv avtomatik boshlanadi.'}[curFilter];
  document.getElementById('grid').innerHTML = evs.length ? evs.map(card).join('') : `<div class="empty">${empt}</div>`;
}
function setFilter(f,btn){curFilter=f;document.querySelectorAll('.ftab').forEach(b=>b.classList.remove('active'));btn.classList.add('active');render();}
async function refresh(){
  const s=await (await fetch('/api/stats')).json();
  document.getElementById('s-cam').textContent=s.active_cameras;
  document.getElementById('s-total').textContent=s.total;
  document.getElementById('s-rec2').textContent=s.recommended;
  document.getElementById('s-sent').textContent=s.sent;
  document.getElementById('rec').textContent=s.recommended;
  const auto=s.auto_send;
  document.getElementById('autostate').textContent=auto?'YONIQ':"O'CHIQ";
  const ab=document.getElementById('autobtn');
  ab.style.color=auto?'#16A34A':''; ab.style.borderColor=auto?'#16A34A':'';
  const d=await (await fetch('/api/events')).json();
  allEvents=d.events; render();
}
async function act(u,msg){await post(u);toast(msg);lastSig='';refresh();}
async function sendRec(){await post('/events/send_recommended');toast('AI tavsiya qilganlar tasdiqlandi');lastSig='';refresh();}
async function toggleAuto(){await post('/settings/autosend');toast('Avtomatik tasdiqlash holati o\'zgardi');refresh();}
refresh(); setInterval(refresh, 4000);
