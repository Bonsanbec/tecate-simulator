"""
Test Axel Master v13 - Reconstrucción Anatómica y Textil Refinada:
- Perfil craneofacial orgánico continuo (sin picos ni dientes de sierra).
- Cuero cabelludo y rostro con delimitación estricta: piel impecable en mejillas, cuello y orejas.
- Cabellera rizada abundante y densa en 360° (frontal, superior, lateral y posterior).
- Saco / Chaleco con cierre dorsal continuo en 360° sin agujeros bajo la sisa.
"""

import bpy
import bmesh
import math
import os
import numpy as np
from mathutils import Vector, Matrix, Euler, Quaternion

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
TEXTURES_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/textures")
SCRATCH_DIR = os.path.join(PROJECT_ROOT, "scratch")

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
                        diffuse_tex_path=None, normal_tex_path=None, specular=0.5):
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

def build_head_mesh(materials):
    me = bpy.data.meshes.new("Player_Head_Mesh_Data")
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")

    n_ring = 32
    # Perfil craneal masculino refinado:
    # Curva occipital posterior continua (-0.052 -> -0.076 -> -0.098 -> -0.104 -> -0.095 -> -0.078)
    # Perfil facial armónico: mentón angular, surco labiomental suave, labios proporcionados, nariz recta
    head_profile = [
        # z,      rx,    ry_front, ry_back, y_offset, v_uv
        (1.372, 0.050, 0.042,   0.048,   -0.004,   0.12), # 0: Base cuello
        (1.392, 0.048, 0.043,   0.052,   -0.002,   0.18), # 1: Cuello medio
        (1.412, 0.052, 0.048,   0.060,    0.002,   0.24), # 2: Submandíbula
        (1.428, 0.060, 0.068,   0.072,    0.012,   0.30), # 3: Mentón angular masculino proyectado
        (1.442, 0.066, 0.063,   0.082,    0.010,   0.35), # 4: Ángulo mandibular y surco labiomental
        (1.455, 0.068, 0.071,   0.088,    0.008,   0.38), # 5: Labio inferior
        (1.465, 0.070, 0.066,   0.094,    0.007,   0.40), # 6: Hendidura labial
        (1.476, 0.071, 0.073,   0.098,    0.005,   0.43), # 7: Labio superior con arco de Cupido
        (1.490, 0.074, 0.068,   0.102,    0.003,   0.48), # 8: Base nasal / Filtrum
        (1.503, 0.077, 0.088,   0.104,    0.001,   0.54), # 9: Punta nasal recta y definida
        (1.515, 0.081, 0.072,   0.105,    0.000,   0.63), # 10: Ojos / cuencas (Z = 1.515)
        (1.530, 0.082, 0.079,   0.104,   -0.002,   0.72), # 11: Pómulos y cejas
        (1.548, 0.080, 0.072,   0.102,   -0.004,   0.79), # 12: Frente baja / relieve occipital
        (1.568, 0.077, 0.066,   0.096,   -0.006,   0.85), # 13: Frente media
        (1.588, 0.072, 0.058,   0.088,   -0.008,   0.91), # 14: Asiento sombrero
        (1.615, 0.060, 0.044,   0.074,   -0.010,   0.96), # 15: Bóveda craneal
        (1.635, 0.038, 0.026,   0.046,   -0.012,   0.99), # 16: Coronilla
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

            # Modulaciones faciales suaves (sin dientes de sierra)
            if l_idx in (5, 6, 7) and 0.38 * math.pi <= ang <= 0.62 * math.pi:
                mw = math.cos((ang - 0.5 * math.pi) / 0.12 * (0.5 * math.pi))**2
                if l_idx == 5: y += 0.006 * mw
                elif l_idx == 6: y -= 0.004 * mw
                elif l_idx == 7: y += 0.005 * mw

            if l_idx in (8, 9) and 0.42 * math.pi <= ang <= 0.58 * math.pi:
                nw = math.cos((ang - 0.5 * math.pi) / 0.08 * (0.5 * math.pi))**2
                y += (0.014 if l_idx == 9 else 0.006) * nw

            if l_idx == 3 and 0.40 * math.pi <= ang <= 0.60 * math.pi:
                cw = math.cos((ang - 0.5 * math.pi) / 0.10 * (0.5 * math.pi))**2
                y += 0.008 * cw

            # Hendidura orbital en nivel 10
            if l_idx == 10 and (0.30 * math.pi <= ang <= 0.42 * math.pi or 0.58 * math.pi <= ang <= 0.70 * math.pi):
                y -= 0.018

            cur_ring.append(bm.verts.new((x, y, z)))
            u_coord = ((ang - 0.5 * math.pi) / (2.0 * math.pi) + 0.5) % 1.0
            cur_u.append(u_coord)
        rings.append((cur_ring, cur_u, v_uv))

    # Construir caras y asignar piel por defecto
    for l_idx in range(len(head_profile) - 1):
        r1, u1, v1 = rings[l_idx]
        r2, u2, v2 = rings[l_idx + 1]
        z_mid = (head_profile[l_idx][0] + head_profile[l_idx + 1][0]) * 0.5
        for i in range(n_ring):
            inxt = (i + 1) % n_ring
            f = bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))

            ang_mid = (2.0 * math.pi * (i + 0.5)) / n_ring
            sin_mid = math.sin(ang_mid)
            # Solo coronilla superior y occipital posterior alto reciben material de cabello
            is_scalp = (z_mid >= 1.585) or (z_mid >= 1.53 and sin_mid < -0.35)
            f.material_index = 2 if is_scalp else 0 # 2: Hair, 0: Skin (rostro, mejillas, cuello 100% piel)

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

    # Ojos 3D almendrados
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
            nf.material_index = 1
            for loop in nf.loops:
                co = loop.vert.co - Vector(pos)
                loop[uv_lay].uv = (0.5 + co.x / (2.0 * eye_r), 0.5 + co.z / (2.0 * eye_r))
        e_bm.free()

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

            upper_margin.append(bm.verts.new((ex + dx, ey + dy_margin, ez + dz_margin_sup)))
            upper_crease.append(bm.verts.new((ex + dx, ey + dy_margin * 0.98 + 0.002, ez + dz_margin_sup + 0.0045 * arch_sup)))
            upper_brow.append(bm.verts.new((ex + dx, ey + dy_margin * 0.92 + 0.005, ez + dz_margin_sup + 0.0100 * arch_sup)))
            lower_margin.append(bm.verts.new((ex + dx, ey + dy_margin_inf, ez + dz_margin_inf)))
            lower_crease.append(bm.verts.new((ex + dx, ey + dy_margin_inf * 0.96 + 0.003, ez + dz_margin_inf - 0.0060 * arch_sup)))

        for i in range(n_pts - 1):
            bm.faces.new((upper_margin[i], upper_margin[i+1], upper_crease[i+1], upper_crease[i])).material_index = 0
            bm.faces.new((upper_crease[i], upper_crease[i+1], upper_brow[i+1], upper_brow[i])).material_index = 0
            bm.faces.new((lower_crease[i], lower_crease[i+1], lower_margin[i+1], lower_margin[i])).material_index = 0

    # Orejas suaves
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
    # CABELLERA RIZADA VOLUMINOSA EN 360° ("THE HAIR WAS FINE")
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
                    f_c.material_index = 2
            prev_ring = c_ring

    # 1. Flequillo frontal en 2 capas (24 rizos orgánicos que caen hacia la frente)
    for row_z, row_r, n_curls in [(1.585, 0.068, 12), (1.572, 0.073, 12)]:
        for i in range(n_curls):
            t_f = (i / float(n_curls - 1)) * 2.0 - 1.0
            x_pos = t_f * 0.058
            y_pos = row_r * math.sqrt(max(0.01, 1.0 - (x_pos / 0.082)**2)) + 0.006
            dx = t_f * 0.010 + (0.004 if i % 2 == 0 else -0.004)
            dy = 0.014 - 0.006 * abs(t_f)
            dz = -0.042 - 0.010 * (1.0 - abs(t_f))
            r_c = 0.010 + 0.002 * (i % 3)
            turns_c = 2.3 + 0.3 * (i % 2)
            phi = 0.85 * i + (1.2 if row_z < 1.58 else 0.0)
            add_curl((x_pos, y_pos, row_z), (dx, dy, dz), r_c, turns_c, phi, base_thick=0.0070)

    # 2. Sienes y patillas sobre las orejas (20 rizos: 10 por lado)
    for s_side in (1.0, -1.0):
        side_specs = [
            ( 0.040, 1.575,  0.006, -0.048, 0.010, 2.4),
            ( 0.025, 1.572,  0.004, -0.052, 0.011, 2.5),
            ( 0.010, 1.570,  0.002, -0.055, 0.011, 2.6),
            (-0.005, 1.568, -0.002, -0.056, 0.011, 2.5),
            (-0.020, 1.565, -0.004, -0.054, 0.011, 2.4),
            (-0.035, 1.562, -0.006, -0.050, 0.010, 2.3),
            # Patilla baja
            ( 0.030, 1.538,  0.004, -0.044, 0.009, 2.3),
            ( 0.015, 1.532,  0.002, -0.048, 0.010, 2.4),
            (-0.002, 1.528, -0.002, -0.050, 0.010, 2.4),
            (-0.018, 1.528, -0.004, -0.048, 0.010, 2.3),
        ]
        for idx_s, (sy, sz, sdy, sdz, src, sturns) in enumerate(side_specs):
            sx = s_side * (0.074 + 0.006 * (idx_s % 2))
            sdx = s_side * 0.006
            phi = 0.9 * idx_s + (0.5 if s_side < 0 else 0.0)
            add_curl((sx, sy, sz), (sdx, sdy, sdz), src, sturns, phi, base_thick=0.0070)

    # 3. Nuca posterior en 3 niveles (30 rizos)
    nape_levels = [
        (1.575, 11, 0.094, -0.048),
        (1.535, 11, 0.090, -0.050),
        (1.495,  8, 0.084, -0.045),
    ]
    for n_z, n_cnt, n_rad, n_dz in nape_levels:
        angles = np.linspace(-math.pi * 0.86, -math.pi * 0.14, n_cnt)
        for i_n, ang in enumerate(angles):
            nx = n_rad * math.cos(ang)
            ny = n_rad * math.sin(ang) - 0.006
            dx = 0.006 * math.cos(ang)
            dy = 0.006 * math.sin(ang)
            dz = n_dz - 0.006 * abs(math.cos(ang))
            rc = 0.010 + 0.002 * (i_n % 3)
            tc = 2.3 + 0.3 * (i_n % 2)
            phi = 0.75 * i_n + n_z * 3.0
            add_curl((nx, ny, n_z), (dx, dy, dz), rc, tc, phi, base_thick=0.0072)

    # 4. Corona perimétrica bajo el fedora (20 rizos en 360°)
    rim_angles = np.linspace(0, 2.0 * math.pi, 20, endpoint=False)
    for i_r, r_ang in enumerate(rim_angles):
        rx_c = 0.080 * math.cos(r_ang)
        ry_c = 0.088 * math.sin(r_ang) - 0.004
        rz_c = 1.588
        dx_c = 0.008 * math.cos(r_ang)
        dy_c = 0.008 * math.sin(r_ang)
        dz_c = -0.026
        rc_c = 0.009
        tc_c = 1.8
        phi_c = 1.1 * i_r
        add_curl((rx_c, ry_c, rz_c), (dx_c, dy_c, dz_c), rc_c, tc_c, phi_c, base_thick=0.0068)

    # Sombrero Fedora adaptado al nuevo relieve craneal
    fedora_bm = bmesh.new()
    n_hat = 32
    hat_levels = [
        # z_local, rx,    ry,    y_c,   pinch_x, crease
        (0.000,   0.095, 0.112, -0.004, 1.00,    0.000), # 0: Cinta
        (0.025,   0.093, 0.110, -0.004, 0.96,    0.000), # 1: Copa baja
        (0.055,   0.088, 0.104, -0.004, 0.90,    0.000), # 2: Copa media
        (0.080,   0.083, 0.098, -0.004, 0.84,    0.000), # 3: Copa alta
        (0.100,   0.079, 0.092, -0.004, 0.78,    0.016), # 4: Corona Teardrop
    ]
    fed_rings = []
    for (z, rx, ry, y_c, pinch_x, crease) in hat_levels:
        cur_ring = []
        for i in range(n_hat):
            ang = (2.0 * math.pi * i) / n_hat
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            cur_rx = rx * (pinch_x if sin_a > 0 else 1.0)
            vx = cur_rx * cos_a
            vy = ry * sin_a + y_c
            vz = z
            if crease > 0.0:
                dist_x = abs(vx) / cur_rx
                if dist_x < 0.6: vz -= crease * (1.0 - dist_x / 0.6)
            cur_ring.append(fedora_bm.verts.new((vx, vy, vz)))
        fed_rings.append(cur_ring)

    for l in range(len(hat_levels) - 1):
        r1 = fed_rings[l]
        r2 = fed_rings[l + 1]
        m_idx = 4 if l == 0 else 3
        for i in range(n_hat):
            inxt = (i + 1) % n_hat
            fedora_bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i])).material_index = m_idx

    top_c = fedora_bm.verts.new((0.0, -0.004, 0.088))
    for i in range(n_hat):
        inxt = (i + 1) % n_hat
        fedora_bm.faces.new((fed_rings[-1][i], fed_rings[-1][inxt], top_c)).material_index = 3

    b_in_top = fed_rings[0]
    b_out_top, b_out_bot, b_in_bot = [], [], []
    for i in range(n_hat):
        ang = (2.0 * math.pi * i) / n_hat
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        brim_ext = 0.050 + 0.008 * max(0.0, sin_a)
        ox = (0.095 + brim_ext) * cos_a
        oy = (0.112 + brim_ext) * sin_a - 0.004
        dip = -0.008 * math.sin(ang) if sin_a > 0 else 0.012 * abs(sin_a)
        dip += 0.005 * (cos_a**2)
        b_out_top.append(fedora_bm.verts.new((ox, oy, dip)))
        b_out_bot.append(fedora_bm.verts.new((ox, oy, dip - 0.0045)))
        b_in_bot.append(fedora_bm.verts.new((b_in_top[i].co.x, b_in_top[i].co.y, b_in_top[i].co.z - 0.0045)))

    for i in range(n_hat):
        inxt = (i + 1) % n_hat
        fedora_bm.faces.new((b_in_top[i], b_in_top[inxt], b_out_top[inxt], b_out_top[i])).material_index = 3
        fedora_bm.faces.new((b_out_top[i], b_out_top[inxt], b_out_bot[inxt], b_out_bot[i])).material_index = 3
        fedora_bm.faces.new((b_out_bot[i], b_out_bot[inxt], b_in_bot[inxt], b_in_bot[i])).material_index = 3
        fedora_bm.faces.new((b_in_bot[i], b_in_bot[inxt], b_in_top[inxt], b_in_top[i])).material_index = 3

    bmesh.ops.translate(fedora_bm, verts=fedora_bm.verts, vec=(0.0, 0.0, 1.585))
    v_map_fed = {v: bm.verts.new(v.co) for v in fedora_bm.verts}
    for f in fedora_bm.faces:
        bm.faces.new([v_map_fed[v] for v in f.verts]).material_index = f.material_index
    fedora_bm.free()

    bm.normal_update()
    for f in bm.faces: f.smooth = True
    bm.to_mesh(me)
    bm.free()

    for mat in materials["head"]:
        me.materials.append(mat)

    obj_head = bpy.data.objects.new("Player_Head_Mesh", me)
    bpy.context.scene.collection.objects.link(obj_head)
    return obj_head

def build_body_mesh(materials):
    mesh_graph = bpy.data.meshes.new("Body_Graph_Data")
    obj_body = bpy.data.objects.new("Player_Body_Mesh", mesh_graph)
    bpy.context.scene.collection.objects.link(obj_body)

    # Nodos biomecánicos con curvatura espinal natural
    nodes = [
        # Tronco
        (0.00,  0.000, 0.82, 0.130, 0.100), # 0: Pelvis base
        (0.00,  0.004, 0.94, 0.145, 0.105), # 1: Caderas / Cintura pantalón
        (0.00,  0.008, 1.04, 0.136, 0.096), # 2: Cintura entallada
        (0.00, -0.010, 1.16, 0.156, 0.114), # 3: Costillas / cifosis dorsal
        (0.00, -0.012, 1.28, 0.172, 0.124), # 4: Pectorales y omóplatos
        (0.00, -0.005, 1.36, 0.155, 0.108), # 5: Clavículas / hombros
        (0.00,  0.005, 1.40, 0.050, 0.050), # 6: Base del cuello

        # Brazos
        ( 0.06, -0.005, 1.36, 0.070, 0.070), # 7
        ( 0.18, -0.005, 1.34, 0.062, 0.062), # 8: Hombro L
        ( 0.26,  0.000, 1.15, 0.050, 0.050), # 9: Codo L
        ( 0.33,  0.010, 0.92, 0.036, 0.032), # 10: Manga / Puño L

        (-0.06, -0.005, 1.36, 0.070, 0.070), # 11
        (-0.18, -0.005, 1.34, 0.062, 0.062), # 12: Hombro R
        (-0.26,  0.000, 1.15, 0.050, 0.050), # 13: Codo R
        (-0.33,  0.010, 0.92, 0.036, 0.032), # 14: Manga / Puño R

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

    for p in bm.faces:
        center_z = p.calc_center_median().z
        if center_z < 0.10:
            p.material_index = 2 # Zapatos
        elif center_z < 0.94:
            p.material_index = 1 # Pantalón
        else:
            p.material_index = 0 # Camisa

    # Cuello camisero
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
        bm.faces.new((c_bot[i], c_bot[i_next], c_top[i_next], c_top[i])).material_index = 0

    c_wings = [
        [bm.verts.new((0.008, 0.058, 1.418)), bm.verts.new((0.050, 0.046, 1.412)), bm.verts.new((0.028, 0.080, 1.365))],
        [bm.verts.new((-0.008, 0.058, 1.418)), bm.verts.new((-0.028, 0.080, 1.365)), bm.verts.new((-0.050, 0.046, 1.412))],
    ]
    bm.faces.new(c_wings[0]).material_index = 0
    bm.faces.new(c_wings[1]).material_index = 0

    # Corbata
    k_v = [
        bm.verts.new((-0.016, 0.068, 1.415)),
        bm.verts.new(( 0.016, 0.068, 1.415)),
        bm.verts.new(( 0.013, 0.096, 1.370)),
        bm.verts.new((-0.013, 0.096, 1.370)),
        bm.verts.new(( 0.000, 0.102, 1.392)),
    ]
    bm.faces.new((k_v[0], k_v[1], k_v[4])).material_index = 4
    bm.faces.new((k_v[1], k_v[2], k_v[4])).material_index = 4
    bm.faces.new((k_v[2], k_v[3], k_v[4])).material_index = 4
    bm.faces.new((k_v[3], k_v[0], k_v[4])).material_index = 4

    tie_profile = [
        (1.370, 0.013, 0.096),
        (1.320, 0.015, 0.114),
        (1.270, 0.016, 0.122),
        (1.215, 0.015, 0.123),
        (1.150, 0.013, 0.116),
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
    # SACO / CHALECO SASTRE CONTINUO EN 360° (ANILLOS PERIMETRALES)
    # -------------------------------------------------------------------------
    # Envolvente anatómica tubular cerrada de 24 vértices por nivel:
    # Delantero (+Y), costados (±X) y espalda completa (-Y) en material_index = 3 (Mat_Axel_Vest)
    garment_levels = [
        # z,      rx,    ry_front, ry_back, y_c,    v_cut
        (1.380, 0.130, 0.075,   0.095,   -0.005, 0.075), # 0: Hombros / clavículas
        (1.330, 0.145, 0.100,   0.110,   -0.010, 0.055), # 1: Pecho alto
        (1.260, 0.160, 0.125,   0.122,   -0.012, 0.035), # 2: Pecho medio / sisa
        (1.190, 0.162, 0.130,   0.122,   -0.010, 0.000), # 3: Vértice escote en V (cierre botones)
        (1.120, 0.156, 0.126,   0.118,   -0.008, 0.000), # 4: Costillas / cintura alta
        (1.050, 0.148, 0.122,   0.114,   -0.006, 0.000), # 5: Cintura media (martingala)
        (0.980, 0.148, 0.118,   0.112,   -0.004, 0.000), # 6: Cintura baja
        (0.920, 0.152, 0.116,   0.114,   -0.002, 0.000), # 7: Dobladillo inferior
    ]

    n_g = 24
    g_rings = []
    for l_idx, (gz, grx, gry_f, gry_b, gy_c, g_vcut) in enumerate(garment_levels):
        cur_ring = []
        for i in range(n_g):
            ang = (2.0 * math.pi * i) / n_g
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)

            # Ancho y profundidad en cada punto angular
            cur_rx = grx * (1.02)
            cur_ry = (gry_f if sin_a >= 0 else gry_b) * (1.02)
            vx = cur_rx * cos_a
            vy = cur_ry * sin_a + gy_c
            vz = gz

            # Escote en V delantero para niveles superiores
            if g_vcut > 0.0 and sin_a > 0.70:
                dist_center = abs(cos_a)
                if dist_center < (g_vcut / grx):
                    # Retraer vértices del escote hacia el cuello de la camisa
                    vy -= 0.030 * (1.0 - dist_center / (g_vcut / grx))

            # Picos delanteros sastre en el dobladillo inferior (l_idx == 7)
            if l_idx == 7:
                if 0.35 * math.pi <= ang <= 0.65 * math.pi:
                    peak_w = max(0.0, 1.0 - (abs(ang - 0.5 * math.pi) / 0.15)**2)
                    vz -= 0.035 * peak_w # Picos caen hacia Z = 0.885

            cur_ring.append(bm.verts.new((vx, vy, vz)))
        g_rings.append(cur_ring)

    # Conectar anillos en 360° continuos con material sastre (material_index = 3)
    for l in range(len(garment_levels) - 1):
        r1 = g_rings[l]
        r2 = g_rings[l + 1]
        for i in range(n_g):
            inxt = (i + 1) % n_g
            # Si es el escote central delantero en los primeros niveles, omitir cara para dejar ver la corbata
            ang_f = (2.0 * math.pi * (i + 0.5)) / n_g
            sin_f = math.sin(ang_f)
            cos_f = math.cos(ang_f)
            is_v_opening = (l < 3) and (sin_f > 0.88) and (abs(cos_f) < 0.22)
            if not is_v_opening:
                f = bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))
                f.material_index = 3 # 100% material sastre (frente, costados y espalda)

    # Martingala / Cinturón posterior en Z = 1.050 (nivel 5)
    mart_l = bm.verts.new(( 0.080, -0.124, 1.055))
    mart_r = bm.verts.new((-0.080, -0.124, 1.055))
    mart_c1 = bm.verts.new(( 0.014, -0.128, 1.055))
    mart_c2 = bm.verts.new((-0.014, -0.128, 1.055))
    mart_l_b = bm.verts.new(( 0.080, -0.124, 1.035))
    mart_r_b = bm.verts.new((-0.080, -0.124, 1.035))
    mart_c1_b = bm.verts.new(( 0.014, -0.128, 1.035))
    mart_c2_b = bm.verts.new((-0.014, -0.128, 1.035))

    bm.faces.new((mart_l, mart_c1, mart_c1_b, mart_l_b)).material_index = 3
    bm.faces.new((mart_c2, mart_r, mart_r_b, mart_c2_b)).material_index = 3
    bm.faces.new((mart_c1, mart_c2, mart_c2_b, mart_c1_b)).material_index = 5 # Hebilla plateada

    # Botones frontales plateados
    b_zs = [1.190, 1.130, 1.070, 1.010, 0.950]
    for bz in b_zs:
        by = 0.128 + (1.190 - bz) * (-0.012)
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.0048)
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.0, by + 0.007, bz))
        v_map = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            bm.faces.new([v_map[v] for v in f.verts]).material_index = 5
        btn_bm.free()

    # Bolsillos sastre
    p_specs = [(0.070, 0.985, 0.032), (-0.070, 0.985, 0.032), (0.065, 1.140, 0.026)]
    for (px, pz, pw) in p_specs:
        py = 0.124
        p_box = [
            bm.verts.new((px - pw*0.5, py + 0.003, pz + 0.004)),
            bm.verts.new((px + pw*0.5, py + 0.003, pz + 0.004)),
            bm.verts.new((px + pw*0.5, py + 0.003, pz - 0.004)),
            bm.verts.new((px - pw*0.5, py + 0.003, pz - 0.004)),
        ]
        bm.faces.new(p_box).material_index = 3

    # Manos y dedos anatómicos (con pesos blindados para Hand.L / Hand.R)
    for is_left in (True, False):
        sign_h = 1.0 if is_left else -1.0
        w_center = Vector((sign_h * 0.33, 0.010, 0.920))

        n_cuff = 12
        cuff_top, cuff_bot = [], []
        for k in range(n_cuff):
            ang = (2.0 * math.pi * k) / n_cuff
            cx = w_center.x + 0.030 * math.cos(ang)
            cy = w_center.y + 0.026 * math.sin(ang)
            cuff_top.append(bm.verts.new((cx, cy, 0.925)))
            cuff_bot.append(bm.verts.new((cx * 1.02, cy * 1.02, 0.898)))
        for k in range(n_cuff):
            kn = (k + 1) % n_cuff
            bm.faces.new((cuff_top[k], cuff_top[kn], cuff_bot[kn], cuff_bot[k])).material_index = 0

        wrist_v = []
        for k in range(n_cuff):
            ang = (2.0 * math.pi * k) / n_cuff
            wx = w_center.x + 0.022 * math.cos(ang)
            wy = w_center.y + 0.018 * math.sin(ang)
            wrist_v.append(bm.verts.new((wx, wy, 0.905)))
        for k in range(n_cuff):
            kn = (k + 1) % n_cuff
            bm.faces.new((wrist_v[k], wrist_v[kn], cuff_bot[kn], cuff_bot[k])).material_index = 6

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
        bm.faces.new((p_box[0], p_box[1], p_box[5], p_box[4])).material_index = 6
        bm.faces.new((p_box[1], p_box[2], p_box[6], p_box[5])).material_index = 6
        bm.faces.new((p_box[2], p_box[3], p_box[7], p_box[6])).material_index = 6
        bm.faces.new((p_box[3], p_box[0], p_box[4], p_box[7])).material_index = 6

        finger_specs = [
            ("Index",   w_center.y + 0.018, 0.060, 0.0068, 0.85, is_left),
            ("Middle",  w_center.y + 0.005, 0.066, 0.0072, 1.00, is_left),
            ("Ring",    w_center.y - 0.008, 0.061, 0.0068, 1.15, False),
            ("Little",  w_center.y - 0.019, 0.050, 0.0058, 1.30, False),
        ]
        curl_dir = Vector((-sign_h * 0.70, 0.35, 0.0)).normalized()

        for (f_name, fy, flen, frad, curl, has_ring) in finger_specs:
            mcp = Vector((w_center.x, fy, z_knuckles))
            p0 = mcp
            p1 = p0 + Vector((0, 0, -flen * 0.38)) + curl_dir * (flen * 0.18 * curl)
            p2 = p1 + Vector((0, 0, -flen * 0.34)) + curl_dir * (flen * 0.38 * curl)
            p3 = p2 + Vector((0, 0, -flen * 0.24)) + curl_dir * (flen * 0.48 * curl)

            joints = [p0, p1, p2, p3]
            prev_ring = None
            ring_joints = []
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
                        bm.faces.new((prev_ring[k], prev_ring[kn], cur_ring[kn], cur_ring[k])).material_index = 6
                prev_ring = cur_ring
                ring_joints.append(pt)

            tip_v = bm.verts.new(p3 + curl_dir * 0.003 - Vector((0, 0, 0.003)))
            for k in range(6):
                kn = (k + 1) % 6
                bm.faces.new((prev_ring[kn], prev_ring[k], tip_v)).material_index = 6

            if has_ring:
                r_c = (ring_joints[0] + ring_joints[1]) * 0.5
                r_rad = frad * 1.30
                r1_pts, r2_pts = [], []
                for k in range(8):
                    ang_r = (2.0 * math.pi * k) / 8.0
                    rx = r_c.x + r_rad * math.cos(ang_r)
                    ry = r_c.y + r_rad * math.sin(ang_r)
                    r1_pts.append(bm.verts.new((rx, ry, r_c.z + 0.0035)))
                    r2_pts.append(bm.verts.new((rx, ry, r_c.z - 0.0035)))
                for k in range(8):
                    kn = (k + 1) % 8
                    bm.faces.new((r1_pts[k], r1_pts[kn], r2_pts[kn], r2_pts[k])).material_index = 5

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
                    bm.faces.new((prev_th[k], prev_th[kn], cur_ring[kn], cur_ring[k])).material_index = 6
            prev_th = cur_ring
        tip_th = bm.verts.new(th_joints[-1] + Vector((-sign_h * 0.002, 0.003, -0.003)))
        for k in range(6):
            kn = (k + 1) % 6
            bm.faces.new((prev_th[kn], prev_th[k], tip_th)).material_index = 6

    bm.normal_update()
    for f in bm.faces: f.smooth = True
    bm.to_mesh(obj_body.data)
    bm.free()

    for mat in materials["body"]:
        obj_body.data.materials.append(mat)

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
            if co.z < 0.04 and abs(co.x) <= 0.18:
                obj.vertex_groups["Toes.L" if co.x > 0 else "Toes.R"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.12 and abs(co.x) <= 0.18:
                obj.vertex_groups["Foot.L" if co.x > 0 else "Foot.R"].add([v.index], 1.0, 'REPLACE')
            elif abs(co.x) > 0.18 and co.z < 1.38:
                side = ".L" if co.x > 0 else ".R"
                if co.z < 0.93:
                    obj.vertex_groups["Hand" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.15:
                    obj.vertex_groups["Forearm" + side].add([v.index], 1.0, 'REPLACE')
                else:
                    obj.vertex_groups["UpperArm" + side].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.48:
                obj.vertex_groups["LowerLeg.L" if co.x > 0 else "LowerLeg.R"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.82 and abs(co.x) > 0.03:
                obj.vertex_groups["UpperLeg.L" if co.x > 0 else "UpperLeg.R"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.95:
                obj.vertex_groups["Hips"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 1.15:
                obj.vertex_groups["Spine"].add([v.index], 1.0, 'REPLACE')
            else:
                obj.vertex_groups["Chest"].add([v.index], 1.0, 'REPLACE')

def render_views():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.device = 'CPU'

    key = bpy.data.objects.new("Key", bpy.data.lights.new("Key", 'AREA'))
    key.data.energy = 90.0
    key.data.size = 1.4
    key.location = Vector((-0.6, 1.6, 1.6))
    key.rotation_euler = (math.radians(50.0), 0.0, math.radians(-155.0))
    scene.collection.objects.link(key)

    fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", 'AREA'))
    fill.data.energy = 45.0
    fill.data.size = 1.8
    fill.location = Vector((0.7, 1.6, 1.4))
    scene.collection.objects.link(fill)

    catch = bpy.data.objects.new("EyeCatch", bpy.data.lights.new("EyeCatch", 'AREA'))
    catch.data.energy = 30.0
    catch.data.size = 0.6
    catch.location = Vector((0.0, 1.2, 1.515))
    scene.collection.objects.link(catch)

    rim = bpy.data.objects.new("Rim", bpy.data.lights.new("Rim", 'SPOT'))
    rim.data.energy = 70.0
    rim.data.spot_size = math.radians(65.0)
    rim.location = Vector((0.0, -1.2, 1.8))
    rim.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
    scene.collection.objects.link(rim)

    back_fill = bpy.data.objects.new("BackFill", bpy.data.lights.new("BackFill", 'AREA'))
    back_fill.data.energy = 55.0
    back_fill.data.size = 1.6
    back_fill.location = Vector((0.0, -1.6, 1.3))
    back_fill.rotation_euler = (math.radians(-70.0), 0.0, math.radians(180.0))
    scene.collection.objects.link(back_fill)

    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.lens = 50.0
    scene.collection.objects.link(cam)
    scene.camera = cam

    scene.render.resolution_x = 720
    scene.render.resolution_y = 1080
    scene.render.image_settings.file_format = 'PNG'

    views = [
        ("axel_v13_front.png", Vector((0.0, 1.65, 1.25)), (math.radians(88.5), 0.0, math.radians(178.0))),
        ("axel_v13_profile.png", Vector((1.65, 0.0, 1.45)), (math.radians(88.5), 0.0, math.radians(88.0))),
        ("axel_v13_back.png", Vector((0.0, -1.65, 1.25)), (math.radians(91.5), 0.0, math.radians(-2.0))),
        ("axel_v13_threequarter.png", Vector((1.15, 1.15, 1.35)), (math.radians(82.0), 0.0, math.radians(135.0))),
    ]

    for fname, loc, rot in views:
        cam.location = loc
        cam.rotation_euler = rot
        out_path = os.path.join(SCRATCH_DIR, fname)
        scene.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        print(f"✓ Render {fname} guardado en: {out_path}")

def main():
    print("=" * 60)
    print("EJECUTANDO AXEL MASTER V13")
    print("=" * 60)
    clean_scene()

    mat_skin = create_pbr_material("Mat_Axel_Skin", (0.82, 0.61, 0.49, 1.0), roughness=0.52,
                                   diffuse_tex_path=os.path.join(TEXTURES_DIR, "axel_face_diffuse.png"),
                                   normal_tex_path=os.path.join(TEXTURES_DIR, "axel_face_normal.png"))
    mat_eye = create_pbr_material("Mat_Axel_Eyes", (1, 1, 1, 1), roughness=0.08,
                                  diffuse_tex_path=os.path.join(TEXTURES_DIR, "axel_eye_diffuse.png"))
    mat_hair = create_pbr_material("Mat_Axel_Hair", (0.04, 0.035, 0.03, 1.0), roughness=0.82)
    mat_fedora = create_pbr_material("Mat_Axel_Fedora", (0.02, 0.02, 0.025, 1.0), roughness=0.92,
                                     diffuse_tex_path=os.path.join(TEXTURES_DIR, "axel_hat_diffuse.png"),
                                     normal_tex_path=os.path.join(TEXTURES_DIR, "axel_hat_normal.png"))
    mat_hatband = create_pbr_material("Mat_Axel_Hatband", (0.015, 0.015, 0.02, 1.0), roughness=0.45, specular=0.6)

    mat_shirt = create_pbr_material("Mat_Axel_Shirt", (0.17, 0.18, 0.20, 1.0), roughness=0.75,
                                    diffuse_tex_path=os.path.join(TEXTURES_DIR, "axel_shirt_diffuse.png"),
                                    normal_tex_path=os.path.join(TEXTURES_DIR, "axel_shirt_normal.png"))
    mat_pants = create_pbr_material("Mat_Axel_Pants", (0.13, 0.14, 0.16, 1.0), roughness=0.78,
                                    diffuse_tex_path=os.path.join(TEXTURES_DIR, "axel_pants_diffuse.png"),
                                    normal_tex_path=os.path.join(TEXTURES_DIR, "axel_pants_normal.png"))
    mat_shoes = create_pbr_material("Mat_Axel_Shoes", (0.03, 0.03, 0.035, 1.0), roughness=0.28, specular=0.7,
                                    diffuse_tex_path=os.path.join(TEXTURES_DIR, "axel_shoes_diffuse.png"),
                                    normal_tex_path=os.path.join(TEXTURES_DIR, "axel_shoes_normal.png"))
    mat_vest = create_pbr_material("Mat_Axel_Vest", (0.84, 0.85, 0.87, 1.0), roughness=0.68,
                                   diffuse_tex_path=os.path.join(TEXTURES_DIR, "axel_vest_diffuse.png"),
                                   normal_tex_path=os.path.join(TEXTURES_DIR, "axel_vest_normal.png"))
    mat_tie = create_pbr_material("Mat_Axel_Tie", (0.35, 0.36, 0.38, 1.0), roughness=0.4, specular=0.7,
                                  diffuse_tex_path=os.path.join(TEXTURES_DIR, "axel_tie_diffuse.png"),
                                  normal_tex_path=os.path.join(TEXTURES_DIR, "axel_tie_normal.png"))
    mat_silver = create_pbr_material("Mat_Axel_Silver", (0.88, 0.89, 0.90, 1.0), roughness=0.18, metallic=0.95)

    materials = {
        "head": [mat_skin, mat_eye, mat_hair, mat_fedora, mat_hatband],
        "body": [mat_shirt, mat_pants, mat_shoes, mat_vest, mat_tie, mat_silver, mat_skin]
    }

    skel = build_skeleton()
    head_obj = build_head_mesh(materials)
    assign_weights(head_obj, is_head=True)
    head_obj.parent = skel
    mod_h = head_obj.modifiers.new("Armature", type='ARMATURE')
    mod_h.object = skel

    body_obj = build_body_mesh(materials)
    assign_weights(body_obj, is_head=False)
    body_obj.parent = skel
    mod_b = body_obj.modifiers.new("Armature", type='ARMATURE')
    mod_b.object = skel

    render_views()
    print("=" * 60)
    print("PROCESO AXEL V13 COMPLETADO")
    print("=" * 60)

if __name__ == "__main__":
    main()
