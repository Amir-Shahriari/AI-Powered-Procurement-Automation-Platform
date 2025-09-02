# app/services/templates_catalog.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Folder layout:
# app/templates_catalog/<category>/{tepp.json, returnable_schedules.json, rft.json}
CATALOG_DIR = Path(__file__).resolve().parent.parent / "templates_catalog"
DOC_TYPES = {"tepp", "returnable_schedules", "rft"}
DEFAULT_CATEGORY = "generic"  # fallback if a category file is missing

def _read_json(p: Path) -> Dict[str, Any]:
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def list_categories(doc_type: Optional[str] = None) -> List[str]:
    """List available categories. If doc_type is given, only those with that file."""
    if not CATALOG_DIR.exists():
        return [DEFAULT_CATEGORY]
    cats: List[str] = []
    for cat_dir in CATALOG_DIR.iterdir():
        if not cat_dir.is_dir():
            continue
        if doc_type and doc_type in DOC_TYPES:
            if (cat_dir / f"{doc_type}.json").exists():
                cats.append(cat_dir.name)
        else:
            cats.append(cat_dir.name)
    # always ensure default exists in list, even if directory missing
    if DEFAULT_CATEGORY not in cats:
        cats.insert(0, DEFAULT_CATEGORY)
    return sorted(dict.fromkeys(cats))

def load_category_template(doc_type: str, category: str) -> Dict[str, Any]:
    """Load the template for a given doc type/category, falling back to generic."""
    if doc_type not in DOC_TYPES:
        raise ValueError(f"Unknown doc_type '{doc_type}'. Expected one of {sorted(DOC_TYPES)}")
    # 1) chosen category
    p = CATALOG_DIR / category / f"{doc_type}.json"
    if p.exists():
        return _read_json(p)
    # 2) generic fallback
    p = CATALOG_DIR / DEFAULT_CATEGORY / f"{doc_type}.json"
    if p.exists():
        return _read_json(p)
    # 3) empty fallback
    return {}

def deep_merge(template: Any, generated: Any) -> Any:
    """
    Merge two JSON-like structures:
      - dict: keys merged; generated overrides template when value is truthy/non-empty
      - list: if generated is non-empty, keep it; else use template
      - primitives: prefer generated if it is not None/empty, else template
    """
    # If generated is "truthy" primitive, take it
    if not isinstance(template, (dict, list)) and not isinstance(generated, (dict, list)):
        return generated if _is_meaningful(generated) else template

    # Dict merge
    if isinstance(template, dict) and isinstance(generated, dict):
        out: Dict[str, Any] = {}
        keys = set(template.keys()) | set(generated.keys())
        for k in keys:
            t_val = template.get(k)
            g_val = generated.get(k)
            if isinstance(t_val, dict) and isinstance(g_val, dict):
                out[k] = deep_merge(t_val, g_val)
            elif isinstance(t_val, list) and isinstance(g_val, list):
                out[k] = g_val if _has_meaningful_list(g_val) else t_val
            else:
                out[k] = g_val if _is_meaningful(g_val) else t_val
        return out

    # List policy: keep generated if it has content, else template
    if isinstance(template, list) and isinstance(generated, list):
        return generated if _has_meaningful_list(generated) else template

    # Fallbacks when shapes differ
    if _is_meaningful(generated):
        return generated
    return template

def _is_meaningful(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() != ""
    if isinstance(v, (list, tuple, set, dict)):
        return len(v) > 0
    return True

def _has_meaningful_list(v: List[Any]) -> bool:
    return any(_is_meaningful(x) for x in v)
