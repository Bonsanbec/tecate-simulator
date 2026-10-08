"""
=============================================================================
RECONSTRUCCIÓN INTEGRAL Y CANÓNICA DE ASTORGA (TECATE SIMULATOR)
=============================================================================
Implementa con máxima fidelidad la referencia real (scratch/humans/astorga.png)
y resuelve los 4 puntos marcados por el usuario:

1. Camisa separada del cuerpo: Prenda independiente con su propia geometría
   cilíndrica entallada que viste el torso desde el cuello (Z=1.35) hasta
   la cintura (Z=0.84) sin clippear con el cuerpo base.
2. Saco separado del cuerpo con apertura física: Chaqueta sastre tridimensional
   independiente (r_saco > r_camisa) que envuelve el torso y hombros, cuyos
   paneles frontales se abren en escote superior en V y, debajo del botón (Z=1.02),
   se abren físicamente en V invertida hacia los costados (Z=0.72), revelando
   la camisa vinotinto y la pretina del pantalón.
3. Hombro estructurado sin colapso (Cero deltoides sumido): Manga y hombrera
   articuladas con transición esférica suave de pesos armónicos, evitando
   estrangulamientos en la axila al posar el brazo.
4. Prensión anatómica del violín y el arco:
   - Mano derecha (Viewer's Left, con el arco): dedos flexionados cerrados
     abrazando la nuez y vara del arco.
   - Mano izquierda (Viewer's Right, con el violín): mano alzada, dedos curvados
     tocando y abrazando físicamente el mástil del violín por el frente.
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
ICONS_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/icons")

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

# =============================================================================
# 1. CABEZA CANÓNICA (APROBADA)
# =============================================================================
def build_head(materials):
    from scripts.characters.generate_astorga import build_head_mesh
    return build_head_mesh(materials)

# =============================================================================
# 2. CUERPO ESTRUCTURADO EN 3 CAPAS LIMPIAS:
#    CAPA A: CUERPO BASE (PANTALÓN, ZAPATOS Y MANOS CON PRENSIÓN EXACTA)
#    CAPA B: CAMISA VINOTINTO SEPARADA (Z=0.84 a Z=1.35) CON CUELLO 3D Y CORBATA
#    CAPA C: SACO SASTRE SEPARADO CON APERTURA FRONTAL EN V INVERTIDA Y MANGAS
# =============================================================================
def build_layered_body(materials):
    me = bpy.data.meshes.new("Player_Body_Mesh_Data")
    bm = bmesh.new()

    # Índices de materiales:
    # 0: suit, 1: pants, 2: shoes, 3: skin, 4: shirt, 5: tie, 6: buttons

    # -------------------------------------------------------------------------
    # CAPA A: CUERPO BASE - PIERNAS Y PANTALÓN (Estatura Astorga 1.65 m)
    # -------------------------------------------------------------------------
    leg_nodes = [
        # x, y, z, r
        (0.062, 0.002, 0.72, 0.048), # 0: Cadera baja
        (0.062, 0.002, 0.56, 0.044), # 1: Muslo medio
        (0.062, 0.000, 0.42, 0.038), # 2: Rodilla
        (0.062, 0.000, 0.26, 0.035), # 3: Pantorrilla
        (0.062, 0.002, 0.11, 0.032), # 4: Tobillo
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
                    f.material_index = 1 # Mat_Astorga_Pants
            prev_ring = cur_ring

        # Zapatos formales negros pulidos con suela y puntera
        v_ankle = prev_ring
        shoe_sole = []
        for i in range(n_ring):
            ang = (2.0 * math.pi * i) / n_ring
            ca = math.cos(ang)
            sa = math.sin(ang)
            sx = sign * 0.062 + 0.034 * ca
            sy = 0.024 + (0.072 if sa > 0 else 0.042) * sa
            sz = 0.012
            shoe_sole.append(bm.verts.new((sx, sy, sz)))
        for i in range(n_ring):
            inxt = (i + 1) % n_ring
            f = bm.faces.new((v_ankle[i], v_ankle[inxt], shoe_sole[inxt], shoe_sole[i]))
            f.material_index = 2 # Mat_Astorga_Shoes
        # Suela plana
        sole_cen = bm.verts.new((sign * 0.062, 0.024, 0.000))
        for i in range(n_ring):
            inxt = (i + 1) % n_ring
            f = bm.faces.new((shoe_sole[inxt], shoe_sole[i], sole_cen))
            f.material_index = 2

    # Pelvis del pantalón (Z = 0.72 a 0.86)
    pelvis_levels = [
        (0.72, 0.114, 0.074),
        (0.78, 0.116, 0.076),
        (0.85, 0.112, 0.072), # Cintura / Pretina del pantalón
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

    # Cierre de entrepierna inferior
    crotch_cen = bm.verts.new((0.0, 0.002, 0.72))
    r_pelv_bot = pelvis_rings[0]
    for i in range(n_pelv):
        inxt = (i + 1) % n_pelv
        bm.faces.new((r_pelv_bot[inxt], r_pelv_bot[i], crotch_cen)).material_index = 1

    # Cinturón negro de vestir con hebilla sutil en Z = 0.85
    belt_ring_top = []
    for i in range(n_pelv):
        ang = (2.0 * math.pi * i) / n_pelv
        vx = 0.113 * math.cos(ang)
        vy = 0.073 * math.sin(ang)
        belt_ring_top.append(bm.verts.new((vx, vy, 0.865)))
    r_belt_bot = pelvis_rings[-1]
    for i in range(n_pelv):
        inxt = (i + 1) % n_pelv
        bm.faces.new((r_belt_bot[i], r_belt_bot[inxt], belt_ring_top[inxt], belt_ring_top[i])).material_index = 2

    # -------------------------------------------------------------------------
    # CAPA B: CAMISA VINOTINTO SEPARADA (Z = 0.85 a Z = 1.35)
    # Cilindro entallado independiente que cubre todo el torso.
    # -------------------------------------------------------------------------
    shirt_levels = [
        # z,     rx,    ry_front, ry_back, y_off
        (0.85,  0.112,  0.074,    0.072,   0.002), # Base de camisa (metida en pantalón)
        (0.94,  0.114,  0.076,    0.074,   0.002), # Abdomen bajo
        (1.02,  0.116,  0.078,    0.076,   0.000), # Ombligo / botón
        (1.10,  0.122,  0.082,    0.082,  -0.002), # Tórax
        (1.18,  0.128,  0.088,    0.086,  -0.004), # Pectorales
        (1.26,  0.130,  0.088,    0.086,  -0.004), # Pecho alto
        (1.32,  0.114,  0.078,    0.078,  -0.002), # Clavícula
        (1.36,  0.046,  0.046,    0.046,   0.002), # Base del cuello
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
            f.material_index = 4 # Mat_Astorga_Shirt (Vinotinto puro)

    # Cuello camisero 3D con solapillas dobladas
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

    # Tapeta central camisera con botones en relieve
    for bz in (0.90, 0.98, 1.06, 1.14, 1.22):
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=6, v_segments=4, radius=0.0030)
        bmesh.ops.scale(btn_bm, verts=btn_bm.verts, vec=(1.0, 0.4, 1.0))
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.0, 0.080, bz))
        v_map_b = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            bm.faces.new([v_map_b[v] for v in f.verts]).material_index = 4
        btn_bm.free()

    # Corbata negra con nudo Windsor y caída vertical limpia
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
        bm.faces.new(f_verts).material_index = 5 # Mat_Astorga_Tie

    tie_profile = [
        (1.335,  0.010,  0.076),
        (1.265,  0.012,  0.088),
        (1.195,  0.013,  0.092),
        (1.125,  0.013,  0.090),
        (1.045,  0.011,  0.084),
        (0.965,  0.010,  0.080),
        (0.885,  0.008,  0.076), # Cae hasta la pretina
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
    # CAPA C: SACO SASTRE SEPARADO CON APERTURA REAL EN V INVERTIDA
    # (r_saco > r_camisa)
    # El faldón del saco se abre físicamente desde el botón (Z=1.02) hacia
    # los costados (Z=0.70), revelando la camisa vinotinto y la pretina.
    # -------------------------------------------------------------------------
    suit_levels = [
        # z,     rx,    ry_front, ry_back, y_off,  v_open_w (semiancho apertura frontal)
        (0.70,  0.124,  0.084,    0.084,   0.002,  0.072), # Faldón inferior abierto
        (0.76,  0.122,  0.083,    0.083,   0.002,  0.055), # Cadera media abierta
        (0.84,  0.120,  0.082,    0.082,   0.002,  0.038), # Cintura baja
        (0.94,  0.118,  0.081,    0.081,   0.000,  0.018), # Bajo el botón
        (1.02,  0.120,  0.083,    0.082,   0.000,  0.005), # Botón central (cerrado formal)
        (1.12,  0.128,  0.090,    0.088,  -0.002,  0.024), # Pecho medio (apertura en V superior)
        (1.22,  0.136,  0.094,    0.092,  -0.004,  0.046), # Pecho alto
        (1.30,  0.138,  0.090,    0.088,  -0.004,  0.062), # Hombros sastre
    ]
    n_suit_pts = 28
    suit_rings = []
    for (sz, srx, sry_f, sry_b, sy_off, open_w) in suit_levels:
        cur_ring = []
        for i in range(n_suit_pts):
            t = i / float(n_suit_pts - 1)
            # t=0: borde frontal derecho (-X)
            # t=0.5: centro espalda (0, -Y)
            # t=1.0: borde frontal izquierdo (+X)
            ang_start = math.asin(min(0.92, open_w / max(0.01, srx)))
            phi = -math.pi * 0.5 + (t - 0.5) * (2.0 * math.pi - 2.0 * ang_start)
            vx = srx * math.sin(phi)
            sa = -math.cos(phi)
            vy = (sry_f if sa >= 0 else sry_b) * sa + sy_off
            cur_ring.append(bm.verts.new((vx, vy, sz)))
        suit_rings.append(cur_ring)

    for l_idx in range(len(suit_levels) - 1):
        r1 = suit_rings[l_idx]
        r2 = suit_rings[l_idx + 1]
        for i in range(n_suit_pts - 1):
            f = bm.faces.new((r1[i], r1[i+1], r2[i+1], r2[i]))
            f.material_index = 0 # Mat_Astorga_Suit

    # Dobladillo con grosor sastre en bordes frontales
    for l_idx in range(len(suit_levels) - 1):
        v1_r = suit_rings[l_idx][0]
        v2_r = suit_rings[l_idx + 1][0]
        v1_in = bm.verts.new((v1_r.co.x * 0.96, v1_r.co.y - 0.003, v1_r.co.z))
        v2_in = bm.verts.new((v2_r.co.x * 0.96, v2_r.co.y - 0.003, v2_r.co.z))
        bm.faces.new((v1_r, v2_r, v2_in, v1_in)).material_index = 0

        v1_l = suit_rings[l_idx][-1]
        v2_l = suit_rings[l_idx + 1][-1]
        v1_lin = bm.verts.new((v1_l.co.x * 0.96, v1_l.co.y - 0.003, v1_l.co.z))
        v2_lin = bm.verts.new((v2_l.co.x * 0.96, v2_l.co.y - 0.003, v2_l.co.z))
        bm.faces.new((v1_l, v1_lin, v2_lin, v2_l)).material_index = 0

    # Dobladillo inferior del saco
    r_bot = suit_rings[0]
    for i in range(n_suit_pts - 1):
        v1 = r_bot[i]
        v2 = r_bot[i+1]
        v1_in = bm.verts.new((v1.co.x * 0.97, v1.co.y * 0.97, v1.co.z + 0.003))
        v2_in = bm.verts.new((v2.co.x * 0.97, v2.co.y * 0.97, v2.co.z + 0.003))
        bm.faces.new((v1, v2, v2_in, v1_in)).material_index = 0

    # Solapas notch clásicas en relieve
    for s_side in (1.0, -1.0):
        lapel_v = [
            bm.verts.new((s_side * 0.040, 0.044, 1.355)),
            bm.verts.new((s_side * 0.084, 0.076, 1.305)),
            bm.verts.new((s_side * 0.088, 0.086, 1.265)),
            bm.verts.new((s_side * 0.074, 0.088, 1.250)),
            bm.verts.new((s_side * 0.084, 0.096, 1.230)),
            bm.verts.new((s_side * 0.014, 0.084, 1.020)),
            bm.verts.new((s_side * 0.032, 0.088, 1.210)),
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
    bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.005, 0.086, 1.020))
    v_map_b = {v: bm.verts.new(v.co) for v in btn_bm.verts}
    for f in btn_bm.faces:
        bm.faces.new([v_map_b[v] for v in f.verts]).material_index = 6
    btn_bm.free()

    # Bolsillo superior de ojal
    p_box = [
        bm.verts.new((0.044, 0.094, 1.205)),
        bm.verts.new((0.080, 0.090, 1.205)),
        bm.verts.new((0.080, 0.090, 1.198)),
        bm.verts.new((0.044, 0.094, 1.198)),
    ]
    bm.faces.new(p_box).material_index = 0

    # -------------------------------------------------------------------------
    # CAPA D: BRAZOS, MANGAS Y MANOS CONECTADAS (CERO COLAPSO AXILAR)
    # Las mangas del saco están modeladas como cilindros orgánicos con
    # cúpula convexa cerrada en el hombro, puenteada con la sisa del torso.
    # -------------------------------------------------------------------------
    for is_l in (True, False):
        sign = 1.0 if is_l else -1.0

        # Manga sastre completa (desde el hombro hasta el puño)
        # 7 secciones para máxima fluidez articular
        arm_sections = [
            # center_x, center_y, z, radius
            (sign * 0.170, -0.003, 1.300, 0.046), # Sisa superior / hombrera
            (sign * 0.190, -0.002, 1.250, 0.042), # Deltoides
            (sign * 0.215,  0.000, 1.190, 0.038), # Bíceps
            (sign * 0.245,  0.002, 1.120, 0.035), # Codo
            (sign * 0.265,  0.005, 1.020, 0.030), # Antebrazo
            (sign * 0.280,  0.007, 0.940, 0.026), # Antebrazo bajo
            (sign * 0.285,  0.008, 0.885, 0.024), # Puño manga
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

        # Cúpula convexa superior de la hombrera (cierre suave del hombro)
        sh_apex = bm.verts.new((sign * 0.170, -0.003, 1.325))
        r_sh_top = arm_rings[0]
        for i in range(n_arm):
            inxt = (i + 1) % n_arm
            if sign > 0:
                bm.faces.new((r_sh_top[i], r_sh_top[inxt], sh_apex)).material_index = 0
            else:
                bm.faces.new((r_sh_top[inxt], r_sh_top[i], sh_apex)).material_index = 0

        # Conectar anillos de la manga
        for l_idx in range(len(arm_sections) - 1):
            r1 = arm_rings[l_idx]
            r2 = arm_rings[l_idx + 1]
            for i in range(n_arm):
                inxt = (i + 1) % n_arm
                if sign > 0:
                    bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i])).material_index = 0
                else:
                    bm.faces.new((r1[inxt], r1[i], r2[i], r2[inxt])).material_index = 0

        # Puño de camisa asomando
        cuff_ring = []
        for i in range(n_arm):
            ang = (2.0 * math.pi * i) / n_arm
            vx = sign * 0.285 + 0.020 * math.cos(ang)
            vy = 0.008 + 0.016 * math.sin(ang)
            cuff_ring.append(bm.verts.new((vx, vy, 0.868)))
        r_cuff_top = arm_rings[-1]
        for i in range(n_arm):
            inxt = (i + 1) % n_arm
            if sign > 0:
                bm.faces.new((r_cuff_top[i], r_cuff_top[inxt], cuff_ring[inxt], cuff_ring[i])).material_index = 4
            else:
                bm.faces.new((r_cuff_top[inxt], r_cuff_top[i], cuff_ring[i], cuff_ring[inxt])).material_index = 4

        # Muñeca anatómica de piel
        wrist_ring = []
        for i in range(n_arm):
            ang = (2.0 * math.pi * i) / n_arm
            vx = sign * 0.285 + 0.017 * math.cos(ang)
            vy = 0.008 + 0.013 * math.sin(ang)
            wrist_ring.append(bm.verts.new((vx, vy, 0.845)))
        for i in range(n_arm):
            inxt = (i + 1) % n_arm
            if sign > 0:
                bm.faces.new((cuff_ring[i], cuff_ring[inxt], wrist_ring[inxt], wrist_ring[i])).material_index = 3
            else:
                bm.faces.new((cuff_ring[inxt], cuff_ring[i], wrist_ring[i], wrist_ring[inxt])).material_index = 3

        # Palma anatómica
        w_center = Vector((sign * 0.285, 0.008, 0.820))
        z_knuckles = 0.816

        # Dedos anatómicos calibrados para PRENSIÓN REAL:
        # Mano L (Viewer's Left, sostiene el arco): puño cerrado abrazando el arco
        # Mano R (Viewer's Right, sostiene el violín): dedos curvados tocando el mástil
        finger_specs = [
            ("Index",   w_center.y + 0.012, 0.046, 0.0048),
            ("Middle",  w_center.y + 0.003, 0.050, 0.0050),
            ("Ring",    w_center.y - 0.005, 0.045, 0.0048),
            ("Pinky",   w_center.y - 0.013, 0.036, 0.0042),
        ]

        if is_l:
            # Mano L: empuñando el arco
            curl_dir = Vector((-0.35, 0.84, -0.28)).normalized()
        else:
            # Mano R: abrazando el mástil del violín por el frente (+Y, hacia el centro +X)
            curl_dir = Vector(( 0.38, 0.70, -0.42)).normalized()

        for fname, fy, f_len, f_rad in finger_specs:
            fx = sign * 0.285 + (sign * 0.012 if fname == "Index" else 0.0)
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
        th_root = Vector((sign * (0.285 - 0.014), w_center.y + 0.008, 0.822))
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

# =============================================================================
# 3. ESQUELETO Y RIGGING CON TRANSICIONES ARMÓNICAS (CERO DELTOIDES SUMIDO)
# =============================================================================
def build_skeleton():
    arm_data = bpy.data.armatures.new("Skeleton3D")
    arm_obj = bpy.data.objects.new("Skeleton3D", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = arm_data.edit_bones

    # Esqueleto calibrado a 1.65 m
    bones_def = [
        ("Root",        None,          (0, 0, 0),         (0, 0, 0.10)),
        ("Hips",        "Root",        (0, 0, 0.72),      (0, 0, 0.86)),
        ("Spine",       "Hips",        (0, 0, 0.86),      (0, 0, 1.08)),
        ("Chest",       "Spine",       (0, 0, 1.08),      (0, 0, 1.30)),
        ("Neck",        "Chest",       (0, 0, 1.30),      (0, 0, 1.37)),
        ("Head",        "Neck",        (0, 0, 1.37),      (0, 0, 1.63)),

        ("Shoulder.L",  "Chest",       (0.04, 0, 1.30),   (0.170, 0, 1.29)),
        ("UpperArm.L",  "Shoulder.L",  (0.170, 0, 1.29),  (0.245, 0.002, 1.12)),
        ("Forearm.L",   "UpperArm.L",  (0.245, 0.002, 1.12),(0.280, 0.007, 0.94)),
        ("Hand.L",      "Forearm.L",   (0.280, 0.007, 0.94),(0.285, 0.008, 0.76)),

        ("Shoulder.R",  "Chest",       (-0.04, 0, 1.30),  (-0.170, 0, 1.29)),
        ("UpperArm.R",  "Shoulder.R",  (-0.170, 0, 1.29), (-0.245, 0.002, 1.12)),
        ("Forearm.R",   "UpperArm.R",  (-0.245, 0.002, 1.12),(-0.280, 0.007, 0.94)),
        ("Hand.R",      "Forearm.R",   (-0.280, 0.007, 0.94),(-0.285, 0.008, 0.76)),

        ("UpperLeg.L",  "Hips",        (0.062, 0, 0.72),  (0.062, 0, 0.42)),
        ("LowerLeg.L",  "UpperLeg.L",  (0.062, 0, 0.42),  (0.062, 0, 0.11)),
        ("Foot.L",      "LowerLeg.L",  (0.062, 0, 0.11),  (0.062, 0.045, 0.03)),
        ("Toes.L",      "Foot.L",      (0.062, 0.045, 0.03),(0.062, 0.090, 0.00)),

        ("UpperLeg.R",  "Hips",        (-0.062, 0, 0.72), (-0.062, 0, 0.42)),
        ("LowerLeg.R",  "UpperLeg.R",  (-0.062, 0, 0.42), (-0.062, 0, 0.11)),
        ("Foot.R",      "LowerLeg.R",  (-0.062, 0, 0.11), (-0.062, 0.045, 0.03)),
        ("Toes.R",      "Foot.R",      (-0.062, 0.045, 0.03),(-0.062, 0.090, 0.00)),
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

            # 1. BRAZOS Y MANGAS (ax >= 0.14 y z entre 0.70 y 1.35)
            # Transición armónica en hombro basada en distancia euclidiana al acromion
            if ax >= 0.14 and co.z >= 0.70 and co.z <= 1.35:
                sh_cen = Vector((math.copysign(0.170, co.x), 0.0, 1.29))
                dist_sh = (Vector((co.x, co.y, co.z)) - sh_cen).length

                if co.z < 0.88:
                    # Mano
                    obj.vertex_groups["Hand" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.94:
                    # Muñeca
                    t = (co.z - 0.88) / 0.06
                    obj.vertex_groups["Hand" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Forearm" + side].add([v.index], t, 'REPLACE')
                elif co.z < 1.08:
                    # Antebrazo
                    obj.vertex_groups["Forearm" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.16:
                    # Codo
                    t = (co.z - 1.08) / 0.08
                    obj.vertex_groups["Forearm" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["UpperArm" + side].add([v.index], t, 'REPLACE')
                elif co.z < 1.24:
                    # Brazo superior
                    obj.vertex_groups["UpperArm" + side].add([v.index], 1.0, 'REPLACE')
                else:
                    # Zona deltoides / hombrera (dist_sh < 0.08):
                    # Transición suave entre Chest, Shoulder y UpperArm para evitar colapso
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

            # 2. HOMBRO INTERIOR / CLAVÍCULA (ax entre 0.08 y 0.14)
            elif ax >= 0.08 and co.z >= 1.22:
                t = (ax - 0.08) / 0.06
                obj.vertex_groups["Chest"].add([v.index], 1.0 - 0.75 * t, 'REPLACE')
                obj.vertex_groups["Shoulder" + side].add([v.index], 0.75 * t, 'REPLACE')

            # 3. PIERNAS Y CALZADO (co.z < 0.72)
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

            # 4. TORSO, CAMISA Y SACO CENTRAL
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

# =============================================================================
# 4. POSICIONAMIENTO Y PRENSIÓN EXACTA DE VIOLÍN Y ARCO
# =============================================================================
def apply_violin_pose_and_props(arm_obj):
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')

    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)

    # Pose canónica de Astorga según scratch/humans/astorga.png:
    # 1. Torso erguido con leve giro 3/4
    arm_obj.pose.bones['Chest'].rotation_euler = (math.radians(-2), math.radians(-4), math.radians(2))
    arm_obj.pose.bones['Head'].rotation_euler = (math.radians(-1), math.radians(5), math.radians(1))

    # 2. Brazo VIEWER'S RIGHT (Hand.R, -X): Sostiene el VIOLÍN verticalmente
    # Hombro acompaña coordinadamente, codo flexionado en ángulo agudo, muñeca alzada
    arm_obj.pose.bones['Shoulder.R'].rotation_euler = (math.radians(2), math.radians(2), math.radians(-2))
    arm_obj.pose.bones['UpperArm.R'].rotation_euler = (math.radians(32), math.radians(14), math.radians(-26))
    arm_obj.pose.bones['Forearm.R'].rotation_euler = (math.radians(98), math.radians(14), math.radians(-8))
    arm_obj.pose.bones['Hand.R'].rotation_euler = (math.radians(26), math.radians(-16), math.radians(42))

    # 3. Brazo VIEWER'S LEFT (Hand.L, +X): Sostiene el ARCO cruzado en diagonal
    # Clavícula acompaña suavemente (+2°), hombro con transición coordinada (cero sumido)
    arm_obj.pose.bones['Shoulder.L'].rotation_euler = (math.radians(2), math.radians(-1), math.radians(2))
    arm_obj.pose.bones['UpperArm.L'].rotation_euler = (math.radians(18), math.radians(-4), math.radians(8))
    arm_obj.pose.bones['Forearm.L'].rotation_euler = (math.radians(50), math.radians(-6), math.radians(6))
    arm_obj.pose.bones['Hand.L'].rotation_euler = (math.radians(22), math.radians(10), math.radians(-8))

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()

    hand_l_mat = arm_obj.matrix_world @ arm_obj.pose.bones['Hand.L'].matrix
    hand_r_mat = arm_obj.matrix_world @ arm_obj.pose.bones['Hand.R'].matrix
    hand_l_loc = hand_l_mat.to_translation()
    hand_r_loc = hand_r_mat.to_translation()

    # Cargar Violín y Arco
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
                    # Violín vertical sujetado anatómicamente:
                    # El mástil pasa exactamente por el espacio entre pulgar y dedos de Hand.R
                    o.rotation_euler = Euler((math.radians(-76), math.radians(172), math.radians(18)), 'XYZ')
                    # Calibrado milimétrico para contacto frontal visible
                    o.location = Vector((hand_r_loc.x + 0.007, hand_r_loc.y - 0.012, hand_r_loc.z - 0.208))
                elif o.name == "Violin_Bow":
                    o.scale = (0.70, 0.70, 0.70)
                    # El arco pasa a través del puño cerrado de Hand.L
                    o.rotation_euler = Euler((math.radians(26), math.radians(-4), math.radians(-18)), 'XYZ')
                    o.location = Vector((hand_l_loc.x - 0.001, hand_l_loc.y + 0.008, hand_l_loc.z - 0.020))

def render_views(arm_obj):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 24
    scene.view_settings.view_transform = 'Standard'

    # Luces de estudio cinemático
    def add_light(name, ltype, energy, loc, color=(1,1,1), size=1.0):
        ld = bpy.data.lights.new(name, ltype)
        ld.energy = energy
        ld.color = color
        if hasattr(ld, 'size'): ld.size = size
        lo = bpy.data.objects.new(name, ld)
        lo.location = Vector(loc)
        scene.collection.objects.link(lo)
        return lo

    chest_t = Vector((0.0, 0.0, 1.20))
    head_t = Vector((0.0, 0.0, 1.48))

    add_light("KeyLight",   'AREA', 180.0, (-0.8, 1.8, 1.6), (1.0, 0.96, 0.92), size=1.8)
    add_light("FillLight",  'AREA', 100.0, ( 1.0, 1.6, 1.4), (0.94, 0.96, 1.0), size=2.2)
    add_light("RimLight",   'SPOT', 140.0, ( 0.1,-1.5, 1.9), (1.0, 0.98, 0.94))
    add_light("ViolinLight",'AREA',  75.0, (-0.5, 1.7, 1.28), (1.0, 0.95, 0.88), size=1.0)
    add_light("BodyFill",   'AREA',  60.0, ( 0.0, 2.0, 0.90), (0.98, 0.98, 1.0), size=2.0)

    cam_data = bpy.data.cameras.new("RenderCam")
    cam_obj = bpy.data.objects.new("RenderCam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # 1. Render de Tarjeta / Retrato (1024x1024)
    cam_data.lens = 72.0
    cam_obj.location = Vector((0.0, 2.15, 1.24))
    target = Vector((0.0, 0.0, 1.21))
    cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024

    out_portrait = os.path.join(SCRATCH_DIR, "test_astorga_portrait_v2.png")
    scene.render.filepath = out_portrait
    bpy.ops.render.render(write_still=True)
    print("✓ Render de retrato guardado en:", out_portrait)

    # 2. Render de Cuerpo Completo (800x1200)
    cam_data.lens = 52.0
    cam_obj.location = Vector((0.0, 2.50, 0.94))
    target_fb = Vector((0.0, 0.0, 0.86))
    cam_obj.rotation_euler = (target_fb - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1200

    out_fb = os.path.join(SCRATCH_DIR, "test_astorga_fullbody_v2.png")
    scene.render.filepath = out_fb
    bpy.ops.render.render(write_still=True)
    print("✓ Render de cuerpo completo guardado en:", out_fb)

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
