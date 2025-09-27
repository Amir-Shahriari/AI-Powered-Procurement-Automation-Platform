# app/services/compose/tepp.py
from __future__ import annotations
import calendar
from datetime import datetime, date, timedelta
import json
import re
from typing import Any, Dict, List, Optional
from collections import OrderedDict

from langchain.schema import SystemMessage, HumanMessage
from app.services.llm import _llm
from app.services.base import rag_json_plus, unique_keep_order, _try_parse_json
from app.services.templates import load_tepp_template
from app.services.returnables import compose_returnable_schedules

# =============================================================================
# Small safety helpers (type normalisers)
# =============================================================================

def _to_str(x) -> str:
    """Coerce unknown LLM field types into a safe string."""
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, dict) and "text" in x and isinstance(x["text"], str):
        # common pattern when models wrap text
        return x["text"]
    try:
        return json.dumps(x, ensure_ascii=False)
    except Exception:
        return str(x)


def _ensure_dict(obj: Dict[str, Any], key: str) -> Dict[str, Any]:
    val = obj.get(key)
    if not isinstance(val, dict):
        obj[key] = {}
    return obj[key]

def _ensure_list_path(root: Dict[str, Any], path: List[str]) -> List[Any]:
    cur = root
    for i, k in enumerate(path):
        last = i == len(path) - 1
        if last:
            v = cur.get(k)
            if v is None:
                cur[k] = []
            elif isinstance(v, list):
                pass
            elif isinstance(v, (str, int, float, bool, dict)):
                cur[k] = [v]
            else:
                cur[k] = []
            return cur[k]
        else:
            v = cur.get(k)
            if not isinstance(v, dict):
                cur[k] = {}
            cur = cur[k]
    return []

def _as_list(v) -> List[str]:
    if not v:
        return []
    if isinstance(v, list):
        return [str(x) for x in v if isinstance(x, (str, int, float, bool)) and str(x).strip()]
    if isinstance(v, (str, int, float, bool)) and str(v).strip():
        return [str(v).strip()]
    return []

def _join_bullets(lines: List[str]) -> str:
    cleaned: List[str] = []
    for l in (lines or []):
        s = str(l).strip()
        if not s:
            continue
        s = re.sub(r"^\s*[•\-]\s*", "", s)
        cleaned.append("• " + s)
    return "\n".join(cleaned)

# =============================================================================
# Category ranges (NO “over $249,999” variants)
# =============================================================================

CATEGORY_WEIGHT_RANGES: Dict[str, Dict[str, str]] = {
    # Standard goods
    "standard product or good": {
        "Price (Full Cost)": "40% to 60%",
        "Relevant Experience": "10% to 30%",
        "Capability": "10% to 30%",
        "Management & Financial Capacity": "5% to 10%",
        "WHS": "5% to 10%",
    },
    # Construction
    "construction contract": {
        "Price (Full Cost)": "35% to 60%",
        "Relevant Experience": "10% to 20%",
        "Capability": "10% to 20%",
        "Management & Financial Capacity": "5% to 15%",
        "Quality Management": "5% to 10%",
        "WHS": "5% to 10%",
    },
    # Consultancy
    "consultancy contract": {
        "Price (Full Cost)": "25% to 50%",
        "Relevant Experience": "10% to 30%",
        "Capability": "10% to 30%",
        "Management & Financial Capacity": "5% to 10%",
        "WHS": "5% to 10%",
    },
    # Service delivery
    "service delivery contract": {
        "Price (Full Cost)": "30% to 50%",
        "Relevant Experience": "10% to 30%",
        "Capability": "10% to 30%",
        "Management & Financial Capacity": "5% to 10%",
        "Quality Management": "5% to 10%",
        "WHS": "5% to 10%",
    },
    # Management / Lease
    "management contract": {
        "Price (Full Cost)": "30% to 50%",
        "Relevant Experience": "10% to 30%",
        "Capability": "10% to 30%",
        "Management & Financial Capacity": "5% to 15%",
        "Quality Management": "5% to 10%",
        "WHS": "0% to 10%",
    },
    "lease / license": {
        "Price (Full Cost)": "30% to 50%",
        "Relevant Experience": "10% to 30%",
        "Capability": "10% to 30%",
        "Management & Financial Capacity": "5% to 15%",
        "Quality Management": "5% to 10%",
        "WHS": "0% to 10%",
    },
}
PURCHASE_CATEGORIES: List[str] = list(CATEGORY_WEIGHT_RANGES.keys())

# Map common synonyms → canonical key in CATEGORY_WEIGHT_RANGES
_CATEGORY_SYNONYMS = {
    "construction": "construction contract",
    "construction contract": "construction contract",
    "consultancy": "consultancy contract",
    "consultant": "consultancy contract",
    "service delivery": "service delivery contract",
    "service": "service delivery contract",
    "management": "management contract",
    "lease": "lease / license",
    "licence": "lease / license",
    "license": "lease / license",
    "goods": "standard product or good",
    "standard goods": "standard product or good",
    "standard product": "standard product or good",
}

# Strip any “valued at over $249,999” / “over 249,999” qualifiers, then normalise
_OVER_CLAUSE = re.compile(
    r"(valued\s+at\s+over\s+\$?\s*249,?999|over\s+\$?\s*249,?999)",
    re.IGNORECASE,
)

def _normalise_category(cat: Optional[str]) -> str:
    if not cat:
        return "construction contract"
    key = str(cat).strip().lower()
    key = _OVER_CLAUSE.sub("", key)  # drop the threshold wording if present
    key = re.sub(r"\s+", " ", re.sub(r"[^\w\s/]", " ", key)).strip()

    if key in CATEGORY_WEIGHT_RANGES:
        return key
    if key in _CATEGORY_SYNONYMS:
        return _CATEGORY_SYNONYMS[key]

    # fuzzy contains checks
    if "construction" in key:
        return "construction contract"
    if "consult" in key:
        return "consultancy contract"
    if "service" in key:
        return "service delivery contract"
    if "manage" in key:
        return "management contract"
    if "lease" in key or "license" in key or "licence" in key:
        return "lease / license"
    if "good" in key or "product" in key:
        return "standard product or good"
    return "construction contract"

# =============================================================================
# Section 1 & 2 prompts (schema-driven) with strong fallbacks
# =============================================================================

AIM_SECTION_PROMPT = """
You draft Section 1 'Aim' of a Council Tender Evaluation & Probity Plan (TEPP).
Return STRICT JSON:
{
  "intro": string,
  "body": string
}
Guidance:
- intro: One paragraph that reads like:
  "The Request for Tender (RFT) is for the {PROJECT_TITLE} to Council for the service of the procurement,
   installation, and integration of the specified works for a period specified in the context."
  Use the provided context for project title and scope. If term is present (e.g., 12 months) include it.
- body: One paragraph starting with:
  "This Tender Evaluation and Probity Plan (TEPP) is the planning and control document in conducting the evaluation
   of Tenders received in response to the RFT. The TEPP sets out:"
  Then include the EXACT four dot points as a single paragraph with bullet marks (•), separated by newlines:
    • the processes and principles to be followed when evaluating Tenders;
    • individual’s responsibilities;
    • the evaluation schedule; and
    • reporting requirements.
Use ONLY the provided context where possible. If details are missing in context, use NSW/Australian council best practice.
"""

DESC_OVERVIEW_PROMPT = """
You draft Section 2 (Description of Requirement) OVERVIEW for a council TEPP.
Provide:
- "overview": 1–2 paragraphs summarising the works described in the specification (e.g., refurbishment, supply and installation, service delivery, etc.), referencing the site or tender where available.
- "general": an array of at least 5 short, specific general requirements (licences, compliance with Australian Standards & NSW WHS, schedule & milestones, mandatory site visit, minimal disruption, etc.).
Return STRICT JSON: { "overview": [string,...], "general": [string,...] }.
"""

DESC_SUBSECTION_PROMPT_TMPL = """
You draft Section 2 (Description of Requirement) – {title} for a council TEPP.
Write a bullet list of detailed, specific, actionable items for {title}, suitable for the project's scope in NSW.
Use short imperative bullets. Use Australian context (AS/NZS standards, SafeWork NSW, relevant legislation, etc.) where relevant.
Return STRICT JSON: {{ "title": "{title}", "bullets": [string, ...] }}.
"""

DESC_INVOICING_PROMPT = """
Provide Invoicing requirements.
Return STRICT JSON: { "invoicing": [string, ...] } with at least 4 bullets (30 day terms, itemised invoices, milestone/progress payments, variations pre-approval by Council).
"""

DESC_REPORTING_PROMPT = """
Provide Reporting requirements.
Return STRICT JSON: { "reporting": [string, ...] } with weekly progress reporting bullets and a final report pack (as-built, commissioning results, O&M, lessons learned).
"""

DESC_PERFORMANCE_PROMPT = """
Provide performance monitoring note and criteria list for a council contract.
Return STRICT JSON: { "note": string, "criteria": [string, ...] }.
"""

DESC_OUTCOMES_PROMPT = """
Provide 2.1 Desired Outcomes for this engagement (council style).
Return STRICT JSON: { "desired_outcomes": [string, ...] } with at least 7 bullets (reliable delivery, timeliness, high quality, qualified staff, complaint management, contract administration, WHS, value for money).
"""

DESC_PURPOSE_RFT_PROMPT = """
Provide 2.2 Purpose of Request for Tender (RFT) for a council.
Include: legislative basis, single or panel option, reference to the works.
Return STRICT JSON: { "purpose_rft": [string, ...] }.
"""

# =============================================================================
# Generators for Section 1 & 2 (more tolerant + fallbacks)
# =============================================================================

def _gen_desc_overview(vs, tender_name: str, site_name: Optional[str], extra_vss=None):
    hints = []
    if tender_name:
        hints.append(f"Tender: {tender_name}")
    if site_name:
        hints.append(f"Site: {site_name}")
    q = ["description of requirement overview", "scope summary", tender_name or "", site_name or ""]
    prompt = DESC_OVERVIEW_PROMPT
    if hints:
        prompt += ("\n\nHints:\n" + "\n".join(f"- {h}" for h in hints))
    out = rag_json_plus(
        vs, prompt, q, extra_vss=extra_vss, max_ctx=10, min_chars=1200, allow_synthesis=True
    ) or {}
    overview = _as_list(out.get("overview"))
    general = _as_list(out.get("general"))
    if not overview:
        overview = [f"This procurement relates to {tender_name or 'the specified works'} for Council."]
    if len(general) < 5:
        general = unique_keep_order(general + [
            "Comply with relevant AS/NZS standards and NSW WHS legislation",
            "Hold all required licences and insurances before commencing works",
            "Provide detailed program and milestones; notify of delays immediately",
            "Attend mandatory site visit and verify dimensions/conditions",
            "Minimise disruption to Council operations and the public",
        ])[:8]
    return {"overview": overview, "general": general}

def _gen_subsection_titles(vs, tender_name: str, site_name: Optional[str] = None, extra_vss=None) -> List[str]:
    base_prompt = """
    You are preparing the 'Technical Requirements' section of a Council TEPP.
    Based on the provided tender name and context, propose a list of 4 to 6 concise subsection titles that
    reflect the key stages or workstreams in the specification's scope (e.g., decommissioning, supply and installation,
    electrical works, commissioning, maintenance). Avoid domain bias unless present in the context.
    Return STRICT JSON: { "subsection_titles": [string, ...] }.
    """
    queries = ["technical requirements subsection titles", tender_name or "", site_name or ""]
    try:
        out = rag_json_plus(vs, base_prompt, queries, extra_vss=extra_vss, max_ctx=8, min_chars=900, allow_synthesis=True) or {}
        titles = _as_list(out.get("subsection_titles"))
    except Exception:
        titles = []
    if not titles:
        titles = [
            "Decommissioning & Removal",
            "Delivery & Logistics",
            "Supply & Installation",
            "Testing & Commissioning",
            "Maintenance & Warranty",
        ]
    return titles

def _gen_desc_subsection(vs, title: str, tender_name: str = "", site_name: Optional[str] = None, extra_vss=None):
    queries = [f"{title} scope requirements", f"{title} {tender_name}" if tender_name else title, tender_name or "", site_name or ""]
    prompt = DESC_SUBSECTION_PROMPT_TMPL.format(title=title)
    out = rag_json_plus(vs, prompt, queries, extra_vss=extra_vss, max_ctx=8, min_chars=800, allow_synthesis=True) or {}
    bullets = _as_list(out.get("bullets"))
    if len(bullets) < 5:
        bullets = unique_keep_order(bullets + [
            "Provide method statements and SWMS for all high-risk activities",
            "Coordinate works with other trades and Council representatives",
            "Verify dimensions and services prior to fabrication/installation",
            "Test and commission to manufacturer and AS/NZS requirements",
            "Provide as-built documentation and O&M manuals at completion",
        ])[:10]
    return {"title": title, "bullets": bullets}

def _gen_invoicing(vs, extra_vss=None):
    out = rag_json_plus(vs, DESC_INVOICING_PROMPT, ["invoicing requirements council", "payment terms progress payments"], extra_vss=extra_vss, allow_synthesis=True) or {}
    items = _as_list(out.get("invoicing"))
    if len(items) < 4:
        items = [
            "Invoices must be itemised and reference purchase order and contract number",
            "Standard 30 day payment terms from receipt of valid tax invoice",
            "Milestone/progress claims to align with agreed program and deliverables",
            "Variations require prior written approval by Council",
        ]
    return items

def _gen_reporting(vs, extra_vss=None):
    out = rag_json_plus(vs, DESC_REPORTING_PROMPT, ["reporting weekly final report as-built"], extra_vss=extra_vss, allow_synthesis=True) or {}
    items = _as_list(out.get("reporting"))
    if len(items) < 4:
        items = [
            "Weekly progress report with status, risks, and updated program",
            "Monthly summary including KPI performance and incidents",
            "Final report pack including commissioning results and certificates",
            "Provide as-built drawings, O&M manuals and warranties",
        ]
    return items

def _gen_performance(vs, extra_vss=None):
    out = rag_json_plus(vs, DESC_PERFORMANCE_PROMPT, ["performance monitoring criteria council contract"], extra_vss=extra_vss, allow_synthesis=True) or {}
    note = (out.get("note") or "").strip() or "Performance will be monitored against agreed KPIs and contract requirements."
    criteria = _as_list(out.get("criteria")) or [
        "On-time delivery vs program",
        "Quality of workmanship and defect rate",
        "Compliance with WHS and environmental obligations",
        "Responsiveness to Council requests",
        "Customer/stakeholder satisfaction",
    ]
    return {"note": note, "criteria": criteria}

def _gen_outcomes(vs, extra_vss=None):
    out = rag_json_plus(vs, DESC_OUTCOMES_PROMPT, ["desired outcomes council procurement"], extra_vss=extra_vss, allow_synthesis=True) or {}
    items = _as_list(out.get("desired_outcomes"))
    if len(items) < 7:
        items = [
            "Reliable delivery to program",
            "High quality workmanship and materials",
            "Qualified and competent staff",
            "Effective communication and complaint management",
            "Strong WHS culture with zero harm",
            "Robust contract administration and reporting",
            "Value for money over the whole-of-life",
        ]
    return items

def _gen_purpose_rft(vs, tender_name: Optional[str], extra_vss=None):
    base_q = ["purpose of rft council legislative", "panel or single supplier", tender_name or ""]
    out = rag_json_plus(vs, DESC_PURPOSE_RFT_PROMPT, base_q, extra_vss=extra_vss, allow_synthesis=True) or {}
    items = _as_list(out.get("purpose_rft"))
    if len(items) < 3:
        items = [
            "Set out the requirements, terms and evaluation method for the procurement",
            "Identify either a single supplier or a panel arrangement as permitted by legislation",
            "Achieve best value consistent with Council policies and probity",
        ]
    return items

def generate_section_aim(vs, tender_name: str, term_text: str, site_name: Optional[str] = None, extra_vss=None) -> Dict[str, str]:
    title_hint = tender_name or "this procurement"
    prompt = AIM_SECTION_PROMPT.replace("{PROJECT_TITLE}", title_hint)
    queries = ["tender title or document title", "scope of works", "term defects liability warranty months", tender_name or "", site_name or ""]
    out = rag_json_plus(vs, prompt, queries, extra_vss=extra_vss, max_ctx=8, min_chars=900, allow_synthesis=True) or {}
    intro = _to_str(out.get("intro")).strip()
    body  = _to_str(out.get("body")).strip()
    if not intro:
        intro = f"The Request for Tender (RFT) is for the {title_hint} to Council for the service of the procurement, installation, and integration of the specified works. {term_text or ''}".strip()
    if not body:
        body = (
            "This Tender Evaluation and Probity Plan (TEPP) is the planning and control document in conducting the "
            "evaluation of Tenders received in response to the RFT. The TEPP sets out:\n"
            "• the processes and principles to be followed when evaluating Tenders;\n"
            "• individual’s responsibilities;\n"
            "• the evaluation schedule; and\n"
            "• reporting requirements."
        )
    return {"intro": intro, "body": body}

def generate_sections_1_2(vs, tender_name: str, term_text: str, site_name: Optional[str] = None, extra_vss=None) -> Dict[str, Any]:
    aim = generate_section_aim(vs, tender_name=tender_name, term_text=term_text, site_name=site_name, extra_vss=extra_vss)
    ov = _gen_desc_overview(vs, tender_name, site_name, extra_vss=extra_vss)
    subsection_titles = _gen_subsection_titles(vs, tender_name, site_name, extra_vss=extra_vss)
    technical_reqs = [_gen_desc_subsection(vs, t, tender_name, site_name, extra_vss=extra_vss) for t in subsection_titles]
    invoicing = _gen_invoicing(vs, extra_vss=extra_vss)
    reporting = _gen_reporting(vs, extra_vss=extra_vss)
    perf = _gen_performance(vs, extra_vss=extra_vss)
    outcomes = _gen_outcomes(vs, extra_vss=extra_vss)
    purpose_rft = _gen_purpose_rft(vs, tender_name, extra_vss=extra_vss)

    dor_items: List[str] = []
    dor_items.extend(ov.get("overview", []))
    if ov.get("general"):
        dor_items.append("General:\n" + _join_bullets(ov["general"]))

    tech_items: List[str] = []
    for blk in technical_reqs:
        title = blk["title"]
        bullets = _join_bullets(blk["bullets"])
        tech_items.append(f"{title}:\n{bullets}" if bullets else f"{title}:")

    return {
        "aim": {"intro": aim["intro"], "body": aim["body"]},
        "description_of_requirement": dor_items,
        "technical_requirements": tech_items,
        "invoicing": invoicing,
        "reporting": reporting,
        "performance_monitoring": {"note": perf["note"], "items": perf["criteria"]},
        "desired_outcomes": outcomes,
        "purpose_rft": purpose_rft,
        "summary": ov.get("overview", []),
    }

# =============================================================================
# Commencement date helpers (kept for compatibility)
# =============================================================================

_COMMENCE_EXTRACTION_PROMPT = """
Extract the contract commencement date from the RFT/spec context.
Return STRICT JSON:
{
  "commencement_date_text": string | null,
  "notes": [string, ...]
}
Rules:
- If a single, explicit commencement/start/mobilisation date is present, return it as plain text (e.g., "1 August 2025" or "August 2025").
- If multiple are present, choose the latest explicit commencement/start-of-services date.
- If month+year only, keep that (day may be implied as 1).
- If no clear date, set commencement_date_text to null.
- Add any short clarifying notes (e.g., dependencies/conditions) into notes.
"""

def _fmt_date(d: date) -> str:
    return d.strftime("%d %b %Y")

def _parse_date_any(s: str) -> Optional[date]:
    if not s:
        return None
    s_clean = s.strip()
    fmts = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y", "%d %b %Y", "%d %B %Y", "%b %d %Y", "%B %d %Y", "%b %Y", "%B %Y"]
    for f in fmts:
        try:
            dt = datetime.strptime(s_clean, f)
            return dt.date()
        except Exception:
            pass
    m = re.search(r"(?i)\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b[\s,/-]*([12]\d{3})", s_clean)
    if m:
        for fmt in ("%d %B %Y", "%d %b %Y"):
            try:
                return datetime.strptime(f"1 {m.group(1)} {m.group(2)}", fmt).date()
            except Exception:
                pass
    m2 = re.search(r"\b(20\d{2})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b", s_clean)
    if m2:
        try:
            return date(int(m2.group(1)), int(m2.group(2)), int(m2.group(3)))
        except Exception:
            pass
    return None

def _get_title_date(spec_summary: Any) -> Optional[date]:
    for attr in ["title_date", "issue_date", "published_date", "created_date"]:
        if getattr(spec_summary, attr, None):
            try:
                val = getattr(spec_summary, attr)
                if isinstance(val, date):
                    return val
                if isinstance(val, datetime):
                    return val.date()
                parsed = _parse_date_any(str(val))
                if parsed:
                    return parsed
            except Exception:
                pass
    title_text = (getattr(spec_summary, "title", "") or "").strip()
    parsed = _parse_date_any(title_text)
    if parsed:
        return parsed
    return date.today()

def _gen_commencement_from_spec(vs_spec, extra_vss=None) -> tuple[Optional[str], List[str]]:
    out = rag_json_plus(
        vs_spec,
        _COMMENCE_EXTRACTION_PROMPT,
        ["contract commencement date", "commence services start date", "mobilisation start", "start of services", "program start"],
        extra_vss=extra_vss,
        max_ctx=8,
        allow_synthesis=True,
    ) or {}
    return (out.get("commencement_date_text"), (out.get("notes") or []))

def _apply_commencement_policy(title_dt: Optional[date], extracted_text: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    title_base = title_dt or date.today()
    policy_min = title_base + timedelta(days=26)
    chosen: Optional[date] = None
    if extracted_text:
        parsed = _parse_date_any(extracted_text)
        if parsed:
            chosen = parsed
    policy_note: Optional[str] = None
    if chosen:
        if chosen < policy_min:
            final = policy_min
            policy_note = (
                f"Commencement date in spec ({_fmt_date(chosen)}) is earlier than policy minimum; "
                f"adjusted to {_fmt_date(policy_min)} (≥ title date + 26 days)."
            )
        else:
            final = chosen
    else:
        final = policy_min
        policy_note = (
            f"No explicit commencement date found in spec; set to policy minimum {_fmt_date(policy_min)} "
            f"(≥ title date + 26 days)."
        )
    return (f"Contract Commencement: {_fmt_date(final)}", policy_note)

# =============================================================================
# Title-date parsing helpers (legacy compat)
# =============================================================================

_MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
_ABBR = {m.lower(): i for i, m in enumerate(calendar.month_abbr) if m}
_MONTH_LOOKUP = {**_MONTHS, **_ABBR}

def _try_parse_dt(y: int, m: int, d: int) -> Optional[datetime]:
    try:
        return datetime(y, m, d)
    except Exception:
        return None

def _parse_date_from_text(text: str) -> Optional[datetime]:
    if not text:
        return None
    s = " " + text.strip() + " "
    m = re.search(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\.?\s+(\d{4})\b", s)
    if m:
        d = int(m.group(1)); mon = m.group(2).lower(); y = int(m.group(3))
        mm = _MONTH_LOOKUP.get(mon)
        if mm:
            dt = _try_parse_dt(y, mm, d)
            if dt: return dt
    m = re.search(r"\b([A-Za-z]{3,9})\.?\s+(\d{4})\b", s)
    if m:
        mon = m.group(1).lower(); y = int(m.group(2)); mm = _MONTH_LOOKUP.get(mon)
        if mm:
            dt = _try_parse_dt(y, mm, 1)
            if dt: return dt
    m = re.search(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b", s)
    if m:
        y, mm, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        dt = _try_parse_dt(y, mm, d)
        if dt: return dt
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](20\d{2})\b", s)
    if m:
        d, mm, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        dt = _try_parse_dt(y, mm, d)
        if dt: return dt
    return None

def _fmt_datetime(dt: datetime) -> str:
    return f"{dt.day} {calendar.month_abbr[dt.month]} {dt.year}"

def _get_title_date_legacy(spec_summary: Any) -> Optional[datetime]:
    for attr in ("title_date", "issue_date", "publish_date", "created_at"):
        if hasattr(spec_summary, attr) and getattr(spec_summary, attr):
            val = getattr(spec_summary, attr)
            if isinstance(val, datetime):
                return val
            if isinstance(val, str):
                parsed = _parse_date_from_text(val)
                if parsed:
                    return parsed
    title = getattr(spec_summary, "title", "") or ""
    return _parse_date_from_text(title)

# =============================================================================
# Risk, rationale, weighting helpers
# =============================================================================

def _extract_risk_factors(parsed: Dict[str, Any]) -> Dict[str, Any]:
    risks: Dict[str, Any] = {}
    bmcs = (parsed or {}).get("bmcs", {}) or {}
    equip = (parsed or {}).get("equipment", {}) or {}
    tests = (parsed or {}).get("tests", []) or []
    whs = (parsed or {}).get("whs", []) or []
    warranty_months = (parsed or {}).get("warranty_months")
    risks["integration_risk"] = bool(bmcs.get("integration"))
    risks["num_ec_fans"] = (equip.get("ec_fans", {}) or {}).get("count", 0)
    risks["has_chillers"] = bool(equip.get("chillers"))
    risks["commissioning_complexity"] = len(tests)
    risks["safety_criticality"] = len(whs)
    risks["warranty_months"] = warranty_months or 0
    risks["has_quality_requirements"] = bool((parsed or {}).get("quality", []))
    return risks

def _parse_percent(s: str) -> Optional[float]:
    if not s:
        return None
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*%", str(s))
    return float(m.group(1)) if m else None

def _default_rationale_for(criterion: str, weight: str, parsed: Dict[str, Any]) -> str:
    rf = _extract_risk_factors(parsed)
    bits: List[str] = []
    c = (criterion or "").strip().lower()
    if c.startswith("price"):
        bits.append("Price emphasised to deliver value for money on a high-value construction.")
    if "relevant experience" in c:
        bits.append("Proven experience reduces delivery risk" + (" with BMCS integration." if rf.get("integration_risk") else "."))
    if "capability" in c and "management" not in c:
        msg = "Technical complexity (testing/commissioning)"
        if rf.get("commissioning_complexity", 0) > 0:
            msg += f" with {rf['commissioning_complexity']} test items"
        if rf.get("has_chillers"):
            msg += "; specialist HVAC/chiller scope"
        bits.append(msg + ".")
    if "management" in c or "financial capacity" in c:
        bits.append("Financial stability & governance mitigate schedule and performance risk.")
    if "quality" in c:
        if rf.get("has_quality_requirements"):
            bits.append("Quality controls ensure conformance to specified requirements.")
        else:
            bits.append("Quality controls minimise rework and defects.")
    if "whs" in c or "work health & safety" in c:
        sc = rf.get("safety_criticality", 0)
        bits.append("Safety-critical activities demand strong WHS" + (f" (risk level {sc})." if sc else "."))
    if "sustainability" in c or "eeo" in c:
        bits.append("Council policy ties Sustainability/EEO to 10% of Price.")
    bits.append(f"Final weight used: {weight}.")
    return " ".join(bits).strip()

def _sanitize_llm_rationale(text: str) -> str:
    if not text:
        return ""
    placeholder = "__TENPERCENTPRICE__"
    text = re.sub(r"(?i)\b10%\s+of\s+price\b", placeholder, text)
    text = re.sub(r"(?i)\b\d+(?:\.\d+)?\s*%(\s*weight(?:ing)?s?)?", "", text)
    text = text.replace(placeholder, "10% of Price")
    text = re.sub(r"\s{2,}", " ", text).strip(" .")
    return text

def _compose_sustainability_rationale(final_w: str, price_w_float: Optional[float]) -> str:
    if price_w_float is not None:
        sust_calc = round(price_w_float * 0.10, 1)
        return (
            f"Council policy ties Sustainability/EEO to 10% of the Price weighting. "
            f"Price is {price_w_float:.1f}%, so Sustainability is {sust_calc:.1f}%. "
            f"Final weight used: {final_w}."
        )
    return f"Council policy ties Sustainability/EEO to 10% of the Price weighting. Final weight used: {final_w}."

def _llm_weighting_decider(category: str, ranges: Dict[str, str], risk_factors: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    cat_key = _normalise_category(category)
    if not ranges:
        return None
    constraint_lines = [f"- {crit}: {rg}" for crit, rg in ranges.items()]
    constraints_txt = "\n".join(constraint_lines)
    sust_rule = "If the category includes Sustainability/EEO, set it to exactly 10% of the chosen Price weight."
    risk_txt = json.dumps(risk_factors or {}, ensure_ascii=False)

    messages = [
        SystemMessage(content=(
            "You allocate tender evaluation weightings within strict policy ranges. "
            "You must obey the ranges and explain the risk-driven rationale. "
            "Return STRICT JSON only."
        )),
        HumanMessage(content=f"""Context:
Purchase category: {cat_key}
Allowed ranges (percent of total):
{constraints_txt}

Rule:
{sust_rule}

Risk factors to consider (JSON):
{risk_txt}

Instructions:
- Propose weightings for each criterion listed in the ranges.
- Keep each weight within its stated min-max.
- If Sustainability/EEO applies, set it to 10% of the chosen Price weight.
- Ensure the total of all criteria (including Sustainability if present) sums to ~100 before rounding.
- Provide a brief rationale per criterion.
- Return STRICT JSON:
{{
  "weights": {{"Price (Full Cost)": number, "...": number}},
  "rationales": {{"Price (Full Cost)": "reason", "...": "reason"}}
}}
""")
    ]
    try:
        raw = _llm(json_mode=True).invoke(messages).content
        out = _try_parse_json(raw)
    except Exception:
        try:
            messages.append(HumanMessage(content="Return ONLY the JSON object as specified."))
            raw2 = _llm(json_mode=True).invoke(messages).content
            out = _try_parse_json(raw2)
        except Exception:
            return None

    if not isinstance(out, dict) or "weights" not in out:
        return None
    weights = out.get("weights") or {}
    rationales = out.get("rationales") or {}

    def _parse_range(range_str: str) -> Optional[tuple]:
        if not range_str:
            return None
        m = re.match(r"\s*(\d+(?:\.\d+)?)%?\s*to\s*(\d+(?:\.\d+)?)%?", range_str.lower())
        if m:
            return float(m.group(1)), float(m.group(2))
        m2 = re.match(r"\s*(\d+(?:\.\d+)?)%", range_str.lower())
        if m2:
            v = float(m2.group(1))
            return v, v
        return None

    parsed_ranges: Dict[str, tuple] = {}
    for crit, rg in ranges.items():
        pr = _parse_range(rg)
        if pr:
            parsed_ranges[crit] = pr

    clamped: Dict[str, float] = {}
    for crit, (mn, mx) in parsed_ranges.items():
        v = float(weights.get(crit, (mn + mx) / 2.0))
        v = max(mn, min(mx, v))
        clamped[crit] = v

    sust_key = "Sustainability and EEO & Fair Employment"
    has_sust = sust_key in parsed_ranges
    if has_sust:
        price_v = clamped.get("Price (Full Cost)")
        if price_v is None:
            return None
        clamped[sust_key] = round(price_v * 0.10, 6)

    target_total = 100.0
    locked_keys = ["Price (Full Cost)"] + ([sust_key] if has_sust else [])
    locked_total = sum(clamped[k] for k in clamped if k in locked_keys)
    others = {k: v for k, v in clamped.items() if k not in locked_keys}
    others_sum = sum(others.values())
    remaining = target_total - locked_total
    if remaining < 0 and others_sum > 0:
        return None

    scaled: Dict[str, float] = {}
    if others_sum > 0:
        scale = remaining / others_sum if others_sum else 1.0
        for k, v in others.items():
            scaled[k] = v * scale

    final_weights: Dict[str, float] = {}
    for k in locked_keys:
        if k in clamped:
            final_weights[k] = clamped[k]
    for k, v in scaled.items():
        final_weights[k] = v

    order_pref = [
        "Price (Full Cost)",
        "Relevant Experience",
        "Capability",
        "Management & Financial Capacity",
        "Quality Management",
        "WHS",
        "Sustainability and EEO & Fair Employment",
    ]
    keys = [k for k in order_pref if k in final_weights] + [k for k in final_weights if k not in order_pref]
    rounded = {k: round(final_weights[k], 1) for k in keys}
    diff = round(100.0 - sum(rounded.values()), 1)
    if abs(diff) > 0.0 and keys:
        adjustable = [k for k in keys if k not in ["Price (Full Cost)", sust_key] and rounded[k] > 0]
        target_key = adjustable[-1] if adjustable else keys[-1]
        rounded[target_key] = round(rounded[target_key] + diff, 1)

    return {"weights": rounded, "rationales": rationales}

# =============================================================================
# Deterministic enrichment from parsed spec & policy (hardened)
# =============================================================================

def enrich_tepp_with_spec(tepp_json: Dict[str, Any], spec_summary: Any, parsed: Dict[str, Any]) -> Dict[str, Any]:
    tepp_json.setdefault("evaluation_methodology", {})
    _ensure_list_path(tepp_json, ["evaluation_methodology", "compliance_criteria"])
    _ensure_list_path(tepp_json, ["evaluation_methodology", "required_criteria"])
    _ensure_dict(tepp_json, "pricing")
    _ensure_list_path(tepp_json, ["pricing", "value_for_money"])

    tepp_json.setdefault("probity_and_accountability", {})
    _ensure_list_path(tepp_json, ["probity_and_accountability", "risks"])
    _ensure_list_path(tepp_json, ["evaluation_schedule"])
    tepp_json.setdefault("description", {"summary": []})
    _ensure_list_path(tepp_json, ["description", "summary"])

    whs = parsed.get("whs", [])
    tests = parsed.get("tests", [])
    warranty_months = parsed.get("warranty_months")
    maintenance = parsed.get("maintenance", [])
    bmcs = parsed.get("bmcs", {})
    equip = parsed.get("equipment", {})

    headline_bits = []
    if equip.get("chillers"):
        headline_bits.append("Replacement/upgrade of water-cooled heat pump chillers")
    if equip.get("coils", {}).get("evaporator_count") or equip.get("coils", {}).get("condenser_count"):
        headline_bits.append("AHU coil refurbishments")
    if equip.get("ec_fans", {}).get("count"):
        headline_bits.append(f"{equip['ec_fans']['count']} EC plug fans")
    if bmcs.get("integration"):
        headline_bits.append("BMCS integration (e.g., BACnet HLI)")
    if headline_bits:
        tepp_json["description"]["summary"] = unique_keep_order(
            (tepp_json["description"].get("summary") or []) + ["Scope includes: " + "; ".join(headline_bits)]
        )

    cc_list = []
    for w in whs:
        if isinstance(w, str) and w.strip():
            cc_list.append(w.strip())
    if tests:
        cc_list.append("Provide commissioning plan and evidence of tests per Section 10")
    tepp_json["evaluation_methodology"]["compliance_criteria"] = unique_keep_order(
        (tepp_json["evaluation_methodology"].get("compliance_criteria") or []) + cc_list
    )

    req = tepp_json["evaluation_methodology"]["required_criteria"]

    def _get_req(name_prefix: str, default_weight: float, mandatory: bool=False):
        for r in req:
            if r.get("name","" ).lower().startswith(name_prefix.lower()):
                return r
        r = {"name": name_prefix, "weight": default_weight, "description": "", "mandatory": mandatory}
        req.append(r); return r

    meth = _get_req("Methodology", 12.5)
    qms  = _get_req("Quality", 5.0)
    whs_c = _get_req("Work Health & Safety", 5.0, mandatory=True)

    meth_lines: List[str] = []
    if tests:
        meth_lines.append("Commissioning plan covering: " + "; ".join(tests[:6]) + ("…" if len(tests) > 6 else ""))
    if bmcs.get("integration"):
        proto = ", ".join(bmcs.get("protocols") or []) or "BACnet"
        meth_lines.append(f"BMCS integration/HLI ({proto}) with IO schedules and point lists")
    if warranty_months:
        meth_lines.append(f"Program includes defects liability / warranty of {warranty_months} months")
    if maintenance:
        meth_lines.append("Provision for service/maintenance handover & schedules")
    meth["description"] = "; ".join([s for s in meth_lines if s])

    qms_desc_bits = [(qms.get("description") or ""), "Quality plan incl. ITPs; as-built docs; performance verification"]
    qms["description"] = "; ".join(unique_keep_order([x for x in qms_desc_bits if x]))
    if whs:
        whs_c["mandatory"] = True
        whs_c["description"] = "; ".join(unique_keep_order(whs))

    vfm_list = _ensure_list_path(tepp_json, ["pricing", "value_for_money"])
    if maintenance or warranty_months:
        vfm_list.append("Consider whole-of-life costs incl. maintenance and warranty obligations")
    if equip.get("chillers"):
        vfm_list.append("Energy efficiency and control strategy for chillers/AHUs")
    tepp_json["pricing"]["value_for_money"] = unique_keep_order(vfm_list)

    risks = tepp_json["probity_and_accountability"]["risks"]
    def _risk(issue, consequence, action):
        risks.append({"issue": issue, "consequence": consequence, "action": action})
    if bmcs.get("integration"):
        _risk("BMCS integration failure", "Loss of monitoring/control", "FAT; point-to-point I/O test; SAT with witness")
    if equip.get("ec_fans", {}).get("count"):
        _risk("EC fan performance shortfall", "Insufficient airflow/pressure", "Verify duty; commissioning with TAB report")
    if warranty_months:
        _risk("Warranty service response", "Extended downtime", "Specify response/rectification times & contacts")

    sched = tepp_json["evaluation_schedule"]
    def _sched(task):
        sched.append({"task": task, "responsible": None, "due": None})
    if tests:
        _sched("Review Testing & Commissioning plan and witness tests")
    if maintenance:
        _sched("Review maintenance schedules and O&M handover")
    if bmcs.get("integration"):
        _sched("Review BMCS HLI/point list and integration test records")

    if spec_summary and getattr(spec_summary, "closing_datetime", None):
        tepp_json["critical_dates"] = unique_keep_order(
            (tepp_json.get("critical_dates") or []) + [f"RFT Closing: {spec_summary.closing_datetime}"]
        )
    return tepp_json

# =============================================================================
# Section 6 builders (static narrative + compliance table + rubrics)
# =============================================================================

def _build_section6_methodology_overview() -> str:
    return (
        "The Evaluation Committee, in accordance with the evaluation methodology specified in the RFT and "
        "reproduced in this document, will evaluate all tenders. Compliance is generally taken to mean submission "
        "of the Tender by the closing date, in accordance with all lodgement instructions and provision of all "
        "information requested in the RFT (including any late tender provisions). Compliance criteria are not "
        "scored or weighted; depending on the nature, extent and implications of partial or non-compliance, a "
        "Tender may be disqualified from further evaluation."
    )

def _build_section6_compliance_table() -> Dict[str, Any]:
    return {
        "title": "6.1.1 Compliance Criteria",
        "render_hint": "table",
        "columns": [
            {"key": "criterion", "label": "Compliance Criteria"},
            {"key": "weight", "label": "Weight"},
        ],
        "rows": [
            {"criterion": "Tender Details", "weight": "Nil"},
            {"criterion": "Compliance of RFT Terms & Conditions", "weight": "Nil"},
            {"criterion": "Tenderer’s Statutory Declaration", "weight": "Nil"},
        ],
        "notes": [
            "Compliance criteria are not scored or weighted. Non-compliant tenders may be excluded from further evaluation."
        ],
    }

def _build_section6_nonprice_rating_scale() -> List[Dict[str, Any]]:
    return [
        {"score": 5, "label": "Exceptional", "description": "Fully compliant; no risks or weaknesses."},
        {"score": 4, "label": "Superior", "description": "Sound achievement; minor risks/weaknesses may be acceptable."},
        {"score": 3, "label": "Good", "description": "Reasonable achievement; errors/risks can be corrected with minimal effort."},
        {"score": 2, "label": "Adequate", "description": "Minimal achievement; issues possible to correct/overcome."},
        {"score": 1, "label": "Poor to Deficient", "description": "No/low achievement; numerous errors/risks/weaknesses."},
        {"score": 0, "label": "Unacceptable", "description": "Totally deficient and non-compliant."},
    ]

def _build_section6_returnable_scoring_rubrics() -> Dict[str, Any]:
    return {"note": "See evaluation workbook and schedules for detailed rubrics.", "rubrics": []}

# =============================================================================
# Section 7 builders (Pricing & related)
# =============================================================================

def _build_section7_blocks() -> Dict[str, Any]:
    return {
        "pricing": {
            "model": {
                "narrative": (
                    "Pricing for tender evaluation will be normalised; the lowest fee achieves the maximum score equal "
                    "to the Price criterion weighting. In accordance with State Government scoring, the Total Net Cost "
                    "for tender evaluation is normalised and weighted for comparison as follows."
                ),
                "variables": [
                    "Pc = Total Net Cost calculated for tender evaluation",
                    "Pav = Average of all Total Net Costs",
                    "Ps = Price Score",
                    "Pn = Normalised Price Score",
                    "Pw = Weighted Price Score",
                ],
                "formulae": [
                    "Ps = 200 – (Pc / Pav × 100)",
                    "Pn = Ps / 200",
                    "Pw = Pn × (Price weighting)",
                ],
                "notes": [
                    "The total score each Tenderer receives provides a numeric basis for comparison.",
                    "Recommendation on the preferred Tender will be based on scoring comparisons.",
                    "The basis of any increase will be calculated for the full term of the contract, including optional extensions."
                ],
            },
            "local_preference_policy": {
                "policy_ref": "Procurement Policy P000553.1",
                "blacktown_lga_discount": "5% discount capped at $50,000 for suppliers located in Blacktown City LGA",
                "western_sydney_discount": "2.5% discount capped at $25,000 for suppliers located in Western Sydney councils",
                "definitions": [
                    "Blacktown City Local supplier: principal place of business (not a PO Box) located within Blacktown City LGA.",
                    "Western Sydney Council supplier: principal place of business (not a PO Box) located within a Western Sydney Council LGA."
                ],
                "western_sydney_councils": [
                    "Blue Mountains City Council", "City of Parramatta Council", "Cumberland City Council",
                    "Fairfield City Council", "Hawkesbury City Council", "Liverpool City Council",
                    "Parramatta City Council", "Penrith City Council", "The Hills Shire Council",
                ],
                "application_note": (
                    "For any suppliers eligible for local preference, provide the confirming address in the third tab of the "
                    "tender evaluation spreadsheet."
                ),
            },
            "value_for_money": [
                "‘Value for Money’ is assessed on the combined outcomes of qualitative criteria and price.",
                "Consider quality of proposed services against whole-of-life costs and risk (capacity to deliver on-time and on-budget).",
            ],
        },
        "interviews_presentations": [
            "Final scores may be revised following interviews/presentations conducted with shortlisted Tenderers, "
            "in accordance with Section 6.4 Tenderer Presentations."
        ],
        "shortlisting_alternatives": [
            "Where many tenders are received, clearly non-competitive tenders with no reasonable prospect of best value "
            "may be excluded from detailed evaluation. Reasons for exclusion must be defensible and recorded in the evaluation report."
        ],
        "alternative_tenders": [
            "Alternative tenders will be evaluated in accordance with the RFT evaluation methodology reproduced in this document."
        ],
        "tenderer_presentations": [
            "Tenderers may be invited to interview to clarify their tender. No new or additional information will be requested "
            "or permitted at this stage (see Section 3.8 – Requests for Clarification). Answers must be factual and unbiased; "
            "no personal opinions are to be expressed."
        ],
        "evaluation_report": [
            "On completion of the evaluation, results will be documented in a Council Report including:",
            "• a summary of the evaluation method,",
            "• the number of tenders received,",
            "• the relative ranking of tenders,",
            "• the recommendation of the preferred tender, and",
            "• the rationale used to select the preferred supplier.",
            "The report will highlight key issues for negotiation/ongoing scrutiny, be considered by the Tender Review Committee, "
            "and, if approved, be endorsed by all Committee Members and presented to the Ordinary Council Meeting for adoption. "
            "The ultimate decision maker is Blacktown City Council’s elected officials."
        ],
    }

# =============================================================================
# Sections 8–10 (static narratives)
# =============================================================================

def _build_sections_8_9_10_static() -> Dict[str, str]:
    return {
        "contract_negotiations": (
            "A period of negotiation with the successful Tenderer may arise following completion of the Tender phase "
            "and will commence subject to approval by the Director. This period will result in the executed copies of "
            "the contractual documentation being completed and will necessitate a combination of meetings comprising "
            "formal written obligations to be resolved. The role of the negotiators is to ensure that the negotiation "
            "approach is appropriate to the nature of the project, is open and fair, meets the needs of the Tenderer "
            "and can be accommodated within the Tenderer’s resources. Negotiations must not result in material changes "
            "to the requirements of the Tender. The outcome of the negotiations will be reflected in the final contract "
            "and all negotiation discussions and outcomes will be documented."
        ),
        "debriefing": (
            "The Evaluation Panel may arrange for the debriefing of any unsuccessful Tenderers who request such a "
            "debriefing. The purpose of the debriefing is to provide Tenderers with general comments regarding "
            "evaluation of the Tenderer’s submission against the criteria. If undertaken, the debriefing process will "
            "be conducted by at least two members of the Evaluation Committee and may be carried out by telephone or "
            "letter. The debriefing process will be limited to the unsuccessful Tenderer’s offer. No comparisons will "
            "be made with the successful Tender and the debriefing process will not be used to justify the selection "
            "of the successful Tender. No scoring details will be provided."
        ),
        "contract_management": (
            "The contract will be managed by Manager City Fleet or delegate."
        ),
    }

# =============================================================================
# Section 11 (Critical dates)
# =============================================================================

def _assemble_section11_critical_dates(spec_summary: Any, parsed: Dict[str, Any], vs_spec, extra_vss=None) -> List[str]:
    council_line = parsed.get("council_critical_line")
    if council_line:
        return [str(council_line).strip()]
    title_dt = _get_title_date(spec_summary)
    extracted, notes = _gen_commencement_from_spec(vs_spec, extra_vss=extra_vss)
    final_text, policy_note = _apply_commencement_policy(title_dt, extracted)
    out = [final_text] if final_text else []
    if policy_note:
        out.append(policy_note)
    return out or ["It is essential that the new contract be commenced in a timely manner."]

# =============================================================================
# Final document ordering helpers
# =============================================================================

_SECTION_ORDER = [
    "document_metadata",
    "table_of_contents",
    "aim",
    "description_of_requirement",
    "technical_requirements",
    "invoicing",
    "reporting",
    "performance_monitoring",
    "desired_outcomes",
    "purpose_rft",
    "probity_and_accountability",
    "evaluation_committee",
    "evaluation_schedule",
    "tender_evaluation",
    "pricing",
    "contract_negotiations",
    "debriefing",
    "contract_management",
    "critical_dates",
    "how_to_complete_tepp",
    "returnable_schedules",
    "description",
]

def _reorder_top_level(tepp: Dict[str, Any]) -> Dict[str, Any]:
    ordered = OrderedDict()
    for key in _SECTION_ORDER:
        if key in tepp:
            ordered[key] = tepp[key]
    for k, v in tepp.items():
        if k not in ordered:
            ordered[k] = v
    return dict(ordered)

# =============================================================================
# Main composer
# =============================================================================

def compose_tepp(spec_summary: Any, parsed: Dict[str, Any], vs_spec, extra_vss: Optional[List[Any]]):
    tepp = load_tepp_template()

    # ---------- Title / header ----------
    _ensure_dict(tepp, "document_metadata")
    tepp["document_metadata"]["document_title"] = "Tender Evaluation and Probity Plan"
    tepp["document_metadata"]["tender_number"] = getattr(spec_summary, "tender_no", "") or ""

    # Use the manually-typed project/folder name if provided by the UI (page_upload).
    # Just set parsed["project_name"] = project_name before calling compose_tepp().
    project_name = (parsed or {}).get("project_name") \
                   or getattr(spec_summary, "title", "") \
                   or ""
    print(f"DEBUG: TEPP compose received project_name='{project_name}' (from parsed: '{(parsed or {}).get('project_name')}', from spec_summary.title: '{getattr(spec_summary, 'title', '')}')")
    tepp["document_metadata"]["project_name"] = project_name

    term = parsed.get("term") or "For a term of 12 months."
    tepp["document_metadata"]["term"] = term

    # ---------- 1. Aim ----------
    tender_name = project_name or "this procurement"
    site_name = parsed.get("site_name") or None
    aim_gen = generate_section_aim(vs_spec, tender_name=tender_name, term_text=term, site_name=site_name, extra_vss=extra_vss)
    tepp.setdefault("aim", {})
    tepp["aim"]["intro"] = aim_gen["intro"]
    tepp["aim"]["body"]  = aim_gen["body"]

    # ---------- 2. Description of Requirement ----------
    sec2 = generate_sections_1_2(vs_spec, tender_name=tender_name, term_text=term, site_name=site_name, extra_vss=extra_vss)
    tepp["description_of_requirement"] = unique_keep_order(sec2.get("description_of_requirement", []))
    tepp["technical_requirements"]     = unique_keep_order(sec2.get("technical_requirements", []))
    tepp["invoicing"]                  = unique_keep_order(sec2.get("invoicing", []))
    tepp["reporting"]                  = unique_keep_order(sec2.get("reporting", []))
    tepp["performance_monitoring"]     = {
        "note": (sec2.get("performance_monitoring", {}) or {}).get("note", ""),
        "items": unique_keep_order((sec2.get("performance_monitoring", {}) or {}).get("items", [])),
    }
    tepp["desired_outcomes"] = unique_keep_order(sec2.get("desired_outcomes", []))
    tepp["purpose_rft"]      = unique_keep_order(sec2.get("purpose_rft", []))
    tepp.setdefault("description", {"summary": []})
    if sec2.get("summary"):
        tepp["description"]["summary"] = unique_keep_order(list(sec2["summary"]))

    # ---------- Enrichment ----------
    tepp = enrich_tepp_with_spec(tepp, spec_summary, parsed)

    # ---------- 6. Evaluation weighting ----------
    tepp.setdefault("tender_evaluation", {}).setdefault("evaluation_methodology", {})
    em = tepp["tender_evaluation"]["evaluation_methodology"]
    em["overview"] = _build_section6_methodology_overview()
    em["compliance_criteria_table"] = _build_section6_compliance_table()
    em["non_price_rating_scale"] = _build_section6_nonprice_rating_scale()

    # Always normalise to the base category (no “over $249,999” wording)
    category = _normalise_category(parsed.get("purchase_category") or "construction contract")
    ranges = CATEGORY_WEIGHT_RANGES.get(category, {})
    risk_factors = _extract_risk_factors(parsed)
    table_rows: List[Dict[str, str]] = []
    price_weight_float: Optional[float] = None

    llm_out = _llm_weighting_decider(category, ranges, risk_factors) if ranges else None
    if llm_out and isinstance(llm_out.get("weights"), dict):
        ordered_crits = [
            "Price (Full Cost)",
            "Relevant Experience",
            "Capability",
            "Management & Financial Capacity",
            "Quality Management",
            "WHS",
            "Sustainability and EEO & Fair Employment",
        ]
        weights_map = llm_out["weights"]
        raw_rationales = llm_out.get("rationales", {}) or {}
        crits = [c for c in ordered_crits if c in weights_map] + [c for c in weights_map if c not in ordered_crits]
        for c in crits:
            w = f"{weights_map[c]}%"
            if c == "Price (Full Cost)":
                price_weight_float = _parse_percent(w)
            r = _sanitize_llm_rationale(raw_rationales.get(c, "")) or _default_rationale_for(c, w, parsed)
            if c == "Sustainability and EEO & Fair Employment":
                r = _compose_sustainability_rationale(w, price_weight_float)
            table_rows.append({"criterion": c, "weight": w, "rationale": r})
    else:
        # Deterministic midpoint fallback
        def _parse_range(range_str: str) -> Optional[tuple]:
            if not range_str: return None
            m = re.match(r"\s*(\d+(?:\.\d+)?)%?\s*to\s*(\d+(?:\.\d+)?)%?", range_str.lower())
            if m: return float(m.group(1)), float(m.group(2))
            m2 = re.match(r"\s*(\d+(?:\.\d+)?)%", range_str.lower())
            if m2: return float(m2.group(1)), float(m2.group(1))
            return None

        mids: Dict[str, float] = {}
        for crit, rg in (ranges or {}).items():
            pr = _parse_range(rg)
            if pr:
                mids[crit] = (pr[0]+pr[1])/2.0
        price = mids.get("Price (Full Cost)", 50.0)
        sust_key = "Sustainability and EEO & Fair Employment"
        sust = price * 0.10 if sust_key in (ranges or {}) else 0.0
        others = {k:v for k,v in mids.items() if k!="Price (Full Cost)"}
        if sust>0:
            others[sust_key]=sust
        rem = 100.0 - price - (sust if sust>0 else 0.0)
        other_sum = sum(v for k,v in others.items() if k!=sust_key)
        scaled: Dict[str,float]={}
        if other_sum>0:
            scale = rem/other_sum
            for k,v in others.items():
                if k!=sust_key:
                    scaled[k]=v*scale
            if sust>0:
                scaled[sust_key]=sust
        rounded = {"Price (Full Cost)": round(price,1)}
        for k,v in scaled.items():
            rounded[k]=round(v,1)
        diff = round(100.0 - sum(rounded.values()),1)
        keys = [k for k in rounded if k!="Price (Full Cost)"]
        if keys:
            rounded[keys[-1]] = round(rounded[keys[-1]]+diff,1)
        for c,wv in rounded.items():
            w = f"{wv}%"
            if c=="Price (Full Cost)":
                price_weight_float = _parse_percent(w)
            r = _default_rationale_for(c, w, parsed)
            if c==sust_key:
                r = _compose_sustainability_rationale(w, price_weight_float)
            table_rows.append({"criterion": c, "weight": w, "rationale": r})

    em["required_criteria_table"] = table_rows
    em["required_criteria_caption"] = "Evaluation Criteria (policy-aligned)."

    tepp.pop("weighting_rationales", None)
    tepp["evaluation_criteria"] = []
    tepp.setdefault("meta", {})
    tepp["meta"]["purchase_category_used"] = category
    tepp["meta"]["ranges_used"] = ranges or {}

    # ---------- 6.2 Returnable Schedules Scoring ----------
    tepp.setdefault("tender_evaluation", {})
    tepp["tender_evaluation"]["section_6_2_title"] = "6.2 RETURNABALE SCHEDULES SCORING"  # keep Council typo
    tepp["tender_evaluation"]["returnable_scoring"] = _build_section6_returnable_scoring_rubrics()

    # ---------- 7. Pricing & related ----------
    sec7 = _build_section7_blocks()
    _ensure_dict(tepp, "pricing")
    _ensure_list_path(tepp, ["pricing", "value_for_money"])
    tepp["pricing"]["model"] = sec7["pricing"]["model"]
    tepp["pricing"]["local_preference_policy"] = sec7["pricing"]["local_preference_policy"]
    tepp["pricing"]["value_for_money"] = unique_keep_order(
        (tepp["pricing"].get("value_for_money") or []) + sec7["pricing"]["value_for_money"]
    )
    tepp["interviews_presentations"]   = sec7["interviews_presentations"]
    tepp["shortlisting_alternatives"]  = sec7["shortlisting_alternatives"]
    tepp["alternative_tenders"]        = sec7["alternative_tenders"]
    tepp["tenderer_presentations"]     = sec7["tenderer_presentations"]
    tepp["evaluation_report"]          = sec7["evaluation_report"]

    # ---------- 8–10 ----------
    sec8_10 = _build_sections_8_9_10_static()
    tepp["contract_negotiations"] = sec8_10["contract_negotiations"]
    tepp["debriefing"]            = sec8_10["debriefing"]
    tepp["contract_management"]   = sec8_10["contract_management"]

    # ---------- 11: Critical dates ----------
    tepp["critical_dates"] = _assemble_section11_critical_dates(
        spec_summary=spec_summary,
        parsed=parsed,
        vs_spec=vs_spec,
        extra_vss=extra_vss,
    )

    # ---------- FINAL order ----------
    tepp = _reorder_top_level(tepp)
    return tepp
