# app/services/compose/evaluation.py
from __future__ import annotations
import io
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter

from ..config import settings
from app.services.textio import extract_text
from app.services.supplier import list_suppliers, _data_dir as _supplier_data_dir

# =============================
# Supplier files discovery/IO
# =============================
def _supplier_store() -> Path:
    try:
        return _supplier_data_dir()
    except Exception:
        return settings.DATA_DIR

def _supplier_json_paths(rec_id: str) -> List[Path]:
    root = _supplier_store()
    return sorted(Path(root).glob(f"{rec_id}_supplier_*.returnables.json"))

def _supplier_raw_paths(rec_id: str) -> List[Path]:
    root = _supplier_store()
    pats: List[Path] = []
    for ext in ("pdf", "docx", "doc", "txt"):
        pats += list(Path(root).glob(f"{rec_id}_supplier_*.{ext}"))
    return sorted(pats)

def _read_text_from_file(path: Path) -> str:
    try:
        return extract_text(path)
    except Exception:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

# =============================
# JSON/text flattening helpers
# =============================
def _deep_iter_kv(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            newp = f"{path}.{k}" if path else str(k)
            yield from _deep_iter_kv(v, newp)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            newp = f"{path}[{i}]"
            yield from _deep_iter_kv(v, newp)
    else:
        yield path, None, obj

def _flatten_texts(obj) -> List[str]:
    if isinstance(obj, str):
        return [obj]
    out: List[str] = []
    for _, _, v in _deep_iter_kv(obj):
        if isinstance(v, (str, int, float, bool)):
            out.append(str(v))
    return out

# =============================
# Scorers & extractors
# =============================
_PRICE_KEY_HINTS = {"total_price", "price_total", "tender_price", "sum", "subtotal", "total", "amount", "lump_sum"}
_PRICE_CTX_HINTS = {"price", "cost", "offer", "tender", "gst", "ex gst", "incl gst", "exc gst", "exclusive", "inclusive", "net", "gross", "fee"}

def extract_price_any(payload_or_text: Any) -> Optional[float]:
    """Find a plausible 'total price' from a supplier returnables JSON or raw text."""
    def _coerce_num(x):
        try:
            s = str(x)
            s = re.sub(r"[^\d.,()-]", "", s)
            s = s.replace(",", "")
            m = re.search(r"-?\(?\d+(?:\.\d+)?\)?", s)
            if not m:
                return None
            num = m.group(0)
            neg = "(" in s and ")" in s
            val = float(num.replace("(", "").replace(")", ""))
            return -val if neg else val
        except Exception:
            return None

    found: List[float] = []
    if isinstance(payload_or_text, dict):
        for k, v in payload_or_text.items():
            lk = str(k).lower().strip()
            if lk in _PRICE_KEY_HINTS or any(h in lk for h in _PRICE_CTX_HINTS):
                num = _coerce_num(v)
                if isinstance(num, (int, float)) and num != 0:
                    found.append(float(num))

    texts = " ".join(_flatten_texts(payload_or_text)) if not isinstance(payload_or_text, str) else payload_or_text
    texts_l = texts.lower()

    if not found and texts_l:
        cand = re.findall(r"(?:\$|aud\$?)?\s*([1-9]\d{2,}(?:\.\d{2})?)", texts_l)
        nums: List[float] = []
        for c in cand:
            try:
                n = float(c.replace(",", ""))
                if n > 0:
                    nums.append(n)
            except Exception:
                pass
        if nums:
            nums.sort()
            found = [nums[-1]]  # assume largest is the 'total'

    return max(found) if found else None

def presence_score(text_or_json: Any, keywords: List[str]) -> float:
    texts = " ".join(_flatten_texts(text_or_json)).lower() if not isinstance(text_or_json, str) else text_or_json.lower()
    if not keywords:
        return 0.0
    hits = sum(1 for kw in keywords if re.search(rf"\b{re.escape(kw.lower())}\b", texts))
    return min(100.0, 100.0 * hits / len(keywords))

def coverage_score(text_or_json: Any, sections: List[str]) -> float:
    texts = " ".join(_flatten_texts(text_or_json)).lower() if not isinstance(text_or_json, str) else text_or_json.lower()
    if not sections:
        return 0.0
    c = Counter()
    for s in sections:
        c[s] = len(re.findall(rf"\b{re.escape(s.lower())}\b", texts))
    present = sum(1 for s in sections if c[s] > 0)
    presence_part = 100.0 * present / len(sections)
    freq_part = min(100.0, 10.0 * sum(min(5, c[s]) for s in sections))  # cap
    return 0.5 * presence_part + 0.5 * min(100.0, freq_part)

_BASE_SCORERS = {
    "relevant experience": lambda j: coverage_score(j, ["experience", "project", "reference", "referee", "past performance"]),
    "capability": lambda j: coverage_score(j, ["capability", "resources", "equipment", "methodology", "approach", "schedule"]),
    "management & financial capacity": lambda j: coverage_score(j, ["financial", "capacity", "org chart", "insurance", "licence", "license", "policy"]),
    "quality management": lambda j: presence_score(j, ["quality", "qa", "qc", "iso 9001", "quality management"]),
    "whs": lambda j: presence_score(j, ["whs", "ohs", "safety", "swms", "incident", "risk", "hazard"]),
    "sustainability and eeo & fair employment": lambda j: presence_score(j, ["sustainability", "environment", "eeo", "diversity", "modern slavery", "recycled", "carbon"]),
}

def _get_criterion_scorer(crit_name: str):
    key = (crit_name or "").strip().lower()
    if key in _BASE_SCORERS:
        return _BASE_SCORERS[key]
    tokens = [t for t in re.split(r"[^a-zA-Z0-9]+", key) if t and t not in {"and", "the", "of", "for", "to"}]
    if not tokens:
        tokens = [key] if key else ["criterion"]
    return lambda j: presence_score(j, tokens)

def schema_terms_from_returnables(base_returnables: Dict[str, Any]) -> List[str]:
    """Harvest labels from your baseline returnables to anchor scoring."""
    terms: List[str] = []
    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                label = str(k).strip()
                if 3 <= len(label) <= 48:
                    terms.append(label)
                walk(v)
        elif isinstance(x, list):
            for i in x:
                walk(i)
        elif isinstance(x, str):
            s = x.strip()
            if 3 <= len(s) <= 60 and len(s.split()) <= 8:
                terms.append(s)
    walk(base_returnables or {})
    seen = set()
    out: List[str] = []
    for t in terms:
        lt = t.lower()
        if lt not in seen:
            seen.add(lt)
            out.append(lt)
    return out[:300]

def compute_price_scores(price_map: Dict[str, Optional[float]]) -> Dict[str, float]:
    vals = [v for v in price_map.values() if isinstance(v, (int, float)) and v > 0]
    if not vals:
        return {k: 0.0 for k in price_map}
    pmin = min(vals)
    return {k: (pmin / v * 100.0) if (v and v > 0) else 0.0 for k, v in price_map.items()}

# =============================
# TEPP weights loaders (robust)
# =============================
_NUM = re.compile(r"(-?\d+(?:\.\d+)?)")

def _as_float_pct(v: Any) -> Optional[float]:
    """Accept '40', '40%', 40, 40.0 → return 40.0. Return None if not numeric."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = _NUM.search(str(v))
    return float(m.group(1)) if m else None

def _read_tepp_dict(rec_id_or_path: str | Path) -> Dict:
    """Accept a record id like 'UntMKL' or a full path to a tepp.json file."""
    p = Path(rec_id_or_path)
    if p.suffix.lower() == ".json":
        tepp_path = p
    else:
        tepp_path = settings.DATA_DIR / f"{str(rec_id_or_path).strip()}.tepp.json"
    return json.loads(tepp_path.read_text(encoding="utf-8"))

def _dig(d: Dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return cur if cur is not None else default

def _extract_weights_from_tepp(tepp: Dict) -> Dict[str, float]:
    """
    Understands both shapes:
    1) Table of rows:
       tepp["tender_evaluation"]["evaluation_methodology"]["required_criteria_table"] -> list of {criterion, weight}
       or a dict with a "rows" list inside.
    2) Plain dict:
       tepp["weights"] or tepp["evaluation_weights"] -> {criterion: number or '40%'}
    """
    # Modern path (may be list of rows or an object with "rows")
    rows = _dig(tepp, "tender_evaluation", "evaluation_methodology", "required_criteria_table", default=None)
    if isinstance(rows, dict) and isinstance(rows.get("rows"), list):
        rows = rows["rows"]

    # Legacy location
    if not isinstance(rows, list):
        rows = _dig(tepp, "evaluation_methodology", "required_criteria_table", default=None)
        if isinstance(rows, dict) and isinstance(rows.get("rows"), list):
            rows = rows["rows"]

    weights: Dict[str, float] = {}
    if isinstance(rows, list):
        for r in rows:
            if not isinstance(r, dict):
                continue
            crit = (r.get("criterion") or r.get("criteria") or "").strip()
            w = _as_float_pct(r.get("weight"))
            if crit and w is not None:
                weights[crit] = float(w)

    # Plain-dict fallback
    if not weights:
        maybe = _dig(tepp, "weights") or _dig(tepp, "evaluation_weights")
        if isinstance(maybe, dict):
            out: Dict[str, float] = {}
            for k, v in maybe.items():
                fv = _as_float_pct(v)
                if fv is not None:
                    out[str(k)] = fv
            if out:
                return out

    return weights

def _load_tepp_weights(rec_id_or_path: str | Path) -> Tuple[Dict[str, float], Dict]:
    """
    Public loader used by Streamlit page.
    Returns (weights_dict, tepp_json).
    """
    tepp = _read_tepp_dict(rec_id_or_path)
    weights = _extract_weights_from_tepp(tepp)
    return (weights, tepp)

# Convenience for callers that only want the dict (e.g., Excel export path)
def _load_weights_from_tepp(rec_id_or_path: str | Path) -> Dict[str, float]:
    w, _ = _load_tepp_weights(rec_id_or_path)
    return w

# (Kept for compatibility with older code that already has the tepp dict in-hand)
def load_tepp_weights(tepp: dict) -> Dict[str, float]:
    return _extract_weights_from_tepp(tepp)

# =============================
# Supplier payload ingestion
# =============================
def load_or_parse_supplier_payloads(rec_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Returns {supplier_id: {"json": dict|None, "text": str|None, "name": str|None}}
    Looks for JSON first; if missing, falls back to raw doc text.
    """
    out: Dict[str, Dict[str, Any]] = {}
    for jpath in _supplier_json_paths(rec_id):
        sid = jpath.stem.split("_supplier_")[-1].replace(".returnables","")
        try:
            payload = json.loads(jpath.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        out[sid] = {"json": payload, "text": " ".join(_flatten_texts(payload))[:1_000_000], "name": sid}

    for rpath in _supplier_raw_paths(rec_id):
        sid = rpath.stem.split("_supplier_")[-1]
        if sid not in out or not out[sid].get("json"):
            text = _read_text_from_file(rpath)
            entry = out.setdefault(sid, {"json": None, "text": None, "name": sid})
            entry["text"] = text

    try:
        manifest = list_suppliers(rec_id) or []
        m = {row.get("id"): row.get("name") for row in manifest if row.get("id")}
        for sid, e in out.items():
            if sid in m and m[sid]:
                e["name"] = m[sid]
    except Exception:
        pass
    return out

# =============================
# Blended scoring
# =============================
def blend_schema_aware_score(payload_or_text: Any, crit: str, schema_terms: List[str], alpha: float = 0.7) -> float:
    """
    raw = alpha * base_criterion_score + (1-alpha) * coverage_on_schema_terms
    """
    base_fn = _get_criterion_scorer(crit)
    base = float(base_fn(payload_or_text))
    coverage = coverage_score(payload_or_text, schema_terms) if schema_terms else 0.0
    return round(alpha * base + (1.0 - alpha) * coverage, 2)
