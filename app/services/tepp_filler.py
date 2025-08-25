# app/services/tepp_filler.py
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

def seed_tepp_from_spec(template: Dict[str, Any],
                        spec_summary: Dict[str, Any],
                        parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fill TEPP skeleton with obvious bits (title / tender_no / high-level summary from scope).
    Only fills empty fields.
    """
    out = deepcopy(template)

    title      = _first(spec_summary.get("title"), spec_summary.get("tender_title"))
    tender_no  = spec_summary.get("tender_no")
    scope_list = _text_list(spec_summary.get("scope"))

    # document_metadata.*
    _set_if_empty(out, ["document_metadata", "document_title"], title or "")
    _set_if_empty(out, ["document_metadata", "tender_number"],  tender_no or "")

    # introduction.objectives / background from scope if empty
    if scope_list:
        _set_if_empty(out, ["introduction", "objectives"], " ; ".join(scope_list))

    # If parse_spec provides any committee/contact structure, lightly prefill
    committee = parsed.get("evaluation_committee") if isinstance(parsed, dict) else None
    if isinstance(committee, list) and committee and isinstance(out.get("evaluation_governance", {}).get("evaluation_committee", {}).get("members"), list):
        # Only seed the first member if the template is empty/default
        members = out["evaluation_governance"]["evaluation_committee"]["members"]
        if not members or (len(members) == 1 and not any(members[0].values())):
            out["evaluation_governance"]["evaluation_committee"]["members"] = committee

    return out
