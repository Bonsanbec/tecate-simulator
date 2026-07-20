import json
import bpy
import mathutils
import math

bpy.ops.wm.open_mainfile(filepath="models/tecate/osm2world.blend")
translation = mathutils.Vector((34975.75, -31878.95, 0.0))

excluded_materials = {
    'ASPHALT', 'ASPHALT.001', 'EARTH', 'GRAVEL', 'HEDGE', 
    'helipad_markings', 'PAVING_STONE', 'pitchTennis', 
    'RAIL_BALLAST', 'road_arrow_right', 'road_arrow_through', 
    'ROAD_MARKING', 'ROAD_MARKING.001', 'road_marking_crossing', 
    'road_marking_dash', 'RUNWAY_CENTER_MARKING', 'SAND', 
    'SCREE', 'TENNIS_NET', 'TERRAIN_DEFAULT', 'WATER'
}

original_collection = bpy.data.collections.get("Collection")
building_objs = []
for obj in original_collection.objects:
    if obj.type == 'MESH':
        is_excluded = False
        if len(obj.material_slots) == 0:
            is_excluded = True
        else:
            for slot in obj.material_slots:
                if slot.material and slot.material.name in excluded_materials:
                    is_excluded = True
                    break
        if not is_excluded:
            building_objs.append(obj)

print(f"Total building objects: {len(building_objs)}")

# Load blocks_cache.json
with open("data/blocks_cache.json", "r") as f:
    blocks = json.load(f)

# Precompute block centroids and polygons
block_data_processed = {}
for block_id, block_info in blocks.items():
    poly = block_info["polygon"]
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0
    block_data_processed[block_id] = {
        "minx": minx, "maxx": maxx, "miny": miny, "maxy": maxy,
        "cx": cx, "cy": cy, "poly": poly
    }

def point_in_poly(x, y, poly):
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

matched_exact = 0
matched_nearest = 0

mapping_results = {}

for i, obj in enumerate(building_objs):
    mw = obj.matrix_world
    bbox_world = [mw @ mathutils.Vector(corner) + translation for corner in obj.bound_box]
    bcx = sum(v.x for v in bbox_world) / len(bbox_world)
    bcy = sum(v.y for v in bbox_world) / len(bbox_world)
    
    # 1. Try exact polygon containment
    matched_id = None
    for block_id, binfo in block_data_processed.items():
        if binfo["minx"] - 5.0 <= bcx <= binfo["maxx"] + 5.0 and binfo["miny"] - 5.0 <= bcy <= binfo["maxy"] + 5.0:
            if point_in_poly(bcx, bcy, binfo["poly"]):
                matched_id = block_id
                matched_exact += 1
                break
                
    # 2. If not inside polygon, match to nearest block centroid
    if not matched_id:
        best_dist = float('inf')
        for block_id, binfo in block_data_processed.items():
            dist = math.hypot(bcx - binfo["cx"], bcy - binfo["cy"])
            if dist < best_dist:
                best_dist = dist
                matched_id = block_id
        if matched_id:
            matched_nearest += 1

    if matched_id:
        mapping_results[obj.name] = {
            "block_id": matched_id,
            "centroid": (bcx, bcy),
            "materials": [s.material.name for s in obj.material_slots if s.material]
        }

print(f"Exact polygon matches: {matched_exact}")
print(f"Nearest centroid matches: {matched_nearest}")
print(f"Total mapped buildings: {len(mapping_results)} / {len(building_objs)}")
print(f"Total unique manzanas mapped: {len(set(m['block_id'] for m in mapping_results.values()))}")

