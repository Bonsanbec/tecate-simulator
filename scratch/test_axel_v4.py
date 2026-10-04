"""
Axel V4: Integración completa de cuerpo continuo orgánico (Skin + Subsurf),
cabeza anatómica con rasgos 3D de Axel, manos oponibles, y cero IA.
"""
import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)

clean_scene()

def create_mat(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metallic
    return mat

# =============================================================================
# 1. CUERPO CONTINUO ORGÁNICO (Player_Body_Mesh)
# =============================================================================
body_mesh = bpy.data.meshes.new("Body_Continuous_Mesh")
body_obj = bpy.data.objects.new("Player_Body_Mesh", body_mesh)
bpy.context.scene.collection.objects.link(body_obj)

# Esqueleto para el modificador Skin del cuerpo
nodes = [
    # 0: Pelvis centro
    (0.0, 0.0, 0.96, 0.165, 0.135),
    # 1: Cintura / Ombligo
    (0.0, 0.0, 1.08, 0.155, 0.125),
    # 2: Pecho bajo / Esternón
    (0.0, 0.0, 1.22, 0.180, 0.138),
    # 3: Pecho alto
    (0.0, 0.0, 1.36, 0.200, 0.145),
    # 4: Cuello base de la chamarra
    (0.0, 0.0, 1.46, 0.065, 0.068),

    # Hombros y brazos Izquierda (-X)
    (-0.08, 0.0, 1.44, 0.085, 0.085), # 5: Clavícula L
    (-0.19, 0.0, 1.40, 0.076, 0.076), # 6: Hombro L
    (-0.30, 0.0, 1.16, 0.062, 0.062), # 7: Codo L
    (-0.38, 0.0, 0.92, 0.046, 0.046), # 8: Muñeca L

    # Hombros y brazos Derecha (+X)
    (0.08, 0.0, 1.44, 0.085, 0.085),  # 9: Clavícula R
    (0.19, 0.0, 1.40, 0.076, 0.076),  # 10: Hombro R
    (0.30, 0.0, 1.16, 0.062, 0.062),  # 11: Codo R
    (0.38, 0.0, 0.92, 0.046, 0.046),  # 12: Muñeca R

    # Piernas Izquierda (-X)
    (-0.10, 0.0, 0.92, 0.105, 0.105), # 13: Cadera L
    (-0.11, 0.0, 0.70, 0.096, 0.096), # 14: Muslo L
    (-0.11, 0.0, 0.50, 0.082, 0.082), # 15: Rodilla L
    (-0.11, 0.0, 0.30, 0.072, 0.072), # 16: Pantorrilla L
    (-0.11, 0.0, 0.12, 0.058, 0.058), # 17: Tobillo L
    (-0.11, 0.06, 0.03, 0.062, 0.120),# 18: Pie L

    # Piernas Derecha (+X)
    (0.10, 0.0, 0.92, 0.105, 0.105),  # 19: Cadera R
    (0.11, 0.0, 0.70, 0.096, 0.096),  # 20: Muslo R
    (0.11, 0.0, 0.50, 0.082, 0.082),  # 21: Rodilla R
    (0.11, 0.0, 0.30, 0.072, 0.072),  # 22: Pantorrilla R
    (0.11, 0.0, 0.12, 0.058, 0.058),  # 23: Tobillo R
    (0.11, 0.06, 0.03, 0.062, 0.120), # 24: Pie R
]

edges = [
    # Torso
    (0, 1), (1, 2), (2, 3), (3, 4),
    # Brazo Izquierdo
    (3, 5), (5, 6), (6, 7), (7, 8),
    # Brazo Derecho
    (3, 9), (9, 10), (10, 11), (11, 12),
    # Pierna Izquierda
    (0, 13), (13, 14), (14, 15), (15, 16), (16, 17), (17, 18),
    # Pierna Derecha
    (0, 19), (19, 20), (20, 21), (21, 22), (22, 23), (23, 24),
]

verts = [Vector((n[0], n[1], n[2])) for n in nodes]
body_mesh.from_pydata(verts, edges, [])
body_mesh.update()

# Aplicar Skin Modifier
bpy.context.view_layer.objects.active = body_obj
mod_skin = body_obj.modifiers.new(name="Skin", type='SKIN')
skin_data = body_mesh.skin_vertices[0].data
for i, n in enumerate(nodes):
    skin_data[i].radius = (n[3], n[4])

# Convertir el modificador Skin a malla real para permitir añadir manos, cinturón y materiales
bpy.ops.object.modifier_apply(modifier="Skin")

# Añadir Manos Anatómicas con Pulgar Oponible a la malla del cuerpo
bm_body = bmesh.new()
bm_body.from_mesh(body_mesh)

def add_detailed_hand(bm, p_wrist, sign_x, mat_idx=3):
    w_p = 0.034
    t_p = 0.014
    h_layers = [
        ( 0.000, 0.75, 0.85),
        (-0.025, 0.95, 1.00),
        (-0.055, 1.05, 0.95),
        (-0.075, 1.00, 0.80),
    ]
    h_rings = []
    for dz, ws, ts in h_layers:
        c = p_wrist + Vector((0, 0, dz))
        rng = []
        for i in range(12):
            ang = (2.0 * math.pi * i) / 12.0
            vx = c.x + math.cos(ang) * (w_p * ws)
            vy = c.y + math.sin(ang) * (t_p * ts)
            rng.append(bm.verts.new(Vector((vx, vy, c.z))))
        h_rings.append(rng)
    for li in range(len(h_rings) - 1):
        r0 = h_rings[li]
        r1 = h_rings[li + 1]
        for i in range(12):
            in_idx = (i + 1) % 12
            f = bm.faces.new([r0[i], r0[in_idx], r1[in_idx], r1[i]])
            f.material_index = mat_idx

    def add_digit(pts, rads):
        fr = []
        for pt, r in zip(pts, rads):
            rng = []
            for a in range(8):
                ang = (2.0 * math.pi * a) / 8.0
                rng.append(bm.verts.new(pt + Vector((math.cos(ang) * r, math.sin(ang) * r, 0))))
            fr.append(rng)
        for i in range(len(fr) - 1):
            r0 = fr[i]
            r1 = fr[i + 1]
            for a in range(8):
                an = (a + 1) % 8
                f = bm.faces.new([r0[a], r0[an], r1[an], r1[a]])
                f.material_index = mat_idx
        tip = bm.verts.new(pts[-1] + Vector((0, 0, -rads[-1] * 0.4)))
        for a in range(8):
            an = (a + 1) % 8
            f = bm.faces.new([fr[-1][a], fr[-1][an], tip])
            f.material_index = mat_idx

    # Pulgar oponible medial hacia el fondo/palma
    t_pts = [
        p_wrist + Vector((-sign_x * 0.022, -0.005, -0.025)),
        p_wrist + Vector((-sign_x * 0.034, -0.008, -0.045)),
        p_wrist + Vector((-sign_x * 0.030, -0.016, -0.065)),
        p_wrist + Vector((-sign_x * 0.020, -0.022, -0.080)),
    ]
    add_digit(t_pts, [0.011, 0.010, 0.0085, 0.0065])

    # 4 Dedos
    fdata = [
        (-sign_x * 0.016, 0.066, 0.0090),
        (-sign_x * 0.005, 0.074, 0.0095),
        ( sign_x * 0.007, 0.068, 0.0085),
        ( sign_x * 0.020, 0.052, 0.0075),
    ]
    for fx, flen, frad in fdata:
        kn = p_wrist + Vector((fx, 0.002, -0.075))
        p1 = kn + Vector((0, -0.006, -flen * 0.45))
        p2 = p1 + Vector((0, -0.012, -flen * 0.35))
        pt = p2 + Vector((0, -0.016, -flen * 0.20))
        add_digit([kn, p1, p2, pt], [frad, frad * 0.88, frad * 0.72, frad * 0.50])

add_detailed_hand(bm_body, Vector((-0.38, 0.0, 0.92)), sign_x=-1.0, mat_idx=3)
add_detailed_hand(bm_body, Vector(( 0.38, 0.0, 0.92)), sign_x= 1.0, mat_idx=3)

# Añadir Cinturón de Cuero con Hebilla Metálica
def add_belt_ring(bm, z0, z1, r0, r1):
    r_list = []
    for z, r in [(z0, r0), (z1, r1)]:
        rng = []
        for i in range(24):
            ang = (2.0 * math.pi * i) / 24.0
            vx = math.cos(ang) * (r * 1.04)
            vy = math.sin(ang) * (r * 0.90)
            rng.append(bm.verts.new(Vector((vx, vy, z))))
        r_list.append(rng)
    for i in range(24):
        in_idx = (i + 1) % 24
        f = bm.faces.new([r_list[0][i], r_list[0][in_idx], r_list[1][in_idx], r_list[1][i]])
        f.material_index = 4 # mat_belt

add_belt_ring(bm_body, 1.03, 0.97, 0.170, 0.172)
# Hebilla
b_box = bmesh.ops.create_cube(bm_body, size=0.035, matrix=Matrix.Translation(Vector((0, 0.165, 1.00))))
for v in b_box['verts']:
    for f in v.link_faces:
        f.material_index = 5 # mat_buckle

# Asignar índices de materiales en el cuerpo según la altura Z
for f in bm_body.faces:
    if f.material_index in [3, 4, 5]:
        continue # Manos, cinturón y hebilla ya asignados
    fz = f.calc_center_median().z
    if fz >= 1.01:
        f.material_index = 0 # Chamarra azul marino
    elif fz >= 0.14:
        f.material_index = 1 # Pantalón denim
    else:
        f.material_index = 2 # Zapatos

bm_body.to_mesh(body_mesh)
bm_body.free()

# Materiales del cuerpo
m_jacket = create_mat("Mat_Axel_Jacket", (0.10, 0.12, 0.18, 1.0), roughness=0.60)
m_pants = create_mat("Mat_Axel_Pants", (0.12, 0.13, 0.16, 1.0), roughness=0.85)
m_shoes = create_mat("Mat_Axel_Shoes", (0.12, 0.12, 0.14, 1.0), roughness=0.50)
m_skin = create_mat("Mat_Axel_Skin", (0.76, 0.58, 0.48, 1.0), roughness=0.52)
m_belt = create_mat("Mat_Axel_Belt", (0.24, 0.15, 0.10, 1.0), roughness=0.45)
m_buckle = create_mat("Mat_Axel_Buckle", (0.75, 0.75, 0.78, 1.0), roughness=0.25, metallic=0.95)

body_obj.data.materials.append(m_jacket) # 0
body_obj.data.materials.append(m_pants)  # 1
body_obj.data.materials.append(m_shoes)  # 2
body_obj.data.materials.append(m_skin)   # 3
body_obj.data.materials.append(m_belt)   # 4
body_obj.data.materials.append(m_buckle) # 5

for poly in body_mesh.polygons:
    poly.use_smooth = True

mod_sub_body = body_obj.modifiers.new(name="Subsurf", type='SUBSURF')
mod_sub_body.levels = 1
mod_sub_body.render_levels = 2

# =============================================================================
# 2. CABEZA PROPORCIONADA DE AXEL (Player_Head_Mesh)
# =============================================================================
head_mesh = bpy.data.meshes.new("Head_Detailed_Mesh")
head_obj = bpy.data.objects.new("Player_Head_Mesh", head_mesh)
bpy.context.scene.collection.objects.link(head_obj)

bm_head = bmesh.new()

n_u = 32
n_v = 24
h_grid = []

for vi in range(n_v + 1):
    tv = vi / float(n_v)
    if tv < 0.25: # Cuello (1.46 a 1.53)
        z = 1.460 + (tv / 0.25) * 0.070
        rx = 0.046
        ry_f = 0.048
        ry_b = 0.046
        yc = 0.005
    elif tv < 0.50: # Barbilla, boca y mandíbula (1.53 a 1.585)
        tj = (tv - 0.25) / 0.25
        z = 1.530 + tj * 0.055
        rx = 0.052 + tj * 0.016
        ry_f = 0.060 + tj * 0.016
        ry_b = 0.050 + tj * 0.016
        yc = 0.003
    elif tv < 0.75: # Nariz y ojos (1.585 a 1.650)
        tm = (tv - 0.50) / 0.25
        z = 1.585 + tm * 0.065
        rx = 0.068 + tm * 0.006
        ry_f = 0.076
        ry_b = 0.066 + tm * 0.008
        yc = 0.0
    else: # Frente y cráneo (1.650 a 1.735)
        tt = (tv - 0.75) / 0.25
        z = 1.650 + tt * 0.085
        dome = math.sqrt(max(0.01, 1.0 - (tt * 0.94)**2))
        rx = 0.074 * dome + 0.003
        ry_f = 0.076 * dome + 0.003
        ry_b = 0.076 * dome + 0.003
        yc = -0.008 * tt

    ring = []
    for ui in range(n_u):
        ang = (ui / float(n_u)) * 2.0 * math.pi - (math.pi / 2.0)
        sin_a = math.sin(ang)
        cos_a = math.cos(ang)
        vx = cos_a * rx
        vy = yc + (sin_a * ry_f if sin_a >= 0 else sin_a * ry_b)
        vz = z

        if sin_a > 0:
            # Mentón
            if abs(vz - 1.540) < 0.020 and abs(vx) < 0.026:
                cd = math.sqrt((vx / 0.026)**2 + ((vz - 1.540) / 0.020)**2)
                if cd < 1.0:
                    vy += 0.015 * (1.0 - cd)**2
            # Boca
            if abs(vz - 1.568) < 0.012 and abs(vx) < 0.025:
                lw = (1.0 - abs(vx) / 0.025)
                if vz > 1.568:
                    vy += 0.010 * lw * math.sin(((vz - 1.568) / 0.010) * math.pi)
                else:
                    vy += 0.012 * lw * math.sin(((1.568 - vz) / 0.010) * math.pi)
            # Nariz 3D
            if 1.580 < vz < 1.635 and abs(vx) < 0.022:
                tn = (vz - 1.580) / 0.055
                nw = 0.010 + (1.0 - tn) * 0.010
                if abs(vx) < nw:
                    lf = 1.0 - (abs(vx) / nw)
                    n_proj = 0.025 * math.sin(tn * math.pi * 0.8) if tn < 0.4 else 0.016 + (1.0 - tn) * 0.008
                    vy += n_proj * (lf**1.4)
            # Cuencas de ojos
            for ecx in [-0.032, 0.032]:
                de = math.sqrt(((vx - ecx) / 0.018)**2 + ((vz - 1.628) / 0.014)**2)
                if de < 1.0:
                    vy -= 0.010 * (1.0 - de)**2
            # Nuez de Adán
            if abs(vz - 1.490) < 0.014 and abs(vx) < 0.012:
                vy += 0.005 * (1.0 - abs(vx) / 0.012)

        ring.append(bm_head.verts.new(Vector((vx, vy, vz))))
    h_grid.append(ring)

for vi in range(n_v):
    r0 = h_grid[vi]
    r1 = h_grid[vi + 1]
    for ui in range(n_u):
        un = (ui + 1) % n_u
        f = bm_head.faces.new([r0[ui], r0[un], r1[un], r1[ui]])
        fc = (r0[ui].co + r0[un].co + r1[un].co + r1[ui].co) * 0.25
        if abs(fc.z - 1.568) < 0.012 and abs(fc.x) < 0.022 and fc.y > 0.05:
            f.material_index = 5 # labios
        else:
            f.material_index = 0 # piel

top_vh = bm_head.verts.new(Vector((0.0, -0.008, 1.740)))
for ui in range(n_u):
    un = (ui + 1) % n_u
    f = bm_head.faces.new([h_grid[-1][ui], h_grid[-1][un], top_vh])
    f.material_index = 0

# Globos Oculares 3D en cuencas (Z=1.628, X=+/-0.032)
for ex in [-0.032, 0.032]:
    p_eye = Vector((ex, 0.066, 1.628))
    sph = bmesh.ops.create_uvsphere(bm_head, u_segments=16, v_segments=12, radius=0.012, matrix=Matrix.Translation(p_eye))
    for v in sph['verts']:
        for f in v.link_faces:
            f.material_index = 3 # ojos

    # Párpados
    etop = [
        Vector((ex - 0.014, 0.070, 1.626)),
        Vector((ex - 0.006, 0.076, 1.636)),
        Vector((ex + 0.006, 0.076, 1.636)),
        Vector((ex + 0.014, 0.070, 1.626)),
        Vector((ex + 0.016, 0.073, 1.632)),
        Vector((ex + 0.007, 0.079, 1.641)),
        Vector((ex - 0.007, 0.079, 1.641)),
        Vector((ex - 0.016, 0.073, 1.632)),
    ]
    ev = [bm_head.verts.new(p) for p in etop]
    f1 = bm_head.faces.new([ev[0], ev[1], ev[6], ev[7]])
    f2 = bm_head.faces.new([ev[1], ev[2], ev[5], ev[6]])
    f3 = bm_head.faces.new([ev[2], ev[3], ev[4], ev[5]])
    for ff in [f1, f2, f3]:
        ff.material_index = 0

    # Cejas 3D
    sb = -1.0 if ex < 0 else 1.0
    bpts = [
        Vector((ex - sb * 0.015, 0.073, 1.646)),
        Vector((ex - sb * 0.004, 0.078, 1.654)),
        Vector((ex + sb * 0.010, 0.077, 1.652)),
        Vector((ex + sb * 0.018, 0.072, 1.646)),
        Vector((ex + sb * 0.016, 0.073, 1.650)),
        Vector((ex + sb * 0.008, 0.080, 1.658)),
        Vector((ex - sb * 0.004, 0.081, 1.659)),
        Vector((ex - sb * 0.013, 0.075, 1.651)),
    ]
    bv = [bm_head.verts.new(p) for p in bpts]
    bf1 = bm_head.faces.new([bv[0], bv[1], bv[6], bv[7]])
    bf2 = bm_head.faces.new([bv[1], bv[2], bv[5], bv[6]])
    bf3 = bm_head.faces.new([bv[2], bv[3], bv[4], bv[5]])
    for bf in [bf1, bf2, bf3]:
        bf.material_index = 4 # cejas

# Orejas
for ear_x, ear_sgn in [(-0.070, -1.0), (0.070, 1.0)]:
    p_ear = Vector((ear_x, 0.002, 1.616))
    sph_ear = bmesh.ops.create_uvsphere(bm_head, u_segments=10, v_segments=8, radius=0.014, matrix=Matrix.Translation(p_ear))
    for v in sph_ear['verts']:
        v.co.x = ear_x + (v.co.x - ear_x) * 0.38
        v.co.y = 0.002 + (v.co.y - 0.002) * 0.85
        v.co.z = 1.616 + (v.co.z - 1.616) * 1.25
        for f in v.link_faces:
            f.material_index = 0

# Mechones de Cabello Ondulado (Axel Bangs)
def add_hair_wave(bm, pts, rads):
    sr = []
    for pt, r in zip(pts, rads):
        rng = []
        for a in range(8):
            ang = (2.0 * math.pi * a) / 8.0
            vx = pt.x + math.cos(ang) * r
            vy = pt.y + math.sin(ang) * r * 0.75
            vz = pt.z - math.sin(ang) * r * 0.35
            rng.append(bm.verts.new(Vector((vx, vy, vz))))
        sr.append(rng)
    for i in range(len(sr) - 1):
        r0 = sr[i]
        r1 = sr[i + 1]
        for a in range(8):
            an = (a + 1) % 8
            f = bm.faces.new([r0[a], r0[an], r1[an], r1[a]])
            f.material_index = 2
    tip = bm.verts.new(pts[-1] + Vector((0, 0, -rads[-1] * 0.4)))
    for a in range(8):
        an = (a + 1) % 8
        f = bm.faces.new([sr[-1][a], sr[-1][an], tip])
        f.material_index = 2

hair_locks = [
    ([Vector((-0.036, 0.072, 1.680)), Vector((-0.030, 0.080, 1.665)), Vector((-0.022, 0.082, 1.648))], [0.010, 0.008, 0.003]),
    ([Vector((-0.018, 0.076, 1.683)), Vector((-0.012, 0.084, 1.668)), Vector((-0.005, 0.085, 1.646))], [0.011, 0.009, 0.003]),
    ([Vector((-0.002, 0.078, 1.683)), Vector(( 0.005, 0.085, 1.668)), Vector(( 0.012, 0.085, 1.646))], [0.011, 0.009, 0.003]),
    ([Vector(( 0.014, 0.077, 1.683)), Vector(( 0.020, 0.084, 1.668)), Vector(( 0.026, 0.084, 1.648))], [0.011, 0.009, 0.003]),
    ([Vector(( 0.028, 0.074, 1.680)), Vector(( 0.034, 0.080, 1.665)), Vector(( 0.038, 0.081, 1.650))], [0.010, 0.008, 0.003]),
    # Patillas
    ([Vector((-0.066, 0.020, 1.675)), Vector((-0.068, 0.018, 1.645)), Vector((-0.068, 0.015, 1.615))], [0.009, 0.007, 0.003]),
    ([Vector(( 0.066, 0.020, 1.675)), Vector(( 0.070, 0.018, 1.645)), Vector(( 0.068, 0.015, 1.615))], [0.009, 0.007, 0.003]),
    # Nuca
    ([Vector((-0.028, -0.066, 1.680)), Vector((-0.028, -0.062, 1.640)), Vector((-0.026, -0.058, 1.605))], [0.010, 0.008, 0.003]),
    ([Vector(( 0.000, -0.068, 1.680)), Vector(( 0.000, -0.064, 1.640)), Vector(( 0.000, -0.060, 1.603))], [0.011, 0.009, 0.003]),
    ([Vector(( 0.028, -0.066, 1.680)), Vector(( 0.028, -0.062, 1.640)), Vector(( 0.026, -0.058, 1.605))], [0.010, 0.008, 0.003]),
]
for pts, rads in hair_locks:
    add_hair_wave(bm_head, pts, rads)

# Beanie de Lana Verde Oliva Ajustado y Redondeado
beanie_levels = [
    (1.660, 1.630, 0.078, 0.082, 0.003),
    (1.678, 1.648, 0.082, 0.086, 0.004),
    (1.696, 1.666, 0.080, 0.084, 0.002),
    (1.718, 1.694, 0.076, 0.080, 0.000),
    (1.740, 1.720, 0.066, 0.070, 0.000),
    (1.758, 1.742, 0.048, 0.052, 0.000),
    (1.770, 1.760, 0.022, 0.024, 0.000),
]
beanie_rings = []
for zf, zb, rx, ry, rib_amp in beanie_levels:
    br = []
    for i in range(28):
        ang = (2.0 * math.pi * i) / 28.0
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        t_fb = (cos_a + 1.0) * 0.5
        z = zb * (1.0 - t_fb) + zf * t_fb
        rib = math.sin(i * 4.0 * math.pi) * rib_amp if rib_amp > 0 else 0.0
        vx = sin_a * (rx + rib)
        vy = (cos_a * ry) - 0.008 * (1.0 - t_fb)
        br.append(bm_head.verts.new(Vector((vx, vy, z))))
    beanie_rings.append(br)

for r in range(len(beanie_rings) - 1):
    r0 = beanie_rings[r]
    r1 = beanie_rings[r + 1]
    for i in range(28):
        in_idx = (i + 1) % 28
        f = bm_head.faces.new([r0[i], r0[in_idx], r1[in_idx], r1[i]])
        f.material_index = 1

top_beanie = bm_head.verts.new(Vector((0.0, -0.012, 1.775)))
for i in range(28):
    in_idx = (i + 1) % 28
    f = bm_head.faces.new([beanie_rings[-1][i], beanie_rings[-1][in_idx], top_beanie])
    f.material_index = 1

bm_head.to_mesh(head_mesh)
bm_head.free()

# Materiales de la Cabeza
m_skin_head = create_mat("Mat_Axel_Skin", (0.76, 0.58, 0.48, 1.0), roughness=0.52)
m_beanie = create_mat("Mat_Axel_Beanie", (0.30, 0.34, 0.22, 1.0), roughness=0.88)
m_hair = create_mat("Mat_Axel_Hair", (0.08, 0.06, 0.05, 1.0), roughness=0.55)
m_eyes = create_mat("Mat_Axel_Eyes", (0.16, 0.11, 0.08, 1.0), roughness=0.05)
m_brows = create_mat("Mat_Axel_Brows", (0.07, 0.05, 0.04, 1.0), roughness=0.65)
m_lips = create_mat("Mat_Axel_Lips", (0.68, 0.40, 0.36, 1.0), roughness=0.40)

head_obj.data.materials.append(m_skin_head) # 0
head_obj.data.materials.append(m_beanie)    # 1
head_obj.data.materials.append(m_hair)      # 2
head_obj.data.materials.append(m_eyes)      # 3
head_obj.data.materials.append(m_brows)     # 4
head_obj.data.materials.append(m_lips)      # 5

for poly in head_mesh.polygons:
    poly.use_smooth = True

mod_sub_head = head_obj.modifiers.new(name="Subsurf", type='SUBSURF')
mod_sub_head.levels = 1
mod_sub_head.render_levels = 2

# Render de prueba
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.device = 'CPU'
scene.render.resolution_x = 720
scene.render.resolution_y = 1280

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 65.0
cam = bpy.data.objects.new("Cam", cam_data)
cam.location = Vector((0.15, 2.2, 1.34))
cam.rotation_euler = (math.radians(88.0), 0.0, math.radians(176.0))
scene.collection.objects.link(cam)
scene.camera = cam

# Luces suaves
key_data = bpy.data.lights.new("Key", type='AREA')
key_data.energy = 55.0
key_data.size = 1.0
key = bpy.data.objects.new("Key", key_data)
key.location = Vector((-1.0, 1.8, 1.9))
scene.collection.objects.link(key)

fill_data = bpy.data.lights.new("Fill", type='AREA')
fill_data.energy = 22.0
fill_data.size = 1.4
fill = bpy.data.objects.new("Fill", fill_data)
fill.location = Vector((1.2, 1.8, 1.4))
scene.collection.objects.link(fill)

rim_data = bpy.data.lights.new("Rim", type='SPOT')
rim_data.energy = 45.0
rim_data.spot_size = math.radians(70.0)
rim = bpy.data.objects.new("Rim", rim_data)
rim.location = Vector((0.0, -1.5, 2.0))
rim.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
scene.collection.objects.link(rim)

scene.render.filepath = os.path.abspath("scratch/test_axel_v4_render.png")
bpy.ops.render.render(write_still=True)
print("Rendered scratch/test_axel_v4_render.png")
