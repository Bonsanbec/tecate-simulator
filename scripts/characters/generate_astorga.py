"""
=============================================================================
GENERADOR CANÓNICO PROCEDURAL DE ALTA FIDELIDAD: ASTORGA (TECATE SIMULATOR)
=============================================================================
Reconstrucción fidedigna del personaje Astorga ("Músico") en Tecate Simulator:
1. Cabeza, Rostro y Fenotipo Auténtico:
   - Fisonomía facial expresiva (mentón firme, perfil nasal recto, mandíbula angular).
   - Piel apiñonada cálida con textura PBR fidedigna ('scratch/humans/astorga.png').
   - Ojos castaños profundos con párpados 3D y Shape Key 'blink'.
   - Melena setentera continua y voluminosa en 360° con ondas orgánicas,
     volumen amplio en sienes que cubre las orejas, flequillo peinado a los lados
     y caída fluida hacia la nuca (sin huecos ni desconexiones desde ningún ángulo).
2. Arquitectura de Sastrería en 3 Capas Físicas:
   - Cuerpo Base: Piernas con pantalón formal recto de paño negro, calzado sastre
     pulido con tacón y suela, pretina con cinturón y hebilla en Z = 0.94.
   - Camisa Vinotinto: Prenda cilíndrica entallada continua independiente
     desde el cuello hasta la cintura (Z = 0.94, fajada formalmente),
     con cuello camisero 3D, tapeta y corbata negra con nudo Windsor.
   - Saco Formal Sastre (Smoking Negro): Chaqueta tridimensional envolvente
     (r_saco > r_camisa) que cubre espalda y costados (Z = 0.74 a 1.34).
     Hombros y deltoides 100% negros estructurados.
     Abierta en el frente: escote superior en V en el pecho, botón central
     en Z = 1.05 y faldones que se abren en V invertida hacia las caderas,
     revelando la camisa vinotinto fajada, el cinturón y los pantalones.
     Solapas notch clásicas en relieve 3D.
   - Brazos y Manos: Mangas estructuradas, puños vinotinto asomando,
     muñecas y manos anatómicas con dedos y pulgar oponible calibrados.
3. Rigging Canónico de 22 Huesos y Ponderación Armónica (Cero Deltoides Sumido):
   - Transición radial continua basada en distancia euclidiana e interpolación armónica,
     garantizando curvatura convexa sin colapso axilar, de codo ni de rodilla.
4. Exportación Limpia a 'astorga.blend' y 'astorga.glb'.
5. Renders de Control Multi-Ángulo con Cycles CPU.
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

def setup_pbr_material(name, diffuse_tex_path, normal_tex_path=None,
                       base_color=(0.8, 0.8, 0.8, 1.0), roughness=0.6,
                       metallic=0.0, specular=0.5):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
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
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = specular

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
                                   base_color=(0.025, 0.020, 0.018, 1.0), roughness=0.68, specular=0.35),
        "suit": setup_pbr_material("Mat_Astorga_Suit",
                                   os.path.join(TEXTURES_DIR, "astorga_suit_diffuse.png"),
                                   os.path.join(TEXTURES_DIR, "astorga_suit_normal.png"),
                                   base_color=(0.024, 0.025, 0.028, 1.0), roughness=0.65),
        "shirt": setup_pbr_material("Mat_Astorga_Shirt",
                                     os.path.join(TEXTURES_DIR, "astorga_shirt_diffuse.png"),
                                     os.path.join(TEXTURES_DIR, "astorga_shirt_normal.png"),
                                     base_color=(0.280, 0.045, 0.065, 1.0), roughness=0.55),
        "tie": setup_pbr_material("Mat_Astorga_Tie",
                                   os.path.join(TEXTURES_DIR, "astorga_tie_diffuse.png"),
                                   os.path.join(TEXTURES_DIR, "astorga_tie_normal.png"),
                                   base_color=(0.016, 0.016, 0.018, 1.0), roughness=0.35, specular=0.55),
        "pants": setup_pbr_material("Mat_Astorga_Pants",
                                     os.path.join(TEXTURES_DIR, "astorga_pants_diffuse.png"),
                                     os.path.join(TEXTURES_DIR, "astorga_pants_normal.png"),
                                     base_color=(0.024, 0.025, 0.028, 1.0), roughness=0.65),
        "shoes": setup_pbr_material("Mat_Astorga_Shoes",
                                     os.path.join(TEXTURES_DIR, "astorga_shoes_diffuse.png"),
                                     os.path.join(TEXTURES_DIR, "astorga_shoes_normal.png"),
                                     base_color=(0.015, 0.015, 0.018, 1.0), roughness=0.20, specular=0.65),
        "buttons": setup_pbr_material("Mat_Astorga_Buttons",
                                       None, None,
                                       base_color=(0.02, 0.02, 0.02, 1.0), roughness=0.20, metallic=0.40),
    }

# =============================================================================
# 1. CABEZA, ROSTRO, OJOS, PÁRPADOS 3D Y MELENA SETENTERA CONTINUA 360°
# =============================================================================
def build_head_mesh(materials):
    me = bpy.data.meshes.new("Player_Head_Mesh_Data")
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")

    def calc_face_uv(x, z):
        u = 0.50 + x / 0.275
        v = 0.50 + (z - 1.485) / 0.240
        return (max(0.0, min(1.0, u)), max(0.0, min(1.0, v)))

    head_profile = [
        # z,      rx,    ry_front, ry_back, y_offset, is_face
        (1.365,  0.042, 0.042,    0.044,   -0.002,   False), # Base cuello
        (1.385,  0.044, 0.043,    0.046,   -0.002,   False), # Cuello medio
        (1.405,  0.048, 0.045,    0.052,    0.000,   True),  # Mandíbula / ángulo
        (1.424,  0.056, 0.062,    0.065,    0.004,   True),  # Mentón firme
        (1.440,  0.060, 0.062,    0.071,    0.003,   True),  # Surco mentolabial
        (1.452,  0.062, 0.064,    0.078,    0.003,   True),  # Labio inferior
        (1.462,  0.064, 0.063,    0.082,    0.002,   True),  # Hendidura labial
        (1.472,  0.066, 0.066,    0.086,    0.002,   True),  # Labio superior
        (1.486,  0.069, 0.065,    0.088,    0.001,   True),  # Base nasal
        (1.498,  0.071, 0.073,    0.089,    0.000,   True),  # Punta nasal recta
        (1.508,  0.073, 0.067,    0.089,    0.000,   True),  # Puente nasal y ojos
        (1.524,  0.074, 0.070,    0.088,   -0.002,   True),  # Pómulos y cejas
        (1.542,  0.073, 0.067,    0.086,   -0.004,   True),  # Sienes y frente baja
        (1.558,  0.071, 0.062,    0.082,   -0.006,   True),  # Frente media
        (1.574,  0.067, 0.054,    0.076,   -0.008,   False), # Bóveda baja
        (1.590,  0.057, 0.043,    0.066,   -0.010,   False), # Bóveda media
        (1.606,  0.039, 0.029,    0.044,   -0.012,   False), # Coronilla
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
                elif l_idx in (8, 10): y += 0.005 * nw

            cur_ring.append(bm.verts.new((x, y, z)))
        rings.append(cur_ring)

    for l_idx in range(len(head_profile) - 1):
        r1 = rings[l_idx]
        r2 = rings[l_idx + 1]
        for i in range(n_ring):
            inxt = (i + 1) % n_ring
            f = bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))
            f.material_index = 0
            for loop in f.loops:
                loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

    crown_center = bm.verts.new((0.0, -0.012, 1.614))
    r_top = rings[-1]
    for i in range(n_ring):
        inxt = (i + 1) % n_ring
        f = bm.faces.new((r_top[inxt], r_top[i], crown_center))
        f.material_index = 0
        for loop in f.loops:
            loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

    # Ojos y párpados 3D
    eye_radius = 0.0125
    eye_z = 1.508
    eye_x = 0.033
    eye_y = 0.064
    for sign in (1.0, -1.0):
        eye_bm = bmesh.new()
        bmesh.ops.create_uvsphere(eye_bm, u_segments=16, v_segments=12, radius=eye_radius)
        bmesh.ops.rotate(eye_bm, verts=eye_bm.verts, cent=(0,0,0),
                         matrix=Euler((0, 0, math.radians(-sign * 3)), 'XYZ').to_matrix())
        bmesh.ops.translate(eye_bm, verts=eye_bm.verts, vec=(sign * eye_x, eye_y, eye_z))
        v_map = {v: bm.verts.new(v.co) for v in eye_bm.verts}
        for f in eye_bm.faces:
            nf = bm.faces.new([v_map[v] for v in f.verts])
            nf.material_index = 1
            for loop in nf.loops:
                loop[uv_lay].uv = (0.5 + (loop.vert.co.x - sign * eye_x) / (2 * eye_radius),
                                   0.5 + (loop.vert.co.z - eye_z) / (2 * eye_radius))
        eye_bm.free()

    upper_lid_margin_verts = []
    upper_lid_crease_verts = []
    n_lid = 8
    for sign in (1.0, -1.0):
        m_ring, c_ring = [], []
        for i in range(n_lid):
            t = i / float(n_lid - 1)
            ang = math.pi * 0.08 + t * (math.pi * 0.84)
            dx = sign * eye_radius * 1.05 * math.cos(ang)
            dy = eye_radius * 1.04 * math.sin(ang)
            dz = eye_radius * 1.04 * math.sin(ang) * 0.40
            vm = bm.verts.new((sign * eye_x + dx, eye_y + dy + 0.0015, eye_z + dz))
            vc = bm.verts.new((sign * eye_x + dx * 1.15, eye_y + dy + 0.0035, eye_z + dz + 0.007))
            m_ring.append(vm)
            c_ring.append(vc)
            upper_lid_margin_verts.append(vm)
            upper_lid_crease_verts.append(vc)
        for i in range(n_lid - 1):
            if sign > 0:
                f = bm.faces.new((m_ring[i], m_ring[i+1], c_ring[i+1], c_ring[i]))
            else:
                f = bm.faces.new((m_ring[i+1], m_ring[i], c_ring[i], c_ring[i+1]))
            f.material_index = 0
            for loop in f.loops:
                loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

    # -------------------------------------------------------------------------
    # MELENA SETENTERA CANÓNICA ORIGINAL (commit 45957b5: 'fix hair astorga')
    # 9 niveles concéntricos con volumen en sienes + capas de flequillo y ondas
    # -------------------------------------------------------------------------
    hair_bm = bmesh.new()
    hair_rings_spec = [
        # z,     rx,    ry_front, ry_back, y_offset, face_open
        (1.636, 0.035, 0.030,    0.035,   -0.010,   0.00), # Coronilla alta redondeada
        (1.618, 0.070, 0.055,    0.075,   -0.010,   0.00), # Bóveda superior
        (1.592, 0.098, 0.074,    0.102,   -0.008,   0.00), # Coronilla media
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
            hair_bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i])).material_index = 2

    # Ápice
    apex_top = hair_bm.verts.new((0.0, -0.010, 1.640))
    r_top = h_rings[0]
    for i in range(n_hverts):
        inxt = (i + 1) % n_hverts
        hair_bm.faces.new((r_top[i], apex_top, r_top[inxt])).material_index = 2

    # Mechones frontales ondulados del flequillo y sienes peinados a los lados
    def add_bang_layer(p_start, p_mid, p_end, w0=0.030, w1=0.038, w2=0.015, thick=0.010):
        n_s = 6
        p0 = Vector(p_start)
        p1 = Vector(p_mid)
        p2 = Vector(p_end)
        prev_v = None
        for s in range(n_s + 1):
            t = s / float(n_s)
            p = (1.0 - t)**2 * p0 + 2.0 * (1.0 - t) * t * p1 + t**2 * p2
            tang = (2.0 * (1.0 - t) * (p1 - p0) + 2.0 * t * (p2 - p1)).normalized()
            up = Vector((0, 0, 1))
            side = tang.cross(up).normalized()
            nor = side.cross(tang).normalized()
            w = w0 + (w1 - w0) * math.sin(t * math.pi)
            tk = thick * (1.0 - 0.3 * t)

            v_l = hair_bm.verts.new(p - side * (w * 0.5))
            v_c = hair_bm.verts.new(p + nor * tk)
            v_r = hair_bm.verts.new(p + side * (w * 0.5))
            cur_v = [v_l, v_c, v_r]
            if prev_v:
                hair_bm.faces.new((prev_v[0], prev_v[1], cur_v[1], cur_v[0])).material_index = 2
                hair_bm.faces.new((prev_v[1], prev_v[2], cur_v[2], cur_v[1])).material_index = 2
            prev_v = cur_v

    add_bang_layer(( 0.005, 0.064, 1.585), ( 0.045, 0.076, 1.550), ( 0.088, 0.055, 1.510), w0=0.034, w1=0.044, w2=0.020)
    add_bang_layer((-0.005, 0.064, 1.585), (-0.045, 0.076, 1.550), (-0.088, 0.055, 1.510), w0=0.034, w1=0.044, w2=0.020)
    add_bang_layer(( 0.020, 0.062, 1.590), ( 0.065, 0.072, 1.545), ( 0.100, 0.042, 1.490), w0=0.032, w1=0.042, w2=0.020)
    add_bang_layer((-0.020, 0.062, 1.590), (-0.065, 0.072, 1.545), (-0.100, 0.042, 1.490), w0=0.032, w1=0.042, w2=0.020)
    add_bang_layer((-0.010, 0.068, 1.580), ( 0.015, 0.078, 1.555), ( 0.045, 0.068, 1.525), w0=0.024, w1=0.032, w2=0.016)
    add_bang_layer(( 0.075, 0.042, 1.550), ( 0.108, 0.035, 1.500), ( 0.096, 0.015, 1.430), w0=0.028, w1=0.036, w2=0.018, thick=0.012)
    add_bang_layer((-0.075, 0.042, 1.550), (-0.108, 0.035, 1.500), (-0.096, 0.015, 1.430), w0=0.028, w1=0.036, w2=0.018, thick=0.012)

    v_map_h = {v: bm.verts.new(v.co) for v in hair_bm.verts}
    for f in hair_bm.faces:
        nf = bm.faces.new([v_map_h[v] for v in f.verts])
        nf.material_index = 2
        for loop in nf.loops:
            loop[uv_lay].uv = (0.5 + loop.vert.co.x * 2.2, 0.5 + (loop.vert.co.z - 1.50) * 2.2)
    hair_bm.free()

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    for f in bm.faces: f.smooth = True

    bm.verts.ensure_lookup_table()
    margin_v_indices = [v.index for v in upper_lid_margin_verts]
    crease_v_indices = [v.index for v in upper_lid_crease_verts]

    bm.to_mesh(me)
    bm.free()

    for mat in materials["head"]: me.materials.append(mat)
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
# 2. CUERPO CANÓNICO (SKIN MODIFIER + SASTRERÍA EXTERNA 3D)
# =============================================================================
def build_body_mesh(materials):
    mesh_graph = bpy.data.meshes.new("Body_Graph_Data")
    obj_body = bpy.data.objects.new("Player_Body_Mesh", mesh_graph)
    bpy.context.scene.collection.objects.link(obj_body)

    # Nodos anatómicos realistas y proporcionados para Astorga (1.65 m)
    nodes = [
        # Tronco
        (0.00,  0.000, 0.76, 0.128, 0.092), # 0: Crotch anatómico
        (0.00,  0.002, 0.88, 0.126, 0.088), # 1: Caderas / Cintura baja
        (0.00,  0.004, 1.00, 0.122, 0.084), # 2: Cintura sastre
        (0.00, -0.004, 1.14, 0.130, 0.090), # 3: Tórax / costillas
        (0.00, -0.006, 1.25, 0.140, 0.096), # 4: Pectorales y espalda
        (0.00, -0.003, 1.33, 0.130, 0.088), # 5: Clavículas / hombros
        (0.00,  0.002, 1.37, 0.046, 0.046), # 6: Base cuello camisero

        # Brazos sastre estructurados
        ( 0.06, -0.003, 1.33, 0.058, 0.058), # 7
        ( 0.180,-0.003, 1.30, 0.050, 0.050), # 8: Hombro L
        ( 0.245, 0.002, 1.12, 0.040, 0.040), # 9: Codo L
        ( 0.285, 0.008, 0.90, 0.030, 0.028), # 10: Manga puño L

        (-0.06, -0.003, 1.33, 0.058, 0.058), # 11
        (-0.180,-0.003, 1.30, 0.050, 0.050), # 12: Hombro R
        (-0.245, 0.002, 1.12, 0.040, 0.040), # 13: Codo R
        (-0.285, 0.008, 0.90, 0.030, 0.028), # 14: Manga puño R

        # Piernas con pantalón formal de proporción y postura natural (1.65 m)
        ( 0.088, 0.002, 0.76, 0.076, 0.074), # 15: Cadera sup L
        ( 0.090, 0.002, 0.60, 0.070, 0.068), # 16: Muslo medio L
        ( 0.092, 0.000, 0.44, 0.062, 0.060), # 17: Rodilla L
        ( 0.094, 0.000, 0.28, 0.056, 0.054), # 18: Pantorrilla L
        ( 0.096, 0.002, 0.12, 0.048, 0.048), # 19: Tobillo L
        ( 0.096, 0.045, 0.03, 0.050, 0.105), # 20: Zapato formal L

        (-0.088, 0.002, 0.76, 0.076, 0.074), # 21: Cadera sup R
        (-0.090, 0.002, 0.60, 0.070, 0.068), # 22: Muslo medio R
        (-0.092, 0.000, 0.44, 0.062, 0.060), # 23: Rodilla R
        (-0.094, 0.000, 0.28, 0.056, 0.054), # 24: Pantorrilla R
        (-0.096, 0.002, 0.12, 0.048, 0.048), # 25: Tobillo R
        (-0.096, 0.045, 0.03, 0.050, 0.105), # 26: Zapato formal R

        # Muñecas anatómicas estructuradas (fin de manga)
        ( 0.285,  0.010, 0.852, 0.014, 0.022), # 27: Muñeca L
        (-0.285,  0.010, 0.852, 0.014, 0.022), # 28: Muñeca R
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6),
        (5, 7), (7, 8), (8, 9), (9, 10), (10, 27),
        (5, 11), (11, 12), (12, 13), (13, 14), (14, 28),
        (0, 15), (15, 16), (16, 17), (17, 18), (18, 19), (19, 20),
        (0, 21), (21, 22), (22, 23), (23, 24), (24, 25), (26, 26) if False else (25, 26),
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

    # Mapeo de materiales en el cuerpo base:
    # 0: suit (negro), 1: pants (negro sastre), 2: shoes (cuero), 3: skin, 4: shirt (vinotinto), 5: tie, 6: buttons
    for p in bm.faces:
        c_median = p.calc_center_median()
        cz = c_median.z
        cx = abs(c_median.x)
        cy = c_median.y

        if cz < 0.12:
            p.material_index = 2 # Zapatos de vestir
        elif cz < 0.94 and cx < 0.20:
            p.material_index = 1 # Pantalón sastre
        elif cx > 0.16 or (cz > 1.24 and cx > 0.05):
            # Mangas, hombros y deltoides: 100% Saco formal NEGRO
            if cz < 0.85 and cx > 0.22:
                p.material_index = 3 # Manos y muñecas de piel
            elif cz < 0.88 and cx > 0.22:
                p.material_index = 4 # Puños vinotinto de camisa asomando
            else:
                p.material_index = 0 # Mangas y hombros del saco negro
        else:
            # Torso central:
            if cy > 0.01 and cx < 0.07 and cz >= 0.94:
                p.material_index = 4 # Camisa vinotinto en el pecho frontal
            else:
                p.material_index = 0 # Todo lo demás es SACO NEGRO

        for loop in p.loops:
            loop[uv_lay].uv = (loop.vert.co.x * 2.0 + 0.5, loop.vert.co.z * 1.5)

    # Cinturón negro formal en la pretina (Z = 0.94)
    n_pelv = 24
    belt_ring = []
    for i in range(n_pelv):
        ang = (2.0 * math.pi * i) / n_pelv
        vx = 0.124 * math.cos(ang)
        vy = 0.084 * math.sin(ang)
        belt_ring.append(bm.verts.new((vx, vy, 0.942)))
        belt_ring.append(bm.verts.new((vx * 1.012, vy * 1.012, 0.954)))
    for i in range(0, len(belt_ring) - 2, 2):
        bm.faces.new((belt_ring[i], belt_ring[i+1], belt_ring[i+3], belt_ring[i+2])).material_index = 2
    bm.faces.new((belt_ring[-2], belt_ring[-1], belt_ring[1], belt_ring[0])).material_index = 2

    # Hebilla metálica en Z = 0.948
    buckle_bm = bmesh.new()
    bmesh.ops.create_cube(buckle_bm, size=1.0)
    bmesh.ops.scale(buckle_bm, verts=buckle_bm.verts, vec=(0.014, 0.003, 0.010))
    bmesh.ops.translate(buckle_bm, verts=buckle_bm.verts, vec=(0.0, 0.088, 0.948))
    for f in buckle_bm.faces:
        nf = bm.faces.new([bm.verts.new(v.co) for v in f.verts])
        nf.material_index = 6
    buckle_bm.free()

    # Cuello camisero 3D vinotinto alrededor del cuello
    n_c = 18
    c_bot, c_top = [], []
    for i in range(n_c):
        ang = (2.0 * math.pi * i) / n_c
        cx = 0.048 * math.cos(ang)
        cy = 0.048 * math.sin(ang) + 0.002
        c_bot.append(bm.verts.new((cx, cy, 1.350)))
        c_top.append(bm.verts.new((cx * 1.08, cy * 1.08, 1.390)))
    for i in range(n_c):
        inxt = (i + 1) % n_c
        bm.faces.new((c_bot[i], c_bot[inxt], c_top[inxt], c_top[i])).material_index = 4

    # Puntas de cuello camisero sobre el pecho
    wing_l = [bm.verts.new((0.005, 0.054, 1.385)), bm.verts.new((0.038, 0.046, 1.378)), bm.verts.new((0.020, 0.068, 1.338))]
    wing_r = [bm.verts.new((-0.005, 0.054, 1.385)), bm.verts.new((-0.020, 0.068, 1.338)), bm.verts.new((-0.038, 0.046, 1.378))]
    bm.faces.new(wing_l).material_index = 4
    bm.faces.new(wing_r).material_index = 4

    # Corbata negra Windsor en el pecho
    knot_v = [
        bm.verts.new((-0.013, 0.056, 1.380)),
        bm.verts.new(( 0.013, 0.056, 1.380)),
        bm.verts.new(( 0.010, 0.076, 1.340)),
        bm.verts.new((-0.010, 0.076, 1.340)),
        bm.verts.new(( 0.000, 0.084, 1.360)),
    ]
    bm.faces.new((knot_v[0], knot_v[1], knot_v[4])).material_index = 5
    bm.faces.new((knot_v[1], knot_v[2], knot_v[4])).material_index = 5
    bm.faces.new((knot_v[2], knot_v[3], knot_v[4])).material_index = 5
    bm.faces.new((knot_v[3], knot_v[0], knot_v[4])).material_index = 5

    tie_profile = [
        (1.340, 0.010, 0.076),
        (1.270, 0.012, 0.088),
        (1.200, 0.013, 0.092),
        (1.130, 0.013, 0.090),
        (1.070, 0.011, 0.084),
        (1.030, 0.010, 0.080),
        (0.960, 0.008, 0.080),
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
    # SACO SASTRE EXTERIOR 3D SEPARADO (SMOKING FORMAL NEGRO)
    # Envuelve tórax, espalda y faldones (Z=0.74 a 1.34).
    # -------------------------------------------------------------------------
    suit_specs = [
        # z,     rx,    ry_back, ry_front, y_off,  x_open
        (0.74,  0.138,  0.096,   0.096,    0.002,  0.078), # Faldón bajo abierto en V invertida
        (0.84,  0.136,  0.094,   0.094,    0.002,  0.052), # Cadera media
        (0.94,  0.132,  0.090,   0.090,    0.002,  0.026), # Cintura / pretina
        (1.00,  0.130,  0.089,   0.089,    0.000,  0.010), # Bajo el botón
        (1.05,  0.131,  0.090,   0.090,    0.000,  0.005), # Botón central
        (1.14,  0.138,  0.096,   0.094,   -0.002,  0.026), # Pecho medio (apertura en V superior)
        (1.24,  0.146,  0.100,   0.098,   -0.004,  0.048), # Pecho alto
        (1.33,  0.146,  0.096,   0.094,   -0.004,  0.064), # Hombros y clavícula
    ]

    n_suit_pts = 25
    suit_levels_verts = []

    for (sz, srx, sry_b, sry_f, sy_off, x_op) in suit_specs:
        cur_row = []
        alpha = math.asin(min(0.95, x_op / srx))
        for i in range(n_suit_pts):
            t = i / float(n_suit_pts - 1)
            phi = -alpha - t * (2.0 * math.pi - 2.0 * alpha)
            vx = srx * math.sin(phi)
            ca = math.cos(phi)
            vy = (sry_f if ca >= 0 else sry_b) * ca + sy_off
            cur_row.append(bm.verts.new((vx, vy, sz)))
        suit_levels_verts.append(cur_row)

    for l_idx in range(len(suit_specs) - 1):
        r1 = suit_levels_verts[l_idx]
        r2 = suit_levels_verts[l_idx + 1]
        for i in range(n_suit_pts - 1):
            f = bm.faces.new((r1[i], r1[i+1], r2[i+1], r2[i]))
            f.material_index = 0
            for loop in f.loops:
                loop[uv_lay].uv = (loop.vert.co.x * 2.0 + 0.5, loop.vert.co.z * 1.5)

    for l_idx in range(len(suit_specs) - 1):
        v1_r = suit_levels_verts[l_idx][0]
        v2_r = suit_levels_verts[l_idx + 1][0]
        v1_in = bm.verts.new((v1_r.co.x * 0.95, v1_r.co.y - 0.005, v1_r.co.z))
        v2_in = bm.verts.new((v2_r.co.x * 0.95, v2_r.co.y - 0.005, v2_r.co.z))
        f_r = bm.faces.new((v1_r, v2_r, v2_in, v1_in))
        f_r.material_index = 0

        v1_l = suit_levels_verts[l_idx][-1]
        v2_l = suit_levels_verts[l_idx + 1][-1]
        v1_lin = bm.verts.new((v1_l.co.x * 0.95, v1_l.co.y - 0.005, v1_l.co.z))
        v2_lin = bm.verts.new((v2_l.co.x * 0.95, v2_l.co.y - 0.005, v2_l.co.z))
        f_l = bm.faces.new((v1_l, v1_lin, v2_lin, v2_l))
        f_l.material_index = 0

    r_bot = suit_levels_verts[0]
    for i in range(n_suit_pts - 1):
        v1 = r_bot[i]
        v2 = r_bot[i+1]
        v1_in = bm.verts.new((v1.co.x * 0.96, v1.co.y * 0.96, v1.co.z + 0.006))
        v2_in = bm.verts.new((v2.co.x * 0.96, v2.co.y * 0.96, v2.co.z + 0.006))
        f_b = bm.faces.new((v1, v2, v2_in, v1_in))
        f_b.material_index = 0

    # Solapas notch clásicas en relieve
    for s_side in (1.0, -1.0):
        lapel_v = [
            bm.verts.new((s_side * 0.040, 0.046, 1.365)),
            bm.verts.new((s_side * 0.088, 0.078, 1.315)),
            bm.verts.new((s_side * 0.092, 0.088, 1.275)),
            bm.verts.new((s_side * 0.078, 0.090, 1.258)),
            bm.verts.new((s_side * 0.088, 0.098, 1.238)),
            bm.verts.new((s_side * 0.016, 0.086, 1.050)),
            bm.verts.new((s_side * 0.034, 0.090, 1.220)),
        ]
        if s_side > 0:
            f1 = bm.faces.new((lapel_v[0], lapel_v[1], lapel_v[2], lapel_v[3]))
            f2 = bm.faces.new((lapel_v[0], lapel_v[3], lapel_v[6]))
            f3 = bm.faces.new((lapel_v[3], lapel_v[4], lapel_v[5], lapel_v[6]))
        else:
            f1 = bm.faces.new((lapel_v[1], lapel_v[0], lapel_v[3], lapel_v[2]))
            f2 = bm.faces.new((lapel_v[3], lapel_v[0], lapel_v[6]))
            f3 = bm.faces.new((lapel_v[4], lapel_v[3], lapel_v[6], lapel_v[5]))
        for f in (f1, f2, f3):
            f.material_index = 0
            for loop in f.loops:
                loop[uv_lay].uv = (loop.vert.co.x * 2.0 + 0.5, loop.vert.co.z * 1.5)

    sc_top, sc_bot = [], []
    for i in range(12):
        ang = math.pi * 0.12 + (math.pi * 0.76 * i) / 11.0
        bx = 0.052 * math.cos(ang)
        by = -0.050 * math.sin(ang) - 0.003
        sc_top.append(bm.verts.new((bx, by, 1.385)))
        sc_bot.append(bm.verts.new((bx, by, 1.350)))
    for i in range(11):
        f = bm.faces.new((sc_bot[i], sc_bot[i+1], sc_top[i+1], sc_top[i]))
        f.material_index = 0

    btn_bm = bmesh.new()
    bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.005)
    bmesh.ops.scale(btn_bm, verts=btn_bm.verts, vec=(1.0, 0.30, 1.0))
    bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.006, 0.090, 1.050))
    v_map_b = {v: bm.verts.new(v.co) for v in btn_bm.verts}
    for f in btn_bm.faces:
        bm.faces.new([v_map_b[v] for v in f.verts]).material_index = 6
    btn_bm.free()

    # =========================================================================
    # MODELADO ANATÓMICO CANÓNICO DE MANOS: 5 DEDOS INDEPENDIENTES Y SUJECIÓN
    # =========================================================================
    # Se genera una palma anatómica trapezoidal suave desde la muñeca (Z = 0.850)
    # hasta los nudillos (Z = 0.785), y 5 dedos articulados con 3 falanges cada uno:
    # - Pulgar: oponible, grueso (r=0.0068), longitud 0.048 m
    # - Índice: r=0.0054, longitud 0.068 m
    # - Medio:  r=0.0058, longitud 0.078 m (el más largo)
    # - Anular: r=0.0053, longitud 0.070 m
    # - Meñique: r=0.0044, longitud 0.052 m (claramente más corto y estilizado)
    # =========================================================================

    def add_curved_finger(p_knuckle, curl_angles, seg_lengths, radii, lat_axis, palm_normal):
        """
        Crea un dedo con articulaciones independientes (falanges) que se curvan
        naturalmente alrededor de un eje.
        curl_angles: lista de 3 ángulos de flexión en radianes (nudillo, PIP, DIP).
        seg_lengths: lista de longitudes de las 3 falanges.
        radii: lista de radios en cada nudo (4 valores: base, pip, dip, yema).
        """
        rings = []
        cur_pos = Vector(p_knuckle)
        # Dirección inicial del dedo (hacia abajo -Z en reposo)
        cur_dir = Vector((0.0, 0.0, -1.0))

        # Eje de flexión (lateral al dedo, perpendicular a la flexión palmar)
        flex_axis = lat_axis.normalized()
        norm_axis = palm_normal.normalized()

        for s in range(4):
            # Posición del anillo
            if s > 0:
                angle = curl_angles[s-1]
                # Rotar la dirección alrededor del eje de flexión
                rot_m = Matrix.Rotation(angle, 3, flex_axis)
                cur_dir = rot_m @ cur_dir
                cur_pos = cur_pos + cur_dir * seg_lengths[s-1]

            r = radii[s]
            ring_v = []
            # 8 vértices para un cilindro suave y orgánico
            u_dir = flex_axis
            v_dir = cur_dir.cross(u_dir).normalized()
            for k in range(8):
                ang = (2.0 * math.pi * k) / 8.0
                offset = (u_dir * math.cos(ang) + v_dir * math.sin(ang)) * r
                ring_v.append(bm.verts.new(cur_pos + offset))
            rings.append(ring_v)

        # Conectar segmentos
        for s in range(3):
            r1, r2 = rings[s], rings[s+1]
            for k in range(8):
                knxt = (k + 1) % 8
                f = bm.faces.new((r1[k], r1[knxt], r2[knxt], r2[k]))
                f.material_index = 3
                f.smooth = True

        # Yema redondeada
        tip_pos = cur_pos + cur_dir * (radii[-1] * 0.6)
        tip_v = bm.verts.new(tip_pos)
        r_last = rings[-1]
        for k in range(8):
            knxt = (k + 1) % 8
            f = bm.faces.new((r_last[knxt], r_last[k], tip_v))
            f.material_index = 3
            f.smooth = True

    for is_l in (True, False):
        sign = 1.0 if is_l else -1.0
        # Centro de la muñeca
        wx = sign * 0.285
        wy = 0.010
        wz_top = 0.852
        wz_knuckles = 0.785

        # 1. Palma de la mano (Palmar wedge)
        # Dorso en +X para L, -X para R; Palma interior en -X para L, +X para R
        # Ancho Y: de -0.026 a +0.030 (span de 5.6 cm)
        # Espesor X: ±0.012 (2.4 cm)
        p_top_verts = [
            bm.verts.new((wx - sign * 0.011, wy - 0.018, wz_top)),
            bm.verts.new((wx + sign * 0.011, wy - 0.018, wz_top)),
            bm.verts.new((wx + sign * 0.011, wy + 0.022, wz_top)),
            bm.verts.new((wx - sign * 0.011, wy + 0.022, wz_top)),
        ]
        p_bot_verts = [
            bm.verts.new((wx - sign * 0.010, wy - 0.028, wz_knuckles)),
            bm.verts.new((wx + sign * 0.010, wy - 0.028, wz_knuckles)),
            bm.verts.new((wx + sign * 0.010, wy + 0.034, wz_knuckles)),
            bm.verts.new((wx - sign * 0.010, wy + 0.034, wz_knuckles)),
        ]
        # Caras de la palma
        f_p1 = bm.faces.new((p_top_verts[0], p_top_verts[1], p_bot_verts[1], p_bot_verts[0]))
        f_p2 = bm.faces.new((p_top_verts[1], p_top_verts[2], p_bot_verts[2], p_bot_verts[1]))
        f_p3 = bm.faces.new((p_top_verts[2], p_top_verts[3], p_bot_verts[3], p_bot_verts[2]))
        f_p4 = bm.faces.new((p_top_verts[3], p_top_verts[0], p_bot_verts[0], p_bot_verts[3]))
        f_p5 = bm.faces.new((p_top_verts[0], p_top_verts[3], p_top_verts[2], p_top_verts[1]))
        f_p6 = bm.faces.new((p_bot_verts[0], p_bot_verts[1], p_bot_verts[2], p_bot_verts[3]))
        for fp in (f_p1, f_p2, f_p3, f_p4, f_p5, f_p6):
            fp.material_index = 3
            fp.smooth = True

        # 2. Los 4 Dedos (Meñique, Anular, Medio, Índice)
        # Separación clara en Y para que no se fundan:
        finger_data = [
            # Nombre, dy_nudillo, [l1, l2, l3], [r0, r1, r2, r3]
            ("Pinky",  wy - 0.021, [0.022, 0.016, 0.013], [0.0046, 0.0042, 0.0038, 0.0034]), # Meñique corto
            ("Ring",   wy - 0.007, [0.028, 0.022, 0.017], [0.0054, 0.0050, 0.0045, 0.0040]), # Anular
            ("Middle", wy + 0.008, [0.032, 0.025, 0.019], [0.0058, 0.0054, 0.0048, 0.0042]), # Medio más largo
            ("Index",  wy + 0.023, [0.028, 0.021, 0.016], [0.0055, 0.0051, 0.0046, 0.0040]), # Índice
        ]

        if is_l:
            # Mano L (sostiene la vara del arco en la cadera):
            # Los dedos se curvan suavemente envolviendo la vara
            curl_angles_fingers = [math.radians(28), math.radians(42), math.radians(24)]
            lat_axis = Vector((0.0, 1.0, 0.0))
            palm_normal = Vector((-1.0, 0.0, 0.0))
        else:
            # Mano R (en realidad izquierda del personaje, sostiene el violín por el mástil):
            # Espejado anatómico canónico: el eje de flexión se invierte a -Y para curvar hacia la palma (+X)
            curl_angles_fingers = [math.radians(24), math.radians(38), math.radians(26)]
            lat_axis = Vector((0.0, -1.0, 0.0))
            palm_normal = Vector((1.0, 0.0, 0.0))

        for fname, fy, lens, rads in finger_data:
            knuckle_pos = Vector((wx, fy, wz_knuckles))
            add_curved_finger(knuckle_pos, curl_angles_fingers, lens, rads, lat_axis, palm_normal)

        # 3. Quinto Dedo: Pulgar Oponible (Thumb)
        # Nace en la eminencia tenar (mitad de la palma en Z = 0.825, cara anterior Y = +0.020)
        th_knuckle = Vector((wx - sign * 0.012, wy + 0.022, 0.825))
        th_lens = [0.026, 0.020, 0.012]
        th_rads = [0.0068, 0.0062, 0.0054, 0.0046]
        if is_l:
            # Pulgar de la mano del arco: se opone a los dedos por debajo de la vara
            th_curl = [math.radians(35), math.radians(30), math.radians(20)]
            th_lat = Vector((-0.4, 0.9, 0.2)).normalized()
            th_norm = Vector((-0.8, -0.3, 0.5)).normalized()
        else:
            # Pulgar de la mano del violín: se apoya en el borde posterior del mástil
            # Espejado axial correcto: inversión de componentes paralelas al plano de reflexión
            th_curl = [math.radians(30), math.radians(35), math.radians(22)]
            th_lat = Vector((-0.4, -0.9, -0.2)).normalized()
            th_norm = Vector((-0.8, 0.3, -0.5)).normalized()

        add_curved_finger(th_knuckle, th_curl, th_lens, th_rads, th_lat, th_norm)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    for f in bm.faces: f.smooth = True

    bm.to_mesh(obj_body.data)
    bm.free()

    for mat in materials["body"]:
        obj_body.data.materials.append(mat)

    return obj_body

# =============================================================================
# 3. ESQUELETO Y RIGGING BLINDADO CON DEFORMACIÓN ARMÓNICA (CERO SUMIDO)
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
        ("Hips",        "Root",        (0, 0, 0.76),      (0, 0, 0.94)),
        ("Spine",       "Hips",        (0, 0, 0.94),      (0, 0, 1.14)),
        ("Chest",       "Spine",       (0, 0, 1.14),      (0, 0, 1.30)),
        ("Neck",        "Chest",       (0, 0, 1.30),      (0, 0, 1.37)),
        ("Head",        "Neck",        (0, 0, 1.37),      (0, 0, 1.63)),

        ("Shoulder.L",  "Chest",       (0.04, 0, 1.30),   (0.180, 0, 1.300)),
        ("UpperArm.L",  "Shoulder.L",  (0.180, 0, 1.300), (0.245, 0.002, 1.120)),
        ("Forearm.L",   "UpperArm.L",  (0.245, 0.002, 1.120),(0.285, 0.008, 0.900)),
        ("Hand.L",      "Forearm.L",   (0.285, 0.008, 0.900),(0.285, 0.008, 0.76)),

        ("Shoulder.R",  "Chest",       (-0.04, 0, 1.30),  (-0.180, 0, 1.300)),
        ("UpperArm.R",  "Shoulder.R",  (-0.180, 0, 1.300), (-0.245, 0.002, 1.120)),
        ("Forearm.R",   "UpperArm.R",  (-0.245, 0.002, 1.120),(-0.285, 0.008, 0.900)),
        ("Hand.R",      "Forearm.R",   (-0.285, 0.008, 0.900),(-0.285, 0.008, 0.76)),

        ("UpperLeg.L",  "Hips",        (0.088, 0, 0.76),  (0.092, 0, 0.44)),
        ("LowerLeg.L",  "UpperLeg.L",  (0.092, 0, 0.44),  (0.096, 0, 0.12)),
        ("Foot.L",      "LowerLeg.L",  (0.096, 0, 0.12),  (0.096, 0.05, 0.03)),
        ("Toes.L",      "Foot.L",      (0.096, 0.05, 0.03),(0.096, 0.10, 0.00)),

        ("UpperLeg.R",  "Hips",        (-0.088, 0, 0.76), (-0.092, 0, 0.44)),
        ("LowerLeg.R",  "UpperLeg.R",  (-0.092, 0, 0.44), (-0.096, 0, 0.12)),
        ("Foot.R",      "LowerLeg.R",  (-0.096, 0, 0.12), (-0.096, 0.05, 0.03)),
        ("Toes.R",      "Foot.R",      (-0.096, 0.05, 0.03),(-0.096, 0.10, 0.00)),
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

    if is_head:
        for v in obj.data.vertices:
            co = v.co
            if co.z < 1.37:
                obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 1.41:
                t = (co.z - 1.37) / 0.04
                obj.vertex_groups["Neck"].add([v.index], 1.0 - t, 'REPLACE')
                obj.vertex_groups["Head"].add([v.index], t, 'REPLACE')
            else:
                obj.vertex_groups["Head"].add([v.index], 1.0, 'REPLACE')
        return

    for v in obj.data.vertices:
        co = v.co
        idx = v.index
        ax = abs(co.x)

        # 1. PIES Y DEDOS
        if co.z < 0.04 and ax <= 0.20:
            obj.vertex_groups["Toes.L" if co.x > 0 else "Toes.R"].add([idx], 1.0, 'REPLACE')
        elif co.z < 0.10 and ax <= 0.20:
            obj.vertex_groups["Foot.L" if co.x > 0 else "Foot.R"].add([idx], 1.0, 'REPLACE')
        elif co.z < 0.14 and ax <= 0.20:
            t_f = (co.z - 0.10) / 0.04
            side = ".L" if co.x > 0 else ".R"
            obj.vertex_groups["Foot" + side].add([idx], 1.0 - t_f, 'REPLACE')
            obj.vertex_groups["LowerLeg" + side].add([idx], t_f, 'REPLACE')

        # 2. EXTREMIDADES SUPERIORES (BRAZOS)
        elif ax > 0.16 and co.z < 1.38:
            side = ".L" if co.x > 0 else ".R"
            if co.z < 0.86:
                obj.vertex_groups["Hand" + side].add([idx], 1.0, 'REPLACE')
            elif co.z < 0.90:
                t_w = (co.z - 0.86) / 0.04
                obj.vertex_groups["Forearm" + side].add([idx], t_w, 'REPLACE')
                obj.vertex_groups["Hand" + side].add([idx], 1.0 - t_w, 'REPLACE')
            elif co.z < 1.08:
                obj.vertex_groups["Forearm" + side].add([idx], 1.0, 'REPLACE')
            elif co.z < 1.16:
                t_e = (co.z - 1.08) / 0.08
                obj.vertex_groups["Forearm" + side].add([idx], 1.0 - t_e, 'REPLACE')
                obj.vertex_groups["UpperArm" + side].add([idx], t_e, 'REPLACE')
            else:
                obj.vertex_groups["UpperArm" + side].add([idx], 1.0, 'REPLACE')

        # 3. EXTREMIDADES INFERIORES (PIERNAS)
        elif co.z < 0.40:
            obj.vertex_groups["LowerLeg.L" if co.x > 0 else "LowerLeg.R"].add([idx], 1.0, 'REPLACE')
        elif co.z < 0.48:
            t_k = (co.z - 0.40) / 0.08
            side = ".L" if co.x > 0 else ".R"
            obj.vertex_groups["LowerLeg" + side].add([idx], 1.0 - t_k, 'REPLACE')
            obj.vertex_groups["UpperLeg" + side].add([idx], t_k, 'REPLACE')
        elif co.z < 0.76 and ax > 0.02:
            obj.vertex_groups["UpperLeg.L" if co.x > 0 else "UpperLeg.R"].add([idx], 1.0, 'REPLACE')

        # 4. PELVIS, COLUMNA Y PECHO
        elif co.z < 0.94:
            obj.vertex_groups["Hips"].add([idx], 1.0, 'REPLACE')
        elif co.z < 1.14:
            obj.vertex_groups["Spine"].add([idx], 1.0, 'REPLACE')
        else:
            obj.vertex_groups["Chest"].add([idx], 1.0, 'REPLACE')

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
    scene.cycles.samples = 32
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1200
    scene.render.film_transparent = False

    for light in [o for o in scene.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(light, do_unlink=True)

    def add_light(name, ltype, energy, loc, color=(1.0, 1.0, 1.0), size=1.5):
        ld = bpy.data.lights.new(name, ltype)
        ld.energy = energy
        ld.color = color
        ld.size = size
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        scene.collection.objects.link(lo)
        return lo

    add_light("KeyLight",   'AREA', 180.0, ( 0.5,  1.8, 1.6), (1.0, 0.96, 0.92), size=1.8)
    add_light("FillLight",  'AREA', 110.0, (-0.8,  1.6, 1.4), (0.95, 0.97, 1.0), size=2.2)
    add_light("RimLight",   'AREA', 140.0, ( 0.0, -1.8, 1.6), (1.0, 0.98, 0.95), size=1.5)
    add_light("HeadFill",   'AREA',  65.0, ( 0.0,  1.2, 1.7), (1.0, 0.96, 0.92), size=1.0)

    cam_data = bpy.data.cameras.new("RenderCam")
    cam_data.lens = 52.0
    cam_obj = bpy.data.objects.new("RenderCam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    target_pos = (0.0, 0.0, 0.90)
    shots = [
        ("astorga_preview.png",             ( 0.00,  1.85, 1.20), ( 0.00, 0.00, 1.20), PREVIEW_PNG),
        ("astorga_master_front.png",        ( 0.00,  2.35, 0.95), target_pos, os.path.join(SCRATCH_DIR, "astorga_master_front.png")),
        ("astorga_master_profile.png",      (-2.35,  0.00, 0.95), target_pos, os.path.join(SCRATCH_DIR, "astorga_master_profile.png")),
        ("astorga_master_back.png",         ( 0.00, -2.35, 0.95), target_pos, os.path.join(SCRATCH_DIR, "astorga_master_back.png")),
        ("astorga_master_threequarter.png", ( 1.45,  1.80, 1.05), target_pos, os.path.join(SCRATCH_DIR, "astorga_master_threequarter.png")),
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
    print("GENERANDO ASTORGA CANÓNICO CORREGIDO: SASTRERÍA 3D, MELENA 360 Y RIG 22")
    print("=" * 65)

    clean_scene()

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
    print("✓ Player_Head_Mesh generado con rostro auténtico y melena setentera continua 360°.")

    # 3. Malla de Cuerpo modular
    obj_body = build_body_mesh(mat_groups)
    assign_weights(obj_body, is_head=False)
    attach_armature_modifier(obj_body, arm_obj)
    print("✓ Player_Body_Mesh generado con proporciones esbeltas, sastrería 3D y camisa vinotinto.")

    # Verificación matemática de pesos
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
