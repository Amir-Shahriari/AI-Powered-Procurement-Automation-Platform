import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Form

from ..config import settings
from ..schemas import Record, SpecSummary
from ..services.textio import extract_text, chunks
from ..services.vectorstores import build_index, get_vs, _faiss_path, _chroma_name
from ..services.llm import rag_json, set_runtime_model, reset_runtime_model
from ..services.parse_spec import parse_spec
from ..services.policy import scan_policy_files, extract_many, _build_ephemeral_vs

from ..services.templates import (
    load_returnables_template,
    load_rft_template,
    write_json,
)
from ..services.returnables_filler import seed_returnables_from_spec
from ..services.rft_filler import seed_rft_from_spec
from ..services.compose import compose_tepp, compose_returnable_schedules

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



@router.post("/upload", response_model=Record)
async def upload(
    file: UploadFile = File(...),
    model: Optional[str] = Form(None),  # <-- model from dropdown
):
    # Save upload
    if not file or not file.filename:
        raise HTTPException(400, "No file provided.")

    doc_id = str(uuid.uuid4())
    suffix = Path(file.filename).suffix
    tmp = settings.DATA_DIR / f"{doc_id}{suffix}"
    with open(tmp, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Extract text
    text = extract_text(tmp)
    if not text.strip():
        raise HTTPException(400, "Could not read text from the document.")

    # Build VS for summary + generation
    chs = chunks(text)
    build_index(doc_id, chs)
    vs = get_vs(doc_id)

    # Set the runtime model override for this request only
    token = set_runtime_model(model)

    try:
        # Summarise spec (high-level metadata)
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

        # Deterministic parsing pass
        parsed = parse_spec(text)

        # (Optional) policy context
        policy_files = scan_policy_files()
        policy_texts = extract_many(policy_files)
        policy_chunks = []
        if policy_texts:
            from ..deps import SPLITTER
            for t in policy_texts:
                policy_chunks.extend(SPLITTER.split_text(t))
        vs_policy = _build_ephemeral_vs(policy_chunks) if policy_chunks else None

        # Generate and SAVE JSON artifacts
        ret_filled = compose_returnable_schedules(spec_summary, parsed, non_negotiable_date=None)
        write_json(settings.DATA_DIR / f"{doc_id}.returnables.json", ret_filled)
        rft_filled  = seed_rft_from_spec(load_rft_template(),         spec_summary.model_dump(), parsed)
        tepp_filled = compose_tepp(spec_summary, parsed, vs, [vs_policy] if vs_policy else None)

        write_json(settings.DATA_DIR / f"{doc_id}.returnables.json", ret_filled)
        write_json(settings.DATA_DIR / f"{doc_id}.rft.json",          rft_filled)
        write_json(settings.DATA_DIR / f"{doc_id}.tepp.json",         tepp_filled)

        # Persist minimal record
        now = datetime.utcnow().isoformat()
        rec = Record(
            id=doc_id,
            created_at=now,
            updated_at=now,
            file_name=file.filename,
            source_type=suffix.lower(),
            vs_backend=settings.VECTOR_BACKEND,
            vs_location=str(
                _faiss_path(doc_id) if settings.VECTOR_BACKEND == "faiss_gpu" else _chroma_name(doc_id)
            ),
            spec_summary=spec_summary,
            # JSON files are the source of truth; the in-memory doc fields aren’t used
            rft=None,
            tepp=None,
            citations={},
            status="draft",
            raw_excerpt=text[:2000],
            returnable=None,
            returnable_structured=None,
        )

        from ..repo.records import save_record
        save_record(rec)
        return rec
    finally:
        # Always clear the override so it doesn't leak between requests
        reset_runtime_model(token)
