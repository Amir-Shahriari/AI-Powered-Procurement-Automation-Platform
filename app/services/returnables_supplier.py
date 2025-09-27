"""
Utilities for populating Returnable Schedule fields from supplier-submitted
documents.  This module provides a function that takes an existing returnable
schedule JSON document, scans all fields for empty values, and uses the
retrieval‑augmented generation (RAG) helper functions to extract answers
from supplier documents.  The goal is to automatically fill in as much
information as possible from the suppliers' responses while leaving any
fields untouched if no relevant information is found.

The high‑level workflow is:

1.  Accept a list of vector store instances (one for each uploaded supplier
    document).  Each vector store should already be built and contain
    embeddings for the supplier text.  The first vector store in the list
    will be treated as the primary search backend; additional stores are
    used as secondary context sources.
2.  Traverse the returnable schedule recursively to discover all leaf
    entries whose current value is considered "empty" (i.e. null, empty
    string, empty list, or empty dict).  We only attempt to fill
    primitives (strings, numbers, booleans) and lists of strings; nested
    objects are not populated automatically.
3.  For each empty field, build a human‑readable label based on its path
    (e.g. "schedule 2 financial capacity financial institution name").
    Compose a prompt instructing the language model to extract the answer
    for that specific field from the supplier responses.  The prompt
    explicitly asks for a JSON object with a single key "value" and
    instructs the model to return null when the answer cannot be found.
4.  Use ``rag_json_plus`` to perform retrieval over the supplier
    documents and ask the model for the value.  If the model returns
    something other than null/empty, update the corresponding field in
    the returnables JSON structure.

This module deliberately keeps the implementation generic.  Should you
require more sophisticated filling logic (e.g. handling nested tables or
interpreting yes/no questions), you can extend the ``_infer_type`` and
``_build_prompt`` helpers to provide more guidance to the model.
"""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Dict, Iterable, List, Tuple

from app.services.llm import rag_json_plus


def _is_empty(value: Any) -> bool:
    """Return True if the value should be considered empty."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    if isinstance(value, dict) and len(value) == 0:
        return True
    return False


def _flatten_paths(obj: Any, prefix: List[str] | None = None) -> Iterable[Tuple[List[str], Any]]:
    """
    Recursively walk ``obj`` and yield (path, value) tuples for every leaf.

    ``path`` is a list of keys describing the location within the nested
    dictionary.  For lists, the index is represented as a string in the
    path (e.g. ``["schedule_7_current_clients", "clients", "0"]``).
    """
    if prefix is None:
        prefix = []
    # Base case: primitive or empty container
    if not isinstance(obj, (dict, list)):
        yield (prefix, obj)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            yield from _flatten_paths(item, prefix + [str(idx)])
    else:  # dict
        for key, val in obj.items():
            yield from _flatten_paths(val, prefix + [key])


def _path_to_label(path: List[str]) -> str:
    """Convert a path of keys into a human‑readable label for prompting."""
    # Remove numeric indices – we don't include positions in labels
    parts = [p for p in path if not re.fullmatch(r"\d+", p)]
    # Replace underscores with spaces and capitalise words
    label_parts = []
    for p in parts:
        label = p.replace("_", " ").strip()
        # Normalise schedule prefixes (e.g. schedule_1 -> schedule 1)
        m = re.match(r"schedule (\d+)", label, flags=re.IGNORECASE)
        if m:
            # ensure schedule number has a dash if needed
            label_parts.append(f"schedule {m.group(1)}")
            # Append the remainder of the string after the schedule number
            remainder = label[len(m.group(0)):].strip()
            if remainder:
                label_parts.append(remainder)
        else:
            label_parts.append(label)
    return " ".join(label_parts)


def _infer_type(value: Any) -> str:
    """
    Infer a coarse type for a field based on the current value.  Used to
    customise the prompt and expected JSON schema.  Returns one of
    ``"string"``, ``"list"``, or ``"boolean"``.
    """
    if isinstance(value, list):
        return "list"
    if isinstance(value, bool):
        return "boolean"
    # Default to string for numbers and strings; numbers will be
    # coerced to strings by the prompt instructions.
    return "string"


def _build_prompt(field_label: str, field_type: str) -> str:
    """
    Construct a system prompt instructing the LLM how to extract the value
    for a specific returnable schedule field.  The prompt must instruct
    the model to only use the provided context and to return a strict JSON
    object with a single key ``"value"``.
    """
    base = (
        f"You are assisting with populating a tender Returnable Schedule from supplier responses.\n"
        f"The buyer provided an empty template, and the supplier has submitted documents in response.\n"
        f"Your task is to extract the answer for the field named '{field_label}'.\n"
        f"Only use the information from the supplied context; if you cannot find a clear answer, return null."
    )
    # Describe the expected type to help the model format correctly
    if field_type == "list":
        base += (
            "\nReturn a JSON object with a single key `value` whose value is an array of strings."
            " If multiple pieces of information correspond to the field, include them all in the array."
            " If none are found, use an empty array."
        )
    elif field_type == "boolean":
        base += (
            "\nReturn a JSON object with a single key `value` whose value is either true or false."
            " Infer true/false based on whether the supplier documents explicitly indicate affirmative or negative for this field."
            " If uncertain or absent, return null."
        )
    else:
        base += (
            "\nReturn a JSON object with a single key `value` whose value is a string."
            " If the answer is numeric, return it as a string."
            " If no answer is found, set value to null."
        )
    return base


def fill_returnables_from_supplier(
    returnables: Dict[str, Any],
    supplier_vss: List[Any],
    max_ctx: int = 6,
    min_chars: int = 1500,
) -> Dict[str, Any]:
    """
    Populate empty fields in a Returnable Schedules JSON document based on
    supplier responses contained in one or more vector stores.

    Args:
        returnables: The current returnable schedules JSON structure (will
            not be mutated).
        supplier_vss: A list of vector store objects corresponding to the
            supplier documents.  The first element is treated as the
            primary store; subsequent stores are used as additional
            context sources.
        max_ctx: Maximum number of context chunks to retrieve per field.
        min_chars: Minimum total characters of retrieved context across
            all queries.  The retrieval helper may broaden the search if
            fewer than this many characters are gathered.

    Returns:
        A new returnables dictionary with empty fields filled where
        possible.  Fields for which no answer was found remain unchanged.
    """
    if not supplier_vss:
        # No supplier documents – return unchanged
        return deepcopy(returnables)
    primary_vs = supplier_vss[0]
    extra_vss = supplier_vss[1:] if len(supplier_vss) > 1 else None
    result = deepcopy(returnables)
    # Find all empty leaf nodes
    for path, value in _flatten_paths(returnables):
        if not _is_empty(value):
            continue
        # Determine human‑readable field label
        label = _path_to_label(path)
        field_type = _infer_type(value)
        prompt = _build_prompt(label, field_type)
        # Use the label as query; synonyms handled internally by rag_json_plus
        try:
            response = rag_json_plus(
                primary_vs,
                prompt,
                field_queries=[label],
                extra_vss=extra_vss,
                max_ctx=max_ctx,
                min_chars=min_chars,
            )
        except Exception:
            continue
        if not isinstance(response, dict):
            continue
        extracted = response.get("value")
        if extracted in (None, "", [], {}):
            continue
        # Walk the result structure to set the value
        cur = result
        for part in path[:-1]:
            # For numeric indices, convert to int and traverse list
            if re.fullmatch(r"\d+", part):
                idx = int(part)
                cur = cur[idx]
            else:
                cur = cur.setdefault(part, {})
        leaf = path[-1]
        if re.fullmatch(r"\d+", leaf):
            idx = int(leaf)
            # Extend list if necessary
            if not isinstance(cur, list):
                continue
            while len(cur) <= idx:
                cur.append(None)
            cur[idx] = extracted
        else:
            cur[leaf] = extracted
    return result
