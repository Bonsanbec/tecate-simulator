import bpy
import bmesh
import math
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

print(f"M_UrbanPark material index: {park_mat_idx}")

# Filter faces within 80m of Kiosko
kiosko_blender = Vector((-6.6844, -2.6878, 400.0132))
local_park_faces = []
for p in mesh.polygons:
    if p.material_index == park_mat_idx:
        center = sum((mesh.vertices[vi].co for vi in p.vertices), Vector((0,0,0))) / len(p.vertices)
        if (center.x - kiosko_blender.x)**2 + (center.y - kiosko_blender.y)**2 < 80**2:
            local_park_faces.append(p)

print(f"Local M_UrbanPark faces near Kiosko: {len(local_park_faces)}")

vert_indices = set()
for p in local_park_faces:
    for vi in p.vertices:
        vert_indices.add(vi)

verts = [mesh.vertices[vi].co for vi in vert_indices]
xs = [v.x for v in verts]
ys = [v.y for v in verts]
zs = [v.z for v in verts]
print(f"Blender X range (Godot X): {min(xs):.2f} to {max(xs):.2f} (span: {max(xs)-min(xs):.2f}m)")
print(f"Blender Y range (-Godot Z): {min(ys):.2f} to {max(ys):.2f} (span: {max(ys)-min(ys):.2f}m)")
print(f"Blender Z range (Godot Y elevation): {min(zs):.2f} to {max(zs):.2f} (span: {max(zs)-min(zs):.2f}m)")

# Check normals of these faces to determine terrain slope / tilt
normals = [p.normal for p in local_park_faces]
avg_norm = sum(normals, Vector((0,0,0))) / len(normals)
print(f"Average surface normal in Blender (X, Y, Z): {avg_norm}")
slope_x = -avg_norm.x / avg_norm.z
slope_y = -avg_norm.y / avg_norm.z
print(f"  Slope in X: {slope_x:.6f} rad = {math.degrees(slope_x):.3f} deg")
print(f"  Slope in Y: {slope_y:.6f} rad = {math.degrees(slope_y):.3f} deg")

# Find boundary edges of local_park_faces
edge_face_count = {}
for p in local_park_faces:
    v_list = list(p.vertices)
    for i in range(len(v_list)):
        e = tuple(sorted((v_list[i], v_list[(i+1)%len(v_list)])))
        edge_face_count[e] = edge_face_count.get(e, 0) + 1

boundary_edges = [e for e, count in edge_face_count.items() if count == 1]
print(f"Boundary edges count: {len(boundary_edges)}")

# Chain boundary edges into polygon loop(s)
boundary_adj = {}
for v1, v2 in boundary_edges:
    boundary_adj.setdefault(v1, []).append(v2)
    boundary_adj.setdefault(v2, []).append(v1)

loops = []
visited_edges = set()

for e in boundary_edges:
    if e in visited_edges:
        continue
    loop = [e[0]]
    curr = e[1]
    prev = e[0]
    visited_edges.add(e)
    
    while curr != loop[0]:
        loop.append(curr)
        nxts = [n for n in boundary_adj[curr] if n != prev]
        if not nxts:
            break
        nxt = nxts[0]
        visited_edges.add(tuple(sorted((curr, nxt))))
        prev = curr
        curr = nxt
    loops.append(loop)

print(f"Found {len(loops)} boundary loop(s).")
for l_i, loop in enumerate(loops):
    print(f"\n--- Loop {l_i} (verts: {len(loop)}) ---")
    coords = [mesh.vertices[vi].co for vi in loop]
    for vi, co in enumerate(coords):
        rel = co - kiosko_blender
        print(f"  V{vi:02d}: global=({co.x:7.2f}, {co.y:7.2f}, {co.z:7.2f}) -> rel_kiosko=({rel.x:7.2f}, {rel.y:7.2f}, {rel.z:7.2f})")
