import bpy
import json
import mathutils
import sys
import os

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

print(f"Total building objects in Blender: {len(building_objs)}")

# Load blocks_cache.json
with open("data/blocks_cache.json", "r") as f:
    blocks = json.load(f)

print(f"Total blocks in cache: {len(blocks)}")

# Fast Point-in-Polygon implementation
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

# Precompute block bounding boxes for spatial indexing
block_bboxes = {}
for block_id, block_data in blocks.items():
    poly = block_data["polygon"]
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    block_bboxes[block_id] = (min(xs), max(xs), min(ys), max(ys), poly)

# Map each building object to a block
building_mapping = {}
unmatched_count = 0

for obj in building_objs:
    # Compute center of object in world coords (after translation)
    world_center = obj.matrix_world @ mathutils.Vector((0, 0, 0)) + translation
    cx = world_center.x
    cy = world_center.y
    
    # Also compute BBox centroid
    world_verts = [obj.matrix_world @ v.co + translation for v in obj.data.vertices[:50]] # sample up to 50 verts
    bcx = sum(v.x for v in world_verts) / len(world_verts)
    bcy = sum(v.y for v in world_verts) / len(world_verts)
    
    matched_block = None
    # Check candidate blocks using BBox
    for block_id, (minx, maxx, miny, maxy, poly) in block_bboxes.items():
        if minx <= bcx <= maxx and miny <= bcy <= maxy:
            if point_in_poly(bcx, bcy, poly):
                matched_block = block_id
                break
                
    if matched_block:
        building_mapping[obj.name] = matched_block
    else:
        unmatched_count += 1

matched_blocks = set(building_mapping.values())
print(f"Successfully mapped {len(building_mapping)} buildings to {len(matched_blocks)} unique manzanas!")
print(f"Unmatched buildings: {unmatched_count}")

