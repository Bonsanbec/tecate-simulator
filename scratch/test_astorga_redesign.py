"""
Script de desarrollo y validación visual iterativa de Astorga:
- Melena setentera continua 360° (Horseshoe loft + crown + flequillo)
- Saco sastre formal 3D con faldón integrado y apertura inferior en V
- Camisa vinotinto continua hasta la cintura
- Botones anclados exactamente a la superficie textil (cero flotación)
- Encuadre de cámara calibrado
"""
import os
import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
SCRATCH_DIR = os.path.join(PROJECT_ROOT, "scratch")

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)

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
        "hair": get_or_create("Mat_Astorga_Hair", (0.09, 0.07, 0.06, 1.0), rough=0.72),
        "suit": get_or_create("Mat_Astorga_Suit", (0.070, 0.074, 0.082, 1.0), rough=0.65),
        "shirt": get_or_create("Mat_Astorga_Shirt", (0.340, 0.055, 0.085, 1.0), rough=0.58), # Rojo vino
        "tie": get_or_create("Mat_Astorga_Tie", (0.055, 0.040, 0.050, 1.0), rough=0.40),
        "pants": get_or_create("Mat_Astorga_Pants", (0.065, 0.070, 0.076, 1.0), rough=0.70),
        "shoes": get_or_create("Mat_Astorga_Shoes", (0.035, 0.035, 0.040, 1.0), rough=0.25),
        "buttons": get_or_create("Mat_Astorga_Buttons", (0.03, 0.03, 0.03, 1.0), rough=0.20, metal=0.4),
    }
    return mats

def build_head_mesh(materials):
    me = bpy.data.meshes.new("Player_Head_Mesh_Data")
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")

    def calc_face_uv(x, z):
        u = 0.50 + x / 0.275
        v = 0.50 + (z - 1.485) / 0.240
        return (max(0.0, min(1.0, u)), max(0.0, min(1.0, v)))

    # Perfil craneofacial de Astorga
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

    # Caras del rostro y cráneo base
    for l_idx in range(len(head_profile) - 1):
        r1 = rings[l_idx]
        r2 = rings[l_idx + 1]
        z_mid = (head_profile[l_idx][0] + head_profile[l_idx + 1][0]) * 0.5
        for i in range(n_ring):
            inxt = (i + 1) % n_ring
            f = bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))
            ang_mid = (2.0 * math.pi * (i + 0.5)) / n_ring
            sin_mid = math.sin(ang_mid)
            is_face_skin = (z_mid < 1.546 and sin_mid > -0.05)
            f.material_index = 0 if is_face_skin else 2 # 0: Skin, 2: Hair
            for loop in f.loops:
                loop[uv_lay].uv = calc_face_uv(loop.vert.co.x, loop.vert.co.z)

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

    # Párpados anatómicos 3D con Shape Key 'blink'
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
    # MELENA SETENTERA CONTINUA 360° DE ALTA FIDELIDAD:
    # 1. Capa envolvente continua tipo casquete escultórico en 360°
    # 2. Mechones de flequillo y ondas laterales perfectamente integrados
    # -------------------------------------------------------------------------
    hair_bm = bmesh.new()

    # Niveles de corte horizontal para la masa capilar envolvente (Horseshoe Loft)
    # Cubre desde el cuello/nuca (Z=1.385) hasta la parte superior de la frente (Z=1.58)
    # y cierra en domo continuo sobre la coronilla (Z=1.65).
    # ang va desde el frente derecho (templo R, phi ~ -0.65*pi) pasando por el dorso (phi = 0)
    # hasta el frente izquierdo (templo L, phi ~ +0.65*pi).
    hair_levels = [
        # z,      rx,    ry_back, y_cen,  phi_span, wave_freq, wave_amp
        (1.385,  0.076,  0.098,  -0.016,  0.55 * math.pi,  3.0,  0.005), # Puntas nuca sobre cuello
        (1.420,  0.088,  0.106,  -0.014,  0.60 * math.pi,  4.0,  0.006), # Cuello medio bajo
        (1.460,  0.098,  0.114,  -0.012,  0.64 * math.pi,  4.0,  0.008), # Altura mandíbula / lóbulo
        (1.500,  0.105,  0.118,  -0.010,  0.66 * math.pi,  4.0,  0.008), # Plena oreja y sienes (volumen máximo)
        (1.540,  0.102,  0.116,  -0.008,  0.68 * math.pi,  4.0,  0.007), # Sienes y frente media
        (1.575,  0.094,  0.110,  -0.008,  0.72 * math.pi,  3.0,  0.006), # Bóveda baja y línea frontal
    ]

    n_pts_hs = 25
    hs_rings = []
    for (hz, hrx, hry, hy_cen, phi_span, w_freq, w_amp) in hair_levels:
        cur_pts = []
        for i in range(n_pts_hs):
            t = (i / float(n_pts_hs - 1)) * 2.0 - 1.0 # -1 a +1
            phi = t * phi_span
            sin_p = math.sin(phi)
            cos_p = math.cos(phi)

            # Rizo / onda setentera suave
            w = w_amp * math.sin(t * w_freq * math.pi)

            # X = hrx * sin(phi) (phi=0 atrás, sin=0; phi>0 lado L; phi<0 lado R)
            hx = (hrx + w) * sin_p
            # Y = atrás es -Y, por tanto -cos(phi) * hry
            hy = -(hry + w) * cos_p + hy_cen
            cur_pts.append(hair_bm.verts.new((hx, hy, hz)))
        hs_rings.append(cur_pts)

    # Caras del manto capilar
    for l_idx in range(len(hair_levels) - 1):
        r1 = hs_rings[l_idx]
        r2 = hs_rings[l_idx + 1]
        for i in range(n_pts_hs - 1):
            f = hair_bm.faces.new((r1[i], r1[i+1], r2[i+1], r2[i]))
            f.material_index = 2

    # Domo superior continuo (Crown Dome) que conecta con el último anillo
    # Cubre desde Z=1.575 hasta la coronilla a Z=1.650
    dome_levels = [
        # z,     rx,    ry_front, ry_back, y_cen
        (1.605, 0.082, 0.068,    0.095,   -0.008),
        (1.630, 0.062, 0.050,    0.075,   -0.010),
        (1.648, 0.036, 0.030,    0.045,   -0.010),
    ]
    dome_rings = []
    n_dring = 24
    for (dz, drx, dry_f, dry_b, dy_c) in dome_levels:
        cur_d = []
        for i in range(n_dring):
            ang = (2.0 * math.pi * i) / n_dring
            ca = math.cos(ang)
            sa = math.sin(ang)
            dx = drx * ca
            dy = (dry_f if sa >= 0 else dry_b) * sa + dy_c
            # Onda sutil en la coronilla
            dw = 0.004 * math.sin(ang * 4.0)
            cur_d.append(hair_bm.verts.new((dx + dw * ca, dy + dw * sa, dz)))
        dome_rings.append(cur_d)

    # Caras del domo superior
    for l_idx in range(len(dome_levels) - 1):
        d1 = dome_rings[l_idx]
        d2 = dome_rings[l_idx + 1]
        for i in range(n_dring):
            inxt = (i + 1) % n_dring
            hair_bm.faces.new((d1[i], d1[inxt], d2[inxt], d2[i])).material_index = 2

    # Punto ápice de la coronilla
    dome_top = hair_bm.verts.new((0.0, -0.010, 1.658))
    d_last = dome_rings[-1]
    for i in range(n_dring):
        inxt = (i + 1) % n_dring
        hair_bm.faces.new((d_last[i], d_last[inxt], dome_top)).material_index = 2

    # Conectar el último anillo de herradura (hs_rings[-1]) con el domo (dome_rings[0])
    # a través de caras orgánicas
    r_top_hs = hs_rings[-1]
    d_base = dome_rings[0]
    for i in range(n_pts_hs - 1):
        # Mapear índice a través del perímetro posterior
        d_idx1 = int((i / float(n_pts_hs - 1)) * (n_dring * 0.65) + (n_dring * 0.42)) % n_dring
        d_idx2 = int(((i + 1) / float(n_pts_hs - 1)) * (n_dring * 0.65) + (n_dring * 0.42)) % n_dring
        if d_idx1 != d_idx2:
            hair_bm.faces.new((r_top_hs[i], r_top_hs[i+1], d_base[d_idx2], d_base[d_idx1])).material_index = 2

    # 3. Mechones de flequillo frontal ondulado estilo 70s peinados a los lados
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

    # Flequillo izquierdo y derecho enmarcando la frente
    add_bang_layer(( 0.005, 0.068, 1.610), ( 0.045, 0.082, 1.570), ( 0.088, 0.060, 1.520), w0=0.032, w1=0.042, w2=0.018)
    add_bang_layer((-0.005, 0.068, 1.610), (-0.045, 0.082, 1.570), (-0.088, 0.060, 1.520), w0=0.032, w1=0.042, w2=0.018)
    add_bang_layer(( 0.020, 0.066, 1.615), ( 0.068, 0.076, 1.565), ( 0.102, 0.045, 1.505), w0=0.030, w1=0.040, w2=0.018)
    add_bang_layer((-0.020, 0.066, 1.615), (-0.068, 0.076, 1.565), (-0.102, 0.045, 1.505), w0=0.030, w1=0.040, w2=0.018)

    # Mechones laterales adicionales que caen con gracia sobre las sienes y orejas
    add_bang_layer(( 0.075, 0.042, 1.560), ( 0.108, 0.035, 1.505), ( 0.096, 0.015, 1.435), w0=0.028, w1=0.036, w2=0.018, thick=0.012)
    add_bang_layer((-0.075, 0.042, 1.560), (-0.108, 0.035, 1.505), (-0.096, 0.015, 1.435), w0=0.028, w1=0.036, w2=0.018, thick=0.012)

    # Integrar cabellera en la malla principal
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

def build_body_mesh(materials):
    mesh_graph = bpy.data.meshes.new("Body_Graph_Data")
    obj_body = bpy.data.objects.new("Player_Body_Mesh", mesh_graph)
    bpy.context.scene.collection.objects.link(obj_body)

    # Nodos biomecánicos con proporciones esbeltas de Astorga:
    # Crotch natural a Z=0.74, cadera estrecha, brazos delgados
    nodes = [
        # Tronco
        (0.00,  0.000, 0.74, 0.112, 0.080), # 0: Base pelvis / inicio entrepierna
        (0.00,  0.002, 0.86, 0.116, 0.080), # 1: Caderas / Cintura baja
        (0.00,  0.004, 0.98, 0.114, 0.076), # 2: Cintura entallada
        (0.00, -0.004, 1.10, 0.124, 0.086), # 3: Tórax / costillas
        (0.00, -0.006, 1.22, 0.134, 0.094), # 4: Pectorales y espalda
        (0.00, -0.003, 1.33, 0.126, 0.084), # 5: Clavículas / hombros
        (0.00,  0.002, 1.37, 0.044, 0.044), # 6: Base del cuello camisero

        # Brazos delgados de violinista
        ( 0.05, -0.003, 1.33, 0.050, 0.050), # 7
        ( 0.160,-0.003, 1.31, 0.045, 0.045), # 8: Hombro L
        ( 0.230, 0.002, 1.13, 0.036, 0.036), # 9: Codo L
        ( 0.285, 0.008, 0.915, 0.027, 0.025), # 10: Manga puño L

        (-0.05, -0.003, 1.33, 0.050, 0.050), # 11
        (-0.160,-0.003, 1.31, 0.045, 0.045), # 12: Hombro R
        (-0.230, 0.002, 1.13, 0.036, 0.036), # 13: Codo R
        (-0.285, 0.008, 0.915, 0.027, 0.025), # 14: Manga puño R

        # Piernas con pantalón sastre recto (separación anatómica X=±0.065 m)
        ( 0.065, 0.002, 0.74, 0.054, 0.054), # 15: Cadera sup L
        ( 0.065, 0.002, 0.58, 0.048, 0.048), # 16: Muslo medio L
        ( 0.065, 0.000, 0.43, 0.042, 0.042), # 17: Rodilla L
        ( 0.065, 0.000, 0.27, 0.036, 0.036), # 18: Pantorrilla L
        ( 0.065, 0.002, 0.11, 0.030, 0.030), # 19: Tobillo L
        ( 0.065, 0.050, 0.03, 0.036, 0.090), # 20: Zapato L

        (-0.065, 0.002, 0.74, 0.054, 0.054), # 21: Cadera sup R
        (-0.065, 0.002, 0.58, 0.048, 0.048), # 22: Muslo medio R
        (-0.065, 0.000, 0.43, 0.042, 0.042), # 23: Rodilla R
        (-0.065, 0.000, 0.27, 0.036, 0.036), # 24: Pantorrilla R
        (-0.065, 0.002, 0.11, 0.030, 0.030), # 25: Tobillo R
        (-0.065, 0.050, 0.03, 0.036, 0.090), # 26: Zapato R

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

    # Mapeo de materiales en el cuerpo base:
    # 0: Mat_Astorga_Suit   (Saco y faldones)
    # 1: Mat_Astorga_Pants  (Pantalón sastre)
    # 2: Mat_Astorga_Shoes  (Zapatos negros)
    # 3: Mat_Astorga_Skin   (Manos)
    # 4: Mat_Astorga_Shirt  (Camisa vinotinto EXTENDIDA)
    # 5: Mat_Astorga_Tie    (Corbata)
    # 6: Mat_Astorga_Buttons (Botones)
    for p in bm.faces:
        c_median = p.calc_center_median()
        cz = c_median.z
        cx = abs(c_median.x)
        cy = c_median.y

        if cz < 0.08:
            p.material_index = 2 # Zapatos
        elif cz < 0.88 and cx < 0.15:
            # Pantalón formal negro
            # Si está al frente en la abertura baja del saco (0.74 < cz < 0.88 y cx < 0.06 y cy > 0):
            # se ve el pantalón y cintura formal
            p.material_index = 1
        elif cx > 0.15:
            if cz < 0.90:
                p.material_index = 3 # Manos y muñecas
            else:
                p.material_index = 0 # Mangas del saco
        else:
            # Tronco central:
            # Camisa roja/vinotinto EXTENDIDA que baja desde Z=1.36 hasta Z=0.92
            # Ancho en V: se abre arriba (Z=1.30) y se estrecha hacia el botón (Z=1.06),
            # y vuelve a verse sutilmente en la cintura por encima del cinturón
            v_width = 0.016 + max(0.0, (cz - 1.04) / 0.32) * 0.038
            if 0.92 <= cz <= 1.36 and cy > 0.025 and cx < v_width:
                p.material_index = 4 # Camisa vinotinto extendida visible
            else:
                p.material_index = 0 # Saco

        for loop in p.loops:
            loop[uv_lay].uv = (loop.vert.co.x * 2.0 + 0.5, loop.vert.co.z * 1.5)

    # -------------------------------------------------------------------------
    # A. CUELLO CAMISERO VINOTINTO TRIDIMENSIONAL
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
    # B. CORBATA CON NUDO WINDSOR (Z = 1.06 a 1.38)
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

    # Pala de la corbata
    tie_profile = [
        # z,     half_w, y_front
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
    # C. SASTRERÍA 3D: FALDONES DEL SACO FORMAL QUE SE ABREN AL FRENTE EN V INVERTIDA
    # Los faldones caen desde la cintura (Z=0.92) hasta Z=0.72 cubriendo caderas y glúteos
    # -------------------------------------------------------------------------
    faldon_levels = [
        # z,      rx,    ry_front, ry_back, open_hw
        (0.92,   0.120, 0.082,    0.084,   0.010), # Unión en cintura
        (0.85,   0.123, 0.084,    0.088,   0.035), # Se abre mostrando pantalón
        (0.78,   0.126, 0.086,    0.092,   0.065), # Apertura en V pronunciada
        (0.72,   0.128, 0.088,    0.094,   0.090), # Dobladillo inferior del saco
    ]

    n_fpts = 20
    faldon_rings = []
    for (fz, frx, fry_f, fry_b, open_hw) in faldon_levels:
        cur_fring = []
        for i in range(n_fpts):
            t = i / float(n_fpts - 1) # 0 (borde frontal R) a 1 (borde frontal L)
            # Ángulo que envuelve por los costados y la espalda:
            # t=0: frente derecho (+X > open_hw, +Y)
            # t=0.5: espalda (-Y)
            # t=1.0: frente izquierdo (-X < -open_hw, +Y)
            ang = math.pi * 0.40 - t * (math.pi * 1.80)
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)

            fx = frx * cos_a
            # Si estamos en los bordes frontales, respetar la abertura open_hw
            if t == 0:
                fx = max(open_hw, fx)
            elif t == 1:
                fx = min(-open_hw, fx)

            fy = (fry_f if sin_a >= 0 else fry_b) * sin_a
            cur_fring.append(bm.verts.new((fx, fy, fz)))
        faldon_rings.append(cur_fring)

    for l_idx in range(len(faldon_levels) - 1):
        r1 = faldon_rings[l_idx]
        r2 = faldon_rings[l_idx + 1]
        for i in range(n_fpts - 1):
            bm.faces.new((r1[i], r1[i+1], r2[i+1], r2[i])).material_index = 0

    # Dobladillo inferior con vuelo sastre
    r_last_f = faldon_rings[-1]
    inner_hem = []
    for v in r_last_f:
        inner_hem.append(bm.verts.new((v.co.x * 0.97, v.co.y * 0.97, v.co.z + 0.006)))
    for i in range(n_fpts - 1):
        bm.faces.new((r_last_f[i], r_last_f[i+1], inner_hem[i+1], inner_hem[i])).material_index = 0

    # -------------------------------------------------------------------------
    # D. SOLAPAS DE MUESCA (NOTCH LAPELS) Y BOTONES ANCLADOS EXACTOS A LA TELA
    # -------------------------------------------------------------------------
    for s_side in (1.0, -1.0):
        lapel_v = [
            bm.verts.new((s_side * 0.040, 0.042, 1.365)), # 0: Cuello nuca
            bm.verts.new((s_side * 0.076, 0.072, 1.315)), # 1: Pectoral exterior
            bm.verts.new((s_side * 0.080, 0.082, 1.275)), # 2: Vértice superior muesca
            bm.verts.new((s_side * 0.068, 0.084, 1.260)), # 3: Vértice interior muesca
            bm.verts.new((s_side * 0.078, 0.092, 1.240)), # 4: Vértice inferior solapa
            bm.verts.new((s_side * 0.012, 0.084, 1.070)), # 5: Punto de abotonado
            bm.verts.new((s_side * 0.030, 0.086, 1.220)), # 6: Borde interior medio
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
        bx = 0.048 * math.cos(ang)
        by = -0.046 * math.sin(ang) - 0.003
        sc_top.append(bm.verts.new((bx, by, 1.382)))
        sc_bot.append(bm.verts.new((bx, by, 1.355)))
    for i in range(9):
        bm.faces.new((sc_bot[i], sc_bot[i+1], sc_top[i+1], sc_top[i])).material_index = 0

    # BOTONES SASTRE: ANCLADOS EXACTAMENTE EN LA TELA
    # En Z=1.065 (botón 1) y Z=0.990 (botón 2):
    # La superficie del saco en X=0.004 está exactamente en Y=0.084 y Y=0.082
    button_coords = [
        (0.004, 0.084, 1.065),
        (0.004, 0.082, 0.990)
    ]
    for (bx, by, bz) in button_coords:
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.0042)
        bmesh.ops.scale(btn_bm, verts=btn_bm.verts, vec=(1.0, 0.30, 1.0))
        # Desplazamiento mínimo de 0.001 m para descansar sobre la tela sin flotación
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(bx, by + 0.0012, bz))
        v_map_b = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            bm.faces.new([v_map_b[v] for v in f.verts]).material_index = 6
        btn_bm.free()

    # Bolsillo de ojal superior
    p_box = [
        bm.verts.new((0.042, 0.090, 1.215)),
        bm.verts.new((0.076, 0.086, 1.215)),
        bm.verts.new((0.076, 0.086, 1.208)),
        bm.verts.new((0.042, 0.090, 1.208)),
    ]
    bm.faces.new(p_box).material_index = 0

    # Puños de camisa y botones de manga
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
    # E. MANOS DE VIOLINISTA CON PRESIÓN Y CURVATURA ANATÓMICA
    # -------------------------------------------------------------------------
    for is_l in (True, False):
        sign_a = 1.0 if is_l else -1.0
        w_center = Vector((sign_a * 0.285, 0.008, 0.835))
        z_knuckles = 0.832

        finger_specs = [
            ("Index",   w_center.y + 0.013, 0.048, 0.0048),
            ("Middle",  w_center.y + 0.004, 0.052, 0.0050),
            ("Ring",    w_center.y - 0.005, 0.047, 0.0048),
            ("Pinky",   w_center.y - 0.014, 0.038, 0.0042),
        ]
        curl_dir = Vector((-sign_a * 0.55, 0.28, -0.22)).normalized()

        for (f_name, fy, f_len, f_rad) in finger_specs:
            fx = sign_a * 0.285
            n_seg = 3
            prev_fring = None
            for s in range(n_seg + 1):
                t = s / float(n_seg)
                fz = z_knuckles - f_len * t
                cur_y = fy + curl_dir.y * (f_len * 0.30 * (t**1.3))
                cur_x = fx + curl_dir.x * (f_len * 0.22 * (t**1.3))
                r_cur = f_rad * (1.0 - 0.28 * t)

                cur_fring = []
                for k in range(6):
                    fang = (2.0 * math.pi * k) / 6.0
                    cur_fring.append(bm.verts.new((cur_x + r_cur * math.cos(fang),
                                                  cur_y + r_cur * math.sin(fang),
                                                  fz + curl_dir.z * (f_len * 0.20 * t))))
                if prev_fring:
                    for k in range(6):
                        knxt = (k + 1) % 6
                        bm.faces.new((prev_fring[k], prev_fring[knxt], cur_fring[knxt], cur_fring[k])).material_index = 3
                prev_fring = cur_fring

            tip_v = bm.verts.new((cur_x + curl_dir.x * 0.003, cur_y + curl_dir.y * 0.003, z_knuckles - f_len - 0.003))
            for k in range(6):
                knxt = (k + 1) % 6
                bm.faces.new((prev_fring[knxt], prev_fring[k], tip_v)).material_index = 3

        th_root = Vector((sign_a * (0.285 - 0.016), w_center.y + 0.010, 0.838))
        prev_th = None
        for s in range(4):
            t = s / 3.0
            tx = th_root.x - sign_a * 0.012 * t
            ty = th_root.y + 0.012 * t
            tz = th_root.z - 0.026 * t
            trad = 0.0054 * (1.0 - 0.25 * t)
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

        tip_th = bm.verts.new((th_root.x - sign_a * 0.014, th_root.y + 0.014, th_root.z - 0.030))
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

def render_test_views():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 32
    scene.render.resolution_x = 768
    scene.render.resolution_y = 1024

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

    # Iluminación de estudio calibrada para iluminar cabeza, torso y cuerpo completo
    add_l("KeyWarm",   260.0, ( 0.5, 1.8, 1.6), (1.0, 0.98, 0.95), size=1.8)
    add_l("FillFront", 160.0, (-0.8, 1.6, 1.4), (0.95, 0.97, 1.0),  size=2.2)
    add_l("RimBack",   220.0, ( 0.0, -1.8, 1.6), (1.0, 0.98, 0.95), size=1.5)
    add_l("HeadLight",  90.0, ( 0.0, 1.2, 1.7), (1.0, 0.96, 0.92), size=1.0)

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 52.0
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    # Encuadre completo centrado en Z=1.12 a 2.3 metros
    target_pos = (0.0, 0.0, 1.12)
    shots = [
        ("test_redesign_front.png",   ( 0.0,  2.30, 1.18), target_pos),
        ("test_redesign_profile.png", (-2.30,  0.0, 1.18), target_pos),
        ("test_redesign_back.png",    ( 0.0, -2.30, 1.18), target_pos),
        ("test_redesign_3q.png",      ( 1.40,  1.70, 1.22), target_pos),
    ]

    for fname, c_pos, t_pos in shots:
        cam.location = Vector(c_pos)
        cam.rotation_euler = (Vector(t_pos) - Vector(c_pos)).to_track_quat('-Z', 'Y').to_euler()
        out_p = os.path.join(SCRATCH_DIR, fname)
        scene.render.filepath = out_p
        bpy.ops.render.render(write_still=True)
        print("✓ Render guardado:", out_p)

clean_scene()
mats = setup_materials()
mat_groups = {
    "head": [mats["skin"], mats["eyes"], mats["hair"]],
    "body": [mats["suit"], mats["pants"], mats["shoes"], mats["skin"], mats["shirt"], mats["tie"], mats["buttons"]],
}
obj_head = build_head_mesh(mat_groups)
obj_body = build_body_mesh(mat_groups)
render_test_views()
print("✓ Prueba completada con éxito.")
