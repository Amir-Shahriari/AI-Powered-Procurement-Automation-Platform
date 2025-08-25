# app/services/returnables_filler.py
from __future__ import annotations
from copy import deepcopy
from typing import Any, Dict, List, Optional

def _first(*vals):
    for v in vals:
        if v not in (None, "", [], {}):
            return v
    return None

def _text_list(val) -> List[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    return [str(val).strip()]

def _set_if_empty(obj: Dict[str, Any], path: List[str], value: Any):
    """Set obj[path...] = value only if the current value is 'empty' (None, '', [], {})."""
    cur = obj
    for k in path[:-1]:
        if not isinstance(cur.get(k), dict):
            cur[k] = {}
        cur = cur[k]
    leaf = path[-1]
    existing = cur.get(leaf, None)
    if existing in (None, "", [], {}):
        cur[leaf] = value

def seed_returnables_from_spec(template: Dict[str, Any],
                               spec_summary: Dict[str, Any],
                               parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fills obvious fields in the Returnable Schedules skeleton using:
      - spec_summary: output of the SPEC_SUMMARY_PROMPT (title, tender_no, contract_no, closing_datetime, contact, scope, location, safety_standards)
      - parsed: deterministic parse_spec(text) dict (whatever you expose there)
    Only fills empty fields. Never overwrites existing non-empty values in the template.
    """
    out = deepcopy(template)

    title = _first(spec_summary.get("title"),
                   spec_summary.get("tender_title"))
    tender_no   = spec_summary.get("tender_no")
    contract_no = spec_summary.get("contract_no")
    closing     = spec_summary.get("closing_datetime")
    contact     = spec_summary.get("contact") or {}
    scope_list  = _text_list(spec_summary.get("scope"))
    location    = spec_summary.get("location")
    safety      = _text_list(spec_summary.get("safety_standards"))

    # Top-level meta/header (your skeleton uses "meta" — adjust to match your file)
    # If your skeleton uses "header" instead, change the paths accordingly.
    # meta
    _set_if_empty(out, ["meta", "rft_title"],       title or "")
    _set_if_empty(out, ["meta", "contract_no"],     contract_no or "")
    _set_if_empty(out, ["meta", "created_at"],      "")
    _set_if_empty(out, ["meta", "prepared_by"],     "")

    # Optional helpful prefill into Schedule 9 (service delivery / capability summary)
    if scope_list:
        _set_if_empty(out, ["schedule_9_service_delivery_performance", "capability_summary", "methodology_and_procedures"],
                      " ; ".join(scope_list))
    if location:
        _set_if_empty(out, ["schedule_9_service_delivery_performance", "capability_summary", "principal_address"], location)
    if safety:
        # append to 'accreditations' if empty
        path = ["schedule_9_service_delivery_performance", "capability_summary", "accreditations"]
        cur = out
        for k in path[:-1]:
            cur = cur.setdefault(k, {})
        leaf = path[-1]
        if not isinstance(cur.get(leaf), list) or not cur.get(leaf):
            cur[leaf] = safety

    # Closing date is sometimes useful in Schedule 10 validity
    if closing:
        _set_if_empty(out, ["schedule_10_fee_structure", "validity_period_days"], "")

    # Contact (dump in schedule 1 contact_details if empty)
    if contact:
        _set_if_empty(out, ["schedule_1_corporate_information_and_declaration", "contact_details", "name"],    contact.get("name") or "")
        _set_if_empty(out, ["schedule_1_corporate_information_and_declaration", "contact_details", "phone"],   contact.get("phone") or "")
        _set_if_empty(out, ["schedule_1_corporate_information_and_declaration", "contact_details", "email"],   contact.get("email") or "")

    # Use parsed (if available) to prefill small bits
    # e.g., parsed.get("equipment") => might seed "schedule_of_performance_heat_pump_chillers"
    equip = parsed.get("equipment") if isinstance(parsed, dict) else None
    if isinstance(equip, dict):
        hpc = equip.get("heat_pump_chillers") or {}
        qty = hpc.get("quantity")
        if qty:
            _set_if_empty(out, ["schedule_10_fee_structure", "schedule_of_performance_heat_pump_chillers", "spec", "quantity"], str(qty))

    return out
