import bpy
import mathutils

bpy.ops.wm.open_mainfile(filepath="models/tecate/osm2world.blend")

for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.name in ["Mesh_228", "Mesh_4223", "Mesh_11996"]:
        print(f"Object '{obj.name}':")
        print(f"  obj.location = {obj.location}")
        print(f"  obj.matrix_world = \n{obj.matrix_world}")
        print(f"  Mesh vertex count: {len(obj.data.vertices)}")
        sample_verts = [v.co for v in obj.data.vertices[:5]]
        print(f"  Sample local vert.co: {sample_verts}")
        world_verts = [obj.matrix_world @ v.co for v in obj.data.vertices[:5]]
        print(f"  Sample world_verts (mw @ v.co): {world_verts}")

