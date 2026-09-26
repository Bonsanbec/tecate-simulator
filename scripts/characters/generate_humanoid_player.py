"""
=============================================================================
Generador 3D Procedural: Avatar Humanoide Estilizado para Tecate Simulator
=============================================================================
Construye un avatar humano con proporciones anatómicas limpias (H = 1.78 m),
orientado canónicamente hacia +Y en Blender (para que en glTF/Godot su frente
sea exactamente -Z). Los huesos de los brazos y piernas tienen sus ejes
alineados para animación biomecánica de marcha y trote sin deformaciones ni
aleteo lateral.
=============================================================================
"""

import os
import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler, Quaternion

OUTPUT_GLB = "godot_project/assets/characters/humanoid_player.glb"
OUTPUT_BLEND = "godot_project/assets/characters/humanoid_player.blend"

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

def create_pbr_material(name, base_color, roughness=0.7, metallic=0.0):
    """Crea un material Principled BSDF compatible con Godot 4."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    node_output.location = (300, 0)

    node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_bsdf.location = (0, 0)
    node_bsdf.inputs['Base Color'].default_value = base_color
    node_bsdf.inputs['Roughness'].default_value = roughness
    node_bsdf.inputs['Metallic'].default_value = metallic

    mat.node_tree.links.new(node_bsdf.outputs['BSDF'], node_output.inputs['Surface'])
    return mat

def build_humanoid_armature():
    """
    Construye el esqueleto antropométrico (22 huesos).
    Z: Arriba (Up en Blender, +Y en Godot)
    +Y: Adelante (Forward en Blender, -Z en Godot mediante Z_godot = -Y_blender)
    -X: Izquierda (.L)
    +X: Derecha (.R)
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

    # 2. Pelvis
    b_hips = edit_bones.new("Hips")
    b_hips.head = Vector((0.0, 0.0, 0.95))
    b_hips.tail = Vector((0.0, 0.0, 1.10))
    b_hips.parent = b_root

    # 3. Columna
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
    b_head.tail = Vector((0.0, 0.0, 1.80))
    b_head.parent = b_neck

    b_eyes = edit_bones.new("EyesAnchor")
    b_eyes.head = Vector((0.0, 0.08, 1.68))
    b_eyes.tail = Vector((0.0, 0.18, 1.68))
    b_eyes.parent = b_head

    # 5. Brazos (Colocados verticalmente naturales para oscilación biomecánica pura en X)
    # Brazo Izquierdo (X negativo)
    b_sh_l = edit_bones.new("Shoulder.L")
    b_sh_l.head = Vector((-0.06, 0.0, 1.50))
    b_sh_l.tail = Vector((-0.20, 0.0, 1.48))
    b_sh_l.parent = b_chest

    b_arm_l = edit_bones.new("UpperArm.L")
    b_arm_l.head = Vector((-0.20, 0.0, 1.48))
    b_arm_l.tail = Vector((-0.20, 0.0, 1.18))
    b_arm_l.parent = b_chest

    b_forearm_l = edit_bones.new("Forearm.L")
    b_forearm_l.head = Vector((-0.20, 0.0, 1.18))
    b_forearm_l.tail = Vector((-0.20, 0.0, 0.90))
    b_forearm_l.parent = b_arm_l

    b_hand_l = edit_bones.new("Hand.L")
    b_hand_l.head = Vector((-0.20, 0.0, 0.90))
    b_hand_l.tail = Vector((-0.20, 0.0, 0.77))
    b_hand_l.parent = b_forearm_l

    # Brazo Derecho (X positivo)
    b_sh_r = edit_bones.new("Shoulder.R")
    b_sh_r.head = Vector((0.06, 0.0, 1.50))
    b_sh_r.tail = Vector((0.20, 0.0, 1.48))
    b_sh_r.parent = b_chest

    b_arm_r = edit_bones.new("UpperArm.R")
    b_arm_r.head = Vector((0.20, 0.0, 1.48))
    b_arm_r.tail = Vector((0.20, 0.0, 1.18))
    b_arm_r.parent = b_chest

    b_forearm_r = edit_bones.new("Forearm.R")
    b_forearm_r.head = Vector((0.20, 0.0, 1.18))
    b_forearm_r.tail = Vector((0.20, 0.0, 0.90))
    b_forearm_r.parent = b_arm_r

    b_hand_r = edit_bones.new("Hand.R")
    b_hand_r.head = Vector((0.20, 0.0, 0.90))
    b_hand_r.tail = Vector((0.20, 0.0, 0.77))
    b_hand_r.parent = b_forearm_r

    # 6. Piernas
    # Pierna Izquierda
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

    # Pierna Derecha
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

def add_part_cylinder(bm, p_start, p_end, r_start, r_end, segments=12, rings=3, mat_idx=0):
    """Genera un segmento tubular cónico y devuelve la lista de vértices creados."""
    dir_v = p_end - p_start
    length = dir_v.length
    if length < 0.0001:
        return []
    dir_norm = dir_v.normalized()

    up_ref = Vector((0, 0, 1)) if abs(dir_norm.z) < 0.95 else Vector((0, 1, 0))
    x_axis = dir_norm.cross(up_ref).normalized()
    y_axis = x_axis.cross(dir_norm).normalized()

    created_verts = []
    ring_verts = []
    for ring_i in range(rings + 1):
        t = ring_i / float(rings)
        center = p_start + dir_v * t
        r = r_start + (r_end - r_start) * t
        current_ring = []
        for s in range(segments):
            angle = (2.0 * math.pi * s) / segments
            pos = center + (x_axis * math.cos(angle) + y_axis * math.sin(angle)) * r
            v = bm.verts.new(pos)
            current_ring.append(v)
            created_verts.append(v)
        ring_verts.append(current_ring)

    for ring_i in range(rings):
        r0 = ring_verts[ring_i]
        r1 = ring_verts[ring_i + 1]
        for s in range(segments):
            s_next = (s + 1) % segments
            f = bm.faces.new([r0[s], r0[s_next], r1[s_next], r1[s]])
            f.material_index = mat_idx

    f_bot = bm.faces.new(list(reversed(ring_verts[0])))
    f_bot.material_index = mat_idx
    f_top = bm.faces.new(ring_verts[-1])
    f_top.material_index = mat_idx

    return created_verts

def add_part_sphere(bm, center, radius, segments=12, rings=8, mat_idx=0):
    """Genera una esfera UV suave y devuelve la lista de vértices creados."""
    mesh_tmp = bpy.data.meshes.new("tmp_sph")
    bm_tmp = bmesh.new()
    bmesh.ops.create_uvsphere(bm_tmp, u_segments=segments, v_segments=rings, radius=radius)
    for v in bm_tmp.verts:
        v.co += center
    bm_tmp.to_mesh(mesh_tmp)
    bm_tmp.free()

    v_map = {}
    created_verts = []
    for v in mesh_tmp.vertices:
        new_v = bm.verts.new(v.co)
        v_map[v.index] = new_v
        created_verts.append(new_v)
    for p in mesh_tmp.polygons:
        try:
            f = bm.faces.new([v_map[i] for i in p.vertices])
            f.material_index = mat_idx
        except Exception:
            pass
    bpy.data.meshes.remove(mesh_tmp)
    return created_verts

def build_head_mesh(arm_obj, mat_skin, mat_hair, mat_sunglasses):
    """
    Construye la cabeza del jugador:
    - Rostro humanoide estilizado continuo hacia +Y.
    - Cabello urbano estilizado.
    - Lentes de sol urbanos al frente (+Y).
    - Capa Visual 2 (oculta para 1P, visible en 2P/3P y sombras).
    """
    mesh = bpy.data.meshes.new("Mesh_Player_Head")
    bm = bmesh.new()

    # 1. Cráneo y Rostro orgánico continuo (Elipsoide humanoide hacia +Y)
    c_head = Vector((0.0, 0.02, 1.70))
    verts_head = add_part_sphere(bm, c_head, 0.115, segments=16, rings=12, mat_idx=0)
    for v in verts_head:
        dz = v.co.z - c_head.z
        v.co.z += dz * 0.12
        if v.co.y > 0.02: # Frontal del rostro en +Y
            v.co.x *= 0.92

    # 2. Cuello superior continuo
    verts_neck = add_part_cylinder(bm, Vector((0.0, 0.0, 1.58)), Vector((0.0, 0.01, 1.66)), 0.055, 0.060, segments=12, rings=2, mat_idx=0)

    # 3. Cabello moderno estilizado (cubierta superior y posterior hacia -Y)
    verts_hair = add_part_sphere(bm, Vector((0.0, 0.01, 1.72)), 0.120, segments=16, rings=10, mat_idx=1)
    faces_to_remove = []
    for f in bm.faces:
        if f.material_index == 1:
            c = f.calc_center_median()
            # Eliminar frente inferior para dejar rostro visible
            if c.z < 1.68 and c.y > 0.01:
                faces_to_remove.append(f)
    bmesh.ops.delete(bm, geom=faces_to_remove, context='FACES')

    # 4. Gafas envolventes en el frontal (+Y)
    arc_segments = 8
    band_top = []
    band_bot = []
    r_face = 0.120
    for i in range(arc_segments + 1):
        # Arco que envuelve el frente del rostro (+Y) de sien a sien
        ang = math.radians(30.0 + (120.0 * float(i) / arc_segments))
        px = math.cos(ang) * (r_face * 0.92)
        py = math.sin(ang) * r_face + 0.02
        v_t = bm.verts.new(Vector((px, py, 1.715)))
        v_b = bm.verts.new(Vector((px, py, 1.665)))
        band_top.append(v_t)
        band_bot.append(v_b)

    for i in range(arc_segments):
        f = bm.faces.new([band_top[i], band_top[i+1], band_bot[i+1], band_bot[i]])
        f.material_index = 2

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Player_Head_Mesh", mesh)
    bpy.context.scene.collection.objects.link(obj)

    obj.data.materials.append(mat_skin)        # 0
    obj.data.materials.append(mat_hair)        # 1
    obj.data.materials.append(mat_sunglasses)  # 2

    obj.parent = arm_obj
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj

    # Asignar pesos: 100% de la cabeza a Head y Neck
    vg_head = obj.vertex_groups.new(name="Head")
    vg_neck = obj.vertex_groups.new(name="Neck")

    for v in mesh.vertices:
        if v.co.z >= 1.64:
            vg_head.add([v.index], 1.0, 'REPLACE')
        else:
            vg_neck.add([v.index], 1.0, 'REPLACE')

    return obj

def build_body_mesh(arm_obj, mat_jacket, mat_pants, mat_boots, mat_skin):
    """
    Construye la malla del cuerpo con asignación directa y desacoplada de grupos
    de vértices para evitar estiramientos no deseados en el torso.
    Capa Visual 1 (visible en 1P al mirar abajo, y en 2P/3P).
    """
    mesh = bpy.data.meshes.new("Mesh_Player_Body")
    bm = bmesh.new()

    bone_names = [
        "Root", "Hips", "Spine", "Spine1", "Chest", "Neck",
        "Shoulder.L", "UpperArm.L", "Forearm.L", "Hand.L",
        "Shoulder.R", "UpperArm.R", "Forearm.R", "Hand.R",
        "UpperLeg.L", "LowerLeg.L", "Foot.L", "Toes.L",
        "UpperLeg.R", "LowerLeg.R", "Foot.R", "Toes.R"
    ]

    raw_assignments = []

    def register_part(verts, bone_name, weight=1.0):
        raw_assignments.append((verts, bone_name, weight))

    # 1. Cuello base (Piel/Chamarra)
    v_neck = add_part_cylinder(bm, Vector((0.0, 0.0, 1.54)), Vector((0.0, 0.0, 1.62)), 0.056, 0.052, segments=12, rings=2, mat_idx=3)
    register_part(v_neck, "Neck")

    # 2. Torso: Pecho y Tórax (Chamarra urbana, leve prominencia hacia +Y)
    v_chest = add_part_cylinder(bm, Vector((0.0, 0.0, 1.54)), Vector((0.0, 0.01, 1.36)), 0.155, 0.145, segments=16, rings=3, mat_idx=0)
    register_part(v_chest, "Chest")

    # 3. Torso: Abdomen y Cintura
    v_waist = add_part_cylinder(bm, Vector((0.0, 0.01, 1.36)), Vector((0.0, 0.01, 1.15)), 0.145, 0.135, segments=16, rings=3, mat_idx=0)
    register_part(v_waist, "Spine1")

    # 4. Pelvis y Caderas (Pantalón)
    v_pelvis = add_part_cylinder(bm, Vector((0.0, 0.01, 1.15)), Vector((0.0, 0.0, 0.94)), 0.135, 0.145, segments=16, rings=3, mat_idx=1)
    register_part(v_pelvis, "Hips")

    # 5. Hombros
    v_sh_l = add_part_sphere(bm, Vector((-0.20, 0.0, 1.48)), 0.065, segments=10, rings=6, mat_idx=0)
    register_part(v_sh_l, "Shoulder.L")

    v_sh_r = add_part_sphere(bm, Vector((0.20, 0.0, 1.48)), 0.065, segments=10, rings=6, mat_idx=0)
    register_part(v_sh_r, "Shoulder.R")

    # 6. Brazo Izquierdo (X negativo, vertical natural)
    p_sh_l = Vector((-0.20, 0.0, 1.48))
    p_elb_l = Vector((-0.20, 0.0, 1.18))
    p_wri_l = Vector((-0.20, 0.02, 0.90))

    v_uarm_l = add_part_cylinder(bm, p_sh_l, p_elb_l, 0.058, 0.048, segments=12, rings=3, mat_idx=0)
    register_part(v_uarm_l, "UpperArm.L")

    v_elbow_l = add_part_sphere(bm, p_elb_l, 0.046, segments=8, rings=6, mat_idx=0)
    register_part(v_elbow_l, "UpperArm.L")

    v_farm_l = add_part_cylinder(bm, p_elb_l, p_wri_l, 0.046, 0.038, segments=12, rings=3, mat_idx=0)
    register_part(v_farm_l, "Forearm.L")

    # Mano Izquierda (Piel - visible en 1P)
    p_hand_l = Vector((-0.20, 0.03, 0.81))
    v_hand_l = add_part_cylinder(bm, p_wri_l, p_hand_l, 0.038, 0.032, segments=10, rings=2, mat_idx=3)
    register_part(v_hand_l, "Hand.L")

    v_thumb_l = add_part_cylinder(bm, Vector((-0.19, 0.03, 0.85)), Vector((-0.17, 0.06, 0.82)), 0.014, 0.010, segments=6, rings=2, mat_idx=3)
    register_part(v_thumb_l, "Hand.L")
    v_fing_l = add_part_cylinder(bm, p_hand_l, Vector((-0.20, 0.04, 0.74)), 0.030, 0.024, segments=8, rings=2, mat_idx=3)
    register_part(v_fing_l, "Hand.L")

    # 7. Brazo Derecho (X positivo, vertical natural)
    p_sh_r = Vector((0.20, 0.0, 1.48))
    p_elb_r = Vector((0.20, 0.0, 1.18))
    p_wri_r = Vector((0.20, 0.02, 0.90))

    v_uarm_r = add_part_cylinder(bm, p_sh_r, p_elb_r, 0.058, 0.048, segments=12, rings=3, mat_idx=0)
    register_part(v_uarm_r, "UpperArm.R")

    v_elbow_r = add_part_sphere(bm, p_elb_r, 0.046, segments=8, rings=6, mat_idx=0)
    register_part(v_elbow_r, "UpperArm.R")

    v_farm_r = add_part_cylinder(bm, p_elb_r, p_wri_r, 0.046, 0.038, segments=12, rings=3, mat_idx=0)
    register_part(v_farm_r, "Forearm.R")

    p_hand_r = Vector((0.20, 0.03, 0.81))
    v_hand_r = add_part_cylinder(bm, p_wri_r, p_hand_r, 0.038, 0.032, segments=10, rings=2, mat_idx=3)
    register_part(v_hand_r, "Hand.R")

    v_thumb_r = add_part_cylinder(bm, Vector((0.19, 0.03, 0.85)), Vector((0.17, 0.06, 0.82)), 0.014, 0.010, segments=6, rings=2, mat_idx=3)
    register_part(v_thumb_r, "Hand.R")
    v_fing_r = add_part_cylinder(bm, p_hand_r, Vector((0.20, 0.04, 0.74)), 0.030, 0.024, segments=8, rings=2, mat_idx=3)
    register_part(v_fing_r, "Hand.R")

    # 8. Pierna Izquierda
    p_hip_l = Vector((-0.11, 0.0, 0.92))
    p_knee_l = Vector((-0.11, 0.0, 0.50))
    p_ank_l = Vector((-0.11, 0.0, 0.11))

    v_thigh_l = add_part_cylinder(bm, p_hip_l, p_knee_l, 0.082, 0.064, segments=14, rings=4, mat_idx=1)
    register_part(v_thigh_l, "UpperLeg.L")

    v_knee_l = add_part_sphere(bm, p_knee_l, 0.064, segments=10, rings=6, mat_idx=1)
    register_part(v_knee_l, "UpperLeg.L")

    v_calf_l = add_part_cylinder(bm, p_knee_l, p_ank_l, 0.062, 0.048, segments=12, rings=4, mat_idx=1)
    register_part(v_calf_l, "LowerLeg.L")

    # Bota Izquierda (talón en -Y, punta en +Y)
    p_boot_l_top = Vector((-0.11, 0.0, 0.12))
    p_boot_l_ankle = Vector((-0.11, 0.03, 0.04))
    v_boot_l1 = add_part_cylinder(bm, p_boot_l_top, p_boot_l_ankle, 0.052, 0.058, segments=10, rings=2, mat_idx=2)
    register_part(v_boot_l1, "Foot.L")

    p_sole_l_heel = Vector((-0.11, -0.04, 0.02))
    p_sole_l_toe = Vector((-0.11, 0.18, 0.02))
    v_boot_l2 = add_part_cylinder(bm, p_sole_l_heel, p_sole_l_toe, 0.058, 0.050, segments=10, rings=2, mat_idx=2)
    v_boot_l2_toes = [v for v in v_boot_l2 if v.co.y > 0.12]
    v_boot_l2_foot = [v for v in v_boot_l2 if v.co.y <= 0.12]
    raw_assignments.append((v_boot_l2_toes, "Toes.L", 1.0))
    raw_assignments.append((v_boot_l2_foot, "Foot.L", 1.0))

    # 9. Pierna Derecha
    p_hip_r = Vector((0.11, 0.0, 0.92))
    p_knee_r = Vector((0.11, 0.0, 0.50))
    p_ank_r = Vector((0.11, 0.0, 0.11))

    v_thigh_r = add_part_cylinder(bm, p_hip_r, p_knee_r, 0.082, 0.064, segments=14, rings=4, mat_idx=1)
    register_part(v_thigh_r, "UpperLeg.R")

    v_knee_r = add_part_sphere(bm, p_knee_r, 0.064, segments=10, rings=6, mat_idx=1)
    register_part(v_knee_r, "UpperLeg.R")

    v_calf_r = add_part_cylinder(bm, p_knee_r, p_ank_r, 0.062, 0.048, segments=12, rings=4, mat_idx=1)
    register_part(v_calf_r, "LowerLeg.R")

    # Bota Derecha
    p_boot_r_top = Vector((0.11, 0.0, 0.12))
    p_boot_r_ankle = Vector((0.11, 0.03, 0.04))
    v_boot_r1 = add_part_cylinder(bm, p_boot_r_top, p_boot_r_ankle, 0.052, 0.058, segments=10, rings=2, mat_idx=2)
    register_part(v_boot_r1, "Foot.R")

    p_sole_r_heel = Vector((0.11, -0.04, 0.02))
    p_sole_r_toe = Vector((0.11, 0.18, 0.02))
    v_boot_r2 = add_part_cylinder(bm, p_sole_r_heel, p_sole_r_toe, 0.058, 0.050, segments=10, rings=2, mat_idx=2)
    v_boot_r2_toes = [v for v in v_boot_r2 if v.co.y > 0.12]
    v_boot_r2_foot = [v for v in v_boot_r2 if v.co.y <= 0.12]
    raw_assignments.append((v_boot_r2_toes, "Toes.R", 1.0))
    raw_assignments.append((v_boot_r2_foot, "Foot.R", 1.0))

    bm.verts.index_update()
    vertex_bone_assignments = []
    for verts, b_name, weight in raw_assignments:
        for v in verts:
            vertex_bone_assignments.append((v.index, b_name, weight))

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Player_Body_Mesh", mesh)
    bpy.context.scene.collection.objects.link(obj)

    obj.data.materials.append(mat_jacket) # 0
    obj.data.materials.append(mat_pants)  # 1
    obj.data.materials.append(mat_boots)  # 2
    obj.data.materials.append(mat_skin)   # 3

    obj.parent = arm_obj
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj

    v_groups = {name: obj.vertex_groups.new(name=name) for name in bone_names}

    for v_idx, b_name, weight in vertex_bone_assignments:
        if b_name in v_groups and v_idx < len(mesh.vertices):
            v_groups[b_name].add([v_idx], weight, 'REPLACE')

    return obj

def main():
    print("==================================================")
    print("INICIANDO GENERACIÓN DEL HUMANOIDE ESTILIZADO")
    print("==================================================")

    clean_scene()

    mat_skin = create_pbr_material("Mat_Humanoid_Skin", (0.84, 0.68, 0.58, 1.0), roughness=0.55, metallic=0.0)
    mat_hair = create_pbr_material("Mat_Humanoid_Hair", (0.16, 0.12, 0.10, 1.0), roughness=0.8, metallic=0.0)
    mat_sunglasses = create_pbr_material("Mat_Humanoid_Glasses", (0.05, 0.05, 0.06, 1.0), roughness=0.15, metallic=0.9)
    mat_jacket = create_pbr_material("Mat_Humanoid_Jacket", (0.20, 0.28, 0.38, 1.0), roughness=0.7, metallic=0.05)
    mat_pants = create_pbr_material("Mat_Humanoid_Pants", (0.14, 0.16, 0.20, 1.0), roughness=0.8, metallic=0.0)
    mat_boots = create_pbr_material("Mat_Humanoid_Boots", (0.11, 0.10, 0.09, 1.0), roughness=0.6, metallic=0.1)

    arm_obj = build_humanoid_armature()
    print("✓ Armature_Humanoid estructurado con 22 huesos.")

    head_obj = build_head_mesh(arm_obj, mat_skin, mat_hair, mat_sunglasses)
    print("✓ Player_Head_Mesh generado con rostro y peinado orgánico continuo.")

    body_obj = build_body_mesh(arm_obj, mat_jacket, mat_pants, mat_boots, mat_skin)
    print("✓ Player_Body_Mesh generado con pesos desacoplados por extremidad.")

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
    print("HUMANOIDE RIGGED GENERADO CON ÉXITO")
    print("==================================================")

if __name__ == "__main__":
    main()
