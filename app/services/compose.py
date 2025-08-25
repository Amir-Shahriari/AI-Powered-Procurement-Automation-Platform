# app/services/compose.py
import re
import json
from typing import Any, Dict, List, Optional

from langchain.schema import SystemMessage, HumanMessage

# -----------------------------------------------------------------------------
# Evaluation criteria ranges per purchase category.  These are derived from
# council tender guidance and define the allowed range for each criterion.  The
# ranges are expressed as strings with percentage bounds (min% to max%).
# Sustainability / EEO & Fair Employment (or Social & Community) weight is
# specified as 10% of the chosen price weight and will be calculated
# accordingly.
CATEGORY_WEIGHT_RANGES: Dict[str, Dict[str, str]] = {
    "standard product or good": {
        "Price (Full Cost)": "40% to 60%",
        "Relevant Experience": "10% to 30%",
        "Capability": "10% to 30%",
        "Management & Financial Capacity": "5% to 10%",
        "WHS": "5% to 10%",
        # Sustainability/EEO is handled separately as 10% of price
    },
    "construction contract valued at over $249,999": {
        "Price (Full Cost)": "35% to 60%",
        "Relevant Experience": "10% to 20%",
        "Capability": "10% to 20%",
        "Management & Financial Capacity": "5% to 15%",
        "Quality Management": "5% to 10%",
        "WHS": "5% to 10%",
        # Sustainability/EEO is 10% of price
    },
    "consultancy contract valued at over $249,999": {
        "Price (Full Cost)": "25% to 50%",
        "Relevant Experience": "10% to 30%",
        "Capability": "10% to 30%",
        "Management & Financial Capacity": "5% to 10%",
        "WHS": "5% to 10%",
        # Sustainability/EEO or Social & Community is 10% of price
    },
    "service delivery contract valued at over $249,999": {
        "Price (Full Cost)": "30% to 50%",
        "Relevant Experience": "10% to 30%",
        "Capability": "10% to 30%",
        "Management & Financial Capacity": "5% to 10%",
        "Quality Management": "5% to 10%",
        "WHS": "5% to 10%",
        # Sustainability/EEO & Social & Community is 10% of price
    },
    "management contract valued at over $249,999": {
        "Price (Full Cost)": "30% to 50%",
        "Relevant Experience": "10% to 30%",
        "Capability": "10% to 30%",
        "Management & Financial Capacity": "5% to 15%",
        "Quality Management": "5% to 10%",
        "WHS": "0% to 10%",
        # No explicit Sustainability/EEO weighting given; local preference handled separately
    },
    "lease / license valued at over $249,999": {
        "Price (Full Cost)": "30% to 50%",
        "Relevant Experience": "10% to 30%",
        "Capability": "10% to 30%",
        "Management & Financial Capacity": "5% to 15%",
        "Quality Management": "5% to 10%",
        "WHS": "0% to 10%",
        # Sustainability/EEO not specified separately
    },
}

def _parse_range(range_str: str) -> Optional[tuple]:
    """Parse a range like '10% to 30%' into a (min,max) tuple of floats."""
    if not range_str:
        return None
    m = re.match(r"\s*(\d+(?:\.\d+)?)%?\s*to\s*(\d+(?:\.\d+)?)%?", range_str.lower())
    if m:
        return float(m.group(1)), float(m.group(2))
    # handle single value or '0%'
    m2 = re.match(r"\s*(\d+(?:\.\d+)?)%", range_str.lower())
    if m2:
        v = float(m2.group(1))
        return v, v
    return None

def _calculate_dynamic_evaluation_weights(category: str) -> Optional[List[Dict[str, Any]]]:
    """
    Midpoint-based deterministic weighting (fallback).
    """
    cat_key = category.strip().lower()
    ranges = CATEGORY_WEIGHT_RANGES.get(cat_key)
    if not ranges:
        return None
    # Determine base midpoints for price and each criterion
    midpoints: Dict[str, float] = {}
    for crit, rg in ranges.items():
        pr = _parse_range(rg)
        if pr:
            midpoints[crit] = (pr[0] + pr[1]) / 2.0
    # Extract and remove price for separate handling
    price_weight = midpoints.pop("Price (Full Cost)", None)
    if price_weight is None:
        return None
    # Sustainability/EEO weight: 10% of price weight if category has such rule
    sustainability_weight = 0.0
    if cat_key in [
        "standard product or good",
        "construction contract valued at over $249,999",
        "consultancy contract valued at over $249,999",
        "service delivery contract valued at over $249,999",
    ]:
        sustainability_weight = price_weight * 0.10
        midpoints["Sustainability and EEO & Fair Employment"] = sustainability_weight
    # Sum midpoints of remaining criteria (except price and sustainability)
    other_total = sum(midpoints.values())
    remaining = 100.0 - price_weight - sustainability_weight
    if remaining <= 0 or other_total <= 0:
        return None
    scale = remaining / other_total
    final_weights: Dict[str, float] = {}
    for crit, mid in midpoints.items():
        if crit == "Sustainability and EEO & Fair Employment":
            final_weights[crit] = sustainability_weight
        else:
            final_weights[crit] = mid * scale
    final_weights["Price (Full Cost)"] = price_weight
    ordered_crits = [
        "Price (Full Cost)",
        "Relevant Experience",
        "Capability",
        "Management & Financial Capacity",
        "Quality Management",
        "WHS",
        "Sustainability and EEO & Fair Employment",
    ]
    crits = [c for c in ordered_crits if c in final_weights]
    weights = [final_weights[c] for c in crits]
    rounded = [round(w, 1) for w in weights]
    total = sum(rounded)
    diff = round(100.0 - total, 1)
    if rounded:
        rounded[-1] += diff
    result = []
    for i, crit in enumerate(crits):
        wt = f"{rounded[i]}%"
        result.append({"criterion": crit, "weighting": wt, "subcriteria": []})
    return result

# We reuse your LLM wrapper's rag_json; this file provides rag_json_plus for multi-VS
from ..services.llm import rag_json, _llm  # _llm is your ChatOllama/ChatOpenAI selector

# -------------------- LLM prompts (kept for potential future use) --------------------
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

TEPP_PROMPT = """You are generating a Tender Evaluation & Probity Plan (TEPP) that mirrors Council’s template and methodology.
Use ONLY the provided context from: (a) the technical specification, (b) the Council TEPP template, (c) the evaluation manual.
Populate policy-driven sections from template/manual; populate technical details (WHS/tests/warranty/scope) from the spec.
If unknown, leave null or [] (do NOT invent). Return STRICT JSON with the following shape:

{
  "header": { "project_title": null|string, "tender_no": null|string, "panel_roles": [string,...] },

  "aim": [string,...],

  "description": {
    "summary": [string,...],
    "desired_outcomes": [string,...],
    "purpose_rft": [string,...]
  },

  "probity_and_accountability": {
    "authorised_contact_officer": {"name": null|string, "title": null|string, "email": null|string, "phone": null|string},
    "receipt_of_tenders": [string,...],
    "late_tenders": [string,...],
    "clarifications": [string,...],
    "risks": [{"issue": string, "consequence": string, "action": string}, ...]
  },

  "evaluation_committee": [{"name": null|string, "title": null|string, "branch": null|string, "role": null|string}, ...],

  "evaluation_schedule": [{"task": string, "responsible": string|null, "due": string|null}, ...],

  "evaluation_methodology": {
    "compliance_criteria": [string,...],
    "required_criteria": [
      {"name": "Pricing (Total Cost & Life-Cycle Costs)", "weight": 50, "description": "", "mandatory": false},
      {"name": "Relevant Experience", "weight": 12.5, "description": "", "mandatory": false},
      {"name": "Capability", "weight": 12.5, "description": "", "mandatory": false},
      {"name": "Management Skills, Qualifications & Financial Capacity", "weight": 10, "description": "", "mandatory": false},
      {"name": "Sustainability and EEO & Fair Employment", "weight": 5, "description": "", "mandatory": false},
      {"name": "Quality Management", "weight": 5, "description": "Quality plan incl. ITPs; as-built docs; performance verification", "mandatory": false},
      {"name": "Work Health & Safety (WHS)", "weight": 5, "description": "", "mandatory": true}
    ],
    "rating_scale": [string,...]
  },

  "returnable_scoring": {
    "relevant_experience": {"levels":[{"level":"Exceptional","requirement":"20–15 years’ experience","score":5},{"level":"Superior","requirement":"15–10 years’ experience","score":4},{"level":"Good","requirement":"10–5 years’ experience","score":3},{"level":"Adequate","requirement":"5–3 years’ experience","score":2},{"level":"Poor to deficient","requirement":"3–1 years’ experience","score":1},{"level":"Unacceptable","requirement":"No experience","score":0}]},
    "capability": {"levels":[{"level":"Outstanding","requirement":"program, resources, and past performance present no risk","score":5},{"level":"Strong","requirement":"minor risks, strong methodology","score":4},{"level":"Sound","requirement":"adequate methodology/resources","score":3},{"level":"Limited","requirement":"gaps/risks in program/resources","score":2},{"level":"Deficient","requirement":"major gaps or risks","score":1}]},
    "quality": {"levels":[{"level":"Comprehensive QMS incl. ITPs","score":5},{"level":"Sound QMS","score":4},{"level":"Basic QMS","score":3},{"level":"Ad-hoc QMS","score":2},{"level":"No QMS evidence","score":1}]},
    "whs": {"levels":[{"level":"Certified WHS, comprehensive plans & PPE; zero incidents","score":5},{"level":"Strong WHS evidence","score":4},{"level":"Adequate WHS","score":3},{"level":"Gaps in WHS","score":2},{"level":"Non-compliant","requirement":"","score":1}]}
  },

  "pricing": {
    "model": {
      "variables": ["Pc (Total Net Cost)","Pav (Average of Total Net Costs)","Ps (Price Score)","Pn (Normalised Price Score)","Pw (Weighted Price Score)"],
      "formulae": ["Ps = 200 – (Pc / Pav × 100)", "Pn = Ps / 200", "Pw = Pn × 50"]
    },
    "local_preference_policy": {
      "blacktown_lga_discount": "5% capped at $50,000",
      "western_sydney_discount": "2.5% capped at $25,000",
      "notes": [string,...]
    },
    "value_for_money": [string,...]
  },

  "interviews_presentations": [string,...],
  "shortlisting_alternatives": [string,...],
  "evaluation_report": [string,...],
  "contract_negotiations": [string,...],
  "debriefing": [string,...],
  "contract_management": [string,...],
  "critical_dates": [string,...],

  "evaluation_criteria": [],
  "probity": {},
  "milestones": []
}
"""

# -------------------- Helpers --------------------
def _try_parse_json(response: str) -> Any:
    s = response.strip()
    if s.startswith("```"):
        s = re.sub(r"^```json|^```", "", s).strip()
        s = re.sub(r"```$", "", s).strip()
    try:
        return json.loads(s)
    except Exception:
        m = re.search(r"\{[\s\S]*\}$", response.strip())
        if not m:
            raise
        return json.loads(m.group(0))

def _similar(vs, query: str, k: int = 6) -> List[str]:
    try:
        docs = vs.similarity_search(query, k=k)
        return [d.page_content for d in docs]
    except Exception:
        return []

def _unique_keep_order(items: List[str]) -> List[str]:
    seen = set(); out = []
    for it in items or []:
        key = re.sub(r"\s+", " ", (it or "").strip().lower())
        if key and key not in seen:
            seen.add(key); out.append((it or "").strip())
    return out

# -------------------- Multi-VS RAG (policy + spec) --------------------
def rag_json_plus(vs_primary, prompt: str, field_queries: List[str],
                  extra_vss: Optional[List[Any]] = None, max_ctx: int = 6) -> Any:
    ctx_blocks = []
    for q in field_queries:
        snips = []
        snips += _similar(vs_primary, q, k=max_ctx)
        if extra_vss:
            for evs in extra_vss:
                try:
                    snips += _similar(evs, q, k=max(2, max_ctx // 2))
                except Exception:
                    pass
        if snips:
            ctx_blocks.append(f"[{q}]\n" + "\n---\n".join(snips))
    context = "\n\n".join(ctx_blocks) if ctx_blocks else "NO_CONTEXT"

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"Context:\n{context}\n\nReturn ONLY the JSON object.")
    ]
    resp = _llm(json_mode=True).invoke(messages).content
    try:
        return _try_parse_json(resp)
    except Exception:
        repair = messages + [HumanMessage(content="Respond again as STRICT JSON only. No prose.")]
        resp2 = _llm(json_mode=True).invoke(repair).content
        return _try_parse_json(resp2)

# -------------------- NEW: simple risk extraction for the prompt -------------
def _extract_risk_factors(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Heuristic risk hints the LLM can use:
      - complexity, timeline pressure, integration risk, safety criticality,
        warranty/maintenance burden, performance variability, etc.
    """
    risks: Dict[str, Any] = {}
    bmcs = (parsed or {}).get("bmcs", {}) or {}
    equip = (parsed or {}).get("equipment", {}) or {}
    tests = (parsed or {}).get("tests", []) or []
    whs = (parsed or {}).get("whs", []) or []
    warranty_months = (parsed or {}).get("warranty_months")

    risks["integration_risk"] = bool(bmcs.get("integration"))
    risks["num_ec_fans"] = (equip.get("ec_fans", {}) or {}).get("count", 0)
    risks["has_chillers"] = bool(equip.get("chillers"))
    risks["commissioning_complexity"] = len(tests)          # more tests ⇒ higher complexity
    risks["safety_criticality"] = len(whs)                  # more WHS clauses ⇒ higher WHS risk
    risks["warranty_months"] = warranty_months or 0
    risks["has_quality_requirements"] = bool((parsed or {}).get("quality", []))

    return risks

# -------------------- NEW: LLM-driven weighting decider within bounds --------
def _llm_weighting_decider(category: str,
                           ranges: Dict[str, str],
                           risk_factors: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Ask the LLM to propose criterion weights *within the provided ranges*
    based on risk factors. Then validate, clamp, and normalise to 100,
    preserving Sustainability = 10% of Price (for applicable categories).

    Returns:
      {"weights": {"criterion": float, ...}, "rationales": {"criterion": str, ...}}
      or None on failure.
    """
    cat_key = (category or "").strip().lower()
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
Purchase category: {category}
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

    # Parse bounds
    parsed_ranges: Dict[str, tuple] = {}
    for crit, rg in ranges.items():
        pr = _parse_range(rg)
        if pr:
            parsed_ranges[crit] = pr

    # Clamp to min/max; default to midpoint if missing
    clamped: Dict[str, float] = {}
    for crit, (mn, mx) in parsed_ranges.items():
        v = float(weights.get(crit, (mn + mx) / 2.0))
        v = max(mn, min(mx, v))
        clamped[crit] = v

    # Sustainability = 10% of Price if applicable
    has_sust = cat_key in [
        "standard product or good",
        "construction contract valued at over $249,999",
        "consultancy contract valued at over $249,999",
        "service delivery contract valued at over $249,999",
    ]
    sust_key = "Sustainability and EEO & Fair Employment"
    if has_sust:
        price_v = clamped.get("Price (Full Cost)")
        if price_v is None:
            return None
        clamped[sust_key] = round(price_v * 0.10, 6)

    # Normalise to 100 while preserving Price (+ Sustainability linkage if present)
    target_total = 100.0
    locked_keys = ["Price (Full Cost)"] + ([sust_key] if has_sust else [])
    locked_total = sum(clamped[k] for k in locked_keys if k in clamped)

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

    # Round to 1 decimal and force exact 100 by adjusting a non-price criterion
    order_pref = [
        "Price (Full Cost)",
        "Relevant Experience",
        "Capability",
        "Management & Financial Capacity",
        "Quality Management",
        "WHS",
        sust_key,
    ]
    keys = [k for k in order_pref if k in final_weights] + [k for k in final_weights if k not in order_pref]
    rounded = {k: round(final_weights[k], 1) for k in keys}
    diff = round(100.0 - sum(rounded.values()), 1)
    if abs(diff) > 0.0 and keys:
        adjustable = [k for k in keys if k not in ["Price (Full Cost)", sust_key] and rounded[k] > 0]
        target_key = adjustable[-1] if adjustable else keys[-1]
        rounded[target_key] = round(rounded[target_key] + diff, 1)

    return {"weights": rounded, "rationales": rationales}

# -------------------- TEPP enrichment --------------------
def enrich_tepp_with_spec(tepp_json: Dict[str, Any],
                          spec_summary: Any,
                          parsed: Dict[str, Any]) -> Dict[str, Any]:
    tepp_json.setdefault("evaluation_methodology", {})
    tepp_json["evaluation_methodology"].setdefault("compliance_criteria", [])
    tepp_json["evaluation_methodology"].setdefault("required_criteria", [])
    tepp_json.setdefault("pricing", {})

    # ---- FIX: coerce pricing.value_for_money to a list ----
    if "value_for_money" not in tepp_json["pricing"]:
        tepp_json["pricing"]["value_for_money"] = []
    else:
        vfm_seed = tepp_json["pricing"]["value_for_money"]
        if isinstance(vfm_seed, str):
            tepp_json["pricing"]["value_for_money"] = [vfm_seed]
        elif vfm_seed is None:
            tepp_json["pricing"]["value_for_money"] = []

    tepp_json.setdefault("probity_and_accountability", {})
    tepp_json["probity_and_accountability"].setdefault("risks", [])
    tepp_json.setdefault("evaluation_schedule", [])
    tepp_json.setdefault("critical_dates", [])
    tepp_json.setdefault("description", {"summary": [], "desired_outcomes": [], "purpose_rft": []})

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
        tepp_json["description"]["summary"] = _unique_keep_order(
            (tepp_json["description"].get("summary") or []) + ["Scope includes: " + "; ".join(headline_bits)]
        )

    # Compliance criteria
    for w in whs:
        if w:
            tepp_json["evaluation_methodology"]["compliance_criteria"].append(w)
    if tests:
        tepp_json["evaluation_methodology"]["compliance_criteria"].append(
            "Provide commissioning plan and evidence of tests per Section 10"
        )
    tepp_json["evaluation_methodology"]["compliance_criteria"] = _unique_keep_order(
        tepp_json["evaluation_methodology"]["compliance_criteria"]
    )

    # Required criteria enrichments
    req = tepp_json["evaluation_methodology"]["required_criteria"]

    def _get_req(name_prefix: str, default_weight: float, mandatory: bool=False):
        for r in req:
            if r.get("name","").lower().startswith(name_prefix.lower()):
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
        proto = ", ".join(bmcs.get("protocols") or [])
        meth_lines.append(f"BMCS integration/HLI ({proto}) with IO schedules and point lists")
    if warranty_months:
        meth_lines.append(f"Program includes defects liability / warranty of {warranty_months} months")
    if maintenance:
        meth_lines.append("Provision for service/maintenance handover & schedules")
    meth["description"] = "; ".join([s for s in meth_lines if s])

    qms_desc_bits = [(qms.get("description") or ""), "Quality plan incl. ITPs; as-built docs; performance verification"]
    qms["description"] = "; ".join(_unique_keep_order([x for x in qms_desc_bits if x]))

    if whs:
        whs_c["mandatory"] = True
        whs_c["description"] = "; ".join(_unique_keep_order(whs))

    # ---- With value_for_money safely a list, we can append policy notes ----
    if maintenance or warranty_months:
        tepp_json["pricing"]["value_for_money"].append(
            "Consider whole-of-life costs incl. maintenance and warranty obligations"
        )
    if equip.get("chillers"):
        tepp_json["pricing"]["value_for_money"].append(
            "Energy efficiency and control strategy for chillers/AHUs"
        )
    tepp_json["pricing"]["value_for_money"] = _unique_keep_order(tepp_json["pricing"]["value_for_money"])

    # Risks
    risks = tepp_json["probity_and_accountability"]["risks"]
    def _risk(issue, consequence, action):
        risks.append({"issue": issue, "consequence": consequence, "action": action})
    if bmcs.get("integration"):
        _risk("BMCS integration failure", "Loss of monitoring/control", "FAT; point-to-point I/O test; SAT with witness")
    if equip.get("ec_fans", {}).get("count"):
        _risk("EC fan performance shortfall", "Insufficient airflow/pressure", "Verify duty; commissioning with TAB report")
    if warranty_months:
        _risk("Warranty service response", "Extended downtime", "Specify response/rectification times & contacts")

    # Evaluation schedule
    sched = tepp_json["evaluation_schedule"]
    def _sched(task):
        sched.append({"task": task, "responsible": None, "due": None})
    if tests:
        _sched("Review Testing & Commissioning plan and witness tests")
    if maintenance:
        _sched("Review maintenance schedules and O&M handover")
    if bmcs.get("integration"):
        _sched("Review BMCS HLI/point list and integration test records")

    # Critical date seed
    if spec_summary and getattr(spec_summary, "closing_datetime", None):
        tepp_json["critical_dates"] = _unique_keep_order(
            (tepp_json.get("critical_dates") or []) + [f"RFT Closing: {spec_summary.closing_datetime}"]
        )

    return tepp_json

# -------------------- Public composers --------------------
def compose_rft(spec_summary: Any, parsed: Dict[str, Any]) -> Any:
    """Return an RFTDoc-compatible dict with header + sections (no Section model)."""
    overview = []
    if getattr(spec_summary, "title", None):
        overview.append(spec_summary.title)
    if getattr(spec_summary, "location", None):
        overview.append(f"Location: {spec_summary.location}")

    if parsed.get("equipment", {}).get("chillers"):
        overview.append("Includes new/replacement heat pump chillers and AHU refurbishments")

    tech_items: List[str] = []
    eq = parsed.get("equipment", {})
    if eq.get("chillers"):
        for ch in eq["chillers"]:
            mm = ch.get("make_model") or "Water-cooled heat pump chiller"
            cap = f"{int(ch['heating_capacity_kw'])} kW" if ch.get("heating_capacity_kw") else ""
            cnt = f"x{ch.get('count')}" if ch.get("count") else ""
            tech_items.append(f"Supply & install {cnt} {mm} {cap}".strip())
    coils = eq.get("coils", {})
    if coils.get("evaporator_count"): tech_items.append(f"{coils['evaporator_count']} new evaporator coils")
    if coils.get("condenser_count"):  tech_items.append(f"{coils['condenser_count']} condenser coils")
    if coils.get("heat_recovery_sets"): tech_items.append(f"{coils['heat_recovery_sets']} sets of run-around heat recovery coils")

    resp_req = [
        "Complete all Returnable Schedules in the provided JSON template",
        "Provide product data/catalogues & technical sheets for all proposed equipment",
        "Provide draft layout and connection diagrams",
        "Provide methodology/program and risk controls",
        "Provide warranty terms and service schedules",
    ]

    submission = []
    if getattr(spec_summary, "closing_datetime", None):
        submission.append(f"Closing date and time: {spec_summary.closing_datetime}")

    header = {
        "tender_title": getattr(spec_summary, "title", None),
        "tender_no": getattr(spec_summary, "tender_no", None),
        "contract_no": getattr(spec_summary, "contract_no", None),
        "closing_datetime": getattr(spec_summary, "closing_datetime", None),
        "contact": (getattr(spec_summary, "contact", None) or {"name": None, "email": None, "phone": None}),
        "lodgement_instructions": None,
    }

    sections = [
        {"title": "Overview", "items": _unique_keep_order(overview)},
        {"title": "Technical Scope Summary", "items": _unique_keep_order(tech_items)[:80]},
        {"title": "Response Requirements", "items": resp_req},
        {"title": "Submission & Closing", "items": submission},
    ]
    return {"header": header, "sections": sections}

def compose_tepp(spec_summary: Any, parsed: Dict[str, Any], vs_spec, extra_vss: Optional[List[Any]]):
    """
    Council-style TEPP composer that populates a static TEPP skeleton with
    spec- and policy-derived content. It also computes the evaluation weighting
    (LLM within Council ranges, with fallbacks) and injects it into the TEPP.
    """
    from .templates import load_tepp_template

    tepp = load_tepp_template()

    # ---------- Title page / header ----------
    tepp["document_metadata"]["document_title"] = "Tender Evaluation and Probity Plan"
    tepp["document_metadata"]["tender_number"] = getattr(spec_summary, "tender_no", "") or ""
    tepp["document_metadata"]["project_name"]  = getattr(spec_summary, "title", "") or ""
    term = parsed.get("term") or "For a term of 12 months."
    tepp["document_metadata"]["term"] = term

    # ---------- 1. Aim ----------
    brief = tepp["document_metadata"]["project_name"] or "this procurement"
    tepp["aim"]["intro"] = (
        f"The Request for Tender (RFT) is for the {brief} to Council for the service of the procurement, "
        "installation, and integration of the specified works."
    )

    # ---------- 2. Description of Requirement ----------
    tepp = enrich_tepp_with_spec(tepp, spec_summary, parsed)

    # ---------- 6. Evaluation weighting (LLM + fallbacks) ----------
    tepp.setdefault("evaluation_criteria", [])
    tepp.setdefault("tender_evaluation", {}).setdefault("evaluation_methodology", {})
    em = tepp["tender_evaluation"]["evaluation_methodology"]

    # If caller didn't provide final weights, compute them now:
    if not parsed.get("final_weights"):
        category = (parsed.get("purchase_category") or "construction contract valued at over $249,999").strip().lower()
        ranges = CATEGORY_WEIGHT_RANGES.get(category)
        risk_factors = _extract_risk_factors(parsed)

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
            crits = [c for c in ordered_crits if c in weights_map] + [c for c in weights_map if c not in ordered_crits]
            tepp["evaluation_criteria"] = [
                {"criterion": c, "weighting": f"{weights_map[c]}%", "subcriteria": []}
                for c in crits
            ]
            em["weighting_rationales"] = llm_out.get("rationales", {})
        else:
            dyn = _calculate_dynamic_evaluation_weights(category or "")
            tepp["evaluation_criteria"] = dyn if dyn else [
                {"criterion": "Price (Full Cost)", "weighting": "50%", "subcriteria": []},
                {"criterion": "Relevant Experience", "weighting": "12.5%", "subcriteria": []},
                {"criterion": "Capability", "weighting": "12.5%", "subcriteria": []},
                {"criterion": "Management & Financial Capacity", "weighting": "10%", "subcriteria": []},
                {"criterion": "Quality Management", "weighting": "5%", "subcriteria": []},
                {"criterion": "WHS", "weighting": "5%", "subcriteria": []},
                {"criterion": "Sustainability and EEO & Fair Employment", "weighting": "5%", "subcriteria": []},
            ]

        # Expose to parsed for downstream consumers
        parsed["final_weights"] = [
            {"criterion": item["criterion"], "weighting": item["weighting"]}
            for item in tepp.get("evaluation_criteria", [])
        ]

    # Populate the Council table 6.1.2 (required_criteria_table) from final_weights
    required_table = []
    for row in parsed.get("final_weights", []):
        required_table.append({"criterion": row.get("criterion", ""), "weight": row.get("weighting", "")})
    em["required_criteria_table"] = required_table

    # ---------- 11. Critical dates ----------
    tepp["critical_dates"] = _unique_keep_order(
        (tepp.get("critical_dates") or [])
        + ([f"RFT Closing: {getattr(spec_summary,'closing_datetime','')}"] if getattr(spec_summary,'closing_datetime',None) else [])
        + (parsed.get("critical_dates") or [])
    )

    return tepp
