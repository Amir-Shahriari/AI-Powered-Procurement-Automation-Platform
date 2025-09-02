#app/routers/api.py

import uuid
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import List, Any

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from ..config import settings
from ..repo.records import load_record, save_record
from ..schemas import Record, SpecSummary
from ..services.textio import extract_text, chunks
from ..services.vectorstores import build_index, get_vs, _faiss_path, _chroma_name
from ..services.llm import rag_json
from ..services.parse_spec import parse_spec
from ..services.policy import scan_policy_files, extract_many, _build_ephemeral_vs
from ..services.templates import (
    load_returnables_template,
    load_rft_template,
    load_tepp_template,
    write_json,
)
from typing import List, Optional
from pathlib import Path
import json

from fastapi import APIRouter, UploadFile, File, Body, HTTPException
from fastapi.responses import FileResponse

from ..config import settings
from ..services.supplier import (
    process_suppliers,
    list_suppliers,
    get_supplier_returnables,
    save_supplier_returnables,
    generate_evaluation_for_suppliers,
)

from ..services.supplier import (
    process_suppliers,
    list_suppliers,
    get_supplier_returnables,
    save_supplier_returnables,
    generate_evaluation_for_suppliers,
)
from ..services.docx_export import export_json_to_docx
from ..services.returnables_filler import seed_returnables_from_spec
from ..services.rft_filler import seed_rft_from_spec
from ..services.compose import compose_tepp
from ..services.returnables_supplier import fill_returnables_from_supplier
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import FileResponse

from ..repo.records import load_record
from ..services.evaluation import generate_evaluation_excel
router = APIRouter()

SPEC_SUMMARY_PROMPT = """You summarise government engineering tender specifications.
Return ONLY strict JSON with fields:
{
  "title": null|string,
  "tender_no": null|string,
  "contract_no": null|string,
  "closing_datetime": null|string,
  "contact": {"name": null|string, "email": null|string, "phone": null|string},
  "scope": [string,...],
  "location": null|string,
  "safety_standards": [string,...]
}
Use ONLY the provided context. If unknown, set null or [].
"""

# -------------------------
# Upload -> generate JSONs
# -------------------------
@router.post("/upload", response_model=Record)
async def upload(file: UploadFile = File(...)):
    doc_id = str(uuid.uuid4())
    suffix = Path(file.filename).suffix or ".bin"
    tmp = settings.DATA_DIR / f"{doc_id}{suffix}"
    with open(tmp, "wb") as f:
        shutil.copyfileobj(file.file, f)

    text = extract_text(tmp)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not read text from the document.")

    # Build RAG index
    chs = chunks(text)
    build_index(doc_id, chs)
    vs = get_vs(doc_id)

    # Summary from RAG
    summary = rag_json(
        vs,
        SPEC_SUMMARY_PROMPT,
        [
            "tender title or document title",
            "tender number or contract number",
            "closing date and time",
            "contact name email phone",
            "scope of works",
            "location site",
            "safety standards ADR WHS ISO Australian Standards",
        ],
        max_ctx=8,
        min_chars=2000,
    )
    spec_summary = SpecSummary.model_validate(summary)
    parsed = parse_spec(text)

    # Optional policy corpus
    policy_files = scan_policy_files()
    policy_texts = extract_many(policy_files)
    policy_chunks = []
    if policy_texts:
        from ..deps import SPLITTER
        for t in policy_texts:
            policy_chunks.extend(SPLITTER.split_text(t))
    vs_policy = _build_ephemeral_vs(policy_chunks) if policy_chunks else None

    # Generate JSON artifacts
    ret = seed_returnables_from_spec(load_returnables_template(), spec_summary.model_dump(), parsed)
    rft = seed_rft_from_spec(load_rft_template(),         spec_summary.model_dump(), parsed)
    tepp = compose_tepp(spec_summary, parsed, vs, [vs_policy] if vs_policy else None)

    write_json(settings.DATA_DIR / f"{doc_id}.returnables.json", ret)
    write_json(settings.DATA_DIR / f"{doc_id}.rft.json", rft)
    write_json(settings.DATA_DIR / f"{doc_id}.tepp.json", tepp)

    # Persist record
    now = datetime.utcnow().isoformat()
    rec = Record(
        id=doc_id,
        created_at=now,
        updated_at=now,
        file_name=file.filename,
        source_type=suffix.lower(),
        vs_backend=settings.VECTOR_BACKEND,
        vs_location=str(_faiss_path(doc_id) if settings.VECTOR_BACKEND == "faiss_gpu" else _chroma_name(doc_id)),
        spec_summary=spec_summary,
        citations={},
        status="draft",
        raw_excerpt=text[:2000],
        returnable=None,
        returnable_structured=None,
        rft=None,
        tepp=None,
    )
    save_record(rec)
    return rec

@router.post("/records/{rec_id}/supplier_responses")
async def submit_supplier_responses(rec_id: str, files: List[UploadFile] = File(...)):
    """
    Accept one or more supplier response documents, build vector stores for
    each, run the LLM to populate empty fields in the existing returnable
    schedule, and save the updated schedule.
    """
    _ = load_record(rec_id)
    if not files:
        raise HTTPException(status_code=400, detail="No files submitted.")
    vs_list: List[Any] = []
    for f in files:
        if not f.filename:
            continue
        sup_id = f"{rec_id}_supplier_{uuid.uuid4()}"
        suffix = Path(f.filename).suffix or ".bin"
        dest = settings.DATA_DIR / f"{sup_id}{suffix}"
        with open(dest, "wb") as out_file:
            shutil.copyfileobj(f.file, out_file)
        try:
            text = extract_text(dest)
        except Exception:
            continue
        if text and text.strip():
            chs = chunks(text)
            build_index(sup_id, chs)
            vs_list.append(get_vs(sup_id))
    if not vs_list:
        raise HTTPException(status_code=400, detail="Could not extract any text from the uploaded supplier documents.")
    ret_path = settings.DATA_DIR / f"{rec_id}.returnables.json"
    current = json.loads(ret_path.read_text(encoding="utf-8"))
    updated = fill_returnables_from_supplier(current, vs_list)
    ret_path.write_text(json.dumps(updated, indent=2), encoding="utf-8")
    return {"ok": True}

@router.post("/records/{rec_id}/evaluation_sheet")
def generate_evaluation_sheet(rec_id: str, suppliers: List[str] = Body(...)):
    """
    Generate an Excel workbook for evaluating supplier tenders.

    The caller must provide a JSON array of supplier names.  The TEPP
    document associated with the record must exist (the TEPP is used to
    obtain the evaluation criteria and weightings).  The resulting
    spreadsheet includes columns for price, normalised price scores,
    qualitative scores (raw and weighted), total scores and ranking.  It
    is saved under the record's data directory and returned as a file
    response.
    """
    # Ensure the record exists
    _ = load_record(rec_id)
    try:
        path = generate_evaluation_excel(rec_id, suppliers)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    filename = f"{rec_id}_evaluation.xlsx"
    return FileResponse(path, filename=filename,
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.post("/records/{rec_id}/supplier_responses")
async def submit_supplier_responses(rec_id: str, files: List[UploadFile] = File(...)):
    base_returnables = json.loads(_path_returnables(rec_id).read_text(encoding="utf-8"))
    suppliers = process_suppliers(rec_id, files, base_returnables)
    return {"ok": True, "suppliers": suppliers}

@router.get("/records/{rec_id}/suppliers")
def get_suppliers(rec_id: str):
    return list_suppliers(rec_id)

@router.get("/records/{rec_id}/suppliers/{sup_id}/returnables_json")
def get_supplier_returnables_json(rec_id: str, sup_id: str):
    return get_supplier_returnables(rec_id, sup_id)

@router.patch("/records/{rec_id}/suppliers/{sup_id}/returnables_json")
def patch_supplier_returnables_json(rec_id: str, sup_id: str, payload: dict):
    save_supplier_returnables(rec_id, sup_id, payload); return {"ok": True}

@router.post("/records/{rec_id}/evaluate_suppliers")
def evaluate_suppliers(rec_id: str, supplier_ids: Optional[List[str]] = Body(None)):
    path = generate_evaluation_for_suppliers(rec_id, supplier_ids)
    return FileResponse(path, filename=f"{rec_id}_evaluation.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
# Upload supplier responses, auto-fill per-supplier returnables, and update manifest
@router.post("/records/{rec_id}/supplier_responses")
async def submit_supplier_responses(
    rec_id: str,
    files: List[UploadFile] = File(...),
):
    # Load the base (blank/generated) returnables JSON for this record
    ret_path = settings.DATA_DIR / f"{rec_id}.returnables.json"
    if not ret_path.exists():
        raise HTTPException(status_code=400, detail="Base returnables JSON not found for this record.")
    base_returnables = json.loads(ret_path.read_text(encoding="utf-8"))

    suppliers = process_suppliers(rec_id, files, base_returnables)
    return {"ok": True, "suppliers": suppliers}

# List suppliers for a record (reads the manifest)
@router.get("/records/{rec_id}/suppliers")
def api_list_suppliers(rec_id: str):
    return list_suppliers(rec_id)

# Get / update a specific supplier's filled returnables JSON
@router.get("/records/{rec_id}/suppliers/{sup_id}/returnables_json")
def api_get_supplier_returnables(rec_id: str, sup_id: str):
    return get_supplier_returnables(rec_id, sup_id)

@router.patch("/records/{rec_id}/suppliers/{sup_id}/returnables_json")
def api_patch_supplier_returnables(rec_id: str, sup_id: str, payload: dict):
    save_supplier_returnables(rec_id, sup_id, payload)
    return {"ok": True}

# Generate evaluation workbook (uses TEPP weights if present)
@router.post("/records/{rec_id}/evaluate_suppliers")
def api_evaluate_suppliers(
    rec_id: str,
    supplier_ids: Optional[List[str]] = Body(None),
):
    path = generate_evaluation_for_suppliers(rec_id, supplier_ids)
    return FileResponse(
        path,
        filename=f"{rec_id}_evaluation.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# -------------------------
# Record (basic)
# -------------------------
@router.get("/records/{rec_id}", response_model=Record)
def get_record(rec_id: str):
    return load_record(rec_id)


# -------------------------
# JSON artifacts: Returnables / RFT / TEPP
# -------------------------
def _path_returnables(rec_id: str) -> Path:
    return settings.DATA_DIR / f"{rec_id}.returnables.json"

def _path_rft(rec_id: str) -> Path:
    return settings.DATA_DIR / f"{rec_id}.rft.json"

def _path_tepp(rec_id: str) -> Path:
    return settings.DATA_DIR / f"{rec_id}.tepp.json"

def _read_json(path: Path):
    if not path.exists():
        raise HTTPException(status_code=404, detail="JSON not found for this record.")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read JSON: {e}")

def _write_json(path: Path, payload: dict):
    try:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write JSON: {e}")

@router.get("/records/{rec_id}/returnables_json")
def get_returnables_json(rec_id: str):
    _ = load_record(rec_id)
    return _read_json(_path_returnables(rec_id))

@router.patch("/records/{rec_id}/returnables_json")
def patch_returnables_json(rec_id: str, payload: dict):
    _ = load_record(rec_id)
    _write_json(_path_returnables(rec_id), payload)
    return {"ok": True}

@router.get("/records/{rec_id}/rft_json")
def get_rft_json(rec_id: str):
    _ = load_record(rec_id)
    return _read_json(_path_rft(rec_id))

@router.patch("/records/{rec_id}/rft_json")
def patch_rft_json(rec_id: str, payload: dict):
    _ = load_record(rec_id)
    _write_json(_path_rft(rec_id), payload)
    return {"ok": True}

@router.get("/records/{rec_id}/tepp_json")
def get_tepp_json(rec_id: str):
    _ = load_record(rec_id)
    return _read_json(_path_tepp(rec_id))

@router.patch("/records/{rec_id}/tepp_json")
def patch_tepp_json(rec_id: str, payload: dict):
    _ = load_record(rec_id)
    _write_json(_path_tepp(rec_id), payload)
    return {"ok": True}


# -------------------------
# DOCX Download endpoints
# -------------------------
@router.get("/records/{rec_id}/returnables_docx")
def download_returnables_docx(rec_id: str):
    _ = load_record(rec_id)
    data = _read_json(_path_returnables(rec_id))
    docx_path = export_json_to_docx(data, "Returnable Schedules")
    filename = f"{rec_id}.returnables.docx"
    return FileResponse(docx_path, filename=filename,
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

@router.get("/records/{rec_id}/rft_docx")
def download_rft_docx(rec_id: str):
    _ = load_record(rec_id)
    data = _read_json(_path_rft(rec_id))
    docx_path = export_json_to_docx(data, "Request for Tender")
    filename = f"{rec_id}.rft.docx"
    return FileResponse(docx_path, filename=filename,
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

@router.get("/records/{rec_id}/tepp_docx")
def download_tepp_docx(rec_id: str):
    _ = load_record(rec_id)
    data = _read_json(_path_tepp(rec_id))
    docx_path = export_json_to_docx(data, "Tender Evaluation & Probity Plan")
    filename = f"{rec_id}.tepp.docx"
    return FileResponse(docx_path, filename=filename,
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
