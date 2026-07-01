#!/usr/bin/env python3
"""Copy converted database files from simulation_database to a release directory."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

DATABASES = {
    "oghma": {
        "subdir": "og",
        "data_dirs": ("materials", "spectra"),
    },
    "freesnell": {
        "subdir": "fs",
        "data_dirs": ("materials",),
    },
    "refractive_index_info": {
        "subdir": "rii",
        "data_dirs": ("materials",),
    },
    "virtuallab": {
        "subdir": "vl",
        "data_dirs": ("materials",),
    },
    "granfilm": {
        "subdir": "gf",
        "data_dirs": ("materials", "finite_size"),
    },
    "openfilters": {
        "subdir": "of",
        "data_dirs": ("materials",),
    },
}


def count_tree(path: Path) -> tuple[int, int]:
    files = 0
    nbytes = 0
    for item in path.rglob("*"):
        if item.is_file():
            files += 1
            nbytes += item.stat().st_size
    return files, nbytes


def release_database(
    name: str,
    spec: dict,
    dest: Path,
    *,
    clean: bool,
    dry_run: bool,
) -> tuple[int, int, list[str]]:
    subdir = spec["subdir"]
    src_root = ROOT / subdir
    dest_root = dest / subdir
    warnings: list[str] = []
    total_files = 0
    total_bytes = 0

    if not src_root.is_dir():
        warnings.append(f"{name}: source missing: {src_root}")
        return total_files, total_bytes, warnings

    existing_dirs = [src_root / d for d in spec["data_dirs"] if (src_root / d).is_dir()]
    if not existing_dirs:
        warnings.append(f"{name}: no data directories found under {src_root}")
        return total_files, total_bytes, warnings

    if clean and dest_root.exists():
        if dry_run:
            print(f"  would remove {dest_root}")
        else:
            shutil.rmtree(dest_root)

    for data_dir in spec["data_dirs"]:
        src = src_root / data_dir
        dst = dest_root / data_dir
        if not src.is_dir():
            warnings.append(f"{name}: skip missing {src}")
            continue

        files, nbytes = count_tree(src)
        total_files += files
        total_bytes += nbytes
        print(f"  {src} -> {dst}  ({files} files, {nbytes} bytes)")

        if dry_run:
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, dirs_exist_ok=True)

    return total_files, total_bytes, warnings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy simulation_database data directories to a release path.",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        required=True,
        help="Target root directory (submodule folders are created beneath it)",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        choices=list(DATABASES.keys()),
        help="Release only selected databases",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove <dest>/<submodule>/ before copying each database",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned copies without writing files",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue releasing remaining databases after a failure",
    )
    args = parser.parse_args()

    dest = args.dest.resolve()
    if not args.dry_run:
        dest.mkdir(parents=True, exist_ok=True)

    names = args.only or list(DATABASES.keys())
    failures: list[str] = []
    released = 0
    grand_files = 0
    grand_bytes = 0

    for name in names:
        print(f"\n=== release: {name} ===")
        files, nbytes, warnings = release_database(
            name,
            DATABASES[name],
            dest,
            clean=args.clean,
            dry_run=args.dry_run,
        )

        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)

        if warnings and files == 0:
            failures.append(name)
            if not args.continue_on_error:
                remaining = [n for n in names[names.index(name) + 1 :] if n not in failures]
                if remaining:
                    print(
                        f"database_release: stopping after {name} failure; "
                        f"skipped: {', '.join(remaining)}",
                        file=sys.stderr,
                    )
                break
            continue

        if files > 0:
            released += 1
            grand_files += files
            grand_bytes += nbytes
            print(f"  released {name}: {files} files, {nbytes} bytes")

    if failures:
        print(f"\ndatabase_release: failed databases: {', '.join(failures)}", file=sys.stderr)
        return 1

    action = "would release" if args.dry_run else "released"
    print(
        f"\ndatabase_release: {action} {released} database(s), "
        f"{grand_files} files, {grand_bytes} bytes -> {dest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
