import bpy
import bmesh
from mathutils import Vector

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

# Delete all faces that are NOT M_UrbanPark or far from Kiosko
faces_to_delete = []
for f in bm.faces:
    center = f.calc_center_median()
    if f.material_index != park_mat_idx or (center.x - kiosko_blender.x)**2 + (center.y - kiosko_blender.y)**2 > 80**2:
        faces_to_delete.append(f)

bmesh.ops.delete(bm, geom=faces_to_delete, context='FACES')
bm.faces.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.verts.ensure_lookup_table()

print(f"Remaining park faces in BMesh: {len(bm.faces)}, edges: {len(bm.edges)}, verts: {len(bm.verts)}")

# Dissolve all non-boundary edges!
internal_edges = [e for e in bm.edges if not e.is_boundary]
print(f"Internal edges to dissolve: {len(internal_edges)}")
bmesh.ops.dissolve_edges(bm, edges=internal_edges, use_verts=True)

bm.faces.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.verts.ensure_lookup_table()

print(f"After dissolving internal edges: faces={len(bm.faces)}, boundary verts={len(bm.verts)}, boundary edges={len(bm.edges)}")

for fi, f in enumerate(bm.faces):
    print(f"Face {fi}: {len(f.verts)} verts, area={f.calc_area():.2f}")
    loop_verts = [v.co for v in f.verts]
    for vi, v in enumerate(loop_verts):
        rel = v - kiosko_blender
        print(f"  V{vi:02d}: global=({v.x:7.2f}, {v.y:7.2f}, {v.z:7.2f}) -> rel_kiosko=({rel.x:7.2f}, {rel.y:7.2f}, {rel.z:7.2f})")

bm.free()
