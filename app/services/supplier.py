# app/services/supplier.py
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Iterable

from fastapi import UploadFile

from ..config import settings
from .textio import extract_text, chunks
from .vectorstores import build_index, get_vs, _faiss_path, _chroma_name
from .returnables_supplier import fill_returnables_from_supplier

# Excel generation
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side


# =============================================================================
# Paths & IO helpers
# =============================================================================

def _data_dir() -> Path:
    return settings.DATA_DIR

def _path_record_returnables(rec_id: str) -> Path:
    return _data_dir() / f"{rec_id}.returnables.json"

def _path_record_tepp(rec_id: str) -> Path:
    return _data_dir() / f"{rec_id}.tepp.json"

def _path_suppliers_manifest(rec_id: str) -> Path:
    return _data_dir() / f"{rec_id}.suppliers.json"

def _path_supplier_returnables(rec_id: str, sup_id: str) -> Path:
    return _data_dir() / f"{rec_id}_{sup_id}.returnables.json"

def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


# =============================================================================
# Supplier manifest management
# =============================================================================

def _load_suppliers(rec_id: str) -> List[Dict[str, Any]]:
    path = _path_suppliers_manifest(rec_id)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

def _save_suppliers(rec_id: str, items: List[Dict[str, Any]]) -> None:
    _path_suppliers_manifest(rec_id).write_text(json.dumps(items, indent=2), encoding="utf-8")

def list_suppliers(rec_id: str) -> List[Dict[str, Any]]:
    """
    Public: return the suppliers manifest (id, name, filename, uploaded_at, paths).
    If the manifest is empty/missing, try an on-disk rebuild so the UI doesn’t look empty.
    """
    items = _load_suppliers(rec_id)
    if not items:
        items = _rebuild_suppliers_manifest_from_disk(rec_id)
        if items:
            _save_suppliers(rec_id, items)
    return items


# =============================================================================
# Name extraction from Returnables
# =============================================================================

def _first_nonempty(*vals) -> Optional[str]:
    for v in vals:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None

def _get_nested(d: Dict[str, Any], path: List[str]) -> Any:
    cur = d
    for p in path:
        if isinstance(cur, dict):
            cur = cur.get(p)
        else:
            return None
    return cur

def _supplier_display_name(ret: Dict[str, Any], fallback: str) -> str:
    """
    Try common spots in your Returnables JSON to get the supplier name.
    Falls back to provided label (e.g., filename stem).
    """
    legal = _get_nested(ret, ["schedule_1_corporate_information_and_declaration", "company_details", "legal_name"])
    trading = _get_nested(ret, ["schedule_1_corporate_information_and_declaration", "company_details", "trading_name"])
    tenderer = _get_nested(ret, ["schedule_16_acknowledgement_of_addenda_and_declaration", "tenderer_declaration", "tenderer_name"])
    contact_name = _get_nested(ret, ["schedule_1_corporate_information_and_declaration", "contact_details", "name"])
    return _first_nonempty(legal, trading, tenderer, contact_name, fallback) or fallback


# =============================================================================
# Public accessors for per-supplier Returnables
# =============================================================================

def get_supplier_returnables(rec_id: str, sup_id: str) -> Dict[str, Any]:
    path = _path_supplier_returnables(rec_id, sup_id)
    if not path.exists():
        raise FileNotFoundError(f"Supplier returnables not found: {sup_id}")
    return _read_json(path)

def save_supplier_returnables(rec_id: str, sup_id: str, payload: Dict[str, Any]) -> None:
    _write_json(_path_supplier_returnables(rec_id, sup_id), payload)
    # Optional: refresh supplier name in manifest in case user edited Schedule 1
    try:
        manifest = _load_suppliers(rec_id)
        for s in manifest:
            if s.get("id") == sup_id:
                s["name"] = _supplier_display_name(payload, s.get("name") or s.get("filename") or sup_id)
                break
        _save_suppliers(rec_id, manifest)
    except Exception:
        pass


# =============================================================================
# Supplier processing (fill returnables from uploaded files)
# =============================================================================

def process_suppliers(rec_id: str, files: List[UploadFile], base_returnables: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    For each uploaded supplier file:
      - extract text
      - build vector store
      - fill a deep copy of baseline Returnables using supplier docs
      - write supplier-specific Returnables JSON
      - append to {rec_id}.suppliers.json manifest
    Returns the updated manifest list.
    """
    if not files:
        # Give the caller whatever we can rediscover, so subsequent evaluation works.
        items = _load_suppliers(rec_id)
        if not items:
            items = _rebuild_suppliers_manifest_from_disk(rec_id)
            if items:
                _save_suppliers(rec_id, items)
        return items

    manifest = _load_suppliers(rec_id)

    for up in files:
        if not up or not up.filename:
            continue

        sup_id = str(uuid.uuid4())[:8]
        suffix = Path(up.filename).suffix or ".bin"
        raw_path = _data_dir() / f"{rec_id}_supplier_{sup_id}{suffix}"

        # Persist raw file
        with open(raw_path, "wb") as f:
            f.write(up.file.read())

        # Extract text & build VS
        text = ""
        try:
            text = extract_text(raw_path)
        except Exception:
            text = ""

        if not text.strip():
            # record a stub supplier so user can fix manually
            filled = json.loads(json.dumps(base_returnables))  # deep clone
            supplier_name = Path(up.filename).stem
            vs_loc = None
        else:
            chs = chunks(text)
            build_index(f"{rec_id}_supplier_{sup_id}", chs)
            vs = get_vs(f"{rec_id}_supplier_{sup_id}")

            # Fill using supplier docs
            filled = fill_returnables_from_supplier(base_returnables, [vs])
            supplier_name = _supplier_display_name(filled, Path(up.filename).stem)

            # Vector store location (optional)
            vs_loc = (
                str(_faiss_path(f"{rec_id}_supplier_{sup_id}"))
                if settings.VECTOR_BACKEND == "faiss_gpu"
                else _chroma_name(f"{rec_id}_supplier_{sup_id}")
            )

        # Save supplier-specific returnables
        out_path = _path_supplier_returnables(rec_id, sup_id)
        _write_json(out_path, filled)

        manifest.append({
            "id": sup_id,
            "name": supplier_name,
            "filename": up.filename,
            "uploaded_at": datetime.utcnow().isoformat(),
            "returnables_path": str(out_path),
            "raw_path": str(raw_path),
            "vs_backend": settings.VECTOR_BACKEND,
            "vs_location": vs_loc,
        })

    _save_suppliers(rec_id, manifest)
    return manifest


# =============================================================================
# Auto-discovery / manifest rebuild (robust)
# =============================================================================

_DISCOVERY_PATTERNS = (
    # Common/expected:
    "{rec_id}_*.returnables.json",
    # Alternate some projects emit:
    "{rec_id}_supplier_*.returnables.json",
)

def _iter_candidate_returnables(rec_id: str) -> Iterable[Path]:
    """
    Yield all returnables JSON paths under DATA_DIR for this record id,
    searching recursively and trying multiple naming patterns.
    """
    root = _data_dir()
    for pat in _DISCOVERY_PATTERNS:
        for p in root.rglob(pat.format(rec_id=rec_id)):
            # Ensure it's a file (not directory) and ends with the expected suffix
            if p.is_file() and p.name.endswith(".returnables.json"):
                yield p

_SUP_ID_REGEXES = (
    # <rec_id>_<supid>.returnables.json
    lambda rec_id: re.compile(rf"^{re.escape(rec_id)}_([^/\\]+?)\.returnables\.json$", re.IGNORECASE),
    # <rec_id>_supplier_<supid>.returnables.json
    lambda rec_id: re.compile(rf"^{re.escape(rec_id)}_supplier_([^/\\]+?)\.returnables\.json$", re.IGNORECASE),
)

def _extract_sup_id_from_name(rec_id: str, filename: str) -> Optional[str]:
    for rx in _SUP_ID_REGEXES:
        m = rx(rec_id).match(filename)
        if m:
            return m.group(1)
    # Fallback: last token before .returnables.json
    stem = filename.replace(".returnables.json", "")
    parts = stem.split("_")
    if len(parts) >= 2:
        return parts[-1]
    return None

def _rebuild_suppliers_manifest_from_disk(rec_id: str) -> List[Dict[str, Any]]:
    """
    Rebuild suppliers manifest by scanning the data dir (recursively) for any
    returnables belonging to this record id, inferring supplier id and name.
    """
    rebuilt: List[Dict[str, Any]] = []
    for ret_path in _iter_candidate_returnables(rec_id):
        sup_id = _extract_sup_id_from_name(rec_id, ret_path.name)
        if not sup_id:
            continue
        try:
            ret = _read_json(ret_path)
        except Exception:
            ret = {}
        name = _supplier_display_name(ret, sup_id)

        # Try to guess raw and VS paths (best effort)
        guessed_raw = None
        # Consider both <rec_id>_<supid>.* and <rec_id>_supplier_<supid>.*
        for raw in _data_dir().rglob(f"{rec_id}_supplier_{sup_id}.*"):
            guessed_raw = str(raw)
            break
        if not guessed_raw:
            for raw in _data_dir().rglob(f"{rec_id}_{sup_id}.*"):
                if raw.suffix.lower() not in (".json",):
                    guessed_raw = str(raw)
                    break

        if settings.VECTOR_BACKEND == "faiss_gpu":
            vs_loc = str(_faiss_path(f"{rec_id}_supplier_{sup_id}"))
        else:
            # For Chroma, collection name only (best effort)
            vs_loc = _chroma_name(f"{rec_id}_supplier_{sup_id}")

        rebuilt.append({
            "id": sup_id,
            "name": name,
            "filename": None,
            "uploaded_at": None,
            "returnables_path": str(ret_path),
            "raw_path": guessed_raw,
            "vs_backend": settings.VECTOR_BACKEND,
            "vs_location": vs_loc,
        })

    # Stable ordering for deterministic workbooks
    rebuilt.sort(key=lambda x: (x.get("name") or "").lower() or (x.get("id") or ""))
    return rebuilt


# =============================================================================
# Evaluation workbook
# =============================================================================

def _load_weights_from_tepp(rec_id: str) -> List[Tuple[str, float, str]]:
    """
    Returns list of (criterion, weight_percent, rationale) from TEPP JSON.
    If not found, returns a basic default.
    """
    path = _path_record_tepp(rec_id)
    if not path.exists():
        return [
            ("Price (Full Cost)", 40.0, ""),
            ("Relevant Experience", 20.0, ""),
            ("Capability", 20.0, ""),
            ("Management & Financial Capacity", 10.0, ""),
            ("WHS", 10.0, ""),
        ]
    try:
        tepp = _read_json(path)
        rows = tepp.get("tender_evaluation", {}) \
                   .get("evaluation_methodology", {}) \
                   .get("required_criteria_table", []) or []
        out: List[Tuple[str, float, str]] = []
        for r in rows:
            crit = (r.get("criterion") or "").strip()
            wtxt = (r.get("weight") or "").strip()
            rationale = r.get("rationale") or ""
            m = re.search(r"(-?\d+(?:\.\d+)?)", wtxt)
            if crit and m:
                out.append((crit, float(m.group(1)), rationale))
        if out:
            return out
    except Exception:
        pass
    # fallback
    return [
        ("Price (Full Cost)", 40.0, ""),
        ("Relevant Experience", 20.0, ""),
        ("Capability", 20.0, ""),
        ("Management & Financial Capacity", 10.0, ""),
        ("WHS", 10.0, ""),
    ]

def _parse_money(s: Any) -> Optional[float]:
    """Parse '12,345.67', '$12,345', '12345' into float. Returns None if not parseable."""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    txt = str(s).strip()
    if not txt:
        return None
    # Keep digits, dot, comma, minus
    cleaned = re.sub(r"[^\d,.\-]", "", txt)
    # If both comma and dot appear, assume comma=thousands, dot=decimal
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")
    else:
        # If only comma appears, treat it as thousands
        cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except Exception:
        return None

def _total_incl_gst_from_returnables(ret: Dict[str, Any]) -> Optional[float]:
    """
    Try to read Schedule 10 'pricing_totals.total_incl_gst'.
    If missing, attempt to sum 'pricing_schedule_ahu_refurbishments' incl_gst.
    """
    tot = ret.get("schedule_10_fee_structure", {}).get("pricing_totals", {}).get("total_incl_gst")
    v = _parse_money(tot)
    if v is not None:
        return v
    # Try sum of line items
    rows = ret.get("schedule_10_fee_structure", {}).get("pricing_schedule_ahu_refurbishments", []) or []
    acc = 0.0
    any_val = False
    for r in rows:
        val = _parse_money(r.get("price_incl_gst"))
        if val is not None:
            any_val = True
            acc += val
    return acc if any_val else None


def _style_header(ws, row=1):
    fill = PatternFill("solid", fgColor="1f2937")
    white = Font(color="FFFFFF", bold=True)
    for cell in ws[row]:
        cell.font = white
        cell.fill = fill
        cell.alignment = Alignment(vertical="center")
    thin = Side(style="thin", color="374151")
    for cell in ws[row]:
        cell.border = Border(top=thin, bottom=thin, left=thin, right=thin)

def _autosize(ws):
    widths: Dict[int, float] = {}
    for row in ws.iter_rows():
        for cell in row:
            if cell.value is None:
                continue
            val = str(cell.value)
            widths[cell.column] = max(widths.get(cell.column, 10.0), len(val) + 2.0)
    for col, w in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = min(w, 48)

def _safe_name(name: str) -> str:
    return re.sub(r"[\[\]*/\\?:]", "_", name)[:28] or "Supplier"

def _build_price_sheet(wb: Workbook, suppliers: List[Dict[str, Any]], price_weight: float):
    ws = wb.create_sheet("Price")
    headers = ["Supplier", "Pc (Total $)", "Ps", "Pn", "Price Weight (%)", "Pw (Weighted)"]
    ws.append(headers)
    _style_header(ws, 1)

    # Data rows
    for s in suppliers:
        ws.append([s["name"], s.get("pc") or None, None, None, price_weight, None])

    n = len(suppliers)
    # Average Pc range
    if n > 0:
        pc_range = f"B2:B{n+1}"
        for i in range(2, n + 2):
            # Ps = 200 – (Pc / Pav × 100) ; Pav = AVERAGE(Pc)
            ws[f"C{i}"] = f"=200 - (B{i} / AVERAGE({pc_range}) * 100)"
            # Pn = Ps / 200
            ws[f"D{i}"] = f"=C{i} / 200"
            # Pw = Pn × Price weight
            ws[f"F{i}"] = f"=D{i} * E{i}"

    _autosize(ws)
    return ws

def _build_weights_sheet(wb: Workbook, weights: List[Tuple[str, float, str]]):
    ws = wb.create_sheet("Weights")
    ws.append(["Criterion", "Weight (%)", "Rationale"])
    _style_header(ws, 1)
    for crit, w, rationale in weights:
        ws.append([crit, w, rationale or ""])
    _autosize(ws)
    return ws

def _build_scores_sheet(wb: Workbook,
                        suppliers: List[Dict[str, Any]],
                        nonprice_weights: List[Tuple[str, float]],
                        price_sheet_name: str):
    """
    Build "Scores" sheet with:
      - row 1: headers
      - row 2: weights
      - rows 3..: supplier ratings input (0..5) for non-price, Price Pw linked from 'Price'
      - Total and Rank columns
    """
    ws = wb.create_sheet("Scores")
    headers = ["Supplier"] + [c for c, _ in nonprice_weights] + ["Price (Weighted)", "Total (%)", "Rank"]
    ws.append(headers)
    _style_header(ws, 1)

    # Weights row
    weight_row = ["Weight (%)"] + [w for _, w in nonprice_weights] + [None, None, None]
    ws.append(weight_row)

    # Supplier rows
    for idx, s in enumerate(suppliers, start=3):
        row = [s["name"]]
        # Placeholder input cells for non-price ratings (0..5)
        row += [None for _ in nonprice_weights]
        # Link to Price!F{?}
        price_row = idx - 1  # Price sheet data starts at row 2
        row += [f"='{price_sheet_name}'!F{price_row}"]
        row += [None, None]  # Total, Rank (filled after append)
        ws.append(row)

    # Formulas for totals and rank
    n = len(suppliers)
    np_count = len(nonprice_weights)
    if n > 0:
        for r in range(3, n + 3):
            # Sum of (rating/5 * weight) across non-price cols
            contribs = []
            for j in range(np_count):
                rating_col = get_column_letter(2 + j)  # B .. (B + np_count - 1)
                weight_cell = f"{get_column_letter(2 + j)}2"  # weight row 2
                contribs.append(f"IFERROR(({rating_col}{r}/5)*{weight_cell},0)")
            nonprice_sum = "+".join(contribs) if contribs else "0"
            price_w_col = get_column_letter(2 + np_count)  # right after non-price
            total_col = get_column_letter(3 + np_count)    # Total column
            rank_col = get_column_letter(4 + np_count)     # Rank column

            ws[f"{total_col}{r}"] = f"=ROUND({nonprice_sum} + {price_w_col}{r}, 2)"
        # Rank (descending)
        total_col = get_column_letter(3 + np_count)
        total_range = f"${total_col}$3:${total_col}${n+2}"
        for r in range(3, n + 3):
            ws[f"{get_column_letter(4 + np_count)}{r}"] = f"=RANK({total_col}{r}, {total_range}, 0)"

    # Format bits
    for c in range(2, 2 + np_count):
        ws[f"{get_column_letter(c)}2"].number_format = "0.0"
    for r in range(3, n + 3):
        ws[f"{get_column_letter(2 + np_count)}{r}"].number_format = "0.0"  # Price weighted
        ws[f"{get_column_letter(3 + np_count)}{r}"].number_format = "0.00"  # Total
    _autosize(ws)
    return ws


def _create_evaluation_workbook(rec_id: str,
                                supplier_records: List[Dict[str, Any]],
                                weights: List[Tuple[str, float, str]]) -> Path:
    """
    Build an Excel workbook with three sheets: Weights, Price, Scores.
    Returns output file path.
    """
    # Partition weights
    price_weight = 0.0
    nonprice: List[Tuple[str, float]] = []
    for crit, w, _ in weights:
        if crit.lower().startswith("price"):
            price_weight = w
        else:
            nonprice.append((crit, w))

    # Suppliers enriched with Pc (price total)
    enriched: List[Dict[str, Any]] = []
    for s in supplier_records:
        ret = _read_json(Path(s["returnables_path"]))
        pc = _total_incl_gst_from_returnables(ret)
        enriched.append({"id": s["id"], "name": s["name"], "pc": pc})

    wb = Workbook()
    # Default sheet "Sheet" will be replaced by Weights
    wb.remove(wb.active)

    ws_w = _build_weights_sheet(wb, weights)
    ws_p = _build_price_sheet(wb, enriched, price_weight)
    ws_s = _build_scores_sheet(wb, enriched, nonprice, ws_p.title)

    # Make Scores the first sheet
    wb._sheets = [ws_s, ws_p, ws_w]

    out_path = _data_dir() / f"{rec_id}_evaluation.xlsx"
    wb.save(out_path)
    return out_path


def generate_evaluation_for_suppliers(rec_id: str, supplier_ids: Optional[List[str]] = None) -> Path:
    """
    Create a multi-supplier evaluation workbook.
    - If supplier_ids is None, include all suppliers in the manifest.
    - Uses TEPP weights when available.
    - If manifest is empty/missing, auto-discover suppliers from disk (recursively).
    """
    manifest = _load_suppliers(rec_id)
    if not manifest:
        manifest = _rebuild_suppliers_manifest_from_disk(rec_id)
        if manifest:
            _save_suppliers(rec_id, manifest)

    if not manifest:
        # Give a clear, actionable error with search details
        patterns = [p.format(rec_id=rec_id) for p in _DISCOVERY_PATTERNS]
        raise FileNotFoundError(
            "No suppliers have been processed for this record. "
            f"Searched recursively under DATA_DIR='{_data_dir()}' "
            f"for patterns: {patterns}. If you just uploaded files, "
            "ensure the /records/{rec_id}/supplier_responses endpoint writes "
            "per-supplier returnables like '{rec_id}_{sup_id}.returnables.json'."
        )

    selected = manifest
    if supplier_ids:
        idset = set(supplier_ids)
        selected = [s for s in manifest if s.get("id") in idset]
        if not selected:
            raise ValueError("None of the specified supplier IDs matched the manifest.")

    weights = _load_weights_from_tepp(rec_id)
    return _create_evaluation_workbook(rec_id, selected, weights)
