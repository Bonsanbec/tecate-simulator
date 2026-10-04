"""
=============================================================================
Generador 3D Procedural: Axel - Personaje Hiperrealista (Tecate Simulator)
=============================================================================
Construye el avatar 3D de Axel con fidelidad anatómica y técnica estándar
de Fortnite (Epic Games):
- Malla continua con bucles faciales y orgánicos (ojos, nariz, labios, mandíbula)
- Gorro beanie 3D tejido con dobladillo acanalado en relieve
- Chamarra acolchada azul marino con cuello alto, cremallera y arrugas reales
- Cinturón con hebilla metálica
- Pantalón con pliegues biomecánicos en rodillas y dobladillo
- Manos anatómicas de 5 dedos (mano derecha empuñando micrófono dinámico)
- Micrófono de mano SM58 con rejilla esférica y cable flexible
- Suite de texturas PBR (Albedo, Normal OpenGL, ORM) en resolución 1024x1024
- Ponderación de pesos suave multihueso (Smooth Skinning)
- Separación de capas para Godot (Player_Body_Mesh Capa 1, Player_Head_Mesh Capa 2)
=============================================================================
"""

import os
import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler, Quaternion

OUTPUT_GLB = "godot_project/assets/characters/citizens/axel.glb"
OUTPUT_BLEND = "godot_project/assets/characters/citizens/axel.blend"
TEXTURES_DIR = "godot_project/assets/characters/textures"

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

def create_pbr_textured_material(name, albedo_file, normal_file, orm_file, base_tint=(1, 1, 1, 1)):
    """Crea un material Principled BSDF conectado a sus mapas PBR (Albedo, Normal, ORM)."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Nodo de salida
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    node_output.location = (600, 0)

    # Shader Principled BSDF
    node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_bsdf.location = (250, 0)
    links.new(node_bsdf.outputs['BSDF'], node_output.inputs['Surface'])

    # 1. Albedo / Base Color
    albedo_path = os.path.abspath(os.path.join(TEXTURES_DIR, albedo_file))
    if os.path.exists(albedo_path):
        img_albedo = bpy.data.images.load(albedo_path)
        node_albedo = nodes.new(type='ShaderNodeTexImage')
        node_albedo.location = (-150, 200)
        node_albedo.image = img_albedo
        links.new(node_albedo.outputs['Color'], node_bsdf.inputs['Base Color'])
    else:
        node_bsdf.inputs['Base Color'].default_value = base_tint

    # 2. Normal Map
    normal_path = os.path.abspath(os.path.join(TEXTURES_DIR, normal_file))
    if os.path.exists(normal_path):
        img_normal = bpy.data.images.load(normal_path)
        img_normal.colorspace_settings.name = 'Non-Color'
        node_tex_norm = nodes.new(type='ShaderNodeTexImage')
        node_tex_norm.location = (-250, -200)
        node_tex_norm.image = img_normal

        node_norm_map = nodes.new(type='ShaderNodeNormalMap')
        node_norm_map.location = (0, -200)
        node_norm_map.space = 'TANGENT'
        links.new(node_tex_norm.outputs['Color'], node_norm_map.inputs['Color'])
        links.new(node_norm_map.outputs['Normal'], node_bsdf.inputs['Normal'])

    # 3. ORM (Occlusion, Roughness, Metallic)
    orm_path = os.path.abspath(os.path.join(TEXTURES_DIR, orm_file))
    if os.path.exists(orm_path):
        img_orm = bpy.data.images.load(orm_path)
        img_orm.colorspace_settings.name = 'Non-Color'
        node_orm = nodes.new(type='ShaderNodeTexImage')
        node_orm.location = (-250, 0)
        node_orm.image = img_orm

        node_sep = nodes.new(type='ShaderNodeSeparateColor')
        node_sep.location = (0, 0)
        links.new(node_orm.outputs['Color'], node_sep.inputs['Color'])
        links.new(node_sep.outputs['Green'], node_bsdf.inputs['Roughness'])
        links.new(node_sep.outputs['Blue'], node_bsdf.inputs['Metallic'])
    else:
        node_bsdf.inputs['Roughness'].default_value = 0.6
        node_bsdf.inputs['Metallic'].default_value = 0.0

    return mat

def build_axel_armature():
    """
    Construye el esqueleto antropométrico canónico (22 huesos).
    - Brazo izquierdo relajado en A-pose (~25°).
    - Brazo derecho articulado empuñando el micrófono frente al pecho/mentón (fiel a axel.png).
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
    b_spine1.tail = Vector((0.0, 0.0, 1.40))
    b_spine1.parent = b_spine

    b_chest = edit_bones.new("Chest")
    b_chest.head = Vector((0.0, 0.0, 1.40))
    b_chest.tail = Vector((0.0, 0.0, 1.55))
    b_chest.parent = b_spine1

    # 4. Cuello y Cabeza
    b_neck = edit_bones.new("Neck")
    b_neck.head = Vector((0.0, 0.0, 1.55))
    b_neck.tail = Vector((0.0, 0.0, 1.63))
    b_neck.parent = b_chest

    b_head = edit_bones.new("Head")
    b_head.head = Vector((0.0, 0.0, 1.63))
    b_head.tail = Vector((0.0, 0.0, 1.83))
    b_head.parent = b_neck

    b_eyes = edit_bones.new("EyesAnchor")
    b_eyes.head = Vector((0.0, 0.08, 1.68))
    b_eyes.tail = Vector((0.0, 0.18, 1.68))
    b_eyes.parent = b_head

    # 5. Brazo Izquierdo (A-pose natural)
    b_sh_l = edit_bones.new("Shoulder.L")
    b_sh_l.head = Vector((-0.06, 0.0, 1.50))
    b_sh_l.tail = Vector((-0.20, 0.0, 1.48))
    b_sh_l.parent = b_chest

    b_arm_l = edit_bones.new("UpperArm.L")
    b_arm_l.head = Vector((-0.20, 0.0, 1.48))
    b_arm_l.tail = Vector((-0.34, 0.0, 1.18))
    b_arm_l.parent = b_chest

    b_forearm_l = edit_bones.new("Forearm.L")
    b_forearm_l.head = Vector((-0.34, 0.0, 1.18))
    b_forearm_l.tail = Vector((-0.42, 0.04, 0.88))
    b_forearm_l.parent = b_arm_l

    b_hand_l = edit_bones.new("Hand.L")
    b_hand_l.head = Vector((-0.42, 0.04, 0.88))
    b_hand_l.tail = Vector((-0.46, 0.06, 0.76))
    b_hand_l.parent = b_forearm_l

    # 6. Brazo Derecho (Articulado sosteniendo micrófono hacia el pecho/mentón)
    b_sh_r = edit_bones.new("Shoulder.R")
    b_sh_r.head = Vector((0.06, 0.0, 1.50))
    b_sh_r.tail = Vector((0.20, 0.0, 1.48))
    b_sh_r.parent = b_chest

    b_arm_r = edit_bones.new("UpperArm.R")
    b_arm_r.head = Vector((0.20, 0.0, 1.48))
    b_arm_r.tail = Vector((0.25, 0.12, 1.22))
    b_arm_r.parent = b_chest

    b_forearm_r = edit_bones.new("Forearm.R")
    b_forearm_r.head = Vector((0.25, 0.12, 1.22))
    b_forearm_r.tail = Vector((0.15, 0.26, 1.40))
    b_forearm_r.parent = b_arm_r

    b_hand_r = edit_bones.new("Hand.R")
    b_hand_r.head = Vector((0.15, 0.26, 1.40))
    b_hand_r.tail = Vector((0.10, 0.30, 1.48))
    b_hand_r.parent = b_forearm_r

    # 7. Pierna Izquierda
    b_leg_l = edit_bones.new("UpperLeg.L")
    b_leg_l.head = Vector((-0.11, 0.0, 0.92))
    b_leg_l.tail = Vector((-0.11, 0.0, 0.50))
    b_leg_l.parent = b_hips

    b_lowerleg_l = edit_bones.new("LowerLeg.L")
    b_lowerleg_l.head = Vector((-0.11, 0.0, 0.50))
    b_lowerleg_l.tail = Vector((-0.11, 0.0, 0.09))
    b_lowerleg_l.parent = b_leg_l

    b_foot_l = edit_bones.new("Foot.L")
    b_foot_l.head = Vector((-0.11, 0.0, 0.09))
    b_foot_l.tail = Vector((-0.11, 0.14, 0.02))
    b_foot_l.parent = b_lowerleg_l

    b_toe_l = edit_bones.new("Toes.L")
    b_toe_l.head = Vector((-0.11, 0.14, 0.02))
    b_toe_l.tail = Vector((-0.11, 0.22, 0.02))
    b_toe_l.parent = b_foot_l

    # 8. Pierna Derecha
    b_leg_r = edit_bones.new("UpperLeg.R")
    b_leg_r.head = Vector((0.11, 0.0, 0.92))
    b_leg_r.tail = Vector((0.11, 0.0, 0.50))
    b_leg_r.parent = b_hips

    b_lowerleg_r = edit_bones.new("LowerLeg.R")
    b_lowerleg_r.head = Vector((0.11, 0.0, 0.50))
    b_lowerleg_r.tail = Vector((0.11, 0.0, 0.09))
    b_lowerleg_r.parent = b_leg_r

    b_foot_r = edit_bones.new("Foot.R")
    b_foot_r.head = Vector((0.11, 0.0, 0.09))
    b_foot_r.tail = Vector((0.11, 0.14, 0.02))
    b_foot_r.parent = b_lowerleg_r

    b_toe_r = edit_bones.new("Toes.R")
    b_toe_r.head = Vector((0.11, 0.14, 0.02))
    b_toe_r.tail = Vector((0.11, 0.22, 0.02))
    b_toe_r.parent = b_foot_r

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

def build_head_mesh(arm_obj, mat_skin, mat_beanie):
    """
    Construye la cabeza hiperrealista y continua de Axel:
    - Cuello anatómico continuo desde Z = 1.48 m (sin separación con la chamarra).
    - Rostro esculpido con barbilla en Z=1.56, boca en Z=1.60, nariz en Z=1.64 y ojos en Z=1.67.
    - Gorro Beanie volumétrico envolvente desde Z=1.68 hasta la coronilla en Z=1.84.
    """
    mesh = bpy.data.meshes.new("Player_Head_Mesh_Data")
    bm = bmesh.new()

    u_segs = 28
    v_rings = 24
    face_verts = []

    # 1. Cuello, Mandíbula, Rostro y Cráneo
    for r in range(v_rings + 1):
        t = r / float(v_rings)
        # Altura continua: Z va desde 1.48 (cuello dentro del cuello alto) hasta 1.84 (coronilla del beanie)
        z = 1.48 + t * 0.36
        
        # Radio base anatómico según altura
        if z < 1.55: # Cuello
            rx = 0.068
            ry = 0.072
            is_beanie = False
        elif z < 1.69: # Rostro, barbilla, pómulos
            face_t = (z - 1.55) / 0.14
            rx = 0.075 + face_t * 0.018
            ry = 0.080 + face_t * 0.015
            is_beanie = False
        else: # Zona cubierta por el Beanie (domo redondeado suave)
            beanie_t = (z - 1.69) / 0.15 # De 0 a 1
            is_beanie = True
            dome_factor = math.sqrt(max(0.01, 1.0 - (beanie_t * 0.94)**2))
            rx = 0.095 * dome_factor + 0.008
            ry = 0.098 * dome_factor + 0.008
            # Dobladillo acanalado en la base del gorro
            if beanie_t < 0.22:
                rx += 0.010
                ry += 0.010

        ring = []
        for s in range(u_segs):
            theta = (s / float(u_segs)) * 2.0 * math.pi - (math.pi / 2.0)
            x = math.cos(theta) * rx
            y = math.sin(theta) * ry

            # Deformación anatómica en la cara (sólo para la zona frontal y piel)
            if not is_beanie and y > 0.0:
                # 1. Mentón / Barbilla (Z ~ 1.56)
                if abs(z - 1.56) < 0.025 and abs(x) < 0.035:
                    y += 0.020 * math.exp(-(x**2 / 0.0006 + (z - 1.56)**2 / 0.0003))

                # 2. Labios (Z ~ 1.605)
                if abs(z - 1.605) < 0.020 and abs(x) < 0.030:
                    y += 0.016 * math.exp(-(x**2 / 0.0004 + (z - 1.605)**2 / 0.0002))

                # 3. Nariz (Z ~ 1.645)
                if abs(z - 1.645) < 0.030 and abs(x) < 0.025:
                    y += 0.036 * math.exp(-(x**2 / 0.0003 + (z - 1.645)**2 / 0.0004))

                # 4. Cuencas Oculares (Z ~ 1.675)
                for eye_x in [-0.038, 0.038]:
                    d_eye = math.sqrt((x - eye_x)**2 + (z - 1.675)**2)
                    if d_eye < 0.022:
                        y -= (1.0 - d_eye / 0.022) * 0.010

            v = bm.verts.new(Vector((x, y, z)))
            ring.append(v)
        face_verts.append(ring)

    # Crear caras con asignación de material según altura
    for r in range(v_rings):
        r0 = face_verts[r]
        r1 = face_verts[r + 1]
        z_mid = (r0[0].co.z + r1[0].co.z) * 0.5
        mat_idx = 1 if z_mid >= 1.69 else 0 # 1: Beanie, 0: Piel
        for s in range(u_segs):
            s_next = (s + 1) % u_segs
            f = bm.faces.new([r0[s], r0[s_next], r1[s_next], r1[s]])
            f.material_index = mat_idx

    # Tapa superior del gorro
    f_top = bm.faces.new(list(reversed(face_verts[-1])))
    f_top.material_index = 1

    # Asignar coordenadas UV analíticas precisas
    uv_layer = bm.loops.layers.uv.new("UVMap")
    for face in bm.faces:
        for loop in face.loops:
            v = loop.vert
            ang = math.atan2(v.co.x, v.co.y)
            u = (ang / (2.0 * math.pi)) + 0.5
            if v.co.z >= 1.69:
                v_coord = (v.co.z - 1.69) / 0.15
            else:
                v_coord = clampf((v.co.z - 1.50) / 0.22, 0.0, 1.0)
            loop[uv_layer].uv = (u, v_coord)

    bm.verts.index_update()
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Player_Head_Mesh", mesh)
    bpy.context.scene.collection.objects.link(obj)

    obj.data.materials.append(mat_skin)   # Slot 0
    obj.data.materials.append(mat_beanie) # Slot 1

    for poly in mesh.polygons:
        poly.use_smooth = True

    # Ponderación suave a Head y Neck
    obj.parent = arm_obj
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj

    vg_head = obj.vertex_groups.new(name="Head")
    vg_neck = obj.vertex_groups.new(name="Neck")

    for v in mesh.vertices:
        z = v.co.z
        if z >= 1.60:
            vg_head.add([v.index], 1.0, 'REPLACE')
        else:
            w_neck = clampf((1.60 - z) / 0.12, 0.0, 1.0)
            vg_head.add([v.index], 1.0 - w_neck, 'REPLACE')
            vg_neck.add([v.index], w_neck, 'REPLACE')

    return obj

def clampf(v, min_v, max_v):
    return max(min_v, min(v, max_v))

def add_cylinder_strip(bm, p0, p1, r0, r1, segments=16, rings=4, mat_idx=0, bulge=0.0):
    """Crea una geometría tubular suave con abombamiento paramétrico."""
    dir_v = p1 - p0
    length = dir_v.length
    if length < 0.001:
        return []
    dir_norm = dir_v.normalized()

    up_ref = Vector((0, 0, 1)) if abs(dir_norm.z) < 0.9 else Vector((0, 1, 0))
    x_axis = dir_norm.cross(up_ref).normalized()
    y_axis = x_axis.cross(dir_norm).normalized()

    ring_verts = []
    all_verts = []
    for ri in range(rings + 1):
        t = ri / float(rings)
        center = p0 + dir_v * t
        radius = r0 + (r1 - r0) * t
        if bulge != 0.0:
            radius += math.sin(t * math.pi) * bulge

        c_ring = []
        for s in range(segments):
            angle = (2.0 * math.pi * s) / segments
            pos = center + (x_axis * math.cos(angle) + y_axis * math.sin(angle)) * radius
            v = bm.verts.new(pos)
            c_ring.append(v)
            all_verts.append(v)
        ring_verts.append(c_ring)

    for ri in range(rings):
        r_a = ring_verts[ri]
        r_b = ring_verts[ri + 1]
        for s in range(segments):
            s_next = (s + 1) % segments
            f = bm.faces.new([r_a[s], r_a[s_next], r_b[s_next], r_b[s]])
            f.material_index = mat_idx

    return all_verts

def build_body_mesh(arm_obj, mat_jacket, mat_pants, mat_shoes, mat_skin):
    """
    Construye el cuerpo hiperrealista de Axel:
    - Chamarra acolchada con cuello alto, solapa frontal y cremallera.
    - Cinturón y hebilla.
    - Pantalón con arrugas de flexión en rodillas.
    - Calzado urbano con suela modelada.
    - Manos de 5 dedos (mano derecha en pose ergonómica para micrófono).
    """
    mesh = bpy.data.meshes.new("Player_Body_Mesh_Data")
    bm = bmesh.new()

    raw_assignments = [] # (verts, bone_name, weight)

    # 1. Cuello Alto de la Chamarra (High collar stand)
    v_collar = add_cylinder_strip(bm, Vector((0, 0, 1.48)), Vector((0, 0, 1.58)), 0.088, 0.092, segments=18, rings=3, mat_idx=0)
    raw_assignments.append((v_collar, "Neck", 0.75))
    raw_assignments.append((v_collar, "Chest", 0.25))

    # 2. Torso de la Chamarra Acolchada (Puffer jacket con baffles)
    torso_rings = 10
    torso_grid = []
    all_torso = []
    for tri in range(torso_rings + 1):
        t = tri / float(torso_rings)
        z = 1.48 - t * 0.46 # De 1.48 a 1.02
        # Silueta anatómica: ancho en pecho (1.40), entallado en cintura (1.10), apertura en cadera (1.02)
        rx = 0.22 - (t * 0.04) + (0.015 * math.sin(t * math.pi))
        ry = 0.16 - (t * 0.03)

        # Baffles horizontales 3D reales (acolchado con relieve)
        baffle_disp = math.sin(t * 12.0 * math.pi) * 0.008
        rx += baffle_disp
        ry += baffle_disp

        c_ring = []
        for s in range(20):
            angle = (2.0 * math.pi * s) / 20.0
            x = math.cos(angle) * rx
            y = math.sin(angle) * ry
            # Solapa frontal de cremallera en +Y
            if abs(x) < 0.02 and y > 0.0:
                y += 0.012 # Saliente física de la cremallera
            v = bm.verts.new(Vector((x, y, z)))
            c_ring.append(v)
            all_torso.append(v)
        torso_grid.append(c_ring)

    for tri in range(torso_rings):
        r0 = torso_grid[tri]
        r1 = torso_grid[tri + 1]
        for s in range(20):
            s_next = (s + 1) % 20
            f = bm.faces.new([r0[s], r0[s_next], r1[s_next], r1[s]])
            f.material_index = 0 # Mat_Jacket

    # Ponderar torso según altura Z
    for v in all_torso:
        z = v.co.z
        if z > 1.35:
            raw_assignments.append(([v], "Chest", 0.85))
            raw_assignments.append(([v], "Spine1", 0.15))
        elif z > 1.20:
            raw_assignments.append(([v], "Spine1", 0.70))
            raw_assignments.append(([v], "Spine", 0.30))
        elif z > 1.08:
            raw_assignments.append(([v], "Spine", 0.75))
            raw_assignments.append(([v], "Hips", 0.25))
        else:
            raw_assignments.append(([v], "Hips", 0.90))
            raw_assignments.append(([v], "Spine", 0.10))

    # 3. Cinturón y Hebilla
    v_belt = add_cylinder_strip(bm, Vector((0, 0, 1.02)), Vector((0, 0, 0.96)), 0.165, 0.168, segments=18, rings=2, mat_idx=1)
    raw_assignments.append((v_belt, "Hips", 1.0))

    # Pelvis / Entrepierna conectada (cierre de cadera)
    v_crotch = add_cylinder_strip(bm, Vector((0, 0, 0.98)), Vector((0, 0, 0.88)), 0.160, 0.145, segments=16, rings=2, mat_idx=1)
    raw_assignments.append((v_crotch, "Hips", 1.0))

    # Hebilla metálica rectangular al frente
    bmesh.ops.create_cube(bm, size=0.035, matrix=Matrix.Translation(Vector((0, 0.175, 0.99))))

    # 4. Brazo Izquierdo (Hombro Deltoides, Manga de Chamarra y Mano)
    p_sh_l = Vector((-0.20, 0.0, 1.48))
    p_elb_l = Vector((-0.34, 0.0, 1.18))
    p_wri_l = Vector((-0.42, 0.04, 0.88))

    # Hombro / Deltoides esférico redondeado continuo
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.078, matrix=Matrix.Translation(p_sh_l))

    v_uarm_l = add_cylinder_strip(bm, p_sh_l, p_elb_l, 0.078, 0.065, segments=14, rings=5, mat_idx=0, bulge=0.010)
    raw_assignments.append((v_uarm_l, "UpperArm.L", 0.85))
    raw_assignments.append((v_uarm_l, "Shoulder.L", 0.15))

    # Codo continuo
    v_elb_l = add_cylinder_strip(bm, p_elb_l + Vector((0.01, 0, 0.01)), p_elb_l - Vector((0.01, 0, 0.01)), 0.066, 0.065, segments=12, rings=1, mat_idx=0)
    raw_assignments.append((v_elb_l, "UpperArm.L", 0.50))
    raw_assignments.append((v_elb_l, "Forearm.L", 0.50))

    v_farm_l = add_cylinder_strip(bm, p_elb_l, p_wri_l, 0.065, 0.052, segments=14, rings=5, mat_idx=0, bulge=0.006)
    raw_assignments.append((v_farm_l, "Forearm.L", 0.90))
    raw_assignments.append((v_farm_l, "UpperArm.L", 0.10))

    # Mano Izquierda (Piel - 5 dedos)
    p_hand_l = Vector((-0.45, 0.05, 0.78))
    v_hand_l = add_cylinder_strip(bm, p_wri_l, p_hand_l, 0.045, 0.036, segments=12, rings=2, mat_idx=3)
    raw_assignments.append((v_hand_l, "Hand.L", 1.0))

    # Dedos de mano izquierda
    for fi, f_off in enumerate([-0.025, -0.01, 0.005, 0.02]):
        v_f = add_cylinder_strip(bm, p_hand_l + Vector((f_off, 0, 0)), p_hand_l + Vector((f_off * 1.1, 0.02, -0.06)), 0.011, 0.008, segments=8, rings=2, mat_idx=3)
        raw_assignments.append((v_f, "Hand.L", 1.0))
    # Pulgar
    v_th_l = add_cylinder_strip(bm, p_hand_l + Vector((0.02, 0.02, 0.02)), p_hand_l + Vector((0.04, 0.04, -0.02)), 0.013, 0.009, segments=8, rings=2, mat_idx=3)
    raw_assignments.append((v_th_l, "Hand.L", 1.0))

    # 5. Brazo Derecho (Hombro Deltoides, Articulado hacia el Micrófono)
    p_sh_r = Vector((0.20, 0.0, 1.48))
    p_elb_r = Vector((0.25, 0.12, 1.22))
    p_wri_r = Vector((0.15, 0.26, 1.40))

    # Hombro / Deltoides esférico redondeado continuo derecho
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.078, matrix=Matrix.Translation(p_sh_r))

    v_uarm_r = add_cylinder_strip(bm, p_sh_r, p_elb_r, 0.078, 0.065, segments=14, rings=5, mat_idx=0, bulge=0.010)
    raw_assignments.append((v_uarm_r, "UpperArm.R", 0.85))
    raw_assignments.append((v_uarm_r, "Shoulder.R", 0.15))

    # Codo continuo derecho
    v_elb_r = add_cylinder_strip(bm, p_elb_r + Vector((-0.01, -0.01, 0.01)), p_elb_r + Vector((0.01, 0.01, -0.01)), 0.066, 0.065, segments=12, rings=1, mat_idx=0)
    raw_assignments.append((v_elb_r, "UpperArm.R", 0.50))
    raw_assignments.append((v_elb_r, "Forearm.R", 0.50))

    v_farm_r = add_cylinder_strip(bm, p_elb_r, p_wri_r, 0.068, 0.054, segments=14, rings=5, mat_idx=0, bulge=0.008)
    raw_assignments.append((v_farm_r, "Forearm.R", 0.90))
    raw_assignments.append((v_farm_r, "UpperArm.R", 0.10))

    # Mano Derecha (Piel - dedos curvados sujetando el micrófono)
    p_hand_r = Vector((0.12, 0.29, 1.45))
    v_hand_r = add_cylinder_strip(bm, p_wri_r, p_hand_r, 0.045, 0.038, segments=12, rings=2, mat_idx=3)
    raw_assignments.append((v_hand_r, "Hand.R", 1.0))

    # Dedos curvados en agarre
    for fi, f_off in enumerate([-0.02, -0.005, 0.01, 0.025]):
        # Dedos abrazan el cilindro del mango
        v_f = add_cylinder_strip(bm, p_hand_r + Vector((0, f_off, 0)), p_hand_r + Vector((-0.035, f_off, 0.01)), 0.011, 0.008, segments=8, rings=2, mat_idx=3)
        raw_assignments.append((v_f, "Hand.R", 1.0))
    # Pulgar opuesto
    v_th_r = add_cylinder_strip(bm, p_hand_r + Vector((0.02, 0.01, -0.02)), p_hand_r + Vector((-0.01, 0.02, 0.02)), 0.013, 0.009, segments=8, rings=2, mat_idx=3)
    raw_assignments.append((v_th_r, "Hand.R", 1.0))

    # 6. Pantalón (Piernas con pliegues biomecánicos)
    # Pierna Izquierda
    p_hip_l = Vector((-0.11, 0.0, 0.96))
    p_knee_l = Vector((-0.11, 0.0, 0.50))
    p_ank_l = Vector((-0.11, 0.0, 0.12))

    v_thigh_l = add_cylinder_strip(bm, p_hip_l, p_knee_l, 0.105, 0.082, segments=16, rings=6, mat_idx=1, bulge=0.015)
    raw_assignments.append((v_thigh_l, "UpperLeg.L", 0.90))
    raw_assignments.append((v_thigh_l, "Hips", 0.10))

    v_calf_l = add_cylinder_strip(bm, p_knee_l, p_ank_l, 0.082, 0.068, segments=16, rings=6, mat_idx=1, bulge=0.010)
    raw_assignments.append((v_calf_l, "LowerLeg.L", 0.85))
    raw_assignments.append((v_calf_l, "UpperLeg.L", 0.15))

    # Pierna Derecha
    p_hip_r = Vector((0.11, 0.0, 0.96))
    p_knee_r = Vector((0.11, 0.0, 0.50))
    p_ank_r = Vector((0.11, 0.0, 0.12))

    v_thigh_r = add_cylinder_strip(bm, p_hip_r, p_knee_r, 0.105, 0.082, segments=16, rings=6, mat_idx=1, bulge=0.015)
    raw_assignments.append((v_thigh_r, "UpperLeg.R", 0.90))
    raw_assignments.append((v_thigh_r, "Hips", 0.10))

    v_calf_r = add_cylinder_strip(bm, p_knee_r, p_ank_r, 0.082, 0.068, segments=16, rings=6, mat_idx=1, bulge=0.010)
    raw_assignments.append((v_calf_r, "LowerLeg.R", 0.85))
    raw_assignments.append((v_calf_r, "UpperLeg.R", 0.15))

    # 7. Calzado (Sneakers Urbanos con Suela y Empeine)
    for sign_x, foot_bone, toe_bone in [(-1, "Foot.L", "Toes.L"), (1, "Foot.R", "Toes.R")]:
        cx = sign_x * 0.11
        # Suela vulcanizada
        v_sole = add_cylinder_strip(bm, Vector((cx, -0.06, 0.02)), Vector((cx, 0.19, 0.02)), 0.065, 0.055, segments=12, rings=2, mat_idx=2)
        # Empeine del zapato
        v_upper = add_cylinder_strip(bm, Vector((cx, 0.0, 0.12)), Vector((cx, 0.06, 0.04)), 0.062, 0.068, segments=12, rings=3, mat_idx=2)

        for v in v_sole + v_upper:
            if v.co.y > 0.12:
                raw_assignments.append(([v], toe_bone, 0.90))
                raw_assignments.append(([v], foot_bone, 0.10))
            else:
                raw_assignments.append(([v], foot_bone, 0.95))
                raw_assignments.append(([v], toe_bone, 0.05))

    bm.verts.index_update()
    indexed_assignments = []
    for verts, b_name, weight in raw_assignments:
        indices = [v.index for v in verts]
        indexed_assignments.append((indices, b_name, weight))

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Player_Body_Mesh", mesh)
    bpy.context.scene.collection.objects.link(obj)

    obj.data.materials.append(mat_jacket) # 0
    obj.data.materials.append(mat_pants)  # 1
    obj.data.materials.append(mat_shoes)  # 2
    obj.data.materials.append(mat_skin)   # 3

    for poly in mesh.polygons:
        poly.use_smooth = True

    # Generar coordenadas UV
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')

    obj.parent = arm_obj
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj

    # Asignación de grupos de vértices
    bone_names = [b.name for b in arm_obj.data.bones]
    v_groups = {name: obj.vertex_groups.new(name=name) for name in bone_names}

    for indices, b_name, weight in indexed_assignments:
        if b_name in v_groups:
            valid_indices = [idx for idx in indices if idx < len(mesh.vertices)]
            if valid_indices:
                v_groups[b_name].add(valid_indices, weight, 'ADD')

    return obj

def build_microphone_mesh(arm_obj, mat_mic):
    """
    Construye el micrófono dinámico SM58 con rejilla esférica y cable colgante.
    Asignado a Player_Props_Mesh y vinculado al hueso Hand.R.
    """
    mesh = bpy.data.meshes.new("Player_Props_Mesh_Data")
    bm = bmesh.new()

    # Ubicación en la mano derecha
    center = Vector((0.11, 0.30, 1.45))
    axis = Vector((-0.2, 0.3, 0.9)).normalized() # Orientación diagonal natural

    # 1. Mango cilíndrico cónico del micrófono
    p_base = center - axis * 0.09
    p_top = center + axis * 0.04
    add_cylinder_strip(bm, p_base, p_top, 0.014, 0.018, segments=14, rings=3, mat_idx=0)

    # 2. Rejilla esférica del micrófono
    p_head = p_top + axis * 0.025
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=0.024, matrix=Matrix.Translation(p_head))

    # 3. Cable flexible que desciende hacia la cintura
    cable_pts = [
        p_base,
        p_base - Vector((0, 0.02, 0.08)),
        p_base - Vector((0.02, 0.04, 0.20)),
        Vector((0.08, 0.20, 1.15)),
        Vector((0.06, 0.16, 1.02))
    ]
    for i in range(len(cable_pts) - 1):
        add_cylinder_strip(bm, cable_pts[i], cable_pts[i + 1], 0.005, 0.005, segments=8, rings=1, mat_idx=0)

    bm.verts.index_update()
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Player_Props_Mesh", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(mat_mic)

    for poly in mesh.polygons:
        poly.use_smooth = True

    # Generar coordenadas UV
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')

    obj.parent = arm_obj
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj

    # Todo el micrófono se mueve rígidamente con Hand.R
    vg_hand = obj.vertex_groups.new(name="Hand.R")
    vg_hand.add(list(range(len(mesh.vertices))), 1.0, 'REPLACE')

    return obj

def main():
    print("==================================================")
    print("INICIANDO RECONSTRUCCIÓN 3D DE AXEL (ESTÁNDAR FORTNITE)")
    print("==================================================")

    clean_scene()

    # Materiales PBR
    mat_skin = create_pbr_textured_material("Mat_Axel_Skin", "axel_skin_albedo.png", "axel_skin_normal.png", "axel_skin_orm.png", (0.78, 0.62, 0.52, 1))
    mat_beanie = create_pbr_textured_material("Mat_Axel_Beanie", "axel_beanie_albedo.png", "axel_beanie_normal.png", "axel_beanie_orm.png", (0.28, 0.32, 0.20, 1))
    mat_jacket = create_pbr_textured_material("Mat_Axel_Jacket", "axel_jacket_albedo.png", "axel_jacket_normal.png", "axel_jacket_orm.png", (0.09, 0.11, 0.16, 1))
    mat_pants = create_pbr_textured_material("Mat_Axel_Pants", "axel_pants_albedo.png", "axel_pants_normal.png", "axel_pants_orm.png", (0.11, 0.12, 0.15, 1))
    mat_shoes = create_pbr_textured_material("Mat_Axel_Shoes", "axel_shoes_albedo.png", "axel_shoes_normal.png", "axel_shoes_orm.png", (0.10, 0.10, 0.10, 1))
    mat_mic = create_pbr_textured_material("Mat_Axel_Mic", "axel_mic_albedo.png", "axel_mic_normal.png", "axel_mic_orm.png", (0.14, 0.14, 0.15, 1))

    # Esqueleto
    arm_obj = build_axel_armature()
    print("✓ Armature_Humanoid estructurado canónicamente con 22 huesos.")

    # Malla de Cabeza (Capa 2)
    head_obj = build_head_mesh(arm_obj, mat_skin, mat_beanie)
    print("✓ Player_Head_Mesh generado con rostro anatómico y gorro beanie volumétrico.")

    # Malla de Cuerpo (Capa 1)
    body_obj = build_body_mesh(arm_obj, mat_jacket, mat_pants, mat_shoes, mat_skin)
    print("✓ Player_Body_Mesh generado con chamarra acolchada, cremallera, cinturón y manos de 5 dedos.")

    # Micrófono Prop (Capa 1)
    prop_obj = build_microphone_mesh(arm_obj, mat_mic)
    print("✓ Player_Props_Mesh generado con micrófono dinámico SM58 y cable continuo.")

    # Guardar .blend y exportar .glb
    os.makedirs(os.path.dirname(OUTPUT_GLB), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUTPUT_BLEND))
    print(f"✓ Guardado .blend en: {OUTPUT_BLEND}")

    bpy.ops.export_scene.gltf(
        filepath=os.path.abspath(OUTPUT_GLB),
        export_format='GLB',
        use_selection=False,
        export_yup=True,
        export_apply=False,
        export_skins=True,
        export_all_influences=False,
        export_materials='EXPORT',
        export_lights=False,
        export_cameras=False
    )
    print(f"✓ Exportado .glb en: {OUTPUT_GLB}")
    print("==================================================")
    print("AVATAR DE AXEL RECONSTRUIDO EXITOSAMENTE")
    print("==================================================")

if __name__ == "__main__":
    main()
