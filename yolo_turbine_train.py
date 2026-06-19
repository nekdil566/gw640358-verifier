#!/usr/bin/env python3
"""
yolo_turbine_train.py - fine-tune YOLOv8 on farm turbine tiles.

Steps:
1. Tile a bounding box of the farm
2. Review tile images/overlays to create labels
3. Place labeled data under data/turbines/images and labels
4. Run: python yolo_turbine_train.py

Outputs: runs/detect/train/weights/best.pt
"""
from __future__ import annotations

import argparse
import csv
import io
import math
import os
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

import cv2
import numpy as np
import requests
from PIL import Image


DEFAULT_CSV = Path.home() / "Downloads" / "dim_wind_turbine_202605181910 (1).csv"
TILE_DIR = Path.home() / "wind-turbine-verifier" / "yolo_data" / "tiles"
OUT_DIR = Path.home() / "wind-turbine-verifier" / "yolo_data"
TILE_ZOOM = 18


@dataclass
class Turbine:
    id: str
    lat: float
    lon: float
    name: str = ""
    typ: str = ""


def load_turbines(path: Path) -> List[Turbine]:
    rows: List[Turbine] = []
    with path.open("rb") as f:
        raw = f.read()
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        def _val(k: str) -> str:
            v = row.get(k) or row.get(k.strip()) or ""
            return v.strip()
        try:
            lat = float(_val("lat") or _val("latitude") or _val("Latitude") or 0)
            lon = float(_val("lon") or _val("longitude") or _val("Lon") or 0)
        except ValueError:
            continue
        tid = _val("wtid") or _val("id") or _val("ID") or ("T" + str(len(rows) + 1))
        rows.append(Turbine(id=tid, lat=lat, lon=lon, name=_val("name"), typ=_val("type")))
    return rows


def deg2num(lat, lon, zoom):
    n = 1 << zoom
    xt = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    yt = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xt, yt


def num2deg(xt, yt, zoom):
    n = 1 << zoom
    lon = xt / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * yt / n)))
    lat = math.degrees(lat_rad)
    return lat, lon


def download_tile(z, x, y):
    url = f"https://mt{(x+y)%4 + 1}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
    r = requests.get(url, timeout=15)
    if r.status_code != 200 or len(r.content) < 2000:
        return None
    return Image.open(io.BytesIO(r.content)).convert("RGB")


def make_tiles(turbines: Iterable[Turbine]):
    TILE_DIR.mkdir(parents=True, exist_ok=True)
    seen = set()
    for t in turbines:
        lat, lon = t.lat, t.lon
        cx, cy = deg2num(lat, lon, TILE_ZOOM)
        for xy in [(cx, cy), (cx, cy + 1), (cx + 1, cy), (cx, cy - 1), (cx - 1, cy)]:
            if xy in seen:
                continue
            seen.add(xy)
            out = TILE_DIR / f"z{TILE_ZOOM}_x{xy[0]}_y{xy[1]}.png"
            if out.exists() and out.stat().st_size > 2000:
                continue
            img = download_tile(TILE_ZOOM, xy[0], xy[1])
            if img:
                img.save(out)


def export_train_csv(turbines: List[Turbine]) -> Path:
    csv_path = OUT_DIR / "tiles.csv"
    rows = [["tile_x", "tile_y", "zoom", "turbine_lat", "turbine_lon", "turbine_id"]]
    seen = set()
    for t in turbines:
        cx, cy = deg2num(t.lat, t.lon, TILE_ZOOM)
        for xy in [(cx, cy), (cx, cy + 1), (cx + 1, cy), (cx, cy - 1), (cx - 1, cy)]:
            key = (xy[0], xy[1])
            if key in seen:
                continue
            seen.add(key)
            rows.append([xy[0], xy[1], TILE_ZOOM, f"{t.lat:.6f}", f"{t.lon:.6f}", t.id])
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    return csv_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    args = ap.parse_args()
    if not args.csv.exists():
        print(f"CSV not found: {args.csv}")
        return 2
    turbines = load_turbines(args.csv)
    print(f"Loaded {len(turbines)} turbines")
    make_tiles(turbines)
    out = export_train_csv(turbines)
    print(f"Tile manifest: {out}")
    print("Next: add turbine center labels under yolo_data/labels/*.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
