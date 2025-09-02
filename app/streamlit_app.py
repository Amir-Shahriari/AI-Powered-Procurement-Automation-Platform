"""
Streamlit user interface for generating tender documents.

This script provides an interactive, browser‐based workflow for generating
a Tender Evaluation & Probity Plan (TEPP) and the associated returnable
schedules from a technical specification.  It wraps the existing
low‑level services found in the ``app.services`` package with a simple
and approachable user interface built on top of `streamlit`.  Users
upload a specification file, pick a model for the LLM, and the app
handles the rest: it extracts text, builds a vector store, calls the
LLM to summarise and parse the spec, composes a TEPP, displays the
evaluation criteria and weighting rationales, and finally assembles
the returnable schedules.  At each stage the user can inspect the
intermediate JSON and download the generated DOCX files.

To run this app locally install `streamlit` in your environment and
execute:

    streamlit run app/streamlit_app.py

The application reads and writes data into the same DATA_DIR defined
in :mod:`app.config`.  Temporary vector stores are also persisted
under that directory; unique document identifiers are generated per
session to avoid collisions.
"""
import os, sys
# Ensure the project root (the parent of 'app') is on sys.path when run by Streamlit
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import uuid
from pathlib import Path
from typing import Optional, List, Dict

import pandas as pd
import streamlit as st

from app.config import settings
from app.schemas import SpecSummary
from app.services.textio import extract_text, chunks
from app.services.vectorstores import build_index, get_vs
from app.services.llm import rag_json, set_runtime_model, reset_runtime_model
from app.services.parse_spec import parse_spec
from app.services.policy import scan_policy_files, extract_many, _build_ephemeral_vs
from app.services.templates import load_rft_template, load_tepp_template, write_json
from app.services.returnables_filler import seed_returnables_from_spec
from app.services.rft_filler import seed_rft_from_spec
from app.services.compose import compose_tepp, compose_returnable_schedules
from app.services.docx_export import export_json_to_docx
from app.repo.records import save_record, load_record


# The same prompt used by the FastAPI upload route.  It instructs the
# LLM to produce a concise JSON summary of the tender specification
# including title, tender number and other high‑level metadata.  If
# values are unknown they should be null or empty.
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


def _generate_documents(file_path: Path, model: str) -> Dict[str, Dict]:
    """Drive the core document generation pipeline.

    Given the path to an uploaded specification and a model name, this
    helper function extracts text, builds a vector store, summarises
    and parses the specification, composes the TEPP and returnables
    JSONs, and returns them along with the parsed metadata.  A
    temporary document identifier is generated for each call so that
    vector stores and JSON artefacts do not collide across sessions.

    Parameters
    ----------
    file_path: Path
        Location of the uploaded specification on disk.
    model: str
        The name of the Ollama/Gemini model to use.  This value is
        passed through to :func:`set_runtime_model` which overrides
        the model for the duration of the call.

    Returns
    -------
    dict
        A dictionary with keys ``spec_summary``, ``parsed``, ``tepp``
        and ``returnables``.  Values are the corresponding Python
        objects; ``tepp`` and ``returnables`` are nested dictionaries
        serialisable to JSON.
    """
    # Create a new document identifier to isolate vector stores and
    # outputs.  Persist under the configured DATA_DIR.
    doc_id = str(uuid.uuid4())
    suffix = file_path.suffix or ".bin"
    temp_path = settings.DATA_DIR / f"{doc_id}{suffix}"
    # Copy the uploaded file into our data directory.  The input file
    # may be a SpooledTemporaryFile so we read bytes from it.
    with open(file_path, "rb") as src, open(temp_path, "wb") as dst:
        dst.write(src.read())

    # Extract raw text from the specification.  ``extract_text``
    # supports common office formats and falls back to ``textract``
    # under the hood.  If no text can be read an exception will be
    # raised to the caller.
    text = extract_text(temp_path)
    if not text or not text.strip():
        raise ValueError("Could not read text from the document.")

    # Split the text into overlapping chunks suitable for building a
    # vector store.  The default chunker in ``textio`` uses
    # heuristics to preserve sentence boundaries.
    chs = chunks(text)
    build_index(doc_id, chs)
    vs = get_vs(doc_id)

    # Override the model for the duration of this request.  When using
    # Gemini the environment variable GOOGLE_API_KEY must be set; for
    # local operation set LLM_PROVIDER=ollama and ensure an Ollama
    # server is running.  After generation we reset the override.
    token = set_runtime_model(model)
    try:
        # Summarise the specification into a simple JSON payload.  This
        # call uses the RAG pipeline to retrieve relevant context from
        # the vector store and then queries the LLM with the prompt and
        # a set of field queries.  The output is validated using
        # pydantic's SpecSummary model.
        summary_json = rag_json(
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
        spec_summary = SpecSummary.model_validate(summary_json)

        # Perform a deterministic parse of the specification.  This
        # function extracts project metadata and domain‑specific
        # information without using the LLM.
        parsed = parse_spec(text)

        # Optionally incorporate policy documents into the RAG context.
        # If additional policies exist in ``app/policy``, they will
        # influence the TEPP generation.  We build a small vector
        # store on the fly for these documents.  For simplicity we
        # ignore errors if no policy files are present.
        policy_files = scan_policy_files()
        policy_texts = extract_many(policy_files)
        policy_chunks: List[str] = []
        if policy_texts:
            from .deps import SPLITTER  # imported lazily to avoid circular import
            for t in policy_texts:
                policy_chunks.extend(SPLITTER.split_text(t))
        vs_policy = _build_ephemeral_vs(policy_chunks) if policy_chunks else None

        # Compose the TEPP.  This function orchestrates a complex
        # interaction with the LLM, retrieving context, prompting
        # sections, deciding evaluation weightings and building a rich
        # structured JSON representation of the Tender Evaluation &
        # Probity Plan.  The optional ``extra_vss`` argument allows
        # additional vector stores (e.g. policies) to be consulted.
        tepp = compose_tepp(spec_summary, parsed, vs, [vs_policy] if vs_policy else None)

        # Build the returnable schedules.  Unlike the TEPP this
        # generator does not call the LLM; it assembles a structured
        # JSON document containing instructions, reference checklists
        # and all schedules that tenderers must complete.  The
        # ``non_negotiable_date`` parameter may be provided to insert
        # a mandated commencement date in Schedule 9; we leave it
        # unset here.
        returnables = compose_returnable_schedules(spec_summary, parsed, non_negotiable_date=None)

        return {
            "spec_summary": spec_summary.model_dump(),
            "parsed": parsed,
            "tepp": tepp,
            "returnables": returnables,
        }
    finally:
        reset_runtime_model(token)


def main() -> None:
    """Entry point for the Streamlit UI."""
    st.set_page_config(page_title="Before Advertisement", layout="wide")
    st.title("Before Advertisement")

    # Model selector allows the user to pick the underlying LLM.  The
    # default options correspond to local Ollama models defined in
    # ``app/config.py``.  Additional models can be added here if
    # available.
    model = st.selectbox(
        "Choose LLM model",
        options=["llama3.1:8b", "llama3:latest", "mistral:latest"],
        index=0,
        help="Select which language model to use for summarising and composing documents."
    )

    uploaded_file = st.file_uploader(
        "Upload technical specification",
        type=["pdf", "docx", "txt", "doc"],
        help="Provide the tender specification file (PDF, DOCX, DOC or TXT)."
    )

    # When the user clicks the Generate button we run the pipeline.
    if uploaded_file is not None:
        if st.button("Generate TEPP and Returnables"):
            # Persist the uploaded file to a temporary location.  Use
            # Streamlit's uploaded file API to access the underlying
            # buffer and write it to disk.  We use a UUID file name to
            # avoid clobbering existing files.
            temp_dir = Path(st.experimental_get_query_params().get("data_dir", [str(settings.DATA_DIR)])[0])
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_path = temp_dir / uploaded_file.name
            with open(temp_path, "wb") as out:
                out.write(uploaded_file.getbuffer())

            with st.spinner("Generating documents, please wait…"):
                try:
                    outputs = _generate_documents(temp_path, model)
                except Exception as exc:
                    st.error(f"An error occurred during generation: {exc}")
                    return

            # Store results in the session state so they persist across
            # interactions (e.g. when the user expands sections or
            # downloads files).  The 'tepp' key is especially
            # important as it drives the display of the criteria table.
            st.session_state["spec_summary"] = outputs["spec_summary"]
            st.session_state["parsed"] = outputs["parsed"]
            st.session_state["tepp"] = outputs["tepp"]
            st.session_state["returnables"] = outputs["returnables"]
            st.success("Document generation complete!")

    # Once a TEPP has been generated we reveal the evaluation criteria
    # table.  This section is rendered whenever the corresponding
    # object exists in the session state.
    if "tepp" in st.session_state:
        tepp = st.session_state["tepp"]
        # Navigate to the weighted criteria.  Defensive checks are
        # employed to avoid KeyError if the JSON structure changes.
        table: List[Dict[str, str]] = (
            tepp
            .get("tender_evaluation", {})
            .get("evaluation_methodology", {})
            .get("required_criteria_table", [])
        )
        st.subheader("Evaluation criteria and weightings")
        if table:
            df = pd.DataFrame(table)
            # Reorder columns for a nicer display
            cols = [c for c in ["criterion", "weight", "rationale"] if c in df.columns]
            st.table(df[cols])
        else:
            st.info("No criteria table was generated.")

        # Button to view the full TEPP JSON.  We use an expander to
        # collapse the potentially large document by default.  The
        # document is presented as formatted JSON using Streamlit's
        # built‑in rendering.
        with st.expander("Full TEPP document", expanded=False):
            st.json(tepp)

        # Provide a download option for the TEPP as a DOCX.  We
        # generate the DOCX on demand to avoid unnecessary work.
        if st.button("Download TEPP (DOCX)"):
            docx_path = export_json_to_docx(tepp, "Tender Evaluation & Probity Plan")
            with open(docx_path, "rb") as f:
                data = f.read()
            st.download_button(
                label="Download TEPP",
                data=data,
                file_name="tepp.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

        # Show the returnable schedules once TEPP has been generated.
        st.subheader("Returnable schedules")
        returnables = st.session_state.get("returnables")
        if returnables:
            with st.expander("Returnables JSON", expanded=False):
                st.json(returnables)
            if st.button("Download Returnables (DOCX)"):
                docx_path = export_json_to_docx(returnables, "Returnable Schedules")
                with open(docx_path, "rb") as f:
                    data = f.read()
                st.download_button(
                    label="Download Returnables",
                    data=data,
                    file_name="returnables.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
        else:
            st.info("Returnable schedules have not been generated yet.")


if __name__ == "__main__":
    main()