import json
import math
from src.core_io.coords import gps_to_local

target_lat = 32.573366
target_lon = -116.626902
target_x, target_y = gps_to_local(target_lat, target_lon)

with open("scratch/cache/facades_cache.json") as f:
    facades = json.load(f)

with open("scratch/cache/panoramas_cache.json") as f:
    panos = json.load(f)

with open("scratch/cache/blocks_cache.json") as f:
    blocks = json.load(f)

# Find all facades of the park
park_block = "block_lat_32.57293_lon_-116.62685"
print(f"Target Fountain: ({target_lat}, {target_lon}) -> local x={target_x:.2f}, y={target_y:.2f}")

fountain_candidates = []
for fac_id, fac in facades.items():
    pid = fac.get("pano_id")
    p = panos.get(pid, {})
    plat = p.get("latitude")
    plon = p.get("longitude")
    if plat is None:
        continue
    px, py = gps_to_local(plat, plon)
    dist = math.hypot(px - target_x, py - target_y)
    if dist < 60:
        # compute angle from pano to fountain
        # Bearing from North: dx = target_x - px, dy = target_y - py
        bearing_to_fountain = (math.degrees(math.atan2(target_x - px, target_y - py)) + 360) % 360
        heading = fac.get("heading", 0)
        angle_diff = abs((bearing_to_fountain - heading + 180) % 360 - 180)
        fountain_candidates.append({
            "facade_id": fac_id,
            "pano_id": pid,
            "dist": dist,
            "date": p.get("date"),
            "pano_x": px,
            "pano_y": py,
            "heading": heading,
            "captured_heading": fac.get("captured_heading"),
            "bearing_to_fountain": bearing_to_fountain,
            "angle_diff": angle_diff
        })

print(f"\nTotal facades within 60m of fountain: {len(fountain_candidates)}")
# Sort by date (preferring 2009) and then dist
fountain_candidates.sort(key=lambda c: (0 if "2009" in str(c["date"]) else 1, c["dist"], c["angle_diff"]))

seen_panos = set()
for c in fountain_candidates:
    key = (c["pano_id"], round(c["heading"], 1))
    if key in seen_panos:
        continue
    seen_panos.add(key)
    print(f"Pano: {c['pano_id']} | Date: {c['date']} | Dist: {c['dist']:.1f}m | Heading: {c['heading']:.1f}° | BearingToFountain: {c['bearing_to_fountain']:.1f}° | Diff: {c['angle_diff']:.1f}° | Facade: {c['facade_id']}")
