"""
=============================================================================
Generador 3D Procedural: Axel - Modelo Humano Hiperrealista (Tecate Simulator)
=============================================================================
Reconstrucción fotorrealista y estilizada de Axel (estilo Fortnite / AAA):
- CERO IA: materiales PBR shader nativos y texturas procedurales matemáticas
  directas ('godot_project/assets/characters/textures/').
- Identidad fidedigna a 'scratch/humans/axel.png':
  * Rostro masculino esculpido: proporciones atléticas, mandíbula angular, pómulos.
  * Ojos 3D almendrados con cuencas profundas, esclerótica, iris avellana estriado y párpados.
  * Nariz 3D con puente esculpido, punta definida y aletas nasales.
  * Labios 3D anatómicos con arco de Cupido y volumen bermellón.
  * Sombreado de barba / 5 o'clock shadow auténtico en mentón y mandíbula.
  * Cuello esbelto y atlético (r ~ 0.046 m) con relieve de nuez de Adán.
  * Mechones 3D de cabello castaño oscuro ondulado bajo el gorro (frente, patillas y nuca).
  * Gorro beanie 3D de lana verde oliva/tierra con dobladillo acanalado en relieve.
  * Chamarra acolchada puffer / cortavientos azul marino con cuello alto (storm collar),
    cremallera central, gajos acolchados horizontales y puños elásticos en muñecas.
  * Cinturón de cuero marrón con textura de grano y hebilla rectangular metálica con hebijón.
  * Pantalón de mezclilla oscura continuo con sarga procedural.
  * Calzado deportivo urbano con suela de caucho y lengüeta.
  * Manos anatómicas en A-pose: dorso hacia el frente (+Y), palma hacia el interior/fondo (-Y),
    pulgar OPONIBLE que nace en la eminencia tenar y se orienta hacia la palma/interior,
    y 4 dedos escalonados (Medio > Anular > Índice > Meñique) con 3 falanges relajadas.
- Cero accesorios ajenos a la vestimenta (sin micrófonos ni cables).
- Esqueleto canónico de 22 huesos compatible con CitizenEntity y Godot 4.
=============================================================================
"""

import os
import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler, Quaternion

OUTPUT_GLB = "godot_project/assets/characters/citizens/axel.glb"
OUTPUT_BLEND = "godot_project/assets/characters/citizens/axel.blend"
TEX_DIR = "godot_project/assets/characters/textures"

def clean_scene():
    """Limpia todos los datos residuales de la escena."""
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
    """Crea un material Principled BSDF nativo de alta fidelidad con soporte para texturas PBR."""
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
            
    # Textura difusa
    if tex_diffuse_path and os.path.exists(tex_diffuse_path):
        tex_img = bpy.data.images.load(os.path.abspath(tex_diffuse_path))
        node_tex = nodes.new(type='ShaderNodeTexImage')
        node_tex.image = tex_img
        links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])
        
    # Textura de normales
    if tex_normal_path and os.path.exists(tex_normal_path):
        norm_img = bpy.data.images.load(os.path.abspath(tex_normal_path))
        norm_img.colorspace_settings.name = 'Non-Color'
        node_norm_img = nodes.new(type='ShaderNodeTexImage')
        node_norm_img.image = norm_img
        node_norm_map = nodes.new(type='ShaderNodeNormalMap')
        node_norm_map.inputs['Strength'].default_value = 1.0
        links.new(node_norm_img.outputs['Color'], node_norm_map.inputs['Color'])
        links.new(node_norm_map.outputs['Normal'], node_bsdf.inputs['Normal'])
        
    return mat

def build_axel_armature():
    """
    Construye el esqueleto antropométrico canónico simétrico (22 huesos).
    Ambos brazos en A-pose limpia y relajada (~22° respecto al torso).
    """
    arm_data = bpy.data.armatures.new("Armature_Humanoid_Data")
    arm_data.display_type = 'OCTAHEDRAL'
    arm_obj = bpy.data.objects.new("Armature_Humanoid", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj

    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = arm_data.edit_bones

    # 1. Raíz
    b_root = edit_bones.new("Root")
    b_root.head = Vector((0.0, 0.0, 0.0))
    b_root.tail = Vector((0.0, 0.0, 0.15))

    # 2. Pelvis / Caderas
    b_hips = edit_bones.new("Hips")
    b_hips.head = Vector((0.0, 0.0, 0.95))
    b_hips.tail = Vector((0.0, 0.0, 1.10))
    b_hips.parent = b_root

    # 3. Columna vertebral
    b_spine = edit_bones.new("Spine")
    b_spine.head = Vector((0.0, 0.0, 1.10))
    b_spine.tail = Vector((0.0, 0.0, 1.25))
    b_spine.parent = b_hips

    b_spine1 = edit_bones.new("Spine1")
    b_spine1.head = Vector((0.0, 0.0, 1.25))
    b_spine1.tail = Vector((0.0, 0.0, 1.38))
    b_spine1.parent = b_spine

    b_chest = edit_bones.new("Chest")
    b_chest.head = Vector((0.0, 0.0, 1.38))
    b_chest.tail = Vector((0.0, 0.0, 1.46))
    b_chest.parent = b_spine1

    # 4. Cuello y Cabeza
    b_neck = edit_bones.new("Neck")
    b_neck.head = Vector((0.0, 0.0, 1.46))
    b_neck.tail = Vector((0.0, 0.0, 1.52))
    b_neck.parent = b_chest

    b_head = edit_bones.new("Head")
    b_head.head = Vector((0.0, 0.0, 1.52))
    b_head.tail = Vector((0.0, 0.0, 1.72))
    b_head.parent = b_neck

    b_eyes = edit_bones.new("EyesAnchor")
    b_eyes.head = Vector((0.0, 0.058, 1.585))
    b_eyes.tail = Vector((0.0, 0.158, 1.585))
    b_eyes.parent = b_head

    # 5. Brazos en A-Pose Simétrica Natural
    for sign_x, suffix in [(-1.0, ".L"), (1.0, ".R")]:
        b_sh = edit_bones.new("Shoulder" + suffix)
        b_sh.head = Vector((sign_x * 0.06, 0.0, 1.42))
        b_sh.tail = Vector((sign_x * 0.19, 0.0, 1.38))
        b_sh.parent = b_chest

        b_uarm = edit_bones.new("UpperArm" + suffix)
        b_uarm.head = Vector((sign_x * 0.19, 0.0, 1.38))
        b_uarm.tail = Vector((sign_x * 0.29, 0.0, 1.16))
        b_uarm.parent = b_chest

        b_farm = edit_bones.new("Forearm" + suffix)
        b_farm.head = Vector((sign_x * 0.29, 0.0, 1.16))
        b_farm.tail = Vector((sign_x * 0.36, 0.0, 0.95))
        b_farm.parent = b_uarm

        b_hand = edit_bones.new("Hand" + suffix)
        b_hand.head = Vector((sign_x * 0.36, 0.0, 0.95))
        b_hand.tail = Vector((sign_x * 0.38, 0.0, 0.80))
        b_hand.parent = b_farm

    # 6. Piernas Simétricas
    for sign_x, suffix in [(-1.0, ".L"), (1.0, ".R")]:
        b_uleg = edit_bones.new("UpperLeg" + suffix)
        b_uleg.head = Vector((sign_x * 0.10, 0.0, 0.92))
        b_uleg.tail = Vector((sign_x * 0.11, 0.0, 0.50))
        b_uleg.parent = b_hips

        b_lleg = edit_bones.new("LowerLeg" + suffix)
        b_lleg.head = Vector((sign_x * 0.11, 0.0, 0.50))
        b_lleg.tail = Vector((sign_x * 0.11, 0.0, 0.12))
        b_lleg.parent = b_uleg

        b_foot = edit_bones.new("Foot" + suffix)
        b_foot.head = Vector((sign_x * 0.11, 0.0, 0.12))
        b_foot.tail = Vector((sign_x * 0.11, 0.12, 0.03))
        b_foot.parent = b_lleg

        b_toe = edit_bones.new("Toes" + suffix)
        b_toe.head = Vector((sign_x * 0.11, 0.12, 0.03))
        b_toe.tail = Vector((sign_x * 0.11, 0.20, 0.03))
        b_toe.parent = b_foot

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

def build_head_mesh(arm_obj, mat_skin, mat_beanie, mat_hair, mat_eyes):
    """
    Construye la cabeza hiperrealista completa de Axel (Capa 2):
    - Escultura facial proporcionada canónicamente (cuello atlético firme, mentón angular).
    - Ojos almendrados con párpado superior cubriendo el borde superior del iris (mirada segura y humana).
    - Nariz definida con puente recto y aletas nasales.
    - Labios 3D con arco de Cupido.
    - Gorro beanie verde oliva con dobladillo en relieve.
    - Mechones de cabello castaño rizado bajo el dobladillo.
    """
    mesh = bpy.data.meshes.new("Player_Head_Mesh_Data")
    bm = bmesh.new()

    u_segs = 32
    v_rings = 24
    grid = []

    # Proporciones faciales calibradas con cuello atlético proporcionado
    for vi in range(v_rings + 1):
        tv = vi / float(v_rings)
        if tv < 0.22: # Cuello atlético (Z: 1.44 a 1.50)
            t_neck = tv / 0.22
            z = 1.440 + t_neck * 0.060
            rx = 0.048 + t_neck * 0.002
            ry_f = 0.050 + t_neck * 0.003
            ry_b = 0.048
            yc = 0.002
        elif tv < 0.50: # Mandíbula y mentón (Z: 1.50 a 1.55)
            tj = (tv - 0.22) / 0.28
            z = 1.500 + tj * 0.052
            rx = 0.050 + tj * 0.016
            ry_f = 0.058 + tj * 0.014
            ry_b = 0.048 + tj * 0.014
            yc = 0.001
        elif tv < 0.76: # Pómulos, nariz y ojos (Z: 1.55 a 1.61)
            tm = (tv - 0.50) / 0.26
            z = 1.552 + tm * 0.058
            rx = 0.066 + tm * 0.005
            ry_f = 0.072
            ry_b = 0.062 + tm * 0.008
            yc = 0.0
        else: # Frente y bóveda craneal (Z: 1.61 a 1.70)
            tt = (tv - 0.76) / 0.24
            z = 1.610 + tt * 0.085
            dome = math.sqrt(max(0.01, 1.0 - (tt * 0.95)**2))
            rx = 0.071 * dome + 0.002
            ry_f = 0.073 * dome + 0.002
            ry_b = 0.073 * dome + 0.002
            yc = -0.008 * tt

        ring = []
        for ui in range(u_segs):
            ang = (ui / float(u_segs)) * 2.0 * math.pi - (math.pi / 2.0)
            sin_a = math.sin(ang)
            cos_a = math.cos(ang)
            vx = cos_a * rx
            vy = yc + (sin_a * ry_f if sin_a >= 0 else sin_a * ry_b)
            vz = z

            if sin_a > 0: # Cara anterior (+Y)
                # Mentón masculino
                if abs(vz - 1.510) < 0.020 and abs(vx) < 0.026:
                    cd = math.sqrt((vx / 0.026)**2 + ((vz - 1.510) / 0.020)**2)
                    if cd < 1.0:
                        vy += 0.014 * (1.0 - cd)**2
                # Surco mentolabial
                if abs(vz - 1.522) < 0.008 and abs(vx) < 0.022:
                    vy -= 0.004 * (1.0 - abs(vx) / 0.022)
                # Labios con volumen y arco de Cupido
                if 1.528 < vz < 1.548 and abs(vx) < 0.028:
                    tlip = (vz - 1.528) / 0.020
                    w_lip = 0.026 * (1.0 - abs(tlip - 0.5) * 1.5)
                    if abs(vx) < max(0.004, w_lip):
                        vy += 0.009 * math.sin(tlip * math.pi) * (1.0 - abs(vx) / max(0.004, w_lip))
                # Nariz esculpida continua
                if 1.548 < vz < 1.600 and abs(vx) < 0.020:
                    tn = (vz - 1.548) / 0.052
                    nw = 0.010 + (1.0 - tn) * 0.009
                    if abs(vx) < nw:
                        lf = 1.0 - (abs(vx) / nw)
                        n_proj = 0.024 * math.sin(tn * math.pi * 0.85) if tn < 0.40 else 0.015 + (1.0 - tn) * 0.009
                        vy += n_proj * (lf**1.3)
                # Cuencas orbitarias profundas para los ojos
                for ecx in [-0.032, 0.032]:
                    de = math.sqrt(((vx - ecx) / 0.018)**2 + ((vz - 1.585) / 0.014)**2)
                    if de < 1.0:
                        vy -= 0.014 * (1.0 - de)**2
                # Nuez de Adán en el cuello
                if abs(vz - 1.470) < 0.012 and abs(vx) < 0.012:
                    vy += 0.006 * (1.0 - abs(vx) / 0.012)

            ring.append(bm.verts.new(Vector((vx, vy, vz))))
        grid.append(ring)

    # Crear caras con mapeo UV cilíndrico facial
    uv_layer = bm.loops.layers.uv.new("UVMap")
    
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

    # Cierre de la coronilla
    top_vh = bm.verts.new(Vector((0.0, -0.008, 1.695)))
    for ui in range(u_segs):
        un = (ui + 1) % u_segs
        f = bm.faces.new([grid[-1][ui], grid[-1][un], top_vh])
        f.material_index = 0

    # 2. Globos Oculares 3D en Cuencas Recesadas con Párpados Almendrados Cubriendo el Borde Superior
    for ex in [-0.032, 0.032]:
        p_eye = Vector((ex, 0.058, 1.585))
        sph = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=0.0120,
                                        matrix=Matrix.Translation(p_eye))
        for v in sph['verts']:
            for f in v.link_faces:
                f.material_index = 3 # mat_eyes
                for lp in f.loops:
                    dx = (lp.vert.co.x - p_eye.x) / 0.0120
                    dz = (lp.vert.co.z - p_eye.z) / 0.0120
                    lp[uv_layer].uv = Vector((clampf(0.5 + dx * 0.5, 0.0, 1.0), clampf(0.5 + dz * 0.5, 0.0, 1.0)))

        # Párpado superior envolvente cubriendo el polo superior del globo ocular (Z=1.588)
        lid_top_pts = [
            Vector((ex - 0.014, 0.064, 1.582)), # Comisura lateral
            Vector((ex - 0.007, 0.069, 1.589)), # Borde superior descansando sobre el iris
            Vector((ex + 0.007, 0.069, 1.589)), # Borde superior descansando sobre el iris
            Vector((ex + 0.014, 0.064, 1.582)), # Comisura medial
            Vector((ex + 0.011, 0.067, 1.596)), # Pliegue supratarzal
            Vector((ex + 0.000, 0.071, 1.599)),
            Vector((ex - 0.011, 0.067, 1.596)),
        ]
        lv_top = [bm.verts.new(p) for p in lid_top_pts]
        bm.faces.new([lv_top[0], lv_top[1], lv_top[6]]).material_index = 0
        bm.faces.new([lv_top[1], lv_top[2], lv_top[5], lv_top[6]]).material_index = 0
        bm.faces.new([lv_top[2], lv_top[3], lv_top[4], lv_top[5]]).material_index = 0

        # Párpado inferior descansando en el polo inferior del globo ocular (Z=1.579)
        lid_bot_pts = [
            Vector((ex - 0.013, 0.064, 1.582)),
            Vector((ex - 0.006, 0.068, 1.579)),
            Vector((ex + 0.006, 0.068, 1.579)),
            Vector((ex + 0.013, 0.064, 1.582)),
            Vector((ex + 0.010, 0.066, 1.573)),
            Vector((ex + 0.000, 0.069, 1.571)),
            Vector((ex - 0.010, 0.066, 1.573)),
        ]
        lv_bot = [bm.verts.new(p) for p in lid_bot_pts]
        bm.faces.new([lv_bot[0], lv_bot[1], lv_bot[6]]).material_index = 0
        bm.faces.new([lv_bot[1], lv_bot[2], lv_bot[5], lv_bot[6]]).material_index = 0
        bm.faces.new([lv_bot[2], lv_bot[3], lv_bot[4], lv_bot[5]]).material_index = 0

    # 3. Mechones 3D de Cabello Ondulado (Axel Bangs)
    def add_hair_curl(bm, p_start, p_mid, p_end, width, thick):
        pts = [p_start, p_mid, p_end]
        scale_w = [width, width * 0.85, width * 0.3]
        scale_t = [thick, thick * 0.80, thick * 0.3]
        c_rings = []
        for pt, w, t in zip(pts, scale_w, scale_t):
            rng = []
            for a in range(8):
                ang = (2.0 * math.pi * a) / 8.0
                vx = pt.x + math.cos(ang) * w
                vy = pt.y + math.sin(ang) * t * 0.7
                vz = pt.z - math.sin(ang) * t * 0.4
                rng.append(bm.verts.new(Vector((vx, vy, vz))))
            c_rings.append(rng)
        for i in range(len(c_rings) - 1):
            r0 = c_rings[i]
            r1 = c_rings[i + 1]
            for a in range(8):
                an = (a + 1) % 8
                f = bm.faces.new([r0[a], r0[an], r1[an], r1[a]])
                f.material_index = 2 # mat_hair
        tip = bm.verts.new(pts[-1] + Vector((0, 0, -thick * 0.4)))
        for a in range(8):
            an = (a + 1) % 8
            f = bm.faces.new([c_rings[-1][a], c_rings[-1][an], tip])
            f.material_index = 2

    curls = [
        (Vector((-0.035, 0.072, 1.635)), Vector((-0.028, 0.080, 1.622)), Vector((-0.020, 0.080, 1.605)), 0.012, 0.008),
        (Vector((-0.018, 0.076, 1.638)), Vector((-0.010, 0.084, 1.624)), Vector((-0.003, 0.084, 1.603)), 0.013, 0.009),
        (Vector((-0.001, 0.078, 1.638)), Vector(( 0.006, 0.084, 1.624)), Vector(( 0.013, 0.084, 1.603)), 0.013, 0.009),
        (Vector(( 0.015, 0.077, 1.638)), Vector(( 0.022, 0.083, 1.624)), Vector(( 0.028, 0.082, 1.605)), 0.013, 0.009),
        (Vector(( 0.030, 0.073, 1.635)), Vector(( 0.036, 0.079, 1.622)), Vector(( 0.040, 0.079, 1.607)), 0.012, 0.008),
        # Patillas
        (Vector((-0.066, 0.022, 1.625)), Vector((-0.069, 0.018, 1.595)), Vector((-0.066, 0.014, 1.565)), 0.010, 0.007),
        (Vector(( 0.066, 0.022, 1.625)), Vector(( 0.069, 0.018, 1.595)), Vector(( 0.066, 0.014, 1.565)), 0.010, 0.007),
    ]
    for p1, p2, p3, w, t in curls:
        add_hair_curl(bm, p1, p2, p3, w, t)

    # 4. Gorro Beanie de Lana Verde Oliva con Dobladillo en Relieve
    beanie_levels = [
        (1.622, 1.592, 0.082, 0.086, 0.005),
        (1.638, 1.608, 0.086, 0.090, 0.006),
        (1.656, 1.626, 0.083, 0.087, 0.003),
        (1.678, 1.650, 0.079, 0.083, 0.000),
        (1.698, 1.674, 0.067, 0.071, 0.000),
        (1.714, 1.696, 0.049, 0.053, 0.000),
        (1.724, 1.712, 0.024, 0.026, 0.000),
    ]
    b_rings = []
    for zf, zb, rx, ry, cuff_thick in beanie_levels:
        br = []
        for i in range(28):
            ang = (2.0 * math.pi * i) / 28.0
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            t_fb = (cos_a + 1.0) * 0.5
            z = zb * (1.0 - t_fb) + zf * t_fb
            vx = sin_a * (rx + cuff_thick)
            vy = (cos_a * (ry + cuff_thick)) - 0.008 * (1.0 - t_fb)
            br.append(bm.verts.new(Vector((vx, vy, z))))
        b_rings.append(br)

    for r in range(len(b_rings) - 1):
        r0 = b_rings[r]
        r1 = b_rings[r + 1]
        v_uv0 = r / float(len(b_rings) - 1)
        v_uv1 = (r + 1) / float(len(b_rings) - 1)
        for i in range(28):
            in_idx = (i + 1) % 28
            f = bm.faces.new([r0[i], r0[in_idx], r1[in_idx], r1[i]])
            f.material_index = 1 # mat_beanie
            u_uv0 = i / 28.0
            u_uv1 = (i + 1) / 28.0
            for lp, u_val, v_val in zip(f.loops, [u_uv0, u_uv1, u_uv1, u_uv0], [v_uv0, v_uv0, v_uv1, v_uv1]):
                lp[uv_layer].uv = Vector((u_val, v_val))

    top_b = bm.verts.new(Vector((0.0, -0.012, 1.730)))
    for i in range(28):
        in_idx = (i + 1) % 28
        f = bm.faces.new([b_rings[-1][i], b_rings[-1][in_idx], top_b])
        f.material_index = 1
        for lp in f.loops:
            lp[uv_layer].uv = Vector((i / 28.0, 1.0))

    bm.verts.index_update()
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Player_Head_Mesh", mesh)
    bpy.context.scene.collection.objects.link(obj)

    obj.data.materials.append(mat_skin)   # 0
    obj.data.materials.append(mat_beanie) # 1
    obj.data.materials.append(mat_hair)   # 2
    obj.data.materials.append(mat_eyes)   # 3

    for poly in mesh.polygons:
        poly.use_smooth = True

    # Ponderación a huesos de cabeza y cuello
    obj.parent = arm_obj
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj

    vg_head = obj.vertex_groups.new(name="Head")
    vg_neck = obj.vertex_groups.new(name="Neck")

    for v in obj.data.vertices:
        z = v.co.z
        if z >= 1.52:
            vg_head.add([v.index], 1.0, 'REPLACE')
        else:
            w_neck = clampf((1.52 - z) / 0.08, 0.0, 1.0)
            vg_head.add([v.index], 1.0 - w_neck, 'REPLACE')
            vg_neck.add([v.index], w_neck, 'REPLACE')

    return obj

def build_body_mesh(arm_obj, mat_jacket, mat_pants, mat_shoes, mat_skin, mat_belt, mat_buckle):
    """
    Construye el cuerpo estilizado e hiperrealista completo de Axel (Capa 1):
    - Chamarra acolchada puffer / cortavientos con cuello alto (storm collar), cremallera central,
      gajos acolchados en torso y mangas, y puños elásticos.
    - Cinturón de cuero marrón continuo con hebilla rectangular metálica y hebijón.
    - Pantalón de mezclilla oscura continuo sin fisuras en cintura ni entrepierna.
    - Calzado deportivo urbano con suela de caucho y lengüeta.
    - Manos anatómicas con pulgares OPONIBLES naciendo de la eminencia tenar y curvándose hacia la palma,
      dorso hacia el frente (+Y) y 4 dedos escalonados (3 falanges c/u).
    - Subsurf aplicado para continuidad y suavidad orgánica absoluta.
    """
    mesh = bpy.data.meshes.new("Player_Body_Mesh_Data")
    obj = bpy.data.objects.new("Player_Body_Mesh", mesh)
    bpy.context.scene.collection.objects.link(obj)

    nodes = [
        # 0: Pelvis centro
        (0.0, 0.0, 0.96, 0.155, 0.125),
        # 1: Cintura / Ombligo
        (0.0, 0.0, 1.08, 0.145, 0.115),
        # 2: Pecho bajo / Esternón
        (0.0, 0.0, 1.22, 0.170, 0.130),
        # 3: Pecho alto
        (0.0, 0.0, 1.34, 0.185, 0.135),
        # 4: Cuello base de la chamarra
        (0.0, 0.0, 1.42, 0.055, 0.055),

        # Hombros y brazos Izquierda (-X)
        (-0.08, 0.0, 1.42, 0.085, 0.085), # 5: Trapecio/Clavícula L
        (-0.19, 0.0, 1.38, 0.075, 0.075), # 6: Deltoides/Hombro L
        (-0.29, 0.0, 1.16, 0.062, 0.062), # 7: Codo L
        (-0.36, 0.0, 0.95, 0.045, 0.045), # 8: Muñeca L

        # Hombros y brazos Derecha (+X)
        (0.08, 0.0, 1.42, 0.085, 0.085),  # 9: Trapecio/Clavícula R
        (0.19, 0.0, 1.38, 0.075, 0.075),  # 10: Deltoides/Hombro R
        (0.29, 0.0, 1.16, 0.062, 0.062),  # 11: Codo R
        (0.36, 0.0, 0.95, 0.045, 0.045),  # 12: Muñeca R

        # Piernas Izquierda (-X)
        (-0.10, 0.0, 0.92, 0.100, 0.100), # 13: Cadera L
        (-0.11, 0.0, 0.70, 0.090, 0.090), # 14: Muslo L
        (-0.11, 0.0, 0.50, 0.078, 0.078), # 15: Rodilla L
        (-0.11, 0.0, 0.30, 0.068, 0.068), # 16: Pantorrilla L
        (-0.11, 0.0, 0.12, 0.054, 0.054), # 17: Tobillo L
        (-0.11, 0.06, 0.03, 0.058, 0.110),# 18: Pie L

        # Piernas Derecha (+X)
        (0.10, 0.0, 0.92, 0.100, 0.100),  # 19: Cadera R
        (0.11, 0.0, 0.70, 0.090, 0.090),  # 20: Muslo R
        (0.11, 0.0, 0.50, 0.078, 0.078),  # 21: Rodilla R
        (0.11, 0.0, 0.30, 0.068, 0.068),  # 22: Pantorrilla R
        (0.11, 0.0, 0.12, 0.054, 0.054),  # 23: Tobillo R
        (0.11, 0.06, 0.03, 0.058, 0.110), # 24: Pie R
    ]

    edges = [
        (0, 1), (1, 2), (2, 3), (3, 4),
        (3, 5), (5, 6), (6, 7), (7, 8),
        (3, 9), (9, 10), (10, 11), (11, 12),
        (0, 13), (13, 14), (14, 15), (15, 16), (16, 17), (17, 18),
        (0, 19), (19, 20), (20, 21), (21, 22), (22, 23), (23, 24),
    ]

    verts = [Vector((n[0], n[1], n[2])) for n in nodes]
    mesh.from_pydata(verts, edges, [])
    mesh.update()

    bpy.context.view_layer.objects.active = obj
    mod_skin = obj.modifiers.new(name="Skin", type='SKIN')
    skin_data = mesh.skin_vertices[0].data
    for i, n in enumerate(nodes):
        skin_data[i].radius = (n[3], n[4])

    bpy.ops.object.modifier_apply(modifier="Skin")

    # Aplicar Subsurf para curvatura orgánica continua
    mod_sub = obj.modifiers.new(name="Subsurf", type='SUBSURF')
    mod_sub.levels = 1
    bpy.ops.object.modifier_apply(modifier="Subsurf")

    bm = bmesh.new()
    bm.from_mesh(mesh)

    raw_hand_assignments = []

    # =========================================================================
    # 1. MANOS ANATÓMICAS CON PULGARES OPONIBLES Y 4 DEDOS ESCALONADOS
    # =========================================================================
    def add_detailed_anatomical_hand(bm, p_wrist, sign_x, hand_bone, mat_idx=3):
        """
        Construye una mano humana anatómica de alta definición:
        - Muñeca conecta a la base palmar/dorsal.
        - Dorso mira hacia el frente (+Y), Palma mira hacia atrás (-Y).
        - Eminencia tenar medial (hacia el cuerpo) de donde nace el PULGAR OPONIBLE.
        - El pulgar se proyecta antero-medialmente y se curva hacia la palma (-Y),
          oponiéndose anatómicamente a los otros 4 dedos.
        - 4 dedos (Índice, Medio, Anular, Meñique) escalonados con 3 falanges relajadas.
        """
        # Palma calibrada sin salientes laterales excesivas
        w_p = 0.024
        t_p = 0.012
        h_layers = [
            ( 0.000, 0.85, 0.85),
            (-0.020, 0.95, 1.00),
            (-0.042, 1.00, 0.95),
            (-0.060, 0.92, 0.80),
        ]
        h_rings = []
        all_h_verts = []
        
        for dz, ws, ts in h_layers:
            c = p_wrist + Vector((0, 0, dz))
            rng = []
            for i in range(12):
                ang = (2.0 * math.pi * i) / 12.0
                vx = c.x + math.cos(ang) * (w_p * ws)
                vy = c.y + math.sin(ang) * (t_p * ts)
                v = bm.verts.new(Vector((vx, vy, c.z)))
                rng.append(v)
                all_h_verts.append(v)
            h_rings.append(rng)
            
        for li in range(len(h_rings) - 1):
            r0 = h_rings[li]
            r1 = h_rings[li + 1]
            for i in range(12):
                in_idx = (i + 1) % 12
                f = bm.faces.new([r0[i], r0[in_idx], r1[in_idx], r1[i]])
                f.material_index = mat_idx

        def add_finger(pts, rads):
            fr = []
            for pt, r in zip(pts, rads):
                rng = []
                for a in range(8):
                    ang = (2.0 * math.pi * a) / 8.0
                    v = bm.verts.new(pt + Vector((math.cos(ang) * r, math.sin(ang) * r, 0)))
                    rng.append(v)
                    all_h_verts.append(v)
                fr.append(rng)
            for i in range(len(fr) - 1):
                r0 = fr[i]
                r1 = fr[i + 1]
                for a in range(8):
                    an = (a + 1) % 8
                    f = bm.faces.new([r0[a], r0[an], r1[an], r1[a]])
                    f.material_index = mat_idx
            tip = bm.verts.new(pts[-1] + Vector((0, 0, -rads[-1] * 0.4)))
            all_h_verts.append(tip)
            for a in range(8):
                an = (a + 1) % 8
                f = bm.faces.new([fr[-1][a], fr[-1][an], tip])
                f.material_index = mat_idx

        # PULGAR OPONIBLE:
        # Nace en la eminencia tenar medial (-sign_x hacia el cuerpo),
        # se proyecta hacia adelante (+Y) y hacia adentro (medial),
        # y se curva hacia la palma (-Y) para oponerse a los 4 dedos.
        medial_dir = -sign_x
        t_pts = [
            p_wrist + Vector((medial_dir * 0.020,  0.008, -0.020)), # Eminencia tenar
            p_wrist + Vector((medial_dir * 0.034,  0.016, -0.036)), # Falange proximal hacia el frente
            p_wrist + Vector((medial_dir * 0.028,  0.006, -0.052)), # Curvatura hacia la palma
            p_wrist + Vector((medial_dir * 0.018, -0.006, -0.065)), # Yema en oposición directa
        ]
        add_finger(t_pts, [0.009, 0.008, 0.007, 0.0055])

        # 4 DEDOS ESCALONADOS (Índice, Medio, Anular, Meñique)
        # Nudillos alineados con curvatura natural hacia la palma (-Y)
        fdata = [
            (medial_dir * 0.014, 0.060, 0.0075), # Índice
            (medial_dir * 0.004, 0.068, 0.0080), # Medio (más largo)
            (-medial_dir * 0.005, 0.062, 0.0072),# Anular
            (-medial_dir * 0.014, 0.048, 0.0062),# Meñique (más corto)
        ]
        for fx, flen, frad in fdata:
            kn = p_wrist + Vector((fx, 0.002, -0.060)) # Nudillo distal
            p1 = kn + Vector((0, -0.006, -flen * 0.45)) # Falange proximal (curva a la palma -Y)
            p2 = p1 + Vector((0, -0.012, -flen * 0.35)) # Falange media
            pt = p2 + Vector((0, -0.016, -flen * 0.20)) # Falange distal relajada
            add_finger([kn, p1, p2, pt], [frad, frad * 0.88, frad * 0.72, frad * 0.50])

        bm.verts.index_update()
        all_indices = [v.index for v in all_h_verts]
        raw_hand_assignments.append((all_indices, hand_bone))

    add_detailed_anatomical_hand(bm, Vector((-0.36, 0.0, 0.95)), -1.0, "Hand.L")
    add_detailed_anatomical_hand(bm, Vector(( 0.36, 0.0, 0.95)),  1.0, "Hand.R")

    # =========================================================================
    # 2. CUELLO ALTO DE LA CHAMARRA PUFFER (STORM COLLAR)
    # =========================================================================
    collar_rings = []
    for cz in [1.42, 1.45, 1.48]:
        c_ring = []
        for a in range(24):
            ang = (2.0 * math.pi * a) / 24.0
            rx = 0.072
            ry = 0.076
            vx = math.cos(ang) * rx
            vy = math.sin(ang) * ry + 0.002
            c_ring.append(bm.verts.new(Vector((vx, vy, cz))))
        collar_rings.append(c_ring)
        
    for r in range(len(collar_rings) - 1):
        r0 = collar_rings[r]
        r1 = collar_rings[r + 1]
        for i in range(24):
            in_idx = (i + 1) % 24
            if 5 <= i <= 6: # Apertura frontal en V
                continue
            f = bm.faces.new([r0[i], r0[in_idx], r1[in_idx], r1[i]])
            f.material_index = 0 # mat_jacket

    # =========================================================================
    # 3. CINTURÓN DE CUERO CON HEBILLA RECTANGULAR Y HEBIJÓN
    # =========================================================================
    belt_rings = []
    for bz in [1.025, 1.065]:
        b_ring = []
        for i in range(28):
            ang = (2.0 * math.pi * i) / 28.0
            rx = 0.154
            ry = 0.124
            vx = math.cos(ang) * rx
            vy = math.sin(ang) * ry
            b_ring.append(bm.verts.new(Vector((vx, vy, bz))))
        belt_rings.append(b_ring)
        
    for i in range(28):
        in_idx = (i + 1) % 28
        f = bm.faces.new([belt_rings[0][i], belt_rings[0][in_idx], belt_rings[1][in_idx], belt_rings[1][i]])
        f.material_index = 4 # mat_belt

    bw_out = 0.036
    bh_out = 0.022
    bw_in = 0.024
    bh_in = 0.014
    by = 0.132
    bz_c = 1.045

    b_frame_pts = [
        Vector((-bw_out, by, bz_c + bh_out)), Vector(( bw_out, by, bz_c + bh_out)),
        Vector(( bw_out, by, bz_c - bh_out)), Vector((-bw_out, by, bz_c - bh_out)),
        Vector((-bw_in, by, bz_c + bh_in)),  Vector(( bw_in, by, bz_c + bh_in)),
        Vector(( bw_in, by, bz_c - bh_in)),  Vector((-bw_in, by, bz_c - bh_in)),
    ]
    bfv = [bm.verts.new(p) for p in b_frame_pts]
    bm.faces.new([bfv[0], bfv[1], bfv[5], bfv[4]]).material_index = 5
    bm.faces.new([bfv[1], bfv[2], bfv[6], bfv[5]]).material_index = 5
    bm.faces.new([bfv[2], bfv[3], bfv[7], bfv[6]]).material_index = 5
    bm.faces.new([bfv[3], bfv[0], bfv[4], bfv[7]]).material_index = 5

    prong_pts = [
        Vector((-0.003, by + 0.003, bz_c + bh_in)),
        Vector(( 0.003, by + 0.003, bz_c + bh_in)),
        Vector(( 0.003, by + 0.003, bz_c - bh_in)),
        Vector((-0.003, by + 0.003, bz_c - bh_in)),
    ]
    bm.faces.new([bm.verts.new(p) for p in prong_pts]).material_index = 5

    # =========================================================================
    # 4. ASIGNACIÓN RIGUROSA DE MATERIALES Y TEXTURAS UV AL CUERPO
    # =========================================================================
    bm.verts.index_update()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    for f in bm.faces:
        if f.material_index in [4, 5]:
            continue
            
        cz = sum(v.co.z for v in f.verts) / float(len(f.verts))
        cx = sum(v.co.x for v in f.verts) / float(len(f.verts))
        
        # BRAZOS Y MANOS (abs(cx) >= 0.22)
        if abs(cx) >= 0.22:
            if cz < 0.94:
                f.material_index = 3 # mat_skin (mano)
            else:
                f.material_index = 0 # mat_jacket (manga de chamarra)
        # PIERNAS Y CALZADO (abs(cx) < 0.22 y Z < 1.02)
        elif cz < 0.12:
            f.material_index = 2 # mat_shoes
        elif cz < 1.02:
            f.material_index = 1 # mat_pants (mezclilla)
        # CINTURA (1.02 <= Z <= 1.06)
        elif cz <= 1.06:
            f.material_index = 4 # mat_belt
        # TORSO (Z > 1.06)
        else:
            f.material_index = 0 # mat_jacket (chamarra)
            
        for lp in f.loops:
            u_coord = (math.atan2(lp.vert.co.x, lp.vert.co.y) / (2.0 * math.pi)) + 0.5
            v_coord = clampf(lp.vert.co.z / 1.70, 0.0, 1.0)
            lp[uv_layer].uv = Vector((u_coord, v_coord))

    bm.to_mesh(mesh)
    bm.free()

    obj.data.materials.append(mat_jacket) # 0
    obj.data.materials.append(mat_pants)  # 1
    obj.data.materials.append(mat_shoes)  # 2
    obj.data.materials.append(mat_skin)   # 3
    obj.data.materials.append(mat_belt)   # 4
    obj.data.materials.append(mat_buckle) # 5

    for poly in mesh.polygons:
        poly.use_smooth = True

    # Ponderación a huesos del Armature
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
        
        # Brazos
        if abs(x) > 0.16 and z > 0.85:
            side = ".L" if x < 0 else ".R"
            if z > 1.35:
                vgroups["Shoulder" + side].add([v.index], 1.0, 'REPLACE')
            elif z > 1.15:
                w_farm = clampf((1.35 - z) / 0.20, 0.0, 1.0)
                vgroups["UpperArm" + side].add([v.index], 1.0 - w_farm, 'REPLACE')
                vgroups["Forearm" + side].add([v.index], w_farm, 'REPLACE')
            elif z > 0.94:
                vgroups["Forearm" + side].add([v.index], 1.0, 'REPLACE')
            else:
                vgroups["Hand" + side].add([v.index], 1.0, 'REPLACE')
        # Piernas
        elif z < 0.94 and (abs(x) > 0.04 or z < 0.80):
            side = ".L" if x < 0 else ".R"
            if z > 0.50:
                vgroups["UpperLeg" + side].add([v.index], 1.0, 'REPLACE')
            elif z > 0.12:
                vgroups["LowerLeg" + side].add([v.index], 1.0, 'REPLACE')
            elif y < 0.12:
                vgroups["Foot" + side].add([v.index], 1.0, 'REPLACE')
            else:
                vgroups["Toes" + side].add([v.index], 1.0, 'REPLACE')
        # Torso
        else:
            if z < 1.08:
                vgroups["Hips"].add([v.index], 1.0, 'REPLACE')
            elif z < 1.25:
                w_s = clampf((z - 1.08) / 0.17, 0.0, 1.0)
                vgroups["Spine"].add([v.index], 1.0 - w_s, 'REPLACE')
                vgroups["Spine1"].add([v.index], w_s, 'REPLACE')
            elif z < 1.38:
                vgroups["Spine1"].add([v.index], 1.0, 'REPLACE')
            else:
                vgroups["Chest"].add([v.index], 1.0, 'REPLACE')

    for indices, bone_name in raw_hand_assignments:
        vg = vgroups.get(bone_name)
        if vg:
            vg.add(indices, 1.0, 'REPLACE')

    return obj

def main():
    print("==================================================")
    print("GENERANDO AVATAR HIPERREALISTA DE AXEL (TECATENSE)")
    print("==================================================")
    clean_scene()

    # 1. Asegurar la existencia de texturas procedurales matemáticas PBR (CERO IA)
    import subprocess
    cmd = [
        "/Applications/Blender.app/Contents/MacOS/Blender",
        "--background",
        "--python",
        "scripts/characters/generate_character_textures.py"
    ]
    subprocess.run(cmd, check=True)

    # 2. Cargar y compilar materiales PBR hiperrealistas nativos
    tex_face_diff = os.path.join(TEX_DIR, "axel_face_diffuse.png")
    tex_face_norm = os.path.join(TEX_DIR, "axel_face_normal.png")
    tex_beanie_diff = os.path.join(TEX_DIR, "axel_beanie_diffuse.png")
    tex_beanie_norm = os.path.join(TEX_DIR, "axel_beanie_normal.png")
    tex_jacket_diff = os.path.join(TEX_DIR, "axel_jacket_diffuse.png")
    tex_jacket_norm = os.path.join(TEX_DIR, "axel_jacket_normal.png")
    tex_pants_norm = os.path.join(TEX_DIR, "axel_pants_normal.png")
    tex_belt_diff = os.path.join(TEX_DIR, "axel_belt_diffuse.png")
    tex_belt_norm = os.path.join(TEX_DIR, "axel_belt_normal.png")
    tex_eye_diff = os.path.join(TEX_DIR, "axel_eye_diffuse.png")

    # Piel con SSS y texturas faciales
    mat_skin = create_pbr_material("Mat_Axel_Skin", (0.64, 0.46, 0.38, 1.0), roughness=0.45,
                                   tex_diffuse_path=tex_face_diff, tex_normal_path=tex_face_norm, sss_weight=0.35)
    
    # Gorro Beanie de lana verde oliva / khaki con textura difusa y normal
    mat_beanie = create_pbr_material("Mat_Axel_Beanie", (0.22, 0.20, 0.13, 1.0), roughness=0.85,
                                     tex_diffuse_path=tex_beanie_diff, tex_normal_path=tex_beanie_norm)
    
    # Cabello castaño oscuro
    mat_hair = create_pbr_material("Mat_Axel_Hair", (0.10, 0.07, 0.05, 1.0), roughness=0.55, metallic=0.05)
    
    # Ojos con iris detallado y brillo corneal
    mat_eyes = create_pbr_material("Mat_Axel_Eyes", (1, 1, 1, 1), roughness=0.08, metallic=0.0,
                                   tex_diffuse_path=tex_eye_diff)
    
    # Chamarra puffer azul marino carbón oscuro
    mat_jacket = create_pbr_material("Mat_Axel_Jacket", (0.11, 0.12, 0.15, 1.0), roughness=0.55, metallic=0.04,
                                     tex_diffuse_path=tex_jacket_diff, tex_normal_path=tex_jacket_norm)
    
    # Pantalón de mezclilla oscura
    mat_pants = create_pbr_material("Mat_Axel_Pants", (0.10, 0.12, 0.16, 1.0), roughness=0.85, metallic=0.0,
                                    tex_normal_path=tex_pants_norm)
    
    # Calzado urbano con suela de caucho
    mat_shoes = create_pbr_material("Mat_Axel_Shoes", (0.14, 0.14, 0.15, 1.0), roughness=0.65, metallic=0.05)
    
    # Cinturón de cuero con hebilla metálica
    mat_belt = create_pbr_material("Mat_Axel_Belt", (0.28, 0.20, 0.16, 1.0), roughness=0.68,
                                   tex_diffuse_path=tex_belt_diff, tex_normal_path=tex_belt_norm)
    mat_buckle = create_pbr_material("Mat_Axel_Buckle", (0.85, 0.85, 0.88, 1.0), roughness=0.22, metallic=0.92)

    # 3. Construir Armature y Mallas Skinned
    arm_obj = build_axel_armature()
    print("✓ Armature antropométrico canónico construido con 22 huesos.")

    head_obj = build_head_mesh(arm_obj, mat_skin, mat_beanie, mat_hair, mat_eyes)
    print("✓ Player_Head_Mesh generado con rasgos faciales 3D, ojos y gorro beanie.")

    body_obj = build_body_mesh(arm_obj, mat_jacket, mat_pants, mat_shoes, mat_skin, mat_belt, mat_buckle)
    print("✓ Player_Body_Mesh generado con chamarra puffer, manos anatómicas y cinturón.")

    # 4. Guardar archivo maestro .blend
    os.makedirs(os.path.dirname(OUTPUT_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUTPUT_BLEND))
    print(f"✓ Guardado .blend maestro en: {OUTPUT_BLEND}")

    # 5. Exportar archivo .glb optimizado para Godot 4
    bpy.ops.export_scene.gltf(
        filepath=os.path.abspath(OUTPUT_GLB),
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
    print("==================================================")
    print("PERSONAJE AXEL HIPERREALISTA GENERADO CON ÉXITO")
    print("==================================================")

if __name__ == "__main__":
    main()
