import bpy
from mathutils import Vector
import numpy as np
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='godot_project/assets/manzanas_baked.glb')

obj = bpy.data.objects['UrbanManzanas']
mesh = obj.data

park_mat_idx = None
for idx, mat in enumerate(mesh.materials):
    if mat.name == 'M_UrbanPark':
        park_mat_idx = idx
        break

kiosko_blender = Vector((-6.6844, -2.6878, 400.0132))

park_verts = set()
for p in mesh.polygons:
    if p.material_index == park_mat_idx and p.normal.z > 0.8:
        center = sum((mesh.vertices[vi].co for vi in p.vertices), Vector((0,0,0))) / len(p.vertices)
        if (center.x - kiosko_blender.x)**2 + (center.y - kiosko_blender.y)**2 < 80**2:
            for vi in p.vertices:
                park_verts.add(vi)

vert_cos = [mesh.vertices[vi].co for vi in park_verts]
print(f"Total top park vertices: {len(vert_cos)}")

# Fit plane: Z = a*X + b*Y + c
# Using coords relative to Kiosko:
# z_rel = a * x_rel + b * y_rel + z0
X_rel = np.array([v.x - kiosko_blender.x for v in vert_cos])
Y_rel = np.array([v.y - kiosko_blender.y for v in vert_cos])
Z_rel = np.array([v.z - kiosko_blender.z for v in vert_cos])

A = np.column_stack([X_rel, Y_rel, np.ones_like(X_rel)])
plane_params, residuals, rank, s = np.linalg.lstsq(A, Z_rel, rcond=None)
a, b, c = plane_params

print(f"\nLeast squares plane fit (relative to Kiosko at (0,0,0)):")
print(f"  Z_rel(X_rel, Y_rel) = {a:.6f} * X_rel + {b:.6f} * Y_rel + {c:.6f}")
print(f"  Slope along X (East): {a*100:.2f}% ({math.degrees(math.atan(a)):.3f} deg)")
print(f"  Slope along Y (North): {b*100:.2f}% ({math.degrees(math.atan(b)):.3f} deg)")

# Check residuals
predicted = a * X_rel + b * Y_rel + c
errors = np.abs(Z_rel - predicted)
print(f"Max error: {np.max(errors):.3f} m, Mean error: {np.mean(errors):.3f} m, RMS: {np.sqrt(np.mean(errors**2)):.3f} m")

# Print heights at key corners
corners = [
    ("Kiosko (Center)", 0.0, 0.0),
    ("NE Corner (Juárez & Ortiz Rubio)", 52.66, 40.78),
    ("NW Corner (Juárez & Cárdenas)", -59.50, 29.97),
    ("SE Corner (Ortiz Rubio & Libertad)", 57.30, -31.93),
    ("SW Corner (Cárdenas & Libertad)", -52.94, -32.42),
    ("Monumento a Juárez", 44.0, 34.0),
    ("Fuente de la Paz", -32.3, 15.2),
    ("Monumento a Cárdenas", -45.0, -25.0),
    ("Monumento a Hidalgo", 0.0, -22.0),
    ("Obelisco", 42.0, -10.0),
]

print("\nPredicted elevation offsets relative to Kiosko:")
for name, rx, ry in corners:
    z_elev = a * rx + b * ry + c
    global_z = kiosko_blender.z + z_elev
    print(f"  {name:35s}: rel=({rx:6.1f}, {ry:6.1f}) -> dz={z_elev:+5.2f}m (Global Z={global_z:.2f}m)")
