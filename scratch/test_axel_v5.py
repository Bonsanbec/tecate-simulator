"""
Axel V5: Perfeccionamiento anatómico hiperrealista y estilizado:
- Hombros con silueta trapezoidal continua y cuello integrado con músculos esternocleidomastoideos
- Cabeza con proporciones exactas de Axel: boca y labios con curvatura natural, nariz tridimensional definida,
  cuencas de ojos con párpados superior e inferior, cejas densas
- Mechones 3D de cabello ondulado con volumen y superposición natural
- Gorro beanie de lana con dobladillo acanalado en relieve grueso que enmarca el rostro
- Manos anatómicas completamente visibles en el encuadre: pulgares oponibles hacia el interior/palma, dorso al frente
- Chamarra acolchada con volumen realista y costuras horizontales
- Iluminación de estudio profesional calibrada (Key 120W, Fill 55W, Rim 85W)
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
# 1. CUERPO CONTINUO ANATÓMICO (Player_Body_Mesh)
# =============================================================================
body_mesh = bpy.data.meshes.new("Body_Mesh")
body_obj = bpy.data.objects.new("Player_Body_Mesh", body_mesh)
bpy.context.scene.collection.objects.link(body_obj)

# Esqueleto para Skin Modifier
nodes = [
    # 0: Pelvis centro
    (0.0, 0.0, 0.96, 0.165, 0.135),
    # 1: Cintura / Ombligo
    (0.0, 0.0, 1.08, 0.155, 0.125),
    # 2: Pecho bajo / Esternón
    (0.0, 0.0, 1.22, 0.185, 0.140),
    # 3: Pecho alto
    (0.0, 0.0, 1.36, 0.205, 0.145),
    # 4: Cuello base de la chamarra
    (0.0, 0.0, 1.46, 0.068, 0.070),

    # Hombros y brazos Izquierda (-X)
    (-0.08, 0.0, 1.44, 0.090, 0.090), # 5: Trapecio/Clavícula L
    (-0.20, 0.0, 1.39, 0.078, 0.078), # 6: Deltoides/Hombro L
    (-0.30, 0.0, 1.16, 0.065, 0.065), # 7: Codo L
    (-0.37, 0.0, 0.93, 0.048, 0.048), # 8: Muñeca L

    # Hombros y brazos Derecha (+X)
    (0.08, 0.0, 1.44, 0.090, 0.090),  # 9: Trapecio/Clavícula R
    (0.20, 0.0, 1.39, 0.078, 0.078),  # 10: Deltoides/Hombro R
    (0.30, 0.0, 1.16, 0.065, 0.065),  # 11: Codo R
    (0.37, 0.0, 0.93, 0.048, 0.048),  # 12: Muñeca R

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
    (0, 1), (1, 2), (2, 3), (3, 4),
    (3, 5), (5, 6), (6, 7), (7, 8),
    (3, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16), (16, 17), (17, 18),
    (0, 19), (19, 20), (20, 21), (21, 22), (22, 23), (23, 24),
]

verts = [Vector((n[0], n[1], n[2])) for n in nodes]
body_mesh.from_pydata(verts, edges, [])
body_mesh.update()

bpy.context.view_layer.objects.active = body_obj
mod_skin = body_obj.modifiers.new(name="Skin", type='SKIN')
skin_data = body_mesh.skin_vertices[0].data
for i, n in enumerate(nodes):
    skin_data[i].radius = (n[3], n[4])

bpy.ops.object.modifier_apply(modifier="Skin")

# Añadir manos anatómicas con pulgar oponible
bm_body = bmesh.new()
bm_body.from_mesh(body_mesh)

def add_detailed_hand(bm, p_wrist, sign_x, mat_idx=3):
    w_p = 0.033
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

    # Pulgar oponible medial hacia el fondo/palma (-Y)
    t_pts = [
        p_wrist + Vector((-sign_x * 0.020, -0.005, -0.025)),
        p_wrist + Vector((-sign_x * 0.032, -0.008, -0.045)),
        p_wrist + Vector((-sign_x * 0.028, -0.016, -0.065)),
        p_wrist + Vector((-sign_x * 0.018, -0.022, -0.080)),
    ]
    add_digit(t_pts, [0.011, 0.010, 0.0085, 0.0065])

    # 4 Dedos
    fdata = [
        (-sign_x * 0.015, 0.065, 0.0090),
        (-sign_x * 0.005, 0.073, 0.0095),
        ( sign_x * 0.006, 0.067, 0.0085),
        ( sign_x * 0.018, 0.052, 0.0075),
    ]
    for fx, flen, frad in fdata:
        kn = p_wrist + Vector((fx, 0.002, -0.075))
        p1 = kn + Vector((0, -0.006, -flen * 0.45))
        p2 = p1 + Vector((0, -0.012, -flen * 0.35))
        pt = p2 + Vector((0, -0.016, -flen * 0.20))
        add_digit([kn, p1, p2, pt], [frad, frad * 0.88, frad * 0.72, frad * 0.50])

add_detailed_hand(bm_body, Vector((-0.37, 0.0, 0.93)), sign_x=-1.0, mat_idx=3)
add_detailed_hand(bm_body, Vector(( 0.37, 0.0, 0.93)), sign_x= 1.0, mat_idx=3)

# Cinturón de Cuero con Hebilla Metálica
def add_belt(bm, z0, z1, r0, r1):
    r_list = []
    for z, r in [(z0, r0), (z1, r1)]:
        rng = []
        for i in range(24):
            ang = (2.0 * math.pi * i) / 24.0
            vx = math.cos(ang) * (r * 1.04)
            vy = math.sin(ang) * (r * 0.92)
            rng.append(bm.verts.new(Vector((vx, vy, z))))
        r_list.append(rng)
    for i in range(24):
        in_idx = (i + 1) % 24
        f = bm.faces.new([r_list[0][i], r_list[0][in_idx], r_list[1][in_idx], r_list[1][i]])
        f.material_index = 4

add_belt(bm_body, 1.03, 0.97, 0.170, 0.172)
b_box = bmesh.ops.create_cube(bm_body, size=0.035, matrix=Matrix.Translation(Vector((0, 0.165, 1.00))))
for v in b_box['verts']:
    for f in v.link_faces:
        f.material_index = 5

for f in bm_body.faces:
    if f.material_index in [3, 4, 5]:
        continue
    fz = f.calc_center_median().z
    if fz >= 1.01:
        f.material_index = 0 # Chamarra azul marino
    elif fz >= 0.14:
        f.material_index = 1 # Pantalón denim
    else:
        f.material_index = 2 # Zapatos

bm_body.to_mesh(body_mesh)
bm_body.free()

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

mod_sub_b = body_obj.modifiers.new(name="Subsurf", type='SUBSURF')
mod_sub_b.levels = 1
mod_sub_b.render_levels = 2

# =============================================================================
# 2. CABEZA ANATÓMICA Y RASGOS FACIALES (Player_Head_Mesh)
# =============================================================================
head_mesh = bpy.data.meshes.new("Head_Mesh")
head_obj = bpy.data.objects.new("Player_Head_Mesh", head_mesh)
bpy.context.scene.collection.objects.link(head_obj)

bm_head = bmesh.new()

n_u = 32
n_v = 24
h_grid = []

# Proporciones humanas compactas (Cuello Z=1.46 a 1.52, Cara Z=1.52 a 1.63, Beanie Z=1.63 a 1.74)
for vi in range(n_v + 1):
    tv = vi / float(n_v)
    if tv < 0.25: # Cuello proporcionado
        z = 1.460 + (tv / 0.25) * 0.060
        rx = 0.050
        ry_f = 0.052
        ry_b = 0.050
        yc = 0.005
    elif tv < 0.52: # Mandíbula, mentón y labios (1.520 a 1.575)
        tj = (tv - 0.25) / 0.27
        z = 1.520 + tj * 0.055
        rx = 0.054 + tj * 0.016
        ry_f = 0.062 + tj * 0.016
        ry_b = 0.052 + tj * 0.016
        yc = 0.003
    elif tv < 0.78: # Nariz, ojos y pómulos (1.575 a 1.635)
        tm = (tv - 0.52) / 0.26
        z = 1.575 + tm * 0.060
        rx = 0.070 + tm * 0.005
        ry_f = 0.078
        ry_b = 0.068 + tm * 0.008
        yc = 0.0
    else: # Frente y cráneo (1.635 a 1.715)
        tt = (tv - 0.78) / 0.22
        z = 1.635 + tt * 0.080
        dome = math.sqrt(max(0.01, 1.0 - (tt * 0.94)**2))
        rx = 0.075 * dome + 0.003
        ry_f = 0.078 * dome + 0.003
        ry_b = 0.078 * dome + 0.003
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
            if abs(vz - 1.530) < 0.018 and abs(vx) < 0.026:
                cd = math.sqrt((vx / 0.026)**2 + ((vz - 1.530) / 0.018)**2)
                if cd < 1.0:
                    vy += 0.016 * (1.0 - cd)**2
            # Labios y comisura (Z ~ 1.556)
            if abs(vz - 1.556) < 0.012 and abs(vx) < 0.025:
                lw = (1.0 - abs(vx) / 0.025)
                if vz > 1.556:
                    vy += 0.011 * lw * math.sin(((vz - 1.556) / 0.010) * math.pi)
                else:
                    vy += 0.013 * lw * math.sin(((1.556 - vz) / 0.010) * math.pi)
            # Surco mentolabial
            if abs(vz - 1.542) < 0.007 and abs(vx) < 0.020:
                vy -= 0.004 * (1.0 - abs(vx) / 0.020)
            # Nariz 3D continua con puente y punta
            if 1.568 < vz < 1.622 and abs(vx) < 0.022:
                tn = (vz - 1.568) / 0.054
                nw = 0.010 + (1.0 - tn) * 0.011
                if abs(vx) < nw:
                    lf = 1.0 - (abs(vx) / nw)
                    n_proj = 0.027 * math.sin(tn * math.pi * 0.85) if tn < 0.42 else 0.016 + (1.0 - tn) * 0.010
                    vy += n_proj * (lf**1.4)
            # Cuencas orbitarias
            for ecx in [-0.032, 0.032]:
                de = math.sqrt(((vx - ecx) / 0.018)**2 + ((vz - 1.615) / 0.014)**2)
                if de < 1.0:
                    vy -= 0.010 * (1.0 - de)**2
            # Nuez de Adán
            if abs(vz - 1.485) < 0.012 and abs(vx) < 0.012:
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
        if abs(fc.z - 1.556) < 0.010 and abs(fc.x) < 0.020 and fc.y > 0.05:
            f.material_index = 5 # labios
        else:
            f.material_index = 0 # piel

top_vh = bm_head.verts.new(Vector((0.0, -0.008, 1.720)))
for ui in range(n_u):
    un = (ui + 1) % n_u
    f = bm_head.faces.new([h_grid[-1][ui], h_grid[-1][un], top_vh])
    f.material_index = 0

# Globos Oculares 3D (Z=1.615, X=+/-0.032)
for ex in [-0.032, 0.032]:
    p_eye = Vector((ex, 0.066, 1.615))
    sph = bmesh.ops.create_uvsphere(bm_head, u_segments=16, v_segments=12, radius=0.012, matrix=Matrix.Translation(p_eye))
    for v in sph['verts']:
        for f in v.link_faces:
            f.material_index = 3

    # Párpados
    etop = [
        Vector((ex - 0.014, 0.070, 1.613)),
        Vector((ex - 0.006, 0.076, 1.623)),
        Vector((ex + 0.006, 0.076, 1.623)),
        Vector((ex + 0.014, 0.070, 1.613)),
        Vector((ex + 0.016, 0.073, 1.619)),
        Vector((ex + 0.007, 0.079, 1.628)),
        Vector((ex - 0.007, 0.079, 1.628)),
        Vector((ex - 0.016, 0.073, 1.619)),
    ]
    ev = [bm_head.verts.new(p) for p in etop]
    f1 = bm_head.faces.new([ev[0], ev[1], ev[6], ev[7]])
    f2 = bm_head.faces.new([ev[1], ev[2], ev[5], ev[6]])
    f3 = bm_head.faces.new([ev[2], ev[3], ev[4], ev[5]])
    for ff in [f1, f2, f3]:
        ff.material_index = 0

    # Cejas 3D densas
    sb = -1.0 if ex < 0 else 1.0
    bpts = [
        Vector((ex - sb * 0.015, 0.073, 1.632)),
        Vector((ex - sb * 0.004, 0.078, 1.640)),
        Vector((ex + sb * 0.010, 0.077, 1.638)),
        Vector((ex + sb * 0.018, 0.072, 1.632)),
        Vector((ex + sb * 0.016, 0.073, 1.636)),
        Vector((ex + sb * 0.008, 0.080, 1.644)),
        Vector((ex - sb * 0.004, 0.081, 1.645)),
        Vector((ex - sb * 0.013, 0.075, 1.637)),
    ]
    bv = [bm_head.verts.new(p) for p in bpts]
    bf1 = bm_head.faces.new([bv[0], bv[1], bv[6], bv[7]])
    bf2 = bm_head.faces.new([bv[1], bv[2], bv[5], bv[6]])
    bf3 = bm_head.faces.new([bv[2], bv[3], bv[4], bv[5]])
    for bf in [bf1, bf2, bf3]:
        bf.material_index = 4

# Orejas
for ear_x, ear_sgn in [(-0.070, -1.0), (0.070, 1.0)]:
    p_ear = Vector((ear_x, 0.002, 1.605))
    sph_ear = bmesh.ops.create_uvsphere(bm_head, u_segments=10, v_segments=8, radius=0.014, matrix=Matrix.Translation(p_ear))
    for v in sph_ear['verts']:
        v.co.x = ear_x + (v.co.x - ear_x) * 0.38
        v.co.y = 0.002 + (v.co.y - 0.002) * 0.85
        v.co.z = 1.605 + (v.co.z - 1.605) * 1.25
        for f in v.link_faces:
            f.material_index = 0

# Mechones 3D de Cabello Rizado Ondulado (Axel Bangs)
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
    ([Vector((-0.038, 0.074, 1.662)), Vector((-0.030, 0.082, 1.648)), Vector((-0.020, 0.084, 1.632))], [0.011, 0.009, 0.003]),
    ([Vector((-0.020, 0.078, 1.666)), Vector((-0.012, 0.086, 1.650)), Vector((-0.004, 0.087, 1.630))], [0.012, 0.010, 0.003]),
    ([Vector((-0.002, 0.080, 1.666)), Vector(( 0.006, 0.087, 1.650)), Vector(( 0.014, 0.087, 1.630))], [0.012, 0.010, 0.003]),
    ([Vector(( 0.016, 0.079, 1.666)), Vector(( 0.022, 0.086, 1.650)), Vector(( 0.028, 0.086, 1.632))], [0.012, 0.010, 0.003]),
    ([Vector(( 0.030, 0.076, 1.662)), Vector(( 0.036, 0.082, 1.648)), Vector(( 0.040, 0.083, 1.634))], [0.011, 0.009, 0.003]),
    # Patillas
    ([Vector((-0.068, 0.022, 1.660)), Vector((-0.070, 0.020, 1.630)), Vector((-0.068, 0.016, 1.600))], [0.010, 0.008, 0.003]),
    ([Vector(( 0.068, 0.022, 1.660)), Vector(( 0.070, 0.020, 1.630)), Vector(( 0.068, 0.016, 1.600))], [0.010, 0.008, 0.003]),
    # Nuca
    ([Vector((-0.028, -0.066, 1.660)), Vector((-0.028, -0.062, 1.620)), Vector((-0.026, -0.058, 1.585))], [0.010, 0.008, 0.003]),
    ([Vector(( 0.000, -0.068, 1.660)), Vector(( 0.000, -0.064, 1.620)), Vector(( 0.000, -0.060, 1.583))], [0.011, 0.009, 0.003]),
    ([Vector(( 0.028, -0.066, 1.660)), Vector(( 0.028, -0.062, 1.620)), Vector(( 0.026, -0.058, 1.585))], [0.010, 0.008, 0.003]),
]
for pts, rads in hair_locks:
    add_hair_wave(bm_head, pts, rads)

# Beanie de Lana Verde Oliva Ajustado y Redondeado
beanie_levels = [
    (1.645, 1.615, 0.080, 0.084, 0.003),
    (1.662, 1.632, 0.085, 0.089, 0.004),
    (1.680, 1.650, 0.082, 0.086, 0.002),
    (1.702, 1.678, 0.078, 0.082, 0.000),
    (1.725, 1.705, 0.066, 0.070, 0.000),
    (1.742, 1.728, 0.048, 0.052, 0.000),
    (1.755, 1.745, 0.022, 0.024, 0.000),
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

top_beanie = bm_head.verts.new(Vector((0.0, -0.012, 1.760)))
for i in range(28):
    in_idx = (i + 1) % 28
    f = bm_head.faces.new([beanie_rings[-1][i], beanie_rings[-1][in_idx], top_beanie])
    f.material_index = 1

bm_head.to_mesh(head_mesh)
bm_head.free()

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

mod_sub_h = head_obj.modifiers.new(name="Subsurf", type='SUBSURF')
mod_sub_h.levels = 1
mod_sub_h.render_levels = 2

# =============================================================================
# 3. ILUMINACIÓN Y CÁMARA CALIBRADAS
# =============================================================================
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.device = 'CPU'
scene.render.resolution_x = 720
scene.render.resolution_y = 1280

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 54.0 # Lente más amplio para encuadre completo de manos y torso
cam = bpy.data.objects.new("Cam", cam_data)
# Encuadre frontal 3/4 suave que abarca torso, manos completas y rostro
cam.location = Vector((0.10, 2.30, 1.25))
cam.rotation_euler = (math.radians(88.0), 0.0, math.radians(178.0))
scene.collection.objects.link(cam)
scene.camera = cam

# Luces de estudio suaves calibradas
key_data = bpy.data.lights.new("Key", type='AREA')
key_data.energy = 120.0
key_data.size = 1.2
key_data.color = (1.0, 0.98, 0.96)
key = bpy.data.objects.new("Key", key_data)
key.location = Vector((-1.0, 1.8, 1.9))
scene.collection.objects.link(key)

fill_data = bpy.data.lights.new("Fill", type='AREA')
fill_data.energy = 50.0
fill_data.size = 1.5
fill_data.color = (0.92, 0.96, 1.0)
fill = bpy.data.objects.new("Fill", fill_data)
fill.location = Vector((1.2, 1.8, 1.4))
scene.collection.objects.link(fill)

rim_data = bpy.data.lights.new("Rim", type='SPOT')
rim_data.energy = 85.0
rim_data.spot_size = math.radians(70.0)
rim = bpy.data.objects.new("Rim", rim_data)
rim.location = Vector((0.0, -1.5, 2.0))
rim.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
scene.collection.objects.link(rim)

scene.render.filepath = os.path.abspath("scratch/test_axel_v5_render.png")
bpy.ops.render.render(write_still=True)
print("Rendered scratch/test_axel_v5_render.png")
