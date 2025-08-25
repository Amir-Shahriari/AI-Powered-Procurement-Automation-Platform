# app/services/fill_utils.py
from __future__ import annotations
import json
from typing import Any, Dict

def deepcopy_json(obj: Dict[str, Any]) -> Dict[str, Any]:
    # safe deep copy for nested dict/list
    return json.loads(json.dumps(obj))

def set_if_exists(container: Dict[str, Any], key: str, value):
    if isinstance(container, dict) and key in container:
        container[key] = value
