# Wind Farm Coordinate Verifier (v2.0)

A lightweight, local-first tool for **manually verifying and correcting wind-turbine
coordinates** against high-resolution satellite imagery (Esri World Imagery basemap).
It is **farm-agnostic**: use it for *any* wind farm, not just 640358.

> This is **Path 1 — Manual verification**, now generalized + packaged as a
> one-click tool. The automated image-based detection tool (YOLO / SAM) is a
> separate effort (Path 2/3).

## What it does

- Upload a turbine list as **CSV** or **PDF** (a turbine layout sheet)
- See every turbine on a satellite basemap (map auto-fits to your data bounds)
- Click a row → fly to the original location
- **✏️ Edit** → click the real turbine on the map → records corrected coordinates + deviation (meters)
- **OK** → confirm the original is correct (0 m)
- **↺ Reset** → clear a row to re-correct it
- **Undo** (⌘/Ctrl+Z) → revert the last correction
- Auto-advances to the next unverified turbine; live OK / Review / Offset KPIs
- Auto-saves **per farm** to the browser; **Export** a re-importable corrected CSV

## The one-click tool (recommended)

`wind-farm-verifier.html` is a **single self-contained file** — Leaflet + pdf.js are
inlined, so it works by **double-clicking it** (opens in your default browser, no
server, no internet for assets; map tiles do need internet). PDFs are parsed
**in-browser**, so there is no backend dependency at all.

Just double-click `wind-farm-verifier.html` and upload your CSV/PDF. That's it.

## Run as a dev server (optional)

The dev source `index.html` references `lib/` assets, so serve it with the bundled
Flask app (or any static server). Convenient when you want to hot-edit `index.html`
and rebuild.

```bash
cd wind-turbine-verifier
pip install -r requirements.txt
python3 server.py            # http://127.0.0.1:8000
# or: bash start.sh           # creates a venv and starts on :8000
```

> Note: `index.html` expects `lib/pdfjs/*.js` to exist (download via build step).
> `wind-farm-verifier.html` is fully standalone and does not need these.

## Build the standalone file

```bash
python3 build.py             # -> wind-farm-verifier.html (single file, inlined assets)
```

Requires `lib/leaflet.js`, `lib/leaflet.css`, `lib/pdfjs/pdf.min.js`,
`lib/pdfjs/pdf.worker.min.js` to be present (provided in this repo).

## CSV format

Minimum columns (header names are case-insensitive aliases):

```csv
id,lat,lon
6403580001,37.3733,106.4133
```

Accepted aliases:
- **ID**: `wtid`, `id`, `turbine_id`
- **Latitude**: `lat`, `latitude`, `lat_corrected`, `corrected_lat`
- **Longitude**: `lon`, `longitude`, `lon_corrected`, `corrected_lon`

If the CSV already carries corrected coordinates, they are restored as the baseline.

## PDF import

Upload a turbine layout PDF. Coordinates are extracted **in-browser** with pdf.js
(no server needed) using the same pattern as before: a 4+ digit id followed by two
decimal coordinates (lat in [-90,90], lon in [-180,180]).

## Farm name

The farm name is editable in the top bar. It is derived from the uploaded file name
(unless you type your own) and used for **per-farm storage** and the export filename.
Nothing is auto-restored on load — upload your CSV/PDF each session.

## Status badges

| Badge | Meaning |
|-------|---------|
| `ok`  | deviation 0–20 m |
| `wn`  | deviation 20–100 m (Review) |
| `er`  | deviation > 100 m (Offset) |
| `na`  | not yet verified |

## Testing

Real browser end-to-end check (headless Chrome, requires Google Chrome installed):

```bash
npm install puppeteer-core
node test_e2e.js            # builds nothing; tests wind-farm-verifier.html
```

## Repository layout

```
index.html            # dev verifier UI (references lib/ assets)
wind-farm-verifier.html  # STANDALONE one-click deliverable (inlined assets)
build.py              # inlines assets -> wind-farm-verifier.html
test_e2e.js           # headless-Chrome end-to-end test
server.py             # optional Flask backend (legacy PDF path / static serve)
lib/                  # bundled Leaflet + pdf.js
analyze.py            # batch diagnostic vs OSM
auto_verify.py        # earlier classical-CV attempt (superseded)
requirements.txt
```

## Roadmap

- [x] Generalized, farm-agnostic manual verifier
- [x] One-click standalone HTML (in-browser PDF parsing, no server)
- [ ] **Separate repo** `gw640358-auto`: automated turbine detection from imagery (YOLO/SAM)
