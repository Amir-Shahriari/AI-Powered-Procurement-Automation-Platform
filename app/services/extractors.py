# app/services/extractors.py
from __future__ import annotations
from typing import Any, Dict, Iterable, List
from copy import deepcopy

from app.services.llm import rag_json

def _merge(a: Any, b: Any) -> Any:
    # Deep-ish merge for dicts/lists; b wins on conflicts; primitive overwrite.
    if isinstance(a, dict) and isinstance(b, dict):
        out = dict(a)
        for k, v in b.items():
            out[k] = _merge(out.get(k), v)
        return out
    if isinstance(a, list) and isinstance(b, list):
        return a if a else b
    return b if b not in (None, "", [], {}) else a

def extract_returnables(vs, extra_retrievers: Iterable = ()):
    """
    Ask the LLM for narrowly-scoped JSON chunks we can merge into the
    Returnables skeleton without hallucinating. Keep requests small & explicit.
    """
    hints = [
        # Milestones / programme
        {
          "prompt": """Return ONLY strict JSON:
{"schedule_9_service_delivery_performance":{"programme":{"milestones":[{"name":"","start_date":"","end_date":""}, ...]}}}
Use the spec wording for milestone names when possible. If dates are not stated, keep empty strings.""",
          "keywords": [
              "program", "programme", "schedule", "milestone",
              "practical completion", "testing", "commissioning"
          ]
        },
        # Safety/WHS snippets
        {
          "prompt": """Return ONLY strict JSON:
{"schedule_14_work_health_and_safety":{"verification_documents":{"manual_policy_procedures":null,"responsibilities_allocation_chart":null,"consultation_statement":null,"sample_inspection_checklists_and_records":null,"sample_hazard_report_corrective_actions":null}}}
For each field set true/false if the spec explicitly requires it; otherwise null.""",
          "keywords": ["WHS", "work health", "safety", "SafeWork", "ISO", "AS/NZS"]
        },
        # Pricing table hints (if your spec lists any explicit lines)
        {
          "prompt": """Return ONLY strict JSON:
{"schedule_10_fee_structure":{"pricing_schedule_ahu_refurbishments":[{"item_no":"","service_details":""}]}}
Add items exactly as listed in the spec if present. If none, return an empty array.""",
          "keywords": ["price", "pricing", "schedule", "boq", "bill of quantities", "lump sum"]
        },
    ]
    out: Dict[str, Any] = {}
    for h in hints:
        piece = rag_json(vs, h["prompt"], h["keywords"], extra_retrievers=list(extra_retrievers))
        out = _merge(out, piece if isinstance(piece, dict) else {})
    return out

def extract_rft(vs, extra_retrievers: Iterable = ()):
    hints = [
        {
          "prompt": """Return ONLY strict JSON:
{"part_2_scope":{"services":{"decommissioning_removal":[],"supply_installation":[],"electrical_controls":[],"hoisting_cranage":[],"testing_commissioning":[],"maintenance_warranty":[]}}}
Populate arrays with short bullet strings quoted directly or closely from the spec. Leave arrays empty if not found.""",
          "keywords": ["scope", "decommission", "supply", "install", "electrical", "controls", "crane", "testing", "commissioning", "maintenance", "warranty"]
        },
        {
          "prompt": """Return ONLY strict JSON:
{"part_2_scope":{"site_visit":{"required":null,"datetime":null,"location":null,"ppe_required":[]}}}
If a site visit is required or recommended, set required=true; if optional set false; if not stated set null.""",
          "keywords": ["site visit", "inspection", "briefing", "pre-tender", "PPE"]
        },
        {
          "prompt": """Return ONLY strict JSON:
{"evaluation":{"criteria":[]}}
Each criterion should be a short string from the spec (e.g. "Capability and experience"). Return [] if not specified.""",
          "keywords": ["evaluation", "criteria", "weighted", "assessment", "value for money", "conformance"]
        },
    ]
    out: Dict[str, Any] = {}
    for h in hints:
        piece = rag_json(vs, h["prompt"], h["keywords"], extra_retrievers=list(extra_retrievers))
        out = _merge(out, piece if isinstance(piece, dict) else {})
    return out

def extract_tepp(vs, extra_retrievers: Iterable = ()):
    hints = [
        {
          "prompt": """Return ONLY strict JSON:
{"evaluation_process":{"scoring_methodology":{"scale":"","definitions":"","weightings":[]}}}
Copy scale/definitions text if stated; if not, leave empty strings/arrays.""",
          "keywords": ["score", "scoring", "rating", "weighting", "methodology"]
        },
        {
          "prompt": """Return ONLY strict JSON:
{"evaluation_criteria":[{"criterion":"","weighting":"","subcriteria":[{"subcriterion":"","weighting":""}]}]}
Use exact criterion names where possible; weightings may be numbers or strings. If not present, return [].""",
          "keywords": ["evaluation criteria", "weight", "criterion", "sub-criteria"]
        },
        {
          "prompt": """Return ONLY strict JSON:
{"evaluation_process":{"evaluation_stages":[{"stage_name":"","description":"","responsible_party":"","deliverables":""}]}}
Return the stages if the process is described, else [].""",
          "keywords": ["stage", "process", "timeline", "procedure", "committee"]
        },
    ]
    out: Dict[str, Any] = {}
    for h in hints:
        piece = rag_json(vs, h["prompt"], h["keywords"], extra_retrievers=list(extra_retrievers))
        out = _merge(out, piece if isinstance(piece, dict) else {})
    return out
