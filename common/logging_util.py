"""Per-material warning logging."""

from __future__ import annotations

import sys
from pathlib import Path


class MaterialLogger:
    def __init__(self, name: str, log_dir: Path | None = None) -> None:
        self.name = name
        self.warnings: list[str] = []
        self.log_dir = log_dir

    def warn(self, message: str) -> None:
        line = f"[{self.name}] {message}"
        self.warnings.append(message)
        print(line, file=sys.stderr)

    def flush(self) -> None:
        if self.log_dir is None:
            return
        self.log_dir.mkdir(parents=True, exist_ok=True)
        safe_name = self.name.replace("/", "_")
        log_path = self.log_dir / f"{safe_name}.log"
        if not self.warnings:
            if log_path.is_file():
                log_path.unlink()
            return
        log_path.write_text("\n".join(self.warnings) + "\n", encoding="utf-8")
