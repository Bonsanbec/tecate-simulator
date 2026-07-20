import json
import bpy
import mathutils

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

b_min_x = b_min_y = float('inf')
b_max_x = b_max_y = float('-inf')

for obj in building_objs:
    mw = obj.matrix_world
    # Vertex bounds
    xs = [ (mw @ v.co).x + translation.x for v in obj.data.vertices ]
    ys = [ (mw @ v.co).y + translation.y for v in obj.data.vertices ]
    if xs and ys:
        b_min_x = min(b_min_x, min(xs))
        b_max_x = max(b_max_x, max(xs))
        b_min_y = min(b_min_y, min(ys))
        b_max_y = max(b_max_y, max(ys))

print("OSM2World Buildings VERTEX BBox (TRANSLATED):")
print(f"  X: [{b_min_x:.2f}, {b_max_x:.2f}]")
print(f"  Y: [{b_min_y:.2f}, {b_max_y:.2f}]")

# Load blocks_cache.json
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

print("\nBlocks Cache BBox (Local coordinates):")
print(f"  X: [{block_min_x:.2f}, {block_max_x:.2f}]")
print(f"  Y: [{block_min_y:.2f}, {block_max_y:.2f}]")

