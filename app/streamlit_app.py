from __future__ import annotations

# ===== Standard libs =====
import os
import sys
import io
import json
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import Counter
import threading

# ---- Global task registry (threads MUST NOT touch st.session_state) ----
TASKS: Dict[str, Dict[str, Any]] = {}
TASKS_LOCK = threading.Lock()

# ===== Third-party =====
import pandas as pd
import requests
import streamlit as st

ADMIN_PASS_KEY = "5661"

# ---------------------------------------------------------------------
# Put the repo root on sys.path so 'app.*' imports are stable
# ---------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------
# App imports
# ---------------------------------------------------------------------
from app.config import settings
from app.schemas import SpecSummary

from app.services.textio import extract_text, chunks
from app.services.vectorstores import build_index, get_vs
from app.services.llm import rag_json, set_runtime_model, reset_runtime_model
from app.services.parse_spec import parse_spec
from app.services.policy import scan_policy_files, extract_many, _build_ephemeral_vs

# IMPORTANT: import from the **submodules**, not app.services.compose (file)

from app.services.compose.evaluation import (
    load_or_parse_supplier_payloads,
    _load_tepp_weights,
    schema_terms_from_returnables,
    extract_price_any,
    compute_price_scores,
    blend_schema_aware_score,
)

from app.services.compose.tepp import (
    compose_tepp,
    CATEGORY_WEIGHT_RANGES,
    _llm_weighting_decider,
    _extract_risk_factors,
    _parse_percent,
    _default_rationale_for,
    _sanitize_llm_rationale,
    _compose_sustainability_rationale,
)
from app.services.compose.returnables import compose_returnable_schedules
from app.services.docx_export import export_json_to_docx

from app.services.templates_catalog import (
    list_categories,
    load_category_template,
    deep_merge,
)

# Supplier / evaluation services
from app.services.supplier import (
    process_suppliers,
    list_suppliers,
    _load_weights_from_tepp,
    _data_dir as _supplier_data_dir,
)

# ---- Persisted task storage (resilient across reloads) ----
def _ensure_tasks_dir() -> Path:
    base = getattr(settings, "DATA_DIR", PROJECT_ROOT / "data")
    tasks_dir = Path(base) / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    return tasks_dir

def _task_path(task_id: str) -> Path:
    return _ensure_tasks_dir() / f"{task_id}.json"

def _task_write(task_id: str, payload: Dict[str, Any], merge: bool = True) -> None:
    try:
        p = _task_path(task_id)
        if merge and p.exists():
            old = json.loads(p.read_text(encoding="utf-8"))
            old.update(payload)
            payload = old
        p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        # best-effort; don't crash UI
        pass

def _task_read(task_id: str) -> Optional[Dict[str, Any]]:
    p = _task_path(task_id)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None

# ---------------------------------------------------------------------
# Prompt for spec summary (matches your llm.rag_json signature)
# ---------------------------------------------------------------------
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

SUMMARY_FIELD_QUERIES = [
    "title",
    "tender number / contract number",
    "closing date and time",
    "contact name email phone",
    "scope of works",
    "location site",
    "safety standards ADR WHS ISO Australian Standards",
]

PURCHASE_CATEGORIES: List[str] = list(CATEGORY_WEIGHT_RANGES.keys())

# ---------------------------------------------------------------------
# Model discovery (no dependency on settings.UI_MODELS)
# ---------------------------------------------------------------------
def _env_list(var: str, sep: str = ",") -> List[str]:
    v = (os.getenv(var) or "").strip()
    return [x.strip() for x in v.split(sep) if x.strip()] if v else []

def discover_models() -> List[str]:
    for attr in ("UI_MODELS", "OLLAMA_MODELS", "MODELS", "AVAILABLE_MODELS"):
        if hasattr(settings, attr):
            val = getattr(settings, attr)
            if isinstance(val, str):
                arr = [m.strip() for m in val.split(",") if m.strip()]
                if arr:
                    return arr
            if isinstance(val, (list, tuple)):
                arr = [str(m).strip() for m in val if str(m).strip()]
                if arr:
                    return arr

    env_models = _env_list("UI_MODELS") or _env_list("OLLAMA_MODELS") or _env_list("MODELS")
    if env_models:
        return env_models

    host = (
        getattr(settings, "OLLAMA_BASE_URL", None)
        or getattr(settings, "OLLAMA_HOST", None)
        or os.getenv("OLLAMA_BASE_URL")
        or os.getenv("OLLAMA_HOST")
        or "http://localhost:11434"
    )
    try:
        r = requests.get(f"{host.rstrip('/')}/api/tags", timeout=2)
        if r.ok:
            tags = [m.get("name") for m in r.json().get("models", []) if m.get("name")]
            if tags:
                return tags
    except Exception:
        pass

    return ["llama3.1:8b"]

# ---------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------
def _inject_css():
    default_path = Path(__file__).parent / "ui" / "theme.css"
    css_path_str = os.getenv("APP_THEME_CSS", str(default_path))
    css_path = Path(css_path_str)
    try:
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Could not read CSS at {css_path}: {e}")

# ---------------------------------------------------------------------
# Navigation helper
# ---------------------------------------------------------------------
def _nav_set(view: str, extra: Optional[Dict[str, str]] = None):
    payload = dict(st.query_params)
    # flatten list values
    for k, v in list(payload.items()):
        if isinstance(v, list) and v:
            payload[k] = v[0]
    payload["view"] = view
    if extra:
        payload.update(extra)
    st.query_params.clear()
    st.query_params.update(payload)
    st.rerun()

def _nav_init():
    # Remember the very first state so back works from the start
    if "nav_history" not in st.session_state:
        st.session_state["nav_history"] = []

def _nav_snapshot_current():
    # Take a snapshot of current query params
    snap = dict(st.query_params)
    # flatten lists
    for k, v in list(snap.items()):
        if isinstance(v, list) and v:
            snap[k] = v[0]
    return snap

def _nav_push_current():
    st.session_state.setdefault("nav_history", [])
    st.session_state["nav_history"].append(_nav_snapshot_current())

def _nav_back():
    hist = st.session_state.get("nav_history", [])
    if hist:
        prev = hist.pop()
        st.session_state["nav_history"] = hist
        st.query_params.clear()
        st.query_params.update(prev)
        st.rerun()

def _topbar():
    # Minimal top bar with a Back button; include it on every page after auth guard
    colA, colB = st.columns([1, 9])
    with colA:
        if st.button("← Back", key="global_back"):
            _nav_back()

# ---------------------------------------------------------------------
# UI helpers: sticky expanders that persist open/closed state across reruns
# ---------------------------------------------------------------------
def _sticky_expander(label: str, key: str, default_expanded: bool = False):
    """An expander that remembers its open state across reruns.
    Adds a small 'Keep open during auto-refresh' pin inside to persist state.
    """
    state_key = f"exp_open__{key}"
    pin_key = f"exp_pin__{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = bool(default_expanded)
    exp = st.expander(label, expanded=bool(st.session_state[state_key]))
    class _ExpanderCtx:
        def __enter__(self):
            self._ctx = exp.__enter__()
            # Pin control (optional)
            cols = st.columns([1, 9])
            with cols[0]:
                pin_val = st.checkbox(
                    "Keep open",
                    key=pin_key,
                    value=bool(st.session_state[state_key]),
                    help="Keep this panel open during auto-refresh",
                )
                st.session_state[state_key] = bool(pin_val)
            return self._ctx
        def __exit__(self, exc_type, exc, tb):
            return exp.__exit__(exc_type, exc, tb)
    return _ExpanderCtx()

# ---------------------------------------------------------------------
# Project directory helpers
# ---------------------------------------------------------------------
PROJECTS_ROOT = (Path(__file__).resolve().parent.parent / "projects")
PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)

def _slugify(text: str, max_len: int = 60) -> str:
    """Return a filesystem-friendly slug from arbitrary text."""
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:max_len].strip("-") or "project"

def _get_project_dir(project_name: str, rec_id: str) -> Path:
    """Compute and create (if needed) the project directory for a name/rec_id."""
    slug = _slugify(project_name or "project")
    project_dir = PROJECTS_ROOT / f"{slug}-{rec_id[:8]}"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "uploads").mkdir(exist_ok=True)
    (project_dir / "generated").mkdir(exist_ok=True)
    return project_dir

def _save_uploaded_file_to_project(uploaded_file, project_dir: Path) -> Path:
    """Persist the uploaded spec file into the project's uploads folder."""
    dest = project_dir / "uploads" / uploaded_file.name
    try:
        data = uploaded_file.getbuffer()
    except Exception:
        data = uploaded_file.read()
    with open(dest, "wb") as f:
        f.write(data)
    return dest

def _save_text_spec_to_project(text: str, project_dir: Path) -> Path:
    """Persist raw spec text into a file under uploads (as spec.txt)."""
    dest = project_dir / "uploads" / "spec.txt"
    dest.write_text(text, encoding="utf-8")
    return dest

def _save_json_to_project(data: dict, project_dir: Path, filename: str) -> Path:
    """Persist a dict as JSON into the project's generated folder."""
    dest = project_dir / "generated" / filename
    dest.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return dest

# ---------------------------------------------------------------------
# Auth: user database (salted+hashed) + session guard
# ---------------------------------------------------------------------
USERS_DB = (Path(__file__).resolve().parent / "users" / "users.json")

def _ensure_users_db():
    USERS_DB.parent.mkdir(parents=True, exist_ok=True)
    if not USERS_DB.exists():
        USERS_DB.write_text(json.dumps({"users": []}, indent=2), encoding="utf-8")

def _load_users() -> dict:
    _ensure_users_db()
    try:
        return json.loads(USERS_DB.read_text(encoding="utf-8"))
    except Exception:
        return {"users": []}

def _save_users(db: dict) -> None:
    _ensure_users_db()
    USERS_DB.write_text(json.dumps(db, indent=2), encoding="utf-8")

def _hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Return (salt_hex, hash_hex) using scrypt."""
    import hashlib, binascii
    if salt is None:
        salt_bytes = os.urandom(16)
    else:
        salt_bytes = binascii.unhexlify(salt)
    h = hashlib.scrypt(password.encode("utf-8"), salt=salt_bytes, n=2**14, r=8, p=1, dklen=32)
    return binascii.hexlify(salt_bytes).decode(), binascii.hexlify(h).decode()

def _verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    _, h2 = _hash_password(password, salt_hex)
    return h2 == hash_hex

def _create_user(username: str, password: str, is_admin: bool = False) -> None:
    db = _load_users()
    if any(u.get("username") == username for u in db.get("users", [])):
        raise ValueError("Username already exists.")
    salt, h = _hash_password(password)
    db["users"].append({
        "username": username,
        "salt": salt,
        "hash": h,
        "is_admin": bool(is_admin),
        "created_at": datetime.utcnow().isoformat() + "Z",
    })
    _save_users(db)

def _authenticate(username: str, password: str) -> bool:
    db = _load_users()
    for u in db.get("users", []):
        if u.get("username") == username:
            return _verify_password(password, u.get("salt", ""), u.get("hash", ""))
    return False

# ---------------------------------------------------------------------
# Small helpers for UI + editing
# ---------------------------------------------------------------------
def _coerce_to_text(x) -> str:
    if x is None:
        return ""
    if isinstance(x, (str, int, float, bool)):
        return str(x)
    try:
        return json.dumps(x, ensure_ascii=False)
    except Exception:
        return str(x)

def _pretty(s: str) -> str:
    return s.replace("_", " ").replace("-", " ").title()

def _is_uniform_dict_list(xs: list) -> bool:
    if not xs or not all(isinstance(x, dict) for x in xs):
        return False
    keys = [tuple(sorted(x.keys())) for x in xs]
    return len(set(keys)) == 1

def _edit_table(rows: List[Dict], key: str) -> List[Dict]:
    df = pd.DataFrame(rows)
    edited = st.data_editor(
        df, key=key, use_container_width=True, hide_index=True, num_rows="dynamic",
    )
    return edited.to_dict(orient="records")

def _dynamic_caption_for_category(category_key_lower: str) -> str:
    mapping = {
        "standard product or good": "Evaluation Criteria for standard products/goods ($250k+).",
        "construction contract valued at over $249,999": "Evaluation Criteria for construction contracts ($250k+).",
        "consultancy contract": "Evaluation Criteria for consultancy contracts ($250k+).",
        "service delivery contract": "Evaluation Criteria for service delivery contracts ($250k+).",
        "management contract": "Evaluation Criteria for management contracts ($250k+).",
        "lease / license": "Evaluation Criteria for lease/licence ($250k+).",
    }
    return mapping.get(category_key_lower, "Evaluation Criteria.")

def _get_tepp_criteria(tepp: dict) -> List[Dict[str, str]]:
    return tepp.setdefault("tender_evaluation", {})                .setdefault("evaluation_methodology", {})                .get("required_criteria_table", []) or []

def _set_tepp_criteria(tepp: dict, rows: List[Dict]) -> None:
    tepp.setdefault("tender_evaluation", {})         .setdefault("evaluation_methodology", {})["required_criteria_table"] = rows

def _recompute_weights_inplace(tepp: dict, parsed: dict, category_key_lower: str) -> None:
    """Rebuild Required Criteria table using policy ranges + parsed features."""
    ranges = CATEGORY_WEIGHT_RANGES.get(category_key_lower) or {}
    risk_factors = _extract_risk_factors(parsed or {})
    table_rows: List[Dict[str, str]] = []
    price_weight_float: Optional[float] = None

    llm_out = _llm_weighting_decider(category_key_lower, ranges, risk_factors) if ranges else None
    if llm_out and isinstance(llm_out.get("weights"), dict):
        ordered = [
            "Price (Full Cost)",
            "Relevant Experience",
            "Capability",
            "Management & Financial Capacity",
            "Quality Management",
            "WHS",
            "Sustainability and EEO & Fair Employment",
        ]
        weights_map = llm_out["weights"]
        rationales = llm_out.get("rationales", {}) or {}
        crits = [c for c in ordered if c in weights_map] + [c for c in weights_map if c not in ordered]
        for c in crits:
            w = f"{weights_map[c]}%"
            if c == "Price (Full Cost)":
                price_weight_float = _parse_percent(w)
            r = _sanitize_llm_rationale(rationales.get(c, "")) or _default_rationale_for(c, w, parsed)
            if c == "Sustainability and EEO & Fair Employment":
                r = _compose_sustainability_rationale(w, price_weight_float)
            table_rows.append({"criterion": c, "weight": w, "rationale": r})
    else:
        # Midpoint scaling fallback: ensure total 100 and sust=10% of price where applicable
        price_rng = ranges.get("Price (Full Cost)")
        def _mid(s: str) -> float:
            import re as _re
            m = _re.search(r"(\d+(?:\.\d+)?)\s*%\s*to\s*(\d+(?:\.\d+)?)\s*%", (s or ""), _re.I)
            if m: return (float(m.group(1)) + float(m.group(2))) / 2.0
            m2 = _re.search(r"(\d+(?:\.\d+)?)\s*%", (s or ""), _re.I)
            return float(m2.group(1)) if m2 else 0.0

        price = _mid(price_rng or "50%")
        sust = round(price * 0.10, 1) if "construction contract" in category_key_lower             or "standard product" in category_key_lower or "service delivery" in category_key_lower             or "consultancy" in category_key_lower else 0.0

        others = {k: _mid(v) for k, v in ranges.items() if k not in ("Price (Full Cost)",)}
        rem = 100.0 - price - (sust if sust > 0 else 0.0)
        base_other_sum = sum(others.values())
        scaled: Dict[str, float] = {}
        if base_other_sum > 0:
            scale = rem / base_other_sum
            for k, v in others.items():
                if k != "Sustainability and EEO & Fair Employment":
                    scaled[k] = v * scale
            if sust > 0:
                scaled["Sustainability and EEO & Fair Employment"] = sust

        all_keys = ["Price (Full Cost)"] + list(scaled.keys())
        rounded = {k: round((price if k == "Price (Full Cost)" else scaled[k]), 1) for k in all_keys}
        diff = round(100.0 - sum(rounded.values()), 1)
        adjustable = [k for k in rounded if k not in ["Price (Full Cost)", "Sustainability and EEO & Fair Employment"] and rounded[k] > 0]
        if abs(diff) > 0 and (adjustable or rounded):
            target_key = adjustable[-1] if adjustable else (all_keys[-1] if all_keys else None)
            if target_key:
                rounded[target_key] = round(rounded[target_key] + diff, 1)

        price_weight_float = price
        for c, wv in rounded.items():
            w = f"{wv}%"
            r = _default_rationale_for(c, w, parsed)
            if c == "Sustainability and EEO & Fair Employment":
                r = _compose_sustainability_rationale(w, price_weight_float)
            table_rows.append({"criterion": c, "weight": w, "rationale": r})

    em = tepp.setdefault("tender_evaluation", {}).setdefault("evaluation_methodology", {})
    em["required_criteria_table"] = table_rows
    em["required_criteria_caption"] = _dynamic_caption_for_category(category_key_lower)

# ===== Editable JSON form helpers =====
def _edit_scalar(label: str, value, key):
    if isinstance(value, bool):
        return st.checkbox(label, value=value, key=key)
    if isinstance(value, (int, float)):
        return st.number_input(label, value=value, key=key)
    return st.text_input(label, value=_coerce_to_text(value), key=key)

def _render_form(obj, key_prefix: str = ""):
    """
    Generic form renderer:
      - dict of scalars -> inputs
      - dict of dicts/lists -> nested expanders
      - list[dict] (uniform columns) -> editable table
      - list[scalars]/list[mixed] -> JSON textarea
    Returns the edited object with the same structure.
    """
    # Dict -> recurse / inputs
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            pk = f"{key_prefix}.{k}" if key_prefix else str(k)
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

    # List -> table if uniform dicts, else JSON textarea
    if isinstance(obj, list):
        if _is_uniform_dict_list(obj):
            return _edit_table(obj, key=f"{key_prefix}.table")
        text = st.text_area(
            _pretty(key_prefix or "list"),
            value=json.dumps(obj, indent=2, ensure_ascii=False),
            key=f"{key_prefix}.json",
            height=220,
        )
        try:
            return json.loads(text)
        except Exception:
            st.warning("Invalid JSON; keeping original list.")
            return obj

    # Anything else -> passthrough
    return obj

# ---------------------------------------------------------------------
# Generation pipeline
# ---------------------------------------------------------------------
def _generate_documents(file_path: Path, model: str, purchase_category: Optional[str]) -> Dict[str, Any]:
    """Extract → index → summarise/parse → (optional) policy VS → compose TEPP & Returnables."""
    rec_id = str(uuid.uuid4())
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Copy raw to DATA_DIR
    temp_path = settings.DATA_DIR / f"{rec_id}{(file_path.suffix or '.bin')}"
    with open(file_path, "rb") as src, open(temp_path, "wb") as dst:
        dst.write(src.read())

    # 1) Extract text
    text = _coerce_to_text(extract_text(temp_path))
    if not text.strip():
        raise ValueError("Could not read text from the document.")

    # 2) Build VS
    build_index(rec_id, chunks(text))
    vs = get_vs(rec_id)

    # 3) LLM selection
    token = set_runtime_model(model)
    try:
        # 4) Summary
        summary_json = rag_json(
            vs,
            SPEC_SUMMARY_PROMPT,
            field_queries=SUMMARY_FIELD_QUERIES,
            max_ctx=8,
            min_chars=2000,
        )
        spec_summary = SpecSummary.model_validate(summary_json)

        # 5) Parse features
        parsed = parse_spec(text)
        if purchase_category and isinstance(purchase_category, str):
            parsed["purchase_category"] = purchase_category

        # 6) Extra policy VS (optional) - only if policy files exist
        vs_policy = None
        try:
            policy_files = scan_policy_files()
            if policy_files:  # Only process if files exist
                policy_texts = extract_many(policy_files)
                policy_chunks: List[str] = []
                for t in (policy_texts or []):
                    s = _coerce_to_text(t)
                    if s.strip():
                        from app.deps import SPLITTER
                        policy_chunks.extend(SPLITTER.split_text(s))
                vs_policy = _build_ephemeral_vs(policy_chunks) if policy_chunks else None
        except Exception:
            # If policy processing fails, continue without it
            vs_policy = None

        # 7) Compose TEPP & Returnables
        tepp = compose_tepp(spec_summary, parsed, vs, [vs_policy] if vs_policy else None)
        returnables = compose_returnable_schedules(spec_summary, parsed, non_negotiable_date=None)

        # 8) Persist JSONs needed for evaluation flow
        tepp_path = settings.DATA_DIR / f"{rec_id}.tepp.json"
        ret_path = settings.DATA_DIR / f"{rec_id}.returnables.json"
        tepp_path.write_text(json.dumps(tepp, indent=2, ensure_ascii=False), encoding="utf-8")
        ret_path.write_text(json.dumps(returnables, indent=2, ensure_ascii=False), encoding="utf-8")

        return {
            "rec_id": rec_id,
            "tepp": tepp,
            "returnables": returnables,
            "spec_summary": spec_summary.model_dump(),
            "parsed": parsed,
        }
    finally:
        reset_runtime_model(token)

# ==========================
# Supplier Evaluation Functions
# ==========================
def perform_supplier_evaluation(rec_id: str, suppliers: List[Dict[str, Any]], tepp: Dict[str, Any], returnables: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Perform comprehensive evaluation of suppliers against TEPP criteria.
    Returns a list of evaluation results with scores for each criterion.
    """
    from app.services.compose.evaluation import (
        load_tepp_weights, 
        load_or_parse_supplier_payloads,
        extract_price_any,
        compute_price_scores,
        blend_schema_aware_score,
        schema_terms_from_returnables
    )
    
    try:
        # Get weights from TEPP
        weights = load_tepp_weights(tepp)
        if not weights:
            st.warning("No weights found in TEPP. Using default weights.")
            weights = {
                "Price (Full Cost)": 40.0,
                "Relevant Experience": 20.0,
                "Capability": 20.0,
                "Management & Financial Capacity": 10.0,
                "WHS": 10.0
            }
        
        # Get schema terms from returnables for scoring
        schema_terms = schema_terms_from_returnables(returnables)
        
        # Load supplier payloads
        supplier_payloads = load_or_parse_supplier_payloads(rec_id)
        
        # First pass: collect all prices for comparison
        supplier_prices = {}
        for supplier in suppliers:
            supplier_id = supplier.get("id")
            if supplier_id in supplier_payloads:
                payload = supplier_payloads[supplier_id]
                price = extract_price_any(payload.get("json") or payload.get("text", ""))
                if price and price > 0:
                    supplier_prices[supplier_id] = price
        
        # Calculate price scores using relative comparison
        price_scores = {}
        if supplier_prices:
            prices = list(supplier_prices.values())
            min_price = min(prices)
            max_price = max(prices)
            price_range = max_price - min_price if max_price > min_price else 1
            
            for supplier_id, price in supplier_prices.items():
                # Lower price gets higher score (0-100 scale)
                if price_range > 0:
                    price_scores[supplier_id] = max(0, 100 - ((price - min_price) / price_range) * 100)
                else:
                    price_scores[supplier_id] = 100  # All prices are the same
        
        results = []
        
        for supplier in suppliers:
            supplier_id = supplier.get("id")
            supplier_name = supplier.get("name", f"Supplier {supplier_id}")
            
            # Fix generic "Name" values
            if supplier_name.lower() in ["name", "company name", "organization name", "business name"]:
                filename = supplier.get("filename", "")
                if filename:
                    # Try to extract a better name from the filename
                    clean_name = filename.replace("C112025-Part-5-Returnable-Schedules-", "").replace("C112025_SDE_Returnable-Schedules", "")
                    clean_name = clean_name.replace(".pdf", "").replace(".docx", "").replace(".doc", "")
                    if clean_name and len(clean_name) > 3:
                        supplier_name = f"Company {clean_name}"
                    else:
                        supplier_name = f"Company {supplier_id}"
                else:
                    supplier_name = f"Company {supplier_id}"
            
            if supplier_id not in supplier_payloads:
                st.warning(f"No payload found for supplier {supplier_name}")
                continue
                
            payload = supplier_payloads[supplier_id]
            
            # Initialize result
            result = {
                "Supplier ID": supplier_id,
                "Supplier Name": supplier_name,
                "Total Score": 0.0
            }
            
            # Score each criterion
            total_weighted_score = 0.0
            total_weight = 0.0
            
            for criterion, weight in weights.items():
                if criterion.lower().startswith("price"):
                    # Price scoring using relative comparison
                    price_score = price_scores.get(supplier_id, 0)
                    weighted_score = price_score * (weight / 100)
                    result[criterion] = round(price_score, 2)
                else:
                    # Non-price criteria scoring
                    supplier_text = payload.get("text", "") or payload.get("json", {})
                    score = blend_schema_aware_score(supplier_text, criterion, schema_terms)
                    weighted_score = score * (weight / 100)
                    result[criterion] = round(score, 2)
                
                total_weighted_score += weighted_score
                total_weight += weight / 100
            
            # Calculate total score
            if total_weight > 0:
                result["Total Score"] = round(total_weighted_score / total_weight * 100, 2)
            else:
                result["Total Score"] = 0.0
                
            results.append(result)
        
        return results
        
    except Exception as e:
        st.error(f"Error in supplier evaluation: {e}")
        st.exception(e)
        return []

# ==========================
# TEPP criteria merge helper (policy/LLM)
# ==========================
def _merge_default_tepp_with_llm(tepp: dict, llm_out: dict, parsed: dict, category_weight_ranges: dict | None = None):
    """Populate required_criteria_table via LLM output or policy midpoints."""
    # local fallbacks
    def _parse_percent_local(s: str) -> float:
        try:
            return float(str(s).strip().replace("%", ""))
        except Exception:
            return 0.0

    def _default_rationale_local(crit: str, weight_text: str, _parsed: dict) -> str:
        return f"{crit} is set to {weight_text} in line with policy and scope requirements."

    def _sanitize_llm_rationale_local(s: str) -> str:
        return (s or "").strip()

    def _compose_sustainability_rationale_local(weight_text: str, price_weight_float: float) -> str:
        return (
            f"The sustainability criterion is set to {weight_text}, balancing value-for-money with "
            f"environmental and social responsibility. Price is ~{price_weight_float:.1f}% to ensure competitiveness."
        )

    def _dynamic_caption_for_category_local(cat_lower: str) -> str:
        if "over $249,999" in (cat_lower or "") or "over 249,999" in (cat_lower or ""):
            return "Evaluation Criteria for Contracts over $249,999 (policy-aligned)."
        return "Evaluation Criteria (policy-aligned)."

    _parse_local = globals().get("_parse_percent", _parse_percent_local)
    _def_rat = globals().get("_default_rationale_for", _default_rationale_local)
    _san = globals().get("_sanitize_llm_rationale", _sanitize_llm_rationale_local)
    _sust = globals().get("_compose_sustainability_rationale", _compose_sustainability_rationale_local)
    _caption = globals().get("_dynamic_caption_for_category", _dynamic_caption_for_category_local)

    ranges_src = category_weight_ranges or globals().get("CATEGORY_WEIGHT_RANGES", {}) or {}

    table_rows: list[dict] = []

    # Prefer LLM results if present
    if isinstance(llm_out, dict) and llm_out.get("weights"):
        weights_map = llm_out["weights"]
        rationales = llm_out.get("rationales", {}) or {}
        ordered = [
            "Price (Full Cost)",
            "Relevant Experience",
            "Capability",
            "Management & Financial Capacity",
            "Quality Management",
            "WHS",
            "Sustainability and EEO & Fair Employment",
        ]
        crits = [c for c in ordered if c in weights_map] + [c for c in weights_map if c not in ordered]

        price_weight = 0.0
        for crit in crits:
            w = f"{weights_map[crit]}%"
            if crit == "Price (Full Cost)":
                price_weight = _parse_local(w)
            rationale = _san(rationales.get(crit, "")) or _def_rat(crit, w, parsed)
            if crit == "Sustainability and EEO & Fair Employment":
                rationale = _sust(w, price_weight)
            table_rows.append({"criterion": crit, "weight": w, "rationale": rationale})

    else:
        # derive from policy midpoints
        cat_lower = (
            (tepp.get("meta", {}) or {}).get("purchase_category_used")
            or parsed.get("purchase_category")
            or "construction contract valued at over $249,999"
        )
        cat_lower = str(cat_lower).strip().lower()
        ranges = ranges_src.get(cat_lower, {})

        label_map = {
            "price": "Price (Full Cost)",
            "experience": "Relevant Experience",
            "capability": "Capability",
            "management": "Management & Financial Capacity",
            "quality": "Quality Management",
            "whs": "WHS",
            "sustainability": "Sustainability and EEO & Fair Employment",
        }

        def _midpoint(s: str) -> float:
            # use re from top-level import to avoid NameError
            m = re.match(r"\s*(\d+(?:\.\d+)?)\s*%?\s*to\s*(\d+(?:\.\d+)?)\s*%?\s*$", str(s), flags=re.I)
            if m:
                return (float(m.group(1)) + float(m.group(2))) / 2.0
            m2 = re.match(r"\s*(\d+(?:\.\d+)?)\s*%?\s*$", str(s), flags=re.I)
            return float(m2.group(1)) if m2 else 0.0

        numeric: dict[str, float] = {}
        for k, v in ranges.items():
            label = label_map.get(k, k)
            numeric[label] = _midpoint(v)

        if not numeric:
            numeric = {
                "Price (Full Cost)": 50.0,
                "Relevant Experience": 15.0,
                "Capability": 15.0,
                "Quality Management": 5.0,
                "WHS": 5.0,
                "Management & Financial Capacity": 5.0,
                "Sustainability and EEO & Fair Employment": 5.0,
            }

        total = sum(numeric.values()) or 1.0
        pct = {k: round((v / total) * 100.0, 1) for k, v in numeric.items()}
        drift = round(100.0 - sum(pct.values()), 1)
        if abs(drift) >= 0.1:
            keys = list(pct.keys())
            adjustable = [k for k in keys if k != "Price (Full Cost)"]
            target = adjustable[-1] if adjustable else keys[-1]
            pct[target] = round(pct[target] + drift, 1)

        price_weight = 0.0
        for crit, val in pct.items():
            w = f"{val}%"
            if crit == "Price (Full Cost)":
                price_weight = _parse_local(w)
            rationale = _def_rat(crit, w, parsed)
            if crit == "Sustainability and EEO & Fair Employment":
                rationale = _sust(w, price_weight)
            table_rows.append({"criterion": crit, "weight": w, "rationale": rationale})

        tepp.setdefault("meta", {})
        tepp["meta"]["purchase_category_used"] = cat_lower
        tepp["meta"]["ranges_used"] = ranges

    em = tepp.setdefault("tender_evaluation", {}).setdefault("evaluation_methodology", {})
    em["required_criteria_table"] = table_rows
    cat_for_caption = (tepp.get("meta", {}) or {}).get("purchase_category_used", "")
    em["required_criteria_caption"] = _caption(str(cat_for_caption).lower())

# ---------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------
def page_login():
    # Title
    st.markdown("<h2 style='text-align:center;margin-top:1rem'>Sign in</h2>", unsafe_allow_html=True)

    db = _load_users()
    no_users = len(db.get("users", [])) == 0

    if no_users:
        # First-run bootstrap: show Sign in + Create Admin side-by-side
        colA, colB = st.columns([1, 1], gap="large")

        with colA:
            st.subheader("Sign in")
            with st.form("login_form"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign in", type="primary")
            if submitted:
                if _authenticate(u, p):
                    st.session_state["auth_user"] = u
                    next_view = st.query_params.get("next")
                    if isinstance(next_view, list):
                        next_view = next_view[0]
                    dest = next_view or "home"
                    st.query_params.clear()
                    st.query_params.update({"view": dest})
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

        with colB:
            st.subheader("Create the first (admin) account")
            with st.form("create_admin_form"):
                u2  = st.text_input("New username")
                p2  = st.text_input("New password", type="password")
                p2b = st.text_input("Confirm password", type="password")
                submitted2 = st.form_submit_button("Create admin")
            if submitted2:
                if not u2 or not p2:
                    st.error("Username and password are required.")
                elif p2 != p2b:
                    st.error("Passwords do not match.")
                else:
                    try:
                        _create_user(u2, p2, is_admin=True)
                        st.success("Admin account created. You can sign in now.")
                    except Exception as e:
                        st.error(str(e))

    else:
        # Normal case: centered sign-in card
        left, center, right = st.columns([1, 2, 1])
        with center:
            st.subheader("Sign in")
            with st.form("login_form"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign in", type="primary")
            if submitted:
                if _authenticate(u, p):
                    st.session_state["auth_user"] = u
                    next_view = st.query_params.get("next")
                    if isinstance(next_view, list):
                        next_view = next_view[0]
                    dest = next_view or "home"
                    st.query_params.clear()
                    st.query_params.update({"view": dest})
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

            # Existing users banner
            st.info("User database already initialised. Ask an admin to add users.")

            # --- Self-serve user creation with admin pass key ---
            with st.expander("Create a new user (requires admin pass key)"):
                with st.form("create_user_with_passkey"):
                    pk = st.text_input("Admin pass key", type="password")
                    new_u = st.text_input("New username")
                    new_p = st.text_input("New password", type="password")
                    new_p2 = st.text_input("Confirm password", type="password")
                    sub_new = st.form_submit_button("Create user")
                if sub_new:
                    if pk != ADMIN_PASS_KEY:
                        st.error("Invalid admin pass key.")
                    elif not new_u or not new_p:
                        st.error("Username and password are required.")
                    elif new_p != new_p2:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            _create_user(new_u, new_p, is_admin=False)
                            st.success(f"User '{new_u}' created. You can sign in now.")
                        except Exception as e:
                            st.error(str(e))

def page_home():
    _topbar()
    st.markdown('<div class="page-header"><h1>AI Tendering Automation</h1></div>', unsafe_allow_html=True)

    # ---- Value threshold switch ----
    top_cols = st.columns([1, 2])
    with top_cols[0]:
        over_250k = st.toggle(
            "Contract value ≥ $249,999",
            value=st.session_state.get("over_249999", True),
            help="Turn OFF if this is a under $250k procurement (RFQ)."
        )
        st.session_state["over_249999"] = over_250k

    with st.expander("What should I do on this page?", expanded=True):
        st.markdown(
            "- Pick the **LLM model** you want to use.\n"
            "- Select the **Tender Category** and **Purchase Category** (if ≥ $249,999), or RFQ options (if under $250k).\n"
            "- Click **Continue to Upload** to go to the next step."
        )

    # Model picker
    st.markdown("### Model & Category")
    options = discover_models()
    prev = st.session_state.get("selected_model", options[0])
    model = st.selectbox("Model", options, index=(options.index(prev) if prev in options else 0))
    st.session_state.selected_model = model

    if over_250k:
        # ------ TENDER MODE ------
        st.markdown('<div class="card"><h2>Please Select The Categories & The AI</h2></div>', unsafe_allow_html=True)

        categories = list_categories(doc_type="tepp")
        default_purchase = st.session_state.get("purchase_category", "construction contract")
        if default_purchase not in PURCHASE_CATEGORIES:
            default_purchase = "construction contract"

        col1, col2 = st.columns(2)
        with col1:
            sel_cat = st.selectbox("Tender Category (for template merge)", categories, key="selected_category")
        with col2:
            sel_purchase = st.selectbox(
                "Purchase Category (policy ranges)",
                PURCHASE_CATEGORIES,
                index=PURCHASE_CATEGORIES.index(default_purchase),
                key="selected_purchase_category"
            )
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Continue to Upload"):
            _nav_push_current()
            _nav_set("upload", {
                "model": model,
                "category": sel_cat,
                "purchase_category": sel_purchase,
                "rfq": "0",
            })

    else:
        # ------ RFQ MODE ------
        st.markdown('<div class="card"><h2>RFQ (Under $250k) – Select Options & AI</h2></div>', unsafe_allow_html=True)
        rfq_categories = list_categories(doc_type="tepp")  # reuse; swap if you add rfq-specific templates
        sel_cat_rfq = st.selectbox("RFQ Category (for template merge)", rfq_categories, key="selected_category_rfq")

        st.caption("RFQ mode uses simplified evaluation. Purchase Category weighting ranges are not applied.")

        if st.button("Continue to Upload (RFQ)"):
            _nav_push_current()
            _nav_set("upload", {
                "model": model,
                "category": sel_cat_rfq,
                "rfq": "1",
            })

# ---------------------------------------------------------------------
# Thread-safe task starter (background generation)
# ---------------------------------------------------------------------
def _start_generation_task(file_path: Path, model: str, purchase_category: Optional[str], meta: Optional[Dict[str, Any]] = None):
    """
    Launch _generate_documents(...) in a background thread.
    Stores status in process-wide TASKS and on disk under DATA_DIR/tasks.
    Returns a short task_id.
    """
    task_id = uuid.uuid4().hex[:8]
    seed = {
        "status": "running",
        "created": datetime.utcnow().isoformat() + "Z",
        "meta": meta or {},
        "tmp_spec_path": str(file_path),
    }
    with TASKS_LOCK:
        TASKS[task_id] = seed
    _task_write(task_id, seed, merge=False)

    def _worker():
        try:
            outputs = _generate_documents(file_path, model, purchase_category)
            
            # Create project folder and save artifacts there as well (nice for Results)
            # Only do this if project_name is provided to avoid unnecessary work
            project_name = (meta or {}).get("project_name")
            if project_name:
                rec_id = outputs.get("rec_id")
                project_dir = _get_project_dir(project_name, rec_id)
                
                # copy the original spec into uploads (async, don't block)
                try:
                    src = Path(file_path)
                    if src.exists():
                        dest = project_dir / "uploads" / (src.name or "spec.bin")
                        dest.write_bytes(src.read_bytes())
                except Exception:
                    pass
                
                # save the generated jsons into the project folder too (async, don't block)
                try:
                    _save_json_to_project(outputs["tepp"], project_dir, "tepp.json")
                    _save_json_to_project(outputs["returnables"], project_dir, "returnables.json")
                except Exception:
                    pass
                
                outputs["project_dir"] = str(project_dir)

            payload = {
                "status": "done",
                "outputs": outputs,
            }
            with TASKS_LOCK:
                TASKS[task_id].update(payload)
            _task_write(task_id, payload)

        except Exception as e:
            payload = {"status": "error", "error": str(e)}
            with TASKS_LOCK:
                TASKS[task_id].update(payload)
            _task_write(task_id, payload)

    threading.Thread(target=_worker, daemon=True).start()
    return task_id


# ---------------------------------------------------------------------
# Upload page (async-aware; can jump back to results without a spec if running)
# ---------------------------------------------------------------------
def page_upload():
    _topbar()
    rfq_mode = (st.query_params.get("rfq") == "1") or (not st.session_state.get("over_249999", True))

    st.title("Upload or Paste Specification" + (" – RFQ" if rfq_mode else ""))
    st.markdown(
        '<div class="card fade-in">Provide your technical specification either as a file or raw text. '
        'After you click Generate, the process runs <b>in the background</b>. You can navigate away and come back later.</div>',
        unsafe_allow_html=True
    )

    with st.expander("What should I do on this page?", expanded=True):
        st.markdown(
            "- Give your project a **clear name** (used for the save folder).\n"
            "- Provide the specification by **uploading a file** or **pasting raw text**.\n"
            "- If a generation is already running, you can simply click **Go to Results** to watch progress.\n"
            "- Click **Generate** to start a new background generation.\n"
            "- Use **Return to Results** to go back to previously generated documents."
        )

    # Project name
    project_name = st.text_input(
        "Project name",
        value=st.session_state.get("project_name", "Untitled Project"),
        help="Used as the folder name prefix where all files will be saved."
    )
    st.session_state["project_name"] = project_name

    # Model/category from session or query params (needed for navigation)
    qp = st.query_params
    model = qp.get("model", st.session_state.get("selected_model", "llama3.1:8b"))
    category = qp.get("category", st.session_state.get("selected_category", "generic"))
    purchase_category = qp.get("purchase_category", st.session_state.get("selected_purchase_category", None))
    if isinstance(model, list): model = model[0]
    if isinstance(category, list): category = category[0]
    if isinstance(purchase_category, list): purchase_category = purchase_category[0]

    # Check if there are any existing results to return to
    data_dir = settings.DATA_DIR
    existing_results = sorted(data_dir.glob("*.tepp.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if existing_results:
        st.divider()
        st.subheader("📋 Previous Results")
        st.caption("Return to previously generated documents without uploading a new specification.")
        
        # Show the most recent result
        latest_result = existing_results[0]
        rec_id = latest_result.stem.replace(".tepp", "")
        result_time = datetime.fromtimestamp(latest_result.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"**Latest result**: {rec_id[:8]}... (generated {result_time})")
        with col2:
            if st.button("Return to Results", key="return_to_results", help="Go back to the most recent generated documents"):
                _nav_push_current()
                _nav_set("results", {
                    "rec_id": rec_id,
                    "rfq": "1" if rfq_mode else "0",
                    "model": model,
                    "category": category,
                    "purchase_category": purchase_category if not rfq_mode else None
                })
                return
        
        # Show additional results if there are more than one
        if len(existing_results) > 1:
            with st.expander(f"View all {len(existing_results)} previous results", expanded=False):
                for i, result_path in enumerate(existing_results[:5]):  # Show up to 5 most recent
                    result_rec_id = result_path.stem.replace(".tepp", "")
                    result_time = datetime.fromtimestamp(result_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{i+1}.** {result_rec_id[:8]}... (generated {result_time})")
                    with col2:
                        if st.button("Open", key=f"open_result_{i}"):
                            _nav_push_current()
                            _nav_set("results", {
                                "rec_id": result_rec_id,
                                "rfq": "1" if rfq_mode else "0",
                                "model": model,
                                "category": category,
                                "purchase_category": purchase_category if not rfq_mode else None
                            })
                            return

    # Detect any running task
    running_task_id = None
    with TASKS_LOCK:
        for tid, t in TASKS.items():
            if t.get("status") == "running":
                running_task_id = tid
                break

    # If a task is running, show a focused banner + shortcut button
    if running_task_id:
        st.success("A generation is currently running in the background.")
        if st.button("Go to Results (watch progress)"):
            _nav_push_current()
            _nav_set("results", {
                "task": running_task_id, 
                "rfq": "1" if rfq_mode else "0",
                "model": model,
                "category": category,
                "purchase_category": purchase_category if not rfq_mode else None
            })
            return

    # Spec intake UI
    intake_mode = st.radio(
        "How do you want to provide the specification?",
        ["Upload a file", "Paste raw text"],
        horizontal=True,
        disabled=False
    )

    uploaded_file = None
    pasted_text = None

    if intake_mode == "Upload a file":
        uploaded_file = st.file_uploader(
            "Technical specification",
            type=["pdf", "docx", "txt", "doc"],
            help="Provide the tender/RFQ specification file (PDF, DOCX, DOC or TXT)."
        )
    else:
        pasted_text = st.text_area(
            "Paste the full technical specification text here",
            height=240,
            placeholder="Paste the raw spec text…"
        )


    # Proceed if task already running OR spec provided
    spec_provided = (uploaded_file is not None) or (pasted_text and pasted_text.strip())
    can_click = bool(running_task_id or spec_provided)

    col_gen, col_go = st.columns([1, 1])
    with col_gen:
        if st.button("Generate TEPP and Returnables", disabled=not can_click, key="btn_generate"):
            # If a task is already running, just jump back to results to watch it
            if running_task_id:
                _nav_push_current()
                _nav_set("results", {
                    "task": running_task_id, 
                    "rfq": "1" if rfq_mode else "0",
                    "model": model,
                    "category": category,
                    "purchase_category": purchase_category if not rfq_mode else None
                })
                return

            # Otherwise start a brand-new background task
            if uploaded_file is not None:
                suffix = Path(uploaded_file.name).suffix or ".bin"
                tmp = settings.DATA_DIR / f"upload_{uuid.uuid4().hex}{suffix}"
                settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
                with open(tmp, "wb") as f:
                    f.write(uploaded_file.read())
            else:
                tmp = settings.DATA_DIR / f"upload_{uuid.uuid4().hex}.txt"
                settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
                tmp.write_text((pasted_text or "").strip(), encoding="utf-8")

            task_id = _start_generation_task(
                tmp,
                model,
                None if rfq_mode else purchase_category,
                meta={
                    "project_name": project_name,
                    "category": category,
                    "rfq_mode": bool(rfq_mode),
                }
            )

            st.session_state["selected_category"] = category
            st.session_state["selected_purchase_category"] = purchase_category
            st.session_state["rfq_mode"] = bool(rfq_mode)

            _nav_push_current()
            _nav_set("results", {
                "task": task_id, 
                "rfq": "1" if rfq_mode else "0",
                "model": model,
                "category": category,
                "purchase_category": purchase_category if not rfq_mode else None
            })
            return

    with col_go:
        # Convenience button visible even if "Generate" is disabled
        if running_task_id and st.button("Go to Results (watch progress)", key="btn_go_results_secondary"):
            _nav_push_current()
            _nav_set("results", {
                "task": running_task_id, 
                "rfq": "1" if rfq_mode else "0",
                "model": model,
                "category": category,
                "purchase_category": purchase_category if not rfq_mode else None
            })
            return

# ---------------------------------------------------------------------
# Results page (async-aware, editable, export)
# ---------------------------------------------------------------------
def page_results():
    _topbar()
    st.title("Results & Editing")
    st.caption("Step 2 of 2 – Review, edit, and export.")

    with st.expander("What should I do on this page?", expanded=True):
        st.markdown(
            "- **Preview** the generated TEPP and Returnable Schedules.\n"
            "- **Edit** fields inline where available (criteria, weights, etc.).\n"
            "- **Download** the DOCX files.\n"
            "- (Optional) **Upload filled Returnable Schedules** from suppliers, then click **Evaluate** to score and rank.\n"
            "- Re-run generation if you make major changes to the spec."
        )

    project_dir = Path(st.session_state.get("project_dir", ""))
    if project_dir and project_dir.exists():
        st.info(f"Project folder: `{project_dir}`")

    # --- Query params / dirs
    qp = st.query_params
    data_dir_val = qp.get("data_dir", str(settings.DATA_DIR))
    if isinstance(data_dir_val, list):
        data_dir_val = data_dir_val[0]
    data_dir = Path(data_dir_val)

    # --- Support async arrival via ?task=... (background generation watcher)
    task_id = qp.get("task")
    if isinstance(task_id, list):
        task_id = task_id[0]

    rec_id = st.session_state.get("record_id") or qp.get("rec_id")
    if isinstance(rec_id, list):
        rec_id = rec_id[0]

    if not rec_id and task_id:
        # Always try disk first for more reliable status checking
        task = _task_read(task_id)
        
        # If not found on disk, try in-memory as fallback
        if not task:
            with TASKS_LOCK:
                task = TASKS.get(task_id)

        if not task:
            st.warning("Task not found (process likely reloaded). If you just started it, wait a moment and press Refresh.")
            st.button("Refresh", key="refresh_missing_task")
            # As a convenience, fall back to most-recent .tepp.json if present
            candidates = sorted(data_dir.glob("*.tepp.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if candidates:
                fallback_rec = candidates[0].stem.replace(".tepp", "")
                if st.button(f"Open latest results (rec_id={fallback_rec[:8]}…)", key="open_latest_fallback"):
                    _nav_push_current()
                    _nav_set("results", {
                        "rec_id": fallback_rec, 
                        "rfq": qp.get("rfq", "0"),
                        "model": qp.get("model"),
                        "category": qp.get("category"),
                        "purchase_category": qp.get("purchase_category")
                    })
            return

        status = task.get("status")
        
        # Debug information
        st.caption(f"Task ID: {task_id} | Status: {status} | Last updated: {task.get('created', 'Unknown')}")
        
        if status == "running":
            # Calculate elapsed time
            import time
            from datetime import datetime
            created_time = task.get("created", "")
            if created_time:
                try:
                    created_dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                    elapsed = time.time() - created_dt.timestamp()
                    elapsed_min = int(elapsed // 60)
                    elapsed_sec = int(elapsed % 60)
                    elapsed_str = f"{elapsed_min}m {elapsed_sec}s"
                except:
                    elapsed_str = "Unknown"
            else:
                elapsed_str = "Unknown"
            
            with st.status("Generating TEPP & Returnables in background...", state="running"):
                st.write("You can navigate around. Come back any time; the task will continue.")
                st.write(f"⏱️ **Elapsed time**: {elapsed_str}")
                st.write("🔄 Auto-refreshing every 3 seconds while the task is running…")

            # Hard-reliable auto-refresh: sleep for 3 seconds, then rerun
            time.sleep(3)
            st.rerun()
            return
        elif status == "error":
            st.error(f"Generation failed: {task.get('error', 'Unknown error')}")
            return
        else:
            outputs = task.get("outputs") or {}
            rec_id = outputs.get("rec_id")
            if rec_id:
                st.session_state["record_id"] = rec_id
                # also stash project_dir if present
                if outputs.get("project_dir"):
                    st.session_state["project_dir"] = outputs["project_dir"]
                # switch to canonical rec_id URL
                _nav_push_current()
                _nav_set("results", {
                    "rec_id": rec_id, 
                    "rfq": qp.get("rfq", "0"),
                    "model": qp.get("model"),
                    "category": qp.get("category"),
                    "purchase_category": qp.get("purchase_category")
                })
                return
            else:
                st.warning("Task finished but no record id was returned.")
                return


    # --- If still no rec_id, fall back to latest on disk
    if not rec_id:
        candidates = sorted(data_dir.glob("*.tepp.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            rec_id = candidates[0].stem.replace(".tepp", "")
            st.session_state["record_id"] = rec_id

    if not rec_id:
        st.error("No active record. Please go back to Upload and generate documents.")
        return

    tepp_path = data_dir / f"{rec_id}.tepp.json"
    ret_path  = data_dir / f"{rec_id}.returnables.json"

    try:
        tepp = json.loads(tepp_path.read_text(encoding="utf-8"))
    except Exception:
        tepp = {}
    try:
        returnables = json.loads(ret_path.read_text(encoding="utf-8"))
    except Exception:
        returnables = {}

    if not tepp or not returnables:
        st.warning("Missing TEPP and/or Returnable Schedules. Please re-run generation.")
    st.session_state["tepp"] = tepp
    st.session_state["returnables"] = returnables
    # Try to infer and remember the project folder for display
    if not st.session_state.get("project_dir"):
        proj_name = (tepp.get("document_metadata", {}) or {}).get("project_name")
        if proj_name and st.session_state.get("record_id"):
            try:
                probe = _get_project_dir(proj_name, st.session_state["record_id"])
                # Only set if exists (worker may not have created it in very old runs)
                if probe.exists():
                    st.session_state["project_dir"] = str(probe)
            except Exception:
                pass

    tabs = st.tabs(["TEPP (editable)", "Returnables (editable)", "Raw JSON", "Export"])

    # ===================== TEPP (editable) =====================
    with tabs[0]:
        st.subheader("Overview")
        col1, col2 = st.columns(2)
        with col1:
            tepp_title = st.text_input("Title", value=tepp.get("title", ""))
            tender_no  = st.text_input("Tender No.", value=tepp.get("tender_no", ""))
            contract_no = st.text_input("Contract No.", value=tepp.get("contract_no", ""))
        with col2:
            closing    = st.text_input("Closing Date/Time", value=tepp.get("closing_datetime", ""))
            location   = st.text_input("Location / Site", value=tepp.get("location", ""))

        c1, c2, c3 = st.columns(3)
        contact = tepp.get("contact", {}) or {}
        with c1:
            contact_name  = st.text_input("Contact Name", value=contact.get("name", ""))
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
            (data_dir / f"{rec_id}.tepp.json").write_text(json.dumps(tepp, indent=2, ensure_ascii=False), encoding="utf-8")
            st.session_state["tepp"] = tepp
            st.success("Overview saved.")

        st.divider()
        st.subheader("Evaluation Criteria & Weights")
        em = tepp.setdefault("tender_evaluation", {}).setdefault("evaluation_methodology", {})
        table = em.get("required_criteria_table") or []
        edited_table = _edit_table(table, key="crit_table_edit")
        if st.button("Save Criteria Table", key="save_crit_table"):
            em["required_criteria_table"] = edited_table
            (data_dir / f"{rec_id}.tepp.json").write_text(json.dumps(tepp, indent=2, ensure_ascii=False), encoding="utf-8")
            st.session_state["tepp"] = tepp
            st.success("Criteria table saved.")

        st.caption("Need to rebuild weights from policy ranges? Use the button below.")
        if st.button("Recompute weights from purchase category", key="recalc_weights"):
            parsed = st.session_state.get("parsed", {})
            purchase_category = parsed.get("purchase_category") or tepp.get("meta", {}).get("purchase_category_used")
            if not purchase_category:
                st.warning("No purchase category in parsed spec or TEPP meta; cannot rebuild.")
            else:
                try:
                    cat_key = str(purchase_category).lower()
                    ranges = CATEGORY_WEIGHT_RANGES.get(cat_key, {})
                    risks = _extract_risk_factors(parsed)
                    out = _llm_weighting_decider(cat_key, ranges, risks)
                except Exception:
                    out = {}
                _merge_default_tepp_with_llm(tepp, out, parsed)
                (data_dir / f"{rec_id}.tepp.json").write_text(json.dumps(tepp, indent=2, ensure_ascii=False), encoding="utf-8")
                st.session_state["tepp"] = tepp
                st.success("Weights rebuilt and TEPP updated.")

        st.divider()
        st.subheader("Full TEPP (advanced editor)")
        st.caption("Edit any part of the TEPP structure. Be careful—this is the master document.")
        tepp_full_edited = _render_form(tepp, key_prefix="tepp_full")
        if st.button("Save Full TEPP", key="save_full_tepp"):
            try:
                (data_dir / f"{rec_id}.tepp.json").write_text(json.dumps(tepp_full_edited, indent=2, ensure_ascii=False), encoding="utf-8")
                st.session_state["tepp"] = tepp_full_edited
                st.success("TEPP saved.")
            except Exception as e:
                st.error(f"Could not save TEPP: {e}")

        st.divider()
        if st.button("Evaluate supplier responses →", key="go_eval_from_tepp"):
            _nav_push_current()
            _nav_set("evaluation", {"rec_id": rec_id})

    # ===================== Returnables (editable) =====================
    with tabs[1]:
        st.subheader("Returnable Schedules (editable)")
        if not returnables:
            st.info("No Returnable Schedules found.")
        else:
            edited_returnables = {}
            for sched_name, sched_data in returnables.items():
                with st.expander(_pretty(sched_name), expanded=False):
                    edited_returnables[sched_name] = _render_form(sched_data, key_prefix=f"ret.{sched_name}")

            colA, colB = st.columns(2)
            with colA:
                if st.button("Save Returnables", key="save_returnables"):
                    try:
                        (data_dir / f"{rec_id}.returnables.json").write_text(json.dumps(edited_returnables, indent=2, ensure_ascii=False), encoding="utf-8")
                        st.session_state["returnables"] = edited_returnables
                        st.success("Returnables saved.")
                    except Exception as e:
                        st.error(f"Could not save Returnables: {e}")
            with colB:
                try:
                    if st.button("Build Returnables DOCX", key="build_ret_docx"):
                        docx_path = export_json_to_docx(st.session_state["returnables"], "Returnable Schedules")
                        with open(docx_path, "rb") as f:
                            st.download_button(
                                "Download Returnables DOCX",
                                f.read(),
                                file_name="returnables.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key="dl_ret_docx"
                            )
                except Exception as e:
                    st.warning(f"DOCX export (Returnables) not available: {e}")

        st.divider()
        if st.button("Evaluate supplier responses →", key="go_eval_from_returnables"):
            _nav_push_current()
            _nav_set("evaluation", {"rec_id": rec_id})

    # ===================== Raw JSON =====================
    with tabs[2]:
        r1, r2 = st.tabs(["TEPP JSON", "Returnables JSON"])
        with r1:
            tepp_str = json.dumps(st.session_state.get("tepp", tepp), indent=2, ensure_ascii=False)
            new_tepp_str = st.text_area("TEPP JSON", value=tepp_str, height=380, key="tepp_json_raw")
            if st.button("Save TEPP JSON", key="save_tepp_json"):
                try:
                    new_tepp = json.loads(new_tepp_str)
                    (data_dir / f"{rec_id}.tepp.json").write_text(json.dumps(new_tepp, indent=2, ensure_ascii=False), encoding="utf-8")
                    st.session_state["tepp"] = new_tepp
                    st.success("TEPP JSON saved.")
                except Exception as e:
                    st.error(f"Invalid TEPP JSON: {e}")
        with r2:
            ret_str = json.dumps(st.session_state.get("returnables", returnables), indent=2, ensure_ascii=False)
            new_ret_str = st.text_area("Returnables JSON", value=ret_str, height=380, key="ret_json_raw")
            if st.button("Save Returnables JSON", key="save_ret_json"):
                try:
                    new_ret = json.loads(new_ret_str)
                    (data_dir / f"{rec_id}.returnables.json").write_text(json.dumps(new_ret, indent=2, ensure_ascii=False), encoding="utf-8")
                    st.session_state["returnables"] = new_ret
                    st.success("Returnables JSON saved.")
                except Exception as e:
                    st.error(f"Invalid Returnables JSON: {e}")

    # ===================== Export =====================
    with tabs[3]:
        st.subheader("Download / Export")
        c1, c2, _ = st.columns(3)
        with c1:
            st.download_button(
                "Download TEPP JSON",
                data=json.dumps(st.session_state.get("tepp", tepp), indent=2, ensure_ascii=False).encode("utf-8"),
                file_name="tepp.json",
                mime="application/json",
                key="dl_tepp_json"
            )
        with c2:
            st.download_button(
                "Download Returnables JSON",
                data=json.dumps(st.session_state.get("returnables", returnables), indent=2, ensure_ascii=False).encode("utf-8"),
                file_name="returnables.json",
                mime="application/json",
                key="dl_ret_json"
            )

        st.divider()
        colx, coly = st.columns(2)
        with colx:
            try:
                if st.button("Build TEPP DOCX", key="build_tepp_docx"):
                    tepp_docx = export_json_to_docx(st.session_state.get("tepp", tepp), "TEPP")
                    with open(tepp_docx, "rb") as f:
                        st.download_button(
                            "Download TEPP DOCX",
                            f.read(),
                            file_name="tepp.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="dl_tepp_docx"
                        )
            except Exception as e:
                st.warning(f"DOCX export (TEPP) not available: {e}")

        with coly:
            try:
                if st.button("Build Returnables DOCX (again)", key="build_ret_docx_2"):
                    ret_docx = export_json_to_docx(st.session_state["returnables"], "Returnable Schedules")
                    with open(ret_docx, "rb") as f:
                        st.download_button(
                            "Download Returnables DOCX",
                            f.read(),
                            file_name="returnables.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="dl_ret_docx_2"
                        )
            except Exception as e:
                st.warning(f"DOCX export (Returnables) not available: {e}")

        st.divider()
        if st.button("Evaluate supplier responses →", key="go_eval_from_export"):
            _nav_push_current()
            _nav_set("evaluation", {"rec_id": rec_id})

# ---------------------------------------------------------------------
# Evaluation page (restored)
# ---------------------------------------------------------------------
def page_evaluation():
    _topbar()
    st.title("Evaluation")
    st.caption("Upload supplier responses and compute scores & rankings.")

    qp = st.query_params
    data_dir_val = qp.get("data_dir", str(settings.DATA_DIR))
    if isinstance(data_dir_val, list):
        data_dir_val = data_dir_val[0]
    data_dir = Path(data_dir_val)

    rec_id = st.session_state.get("record_id") or qp.get("rec_id")
    if isinstance(rec_id, list):
        rec_id = rec_id[0]

    if not rec_id:
        # Try latest
        candidates = sorted(data_dir.glob("*.tepp.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            rec_id = candidates[0].stem.replace(".tepp", "")
            st.session_state["record_id"] = rec_id

    if not rec_id:
        st.error("No active record. Go to Results, generate or select a record first.")
        return

    tepp_path = data_dir / f"{rec_id}.tepp.json"
    ret_path  = data_dir / f"{rec_id}.returnables.json"
    try:
        tepp = json.loads(tepp_path.read_text(encoding="utf-8"))
    except Exception:
        tepp = {}
    try:
        returnables = json.loads(ret_path.read_text(encoding="utf-8"))
    except Exception:
        returnables = {}

    if not tepp or not returnables:
        st.warning("Missing TEPP and/or Returnables. Return to Results and re-generate.")
        return

    # Where supplier files go
    sup_dir = _supplier_data_dir() / rec_id
    sup_dir.mkdir(parents=True, exist_ok=True)
    st.info(f"Supplier files directory: `{sup_dir}`")

    with _sticky_expander("Upload supplier responses", key="eval.upload", default_expanded=True):

        st.info("📄 **Supported file types**: PDF, DOCX, DOC, CSV, XLSX, XLS, JSON, TXT")
        st.caption("💡 Upload either general supplier responses (we will fill a blank Returnable Schedule) or an already filled Returnable Schedule (JSON preferred; PDF/DOCX supported).")

        # Choose ingestion mode
        mode = st.radio(
            "Choose ingestion mode",
            ["Supplier responses", "Filled Returnable Schedule"],
            horizontal=True,
            key="ingestion_mode",
        )
        input_type = "responses" if mode == "Supplier responses" else "filled_returnables"

        up_files = st.file_uploader(
            "Upload one or more supplier file(s)",
            type=["pdf", "docx", "doc", "csv", "xlsx", "xls", "json", "txt"],
            accept_multiple_files=True,
            help=("For 'Supplier responses', upload quotes/capability docs. For 'Filled Returnable Schedule', upload the supplier's filled RS (JSON ideal; PDF/DOCX also OK).")
        )
        if up_files:
            try:
                class MockUploadFile:
                    def __init__(self, sf):
                        self.filename = sf.name
                        self.file = sf
                mock_files = [MockUploadFile(f) for f in up_files]
                suppliers = process_suppliers(rec_id, mock_files, returnables, input_type=input_type)
                if suppliers:
                    st.success(f"Successfully processed {len(suppliers)} supplier file(s).")
                    supplier_df = pd.DataFrame([
                        {"ID": s.get("id", ""), "Name": s.get("name", ""), "Filename": s.get("filename", ""), "Uploaded": s.get("uploaded_at", "")}
                        for s in suppliers
                    ])
                    st.dataframe(supplier_df, use_container_width=True)
                else:
                    st.warning("Files uploaded but no suppliers were processed.")
            except Exception as e:
                st.error(f"Error processing supplier files: {e}")
                st.exception(e)
                sup_dir = _supplier_data_dir() / rec_id
                sup_dir.mkdir(parents=True, exist_ok=True)
                for f in up_files:
                    dest = sup_dir / f.name
                    try:
                        data = f.getbuffer()
                    except Exception:
                        data = f.read()
                    with open(dest, "wb") as o:
                        o.write(data)
                st.info(f"Files saved to `{sup_dir.name}` but not processed.")

    with _sticky_expander("Weights preview", key="eval.weights", default_expanded=False):
        try:
            # Use the correct function that takes a tepp dict
            from app.services.compose.evaluation import load_tepp_weights
            weights = load_tepp_weights(tepp)
            st.json(weights or {"info": "No weights parsed from TEPP."})
            
            # Also show the evaluation criteria table
            criteria_table = tepp.get("tender_evaluation", {}).get("evaluation_methodology", {}).get("required_criteria_table", [])
            if criteria_table:
                st.subheader("Evaluation Criteria")
                criteria_df = pd.DataFrame(criteria_table)
                st.dataframe(criteria_df, use_container_width=True)
            else:
                st.warning("No evaluation criteria table found in TEPP.")
                
        except Exception as e:
            st.error(f"Error loading weights: {e}")
            st.json({"info": "No weights parsed from TEPP."})

    # Build evaluation workbook convenience
    st.divider()
    colA, colB = st.columns([1, 1])
    with colA:
        if st.button("Build Evaluation Workbook (XLSX)"):
            st.info("Workbook generation is disabled. Only in-app evaluation is available.")

    with colB:
        if st.button("Run Evaluation (score & rank)"):
            try:
                # Get suppliers and perform actual evaluation
                suppliers = process_suppliers(rec_id, [], returnables)
                
                if not suppliers:
                    st.warning("No suppliers found for evaluation. Upload supplier files first.")
                else:
                    st.success(f"Found {len(suppliers)} suppliers for evaluation.")
                    
                    # Show evaluation criteria being used
                    st.subheader("📋 Evaluation Criteria")
                    try:
                        weights = load_tepp_weights(tepp)
                        if weights:
                            criteria_df = pd.DataFrame([
                                {"Criterion": criterion, "Weight (%)": f"{weight:.1f}%"}
                                for criterion, weight in weights.items()
                            ])
                            st.dataframe(criteria_df, use_container_width=True)
                        else:
                            st.warning("No evaluation criteria found in TEPP.")
                    except Exception as e:
                        st.warning(f"Could not load evaluation criteria: {e}")
                    
                    # Perform actual evaluation scoring
                    with st.spinner("Evaluating suppliers against TEPP criteria..."):
                        evaluation_results = perform_supplier_evaluation(rec_id, suppliers, tepp, returnables)
                    
                    if evaluation_results:
                        st.subheader("📊 Evaluation Results")
                        
                        # Display results table with enhanced formatting
                        results_df = pd.DataFrame(evaluation_results)
                        
                        # Reorder columns to put Supplier Name first
                        cols = ['Supplier Name', 'Supplier ID', 'Total Score'] + [col for col in results_df.columns if col not in ['Supplier Name', 'Supplier ID', 'Total Score']]
                        results_df = results_df[cols]
                        
                        # Format the dataframe for better display
                        st.dataframe(results_df, use_container_width=True)
                        
                        # Show ranking with enhanced formatting
                        st.subheader("🏆 Supplier Ranking")
                        ranking_df = results_df.sort_values('Total Score', ascending=False).reset_index(drop=True)
                        ranking_df['Rank'] = range(1, len(ranking_df) + 1)
                        
                        # Reorder ranking columns to emphasize company names
                        ranking_cols = ['Rank', 'Supplier Name', 'Total Score']
                        ranking_display = ranking_df[ranking_cols].copy()
                        
                        # Add some styling information
                        st.info(f"📈 **Total Suppliers Evaluated**: {len(ranking_df)}")
                        st.dataframe(ranking_display, use_container_width=True)
                        
                        # Show top 3 suppliers prominently
                        if len(ranking_df) >= 3:
                            st.subheader("🥇 Top 3 Suppliers")
                            top_3 = ranking_df.head(3)
                            for i, (_, row) in enumerate(top_3.iterrows()):
                                medal = ["🥇", "🥈", "🥉"][i]
                                st.success(f"{medal} **{row['Supplier Name']}** - Score: {row['Total Score']:.2f}")
                        
                        # Show detailed scores
                        with _sticky_expander("📈 Detailed Scores", key="eval.detailed_scores", default_expanded=False):
                            score_cols = [col for col in results_df.columns if col not in ['Supplier ID', 'Supplier Name', 'Total Score']]
                            detailed_df = results_df[['Supplier Name'] + score_cols]
                            st.dataframe(detailed_df, use_container_width=True)
                    else:
                        st.warning("Evaluation completed but no results generated.")
                        
            except Exception as e:
                st.error(f"Evaluation failed: {e}")
                st.exception(e)

    st.divider()
    st.subheader("Current supplier files")
    
    # Show processed suppliers from manifest
    try:
        suppliers = process_suppliers(rec_id, [], returnables)
        if suppliers:
            st.success(f"Found {len(suppliers)} processed suppliers:")
            
            # Create enhanced supplier display
            supplier_data = []
            for s in suppliers:
                supplier_name = s.get("name", "")
                # If name is generic or just the filename, try to extract better name
                if (not supplier_name or 
                    supplier_name.lower() in ["name", "company name", "organization name", "business name"] or
                    supplier_name == s.get("filename", "").replace(".pdf", "").replace(".docx", "")):
                    # Try to extract a better name from the filename
                    filename = s.get("filename", "")
                    if filename:
                        # Remove common prefixes and extensions
                        clean_name = filename.replace("C112025-Part-5-Returnable-Schedules-", "").replace("C112025_SDE_Returnable-Schedules", "")
                        clean_name = clean_name.replace(".pdf", "").replace(".docx", "").replace(".doc", "")
                        if clean_name and len(clean_name) > 3:
                            supplier_name = f"Company {clean_name}"
                        else:
                            supplier_name = f"Company {s.get('id', 'Unknown')}"
                    else:
                        supplier_name = f"Company {s.get('id', 'Unknown')}"
                
                supplier_data.append({
                    "🏢 Company Name": supplier_name,
                    "📄 Original Filename": s.get("filename", ""),
                    "🆔 ID": s.get("id", ""),
                    "📅 Uploaded": s.get("uploaded_at", ""),
                })
            
            supplier_df = pd.DataFrame(supplier_data)
            st.dataframe(supplier_df, use_container_width=True)
            
            # Show company names prominently
            st.subheader("🏢 Identified Companies")
            for i, supplier in enumerate(suppliers, 1):
                company_name = supplier.get("name", f"Company {supplier.get('id', 'Unknown')}")
                
                # Fix generic "Name" values
                if company_name.lower() in ["name", "company name", "organization name", "business name"]:
                    filename = supplier.get("filename", "")
                    if filename:
                        # Try to extract a better name from the filename
                        clean_name = filename.replace("C112025-Part-5-Returnable-Schedules-", "").replace("C112025_SDE_Returnable-Schedules", "")
                        clean_name = clean_name.replace(".pdf", "").replace(".docx", "").replace(".doc", "")
                        if clean_name and len(clean_name) > 3:
                            company_name = f"Company {clean_name}"
                        else:
                            company_name = f"Company {supplier.get('id', 'Unknown')}"
                    else:
                        company_name = f"Company {supplier.get('id', 'Unknown')}"
                
                filename = supplier.get("filename", "Unknown file")
                st.write(f"**{i}.** {company_name} *(from {filename})*")
            
            # Add button to refresh supplier names
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🔄 Refresh Company Names", help="Re-extract company names from uploaded documents"):
                    try:
                        from app.services.supplier import _load_suppliers, _save_suppliers, _supplier_display_name, _read_json
                        from app.services.supplier import _path_supplier_returnables
                        
                        # Reload and update supplier names
                        updated_suppliers = []
                        for supplier in suppliers:
                            supplier_id = supplier.get("id")
                            if supplier_id:
                                # Try to read the returnables file to extract better name
                                try:
                                    returnables_path = _path_supplier_returnables(rec_id, supplier_id)
                                    if returnables_path.exists():
                                        returnables_data = _read_json(returnables_path)
                                        new_name = _supplier_display_name(returnables_data, supplier.get("filename", ""))
                                        
                                        # If still generic, try raw text extraction
                                        if new_name.lower() in ["name", "company name", "organization name", "business name"]:
                                            from app.services.supplier import _extract_company_name_from_raw_text
                                            raw_path = Path(supplier.get("raw_path", ""))
                                            if raw_path.exists():
                                                raw_name = _extract_company_name_from_raw_text(raw_path)
                                                if raw_name:
                                                    new_name = raw_name
                                        
                                        supplier["name"] = new_name
                                except Exception:
                                    pass
                            updated_suppliers.append(supplier)
                        
                        # Save updated manifest
                        from app.services.supplier import _save_suppliers
                        _save_suppliers(rec_id, updated_suppliers)
                        st.success("Company names refreshed! Please refresh the page to see updated names.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to refresh company names: {e}")
            
            with col2:
                st.caption("💡 Company names are automatically extracted from documents")
        else:
            st.info("No processed suppliers found.")
    except Exception as e:
        st.warning(f"Could not load supplier manifest: {e}")
    
    # Also show raw files in directory
    try:
        entries = sorted([p.name for p in sup_dir.iterdir() if p.is_file()])
        if entries:
            st.subheader("Raw files in directory")
            for name in entries:
                st.write(f"• {name}")
        else:
            st.write("No raw files in supplier directory.")
    except Exception as e:
        st.warning(f"Could not list supplier files: {e}")

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main():
    st.set_page_config(page_title="AIT – Tender Docs", layout="wide")
    _inject_css()

    # Sidebar: auth info + logout
    with st.sidebar:
        user = st.session_state.get("auth_user")
        if user:
            st.caption(f"Signed in as **{user}**")
            if st.button("Log out"):
                st.session_state.clear()
                st.query_params.clear()
                st.query_params.update({"view": "login"})
                st.rerun()

    view = st.query_params.get("view", "home")
    _nav_init()
    if isinstance(view, list): view = view[0]

    # ---------- AUTH GUARD ----------
    authed = bool(st.session_state.get("auth_user"))
    # If not authenticated and not already on login, redirect to login and remember intended view
    if not authed and view != "login":
        st.query_params.clear()
        st.query_params.update({"view": "login", "next": view})
        return page_login()
    # If authenticated but still on login page, bounce to home
    if authed and view == "login":
        st.query_params.clear()
        st.query_params.update({"view": "home"})
        st.rerun()
    # If on login (unauthenticated), show login page
    if view == "login":
        return page_login()
    # --------------------------------

    pc = st.query_params.get("purchase_category")
    if isinstance(pc, list): pc = pc[0]
    if pc:
        st.session_state.purchase_category = pc

    if view == "home":
        page_home()
    elif view == "upload":
        page_upload()
    elif view == "evaluation":
        page_evaluation()
    else:
        page_results()

if __name__ == "__main__":
    main()
