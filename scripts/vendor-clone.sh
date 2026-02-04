#!/usr/bin/env bash
set -euo pipefail

mkdir -p vendor

clone_repo() {
  local name="$1"
  local url="$2"
  local dest="vendor/$name"

  if [ -d "$dest" ]; then
    echo "$dest already exists, skipping"
    return
  fi

  git clone "$url" "$dest"
  pushd "$dest" >/dev/null
  git rev-parse HEAD > UPSTREAM_VERSION.md
  rm -rf .git
  mkdir -p aria_extensions
  touch aria_extensions/__init__.py
  popd >/dev/null
}

clone_repo "aihawk" "https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk"
clone_repo "skyvern" "https://github.com/Skyvern-AI/skyvern"
clone_repo "browser-use" "https://github.com/browser-use/browser-use"
clone_repo "openadapt" "https://github.com/OpenAdaptAI/OpenAdapt"

echo "Vendor clone complete"
