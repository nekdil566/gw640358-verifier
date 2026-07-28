#!/usr/bin/env bash
# Start the manual verifier backend and open it in the browser.
set -e
cd "$(dirname "$0")"

# Create/activate a local venv so PDF extraction libs are isolated.
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
. .venv/bin/activate

pip install -q -r requirements.txt

PORT="${1:-8000}"
echo "Starting Farm 640358 manual verifier on http://127.0.0.1:${PORT}"
python3 server.py "$PORT"
