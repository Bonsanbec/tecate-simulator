import bpy
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='godot_project/assets/manzanas_baked.glb')
print("MANZANAS OBJECTS:")
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        print(f"Mesh: {obj.name}, verts: {len(obj.data.vertices)}")
        # Check vertices near Kiosko: Godot X=-6.68, Z=2.68
        # In Blender gltf import: Godot Z is Blender -Y or Y depending on import settings
        # Let's inspect coordinates of vertices near X in [-80, 80]
        near_verts = [obj.matrix_world @ v.co for v in obj.data.vertices if abs(v.co.x) < 100 and abs(v.co.y) < 100]
        print(f"  Near center (<100m): {len(near_verts)}")
        if near_verts:
            xs = [v.x for v in near_verts]
            ys = [v.y for v in near_verts]
            zs = [v.z for v in near_verts]
            print(f"  X range: {min(xs):.2f} to {max(xs):.2f}")
            print(f"  Y range: {min(ys):.2f} to {max(ys):.2f}")
            print(f"  Z range: {min(zs):.2f} to {max(zs):.2f}")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='godot_project/assets/roadways_baked.glb')
print("\nROADWAYS OBJECTS:")
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        print(f"Mesh: {obj.name}, verts: {len(obj.data.vertices)}, mats: {[m.name for m in obj.data.materials]}")
        near_verts = [obj.matrix_world @ v.co for v in obj.data.vertices if abs(v.co.x) < 100 and abs(v.co.y) < 100]
        print(f"  Near center (<100m): {len(near_verts)}")
        if near_verts:
            xs = [v.x for v in near_verts]
            ys = [v.y for v in near_verts]
            zs = [v.z for v in near_verts]
            print(f"  X range: {min(xs):.2f} to {max(xs):.2f}")
            print(f"  Y range: {min(ys):.2f} to {max(ys):.2f}")
            print(f"  Z range: {min(zs):.2f} to {max(zs):.2f}")
