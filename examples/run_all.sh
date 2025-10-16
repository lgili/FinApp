#!/usr/bin/env bash
# Run all examples in sequence (zsh/bash)
set -euo pipefail

ROOT_DIR=$(cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd)
cd "$ROOT_DIR"

if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
else
  echo "Warning: .venv not found. Consider creating a virtualenv and installing requirements.txt"
fi

export PYTHONPATH="${PYTHONPATH}:$ROOT_DIR/backend"

echo "Running examples..."
python3 examples/01_setup_accounts.py || true
python3 examples/02_create_transactions.py || true
python3 examples/03_import_csv.py || true
python3 examples/04_query_data.py || true
python3 examples/05_full_workflow.py --reset || true

echo "Done."
