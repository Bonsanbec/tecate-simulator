"""
=============================================================================
Axel V6: Anatomía Humana Hiperrealista Estilizada (Fortnite / AAA)
=============================================================================
Proporciones anatómicas correctas (1.75 m):
- Cuello proporcionado atlético (longitud 8 cm, de Z=1.40 a 1.48) con trapecios y nuez de Adán.
- Hombros continuos integrados con el torso y brazos (sin cortes ni cilindros flotantes).
- Pelvis y entrepierna continuas conectadas a las piernas y pantalones (sin huecos).
- Rostro esculpido masculino de Axel (axel2.tiff): pómulos altos, mandíbula cuadrada con perilla,
  nariz recta con aletas y punta esculpida, labios carnosos con arco de Cupido, ojos almendrados
  con párpados 3D y orejas completas.
- Cabello rizado 3D en racimos orgánicos bajo el sombrero fedora.
- Sombrero fedora negro de ala ancha con pellizco frontal (pinch front) y hendidura en lágrima.
- Chaleco sastre gris perla/blanco entallado con solapa en V, 5 botones plateados, picos inferiores
  y bolsillos de ribete.
- Camisa carbón oscura con cuello doblado y corbata de seda con nudo 3D y franjas diagonales.
- Pantalón sastre con raya diplomática continua hasta los zapatos de cuero negro.
- Manos anatómicas conectadas a las mangas, con dorso al frente (+Y), palma atrás (-Y),
  pulgares oponibles hacia el interior y 4 dedos escalonados con curvatura relajada.
=============================================================================
"""

import os
import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler, Quaternion

TEX_DIR = os.path.abspath("godot_project/assets/characters/textures")
OUTPUT_BLEND = os.path.abspath("godot_project/assets/characters/citizens/axel.blend")
OUTPUT_GLB = os.path.abspath("godot_project/assets/characters/citizens/axel.glb")
PREVIEW_PNG = os.path.abspath("godot_project/assets/characters/axel_preview.png")

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

def clampf(v, min_v, max_v):
    return max(min_v, min(v, max_v))

def create_pbr_material(name, base_color=(1, 1, 1, 1), roughness=0.5, metallic=0.0,
                        tex_diffuse_path=None, tex_normal_path=None, sss_weight=0.0):
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
    
    if sss_weight > 0.0:
        if 'Subsurface Weight' in node_bsdf.inputs:
            node_bsdf.inputs['Subsurface Weight'].default_value = sss_weight
        elif 'Subsurface' in node_bsdf.inputs:
            node_bsdf.inputs['Subsurface'].default_value = sss_weight
        if 'Subsurface Radius' in node_bsdf.inputs:
            node_bsdf.inputs['Subsurface Radius'].default_value = (0.04, 0.02, 0.01)
            
    if tex_diffuse_path and os.path.exists(tex_diffuse_path):
        tex_img = bpy.data.images.load(tex_diffuse_path)
        node_tex = nodes.new(type='ShaderNodeTexImage')
        node_tex.image = tex_img
        links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
        
    if tex_normal_path and os.path.exists(tex_normal_path):
        norm_img = bpy.data.images.load(tex_normal_path)
        norm_img.colorspace_settings.name = 'Non-Color'
        node_norm_img = nodes.new(type='ShaderNodeTexImage')
        node_norm_img.image = norm_img
        node_norm_map = nodes.new(type='ShaderNodeNormalMap')
        node_norm_map.inputs['Strength'].default_value = 1.0
        links.new(node_norm_img.outputs['Color'], node_norm_map.inputs['Color'])
        links.new(node_norm_map.outputs['Normal'], node_bsdf.inputs['Normal'])
        
    return mat

def build_axel_armature():
    arm_data = bpy.data.armatures.new("Armature_Humanoid_Data")
    arm_data.display_type = 'OCTAHEDRAL'
    arm_obj = bpy.data.objects.new("Armature_Humanoid", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj

    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = arm_data.edit_bones

    b_root = edit_bones.new("Root")
    b_root.head = Vector((0.0, 0.0, 0.0))
    b_root.tail = Vector((0.0, 0.0, 0.15))

    b_hips = edit_bones.new("Hips")
    b_hips.parent = b_root
    b_hips.head = Vector((0.0, 0.0, 0.86))
    b_hips.tail = Vector((0.0, 0.0, 1.00))

    b_spine = edit_bones.new("Spine")
    b_spine.parent = b_hips
    b_spine.head = Vector((0.0, 0.0, 1.00))
    b_spine.tail = Vector((0.0, 0.0, 1.15))

    b_spine1 = edit_bones.new("Spine1")
    b_spine1.parent = b_spine
    b_spine1.head = Vector((0.0, 0.0, 1.15))
    b_spine1.tail = Vector((0.0, 0.0, 1.28))

    b_chest = edit_bones.new("Chest")
    b_chest.parent = b_spine1
    b_chest.head = Vector((0.0, 0.0, 1.28))
    b_chest.tail = Vector((0.0, 0.0, 1.38))

    b_neck = edit_bones.new("Neck")
    b_neck.parent = b_chest
    b_neck.head = Vector((0.0, 0.0, 1.38))
    b_neck.tail = Vector((0.0, 0.0, 1.46))

    b_head = edit_bones.new("Head")
    b_head.parent = b_neck
    b_head.head = Vector((0.0, 0.0, 1.46))
    b_head.tail = Vector((0.0, 0.0, 1.70))

    for side, sign_x in [(".L", -1.0), (".R", 1.0)]:
        b_sh = edit_bones.new(f"Shoulder{side}")
        b_sh.parent = b_chest
        b_sh.head = Vector((sign_x * 0.04, 0.0, 1.37))
        b_sh.tail = Vector((sign_x * 0.18, 0.0, 1.35))

        b_uarm = edit_bones.new(f"UpperArm{side}")
        b_uarm.parent = b_sh
        b_uarm.head = Vector((sign_x * 0.18, 0.0, 1.35))
        b_uarm.tail = Vector((sign_x * 0.28, 0.0, 1.14))

        b_farm = edit_bones.new(f"Forearm{side}")
        b_farm.parent = b_uarm
        b_farm.head = Vector((sign_x * 0.28, 0.0, 1.14))
        b_farm.tail = Vector((sign_x * 0.35, 0.0, 0.94))

        b_hand = edit_bones.new(f"Hand{side}")
        b_hand.parent = b_farm
        b_hand.head = Vector((sign_x * 0.35, 0.0, 0.94))
        b_hand.tail = Vector((sign_x * 0.37, 0.0, 0.82))

        b_uleg = edit_bones.new(f"UpperLeg{side}")
        b_uleg.parent = b_hips
        b_uleg.head = Vector((sign_x * 0.09, 0.0, 0.84))
        b_uleg.tail = Vector((sign_x * 0.10, 0.0, 0.48))

        b_lleg = edit_bones.new(f"LowerLeg{side}")
        b_lleg.parent = b_uleg
        b_lleg.head = Vector((sign_x * 0.10, 0.0, 0.48))
        b_lleg.tail = Vector((sign_x * 0.10, 0.0, 0.12))

        b_foot = edit_bones.new(f"Foot{side}")
        b_foot.parent = b_lleg
        b_foot.head = Vector((sign_x * 0.10, 0.0, 0.12))
        b_foot.tail = Vector((sign_x * 0.10, 0.08, 0.03))

        b_toes = edit_bones.new(f"Toes{side}")
        b_toes.parent = b_foot
        b_toes.head = Vector((sign_x * 0.10, 0.08, 0.03))
        b_toes.tail = Vector((sign_x * 0.10, 0.14, 0.01))

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

# =============================================================================
# CABEZA, ROSTRO, RIZOS Y SOMBRERO (Player_Head_Mesh)
# =============================================================================
def build_head_mesh(arm_obj, mat_skin, mat_hat, mat_hair, mat_eyes):
    mesh = bpy.data.meshes.new("Player_Head_Mesh_Data")
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    # Coordenadas antropométricas corregidas de Axel:
    # Cuello base: Z = 1.38 a 1.46 (encaja dentro del cuello de la camisa Z = 1.39)
    # Mandíbula / barbilla: Z = 1.47 a 1.51
    # Boca / labios: Z = 1.515 a 1.530
    # Nariz: Z = 1.535 a 1.580
    # Ojos y cuencas: Z = 1.575 a 1.595
    # Cejas: Z = 1.605
    # Frente y cráneo: Z = 1.615 a 1.690
    
    v_rings = 36
    u_segs = 32
    grid = []

    for vi in range(v_rings + 1):
        tv = vi / float(v_rings)
        
        if tv < 0.22: # Cuello atlético (1.39 a 1.47) - 8 cm de longitud real
            tn = tv / 0.22
            z = 1.390 + tn * 0.080
            rx = 0.048 + tn * 0.005
            ry_f = 0.050 + tn * 0.008
            ry_b = 0.048 + tn * 0.006
            yc = 0.002
        elif tv < 0.46: # Mandíbula, mentón, boca (1.47 a 1.535)
            tj = (tv - 0.22) / 0.24
            z = 1.470 + tj * 0.065
            rx = 0.053 + tj * 0.016
            ry_f = 0.058 + tj * 0.018
            ry_b = 0.054 + tj * 0.014
            yc = 0.001
        elif tv < 0.72: # Nariz, pómulos, ojos (1.535 a 1.605)
            tm = (tv - 0.46) / 0.26
            z = 1.535 + tm * 0.070
            rx = 0.069 + tm * 0.005
            ry_f = 0.076 + tm * 0.002
            ry_b = 0.068 + tm * 0.008
            yc = 0.0
        else: # Frente y cráneo (1.605 a 1.690)
            tt = (tv - 0.72) / 0.28
            z = 1.605 + tt * 0.085
            dome = math.sqrt(max(0.01, 1.0 - (tt * 0.94)**2))
            rx = 0.074 * dome + 0.002
            ry_f = 0.078 * dome + 0.002
            ry_b = 0.076 * dome + 0.002
            yc = -0.006 * tt

        ring = []
        for ui in range(u_segs):
            ang = (ui / float(u_segs)) * 2.0 * math.pi - (math.pi / 2.0)
            sin_a = math.sin(ang)
            cos_a = math.cos(ang)
            vx = cos_a * rx
            vy = yc + (sin_a * ry_f if sin_a >= 0 else sin_a * ry_b)
            vz = z

            if sin_a > 0: # Cara anterior (+Y)
                # Nuez de Adán en cuello anterior
                if abs(vz - 1.435) < 0.015 and abs(vx) < 0.012:
                    vy += 0.008 * (1.0 - abs(vx) / 0.012) * (1.0 - abs(vz - 1.435) / 0.015)
                    
                # Mentón masculino esculpido cuadrado con perilla (Z = 1.485)
                if abs(vz - 1.485) < 0.020 and abs(vx) < 0.025:
                    cd = math.sqrt((vx / 0.025)**2 + ((vz - 1.485) / 0.020)**2)
                    if cd < 1.0:
                        vy += 0.022 * (1.0 - cd)**1.6
                        if abs(vx) < 0.005 and abs(vz - 1.485) < 0.010:
                            vy -= 0.003
                            
                # Surco mentolabial
                if abs(vz - 1.503) < 0.008 and abs(vx) < 0.020:
                    vy -= 0.005 * (1.0 - abs(vx) / 0.020)
                    
                # Labios con arco de Cupido (Z = 1.512 a 1.530)
                if 1.508 < vz < 1.532 and abs(vx) < 0.026:
                    tlip = (vz - 1.508) / 0.024
                    w_lip = 0.025 * (1.0 - abs(tlip - 0.5) * 1.4)
                    if abs(vx) < max(0.004, w_lip):
                        cupid_dip = 0.003 if (tlip > 0.6 and abs(vx) < 0.005) else 0.0
                        vy += (0.012 * math.sin(tlip * math.pi) - cupid_dip) * (1.0 - abs(vx) / max(0.004, w_lip))
                        
                # Filtrum
                if 1.530 <= vz <= 1.545 and abs(vx) < 0.007:
                    vy -= 0.003 * (1.0 - abs(vx) / 0.007)
                    
                # Nariz esculpida (Z = 1.540 a 1.585)
                if 1.540 < vz < 1.585 and abs(vx) < 0.020:
                    tn = (vz - 1.540) / 0.045
                    if tn < 0.35: # Punta y aletas
                        if abs(vx) < 0.010:
                            vy += 0.026 * (1.0 - abs(vx) / 0.010) * math.sin((tn / 0.35) * math.pi)
                        elif abs(vx) < 0.018:
                            vy += 0.013 * (1.0 - abs(abs(vx) - 0.014) / 0.005) * math.sin((tn / 0.35) * math.pi)
                    else: # Puente recto
                        nw = 0.007 + (1.0 - tn) * 0.004
                        if abs(vx) < nw:
                            vy += (0.020 - tn * 0.005) * (1.0 - abs(vx) / nw)**1.2
                            
                # Pómulos altos (Z = 1.555 a 1.580)
                for cx in [-0.046, 0.046]:
                    dc = math.sqrt(((vx - cx) / 0.020)**2 + ((vz - 1.568) / 0.016)**2)
                    if dc < 1.0:
                        vy += 0.010 * (1.0 - dc)**2
                        
                # Cuencas orbitarias profundas (Z = 1.575)
                for ex in [-0.033, 0.033]:
                    de = math.sqrt(((vx - ex) / 0.018)**2 + ((vz - 1.575) / 0.014)**2)
                    if de < 1.0:
                        vy -= 0.015 * (1.0 - de)**2
                        
                # Arco superciliar / cejas (Z = 1.595)
                if 1.588 < vz < 1.605 and abs(vx) < 0.052:
                    tbrow = 1.0 - (abs(vz - 1.596) / 0.008)
                    vy += 0.011 * tbrow * (1.0 - (abs(vx) / 0.052)**2)

            ring.append(bm.verts.new(Vector((vx, vy, vz))))
        grid.append(ring)

    # Conectar caras cilíndricas faciales
    for vi in range(v_rings):
        r0 = grid[vi]
        r1 = grid[vi + 1]
        v_coord0 = vi / float(v_rings)
        v_coord1 = (vi + 1) / float(v_rings)
        for ui in range(u_segs):
            un = (ui + 1) % u_segs
            f = bm.faces.new([r0[ui], r0[un], r1[un], r1[ui]])
            f.material_index = 0 # mat_skin
            
            u0 = 0.5 + math.atan2(r0[ui].co.x, max(0.001, r0[ui].co.y)) / (2.0 * math.pi)
            u1 = 0.5 + math.atan2(r0[un].co.x, max(0.001, r0[un].co.y)) / (2.0 * math.pi)
            u2 = 0.5 + math.atan2(r1[un].co.x, max(0.001, r1[un].co.y)) / (2.0 * math.pi)
            u3 = 0.5 + math.atan2(r1[ui].co.x, max(0.001, r1[ui].co.y)) / (2.0 * math.pi)
            
            for lp, u_val, v_val in zip(f.loops, [u0, u1, u2, u3], [v_coord0, v_coord0, v_coord1, v_coord1]):
                lp[uv_layer].uv = Vector((clampf(u_val, 0.0, 1.0), clampf(v_val, 0.0, 1.0)))

    # Cierre de coronilla
    top_vh = bm.verts.new(Vector((0.0, -0.006, 1.690)))
    for ui in range(u_segs):
        un = (ui + 1) % u_segs
        f = bm.faces.new([grid[-1][ui], grid[-1][un], top_vh])
        f.material_index = 0
        for lp in f.loops:
            lp[uv_layer].uv = Vector((ui / float(u_segs), 1.0))

    # Globos oculares 3D y párpados descansando sobre el iris
    for ex in [-0.033, 0.033]:
        p_eye = Vector((ex, 0.058, 1.575))
        sph = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=0.0125,
                                        matrix=Matrix.Translation(p_eye))
        for v in sph['verts']:
            for f in v.link_faces:
                f.material_index = 3 # mat_eyes
                for lp in f.loops:
                    dx = (lp.vert.co.x - p_eye.x) / 0.0125
                    dz = (lp.vert.co.z - p_eye.z) / 0.0125
                    lp[uv_layer].uv = Vector((clampf(0.5 + dx * 0.5, 0.0, 1.0), clampf(0.5 + dz * 0.5, 0.0, 1.0)))

        # Párpados 3D
        sign_side = 1.0 if ex > 0 else -1.0
        lid_top_pts = [
            Vector((ex - 0.014 * sign_side, 0.065, 1.572)),
            Vector((ex - 0.007 * sign_side, 0.070, 1.580)),
            Vector((ex + 0.007 * sign_side, 0.070, 1.580)),
            Vector((ex + 0.014 * sign_side, 0.065, 1.574)),
            Vector((ex + 0.011 * sign_side, 0.068, 1.586)),
            Vector((ex + 0.000 * sign_side, 0.072, 1.589)),
            Vector((ex - 0.011 * sign_side, 0.068, 1.586)),
        ]
        lv_top = [bm.verts.new(p) for p in lid_top_pts]
        bm.faces.new([lv_top[0], lv_top[1], lv_top[6]]).material_index = 0
        bm.faces.new([lv_top[1], lv_top[2], lv_top[5], lv_top[6]]).material_index = 0
        bm.faces.new([lv_top[2], lv_top[3], lv_top[4], lv_top[5]]).material_index = 0

        lid_bot_pts = [
            Vector((ex - 0.013 * sign_side, 0.065, 1.572)),
            Vector((ex - 0.006 * sign_side, 0.069, 1.568)),
            Vector((ex + 0.006 * sign_side, 0.069, 1.568)),
            Vector((ex + 0.013 * sign_side, 0.065, 1.574)),
            Vector((ex + 0.010 * sign_side, 0.067, 1.562)),
            Vector((ex + 0.000 * sign_side, 0.070, 1.560)),
            Vector((ex - 0.010 * sign_side, 0.067, 1.562)),
        ]
        lv_bot = [bm.verts.new(p) for p in lid_bot_pts]
        bm.faces.new([lv_bot[0], lv_bot[1], lv_bot[6]]).material_index = 0
        bm.faces.new([lv_bot[1], lv_bot[2], lv_bot[5], lv_bot[6]]).material_index = 0
        bm.faces.new([lv_bot[2], lv_bot[3], lv_bot[4], lv_bot[5]]).material_index = 0

    # Orejas 3D
    for sign_x in [-1.0, 1.0]:
        ear_pts = [
            Vector((sign_x * 0.070, -0.002, 1.595)),
            Vector((sign_x * 0.076, -0.014, 1.590)),
            Vector((sign_x * 0.078, -0.018, 1.570)),
            Vector((sign_x * 0.074, -0.016, 1.550)),
            Vector((sign_x * 0.068, -0.006, 1.545)),
            Vector((sign_x * 0.069,  0.006, 1.570)),
            Vector((sign_x * 0.072, -0.008, 1.572)),
        ]
        ev = [bm.verts.new(p) for p in ear_pts]
        bm.faces.new([ev[0], ev[1], ev[6], ev[5]]).material_index = 0
        bm.faces.new([ev[1], ev[2], ev[6]]).material_index = 0
        bm.faces.new([ev[2], ev[3], ev[6]]).material_index = 0
        bm.faces.new([ev[3], ev[4], ev[6]]).material_index = 0
        bm.faces.new([ev[4], ev[5], ev[6]]).material_index = 0

    # Cabello Rizado Tridimensional Auténtico de Axel (Espirales Helicoidales)
    def add_curly_strand(bm, center_start, center_end, n_turns=2.4, radius_curl=0.007,
                         thick=0.0055, n_segs=14):
        strand_rings = []
        for s in range(n_segs + 1):
            t = s / float(n_segs)
            p_core = center_start.lerp(center_end, t)
            phase = t * n_turns * 2.0 * math.pi
            helix_offset = Vector((math.cos(phase) * radius_curl, math.sin(phase) * radius_curl * 0.6, 0.0))
            p_center = p_core + helix_offset
            cur_thick = thick * (1.0 - t * 0.45)
            rng = []
            for a in range(8):
                ang = (a / 8.0) * 2.0 * math.pi
                vx = p_center.x + math.cos(ang) * cur_thick
                vy = p_center.y + math.sin(ang) * cur_thick * 0.8
                vz = p_center.z + math.sin(ang + phase) * cur_thick * 0.3
                rng.append(bm.verts.new(Vector((vx, vy, vz))))
            strand_rings.append(rng)
            
        for i in range(len(strand_rings) - 1):
            r0 = strand_rings[i]
            r1 = strand_rings[i + 1]
            for a in range(8):
                an = (a + 1) % 8
                f = bm.faces.new([r0[a], r0[an], r1[an], r1[a]])
                f.material_index = 2 # mat_hair
                
        tip = bm.verts.new(strand_rings[-1][0].co.lerp(strand_rings[-1][4].co, 0.5) + Vector((0, 0, -thick * 0.5)))
        for a in range(8):
            an = (a + 1) % 8
            f = bm.faces.new([strand_rings[-1][a], strand_rings[-1][an], tip])
            f.material_index = 2

    curls_specs = [
        # Flequillo frontal sobre la frente (Z = 1.635 a 1.590)
        (Vector((-0.038, 0.076, 1.635)), Vector((-0.030, 0.082, 1.592)), 2.2, 0.007, 0.006),
        (Vector((-0.024, 0.078, 1.638)), Vector((-0.016, 0.084, 1.588)), 2.6, 0.008, 0.006),
        (Vector((-0.010, 0.080, 1.640)), Vector((-0.004, 0.086, 1.585)), 2.8, 0.008, 0.006),
        (Vector(( 0.004, 0.080, 1.640)), Vector(( 0.010, 0.086, 1.586)), 2.8, 0.008, 0.006),
        (Vector(( 0.018, 0.078, 1.638)), Vector(( 0.024, 0.084, 1.588)), 2.5, 0.008, 0.006),
        (Vector(( 0.032, 0.076, 1.635)), Vector(( 0.038, 0.082, 1.592)), 2.2, 0.007, 0.006),
        # Patillas y sienes
        (Vector((-0.068, 0.028, 1.620)), Vector((-0.072, 0.020, 1.565)), 2.4, 0.007, 0.006),
        (Vector((-0.066, 0.012, 1.610)), Vector((-0.070, 0.006, 1.555)), 2.2, 0.006, 0.005),
        (Vector(( 0.068, 0.028, 1.620)), Vector(( 0.072, 0.020, 1.565)), 2.4, 0.007, 0.006),
        (Vector(( 0.066, 0.012, 1.610)), Vector(( 0.070, 0.006, 1.555)), 2.2, 0.006, 0.005),
        # Nuca
        (Vector((-0.040, -0.065, 1.600)), Vector((-0.035, -0.062, 1.545)), 2.0, 0.007, 0.006),
        (Vector(( 0.040, -0.065, 1.600)), Vector(( 0.035, -0.062, 1.545)), 2.0, 0.007, 0.006),
    ]
    for p1, p2, turns, r_c, th in curls_specs:
        add_curly_strand(bm, p1, p2, turns, r_c, th)

    # Sombrero Fedora de Fieltro Negro de Axel (Z = 1.625 a 1.735)
    n_brim_pts = 32
    brim_inner = []
    brim_outer = []
    
    for i in range(n_brim_pts):
        ang = (i / float(n_brim_pts)) * 2.0 * math.pi
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        dip_z = -0.016 * sin_a if sin_a > 0 else 0.010 * (-sin_a)
        
        rx_in = 0.078
        ry_in = 0.084
        vx_in = cos_a * rx_in
        vy_in = sin_a * ry_in - 0.006
        vz_in = 1.628 + dip_z * 0.4
        brim_inner.append(bm.verts.new(Vector((vx_in, vy_in, vz_in))))
        
        rx_out = 0.138
        ry_out = 0.146
        vx_out = cos_a * rx_out
        vy_out = sin_a * ry_out - 0.006
        vz_out = 1.620 + dip_z
        brim_outer.append(bm.verts.new(Vector((vx_out, vy_out, vz_out))))

    for i in range(n_brim_pts):
        nxt = (i + 1) % n_brim_pts
        f = bm.faces.new([brim_inner[i], brim_outer[i], brim_outer[nxt], brim_inner[nxt]])
        f.material_index = 1 # mat_hat

    crown_levels = [
        (1.628, 0.078, 0.084, 0.0),
        (1.648, 0.076, 0.082, 0.0),
        (1.675, 0.073, 0.079, 0.006),
        (1.705, 0.068, 0.074, 0.012),
        (1.725, 0.060, 0.068, 0.016),
    ]
    crown_rings = []
    for z_c, rx_c, ry_c, pinch in crown_levels:
        c_ring = []
        for i in range(n_brim_pts):
            ang = (i / float(n_brim_pts)) * 2.0 * math.pi
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            vx = cos_a * rx_c
            vy = sin_a * ry_c - 0.006
            vz = z_c
            if sin_a > 0.3 and abs(cos_a) > 0.2:
                vx *= (1.0 - pinch * 0.7)
            c_ring.append(bm.verts.new(Vector((vx, vy, vz))))
        crown_rings.append(c_ring)

    for r in range(len(crown_rings) - 1):
        r0 = crown_rings[r]
        r1 = crown_rings[r + 1]
        for i in range(n_brim_pts):
            nxt = (i + 1) % n_brim_pts
            f = bm.faces.new([r0[i], r0[nxt], r1[nxt], r1[i]])
            f.material_index = 1

    top_crease = []
    for i in range(n_brim_pts):
        ang = (i / float(n_brim_pts)) * 2.0 * math.pi
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        vx = cos_a * 0.038
        vy = sin_a * 0.046 - 0.006
        vz = 1.710 - (0.014 * (1.0 - min(1.0, abs(cos_a) * 1.5)))
        top_crease.append(bm.verts.new(Vector((vx, vy, vz))))

    for i in range(n_brim_pts):
        nxt = (i + 1) % n_brim_pts
        f = bm.faces.new([crown_rings[-1][i], crown_rings[-1][nxt], top_crease[nxt], top_crease[i]])
        f.material_index = 1

    center_top = bm.verts.new(Vector((0.0, -0.006, 1.698)))
    for i in range(n_brim_pts):
        nxt = (i + 1) % n_brim_pts
        f = bm.faces.new([top_crease[i], top_crease[nxt], center_top])
        f.material_index = 1

    bm.verts.index_update()
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Player_Head_Mesh", mesh)
    bpy.context.scene.collection.objects.link(obj)

    obj.data.materials.append(mat_skin) # 0
    obj.data.materials.append(mat_hat)  # 1
    obj.data.materials.append(mat_hair) # 2
    obj.data.materials.append(mat_eyes) # 3

    for poly in mesh.polygons:
        poly.use_smooth = True

    # Ponderación
    obj.parent = arm_obj
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj

    vg_head = obj.vertex_groups.new(name="Head")
    vg_neck = obj.vertex_groups.new(name="Neck")

    for v in obj.data.vertices:
        z = v.co.z
        if z >= 1.46:
            vg_head.add([v.index], 1.0, 'REPLACE')
        else:
            w_neck = clampf((1.46 - z) / 0.07, 0.0, 1.0)
            vg_head.add([v.index], 1.0 - w_neck, 'REPLACE')
            vg_neck.add([v.index], w_neck, 'REPLACE')

    return obj

# =============================================================================
# CUERPO, INDUMENTARIA Y MANOS (Player_Body_Mesh)
# =============================================================================
def build_body_mesh(arm_obj, mat_shirt, mat_vest, mat_tie, mat_pants, mat_shoes, mat_skin, mat_buttons):
    mesh = bpy.data.meshes.new("Player_Body_Mesh_Data")
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    # Materiales:
    # 0: Camisa (mat_shirt)
    # 1: Chaleco (mat_vest)
    # 2: Corbata (mat_tie)
    # 3: Pantalón (mat_pants)
    # 4: Zapatos (mat_shoes)
    # 5: Piel manos (mat_skin)
    # 6: Botones/Hebilla metálica (mat_buttons)

    # 1. Torso Completo con Hombros Cerrados y Escote en V (Z: 0.84 a 1.42)
    torso_levels = [
        (0.84, 0.145, 0.115, 3), # Base pelvis / entrepierna
        (0.92, 0.150, 0.118, 3), # Cintura baja / cadera
        (1.00, 0.145, 0.112, 1), # Cintura / ombligo (chaleco bajo)
        (1.10, 0.155, 0.118, 1), # Esternón bajo
        (1.22, 0.175, 0.128, 1), # Pecho / busto sastre
        (1.32, 0.185, 0.132, 1), # Pecho alto
        (1.38, 0.170, 0.115, 0), # Hombros / clavículas
        (1.42, 0.052, 0.054, 0), # Cuello camisero que rodea el cuello
    ]
    
    n_torso_pts = 32
    torso_rings = []
    
    for z, rx, ry, base_mat in torso_levels:
        t_ring = []
        for i in range(n_torso_pts):
            ang = (i / float(n_torso_pts)) * 2.0 * math.pi
            vx = math.cos(ang) * rx
            vy = math.sin(ang) * ry
            vz = z
            t_ring.append(bm.verts.new(Vector((vx, vy, vz))))
        torso_rings.append(t_ring)

    for r in range(len(torso_rings) - 1):
        r0 = torso_rings[r]
        r1 = torso_rings[r + 1]
        z_mid = (torso_levels[r][0] + torso_levels[r + 1][0]) * 0.5
        for i in range(n_torso_pts):
            nxt = (i + 1) % n_torso_pts
            ang = (i / float(n_torso_pts)) * 2.0 * math.pi
            f = bm.faces.new([r0[i], r0[nxt], r1[nxt], r1[i]])
            
            # Escote en V del chaleco en el pecho anterior
            is_anterior = (math.sin(ang) > 0.3)
            is_v_neck = is_anterior and (1.18 <= z_mid <= 1.40) and (abs(math.cos(ang)) < 0.38)
            
            if z_mid < 0.95:
                f.material_index = 3 # Pantalón
            elif 0.95 <= z_mid <= 1.36 and not is_v_neck:
                f.material_index = 1 # Chaleco
            else:
                f.material_index = 0 # Camisa

    # Cuello camisero doblado (collar leaves)
    for sign_c in [-1.0, 1.0]:
        c_pts = [
            Vector((sign_c * 0.048, 0.020, 1.420)),
            Vector((sign_c * 0.032, 0.052, 1.415)),
            Vector((sign_c * 0.014, 0.065, 1.398)), # Punta del cuello
            Vector((sign_c * 0.028, 0.038, 1.395)),
        ]
        cv = [bm.verts.new(p) for p in c_pts]
        bm.faces.new(cv).material_index = 0

    # Nudo tridimensional de corbata
    k_pts = [
        Vector((-0.012, 0.060, 1.412)),
        Vector(( 0.012, 0.060, 1.412)),
        Vector(( 0.010, 0.066, 1.388)),
        Vector((-0.010, 0.066, 1.388)),
    ]
    kv = [bm.verts.new(p) for p in k_pts]
    bm.faces.new(kv).material_index = 2 # mat_tie

    # Pala de corbata cayendo recta
    tie_levels = [
        (1.388, 0.010, 0.066),
        (1.300, 0.015, 0.088),
        (1.200, 0.022, 0.098),
        (1.120, 0.025, 0.095),
    ]
    tie_rings = []
    for z_t, w_t, y_t in tie_levels:
        v_l = bm.verts.new(Vector((-w_t, y_t, z_t)))
        v_r = bm.verts.new(Vector(( w_t, y_t, z_t)))
        tie_rings.append((v_l, v_r))

    for idx in range(len(tie_rings) - 1):
        l0, r0 = tie_rings[idx]
        l1, r1 = tie_rings[idx + 1]
        f = bm.faces.new([l0, r0, r1, l1])
        f.material_index = 2

    # Botones metálicos en la botonadura central del chaleco
    for zb in [0.98, 1.03, 1.08, 1.13, 1.18]:
        btn = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.005,
                                        matrix=Matrix.Translation(Vector((0.0, 0.118, zb))))
        for v in btn['verts']:
            for f in v.link_faces:
                f.material_index = 6

    # Picos inferiores clásicos del chaleco
    for sign_p in [-1.0, 1.0]:
        peak_pts = [
            Vector((sign_p * 0.015, 0.116, 0.950)),
            Vector((sign_p * 0.055, 0.114, 0.950)),
            Vector((sign_p * 0.035, 0.118, 0.925)),
        ]
        pv = [bm.verts.new(p) for p in peak_pts]
        bm.faces.new(pv).material_index = 1

    # 2. Brazos y Mangas CONTINUOS con Caperuza de Hombro Cerrada
    for sign_x in [-1.0, 1.0]:
        arm_joints = [
            (Vector((sign_x * 0.18, 0.0, 1.35)), 0.065), # Hombro
            (Vector((sign_x * 0.23, 0.0, 1.25)), 0.056), # Bíceps
            (Vector((sign_x * 0.28, 0.0, 1.14)), 0.050), # Codo
            (Vector((sign_x * 0.32, 0.0, 1.04)), 0.044), # Antebrazo
            (Vector((sign_x * 0.35, 0.0, 0.94)), 0.038), # Muñeca / puño
        ]
        s_rings = []
        for center, r_arm in arm_joints:
            rng = []
            for a in range(16):
                ang = (a / 16.0) * 2.0 * math.pi
                vx = center.x + math.cos(ang) * r_arm
                vy = center.y + math.sin(ang) * r_arm
                vz = center.z
                rng.append(bm.verts.new(Vector((vx, vy, vz))))
            s_rings.append(rng)
            
        # Caperuza cerrada en el hombro (evita huecos abiertos en axilas)
        sh_top = bm.verts.new(Vector((sign_x * 0.17, 0.0, 1.375)))
        for a in range(16):
            an = (a + 1) % 16
            f = bm.faces.new([s_rings[0][a], s_rings[0][an], sh_top])
            f.material_index = 0
            
        for i in range(len(s_rings) - 1):
            r0 = s_rings[i]
            r1 = s_rings[i + 1]
            for a in range(16):
                an = (a + 1) % 16
                f = bm.faces.new([r0[a], r0[an], r1[an], r1[a]])
                f.material_index = 0

        # 3. Manos Anatómicas Conectadas
        wrist_pos = Vector((sign_x * 0.35, 0.0, 0.94))
        medial_dir = Vector((-sign_x, 0, 0))
        distal_dir = Vector((sign_x * 0.15, 0, -1)).normalized()
        
        finger_specs = [
            ("Index",  0.011, 0.062, 0.0072),
            ("Middle", 0.000, 0.070, 0.0078),
            ("Ring",  -0.011, 0.064, 0.0072),
            ("Pinky", -0.021, 0.050, 0.0065),
        ]
        
        base_knuckles = wrist_pos + distal_dir * 0.055
        for f_name, lat_offset, f_len, f_thick in finger_specs:
            f_root = base_knuckles + medial_dir * (lat_offset * sign_x)
            p0 = f_root
            p1 = p0 + distal_dir * (f_len * 0.38) + Vector((0, -0.004, 0))
            p2 = p1 + distal_dir * (f_len * 0.34) + Vector((0, -0.008, 0))
            p3 = p2 + distal_dir * (f_len * 0.28) + Vector((0, -0.011, 0))
            
            f_rings = []
            for idx_p, pt in enumerate([p0, p1, p2, p3]):
                scale_t = f_thick * (1.0 - idx_p * 0.16)
                rng = []
                for a in range(8):
                    ang = (a / 8.0) * 2.0 * math.pi
                    vx = pt.x + math.cos(ang) * scale_t
                    vy = pt.y + math.sin(ang) * scale_t
                    vz = pt.z
                    rng.append(bm.verts.new(Vector((vx, vy, vz))))
                f_rings.append(rng)
                
            for idx_r in range(len(f_rings) - 1):
                r0 = f_rings[idx_r]
                r1 = f_rings[idx_r + 1]
                for a in range(8):
                    an = (a + 1) % 8
                    f = bm.faces.new([r0[a], r0[an], r1[an], r1[a]])
                    f.material_index = 5
                    
            f_tip = bm.verts.new(p3 + distal_dir * 0.004 + Vector((0, -0.004, 0)))
            for a in range(8):
                an = (a + 1) % 8
                f = bm.faces.new([f_rings[-1][a], f_rings[-1][an], f_tip])
                f.material_index = 5

            if f_name == "Ring" and sign_x > 0:
                ring_obj = bmesh.ops.create_circle(bm, cap_ends=False, radius=f_thick * 1.15,
                                                   matrix=Matrix.Translation(p0.lerp(p1, 0.4)))
                r_edges = [e for e in bm.edges if e.is_boundary and e.verts[0] in ring_obj['verts']]
                res_ext = bmesh.ops.extrude_edge_only(bm, edges=r_edges)
                for v in res_ext['geom']:
                    if isinstance(v, bmesh.types.BMVert):
                        v.co += distal_dir * 0.004
                for f in [g for g in res_ext['geom'] if isinstance(g, bmesh.types.BMFace)]:
                    f.material_index = 6

        # Pulgar Oponible Anatómico
        thumb_base = wrist_pos + medial_dir * 0.022 + distal_dir * 0.020 + Vector((0, -0.005, 0))
        t_p0 = thumb_base
        t_p1 = t_p0 + medial_dir * 0.020 + Vector((0, -0.012, -0.016))
        t_p2 = t_p1 + medial_dir * 0.014 + Vector((0, -0.016, -0.018))
        
        t_rings = []
        for idx_t, pt in enumerate([t_p0, t_p1, t_p2]):
            th_rad = 0.0090 * (1.0 - idx_t * 0.18)
            rng = []
            for a in range(8):
                ang = (a / 8.0) * 2.0 * math.pi
                vx = pt.x + math.cos(ang) * th_rad
                vy = pt.y + math.sin(ang) * th_rad
                vz = pt.z
                rng.append(bm.verts.new(Vector((vx, vy, vz))))
            t_rings.append(rng)
            
        for idx_r in range(len(t_rings) - 1):
            r0 = t_rings[idx_r]
            r1 = t_rings[idx_r + 1]
            for a in range(8):
                an = (a + 1) % 8
                f = bm.faces.new([r0[a], r0[an], r1[an], r1[a]])
                f.material_index = 5
                
        thumb_tip = bm.verts.new(t_p2 + medial_dir * 0.005 + Vector((0, -0.005, -0.005)))
        for a in range(8):
            an = (a + 1) % 8
            f = bm.faces.new([t_rings[-1][a], t_rings[-1][an], thumb_tip])
            f.material_index = 5

        # Cierre limpio de la muñeca
        wrist_cap = bm.verts.new(wrist_pos + distal_dir * 0.025)
        for a in range(16):
            an = (a + 1) % 16
            f = bm.faces.new([s_rings[-1][a], s_rings[-1][an], wrist_cap])
            f.material_index = 5

    # 4. Piernas y Pantalones CONTINUOS Cerrados (Sin Huecos en la Pelvis)
    # Tapa inferior cerrada de la entrepierna para unir las piernas al torso
    crotch_center = bm.verts.new(Vector((0.0, 0.0, 0.83)))
    for a in range(n_torso_pts):
        an = (a + 1) % n_torso_pts
        f = bm.faces.new([torso_rings[0][a], torso_rings[0][an], crotch_center])
        f.material_index = 3 # Pantalón

    for sign_x in [-1.0, 1.0]:
        leg_joints = [
            (Vector((sign_x * 0.09, 0.0, 0.83)), 0.090, 3), # Ingle / cadera
            (Vector((sign_x * 0.095, 0.0, 0.65)), 0.082, 3),# Muslo
            (Vector((sign_x * 0.10, 0.0, 0.48)), 0.072, 3), # Rodilla
            (Vector((sign_x * 0.10, 0.0, 0.30)), 0.064, 3), # Pantorrilla
            (Vector((sign_x * 0.10, 0.0, 0.12)), 0.055, 3), # Tobillo / dobladillo
            # Zapatos de vestir
            (Vector((sign_x * 0.10, 0.02, 0.07)), 0.052, 4),# Empeine
            (Vector((sign_x * 0.10, 0.05, 0.02)), 0.054, 4),# Suela
        ]
        leg_rings = []
        for center, r_leg, mat_idx in leg_joints:
            rng = []
            for a in range(16):
                ang = (a / 16.0) * 2.0 * math.pi
                crease_y = 0.007 if (a == 4 and center.z > 0.10) else 0.0
                vx = center.x + math.cos(ang) * r_leg
                vy = center.y + math.sin(ang) * r_leg + crease_y
                vz = center.z
                rng.append(bm.verts.new(Vector((vx, vy, vz))))
            leg_rings.append((rng, mat_idx))
            
        for i in range(len(leg_rings) - 1):
            r0, m0 = leg_rings[i]
            r1, m1 = leg_rings[i + 1]
            for a in range(16):
                an = (a + 1) % 16
                f = bm.faces.new([r0[a], r0[an], r1[an], r1[a]])
                f.material_index = m0

        # Suela del zapato
        sole_verts = leg_rings[-1][0]
        sole_center = bm.verts.new(Vector((sign_x * 0.10, 0.05, 0.0)))
        for a in range(16):
            an = (a + 1) % 16
            f = bm.faces.new([sole_verts[a], sole_verts[an], sole_center])
            f.material_index = 4

    bm.verts.index_update()
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Player_Body_Mesh", mesh)
    bpy.context.scene.collection.objects.link(obj)

    obj.data.materials.append(mat_shirt)   # 0
    obj.data.materials.append(mat_vest)    # 1
    obj.data.materials.append(mat_tie)     # 2
    obj.data.materials.append(mat_pants)   # 3
    obj.data.materials.append(mat_shoes)   # 4
    obj.data.materials.append(mat_skin)    # 5
    obj.data.materials.append(mat_buttons) # 6

    for poly in mesh.polygons:
        poly.use_smooth = True

    obj.parent = arm_obj
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj

    bone_names = [
        "Hips", "Spine", "Spine1", "Chest",
        "Shoulder.L", "UpperArm.L", "Forearm.L", "Hand.L",
        "Shoulder.R", "UpperArm.R", "Forearm.R", "Hand.R",
        "UpperLeg.L", "LowerLeg.L", "Foot.L", "Toes.L",
        "UpperLeg.R", "LowerLeg.R", "Foot.R", "Toes.R"
    ]
    vgroups = {b: obj.vertex_groups.new(name=b) for b in bone_names}

    for v in obj.data.vertices:
        x, y, z = v.co.x, v.co.y, v.co.z
        if abs(x) > 0.14 and z > 0.80:
            side = ".L" if x < 0 else ".R"
            if z > 1.30:
                vgroups["Shoulder" + side].add([v.index], 1.0, 'REPLACE')
            elif z > 1.10:
                w_farm = clampf((1.30 - z) / 0.20, 0.0, 1.0)
                vgroups["UpperArm" + side].add([v.index], 1.0 - w_farm, 'REPLACE')
                vgroups["Forearm" + side].add([v.index], w_farm, 'REPLACE')
            elif z > 0.92:
                vgroups["Forearm" + side].add([v.index], 1.0, 'REPLACE')
            else:
                vgroups["Hand" + side].add([v.index], 1.0, 'REPLACE')
        elif z < 0.84 and (abs(x) > 0.03 or z < 0.70):
            side = ".L" if x < 0 else ".R"
            if z > 0.48:
                vgroups["UpperLeg" + side].add([v.index], 1.0, 'REPLACE')
            elif z > 0.12:
                vgroups["LowerLeg" + side].add([v.index], 1.0, 'REPLACE')
            elif y < 0.10:
                vgroups["Foot" + side].add([v.index], 1.0, 'REPLACE')
            else:
                vgroups["Toes" + side].add([v.index], 1.0, 'REPLACE')
        else:
            if z < 1.00:
                vgroups["Hips"].add([v.index], 1.0, 'REPLACE')
            elif z < 1.18:
                w_s = clampf((z - 1.00) / 0.18, 0.0, 1.0)
                vgroups["Spine"].add([v.index], 1.0 - w_s, 'REPLACE')
                vgroups["Spine1"].add([v.index], w_s, 'REPLACE')
            elif z < 1.30:
                vgroups["Spine1"].add([v.index], 1.0, 'REPLACE')
            else:
                vgroups["Chest"].add([v.index], 1.0, 'REPLACE')

    return obj

def render_preview_image():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.device = 'CPU'
    scene.render.resolution_x = 720
    scene.render.resolution_y = 1280
    scene.render.resolution_percentage = 100

    cam_data = bpy.data.cameras.new("StudioCamera")
    cam_data.lens = 55.0
    cam_obj = bpy.data.objects.new("StudioCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    # Encuadre frontal de retrato a nivel del esternón
    cam_obj.location = Vector((0.08, 1.95, 1.25))
    cam_obj.rotation_euler = (math.radians(88.5), 0.0, math.radians(178.0))

    key_data = bpy.data.lights.new("KeyLight", type='AREA')
    key_data.energy = 85.0
    key_data.size = 1.4
    key_data.color = (1.0, 0.98, 0.95)
    key_obj = bpy.data.objects.new("KeyLight", key_data)
    key_obj.location = Vector((-0.8, 1.5, 1.7))
    key_obj.rotation_euler = (math.radians(55.0), 0.0, math.radians(-145.0))
    scene.collection.objects.link(key_obj)

    fill_data = bpy.data.lights.new("FillLight", type='AREA')
    fill_data.energy = 38.0
    fill_data.size = 1.6
    fill_data.color = (0.92, 0.96, 1.0)
    fill_obj = bpy.data.objects.new("FillLight", fill_data)
    fill_obj.location = Vector((1.0, 1.5, 1.3))
    scene.collection.objects.link(fill_obj)

    rim_data = bpy.data.lights.new("RimLight", type='SPOT')
    rim_data.energy = 45.0
    rim_data.spot_size = math.radians(65.0)
    rim_data.color = (1.0, 1.0, 1.0)
    rim_obj = bpy.data.objects.new("RimLight", rim_data)
    rim_obj.location = Vector((0.0, -1.2, 1.9))
    rim_obj.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
    scene.collection.objects.link(rim_obj)

    scene.render.filepath = PREVIEW_PNG
    bpy.ops.render.render(write_still=True)
    print(f"✓ Render preview guardado en: {PREVIEW_PNG}")

def main():
    print("==================================================")
    print("GENERANDO AXEL V6 HIPERREALISTA (ESTILO FORTNITE)")
    print("==================================================")
    clean_scene()

    tex_face_diff = os.path.join(TEX_DIR, "axel_face_diffuse.png")
    tex_face_norm = os.path.join(TEX_DIR, "axel_face_normal.png")
    tex_hat_diff = os.path.join(TEX_DIR, "axel_hat_diffuse.png")
    tex_hat_norm = os.path.join(TEX_DIR, "axel_hat_normal.png")
    tex_vest_diff = os.path.join(TEX_DIR, "axel_vest_diffuse.png")
    tex_vest_norm = os.path.join(TEX_DIR, "axel_vest_normal.png")
    tex_shirt_diff = os.path.join(TEX_DIR, "axel_shirt_diffuse.png")
    tex_shirt_norm = os.path.join(TEX_DIR, "axel_shirt_normal.png")
    tex_tie_diff = os.path.join(TEX_DIR, "axel_tie_diffuse.png")
    tex_tie_norm = os.path.join(TEX_DIR, "axel_tie_normal.png")
    tex_pants_diff = os.path.join(TEX_DIR, "axel_pants_diffuse.png")
    tex_pants_norm = os.path.join(TEX_DIR, "axel_pants_normal.png")
    tex_shoes_diff = os.path.join(TEX_DIR, "axel_shoes_diffuse.png")
    tex_shoes_norm = os.path.join(TEX_DIR, "axel_shoes_normal.png")
    tex_eye_diff = os.path.join(TEX_DIR, "axel_eye_diffuse.png")

    mat_skin = create_pbr_material("Mat_Axel_Skin", (0.80, 0.58, 0.46, 1.0), roughness=0.45,
                                   tex_diffuse_path=tex_face_diff, tex_normal_path=tex_face_norm, sss_weight=0.35)
    mat_hat = create_pbr_material("Mat_Axel_Hat", (0.08, 0.08, 0.09, 1.0), roughness=0.85,
                                  tex_diffuse_path=tex_hat_diff, tex_normal_path=tex_hat_norm)
    mat_hair = create_pbr_material("Mat_Axel_Hair", (0.09, 0.07, 0.06, 1.0), roughness=0.60, metallic=0.05)
    mat_eyes = create_pbr_material("Mat_Axel_Eyes", (1, 1, 1, 1), roughness=0.06,
                                   tex_diffuse_path=tex_eye_diff)
    mat_shirt = create_pbr_material("Mat_Axel_Shirt", (0.16, 0.17, 0.19, 1.0), roughness=0.65,
                                    tex_diffuse_path=tex_shirt_diff, tex_normal_path=tex_shirt_norm)
    mat_vest = create_pbr_material("Mat_Axel_Vest", (0.82, 0.84, 0.86, 1.0), roughness=0.55,
                                   tex_diffuse_path=tex_vest_diff, tex_normal_path=tex_vest_norm)
    mat_tie = create_pbr_material("Mat_Axel_Tie", (0.45, 0.48, 0.52, 1.0), roughness=0.35, metallic=0.15,
                                  tex_diffuse_path=tex_tie_diff, tex_normal_path=tex_tie_norm)
    mat_pants = create_pbr_material("Mat_Axel_Pants", (0.13, 0.14, 0.16, 1.0), roughness=0.75,
                                    tex_diffuse_path=tex_pants_diff, tex_normal_path=tex_pants_norm)
    mat_shoes = create_pbr_material("Mat_Axel_Shoes", (0.08, 0.08, 0.09, 1.0), roughness=0.45, metallic=0.05,
                                    tex_diffuse_path=tex_shoes_diff, tex_normal_path=tex_shoes_norm)
    mat_buttons = create_pbr_material("Mat_Axel_Buttons", (0.85, 0.85, 0.88, 1.0), roughness=0.22, metallic=0.92)

    arm_obj = build_axel_armature()
    print("✓ Armature antropométrico canónico construido con 22 huesos.")

    head_obj = build_head_mesh(arm_obj, mat_skin, mat_hat, mat_hair, mat_eyes)
    print("✓ Player_Head_Mesh generado con proporciones anatómicas, rizos y fedora.")

    body_obj = build_body_mesh(arm_obj, mat_shirt, mat_vest, mat_tie, mat_pants, mat_shoes, mat_skin, mat_buttons)
    print("✓ Player_Body_Mesh generado con hombros continuos, chaleco, corbata y manos anatómicas.")

    os.makedirs(os.path.dirname(OUTPUT_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
    print(f"✓ Guardado .blend maestro en: {OUTPUT_BLEND}")

    bpy.ops.export_scene.gltf(
        filepath=OUTPUT_GLB,
        export_format='GLB',
        use_selection=False,
        export_yup=True,
        export_apply=False,
        export_skins=True,
        export_all_influences=False,
        export_materials='EXPORT',
        export_image_format='AUTO',
        export_lights=False,
        export_cameras=False
    )
    print(f"✓ Exportado archivo glTF .glb en: {OUTPUT_GLB}")

    render_preview_image()
    print("==================================================")
    print("PROCESO COMPLETADO EXITOSAMENTE")
    print("==================================================")

if __name__ == "__main__":
    main()
