import bpy
import bmesh
import math
import os
import numpy as np
from mathutils import Vector, Matrix

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
TEXTURES_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/textures")

bpy.ops.wm.read_factory_settings(use_empty=True)

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

# Tono de piel cálido natural uniforme para evitar la franja blanca
mat_skin = create_pbr_material("Mat_Axel_Skin", (0.80, 0.60, 0.48, 1.0), roughness=0.52,
                               normal_tex_path=os.path.join(TEXTURES_DIR, "axel_face_normal.png"))
mat_eye = create_pbr_material("Mat_Axel_Eyes", (1, 1, 1, 1), roughness=0.08,
                              diffuse_tex_path=os.path.join(TEXTURES_DIR, "axel_eye_diffuse.png"))
mat_hair = create_pbr_material("Mat_Axel_Hair", (0.04, 0.035, 0.03, 1.0), roughness=0.82)
mat_fedora = create_pbr_material("Mat_Axel_Fedora", (0.02, 0.02, 0.025, 1.0), roughness=0.92,
                                 diffuse_tex_path=os.path.join(TEXTURES_DIR, "axel_hat_diffuse.png"))
mat_hatband = create_pbr_material("Mat_Axel_Hatband", (0.015, 0.015, 0.02, 1.0), roughness=0.45, specular=0.6)

me = bpy.data.meshes.new("TestHeadSculpted")
obj = bpy.data.objects.new("TestHeadSculpted", me)
bpy.context.scene.collection.objects.link(obj)
bm = bmesh.new()
uv_lay = bm.loops.layers.uv.new("UVMap")

# Perfil anatómico con mandíbula angulada, mentón proyectado y ángulo cervicomandibular limpio
n_ring = 32
head_profile = [
    # z, rx, ry_front, ry_back, y_offset, v_uv
    (1.370, 0.048, 0.038, 0.048, -0.005, 0.12), # 0: Base cuello (hacia atrás)
    (1.395, 0.046, 0.036, 0.046, -0.003, 0.18), # 1: Cuello medio
    (1.415, 0.050, 0.038, 0.050,  0.000, 0.24), # 2: Submandíbula / receso del cuello
    (1.435, 0.058, 0.076, 0.058,  0.016, 0.30), # 3: Mentón PROYECTADO hacia adelante (+Y)
    (1.450, 0.065, 0.062, 0.065,  0.012, 0.35), # 4: Surco mentolabial marcado
    (1.460, 0.068, 0.076, 0.068,  0.010, 0.38), # 5: Labio inferior carnosos
    (1.468, 0.070, 0.068, 0.070,  0.008, 0.40), # 6: Hendidura labial (Boca)
    (1.478, 0.071, 0.077, 0.071,  0.006, 0.43), # 7: Labio superior con arco de Cupido
    (1.492, 0.074, 0.072, 0.074,  0.004, 0.48), # 8: Base nasal / Filtrum
    (1.505, 0.077, 0.096, 0.077,  0.002, 0.54), # 9: Punta nasal recta y definida (+Y prominente)
    (1.528, 0.081, 0.072, 0.080,  0.000, 0.63), # 10: Ojos / cuencas (Z = 1.528)
    (1.546, 0.082, 0.080, 0.081, -0.002, 0.72), # 11: Pómulos altos prominentes y cejas
    (1.564, 0.079, 0.070, 0.080, -0.004, 0.79), # 12: Frente baja
    (1.580, 0.076, 0.065, 0.078, -0.006, 0.85), # 13: Frente media
    (1.595, 0.071, 0.055, 0.074, -0.008, 0.91), # 14: Asiento sombrero
    (1.618, 0.058, 0.042, 0.062, -0.010, 0.96), # 15: Bóveda craneal
    (1.635, 0.038, 0.026, 0.040, -0.012, 0.99), # 16: Coronilla
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

        # Labios
        if l_idx in (5, 6, 7) and 0.38 * math.pi <= ang <= 0.62 * math.pi:
            m_dist = abs(ang - 0.5 * math.pi) / 0.12
            mw = max(0.0, 1.0 - m_dist**2)
            if l_idx == 5: y += 0.012 * mw
            elif l_idx == 6: y -= 0.007 * mw
            elif l_idx == 7: y += 0.011 * mw

        # Nariz recta
        if l_idx in (8, 9) and 0.42 * math.pi <= ang <= 0.58 * math.pi:
            nw = max(0.0, 1.0 - abs(ang - 0.5 * math.pi) / 0.16)
            y += (0.024 if l_idx == 9 else 0.012) * nw

        # Mentón angular proyectado hacia adelante
        if l_idx == 3 and 0.38 * math.pi <= ang <= 0.62 * math.pi:
            cw = max(0.0, 1.0 - abs(ang - 0.5 * math.pi) / 0.22)
            y += 0.018 * cw

        # Hendidura orbital en nivel 10
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

# Globos oculares en Z = 1.528
eye_pos = [(0.033, 0.053, 1.528), (-0.033, 0.053, 1.528)]
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

# Párpados anatómicos delgados integrados
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

        dz_margin_sup = 0.0022 * arch_sup + 0.0005 * t
        dz_margin_inf = -0.0040 * arch_sup + 0.0003 * t

        dy_margin = math.sqrt(max(0.0001, (eye_r * 1.02)**2 - dx**2 - dz_margin_sup**2))
        dy_margin_inf = math.sqrt(max(0.0001, (eye_r * 1.02)**2 - dx**2 - dz_margin_inf**2))

        v_um = bm.verts.new((ex + dx, ey + dy_margin, ez + dz_margin_sup))
        v_uc = bm.verts.new((ex + dx, ey + dy_margin * 0.98 + 0.002, ez + dz_margin_sup + 0.0045 * arch_sup))
        v_ub = bm.verts.new((ex + dx, ey + dy_margin * 0.92 + 0.005, ez + dz_margin_sup + 0.0100 * arch_sup))

        v_lm = bm.verts.new((ex + dx, ey + dy_margin_inf, ez + dz_margin_inf))
        v_lc = bm.verts.new((ex + dx, ey + dy_margin_inf * 0.96 + 0.003, ez + dz_margin_inf - 0.0060 * arch_sup))

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

# Cabello rizado abundante ("the hair was fine")
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
                f_c.material_index = 2
        prev_ring = c_ring

frontal_curls = [
    ( 0.000, 0.068, 1.590,  0.003, 0.016, -0.038, 0.011, 2.2, 0.2, 0.0070),
    ( 0.015, 0.066, 1.588,  0.006, 0.015, -0.040, 0.011, 2.4, 0.9, 0.0068),
    (-0.015, 0.066, 1.588, -0.006, 0.015, -0.040, 0.011, 2.4, 1.6, 0.0068),
    ( 0.028, 0.063, 1.585,  0.009, 0.014, -0.042, 0.010, 2.3, 2.3, 0.0066),
    (-0.028, 0.063, 1.585, -0.009, 0.014, -0.042, 0.010, 2.3, 3.0, 0.0066),
    ( 0.042, 0.058, 1.582,  0.012, 0.012, -0.044, 0.010, 2.1, 3.8, 0.0065),
    (-0.042, 0.058, 1.582, -0.012, 0.012, -0.044, 0.010, 2.1, 4.5, 0.0065),
    ( 0.054, 0.050, 1.579,  0.013, 0.010, -0.044, 0.009, 2.0, 0.6, 0.0062),
    (-0.054, 0.050, 1.579, -0.013, 0.010, -0.044, 0.009, 2.0, 1.8, 0.0062),
    ( 0.008, 0.070, 1.594,  0.005, 0.018, -0.035, 0.012, 2.0, 1.2, 0.0072),
    (-0.008, 0.070, 1.594, -0.005, 0.018, -0.035, 0.012, 2.0, 2.8, 0.0072),
    ( 0.022, 0.067, 1.591,  0.009, 0.016, -0.038, 0.011, 2.3, 0.5, 0.0068),
    (-0.022, 0.067, 1.591, -0.009, 0.016, -0.038, 0.011, 2.3, 3.6, 0.0068),
]
for c in frontal_curls:
    add_curl(c[:3], c[3:6], c[6], c[7], c[8], c[9])

side_curls = [
    ( 0.066, 0.038, 1.575,  0.010, 0.008, -0.052, 0.010, 2.5, 0.5, 0.0068),
    ( 0.072, 0.024, 1.573,  0.008, 0.006, -0.056, 0.011, 2.6, 1.4, 0.0070),
    ( 0.074, 0.010, 1.571,  0.006, 0.004, -0.058, 0.010, 2.7, 2.3, 0.0070),
    ( 0.072,-0.006, 1.569,  0.005, 0.002, -0.060, 0.011, 2.6, 3.2, 0.0072),
    (-0.066, 0.038, 1.575, -0.010, 0.008, -0.052, 0.010, 2.5, 1.7, 0.0068),
    (-0.072, 0.024, 1.573, -0.008, 0.006, -0.056, 0.010, 2.6, 2.6, 0.0070),
    (-0.074, 0.010, 1.571, -0.006, 0.004, -0.056, 0.010, 2.7, 3.5, 0.0070),
    (-0.072,-0.006, 1.569, -0.005, 0.002, -0.060, 0.011, 2.6, 4.4, 0.0072),
]
for c in side_curls:
    add_curl(c[:3], c[3:6], c[6], c[7], c[8], c[9])

# Sombrero Fedora con geometría completamente limpia y simétrica
fedora_bm = bmesh.new()
n_hat = 32
hat_levels = [
    (0.000, 0.092, 0.100, 0.000, 1.00, 0.000),
    (0.025, 0.090, 0.098, 0.000, 0.96, 0.000),
    (0.055, 0.086, 0.094, 0.000, 0.90, 0.000),
    (0.080, 0.082, 0.090, 0.000, 0.84, 0.000),
    (0.100, 0.078, 0.086, 0.000, 0.78, 0.016),
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
        f = fedora_bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))
        f.material_index = m_idx

top_c = fedora_bm.verts.new((0.0, 0.0, 0.088))
for i in range(n_hat):
    inxt = (i + 1) % n_hat
    f = fedora_bm.faces.new((fed_rings[-1][i], fed_rings[-1][inxt], top_c))
    f.material_index = 3

# Ala suave con curvatura regular continua
b_in_top = fed_rings[0]
b_out_top = []
b_out_bot = []
b_in_bot = []

for i in range(n_hat):
    ang = (2.0 * math.pi * i) / n_hat
    cos_a = math.cos(ang)
    sin_a = math.sin(ang)
    # Ala suave: sube 1 cm a los lados, baja 4 mm al frente
    curl_z = 0.010 * abs(cos_a) - 0.004 * max(0.0, sin_a)
    bx = 0.158 * cos_a
    by = 0.168 * sin_a
    bz = curl_z
    b_out_top.append(fedora_bm.verts.new((bx, by, bz + 0.0015)))
    b_out_bot.append(fedora_bm.verts.new((bx, by, bz - 0.0015)))
    in_co = fed_rings[0][i].co
    b_in_bot.append(fedora_bm.verts.new((in_co.x * 0.98, in_co.y * 0.98, in_co.z - 0.002)))

for i in range(n_hat):
    inxt = (i + 1) % n_hat
    f_top = fedora_bm.faces.new((b_in_top[inxt], b_in_top[i], b_out_top[i], b_out_top[inxt]))
    f_top.material_index = 3
    f_rim = fedora_bm.faces.new((b_out_top[i], b_out_bot[i], b_out_bot[inxt], b_out_top[inxt]))
    f_rim.material_index = 3
    f_bot = fedora_bm.faces.new((b_out_bot[i], b_in_bot[i], b_in_bot[inxt], b_out_bot[inxt]))
    f_bot.material_index = 3

xform = Matrix.Translation(Vector((0.0, -0.006, 1.595))) @ Matrix.Rotation(math.radians(-5.0), 4, 'X')
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

for mat in [mat_skin, mat_eye, mat_hair, mat_fedora, mat_hatband]:
    obj.data.materials.append(mat)

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

# =============================================================================
# CÁMARA 3/4 PERFIL ANGULADO (FIEL A AXEL2_FACE_CROP.PNG)
# =============================================================================
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 28
scene.render.resolution_x = 720
scene.render.resolution_y = 900

# Ángulo 38 grados hacia el lateral de Axel
cam_angle = math.radians(38.0)
cam_dist = 0.70
cam_z = 1.495
cam_x = cam_dist * math.sin(cam_angle)
cam_y = cam_dist * math.cos(cam_angle)

cam_34 = bpy.data.objects.new("Cam34", bpy.data.cameras.new("Cam34"))
cam_34.data.lens = 68.0
cam_34.location = Vector((cam_x, cam_y, cam_z))
look_target = Vector((0.0, 0.04, 1.485))
direction = look_target - cam_34.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_34.rotation_euler = rot_quat.to_euler()
scene.collection.objects.link(cam_34)
scene.camera = cam_34

# Iluminación
key = bpy.data.objects.new("Key", bpy.data.lights.new("Key", 'AREA'))
key.data.energy = 48.0
key.location = Vector((cam_x + 0.25, cam_y - 0.1, cam_z + 0.25))
key.data.size = 0.8
scene.collection.objects.link(key)

fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", 'AREA'))
fill.data.energy = 26.0
fill.location = Vector((-0.4, 0.6, 1.45))
fill.data.size = 1.2
scene.collection.objects.link(fill)

rim = bpy.data.objects.new("Rim", bpy.data.lights.new("Rim", 'SPOT'))
rim.data.energy = 50.0
rim.location = Vector((-0.3, -0.6, 1.65))
rim.rotation_euler = (math.radians(-50.0), 0.0, math.radians(30.0))
scene.collection.objects.link(rim)

scene.render.filepath = "/tmp/test_head_sculpted_profile.png"
bpy.ops.render.render(write_still=True)
print("Sculpted profile preview rendered successfully to /tmp/test_head_sculpted_profile.png!")
