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
# Ignore non-numeric args (e.g. a pasted comment) and fall back to 8000.
case "$PORT" in (*[!0-9]*) PORT=8000;; esac

# Sanitize PYTHONPATH: the project .venv is Python 3.9, but an inherited
# PYTHONPATH pointing at another Python (e.g. Hermes' 3.11) breaks native
# extensions like cryptography/pdfminer ('symbol not found in flat namespace').
# Drop any PYTHONPATH entries that don't belong to THIS venv.
if [ -n "$PYTHONPATH" ]; then
  venv_sp="$(cd .venv/lib/*/site-packages 2>/dev/null && pwd)"
  cleaned=""
  IFS=':' read -ra parts <<< "$PYTHONPATH"
  for p in "${parts[@]}"; do
    case "$p" in
      "$venv_sp"|"$(pwd)"*) : ;;            # keep our own paths
      *".hermes"*|*python3.1"1"*) : ;;       # skip other interpreters' paths
      *) [ -z "$cleaned" ] && cleaned="$p" || cleaned="$cleaned:$p" ;;
    esac
  done
  export PYTHONPATH="$cleaned"
fi

echo "Starting Farm 640358 manual verifier on http://127.0.0.1:${PORT}"
python3 server.py "$PORT"
