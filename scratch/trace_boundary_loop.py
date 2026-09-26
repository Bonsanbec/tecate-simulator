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

# Select only horizontal top faces of M_UrbanPark near Kiosko
park_faces = []
for p in mesh.polygons:
    if p.material_index == park_mat_idx and p.normal.z > 0.8:
        center = sum((mesh.vertices[vi].co for vi in p.vertices), Vector((0,0,0))) / len(p.vertices)
        if (center.x - kiosko_blender.x)**2 + (center.y - kiosko_blender.y)**2 < 80**2:
            park_faces.append(p)

print(f"Total top park faces: {len(park_faces)}")

# Boundary edges
edge_count = {}
for p in park_faces:
    vs = list(p.vertices)
    for i in range(len(vs)):
        # directed edge according to face winding
        v1, v2 = vs[i], vs[(i+1)%len(vs)]
        undirected = tuple(sorted((v1, v2)))
        edge_count[undirected] = edge_count.get(undirected, 0) + 1

boundary_undirected = {e for e, count in edge_count.items() if count == 1}
print(f"Boundary undirected edges: {len(boundary_undirected)}")

# Now find directed boundary edges
directed_boundary = {}
for p in park_faces:
    vs = list(p.vertices)
    for i in range(len(vs)):
        v1, v2 = vs[i], vs[(i+1)%len(vs)]
        if tuple(sorted((v1, v2))) in boundary_undirected:
            directed_boundary[v1] = v2

print(f"Directed boundary edges: {len(directed_boundary)}")

# Trace loop
start_v = list(directed_boundary.keys())[0]
curr_v = start_v
ordered_verts = []
visited = set()

while curr_v in directed_boundary and curr_v not in visited:
    visited.add(curr_v)
    ordered_verts.append(curr_v)
    curr_v = directed_boundary[curr_v]

print(f"Ordered boundary loop length: {len(ordered_verts)} (closed: {curr_v == start_v})")

# Print the 2D polygon vertices
coords = [mesh.vertices[vi].co for vi in ordered_verts]
print("\n--- EXACT 2D PARK POLYGON (GLOBAL & RELATIVE TO KIOSKO) ---")
print("polygon_relative_to_kiosko = [")
for i, co in enumerate(coords):
    rel = co - kiosko_blender
    print(f"    ({rel.x:7.2f}, {rel.y:7.2f}, {rel.z:7.2f}), # V{i:02d}: global=({co.x:7.2f}, {co.y:7.2f}, {co.z:7.2f})")
print("]")

# Calculate 2D Area
area = 0.0
for i in range(len(coords)):
    j = (i + 1) % len(coords)
    area += coords[i].x * coords[j].y - coords[j].x * coords[i].y
area = abs(area) * 0.5
print(f"\nCalculated 2D Area of M_UrbanPark: {area:.2f} m² ({area/10000:.3f} ha)")

# Also let's inspect the Roadways around this polygon!
# Which streets surround this polygon?
xs = [c.x for c in coords]
ys = [c.y for c in coords]
print(f"X bounds: {min(xs):.2f} to {max(xs):.2f}")
print(f"Y bounds: {min(ys):.2f} to {max(ys):.2f}")
