"""
=============================================================================
GENERADOR CANÓNICO PROCEDURAL DE ALTA FIDELIDAD: ASTORGA (TECATE SIMULATOR)
=============================================================================
Reconstrucción fidedigna del personaje Astorga basada en 'scratch/humans/astorga.png':
1. Cabeza y Fisiología Facial:
   - Rostro masculino estilizado con mandíbula angulada, mentón limpio sin barba
     y pómulos definidos acordes a la referencia fotográfica.
   - Ojos castaños profundos estilizados con párpados 3D y Shape Key 'blink'.
   - Cabellera oscura setentera/ochentera voluminosa con ondas orgánicas 360° y patillas.
   - Sin accesorios en el rostro (sin gafas).
2. Indumentaria: Traje Sastre Negro, Camisa Vinotinto y Corbata Oscura:
   - Saco formal negro carbón con solapas sastre, hombreras armadas y mangas completas.
   - Camisa de vestir formal en tono vino tinto / borgoña profundo (burgundy).
   - Corbata de seda oscura visible en el pecho.
   - Manos anatómicas de 5 dedos en reposo biomecánico, conectadas a las muñecas.
   - Pantalón sastre negro recto con raya de planchado.
   - Zapatos de vestir negros lustrados con suela y tacón de etiqueta.
   - Cero objetos embebidos: el violín se mantiene como prop independiente.
3. Arquitectura y Contratos de Rigging de Tecate Simulator:
   - Submallas modulares requeridas por CitizenEntity:
     * 'Player_Head_Mesh' (cabeza, ojos, párpados con blink, cabello ondulado 360°)
     * 'Player_Body_Mesh' (saco sastre, camisa, corbata, pantalón, zapatos y manos)
   - Esqueleto canónico 'Skeleton3D' con los 22 huesos antropométricos estándar.
   - Asignación de pesos sin fugas (0 vértices de manos asignados a piernas).
   - Exportación a 'astorga.glb' y 'astorga.blend'.
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
def get_or_create_material(name):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
    return mat

def setup_pbr_material(name, diffuse_tex_path, normal_tex_path=None,
                       base_color=(0.8, 0.8, 0.8, 1.0), roughness=0.6,
                       metallic=0.0, transmission=0.0, alpha=1.0, emission_color=None):
    mat = get_or_create_material(name)
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

    if emission_color and 'Emission Color' in bsdf.inputs:
        bsdf.inputs['Emission Color'].default_value = emission_color

    if 'Transmission Weight' in bsdf.inputs:
        bsdf.inputs['Transmission Weight'].default_value = transmission
    elif 'Transmission' in bsdf.inputs:
        bsdf.inputs['Transmission'].default_value = transmission

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
        links.new(norm_tex.outputs['Color'], norm_map.inputs['Color'])
        links.new(norm_map.outputs['Normal'], bsdf.inputs['Normal'])

    return mat

def create_materials():
    materials = {
        "skin": setup_pbr_material("Mat_Astorga_Skin",
                                   os.path.join(TEXTURES_DIR, "astorga_face_diffuse.png"),
                                   os.path.join(TEXTURES_DIR, "astorga_face_normal.png"),
                                   base_color=(0.835, 0.665, 0.575, 1.0), roughness=0.52),
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
                                      base_color=(0.05, 0.05, 0.06, 1.0), roughness=0.20, metallic=0.30),
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

    # Perfil craneofacial estilizado de Astorga basado en astorga.png
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
            is_face_skin = (z_mid < 1.555 and sin_mid > -0.10)
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
            dz_sup = 0.0030 * arch + 0.0003 * t
            dz_inf = -0.0026 * arch + 0.0002 * t
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
    # CABELLERA ONDULADA Y VOLUMINOSA 360° DE ASTORGA (astorga.png)
    # -------------------------------------------------------------------------
    # Melena con volumen en sienes, nuca, flequillo ondulado y coronilla
    hair_bm = bmesh.new()
    strand_layers = [
        # Flequillo ondulado frontal
        (-0.065, 0.052, 1.565, 0.022, 0.055, 0.018, 18.0),
        (-0.040, 0.064, 1.572, 0.024, 0.060, 0.020, 12.0),
        (-0.015, 0.070, 1.578, 0.025, 0.062, 0.022, 6.0),
        ( 0.015, 0.070, 1.578, 0.025, 0.062, 0.022, -6.0),
        ( 0.040, 0.064, 1.572, 0.024, 0.060, 0.020, -12.0),
        ( 0.065, 0.052, 1.565, 0.022, 0.055, 0.018, -18.0),

        # Sienes y patillas voluminosas
        (-0.082,  0.018, 1.530, 0.025, 0.045, 0.045,  30.0),
        (-0.088, -0.012, 1.520, 0.026, 0.046, 0.050,  20.0),
        (-0.086, -0.042, 1.505, 0.026, 0.046, 0.055,  10.0),
        ( 0.082,  0.018, 1.530, 0.025, 0.045, 0.045, -30.0),
        ( 0.088, -0.012, 1.520, 0.026, 0.046, 0.050, -20.0),
        ( 0.086, -0.042, 1.505, 0.026, 0.046, 0.055, -10.0),

        # Nuca densa y occipital amplio
        (-0.060, -0.075, 1.485, 0.028, 0.042, 0.055, 0.0),
        (-0.025, -0.085, 1.480, 0.030, 0.044, 0.058, 0.0),
        ( 0.025, -0.085, 1.480, 0.030, 0.044, 0.058, 0.0),
        ( 0.060, -0.075, 1.485, 0.028, 0.042, 0.055, 0.0),

        # Coronilla y volumen superior
        (-0.050, -0.025, 1.625, 0.032, 0.048, 0.035, 15.0),
        ( 0.000, -0.025, 1.635, 0.036, 0.052, 0.038, 0.0),
        ( 0.050, -0.025, 1.625, 0.032, 0.048, 0.035, -15.0),
        (-0.040, -0.055, 1.610, 0.032, 0.046, 0.038, 5.0),
        ( 0.040, -0.055, 1.610, 0.032, 0.046, 0.038, -5.0),
    ]

    for hx, hy, hz, sx, sy, sz, rot_y in strand_layers:
        s_bm = bmesh.new()
        bmesh.ops.create_uvsphere(s_bm, u_segments=12, v_segments=8, radius=1.0)
        bmesh.ops.scale(s_bm, verts=s_bm.verts, vec=(sx, sy, sz))
        bmesh.ops.rotate(s_bm, verts=s_bm.verts, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(rot_y), 4, 'Y'))
        bmesh.ops.translate(s_bm, verts=s_bm.verts, vec=(hx, hy, hz))
        v_map = {v: hair_bm.verts.new(v.co) for v in s_bm.verts}
        for f in s_bm.faces:
            nf = hair_bm.faces.new([v_map[v] for v in f.verts])
            nf.material_index = 2 # 2: Hair
        s_bm.free()

    v_map_hair = {v: bm.verts.new(v.co) for v in hair_bm.verts}
    for f in hair_bm.faces:
        nf = bm.faces.new([v_map_hair[v] for v in f.verts])
        nf.material_index = 2
        for loop in nf.loops: loop[uv_lay].uv = (0.5, 0.5)
    hair_bm.free()

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
        sk_blink.data[v_idx].co.z -= 0.0036
        sk_blink.data[v_idx].co.y += 0.0006
    for v_idx in crease_v_indices:
        sk_blink.data[v_idx].co.z -= 0.0018
        sk_blink.data[v_idx].co.y += 0.0003

    return obj_head

# =============================================================================
# 2. CUERPO: SACO SASTRE NEGRO, CAMISA VINOTINTO, CORBATA Y PANTALÓN FORMAL
# =============================================================================
def build_body_mesh(materials):
    mesh_graph = bpy.data.meshes.new("Body_Graph_Data")
    obj_body = bpy.data.objects.new("Player_Body_Mesh", mesh_graph)
    bpy.context.scene.collection.objects.link(obj_body)

    nodes = [
        # Tronco
        (0.00,  0.000, 0.82, 0.145, 0.108), # 0: Base pelvis
        (0.00,  0.002, 0.94, 0.148, 0.106), # 1: Caderas / Cintura sastre
        (0.00,  0.004, 1.04, 0.145, 0.102), # 2: Cintura
        (0.00, -0.006, 1.16, 0.158, 0.114), # 3: Costillas / tórax
        (0.00, -0.008, 1.28, 0.170, 0.122), # 4: Pectorales y espalda sastre
        (0.00, -0.004, 1.36, 0.160, 0.110), # 5: Clavículas / hombros armados
        (0.00,  0.004, 1.39, 0.048, 0.048), # 6: Base del cuello camisero

        # Brazos con mangas completas de traje
        ( 0.06, -0.004, 1.36, 0.072, 0.072), # 7
        ( 0.185, -0.004, 1.34, 0.068, 0.068), # 8: Hombro L
        ( 0.265,  0.002, 1.15, 0.054, 0.054), # 9: Codo L
        ( 0.315,  0.008, 0.96, 0.040, 0.038), # 10: Manga puño bajo L

        (-0.06, -0.004, 1.36, 0.072, 0.072), # 11
        (-0.185, -0.004, 1.34, 0.068, 0.068), # 12: Hombro R
        (-0.265,  0.002, 1.15, 0.054, 0.054), # 13: Codo R
        (-0.315,  0.008, 0.96, 0.040, 0.038), # 14: Manga puño bajo R

        # Piernas con pantalón sastre recto
        ( 0.088, 0.002, 0.82, 0.084, 0.084), # 15: Cadera sup L
        ( 0.088, 0.002, 0.65, 0.076, 0.076), # 16: Muslo medio L
        ( 0.088, 0.000, 0.48, 0.068, 0.068), # 17: Rodilla L
        ( 0.088, 0.000, 0.30, 0.060, 0.060), # 18: Pantorrilla L
        ( 0.088, 0.002, 0.12, 0.052, 0.052), # 19: Tobillo L
        ( 0.088, 0.055, 0.03, 0.054, 0.108), # 20: Zapato L

        (-0.088, 0.002, 0.82, 0.084, 0.084), # 21: Cadera sup R
        (-0.088, 0.002, 0.65, 0.076, 0.076), # 22: Muslo medio R
        (-0.088, 0.000, 0.48, 0.068, 0.068), # 23: Rodilla R
        (-0.088, 0.000, 0.30, 0.060, 0.060), # 24: Pantorrilla R
        (-0.088, 0.002, 0.12, 0.052, 0.052), # 25: Tobillo R
        (-0.088, 0.055, 0.03, 0.054, 0.108), # 26: Zapato R

        # Muñecas y Palmas anatómicas
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

    # Asignación de materiales base:
    # 0: Mat_Astorga_Suit  (Saco sastre negro y mangas)
    # 1: Mat_Astorga_Pants (Pantalón sastre negro)
    # 2: Mat_Astorga_Shoes (Zapatos de vestir negros)
    # 3: Mat_Astorga_Skin  (Manos anatómicas en piel)
    # 4: Mat_Astorga_Shirt (Camisa vinotinto en pechera frontal)
    # 5: Mat_Astorga_Tie   (Corbata oscura)
    for p in bm.faces:
        c_median = p.calc_center_median()
        cz = c_median.z
        cx = abs(c_median.x)
        cy = c_median.y

        if cz < 0.12:
            p.material_index = 2 # Zapatos
        elif cz < 0.96 and cx < 0.18:
            p.material_index = 1 # Pantalón sastre
        elif cx > 0.18:
            if cz < 0.91:
                p.material_index = 3 # Manos anatómicas en piel
            else:
                p.material_index = 0 # Mangas del saco sastre
        else:
            # Pecho frontal: escote sastre en V exhibiendo camisa vinotinto
            if 1.18 <= cz <= 1.38 and cy > 0.05 and cx < 0.065:
                # Corbata central
                if cx < 0.020 and cz <= 1.36:
                    p.material_index = 5 # Corbata oscura
                else:
                    p.material_index = 4 # Camisa vinotinto
            else:
                p.material_index = 0 # Saco sastre formal negro

        for loop in p.loops:
            loop[uv_lay].uv = (loop.vert.co.x * 2.0 + 0.5, loop.vert.co.z * 1.5)

    # Cuello de camisa formal de vestir cerrado (Z = 1.36 a 1.40)
    collar_bm = bmesh.new()
    n_col = 20
    col_bot, col_top = [], []
    for i in range(n_col):
        ang = (2.0 * math.pi * i) / n_col
        cx = 0.056 * math.cos(ang)
        cy = (0.054 if math.sin(ang) >= 0 else 0.052) * math.sin(ang) + 0.002
        col_bot.append(collar_bm.verts.new((cx, cy, 1.360)))
        col_top.append(collar_bm.verts.new((cx * 1.06, cy * 1.06, 1.400)))
    for i in range(n_col):
        inxt = (i + 1) % n_col
        f = collar_bm.faces.new((col_bot[i], col_bot[inxt], col_top[inxt], col_top[i]))
        f.material_index = 4 # Mat_Astorga_Shirt
    v_map_col = {v: bm.verts.new(v.co) for v in collar_bm.verts}
    for f in collar_bm.faces:
        nf = bm.faces.new([v_map_col[v] for v in f.verts])
        nf.material_index = 4
        for loop in nf.loops: loop[uv_lay].uv = (0.5, 0.5)
    collar_bm.free()

    # Manos anatómicas con 5 dedos diferenciados
    for is_l in (True, False):
        s_sign = 1.0 if is_l else -1.0
        h_center = Vector((s_sign * 0.325, 0.012, 0.835))
        fingers_data = [
            (0.016, 0.008, 0.010, 0.005, -35.0, 15.0), # Pulgar
            (0.010, 0.003, -0.038, 0.004,   0.0,  0.0), # Índice
            (0.003, 0.002, -0.042, 0.004,   0.0,  0.0), # Medio
            (-0.004, 0.002, -0.038, 0.004,  0.0,  0.0), # Anular
            (-0.010, 0.001, -0.030, 0.0035, 0.0,  0.0), # Meñique
        ]
        for f_dx, f_dy, f_dz, f_rad, f_rot_y, f_rot_x in fingers_data:
            f_bm = bmesh.new()
            bmesh.ops.create_uvsphere(f_bm, u_segments=8, v_segments=6, radius=f_rad)
            f_len = abs(f_dz) if abs(f_dz) > 0.015 else 0.025
            bmesh.ops.scale(f_bm, verts=f_bm.verts, vec=(1.0, 1.0, f_len / f_rad))
            bmesh.ops.rotate(f_bm, verts=f_bm.verts, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(s_sign * f_rot_y), 4, 'Y'))
            f_pos = h_center + Vector((s_sign * f_dx, f_dy, f_dz * 0.5))
            bmesh.ops.translate(f_bm, verts=f_bm.verts, vec=f_pos)
            v_map_f = {v: bm.verts.new(v.co) for v in f_bm.verts}
            for f in f_bm.faces:
                nf = bm.faces.new([v_map_f[v] for v in f.verts])
                nf.material_index = 3 # 3: Skin
                for loop in nf.loops: loop[uv_lay].uv = (0.5, 0.5)
            f_bm.free()

    bm.to_mesh(obj_body.data)
    bm.free()

    # Asignar materiales
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
        ("Hand.L",      "Forearm.L",   (0.325, 0.015, 0.93),(0.325, 0.015, 0.80)),

        ("Shoulder.R",  "Chest",       (-0.04, 0, 1.36),  (-0.185, 0, 1.36)),
        ("UpperArm.R",  "Shoulder.R",  (-0.185, 0, 1.36), (-0.265, 0.005, 1.15)),
        ("Forearm.R",   "UpperArm.R",  (-0.265, 0.005, 1.15),(-0.325, 0.015, 0.93)),
        ("Hand.R",      "Forearm.R",   (-0.325, 0.015, 0.93),(-0.325, 0.015, 0.80)),

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
        ("astorga_preview.png",             ( 0.00,  1.70, 1.30), ( 0.00, 0.00, 1.30), os.path.join(PROJECT_ROOT, "godot_project/assets/characters/astorga_preview.png")),
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
    print("GENERANDO ASTORGA CANÓNICO: TRAJE SASTRE, CAMISA VINOTINTO Y RIG 22")
    print("=" * 65)

    bpy.ops.wm.read_factory_settings(use_empty=True)

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
    print("✓ Player_Head_Mesh generado con ojos a Z=1.515, párpados con 'blink' y cabello ondulado 360°.")

    # 3. Malla de Cuerpo modular
    obj_body = build_body_mesh(mat_groups)
    assign_weights(obj_body, is_head=False)
    attach_armature_modifier(obj_body, arm_obj)
    print("✓ Player_Body_Mesh generado con traje formal, camisa vinotinto y pantalón sastre.")

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
