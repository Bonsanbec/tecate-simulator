"""
=============================================================================
Generador 3D Paramétrico: Kiosco Octagonal Tradicional de Tecate, B.C.
(Parque Miguel Hidalgo) - Versión de Alta Fidelidad
=============================================================================
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# =============================================================================
# CONSTANTES Y COTAS ARQUITECTÓNICAS
# =============================================================================
OCT_APOTHEM = 3.35         # Radio inscrito / apotema base (m)
OCT_CIRCUM = OCT_APOTHEM / math.cos(math.pi / 8.0) # ~3.62624 m
BASE_HEIGHT = 1.20        # Cota de piso / altura zócalo (m)
CORNICE_OUT = 0.12        # Saliente moldura piso (m)
CORNICE_THICK = 0.10      # Espesor vertical moldura piso (m)

STAIR_STEPS = 7           # Número de peldaños
STAIR_WIDTH = 1.60        # Ancho libre de escalera (m)
STAIR_TREAD = 0.32        # Huella de peldaño (m)
STAIR_RISER = BASE_HEIGHT / STAIR_STEPS # ~0.17143 m

COL_RADIUS = 3.05         # Radio radial de centros de columnas (m)
PLINTH_SIZE = 0.55        # Lado de base cuadrada plinto (m)
PLINTH_HEIGHT = 0.20      # Altura plinto (Z = 1.20 a 1.40 m)
COLUMN_SIZE = 0.45        # Lado sección fuste ladrillo (m)
COLUMN_HEIGHT = 2.50      # Altura fuste (Z = 1.40 a 3.90 m)
CAPITAL_SIZE = 0.52       # Lado capitel blanco (m)
CAPITAL_HEIGHT = 0.15     # Altura capitel (Z = 3.75 a 3.90 m)

RING_R_OUT = 3.70         # Radio exterior anillo corona (Ø 7.40 m)
RING_R_IN = 3.15          # Radio interior anillo corona (Ø 6.30 m)
RING_Z_BOTTOM = 3.90      # Arranque anillo entablamento (m)
RING_HEIGHT = 0.45        # Altura anillo (Z = 3.90 a 4.35 m)

ROOF_R_BASE = 3.80        # Radio base cono cubierta (Ø 7.60 m)
ROOF_Z_EAVE = 4.35        # Cota del alero volado (m)
ROOF_Z_PEAK = 5.55        # Cota de la cúspide máxima (m)


def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)


def create_materials():
    mats = {}

    # 1. M_Piedra_Base: Cantería / laja irregular ocre con mortero gris
    m_piedra = bpy.data.materials.new(name="M_Piedra_Base")
    nodes = m_piedra.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.64, 0.52, 0.36, 1.0) # Tono laja ocre dorado tecatense
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Roughness"].default_value = 0.88
    mats["M_Piedra_Base"] = m_piedra

    # 2. M_Ladrillo_Pilar: Ladrillo cocido terracota / óxido
    m_ladrillo = bpy.data.materials.new(name="M_Ladrillo_Pilar")
    nodes = m_ladrillo.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.62, 0.25, 0.15, 1.0) # Terracota rojizo cálido
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Roughness"].default_value = 0.80
    mats["M_Ladrillo_Pilar"] = m_ladrillo

    # 3. M_Mortero_Gris: Mortero gris claro para juntas de ladrillo y piedra
    m_mortero = bpy.data.materials.new(name="M_Mortero_Gris")
    nodes = m_mortero.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.76, 0.74, 0.70, 1.0) # Cemento / cal claro
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Roughness"].default_value = 0.92
    mats["M_Mortero_Gris"] = m_mortero

    # 4. M_Estuco_Blanco: Estuco blanco marfil cálido / yeso
    m_estuco = bpy.data.materials.new(name="M_Estuco_Blanco")
    nodes = m_estuco.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.90, 0.89, 0.86, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Roughness"].default_value = 0.65
    mats["M_Estuco_Blanco"] = m_estuco

    # 5. M_Herreria_Negra: Negro forja grafito anticorrosivo
    m_hierro = bpy.data.materials.new(name="M_Herreria_Negra")
    nodes = m_hierro.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.04, 0.04, 0.04, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.85
        bsdf.inputs["Roughness"].default_value = 0.45
    mats["M_Herreria_Negra"] = m_hierro

    # 6. M_Teja_Terracota: Arcilla cocida roja tradicional colonial
    m_teja = bpy.data.materials.new(name="M_Teja_Terracota")
    nodes = m_teja.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.58, 0.23, 0.15, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Roughness"].default_value = 0.75
    mats["M_Teja_Terracota"] = m_teja

    # 7. M_Piso_Cantera: Cantera beige claro / losas de piso
    m_piso = bpy.data.materials.new(name="M_Piso_Cantera")
    nodes = m_piso.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.78, 0.76, 0.71, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Roughness"].default_value = 0.60
    mats["M_Piso_Cantera"] = m_piso

    # 8. M_Vidrio_Farol: Vidrio ámbar/cálido de los faroles
    m_vidrio = bpy.data.materials.new(name="M_Vidrio_Farol")
    nodes = m_vidrio.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.95, 0.90, 0.78, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.1
        bsdf.inputs["Roughness"].default_value = 0.25
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.95, 0.85, 0.60, 1.0)
            bsdf.inputs["Emission Strength"].default_value = 0.8
    mats["M_Vidrio_Farol"] = m_vidrio

    return mats


def get_octagon_vertices(radius, z):
    verts = []
    base_angle = -math.pi / 2.0 - math.pi / 8.0
    for k in range(8):
        ang = base_angle + k * (math.pi / 4.0)
        x = radius * math.cos(ang)
        y = radius * math.sin(ang)
        verts.append(Vector((x, y, z)))
    return verts


def create_annular_ring(bm, r_in, r_out, thick, segments=12, matrix=Matrix()):
    """Crea un anillo toroidal/anular extruido sólido y cerrado en el plano XZ."""
    v_front_in = []
    v_front_out = []
    v_back_in = []
    v_back_out = []
    half_t = thick / 2.0
    for i in range(segments):
        ang = 2.0 * math.pi * i / segments
        ca, sa = math.cos(ang), math.sin(ang)
        v_front_in.append(bm.verts.new(matrix @ Vector((ca * r_in, half_t, sa * r_in))))
        v_front_out.append(bm.verts.new(matrix @ Vector((ca * r_out, half_t, sa * r_out))))
        v_back_in.append(bm.verts.new(matrix @ Vector((ca * r_in, -half_t, sa * r_in))))
        v_back_out.append(bm.verts.new(matrix @ Vector((ca * r_out, -half_t, sa * r_out))))

    faces = []
    for i in range(segments):
        nxt = (i + 1) % segments
        faces.append(bm.faces.new([v_front_in[i], v_front_out[i], v_front_out[nxt], v_front_in[nxt]]))
        faces.append(bm.faces.new([v_back_in[nxt], v_back_out[nxt], v_back_out[i], v_back_in[i]]))
        faces.append(bm.faces.new([v_front_out[i], v_back_out[i], v_back_out[nxt], v_front_out[nxt]]))
        faces.append(bm.faces.new([v_front_in[nxt], v_back_in[nxt], v_back_in[i], v_front_in[i]]))
    return faces


def build_octagonal_base(mats, col):
    """
    Construye la Base Octagonal de Mampostería (Z = 0.0 a 1.20 m):
    - Plinto inferior de desplante (Z = 0 a 0.08 m).
    - Muro con hiladas de mampostería de piedra laja y juntas de mortero.
    - Piso superior de cantera (M_Piso_Cantera).
    - Moldura perimetral en voladizo (M_Estuco_Blanco).
    - Registro / Puerta de servicio empotrada en cara lateral derecha (-45°).
    """
    bm = bmesh.new()

    # 1. Zócalo / Desplante inferior de cimentación (Z = 0.0 a 0.08 m)
    r_foot = OCT_CIRCUM + 0.04
    v_foot_bot = [bm.verts.new(v) for v in get_octagon_vertices(r_foot, 0.0)]
    v_foot_top = [bm.verts.new(v) for v in get_octagon_vertices(r_foot, 0.08)]
    bm.faces.new(list(reversed(v_foot_bot))).material_index = 0

    for k in range(8):
        kn = (k + 1) % 8
        f = bm.faces.new([v_foot_bot[k], v_foot_bot[kn], v_foot_top[kn], v_foot_top[k]])
        f.material_index = 0

    # 2. Muro octagonal con hiladas de laja de piedra (Z = 0.08 m a 1.20 m)
    # Creamos 5 hiladas horizontales para articular la mampostería de piedra
    stone_courses = 5
    z_start = 0.08
    z_end = BASE_HEIGHT
    course_h = (z_end - z_start) / stone_courses

    v_prev_ring = [bm.verts.new(v) for v in get_octagon_vertices(OCT_CIRCUM, z_start)]
    # Chaflán de conexión con el zócalo
    for k in range(8):
        kn = (k + 1) % 8
        f = bm.faces.new([v_foot_top[k], v_foot_top[kn], v_prev_ring[kn], v_prev_ring[k]])
        f.material_index = 0

    for c in range(stone_courses):
        z_c_top = z_start + (c + 1) * course_h
        # Sutil variación de relieve en cada hilada (±6 mm) para realismo de cantería
        r_c = OCT_CIRCUM + (0.008 if c % 2 == 1 else -0.004)
        v_next_ring = [bm.verts.new(v) for v in get_octagon_vertices(r_c if c < stone_courses - 1 else OCT_CIRCUM, z_c_top)]

        for k in range(8):
            kn = (k + 1) % 8
            f = bm.faces.new([v_prev_ring[k], v_prev_ring[kn], v_next_ring[kn], v_next_ring[k]])
            f.material_index = 0 # Piedra base

        v_prev_ring = v_next_ring

    # Piso superior (Z = 1.20 m)
    f_top = bm.faces.new(v_prev_ring)
    f_top.material_index = 1 # Piso Cantera

    # 3. Moldura / Cornisa Perimetral Volada (Z = 1.10 m a 1.22 m, saliente +0.12 m)
    r_c_bot = OCT_CIRCUM + 0.02
    r_c_lip = OCT_CIRCUM + CORNICE_OUT
    r_c_top = OCT_CIRCUM + CORNICE_OUT - 0.01

    v_c_bot = [bm.verts.new(v) for v in get_octagon_vertices(r_c_bot, BASE_HEIGHT - CORNICE_THICK)]
    v_c_lip = [bm.verts.new(v) for v in get_octagon_vertices(r_c_lip, BASE_HEIGHT - 0.02)]
    v_c_top = [bm.verts.new(v) for v in get_octagon_vertices(r_c_top, BASE_HEIGHT + 0.02)]
    v_c_in  = [bm.verts.new(v) for v in get_octagon_vertices(OCT_CIRCUM, BASE_HEIGHT + 0.02)]

    for k in range(8):
        kn = (k + 1) % 8
        f1 = bm.faces.new([v_c_bot[k], v_c_bot[kn], v_c_lip[kn], v_c_lip[k]])
        f1.material_index = 2 # Estuco blanco
        f2 = bm.faces.new([v_c_lip[k], v_c_lip[kn], v_c_top[kn], v_c_top[k]])
        f2.material_index = 2
        f3 = bm.faces.new([v_c_top[k], v_c_top[kn], v_c_in[kn], v_c_in[k]])
        f3.material_index = 2

    # 4. Puerta de Servicio en Cara 1 (-45°)
    door_w = 0.65
    door_h = 0.85
    door_z_min = 0.15
    door_z_max = door_z_min + door_h

    ang_f1 = -math.pi / 4.0
    f1_normal = Vector((math.cos(ang_f1), math.sin(ang_f1), 0.0))
    f1_tangent = Vector((-math.sin(ang_f1), math.cos(ang_f1), 0.0))
    f1_center = f1_normal * OCT_APOTHEM
    f1_rot = Matrix.Rotation(ang_f1 - math.pi / 2.0, 4, 'Z')

    # Marco de ángulo de hierro
    frame_w = 0.04
    frame_res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((door_w + frame_w*2, 0.03, door_h + frame_w*2)), verts=frame_res['verts'])
    bmesh.ops.transform(bm, matrix=f1_rot, verts=frame_res['verts'])
    bmesh.ops.translate(bm, vec=f1_center + Vector((0, 0, door_z_min + door_h/2.0)) + f1_normal * 0.015, verts=frame_res['verts'])
    for v in frame_res['verts']:
        for f in v.link_faces:
            f.material_index = 3 # Herrería negra

    # Chapa central empotrada
    door_res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((door_w, 0.02, door_h)), verts=door_res['verts'])
    bmesh.ops.transform(bm, matrix=f1_rot, verts=door_res['verts'])
    bmesh.ops.translate(bm, vec=f1_center + Vector((0, 0, door_z_min + door_h/2.0)) + f1_normal * 0.02, verts=door_res['verts'])
    for v in door_res['verts']:
        for f in v.link_faces:
            f.material_index = 3

    # Tirador y cerrojo
    h_res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((0.025, 0.025, 0.10)), verts=h_res['verts'])
    bmesh.ops.transform(bm, matrix=f1_rot, verts=h_res['verts'])
    bmesh.ops.translate(bm, vec=f1_center + f1_tangent * (door_w * 0.3) + Vector((0, 0, door_z_min + door_h * 0.5)) + f1_normal * 0.045, verts=h_res['verts'])
    for v in h_res['verts']:
        for f in v.link_faces:
            f.material_index = 3

    for f in bm.faces:
        f.smooth = False

    mesh = bpy.data.meshes.new("Mesh_Base_Octagonal")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Base_Octagonal", mesh)
    obj.data.materials.append(mats["M_Piedra_Base"])     # 0
    obj.data.materials.append(mats["M_Piso_Cantera"])    # 1
    obj.data.materials.append(mats["M_Estuco_Blanco"])   # 2
    obj.data.materials.append(mats["M_Herreria_Negra"])  # 3

    col.objects.link(obj)
    return obj


def build_staircase(mats, col):
    """
    Construye la Escalinata de Acceso Frontal:
    - 7 peldaños de cantera con bocel (0.32 x 0.1714 m).
    - Alfardas/muros laterales de piedra laja en declive continuo que enmarcan la escalera.
    - Barandales de herrería negra con balaustres verticales.
    """
    bm = bmesh.new()

    half_w = STAIR_WIDTH / 2.0
    y_wall = -OCT_APOTHEM
    total_run = STAIR_STEPS * STAIR_TREAD
    y_start = y_wall - total_run

    for i in range(STAIR_STEPS):
        z_step_bot = i * STAIR_RISER
        z_step_top = (i + 1) * STAIR_RISER
        y_step_front = y_start + i * STAIR_TREAD

        # Huella (Cantera)
        v1 = bm.verts.new(Vector((-half_w, y_step_front, z_step_top)))
        v2 = bm.verts.new(Vector(( half_w, y_step_front, z_step_top)))
        v3 = bm.verts.new(Vector(( half_w, y_wall, z_step_top)))
        v4 = bm.verts.new(Vector((-half_w, y_wall, z_step_top)))
        f_tread = bm.faces.new([v1, v2, v3, v4])
        f_tread.material_index = 0

        # Contrahuella
        v5 = bm.verts.new(Vector((-half_w, y_step_front, z_step_bot)))
        v6 = bm.verts.new(Vector(( half_w, y_step_front, z_step_bot)))
        f_riser = bm.faces.new([v5, v6, v2, v1])
        f_riser.material_index = 0

        # Bocel/Nosing saliente (+2 cm)
        vn1 = bm.verts.new(Vector((-half_w - 0.02, y_step_front - 0.02, z_step_top)))
        vn2 = bm.verts.new(Vector(( half_w + 0.02, y_step_front - 0.02, z_step_top)))
        vn3 = bm.verts.new(Vector(( half_w + 0.02, y_step_front, z_step_top)))
        vn4 = bm.verts.new(Vector((-half_w - 0.02, y_step_front, z_step_top)))
        fn = bm.faces.new([vn1, vn2, vn3, vn4])
        fn.material_index = 0

    # Alfardas / Flancos laterales sólidos de piedra en pendiente
    alfarda_thick = 0.12
    for side_sign in [-1.0, 1.0]:
        x_in = side_sign * half_w
        x_out = side_sign * (half_w + alfarda_thick)

        # 4 vértices del trapecio lateral inclinado
        p_bot_front = Vector((x_out, y_start, 0.0))
        p_bot_back  = Vector((x_out, y_wall, 0.0))
        p_top_back  = Vector((x_out, y_wall, BASE_HEIGHT + 0.04))
        p_top_front = Vector((x_out, y_start, STAIR_RISER + 0.04))

        v_bf = bm.verts.new(p_bot_front)
        v_bb = bm.verts.new(p_bot_back)
        v_tb = bm.verts.new(p_top_back)
        v_tf = bm.verts.new(p_top_front)

        v_bf_in = bm.verts.new(Vector((x_in, y_start, 0.0)))
        v_bb_in = bm.verts.new(Vector((x_in, y_wall, 0.0)))
        v_tb_in = bm.verts.new(Vector((x_in, y_wall, BASE_HEIGHT + 0.04)))
        v_tf_in = bm.verts.new(Vector((x_in, y_start, STAIR_RISER + 0.04)))

        # Cara exterior de la alfarda (Piedra base)
        if side_sign < 0:
            f_ext = bm.faces.new([v_bf, v_bb, v_tb, v_tf])
            f_top_a = bm.faces.new([v_tf, v_tb, v_tb_in, v_tf_in])
        else:
            f_ext = bm.faces.new([v_bf, v_tf, v_tb, v_bb])
            f_top_a = bm.faces.new([v_tf_in, v_tb_in, v_tb, v_tf])

        f_ext.material_index = 1 # Piedra base
        f_top_a.material_index = 1

    # Barandales laterales inclinados a 0.90 m
    rail_h = 0.90
    for side_x in [-half_w, half_w]:
        p_start_bot = Vector((side_x, y_start + 0.10, STAIR_RISER))
        p_start_top = p_start_bot + Vector((0, 0, rail_h))
        p_end_bot = Vector((side_x, y_wall, BASE_HEIGHT))
        p_end_top = p_end_bot + Vector((0, 0, rail_h))

        dir_vec = (p_end_top - p_start_top)
        length = dir_vec.length
        mid_point = (p_start_top + p_end_top) / 2.0
        rot_quat = Vector((0, 0, 1)).rotation_difference(dir_vec)

        res = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((0.04, 0.05, length)), verts=res['verts'])
        bmesh.ops.rotate(bm, cent=Vector((0, 0, 0)), matrix=rot_quat.to_matrix(), verts=res['verts'])
        bmesh.ops.translate(bm, vec=mid_point, verts=res['verts'])
        for f in res['verts']:
            for face in f.link_faces:
                face.material_index = 2 # Herrería negra

        for step_idx in range(STAIR_STEPS):
            bx = side_x
            by = y_start + step_idx * STAIR_TREAD + 0.16
            bz = (step_idx + 1) * STAIR_RISER
            tz = bz + rail_h
            post_h = tz - bz
            res_p = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=Vector((0.022, 0.022, post_h)), verts=res_p['verts'])
            bmesh.ops.translate(bm, vec=Vector((bx, by, bz + post_h / 2.0)), verts=res_p['verts'])
            for f in res_p['verts']:
                for face in f.link_faces:
                    face.material_index = 2

    for f in bm.faces:
        f.smooth = False

    mesh = bpy.data.meshes.new("Mesh_Escalinata")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Escalinata", mesh)
    obj.data.materials.append(mats["M_Piso_Cantera"])    # 0
    obj.data.materials.append(mats["M_Piedra_Base"])     # 1
    obj.data.materials.append(mats["M_Herreria_Negra"])  # 2

    col.objects.link(obj)
    return obj


def build_colonial_lantern(bm, center_pos, rotation_z):
    """
    Construye un farol colonial tradicional de Tecate:
    - Placa mural y brazo de forja en 'S' saliente.
    - Caja trapezoidal clásica de 4 caras de vidrio ámbar enmarcada en hierro.
    - Cubierta piramidal con cúspide y remate inferior.
    """
    rot_mat = Matrix.Rotation(rotation_z, 4, 'Z')

    # 1. Placa de anclaje a la pared de ladrillo
    plate_res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((0.08, 0.02, 0.20)), verts=plate_res['verts'])
    bmesh.ops.transform(bm, matrix=rot_mat, verts=plate_res['verts'])
    bmesh.ops.translate(bm, vec=center_pos, verts=plate_res['verts'])
    for v in plate_res['verts']:
        for f in v.link_faces:
            f.material_index = 2 # Herrería negra

    # 2. Brazo de soporte curvo en 'S'
    arm_res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((0.03, 0.22, 0.03)), verts=arm_res['verts'])
    bmesh.ops.translate(bm, vec=Vector((0.0, 0.11, 0.04)), verts=arm_res['verts'])
    bmesh.ops.transform(bm, matrix=rot_mat, verts=arm_res['verts'])
    bmesh.ops.translate(bm, vec=center_pos, verts=arm_res['verts'])
    for v in arm_res['verts']:
        for f in v.link_faces:
            f.material_index = 2

    # Puntal diagonal inferior
    strut_res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((0.02, 0.16, 0.02)), verts=strut_res['verts'])
    bmesh.ops.rotate(bm, cent=Vector((0,0,0)), matrix=Matrix.Rotation(math.radians(-35), 4, 'X'), verts=strut_res['verts'])
    bmesh.ops.translate(bm, vec=Vector((0.0, 0.10, -0.06)), verts=strut_res['verts'])
    bmesh.ops.transform(bm, matrix=rot_mat, verts=strut_res['verts'])
    bmesh.ops.translate(bm, vec=center_pos, verts=strut_res['verts'])
    for v in strut_res['verts']:
        for f in v.link_faces:
            f.material_index = 2

    # 3. Caja trapezoidal del farol (más ancha arriba que abajo)
    lantern_center = center_pos + rot_mat @ Vector((0.0, 0.24, -0.02))
    h_cage = 0.24
    w_top = 0.18
    w_bot = 0.12

    # Vidrio interior trapezoidal
    v_vt = [
        Vector((-w_top/2, -w_top/2, h_cage/2)),
        Vector(( w_top/2, -w_top/2, h_cage/2)),
        Vector(( w_top/2,  w_top/2, h_cage/2)),
        Vector((-w_top/2,  w_top/2, h_cage/2)),
    ]
    v_vb = [
        Vector((-w_bot/2, -w_bot/2, -h_cage/2)),
        Vector(( w_bot/2, -w_bot/2, -h_cage/2)),
        Vector(( w_bot/2,  w_bot/2, -h_cage/2)),
        Vector((-w_bot/2,  w_bot/2, -h_cage/2)),
    ]

    vt_bm = [bm.verts.new(lantern_center + rot_mat @ p) for p in v_vt]
    vb_bm = [bm.verts.new(lantern_center + rot_mat @ p) for p in v_vb]

    for i in range(4):
        nxt = (i + 1) % 4
        f_glass = bm.faces.new([vb_bm[i], vb_bm[nxt], vt_bm[nxt], vt_bm[i]])
        f_glass.material_index = 3 # Vidrio farol

    # Costillas y marcos de hierro en las 4 aristas
    for i in range(4):
        rib_res = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((0.016, 0.016, h_cage + 0.02)), verts=rib_res['verts'])
        rib_p = lantern_center + rot_mat @ ((v_vt[i] + v_vb[i]) / 2.0)
        bmesh.ops.transform(bm, matrix=rot_mat, verts=rib_res['verts'])
        bmesh.ops.translate(bm, vec=rib_p, verts=rib_res['verts'])
        for v in rib_res['verts']:
            for f in v.link_faces:
                f.material_index = 2 # Herrería

    # 4. Tejadillo piramidal de 4 aguas con alero
    roof_h = 0.12
    r_alero = w_top + 0.04
    v_rt = [
        Vector((-r_alero/2, -r_alero/2, h_cage/2)),
        Vector(( r_alero/2, -r_alero/2, h_cage/2)),
        Vector(( r_alero/2,  r_alero/2, h_cage/2)),
        Vector((-r_alero/2,  r_alero/2, h_cage/2)),
    ]
    p_peak = Vector((0.0, 0.0, h_cage/2 + roof_h))

    v_rt_bm = [bm.verts.new(lantern_center + rot_mat @ p) for p in v_rt]
    v_peak_bm = bm.verts.new(lantern_center + rot_mat @ p_peak)

    for i in range(4):
        nxt = (i + 1) % 4
        f_roof = bm.faces.new([v_rt_bm[i], v_rt_bm[nxt], v_peak_bm])
        f_roof.material_index = 2 # Herrería

    # Remate superior esférico/puntal
    spire_res = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.025, radius2=0.005, depth=0.06)
    bmesh.ops.transform(bm, matrix=rot_mat, verts=spire_res['verts'])
    bmesh.ops.translate(bm, vec=lantern_center + rot_mat @ (p_peak + Vector((0,0,0.03))), verts=spire_res['verts'])
    for v in spire_res['verts']:
        for f in v.link_faces:
            f.material_index = 2

    # Remate inferior en gota
    drop_res = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.015, radius2=0.005, depth=0.05)
    bmesh.ops.rotate(bm, cent=Vector((0,0,0)), matrix=Matrix.Rotation(math.pi, 4, 'X'), verts=drop_res['verts'])
    bmesh.ops.transform(bm, matrix=rot_mat, verts=drop_res['verts'])
    bmesh.ops.translate(bm, vec=lantern_center + rot_mat @ Vector((0,0,-h_cage/2 - 0.025)), verts=drop_res['verts'])
    for v in drop_res['verts']:
        for f in v.link_faces:
            f.material_index = 2


def build_columns(mats, col):
    """
    Construye las 8 Columnas Radiales (R = 3.05 m):
    - Plinto base blanco (0.55 x 0.55 x 0.20 m con chaflán 45°).
    - Fuste con 28 hiladas de ladrillo rojo y llagas de mortero gris.
    - Capitel blanco moldurado (0.52 x 0.52 x 0.15 m).
    - Faroles coloniales en Z = 3.10 m.
    """
    bm = bmesh.new()
    base_angle = -math.pi / 2.0 - math.pi / 8.0

    for k in range(8):
        ang = base_angle + k * (math.pi / 4.0)
        cx = COL_RADIUS * math.cos(ang)
        cy = COL_RADIUS * math.sin(ang)
        col_pos = Vector((cx, cy, 0.0))
        rot_z = ang - math.pi / 2.0
        rot_mat = Matrix.Rotation(rot_z, 4, 'Z')

        # 1. Plinto base blanco (Z = 1.20 a 1.40 m)
        p_res = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((PLINTH_SIZE, PLINTH_SIZE, 0.14)), verts=p_res['verts'])
        bmesh.ops.transform(bm, matrix=rot_mat, verts=p_res['verts'])
        bmesh.ops.translate(bm, vec=col_pos + Vector((0, 0, 1.20 + 0.07)), verts=p_res['verts'])
        for v in p_res['verts']:
            for f in v.link_faces:
                f.material_index = 1 # Estuco blanco

        ch_res = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((PLINTH_SIZE - 0.04, PLINTH_SIZE - 0.04, 0.06)), verts=ch_res['verts'])
        bmesh.ops.transform(bm, matrix=rot_mat, verts=ch_res['verts'])
        bmesh.ops.translate(bm, vec=col_pos + Vector((0, 0, 1.34 + 0.03)), verts=ch_res['verts'])
        for v in ch_res['verts']:
            for f in v.link_faces:
                f.material_index = 1 # Estuco blanco

        # 2. Fuste de ladrillo aparente con hiladas y llagas de mortero (Z = 1.40 a 3.75 m)
        fuste_z_start = 1.40
        fuste_z_end = 3.75
        fuste_h = fuste_z_end - fuste_z_start
        num_courses = 28
        total_course_h = fuste_h / num_courses
        brick_h = total_course_h * 0.82
        mortar_h = total_course_h * 0.18

        for c in range(num_courses):
            # Bloque de ladrillo
            cz_brick = fuste_z_start + c * total_course_h + brick_h / 2.0
            c_size = COLUMN_SIZE - (0.004 if c % 2 == 0 else 0.001)
            b_res = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=Vector((c_size, c_size, brick_h)), verts=b_res['verts'])
            bmesh.ops.transform(bm, matrix=rot_mat, verts=b_res['verts'])
            bmesh.ops.translate(bm, vec=col_pos + Vector((0, 0, cz_brick)), verts=b_res['verts'])
            for v in b_res['verts']:
                for f in v.link_faces:
                    f.material_index = 0 # Ladrillo pilar

            # Llaga de mortero gris (recesada 6 mm hacia adentro)
            if c < num_courses - 1:
                cz_mortar = fuste_z_start + (c + 1) * total_course_h - mortar_h / 2.0
                m_size = COLUMN_SIZE - 0.012
                m_res = bmesh.ops.create_cube(bm, size=1.0)
                bmesh.ops.scale(bm, vec=Vector((m_size, m_size, mortar_h)), verts=m_res['verts'])
                bmesh.ops.transform(bm, matrix=rot_mat, verts=m_res['verts'])
                bmesh.ops.translate(bm, vec=col_pos + Vector((0, 0, cz_mortar)), verts=m_res['verts'])
                for v in m_res['verts']:
                    for f in v.link_faces:
                        f.material_index = 4 # Mortero gris

        # 3. Capitel blanco moldurado (Z = 3.75 a 3.90 m)
        c1_res = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((COLUMN_SIZE + 0.03, COLUMN_SIZE + 0.03, 0.05)), verts=c1_res['verts'])
        bmesh.ops.transform(bm, matrix=rot_mat, verts=c1_res['verts'])
        bmesh.ops.translate(bm, vec=col_pos + Vector((0, 0, 3.75 + 0.025)), verts=c1_res['verts'])
        for v in c1_res['verts']:
            for f in v.link_faces:
                f.material_index = 1 # Estuco blanco

        c2_res = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((CAPITAL_SIZE, CAPITAL_SIZE, 0.10)), verts=c2_res['verts'])
        bmesh.ops.transform(bm, matrix=rot_mat, verts=c2_res['verts'])
        bmesh.ops.translate(bm, vec=col_pos + Vector((0, 0, 3.80 + 0.05)), verts=c2_res['verts'])
        for v in c2_res['verts']:
            for f in v.link_faces:
                f.material_index = 1 # Estuco blanco

        # 4. Farol Colonial (Z = 3.10 m) en la cara exterior
        outer_face_offset = rot_mat @ Vector((0.0, COLUMN_SIZE / 2.0, 0.0))
        lantern_anchor = col_pos + outer_face_offset + Vector((0, 0, 3.10))
        build_colonial_lantern(bm, lantern_anchor, rot_z)

    for f in bm.faces:
        f.smooth = False

    mesh = bpy.data.meshes.new("Mesh_Columnas_Octeto")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Columnas_Octeto", mesh)
    obj.data.materials.append(mats["M_Ladrillo_Pilar"]) # 0
    obj.data.materials.append(mats["M_Estuco_Blanco"])  # 1
    obj.data.materials.append(mats["M_Herreria_Negra"]) # 2
    obj.data.materials.append(mats["M_Vidrio_Farol"])   # 3
    obj.data.materials.append(mats["M_Mortero_Gris"])   # 4

    col.objects.link(obj)
    return obj


def build_perimeter_railings(mats, col):
    bm = bmesh.new()
    base_angle = -math.pi / 2.0 - math.pi / 8.0

    for k in range(1, 8):
        ang1 = base_angle + k * (math.pi / 4.0)
        ang2 = base_angle + ((k + 1) % 8) * (math.pi / 4.0)

        p1 = Vector((COL_RADIUS * math.cos(ang1), COL_RADIUS * math.sin(ang1), 0.0))
        p2 = Vector((COL_RADIUS * math.cos(ang2), COL_RADIUS * math.sin(ang2), 0.0))

        span_vec = p2 - p1
        span_dist = span_vec.length
        span_dir = span_vec.normalized()
        span_mid = (p1 + p2) / 2.0

        clear_span = span_dist - COLUMN_SIZE
        rot_angle = math.atan2(span_dir.y, span_dir.x)
        rot_mat = Matrix.Rotation(rot_angle, 4, 'Z')

        # 1. Solera inferior (Z = 1.28 m)
        r_bot = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((clear_span, 0.03, 0.015)), verts=r_bot['verts'])
        bmesh.ops.transform(bm, matrix=rot_mat, verts=r_bot['verts'])
        bmesh.ops.translate(bm, vec=span_mid + Vector((0, 0, 1.28)), verts=r_bot['verts'])

        # 2. Sub-solera (Z = 1.98 m)
        r_sub = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((clear_span, 0.03, 0.015)), verts=r_sub['verts'])
        bmesh.ops.transform(bm, matrix=rot_mat, verts=r_sub['verts'])
        bmesh.ops.translate(bm, vec=span_mid + Vector((0, 0, 1.98)), verts=r_sub['verts'])

        # 3. Pasamanos superior (Z = 2.10 m)
        r_top = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((clear_span, 0.05, 0.025)), verts=r_top['verts'])
        bmesh.ops.transform(bm, matrix=rot_mat, verts=r_top['verts'])
        bmesh.ops.translate(bm, vec=span_mid + Vector((0, 0, 2.10)), verts=r_top['verts'])

        # 4. Cenefa de Aros decorativos (Z = 1.98 a 2.10 m)
        num_rings = int(clear_span / 0.11)
        ring_step = clear_span / max(num_rings, 1)
        for ri in range(num_rings):
            t = (ri + 0.5) * ring_step - clear_span / 2.0
            ring_pos = span_mid + span_dir * t + Vector((0, 0, 2.04))
            ring_mat = Matrix.Translation(ring_pos) @ rot_mat
            create_annular_ring(bm, r_in=0.032, r_out=0.046, thick=0.012, segments=12, matrix=ring_mat)

        # 5. Balaustres verticales (cada 0.11 m)
        num_balusters = int(clear_span / 0.11)
        bal_step = clear_span / max(num_balusters, 1)
        bal_h = 1.98 - 1.28
        for bi in range(num_balusters):
            t = (bi + 0.5) * bal_step - clear_span / 2.0
            bal_pos = span_mid + span_dir * t + Vector((0, 0, 1.28 + bal_h / 2.0))
            bal_res = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=Vector((0.018, 0.018, bal_h)), verts=bal_res['verts'])
            bmesh.ops.transform(bm, matrix=rot_mat, verts=bal_res['verts'])
            bmesh.ops.translate(bm, vec=bal_pos, verts=bal_res['verts'])

    for f in bm.faces:
        f.material_index = 0
        f.smooth = False

    mesh = bpy.data.meshes.new("Mesh_Herreria_Perimetral")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Herreria_Perimetral", mesh)
    obj.data.materials.append(mats["M_Herreria_Negra"])
    col.objects.link(obj)
    return obj


def build_openwork_arches(mats, col):
    """
    Construye los 8 Arcos Calados de Herrería Superiores (Z = 3.50 a 3.90 m):
    - Arcos escarzanos con barrotes colgantes de crestería.
    - Volutas / espirales de forja en las esquinas de unión con los capiteles.
    """
    bm = bmesh.new()
    base_angle = -math.pi / 2.0 - math.pi / 8.0

    for k in range(8):
        ang1 = base_angle + k * (math.pi / 4.0)
        ang2 = base_angle + ((k + 1) % 8) * (math.pi / 4.0)

        p1 = Vector((COL_RADIUS * math.cos(ang1), COL_RADIUS * math.sin(ang1), 0.0))
        p2 = Vector((COL_RADIUS * math.cos(ang2), COL_RADIUS * math.sin(ang2), 0.0))

        span_vec = p2 - p1
        span_dist = span_vec.length
        span_dir = span_vec.normalized()
        span_mid = (p1 + p2) / 2.0

        clear_span = span_dist - COLUMN_SIZE
        rot_angle = math.atan2(span_dir.y, span_dir.x)
        rot_mat = Matrix.Rotation(rot_angle, 4, 'Z')

        # 1. Solera superior (Z = 3.88 m)
        top_bar = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((clear_span, 0.03, 0.02)), verts=top_bar['verts'])
        bmesh.ops.transform(bm, matrix=rot_mat, verts=top_bar['verts'])
        bmesh.ops.translate(bm, vec=span_mid + Vector((0, 0, 3.88)), verts=top_bar['verts'])

        # 2. Arco escarzano curvo
        arc_segments = 16
        z_spring = 3.82
        z_crown = 3.50
        half_s = clear_span / 2.0

        prev_pt = None
        for s in range(arc_segments + 1):
            u = s / float(arc_segments)
            t = -half_s + u * clear_span
            z_curve = z_crown + (z_spring - z_crown) * ((t / half_s) ** 2)
            curr_pt = span_mid + span_dir * t + Vector((0, 0, z_curve))

            if prev_pt is not None:
                seg_vec = curr_pt - prev_pt
                seg_len = seg_vec.length
                seg_mid = (prev_pt + curr_pt) / 2.0
                seg_rot = Vector((0, 0, 1)).rotation_difference(seg_vec)

                arch_res = bmesh.ops.create_cube(bm, size=1.0)
                bmesh.ops.scale(bm, vec=Vector((0.02, 0.025, seg_len)), verts=arch_res['verts'])
                bmesh.ops.rotate(bm, cent=Vector((0, 0, 0)), matrix=seg_rot.to_matrix(), verts=arch_res['verts'])
                bmesh.ops.translate(bm, vec=seg_mid, verts=arch_res['verts'])

            prev_pt = curr_pt

            # Barrotes verticales de crestería
            if s > 0 and s < arc_segments and s % 2 == 0:
                bar_bot = z_curve
                bar_top = 3.88
                bar_len = bar_top - bar_bot
                if bar_len > 0.03:
                    bar_res = bmesh.ops.create_cube(bm, size=1.0)
                    bmesh.ops.scale(bm, vec=Vector((0.016, 0.016, bar_len)), verts=bar_res['verts'])
                    bmesh.ops.transform(bm, matrix=rot_mat, verts=bar_res['verts'])
                    bmesh.ops.translate(bm, vec=span_mid + span_dir * t + Vector((0, 0, (bar_bot + bar_top) / 2.0)), verts=bar_res['verts'])

        # 3. Volutas decorativas en las enjutas/esquinas superiores
        for side_s in [-1.0, 1.0]:
            scroll_pos = span_mid + span_dir * (side_s * (half_s - 0.12)) + Vector((0, 0, 3.75))
            sc_mat = Matrix.Translation(scroll_pos) @ rot_mat
            create_annular_ring(bm, r_in=0.035, r_out=0.050, thick=0.012, segments=12, matrix=sc_mat)

    for f in bm.faces:
        f.material_index = 0
        f.smooth = False

    mesh = bpy.data.meshes.new("Mesh_Arcos_Calados")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Arcos_Calados_Herreria", mesh)
    obj.data.materials.append(mats["M_Herreria_Negra"])
    col.objects.link(obj)
    return obj


def build_entablature_ring(mats, col):
    """
    Construye el Anillo de Entablamento Continuo (Z = 3.90 a 4.35 m):
    - Cilindro continuo liso blanco (Ø ext 7.40 m, Ø int 6.30 m).
    - Moldura perimetral superior saliente.
    - Plafón interior horizontal.
    """
    bm = bmesh.new()
    segments = 64

    z_bot = RING_Z_BOTTOM
    z_mid = z_bot + RING_HEIGHT - 0.06
    z_top = z_bot + RING_HEIGHT

    v_ext_bot = []
    v_ext_mid = []
    v_ext_lip = []
    v_ext_top = []
    v_int_bot = []
    v_int_top = []

    for i in range(segments):
        ang = (2.0 * math.pi * i) / segments
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)

        v_ext_bot.append(bm.verts.new(Vector((RING_R_OUT * cos_a, RING_R_OUT * sin_a, z_bot))))
        v_ext_mid.append(bm.verts.new(Vector((RING_R_OUT * cos_a, RING_R_OUT * sin_a, z_mid))))
        v_ext_lip.append(bm.verts.new(Vector(((RING_R_OUT + 0.05) * cos_a, (RING_R_OUT + 0.05) * sin_a, z_mid + 0.03))))
        v_ext_top.append(bm.verts.new(Vector(((RING_R_OUT + 0.04) * cos_a, (RING_R_OUT + 0.04) * sin_a, z_top))))

        v_int_bot.append(bm.verts.new(Vector((RING_R_IN * cos_a, RING_R_IN * sin_a, z_bot))))
        v_int_top.append(bm.verts.new(Vector((RING_R_IN * cos_a, RING_R_IN * sin_a, z_top))))

    for i in range(segments):
        nxt = (i + 1) % segments

        f1 = bm.faces.new([v_ext_bot[i], v_ext_bot[nxt], v_ext_mid[nxt], v_ext_mid[i]])
        f2 = bm.faces.new([v_ext_mid[i], v_ext_mid[nxt], v_ext_lip[nxt], v_ext_lip[i]])
        f3 = bm.faces.new([v_ext_lip[i], v_ext_lip[nxt], v_ext_top[nxt], v_ext_top[i]])
        f_in = bm.faces.new([v_int_top[i], v_int_top[nxt], v_int_bot[nxt], v_int_bot[i]])
        f_bot = bm.faces.new([v_ext_bot[i], v_int_bot[i], v_int_bot[nxt], v_ext_bot[nxt]])
        f_top = bm.faces.new([v_ext_top[i], v_ext_top[nxt], v_int_top[nxt], v_int_top[i]])

        for f in [f1, f2, f3, f_in, f_bot, f_top]:
            f.material_index = 0
            f.smooth = True

    # Plafón interior enlucido blanco
    f_ceiling = bm.faces.new(v_int_top)
    f_ceiling.material_index = 0
    f_ceiling.smooth = True

    mesh = bpy.data.meshes.new("Mesh_Anillo_Entablamento")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Anillo_Entablamento", mesh)
    obj.data.materials.append(mats["M_Estuco_Blanco"])
    col.objects.link(obj)
    return obj


def build_conical_roof(mats, col):
    """
    Construye la Cubierta Cónica Tradicional con Hileras de Teja Española (Z = 4.35 a 5.55 m):
    - Hileras concéntricas escalonadas de teja curva (canal y cobija).
    - Alero perimetral festoneado sobresaliente.
    - 8 limatesas / caballetes radiales en los ejes octagonales.
    - Cúspide cónica con remate cerámico a Z = 5.55 m.
    """
    bm = bmesh.new()
    segments = 64
    z_eave = ROOF_Z_EAVE
    z_peak = ROOF_Z_PEAK

    # 1. Anillos concéntricos de tejas escalonadas (6 hiladas concéntricas)
    num_rings = 6
    prev_ring_verts = []

    # Borde de alero con festoneado ondulado (48 ondas radiales de tejas)
    v_under = []
    for i in range(segments):
        ang = (2.0 * math.pi * i) / segments
        wave = math.sin(ang * 48.0)
        r_wave = ROOF_R_BASE + 0.03 * wave
        z_wave = z_eave + 0.015 * wave
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)

        prev_ring_verts.append(bm.verts.new(Vector((r_wave * cos_a, r_wave * sin_a, z_wave))))
        v_under.append(bm.verts.new(Vector(((r_wave - 0.08) * cos_a, (r_wave - 0.08) * sin_a, z_wave - 0.04))))

    # Canto inferior del alero
    for i in range(segments):
        nxt = (i + 1) % segments
        f_edge = bm.faces.new([v_under[i], v_under[nxt], prev_ring_verts[nxt], prev_ring_verts[i]])
        f_edge.material_index = 0
        f_edge.smooth = True

    # Generación de las bandas de teja
    for ring_idx in range(1, num_rings + 1):
        frac = ring_idx / float(num_rings)
        r_current = ROOF_R_BASE * (1.0 - frac) + 0.20 * frac
        z_current = z_eave + (z_peak - z_eave - 0.15) * (frac ** 0.95)

        curr_ring_verts = []
        for i in range(segments):
            ang = (2.0 * math.pi * i) / segments
            wave = math.sin(ang * 48.0) * (1.0 - frac * 0.7)
            r_w = r_current + 0.02 * wave
            z_w = z_current + 0.012 * wave
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            curr_ring_verts.append(bm.verts.new(Vector((r_w * cos_a, r_w * sin_a, z_w))))

        # Conectar quads entre el anillo anterior y el actual
        for i in range(segments):
            nxt = (i + 1) % segments
            f_tier = bm.faces.new([prev_ring_verts[i], prev_ring_verts[nxt], curr_ring_verts[nxt], curr_ring_verts[i]])
            f_tier.material_index = 0
            f_tier.smooth = True

        prev_ring_verts = curr_ring_verts

    # Cúspide final del cono
    v_peak = bm.verts.new(Vector((0.0, 0.0, z_peak - 0.08)))
    for i in range(segments):
        nxt = (i + 1) % segments
        f_top = bm.faces.new([prev_ring_verts[i], prev_ring_verts[nxt], v_peak])
        f_top.material_index = 0
        f_top.smooth = True

    # 2. Limatesas / Caballetes radiales en los 8 vértices del octágono
    base_angle = -math.pi / 2.0 - math.pi / 8.0
    for k in range(8):
        ang = base_angle + k * (math.pi / 4.0)
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)

        p_base = Vector((ROOF_R_BASE * cos_a, ROOF_R_BASE * sin_a, z_eave))
        p_top = Vector((0.18 * cos_a, 0.18 * sin_a, z_peak - 0.08))
        dir_vec = p_top - p_base
        rib_len = dir_vec.length
        rot_quat = Vector((0, 0, 1)).rotation_difference(dir_vec)

        rib_res = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((0.08, 0.05, rib_len)), verts=rib_res['verts'])
        bmesh.ops.rotate(bm, cent=Vector((0, 0, 0)), matrix=rot_quat.to_matrix(), verts=rib_res['verts'])
        bmesh.ops.translate(bm, vec=(p_base + p_top) / 2.0 + Vector((0, 0, 0.025)), verts=rib_res['verts'])
        for v in rib_res['verts']:
            for f in v.link_faces:
                f.material_index = 0
                f.smooth = True

    # 3. Remate cerámico de cúspide (Z = 5.45 a 5.55 m)
    finial_base = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.25, radius2=0.08, depth=0.14)
    bmesh.ops.translate(bm, vec=Vector((0.0, 0.0, z_peak - 0.04)), verts=finial_base['verts'])
    for v in finial_base['verts']:
        for f in v.link_faces:
            f.material_index = 0
            f.smooth = True

    finial_tip = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.08, radius2=0.01, depth=0.10)
    bmesh.ops.translate(bm, vec=Vector((0.0, 0.0, z_peak + 0.05)), verts=finial_tip['verts'])
    for v in finial_tip['verts']:
        for f in v.link_faces:
            f.material_index = 0
            f.smooth = True

    mesh = bpy.data.meshes.new("Mesh_Cubierta_Conica")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Cubierta_Conica", mesh)
    obj.data.materials.append(mats["M_Teja_Terracota"])
    col.objects.link(obj)
    return obj


def setup_lighting_and_cameras():
    # Suelo receptor de sombras para realismo visual en renders
    ground_mesh = bpy.data.meshes.new("Mesh_Suelo_Plaza")
    bm_g = bmesh.new()
    bmesh.ops.create_circle(bm_g, cap_ends=True, radius=14.0, segments=48)
    bm_g.to_mesh(ground_mesh)
    bm_g.free()
    ground_obj = bpy.data.objects.new("Suelo_Plaza_Render", ground_mesh)
    ground_obj.is_shadow_catcher = True
    bpy.context.scene.collection.objects.link(ground_obj)

    # 1. Luz Solar Principal (Key Light)
    sun_key_d = bpy.data.lights.new('Luz_Key_Sun', type='SUN')
    sun_key_d.energy = 5.5
    sun_key_d.color = (1.0, 0.96, 0.90)
    sun_key = bpy.data.objects.new('Luz_Key_Sun', sun_key_d)
    bpy.context.scene.collection.objects.link(sun_key)
    sun_key.rotation_euler = (math.radians(48.0), math.radians(22.0), math.radians(-32.0))

    # 2. Luz de Relleno (Fill Light)
    sun_fill_d = bpy.data.lights.new('Luz_Fill_Sun', type='SUN')
    sun_fill_d.energy = 2.8
    sun_fill_d.color = (0.78, 0.88, 1.0)
    sun_fill = bpy.data.objects.new('Luz_Fill_Sun', sun_fill_d)
    bpy.context.scene.collection.objects.link(sun_fill)
    sun_fill.rotation_euler = (math.radians(62.0), math.radians(-28.0), math.radians(145.0))

    # 3. Luz Trasera de Contorno (Rim Light)
    sun_rim_d = bpy.data.lights.new('Luz_Rim_Sun', type='SUN')
    sun_rim_d.energy = 3.2
    sun_rim_d.color = (1.0, 0.95, 0.85)
    sun_rim = bpy.data.objects.new('Luz_Rim_Sun', sun_rim_d)
    bpy.context.scene.collection.objects.link(sun_rim)
    sun_rim.rotation_euler = (math.radians(25.0), math.radians(-45.0), math.radians(-160.0))

    # Entorno
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new('World')
        bpy.context.scene.world = world
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (0.82, 0.88, 0.94, 1.0)
        bg.inputs['Strength'].default_value = 1.0

    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.device = 'CPU'
    bpy.context.scene.cycles.samples = 32
    bpy.context.scene.render.film_transparent = True


def render_views():
    # 1. Vista General
    cam1_d = bpy.data.cameras.new("Cam_General")
    cam1_d.lens = 38
    cam1 = bpy.data.objects.new("Cam_General", cam1_d)
    bpy.context.scene.collection.objects.link(cam1)
    bpy.context.scene.camera = cam1

    cam1.location = (8.2, -10.5, 4.8)
    cam1.rotation_euler = (math.radians(74.0), 0.0, math.radians(38.0))

    bpy.context.scene.render.resolution_x = 1600
    bpy.context.scene.render.resolution_y = 1200
    p1 = "docs/images/kiosko_preview.png"
    bpy.context.scene.render.filepath = f"//{p1}"
    bpy.ops.render.render(write_still=True)
    print(f"--> Render 1 guardado: {p1}")

    # 2. Detalle de Escalinata de Acceso y Puerta de Servicio
    cam2_d = bpy.data.cameras.new("Cam_Acceso")
    cam2_d.lens = 45
    cam2 = bpy.data.objects.new("Cam_Acceso", cam2_d)
    bpy.context.scene.collection.objects.link(cam2)
    bpy.context.scene.camera = cam2

    cam2.location = (2.2, -7.5, 1.6)
    cam2.rotation_euler = (math.radians(82.0), 0.0, math.radians(16.0))

    bpy.context.scene.render.resolution_x = 1400
    bpy.context.scene.render.resolution_y = 1050
    p2 = "docs/images/kiosko_acceso.png"
    bpy.context.scene.render.filepath = f"//{p2}"
    bpy.ops.render.render(write_still=True)
    print(f"--> Render 2 guardado: {p2}")

    # 3. Detalle de Columnas, Plintos, Faroles y Arcos Calados
    cam3_d = bpy.data.cameras.new("Cam_Columnas_Arcos")
    cam3_d.lens = 65
    cam3 = bpy.data.objects.new("Cam_Columnas_Arcos", cam3_d)
    bpy.context.scene.collection.objects.link(cam3)
    bpy.context.scene.camera = cam3

    cam3.location = (-1.8, -5.8, 3.1)
    cam3.rotation_euler = (math.radians(88.0), 0.0, math.radians(-17.0))

    bpy.context.scene.render.resolution_x = 1400
    bpy.context.scene.render.resolution_y = 1050
    p3 = "docs/images/kiosko_columnas_arcos.png"
    bpy.context.scene.render.filepath = f"//{p3}"
    bpy.ops.render.render(write_still=True)
    print(f"--> Render 3 guardado: {p3}")

    # 4. Detalle de Entablamento Circular y Techo de Teja
    cam4_d = bpy.data.cameras.new("Cam_Techo")
    cam4_d.lens = 50
    cam4 = bpy.data.objects.new("Cam_Techo", cam4_d)
    bpy.context.scene.collection.objects.link(cam4)
    bpy.context.scene.camera = cam4

    cam4.location = (5.5, -6.5, 5.8)
    cam4.rotation_euler = (math.radians(66.0), 0.0, math.radians(40.0))

    bpy.context.scene.render.resolution_x = 1400
    bpy.context.scene.render.resolution_y = 1050
    p4 = "docs/images/kiosko_techo.png"
    bpy.context.scene.render.filepath = f"//{p4}"
    bpy.ops.render.render(write_still=True)
    print(f"--> Render 4 guardado: {p4}")


def main():
    print("================================================================")
    print(" GENERADOR PARAMÉTRICO: KIOSCO PARQUE HIDALGO (TECATE, B.C.)    ")
    print("================================================================")
    clean_scene()

    main_col = bpy.data.collections.new("Kiosco_Parque_Hidalgo")
    bpy.context.scene.collection.children.link(main_col)

    mats = create_materials()

    obj_base = build_octagonal_base(mats, main_col)
    obj_escalinata = build_staircase(mats, main_col)
    obj_columnas = build_columns(mats, main_col)
    obj_barandales = build_perimeter_railings(mats, main_col)
    obj_arcos = build_openwork_arches(mats, main_col)
    obj_anillo = build_entablature_ring(mats, main_col)
    obj_cubierta = build_conical_roof(mats, main_col)

    root_empty = bpy.data.objects.new("Kiosco_Root", None)
    root_empty.empty_display_type = 'PLAIN_AXES'
    main_col.objects.link(root_empty)

    all_components = [
        obj_base,
        obj_escalinata,
        obj_columnas,
        obj_barandales,
        obj_arcos,
        obj_anillo,
        obj_cubierta
    ]

    for comp in all_components:
        comp.parent = root_empty

    setup_lighting_and_cameras()
    bpy.context.view_layer.update()

    min_z = min([min([(obj.matrix_world @ Vector(corner)).z for corner in obj.bound_box]) for obj in all_components])
    max_z = max([max([(obj.matrix_world @ Vector(corner)).z for corner in obj.bound_box]) for obj in all_components])
    max_x = max([max([(obj.matrix_world @ Vector(corner)).x for corner in obj.bound_box]) for obj in all_components])
    min_x = min([min([(obj.matrix_world @ Vector(corner)).x for corner in obj.bound_box]) for obj in all_components])
    max_y = max([max([(obj.matrix_world @ Vector(corner)).y for corner in obj.bound_box]) for obj in all_components])
    min_y = min([min([(obj.matrix_world @ Vector(corner)).y for corner in obj.bound_box]) for obj in all_components])

    total_h = max_z - min_z
    diam_x = max_x - min_x
    print(f"--> Altura Total Calculada: {total_h:.3f} m (Min Z: {min_z:.3f} m, Max Z: {max_z:.3f} m)")
    print(f"--> Envergadura X (Diámetro Tejado): {diam_x:.3f} m")
    print(f"--> Envergadura Y (con Escalinata): {(max_y - min_y):.3f} m")

    blend_path = "blender_assets/kiosko_parque_hidalgo.blend"
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"--> Archivo maestro Blender guardado: {blend_path}")

    # Exportación GLB limpia para Godot (excluyendo el shadow catcher del render)
    bpy.ops.object.select_all(action='DESELECT')
    root_empty.select_set(True)
    for comp in all_components:
        comp.select_set(True)
    bpy.context.view_layer.objects.active = root_empty

    glb_path = "godot_project/assets/kiosko_parque_hidalgo.glb"
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        use_selection=True,
        export_apply=False,
        export_materials='EXPORT',
        export_yup=True
    )
    print(f"--> Modelo optimizado para Godot exportado: {glb_path}")

    render_views()

    print("================================================================")
    print(" GENERACIÓN DEL KIOSCO FINALIZADA EXITOSAMENTE                 ")
    print("================================================================")

if __name__ == '__main__':
    main()
