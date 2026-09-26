import bpy
from mathutils import Vector
import numpy as np
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='godot_project/assets/manzanas_baked.glb')

obj = bpy.data.objects['UrbanManzanas']
mesh = obj.data

park_mat_idx = [i for i, m in enumerate(mesh.materials) if m.name == 'M_UrbanPark'][0]
kiosko_blender = Vector((-6.6844, -2.6878, 400.0132))

# Let's get all top vertices of M_UrbanPark
park_verts = set()
for p in mesh.polygons:
    if p.material_index == park_mat_idx and p.normal.z > 0.8:
        center = sum((mesh.vertices[vi].co for vi in p.vertices), Vector((0,0,0))) / len(p.vertices)
        if (center.x - kiosko_blender.x)**2 + (center.y - kiosko_blender.y)**2 < 85**2:
            for vi in p.vertices:
                park_verts.add(vi)

all_cos = [mesh.vertices[vi].co for vi in park_verts]
print(f"Total top park vertices: {len(all_cos)}")

# Find extreme points along 36 radial directions (every 10 degrees)
# from the centroid of all vertices
cx = sum(v.x for v in all_cos) / len(all_cos)
cy = sum(v.y for v in all_cos) / len(all_cos)
print(f"Centroid of M_UrbanPark: ({cx:.2f}, {cy:.2f})")
print(f"Kiosko position: ({kiosko_blender.x:.2f}, {kiosko_blender.y:.2f})")
print(f"Offset from Kiosko to Centroid: ({cx - kiosko_blender.x:.2f}, {cy - kiosko_blender.y:.2f})")

# Let's find the outer envelope by taking the maximum radial distance in each direction
envelope = []
for deg in range(0, 360, 5):
    rad = math.radians(deg)
    d = Vector((math.cos(rad), math.sin(rad)))
    # project each vertex along this direction
    best_v = max(all_cos, key=lambda v: (v.x - cx)*d.x + (v.y - cy)*d.y)
    envelope.append(best_v)

# Filter unique vertices preserving order
unique_env = []
seen = set()
for v in envelope:
    t = (round(v.x, 2), round(v.y, 2))
    if t not in seen:
        seen.add(t)
        unique_env.append(v)

print(f"\nOuter envelope points: {len(unique_env)}")
for i, v in enumerate(unique_env):
    rel = v - kiosko_blender
    print(f"E{i:02d}: global=({v.x:7.2f}, {v.y:7.2f}, {v.z:7.2f}) | Rel_Kiosko=({rel.x:7.2f}, {rel.y:7.2f}, {rel.z:7.2f})")

# 2D Area of Envelope
area = 0.0
for i in range(len(unique_env)):
    j = (i + 1) % len(unique_env)
    area += unique_env[i].x * unique_env[j].y - unique_env[j].x * unique_env[i].y
area = abs(area) * 0.5
print(f"\n2D Area of Envelope: {area:.2f} m² ({area/10000:.3f} ha)")
