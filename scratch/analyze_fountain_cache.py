import json
import math
import re

target_lat = 32.573366
target_lon = -116.626902

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

print("=== 1. ANALIZANDO MANZANAS CERCANAS A LA FUENTE ===")
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
    if dist < 150:
        nearby_blocks.append((dist, block_id, data, blat, blon))

nearby_blocks.sort(key=lambda x: x[0])
for dist, b_id, data, blat, blon in nearby_blocks[:10]:
    print(f"Block: {b_id} | Dist: {dist:.1f}m | Area: {data.get('area_sq_meters')}m2 | Height: {data.get('height_meters')}")

print("\n=== 2. ANALIZANDO PANORAMAS CERCANOS A LA FUENTE ===")
with open("scratch/cache/panoramas_cache.json", "r") as f:
    panos = json.load(f)

nearby_panos = []
for p_id, p_data in panos.items():
    lat = p_data.get("latitude")
    lon = p_data.get("longitude")
    if lat is None or lon is None:
        continue
    dist = haversine(target_lat, target_lon, lat, lon)
    if dist < 120:
        nearby_panos.append((dist, p_id, p_data))

nearby_panos.sort(key=lambda x: x[0])
print(f"Total panoramas dentro de 120m: {len(nearby_panos)}")
for dist, p_id, p_data in nearby_panos[:30]:
    date = p_data.get("date", "")
    road = p_data.get("road_name", "")
    pyaw = p_data.get("projection_yaw", p_data.get("pano_yaw"))
    plat = p_data.get("latitude")
    plon = p_data.get("longitude")
    print(f"Pano: {p_id} | Dist: {dist:.1f}m | Date: {date} | Road: {road} | ({plat:.6f}, {plon:.6f}) | Yaw: {pyaw}")

print("\n=== 3. DETALLES DE PANORAMAS 2009 CERCANOS ===")
panos_2009 = [p for p in nearby_panos if "2009" in str(p[2].get("date", ""))]
print(f"Total panoramas 2009 dentro de 120m: {len(panos_2009)}")
for dist, p_id, p_data in panos_2009:
    date = p_data.get("date", "")
    road = p_data.get("road_name", "")
    pyaw = p_data.get("projection_yaw", p_data.get("pano_yaw"))
    plat = p_data.get("latitude")
    plon = p_data.get("longitude")
    # compute bearing from panorama to target
    dlon = math.radians(target_lon - plon)
    y = math.sin(dlon) * math.cos(math.radians(target_lat))
    x = math.cos(math.radians(plat)) * math.sin(math.radians(target_lat)) - math.sin(math.radians(plat)) * math.cos(math.radians(target_lat)) * math.cos(dlon)
    bearing_to_target = (math.degrees(math.atan2(y, x)) + 360) % 360
    print(f"Pano: {p_id} | Dist: {dist:.1f}m | Date: {date} | Road: {road} | ({plat:.6f}, {plon:.6f}) | BearingToFountain: {bearing_to_target:.1f} deg")
