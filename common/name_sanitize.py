"""Filesystem entry names safe for filmstack formula material tokens."""

from __future__ import annotations

import re

_FALLBACK = "entry"


def safe_entry_name(name: str) -> str:
    """Return a token-safe name: whitespace, parens, and illegal chars become ``_``."""
    slug = re.sub(r"\s+", "_", name.strip())
    slug = slug.replace("(", "_").replace(")", "_")
    slug = re.sub(r"[^\w.\-]+", "_", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or _FALLBACK


def sanitize_path_segment(segment: str) -> str:
    """Sanitize one path component (directory name or yml stem without suffix)."""
    return safe_entry_name(segment)
