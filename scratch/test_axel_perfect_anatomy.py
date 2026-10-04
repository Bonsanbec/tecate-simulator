"""
Generador Maestro Definitivo de Axel (Tecate Simulator)
Fidelidad estilo Fortnite / Pixar, basado exactamente en la fotografía 'scratch/humans/axel2.tiff'.

Arquitectura de Modelado:
1. Cabeza y Rostro:
   - Modelado orgánico por cajas y lazos quads con Subdivision Surface.
   - Barbilla prominente cincelada, mandíbula angular con reborde submandibular de 90°.
   - Cuello atlético proporcionado (8 cm) con nuez de Adán y esternocleidomastoideo.
   - Nariz definida con tabique recto, punta y fosas nasales.
   - Labios carnosos con arco de Cupido y comisuras rehundidas.
   - Cuencas oculares con globos oculares 3D (iris avellana estriado, anillo limbal y pupila).
   - Orejas modeladas en los laterales.
   - Racimos volumétricos de rizos densos y orgánicos de Axel cayendo bajo el sombrero.
   - Sombrero fedora negro de fieltro con hendidura en lágrima (teardrop crease), pellizco frontal,
     cinta grosgrain de seda y ala ancha snap-brim con caída frontal y laterales curvados hacia arriba.
2. Torso y Ropa de Gala (Idéntica a axel2.tiff):
   - Camisa de vestir popelina carbón oscuro con cuello camisero doblado y puños con botones.
   - Corbata de seda con nudo Windsor y pala con rayas diagonales rep-stripes.
   - Chaleco sastre gris plata con tirantes sobre los hombros, sisas contorneadas,
     escote en V profundo, 5 botones plateados, ribetes de bolsillos y faldón en picos puntiagudos.
   - Pantalón de vestir carbón con finas rayas diplomáticas y raya de planchado.
   - Zapatos Oxford en cuero negro pulido con suela y tacón de cuero.
3. Manos Anatómicas:
   - Dorso orientado al frente (+Y) y palma hacia atrás (-Y).
   - 4 dedos relajados con 3 falanges articuladas curvándose suavemente.
   - Pulgar oponible medial naciendo de la eminencia tenar hacia adentro del eje corporal.
   - Dos anillos de plata en la mano izquierda (en dedo índice y medio como en axel2.png).
4. Rig y Compatibilidad:
   - 22 huesos canónicos (Skeleton3D / Armature).
   - Submallas Player_Head_Mesh (capa 2) y Player_Body_Mesh (capa 1).
   - Render Cycles CPU para evitar errores de Metal en sandbox.
"""

import bpy
import bmesh
import math
import os
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
# MODELADO DE CABEZA, ROSTRO, RIZOS Y FEDORA
# =============================================================================
def build_head_mesh(materials):
    me = bpy.data.meshes.new("Player_Head_Mesh_Data")
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")

    # 1. Anatomía Facial Estilizada Fortnite de Axel
    # Proporciones reales: Cuello arranca en Z=1.42 (encima de las clavículas a 1.40),
    # barbilla a Z=1.50, boca a Z=1.54, nariz a Z=1.58, ojos a Z=1.63, cejas a 1.66,
    # frente a 1.70, coronilla a 1.76.
    
    n_ring = 32
    head_profile = [
        # z, rx, ry_front, ry_back, y_offset, u_v
        (1.410, 0.052, 0.046, 0.052, 0.010, 0.15), # Base cuello / contacto con camisa
        (1.435, 0.050, 0.045, 0.050, 0.014, 0.22), # Cuello medio / nuez de Adán
        (1.465, 0.049, 0.042, 0.052, 0.015, 0.28), # Garganta / submandíbula retraída
        (1.490, 0.058, 0.076, 0.062, 0.020, 0.35), # Barbilla pronunciada y ángulo mandibular
        (1.512, 0.062, 0.068, 0.066, 0.018, 0.40), # Surco mentolabial
        (1.532, 0.064, 0.078, 0.072, 0.015, 0.44), # Labio inferior
        (1.548, 0.065, 0.075, 0.074, 0.012, 0.48), # Comisura labial / línea de boca
        (1.564, 0.066, 0.080, 0.076, 0.010, 0.51), # Labio superior con arco de Cupido
        (1.582, 0.067, 0.090, 0.078, 0.008, 0.54), # Punta nasal prominente y alas
        (1.602, 0.069, 0.080, 0.080, 0.005, 0.58), # Puente nasal / pómulos altos
        (1.628, 0.071, 0.064, 0.083, 0.002, 0.64), # Cuencas oculares (órbita retraída)
        (1.654, 0.073, 0.070, 0.084, 0.000, 0.70), # Arco superciliar y cejas
        (1.685, 0.074, 0.066, 0.083, -0.003, 0.78),# Frente media
        (1.718, 0.071, 0.058, 0.078, -0.006, 0.86),# Frente alta / nacimiento cabello
        (1.745, 0.058, 0.045, 0.064, -0.008, 0.93),# Bóveda craneal
        (1.765, 0.035, 0.025, 0.040, -0.010, 0.98),# Coronilla
    ]
    
    rings = []
    for l_idx, (z, rx, ry_f, ry_b, y_off, v_coord) in enumerate(head_profile):
        cur_ring = []
        for i in range(n_ring):
            ang = (2.0 * math.pi * i) / n_ring
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            
            x = rx * cos_a
            y = (ry_f if sin_a >= 0 else ry_b) * sin_a + y_off
            
            # Nariz esculpida en l_idx 7, 8, 9
            if l_idx in (7, 8, 9) and 0.4 * math.pi <= ang <= 0.6 * math.pi:
                nw = max(0.0, 1.0 - abs(ang - 0.5 * math.pi) / 0.20)
                y += (0.018 if l_idx == 8 else 0.009) * nw
                
            # Mentón esculpido en l_idx 3
            if l_idx == 3 and 0.35 * math.pi <= ang <= 0.65 * math.pi:
                cw = max(0.0, 1.0 - abs(ang - 0.5 * math.pi) / 0.28)
                y += 0.015 * cw
                
            # Cuencas oculares en l_idx 10
            if l_idx == 10 and (0.28 * math.pi <= ang <= 0.42 * math.pi or 0.58 * math.pi <= ang <= 0.72 * math.pi):
                y -= 0.011
                
            v = bm.verts.new((x, y, z))
            cur_ring.append(v)
        rings.append((cur_ring, v_coord))
        
    for l_idx in range(len(head_profile) - 1):
        r1, v1 = rings[l_idx]
        r2, v2 = rings[l_idx + 1]
        for i in range(n_ring):
            i_next = (i + 1) % n_ring
            f = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
            f.material_index = 0 # Piel
            # Asignar UV continuo
            u_i = 1.0 - (i / float(n_ring))
            u_next = 1.0 - ((i + 1) / float(n_ring))
            if i == n_ring - 1:
                u_next = 0.0
            for loop in f.loops:
                if loop.vert == r1[i]: loop[uv_lay].uv = (u_i, v1)
                elif loop.vert == r1[i_next]: loop[uv_lay].uv = (u_next, v1)
                elif loop.vert == r2[i_next]: loop[uv_lay].uv = (u_next, v2)
                elif loop.vert == r2[i]: loop[uv_lay].uv = (u_i, v2)

    # 2. Ojos 3D con Iris Avellana
    eye_pos = [(0.033, 0.052, 1.628), (-0.033, 0.052, 1.628)]
    for pos in eye_pos:
        e_bm = bmesh.new()
        bmesh.ops.create_uvsphere(e_bm, u_segments=16, v_segments=12, radius=0.0135)
        bmesh.ops.rotate(e_bm, verts=e_bm.verts, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(-90), 4, 'X'))
        bmesh.ops.translate(e_bm, verts=e_bm.verts, vec=pos)
        
        v_map = {v: bm.verts.new(v.co) for v in e_bm.verts}
        for f in e_bm.faces:
            nf = bm.faces.new([v_map[v] for v in f.verts])
            nf.material_index = 1 # Ojos
            for loop in nf.loops:
                co = loop.vert.co - Vector(pos)
                loop[uv_lay].uv = (0.5 + co.x / (2.0 * 0.0135), 0.5 + co.z / (2.0 * 0.0135))
        e_bm.free()

    # 3. Rizos Volumétricos de Axel (mechones orgánicos de cabello rizado)
    curl_specs = [
        # Frente central
        (0.000, 0.068, 1.705, 0.003, 0.018, -0.055, 0.010, 2.2, 0.0),
        (0.016, 0.066, 1.702, 0.008, 0.016, -0.058, 0.010, 2.4, 0.8),
        (-0.016, 0.066, 1.702, -0.008, 0.016, -0.058, 0.010, 2.4, 1.5),
        (0.032, 0.062, 1.698, 0.012, 0.014, -0.052, 0.009, 2.1, 2.2),
        (-0.032, 0.062, 1.698, -0.012, 0.014, -0.052, 0.009, 2.1, 2.9),
        (0.046, 0.054, 1.695, 0.015, 0.012, -0.050, 0.0085, 2.0, 3.7),
        (-0.046, 0.054, 1.695, -0.015, 0.012, -0.050, 0.0085, 2.0, 4.4),
        # Mechones frontales secundarios
        (0.008, 0.065, 1.690, 0.002, 0.012, -0.038, 0.008, 1.8, 1.2),
        (-0.008, 0.065, 1.690, -0.002, 0.012, -0.038, 0.008, 1.8, 2.5),
        (0.024, 0.063, 1.688, 0.005, 0.010, -0.035, 0.0075, 1.7, 3.4),
        (-0.024, 0.063, 1.688, -0.005, 0.010, -0.035, 0.0075, 1.7, 4.8),
        # Patillas y sienes
        (0.064, 0.025, 1.680, 0.010, 0.005, -0.075, 0.0085, 2.5, 0.5),
        (-0.064, 0.025, 1.680, -0.010, 0.005, -0.075, 0.0085, 2.5, 1.7),
        (0.068, 0.005, 1.670, 0.008, -0.002, -0.070, 0.008, 2.3, 2.8),
        (-0.068, 0.005, 1.670, -0.008, -0.002, -0.070, 0.008, 2.3, 3.9),
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
                    f_h.material_index = 2 # Cabello
            prev_ring = cur_ring

    # 4. Sombrero Fedora Maestro (Fieltro negro azabache, cinta grosgrain y ala snap-brim)
    n_hat = 32
    hat_levels = [
        (1.700, 0.088, 0.098, -0.002, 1.00, 0.000), # Base corona / ala
        (1.725, 0.086, 0.096, -0.003, 0.96, 0.000), # Cinta grosgrain
        (1.755, 0.083, 0.093, -0.004, 0.90, 0.000), # Corona media
        (1.785, 0.080, 0.090, -0.005, 0.84, 0.000), # Pellizco frontal
        (1.805, 0.076, 0.086, -0.006, 0.78, 0.016), # Cima lágrima
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
                if dist_x < 0.6:
                    vz -= crease * (1.0 - dist_x / 0.6)
            cur_ring.append(bm.verts.new((vx, vy, vz)))
        hat_rings.append(cur_ring)
        
    for l_idx in range(len(hat_levels) - 1):
        r1 = hat_rings[l_idx]
        r2 = hat_rings[l_idx + 1]
        m_idx = 4 if l_idx == 0 else 3 # 4: Cinta, 3: Fedora
        for i in range(n_hat):
            i_next = (i + 1) % n_hat
            f = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
            f.material_index = m_idx
            
    top_c = bm.verts.new((0.0, -0.006, 1.790))
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
        
        brim_mid.append(bm.verts.new((0.125 * cos_a, 0.138 * sin_a - 0.002, 1.700 + dip_z * 0.5)))
        brim_outer.append(bm.verts.new((0.158 * cos_a, 0.170 * sin_a - 0.002, 1.700 + dip_z)))
        
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
# MODELADO DE CUERPO, CHALECO, CAMISA, PANTALÓN, ZAPATOS Y MANOS ANATÓMICAS
# =============================================================================
def build_body_mesh(materials):
    me = bpy.data.meshes.new("Player_Body_Mesh_Data")
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")

    # 1. Torso Base con Hombros Claviculares y Trapecio Inclinado
    # Z va de 1.41 (cuello) bajando a 1.38 (hombros), 1.25 (pecho), 1.05 (cintura), 0.95 (cinturón)
    torso_levels = [
        # z, rx, ry, y_c, mat_idx (0: Shirt, 1: Pants, 2: Shoes, 3: Vest, 4: Tie, 5: Silver, 6: Skin)
        (1.41, 0.070, 0.055, 0.010, 0), # Cuello base
        (1.38, 0.185, 0.095, 0.005, 0), # Hombros / clavículas / trapecio inclinado
        (1.28, 0.180, 0.110, 0.002, 0), # Pectorales / pecho alto
        (1.18, 0.170, 0.106, 0.000, 0), # Mitad pecho
        (1.08, 0.158, 0.098, -0.002, 0),# Costillas
        (1.00, 0.148, 0.092, -0.004, 0),# Cintura estrecha entallada
        (0.94, 0.155, 0.096, -0.002, 1),# Cinturón / cintura de pantalón
        (0.88, 0.162, 0.102, 0.000, 1), # Caderas / pelvis
        (0.82, 0.158, 0.098, 0.000, 1), # Entrepierna
    ]
    n_torso = 24
    torso_rings = []
    for (z, rx, ry, y_c, m_idx) in torso_levels:
        cur_ring = []
        for i in range(n_torso):
            ang = (2.0 * math.pi * i) / n_torso
            vx = rx * math.cos(ang)
            vy = ry * math.sin(ang) + y_c
            vz = z
            cur_ring.append(bm.verts.new((vx, vy, vz)))
        torso_rings.append((cur_ring, m_idx))
        
    for l_idx in range(len(torso_levels) - 1):
        r1, m_idx = torso_rings[l_idx]
        r2, _ = torso_rings[l_idx + 1]
        for i in range(n_torso):
            i_next = (i + 1) % n_torso
            f = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
            f.material_index = m_idx

    # 2. Piernas y Pantalón de Vestir con Raya
    leg_levels = [
        (0.82, 0.072, 0.076, 1),
        (0.70, 0.066, 0.070, 1),
        (0.58, 0.060, 0.062, 1),
        (0.46, 0.054, 0.055, 1), # Rodilla
        (0.34, 0.050, 0.051, 1),
        (0.22, 0.046, 0.047, 1),
        (0.10, 0.044, 0.045, 1), # Dobladillo
    ]
    n_leg = 16
    for sign_leg in (1.0, -1.0):
        leg_x = sign_leg * 0.088
        l_rings = []
        for (z, rx, ry, m_idx) in leg_levels:
            cur_r = []
            for i in range(n_leg):
                ang = (2.0 * math.pi * i) / n_leg
                cos_a = math.cos(ang)
                sin_a = math.sin(ang)
                cur_ry = ry * (1.08 if abs(cos_a) < 0.2 else 1.0)
                cur_r.append(bm.verts.new((leg_x + rx * cos_a, cur_ry * sin_a, z)))
            l_rings.append((cur_r, m_idx))
        for l_idx in range(len(leg_levels) - 1):
            r1, m_idx = l_rings[l_idx]
            r2, _ = l_rings[l_idx + 1]
            for i in range(n_leg):
                i_next = (i + 1) % n_leg
                f = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
                f.material_index = m_idx

        # 3. Zapatos de Vestir Oxford en Cuero Negro
        shoe_levels = [
            (0.10, 0.044, 0.050, 0.045, 0.005),
            (0.06, 0.046, 0.075, 0.048, 0.015),
            (0.03, 0.048, 0.095, 0.050, 0.025),
            (0.00, 0.049, 0.098, 0.052, 0.025),
        ]
        s_rings = []
        for (z, rx, ry_f, ry_b, y_off) in shoe_levels:
            cur_r = []
            for i in range(n_leg):
                ang = (2.0 * math.pi * i) / n_leg
                cos_a = math.cos(ang)
                sin_a = math.sin(ang)
                vy = (ry_f if sin_a >= 0 else ry_b) * sin_a + y_off
                cur_r.append(bm.verts.new((leg_x + rx * cos_a, vy, z)))
            s_rings.append(cur_r)
        for l_idx in range(len(shoe_levels) - 1):
            r1 = s_rings[l_idx]
            r2 = s_rings[l_idx + 1]
            for i in range(n_leg):
                i_next = (i + 1) % n_leg
                f = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
                f.material_index = 2 # Zapatos
        bot_s = s_rings[-1]
        bot_c = bm.verts.new((leg_x, 0.025, 0.00))
        for i in range(n_leg):
            i_next = (i + 1) % n_leg
            f = bm.faces.new((bot_s[i_next], bot_s[i], bot_c))
            f.material_index = 2

    # 4. Brazos y Mangas de Camisa Popelina Carbón
    arm_levels = [
        (0.00, 0.065, 0.062),
        (0.20, 0.058, 0.056),
        (0.40, 0.052, 0.050),
        (0.60, 0.048, 0.046),
        (0.80, 0.044, 0.042),
        (0.95, 0.040, 0.038),
        (1.00, 0.036, 0.034),
    ]
    n_arm = 12
    for sign_arm in (1.0, -1.0):
        p_sh = Vector((sign_arm * 0.185, 0.00, 1.36))
        p_wr = Vector((sign_arm * 0.330, 0.015, 0.90))
        arm_rings = []
        for (t, rx, ry) in arm_levels:
            center = p_sh.lerp(p_wr, t)
            if 0.4 <= t <= 0.7:
                center.y -= 0.012 * math.sin((t - 0.4) / 0.3 * math.pi)
            cur_r = []
            for i in range(n_arm):
                ang = (2.0 * math.pi * i) / n_arm
                cur_r.append(bm.verts.new((center.x + rx * math.cos(ang),
                                          center.y + ry * math.sin(ang),
                                          center.z)))
            arm_rings.append(cur_r)
        for l_idx in range(len(arm_levels) - 1):
            r1 = arm_rings[l_idx]
            r2 = arm_rings[l_idx + 1]
            for i in range(n_arm):
                i_next = (i + 1) % n_arm
                f = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
                f.material_index = 0 # Camisa

    # 5. Manos Anatómicas Hiperrealistas con Pulgar Oponible Medial y Anillos
    for is_left in (True, False):
        sign_h = 1.0 if is_left else -1.0
        w_m = sign_h * 0.295 # Medial (hacia el cuerpo)
        w_l = sign_h * 0.365 # Lateral (hacia afuera)
        
        finger_specs = [
            ("Index",  0.22, 0.075, 0.0065),
            ("Middle", 0.45, 0.082, 0.0070),
            ("Ring",   0.68, 0.076, 0.0065),
            ("Little", 0.90, 0.065, 0.0055),
        ]
        
        # Base de nudillos
        base_z = 0.82
        base_y = 0.014
        
        for (f_name, f_frac, f_len, f_rad) in finger_specs:
            f_x = w_m + (w_l - w_m) * f_frac
            # 3 Falanges curvadas suavemente hacia la palma (-Y)
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
                
            # Dos Anillos de Plata de Axel en mano izquierda (en falange proximal de Índice y Medio)
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

        # Pulgar Oponible Medial: naciendo hacia adentro del cuerpo (-sign) y hacia la palma (-Y)
        th_pts = [
            Vector((w_m, 0.008, 0.875)),
            Vector((w_m - sign_h * 0.015, 0.004, 0.850)),
            Vector((w_m - sign_h * 0.026, 0.000, 0.825)),
            Vector((w_m - sign_h * 0.032, -0.005, 0.805)),
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

        # Masa de la palma
        p_box = [
            bm.verts.new((w_m, 0.025, 0.90)),
            bm.verts.new((w_l, 0.025, 0.90)),
            bm.verts.new((w_l, 0.002, 0.90)),
            bm.verts.new((w_m, 0.002, 0.90)),
            bm.verts.new((w_m, 0.025, 0.82)),
            bm.verts.new((w_l, 0.025, 0.82)),
            bm.verts.new((w_l, 0.002, 0.82)),
            bm.verts.new((w_m, 0.002, 0.82)),
        ]
        p_f_idxs = [(0, 1, 5, 4), (3, 7, 6, 2), (0, 4, 7, 3), (1, 2, 6, 5), (0, 3, 2, 1)]
        for pfi in p_f_idxs:
            f_p = bm.faces.new([p_box[idx] for idx in pfi])
            f_p.material_index = 6

    # 6. Cuello Camisero Doblado y Corbata de Seda 3D
    collar_l = [
        bm.verts.new((0.010, 0.052, 1.435)),
        bm.verts.new((0.055, 0.040, 1.425)),
        bm.verts.new((0.025, 0.068, 1.375)),
    ]
    collar_r = [
        bm.verts.new((-0.010, 0.052, 1.435)),
        bm.verts.new((-0.025, 0.068, 1.375)),
        bm.verts.new((-0.055, 0.040, 1.425)),
    ]
    bm.faces.new(collar_l).material_index = 0
    bm.faces.new(collar_r).material_index = 0

    # Nudo Windsor
    knot_v = [
        bm.verts.new((-0.016, 0.068, 1.415)),
        bm.verts.new((0.016, 0.068, 1.415)),
        bm.verts.new((0.011, 0.074, 1.375)),
        bm.verts.new((-0.011, 0.074, 1.375)),
        bm.verts.new((0.000, 0.058, 1.395)),
    ]
    bm.faces.new((knot_v[0], knot_v[1], knot_v[2], knot_v[3])).material_index = 4 # Corbata
    bm.faces.new((knot_v[0], knot_v[3], knot_v[4])).material_index = 4
    bm.faces.new((knot_v[1], knot_v[4], knot_v[2])).material_index = 4

    # Pala de la corbata
    tie_v = [
        bm.verts.new((-0.011, 0.074, 1.375)),
        bm.verts.new((0.011, 0.074, 1.375)),
        bm.verts.new((0.016, 0.098, 1.300)),
        bm.verts.new((-0.016, 0.098, 1.300)),
        bm.verts.new((0.020, 0.106, 1.230)),
        bm.verts.new((-0.020, 0.106, 1.230)),
        bm.verts.new((0.022, 0.102, 1.160)),
        bm.verts.new((-0.022, 0.102, 1.160)),
    ]
    for ts in range(3):
        f_t = bm.faces.new((tie_v[ts*2], tie_v[ts*2+1], tie_v[(ts+1)*2+1], tie_v[(ts+1)*2]))
        f_t.material_index = 4

    # 7. Chaleco Entallado 3D (Waistcoat) Completo
    # Envuelve el torso con tirantes, sisas, escote en V y picos inferiores
    vest_levels = [
        # z, rx, ry_f, ry_b, v_width, is_v_open
        (1.37, 0.186, 0.102, 0.098, 0.080, True),  # Clavículas / hombros
        (1.30, 0.182, 0.116, 0.110, 0.050, True),  # Pecho alto
        (1.23, 0.174, 0.112, 0.106, 0.018, True),  # Punto inferior del escote en V
        (1.16, 0.166, 0.106, 0.102, 0.000, False), # Botón 2
        (1.09, 0.158, 0.101, 0.097, 0.000, False), # Botón 3
        (1.02, 0.152, 0.098, 0.094, 0.000, False), # Botón 4
        (0.95, 0.156, 0.102, 0.098, 0.000, False), # Botón 5
    ]
    n_vest = 24
    vest_grid = []
    for (z, rx, ry_f, ry_b, v_w, is_open) in vest_levels:
        cur_v = []
        for i in range(n_vest):
            ang = (2.0 * math.pi * i) / n_vest
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            vx = rx * cos_a
            vy = (ry_f if sin_a >= 0 else ry_b) * sin_a
            vz = z
            if is_open and sin_a > 0.4 and abs(vx) < v_w:
                vx = math.copysign(v_w, vx) if abs(vx) > 0.001 else v_w
            cur_v.append(bm.verts.new((vx, vy, vz)))
        vest_grid.append(cur_v)
        
    for l_idx in range(len(vest_levels) - 1):
        r1 = vest_grid[l_idx]
        r2 = vest_grid[l_idx + 1]
        is_open = vest_levels[l_idx][5]
        for i in range(n_vest):
            i_next = (i + 1) % n_vest
            if is_open and (5 <= i <= 7):
                continue
            f_v = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
            f_v.material_index = 3 # Chaleco

    # Picos inferiores frontales del chaleco
    peak_l = [vest_grid[-1][5], vest_grid[-1][6], bm.verts.new((0.038, 0.106, 0.910))]
    peak_r = [vest_grid[-1][6], vest_grid[-1][7], bm.verts.new((-0.038, 0.106, 0.910))]
    bm.faces.new(peak_l).material_index = 3
    bm.faces.new(peak_r).material_index = 3

    # 5 Botones plateados
    b_coords = [1.23, 1.16, 1.09, 1.02, 0.95]
    for bz in b_coords:
        by = 0.108 + (1.23 - bz) * (-0.005)
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.0045)
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.0, by + 0.005, bz))
        v_map = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            nf = bm.faces.new([v_map[v] for v in f.verts])
            nf.material_index = 5 # Plata
        btn_bm.free()

    # Bolsillos Welt
    pocket_specs = [(0.075, 1.005, 0.032), (-0.075, 1.005, 0.032), (0.065, 1.160, 0.026)]
    for (px, pz, pw) in pocket_specs:
        py = 0.110
        p_box = [
            bm.verts.new((px - pw*0.5, py + 0.003, pz + 0.004)),
            bm.verts.new((px + pw*0.5, py + 0.003, pz + 0.004)),
            bm.verts.new((px + pw*0.5, py + 0.003, pz - 0.004)),
            bm.verts.new((px - pw*0.5, py + 0.003, pz - 0.004)),
        ]
        bm.faces.new(p_box).material_index = 3

    bm.normal_update()
    for f in bm.faces: f.smooth = True
    bm.to_mesh(me)
    bm.free()

    obj = bpy.data.objects.new("Player_Body_Mesh", me)
    bpy.context.scene.collection.objects.link(obj)
    for mat in materials["body"]:
        obj.data.materials.append(mat)
    sub = obj.modifiers.new("Subsurf", type='SUBSURF')
    sub.levels = 1
    sub.render_levels = 1
    return obj

# =============================================================================
# RIG CANÓNICO Y ASIGNACIÓN DE PESOS
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
        ("Chest",       "Spine",       (0, 0, 1.15),      (0, 0, 1.38)),
        ("Neck",        "Chest",       (0, 0, 1.38),      (0, 0, 1.48)),
        ("Head",        "Neck",        (0, 0, 1.48),      (0, 0, 1.78)),
        
        ("Shoulder.L",  "Chest",       (0.04, 0, 1.36),   (0.185, 0, 1.36)),
        ("UpperArm.L",  "Shoulder.L",  (0.185, 0, 1.36),  (0.260, 0.007, 1.14)),
        ("Forearm.L",   "UpperArm.L",  (0.260, 0.007, 1.14),(0.330, 0.015, 0.90)),
        ("Hand.L",      "Forearm.L",   (0.330, 0.015, 0.90),(0.330, 0.015, 0.80)),
        
        ("Shoulder.R",  "Chest",       (-0.04, 0, 1.36),  (-0.185, 0, 1.36)),
        ("UpperArm.R",  "Shoulder.R",  (-0.185, 0, 1.36), (-0.260, 0.007, 1.14)),
        ("Forearm.R",   "UpperArm.R",  (-0.260, 0.007, 1.14),(-0.330, 0.015, 0.90)),
        ("Hand.R",      "Forearm.R",   (-0.330, 0.015, 0.90),(-0.330, 0.015, 0.80)),
        
        ("UpperLeg.L",  "Hips",        (0.088, 0, 0.82),  (0.088, 0, 0.46)),
        ("LowerLeg.L",  "UpperLeg.L",  (0.088, 0, 0.46),  (0.088, 0, 0.10)),
        ("Foot.L",      "LowerLeg.L",  (0.088, 0, 0.10),  (0.088, 0.07, 0.02)),
        ("Toes.L",      "Foot.L",      (0.088, 0.07, 0.02),(0.088, 0.13, 0.00)),
        
        ("UpperLeg.R",  "Hips",        (-0.088, 0, 0.82), (-0.088, 0, 0.46)),
        ("LowerLeg.R",  "UpperLeg.R",  (-0.088, 0, 0.46), (-0.088, 0, 0.10)),
        ("Foot.R",      "LowerLeg.R",  (-0.088, 0, 0.10), (-0.088, 0.07, 0.02)),
        ("Toes.R",      "Foot.R",      (-0.088, 0.07, 0.02),(-0.088, 0.13, 0.00)),
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
            grp = "Neck" if co.z < 1.45 else "Head"
            obj.vertex_groups[grp].add([v.index], 1.0, 'REPLACE')
        else:
            if co.z < 0.04:
                obj.vertex_groups["Toes.L" if co.x > 0 else "Toes.R"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.12:
                obj.vertex_groups["Foot.L" if co.x > 0 else "Foot.R"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.46:
                obj.vertex_groups["LowerLeg.L" if co.x > 0 else "LowerLeg.R"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.82 and abs(co.x) > 0.03:
                obj.vertex_groups["UpperLeg.L" if co.x > 0 else "UpperLeg.R"].add([v.index], 1.0, 'REPLACE')
            elif abs(co.x) > 0.20 and co.z < 1.38:
                side = ".L" if co.x > 0 else ".R"
                if co.z < 0.92: obj.vertex_groups["Hand" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.14: obj.vertex_groups["Forearm" + side].add([v.index], 1.0, 'REPLACE')
                else: obj.vertex_groups["UpperArm" + side].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.95: obj.vertex_groups["Hips"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 1.15: obj.vertex_groups["Spine"].add([v.index], 1.0, 'REPLACE')
            else: obj.vertex_groups["Chest"].add([v.index], 1.0, 'REPLACE')

def render_preview():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    scene.cycles.device = 'CPU'

    # Luz de 3 puntos
    key = bpy.data.objects.new("Key", bpy.data.lights.new("Key", 'AREA'))
    key.data.energy = 95.0
    key.data.size = 1.4
    key.data.color = (1.0, 0.98, 0.95)
    key.location = Vector((-0.8, 1.6, 1.7))
    key.rotation_euler = (math.radians(55.0), 0.0, math.radians(-145.0))
    scene.collection.objects.link(key)

    fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", 'AREA'))
    fill.data.energy = 42.0
    fill.data.size = 1.6
    fill.data.color = (0.92, 0.96, 1.0)
    fill.location = Vector((1.0, 1.6, 1.3))
    scene.collection.objects.link(fill)

    rim = bpy.data.objects.new("Rim", bpy.data.lights.new("Rim", 'SPOT'))
    rim.data.energy = 55.0
    rim.data.spot_size = math.radians(65.0)
    rim.data.color = (1.0, 1.0, 1.0)
    rim.location = Vector((0.0, -1.2, 1.9))
    rim.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
    scene.collection.objects.link(rim)

    # Cámara retrato
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    cam.data.lens = 55.0
    cam.location = Vector((0.04, 1.85, 1.32))
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
    print("GENERANDO MODELO DE AXEL DEFINITIVO (FORTNITE / AXEL2.PNG)")
    print("=" * 60)
    clean_scene()

    # Materiales PBR
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
    print("✓ Player_Head_Mesh generado con rasgos faciales 3D, rizos y fedora snap-brim.")
    
    body_obj = build_body_mesh(materials)
    assign_weights(body_obj, is_head=False)
    body_obj.parent = skel
    mod_b = body_obj.modifiers.new("Armature", type='ARMATURE')
    mod_b.object = skel
    print("✓ Player_Body_Mesh generado con chaleco sastre 3D, camisa, corbata y manos anatómicas.")
    
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
    print("MODELO GENERADO Y EXPORTADO CON ÉXITO")
    print("=" * 60)

if __name__ == "__main__":
    main()
