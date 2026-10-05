"""
Axel Master Generator - Versión Anatómica, Sartorial y Rigged Canónica
1. Cotas craneales humanas con perfil facial armónico y curvatura occipital continua (sin pico nasal ni nuca plana).
2. Cuero cabelludo oscuro continuo bajo los rizos en la nuca y coronilla, con piel limpia en rostro y cuello.
3. Cabellera rizada abundante y densa en 360° (94 mechones helicoidales distribuidos en flequillo, sienes, nuca y contorno del fedora).
4. Párpados 3D almendrados con Shape Key 'blink' para parpadeo biológico, ojos a Z=1.515 y orejas anatómicas.
5. Chaleco sastre sartorial fiel a scratch/humans/axel2.png:
   - Escote en V profundo y abierto (Z=1.38 a Z=1.20) exhibiendo camisa oscura y corbata.
   - Tirantes de hombro continuos hacia la espalda.
   - Sisas anatómicas para los brazos y costados cerrados bajo las axilas (Z <= 1.26).
   - Espalda 100% cubierta con Mat_Axel_Vest y martingala con hebilla plateada.
   - Hilera de 5 botones plateados en el frente y picos sastre en el dobladillo (Z=0.885).
6. Manos anatómicas semi-pronadas con dedos curvados en reposo natural, anillos de plata y puños camiseros.
7. Rigging blindado de 22 huesos con ponderación estricta (0 fugas de vértices hacia las piernas).
8. Sombrero fedora manifold simétrico con pellizco de lágrima y ala moldeada.
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
OUTPUT_BLEND = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/citizens/axel.blend")
OUTPUT_GLB = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/citizens/axel.glb")
PREVIEW_PNG = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/axel_preview.png")

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

# =============================================================================
# 1. CABEZA PROPORCIONADA, OJOS DESCENDIDOS A Z=1.515, PÁRPADOS 3D Y RIZOS 360°
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
        (1.428, 0.060, 0.068, 0.070,  0.010, 0.30), # 3: Mentón masculino angular
        (1.442, 0.065, 0.064, 0.076,  0.008, 0.35), # 4: Surco mentolabial suave
        (1.455, 0.068, 0.071, 0.082,  0.006, 0.38), # 5: Labio inferior
        (1.465, 0.070, 0.067, 0.085,  0.005, 0.40), # 6: Hendidura labial
        (1.476, 0.071, 0.073, 0.088,  0.003, 0.43), # 7: Labio superior
        (1.490, 0.074, 0.068, 0.090,  0.001, 0.48), # 8: Base nasal / Filtrum
        (1.503, 0.077, 0.080, 0.090, -0.001, 0.54), # 9: Punta nasal recta y definida
        (1.515, 0.080, 0.074, 0.089, -0.002, 0.63), # 10: Ojos / puente nasal medio (Z = 1.515)
        (1.530, 0.082, 0.078, 0.088, -0.004, 0.72), # 11: Pómulos y cejas
        (1.548, 0.080, 0.073, 0.086, -0.006, 0.79), # 12: Frente baja / relieve occipital
        (1.568, 0.077, 0.067, 0.082, -0.007, 0.85), # 13: Frente media
        (1.588, 0.072, 0.058, 0.078, -0.008, 0.91), # 14: Asiento sombrero
        (1.615, 0.060, 0.044, 0.070, -0.010, 0.96), # 15: Bóveda craneal
        (1.635, 0.038, 0.026, 0.044, -0.012, 0.99), # 16: Coronilla
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

            # Modulaciones faciales anatómicas continuas
            if l_idx in (5, 6, 7) and 0.40 * math.pi <= ang <= 0.60 * math.pi:
                mw = math.cos((ang - 0.5 * math.pi) / 0.10 * (0.5 * math.pi))**2
                if l_idx == 5: y += 0.005 * mw
                elif l_idx == 6: y -= 0.003 * mw
                elif l_idx == 7: y += 0.004 * mw

            if l_idx in (8, 9, 10) and 0.44 * math.pi <= ang <= 0.56 * math.pi:
                nw = math.cos((ang - 0.5 * math.pi) / 0.06 * (0.5 * math.pi))**2
                if l_idx == 9: y += 0.010 * nw
                elif l_idx == 10: y += 0.006 * nw
                elif l_idx == 8: y += 0.004 * nw

            if l_idx == 3 and 0.42 * math.pi <= ang <= 0.58 * math.pi:
                cw = math.cos((ang - 0.5 * math.pi) / 0.08 * (0.5 * math.pi))**2
                y += 0.006 * cw

            if l_idx == 10 and (0.32 * math.pi <= ang <= 0.42 * math.pi or 0.58 * math.pi <= ang <= 0.68 * math.pi):
                y -= 0.015

            cur_ring.append(bm.verts.new((x, y, z)))
            u_coord = ((ang - 0.5 * math.pi) / (2.0 * math.pi) + 0.5) % 1.0
            cur_u.append(u_coord)
        rings.append((cur_ring, cur_u, v_uv))

    # Construir caras y asignar materiales:
    # 0: Mat_Axel_Skin (rostro, mejillas, cuello)
    # 2: Mat_Axel_Hair (cuero cabelludo en coronilla y nuca posterior)
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

    # Ojos 3D almendrados en Z = 1.515
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
            nf.material_index = 1 # mat_eye
            for loop in nf.loops:
                co = loop.vert.co - Vector(pos)
                loop[uv_lay].uv = (0.5 + co.x / (2.0 * eye_r), 0.5 + co.z / (2.0 * eye_r))
        e_bm.free()

    upper_lid_margin_verts = []
    upper_lid_crease_verts = []
    for side_idx, (ex, ey, ez) in enumerate(eye_pos):
        sign_side = 1.0 if ex > 0 else -1.0
        n_pts = 9
        upper_margin, upper_crease, upper_brow = [], [], []
        lower_margin, lower_crease = [], []
        for i in range(n_pts):
            t = (i / float(n_pts - 1)) * 2.0 - 1.0
            dx = t * 0.0125 * sign_side
            arch_sup = math.sqrt(max(0.0, 1.0 - t**2))
            dz_margin_sup = 0.0024 * arch_sup + 0.0003 * t
            dz_margin_inf = -0.0024 * arch_sup + 0.0002 * t
            dy_margin = math.sqrt(max(0.0001, (eye_r * 1.02)**2 - dx**2 - dz_margin_sup**2))
            dy_margin_inf = math.sqrt(max(0.0001, (eye_r * 1.02)**2 - dx**2 - dz_margin_inf**2))

            v_sup_m = bm.verts.new((ex + dx, ey + dy_margin, ez + dz_margin_sup))
            v_sup_c = bm.verts.new((ex + dx, ey + dy_margin * 0.98 + 0.002, ez + dz_margin_sup + 0.0035 * arch_sup))
            v_sup_b = bm.verts.new((ex + dx, ey + dy_margin * 0.92 + 0.005, ez + dz_margin_sup + 0.0090 * arch_sup))
            v_inf_m = bm.verts.new((ex + dx, ey + dy_margin_inf, ez + dz_margin_inf))
            v_inf_c = bm.verts.new((ex + dx, ey + dy_margin_inf * 0.96 + 0.003, ez + dz_margin_inf - 0.0045 * arch_sup))

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
    # CABELLERA RIZADA VOLUMINOSA EN 360° (94 MECHONES HELICOIDALES)
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

    # 1. Flequillo frontal en 2 capas recortado en '^' (24 rizos)
    for row_z, row_r, n_curls in [(1.585, 0.068, 12), (1.572, 0.073, 12)]:
        for i in range(n_curls):
            t_f = (i / float(n_curls - 1)) * 2.0 - 1.0
            x_pos = t_f * 0.058
            y_pos = row_r * math.sqrt(max(0.01, 1.0 - (x_pos / 0.082)**2)) + 0.006
            dx = t_f * 0.010 + (0.004 if i % 2 == 0 else -0.004)
            dy = 0.014 - 0.006 * abs(t_f)
            cur_z_start = row_z
            if row_z < 1.58:
                cur_z_start += 0.012 * max(0.0, 1.0 - abs(t_f) / 0.35)
                dz = -0.022 - 0.026 * abs(t_f)
            else:
                dz = -0.024 - 0.024 * abs(t_f)
            r_c = 0.009 + 0.002 * (i % 3)
            turns_c = 2.1 + 0.3 * (i % 2)
            phi = 0.85 * i + (1.2 if row_z < 1.58 else 0.0)
            add_curl((x_pos, y_pos, cur_z_start), (dx, dy, dz), r_c, turns_c, phi, base_thick=0.0070)

    # 2. Sienes y patillas (20 rizos)
    for s_side in (1.0, -1.0):
        side_specs = [
            ( 0.040, 1.575,  0.006, -0.048, 0.010, 2.4),
            ( 0.025, 1.572,  0.004, -0.052, 0.011, 2.5),
            ( 0.010, 1.570,  0.002, -0.055, 0.011, 2.6),
            (-0.005, 1.568, -0.002, -0.056, 0.011, 2.5),
            (-0.020, 1.565, -0.004, -0.054, 0.011, 2.4),
            (-0.035, 1.562, -0.006, -0.050, 0.010, 2.3),
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

    # 3. Nuca posterior completa en 3 niveles (30 rizos)
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

    # Sombrero Fedora adaptado
    fedora_bm = bmesh.new()
    n_hat = 32
    hat_levels = [
        (0.000, 0.095, 0.112, -0.004, 1.00, 0.000),
        (0.025, 0.093, 0.110, -0.004, 0.96, 0.000),
        (0.055, 0.088, 0.104, -0.004, 0.90, 0.000),
        (0.080, 0.083, 0.098, -0.004, 0.84, 0.000),
        (0.100, 0.079, 0.092, -0.004, 0.78, 0.016),
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
    sk_blink.value = 0.0
    for v_idx in margin_v_indices:
        sk_blink.data[v_idx].co.z -= 0.0030
        sk_blink.data[v_idx].co.y += 0.0004
    for v_idx in crease_v_indices:
        sk_blink.data[v_idx].co.z -= 0.0015
        sk_blink.data[v_idx].co.y += 0.0002

    return obj_head

# =============================================================================
# 2. CUERPO: CHALECO SASTRE SARTORIAL, CORBATA Y MANOS ANATÓMICAS
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

        # Muñecas y Palmas anatómicas continuas en piel (arquitectura unificada como Eli)
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

    for p in bm.faces:
        c_median = p.calc_center_median()
        center_z = c_median.z
        cx = abs(c_median.x)
        if center_z < 0.10:
            p.material_index = 2 # Zapatos
        elif center_z < 0.94 and cx < 0.18:
            p.material_index = 1 # Pantalón
        elif cx > 0.18 and center_z < 0.915:
            p.material_index = 6 # Mat_Axel_Skin (Muñeca y palma continuas)
        else:
            p.material_index = 0 # Camisa / Manga gris

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
        (1.270, 0.016, 0.124),
        (1.215, 0.015, 0.125),
        (1.150, 0.013, 0.118),
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
    # CHALECO SASTRE SARTORIAL AUTÉNTICO CON ESCOTE EN V ABIERTO Y ESPALDA COMPLETA
    # -------------------------------------------------------------------------
    # 1. Espalda Completa (Curvatura continua de omóplatos a cintura, 7 vértices por fila)
    back_levels = [
        # z,     hw,    y_back, y_side
        (1.380, 0.110, -0.095, -0.040), # 0: Base cuello posterior / hombros
        (1.330, 0.130, -0.112, -0.055), # 1: Pecho alto dorsal
        (1.270, 0.150, -0.124, -0.065), # 2: Omóplatos / axila
        (1.200, 0.156, -0.122, -0.060), # 3: Tórax medio
        (1.130, 0.152, -0.118, -0.050), # 4: Costillas
        (1.060, 0.144, -0.114, -0.040), # 5: Cintura (martingala)
        (0.990, 0.144, -0.112, -0.035), # 6: Cintura baja
        (0.930, 0.148, -0.114, -0.030), # 7: Dobladillo posterior
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
            bm.faces.new((r1[i], r1[i+1], r2[i+1], r2[i])).material_index = 3 # Mat_Axel_Vest

    # 2. Delanteros (Paneles Izquierdo y Derecho con Escote en V)
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

    # -------------------------------------------------------------------------
    # TIRANTES DE HOMBRO ANATÓMICOS Y BANDA DE CUELLO TRASERA (CHALECO CONTINUO 360°)
    # El chaleco pasa SOBRE el hombro (trapecio Z=1.408) y rodea la nuca conectando con la espalda.
    # -------------------------------------------------------------------------
    # Tirante Izquierdo (X > 0): 3 filas sobre el hombro
    sh_l_f = [bm.verts.new((0.055,  0.038, 1.396)), bm.verts.new((0.085,  0.030, 1.396)), bm.verts.new((0.112,  0.022, 1.396))]
    sh_l_m = [bm.verts.new((0.052, -0.008, 1.408)), bm.verts.new((0.082, -0.012, 1.408)), bm.verts.new((0.110, -0.018, 1.408))]
    sh_l_b = [bm.verts.new((0.050, -0.052, 1.398)), bm.verts.new((0.080, -0.054, 1.398)), bm.verts.new((0.108, -0.045, 1.398))]

    # Tirante Derecho (X < 0): simétrico
    sh_r_f = [bm.verts.new((-0.055,  0.038, 1.396)), bm.verts.new((-0.085,  0.030, 1.396)), bm.verts.new((-0.112,  0.022, 1.396))]
    sh_r_m = [bm.verts.new((-0.052, -0.008, 1.408)), bm.verts.new((-0.082, -0.012, 1.408)), bm.verts.new((-0.110, -0.018, 1.408))]
    sh_r_b = [bm.verts.new((-0.050, -0.052, 1.398)), bm.verts.new((-0.080, -0.054, 1.398)), bm.verts.new((-0.108, -0.045, 1.398))]

    # Caras del tirante izquierdo:
    bm.faces.new((front_l_upper[0][0], front_l_upper[0][1], sh_l_f[1], sh_l_f[0])).material_index = 3
    bm.faces.new((front_l_upper[0][1], front_l_upper[0][2], sh_l_f[2], sh_l_f[1])).material_index = 3
    bm.faces.new((sh_l_f[0], sh_l_f[1], sh_l_m[1], sh_l_m[0])).material_index = 3
    bm.faces.new((sh_l_f[1], sh_l_f[2], sh_l_m[2], sh_l_m[1])).material_index = 3
    bm.faces.new((sh_l_m[0], sh_l_m[1], sh_l_b[1], sh_l_b[0])).material_index = 3
    bm.faces.new((sh_l_m[1], sh_l_m[2], sh_l_b[2], sh_l_b[1])).material_index = 3
    bm.faces.new((sh_l_b[0], sh_l_b[1], back_rows[0][5], back_rows[0][4])).material_index = 3
    bm.faces.new((sh_l_b[1], sh_l_b[2], back_rows[0][6], back_rows[0][5])).material_index = 3

    # Caras del tirante derecho:
    bm.faces.new((front_r_upper[0][1], front_r_upper[0][0], sh_r_f[0], sh_r_f[1])).material_index = 3
    bm.faces.new((front_r_upper[0][2], front_r_upper[0][1], sh_r_f[1], sh_r_f[2])).material_index = 3
    bm.faces.new((sh_r_f[1], sh_r_f[0], sh_r_m[0], sh_r_m[1])).material_index = 3
    bm.faces.new((sh_r_f[2], sh_r_f[1], sh_r_m[1], sh_r_m[2])).material_index = 3
    bm.faces.new((sh_r_m[1], sh_r_m[0], sh_r_b[0], sh_r_b[1])).material_index = 3
    bm.faces.new((sh_r_m[2], sh_r_m[1], sh_r_b[1], sh_r_b[2])).material_index = 3
    bm.faces.new((sh_r_b[1], sh_r_b[0], back_rows[0][2], back_rows[0][1])).material_index = 3
    bm.faces.new((sh_r_b[2], sh_r_b[1], back_rows[0][1], back_rows[0][0])).material_index = 3

    # Banda de cuello trasera sobre la nuca (une hombro L y R con el centro de la espalda)
    neck_t_l = bm.verts.new(( 0.026, -0.048, 1.406))
    neck_t_c = bm.verts.new(( 0.000, -0.050, 1.408))
    neck_t_r = bm.verts.new((-0.026, -0.048, 1.406))

    bm.faces.new((sh_l_b[0], neck_t_l, back_rows[0][4], back_rows[0][3])).material_index = 3
    bm.faces.new((neck_t_l, neck_t_c, back_rows[0][3])).material_index = 3
    bm.faces.new((neck_t_c, neck_t_r, back_rows[0][3])).material_index = 3
    bm.faces.new((neck_t_r, sh_r_b[0], back_rows[0][2], back_rows[0][3])).material_index = 3

    # Conectar filas superiores del delantero
    for l in range(2):
        la_in, la_mid, la_out = front_l_upper[l]
        lb_in, lb_mid, lb_out = front_l_upper[l+1]
        bm.faces.new((la_in, la_mid, lb_mid, lb_in)).material_index = 3
        bm.faces.new((la_mid, la_out, lb_out, lb_mid)).material_index = 3

        ra_in, ra_mid, ra_out = front_r_upper[l]
        rb_in, rb_mid, rb_out = front_r_upper[l+1]
        bm.faces.new((ra_mid, ra_in, rb_in, rb_mid)).material_index = 3
        bm.faces.new((ra_out, ra_mid, rb_mid, rb_out)).material_index = 3

    # Delantero inferior cerrado con botones (Z=1.200 a Z=0.930)
    front_specs_lower = [
        # z,     hw,    y_center, y_side
        (1.200, 0.156,  0.134,   -0.060), # 3: Vértice del escote en V / botón 1
        (1.130, 0.152,  0.128,   -0.050), # 4: Costillas / botón 2
        (1.060, 0.144,  0.122,   -0.040), # 5: Cintura / botón 3
        (0.990, 0.144,  0.118,   -0.035), # 6: Cintura baja / botón 4
        (0.930, 0.148,  0.116,   -0.030), # 7: Dobladillo base / botón 5
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

    bm.faces.new((lin_2, lmid_2, fl0[4], fl0[3])).material_index = 3
    bm.faces.new((lmid_2, lout_2, fl0[5], fl0[4])).material_index = 3
    bm.faces.new((lout_2, back_rows[2][6], back_rows[3][6], fl0[6])).material_index = 3
    bm.faces.new((lout_2, fl0[6], fl0[5])).material_index = 3

    bm.faces.new((rmid_2, rin_2, fl0[3], fl0[2])).material_index = 3
    bm.faces.new((rout_2, rmid_2, fl0[2], fl0[1])).material_index = 3
    bm.faces.new((back_rows[2][0], rout_2, fl0[0], back_rows[3][0])).material_index = 3
    bm.faces.new((rout_2, fl0[1], fl0[0])).material_index = 3

    # Conectar filas inferiores y costados
    for l in range(len(front_lower_rows) - 1):
        fa = front_lower_rows[l]
        fb = front_lower_rows[l+1]
        ba = back_rows[l + 3]
        bb = back_rows[l + 4]

        for i in range(6):
            bm.faces.new((fa[i], fa[i+1], fb[i+1], fb[i])).material_index = 3

        bm.faces.new((fa[6], ba[6], bb[6], fb[6])).material_index = 3
        bm.faces.new((ba[0], fa[0], fb[0], bb[0])).material_index = 3

    # Picos sastre delanteros en Z=0.885
    f_last = front_lower_rows[-1]
    peak_l = bm.verts.new(( 0.045, f_last[4].co.y + 0.002, 0.885))
    peak_r = bm.verts.new((-0.045, f_last[2].co.y + 0.002, 0.885))

    bm.faces.new((f_last[3], f_last[4], peak_l)).material_index = 3
    bm.faces.new((f_last[4], f_last[5], peak_l)).material_index = 3
    bm.faces.new((f_last[2], f_last[3], peak_r)).material_index = 3
    bm.faces.new((f_last[1], f_last[2], peak_r)).material_index = 3

    # Martingala posterior con hebilla plateada
    mart_l = bm.verts.new(( 0.075, -0.122, 1.065))
    mart_r = bm.verts.new((-0.075, -0.122, 1.065))
    mart_c1 = bm.verts.new(( 0.014, -0.126, 1.065))
    mart_c2 = bm.verts.new((-0.014, -0.126, 1.065))
    mart_l_b = bm.verts.new(( 0.075, -0.122, 1.045))
    mart_r_b = bm.verts.new((-0.075, -0.122, 1.045))
    mart_c1_b = bm.verts.new(( 0.014, -0.126, 1.045))
    mart_c2_b = bm.verts.new((-0.014, -0.126, 1.045))

    bm.faces.new((mart_l, mart_c1, mart_c1_b, mart_l_b)).material_index = 3
    bm.faces.new((mart_c2, mart_r, mart_r_b, mart_c2_b)).material_index = 3
    bm.faces.new((mart_c1, mart_c2, mart_c2_b, mart_c1_b)).material_index = 5 # Mat_Axel_Silver

    # Botones plateados
    b_zs = [1.200, 1.130, 1.060, 0.990, 0.930]
    for bz in b_zs:
        by = 0.134 + (1.200 - bz) * (-0.030)
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.0048)
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.0, by + 0.006, bz))
        v_map = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            bm.faces.new([v_map[v] for v in f.verts]).material_index = 5
        btn_bm.free()

    # Bolsillos ribeteados horizontales
    p_specs = [(0.068, 0.985, 0.032), (-0.068, 0.985, 0.032)]
    for (px, pz, pw) in p_specs:
        py = 0.120
        p_box = [
            bm.verts.new((px - pw*0.5, py + 0.003, pz + 0.004)),
            bm.verts.new((px + pw*0.5, py + 0.003, pz + 0.004)),
            bm.verts.new((px + pw*0.5, py + 0.003, pz - 0.004)),
            bm.verts.new((px - pw*0.5, py + 0.003, pz - 0.004)),
        ]
        bm.faces.new(p_box).material_index = 3

    # -------------------------------------------------------------------------
    # PUÑOS DE CAMISA Y DEDOS ANATÓMICOS CONECTADOS A LA PALMA CONTINUA (PIEL)
    # Arquitectura idéntica a Eli: Palma continua en el grafo corporal, puño exterior
    # que abraza la muñeca sin cortes y dedos orgánicos con anillos de plata.
    # -------------------------------------------------------------------------
    for is_l in (True, False):
        sign_a = 1.0 if is_l else -1.0
        w_center = Vector((sign_a * 0.325, 0.012, 0.835))
        z_knuckles = 0.842

        # 1. Puño exterior de camisa superpuesto (cuff que rodea la muñeca continua sin cortar)
        n_cuff = 12
        cuff_top, cuff_bot = [], []
        for k in range(n_cuff):
            ang = (2.0 * math.pi * k) / n_cuff
            cx = sign_a * 0.325 + 0.029 * math.cos(ang)
            cy = 0.012 + 0.024 * math.sin(ang)
            cuff_top.append(bm.verts.new((cx, cy, 0.932)))
            cuff_bot.append(bm.verts.new((cx * 1.01, cy * 1.01, 0.908)))
        for k in range(n_cuff):
            kn = (k + 1) % n_cuff
            bm.faces.new((cuff_top[k], cuff_top[kn], cuff_bot[kn], cuff_bot[k])).material_index = 0

        # Botón plateado en el puño exterior
        btn_cuff_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_cuff_bm, u_segments=8, v_segments=6, radius=0.0032)
        bmesh.ops.translate(btn_cuff_bm, verts=btn_cuff_bm.verts, vec=(sign_a * (0.325 + 0.030), 0.012, 0.920))
        for f in btn_cuff_bm.faces:
            bm.faces.new([bm.verts.new(v.co) for v in f.verts]).material_index = 5
        btn_cuff_bm.free()

        # 2. 4 Dedos estilizados orgánicos en reposo anatómico
        finger_specs = [
            ("Index",   w_center.y + 0.013, 0.048, 0.0050, is_l),
            ("Middle",  w_center.y + 0.004, 0.052, 0.0052, is_l),
            ("Ring",    w_center.y - 0.004, 0.048, 0.0048, False),
            ("Pinky",   w_center.y - 0.012, 0.038, 0.0042, False),
        ]
        curl_dir = Vector((-sign_a * 0.70, 0.35, -0.25)).normalized()

        for (f_name, fy, f_len, f_rad, has_ring) in finger_specs:
            fx = sign_a * 0.325
            n_seg = 3
            prev_fring = None
            ring_joints = []
            for s in range(n_seg + 1):
                t = s / float(n_seg)
                fz = z_knuckles - f_len * t
                cur_y = fy + curl_dir.y * (f_len * 0.35 * (t**1.3))
                cur_x = fx + curl_dir.x * (f_len * 0.25 * (t**1.3))
                r_cur = f_rad * (1.0 - 0.28 * t)

                cur_fring = []
                for k in range(6):
                    fang = (2.0 * math.pi * k) / 6.0
                    cur_fring.append(bm.verts.new((cur_x + r_cur * math.cos(fang),
                                                  cur_y + r_cur * math.sin(fang),
                                                  fz + curl_dir.z * (f_len * 0.25 * t))))
                if prev_fring:
                    for k in range(6):
                        knxt = (k + 1) % 6
                        ff = bm.faces.new((prev_fring[k], prev_fring[knxt], cur_fring[knxt], cur_fring[k]))
                        ff.material_index = 6 # Mat_Axel_Skin
                prev_fring = cur_fring
                ring_joints.append(Vector((cur_x, cur_y, fz)))

            tip_v = bm.verts.new((cur_x + curl_dir.x * 0.003, cur_y + curl_dir.y * 0.003, z_knuckles - f_len - 0.003))
            for k in range(6):
                knxt = (k + 1) % 6
                ff_tip = bm.faces.new((prev_fring[knxt], prev_fring[k], tip_v))
                ff_tip.material_index = 6

            # Anillos de plata en mano izquierda (axel2.png)
            if has_ring:
                r_c = (ring_joints[0] + ring_joints[1]) * 0.5
                r_rad = f_rad * 1.30
                r1_pts, r2_pts = [], []
                for k in range(8):
                    ang_r = (2.0 * math.pi * k) / 8.0
                    rx = r_c.x + r_rad * math.cos(ang_r)
                    ry = r_c.y + r_rad * math.sin(ang_r)
                    r1_pts.append(bm.verts.new((rx, ry, r_c.z + 0.0025)))
                    r2_pts.append(bm.verts.new((rx, ry, r_c.z - 0.0025)))
                for k in range(8):
                    kn = (k + 1) % 8
                    bm.faces.new((r1_pts[k], r1_pts[kn], r2_pts[kn], r2_pts[k])).material_index = 5 # Mat_Axel_Silver

        # 3. Pulgar anatómico conectado a la palma
        th_mcp = Vector((sign_a * (0.325 - 0.014), w_center.y + 0.008, 0.846))
        th_len = 0.036
        th_rad_base = 0.0055
        prev_th = None
        for s in range(4):
            t = s / 3.0
            tx = th_mcp.x - sign_a * 0.010 * t
            ty = th_mcp.y + 0.012 * t
            tz = th_mcp.z - 0.024 * t
            r_t = th_rad_base * (1.0 - 0.25 * t)
            cur_th = []
            for k in range(6):
                fang = (2.0 * math.pi * k) / 6.0
                cur_th.append(bm.verts.new((tx + r_t * math.cos(fang),
                                           ty + r_t * math.sin(fang),
                                           tz)))
            if prev_th:
                for k in range(6):
                    kn = (k + 1) % 6
                    bm.faces.new((prev_th[k], prev_th[kn], cur_th[kn], cur_th[k])).material_index = 6
            prev_th = cur_th
        tip_th = bm.verts.new((th_mcp.x - sign_a * 0.012, th_mcp.y + 0.014, th_mcp.z - 0.026))
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
            # 2. Extremidades superiores (|X| > 0.18) - Prioridad absoluta para evitar fugas a piernas
            elif abs(co.x) > 0.18 and co.z < 1.38:
                side = ".L" if co.x > 0 else ".R"
                if co.z < 0.90:
                    obj.vertex_groups["Hand" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.93:
                    t_w = (co.z - 0.90) / 0.03
                    obj.vertex_groups["Forearm" + side].add([v.index], t_w, 'REPLACE')
                    obj.vertex_groups["Hand" + side].add([v.index], 1.0 - t_w, 'REPLACE')
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
# 4. RENDER PREVIEW DE ESTUDIO CINEMATOGRÁFICO Y VISTAS DE CONTROL
# =============================================================================
def render_studio_views():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.device = 'CPU'

    key = bpy.data.objects.new("Key", bpy.data.lights.new("Key", 'AREA'))
    key.data.energy = 90.0
    key.data.size = 1.4
    key.data.color = (1.0, 0.98, 0.95)
    key.location = Vector((-0.6, 1.6, 1.6))
    key.rotation_euler = (math.radians(50.0), 0.0, math.radians(-155.0))
    scene.collection.objects.link(key)

    fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", 'AREA'))
    fill.data.energy = 45.0
    fill.data.size = 1.8
    fill.data.color = (0.94, 0.97, 1.0)
    fill.location = Vector((0.7, 1.6, 1.4))
    scene.collection.objects.link(fill)

    catch = bpy.data.objects.new("EyeCatch", bpy.data.lights.new("EyeCatch", 'AREA'))
    catch.data.energy = 30.0
    catch.data.size = 0.6
    catch.data.color = (1.0, 0.98, 0.96)
    catch.location = Vector((0.0, 1.2, 1.515))
    scene.collection.objects.link(catch)

    rim = bpy.data.objects.new("Rim", bpy.data.lights.new("Rim", 'SPOT'))
    rim.data.energy = 60.0
    rim.data.spot_size = math.radians(65.0)
    rim.data.color = (1.0, 1.0, 1.0)
    rim.location = Vector((0.0, -1.2, 1.8))
    rim.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
    scene.collection.objects.link(rim)

    back_light = bpy.data.objects.new("BackLight", bpy.data.lights.new("BackLight", 'AREA'))
    back_light.data.energy = 75.0
    back_light.data.size = 1.6
    back_light.data.color = (1.0, 0.98, 0.95)
    back_light.location = Vector((0.0, -1.8, 1.3))
    back_light.rotation_euler = (math.radians(-70.0), 0.0, math.radians(180.0))
    scene.collection.objects.link(back_light)

    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.lens = 50.0
    cam.location = Vector((0.02, 1.65, 1.25))
    cam.rotation_euler = (math.radians(88.5), 0.0, math.radians(178.0))
    scene.collection.objects.link(cam)
    scene.camera = cam

    scene.render.resolution_x = 720
    scene.render.resolution_y = 1280
    scene.render.filepath = PREVIEW_PNG
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
    print(f"✓ Render preview principal guardado en: {PREVIEW_PNG}")

    # Guardar vistas multi-ángulo de verificación en scratch
    scene.render.resolution_y = 1080
    views = [
        ("axel_master_front.png", Vector((0.0, 1.65, 1.25)), (math.radians(88.5), 0.0, math.radians(178.0))),
        ("axel_master_profile.png", Vector((1.65, 0.0, 1.45)), (math.radians(88.5), 0.0, math.radians(88.0))),
        ("axel_master_back.png", Vector((0.0, -1.65, 1.25)), (math.radians(91.5), 0.0, math.radians(-2.0))),
        ("axel_master_threequarter.png", Vector((1.15, 1.15, 1.35)), (math.radians(82.0), 0.0, math.radians(135.0))),
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
    print("GENERANDO AXEL CANÓNICO: CABEZA ANATÓMICA, RIZOS 360°, CHALECO Y MANOS")
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
    print("✓ Armature canónico construido con 22 huesos.")

    head_obj = build_head_mesh(materials)
    assign_weights(head_obj, is_head=True)
    head_obj.parent = skel
    mod_h = head_obj.modifiers.new("Armature", type='ARMATURE')
    mod_h.object = skel
    print("✓ Player_Head_Mesh generado con ojos a Z=1.515, párpados 3D, shape key 'blink' y 94 rizos 360°.")

    body_obj = build_body_mesh(materials)
    assign_weights(body_obj, is_head=False)
    body_obj.parent = skel
    mod_b = body_obj.modifiers.new("Armature", type='ARMATURE')
    mod_b.object = skel
    print("✓ Player_Body_Mesh generado con chaleco sartorial en V, espalda cubierta, martingala y manos blindadas.")

    # Verificación de pesos
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
    print("PROCESO AXEL COMPLETADO EXITOSAMENTE")
    print("=" * 60)

if __name__ == "__main__":
    main()
