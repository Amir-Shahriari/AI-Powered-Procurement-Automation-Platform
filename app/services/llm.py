import json, re, contextvars
from typing import Any, List, Optional, Iterable, Tuple
from langchain.schema import SystemMessage, HumanMessage
# from langchain_community.chat_models import ChatOllama
from langchain_ollama import ChatOllama  # switch from langchain_community
from langchain_openai import ChatOpenAI
from ..config import settings


# -------------------------------
# Runtime model override (per-request)
# -------------------------------
# We let the /upload route set a per-request model (e.g., "llama3.1:8b") via a context var.
_RUNTIME_MODEL: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "runtime_model", default=None
)

def set_runtime_model(model: Optional[str]) -> Optional[contextvars.Token]:
    """Temporarily override the model for the current request/task. Returns a token for reset."""
    if model and isinstance(model, str) and model.strip():
        return _RUNTIME_MODEL.set(model.strip())
    return None

def reset_runtime_model(token: Optional[contextvars.Token]) -> None:
    """Reset the model override after finishing a request."""
    if token is not None:
        _RUNTIME_MODEL.reset(token)

def _current_model(default_ollama: str, default_openai: str) -> str:
    """Return the model name, preferring the per-request override if present."""
    return _RUNTIME_MODEL.get() or (default_ollama if settings.LLM_PROVIDER.lower() == "ollama" else default_openai)


# -------------------------------
# LLM client
# -------------------------------
def _llm(json_mode: bool = False):
    """
    Create an LLM client based on settings.
    - Ollama supports `format="json"` via LangChain's ChatOllama JSON mode.
    - OpenAI uses response_format for JSON.
    """
    provider = settings.LLM_PROVIDER.lower()
    if provider == "ollama":
        # Use per-request override if available, else settings.OLLAMA_MODEL
        model_name = _current_model(settings.OLLAMA_MODEL, settings.OPENAI_MODEL)
        kwargs = dict(
            base_url=settings.OLLAMA_BASE_URL,
            model=model_name,
            temperature=0,
            request_timeout=150,   # ← hard timeout so requests never hang
        )
        if json_mode:
            kwargs["format"] = "json"
        return ChatOllama(**kwargs)

    # OpenAI (optionally respects the runtime override too)
    model_name = _current_model(settings.OLLAMA_MODEL, settings.OPENAI_MODEL)
    kwargs = dict(
        model=model_name,
        temperature=0,
        base_url=settings.OPENAI_BASE_URL,
        request_timeout=150,     # ← hard timeout so requests never hang
        max_retries=2,
    )
    if json_mode:
        kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
    return ChatOpenAI(**kwargs)


# -------------------------------
# JSON utilities
# -------------------------------
_CODE_FENCE_OPEN = re.compile(r"^```(?:json)?", flags=re.IGNORECASE)
_CODE_FENCE_CLOSE = re.compile(r"```$")

def _clean_json(s: str) -> str:
    """Strip ``` fences and trailing code fences if present."""
    s = s.strip()
    if s.startswith("```"):
        s = _CODE_FENCE_OPEN.sub("", s).strip()
        s = _CODE_FENCE_CLOSE.sub("", s).strip()
    return s

def _try_parse_json(response: str) -> Any:
    """
    Parse JSON with fallbacks:
      - remove code fences
      - grab the last JSON object/array if extra prose leaked
    """
    s = _clean_json(response)
    try:
        return json.loads(s)
    except Exception:
        m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])\s*$", response.strip())
        if not m:
            raise
        return json.loads(m.group(1))


# -------------------------------
# Retrieval helpers
# -------------------------------
def _expand_query(q: str) -> List[str]:
    """
    Light query expansion to catch common spec phrasing variants.
    Keeps the original first so 'similar' ranks by it first.
    """
    ql = q.lower()
    alts = [q]
    synonyms: List[Tuple[str, List[str]]] = [
        ("work health & safety", ["whs", "oh&s", "safety", "occupational health and safety"]),
        ("testing & commissioning", ["testing and commissioning", "commissioning", "testing", "site acceptance test", "sat", "factory acceptance test", "fat"]),
        ("bmcs", ["bms", "building management system", "bacnet", "hli", "high level interface"]),
        ("warranty", ["defects liability", "defects period", "warranty period"]),
        ("maintenance", ["service", "preventive maintenance", "o&m", "operations and maintenance"]),
        ("scope", ["scope of works", "scope", "description of works", "project scope"]),
        ("evaluation criteria", ["assessment criteria", "selection criteria", "weighting"]),
        ("quality", ["quality management", "qms", "itp", "inspection test plan"]),
        ("drawings", ["schematics", "diagrams", "shop drawings"]),
    ]
    for key, vs in synonyms:
        if key in ql:
            alts.extend(vs)
    return list(dict.fromkeys(alts))  # de-dupe preserve order


def _dedup_strs(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for s in items:
        s_norm = re.sub(r"\s+", " ", (s or "").strip())
        if s_norm and s_norm not in seen:
            seen.add(s_norm); out.append(s_norm)
    return out


def _gather_snippets(similar_fn, queries: List[str], max_ctx: int, min_chars: int) -> List[str]:
    """
    Try expanded queries first; widen until we meet a minimum total char budget.
    """
    blocks: List[str] = []
    # pass 1: expanded queries
    for q in queries:
        for variant in _expand_query(q):
            try:
                blocks.extend(similar_fn(variant, k=max_ctx) or [])
            except Exception:
                pass
    blocks = _dedup_strs(blocks)

    # pass 2: if still too short, broaden with generic anchors
    total_chars = sum(len(b) for b in blocks)
    if total_chars < min_chars:
        generic = [
            "scope", "summary", "specification", "standards", "testing",
            "commissioning", "warranty", "maintenance", "bmcs", "pricing"
        ]
        for g in generic:
            try:
                blocks.extend(similar_fn(g, k=max(3, max_ctx // 2)) or [])
            except Exception:
                pass
        blocks = _dedup_strs(blocks)

    # soft cap context to keep prompts reasonable
    cap_chars = max(min_chars * 2, 8000)
    trimmed: List[str] = []
    running = 0
    for b in blocks:
        if running + len(b) > cap_chars:
            break
        trimmed.append(b); running += len(b)
    return trimmed


# -------------------------------
# RAG -> JSON (single VS)
# -------------------------------
def rag_json(
    vs,
    prompt: str,
    field_queries: List[str],
    max_ctx: int = 8,
    min_chars: int = 2500,
) -> Any:
    """
    Retrieve labeled context blocks and ask the LLM to return STRICT JSON.
    Improvements:
      - query expansion to improve recall
      - minimum context budget (min_chars) with broadening if needed
      - de-duplication and soft char cap to avoid token blowups
    """
    # similar(vs, query, k) is already provided in your repo
    from .vectorstores import similar

    def _similar(q: str, k: int = max_ctx) -> List[str]:
        try:
            return similar(vs, q, k=k)
        except Exception:
            # Fallback to LangChain interface if available
            try:
                docs = vs.similarity_search(q, k=k)
                return [d.page_content for d in docs]
            except Exception:
                return []

    blocks = _gather_snippets(_similar, field_queries, max_ctx=max_ctx, min_chars=min_chars)
    context = ""
    if blocks:
        # label by coarse query categories for better grounding
        labeled = []
        for i, b in enumerate(blocks, 1):
            labeled.append(f"[CTX {i}]\n{b}")
        context = "\n\n".join(labeled)
    else:
        context = "NO_CONTEXT"

    messages = [
        SystemMessage(content=prompt.strip()),
        HumanMessage(content=(
            "Context:\n" + context +
            "\n\nReturn ONLY the JSON object. Do not include any keys not asked for. "
            "If a value is not clearly supported by the context, set it to null or []."
        )),
    ]
    resp = _llm(json_mode=True).invoke(messages).content
    try:
        return _try_parse_json(resp)
    except Exception:
        repair = messages + [HumanMessage(content="Respond again as STRICT JSON only. No prose.")]
        resp2 = _llm(json_mode=True).invoke(repair).content
        return _try_parse_json(resp2)


# -------------------------------
# RAG -> JSON (primary + extras)
# -------------------------------
def rag_json_plus(
    vs_primary,
    prompt: str,
    field_queries: List[str],
    extra_vss: Optional[List[Any]] = None,
    max_ctx: int = 8,
    min_chars: int = 2500,
) -> Any:
    """
    Like rag_json, but gathers from extra vector stores (e.g., policy manuals).
    """
    from .vectorstores import similar

    def _collect(vs, q, k) -> List[str]:
        try:
            return similar(vs, q, k=k)
        except Exception:
            try:
                docs = vs.similarity_search(q, k=k)
                return [d.page_content for d in docs]
            except Exception:
                return []

    # gather
    blocks: List[str] = []
    for q in field_queries:
        for variant in _expand_query(q):
            blocks.extend(_collect(vs_primary, variant, k=max_ctx) or [])
            if extra_vss:
                for evs in extra_vss:
                    blocks.extend(_collect(evs, variant, k=max(3, max_ctx // 2)) or [])
    blocks = _dedup_strs(blocks)

    # widen if needed
    if sum(len(b) for b in blocks) < min_chars:
        for g in ["scope", "probity", "evaluation", "criteria", "testing", "warranty", "maintenance"]:
            blocks.extend(_collect(vs_primary, g, k=max(3, max_ctx // 2)) or [])
    blocks = _dedup_strs(blocks)

    # cap
    cap_chars = max(min_chars * 2, 8000)
    trimmed: List[str] = []
    running = 0
    for b in blocks:
        if running + len(b) > cap_chars:
            break
        trimmed.append(b); running += len(b)

    context = "NO_CONTEXT" if not trimmed else "\n\n".join(f"[CTX {i}]\n{b}" for i, b in enumerate(trimmed, 1))

    messages = [
        SystemMessage(content=prompt.strip()),
        HumanMessage(content=(
            "Context:\n" + context +
            "\n\nReturn ONLY the JSON object. Do not include any keys not asked for. "
            "If a value is not clearly supported by the context, set it to null or []."
        )),
    ]
    resp = _llm(json_mode=True).invoke(messages).content
    try:
        return _try_parse_json(resp)
    except Exception:
        repair = messages + [HumanMessage(content="Respond again as STRICT JSON only. No prose.")]
        resp2 = _llm(json_mode=True).invoke(repair).content
        return _try_parse_json(resp2)
