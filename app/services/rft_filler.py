# app/services/rft_filler.py
from __future__ import annotations
from copy import deepcopy
from typing import Any, Dict, List

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
    cur = obj
    for k in path[:-1]:
        if not isinstance(cur.get(k), dict):
            cur[k] = {}
        cur = cur[k]
    leaf = path[-1]
    existing = cur.get(leaf, None)
    if existing in (None, "", [], {}):
        cur[leaf] = value

def seed_rft_from_spec(template: Dict[str, Any],
                       spec_summary: Dict[str, Any],
                       parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fill RFT skeleton header and a couple obvious spots from spec_summary/parsed.
    Only fills empty fields.
    """
    out = deepcopy(template)

    title       = _first(spec_summary.get("title"), spec_summary.get("tender_title"))
    tender_no   = spec_summary.get("tender_no")
    contract_no = spec_summary.get("contract_no")
    closing     = spec_summary.get("closing_datetime")
    contact     = spec_summary.get("contact") or {}
    scope_list  = _text_list(spec_summary.get("scope"))

    # header.*
    _set_if_empty(out, ["header", "tender_title"],          title)
    _set_if_empty(out, ["header", "tender_no"],             tender_no)
    _set_if_empty(out, ["header", "contract_no"],           contract_no)
    _set_if_empty(out, ["header", "closing_datetime"],      closing)

    _set_if_empty(out, ["header", "contact", "name"],       contact.get("name") or None)
    _set_if_empty(out, ["header", "contact", "email"],      contact.get("email") or None)
    _set_if_empty(out, ["header", "contact", "phone"],      contact.get("phone") or None)

    # sections: add a minimal "Overview" if empty and we have scope/title
    if isinstance(out.get("sections"), list) and not out["sections"]:
        overview_items = []
        if title:
            overview_items.append(title)
        if scope_list:
            overview_items.extend(scope_list[:5])
        if overview_items:
            out["sections"].append({
                "title": "Overview",
                "items": overview_items
            })

    # parsed fields (optional) -> could add service dates, etc., if your parse_spec supplies them
    service_dates = parsed.get("service_dates") if isinstance(parsed, dict) else None
    if isinstance(service_dates, dict):
        # If your RFT skeleton has a part_2.service_dates area, fill it;
        # if not, skip. (Leave structure untouched if absent.)
        try:
            _set_if_empty(out, ["part_2_scope", "service_dates", "anticipated_start_date"], service_dates.get("anticipated_start_date"))
            _set_if_empty(out, ["part_2_scope", "service_dates", "end_date"],              service_dates.get("end_date"))
        except Exception:
            pass

    return out
