#!/usr/bin/env bash
set -euo pipefail

python - <<'PY'
import sys
major, minor = sys.version_info[:2]
if (major, minor) < (3, 11):
    raise SystemExit("Python 3.11+ is required")
print(f"Python {major}.{minor} detected")
PY

if [ ! -d ".venv" ]; then
  python -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

pip install -e ".[dev]"
pre-commit install
pre-commit install --hook-type commit-msg
playwright install

if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
fi

echo "Setup complete. Activate venv with: source .venv/bin/activate"
