"""Read Oghma / simulation_toolkits CSV material tables."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np


def read_oghma_csv(path: Path) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    meta: dict[str, Any] = {}
    if lines and lines[0].startswith("#"):
        match = re.search(r"\{(.+)\}", lines[0])
        if match:
            raw = "{" + match.group(1) + "}"
            raw = re.sub(r":\s*nan\b", ": null", raw, flags=re.IGNORECASE)
            raw = re.sub(r":\s*-?inf\b", ": null", raw, flags=re.IGNORECASE)
            meta = json.loads(raw)
    xs: list[float] = []
    ys: list[float] = []
    for line in lines[1:]:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [float(x) for x in line.replace(",", " ").split()]
        if len(parts) < 2:
            continue
        xs.append(parts[0])
        ys.append(parts[1])
    return np.asarray(xs, dtype=float), np.asarray(ys, dtype=float), meta


def oghma_axis_to_um(values: np.ndarray, meta: dict[str, Any], *, axis: str = "y") -> np.ndarray:
    mul_key = "y_mul" if axis == "y" else "x_mul"
    units_key = "y_units" if axis == "y" else "x_units"
    fallback_mul = meta.get("y_mul" if axis == "x" else "x_mul", 1.0)
    fallback_units = meta.get("y_units" if axis == "x" else "x_units", "m")
    mul = float(meta.get(mul_key, fallback_mul))
    units = str(meta.get(units_key, fallback_units))
    pos = values * mul if mul != 1.0 else values
    if units == "nm":
        return np.asarray(pos, dtype=float) * 1e-3
    if units == "um":
        return np.asarray(pos, dtype=float)
    return np.asarray(pos, dtype=float) * 1e6


def read_tabulated_xy_um(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Read two-column CSV; return sorted (wl_um, value)."""
    wl_raw, val, meta = read_oghma_csv(path)
    if meta:
        wl_um = oghma_axis_to_um(wl_raw, meta, axis="y")
    else:
        wl_raw_arr = np.asarray(wl_raw, dtype=float)
        if wl_raw_arr.size == 0:
            wl_um = wl_raw_arr
        elif np.nanmax(wl_raw_arr) < 1e-2:
            wl_um = wl_raw_arr * 1e6
        else:
            wl_um = wl_raw_arr
    val_arr = np.asarray(val, dtype=float)
    order = np.argsort(wl_um)
    return wl_um[order], val_arr[order]


def read_material_nk_table(
    root: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Read n.csv / alpha.csv from a material directory (sorted axes in um)."""
    n_x, n_y, n_meta = read_oghma_csv(root / "n.csv")
    wl_um = oghma_axis_to_um(n_x, n_meta, axis="y")
    n_vals = np.asarray(n_y, dtype=float)

    alpha_path = root / "alpha.csv"
    if alpha_path.is_file():
        a_x, a_y, a_meta = read_oghma_csv(alpha_path)
        wl_alpha_um = oghma_axis_to_um(a_x, a_meta, axis="y")
        alpha_vals = np.asarray(a_y, dtype=float)
    else:
        wl_alpha_um = np.array([], dtype=float)
        alpha_vals = np.array([], dtype=float)

    n_order = np.argsort(wl_um)
    wl_um = wl_um[n_order]
    n_vals = n_vals[n_order]
    if wl_alpha_um.size:
        alpha_order = np.argsort(wl_alpha_um)
        wl_alpha_um = wl_alpha_um[alpha_order]
        alpha_vals = alpha_vals[alpha_order]
    return wl_um, n_vals, wl_alpha_um, alpha_vals
