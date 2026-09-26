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
park_verts = set()
for p in mesh.polygons:
    if p.material_index == park_mat_idx and p.normal.z > 0.8:
        center = sum((mesh.vertices[vi].co for vi in p.vertices), Vector((0,0,0))) / len(p.vertices)
        if (center.x - kiosko_blender.x)**2 + (center.y - kiosko_blender.y)**2 < 80**2:
            for vi in p.vertices:
                park_verts.add(vi)

vert_cos = [mesh.vertices[vi].co for vi in park_verts]
print(f"Total vertices in top park faces: {len(vert_cos)}")

# Create a 2D BMesh from these XY vertices (with Z=0 for 2D hull)
bm = bmesh.new()
bm_verts = [bm.verts.new((co.x, co.y, 0.0)) for co in vert_cos]
bm.verts.ensure_lookup_table()

# Compute 2D Convex Hull
res = bmesh.ops.convex_hull(bm, input=bm_verts)
# res['geom'] contains hull faces, edges, verts
hull_verts = [ele for ele in res['geom'] if isinstance(ele, bmesh.types.BMVert)]
hull_edges = [ele for ele in res['geom'] if isinstance(ele, bmesh.types.BMEdge)]

print(f"Convex hull verts: {len(hull_verts)}, edges: {len(hull_edges)}")

# Sort hull vertices in CCW order around centroid
hull_cos = [v.co.to_2d() for v in hull_verts]
cx = sum((v.x for v in hull_cos)) / len(hull_cos)
cy = sum((v.y for v in hull_cos)) / len(hull_cos)

hull_cos.sort(key=lambda v: math.atan2(v.y - cy, v.x - cx))

print("\n--- 2D CONVEX HULL OF M_URBANPARK ---")
for i, v in enumerate(hull_cos):
    # Find original 3D vertex with closest XY
    closest = min(vert_cos, key=lambda c: (c.x - v.x)**2 + (c.y - v.y)**2)
    rel = closest - kiosko_blender
    print(f"H{i:02d}: global=({closest.x:7.2f}, {closest.y:7.2f}, {closest.z:7.2f}) | Rel_Kiosko=({rel.x:7.2f}, {rel.y:7.2f}, {rel.z:7.2f})")

# Calculate Area of Hull
area = 0.0
for i in range(len(hull_cos)):
    j = (i + 1) % len(hull_cos)
    area += hull_cos[i].x * hull_cos[j].y - hull_cos[j].x * hull_cos[i].y
area = abs(area) * 0.5
print(f"\n2D Area of Hull: {area:.2f} m² ({area/10000:.3f} ha)")

bm.free()
