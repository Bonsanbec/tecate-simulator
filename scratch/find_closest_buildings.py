import bpy
import mathutils
import numpy as np

target = mathutils.Vector((-34853.00, 31816.85))

bpy.ops.wm.open_mainfile(filepath="models/tecate/osm2world.blend")

building_mats = {'clay', 'Plaster002', 'RoofingTiles010', 'Concrete034', 'Material'}

mats_found = set()
for mat in bpy.data.materials:
    mats_found.add(mat.name)

print(f"Total materials in file: {len(mats_found)}")

objs_info = []

for obj in bpy.data.objects:
    if obj.type == 'MESH' and len(obj.data.vertices) > 0:
        is_building = False
        mats = []
        for slot in obj.material_slots:
            if slot.material:
                mats.append(slot.material.name)
                if slot.material.name in building_mats:
                    is_building = True
                    
        # Calculate world space centroid
        matrix = obj.matrix_world
        centroid = matrix @ (sum((v.co for v in obj.data.vertices), mathutils.Vector()) / len(obj.data.vertices))
        
        dist = (centroid.xy - target).length
        objs_info.append({
            "name": obj.name,
            "dist": dist,
            "centroid": (centroid.x, centroid.y),
            "mats": mats,
            "is_building": is_building,
            "verts": len(obj.data.vertices)
        })

print("\nTop 20 closest objects of ANY type:")
sorted_any = sorted(objs_info, key=lambda x: x["dist"])
for i, info in enumerate(sorted_any[:20]):
    print(f"  {i+1}. {info['name']}: dist={info['dist']:.2f}m, centroid=({info['centroid'][0]:.2f}, {info['centroid'][1]:.2f}), verts={info['verts']}, mats={info['mats']}, building={info['is_building']}")

print("\nTop 20 closest BUILDING objects:")
sorted_buildings = sorted([x for x in objs_info if x["is_building"]], key=lambda x: x["dist"])
for i, info in enumerate(sorted_buildings[:20]):
    print(f"  {i+1}. {info['name']}: dist={info['dist']:.2f}m, centroid=({info['centroid'][0]:.2f}, {info['centroid'][1]:.2f}), verts={info['verts']}, mats={info['mats']}")
