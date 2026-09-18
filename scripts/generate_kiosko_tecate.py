"""
=============================================================================
Generador 3D Paramétrico: Kiosco Octagonal Tradicional de Tecate, B.C.
(Parque Miguel Hidalgo) - Versión v3.0 (Fidelidad Morfológica Total)
=============================================================================
Correcciones v3.0:
1. Barandilla de escalinata que pisa firmemente el octágono con tramos laterales
   cortos desde las columnas frontales para cerrar el perímetro.
2. Tejas coloniales curvas 3D volumétricas apiladas (canal y cobija con solape real).
3. Arcos superiores de herrería calada con vano ascendente |_^_|.
4. Escalinata con laterales escalonados de roca (saw-tooth) sin muros ciegos al suelo.
5. Columnas con ladrillo grueso y envejecido artesanal del siglo XIX con mapas PBR.
=============================================================================
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix

# =============================================================================
# CONSTANTES Y COTAS ARQUITECTÓNICAS (v3.0)
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
COLUMN_HEIGHT = 2.46      # Altura fuste (Z = 1.40 a 3.86 m)
CAPITAL_SIZE = 0.58       # Lado capitel ensanchado (m)
CAPITAL_HEIGHT = 0.18     # Altura capitel (Z = 3.74 a 3.92 m)

# Anillo de corona cilíndrico continuo
RING_R_OUT = 3.75         # Radio exterior tambor cilíndrico (Ø 7.50 m)
RING_R_CORNICE = 3.85     # Radio volado cornisa superior anillo (Ø 7.70 m)
RING_R_IN = 3.10          # Radio interior anillo (Ø 6.20 m)
RING_Z_BOTTOM = 3.85      # Arranque anillo entablamento (m)
RING_Z_TOP = 4.40         # Cota superior del anillo (m, H = 0.55 m)

# Cubierta cónica circular con tejas 3D volumétricas
ROOF_R_BASE = 3.92        # Radio base cono cubierta (Ø 7.84 m)
ROOF_Z_EAVE = 4.38        # Cota del alero volado (m)
ROOF_Z_PEAK = 5.50        # Cota de la cúspide máxima (m)


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
    """Configura materiales PBR calibrados con texturas generadas."""
    mats = {}
    tex_dir = os.path.abspath("godot_project/assets/textures")

    # 1. M_Piedra_Base con mapas PBR
    m_piedra = bpy.data.materials.new(name="M_Piedra_Base")
    nodes_p = m_piedra.node_tree.nodes
    links_p = m_piedra.node_tree.links
    bsdf_p = nodes_p.get("Principled BSDF")

    p_alb = os.path.join(tex_dir, "kiosko_laja_albedo.png")
    p_nrm = os.path.join(tex_dir, "kiosko_laja_normal.png")
    p_rgh = os.path.join(tex_dir, "kiosko_laja_roughness.png")

    if os.path.exists(p_alb):
        img_alb = bpy.data.images.load(p_alb)
        node_alb = nodes_p.new("ShaderNodeTexImage")
        node_alb.image = img_alb
        links_p.new(node_alb.outputs["Color"], bsdf_p.inputs["Base Color"])
    else:
        bsdf_p.inputs["Base Color"].default_value = (0.64, 0.52, 0.36, 1.0)

    if os.path.exists(p_rgh):
        img_rgh = bpy.data.images.load(p_rgh)
        img_rgh.colorspace_settings.name = "Non-Color"
        node_rgh = nodes_p.new("ShaderNodeTexImage")
        node_rgh.image = img_rgh
        links_p.new(node_rgh.outputs["Color"], bsdf_p.inputs["Roughness"])
    else:
        bsdf_p.inputs["Roughness"].default_value = 0.88

    if os.path.exists(p_nrm):
        img_nrm = bpy.data.images.load(p_nrm)
        img_nrm.colorspace_settings.name = "Non-Color"
        node_nrm_tex = nodes_p.new("ShaderNodeTexImage")
        node_nrm_tex.image = img_nrm
        node_norm_map = nodes_p.new("ShaderNodeNormalMap")
        node_norm_map.inputs["Strength"].default_value = 1.4
        links_p.new(node_nrm_tex.outputs["Color"], node_norm_map.inputs["Color"])
        links_p.new(node_norm_map.outputs["Normal"], bsdf_p.inputs["Normal"])

    bsdf_p.inputs["Metallic"].default_value = 0.0
    mats["M_Piedra_Base"] = m_piedra

    # 2. M_Ladrillo_Pilar: Ladrillo artesanal siglo XIX con mapas PBR
    m_ladrillo = bpy.data.materials.new(name="M_Ladrillo_Pilar")
    nodes_l = m_ladrillo.node_tree.nodes
    links_l = m_ladrillo.node_tree.links
    bsdf_l = nodes_l.get("Principled BSDF")

    lad_alb = os.path.join(tex_dir, "kiosko_ladrillo_albedo.png")
    lad_nrm = os.path.join(tex_dir, "kiosko_ladrillo_normal.png")
    lad_rgh = os.path.join(tex_dir, "kiosko_ladrillo_roughness.png")

    if os.path.exists(lad_alb):
        img_lad_alb = bpy.data.images.load(lad_alb)
        node_lad_alb = nodes_l.new("ShaderNodeTexImage")
        node_lad_alb.image = img_lad_alb
        links_l.new(node_lad_alb.outputs["Color"], bsdf_l.inputs["Base Color"])
    else:
        bsdf_l.inputs["Base Color"].default_value = (0.35, 0.20, 0.13, 1.0)

    if os.path.exists(lad_rgh):
        img_lad_rgh = bpy.data.images.load(lad_rgh)
        img_lad_rgh.colorspace_settings.name = "Non-Color"
        node_lad_rgh = nodes_l.new("ShaderNodeTexImage")
        node_lad_rgh.image = img_lad_rgh
        links_l.new(node_lad_rgh.outputs["Color"], bsdf_l.inputs["Roughness"])
    else:
        bsdf_l.inputs["Roughness"].default_value = 0.85

    if os.path.exists(lad_nrm):
        img_lad_nrm = bpy.data.images.load(lad_nrm)
        img_lad_nrm.colorspace_settings.name = "Non-Color"
        node_lad_nrm = nodes_l.new("ShaderNodeTexImage")
        node_lad_nrm.image = img_lad_nrm
        node_lad_map = nodes_l.new("ShaderNodeNormalMap")
        node_lad_map.inputs["Strength"].default_value = 1.6
        links_l.new(node_lad_nrm.outputs["Color"], node_lad_map.inputs["Color"])
        links_l.new(node_lad_map.outputs["Normal"], bsdf_l.inputs["Normal"])

    bsdf_l.inputs["Metallic"].default_value = 0.0
    mats["M_Ladrillo_Pilar"] = m_ladrillo

    # 3. M_Mortero_Gris: Cemento/cal rústico
    m_mortero = bpy.data.materials.new(name="M_Mortero_Gris")
    bsdf_m = m_mortero.node_tree.nodes.get("Principled BSDF")
    if bsdf_m:
        bsdf_m.inputs["Base Color"].default_value = (0.22, 0.18, 0.15, 1.0)
        bsdf_m.inputs["Metallic"].default_value = 0.0
        bsdf_m.inputs["Roughness"].default_value = 0.95
    mats["M_Mortero_Gris"] = m_mortero

    # 4. M_Estuco_Blanco: Estuco blanco marfil cálido / yeso colonial
    m_estuco = bpy.data.materials.new(name="M_Estuco_Blanco")
    bsdf_e = m_estuco.node_tree.nodes.get("Principled BSDF")
    if bsdf_e:
        bsdf_e.inputs["Base Color"].default_value = (0.91, 0.90, 0.87, 1.0)
        bsdf_e.inputs["Metallic"].default_value = 0.0
        bsdf_e.inputs["Roughness"].default_value = 0.65
    mats["M_Estuco_Blanco"] = m_estuco

    # 5. M_Herreria_Negra: Hierro forjado martillado anticorrosivo
    m_hierro = bpy.data.materials.new(name="M_Herreria_Negra")
    bsdf_h = m_hierro.node_tree.nodes.get("Principled BSDF")
    if bsdf_h:
        bsdf_h.inputs["Base Color"].default_value = (0.05, 0.05, 0.05, 1.0)
        bsdf_h.inputs["Metallic"].default_value = 0.85
        bsdf_h.inputs["Roughness"].default_value = 0.45
    mats["M_Herreria_Negra"] = m_hierro

    # 6. M_Teja_Terracota con mapas PBR
    m_teja = bpy.data.materials.new(name="M_Teja_Terracota")
    nodes_t = m_teja.node_tree.nodes
    links_t = m_teja.node_tree.links
    bsdf_t = nodes_t.get("Principled BSDF")

    p_tj_alb = os.path.join(tex_dir, "kiosko_teja_albedo.png")
    p_tj_nrm = os.path.join(tex_dir, "kiosko_teja_normal.png")
    p_tj_rgh = os.path.join(tex_dir, "kiosko_teja_roughness.png")

    if os.path.exists(p_tj_alb):
        img_tj_alb = bpy.data.images.load(p_tj_alb)
        node_talb = nodes_t.new("ShaderNodeTexImage")
        node_talb.image = img_tj_alb
        links_t.new(node_talb.outputs["Color"], bsdf_t.inputs["Base Color"])
    else:
        bsdf_t.inputs["Base Color"].default_value = (0.55, 0.20, 0.12, 1.0)

    if os.path.exists(p_tj_rgh):
        img_tj_rgh = bpy.data.images.load(p_tj_rgh)
        img_tj_rgh.colorspace_settings.name = "Non-Color"
        node_trgh = nodes_t.new("ShaderNodeTexImage")
        node_trgh.image = img_tj_rgh
        links_t.new(node_trgh.outputs["Color"], bsdf_t.inputs["Roughness"])
    else:
        bsdf_t.inputs["Roughness"].default_value = 0.78

    if os.path.exists(p_tj_nrm):
        img_tj_nrm = bpy.data.images.load(p_tj_nrm)
        img_tj_nrm.colorspace_settings.name = "Non-Color"
        node_tnrm_tex = nodes_t.new("ShaderNodeTexImage")
        node_tnrm_tex.image = img_tj_nrm
        node_tnorm_map = nodes_t.new("ShaderNodeNormalMap")
        node_tnorm_map.inputs["Strength"].default_value = 1.3
        links_t.new(node_tnrm_tex.outputs["Color"], node_tnorm_map.inputs["Color"])
        links_t.new(node_tnorm_map.outputs["Normal"], bsdf_t.inputs["Normal"])

    bsdf_t.inputs["Metallic"].default_value = 0.0
    mats["M_Teja_Terracota"] = m_teja

    # 7. M_Piso_Cantera con texturas
    m_piso = bpy.data.materials.new(name="M_Piso_Cantera")
    nodes_pi = m_piso.node_tree.nodes
    links_pi = m_piso.node_tree.links
    bsdf_pi = nodes_pi.get("Principled BSDF")

    p_can_alb = os.path.join(tex_dir, "kiosko_cantera_albedo.png")
    p_can_nrm = os.path.join(tex_dir, "kiosko_cantera_normal.png")

    if os.path.exists(p_can_alb):
        img_can_alb = bpy.data.images.load(p_can_alb)
        node_calb = nodes_pi.new("ShaderNodeTexImage")
        node_calb.image = img_can_alb
        links_pi.new(node_calb.outputs["Color"], bsdf_pi.inputs["Base Color"])
    else:
        bsdf_pi.inputs["Base Color"].default_value = (0.76, 0.74, 0.69, 1.0)

    if os.path.exists(p_can_nrm):
        img_can_nrm = bpy.data.images.load(p_can_nrm)
        img_can_nrm.colorspace_settings.name = "Non-Color"
        node_cnrm_tex = nodes_pi.new("ShaderNodeTexImage")
        node_cnrm_tex.image = img_can_nrm
        node_cnorm_map = nodes_pi.new("ShaderNodeNormalMap")
        node_cnorm_map.inputs["Strength"].default_value = 0.8
        links_pi.new(node_cnrm_tex.outputs["Color"], node_cnorm_map.inputs["Color"])
        links_pi.new(node_cnorm_map.outputs["Normal"], bsdf_pi.inputs["Normal"])

    bsdf_pi.inputs["Metallic"].default_value = 0.0
    bsdf_pi.inputs["Roughness"].default_value = 0.60
    mats["M_Piso_Cantera"] = m_piso

    # 8. M_Vidrio_Farol
    m_vidrio = bpy.data.materials.new(name="M_Vidrio_Farol")
    bsdf_v = m_vidrio.node_tree.nodes.get("Principled BSDF")
    if bsdf_v:
        bsdf_v.inputs["Base Color"].default_value = (0.96, 0.92, 0.82, 1.0)
        bsdf_v.inputs["Metallic"].default_value = 0.05
        bsdf_v.inputs["Roughness"].default_value = 0.25
        if "Emission Color" in bsdf_v.inputs:
            bsdf_v.inputs["Emission Color"].default_value = (0.96, 0.86, 0.62, 1.0)
            bsdf_v.inputs["Emission Strength"].default_value = 1.0
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
    v_front_in, v_front_out, v_back_in, v_back_out = [], [], [], []
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
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.verify()

    # 1. Zócalo / Desplante inferior de cimentación (Z = 0.0 a 0.08 m)
    r_foot = OCT_CIRCUM + 0.04
    v_foot_bot = [bm.verts.new(v) for v in get_octagon_vertices(r_foot, 0.0)]
    v_foot_top = [bm.verts.new(v) for v in get_octagon_vertices(r_foot, 0.08)]
    bm.faces.new(list(reversed(v_foot_bot))).material_index = 0

    for k in range(8):
        kn = (k + 1) % 8
        f = bm.faces.new([v_foot_bot[k], v_foot_bot[kn], v_foot_top[kn], v_foot_top[k]])
        f.material_index = 0

    # 2. Muro octagonal principal (Z = 0.08 a 1.20 m)
    v_wall_bot = [bm.verts.new(v) for v in get_octagon_vertices(OCT_CIRCUM, 0.08)]
    v_wall_top = [bm.verts.new(v) for v in get_octagon_vertices(OCT_CIRCUM, BASE_HEIGHT)]

    for k in range(8):
        kn = (k + 1) % 8
        f = bm.faces.new([v_wall_bot[k], v_wall_bot[kn], v_wall_top[kn], v_wall_top[k]])
        f.material_index = 0
        v_diff = (v_wall_bot[kn].co - v_wall_bot[k].co)
        wall_len = v_diff.length
        f.loops[0][uv_layer].uv = Vector((0.0, 0.0))
        f.loops[1][uv_layer].uv = Vector((wall_len * 0.8, 0.0))
        f.loops[2][uv_layer].uv = Vector((wall_len * 0.8, (BASE_HEIGHT - 0.08) * 0.8))
        f.loops[3][uv_layer].uv = Vector((0.0, (BASE_HEIGHT - 0.08) * 0.8))

    # 3. Plataforma superior de piso en cantera (Z = 1.20 m)
    f_top = bm.faces.new(v_wall_top)
    f_top.material_index = 2
    for loop in f_top.loops:
        loop[uv_layer].uv = Vector((loop.vert.co.x * 0.5, loop.vert.co.y * 0.5))

    # 4. Moldura perimetral en voladizo (Z = 1.10 a 1.22 m)
    r_cornice = OCT_CIRCUM + CORNICE_OUT
    v_corn_bot = [bm.verts.new(v) for v in get_octagon_vertices(OCT_CIRCUM, 1.10)]
    v_corn_out = [bm.verts.new(v) for v in get_octagon_vertices(r_cornice, 1.15)]
    v_corn_top = [bm.verts.new(v) for v in get_octagon_vertices(OCT_CIRCUM, 1.22)]

    for k in range(8):
        kn = (k + 1) % 8
        f1 = bm.faces.new([v_corn_bot[k], v_corn_bot[kn], v_corn_out[kn], v_corn_out[k]])
        f2 = bm.faces.new([v_corn_out[k], v_corn_out[kn], v_corn_top[kn], v_corn_top[k]])
        f1.material_index = 1
        f2.material_index = 1

    # 5. Puerta de registro de servicio en cara lateral (-45°)
    door_w = 0.65
    door_h = 0.85
    face_rot = Matrix.Rotation(math.radians(45), 4, 'Z')
    door_center = face_rot @ Vector((0.0, -OCT_APOTHEM, 0.15 + door_h / 2.0))

    d_res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((door_w + 0.08, 0.04, door_h + 0.08)), verts=d_res['verts'])
    bmesh.ops.transform(bm, matrix=face_rot, verts=d_res['verts'])
    bmesh.ops.translate(bm, vec=door_center, verts=d_res['verts'])
    for v in d_res['verts']:
        for f in v.link_faces:
            f.material_index = 3

    p_res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((door_w, 0.03, door_h)), verts=p_res['verts'])
    bmesh.ops.transform(bm, matrix=face_rot, verts=p_res['verts'])
    bmesh.ops.translate(bm, vec=door_center + face_rot @ Vector((0, -0.015, 0)), verts=p_res['verts'])
    for v in p_res['verts']:
        for f in v.link_faces:
            f.material_index = 3

    h_res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((0.02, 0.04, 0.12)), verts=h_res['verts'])
    bmesh.ops.transform(bm, matrix=face_rot, verts=h_res['verts'])
    bmesh.ops.translate(bm, vec=door_center + face_rot @ Vector((door_w * 0.35, -0.04, 0)), verts=h_res['verts'])
    for v in h_res['verts']:
        for f in v.link_faces:
            f.material_index = 3

    for f in bm.faces:
        f.smooth = False

    mesh = bpy.data.meshes.new("Mesh_Base_Octagonal")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Base_Octagonal", mesh)
    obj.data.materials.append(mats["M_Piedra_Base"])   # 0
    obj.data.materials.append(mats["M_Estuco_Blanco"]) # 1
    obj.data.materials.append(mats["M_Piso_Cantera"])  # 2
    obj.data.materials.append(mats["M_Herreria_Negra"])# 3

    col.objects.link(obj)
    return obj


def build_staircase(mats, col):
    """
    Construye la Escalinata de Acceso Frontal (v3.0):
    - 7 peldaños escalonados en saw-tooth de cantera/roca (sin muro ciego hasta el suelo).
    - Espacio abierto bajo la rampa de escalones como en el kiosco real.
    - Huellas con borde redondeado (+2 cm).
    - Barandilla de escalera con poste superior que PISA FIRMEMENTE la losa del octágono.
    """
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.verify()

    half_w = STAIR_WIDTH / 2.0
    y_wall = -OCT_APOTHEM
    total_run = STAIR_STEPS * STAIR_TREAD
    y_start = y_wall - total_run

    # 1. Peldaños individuales como bloques sólidos de cantera/roca
    for i in range(STAIR_STEPS):
        z_step_bot = i * STAIR_RISER
        z_step_top = (i + 1) * STAIR_RISER
        y_step_front = y_start + i * STAIR_TREAD
        y_step_back = y_step_front + STAIR_TREAD if i < STAIR_STEPS - 1 else y_wall

        # Vértices del bloque del escalón
        # Frontal inferior
        v_f_bl = bm.verts.new(Vector((-half_w, y_step_front, z_step_bot)))
        v_f_br = bm.verts.new(Vector(( half_w, y_step_front, z_step_bot)))
        # Frontal superior
        v_f_tl = bm.verts.new(Vector((-half_w, y_step_front, z_step_top)))
        v_f_tr = bm.verts.new(Vector(( half_w, y_step_front, z_step_top)))
        # Trasero superior
        v_b_tl = bm.verts.new(Vector((-half_w, y_step_back, z_step_top)))
        v_b_tr = bm.verts.new(Vector(( half_w, y_step_back, z_step_top)))
        # Trasero inferior
        v_b_bl = bm.verts.new(Vector((-half_w, y_step_back, z_step_bot)))
        v_b_br = bm.verts.new(Vector(( half_w, y_step_back, z_step_bot)))

        # Huella (Top face) - Cantera
        f_top = bm.faces.new([v_f_tl, v_f_tr, v_b_tr, v_b_tl])
        f_top.material_index = 0
        for loop in f_top.loops:
            loop[uv_layer].uv = Vector((loop.vert.co.x * 0.6, loop.vert.co.y * 0.6))

        # Contrahuella (Front face) - Roca / Piedra
        f_front = bm.faces.new([v_f_bl, v_f_br, v_f_tr, v_f_tl])
        f_front.material_index = 1
        for loop in f_front.loops:
            loop[uv_layer].uv = Vector((loop.vert.co.x * 0.8, loop.vert.co.z * 0.8))

        # Lateral Izquierdo (Left saw-tooth side face) - Roca / Piedra
        f_left = bm.faces.new([v_f_bl, v_f_tl, v_b_tl, v_b_bl])
        f_left.material_index = 1
        for loop in f_left.loops:
            loop[uv_layer].uv = Vector((loop.vert.co.y * 0.8, loop.vert.co.z * 0.8))

        # Lateral Derecho (Right saw-tooth side face) - Roca / Piedra
        f_right = bm.faces.new([v_f_br, v_b_br, v_b_tr, v_f_tr])
        f_right.material_index = 1
        for loop in f_right.loops:
            loop[uv_layer].uv = Vector((loop.vert.co.y * 0.8, loop.vert.co.z * 0.8))

        # Fondo del escalón (Bottom face)
        f_bot = bm.faces.new([v_f_bl, v_b_bl, v_b_br, v_f_br])
        f_bot.material_index = 1

        # Bocel/Nosing saliente en la arista del escalón (+2 cm)
        vn1 = bm.verts.new(Vector((-half_w - 0.02, y_step_front - 0.02, z_step_top)))
        vn2 = bm.verts.new(Vector(( half_w + 0.02, y_step_front - 0.02, z_step_top)))
        vn3 = bm.verts.new(Vector(( half_w + 0.02, y_step_front, z_step_top)))
        vn4 = bm.verts.new(Vector((-half_w - 0.02, y_step_front, z_step_top)))
        fn = bm.faces.new([vn1, vn2, vn3, vn4])
        fn.material_index = 0

    # 2. Barandales laterales inclinados a 0.90 m
    # Extienden hacia adentro de la losa para PISAR EL OCTÁGONO
    rail_h = 0.90
    for side_x in [-half_w, half_w]:
        # Arranque en el primer escalón
        p_start_bot = Vector((side_x, y_start + 0.12, STAIR_RISER))
        p_start_top = p_start_bot + Vector((0, 0, rail_h))

        # Llegada al borde del octágono
        p_landing_bot = Vector((side_x, y_wall, BASE_HEIGHT))
        p_landing_top = p_landing_bot + Vector((0, 0, rail_h))

        # Tramo inclinado de pasamanos
        dir_vec = (p_landing_top - p_start_top)
        length = dir_vec.length
        mid_point = (p_start_top + p_landing_top) / 2.0
        rot_quat = Vector((0, 0, 1)).rotation_difference(dir_vec)

        res = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((0.045, 0.035, length)), verts=res['verts'])
        bmesh.ops.rotate(bm, cent=Vector((0, 0, 0)), matrix=rot_quat.to_matrix(), verts=res['verts'])
        bmesh.ops.translate(bm, vec=mid_point, verts=res['verts'])
        for f in res['verts']:
            for face in f.link_faces:
                face.material_index = 2

        # Tramo horizontal sobre la losa del octágono (0.20 m adentro)
        p_in_bot = Vector((side_x, y_wall + 0.20, BASE_HEIGHT))
        p_in_top = p_in_bot + Vector((0, 0, rail_h))

        res_horiz = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((0.045, 0.20, 0.035)), verts=res_horiz['verts'])
        bmesh.ops.translate(bm, vec=Vector((side_x, y_wall + 0.10, BASE_HEIGHT + rail_h)), verts=res_horiz['verts'])
        for f in res_horiz['verts']:
            for face in f.link_faces:
                face.material_index = 2

        # Poste maestro terminal que PISA EL OCTÁGONO
        res_post_oct = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((0.04, 0.04, rail_h)), verts=res_post_oct['verts'])
        bmesh.ops.translate(bm, vec=Vector((side_x, y_wall + 0.20, BASE_HEIGHT + rail_h / 2.0)), verts=res_post_oct['verts'])
        for f in res_post_oct['verts']:
            for face in f.link_faces:
                face.material_index = 2

        # Balaustres verticales en cada escalón
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
    rot_mat = Matrix.Rotation(rotation_z, 4, 'Z')
    # Soporte mural
    brk = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((0.08, 0.02, 0.22)), verts=brk['verts'])
    bmesh.ops.transform(bm, matrix=rot_mat, verts=brk['verts'])
    bmesh.ops.translate(bm, vec=center_pos + rot_mat @ Vector((0, 0.01, 0)), verts=brk['verts'])
    for v in brk['verts']:
        for f in v.link_faces:
            f.material_index = 2

    arm = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((0.025, 0.18, 0.025)), verts=arm['verts'])
    bmesh.ops.transform(bm, matrix=rot_mat, verts=arm['verts'])
    bmesh.ops.translate(bm, vec=center_pos + rot_mat @ Vector((0, 0.10, 0)), verts=arm['verts'])
    for v in arm['verts']:
        for f in v.link_faces:
            f.material_index = 2

    lantern_center = center_pos + rot_mat @ Vector((0, 0.19, -0.04))

    # Base inferior
    b_cap = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((0.14, 0.14, 0.025)), verts=b_cap['verts'])
    bmesh.ops.transform(bm, matrix=rot_mat, verts=b_cap['verts'])
    bmesh.ops.translate(bm, vec=lantern_center + Vector((0, 0, -0.16)), verts=b_cap['verts'])
    for v in b_cap['verts']:
        for f in v.link_faces:
            f.material_index = 2

    # Jaula de vidrio
    glass_h = 0.28
    w_bot = 0.13
    w_top = 0.20
    half_bot = w_bot / 2.0
    half_top = w_top / 2.0

    v_gb = [
        Vector((-half_bot, -half_bot, -glass_h / 2.0)),
        Vector(( half_bot, -half_bot, -glass_h / 2.0)),
        Vector(( half_bot,  half_bot, -glass_h / 2.0)),
        Vector((-half_bot,  half_bot, -glass_h / 2.0)),
    ]
    v_gt = [
        Vector((-half_top, -half_top, glass_h / 2.0)),
        Vector(( half_top, -half_top, glass_h / 2.0)),
        Vector(( half_top,  half_top, glass_h / 2.0)),
        Vector((-half_top,  half_top, glass_h / 2.0)),
    ]
    v_gb_w = [bm.verts.new(lantern_center + rot_mat @ v) for v in v_gb]
    v_gt_w = [bm.verts.new(lantern_center + rot_mat @ v) for v in v_gt]

    for vi in range(4):
        vn = (vi + 1) % 4
        fg = bm.faces.new([v_gb_w[vi], v_gb_w[vn], v_gt_w[vn], v_gt_w[vi]])
        fg.material_index = 3
        fg.smooth = True

    # Montantes esquineros
    for vi in range(4):
        p1 = lantern_center + rot_mat @ v_gb[vi]
        p2 = lantern_center + rot_mat @ v_gt[vi]
        p_mid = (p1 + p2) / 2.0
        p_dir = (p2 - p1)
        p_len = p_dir.length
        p_rot = Vector((0, 0, 1)).rotation_difference(p_dir)

        strut = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((0.016, 0.016, p_len)), verts=strut['verts'])
        bmesh.ops.rotate(bm, cent=Vector((0,0,0)), matrix=p_rot.to_matrix(), verts=strut['verts'])
        bmesh.ops.translate(bm, vec=p_mid, verts=strut['verts'])
        for v in strut['verts']:
            for f in v.link_faces:
                f.material_index = 2

    # Tejadillo piramidal
    pyr_h = 0.12
    v_pyr_peak = bm.verts.new(lantern_center + rot_mat @ Vector((0, 0, glass_h / 2.0 + pyr_h)))
    for vi in range(4):
        vn = (vi + 1) % 4
        f_pyr = bm.faces.new([v_gt_w[vi], v_gt_w[vn], v_pyr_peak])
        f_pyr.material_index = 2

    # Pináculo
    fin = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((0.03, 0.03, 0.06)), verts=fin['verts'])
    bmesh.ops.transform(bm, matrix=rot_mat, verts=fin['verts'])
    bmesh.ops.translate(bm, vec=lantern_center + rot_mat @ Vector((0, 0, glass_h / 2.0 + pyr_h + 0.03)), verts=fin['verts'])
    for v in fin['verts']:
        for f in v.link_faces:
            f.material_index = 2


def build_columns(mats, col):
    """
    Construye las 8 Columnas Radiales (v3.0):
    - Plinto base blanco moldurado.
    - Fuste con 18 hiladas gruesas de ladrillo artesanal siglo XIX con textura PBR.
    - Capiteles ensanchados (0.58 x 0.58 m) que acunan el anillo cilíndrico.
    - Faroles coloniales en la cara exterior.
    """
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.verify()
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
                f.material_index = 1

        ch_res = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((PLINTH_SIZE - 0.04, PLINTH_SIZE - 0.04, 0.06)), verts=ch_res['verts'])
        bmesh.ops.transform(bm, matrix=rot_mat, verts=ch_res['verts'])
        bmesh.ops.translate(bm, vec=col_pos + Vector((0, 0, 1.34 + 0.03)), verts=ch_res['verts'])
        for v in ch_res['verts']:
            for f in v.link_faces:
                f.material_index = 1

        # 2. Fuste de ladrillo artesanal decimonónico (Z = 1.40 a 3.74 m, H = 2.34 m)
        # 18 hiladas gruesas compactas sin bandas blancas ni separaciones pronunciadas (fiel a media_1789717720582.png)
        fuste_z_start = 1.40
        fuste_z_end = 3.74
        fuste_h = fuste_z_end - fuste_z_start
        num_courses = 18
        total_course_h = fuste_h / num_courses # ~0.13 m
        brick_h = total_course_h - 0.003       # Junta casi a tope con leve hendidura rústica (3 mm)

        for c in range(num_courses):
            cz_brick = fuste_z_start + c * total_course_h + total_course_h / 2.0
            c_size = COLUMN_SIZE - (0.004 if c % 2 == 0 else 0.001)
            b_res = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=Vector((c_size, c_size, brick_h)), verts=b_res['verts'])
            bmesh.ops.transform(bm, matrix=rot_mat, verts=b_res['verts'])
            bmesh.ops.translate(bm, vec=col_pos + Vector((0, 0, cz_brick)), verts=b_res['verts'])
            for v in b_res['verts']:
                for f in v.link_faces:
                    f.material_index = 0
                    for loop in f.loops:
                        # Mapeo UV que rota y desplaza por hilada para romper uniformidad
                        u_coord = (loop.vert.co.x + loop.vert.co.y) * 1.8 + (c * 0.15)
                        v_coord = loop.vert.co.z * 1.2
                        loop[uv_layer].uv = Vector((u_coord, v_coord))

        # 3. Capitel blanco ensanchado (Z = 3.74 a 3.92 m, ancho 0.58 m)
        c1_res = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((COLUMN_SIZE + 0.04, COLUMN_SIZE + 0.04, 0.04)), verts=c1_res['verts'])
        bmesh.ops.transform(bm, matrix=rot_mat, verts=c1_res['verts'])
        bmesh.ops.translate(bm, vec=col_pos + Vector((0, 0, 3.74 + 0.02)), verts=c1_res['verts'])
        for v in c1_res['verts']:
            for f in v.link_faces:
                f.material_index = 1

        c2_res = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((0.54, 0.54, 0.06)), verts=c2_res['verts'])
        bmesh.ops.transform(bm, matrix=rot_mat, verts=c2_res['verts'])
        bmesh.ops.translate(bm, vec=col_pos + Vector((0, 0, 3.78 + 0.03)), verts=c2_res['verts'])
        for v in c2_res['verts']:
            for f in v.link_faces:
                f.material_index = 1

        c3_res = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((CAPITAL_SIZE, CAPITAL_SIZE, 0.08)), verts=c3_res['verts'])
        bmesh.ops.transform(bm, matrix=rot_mat, verts=c3_res['verts'])
        bmesh.ops.translate(bm, vec=col_pos + Vector((0, 0, 3.84 + 0.04)), verts=c3_res['verts'])
        for v in c3_res['verts']:
            for f in v.link_faces:
                f.material_index = 1

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
    """
    Construye los Barandales Perimetrales (v3.0):
    - 7 vanos regulares completos entre columnas (k = 1 a 7).
    - 2 tramos cortos en la cara frontal (k = 0) desde las columnas hasta encontrarse
      con la barandilla de la escalinata.
    """
    bm = bmesh.new()
    base_angle = -math.pi / 2.0 - math.pi / 8.0

    def add_railing_section(p_start, p_end):
        span_vec = p_end - p_start
        span_dist = span_vec.length
        if span_dist < 0.05:
            return
        span_dir = span_vec.normalized()
        span_mid = (p_start + p_end) / 2.0
        rot_angle = math.atan2(span_dir.y, span_dir.x)
        rot_mat = Matrix.Rotation(rot_angle, 4, 'Z')

        # 1. Solera inferior (Z = 1.28 m)
        r_bot = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((span_dist, 0.03, 0.015)), verts=r_bot['verts'])
        bmesh.ops.transform(bm, matrix=rot_mat, verts=r_bot['verts'])
        bmesh.ops.translate(bm, vec=span_mid + Vector((0, 0, 1.28)), verts=r_bot['verts'])

        # 2. Sub-solera (Z = 1.98 m)
        r_sub = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((span_dist, 0.03, 0.015)), verts=r_sub['verts'])
        bmesh.ops.transform(bm, matrix=rot_mat, verts=r_sub['verts'])
        bmesh.ops.translate(bm, vec=span_mid + Vector((0, 0, 1.98)), verts=r_sub['verts'])

        # 3. Pasamanos superior (Z = 2.10 m)
        r_top = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((span_dist, 0.05, 0.025)), verts=r_top['verts'])
        bmesh.ops.transform(bm, matrix=rot_mat, verts=r_top['verts'])
        bmesh.ops.translate(bm, vec=span_mid + Vector((0, 0, 2.10)), verts=r_top['verts'])

        # 4. Cenefa de Aros decorativos (Z = 1.98 a 2.10 m)
        num_rings = int(span_dist / 0.11)
        if num_rings > 0:
            ring_step = span_dist / num_rings
            for ri in range(num_rings):
                t = (ri + 0.5) * ring_step - span_dist / 2.0
                ring_pos = span_mid + span_dir * t + Vector((0, 0, 2.04))
                ring_mat = Matrix.Translation(ring_pos) @ rot_mat
                create_annular_ring(bm, r_in=0.032, r_out=0.046, thick=0.012, segments=12, matrix=ring_mat)

        # 5. Balaustres verticales
        num_balusters = max(int(span_dist / 0.11), 1)
        bal_step = span_dist / num_balusters
        bal_h = 1.98 - 1.28
        for bi in range(num_balusters):
            t = (bi + 0.5) * bal_step - span_dist / 2.0
            bal_pos = span_mid + span_dir * t + Vector((0, 0, 1.28 + bal_h / 2.0))
            bal_res = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=Vector((0.020, 0.020, bal_h)), verts=bal_res['verts'])
            bmesh.ops.transform(bm, matrix=rot_mat, verts=bal_res['verts'])
            bmesh.ops.translate(bm, vec=bal_pos, verts=bal_res['verts'])

    # 1. Los 7 vanos regulares completos
    for k in range(1, 8):
        ang1 = base_angle + k * (math.pi / 4.0)
        ang2 = base_angle + ((k + 1) % 8) * (math.pi / 4.0)
        p1 = Vector((COL_RADIUS * math.cos(ang1), COL_RADIUS * math.sin(ang1), 0.0))
        p2 = Vector((COL_RADIUS * math.cos(ang2), COL_RADIUS * math.sin(ang2), 0.0))
        span_dir = (p2 - p1).normalized()
        p1_trim = p1 + span_dir * (COLUMN_SIZE / 2.0)
        p2_trim = p2 - span_dir * (COLUMN_SIZE / 2.0)
        add_railing_section(p1_trim, p2_trim)

    # 2. Cara frontal (k = 0): Encuentro entre columnas y escalinata
    col0_pos = Vector((COL_RADIUS * math.cos(base_angle), COL_RADIUS * math.sin(base_angle), 0.0))
    col1_pos = Vector((COL_RADIUS * math.cos(base_angle + math.pi / 4.0), COL_RADIUS * math.sin(base_angle + math.pi / 4.0), 0.0))

    half_w = STAIR_WIDTH / 2.0
    stair_left_post = Vector((-half_w, -OCT_APOTHEM + 0.20, 0.0))
    stair_right_post = Vector(( half_w, -OCT_APOTHEM + 0.20, 0.0))

    # Tramo izquierdo: Col 0 -> Poste izquierdo escalinata
    c0_inner = col0_pos + Vector((COLUMN_SIZE / 2.0, 0, 0))
    add_railing_section(c0_inner, stair_left_post)

    # Tramo derecho: Poste derecho escalinata -> Col 1
    c1_inner = col1_pos - Vector((COLUMN_SIZE / 2.0, 0, 0))
    add_railing_section(stair_right_post, c1_inner)

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
    Construye los 8 Arcos Calados de Herrería Superiores |_^_| (v3.0):
    - Solera superior horizontal anclada bajo el anillo (Z = 3.86 m).
    - Montantes verticales en los extremos junto a las columnas (Z = 3.52 a 3.86 m).
    - Perfil inferior con tramos horizontales de arranque y arco que apunta hacia ARRIBA (Z = 3.52 a 3.78 m).
    - Barrotes verticales calados desde el arco hacia la solera superior, dejando el vano libre |_^_|.
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
        half_s = clear_span / 2.0
        rot_angle = math.atan2(span_dir.y, span_dir.x)
        rot_mat = Matrix.Rotation(rot_angle, 4, 'Z')

        # 1. Solera superior horizontal en Z = 3.86 m
        top_bar = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((clear_span, 0.03, 0.02)), verts=top_bar['verts'])
        bmesh.ops.transform(bm, matrix=rot_mat, verts=top_bar['verts'])
        bmesh.ops.translate(bm, vec=span_mid + Vector((0, 0, 3.86)), verts=top_bar['verts'])

        # 2. Montantes verticales laterales en los extremos (| en |_^_|)
        side_h = 3.86 - 3.52
        for s_sign in [-1.0, 1.0]:
            side_pos = span_mid + span_dir * (s_sign * (half_s - 0.015)) + Vector((0, 0, 3.52 + side_h / 2.0))
            s_post = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=Vector((0.025, 0.025, side_h)), verts=s_post['verts'])
            bmesh.ops.transform(bm, matrix=rot_mat, verts=s_post['verts'])
            bmesh.ops.translate(bm, vec=side_pos, verts=s_post['verts'])

        # 3. Tramos horizontales de arranque inferior (_ en |_^_|)
        step_len = 0.16
        for s_sign in [-1.0, 1.0]:
            step_mid = span_mid + span_dir * (s_sign * (half_s - step_len / 2.0)) + Vector((0, 0, 3.52))
            st_bar = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=Vector((step_len, 0.025, 0.02)), verts=st_bar['verts'])
            bmesh.ops.transform(bm, matrix=rot_mat, verts=st_bar['verts'])
            bmesh.ops.translate(bm, vec=step_mid, verts=st_bar['verts'])

        # 4. Arco que apunta hacia ARRIBA (^ en |_^_|)
        # Sube desde Z = 3.52 m hasta Z = 3.78 m en el centro
        arc_half_span = half_s - step_len
        arc_segments = 16
        z_spring = 3.52
        z_crown = 3.78

        prev_pt = None
        for s in range(arc_segments + 1):
            u = s / float(arc_segments)
            t = -arc_half_span + u * (2.0 * arc_half_span)
            # Curva que alcanza su máximo z_crown en el centro (t = 0)
            z_curve = z_crown - (z_crown - z_spring) * ((t / arc_half_span) ** 2)
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

        # 5. Crestería de barrotes verticales calados que van del arco/solera hacia la solera superior
        num_pickets = int(clear_span / 0.09)
        picket_step = clear_span / max(num_pickets, 1)
        for pi in range(num_pickets):
            t = (pi + 0.5) * picket_step - half_s
            abs_t = abs(t)
            if abs_t > arc_half_span:
                z_bot = 3.52
            else:
                z_bot = z_crown - (z_crown - z_spring) * ((abs_t / arc_half_span) ** 2)

            z_top = 3.86
            bar_len = z_top - z_bot
            if bar_len > 0.025:
                bar_res = bmesh.ops.create_cube(bm, size=1.0)
                bmesh.ops.scale(bm, vec=Vector((0.016, 0.016, bar_len)), verts=bar_res['verts'])
                bmesh.ops.transform(bm, matrix=rot_mat, verts=bar_res['verts'])
                bmesh.ops.translate(bm, vec=span_mid + span_dir * t + Vector((0, 0, (z_bot + z_top) / 2.0)), verts=bar_res['verts'])

        # 6. Volutas decorativas en las esquinas inferiores
        for s_sign in [-1.0, 1.0]:
            scroll_pos = span_mid + span_dir * (s_sign * (half_s - 0.08)) + Vector((0, 0, 3.60))
            sc_mat = Matrix.Translation(scroll_pos) @ rot_mat
            create_annular_ring(bm, r_in=0.025, r_out=0.038, thick=0.012, segments=12, matrix=sc_mat)

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
    Construye el Anillo de Entablamento Cilíndrico Continuo (v2.0):
    - Cilindro perfecto de 96 subdivisiones (Ø ext 7.50 m, H = 0.55 m).
    - Moldura en voladizo superior (Ø 7.70 m).
    - Bóveda interior cónica enyesada (Soffit) de Z = 4.00 a 4.60 m.
    """
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.verify()

    segments = 96
    z_bot = RING_Z_BOTTOM
    z_top = RING_Z_TOP
    z_mid = z_bot + 0.38
    r_main = RING_R_OUT
    r_cornice = RING_R_CORNICE
    r_in = RING_R_IN

    v_ext_bot, v_ext_mid, v_ext_corn, v_ext_top = [], [], [], []
    v_int_top, v_int_bot = [], []

    for i in range(segments):
        ang = (2.0 * math.pi * i) / segments
        ca, sa = math.cos(ang), math.sin(ang)
        v_ext_bot.append(bm.verts.new(Vector((ca * r_main, sa * r_main, z_bot))))
        v_ext_mid.append(bm.verts.new(Vector((ca * r_main, sa * r_main, z_mid))))
        v_ext_corn.append(bm.verts.new(Vector((ca * r_cornice, sa * r_cornice, z_top - 0.05))))
        v_ext_top.append(bm.verts.new(Vector((ca * r_cornice, sa * r_cornice, z_top))))
        v_int_top.append(bm.verts.new(Vector((ca * r_in, sa * r_in, z_top))))
        v_int_bot.append(bm.verts.new(Vector((ca * r_in, sa * r_in, z_bot + 0.15))))

    for i in range(segments):
        nxt = (i + 1) % segments
        # Cara exterior principal
        f1 = bm.faces.new([v_ext_bot[i], v_ext_bot[nxt], v_ext_mid[nxt], v_ext_mid[i]])
        f2 = bm.faces.new([v_ext_mid[i], v_ext_mid[nxt], v_ext_corn[nxt], v_ext_corn[i]])
        f3 = bm.faces.new([v_ext_corn[i], v_ext_corn[nxt], v_ext_top[nxt], v_ext_top[i]])
        f_top = bm.faces.new([v_ext_top[i], v_ext_top[nxt], v_int_top[nxt], v_int_top[i]])
        f_in = bm.faces.new([v_int_top[i], v_int_top[nxt], v_int_bot[nxt], v_int_bot[i]])
        f_bot_ann = bm.faces.new([v_int_bot[nxt], v_int_bot[i], v_ext_bot[i], v_ext_bot[nxt]])

        for f in [f1, f2, f3, f_top, f_in, f_bot_ann]:
            f.material_index = 0
            f.smooth = True

    # Plafón interior / Cielo abovedado cónico (Z = 4.00 a 4.60 m)
    v_apex_vault = bm.verts.new(Vector((0.0, 0.0, 4.60)))
    for i in range(segments):
        nxt = (i + 1) % segments
        f_vault = bm.faces.new([v_int_bot[nxt], v_int_bot[i], v_apex_vault])
        f_vault.material_index = 0
        f_vault.smooth = True

    mesh = bpy.data.meshes.new("Mesh_Anillo_Entablamento")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Anillo_Entablamento", mesh)
    obj.data.materials.append(mats["M_Estuco_Blanco"])
    col.objects.link(obj)
    return obj


def build_conical_roof(mats, col):
    """
    Construye la Cubierta Cónica con Tejas Coloniales 3D Volumétricas (v3.0):
    - 40 sectores radiales alrededor del cono circular (R_base = 3.92 m, peak = 5.50 m).
    - 6 hiladas concéntricas escalonadas con solape real entre niveles superiores e inferiores.
    - Tejas curvas físicas 3D (canal y cobija) con labio frontal de espesor real (0.016 m).
    - Alero perimetral ondulado donde las cobijas sobresalen con volumen real sobre el entablamento.
    - Pináculo cónico cerámico en la cúspide (Z = 5.50 a 5.66 m).
    """
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.verify()

    N_RADIAL = 40
    N_TIERS = 6
    R_BASE = ROOF_R_BASE
    R_TOP = 0.40
    Z_EAVE = ROOF_Z_EAVE
    Z_PEAK = ROOF_Z_PEAK
    h_cobija = 0.045
    h_canal = 0.035
    tile_thick = 0.016

    for tier in range(N_TIERS):
        frac_t = tier / float(N_TIERS)
        frac_b = (tier + 1.15) / float(N_TIERS)
        if tier == N_TIERS - 1:
            frac_b = 1.02 # Vuelo sobre el alero

        r_top = R_TOP + (R_BASE - R_TOP) * frac_t
        r_bot = R_TOP + (R_BASE - R_TOP) * frac_b

        tier_lift = (N_TIERS - 1 - tier) * 0.018
        z_top = Z_PEAK + (Z_EAVE - Z_PEAK) * (frac_t ** 0.95) + tier_lift
        z_bot = Z_PEAK + (Z_EAVE - Z_PEAK) * (frac_b ** 0.95) + tier_lift

        d_theta = 2.0 * math.pi / N_RADIAL
        for i in range(N_RADIAL):
            # 1. Cobija (over-tile)
            th_center = i * d_theta
            half_ang = d_theta * 0.38
            n_arc = 4
            v_top, v_bot, v_bot_under = [], [], []

            for a in range(n_arc + 1):
                fa = -1.0 + 2.0 * (a / float(n_arc))
                ang = th_center + fa * half_ang
                cos_a = math.cos(ang)
                sin_a = math.sin(ang)
                arc_h = h_cobija * math.cos(fa * math.pi * 0.5)

                p_t = Vector((r_top * cos_a, r_top * sin_a, z_top + arc_h))
                p_b = Vector((r_bot * cos_a, r_bot * sin_a, z_bot + arc_h))
                p_bu = Vector((r_bot * cos_a, r_bot * sin_a, z_bot + arc_h - tile_thick))

                v_top.append(bm.verts.new(p_t))
                v_bot.append(bm.verts.new(p_b))
                v_bot_under.append(bm.verts.new(p_bu))

            for a in range(n_arc):
                # Superficie superior curva
                f_top = bm.faces.new([v_top[a], v_top[a+1], v_bot[a+1], v_bot[a]])
                f_top.material_index = 0
                f_top.smooth = True
                u1 = (i + (a / n_arc)) / N_RADIAL * 4.0
                u2 = (i + ((a+1) / n_arc)) / N_RADIAL * 4.0
                f_top.loops[0][uv_layer].uv = Vector((u1, tier))
                f_top.loops[1][uv_layer].uv = Vector((u2, tier))
                f_top.loops[2][uv_layer].uv = Vector((u2, tier + 1))
                f_top.loops[3][uv_layer].uv = Vector((u1, tier + 1))

                # Labio frontal de grosor físico
                f_lip = bm.faces.new([v_bot[a], v_bot[a+1], v_bot_under[a+1], v_bot_under[a]])
                f_lip.material_index = 0
                f_lip.smooth = True

            # 2. Canal (under-tile)
            th_c_center = (i + 0.5) * d_theta
            half_c_ang = d_theta * 0.36
            vc_top, vc_bot = [], []

            for a in range(n_arc + 1):
                fa = -1.0 + 2.0 * (a / float(n_arc))
                ang = th_c_center + fa * half_c_ang
                cos_a = math.cos(ang)
                sin_a = math.sin(ang)
                arc_hc = -h_canal * math.cos(fa * math.pi * 0.5) - 0.015

                pc_t = Vector((r_top * cos_a, r_top * sin_a, z_top + arc_hc))
                pc_b = Vector((r_bot * cos_a, r_bot * sin_a, z_bot + arc_hc))
                vc_top.append(bm.verts.new(pc_t))
                vc_bot.append(bm.verts.new(pc_b))

            for a in range(n_arc):
                f_c = bm.faces.new([vc_top[a], vc_top[a+1], vc_bot[a+1], vc_bot[a]])
                f_c.material_index = 0
                f_c.smooth = True

    # 3. Manto / Entablado de soporte bajo las tejas (cierra cualquier holgura bajo las canales)
    v_deck_bot, v_deck_top = [], []
    for i in range(N_RADIAL):
        ang = (2.0 * math.pi * i) / N_RADIAL
        ca, sa = math.cos(ang), math.sin(ang)
        v_deck_bot.append(bm.verts.new(Vector(((R_BASE - 0.04) * ca, (R_BASE - 0.04) * sa, Z_EAVE - 0.02))))
        v_deck_top.append(bm.verts.new(Vector((0.36 * ca, 0.36 * sa, Z_PEAK - 0.02))))

    for i in range(N_RADIAL):
        nxt = (i + 1) % N_RADIAL
        f_dk = bm.faces.new([v_deck_bot[i], v_deck_bot[nxt], v_deck_top[nxt], v_deck_top[i]])
        f_dk.material_index = 0
        f_dk.smooth = True

    # 4. Pináculo cónico cerámico en la cúspide (Z = 5.48 a 5.66 m)
    finial_base = bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.36, radius2=0.12, depth=0.16)
    bmesh.ops.translate(bm, vec=Vector((0.0, 0.0, Z_PEAK + 0.06)), verts=finial_base['verts'])
    for v in finial_base['verts']:
        for f in v.link_faces:
            f.material_index = 0
            f.smooth = True

    finial_tip = bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.12, radius2=0.015, depth=0.12)
    bmesh.ops.translate(bm, vec=Vector((0.0, 0.0, Z_PEAK + 0.18)), verts=finial_tip['verts'])
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
    col_setup = bpy.data.collections.new("Setup_Render")
    bpy.context.scene.collection.children.link(col_setup)

    # Suelo receptor de sombras neutro
    bpy.ops.mesh.primitive_plane_add(size=80.0, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground_Shadow_Receiver"
    col_setup.objects.link(ground)
    bpy.context.scene.collection.objects.unlink(ground)

    mat_g = bpy.data.materials.new(name="M_Ground_Shadow")
    mat_g.use_nodes = True
    bsdf_g = mat_g.node_tree.nodes.get("Principled BSDF")
    bsdf_g.inputs["Base Color"].default_value = (0.92, 0.92, 0.92, 1.0)
    bsdf_g.inputs["Roughness"].default_value = 0.90
    ground.data.materials.append(mat_g)

    # Iluminación de 3 puntos calibrada
    light_key_data = bpy.data.lights.new(name="Sun_Key", type='SUN')
    light_key_data.energy = 3.6
    light_key_data.color = (1.0, 0.98, 0.94)
    light_key_obj = bpy.data.objects.new("Sun_Key", light_key_data)
    light_key_obj.rotation_euler = (math.radians(52), math.radians(18), math.radians(-38))
    col_setup.objects.link(light_key_obj)

    light_fill_data = bpy.data.lights.new(name="Sun_Fill", type='SUN')
    light_fill_data.energy = 2.2
    light_fill_data.color = (0.90, 0.94, 1.0)
    light_fill_obj = bpy.data.objects.new("Sun_Fill", light_fill_data)
    light_fill_obj.rotation_euler = (math.radians(45), math.radians(-25), math.radians(140))
    col_setup.objects.link(light_fill_obj)

    light_rim_data = bpy.data.lights.new(name="Sun_Rim", type='SUN')
    light_rim_data.energy = 2.6
    light_rim_data.color = (1.0, 0.96, 0.90)
    light_rim_obj = bpy.data.objects.new("Sun_Rim", light_rim_data)
    light_rim_obj.rotation_euler = (math.radians(35), math.radians(40), math.radians(-150))
    col_setup.objects.link(light_rim_obj)

    # Cámaras de inspección calibradas
    cams = {}
    cam_configs = [
        ("Cam_Preview", (7.8, -9.6, 6.2), (math.radians(65), 0, math.radians(38)), 48),
        ("Cam_Acceso", (2.8, -6.8, 2.4), (math.radians(76), 0, math.radians(22)), 45),
        ("Cam_Columnas_Arcos", (1.4, -4.6, 3.4), (math.radians(78), 0, math.radians(18)), 42),
        ("Cam_Techo", (4.8, -6.4, 5.8), (math.radians(58), 0, math.radians(36)), 50),
    ]

    for name, pos, rot, fov in cam_configs:
        cdata = bpy.data.cameras.new(name)
        cdata.lens = fov
        cobj = bpy.data.objects.new(name, cdata)
        cobj.location = pos
        cobj.rotation_euler = rot
        col_setup.objects.link(cobj)
        cams[name] = cobj

    # Cielo atmosférico diurno
    if bpy.context.scene.world and bpy.context.scene.world.node_tree:
        bg_node = bpy.context.scene.world.node_tree.nodes.get("Background")
        if bg_node:
            bg_node.inputs["Color"].default_value = (0.78, 0.84, 0.90, 1.0)
            bg_node.inputs["Strength"].default_value = 0.85
    return cams


def render_views():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1200
    scene.render.film_transparent = False

    render_jobs = [
        ("Cam_Preview", "kiosko_preview.png", "Render 1: Vista General Axonométrica"),
        ("Cam_Acceso", "kiosko_acceso.png", "Render 2: Detalle Escalinata y Acceso"),
        ("Cam_Columnas_Arcos", "kiosko_columnas_arcos.png", "Render 3: Detalle Columnas y Arcos |_^_|"),
        ("Cam_Techo", "kiosko_techo.png", "Render 4: Detalle Tejas 3D y Entablamento"),
    ]

    for cam_name, filename, desc in render_jobs:
        cam_obj = bpy.data.objects.get(cam_name)
        if not cam_obj:
            continue
        scene.camera = cam_obj
        filepath = os.path.abspath(os.path.join("docs", "images", filename))
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        scene.render.filepath = filepath
        bpy.ops.render.render(write_still=True)
        print(f"--> {desc} guardado: {filepath}")


def export_gltf(output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    root_obj = bpy.data.objects.get("Kiosco_Root")
    if not root_obj:
        print("ERROR: Kiosco_Root no encontrado para exportación.")
        return

    bpy.ops.object.select_all(action='DESELECT')
    root_obj.select_set(True)
    for child in root_obj.children:
        child.select_set(True)

    bpy.ops.export_scene.gltf(
        filepath=output_path,
        use_selection=True,
        export_format='GLB',
        export_materials='EXPORT',
        export_yup=True,
        export_apply=True
    )
    print(f"--> Modelo optimizado para Godot exportado: {output_path}")


def main():
    print("================================================================")
    print(" GENERADOR PARAMÉTRICO: KIOSCO PARQUE HIDALGO (v3.0 FINAL)      ")
    print("================================================================")

    clean_scene()
    col_kiosko = bpy.data.collections.new("Kiosko_Tecate")
    bpy.context.scene.collection.children.link(col_kiosko)

    # Raíz del Kiosco en (0, 0, 0)
    root = bpy.data.objects.new("Kiosco_Root", None)
    root.empty_display_type = 'ARROWS'
    root.empty_display_size = 1.0
    col_kiosko.objects.link(root)

    mats = create_materials()

    # Construcción de los componentes
    base_obj = build_octagonal_base(mats, col_kiosko)
    base_obj.parent = root

    stairs_obj = build_staircase(mats, col_kiosko)
    stairs_obj.parent = root

    cols_obj = build_columns(mats, col_kiosko)
    cols_obj.parent = root

    rails_obj = build_perimeter_railings(mats, col_kiosko)
    rails_obj.parent = root

    arches_obj = build_openwork_arches(mats, col_kiosko)
    arches_obj.parent = root

    ring_obj = build_entablature_ring(mats, col_kiosko)
    ring_obj.parent = root

    roof_obj = build_conical_roof(mats, col_kiosko)
    roof_obj.parent = root

    # Métricas y validación
    min_z = 0.0
    max_z = ROOF_Z_PEAK + 0.18 # Incluyendo pináculo
    print(f"--> Altura Total Calculada: {max_z:.3f} m (Min Z: {min_z:.3f} m, Max Z: {max_z:.3f} m)")
    print(f"--> Envergadura X (Diámetro Tejado): {ROOF_R_BASE * 2.0:.3f} m")
    print(f"--> Envergadura Y (con Escalinata): {OCT_APOTHEM + STAIR_STEPS * STAIR_TREAD + OCT_CIRCUM:.3f} m")

    # Guardar archivo maestro Blender
    blend_path = os.path.abspath("blender_assets/kiosko_parque_hidalgo.blend")
    os.makedirs(os.path.dirname(blend_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"--> Archivo maestro Blender guardado: {blend_path}")

    # Exportar glTF 2.0 para Godot
    glb_path = os.path.abspath("godot_project/assets/kiosko_parque_hidalgo.glb")
    export_gltf(glb_path)

    # Setup de estudio y renders
    setup_lighting_and_cameras()
    render_views()

    print("================================================================")
    print(" GENERACIÓN DEL KIOSCO v3.0 FINALIZADA EXITOSAMENTE            ")
    print("================================================================")


if __name__ == "__main__":
    main()
