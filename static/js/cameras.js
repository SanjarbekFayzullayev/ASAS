let _map, _marker;
function openModal(){document.getElementById('modal').classList.add('show');setTimeout(initMap,150);}
function closeModal(){document.getElementById('modal').classList.remove('show');}
function initMap(){
  if(_map){_map.invalidateSize();return;}
  _map = L.map('map').setView([41.311,69.279],12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19}).addTo(_map);
  _marker = L.marker([41.311,69.279],{draggable:true}).addTo(_map);
  _marker.on('dragend',()=>setLoc(_marker.getLatLng()));
  _map.on('click',e=>{_marker.setLatLng(e.latlng);setLoc(e.latlng);});
}
function setLoc(ll){
  const c = ll.lat.toFixed(5)+', '+ll.lng.toFixed(5);
  const el=document.getElementById('loc'); el.value=c;
  fetch('https://nominatim.openstreetmap.org/reverse?format=json&lat='+ll.lat+'&lon='+ll.lng)
    .then(r=>r.json()).then(d=>{if(d&&d.display_name) el.value=d.display_name;}).catch(()=>{});
}
function locate(){
  if(!navigator.geolocation){toast('Brauzer geolokatsiyani qo\'llamaydi');return;}
  toast('Joylashuv aniqlanmoqda...');
  navigator.geolocation.getCurrentPosition(p=>{
    const ll={lat:p.coords.latitude,lng:p.coords.longitude};
    if(!_map) initMap();
    _map.setView([ll.lat,ll.lng],16); _marker.setLatLng([ll.lat,ll.lng]); setLoc(ll);
  }, ()=>toast('Joylashuv olinmadi — brauzerda ruxsat bering'));
}
setInterval(()=>{document.querySelectorAll('.camfeed img').forEach(i=>{if(!i.complete||i.naturalWidth===0){const s=i.src;i.src='';i.src=s;}});},8000);
