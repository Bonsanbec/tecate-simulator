#!/usr/bin/env python3
import json
import os
import math
import sys

# Attempt to import bpy and mathutils if running inside Blender's python environment
try:
    import bpy
    import mathutils
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False

def run_mapping():
    if not HAS_BLENDER:
        print("Error: This script must be run inside Blender python environment.")
        print("Usage: blender --background --python scripts/1_map_buildings_to_manzanas.py")
        sys.exit(1)

    print("=" * 60)
    print("  STEP 1: BUILDING TO MANZANA SPATIAL MAPPING PIPELINE")
    print("=" * 60)

    blend_file = "models/tecate/osm2world.blend"
    blocks_file = "data/blocks_cache.json"
    osm_cache_file = "data/tecate_osm_cache.json"
    output_file = "data/building_manzana_mapping.json"
    translation = mathutils.Vector((34975.75, -31878.95, 0.0))

    if not os.path.exists(blend_file):
        print(f"Error: Blend file not found at {blend_file}")
        sys.exit(1)
        
    if not os.path.exists(blocks_file):
        print(f"Error: Blocks cache not found at {blocks_file}")
        sys.exit(1)

    # 1. Load Road/POI Spatial Index for Street Name Resolution
    street_segments = []
    if os.path.exists(osm_cache_file):
        print(f"[1/5] Extracting street name spatial index from {osm_cache_file}...")
        try:
            with open(osm_cache_file, "r") as f:
                osm_data = json.load(f)
            nodes = osm_data.get("nodes", {})
            edges = osm_data.get("edges", [])
            
            # Calibration constants for lat/lon -> local coords
            LAT_REF = 32.573229
            LON_REF = -116.626536
            METERS_PER_DEG_LAT = 110900.0
            METERS_PER_DEG_LON = 93800.0

            for e in edges:
                if isinstance(e, dict) and e.get("name"):
                    u_id = str(e.get("u"))
                    v_id = str(e.get("v"))
                    if u_id in nodes and v_id in nodes:
                        u_node = nodes[u_id]
                        v_node = nodes[v_id]
                        ux = (u_node["lon"] - LON_REF) * METERS_PER_DEG_LON
                        uy = (u_node["lat"] - LAT_REF) * METERS_PER_DEG_LAT
                        vx = (v_node["lon"] - LON_REF) * METERS_PER_DEG_LON
                        vy = (v_node["lat"] - LAT_REF) * METERS_PER_DEG_LAT
                        street_segments.append({
                            "name": e["name"],
                            "mid": ((ux + vx) / 2.0, (uy + vy) / 2.0)
                        })
            print(f"  Loaded {len(street_segments)} named street segments.")
        except Exception as e:
            print(f"  [Warning] Could not parse street names from OSM cache: {e}")

    def resolve_street_name(x, y):
        if not street_segments:
            return "Tecate Sector"
        best_dist = float('inf')
        best_name = "Avenida Tecate"
        for s in street_segments:
            mx, my = s["mid"]
            d = math.hypot(x - mx, y - my)
            if d < best_dist:
                best_dist = d
                best_name = s["name"]
        return best_name

    # 2. Open Blender file and filter building objects
    print(f"[2/5] Loading {blend_file}...")
    bpy.ops.wm.open_mainfile(filepath=blend_file)

    excluded_materials = {
        'ASPHALT', 'ASPHALT.001', 'EARTH', 'GRAVEL', 'HEDGE', 
        'helipad_markings', 'PAVING_STONE', 'pitchTennis', 
        'RAIL_BALLAST', 'road_arrow_right', 'road_arrow_through', 
        'ROAD_MARKING', 'ROAD_MARKING.001', 'road_marking_crossing', 
        'road_marking_dash', 'RUNWAY_CENTER_MARKING', 'SAND', 
        'SCREE', 'TENNIS_NET', 'TERRAIN_DEFAULT', 'WATER'
    }

    print("[3/5] Filtering building objects...")
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

    print(f"  Found {len(building_objs)} building mesh primitives.")

    # 3. Load manzana blocks
    print(f"[4/5] Loading manzana blocks from {blocks_file}...")
    with open(blocks_file, "r") as f:
        blocks = json.load(f)

    block_data_processed = {}
    for block_id, block_info in blocks.items():
        poly = block_info.get("polygon", [])
        if not poly:
            continue
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

    # 4. Map primitives and group by building entity per manzana
    print("[5/5] Mapping building primitives to manzanas & assigning spatial labels...")
    mapping_results = {}
    manzana_to_buildings = {}

    exact_count = 0
    nearest_count = 0

    for obj in building_objs:
        mw = obj.matrix_world
        bbox_world = [mw @ mathutils.Vector(corner) + translation for corner in obj.bound_box]
        bcx = sum(v.x for v in bbox_world) / len(bbox_world)
        bcy = sum(v.y for v in bbox_world) / len(bbox_world)
        bcz_min = min(v.z for v in bbox_world)
        bcz_max = max(v.z for v in bbox_world)
        height = bcz_max - bcz_min

        # Match manzana block
        matched_id = None
        for block_id, binfo in block_data_processed.items():
            if binfo["minx"] - 2.0 <= bcx <= binfo["maxx"] + 2.0 and binfo["miny"] - 2.0 <= bcy <= binfo["maxy"] + 2.0:
                if point_in_poly(bcx, bcy, binfo["poly"]):
                    matched_id = block_id
                    exact_count += 1
                    break

        if not matched_id:
            best_dist = float('inf')
            for block_id, binfo in block_data_processed.items():
                dist = math.hypot(bcx - binfo["cx"], bcy - binfo["cy"])
                if dist < best_dist:
                    best_dist = dist
                    matched_id = block_id
            if matched_id:
                nearest_count += 1

        materials = [s.material.name for s in obj.material_slots if s.material]
        street_name = resolve_street_name(bcx, bcy)

        building_info = {
            "building_name": obj.name,
            "street_name": street_name,
            "manzana_id": matched_id,
            "centroid": [round(bcx, 3), round(bcy, 3), round(bcz_min, 3)],
            "height": round(height, 2),
            "materials": materials
        }

        mapping_results[obj.name] = building_info

        if matched_id not in manzana_to_buildings:
            manzana_to_buildings[matched_id] = []
        manzana_to_buildings[matched_id].append(building_info)

    output_payload = {
        "summary": {
            "total_buildings": len(building_objs),
            "exact_polygon_matches": exact_count,
            "nearest_centroid_matches": nearest_count,
            "unique_manzanas": len(manzana_to_buildings)
        },
        "buildings": mapping_results,
        "manzanas": manzana_to_buildings
    }

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(output_payload, f, indent=2)

    print(f"Mapping complete!")
    print(f"  Exact matches: {exact_count}")
    print(f"  Nearest matches: {nearest_count}")
    print(f"  Total unique manzanas: {len(manzana_to_buildings)}")
    print(f"  Saved output to: {output_file}")
    print("=" * 60)

if __name__ == "__main__":
    run_mapping()
