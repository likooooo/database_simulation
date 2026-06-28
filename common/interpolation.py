"""Wavelength grid merging with cubic interpolation."""

from __future__ import annotations

import numpy as np
from scipy.interpolate import CubicSpline

from common.nk_convert import k_from_alpha_on_wl_um


def _dedupe_sorted(wl: np.ndarray, vals: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if wl.size == 0:
        return wl, vals
    order = np.argsort(wl)
    wl = wl[order]
    vals = vals[order]
    unique_wl: list[float] = []
    unique_vals: list[float] = []
    for w, v in zip(wl, vals):
        if unique_wl and np.isclose(w, unique_wl[-1]):
            unique_vals[-1] = float(v)
        else:
            unique_wl.append(float(w))
            unique_vals.append(float(v))
    return np.asarray(unique_wl, dtype=float), np.asarray(unique_vals, dtype=float)


def cubic_interp_extrap(
    x_new: np.ndarray,
    x_src: np.ndarray,
    y_src: np.ndarray,
) -> np.ndarray:
    if x_src.size == 0:
        return np.zeros_like(x_new, dtype=float)
    if x_src.size == 1:
        return np.full_like(x_new, float(y_src[0]), dtype=float)
    spline = CubicSpline(x_src, y_src, extrapolate=True)
    return np.asarray(spline(x_new), dtype=float)


def merge_n_alpha_to_nk(
    wl_n_um: np.ndarray,
    n_vals: np.ndarray,
    wl_alpha_um: np.ndarray,
    alpha_vals: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Merge n and alpha tables onto the wavelength union with cubic interpolation.

    Returns (wl_um, n, k) on the union grid.
    """
    wl_n_um, n_vals = _dedupe_sorted(np.asarray(wl_n_um, dtype=float), np.asarray(n_vals, dtype=float))
    if wl_alpha_um.size:
        wl_alpha_um, alpha_vals = _dedupe_sorted(
            np.asarray(wl_alpha_um, dtype=float),
            np.asarray(alpha_vals, dtype=float),
        )

    grids = [wl_n_um]
    if wl_alpha_um.size:
        grids.append(wl_alpha_um)
    wl_union = np.unique(np.concatenate(grids))

    n_on_union = cubic_interp_extrap(wl_union, wl_n_um, n_vals)
    if wl_alpha_um.size:
        alpha_on_union = cubic_interp_extrap(wl_union, wl_alpha_um, alpha_vals)
    else:
        alpha_on_union = np.zeros_like(wl_union, dtype=float)

    k_on_union = k_from_alpha_on_wl_um(wl_union, alpha_on_union)
    return wl_union, n_on_union, k_on_union
