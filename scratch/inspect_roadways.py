import bpy, bmesh
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="godot_project/assets/roadways_baked.glb")

obj = bpy.data.objects.get("Roadways")
m = obj.data
bm = bmesh.new()
bm.from_mesh(m)
bm.transform(obj.matrix_world)

# Ver materiales
for i, mat in enumerate(obj.data.materials):
    print(f"Material {i}: {mat.name}")

# Caras en el área del parque (-75 < x < 65, -50 < y < 50)
park_faces = [f for f in bm.faces if -75 < f.calc_center_median().x < 65 and -50 < f.calc_center_median().y < 50]
print(f"Total caras en el área del parque: {len(park_faces)}")

# Agrupar por material
mat_counts = {}
for f in park_faces:
    mat_counts[f.material_index] = mat_counts.get(f.material_index, 0) + 1

for midx, count in mat_counts.items():
    mname = obj.data.materials[midx].name if midx < len(obj.data.materials) else "Unknown"
    print(f"  Material {midx} ({mname}): {count} caras")

# Analizar las banquetas interiores (el perímetro que rodea la manzana del parque)
# Encontrar las aristas de borde interior de las banquetas que miran hacia el parque
# o las caras de banqueta que rodean el parque
bm.free()
