import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler

# Clean scene
bpy.ops.wm.read_factory_settings(use_empty=True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)

# Build a head + hair test
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
        is_face_skin = (z_mid < 1.555 and sin_mid > -0.10)
        f.material_index = 2 if not is_face_skin else 0

top_vert = bm.verts.new((0.0, -0.012, 1.622))
r_last = rings[-1]
for i in range(n_ring):
    inxt = (i + 1) % n_ring
    f_top = bm.faces.new((r_last[i], r_last[inxt], top_vert))
    f_top.material_index = 2

# Función para mechones volumétricos estilizados (curva Bézier con perfil biselado)
def add_hair_clump(p_root, p_mid, p_tip, w_root=0.032, w_mid=0.040, w_tip=0.012, depth=0.012, n_seg=8):
    p0 = Vector(p_root)
    p1 = Vector(p_mid)
    p2 = Vector(p_tip)
    prev_verts = None
    for s in range(n_seg + 1):
        t = s / float(n_seg)
        # Posición a lo largo de la curva
        p = (1.0 - t)**2 * p0 + 2.0 * (1.0 - t) * t * p1 + t**2 * p2
        tang = (2.0 * (1.0 - t) * (p1 - p0) + 2.0 * t * (p2 - p1)).normalized()
        up = Vector((0, 0, 1))
        side = tang.cross(up)
        if side.length < 0.001: side = Vector((1, 0, 0))
        else: side.normalize()
        nor = side.cross(tang).normalized()
        
        # Perfil de ancho y grosor
        if t < 0.5:
            w = w_root + (w_mid - w_root) * (t * 2.0)
        else:
            w = w_mid + (w_tip - w_mid) * ((t - 0.5) * 2.0)
        dp = depth * (1.0 - 0.6 * t)
        
        # 5 vértices biselados formando una teja convexa
        v_left  = bm.verts.new(p - side * (w * 0.5))
        v_mid_l = bm.verts.new(p - side * (w * 0.25) + nor * (dp * 0.75))
        v_crest = bm.verts.new(p + nor * dp)
        v_mid_r = bm.verts.new(p + side * (w * 0.25) + nor * (dp * 0.75))
        v_right = bm.verts.new(p + side * (w * 0.5))
        
        c_verts = [v_left, v_mid_l, v_crest, v_mid_r, v_right]
        if prev_verts:
            for k in range(4):
                f = bm.faces.new((prev_verts[k], prev_verts[k+1], c_verts[k+1], c_verts[k]))
                f.material_index = 2
        prev_verts = c_verts
    
    # Cierre en la punta
    v_tip = bm.verts.new(p2 + tang * 0.004)
    for k in range(4):
        f = bm.faces.new((prev_verts[k], prev_verts[k+1], v_tip))
        f.material_index = 2

# Generar melena setentera con mechones canónicos de Astorga (scratch/crop_face.png):
# 1. Flequillo peinado hacia los lados desde una raya sutil (parting at X = -0.010)
# Flequillo izquierdo
add_hair_clump(( 0.000, 0.066, 1.572), ( 0.045, 0.076, 1.550), ( 0.082, 0.045, 1.510), w_root=0.024, w_mid=0.034, w_tip=0.015, depth=0.010)
add_hair_clump(( 0.018, 0.062, 1.584), ( 0.065, 0.070, 1.558), ( 0.096, 0.030, 1.498), w_root=0.026, w_mid=0.038, w_tip=0.016, depth=0.012)
# Flequillo derecho
add_hair_clump((-0.015, 0.066, 1.572), (-0.055, 0.076, 1.550), (-0.088, 0.045, 1.510), w_root=0.024, w_mid=0.034, w_tip=0.015, depth=0.010)
add_hair_clump((-0.030, 0.062, 1.584), (-0.075, 0.070, 1.558), (-0.100, 0.030, 1.498), w_root=0.026, w_mid=0.038, w_tip=0.016, depth=0.012)

# 2. Mechones laterales voluminosos que cubren las orejas y definen la silueta setentera
for sgn in (1.0, -1.0):
    # Mechón anterior de sien y pómulo
    add_hair_clump((sgn * 0.065, 0.042, 1.570), (sgn * 0.104, 0.030, 1.505), (sgn * 0.090, 0.015, 1.442), w_root=0.028, w_mid=0.044, w_tip=0.018, depth=0.016)
    # Mechón principal sobre la oreja (volumen máximo lateral)
    add_hair_clump((sgn * 0.068, 0.012, 1.580), (sgn * 0.112, -0.005, 1.495), (sgn * 0.094, -0.020, 1.430), w_root=0.032, w_mid=0.048, w_tip=0.020, depth=0.018)
    # Mechón posterior de oreja
    add_hair_clump((sgn * 0.065, -0.022, 1.580), (sgn * 0.106, -0.038, 1.490), (sgn * 0.086, -0.048, 1.425), w_root=0.030, w_mid=0.045, w_tip=0.018, depth=0.016)
    # Mechón inferior de patilla / caída hacia cuello
    add_hair_clump((sgn * 0.080, 0.005, 1.465), (sgn * 0.096, -0.015, 1.420), (sgn * 0.075, -0.035, 1.385), w_root=0.024, w_mid=0.035, w_tip=0.014, depth=0.012)

# 3. Corona superior y bóveda craneal peinada hacia atrás
add_hair_clump(( 0.000, 0.042, 1.622), ( 0.000, -0.015, 1.628), ( 0.000, -0.068, 1.575), w_root=0.035, w_mid=0.048, w_tip=0.022, depth=0.014)
add_hair_clump(( 0.035, 0.035, 1.615), ( 0.045, -0.020, 1.620), ( 0.038, -0.070, 1.565), w_root=0.032, w_mid=0.045, w_tip=0.020, depth=0.014)
add_hair_clump((-0.035, 0.035, 1.615), (-0.045, -0.020, 1.620), (-0.038, -0.070, 1.565), w_root=0.032, w_mid=0.045, w_tip=0.020, depth=0.014)

# 4. Caída posterior en nuca hacia el cuello
for nx in (-0.040, -0.015, 0.015, 0.040):
    add_hair_clump((nx * 0.8, -0.065, 1.570), (nx * 1.1, -0.085, 1.480), (nx * 0.9, -0.080, 1.405), w_root=0.028, w_mid=0.038, w_tip=0.016, depth=0.014)

bm.normal_update()
for f in bm.faces: f.smooth = True

me = bpy.data.meshes.new("TestClumpsMesh")
bm.to_mesh(me)
bm.free()

obj = bpy.data.objects.new("TestHead", me)
scene = bpy.context.scene
scene.collection.objects.link(obj)

# Materiales
mat_skin = bpy.data.materials.new("Skin")
mat_skin.use_nodes = True
mat_skin.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.485, 0.345, 0.265, 1.0)
mat_skin.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.55
me.materials.append(mat_skin)

mat_eyes = bpy.data.materials.new("Eyes")
me.materials.append(mat_eyes)

mat_hair = bpy.data.materials.new("Hair")
mat_hair.use_nodes = True
mat_hair.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.09, 0.07, 0.06, 1.0)
mat_hair.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.65
me.materials.append(mat_hair)

# Cámara
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 85.0
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = Vector((0.0, 1.30, 1.51))
target = Vector((0.0, 0.0, 1.50))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()

# Luces
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
scene.render.filepath = 'scratch/test_astorga_clumps.png'

bpy.ops.render.render(write_still=True)
print("Rendered to scratch/test_astorga_clumps.png")
