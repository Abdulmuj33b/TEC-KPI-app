const units = [
  {name:"Fashion",symbol:"✂",description:"Garments, tailoring and textile production."},
  {name:"Leather",symbol:"◇",description:"Leather goods, footwear and accessories."},
  {name:"Graphics",symbol:"▧",description:"Printing, design and graphics services."},
  {name:"Paint",symbol:"◉",description:"Paint manufacturing, batches and sales."},
  {name:"Consumables",symbol:"▤",description:"Consumable products, stock and distribution."},
  {name:"Smart Farm",symbol:"♧",description:"Farm output, harvests and sales."},
  {name:"Aquaculture",symbol:"≈",description:"Fish production, feed and harvest records."}
];

const titles = {
  dashboard:"Overview dashboard",
  production:"Production units",
  training:"Training & courses",
  research:"Research & Development",
  reports:"Production report",
  "training-report":"New training report",
  "research-report":"New R&D report"
};

const productionReports = [];
const trainingReports = [];
const researchReports = [];

const byId = id => document.getElementById(id);
const naira = value => new Intl.NumberFormat("en-NG", {
  style:"currency", currency:"NGN", maximumFractionDigits:2
}).format(Number(value || 0));

const today = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
};

function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  })[char]);
}

function unitCard(unit) {
  return `<article class="unit-card">
    <span class="unit-symbol">${unit.symbol}</span>
    <h3>${unit.name}</h3><p>${unit.description}</p>
    <button type="button" data-unit="${unit.name}">Record report →</button>
  </article>`;
}

byId("unit-grid").innerHTML = units.map(unitCard).join("");
byId("production-grid").innerHTML = units.map(unitCard).join("");
byId("report-unit").innerHTML = '<option value="">Choose a unit</option>' +
  units.map(unit => `<option value="${unit.name}">${unit.name}</option>`).join("");

function showPage(page) {
  if (!titles[page]) return;
  document.querySelectorAll(".page").forEach(el =>
    el.classList.toggle("active-page", el.id === page));
  document.querySelectorAll(".nav-link").forEach(el =>
    el.classList.toggle("active", el.dataset.page === page));
  byId("page-title").textContent = titles[page];
  window.scrollTo({top:0,behavior:"smooth"});
}

document.querySelectorAll("[data-page]").forEach(button =>
  button.addEventListener("click", () => showPage(button.dataset.page)));

document.querySelectorAll("[data-go]").forEach(button =>
  button.addEventListener("click", () => showPage(button.dataset.go)));

document.addEventListener("click", event => {
  const button = event.target.closest("[data-unit]");
  if (!button) return;
  byId("report-unit").value = button.dataset.unit;
  showPage("reports");
});

["report-date","tr-start-date","tr-end-date","rd-date"].forEach(id => byId(id).value = today());

byId("menu-toggle").addEventListener("click", () => {
  const collapsed = document.body.classList.toggle("menu-collapsed");
  byId("menu-toggle").setAttribute("aria-expanded", String(!collapsed));
  byId("menu-toggle").setAttribute("aria-label", collapsed ? "Show navigation" : "Hide navigation");
});

function renderProduction() {
  byId("total-revenue").textContent = naira(
    productionReports.reduce((sum, report) => sum + report.revenue, 0)
  );

  byId("recent-reports").innerHTML = productionReports.length
    ? productionReports.slice().reverse().slice(0,5).map(report => `
      <div class="recent-item"><div><strong>${escapeHTML(report.product)}</strong>
      <small>${escapeHTML(report.unit)} · ${escapeHTML(report.date)}</small></div>
      <div class="recent-amount">${naira(report.revenue)}<small>${escapeHTML(report.status)}</small></div></div>`
    ).join("")
    : '<div class="empty-state">No production reports recorded yet.</div>';

  byId("production-rows").innerHTML = productionReports.length
    ? productionReports.slice().reverse().map(report => `
      <tr><td>${escapeHTML(report.date)}</td><td>${escapeHTML(report.unit)}</td>
      <td>${report.output}</td><td>${naira(report.revenue)}</td><td>${escapeHTML(report.status)}</td></tr>`
    ).join("")
    : '<tr><td colspan="5">No production reports recorded yet.</td></tr>';
}

byId("report-form").addEventListener("submit", event => {
  event.preventDefault();
  const output = Number(byId("report-output").value);
  const sold = Number(byId("report-sold").value || 0);
  const stock = Number(byId("report-stock").value || 0);
  const revenue = Number(byId("report-revenue").value);

  if (sold > output) {
    byId("form-message").textContent = "Quantity sold cannot exceed quantity produced in this simple form.";
    return;
  }

  productionReports.push({
    date:byId("report-date").value, unit:byId("report-unit").value,
    product:byId("report-product").value.trim(), output, sold, stock, revenue,
    status:byId("report-status").value,
    challenges:byId("report-challenges").value.trim(),
    recommendations:byId("report-recommendations").value.trim()
  });

  renderProduction();
  event.target.reset();
  byId("report-date").value = today();
  byId("form-message").textContent = "Production report added in demo mode; not saved to a database.";
  showPage("dashboard");
});

const API_BASE_URL = "http://localhost:8000";
let trainingToken = sessionStorage.getItem("tec_training_token") || "";
let trainingProgrammes = [];
let trainingSkills = [];
let trainingFacilitators = [];
let trainingApiRecords = [];
let selectedTrainingFile = null;

async function trainingApi(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (trainingToken) headers.set("Authorization", `Bearer ${trainingToken}`);
  const response = await fetch(`${API_BASE_URL}${path}`, {...options, headers});
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail || `Request failed (${response.status})`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return payload;
}

function renderTraining() {
  const rows = trainingApiRecords;
  byId("training-count").textContent = rows.length;
  byId("training-enrolled").textContent =
    rows.reduce((sum, r) => sum + Number(r.enrolled || 0), 0).toLocaleString();
  byId("training-completed").textContent =
    rows.reduce((sum, r) => sum + Number(r.completed || 0), 0).toLocaleString();

  byId("training-rows").innerHTML = rows.length
    ? rows.map(r => `
      <tr><td>${escapeHTML(r.start_date)} – ${escapeHTML(r.end_date)}</td>
      <td>${escapeHTML(r.programme_name)}<br>${escapeHTML(r.level)}</td>
      <td>${escapeHTML(r.skill_name)}</td>
      <td>${escapeHTML((r.facilitators || []).map(f => f.full_name).join(", ") || "Not assigned")}</td>
      <td>${Number(r.enrolled)}</td><td>${Number(r.trained)}</td><td>${Number(r.completed)}</td>
      <td>${escapeHTML(r.status)}</td></tr>`
    ).join("")
    : '<tr><td colspan="8">No training records found in the database.</td></tr>';
}

async function loadTrainingReferenceData() {
  [trainingProgrammes, trainingSkills, trainingFacilitators] = await Promise.all([
    trainingApi("/api/training/programmes"),
    trainingApi("/api/training/skills"),
    trainingApi("/api/training/facilitators")
  ]);
  const unitRows = await trainingApi("/api/units");
  byId("tr-unit").innerHTML = '<option value="">Institution-wide / not applicable</option>' +
    unitRows.map(u => `<option value="${u.id}">${escapeHTML(u.name)}</option>`).join("");
  byId("tr-programme").innerHTML =
    '<option value="">Choose programme</option>' +
    trainingProgrammes.map(p => `<option value="${p.id}">${escapeHTML(p.name)}</option>`).join("");
  byId("tr-facilitators").innerHTML = trainingFacilitators.map(f =>
    `<option value="${f.id}">${escapeHTML(f.full_name)}</option>`).join("");
  await loadTrainingActivities();
}

async function loadTrainingActivities() {
  trainingApiRecords = await trainingApi("/api/training/activities?limit=500");
  renderTraining();
}

byId("training-login-form").addEventListener("submit", async event => {
  event.preventDefault();
  const message = byId("training-api-message");
  message.textContent = "Connecting...";
  try {
    const form = new URLSearchParams();
    form.set("username", byId("training-email").value.trim());
    form.set("password", byId("training-password").value);
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: {"Content-Type":"application/x-www-form-urlencoded"},
      body: form
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.detail || `Login failed (${response.status})`);
    trainingToken = result.access_token;
    sessionStorage.setItem("tec_training_token", trainingToken);
    byId("training-password").value = "";
    await loadTrainingReferenceData();
    message.textContent = `Connected. Loaded ${trainingProgrammes.length} programmes, ${trainingSkills.length} skills and ${trainingFacilitators.length} active facilitators.`;
  } catch (error) {
    trainingToken = "";
    sessionStorage.removeItem("tec_training_token");
    message.textContent = error.message;
  }
});

byId("training-disconnect").addEventListener("click", () => {
  trainingToken = "";
  sessionStorage.removeItem("tec_training_token");
  trainingApiRecords = [];
  renderTraining();
  byId("training-api-message").textContent = "Disconnected.";
});

if (trainingToken) {
  loadTrainingReferenceData()
    .then(() => { byId("training-api-message").textContent = "Reconnected using this browser session."; })
    .catch(error => {
      trainingToken = "";
      sessionStorage.removeItem("tec_training_token");
      byId("training-api-message").textContent = `Session expired. Please connect again. ${error.message}`;
    });
}

byId("tr-programme").addEventListener("change", () => {
  const programmeId = Number(byId("tr-programme").value);
  const options = trainingSkills.filter(s => s.programme_id === programmeId);
  byId("tr-skill").innerHTML = '<option value="">Choose skill</option>' +
    options.map(s => `<option value="${s.id}">${escapeHTML(s.name)}</option>`).join("");
});

byId("training-form").addEventListener("submit", async event => {
  event.preventDefault();
  if (!trainingToken) {
    byId("training-form-message").textContent = "Connect to the API first.";
    return;
  }
  const facilitatorIds = Array.from(byId("tr-facilitators").selectedOptions)
    .map(option => Number(option.value));
  const payload = {
    programme_id: Number(byId("tr-programme").value),
    skill_id: Number(byId("tr-skill").value),
    unit_id: byId("tr-unit").value ? Number(byId("tr-unit").value) : null,
    start_date: byId("tr-start-date").value,
    end_date: byId("tr-end-date").value,
    level: byId("tr-level").value.trim(),
    course_name: byId("tr-course").value.trim(),
    enrolled: Number(byId("tr-enrolled").value),
    trained: Number(byId("tr-trained").value),
    completed: Number(byId("tr-completed").value),
    status: byId("tr-status").value.toLowerCase(),
    facilitator_ids: facilitatorIds,
    notes: byId("tr-notes").value.trim() || null
  };
  try {
    await trainingApi("/api/training/activities", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify(payload)
    });
    await loadTrainingActivities();
    event.target.reset();
    byId("tr-start-date").value = today();
    byId("tr-end-date").value = today();
    byId("tr-skill").innerHTML = '<option value="">Select a programme first</option>';
    byId("training-form-message").textContent = "Training activity saved to the database.";
    showPage("training");
  } catch (error) {
    byId("training-form-message").textContent = error.message;
  }
});

function renderResearch() {
  byId("research-rows").innerHTML = researchReports.length
    ? researchReports.slice().reverse().map(r => `
      <tr><td>${escapeHTML(r.date)}</td><td>${escapeHTML(r.category)}</td>
      <td>${escapeHTML(r.title)}</td><td>${naira(r.funding)}</td><td>${escapeHTML(r.status)}</td></tr>`
    ).join("")
    : '<tr><td colspan="5">No R&D reports yet.</td></tr>';
}

byId("research-form").addEventListener("submit", event => {
  event.preventDefault();
  researchReports.push({
    date:byId("rd-date").value,
    category:byId("rd-category").value,
    title:byId("rd-title").value.trim(),
    funding:Number(byId("rd-funding").value || 0),
    status:byId("rd-status").value,
    partner:byId("rd-partner").value.trim(),
    target:byId("rd-target").value,
    notes:byId("rd-notes").value.trim()
  });
  renderResearch();
  event.target.reset();
  byId("rd-date").value = today();
  byId("research-form-message").textContent = "R&D report added in demo mode; not saved to a database.";
  showPage("research");
});

/* CSV import is sent to the API; PostgreSQL performs validation and persistence. */
byId("training-csv").addEventListener("change", event => {
  selectedTrainingFile = event.target.files[0] || null;
  byId("csv-preview").innerHTML = selectedTrainingFile
    ? `<p>Selected: <strong>${escapeHTML(selectedTrainingFile.name)}</strong> (${Math.ceil(selectedTrainingFile.size/1024)} KB)</p>`
    : "";
  byId("import-training").disabled = !selectedTrainingFile || !trainingToken;
  byId("csv-message").textContent = selectedTrainingFile
    ? "File selected. Connect to the API, then import."
    : "";
});

byId("import-training").addEventListener("click", async () => {
  if (!selectedTrainingFile) return;
  if (!trainingToken) {
    byId("csv-message").textContent = "Connect to the API before importing.";
    return;
  }
  const button = byId("import-training");
  button.disabled = true;
  byId("csv-message").textContent = "Uploading and validating CSV...";
  const body = new FormData();
  body.append("file", selectedTrainingFile);
  try {
    const result = await trainingApi("/api/training/activities/import", {
      method:"POST",
      body
    });
    byId("csv-message").textContent =
      `Import complete: ${result.imported} imported, ${result.skipped} duplicates skipped, ${result.rejected} rejected.`;
    byId("csv-preview").innerHTML = `
      <div class="table-wrap"><table><thead><tr><th>CSV row</th><th>Result</th><th>Details</th></tr></thead>
      <tbody>${result.results.map(item => `<tr><td>${item.row}</td><td>${escapeHTML(item.status)}</td><td>${escapeHTML(item.reason || "")}</td></tr>`).join("")}</tbody></table></div>`;
    selectedTrainingFile = null;
    byId("training-csv").value = "";
    await loadTrainingActivities();
  } catch (error) {
    byId("csv-message").textContent = error.message;
  } finally {
    button.disabled = !selectedTrainingFile;
  }
});

byId("download-training-template").addEventListener("click", () => {
  const template = [
    "programme,start_date,end_date,course,level,skill,unit,enrolled,trained,completed,facilitator_names,status,notes",
    '"300-level Skill Acquisition / Venture Creation",2026-11-16,2026-11-20,Fashion Design Practical Training,300-level,"Fashion Design and Garment Production",Fashion,30,25,20,"Test Facilitator One; Test Facilitator Two",ongoing,"Example only; remove or replace this row before importing"'
  ].join("\r\n");
  const url = URL.createObjectURL(new Blob([template], {type:"text/csv;charset=utf-8;"}));
  const link = document.createElement("a");
  link.href = url;
  link.download = "tec-training-import-template.csv";
  link.click();
  URL.revokeObjectURL(url);
});

renderProduction();
renderTraining();
renderResearch();
