# app/services/templates.py
from __future__ import annotations
import json
from pathlib import Path

TEMPLATES_DIR = Path("app/templates")  # same folder you already use
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)

def _read_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

# Existing
def load_returnables_template() -> dict:
    return _read_json(TEMPLATES_DIR / "returnables_template.json")

# NEW
def load_rft_template() -> dict:
    return _read_json(TEMPLATES_DIR / "rft_template.json")

def load_tepp_template() -> dict:
    return _read_json(TEMPLATES_DIR / "tepp_template.json")
