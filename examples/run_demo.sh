#!/usr/bin/env bash
set -euo pipefail

# Simple demo runner for Unix-like systems.
# Run from repository root: ./examples/run_demo.sh

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$REPO_ROOT"

# 1) Create venv if missing
if [ ! -d ".venv" ]; then
  python -m venv .venv
fi

# 2) Activate venv for this script
# shellcheck source=/dev/null
source .venv/bin/activate

# 3) Install package in editable mode
pip install -e .

# 4) Start mock API in background
python examples/mock_apis/users_api.py &
API_PID=$!
echo "Started mock API (PID=$API_PID). Waiting 1s for server to start..."
sleep 1

# 5) Run validator (uses CLI `acv` provided by package)
acv validate --spec openapi/sample_users_api.yaml --url http://localhost:8000

# 6) Optional: copy last report path for convenience
echo "Demo finished. Shutting down mock API (PID=$API_PID)"
kill $API_PID || true

exit 0
