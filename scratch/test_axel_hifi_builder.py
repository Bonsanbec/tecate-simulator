"""
Generador Maestro Hiperrealista / Estilizado de Axel (Tecate Simulator)
Fidelidad comparable a Fortnite (Epic Games), basada estrictamente en la fotografía
de referencia 'scratch/humans/axel2.tiff'.
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

def build_head_mesh(materials):
    me = bpy.data.meshes.new("Player_Head_Mesh_Data")
    bm = bmesh.new()

    # 1. Base Head & Face Topology
    n_ring = 24
    levels = [
        # Z, rx, ry_front, ry_back, y_offset
        (1.30, 0.052, 0.048, 0.052, 0.005), # 0: Base cuello / clavículas
        (1.34, 0.050, 0.046, 0.050, 0.010), # 1: Cuello bajo
        (1.37, 0.048, 0.048, 0.048, 0.015), # 2: Nuez de Adán
        (1.40, 0.052, 0.040, 0.052, 0.012), # 3: Cuello superior / garganta retraída
        (1.412, 0.060, 0.074, 0.062, 0.018),# 4: Mentón prominente y base mandibular
        (1.428, 0.064, 0.066, 0.068, 0.015),# 5: Surco mentolabial
        (1.442, 0.066, 0.076, 0.072, 0.012),# 6: Labio inferior prominente
        (1.455, 0.067, 0.074, 0.074, 0.010),# 7: Comisura labial / línea de boca
        (1.468, 0.068, 0.078, 0.076, 0.008),# 8: Labio superior (arco de Cupido)
        (1.482, 0.069, 0.075, 0.078, 0.005),# 9: Filtrum / base nasal
        (1.498, 0.070, 0.088, 0.080, 0.004),# 10: Punta de la nariz (apex y alas)
        (1.520, 0.072, 0.076, 0.082, 0.002),# 11: Puente nasal / pómulos altos
        (1.542, 0.071, 0.062, 0.084, 0.000),# 12: Cuencas oculares (órbita retraída)
        (1.570, 0.073, 0.066, 0.085, 0.000),# 13: Arco superciliar (cejas prominentes)
        (1.605, 0.074, 0.064, 0.084, -0.002),# 14: Frente media
        (1.645, 0.072, 0.060, 0.080, -0.005),# 15: Frente alta / nacimiento cabello
        (1.680, 0.062, 0.050, 0.068, -0.008),# 16: Bóveda craneal
        (1.705, 0.040, 0.030, 0.045, -0.010),# 17: Coronilla superior
    ]
    
    ring_verts = []
    for l_idx, (z, rx, ry_front, ry_back, y_off) in enumerate(levels):
        current_ring = []
        for i in range(n_ring):
            angle = (2.0 * math.pi * i) / n_ring
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            x = rx * cos_a
            if sin_a >= 0:
                y = ry_front * sin_a + y_off
            else:
                y = ry_back * sin_a + y_off
                
            # Esculpido anatómico
            if l_idx in (9, 10, 11) and 0.4 * math.pi <= angle <= 0.6 * math.pi:
                nose_dist = abs(angle - 0.5 * math.pi)
                nose_weight = max(0.0, 1.0 - nose_dist / 0.25)
                if l_idx == 10:
                    y += 0.014 * nose_weight
                elif l_idx in (9, 11):
                    y += 0.008 * nose_weight
                    
            if l_idx == 4 and 0.35 * math.pi <= angle <= 0.65 * math.pi:
                chin_dist = abs(angle - 0.5 * math.pi)
                chin_weight = max(0.0, 1.0 - chin_dist / 0.35)
                y += 0.012 * chin_weight
                
            if l_idx == 12:
                if (0.28 * math.pi <= angle <= 0.42 * math.pi) or (0.58 * math.pi <= angle <= 0.72 * math.pi):
                    y -= 0.010
                    
            if l_idx in (3, 4) and (abs(cos_a) > 0.8 and sin_a < 0):
                x *= 1.15
                
            v = bm.verts.new((x, y, z))
            current_ring.append(v)
        ring_verts.append(current_ring)
        
    for l_idx in range(len(levels) - 1):
        r1 = ring_verts[l_idx]
        r2 = ring_verts[l_idx + 1]
        for i in range(n_ring):
            i_next = (i + 1) % n_ring
            f = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
            f.material_index = 0 # Mat_Axel_Skin
            
    top_center = bm.verts.new((0, -0.010, 1.715))
    top_ring = ring_verts[-1]
    for i in range(n_ring):
        i_next = (i + 1) % n_ring
        f = bm.faces.new((top_ring[i], top_ring[i_next], top_center))
        f.material_index = 0
        
    bottom_center = bm.verts.new((0, 0.005, 1.295))
    bot_ring = ring_verts[0]
    for i in range(n_ring):
        i_next = (i + 1) % n_ring
        f = bm.faces.new((bot_ring[i_next], bot_ring[i], bottom_center))
        f.material_index = 0

    # 2. Ojos 3D reales
    eye_positions = [(0.033, 0.050, 1.542), (-0.033, 0.050, 1.542)]
    for eye_pos in eye_positions:
        eye_bm = bmesh.new()
        bmesh.ops.create_uvsphere(eye_bm, u_segments=16, v_segments=12, radius=0.0135)
        bmesh.ops.rotate(eye_bm, verts=eye_bm.verts, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(90), 4, 'X'))
        bmesh.ops.translate(eye_bm, verts=eye_bm.verts, vec=eye_pos)
        
        vert_map = {v: bm.verts.new(v.co) for v in eye_bm.verts}
        for f in eye_bm.faces:
            nf = bm.faces.new([vert_map[v] for v in f.verts])
            nf.material_index = 1 # Mat_Axel_Eyes
        eye_bm.free()

    # 3. Orejas esculpidas 3D
    for sign_x in (1.0, -1.0):
        ear_verts = [
            bm.verts.new((sign_x * 0.072, 0.005, 1.545)),
            bm.verts.new((sign_x * 0.082, 0.002, 1.540)),
            bm.verts.new((sign_x * 0.085, -0.010, 1.520)),
            bm.verts.new((sign_x * 0.082, -0.015, 1.490)),
            bm.verts.new((sign_x * 0.074, -0.008, 1.475)),
            bm.verts.new((sign_x * 0.070, 0.002, 1.495)),
            bm.verts.new((sign_x * 0.071, 0.000, 1.525)),
        ]
        f_ear = bm.faces.new(ear_verts)
        f_ear.material_index = 0

    # 4. Rizos Tridimensionales Orgánicos
    curl_specs = [
        (0.000, 0.068, 1.635, 0.003, 0.018, -0.052, 0.009, 2.2, 0.0),
        (0.016, 0.066, 1.632, 0.008, 0.016, -0.055, 0.009, 2.4, 0.8),
        (-0.016, 0.066, 1.632, -0.008, 0.016, -0.055, 0.009, 2.4, 1.5),
        (0.032, 0.062, 1.628, 0.012, 0.014, -0.050, 0.0085, 2.1, 2.2),
        (-0.032, 0.062, 1.628, -0.012, 0.014, -0.050, 0.0085, 2.1, 2.9),
        (0.046, 0.054, 1.625, 0.015, 0.012, -0.048, 0.008, 2.0, 3.7),
        (-0.046, 0.054, 1.625, -0.015, 0.012, -0.048, 0.008, 2.0, 4.4),
        (0.008, 0.065, 1.620, 0.002, 0.012, -0.035, 0.0075, 1.8, 1.2),
        (-0.008, 0.065, 1.620, -0.002, 0.012, -0.035, 0.0075, 1.8, 2.5),
        (0.024, 0.063, 1.618, 0.005, 0.010, -0.032, 0.007, 1.7, 3.4),
        (-0.024, 0.063, 1.618, -0.005, 0.010, -0.032, 0.007, 1.7, 4.8),
        (0.064, 0.025, 1.610, 0.010, 0.005, -0.070, 0.008, 2.5, 0.5),
        (-0.064, 0.025, 1.610, -0.010, 0.005, -0.070, 0.008, 2.5, 1.7),
        (0.068, 0.005, 1.600, 0.008, -0.002, -0.065, 0.0075, 2.3, 2.8),
        (-0.068, 0.005, 1.600, -0.008, -0.002, -0.065, 0.0075, 2.3, 3.9),
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
            
            spiral_cx = c_x + cur_r * math.cos(phase)
            spiral_cy = c_y + cur_r * math.sin(phase)
            spiral_cz = c_z
            
            tube_r = 0.0055 * (1.0 - 0.5 * t)
            cur_ring = []
            for k in range(4):
                k_ang = (2.0 * math.pi * k) / 4.0
                vx = spiral_cx + tube_r * math.cos(k_ang)
                vy = spiral_cy + tube_r * math.sin(k_ang) * 0.5
                vz = spiral_cz + tube_r * math.sin(k_ang) * 0.8
                cur_ring.append(bm.verts.new((vx, vy, vz)))
                
            if prev_ring:
                for k in range(4):
                    k_next = (k + 1) % 4
                    f_hair = bm.faces.new((prev_ring[k], prev_ring[k_next], cur_ring[k_next], cur_ring[k]))
                    f_hair.material_index = 2 # Mat_Axel_Hair
            prev_ring = cur_ring

    # 5. Sombrero Fedora Maestro
    n_hat = 32
    hat_levels = [
        (1.630, 0.088, 0.098, -0.002, 1.00, 0.000), # Base de la corona
        (1.655, 0.086, 0.096, -0.003, 0.96, 0.000), # Cinta grosgrain
        (1.685, 0.083, 0.093, -0.004, 0.90, 0.000), # Corona media
        (1.715, 0.080, 0.090, -0.005, 0.84, 0.000), # Pellizco frontal
        (1.735, 0.076, 0.086, -0.006, 0.78, 0.016), # Cima hendidura gota
    ]
    
    hat_ring_verts = []
    for l_idx, (z, rx, ry, y_c, pinch_x, crease) in enumerate(hat_levels):
        cur_ring = []
        for i in range(n_hat):
            ang = (2.0 * math.pi * i) / n_hat
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            
            cur_rx = rx
            if sin_a > 0:
                cur_rx *= pinch_x
                
            vx = cur_rx * cos_a
            vy = ry * sin_a + y_c
            vz = z
            
            if crease > 0.0:
                center_dist_x = abs(vx) / cur_rx
                if center_dist_x < 0.6:
                    vz -= crease * (1.0 - center_dist_x / 0.6)
                    
            cur_ring.append(bm.verts.new((vx, vy, vz)))
        hat_ring_verts.append(cur_ring)
        
    for l_idx in range(len(hat_levels) - 1):
        r1 = hat_ring_verts[l_idx]
        r2 = hat_ring_verts[l_idx + 1]
        mat_idx = 4 if l_idx == 0 else 3 # 4: Hatband, 3: Fedora
        for i in range(n_hat):
            i_next = (i + 1) % n_hat
            f_hat = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
            f_hat.material_index = mat_idx
            
    top_hat_ring = hat_ring_verts[-1]
    top_hat_center = bm.verts.new((0.0, -0.006, 1.720))
    for i in range(n_hat):
        i_next = (i + 1) % n_hat
        f_top = bm.faces.new((top_hat_ring[i], top_hat_ring[i_next], top_hat_center))
        f_top.material_index = 3 # Fedora
        
    # Ala del sombrero (Snap-Brim)
    base_hat_ring = hat_ring_verts[0]
    brim_mid_ring = []
    brim_outer_ring = []
    
    for i in range(n_hat):
        ang = (2.0 * math.pi * i) / n_hat
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        dip_z = -0.020 * max(0.0, sin_a) + 0.014 * abs(cos_a) + 0.008 * max(0.0, -sin_a)
        
        rm_x = 0.125 * cos_a
        rm_y = 0.138 * sin_a - 0.002
        rm_z = 1.630 + dip_z * 0.5
        brim_mid_ring.append(bm.verts.new((rm_x, rm_y, rm_z)))
        
        ro_x = 0.158 * cos_a
        ro_y = 0.170 * sin_a - 0.002
        ro_z = 1.630 + dip_z
        brim_outer_ring.append(bm.verts.new((ro_x, ro_y, ro_z)))
        
    for i in range(n_hat):
        i_next = (i + 1) % n_hat
        f1 = bm.faces.new((base_hat_ring[i], base_hat_ring[i_next], brim_mid_ring[i_next], brim_mid_ring[i]))
        f2 = bm.faces.new((brim_mid_ring[i], brim_mid_ring[i_next], brim_outer_ring[i_next], brim_outer_ring[i]))
        f1.material_index = 3
        f2.material_index = 3

    bm.normal_update()
    for f in bm.faces:
        f.smooth = True
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

def build_body_mesh(materials):
    me = bpy.data.meshes.new("Player_Body_Mesh_Data")
    bm = bmesh.new()

    # 1. Torso Base (Camisa carbón)
    torso_levels = [
        # z, rx, ry, y_c, mat_idx (0: Shirt, 1: Pants, 2: Shoes, 3: Vest, 4: Tie, 5: Silver, 6: Skin)
        (1.30, 0.170, 0.100, 0.000, 0),
        (1.24, 0.165, 0.105, 0.002, 0),
        (1.18, 0.160, 0.102, 0.000, 0),
        (1.10, 0.152, 0.096, -0.002, 0),
        (1.02, 0.145, 0.092, -0.004, 0),
        (0.95, 0.150, 0.096, -0.002, 1),
        (0.88, 0.158, 0.102, 0.000, 1),
        (0.82, 0.155, 0.098, 0.000, 1),
    ]
    
    n_torso = 24
    torso_ring_verts = []
    for (z, rx, ry, y_c, m_idx) in torso_levels:
        cur_ring = []
        for i in range(n_torso):
            ang = (2.0 * math.pi * i) / n_torso
            vx = rx * math.cos(ang)
            vy = ry * math.sin(ang) + y_c
            vz = z
            cur_ring.append(bm.verts.new((vx, vy, vz)))
        torso_ring_verts.append((cur_ring, m_idx))
        
    for l_idx in range(len(torso_levels) - 1):
        r1, m_idx = torso_ring_verts[l_idx]
        r2, _ = torso_ring_verts[l_idx + 1]
        for i in range(n_torso):
            i_next = (i + 1) % n_torso
            f = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
            f.material_index = m_idx

    top_torso_ring = torso_ring_verts[0][0]
    top_torso_center = bm.verts.new((0, 0, 1.30))
    for i in range(n_torso):
        i_next = (i + 1) % n_torso
        f = bm.faces.new((top_torso_ring[i], top_torso_ring[i_next], top_torso_center))
        f.material_index = 0

    # 2. Piernas y Pantalón con Raya
    leg_levels = [
        (0.82, 0.070, 0.075, 1),
        (0.72, 0.065, 0.068, 1),
        (0.60, 0.058, 0.060, 1),
        (0.48, 0.052, 0.054, 1),
        (0.36, 0.048, 0.050, 1),
        (0.24, 0.045, 0.046, 1),
        (0.12, 0.043, 0.044, 1),
    ]
    n_leg = 16
    for sign_leg in (1.0, -1.0):
        leg_x = sign_leg * 0.088
        leg_rings = []
        for (z, rx, ry, m_idx) in leg_levels:
            cur_ring = []
            for i in range(n_leg):
                ang = (2.0 * math.pi * i) / n_leg
                cos_a = math.cos(ang)
                sin_a = math.sin(ang)
                cur_ry = ry
                if abs(cos_a) < 0.2:
                    cur_ry *= 1.08
                vx = leg_x + rx * cos_a
                vy = cur_ry * sin_a
                vz = z
                cur_ring.append(bm.verts.new((vx, vy, vz)))
            leg_rings.append((cur_ring, m_idx))
            
        for l_idx in range(len(leg_levels) - 1):
            r1, m_idx = leg_rings[l_idx]
            r2, _ = leg_rings[l_idx + 1]
            for i in range(n_leg):
                i_next = (i + 1) % n_leg
                f = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
                f.material_index = m_idx

        # 3. Zapatos de Vestir Oxford
        shoe_levels = [
            (0.10, 0.044, 0.050, 0.045, 0.005),
            (0.06, 0.046, 0.075, 0.048, 0.015),
            (0.03, 0.048, 0.095, 0.050, 0.025),
            (0.00, 0.049, 0.098, 0.052, 0.025),
        ]
        shoe_rings = []
        for (z, rx, ry_f, ry_b, y_off) in shoe_levels:
            cur_ring = []
            for i in range(n_leg):
                ang = (2.0 * math.pi * i) / n_leg
                cos_a = math.cos(ang)
                sin_a = math.sin(ang)
                vx = leg_x + rx * cos_a
                vy = (ry_f if sin_a >= 0 else ry_b) * sin_a + y_off
                vz = z
                cur_ring.append(bm.verts.new((vx, vy, vz)))
            shoe_rings.append(cur_ring)
            
        for l_idx in range(len(shoe_levels) - 1):
            r1 = shoe_rings[l_idx]
            r2 = shoe_rings[l_idx + 1]
            for i in range(n_leg):
                i_next = (i + 1) % n_leg
                f = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
                f.material_index = 2 # Mat_Axel_Shoes
                
        bot_shoe = shoe_rings[-1]
        bot_c = bm.verts.new((leg_x, 0.025, 0.00))
        for i in range(n_leg):
            i_next = (i + 1) % n_leg
            f = bm.faces.new((bot_shoe[i_next], bot_shoe[i], bot_c))
            f.material_index = 2

    # 4. Brazos y Mangas de Camisa
    arm_levels = [
        (0.00, 0.062, 0.060),
        (0.20, 0.055, 0.054),
        (0.40, 0.050, 0.048),
        (0.60, 0.046, 0.045),
        (0.80, 0.042, 0.040),
        (0.95, 0.038, 0.036),
        (1.00, 0.035, 0.032),
    ]
    n_arm = 12
    for sign_arm in (1.0, -1.0):
        p_sh = Vector((sign_arm * 0.175, 0.00, 1.28))
        p_wr = Vector((sign_arm * 0.330, 0.015, 0.86))
        
        arm_rings = []
        for (t, rx, ry) in arm_levels:
            center = p_sh.lerp(p_wr, t)
            if 0.4 <= t <= 0.7:
                center.y -= 0.012 * math.sin((t - 0.4) / 0.3 * math.pi)
                
            cur_ring = []
            for i in range(n_arm):
                ang = (2.0 * math.pi * i) / n_arm
                vx = center.x + rx * math.cos(ang)
                vy = center.y + ry * math.sin(ang)
                vz = center.z
                cur_ring.append(bm.verts.new((vx, vy, vz)))
            arm_rings.append(cur_ring)
            
        for l_idx in range(len(arm_levels) - 1):
            r1 = arm_rings[l_idx]
            r2 = arm_rings[l_idx + 1]
            for i in range(n_arm):
                i_next = (i + 1) % n_arm
                f = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
                f.material_index = 0 # Mat_Axel_Shirt

    # 5. Manos Anatómicas con Pulgar Oponible Medial y Anillos
    for is_left in (True, False):
        sign_h = 1.0 if is_left else -1.0
        w_m = sign_h * 0.295 # medial (pulgar)
        w_l = sign_h * 0.365 # lateral (meñique)
        
        finger_specs = [
            ("Index",  0.22, 0.075, 0.0065),
            ("Middle", 0.45, 0.082, 0.0070),
            ("Ring",   0.68, 0.076, 0.0065),
            ("Little", 0.90, 0.065, 0.0055),
        ]
        
        for (f_name, f_frac, f_len, f_rad) in finger_specs:
            f_x = w_m + (w_l - w_m) * f_frac
            base_z = 0.77
            base_y = 0.014
            
            p_joint = [
                Vector((f_x, base_y, base_z)),
                Vector((f_x, base_y - 0.004, base_z - f_len * 0.40)),
                Vector((f_x, base_y - 0.010, base_z - f_len * 0.75)),
                Vector((f_x, base_y - 0.015, base_z - f_len * 1.00)),
            ]
            
            prev_f_ring = None
            for j_idx, pt in enumerate(p_joint):
                cur_r = f_rad * (1.0 - 0.25 * (j_idx / 3.0))
                cur_f_ring = [
                    bm.verts.new((pt.x - cur_r, pt.y, pt.z)),
                    bm.verts.new((pt.x, pt.y + cur_r, pt.z)),
                    bm.verts.new((pt.x + cur_r, pt.y, pt.z)),
                    bm.verts.new((pt.x, pt.y - cur_r, pt.z)),
                ]
                if prev_f_ring:
                    for k in range(4):
                        k_next = (k + 1) % 4
                        f_seg = bm.faces.new((prev_f_ring[k], prev_f_ring[k_next], cur_f_ring[k_next], cur_f_ring[k]))
                        f_seg.material_index = 6 # Skin
                prev_f_ring = cur_f_ring
                
            tip_v = bm.verts.new((p_joint[-1].x, p_joint[-1].y - 0.003, p_joint[-1].z - 0.004))
            for k in range(4):
                k_next = (k + 1) % 4
                f_tip = bm.faces.new((prev_f_ring[k_next], prev_f_ring[k], tip_v))
                f_tip.material_index = 6
                
            # Anillos de Plata de Axel en mano izquierda
            if is_left and f_name in ("Index", "Middle"):
                ring_z_center = base_z - f_len * 0.20
                ring_rad = f_rad * 1.18
                ring_r1 = []
                ring_r2 = []
                for k in range(8):
                    ang_r = (2.0 * math.pi * k) / 8.0
                    rx = f_x + ring_rad * math.cos(ang_r)
                    ry = (base_y - 0.002) + ring_rad * math.sin(ang_r)
                    ring_r1.append(bm.verts.new((rx, ry, ring_z_center + 0.003)))
                    ring_r2.append(bm.verts.new((rx, ry, ring_z_center - 0.003)))
                for k in range(8):
                    k_next = (k + 1) % 8
                    f_ring = bm.faces.new((ring_r1[k], ring_r1[k_next], ring_r2[k_next], ring_r2[k]))
                    f_ring.material_index = 5 # Silver

        # Pulgar Oponible Medial Curvado hacia la Palma
        th_base_x = w_m
        th_base_y = 0.008
        th_base_z = 0.835
        
        th_pts = [
            Vector((th_base_x, th_base_y, th_base_z)),
            Vector((th_base_x - sign_h * 0.015, th_base_y - 0.004, th_base_z - 0.022)),
            Vector((th_base_x - sign_h * 0.026, th_base_y - 0.008, th_base_z - 0.045)),
            Vector((th_base_x - sign_h * 0.032, th_base_y - 0.012, th_base_z - 0.065)),
        ]
        
        prev_th_ring = None
        for j_idx, pt in enumerate(th_pts):
            th_r = 0.0075 * (1.0 - 0.20 * (j_idx / 3.0))
            cur_th_ring = [
                bm.verts.new((pt.x - th_r, pt.y, pt.z)),
                bm.verts.new((pt.x, pt.y + th_r, pt.z)),
                bm.verts.new((pt.x + th_r, pt.y, pt.z)),
                bm.verts.new((pt.x, pt.y - th_r, pt.z)),
            ]
            if prev_th_ring:
                for k in range(4):
                    k_next = (k + 1) % 4
                    f_th = bm.faces.new((prev_th_ring[k], prev_th_ring[k_next], cur_th_ring[k_next], cur_th_ring[k]))
                    f_th.material_index = 6 # Skin
            prev_th_ring = cur_th_ring
            
        tip_th = bm.verts.new((th_pts[-1].x - sign_h * 0.003, th_pts[-1].y - 0.004, th_pts[-1].z - 0.004))
        for k in range(4):
            k_next = (k + 1) % 4
            f_tip_th = bm.faces.new((prev_th_ring[k_next], prev_th_ring[k], tip_th))
            f_tip_th.material_index = 6

        # Bloque de la Palma
        palm_box_verts = [
            bm.verts.new((w_m, 0.025, 0.86)),
            bm.verts.new((w_l, 0.025, 0.86)),
            bm.verts.new((w_l, 0.002, 0.86)),
            bm.verts.new((w_m, 0.002, 0.86)),
            bm.verts.new((w_m, 0.025, 0.77)),
            bm.verts.new((w_l, 0.025, 0.77)),
            bm.verts.new((w_l, 0.002, 0.77)),
            bm.verts.new((w_m, 0.002, 0.77)),
        ]
        p_faces = [
            (0, 1, 5, 4),
            (3, 7, 6, 2),
            (0, 4, 7, 3),
            (1, 2, 6, 5),
            (0, 3, 2, 1),
        ]
        for pf in p_faces:
            f_p = bm.faces.new([palm_box_verts[idx] for idx in pf])
            f_p.material_index = 6

    # 6. Cuello Camisero y Corbata de Seda 3D
    collar_l = [
        bm.verts.new((0.010, 0.052, 1.345)),
        bm.verts.new((0.055, 0.040, 1.335)),
        bm.verts.new((0.025, 0.068, 1.285)),
    ]
    collar_r = [
        bm.verts.new((-0.010, 0.052, 1.345)),
        bm.verts.new((-0.025, 0.068, 1.285)),
        bm.verts.new((-0.055, 0.040, 1.335)),
    ]
    f_cl = bm.faces.new(collar_l)
    f_cr = bm.faces.new(collar_r)
    f_cl.material_index = 0
    f_cr.material_index = 0

    knot_verts = [
        bm.verts.new((-0.016, 0.068, 1.325)),
        bm.verts.new((0.016, 0.068, 1.325)),
        bm.verts.new((0.011, 0.074, 1.285)),
        bm.verts.new((-0.011, 0.074, 1.285)),
        bm.verts.new((0.000, 0.058, 1.305)),
    ]
    bm.faces.new((knot_verts[0], knot_verts[1], knot_verts[2], knot_verts[3])).material_index = 4 # Tie
    bm.faces.new((knot_verts[0], knot_verts[3], knot_verts[4])).material_index = 4
    bm.faces.new((knot_verts[1], knot_verts[4], knot_verts[2])).material_index = 4

    tie_blade_verts = [
        bm.verts.new((-0.011, 0.074, 1.285)),
        bm.verts.new((0.011, 0.074, 1.285)),
        bm.verts.new((0.016, 0.098, 1.210)),
        bm.verts.new((-0.016, 0.098, 1.210)),
        bm.verts.new((0.020, 0.106, 1.140)),
        bm.verts.new((-0.020, 0.106, 1.140)),
        bm.verts.new((0.022, 0.102, 1.070)),
        bm.verts.new((-0.022, 0.102, 1.070)),
    ]
    for t_step in range(3):
        v1 = tie_blade_verts[t_step * 2]
        v2 = tie_blade_verts[t_step * 2 + 1]
        v3 = tie_blade_verts[(t_step + 1) * 2 + 1]
        v4 = tie_blade_verts[(t_step + 1) * 2]
        bm.faces.new((v1, v2, v3, v4)).material_index = 4

    # 7. Chaleco Entallado 3D (Waistcoat)
    vest_z_levels = [
        (1.28, 0.170, 0.110, 0.104, 0.075, True),
        (1.22, 0.168, 0.114, 0.108, 0.048, True),
        (1.16, 0.164, 0.112, 0.105, 0.015, True),
        (1.10, 0.158, 0.105, 0.101, 0.000, False),
        (1.04, 0.151, 0.101, 0.097, 0.000, False),
        (0.98, 0.153, 0.103, 0.099, 0.000, False),
        (0.93, 0.156, 0.105, 0.101, 0.000, False),
    ]
    
    n_vest = 24
    vest_grid = []
    
    for l_idx, (z, rx, ry_f, ry_b, v_w, is_open) in enumerate(vest_z_levels):
        cur_level_verts = []
        for i in range(n_vest):
            ang = (2.0 * math.pi * i) / n_vest
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            
            vx = rx * cos_a
            vy = (ry_f if sin_a >= 0 else ry_b) * sin_a
            vz = z
            
            if is_open and sin_a > 0.4 and abs(vx) < v_w:
                vx = math.copysign(v_w, vx) if abs(vx) > 0.001 else v_w
                
            cur_level_verts.append(bm.verts.new((vx, vy, vz)))
        vest_grid.append(cur_level_verts)
        
    for l_idx in range(len(vest_z_levels) - 1):
        r1 = vest_grid[l_idx]
        r2 = vest_grid[l_idx + 1]
        is_open = vest_z_levels[l_idx][5]
        for i in range(n_vest):
            i_next = (i + 1) % n_vest
            if is_open and (5 <= i <= 7):
                continue
            f_v = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
            f_v.material_index = 3 # Vest

    peak_l = [
        vest_grid[-1][5],
        vest_grid[-1][6],
        bm.verts.new((0.038, 0.106, 0.895)),
    ]
    peak_r = [
        vest_grid[-1][6],
        vest_grid[-1][7],
        bm.verts.new((-0.038, 0.106, 0.895)),
    ]
    bm.faces.new(peak_l).material_index = 3
    bm.faces.new(peak_r).material_index = 3

    # Botones Plateados
    button_z_coords = [1.16, 1.10, 1.04, 0.98, 0.93]
    for b_z in button_z_coords:
        btn_y = 0.105 + (1.16 - b_z) * (-0.005)
        btn_bm = bmesh.new()
        bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.0045)
        bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.0, btn_y + 0.005, b_z))
        v_map = {v: bm.verts.new(v.co) for v in btn_bm.verts}
        for f in btn_bm.faces:
            nf = bm.faces.new([v_map[v] for v in f.verts])
            nf.material_index = 5 # Silver
        btn_bm.free()

    # Bolsillos Welt
    pocket_specs = [
        (0.075, 0.985, 0.032),
        (-0.075, 0.985, 0.032),
        (0.065, 1.140, 0.026),
    ]
    for (px, pz, pw) in pocket_specs:
        py = 0.108
        p_box = [
            bm.verts.new((px - pw*0.5, py + 0.003, pz + 0.004)),
            bm.verts.new((px + pw*0.5, py + 0.003, pz + 0.004)),
            bm.verts.new((px + pw*0.5, py + 0.003, pz - 0.004)),
            bm.verts.new((px - pw*0.5, py + 0.003, pz - 0.004)),
        ]
        bm.faces.new(p_box).material_index = 3

    bm.normal_update()
    for f in bm.faces:
        f.smooth = True
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
        ("Spine",       "Hips",        (0, 0, 0.95),      (0, 0, 1.12)),
        ("Chest",       "Spine",       (0, 0, 1.12),      (0, 0, 1.30)),
        ("Neck",        "Chest",       (0, 0, 1.30),      (0, 0, 1.40)),
        ("Head",        "Neck",        (0, 0, 1.40),      (0, 0, 1.72)),
        
        ("Shoulder.L",  "Chest",       (0.04, 0, 1.28),   (0.175, 0, 1.28)),
        ("UpperArm.L",  "Shoulder.L",  (0.175, 0, 1.28),  (0.250, 0.007, 1.07)),
        ("Forearm.L",   "UpperArm.L",  (0.250, 0.007, 1.07),(0.330, 0.015, 0.86)),
        ("Hand.L",      "Forearm.L",   (0.330, 0.015, 0.86),(0.330, 0.015, 0.76)),
        
        ("Shoulder.R",  "Chest",       (-0.04, 0, 1.28),  (-0.175, 0, 1.28)),
        ("UpperArm.R",  "Shoulder.R",  (-0.175, 0, 1.28), (-0.250, 0.007, 1.07)),
        ("Forearm.R",   "UpperArm.R",  (-0.250, 0.007, 1.07),(-0.330, 0.015, 0.86)),
        ("Hand.R",      "Forearm.R",   (-0.330, 0.015, 0.86),(-0.330, 0.015, 0.76)),
        
        ("UpperLeg.L",  "Hips",        (0.088, 0, 0.82),  (0.088, 0, 0.48)),
        ("LowerLeg.L",  "UpperLeg.L",  (0.088, 0, 0.48),  (0.088, 0, 0.10)),
        ("Foot.L",      "LowerLeg.L",  (0.088, 0, 0.10),  (0.088, 0.07, 0.02)),
        ("Toes.L",      "Foot.L",      (0.088, 0.07, 0.02),(0.088, 0.13, 0.00)),
        
        ("UpperLeg.R",  "Hips",        (-0.088, 0, 0.82), (-0.088, 0, 0.48)),
        ("LowerLeg.R",  "UpperLeg.R",  (-0.088, 0, 0.48), (-0.088, 0, 0.10)),
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
        if parent:
            created[name].parent = created[parent]
            
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

def assign_vertex_weights(obj, is_head=False):
    bone_names = [
        "Root", "Hips", "Spine", "Chest", "Neck", "Head",
        "Shoulder.L", "UpperArm.L", "Forearm.L", "Hand.L",
        "Shoulder.R", "UpperArm.R", "Forearm.R", "Hand.R",
        "UpperLeg.L", "LowerLeg.L", "Foot.L", "Toes.L",
        "UpperLeg.R", "LowerLeg.R", "Foot.R", "Toes.R"
    ]
    for b_name in bone_names:
        if b_name not in obj.vertex_groups:
            obj.vertex_groups.new(name=b_name)
            
    mesh = obj.data
    for v in mesh.vertices:
        co = v.co
        if is_head:
            if co.z < 1.34:
                obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')
            else:
                obj.vertex_groups["Head"].add([v.index], 1.0, 'REPLACE')
        else:
            if co.z < 0.04:
                grp = "Toes.L" if co.x > 0 else "Toes.R"
                obj.vertex_groups[grp].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.12:
                grp = "Foot.L" if co.x > 0 else "Foot.R"
                obj.vertex_groups[grp].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.48:
                grp = "LowerLeg.L" if co.x > 0 else "LowerLeg.R"
                obj.vertex_groups[grp].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.82 and abs(co.x) > 0.03:
                grp = "UpperLeg.L" if co.x > 0 else "UpperLeg.R"
                obj.vertex_groups[grp].add([v.index], 1.0, 'REPLACE')
            elif abs(co.x) > 0.20 and co.z < 1.30:
                side = ".L" if co.x > 0 else ".R"
                if co.z < 0.88:
                    obj.vertex_groups["Hand" + side].add([v.index], 1.0, 'REPLACE')
                elif co.z < 1.07:
                    obj.vertex_groups["Forearm" + side].add([v.index], 1.0, 'REPLACE')
                else:
                    obj.vertex_groups["UpperArm" + side].add([v.index], 1.0, 'REPLACE')
            elif co.z < 0.95:
                obj.vertex_groups["Hips"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 1.12:
                obj.vertex_groups["Spine"].add([v.index], 1.0, 'REPLACE')
            else:
                obj.vertex_groups["Chest"].add([v.index], 1.0, 'REPLACE')

def render_preview():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    scene.cycles.device = 'CPU'
    
    # Luz Clave
    key_data = bpy.data.lights.new("KeyLight", type='AREA')
    key_data.energy = 85.0
    key_data.size = 1.4
    key_data.color = (1.0, 0.98, 0.95)
    key_obj = bpy.data.objects.new("KeyLight", key_data)
    key_obj.location = Vector((-0.8, 1.5, 1.7))
    key_obj.rotation_euler = (math.radians(55.0), 0.0, math.radians(-145.0))
    scene.collection.objects.link(key_obj)

    # Luz de Relleno
    fill_data = bpy.data.lights.new("FillLight", type='AREA')
    fill_data.energy = 38.0
    fill_data.size = 1.6
    fill_data.color = (0.92, 0.96, 1.0)
    fill_obj = bpy.data.objects.new("FillLight", fill_data)
    fill_obj.location = Vector((1.0, 1.5, 1.3))
    scene.collection.objects.link(fill_obj)

    # Luz Rim posterior
    rim_data = bpy.data.lights.new("RimLight", type='SPOT')
    rim_data.energy = 45.0
    rim_data.spot_size = math.radians(65.0)
    rim_data.color = (1.0, 1.0, 1.0)
    rim_obj = bpy.data.objects.new("RimLight", rim_data)
    rim_obj.location = Vector((0.0, -1.2, 1.9))
    rim_obj.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
    scene.collection.objects.link(rim_obj)

    # Cámara
    cam_data = bpy.data.cameras.new("Camera_Preview")
    cam_data.lens = 55.0
    cam_obj = bpy.data.objects.new("Camera_Preview", cam_data)
    cam_obj.location = Vector((0.05, 1.85, 1.25))
    cam_obj.rotation_euler = (math.radians(88.5), 0.0, math.radians(178.0))
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    scene.render.resolution_x = 720
    scene.render.resolution_y = 1280
    scene.render.filepath = PREVIEW_PNG
    scene.render.image_settings.file_format = 'PNG'

    bpy.ops.render.render(write_still=True)
    print(f"✓ Render preview guardado en: {PREVIEW_PNG}")

def main():
    print("=" * 60)
    print("GENERANDO AXEL HIFI MASTER (ESTILO FORTNITE / AXEL2.PNG)")
    print("=" * 60)
    clean_scene()

    # Materiales PBR
    mat_skin = create_pbr_material("Mat_Axel_Skin", (0.80, 0.63, 0.52, 1.0), roughness=0.52,
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
    print("✓ Esqueleto canónico de 22 huesos generado.")
    
    head_obj = build_head_mesh(materials)
    assign_vertex_weights(head_obj, is_head=True)
    head_obj.parent = skel
    mod_h = head_obj.modifiers.new("Armature", type='ARMATURE')
    mod_h.object = skel
    print("✓ Player_Head_Mesh generado con rasgos faciales 3D, rizos y fedora.")
    
    body_obj = build_body_mesh(materials)
    assign_vertex_weights(body_obj, is_head=False)
    body_obj.parent = skel
    mod_b = body_obj.modifiers.new("Armature", type='ARMATURE')
    mod_b.object = skel
    print("✓ Player_Body_Mesh generado con chaleco entallado 3D, camisa, corbata y manos anatómicas.")
    
    os.makedirs(os.path.dirname(OUTPUT_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
    print(f"✓ Guardado .blend maestro en: {OUTPUT_BLEND}")
    
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
