#!/usr/bin/env python3
"""One-click update for all simulation_database submodules."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent

SUBMODULES = {
    "refractive_index_info": {
        "script": "rii/update_current_database.py",
        "args": [],
    },
    "oghma": {
        "script": "og/update_current_database.py",
        "args": [],
    },
    # "oghma_projects": {
    #     "script": "og/export_oghma_projects.sh",
    #     "args": [],
    #     "config_keys": ["oghma_projects.source_dir"],
    # },
    "freesnell": {
        "script": "fs/update_current_database.py",
        "args": ["--scm", "--rwb"],
        "config_keys": ["freesnell.scm", "freesnell.rwb"],
    },
    "virtuallab": {
        "script": "vl/update_current_database.py",
        "args": ["--virtuallab-dir", "--csv-source", "--index-csv"],
        "config_keys": [
            "virtuallab.virtuallab_dir",
            "virtuallab.csv_source",
            "virtuallab.index_csv",
        ],
    },
    "granfilm": {
        "script": "gf/update_current_database.py",
        "args": ["--download-url", "--granfilm-dir", "--dielectric-dir"],
        "config_keys": [
            "granfilm.download_url",
            "granfilm.granfilm_dir",
            "granfilm.force",
        ],
    },
}


def load_config(path: Path) -> dict:
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {}


def nested_get(cfg: dict, dotted: str):
    node = cfg
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def git_submodule_update(pull: bool) -> int:
    init = subprocess.run(
        ["git", "submodule", "update", "--init", "--recursive"],
        cwd=ROOT,
        check=False,
    )
    if init.returncode != 0:
        print(
            "error: git submodule update --init failed "
            f"(exit {init.returncode}); run ./setup_submodules.sh if submodules are not registered yet",
            file=sys.stderr,
        )
        return init.returncode
    if not pull:
        return 0
    result = subprocess.run(
        ["git", "submodule", "foreach", "git", "pull", "--ff-only"],
        cwd=ROOT,
        check=False,
    )
    if result.returncode != 0:
        print(
            f"error: git submodule foreach pull failed (exit {result.returncode})",
            file=sys.stderr,
        )
    return result.returncode


def run_script(name: str, spec: dict, cfg: dict, config_path: Path) -> int:
    script = ROOT / spec["script"]
    if not script.is_file():
        print(
            f"error: script missing for {name}: {script}\n"
            "hint: run 'git submodule update --init' or ./setup_submodules.sh",
            file=sys.stderr,
        )
        return 1

    cmd = [sys.executable, str(script)]

    if name == "refractive_index_info":
        sha = nested_get(cfg, "refractive_index_info.sha")
        if sha:
            cmd.extend(["--sha", str(sha)])
    elif name == "oghma":
        if nested_get(cfg, "oghma.force"):
            cmd.append("--force")
    elif name == "oghma_projects":
        remote_via_windows = nested_get(cfg, "oghma_projects.remote_via_windows")
        if sys.platform != "win32" and remote_via_windows is not False:
            remote_script = ROOT / "og/export_oghma_projects.sh"
            if not remote_script.is_file():
                print(f"error: remote export script missing: {remote_script}", file=sys.stderr)
                return 1
            config_arg = []
            if config_path.is_file():
                config_arg = ["--config", str(config_path)]
            cmd = ["bash", str(remote_script), *config_arg]
            print(f"\n=== update: {name} (WSL → Windows SSH/scp → OneDrive → database/og/oghma_projects) ===")
            print(" ".join(cmd))
            try:
                result = subprocess.run(cmd, cwd=ROOT, check=False)
            except OSError as exc:
                print(f"error: failed to run {name}: {exc}", file=sys.stderr)
                return 1
            if result.returncode != 0:
                print(
                    f"error: {name} remote sync failed with exit code {result.returncode}",
                    file=sys.stderr,
                )
            return result.returncode
        print(
            "error: oghma_projects sync requires WSL with remote_via_windows "
            "(or run og/export_oghma_projects.sh manually)",
            file=sys.stderr,
        )
        return 1
    elif name == "freesnell":
        scm = nested_get(cfg, "freesnell.scm")
        rwb = nested_get(cfg, "freesnell.rwb")
        if scm:
            cmd.extend(["--scm", str(scm)])
        if rwb:
            cmd.extend(["--rwb", str(rwb)])
    elif name == "granfilm":
        url = nested_get(cfg, "granfilm.download_url")
        gf_dir = nested_get(cfg, "granfilm.granfilm_dir")
        force = nested_get(cfg, "granfilm.force")
        if url:
            cmd.extend(["--download-url", str(url)])
        if gf_dir:
            cmd.extend(["--granfilm-dir", str(gf_dir)])
        if force:
            cmd.append("--force")
    elif name == "virtuallab":
        vl_dir = nested_get(cfg, "virtuallab.virtuallab_dir")
        remote_via_windows = nested_get(cfg, "virtuallab.remote_via_windows")
        # WSL/Linux + virtuallab_dir: scp ps1 → Windows CSV → WSL staging → YAML
        use_wsl_remote = (
            sys.platform != "win32"
            and vl_dir
            and remote_via_windows is not False
        )
        if use_wsl_remote:
            remote_script = ROOT / "vl/export_via_windows.sh"
            if not remote_script.is_file():
                print(f"error: remote export script missing: {remote_script}", file=sys.stderr)
                return 1
            config_arg = []
            if config_path.is_file():
                config_arg = ["--config", str(config_path)]
            cmd = ["bash", str(remote_script), *config_arg]
            print(f"\n=== update: {name} (WSL → Windows SSH → CSV → YAML) ===")
            print(" ".join(cmd))
            try:
                result = subprocess.run(cmd, cwd=ROOT, check=False)
            except OSError as exc:
                print(f"error: failed to run {name}: {exc}", file=sys.stderr)
                return 1
            if result.returncode != 0:
                print(
                    f"error: {name} remote export failed with exit code {result.returncode}",
                    file=sys.stderr,
                )
            return result.returncode

        csv_source = nested_get(cfg, "virtuallab.csv_source")
        index_csv = nested_get(cfg, "virtuallab.index_csv")
        if remote_via_windows is False:
            if csv_source:
                cmd.extend(["--csv-source", str(csv_source)])
            elif vl_dir:
                print(
                    "warning: virtuallab.remote_via_windows=false on WSL; "
                    "set csv_source or enable remote export",
                    file=sys.stderr,
                )
        elif vl_dir:
            cmd.extend(["--virtuallab-dir", str(vl_dir)])
        elif csv_source:
            cmd.extend(["--csv-source", str(csv_source)])
        if index_csv:
            cmd.extend(["--index-csv", str(index_csv)])
        if not vl_dir and not csv_source:
            print(
                "warning: virtuallab.virtuallab_dir / csv_source not set; "
                "using update_current_database.py defaults",
                file=sys.stderr,
            )

    print(f"\n=== update: {name} ===")
    print(" ".join(cmd))
    try:
        result = subprocess.run(cmd, cwd=ROOT, check=False)
    except OSError as exc:
        print(f"error: failed to run {name}: {exc}", file=sys.stderr)
        return 1
    if result.returncode != 0:
        print(f"error: {name} failed with exit code {result.returncode}", file=sys.stderr)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Update all simulation_database submodules.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config.yaml",
        help="Config file (falls back to config.example.yaml)",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        choices=list(SUBMODULES.keys()),
        help="Run only selected submodules",
    )
    parser.add_argument(
        "--pull",
        action="store_true",
        help="git pull inside each submodule before export",
    )
    parser.add_argument(
        "--skip-submodule-init",
        action="store_true",
        help="Skip git submodule update --init",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Run remaining modules even if one fails",
    )
    args = parser.parse_args()

    config_path = args.config.resolve()
    if not config_path.is_file():
        example = ROOT / "config.example.yaml"
        if example.is_file():
            print(f"note: using {example} (config.yaml not found)", file=sys.stderr)
            config_path = example
        else:
            print(f"warning: config not found: {config_path}", file=sys.stderr)
    cfg = load_config(config_path)

    if not args.skip_submodule_init and (ROOT / ".git").is_dir():
        rc = git_submodule_update(args.pull)
        if rc != 0 and not args.continue_on_error:
            return rc

    names = args.only or list(SUBMODULES.keys())
    failures: list[str] = []
    for name in names:
        rc = run_script(name, SUBMODULES[name], cfg, config_path)
        if rc != 0:
            failures.append(name)
            if not args.continue_on_error:
                remaining = [n for n in names[names.index(name) + 1 :] if n not in failures]
                if remaining:
                    print(
                        f"update_all: stopping after {name} failure; "
                        f"skipped: {', '.join(remaining)}",
                        file=sys.stderr,
                    )
                break

    if failures:
        print(f"\nupdate_all: failed modules: {', '.join(failures)}", file=sys.stderr)
        return 1
    print("\nupdate_all: all modules completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
