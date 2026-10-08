"""
=============================================================================
PRUEBA PERFECCIONADA DE ALTA FIDELIDAD: ASTORGA (TECATE SIMULATOR)
=============================================================================
Fiel a la fotografía de referencia scratch/humans/astorga.png:
1. Melena setentera continua en 360° con volumen en sienes, flequillo lateral orgánico y cero huecos.
2. Silueta sastre de hombros estructurados, cintura entallada y proporciones anatómicas (1.65 m).
3. Saco formal negro con solapas anchas, corte integrado sin alas y apertura clásica en V invertida.
4. Camisa vinotinto modelada y continua por todo el torso hasta la cintura (Z = 0.88) con corbata de seda.
5. Prensión exacta de instrumentos:
   - Mano derecha sostiene el mástil del violín a la altura del pecho.
   - Mano izquierda empuña el arco en diagonal idéntica a la fotografía real.
6. Pantalón sastre negro recto y calzado de vestir pulido.
=============================================================================
"""

import os
import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
TEXTURES_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/textures")
SCRATCH_DIR = os.path.join(PROJECT_ROOT, "scratch")
VIOLIN_BLEND = os.path.join(PROJECT_ROOT, "godot_project/assets/props/violin.blend")

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm, do_unlink=True)

def setup_pbr_material(name, diffuse_tex_path, normal_tex_path=None,
                       base_color=(0.8, 0.8, 0.8, 1.0), roughness=0.6,
                       metallic=0.0, specular=0.5):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out_node = nodes.new('ShaderNodeOutputMaterial')
    out_node.location = (400, 0)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])

    bsdf.inputs['Base Color'].default_value = base_color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = specular

    if diffuse_tex_path and os.path.exists(diffuse_tex_path):
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.location = (-400, 100)
        img = bpy.data.images.load(diffuse_tex_path, check_existing=True)
        tex_node.image = img
        links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])

    if normal_tex_path and os.path.exists(normal_tex_path):
        norm_tex = nodes.new('ShaderNodeTexImage')
        norm_tex.location = (-400, -200)
        img_n = bpy.data.images.load(normal_tex_path, check_existing=True)
        img_n.colorspace_settings.name = 'Non-Color'
        norm_tex.image = img_n
        norm_map = nodes.new('ShaderNodeNormalMap')
        norm_map.location = (-150, -200)
        norm_map.inputs['Strength'].default_value = 0.85
        links.new(norm_tex.outputs['Color'], norm_map.inputs['Color'])
        links.new(norm_map.outputs['Normal'], bsdf.inputs['Normal'])

    return mat

def create_materials():
    return {
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
                                   base_color=(0.045, 0.035, 0.030, 1.0), roughness=0.68),
        "suit": setup_pbr_material("Mat_Astorga_Suit",
                                   os.path.join(TEXTURES_DIR, "astorga_suit_diffuse.png"),
                                   os.path.join(TEXTURES_DIR, "astorga_suit_normal.png"),
                                   base_color=(0.045, 0.048, 0.055, 1.0), roughness=0.62),
        "pants": setup_pbr_material("Mat_Astorga_Pants",
                                    os.path.join(TEXTURES_DIR, "astorga_pants_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "astorga_pants_normal.png"),
                                    base_color=(0.045, 0.048, 0.055, 1.0), roughness=0.65),
        "shoes": setup_pbr_material("Mat_Astorga_Shoes",
                                    os.path.join(TEXTURES_DIR, "astorga_shoes_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "astorga_shoes_normal.png"),
                                    base_color=(0.020, 0.020, 0.025, 1.0), roughness=0.20, specular=0.65),
        "shirt": setup_pbr_material("Mat_Astorga_Shirt",
                                    os.path.join(TEXTURES_DIR, "astorga_shirt_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "astorga_shirt_normal.png"),
                                    base_color=(0.280, 0.045, 0.065, 1.0), roughness=0.55),
        "tie": setup_pbr_material("Mat_Astorga_Tie",
                                  os.path.join(TEXTURES_DIR, "astorga_tie_diffuse.png"),
                                  os.path.join(TEXTURES_DIR, "astorga_tie_normal.png"),
                                  base_color=(0.025, 0.020, 0.022, 1.0), roughness=0.35, specular=0.55),
        "belt": setup_pbr_material("Mat_Astorga_Belt",
                                   None, None,
                                   base_color=(0.02, 0.02, 0.02, 1.0), roughness=0.30),
        "buckle": setup_pbr_material("Mat_Astorga_Buckle",
                                     None, None,
                                     base_color=(0.85, 0.82, 0.75, 1.0), roughness=0.25, metallic=0.90),
        "buttons": setup_pbr_material("Mat_Astorga_Buttons",
                                      None, None,
                                      base_color=(0.02, 0.02, 0.02, 1.0), roughness=0.20, metallic=0.40),
    }

# =============================================================================
# 1. CABEZA CON ROSTRO Y MELENA SETENTERA VOLUMINOSA CONTINUA (CERO HUECOS)
# =============================================================================
def build_head_mesh(materials):
    me = bpy.data.meshes.new("Player_Head_Mesh_Data")
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")

    def calc_face_uv(x, z):
        u = 0.50 + x / 0.275
        v = 0.50 + (z - 1.485) / 0.240
        return (max(0.0, min(1.0, u)), max(0.0, min(1.0, v)))

    # Perfil craneofacial
    head_profile = [
        # z,      rx,    ry_front, ry_back, y_offset, is_face
        (1.365,  0.044, 0.044,    0.046,   -0.002,   False), # 0: Base cuello
        (1.385,  0.045, 0.044,    0.048,   -0.002,   False), # 1: Cuello medio
        (1.405,  0.050, 0.046,    0.054,    0.000,   True),  # 2: Ángulo submandibular
        (1.422,  0.057, 0.063,    0.066,    0.004,   True),  # 3: Mentón masculino firme
        (1.440,  0.061, 0.063,    0.072,    0.003,   True),  # 4: Surco mentolabial
        (1.452,  0.063, 0.065,    0.080,    0.003,   True),  # 5: Labio inferior
        (1.462,  0.065, 0.064,    0.084,    0.002,   True),  # 6: Hendidura labial serena
        (1.472,  0.067, 0.067,    0.088,    0.002,   True),  # 7: Labio superior
        (1.486,  0.070, 0.066,    0.090,    0.001,   True),  # 8: Base nasal / Filtrum
        (1.498,  0.072, 0.074,    0.091,    0.000,   True),  # 9: Punta nasal recta y definida
        (1.508,  0.074, 0.068,    0.091,    0.000,   True),  # 10: Ojos (Z = 1.508)
        (1.524,  0.075, 0.071,    0.090,   -0.002,   True),  # 11: Pómulos y cejas expresivas
        (1.542,  0.074, 0.068,    0.088,   -0.004,   True),  # 12: Sienes y frente baja
        (1.558,  0.072, 0.063,    0.084,   -0.006,   True),  # 13: Frente media
        (1.574,  0.068, 0.055,    0.078,   -0.008,   False), # 14: Bóveda craneal
        (1.590,  0.058, 0.044,    0.068,   -0.010,   False), # 15: Bóveda alta
        (1.606,  0.040, 0.030,    0.045,   -0.012,   False), # 16: Coronilla
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

    for l_idx in range(len(head_profile) - 1):
        r1 = rings[l_idx]
        r2 = rings[l_idx + 1]
        z_mid = (head_profile[l_idx][0] + head_profile[l_idx + 1][0]) * 0.5
        for i in range(n_ring):
            inxt = (i + 1) % n_ring
            f = bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))
            ang_mid = (2.0 * math.pi * (i + 0.5)) / n_ring
            sin_mid = math.sin(ang_mid)
            is_face_skin = (z_mid < 1.565 and sin_mid > -0.05)
            f.material_index = 0 if is_face_skin else 2
            for loop in f.loops: loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

    top_vert = bm.verts.new((0.0, -0.012, 1.610))
    r_last = rings[-1]
    for i in range(n_ring):
        inxt = (i + 1) % n_ring
        f_top = bm.faces.new((r_last[i], r_last[inxt], top_vert))
        f_top.material_index = 2
        for loop in f_top.loops: loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

    # Globos oculares 3D (Z = 1.508, Y = 0.0535)
    eye_pos = [(0.033, 0.0535, 1.508), (-0.033, 0.0535, 1.508)]
    eye_r = 0.0120
    for pos in eye_pos:
        e_bm = bmesh.new()
        bmesh.ops.create_uvsphere(e_bm, u_segments=16, v_segments=12, radius=eye_r)
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

    # Párpados 3D
    upper_lid_margin_verts, upper_lid_crease_verts = [], []
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
                f.material_index = 0
                for loop in f.loops: loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

    # Orejas
    for is_l in (True, False):
        s_sign = 1.0 if is_l else -1.0
        ear_bm = bmesh.new()
        bmesh.ops.create_uvsphere(ear_bm, u_segments=8, v_segments=6, radius=0.014)
        bmesh.ops.scale(ear_bm, verts=ear_bm.verts, vec=(0.35, 0.65, 1.15))
        bmesh.ops.rotate(ear_bm, verts=ear_bm.verts, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(s_sign * 12.0), 4, 'Y'))
        bmesh.ops.translate(ear_bm, verts=ear_bm.verts, vec=(s_sign * 0.071, -0.006, 1.498))
        v_map = {v: bm.verts.new(v.co) for v in ear_bm.verts}
        for f in ear_bm.faces:
            nf = bm.faces.new([v_map[v] for v in f.verts])
            nf.material_index = 0
            for loop in nf.loops: loop[uv_lay].uv = (0.5, 0.5)
        ear_bm.free()

    # -------------------------------------------------------------------------
    # MELENA SETENTERA CANÓNICA Y VOLUMINOSA 360° (scratch/humans/astorga.png)
    # Volumen ancho en sienes (RX hasta 0.124), ondas suaves, flequillo lateral
    # y caída continua estanca en 360° sin ningún hueco.
    # -------------------------------------------------------------------------
    hair_bm = bmesh.new()
    hair_rings_spec = [
        # z,     rx,    ry_front, ry_back, y_offset, face_open
        (1.632, 0.035, 0.030,    0.035,   -0.010,   0.00), # Coronilla alta redondeada
        (1.615, 0.070, 0.055,    0.075,   -0.010,   0.00), # Bóveda superior
        (1.590, 0.098, 0.074,    0.102,   -0.008,   0.00), # Coronilla media
        (1.562, 0.118, 0.080,    0.114,   -0.006,   0.20), # Flequillo cae hacia los lados
        (1.528, 0.126, 0.068,    0.122,   -0.006,   0.50), # Sienes muy anchas y voluminosas (foto)
        (1.490, 0.124, 0.054,    0.120,   -0.008,   0.68), # Orejas cubiertas completamente
        (1.450, 0.114, 0.040,    0.116,   -0.010,   0.80), # Caída hacia mandíbula y nuca
        (1.412, 0.098, 0.026,    0.108,   -0.012,   0.88), # Nuca baja
        (1.380, 0.082, 0.012,    0.098,   -0.014,   0.94), # Puntas sobre cuello de saco
    ]

    n_hverts = 32
    h_rings = []
    for l_idx, (hz, hrx, hry_f, hry_b, hy_off, f_open) in enumerate(hair_rings_spec):
        cur_ring = []
        for i in range(n_hverts):
            ang = (2.0 * math.pi * i) / n_hverts
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)

            # Ondulación setentera orgánica
            wave = 0.006 * math.sin(ang * 4.0 + l_idx * 0.75) + 0.003 * math.cos(ang * 6.0)

            hx = (hrx + wave) * cos_a
            hy_base = (hry_f if sin_a >= 0 else hry_b) + wave
            hy = hy_base * sin_a + hy_off

            # Apertura frontal armónica del rostro (frente y ojos despejados, sienes cubiertas)
            if f_open > 0 and sin_a > 0:
                center_factor = math.exp(-((cos_a / 0.52)**2))
                hy -= f_open * 0.060 * center_factor
                hx *= (1.0 + f_open * 0.14 * center_factor)

            if l_idx == len(hair_rings_spec) - 1:
                hz_eff = hz + 0.008 * math.sin(ang * 5.0)**2
            else:
                hz_eff = hz

            v = hair_bm.verts.new((hx, hy, hz_eff))
            cur_ring.append(v)
        h_rings.append(cur_ring)

    for l_idx in range(len(hair_rings_spec) - 1):
        r1 = h_rings[l_idx]
        r2 = h_rings[l_idx + 1]
        for i in range(n_hverts):
            inxt = (i + 1) % n_hverts
            f = hair_bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))
            f.material_index = 2

    # Ápice
    apex_top = hair_bm.verts.new((0.0, -0.010, 1.636))
    r_top = h_rings[0]
    for i in range(n_hverts):
        inxt = (i + 1) % n_hverts
        f = hair_bm.faces.new((r_top[i], apex_top, r_top[inxt]))
        f.material_index = 2

    v_map_h = {v: bm.verts.new(v.co) for v in hair_bm.verts}
    for f in hair_bm.faces:
        nf = bm.faces.new([v_map_h[v] for v in f.verts])
        nf.material_index = 2
        for loop in nf.loops:
            loop[uv_lay].uv = (0.5 + loop.vert.co.x * 2.0, 0.5 + (loop.vert.co.z - 1.50) * 2.0)
    hair_bm.free()

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
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
# 2. CUERPO: SASTRERÍA FORMAL 70s, CAMISA VINOTINTO COMPLETA Y PRENSIÓN EXACTA
# =============================================================================
def build_body_mesh(materials):
    mesh_graph = bpy.data.meshes.new("Body_Graph_Data")
    obj_body = bpy.data.objects.new("Player_Body_Mesh", mesh_graph)
    bpy.context.scene.collection.objects.link(obj_body)

    # Grafo anatómico con hombreras estructuradas de traje y proporciones reales (1.65 m)
    nodes = [
        # Tronco
        (0.00,  0.000, 0.74, 0.114, 0.078), # 0: Crotch anatómico
        (0.00,  0.002, 0.86, 0.118, 0.078), # 1: Caderas / Cintura baja (dobladillo de saco)
        (0.00,  0.004, 0.98, 0.114, 0.074), # 2: Cintura entallada
        (0.00, -0.004, 1.10, 0.126, 0.084), # 3: Tórax
        (0.00, -0.006, 1.22, 0.142, 0.092), # 4: Pectorales y espalda ancha sastre
        (0.00, -0.003, 1.31, 0.134, 0.082), # 5: Clavículas / hombros
        (0.00,  0.002, 1.36, 0.044, 0.044), # 6: Base cuello camisero

        # Brazos sastre estructurados (ancho de hombros clásico en X = 0.185)
        ( 0.06, -0.003, 1.31, 0.048, 0.048), # 7
        ( 0.185,-0.003, 1.29, 0.044, 0.044), # 8: Hombro L estructurado con hombrera
        ( 0.245, 0.002, 1.12, 0.035, 0.035), # 9: Codo L
        ( 0.285, 0.008, 0.915, 0.026, 0.024), # 10: Manga puño L

        (-0.06, -0.003, 1.31, 0.048, 0.048), # 11
        (-0.185,-0.003, 1.29, 0.044, 0.044), # 12: Hombro R estructurado con hombrera
        (-0.245, 0.002, 1.12, 0.035, 0.035), # 13: Codo R
        (-0.285, 0.008, 0.915, 0.026, 0.024), # 14: Manga puño R

        # Piernas con pantalón sastre recto clásico
        ( 0.062, 0.002, 0.74, 0.052, 0.052), # 15: Cadera sup L
        ( 0.062, 0.002, 0.58, 0.046, 0.046), # 16: Muslo medio L
        ( 0.062, 0.000, 0.43, 0.040, 0.040), # 17: Rodilla L
        ( 0.062, 0.000, 0.27, 0.036, 0.036), # 18: Pantorrilla L
        ( 0.062, 0.002, 0.11, 0.032, 0.032), # 19: Tobillo L
        ( 0.062, 0.048, 0.03, 0.036, 0.090), # 20: Zapato L formal con puntera

        (-0.062, 0.002, 0.74, 0.052, 0.052), # 21: Cadera sup R
        (-0.062, 0.002, 0.58, 0.046, 0.046), # 22: Muslo medio R
        (-0.062, 0.000, 0.43, 0.040, 0.040), # 23: Rodilla R
        (-0.062, 0.000, 0.27, 0.036, 0.036), # 24: Pantorrilla R
        (-0.062, 0.002, 0.11, 0.032, 0.032), # 25: Tobillo R
        (-0.062, 0.048, 0.03, 0.036, 0.090), # 26: Zapato R formal con puntera

        # Muñecas y Palmas
        ( 0.285,  0.010, 0.885, 0.018, 0.014), # 27: Muñeca L
        ( 0.285,  0.010, 0.835, 0.022, 0.012), # 28: Palma L
        (-0.285,  0.010, 0.885, 0.018, 0.014), # 29: Muñeca R
        (-0.285,  0.010, 0.835, 0.022, 0.012), # 30: Palma R
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

    # Mapeo de materiales:
    # 0: Mat_Astorga_Suit   (Saco formal negro carbón)
    # 1: Mat_Astorga_Pants  (Pantalón sastre negro)
    # 2: Mat_Astorga_Shoes  (Zapatos negros pulidos)
    # 3: Mat_Astorga_Skin   (Manos y muñecas)
    # 4: Mat_Astorga_Shirt  (Camisa vinotinto MODELADA Y EXTENDIDA)
    # 5: Mat_Astorga_Tie    (Corbata de seda oscura)
    # 6: Mat_Astorga_Belt   (Cinturón formal)
    # 7: Mat_Astorga_Buckle (Hebilla metálica)
    # 8: Mat_Astorga_Buttons (Botones)
    for p in bm.faces:
        c_median = p.calc_center_median()
        cz = c_median.z
        cx = abs(c_median.x)
        cy = c_median.y

        if cz < 0.08:
            p.material_index = 2 # Zapatos
        elif cz < 0.74 and cx < 0.15:
            p.material_index = 1 # Pantalón sastre bajo el faldón
        elif cx > 0.16:
            if cz < 0.90:
                p.material_index = 3 # Manos
            else:
                p.material_index = 0 # Mangas del saco
        else:
            # Torso y sastrería:
            # - Camisa vinotinto en el centro frontal continuo desde Z = 1.35 hasta Z = 0.88 (cintura)
            # - En la cintura (Z = 0.86 a 0.89) en el centro frontal: cinturón formal con hebilla
            # - En Z < 0.86 en el centro: pantalón formal negro visible en la apertura en V invertida
            # - En costados y espalda: saco formal
            if cy > 0.025:
                # Centro del pecho:
                if 0.89 <= cz <= 1.35 and cx < (0.026 + max(0.0, (cz - 1.05) / 0.30) * 0.038):
                    p.material_index = 4 # Camisa vinotinto
                elif 0.86 <= cz < 0.89 and cx < 0.035:
                    p.material_index = 7 if cx < 0.012 else 6 # Hebilla / Cinturón
                elif 0.74 <= cz < 0.86 and cx < (0.018 + (0.86 - cz) * 0.38):
                    p.material_index = 1 # Pantalón formal en la apertura inferior
                else:
                    p.material_index = 0 # Saco
            else:
                p.material_index = 0 # Saco en espalda

        for loop in p.loops:
            loop[uv_lay].uv = (loop.vert.co.x * 2.0 + 0.5, loop.vert.co.z * 1.5)

    # -------------------------------------------------------------------------
    # A. CUELLO Y PECHERA CAMISERA VINOTINTO TRIDIMENSIONAL
    # -------------------------------------------------------------------------
    n_c = 18
    c_bot, c_top = [], []
    for i in range(n_c):
        ang = (2.0 * math.pi * i) / n_c
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        cx = 0.046 * cos_a
        cy = (0.048 if sin_a >= 0 else 0.044) * sin_a + 0.002
        c_bot.append(bm.verts.new((cx, cy, 1.340)))
        c_top.append(bm.verts.new((cx * 1.05, cy * 1.05, 1.385)))
    for i in range(n_c):
        inxt = (i + 1) % n_c
        bm.faces.new((c_bot[i], c_bot[inxt], c_top[inxt], c_top[i])).material_index = 4

    wing_l = [bm.verts.new((0.006, 0.054, 1.382)), bm.verts.new((0.040, 0.044, 1.375)), bm.verts.new((0.020, 0.068, 1.335))]
    wing_r = [bm.verts.new((-0.006, 0.054, 1.382)), bm.verts.new((-0.020, 0.068, 1.335)), bm.verts.new((-0.040, 0.044, 1.375))]
    bm.faces.new(wing_l).material_index = 4
    bm.faces.new(wing_r).material_index = 4

    # -------------------------------------------------------------------------
    # B. CORBATA TRIDIMENSIONAL CON NUDO WINDSOR CAYENDO VERTICAL
    # -------------------------------------------------------------------------
    knot_v = [
        bm.verts.new((-0.014, 0.056, 1.375)),
        bm.verts.new(( 0.014, 0.056, 1.375)),
        bm.verts.new(( 0.010, 0.076, 1.335)),
        bm.verts.new((-0.010, 0.076, 1.335)),
        bm.verts.new(( 0.000, 0.084, 1.355)),
    ]
    for f_verts in [
        (knot_v[0], knot_v[1], knot_v[4]),
        (knot_v[1], knot_v[2], knot_v[4]),
        (knot_v[2], knot_v[3], knot_v[4]),
        (knot_v[3], knot_v[0], knot_v[4]),
    ]:
        bm.faces.new(f_verts).material_index = 5

    tie_profile = [
        (1.335,  0.010,  0.076),
        (1.265,  0.012,  0.088),
        (1.195,  0.013,  0.092),
        (1.125,  0.013,  0.090),
        (1.055,  0.011,  0.084),
    ]
    tie_rows = []
    for tz, thw, ty in tie_profile:
        vl = bm.verts.new((-thw, ty, tz))
        vm = bm.verts.new(( 0.000, ty + 0.003, tz))
        vr = bm.verts.new(( thw, ty, tz))
        tie_rows.append((vl, vm, vr))

    for idx in range(len(tie_rows) - 1):
        la, ma, ra = tie_rows[idx]
        lb, mb, rb = tie_rows[idx + 1]
        bm.faces.new((la, ma, mb, lb)).material_index = 5
        bm.faces.new((ma, ra, rb, mb)).material_index = 5

    # -------------------------------------------------------------------------
    # C. SASTRERÍA 3D: SOLAPAS NOTCH ANCHAS ESTILO 70s INTEGRADAS AL CUERPO
    # Cero alas despegadas: la silueta sastre abraza orgánicamente el torso
    # -------------------------------------------------------------------------
    for s_side in (1.0, -1.0):
        lapel_v = [
            bm.verts.new((s_side * 0.040, 0.042, 1.355)),
            bm.verts.new((s_side * 0.084, 0.076, 1.305)), # Solapa ancha setentera
            bm.verts.new((s_side * 0.088, 0.086, 1.265)),
            bm.verts.new((s_side * 0.072, 0.088, 1.250)),
            bm.verts.new((s_side * 0.084, 0.096, 1.230)),
            bm.verts.new((s_side * 0.014, 0.084, 1.060)),
            bm.verts.new((s_side * 0.032, 0.088, 1.210)),
        ]
        if s_side > 0:
            bm.faces.new((lapel_v[0], lapel_v[1], lapel_v[2], lapel_v[3])).material_index = 0
            bm.faces.new((lapel_v[0], lapel_v[3], lapel_v[6])).material_index = 0
            bm.faces.new((lapel_v[3], lapel_v[4], lapel_v[5], lapel_v[6])).material_index = 0
        else:
            bm.faces.new((lapel_v[1], lapel_v[0], lapel_v[3], lapel_v[2])).material_index = 0
            bm.faces.new((lapel_v[3], lapel_v[0], lapel_v[6])).material_index = 0
            bm.faces.new((lapel_v[4], lapel_v[3], lapel_v[6], lapel_v[5])).material_index = 0

    sc_top, sc_bot = [], []
    for i in range(10):
        ang = math.pi * 0.15 + (math.pi * 0.70 * i) / 9.0
        bx = 0.048 * math.cos(ang)
        by = -0.046 * math.sin(ang) - 0.003
        sc_top.append(bm.verts.new((bx, by, 1.372)))
        sc_bot.append(bm.verts.new((bx, by, 1.345)))
    for i in range(9):
        bm.faces.new((sc_bot[i], sc_bot[i+1], sc_top[i+1], sc_top[i])).material_index = 0

    # Botones sastre anclados exactamente sobre la tela
    button_coords = [
        (0.004, 0.084, 1.055),
        (0.004, 0.082, 0.980)
    ]
    for (bx, by, bz) in button_coords:
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.0042)
        bmesh.ops.scale(btn_bm, verts=btn_bm.verts, vec=(1.0, 0.30, 1.0))
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(bx, by + 0.0012, bz))
        v_map_b = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            bm.faces.new([v_map_b[v] for v in f.verts]).material_index = 8
        btn_bm.free()

    # Bolsillo de ojal
    p_box = [
        bm.verts.new((0.044, 0.092, 1.205)),
        bm.verts.new((0.080, 0.088, 1.205)),
        bm.verts.new((0.080, 0.088, 1.198)),
        bm.verts.new((0.044, 0.092, 1.198)),
    ]
    bm.faces.new(p_box).material_index = 0

    # Puños de camisa
    for is_l in (True, False):
        s_sign = 1.0 if is_l else -1.0
        n_cuff = 12
        cuff_top, cuff_bot = [], []
        for k in range(n_cuff):
            ang = (2.0 * math.pi * k) / n_cuff
            cx = s_sign * 0.285 + 0.021 * math.cos(ang)
            cy = 0.008 + 0.017 * math.sin(ang)
            cuff_top.append(bm.verts.new((cx, cy, 0.915)))
            cuff_bot.append(bm.verts.new((cx * 1.01, cy * 1.01, 0.895)))
        for k in range(n_cuff):
            kn = (k + 1) % n_cuff
            bm.faces.new((cuff_top[k], cuff_top[kn], cuff_bot[kn], cuff_bot[k])).material_index = 4

        for b_mz in [0.925, 0.938, 0.951]:
            btn_m = bmesh.new()
            bmesh.ops.create_uvsphere(btn_m, u_segments=6, v_segments=4, radius=0.0022)
            bmesh.ops.translate(btn_m, verts=btn_m.verts, vec=(s_sign * (0.285 + 0.023), 0.008, b_mz))
            v_map_bm = {v: bm.verts.new(v.co) for v in btn_m.verts}
            for f in btn_m.faces:
                bm.faces.new([v_map_bm[v] for v in f.verts]).material_index = 8
            btn_m.free()

    # -------------------------------------------------------------------------
    # D. MANOS ANATÓMICAS CON PRENSIÓN EXACTA SEGÚN scratch/humans/astorga.png
    # - Mano izquierda (viewer's left): empuña el talón del arco con dedos curvados
    # - Mano derecha (viewer's right): sostiene el mástil del violín con dedos rodeando el mástil
    # -------------------------------------------------------------------------
    for is_l in (True, False):
        sign_a = 1.0 if is_l else -1.0
        w_center = Vector((sign_a * 0.285, 0.008, 0.835))
        z_knuckles = 0.832

        finger_specs = [
            ("Index",   w_center.y + 0.012, 0.046, 0.0048),
            ("Middle",  w_center.y + 0.003, 0.050, 0.0050),
            ("Ring",    w_center.y - 0.005, 0.045, 0.0048),
            ("Pinky",   w_center.y - 0.013, 0.036, 0.0042),
        ]

        if is_l:
            # Mano izquierda empuñando el arco: dedos firmemente cerrados hacia la palma
            curl_dir = Vector((-0.25, 0.82, -0.40)).normalized()
        else:
            # Mano derecha sosteniendo el violín: dedos curvados abrazando el mástil por el frente
            curl_dir = Vector(( 0.35, 0.70, -0.45)).normalized()

        for (f_name, fy, f_len, f_rad) in finger_specs:
            fx = sign_a * 0.285
            n_seg = 3
            prev_fring = None
            for s in range(n_seg + 1):
                t = s / float(n_seg)
                fz = z_knuckles - f_len * (t**0.85) * 0.68
                cur_y = fy + curl_dir.y * (f_len * 0.78 * (t**1.2))
                cur_x = fx + curl_dir.x * (f_len * 0.42 * (t**1.2))
                r_cur = f_rad * (1.0 - 0.25 * t)

                cur_fring = []
                for k in range(6):
                    fang = (2.0 * math.pi * k) / 6.0
                    cur_fring.append(bm.verts.new((cur_x + r_cur * math.cos(fang),
                                                  cur_y + r_cur * math.sin(fang),
                                                  fz + curl_dir.z * (f_len * 0.30 * t))))
                if prev_fring:
                    for k in range(6):
                        knxt = (k + 1) % 6
                        bm.faces.new((prev_fring[k], prev_fring[knxt], cur_fring[knxt], cur_fring[k])).material_index = 3
                prev_fring = cur_fring

            tip_v = bm.verts.new((cur_x + curl_dir.x * 0.004, cur_y + curl_dir.y * 0.004, fz - 0.004))
            for k in range(6):
                knxt = (k + 1) % 6
                bm.faces.new((prev_fring[knxt], prev_fring[k], tip_v)).material_index = 3

        # Pulgar opuesto
        th_root = Vector((sign_a * (0.285 - 0.014), w_center.y + 0.008, 0.838))
        prev_th = None
        th_curl = Vector((-sign_a * 0.45, 0.68, -0.32)).normalized()
        for s in range(4):
            t = s / 3.0
            tx = th_root.x + th_curl.x * 0.024 * t
            ty = th_root.y + th_curl.y * 0.024 * t
            tz = th_root.z - 0.020 * t
            trad = 0.0054 * (1.0 - 0.22 * t)
            cur_th = []
            for k in range(6):
                tang = (2.0 * math.pi * k) / 6.0
                cur_th.append(bm.verts.new((tx + trad * math.cos(tang),
                                           ty + trad * math.sin(tang),
                                           tz)))
            if prev_th:
                for k in range(6):
                    knxt = (k + 1) % 6
                    bm.faces.new((prev_th[k], prev_th[knxt], cur_th[knxt], cur_th[k])).material_index = 3
            prev_th = cur_th

        tip_th = bm.verts.new((tx + th_curl.x * 0.003, ty + th_curl.y * 0.003, tz - 0.003))
        for k in range(6):
            knxt = (k + 1) % 6
            bm.faces.new((prev_th[knxt], prev_th[k], tip_th)).material_index = 3

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    for f in bm.faces: f.smooth = True

    bm.to_mesh(obj_body.data)
    bm.free()

    for mat in materials["body"]:
        obj_body.data.materials.append(mat)

    return obj_body

# =============================================================================
# 3. ESQUELETO Y RIGGING CON SUAVIZADO EN HOMBROS (CERO SUMIDO Y CERO ERRORES)
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
        ("Hips",        "Root",        (0, 0, 0.74),      (0, 0, 0.88)),
        ("Spine",       "Hips",        (0, 0, 0.88),      (0, 0, 1.10)),
        ("Chest",       "Spine",       (0, 0, 1.10),      (0, 0, 1.31)),
        ("Neck",        "Chest",       (0, 0, 1.31),      (0, 0, 1.38)),
        ("Head",        "Neck",        (0, 0, 1.38),      (0, 0, 1.63)),

        ("Shoulder.L",  "Chest",       (0.04, 0, 1.31),   (0.180, 0, 1.30)),
        ("UpperArm.L",  "Shoulder.L",  (0.180, 0, 1.30),  (0.245, 0.005, 1.12)),
        ("Forearm.L",   "UpperArm.L",  (0.245, 0.005, 1.12),(0.285, 0.015, 0.915)),
        ("Hand.L",      "Forearm.L",   (0.285, 0.015, 0.915),(0.285, 0.015, 0.76)),

        ("Shoulder.R",  "Chest",       (-0.04, 0, 1.31),  (-0.180, 0, 1.30)),
        ("UpperArm.R",  "Shoulder.R",  (-0.180, 0, 1.30), (-0.245, 0.005, 1.12)),
        ("Forearm.R",   "UpperArm.R",  (-0.245, 0.005, 1.12),(-0.285, 0.015, 0.915)),
        ("Hand.R",      "Forearm.R",   (-0.285, 0.015, 0.915),(-0.285, 0.015, 0.76)),

        ("UpperLeg.L",  "Hips",        (0.062, 0, 0.74),  (0.062, 0, 0.43)),
        ("LowerLeg.L",  "UpperLeg.L",  (0.062, 0, 0.43),  (0.062, 0, 0.11)),
        ("Foot.L",      "LowerLeg.L",  (0.062, 0, 0.11),  (0.062, 0.048, 0.03)),
        ("Toes.L",      "Foot.L",      (0.062, 0.048, 0.03),(0.062, 0.095, 0.00)),

        ("UpperLeg.R",  "Hips",        (-0.062, 0, 0.74), (-0.062, 0, 0.43)),
        ("LowerLeg.R",  "UpperLeg.R",  (-0.062, 0, 0.43), (-0.062, 0, 0.11)),
        ("Foot.R",      "LowerLeg.R",  (-0.062, 0, 0.11), (-0.062, 0.048, 0.03)),
        ("Toes.R",      "Foot.R",      (-0.062, 0.048, 0.03),(-0.062, 0.095, 0.00)),
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
            if co.z < 1.38:
                obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 1.42:
                t = (co.z - 1.38) / 0.04
                obj.vertex_groups["Neck"].add([v.index], 1.0 - t, 'REPLACE')
                obj.vertex_groups["Head"].add([v.index], t, 'REPLACE')
            else:
                obj.vertex_groups["Head"].add([v.index], 1.0, 'REPLACE')
        else:
            ax = abs(co.x)
            # 1. BRAZOS
            if ax > 0.165 and co.z < 1.35 and co.z >= 0.70:
                side = ".L" if co.x > 0 else ".R"
                if co.z < 0.90:
                    obj.vertex_groups["Hand" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.94:
                    t = (co.z - 0.90) / 0.04
                    obj.vertex_groups["Hand" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Forearm" + side].add([v.index], t, 'REPLACE')
                elif co.z < 1.10:
                    obj.vertex_groups["Forearm" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.18:
                    t = (co.z - 1.10) / 0.08
                    obj.vertex_groups["Forearm" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["UpperArm" + side].add([v.index], t, 'REPLACE')
                else:
                    if ax > 0.185:
                        obj.vertex_groups["UpperArm" + side].add([v.index], 1.0, 'REPLACE')
                    else:
                        t = (ax - 0.165) / 0.020
                        obj.vertex_groups["Shoulder" + side].add([v.index], 1.0 - t, 'REPLACE')
                        obj.vertex_groups["UpperArm" + side].add([v.index], t, 'REPLACE')

            # 2. HOMBRO INTERIOR / CLAVÍCULA
            elif ax > 0.120 and co.z >= 1.20:
                side = ".L" if co.x > 0 else ".R"
                t = (ax - 0.120) / 0.045
                obj.vertex_groups["Chest"].add([v.index], 1.0 - t, 'REPLACE')
                obj.vertex_groups["Shoulder" + side].add([v.index], t, 'REPLACE')

            # 3. PIERNAS
            elif co.z < 0.74:
                side = ".L" if co.x > 0 else ".R"
                if co.z < 0.035 and co.y > 0.04:
                    obj.vertex_groups["Toes" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.10:
                    obj.vertex_groups["Foot" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.14:
                    t = (co.z - 0.10) / 0.04
                    obj.vertex_groups["Foot" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["LowerLeg" + side].add([v.index], t, 'REPLACE')
                elif co.z < 0.40:
                    obj.vertex_groups["LowerLeg" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 0.48:
                    t = (co.z - 0.40) / 0.08
                    obj.vertex_groups["LowerLeg" + side].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["UpperLeg" + side].add([v.index], t, 'REPLACE')
                else:
                    obj.vertex_groups["UpperLeg" + side].add([v.index], 1.0, 'REPLACE')

            # 4. TORSO Y SACO COMPLETO
            else:
                if co.z < 0.88:
                    obj.vertex_groups["Hips"].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.10:
                    t = (co.z - 0.88) / 0.22
                    obj.vertex_groups["Hips"].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Spine"].add([v.index], t, 'REPLACE')
                elif co.z < 1.28:
                    t = (co.z - 1.10) / 0.18
                    obj.vertex_groups["Spine"].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Chest"].add([v.index], t, 'REPLACE')
                elif co.z < 1.34:
                    t = (co.z - 1.28) / 0.06
                    obj.vertex_groups["Chest"].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Neck"].add([v.index], t, 'REPLACE')
                else:
                    obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')

def attach_armature(obj, arm_obj):
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj
    obj.parent = arm_obj

# =============================================================================
# 4. POSE CANÓNICA EXACTA A LA FOTOGRAFÍA (scratch/humans/astorga.png)
# =============================================================================
def setup_pose_and_props(arm_obj, scene):
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')

    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)

    # 1. Torso y cabeza con garbo relajado según la fotografía
    arm_obj.pose.bones['Chest'].rotation_euler = (math.radians(-2), math.radians(-5), math.radians(2))
    arm_obj.pose.bones['Head'].rotation_euler = (math.radians(-2), math.radians(6), math.radians(2))

    # 2. BRAZO DERECHO (Hand.R, -X, lado derecho de la imagen):
    # Sostiene el VIOLÍN erguido a la altura del pecho derecho.
    # Codo bajo natural cerca del cuerpo, antebrazo sube vertical-diagonal,
    # mano rodea el mástil a la altura del diapasón/caja
    arm_obj.pose.bones['UpperArm.R'].rotation_euler = (math.radians(34), math.radians(16), math.radians(-28))
    arm_obj.pose.bones['Forearm.R'].rotation_euler = (math.radians(96), math.radians(16), math.radians(-10))
    arm_obj.pose.bones['Hand.R'].rotation_euler = (math.radians(24), math.radians(-18), math.radians(44))

    # 3. BRAZO IZQUIERDO (Hand.L, +X, lado izquierdo de la imagen):
    # Sostiene el ARCO en diagonal idéntica a la fotografía.
    # Clavícula acompaña levemente (+3°), deltoides natural (cero sumido),
    # antebrazo cruzado con la mano empuñando el talón del arco
    arm_obj.pose.bones['Shoulder.L'].rotation_euler = (math.radians(3), math.radians(-1), math.radians(3))
    arm_obj.pose.bones['UpperArm.L'].rotation_euler = (math.radians(20), math.radians(-5), math.radians(10))
    arm_obj.pose.bones['Forearm.L'].rotation_euler = (math.radians(52), math.radians(-8), math.radians(8))
    arm_obj.pose.bones['Hand.L'].rotation_euler = (math.radians(24), math.radians(12), math.radians(-10))

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()

    hand_l_mat = arm_obj.matrix_world @ arm_obj.pose.bones['Hand.L'].matrix
    hand_r_mat = arm_obj.matrix_world @ arm_obj.pose.bones['Hand.R'].matrix
    hand_l_loc = hand_l_mat.to_translation()
    hand_r_loc = hand_r_mat.to_translation()

    # Cargar y posicionar Violín y Arco de forma milimétrica
    if os.path.exists(VIOLIN_BLEND):
        with bpy.data.libraries.load(VIOLIN_BLEND, link=False) as (data_from, data_to):
            data_to.objects = [o for o in data_from.objects if o in ("Violin_Prop", "Violin_Bow")]
        for o in data_to.objects:
            if o:
                scene.collection.objects.link(o)
                for p in o.data.polygons: p.use_smooth = True
                if o.name == "Violin_Prop":
                    o.scale = (0.76, 0.76, 0.76)
                    # El violín vertical sujetado anatómicamente en Hand.R:
                    # El mástil pasa exactamente por el agarre de la mano derecha
                    o.rotation_euler = Euler((math.radians(-76), math.radians(172), math.radians(18)), 'XYZ')
                    # Ubicación calibrada para que los dedos abracen el mástil por el frente
                    o.location = Vector((hand_r_loc.x + 0.012, hand_r_loc.y + 0.004, hand_r_loc.z - 0.220))
                elif o.name == "Violin_Bow":
                    o.scale = (0.70, 0.70, 0.70)
                    # El arco pasa DIRECTAMENTE a través de la palma y dedos de Hand.L:
                    # Apunta en diagonal elegante hacia el hombro/pecho como en la fotografía
                    o.rotation_euler = Euler((math.radians(26), math.radians(-4), math.radians(-18)), 'XYZ')
                    o.location = Vector((hand_l_loc.x + 0.004, hand_l_loc.y + 0.020, hand_l_loc.z - 0.005))

def render_dual_views(scene):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 36

    for l in [o for o in scene.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(l, do_unlink=True)

    def add_l(name, en, loc, col=(1.0, 0.98, 0.95), size=1.5):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = en
        ld.color = col
        ld.size = size
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        scene.collection.objects.link(lo)

    head_t = (0.0, 0.0, 1.48)
    chest_t = (0.0, 0.0, 1.20)
    add_l("KeyWarm",    135.0, ( 0.6, 1.8, 1.6), (1.0, 0.96, 0.92), size=1.6)
    add_l("FillFront",   70.0, (-0.8, 1.7, 1.4), (0.94, 0.96, 1.0),  size=2.2)
    add_l("RimBack",    100.0, ( 0.1, -1.5, 1.7), (1.0, 0.98, 0.95), size=1.5)
    add_l("ViolinLight", 50.0, (-0.4, 1.6, 1.28), (1.0, 0.95, 0.90), size=1.0)
    add_l("HairLight",   55.0, ( 0.0, 0.3, 1.9), (1.0, 0.98, 0.96), size=1.2)

    cam_data = bpy.data.cameras.new("CamAstorga")
    cam = bpy.data.objects.new("CamAstorga", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    # 1. Render de Tarjeta / Retrato (1024x1024)
    cam_data.lens = 72.0
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    cam.location = Vector((0.0, 2.15, 1.24))
    target = Vector((0.0, 0.0, 1.21))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()

    out_card = os.path.join(SCRATCH_DIR, "test_astorga_portrait_perfect.png")
    scene.render.filepath = out_card
    bpy.ops.render.render(write_still=True)
    print("✓ Render de tarjeta/retrato guardado en:", out_card)

    # 2. Render de Cuerpo Completo (800x1200)
    cam_data.lens = 52.0
    cam.location = Vector((0.0, 2.50, 0.96))
    target_fb = Vector((0.0, 0.0, 0.88))
    cam.rotation_euler = (target_fb - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1200

    out_fb = os.path.join(SCRATCH_DIR, "test_astorga_fullbody_perfect.png")
    scene.render.filepath = out_fb
    bpy.ops.render.render(write_still=True)
    print("✓ Render de cuerpo completo guardado en:", out_fb)

def main():
    clean_scene()
    mats = create_materials()
    mat_groups = {
        "head": [mats["skin"], mats["eyes"], mats["hair"]],
        "body": [mats["suit"], mats["pants"], mats["shoes"], mats["skin"], mats["shirt"], mats["tie"], mats["belt"], mats["buckle"], mats["buttons"]],
    }

    arm_obj = build_skeleton()
    obj_head = build_head_mesh(mat_groups)
    assign_weights(obj_head, is_head=True)
    attach_armature(obj_head, arm_obj)

    obj_body = build_body_mesh(mat_groups)
    assign_weights(obj_body, is_head=False)
    attach_armature(obj_body, arm_obj)

    scene = bpy.context.scene
    setup_pose_and_props(arm_obj, scene)
    render_dual_views(scene)
    print("✓ Script test_astorga_perfect ejecutado exitosamente.")

if __name__ == "__main__":
    main()
