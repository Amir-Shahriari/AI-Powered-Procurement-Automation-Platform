#app/services/vectorstores.py

from pathlib import Path
from typing import List
from fastapi import HTTPException
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores import FAISS as LCFAISS
from ..config import settings
from app.deps import EMBED, CHROMA_SETTINGS

def _faiss_path(doc_id: str) -> Path:
    return settings.FAISS_DIR / f"{doc_id}"

def _chroma_name(doc_id: str) -> str:
    return f"spec-{doc_id}"

def build_index(doc_id: str, chunks: List[str]):
    if settings.VECTOR_BACKEND == "faiss_gpu":
        try:
            # import here so environments without faiss can still import the module
            import faiss  # noqa: F401
        except Exception:
            raise HTTPException(500, "FAISS-GPU not available. Install faiss-gpu via conda.")
        vs = LCFAISS.from_texts(texts=chunks, embedding=EMBED)
        vs.save_local(str(_faiss_path(doc_id)))
        return
    Chroma.from_texts(
        texts=chunks, embedding=EMBED, persist_directory=str(settings.INDEX_DIR),
        collection_name=_chroma_name(doc_id), client_settings=CHROMA_SETTINGS
    )

def get_vs(doc_id: str):
    if settings.VECTOR_BACKEND == "faiss_gpu":
        try:
            import faiss
        except Exception:
            raise HTTPException(500, "FAISS-GPU not available.")
        vs = LCFAISS.load_local(str(_faiss_path(doc_id)), embeddings=EMBED, allow_dangerous_deserialization=True)
        try:
            # Try to move the index to GPU. If it fails (for example, due to lack of GPU memory)
            # leave the index on CPU instead of raising an exception.
            res = faiss.StandardGpuResources()
            vs.index = faiss.index_cpu_to_gpu(res, 0, vs.index)
        except Exception:
            pass  # Leave the index on CPU; retrieval will still work.
        return vs
    return Chroma(
        embedding_function=EMBED, persist_directory=str(settings.INDEX_DIR),
        collection_name=_chroma_name(doc_id), client_settings=CHROMA_SETTINGS,
    )

def similar(vs, query: str, k: int = 6) -> List[str]:
    try:
        docs = vs.similarity_search(query, k=k)
        return [d.page_content for d in docs]
    except Exception:
        return []
