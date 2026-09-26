import bpy
from mathutils import Vector
import numpy as np
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='godot_project/assets/manzanas_baked.glb')

obj = bpy.data.objects['UrbanManzanas']
mesh = obj.data

# We want the boundary between M_UrbanPark and M_UrbanSidewalk!
park_mat_idx = [i for i, m in enumerate(mesh.materials) if m.name == 'M_UrbanPark'][0]
sidewalk_mat_idx = [i for i, m in enumerate(mesh.materials) if m.name == 'M_UrbanSidewalk'][0]

kiosko_blender = Vector((-6.6844, -2.6878, 400.0132))

# Find all edges shared between a face with M_UrbanPark and a face with M_UrbanSidewalk
edge_park = {}
edge_sidewalk = {}

for p in mesh.polygons:
    c = sum((mesh.vertices[vi].co for vi in p.vertices), Vector((0,0,0))) / len(p.vertices)
    if (c.x - kiosko_blender.x)**2 + (c.y - kiosko_blender.y)**2 < 85**2:
        vs = list(p.vertices)
        for i in range(len(vs)):
            e = tuple(sorted((vs[i], vs[(i+1)%len(vs)])))
            if p.material_index == park_mat_idx:
                edge_park[e] = edge_park.get(e, 0) + 1
            elif p.material_index == sidewalk_mat_idx:
                edge_sidewalk[e] = edge_sidewalk.get(e, 0) + 1

shared_boundary = [e for e in edge_park if e in edge_sidewalk]
print(f"Shared boundary edges between Park and Sidewalk: {len(shared_boundary)}")

if shared_boundary:
    shared_verts = set()
    for e in shared_boundary:
        shared_verts.add(e[0])
        shared_verts.add(e[1])
    print(f"Shared boundary vertices: {len(shared_verts)}")
    
    # Let's inspect these vertices
    b_verts = [mesh.vertices[vi].co for vi in shared_verts]
    xs = [v.x for v in b_verts]
    ys = [v.y for v in b_verts]
    zs = [v.z for v in b_verts]
    print(f"X: {min(xs):.2f} to {max(xs):.2f}")
    print(f"Y: {min(ys):.2f} to {max(ys):.2f}")
    print(f"Z: {min(zs):.2f} to {max(zs):.2f}")
    
    # Let's group vertices by side:
    # North (Y > 15), South (Y < -20), East (X > 30), West (X < -30)
    north_pts = [v for v in b_verts if v.y > 20]
    south_pts = [v for v in b_verts if v.y < -25]
    east_pts = [v for v in b_verts if v.x > 35]
    west_pts = [v for v in b_verts if v.x < -45]
    
    print(f"\nNorth boundary (Juárez side) points: {len(north_pts)}")
    if north_pts:
        nx = np.array([v.x for v in north_pts])
        ny = np.array([v.y for v in north_pts])
        m_n, c_n = np.polyfit(nx, ny, 1)
        print(f"  Line: Y = {m_n:.5f} * X + {c_n:.2f} (angle = {math.degrees(math.atan(m_n)):.3f} deg)")
        print(f"  X span: {min(nx):.2f} to {max(nx):.2f}")
        
    print(f"\nEast boundary (Ortiz Rubio side) points: {len(east_pts)}")
    if east_pts:
        ex = np.array([v.x for v in east_pts])
        ey = np.array([v.y for v in east_pts])
        m_e, c_e = np.polyfit(ey, ex, 1)
        print(f"  Line: X = {m_e:.5f} * Y + {c_e:.2f} (angle = {math.degrees(math.atan(m_e)):.3f} deg)")
        print(f"  Y span: {min(ey):.2f} to {max(ey):.2f}")
        
    print(f"\nSouth boundary (Libertad side) points: {len(south_pts)}")
    if south_pts:
        sx = np.array([v.x for v in south_pts])
        sy = np.array([v.y for v in south_pts])
        m_s, c_s = np.polyfit(sx, sy, 1)
        print(f"  Line: Y = {m_s:.5f} * X + {c_s:.2f} (angle = {math.degrees(math.atan(m_s)):.3f} deg)")
        print(f"  X span: {min(sx):.2f} to {max(sx):.2f}")
        
    print(f"\nWest boundary (Cárdenas side) points: {len(west_pts)}")
    if west_pts:
        wx = np.array([v.x for v in west_pts])
        wy = np.array([v.y for v in west_pts])
        m_w, c_w = np.polyfit(wy, wx, 1)
        print(f"  Line: X = {m_w:.5f} * Y + {c_w:.2f} (angle = {math.degrees(math.atan(m_w)):.3f} deg)")
        print(f"  Y span: {min(wy):.2f} to {max(wy):.2f}")
