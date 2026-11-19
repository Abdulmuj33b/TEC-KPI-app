const API = "http://localhost:8000";
let token = sessionStorage.getItem("tec_training_token") || "";
let allRows = [], programmes = [], units = [];
const $ = id => document.getElementById(id);
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
async function api(path, options={}) {
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(API + path, {...options, headers});
  const data = await res.json().catch(()=>({}));
  if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
  return data;
}
function setStatus(text){$("connection-status").textContent=text;}
function total(rows,key){return rows.reduce((n,r)=>n+Number(r[key]||0),0);}
function filtered(){
  const from=$("from-date").value, to=$("to-date").value, p=$("programme").value, u=$("unit").value;
  return allRows.filter(r=>(!from||r.start_date>=from)&&(!to||r.start_date<=to)&&(!p||String(r.programme_id)===p)&&(!u||String(r.unit_id)===u));
}
function drawGrouped(target, items){
  const el=$(target);
  if(!items.length){el.className="bars empty";el.textContent="No matching records.";return;}
  const max=Math.max(1,...items.flatMap(x=>[x.enrolled,x.trained,x.completed]));
  el.className="bars";
  el.innerHTML=items.map(x=>`<div><div class="bar-row"><span>${esc(x.name)}</span><div class="bar-track multi"><div class="bar-fill" title="Enrolled: ${x.enrolled}" style="width:${100*x.enrolled/max}%;background:#27836b"></div></div><b>${x.enrolled}</b></div><div class="bar-row"><span></span><div class="bar-track multi"><div class="bar-fill" title="Trained: ${x.trained}" style="width:${100*x.trained/max}%;background:#e0a33b"></div></div><b>${x.trained}</b></div><div class="bar-row"><span></span><div class="bar-track multi"><div class="bar-fill" title="Completed: ${x.completed}" style="width:${100*x.completed/max}%;background:#4c78a8"></div></div><b>${x.completed}</b></div></div>`).join("")+'<div class="legend"><span>Enrolled</span><span class="trained">Trained</span><span class="completed">Completed</span></div>';
}
function drawBars(target, items){
  const el=$(target);
  if(!items.length){el.className="bars empty";el.textContent="No matching records.";return;}
  const max=Math.max(1,...items.map(x=>x.value));
  el.className="bars";
  el.innerHTML=items.map(x=>`<div class="bar-row"><span>${esc(x.name)}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(x.value?1:0,100*x.value/max)}%"></div></div><b>${x.value}</b></div>`).join("");
}
function render(){
  const rows=filtered(), enrolled=total(rows,"enrolled"), trained=total(rows,"trained"), completed=total(rows,"completed");
  $("k-activities").textContent=rows.length.toLocaleString();
  $("k-enrolled").textContent=enrolled.toLocaleString();
  $("k-trained").textContent=trained.toLocaleString();
  $("k-completed").textContent=completed.toLocaleString();
  $("k-rate").textContent=(enrolled?`${(100*completed/enrolled).toFixed(1)}%`:"0%");
  $("k-conversion").textContent=(trained?`${(100*completed/trained).toFixed(1)}%`:"0%");
  $("record-count").textContent=`${rows.length} matching activities`;
  const grouped=(key,name,base)=>base.map(b=>{const matching=rows.filter(r=>String(r[key]??"")===String(b.id));return {name:b.name,enrolled:total(matching,"enrolled"),trained:total(matching,"trained"),completed:total(matching,"completed")};});
  drawGrouped("programme-chart",grouped("programme_id","programme_name",programmes));
  drawGrouped("unit-chart",grouped("unit_id","unit_name",units));
  const months=new Map();
  rows.forEach(r=>{const m=String(r.start_date||"").slice(0,7);if(m)months.set(m,(months.get(m)||0)+1);});
  drawBars("monthly-chart",[...months].sort((a,b)=>a[0].localeCompare(b[0])).map(([name,value])=>({name,value})));
  const fm=new Map();
  rows.forEach(r=>(r.facilitators||[]).forEach(f=>{const n=typeof f==="string"?f:f.full_name||"Unknown";fm.set(n,(fm.get(n)||0)+1);}));
  drawBars("facilitator-chart",[...fm].map(([name,value])=>({name,value})).sort((a,b)=>b.value-a.value));
  $("records").innerHTML=rows.length?rows.map(r=>`<tr><td>${esc(r.course_name)}</td><td>${esc(r.programme_name)}</td><td>${esc(r.skill_name)}</td><td>${esc(r.unit_name||"Institutional")}</td><td>${esc(r.start_date)} – ${esc(r.end_date)}</td><td>${r.enrolled}</td><td>${r.trained}</td><td>${r.completed}</td><td><span class="pill">${esc(r.status)}</span></td><td>${esc((r.facilitators||[]).map(f=>typeof f==="string"?f:f.full_name).join(", "))}</td></tr>`).join(""):'<tr><td colspan="10">No matching activities.</td></tr>';
}
async function load(){
  [programmes,units,allRows]=await Promise.all([api("/api/training/programmes"),api("/api/units"),api("/api/training/activities?limit=500")]);
  $("programme").innerHTML='<option value="">All programmes</option>'+programmes.map(p=>`<option value="${p.id}">${esc(p.name)}</option>`).join("");
  $("unit").innerHTML='<option value="">All units</option>'+units.map(u=>`<option value="${u.id}">${esc(u.name)}</option>`).join("");
  render();setStatus(`Connected. Loaded ${allRows.length} training activities.`);
}
$("login-form").addEventListener("submit",async e=>{e.preventDefault();setStatus("Connecting…");try{const body=new URLSearchParams({username:$("email").value.trim(),password:$("password").value});const r=await fetch(API+"/api/auth/login",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Login failed");token=d.access_token;sessionStorage.setItem("tec_training_token",token);$("password").value="";await load();}catch(err){setStatus(err.message);}});
$("disconnect").addEventListener("click",()=>{token="";sessionStorage.removeItem("tec_training_token");allRows=[];render();setStatus("Disconnected.");});
$("apply-filters").addEventListener("click",render);
$("reset-filters").addEventListener("click",()=>{["from-date","to-date","programme","unit"].forEach(id=>$(id).value="");render();});
function exportRows(){
  return filtered().map(r=>({
    Activity:r.course_name, Programme:r.programme_name, Skill:r.skill_name,
    Unit:r.unit_name||"Institutional", "Start date":r.start_date, "End date":r.end_date,
    Enrolled:Number(r.enrolled||0), Trained:Number(r.trained||0), Completed:Number(r.completed||0),
    Status:r.status, Facilitators:(r.facilitators||[]).map(f=>typeof f==="string"?f:f.full_name||"").join("; ")
  }));
}
function downloadBlob(blob, filename){
  const url=URL.createObjectURL(blob), a=document.createElement("a");
  a.href=url; a.download=filename; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
$("export-csv").addEventListener("click",()=>{
  const rows=exportRows(), headers=Object.keys(rows[0]||{});
  if(!headers.length){setStatus("No matching records to export.");return;}
  const q=v=>`"${String(v??"").replace(/"/g,'""')}"`;
  const lines=[headers.map(q).join(","),...rows.map(r=>headers.map(h=>q(r[h])).join(","))];
  downloadBlob(new Blob(["\ufeff"+lines.join("\r\n")],{type:"text/csv;charset=utf-8"}),"tec-training-dashboard.csv");
});
$("export-excel").addEventListener("click",()=>{
  const rows=exportRows();
  if(!rows.length){setStatus("No matching records to export.");return;}
  if(!window.XLSX){setStatus("Excel library did not load. Check internet access and refresh.");return;}
  const ws=XLSX.utils.json_to_sheet(rows);
  ws["!cols"]=[{wch:34},{wch:38},{wch:34},{wch:18},{wch:14},{wch:14},{wch:12},{wch:12},{wch:12},{wch:14},{wch:42}];
  const wb=XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb,ws,"Training Activities");
  XLSX.writeFile(wb,"tec-training-dashboard.xlsx");
});
$("export-pdf").addEventListener("click",()=>{
  if(!filtered().length){setStatus("No matching records to print.");return;}
  setStatus("In the print window, select Save to PDF as the destination.");
  window.print();
});
if(token)load().catch(err=>{token="";sessionStorage.removeItem("tec_training_token");setStatus(`Session expired or unavailable: ${err.message}. Please connect again.`);});
