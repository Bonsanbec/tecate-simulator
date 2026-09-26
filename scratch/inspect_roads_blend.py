import bpy
from mathutils import Vector

print("Scene objects:", len(bpy.context.scene.objects))
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        bbox = [obj.matrix_world @ Vector(b) for b in obj.bound_box]
        xs = [v.x for v in bbox]
        ys = [v.y for v in bbox]
        if min(xs) < -6.68 < max(xs) and min(ys) < 2.69 < max(ys):
            print(f"Objeto sobre el parque: {obj.name}, X [{min(xs):.1f}, {max(xs):.1f}], Y [{min(ys):.1f}, {max(ys):.1f}]")
    elif "hidalgo" in obj.name.lower() or "parque" in obj.name.lower():
        print(f"Objeto nombrado: {obj.name}, tipo: {obj.type}")
