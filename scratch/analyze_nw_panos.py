import json
import math
from src.core_io.coords import gps_to_local

target_lat = 32.573366
target_lon = -116.626902
tx, ty = gps_to_local(target_lat, target_lon)

with open("scratch/cache/panoramas_cache.json") as f:
    panos = json.load(f)

with open("scratch/cache/facades_cache.json") as f:
    facades = json.load(f)

print("--- PANORAMAS ON JUAREZ & CARDENAS (WEST & NORTH OF FOUNTAIN) ---")
cardenas_juarez_panos = []
for pid, p in panos.items():
    lat = p.get("latitude")
    lon = p.get("longitude")
    if lat is None or lon is None:
        continue
    x, y = gps_to_local(lat, lon)
    dist = math.hypot(x - tx, y - ty)
    if dist < 65:
        # Bearing from pano to fountain
        bearing = (math.degrees(math.atan2(tx - x, ty - y)) + 360) % 360
        # Find which facades use this pano
        fac_list = [f"{fid} (hdg {f['heading']:.1f})" for fid, f in facades.items() if f.get("pano_id") == pid]
        cardenas_juarez_panos.append({
            "pid": pid,
            "dist": dist,
            "date": p.get("date"),
            "x": x, "y": y,
            "lat": lat, "lon": lon,
            "bearing": bearing,
            "facades": fac_list
        })

cardenas_juarez_panos.sort(key=lambda p: (0 if "2009" in str(p["date"]) else 1, p["dist"]))
for p in cardenas_juarez_panos:
    print(f"Pano: {p['pid']} | {p['date']} | Dist: {p['dist']:.1f}m | Local: ({p['x']:.1f}, {p['y']:.1f}) | BearingToFtn: {p['bearing']:.1f}°")
    for f in p["facades"][:4]:
        print(f"    {f}")
