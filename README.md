# Farm 640358 · Manual Coordinate Verifier (v1.0)

A lightweight, local-first tool for **manually verifying and correcting wind-turbine
coordinates** against high-resolution satellite imagery (ArcGIS World Imagery), built
for Goldwind farm **640358** (55 turbines).

> This repo is **Path 1 — Manual verification**. The automated, image-based
> detection tool (YOLO / SAM) lives in a separate repository and is developed later.

## What it does

- Upload a turbine list as **CSV** or **PDF** (a turbine layout sheet)
- See every turbine on a satellite basemap
- Click a row → fly to the original location
- **✏️ Edit** → click the real turbine on the map → records corrected coordinates + deviation (meters)
- **OK** → confirm the original is correct (0 m)
- **↺ Reset** → clear a row to re-correct it
- **Undo** (⌘/Ctrl+Z) → revert the last correction
- Auto-advances to the next unverified turbine; live OK / Review / Offset KPIs
- Auto-saves to the browser; **Export** a re-importable corrected CSV

## Run it

The PDF import needs a tiny local server (browsers block PDF parsing on `file://`).

```bash
cd wind-turbine-verifier
pip install -r requirements.txt
python3 server.py            # http://127.0.0.1:8000
# or: bash start.sh           # creates a venv and starts on :8000
```

Then open `http://127.0.0.1:8000/`.

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

Upload a turbine layout PDF. The backend (`server.py`, `/api/import_pdf`) extracts
`wtid, lat, lon` rows via `pdfminer` and loads them. Pattern expected per line:
a 4+ digit id followed by two decimal coordinates (lat in [-90,90], lon in [-180,180]).

## Status badges

| Badge | Meaning |
|-------|---------|
| `ok`  | deviation 0–20 m |
| `wn`  | deviation 20–100 m (Review) |
| `er`  | deviation > 100 m (Offset) |
| `na`  | not yet verified |

## Batch diagnostics (separate script)

`analyze.py` cross-checks all 55 coordinates against OpenStreetMap `wind_turbine`
nodes and writes a farm-wide report (counts + max/avg/median deviation). This is the
**batch diagnostic** capability, distinct from per-turbine manual verification.

## Repository layout

```
index.html      # the verifier UI
server.py       # Flask backend (serves files + PDF import)
lib/            # bundled Leaflet (works offline)
analyze.py      # batch diagnostic vs OSM
auto_verify.py  # earlier classical-CV attempt (superseded by the auto repo)
requirements.txt
```

## Roadmap

- [x] Manual verifier (CSV + PDF, click-to-correct, export)
- [ ] **Separate repo** `gw640358-auto`: automated turbine detection from imagery (YOLO/SAM)
