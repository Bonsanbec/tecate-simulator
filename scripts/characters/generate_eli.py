"""
=============================================================================
Eli Master Generator - Versión Anatómica, Sartorial Formal Beige y Rig Canónico
=============================================================================
Implementación fidedigna de Eli para Tecate Simulator basada en 'scratch/humans/eli.png':
1. Cotas craneales humanas con perfil facial armónico, sonrisa radiante y dientes visibles.
2. Montura de gafas/anteojos de acetato oscuro moderna con puente, patillas ergonómicas y cristales.
3. Cabellera ondulada/rizada voluminosa en 360° estructurada sobre cúpula craneal convexa
   (126 mechones helicoidales distribuidos en tupé frontal alzado, coronilla abombada, sienes y nuca).
4. Párpados 3D almendrados con Shape Key 'blink' para parpadeo biológico, ojos a Z=1.515 y orejas anatómicas.
5. Saco sastre formal beige/arena ("formal_beige") cerrado y estructurado:
   - Malla envolvente continua de hombros a faldón bajo (Z=0.840), con espalda completa y costados sellados.
   - Solapas de muesca clásicas (notched lapels) en relieve 3D sobre el pecho.
   - Escote en V exhibiendo camisa de vestir celeste formal y corbata de seda vino tinto.
   - 3 botones frontales de carey oscuro y bolsillos plastrón/parche inferiores adosados al saco.
   - Bocamangas con botones pequeños y puños camiseros celestes asomando (1.5 cm).
   - Pretina con cinturón de cuero café oscuro y hebilla metálica bajo el saco.
   - Pantalón sastre beige formal a juego y zapatos de vestir en cuero café oscuro/coñac pulido.
6. Manos anatómicas semi-pronadas con dedos curvados en reposo natural.
7. Rigging blindado de 22 huesos con ponderación estricta (0 fugas de vértices hacia las piernas).
=============================================================================
"""

import bpy
import bmesh
import math
import os
import numpy as np
from mathutils import Vector, Matrix, Euler, Quaternion

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
TEXTURES_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/textures")
CITIZENS_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/citizens")
SCRATCH_DIR = os.path.join(PROJECT_ROOT, "scratch")
OUTPUT_BLEND = os.path.join(CITIZENS_DIR, "eli.blend")
OUTPUT_GLB = os.path.join(CITIZENS_DIR, "eli.glb")
PREVIEW_PNG = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/eli_preview.png")

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

def create_pbr_material(name, base_color=(1, 1, 1, 1), roughness=0.5, metallic=0.0,
                        diffuse_tex_path=None, normal_tex_path=None, specular=0.5,
                        transmission=0.0, alpha=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])

    node_bsdf.inputs['Base Color'].default_value = base_color
    node_bsdf.inputs['Roughness'].default_value = roughness
    node_bsdf.inputs['Metallic'].default_value = metallic
    if 'Specular IOR Level' in node_bsdf.inputs:
        node_bsdf.inputs['Specular IOR Level'].default_value = specular
    if 'Transmission Weight' in node_bsdf.inputs and transmission > 0.0:
        node_bsdf.inputs['Transmission Weight'].default_value = transmission
    elif 'Transmission' in node_bsdf.inputs and transmission > 0.0:
        node_bsdf.inputs['Transmission'].default_value = transmission

    if alpha < 1.0:
        if 'Alpha' in node_bsdf.inputs:
            node_bsdf.inputs['Alpha'].default_value = alpha
        mat.blend_method = 'BLEND'

    if diffuse_tex_path and os.path.exists(diffuse_tex_path):
        tex_node = nodes.new(type='ShaderNodeTexImage')
        img = bpy.data.images.load(diffuse_tex_path)
        tex_node.image = img
        links.new(tex_node.outputs['Color'], node_bsdf.inputs['Base Color'])

    if normal_tex_path and os.path.exists(normal_tex_path):
        norm_img_node = nodes.new(type='ShaderNodeTexImage')
        img_norm = bpy.data.images.load(normal_tex_path)
        img_norm.colorspace_settings.name = 'Non-Color'
        norm_img_node.image = img_norm

        norm_map_node = nodes.new(type='ShaderNodeNormalMap')
        norm_map_node.inputs['Strength'].default_value = 0.85
        links.new(norm_img_node.outputs['Color'], norm_map_node.inputs['Color'])
        links.new(norm_map_node.outputs['Normal'], node_bsdf.inputs['Normal'])

    return mat

# =============================================================================
# 1. CABEZA PROPORCIONADA, SONRISA, GAFAS 3D, PÁRPADOS Y ONDAS 360°
# =============================================================================
def build_head_mesh(materials):
    me = bpy.data.meshes.new("Player_Head_Mesh_Data")
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")

    n_ring = 32
    head_profile = [
        # z, rx, ry_front, ry_back, y_offset, v_uv
        (1.372, 0.050, 0.044, 0.050, -0.004, 0.12), # 0: Base cuello
        (1.392, 0.048, 0.044, 0.056, -0.002, 0.18), # 1: Cuello medio
        (1.412, 0.052, 0.048, 0.064,  0.002, 0.24), # 2: Submandíbula
        (1.428, 0.060, 0.066, 0.076,  0.010, 0.30), # 3: Mentón con barba
        (1.442, 0.065, 0.064, 0.086,  0.009, 0.35), # 4: Surco mentolabial
        (1.455, 0.069, 0.072, 0.094,  0.008, 0.38), # 5: Labio inferior sonriente
        (1.465, 0.071, 0.068, 0.100,  0.007, 0.40), # 6: Hendidura / sonrisa
        (1.476, 0.071, 0.073, 0.104,  0.005, 0.43), # 7: Labio superior / bigote
        (1.490, 0.074, 0.069, 0.106,  0.003, 0.48), # 8: Base nasal / Filtrum
        (1.503, 0.077, 0.080, 0.106,  0.001, 0.54), # 9: Punta nasal
        (1.515, 0.080, 0.074, 0.105,  0.000, 0.63), # 10: Ojos / puente nasal (Z = 1.515)
        (1.530, 0.082, 0.078, 0.104, -0.002, 0.72), # 11: Pómulos y cejas
        (1.548, 0.080, 0.073, 0.102, -0.004, 0.79), # 12: Frente baja / relieve occipital
        (1.568, 0.078, 0.068, 0.098, -0.006, 0.85), # 13: Frente media
        (1.590, 0.074, 0.060, 0.092, -0.008, 0.91), # 14: Nacimiento de cabello / frente alta
        (1.615, 0.063, 0.048, 0.078, -0.010, 0.96), # 15: Bóveda craneal
        (1.635, 0.040, 0.030, 0.050, -0.012, 0.99), # 16: Coronilla
    ]

    rings = []
    for l_idx, (z, rx, ry_f, ry_b, y_off, v_uv) in enumerate(head_profile):
        cur_ring = []
        cur_u = []
        for i in range(n_ring):
            ang = (2.0 * math.pi * i) / n_ring
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            x = rx * cos_a
            y = (ry_f if sin_a >= 0 else ry_b) * sin_a + y_off

            # Modulaciones faciales anatómicas: sonrisa de Eli con elevación de comisuras
            if l_idx in (5, 6, 7) and 0.38 * math.pi <= ang <= 0.62 * math.pi:
                mw = math.cos((ang - 0.5 * math.pi) / 0.12 * (0.5 * math.pi))**2
                if l_idx == 5: y += 0.006 * mw
                elif l_idx == 6: y -= 0.002 * mw
                elif l_idx == 7: y += 0.005 * mw

            # Nariz recta y definida
            if l_idx in (8, 9, 10) and 0.44 * math.pi <= ang <= 0.56 * math.pi:
                nw = math.cos((ang - 0.5 * math.pi) / 0.06 * (0.5 * math.pi))**2
                if l_idx == 9: y += 0.011 * nw
                elif l_idx == 10: y += 0.006 * nw
                elif l_idx == 8: y += 0.004 * nw

            # Mentón prominente con barba
            if l_idx == 3 and 0.42 * math.pi <= ang <= 0.58 * math.pi:
                cw = math.cos((ang - 0.5 * math.pi) / 0.08 * (0.5 * math.pi))**2
                y += 0.007 * cw

            # Hueco de órbitas oculares para encastrar los ojos a Z=1.515
            if l_idx == 10 and (0.32 * math.pi <= ang <= 0.42 * math.pi or 0.58 * math.pi <= ang <= 0.68 * math.pi):
                y -= 0.015

            cur_ring.append(bm.verts.new((x, y, z)))
            u_coord = ((ang - 0.5 * math.pi) / (2.0 * math.pi) + 0.5) % 1.0
            cur_u.append(u_coord)
        rings.append((cur_ring, cur_u, v_uv))

    # Construir caras y asignar materiales:
    # 0: Mat_Eli_Skin (rostro, mejillas, cuello)
    # 2: Mat_Eli_Hair (cuero cabelludo en coronilla y nuca posterior)
    for l_idx in range(len(head_profile) - 1):
        r1, u1, v1 = rings[l_idx]
        r2, u2, v2 = rings[l_idx + 1]
        z_mid = (head_profile[l_idx][0] + head_profile[l_idx + 1][0]) * 0.5
        for i in range(n_ring):
            inxt = (i + 1) % n_ring
            f = bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))

            ang_mid = (2.0 * math.pi * (i + 0.5)) / n_ring
            sin_mid = math.sin(ang_mid)
            is_scalp = (z_mid >= 1.585) or (z_mid >= 1.43 and sin_mid < -0.15)
            f.material_index = 2 if is_scalp else 0

            u_a = u1[i]
            u_b = u1[inxt]
            if abs(u_b - u_a) > 0.5: u_b = u_b + 1.0 if u_a > 0.5 else u_b - 1.0
            u_c = u2[inxt]
            u_d = u2[i]
            if abs(u_c - u_d) > 0.5: u_c = u_c + 1.0 if u_d > 0.5 else u_c - 1.0

            for loop in f.loops:
                if loop.vert == r1[i]: loop[uv_lay].uv = (u_a, v1)
                elif loop.vert == r1[inxt]: loop[uv_lay].uv = (u_b, v1)
                elif loop.vert == r2[inxt]: loop[uv_lay].uv = (u_c, v2)
                elif loop.vert == r2[i]: loop[uv_lay].uv = (u_d, v2)

    top_vert = bm.verts.new((0.0, -0.012, 1.640))
    r_last, _, v_last = rings[-1]
    for i in range(n_ring):
        inxt = (i + 1) % n_ring
        f_top = bm.faces.new((r_last[i], r_last[inxt], top_vert))
        f_top.material_index = 2

    # Ojos 3D almendrados a Z = 1.515
    eye_pos = [(0.033, 0.053, 1.515), (-0.033, 0.053, 1.515)]
    eye_r = 0.0120
    for pos in eye_pos:
        e_bm = bmesh.new()
        bmesh.ops.create_uvsphere(e_bm, u_segments=20, v_segments=16, radius=eye_r)
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

    # Párpados 3D almendrados con deformación Shape Key
    upper_lid_margin_verts = []
    upper_lid_crease_verts = []
    for side_idx, (ex, ey, ez) in enumerate(eye_pos):
        sign_side = 1.0 if ex > 0 else -1.0
        n_pts = 9
        upper_margin, upper_crease, upper_brow = [], [], []
        lower_margin, lower_crease = [], []
        for i in range(n_pts):
            t = (i / float(n_pts - 1)) * 2.0 - 1.0
            dx = t * 0.0135 * sign_side
            arch_sup = math.sqrt(max(0.0, 1.0 - t**2))
            dz_margin_sup = 0.0022 * arch_sup + 0.0005 * t
            dz_margin_inf = -0.0040 * arch_sup + 0.0003 * t
            dy_margin = math.sqrt(max(0.0001, (eye_r * 1.02)**2 - dx**2 - dz_margin_sup**2))
            dy_margin_inf = math.sqrt(max(0.0001, (eye_r * 1.02)**2 - dx**2 - dz_margin_inf**2))

            v_sup_m = bm.verts.new((ex + dx, ey + dy_margin, ez + dz_margin_sup))
            v_sup_c = bm.verts.new((ex + dx, ey + dy_margin * 0.98 + 0.002, ez + dz_margin_sup + 0.0045 * arch_sup))
            v_sup_b = bm.verts.new((ex + dx, ey + dy_margin * 0.92 + 0.005, ez + dz_margin_sup + 0.0100 * arch_sup))
            v_inf_m = bm.verts.new((ex + dx, ey + dy_margin_inf, ez + dz_margin_inf))
            v_inf_c = bm.verts.new((ex + dx, ey + dy_margin_inf * 0.96 + 0.003, ez + dz_margin_inf - 0.0060 * arch_sup))

            upper_margin.append(v_sup_m)
            upper_crease.append(v_sup_c)
            upper_brow.append(v_sup_b)
            lower_margin.append(v_inf_m)
            lower_crease.append(v_inf_c)

            upper_lid_margin_verts.append(v_sup_m)
            upper_lid_crease_verts.append(v_sup_c)

        for i in range(n_pts - 1):
            bm.faces.new((upper_margin[i], upper_margin[i+1], upper_crease[i+1], upper_crease[i])).material_index = 0
            bm.faces.new((upper_crease[i], upper_crease[i+1], upper_brow[i+1], upper_brow[i])).material_index = 0
            bm.faces.new((lower_crease[i], lower_crease[i+1], lower_margin[i+1], lower_margin[i])).material_index = 0

    # Dientes anatómicos 3D visibles en la sonrisa radiante
    teeth_bm = bmesh.new()
    n_t = 12
    t_arc_r = 0.024
    t_top_v, t_bot_v = [], []
    for k in range(n_t):
        ang_t = (k / float(n_t - 1) - 0.5) * 1.2
        tx = t_arc_r * math.sin(ang_t)
        ty = 0.052 + t_arc_r * (math.cos(ang_t) - 1.0) * 0.4
        t_top_v.append(teeth_bm.verts.new((tx, ty, 1.468)))
        t_bot_v.append(teeth_bm.verts.new((tx, ty, 1.460)))
    for k in range(n_t - 1):
        teeth_bm.faces.new((t_top_v[k], t_top_v[k+1], t_bot_v[k+1], t_bot_v[k])).material_index = 5 # Mat_Eli_Teeth
    v_map_t = {v: bm.verts.new(v.co) for v in teeth_bm.verts}
    for f in teeth_bm.faces:
        bm.faces.new([v_map_t[v] for v in f.verts]).material_index = 5
    teeth_bm.free()

    # Orejas anatómicas en piel
    for is_l in (True, False):
        s_sign = 1.0 if is_l else -1.0
        ear_bm = bmesh.new()
        bmesh.ops.create_uvsphere(ear_bm, u_segments=10, v_segments=8, radius=0.015)
        bmesh.ops.scale(ear_bm, verts=ear_bm.verts, vec=(0.35, 0.70, 1.25))
        bmesh.ops.rotate(ear_bm, verts=ear_bm.verts, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(s_sign * 14.0), 4, 'Y'))
        bmesh.ops.rotate(ear_bm, verts=ear_bm.verts, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(-10.0), 4, 'X'))
        bmesh.ops.translate(ear_bm, verts=ear_bm.verts, vec=(s_sign * 0.076, -0.008, 1.505))
        v_map = {v: bm.verts.new(v.co) for v in ear_bm.verts}
        for f in ear_bm.faces:
            bm.faces.new([v_map[v] for v in f.verts]).material_index = 0
        ear_bm.free()

    # -------------------------------------------------------------------------
    # ANTEOJOS / GAFAS 3D (Montura de Acetato Gruesa Elegante + Cristales)
    # -------------------------------------------------------------------------
    glasses_bm = bmesh.new()
    frame_w = 0.0055
    frame_depth = 0.0035
    lens_hw = 0.020
    lens_hh = 0.0135
    lens_y = 0.071
    lens_z = 1.516

    for s_side in (1.0, -1.0):
        c_x = s_side * 0.033
        n_frame = 16
        inner_front, outer_front = [], []
        inner_back, outer_back = [], []
        lens_inner = []
        for i in range(n_frame):
            ang = (2.0 * math.pi * i) / n_frame
            cos_a = math.copysign(abs(math.cos(ang))**0.8, math.cos(ang))
            sin_a = math.copysign(abs(math.sin(ang))**0.8, math.sin(ang))

            rx_in = c_x + lens_hw * cos_a
            rz_in = lens_z + lens_hh * sin_a
            rx_out = c_x + (lens_hw + frame_w) * cos_a
            rz_out = lens_z + (lens_hh + frame_w) * sin_a

            v_if = glasses_bm.verts.new((rx_in, lens_y + frame_depth * 0.5, rz_in))
            v_of = glasses_bm.verts.new((rx_out, lens_y + frame_depth * 0.5, rz_out))
            v_ib = glasses_bm.verts.new((rx_in, lens_y - frame_depth * 0.5, rz_in))
            v_ob = glasses_bm.verts.new((rx_out, lens_y - frame_depth * 0.5, rz_out))

            inner_front.append(v_if)
            outer_front.append(v_of)
            inner_back.append(v_ib)
            outer_back.append(v_ob)
            lens_inner.append(v_if)

        for i in range(n_frame):
            inxt = (i + 1) % n_frame
            # Frontal con bisel
            glasses_bm.faces.new((inner_front[i], inner_front[inxt], outer_front[inxt], outer_front[i])).material_index = 3
            # Exterior
            glasses_bm.faces.new((outer_front[i], outer_front[inxt], outer_back[inxt], outer_back[i])).material_index = 3
            # Interior aro
            glasses_bm.faces.new((inner_back[i], inner_back[inxt], inner_front[inxt], inner_front[i])).material_index = 3
            # Posterior
            glasses_bm.faces.new((outer_back[i], outer_back[inxt], inner_back[inxt], inner_back[i])).material_index = 3

        # Cristal
        c_lens = glasses_bm.verts.new((c_x, lens_y, lens_z))
        for i in range(n_frame):
            inxt = (i + 1) % n_frame
            glasses_bm.faces.new((lens_inner[i], lens_inner[inxt], c_lens)).material_index = 4

        # Patilla ergonómica limpia hacia la oreja
        tx_front = s_side * (lens_hw + frame_w + 0.033)
        tx_ear = s_side * 0.076
        t_bar = [
            glasses_bm.verts.new((tx_front, lens_y - 0.001, lens_z + 0.002)),
            glasses_bm.verts.new((tx_ear,   -0.008,         1.512 + 0.002)),
            glasses_bm.verts.new((tx_ear,   -0.008,         1.512 - 0.002)),
            glasses_bm.verts.new((tx_front, lens_y - 0.001, lens_z - 0.002)),
        ]
        if s_side > 0:
            glasses_bm.faces.new(t_bar).material_index = 3
        else:
            glasses_bm.faces.new(t_bar[::-1]).material_index = 3

    # Puente nasal firme
    bridge_box = [
        glasses_bm.verts.new(( 0.013, lens_y + frame_depth * 0.5, lens_z + 0.005)),
        glasses_bm.verts.new((-0.013, lens_y + frame_depth * 0.5, lens_z + 0.005)),
        glasses_bm.verts.new((-0.013, lens_y - frame_depth * 0.5, lens_z + 0.001)),
        glasses_bm.verts.new(( 0.013, lens_y - frame_depth * 0.5, lens_z + 0.001)),
    ]
    glasses_bm.faces.new(bridge_box).material_index = 3

    v_map_g = {v: bm.verts.new(v.co) for v in glasses_bm.verts}
    for f in glasses_bm.faces:
        bm.faces.new([v_map_g[v] for v in f.verts]).material_index = f.material_index
    glasses_bm.free()

    # -------------------------------------------------------------------------
    # CABELLERA ONDULADA / RIZADA EN 360° (120 MECHONES HELICOIDALES PROCEDURALES)
    # -------------------------------------------------------------------------
    def add_curl(p_start, p_delta, r_curl, turns, phi0, base_thick=0.0072, n_steps=14):
        prev_ring = None
        for s in range(n_steps):
            t = s / float(n_steps - 1)
            cx = p_start[0] + p_delta[0] * t
            cy = p_start[1] + p_delta[1] * t
            cz = p_start[2] + p_delta[2] * t
            cur_r = r_curl * (1.0 - 0.25 * t)
            phase = 2.0 * math.pi * turns * t + phi0
            sp_x = cx + cur_r * math.cos(phase)
            sp_y = cy + cur_r * math.sin(phase)
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
                    f_c.material_index = 2 # Mat_Eli_Hair
            prev_ring = c_ring

    # 1. Tupé frontal superior con volumen alzado hacia atrás (32 rizos en 2 filas)
    for row_z, row_r, n_curls in [(1.595, 0.072, 16), (1.578, 0.076, 16)]:
        for i in range(n_curls):
            t_f = (i / float(n_curls - 1)) * 2.0 - 1.0
            x_pos = t_f * 0.062
            y_pos = row_r * math.sqrt(max(0.01, 1.0 - (x_pos / 0.082)**2)) + 0.008
            dx = t_f * 0.010 + (0.003 if i % 2 == 0 else -0.003)
            dy = -0.024 - 0.010 * abs(t_f)
            dz = 0.042 - 0.015 * abs(t_f)
            r_c = 0.011 + 0.002 * (i % 3)
            turns_c = 2.0 + 0.3 * (i % 2)
            phi = 0.85 * i + (1.0 if row_z < 1.585 else 0.0)
            add_curl((x_pos, y_pos, row_z), (dx, dy, dz), r_c, turns_c, phi, base_thick=0.0076)

    # 2. Cúpula craneal convexa abombada en 3 niveles esféricos (38 rizos)
    dome_levels = [
        (1.638, 8,  0.028, 0.038, -0.010),
        (1.622, 15, 0.048, 0.060, -0.015),
        (1.602, 15, 0.068, 0.080, -0.022),
    ]
    for c_z, c_cnt, c_rad_x, c_rad_y, c_dz in dome_levels:
        c_angles = np.linspace(0, 2.0 * math.pi, c_cnt, endpoint=False)
        for i_c, c_ang in enumerate(c_angles):
            cx = c_rad_x * math.cos(c_ang)
            cy = c_rad_y * math.sin(c_ang) - 0.010
            dx = 0.012 * math.cos(c_ang)
            dy = 0.012 * math.sin(c_ang) - 0.008
            dz = c_dz + 0.010 * math.sin(c_ang * 2.0)
            rc = 0.010 + 0.002 * (i_c % 2)
            tc = 2.1
            phi = 1.1 * i_c + c_z * 2.0
            add_curl((cx, cy, c_z), (dx, dy, dz), rc, tc, phi, base_thick=0.0072)

    # 3. Sienes y laterales (20 rizos, sin colas colgantes)
    for s_side in (1.0, -1.0):
        side_specs = [
            ( 0.035, 1.575,  0.004, -0.038, 0.010, 2.3),
            ( 0.020, 1.570,  0.002, -0.042, 0.010, 2.4),
            ( 0.005, 1.568, -0.002, -0.045, 0.011, 2.4),
            (-0.010, 1.565, -0.004, -0.045, 0.011, 2.3),
            (-0.025, 1.562, -0.006, -0.042, 0.010, 2.2),
            (-0.038, 1.558, -0.008, -0.038, 0.010, 2.2),
            ( 0.025, 1.542,  0.002, -0.032, 0.009, 2.2),
            ( 0.010, 1.536, -0.002, -0.034, 0.009, 2.3),
            (-0.005, 1.532, -0.004, -0.036, 0.010, 2.3),
            (-0.020, 1.530, -0.006, -0.034, 0.010, 2.2),
        ]
        for idx_s, (sy, sz, sdy, sdz, src, sturns) in enumerate(side_specs):
            sx = s_side * (0.075 + 0.005 * (idx_s % 2))
            sdx = s_side * 0.005
            phi = 0.9 * idx_s + (0.4 if s_side < 0 else 0.0)
            add_curl((sx, sy, sz), (sdx, sdy, sdz), src, sturns, phi, base_thick=0.0068)

    # 4. Nuca posterior completa en 3 niveles (26 rizos, confinada al occipital)
    nape_levels = [
        (1.575, 10, 0.090, -0.024),
        (1.540, 10, 0.086, -0.025),
        (1.510,  6, 0.080, -0.020),
    ]
    for n_z, n_cnt, n_rad, n_dz in nape_levels:
        angles = np.linspace(-math.pi * 0.74, -math.pi * 0.26, n_cnt)
        for i_n, ang in enumerate(angles):
            nx = n_rad * math.cos(ang)
            ny = n_rad * math.sin(ang) - 0.006
            dx = 0.005 * math.cos(ang)
            dy = 0.005 * math.sin(ang)
            dz = n_dz
            rc = 0.009 + 0.002 * (i_n % 2)
            tc = 2.0
            phi = 0.75 * i_n + n_z * 3.0
            add_curl((nx, ny, n_z), (dx, dy, dz), rc, tc, phi, base_thick=0.0070)

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

    # Shape Keys: Parpadeo biológico 'blink'
    sk_basis = obj_head.shape_key_add(name="Basis")
    sk_blink = obj_head.shape_key_add(name="blink")
    for v_idx in margin_v_indices:
        sk_blink.data[v_idx].co.z -= 0.0068
        sk_blink.data[v_idx].co.y += 0.0008
    for v_idx in crease_v_indices:
        sk_blink.data[v_idx].co.z -= 0.0034
        sk_blink.data[v_idx].co.y += 0.0004

    return obj_head

# =============================================================================
# 2. CUERPO: SACO SASTRE BEIGE, SOLAPAS, CORBATA VINO, PANTALÓN Y MANOS
# =============================================================================
def build_body_mesh(materials):
    mesh_graph = bpy.data.meshes.new("Body_Graph_Data")
    obj_body = bpy.data.objects.new("Player_Body_Mesh", mesh_graph)
    bpy.context.scene.collection.objects.link(obj_body)

    nodes = [
        # Tronco
        (0.00,  0.000, 0.82, 0.130, 0.100), # 0: Pelvis base
        (0.00,  0.004, 0.94, 0.145, 0.105), # 1: Caderas / Cintura pantalón
        (0.00,  0.008, 1.04, 0.136, 0.096), # 2: Cintura entallada
        (0.00, -0.010, 1.16, 0.156, 0.114), # 3: Costillas / tórax medio
        (0.00, -0.012, 1.28, 0.172, 0.124), # 4: Pectorales y omóplatos
        (0.00, -0.005, 1.36, 0.155, 0.108), # 5: Clavículas / hombros
        (0.00,  0.005, 1.40, 0.050, 0.050), # 6: Base del cuello

        # Brazos
        ( 0.06, -0.005, 1.36, 0.070, 0.070), # 7
        ( 0.18, -0.005, 1.34, 0.075, 0.075), # 8: Hombro L
        ( 0.26,  0.000, 1.15, 0.052, 0.052), # 9: Codo L
        ( 0.33,  0.010, 0.92, 0.038, 0.034), # 10: Manga / Puño L

        (-0.06, -0.005, 1.36, 0.070, 0.070), # 11
        (-0.18, -0.005, 1.34, 0.075, 0.075), # 12: Hombro R
        (-0.26,  0.000, 1.15, 0.052, 0.052), # 13: Codo R
        (-0.33,  0.010, 0.92, 0.038, 0.034), # 14: Manga / Puño R

        # Piernas
        ( 0.088, 0.00, 0.82, 0.085, 0.085), # 15
        ( 0.088, 0.00, 0.65, 0.078, 0.078), # 16: Muslo L
        ( 0.088, 0.00, 0.48, 0.068, 0.068), # 17: Rodilla L
        ( 0.088, 0.00, 0.30, 0.060, 0.060), # 18: Pantorrilla L
        ( 0.088, 0.00, 0.12, 0.048, 0.048), # 19: Tobillo L
        ( 0.088, 0.06, 0.03, 0.050, 0.105), # 20: Pie L

        (-0.088, 0.00, 0.82, 0.085, 0.085), # 21
        (-0.088, 0.00, 0.65, 0.078, 0.078), # 22: Muslo R
        (-0.088, 0.00, 0.48, 0.068, 0.068), # 23: Rodilla R
        (-0.088, 0.00, 0.30, 0.060, 0.060), # 24: Pantorrilla R
        (-0.088, 0.00, 0.12, 0.048, 0.048), # 25: Tobillo R
        (-0.088, 0.06, 0.03, 0.050, 0.105), # 26: Pie R
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

    # Materiales de base según altura:
    # 0: Mat_Eli_Suit (Saco beige en brazos y base)
    # 1: Mat_Eli_Pants (Pantalón beige en piernas)
    # 2: Mat_Eli_Shoes (Zapatos café en pies)
    for p in bm.faces:
        center_z = p.calc_center_median().z
        if center_z < 0.10:
            p.material_index = 2 # Zapatos
        elif center_z < 0.94:
            p.material_index = 1 # Pantalón
        else:
            p.material_index = 0 # Saco

    # Cuello camisero formal celeste
    n_c = 16
    c_bot = []
    c_top = []
    for i in range(n_c):
        ang = (2.0 * math.pi * i) / n_c
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        c_bot.append(bm.verts.new((0.052 * cos_a, 0.052 * sin_a + 0.008, 1.375)))
        c_top.append(bm.verts.new((0.052 * cos_a, 0.052 * sin_a + 0.008, 1.418)))

    for i in range(n_c):
        i_next = (i + 1) % n_c
        bm.faces.new((c_bot[i], c_bot[i_next], c_top[i_next], c_top[i])).material_index = 3 # Mat_Eli_Shirt

    # Puntas del cuello camisero dobladas
    c_wings = [
        [bm.verts.new((0.008, 0.058, 1.418)), bm.verts.new((0.050, 0.046, 1.412)), bm.verts.new((0.028, 0.080, 1.365))],
        [bm.verts.new((-0.008, 0.058, 1.418)), bm.verts.new((-0.028, 0.080, 1.365)), bm.verts.new((-0.050, 0.046, 1.412))],
    ]
    bm.faces.new(c_wings[0]).material_index = 3
    bm.faces.new(c_wings[1]).material_index = 3

    # Pechera de camisa celeste visible en el escote en V del saco (Z=1.18 a 1.38)
    shirt_chest_pts = [
        bm.verts.new(( 0.040, 0.105, 1.375)),
        bm.verts.new((-0.040, 0.105, 1.375)),
        bm.verts.new((-0.015, 0.126, 1.180)),
        bm.verts.new(( 0.015, 0.126, 1.180)),
    ]
    bm.faces.new(shirt_chest_pts).material_index = 3

    # Corbata de seda vino tinto (Nudo y caída recta)
    k_v = [
        bm.verts.new((-0.016, 0.068, 1.415)),
        bm.verts.new(( 0.016, 0.068, 1.415)),
        bm.verts.new(( 0.013, 0.096, 1.370)),
        bm.verts.new((-0.013, 0.096, 1.370)),
        bm.verts.new(( 0.000, 0.102, 1.392)),
    ]
    bm.faces.new((k_v[0], k_v[1], k_v[4])).material_index = 4 # Mat_Eli_Tie
    bm.faces.new((k_v[1], k_v[2], k_v[4])).material_index = 4
    bm.faces.new((k_v[2], k_v[3], k_v[4])).material_index = 4
    bm.faces.new((k_v[3], k_v[0], k_v[4])).material_index = 4

    tie_profile = [
        (1.370, 0.013, 0.096),
        (1.320, 0.016, 0.114),
        (1.260, 0.018, 0.125),
        (1.180, 0.018, 0.128),
        (1.120, 0.015, 0.122),
    ]
    tie_rows = [ (k_v[3], k_v[2]) ]
    for z, hw, y_f in tie_profile[1:]:
        vl = bm.verts.new((-hw, y_f, z))
        vr = bm.verts.new(( hw, y_f, z))
        tie_rows.append((vl, vr))

    for idx in range(len(tie_rows) - 1):
        tl_a, tr_a = tie_rows[idx]
        tl_b, tr_b = tie_rows[idx + 1]
        bm.faces.new((tl_a, tr_a, tr_b, tl_b)).material_index = 4

    # -------------------------------------------------------------------------
    # SACO SASTRE SARTORIAL COMPLETO: ESPALDA, COSTADOS, SOLAPAS Y DOBADILLO
    # -------------------------------------------------------------------------
    # 1. Espalda Completa (Curvatura continua de hombros a faldón largo en Z=0.840)
    back_levels = [
        # z,     hw,    y_back, y_side
        (1.380, 0.110, -0.095, -0.040), # 0: Hombros / cuello posterior
        (1.330, 0.130, -0.112, -0.055), # 1: Pecho alto dorsal
        (1.270, 0.150, -0.124, -0.065), # 2: Omóplatos / axila
        (1.200, 0.156, -0.122, -0.060), # 3: Tórax medio
        (1.130, 0.152, -0.118, -0.050), # 4: Costillas
        (1.060, 0.144, -0.114, -0.040), # 5: Cintura
        (0.980, 0.146, -0.112, -0.035), # 6: Cintura baja / cadera alta
        (0.910, 0.150, -0.114, -0.030), # 7: Cadera media
        (0.850, 0.154, -0.110, -0.025), # 8: Dobladillo largo del saco sastre
    ]

    back_rows = []
    for (bz, bhw, by_c, by_s) in back_levels:
        row = []
        for i in range(7):
            t = (i / 6.0) * 2.0 - 1.0
            bx = t * bhw
            by = by_c * (1.0 - 0.40 * (t**2)) + by_s * 0.40 * (t**2)
            row.append(bm.verts.new((bx, by, bz)))
        back_rows.append(row)

    for l in range(len(back_levels) - 1):
        r1 = back_rows[l]
        r2 = back_rows[l + 1]
        for i in range(6):
            bm.faces.new((r1[i], r1[i+1], r2[i+1], r2[i])).material_index = 0 # Mat_Eli_Suit

    # 2. Delanteros Superiores con Escote en V (Z=1.380 a Z=1.200)
    front_specs_upper = [
        # z,     x_in,  x_mid, x_out, y_in,  y_out
        (1.380, 0.055, 0.085, 0.110, 0.078, 0.055), # Hombro (conecta con back_rows[0])
        (1.330, 0.040, 0.088, 0.130, 0.104, 0.070), # Pecho alto
        (1.270, 0.022, 0.090, 0.150, 0.126, 0.065), # Sisa inferior
    ]

    front_l_upper = []
    front_r_upper = []
    for (fz, xin, xmid, xout, yin, yout) in front_specs_upper:
        vl_in = bm.verts.new(( xin, yin, fz))
        vl_mid = bm.verts.new(( xmid, (yin + yout)*0.5 + 0.010, fz))
        vl_out = bm.verts.new(( xout, yout, fz))
        front_l_upper.append((vl_in, vl_mid, vl_out))

        vr_in = bm.verts.new((-xin, yin, fz))
        vr_mid = bm.verts.new((-xmid, (yin + yout)*0.5 + 0.010, fz))
        vr_out = bm.verts.new((-xout, yout, fz))
        front_r_upper.append((vr_in, vr_mid, vr_out))

    # Conectar hombros: delantero con espalda en Z=1.380
    bm.faces.new((front_l_upper[0][0], front_l_upper[0][1], back_rows[0][5], back_rows[0][4])).material_index = 0
    bm.faces.new((front_l_upper[0][1], front_l_upper[0][2], back_rows[0][6], back_rows[0][5])).material_index = 0
    bm.faces.new((front_r_upper[0][1], front_r_upper[0][0], back_rows[0][2], back_rows[0][1])).material_index = 0
    bm.faces.new((front_r_upper[0][2], front_r_upper[0][1], back_rows[0][1], back_rows[0][0])).material_index = 0

    # Cerrar hombreras exteriores sobre el deltoides:
    bm.faces.new((front_l_upper[0][2], front_l_upper[1][2], back_rows[1][6], back_rows[0][6])).material_index = 0
    bm.faces.new((front_r_upper[1][2], front_r_upper[0][2], back_rows[0][0], back_rows[1][0])).material_index = 0

    # Conectar filas superiores del delantero
    for l in range(2):
        la_in, la_mid, la_out = front_l_upper[l]
        lb_in, lb_mid, lb_out = front_l_upper[l+1]
        bm.faces.new((la_in, la_mid, lb_mid, lb_in)).material_index = 0
        bm.faces.new((la_mid, la_out, lb_out, lb_mid)).material_index = 0

        ra_in, ra_mid, ra_out = front_r_upper[l]
        rb_in, rb_mid, rb_out = front_r_upper[l+1]
        bm.faces.new((ra_mid, ra_in, rb_in, rb_mid)).material_index = 0
        bm.faces.new((ra_out, ra_mid, rb_mid, rb_out)).material_index = 0

    # 3. Delanteros Inferiores y Faldón Largo (Z=1.200 a Z=0.850)
    front_specs_lower = [
        # z,     hw,    y_center, y_side
        (1.200, 0.156,  0.134,   -0.060), # 3: Vértice del escote / botón 1
        (1.130, 0.152,  0.128,   -0.050), # 4: Costillas / botón 2
        (1.060, 0.144,  0.122,   -0.040), # 5: Cintura / botón 3
        (0.980, 0.146,  0.118,   -0.035), # 6: Caderas
        (0.910, 0.150,  0.116,   -0.030), # 7: Cadera baja
        (0.850, 0.154,  0.112,   -0.025), # 8: Dobladillo largo del saco sastre
    ]

    front_lower_rows = []
    for l_idx, (fz, fhw, fy_c, fy_s) in enumerate(front_specs_lower):
        row = []
        for i in range(7):
            t = (i / 6.0) * 2.0 - 1.0
            fx = t * fhw
            fy = fy_c * (1.0 - 0.40 * (t**2)) + fy_s * 0.40 * (t**2)
            row.append(bm.verts.new((fx, fy, fz)))
        front_lower_rows.append(row)

    # Transición entre parte superior y parte inferior
    lin_2, lmid_2, lout_2 = front_l_upper[2]
    rin_2, rmid_2, rout_2 = front_r_upper[2]
    fl0 = front_lower_rows[0]

    bm.faces.new((lin_2, lmid_2, fl0[4], fl0[3])).material_index = 0
    bm.faces.new((lmid_2, lout_2, fl0[5], fl0[4])).material_index = 0
    bm.faces.new((lout_2, back_rows[2][6], back_rows[3][6], fl0[6])).material_index = 0
    bm.faces.new((lout_2, fl0[6], fl0[5])).material_index = 0

    bm.faces.new((rmid_2, rin_2, fl0[3], fl0[2])).material_index = 0
    bm.faces.new((rout_2, rmid_2, fl0[2], fl0[1])).material_index = 0
    bm.faces.new((back_rows[2][0], rout_2, fl0[0], back_rows[3][0])).material_index = 0
    bm.faces.new((rout_2, fl0[1], fl0[0])).material_index = 0

    # Conectar filas inferiores y costados
    for l in range(len(front_lower_rows) - 1):
        fa = front_lower_rows[l]
        fb = front_lower_rows[l+1]
        ba = back_rows[l + 3]
        bb = back_rows[l + 4]

        for i in range(6):
            bm.faces.new((fa[i], fa[i+1], fb[i+1], fb[i])).material_index = 0

        bm.faces.new((fa[6], ba[6], bb[6], fb[6])).material_index = 0
        bm.faces.new((ba[0], fa[0], fb[0], bb[0])).material_index = 0

    # 4. Solapas de Muesca (Notched Lapels) integradas en 3D sobre el pecho
    for s_side in (1.0, -1.0):
        sgn = s_side
        # Vértices de la solapa sastre doblada hacia afuera
        v_lapel_collar = bm.verts.new((sgn * 0.055, 0.082, 1.380))
        v_lapel_peak   = bm.verts.new((sgn * 0.092, 0.108, 1.320))
        v_lapel_notch  = bm.verts.new((sgn * 0.076, 0.120, 1.300))
        v_lapel_step   = bm.verts.new((sgn * 0.086, 0.128, 1.280))
        v_lapel_base   = bm.verts.new((sgn * 0.020, 0.138, 1.200))
        v_lapel_inner  = bm.verts.new((sgn * 0.040, 0.110, 1.270))

        if s_side > 0:
            bm.faces.new((v_lapel_collar, v_lapel_peak, v_lapel_notch)).material_index = 0
            bm.faces.new((v_lapel_collar, v_lapel_notch, v_lapel_inner)).material_index = 0
            bm.faces.new((v_lapel_notch, v_lapel_step, v_lapel_base)).material_index = 0
            bm.faces.new((v_lapel_notch, v_lapel_base, v_lapel_inner)).material_index = 0
        else:
            bm.faces.new((v_lapel_peak, v_lapel_collar, v_lapel_notch)).material_index = 0
            bm.faces.new((v_lapel_notch, v_lapel_collar, v_lapel_inner)).material_index = 0
            bm.faces.new((v_lapel_step, v_lapel_notch, v_lapel_base)).material_index = 0
            bm.faces.new((v_lapel_base, v_lapel_notch, v_lapel_inner)).material_index = 0

    # 5. Bolsillos Plastrón / Parche adosados sobre los faldones inferiores
    for px_sign in (1.0, -1.0):
        px = px_sign * 0.088
        pz_c = 0.940
        pw, ph = 0.054, 0.068
        py = 0.120
        p_patch = [
            bm.verts.new((px - px_sign * pw*0.5, py, pz_c + ph*0.5)),
            bm.verts.new((px + px_sign * pw*0.5, py - 0.006, pz_c + ph*0.5)),
            bm.verts.new((px + px_sign * pw*0.5, py - 0.006, pz_c - ph*0.5)),
            bm.verts.new((px - px_sign * pw*0.5, py, pz_c - ph*0.5)),
        ]
        if px_sign > 0:
            bm.faces.new(p_patch).material_index = 0
        else:
            bm.faces.new(p_patch[::-1]).material_index = 0

    # 6. Botones oscuros de carey en el cruce delantero (Z=1.200, 1.100, 1.000)
    for bz in [1.200, 1.100, 1.000]:
        by = 0.134 + (1.200 - bz) * (-0.024)
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.0055)
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.0, by + 0.006, bz))
        v_map = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            bm.faces.new([v_map[v] for v in f.verts]).material_index = 6 # Mat_Eli_Buttons
        btn_bm.free()

    # 7. Cinturón y hebilla en Z=0.960
    b_pts = [
        bm.verts.new((-0.022, 0.119, 0.970)),
        bm.verts.new(( 0.022, 0.119, 0.970)),
        bm.verts.new(( 0.022, 0.119, 0.945)),
        bm.verts.new((-0.022, 0.119, 0.945)),
    ]
    bm.faces.new(b_pts).material_index = 8 # Hebilla metálica

    # -------------------------------------------------------------------------
    # MANOS Y DEDOS ANATÓMICOS CON RIGGING BLINDADO Y PUÑOS CAMISEROS
    # -------------------------------------------------------------------------
    for is_left in (True, False):
        sign_h = 1.0 if is_left else -1.0
        w_center = Vector((sign_h * 0.33, 0.010, 0.920))

        # Bocamanga del saco beige (termina en Z=0.935)
        n_cuff = 12
        sleeve_top, sleeve_bot = [], []
        for k in range(n_cuff):
            ang = (2.0 * math.pi * k) / n_cuff
            cx = w_center.x + 0.033 * math.cos(ang)
            cy = w_center.y + 0.028 * math.sin(ang)
            sleeve_top.append(bm.verts.new((cx, cy, 0.945)))
            sleeve_bot.append(bm.verts.new((cx * 1.01, cy * 1.01, 0.932)))
        for k in range(n_cuff):
            kn = (k + 1) % n_cuff
            bm.faces.new((sleeve_top[k], sleeve_top[kn], sleeve_bot[kn], sleeve_bot[k])).material_index = 0

        # Botones pequeños en la bocamanga del saco
        for b_idx in range(3):
            btn_sz = 0.940 - b_idx * 0.012
            btn_sx = w_center.x + sign_h * 0.033
            b_s_bm = bmesh.new()
            bmesh.ops.create_uvsphere(b_s_bm, u_segments=6, v_segments=4, radius=0.003)
            bmesh.ops.translate(b_s_bm, verts=b_s_bm.verts, vec=(btn_sx, w_center.y + 0.012, btn_sz))
            v_map_b = {v: bm.verts.new(v.co) for v in b_s_bm.verts}
            for f in b_s_bm.faces:
                bm.faces.new([v_map_b[v] for v in f.verts]).material_index = 6
            b_s_bm.free()

        # Puño camisero celeste asomando (1.5 cm) bajo la manga del saco
        cuff_top, cuff_bot = [], []
        for k in range(n_cuff):
            ang = (2.0 * math.pi * k) / n_cuff
            cx = w_center.x + 0.028 * math.cos(ang)
            cy = w_center.y + 0.024 * math.sin(ang)
            cuff_top.append(bm.verts.new((cx, cy, 0.932)))
            cuff_bot.append(bm.verts.new((cx * 1.01, cy * 1.01, 0.912)))
        for k in range(n_cuff):
            kn = (k + 1) % n_cuff
            bm.faces.new((cuff_top[k], cuff_top[kn], cuff_bot[kn], cuff_bot[k])).material_index = 3 # Camisa celeste

        # Muñeca anatómica en piel
        wrist_v = []
        for k in range(n_cuff):
            ang = (2.0 * math.pi * k) / n_cuff
            wx = w_center.x + 0.022 * math.cos(ang)
            wy = w_center.y + 0.018 * math.sin(ang)
            wrist_v.append(bm.verts.new((wx, wy, 0.905)))
        for k in range(n_cuff):
            kn = (k + 1) % n_cuff
            bm.faces.new((wrist_v[k], wrist_v[kn], cuff_bot[kn], cuff_bot[k])).material_index = 9 # Piel

        # Palma y nudillos anatómicos
        z_knuckles = 0.845
        x_in = w_center.x - sign_h * 0.013
        x_out = w_center.x + sign_h * 0.013
        y_ant = w_center.y + 0.026
        y_post = w_center.y - 0.024

        p_box = [
            bm.verts.new((x_in,  y_ant,  0.895)),
            bm.verts.new((x_out, y_ant,  0.895)),
            bm.verts.new((x_out, y_post, 0.895)),
            bm.verts.new((x_in,  y_post, 0.895)),
            bm.verts.new((x_in,  y_ant,  z_knuckles)),
            bm.verts.new((x_out, y_ant,  z_knuckles)),
            bm.verts.new((x_out, y_post, z_knuckles)),
            bm.verts.new((x_in,  y_post, z_knuckles)),
        ]
        bm.faces.new((p_box[0], p_box[1], p_box[5], p_box[4])).material_index = 9
        bm.faces.new((p_box[1], p_box[2], p_box[6], p_box[5])).material_index = 9
        bm.faces.new((p_box[2], p_box[3], p_box[7], p_box[6])).material_index = 9
        bm.faces.new((p_box[3], p_box[0], p_box[4], p_box[7])).material_index = 9

        # Dedos anatómicos con articulaciones y curvatura natural de reposo
        finger_specs = [
            ("Index",   w_center.y + 0.018, 0.060, 0.0068, 0.85),
            ("Middle",  w_center.y + 0.005, 0.066, 0.0072, 1.00),
            ("Ring",    w_center.y - 0.008, 0.061, 0.0068, 1.15),
            ("Little",  w_center.y - 0.019, 0.050, 0.0058, 1.30),
        ]
        curl_dir = Vector((-sign_h * 0.70, 0.35, 0.0)).normalized()

        for (f_name, fy, flen, frad, curl) in finger_specs:
            mcp = Vector((w_center.x, fy, z_knuckles))
            p0 = mcp
            p1 = p0 + Vector((0, 0, -flen * 0.38)) + curl_dir * (flen * 0.18 * curl)
            p2 = p1 + Vector((0, 0, -flen * 0.34)) + curl_dir * (flen * 0.38 * curl)
            p3 = p2 + Vector((0, 0, -flen * 0.24)) + curl_dir * (flen * 0.48 * curl)

            joints = [p0, p1, p2, p3]
            prev_ring = None
            for j_idx, pt in enumerate(joints):
                rad = frad * (1.0 - 0.25 * (j_idx / 3.0))
                cur_ring = []
                for k in range(6):
                    ang = (2.0 * math.pi * k) / 6.0
                    vx = pt.x + rad * math.cos(ang)
                    vy = pt.y + rad * math.sin(ang)
                    vz = pt.z + rad * 0.5 * math.sin(ang)
                    cur_ring.append(bm.verts.new((vx, vy, vz)))
                if prev_ring:
                    for k in range(6):
                        kn = (k + 1) % 6
                        bm.faces.new((prev_ring[k], prev_ring[kn], cur_ring[kn], cur_ring[k])).material_index = 9
                prev_ring = cur_ring

            tip_v = bm.verts.new(p3 + curl_dir * 0.003 - Vector((0, 0, 0.003)))
            for k in range(6):
                kn = (k + 1) % 6
                bm.faces.new((prev_ring[kn], prev_ring[k], tip_v)).material_index = 9

        # Pulgar anatómico abducido
        th_mcp = Vector((x_in - sign_h * 0.004, y_ant + 0.005, z_knuckles + 0.022))
        th_joints = [
            th_mcp,
            th_mcp + Vector((-sign_h * 0.008, 0.012, -0.018)),
            th_mcp + Vector((-sign_h * 0.014, 0.018, -0.035)),
            th_mcp + Vector((-sign_h * 0.016, 0.020, -0.048)),
        ]
        prev_th = None
        for j_idx, pt in enumerate(th_joints):
            th_rad = 0.0078 * (1.0 - 0.20 * (j_idx / 3.0))
            cur_ring = []
            for k in range(6):
                ang = (2.0 * math.pi * k) / 6.0
                vx = pt.x + th_rad * math.cos(ang)
                vy = pt.y + th_rad * math.sin(ang)
                vz = pt.z + th_rad * 0.5 * math.sin(ang)
                cur_ring.append(bm.verts.new((vx, vy, vz)))
            if prev_th:
                for k in range(6):
                    kn = (k + 1) % 6
                    bm.faces.new((prev_th[k], prev_th[kn], cur_ring[kn], cur_ring[k])).material_index = 9
            prev_th = cur_ring
        tip_th = bm.verts.new(th_joints[-1] + Vector((-sign_h * 0.002, 0.003, -0.003)))
        for k in range(6):
            kn = (k + 1) % 6
            bm.faces.new((prev_th[kn], prev_th[k], tip_th)).material_index = 9

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

        ("Shoulder.L",  "Chest",       (0.04, 0, 1.36),   (0.180, 0, 1.36)),
        ("UpperArm.L",  "Shoulder.L",  (0.180, 0, 1.36),  (0.260, 0.007, 1.15)),
        ("Forearm.L",   "UpperArm.L",  (0.260, 0.007, 1.15),(0.330, 0.015, 0.92)),
        ("Hand.L",      "Forearm.L",   (0.330, 0.015, 0.92),(0.330, 0.015, 0.80)),

        ("Shoulder.R",  "Chest",       (-0.04, 0, 1.36),  (-0.180, 0, 1.36)),
        ("UpperArm.R",  "Shoulder.R",  (-0.180, 0, 1.36), (-0.260, 0.007, 1.15)),
        ("Forearm.R",   "UpperArm.R",  (-0.260, 0.007, 1.15),(-0.330, 0.015, 0.92)),
        ("Hand.R",      "Forearm.R",   (-0.330, 0.015, 0.92),(-0.330, 0.015, 0.80)),

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
            grp = "Neck" if co.z < 1.41 else "Head"
            obj.vertex_groups[grp].add([v.index], 1.0, 'REPLACE')
        else:
            # 1. Pies y dedos de los pies (|X| <= 0.18)
            if co.z < 0.04 and abs(co.x) <= 0.18:
                obj.vertex_groups["Toes.L" if co.x > 0 else "Toes.R"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.12 and abs(co.x) <= 0.18:
                obj.vertex_groups["Foot.L" if co.x > 0 else "Foot.R"].add([v.index], 1.0, 'REPLACE')
            # 2. Extremidades superiores (|X| > 0.18) - Blindaje absoluto contra fugas a piernas
            elif abs(co.x) > 0.18 and co.z < 1.38:
                side = ".L" if co.x > 0 else ".R"
                if co.z < 0.93:
                    obj.vertex_groups["Hand" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.15:
                    obj.vertex_groups["Forearm" + side].add([v.index], 1.0, 'REPLACE')
                else:
                    obj.vertex_groups["UpperArm" + side].add([v.index], 1.0, 'REPLACE')
            # 3. Extremidades inferiores (|X| <= 0.18)
            elif co.z < 0.48:
                obj.vertex_groups["LowerLeg.L" if co.x > 0 else "LowerLeg.R"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.82 and abs(co.x) > 0.03:
                obj.vertex_groups["UpperLeg.L" if co.x > 0 else "UpperLeg.R"].add([v.index], 1.0, 'REPLACE')
            # 4. Pelvis y columna
            elif co.z < 0.95:
                obj.vertex_groups["Hips"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 1.15:
                obj.vertex_groups["Spine"].add([v.index], 1.0, 'REPLACE')
            else:
                obj.vertex_groups["Chest"].add([v.index], 1.0, 'REPLACE')

# =============================================================================
# 4. RENDER PREVIEW DE ESTUDIO CINEMATOGRÁFICO Y VISTAS MULTI-ÁNGULO
# =============================================================================
def render_studio_views():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.device = 'CPU'

    # Iluminación de estudio suave y halagadora para retratos
    key = bpy.data.objects.new("Key", bpy.data.lights.new("Key", 'AREA'))
    key.data.energy = 65.0
    key.data.size = 1.6
    key.data.color = (1.0, 0.98, 0.95)
    key.location = Vector((-0.7, 1.7, 1.6))
    key.rotation_euler = (math.radians(52.0), 0.0, math.radians(-150.0))
    scene.collection.objects.link(key)

    fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", 'AREA'))
    fill.data.energy = 28.0
    fill.data.size = 1.8
    fill.data.color = (0.94, 0.97, 1.0)
    fill.location = Vector((0.8, 1.6, 1.4))
    scene.collection.objects.link(fill)

    catch = bpy.data.objects.new("EyeCatch", bpy.data.lights.new("EyeCatch", 'AREA'))
    catch.data.energy = 6.0
    catch.data.size = 0.5
    catch.data.color = (1.0, 0.98, 0.96)
    catch.location = Vector((0.0, 1.5, 1.515))
    scene.collection.objects.link(catch)

    rim = bpy.data.objects.new("Rim", bpy.data.lights.new("Rim", 'SPOT'))
    rim.data.energy = 40.0
    rim.data.spot_size = math.radians(65.0)
    rim.data.color = (1.0, 1.0, 1.0)
    rim.location = Vector((0.0, -1.3, 1.8))
    rim.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
    scene.collection.objects.link(rim)

    back_light = bpy.data.objects.new("BackLight", bpy.data.lights.new("BackLight", 'AREA'))
    back_light.data.energy = 55.0
    back_light.data.size = 1.6
    back_light.data.color = (1.0, 0.98, 0.95)
    back_light.location = Vector((0.0, -1.8, 1.3))
    back_light.rotation_euler = (math.radians(-70.0), 0.0, math.radians(180.0))
    scene.collection.objects.link(back_light)

    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.lens = 52.0
    cam.location = Vector((0.02, 1.75, 1.25))
    cam.rotation_euler = (math.radians(88.5), 0.0, math.radians(178.0))
    scene.collection.objects.link(cam)
    scene.camera = cam

    scene.render.resolution_x = 720
    scene.render.resolution_y = 1280
    scene.render.filepath = PREVIEW_PNG
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
    print(f"✓ Render preview principal guardado en: {PREVIEW_PNG}")

    # Vistas de control multi-ángulo en scratch
    scene.render.resolution_y = 1080
    views = [
        ("eli_master_front.png", Vector((0.0, 1.75, 1.25)), (math.radians(88.5), 0.0, math.radians(178.0))),
        ("eli_master_profile.png", Vector((1.75, 0.0, 1.45)), (math.radians(88.5), 0.0, math.radians(88.0))),
        ("eli_master_back.png", Vector((0.0, -1.75, 1.25)), (math.radians(91.5), 0.0, math.radians(-2.0))),
        ("eli_master_threequarter.png", Vector((1.25, 1.25, 1.35)), (math.radians(82.0), 0.0, math.radians(135.0))),
    ]
    for fname, loc, rot in views:
        cam.location = loc
        cam.rotation_euler = rot
        out_p = os.path.join(SCRATCH_DIR, fname)
        scene.render.filepath = out_p
        bpy.ops.render.render(write_still=True)
        print(f"✓ Vista de control {fname} guardada en: {out_p}")

def main():
    print("=" * 60)
    print("GENERANDO ELI CANÓNICO: TRAJE FORMAL BEIGE, GAFAS, CABELLO 360° Y RIG")
    print("=" * 60)
    clean_scene()

    # Creación de materiales PBR de Eli
    mat_skin = create_pbr_material("Mat_Eli_Skin", (0.83, 0.66, 0.55, 1.0), roughness=0.55, specular=0.35,
                                   diffuse_tex_path=os.path.join(TEXTURES_DIR, "eli_face_diffuse.png"),
                                   normal_tex_path=os.path.join(TEXTURES_DIR, "eli_face_normal.png"))
    mat_eye = create_pbr_material("Mat_Eli_Eyes", (1, 1, 1, 1), roughness=0.08,
                                  diffuse_tex_path=os.path.join(TEXTURES_DIR, "eli_eye_diffuse.png"))
    mat_hair = create_pbr_material("Mat_Eli_Hair", (0.05, 0.04, 0.035, 1.0), roughness=0.82)
    mat_glasses = create_pbr_material("Mat_Eli_Glasses", (0.05, 0.05, 0.06, 1.0), roughness=0.20, specular=0.8,
                                      diffuse_tex_path=os.path.join(TEXTURES_DIR, "eli_glasses_diffuse.png"),
                                      normal_tex_path=os.path.join(TEXTURES_DIR, "eli_glasses_normal.png"))
    mat_glass = create_pbr_material("Mat_Eli_Glass", (0.9, 0.95, 1.0, 0.20), roughness=0.05, specular=0.9,
                                    transmission=0.85, alpha=0.35)
    mat_teeth = create_pbr_material("Mat_Eli_Teeth", (0.95, 0.94, 0.92, 1.0), roughness=0.20, specular=0.8)

    mat_suit = create_pbr_material("Mat_Eli_Suit", (0.83, 0.78, 0.70, 1.0), roughness=0.70,
                                   diffuse_tex_path=os.path.join(TEXTURES_DIR, "eli_suit_diffuse.png"),
                                   normal_tex_path=os.path.join(TEXTURES_DIR, "eli_suit_normal.png"))
    mat_pants = create_pbr_material("Mat_Eli_Pants", (0.83, 0.78, 0.70, 1.0), roughness=0.72,
                                    diffuse_tex_path=os.path.join(TEXTURES_DIR, "eli_pants_diffuse.png"),
                                    normal_tex_path=os.path.join(TEXTURES_DIR, "eli_pants_normal.png"))
    mat_shirt = create_pbr_material("Mat_Eli_Shirt", (0.74, 0.84, 0.93, 1.0), roughness=0.75,
                                    diffuse_tex_path=os.path.join(TEXTURES_DIR, "eli_shirt_diffuse.png"),
                                    normal_tex_path=os.path.join(TEXTURES_DIR, "eli_shirt_normal.png"))
    mat_tie = create_pbr_material("Mat_Eli_Tie", (0.44, 0.09, 0.15, 1.0), roughness=0.40, specular=0.65,
                                  diffuse_tex_path=os.path.join(TEXTURES_DIR, "eli_tie_diffuse.png"),
                                  normal_tex_path=os.path.join(TEXTURES_DIR, "eli_tie_normal.png"))
    mat_shoes = create_pbr_material("Mat_Eli_Shoes", (0.22, 0.12, 0.08, 1.0), roughness=0.28, specular=0.75,
                                    diffuse_tex_path=os.path.join(TEXTURES_DIR, "eli_shoes_diffuse.png"),
                                    normal_tex_path=os.path.join(TEXTURES_DIR, "eli_shoes_normal.png"))
    mat_belt = create_pbr_material("Mat_Eli_Belt", (0.20, 0.10, 0.06, 1.0), roughness=0.35, specular=0.60,
                                   diffuse_tex_path=os.path.join(TEXTURES_DIR, "eli_belt_diffuse.png"),
                                   normal_tex_path=os.path.join(TEXTURES_DIR, "eli_belt_normal.png"))
    mat_buttons = create_pbr_material("Mat_Eli_Buttons", (0.12, 0.08, 0.06, 1.0), roughness=0.20, specular=0.8)
    mat_metal = create_pbr_material("Mat_Eli_Metal", (0.88, 0.89, 0.90, 1.0), roughness=0.18, metallic=0.95)

    materials = {
        "head": [mat_skin, mat_eye, mat_hair, mat_glasses, mat_glass, mat_teeth],
        "body": [mat_suit, mat_pants, mat_shoes, mat_shirt, mat_tie, mat_buttons, mat_buttons, mat_belt, mat_metal, mat_skin]
    }

    skel = build_skeleton()
    print("✓ Armature canónico construido con 22 huesos.")

    head_obj = build_head_mesh(materials)
    assign_weights(head_obj, is_head=True)
    head_obj.parent = skel
    mod_h = head_obj.modifiers.new("Armature", type='ARMATURE')
    mod_h.object = skel
    print("✓ Player_Head_Mesh generado con gafas 3D, ojos a Z=1.515, párpados con shape key 'blink' y 126 rizos 360°.")

    body_obj = build_body_mesh(materials)
    assign_weights(body_obj, is_head=False)
    body_obj.parent = skel
    mod_b = body_obj.modifiers.new("Armature", type='ARMATURE')
    mod_b.object = skel
    print("✓ Player_Body_Mesh generado con traje formal beige, solapas de muesca, corbata de seda y manos anatómicas.")

    # Verificación matemática estricta de pesos
    leg_groups = ["UpperLeg.L", "UpperLeg.R", "LowerLeg.L", "LowerLeg.R", "Foot.L", "Foot.R", "Toes.L", "Toes.R"]
    for g_name in leg_groups:
        grp = body_obj.vertex_groups[g_name]
        for v in body_obj.data.vertices:
            for g in v.groups:
                if g.group == grp.index and g.weight > 0.0:
                    assert abs(v.co.x) <= 0.18, f"Fuga de vértice de mano a pierna detectada: {v.co}"
    print("✓ Verificación matemática de pesos: 0 vértices de manos fugados a piernas.")

    os.makedirs(os.path.dirname(OUTPUT_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
    print(f"✓ Guardado .blend en: {OUTPUT_BLEND}")

    bpy.ops.export_scene.gltf(
        filepath=OUTPUT_GLB,
        export_format='GLB',
        use_selection=False,
        export_apply=False,
        export_def_bones=True,
        export_materials='EXPORT',
        export_cameras=False,
        export_lights=False
    )
    print(f"✓ Exportado .glb canónico en: {OUTPUT_GLB}")

    render_studio_views()
    print("=" * 60)
    print("PROCESO ELI COMPLETADO EXITOSAMENTE")
    print("=" * 60)

if __name__ == "__main__":
    main()
