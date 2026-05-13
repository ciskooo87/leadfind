#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  echo "Ambiente .venv não encontrado" >&2
  exit 1
fi

source .venv/bin/activate
python scripts/run_due_watchlists.py
