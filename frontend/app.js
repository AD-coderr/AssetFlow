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

const fullName = (e) => `${e.first_name} ${e.last_name}`;
const initials = (e) => ((e.first_name[0] || "") + (e.last_name[0] || "")).toUpperCase();

// The API returns UTC timestamps without a zone suffix.
function fmtDate(value) {
  if (!value) return "";
  const d = new Date(/Z|[+-]\d\d:\d\d$/.test(value) ? value : value + "Z");
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }) +
    ", " + d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

const ICONS = {
  assign: '<path d="M15 19c0-2.8-2.7-5-6-5s-6 2.2-6 5"/><circle cx="9" cy="7" r="4"/><path d="M19 8v6M16 11h6"/>',
  return: '<path d="M9 14L4 9l5-5"/><path d="M4 9h10a6 6 0 010 12h-3"/>',
  history: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
};
const iconBtn = (attr, id, icon, label, cls = "") =>
  `<button class="icon-btn ${cls}" ${attr}="${id}" aria-label="${label}" title="${label}">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONS[icon]}</svg>
  </button>`;

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
      {
        label: "Assigned to",
        render: (a) =>
          a.assigned_to
            ? `<span class="holder"><span class="avatar">${esc(initials(a.assigned_to))}</span>${esc(fullName(a.assigned_to))}</span>`
            : dash(),
      },
      { label: "Status", render: (a) => `<span class="pill ${esc((a.status || "").toLowerCase())}">${esc(statusLabel(a.status))}</span>` },
    ],
    searchText: (a) => [a.asset_tag, a.asset_type, a.brand, a.model, a.serial_number, a.location, statusLabel(a.status), a.assigned_to ? fullName(a.assigned_to) : ""].join(" "),
    rowActions: (a) =>
      (a.assigned_to
        ? iconBtn("data-return", a.id, "return", "Return asset", "accent")
        : a.status === "AVAILABLE"
          ? iconBtn("data-assign", a.id, "assign", "Assign to employee", "accent")
          : "") + iconBtn("data-history", a.id, "history", "Assignment history"),
    historyTitle: (a) => [`History · ${a.asset_tag}`, `${a.brand} ${a.model}`],
    historyLabel: (h) => fullName(h.employee),
    historyEmpty: "This asset has never been assigned.",
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
          `<span class="avatar">${esc(initials(e))}</span><span class="primary-cell">${esc(fullName(e))}</span>`,
      },
      {
        label: "Assets",
        render: (e) => (e.assets.length ? e.assets.map((a) => `<span class="chip">${esc(a.asset_tag)}</span>`).join("") : dash()),
      },
      { label: "Email", render: (e) => `<span class="muted">${esc(e.email)}</span>` },
      { label: "Department", render: (e) => dash(e.department) },
      { label: "Position", render: (e) => dash(e.position) },
    ],
    searchText: (e) => [e.first_name, e.last_name, e.email, e.department, e.position, ...e.assets.map((a) => a.asset_tag)].join(" "),
    rowActions: (e) => iconBtn("data-history", e.id, "history", "Assignment history"),
    historyTitle: (e) => [`History · ${fullName(e)}`, e.email],
    historyLabel: (h) => `${h.asset.asset_tag} · ${h.asset.brand} ${h.asset.model}`,
    historyEmpty: "This employee has never been assigned an asset.",
    stats: (items) => [
      ["Total employees", items.length],
      ["Departments", new Set(items.map((e) => e.department).filter(Boolean)).size],
      ["Assets checked out", items.reduce((n, e) => n + e.assets.length, 0)],
    ],
    name: (e) => `${e.first_name} ${e.last_name}`,
  },
};

const $ = (id) => document.getElementById(id);
const state = { view: "assets", items: [], query: "", editing: null, assigning: null };

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

// In-page confirmation. The browser's native confirm box is blocked in some
// embedded browsers, where it silently answers "no".
function askConfirm({ title, message, okLabel = "Confirm", danger = false }) {
  const dialog = $("confirm-dialog");
  const ok = $("confirm-ok");
  $("confirm-title").textContent = title;
  $("confirm-message").textContent = message;
  ok.textContent = okLabel;
  ok.className = `btn ${danger ? "btn-danger" : "btn-primary"}`;
  return new Promise((resolve) => {
    const finish = (value) => {
      ok.removeEventListener("click", onOk);
      $("confirm-cancel").removeEventListener("click", onCancel);
      dialog.removeEventListener("close", onCancel);
      if (dialog.open) dialog.close();
      resolve(value);
    };
    const onOk = () => finish(true);
    const onCancel = () => finish(false);
    ok.addEventListener("click", onOk);
    $("confirm-cancel").addEventListener("click", onCancel);
    dialog.addEventListener("close", onCancel);
    dialog.showModal();
    ok.focus();
  });
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
          ${c.rowActions(item)}
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
      const locked = f.key === "status" && item && item.assigned_to;
      const options = f.key === "status" ? f.options.filter(([v]) => v !== "ASSIGNED" || value === "ASSIGNED") : f.options;
      const hint = locked ? `<span class="hint">Return the asset to change its status.</span>` : "";
      const control =
        f.type === "select"
          ? `<select id="f-${f.key}" name="${f.key}"${locked ? " disabled" : ""}>${options
              .map(([v, l]) => `<option value="${esc(v)}"${v === value ? " selected" : ""}>${esc(l)}</option>`)
              .join("")}</select>`
          : `<input id="f-${f.key}" name="${f.key}" type="${f.type || "text"}" value="${esc(value)}" placeholder="${esc(f.placeholder || "")}"${f.required ? " required" : ""}>`;
      return `<div class="field${f.full ? " full" : ""}">${label}${control}${hint}</div>`;
    })
    .join("");
  $("dialog").showModal();
  $("fields").querySelector("input, select")?.focus();
}

async function openAssign(asset) {
  let employees;
  try {
    employees = await api("/employees");
  } catch (err) {
    return toast(err.message, true);
  }
  if (!employees.length) return toast("Add an employee first, then assign the asset", true);

  state.assigning = asset;
  $("assign-title").textContent = `Assign ${asset.asset_tag}`;
  $("assign-subtitle").textContent = `${asset.brand} ${asset.model}`;
  $("assign-employee").innerHTML = employees
    .map((e) => `<option value="${e.id}">${esc(fullName(e))}${e.department ? ` (${esc(e.department)})` : ""}</option>`)
    .join("");
  $("assign-notes").value = "";
  $("assign-error").hidden = true;
  $("assign-dialog").showModal();
  $("assign-employee").focus();
}

async function submitAssign(event) {
  event.preventDefault();
  const btn = $("assign-btn");
  btn.disabled = true;
  try {
    const res = await api(`/assets/${state.assigning.id}/assign`, {
      method: "POST",
      body: JSON.stringify({
        employee_id: Number($("assign-employee").value),
        notes: $("assign-notes").value.trim() || null,
      }),
    });
    $("assign-dialog").close();
    toast(res.message);
    load();
  } catch (err) {
    $("assign-error").textContent = err.message;
    $("assign-error").hidden = false;
  } finally {
    btn.disabled = false;
  }
}

async function returnAsset(asset) {
  const sure = await askConfirm({
    title: `Return ${asset.asset_tag}?`,
    message: `It's currently assigned to ${fullName(asset.assigned_to)}. Returning it makes it available again.`,
    okLabel: "Return asset",
  });
  if (!sure) return;
  try {
    const res = await api(`/assets/${asset.id}/return`, { method: "POST" });
    toast(res.message);
    load();
  } catch (err) {
    toast(err.message, true);
  }
}

async function openHistory(item) {
  const c = cfg();
  let rows;
  try {
    rows = await api(`${c.path}/${item.id}/assignments`);
  } catch (err) {
    return toast(err.message, true);
  }
  const [title, subtitle] = c.historyTitle(item);
  $("history-title").textContent = title;
  $("history-subtitle").textContent = subtitle;
  $("history-body").innerHTML = rows.length
    ? rows
        .map(
          (h) => `<div class="history-item${h.is_active ? " active" : ""}">
            <div class="history-top">
              <span class="history-who">${esc(c.historyLabel(h))}</span>
              <span class="pill ${h.is_active ? "assigned" : "retired"}">${h.is_active ? "Current" : "Returned"}</span>
            </div>
            <div class="history-dates">${esc(fmtDate(h.assigned_at))} → ${h.is_active ? "now" : esc(fmtDate(h.returned_at))}</div>
            ${h.notes ? `<div class="history-notes">${esc(h.notes)}</div>` : ""}
          </div>`
        )
        .join("")
    : `<div class="history-empty">${esc(c.historyEmpty)}</div>`;
  $("history-dialog").showModal();
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
  if (!item) return;
  const sure = await askConfirm({
    title: `Delete ${c.name(item)}?`,
    message: "This also deletes its assignment history and can't be undone.",
    okLabel: "Delete",
    danger: true,
  });
  if (!sure) return;
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
$("assign-form").addEventListener("submit", submitAssign);
document.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", () => b.closest("dialog").close()));
$("search").addEventListener("input", (e) => {
  state.query = e.target.value;
  render();
});
$("tbody").addEventListener("click", (e) => {
  const edit = e.target.closest("[data-edit]");
  const del = e.target.closest("[data-delete]");
  const byId = (el, key) => state.items.find((i) => i.id === Number(el.dataset[key]));
  const assign = e.target.closest("[data-assign]");
  const ret = e.target.closest("[data-return]");
  const history = e.target.closest("[data-history]");
  if (assign) openAssign(byId(assign, "assign"));
  if (ret) returnAsset(byId(ret, "return"));
  if (history) openHistory(byId(history, "history"));
  if (edit) openForm(state.items.find((i) => i.id === Number(edit.dataset.edit)));
  if (del) remove(Number(del.dataset.delete));
});

let initial = "assets";
try { initial = localStorage.getItem("assetflow:view") || "assets"; } catch {}
setView(RESOURCES[initial] ? initial : "assets");
