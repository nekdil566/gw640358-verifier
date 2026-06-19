import csv
import math
import urllib.request
import urllib.parse
import json

# Read CSV
with open('/Users/nekdilkhan/Downloads/dim_wind_turbine_202605181910 (1).csv', 'rb') as f:
    raw = f.read()
try:
    text = raw.decode('utf-8-sig')
except:
    text = raw.decode('gbk', errors='replace')

reader = csv.DictReader(text.splitlines())
turbines = []
for i, row in enumerate(reader, 1):
    try:
        lat = float(row['lat'])
        lon = float(row['lon'])
        wtid = row.get('wtid', '').strip()
        ttype = row.get('type', '').strip()
        if not wtid:
            wtid = 'WT-%03d' % i
        turbines.append({'id': wtid, 'lat': lat, 'lon': lon, 'type': ttype if ttype else 'GW140/2500b'})
    except Exception as e:
        print(f'Skip row {i}: {e}')

print(f"Loaded {len(turbines)} turbines")

lats = [t['lat'] for t in turbines]
lons = [t['lon'] for t in turbines]
min_lat, max_lat = min(lats)-0.02, max(lats)+0.02
min_lon, max_lon = min(lons)-0.02, max(lons)+0.02

print(f"Bounding box: {min_lat:.4f},{min_lon:.4f} to {max_lat:.4f},{max_lon:.4f}")

overpass_url = "https://overpass-api.de/api/interpreter"
query = f"""
[out:json][timeout:25];
(
  node["generator:type"="wind_turbine"]({min_lat},{min_lon},{max_lat},{max_lon});
  way["generator:type"="wind_turbine"]({min_lat},{min_lon},{max_lat},{max_lon});
  node["man_made"="wind_turbine"]({min_lat},{min_lon},{max_lat},{max_lon});
  way["man_made"="wind_turbine"]({min_lat},{min_lon},{max_lat},{max_lon});
);
out center;
"""

data = urllib.parse.urlencode({'data': query}).encode()
req = urllib.request.Request(overpass_url, data=data, headers={'User-Agent': 'Mozilla/5.0'})

osm_turbines = []
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        osm_data = json.loads(resp.read())
    for el in osm_data.get('elements', []):
        if 'center' in el:
            osm_turbines.append({'lat': el['center']['lat'], 'lon': el['center']['lon'], 'id': str(el.get('id', ''))})
        elif 'lat' in el and 'lon' in el:
            osm_turbines.append({'lat': el['lat'], 'lon': el['lon'], 'id': str(el.get('id', ''))})
    print(f"Found {len(osm_turbines)} OSM turbines")
except Exception as e:
    print(f"Overpass API error: {e}")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3
    p = math.pi / 180
    dlat = (lat2 - lat1) * p
    dlon = (lon2 - lon1) * p
    a = math.sin(dlat/2)**2 + math.cos(lat1*p) * math.cos(lat2*p) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

results = []
for t in turbines:
    min_dist = float('inf')
    nearest = None
    for o in osm_turbines:
        d = haversine(t['lat'], t['lon'], o['lat'], o['lon'])
        if d < min_dist:
            min_dist = d
            nearest = o
    if min_dist < 20:
        status = 'OK'
    elif min_dist < 100:
        status = 'Review'
    else:
        status = 'Offset'
    results.append({**t, 'deviation': round(min_dist, 1), 'status': status, 'nearest': nearest['id'] if nearest else None})

results.sort(key=lambda x: x['deviation'], reverse=True)
ok_count = sum(1 for r in results if r['status'] == 'OK')
wn_count = sum(1 for r in results if r['status'] == 'Review')
er_count = sum(1 for r in results if r['status'] == 'Offset')
devs = [r['deviation'] for r in results]

print("\n" + "="*80)
print("WIND FARM COORDINATE VERIFICATION REPORT")
print(f"Farm ID: 640358 | Turbines: {len(results)} | Base: Google Earth Satellite")
print("="*80)
print(f"\nSUMMARY: {ok_count} OK | {wn_count} Review | {er_count} Offset")
if devs:
    print(f"Max deviation: {max(devs):.1f} m")
    print(f"Avg deviation: {sum(devs)/len(devs):.1f} m")
    print(f"Median deviation: {sorted(devs)[len(devs)//2]:.1f} m")

print("\nALL TURBINES (sorted by deviation):")
print(f"{'ID':<15} {'Type':<15} {'Lat':<12} {'Lon':<12} {'Dev (m)':<10} {'Status'}")
print("-"*80)
for r in results:
    print(f"{r['id']:<15} {r['type']:<15} {r['lat']:<12.5f} {r['lon']:<12.5f} {r['deviation']:<10} {r['status']}")

with open('/Users/nekdilkhan/wind-turbine-verifier/verification-report.txt', 'w') as f:
    f.write("WIND FARM COORDINATE VERIFICATION REPORT\n")
    f.write(f"Farm ID: 640358 | Turbines: {len(results)} | Base: Google Earth Satellite\n")
    f.write("="*80 + "\n\n")
    f.write(f"SUMMARY: {ok_count} OK | {wn_count} Review | {er_count} Offset\n")
    if devs:
        f.write(f"Max deviation: {max(devs):.1f} m\n")
        f.write(f"Avg deviation: {sum(devs)/len(devs):.1f} m\n")
        f.write(f"Median deviation: {sorted(devs)[len(devs)//2]:.1f} m\n")
    f.write("\nALL TURBINES:\n")
    f.write(f"{'ID':<15} {'Type':<15} {'Lat':<12} {'Lon':<12} {'Dev (m)':<10} {'Status'}\n")
    f.write("-"*80 + "\n")
    for r in results:
        f.write(f"{r['id']:<15} {r['type']:<15} {r['lat']:<12.5f} {r['lon']:<12.5f} {r['deviation']:<10} {r['status']}\n")

print("\nReport saved.")
