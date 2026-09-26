import bpy
from mathutils import Vector
import numpy as np
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='godot_project/assets/roadways_baked.glb')

obj = bpy.data.objects['Roadways']
mesh = obj.data

kiosko_blender = Vector((-6.6844, -2.6878, 400.0132))

# Find yellow markings (centerlines) near the park
yellow_idx = None
curb_idx = None
for idx, mat in enumerate(mesh.materials):
    if mat.name == 'M_RoadMarkingYellow':
        yellow_idx = idx
    elif mat.name == 'M_CurbConcrete':
        curb_idx = idx

print(f"Yellow index: {yellow_idx}, Curb index: {curb_idx}")

# Filter yellow line faces near park
yellow_faces = []
for p in mesh.polygons:
    if p.material_index == yellow_idx:
        c = sum((mesh.vertices[vi].co for vi in p.vertices), Vector((0,0,0))) / len(p.vertices)
        if (c.x - kiosko_blender.x)**2 + (c.y - kiosko_blender.y)**2 < 85**2:
            yellow_faces.append(p)

print(f"Yellow line faces near park: {len(yellow_faces)}")

# Check orientation of Av. Benito Juarez (North, Y > kiosko_y + 30)
juarez_faces = []
for p in yellow_faces:
    c = sum((mesh.vertices[vi].co for vi in p.vertices), Vector((0,0,0))) / len(p.vertices)
    if c.y > kiosko_blender.y + 30:
        juarez_faces.append(p)

print(f"Juárez centerline faces: {len(juarez_faces)}")
if juarez_faces:
    j_verts = [mesh.vertices[vi].co for p in juarez_faces for vi in p.vertices]
    xs = np.array([v.x for v in j_verts])
    ys = np.array([v.y for v in j_verts])
    zs = np.array([v.z for v in j_verts])
    # fit line Y = m*X + c
    m, c_line = np.polyfit(xs, ys, 1)
    ang = math.degrees(math.atan(m))
    print(f"Juárez centerline equation: Y = {m:.5f} * X + {c_line:.2f}")
    print(f"  Juárez angle from X-axis: {ang:.3f} deg")
    print(f"  Juárez X span: {min(xs):.1f} to {max(xs):.1f}, Y span: {min(ys):.1f} to {max(ys):.1f}")
    print(f"  Juárez elevation Z: {min(zs):.2f} to {max(zs):.2f}")

# Check Ortiz Rubio (East, X > kiosko_x + 40)
ortiz_faces = []
for p in yellow_faces:
    c = sum((mesh.vertices[vi].co for vi in p.vertices), Vector((0,0,0))) / len(p.vertices)
    if c.x > kiosko_blender.x + 40:
        ortiz_faces.append(p)
print(f"\nOrtiz Rubio centerline faces: {len(ortiz_faces)}")
if ortiz_faces:
    o_verts = [mesh.vertices[vi].co for p in ortiz_faces for vi in p.vertices]
    xs = np.array([v.x for v in o_verts])
    ys = np.array([v.y for v in o_verts])
    # fit line X = m*Y + c
    m_inv, c_inv = np.polyfit(ys, xs, 1)
    ang = math.degrees(math.atan(m_inv))
    print(f"Ortiz Rubio centerline equation: X = {m_inv:.5f} * Y + {c_inv:.2f}")
    print(f"  Ortiz Rubio angle from Y-axis: {ang:.3f} deg")

# Check Cárdenas (West, X < kiosko_x - 40)
cardenas_faces = []
for p in yellow_faces:
    c = sum((mesh.vertices[vi].co for vi in p.vertices), Vector((0,0,0))) / len(p.vertices)
    if c.x < kiosko_blender.x - 40:
        cardenas_faces.append(p)
print(f"\nCárdenas centerline faces: {len(cardenas_faces)}")
if cardenas_faces:
    c_verts = [mesh.vertices[vi].co for p in cardenas_faces for vi in p.vertices]
    xs = np.array([v.x for v in c_verts])
    ys = np.array([v.y for v in c_verts])
    m_inv, c_inv = np.polyfit(ys, xs, 1)
    ang = math.degrees(math.atan(m_inv))
    print(f"Cárdenas centerline equation: X = {m_inv:.5f} * Y + {c_inv:.2f}")
    print(f"  Cárdenas angle from Y-axis: {ang:.3f} deg")

# Check Libertad (South, Y < kiosko_y - 30)
libertad_faces = []
for p in yellow_faces:
    c = sum((mesh.vertices[vi].co for vi in p.vertices), Vector((0,0,0))) / len(p.vertices)
    if c.y < kiosko_blender.y - 30:
        libertad_faces.append(p)
print(f"\nLibertad centerline faces: {len(libertad_faces)}")
if libertad_faces:
    l_verts = [mesh.vertices[vi].co for p in libertad_faces for vi in p.vertices]
    xs = np.array([v.x for v in l_verts])
    ys = np.array([v.y for v in l_verts])
    m, c_line = np.polyfit(xs, ys, 1)
    ang = math.degrees(math.atan(m))
    print(f"Libertad centerline equation: Y = {m:.5f} * X + {c_line:.2f}")
    print(f"  Libertad angle from X-axis: {ang:.3f} deg")
