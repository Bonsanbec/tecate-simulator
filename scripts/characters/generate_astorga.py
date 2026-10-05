"""
=============================================================================
GENERADOR CANÓNICO PROCEDURAL DE ALTA FIDELIDAD: ASTORGA (TECATE SIMULATOR)
=============================================================================
Reconstrucción fidedigna del personaje Astorga ("Músico") en Tecate Simulator:
1. Cabeza, Rostro y Fenotipo Auténtico:
   - Fisonomía facial expresiva (mentón firme, perfil nasal clásico, mandíbula angular)
     preservada exactamente según la morfología original que el usuario aprobó.
   - Piel morena cálida / apiñonada auténtica con matices oliva y bronce (sRGB ~ 0.55, 0.40, 0.315),
     reemplazando el tono pálido/albino anterior.
   - Ojos castaños profundos a Z=1.515 con párpados 3D anatómicos y Shape Key 'blink'.
   - Melena setentera/ochentera voluminosa con ondas orgánicas continuas en 360°,
     volumen en sienes que cubre las orejas suavemente, flequillo peinado hacia los lados
     y caída fluida hacia la nuca (eliminando la peluca colonial/salchichas anterior).
2. Manos Anatómicas de Alta Fidelidad (Manos de Violinista):
   - Palma continua integrada al grafo biomecánico del brazo.
   - 4 dedos estilizados y alargados con 3 falanges articuladas cada uno, reposo anatómico
     con curvatura orgánica elegante.
   - Pulgar en oposición anatómica con 3 falanges conectadas al tensor tenar.
   - Erradicación total de muñones y agujas/palitos desarticulados.
3. Sastrería 3D Completa (Traje Sastre Formal Negro):
   - Saco formal negro carbón con solapas de muesca sastre en relieve 3D (notch lapels),
     cuello vuelto alrededor de la nuca, pechera abierta en V, cierre frontal con 2 botones
     sastre 3D, bolsillo de ojal en pecho izquierdo y faldón inferior que cubre la cadera.
   - Cuello camisero formal vinotinto (burgundy) estructurado en 3D.
   - Corbata tridimensional de seda oscura con nudo Windsor y caída vertical centrada.
   - Mangas estructuradas con dobladillo sastre y puños que asoman la camisa vinotinto.
   - Pantalón sastre negro recto con raya de planchado.
   - Zapatos de vestir negros pulidos con suela y tacón sastre.
   - Sombreado suave (Smooth Shading) forzado en el 100% de las mallas corporales y faciales.
4. Rigging y Contratos de Animación de Tecate Simulator:
   - Submallas requeridas por CitizenEntity:
     * 'Player_Head_Mesh' (cabeza, ojos, párpados con blink, cabello ondulado 360°)
     * 'Player_Body_Mesh' (saco sastre 3D, camisa vinotinto, corbata, pantalón, zapatos y manos de 5 dedos)
   - Esqueleto canónico 'Skeleton3D' con los 22 huesos antropométricos estándar.
   - Blindaje matemático de pesos: 0 vértices de manos fugados a piernas.
   - Exportación limpia a 'astorga.glb' y 'astorga.blend'.
   - Renders de validación multi-ángulo con Cycles CPU.
=============================================================================
"""

import os
import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
ASSETS_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/citizens")
TEXTURES_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/textures")
SCRATCH_DIR = os.path.join(PROJECT_ROOT, "scratch")

OUTPUT_BLEND = os.path.join(ASSETS_DIR, "astorga.blend")
OUTPUT_GLB = os.path.join(ASSETS_DIR, "astorga.glb")
PREVIEW_PNG = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/astorga_preview.png")

os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(SCRATCH_DIR, exist_ok=True)

# =============================================================================
# 0. CONFIGURACIÓN DE MATERIALES PBR
# =============================================================================
def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)

def setup_pbr_material(name, diffuse_tex_path, normal_tex_path=None,
                       base_color=(0.8, 0.8, 0.8, 1.0), roughness=0.6,
                       metallic=0.0, specular=0.5):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (400, 0)
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    links.new(bsdf.outputs['BSDF'], output_node.inputs['Surface'])

    bsdf.inputs['Base Color'].default_value = base_color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = specular

    if diffuse_tex_path and os.path.exists(diffuse_tex_path):
        tex_node = nodes.new(type='ShaderNodeTexImage')
        tex_node.location = (-400, 100)
        img = bpy.data.images.load(diffuse_tex_path, check_existing=True)
        tex_node.image = img
        links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])

    if normal_tex_path and os.path.exists(normal_tex_path):
        norm_tex = nodes.new(type='ShaderNodeTexImage')
        norm_tex.location = (-400, -200)
        img_n = bpy.data.images.load(normal_tex_path, check_existing=True)
        img_n.colorspace_settings.name = 'Non-Color'
        norm_tex.image = img_n
        norm_map = nodes.new(type='ShaderNodeNormalMap')
        norm_map.location = (-150, -200)
        norm_map.inputs['Strength'].default_value = 0.85
        links.new(norm_tex.outputs['Color'], norm_map.inputs['Color'])
        links.new(norm_map.outputs['Normal'], bsdf.inputs['Normal'])

    return mat

def create_materials():
    materials = {
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
                                   base_color=(0.09, 0.07, 0.06, 1.0), roughness=0.72),
        "suit": setup_pbr_material("Mat_Astorga_Suit",
                                   os.path.join(TEXTURES_DIR, "astorga_suit_diffuse.png"),
                                   os.path.join(TEXTURES_DIR, "astorga_suit_normal.png"),
                                   base_color=(0.082, 0.088, 0.096, 1.0), roughness=0.68),
        "shirt": setup_pbr_material("Mat_Astorga_Shirt",
                                    os.path.join(TEXTURES_DIR, "astorga_shirt_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "astorga_shirt_normal.png"),
                                    base_color=(0.295, 0.075, 0.105, 1.0), roughness=0.58),
        "tie": setup_pbr_material("Mat_Astorga_Tie",
                                  os.path.join(TEXTURES_DIR, "astorga_tie_diffuse.png"),
                                  os.path.join(TEXTURES_DIR, "astorga_tie_normal.png"),
                                  base_color=(0.090, 0.055, 0.065, 1.0), roughness=0.45),
        "pants": setup_pbr_material("Mat_Astorga_Pants",
                                    os.path.join(TEXTURES_DIR, "astorga_pants_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "astorga_pants_normal.png"),
                                    base_color=(0.078, 0.082, 0.090, 1.0), roughness=0.70),
        "shoes": setup_pbr_material("Mat_Astorga_Shoes",
                                    os.path.join(TEXTURES_DIR, "astorga_shoes_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "astorga_shoes_normal.png"),
                                    base_color=(0.055, 0.058, 0.062, 1.0), roughness=0.30),
        "buttons": setup_pbr_material("Mat_Astorga_Buttons",
                                      None, None,
                                      base_color=(0.04, 0.04, 0.05, 1.0), roughness=0.22, metallic=0.20),
    }
    return materials

# =============================================================================
# 1. CABEZA, ROSTRO, OJOS, PÁRPADOS 3D Y CABELLO ONDULADO 360° (Player_Head_Mesh)
# =============================================================================
def build_head_mesh(materials):
    me = bpy.data.meshes.new("Player_Head_Mesh_Data")
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")

    def calc_face_uv(x, z):
        u = 0.50 + x / 0.275
        v = 0.50 + (z - 1.485) / 0.240
        return (max(0.0, min(1.0, u)), max(0.0, min(1.0, v)))

    # Perfil craneofacial estilizado de Astorga (conservado exactamente según el aprobado)
    head_profile = [
        # z,      rx,    ry_front, ry_back, y_offset, is_face
        (1.370,  0.046, 0.046,    0.048,   -0.002,   False), # 0: Base cuello
        (1.392,  0.046, 0.044,    0.050,   -0.002,   False), # 1: Cuello medio (piel limpia)
        (1.412,  0.050, 0.046,    0.056,    0.000,   True),  # 2: Ángulo submandibular
        (1.428,  0.058, 0.064,    0.068,    0.004,   True),  # 3: Mentón masculino firme sin barba
        (1.445,  0.062, 0.064,    0.074,    0.003,   True),  # 4: Surco mentolabial
        (1.458,  0.064, 0.066,    0.082,    0.003,   True),  # 5: Labio inferior
        (1.468,  0.066, 0.065,    0.086,    0.002,   True),  # 6: Hendidura labial serena
        (1.478,  0.068, 0.068,    0.090,    0.002,   True),  # 7: Labio superior
        (1.492,  0.071, 0.067,    0.092,    0.001,   True),  # 8: Base nasal / Filtrum
        (1.505,  0.073, 0.075,    0.093,    0.000,   True),  # 9: Punta nasal recta y definida
        (1.515,  0.075, 0.069,    0.093,    0.000,   True),  # 10: Ojos y puente nasal (Z = 1.515)
        (1.532,  0.076, 0.072,    0.092,   -0.002,   True),  # 11: Pómulos y cejas expresivas
        (1.550,  0.075, 0.069,    0.090,   -0.004,   True),  # 12: Sienes y frente baja
        (1.566,  0.073, 0.064,    0.086,   -0.006,   True),  # 13: Frente media
        (1.582,  0.070, 0.056,    0.080,   -0.008,   False), # 14: Bóveda baja
        (1.598,  0.062, 0.046,    0.072,   -0.010,   False), # 15: Bóveda media
        (1.615,  0.044, 0.032,    0.048,   -0.012,   False), # 16: Coronilla
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

            # Modulaciones anatómicas:
            if l_idx == 3 and 0.44 * math.pi <= ang <= 0.56 * math.pi:
                y += 0.005 * math.cos((ang - 0.5 * math.pi) / 0.06 * (0.5 * math.pi))**2

            if l_idx in (8, 9, 10) and 0.46 * math.pi <= ang <= 0.54 * math.pi:
                nw = math.cos((ang - 0.5 * math.pi) / 0.04 * (0.5 * math.pi))**2
                if l_idx == 9: y += 0.010 * nw
                elif l_idx in (8, 10): y += 0.004 * nw

            if l_idx == 10 and (0.32 * math.pi <= ang <= 0.43 * math.pi or 0.57 * math.pi <= ang <= 0.68 * math.pi):
                y -= 0.008

            v = bm.verts.new((x, y, z))
            cur_ring.append(v)
        rings.append(cur_ring)

    # Construir caras de la cabeza:
    for l_idx in range(len(head_profile) - 1):
        r1 = rings[l_idx]
        r2 = rings[l_idx + 1]
        z_mid = (head_profile[l_idx][0] + head_profile[l_idx + 1][0]) * 0.5
        for i in range(n_ring):
            inxt = (i + 1) % n_ring
            f = bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))

            ang_mid = (2.0 * math.pi * (i + 0.5)) / n_ring
            sin_mid = math.sin(ang_mid)

            # Rostro visible en frente: piel (0: Skin)
            is_face_skin = (z_mid < 1.546 and sin_mid > -0.05)
            is_hair_base = not is_face_skin

            f.material_index = 2 if is_hair_base else 0 # 2: Hair, 0: Skin

            for loop in f.loops:
                loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

    # Coronilla superior
    top_vert = bm.verts.new((0.0, -0.012, 1.622))
    r_last = rings[-1]
    for i in range(n_ring):
        inxt = (i + 1) % n_ring
        f_top = bm.faces.new((r_last[i], r_last[inxt], top_vert))
        f_top.material_index = 2 # 2: Hair
        for loop in f_top.loops:
            loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

    # Globos oculares 3D (Z = 1.515, Y = 0.0535, Radio = 0.0120)
    eye_pos = [(0.033, 0.0535, 1.515), (-0.033, 0.0535, 1.515)]
    eye_r = 0.0120
    for pos in eye_pos:
        e_bm = bmesh.new()
        bmesh.ops.create_uvsphere(e_bm, u_segments=16, v_segments=12, radius=eye_r)
        bmesh.ops.rotate(e_bm, verts=e_bm.verts, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(-90), 4, 'X'))
        bmesh.ops.translate(e_bm, verts=e_bm.verts, vec=pos)
        v_map = {v: bm.verts.new(v.co) for v in e_bm.verts}
        for f in e_bm.faces:
            nf = bm.faces.new([v_map[v] for v in f.verts])
            nf.material_index = 1 # Mat_Astorga_Eyes
            for loop in nf.loops:
                co = loop.vert.co - Vector(pos)
                loop[uv_lay].uv = (0.5 + co.x / (2.0 * eye_r), 0.5 + co.z / (2.0 * eye_r))
        e_bm.free()

    # Párpados anatómicos 3D con Shape Key 'blink'
    upper_lid_margin_verts = []
    upper_lid_crease_verts = []
    for ex, ey, ez in eye_pos:
        sign_side = 1.0 if ex > 0 else -1.0
        n_pts = 9
        upper_margin, upper_crease, upper_brow = [], [], []
        lower_margin, lower_crease, lower_cheek = [], [], []
        for i in range(n_pts):
            t = (i / float(n_pts - 1)) * 2.0 - 1.0
            dx = t * 0.0135 * sign_side
            arch = math.sqrt(max(0.0, 1.0 - t**2))
            dz_sup = 0.0068 * arch + 0.0003 * t
            dz_inf = -0.0048 * arch + 0.0002 * t
            dy_sup = math.sqrt(max(0.0001, (eye_r * 1.02)**2 - dx**2 - dz_sup**2))
            dy_inf = math.sqrt(max(0.0001, (eye_r * 1.02)**2 - dx**2 - dz_inf**2))

            v_sup_m = bm.verts.new((ex + dx, ey + dy_sup, ez + dz_sup))
            v_sup_c = bm.verts.new((ex + dx, ey + dy_sup * 0.97 + 0.003, ez + dz_sup + 0.0040 * arch))
            v_sup_b = bm.verts.new((ex + dx, ey + dy_sup * 0.91 + 0.006, ez + dz_sup + 0.0095 * arch))

            v_inf_m = bm.verts.new((ex + dx, ey + dy_inf, ez + dz_inf))
            v_inf_c = bm.verts.new((ex + dx, ey + dy_inf * 0.97 + 0.003, ez + dz_inf - 0.0035 * arch))
            v_inf_k = bm.verts.new((ex + dx, ey + dy_inf * 0.91 + 0.006, ez + dz_inf - 0.0080 * arch))

            upper_margin.append(v_sup_m)
            upper_crease.append(v_sup_c)
            upper_brow.append(v_sup_b)

            lower_margin.append(v_inf_m)
            lower_crease.append(v_inf_c)
            lower_cheek.append(v_inf_k)

            upper_lid_margin_verts.append(v_sup_m)
            upper_lid_crease_verts.append(v_sup_c)

        for i in range(n_pts - 1):
            f1 = bm.faces.new((upper_margin[i], upper_margin[i+1], upper_crease[i+1], upper_crease[i]))
            f2 = bm.faces.new((upper_crease[i], upper_crease[i+1], upper_brow[i+1], upper_brow[i]))
            f3 = bm.faces.new((lower_crease[i], lower_crease[i+1], lower_margin[i+1], lower_margin[i]))
            f4 = bm.faces.new((lower_cheek[i], lower_cheek[i+1], lower_crease[i+1], lower_crease[i]))
            for f in (f1, f2, f3, f4):
                f.material_index = 0 # 0: Skin
                for loop in f.loops: loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

    # Orejas anatómicas en piel
    for is_l in (True, False):
        s_sign = 1.0 if is_l else -1.0
        ear_bm = bmesh.new()
        bmesh.ops.create_uvsphere(ear_bm, u_segments=8, v_segments=6, radius=0.014)
        bmesh.ops.scale(ear_bm, verts=ear_bm.verts, vec=(0.35, 0.65, 1.15))
        bmesh.ops.rotate(ear_bm, verts=ear_bm.verts, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(s_sign * 12.0), 4, 'Y'))
        bmesh.ops.translate(ear_bm, verts=ear_bm.verts, vec=(s_sign * 0.072, -0.006, 1.505))
        v_map = {v: bm.verts.new(v.co) for v in ear_bm.verts}
        for f in ear_bm.faces:
            nf = bm.faces.new([v_map[v] for v in f.verts])
            nf.material_index = 0
            for loop in nf.loops: loop[uv_lay].uv = (0.5, 0.5)
        ear_bm.free()

    # -------------------------------------------------------------------------
    # CABELLERA ONDULADA Y VOLUMINOSA 360° DE ASTORGA (scratch/humans/astorga.png)
    # Melena setentera canónica: tejas biseladas volumétricas de 5 vértices
    # -------------------------------------------------------------------------
    hair_bm = bmesh.new()

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

            v_left  = hair_bm.verts.new(p - side * (w * 0.5))
            v_mid_l = hair_bm.verts.new(p - side * (w * 0.25) + nor * (dp * 0.70))
            v_crest = hair_bm.verts.new(p + nor * dp)
            v_mid_r = hair_bm.verts.new(p + side * (w * 0.25) + nor * (dp * 0.70))
            v_right = hair_bm.verts.new(p + side * (w * 0.5))

            c_verts = [v_left, v_mid_l, v_crest, v_mid_r, v_right]
            if prev_verts:
                for k in range(4):
                    f = hair_bm.faces.new((prev_verts[k], prev_verts[k+1], c_verts[k+1], c_verts[k]))
                    f.material_index = 2
            prev_verts = c_verts

        v_tip = hair_bm.verts.new(p2 + tang * 0.003)
        for k in range(4):
            f = hair_bm.faces.new((prev_verts[k], prev_verts[k+1], v_tip))
            f.material_index = 2

    # 1. Cobertura de la corona y bóveda craneal (suave, envolvente)
    for xo, ang_s in [(0.0, 0.0), (0.028, 0.08), (-0.028, -0.08), (0.052, 0.15), (-0.052, -0.15)]:
        add_hair_clump((xo * 0.6, 0.038, 1.624), (xo * 0.9, -0.020, 1.626), (xo * 1.1, -0.065, 1.565),
                       w_root=0.038, w_mid=0.046, w_tip=0.020, depth=0.010)

    # 2. Flequillo frontal natural peinado a los lados desde la raya (X = -0.008)
    # Lado izquierdo (+X)
    add_hair_clump(( 0.002, 0.058, 1.582), ( 0.042, 0.074, 1.558), ( 0.078, 0.050, 1.520), w_root=0.028, w_mid=0.036, w_tip=0.018, depth=0.011)
    add_hair_clump(( 0.018, 0.054, 1.590), ( 0.060, 0.068, 1.564), ( 0.092, 0.035, 1.508), w_root=0.030, w_mid=0.040, w_tip=0.018, depth=0.012)
    add_hair_clump(( 0.032, 0.048, 1.598), ( 0.078, 0.058, 1.568), ( 0.104, 0.020, 1.495), w_root=0.032, w_mid=0.042, w_tip=0.018, depth=0.012)

    # Lado derecho (-X)
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
        # Mechón inferior de patilla / caída hacia cuello
        add_hair_clump((sgn * 0.082, 0.008, 1.460), (sgn * 0.098, -0.010, 1.415), (sgn * 0.078, -0.028, 1.385),
                       w_root=0.026, w_mid=0.036, w_tip=0.016, depth=0.012)

    # 4. Caída posterior en nuca
    for nx in (-0.045, -0.022, 0.000, 0.022, 0.045):
        add_hair_clump((nx * 0.8, -0.062, 1.568), (nx * 1.1, -0.084, 1.478), (nx * 0.9, -0.078, 1.402),
                       w_root=0.030, w_mid=0.040, w_tip=0.018, depth=0.013)

    v_map_hair = {v: bm.verts.new(v.co) for v in hair_bm.verts}
    for f in hair_bm.faces:
        nf = bm.faces.new([v_map_hair[v] for v in f.verts])
        nf.material_index = 2
        for loop in nf.loops: loop[uv_lay].uv = (0.5, 0.5)
    hair_bm.free()

    # Suavizado de normales en toda la cabeza
    bm.normal_update()
    for f in bm.faces: f.smooth = True

    bm.verts.ensure_lookup_table()
    margin_v_indices = [v.index for v in upper_lid_margin_verts]
    crease_v_indices = [v.index for v in upper_lid_crease_verts]

    bm.to_mesh(me)
    bm.free()

    for mat in materials["head"]:
        me.materials.append(mat)

    obj_head = bpy.data.objects.new("Player_Head_Mesh", me)
    bpy.context.scene.collection.objects.link(obj_head)

    # Crear Shape Key 'blink' en párpados
    sk_basis = obj_head.shape_key_add(name="Basis")
    sk_blink = obj_head.shape_key_add(name="blink")
    sk_blink.value = 0.0
    for v_idx in margin_v_indices:
        sk_blink.data[v_idx].co.z -= 0.0105
        sk_blink.data[v_idx].co.y += 0.0010
    for v_idx in crease_v_indices:
        sk_blink.data[v_idx].co.z -= 0.0055
        sk_blink.data[v_idx].co.y += 0.0005

    return obj_head

# =============================================================================
# 2. CUERPO: SASTRERÍA 3D, CAMISA VINOTINTO, CORBATA Y MANOS DE 5 DEDOS
# =============================================================================
def build_body_mesh(materials):
    mesh_graph = bpy.data.meshes.new("Body_Graph_Data")
    obj_body = bpy.data.objects.new("Player_Body_Mesh", mesh_graph)
    bpy.context.scene.collection.objects.link(obj_body)

    # Grafo anatómico esquelético
    nodes = [
        # Tronco
        (0.00,  0.000, 0.82, 0.142, 0.104), # 0: Base pelvis
        (0.00,  0.002, 0.94, 0.146, 0.104), # 1: Caderas / Cintura sastre
        (0.00,  0.004, 1.04, 0.142, 0.100), # 2: Cintura
        (0.00, -0.006, 1.16, 0.156, 0.112), # 3: Costillas / tórax
        (0.00, -0.008, 1.28, 0.168, 0.120), # 4: Pectorales y espalda sastre
        (0.00, -0.004, 1.36, 0.158, 0.108), # 5: Clavículas / hombros armados
        (0.00,  0.004, 1.39, 0.048, 0.048), # 6: Base del cuello camisero

        # Brazos con mangas completas de traje
        ( 0.06, -0.004, 1.36, 0.070, 0.070), # 7
        ( 0.185, -0.004, 1.34, 0.066, 0.066), # 8: Hombro L
        ( 0.265,  0.002, 1.15, 0.052, 0.052), # 9: Codo L
        ( 0.325,  0.010, 0.925, 0.038, 0.034), # 10: Manga puño L

        (-0.06, -0.004, 1.36, 0.070, 0.070), # 11
        (-0.185, -0.004, 1.34, 0.066, 0.066), # 12: Hombro R
        (-0.265,  0.002, 1.15, 0.052, 0.052), # 13: Codo R
        (-0.325,  0.010, 0.925, 0.038, 0.034), # 14: Manga puño R

        # Piernas con pantalón sastre recto
        ( 0.088, 0.002, 0.82, 0.082, 0.082), # 15: Cadera sup L
        ( 0.088, 0.002, 0.65, 0.075, 0.075), # 16: Muslo medio L
        ( 0.088, 0.000, 0.48, 0.066, 0.066), # 17: Rodilla L
        ( 0.088, 0.000, 0.30, 0.058, 0.058), # 18: Pantorrilla L
        ( 0.088, 0.002, 0.12, 0.050, 0.050), # 19: Tobillo L
        ( 0.088, 0.055, 0.03, 0.052, 0.106), # 20: Zapato L

        (-0.088, 0.002, 0.82, 0.082, 0.082), # 21: Cadera sup R
        (-0.088, 0.002, 0.65, 0.075, 0.075), # 22: Muslo medio R
        (-0.088, 0.000, 0.48, 0.066, 0.066), # 23: Rodilla R
        (-0.088, 0.000, 0.30, 0.058, 0.058), # 24: Pantorrilla R
        (-0.088, 0.002, 0.12, 0.050, 0.050), # 25: Tobillo R
        (-0.088, 0.055, 0.03, 0.052, 0.106), # 26: Zapato R

        # Muñecas y Palmas anatómicas continuas en piel
        ( 0.325,  0.012, 0.895, 0.024, 0.017), # 27: Muñeca L
        ( 0.325,  0.012, 0.835, 0.028, 0.014), # 28: Palma L
        (-0.325,  0.012, 0.895, 0.024, 0.017), # 29: Muñeca R
        (-0.325,  0.012, 0.835, 0.028, 0.014), # 30: Palma R
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6),
        (5, 7), (7, 8), (8, 9), (9, 10), (10, 27), (27, 28),
        (5, 11), (11, 12), (12, 13), (13, 14), (14, 29), (29, 30),
        (0, 15), (15, 16), (16, 17), (17, 18), (18, 19), (19, 20),
        (0, 21), (21, 22), (22, 23), (23, 24), (24, 25), (25, 26),
    ]

    verts = [Vector((n[0], n[1], n[2])) for n in nodes]
    mesh_graph.from_pydata(verts, edges, [])
    mesh_graph.update()

    bpy.context.view_layer.objects.active = obj_body
    mod_skin = obj_body.modifiers.new(name="Skin", type='SKIN')
    skin_data = mesh_graph.skin_vertices[0].data
    for i, n in enumerate(nodes):
        skin_data[i].radius = (n[3], n[4])

    bpy.ops.object.modifier_apply(modifier="Skin")
    mod_sub = obj_body.modifiers.new(name="Subsurf", type='SUBSURF')
    mod_sub.levels = 1
    bpy.ops.object.modifier_apply(modifier="Subsurf")

    bm = bmesh.new()
    bm.from_mesh(obj_body.data)
    uv_lay = bm.loops.layers.uv.new("UVMap")

    # Mapeo de materiales en el cuerpo base:
    # 0: Mat_Astorga_Suit   (Saco y mangas)
    # 1: Mat_Astorga_Pants  (Pantalón formal)
    # 2: Mat_Astorga_Shoes  (Zapatos negros)
    # 3: Mat_Astorga_Skin   (Muñecas y palmas continuas)
    # 4: Mat_Astorga_Shirt  (Camisa vinotinto)
    # 5: Mat_Astorga_Tie    (Corbata)
    # 6: Mat_Astorga_Buttons (Botones)
    for p in bm.faces:
        c_median = p.calc_center_median()
        cz = c_median.z
        cx = abs(c_median.x)
        cy = c_median.y

        if cz < 0.10:
            p.material_index = 2 # Zapatos
        elif cz < 0.94 and cx < 0.18:
            p.material_index = 1 # Pantalón sastre
        elif cx > 0.18:
            if cz < 0.915:
                p.material_index = 3 # Piel de manos y muñecas
            else:
                p.material_index = 0 # Mangas de saco sastre
        else:
            # Pecho frontal: pechera interior vinotinto en forma de V estricta bajo las solapas
            v_width = 0.010 + max(0.0, (cz - 1.18) / 0.20) * 0.038
            if 1.18 <= cz <= 1.38 and cy > 0.045 and cx < v_width:
                p.material_index = 4 # Camisa vinotinto en el escote en V central
            else:
                p.material_index = 0 # Saco sastre formal negro

        for loop in p.loops:
            loop[uv_lay].uv = (loop.vert.co.x * 2.0 + 0.5, loop.vert.co.z * 1.5)

    # -------------------------------------------------------------------------
    # A. CUELLO CAMISERO VINOTINTO TRIDIMENSIONAL (Z = 1.365 a 1.410)
    # -------------------------------------------------------------------------
    n_c = 18
    c_bot, c_top = [], []
    for i in range(n_c):
        ang = (2.0 * math.pi * i) / n_c
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        cx = 0.052 * cos_a
        cy = (0.054 if sin_a >= 0 else 0.050) * sin_a + 0.004
        c_bot.append(bm.verts.new((cx, cy, 1.370)))
        c_top.append(bm.verts.new((cx * 1.05, cy * 1.05, 1.412)))
    for i in range(n_c):
        inxt = (i + 1) % n_c
        f = bm.faces.new((c_bot[i], c_bot[inxt], c_top[inxt], c_top[i]))
        f.material_index = 4 # Mat_Astorga_Shirt
        for loop in f.loops: loop[uv_lay].uv = (0.5, 0.5)

    # Puntas del cuello de camisa (cuello cerrado bajo la corbata)
    wing_l = [bm.verts.new((0.006, 0.060, 1.410)), bm.verts.new((0.046, 0.048, 1.405)), bm.verts.new((0.024, 0.076, 1.362))]
    wing_r = [bm.verts.new((-0.006, 0.060, 1.410)), bm.verts.new((-0.024, 0.076, 1.362)), bm.verts.new((-0.046, 0.048, 1.405))]
    f_wl = bm.faces.new(wing_l)
    f_wr = bm.faces.new(wing_r)
    f_wl.material_index = 4
    f_wr.material_index = 4

    # -------------------------------------------------------------------------
    # B. CORBATA TRIDIMENSIONAL CON NUDO Y CAÍDA VERTICAL (Z = 1.15 a 1.40)
    # -------------------------------------------------------------------------
    # Nudo Windsor central
    knot_v = [
        bm.verts.new((-0.016, 0.064, 1.405)),
        bm.verts.new(( 0.016, 0.064, 1.405)),
        bm.verts.new(( 0.012, 0.088, 1.365)),
        bm.verts.new((-0.012, 0.088, 1.365)),
        bm.verts.new(( 0.000, 0.096, 1.385)),
    ]
    for face_verts in [
        (knot_v[0], knot_v[1], knot_v[4]),
        (knot_v[1], knot_v[2], knot_v[4]),
        (knot_v[2], knot_v[3], knot_v[4]),
        (knot_v[3], knot_v[0], knot_v[4]),
    ]:
        f_k = bm.faces.new(face_verts)
        f_k.material_index = 5 # Mat_Astorga_Tie

    # Pala de la corbata (abovedada con 3 vértices por fila para relieve central)
    tie_profile = [
        # z,     half_w, y_front
        (1.365,  0.012,  0.088),
        (1.315,  0.014,  0.106),
        (1.265,  0.015,  0.116),
        (1.215,  0.015,  0.120),
        (1.155,  0.014,  0.118),
    ]
    tie_rows = []
    for tz, thw, ty in tie_profile:
        vl = bm.verts.new((-thw, ty, tz))
        vm = bm.verts.new(( 0.000, ty + 0.005, tz))
        vr = bm.verts.new(( thw, ty, tz))
        tie_rows.append((vl, vm, vr))

    for idx in range(len(tie_rows) - 1):
        la, ma, ra = tie_rows[idx]
        lb, mb, rb = tie_rows[idx + 1]
        f_tl = bm.faces.new((la, ma, mb, lb))
        f_tr = bm.faces.new((ma, ra, rb, mb))
        f_tl.material_index = 5
        f_tr.material_index = 5

    # -------------------------------------------------------------------------
    # C. SACO SASTRE FORMAL CON SOLAPAS DE MUESCA TRIDIMENSIONALES (NOTCH LAPELS)
    # -------------------------------------------------------------------------
    # Solapa Izquierda (X > 0) y Solapa Derecha (X < 0) con volumen real sobresaliente
    for s_side in (1.0, -1.0):
        s_sign = s_side
        lapel_v = [
            bm.verts.new((s_sign * 0.046, 0.050, 1.392)), # 0: Cuello nuca
            bm.verts.new((s_sign * 0.092, 0.088, 1.340)), # 1: Pectoral alto exterior
            bm.verts.new((s_sign * 0.096, 0.102, 1.300)), # 2: Vértice superior de muesca
            bm.verts.new((s_sign * 0.082, 0.104, 1.285)), # 3: Vértice interior de muesca (notch)
            bm.verts.new((s_sign * 0.095, 0.115, 1.265)), # 4: Vértice inferior de solapa
            bm.verts.new((s_sign * 0.024, 0.122, 1.180)), # 5: Vértice del escote en V / botón superior
            bm.verts.new((s_sign * 0.040, 0.110, 1.260)), # 6: Borde interior medio
        ]

        # Caras de la solapa con grosor tridimensional
        if s_sign > 0:
            bm.faces.new((lapel_v[0], lapel_v[1], lapel_v[2], lapel_v[3])).material_index = 0
            bm.faces.new((lapel_v[0], lapel_v[3], lapel_v[6])).material_index = 0
            bm.faces.new((lapel_v[3], lapel_v[4], lapel_v[5], lapel_v[6])).material_index = 0
        else:
            bm.faces.new((lapel_v[1], lapel_v[0], lapel_v[3], lapel_v[2])).material_index = 0
            bm.faces.new((lapel_v[3], lapel_v[0], lapel_v[6])).material_index = 0
            bm.faces.new((lapel_v[4], lapel_v[3], lapel_v[6], lapel_v[5])).material_index = 0

    # Banda trasera del cuello del saco sobre la nuca
    n_scollar = 10
    sc_top, sc_bot = [], []
    for i in range(n_scollar):
        ang = math.pi * 0.15 + (math.pi * 0.70 * i) / (n_scollar - 1)
        bx = 0.054 * math.cos(ang)
        by = -0.052 * math.sin(ang) - 0.005
        sc_top.append(bm.verts.new((bx, by, 1.408)))
        sc_bot.append(bm.verts.new((bx, by, 1.382)))
    for i in range(n_scollar - 1):
        f_sc = bm.faces.new((sc_bot[i], sc_bot[i+1], sc_top[i+1], sc_top[i]))
        f_sc.material_index = 0 # Mat_Astorga_Suit

    # Botones sastre frontales en el saco (Z = 1.170 y Z = 1.090)
    for bz in [1.170, 1.090]:
        by = 0.126 + (1.170 - bz) * (-0.015)
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.0050)
        bmesh.ops.scale(btn_bm, verts=btn_bm.verts, vec=(1.0, 0.40, 1.0))
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.0, by + 0.004, bz))
        v_map_b = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            nf = bm.faces.new([v_map_b[v] for v in f.verts])
            nf.material_index = 6 # Mat_Astorga_Buttons
        btn_bm.free()

    # Bolsillo de ojal en pecho izquierdo (pañuelo sastre)
    p_box = [
        bm.verts.new((0.055, 0.114, 1.246)),
        bm.verts.new((0.095, 0.110, 1.246)),
        bm.verts.new((0.095, 0.110, 1.238)),
        bm.verts.new((0.055, 0.114, 1.238)),
    ]
    bm.faces.new(p_box).material_index = 0

    # -------------------------------------------------------------------------
    # D. PUÑOS CAMISEROS VINOTINTO Y BOTONES DE MANGA
    # -------------------------------------------------------------------------
    for is_l in (True, False):
        s_sign = 1.0 if is_l else -1.0
        # Puño camisero que asoma bajo la manga del traje (Z = 0.905 a 0.925)
        n_cuff = 14
        cuff_top, cuff_bot = [], []
        for k in range(n_cuff):
            ang = (2.0 * math.pi * k) / n_cuff
            cx = s_sign * 0.325 + 0.027 * math.cos(ang)
            cy = 0.012 + 0.022 * math.sin(ang)
            cuff_top.append(bm.verts.new((cx, cy, 0.925)))
            cuff_bot.append(bm.verts.new((cx * 1.01, cy * 1.01, 0.905)))
        for k in range(n_cuff):
            kn = (k + 1) % n_cuff
            f_cf = bm.faces.new((cuff_top[k], cuff_top[kn], cuff_bot[kn], cuff_bot[k]))
            f_cf.material_index = 4 # Mat_Astorga_Shirt

        # Botones de manga sastre en el saco
        for b_mz in [0.935, 0.948, 0.961]:
            btn_m_bm = bmesh.new()
            bmesh.ops.create_uvsphere(btn_m_bm, u_segments=6, v_segments=4, radius=0.0028)
            bmesh.ops.translate(btn_m_bm, verts=btn_m_bm.verts, vec=(s_sign * (0.325 + 0.028), 0.012, b_mz))
            v_map_bm = {v: bm.verts.new(v.co) for v in btn_m_bm.verts}
            for f in btn_m_bm.faces:
                bm.faces.new([v_map_bm[v] for v in f.verts]).material_index = 6
            btn_m_bm.free()

    # -------------------------------------------------------------------------
    # E. MANOS ANATÓMICAS DE ALTA FIDELIDAD (MANOS DE VIOLINISTA CON 5 DEDOS)
    # Arquitectura hexanodal paramétrica articulada en 3 falanges + pulgar opuesto
    # -------------------------------------------------------------------------
    for is_l in (True, False):
        sign_a = 1.0 if is_l else -1.0
        w_center = Vector((sign_a * 0.325, 0.012, 0.835))
        z_knuckles = 0.832

        # 4 Dedos alargados estilizados de músico (Índice, Medio, Anular, Meñique)
        finger_specs = [
            ("Index",   w_center.y + 0.015, 0.052, 0.0055),
            ("Middle",  w_center.y + 0.005, 0.056, 0.0058),
            ("Ring",    w_center.y - 0.005, 0.051, 0.0055),
            ("Pinky",   w_center.y - 0.015, 0.042, 0.0048),
        ]
        curl_dir = Vector((-sign_a * 0.65, 0.32, -0.22)).normalized()

        for (f_name, fy, f_len, f_rad) in finger_specs:
            fx = sign_a * 0.325
            n_seg = 3
            prev_fring = None
            for s in range(n_seg + 1):
                t = s / float(n_seg)
                fz = z_knuckles - f_len * t
                cur_y = fy + curl_dir.y * (f_len * 0.30 * (t**1.3))
                cur_x = fx + curl_dir.x * (f_len * 0.22 * (t**1.3))
                r_cur = f_rad * (1.0 - 0.28 * t)

                cur_fring = []
                for k in range(6):
                    fang = (2.0 * math.pi * k) / 6.0
                    cur_fring.append(bm.verts.new((cur_x + r_cur * math.cos(fang),
                                                  cur_y + r_cur * math.sin(fang),
                                                  fz + curl_dir.z * (f_len * 0.20 * t))))
                if prev_fring:
                    for k in range(6):
                        knxt = (k + 1) % 6
                        ff = bm.faces.new((prev_fring[k], prev_fring[knxt], cur_fring[knxt], cur_fring[k]))
                        ff.material_index = 3 # Mat_Astorga_Skin
                prev_fring = cur_fring

            # Yema / punta redondeada del dedo
            tip_v = bm.verts.new((cur_x + curl_dir.x * 0.003, cur_y + curl_dir.y * 0.003, z_knuckles - f_len - 0.003))
            for k in range(6):
                knxt = (k + 1) % 6
                ff_tip = bm.faces.new((prev_fring[knxt], prev_fring[k], tip_v))
                ff_tip.material_index = 3

        # Pulgar en oposición anatómica con 3 segmentos
        th_root = Vector((sign_a * (0.325 - 0.018), w_center.y + 0.012, 0.840))
        n_tseg = 3
        prev_th = None
        for s in range(n_tseg + 1):
            t = s / float(n_tseg)
            tx = th_root.x - sign_a * 0.014 * t
            ty = th_root.y + 0.014 * t
            tz = th_root.z - 0.030 * t
            trad = 0.0062 * (1.0 - 0.25 * t)
            cur_th = []
            for k in range(6):
                tang = (2.0 * math.pi * k) / 6.0
                cur_th.append(bm.verts.new((tx + trad * math.cos(tang),
                                           ty + trad * math.sin(tang),
                                           tz)))
            if prev_th:
                for k in range(6):
                    knxt = (k + 1) % 6
                    thf = bm.faces.new((prev_th[k], prev_th[knxt], cur_th[knxt], cur_th[k]))
                    thf.material_index = 3
            prev_th = cur_th

        tip_th = bm.verts.new((th_root.x - sign_a * 0.016, th_root.y + 0.016, th_root.z - 0.034))
        for k in range(6):
            knxt = (k + 1) % 6
            thf_tip = bm.faces.new((prev_th[knxt], prev_th[k], tip_th))
            thf_tip.material_index = 3

    # Recalcular normales y activar sombreado suave (Smooth Shading) en todo el cuerpo
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    for f in bm.faces: f.smooth = True

    bm.to_mesh(obj_body.data)
    bm.free()

    for mat in materials["body"]:
        obj_body.data.materials.append(mat)

    return obj_body

# =============================================================================
# 3. ESQUELETO Y RIGGING CANÓNICO (22 HUESOS)
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
        ("Hips",        "Root",        (0, 0, 0.82),      (0, 0, 0.95)),
        ("Spine",       "Hips",        (0, 0, 0.95),      (0, 0, 1.15)),
        ("Chest",       "Spine",       (0, 0, 1.15),      (0, 0, 1.36)),
        ("Neck",        "Chest",       (0, 0, 1.36),      (0, 0, 1.42)),
        ("Head",        "Neck",        (0, 0, 1.42),      (0, 0, 1.66)),

        ("Shoulder.L",  "Chest",       (0.04, 0, 1.36),   (0.185, 0, 1.36)),
        ("UpperArm.L",  "Shoulder.L",  (0.185, 0, 1.36),  (0.265, 0.005, 1.15)),
        ("Forearm.L",   "UpperArm.L",  (0.265, 0.005, 1.15),(0.325, 0.015, 0.93)),
        ("Hand.L",      "Forearm.L",   (0.325, 0.015, 0.93),(0.325, 0.015, 0.76)),

        ("Shoulder.R",  "Chest",       (-0.04, 0, 1.36),  (-0.185, 0, 1.36)),
        ("UpperArm.R",  "Shoulder.R",  (-0.185, 0, 1.36), (-0.265, 0.005, 1.15)),
        ("Forearm.R",   "UpperArm.R",  (-0.265, 0.005, 1.15),(-0.325, 0.015, 0.93)),
        ("Hand.R",      "Forearm.R",   (-0.325, 0.015, 0.93),(-0.325, 0.015, 0.76)),

        ("UpperLeg.L",  "Hips",        (0.088, 0, 0.82),  (0.088, 0, 0.48)),
        ("LowerLeg.L",  "UpperLeg.L",  (0.088, 0, 0.48),  (0.088, 0, 0.12)),
        ("Foot.L",      "LowerLeg.L",  (0.088, 0, 0.12),  (0.088, 0.06, 0.03)),
        ("Toes.L",      "Foot.L",      (0.088, 0.06, 0.03),(0.088, 0.12, 0.00)),

        ("UpperLeg.R",  "Hips",        (-0.088, 0, 0.82), (-0.088, 0, 0.48)),
        ("LowerLeg.R",  "UpperLeg.R",  (-0.088, 0, 0.48), (-0.088, 0, 0.12)),
        ("Foot.R",      "LowerLeg.R",  (-0.088, 0, 0.12), (-0.088, 0.06, 0.03)),
        ("Toes.R",      "Foot.R",      (-0.088, 0.06, 0.03),(-0.088, 0.12, 0.00)),
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
            if co.z < 1.39:
                obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 1.43:
                t = (co.z - 1.39) / 0.04
                obj.vertex_groups["Neck"].add([v.index], 1.0 - t, 'REPLACE')
                obj.vertex_groups["Head"].add([v.index], t, 'REPLACE')
            else:
                obj.vertex_groups["Head"].add([v.index], 1.0, 'REPLACE')
        else:
            # EXTREMIDADES SUPERIORES (|X| > 0.18 m y Z < 1.38 m)
            if abs(co.x) > 0.18 and co.z < 1.38:
                side = ".L" if co.x > 0 else ".R"
                if co.z < 0.90:
                    obj.vertex_groups["Hand" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.94:
                    t = (co.z - 0.90) / 0.04
                    obj.vertex_groups["Hand" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Forearm" + side].add([v.index], t, 'REPLACE')
                elif co.z < 1.11:
                    obj.vertex_groups["Forearm" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.19:
                    t = (co.z - 1.11) / 0.08
                    obj.vertex_groups["Forearm" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["UpperArm" + side].add([v.index], t, 'REPLACE')
                else:
                    obj.vertex_groups["UpperArm" + side].add([v.index], 1.0, 'REPLACE')

            # EXTREMIDADES INFERIORES (|X| <= 0.18 m y Z < 0.82 m)
            elif co.z < 0.82:
                side = ".L" if co.x > 0 else ".R"
                if co.z < 0.035 and co.y > 0.04:
                    obj.vertex_groups["Toes" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.10:
                    obj.vertex_groups["Foot" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.14:
                    t = (co.z - 0.10) / 0.04
                    obj.vertex_groups["Foot" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["LowerLeg" + side].add([v.index], t, 'REPLACE')
                elif co.z < 0.44:
                    obj.vertex_groups["LowerLeg" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.52:
                    t = (co.z - 0.44) / 0.08
                    obj.vertex_groups["LowerLeg" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["UpperLeg" + side].add([v.index], t, 'REPLACE')
                else:
                    obj.vertex_groups["UpperLeg" + side].add([v.index], 1.0, 'REPLACE')

            # TORSO Y COLUMNA
            else:
                if co.z < 0.95:
                    obj.vertex_groups["Hips"].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.15:
                    t = (co.z - 0.95) / 0.20
                    obj.vertex_groups["Hips"].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Spine"].add([v.index], t, 'REPLACE')
                elif co.z < 1.34:
                    t = (co.z - 1.15) / 0.19
                    obj.vertex_groups["Spine"].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Chest"].add([v.index], t, 'REPLACE')
                elif co.z < 1.38:
                    t = (co.z - 1.34) / 0.04
                    obj.vertex_groups["Chest"].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Neck"].add([v.index], t, 'REPLACE')
                else:
                    obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')

def attach_armature_modifier(obj, arm_obj):
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj
    obj.parent = arm_obj

# =============================================================================
# 4. RENDERS DE CONTROL Y VALIDACIÓN MULTI-ÁNGULO (CYCLES CPU)
# =============================================================================
def render_control_views():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 48
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1200
    scene.render.film_transparent = False

    for light in [o for o in scene.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(light, do_unlink=True)

    def add_light(name, ltype, energy, loc, color=(1.0, 1.0, 1.0)):
        ld = bpy.data.lights.new(name, ltype)
        ld.energy = energy
        ld.color = color
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        scene.collection.objects.link(lo)
        return lo

    add_light("KeyLight", 'AREA', 240.0, (0.4, 1.6, 1.6), color=(1.0, 0.98, 0.95))
    add_light("FillLight", 'AREA', 150.0, (-0.8, 1.4, 1.4), color=(0.95, 0.97, 1.0))
    add_light("RimLight", 'AREA', 220.0, (0.0, -1.6, 1.6), color=(1.0, 0.98, 0.95))

    cam_data = bpy.data.cameras.new("RenderCam")
    cam_data.lens = 65
    cam_obj = bpy.data.objects.new("RenderCam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    shots = [
        ("astorga_preview.png",             ( 0.00,  1.85, 1.25), ( 0.00, 0.00, 1.25), os.path.join(PROJECT_ROOT, "godot_project/assets/characters/astorga_preview.png")),
        ("astorga_master_front.png",        ( 0.00,  2.20, 1.05), ( 0.00, 0.00, 1.05), os.path.join(SCRATCH_DIR, "astorga_master_front.png")),
        ("astorga_master_profile.png",      (-2.00,  0.00, 1.15), ( 0.00, 0.00, 1.15), os.path.join(SCRATCH_DIR, "astorga_master_profile.png")),
        ("astorga_master_back.png",         ( 0.00, -2.00, 1.15), ( 0.00, 0.00, 1.15), os.path.join(SCRATCH_DIR, "astorga_master_back.png")),
        ("astorga_master_threequarter.png", ( 1.20,  1.45, 1.20), ( 0.00, 0.00, 1.20), os.path.join(SCRATCH_DIR, "astorga_master_threequarter.png")),
    ]

    for name, c_pos, t_pos, out_p in shots:
        cam_obj.location = Vector(c_pos)
        direction = Vector(t_pos) - Vector(c_pos)
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cam_obj.rotation_euler = rot_quat.to_euler()
        scene.render.filepath = out_p
        bpy.ops.render.render(write_still=True)
        print(f"✓ Vista de control guardada: {out_p}")

def main():
    print("=" * 65)
    print("GENERANDO ASTORGA CANÓNICO: SASTRERÍA 3D, DEDOS DE VIOLINISTA Y RIG 22")
    print("=" * 65)

    clean_scene()

    all_mats = create_materials()
    mat_groups = {
        "head": [
            all_mats["skin"],
            all_mats["eyes"],
            all_mats["hair"]
        ],
        "body": [
            all_mats["suit"],
            all_mats["pants"],
            all_mats["shoes"],
            all_mats["skin"],
            all_mats["shirt"],
            all_mats["tie"],
            all_mats["buttons"]
        ]
    }

    # 1. Esqueleto canónico de 22 huesos
    arm_obj = build_skeleton()
    print("✓ Armature canónico construido con 22 huesos.")

    # 2. Malla de Cabeza modular
    obj_head = build_head_mesh(mat_groups)
    assign_weights(obj_head, is_head=True)
    attach_armature_modifier(obj_head, arm_obj)
    print("✓ Player_Head_Mesh generado con rostro moreno cálido, párpados con 'blink' y cabello ondulado 360°.")

    # 3. Malla de Cuerpo modular
    obj_body = build_body_mesh(mat_groups)
    assign_weights(obj_body, is_head=False)
    attach_armature_modifier(obj_body, arm_obj)
    print("✓ Player_Body_Mesh generado con sastrería 3D, solapas notch, camisa vinotinto y manos de 5 dedos.")

    # Verificación de fugas de pesos hacia las piernas
    vg_h_l = obj_body.vertex_groups.get("Hand.L")
    vg_h_r = obj_body.vertex_groups.get("Hand.R")
    leg_groups = [obj_body.vertex_groups[name].index for name in ["UpperLeg.L", "LowerLeg.L", "UpperLeg.R", "LowerLeg.R", "Foot.L", "Foot.R"] if name in obj_body.vertex_groups]
    leaks = 0
    if vg_h_l and vg_h_r:
        hand_indices = {vg_h_l.index, vg_h_r.index}
        for v in obj_body.data.vertices:
            g_ids = {g.group for g in v.groups if g.weight > 0.01}
            if hand_indices.intersection(g_ids) and any(lg in g_ids for lg in leg_groups):
                leaks += 1
    print(f"✓ Verificación matemática de pesos: {leaks} vértices de manos fugados a piernas.")

    # Guardar archivo .blend canónico
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
    print(f"✓ Guardado .blend en: {OUTPUT_BLEND}")

    # Exportar archivo .glb canónico
    bpy.ops.export_scene.gltf(
        filepath=OUTPUT_GLB,
        export_format='GLB',
        use_selection=False,
        export_apply=False,
        export_animations=False,
        export_skins=True,
        export_morph=True,
        export_materials='EXPORT',
        export_cameras=False,
        export_lights=False
    )
    print(f"✓ Exportado .glb canónico en: {OUTPUT_GLB}")

    # Renders de validación multi-ángulo
    render_control_views()

    print("=" * 65)
    print("PROCESO ASTORGA COMPLETADO EXITOSAMENTE")
    print("=" * 65)

if __name__ == "__main__":
    main()
