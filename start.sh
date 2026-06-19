#!/bin/bash
set -e
PORT=8000
if lsof -t -iTCP:${PORT} -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Server already running on ${PORT}"
else
  nohup python3 -m http.server ${PORT} --bind 0.0.0.0 >/dev/null 2>&1 &
  sleep 1
fi
open http://localhost:${PORT}/
