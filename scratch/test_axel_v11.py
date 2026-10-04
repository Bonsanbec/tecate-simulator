"""
Axel v11 - Perfeccionamiento Anatómico y Vestimenta Sastre Estratificada
- Ropa estratificada con offsets de capas reales: Cuerpo/Camisa (+0mm) -> Corbata (+3mm) -> Chaleco (+7mm).
- Chaleco con escote en V diagonal continuo que converge en el botón superior (Z=1.22).
- Corbata con nudo Windsor y pala que desciende por el escote en V y se esconde bajo el chaleco.
- Boca anatómica 3D esculpida (labio superior con arco de Cupido, labio inferior carnosos,
  hendidura labial rehundida, comisuras y surco mentolabial) sincronizada con las coordenadas UV del mapa difuso.
- Manos anatómicas naturales con pulgar medial oponible y anillos de plata.
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
# 1. CABEZA CON BOCA ANATÓMICA 3D REAL Y TEXTURAS SINCRONIZADAS
# =============================================================================
def build_head_mesh(materials):
    me = bpy.data.meshes.new("Player_Head_Mesh_Data")
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")

    # Mapeo UV sincronizado con axel_face_diffuse.png:
    # Barbilla / perilla: V = 0.28 a 0.32
    # Labio inferior: V = 0.372
    # Hendidura labial: V = 0.385
    # Labio superior con arco de Cupido: V = 0.398
    # Nariz: V = 0.52
    # Cuencas oculares: V = 0.63
    # Cejas: V = 0.72
    # Frente: V = 0.82
    # Coronilla: V = 0.95
    n_ring = 32
    head_profile = [
        # z, rx, ry_front, ry_back, y_offset, v_uv
        (1.410, 0.050, 0.045, 0.050, 0.010, 0.16), # Base cuello
        (1.435, 0.048, 0.044, 0.048, 0.014, 0.22), # Cuello medio
        (1.450, 0.048, 0.038, 0.050, 0.015, 0.26), # Garganta / submandíbula
        (1.468, 0.056, 0.076, 0.058, 0.022, 0.30), # Barbilla / perilla
        (1.485, 0.058, 0.065, 0.062, 0.018, 0.34), # Surco mentolabial
        (1.498, 0.061, 0.076, 0.066, 0.016, 0.372),# Labio inferior carnosos
        (1.508, 0.062, 0.068, 0.068, 0.014, 0.385),# Hendidura labial (boca entreabierta sutil)
        (1.518, 0.063, 0.077, 0.070, 0.012, 0.398),# Labio superior (arco de Cupido)
        (1.532, 0.064, 0.070, 0.072, 0.010, 0.44), # Filtrum / base nasal
        (1.550, 0.065, 0.090, 0.074, 0.008, 0.52), # Punta de la nariz prominente
        (1.572, 0.067, 0.078, 0.076, 0.005, 0.58), # Puente nasal / pómulos
        (1.595, 0.069, 0.062, 0.078, 0.002, 0.63), # Cuencas oculares
        (1.618, 0.071, 0.068, 0.080, 0.000, 0.72), # Cejas prominentes
        (1.645, 0.072, 0.064, 0.080, -0.003, 0.80),# Frente
        (1.670, 0.068, 0.056, 0.075, -0.006, 0.88),# Frente alta
        (1.695, 0.056, 0.044, 0.062, -0.008, 0.94),# Bóveda craneal
        (1.712, 0.035, 0.025, 0.040, -0.010, 0.98),# Coronilla
    ]

    rings = []
    for l_idx, (z, rx, ry_f, ry_b, y_off, v_uv) in enumerate(head_profile):
        cur_ring = []
        for i in range(n_ring):
            ang = (2.0 * math.pi * i) / n_ring
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            x = rx * cos_a
            y = (ry_f if sin_a >= 0 else ry_b) * sin_a + y_off

            # 1. Esculpido de la Boca (labios y comisuras) en l_idx 5, 6, 7
            if l_idx in (5, 6, 7):
                if 0.38 * math.pi <= ang <= 0.62 * math.pi:
                    m_dist = abs(ang - 0.5 * math.pi) / 0.12
                    mw = max(0.0, 1.0 - m_dist**2)
                    if l_idx == 5: # Labio inferior carnosos
                        y += 0.008 * mw
                    elif l_idx == 6: # Hendidura labial rehundida
                        y -= 0.005 * mw
                    elif l_idx == 7: # Labio superior con arco de Cupido
                        # Dos picos en ang ~ 0.46 pi y 0.54 pi
                        cupid_dip = math.cos((ang - 0.5 * math.pi) * 20.0) * 0.003
                        y += (0.007 + cupid_dip) * mw

            # 2. Esculpido de la Nariz en l_idx 8, 9, 10
            if l_idx in (8, 9, 10) and 0.40 * math.pi <= ang <= 0.60 * math.pi:
                nw = max(0.0, 1.0 - abs(ang - 0.5 * math.pi) / 0.20)
                y += (0.020 if l_idx == 9 else 0.008) * nw

            # 3. Esculpido del Mentón en l_idx 3
            if l_idx == 3 and 0.35 * math.pi <= ang <= 0.65 * math.pi:
                cw = max(0.0, 1.0 - abs(ang - 0.5 * math.pi) / 0.28)
                y += 0.016 * cw

            # 4. Cuencas oculares en l_idx 11
            if l_idx == 11 and (0.28 * math.pi <= ang <= 0.42 * math.pi or 0.58 * math.pi <= ang <= 0.72 * math.pi):
                y -= 0.012

            cur_ring.append(bm.verts.new((x, y, z)))
        rings.append((cur_ring, v_uv))

    for l_idx in range(len(head_profile) - 1):
        r1, v1 = rings[l_idx]
        r2, v2 = rings[l_idx + 1]
        for i in range(n_ring):
            i_next = (i + 1) % n_ring
            f = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
            f.material_index = 0
            u_i = 1.0 - (i / float(n_ring))
            u_next = 1.0 - ((i + 1) / float(n_ring))
            if i == n_ring - 1: u_next = 0.0
            for loop in f.loops:
                if loop.vert == r1[i]: loop[uv_lay].uv = (u_i, v1)
                elif loop.vert == r1[i_next]: loop[uv_lay].uv = (u_next, v1)
                elif loop.vert == r2[i_next]: loop[uv_lay].uv = (u_next, v2)
                elif loop.vert == r2[i]: loop[uv_lay].uv = (u_i, v2)

    # Ojos 3D reales con iris avellana
    eye_pos = [(0.033, 0.052, 1.595), (-0.033, 0.052, 1.595)]
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

    # Rizos volumétricos de Axel
    curl_specs = [
        (0.000, 0.068, 1.660, 0.003, 0.018, -0.055, 0.010, 2.2, 0.0),
        (0.016, 0.066, 1.658, 0.008, 0.016, -0.058, 0.010, 2.4, 0.8),
        (-0.016, 0.066, 1.658, -0.008, 0.016, -0.058, 0.010, 2.4, 1.5),
        (0.032, 0.062, 1.654, 0.012, 0.014, -0.052, 0.009, 2.1, 2.2),
        (-0.032, 0.062, 1.654, -0.012, 0.014, -0.052, 0.009, 2.1, 2.9),
        (0.046, 0.054, 1.650, 0.015, 0.012, -0.050, 0.0085, 2.0, 3.7),
        (-0.046, 0.054, 1.650, -0.015, 0.012, -0.050, 0.0085, 2.0, 4.4),
        (0.008, 0.065, 1.646, 0.002, 0.012, -0.038, 0.008, 1.8, 1.2),
        (-0.008, 0.065, 1.646, -0.002, 0.012, -0.038, 0.008, 1.8, 2.5),
        (0.024, 0.063, 1.644, 0.005, 0.010, -0.035, 0.0075, 1.7, 3.4),
        (-0.024, 0.063, 1.644, -0.005, 0.010, -0.035, 0.0075, 1.7, 4.8),
        (0.064, 0.025, 1.636, 0.010, 0.005, -0.075, 0.0085, 2.5, 0.5),
        (-0.064, 0.025, 1.636, -0.010, 0.005, -0.075, 0.0085, 2.5, 1.7),
        (0.068, 0.005, 1.626, 0.008, -0.002, -0.070, 0.008, 2.3, 2.8),
        (-0.068, 0.005, 1.626, -0.008, -0.002, -0.070, 0.008, 2.3, 3.9),
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
        (1.650, 0.088, 0.098, -0.002, 1.00, 0.000),
        (1.675, 0.086, 0.096, -0.003, 0.96, 0.000),
        (1.705, 0.083, 0.093, -0.004, 0.90, 0.000),
        (1.730, 0.080, 0.090, -0.005, 0.84, 0.000),
        (1.750, 0.076, 0.086, -0.006, 0.78, 0.016),
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

    top_c = bm.verts.new((0.0, -0.006, 1.735))
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
        brim_mid.append(bm.verts.new((0.125 * cos_a, 0.138 * sin_a - 0.002, 1.650 + dip_z * 0.5)))
        brim_outer.append(bm.verts.new((0.158 * cos_a, 0.170 * sin_a - 0.002, 1.650 + dip_z)))

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
# 2. CUERPO CONTINUO, CHALECO CONFORMADO SOBRE EL CUERPO, CORBATA Y MANOS
# =============================================================================
def build_body_mesh(materials):
    mesh_graph = bpy.data.meshes.new("Body_Graph_Data")
    obj_body = bpy.data.objects.new("Player_Body_Mesh", mesh_graph)
    bpy.context.scene.collection.objects.link(obj_body)

    # Nodos de piel para el cuerpo anatómico base (camisa y pantalón)
    nodes = [
        # Tronco
        (0.00,  0.00, 0.82, 0.130, 0.100), # 0: Pelvis base
        (0.00,  0.00, 0.94, 0.145, 0.105), # 1: Caderas / Cintura pantalón
        (0.00,  0.00, 1.04, 0.135, 0.098), # 2: Cintura entallada
        (0.00,  0.00, 1.16, 0.155, 0.110), # 3: Costillas
        (0.00,  0.00, 1.28, 0.170, 0.120), # 4: Pectorales
        (0.00,  0.00, 1.36, 0.150, 0.105), # 5: Clavículas / hombros
        (0.00,  0.00, 1.41, 0.052, 0.052), # 6: Base del cuello

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

    # Materiales según altura
    for p in bm.faces:
        center_z = p.calc_center_median().z
        if center_z < 0.10:
            p.material_index = 2 # Zapatos
        elif center_z < 0.94:
            p.material_index = 1 # Pantalón
        else:
            p.material_index = 0 # Camisa

    # =========================================================================
    # CUELLO CAMISERO Y CORBATA DE SEDA (CAPA INTERMEDIA: +3mm sobre camisa)
    # =========================================================================
    # Cuello de camisa
    collar_l = [
        bm.verts.new((0.010, 0.052, 1.435)),
        bm.verts.new((0.055, 0.040, 1.425)),
        bm.verts.new((0.025, 0.068, 1.365)),
    ]
    collar_r = [
        bm.verts.new((-0.010, 0.052, 1.435)),
        bm.verts.new((-0.025, 0.068, 1.365)),
        bm.verts.new((-0.055, 0.040, 1.425)),
    ]
    bm.faces.new(collar_l).material_index = 0
    bm.faces.new(collar_r).material_index = 0

    # Nudo Windsor de la corbata
    knot_v = [
        bm.verts.new((-0.018, 0.068, 1.415)),
        bm.verts.new((0.018, 0.068, 1.415)),
        bm.verts.new((0.012, 0.074, 1.365)),
        bm.verts.new((-0.012, 0.074, 1.365)),
        bm.verts.new((0.000, 0.058, 1.395)),
    ]
    bm.faces.new((knot_v[0], knot_v[1], knot_v[2], knot_v[3])).material_index = 4
    bm.faces.new((knot_v[0], knot_v[3], knot_v[4])).material_index = 4
    bm.faces.new((knot_v[1], knot_v[4], knot_v[2])).material_index = 4

    # Pala de la corbata descendiendo limpia por el centro hasta esconderse bajo el chaleco
    # Capa intermedia a Y = +0.004 m sobre la camisa
    tie_v = [
        # Z = 1.365
        bm.verts.new((-0.012, 0.074, 1.365)),
        bm.verts.new((0.012, 0.074, 1.365)),
        # Z = 1.300
        bm.verts.new((-0.015, 0.096, 1.300)),
        bm.verts.new((0.015, 0.096, 1.300)),
        # Z = 1.230
        bm.verts.new((-0.018, 0.114, 1.230)),
        bm.verts.new((0.018, 0.114, 1.230)),
        # Z = 1.160 (adentro del cierre del chaleco)
        bm.verts.new((-0.020, 0.110, 1.160)),
        bm.verts.new((0.020, 0.110, 1.160)),
    ]
    for ts in range(3):
        v1 = tie_v[ts * 2]
        v2 = tie_v[ts * 2 + 1]
        v3 = tie_v[(ts + 1) * 2 + 1]
        v4 = tie_v[(ts + 1) * 2]
        bm.faces.new((v1, v2, v3, v4)).material_index = 4

    # =========================================================================
    # CHALECO ENTALLADO 3D REAL (CAPA EXTERIOR: +7mm SOBRE EL CUERPO)
    # =========================================================================
    # El chaleco envuelve el cuerpo orgánicamente:
    # Tiene hombros, espalda, sisas y un escote en V diagonal elegante
    # que va desde las clavículas (X = ±0.065, Z = 1.36) hasta converger en X = 0 en Z = 1.22.
    # Desde Z = 1.22 hasta Z = 0.93 está cerrado en el centro por 5 botones plateados.
    
    vest_levels = [
        # Z, rx, ry_front, ry_back, v_opening_half_width
        (1.36, 0.176, 0.118, 0.110, 0.065), # Clavículas / hombros
        (1.30, 0.174, 0.128, 0.116, 0.040), # Pecho superior
        (1.25, 0.170, 0.126, 0.114, 0.018), # Pecho medio
        (1.21, 0.166, 0.122, 0.112, 0.000), # Convergencia en V / Botón 1
        (1.14, 0.160, 0.118, 0.108, 0.000), # Botón 2
        (1.07, 0.152, 0.114, 0.104, 0.000), # Botón 3 / Cintura entallada
        (1.00, 0.150, 0.112, 0.102, 0.000), # Botón 4
        (0.93, 0.154, 0.114, 0.104, 0.000), # Botón 5 / Inicio picos
    ]
    
    n_v = 24
    vest_rings = []
    for (z, rx, ry_f, ry_b, v_w) in vest_levels:
        cur_ring = []
        for i in range(n_v):
            ang = (2.0 * math.pi * i) / n_v
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            
            vx = rx * cos_a
            vy = (ry_f if sin_a >= 0 else ry_b) * sin_a
            vz = z
            
            # Escote en V diagonal:
            # Los vértices del frente central (sin_a > 0.4) se retraen hacia los lados
            # respetando la apertura del escote en V (v_w)
            if v_w > 0.0 and sin_a > 0.35:
                if abs(vx) < v_w:
                    vx = math.copysign(v_w, vx) if abs(vx) > 0.001 else (v_w if cos_a >= 0 else -v_w)
                    
            cur_ring.append(bm.verts.new((vx, vy, vz)))
        vest_rings.append(cur_ring)

    for l_idx in range(len(vest_levels) - 1):
        r1 = vest_rings[l_idx]
        r2 = vest_rings[l_idx + 1]
        v_w = vest_levels[l_idx][4]
        for i in range(n_v):
            i_next = (i + 1) % n_v
            # Si cruza el centro frontal en zona de escote en V abierto, no conectar cara
            ang = (2.0 * math.pi * i) / n_v
            if v_w > 0.0 and (5 <= i <= 7):
                continue
            f_v = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
            f_v.material_index = 3 # Chaleco

    # Picos inferiores frontales del chaleco (picos elegantes afilados sobre el pantalón)
    peak_l = [vest_rings[-1][5], vest_rings[-1][6], bm.verts.new((0.038, 0.116, 0.880))]
    peak_r = [vest_rings[-1][6], vest_rings[-1][7], bm.verts.new((-0.038, 0.116, 0.880))]
    bm.faces.new(peak_l).material_index = 3
    bm.faces.new(peak_r).material_index = 3

    # 5 Botones plateados tridimensionales alineados en la tapeta central
    b_zs = [1.21, 1.14, 1.07, 1.00, 0.93]
    for bz in b_zs:
        by = 0.118 + (1.21 - bz) * (-0.006)
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.0045)
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.0, by + 0.005, bz))
        v_map = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            nf = bm.faces.new([v_map[v] for v in f.verts])
            nf.material_index = 5 # Plata
        btn_bm.free()

    # Bolsillos Welt de ribete
    p_specs = [(0.075, 0.985, 0.032), (-0.075, 0.985, 0.032), (0.065, 1.140, 0.026)]
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
    # MANOS ANATÓMICAS CON PULGAR OPONIBLE MEDIAL Y ANILLOS DE PLATA
    # =========================================================================
    for is_left in (True, False):
        sign_h = 1.0 if is_left else -1.0
        w_m = sign_h * 0.295 # Medial (hacia el cuerpo)
        w_l = sign_h * 0.365 # Lateral (hacia afuera)

        base_z = 0.84
        base_y = 0.014

        finger_specs = [
            ("Index",  0.22, 0.075, 0.0065),
            ("Middle", 0.45, 0.082, 0.0070),
            ("Ring",   0.68, 0.076, 0.0065),
            ("Little", 0.90, 0.065, 0.0055),
        ]

        for (f_name, f_frac, f_len, f_rad) in finger_specs:
            f_x = w_m + (w_l - w_m) * f_frac
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
                r_rad = f_rad * 1.20
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

        # Pulgar Oponible Medial Curvado hacia la Palma (-Y)
        th_pts = [
            Vector((w_m, 0.008, 0.895)),
            Vector((w_m - sign_h * 0.015, 0.004, 0.870)),
            Vector((w_m - sign_h * 0.026, 0.000, 0.845)),
            Vector((w_m - sign_h * 0.032, -0.005, 0.825)),
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
        tip_th = bm.verts.new((th_pts[-1].x - sign_h * 0.003, th_pts[-1].y - 0.004, th_pts[-1].z - 0.004))
        for k in range(4):
            k_next = (k + 1) % 4
            f_tip_th = bm.faces.new((prev_th_r[k_next], prev_th_r[k], tip_th))
            f_tip_th.material_index = 6

        # Masa de la palma contorneada
        p_box = [
            bm.verts.new((w_m, 0.025, 0.92)),
            bm.verts.new((w_l, 0.025, 0.92)),
            bm.verts.new((w_l, 0.002, 0.92)),
            bm.verts.new((w_m, 0.002, 0.92)),
            bm.verts.new((w_m, 0.025, 0.84)),
            bm.verts.new((w_l, 0.025, 0.84)),
            bm.verts.new((w_l, 0.002, 0.84)),
            bm.verts.new((w_m, 0.002, 0.84)),
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
# 3. ESQUELETO Y RIGGING
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
        ("Neck",        "Chest",       (0, 0, 1.36),      (0, 0, 1.45)),
        ("Head",        "Neck",        (0, 0, 1.45),      (0, 0, 1.74)),
        
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
            grp = "Neck" if co.z < 1.44 else "Head"
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
# 4. RENDER PREVIEW DE ESTUDIO
# =============================================================================
def render_preview():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    scene.cycles.device = 'CPU'

    key = bpy.data.objects.new("Key", bpy.data.lights.new("Key", 'AREA'))
    key.data.energy = 110.0
    key.data.size = 1.4
    key.data.color = (1.0, 0.98, 0.95)
    key.location = Vector((-0.8, 1.6, 1.7))
    key.rotation_euler = (math.radians(55.0), 0.0, math.radians(-145.0))
    scene.collection.objects.link(key)

    fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", 'AREA'))
    fill.data.energy = 50.0
    fill.data.size = 1.8
    fill.data.color = (0.92, 0.96, 1.0)
    fill.location = Vector((1.0, 1.6, 1.3))
    scene.collection.objects.link(fill)

    rim = bpy.data.objects.new("Rim", bpy.data.lights.new("Rim", 'SPOT'))
    rim.data.energy = 65.0
    rim.data.spot_size = math.radians(65.0)
    rim.data.color = (1.0, 1.0, 1.0)
    rim.location = Vector((0.0, -1.2, 1.9))
    rim.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
    scene.collection.objects.link(rim)

    # Cámara encuadrando medio cuerpo (desde la cintura hasta la punta del sombrero fedora)
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.lens = 52.0
    cam.location = Vector((0.04, 1.75, 1.30))
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
    print("GENERANDO AXEL V11 (BOCA ESCULPIDA Y ROPA ESTRATIFICADA)")
    print("=" * 60)
    clean_scene()

    mat_skin = create_pbr_material("Mat_Axel_Skin", (0.80, 0.63, 0.52, 1.0), roughness=0.50,
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
    print("✓ Player_Head_Mesh generado con boca 3D esculpida y fedora snap-brim.")
    
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
