from pathlib import Path
from fastapi import HTTPException
import fitz, docx2txt
from typing import List
from ..deps import SPLITTER

def extract_text(tmp: Path) -> str:
    ext = tmp.suffix.lower()
    if ext == ".pdf":
        doc = fitz.open(tmp)
        return "\n".join([doc.load_page(i).get_text("text") for i in range(len(doc))])
    if ext == ".docx":
        return docx2txt.process(str(tmp)) or ""
    if ext == ".txt":
        return tmp.read_text(encoding="utf-8", errors="ignore")
    raise HTTPException(400, "Unsupported file type. Upload PDF, DOCX, or TXT.")

def chunks(text: str) -> List[str]:
    return SPLITTER.split_text(text)
