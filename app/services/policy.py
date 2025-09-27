from pathlib import Path
from typing import List
from ..config import settings
from app.services.textio import extract_text
from app.services.vectorstores import LCFAISS  # type: ignore
from app.deps import EMBED

def _build_ephemeral_vs(texts: List[str]):
    if not texts: return None
    return LCFAISS.from_texts(texts=texts, embedding=EMBED)

def scan_policy_files() -> List[Path]:
    pats = ["tepp", "evaluation", "eval", "manual", "quotation", "returnable", "schedule", "part 5", "fee structure", "pricing"]
    roots = [settings.DATA_DIR]
    out = []
    for root in roots:
        if not root.exists(): continue
        for p in root.glob("*"):
            name = p.name.lower()
            if any(k in name for k in pats) and p.suffix.lower() in (".pdf", ".docx", ".txt"):
                out.append(p)
    return out

def extract_many(paths: List[Path]) -> List[str]:
    out = []
    for p in paths:
        try:
            out.append(extract_text(p))
        except Exception:
            continue
    return out
