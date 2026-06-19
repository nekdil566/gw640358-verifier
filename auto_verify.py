#!/usr/bin/env python3
"""auto_verify.py - wind turbine coordinate verification via satellite imagery.

For each turbine in CSV:
1. Download a small patch of Google Satellite tiles
2. Run classical CV detection to find bright circular objects (turbines)
3. Compare detected position to recorded coordinates
4. Output corrected CSV

Requires:
  requests, Pillow, numpy, opencv-python-headless
"""

from __future__ import annotations

import argparse
import csv as csv_mod
import io
import math
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
import requests
from PIL import Image


# ---- config defaults -------------------------------------------------------
DEFAULT_CSV = Path.home() / "Downloads" / "dim_wind_turbine_202605181910 (1).csv"
TILE_DIR = Path("/tmp/sat_tiles")
TILE_DIR.mkdir(parents=True, exist_ok=True)
TILE_ZOOM = 18  # high enough to see turbines
SEARCH_RADIUS_M = 120  # patch half-width around recorded center


# ---- data ------------------------------------------------------------------

@dataclass
class Turbine:
    id: str
    lat: float
    lon: float
    name: str = ""
    typ: str = ""
    ref_lat: Optional[float] = None
    ref_lon: Optional[float] = None
    dist_m: Optional[float] = None
    status: str = "Pending"


# ---- tile math -------------------------------------------------------------

MAX_ZOOM = 20
RACK_URL_TMPL = "https://mt{session}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"


def deg2num(lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
    n = 1 << zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat_deg)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile


def num2deg(xtile: int, ytile: int, zoom: int) -> Tuple[float, float]:
    n = 1 << zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg


def meters_per_pixel(lat: float, zoom: int) -> float:
    return 156543.03392 * math.cos(math.radians(lat)) / (2 ** zoom)


# ---- fetch / stitch --------------------------------------------------------

def _session_num(x: int, y: int) -> int:
    return ((x + y) % 4) + 1


def fetch_tile(zoom: int, x: int, y: int) -> Optional[np.ndarray]:
    s = _session_num(x, y)
    url = f"https://mt{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={zoom}"
    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "GoldwindVerifier/1.0"})
        if r.status_code != 200 or len(r.content) < 2000:
            return None
        img = Image.open(io.BytesIO(r.content)).convert("RGB")
        arr = np.array(img)[:, :, ::-1].copy()
        return arr
    except requests.RequestException:
        return None


def _tile_cache_path(x: int, y: int, z: int) -> Path:
    return TILE_DIR / f"z{z}_x{x}_y{y}.png"


def get_tile(zoom: int, x: int, y: int) -> Optional[np.ndarray]:
    p = _tile_cache_path(x, y, zoom)
    if p.exists() and p.stat().st_size > 2000:
        try:
            return cv2.imread(str(p), cv2.IMREAD_COLOR)
        except Exception:
            pass
    img = fetch_tile(zoom, x, y)
    if img is not None:
        try:
            cv2.imwrite(str(p), img)
        except Exception:
            pass
    return img


def stitch_tiles(center_lat: float, center_lon: float, radius_m: float, zoom: int) -> Tuple[Optional[np.ndarray], dict]:
    cx, cy = deg2num(center_lat, center_lon, zoom)
    mpp = meters_per_pixel(center_lat, zoom)
    half = max(1, int(math.ceil(radius_m / (256.0 * mpp))))
    rows = []
    meta: dict = {"cx": cx, "cy": cy, "half": half, "zoom": zoom, "mpp": mpp}
    for yy in range(cy - half, cy + half + 1):
        row = []
        for xx in range(cx - half, cx + half + 1):
            row.append(get_tile(zoom, xx, yy))
        rows.append(row)
    if any(t is None for row in rows for t in row):
        return None, meta
    stitched = np.vstack([np.hstack(row) for row in rows])
    return stitched, meta


# ---- detection -------------------------------------------------------------

def _preprocess(img_bgr: np.ndarray) -> np.ndarray:
    small = cv2.resize(img_bgr, (1024, 1024), interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    lab2 = cv2.merge((l2, a, b))
    out = cv2.cvtColor(lab2, cv2.COLOR_LAB2BGR)
    gray = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 1.2)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    tophat = cv2.morphologyEx(blur, cv2.MORPH_TOPHAT, kernel)
    combined = cv2.addWeighted(blur, 0.65, tophat, 0.35, 0)
    return combined


def _detect(img_gray: np.ndarray) -> List[cv2.KeyPoint]:
    detector = cv2.ORB_create(nfeatures=1200, scaleFactor=1.25, nlevels=6)
    try:
        kps = detector.detect(img_gray, None)
    except cv2.error:
        kps = []
    return kps


def _nearest_match(kps: List[cv2.KeyPoint], cx: float, cy: float) -> Optional[Tuple[float, float]]:
    if not kps:
        return None
    best, best_d = None, 1e18
    for kp in kps:
        d = (kp.pt[0] - cx) ** 2 + (kp.pt[1] - cy) ** 2
        if d < best_d:
            best_d, best = d, kp
    return best.pt if best else None


def detect_turbine_center(preprocessed: np.ndarray, fallback_center: Tuple[float, float]) -> Optional[Tuple[float, float]]:
    pts = _detect(preprocessed)
    if not pts:
        return None
    hit = _nearest_match(pts, fallback_center[0], fallback_center[1])
    if hit is None:
        return None
    d = math.hypot(hit[0] - fallback_center[0], hit[1] - fallback_center[1])
    max_r = 180.0
    if d > max_r:
        return None
    return hit


# ---- pipeline --------------------------------------------------------------

def load_csv(path: Path) -> List[Turbine]:
    rows: List[Turbine] = []
    with path.open("rb") as f:
        raw = f.read()
    text = raw.decode("utf-8-sig", errors="replace")
    reader = csv_mod.DictReader(io.StringIO(text))
    for row in reader:
        def _val(k: str) -> Optional[str]:
            v = row.get(k) or row.get(k.strip()) or ""
            return v.strip()
        try:
            lat = float(_val("lat") or _val("latitude") or _val("Latitude") or 0)
            lon = float(_val("lon") or _val("longitude") or _val("Lon") or 0)
        except ValueError:
            continue
        tid = _val("wtid") or _val("id") or _val("ID") or ("T" + str(len(rows) + 1))
        name = _val("name") or _val("Name") or ""
        typ = _val("type") or _val("Type") or ""
        rows.append(Turbine(id=tid, lat=lat, lon=lon, name=name, typ=typ))
    return rows


def process(turbines: List[Turbine]) -> List[Turbine]:
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=2, pool_connections=4, pool_maxsize=4)
    session.mount("https://", adapter)

    for idx, t in enumerate(turbines, 1):
        print(f"[{idx}/{len(turbines)}] {t.id} @ {t.lat:.5f}, {t.lon:.5f}")
        patch, meta = stitch_tiles(t.lat, t.lon, SEARCH_RADIUS_M, TILE_ZOOM)
        if patch is None:
            t.status = "Review"
            t.ref_lat, t.ref_lon = t.lat, t.lon
            continue
        cx = (meta["half"] * 256) + (meta["cx"] % 1) * 256
        cy = (meta["half"] * 256) + (meta["cy"] % 1) * 256
        pre = _preprocess(patch)
        hit = detect_turbine_center(pre, (cx, cy))
        if hit is not None:
            scale = meta["mpp"] / (256.0 / patch.shape[0])
            dx = (hit[0] - cx) * scale
            dy = (hit[1] - cy) * scale
            dlat = dy / 111320.0
            dlon = dx / (111320.0 * math.cos(math.radians(t.lat)))
            clat, clon = t.lat + dlat, t.lon + dlon
            t.ref_lat, t.ref_lon = clat, clon
            t.dist_m = math.hypot(dx, dy)
            t.status = "OK" if t.dist_m < 20.0 else ("Review" if t.dist_m <= 100.0 else "Offset")
        else:
            t.ref_lat, t.ref_lon = t.lat, t.lon
            t.status = "Offset"
        print(f"     -> {t.status} {t.dist_m if t.dist_m is not None else 'n/a'}")
    return turbines


def export_csv(turbines: List[Turbine], out: Path) -> None:
    with out.open("w", newline="", encoding="utf-8") as f:
        f.write("\ufeff")
        w = csv_mod.writer(f)
        w.writerow(["id", "type", "lat_original", "lon_original", "lat_corrected", "lon_corrected", "distance_m", "status"])
        for t in turbines:
            w.writerow([
                t.id,
                (t.typ or "").replace(",", " "),
                f"{t.lat:.6f}",
                f"{t.lon:.6f}",
                f"{t.ref_lat:.6f}" if t.ref_lat is not None else "",
                f"{t.ref_lon:.6f}" if t.ref_lon is not None else "",
                f"{t.dist_m:.2f}" if t.dist_m is not None else "",
                t.status,
            ])
    print(f"Exported {len(turbines)} rows to {out}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    ap.add_argument("--out", type=Path, default=Path("GW-640358-verified.csv"))
    args = ap.parse_args()

    if not args.csv.exists():
        print(f"CSV not found: {args.csv}")
        return 2

    turbines = load_csv(args.csv)
    if not turbines:
        print("No turbines loaded")
        return 2

    process(turbines)
    export_csv(turbines, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
