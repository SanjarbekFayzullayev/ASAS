const D = ASAS_DATA;
Chart.defaults.font.family = "Inter, Segoe UI, sans-serif";
Chart.defaults.color = '#64748B';
function chCursor(e,el){if(e.native&&e.native.target)e.native.target.style.cursor=el.length?'pointer':'default';}
// Hududlar reytingi — GORIZONTAL (o'qilishi oson) — bosilsa hudud tafsiloti
new Chart(document.getElementById('barRegion'), {
  type:'bar',
  data:{labels:D.region_totals.map(x=>x.region),
        datasets:[{data:D.region_totals.map(x=>x.total),backgroundColor:'#7C3AED',borderRadius:6,barThickness:16}]},
  options:{indexAxis:'y',plugins:{legend:{display:false}},onHover:chCursor,
    onClick:(e,el)=>{if(el.length)showRegion(D.region_totals[el[0].index].region);},
    scales:{y:{ticks:{font:{size:12}},grid:{display:false}},x:{grid:{color:'#EEF1F6'}}}}
});
// Oylik dinamika — nuqta bosilsa shu oy ko'rsatkichi
new Chart(document.getElementById('lineMonthly'), {
  type:'line',
  data:{labels:D.monthly.labels,
        datasets:[{data:D.monthly.counts,borderColor:'#7C3AED',backgroundColor:'rgba(124,58,237,.14)',fill:true,tension:.35,pointRadius:0,pointHitRadius:14,borderWidth:2.5}]},
  options:{plugins:{legend:{display:false}},onHover:chCursor,
    onClick:(e,el)=>{if(el.length){const i=el[0].index;showMonth(D.monthly.labels[i],D.monthly.counts[i]);}},
    scales:{x:{ticks:{maxRotation:90,minRotation:50,font:{size:9}},grid:{display:false}},y:{grid:{color:'#EEF1F6'}}}}
});
// Mavsumiy taqsimot — doiraviy — bo'lak bosilsa mavsum tafsiloti
const st=D.season_totals;
new Chart(document.getElementById('donutSeason'), {
  type:'doughnut',
  data:{labels:Object.keys(st),
        datasets:[{data:Object.values(st),backgroundColor:['#22C55E','#EF4444','#F59E0B','#3B82F6'],borderWidth:2,borderColor:'#fff'}]},
  options:{cutout:'60%',onHover:chCursor,
    onClick:(e,el)=>{if(el.length)showSeason(Object.keys(st)[el[0].index]);},
    plugins:{legend:{position:'bottom',labels:{padding:14,font:{size:12}}}}}
});

// ===== Karta tafsilotlari (bosilganda) =====
const LVLP={Yuqori:'p-dismiss',"O'rta":'p-warn',Past:'p-sent'};
function bars(rows){ // rows: [{name,val,pct,color,tag,tagcls}]
  return rows.map(r=>`<div class="fc-row">
    <div class="fc-name" title="${r.name}">${r.name}</div>
    <div class="fc-track"><div class="fc-fill" style="width:${r.pct}%;background:${r.color||'#7C3AED'}"></div></div>
    <div class="fc-val">${r.val}</div>
    ${r.tag?`<span class="pill ${r.tagcls||''}">${r.tag}</span>`:'<span></span>'}
  </div>`).join('');
}
function openD(title,body){
  document.getElementById('dTitle').textContent=title;
  document.getElementById('dBody').innerHTML=body;
  document.getElementById('detailModal').classList.add('show');
}
function regionDetailBody(r){
  const tr=D.trend[r]||0;
  const fc=D.forecast.find(f=>f.region===r)||{risk:0,level:'Past'};
  const rt=D.region_totals.find(x=>x.region===r)||{total:0};
  const seas=D.seasons.map(s=>({name:s,val:D.heat[r][s],pct:0}));
  const smx=Math.max(...seas.map(s=>s.val))||1; seas.forEach(s=>s.pct=Math.round(s.val/smx*100));
  return `<div class="dstat"><span>Jami jinoyatlar (24 oy)</span><b>${rt.total}</b></div>
    <div class="dstat"><span>Trend (oxirgi davr)</span><b style="color:${tr>0?'#DC2626':'#16A34A'}">${tr>0?'+':''}${tr}%</b></div>
    <div class="dstat"><span>Kelgusi mavsum xavfi</span><b><span class="pill ${LVLP[fc.level]}">${fc.level} (${fc.risk}%)</span></b></div>
    <p class="dmut" style="margin-top:14px">Mavsumiy o\'rtacha (jinoyat/oy):</p>`+bars(seas);
}
function showRegion(r){openD('Hudud: '+r, regionDetailBody(r));}
function showSeason(s){
  const rows=D.region_totals.map(x=>({region:x.region,val:D.heat[x.region][s]})).sort((a,b)=>b.val-a.val);
  const mx=rows[0]?rows[0].val:1;
  openD('Mavsum: '+s, `<p class="dmut"><b>${s}</b> mavsumida hududlar bo\'yicha o\'rtacha jinoyat (oyiga):</p>`+
    bars(rows.map(r=>({name:r.region,val:r.val,pct:Math.round(r.val/(mx||1)*100),color:'#7C3AED'}))));
}
function showMonth(label,count){
  openD('Oylik ko\'rsatkich', `<div class="dstat"><span>Davr</span><b>${label}</b></div>
    <div class="dstat"><span>Jami jinoyatlar (barcha hududlar)</span><b>${count}</b></div>
    <p class="dmut" style="margin-top:12px">Bu — shu oyda butun mamlakat bo\'yicha qayd etilgan jinoyatlar yig\'indisi.</p>`);
}
function showDetail(kind){
  let title='', body='';
  if(kind==='total'){
    title='Jami jinoyatlar — hududlar bo\'yicha';
    const mx=D.region_totals[0]?D.region_totals[0].total:1;
    body=`<p class="dmut">So\'nggi 24 oyda jami <b>${D.grand_total}</b> ta qayd. Hududlar ulushi:</p>`+
      bars(D.region_totals.map(x=>({name:x.region,val:x.total,pct:Math.round(x.total/mx*100),color:'#7C3AED'})));
  } else if(kind==='top'){
    const r=D.top_region; const tr=D.trend[r]||0;
    const fc=D.forecast.find(f=>f.region===r)||{risk:0,level:'Past'};
    title='Eng xavfli hudud — '+r;
    const seas=D.seasons.map(s=>({name:s,val:D.heat[r][s],pct:0}));
    const smx=Math.max(...seas.map(s=>s.val))||1; seas.forEach(s=>s.pct=Math.round(s.val/smx*100));
    body=`<p class="dmut">Bu hudud so\'nggi davrda eng ko\'p jinoyat qayd etilgan hudud.</p>
      <div class="dstat"><span>Trend (oxirgi davr)</span><b style="color:${tr>0?'#DC2626':'#16A34A'}">${tr>0?'+':''}${tr}%</b></div>
      <div class="dstat"><span>Kelgusi mavsum xavfi</span><b><span class="pill ${LVLP[fc.level]}">${fc.level} (${fc.risk}%)</span></b></div>
      <p class="dmut" style="margin-top:14px">Mavsumiy o\'rtacha (jinoyat/oy):</p>`+bars(seas);
  } else if(kind==='rising'){
    title='Xavfi o\'sayotgan hududlar';
    if(!D.rising.length){body='<p class="dmut">Hozircha sezilarli o\'sish kuzatilmagan.</p>';}
    else{const mx=D.rising[0].pct||1;
      body=`<p class="dmut">Quyidagi hududlarda jinoyatlar oxirgi davrda <b>oshgan</b> — diqqat talab:</p>`+
        bars(D.rising.map(x=>({name:x.region,val:'+'+x.pct+'%',pct:Math.min(100,Math.round(x.pct/mx*100)),color:'#F59E0B',tag:'o\'smoqda',tagcls:'p-warn'})));}
  } else if(kind==='season'){
    title='Kelgusi mavsum — '+D.next_season+' prognozi';
    const top=D.forecast.slice(0,8);
    body=`<p class="dmut"><b>${D.next_season}</b> mavsumida eng yuqori xavfli hududlar (prognoz):</p>`+
      bars(top.map(f=>({name:f.region,val:f.risk+'%',pct:f.risk,
        color:f.level==='Yuqori'?'#DC2626':(f.level==="O'rta"?'#F59E0B':'#16A34A'),
        tag:f.level,tagcls:LVLP[f.level]})));
  }
  document.getElementById('dTitle').textContent=title;
  document.getElementById('dBody').innerHTML=body;
  document.getElementById('detailModal').classList.add('show');
}
function closeDetail(){document.getElementById('detailModal').classList.remove('show');}
document.getElementById('detailModal').addEventListener('click',e=>{if(e.target.id==='detailModal')closeDetail();});
