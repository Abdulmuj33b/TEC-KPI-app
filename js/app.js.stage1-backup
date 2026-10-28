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
let pendingTrainingRows = [];

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

function renderTraining() {
  byId("training-count").textContent = trainingReports.length;
  byId("training-enrolled").textContent =
    trainingReports.reduce((sum, r) => sum + r.enrolled, 0).toLocaleString();
  byId("training-completed").textContent =
    trainingReports.reduce((sum, r) => sum + r.completed, 0).toLocaleString();

  byId("training-rows").innerHTML = trainingReports.length
    ? trainingReports.slice().reverse().map(r => `
      <tr><td>${escapeHTML(r.startDate)} – ${escapeHTML(r.endDate)}</td><td>${escapeHTML(r.level)}<br>${escapeHTML(r.course)}</td>
      <td>${escapeHTML(r.skill)}</td><td>${r.facilitators}</td><td>${r.enrolled}</td>
      <td>${r.trained}</td><td>${r.completed}</td><td>${escapeHTML(r.status)}</td></tr>`
    ).join("")
    : '<tr><td colspan="8">No training records yet.</td></tr>';
}

function getTrainingFormRecord() {
  return {
    startDate:byId("tr-start-date").value,
    endDate:byId("tr-end-date").value,
    course:byId("tr-course").value.trim(),
    level:byId("tr-level").value,
    skill:byId("tr-skill").value.trim(),
    facilitators:Number(byId("tr-facilitators").value),
    enrolled:Number(byId("tr-enrolled").value),
    trained:Number(byId("tr-trained").value),
    completed:Number(byId("tr-completed").value),
    status:byId("tr-status").value,
    notes:byId("tr-notes").value.trim()
  };
}

function validateTrainingRecord(r) {
  if (!r.startDate || !r.endDate || !r.course || !r.level || !r.skill)
    return "Start date, end date, programme, course and skill are required.";
  if (r.endDate < r.startDate) return "The end date cannot be earlier than the start date.";
  if (![r.facilitators,r.enrolled,r.trained,r.completed].every(n => Number.isInteger(n) && n >= 0))
    return "Facilitator and student counts must be whole numbers of zero or more.";
  if (r.trained > r.enrolled) return "Students trained cannot exceed students enrolled.";
  if (r.completed > r.trained) return "Students completed cannot exceed students trained.";
  return "";
}

byId("training-form").addEventListener("submit", event => {
  event.preventDefault();
  const record = getTrainingFormRecord();
  const error = validateTrainingRecord(record);
  if (error) {
    byId("training-form-message").textContent = error;
    return;
  }
  trainingReports.push(record);
  renderTraining();
  event.target.reset();
  byId("tr-start-date").value = today();
  byId("tr-end-date").value = today();
  byId("training-form-message").textContent = "Training report added in demo mode; not saved to a database.";
  showPage("training");
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

/* CSV parser supports quoted fields and commas inside quoted text. */
function parseCSV(text) {
  const rows = [];
  let row = [], cell = "", quoted = false;
  text = text.replace(/^\uFEFF/, "");

  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"' && quoted && text[i+1] === '"') {
      cell += '"'; i++;
    } else if (c === '"') {
      quoted = !quoted;
    } else if (c === "," && !quoted) {
      row.push(cell.trim()); cell = "";
    } else if ((c === "\n" || c === "\r") && !quoted) {
      if (c === "\r" && text[i+1] === "\n") i++;
      row.push(cell.trim()); cell = "";
      if (row.some(value => value !== "")) rows.push(row);
      row = [];
    } else {
      cell += c;
    }
  }
  if (quoted) throw new Error("The CSV contains an unclosed quotation mark.");
  row.push(cell.trim());
  if (row.some(value => value !== "")) rows.push(row);
  return rows;
}

function csvTrainingRecord(headers, cells, lineNumber) {
  const data = {};
  headers.forEach((header, i) => data[header] = (cells[i] || "").trim());

  const required = ["start_date","end_date","course","level","skill","facilitators","enrolled","trained","completed"];
  const missing = required.filter(key => !(key in data));
  if (missing.length) throw new Error(`Missing required columns: ${missing.join(", ")}.`);

  const numeric = key => {
    if (data[key] === "" || !/^\d+$/.test(data[key])) {
      throw new Error(`Row ${lineNumber}: ${key} must be a whole number.`);
    }
    return Number(data[key]);
  };

  const record = {
    startDate:data.start_date, endDate:data.end_date,
    course:data.course, level:data.level, skill:data.skill,
    facilitators:numeric("facilitators"),
    enrolled:numeric("enrolled"),
    trained:numeric("trained"),
    completed:numeric("completed"),
    status:data.status || "Draft",
    notes:data.notes || ""
  };
  const error = validateTrainingRecord(record);
  if (error) throw new Error(`Row ${lineNumber}: ${error}`);
  for (const [label, date] of [["start_date", record.startDate], ["end_date", record.endDate]]) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || Number.isNaN(Date.parse(date)))
      throw new Error(`Row ${lineNumber}: ${label} must use YYYY-MM-DD.`);
  }
  if (record.endDate < record.startDate)
    throw new Error(`Row ${lineNumber}: end_date cannot be earlier than start_date.`);
  return record;
}

byId("training-csv").addEventListener("change", async event => {
  pendingTrainingRows = [];
  byId("csv-preview").innerHTML = "";
  byId("import-training").disabled = true;
  byId("csv-message").textContent = "";

  const file = event.target.files[0];
  if (!file) return;

  try {
    const rows = parseCSV(await file.text());
    if (rows.length < 2) throw new Error("The file needs a header row and at least one data row.");

    const headers = rows[0].map(h => h.trim().toLowerCase());
    const required = ["start_date","end_date","course","level","skill","facilitators","enrolled","trained","completed"];
    const missing = required.filter(h => !headers.includes(h));
    if (missing.length) throw new Error(`Missing columns: ${missing.join(", ")}.`);

    const errors = [];
    rows.slice(1).forEach((cells, i) => {
      try {
        pendingTrainingRows.push(csvTrainingRecord(headers, cells, i + 2));
      } catch (error) {
        errors.push(error.message);
      }
    });

    byId("csv-preview").innerHTML = `
      <table><thead><tr><th>Row</th><th>Date</th><th>Course</th><th>Level</th><th>Enrolled</th><th>Completed</th></tr></thead>
      <tbody>${pendingTrainingRows.slice(0,10).map((r,i) => `
        <tr><td>${i+2}</td><td>${escapeHTML(r.startDate)} – ${escapeHTML(r.endDate)}</td><td>${escapeHTML(r.course)}</td>
        <td>${escapeHTML(r.level)} / ${escapeHTML(r.skill)}</td><td>${r.enrolled}</td><td>${r.completed}</td></tr>`).join("")}</tbody></table>
      ${pendingTrainingRows.length > 10 ? `<p class="muted">Preview shows 10 of ${pendingTrainingRows.length} valid rows.</p>` : ""}
      ${errors.length ? `<p class="form-message">${errors.length} row(s) rejected:<br>${errors.slice(0,8).map(escapeHTML).join("<br>")}${errors.length>8?"<br>More errors omitted from preview.":""}</p>` : ""}
    `;

    byId("import-training").disabled = pendingTrainingRows.length === 0;
    byId("csv-message").textContent =
      `${pendingTrainingRows.length} valid row(s) ready to import. ${errors.length} invalid row(s) will be skipped.`;
  } catch (error) {
    byId("csv-message").textContent = error.message;
  }
});

byId("import-training").addEventListener("click", () => {
  if (!pendingTrainingRows.length) return;
  trainingReports.push(...pendingTrainingRows);
  const count = pendingTrainingRows.length;
  pendingTrainingRows = [];
  byId("training-csv").value = "";
  byId("csv-preview").innerHTML = "";
  byId("import-training").disabled = true;
  byId("csv-message").textContent = `${count} training record(s) imported into this browser session.`;
  renderTraining();
});

byId("cancel-training-import").addEventListener("click", () => {
  pendingTrainingRows = [];
  byId("training-csv").value = "";
  byId("csv-preview").innerHTML = "";
  byId("csv-message").textContent = "Import cancelled.";
  byId("import-training").disabled = true;
});

byId("download-training-template").addEventListener("click", () => {
  const template = [
    "start_date,end_date,course,level,skill,facilitators,enrolled,trained,completed,status",
    "2026-10-16,2026-11-16,Entrepreneurship Training,200-level ENT,Entrepreneurship,3,120,115,110,Draft",
    "2026-10-16,2026-11-30,Skill Acquisition / Venture Creation,300-level Skill Acquisition / Venture Creation,Leatherwork,4,80,78,75,Draft"
  ].join("\r\n");
  const url = URL.createObjectURL(new Blob([template], {type:"text/csv;charset=utf-8;"}));
  const link = document.createElement("a");
  link.href = url;
  link.download = "training-template.csv";
  link.click();
  URL.revokeObjectURL(url);
});

renderProduction();
renderTraining();
renderResearch();
