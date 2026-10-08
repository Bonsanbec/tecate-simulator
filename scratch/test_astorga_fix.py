"""
Test de corrección integral de Astorga (v5 - Hombros 100% Sastre Negro):
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
    for obj in list(bpy.data.objects): bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes): bpy.data.meshes.remove(mesh, do_unlink=True)
    for mat in list(bpy.data.materials): bpy.data.materials.remove(mat, do_unlink=True)
    for arm in list(bpy.data.armatures): bpy.data.armatures.remove(arm, do_unlink=True)

def setup_pbr_material(name, diffuse_path=None, normal_path=None, base_color=(1,1,1,1), roughness=0.5, metallic=0.0, specular=0.5):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    bsdf.inputs['Base Color'].default_value = base_color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = specular

    if diffuse_path and os.path.exists(diffuse_path):
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(diffuse_path)
        links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])

    if normal_path and os.path.exists(normal_path):
        norm_img = nodes.new('ShaderNodeTexImage')
        img_norm = bpy.data.images.load(normal_path)
        img_norm.colorspace_settings.name = 'Non-Color'
        norm_img.image = img_norm
        norm_map = nodes.new('ShaderNodeNormalMap')
        norm_map.inputs['Strength'].default_value = 0.85
        links.new(norm_img.outputs['Color'], norm_map.inputs['Color'])
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
                                   base_color=(0.045, 0.035, 0.030, 1.0), roughness=0.70, specular=0.35),
        "suit": setup_pbr_material("Mat_Astorga_Suit",
                                   os.path.join(TEXTURES_DIR, "astorga_suit_diffuse.png"),
                                   os.path.join(TEXTURES_DIR, "astorga_suit_normal.png"),
                                   base_color=(0.045, 0.048, 0.055, 1.0), roughness=0.62),
        "shirt": setup_pbr_material("Mat_Astorga_Shirt",
                                    os.path.join(TEXTURES_DIR, "astorga_shirt_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "astorga_shirt_normal.png"),
                                    base_color=(0.280, 0.045, 0.065, 1.0), roughness=0.55),
        "tie": setup_pbr_material("Mat_Astorga_Tie",
                                  os.path.join(TEXTURES_DIR, "astorga_tie_diffuse.png"),
                                  os.path.join(TEXTURES_DIR, "astorga_tie_normal.png"),
                                  base_color=(0.025, 0.020, 0.022, 1.0), roughness=0.35, specular=0.55),
        "pants": setup_pbr_material("Mat_Astorga_Pants",
                                    os.path.join(TEXTURES_DIR, "astorga_pants_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "astorga_pants_normal.png"),
                                    base_color=(0.045, 0.048, 0.055, 1.0), roughness=0.65),
        "shoes": setup_pbr_material("Mat_Astorga_Shoes",
                                    os.path.join(TEXTURES_DIR, "astorga_shoes_diffuse.png"),
                                    os.path.join(TEXTURES_DIR, "astorga_shoes_normal.png"),
                                    base_color=(0.020, 0.020, 0.025, 1.0), roughness=0.20, specular=0.65),
        "buttons": setup_pbr_material("Mat_Astorga_Buttons",
                                      None, None,
                                      base_color=(0.02, 0.02, 0.02, 1.0), roughness=0.20, metallic=0.40),
    }

# =============================================================================
# 1. CABEZA Y MELENA 360° CONTINUA
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
        (1.370,  0.040, 0.040,    0.042,   -0.002,   False), # 0: Base cuello
        (1.390,  0.042, 0.041,    0.045,   -0.002,   False), # 1: Cuello medio
        (1.410,  0.047, 0.044,    0.051,    0.000,   True),  # 2: Ángulo submandibular
        (1.426,  0.055, 0.061,    0.064,    0.004,   True),  # 3: Mentón firme
        (1.442,  0.059, 0.061,    0.070,    0.003,   True),  # 4: Surco mentolabial
        (1.454,  0.061, 0.063,    0.077,    0.003,   True),  # 5: Labio inferior
        (1.464,  0.063, 0.062,    0.081,    0.002,   True),  # 6: Hendidura labial
        (1.474,  0.065, 0.065,    0.085,    0.002,   True),  # 7: Labio superior
        (1.488,  0.068, 0.064,    0.087,    0.001,   True),  # 8: Base nasal / Filtrum
        (1.500,  0.070, 0.072,    0.088,    0.000,   True),  # 9: Punta nasal recta
        (1.510,  0.072, 0.066,    0.088,    0.000,   True),  # 10: Ojos y puente nasal
        (1.526,  0.073, 0.069,    0.087,   -0.002,   True),  # 11: Pómulos y cejas
        (1.544,  0.072, 0.066,    0.085,   -0.004,   True),  # 12: Sienes y frente baja
        (1.560,  0.070, 0.061,    0.081,   -0.006,   True),  # 13: Frente media
        (1.576,  0.066, 0.053,    0.075,   -0.008,   False), # 14: Bóveda baja
        (1.592,  0.056, 0.042,    0.065,   -0.010,   False), # 15: Bóveda media
        (1.608,  0.038, 0.028,    0.043,   -0.012,   False), # 16: Coronilla
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
            c_med = f.calc_center_median()
            if c_med.z > 1.56 or (c_med.z > 1.52 and c_med.y < 0.025):
                f.material_index = 2 # Cabello oscuro
            else:
                f.material_index = 0 # Piel

            for loop in f.loops:
                loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

    crown_center = bm.verts.new((0.0, -0.012, 1.616))
    r_top = rings[-1]
    for i in range(n_ring):
        inxt = (i + 1) % n_ring
        f = bm.faces.new((r_top[inxt], r_top[i], crown_center))
        f.material_index = 2
        for loop in f.loops:
            loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

    # Ojos y párpados 3D
    eye_radius = 0.0125
    eye_z = 1.510
    eye_x = 0.033
    eye_y = 0.063
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

    # Melena setentera con volumen lateral auténtico
    hair_mesh_profile = [
        # z,     rx,    ry_front, ry_back, y_off,  is_closed
        (1.370, 0.080, 0.060, 0.096, -0.024, False), # Caída cuello
        (1.410, 0.088, 0.070, 0.100, -0.020, False), # Mandíbula
        (1.450, 0.098, 0.080, 0.105, -0.016, False), # Volumen orejas/pómulos
        (1.490, 0.100, 0.085, 0.107, -0.014, False), # Sienes
        (1.530, 0.098, 0.085, 0.105, -0.012, False), # Frente baja
        (1.558, 0.090, 0.078, 0.098, -0.010, True),  # Flequillo suave continuo
        (1.588, 0.077, 0.066, 0.084, -0.010, True),  # Bóveda media
        (1.618, 0.048, 0.040, 0.052, -0.010, True),  # Cúspide
    ]

    n_h = 28
    h_rings = []
    for l_idx, (hz, hrx, hry_f, hry_b, hy_off, is_c) in enumerate(hair_mesh_profile):
        cur_ring = []
        for i in range(n_h):
            ang = (2.0 * math.pi * i) / n_h
            ca = math.cos(ang)
            sa = math.sin(ang)

            if not is_c and sa > 0.38:
                face_t = (sa - 0.38) / 0.62
                wave = 0.003 * math.sin(ang * 4.0 + l_idx * 0.8)
                vx = (hrx + wave) * ca
                vy = (hry_f * (0.92 - 0.32 * face_t)) + hy_off
                vz = hz + 0.002 * math.sin(ang * 3.0)
            else:
                wave = 0.005 * math.sin(ang * 3.0 + l_idx * 0.6) + 0.002 * math.cos(ang * 2.0)
                vx = (hrx + wave) * ca
                vy = ((hry_f if sa >= 0 else hry_b) + wave) * sa + hy_off
                vz = hz + 0.002 * math.sin(ang * 2.0)

            cur_ring.append(bm.verts.new((vx, vy, vz)))
        h_rings.append(cur_ring)

    for l_idx in range(len(hair_mesh_profile) - 1):
        r1 = h_rings[l_idx]
        r2 = h_rings[l_idx + 1]
        for i in range(n_h):
            inxt = (i + 1) % n_h
            is_face_gap = (l_idx < 4) and (math.sin((2.0 * math.pi * i) / n_h) > 0.42)
            if not is_face_gap:
                f = bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))
                f.material_index = 2
                for loop in f.loops:
                    loop[uv_lay].uv = (loop.vert.co.x * 2.5 + 0.5, loop.vert.co.z * 2.0)

    hair_top = bm.verts.new((0.0, -0.010, 1.628))
    r_last = h_rings[-1]
    for i in range(n_h):
        inxt = (i + 1) % n_h
        f = bm.faces.new((r_last[inxt], r_last[i], hair_top))
        f.material_index = 2
        for loop in f.loops:
            loop[uv_lay].uv = (loop.vert.co.x * 2.5 + 0.5, loop.vert.co.z * 2.0)

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

    # Grafo anatómico esbelto y proporcionado de Astorga (1.65 m)
    nodes = [
        # Tronco
        (0.00,  0.000, 0.78, 0.122, 0.084), # 0: Crotch anatómico
        (0.00,  0.002, 0.90, 0.120, 0.080), # 1: Caderas / Cintura baja
        (0.00,  0.004, 1.02, 0.116, 0.076), # 2: Cintura entallada
        (0.00, -0.004, 1.14, 0.124, 0.084), # 3: Tórax / costillas
        (0.00, -0.006, 1.25, 0.134, 0.090), # 4: Pectorales y espalda
        (0.00, -0.003, 1.33, 0.124, 0.082), # 5: Clavículas / hombros
        (0.00,  0.002, 1.37, 0.044, 0.044), # 6: Base cuello camisero

        # Brazos sastre continuos (cero desgarro)
        ( 0.05, -0.003, 1.33, 0.054, 0.054), # 7
        ( 0.174,-0.003, 1.30, 0.046, 0.046), # 8: Hombro L
        ( 0.240, 0.002, 1.12, 0.036, 0.036), # 9: Codo L
        ( 0.282, 0.008, 0.90, 0.026, 0.024), # 10: Manga puño L

        (-0.05, -0.003, 1.33, 0.054, 0.054), # 11
        (-0.174,-0.003, 1.30, 0.046, 0.046), # 12: Hombro R
        (-0.240, 0.002, 1.12, 0.036, 0.036), # 13: Codo R
        (-0.282, 0.008, 0.90, 0.026, 0.024), # 14: Manga puño R

        # Piernas con pantalón formal de proporción real (1.65 m)
        ( 0.068, 0.002, 0.78, 0.064, 0.064), # 15: Cadera sup L
        ( 0.068, 0.002, 0.62, 0.056, 0.056), # 16: Muslo medio L
        ( 0.068, 0.000, 0.46, 0.048, 0.048), # 17: Rodilla L
        ( 0.068, 0.000, 0.30, 0.042, 0.042), # 18: Pantorrilla L
        ( 0.068, 0.002, 0.12, 0.036, 0.036), # 19: Tobillo L
        ( 0.068, 0.050, 0.03, 0.040, 0.095), # 20: Zapato L

        (-0.068, 0.002, 0.78, 0.064, 0.064), # 21: Cadera sup R
        (-0.068, 0.002, 0.62, 0.056, 0.056), # 22: Muslo medio R
        (-0.068, 0.000, 0.46, 0.048, 0.048), # 23: Rodilla R
        (-0.068, 0.000, 0.30, 0.042, 0.042), # 24: Pantorrilla R
        (-0.068, 0.002, 0.12, 0.036, 0.036), # 25: Tobillo R
        (-0.068, 0.050, 0.03, 0.040, 0.095), # 26: Zapato R

        # Muñecas y palmas continuas
        ( 0.282,  0.010, 0.865, 0.019, 0.015), # 27: Muñeca L
        ( 0.282,  0.010, 0.820, 0.024, 0.013), # 28: Palma L
        (-0.282,  0.010, 0.865, 0.019, 0.015), # 29: Muñeca R
        (-0.282,  0.010, 0.820, 0.024, 0.013), # 30: Palma R
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

    # Mapeo de materiales en el cuerpo base:
    # 0: suit, 1: pants, 2: shoes, 3: skin, 4: shirt, 5: tie, 6: buttons
    for p in bm.faces:
        c_median = p.calc_center_median()
        cz = c_median.z
        cx = abs(c_median.x)

        if cz < 0.12:
            p.material_index = 2 # Zapatos de vestir
        elif cz < 0.94 and cx < 0.18:
            p.material_index = 1 # Pantalón sastre
        elif cx > 0.14 or (cz > 1.25 and cx > 0.08):
            # Mangas, hombros y deltoides: 100% Saco formal
            if cz < 0.85 and cx > 0.22:
                p.material_index = 3 # Manos y muñecas de piel
            elif cz < 0.88 and cx > 0.22:
                p.material_index = 4 # Puños vinotinto de camisa
            else:
                p.material_index = 0 # Mangas y hombros del saco
        else:
            p.material_index = 4 # Camisa vinotinto continua en torso central

        for loop in p.loops:
            loop[uv_lay].uv = (loop.vert.co.x * 2.0 + 0.5, loop.vert.co.z * 1.5)

    # Cinturón negro en Z = 0.94
    n_pelv = 24
    belt_ring = []
    for i in range(n_pelv):
        ang = (2.0 * math.pi * i) / n_pelv
        vx = 0.118 * math.cos(ang)
        vy = 0.078 * math.sin(ang)
        belt_ring.append(bm.verts.new((vx, vy, 0.945)))
        belt_ring.append(bm.verts.new((vx * 1.01, vy * 1.01, 0.955)))
    for i in range(0, len(belt_ring) - 2, 2):
        bm.faces.new((belt_ring[i], belt_ring[i+1], belt_ring[i+3], belt_ring[i+2])).material_index = 2
    bm.faces.new((belt_ring[-2], belt_ring[-1], belt_ring[1], belt_ring[0])).material_index = 2

    # Cuello camisero 3D vinotinto
    n_c = 18
    c_bot, c_top = [], []
    for i in range(n_c):
        ang = (2.0 * math.pi * i) / n_c
        cx = 0.046 * math.cos(ang)
        cy = 0.046 * math.sin(ang) + 0.002
        c_bot.append(bm.verts.new((cx, cy, 1.355)))
        c_top.append(bm.verts.new((cx * 1.08, cy * 1.08, 1.395)))
    for i in range(n_c):
        inxt = (i + 1) % n_c
        bm.faces.new((c_bot[i], c_bot[inxt], c_top[inxt], c_top[i])).material_index = 4

    wing_l = [bm.verts.new((0.005, 0.054, 1.392)), bm.verts.new((0.038, 0.046, 1.384)), bm.verts.new((0.020, 0.068, 1.344))]
    wing_r = [bm.verts.new((-0.005, 0.054, 1.392)), bm.verts.new((-0.020, 0.068, 1.344)), bm.verts.new((-0.038, 0.046, 1.384))]
    bm.faces.new(wing_l).material_index = 4
    bm.faces.new(wing_r).material_index = 4

    # Corbata negra Windsor en el pecho
    knot_v = [
        bm.verts.new((-0.013, 0.056, 1.385)),
        bm.verts.new(( 0.013, 0.056, 1.385)),
        bm.verts.new(( 0.010, 0.076, 1.345)),
        bm.verts.new((-0.010, 0.076, 1.345)),
        bm.verts.new(( 0.000, 0.084, 1.365)),
    ]
    bm.faces.new((knot_v[0], knot_v[1], knot_v[4])).material_index = 5
    bm.faces.new((knot_v[1], knot_v[2], knot_v[4])).material_index = 5
    bm.faces.new((knot_v[2], knot_v[3], knot_v[4])).material_index = 5
    bm.faces.new((knot_v[3], knot_v[0], knot_v[4])).material_index = 5

    tie_profile = [
        (1.345, 0.010, 0.076),
        (1.275, 0.012, 0.088),
        (1.205, 0.013, 0.092),
        (1.135, 0.013, 0.090),
        (1.075, 0.011, 0.084),
        (1.035, 0.010, 0.080),
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
    # SACO SASTRE EXTERIOR 3D SEPARADO (SMOKING FORMAL)
    # Envuelve el torso y faldones (Z=0.76 a 1.32), abre en V arriba y V invertida abajo
    # -------------------------------------------------------------------------
    suit_specs = [
        # z,     rx,    ry_back, ry_front, y_off,  x_open
        (0.76,  0.134,  0.092,   0.092,    0.002,  0.078), # Faldón bajo abierto en V invertida
        (0.84,  0.132,  0.090,   0.090,    0.002,  0.055), # Cadera media
        (0.94,  0.128,  0.086,   0.086,    0.002,  0.030), # Cintura / pretina
        (1.00,  0.127,  0.086,   0.086,    0.000,  0.012), # Bajo el botón
        (1.05,  0.128,  0.087,   0.087,    0.000,  0.006), # Botón central
        (1.14,  0.134,  0.093,   0.092,   -0.002,  0.026), # Pecho medio (apertura en V superior)
        (1.24,  0.142,  0.098,   0.096,   -0.004,  0.050), # Pecho alto
        (1.32,  0.144,  0.094,   0.092,   -0.004,  0.066), # Hombros
    ]

    n_suit_pts = 23
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
            bm.faces.new((r1[i], r1[i+1], r2[i+1], r2[i])).material_index = 0

    # Dobladillos sastre con grosor hacia adentro
    for l_idx in range(len(suit_specs) - 1):
        v1_r = suit_levels_verts[l_idx][0]
        v2_r = suit_levels_verts[l_idx + 1][0]
        v1_in = bm.verts.new((v1_r.co.x * 0.95, v1_r.co.y - 0.004, v1_r.co.z))
        v2_in = bm.verts.new((v2_r.co.x * 0.95, v2_r.co.y - 0.004, v2_r.co.z))
        bm.faces.new((v1_r, v2_r, v2_in, v1_in)).material_index = 0

        v1_l = suit_levels_verts[l_idx][-1]
        v2_l = suit_levels_verts[l_idx + 1][-1]
        v1_lin = bm.verts.new((v1_l.co.x * 0.95, v1_l.co.y - 0.004, v1_l.co.z))
        v2_lin = bm.verts.new((v2_l.co.x * 0.95, v2_l.co.y - 0.004, v2_l.co.z))
        bm.faces.new((v1_l, v1_lin, v2_lin, v2_l)).material_index = 0

    # Dobladillo inferior en Z = 0.76
    r_bot = suit_levels_verts[0]
    for i in range(n_suit_pts - 1):
        v1 = r_bot[i]
        v2 = r_bot[i+1]
        v1_in = bm.verts.new((v1.co.x * 0.96, v1.co.y * 0.96, v1.co.z + 0.005))
        v2_in = bm.verts.new((v2.co.x * 0.96, v2.co.y * 0.96, v2.co.z + 0.005))
        bm.faces.new((v1, v2, v2_in, v1_in)).material_index = 0

    # Solapas notch clásicas en relieve
    for s_side in (1.0, -1.0):
        lapel_v = [
            bm.verts.new((s_side * 0.040, 0.044, 1.365)),
            bm.verts.new((s_side * 0.086, 0.076, 1.315)),
            bm.verts.new((s_side * 0.090, 0.086, 1.275)),
            bm.verts.new((s_side * 0.076, 0.088, 1.258)),
            bm.verts.new((s_side * 0.086, 0.096, 1.238)),
            bm.verts.new((s_side * 0.016, 0.084, 1.050)),
            bm.verts.new((s_side * 0.034, 0.088, 1.220)),
        ]
        if s_side > 0:
            bm.faces.new((lapel_v[0], lapel_v[1], lapel_v[2], lapel_v[3])).material_index = 0
            bm.faces.new((lapel_v[0], lapel_v[3], lapel_v[6])).material_index = 0
            bm.faces.new((lapel_v[3], lapel_v[4], lapel_v[5], lapel_v[6])).material_index = 0
        else:
            bm.faces.new((lapel_v[1], lapel_v[0], lapel_v[3], lapel_v[2])).material_index = 0
            bm.faces.new((lapel_v[3], lapel_v[0], lapel_v[6])).material_index = 0
            bm.faces.new((lapel_v[4], lapel_v[3], lapel_v[6], lapel_v[5])).material_index = 0

    # Cuello de saco en nuca
    sc_top, sc_bot = [], []
    for i in range(10):
        ang = math.pi * 0.15 + (math.pi * 0.70 * i) / 9.0
        bx = 0.050 * math.cos(ang)
        by = -0.048 * math.sin(ang) - 0.003
        sc_top.append(bm.verts.new((bx, by, 1.385)))
        sc_bot.append(bm.verts.new((bx, by, 1.355)))
    for i in range(9):
        bm.faces.new((sc_bot[i], sc_bot[i+1], sc_top[i+1], sc_top[i])).material_index = 0

    # Botón sastre central en Z = 1.05
    btn_bm = bmesh.new()
    bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.0045)
    bmesh.ops.scale(btn_bm, verts=btn_bm.verts, vec=(1.0, 0.30, 1.0))
    bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.008, 0.088, 1.050))
    v_map_b = {v: bm.verts.new(v.co) for v in btn_bm.verts}
    for f in btn_bm.faces:
        bm.faces.new([v_map_b[v] for v in f.verts]).material_index = 6
    btn_bm.free()

    # Dedos anatómicos articulados en las manos
    for is_l in (True, False):
        sign = 1.0 if is_l else -1.0
        w_center = Vector((sign * 0.282, 0.010, 0.820))
        z_knuckles = 0.820

        finger_specs = [
            ("Index",   w_center.y + 0.012, 0.046, 0.0048),
            ("Middle",  w_center.y + 0.003, 0.050, 0.0050),
            ("Ring",    w_center.y - 0.005, 0.045, 0.0048),
            ("Pinky",   w_center.y - 0.013, 0.036, 0.0042),
        ]

        if is_l:
            curl_dir = Vector((-0.25, 0.85, -0.40)).normalized()
        else:
            curl_dir = Vector(( 0.35, 0.70, -0.30)).normalized()

        for fname, fy, f_len, f_rad in finger_specs:
            fx = sign * 0.282 + (sign * 0.012 if fname == "Index" else 0.0)
            n_seg = 3
            prev_fring = None
            for s in range(n_seg + 1):
                t = s / float(n_seg)
                if is_l:
                    fz = z_knuckles - f_len * (t**0.90) * 0.60
                    cur_y = fy + curl_dir.y * (f_len * 0.85 * (t**1.10))
                    cur_x = fx + curl_dir.x * (f_len * 0.50 * (t**1.10))
                else:
                    fz = z_knuckles - f_len * (t**0.88) * 0.50
                    cur_y = fy + curl_dir.y * (f_len * 0.90 * (t**1.05))
                    cur_x = fx + curl_dir.x * (f_len * 0.55 * (t**1.05))
                r_cur = f_rad * (1.0 - 0.25 * t)

                cur_fring = []
                for k in range(6):
                    fang = (2.0 * math.pi * k) / 6.0
                    v = bm.verts.new((cur_x + r_cur * math.cos(fang),
                                      cur_y + r_cur * math.sin(fang),
                                      fz + curl_dir.z * (f_len * 0.30 * t)))
                    cur_fring.append(v)
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
        th_root = Vector((sign * (0.282 - 0.014), w_center.y + 0.008, 0.825))
        prev_th = None
        th_curl = Vector((-sign * 0.45, 0.68, -0.32)).normalized()
        for s in range(3):
            t = s / 2.0
            tx = th_root.x + th_curl.x * 0.024 * t
            ty = th_root.y + th_curl.y * 0.024 * t
            tz = th_root.z - 0.018 * t
            trad = 0.0054 * (1.0 - 0.22 * t)
            cur_th = []
            for k in range(6):
                tang = (2.0 * math.pi * k) / 6.0
                v = bm.verts.new((tx + trad * math.cos(tang),
                                           ty + trad * math.sin(tang),
                                           tz))
                cur_th.append(v)
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
        ("Hips",        "Root",        (0, 0, 0.78),      (0, 0, 0.94)),
        ("Spine",       "Hips",        (0, 0, 0.94),      (0, 0, 1.14)),
        ("Chest",       "Spine",       (0, 0, 1.14),      (0, 0, 1.30)),
        ("Neck",        "Chest",       (0, 0, 1.30),      (0, 0, 1.37)),
        ("Head",        "Neck",        (0, 0, 1.37),      (0, 0, 1.63)),

        ("Shoulder.L",  "Chest",       (0.04, 0, 1.30),   (0.174, 0, 1.300)),
        ("UpperArm.L",  "Shoulder.L",  (0.174, 0, 1.300), (0.240, 0.002, 1.120)),
        ("Forearm.L",   "UpperArm.L",  (0.240, 0.002, 1.120),(0.282, 0.008, 0.900)),
        ("Hand.L",      "Forearm.L",   (0.282, 0.008, 0.900),(0.282, 0.008, 0.76)),

        ("Shoulder.R",  "Chest",       (-0.04, 0, 1.30),  (-0.174, 0, 1.300)),
        ("UpperArm.R",  "Shoulder.R",  (-0.174, 0, 1.300), (-0.240, 0.002, 1.120)),
        ("Forearm.R",   "UpperArm.R",  (-0.240, 0.002, 1.120),(-0.282, 0.008, 0.900)),
        ("Hand.R",      "Forearm.R",   (-0.282, 0.008, 0.900),(-0.282, 0.008, 0.76)),

        ("UpperLeg.L",  "Hips",        (0.068, 0, 0.78),  (0.068, 0, 0.46)),
        ("LowerLeg.L",  "UpperLeg.L",  (0.068, 0, 0.46),  (0.068, 0, 0.12)),
        ("Foot.L",      "LowerLeg.L",  (0.068, 0, 0.12),  (0.068, 0.05, 0.03)),
        ("Toes.L",      "Foot.L",      (0.068, 0.05, 0.03),(0.068, 0.10, 0.00)),

        ("UpperLeg.R",  "Hips",        (-0.068, 0, 0.78), (-0.068, 0, 0.46)),
        ("LowerLeg.R",  "UpperLeg.R",  (-0.068, 0, 0.46), (-0.068, 0, 0.12)),
        ("Foot.R",      "LowerLeg.R",  (-0.068, 0, 0.12), (-0.068, 0.05, 0.03)),
        ("Toes.R",      "Foot.R",      (-0.068, 0.05, 0.03),(-0.068, 0.10, 0.00)),
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
        if co.z < 0.04 and ax <= 0.16:
            obj.vertex_groups["Toes.L" if co.x > 0 else "Toes.R"].add([idx], 1.0, 'REPLACE')
        elif co.z < 0.12 and ax <= 0.16:
            obj.vertex_groups["Foot.L" if co.x > 0 else "Foot.R"].add([idx], 1.0, 'REPLACE')
        # 2. EXTREMIDADES SUPERIORES (BRAZOS)
        elif ax > 0.17 and co.z < 1.38:
            side = ".L" if co.x > 0 else ".R"
            if co.z < 0.86:
                obj.vertex_groups["Hand" + side].add([idx], 1.0, 'REPLACE')
            elif co.z < 0.90:
                t_w = (co.z - 0.86) / 0.04
                obj.vertex_groups["Forearm" + side].add([idx], t_w, 'REPLACE')
                obj.vertex_groups["Hand" + side].add([idx], 1.0 - t_w, 'REPLACE')
            elif co.z < 1.12:
                obj.vertex_groups["Forearm" + side].add([idx], 1.0, 'REPLACE')
            else:
                obj.vertex_groups["UpperArm" + side].add([idx], 1.0, 'REPLACE')
        # 3. EXTREMIDADES INFERIORES (PIERNAS)
        elif co.z < 0.46:
            obj.vertex_groups["LowerLeg.L" if co.x > 0 else "LowerLeg.R"].add([idx], 1.0, 'REPLACE')
        elif co.z < 0.78 and ax > 0.02:
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
# 4. RENDER DE POSE Y FOTOGRAFÍA CANÓNICA
# =============================================================================
def apply_pose_and_render():
    scene = bpy.context.scene
    arm = bpy.data.objects["Skeleton3D"]
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)

    # Torso erguido con leve giro 3/4
    arm.pose.bones['Chest'].rotation_euler = (math.radians(-2), math.radians(-3), math.radians(2))
    arm.pose.bones['Head'].rotation_euler = (math.radians(-1), math.radians(4), math.radians(1))

    # Brazo violinista (Hand.R, -X, viewer's right): sostiene el violín erguido
    arm.pose.bones['Shoulder.R'].rotation_euler = (math.radians(2), math.radians(3), math.radians(-3))
    arm.pose.bones['UpperArm.R'].rotation_euler = (math.radians(38), math.radians(14), math.radians(-26))
    arm.pose.bones['Forearm.R'].rotation_euler = (math.radians(90), math.radians(16), math.radians(-6))
    arm.pose.bones['Hand.R'].rotation_euler = (math.radians(14), math.radians(-4), math.radians(22))

    # Brazo arco (Hand.L, +X, viewer's left): descansando elegante en la cintura
    arm.pose.bones['Shoulder.L'].rotation_euler = (math.radians(-1), math.radians(-2), math.radians(1))
    arm.pose.bones['UpperArm.L'].rotation_euler = (math.radians(10), math.radians(-4), math.radians(6))
    arm.pose.bones['Forearm.L'].rotation_euler = (math.radians(20), math.radians(-4), math.radians(2))
    arm.pose.bones['Hand.L'].rotation_euler = (math.radians(8), math.radians(4), math.radians(-2))

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_obj = bpy.data.objects["Player_Body_Mesh"]
    body_eval = body_obj.evaluated_get(depsgraph)
    mesh_eval = body_eval.to_mesh()

    vg_r = body_obj.vertex_groups.get("Hand.R")
    hand_r_verts = [v.co for v in mesh_eval.vertices if any(g.group == vg_r.index and g.weight > 0.4 for g in body_obj.data.vertices[v.index].groups)]
    avg_hand_r = sum(hand_r_verts, Vector((0,0,0))) / max(1, len(hand_r_verts))

    vg_l = body_obj.vertex_groups.get("Hand.L")
    hand_l_verts = [v.co for v in mesh_eval.vertices if any(g.group == vg_l.index and g.weight > 0.4 for g in body_obj.data.vertices[v.index].groups)]
    avg_hand_l = sum(hand_l_verts, Vector((0,0,0))) / max(1, len(hand_l_verts))
    body_eval.to_mesh_clear()

    # Cargar Violín y Arco
    if os.path.exists(VIOLIN_BLEND):
        with bpy.data.libraries.load(VIOLIN_BLEND, link=False) as (data_from, data_to):
            data_to.objects = [o for o in data_from.objects if o in ("Violin_Prop", "Violin_Bow")]
        for o in data_to.objects:
            if o:
                scene.collection.objects.link(o)
                for p in o.data.polygons: p.use_smooth = True
                if o.name == "Violin_Prop":
                    o.scale = (0.76, 0.76, 0.76)
                    rot_v = Euler((math.radians(-76), math.radians(168), math.radians(16)), 'XYZ')
                    o.rotation_euler = rot_v
                    neck_local = Vector((0.0, 0.47, 0.015))
                    neck_world_vec = rot_v.to_matrix() @ (Vector(o.scale) * neck_local)
                    o.location = avg_hand_r - neck_world_vec + Vector((0.008, 0.010, -0.006))
                elif o.name == "Violin_Bow":
                    o.scale = (0.72, 0.72, 0.72)
                    rot_b = Euler((math.radians(50), math.radians(-28), math.radians(58)), 'XYZ')
                    o.rotation_euler = rot_b
                    grip_local = Vector((0.0, 0.08, 0.0))
                    grip_world_vec = rot_b.to_matrix() @ (Vector(o.scale) * grip_local)
                    o.location = avg_hand_l - grip_world_vec + Vector((0.004, 0.006, -0.004))

    for o in list(scene.objects):
        if o.type in {'LIGHT', 'CAMERA'}: bpy.data.objects.remove(o, do_unlink=True)

    def add_light(name, ltype, energy, loc, target, color=(1,1,1), size=1.4):
        ld = bpy.data.lights.new(name, ltype)
        ld.energy = energy
        ld.color = color
        if hasattr(ld, 'size'): ld.size = size
        lo = bpy.data.objects.new(name, ld)
        lo.location = Vector(loc)
        lo.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        scene.collection.objects.link(lo)

    chest_t = (0.0, 0.0, 1.20)
    head_t = (0.0, 0.0, 1.48)
    add_light('KeyWarm', 'AREA', 140.0, (-0.8, 1.6, 1.6), chest_t, (1.0, 0.94, 0.88), size=1.4)
    add_light('FillHall', 'AREA', 65.0, (1.1, 1.5, 1.4), head_t, (0.92, 0.95, 1.0), size=2.0)
    add_light('RimHair', 'SPOT', 125.0, (0.1, -1.3, 1.9), head_t, (1.0, 0.97, 0.92))
    add_light('ViolinLight', 'AREA', 65.0, (-0.45, 1.7, 1.28), (-0.15, 0, 1.25), (1.0, 0.95, 0.88), size=1.0)

    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 36
    scene.render.film_transparent = True

    # 1. Cámara Retrato / Ícono (1024x1024)
    cam_d = bpy.data.cameras.new("AstorgaCardCam")
    cam_d.lens = 72.0
    cam_o = bpy.data.objects.new("AstorgaCardCam", cam_d)
    scene.collection.objects.link(cam_o)
    scene.camera = cam_o
    cam_o.location = Vector((0.0, 2.15, 1.25))
    cam_o.rotation_euler = (Vector((0.0, 0.0, 1.22)) - cam_o.location).to_track_quat('-Z', 'Y').to_euler()

    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    out_icon = os.path.join(SCRATCH_DIR, "test_astorga_icon.png")
    scene.render.filepath = out_icon
    bpy.ops.render.render(write_still=True)
    print(f"✓ Render de prueba guardado en: {out_icon}")

    # 2. Cámara Cuerpo Completo (800x1200)
    cam_d.lens = 48.0
    cam_o.location = Vector((0.0, 2.40, 0.90))
    cam_o.rotation_euler = (Vector((0.0, 0.0, 0.82)) - cam_o.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1200
    out_full = os.path.join(SCRATCH_DIR, "test_astorga_fullbody.png")
    scene.render.filepath = out_full
    bpy.ops.render.render(write_still=True)
    print(f"✓ Render de cuerpo completo guardado en: {out_full}")

def main():
    clean_scene()
    all_mats = create_materials()
    mat_groups = {
        "head": [all_mats["skin"], all_mats["eyes"], all_mats["hair"]],
        "body": [all_mats["suit"], all_mats["pants"], all_mats["shoes"], all_mats["skin"], all_mats["shirt"], all_mats["tie"], all_mats["buttons"]]
    }

    arm_obj = build_skeleton()
    obj_head = build_head_mesh(mat_groups)
    assign_weights(obj_head, is_head=True)
    attach_armature_modifier(obj_head, arm_obj)

    obj_body = build_body_mesh(mat_groups)
    assign_weights(obj_body, is_head=False)
    attach_armature_modifier(obj_body, arm_obj)

    apply_pose_and_render()

if __name__ == "__main__":
    main()
