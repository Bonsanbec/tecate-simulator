import bpy
import mathutils
import json
import os

bpy.ops.wm.open_mainfile(filepath="models/tecate/osm2world.blend")
translation = mathutils.Vector((34975.75, -31878.95, 0.0))
T_mat = mathutils.Matrix.Translation(translation)

test_objs = []
for obj in bpy.data.objects:
    if obj.name in ["Mesh_228", "Mesh_4223", "Mesh_11996"]:
        # 1. Apply world matrix + offset translation directly into mesh vertex data
        full_matrix = T_mat @ obj.matrix_world
        obj.data.transform(full_matrix)
        # Reset object transform to identity
        obj.matrix_world = mathutils.Matrix.Identity(4)
        obj.select_set(True)
        test_objs.append(obj)

test_gltf = os.path.abspath("scratch/test_identity_export.gltf")
bpy.ops.export_scene.gltf(
    filepath=test_gltf,
    export_format='GLTF_SEPARATE',
    use_selection=True
)

print(f"Exported test identity GLTF to {test_gltf}")

# Inspect GLTF node translations
with open(test_gltf, "r") as f:
    gltf = json.load(f)

for n in gltf.get("nodes", []):
    print("Node:", n.get("name"), "translation:", n.get("translation"), "scale:", n.get("scale"))

