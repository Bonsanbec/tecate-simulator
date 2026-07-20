import bpy
import mathutils
import json
import os

bpy.ops.wm.open_mainfile(filepath="models/tecate/osm2world.blend")
translation = mathutils.Vector((34975.75, -31878.95, 0.0))
T_mat = mathutils.Matrix.Translation(translation)

for obj in bpy.data.objects:
    if obj.name in ["Mesh_228", "Mesh_4223", "Mesh_11996"]:
        print(f"Before obj '{obj.name}':")
        print(f"  matrix_world translation = {obj.matrix_world.to_translation()}")
        
        # Apply translation to matrix_world
        obj.matrix_world = T_mat @ obj.matrix_world
        
        print(f"After obj '{obj.name}':")
        print(f"  matrix_world translation = {obj.matrix_world.to_translation()}")
        
        # Check sample world vertices
        sample_world_verts = [obj.matrix_world @ v.co for v in obj.data.vertices[:3]]
        print(f"  World verts after matrix shift: {sample_world_verts}")

