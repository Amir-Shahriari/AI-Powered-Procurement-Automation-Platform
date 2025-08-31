# app/services/compose/base.py
from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from langchain.schema import SystemMessage, HumanMessage
from ..llm import _llm  # Gemini 1.5 primary, fallback to local Ollama via your wrapper

# -----------------------------
# JSON utils (hardened)
# -----------------------------

_CODE_FENCE_OPEN = re.compile(r"^\s*```(?:json)?", flags=re.IGNORECASE)
_CODE_FENCE_CLOSE = re.compile(r"```\s*$", flags=re.IGNORECASE)

def _clean_json_fences(s: str) -> str:
    """
    Strip surrounding triple-backtick fences if present.
    Leaves inner content untouched.
    """
    txt = s.strip()
    txt = _CODE_FENCE_OPEN.sub("", txt).strip()
    txt = _CODE_FENCE_CLOSE.sub("", txt).strip()
    return txt

def _extract_balanced_json_fragment(s: str) -> Optional[str]:
    """
    Find the first top-level balanced JSON object substring, ignoring braces inside strings.
    Returns the substring from the first '{' to its matching '}', or None.
    """
    if not s:
        return None
    start = None
    depth = 0
    in_str = False
    esc = False
    for i, ch in enumerate(s):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            continue
        if ch == "{":
            if start is None:
                start = i
            depth += 1
            continue
        if ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    return s[start : i + 1]
    return None

def _normalise_quotes(s: str) -> str:
    """
    Replace smart quotes with straight quotes to help JSON parsing.
    """
    return (
        s.replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
    )

def _try_parse_json(response: Any) -> Optional[Dict[str, Any]]:
    """
    Parse LLM output into JSON safely. Never raises.
    Returns a dict on success, or None on failure.
    """
    if response is None:
        return None

    # Already JSON-like
    if isinstance(response, dict):
        return response
    if isinstance(response, list):
        # Accept a list if its first element is a dict (common pattern)
        if response and isinstance(response[0], dict):
            return response[0]
        return None

    # Convert to string
    txt = str(response)
    if not txt.strip():
        return None

    # Remove surrounding code fences and normalise quotes
    txt1 = _clean_json_fences(txt)
    txt1 = _normalise_quotes(txt1)

    # Fast path parse
    try:
        parsed = json.loads(txt1)
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
            return parsed[0]
    except Exception:
        pass

    # Some models append prose before/after JSON. Try to extract the first balanced object.
    frag = _extract_balanced_json_fragment(txt1)
    if frag:
        try:
            parsed = json.loads(frag)
            if isinstance(parsed, dict):
                return parsed
            if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                return parsed[0]
        except Exception:
            pass

    # Final attempt: look for a trailing {...} or [...] block with a simple regex
    m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])\s*$", txt1.strip())
    if m:
        try:
            parsed = json.loads(m.group(1))
            if isinstance(parsed, dict):
                return parsed
            if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                return parsed[0]
        except Exception:
            pass

    # Give up
    return None

# -----------------------------
# Retrieval helpers
# -----------------------------

def _expand_query(q: str) -> List[str]:
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
    # dedup, keep order
    seen = set()
    out: List[str] = []
    for a in alts:
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out

def _dedup_strs(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for s in items:
        s_norm = re.sub(r"\s+", " ", (s or "").strip())
        if s_norm and s_norm not in seen:
            seen.add(s_norm)
            out.append(s_norm)
    return out

def _gather_snippets(similar_fn, queries: List[str], max_ctx: int, min_chars: int) -> List[str]:
    blocks: List[str] = []
    # pass 1
    for q in queries:
        for variant in _expand_query(q):
            try:
                blocks.extend(similar_fn(variant, k=max_ctx) or [])
            except Exception:
                pass
    blocks = _dedup_strs(blocks)

    # pass 2 if short
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

    # soft cap
    cap_chars = max(min_chars * 2, 12000)
    trimmed: List[str] = []
    running = 0
    for b in blocks:
        if running + len(b) > cap_chars:
            break
        trimmed.append(b)
        running += len(b)
    return trimmed

# -----------------------------
# RAG -> JSON (single VS)
# -----------------------------

def rag_json(
    vs,
    prompt: str,
    field_queries: List[str],
    max_ctx: int = 8,
    min_chars: int = 2500,
    allow_synthesis: bool = False,
) -> Dict[str, Any]:
    """
    Retrieve relevant context from a single vector store and ask the LLM for STRICT JSON.
    This function is resilient: it never raises on JSON errors; returns {} on failure.
    """
    def _similar(q: str, k: int = max_ctx) -> List[str]:
        try:
            docs = vs.similarity_search(q, k=k)
            return [d.page_content for d in docs]
        except Exception:
            return []

    blocks = _gather_snippets(_similar, field_queries, max_ctx=max_ctx, min_chars=min_chars)
    context = "NO_CONTEXT" if not blocks else "\n\n".join(f"[CTX {i}]\n{b}" for i, b in enumerate(blocks, 1))
    synth_line = (
        "If the context is insufficient, complete missing items using NSW/Australian standards and council best practice. Do not leave fields empty or null."
        if allow_synthesis else
        "If a value is not clearly supported by the context, set it to null or []."
    )
    messages = [
        SystemMessage(content=prompt.strip()),
        HumanMessage(content=f"Context:\n{context}\n\nReturn ONLY the JSON object. {synth_line}")
    ]

    # Attempt 1 (free-form)
    try:
        resp = _llm(json_mode=False).invoke(messages).content
    except Exception:
        resp = None
    obj = _try_parse_json(resp)
    if isinstance(obj, dict):
        return obj

    # Attempt 2 (strict)
    repair = messages + [HumanMessage(content="Respond again as STRICT JSON only. No prose. No code fences.")]
    try:
        resp2 = _llm(json_mode=True).invoke(repair).content
    except Exception:
        resp2 = None
    obj2 = _try_parse_json(resp2)
    if isinstance(obj2, dict):
        return obj2

    # Fallback
    return {}

# -----------------------------
# RAG -> JSON (multi VS)
# -----------------------------

def rag_json_plus(
    vs_primary,
    prompt: str,
    field_queries: List[str],
    extra_vss: Optional[List[Any]] = None,
    max_ctx: int = 8,
    min_chars: int = 2500,
    allow_synthesis: bool = False,
) -> Dict[str, Any]:
    """
    Retrieve relevant context from a primary vector store plus any extras, then ask the LLM.
    Resilient: returns {} on failure (never raises).
    """
    def _collect(vs, q, k) -> List[str]:
        try:
            docs = vs.similarity_search(q, k=k)
            return [d.page_content for d in docs]
        except Exception:
            return []

    blocks: List[str] = []
    for q in field_queries:
        for variant in _expand_query(q):
            blocks.extend(_collect(vs_primary, variant, k=max_ctx) or [])
            if extra_vss:
                for evs in extra_vss:
                    blocks.extend(_collect(evs, variant, k=max(3, max_ctx // 2)) or [])
    blocks = _dedup_strs(blocks)

    if sum(len(b) for b in blocks) < min_chars:
        for g in ["scope", "probity", "evaluation", "criteria", "testing", "warranty", "maintenance"]:
            blocks.extend(_collect(vs_primary, g, k=max(3, max_ctx // 2)) or [])
    blocks = _dedup_strs(blocks)

    # cap
    cap_chars = max(min_chars * 2, 12000)
    trimmed: List[str] = []
    running = 0
    for b in blocks:
        if running + len(b) > cap_chars:
            break
        trimmed.append(b)
        running += len(b)

    context = "NO_CONTEXT" if not trimmed else "\n\n".join(f"[CTX {i}]\n{b}" for i, b in enumerate(trimmed, 1))
    synth_line = (
        "If the context is insufficient, complete missing items using NSW/Australian standards and council best practice. Do not leave fields empty or null."
        if allow_synthesis else
        "If a value is not clearly supported by the context, set it to null or []."
    )
    messages = [
        SystemMessage(content=prompt.strip()),
        HumanMessage(content=f"Context:\n{context}\n\nReturn ONLY the JSON object. {synth_line}")
    ]

    # Attempt 1 (free-form)
    try:
        resp = _llm(json_mode=False).invoke(messages).content
    except Exception:
        resp = None
    obj = _try_parse_json(resp)
    if isinstance(obj, dict):
        return obj

    # Attempt 2 (strict)
    repair = messages + [HumanMessage(content="Respond again as STRICT JSON only. No prose. No code fences.")]
    try:
        resp2 = _llm(json_mode=True).invoke(repair).content
    except Exception:
        resp2 = None
    obj2 = _try_parse_json(resp2)
    if isinstance(obj2, dict):
        return obj2

    # Fallback
    return {}

# -----------------------------
# Misc shared helpers
# -----------------------------

def unique_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for it in items or []:
        key = re.sub(r"\s+", " ", (it or "").strip().lower())
        if key and key not in seen:
            seen.add(key)
            out.append((it or "").strip())
    return out
