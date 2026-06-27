function tick(){const d=new Date();document.getElementById('clock').textContent=
   d.toLocaleDateString('ru-RU')+'  '+d.toLocaleTimeString('ru-RU');}
 setInterval(tick,1000);tick();
 function toast(m){const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');
   setTimeout(()=>t.classList.remove('show'),2500);}
 async function post(u){await fetch(u,{method:'POST'});}
