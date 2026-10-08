"""
=============================================================================
TEST ASTORGA FLAWLESS: ARQUITECTURA EN CAPAS DEFINITIVA
=============================================================================
"""

import os
import sys
import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

TEXTURES_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/textures")
SCRATCH_DIR = os.path.join(PROJECT_ROOT, "scratch")
VIOLIN_BLEND = os.path.join(PROJECT_ROOT, "godot_project/assets/props/violin.blend")

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm, do_unlink=True)

def create_material(name, base_color=(0.8, 0.8, 0.8, 1.0), roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = base_color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat

def create_materials():
    return {
        "suit": create_material("Mat_Astorga_Suit",
                                base_color=(0.045, 0.045, 0.050, 1.0), roughness=0.68, metallic=0.04),
        "pants": create_material("Mat_Astorga_Pants",
                                 base_color=(0.040, 0.040, 0.045, 1.0), roughness=0.72, metallic=0.02),
        "shoes": create_material("Mat_Astorga_Shoes",
                                 base_color=(0.012, 0.012, 0.014, 1.0), roughness=0.22, metallic=0.15),
        "skin": create_material("Mat_Astorga_Skin",
                                base_color=(0.48, 0.30, 0.22, 1.0), roughness=0.52, metallic=0.0),
        "shirt": create_material("Mat_Astorga_Shirt",
                                 base_color=(0.34, 0.065, 0.095, 1.0), roughness=0.50, metallic=0.02),
        "tie": create_material("Mat_Astorga_Tie",
                               base_color=(0.025, 0.025, 0.028, 1.0), roughness=0.35, metallic=0.10),
        "buttons": create_material("Mat_Astorga_Buttons",
                                   base_color=(0.02, 0.02, 0.02, 1.0), roughness=0.20, metallic=0.40),
        "hair": create_material("Mat_Astorga_Hair",
                                base_color=(0.035, 0.022, 0.015, 1.0), roughness=0.82, metallic=0.0),
        "eyes": create_material("Mat_Astorga_Eyes",
                                base_color=(0.18, 0.11, 0.06, 1.0), roughness=0.10, metallic=0.0),
    }

def build_head(materials):
    from scripts.characters.generate_astorga import build_head_mesh
    return build_head_mesh(materials)

def build_layered_body(materials):
    me = bpy.data.meshes.new("Player_Body_Mesh_Data")
    bm = bmesh.new()

    # -------------------------------------------------------------------------
    # 1. PIERNAS Y PANTALÓN (Estatura Astorga 1.65 m)
    # -------------------------------------------------------------------------
    leg_nodes = [
        # x, y, z, r
        (0.060, 0.002, 0.72, 0.046), # 0: Cadera baja
        (0.060, 0.002, 0.56, 0.043), # 1: Muslo medio
        (0.060, 0.000, 0.42, 0.038), # 2: Rodilla
        (0.060, 0.000, 0.26, 0.035), # 3: Pantorrilla
        (0.060, 0.002, 0.11, 0.032), # 4: Tobillo
    ]
    n_ring = 16
    for is_l in (True, False):
        sign = 1.0 if is_l else -1.0
        prev_ring = None
        for (lx, ly, lz, lr) in leg_nodes:
            cur_ring = []
            for i in range(n_ring):
                ang = (2.0 * math.pi * i) / n_ring
                vx = sign * lx + lr * math.cos(ang)
                vy = ly + lr * math.sin(ang)
                v = bm.verts.new((vx, vy, lz))
                cur_ring.append(v)
            if prev_ring:
                for i in range(n_ring):
                    inxt = (i + 1) % n_ring
                    f = bm.faces.new((prev_ring[i], prev_ring[inxt], cur_ring[inxt], cur_ring[i]))
                    f.material_index = 1 # Pantalón
            prev_ring = cur_ring

        # Zapatos de vestir pulidos
        v_ankle = prev_ring
        shoe_sole = []
        for i in range(n_ring):
            ang = (2.0 * math.pi * i) / n_ring
            ca = math.cos(ang)
            sa = math.sin(ang)
            sx = sign * 0.060 + 0.034 * ca
            sy = 0.024 + (0.070 if sa > 0 else 0.040) * sa
            sz = 0.012
            shoe_sole.append(bm.verts.new((sx, sy, sz)))
        for i in range(n_ring):
            inxt = (i + 1) % n_ring
            f = bm.faces.new((v_ankle[i], v_ankle[inxt], shoe_sole[inxt], shoe_sole[i]))
            f.material_index = 2 # Zapatos
        sole_cen = bm.verts.new((sign * 0.060, 0.024, 0.000))
        for i in range(n_ring):
            inxt = (i + 1) % n_ring
            f = bm.faces.new((shoe_sole[inxt], shoe_sole[i], sole_cen))
            f.material_index = 2

    # Pelvis del pantalón (Z = 0.72 a 0.86)
    pelvis_levels = [
        (0.72, 0.112, 0.072),
        (0.78, 0.114, 0.074),
        (0.85, 0.110, 0.070), # Cintura / Pretina
    ]
    pelvis_rings = []
    n_pelv = 24
    for (pz, prx, pry) in pelvis_levels:
        cur_ring = []
        for i in range(n_pelv):
            ang = (2.0 * math.pi * i) / n_pelv
            vx = prx * math.cos(ang)
            vy = pry * math.sin(ang)
            cur_ring.append(bm.verts.new((vx, vy, pz)))
        pelvis_rings.append(cur_ring)

    for l_idx in range(len(pelvis_levels) - 1):
        r1 = pelvis_rings[l_idx]
        r2 = pelvis_rings[l_idx + 1]
        for i in range(n_pelv):
            inxt = (i + 1) % n_pelv
            bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i])).material_index = 1

    crotch_cen = bm.verts.new((0.0, 0.002, 0.72))
    r_pelv_bot = pelvis_rings[0]
    for i in range(n_pelv):
        inxt = (i + 1) % n_pelv
        bm.faces.new((r_pelv_bot[inxt], r_pelv_bot[i], crotch_cen)).material_index = 1

    # Cinturón negro en Z = 0.85
    belt_ring = []
    for i in range(n_pelv):
        ang = (2.0 * math.pi * i) / n_pelv
        vx = 0.112 * math.cos(ang)
        vy = 0.072 * math.sin(ang)
        belt_ring.append(bm.verts.new((vx, vy, 0.865)))
    r_belt_bot = pelvis_rings[-1]
    for i in range(n_pelv):
        inxt = (i + 1) % n_pelv
        bm.faces.new((r_belt_bot[i], r_belt_bot[inxt], belt_ring[inxt], belt_ring[i])).material_index = 2

    # -------------------------------------------------------------------------
    # 2. CAMISA VINOTINTO MODELADA COMO PRENDA COMPLETA (Z = 0.85 a 1.36)
    # Superficie cilíndrica entallada continua.
    # -------------------------------------------------------------------------
    shirt_levels = [
        # z,     rx,    ry_front, ry_back, y_off
        (0.85,  0.112,  0.073,    0.071,   0.002), # Cintura
        (0.94,  0.114,  0.075,    0.073,   0.002), # Abdomen
        (1.02,  0.116,  0.077,    0.075,   0.000), # Ombligo
        (1.10,  0.122,  0.081,    0.081,  -0.002), # Tórax
        (1.18,  0.128,  0.087,    0.085,  -0.004), # Pectorales
        (1.26,  0.130,  0.087,    0.085,  -0.004), # Pecho alto
        (1.32,  0.114,  0.077,    0.077,  -0.002), # Clavícula
        (1.36,  0.046,  0.046,    0.046,   0.002), # Cuello
    ]
    shirt_rings = []
    n_shirt = 24
    for (sz, srx, sry_f, sry_b, sy_off) in shirt_levels:
        cur_ring = []
        for i in range(n_shirt):
            ang = (2.0 * math.pi * i) / n_shirt
            ca = math.cos(ang)
            sa = math.sin(ang)
            sx = srx * ca
            sy = (sry_f if sa >= 0 else sry_b) * sa + sy_off
            cur_ring.append(bm.verts.new((sx, sy, sz)))
        shirt_rings.append(cur_ring)

    for l_idx in range(len(shirt_levels) - 1):
        r1 = shirt_rings[l_idx]
        r2 = shirt_rings[l_idx + 1]
        for i in range(n_shirt):
            inxt = (i + 1) % n_shirt
            f = bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))
            f.material_index = 4 # Mat_Astorga_Shirt

    # Cuello camisero 3D
    n_c = 18
    c_bot, c_top = [], []
    for i in range(n_c):
        ang = (2.0 * math.pi * i) / n_c
        cx = 0.046 * math.cos(ang)
        cy = 0.046 * math.sin(ang) + 0.002
        c_bot.append(bm.verts.new((cx, cy, 1.345)))
        c_top.append(bm.verts.new((cx * 1.08, cy * 1.08, 1.385)))
    for i in range(n_c):
        inxt = (i + 1) % n_c
        bm.faces.new((c_bot[i], c_bot[inxt], c_top[inxt], c_top[i])).material_index = 4

    wing_l = [bm.verts.new((0.005, 0.054, 1.382)), bm.verts.new((0.038, 0.046, 1.375)), bm.verts.new((0.020, 0.068, 1.335))]
    wing_r = [bm.verts.new((-0.005, 0.054, 1.382)), bm.verts.new((-0.020, 0.068, 1.335)), bm.verts.new((-0.038, 0.046, 1.375))]
    bm.faces.new(wing_l).material_index = 4
    bm.faces.new(wing_r).material_index = 4

    # Tapeta central camisera con botones
    for bz in (0.90, 0.98, 1.06, 1.14, 1.22):
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=6, v_segments=4, radius=0.0030)
        bmesh.ops.scale(btn_bm, verts=btn_bm.verts, vec=(1.0, 0.4, 1.0))
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.0, 0.080, bz))
        v_map_b = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            bm.faces.new([v_map_b[v] for v in f.verts]).material_index = 4
        btn_bm.free()

    # Corbata negra con nudo Windsor cayendo verticalmente
    knot_v = [
        bm.verts.new((-0.013, 0.056, 1.375)),
        bm.verts.new(( 0.013, 0.056, 1.375)),
        bm.verts.new(( 0.010, 0.076, 1.335)),
        bm.verts.new((-0.010, 0.076, 1.335)),
        bm.verts.new(( 0.000, 0.084, 1.355)),
    ]
    for f_verts in [
        (knot_v[0], knot_v[1], knot_v[4]),
        (knot_v[1], knot_v[2], knot_v[4]),
        (knot_v[2], knot_v[3], knot_v[4]),
        (knot_v[3], knot_v[0], knot_v[4]),
    ]:
        bm.faces.new(f_verts).material_index = 5 # Corbata

    tie_profile = [
        (1.335,  0.010,  0.076),
        (1.265,  0.012,  0.088),
        (1.195,  0.013,  0.092),
        (1.125,  0.013,  0.090),
        (1.045,  0.011,  0.084),
        (0.965,  0.010,  0.080),
        (0.885,  0.008,  0.076),
    ]
    tie_rows = []
    for tz, thw, ty in tie_profile:
        vl = bm.verts.new((-thw, ty, tz))
        vm = bm.verts.new(( 0.000, ty + 0.003, tz))
        vr = bm.verts.new(( thw, ty, tz))
        tie_rows.append((vl, vm, vr))

    for idx in range(len(tie_rows) - 1):
        la, ma, ra = tie_rows[idx]
        lb, mb, rb = tie_rows[idx + 1]
        bm.faces.new((la, ma, mb, lb)).material_index = 5
        bm.faces.new((ma, ra, rb, mb)).material_index = 5

    # -------------------------------------------------------------------------
    # 3. SACO SASTRE SEPARADO CON APERTURA FÍSICA REAL EN V Y V INVERTIDA
    # Chaqueta externa abierta por delante en el centro.
    # -------------------------------------------------------------------------
    suit_specs = [
        # z,     rx,    ry_back, ry_front, y_off,  x_open (semiancho apertura central)
        (0.70,  0.126,  0.086,   0.086,    0.002,  0.082), # Faldón muy abierto mostrando pantalón
        (0.76,  0.124,  0.085,   0.085,    0.002,  0.065), # Cadera media abierta
        (0.84,  0.122,  0.084,   0.084,    0.002,  0.045), # Cintura baja
        (0.94,  0.120,  0.083,   0.083,    0.000,  0.024), # Bajo el botón
        (1.02,  0.122,  0.084,   0.084,    0.000,  0.010), # Botón central (mínima separación)
        (1.12,  0.130,  0.091,   0.090,   -0.002,  0.028), # Pecho medio (apertura en V superior)
        (1.22,  0.138,  0.095,   0.094,   -0.004,  0.052), # Pecho alto
        (1.30,  0.140,  0.092,   0.090,   -0.004,  0.066), # Hombros
    ]

    # Generamos la chaqueta como una superficie que va:
    # desde el borde delantero derecho (x = -x_open), da la vuelta por la derecha,
    # espalda, costado izquierdo, hasta el borde delantero izquierdo (x = +x_open).
    n_suit_pts = 21 # Puntos a lo largo del arco
    suit_levels_verts = []

    for (sz, srx, sry_b, sry_f, sy_off, x_op) in suit_specs:
        cur_row = []
        # El ángulo theta va desde el frente derecho (theta_start) dando la vuelta
        # por la espalda hasta el frente izquierdo (theta_end).
        # x = srx * sin(phi), y = sry * cos(phi)
        # En el frente, y > 0. phi = 0 es el frente centro (x=0, y>0).
        # Para x = -x_op: phi_start = -asin(x_op / srx)
        # Para x = +x_op: phi_end = +asin(x_op / srx)
        # Queremos el arco exterior que rodea la espalda: phi va de -asin por la izquierda (-pi) a +asin
        alpha = math.asin(min(0.95, x_op / srx))
        # Recorrido de phi: desde -alpha, pasando por -pi/2 (costado derecho, x < 0),
        # por -pi (espalda, y < 0), por -3pi/2 (costado izquierdo, x > 0), hasta -2pi + alpha (= +alpha)
        # Total angular: 2*pi - 2*alpha
        for i in range(n_suit_pts):
            t = i / float(n_suit_pts - 1)
            phi = -alpha - t * (2.0 * math.pi - 2.0 * alpha)
            vx = srx * math.sin(phi)
            ca = math.cos(phi)
            vy = (sry_f if ca >= 0 else sry_b) * ca + sy_off
            cur_row.append(bm.verts.new((vx, vy, sz)))
        suit_levels_verts.append(cur_row)

    # Conectar los quads del saco
    for l_idx in range(len(suit_specs) - 1):
        r1 = suit_levels_verts[l_idx]
        r2 = suit_levels_verts[l_idx + 1]
        for i in range(n_suit_pts - 1):
            f = bm.faces.new((r1[i], r1[i+1], r2[i+1], r2[i]))
            f.material_index = 0 # Saco

    # Dobladillo con grosor en los bordes frontales abiertos
    for l_idx in range(len(suit_specs) - 1):
        v1_r = suit_levels_verts[l_idx][0]
        v2_r = suit_levels_verts[l_idx + 1][0]
        v1_in = bm.verts.new((v1_r.co.x * 0.95, v1_r.co.y - 0.003, v1_r.co.z))
        v2_in = bm.verts.new((v2_r.co.x * 0.95, v2_r.co.y - 0.003, v2_r.co.z))
        bm.faces.new((v1_r, v2_r, v2_in, v1_in)).material_index = 0

        v1_l = suit_levels_verts[l_idx][-1]
        v2_l = suit_levels_verts[l_idx + 1][-1]
        v1_lin = bm.verts.new((v1_l.co.x * 0.95, v1_l.co.y - 0.003, v1_l.co.z))
        v2_lin = bm.verts.new((v2_l.co.x * 0.95, v2_l.co.y - 0.003, v2_l.co.z))
        bm.faces.new((v1_l, v1_lin, v2_lin, v2_l)).material_index = 0

    # Dobladillo inferior (Z = 0.70)
    r_bot = suit_levels_verts[0]
    for i in range(n_suit_pts - 1):
        v1 = r_bot[i]
        v2 = r_bot[i+1]
        v1_in = bm.verts.new((v1.co.x * 0.96, v1.co.y * 0.96, v1.co.z + 0.004))
        v2_in = bm.verts.new((v2.co.x * 0.96, v2.co.y * 0.96, v2.co.z + 0.004))
        bm.faces.new((v1, v2, v2_in, v1_in)).material_index = 0

    # Solapas notch clásicas en relieve sobre el pecho
    for s_side in (1.0, -1.0):
        lapel_v = [
            bm.verts.new((s_side * 0.040, 0.044, 1.355)),
            bm.verts.new((s_side * 0.084, 0.076, 1.305)),
            bm.verts.new((s_side * 0.088, 0.086, 1.265)),
            bm.verts.new((s_side * 0.074, 0.088, 1.250)),
            bm.verts.new((s_side * 0.084, 0.096, 1.230)),
            bm.verts.new((s_side * 0.016, 0.084, 1.020)),
            bm.verts.new((s_side * 0.034, 0.088, 1.210)),
        ]
        if s_side > 0:
            bm.faces.new((lapel_v[0], lapel_v[1], lapel_v[2], lapel_v[3])).material_index = 0
            bm.faces.new((lapel_v[0], lapel_v[3], lapel_v[6])).material_index = 0
            bm.faces.new((lapel_v[3], lapel_v[4], lapel_v[5], lapel_v[6])).material_index = 0
        else:
            bm.faces.new((lapel_v[1], lapel_v[0], lapel_v[3], lapel_v[2])).material_index = 0
            bm.faces.new((lapel_v[3], lapel_v[0], lapel_v[6])).material_index = 0
            bm.faces.new((lapel_v[4], lapel_v[3], lapel_v[6], lapel_v[5])).material_index = 0

    # Cuello de saco en nuca
    sc_top, sc_bot = [], []
    for i in range(10):
        ang = math.pi * 0.15 + (math.pi * 0.70 * i) / 9.0
        bx = 0.050 * math.cos(ang)
        by = -0.048 * math.sin(ang) - 0.003
        sc_top.append(bm.verts.new((bx, by, 1.375)))
        sc_bot.append(bm.verts.new((bx, by, 1.345)))
    for i in range(9):
        bm.faces.new((sc_bot[i], sc_bot[i+1], sc_top[i+1], sc_top[i])).material_index = 0

    # Botón sastre central en Z = 1.02
    btn_bm = bmesh.new()
    bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.0042)
    bmesh.ops.scale(btn_bm, verts=btn_bm.verts, vec=(1.0, 0.30, 1.0))
    bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.008, 0.086, 1.020))
    v_map_b = {v: bm.verts.new(v.co) for v in btn_bm.verts}
    for f in btn_bm.faces:
        bm.faces.new([v_map_b[v] for v in f.verts]).material_index = 6
    btn_bm.free()

    # -------------------------------------------------------------------------
    # 4. BRAZOS, MANGAS Y MANOS CON PRENSIÓN EXACTA
    # -------------------------------------------------------------------------
    for is_l in (True, False):
        sign = 1.0 if is_l else -1.0

        arm_sections = [
            # center_x, center_y, z, radius
            (sign * 0.170, -0.003, 1.295, 0.046), # Hombro sastre
            (sign * 0.190, -0.002, 1.245, 0.041), # Deltoides
            (sign * 0.215,  0.000, 1.185, 0.037), # Bíceps
            (sign * 0.245,  0.002, 1.115, 0.034), # Codo
            (sign * 0.265,  0.005, 1.015, 0.029), # Antebrazo
            (sign * 0.278,  0.007, 0.935, 0.025), # Antebrazo bajo
            (sign * 0.282,  0.008, 0.880, 0.023), # Puño manga
        ]
        arm_rings = []
        n_arm = 16
        for (ax, ay, az, ar) in arm_sections:
            cur_ring = []
            for i in range(n_arm):
                ang = (2.0 * math.pi * i) / n_arm
                vx = ax + ar * math.cos(ang)
                vy = ay + ar * math.sin(ang)
                cur_ring.append(bm.verts.new((vx, vy, az)))
            arm_rings.append(cur_ring)

        # Cúpula suave superior del hombro
        sh_apex = bm.verts.new((sign * 0.170, -0.003, 1.320))
        r_sh_top = arm_rings[0]
        for i in range(n_arm):
            inxt = (i + 1) % n_arm
            if sign > 0:
                bm.faces.new((r_sh_top[i], r_sh_top[inxt], sh_apex)).material_index = 0
            else:
                bm.faces.new((r_sh_top[inxt], r_sh_top[i], sh_apex)).material_index = 0

        for l_idx in range(len(arm_sections) - 1):
            r1 = arm_rings[l_idx]
            r2 = arm_rings[l_idx + 1]
            for i in range(n_arm):
                inxt = (i + 1) % n_arm
                if sign > 0:
                    bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i])).material_index = 0
                else:
                    bm.faces.new((r1[inxt], r1[i], r2[i], r2[inxt])).material_index = 0

        # Puño de camisa vinotinto asomando
        cuff_ring = []
        for i in range(n_arm):
            ang = (2.0 * math.pi * i) / n_arm
            vx = sign * 0.282 + 0.019 * math.cos(ang)
            vy = 0.008 + 0.015 * math.sin(ang)
            cuff_ring.append(bm.verts.new((vx, vy, 0.865)))
        r_cuff_top = arm_rings[-1]
        for i in range(n_arm):
            inxt = (i + 1) % n_arm
            if sign > 0:
                bm.faces.new((r_cuff_top[i], r_cuff_top[inxt], cuff_ring[inxt], cuff_ring[i])).material_index = 4
            else:
                bm.faces.new((r_cuff_top[inxt], r_cuff_top[i], cuff_ring[i], cuff_ring[inxt])).material_index = 4

        # Muñeca de piel
        wrist_ring = []
        for i in range(n_arm):
            ang = (2.0 * math.pi * i) / n_arm
            vx = sign * 0.282 + 0.016 * math.cos(ang)
            vy = 0.008 + 0.012 * math.sin(ang)
            wrist_ring.append(bm.verts.new((vx, vy, 0.842)))
        for i in range(n_arm):
            inxt = (i + 1) % n_arm
            if sign > 0:
                bm.faces.new((cuff_ring[i], cuff_ring[inxt], wrist_ring[inxt], wrist_ring[i])).material_index = 3
            else:
                bm.faces.new((cuff_ring[inxt], cuff_ring[i], wrist_ring[i], wrist_ring[inxt])).material_index = 3

        # Palma y dedos anatómicos
        w_center = Vector((sign * 0.282, 0.008, 0.818))
        z_knuckles = 0.814

        finger_specs = [
            ("Index",   w_center.y + 0.012, 0.046, 0.0048),
            ("Middle",  w_center.y + 0.003, 0.050, 0.0050),
            ("Ring",    w_center.y - 0.005, 0.045, 0.0048),
            ("Pinky",   w_center.y - 0.013, 0.036, 0.0042),
        ]

        if is_l:
            curl_dir = Vector((-0.35, 0.84, -0.28)).normalized()
        else:
            # Mano derecha abrazando el mástil del violín por el frente
            curl_dir = Vector(( 0.40, 0.68, -0.42)).normalized()

        for fname, fy, f_len, f_rad in finger_specs:
            fx = sign * 0.282 + (sign * 0.012 if fname == "Index" else 0.0)
            n_seg = 4
            prev_fring = None
            for s in range(n_seg + 1):
                t = s / float(n_seg)
                if is_l:
                    fz = z_knuckles - f_len * (t**0.85) * 0.65
                    cur_y = fy + curl_dir.y * (f_len * 0.82 * (t**1.15))
                    cur_x = fx + curl_dir.x * (f_len * 0.50 * (t**1.15))
                else:
                    fz = z_knuckles - f_len * (t**0.88) * 0.55
                    cur_y = fy + curl_dir.y * (f_len * 0.90 * (t**1.10))
                    cur_x = fx + curl_dir.x * (f_len * 0.55 * (t**1.10))
                r_cur = f_rad * (1.0 - 0.25 * t)

                cur_fring = []
                for k in range(6):
                    fang = (2.0 * math.pi * k) / 6.0
                    cur_fring.append(bm.verts.new((cur_x + r_cur * math.cos(fang),
                                                  cur_y + r_cur * math.sin(fang),
                                                  fz + curl_dir.z * (f_len * 0.30 * t))))
                if prev_fring:
                    for k in range(6):
                        knxt = (k + 1) % 6
                        bm.faces.new((prev_fring[k], prev_fring[knxt], cur_fring[knxt], cur_fring[k])).material_index = 3
                prev_fring = cur_fring

            tip_v = bm.verts.new((cur_x + curl_dir.x * 0.004, cur_y + curl_dir.y * 0.004, fz - 0.004))
            for k in range(6):
                knxt = (k + 1) % 6
                bm.faces.new((prev_fring[knxt], prev_fring[k], tip_v)).material_index = 3

        # Pulgar opuesto
        th_root = Vector((sign * (0.282 - 0.014), w_center.y + 0.008, 0.820))
        prev_th = None
        th_curl = Vector((-sign * 0.45, 0.68, -0.32)).normalized()
        for s in range(4):
            t = s / 3.0
            tx = th_root.x + th_curl.x * 0.024 * t
            ty = th_root.y + th_curl.y * 0.024 * t
            tz = th_root.z - 0.018 * t
            trad = 0.0054 * (1.0 - 0.22 * t)
            cur_th = []
            for k in range(6):
                tang = (2.0 * math.pi * k) / 6.0
                cur_th.append(bm.verts.new((tx + trad * math.cos(tang),
                                           ty + trad * math.sin(tang),
                                           tz)))
            if prev_th:
                for k in range(6):
                    knxt = (k + 1) % 6
                    bm.faces.new((prev_th[k], prev_th[knxt], cur_th[knxt], cur_th[k])).material_index = 3
            prev_th = cur_th

        tip_th = bm.verts.new((tx + th_curl.x * 0.003, ty + th_curl.y * 0.003, tz - 0.003))
        for k in range(6):
            knxt = (k + 1) % 6
            bm.faces.new((prev_th[knxt], prev_th[k], tip_th)).material_index = 3

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    for f in bm.faces: f.smooth = True

    bm.to_mesh(me)
    bm.free()

    for mat in [materials["suit"], materials["pants"], materials["shoes"],
                materials["skin"], materials["shirt"], materials["tie"], materials["buttons"]]:
        me.materials.append(mat)

    obj_body = bpy.data.objects.new("Player_Body_Mesh", me)
    bpy.context.scene.collection.objects.link(obj_body)
    return obj_body

def build_skeleton():
    arm_data = bpy.data.armatures.new("Skeleton3D")
    arm_obj = bpy.data.objects.new("Skeleton3D", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = arm_data.edit_bones

    bones_def = [
        ("Root",        None,          (0, 0, 0),         (0, 0, 0.10)),
        ("Hips",        "Root",        (0, 0, 0.72),      (0, 0, 0.86)),
        ("Spine",       "Hips",        (0, 0, 0.86),      (0, 0, 1.08)),
        ("Chest",       "Spine",       (0, 0, 1.08),      (0, 0, 1.30)),
        ("Neck",        "Chest",       (0, 0, 1.30),      (0, 0, 1.37)),
        ("Head",        "Neck",        (0, 0, 1.37),      (0, 0, 1.63)),

        ("Shoulder.L",  "Chest",       (0.04, 0, 1.30),   (0.170, 0, 1.29)),
        ("UpperArm.L",  "Shoulder.L",  (0.170, 0, 1.29),  (0.245, 0.002, 1.115)),
        ("Forearm.L",   "UpperArm.L",  (0.245, 0.002, 1.115),(0.278, 0.007, 0.935)),
        ("Hand.L",      "Forearm.L",   (0.278, 0.007, 0.935),(0.282, 0.008, 0.76)),

        ("Shoulder.R",  "Chest",       (-0.04, 0, 1.30),  (-0.170, 0, 1.29)),
        ("UpperArm.R",  "Shoulder.R",  (-0.170, 0, 1.29), (-0.245, 0.002, 1.115)),
        ("Forearm.R",   "UpperArm.R",  (-0.245, 0.002, 1.115),(-0.278, 0.007, 0.935)),
        ("Hand.R",      "Forearm.R",   (-0.278, 0.007, 0.935),(-0.282, 0.008, 0.76)),

        ("UpperLeg.L",  "Hips",        (0.060, 0, 0.72),  (0.060, 0, 0.42)),
        ("LowerLeg.L",  "UpperLeg.L",  (0.060, 0, 0.42),  (0.060, 0, 0.11)),
        ("Foot.L",      "LowerLeg.L",  (0.060, 0, 0.11),  (0.060, 0.045, 0.03)),
        ("Toes.L",      "Foot.L",      (0.060, 0.045, 0.03),(0.060, 0.090, 0.00)),

        ("UpperLeg.R",  "Hips",        (-0.060, 0, 0.72), (-0.060, 0, 0.42)),
        ("LowerLeg.R",  "UpperLeg.R",  (-0.060, 0, 0.42), (-0.060, 0, 0.11)),
        ("Foot.R",      "LowerLeg.R",  (-0.060, 0, 0.11), (-0.060, 0.045, 0.03)),
        ("Toes.R",      "Foot.R",      (-0.060, 0.045, 0.03),(-0.060, 0.090, 0.00)),
    ]
    created = {}
    for name, parent, head, tail in bones_def:
        b = edit_bones.new(name)
        b.head = head
        b.tail = tail
        created[name] = b
    for name, parent, head, tail in bones_def:
        if parent: created[name].parent = created[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

def assign_weights(obj, is_head=False):
    bone_names = [
        "Root", "Hips", "Spine", "Chest", "Neck", "Head",
        "Shoulder.L", "UpperArm.L", "Forearm.L", "Hand.L",
        "Shoulder.R", "UpperArm.R", "Forearm.R", "Hand.R",
        "UpperLeg.L", "LowerLeg.L", "Foot.L", "Toes.L",
        "UpperLeg.R", "LowerLeg.R", "Foot.R", "Toes.R"
    ]
    for b in bone_names:
        if b not in obj.vertex_groups: obj.vertex_groups.new(name=b)

    for v in obj.data.vertices:
        co = v.co
        if is_head:
            if co.z < 1.37:
                obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 1.41:
                t = (co.z - 1.37) / 0.04
                obj.vertex_groups["Neck"].add([v.index], 1.0 - t, 'REPLACE')
                obj.vertex_groups["Head"].add([v.index], t, 'REPLACE')
            else:
                obj.vertex_groups["Head"].add([v.index], 1.0, 'REPLACE')
        else:
            ax = abs(co.x)
            side = ".L" if co.x > 0 else ".R"

            # 1. BRAZOS Y MANGAS (ax >= 0.14)
            if ax >= 0.14 and co.z >= 0.70 and co.z <= 1.35:
                sh_cen = Vector((math.copysign(0.170, co.x), 0.0, 1.29))
                dist_sh = (Vector((co.x, co.y, co.z)) - sh_cen).length

                if co.z < 0.88:
                    obj.vertex_groups["Hand" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.94:
                    t = (co.z - 0.88) / 0.06
                    obj.vertex_groups["Hand" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Forearm" + side].add([v.index], t, 'REPLACE')
                elif co.z < 1.08:
                    obj.vertex_groups["Forearm" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.16:
                    t = (co.z - 1.08) / 0.08
                    obj.vertex_groups["Forearm" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["UpperArm" + side].add([v.index], t, 'REPLACE')
                elif co.z < 1.24:
                    obj.vertex_groups["UpperArm" + side].add([v.index], 1.0, 'REPLACE')
                else:
                    # Deltoides / hombrera: gradiente suave que previene estrangulamiento
                    if dist_sh > 0.055:
                        t = min(1.0, (dist_sh - 0.055) / 0.035)
                        obj.vertex_groups["UpperArm" + side].add([v.index], 0.75 + 0.25 * t, 'REPLACE')
                        obj.vertex_groups["Shoulder" + side].add([v.index], 0.25 * (1.0 - t), 'REPLACE')
                    else:
                        t = dist_sh / 0.055
                        w_sh = 0.50 + 0.30 * t
                        w_up = 0.40 * t
                        w_ch = max(0.0, 1.0 - (w_sh + w_up))
                        obj.vertex_groups["Shoulder" + side].add([v.index], w_sh, 'REPLACE')
                        obj.vertex_groups["UpperArm" + side].add([v.index], w_up, 'REPLACE')
                        if w_ch > 0:
                            obj.vertex_groups["Chest"].add([v.index], w_ch, 'REPLACE')

            # 2. HOMBRO INTERIOR (ax entre 0.08 y 0.14)
            elif ax >= 0.08 and co.z >= 1.22:
                t = (ax - 0.08) / 0.06
                obj.vertex_groups["Chest"].add([v.index], 1.0 - 0.75 * t, 'REPLACE')
                obj.vertex_groups["Shoulder" + side].add([v.index], 0.75 * t, 'REPLACE')

            # 3. PIERNAS
            elif co.z < 0.72:
                if co.z < 0.035 and co.y > 0.04:
                    obj.vertex_groups["Toes" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.10:
                    obj.vertex_groups["Foot" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.14:
                    t = (co.z - 0.10) / 0.04
                    obj.vertex_groups["Foot" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["LowerLeg" + side].add([v.index], t, 'REPLACE')
                elif co.z < 0.38:
                    obj.vertex_groups["LowerLeg" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.46:
                    t = (co.z - 0.38) / 0.08
                    obj.vertex_groups["LowerLeg" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["UpperLeg" + side].add([v.index], t, 'REPLACE')
                else:
                    obj.vertex_groups["UpperLeg" + side].add([v.index], 1.0, 'REPLACE')

            # 4. TORSO Y SACO
            else:
                if co.z < 0.86:
                    obj.vertex_groups["Hips"].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.08:
                    t = (co.z - 0.86) / 0.22
                    obj.vertex_groups["Hips"].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Spine"].add([v.index], t, 'REPLACE')
                elif co.z < 1.26:
                    t = (co.z - 1.08) / 0.18
                    obj.vertex_groups["Spine"].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Chest"].add([v.index], t, 'REPLACE')
                elif co.z < 1.34:
                    t = (co.z - 1.26) / 0.08
                    obj.vertex_groups["Chest"].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Neck"].add([v.index], t, 'REPLACE')
                else:
                    obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')

def attach_armature(obj, arm_obj):
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj
    mod.use_vertex_groups = True
    obj.parent = arm_obj

def apply_violin_pose_and_props(arm_obj):
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')

    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)

    # Pose de Astorga:
    arm_obj.pose.bones['Chest'].rotation_euler = (math.radians(-2), math.radians(-3), math.radians(2))
    arm_obj.pose.bones['Head'].rotation_euler = (math.radians(-1), math.radians(4), math.radians(1))

    # Brazo derecho (Hand.R, -X, Viewer's Right): Sostiene el VIOLÍN en alto
    # Rotación anatómica natural para elevar la mano frente al pecho/hombro
    arm_obj.pose.bones['Shoulder.R'].rotation_euler = (math.radians(4), math.radians(2), math.radians(-3))
    arm_obj.pose.bones['UpperArm.R'].rotation_euler = (math.radians(28), math.radians(12), math.radians(-22))
    arm_obj.pose.bones['Forearm.R'].rotation_euler = (math.radians(102), math.radians(18), math.radians(-6))
    arm_obj.pose.bones['Hand.R'].rotation_euler = (math.radians(20), math.radians(-12), math.radians(38))

    # Brazo izquierdo (Hand.L, +X, Viewer's Left): Sostiene el ARCO
    arm_obj.pose.bones['Shoulder.L'].rotation_euler = (math.radians(2), math.radians(-1), math.radians(2))
    arm_obj.pose.bones['UpperArm.L'].rotation_euler = (math.radians(16), math.radians(-3), math.radians(6))
    arm_obj.pose.bones['Forearm.L'].rotation_euler = (math.radians(48), math.radians(-6), math.radians(6))
    arm_obj.pose.bones['Hand.L'].rotation_euler = (math.radians(18), math.radians(8), math.radians(-6))

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()

    hand_l_mat = arm_obj.matrix_world @ arm_obj.pose.bones['Hand.L'].matrix
    hand_r_mat = arm_obj.matrix_world @ arm_obj.pose.bones['Hand.R'].matrix
    hand_l_loc = hand_l_mat.to_translation()
    hand_r_loc = hand_r_mat.to_translation()

    scene = bpy.context.scene
    if os.path.exists(VIOLIN_BLEND):
        with bpy.data.libraries.load(VIOLIN_BLEND, link=False) as (data_from, data_to):
            data_to.objects = [o for o in data_from.objects if o in ("Violin_Prop", "Violin_Bow")]
        for o in data_to.objects:
            if o:
                scene.collection.objects.link(o)
                for p in o.data.polygons:
                    p.use_smooth = True
                if o.name == "Violin_Prop":
                    o.scale = (0.76, 0.76, 0.76)
                    # El violín se coloca de modo que el mástil pase a través de la mano derecha
                    o.rotation_euler = Euler((math.radians(-74), math.radians(168), math.radians(14)), 'XYZ')
                    # Offset calibrado para que el mástil (Z aprox a 32 cm de base) esté entre pulgar y dedos
                    o.location = Vector((hand_r_loc.x + 0.016, hand_r_loc.y - 0.024, hand_r_loc.z - 0.235))
                elif o.name == "Violin_Bow":
                    o.scale = (0.70, 0.70, 0.70)
                    o.rotation_euler = Euler((math.radians(24), math.radians(-4), math.radians(-16)), 'XYZ')
                    o.location = Vector((hand_l_loc.x - 0.002, hand_l_loc.y + 0.008, hand_l_loc.z - 0.020))

def render_views(arm_obj):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 24
    scene.view_settings.view_transform = 'Standard'

    def add_light(name, ltype, energy, loc, color=(1,1,1), size=1.0):
        ld = bpy.data.lights.new(name, ltype)
        ld.energy = energy
        ld.color = color
        if hasattr(ld, 'size'): ld.size = size
        lo = bpy.data.objects.new(name, ld)
        lo.location = Vector(loc)
        scene.collection.objects.link(lo)
        return lo

    add_light("KeyLight",   'AREA', 180.0, (-0.8, 1.8, 1.6), (1.0, 0.96, 0.92), size=1.8)
    add_light("FillLight",  'AREA', 100.0, ( 1.0, 1.6, 1.4), (0.94, 0.96, 1.0), size=2.2)
    add_light("RimLight",   'SPOT', 140.0, ( 0.1,-1.5, 1.9), (1.0, 0.98, 0.94))
    add_light("ViolinLight",'AREA',  75.0, (-0.4, 1.7, 1.28), (1.0, 0.95, 0.88), size=1.0)
    add_light("BodyFill",   'AREA',  60.0, ( 0.0, 2.0, 0.90), (0.98, 0.98, 1.0), size=2.0)

    cam_data = bpy.data.cameras.new("RenderCam")
    cam_obj = bpy.data.objects.new("RenderCam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # 1. Retrato
    cam_data.lens = 72.0
    cam_obj.location = Vector((0.0, 2.15, 1.24))
    target = Vector((0.0, 0.0, 1.21))
    cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024

    out_portrait = os.path.join(SCRATCH_DIR, "test_astorga_flawless_portrait.png")
    scene.render.filepath = out_portrait
    bpy.ops.render.render(write_still=True)
    print("✓ Retrato guardado en:", out_portrait)

    # 2. Cuerpo Completo
    cam_data.lens = 52.0
    cam_obj.location = Vector((0.0, 2.50, 0.94))
    target_fb = Vector((0.0, 0.0, 0.86))
    cam_obj.rotation_euler = (target_fb - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1200

    out_fb = os.path.join(SCRATCH_DIR, "test_astorga_flawless_fullbody.png")
    scene.render.filepath = out_fb
    bpy.ops.render.render(write_still=True)
    print("✓ Cuerpo completo guardado en:", out_fb)

def main():
    clean_scene()
    mats = create_materials()
    mat_groups_head = {"head": [mats["skin"], mats["eyes"], mats["hair"]]}

    arm_obj = build_skeleton()
    obj_head = build_head(mat_groups_head)
    assign_weights(obj_head, is_head=True)
    attach_armature(obj_head, arm_obj)

    obj_body = build_layered_body(mats)
    assign_weights(obj_body, is_head=False)
    attach_armature(obj_body, arm_obj)

    apply_violin_pose_and_props(arm_obj)
    render_views(arm_obj)
    print("✓ Proceso completado exitosamente.")

if __name__ == "__main__":
    main()
