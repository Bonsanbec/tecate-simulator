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

# Get all vertices belonging to M_UrbanPark with normal.z > 0.8 near Kiosko
park_verts = set()
for p in mesh.polygons:
    if p.material_index == park_mat_idx and p.normal.z > 0.8:
        center = sum((mesh.vertices[vi].co for vi in p.vertices), Vector((0,0,0))) / len(p.vertices)
        if (center.x - kiosko_blender.x)**2 + (center.y - kiosko_blender.y)**2 < 85**2:
            for vi in p.vertices:
                park_verts.add(vi)

all_cos = [mesh.vertices[vi].co for vi in park_verts]
print(f"Total vertices in top park faces: {len(all_cos)}")

# 2D BMesh to find the exact 2D boundary polygon
import bmesh
bm = bmesh.new()
# Project all faces of top M_UrbanPark into 2D BMesh
vert_map = {}
for p in mesh.polygons:
    if p.material_index == park_mat_idx and p.normal.z > 0.8:
        center = sum((mesh.vertices[vi].co for vi in p.vertices), Vector((0,0,0))) / len(p.vertices)
        if (center.x - kiosko_blender.x)**2 + (center.y - kiosko_blender.y)**2 < 85**2:
            bm_face_verts = []
            for vi in p.vertices:
                co = mesh.vertices[vi].co
                key = (round(co.x, 3), round(co.y, 3))
                if key not in vert_map:
                    vert_map[key] = bm.verts.new((co.x, co.y, 0.0))
                bm_face_verts.append(vert_map[key])
            try:
                bm.faces.new(bm_face_verts)
            except Exception:
                pass

bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()
print(f"2D BMesh: faces={len(bm.faces)}, edges={len(bm.edges)}, verts={len(bm.verts)}")

# Dissolve internal edges
internal_edges = [e for e in bm.edges if not e.is_boundary]
print(f"Internal edges to dissolve: {len(internal_edges)}")
bmesh.ops.dissolve_edges(bm, edges=internal_edges, use_verts=True)

bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

print(f"After dissolving: faces={len(bm.faces)}, boundary verts={len(bm.verts)}, edges={len(bm.edges)}")

# Find the largest face
largest_f = max(bm.faces, key=lambda f: f.calc_area())
print(f"Largest face area: {largest_f.calc_area():.2f} m², verts: {len(largest_f.verts)}")

# Print vertices in CCW order
loop_cos = [v.co for v in largest_f.verts]

# Find 3D Z for each 2D vertex by nearest neighbor in all_cos
final_polygon = []
for v in loop_cos:
    closest = min(all_cos, key=lambda c: (c.x - v.x)**2 + (c.y - v.y)**2)
    rel = closest - kiosko_blender
    final_polygon.append((rel.x, rel.y, rel.z, closest.x, closest.y, closest.z))

print("\nPARK_PERIMETER_POLYGON = [")
for i, (rx, ry, rz, gx, gy, gz) in enumerate(final_polygon):
    print(f"    ({rx:7.2f}, {ry:7.2f}), # V{i:02d}: Z_rel={rz:+5.2f} | global=({gx:7.2f}, {gy:7.2f}, {gz:7.2f})")
print("]")

bm.free()
