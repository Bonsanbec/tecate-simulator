"""
GENERADOR PROCEDURAL 3D - PALACIO MUNICIPAL DE TECATE (ÉPOCA 2009)
Tecate Simulator - Godot Engine 4 / Blender Python Headless API

Ubicación: Pdte. Pascual Ortiz Rubio 1310, Zona Centro, 21400 Tecate, B.C., México
Coordenadas GPS: 32.572932°N, -116.626027°W
Manzana: block_lat_32.57293_lon_-116.62685

Disposición de Fachadas Canónica:
  - Chaflán central con pórtico monumental de 4 columnas, balcón y copete con hornacina
  - Lado Izquierdo (Ala Norte): 3 crujías con arcos de ladrillo
  - Lado Derecho (Ala Oriente): 4 crujías con arcos de ladrillo
  - Zócalo basal enterrado: Z in [-1.50, 0.00] m
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector

def clean_scene():
    """Limpia la escena inicial y crea la colección principal del edificio."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    col = bpy.data.collections.new("Palacio_Municipal_Collection")
    scene.collection.children.link(col)
    return col

def create_materials():
    """Crea la suite de materiales PBR calibrados según las fotografías históricas de 2009."""
    mats = {}

    # 1. Muro Estuco Blanco
    m_wall = bpy.data.materials.new("M_Estuco_Blanco")
    m_wall.use_nodes = True
    bsdf = m_wall.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.86, 0.86, 0.84, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.85
    mats["blanco"] = m_wall

    # 2. Estuco Ocre Mostaza (Zócalo basal, plintos, capiteles, cornisas, spandrels)
    m_ocre = bpy.data.materials.new("M_Estuco_Ocre")
    m_ocre.use_nodes = True
    bsdf_o = m_ocre.node_tree.nodes.get("Principled BSDF")
    bsdf_o.inputs["Base Color"].default_value = (0.74, 0.58, 0.22, 1.0)
    bsdf_o.inputs["Roughness"].default_value = 0.78
    mats["ocre"] = m_ocre

    # 3. Ladrillo Rojo Cocido (Arcos y sardineles)
    m_brick = bpy.data.materials.new("M_Ladrillo_Arco")
    m_brick.use_nodes = True
    bsdf_br = m_brick.node_tree.nodes.get("Principled BSDF")
    bsdf_br.inputs["Base Color"].default_value = (0.52, 0.18, 0.12, 1.0)
    bsdf_br.inputs["Roughness"].default_value = 0.82
    mats["ladrillo"] = m_brick

    # 4. Vidrio Comercial Oscuro Tintado
    m_glass = bpy.data.materials.new("M_Vidrio_Oscuro")
    m_glass.use_nodes = True
    bsdf_gl = m_glass.node_tree.nodes.get("Principled BSDF")
    bsdf_gl.inputs["Base Color"].default_value = (0.04, 0.06, 0.08, 1.0)
    bsdf_gl.inputs["Roughness"].default_value = 0.08
    bsdf_gl.inputs["Transmission Weight"].default_value = 0.85
    bsdf_gl.inputs["IOR"].default_value = 1.52
    mats["vidrio"] = m_glass

    # 5. Cancelería Aluminio Negro
    m_alum = bpy.data.materials.new("M_Canceleria")
    m_alum.use_nodes = True
    bsdf_al = m_alum.node_tree.nodes.get("Principled BSDF")
    bsdf_al.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1.0)
    bsdf_al.inputs["Metallic"].default_value = 0.85
    bsdf_al.inputs["Roughness"].default_value = 0.30
    mats["aluminio"] = m_alum

    # 6. Oro / Bronce Relieve (Rótulo y Escudo)
    m_gold = bpy.data.materials.new("M_Letras_Oro")
    m_gold.use_nodes = True
    bsdf_gd = m_gold.node_tree.nodes.get("Principled BSDF")
    bsdf_gd.inputs["Base Color"].default_value = (0.85, 0.70, 0.20, 1.0)
    bsdf_gd.inputs["Metallic"].default_value = 0.85
    bsdf_gd.inputs["Roughness"].default_value = 0.25
    mats["oro"] = m_gold

    # 7. Azotea Asfáltica Impermeabilizada
    m_roof = bpy.data.materials.new("M_Azotea_Asfalto")
    m_roof.use_nodes = True
    bsdf_rf = m_roof.node_tree.nodes.get("Principled BSDF")
    bsdf_rf.inputs["Base Color"].default_value = (0.045, 0.045, 0.045, 1.0)
    bsdf_rf.inputs["Roughness"].default_value = 0.95
    mats["azotea"] = m_roof

    return mats

def assign_material_slots(obj, mat_dict):
    """Asigna todos los materiales a los slots del objeto para referencia por índice."""
    order = ["blanco", "ocre", "ladrillo", "vidrio", "aluminio", "oro", "azotea"]
    for key in order:
        if key in mat_dict:
            obj.data.materials.append(mat_dict[key])
    return {k: i for i, k in enumerate(order)}

def add_box(bm, x1, x2, y1, y2, z1, z2, mat_idx=0):
    """Genera una caja ortogonal cerrada con normales al exterior y material asignado."""
    v = [
        bm.verts.new((x1, y1, z1)), bm.verts.new((x2, y1, z1)),
        bm.verts.new((x2, y2, z1)), bm.verts.new((x1, y2, z1)),
        bm.verts.new((x1, y1, z2)), bm.verts.new((x2, y1, z2)),
        bm.verts.new((x2, y2, z2)), bm.verts.new((x1, y2, z2))
    ]
    faces = [
        (0, 1, 2, 3), (4, 7, 6, 5),
        (0, 4, 5, 1), (1, 5, 6, 2),
        (2, 6, 7, 3), (3, 7, 4, 0)
    ]
    for idxs in faces:
        try:
            f = bm.faces.new([v[i] for i in idxs])
            f.material_index = mat_idx
        except ValueError:
            pass

def add_oriented_box(bm, center_xy, tangent_xy, normal_xy, s_min, s_max, n_min, n_max, z_min, z_max, mat_idx=0):
    """Genera una caja orientada según un marco ortonormal 2D (tangente, normal)."""
    tx, ty = tangent_xy[0], tangent_xy[1]
    nx, ny = normal_xy[0], normal_xy[1]
    cx, cy = center_xy[0], center_xy[1]

    verts = []
    for s in (s_min, s_max):
        for n in (n_min, n_max):
            for z in (z_min, z_max):
                vx = cx + s * tx + n * nx
                vy = cy + s * ty + n * ny
                verts.append(bm.verts.new((vx, vy, z)))

    faces = [
        (0, 1, 3, 2), (4, 6, 7, 5),
        (0, 4, 5, 1), (2, 3, 7, 6),
        (0, 2, 6, 4), (1, 5, 7, 3)
    ]
    for idxs in faces:
        try:
            f = bm.faces.new([verts[i] for i in idxs])
            f.material_index = mat_idx
        except ValueError:
            pass

def add_polygon_slab(bm, poly_xy, z_min, z_max, mat_idx=0):
    """Genera una losa horizontal extruida a partir de un polígono 2D simple."""
    n = len(poly_xy)
    bot_v = [bm.verts.new((pt[0], pt[1], z_min)) for pt in poly_xy]
    top_v = [bm.verts.new((pt[0], pt[1], z_max)) for pt in poly_xy]

    for i in range(n):
        nxt = (i + 1) % n
        try:
            f = bm.faces.new([bot_v[i], bot_v[nxt], top_v[nxt], top_v[i]])
            f.material_index = mat_idx
        except ValueError:
            pass

    try:
        f_top = bm.faces.new(top_v)
        f_top.material_index = mat_idx
    except ValueError:
        pass

    try:
        f_bot = bm.faces.new(list(reversed(bot_v)))
        f_bot.material_index = mat_idx
    except ValueError:
        pass

def add_cylinder(bm, center_xy, radius, z_min, z_max, segments=16, mat_idx=0):
    """Genera un prisma cilíndrico vertical."""
    cx, cy = center_xy[0], center_xy[1]
    bot_v = []
    top_v = []
    for i in range(segments):
        ang = 2.0 * math.pi * i / segments
        vx = cx + radius * math.cos(ang)
        vy = cy + radius * math.sin(ang)
        bot_v.append(bm.verts.new((vx, vy, z_min)))
        top_v.append(bm.verts.new((vx, vy, z_max)))

    for i in range(segments):
        nxt = (i + 1) % segments
        f = bm.faces.new([bot_v[i], bot_v[nxt], top_v[nxt], top_v[i]])
        f.material_index = mat_idx

    f_bot = bm.faces.new(list(reversed(bot_v)))
    f_bot.material_index = mat_idx
    f_top = bm.faces.new(top_v)
    f_top.material_index = mat_idx

def add_arch_border(bm, center_xy, tangent_xy, normal_xy, r_inner, r_outer, z_spring, n_min, n_max, segments=12, mat_idx=2):
    """Genera un arco de medio punto decorativo (dovelas de ladrillo) orientado."""
    cx, cy = center_xy[0], center_xy[1]
    tx, ty = tangent_xy[0], tangent_xy[1]
    nx, ny = normal_xy[0], normal_xy[1]

    ring_inner = []
    ring_outer = []
    for i in range(segments + 1):
        ang = math.pi * i / segments
        s_in = -r_inner * math.cos(ang)
        z_in = z_spring + r_inner * math.sin(ang)
        s_out = -r_outer * math.cos(ang)
        z_out = z_spring + r_outer * math.sin(ang)

        for n in (n_min, n_max):
            vx_in = cx + s_in * tx + n * nx
            vy_in = cy + s_in * ty + n * ny
            ring_inner.append(bm.verts.new((vx_in, vy_in, z_in)))

            vx_out = cx + s_out * tx + n * nx
            vy_out = cy + s_out * ty + n * ny
            ring_outer.append(bm.verts.new((vx_out, vy_out, z_out)))

    for i in range(segments):
        in_curr_n0 = ring_inner[2*i]
        in_curr_n1 = ring_inner[2*i + 1]
        in_next_n0 = ring_inner[2*(i + 1)]
        in_next_n1 = ring_inner[2*(i + 1) + 1]

        out_curr_n0 = ring_outer[2*i]
        out_curr_n1 = ring_outer[2*i + 1]
        out_next_n0 = ring_outer[2*(i + 1)]
        out_next_n1 = ring_outer[2*(i + 1) + 1]

        try:
            f1 = bm.faces.new([in_curr_n1, out_curr_n1, out_next_n1, in_next_n1])
            f1.material_index = mat_idx
        except ValueError:
            pass

        try:
            f2 = bm.faces.new([in_curr_n0, in_curr_n1, in_next_n1, in_next_n0])
            f2.material_index = mat_idx
        except ValueError:
            pass

        try:
            f3 = bm.faces.new([out_curr_n1, out_curr_n0, out_next_n0, out_next_n1])
            f3.material_index = mat_idx
        except ValueError:
            pass

def build_fenestrated_bay(bm, center_xy, tangent_xy, normal_xy, m_idxs):
    """Construye una crujía arquitectónica estándar con vanos y relieves."""
    w_win = 1.60
    r_win = 0.80
    z_bot_up = 4.40
    z_spring = 6.00
    z_top_up = 6.80
    d_brick = 0.28
    t_out = 0.05

    # 1. Arcos y jambas de ladrillo superior
    add_oriented_box(bm, center_xy, tangent_xy, normal_xy,
                     -r_win - d_brick, -r_win, -0.01, t_out, z_bot_up, z_spring, m_idxs["ladrillo"])
    add_oriented_box(bm, center_xy, tangent_xy, normal_xy,
                     r_win, r_win + d_brick, -0.01, t_out, z_bot_up, z_spring, m_idxs["ladrillo"])
    add_arch_border(bm, center_xy, tangent_xy, normal_xy,
                    r_win, r_win + d_brick, z_spring, -0.01, t_out, segments=12, mat_idx=m_idxs["ladrillo"])

    # Vidrio superior oscuro empotrado
    add_oriented_box(bm, center_xy, tangent_xy, normal_xy,
                     -r_win, r_win, -0.22, -0.20, z_bot_up, z_spring, m_idxs["vidrio"])
    add_oriented_box(bm, center_xy, tangent_xy, normal_xy,
                     -r_win + 0.15, r_win - 0.15, -0.22, -0.20, z_spring, z_top_up - 0.08, m_idxs["vidrio"])
    add_oriented_box(bm, center_xy, tangent_xy, normal_xy,
                     -0.03, 0.03, -0.22, -0.18, z_bot_up, z_top_up - 0.12, m_idxs["aluminio"])

    # 2. Spandrel box panel en estuco ocre
    add_oriented_box(bm, center_xy, tangent_xy, normal_xy,
                     -0.925, 0.925, -0.01, 0.12, 3.00, 4.35, m_idxs["ocre"])

    # 3. Ventana inferior rectangular
    add_oriented_box(bm, center_xy, tangent_xy, normal_xy,
                     -0.82, 0.82, -0.05, 0.02, 1.18, 2.82, m_idxs["aluminio"])
    add_oriented_box(bm, center_xy, tangent_xy, normal_xy,
                     -0.80, 0.80, -0.22, -0.20, 1.20, 2.80, m_idxs["vidrio"])
    add_oriented_box(bm, center_xy, tangent_xy, normal_xy,
                     -0.03, 0.03, -0.22, -0.18, 1.20, 2.80, m_idxs["aluminio"])

def build_palacio_geometry(col, mats):
    """
    Genera la geometría física unificada del Palacio Municipal:
      - Ala Oriente (Lado Derecho desde el frente): 4 CRUJÍAS (X de 5.20 a 25.00 m)
      - Ala Norte (Lado Izquierdo desde el frente): 3 CRUJÍAS (Y de 5.20 a 21.40 m)
    """
    me = bpy.data.meshes.new("Mesh_Palacio_Municipal")
    bm = bmesh.new()

    obj = bpy.data.objects.new("Palacio_Municipal_2009", me)
    col.objects.link(obj)
    m_idxs = assign_material_slots(obj, mats)

    T_wall = 0.40
    Z_sub = -1.50
    Z_zoc = 0.90
    Z_roof = 7.00
    Z_pretil = 7.55
    D_east = 11.00
    D_north = 11.00

    center_chamfer = (2.60, 2.60)
    norm_chamfer = (-0.707107, -0.707107)
    tang_chamfer = (0.707107, -0.707107)
    r_chamfer_half = 5.20 * math.sqrt(2.0) / 2.0 # 3.677 m

    # =========================================================================
    # 1. ALA ORIENTE (LADO DERECHO): 4 CRUJÍAS CON ARCOS DE LADRILLO
    #    Superficie exterior en Y = -0.40, normal (0, -1), X in [5.20, 25.00]
    # =========================================================================
    add_box(bm, 5.20, 25.00, -T_wall, 0.0, Z_sub, Z_zoc, m_idxs["ocre"])

    # 4 Crujías centradas en X = [8.00, 12.40, 16.80, 21.20]
    # Vanos de 1.60 m (X in [X-0.80, X+0.80])
    piers_east = [
        (5.20, 7.20),
        (8.80, 11.60),
        (13.20, 16.00),
        (17.60, 20.40),
        (22.00, 25.00)
    ]
    for x1, x2 in piers_east:
        add_box(bm, x1, x2, -T_wall, 0.0, Z_zoc, Z_pretil, m_idxs["blanco"])

    bays_east_x = [8.00, 12.40, 16.80, 21.20]
    for bx in bays_east_x:
        add_box(bm, bx - 0.80, bx + 0.80, -T_wall, 0.0, Z_zoc, 1.18, m_idxs["blanco"])
        add_box(bm, bx - 0.80, bx + 0.80, -T_wall, 0.0, 2.82, 4.40, m_idxs["blanco"])
        add_box(bm, bx - 0.80, bx + 0.80, -T_wall, 0.0, 6.80, Z_pretil, m_idxs["blanco"])
        build_fenestrated_bay(bm, (bx, -T_wall), (1.0, 0.0), (0.0, -1.0), m_idxs)

    # Albardilla cornisa superior oriente (Y = -T_wall)
    add_box(bm, 5.15, 25.05, -T_wall - 0.08, 0.02, 7.40, Z_pretil, m_idxs["ocre"])

    # =========================================================================
    # 2. ALA NORTE (LADO IZQUIERDO): 3 CRUJÍAS CON ARCOS DE LADRILLO
    #    Superficie exterior en X = -0.40, normal (-1, 0), Y in [5.20, 21.40]
    # =========================================================================
    add_box(bm, -T_wall, 0.0, 5.20, 21.40, Z_sub, Z_zoc, m_idxs["ocre"])

    # 3 Crujías centradas en Y = [8.20, 12.80, 17.40]
    piers_north = [
        (5.20, 7.40),
        (9.00, 12.00),
        (13.60, 16.60),
        (18.20, 21.40)
    ]
    for y1, y2 in piers_north:
        add_box(bm, -T_wall, 0.0, y1, y2, Z_zoc, Z_pretil, m_idxs["blanco"])

    bays_north_y = [8.20, 12.80, 17.40]
    for by in bays_north_y:
        add_box(bm, -T_wall, 0.0, by - 0.80, by + 0.80, Z_zoc, 1.18, m_idxs["blanco"])
        add_box(bm, -T_wall, 0.0, by - 0.80, by + 0.80, 2.82, 4.40, m_idxs["blanco"])
        add_box(bm, -T_wall, 0.0, by - 0.80, by + 0.80, 6.80, Z_pretil, m_idxs["blanco"])
        build_fenestrated_bay(bm, (-T_wall, by), (0.0, 1.0), (-1.0, 0.0), m_idxs)

    # Albardilla cornisa superior norte (X = -T_wall)
    add_box(bm, -T_wall - 0.08, 0.02, 5.15, 21.45, 7.40, Z_pretil, m_idxs["ocre"])

    # =========================================================================
    # 3. MUROS MEDIANEROS Y TRASEROS
    # =========================================================================
    # Muro sur medianero en X = 25.00
    add_box(bm, 25.00 - T_wall, 25.00, 0.0, D_east, Z_sub, Z_pretil, m_idxs["blanco"])
    # Muro interior oriente
    add_box(bm, D_north, 25.00, D_east - T_wall, D_east, Z_sub, Z_pretil, m_idxs["blanco"])
    # Muro interior norte
    add_box(bm, D_north - T_wall, D_north, D_east, 21.40, Z_sub, Z_pretil, m_idxs["blanco"])
    # Muro poniente trasero en Y = 21.40
    add_box(bm, 0.0, D_north, 21.40 - T_wall, 21.40, Z_sub, Z_pretil, m_idxs["blanco"])

    # =========================================================================
    # 4. CHAFLÁN RETRANQUEADO (Muro posterior del pórtico)
    # =========================================================================
    add_oriented_box(bm, center_chamfer, tang_chamfer, norm_chamfer,
                     -r_chamfer_half, r_chamfer_half, -T_wall, 0.0, Z_sub, Z_zoc, m_idxs["ocre"])
    add_oriented_box(bm, center_chamfer, tang_chamfer, norm_chamfer,
                     -r_chamfer_half, r_chamfer_half, -T_wall, 0.0, Z_zoc, Z_pretil, m_idxs["blanco"])
    add_oriented_box(bm, center_chamfer, tang_chamfer, norm_chamfer,
                     -r_chamfer_half - 0.05, r_chamfer_half + 0.05, -T_wall - 0.08, 0.04, 7.40, Z_pretil, m_idxs["ocre"])

    # Puerta de acceso diáfana en Planta Baja
    add_oriented_box(bm, center_chamfer, tang_chamfer, norm_chamfer,
                     -1.40, -1.10, 0.0, 0.06, 0.0, 2.80, m_idxs["ladrillo"])
    add_oriented_box(bm, center_chamfer, tang_chamfer, norm_chamfer,
                     1.10, 1.40, 0.0, 0.06, 0.0, 2.80, m_idxs["ladrillo"])
    add_oriented_box(bm, center_chamfer, tang_chamfer, norm_chamfer,
                     -1.40, 1.40, 0.0, 0.06, 2.75, 3.05, m_idxs["ladrillo"])
    add_oriented_box(bm, center_chamfer, tang_chamfer, norm_chamfer,
                     -1.10, 1.10, -0.06, -0.02, 0.0, 2.75, m_idxs["vidrio"])

    # Ventanal de Planta Alta en chaflán
    add_oriented_box(bm, center_chamfer, tang_chamfer, norm_chamfer,
                     -2.10, 2.10, 0.0, 0.04, 4.60, 4.68, m_idxs["aluminio"])
    add_oriented_box(bm, center_chamfer, tang_chamfer, norm_chamfer,
                     -2.10, 2.10, 0.0, 0.04, 6.52, 6.60, m_idxs["aluminio"])
    add_oriented_box(bm, center_chamfer, tang_chamfer, norm_chamfer,
                     -2.00, 2.00, -0.06, -0.02, 4.68, 6.52, m_idxs["vidrio"])
    for ps in [-0.70, 0.70]:
        add_oriented_box(bm, center_chamfer, tang_chamfer, norm_chamfer,
                         ps - 0.03, ps + 0.03, -0.06, 0.02, 4.68, 6.52, m_idxs["aluminio"])

    # =========================================================================
    # 5. PÓRTICO MONUMENTAL Y BALCÓN VOLADO
    # =========================================================================
    d_portico = 1.60
    center_col_line = (center_chamfer[0] + d_portico * norm_chamfer[0],
                       center_chamfer[1] + d_portico * norm_chamfer[1])

    col_s = [-2.55, -0.85, 0.85, 2.55]
    for s in col_s:
        cx = center_col_line[0] + s * tang_chamfer[0]
        cy = center_col_line[1] + s * tang_chamfer[1]
        add_oriented_box(bm, (cx, cy), tang_chamfer, norm_chamfer,
                         -0.30, 0.30, -0.30, 0.30, Z_sub, 0.25, m_idxs["ocre"])
        add_cylinder(bm, (cx, cy), radius=0.24, z_min=0.25, z_max=3.15, segments=16, mat_idx=m_idxs["blanco"])
        add_oriented_box(bm, (cx, cy), tang_chamfer, norm_chamfer,
                         -0.31, 0.31, -0.31, 0.31, 3.15, 3.40, m_idxs["ocre"])

    # Losa del balcón
    add_oriented_box(bm, center_chamfer, tang_chamfer, norm_chamfer,
                     -r_chamfer_half - 0.20, r_chamfer_half + 0.20,
                     -0.10, d_portico + 0.40, 3.40, 3.60, m_idxs["ocre"])

    # Antepecho frontal del balcón
    center_balc_front = (center_chamfer[0] + (d_portico + 0.28) * norm_chamfer[0],
                         center_chamfer[1] + (d_portico + 0.28) * norm_chamfer[1])
    add_oriented_box(bm, center_balc_front, tang_chamfer, norm_chamfer,
                     -3.00, 3.00, -0.12, 0.12, 3.60, 4.55, m_idxs["blanco"])
    add_oriented_box(bm, center_balc_front, tang_chamfer, norm_chamfer,
                     -3.05, 3.05, -0.15, 0.15, 4.50, 4.58, m_idxs["ocre"])

    # Retornos laterales del balcón
    add_oriented_box(bm, center_chamfer, norm_chamfer, tang_chamfer,
                     0.0, d_portico + 0.28, -3.00, -2.76, 3.60, 4.55, m_idxs["blanco"])
    add_oriented_box(bm, center_chamfer, norm_chamfer, tang_chamfer,
                     0.0, d_portico + 0.28, 2.76, 3.00, 3.60, 4.55, m_idxs["blanco"])

    # =========================================================================
    # 6. COPETE SUPERIOR ESCALONADO EN AZOTEA (Frontón con hornacina)
    # =========================================================================
    add_oriented_box(bm, center_chamfer, tang_chamfer, norm_chamfer,
                     -2.50, 2.50, -T_wall, 0.05, 7.40, 8.65, m_idxs["blanco"])
    add_oriented_box(bm, center_chamfer, tang_chamfer, norm_chamfer,
                     -2.55, 2.55, -T_wall - 0.05, 0.10, 8.55, 8.70, m_idxs["ocre"])

    # Nicho semicircular ocre
    add_arch_border(bm, center_chamfer, tang_chamfer, norm_chamfer,
                    0.0, 0.65, z_spring=7.85, n_min=-0.01, n_max=0.07, segments=12, mat_idx=m_idxs["ocre"])
    add_oriented_box(bm, center_chamfer, tang_chamfer, norm_chamfer,
                     -0.65, 0.65, -0.01, 0.07, 7.85, 8.50, m_idxs["ocre"])

    # =========================================================================
    # 7. LOSA DE AZOTEA HERMÉTICA
    # =========================================================================
    poly_roof = [
        (5.20, 0.0),
        (25.00 - T_wall, 0.0),
        (25.00 - T_wall, D_east - T_wall),
        (D_north - T_wall, D_east - T_wall),
        (D_north - T_wall, 21.40 - T_wall),
        (0.0, 21.40 - T_wall),
        (0.0, 5.20)
    ]
    add_polygon_slab(bm, poly_roof, Z_roof - 0.20, Z_roof, m_idxs["azotea"])

    # Finalizar malla
    bm.to_mesh(me)
    bm.free()

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    return obj

def build_signage(col, mats):
    """Genera el rótulo volumétrico 3D 'PALACIO MUNICIPAL' y el Escudo Nacional."""
    center_chamfer = (2.60, 2.60)
    norm_chamfer = (-0.707107, -0.707107)
    d_portico = 1.60
    c_front = (center_chamfer[0] + (d_portico + 0.28 + 0.12 + 0.02) * norm_chamfer[0],
               center_chamfer[1] + (d_portico + 0.28 + 0.12 + 0.02) * norm_chamfer[1])

    # Curva de texto 3D "PALACIO MUNICIPAL"
    txt_data = bpy.data.curves.new(name="Texto_Palacio", type='FONT')
    txt_data.body = "PALACIO MUNICIPAL"
    txt_data.size = 0.26
    txt_data.extrude = 0.025
    txt_data.align_x = 'CENTER'
    txt_data.align_y = 'CENTER'

    txt_obj = bpy.data.objects.new("Rotulo_Palacio_Municipal", txt_data)
    col.objects.link(txt_obj)
    txt_obj.data.materials.append(mats["oro"])

    txt_obj.location = (c_front[0], c_front[1], 3.92)
    txt_obj.rotation_euler = (math.radians(90.0), 0.0, math.radians(-45.0))

    # Escudo Nacional en relieve escultórico con anillo exterior
    me_escudo = bpy.data.meshes.new("Mesh_Escudo_Nacional")
    bm_e = bmesh.new()
    radius_x, radius_z = 0.28, 0.35
    depth = 0.03
    v_ring = []
    seg = 16
    for i in range(seg):
        ang = 2.0 * math.pi * i / seg
        vx = radius_x * math.cos(ang)
        vz = radius_z * math.sin(ang)
        v_ring.append(bm_e.verts.new((vx, 0.0, vz)))
        v_ring.append(bm_e.verts.new((vx, depth, vz)))

    for i in range(seg):
        nxt = (i + 1) % seg
        bm_e.faces.new([v_ring[2*i], v_ring[2*nxt], v_ring[2*nxt + 1], v_ring[2*i + 1]])

    f_front = bm_e.faces.new([v_ring[2*i + 1] for i in range(seg)])
    f_back = bm_e.faces.new([v_ring[2*i] for i in reversed(range(seg))])

    # Anillo exterior moldurado en oro
    r_out_x, r_out_z = 0.32, 0.39
    v_out = []
    for i in range(seg):
        ang = 2.0 * math.pi * i / seg
        vx = r_out_x * math.cos(ang)
        vz = r_out_z * math.sin(ang)
        v_out.append(bm_e.verts.new((vx, depth + 0.015, vz)))

    for i in range(seg):
        nxt = (i + 1) % seg
        bm_e.faces.new([v_ring[2*i + 1], v_ring[2*nxt + 1], v_out[nxt], v_out[i]])

    bm_e.to_mesh(me_escudo)
    bm_e.free()

    escudo_obj = bpy.data.objects.new("Escudo_Nacional", me_escudo)
    col.objects.link(escudo_obj)
    escudo_obj.data.materials.append(mats["oro"])
    escudo_obj.location = (c_front[0] + 0.01 * norm_chamfer[0],
                           c_front[1] + 0.01 * norm_chamfer[1], 4.26)
    escudo_obj.rotation_euler = (0.0, 0.0, math.radians(-45.0))

    return txt_obj, escudo_obj

def setup_lighting_and_cameras(col):
    """Configura sol Cycles y batería canónica de 5 cámaras de inspección."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    if hasattr(scene.cycles, 'device'):
        scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720

    # Sol Diurno
    sun_data = bpy.data.lights.new("Sun_Light", 'SUN')
    sun_data.energy = 4.5
    sun_data.color = (1.0, 0.98, 0.92)
    sun_obj = bpy.data.objects.new("Sun_Light", sun_data)
    col.objects.link(sun_obj)
    sun_obj.rotation_euler = (math.radians(50.0), math.radians(20.0), math.radians(-45.0))

    # Luz de cielo
    world = bpy.data.worlds.new("World_Diurno")
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.65, 0.78, 0.92, 1.0)
    bg.inputs["Strength"].default_value = 1.2
    scene.world = world

    # Cámaras ajustadas
    cams_config = [
        ("Cam_Chaflan_45", (-13.0, -13.0, 5.5), (3.5, 3.5, 3.8), 28),
        ("Cam_Ala_Oriente", (15.10, -16.0, 4.0), (15.10, -0.40, 4.0), 32),
        ("Cam_Ala_Norte", (-16.0, 13.30, 4.0), (-0.40, 13.30, 4.0), 32),
        ("Cam_Cenital_Azotea", (11.0, 11.0, 45.0), (11.0, 11.0, 0.0), 28),
        ("Cam_Closeup_Portico", (-4.0, -4.0, 2.2), (1.5, 1.5, 3.2), 28)
    ]

    cams = {}
    for name, pos, tgt, lens in cams_config:
        c_data = bpy.data.cameras.new(name)
        c_data.lens = lens
        c_obj = bpy.data.objects.new(name, c_data)
        col.objects.link(c_obj)
        c_obj.location = Vector(pos)
        direction = Vector(tgt) - Vector(pos)
        c_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        cams[name] = c_obj

    return cams

def generate_godot_tscn(tscn_path, glb_path):
    """Escribe programáticamente la escena .tscn con física analítica transitable."""
    rel_glb = "res://assets/" + os.path.basename(glb_path)

    content = f'''[gd_scene load_steps=8 format=3 uid="uid://palacio_municipal_2009"]

[ext_resource type="PackedScene" path="{rel_glb}" id="1_mesh"]

[sub_resource type="BoxShape3D" id="BoxShape3D_ala_oriente"]
size = Vector3(19.80, 9.05, 11.00)

[sub_resource type="BoxShape3D" id="BoxShape3D_ala_norte"]
size = Vector3(11.00, 9.05, 16.20)

[sub_resource type="CylinderShape3D" id="CylinderShape3D_columna"]
height = 3.40
radius = 0.25

[sub_resource type="BoxShape3D" id="BoxShape3D_balcon"]
size = Vector3(5.50, 1.20, 2.20)

[sub_resource type="BoxShape3D" id="BoxShape3D_muro_chaflan_sup"]
size = Vector3(5.20, 3.20, 0.40)

[node name="PalacioMunicipal2009" type="StaticBody3D"]

[node name="ModelInstance" parent="." instance=ExtResource("1_mesh")]

[node name="Col_Ala_Oriente" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 15.10, 3.025, 5.50)
shape = SubResource("BoxShape3D_ala_oriente")

[node name="Col_Ala_Norte" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 5.50, 3.025, 13.30)
shape = SubResource("BoxShape3D_ala_norte")

[node name="Col_Pilar_1" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -0.33, 1.70, 3.27)
shape = SubResource("CylinderShape3D_columna")

[node name="Col_Pilar_2" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.87, 1.70, 2.07)
shape = SubResource("CylinderShape3D_columna")

[node name="Col_Pilar_3" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.07, 1.70, 0.87)
shape = SubResource("CylinderShape3D_columna")

[node name="Col_Pilar_4" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 3.27, 1.70, -0.33)
shape = SubResource("CylinderShape3D_columna")

[node name="Col_Balcon" type="CollisionShape3D" parent="."]
transform = Transform3D(0.707107, 0, -0.707107, 0, 1, 0, 0.707107, 0, 0.707107, 1.47, 4.00, 1.47)
shape = SubResource("BoxShape3D_balcon")

[node name="Col_Muro_Chaflan_Sup" type="CollisionShape3D" parent="."]
transform = Transform3D(0.707107, 0, -0.707107, 0, 1, 0, 0.707107, 0, 0.707107, 2.60, 5.80, 2.60)
shape = SubResource("BoxShape3D_muro_chaflan_sup")
'''
    os.makedirs(os.path.dirname(os.path.abspath(tscn_path)), exist_ok=True)
    with open(tscn_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[TSCN] Escena analítica generada exitosamente en: {tscn_path}")

def render_validation_views(cams, render_dir):
    """Renderiza las vistas fijas con Cycles para inspección en bucle cerrado."""
    os.makedirs(render_dir, exist_ok=True)
    scene = bpy.context.scene

    for name, cam_obj in cams.items():
        scene.camera = cam_obj
        out_path = os.path.join(render_dir, f"{name}.png")
        scene.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        print(f"[Render] Generado: {out_path}")

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    blend_path = os.path.join(root_dir, "blender_assets", "palacio_municipal_2009.blend")
    glb_path = os.path.join(root_dir, "godot_project", "assets", "palacio_municipal_2009.glb")
    tscn_path = os.path.join(root_dir, "godot_project", "assets", "palacio_municipal_2009.tscn")
    render_dir = os.path.join(root_dir, "docs", "images", "palacio_municipal")

    os.makedirs(os.path.dirname(blend_path), exist_ok=True)
    os.makedirs(os.path.dirname(glb_path), exist_ok=True)

    print(">>> 1. Limpiando escena e inicializando materiales PBR...")
    col = clean_scene()
    mats = create_materials()

    print(">>> 2. Construyendo volumetría arquitectónica del Palacio Municipal...")
    bldg_obj = build_palacio_geometry(col, mats)

    print(">>> 3. Generando rótulo 3D y heráldica institucional...")
    txt_obj, escudo_obj = build_signage(col, mats)

    print(">>> 4. Guardando archivo maestro Blender .blend...")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"[Blender] Archivo maestro guardado: {blend_path}")

    print(">>> 5. Exportando runtime GLB optimizado...")
    bpy.ops.object.select_all(action='DESELECT')
    bldg_obj.select_set(True)
    txt_obj.select_set(True)
    escudo_obj.select_set(True)
    bpy.context.view_layer.objects.active = bldg_obj

    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        use_selection=True,
        export_format='GLB',
        export_apply=True,
        export_yup=True
    )
    print(f"[GLTF] Asset de producción exportado: {glb_path}")

    print(">>> 6. Generando escena Godot .tscn con física analítica...")
    generate_godot_tscn(tscn_path, glb_path)

    print(">>> 7. Configurando batería de validación y renderizando cámaras...")
    cams = setup_lighting_and_cameras(col)
    render_validation_views(cams, render_dir)

    print(">>> PROCESO COMPLETADO EXITOSAMENTE.")

if __name__ == "__main__":
    main()
