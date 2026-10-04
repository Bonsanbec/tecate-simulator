"""
=============================================================================
GENERADOR CANÓNICO PROCEDURAL DE ALTA FIDELIDAD: ELI (TECATE SIMULATOR)
=============================================================================
Reconstrucción fidedigna del personaje Eli basada en 'scratch/humans/eli.png':
1. Cabeza y Fisiología Facial:
   - Rostro masculino estilizado con mandíbula angulada, mentón firme y pómulos definidos.
   - Sonrisa amplia y cálida característica de Eli, con dientes blancos alineados visibles.
   - Ojos castaños cálidos estilizados con párpados anatómicos y Shape Key 'blink'.
   - Gafas rectangulares modernas de pasta fina negra con cristales transparentes diáfanos.
   - Cabellera castaño oscuro con masa volumétrica continua y textura ondulada 360°
     integrada armónicamente a la silueta del cráneo (sin protuberancias artificiales).
   - Texturas PBR faciales proyectadas frontalmente sin distorsiones cilíndricas.
2. Traje Sastre Formal Beige ("formal_beige"):
   - Malla corporal hermética generada mediante grafo antropométrico unificado
     (Skin + Subsurf), garantizando unión continua y orgánica en hombros, axilas,
     tórax, cadera y piernas.
   - Saco formal beige de lino/algodón con hombreras naturales, faldón sastre integrado,
     escote en V, solapas de muesca (notch lapels), 3 botones oscuros al frente y
     bolsillos de parche laterales adosados.
   - Camisa de vestir celeste pálido con cuello formal y puños asomando bajo las mangas.
   - Corbata de seda vino tinto / borgoña con micro-motas Jacquard.
   - Pantalón beige formal de corte recto a juego con el saco.
   - Zapatos Oxford de piel café oscuro / coñac pulido con suela fina formal.
   - Manos anatómicas de 5 dedos en reposo relajado con pulgar en oposición.
3. Arquitectura y Contratos de Rigging de Tecate Simulator:
   - Submallas modulares requeridas por CitizenEntity:
     * 'Player_Head_Mesh' (cabeza, ojos, gafas, cabello, dientes, párpados con blink)
     * 'Player_Body_Mesh' (traje, camisa, corbata, pantalón, zapatos y manos)
   - Esqueleto canónico 'Skeleton3D' con los 22 huesos antropométricos estándar.
   - Asignación de pesos sin fugas (0 vértices de manos asignados a piernas).
   - Exportación a 'eli.glb' y 'eli.blend'.
   - Renders de validación multi-ángulo con Cycles CPU.
=============================================================================
"""

import os
import math
import bpy
import bmesh
from mathutils import Vector, Matrix

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
ASSETS_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/citizens")
TEXTURES_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/textures")
SCRATCH_DIR = os.path.join(PROJECT_ROOT, "scratch")

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

def setup_pbr_material(name, diffuse_tex_path, normal_tex_path=None, base_color=(0.8, 0.8, 0.8, 1.0), roughness=0.6, metallic=0.0, transmission=0.0, alpha=1.0):
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
                                   base_color=(0.79, 0.62, 0.51, 1.0), roughness=0.52),
        "eyes": setup_pbr_material("Mat_Eli_Eyes",
                                   os.path.join(TEXTURES_DIR, "eli_eye_diffuse.png"),
                                   base_color=(0.96, 0.95, 0.94, 1.0), roughness=0.10),
        "hair": setup_pbr_material("Mat_Eli_Hair", None, None,
                                   base_color=(0.11, 0.08, 0.06, 1.0), roughness=0.72),
        "glasses": setup_pbr_material("Mat_Eli_Glasses",
                                      os.path.join(TEXTURES_DIR, "eli_glasses_diffuse.png"),
                                      base_color=(0.06, 0.06, 0.07, 1.0), roughness=0.25),
        "glass": setup_pbr_material("Mat_Eli_Glass", None, None,
                                    base_color=(0.95, 0.98, 1.0, 1.0), roughness=0.04, transmission=0.96, alpha=0.15),
        "teeth": setup_pbr_material("Mat_Eli_Teeth", None, None,
                                    base_color=(0.96, 0.95, 0.93, 1.0), roughness=0.20),
        "suit": setup_pbr_material("Mat_Eli_Suit",
                                   os.path.join(TEXTURES_DIR, "eli_suit_diffuse.png"),
                                   os.path.join(TEXTURES_DIR, "eli_suit_normal.png"),
                                   base_color=(0.83, 0.78, 0.71, 1.0), roughness=0.68),
        "pants": setup_pbr_material("Mat_Eli_Pants",
                                    os.path.join(TEXTURES_DIR, "eli_pants_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "eli_pants_normal.png"),
                                    base_color=(0.83, 0.78, 0.71, 1.0), roughness=0.68),
        "shirt": setup_pbr_material("Mat_Eli_Shirt",
                                    os.path.join(TEXTURES_DIR, "eli_shirt_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "eli_shirt_normal.png"),
                                    base_color=(0.91, 0.94, 0.97, 1.0), roughness=0.55),
        "tie": setup_pbr_material("Mat_Eli_Tie",
                                  os.path.join(TEXTURES_DIR, "eli_tie_diffuse.png"),
                                  os.path.join(TEXTURES_DIR, "eli_tie_normal.png"),
                                  base_color=(0.45, 0.08, 0.15, 1.0), roughness=0.38),
        "shoes": setup_pbr_material("Mat_Eli_Shoes",
                                    os.path.join(TEXTURES_DIR, "eli_shoes_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "eli_shoes_normal.png"),
                                    base_color=(0.22, 0.12, 0.08, 1.0), roughness=0.28),
        "buttons": setup_pbr_material("Mat_Eli_Buttons", None, None,
                                      base_color=(0.10, 0.08, 0.07, 1.0), roughness=0.30),
        "buckle": setup_pbr_material("Mat_Eli_Buckle", None, None,
                                     base_color=(0.78, 0.75, 0.65, 1.0), roughness=0.25, metallic=0.90),
    }
    return materials

# =============================================================================
# 1. CABEZA, ROSTRO, OJOS, GAFAS Y CABELLO (Player_Head_Mesh)
# =============================================================================
def build_head_mesh(materials):
    me = bpy.data.meshes.new("Player_Head_Mesh_Data")
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")

    # Mapeo UV frontal calibrado milimétricamente con la textura de piel, barba y bigote:
    def calc_face_uv(x, z):
        u = 0.50 + x / 0.275
        v = 0.50 + (z - 1.485) / 0.240
        return (max(0.0, min(1.0, u)), max(0.0, min(1.0, v)))

    # Perfil craneofacial estilizado de Eli (18 secciones transversales de Z=1.365 a Z=1.650)
    head_profile = [
        # z,      rx,    ry_front, ry_back, y_offset, is_face
        (1.365,  0.046, 0.045,    0.048,   -0.002,   False), # 0: Base cuello
        (1.390,  0.048, 0.046,    0.052,   -0.001,   False), # 1: Cuello medio
        (1.412,  0.052, 0.050,    0.060,    0.001,   True),  # 2: Submandíbula
        (1.428,  0.056, 0.062,    0.070,    0.005,   True),  # 3: Mentón con barba
        (1.445,  0.060, 0.062,    0.078,    0.004,   True),  # 4: Surco mentolabial
        (1.458,  0.063, 0.065,    0.084,    0.003,   True),  # 5: Labio inferior sonriente
        (1.468,  0.065, 0.064,    0.088,    0.002,   True),  # 6: Hendidura bucal abierta
        (1.478,  0.067, 0.067,    0.092,    0.002,   True),  # 7: Labio superior con bigote
        (1.492,  0.070, 0.066,    0.094,    0.001,   True),  # 8: Base nasal / Filtrum
        (1.505,  0.072, 0.074,    0.095,    0.000,   True),  # 9: Punta nasal
        (1.515,  0.074, 0.068,    0.095,    0.000,   True),  # 10: Ojos y puente nasal (Z = 1.515)
        (1.532,  0.075, 0.071,    0.094,   -0.002,   True),  # 11: Pómulos y cejas
        (1.550,  0.074, 0.068,    0.091,   -0.004,   True),  # 12: Sienes y frente baja
        (1.570,  0.072, 0.062,    0.087,   -0.006,   True),  # 13: Frente media
        (1.592,  0.068, 0.054,    0.080,   -0.008,   False), # 14: Nacimiento de cabello
        (1.615,  0.058, 0.044,    0.070,   -0.010,   False), # 15: Bóveda craneal
        (1.635,  0.038, 0.026,    0.045,   -0.012,   False), # 16: Coronilla
    ]

    n_ring = 24
    rings = []
    for l_idx, (z, rx, ry_f, ry_b, y_off, is_face) in enumerate(head_profile):
        cur_ring = []
        for i in range(n_ring):
            ang = (2.0 * math.pi * i) / n_ring
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            x = rx * cos_a
            y = (ry_f if sin_a >= 0 else ry_b) * sin_a + y_off

            # Modulaciones faciales anatómicas:
            # 1. Mentón angulado de Eli
            if l_idx == 3 and 0.44 * math.pi <= ang <= 0.56 * math.pi:
                y += 0.005 * math.cos((ang - 0.5 * math.pi) / 0.06 * (0.5 * math.pi))**2

            # 2. Sonrisa de Eli: apertura y comisuras vivas
            if l_idx in (5, 6, 7) and 0.38 * math.pi <= ang <= 0.62 * math.pi:
                sw = math.cos((ang - 0.5 * math.pi) / 0.12 * (0.5 * math.pi))**2
                if l_idx == 6:
                    y -= 0.004 * sw # Hendidura bucal abierta hacia adentro
                else:
                    y += 0.003 * sw

            # 3. Nariz recta de Eli
            if l_idx in (8, 9, 10) and 0.46 * math.pi <= ang <= 0.54 * math.pi:
                nw = math.cos((ang - 0.5 * math.pi) / 0.04 * (0.5 * math.pi))**2
                if l_idx == 9: y += 0.011 * nw
                elif l_idx in (8, 10): y += 0.004 * nw

            # 4. Cuencas orbitarias encastradas para recibir los ojos 3D
            if l_idx == 10 and (0.32 * math.pi <= ang <= 0.43 * math.pi or 0.57 * math.pi <= ang <= 0.68 * math.pi):
                y -= 0.008

            v = bm.verts.new((x, y, z))
            cur_ring.append(v)
        rings.append(cur_ring)

    # Construir caras y asignar UVs de la cabeza:
    for l_idx in range(len(head_profile) - 1):
        r1 = rings[l_idx]
        r2 = rings[l_idx + 1]
        z_mid = (head_profile[l_idx][0] + head_profile[l_idx + 1][0]) * 0.5
        for i in range(n_ring):
            inxt = (i + 1) % n_ring
            f = bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))

            ang_mid = (2.0 * math.pi * (i + 0.5)) / n_ring
            sin_mid = math.sin(ang_mid)
            # Cabello en el cráneo superior y posterior, piel en el rostro y cuello
            is_scalp = (z_mid >= 1.585) or (z_mid >= 1.44 and sin_mid < -0.15)
            f.material_index = 2 if is_scalp else 0 # 2: Hair, 0: Skin

            for loop in f.loops:
                loop_v = loop.vert
                loop[uv_lay].uv = calc_face_uv(loop_v.co.x, loop_v.co.z)

    # Coronilla superior
    top_vert = bm.verts.new((0.0, -0.012, 1.642))
    r_last = rings[-1]
    for i in range(n_ring):
        inxt = (i + 1) % n_ring
        f_top = bm.faces.new((r_last[i], r_last[inxt], top_vert))
        f_top.material_index = 2 # Hair
        for loop in f_top.loops:
            loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

    # Dientes superiores visibles en la sonrisa de Eli
    teeth_bm = bmesh.new()
    n_t = 10
    t_r = 0.022
    t_top, t_bot = [], []
    for k in range(n_t):
        ang_t = (k / float(n_t - 1) - 0.5) * 1.05
        tx = t_r * math.sin(ang_t)
        ty = 0.059 + t_r * (math.cos(ang_t) - 1.0) * 0.30
        t_top.append(teeth_bm.verts.new((tx, ty, 1.472)))
        t_bot.append(teeth_bm.verts.new((tx, ty, 1.464)))
    for k in range(n_t - 1):
        teeth_bm.faces.new((t_top[k], t_top[k+1], t_bot[k+1], t_bot[k])).material_index = 5 # Teeth
    v_map_t = {v: bm.verts.new(v.co) for v in teeth_bm.verts}
    for f in teeth_bm.faces:
        nf = bm.faces.new([v_map_t[v] for v in f.verts])
        nf.material_index = 5
        for loop in nf.loops:
            loop[uv_lay].uv = (0.5, 0.5)
    teeth_bm.free()

    # Globos oculares 3D a flor de piel (Z = 1.515, Y = 0.058, Radio = 0.0135)
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
                for loop in f.loops:
                    loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

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
            for loop in nf.loops:
                loop[uv_lay].uv = (0.5, 0.5)
        ear_bm.free()

    # -------------------------------------------------------------------------
    # GAFAS RECTANGULARES MODERNAS DE ACETATO NEGRO (scratch/humans/eli.png)
    # -------------------------------------------------------------------------
    glasses_bm = bmesh.new()
    frame_w = 0.0016
    frame_depth = 0.0015
    lens_hw = 0.0190
    lens_hh = 0.0125
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
            cos_a = math.copysign(abs(math.cos(ang))**0.80, math.cos(ang))
            sin_a = math.copysign(abs(math.sin(ang))**0.80, math.sin(ang))

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

        # Patillas ergonómicas hacia las orejas (horizontales limpias a Z = 1.515)
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
        glasses_bm.verts.new(( 0.014, lens_y + frame_depth * 0.4, lens_z + 0.0015)),
        glasses_bm.verts.new((-0.014, lens_y + frame_depth * 0.4, lens_z + 0.0015)),
        glasses_bm.verts.new((-0.014, lens_y - frame_depth * 0.4, lens_z - 0.0005)),
        glasses_bm.verts.new(( 0.014, lens_y - frame_depth * 0.4, lens_z - 0.0005)),
    ]
    glasses_bm.faces.new(bridge).material_index = 3

    v_map_g = {v: bm.verts.new(v.co) for v in glasses_bm.verts}
    for f in glasses_bm.faces:
        nf = bm.faces.new([v_map_g[v] for v in f.verts])
        nf.material_index = f.material_index
        for loop in nf.loops:
            loop[uv_lay].uv = (0.5, 0.5)
    glasses_bm.free()

    # -------------------------------------------------------------------------
    # CABELLERA ONDULADA ORGÁNICA INTEGRADA EN 360° (scratch/humans/eli.png)
    # -------------------------------------------------------------------------
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
            # Textura ondulada sutil en el cabello en 360°
            wave = 0.0030 * math.sin(hang * 4.0 + hz * 18.0) + 0.0015 * math.cos(hang * 6.0)
            # Ligero volumen superior en el tupé frontal
            tuft_boost = 0.0050 * math.cos((hang - 0.5 * math.pi) * 2.0)**2 if (hz >= 1.58 and 0.25 * math.pi <= hang <= 0.75 * math.pi) else 0.0
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

    # Shape Key: 'blink' para parpadeo biológico en Godot
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
# 2. CUERPO: GRAFO BASE HERMÉTICO (SKIN + SUBSURF), SOLAPAS, CAMISA Y MANOS
# =============================================================================
def build_body_mesh(materials):
    mesh_graph = bpy.data.meshes.new("Body_Graph_Data")
    obj_body = bpy.data.objects.new("Player_Body_Mesh", mesh_graph)
    bpy.context.scene.collection.objects.link(obj_body)

    # Grafo antropométrico continuo para Skin: hombros unidos orgánicamente,
    # torso sastre entallado, faldón continuo y piernas sin cortes.
    nodes = [
        # Tronco y Traje
        (0.00,  0.000, 0.82, 0.165, 0.116), # 0: Dobladillo inferior del saco
        (0.00,  0.002, 0.92, 0.160, 0.114), # 1: Caderas / faldón medio
        (0.00,  0.004, 1.04, 0.146, 0.104), # 2: Cintura entallada
        (0.00, -0.006, 1.16, 0.158, 0.114), # 3: Costillas / tórax medio
        (0.00, -0.008, 1.28, 0.174, 0.124), # 4: Pectorales y espalda
        (0.00, -0.004, 1.36, 0.160, 0.110), # 5: Clavículas / hombros
        (0.00,  0.004, 1.40, 0.052, 0.050), # 6: Base del cuello

        # Brazos unidos a clavículas (nodo 5)
        ( 0.06, -0.004, 1.36, 0.075, 0.075), # 7
        ( 0.185, -0.004, 1.34, 0.070, 0.070), # 8: Hombro L
        ( 0.265,  0.002, 1.15, 0.056, 0.056), # 9: Codo L
        ( 0.325,  0.012, 0.93, 0.044, 0.040), # 10: Bocamanga L

        (-0.06, -0.004, 1.36, 0.075, 0.075), # 11
        (-0.185, -0.004, 1.34, 0.070, 0.070), # 12: Hombro R
        (-0.265,  0.002, 1.15, 0.056, 0.056), # 13: Codo R
        (-0.325,  0.012, 0.93, 0.044, 0.040), # 14: Bocamanga R

        # Piernas unidas a la base de la pelvis (nodo 0)
        ( 0.088, 0.002, 0.82, 0.082, 0.082), # 15: Cadera / muslo sup L
        ( 0.088, 0.002, 0.65, 0.074, 0.074), # 16: Muslo medio L
        ( 0.088, 0.000, 0.48, 0.066, 0.066), # 17: Rodilla L
        ( 0.088, 0.000, 0.30, 0.058, 0.058), # 18: Pantorrilla L
        ( 0.088, 0.002, 0.12, 0.050, 0.050), # 19: Tobillo L
        ( 0.088, 0.055, 0.03, 0.052, 0.105), # 20: Pie L

        (-0.088, 0.002, 0.82, 0.082, 0.082), # 21: Cadera / muslo sup R
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
    # 0: Mat_Eli_Suit (Saco beige en torso y mangas)
    # 1: Mat_Eli_Pants (Pantalón beige en piernas)
    # 2: Mat_Eli_Shoes (Zapatos Oxford café en pies)
    for p in bm.faces:
        center_z = p.calc_center_median().z
        center_x = abs(p.calc_center_median().x)
        if center_z < 0.10:
            p.material_index = 2 # Zapatos
        elif center_z < 0.82 and center_x < 0.18:
            p.material_index = 1 # Pantalón
        else:
            p.material_index = 0 # Saco
        for loop in p.loops:
            loop[uv_lay].uv = (loop.vert.co.x * 2.0 + 0.5, loop.vert.co.z * 1.5)

    # -------------------------------------------------------------------------
    # ESCOTE EN V, CAMISA CELESTE, CORBATA VINO TINTO Y SOLAPAS DE MUESCA
    # -------------------------------------------------------------------------
    # Cuello de camisa sobresaliente
    c_wings = [
        [bm.verts.new(( 0.006, 0.058, 1.415)), bm.verts.new(( 0.048, 0.046, 1.410)), bm.verts.new(( 0.026, 0.076, 1.370))],
        [bm.verts.new((-0.006, 0.058, 1.415)), bm.verts.new((-0.026, 0.076, 1.370)), bm.verts.new((-0.048, 0.046, 1.410))],
    ]
    f_cw0 = bm.faces.new(c_wings[0])
    f_cw0.material_index = 3 # Shirt
    f_cw1 = bm.faces.new(c_wings[1])
    f_cw1.material_index = 3
    for f in (f_cw0, f_cw1):
        for loop in f.loops: loop[uv_lay].uv = (0.5, 0.5)

    # Pechera celeste formal en el escote en V del saco
    shirt_patch = [
        bm.verts.new(( 0.042, 0.095, 1.375)),
        bm.verts.new((-0.042, 0.095, 1.375)),
        bm.verts.new((-0.018, 0.126, 1.185)),
        bm.verts.new(( 0.018, 0.126, 1.185)),
    ]
    f_sp = bm.faces.new(shirt_patch)
    f_sp.material_index = 3 # Shirt
    for loop in f_sp.loops: loop[uv_lay].uv = (0.5, 0.5)

    # Corbata de seda vino tinto (Nudo y caída sastre)
    k_v = [
        bm.verts.new((-0.014, 0.072, 1.412)),
        bm.verts.new(( 0.014, 0.072, 1.412)),
        bm.verts.new(( 0.012, 0.098, 1.370)),
        bm.verts.new((-0.012, 0.098, 1.370)),
        bm.verts.new(( 0.000, 0.104, 1.392)),
    ]
    bm.faces.new((k_v[0], k_v[1], k_v[4])).material_index = 4 # Tie
    bm.faces.new((k_v[1], k_v[2], k_v[4])).material_index = 4
    bm.faces.new((k_v[2], k_v[3], k_v[4])).material_index = 4
    bm.faces.new((k_v[3], k_v[0], k_v[4])).material_index = 4

    tie_profile = [
        (1.370, 0.012, 0.098),
        (1.315, 0.015, 0.114),
        (1.255, 0.017, 0.124),
        (1.185, 0.016, 0.128),
        (1.115, 0.014, 0.122),
    ]
    tie_rows = [(k_v[3], k_v[2])]
    for tz, thw, ty_f in tie_profile[1:]:
        vl = bm.verts.new((-thw, ty_f, tz))
        vr = bm.verts.new(( thw, ty_f, tz))
        tie_rows.append((vl, vr))
    for idx in range(len(tie_rows) - 1):
        tl_a, tr_a = tie_rows[idx]
        tl_b, tr_b = tie_rows[idx + 1]
        tf = bm.faces.new((tl_a, tr_a, tr_b, tl_b))
        tf.material_index = 4
        for loop in tf.loops: loop[uv_lay].uv = (loop.vert.co.x * 5.0 + 0.5, (loop.vert.co.z - 1.1) * 3.5)

    # Solapas de muesca (Notch Lapels) del saco asentadas sobre el pecho
    for s_side in (1.0, -1.0):
        sgn = s_side
        v_col = bm.verts.new((sgn * 0.052, 0.090, 1.375))
        v_pek = bm.verts.new((sgn * 0.090, 0.114, 1.315))
        v_ntc = bm.verts.new((sgn * 0.074, 0.122, 1.295))
        v_stp = bm.verts.new((sgn * 0.084, 0.128, 1.275))
        v_bas = bm.verts.new((sgn * 0.018, 0.132, 1.185))
        v_inn = bm.verts.new((sgn * 0.038, 0.112, 1.265))

        if sgn > 0:
            bm.faces.new((v_col, v_pek, v_ntc)).material_index = 0 # Suit
            bm.faces.new((v_col, v_ntc, v_inn)).material_index = 0
            bm.faces.new((v_ntc, v_stp, v_bas)).material_index = 0
            bm.faces.new((v_ntc, v_bas, v_inn)).material_index = 0
        else:
            bm.faces.new((v_pek, v_col, v_ntc)).material_index = 0
            bm.faces.new((v_ntc, v_col, v_inn)).material_index = 0
            bm.faces.new((v_stp, v_ntc, v_bas)).material_index = 0
            bm.faces.new((v_bas, v_ntc, v_inn)).material_index = 0

    # 3 botones oscuros al frente del saco perfectamente adosados a la tela
    for bz in [1.170, 1.070, 0.970]:
        by = 0.122 + (1.170 - bz) * (-0.015)
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.0045)
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.0, by, bz))
        v_map_b = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            nf = bm.faces.new([v_map_b[v] for v in f.verts])
            nf.material_index = 5 # Buttons
            for loop in nf.loops: loop[uv_lay].uv = (0.5, 0.5)
        btn_bm.free()

    # Bolsillos de parche laterales en el saco adosados a la superficie
    for px_sign in (1.0, -1.0):
        px = px_sign * 0.092
        pz_c = 0.920
        pw, ph = 0.052, 0.062
        py = 0.096
        p_patch = [
            bm.verts.new((px - px_sign * pw*0.5, py + 0.001, pz_c + ph*0.5)),
            bm.verts.new((px + px_sign * pw*0.5, py - 0.003, pz_c + ph*0.5)),
            bm.verts.new((px + px_sign * pw*0.5, py - 0.003, pz_c - ph*0.5)),
            bm.verts.new((px - px_sign * pw*0.5, py + 0.001, pz_c - ph*0.5)),
        ]
        if px_sign > 0:
            bm.faces.new(p_patch).material_index = 0
        else:
            bm.faces.new(p_patch[::-1]).material_index = 0

    # -------------------------------------------------------------------------
    # BOCAMANGAS DEL SACO, PUÑOS CAMISEROS Y MANOS ANATÓMICAS
    # -------------------------------------------------------------------------
    for is_l in (True, False):
        sign_a = 1.0 if is_l else -1.0
        w_center = Vector((sign_a * 0.325, 0.015, 0.930))

        # Botones de la bocamanga del saco (adosados a la tela exterior)
        for b_idx in range(3):
            btn_sz = 0.942 - b_idx * 0.012
            btn_sx = sign_a * (0.325 + 0.036)
            b_bm = bmesh.new()
            bmesh.ops.create_uvsphere(b_bm, u_segments=6, v_segments=4, radius=0.0025)
            bmesh.ops.translate(b_bm, verts=b_bm.verts, vec=(btn_sx, w_center.y + 0.005, btn_sz))
            v_map_ab = {v: bm.verts.new(v.co) for v in b_bm.verts}
            for f in b_bm.faces:
                nf = bm.faces.new([v_map_ab[v] for v in f.verts])
                nf.material_index = 5 # Buttons
                for loop in nf.loops: loop[uv_lay].uv = (0.5, 0.5)
            b_bm.free()

        # Puño de camisa celeste asomando (1.5 cm) bajo la manga del saco
        n_arm = 12
        cuff_top, cuff_bot = [], []
        for k in range(n_arm):
            cang = (2.0 * math.pi * k) / n_arm
            cx = sign_a * (0.325 + 0.030 * math.cos(cang))
            cy = w_center.y + 0.026 * math.sin(cang)
            cuff_top.append(bm.verts.new((cx, cy, 0.930)))
            cuff_bot.append(bm.verts.new((cx * 1.01, cy * 1.01, 0.915)))
        for k in range(n_arm):
            knxt = (k + 1) % n_arm
            cf = bm.faces.new((cuff_top[k], cuff_top[knxt], cuff_bot[knxt], cuff_bot[k]))
            cf.material_index = 3 # Shirt
            for loop in cf.loops: loop[uv_lay].uv = (0.5, 0.5)

        # Muñeca anatómica en piel
        wrist_v = []
        for k in range(n_arm):
            cang = (2.0 * math.pi * k) / n_arm
            wx = sign_a * (0.325 + 0.022 * math.cos(cang))
            wy = w_center.y + 0.018 * math.sin(cang)
            wrist_v.append(bm.verts.new((wx, wy, 0.905)))
        for k in range(n_arm):
            knxt = (k + 1) % n_arm
            wf = bm.faces.new((wrist_v[k], wrist_v[knxt], cuff_bot[knxt], cuff_bot[k]))
            wf.material_index = 9 # Skin
            for loop in wf.loops: loop[uv_lay].uv = (0.5, 0.5)

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
        f_p1 = bm.faces.new((p_box[0], p_box[1], p_box[5], p_box[4]))
        f_p2 = bm.faces.new((p_box[1], p_box[2], p_box[6], p_box[5]))
        f_p3 = bm.faces.new((p_box[2], p_box[3], p_box[7], p_box[6]))
        f_p4 = bm.faces.new((p_box[3], p_box[0], p_box[4], p_box[7]))
        for f in (f_p1, f_p2, f_p3, f_p4):
            f.material_index = 9 # Skin
            for loop in f.loops: loop[uv_lay].uv = (0.5, 0.5)

        # 4 Dedos estilizados (Índice, Medio, Anular, Meñique) en postura relajada
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
                        ff.material_index = 9
                        for loop in ff.loops: loop[uv_lay].uv = (0.5, 0.5)
                prev_fring = cur_fring

            # Punta del dedo
            tip_v = bm.verts.new((fx + sign_a * 0.002, fy + 0.007, z_knuckles - f_len - 0.003))
            for k in range(6):
                knxt = (k + 1) % 6
                ff_tip = bm.faces.new((prev_fring[knxt], prev_fring[k], tip_v))
                ff_tip.material_index = 9
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
                    thf.material_index = 9
                    for loop in thf.loops: loop[uv_lay].uv = (0.5, 0.5)
            prev_th = cur_th

        tip_th = bm.verts.new((th_root.x - sign_a * 0.020, th_root.y + 0.018, th_root.z - 0.038))
        for k in range(6):
            knxt = (k + 1) % 6
            thf_tip = bm.faces.new((prev_th[knxt], prev_th[k], tip_th))
            thf_tip.material_index = 9
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

    # Iluminación de estudio
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

    # Key light frontal-alta suave, fill suave y rim para recortar silueta
    add_light("KeyLight", 'AREA', 220.0, (0.4, 1.6, 1.6), color=(1.0, 0.97, 0.94))
    add_light("FillLight", 'AREA', 140.0, (-0.8, 1.4, 1.4), color=(0.94, 0.96, 1.0))
    add_light("RimLight", 'AREA', 200.0, (0.0, -1.6, 1.6), color=(1.0, 0.98, 0.95))

    # Cámara
    cam_data = bpy.data.cameras.new("RenderCam")
    cam_data.lens = 65
    cam_obj = bpy.data.objects.new("RenderCam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    shots = [
        ("eli_preview.png",             ( 0.00,  1.75, 1.25), ( 0.00, 0.00, 1.25), os.path.join(PROJECT_ROOT, "godot_project/assets/characters/eli_preview.png")),
        ("eli_master_front.png",        ( 0.00,  1.75, 1.25), ( 0.00, 0.00, 1.25), os.path.join(SCRATCH_DIR, "eli_master_front.png")),
        ("eli_master_profile.png",      (-1.75,  0.00, 1.25), ( 0.00, 0.00, 1.25), os.path.join(SCRATCH_DIR, "eli_master_profile.png")),
        ("eli_master_back.png",         ( 0.00, -1.75, 1.25), ( 0.00, 0.00, 1.25), os.path.join(SCRATCH_DIR, "eli_master_back.png")),
        ("eli_master_threequarter.png", ( 1.15,  1.35, 1.30), ( 0.00, 0.00, 1.25), os.path.join(SCRATCH_DIR, "eli_master_threequarter.png")),
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
    print("GENERANDO ELI CANÓNICO RECONSTRUIDO: ALTA CALIDAD Y PARECIDO REAL")
    print("=" * 60)

    # Limpiar escena inicial
    bpy.ops.wm.read_factory_settings(use_empty=True)

    all_mats = create_materials()
    mat_groups = {
        "head": [all_mats["skin"], all_mats["eyes"], all_mats["hair"], all_mats["glasses"], all_mats["glass"], all_mats["teeth"]],
        "body": [all_mats["suit"], all_mats["pants"], all_mats["shoes"], all_mats["shirt"], all_mats["tie"], all_mats["buttons"], all_mats["buckle"], all_mats["suit"], all_mats["suit"], all_mats["skin"]]
    }

    # 1. Esqueleto canónico
    arm_obj = build_skeleton()
    print("✓ Armature canónico construido con 22 huesos.")

    # 2. Malla de Cabeza modular
    obj_head = build_head_mesh(mat_groups)
    assign_weights(obj_head, is_head=True)
    attach_armature_modifier(obj_head, arm_obj)
    print("✓ Player_Head_Mesh generado con gafas finas, ojos a Z=1.515, párpados con shape key 'blink' y cabello 360°.")

    # 3. Malla de Cuerpo modular
    obj_body = build_body_mesh(mat_groups)
    assign_weights(obj_body, is_head=False)
    attach_armature_modifier(obj_body, arm_obj)
    print("✓ Player_Body_Mesh generado con traje formal beige continuo, solapas y manos anatómicas.")

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
    blend_path = os.path.join(ASSETS_DIR, "eli.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"✓ Guardado .blend en: {blend_path}")

    # Exportar archivo .glb canónico
    glb_path = os.path.join(ASSETS_DIR, "eli.glb")
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
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
    print(f"✓ Exportado .glb canónico en: {glb_path}")

    # Renders de validación multi-ángulo
    render_control_views()

    print("=" * 60)
    print("PROCESO ELI COMPLETADO EXITOSAMENTE")
    print("=" * 60)

if __name__ == "__main__":
    main()
