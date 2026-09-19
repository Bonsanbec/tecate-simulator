import json
import math
from src.core_io.coords import gps_to_local

target_lat = 32.573366
target_lon = -116.626902

dx, dy = gps_to_local(target_lat, target_lon)
print(f"Target local coords relative to Kiosco (0,0): dx = {dx:.2f} m (East), dy = {dy:.2f} m (North)")

with open("scratch/cache/panoramas_cache.json", "r") as f:
    panos = json.load(f)

# Look at panos on the streets bounding Parque Hidalgo
for p_id in [
    "iC5pdw4_s0duwq6JUPlyQw", "PkH0zOLyx3_u9xCFGGbWog", "kpS2nz7jqX2fLtV-gx3n0Q",
    "aNGj8-qOWUNuMxPPGtCdag", "jCGZyZTu0qmivh-MdNyxJA", "PrEbeatItmtZ2ymfflTl0w",
    "rylIDyzHWu3yI9gXza7M5g", "NMwyXMgDo3P_G-_Ki0FQwQ"
]:
    p = panos.get(p_id, {})
    p_lat = p.get("latitude")
    p_lon = p.get("longitude")
    p_dx, p_dy = gps_to_local(p_lat, p_lon)
    print(f"Pano {p_id}: local ({p_dx:.1f}, {p_dy:.1f}), date={p.get('date')}, pano_yaw={p.get('pano_yaw')}, projection_yaw={p.get('projection_yaw')}")
