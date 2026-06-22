# Farm 640358 · Manual Coordinate Verifier

Lightweight browser tool for manually verifying and correcting wind turbine coordinates for Farm 640358. No installation, no dependencies, no cloud service. Runs entirely from a local HTML file.

## What it does

- Upload a turbine CSV
- See all turbines on a satellite basemap
- Click any row to fly to the original location
- Edit a row to place a corrected marker on the map
- Mark turbines as OK if the original location is correct
- Reset a row to re-correct it later
- Export a corrected CSV with updated coordinates and deviations

## How to run

```bash
cd /Users/nekdilkhan/wind-turbine-verifier
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open: `http://localhost:8000/index.html`

If you already have something running on 8000, try 9000:

```bash
python3 -m http.server 9000 --bind 127.0.0.1
```

## How to use

1. **Open the tool** — the page starts empty
2. **Upload CSV** — click `Upload CSV` and select your turbine CSV
   - Accepted headers (case-insensitive): `wtid`, `id`, `turbine_id`, `lat`, `latitude`, `Latitude`, `lon`, `longitude`, `Longitude`
   - If the CSV already has `lat_corrected` / `lon_corrected`, those are used as the original coordinates
3. **Review turbines** — the table shows:
   - **Original** — coordinates from the uploaded CSV
   - **Corrected** — empty until you edit
   - **Dist** — empty until you edit
   - **Actions** — Edit, OK, Reset
4. **Edit a turbine**
   - Click **✏️ Edit** in the Actions column
   - The pin at the top-left changes to: *"Click map at actual turbine"*
   - Click the exact turbine position on the map
   - A red corrected marker and connecting line appear
   - Corrected lat/lon and deviation in meters are saved immediately
5. **Mark OK**
   - Click **OK** if the original location is already correct
   - Corrected coordinates are set to the original values
   - Deviation is recorded as `0 m`
   - Status is set to `ok`
6. **Reset a row**
   - Click **↺ Reset** to clear corrections for that turbine
   - The row returns to the unedited state so you can re-correct it
7. **Export corrected CSV**
   - Click `Export corrected CSV`
   - The file downloads with columns: `id,original_lat,original_lon,corrected_lat,corrected_lon,deviation_m,status`
   - You can import this same CSV later and all corrected positions will be preserved

## CSV format

Minimum required columns:
```
id,lat,lon
6403580001,37.3733,106.4133
6403580002,37.3700,106.4058
```

The importer also accepts these header aliases:
- ID: `wtid`, `id`, `turbine_id`
- Latitude: `lat`, `latitude`, `Latitude`, `lat_corrected`, `corrected_lat`
- Longitude: `lon`, `longitude`, `Longitude`, `lon_corrected`, `corrected_lon`

The file is UTF-8 with BOM safe.

## Status badges

- `ok` — deviation is 0 m or within 20 m
- `wn` — deviation is 20–100 m
- `er` — deviation is over 100 m

## Tips

- Each row is independent — click **Edit** on one turbine, correct it on the map, then move to the next
- The map remembers your corrections for the current session
- Use **Reset** if you click the wrong spot and want to redo just that one turbine
- The export file is re-importable — upload it later and all corrected positions come back

## Repository

GitHub: https://github.com/nekdil566/gw640358-verifier
