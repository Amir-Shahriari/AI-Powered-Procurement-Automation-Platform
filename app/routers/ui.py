from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse
from ..repo.records import load_record

router = APIRouter()

HOME_HTML = r"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>AIT – Spec Intake</title>
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <style>
    body{margin:0;background:#0f172a;color:#e5e7eb;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,"Helvetica Neue",Arial}
    header{padding:16px 20px;background:#0b1220;border-bottom:1px solid #1f2937}
    h1{margin:0;font-size:18px}
    main{padding:16px;max-width:980px;margin:0 auto}
    .card{background:#111827;border:1px solid #1f2937;border-radius:12px;padding:16px}
    .row{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
    button,input[type=submit]{border:1px solid #374151;background:#0b1220;color:#e5e7eb;padding:8px 12px;border-radius:8px;cursor:pointer}
    select{border:1px solid #374151;background:#0b1220;color:#e5e7eb;padding:8px 12px;border-radius:8px}
    a.btn{display:inline-block;text-decoration:none;border:1px solid #374151;background:#0b1220;color:#e5e7eb;padding:8px 12px;border-radius:8px}
    .muted{color:#9ca3af}
    .spacer{height:12px}
    .grid{display:grid;grid-template-columns:1fr;gap:12px}
    @media(min-width:720px){.grid{grid-template-columns:1fr 1fr 1fr}}
    .warn{color:#fbbf24}
    .ok{color:#86efac}
  </style>
</head>
<body>
  <header><h1>AIT – Spec Intake</h1></header>
  <main>
    <div class="card">
      <form id="uploadForm" class="row" method="post" action="/upload" enctype="multipart/form-data">

        <label for="model" class="muted">Model</label>
        <select id="model" name="model" required>
          <!-- adjust to your installed Ollama models -->
          <option value="llama3.1:8b" selected>llama3.1:8b</option>
          <option value="llama3:latest">llama3:latest</option>
          <option value="mistral:latest">mistral:latest</option>
        </select>

        <input type="file" name="file" required />
        <input type="submit" value="Generate" />
        <span id="status" class="muted"></span>
      </form>
      <div class="spacer"></div>
      <div id="after" style="display:none">
        <div class="muted">Record: <span id="recId"></span></div>
        <div class="spacer"></div>
        <div class="grid">
          <!-- When a record is generated, these buttons link to pretty document views -->
          <a class="btn" id="btn-ret"  href="#">Open Returnables</a>
          <a class="btn" id="btn-rft"  href="#">Open RFT</a>
          <a class="btn" id="btn-tepp" href="#">Open TEPP</a>
        </div>
      </div>
    </div>
  </main>
  <script>
    // If page loaded with ?recId=..., show buttons
    const params = new URLSearchParams(location.search);
    const recIdFromQS = params.get("recId");
    const after = document.getElementById("after");
    const statusEl = document.getElementById("status");
    const modelSel = document.getElementById("model");

    function wireButtons(id){
      document.getElementById("recId").textContent = id;
      // Link buttons to the new pretty editors
      document.getElementById("btn-ret").href  = "/ui/returnables/" + id;
      document.getElementById("btn-rft").href  = "/ui/rft/" + id;
      document.getElementById("btn-tepp").href = "/ui/tepp/" + id;
      after.style.display = "block";
    }
    if (recIdFromQS) wireButtons(recIdFromQS);

    // Intercept form to stay on page and show links
    document.getElementById("uploadForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      const form = e.target;
      const data = new FormData(form);
      statusEl.textContent = "Uploading & generating…";
      try {
        const res = await fetch("/upload", { method: "POST", body: data });
        if (!res.ok) throw new Error("Upload failed: " + res.status);
        const rec = await res.json();
        if (!rec || !rec.id) throw new Error("Upload succeeded but response is missing 'id'.");
        statusEl.textContent = "Done";
        statusEl.className = "ok";
        wireButtons(rec.id);
        // Keep selected model in the URL too (handy when reloading)
        const qs = new URLSearchParams({ recId: rec.id, model: modelSel.value }).toString();
        history.replaceState({}, "", "/?" + qs);
      } catch (err) {
        statusEl.textContent = err.message || String(err);
        statusEl.className = "warn";
      }
    });
  </script>
</body>
</html>
"""

# Root/home
@router.get("/", response_class=HTMLResponse)
def home(_: Request):
    return HTMLResponse(HOME_HTML)


# ------- JSON editor (shared) -------
JSON_EDITOR = r"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>__TITLE__</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    :root { --bg:#0f172a; --panel:#111827; --text:#e5e7eb; --muted:#9ca3af; }
    body{margin:0;background:var(--bg);color:var(--text);
      font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,"Helvetica Neue",Arial}
    header{padding:16px 20px;background:#0b1220;border-bottom:1px solid #1f2937;display:flex;justify-content:space-between;align-items:center}
    h1{margin:0;font-size:16px}
    main{padding:16px}
    .card{background:var(--panel);border:1px solid #1f2937;border-radius:12px;overflow:hidden}
    .toolbar{padding:10px;border-bottom:1px solid #1f2937;display:flex;gap:8px;align-items:center}
    button{border:1px solid #374151;background:#0b1220;color:var(--text);padding:8px 12px;border-radius:8px;cursor:pointer}
    button.primary{border-color:#14532d;background:#052e16}
    textarea{width:100%;height:70vh;padding:12px;border:0;outline:none;background:#0b1220;color:#e5e7eb;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13px;line-height:1.4}
    .status{padding:8px 12px;font-size:12px}
    .muted{color:var(--muted);font-size:12px}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>__TITLE__</h1>
      <div class="muted">Record: __REC_ID__</div>
    </div>
    <a href="/?recId=__REC_ID__" class="muted">← Back</a>
  </header>
  <main>
    <div class="card">
      <div class="toolbar">
        <button id="btn-pretty">Pretty-print</button>
        <button id="btn-compact">Compact</button>
        <button class="primary" id="btn-save">Save</button>
        <div id="status" class="status"></div>
      </div>
      <textarea id="editor" spellcheck="false">{}</textarea>
    </div>
  </main>
  <script>
    const endpoint = "__ENDPOINT__";
    const editor = document.getElementById("editor");
    const status = document.getElementById("status");
    function setStatus(msg, ok=false){ status.textContent = msg; status.style.color = ok ? "#86efac" : "#e5e7eb"; }
    async function loadJSON(){
      setStatus("Loading…");
      try{
        const res = await fetch(endpoint);
        if(!res.ok) throw new Error(`GET ${endpoint} -> ${res.status}`);
        const data = await res.json();
        editor.value = JSON.stringify(data, null, 2);
        setStatus("Loaded", true);
      }catch(e){ setStatus("Error: " + e.message); }
    }
    async function saveJSON(){
      setStatus("Saving…");
      try{
        const payload = JSON.parse(editor.value);
        const res = await fetch(endpoint, { method: "PATCH", headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload) });
        if(!res.ok) throw new Error(`PATCH ${endpoint} -> ${res.status}`);
        setStatus("Saved", true);
      }catch(e){ setStatus("Error: " + e.message); }
    }
    document.getElementById("btn-pretty").addEventListener("click", () => { try{ editor.value = JSON.stringify(JSON.parse(editor.value), null, 2);}catch{ setStatus("Invalid JSON"); }});
    document.getElementById("btn-compact").addEventListener("click", () => { try{ editor.value = JSON.stringify(JSON.parse(editor.value)); }catch{ setStatus("Invalid JSON"); }});
    document.getElementById("btn-save").addEventListener("click", saveJSON);
    loadJSON();
  </script>
</body>
</html>
"""

# ------- Rich document editor (editable form) -------
DOCUMENT_EDITOR = r"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>__TITLE__</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    :root { --bg:#0f172a; --panel:#111827; --text:#e5e7eb; --muted:#9ca3af; }
    body{margin:0;background:var(--bg);color:var(--text);
      font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,"Helvetica Neue",Arial}
    header{padding:16px 20px;background:#0b1220;border-bottom:1px solid #1f2937;display:flex;justify-content:space-between;align-items:center}
    h1{margin:0;font-size:18px}
    .muted{color:var(--muted);font-size:12px}
    main{padding:16px;max-width:980px;margin:0 auto}
    .status{padding:8px 0;font-size:12px}
    table{width:100%;border-collapse:collapse;margin-bottom:8px}
    th, td{border:1px solid #374151;padding:4px;color:var(--text);vertical-align:top}
    input[type="text"], input[type="number"], input[type="email"]{width:100%;background:#1f2937;border:1px solid #374151;color:var(--text);padding:4px;border-radius:4px}
    input[type="checkbox"]{transform:scale(1.2);}
    button{border:1px solid #374151;background:#0b1220;color:var(--text);padding:4px 8px;border-radius:6px;margin:2px;cursor:pointer}
    button.primary{border-color:#14532d;background:#052e16}
    ul{margin:0 0 8px 20px;padding:0}
    li{margin-bottom:4px}
  </style>
</head>
<body>
<header>
  <div>
    <h1>__TITLE__</h1>
    <div class="muted">Record: __REC_ID__</div>
  </div>
  <div>
    <button id="saveBtn" class="primary">Save</button>
    <a id="downloadDocx" href="__DOCX_ENDPOINT__" style="border:1px solid #374151;background:#0b1220;color:var(--text);padding:4px 8px;border-radius:6px;margin-left:12px;text-decoration:none">Download Word</a>
    <a href="/?recId=__REC_ID__" class="muted" style="margin-left:12px">← Back</a>
  </div>
</header>
<main>
  <div id="status" class="status"></div>
  <div id="editor"></div>
</main>
<script>
const endpoint = "__ENDPOINT__";
let jsonData = null;

function setStatus(msg, ok=false) {
  const st = document.getElementById('status');
  st.textContent = msg;
  st.style.color = ok ? '#86efac' : '#e5e7eb';
}

// Retrieve nested value given a dot/bracket path string
function getNested(obj, path) {
  if (!path) return obj;
  const parts = path.split('.');
  let current = obj;
  for (let i=0; i<parts.length; i++) {
    let part = parts[i];
    const m = part.match(/(.+)\[(\d+)\]/);
    if (m) {
      const key = m[1];
      const idx = parseInt(m[2]);
      current = current[key];
      current = current[idx];
    } else {
      current = current[part];
    }
    if (current === undefined) return undefined;
  }
  return current;
}

// Set nested value given a dot/bracket path string
function setValue(obj, path, value) {
  const parts = path.split('.');
  let current = obj;
  for (let i=0; i<parts.length; i++) {
    let part = parts[i];
    const m = part.match(/(.+)\[(\d+)\]/);
    if (m) {
      const key = m[1];
      const idx = parseInt(m[2]);
      if (!current[key]) current[key] = [];
      if (i === parts.length - 1) {
        current[key][idx] = value;
        return;
      } else {
        if (!current[key][idx]) current[key][idx] = {};
        current = current[key][idx];
      }
    } else {
      if (i === parts.length - 1) {
        current[part] = value;
        return;
      } else {
        if (!current[part]) current[part] = {};
        current = current[part];
      }
    }
  }
}

// Build UI recursively
function buildUI(data, path, container) {
  if (data === null || typeof data === 'string' || typeof data === 'number' || typeof data === 'boolean') {
    createPrimitive(path, data, container);
  } else if (Array.isArray(data)) {
    let first = null;
    for (let i=0; i<data.length; i++) {
      if (data[i] !== null && data[i] !== undefined) { first = data[i]; break; }
    }
    if (first !== null && typeof first === 'object' && !Array.isArray(first)) {
      createArrayObject(path, data, container);
    } else {
      createArrayPrimitive(path, data, container);
    }
  } else if (typeof data === 'object') {
    createObject(path, data, container);
  }
}

// Render primitive values (string, number, boolean, null)
function createPrimitive(path, value, container) {
  const input = document.createElement('input');
  if (typeof value === 'number') {
    input.type = 'number';
    if (value !== null) input.value = value;
  } else if (typeof value === 'boolean') {
    input.type = 'checkbox';
    input.checked = Boolean(value);
  } else {
    input.type = 'text';
    input.value = value ?? '';
  }
  input.addEventListener('input', (e) => {
    if (input.type === 'number') {
      const v = e.target.value === '' ? null : Number(e.target.value);
      setValue(jsonData, path, v);
    } else if (input.type === 'checkbox') {
      // handled on change
    } else {
      setValue(jsonData, path, e.target.value);
    }
  });
  if (input.type === 'checkbox') {
    input.addEventListener('change', (e) => {
      setValue(jsonData, path, e.target.checked);
    });
  }
  container.appendChild(input);
}

// Render array of primitive values
function createArrayPrimitive(path, arr, container) {
  container.innerHTML = '';
  const list = document.createElement('ul');
  list.style.listStyle = 'disc';
  list.style.marginLeft = '20px';
  arr.forEach((val, idx) => {
    const li = document.createElement('li');
    const input = document.createElement('input');
    input.type = 'text';
    input.value = val ?? '';
    input.addEventListener('input', (e) => {
      setValue(jsonData, path + '[' + idx + ']', e.target.value);
    });
    li.appendChild(input);
    const del = document.createElement('button');
    del.textContent = '✕';
    del.style.marginLeft = '4px';
    del.addEventListener('click', () => {
      const arrRef = getNested(jsonData, path);
      arrRef.splice(idx, 1);
      createArrayPrimitive(path, arrRef, container);
    });
    li.appendChild(del);
    list.appendChild(li);
  });
  const addBtn = document.createElement('button');
  addBtn.textContent = 'Add Item';
  addBtn.addEventListener('click', () => {
    const arrRef = getNested(jsonData, path);
    arrRef.push('');
    createArrayPrimitive(path, arrRef, container);
  });
  container.appendChild(list);
  container.appendChild(addBtn);
}

// Render array of objects as editable table
function createArrayObject(path, arr, container) {
  container.innerHTML = '';
  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const trh = document.createElement('tr');
  const keys = [];
  arr.forEach(obj => {
    if (obj) {
      Object.keys(obj).forEach(k => {
        if (!keys.includes(k)) keys.push(k);
      });
    }
  });
  keys.forEach(k => {
    const th = document.createElement('th');
    th.textContent = k;
    trh.appendChild(th);
  });
  const thAction = document.createElement('th');
  thAction.textContent = '';
  trh.appendChild(thAction);
  thead.appendChild(trh);
  table.appendChild(thead);
  const tbody = document.createElement('tbody');
  arr.forEach((rowObj, idx) => {
    const tr = document.createElement('tr');
    keys.forEach(k => {
      const td = document.createElement('td');
      const input = document.createElement('input');
      input.type = 'text';
      const val = rowObj ? rowObj[k] : '';
      input.value = val ?? '';
      input.addEventListener('input', (e) => {
        setValue(jsonData, path + '[' + idx + '].' + k, e.target.value);
      });
      td.appendChild(input);
      tr.appendChild(td);
    });
    const tdDel = document.createElement('td');
    const delBtn = document.createElement('button');
    delBtn.textContent = 'Delete';
    delBtn.addEventListener('click', () => {
      const arrRef = getNested(jsonData, path);
      arrRef.splice(idx, 1);
      createArrayObject(path, arrRef, container);
    });
    tdDel.appendChild(delBtn);
    tr.appendChild(tdDel);
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  container.appendChild(table);
  const addBtn = document.createElement('button');
  addBtn.textContent = 'Add Row';
  addBtn.addEventListener('click', () => {
    const arrRef = getNested(jsonData, path);
    const newObj = {};
    keys.forEach(k => { newObj[k] = ''; });
    arrRef.push(newObj);
    createArrayObject(path, arrRef, container);
  });
  container.appendChild(addBtn);
}

// Render an object (dictionary) as nested sections
function createObject(path, obj, container) {
  const keys = Object.keys(obj || {});
  keys.forEach(key => {
    const value = obj[key];
    const section = document.createElement('div');
    section.style.marginBottom = '12px';
    const label = document.createElement('div');
    label.textContent = key;
    label.style.fontWeight = 'bold';
    label.style.marginBottom = '4px';
    section.appendChild(label);
    buildUI(value, path ? (path + '.' + key) : key, section);
    container.appendChild(section);
  });
}

async function load() {
  setStatus('Loading…');
  try {
    const res = await fetch(endpoint);
    if (!res.ok) throw new Error('GET failed: ' + res.status);
    jsonData = await res.json();
    const editor = document.getElementById('editor');
    editor.innerHTML = '';
    buildUI(jsonData, '', editor);
    setStatus('Loaded', true);
  } catch (e) {
    setStatus('Error: ' + e.message);
  }
}

async function save() {
  setStatus('Saving…');
  try {
    const res = await fetch(endpoint, { method:'PATCH', headers:{'Content-Type':'application/json'}, body: JSON.stringify(jsonData) });
    if (!res.ok) throw new Error('PATCH failed: ' + res.status);
    setStatus('Saved', true);
  } catch (e) {
    setStatus('Error: ' + e.message);
  }
}

document.getElementById('saveBtn').addEventListener('click', save);
load();
</script>
</body>
</html>
"""

def _render_editor(title: str, rec_id: str, endpoint: str) -> HTMLResponse:
    html = (
        JSON_EDITOR
        .replace("__TITLE__", title)
        .replace("__REC_ID__", rec_id)
        .replace("__ENDPOINT__", endpoint)
    )
    return HTMLResponse(html)

# New helper to render the structured document editor
def _render_document_editor(title: str, rec_id: str, endpoint: str, docx_endpoint: str) -> HTMLResponse:
    """
    Render the rich document editor by injecting the JSON fetch endpoint and DOCX download link.

    Args:
        title: Displayed page title.
        rec_id: Record identifier.
        endpoint: API endpoint to GET/PATCH JSON for this document.
        docx_endpoint: API endpoint to GET the Word document (.docx).

    Returns:
        HTMLResponse with the populated template.
    """
    html = (
        DOCUMENT_EDITOR
        .replace("__TITLE__", title)
        .replace("__REC_ID__", rec_id)
        .replace("__ENDPOINT__", endpoint)
        .replace("__DOCX_ENDPOINT__", docx_endpoint)
    )
    return HTMLResponse(html)

@router.get("/ui/returnables_json/{rec_id}")
def ui_returnables_json(rec_id: str):
    _ = load_record(rec_id)
    return _render_editor("Returnables JSON", rec_id, f"/records/{rec_id}/returnables_json")

@router.get("/ui/rft_json/{rec_id}")
def ui_rft_json(rec_id: str):
    _ = load_record(rec_id)
    return _render_editor("RFT JSON", rec_id, f"/records/{rec_id}/rft_json")

@router.get("/ui/tepp_json/{rec_id}")
def ui_tepp_json(rec_id: str):
    _ = load_record(rec_id)
    return _render_editor("TEPP JSON", rec_id, f"/records/{rec_id}/tepp_json")

# ---------- Routes for pretty document UIs ----------

@router.get("/ui/returnables/{rec_id}")
def ui_returnables_pretty(rec_id: str):
    """Render the Returnable Schedules document as an editable form."""
    _ = load_record(rec_id)
    return _render_document_editor(
        "Returnable Schedules",
        rec_id,
        f"/records/{rec_id}/returnables_json",
        f"/records/{rec_id}/returnables_docx",
    )

@router.get("/ui/rft/{rec_id}")
def ui_rft_pretty(rec_id: str):
    """Render the Request for Tender document as an editable form."""
    _ = load_record(rec_id)
    return _render_document_editor(
        "Request for Tender",
        rec_id,
        f"/records/{rec_id}/rft_json",
        f"/records/{rec_id}/rft_docx",
    )

@router.get("/ui/tepp/{rec_id}")
def ui_tepp_pretty(rec_id: str):
    """Render the TEPP document as an editable form."""
    _ = load_record(rec_id)
    return _render_document_editor(
        "Tender Evaluation & Probity Plan",
        rec_id,
        f"/records/{rec_id}/tepp_json",
        f"/records/{rec_id}/tepp_docx",
    )
