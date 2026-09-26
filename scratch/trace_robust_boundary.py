import bpy
import bmesh
from mathutils import Vector
import math
import numpy as np

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

# Select only horizontal top faces of M_UrbanPark near Kiosko
park_faces = []
for p in mesh.polygons:
    if p.material_index == park_mat_idx and p.normal.z > 0.8:
        center = sum((mesh.vertices[vi].co for vi in p.vertices), Vector((0,0,0))) / len(p.vertices)
        if (center.x - kiosko_blender.x)**2 + (center.y - kiosko_blender.y)**2 < 80**2:
            park_faces.append(p)

print(f"Total top park faces: {len(park_faces)}")

# Collect directed boundary edges from triangles (in CCW order from face)
edge_counts = {}
directed_edges = []
for p in park_faces:
    vs = list(p.vertices)
    for i in range(len(vs)):
        v1, v2 = vs[i], vs[(i+1)%len(vs)]
        undir = tuple(sorted((v1, v2)))
        edge_counts[undir] = edge_counts.get(undir, 0) + 1

boundary_edges = []
for p in park_faces:
    vs = list(p.vertices)
    for i in range(len(vs)):
        v1, v2 = vs[i], vs[(i+1)%len(vs)]
        if edge_counts[tuple(sorted((v1, v2)))] == 1:
            boundary_edges.append((v1, v2))

print(f"Total boundary edges: {len(boundary_edges)}")

# Build adjacency map: v1 -> list of v2
adj = {}
for v1, v2 in boundary_edges:
    adj.setdefault(v1, []).append(v2)

# Find start vertex: the one with minimum X (most western vertex)
unique_verts = set(adj.keys())
min_v = min(unique_verts, key=lambda vi: mesh.vertices[vi].co.x)
print(f"Start vertex: {min_v}, co={mesh.vertices[min_v].co}")

# Traverse outer boundary by always taking the most clockwise / rightmost turn
curr_v = min_v
loop = [curr_v]
visited_edges = set()

# Previous direction vector (initially pointing south/down so next points up)
prev_dir = Vector((0.0, -1.0, 0.0))

for step in range(500):
    candidates = adj.get(curr_v, [])
    if not candidates:
        print(f"Dead end at vertex {curr_v}")
        break
    
    # Choose candidate that minimizes relative angle (most clockwise turn)
    def turn_angle(cand):
        d = (mesh.vertices[cand].co - mesh.vertices[curr_v].co).to_2d().normalized()
        # angle between prev_dir and d
        ang = math.atan2(d.y, d.x) - math.atan2(prev_dir.y, prev_dir.x)
        # normalize to [0, 2*pi)
        while ang <= 0: ang += 2 * math.pi
        while ang > 2 * math.pi: ang -= 2 * math.pi
        return ang
    
    # filter out already traversed directed edges if possible
    unvisited = [c for c in candidates if (curr_v, c) not in visited_edges]
    if unvisited:
        best_cand = min(unvisited, key=turn_angle)
    else:
        best_cand = min(candidates, key=turn_angle)
    
    visited_edges.add((curr_v, best_cand))
    prev_dir = (mesh.vertices[best_cand].co - mesh.vertices[curr_v].co).to_2d().normalized()
    curr_v = best_cand
    
    if curr_v == min_v:
        print(f"Successfully closed outer loop in {len(loop)} vertices!")
        break
    loop.append(curr_v)

coords = [mesh.vertices[vi].co for vi in loop]
print(f"\nOuter loop length: {len(coords)} vertices")

# Simplify collinear points (epsilon = 0.05m)
simplified = []
for i in range(len(coords)):
    p_prev = coords[(i - 1) % len(coords)]
    p_curr = coords[i]
    p_next = coords[(i + 1) % len(coords)]
    v1 = (p_curr - p_prev).to_2d().normalized()
    v2 = (p_next - p_curr).to_2d().normalized()
    # If cross product is significant, it's a corner!
    cross = abs(v1.x * v2.y - v1.y * v2.x)
    if cross > 0.01:
        simplified.append(p_curr)

print(f"Simplified polygon vertices: {len(simplified)}")

print("\n--- SIMPLIFIED OUTER BOUNDARY (COORDINATES IN BLENDER & GODOT) ---")
for i, p in enumerate(simplified):
    rel = p - kiosko_blender
    # Godot coords: Godot X = Blender X, Godot Y = Blender Z, Godot Z = -Blender Y
    godot_x = p.x
    godot_y = p.z
    godot_z = -p.y
    rel_godot_x = rel.x
    rel_godot_y = rel.z
    rel_godot_z = -rel.y
    print(f"P{i:02d}: Blender=({p.x:7.2f}, {p.y:7.2f}, {p.z:7.2f}) | Godot=({godot_x:7.2f}, {godot_y:7.2f}, {godot_z:7.2f}) | Rel_Kiosko=({rel.x:7.2f}, {rel.y:7.2f}, {rel.z:7.2f})")

# Calculate 2D Area
area = 0.0
for i in range(len(simplified)):
    j = (i + 1) % len(simplified)
    area += simplified[i].x * simplified[j].y - simplified[j].x * simplified[i].y
area = abs(area) * 0.5
print(f"\n2D Area of simplified polygon: {area:.2f} m² ({area/10000:.3f} ha)")
