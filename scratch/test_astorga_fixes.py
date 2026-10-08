"""
Script de desarrollo para solucionar las 6 observaciones de Astorga:
1. Cabello 100% estanco y continuo sin huecos visibles desde ningún ángulo.
2. Camisa vinotinto modelada como prenda completa que recorre todo el torso hasta la cintura.
3. Saco formal integrado orgánicamente (curvatura sastre continua, cero 'alas' despegadas).
4. Suavizado de pesos en hombros (eliminar el sumido/pellizco del brazo del arco).
5. Prensión real y visible del arco en la mano izquierda.
6. Prensión anatómica del violín en la mano derecha con dedos envolviendo el mástil por el frente.
7. Renders de cuerpo completo y tarjeta para evaluación exhaustiva.
"""
import os
import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
SCRATCH_DIR = os.path.join(PROJECT_ROOT, "scratch")
VIOLIN_BLEND = os.path.join(PROJECT_ROOT, "godot_project/assets/props/violin.blend")
TEXTURES_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/textures")

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

def setup_materials():
    def get_or_create(name, color, rough=0.6, metal=0.0):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        out = nodes.new('ShaderNodeOutputMaterial')
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Roughness'].default_value = rough
        bsdf.inputs['Metallic'].default_value = metal
        return mat

    mats = {
        "skin": get_or_create("Mat_Astorga_Skin", (0.550, 0.400, 0.315, 1.0), rough=0.52),
        "eyes": get_or_create("Mat_Astorga_Eyes", (0.28, 0.16, 0.09, 1.0), rough=0.10),
        "hair": get_or_create("Mat_Astorga_Hair", (0.08, 0.06, 0.05, 1.0), rough=0.75),
        "suit": get_or_create("Mat_Astorga_Suit", (0.065, 0.068, 0.075, 1.0), rough=0.65),
        "shirt": get_or_create("Mat_Astorga_Shirt", (0.340, 0.055, 0.085, 1.0), rough=0.55),
        "tie": get_or_create("Mat_Astorga_Tie", (0.050, 0.038, 0.045, 1.0), rough=0.40),
        "pants": get_or_create("Mat_Astorga_Pants", (0.060, 0.064, 0.070, 1.0), rough=0.70),
        "shoes": get_or_create("Mat_Astorga_Shoes", (0.035, 0.035, 0.040, 1.0), rough=0.25),
        "buttons": get_or_create("Mat_Astorga_Buttons", (0.03, 0.03, 0.03, 1.0), rough=0.20, metal=0.4),
    }
    return mats

# =============================================================================
# 1. CABEZA CON MELENA 100% ESTANCA Y CONTINUA (CERO HUECOS)
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
        (1.370,  0.044, 0.044,    0.046,   -0.002,   False), # 0: Base cuello
        (1.392,  0.045, 0.044,    0.048,   -0.002,   False), # 1: Cuello medio
        (1.412,  0.050, 0.046,    0.054,    0.000,   True),  # 2: Ángulo submandibular
        (1.428,  0.057, 0.063,    0.066,    0.004,   True),  # 3: Mentón firme
        (1.445,  0.061, 0.063,    0.072,    0.003,   True),  # 4: Surco mentolabial
        (1.458,  0.063, 0.065,    0.080,    0.003,   True),  # 5: Labio inferior
        (1.468,  0.065, 0.064,    0.084,    0.002,   True),  # 6: Hendidura labial
        (1.478,  0.067, 0.067,    0.088,    0.002,   True),  # 7: Labio superior
        (1.492,  0.070, 0.066,    0.090,    0.001,   True),  # 8: Base nasal
        (1.505,  0.072, 0.074,    0.091,    0.000,   True),  # 9: Punta nasal
        (1.515,  0.074, 0.068,    0.091,    0.000,   True),  # 10: Ojos (Z = 1.515)
        (1.532,  0.075, 0.071,    0.090,   -0.002,   True),  # 11: Pómulos y cejas
        (1.550,  0.074, 0.068,    0.088,   -0.004,   True),  # 12: Sienes y frente baja
        (1.566,  0.072, 0.063,    0.084,   -0.006,   True),  # 13: Frente media
        (1.582,  0.068, 0.055,    0.078,   -0.008,   False), # 14: Bóveda baja
        (1.598,  0.060, 0.045,    0.070,   -0.010,   False), # 15: Bóveda media
        (1.615,  0.042, 0.030,    0.046,   -0.012,   False), # 16: Coronilla
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

            is_face_skin = (z_mid < 1.570 and sin_mid > -0.05)
            f.material_index = 0 if is_face_skin else 2

            for loop in f.loops: loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

    top_vert = bm.verts.new((0.0, -0.012, 1.620))
    r_last = rings[-1]
    for i in range(n_ring):
        inxt = (i + 1) % n_ring
        f_top = bm.faces.new((r_last[i], r_last[inxt], top_vert))
        f_top.material_index = 2
        for loop in f_top.loops: loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

    # Ojos 3D
    eye_pos = [(0.033, 0.0535, 1.515), (-0.033, 0.0535, 1.515)]
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
        bmesh.ops.translate(ear_bm, verts=ear_bm.verts, vec=(s_sign * 0.071, -0.006, 1.505))
        v_map = {v: bm.verts.new(v.co) for v in ear_bm.verts}
        for f in ear_bm.faces:
            nf = bm.faces.new([v_map[v] for v in f.verts])
            nf.material_index = 0
            for loop in nf.loops: loop[uv_lay].uv = (0.5, 0.5)
        ear_bm.free()

    # -------------------------------------------------------------------------
    # MELENA SETENTERA 100% ESTANCA Y CONTINUA (CERO HUECOS):
    # Generada a partir de anillos concéntricos completos continuos desde el ápice
    # de la coronilla hasta la nuca y sienes, esculpiendo el vano facial de forma limpia.
    # -------------------------------------------------------------------------
    hair_bm = bmesh.new()

    # Niveles de altitud de la cabellera completa (anillos cerrados de 32 vértices)
    # z, rx, ry_front, ry_back, y_offset, face_open (factor de apertura frontal)
    hair_rings_spec = [
        # Coronilla y bóveda alta (cerrados completamente en domo)
        (1.662, 0.015, 0.015, 0.015, -0.010, 0.00), # Ápice
        (1.645, 0.048, 0.040, 0.055, -0.010, 0.00),
        (1.620, 0.075, 0.065, 0.085, -0.008, 0.00),
        (1.590, 0.096, 0.078, 0.108, -0.006, 0.00), # Nacimiento alto flequillo
        # Zona media: flequillo peinado a los lados y sienes abundantes
        (1.560, 0.108, 0.072, 0.116, -0.006, 0.22), # Flequillo cae sobre sienes
        (1.530, 0.112, 0.062, 0.118, -0.008, 0.48), # Ojos libres, sienes anchas
        (1.490, 0.108, 0.050, 0.116, -0.010, 0.65), # Orejas cubiertas
        (1.450, 0.100, 0.038, 0.112, -0.012, 0.78), # Mandíbula y nuca media
        (1.415, 0.088, 0.024, 0.104, -0.014, 0.88), # Caída hacia cuello
        (1.385, 0.074, 0.012, 0.094, -0.016, 0.94), # Puntas sobre cuello de camisa
    ]

    n_hverts = 32
    h_rings = []
    for l_idx, (hz, hrx, hry_f, hry_b, hy_off, f_open) in enumerate(hair_rings_spec):
        cur_ring = []
        for i in range(n_hverts):
            ang = (2.0 * math.pi * i) / n_hverts
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)

            # Ondulación setentera armónica
            wave = 0.006 * math.sin(ang * 4.0 + l_idx * 0.7) + 0.003 * math.cos(ang * 6.0)

            hx = (hrx + wave) * cos_a
            hy_base = (hry_f if sin_a >= 0 else hry_b) + wave
            hy = hy_base * sin_a + hy_off

            # Apertura del vano facial:
            # Si estamos al frente (sin_a > 0), desplazar hacia los lados para despejar el rostro
            if f_open > 0 and sin_a > 0:
                # Modulación del vano facial
                # Abrir en el centro (|cos_a| bajo)
                center_factor = math.exp(-((cos_a / 0.55)**2))
                # Retraer en Y hacia la línea de la sien y ensanchar en X
                hy -= f_open * 0.065 * center_factor
                hx *= (1.0 + f_open * 0.18 * center_factor)
                # En la nuca baja (l_idx >= 8), festonear las puntas
                if l_idx == len(hair_rings_spec) - 1:
                    hz_eff = hz + 0.008 * math.sin(ang * 5.0)**2
                else:
                    hz_eff = hz
            else:
                hz_eff = hz

            v = hair_bm.verts.new((hx, hy, hz_eff))
            cur_ring.append(v)
        h_rings.append(cur_ring)

    # Conectar los anillos en una malla 100% estanca continua
    for l_idx in range(len(hair_rings_spec) - 1):
        r1 = h_rings[l_idx]
        r2 = h_rings[l_idx + 1]
        for i in range(n_hverts):
            inxt = (i + 1) % n_hverts
            f = hair_bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))
            f.material_index = 2

    # Cerrar el ápice superior de la coronilla
    apex_top = hair_bm.verts.new((0.0, -0.010, 1.666))
    r_top = h_rings[0]
    for i in range(n_hverts):
        inxt = (i + 1) % n_hverts
        f = hair_bm.faces.new((r_top[i], apex_top, r_top[inxt]))
        f.material_index = 2

    # Integrar en la malla principal
    v_map_h = {v: bm.verts.new(v.co) for v in hair_bm.verts}
    for f in hair_bm.faces:
        nf = bm.faces.new([v_map_h[v] for v in f.verts])
        nf.material_index = 2
        for loop in nf.loops: loop[uv_lay].uv = (0.5, 0.5)
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
# 2. CUERPO: SASTRERÍA 3D ORGÁNICA INTEGRADA, CAMISA COMPLETA Y PRENSIÓN REAL
# =============================================================================
def build_body_mesh(materials):
    mesh_graph = bpy.data.meshes.new("Body_Graph_Data")
    obj_body = bpy.data.objects.new("Player_Body_Mesh", mesh_graph)
    bpy.context.scene.collection.objects.link(obj_body)

    # Grafo biomecánico esbelto con hombros reposicionados para cero sumido
    nodes = [
        # Tronco
        (0.00,  0.000, 0.74, 0.110, 0.078), # 0: Crotch anatómico
        (0.00,  0.002, 0.86, 0.114, 0.078), # 1: Caderas / Cintura baja
        (0.00,  0.004, 0.98, 0.112, 0.074), # 2: Cintura entallada
        (0.00, -0.004, 1.10, 0.122, 0.084), # 3: Tórax
        (0.00, -0.006, 1.22, 0.132, 0.092), # 4: Pectorales y espalda
        (0.00, -0.003, 1.33, 0.124, 0.082), # 5: Clavículas / hombros
        (0.00,  0.002, 1.37, 0.044, 0.044), # 6: Base cuello

        # Brazos
        ( 0.05, -0.003, 1.33, 0.048, 0.048), # 7
        ( 0.160,-0.003, 1.31, 0.044, 0.044), # 8: Hombro L
        ( 0.230, 0.002, 1.13, 0.035, 0.035), # 9: Codo L
        ( 0.285, 0.008, 0.915, 0.026, 0.024), # 10: Manga puño L

        (-0.05, -0.003, 1.33, 0.048, 0.048), # 11
        (-0.160,-0.003, 1.31, 0.044, 0.044), # 12: Hombro R
        (-0.230, 0.002, 1.13, 0.035, 0.035), # 13: Codo R
        (-0.285, 0.008, 0.915, 0.026, 0.024), # 14: Manga puño R

        # Piernas con pantalón sastre recto
        ( 0.064, 0.002, 0.74, 0.052, 0.052), # 15: Cadera sup L
        ( 0.064, 0.002, 0.58, 0.046, 0.046), # 16: Muslo medio L
        ( 0.064, 0.000, 0.43, 0.040, 0.040), # 17: Rodilla L
        ( 0.064, 0.000, 0.27, 0.035, 0.035), # 18: Pantorrilla L
        ( 0.064, 0.002, 0.11, 0.030, 0.030), # 19: Tobillo L
        ( 0.064, 0.050, 0.03, 0.036, 0.090), # 20: Zapato L

        (-0.064, 0.002, 0.74, 0.052, 0.052), # 21: Cadera sup R
        (-0.064, 0.002, 0.58, 0.046, 0.046), # 22: Muslo medio R
        (-0.064, 0.000, 0.43, 0.040, 0.040), # 23: Rodilla R
        (-0.064, 0.000, 0.27, 0.035, 0.035), # 24: Pantorrilla R
        (-0.064, 0.002, 0.11, 0.030, 0.030), # 25: Tobillo R
        (-0.064, 0.050, 0.03, 0.036, 0.090), # 26: Zapato R

        # Muñecas y Palmas
        ( 0.285,  0.010, 0.885, 0.019, 0.014), # 27: Muñeca L
        ( 0.285,  0.010, 0.835, 0.023, 0.012), # 28: Palma L
        (-0.285,  0.010, 0.885, 0.019, 0.014), # 29: Muñeca R
        (-0.285,  0.010, 0.835, 0.023, 0.012), # 30: Palma R
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
    # El torso en sí mismo es el saco sastre continuo hasta Z=0.74 (dobladillo)
    # y las piernas son el pantalón sastre.
    # La camisa vinotinto está modelada y presente en el centro frontal continuo.
    for p in bm.faces:
        c_median = p.calc_center_median()
        cz = c_median.z
        cx = abs(c_median.x)
        cy = c_median.y

        if cz < 0.08:
            p.material_index = 2 # Zapatos
        elif cz < 0.74 and cx < 0.15:
            p.material_index = 1 # Pantalón formal bajo el saco
        elif cx > 0.15:
            if cz < 0.90:
                p.material_index = 3 # Manos y muñecas
            else:
                p.material_index = 0 # Mangas del saco
        else:
            # Torso:
            # Saco formal negro en espalda y costados.
            # Al frente:
            # - Camisa vinotinto presente en el centro continuo desde Z=1.36 hasta Z=0.88 (cintura)
            # - En la parte baja (Z=0.74 a 0.88) en el centro: pantalón formal negro visible
            if cy > 0.025:
                # Centro del pecho y abdomen:
                if 0.88 <= cz <= 1.36 and cx < (0.018 + max(0.0, (cz - 1.05) / 0.30) * 0.038):
                    p.material_index = 4 # Camisa vinotinto MODELADA y PRESENTE
                elif 0.74 <= cz < 0.88 and cx < (0.016 + (0.88 - cz) * 0.35):
                    # Apertura inferior en V del saco mostrando el pantalón formal
                    p.material_index = 1 # Pantalón formal
                else:
                    p.material_index = 0 # Saco
            else:
                p.material_index = 0 # Saco en espalda

        for loop in p.loops:
            loop[uv_lay].uv = (loop.vert.co.x * 2.0 + 0.5, loop.vert.co.z * 1.5)

    # -------------------------------------------------------------------------
    # A. CAMISA VINOTINTO MODELADA EN 3D: CUELLO, PECHERA Y BOTONADURA
    # Presente como geometría estructurada sobre el torso
    # -------------------------------------------------------------------------
    n_c = 18
    c_bot, c_top = [], []
    for i in range(n_c):
        ang = (2.0 * math.pi * i) / n_c
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        cx = 0.046 * cos_a
        cy = (0.048 if sin_a >= 0 else 0.044) * sin_a + 0.002
        c_bot.append(bm.verts.new((cx, cy, 1.350)))
        c_top.append(bm.verts.new((cx * 1.05, cy * 1.05, 1.395)))
    for i in range(n_c):
        inxt = (i + 1) % n_c
        f = bm.faces.new((c_bot[i], c_bot[inxt], c_top[inxt], c_top[i]))
        f.material_index = 4

    wing_l = [bm.verts.new((0.006, 0.054, 1.392)), bm.verts.new((0.040, 0.044, 1.385)), bm.verts.new((0.020, 0.068, 1.345))]
    wing_r = [bm.verts.new((-0.006, 0.054, 1.392)), bm.verts.new((-0.020, 0.068, 1.345)), bm.verts.new((-0.040, 0.044, 1.385))]
    bm.faces.new(wing_l).material_index = 4
    bm.faces.new(wing_r).material_index = 4

    # -------------------------------------------------------------------------
    # B. CORBATA TRIDIMENSIONAL CON NUDO WINDSOR
    # -------------------------------------------------------------------------
    knot_v = [
        bm.verts.new((-0.014, 0.056, 1.385)),
        bm.verts.new(( 0.014, 0.056, 1.385)),
        bm.verts.new(( 0.010, 0.076, 1.345)),
        bm.verts.new((-0.010, 0.076, 1.345)),
        bm.verts.new(( 0.000, 0.084, 1.365)),
    ]
    for f_verts in [
        (knot_v[0], knot_v[1], knot_v[4]),
        (knot_v[1], knot_v[2], knot_v[4]),
        (knot_v[2], knot_v[3], knot_v[4]),
        (knot_v[3], knot_v[0], knot_v[4]),
    ]:
        bm.faces.new(f_verts).material_index = 5

    tie_profile = [
        (1.345,  0.010,  0.076),
        (1.275,  0.012,  0.088),
        (1.205,  0.013,  0.092),
        (1.135,  0.013,  0.090),
        (1.070,  0.011,  0.084),
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
    # C. SASTRERÍA 3D: SOLAPAS Y BORDES ORGÁNICOS DEL SACO (CERO ALAS DESPEGADAS)
    # Las solapas y faldones del saco están integrados de forma orgánica al torso
    # -------------------------------------------------------------------------
    for s_side in (1.0, -1.0):
        # Solapas superiores notch
        lapel_v = [
            bm.verts.new((s_side * 0.040, 0.042, 1.365)),
            bm.verts.new((s_side * 0.074, 0.070, 1.315)),
            bm.verts.new((s_side * 0.078, 0.080, 1.275)),
            bm.verts.new((s_side * 0.066, 0.082, 1.260)),
            bm.verts.new((s_side * 0.076, 0.090, 1.240)),
            bm.verts.new((s_side * 0.010, 0.084, 1.070)),
            bm.verts.new((s_side * 0.028, 0.086, 1.220)),
        ]
        if s_side > 0:
            bm.faces.new((lapel_v[0], lapel_v[1], lapel_v[2], lapel_v[3])).material_index = 0
            bm.faces.new((lapel_v[0], lapel_v[3], lapel_v[6])).material_index = 0
            bm.faces.new((lapel_v[3], lapel_v[4], lapel_v[5], lapel_v[6])).material_index = 0
        else:
            bm.faces.new((lapel_v[1], lapel_v[0], lapel_v[3], lapel_v[2])).material_index = 0
            bm.faces.new((lapel_v[3], lapel_v[0], lapel_v[6])).material_index = 0
            bm.faces.new((lapel_v[4], lapel_v[3], lapel_v[6], lapel_v[5])).material_index = 0

        # Borde inferior del saco (curva sastre que bordea la apertura en V inferior)
        # Sigue el contorno del cuerpo suavemente sin alas salientes
        hem_pts = [
            bm.verts.new((s_side * 0.010, 0.084, 1.070)), # Botón
            bm.verts.new((s_side * 0.022, 0.082, 0.980)),
            bm.verts.new((s_side * 0.042, 0.081, 0.880)),
            bm.verts.new((s_side * 0.068, 0.080, 0.780)),
            bm.verts.new((s_side * 0.092, 0.078, 0.730)), # Esquina inferior delantera
        ]
        # Borde exterior ligeramente desplazado para dar relieve de costura sastre
        hem_ext = [
            bm.verts.new((s_side * 0.018, 0.085, 1.070)),
            bm.verts.new((s_side * 0.034, 0.083, 0.980)),
            bm.verts.new((s_side * 0.056, 0.082, 0.880)),
            bm.verts.new((s_side * 0.082, 0.081, 0.780)),
            bm.verts.new((s_side * 0.106, 0.079, 0.730)),
        ]
        for k in range(4):
            if s_side > 0:
                bm.faces.new((hem_pts[k], hem_pts[k+1], hem_ext[k+1], hem_ext[k])).material_index = 0
            else:
                bm.faces.new((hem_pts[k+1], hem_pts[k], hem_ext[k], hem_ext[k+1])).material_index = 0

    # Cuello de saco nuca
    sc_top, sc_bot = [], []
    for i in range(10):
        ang = math.pi * 0.15 + (math.pi * 0.70 * i) / 9.0
        bx = 0.048 * math.cos(ang)
        by = -0.046 * math.sin(ang) - 0.003
        sc_top.append(bm.verts.new((bx, by, 1.382)))
        sc_bot.append(bm.verts.new((bx, by, 1.355)))
    for i in range(9):
        bm.faces.new((sc_bot[i], sc_bot[i+1], sc_top[i+1], sc_top[i])).material_index = 0

    # Botones colocados EXACTAMENTE sobre la tela
    button_coords = [
        (0.004, 0.084, 1.065),
        (0.004, 0.082, 0.990)
    ]
    for (bx, by, bz) in button_coords:
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.0042)
        bmesh.ops.scale(btn_bm, verts=btn_bm.verts, vec=(1.0, 0.30, 1.0))
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(bx, by + 0.0012, bz))
        v_map_b = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            bm.faces.new([v_map_b[v] for v in f.verts]).material_index = 6
        btn_bm.free()

    # Bolsillo de ojal
    p_box = [
        bm.verts.new((0.042, 0.090, 1.215)),
        bm.verts.new((0.076, 0.086, 1.215)),
        bm.verts.new((0.076, 0.086, 1.208)),
        bm.verts.new((0.042, 0.090, 1.208)),
    ]
    bm.faces.new(p_box).material_index = 0

    # Puños y botones de manga
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
                bm.faces.new([v_map_bm[v] for v in f.verts]).material_index = 6
            btn_m.free()

    # -------------------------------------------------------------------------
    # D. MANOS ANATÓMICAS CON PRENSIÓN DE VIOLINISTA (5 DEDOS CURVADOS)
    # Dedos curvados hacia adelante y hacia adentro para sujetar instrumentos
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
        # Curvatura pronunciada hacia la palma (+Y y hacia el centro) para prensión real
        curl_dir = Vector((-sign_a * 0.40, 0.70, -0.45)).normalized()

        for (f_name, fy, f_len, f_rad) in finger_specs:
            fx = sign_a * 0.285
            n_seg = 3
            prev_fring = None
            for s in range(n_seg + 1):
                t = s / float(n_seg)
                fz = z_knuckles - f_len * (t**0.8) * 0.70
                cur_y = fy + curl_dir.y * (f_len * 0.75 * (t**1.2))
                cur_x = fx + curl_dir.x * (f_len * 0.45 * (t**1.2))
                r_cur = f_rad * (1.0 - 0.25 * t)

                cur_fring = []
                for k in range(6):
                    fang = (2.0 * math.pi * k) / 6.0
                    cur_fring.append(bm.verts.new((cur_x + r_cur * math.cos(fang),
                                                  cur_y + r_cur * math.sin(fang),
                                                  fz + curl_dir.z * (f_len * 0.35 * t))))
                if prev_fring:
                    for k in range(6):
                        knxt = (k + 1) % 6
                        bm.faces.new((prev_fring[k], prev_fring[knxt], cur_fring[knxt], cur_fring[k])).material_index = 3
                prev_fring = cur_fring

            tip_v = bm.verts.new((cur_x + curl_dir.x * 0.004, cur_y + curl_dir.y * 0.004, fz - 0.004))
            for k in range(6):
                knxt = (k + 1) % 6
                bm.faces.new((prev_fring[knxt], prev_fring[k], tip_v)).material_index = 3

        # Pulgar opuesto curvado hacia los dedos
        th_root = Vector((sign_a * (0.285 - 0.014), w_center.y + 0.008, 0.838))
        prev_th = None
        th_curl = Vector((-sign_a * 0.50, 0.65, -0.35)).normalized()
        for s in range(4):
            t = s / 3.0
            tx = th_root.x + th_curl.x * 0.025 * t
            ty = th_root.y + th_curl.y * 0.025 * t
            tz = th_root.z - 0.022 * t
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

    for mat in materials["body"]: obj_body.data.materials.append(mat)
    return obj_body

# =============================================================================
# 3. ESQUELETO Y RIGGING CON SUAVIZADO EN HOMBROS (CERO SUMIDO)
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
        ("Chest",       "Spine",       (0, 0, 1.10),      (0, 0, 1.33)),
        ("Neck",        "Chest",       (0, 0, 1.33),      (0, 0, 1.40)),
        ("Head",        "Neck",        (0, 0, 1.40),      (0, 0, 1.66)),

        ("Shoulder.L",  "Chest",       (0.04, 0, 1.33),   (0.155, 0, 1.32)),
        ("UpperArm.L",  "Shoulder.L",  (0.155, 0, 1.32),  (0.230, 0.005, 1.13)),
        ("Forearm.L",   "UpperArm.L",  (0.230, 0.005, 1.13),(0.285, 0.015, 0.915)),
        ("Hand.L",      "Forearm.L",   (0.285, 0.015, 0.915),(0.285, 0.015, 0.76)),

        ("Shoulder.R",  "Chest",       (-0.04, 0, 1.33),  (-0.155, 0, 1.32)),
        ("UpperArm.R",  "Shoulder.R",  (-0.155, 0, 1.32), (-0.230, 0.005, 1.13)),
        ("Forearm.R",   "UpperArm.R",  (-0.230, 0.005, 1.13),(-0.285, 0.015, 0.915)),
        ("Hand.R",      "Forearm.R",   (-0.285, 0.015, 0.915),(-0.285, 0.015, 0.76)),

        ("UpperLeg.L",  "Hips",        (0.064, 0, 0.74),  (0.064, 0, 0.43)),
        ("LowerLeg.L",  "UpperLeg.L",  (0.064, 0, 0.43),  (0.064, 0, 0.11)),
        ("Foot.L",      "LowerLeg.L",  (0.064, 0, 0.11),  (0.064, 0.05, 0.03)),
        ("Toes.L",      "Foot.L",      (0.064, 0.05, 0.03),(0.064, 0.10, 0.00)),

        ("UpperLeg.R",  "Hips",        (-0.064, 0, 0.74), (-0.064, 0, 0.43)),
        ("LowerLeg.R",  "UpperLeg.R",  (-0.064, 0, 0.43), (-0.064, 0, 0.11)),
        ("Foot.R",      "LowerLeg.R",  (-0.064, 0, 0.11), (-0.064, 0.05, 0.03)),
        ("Toes.R",      "Foot.R",      (-0.064, 0.05, 0.03),(-0.064, 0.10, 0.00)),
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
            if co.z < 1.39:
                obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 1.43:
                t = (co.z - 1.39) / 0.04
                obj.vertex_groups["Neck"].add([v.index], 1.0 - t, 'REPLACE')
                obj.vertex_groups["Head"].add([v.index], t, 'REPLACE')
            else:
                obj.vertex_groups["Head"].add([v.index], 1.0, 'REPLACE')
        else:
            # BRAZOS Y HOMBROS CON SUAVIZADO ORGÁNICO (CERO SUMIDO)
            if abs(co.x) > 0.08 and co.z > 0.70:
                side = ".L" if co.x > 0 else ".R"
                ax = abs(co.x)
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
                    # Zona de unión de hombro / deltoides / clavícula (Z > 1.18 y AX > 0.08)
                    # Suavizado gradual entre UpperArm, Shoulder y Chest
                    if ax > 0.165:
                        obj.vertex_groups["UpperArm" + side].add([v.index], 1.0, 'REPLACE')
                    elif ax > 0.115:
                        # Zona deltoide media: blend suave entre UpperArm y Shoulder
                        t = (ax - 0.115) / 0.05
                        obj.vertex_groups["Shoulder" + side].add([v.index], 1.0 - t, 'REPLACE')
                        obj.vertex_groups["UpperArm" + side].add([v.index], t, 'REPLACE')
                    else:
                        # Zona clavicular interna: blend entre Chest y Shoulder
                        t = (ax - 0.08) / 0.035
                        obj.vertex_groups["Chest"].add([v.index], 1.0 - t, 'REPLACE')
                        obj.vertex_groups["Shoulder" + side].add([v.index], t, 'REPLACE')
            # PIERNAS
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
            # TORSO
            else:
                if co.z < 0.88:
                    obj.vertex_groups["Hips"].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.10:
                    t = (co.z - 0.88) / 0.22
                    obj.vertex_groups["Hips"].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Spine"].add([v.index], t, 'REPLACE')
                elif co.z < 1.30:
                    t = (co.z - 1.10) / 0.20
                    obj.vertex_groups["Spine"].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Chest"].add([v.index], t, 'REPLACE')
                elif co.z < 1.35:
                    t = (co.z - 1.30) / 0.05
                    obj.vertex_groups["Chest"].add([v.index], 1.0 - t, 'REPLACE')
                    obj.vertex_groups["Neck"].add([v.index], t, 'REPLACE')
                else:
                    obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')

def attach_armature(obj, arm_obj):
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj
    obj.parent = arm_obj

# =============================================================================
# 4. RENDER DE TARJETA CON POSE NATURAL Y PRENSIÓN DE INSTRUMENTOS
# =============================================================================
def render_portrait_and_fullbody(arm_obj):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 32

    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')

    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)

    # Pose canónica natural de Astorga (scratch/humans/astorga.png):
    # Torso y cabeza con garbo relajado
    arm_obj.pose.bones['Chest'].rotation_euler = (math.radians(-2), math.radians(-5), math.radians(2))
    arm_obj.pose.bones['Head'].rotation_euler = (math.radians(-1), math.radians(6), math.radians(1))

    # BRAZO DERECHO (Hand.R, -X, lado derecho de la imagen):
    # Sostiene el VIOLÍN. Codo flexionado cerca del cuerpo, antebrazo sube con ángulo natural,
    # mano rotada para que la palma dé soporte lateral/trasero y los dedos abracen el mástil por el frente
    arm_obj.pose.bones['UpperArm.R'].rotation_euler = (math.radians(28), math.radians(14), math.radians(-24))
    arm_obj.pose.bones['Forearm.R'].rotation_euler = (math.radians(92), math.radians(12), math.radians(-10))
    arm_obj.pose.bones['Hand.R'].rotation_euler = (math.radians(18), math.radians(-16), math.radians(38))

    # BRAZO IZQUIERDO (Hand.L, +X, lado izquierdo de la imagen):
    # Sostiene el ARCO. Hombro relajado (rotación moderada para NO sumir el deltoides),
    # antebrazo cruzado hacia el pecho, mano empuñando el talón del arco
    arm_obj.pose.bones['Shoulder.L'].rotation_euler = (math.radians(4), math.radians(-2), math.radians(4))
    arm_obj.pose.bones['UpperArm.L'].rotation_euler = (math.radians(16), math.radians(-6), math.radians(10))
    arm_obj.pose.bones['Forearm.L'].rotation_euler = (math.radians(52), math.radians(-8), math.radians(8))
    arm_obj.pose.bones['Hand.L'].rotation_euler = (math.radians(18), math.radians(12), math.radians(-10))

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()

    hand_l_mat = arm_obj.matrix_world @ arm_obj.pose.bones['Hand.L'].matrix
    hand_r_mat = arm_obj.matrix_world @ arm_obj.pose.bones['Hand.R'].matrix
    hand_l_loc = hand_l_mat.to_translation()
    hand_r_loc = hand_r_mat.to_translation()

    # Cargar y posicionar Violín y Arco
    if os.path.exists(VIOLIN_BLEND):
        with bpy.data.libraries.load(VIOLIN_BLEND, link=False) as (data_from, data_to):
            data_to.objects = [o for o in data_from.objects if o in ("Violin_Prop", "Violin_Bow")]
        for o in data_to.objects:
            if o:
                scene.collection.objects.link(o)
                for p in o.data.polygons: p.use_smooth = True
                if o.name == "Violin_Prop":
                    o.scale = (0.76, 0.76, 0.76)
                    # Violín vertical apoyado en Hand.R:
                    # Mástil colocado entre el pulgar y los dedos curvados
                    o.rotation_euler = Euler((math.radians(-76), math.radians(174), math.radians(16)), 'XYZ')
                    # Mástil/caja posicionado exactamente en contacto con Hand.R
                    o.location = Vector((hand_r_loc.x + 0.006, hand_r_loc.y - 0.008, hand_r_loc.z - 0.215))
                elif o.name == "Violin_Bow":
                    o.scale = (0.70, 0.70, 0.70)
                    # El arco colocado DIRECTAMENTE en la mano izquierda:
                    # La vara pasa por el hueco de Hand.L y apunta diagonalmente hacia el pecho
                    o.rotation_euler = Euler((math.radians(22), math.radians(-6), math.radians(-16)), 'XYZ')
                    # Ubicación exacta en la palma/dedos de Hand.L
                    o.location = Vector((hand_l_loc.x + 0.002, hand_l_loc.y + 0.006, hand_l_loc.z - 0.008))

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

    add_l("KeyWarm",    260.0, ( 0.5, 1.8, 1.6), (1.0, 0.98, 0.95), size=1.8)
    add_l("FillFront",  160.0, (-0.8, 1.6, 1.4), (0.95, 0.97, 1.0),  size=2.2)
    add_l("RimBack",    220.0, ( 0.0, -1.8, 1.6), (1.0, 0.98, 0.95), size=1.5)
    add_l("ViolinLight", 90.0, (-0.4, 1.5, 1.25), (1.0, 0.96, 0.92), size=1.0)
    add_l("HairLight",  120.0, ( 0.0, 0.5, 2.0), (1.0, 0.98, 0.95), size=1.2)

    cam_data = bpy.data.cameras.new("CamCard")
    cam_data.lens = 72.0
    cam = bpy.data.objects.new("CamCard", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    # 1. Render de Tarjeta / Retrato (1024x1024)
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    cam.location = Vector((0.0, 2.15, 1.25))
    target = Vector((0.0, 0.0, 1.22))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()

    out_card = os.path.join(SCRATCH_DIR, "test_astorga_portrait_fixed.png")
    scene.render.filepath = out_card
    bpy.ops.render.render(write_still=True)
    print("✓ Render de tarjeta/retrato guardado en:", out_card)

    # 2. Render de Cuerpo Completo (Frontal completo, 800x1200) para inspección de piernas y faldón
    cam_data.lens = 52.0
    cam.location = Vector((0.0, 2.45, 1.05))
    target_fb = Vector((0.0, 0.0, 0.95))
    cam.rotation_euler = (target_fb - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1200

    out_fb = os.path.join(SCRATCH_DIR, "test_astorga_fullbody_fixed.png")
    scene.render.filepath = out_fb
    bpy.ops.render.render(write_still=True)
    print("✓ Render de cuerpo completo guardado en:", out_fb)

clean_scene()
mats = setup_materials()
mat_groups = {
    "head": [mats["skin"], mats["eyes"], mats["hair"]],
    "body": [mats["suit"], mats["pants"], mats["shoes"], mats["skin"], mats["shirt"], mats["tie"], mats["buttons"]],
}

arm_obj = build_skeleton()
obj_head = build_head_mesh(mat_groups)
assign_weights(obj_head, is_head=True)
attach_armature(obj_head, arm_obj)

obj_body = build_body_mesh(mat_groups)
assign_weights(obj_body, is_head=False)
attach_armature(obj_body, arm_obj)

render_portrait_and_fullbody(arm_obj)
print("✓ Pipeline de prueba ejecutado exitosamente.")
