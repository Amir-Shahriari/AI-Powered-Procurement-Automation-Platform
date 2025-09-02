from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse
from ..repo.records import load_record

router = APIRouter()

# ------------------------------
# Home (Lit: <ait-home/>)
# ------------------------------
HOME_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>AIT – Spec Intake</title>
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <style>
    /* Page background so there's no flash before Lit renders */
    html,body{height:100%}
    body{margin:0;background:#0f172a;color:#e5e7eb;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,"Helvetica Neue",Arial}
    /* Skip link */
    .skip{position:absolute;left:-9999px;top:auto;width:1px;height:1px;overflow:hidden}
    .skip:focus{position:static;width:auto;height:auto;padding:8px 12px;background:#1f2937;border-radius:8px;color:#fff}
  </style>
  <script type="module">
    import {LitElement, html, css, nothing, unsafeCSS} from "https://unpkg.com/lit@3/index.js?module";

    const ui = {
      bg:"#0f172a", panel:"#101826", border:"#223048", text:"#e5e7eb", muted:"#9ca3af",
      header:"#0b1220", btn:"#0b1220", btnBorder:"#374151", ok:"#86efac", warn:"#fbbf24"
    };

    class AitChip extends LitElement{
      static properties = { kind:{type:String}, text:{type:String} };
      static styles = css`
        :host{display:inline-flex;align-items:center;border-radius:999px;border:1px solid var(--border,#374151);padding:.4rem .7rem;font:13px/1.25 ui-sans-serif,system-ui}
        :host([kind="ok"]){color:${unsafeCSS(ui.ok)};border-color:${unsafeCSS(ui.ok)}33}
        :host([kind="warn"]){color:${unsafeCSS(ui.warn)};border-color:${unsafeCSS(ui.warn)}33}
        :host([kind="muted"]){color:${unsafeCSS(ui.muted)}}
      `;
      constructor(){ super(); this.setAttribute("role","status"); this.setAttribute("aria-live","polite"); }
      render(){ return html`${this.text||""}`; }
    }
    customElements.define("ait-chip", AitChip);

    class AitHome extends LitElement{
      static properties = {
        recId: {type:String, reflect:true, attribute:"rec-id"},
        model: {type:String},
        teppReady: {type:Boolean},
        isEvaluating: {type:Boolean}
      };
      static styles = css`
        :host{display:block;background:${unsafeCSS(ui.bg)};color:${unsafeCSS(ui.text)}}
        header{padding:18px 20px;background:${unsafeCSS(ui.header)};border-bottom:1px solid ${unsafeCSS(ui.border)}}
        h1{margin:0;font-size:20px}
        main{padding:16px;max-width:980px;margin:0 auto}
        .card{background:${unsafeCSS(ui.panel)};border:1px solid ${unsafeCSS(ui.border)};border-radius:14px;padding:16px}
        .row{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
        select,input[type=file],button,input[type=submit]{border:1px solid ${unsafeCSS(ui.btnBorder)};background:${unsafeCSS(ui.btn)};color:${unsafeCSS(ui.text)};padding:10px 14px;border-radius:10px;cursor:pointer;font-size:14px}
        a.btn{display:inline-block;text-decoration:none;border:1px solid ${unsafeCSS(ui.btnBorder)};background:${unsafeCSS(ui.btn)};color:${unsafeCSS(ui.text)};padding:10px 14px;border-radius:10px}
        .muted{color:${unsafeCSS(ui.muted)}}
        .spacer{height:12px}
        .grid{display:grid;grid-template-columns:1fr;gap:12px}
        @media(min-width:720px){.grid{grid-template-columns:1fr 1fr 1fr}}
        .stack{display:flex;flex-direction:column;gap:12px}
        .tight{gap:10px}
        /* High-visibility focus ring */
        :where(a,button,input,select):focus-visible{outline:3px solid ${unsafeCSS(ui.warn)};outline-offset:2px}
      `;
      constructor(){
        super();
        const qs = new URLSearchParams(location.search);
        this.recId = qs.get("recId") || "";
        this.model = qs.get("model") || "llama3.1:8b";
        this.teppReady = false;
        this.isEvaluating = false;
      }
      firstUpdated(){
        this.renderRoot?.querySelector('input[type="file"]')?.focus();
        if(this.recId) this.refreshTeppReady();
      }
      updated(changed){
        if(changed.has("recId")) this.refreshTeppReady();
      }
      get _status(){ return this.renderRoot?.getElementById("status"); }
      setStatus(msg, kind="muted"){
        const chip = this._status;
        if(!chip) return;
        chip.setAttribute("kind", kind);
        chip.text = msg;
        chip.requestUpdate();
      }
      async onSubmit(e){
        e.preventDefault();
        const form = e.currentTarget;
        const data = new FormData(form);
        this.setStatus("Uploading & generating…","muted");
        try{
          const res = await fetch("/upload",{method:"POST",body:data});
          if(!res.ok) throw new Error("Upload failed: "+res.status);
          const rec = await res.json();
          if(!rec?.id) throw new Error("Upload succeeded but response missing 'id'");
          this.recId = rec.id;
          const qs = new URLSearchParams({ recId: this.recId, model: this.model }).toString();
          history.replaceState({}, "", "/?"+qs);
          this.setStatus("Done","ok");
        }catch(err){
          this.setStatus(err.message || String(err), "warn");
        }
      }
      async submitSupplier(){
        const status = this.renderRoot?.getElementById("supplierStatus");
        const files = this.renderRoot?.getElementById("supplierFiles")?.files;
        if(!this.recId){ status.setAttribute("kind","warn"); status.text="No record selected."; status.requestUpdate(); return; }
        if(!files || files.length===0){ status.setAttribute("kind","warn"); status.text="Please select file(s) first."; status.requestUpdate(); return; }
        const form = new FormData();
        [...files].forEach(f=>form.append("files", f));
        status.setAttribute("kind","muted"); status.text="Uploading…"; status.requestUpdate();
        try{
          const res = await fetch(`/records/${this.recId}/supplier_responses`,{method:"POST",body:form});
          if(!res.ok) throw new Error(`Upload failed: ${res.status}`);
          status.setAttribute("kind","ok"); status.text="Supplier responses processed."; status.requestUpdate();
        }catch(err){
          status.setAttribute("kind","warn"); status.text = err.message || String(err); status.requestUpdate();
        }
      }
      async refreshTeppReady(){
        if(!this.recId){ this.teppReady=false; return; }
        try{
          const res = await fetch(`/records/${this.recId}/tepp_json`);
          this.teppReady = res.ok;
        }catch{ this.teppReady = false; }
      }
      async evaluateAll(){
        const chip = this.renderRoot?.getElementById("evalStatus");
        if(!this.recId) return;
        this.isEvaluating = true;
        if(chip){ chip.setAttribute("kind","muted"); chip.text="Generating evaluation…"; chip.requestUpdate(); }
        try{
          const res = await fetch(`/records/${this.recId}/evaluate_suppliers`, { method: "POST" });
          if(!res.ok) throw new Error("Failed to generate evaluation: "+res.status);
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `${this.recId}_evaluation.xlsx`;
          document.body.appendChild(a);
          a.click();
          a.remove();
          URL.revokeObjectURL(url);
          if(chip){ chip.setAttribute("kind","ok"); chip.text="Evaluation generated."; chip.requestUpdate(); }
        }catch(err){
          if(chip){ chip.setAttribute("kind","warn"); chip.text = err.message || String(err); chip.requestUpdate(); }
        }finally{
          this.isEvaluating = false;
        }
      }
      renderAfter(){
        if(!this.recId) return nothing;
        return html`
          <div class="spacer"></div>
          <div class="stack" aria-labelledby="recordHeading">
            <div id="recordHeading" class="muted">Record: <span>${this.recId}</span></div>
            <div class="grid" role="navigation" aria-label="Record sections">
              <a class="btn" href=${`/ui/returnables/${this.recId}`} aria-label="Open Returnables for record ${this.recId}">Open Returnables</a>
              <a class="btn" href=${`/ui/rft/${this.recId}`} aria-label="Open Request for Tender for record ${this.recId}">Open RFT</a>
              <a class="btn" href=${`/ui/tepp/${this.recId}`} aria-label="Open Tender Evaluation and Probity Plan for record ${this.recId}">Open TEPP</a>
            </div>

            <!-- Evaluate All appears only once TEPP exists -->
            ${this.teppReady ? html`
              <div class="row tight" style="align-items:center;" role="group" aria-label="Evaluation actions">
                <button class="primary"
                        ?disabled=${this.isEvaluating}
                        aria-disabled=${this.isEvaluating?'true':'false'}
                        @click=${this.evaluateAll}
                        title="Generate the evaluation workbook for all suppliers">
                  ${this.isEvaluating ? "Working…" : "Evaluate All Suppliers"}
                </button>
                <ait-chip id="evalStatus" kind="muted"></ait-chip>
              </div>
            ` : html`
              <div class="muted" role="note">Populate TEPP to enable the “Evaluate All Suppliers” action.</div>
            `}

            <div class="row tight" style="align-items:center;">
              <label class="muted" for="supplierFiles">Supplier responses:</label>
              <input id="supplierFiles" type="file" multiple aria-describedby="supplierHelp" />
              <button @click=${this.submitSupplier} aria-describedby="supplierHelp">Submit Supplier Responses</button>
              <ait-chip id="supplierStatus" kind="muted" aria-live="polite"></ait-chip>
            </div>
            <div id="supplierHelp" class="muted">Upload one or more supplier returnable schedules; we’ll attach each to the record.</div>
          </div>
        `;
      }
      render(){
        return html`
          <a href="#main" class="skip">Skip to main content</a>
          <header role="banner"><h1>AIT – Spec Intake</h1></header>
          <main id="main" role="main">
            <div class="card">
              <form class="row" @submit=${this.onSubmit} enctype="multipart/form-data" aria-describedby="genHelp">
                <label class="muted" for="model">Model</label>
                <select id="model" name="model" required @change=${(e)=>{this.model=e.target.value;}}>
                  <option value="llama3.1:8b" ?selected=${this.model==="llama3.1:8b"}>llama3.1:8b</option>
                  <option value="llama3:latest" ?selected=${this.model==="llama3:latest"}>llama3:latest</option>
                  <option value="mistral:latest" ?selected=${this.model==="mistral:latest"}>mistral:latest</option>
                </select>
                <input type="file" name="file" required aria-label="Upload input file to generate record" />
                <input type="submit" value="Generate" />
                <ait-chip id="status" kind="muted"></ait-chip>
              </form>
              <div id="genHelp" class="muted">Choose a model and a source file to generate the record, then use the links below.</div>
              ${this.renderAfter()}
            </div>
          </main>
        `;
      }
    }
    customElements.define("ait-home", AitHome);
  </script>
</head>
<body>
  <ait-home></ait-home>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
def home(_: Request):
    return HTMLResponse(HOME_HTML)


# ------------------------------
# Shared JSON editor (Lit: <ait-json-editor/>)
# ------------------------------
JSON_EDITOR = r"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>__TITLE__</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>html,body{height:100%}body{margin:0;background:#0f172a;color:#e5e7eb;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,"Helvetica Neue",Arial}</style>
  <script type="module">
    import {LitElement, html, css, unsafeCSS} from "https://unpkg.com/lit@3/index.js?module";

    const ui = {
      bg:"#0f172a", panel:"#101826", border:"#223048", text:"#e5e7eb", muted:"#9ca3af",
      header:"#0b1220", btn:"#0b1220", btnBorder:"#374151", ok:"#86efac"
    };

    class AitJsonEditor extends LitElement{
      static properties = {
        title:{type:String}, recId:{type:String, attribute:"rec-id"}, endpoint:{type:String},
        value:{state:true}, status:{state:true}, statusOk:{state:true}
      };
      static styles = css`
        :host{display:block;color:${unsafeCSS(ui.text)}}
        header{padding:16px 20px;background:${unsafeCSS(ui.header)};border-bottom:1px solid ${unsafeCSS(ui.border)};display:flex;justify-content:space-between;align-items:center}
        h1{margin:0;font-size:16px}
        .muted{color:${unsafeCSS(ui.muted)};font-size:12px}
        main{padding:16px}
        .card{background:${unsafeCSS(ui.panel)};border:1px solid ${unsafeCSS(ui.border)};border-radius:12px;overflow:hidden}
        .toolbar{padding:10px;border-bottom:1px solid ${unsafeCSS(ui.border)};display:flex;gap:8px;align-items:center}
        button{border:1px solid ${unsafeCSS(ui.btnBorder)};background:${unsafeCSS(ui.btn)};color:${unsafeCSS(ui.text)};padding:8px 12px;border-radius:8px;cursor:pointer}
        button.primary{border-color:#14532d;background:#052e16}
        textarea{width:100%;height:70vh;padding:12px;border:0;outline:none;background:#0b1220;color:${unsafeCSS(ui.text)};font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13px;line-height:1.4;box-sizing:border-box}
        .status{padding:8px 12px;font-size:12px;color:${unsafeCSS(ui.text)}}
        .ok{color:${unsafeCSS(ui.ok)}}
      `;
      constructor(){ super(); this.value=""; this.status=""; this.statusOk=false; }
      firstUpdated(){ this.load(); document.title = this.title; }
      setStatus(msg, ok=false){ this.status = msg; this.statusOk = ok; }
      async load(){
        this.setStatus("Loading…");
        try{
          const res = await fetch(this.endpoint);
          if(!res.ok) throw new Error(`GET ${this.endpoint} -> ${res.status}`);
          const data = await res.json();
          this.value = JSON.stringify(data, null, 2);
          this.setStatus("Loaded", true);
        }catch(e){ this.setStatus("Error: " + e.message); }
      }
      async save(){
        this.setStatus("Saving…");
        try{
          const payload = JSON.parse(this.value);
          const res = await fetch(this.endpoint, { method: "PATCH", headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload) });
          if(!res.ok) throw new Error(`PATCH ${this.endpoint} -> ${res.status}`);
          this.setStatus("Saved", true);
        }catch(e){ this.setStatus("Error: " + e.message); }
      }
      render(){
        return html`
          <header>
            <div>
              <h1>${this.title}</h1>
              <div class="muted">Record: ${this.recId}</div>
            </div>
            <a href="/?recId=${this.recId}" class="muted">← Back</a>
          </header>
          <main>
            <div class="card">
              <div class="toolbar">
                <button @click=${()=>{ try{ this.value = JSON.stringify(JSON.parse(this.value), null, 2);}catch{ this.setStatus("Invalid JSON"); } }}>Pretty-print</button>
                <button @click=${()=>{ try{ this.value = JSON.stringify(JSON.parse(this.value)); }catch{ this.setStatus("Invalid JSON"); } }}>Compact</button>
                <button class="primary" @click=${this.save}>Save</button>
                <div class="status" style=${this.statusOk?'color:'+ui.ok:''}>${this.status}</div>
              </div>
              <textarea .value=${this.value} @input=${(e)=>{ this.value = e.target.value; }} spellcheck="false"></textarea>
            </div>
          </main>
        `;
      }
    }
    customElements.define("ait-json-editor", AitJsonEditor);
  </script>
</head>
<body>
  <ait-json-editor title="__TITLE__" rec-id="__REC_ID__" endpoint="__ENDPOINT__"></ait-json-editor>
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


# ------------------------------
# Rich document editor (Lit: <ait-doc-editor/>)
# ------------------------------
DOCUMENT_EDITOR = r"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>__TITLE__</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
      /* colour palette reused from the JSON editor */
      :root {
        --bg:#0f172a;
        --panel:#111827;
        --text:#e5e7eb;
        --muted:#9ca3af;
      }
      /* page layout */
      body{
        margin:0;
        background:var(--bg);
        color:var(--text);
        font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,Noto Sans,"Helvetica Neue",Arial;
      }
      header{
        padding:16px 20px;
        background:#0b1220;
        border-bottom:1px solid #1f2937;
        display:flex;
        justify-content:space-between;
        align-items:center;
      }
      h1{
        margin:0;
        font-size:20px;
      }
      .muted{
        color:var(--muted);
        font-size:12px;
      }
      main{
        padding:16px;
        max-width:980px;
        margin:0 auto;
      }
      .status{
        padding:8px 0;
        font-size:12px;
      }
      /* headlining for nested sections */
      h2, h3, h4, h5, h6{
        margin-top:16px;
        margin-bottom:8px;
        font-weight:600;
        color:var(--text);
      }
      /* section wrapper to control spacing */
      .section{
        margin-bottom:16px;
      }
      /* table styling for arrays of objects */
      table{
        width:100%;
        border-collapse:collapse;
        margin-bottom:16px;
      }
      th, td{
        border:1px solid #374151;
        padding:6px;
        vertical-align:top;
      }
      th{
        background-color:#1f2937;
        color:var(--text);
        text-align:left;
      }
      td{
        color:var(--text);
      }
      input[type="text"], input[type="number"], input[type="email"]{
        width:100%;
        box-sizing:border-box;
        background:#1f2937;
        border:1px solid #374151;
        color:var(--text);
        padding:6px;
        border-radius:4px;
      }
      input[type="checkbox"]{
        transform:scale(1.2);
        margin-right:8px;
      }
      button{
        border:1px solid #374151;
        background:#0b1220;
        color:var(--text);
        padding:6px 10px;
        border-radius:6px;
        margin:2px;
        cursor:pointer;
      }
      button.primary{
        border-color:#14532d;
        background:#052e16;
      }
      /* custom list styling for arrays of primitives */
      ul.custom-list{
        list-style-type:disc;
        margin-left:20px;
        margin-bottom:8px;
        padding:0;
      }
      ul.custom-list li{
        margin-bottom:4px;
      }
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
function buildUI(data, path, container, level = 2) {
  if (data === null || typeof data === 'string' || typeof data === 'number' || typeof data === 'boolean') {
    createPrimitive(path, data, container);
  } else if (Array.isArray(data)) {
    let first = null;
    for (let i=0; i<data.length; i++) {
      if (data[i] !== null && data[i] !== undefined) { first = data[i]; break; }
    }
    if (first !== null && typeof first === 'object' && !Array.isArray(first)) {
      createArrayObject(path, data, container, level);
    } else {
      createArrayPrimitive(path, data, container, level);
    }
  } else if (typeof data === 'object') {
    createObject(path, data, container, level);
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
function createArrayPrimitive(path, arr, container, level) {
  container.innerHTML = '';
  const list = document.createElement('ul');
  list.className = 'custom-list';
  
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
function createArrayObject(path, arr, container, level) {
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
function createObject(path, obj, container, level) {
  const keys = Object.keys(obj || {});
  keys.forEach(key => {
    const value = obj[key];
    const section = document.createElement('div');
    section.className = "section";
    const headingLevel = Math.min(level, 6);
    const heading = document.createElement('h' + headingLevel);
    const displayKey = key.replace(/_/g, " " ).replace(/\b\w/g, (c) => c.toUpperCase());
    heading.textContent = displayKey;
    section.appendChild(heading);
    buildUI(value, path ? (path + '.' + key) : key, section, level + 1);
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
    buildUI(jsonData, '', editor, 2);
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


def _render_document_editor(title: str, rec_id: str, endpoint: str, docx_endpoint: str) -> HTMLResponse:
    html = (
        DOCUMENT_EDITOR
        .replace("__TITLE__", title)
        .replace("__REC_ID__", rec_id)
        .replace("__ENDPOINT__", endpoint)
        .replace("__DOCX_ENDPOINT__", docx_endpoint)
    )
    return HTMLResponse(html)

# ---------- JSON editor routes ----------
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

# ---------- Pretty document routes ----------
@router.get("/ui/returnables/{rec_id}")
def ui_returnables_pretty(rec_id: str):
    _ = load_record(rec_id)
    return _render_document_editor(
        "Returnable Schedules",
        rec_id,
        f"/records/{rec_id}/returnables_json",
        f"/records/{rec_id}/returnables_docx",
    )

@router.get("/ui/rft/{rec_id}")
def ui_rft_pretty(rec_id: str):
    _ = load_record(rec_id)
    return _render_document_editor(
        "Request for Tender",
        rec_id,
        f"/records/{rec_id}/rft_json",
        f"/records/{rec_id}/rft_docx",
    )

@router.get("/ui/tepp/{rec_id}")
def ui_tepp_pretty(rec_id: str):
    _ = load_record(rec_id)
    return _render_document_editor(
        "Tender Evaluation & Probity Plan",
        rec_id,
        f"/records/{rec_id}/tepp_json",
        f"/records/{rec_id}/tepp_docx",
    )
