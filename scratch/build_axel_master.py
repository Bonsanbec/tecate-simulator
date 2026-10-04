"""
Axel Master Generator - Proporciones Humanas Anatómicas Perfectas y Ropa Estratificada
Basado fidedignamente en scratch/humans/axel2.png / axel2.tiff
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
# 1. TEXTURAS FACIALES MEJORADAS CON LABIOS BERMELLÓN Y DETALLE DE AXEL2
# =============================================================================
def generate_enhanced_textures():
    w, h = 2048, 2048
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    u = np.linspace(0.0, 1.0, w)
    v = np.linspace(0.0, 1.0, h)
    uu, vv = np.meshgrid(u, v)

    # Tono base cálido de Axel muestreado directamente de axel2.png (R=0.92, G=0.64, B=0.49)
    base_skin = np.array([0.88, 0.62, 0.48], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = base_skin[c]
    diffuse[:, :, 3] = 1.0

    # Rubor y pómulos prominentes
    r_cheeks_l = np.sqrt(((uu - 0.40) / 0.08)**2 + ((vv - 0.58) / 0.09)**2)
    r_cheeks_r = np.sqrt(((uu - 0.60) / 0.08)**2 + ((vv - 0.58) / 0.09)**2)
    flush = np.maximum(np.clip(1.0 - r_cheeks_l, 0, 1)**2, np.clip(1.0 - r_cheeks_r, 0, 1)**2)
    diffuse[:, :, 0] += flush * 0.08
    diffuse[:, :, 1] += flush * 0.03

    # Puente nasal y dorso de la nariz
    nose_mask = np.clip(1.0 - (np.abs(uu - 0.50) / 0.016), 0.0, 1.0) * np.clip(1.0 - (np.abs(vv - 0.52) / 0.10), 0.0, 1.0)
    diffuse[:, :, 0] += nose_mask * 0.05
    diffuse[:, :, 1] += nose_mask * 0.03
    diffuse[:, :, 2] += nose_mask * 0.01

    # LABIOS BERMELLÓN VISIBLES Y DEFINIDOS (V centrado en 0.415)
    lip_dx = (uu - 0.50) / 0.065
    cupid = np.sin(lip_dx * np.pi) * 0.25
    lip_top = np.clip(1.0 - np.sqrt(lip_dx**2 + ((vv - 0.430 - cupid * 0.008) / 0.024)**2), 0.0, 1.0)
    lip_bot = np.clip(1.0 - np.sqrt((lip_dx * 0.90)**2 + ((vv - 0.400) / 0.025)**2), 0.0, 1.0)

    # Color bermellón natural rico
    col_lip_top = np.array([0.76, 0.38, 0.34])
    col_lip_bot = np.array([0.82, 0.44, 0.40])
    col_lip_slit = np.array([0.22, 0.08, 0.08])

    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lip_top) + col_lip_top[c] * lip_top
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lip_bot) + col_lip_bot[c] * lip_bot

    # Hendidura labial y comisuras oscuras bien marcadas
    slit_m = np.clip(1.0 - np.abs(vv - 0.415) / 0.006, 0.0, 1.0) * np.clip(1.0 - np.abs(lip_dx), 0.0, 1.0)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - slit_m) + col_lip_slit[c] * slit_m

    # Perilla / Goatee de Axel en axel2.png (mentón y bajo labio inferior)
    soul_patch = np.clip(1.0 - np.sqrt(((uu - 0.50) / 0.018)**2 + ((vv - 0.365) / 0.022)**2), 0.0, 1.0)
    goatee_chin = np.clip(1.0 - np.sqrt(((uu - 0.50) / 0.042)**2 + ((vv - 0.29) / 0.055)**2), 0.0, 1.0)
    stubble = np.maximum(soul_patch * 1.2, goatee_chin)
    follicles = (np.sin(uu * 600.0) * np.cos(vv * 600.0) * 0.5 + 0.5)
    stubble_final = np.clip(stubble * (0.50 + 0.40 * follicles), 0.0, 1.0)
    col_beard = np.array([0.16, 0.12, 0.11])
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - stubble_final * 0.85) + col_beard[c] * (stubble_final * 0.85)

    # Cejas masculinas densas arqueadas castaño oscuro (V centrado en 0.72)
    def eyebrow_mask(u_center, v_center, sign_side):
        du = (uu - u_center) * sign_side
        dv = (vv - v_center)
        arch = -1.8 * (du - 0.015)**2 + 0.014
        dist = np.sqrt((du / 0.075)**2 + ((dv - arch) / 0.022)**2)
        eyebrow_m = np.clip(1.0 - dist, 0.0, 1.0)**1.5
        b_noise = np.sin((uu + vv * sign_side) * 380.0) * 0.25 + 0.75
        return eyebrow_m * b_noise

    brows = np.maximum(eyebrow_mask(0.42, 0.72, -1.0), eyebrow_mask(0.58, 0.72, 1.0))
    col_brow = np.array([0.12, 0.09, 0.07])
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - brows) + col_brow[c] * brows

    # Orificios nasales
    for u_n in [0.480, 0.520]:
        d_n = np.sqrt(((uu - u_n) / 0.015)**2 + ((vv - 0.485) / 0.012)**2)
        n_mask = np.clip(1.0 - d_n, 0.0, 1.0)
        for c in range(3):
            diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - n_mask * 0.75) + 0.08 * (n_mask * 0.75)

    # Cuencas y párpados
    for u_eye in [0.425, 0.575]:
        d_orbit = np.sqrt(((uu - u_eye) / 0.065)**2 + ((vv - 0.63) / 0.038)**2)
        socket_shadow = np.clip(1.0 - d_orbit, 0.0, 1.0) * 0.22
        for c in range(3):
            diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - socket_shadow) + (diffuse[:, :, c] * 0.70) * socket_shadow

    # Guardar textura
    arr_clipped = np.clip(diffuse, 0.0, 1.0).astype(np.float32)
    b_img = bpy.data.images.get("axel_face_diffuse")
    if b_img: bpy.data.images.remove(b_img)
    b_img = bpy.data.images.new("axel_face_diffuse", width=w, height=h, alpha=True)
    b_img.pixels.foreach_set(arr_clipped.ravel())
    tex_path = os.path.join(TEXTURES_DIR, "axel_face_diffuse.png")
    b_img.filepath_raw = os.path.abspath(tex_path)
    b_img.file_format = 'PNG'
    b_img.save()
    print(f"✓ Textura facial calibrada guardada en: {tex_path}")

# =============================================================================
# 2. CABEZA ANATÓMICA PROPORCIONADA (CUELLO NORMAL, MANDÍBULA Y BOCA 3D)
# =============================================================================
def build_head_mesh(materials):
    me = bpy.data.meshes.new("Player_Head_Mesh_Data")
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")

    n_ring = 32
    # Perfil anatómico normal masculino (altura chin Z=1.43, boca Z=1.472, nariz Z=1.52, ojos Z=1.565, tope Z=1.68)
    head_profile = [
        # z, rx, ry_front, ry_back, y_offset, v_uv
        (1.380, 0.052, 0.048, 0.052, 0.008, 0.12), # Base del cuello (dentro del cuello camisero)
        (1.405, 0.050, 0.047, 0.050, 0.010, 0.18), # Cuello medio / Nuez de Adán
        (1.420, 0.054, 0.042, 0.054, 0.012, 0.24), # Submandíbula / garganta
        (1.435, 0.065, 0.068, 0.062, 0.018, 0.30), # Mentón y ángulo de mandíbula
        (1.450, 0.068, 0.060, 0.066, 0.015, 0.35), # Surco mentolabial
        (1.462, 0.071, 0.076, 0.069, 0.012, 0.395),# Labio inferior carnosos
        (1.472, 0.072, 0.065, 0.071, 0.010, 0.415),# Hendidura labial / comisuras rehundidas
        (1.482, 0.073, 0.077, 0.073, 0.008, 0.435),# Labio superior con arco de Cupido
        (1.500, 0.074, 0.070, 0.075, 0.005, 0.485),# Filtrum / base nasal
        (1.520, 0.075, 0.092, 0.077, 0.002, 0.535),# Punta nasal prominente
        (1.542, 0.077, 0.080, 0.079, 0.000, 0.585),# Puente nasal / pómulos
        (1.565, 0.077, 0.065, 0.081, -0.002, 0.635),# Cuencas oculares
        (1.590, 0.078, 0.070, 0.082, -0.004, 0.720),# Cejas prominentes
        (1.615, 0.077, 0.066, 0.082, -0.006, 0.810),# Frente
        (1.645, 0.071, 0.056, 0.076, -0.008, 0.890),# Frente alta
        (1.670, 0.058, 0.044, 0.064, -0.010, 0.950),# Bóveda craneal
        (1.685, 0.038, 0.026, 0.042, -0.012, 0.990),# Coronilla
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

            # Esculpido 3D anatómico de la Boca
            if l_idx in (5, 6, 7) and 0.38 * math.pi <= ang <= 0.62 * math.pi:
                m_dist = abs(ang - 0.5 * math.pi) / 0.12
                mw = max(0.0, 1.0 - m_dist**2)
                if l_idx == 5:
                    y += 0.012 * mw # Labio inferior carnosos
                elif l_idx == 6:
                    y -= 0.007 * mw # Hendidura labial rehundida
                elif l_idx == 7:
                    # Arco de Cupido con dos cúspides
                    cupid_dip = math.cos((ang - 0.5 * math.pi) * 20.0) * 0.0035
                    y += (0.011 + cupid_dip) * mw

            # Esculpido de la Nariz
            if l_idx in (8, 9, 10) and 0.40 * math.pi <= ang <= 0.60 * math.pi:
                nw = max(0.0, 1.0 - abs(ang - 0.5 * math.pi) / 0.20)
                y += (0.022 if l_idx == 9 else 0.010) * nw

            # Esculpido del Mentón
            if l_idx == 3 and 0.35 * math.pi <= ang <= 0.65 * math.pi:
                cw = max(0.0, 1.0 - abs(ang - 0.5 * math.pi) / 0.28)
                y += 0.016 * cw

            # Cuencas oculares rehundidas
            if l_idx == 11 and (0.28 * math.pi <= ang <= 0.42 * math.pi or 0.58 * math.pi <= ang <= 0.72 * math.pi):
                y -= 0.014

            cur_ring.append(bm.verts.new((x, y, z)))

            # Coordenada U centrada en 0.50 en el frente (+Y)
            u_coord = ((ang - 0.5 * math.pi) / (2.0 * math.pi) + 0.5) % 1.0
            cur_u.append(u_coord)

        rings.append((cur_ring, cur_u, v_uv))

    for l_idx in range(len(head_profile) - 1):
        r1, u1, v1 = rings[l_idx]
        r2, u2, v2 = rings[l_idx + 1]
        for i in range(n_ring):
            i_next = (i + 1) % n_ring
            f = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
            f.material_index = 0

            # Ajuste de costura UV posterior
            u_a = u1[i]
            u_b = u1[i_next]
            if abs(u_b - u_a) > 0.5:
                u_b = u_b + 1.0 if u_a > 0.5 else u_b - 1.0
            u_c = u2[i_next]
            u_d = u2[i]
            if abs(u_c - u_d) > 0.5:
                u_c = u_c + 1.0 if u_d > 0.5 else u_c - 1.0

            for loop in f.loops:
                if loop.vert == r1[i]: loop[uv_lay].uv = (u_a, v1)
                elif loop.vert == r1[i_next]: loop[uv_lay].uv = (u_b, v1)
                elif loop.vert == r2[i_next]: loop[uv_lay].uv = (u_c, v2)
                elif loop.vert == r2[i]: loop[uv_lay].uv = (u_d, v2)

    # Ojos 3D reales avellana
    eye_pos = [(0.033, 0.055, 1.565), (-0.033, 0.055, 1.565)]
    for pos in eye_pos:
        e_bm = bmesh.new()
        bmesh.ops.create_uvsphere(e_bm, u_segments=16, v_segments=12, radius=0.0135)
        bmesh.ops.rotate(e_bm, verts=e_bm.verts, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(-90), 4, 'X'))
        bmesh.ops.translate(e_bm, verts=e_bm.verts, vec=pos)
        v_map = {v: bm.verts.new(v.co) for v in e_bm.verts}
        for f in e_bm.faces:
            nf = bm.faces.new([v_map[v] for v in f.verts])
            nf.material_index = 1
            for loop in nf.loops:
                co = loop.vert.co - Vector(pos)
                loop[uv_lay].uv = (0.5 + co.x / (2.0 * 0.0135), 0.5 + co.z / (2.0 * 0.0135))
        e_bm.free()

    # Rizos volumétricos de Axel bajo el sombrero
    curl_specs = [
        (0.000, 0.068, 1.625, 0.003, 0.018, -0.050, 0.010, 2.2, 0.0),
        (0.016, 0.066, 1.623, 0.008, 0.016, -0.052, 0.010, 2.4, 0.8),
        (-0.016, 0.066, 1.623, -0.008, 0.016, -0.052, 0.010, 2.4, 1.5),
        (0.032, 0.062, 1.620, 0.012, 0.014, -0.048, 0.009, 2.1, 2.2),
        (-0.032, 0.062, 1.620, -0.012, 0.014, -0.048, 0.009, 2.1, 2.9),
        (0.046, 0.054, 1.616, 0.015, 0.012, -0.045, 0.0085, 2.0, 3.7),
        (-0.046, 0.054, 1.616, -0.015, 0.012, -0.045, 0.0085, 2.0, 4.4),
        (0.064, 0.025, 1.605, 0.010, 0.005, -0.065, 0.0085, 2.5, 0.5),
        (-0.064, 0.025, 1.605, -0.010, 0.005, -0.065, 0.0085, 2.5, 1.7),
    ]
    for (x0, y0, z0, dx, dy, dz, r_curl, turns, phi0) in curl_specs:
        steps = 14
        prev_ring = None
        for s in range(steps):
            t = s / float(steps - 1)
            c_x = x0 + dx * t
            c_y = y0 + dy * t
            c_z = z0 + dz * t
            cur_r = r_curl * (1.0 - 0.45 * t)
            phase = 2.0 * math.pi * turns * t + phi0
            sp_cx = c_x + cur_r * math.cos(phase)
            sp_cy = c_y + cur_r * math.sin(phase)
            sp_cz = c_z
            tb_r = 0.0055 * (1.0 - 0.5 * t)
            cur_ring = []
            for k in range(4):
                k_ang = (2.0 * math.pi * k) / 4.0
                cur_ring.append(bm.verts.new((sp_cx + tb_r * math.cos(k_ang),
                                             sp_cy + tb_r * math.sin(k_ang) * 0.5,
                                             sp_cz + tb_r * math.sin(k_ang) * 0.8)))
            if prev_ring:
                for k in range(4):
                    k_next = (k + 1) % 4
                    f_h = bm.faces.new((prev_ring[k], prev_ring[k_next], cur_ring[k_next], cur_ring[k]))
                    f_h.material_index = 2
            prev_ring = cur_ring

    # Sombrero Fedora con Teardrop Pinch, Grosgrain y Snap-Brim
    n_hat = 32
    hat_levels = [
        (1.615, 0.090, 0.100, -0.002, 1.00, 0.000), # Base sobre la frente
        (1.640, 0.088, 0.098, -0.003, 0.96, 0.000), # Banda grosgrain
        (1.670, 0.085, 0.095, -0.004, 0.90, 0.000), # Copa media
        (1.695, 0.082, 0.092, -0.005, 0.84, 0.000), # Copa alta
        (1.715, 0.078, 0.088, -0.006, 0.78, 0.016), # Corona teardrop
    ]
    hat_rings = []
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
            cur_ring.append(bm.verts.new((vx, vy, vz)))
        hat_rings.append(cur_ring)

    for l_idx in range(len(hat_levels) - 1):
        r1 = hat_rings[l_idx]
        r2 = hat_rings[l_idx + 1]
        m_idx = 4 if l_idx == 0 else 3
        for i in range(n_hat):
            i_next = (i + 1) % n_hat
            f = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
            f.material_index = m_idx

    top_c = bm.verts.new((0.0, -0.006, 1.700))
    for i in range(n_hat):
        i_next = (i + 1) % n_hat
        f = bm.faces.new((hat_rings[-1][i], hat_rings[-1][i_next], top_c))
        f.material_index = 3

    # Ala Snap-Brim
    base_r = hat_rings[0]
    brim_mid = []
    brim_outer = []
    for i in range(n_hat):
        ang = (2.0 * math.pi * i) / n_hat
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        dip_z = -0.022 * max(0.0, sin_a) + 0.015 * abs(cos_a) + 0.008 * max(0.0, -sin_a)
        brim_mid.append(bm.verts.new((0.125 * cos_a, 0.138 * sin_a - 0.002, 1.615 + dip_z * 0.5)))
        brim_outer.append(bm.verts.new((0.158 * cos_a, 0.170 * sin_a - 0.002, 1.615 + dip_z)))

    for i in range(n_hat):
        i_next = (i + 1) % n_hat
        f1 = bm.faces.new((base_r[i], base_r[i_next], brim_mid[i_next], brim_mid[i]))
        f2 = bm.faces.new((brim_mid[i], brim_mid[i_next], brim_outer[i_next], brim_outer[i]))
        f1.material_index = 3
        f2.material_index = 3

    bm.normal_update()
    for f in bm.faces: f.smooth = True
    bm.to_mesh(me)
    bm.free()

    obj = bpy.data.objects.new("Player_Head_Mesh", me)
    bpy.context.scene.collection.objects.link(obj)
    for mat in materials["head"]:
        obj.data.materials.append(mat)
    sub = obj.modifiers.new("Subsurf", type='SUBSURF')
    sub.levels = 1
    sub.render_levels = 1
    return obj

# =============================================================================
# 3. CUERPO: CAPAS ESTRATIFICADAS (CAMISA, CUELLO CAMISERO, CORBATA Y CHALECO)
# =============================================================================
def build_body_mesh(materials):
    mesh_graph = bpy.data.meshes.new("Body_Graph_Data")
    obj_body = bpy.data.objects.new("Player_Body_Mesh", mesh_graph)
    bpy.context.scene.collection.objects.link(obj_body)

    # Nodos anatómicos del cuerpo base
    nodes = [
        # Tronco
        (0.00,  0.00, 0.82, 0.130, 0.100), # 0: Pelvis base
        (0.00,  0.00, 0.94, 0.145, 0.105), # 1: Caderas / Cintura pantalón
        (0.00,  0.00, 1.04, 0.135, 0.098), # 2: Cintura entallada
        (0.00,  0.00, 1.16, 0.155, 0.110), # 3: Costillas
        (0.00,  0.00, 1.28, 0.170, 0.120), # 4: Pectorales
        (0.00,  0.00, 1.36, 0.150, 0.105), # 5: Clavículas / hombros
        (0.00,  0.00, 1.40, 0.052, 0.052), # 6: Base del cuello

        # Brazos (+X Left, -X Right)
        ( 0.06, 0.00, 1.36, 0.070, 0.070), # 7
        ( 0.18, 0.00, 1.34, 0.062, 0.062), # 8: Hombro L
        ( 0.26, 0.00, 1.15, 0.050, 0.050), # 9: Codo L
        ( 0.33, 0.01, 0.92, 0.038, 0.034), # 10: Muñeca L

        (-0.06, 0.00, 1.36, 0.070, 0.070), # 11
        (-0.18, 0.00, 1.34, 0.062, 0.062), # 12: Hombro R
        (-0.26, 0.00, 1.15, 0.050, 0.050), # 13: Codo R
        (-0.33, 0.01, 0.92, 0.038, 0.034), # 14: Muñeca R

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

    # Materiales del cuerpo base según altura
    for p in bm.faces:
        center_z = p.calc_center_median().z
        if center_z < 0.10:
            p.material_index = 2 # Zapatos
        elif center_z < 0.94:
            p.material_index = 1 # Pantalón
        else:
            p.material_index = 0 # Camisa

    # =========================================================================
    # CUELLO CAMISERO REAL QUE ENVUELVE EL CUELLO Y PALAS DOBLADAS
    # =========================================================================
    # Tira anular alrededor del cuello (Z = 1.38 a 1.42)
    n_c = 16
    c_bot = []
    c_top = []
    for i in range(n_c):
        ang = (2.0 * math.pi * i) / n_c
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        rx = 0.054
        ry = 0.054
        c_bot.append(bm.verts.new((rx * cos_a, ry * sin_a + 0.008, 1.375)))
        c_top.append(bm.verts.new((rx * cos_a, ry * sin_a + 0.008, 1.418)))

    for i in range(n_c):
        i_next = (i + 1) % n_c
        f_c = bm.faces.new((c_bot[i], c_bot[i_next], c_top[i_next], c_top[i]))
        f_c.material_index = 0

    # Puntas del cuello dobladas hacia abajo-adelante
    c_wings = [
        # Punta izquierda
        [bm.verts.new((0.008, 0.058, 1.415)), bm.verts.new((0.050, 0.048, 1.410)), bm.verts.new((0.028, 0.072, 1.365))],
        # Punta derecha
        [bm.verts.new((-0.008, 0.058, 1.415)), bm.verts.new((-0.028, 0.072, 1.365)), bm.verts.new((-0.050, 0.048, 1.410))],
    ]
    bm.faces.new(c_wings[0]).material_index = 0
    bm.faces.new(c_wings[1]).material_index = 0

    # Nudo Windsor de la corbata ajustado en el cuello
    knot_v = [
        bm.verts.new((-0.016, 0.066, 1.408)),
        bm.verts.new((0.016, 0.066, 1.408)),
        bm.verts.new((0.012, 0.074, 1.365)),
        bm.verts.new((-0.012, 0.074, 1.365)),
        bm.verts.new((0.000, 0.060, 1.390)),
    ]
    bm.faces.new((knot_v[0], knot_v[1], knot_v[2], knot_v[3])).material_index = 4
    bm.faces.new((knot_v[0], knot_v[3], knot_v[4])).material_index = 4
    bm.faces.new((knot_v[1], knot_v[4], knot_v[2])).material_index = 4

    # Pala continua de la corbata
    tie_v = [
        bm.verts.new((-0.012, 0.075, 1.365)),
        bm.verts.new((0.012, 0.075, 1.365)),
        bm.verts.new((-0.015, 0.098, 1.300)),
        bm.verts.new((0.015, 0.098, 1.300)),
        bm.verts.new((-0.018, 0.116, 1.230)),
        bm.verts.new((0.018, 0.116, 1.230)),
        bm.verts.new((-0.020, 0.112, 1.150)),
        bm.verts.new((0.020, 0.112, 1.150)),
    ]
    for ts in range(3):
        bm.faces.new((tie_v[ts*2], tie_v[ts*2+1], tie_v[(ts+1)*2+1], tie_v[(ts+1)*2])).material_index = 4

    # =========================================================================
    # CHALECO SASTRE 3D COMPLETO (TIRANTES, ESCOTE EN V DIAGONAL Y PICO INFERIOR)
    # =========================================================================
    # El chaleco envuelve todo el torso con tirantes sobre los hombros y sisas.
    # Modelamos una rejilla de cilindro envolvente con offset normal (+6mm)
    # Niveles Z del chaleco:
    # 1.36 (hombros/clavículas con escote V y sisas)
    # 1.30 (pecho alto)
    # 1.22 (cierre del escote V en el botón 1)
    # 1.15 (botón 2)
    # 1.08 (botón 3 / cintura)
    # 1.00 (botón 4)
    # 0.94 (botón 5 / cintura baja)
    
    # Perfil del chaleco:
    v_levels = [
        # z, rx, ry_front, ry_back, v_open_halfwidth
        (1.36, 0.165, 0.115, 0.108, 0.055), # Hombros / clavículas
        (1.30, 0.168, 0.125, 0.114, 0.035), # Pecho superior
        (1.22, 0.165, 0.122, 0.112, 0.000), # Botón 1 / Cierre V
        (1.15, 0.160, 0.118, 0.108, 0.000), # Botón 2
        (1.08, 0.152, 0.114, 0.104, 0.000), # Botón 3
        (1.00, 0.150, 0.112, 0.102, 0.000), # Botón 4
        (0.94, 0.154, 0.114, 0.104, 0.000), # Botón 5 / dobladillo
    ]
    
    n_v = 20
    vest_rings = []
    for (z, rx, ry_f, ry_b, v_open) in v_levels:
        ring = []
        for i in range(n_v):
            ang = (2.0 * math.pi * i) / n_v
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            vx = rx * cos_a
            vy = (ry_f if sin_a >= 0 else ry_b) * sin_a
            vz = z

            # Apertura del escote en V en el frente (+Y)
            if v_open > 0.0 and sin_a > 0.40:
                if abs(vx) < v_open:
                    # Empujar hacia el borde del escote para formar un corte diagonal limpio
                    vx = v_open if vx >= 0 else -v_open
                    # Retraer ligeramente para un corte nítido
                    vy = ry_f * math.sqrt(max(0.01, 1.0 - (vx / rx)**2))

            ring.append(bm.verts.new((vx, vy, vz)))
        vest_rings.append(ring)

    # Conectar quads del chaleco
    for l_idx in range(len(v_levels) - 1):
        r1 = vest_rings[l_idx]
        r2 = vest_rings[l_idx + 1]
        for i in range(n_v):
            i_next = (i + 1) % n_v
            # Omitir la cara frontal si está en el hueco del escote en V
            mid_ang = (2.0 * math.pi * (i + 0.5)) / n_v
            sin_m = math.sin(mid_ang)
            cos_m = math.cos(mid_ang)
            v_open_cur = v_levels[l_idx][4]
            if v_open_cur > 0.0 and sin_m > 0.50 and abs(v_levels[l_idx][1] * cos_m) < v_open_cur:
                continue # Apertura del escote en V

            f_v = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
            # Espalda oscura de forro sastre si sin_m < -0.30
            f_v.material_index = 0 if sin_m < -0.30 else 3

    # Picos inferiores frontales del chaleco (puntas triangulares sastre a Z=0.88)
    bot_r = vest_rings[-1]
    # Encontrar los vértices frontales alrededor de ang = pi/2
    front_idx = int(round(n_v * 0.25))
    peak_l = bm.verts.new((0.042, 0.116, 0.880))
    peak_r = bm.verts.new((-0.042, 0.116, 0.880))
    
    # Conectar picos triangulares al dobladillo
    idx_l1 = (front_idx - 1) % n_v
    idx_l2 = front_idx % n_v
    idx_r1 = front_idx % n_v
    idx_r2 = (front_idx + 1) % n_v
    bm.faces.new((bot_r[idx_l1], bot_r[idx_l2], peak_l)).material_index = 3
    bm.faces.new((bot_r[idx_r1], bot_r[idx_r2], peak_r)).material_index = 3

    # 5 Botones plateados tridimensionales alineados verticalmente
    b_zs = [1.22, 1.15, 1.08, 1.01, 0.94]
    for bz in b_zs:
        by = 0.120 + (1.22 - bz) * (-0.006)
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.0045)
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.0, by + 0.005, bz))
        v_map = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            nf = bm.faces.new([v_map[v] for v in f.verts])
            nf.material_index = 5 # Plata
        btn_bm.free()

    # Bolsillos Welt de ribete (pecho izquierdo a Z=1.14 con pañuelo oscuro, y dos inferiores a Z=0.98)
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

    # =========================================================================
    # MANOS ANATÓMICAS CON PALMA CONTORNEADA, DEDOS ARTICULADOS Y ANILLOS
    # =========================================================================
    for is_left in (True, False):
        sign_h = 1.0 if is_left else -1.0
        w_m = sign_h * 0.298 # Medial (hacia el cuerpo)
        w_l = sign_h * 0.362 # Lateral (hacia afuera)

        base_z = 0.84
        base_y = 0.012

        # 4 Dedos anatómicos articulados con 3 falanges
        finger_specs = [
            ("Index",  0.22, 0.075, 0.0065),
            ("Middle", 0.45, 0.082, 0.0070),
            ("Ring",   0.68, 0.076, 0.0065),
            ("Little", 0.90, 0.065, 0.0055),
        ]

        for (f_name, f_frac, f_len, f_rad) in finger_specs:
            f_x = w_m + (w_l - w_m) * f_frac
            # Ligera flexión natural hacia el fondo (-Y)
            p_joint = [
                Vector((f_x, base_y, base_z)),
                Vector((f_x, base_y - 0.004, base_z - f_len * 0.40)),
                Vector((f_x, base_y - 0.010, base_z - f_len * 0.75)),
                Vector((f_x, base_y - 0.015, base_z - f_len * 1.00)),
            ]
            prev_f_r = None
            for j_idx, pt in enumerate(p_joint):
                cur_r = f_rad * (1.0 - 0.25 * (j_idx / 3.0))
                cur_f_r = [
                    bm.verts.new((pt.x - cur_r, pt.y, pt.z)),
                    bm.verts.new((pt.x, pt.y + cur_r, pt.z)),
                    bm.verts.new((pt.x + cur_r, pt.y, pt.z)),
                    bm.verts.new((pt.x, pt.y - cur_r, pt.z)),
                ]
                if prev_f_r:
                    for k in range(4):
                        k_next = (k + 1) % 4
                        f_seg = bm.faces.new((prev_f_r[k], prev_f_r[k_next], cur_f_r[k_next], cur_f_r[k]))
                        f_seg.material_index = 6 # Piel
                prev_f_r = cur_f_r
            tip_v = bm.verts.new((p_joint[-1].x, p_joint[-1].y - 0.003, p_joint[-1].z - 0.004))
            for k in range(4):
                k_next = (k + 1) % 4
                f_tip = bm.faces.new((prev_f_r[k_next], prev_f_r[k], tip_v))
                f_tip.material_index = 6

            # Anillos de Plata de Axel en mano izquierda (Índice y Medio)
            if is_left and f_name in ("Index", "Middle"):
                r_zc = base_z - f_len * 0.20
                r_rad = f_rad * 1.22
                r1_pts = []
                r2_pts = []
                for k in range(8):
                    ang_r = (2.0 * math.pi * k) / 8.0
                    rx = f_x + r_rad * math.cos(ang_r)
                    ry = (base_y - 0.002) + r_rad * math.sin(ang_r)
                    r1_pts.append(bm.verts.new((rx, ry, r_zc + 0.003)))
                    r2_pts.append(bm.verts.new((rx, ry, r_zc - 0.003)))
                for k in range(8):
                    k_next = (k + 1) % 8
                    f_ring = bm.faces.new((r1_pts[k], r1_pts[k_next], r2_pts[k_next], r2_pts[k]))
                    f_ring.material_index = 5 # Plata

        # Pulgar Oponible Medial nacido en la eminencia tenar y curvado hacia la palma
        th_pts = [
            Vector((w_m, 0.008, 0.895)),
            Vector((w_m - sign_h * 0.015, 0.004, 0.870)),
            Vector((w_m - sign_h * 0.026, -0.002, 0.845)),
            Vector((w_m - sign_h * 0.032, -0.008, 0.825)),
        ]
        prev_th_r = None
        for j_idx, pt in enumerate(th_pts):
            th_r = 0.0075 * (1.0 - 0.20 * (j_idx / 3.0))
            cur_th_r = [
                bm.verts.new((pt.x - th_r, pt.y, pt.z)),
                bm.verts.new((pt.x, pt.y + th_r, pt.z)),
                bm.verts.new((pt.x + th_r, pt.y, pt.z)),
                bm.verts.new((pt.x, pt.y - th_r, pt.z)),
            ]
            if prev_th_r:
                for k in range(4):
                    k_next = (k + 1) % 4
                    f_th = bm.faces.new((prev_th_r[k], prev_th_r[k_next], cur_th_r[k_next], cur_th_r[k]))
                    f_th.material_index = 6
            prev_th_r = cur_th_r
        tip_th = bm.verts.new((th_pts[-1].x - sign_h * 0.003, th_pts[-1].y - 0.005, th_pts[-1].z - 0.004))
        for k in range(4):
            k_next = (k + 1) % 4
            f_tip_th = bm.faces.new((prev_th_r[k_next], prev_th_r[k], tip_th))
            f_tip_th.material_index = 6

        # Masa de la palma trapezoidal contorneada (con ahusamiento en muñeca)
        p_box = [
            bm.verts.new((w_m, 0.022, 0.92)),
            bm.verts.new((w_l, 0.022, 0.92)),
            bm.verts.new((w_l, -0.002, 0.92)),
            bm.verts.new((w_m, -0.002, 0.92)),
            bm.verts.new((w_m, 0.022, 0.84)),
            bm.verts.new((w_l, 0.022, 0.84)),
            bm.verts.new((w_l, -0.004, 0.84)),
            bm.verts.new((w_m, -0.004, 0.84)),
        ]
        p_f_idxs = [(0, 1, 5, 4), (3, 7, 6, 2), (0, 4, 7, 3), (1, 2, 6, 5), (0, 3, 2, 1)]
        for pfi in p_f_idxs:
            f_p = bm.faces.new([p_box[idx] for idx in pfi])
            f_p.material_index = 6

    bm.normal_update()
    for f in bm.faces: f.smooth = True
    bm.to_mesh(obj_body.data)
    bm.free()

    for mat in materials["body"]:
        obj_body.data.materials.append(mat)

    return obj_body

# =============================================================================
# 4. ESQUELETO Y RIGGING (22 HUESOS CANÓNICOS)
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
        ("Neck",        "Chest",       (0, 0, 1.36),      (0, 0, 1.43)),
        ("Head",        "Neck",        (0, 0, 1.43),      (0, 0, 1.70)),
        
        ("Shoulder.L",  "Chest",       (0.04, 0, 1.36),   (0.180, 0, 1.36)),
        ("UpperArm.L",  "Shoulder.L",  (0.180, 0, 1.36),  (0.260, 0.007, 1.15)),
        ("Forearm.L",   "UpperArm.L",  (0.260, 0.007, 1.15),(0.330, 0.015, 0.92)),
        ("Hand.L",      "Forearm.L",   (0.330, 0.015, 0.92),(0.330, 0.015, 0.82)),
        
        ("Shoulder.R",  "Chest",       (-0.04, 0, 1.36),  (-0.180, 0, 1.36)),
        ("UpperArm.R",  "Shoulder.R",  (-0.180, 0, 1.36), (-0.260, 0.007, 1.15)),
        ("Forearm.R",   "UpperArm.R",  (-0.260, 0.007, 1.15),(-0.330, 0.015, 0.92)),
        ("Hand.R",      "Forearm.R",   (-0.330, 0.015, 0.92),(-0.330, 0.015, 0.82)),
        
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
            grp = "Neck" if co.z < 1.42 else "Head"
            obj.vertex_groups[grp].add([v.index], 1.0, 'REPLACE')
        else:
            if co.z < 0.04:
                obj.vertex_groups["Toes.L" if co.x > 0 else "Toes.R"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.12:
                obj.vertex_groups["Foot.L" if co.x > 0 else "Foot.R"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.48:
                obj.vertex_groups["LowerLeg.L" if co.x > 0 else "LowerLeg.R"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.82 and abs(co.x) > 0.03:
                obj.vertex_groups["UpperLeg.L" if co.x > 0 else "UpperLeg.R"].add([v.index], 1.0, 'REPLACE')
            elif abs(co.x) > 0.18 and co.z < 1.38:
                side = ".L" if co.x > 0 else ".R"
                if co.z < 0.93: obj.vertex_groups["Hand" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.15: obj.vertex_groups["Forearm" + side].add([v.index], 1.0, 'REPLACE')
                else: obj.vertex_groups["UpperArm" + side].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.95: obj.vertex_groups["Hips"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 1.15: obj.vertex_groups["Spine"].add([v.index], 1.0, 'REPLACE')
            else: obj.vertex_groups["Chest"].add([v.index], 1.0, 'REPLACE')

# =============================================================================
# 5. RENDER PREVIEW DE ESTUDIO FOTOGRÁFICO
# =============================================================================
def render_preview():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    scene.cycles.device = 'CPU'

    # Luz de 3 puntos suave y envolvente
    key = bpy.data.objects.new("Key", bpy.data.lights.new("Key", 'AREA'))
    key.data.energy = 110.0
    key.data.size = 1.4
    key.data.color = (1.0, 0.98, 0.95)
    key.location = Vector((-0.6, 1.7, 1.5))
    key.rotation_euler = (math.radians(50.0), 0.0, math.radians(-155.0))
    scene.collection.objects.link(key)

    fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", 'AREA'))
    fill.data.energy = 55.0
    fill.data.size = 1.8
    fill.data.color = (0.94, 0.97, 1.0)
    fill.location = Vector((0.8, 1.7, 1.3))
    scene.collection.objects.link(fill)

    rim = bpy.data.objects.new("Rim", bpy.data.lights.new("Rim", 'SPOT'))
    rim.data.energy = 65.0
    rim.data.spot_size = math.radians(65.0)
    rim.data.color = (1.0, 1.0, 1.0)
    rim.location = Vector((0.0, -1.2, 1.8))
    rim.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
    scene.collection.objects.link(rim)

    # Cámara encuadrando medio cuerpo (desde el cinturón hasta el sombrero)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.lens = 52.0
    cam.location = Vector((0.02, 1.65, 1.28))
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
    print("GENERANDO AXEL MASTER MODEL (FORTNITE / AXEL2.PNG)")
    print("=" * 60)
    clean_scene()

    generate_enhanced_textures()

    mat_skin = create_pbr_material("Mat_Axel_Skin", (0.88, 0.62, 0.48, 1.0), roughness=0.50,
                                   diffuse_tex_path=os.path.join(TEXTURES_DIR, "axel_face_diffuse.png"),
                                   normal_tex_path=os.path.join(TEXTURES_DIR, "axel_face_normal.png"))
    mat_eye = create_pbr_material("Mat_Axel_Eyes", (1, 1, 1, 1), roughness=0.1,
                                  diffuse_tex_path=os.path.join(TEXTURES_DIR, "axel_eye_diffuse.png"))
    mat_hair = create_pbr_material("Mat_Axel_Hair", (0.05, 0.04, 0.035, 1.0), roughness=0.85)
    mat_fedora = create_pbr_material("Mat_Axel_Fedora", (0.015, 0.015, 0.018, 1.0), roughness=0.92,
                                     diffuse_tex_path=os.path.join(TEXTURES_DIR, "axel_hat_diffuse.png"),
                                     normal_tex_path=os.path.join(TEXTURES_DIR, "axel_hat_normal.png"))
    mat_hatband = create_pbr_material("Mat_Axel_Hatband", (0.02, 0.02, 0.025, 1.0), roughness=0.45, specular=0.6)
    
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
    print("✓ Player_Head_Mesh generado con boca 3D anatómica, proporciones reales y fedora.")
    
    body_obj = build_body_mesh(materials)
    assign_weights(body_obj, is_head=False)
    body_obj.parent = skel
    mod_b = body_obj.modifiers.new("Armature", type='ARMATURE')
    mod_b.object = skel
    print("✓ Player_Body_Mesh generado con chaleco entallado y corbata estratificada.")
    
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
