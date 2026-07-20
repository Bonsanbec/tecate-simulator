import json
import bpy
import mathutils

# 1. Blocks cache BBox
with open("data/blocks_cache.json", "r") as f:
    blocks = json.load(f)

block_min_x = block_min_y = float('inf')
block_max_x = block_max_y = float('-inf')

for block_id, block_data in blocks.items():
    poly = block_data["polygon"]
    for x, y in poly:
        block_min_x = min(block_min_x, x)
        block_max_x = max(block_max_x, x)
        block_min_y = min(block_min_y, y)
        block_max_y = max(block_max_y, y)

print("Blocks Cache BBox (Local coordinates):")
print(f"  X: [{block_min_x:.2f}, {block_max_x:.2f}]")
print(f"  Y: [{block_min_y:.2f}, {block_max_y:.2f}]")

# 2. OSM2World buildings BBox
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
b_min_x = b_min_y = float('inf')
b_max_x = b_max_y = float('-inf')

b_raw_min_x = b_raw_min_y = float('inf')
b_raw_max_x = b_raw_max_y = float('-inf')

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
            # Raw location in osm2world.blend
            r_loc = obj.matrix_world @ mathutils.Vector((0, 0, 0))
            b_raw_min_x = min(b_raw_min_x, r_loc.x)
            b_raw_max_x = max(b_raw_max_x, r_loc.x)
            b_raw_min_y = min(b_raw_min_y, r_loc.y)
            b_raw_max_y = max(b_raw_max_y, r_loc.y)
            
            # Translated location
            t_loc = r_loc + translation
            b_min_x = min(b_min_x, t_loc.x)
            b_max_x = max(b_max_x, t_loc.x)
            b_min_y = min(b_min_y, t_loc.y)
            b_max_y = max(b_max_y, t_loc.y)

print("\nOSM2World Buildings RAW BBox (in blend):")
print(f"  X: [{b_raw_min_x:.2f}, {b_raw_max_x:.2f}]")
print(f"  Y: [{b_raw_min_y:.2f}, {b_raw_max_y:.2f}]")

print("\nOSM2World Buildings TRANSLATED BBox (with offset +34975.75, -31878.95):")
print(f"  X: [{b_min_x:.2f}, {b_max_x:.2f}]")
print(f"  Y: [{b_min_y:.2f}, {b_max_y:.2f}]")

