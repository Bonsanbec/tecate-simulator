"""
=============================================================================
PRUEBA DE ARQUITECTURA POR CAPAS SEPARADAS: ASTORGA (TECATE SIMULATOR)
=============================================================================
Resuelve los 4 problemas señalados por el usuario con rigor absoluto:
1. Camisa separada del cuerpo: Capa geométrica independiente que viste el torso
   desde el cuello hasta la cintura (Z = 0.86) sin clippear con el cuerpo.
2. Saco separado del cuerpo con apertura física: Prenda sastre tridimensional
   independiente (r_saco > r_camisa) con paneles frontales que se cruzan en el
   botón y se abren físicamente en V invertida mostrando la camisa y el pantalón.
3. Hombro estructurado con hombrera sastre: Deltoides/hombrera con volumen convexo
   independiente que no se sume al rotar el brazo.
4. Prensión real del violín: El mástil pasa exactamente a través del agarre de
   la mano derecha, con los dedos abrazando el mástil por el frente visiblemente.
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
ASTORGA_BLEND = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/citizens/astorga.blend")

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

def setup_pbr_material(name, diffuse_tex_path, normal_tex_path=None,
                       base_color=(0.8, 0.8, 0.8, 1.0), roughness=0.6,
                       metallic=0.0, specular=0.5):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out_node = nodes.new('ShaderNodeOutputMaterial')
    out_node.location = (400, 0)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])

    bsdf.inputs['Base Color'].default_value = base_color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = specular

    if diffuse_tex_path and os.path.exists(diffuse_tex_path):
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.location = (-400, 100)
        img = bpy.data.images.load(diffuse_tex_path, check_existing=True)
        tex_node.image = img
        links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])

    if normal_tex_path and os.path.exists(normal_tex_path):
        norm_tex = nodes.new('ShaderNodeTexImage')
        norm_tex.location = (-400, -200)
        img_n = bpy.data.images.load(normal_tex_path, check_existing=True)
        img_n.colorspace_settings.name = 'Non-Color'
        norm_tex.image = img_n
        norm_map = nodes.new('ShaderNodeNormalMap')
        norm_map.location = (-150, -200)
        norm_map.inputs['Strength'].default_value = 0.85
        links.new(norm_tex.outputs['Color'], norm_map.inputs['Color'])
        links.new(norm_map.outputs['Normal'], bsdf.inputs['Normal'])

    return mat

def create_materials():
    return {
        "skin": setup_pbr_material("Mat_Astorga_Skin",
                                   os.path.join(TEXTURES_DIR, "astorga_face_diffuse.png"),
                                   os.path.join(TEXTURES_DIR, "astorga_face_normal.png"),
                                   base_color=(0.550, 0.400, 0.315, 1.0), roughness=0.52),
        "eyes": setup_pbr_material("Mat_Astorga_Eyes",
                                   os.path.join(TEXTURES_DIR, "astorga_eye_diffuse.png"),
                                   None,
                                   base_color=(0.28, 0.16, 0.09, 1.0), roughness=0.10),
        "hair": setup_pbr_material("Mat_Astorga_Hair",
                                   os.path.join(TEXTURES_DIR, "astorga_hair_diffuse.png"),
                                   os.path.join(TEXTURES_DIR, "astorga_hair_normal.png"),
                                   base_color=(0.045, 0.035, 0.030, 1.0), roughness=0.70, specular=0.35),
        "suit": setup_pbr_material("Mat_Astorga_Suit",
                                   os.path.join(TEXTURES_DIR, "astorga_suit_diffuse.png"),
                                   os.path.join(TEXTURES_DIR, "astorga_suit_normal.png"),
                                   base_color=(0.045, 0.048, 0.055, 1.0), roughness=0.62),
        "shirt": setup_pbr_material("Mat_Astorga_Shirt",
                                    os.path.join(TEXTURES_DIR, "astorga_shirt_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "astorga_shirt_normal.png"),
                                    base_color=(0.280, 0.045, 0.065, 1.0), roughness=0.55),
        "tie": setup_pbr_material("Mat_Astorga_Tie",
                                  os.path.join(TEXTURES_DIR, "astorga_tie_diffuse.png"),
                                  os.path.join(TEXTURES_DIR, "astorga_tie_normal.png"),
                                  base_color=(0.025, 0.020, 0.022, 1.0), roughness=0.35, specular=0.55),
        "pants": setup_pbr_material("Mat_Astorga_Pants",
                                    os.path.join(TEXTURES_DIR, "astorga_pants_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "astorga_pants_normal.png"),
                                    base_color=(0.045, 0.048, 0.055, 1.0), roughness=0.65),
        "shoes": setup_pbr_material("Mat_Astorga_Shoes",
                                    os.path.join(TEXTURES_DIR, "astorga_shoes_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "astorga_shoes_normal.png"),
                                    base_color=(0.020, 0.020, 0.025, 1.0), roughness=0.20, specular=0.65),
        "buttons": setup_pbr_material("Mat_Astorga_Buttons",
                                      None, None,
                                      base_color=(0.02, 0.02, 0.02, 1.0), roughness=0.20, metallic=0.40),
    }

# =============================================================================
# 1. CABEZA Y MELENA CONTINUA 360° (APROBADA)
# =============================================================================
# Reutilizamos la función build_head_mesh del generador canónico que ya aprobó el usuario
# (melena continua 360° sin huecos, rostro moreno cálido y ojos castaños)
def build_head(materials):
    from scripts.characters.generate_astorga import build_head_mesh
    return build_head_mesh(materials)

# =============================================================================
# 2. CUERPO ESTRUCTURADO EN 3 CAPAS REALES:
#    CAPA A: CUERPO BASE Y PANTALÓN SASTRE (r_base)
#    CAPA B: CAMISA VINOTINTO COMPLETA SEPARADA (r_camisa = r_base + 3mm)
#    CAPA C: SACO SASTRE SEPARADO CON APERTURA EN V Y HOMBRERAS (r_saco = r_camisa + 4mm)
# =============================================================================
def build_layered_body(materials):
    me = bpy.data.meshes.new("Player_Body_Mesh_Data")
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")

    # -------------------------------------------------------------------------
    # CAPA A: CUERPO BASE (Pantalón formal negro, zapatos y extremidades)
    # -------------------------------------------------------------------------
    # Piernas con corte sastre recto y zapatos
    leg_nodes_l = [
        ( 0.062, 0.002, 0.74, 0.050), # 0: Cadera alta
        ( 0.062, 0.002, 0.58, 0.045), # 1: Muslo
        ( 0.062, 0.000, 0.43, 0.040), # 2: Rodilla
        ( 0.062, 0.000, 0.27, 0.036), # 3: Pantorrilla
        ( 0.062, 0.002, 0.11, 0.032), # 4: Tobillo
    ]
    # Generar anillos de piernas en quads limpios
    n_ring = 16
    for is_l in (True, False):
        sign = 1.0 if is_l else -1.0
        prev_ring = None
        for (lx, ly, lz, lr) in leg_nodes_l:
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

        # Zapatos de vestir pulidos con puntera y tacón modelados
        # Anillo tobillo
        v_ankle = prev_ring
        shoe_sole = []
        for i in range(n_ring):
            ang = (2.0 * math.pi * i) / n_ring
            ca = math.cos(ang)
            sa = math.sin(ang)
            sx = sign * 0.062 + 0.036 * ca
            sy = 0.025 + (0.075 if sa > 0 else 0.045) * sa
            sz = 0.012
            shoe_sole.append(bm.verts.new((sx, sy, sz)))
        for i in range(n_ring):
            inxt = (i + 1) % n_ring
            f = bm.faces.new((v_ankle[i], v_ankle[inxt], shoe_sole[inxt], shoe_sole[i]))
            f.material_index = 2 # Mat_Astorga_Shoes
        # Suela inferior
        sole_cen = bm.verts.new((sign * 0.062, 0.025, 0.000))
        for i in range(n_ring):
            inxt = (i + 1) % n_ring
            f = bm.faces.new((shoe_sole[inxt], shoe_sole[i], sole_cen))
            f.material_index = 2

    # Pelvis / Caderas del pantalón (Z = 0.74 a Z = 0.88)
    pelvis_levels = [
        (0.74, 0.114, 0.076),
        (0.80, 0.116, 0.076),
        (0.86, 0.114, 0.074), # Cintura del pantalón
    ]
    pelvis_rings = []
    for (pz, prx, pry) in pelvis_levels:
        cur_ring = []
        for i in range(24):
            ang = (2.0 * math.pi * i) / 24
            vx = prx * math.cos(ang)
            vy = pry * math.sin(ang)
            cur_ring.append(bm.verts.new((vx, vy, pz)))
        pelvis_rings.append(cur_ring)

    for l_idx in range(len(pelvis_levels) - 1):
        r1 = pelvis_rings[l_idx]
        r2 = pelvis_rings[l_idx + 1]
        for i in range(24):
            inxt = (i + 1) % 24
            bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i])).material_index = 1 # Pantalón

    # Cerrar entrepierna inferior (conexión de piernas con pelvis)
    # Fondo de entrepierna
    crotch_cen = bm.verts.new((0.0, 0.002, 0.74))
    r_pelv_bot = pelvis_rings[0]
    for i in range(24):
        inxt = (i + 1) % 24
        bm.faces.new((r_pelv_bot[inxt], r_pelv_bot[i], crotch_cen)).material_index = 1

    # -------------------------------------------------------------------------
    # CAPA B: CAMISA VINOTINTO MODELADA COMO PRENDA SEPARADA (Z = 0.86 a 1.36)
    # Cubre todo el torso por debajo del saco con radio independiente r_camisa
    # -------------------------------------------------------------------------
    shirt_levels = [
        # z,     rx,    ry_front, ry_back, y_off
        (0.86,  0.116,  0.078,    0.076,   0.002), # Cintura (se mete bajo el pantalón)
        (0.94,  0.116,  0.078,    0.076,   0.002), # Abdomen bajo
        (1.02,  0.118,  0.080,    0.078,   0.000), # Ombligo / abdomen medio
        (1.10,  0.124,  0.084,    0.084,  -0.002), # Tórax
        (1.18,  0.130,  0.090,    0.090,  -0.004), # Pectorales
        (1.26,  0.132,  0.090,    0.090,  -0.004), # Pecho alto
        (1.33,  0.118,  0.080,    0.080,  -0.002), # Clavícula
        (1.36,  0.048,  0.048,    0.048,   0.002), # Cuello
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
            f.material_index = 4 # Mat_Astorga_Shirt (Vinotinto puro continuo)

    # Cuello camisero 3D con pie de cuello y puntas dobladas hacia el frente
    n_c = 18
    c_bot, c_top = [], []
    for i in range(n_c):
        ang = (2.0 * math.pi * i) / n_c
        cx = 0.048 * math.cos(ang)
        cy = 0.048 * math.sin(ang) + 0.002
        c_bot.append(bm.verts.new((cx, cy, 1.345)))
        c_top.append(bm.verts.new((cx * 1.06, cy * 1.06, 1.385)))
    for i in range(n_c):
        inxt = (i + 1) % n_c
        bm.faces.new((c_bot[i], c_bot[inxt], c_top[inxt], c_top[i])).material_index = 4

    wing_l = [bm.verts.new((0.006, 0.055, 1.382)), bm.verts.new((0.042, 0.046, 1.375)), bm.verts.new((0.022, 0.070, 1.335))]
    wing_r = [bm.verts.new((-0.006, 0.055, 1.382)), bm.verts.new((-0.022, 0.070, 1.335)), bm.verts.new((-0.042, 0.046, 1.375))]
    bm.faces.new(wing_l).material_index = 4
    bm.faces.new(wing_r).material_index = 4

    # Tapeta central camisera con botonadura vertical en relieve
    for bz in (0.92, 1.00, 1.08, 1.16, 1.24):
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=6, v_segments=4, radius=0.0030)
        bmesh.ops.scale(btn_bm, verts=btn_bm.verts, vec=(1.0, 0.4, 1.0))
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.0, 0.082, bz))
        v_map_b = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            bm.faces.new([v_map_b[v] for v in f.verts]).material_index = 4
        btn_bm.free()

    # Corbata de seda oscura con nudo Windsor cayendo verticalmente
    knot_v = [
        bm.verts.new((-0.014, 0.058, 1.375)),
        bm.verts.new(( 0.014, 0.058, 1.375)),
        bm.verts.new(( 0.010, 0.078, 1.335)),
        bm.verts.new((-0.010, 0.078, 1.335)),
        bm.verts.new(( 0.000, 0.086, 1.355)),
    ]
    for f_verts in [
        (knot_v[0], knot_v[1], knot_v[4]),
        (knot_v[1], knot_v[2], knot_v[4]),
        (knot_v[2], knot_v[3], knot_v[4]),
        (knot_v[3], knot_v[0], knot_v[4]),
    ]:
        bm.faces.new(f_verts).material_index = 5 # Mat_Astorga_Tie

    tie_profile = [
        (1.335,  0.010,  0.078),
        (1.265,  0.012,  0.090),
        (1.195,  0.013,  0.094),
        (1.125,  0.013,  0.092),
        (1.055,  0.011,  0.086),
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
    # CAPA C: SACO SASTRE SEPARADO CON APERTURA FÍSICA EN V (r_saco > r_camisa)
    # Prenda externa envolvente que cubre hombros, espalda y costados, y cuyos
    # paneles frontales se cruzan en el botón central y SE ABREN hacia abajo en V
    # -------------------------------------------------------------------------
    suit_levels = [
        # z,     rx,    ry_front, ry_back, y_off,  v_open_w (semiancho apertura frontal)
        (0.74,  0.126,  0.086,    0.086,   0.002,  0.080), # Dobladillo inferior abierto en V invertida
        (0.80,  0.124,  0.085,    0.085,   0.002,  0.060), # Cadera media
        (0.88,  0.122,  0.084,    0.084,   0.002,  0.035), # Cintura
        (0.98,  0.120,  0.083,    0.083,   0.000,  0.012), # Botón inferior (casi cerrado)
        (1.05,  0.122,  0.085,    0.084,   0.000,  0.006), # Botón superior (cerrado formal)
        (1.14,  0.132,  0.094,    0.092,  -0.002,  0.025), # Pectorales (apertura en V hacia cuello)
        (1.22,  0.142,  0.098,    0.096,  -0.004,  0.045), # Pecho alto
        (1.30,  0.144,  0.094,    0.092,  -0.004,  0.060), # Hombros sastre anchos
    ]

    # Para cada nivel, generamos un arco abierto al frente que abraza el torso
    n_suit_pts = 28
    suit_rings = []
    for (sz, srx, sry_f, sry_b, sy_off, open_w) in suit_levels:
        cur_ring = []
        for i in range(n_suit_pts):
            t = i / float(n_suit_pts - 1) # 0.0 (borde frontal derecho) a 1.0 (borde frontal izquierdo)
            # Ángulo desde el borde derecho frontal, pasando por la espalda, hasta el borde izquierdo frontal
            # phi de +alpha a -alpha pasando por detrás
            ang_start = math.asin(min(0.95, open_w / max(0.01, srx)))
            # Mapeamos t de 0 a 1 a lo largo del contorno exterior:
            # t=0: borde derecho (X = -open_w, Y frontal)
            # t=0.5: centro de la espalda (X = 0, Y posterior)
            # t=1: borde izquierdo (X = +open_w, Y frontal)
            phi = -math.pi * 0.5 + (t - 0.5) * (2.0 * math.pi - 2.0 * ang_start)
            vx = srx * math.sin(phi)
            sa = -math.cos(phi)
            vy = (sry_f if sa >= 0 else sry_b) * sa + sy_off
            cur_ring.append(bm.verts.new((vx, vy, sz)))
        suit_rings.append(cur_ring)

    # Conectar los anillos del saco
    for l_idx in range(len(suit_levels) - 1):
        r1 = suit_rings[l_idx]
        r2 = suit_rings[l_idx + 1]
        for i in range(n_suit_pts - 1):
            f = bm.faces.new((r1[i], r1[i+1], r2[i+1], r2[i]))
            f.material_index = 0 # Mat_Astorga_Suit

    # Dobladillo con espesor de tela en los bordes frontales abiertos
    # Esto da acabado sastre de alta costura a la abertura del saco
    for l_idx in range(len(suit_levels) - 1):
        # Borde frontal derecho (índice 0)
        v1_r = suit_rings[l_idx][0]
        v2_r = suit_rings[l_idx + 1][0]
        v1_in = bm.verts.new((v1_r.co.x * 0.96, v1_r.co.y - 0.004, v1_r.co.z))
        v2_in = bm.verts.new((v2_r.co.x * 0.96, v2_r.co.y - 0.004, v2_r.co.z))
        bm.faces.new((v1_r, v2_r, v2_in, v1_in)).material_index = 0

        # Borde frontal izquierdo (índice -1)
        v1_l = suit_rings[l_idx][-1]
        v2_l = suit_rings[l_idx + 1][-1]
        v1_lin = bm.verts.new((v1_l.co.x * 0.96, v1_l.co.y - 0.004, v1_l.co.z))
        v2_lin = bm.verts.new((v2_l.co.x * 0.96, v2_l.co.y - 0.004, v2_l.co.z))
        bm.faces.new((v1_l, v1_lin, v2_lin, v2_l)).material_index = 0

    # Dobladillo inferior del saco (cerrar la base en Z = 0.74 hacia adentro)
    r_bot = suit_rings[0]
    for i in range(n_suit_pts - 1):
        v1 = r_bot[i]
        v2 = r_bot[i+1]
        v1_in = bm.verts.new((v1.co.x * 0.97, v1.co.y * 0.97, v1.co.z + 0.004))
        v2_in = bm.verts.new((v2.co.x * 0.97, v2.co.y * 0.97, v2.co.z + 0.004))
        bm.faces.new((v1, v2, v2_in, v1_in)).material_index = 0

    # Solapas notch formales tridimensionales cosidas sobre el borde del saco
    for s_side in (1.0, -1.0):
        lapel_v = [
            bm.verts.new((s_side * 0.044, 0.046, 1.355)),
            bm.verts.new((s_side * 0.088, 0.080, 1.305)),
            bm.verts.new((s_side * 0.092, 0.090, 1.265)),
            bm.verts.new((s_side * 0.076, 0.092, 1.250)),
            bm.verts.new((s_side * 0.088, 0.100, 1.230)),
            bm.verts.new((s_side * 0.016, 0.088, 1.055)),
            bm.verts.new((s_side * 0.034, 0.092, 1.210)),
        ]
        if s_side > 0:
            bm.faces.new((lapel_v[0], lapel_v[1], lapel_v[2], lapel_v[3])).material_index = 0
            bm.faces.new((lapel_v[0], lapel_v[3], lapel_v[6])).material_index = 0
            bm.faces.new((lapel_v[3], lapel_v[4], lapel_v[5], lapel_v[6])).material_index = 0
        else:
            bm.faces.new((lapel_v[1], lapel_v[0], lapel_v[3], lapel_v[2])).material_index = 0
            bm.faces.new((lapel_v[3], lapel_v[0], lapel_v[6])).material_index = 0
            bm.faces.new((lapel_v[4], lapel_v[3], lapel_v[6], lapel_v[5])).material_index = 0

    # Cuello de saco que rodea la nuca
    sc_top, sc_bot = [], []
    for i in range(10):
        ang = math.pi * 0.15 + (math.pi * 0.70 * i) / 9.0
        bx = 0.052 * math.cos(ang)
        by = -0.050 * math.sin(ang) - 0.003
        sc_top.append(bm.verts.new((bx, by, 1.375)))
        sc_bot.append(bm.verts.new((bx, by, 1.345)))
    for i in range(9):
        bm.faces.new((sc_bot[i], sc_bot[i+1], sc_top[i+1], sc_top[i])).material_index = 0

    # Botones sastre anclados exactamente sobre la solapa derecha
    button_coords = [
        (0.005, 0.088, 1.050),
        (0.005, 0.086, 0.980)
    ]
    for (bx, by, bz) in button_coords:
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.0042)
        bmesh.ops.scale(btn_bm, verts=btn_bm.verts, vec=(1.0, 0.30, 1.0))
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(bx, by + 0.0012, bz))
        v_map_b = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            bm.faces.new([v_map_b[v] for v in f.verts]).material_index = 6 # Mat_Astorga_Buttons
        btn_bm.free()

    # Bolsillo superior de ojal
    p_box = [
        bm.verts.new((0.046, 0.096, 1.205)),
        bm.verts.new((0.082, 0.092, 1.205)),
        bm.verts.new((0.082, 0.092, 1.198)),
        bm.verts.new((0.046, 0.096, 1.198)),
    ]
    bm.faces.new(p_box).material_index = 0

    # -------------------------------------------------------------------------
    # CAPA D: BRAZOS SASTRE CON HOMBRERAS CONVEXAS ESTRUCTURADAS (CERO SUMIDO)
    # -------------------------------------------------------------------------
    for is_l in (True, False):
        sign = 1.0 if is_l else -1.0

        # Hombrera convexa estructurada (tapa esférica rígida en el acromion)
        # Nace en X = sign*0.14 hasta sign*0.20 y Z = 1.28 a 1.33
        shoulder_bm = bmesh.new()
        bmesh.ops.create_uvsphere(shoulder_bm, u_segments=12, v_segments=8, radius=0.048)
        bmesh.ops.scale(shoulder_bm, verts=shoulder_bm.verts, vec=(1.1, 0.95, 0.75))
        bmesh.ops.translate(shoulder_bm, verts=shoulder_bm.verts, vec=(sign * 0.180, -0.003, 1.300))
        # Solo conservamos la cúpula superior/externa de la hombrera
        del_verts = [v for v in shoulder_bm.verts if (v.co.z < 1.275 or (v.co.x * sign) < 0.135)]
        bmesh.ops.delete(shoulder_bm, geom=del_verts, context='VERTS')
        v_map_sh = {v: bm.verts.new(v.co) for v in shoulder_bm.verts}
        for f in shoulder_bm.faces:
            bm.faces.new([v_map_sh[v] for v in f.verts]).material_index = 0
        shoulder_bm.free()

        # Manga del saco formal (cilindro sastre articulado continuo)
        arm_sections = [
            # center_x, center_y, z, radius
            (sign * 0.185, -0.003, 1.285, 0.044), # Base hombrera
            (sign * 0.215,  0.000, 1.200, 0.038), # Bíceps
            (sign * 0.245,  0.002, 1.120, 0.035), # Codo
            (sign * 0.270,  0.005, 1.020, 0.030), # Antebrazo
            (sign * 0.285,  0.008, 0.915, 0.026), # Puño manga
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

        for l_idx in range(len(arm_sections) - 1):
            r1 = arm_rings[l_idx]
            r2 = arm_rings[l_idx + 1]
            for i in range(n_arm):
                inxt = (i + 1) % n_arm
                bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i])).material_index = 0

        # Puño de camisa asomando bajo la manga
        cuff_ring = []
        for i in range(n_arm):
            ang = (2.0 * math.pi * i) / n_arm
            vx = sign * 0.285 + 0.021 * math.cos(ang)
            vy = 0.008 + 0.017 * math.sin(ang)
            cuff_ring.append(bm.verts.new((vx, vy, 0.895)))
        r_cuff_top = arm_rings[-1]
        for i in range(n_arm):
            inxt = (i + 1) % n_arm
            bm.faces.new((r_cuff_top[i], r_cuff_top[inxt], cuff_ring[inxt], cuff_ring[i])).material_index = 4

        # Muñeca anatómica de piel
        wrist_ring = []
        for i in range(n_arm):
            ang = (2.0 * math.pi * i) / n_arm
            vx = sign * 0.285 + 0.018 * math.cos(ang)
            vy = 0.008 + 0.014 * math.sin(ang)
            wrist_ring.append(bm.verts.new((vx, vy, 0.865)))
        for i in range(n_arm):
            inxt = (i + 1) % n_arm
            bm.faces.new((cuff_ring[i], cuff_ring[inxt], wrist_ring[inxt], wrist_ring[i])).material_index = 3 # Skin

        # Palma anatómica
        w_center = Vector((sign * 0.285, 0.008, 0.835))
        z_knuckles = 0.832

        # ---------------------------------------------------------------------
        # PRENSIÓN REAL:
        # Mano izquierda: dedos curvados firmemente abrazando el talón del arco
        # Mano derecha: dedos curvados rodeando el mástil del violín por el frente
        # ---------------------------------------------------------------------
        finger_specs = [
            ("Index",   w_center.y + 0.012, 0.046, 0.0048),
            ("Middle",  w_center.y + 0.003, 0.050, 0.0050),
            ("Ring",    w_center.y - 0.005, 0.045, 0.0048),
            ("Pinky",   w_center.y - 0.013, 0.036, 0.0042),
        ]

        if is_l:
            # Mano izquierda empuña el arco con los dedos cerrados hacia la palma
            curl_dir = Vector((-0.38, 0.86, -0.25)).normalized()
        else:
            # Mano derecha: dedos curvados abrazando el mástil hacia adelante y al centro (+Y, +X hacia mástil)
            curl_dir = Vector(( 0.35, 0.72, -0.42)).normalized()

        for (f_name, fy, f_len, f_rad) in finger_specs:
            fx = sign * 0.285
            n_seg = 3
            prev_fring = None
            for s in range(n_seg + 1):
                t = s / float(n_seg)
                if is_l:
                    fz = z_knuckles - f_len * (t**0.9) * 0.52
                    cur_y = fy + curl_dir.y * (f_len * 0.92 * (t**1.1))
                    cur_x = fx + curl_dir.x * (f_len * 0.52 * (t**1.1))
                else:
                    fz = z_knuckles - f_len * (t**0.85) * 0.68
                    cur_y = fy + curl_dir.y * (f_len * 0.80 * (t**1.2))
                    cur_x = fx + curl_dir.x * (f_len * 0.44 * (t**1.2))
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
        th_root = Vector((sign * (0.285 - 0.014), w_center.y + 0.008, 0.838))
        prev_th = None
        th_curl = Vector((-sign * 0.45, 0.68, -0.32)).normalized()
        for s in range(4):
            t = s / 3.0
            tx = th_root.x + th_curl.x * 0.024 * t
            ty = th_root.y + th_curl.y * 0.024 * t
            tz = th_root.z - 0.020 * t
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
# 3. ESQUELETO Y RIGGING CON BLINDAJE DE HOMBRO (CERO SUMIDO)
# =============================================================================
def build_skeleton():
    arm_data = bpy.data.armatures.new("Skeleton3D")
    arm_obj = bpy.data.objects.new("Skeleton3D", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = arm_data.edit_bones

    bones_def = [
        ("Root",        None,          (0, 0, 0),         (0, 0, 0.10)),
        ("Hips",        "Root",        (0, 0, 0.74),      (0, 0, 0.88)),
        ("Spine",       "Hips",        (0, 0, 0.88),      (0, 0, 1.10)),
        ("Chest",       "Spine",       (0, 0, 1.10),      (0, 0, 1.31)),
        ("Neck",        "Chest",       (0, 0, 1.31),      (0, 0, 1.38)),
        ("Head",        "Neck",        (0, 0, 1.38),      (0, 0, 1.63)),

        ("Shoulder.L",  "Chest",       (0.04, 0, 1.31),   (0.180, 0, 1.30)),
        ("UpperArm.L",  "Shoulder.L",  (0.180, 0, 1.30),  (0.245, 0.005, 1.12)),
        ("Forearm.L",   "UpperArm.L",  (0.245, 0.005, 1.12),(0.285, 0.015, 0.915)),
        ("Hand.L",      "Forearm.L",   (0.285, 0.015, 0.915),(0.285, 0.015, 0.76)),

        ("Shoulder.R",  "Chest",       (-0.04, 0, 1.31),  (-0.180, 0, 1.30)),
        ("UpperArm.R",  "Shoulder.R",  (-0.180, 0, 1.30), (-0.245, 0.005, 1.12)),
        ("Forearm.R",   "UpperArm.R",  (-0.245, 0.005, 1.12),(-0.285, 0.015, 0.915)),
        ("Hand.R",      "Forearm.R",   (-0.285, 0.015, 0.915),(-0.285, 0.015, 0.76)),

        ("UpperLeg.L",  "Hips",        (0.062, 0, 0.74),  (0.062, 0, 0.43)),
        ("LowerLeg.L",  "UpperLeg.L",  (0.062, 0, 0.43),  (0.062, 0, 0.11)),
        ("Foot.L",      "LowerLeg.L",  (0.062, 0, 0.11),  (0.062, 0.048, 0.03)),
        ("Toes.L",      "Foot.L",      (0.062, 0.048, 0.03),(0.062, 0.095, 0.00)),

        ("UpperLeg.R",  "Hips",        (-0.062, 0, 0.74), (-0.062, 0, 0.43)),
        ("LowerLeg.R",  "UpperLeg.R",  (-0.062, 0, 0.43), (-0.062, 0, 0.11)),
        ("Foot.R",      "LowerLeg.R",  (-0.062, 0, 0.11), (-0.062, 0.048, 0.03)),
        ("Toes.R",      "Foot.R",      (-0.062, 0.048, 0.03),(-0.062, 0.095, 0.00)),
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
            if co.z < 1.38:
                obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 1.42:
                t = (co.z - 1.38) / 0.04
                obj.vertex_groups["Neck"].add([v.index], 1.0 - t, 'REPLACE')
                obj.vertex_groups["Head"].add([v.index], t, 'REPLACE')
            else:
                obj.vertex_groups["Head"].add([v.index], 1.0, 'REPLACE')
        else:
            ax = abs(co.x)
            # 1. BRAZOS Y MANGAS (ax > 0.165)
            if ax > 0.165 and co.z < 1.35 and co.z >= 0.70:
                side = ".L" if co.x > 0 else ".R"
                if co.z < 0.90:
                    obj.vertex_groups["Hand" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.94:
                    t = (co.z - 0.90) / 0.04
                    obj.vertex_groups["Hand" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Forearm" + side].add([v.index], t, 'REPLACE')
                elif co.z < 1.10:
                    obj.vertex_groups["Forearm" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.18:
                    t = (co.z - 1.10) / 0.08
                    obj.vertex_groups["Forearm" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["UpperArm" + side].add([v.index], t, 'REPLACE')
                else:
                    # Zona deltoides/hombrera (Z >= 1.18)
                    if ax > 0.190:
                        obj.vertex_groups["UpperArm" + side].add([v.index], 1.0, 'REPLACE')
                    else:
                        t = (ax - 0.165) / 0.025
                        obj.vertex_groups["Shoulder" + side].add([v.index], 1.0 - t, 'REPLACE')
                        obj.vertex_groups["UpperArm" + side].add([v.index], t, 'REPLACE')

            # 2. HOMBRO INTERIOR / CLAVÍCULA / HOMBRERA BASE
            elif ax > 0.120 and co.z >= 1.20:
                side = ".L" if co.x > 0 else ".R"
                t = (ax - 0.120) / 0.045
                obj.vertex_groups["Chest"].add([v.index], 1.0 - t, 'REPLACE')
                obj.vertex_groups["Shoulder" + side].add([v.index], t, 'REPLACE')

            # 3. PIERNAS Y PANTALÓN
            elif co.z < 0.74:
                side = ".L" if co.x > 0 else ".R"
                if co.z < 0.035 and co.y > 0.04:
                    obj.vertex_groups["Toes" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.10:
                    obj.vertex_groups["Foot" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.14:
                    t = (co.z - 0.10) / 0.04
                    obj.vertex_groups["Foot" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["LowerLeg" + side].add([v.index], t, 'REPLACE')
                elif co.z < 0.40:
                    obj.vertex_groups["LowerLeg" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.48:
                    t = (co.z - 0.40) / 0.08
                    obj.vertex_groups["LowerLeg" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["UpperLeg" + side].add([v.index], t, 'REPLACE')
                else:
                    obj.vertex_groups["UpperLeg" + side].add([v.index], 1.0, 'REPLACE')

            # 4. TORSO, CAMISA Y SACO
            else:
                if co.z < 0.88:
                    obj.vertex_groups["Hips"].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.10:
                    t = (co.z - 0.88) / 0.22
                    obj.vertex_groups["Hips"].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Spine"].add([v.index], t, 'REPLACE')
                elif co.z < 1.28:
                    t = (co.z - 1.10) / 0.18
                    obj.vertex_groups["Spine"].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Chest"].add([v.index], t, 'REPLACE')
                elif co.z < 1.34:
                    t = (co.z - 1.28) / 0.06
                    obj.vertex_groups["Chest"].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Neck"].add([v.index], t, 'REPLACE')
                else:
                    obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')

def attach_armature(obj, arm_obj):
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj
    obj.parent = arm_obj

# =============================================================================
# 4. RENDERS DE VALIDACIÓN Y CONTROL (TARJETA Y CUERPO COMPLETO)
# =============================================================================
def render_control_views(arm_obj):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 36

    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')

    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)

    # Pose de Astorga idéntica a scratch/humans/astorga.png:
    arm_obj.pose.bones['Chest'].rotation_euler = (math.radians(-2), math.radians(-5), math.radians(2))
    arm_obj.pose.bones['Head'].rotation_euler = (math.radians(-2), math.radians(6), math.radians(2))

    # BRAZO IZQUIERDO (Arco): hombro estructurado con cero colapso
    arm_obj.pose.bones['Shoulder.L'].rotation_euler = (math.radians(2), math.radians(-1), math.radians(2))
    arm_obj.pose.bones['UpperArm.L'].rotation_euler = (math.radians(18), math.radians(-4), math.radians(8))
    arm_obj.pose.bones['Forearm.L'].rotation_euler = (math.radians(50), math.radians(-6), math.radians(6))
    arm_obj.pose.bones['Hand.L'].rotation_euler = (math.radians(22), math.radians(10), math.radians(-8))

    # BRAZO DERECHO (Violín): antebrazo flexionado, mano abrazando el mástil
    arm_obj.pose.bones['UpperArm.R'].rotation_euler = (math.radians(32), math.radians(14), math.radians(-26))
    arm_obj.pose.bones['Forearm.R'].rotation_euler = (math.radians(94), math.radians(14), math.radians(-8))
    arm_obj.pose.bones['Hand.R'].rotation_euler = (math.radians(22), math.radians(-16), math.radians(40))

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()

    hand_l_mat = arm_obj.matrix_world @ arm_obj.pose.bones['Hand.L'].matrix
    hand_r_mat = arm_obj.matrix_world @ arm_obj.pose.bones['Hand.R'].matrix
    hand_l_loc = hand_l_mat.to_translation()
    hand_r_loc = hand_r_mat.to_translation()

    # Cargar y posicionar Violín y Arco
    if os.path.exists(VIOLIN_BLEND):
        with bpy.data.libraries.load(VIOLIN_BLEND, link=False) as (data_from, data_to):
            data_to.objects = [o for o in data_from.objects if o in ("Violin_Prop", "Violin_Bow")]
        for o in data_to.objects:
            if o:
                scene.collection.objects.link(o)
                for p in o.data.polygons: p.use_smooth = True
                if o.name == "Violin_Prop":
                    o.scale = (0.76, 0.76, 0.76)
                    # VIOLÍN: Colocado con precisión de contacto exacto sobre Hand.R
                    # Mástil cruzando exactamente entre el pulgar y las falanges que lo abrazan
                    o.rotation_euler = Euler((math.radians(-76), math.radians(172), math.radians(18)), 'XYZ')
                    # Offset de contacto absoluto:
                    o.location = Vector((hand_r_loc.x + 0.004, hand_r_loc.y + 0.016, hand_r_loc.z - 0.205))
                elif o.name == "Violin_Bow":
                    o.scale = (0.70, 0.70, 0.70)
                    # ARCO: Atraviesa directamente el puño de Hand.L
                    o.rotation_euler = Euler((math.radians(26), math.radians(-4), math.radians(-18)), 'XYZ')
                    o.location = Vector((hand_l_loc.x - 0.001, hand_l_loc.y + 0.016, hand_l_loc.z - 0.022))

    for l in [o for o in scene.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(l, do_unlink=True)

    def add_l(name, en, loc, col=(1.0, 0.98, 0.95), size=1.5):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = en
        ld.color = col
        ld.size = size
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        scene.collection.objects.link(lo)

    head_t = (0.0, 0.0, 1.48)
    chest_t = (0.0, 0.0, 1.20)
    add_l("KeyWarm",    140.0, ( 0.6, 1.8, 1.6), (1.0, 0.96, 0.92), size=1.6)
    add_l("FillFront",   70.0, (-0.8, 1.7, 1.4), (0.94, 0.96, 1.0),  size=2.2)
    add_l("RimBack",    100.0, ( 0.1, -1.5, 1.7), (1.0, 0.98, 0.95), size=1.5)
    add_l("ViolinLight", 60.0, (-0.45, 1.7, 1.28), (1.0, 0.95, 0.88), size=1.0)

    cam_data = bpy.data.cameras.new("CamAstorga")
    cam = bpy.data.objects.new("CamAstorga", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    # 1. Render de Tarjeta / Retrato (1024x1024)
    cam_data.lens = 72.0
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    cam.location = Vector((0.0, 2.15, 1.24))
    target = Vector((0.0, 0.0, 1.21))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()

    out_card = os.path.join(SCRATCH_DIR, "test_layered_portrait.png")
    scene.render.filepath = out_card
    bpy.ops.render.render(write_still=True)
    print("✓ Render de tarjeta/retrato guardado en:", out_card)

    # 2. Render de Cuerpo Completo (800x1200)
    cam_data.lens = 52.0
    cam.location = Vector((0.0, 2.50, 0.96))
    target_fb = Vector((0.0, 0.0, 0.88))
    cam.rotation_euler = (target_fb - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1200

    out_fb = os.path.join(SCRATCH_DIR, "test_layered_fullbody.png")
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

    render_control_views(arm_obj)
    print("✓ Prueba de arquitectura por capas ejecutada con éxito.")

if __name__ == "__main__":
    main()
