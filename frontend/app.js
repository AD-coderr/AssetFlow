const STATUSES = [
  ["AVAILABLE", "Available"],
  ["ASSIGNED", "Assigned"],
  ["IN_REPAIR", "In repair"],
  ["RETIRED", "Retired"],
];
const statusLabel = (s) => (STATUSES.find(([v]) => v === s) || [s, s || "—"])[1];

const esc = (v) =>
  String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const dash = (v) => (v ? esc(v) : '<span class="muted">—</span>');

const RESOURCES = {
  assets: {
    path: "/assets",
    key: "asset",
    singular: "asset",
    title: "Assets",
    subtitle: "Track every device your team owns.",
    fields: [
      { key: "asset_tag", label: "Asset tag", required: true, placeholder: "LAP-001" },
      { key: "asset_type", label: "Type", required: true, placeholder: "Laptop" },
      { key: "brand", label: "Brand", required: true, placeholder: "Dell" },
      { key: "model", label: "Model", required: true, placeholder: "XPS 13" },
      { key: "serial_number", label: "Serial number", placeholder: "Optional" },
      { key: "status", label: "Status", type: "select", options: STATUSES, default: "AVAILABLE" },
      { key: "location", label: "Location", placeholder: "e.g. HQ, 2nd floor", full: true },
    ],
    columns: [
      { label: "Asset", render: (a) => `<div class="primary-cell mono">${esc(a.asset_tag)}</div><div class="sub">${esc(a.asset_type)}</div>` },
      { label: "Brand / model", render: (a) => `${esc(a.brand)} <span class="muted">${esc(a.model)}</span>` },
      { label: "Serial", render: (a) => (a.serial_number ? `<span class="mono">${esc(a.serial_number)}</span>` : dash()) },
      { label: "Location", render: (a) => dash(a.location) },
      { label: "Status", render: (a) => `<span class="pill ${esc((a.status || "").toLowerCase())}">${esc(statusLabel(a.status))}</span>` },
    ],
    searchText: (a) => [a.asset_tag, a.asset_type, a.brand, a.model, a.serial_number, a.location, statusLabel(a.status)].join(" "),
    stats: (items) => [
      ["Total assets", items.length],
      ["Available", items.filter((a) => a.status === "AVAILABLE").length],
      ["Assigned", items.filter((a) => a.status === "ASSIGNED").length],
      ["In repair", items.filter((a) => a.status === "IN_REPAIR").length],
    ],
    name: (a) => a.asset_tag,
  },
  employees: {
    path: "/employees",
    key: "employee",
    singular: "employee",
    title: "Employees",
    subtitle: "The people assets get assigned to.",
    fields: [
      { key: "first_name", label: "First name", required: true },
      { key: "last_name", label: "Last name", required: true },
      { key: "email", label: "Email", required: true, type: "email", placeholder: "name@company.com", full: true },
      { key: "department", label: "Department", placeholder: "IT" },
      { key: "position", label: "Position", placeholder: "Engineer" },
    ],
    columns: [
      {
        label: "Name",
        render: (e) =>
          `<span class="avatar">${esc(((e.first_name[0] || "") + (e.last_name[0] || "")).toUpperCase())}</span><span class="primary-cell">${esc(e.first_name)} ${esc(e.last_name)}</span>`,
      },
      { label: "Email", render: (e) => `<span class="muted">${esc(e.email)}</span>` },
      { label: "Department", render: (e) => dash(e.department) },
      { label: "Position", render: (e) => dash(e.position) },
    ],
    searchText: (e) => [e.first_name, e.last_name, e.email, e.department, e.position].join(" "),
    stats: (items) => [
      ["Total employees", items.length],
      ["Departments", new Set(items.map((e) => e.department).filter(Boolean)).size],
    ],
    name: (e) => `${e.first_name} ${e.last_name}`,
  },
};

const $ = (id) => document.getElementById(id);
const state = { view: "assets", items: [], query: "", editing: null };

async function api(path, options = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const d = body && body.detail;
    const msg = Array.isArray(d) ? d.map((e) => `${e.loc.at(-1)}: ${e.msg}`).join(", ") : d || `Request failed (${res.status})`;
    throw new Error(msg);
  }
  return body;
}

let toastTimer;
function toast(message, isError = false) {
  const t = $("toast");
  t.textContent = message;
  t.classList.toggle("error", isError);
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 2600);
}

const cfg = () => RESOURCES[state.view];

async function load() {
  try {
    state.items = await api(cfg().path);
  } catch (err) {
    state.items = [];
    toast(err.message, true);
  }
  render();
}

function setView(view) {
  state.view = view;
  state.query = "";
  $("search").value = "";
  const c = cfg();
  document.querySelectorAll(".tab").forEach((t) => t.setAttribute("aria-selected", String(t.dataset.view === view)));
  $("page-title").textContent = c.title;
  $("page-subtitle").textContent = c.subtitle;
  $("add-label").textContent = `Add ${c.singular}`;
  $("search").placeholder = `Search ${c.title.toLowerCase()}…`;
  try { localStorage.setItem("assetflow:view", view); } catch {}
  load();
}

function render() {
  const c = cfg();
  $("stats").innerHTML = c
    .stats(state.items)
    .map(([label, value]) => `<div class="stat"><div class="stat-label">${esc(label)}</div><div class="stat-value">${value}</div></div>`)
    .join("");

  const q = state.query.trim().toLowerCase();
  const rows = q ? state.items.filter((i) => c.searchText(i).toLowerCase().includes(q)) : state.items;

  $("thead").innerHTML = `<tr>${c.columns.map((col) => `<th>${esc(col.label)}</th>`).join("")}<th></th></tr>`;
  $("tbody").innerHTML = rows
    .map(
      (item) => `<tr>
        ${c.columns.map((col) => `<td>${col.render(item)}</td>`).join("")}
        <td class="actions"><div class="row-actions">
          <button class="icon-btn" data-edit="${item.id}" aria-label="Edit">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20h4L19 9l-4-4L4 16z"/></svg>
          </button>
          <button class="icon-btn danger" data-delete="${item.id}" aria-label="Delete">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg>
          </button>
        </div></td>
      </tr>`
    )
    .join("");

  const empty = $("empty");
  empty.hidden = rows.length > 0;
  empty.innerHTML = state.items.length
    ? `<strong>No matches</strong>Nothing matches “${esc(state.query)}”.`
    : `<strong>No ${c.title.toLowerCase()} yet</strong>Click “Add ${c.singular}” to create the first one.`;
  $("count").textContent = `${rows.length} of ${state.items.length}`;
}

function openForm(item = null) {
  const c = cfg();
  state.editing = item;
  $("dialog-title").textContent = item ? `Edit ${c.singular}` : `Add ${c.singular}`;
  $("save-btn").textContent = item ? "Save changes" : `Add ${c.singular}`;
  $("form-error").hidden = true;
  $("fields").innerHTML = c.fields
    .map((f) => {
      const value = item ? item[f.key] ?? "" : f.default ?? "";
      const label = `<label for="f-${f.key}">${esc(f.label)}${f.required ? '<span class="req">*</span>' : ""}</label>`;
      const control =
        f.type === "select"
          ? `<select id="f-${f.key}" name="${f.key}">${f.options
              .map(([v, l]) => `<option value="${esc(v)}"${v === value ? " selected" : ""}>${esc(l)}</option>`)
              .join("")}</select>`
          : `<input id="f-${f.key}" name="${f.key}" type="${f.type || "text"}" value="${esc(value)}" placeholder="${esc(f.placeholder || "")}"${f.required ? " required" : ""}>`;
      return `<div class="field${f.full ? " full" : ""}">${label}${control}</div>`;
    })
    .join("");
  $("dialog").showModal();
  $("fields").querySelector("input, select")?.focus();
}

async function submitForm(event) {
  event.preventDefault();
  const c = cfg();
  const data = {};
  let firstInvalid = null;
  for (const f of c.fields) {
    const el = $(`f-${f.key}`);
    const v = el.value.trim();
    const bad = (f.required && !v) || (f.type === "email" && v && !el.checkValidity());
    el.parentElement.classList.toggle("invalid", bad);
    if (bad && !firstInvalid) firstInvalid = el;
    data[f.key] = v || (f.required ? v : null);
  }
  if (firstInvalid) {
    $("form-error").textContent = "Please fill in the highlighted fields.";
    $("form-error").hidden = false;
    firstInvalid.focus();
    return;
  }

  const btn = $("save-btn");
  btn.disabled = true;
  try {
    const editing = state.editing;
    await api(editing ? `${c.path}/${editing.id}` : c.path, {
      method: editing ? "PUT" : "POST",
      body: JSON.stringify(data),
    });
    $("dialog").close();
    toast(editing ? `${c.name(data)} updated` : `${c.name(data)} added`);
    load();
  } catch (err) {
    $("form-error").textContent = err.message;
    $("form-error").hidden = false;
  } finally {
    btn.disabled = false;
  }
}

async function remove(id) {
  const c = cfg();
  const item = state.items.find((i) => i.id === id);
  if (!item || !confirm(`Delete ${c.name(item)}? This can't be undone.`)) return;
  try {
    await api(`${c.path}/${id}`, { method: "DELETE" });
    toast(`${c.name(item)} deleted`);
    load();
  } catch (err) {
    toast(err.message, true);
  }
}

document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => setView(t.dataset.view)));
$("add-btn").addEventListener("click", () => openForm());
$("form").addEventListener("submit", submitForm);
document.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", () => $("dialog").close()));
$("search").addEventListener("input", (e) => {
  state.query = e.target.value;
  render();
});
$("tbody").addEventListener("click", (e) => {
  const edit = e.target.closest("[data-edit]");
  const del = e.target.closest("[data-delete]");
  if (edit) openForm(state.items.find((i) => i.id === Number(edit.dataset.edit)));
  if (del) remove(Number(del.dataset.delete));
});

let initial = "assets";
try { initial = localStorage.getItem("assetflow:view") || "assets"; } catch {}
setView(RESOURCES[initial] ? initial : "assets");
