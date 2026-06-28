#!/usr/bin/env bash
# Register child *_database repos as git submodules once they are initialized.
#
# Each child directory must be an independent git repo (contain .git) before
# this script can register it. Run from the simulation_database root:
#
#   ./setup_submodules.sh
#
# Safe to re-run: already-registered submodules are skipped.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

SUBMODULES=(
  og
  fs
  vl
  rii
)

if [[ ! -d .git ]]; then
  echo "error: parent repo not initialized; run 'git init' in $ROOT first" >&2
  exit 1
fi

is_registered() {
  local dir="$1"
  git config -f .gitmodules --get "submodule.${dir}.url" &>/dev/null
}

register_existing_repo() {
  local dir="$1"
  local abs url

  abs="$(cd "$dir" && pwd)"
  url="file://${abs}"

  echo "==> registering $dir"
  echo "    url: $url"

  if [[ ! -f .gitmodules ]]; then
    : > .gitmodules
  fi

  git config -f .gitmodules "submodule.${dir}.path" "$dir"
  git config -f .gitmodules "submodule.${dir}.url" "$url"
  git add .gitmodules

  # Stage the gitlink for the existing checkout.
  git -C "$dir" rev-parse HEAD >/dev/null
  git add "$dir"

  if git submodule absorbgitdirs "$dir" >/dev/null 2>&1; then
    echo "    absorbed git dir into .git/modules/${dir}"
  fi

  echo "    done"
}

added=0
skipped=0
pending=0

for dir in "${SUBMODULES[@]}"; do
  echo "--- $dir ---"

  if is_registered "$dir"; then
    echo "skip: already in .gitmodules"
    skipped=$((skipped + 1))
    continue
  fi

  if [[ ! -d "$dir" ]]; then
    echo "skip: directory missing"
    pending=$((pending + 1))
    continue
  fi

  if [[ ! -e "$dir/.git" ]]; then
    echo "skip: $dir/.git not found (initialize child repo first)"
    pending=$((pending + 1))
    continue
  fi

  register_existing_repo "$dir"
  added=$((added + 1))
done

echo
echo "setup_submodules: added=${added} skipped=${skipped} pending=${pending}"
if (( pending > 0 )); then
  echo "Initialize remaining child repos, then re-run this script."
fi

if (( added > 0 )); then
  echo "Commit submodule registration:"
  echo "  git commit -m \"Add database submodules\""
fi
