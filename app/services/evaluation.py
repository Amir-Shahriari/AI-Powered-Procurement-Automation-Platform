from __future__ import annotations
import json
from pathlib import Path
from typing import List
import xlsxwriter

from ..config import settings


def _load_tepp_weights(rec_id: str, data_dir: Path = settings.DATA_DIR) -> tuple[float, List[tuple[str, float]]]:
    """Extract price and other evaluation weights from the TEPP JSON."""
    tepp_path = data_dir / f"{rec_id}.tepp.json"
    if not tepp_path.exists():
        raise FileNotFoundError(f"TEPP JSON not found for record {rec_id} at {tepp_path}")
    with tepp_path.open("r", encoding="utf-8") as f:
        tepp = json.load(f)
    em = tepp.get("tender_evaluation", {}).get("evaluation_methodology", {})
    crit_table = em.get("required_criteria_table") or []
    price_weight = None
    other = []
    for row in crit_table:
        name = str(row.get("criterion", "")).strip()
        w_str = str(row.get("weight", "")).strip()
        try:
            w_val = float(w_str[:-1]) if w_str.endswith("%") else float(w_str)
        except Exception:
            continue
        if name.lower().startswith("price"):
            price_weight = w_val
        else:
            other.append((name, w_val))
    if price_weight is None:
        price_weight = 0.0
    return price_weight, other


def generate_evaluation_excel(rec_id: str, suppliers: List[str], data_dir: Path = settings.DATA_DIR) -> str:
    """
    Generate a multi‑sheet evaluation workbook.

    Sheet 1 (“Evaluation Criterion”) lists each evaluation criterion and its weight.
    Sheet 2 (“Total Scoring”) contains the scoring matrix where evaluators enter
    price and qualitative scores; formulas normalise price, apply weights,
    compute totals and ranking automatically.
    """
    price_weight, crit_weights = _load_tepp_weights(rec_id, data_dir=data_dir)
    out_path = data_dir / f"{rec_id}_evaluation.xlsx"
    workbook = xlsxwriter.Workbook(out_path.as_posix())

    # First sheet: criterion and weights
    ws_crit = workbook.add_worksheet("Evaluation Criterion")
    header_fmt = workbook.add_format({"bold": True, "bg_color": "#1f2937", "font_color": "#FFFFFF", "border": 1})
    ws_crit.write(0, 0, "Criterion", header_fmt)
    ws_crit.write(0, 1, "Weight", header_fmt)
    ws_crit.write(1, 0, "Price (Full Cost)")
    ws_crit.write(1, 1, price_weight)
    for idx, (crit, weight) in enumerate(crit_weights, start=2):
        ws_crit.write(idx, 0, crit)
        ws_crit.write(idx, 1, weight)
    ws_crit.set_column(0, 0, 50)
    ws_crit.set_column(1, 1, 15)

    # Second sheet: main scoring matrix
    ws = workbook.add_worksheet("Total Scoring")
    header_fmt = workbook.add_format({"bold": True, "bg_color": "#1f2937", "font_color": "#FFFFFF", "border": 1})
    weight_fmt = workbook.add_format({"italic": True, "align": "center"})
    score_fmt = workbook.add_format({"num_format": "0.00"})
    general_fmt = workbook.add_format({"border": 1})

    weight_row = 0
    header_row = 1
    start_data_row = 2

    # Header columns
    col = 0
    ws.write(header_row, col, "Supplier", header_fmt); col += 1
    ws.write(header_row, col, "Price (Raw Cost)", header_fmt); col += 1
    ws.write(header_row, col, "Price Score", header_fmt); col += 1
    ws.write(header_row, col, "Price Norm Score", header_fmt); col += 1
    ws.write(header_row, col, "Price Weighted Score", header_fmt)
    ws.write(weight_row, col, price_weight, weight_fmt)
    col += 1

    # Non‑price criteria columns
    for crit, weight in crit_weights:
        ws.write(header_row, col, f"Raw {crit}", header_fmt)
        col += 1
        ws.write(header_row, col, f"Weighted {crit}", header_fmt)
        ws.write(weight_row, col, weight, weight_fmt)
        col += 1

    total_col = col
    ws.write(header_row, total_col, "Total Score", header_fmt)
    col += 1
    rank_col = col
    ws.write(header_row, rank_col, "Rank", header_fmt)

    last_data_row = start_data_row + len(suppliers) - 1

    for i, name in enumerate(suppliers):
        row = start_data_row + i
        ws.write(row, 0, name, general_fmt)
        price_cell = xlsxwriter.utility.xl_rowcol_to_cell(row, 1)
        price_score_cell = xlsxwriter.utility.xl_rowcol_to_cell(row, 2)
        price_norm_cell = xlsxwriter.utility.xl_rowcol_to_cell(row, 3)
        price_weighted_cell = xlsxwriter.utility.xl_rowcol_to_cell(row, 4)
        avg_range = f"$B${start_data_row+1}:$B${last_data_row+1}"
        ps_formula = f"=IF({price_cell}=\"\" , \"\", 200 - ({price_cell} / AVERAGE({avg_range}) * 100))"
        ws.write_formula(row, 2, ps_formula, score_fmt)
        pn_formula = f"=IF({price_score_cell}=\"\" , \"\", {price_score_cell} / 200)"
        ws.write_formula(row, 3, pn_formula, score_fmt)
        pw_formula = f"=IF({price_norm_cell}=\"\" , \"\", {price_norm_cell} * {price_weight})"
        ws.write_formula(row, 4, pw_formula, score_fmt)

        col_idx = 5
        total_formula_parts = [price_weighted_cell]
        for crit, weight in crit_weights:
            raw_cell = xlsxwriter.utility.xl_rowcol_to_cell(row, col_idx)
            weighted_cell = xlsxwriter.utility.xl_rowcol_to_cell(row, col_idx + 1)
            ws.write_formula(row, col_idx + 1,
                              f"=IF({raw_cell}=\"\" , \"\", ({raw_cell} / 5) * {weight})",
                              score_fmt)
            total_formula_parts.append(weighted_cell)
            col_idx += 2

        total_formula_cells = ",".join(total_formula_parts)
        total_formula = f"=IF({price_cell}=\"\" , \"\", SUM({total_formula_cells}))"
        ws.write_formula(row, total_col, total_formula, score_fmt)
        total_range = (f"${xlsxwriter.utility.xl_col_to_name(total_col)}"
                       f"${start_data_row+1}"
                       f":${xlsxwriter.utility.xl_col_to_name(total_col)}${last_data_row+1}")
        rank_formula = f"=IF({price_cell}=\"\" , \"\", RANK({xlsxwriter.utility.xl_rowcol_to_cell(row, total_col)}, {total_range}, 0))"
        ws.write_formula(row, rank_col, rank_formula, general_fmt)

    ws.set_column(0, 0, 20)
    ws.set_column(1, 1, 15)
    ws.set_column(2, 4, 18)
    col_idx = 5
    for crit, _ in crit_weights:
        ws.set_column(col_idx, col_idx, 14)
        ws.set_column(col_idx + 1, col_idx + 1, 20)
        col_idx += 2
    ws.set_column(total_col, total_col, 14)
    ws.set_column(rank_col, rank_col, 10)

    workbook.close()
    return out_path.as_posix()
