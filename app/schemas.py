# app/schemas.py
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# --- keep your existing SpecSummary, RFTDoc, TEPPDoc, etc. ---

class SpecSummary(BaseModel):
    title: Optional[str] = None
    tender_no: Optional[str] = None
    contract_no: Optional[str] = None
    closing_datetime: Optional[str] = None
    contact: Optional[Dict[str, Optional[str]]] = None  # or Contact model if you have it
    scope: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    safety_standards: List[str] = Field(default_factory=list)




class PatchPayload(BaseModel):
    data: Dict[str, Any]
    status: Optional[str] = None  # e.g. "draft" | "final" if you use statuses

class Record(BaseModel):
    id: str
    created_at: str
    updated_at: str
    file_name: str
    source_type: str
    vs_backend: str
    vs_location: str
    spec_summary: SpecSummary

    citations: Dict[str, List[str]] = Field(default_factory=dict)
    status: str = "draft"
    raw_excerpt: Optional[str] = None

    # ✅ NEW: single JSON-based Returnables (template-filled)
    returnables_json: Dict[str, Any] = Field(default_factory=dict)
