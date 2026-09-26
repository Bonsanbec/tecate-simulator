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

# Queremos el polígono de la manzana del Parque Hidalgo
# La manzana está rodeada por las banquetas interiores (material 3 = M_CurbConcrete)
curb_faces = [f for f in bm.faces if f.material_index == 3 and -70 < f.calc_center_median().x < 60 and -45 < f.calc_center_median().y < 45]

# Encontremos los vértices de las caras de banqueta que delimitan el parque hacia el interior
# Calculemos el centroide del parque
cx, cy = -6.68, -2.69

# Encontrar los vértices del borde interior en 36 sectores angulares (cada 10 grados)
n_sectors = 36
sector_pts = []
for s in range(n_sectors):
    ang_center = s * 2 * math.pi / n_sectors
    # Buscar el vértice de banqueta más cercano al centro en este sector (± 6 grados)
    best_dist = 1000.0
    best_v = None
    for f in curb_faces:
        for v in f.verts:
            dx = v.co.x - cx
            dy = v.co.y - cy
            d = math.hypot(dx, dy)
            if 25.0 < d < 75.0:
                ang = (math.atan2(dy, dx) + 2*math.pi) % (2*math.pi)
                diff = abs(ang - ang_center)
                if diff > math.pi:
                    diff = 2*math.pi - diff
                if diff < math.radians(6.0):
                    if d < best_dist:
                        best_dist = d
                        best_v = v.co
    if best_v:
        sector_pts.append((round(best_v.x, 2), round(best_v.y, 2)))

print(f"Polígono perimetral refinado ({len(sector_pts)} puntos):")
print(sector_pts)
bm.free()
