# app/routers/records.py
from fastapi import APIRouter
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel

from ..schemas import Record
from ..repo.records import load_record, save_record

class PatchPayload(BaseModel):
    data: Dict[str, Any]
    status: Optional[str] = None

router = APIRouter()

@router.get("/records/{rec_id}", response_model=Record)
def get_record(rec_id: str):
    return load_record(rec_id)



def _merge(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        out = a.copy()
        out.update(b)
        return out
    return b


