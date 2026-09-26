import bpy
from mathutils import Vector
import numpy as np

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='godot_project/assets/manzanas_baked.glb')

obj = bpy.data.objects['UrbanManzanas']
mesh = obj.data

park_mat_idx = [i for i, m in enumerate(mesh.materials) if m.name == 'M_UrbanPark'][0]
kiosko_blender = Vector((-6.6844, -2.6878, 400.0132))

park_verts = set()
for p in mesh.polygons:
    if p.material_index == park_mat_idx and p.normal.z > 0.8:
        center = sum((mesh.vertices[vi].co for vi in p.vertices), Vector((0,0,0))) / len(p.vertices)
        if (center.x - kiosko_blender.x)**2 + (center.y - kiosko_blender.y)**2 < 85**2:
            for vi in p.vertices:
                park_verts.add(vi)

all_cos = [mesh.vertices[vi].co for vi in park_verts]

# Check corners:
# NE: x > 35, y > 25
ne_verts = [v for v in all_cos if v.x > 35 and v.y > 25]
ne_verts.sort(key=lambda v: -(v.x + v.y))
print("NE vertices:")
for v in ne_verts[:8]:
    rel = v - kiosko_blender
    print(f"  global=({v.x:6.2f}, {v.y:6.2f}, {v.z:6.2f}) -> rel=({rel.x:6.2f}, {rel.y:6.2f}, {rel.z:6.2f})")

# NW: x < -50, y > 15
nw_verts = [v for v in all_cos if v.x < -50 and v.y > 15]
nw_verts.sort(key=lambda v: -(-v.x + v.y))
print("\nNW vertices:")
for v in nw_verts[:8]:
    rel = v - kiosko_blender
    print(f"  global=({v.x:6.2f}, {v.y:6.2f}, {v.z:6.2f}) -> rel=({rel.x:6.2f}, {rel.y:6.2f}, {rel.z:6.2f})")

# SE: x > 35, y < -20
se_verts = [v for v in all_cos if v.x > 35 and v.y < -20]
se_verts.sort(key=lambda v: -(v.x - v.y))
print("\nSE vertices:")
for v in se_verts[:8]:
    rel = v - kiosko_blender
    print(f"  global=({v.x:6.2f}, {v.y:6.2f}, {v.z:6.2f}) -> rel=({rel.x:6.2f}, {rel.y:6.2f}, {rel.z:6.2f})")

# SW: x < -40, y < -25
sw_verts = [v for v in all_cos if v.x < -40 and v.y < -25]
sw_verts.sort(key=lambda v: -(-v.x - v.y))
print("\nSW vertices:")
for v in sw_verts[:8]:
    rel = v - kiosko_blender
    print(f"  global=({v.x:6.2f}, {v.y:6.2f}, {v.z:6.2f}) -> rel=({rel.x:6.2f}, {rel.y:6.2f}, {rel.z:6.2f})")
