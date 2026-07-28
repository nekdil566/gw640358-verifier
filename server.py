#!/usr/bin/env python3
"""server.py - local backend for the Farm 640358 manual verifier.

Why this exists:
  The browser's PDF.js worker fails when the page is opened via file://, so
  PDF coordinate import is impossible without a tiny server. This Flask app:
    * serves index.html and the lib/ assets
    * provides /api/import_pdf which extracts wtid/lat/lon rows from a PDF
      (e.g. a turbine layout sheet) using pdfminer and returns CSV.

Run:
    python3 server.py            # http://127.0.0.1:8000
    python3 server.py 9000       # custom port
"""
from __future__ import annotations

import io
import re
import sys

try:
    from flask import Flask, request, send_from_directory, jsonify
except ImportError:
    sys.stderr.write(
        "Flask not installed. Run: pip install -r requirements.txt\n"
    )
    raise

from pdfminer.high_level import extract_text

BASE = __import__("pathlib").Path(__file__).resolve().parent

app = Flask(__name__, static_folder=None)

# ---------------------------------------------------------------------------
# CSV import (unchanged behaviour, served by the same origin)
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(BASE, "index.html")

@app.route("/lib/<path:p>")
def lib(p):
    return send_from_directory(BASE / "lib", p)

# ---------------------------------------------------------------------------
# PDF import
# ---------------------------------------------------------------------------

_COORD_RE = re.compile(
    r"(?P<id>\d{4,})"                       # turbine id (4+ digits)
    r"[^0-9.\-]{0,12}"                       # separator junk
    r"(?P<lat>[+-]?\d{1,3}\.\d{3,8})"        # latitude
    r"[,\s]+"
    r"(?P<lon>[+-]?\d{1,3}\.\d{3,8})"        # longitude
)

# A line is a candidate if it has an id-like token + two decimals close together.
_LINE_RE = re.compile(
    r"(?P<id>\d{4,})\D{0,12}"
    r"(?P<a>[+-]?\d{1,3}\.\d{3,8})\D{0,6}"
    r"(?P<b>[+-]?\d{1,3}\.\d{3,8})"
)


def _parse_pdf(text: str):
    rows = []
    seen = set()
    for line in text.splitlines():
        m = _LINE_RE.search(line)
        if not m:
            continue
        tid = m.group("id")
        a = float(m.group("a"))
        b = float(m.group("b"))
        # Heuristic: latitude is the value in [-90,90], longitude in [-180,180]
        if -90 <= a <= 90 and -180 <= b <= 180:
            lat, lon = a, b
        elif -90 <= b <= 90 and -180 <= a <= 180:
            lat, lon = b, a
        else:
            continue
        if tid in seen:
            continue
        seen.add(tid)
        rows.append((tid, lat, lon))
    return rows


@app.route("/api/import_pdf", methods=["POST"])
def import_pdf():
    if "file" not in request.files:
        return jsonify(error="no file field"), 400
    f = request.files["file"]
    if not f.filename.lower().endswith(".pdf"):
        return jsonify(error="not a PDF"), 400
    try:
        data = f.read()
        text = extract_text(io.BytesIO(data))
    except Exception as e:  # noqa: BLE001
        return jsonify(error=f"PDF parse failed: {e}"), 500
    rows = _parse_pdf(text)
    if not rows:
        return jsonify(error="no turbine coordinates found in PDF", rows=[]), 200
    csv_lines = ["id,lat,lon"] + [f"{t},{lat},{lon}" for t, lat, lon in rows]
    return jsonify(rows=rows, csv="\n".join(csv_lines))


@app.route("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    # Accept the first purely-numeric CLI arg as the port; ignore anything else
    # (e.g. a pasted shell comment) and fall back to 8000.
    port = 8000
    for arg in sys.argv[1:]:
        if arg.isdigit():
            port = int(arg)
            break
    app.run(host="127.0.0.1", port=port, debug=False)
