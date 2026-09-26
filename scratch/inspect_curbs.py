import bpy, bmesh
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="godot_project/assets/roadways_baked.glb")

obj = bpy.data.objects.get("Roadways")
m = obj.data
bm = bmesh.new()
bm.from_mesh(m)
bm.transform(obj.matrix_world)

kiosko_blender = Vector((-6.6844, -2.6878, 400.0132))

# Material 3 es M_CurbConcrete
# Filtremos caras de banquetas alrededor del parque (-75 < x < 60, -45 < y < 45)
curb_faces = [f for f in bm.faces if f.material_index == 3 and -75 < f.calc_center_median().x < 60 and -45 < f.calc_center_median().y < 45]
print(f"Total caras de banqueta del parque: {len(curb_faces)}")

# Encontrar los vértices de estas banquetas
xs = [v.co.x for f in curb_faces for v in f.verts]
ys = [v.co.y for f in curb_faces for v in f.verts]
print(f"Envolvente de banquetas (Blender): X [{min(xs):.2f}, {max(xs):.2f}], Y [{min(ys):.2f}, {max(ys):.2f}]")
print(f"Envolvente de banquetas (Godot): X [{min(xs):.2f}, {max(xs):.2f}], Z [{-max(ys):.2f}, {-min(ys):.2f}]")

# Respecto al Kiosko:
local_xs = [x - kiosko_blender.x for x in xs]
local_ys = [y - kiosko_blender.y for y in ys]
print(f"Envolvente relativa al Kiosko (Blender): X [{min(local_xs):.2f}, {max(local_xs):.2f}], Y [{min(local_ys):.2f}, {max(local_ys):.2f}]")

# Identifiquemos los 4 lados de la banqueta que miran hacia el interior del parque
# Norte (Av. Juárez): y máximo interior
# Sur (Libertad): y mínimo interior
# Este (Ortiz Rubio): x máximo interior
# Oeste (Cárdenas): x mínimo interior

# Agrupemos vértices por cuadrantes / bordes
north_verts = [v.co for f in curb_faces for v in f.verts if v.co.y > 25]
south_verts = [v.co for f in curb_faces for v in f.verts if v.co.y < -25]
east_verts = [v.co for f in curb_faces for v in f.verts if v.co.x > 35]
west_verts = [v.co for f in curb_faces for v in f.verts if v.co.x < -40]

print(f"Norte (Juárez): Y entre {min(v.y for v in north_verts):.2f} y {max(v.y for v in north_verts):.2f}")
print(f"Sur (Libertad): Y entre {min(v.y for v in south_verts):.2f} y {max(v.y for v in south_verts):.2f}")
print(f"Este (Ortiz Rubio): X entre {min(v.x for v in east_verts):.2f} y {max(v.x for v in east_verts):.2f}")
print(f"Oeste (Cárdenas): X entre {min(v.x for v in west_verts):.2f} y {max(v.x for v in west_verts):.2f}")

bm.free()
