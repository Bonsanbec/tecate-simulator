import bpy, bmesh
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="godot_project/assets/roadways_baked.glb")

print("Objetos en roadways_baked.glb:")
for obj in bpy.context.scene.objects:
    print(f"  {obj.name} ({obj.type})")
    if obj.type == 'MESH':
        m = obj.data
        bm = bmesh.new()
        bm.from_mesh(m)
        bm.transform(obj.matrix_world)
        # Buscar caras cerca del parque (-70 < x < 60, -45 < y < 45 en Blender)
        park_faces = [f for f in bm.faces if -70 < f.calc_center_median().x < 60 and -45 < f.calc_center_median().y < 45]
        if park_faces:
            xs = [v.co.x for f in park_faces for v in f.verts]
            ys = [v.co.y for f in park_faces for v in f.verts]
            print(f"    Caras cerca del parque: {len(park_faces)}, X [{min(xs):.2f}, {max(xs):.2f}], Y [{min(ys):.2f}, {max(ys):.2f}]")
        bm.free()
