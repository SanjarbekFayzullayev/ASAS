let history=[];
const EX=["Park hududida shaxs yerga paket ko'mdi","Tintuvda o'qotar qurol topildi","Telegram kanalda narko-reklama va havola bor","Toshkentda kuryer shubhali paket tashiyapti"];
function chips(){const c=document.getElementById('chips');EX.forEach(x=>{const b=document.createElement('span');b.className='chip';b.textContent=x.length>30?x.slice(0,30)+'…':x;b.title=x;b.onclick=()=>{document.getElementById('msg').value=x;send();};c.appendChild(b);});}
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function add(role,html){const log=document.getElementById('chatlog');const d=document.createElement('div');const me=role==='user';
  d.style.cssText='max-width:82%;padding:12px 15px;border-radius:15px;font-size:14px;line-height:1.55;white-space:pre-wrap;'+(me?'align-self:flex-end;background:linear-gradient(135deg,#6366F1,#9333EA);color:#fff;border-bottom-right-radius:5px':'align-self:flex-start;background:var(--soft);color:var(--txt);border-bottom-left-radius:5px');
  d.innerHTML=html;log.appendChild(d);log.scrollTop=log.scrollHeight;return d;}
async function send(){
  const i=document.getElementById('msg');const m=i.value.trim();if(!m)return;i.value='';
  add('user',esc(m));history.push({role:'user',content:m});
  const t=add('ai','<span style="color:var(--mut)">yozmoqda…</span>');
  try{
    const r=await fetch('/assistant/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m,history:history})});
    const d=await r.json();
    let html=esc(d.reply);
    if(d.mode==='rule')html+='<div style="color:var(--mut);font-size:11px;margin-top:8px">(asosiy rejim — to\'liq AI suhbat uchun Ollama yuklanmoqda)</div>';
    t.innerHTML=html;history.push({role:'assistant',content:d.reply});
  }catch(e){t.innerHTML='Xatolik yuz berdi.';}
  document.getElementById('chatlog').scrollTop=1e9;
}
chips();
add('ai','Assalomu alaykum! Men ASAS AI yordamchisiman. Operativ vaziyatni yozing — local ma\'lumotlar asosida xavfni baholab, tavsiyalar beraman.');
