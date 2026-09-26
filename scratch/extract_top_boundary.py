import bpy
import bmesh
from mathutils import Vector
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

bm = bmesh.new()
bm.from_mesh(mesh)
bm.faces.ensure_lookup_table()

# Keep ONLY top surface faces of M_UrbanPark near Kiosko (normal.z > 0.8)
faces_to_delete = []
for f in bm.faces:
    center = f.calc_center_median()
    dist_k = (center.x - kiosko_blender.x)**2 + (center.y - kiosko_blender.y)**2
    if f.material_index != park_mat_idx or dist_k > 80**2 or f.normal.z < 0.8:
        faces_to_delete.append(f)

bmesh.ops.delete(bm, geom=faces_to_delete, context='FACES')
bm.faces.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.verts.ensure_lookup_table()

print(f"Top surface park faces: {len(bm.faces)}, edges: {len(bm.edges)}, verts: {len(bm.verts)}")

# Dissolve internal edges
internal_edges = [e for e in bm.edges if not e.is_boundary]
bmesh.ops.dissolve_edges(bm, edges=internal_edges, use_verts=True)
bm.faces.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.verts.ensure_lookup_table()

print(f"After dissolving internal edges: faces={len(bm.faces)}")
for fi, f in enumerate(bm.faces):
    print(f"\nFace {fi}: verts={len(f.verts)}, area={f.calc_area():.2f}")
    verts = [v.co for v in f.verts]
    for vi, v in enumerate(verts):
        rel = v - kiosko_blender
        print(f"  V{vi:02d}: global=({v.x:7.2f}, {v.y:7.2f}, {v.z:7.2f}) -> rel_kiosko=({rel.x:7.2f}, {rel.y:7.2f}, {rel.z:7.2f})")

# Also check sidewalk material around the park to see curb lines!
sidewalk_mat_idx = None
for idx, mat in enumerate(mesh.materials):
    if mat.name == 'M_UrbanSidewalk':
        sidewalk_mat_idx = idx
        break

print(f"\nM_UrbanSidewalk index: {sidewalk_mat_idx}")

bm.free()
