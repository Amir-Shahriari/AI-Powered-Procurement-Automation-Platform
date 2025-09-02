"""
Streamlit user interface for generating tender documents.

This app provides a clean, two-step UX:
  1) Home: pick an Ollama model.
  2) Upload: upload a spec, generate documents → redirect to Results.
  3) Results: view the criteria table, edit the TEPP JSON, and download TEPP/Returnables.

Run:
    streamlit run app/streamlit_app.py
"""
import os, sys
from pathlib import Path
from typing import List, Dict
import uuid
import json
import subprocess
import requests
import pandas as pd
import streamlit as st

# Ensure the project root (the parent of 'app') is on sys.path when run by Streamlit
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- App imports ---
from app.deps import SPLITTER
from app.config import settings
from app.schemas import SpecSummary
from app.services.textio import extract_text, chunks
from app.services.vectorstores import build_index, get_vs
from app.services.llm import rag_json, set_runtime_model, reset_runtime_model
from app.services.parse_spec import parse_spec
from app.services.policy import scan_policy_files, extract_many, _build_ephemeral_vs
from app.services.compose import compose_tepp, compose_returnable_schedules
from app.services.docx_export import export_json_to_docx

# ---- Prompt (same as API) ----
SPEC_SUMMARY_PROMPT = """You summarise government engineering tender specifications.
Return ONLY strict JSON with fields:
{
  "title": null|string,
  "tender_no": null|string,
  "contract_no": null|string,
  "closing_datetime": null|string,
  "contact": {"name": null|string, "email": null|string, "phone": null|string},
  "scope": [string,...],
  "location": null|string,
  "safety_standards": [string,...]
}
Use ONLY the provided context. If unknown, set null or [].
"""

# ==========================
# Helpers
# ==========================
def _coerce_to_text(x) -> str:
    """Return a plain string for any input (dict/list/bytes/None/etc.)."""
    if x is None:
        return ""
    if isinstance(x, (bytes, bytearray)):
        try:
            return x.decode("utf-8", "ignore")
        except Exception:
            return str(x)
    if isinstance(x, dict):
        # Prefer common text keys if present
        for k in ("text", "content", "body", "value"):
            if k in x:
                return _coerce_to_text(x[k])
        # Fallback to JSON
        try:
            return json.dumps(x, ensure_ascii=False)
        except Exception:
            return str(x)
    if isinstance(x, (list, tuple)):
        # Join lists of strings as lines
        try:
            return "\n".join(_coerce_to_text(i) for i in x)
        except Exception:
            return str(x)
    return str(x)


def list_ollama_models(base_url: str) -> list[str]:
    """
    Return a list of model names available in the local Ollama registry.
    Try REST first (/api/tags), then CLI. CLI fallback parses the default table
    so it works on older Ollama versions without --format json.
    """
    # 1) REST
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=3)
        resp.raise_for_status()
        data = resp.json() or {}
        models = []
        for m in data.get("models", []):
            n = (m.get("name") or m.get("model") or "").strip()
            if n:
                models.append(n)
        if models:
            return sorted(dict.fromkeys(models))
    except Exception:
        pass
    # 2) CLI JSON
    try:
        out = subprocess.check_output(["ollama", "list", "--format", "json"], text=True, timeout=3)
        arr = json.loads(out)
        models = [row.get("name") for row in arr if row.get("name")]
        if models:
            return sorted(dict.fromkeys(models))
    except Exception:
        pass
    # 3) CLI table
    try:
        out = subprocess.check_output(["ollama", "list"], text=True, timeout=3)
        lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
        if lines and lines[0].lower().startswith("name"):  # header
            lines = lines[1:]
        models = []
        for ln in lines:
            parts = ln.split()
            if parts:
                models.append(parts[0])
        return sorted(dict.fromkeys(models))
    except Exception:
        return []

def _generate_documents(file_path: Path, model: str) -> Dict[str, Dict]:
    """Core pipeline: extract → index → summarise/parse → compose TEPP/Returnables."""
    doc_id = str(uuid.uuid4())
    suffix = file_path.suffix or ".bin"
    temp_path = settings.DATA_DIR / f"{doc_id}{suffix}"
    with open(file_path, "rb") as src, open(temp_path, "wb") as dst:
        dst.write(src.read())

    # 1) Extract and coerce to string
    text_raw = extract_text(temp_path)
    text = _coerce_to_text(text_raw)
    if not text or not text.strip():
        raise ValueError("Could not read text from the document.")

    # 2) Build vector store
    chs = chunks(text)  # expects a str; now guaranteed
    build_index(doc_id, chs)
    vs = get_vs(doc_id)

    # 3) Run with selected model
    token = set_runtime_model(model)
    try:
        summary_json = rag_json(
            vs,
            SPEC_SUMMARY_PROMPT,
            [
                "tender title or document title",
                "tender number or contract number",
                "closing date and time",
                "contact name email phone",
                "scope of works",
                "location site",
                "safety standards ADR WHS ISO Australian Standards",
            ],
            max_ctx=8,
            min_chars=2000,
        )
        spec_summary = SpecSummary.model_validate(summary_json)

        parsed = parse_spec(text)

        # 4) Optional policies → ephemeral VS (coerce each to str)
        policy_files = scan_policy_files()
        policy_texts = extract_many(policy_files)
        policy_chunks: List[str] = []
        if policy_texts:
            for t in policy_texts:
                s = _coerce_to_text(t)
                if s.strip():
                    policy_chunks.extend(SPLITTER.split_text(s))
        vs_policy = _build_ephemeral_vs(policy_chunks) if policy_chunks else None

        # 5) Compose TEPP + Returnables
        tepp = compose_tepp(spec_summary, parsed, vs, [vs_policy] if vs_policy else None)
        returnables = compose_returnable_schedules(spec_summary, parsed, non_negotiable_date=None)

        return {
            "spec_summary": spec_summary.model_dump(),
            "parsed": parsed,
            "tepp": tepp,
            "returnables": returnables,
        }
    finally:
        reset_runtime_model(token)


def _inject_css():
    """Read and inject external CSS file."""
    # default location: app/ui/theme.css (sibling folder `ui` next to this file)
    default_path = Path(__file__).parent / "ui" / "theme.css"
    css_path_str = os.getenv("APP_THEME_CSS", str(default_path))
    css_path = Path(css_path_str)
    try:
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Could not read CSS at {css_path}: {e}")

def _nav_set(view: str, extra: Dict[str, str] | None = None):
    """Set view in query params and trigger rerun."""
    payload = dict(st.query_params)
    # Flatten list values from previous state
    for k, v in list(payload.items()):
        if isinstance(v, list) and v:
            payload[k] = v[0]
    payload["view"] = view
    if extra:
        payload.update(extra)
    st.query_params.clear()
    st.query_params.update(payload)


# ---------- Pretty helpers ----------
def _pretty(label: str) -> str:
    return label.replace("_", " ").replace("-", " ").title()

def _is_uniform_dict_list(xs: list) -> bool:
    if not xs or not all(isinstance(x, dict) for x in xs):
        return False
    keys = [tuple(sorted(x.keys())) for x in xs if isinstance(x, dict)]
    return len(set(keys)) == 1

def _edit_table(records: list[dict], key: str, caption: str | None = None) -> list[dict]:
    import pandas as pd
    df = pd.DataFrame(records) if records else pd.DataFrame([{}])
    edited = st.data_editor(
        df,
        key=key,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
    )
    if caption:
        st.caption(caption)
    return edited.to_dict(orient="records")

def _edit_scalar(label: str, value, key: str):
    if isinstance(value, bool):
        return st.checkbox(label, value=value, key=key)
    # keep everything else stringly-typed (safer for downstream)
    return st.text_input(label, value="" if value is None else str(value), key=key)

def _render_form(obj, key_prefix: str = ""):
    """
    Generic form renderer:
      - dict of scalars -> inputs
      - dict of dicts -> nested expanders
      - list[dict (uniform)] -> editable table
      - list[str]/list[scalar] -> multi-line textarea (JSON)
    Returns potentially-edited object.
    """
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            pk = f"{key_prefix}.{k}" if key_prefix else k
            label = _pretty(k)
            if isinstance(v, dict):
                with st.expander(label, expanded=False):
                    out[k] = _render_form(v, pk)
            elif isinstance(v, list):
                with st.expander(label, expanded=False):
                    out[k] = _render_form(v, pk)
            else:
                out[k] = _edit_scalar(label, v, pk)
        return out

    if isinstance(obj, list):
        if _is_uniform_dict_list(obj):
            return _edit_table(obj, key=f"{key_prefix}.table")
        # fallback: free JSON editor for mixed/simple lists
        text = st.text_area(
            _pretty(key_prefix or "List"),
            value=json.dumps(obj, indent=2, ensure_ascii=False),
            height=200,
            key=f"{key_prefix}.json",
        )
        try:
            return json.loads(text)
        except Exception:
            st.warning("Invalid JSON in list editor; keeping previous value.")
            return obj

    # scalars
    return _edit_scalar(_pretty(key_prefix or "Value"), obj, key_prefix)

def _get_tepp_criteria(tepp: dict) -> list[dict]:
    return (
        tepp.get("tender_evaluation", {})
            .get("evaluation_methodology", {})
            .get("required_criteria_table", [])
    )

def _set_tepp_criteria(tepp: dict, rows: list[dict]) -> None:
    tepp.setdefault("tender_evaluation", {})\
        .setdefault("evaluation_methodology", {})["required_criteria_table"] = rows

# ==========================
# Pages
# ==========================
def page_home():
    # Centered page header (replaces st.title)
    st.markdown(
        '<div class="page-header"><h1>Before Advertisement</h1></div>',
        unsafe_allow_html=True
    )

    OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434"))
    if "ollama_models" not in st.session_state:
        st.session_state.ollama_models = list_ollama_models(OLLAMA_URL)

    # One centered column for ALL controls (hero, select, refresh, continue)
    left, main, right = st.columns([1, 3, 1])
    with main:
        # Hero text aligned with everything below
        st.markdown(
            '<div class="hero-bg fade-in center"><h3>Please Select The AI You Want To Use</h3></div>',
            unsafe_allow_html=True
        )

        options = st.session_state.ollama_models or []
        if not options:
            st.warning("No models found from Ollama. Start `ollama serve` or pull a model, e.g., `ollama pull llama3.1`.")
            selected_model = st.text_input(
                "Model (type manually)",
                value=st.session_state.get("selected_model", "llama3.1:8b"),
            )
        else:
            prev = st.session_state.get("selected_model")
            default_index = options.index(prev) if prev in options else 0
            selected_model = st.selectbox("Model", options, index=default_index, key="model_select")

        st.session_state.selected_model = selected_model
        st.markdown(f'<p class="center muted">Using model: <code>{selected_model}</code></p>', unsafe_allow_html=True)

        st.write("")  # spacer
        if st.button("↻ Refresh models", key="refresh_models", use_container_width=True):
            st.session_state.ollama_models = list_ollama_models(OLLAMA_URL)
            st.rerun()

        st.write("")  # spacer
        if st.button("Continue to Upload", key="continue_btn", use_container_width=True):
            _nav_set("upload", {"model": st.session_state.selected_model})

def page_upload():
    st.title("Upload Specification")
    st.markdown('<div class="card fade-in">Upload your technical specification file. After generation you will be redirected to the results page.</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Technical specification",
        type=["pdf", "docx", "txt", "doc"],
        help="Provide the tender specification file (PDF, DOCX, DOC or TXT).",
    )

    if uploaded_file is not None and st.button("Generate TEPP and Returnables"):
        # Resolve data_dir from query params (new API)
        qp = st.query_params
        data_dir_val = qp.get("data_dir", str(settings.DATA_DIR))
        if isinstance(data_dir_val, list):
            data_dir_val = data_dir_val[0]
        temp_dir = Path(data_dir_val)
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_path = temp_dir / uploaded_file.name
        with open(temp_path, "wb") as out:
            out.write(uploaded_file.getbuffer())

        with st.spinner("Generating documents, please wait…"):
            try:
                outputs = _generate_documents(temp_path, st.session_state.get("selected_model", "llama3.1:8b"))
            except Exception as exc:
                st.error(f"An error occurred during generation: {exc}")
                return

        st.session_state["spec_summary"] = outputs["spec_summary"]
        st.session_state["parsed"] = outputs["parsed"]
        st.session_state["tepp"] = outputs["tepp"]
        st.session_state["returnables"] = outputs["returnables"]

        # Redirect to results page
        _nav_set("results")

def page_results():
    st.markdown('<div class="page-header"><h1>Results</h1></div>', unsafe_allow_html=True)

    tepp = st.session_state.get("tepp") or {}
    returnables = st.session_state.get("returnables") or {}
    spec_summary = st.session_state.get("spec_summary") or {}

    tabs = st.tabs(["TEPP", "Returnables", "Raw JSON"])
    # ---------------- TEPP ----------------
    with tabs[0]:
        t1, t2, t3 = st.tabs(["Overview", "Evaluation Criteria", "Sections"])

        # ---- Overview (nice fields) ----
        with t1:
            col1, col2 = st.columns(2)
            with col1:
                tepp_title = st.text_input("Title", value=tepp.get("title") or spec_summary.get("title") or "")
                tender_no  = st.text_input("Tender No.", value=tepp.get("tender_no", ""))
                contract_no= st.text_input("Contract No.", value=tepp.get("contract_no", ""))
            with col2:
                closing    = st.text_input("Closing Date/Time", value=tepp.get("closing_datetime", ""))
                location   = st.text_input("Location / Site", value=tepp.get("location", ""))

            c1, c2, c3 = st.columns(3)
            contact = tepp.get("contact", {}) or {}
            with c1:
                contact_name = st.text_input("Contact Name", value=contact.get("name", ""))
            with c2:
                contact_email = st.text_input("Contact Email", value=contact.get("email", ""))
            with c3:
                contact_phone = st.text_input("Contact Phone", value=contact.get("phone", ""))

            if st.button("Save Overview", key="save_overview"):
                tepp["title"] = tepp_title
                tepp["tender_no"] = tender_no
                tepp["contract_no"] = contract_no
                tepp["closing_datetime"] = closing
                tepp["location"] = location
                tepp["contact"] = {"name": contact_name, "email": contact_email, "phone": contact_phone}
                st.session_state["tepp"] = tepp
                st.success("Overview saved.")

        # ---- Evaluation Criteria (editable table) ----
        with t2:
            rows = _get_tepp_criteria(tepp)
            edited_rows = _edit_table(
                rows, key="criteria_editor",
                caption="Tip: add/remove rows; all cells are editable. Columns like weight can include % symbols."
            )
            if st.button("Save Criteria", key="save_criteria"):
                _set_tepp_criteria(tepp, edited_rows)
                st.session_state["tepp"] = tepp
                st.success("Criteria saved.")

        # ---- Sections (generic nested editor) ----
        with t3:
            st.caption("Edit any other TEPP sections below. Each block expands to reveal fields and tables.")
            edited_tepp = _render_form(tepp, key_prefix="tepp_sections")
            if st.button("Save Sections", key="save_sections"):
                st.session_state["tepp"] = edited_tepp
                st.success("Sections saved.")

        st.divider()
        cA, cB, cC = st.columns(3)
        with cA:
            if st.button("Download TEPP (DOCX)", key="dl_tepp"):
                docx_path = export_json_to_docx(st.session_state["tepp"], "Tender Evaluation & Probity Plan")
                with open(docx_path, "rb") as f:
                    st.download_button("Download TEPP", f.read(), file_name="tepp.docx",
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                       key="dlbtn_tepp")
        with cB:
            if st.button("Back to Home", key="home_btn"):
                _nav_set("home")

    # ---------------- Returnables ----------------
    with tabs[1]:
        if not returnables:
            st.info("No Returnables found.")
        else:
            st.caption("Each schedule opens in its own section. Edit fields/tables directly.")
            # Render top-level dict as expanders
            edited_returnables = {}
            for sched_name, sched_data in returnables.items():
                with st.expander(_pretty(sched_name), expanded=False):
                    edited_returnables[sched_name] = _render_form(sched_data, key_prefix=f"ret.{sched_name}")

            if st.button("Save Returnables", key="save_returnables"):
                st.session_state["returnables"] = edited_returnables
                st.success("Returnables saved.")

            st.divider()
            if st.button("Download Returnables (DOCX)", key="dl_returnables"):
                docx_path = export_json_to_docx(st.session_state["returnables"], "Returnable Schedules")
                with open(docx_path, "rb") as f:
                    st.download_button("Download Returnables", f.read(), file_name="returnables.docx",
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                       key="dlbtn_ret")

    # ---------------- Raw JSON (for power users) ----------------
    with tabs[2]:
        r1, r2 = st.tabs(["TEPP JSON", "Returnables JSON"])
        with r1:
            tepp_str = json.dumps(st.session_state.get("tepp", {}), indent=2, ensure_ascii=False)
            new_tepp_str = st.text_area("TEPP JSON", value=tepp_str, height=360, key="tepp_json_raw")
            if st.button("Apply TEPP JSON"):
                try:
                    st.session_state["tepp"] = json.loads(new_tepp_str)
                    st.success("TEPP JSON applied.")
                except Exception as e:
                    st.error(f"Invalid JSON: {e}")
        with r2:
            ret_str = json.dumps(st.session_state.get("returnables", {}), indent=2, ensure_ascii=False)
            new_ret_str = st.text_area("Returnables JSON", value=ret_str, height=360, key="ret_json_raw")
            if st.button("Apply Returnables JSON"):
                try:
                    st.session_state["returnables"] = json.loads(new_ret_str)
                    st.success("Returnables JSON applied.")
                except Exception as e:
                    st.error(f"Invalid JSON: {e}")


# ==========================
# App entry
# ==========================
def main():
    st.set_page_config(page_title="Before Advertisement", layout="wide")
    _inject_css()  # Inject external CSS

    # Simple router using st.query_params
    qp = st.query_params
    view = qp.get("view", "home")
    if isinstance(view, list):
        view = view[0]

    if view == "home":
        page_home()
    elif view == "upload":
        page_upload()
    else:
        page_results()

if __name__ == "__main__":
    main()
