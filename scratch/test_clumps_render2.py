import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler

bpy.ops.wm.read_factory_settings(use_empty=True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)

bm = bmesh.new()

head_profile = [
    (1.370,  0.046, 0.046,    0.048,   -0.002,   False),
    (1.392,  0.046, 0.044,    0.050,   -0.002,   False),
    (1.412,  0.050, 0.046,    0.056,    0.000,   True),
    (1.428,  0.058, 0.064,    0.068,    0.004,   True),
    (1.445,  0.062, 0.064,    0.074,    0.003,   True),
    (1.458,  0.064, 0.066,    0.082,    0.002,   True),
    (1.468,  0.066, 0.065,    0.086,    0.002,   True),
    (1.478,  0.068, 0.068,    0.090,    0.002,   True),
    (1.492,  0.071, 0.067,    0.092,    0.001,   True),
    (1.505,  0.073, 0.075,    0.093,    0.000,   True),
    (1.515,  0.075, 0.069,    0.093,    0.000,   True),
    (1.532,  0.076, 0.072,    0.092,   -0.002,   True),
    (1.550,  0.075, 0.069,    0.090,   -0.004,   True),
    (1.566,  0.073, 0.064,    0.086,   -0.006,   True),
    (1.582,  0.070, 0.056,    0.080,   -0.008,   False),
    (1.598,  0.062, 0.046,    0.072,   -0.010,   False),
    (1.615,  0.044, 0.032,    0.048,   -0.012,   False),
]

n_ring = 28
rings = []
for l_idx, (z, rx, ry_f, ry_b, y_off, is_face) in enumerate(head_profile):
    cur_ring = []
    for i in range(n_ring):
        ang = (2.0 * math.pi * i) / n_ring
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        x = rx * cos_a
        y = (ry_f if sin_a >= 0 else ry_b) * sin_a + y_off
        v = bm.verts.new((x, y, z))
        cur_ring.append(v)
    rings.append(cur_ring)

for l_idx in range(len(head_profile) - 1):
    r1 = rings[l_idx]
    r2 = rings[l_idx + 1]
    z_mid = (head_profile[l_idx][0] + head_profile[l_idx + 1][0]) * 0.5
    for i in range(n_ring):
        inxt = (i + 1) % n_ring
        f = bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))
        ang_mid = (2.0 * math.pi * (i + 0.5)) / n_ring
        sin_mid = math.sin(ang_mid)
        # Rostro visible
        is_face_skin = (z_mid < 1.548 and sin_mid > -0.05)
        f.material_index = 2 if not is_face_skin else 0

top_vert = bm.verts.new((0.0, -0.012, 1.622))
r_last = rings[-1]
for i in range(n_ring):
    inxt = (i + 1) % n_ring
    f_top = bm.faces.new((r_last[i], r_last[inxt], top_vert))
    f_top.material_index = 2

def add_hair_clump(p_root, p_mid, p_tip, w_root=0.032, w_mid=0.040, w_tip=0.012, depth=0.012, n_seg=8):
    p0 = Vector(p_root)
    p1 = Vector(p_mid)
    p2 = Vector(p_tip)
    prev_verts = None
    for s in range(n_seg + 1):
        t = s / float(n_seg)
        p = (1.0 - t)**2 * p0 + 2.0 * (1.0 - t) * t * p1 + t**2 * p2
        tang = (2.0 * (1.0 - t) * (p1 - p0) + 2.0 * t * (p2 - p1)).normalized()
        up = Vector((0, 0, 1))
        side = tang.cross(up)
        if side.length < 0.001: side = Vector((1, 0, 0))
        else: side.normalize()
        nor = side.cross(tang).normalized()
        
        if t < 0.5:
            w = w_root + (w_mid - w_root) * (t * 2.0)
        else:
            w = w_mid + (w_tip - w_mid) * ((t - 0.5) * 2.0)
        dp = depth * (1.0 - 0.55 * t)
        
        v_left  = bm.verts.new(p - side * (w * 0.5))
        v_mid_l = bm.verts.new(p - side * (w * 0.25) + nor * (dp * 0.70))
        v_crest = bm.verts.new(p + nor * dp)
        v_mid_r = bm.verts.new(p + side * (w * 0.25) + nor * (dp * 0.70))
        v_right = bm.verts.new(p + side * (w * 0.5))
        
        c_verts = [v_left, v_mid_l, v_crest, v_mid_r, v_right]
        if prev_verts:
            for k in range(4):
                f = bm.faces.new((prev_verts[k], prev_verts[k+1], c_verts[k+1], c_verts[k]))
                f.material_index = 2
        prev_verts = c_verts
    
    v_tip = bm.verts.new(p2 + tang * 0.003)
    for k in range(4):
        f = bm.faces.new((prev_verts[k], prev_verts[k+1], v_tip))
        f.material_index = 2

# 1. Cobertura de la corona y bóveda craneal (suave, envolvente)
for xo, ang_s in [(0.0, 0.0), (0.028, 0.08), (-0.028, -0.08), (0.052, 0.15), (-0.052, -0.15)]:
    add_hair_clump((xo * 0.6, 0.038, 1.624), (xo * 0.9, -0.020, 1.626), (xo * 1.1, -0.065, 1.565),
                   w_root=0.038, w_mid=0.046, w_tip=0.020, depth=0.010)

# 2. Flequillo frontal natural peinado a los lados desde la raya (X = -0.008)
# Lado izquierdo
add_hair_clump(( 0.002, 0.058, 1.582), ( 0.042, 0.074, 1.558), ( 0.078, 0.050, 1.520), w_root=0.028, w_mid=0.036, w_tip=0.018, depth=0.011)
add_hair_clump(( 0.018, 0.054, 1.590), ( 0.060, 0.068, 1.564), ( 0.092, 0.035, 1.508), w_root=0.030, w_mid=0.040, w_tip=0.018, depth=0.012)
add_hair_clump(( 0.032, 0.048, 1.598), ( 0.078, 0.058, 1.568), ( 0.104, 0.020, 1.495), w_root=0.032, w_mid=0.042, w_tip=0.018, depth=0.012)

# Lado derecho
add_hair_clump((-0.012, 0.058, 1.582), (-0.050, 0.074, 1.558), (-0.085, 0.050, 1.520), w_root=0.028, w_mid=0.036, w_tip=0.018, depth=0.011)
add_hair_clump((-0.026, 0.054, 1.590), (-0.068, 0.068, 1.564), (-0.098, 0.035, 1.508), w_root=0.030, w_mid=0.040, w_tip=0.018, depth=0.012)
add_hair_clump((-0.040, 0.048, 1.598), (-0.084, 0.058, 1.568), (-0.108, 0.020, 1.495), w_root=0.032, w_mid=0.042, w_tip=0.018, depth=0.012)

# 3. Laterales 70s voluminosos cubriendo orejas
for sgn in (1.0, -1.0):
    add_hair_clump((sgn * 0.070, 0.028, 1.572), (sgn * 0.108, 0.018, 1.505), (sgn * 0.095, 0.005, 1.440),
                   w_root=0.032, w_mid=0.046, w_tip=0.020, depth=0.015)
    add_hair_clump((sgn * 0.068, -0.008, 1.575), (sgn * 0.114, -0.015, 1.495), (sgn * 0.096, -0.028, 1.428),
                   w_root=0.035, w_mid=0.050, w_tip=0.022, depth=0.016)
    add_hair_clump((sgn * 0.064, -0.038, 1.570), (sgn * 0.106, -0.048, 1.488), (sgn * 0.088, -0.054, 1.422),
                   w_root=0.032, w_mid=0.046, w_tip=0.020, depth=0.015)
    # Mechón inferior de patilla
    add_hair_clump((sgn * 0.082, 0.008, 1.460), (sgn * 0.098, -0.010, 1.415), (sgn * 0.078, -0.028, 1.385),
                   w_root=0.026, w_mid=0.036, w_tip=0.016, depth=0.012)

# 4. Caída posterior en nuca
for nx in (-0.045, -0.022, 0.000, 0.022, 0.045):
    add_hair_clump((nx * 0.8, -0.062, 1.568), (nx * 1.1, -0.084, 1.478), (nx * 0.9, -0.078, 1.402),
                   w_root=0.030, w_mid=0.040, w_tip=0.018, depth=0.013)

bm.normal_update()
for f in bm.faces: f.smooth = True

me = bpy.data.meshes.new("TestClumpsMesh2")
bm.to_mesh(me)
bm.free()

scene = bpy.context.scene
obj = bpy.data.objects.new("TestHead2", me)
scene.collection.objects.link(obj)

mat_skin = bpy.data.materials.new("Skin2")
mat_skin.use_nodes = True
mat_skin.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.485, 0.345, 0.265, 1.0)
mat_skin.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.55
me.materials.append(mat_skin)

mat_eyes = bpy.data.materials.new("Eyes2")
me.materials.append(mat_eyes)

mat_hair = bpy.data.materials.new("Hair2")
mat_hair.use_nodes = True
mat_hair.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.09, 0.07, 0.06, 1.0)
mat_hair.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.65
me.materials.append(mat_hair)

cam_data = bpy.data.cameras.new("Cam2")
cam_data.lens = 85.0
cam = bpy.data.objects.new("Cam2", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = Vector((0.0, 1.30, 1.51))
target = Vector((0.0, 0.0, 1.50))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()

ld1 = bpy.data.lights.new('Key', 'AREA')
ld1.energy = 55.0
ld1.size = 1.0
lo1 = bpy.data.objects.new('Key', ld1)
lo1.location = Vector((-0.6, 1.1, 1.65))
lo1.rotation_euler = (target - lo1.location).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(lo1)

ld2 = bpy.data.lights.new('Fill', 'AREA')
ld2.energy = 25.0
ld2.size = 1.4
lo2 = bpy.data.objects.new('Fill', ld2)
lo2.location = Vector((0.6, 1.0, 1.45))
lo2.rotation_euler = (target - lo2.location).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(lo2)

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.film_transparent = True
scene.view_settings.exposure = -0.15
scene.render.filepath = 'scratch/test_astorga_clumps2.png'

bpy.ops.render.render(write_still=True)
print("Rendered to scratch/test_astorga_clumps2.png")
