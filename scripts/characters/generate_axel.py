"""
Axel Master Generator - Versión Anatómica, Expresiva y Proporcionada
Cotas craneales humanas compactas, ojos almendrados a la altura anatómica correcta (Z=1.515),
Shape Key 'blink' para parpadeo biológico, cabellera rizada voluminosa y abundante ("the hair was fine"),
manos anatómicas semi-pronadas con dedos curvados en reposo y anillos de plata,
sombrero fedora manifold simétrico y traje sastre entallado.
Fiel a scratch/humans/axel2.png y axel2_face_crop.png
"""

import bpy
import bmesh
import math
import os
import numpy as np
from mathutils import Vector, Matrix, Euler, Quaternion

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
TEXTURES_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/textures")
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
# 1. CABEZA PROPORCIONADA, OJOS DESCENDIDOS A Z=1.515, PÁRPADOS 3D Y RIZOS
# =============================================================================
def build_head_mesh(materials):
    me = bpy.data.meshes.new("Player_Head_Mesh_Data")
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")

    n_ring = 32
    # Cotas anatómicas compactas: ojos en Z = 1.515 (no altos), mandíbula angular definida
    head_profile = [
        # z, rx, ry_front, ry_back, y_offset, v_uv
        (1.375, 0.050, 0.046, 0.050, 0.005, 0.12), # 0: Base cuello
        (1.395, 0.048, 0.044, 0.048, 0.006, 0.18), # 1: Cuello medio
        (1.412, 0.052, 0.046, 0.052, 0.008, 0.24), # 2: Submandíbula
        (1.428, 0.058, 0.062, 0.058, 0.012, 0.30), # 3: Mentón con perilla
        (1.442, 0.065, 0.060, 0.064, 0.010, 0.35), # 4: Ángulo gonial
        (1.454, 0.068, 0.072, 0.068, 0.008, 0.38), # 5: Labio inferior
        (1.464, 0.070, 0.065, 0.070, 0.007, 0.40), # 6: Hendidura labial
        (1.474, 0.071, 0.074, 0.071, 0.005, 0.43), # 7: Labio superior con arco Cupido
        (1.488, 0.074, 0.068, 0.074, 0.003, 0.48), # 8: Base nasal
        (1.502, 0.077, 0.090, 0.077, 0.001, 0.54), # 9: Punta nasal recta
        (1.515, 0.081, 0.070, 0.080, 0.000, 0.63), # 10: Altura de OJOS (Z = 1.515)
        (1.530, 0.082, 0.080, 0.081, -0.002, 0.72),# 11: Pómulos y cejas (Z = 1.530)
        (1.548, 0.080, 0.072, 0.081, -0.004, 0.79),# 12: Frente baja
        (1.568, 0.077, 0.066, 0.078, -0.006, 0.85),# 13: Frente media
        (1.588, 0.072, 0.056, 0.074, -0.008, 0.91),# 14: Asiento sombrero
        (1.615, 0.060, 0.042, 0.062, -0.010, 0.96),# 15: Bóveda craneal
        (1.635, 0.038, 0.026, 0.040, -0.012, 0.99),# 16: Coronilla
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

            if l_idx in (5, 6, 7) and 0.38 * math.pi <= ang <= 0.62 * math.pi:
                m_dist = abs(ang - 0.5 * math.pi) / 0.12
                mw = max(0.0, 1.0 - m_dist**2)
                if l_idx == 5: y += 0.010 * mw
                elif l_idx == 6: y -= 0.006 * mw
                elif l_idx == 7: y += 0.009 * mw

            if l_idx in (8, 9) and 0.42 * math.pi <= ang <= 0.58 * math.pi:
                nw = max(0.0, 1.0 - abs(ang - 0.5 * math.pi) / 0.16)
                y += (0.022 if l_idx == 9 else 0.010) * nw

            if l_idx == 3 and 0.40 * math.pi <= ang <= 0.60 * math.pi:
                cw = max(0.0, 1.0 - abs(ang - 0.5 * math.pi) / 0.20)
                y += 0.014 * cw

            # Hendidura orbital profunda para albergar ojos 3D
            if l_idx == 10 and (0.28 * math.pi <= ang <= 0.44 * math.pi or 0.56 * math.pi <= ang <= 0.72 * math.pi):
                y -= 0.022

            cur_ring.append(bm.verts.new((x, y, z)))
            u_coord = ((ang - 0.5 * math.pi) / (2.0 * math.pi) + 0.5) % 1.0
            cur_u.append(u_coord)
        rings.append((cur_ring, cur_u, v_uv))

    for l_idx in range(len(head_profile) - 1):
        r1, u1, v1 = rings[l_idx]
        r2, u2, v2 = rings[l_idx + 1]
        for i in range(n_ring):
            inxt = (i + 1) % n_ring
            f = bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))
            f.material_index = 0

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

    # -------------------------------------------------------------------------
    # A. OJOS 3D AVELLANA Y PÁRPADOS ALMENDRADOS EN Z = 1.515
    # -------------------------------------------------------------------------
    eye_pos = [(0.033, 0.052, 1.515), (-0.033, 0.052, 1.515)]
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
        u_center = 0.43 if ex > 0 else 0.57
        n_pts = 9
        upper_margin = []
        upper_crease = []
        upper_brow = []
        lower_margin = []
        lower_crease = []

        for i in range(n_pts):
            t = (i / float(n_pts - 1)) * 2.0 - 1.0
            dx = t * 0.0135 * sign_side
            arch_sup = math.sqrt(max(0.0, 1.0 - t**2))

            # Párpado superior cubre el 25% superior del iris (mirada relajada humana)
            dz_margin_sup = 0.0030 * arch_sup + 0.0008 * t
            dz_margin_inf = -0.0040 * arch_sup + 0.0004 * t

            dy_margin = math.sqrt(max(0.0001, (eye_r * 1.04)**2 - dx**2 - dz_margin_sup**2))
            dy_margin_inf = math.sqrt(max(0.0001, (eye_r * 1.04)**2 - dx**2 - dz_margin_inf**2))

            v_um = bm.verts.new((ex + dx, ey + dy_margin, ez + dz_margin_sup))
            v_uc = bm.verts.new((ex + dx, ey + dy_margin * 0.96 + 0.003, ez + dz_margin_sup + 0.0055 * arch_sup))
            v_ub = bm.verts.new((ex + dx, ey + dy_margin * 0.90 + 0.006, ez + dz_margin_sup + 0.0120 * arch_sup))

            v_lm = bm.verts.new((ex + dx, ey + dy_margin_inf, ez + dz_margin_inf))
            v_lc = bm.verts.new((ex + dx, ey + dy_margin_inf * 0.95 + 0.004, ez + dz_margin_inf - 0.0070 * arch_sup))

            upper_margin.append(v_um)
            upper_crease.append(v_uc)
            upper_brow.append(v_ub)
            lower_margin.append(v_lm)
            lower_crease.append(v_lc)

        upper_lid_margin_verts.extend(upper_margin)
        upper_lid_crease_verts.extend(upper_crease)

        for i in range(n_pts - 1):
            f1 = bm.faces.new((upper_margin[i], upper_margin[i+1], upper_crease[i+1], upper_crease[i]))
            f1.material_index = 0
            f2 = bm.faces.new((upper_crease[i], upper_crease[i+1], upper_brow[i+1], upper_brow[i]))
            f2.material_index = 0
            f3 = bm.faces.new((lower_crease[i], lower_crease[i+1], lower_margin[i+1], lower_margin[i]))
            f3.material_index = 0

            for f_sub in (f1, f2, f3):
                for loop in f_sub.loops:
                    loop[uv_lay].uv = (u_center, 0.63)

    # -------------------------------------------------------------------------
    # B. CABELLERA RIZADA VOLUMINOSA Y ABUNDANTE ("THE HAIR WAS FINE")
    # -------------------------------------------------------------------------
    def add_curl(p_start, p_delta, r_curl, turns, phi0, base_thick=0.0068, n_steps=14):
        prev_ring = None
        for s in range(n_steps):
            t = s / float(n_steps - 1)
            cx = p_start[0] + p_delta[0] * t
            cy = p_start[1] + p_delta[1] * t
            cz = p_start[2] + p_delta[2] * t
            cur_r = r_curl * (1.0 - 0.30 * t)
            phase = 2.0 * math.pi * turns * t + phi0
            sp_x = cx + cur_r * math.cos(phase)
            sp_y = cy + cur_r * math.sin(phase)
            sp_z = cz
            tb_r = base_thick * (1.0 - 0.40 * t)
            c_ring = []
            for k in range(5):
                k_ang = (2.0 * math.pi * k) / 5.0
                c_ring.append(bm.verts.new((sp_x + tb_r * math.cos(k_ang),
                                           sp_y + tb_r * math.sin(k_ang) * 0.7,
                                           sp_z + tb_r * math.sin(k_ang) * 0.8)))
            if prev_ring:
                for k in range(5):
                    kn = (k + 1) % 5
                    f_c = bm.faces.new((prev_ring[k], prev_ring[kn], c_ring[kn], c_ring[k]))
                    f_c.material_index = 2 # mat_hair
            prev_ring = c_ring

    # 1. Mechones frontales voluminosos (brotan en Z ~ 1.585 y caen a Z ~ 1.545, sobre la frente alta)
    frontal_curls = [
        ( 0.000, 0.068, 1.585,  0.003, 0.016, -0.038, 0.011, 2.2, 0.2, 0.0070),
        ( 0.015, 0.066, 1.583,  0.006, 0.015, -0.040, 0.011, 2.4, 0.9, 0.0068),
        (-0.015, 0.066, 1.583, -0.006, 0.015, -0.040, 0.011, 2.4, 1.6, 0.0068),
        ( 0.028, 0.063, 1.580,  0.009, 0.014, -0.042, 0.010, 2.3, 2.3, 0.0066),
        (-0.028, 0.063, 1.580, -0.009, 0.014, -0.042, 0.010, 2.3, 3.0, 0.0066),
        ( 0.042, 0.058, 1.577,  0.012, 0.012, -0.044, 0.010, 2.1, 3.8, 0.0065),
        (-0.042, 0.058, 1.577, -0.012, 0.012, -0.044, 0.010, 2.1, 4.5, 0.0065),
        ( 0.054, 0.050, 1.574,  0.013, 0.010, -0.044, 0.009, 2.0, 0.6, 0.0062),
        (-0.054, 0.050, 1.574, -0.013, 0.010, -0.044, 0.009, 2.0, 1.8, 0.0062),
        ( 0.008, 0.070, 1.590,  0.005, 0.018, -0.035, 0.012, 2.0, 1.2, 0.0072),
        (-0.008, 0.070, 1.590, -0.005, 0.018, -0.035, 0.012, 2.0, 2.8, 0.0072),
        ( 0.022, 0.067, 1.587,  0.009, 0.016, -0.038, 0.011, 2.3, 0.5, 0.0068),
        (-0.022, 0.067, 1.587, -0.009, 0.016, -0.038, 0.011, 2.3, 3.6, 0.0068),
    ]
    for c in frontal_curls:
        add_curl(c[:3], c[3:6], c[6], c[7], c[8], c[9])

    # 2. Patillas rizadas y sienes (delante de las orejas)
    side_curls = [
        ( 0.066, 0.038, 1.572,  0.010, 0.008, -0.052, 0.010, 2.5, 0.5, 0.0068),
        ( 0.072, 0.024, 1.570,  0.008, 0.006, -0.056, 0.010, 2.6, 1.4, 0.0070),
        ( 0.074, 0.010, 1.568,  0.006, 0.004, -0.058, 0.010, 2.7, 2.3, 0.0070),
        ( 0.072,-0.006, 1.566,  0.005, 0.002, -0.060, 0.011, 2.6, 3.2, 0.0072),
        (-0.066, 0.038, 1.572, -0.010, 0.008, -0.052, 0.010, 2.5, 1.7, 0.0068),
        (-0.072, 0.024, 1.570, -0.008, 0.006, -0.056, 0.010, 2.6, 2.6, 0.0070),
        (-0.074, 0.010, 1.568, -0.006, 0.004, -0.056, 0.010, 2.7, 3.5, 0.0070),
        (-0.072,-0.006, 1.566, -0.005, 0.002, -0.060, 0.011, 2.6, 4.4, 0.0072),
    ]
    for c in side_curls:
        add_curl(c[:3], c[3:6], c[6], c[7], c[8], c[9])

    # 3. Nuca y laterales posteriores
    nape_angles = np.linspace(-math.pi * 0.85, -math.pi * 0.15, 12)
    for i, ang in enumerate(nape_angles):
        nx = 0.070 * math.cos(ang)
        ny = 0.072 * math.sin(ang) - 0.006
        nz = 1.570
        dx = 0.006 * math.cos(ang)
        dy = 0.006 * math.sin(ang)
        dz = -0.048 - 0.008 * abs(math.cos(ang))
        r_c = 0.009 + 0.002 * (i % 3)
        t_c = 2.2 + 0.3 * (i % 2)
        phi = 0.7 * i
        add_curl((nx, ny, nz), (dx, dy, dz), r_c, t_c, phi, 0.0065)

    # -------------------------------------------------------------------------
    # C. SOMBRERO FEDORA MANIFOLD CON TEARDROP PINCH Y SNAP-BRIM SIMÉTRICO
    # -------------------------------------------------------------------------
    fedora_bm = bmesh.new()
    n_hat = 32
    hat_levels = [
        # z_local, rx, ry, y_c, pinch_x, crease
        (0.000, 0.092, 0.100, 0.000, 1.00, 0.000), # 0: Cinta
        (0.025, 0.090, 0.098, 0.000, 0.96, 0.000), # 1: Copa baja
        (0.055, 0.086, 0.094, 0.000, 0.90, 0.000), # 2: Copa media
        (0.080, 0.082, 0.090, 0.000, 0.84, 0.000), # 3: Copa alta
        (0.100, 0.078, 0.086, 0.000, 0.78, 0.016), # 4: Corona Teardrop
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
        m_idx = 4 if l == 0 else 3 # 4: Cinta, 3: Fedora
        for i in range(n_hat):
            inxt = (i + 1) % n_hat
            f = fedora_bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))
            f.material_index = m_idx

    top_c = fedora_bm.verts.new((0.0, 0.0, 0.088))
    for i in range(n_hat):
        inxt = (i + 1) % n_hat
        f = fedora_bm.faces.new((fed_rings[-1][i], fed_rings[-1][inxt], top_c))
        f.material_index = 3

    # Ala simétrica manifold
    b_in_top = fed_rings[0]
    b_out_top = []
    b_out_bot = []
    b_in_bot = []

    for i in range(n_hat):
        ang = (2.0 * math.pi * i) / n_hat
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        curl_z = 0.012 * (cos_a**2) - 0.005 * max(0.0, sin_a)
        bx = 0.160 * cos_a
        by = 0.170 * sin_a
        bz = curl_z
        b_out_top.append(fedora_bm.verts.new((bx, by, bz + 0.0015)))
        b_out_bot.append(fedora_bm.verts.new((bx, by, bz - 0.0015)))
        in_co = fed_rings[0][i].co
        b_in_bot.append(fedora_bm.verts.new((in_co.x * 0.98, in_co.y * 0.98, in_co.z - 0.003)))

    for i in range(n_hat):
        inxt = (i + 1) % n_hat
        f_top = fedora_bm.faces.new((b_in_top[inxt], b_in_top[i], b_out_top[i], b_out_top[inxt]))
        f_top.material_index = 3
        f_rim = fedora_bm.faces.new((b_out_top[i], b_out_bot[i], b_out_bot[inxt], b_out_top[inxt]))
        f_rim.material_index = 3
        f_bot = fedora_bm.faces.new((b_out_bot[i], b_in_bot[i], b_in_bot[inxt], b_out_bot[inxt]))
        f_bot.material_index = 3

    # Transformación: inclinado hacia atrás -6 grados y asentado en Z = 1.585
    xform = Matrix.Translation(Vector((0.0, -0.008, 1.585))) @ Matrix.Rotation(math.radians(-6.0), 4, 'X')
    bmesh.ops.transform(fedora_bm, matrix=xform, verts=fedora_bm.verts)

    v_f_map = {v: bm.verts.new(v.co) for v in fedora_bm.verts}
    for f in fedora_bm.faces:
        nf = bm.faces.new([v_f_map[v] for v in f.verts])
        nf.material_index = f.material_index
    fedora_bm.free()

    bm.normal_update()
    for f in bm.faces: f.smooth = True

    bm.verts.ensure_lookup_table()
    margin_v_indices = [v.index for v in upper_lid_margin_verts]
    crease_v_indices = [v.index for v in upper_lid_crease_verts]

    bm.to_mesh(me)
    bm.free()

    obj = bpy.data.objects.new("Player_Head_Mesh", me)
    bpy.context.scene.collection.objects.link(obj)
    for mat in materials["head"]:
        obj.data.materials.append(mat)

    # -------------------------------------------------------------------------
    # D. SHAPE KEYS: PARPADEO EXPRESIVO ("BLINK")
    # -------------------------------------------------------------------------
    sk_basis = obj.shape_key_add(name="Basis")
    sk_blink = obj.shape_key_add(name="blink")
    for v_idx in margin_v_indices:
        sk_blink.data[v_idx].co.z -= 0.0068
        sk_blink.data[v_idx].co.y += 0.0008
    for v_idx in crease_v_indices:
        sk_blink.data[v_idx].co.z -= 0.0034
        sk_blink.data[v_idx].co.y += 0.0004

    sub = obj.modifiers.new("Subsurf", type='SUBSURF')
    sub.levels = 1
    sub.render_levels = 1
    return obj

# =============================================================================
# 2. CUERPO: CHALECO SASTRE, CORBATA Y MANOS ANATÓMICAS CON REPOSO ORGÁNICO
# =============================================================================
def build_body_mesh(materials):
    mesh_graph = bpy.data.meshes.new("Body_Graph_Data")
    obj_body = bpy.data.objects.new("Player_Body_Mesh", mesh_graph)
    bpy.context.scene.collection.objects.link(obj_body)

    nodes = [
        # Tronco
        (0.00,  0.00, 0.82, 0.130, 0.100), # 0: Pelvis base
        (0.00,  0.00, 0.94, 0.145, 0.105), # 1: Caderas / Cintura pantalón
        (0.00,  0.00, 1.04, 0.135, 0.098), # 2: Cintura entallada
        (0.00,  0.00, 1.16, 0.155, 0.110), # 3: Costillas
        (0.00,  0.00, 1.28, 0.170, 0.120), # 4: Pectorales
        (0.00,  0.00, 1.36, 0.150, 0.105), # 5: Clavículas / hombros
        (0.00,  0.00, 1.40, 0.050, 0.050), # 6: Base del cuello

        # Brazos (+X Left, -X Right)
        ( 0.06, 0.00, 1.36, 0.070, 0.070), # 7
        ( 0.18, 0.00, 1.34, 0.062, 0.062), # 8: Hombro L
        ( 0.26, 0.00, 1.15, 0.050, 0.050), # 9: Codo L
        ( 0.33, 0.01, 0.92, 0.036, 0.032), # 10: Manga / Puño L

        (-0.06, 0.00, 1.36, 0.070, 0.070), # 11
        (-0.18, 0.00, 1.34, 0.062, 0.062), # 12: Hombro R
        (-0.26, 0.00, 1.15, 0.050, 0.050), # 13: Codo R
        (-0.33, 0.01, 0.92, 0.036, 0.032), # 14: Manga / Puño R

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

    # -------------------------------------------------------------------------
    # A. CUELLO CAMISERO
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # B. CORBATA CONTINUA
    # -------------------------------------------------------------------------
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
    # C. CHALECO SASTRE ENTALLADO CON ESCOTE EN V
    # -------------------------------------------------------------------------
    v_levels = [
        (1.410, 0.055, 0.065,  1.390, 0.085, 0.055,  1.365, 0.112, 0.040, -0.075, 1.385),
        (1.360, 0.042, 0.096,  1.345, 0.088, 0.092,  1.315, 0.135, 0.070, -0.092, 1.335),
        (1.290, 0.022, 0.122,  1.285, 0.086, 0.118,  1.255, 0.150, 0.050, -0.106, 1.275),
        (1.220, 0.000, 0.132,  1.220, 0.084, 0.124,  1.220, 0.158, 0.015, -0.112, 1.220),
        (1.150, 0.000, 0.127,  1.150, 0.082, 0.120,  1.150, 0.156, 0.000, -0.108, 1.150),
        (1.080, 0.000, 0.123,  1.080, 0.078, 0.116,  1.080, 0.150, -0.005, -0.104, 1.080),
        (1.010, 0.000, 0.120,  1.010, 0.075, 0.114,  1.010, 0.148, -0.005, -0.102, 1.010),
        (0.940, 0.000, 0.118,  0.940, 0.074, 0.112,  0.940, 0.152, -0.005, -0.104, 0.940),
    ]

    front_l_rows = []
    front_r_rows = []
    back_rows = []

    for (z_in, in_x, in_y, z_mid, mid_x, mid_y, z_out, out_x, out_y, b_y, b_z) in v_levels:
        vl_in = bm.verts.new(( in_x,  in_y, z_in))
        vl_mid = bm.verts.new(( mid_x, mid_y, z_mid))
        vl_out = bm.verts.new(( out_x, out_y, z_out))
        front_l_rows.append((vl_in, vl_mid, vl_out))

        if in_x == 0.0:
            vr_in = vl_in
        else:
            vr_in = bm.verts.new((-in_x,  in_y, z_in))
        vr_mid = bm.verts.new((-mid_x, mid_y, z_mid))
        vr_out = bm.verts.new((-out_x, out_y, z_out))
        front_r_rows.append((vr_in, vr_mid, vr_out))

        vb_c = bm.verts.new(( 0.000, b_y, b_z))
        vb_l = bm.verts.new(( mid_x, b_y + 0.005, b_z))
        vb_r = bm.verts.new((-mid_x, b_y + 0.005, b_z))
        back_rows.append((vb_r, vb_c, vb_l))

    for l in range(len(v_levels) - 1):
        (in_a, mid_a, out_a) = front_l_rows[l]
        (in_b, mid_b, out_b) = front_l_rows[l + 1]
        bm.faces.new((in_a, mid_a, mid_b, in_b)).material_index = 3
        bm.faces.new((mid_a, out_a, out_b, mid_b)).material_index = 3

        (rin_a, rmid_a, rout_a) = front_r_rows[l]
        (rin_b, rmid_b, rout_b) = front_r_rows[l + 1]
        bm.faces.new((rmid_a, rin_a, rin_b, rmid_b)).material_index = 3
        bm.faces.new((rout_a, rmid_a, rmid_b, rout_b)).material_index = 3

        (br_a, bc_a, bl_a) = back_rows[l]
        (br_b, bc_b, bl_b) = back_rows[l + 1]
        bm.faces.new((br_a, bc_a, bc_b, br_b)).material_index = 0
        bm.faces.new((bc_a, bl_a, bl_b, bc_b)).material_index = 0

        if l >= 3:
            bm.faces.new((out_a, bl_a, bl_b, out_b)).material_index = 3
            bm.faces.new((br_a, rout_a, rout_b, br_b)).material_index = 3

    in_0, mid_0, out_0 = front_l_rows[0]
    rin_0, rmid_0, rout_0 = front_r_rows[0]
    br_0, bc_0, bl_0 = back_rows[0]
    bm.faces.new((in_0, mid_0, bl_0, bc_0)).material_index = 3
    bm.faces.new((mid_0, out_0, bl_0)).material_index = 3
    bm.faces.new((rin_0, bc_0, br_0, rmid_0)).material_index = 3
    bm.faces.new((rmid_0, br_0, rout_0)).material_index = 3

    bot_l_in, bot_l_mid, bot_l_out = front_l_rows[-1]
    bot_r_in, bot_r_mid, bot_r_out = front_r_rows[-1]
    peak_l = bm.verts.new(( 0.042, 0.116, 0.880))
    peak_r = bm.verts.new((-0.042, 0.116, 0.880))

    bm.faces.new((bot_l_in, bot_l_mid, peak_l)).material_index = 3
    bm.faces.new((bot_l_mid, bot_l_out, peak_l)).material_index = 3
    bm.faces.new((bot_r_mid, bot_r_in, peak_r)).material_index = 3
    bm.faces.new((bot_r_out, bot_r_mid, peak_r)).material_index = 3

    b_zs = [1.220, 1.150, 1.080, 1.010, 0.940]
    for bz in b_zs:
        by = 0.126 + (1.220 - bz) * (-0.008)
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.0045)
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.0, by + 0.007, bz))
        v_map = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            nf = bm.faces.new([v_map[v] for v in f.verts])
            nf.material_index = 5 # Plata
        btn_bm.free()

    p_specs = [(0.070, 0.985, 0.032), (-0.070, 0.985, 0.032), (0.065, 1.140, 0.026)]
    for (px, pz, pw) in p_specs:
        py = 0.122
        p_box = [
            bm.verts.new((px - pw*0.5, py + 0.003, pz + 0.004)),
            bm.verts.new((px + pw*0.5, py + 0.003, pz + 0.004)),
            bm.verts.new((px + pw*0.5, py + 0.003, pz - 0.004)),
            bm.verts.new((px - pw*0.5, py + 0.003, pz - 0.004)),
        ]
        bm.faces.new(p_box).material_index = 3

    # -------------------------------------------------------------------------
    # D. PUÑOS DE CAMISA Y MANOS ANATÓMICAS CON REPOSO ORGÁNICO
    # -------------------------------------------------------------------------
    for is_left in (True, False):
        sign_h = 1.0 if is_left else -1.0
        w_center = Vector((sign_h * 0.33, 0.010, 0.920))

        # 1. Puño de camisa (Cuff) que envuelve la muñeca
        n_cuff = 12
        cuff_top = []
        cuff_bot = []
        for k in range(n_cuff):
            ang = (2.0 * math.pi * k) / n_cuff
            cx = w_center.x + 0.030 * math.cos(ang)
            cy = w_center.y + 0.026 * math.sin(ang)
            cuff_top.append(bm.verts.new((cx, cy, 0.925)))
            cuff_bot.append(bm.verts.new((cx * 1.02, cy * 1.02, 0.898)))
        for k in range(n_cuff):
            kn = (k + 1) % n_cuff
            f_cuff = bm.faces.new((cuff_top[k], cuff_top[kn], cuff_bot[kn], cuff_bot[k]))
            f_cuff.material_index = 0 # Camisa

        # 2. Muñeca anatómica de piel que emerge del puño
        wrist_v = []
        for k in range(n_cuff):
            ang = (2.0 * math.pi * k) / n_cuff
            wx = w_center.x + 0.022 * math.cos(ang)
            wy = w_center.y + 0.018 * math.sin(ang)
            wrist_v.append(bm.verts.new((wx, wy, 0.905)))
        for k in range(n_cuff):
            kn = (k + 1) % n_cuff
            bm.faces.new((wrist_v[k], wrist_v[kn], cuff_bot[kn], cuff_bot[k])).material_index = 6

        # 3. Palma anatómica semi-pronada (orientada hacia el muslo en -X para L)
        z_knuckles = 0.845
        x_in = w_center.x - sign_h * 0.013
        x_out = w_center.x + sign_h * 0.013
        y_ant = w_center.y + 0.026
        y_post = w_center.y - 0.024

        p_box = [
            bm.verts.new((x_in,  y_ant,  0.895)), # 0: Muñeca-palma ant
            bm.verts.new((x_out, y_ant,  0.895)), # 1: Muñeca-dorso ant
            bm.verts.new((x_out, y_post, 0.895)), # 2: Muñeca-dorso post
            bm.verts.new((x_in,  y_post, 0.895)), # 3: Muñeca-palma post
            bm.verts.new((x_in,  y_ant,  z_knuckles)), # 4: Nudillo índice (palmar)
            bm.verts.new((x_out, y_ant,  z_knuckles)), # 5: Nudillo índice (dorsal)
            bm.verts.new((x_out, y_post, z_knuckles)), # 6: Nudillo meñique (dorsal)
            bm.verts.new((x_in,  y_post, z_knuckles)), # 7: Nudillo meñique (palmar)
        ]
        bm.faces.new((p_box[0], p_box[1], p_box[5], p_box[4])).material_index = 6
        bm.faces.new((p_box[1], p_box[2], p_box[6], p_box[5])).material_index = 6
        bm.faces.new((p_box[2], p_box[3], p_box[7], p_box[6])).material_index = 6
        bm.faces.new((p_box[3], p_box[0], p_box[4], p_box[7])).material_index = 6

        # 4. Dedos articulados con 3 falanges en arco relajado natural de reposo
        finger_specs = [
            # name, y_pos, len, rad, curl_factor, has_ring
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
                        f_seg = bm.faces.new((prev_ring[k], prev_ring[kn], cur_ring[kn], cur_ring[k]))
                        f_seg.material_index = 6
                prev_ring = cur_ring
                ring_joints.append(pt)

            tip_v = bm.verts.new(p3 + curl_dir * 0.003 - Vector((0, 0, 0.003)))
            for k in range(6):
                kn = (k + 1) % 6
                f_tip = bm.faces.new((prev_ring[kn], prev_ring[k], tip_v))
                f_tip.material_index = 6

            # Anillos plateados auténticos en mano izquierda (Índice y Medio)
            if has_ring:
                r_c = (ring_joints[0] + ring_joints[1]) * 0.5
                r_rad = frad * 1.30
                r1_pts = []
                r2_pts = []
                for k in range(8):
                    ang_r = (2.0 * math.pi * k) / 8.0
                    rx = r_c.x + r_rad * math.cos(ang_r)
                    ry = r_c.y + r_rad * math.sin(ang_r)
                    r1_pts.append(bm.verts.new((rx, ry, r_c.z + 0.0035)))
                    r2_pts.append(bm.verts.new((rx, ry, r_c.z - 0.0035)))
                for k in range(8):
                    kn = (k + 1) % 8
                    f_rng = bm.faces.new((r1_pts[k], r1_pts[kn], r2_pts[kn], r2_pts[k]))
                    f_rng.material_index = 5 # mat_silver

        # 5. Pulgar en oposición anatómica
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
                    f_th = bm.faces.new((prev_th[k], prev_th[kn], cur_ring[kn], cur_ring[k]))
                    f_th.material_index = 6
            prev_th = cur_ring
        tip_th = bm.verts.new(th_joints[-1] + Vector((-sign_h * 0.002, 0.003, -0.003)))
        for k in range(6):
            kn = (k + 1) % 6
            f_th_tip = bm.faces.new((prev_th[kn], prev_th[k], tip_th))
            f_th_tip.material_index = 6

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
            # 1. Pies y dedos de los pies (confinados a |X| <= 0.18)
            if co.z < 0.04 and abs(co.x) <= 0.18:
                obj.vertex_groups["Toes.L" if co.x > 0 else "Toes.R"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.12 and abs(co.x) <= 0.18:
                obj.vertex_groups["Foot.L" if co.x > 0 else "Foot.R"].add([v.index], 1.0, 'REPLACE')
            # 2. Extremidades superiores completas (|X| > 0.18): Hombros, brazos, antebrazos, manos y dedos
            elif abs(co.x) > 0.18 and co.z < 1.38:
                side = ".L" if co.x > 0 else ".R"
                if co.z < 0.93:
                    obj.vertex_groups["Hand" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.15:
                    obj.vertex_groups["Forearm" + side].add([v.index], 1.0, 'REPLACE')
                else:
                    obj.vertex_groups["UpperArm" + side].add([v.index], 1.0, 'REPLACE')
            # 3. Extremidades inferiores (|X| <= 0.18): Piernas, rodillas y muslos
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
# 4. RENDER PREVIEW DE ESTUDIO CINEMATOGRÁFICO
# =============================================================================
def render_preview():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.device = 'CPU'

    # Luz clave principal
    key = bpy.data.objects.new("Key", bpy.data.lights.new("Key", 'AREA'))
    key.data.energy = 90.0
    key.data.size = 1.4
    key.data.color = (1.0, 0.98, 0.95)
    key.location = Vector((-0.6, 1.6, 1.6))
    key.rotation_euler = (math.radians(50.0), 0.0, math.radians(-155.0))
    scene.collection.objects.link(key)

    # Luz de relleno suave
    fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", 'AREA'))
    fill.data.energy = 45.0
    fill.data.size = 1.8
    fill.data.color = (0.94, 0.97, 1.0)
    fill.location = Vector((0.7, 1.6, 1.4))
    scene.collection.objects.link(fill)

    # Luz frontal dedicada para ojos e iris avellana
    catch = bpy.data.objects.new("EyeCatch", bpy.data.lights.new("EyeCatch", 'AREA'))
    catch.data.energy = 30.0
    catch.data.size = 0.6
    catch.data.color = (1.0, 0.98, 0.96)
    catch.location = Vector((0.0, 1.2, 1.515))
    scene.collection.objects.link(catch)

    # Contraluz de silueta (Rim)
    rim = bpy.data.objects.new("Rim", bpy.data.lights.new("Rim", 'SPOT'))
    rim.data.energy = 60.0
    rim.data.spot_size = math.radians(65.0)
    rim.data.color = (1.0, 1.0, 1.0)
    rim.location = Vector((0.0, -1.2, 1.8))
    rim.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
    scene.collection.objects.link(rim)

    # Cámara encuadrando medio cuerpo (desde manos hasta sombrero)
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
    print(f"✓ Render preview guardado en: {PREVIEW_PNG}")

def main():
    print("=" * 60)
    print("GENERANDO AXEL CON OJOS EN ALTURA CORRECTA (Z=1.515) Y MANOS ANATÓMICAS")
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
    print("✓ Player_Head_Mesh generado con ojos en Z=1.515, párpados 3D almendrados, shape key 'blink' y rizos voluminosos.")
    
    body_obj = build_body_mesh(materials)
    assign_weights(body_obj, is_head=False)
    body_obj.parent = skel
    mod_b = body_obj.modifiers.new("Armature", type='ARMATURE')
    mod_b.object = skel
    print("✓ Player_Body_Mesh generado con puños continuos, manos anatómicas y dedos en reposo natural.")
    
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
    print(f"✓ Exportado .glb en: {OUTPUT_GLB}")
    
    render_preview()
    print("=" * 60)
    print("PROCESO COMPLETADO EXITOSAMENTE")
    print("=" * 60)

if __name__ == "__main__":
    main()
