"""
=============================================================================
GENERADOR CANÓNICO PROCEDURAL DE ALTA FIDELIDAD: ELI (TECATE SIMULATOR)
=============================================================================
Reconstrucción fidedigna del personaje Eli basada en 'eli2.png' y 'eli3.png':
1. Cabeza y Fisiología Facial (eli3.png y eli2.png):
   - Rostro masculino estilizado con mandíbula angulada, mentón firme y pómulos definidos.
   - Sonrisa amplia y cálida característica de Eli, con dientes blancos pulidos visibles.
   - Ojos castaños cálidos estilizados con párpados anatómicos y Shape Key 'blink'.
   - Gafas rectangulares modernas de pasta fina negra con cristales transparentes diáfanos (eli2.png).
   - Cabellera castaño oscuro con volumen y mechones ondulados orgánicos 360° (eli3.png).
   - Barba perfilada completa siguiendo la línea mandibular y cuello en piel limpia.
2. Indumentaria: Camisa Resort en V y Pecho Expuesto (eli2.png):
   - Camisa casual de lino crema / marfil con cuello camp / solapas abiertas tipo cubano.
   - Escote pronunciado en V (Z=1.39 a Z=1.21) que expone el pecho anatómico.
   - Vello pectoral (chest hair) natural procedural con micro-hebras curvas y relieve PBR.
   - Hilera frontal de botones nacarados bajo el escote en V.
   - Mangas cortas de lino integradas y antebrazos anatómicos en piel natural.
   - Cinturón elíptico ceñido con hebilla metálica.
   - Pantalón chino en tono arena cálido / caqui elegante.
   - Zapatos casuales / mocasines de cuero café pulido.
   - Manos anatómicas de 5 dedos en reposo relajado con pulgar en oposición conectadas a la muñeca.
3. Arquitectura y Contratos de Rigging de Tecate Simulator:
   - Submallas modulares requeridas por CitizenEntity:
     * 'Player_Head_Mesh' (cabeza, ojos, gafas, cabello, dientes, párpados con blink)
     * 'Player_Body_Mesh' (camisa en V, pecho con vello pectoral, pantalón, cinturón, zapatos y manos)
   - Esqueleto canónico 'Skeleton3D' con los 22 huesos antropométricos estándar.
   - Asignación de pesos sin fugas (0 vértices de manos asignados a piernas).
   - Exportación a 'eli.glb' y 'eli.blend'.
   - Renders de validación multi-ángulo con Cycles CPU.
=============================================================================
"""

import os
import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
ASSETS_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/citizens")
TEXTURES_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/textures")
SCRATCH_DIR = os.path.join(PROJECT_ROOT, "scratch")

OUTPUT_BLEND = os.path.join(ASSETS_DIR, "eli.blend")
OUTPUT_GLB = os.path.join(ASSETS_DIR, "eli.glb")
PREVIEW_PNG = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/eli_preview.png")

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

    if alpha < 1.0 or transmission > 0.5:
        mat.blend_method = 'BLEND' if hasattr(mat, 'blend_method') else 'OPAQUE'
        if 'Alpha' in bsdf.inputs:
            bsdf.inputs['Alpha'].default_value = alpha

    return mat

def create_materials():
    materials = {
        "skin": setup_pbr_material("Mat_Eli_Skin",
                                   os.path.join(TEXTURES_DIR, "eli_face_diffuse.png"),
                                   os.path.join(TEXTURES_DIR, "eli_face_normal.png"),
                                   base_color=(0.865, 0.685, 0.605, 1.0), roughness=0.52),
        "eyes": setup_pbr_material("Mat_Eli_Eyes",
                                   os.path.join(TEXTURES_DIR, "eli_eye_diffuse.png"),
                                   base_color=(0.96, 0.95, 0.94, 1.0), roughness=0.10),
        "hair": setup_pbr_material("Mat_Eli_Hair", None, None,
                                   base_color=(0.09, 0.07, 0.05, 1.0), roughness=0.74),
        "glasses": setup_pbr_material("Mat_Eli_Glasses",
                                      os.path.join(TEXTURES_DIR, "eli_glasses_diffuse.png"),
                                      base_color=(0.05, 0.05, 0.06, 1.0), roughness=0.25),
        "glass": setup_pbr_material("Mat_Eli_Glass", None, None,
                                    base_color=(0.95, 0.98, 1.0, 1.0), roughness=0.04, transmission=0.95, alpha=0.15),
        "teeth": setup_pbr_material("Mat_Eli_Teeth", None, None,
                                    base_color=(0.98, 0.98, 0.96, 1.0), roughness=0.15,
                                    emission_color=(0.20, 0.20, 0.19, 1.0)),
        "shirt": setup_pbr_material("Mat_Eli_Shirt",
                                    os.path.join(TEXTURES_DIR, "eli_resort_shirt_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "eli_resort_shirt_normal.png"),
                                    base_color=(0.865, 0.855, 0.785, 1.0), roughness=0.70),
        "chest": setup_pbr_material("Mat_Eli_Chest",
                                    os.path.join(TEXTURES_DIR, "eli_chest_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "eli_chest_normal.png"),
                                    base_color=(0.865, 0.685, 0.605, 1.0), roughness=0.52),
        "pants": setup_pbr_material("Mat_Eli_Pants",
                                    os.path.join(TEXTURES_DIR, "eli_pants_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "eli_pants_normal.png"),
                                    base_color=(0.760, 0.710, 0.635, 1.0), roughness=0.65),
        "shoes": setup_pbr_material("Mat_Eli_Shoes",
                                    os.path.join(TEXTURES_DIR, "eli_shoes_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "eli_shoes_normal.png"),
                                    base_color=(0.22, 0.12, 0.08, 1.0), roughness=0.30),
        "belt": setup_pbr_material("Mat_Eli_Belt",
                                   os.path.join(TEXTURES_DIR, "eli_belt_diffuse.png"),
                                   os.path.join(TEXTURES_DIR, "eli_belt_normal.png"),
                                   base_color=(0.20, 0.10, 0.06, 1.0), roughness=0.30),
        "buckle": setup_pbr_material("Mat_Eli_Buckle", None, None,
                                     base_color=(0.82, 0.80, 0.75, 1.0), roughness=0.25, metallic=0.90),
        "buttons": setup_pbr_material("Mat_Eli_Buttons",
                                      os.path.join(TEXTURES_DIR, "eli_button_diffuse.png"),
                                      base_color=(0.91, 0.89, 0.84, 1.0), roughness=0.30),
    }
    return materials

# =============================================================================
# 1. CABEZA, ROSTRO, OJOS, GAFAS Y CABELLO ONDULADO (Player_Head_Mesh)
# =============================================================================
def build_head_mesh(materials):
    me = bpy.data.meshes.new("Player_Head_Mesh_Data")
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")

    def calc_face_uv(x, z):
        u = 0.50 + x / 0.275
        v = 0.50 + (z - 1.485) / 0.240
        return (max(0.0, min(1.0, u)), max(0.0, min(1.0, v)))

    # Perfil craneofacial estilizado de Eli basado en eli3.png
    head_profile = [
        # z,      rx,    ry_front, ry_back, y_offset, is_face
        (1.370,  0.046, 0.046,    0.048,   -0.002,   False), # 0: Base cuello (conecta con cuerpo)
        (1.392,  0.048, 0.046,    0.052,   -0.001,   False), # 1: Cuello medio (piel limpia)
        (1.412,  0.052, 0.050,    0.060,    0.001,   True),  # 2: Submandíbula
        (1.428,  0.057, 0.063,    0.070,    0.006,   True),  # 3: Mentón con barba
        (1.445,  0.061, 0.063,    0.078,    0.005,   True),  # 4: Surco mentolabial
        (1.458,  0.064, 0.066,    0.084,    0.003,   True),  # 5: Labio inferior sonriente
        (1.468,  0.066, 0.065,    0.088,    0.002,   True),  # 6: Hendidura bucal abierta
        (1.478,  0.068, 0.068,    0.092,    0.002,   True),  # 7: Labio superior con bigote
        (1.492,  0.071, 0.067,    0.094,    0.001,   True),  # 8: Base nasal / Filtrum
        (1.505,  0.073, 0.075,    0.095,    0.000,   True),  # 9: Punta nasal recta y definida
        (1.515,  0.075, 0.069,    0.095,    0.000,   True),  # 10: Ojos y puente nasal (Z = 1.515)
        (1.532,  0.076, 0.072,    0.094,   -0.002,   True),  # 11: Pómulos y cejas pobladas
        (1.550,  0.075, 0.069,    0.091,   -0.004,   True),  # 12: Sienes y frente baja
        (1.570,  0.073, 0.063,    0.087,   -0.006,   True),  # 13: Frente media despejada
        (1.592,  0.069, 0.055,    0.080,   -0.008,   False), # 14: Nacimiento de cabello
        (1.615,  0.059, 0.045,    0.070,   -0.010,   False), # 15: Bóveda craneal
        (1.635,  0.039, 0.027,    0.045,   -0.012,   False), # 16: Coronilla
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
                y += 0.006 * math.cos((ang - 0.5 * math.pi) / 0.06 * (0.5 * math.pi))**2

            if l_idx in (5, 6, 7) and 0.38 * math.pi <= ang <= 0.62 * math.pi:
                sw = math.cos((ang - 0.5 * math.pi) / 0.12 * (0.5 * math.pi))**2
                if l_idx == 6: y -= 0.004 * sw
                else: y += 0.003 * sw

            if l_idx in (8, 9, 10) and 0.46 * math.pi <= ang <= 0.54 * math.pi:
                nw = math.cos((ang - 0.5 * math.pi) / 0.04 * (0.5 * math.pi))**2
                if l_idx == 9: y += 0.011 * nw
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
            is_scalp = (z_mid >= 1.585) or (z_mid >= 1.44 and sin_mid < -0.15)
            f.material_index = 2 if is_scalp else 0 # 2: Hair, 0: Skin

            for loop in f.loops:
                loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

    # Coronilla superior
    top_vert = bm.verts.new((0.0, -0.012, 1.642))
    r_last = rings[-1]
    for i in range(n_ring):
        inxt = (i + 1) % n_ring
        f_top = bm.faces.new((r_last[i], r_last[inxt], top_vert))
        f_top.material_index = 2
        for loop in f_top.loops:
            loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

    # Dientes superiores visibles en la sonrisa radiante de Eli (eli2.png)
    teeth_bm = bmesh.new()
    n_t = 10
    t_r = 0.022
    t_top, t_bot = [], []
    for k in range(n_t):
        ang_t = (k / float(n_t - 1) - 0.5) * 1.05
        tx = t_r * math.sin(ang_t)
        ty = 0.063 + t_r * (math.cos(ang_t) - 1.0) * 0.25
        t_top.append(teeth_bm.verts.new((tx, ty, 1.472)))
        t_bot.append(teeth_bm.verts.new((tx, ty, 1.464)))
    for k in range(n_t - 1):
        teeth_bm.faces.new((t_top[k], t_top[k+1], t_bot[k+1], t_bot[k])).material_index = 5 # Teeth
    v_map_t = {v: bm.verts.new(v.co) for v in teeth_bm.verts}
    for f in teeth_bm.faces:
        nf = bm.faces.new([v_map_t[v] for v in f.verts])
        nf.material_index = 5
        for loop in nf.loops: loop[uv_lay].uv = (0.5, 0.5)
    teeth_bm.free()

    # Globos oculares 3D (Z = 1.515, Y = 0.058, Radio = 0.0135)
    eye_pos = [(0.033, 0.058, 1.515), (-0.033, 0.058, 1.515)]
    eye_r = 0.0135
    for pos in eye_pos:
        e_bm = bmesh.new()
        bmesh.ops.create_uvsphere(e_bm, u_segments=16, v_segments=12, radius=eye_r)
        bmesh.ops.rotate(e_bm, verts=e_bm.verts, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(-90), 4, 'X'))
        bmesh.ops.translate(e_bm, verts=e_bm.verts, vec=pos)
        v_map = {v: bm.verts.new(v.co) for v in e_bm.verts}
        for f in e_bm.faces:
            nf = bm.faces.new([v_map[v] for v in f.verts])
            nf.material_index = 1 # Mat_Eli_Eyes
            for loop in nf.loops:
                co = loop.vert.co - Vector(pos)
                loop[uv_lay].uv = (0.5 + co.x / (2.0 * eye_r), 0.5 + co.z / (2.0 * eye_r))
        e_bm.free()

    # Párpados anatómicos con Shape Key 'blink'
    upper_lid_margin_verts = []
    upper_lid_crease_verts = []
    for ex, ey, ez in eye_pos:
        sign_side = 1.0 if ex > 0 else -1.0
        n_pts = 9
        upper_margin, upper_crease = [], []
        lower_margin, lower_crease = [], []
        for i in range(n_pts):
            t = (i / float(n_pts - 1)) * 2.0 - 1.0
            dx = t * 0.0145 * sign_side
            arch = math.sqrt(max(0.0, 1.0 - t**2))
            dz_sup = 0.0040 * arch
            dz_inf = -0.0040 * arch
            dy_sup = math.sqrt(max(0.0001, (eye_r * 1.03)**2 - dx**2 - dz_sup**2))
            dy_inf = math.sqrt(max(0.0001, (eye_r * 1.03)**2 - dx**2 - dz_inf**2))

            v_sup_m = bm.verts.new((ex + dx, ey + dy_sup, ez + dz_sup))
            v_sup_c = bm.verts.new((ex + dx, ey + dy_sup * 0.98 + 0.002, ez + dz_sup + 0.004 * arch))
            v_inf_m = bm.verts.new((ex + dx, ey + dy_inf, ez + dz_inf))
            v_inf_c = bm.verts.new((ex + dx, ey + dy_inf * 0.98 + 0.002, ez + dz_inf - 0.004 * arch))

            upper_margin.append(v_sup_m)
            upper_crease.append(v_sup_c)
            lower_margin.append(v_inf_m)
            lower_crease.append(v_inf_c)

            upper_lid_margin_verts.append(v_sup_m)
            upper_lid_crease_verts.append(v_sup_c)

        for i in range(n_pts - 1):
            f1 = bm.faces.new((upper_margin[i], upper_margin[i+1], upper_crease[i+1], upper_crease[i]))
            f1.material_index = 0
            f2 = bm.faces.new((lower_crease[i], lower_crease[i+1], lower_margin[i+1], lower_margin[i]))
            f2.material_index = 0
            for f in (f1, f2):
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
    # GAFAS RECTANGULARES MODERNAS DE ACETATO NEGRO (eli2.png)
    # -------------------------------------------------------------------------
    glasses_bm = bmesh.new()
    frame_w = 0.0016
    frame_depth = 0.0015
    lens_hw = 0.0205
    lens_hh = 0.0130
    lens_y = 0.0715
    lens_z = 1.515

    for s_side in (1.0, -1.0):
        c_x = s_side * 0.033
        n_frame = 16
        inner_f, outer_f = [], []
        inner_b, outer_b = [], []
        lens_inner = []
        for i in range(n_frame):
            ang = (2.0 * math.pi * i) / n_frame
            cos_a = math.copysign(abs(math.cos(ang))**0.45, math.cos(ang))
            sin_a = math.copysign(abs(math.sin(ang))**0.45, math.sin(ang))

            rx_in = c_x + lens_hw * cos_a
            rz_in = lens_z + lens_hh * sin_a
            rx_out = c_x + (lens_hw + frame_w) * cos_a
            rz_out = lens_z + (lens_hh + frame_w) * sin_a

            v_if = glasses_bm.verts.new((rx_in, lens_y + frame_depth * 0.5, rz_in))
            v_of = glasses_bm.verts.new((rx_out, lens_y + frame_depth * 0.5, rz_out))
            v_ib = glasses_bm.verts.new((rx_in, lens_y - frame_depth * 0.5, rz_in))
            v_ob = glasses_bm.verts.new((rx_out, lens_y - frame_depth * 0.5, rz_out))

            inner_f.append(v_if)
            outer_f.append(v_of)
            inner_b.append(v_ib)
            outer_b.append(v_ob)
            lens_inner.append(v_if)

        for i in range(n_frame):
            inxt = (i + 1) % n_frame
            glasses_bm.faces.new((inner_f[i], inner_f[inxt], outer_f[inxt], outer_f[i])).material_index = 3 # Glasses
            glasses_bm.faces.new((outer_f[i], outer_f[inxt], outer_b[inxt], outer_b[i])).material_index = 3
            glasses_bm.faces.new((inner_b[i], inner_b[inxt], inner_f[inxt], inner_f[i])).material_index = 3
            glasses_bm.faces.new((outer_b[i], outer_b[inxt], inner_b[inxt], inner_b[i])).material_index = 3

        # Cristales diáfanos transparentes
        c_lens = glasses_bm.verts.new((c_x, lens_y, lens_z))
        for i in range(n_frame):
            inxt = (i + 1) % n_frame
            glasses_bm.faces.new((lens_inner[i], lens_inner[inxt], c_lens)).material_index = 4 # Mat_Eli_Glass

        # Patillas ergonómicas hacia las orejas
        tx_front = c_x + s_side * (lens_hw + frame_w)
        tx_ear = s_side * 0.072
        t_bar = [
            glasses_bm.verts.new((tx_front, lens_y - 0.001, lens_z + 0.0010)),
            glasses_bm.verts.new((tx_ear,   -0.006,         1.512 + 0.0010)),
            glasses_bm.verts.new((tx_ear,   -0.006,         1.512 - 0.0010)),
            glasses_bm.verts.new((tx_front, lens_y - 0.001, lens_z - 0.0010)),
        ]
        if s_side > 0:
            glasses_bm.faces.new(t_bar).material_index = 3
        else:
            glasses_bm.faces.new(t_bar[::-1]).material_index = 3

    # Puente nasal recto
    bridge = [
        glasses_bm.verts.new(( 0.013, lens_y + frame_depth * 0.4, lens_z + 0.0015)),
        glasses_bm.verts.new((-0.013, lens_y + frame_depth * 0.4, lens_z + 0.0015)),
        glasses_bm.verts.new((-0.013, lens_y - frame_depth * 0.4, lens_z - 0.0005)),
        glasses_bm.verts.new(( 0.013, lens_y - frame_depth * 0.4, lens_z - 0.0005)),
    ]
    glasses_bm.faces.new(bridge).material_index = 3

    v_map_g = {v: bm.verts.new(v.co) for v in glasses_bm.verts}
    for f in glasses_bm.faces:
        nf = bm.faces.new([v_map_g[v] for v in f.verts])
        nf.material_index = f.material_index
        for loop in nf.loops: loop[uv_lay].uv = (0.5, 0.5)
    glasses_bm.free()

    # -------------------------------------------------------------------------
    # CABELLERA ONDULADA Y RIZADA ORGÁNICA EN 360° (eli3.png)
    # -------------------------------------------------------------------------
    # 1. Cúpula volumétrica base con ondulación continua
    hair_profile = [
        # z,     rx,    ry_front, ry_back, y_offset
        (1.505, 0.078, 0.046,    0.092,   -0.006),
        (1.535, 0.080, 0.058,    0.096,   -0.006),
        (1.565, 0.082, 0.068,    0.098,   -0.005),
        (1.595, 0.080, 0.068,    0.095,   -0.005),
        (1.625, 0.072, 0.060,    0.084,   -0.007),
        (1.648, 0.054, 0.044,    0.064,   -0.009),
        (1.662, 0.030, 0.024,    0.036,   -0.012),
    ]
    n_hring = 24
    h_rings = []
    for l_idx, (hz, hrx, hry_f, hry_b, hy_off) in enumerate(hair_profile):
        cur_h = []
        for i in range(n_hring):
            hang = (2.0 * math.pi * i) / n_hring
            cos_a = math.cos(hang)
            sin_a = math.sin(hang)
            wave = 0.0032 * math.sin(hang * 4.0 + hz * 18.0) + 0.0016 * math.cos(hang * 6.0)
            tuft_boost = 0.0060 * math.cos((hang - 0.5 * math.pi) * 2.0)**2 if (hz >= 1.58 and 0.25 * math.pi <= hang <= 0.75 * math.pi) else 0.0
            hx = (hrx + wave) * cos_a
            hy = ((hry_f if sin_a >= 0 else hry_b) + wave + tuft_boost) * sin_a + hy_off
            cur_h.append(bm.verts.new((hx, hy, hz)))
        h_rings.append(cur_h)

    for l in range(len(h_rings) - 1):
        ra = h_rings[l]
        rb = h_rings[l + 1]
        for i in range(n_hring):
            inxt = (i + 1) % n_hring
            hf = bm.faces.new((ra[i], ra[inxt], rb[inxt], rb[i]))
            hf.material_index = 2 # Mat_Eli_Hair
            for loop in hf.loops: loop[uv_lay].uv = (0.5, 0.5)

    h_top = bm.verts.new((0.0, -0.012, 1.666))
    for i in range(n_hring):
        inxt = (i + 1) % n_hring
        hf_top = bm.faces.new((h_rings[-1][i], h_rings[-1][inxt], h_top))
        hf_top.material_index = 2
        for loop in hf_top.loops: loop[uv_lay].uv = (0.5, 0.5)

    # 2. Mechones ondulados 3D volumétricos en coronilla y flequillo (eli3.png)
    def add_wavy_lock(p_start, p_delta, r_wave, turns, phi0, base_thick=0.0055, n_steps=10):
        prev_ring = None
        for s in range(n_steps):
            t = s / float(n_steps - 1)
            cx = p_start[0] + p_delta[0] * t
            cy = p_start[1] + p_delta[1] * t
            cz = p_start[2] + p_delta[2] * t
            cur_r = r_wave * (1.0 - 0.20 * t)
            phase = 2.0 * math.pi * turns * t + phi0
            sp_x = cx + cur_r * math.cos(phase)
            sp_y = cy + cur_r * math.sin(phase) * 0.5
            sp_z = cz
            tb_r = base_thick * (1.0 - 0.35 * t)
            c_ring = []
            for k in range(5):
                k_ang = (2.0 * math.pi * k) / 5.0
                c_ring.append(bm.verts.new((sp_x + tb_r * math.cos(k_ang),
                                           sp_y + tb_r * math.sin(k_ang) * 0.75,
                                           sp_z + tb_r * math.sin(k_ang) * 0.85)))
            if prev_ring:
                for k in range(5):
                    kn = (k + 1) % 5
                    f_c = bm.faces.new((prev_ring[k], prev_ring[kn], c_ring[kn], c_ring[k]))
                    f_c.material_index = 2
                    for loop in f_c.loops: loop[uv_lay].uv = (0.5, 0.5)
            prev_ring = c_ring

    locks_specs = [
        # Flequillo frontal (ondas rizadas hacia la frente)
        (( 0.024, 0.068, 1.595), ( 0.008, 0.012, -0.028), 0.007, 1.8, 0.5),
        ((-0.024, 0.068, 1.595), (-0.008, 0.012, -0.028), 0.007, 1.8, 1.2),
        (( 0.000, 0.072, 1.605), ( 0.002, 0.014, -0.032), 0.008, 2.1, 2.0),
        (( 0.045, 0.058, 1.585), ( 0.010, 0.008, -0.025), 0.006, 1.7, 0.8),
        ((-0.045, 0.058, 1.585), (-0.010, 0.008, -0.025), 0.006, 1.7, 1.5),
        # Mechones en la coronilla superior
        (( 0.030, 0.025, 1.635), ( 0.012, 0.005, -0.022), 0.007, 1.6, 0.2),
        ((-0.030, 0.025, 1.635), (-0.012, 0.005, -0.022), 0.007, 1.6, 1.0),
        (( 0.000, 0.035, 1.642), ( 0.004, 0.008, -0.024), 0.007, 1.8, 2.4),
        (( 0.020, -0.010, 1.650), ( 0.008, -0.006, -0.020), 0.006, 1.5, 0.6),
        ((-0.020, -0.010, 1.650), (-0.008, -0.006, -0.020), 0.006, 1.5, 1.4),
    ]
    for p_st, p_dt, rw, trns, p0 in locks_specs:
        add_wavy_lock(p_st, p_dt, rw, trns, p0)

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

    # Shape Key: 'blink'
    sk_basis = obj_head.shape_key_add(name="Basis")
    sk_blink = obj_head.shape_key_add(name="blink")
    for v_idx in margin_v_indices:
        sk_blink.data[v_idx].co.z -= 0.0075
        sk_blink.data[v_idx].co.y += 0.0010
    for v_idx in crease_v_indices:
        sk_blink.data[v_idx].co.z -= 0.0038
        sk_blink.data[v_idx].co.y += 0.0005

    return obj_head

# =============================================================================
# 2. CUERPO: CAMISA RESORT EN V, PECHO EXPUESTO CON VELLO PECTORAL Y CHINOS
# =============================================================================
def build_body_mesh(materials):
    mesh_graph = bpy.data.meshes.new("Body_Graph_Data")
    obj_body = bpy.data.objects.new("Player_Body_Mesh", mesh_graph)
    bpy.context.scene.collection.objects.link(obj_body)

    nodes = [
        # Tronco
        (0.00,  0.000, 0.82, 0.145, 0.108), # 0: Base pelvis
        (0.00,  0.002, 0.94, 0.148, 0.106), # 1: Caderas / Cintura pantalón
        (0.00,  0.004, 1.04, 0.142, 0.100), # 2: Cintura
        (0.00, -0.006, 1.16, 0.154, 0.112), # 3: Costillas / tórax
        (0.00, -0.008, 1.28, 0.168, 0.120), # 4: Pectorales y espalda
        (0.00, -0.004, 1.36, 0.156, 0.108), # 5: Clavículas / hombros
        (0.00,  0.004, 1.39, 0.048, 0.048), # 6: Base del cuello
        
        # Brazos
        ( 0.06, -0.004, 1.36, 0.070, 0.070), # 7
        ( 0.185, -0.004, 1.34, 0.065, 0.065), # 8: Hombro L
        ( 0.265,  0.002, 1.15, 0.052, 0.052), # 9: Codo L
        ( 0.325,  0.012, 0.93, 0.038, 0.035), # 10: Muñeca L

        (-0.06, -0.004, 1.36, 0.070, 0.070), # 11
        (-0.185, -0.004, 1.34, 0.065, 0.065), # 12: Hombro R
        (-0.265,  0.002, 1.15, 0.052, 0.052), # 13: Codo R
        (-0.325,  0.012, 0.93, 0.038, 0.035), # 14: Muñeca R

        # Piernas
        ( 0.088, 0.002, 0.82, 0.082, 0.082), # 15: Cadera sup L
        ( 0.088, 0.002, 0.65, 0.074, 0.074), # 16: Muslo medio L
        ( 0.088, 0.000, 0.48, 0.066, 0.066), # 17: Rodilla L
        ( 0.088, 0.000, 0.30, 0.058, 0.058), # 18: Pantorrilla L
        ( 0.088, 0.002, 0.12, 0.050, 0.050), # 19: Tobillo L
        ( 0.088, 0.055, 0.03, 0.052, 0.105), # 20: Pie L

        (-0.088, 0.002, 0.82, 0.082, 0.082), # 21: Cadera sup R
        (-0.088, 0.002, 0.65, 0.074, 0.074), # 22: Muslo medio R
        (-0.088, 0.000, 0.48, 0.066, 0.066), # 23: Rodilla R
        (-0.088, 0.000, 0.30, 0.058, 0.058), # 24: Pantorrilla R
        (-0.088, 0.002, 0.12, 0.050, 0.050), # 25: Tobillo R
        (-0.088, 0.055, 0.03, 0.052, 0.105), # 26: Pie R
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6),
        (5, 7), (7, 8), (8, 9), (9, 10),
        (5, 11), (11, 12), (12, 13), (13, 14),
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

    # Asignación de materiales base a la malla unificada:
    # 0: Mat_Eli_Shirt (Camisa de lino crema en torso y mangas cortas Z >= 1.18)
    # 1: Mat_Eli_Pants (Pantalón chino arena en piernas Z < 0.96)
    # 2: Mat_Eli_Shoes (Zapatos mocasines café en pies Z < 0.10)
    # 3: Mat_Eli_Skin  (Antebrazos y manos en piel natural)
    for p in bm.faces:
        center_z = p.calc_center_median().z
        center_x = abs(p.calc_center_median().x)
        if center_z < 0.10:
            p.material_index = 2 # Zapatos
        elif center_z < 0.96 and center_x < 0.18:
            p.material_index = 1 # Pantalón chino
        elif center_x > 0.18 and center_z < 1.18:
            p.material_index = 3 # Piel del antebrazo expuesto
        else:
            p.material_index = 0 # Camisa de lino crema
        for loop in p.loops:
            loop[uv_lay].uv = (loop.vert.co.x * 2.0 + 0.5, loop.vert.co.z * 1.5)

    # Cinturón elíptico entallado a la cintura (Z = 0.955 a 0.985)
    belt_bm = bmesh.new()
    n_belt = 24
    b_bot, b_top = [], []
    for i in range(n_belt):
        ang = (2.0 * math.pi * i) / n_belt
        bx = 0.146 * math.cos(ang)
        by = (0.106 if math.sin(ang) >= 0 else 0.102) * math.sin(ang) + 0.002
        b_bot.append(belt_bm.verts.new((bx, by, 0.955)))
        b_top.append(belt_bm.verts.new((bx, by, 0.985)))
    for i in range(n_belt):
        inxt = (i + 1) % n_belt
        belt_bm.faces.new((b_bot[i], b_bot[inxt], b_top[inxt], b_top[i])).material_index = 6 # Belt

    # Hebilla metálica en el centro (Z = 0.970, Y = 0.110)
    bmesh.ops.create_cube(belt_bm, size=0.016)
    bmesh.ops.scale(belt_bm, verts=belt_bm.verts[-8:], vec=(1.6, 0.35, 1.1))
    bmesh.ops.translate(belt_bm, verts=belt_bm.verts[-8:], vec=(0.0, 0.108, 0.970))
    for f in belt_bm.faces[-6:]: f.material_index = 7 # Buckle
    v_map_b = {v: bm.verts.new(v.co) for v in belt_bm.verts}
    for f in belt_bm.faces:
        nf = bm.faces.new([v_map_b[v] for v in f.verts])
        nf.material_index = f.material_index
        for loop in nf.loops: loop[uv_lay].uv = (0.5, 0.5)
    belt_bm.free()

    # -------------------------------------------------------------------------
    # PECHO EXPUESTO EN V CON VELLO PECTORAL ANATÓMICO (eli2.png)
    # -------------------------------------------------------------------------
    # Superficie anatómica pectoral dentro del escote en V (Z = 1.21 a Z = 1.39)
    # Mapeo UV calibrado para que el vello pectoral se centre en el esternón
    chest_specs = [
        # z,     hw,    yf
        (1.390, 0.044, 0.088),
        (1.345, 0.038, 0.112),
        (1.300, 0.030, 0.126),
        (1.250, 0.020, 0.130),
        (1.210, 0.005, 0.128),
    ]
    chest_rows = []
    n_cpts = 5
    for cz, chw, cyf in chest_specs:
        row = []
        for i in range(n_cpts):
            t = (i / float(n_cpts - 1)) * 2.0 - 1.0
            cx = t * chw
            cy = cyf - 0.0030 * (1.0 - t**2)
            v = bm.verts.new((cx, cy, cz))
            row.append(v)
        chest_rows.append(row)

    for l in range(len(chest_specs) - 1):
        r1 = chest_rows[l]
        r2 = chest_rows[l + 1]
        for i in range(n_cpts - 1):
            f_ch = bm.faces.new((r1[i], r1[i+1], r2[i+1], r2[i]))
            f_ch.material_index = 4 # Mat_Eli_Chest (Piel con vello pectoral)
            for loop in f_ch.loops:
                vco = loop.vert.co
                u_coord = (vco.x / 0.088) + 0.50
                v_coord = (vco.z - 1.21) / 0.18
                loop[uv_lay].uv = (max(0.0, min(1.0, u_coord)), max(0.0, min(1.0, v_coord)))

    # -------------------------------------------------------------------------
    # CUELLO CAMP / SOLAPAS ABIERTAS RESORT (CUELLO EN V DE LINO) (eli2.png)
    # -------------------------------------------------------------------------
    for s_side in (1.0, -1.0):
        sgn = s_side
        v_neck_top = bm.verts.new((sgn * 0.036, 0.082, 1.392))
        v_lapel_tip = bm.verts.new((sgn * 0.078, 0.112, 1.345))
        v_lapel_notch = bm.verts.new((sgn * 0.068, 0.118, 1.328))
        v_lapel_outer = bm.verts.new((sgn * 0.075, 0.126, 1.280))
        v_v_apex = bm.verts.new((sgn * 0.012, 0.132, 1.210))
        v_mid_inner = bm.verts.new((sgn * 0.026, 0.120, 1.295))

        if sgn > 0:
            bm.faces.new((v_neck_top, v_lapel_tip, v_lapel_notch)).material_index = 0 # Shirt
            bm.faces.new((v_neck_top, v_lapel_notch, v_mid_inner)).material_index = 0
            bm.faces.new((v_lapel_notch, v_lapel_outer, v_v_apex)).material_index = 0
            bm.faces.new((v_lapel_notch, v_v_apex, v_mid_inner)).material_index = 0
        else:
            bm.faces.new((v_lapel_tip, v_neck_top, v_lapel_notch)).material_index = 0
            bm.faces.new((v_lapel_notch, v_neck_top, v_mid_inner)).material_index = 0
            bm.faces.new((v_lapel_outer, v_lapel_notch, v_v_apex)).material_index = 0
            bm.faces.new((v_v_apex, v_lapel_notch, v_mid_inner)).material_index = 0

    # Banda trasera del cuello camisero sobre la nuca (Z = 1.380 a 1.405)
    n_bcollar = 10
    bc_top, bc_bot = [], []
    for i in range(n_bcollar):
        ang = math.pi * 0.15 + (math.pi * 0.70 * i) / (n_bcollar - 1)
        bx = 0.050 * math.cos(ang)
        by = -0.046 * math.sin(ang) - 0.005
        bc_top.append(bm.verts.new((bx, by, 1.405)))
        bc_bot.append(bm.verts.new((bx, by, 1.380)))
    for i in range(n_bcollar - 1):
        f_bc = bm.faces.new((bc_bot[i], bc_bot[i+1], bc_top[i+1], bc_top[i]))
        f_bc.material_index = 0
        for loop in f_bc.loops: loop[uv_lay].uv = (0.5, 0.5)

    # Hilera frontal de botones nacarados bajo el escote en V (Z = 1.150, 1.070, 0.990)
    for bz in [1.150, 1.070, 0.990]:
        by = 0.126 + (1.150 - bz) * (-0.010)
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.0040)
        bmesh.ops.scale(btn_bm, verts=btn_bm.verts, vec=(1.0, 0.45, 1.0))
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.0, by, bz))
        v_map_b = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            nf = bm.faces.new([v_map_b[v] for v in f.verts])
            nf.material_index = 5 # Buttons
            for loop in nf.loops: loop[uv_lay].uv = (0.5, 0.5)
        btn_bm.free()

    # -------------------------------------------------------------------------
    # MANOS ANATÓMICAS CONECTADAS A LA MUÑECA (PIEL, 5 DEDOS)
    # -------------------------------------------------------------------------
    for is_l in (True, False):
        sign_a = 1.0 if is_l else -1.0
        w_center = Vector((sign_a * 0.325, 0.012, 0.930))

        # Muñeca anatómica en piel
        n_w = 8
        wrist_v = []
        for k in range(n_w):
            cang = (2.0 * math.pi * k) / n_w
            wx = sign_a * (0.325 + 0.020 * math.cos(cang))
            wy = w_center.y + 0.018 * math.sin(cang)
            wrist_v.append(bm.verts.new((wx, wy, 0.930)))

        # Palma y nudillos anatómicos
        z_knuckles = 0.850
        x_in = sign_a * (0.325 - 0.012)
        x_out = sign_a * (0.325 + 0.012)
        y_ant = w_center.y + 0.024
        y_post = w_center.y - 0.022

        p_box = [
            bm.verts.new((x_in,  y_ant,  0.900)),
            bm.verts.new((x_out, y_ant,  0.900)),
            bm.verts.new((x_out, y_post, 0.900)),
            bm.verts.new((x_in,  y_post, 0.900)),
            bm.verts.new((x_in,  y_ant,  z_knuckles)),
            bm.verts.new((x_out, y_ant,  z_knuckles)),
            bm.verts.new((x_out, y_post, z_knuckles)),
            bm.verts.new((x_in,  y_post, z_knuckles)),
        ]
        # Conectar muñeca con la caja de la palma (evitar huecos)
        for k in range(n_w):
            kn = (k + 1) % n_w
            # Asignar a la parte superior de p_box
            p_target1 = p_box[k % 4]
            p_target2 = p_box[kn % 4]
            bm.faces.new((wrist_v[k], wrist_v[kn], p_target2, p_target1)).material_index = 3

        f_p1 = bm.faces.new((p_box[0], p_box[1], p_box[5], p_box[4]))
        f_p2 = bm.faces.new((p_box[1], p_box[2], p_box[6], p_box[5]))
        f_p3 = bm.faces.new((p_box[2], p_box[3], p_box[7], p_box[6]))
        f_p4 = bm.faces.new((p_box[3], p_box[0], p_box[4], p_box[7]))
        for f in (f_p1, f_p2, f_p3, f_p4):
            f.material_index = 3 # Skin
            for loop in f.loops: loop[uv_lay].uv = (0.5, 0.5)

        # 4 Dedos estilizados en reposo relajado
        finger_specs = [
            ("Index",   w_center.y + 0.017, 0.055, 0.0062),
            ("Middle",  w_center.y + 0.005, 0.060, 0.0065),
            ("Ring",    w_center.y - 0.007, 0.054, 0.0060),
            ("Pinky",   w_center.y - 0.017, 0.044, 0.0055),
        ]
        for f_name, fy, f_len, f_rad in finger_specs:
            fx = sign_a * 0.325
            n_seg = 3
            prev_fring = None
            for s in range(n_seg + 1):
                t = s / float(n_seg)
                fz = z_knuckles - f_len * t
                cur_y = fy + 0.006 * (t**1.5)
                cur_x = fx + sign_a * 0.002 * t
                r_cur = f_rad * (1.0 - 0.30 * t)

                cur_fring = []
                for k in range(6):
                    fang = (2.0 * math.pi * k) / 6.0
                    cur_fring.append(bm.verts.new((cur_x + r_cur * math.cos(fang),
                                                  cur_y + r_cur * math.sin(fang),
                                                  fz)))
                if prev_fring:
                    for k in range(6):
                        knxt = (k + 1) % 6
                        ff = bm.faces.new((prev_fring[k], prev_fring[knxt], cur_fring[knxt], cur_fring[k]))
                        ff.material_index = 3
                        for loop in ff.loops: loop[uv_lay].uv = (0.5, 0.5)
                prev_fring = cur_fring

            tip_v = bm.verts.new((fx + sign_a * 0.002, fy + 0.007, z_knuckles - f_len - 0.003))
            for k in range(6):
                knxt = (k + 1) % 6
                ff_tip = bm.faces.new((prev_fring[knxt], prev_fring[k], tip_v))
                ff_tip.material_index = 3
                for loop in ff_tip.loops: loop[uv_lay].uv = (0.5, 0.5)

        # Pulgar en oposición anatómica
        th_root = Vector((sign_a * (0.325 - 0.012), w_center.y + 0.014, 0.885))
        n_tseg = 3
        prev_th = None
        for s in range(n_tseg + 1):
            t = s / float(n_tseg)
            tx = th_root.x - sign_a * 0.018 * t
            ty = th_root.y + 0.016 * t
            tz = th_root.z - 0.034 * t
            trad = 0.0070 * (1.0 - 0.25 * t)
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
                    for loop in thf.loops: loop[uv_lay].uv = (0.5, 0.5)
            prev_th = cur_th

        tip_th = bm.verts.new((th_root.x - sign_a * 0.020, th_root.y + 0.018, th_root.z - 0.038))
        for k in range(6):
            knxt = (k + 1) % 6
            thf_tip = bm.faces.new((prev_th[knxt], prev_th[k], tip_th))
            thf_tip.material_index = 3
            for loop in thf_tip.loops: loop[uv_lay].uv = (0.5, 0.5)

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
    """Asignación de pesos matemáticamente blindada contra fugas hacia las piernas."""
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
            # Transición suave cuello -> cabeza
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

            # TORSO Y COLUMNA (|X| <= 0.18 m o Z >= 0.82 m)
            else:
                if co.z < 0.95:
                    obj.vertex_groups["Hips"].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.00:
                    t = (co.z - 0.95) / 0.05
                    obj.vertex_groups["Hips"].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Spine"].add([v.index], t, 'REPLACE')
                elif co.z < 1.15:
                    obj.vertex_groups["Spine"].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.20:
                    t = (co.z - 1.15) / 0.05
                    obj.vertex_groups["Spine"].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Chest"].add([v.index], t, 'REPLACE')
                else:
                    obj.vertex_groups["Chest"].add([v.index], 1.0, 'REPLACE')

def attach_armature_modifier(obj, arm_obj):
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj
    obj.parent = arm_obj

# =============================================================================
# 4. RENDERS DE CONTROL MULTI-ÁNGULO (CYCLES CPU)
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

    # Iluminación de estudio
    add_light("KeyLight", 'AREA', 240.0, (0.3, 1.6, 1.6), color=(1.0, 0.98, 0.95))
    add_light("FillLight", 'AREA', 150.0, (-0.8, 1.4, 1.4), color=(0.95, 0.97, 1.0))
    add_light("RimLight", 'AREA', 220.0, (0.0, -1.6, 1.6), color=(1.0, 0.98, 0.95))

    cam_data = bpy.data.cameras.new("RenderCam")
    cam_data.lens = 65
    cam_obj = bpy.data.objects.new("RenderCam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    shots = [
        ("eli_preview.png",             ( 0.00,  1.70, 1.30), ( 0.00, 0.00, 1.30), os.path.join(PROJECT_ROOT, "godot_project/assets/characters/eli_preview.png")),
        ("eli_master_front.png",        ( 0.00,  2.20, 1.05), ( 0.00, 0.00, 1.05), os.path.join(SCRATCH_DIR, "eli_master_front.png")),
        ("eli_master_profile.png",      (-2.00,  0.00, 1.15), ( 0.00, 0.00, 1.15), os.path.join(SCRATCH_DIR, "eli_master_profile.png")),
        ("eli_master_back.png",         ( 0.00, -2.00, 1.15), ( 0.00, 0.00, 1.15), os.path.join(SCRATCH_DIR, "eli_master_back.png")),
        ("eli_master_threequarter.png", ( 1.20,  1.45, 1.20), ( 0.00, 0.00, 1.20), os.path.join(SCRATCH_DIR, "eli_master_threequarter.png")),
    ]

    for name, c_pos, t_pos, out_p in shots:
        cam_obj.location = Vector(c_pos)
        direction = Vector(t_pos) - Vector(c_pos)
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cam_obj.rotation_euler = rot_quat.to_euler()
        scene.render.filepath = out_p
        bpy.ops.render.render(write_still=True)
        print(f"✓ Vista de control guardada: {out_p}")

# =============================================================================
# 5. PIPELINE PRINCIPAL DE CONSTRUCCIÓN Y EXPORTACIÓN
# =============================================================================
def main():
    print("=" * 60)
    print("GENERANDO ELI CANÓNICO RECONSTRUIDO: CAMISA EN V Y VELLO PECTORAL")
    print("============================================================")

    bpy.ops.wm.read_factory_settings(use_empty=True)

    all_mats = create_materials()
    mat_groups = {
        "head": [
            all_mats["skin"],
            all_mats["eyes"],
            all_mats["hair"],
            all_mats["glasses"],
            all_mats["glass"],
            all_mats["teeth"]
        ],
        "body": [
            all_mats["shirt"],
            all_mats["pants"],
            all_mats["shoes"],
            all_mats["skin"],
            all_mats["chest"],
            all_mats["buttons"],
            all_mats["belt"],
            all_mats["buckle"]
        ]
    }

    # 1. Esqueleto canónico
    arm_obj = build_skeleton()
    print("✓ Armature canónico construido con 22 huesos.")

    # 2. Malla de Cabeza modular
    obj_head = build_head_mesh(mat_groups)
    assign_weights(obj_head, is_head=True)
    attach_armature_modifier(obj_head, arm_obj)
    print("✓ Player_Head_Mesh generado con gafas finas, ojos a Z=1.515, párpados con shape key 'blink' y cabello ondulado 360°.")

    # 3. Malla de Cuerpo modular
    obj_body = build_body_mesh(mat_groups)
    assign_weights(obj_body, is_head=False)
    attach_armature_modifier(obj_body, arm_obj)
    print("✓ Player_Body_Mesh generado con camisa resort en V, pecho con vello pectoral y chinos.")

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

    print("=" * 60)
    print("PROCESO ELI COMPLETADO EXITOSAMENTE")
    print("=" * 60)

if __name__ == "__main__":
    main()
