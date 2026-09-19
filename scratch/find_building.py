import json
import math
import re

target_lat = 32.572763
target_lon = -116.626927

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# 1. Blocks
print("=== 1. BUSCANDO MANZANAS CERCANAS ===")
with open("scratch/cache/blocks_cache.json", "r") as f:
    blocks = json.load(f)

pattern = re.compile(r"block_lat_([-\d.]+)_lon_([-\d.]+)")

nearby_blocks = []
for block_id, data in blocks.items():
    m = pattern.match(block_id)
    if not m:
        continue
    blat = float(m.group(1))
    blon = float(m.group(2))
    dist = haversine(target_lat, target_lon, blat, blon)
    if dist < 120:
        nearby_blocks.append((dist, block_id, data, blat, blon))

nearby_blocks.sort(key=lambda x: x[0])
print(f"Total bloques dentro de 120m: {len(nearby_blocks)}")
for dist, b_id, data, blat, blon in nearby_blocks[:15]:
    print(f"Block: {b_id} | Dist: {dist:.1f}m | Area: {data.get('area_sq_meters')}m2 | Height: {data.get('height_meters')}")

# 2. Panoramas
print("\n=== 2. BUSCANDO PANORAMAS CERCANOS (2009) ===")
with open("scratch/cache/panoramas_cache.json", "r") as f:
    panos = json.load(f)

nearby_panos = []
for p_id, p_data in panos.items():
    lat = p_data.get("latitude")
    lon = p_data.get("longitude")
    if lat is None or lon is None:
        continue
    dist = haversine(target_lat, target_lon, lat, lon)
    if dist < 80:
        nearby_panos.append((dist, p_id, p_data))

nearby_panos.sort(key=lambda x: x[0])
print(f"Total panoramas dentro de 80m: {len(nearby_panos)}")
for dist, p_id, p_data in nearby_panos:
    date = p_data.get("date", "")
    road = p_data.get("road_name", "")
    yaw = p_data.get("projection_yaw")
    pyaw = p_data.get("pano_yaw")
    print(f"Pano: {p_id} | Dist: {dist:.1f}m | Date: {date} | Road: {road} | Lat/Lon: ({p_data['latitude']:.6f}, {p_data['longitude']:.6f}) | Yaw: {yaw}")

# 3. Facades
print("\n=== 3. BUSCANDO FACHADAS ASOCIADAS ===")
with open("scratch/cache/facades_cache.json", "r") as f:
    facades = json.load(f)

for dist, b_id, data, blat, blon in nearby_blocks[:5]:
    matching_facades = {k: v for k, v in facades.items() if k.startswith(b_id)}
    print(f"\nFachadas para {b_id} (Dist {dist:.1f}m): {len(matching_facades)} encontradas")
    for f_id, f_data in matching_facades.items():
        p_id = f_data.get('pano_id')
        p_info = panos.get(p_id, {})
        print(f"  {f_id} -> Pano: {p_id} ({p_info.get('date')}) | Heading: {f_data.get('heading')} | CapHeading: {f_data.get('captured_heading')}")
