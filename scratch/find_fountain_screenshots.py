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

print("=== EXACT SCREENSHOT NAMES IN CACHE WITHIN 50M (2009) ===")
screenshots = []
for fid, f in facades.items():
    pid = f.get("pano_id")
    p = panos.get(pid, {})
    plat = p.get("latitude")
    plon = p.get("longitude")
    if plat is None:
        continue
    x, y = gps_to_local(plat, plon)
    dist = math.hypot(x - tx, y - ty)
    date = str(p.get("date", ""))
    if dist < 50 and "2009" in date:
        bearing = (math.degrees(math.atan2(tx - x, ty - y)) + 360) % 360
        hdg = f.get("heading")
        cap_hdg = f.get("captured_heading")
        diff = abs((bearing - hdg + 180) % 360 - 180)
        # Format filename according to pipeline convention: {pano_id}_yaw_{hdg:.2f}.png
        fname = f"{pid}_yaw_{hdg:.2f}.png"
        screenshots.append({
            "fname": fname,
            "pano_id": pid,
            "dist": dist,
            "date": date,
            "hdg": hdg,
            "cap_hdg": cap_hdg,
            "bearing": bearing,
            "diff": diff,
            "facade_id": fid
        })

# Sort by diff (how directly it looks at the fountain) and dist
screenshots.sort(key=lambda s: (s["diff"], s["dist"]))
seen_fnames = set()
unique_screenshots = []
for s in screenshots:
    if s["fname"] not in seen_fnames:
        seen_fnames.add(s["fname"])
        unique_screenshots.append(s)

print(f"Total unique candidate screenshots: {len(unique_screenshots)}")
for s in unique_screenshots:
    print(f"{s['fname']} | Dist: {s['dist']:.1f}m | Hdg: {s['hdg']:.2f}° | Bearing: {s['bearing']:.1f}° | Diff: {s['diff']:.1f}° | Facade: {s['facade_id']}")
