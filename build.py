#!/usr/bin/env python3
"""build.py - produce a single self-contained wind-farm-verifier.html.

The dev file (index.html) references lib/ assets via relative paths. This
script inlines Leaflet + pdf.js + the pdf worker into ONE html file so the
result works by double-clicking on file:// with no server and no internet
for assets (tiles still need internet, by design).

Output: wind-farm-verifier.html  (drop-in, email-able, one-click tool)
"""
from __future__ import annotations
import json, pathlib, re

BASE = pathlib.Path(__file__).resolve().parent

def read(p: str) -> str:
    return (BASE / p).read_text(encoding="utf-8")

html = read("index.html")

# --- inline leaflet css ---
leaflet_css = read("lib/leaflet.css")
html = html.replace('<link rel="stylesheet" href="lib/leaflet.css">',
                    f"<style>{leaflet_css}</style>")

# --- inline leaflet js ---
leaflet_js = read("lib/leaflet.js")
html = html.replace('<script src="lib/leaflet.js"></script>',
                    f"<script>{leaflet_js}</script>")

# --- inline pdf.min.js ---
pdf_js = read("lib/pdfjs/pdf.min.js")
html = html.replace('<script src="lib/pdfjs/pdf.min.js"></script>',
                    f"<script>{pdf_js}</script>")

# --- inline the pdf worker as a blob source (the __PDF_WORKER_SRC__ token) ---
worker_js = read("lib/pdfjs/pdf.worker.min.js")
# Embed as a JSON string literal so it survives inside the <script> block.
worker_src_literal = json.dumps(worker_js)
html = html.replace('"__PDF_WORKER_SRC__"', worker_src_literal)

out = BASE / "wind-farm-verifier.html"
out.write_text(html, encoding="utf-8")
print(f"built {out}  ({out.stat().st_size/1024:.0f} KB)")
