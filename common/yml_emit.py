"""Emit refractiveindex.info-compatible YAML files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


def _format_value(value: float) -> str:
    """Format numeric columns like refractiveindex.info tabulated data."""
    if value == 0.0:
        return "0"
    abs_val = abs(value)
    if abs_val >= 1e-3 and abs_val < 1e4:
        text = f"{value:.6g}"
    else:
        text = f"{value:.6E}".replace("e", "E")
    return text


def _format_coeff(value: float) -> str:
    if value == 0.0:
        return "0"
    return _format_value(value)


def _block_scalar(key: str, text: str) -> str:
    if not text.strip():
        return f"{key}: |\n"
    lines = text.rstrip("\n").split("\n")
    body = "\n".join(f"    {line}" for line in lines)
    return f"{key}: |\n{body}\n"


def _render_data_blocks(blocks: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = ["DATA:"]
    for block in blocks:
        btype = block["type"]
        lines.append(f"  - type: {btype}")
        if btype.startswith("formula"):
            lines.append(f"    wavelength_range: {block['wl_min']:.6g} {block['wl_max']:.6g}")
            coeff_text = " ".join(_format_coeff(c) for c in block["coefficients"])
            lines.append(f"    coefficients: {coeff_text}")
        elif btype.startswith("tabulated"):
            lines.append("    data: |")
            for row in block["rows"]:
                if len(row) == 2:
                    w, v = row
                    lines.append(f"        {_format_value(w)} {_format_value(v)}")
                else:
                    w, n, k = row
                    lines.append(
                        f"        {_format_value(w)} {_format_value(n)} {_format_value(k)}"
                    )
    return lines


def write_material_yml(
    path: Path,
    data_blocks: list[dict[str, Any]],
    *,
    references: str = "",
    comments: str = "",
    conditions: str = "",
) -> None:
    """Write YAML with one or more DATA blocks (formula, tabulated nk/k, etc.)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    parts = [
        _block_scalar("REFERENCES", references),
        _block_scalar("COMMENTS", comments),
        _block_scalar("CONDITIONS", conditions),
        *_render_data_blocks(data_blocks),
        "",
    ]
    path.write_text("\n".join(parts), encoding="utf-8")


def write_formula_yml(
    path: Path,
    formula_type: int,
    wl_min: float,
    wl_max: float,
    coefficients: list[float],
    *,
    extra_blocks: list[dict[str, Any]] | None = None,
    references: str = "",
    comments: str = "",
    conditions: str = "",
) -> None:
    blocks: list[dict[str, Any]] = [
        {
            "type": f"formula {formula_type}",
            "wl_min": wl_min,
            "wl_max": wl_max,
            "coefficients": coefficients,
        }
    ]
    if extra_blocks:
        blocks.extend(extra_blocks)
    write_material_yml(
        path,
        blocks,
        references=references,
        comments=comments,
        conditions=conditions,
    )


def _tabulated_nk_rows(wl_um: np.ndarray, n_vals: np.ndarray, k_vals: np.ndarray) -> list[tuple]:
    wl_um = np.asarray(wl_um, dtype=float)
    n_vals = np.asarray(n_vals, dtype=float)
    k_vals = np.asarray(k_vals, dtype=float)
    return [(float(w), float(n), float(k)) for w, n, k in zip(wl_um, n_vals, k_vals)]


def _tabulated_k_rows(wl_um: np.ndarray, k_vals: np.ndarray) -> list[tuple]:
    wl_um = np.asarray(wl_um, dtype=float)
    k_vals = np.asarray(k_vals, dtype=float)
    return [(float(w), float(k)) for w, k in zip(wl_um, k_vals)]


def tabulated_nk_block(wl_um: np.ndarray, n_vals: np.ndarray, k_vals: np.ndarray) -> dict[str, Any]:
    return {"type": "tabulated nk", "rows": _tabulated_nk_rows(wl_um, n_vals, k_vals)}


def tabulated_k_block(wl_um: np.ndarray, k_vals: np.ndarray) -> dict[str, Any]:
    return {"type": "tabulated k", "rows": _tabulated_k_rows(wl_um, k_vals)}


def _tabulated_spectra_rows(wl_um: np.ndarray, values: np.ndarray) -> list[tuple]:
    wl_um = np.asarray(wl_um, dtype=float)
    values = np.asarray(values, dtype=float)
    return [(float(w), float(v)) for w, v in zip(wl_um, values)]


def tabulated_spectra_block(wl_um: np.ndarray, values: np.ndarray) -> dict[str, Any]:
    return {"type": "tabulated spectra", "rows": _tabulated_spectra_rows(wl_um, values)}


def write_tabulated_spectra_yml(
    path: Path,
    wl_um: np.ndarray,
    values: np.ndarray,
    *,
    references: str = "",
    comments: str = "",
    conditions: str = "",
) -> None:
    write_material_yml(
        path,
        [tabulated_spectra_block(wl_um, values)],
        references=references,
        comments=comments,
        conditions=conditions,
    )


def write_tabulated_nk_yml(
    path: Path,
    wl_um: np.ndarray,
    n_vals: np.ndarray,
    k_vals: np.ndarray,
    *,
    references: str = "",
    comments: str = "",
    conditions: str = "",
) -> None:
    write_material_yml(
        path,
        [tabulated_nk_block(wl_um, n_vals, k_vals)],
        references=references,
        comments=comments,
        conditions=conditions,
    )
