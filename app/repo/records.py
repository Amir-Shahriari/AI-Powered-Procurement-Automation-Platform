import json
from datetime import datetime
from pathlib import Path
from fastapi import HTTPException
from ..config import settings
from ..schemas import Record

def save_record(rec: Record):
    p = settings.DATA_DIR / f"{rec.id}.json"
    with open(p, "w") as f:
        json.dump(rec.model_dump(), f, indent=2)

def load_record(rec_id: str) -> Record:
    p = settings.DATA_DIR / f"{rec_id}.json"
    if not p.exists():
        raise HTTPException(404, "Record not found")
    with open(p) as f:
        return Record.model_validate(json.load(f))
