# app/services/compose/rft.py
from __future__ import annotations

from typing import Any, Dict, List
from app.services.base import unique_keep_order

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
    if coils.get("evaporator_count"):
        tech_items.append(f"{coils['evaporator_count']} new evaporator coils")
    if coils.get("condenser_count"):
        tech_items.append(f"{coils['condenser_count']} condenser coils")
    if coils.get("heat_recovery_sets"):
        tech_items.append(f"{coils['heat_recovery_sets']} sets of run-around heat recovery coils")

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
        {"title": "Overview", "items": unique_keep_order(overview)},
        {"title": "Technical Scope Summary", "items": unique_keep_order(tech_items)[:80]},
        {"title": "Response Requirements", "items": resp_req},
        {"title": "Submission & Closing", "items": submission},
    ]
    return {"header": header, "sections": sections}
