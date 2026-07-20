import json
import bpy
import mathutils
import sys
import os

sys.path.append(os.path.abspath("scripts"))
from spatial import minecraft_to_gps_2d, gps_to_local, local_to_gps

# 1. Inspect blocks_cache.json coordinates
with open("data/blocks_cache.json", "r") as f:
    blocks = json.load(f)

print("--- Testing Spatial & Blocks Cache ---")
for block_id in list(blocks.keys())[:5]:
    poly = blocks[block_id]["polygon"]
    # block_id is e.g. block_lat_32.56181_lon_-116.57077
    parts = block_id.split("_")
    lat = float(parts[2])
    lon = float(parts[4])
    x_local, y_local = gps_to_local(lat, lon)
    print(f"Block ID: {block_id}")
    print(f"  Encoded Lat/Lon: ({lat}, {lon}) -> Local GPS (x_local={x_local:.2f}, y_local={y_local:.2f})")
    print(f"  Minecraft 2D (x={x_local:.2f}, z={-y_local:.2f})")
    print(f"  Polygon sample point 0: {poly[0]}")

print("\n--- Inspecting Blender building mesh bounds ---")
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

for obj in building_objs[:5]:
    # Compute world AABB
    world_verts = [obj.matrix_world @ v.co + translation for v in obj.data.vertices]
    min_x = min(v.x for v in world_verts)
    max_x = max(v.x for v in world_verts)
    min_y = min(v.y for v in world_verts) # Blender Y
    max_y = max(v.y for v in world_verts)
    min_z = min(v.z for v in world_verts) # Altitude / Z
    max_z = max(v.z for v in world_verts)
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    print(f"Obj {obj.name}: Center (X={center_x:.2f}, Y={center_y:.2f}, Z={center_z if 'center_z' in locals() else (min_z+max_z)/2:.2f})")

