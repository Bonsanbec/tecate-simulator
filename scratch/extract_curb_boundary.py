import bpy, bmesh
from mathutils import Vector
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="godot_project/assets/roadways_baked.glb")

obj = bpy.data.objects.get("Roadways")
m = obj.data
bm = bmesh.new()
bm.from_mesh(m)
bm.transform(obj.matrix_world)

kiosko_godot = Vector((-6.6844, 400.0132, 2.6878))
kiosko_blender = Vector((-6.6844, -2.6878, 400.0132))

# Busquemos los vértices de banqueta (material 3) más cercanos al centro del parque
# que forman el perímetro interior de la manzana
# El parque está aproximadamente en:
# X en [-65, 55], Y en [-42, 42] (en Blender)
curb_faces = [f for f in bm.faces if f.material_index == 3 and -70 < f.calc_center_median().x < 55 and -45 < f.calc_center_median().y < 45]

# Encontrar los vértices interiores (los que delimitan la manzana hacia adentro)
# Para cada ángulo theta de 0 a 360 grados, encontrar el vértice de banqueta más cercano al Kiosko
center = kiosko_blender
n_bins = 72
bin_pts = {}
for f in curb_faces:
    for v in f.verts:
        dx = v.co.x - center.x
        dy = v.co.y - center.y
        dist = math.hypot(dx, dy)
        if 20.0 < dist < 80.0:
            ang = (math.atan2(dy, dx) + 2*math.pi) % (2*math.pi)
            b_idx = int(ang / (2*math.pi) * n_bins)
            if b_idx not in bin_pts or dist < bin_pts[b_idx][0]:
                bin_pts[b_idx] = (dist, v.co.x, v.co.y)

print(f"Puntos del perímetro interior de banquetas (relativo al Kiosko, en Blender):")
polygon_local = []
for b_idx in range(n_bins):
    if b_idx in bin_pts:
        dist, vx, vy = bin_pts[b_idx]
        lx = vx - center.x
        ly = vy - center.y
        polygon_local.append((round(lx, 2), round(ly, 2)))
        deg = b_idx * 360 / n_bins
        if b_idx % 4 == 0:
            print(f"  Ang {deg:5.1f}°: dist={dist:5.2f}m -> Local: ({lx:6.2f}, {ly:6.2f}) | Blender: ({vx:6.2f}, {vy:6.2f})")

print(f"Total vértices en polígono: {len(polygon_local)}")

bm.free()
