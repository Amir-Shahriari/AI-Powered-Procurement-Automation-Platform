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
    if ext == ".doc":
        # For .doc files, try to read as text (basic approach)
        # In a production environment, you might want to use python-docx2txt or similar
        try:
            return tmp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""
    if ext == ".txt":
        return tmp.read_text(encoding="utf-8", errors="ignore")
    if ext in [".csv", ".xlsx", ".xls"]:
        # For spreadsheet files, try to read as text (basic approach)
        try:
            return tmp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""
    if ext == ".json":
        # For JSON files, return the content as text
        try:
            return tmp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""
    raise HTTPException(400, f"Unsupported file type: {ext}. Upload PDF, DOCX, DOC, TXT, CSV, XLSX, XLS, or JSON.")

def chunks(text: str) -> List[str]:
    return SPLITTER.split_text(text)
