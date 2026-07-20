import bpy
import mathutils

target_size_x = 121.87
target_size_y = 77.98
tolerance = 5.0 # m

bpy.ops.wm.open_mainfile(filepath="models/tecate/osm2world.blend")

matches = []

for obj in bpy.data.objects:
    if obj.type == 'MESH':
        # Skip objects with too many vertices
        if len(obj.data.vertices) > 2000 or len(obj.data.vertices) < 10:
            continue
            
        matrix = obj.matrix_world
        bbox_corners = [matrix @ mathutils.Vector(corner) for corner in obj.bound_box]
        
        min_x = min(c.x for c in bbox_corners)
        max_x = max(c.x for c in bbox_corners)
        min_y = min(c.y for c in bbox_corners)
        max_y = max(c.y for c in bbox_corners)
        
        size_x = max_x - min_x
        size_y = max_y - min_y
        
        if (abs(size_x - target_size_x) < tolerance and abs(size_y - target_size_y) < tolerance) or \
           (abs(size_x - target_size_y) < tolerance and abs(size_y - target_size_x) < tolerance):
            
            centroid_x = (min_x + max_x) / 2.0
            centroid_y = (min_y + max_y) / 2.0
            
            # Print materials to confirm if it is a building/roof
            mats = [slot.material.name for slot in obj.material_slots if slot.material]
            
            matches.append({
                "name": obj.name,
                "size": (size_x, size_y),
                "centroid": (centroid_x, centroid_y),
                "mats": mats,
                "verts": len(obj.data.vertices)
            })

print(f"Found {len(matches)} objects matching the case study block dimensions:")
for m in matches:
    print(f"  Object: {m['name']}, size=({m['size'][0]:.2f}, {m['size'][1]:.2f}), centroid=({m['centroid'][0]:.2f}, {m['centroid'][1]:.2f}), verts={m['verts']}, mats={m['mats']}")
