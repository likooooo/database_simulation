"""Refractive index and absorption conversions."""

from __future__ import annotations

import numpy as np


def k_from_alpha_on_wl_um(wl_um: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Oghma convention: k = alpha * lambda / (4*pi), with lambda in metres."""
    wl_um_arr = np.asarray(wl_um, dtype=float)
    alpha_arr = np.asarray(alpha, dtype=float)
    return alpha_arr * wl_um_arr * 1e-6 / (4.0 * np.pi)
