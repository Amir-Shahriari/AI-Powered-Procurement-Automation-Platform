"""
Streamlit UI: Generate TEPP & Returnables, then evaluate supplier responses.

Run:
    streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import os
import sys
import io
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------
# Put the repo root on sys.path so 'app.*' imports are stable
# ---------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------
# Project imports (concrete modules; avoid the compose name collision)
# ---------------------------------------------------------------------
from app.config import settings
from app.schemas import SpecSummary

from app.services.textio import extract_text, chunks
from app.services.vectorstores import build_index, get_vs
from app.services.llm import rag_json, set_runtime_model, reset_runtime_model
from app.services.parse_spec import parse_spec
from app.services.policy import scan_policy_files, extract_many, _build_ephemeral_vs

# IMPORTANT: import from the **submodules**, not app.services.compose (file)
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
    _create_evaluation_workbook,
    _data_dir as _supplier_data_dir,
)

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
                if arr: return arr
            if isinstance(val, (list, tuple)):
                arr = [str(m).strip() for m in val if str(m).strip()]
                if arr: return arr

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
# Small helpers
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
        "consultancy contract valued at over $249,999": "Evaluation Criteria for consultancy contracts ($250k+).",
        "service delivery contract valued at over $249,999": "Evaluation Criteria for service delivery contracts ($250k+).",
        "management contract valued at over $249,999": "Evaluation Criteria for management contracts ($250k+).",
        "lease / license valued at over $249,999": "Evaluation Criteria for lease/licence ($250k+).",
    }
    return mapping.get(category_key_lower, "Evaluation Criteria.")

def _get_tepp_criteria(tepp: dict) -> List[Dict[str, str]]:
    return tepp.setdefault("tender_evaluation", {}) \
               .setdefault("evaluation_methodology", {}) \
               .get("required_criteria_table", []) or []

def _set_tepp_criteria(tepp: dict, rows: List[Dict]) -> None:
    tepp.setdefault("tender_evaluation", {}) \
        .setdefault("evaluation_methodology", {})["required_criteria_table"] = rows

def _recompute_weights_inplace(tepp: dict, parsed: dict, category_key_lower: str) -> None:
    """Rebuild Required Criteria table using current purchase category + parsed features."""
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
            import re
            m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*to\s*(\d+(?:\.\d+)?)\s*%", (s or ""), re.I)
            if m: return (float(m.group(1)) + float(m.group(2))) / 2.0
            m2 = re.search(r"(\d+(?:\.\d+)?)\s*%", (s or ""), re.I)
            return float(m2.group(1)) if m2 else 0.0

        price = _mid(price_rng or "50%")
        sust = round(price * 0.10, 1) if "construction contract valued at over $249,999" in category_key_lower \
            or "standard product" in category_key_lower or "service delivery" in category_key_lower \
            or "consultancy" in category_key_lower else 0.0

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
    for k, v in list(payload.items()):
        if isinstance(v, list) and v:
            payload[k] = v[0]
    payload["view"] = view
    if extra:
        payload.update(extra)
    st.query_params.clear()
    st.query_params.update(payload)
    st.rerun()


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

        # 6) Extra policy VS (optional)
        policy_files = scan_policy_files()
        policy_texts = extract_many(policy_files)
        policy_chunks: List[str] = []
        for t in (policy_texts or []):
            s = _coerce_to_text(t)
            if s.strip():
                # Split using your deps splitter settings
                from app.deps import SPLITTER
                policy_chunks.extend(SPLITTER.split_text(s))
        vs_policy = _build_ephemeral_vs(policy_chunks) if policy_chunks else None

        # 7) Compose TEPP & Returnables (correct signatures)
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
# Evaluation helpers (NEW)
# ==========================
import re
from collections import Counter

def _supplier_json_paths(rec_id: str) -> List[Path]:
    """Find all supplier returnables JSON saved by process_suppliers."""
    try:
        from app.services.supplier import _data_dir as _s_data_dir
        root = _s_data_dir()
    except Exception:
        root = settings.DATA_DIR
    return sorted(Path(root).glob(f"{rec_id}_supplier_*.returnables.json"))

def _deep_iter_kv(obj, path=""):
    """Yield (path, key, value) for dicts/lists recursively."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            newp = f"{path}.{k}" if path else str(k)
            yield from _deep_iter_kv(v, newp)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            newp = f"{path}[{i}]"
            yield from _deep_iter_kv(v, newp)
    else:
        yield path, None, obj

def _flatten_texts(obj) -> List[str]:
    out = []
    for _, _, v in _deep_iter_kv(obj):
        if isinstance(v, (str, int, float, bool)):
            out.append(str(v))
    return out

_PRICE_KEY_HINTS = {"total_price","price_total","tender_price","sum","subtotal","total","amount","lump_sum"}
_PRICE_CTX_HINTS = {"price","cost","offer","tender","gst","ex gst","incl gst","exc gst","exclusive","inclusive","net","gross","fee"}

def _extract_price_any(payload: Any) -> Optional[float]:
    """
    Try hard to find a single 'total price' value from a supplier returnables JSON.
    1) Prefer obvious keys.
    2) Else, search text for currency-like numbers and choose a conservative candidate (median of top-3).
    """
    # 1) Obvious key scan
    found: List[float] = []
    def _coerce_num(x):
        try:
            s = str(x)
            s = re.sub(r"[^\d.,()-]", "", s)
            s = s.replace(",", "")
            m = re.search(r"-?\(?\d+(?:\.\d+)?\)?", s)
            if not m:
                return None
            num = m.group(0)
            neg = "(" in s and ")" in s
            val = float(num.replace("(", "").replace(")", ""))
            return -val if neg else val
        except Exception:
            return None

    if isinstance(payload, dict):
        for k, v in payload.items():
            lk = str(k).lower().strip()
            if lk in _PRICE_KEY_HINTS or any(h in lk for h in _PRICE_CTX_HINTS):
                num = _coerce_num(v)
                if isinstance(num, (int, float)) and num != 0:
                    found.append(float(num))

    # 2) Text sweep
    if not found:
        texts = " ".join(_flatten_texts(payload)).lower()
        # match things like $123,456.78 or 123456.78
        cand = re.findall(r"(?:\$|aud\$?)?\s*([1-9]\d{2,}(?:\.\d{2})?)", texts)
        nums = []
        for c in cand:
            try:
                n = float(c.replace(",", ""))
                if n > 0:
                    nums.append(n)
            except Exception:
                pass
        if nums:
            nums.sort()
            mid_idx = len(nums)//2
            found = [nums[min(mid_idx, len(nums)-1)]]

    if not found:
        return None
    # Return the largest found (tends to be 'total' vs line items)
    return max(found)

def _presence_score(payload: Any, keywords: List[str]) -> float:
    """
    0-100 based on how many thematic keywords appear at least once across all text fields.
    """
    texts = " ".join(_flatten_texts(payload)).lower()
    hit = 0
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw.lower())}\b", texts):
            hit += 1
    if not keywords:
        return 0.0
    return min(100.0, 100.0 * hit / len(keywords))

def _coverage_score(payload: Any, sections: List[str]) -> float:
    """
    0-100: For section-like keywords (e.g., 'experience', 'methodology'), 
    approximate coverage via counts of occurrences plus presence.
    """
    texts = " ".join(_flatten_texts(payload)).lower()
    c = Counter()
    for s in sections:
        # count occurrences roughly
        c[s] = len(re.findall(rf"\b{re.escape(s.lower())}\b", texts))
    if not sections:
        return 0.0
    present = sum(1 for s in sections if c[s] > 0)
    # Presence (50%) + scaled frequency (50%, capped)
    presence_part = 100.0 * present / len(sections)
    freq_part = min(100.0, 10.0 * sum(min(5, c[s]) for s in sections))  # cap per-section at 5 hits
    return 0.5 * presence_part + 0.5 * freq_part

# Per-criterion scorers derived from supplier returnables JSON
SCORERS = {
    "Relevant Experience": lambda j: _coverage_score(j, ["experience","project","reference","referee","past performance"]),
    "Capability": lambda j: _coverage_score(j, ["capability","resources","equipment","methodology","approach","schedule"]),
    "Management & Financial Capacity": lambda j: _coverage_score(j, ["financial","capacity","org chart","insurance","licence","license","policy"]),
    "Quality Management": lambda j: _presence_score(j, ["quality","qa","qc","iso 9001","quality management"]),
    "WHS": lambda j: _presence_score(j, ["whs","ohs","safety","swms","incident","risk","hazard"]),
    "Sustainability and EEO & Fair Employment": lambda j: _presence_score(j, ["sustainability","environment","eeo","diversity","modern slavery","recycled","carbon"]),
    # "Price (Full Cost)" handled separately via normalisation
}

def _load_tepp_weights(tepp: dict) -> Dict[str, float]:
    rows = tepp.get("tender_evaluation", {}).get("evaluation_methodology", {}).get("required_criteria_table", []) or []
    out = {}
    for r in rows:
        crit = str(r.get("criterion", "")).strip()
        w = str(r.get("weight", "0")).strip().replace("%", "")
        try:
            out[crit] = float(w)
        except Exception:
            pass
    return out

def _compute_price_scores(price_map: Dict[str, Optional[float]]) -> Dict[str, float]:
    """Return 0..100 price score per supplier where min price gets 100."""
    vals = [v for v in price_map.values() if isinstance(v, (int,float)) and v > 0]
    if not vals:
        return {k: 0.0 for k in price_map}
    pmin = min(vals)
    return {k: (pmin / v * 100.0) if (v and v > 0) else 0.0 for k, v in price_map.items()}

def _score_supplier(payload: dict, crit_weights: Dict[str, float], price_score: float) -> Dict[str, float]:
    """Return raw 0..100 per-criterion + total weighted."""
    per_crit = {}
    total = 0.0
    for crit, w in crit_weights.items():
        if crit == "Price (Full Cost)":
            raw = price_score
        else:
            f = SCORERS.get(crit)
            raw = float(f(payload)) if f else 0.0
        per_crit[crit] = raw
        total += raw * (w / 100.0)
    per_crit["_total_weighted"] = round(total, 2)
    return per_crit

# ---------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------
def page_home():
    st.markdown('<div class="page-header"><h1>Before Advertisement</h1></div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Model & Category")

    # Model picker
    options = discover_models()
    prev = st.session_state.get("selected_model", options[0])
    model = st.selectbox("Model", options, index=(options.index(prev) if prev in options else 0))
    st.session_state.selected_model = model

    # Category & purchase cat
    categories = list_categories(doc_type="tepp")  # show only cats that have TEPP templates
    default_purchase = st.session_state.get("purchase_category", "construction contract valued at over $249,999")
    if default_purchase not in PURCHASE_CATEGORIES:
        default_purchase = "construction contract valued at over $249,999"

    col1, col2 = st.columns(2)
    with col1:
        sel_cat = st.selectbox("Tender Category (for template merge)", categories, key="selected_category")
    with col2:
        sel_purchase = st.selectbox("Purchase Category (policy ranges)", PURCHASE_CATEGORIES,
                                    index=PURCHASE_CATEGORIES.index(default_purchase),
                                    key="selected_purchase_category")

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Continue to Upload"):
        _nav_set("upload", {
            "model": model,
            "category": sel_cat,
            "purchase_category": sel_purchase,
        })


def page_upload():
    st.title("Upload Specification")
    st.markdown(
        '<div class="card fade-in">Upload your technical specification file. After generation you will be redirected to the results page.</div>',
        unsafe_allow_html=True
    )

    uploaded = st.file_uploader(
        "Technical specification",
        type=["pdf", "docx", "txt", "doc"],
        help="Provide the tender specification file (PDF, DOCX, DOC or TXT).",
    )
    if uploaded is None:
        return

    if st.button("Generate TEPP and Returnables"):
        # Write uploaded to a temp location and run pipeline
        tmp = settings.DATA_DIR / f"upload_{uuid.uuid4().hex}{Path(uploaded.name).suffix}"
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(tmp, "wb") as f:
            f.write(uploaded.read())

        qp = st.query_params
        model = qp.get("model", st.session_state.get("selected_model", "llama3.1:8b"))
        category = qp.get("category", st.session_state.get("selected_category", "generic"))
        purchase_category = qp.get("purchase_category", st.session_state.get("selected_purchase_category", None))
        if isinstance(model, list): model = model[0]
        if isinstance(category, list): category = category[0]
        if isinstance(purchase_category, list): purchase_category = purchase_category[0]

        outputs = _generate_documents(tmp, model, purchase_category)

        # Merge category templates (if present)
        tepp_tmpl = load_category_template("tepp", category)
        ret_tmpl = load_category_template("returnable_schedules", category)
        merged_tepp = deep_merge(tepp_tmpl, outputs["tepp"])
        merged_ret = deep_merge(ret_tmpl, outputs["returnables"])

        # Persist merged (overwrite the base on disk so evaluation uses merged copy)
        rec_id = outputs["rec_id"]
        (settings.DATA_DIR / f"{rec_id}.tepp.json").write_text(json.dumps(merged_tepp, indent=2, ensure_ascii=False), encoding="utf-8")
        (settings.DATA_DIR / f"{rec_id}.returnables.json").write_text(json.dumps(merged_ret, indent=2, ensure_ascii=False), encoding="utf-8")

        # Session
        st.session_state["record_id"] = rec_id
        st.session_state["tepp"] = merged_tepp
        st.session_state["returnables"] = merged_ret
        st.session_state["spec_summary"] = outputs["spec_summary"]
        st.session_state["parsed"] = outputs["parsed"]
        st.session_state["purchase_category"] = purchase_category or st.session_state.get("purchase_category", None)

        _nav_set("results", {"rec_id": rec_id})


def page_results():
    st.markdown('<div class="page-header"><h1>Results</h1></div>', unsafe_allow_html=True)

    tepp = st.session_state.get("tepp") or {}
    returnables = st.session_state.get("returnables") or {}
    parsed = st.session_state.get("parsed") or {}
    chosen_purchase = st.session_state.get("purchase_category", "construction contract valued at over $249,999")
    chosen_key = (chosen_purchase or "").strip().lower()

    if not tepp:
        st.info("No TEPP in session. Go back to Upload.")
        return

    tabs = st.tabs(["TEPP", "Returnables", "Raw JSON"])

    # --------------- TEPP ---------------
    with tabs[0]:
        st.subheader("TEPP Overview")
        em = tepp.setdefault("tender_evaluation", {}).setdefault("evaluation_methodology", {})
        em["required_criteria_caption"] = _dynamic_caption_for_category(chosen_key)
        rows = _get_tepp_criteria(tepp)

        edited_rows = _edit_table(rows, key="criteria_editor")
        if st.button("Save Evaluation Criteria Table", key="save_crit"):
            _set_tepp_criteria(tepp, edited_rows)
            st.session_state["tepp"] = tepp
            (settings.DATA_DIR / f"{st.session_state.get('record_id')}.tepp.json").write_text(
                json.dumps(tepp, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            st.success("Criteria table saved to TEPP JSON.")

        st.caption("Re-run weighting strictly within policy ranges for the current purchase category.")
        if st.button("Recompute weights from purchase category", key="recalc_weights"):
            parsed["purchase_category"] = chosen_purchase
            _recompute_weights_inplace(tepp, parsed, (parsed.get("purchase_category") or "").strip().lower())
            st.session_state["parsed"] = parsed
            st.session_state["tepp"] = tepp
            (settings.DATA_DIR / f"{st.session_state.get('record_id')}.tepp.json").write_text(
                json.dumps(tepp, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            st.success("Weights recomputed and persisted.")

        st.divider()
        if st.button("Evaluate supplier responses →", key="go_eval"):
            _nav_set("evaluation", {"rec_id": st.session_state.get("record_id")})

    # --------------- Returnables ---------------
    with tabs[1]:
        st.subheader("Returnable Schedules")
        st.caption("Edit the generated JSON below or export to DOCX.")
        if st.button("Build Returnables DOCX", key="build_ret_docx"):
            docx_path = export_json_to_docx(returnables, "Returnable Schedules")
            with open(docx_path, "rb") as f:
                st.download_button(
                    "Download Returnables",
                    f.read(),
                    file_name="returnables.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="dlbtn_ret"
                )

    # --------------- Raw JSON ---------------
    with tabs[2]:
        r1, r2 = st.tabs(["TEPP JSON", "Returnables JSON"])
        with r1:
            tepp_str = json.dumps(tepp, indent=2, ensure_ascii=False)
            new_tepp_str = st.text_area("TEPP JSON", value=tepp_str, height=360, key="tepp_json_raw")
            if st.button("Apply TEPP JSON"):
                try:
                    tepp = json.loads(new_tepp_str)
                    st.session_state["tepp"] = tepp
                    (settings.DATA_DIR / f"{st.session_state.get('record_id')}.tepp.json").write_text(
                        json.dumps(tepp, indent=2, ensure_ascii=False), encoding="utf-8"
                    )
                    st.success("TEPP JSON applied and saved.")
                except Exception as e:
                    st.error(f"Invalid JSON: {e}")
        with r2:
            ret_str = json.dumps(returnables, indent=2, ensure_ascii=False)
            new_ret_str = st.text_area("Returnables JSON", value=ret_str, height=360, key="ret_json_raw")
            if st.button("Apply Returnables JSON"):
                try:
                    ret = json.loads(new_ret_str)
                    st.session_state["returnables"] = ret
                    (settings.DATA_DIR / f"{st.session_state.get('record_id')}.returnables.json").write_text(
                        json.dumps(ret, indent=2, ensure_ascii=False), encoding="utf-8"
                    )
                    st.success("Returnables JSON applied and saved.")
                except Exception as e:
                    st.error(f"Invalid JSON: {e}")


def page_evaluation():
    st.title("Evaluation")
    st.markdown(
        '<div class="card fade-in">Upload filled supplier Returnable Schedules and evaluate them here using your TEPP weights. You can also export Excel if needed.</div>',
        unsafe_allow_html=True
    )

    rec_id = st.session_state.get("record_id") or st.query_params.get("rec_id")
    if isinstance(rec_id, list):
        rec_id = rec_id[0]
    if not rec_id:
        st.error("No active record found. Generate TEPP/Returnables first.")
        return

    # Load TEPP (for weights) + baseline returnables (for schema context if needed)
    tepp_path = settings.DATA_DIR / f"{rec_id}.tepp.json"
    ret_path = settings.DATA_DIR / f"{rec_id}.returnables.json"
    try:
        tepp = json.loads(tepp_path.read_text(encoding="utf-8"))
    except Exception:
        st.error("TEPP JSON missing. Please re-run generation.")
        return
    try:
        base_returnables = json.loads(ret_path.read_text(encoding="utf-8")) if ret_path.exists() else {}
    except Exception:
        base_returnables = {}

    # Show criteria & weights
    st.subheader("Criteria & Weights (from TEPP)")
    weights = _load_tepp_weights(tepp)
    if not weights:
        st.warning("No criteria table found in TEPP → Results → Evaluation Criteria.")
    else:
        st.dataframe(
            pd.DataFrame(
                [{"criterion": k, "weight %": v} for k, v in weights.items()]
            ).sort_values("criterion"),
            use_container_width=True
        )

    st.divider()
    st.subheader("Upload supplier responses")
    up_files = st.file_uploader(
        "Supplier files (PDF/DOCX/DOC/TXT/JSON). Multiple allowed.",
        type=["pdf", "docx", "doc", "txt", "json"],
        accept_multiple_files=True,
        help="For JSON uploads, provide the supplier's filled Returnables JSON with the same schema as your baseline."
    )

    # Ingest uploads via your supplier service
    if st.button("Process uploads"):
        from app.services.supplier import process_suppliers, _data_dir as _s_data_dir
        class _Wrap:
            def __init__(self, uf):
                self.filename = getattr(uf, "name", None) or getattr(uf, "filename", "upload.bin")
                self.file = io.BytesIO(uf.read())

        normal = []
        json_count = 0
        for uf in up_files or []:
            nm = (getattr(uf, "name", None) or getattr(uf, "filename", "upload")).lower()
            if nm.endswith(".json"):
                try:
                    payload = json.loads(uf.read().decode("utf-8", errors="ignore"))
                    sup_id = str(uuid.uuid4())[:8]
                    out_path = _s_data_dir() / f"{rec_id}_supplier_{sup_id}.returnables.json"
                    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                    json_count += 1
                except Exception as e:
                    st.error(f"Failed to ingest JSON '{nm}': {e}")
            else:
                normal.append(_Wrap(uf))
        try:
            manifest = process_suppliers(rec_id, normal, base_returnables or {})
            st.success(f"Processed {len(normal)} file(s), plus {json_count} JSON returnables.")
        except Exception as e:
            st.exception(e)

    # List discovered suppliers from disk
    from app.services.supplier import list_suppliers
    manifest = []
    try:
        manifest = list_suppliers(rec_id) or []
    except Exception:
        pass

    if manifest:
        st.subheader("Suppliers discovered")
        st.dataframe(pd.DataFrame(manifest), use_container_width=True)
    else:
        st.info("No suppliers found yet. Upload above to populate.")

    st.divider()
    st.subheader("In-app evaluation (based on TEPP & supplier returnables)")
    st.caption("This runs a rule-based evaluation in the app: price is normalised; qualitative criteria are scored from the supplier’s filled returnables. You can still export a richer Excel using your service.")

    # ----- Run evaluation in-app -----
    if st.button("Run evaluation now"):
        # Load each supplier's returnables JSON
        supplier_paths = _supplier_json_paths(rec_id)
        suppliers_payloads: Dict[str, dict] = {}
        for p in supplier_paths:
            try:
                payload = json.loads(p.read_text(encoding="utf-8"))
                sid = p.stem.split("_supplier_")[-1].replace(".returnables","")
                suppliers_payloads[sid] = payload
            except Exception:
                pass

        if not suppliers_payloads:
            st.warning("No supplier returnables JSON found. Ensure uploads are processed or JSON returnables exist.")
            return

        # Extract prices (from payload or manifest fallback), then price-normalised scores
        price_map: Dict[str, Optional[float]] = {}
        name_map: Dict[str, str] = {}
        # Use manifest names if available
        for m in (manifest or []):
            if m.get("id"):
                name_map[m["id"]] = m.get("name") or m.get("id")

        for sid, payload in suppliers_payloads.items():
            price_map[sid] = _extract_price_any(payload)

        # Fallback: if we couldn't locate a price in JSON, try manifest['price']
        for m in (manifest or []):
            sid = m.get("id")
            if sid in price_map and (price_map[sid] is None or price_map[sid] == 0):
                try:
                    price_map[sid] = float(m.get("price")) if m.get("price") not in (None, "") else None
                except Exception:
                    pass

        price_scores = _compute_price_scores(price_map)

        # Score per-criterion
        results_rows = []
        for sid, payload in suppliers_payloads.items():
            per = _score_supplier(payload, weights, price_scores.get(sid, 0.0))
            row = {
                "supplier_id": sid,
                "supplier": name_map.get(sid, sid),
                "price": price_map.get(sid),
                "price_score": round(price_scores.get(sid, 0.0), 2),
                **{f"{k} (raw)": round(v,2) for k, v in per.items() if k != "_total_weighted"},
                "TOTAL (weighted)": per["_total_weighted"],
            }
            results_rows.append(row)

        if not results_rows:
            st.warning("No results computed.")
            return

        df = pd.DataFrame(results_rows).sort_values("TOTAL (weighted)", ascending=False).reset_index(drop=True)
        st.subheader("Scorecard")
        st.dataframe(df, use_container_width=True)

        # Per-criterion bars
        crits = [c for c in weights.keys()]
        if crits:
            st.subheader("Per-criterion comparison")
            for crit in crits:
                col = f"{crit} (raw)"
                if col in df.columns:
                    st.write(f"**{crit}**")
                    st.bar_chart(df.set_index("supplier")[col])

        # Download CSV (optional)
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download scorecard (CSV)", csv_bytes, file_name="evaluation_scorecard.csv", mime="text/csv")

    st.divider()
    st.subheader("Export Excel (service-generated)")
    st.caption("If you want the full multi-sheet workbook with price normalisation and scoring matrix.")
    if st.button("Generate workbook (.xlsx)", key="gen_eval_xlsx"):
        try:
            from app.services.supplier import _load_weights_from_tepp, _create_evaluation_workbook
            weights2 = _load_weights_from_tepp(rec_id)
            path = _create_evaluation_workbook(rec_id, manifest or [], weights2)
            with open(path, "rb") as f:
                st.download_button(
                    "Download evaluation.xlsx",
                    f.read(),
                    file_name="evaluation.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_eval_xlsx"
                )
        except Exception as e:
            st.exception(e)


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main():
    st.set_page_config(page_title="AIT – Tender Docs", layout="wide")
    _inject_css()

    view = st.query_params.get("view", "home")
    if isinstance(view, list): view = view[0]
    # Keep purchase category from query in session
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
