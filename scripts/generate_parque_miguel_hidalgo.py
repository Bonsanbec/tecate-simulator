#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador Procedural 3D: Parque Miguel Hidalgo (Centro Histórico de Tecate, Época 2009)
Tecate Simulator — Reconstrucción Fotorrealista para Blender y Godot 4

Cumple estrictamente con las reglas de GEMINI.md:
- Zócalo basal enterrado continuo (Z <= -1.50m) para absorción topográfica.
- Prohibición absoluta de banquetas embebidas en el .glb (pertenecen a capas GIS).
- Colisiones analíticas en Godot 4 (.tscn) con BoxShape3D y CylinderShape3D transitables.
- Inversión canónica de ejes de profundidad: Z_godot = -Y_blender.
- Orientación de monumentos: Juárez y Cárdenas mirando hacia sus esquinas exteriores,
  Hidalgo mirando hacia el interior (Kiosko).
- Bancas colocadas estrictamente dentro de los andadores, mirando hacia el centro de los andadores.
- Supresión total de palmeras; arbolado de fresnos y eucaliptos de copa orgánica.
- Dimensiones adaptadas milimétricamente al bloque catastral de Manzanas (117m x 79.5m).
"""

import os
import sys
import math
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
GLB_OUT_PATH = os.path.join(PROJECT_ROOT, "godot_project/assets/parque_miguel_hidalgo.glb")
TSCN_OUT_PATH = os.path.join(PROJECT_ROOT, "godot_project/assets/parque_miguel_hidalgo.tscn")
BLEND_OUT_PATH = os.path.join(PROJECT_ROOT, "blender_assets/parque_miguel_hidalgo.blend")
RENDERS_DIR = os.path.join(PROJECT_ROOT, "docs/images/parque_miguel_hidalgo")
TEXTURES_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/textures")
os.makedirs(RENDERS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GLB_OUT_PATH), exist_ok=True)
os.makedirs(os.path.dirname(BLEND_OUT_PATH), exist_ok=True)

print("[PARQUE HIDALGO] Limpiando escena de Blender...")
bpy.ops.wm.read_factory_settings(use_empty=True)

# ==============================================================================
# 1. CREACIÓN DE MATERIALES PBR CALIBRADOS
# ==============================================================================
def create_pbr_material(name, base_color=(0.8, 0.8, 0.8, 1.0), roughness=0.8, metallic=0.0,
                        texture_prefix=None, uv_scale=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_out.location = (400, 0)
    node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_bsdf.location = (0, 0)
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])

    node_bsdf.inputs['Base Color'].default_value = base_color
    node_bsdf.inputs['Roughness'].default_value = roughness
    node_bsdf.inputs['Metallic'].default_value = metallic

    if texture_prefix:
        albedo_path = os.path.join(TEXTURES_DIR, f"{texture_prefix}_albedo.png")
        normal_path = os.path.join(TEXTURES_DIR, f"{texture_prefix}_normal.png")
        rough_path = os.path.join(TEXTURES_DIR, f"{texture_prefix}_roughness.png")

        tex_coord = nodes.new(type='ShaderNodeTexCoord')
        tex_coord.location = (-800, 0)
        mapping = nodes.new(type='ShaderNodeMapping')
        mapping.location = (-600, 0)
        mapping.inputs['Scale'].default_value = (uv_scale, uv_scale, uv_scale)
        links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

        if os.path.exists(albedo_path):
            img_alb = bpy.data.images.load(albedo_path)
            node_alb = nodes.new(type='ShaderNodeTexImage')
            node_alb.location = (-350, 200)
            node_alb.image = img_alb
            links.new(mapping.outputs['Vector'], node_alb.inputs['Vector'])
            links.new(node_alb.outputs['Color'], node_bsdf.inputs['Base Color'])

        if os.path.exists(rough_path):
            img_rgh = bpy.data.images.load(rough_path)
            img_rgh.colorspace_settings.name = 'Non-Color'
            node_rgh = nodes.new(type='ShaderNodeTexImage')
            node_rgh.location = (-350, -50)
            node_rgh.image = img_rgh
            links.new(mapping.outputs['Vector'], node_rgh.inputs['Vector'])
            links.new(node_rgh.outputs['Color'], node_bsdf.inputs['Roughness'])

        if os.path.exists(normal_path):
            img_nrm = bpy.data.images.load(normal_path)
            img_nrm.colorspace_settings.name = 'Non-Color'
            node_nrm_img = nodes.new(type='ShaderNodeTexImage')
            node_nrm_img.location = (-350, -300)
            node_nrm_img.image = img_nrm
            node_nrm_map = nodes.new(type='ShaderNodeNormalMap')
            node_nrm_map.location = (-100, -300)
            links.new(mapping.outputs['Vector'], node_nrm_img.inputs['Vector'])
            links.new(node_nrm_img.outputs['Color'], node_nrm_map.inputs['Color'])
            links.new(node_nrm_map.outputs['Normal'], node_bsdf.inputs['Normal'])

    return mat

mat_adoquin = create_pbr_material("M_Adoquin_Andador", (0.70, 0.69, 0.66, 1.0), 0.80, 0.0, "parque_adoquin", 0.6)
mat_laja = create_pbr_material("M_Piedra_Laja", (0.82, 0.70, 0.52, 1.0), 0.75, 0.0, uv_scale=1.2)
mat_ocre = create_pbr_material("M_Murete_Ocre", (0.84, 0.64, 0.22, 1.0), 0.85, 0.0) # #C89B3C Amarillo Ocre Municipal
mat_cesped = create_pbr_material("M_Cesped_Jardin", (0.22, 0.46, 0.14, 1.0), 0.95, 0.0, "parque_cesped", 0.4)
mat_tierra = create_pbr_material("M_Tierra_Alcorque", (0.18, 0.13, 0.09, 1.0), 0.95, 0.0)
mat_bronce = create_pbr_material("M_Bronce_Estatua", (0.14, 0.13, 0.11, 1.0), 0.35, 0.85) # Bronce patinado oscuro
mat_bronce_oro = create_pbr_material("M_Bronce_Dorado", (0.52, 0.44, 0.22, 1.0), 0.28, 0.85) # Hidalgo oro antiguo
mat_cantera = create_pbr_material("M_Cantera_Pedestal", (0.74, 0.72, 0.68, 1.0), 0.80, 0.0)
mat_cantera_oscura = create_pbr_material("M_Cantera_Oscura", (0.12, 0.12, 0.13, 1.0), 0.40, 0.05) # Benito Juárez
mat_pedestal_blanco = create_pbr_material("M_Pedestal_Blanco", (0.94, 0.93, 0.90, 1.0), 0.65, 0.0)
mat_madera = create_pbr_material("M_Madera_Banca", (0.34, 0.16, 0.07, 1.0), 0.45, 0.0)
mat_forja = create_pbr_material("M_Herreria_Parque", (0.05, 0.05, 0.06, 1.0), 0.40, 0.85)
mat_caseta_verde = create_pbr_material("M_Caseta_Verde", (0.09, 0.24, 0.12, 1.0), 0.70, 0.0)
mat_teja_roja = create_pbr_material("M_Teja_Roja", (0.60, 0.20, 0.11, 1.0), 0.75, 0.0)
mat_letras_negras = create_pbr_material("M_Letras_Negras", (0.03, 0.03, 0.03, 1.0), 0.80, 0.0)
mat_letras_doradas = create_pbr_material("M_Letras_Doradas", (0.80, 0.70, 0.35, 1.0), 0.35, 0.85)
mat_zocalo = create_pbr_material("M_Zocalo_Basal", (0.28, 0.28, 0.28, 1.0), 0.95, 0.0)
mat_corteza = create_pbr_material("M_Corteza_Arbol", (0.40, 0.33, 0.26, 1.0), 0.90, 0.0, "parque_corteza", 0.4)
mat_follaje = create_pbr_material("M_Follaje_Arbol", (0.16, 0.38, 0.10, 1.0), 0.60, 0.0)
mat_azul_tambo = create_pbr_material("M_Azul_Tambo", (0.05, 0.25, 0.65, 1.0), 0.50, 0.1)
mat_blanco_camisa = create_pbr_material("M_Blanco_Camisa", (0.92, 0.92, 0.90, 1.0), 0.70, 0.0)

# ==============================================================================
# 2. MOTOR GEOMÉTRICO BMESH CON NORMALES EXTERIORES EXACTAS
# ==============================================================================
mesh_parque = bpy.data.meshes.new("Parque_Geometria_Base")
obj_parque = bpy.data.objects.new("Parque_Geometria_Base", mesh_parque)
bpy.context.scene.collection.objects.link(obj_parque)

material_list = [
    mat_adoquin, mat_laja, mat_ocre, mat_cesped, mat_tierra,
    mat_bronce, mat_bronce_oro, mat_cantera, mat_cantera_oscura,
    mat_pedestal_blanco, mat_madera, mat_forja, mat_caseta_verde,
    mat_teja_roja, mat_letras_negras, mat_letras_doradas, mat_zocalo,
    mat_corteza, mat_follaje, mat_azul_tambo, mat_blanco_camisa
]
for m in material_list:
    obj_parque.data.materials.append(m)

idx_adoquin = 0
idx_laja = 1
idx_ocre = 2
idx_cesped = 3
idx_tierra = 4
idx_bronce = 5
idx_bronce_oro = 6
idx_cantera = 7
idx_cantera_oscura = 8
idx_pedestal_blanco = 9
idx_madera = 10
idx_forja = 11
idx_caseta_verde = 12
idx_teja_roja = 13
idx_letras_negras = 14
idx_letras_doradas = 15
idx_zocalo = 16
idx_corteza = 17
idx_follaje = 18
idx_azul_tambo = 19
idx_blanco_camisa = 20

bm = bmesh.new()
uv_layer = bm.loops.layers.uv.new("UVMap")

def assign_uvs(faces, scale=1.0):
    for f in faces:
        n = f.normal
        for loop in f.loops:
            co = loop.vert.co
            if abs(n.z) > 0.5:
                loop[uv_layer].uv = (co.x * scale, co.y * scale)
            elif abs(n.x) > 0.5:
                loop[uv_layer].uv = (co.y * scale, co.z * scale)
            else:
                loop[uv_layer].uv = (co.x * scale, co.z * scale)

def add_solid_box(bm, center, size, rot_z=0.0, mat_index=0, uv_scale=1.0):
    cx, cy, cz = center
    sx, sy, sz = size[0]*0.5, size[1]*0.5, size[2]*0.5
    raw_verts = [
        (-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
        (-sx, -sy,  sz), (sx, -sy,  sz), (sx, sy,  sz), (-sx, sy,  sz)
    ]
    ca = math.cos(rot_z)
    sa = math.sin(rot_z)
    transformed_verts = []
    for vx, vy, vz in raw_verts:
        rx = vx * ca - vy * sa + cx
        ry = vx * sa + vy * ca + cy
        transformed_verts.append(bm.verts.new((rx, ry, vz + cz)))

    face_indices = [
        (0, 3, 2, 1), # Inferior (-Z)
        (4, 5, 6, 7), # Superior (+Z)
        (0, 1, 5, 4), # Sur (-Y)
        (1, 2, 6, 5), # Este (+X)
        (2, 3, 7, 6), # Norte (+Y)
        (3, 0, 4, 7), # Oeste (-X)
    ]
    faces = []
    for idxs in face_indices:
        f = bm.faces.new([transformed_verts[i] for i in idxs])
        f.material_index = mat_index
        faces.append(f)
    assign_uvs(faces, uv_scale)
    return faces

def add_solid_cylinder(bm, center, radius, height, segments=24, mat_index=0, smooth=True, uv_scale=1.0):
    cx, cy, cz = center
    z_bot = cz - height * 0.5
    z_top = cz + height * 0.5
    bot_v = []
    top_v = []
    for i in range(segments):
        ang = 2.0 * math.pi * i / segments
        x = cx + radius * math.cos(ang)
        y = cy + radius * math.sin(ang)
        bot_v.append(bm.verts.new((x, y, z_bot)))
        top_v.append(bm.verts.new((x, y, z_top)))

    faces = []
    for i in range(segments):
        i_n = (i + 1) % segments
        f = bm.faces.new([bot_v[i], top_v[i], top_v[i_n], bot_v[i_n]])
        f.smooth = smooth
        f.material_index = mat_index
        faces.append(f)
    f_top = bm.faces.new(list(reversed(top_v)))
    f_top.material_index = mat_index
    faces.append(f_top)
    f_bot = bm.faces.new(bot_v)
    f_bot.material_index = mat_index
    faces.append(f_bot)

    assign_uvs(faces, uv_scale)
    return faces

def add_solid_ring(bm, center, r_ext, r_int, height, segments=28, mat_index=0, smooth=True):
    cx, cy, cz = center
    zb = cz - height * 0.5
    zt = cz + height * 0.5
    ext_b, ext_t = [], []
    int_b, int_t = [], []
    for i in range(segments):
        ang = 2.0 * math.pi * i / segments
        ca, sa = math.cos(ang), math.sin(ang)
        ext_b.append(bm.verts.new((cx + r_ext * ca, cy + r_ext * sa, zb)))
        ext_t.append(bm.verts.new((cx + r_ext * ca, cy + r_ext * sa, zt)))
        int_b.append(bm.verts.new((cx + r_int * ca, cy + r_int * sa, zb)))
        int_t.append(bm.verts.new((cx + r_int * ca, cy + r_int * sa, zt)))

    faces = []
    for i in range(segments):
        i_n = (i + 1) % segments
        f_ext = bm.faces.new([ext_b[i], ext_t[i], ext_t[i_n], ext_b[i_n]])
        f_ext.smooth = smooth
        f_ext.material_index = mat_index
        faces.append(f_ext)

        f_int = bm.faces.new([int_b[i], int_b[i_n], int_t[i_n], int_t[i]])
        f_int.smooth = smooth
        f_int.material_index = mat_index
        faces.append(f_int)

        f_top = bm.faces.new([ext_t[i], ext_t[i_n], int_t[i_n], int_t[i]])
        f_top.material_index = mat_index
        faces.append(f_top)

        f_bot = bm.faces.new([ext_b[i], int_b[i], int_b[i_n], ext_b[i_n]])
        f_bot.material_index = mat_index
        faces.append(f_bot)

    assign_uvs(faces, 1.0)
    return faces

def add_truncated_pyramid(bm, center, base_s, top_s, height, rot_z=0.0, mat_index=0):
    cx, cy, cz = center
    bx, by = base_s[0]*0.5, base_s[1]*0.5
    tx, ty = top_s[0]*0.5, top_s[1]*0.5
    zb = cz - height*0.5
    zt = cz + height*0.5

    b_raw = [(-bx, -by, zb), (bx, -by, zb), (bx, by, zb), (-bx, by, zb)]
    t_raw = [(-tx, -ty, zt), (tx, -ty, zt), (tx, ty, zt), (-tx, ty, zt)]

    ca, sa = math.cos(rot_z), math.sin(rot_z)
    def trans(p):
        return (p[0]*ca - p[1]*sa + cx, p[0]*sa + p[1]*ca + cy, p[2])

    bv = [bm.verts.new(trans(p)) for p in b_raw]
    tv = [bm.verts.new(trans(p)) for p in t_raw]

    faces = [
        bm.faces.new([bv[0], bv[3], bv[2], bv[1]]), # base (-Z)
        bm.faces.new([tv[0], tv[1], tv[2], tv[3]]), # tope (+Z)
        bm.faces.new([bv[0], bv[1], tv[1], tv[0]]), # cara 1
        bm.faces.new([bv[1], bv[2], tv[2], tv[1]]), # cara 2
        bm.faces.new([bv[2], bv[3], tv[3], tv[2]]), # cara 3
        bm.faces.new([bv[3], bv[0], tv[0], tv[3]]), # cara 4
    ]
    for f in faces:
        f.material_index = mat_index
    assign_uvs(faces, 1.0)
    return faces

def add_3d_text_letters(bm, text_lines, center_x, center_y, base_z, rot_z=0.0,
                        line_spacing=0.20, char_w=0.08, char_h=0.10, char_d=0.03, mat_idx=0):
    ca, sa = math.cos(rot_z), math.sin(rot_z)
    for line_idx, line in enumerate(text_lines):
        cur_z = base_z - line_idx * line_spacing
        n_chars = len(line)
        spacing = char_w * 1.35
        total_w = n_chars * spacing
        start_u = -total_w * 0.5 + spacing * 0.5
        for char_i, ch in enumerate(line):
            if ch != ' ':
                u = start_u + char_i * spacing
                lx = u * ca + center_x
                ly = u * sa + center_y
                add_solid_box(bm, center=(lx, ly, cur_z), size=(char_w, char_d, char_h), rot_z=rot_z, mat_index=mat_idx)

# ==============================================================================
# 3. TOPOGRAFÍA, ZÓCALO BASAL Y 8 ANDADORES EN ESTRELLA (POLÍGONO REAL DE MANZANA)
# ==============================================================================
print("[PARQUE HIDALGO] Construyendo plataforma sólida con el perímetro exacto de las calles...")

# Polígono perimetral exacto del Parque Hidalgo según las banquetas interiores de las 4 calles
# (Av. Benito Juárez al Norte, Pdte. Pascual Ortiz Rubio al Este, Callejón Libertad al Sur,
# y Pdte. Lázaro Cárdenas al Poniente con sus ochavas y alineación angular real).
# Coordenadas relativas al Kiosko central (0.0, 0.0).
PARK_PERIMETER_POLYGON = [
    # Borde Este (Ortiz Rubio - de Norte a Sur)
    (55.74, 25.22),
    (56.49, 16.56),
    (57.48, 5.02),
    (57.97, -0.75),
    (58.46, -6.52),
    (59.21, -15.17),
    (60.45, -29.65),
    # Ochava SE (Ortiz Rubio y Callejón Libertad)
    (60.95, -35.53),
    (54.27, -38.22),
    # Borde Sur (Callejón Libertad - de Este a Oeste)
    (30.00, -38.50),
    (0.00, -38.80),
    (-25.00, -39.00),
    # Ochava SO (Callejón Libertad y Pdte. Lázaro Cárdenas)
    (-38.59, -39.11),
    (-40.01, -28.33),
    # Borde Poniente (Pdte. Lázaro Cárdenas - de Sur a Norte)
    (-41.22, -19.74),
    (-42.43, -11.16),
    (-43.63, -2.57),
    (-44.69, 5.74),
    (-45.69, 14.09),
    (-46.70, 22.44),
    # Ochava NO (Pdte. Cárdenas y Av. Benito Juárez)
    (-35.05, 33.99),
    # Borde Norte (Av. Benito Juárez - de Oeste a Este, pendiente angular ~6.5°)
    (-26.28, 35.00),
    (-17.50, 36.01),
    (-11.65, 36.68),
    (-2.87, 37.69),
    (2.98, 38.36),
    (11.75, 39.37),
    (20.53, 40.38),
    (29.30, 41.39),
    # Ochava NE (Av. Benito Juárez y Ortiz Rubio)
    (43.93, 43.08),
]

poly_xs = [p[0] for p in PARK_PERIMETER_POLYGON]
poly_ys = [p[1] for p in PARK_PERIMETER_POLYGON]
park_min_x, park_max_x = min(poly_xs), max(poly_xs)
park_min_y, park_max_y = min(poly_ys), max(poly_ys)
park_w = park_max_x - park_min_x
park_d = park_max_y - park_min_y
park_cx = (park_min_x + park_max_x) * 0.5
park_cy = (park_min_y + park_max_y) * 0.5

def add_extruded_polygon(bm, polygon_2d, z_top=0.00, z_bottom=-1.50, top_mat=idx_cesped, side_mat=idx_zocalo, bottom_mat=idx_zocalo):
    """
    Extruye verticalmente un polígono cerrado 2D arbitrario.
    Genera zócalo basal continuo Z <= -1.50m (Garantía GEMINI.md) con orientación manifold hacia afuera.
    """
    signed_area = 0.0
    n = len(polygon_2d)
    for i in range(n):
        j = (i + 1) % n
        signed_area += polygon_2d[i][0] * polygon_2d[j][1] - polygon_2d[j][0] * polygon_2d[i][1]

    pts = list(polygon_2d)
    if signed_area < 0:
        pts.reverse()

    n_pts = len(pts)
    top_verts = [bm.verts.new((x, y, z_top)) for x, y in pts]
    bot_verts = [bm.verts.new((x, y, z_bottom)) for x, y in pts]

    # Cara superior (CCW -> normal hacia +Z)
    face_top = bm.faces.new(top_verts)
    face_top.material_index = top_mat
    res_top = bmesh.ops.triangulate(bm, faces=[face_top])
    for f in res_top['faces']:
        f.material_index = top_mat

    # Cara inferior (CW -> normal hacia -Z)
    face_bot = bm.faces.new(list(reversed(bot_verts)))
    face_bot.material_index = bottom_mat
    res_bot = bmesh.ops.triangulate(bm, faces=[face_bot])
    for f in res_bot['faces']:
        f.material_index = bottom_mat

    # Caras laterales (muros perimetrales del zócalo)
    side_faces = []
    for i in range(n_pts):
        j = (i + 1) % n_pts
        f_side = bm.faces.new([top_verts[i], top_verts[j], bot_verts[j], bot_verts[i]])
        f_side.material_index = side_mat
        side_faces.append(f_side)

    bm.normal_update()
    assign_uvs(list(res_top['faces']), scale=0.35)
    assign_uvs(side_faces, scale=1.0)

# Construir plataforma basal con zócalo perimetral continuo a Z = -1.50m
add_extruded_polygon(bm, PARK_PERIMETER_POLYGON, z_top=0.00, z_bottom=-1.50, top_mat=idx_cesped, side_mat=idx_zocalo)

# Glorieta central de adoquín alrededor del Kiosko (vano libre R=5.80m que respeta las escaleras del Kiosko)
add_solid_ring(bm, center=(0.0, 0.0, 0.03), r_ext=12.00, r_int=5.80, height=0.06, segments=36, mat_index=idx_adoquin)
add_solid_ring(bm, center=(0.0, 0.0, 0.16), r_ext=12.35, r_int=12.00, height=0.32, segments=36, mat_index=idx_ocre)

# Función de Andador Sólido Orientado en Ángulo Exacto
def add_oriented_walkway(start_xy, end_xy, width, mat_idx=idx_adoquin):
    sx, sy = start_xy
    ex, ey = end_xy
    dx = ex - sx
    dy = ey - sy
    length = math.hypot(dx, dy)
    if length < 0.1:
        return
    angle = math.atan2(dy, dx)
    mid_x = (sx + ex) * 0.5
    mid_y = (sy + ey) * 0.5

    # Superficie del andador sólida
    add_solid_box(bm, center=(mid_x, mid_y, 0.03), size=(length, width, 0.06), rot_z=angle, mat_index=mat_idx, uv_scale=0.6)

    # Bordillos laterales continuos amarillos ocre
    curb_w = 0.22
    curb_h = 0.28
    ca, sa = math.cos(angle), math.sin(angle)
    offset_dist = (width * 0.5 + curb_w * 0.5)

    l_x = mid_x - sa * offset_dist
    l_y = mid_y + ca * offset_dist
    add_solid_box(bm, center=(l_x, l_y, curb_h*0.5), size=(length, curb_w, curb_h), rot_z=angle, mat_index=idx_ocre)

    r_x = mid_x + sa * offset_dist
    r_y = mid_y - ca * offset_dist
    add_solid_box(bm, center=(r_x, r_y, curb_h*0.5), size=(length, curb_w, curb_h), rot_z=angle, mat_index=idx_ocre)

# 8 Andadores radiales en estrella (trazado orgánico asimétrico original que preserva las visuales históricas)
add_oriented_walkway((0.0, 12.0), (0.0, 38.0), 4.80)     # Norte (Av. Benito Juárez)
# Andador Sur dividido para alojar la explanada peatonal circular del Monumento a Hidalgo (hid_y = -22.0)
add_oriented_walkway((0.0, -12.0), (0.0, -16.2), 4.80)   # Sur (Tramo norte hacia Kiosko)
add_oriented_walkway((0.0, -27.8), (0.0, -39.0), 4.80)   # Sur (Tramo sur hacia Callejón Libertad)
add_oriented_walkway((12.0, 0.0), (34.0, 0.0), 5.20)     # Este (Conecta exactamente en el borde de la explanada Este X=34)
add_oriented_walkway((-12.0, 0.0), (-32.0, 0.0), 5.00)   # Poniente (Conecta en el borde de la explanada Poniente X=-32)
add_oriented_walkway((-8.5, 8.5), (-25.10, 13.16), 4.00) # Diagonal NO (Conecta en el perímetro exterior R=7.5m de la Fuente)
add_oriented_walkway((8.5, 8.5), (32.0, 23.0), 4.00)     # Diagonal NE (Hacia Monumento a Juárez)
add_oriented_walkway((-8.5, -8.5), (-36.0, -25.0), 4.00) # Diagonal SO (Hacia Monumento a Cárdenas)
add_oriented_walkway((8.5, -8.5), (34.0, -24.0), 4.00)   # Diagonal SE (Mismo ángulo histórico ~ -31.3° que sus homólogos NE y SO)

# Conexión continua desde el perímetro de la Fuente hacia el acceso noroeste (Ochava NO)
add_oriented_walkway((-38.55, 19.35), (-44.0, 23.0), 3.80)

# Explanada circular pavimentada para la Fuente de la Paz (R=7.50m, centro exacto coincidente con Godot)
fuente_cx, fuente_cy = -32.3156, 15.1878
add_solid_cylinder(bm, center=(fuente_cx, fuente_cy, 0.03), radius=7.50, height=0.06, segments=36, mat_index=idx_adoquin)
add_solid_ring(bm, center=(fuente_cx, fuente_cy, 0.16), r_ext=7.80, r_int=7.50, height=0.32, segments=36, mat_index=idx_ocre)

# Explanadas pavimentadas en accesos este y poniente (confinadas estrictamente dentro del polígono)
add_solid_box(bm, center=(46.0, 0.0, 0.03), size=(24.0, 24.0, 0.06), mat_index=idx_adoquin, uv_scale=0.6)
add_solid_box(bm, center=(-38.0, 0.0, 0.03), size=(12.0, 16.0, 0.06), mat_index=idx_adoquin, uv_scale=0.6)


# ==============================================================================
# 4. MODELADO DE LOS 4 MONUMENTOS HISTÓRICOS (ORIENTACIÓN RIGUROSA)
# ==============================================================================
print("[PARQUE HIDALGO] Construyendo los 4 monumentos históricos fotorrealistas...")

# ------------------------------------------------------------------------------
# MONUMENTO 1: BUSTO A DON MIGUEL HIDALGO Y COSTILLA (Sector Sur)
# Mirando hacia dentro (hacia el norte +Y, hacia el Kiosko)
# ------------------------------------------------------------------------------
hid_x, hid_y = 0.0, -22.0

# 0. Explanada circular peatonal adoquinada alrededor del monumento (R=5.80m)
add_solid_cylinder(bm, center=(hid_x, hid_y, 0.03), radius=5.80, height=0.06, segments=36, mat_index=idx_adoquin)
# Bordillos curvados ocre delimitando jardineras laterales (este y oeste), dejando libres los accesos norte y sur (|X| <= 2.4)
n_curb_h = 32
for i in range(n_curb_h):
    ang1 = 2.0 * math.pi * i / n_curb_h
    ang2 = 2.0 * math.pi * (i + 1) / n_curb_h
    mid_ang = (ang1 + ang2) * 0.5
    if abs(math.cos(mid_ang)) > 0.45:
        p1 = (hid_x + 5.92 * math.cos(ang1), hid_y + 5.92 * math.sin(ang1), 0.16)
        p2 = (hid_x + 5.92 * math.cos(ang2), hid_y + 5.92 * math.sin(ang2), 0.16)
        mx, my = (p1[0] + p2[0]) * 0.5, (p1[1] + p2[1]) * 0.5
        seg_len = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        seg_ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        add_solid_box(bm, center=(mx, my, 0.16), size=(seg_len * 1.05, 0.25, 0.32), rot_z=seg_ang, mat_index=idx_ocre)

# 1. Medallón circular en el suelo (Piedra laja rústica de media_1790414613164.png)
add_solid_cylinder(bm, center=(hid_x, hid_y, 0.04), radius=3.20, height=0.08, segments=32, mat_index=idx_laja)
add_solid_ring(bm, center=(hid_x, hid_y, 0.06), r_ext=3.40, r_int=3.20, height=0.12, segments=32, mat_index=idx_cantera)

# 2. Zócalo de mampostería de piedra rústica
add_solid_box(bm, center=(hid_x, hid_y, 0.22), size=(1.70, 1.70, 0.36), mat_index=idx_cantera)

# 3. Pedestal blanco moldurado clásico (Obelisco truncado de media_1790414613164.png)
add_solid_box(bm, center=(hid_x, hid_y, 0.46), size=(1.10, 1.10, 0.16), mat_index=idx_pedestal_blanco)
add_truncated_pyramid(bm, center=(hid_x, hid_y, 1.30), base_s=(0.88, 0.88), top_s=(0.66, 0.66), height=1.52, mat_index=idx_pedestal_blanco)
add_solid_box(bm, center=(hid_x, hid_y, 2.12), size=(0.78, 0.78, 0.12), mat_index=idx_pedestal_blanco)
add_solid_box(bm, center=(hid_x, hid_y, 2.22), size=(0.85, 0.85, 0.08), mat_index=idx_cantera)

# 4. Busto de Miguel Hidalgo en bronce dorado (Mirando al norte hacia el Kiosko)
add_solid_box(bm, center=(hid_x, hid_y, 2.32), size=(0.54, 0.42, 0.12), mat_index=idx_bronce_oro)
add_truncated_pyramid(bm, center=(hid_x, hid_y, 2.54), base_s=(0.60, 0.38), top_s=(0.44, 0.28), height=0.32, mat_index=idx_bronce_oro)
add_solid_box(bm, center=(hid_x, hid_y + 0.14, 2.68), size=(0.14, 0.03, 0.06), mat_index=idx_blanco_camisa)
add_solid_cylinder(bm, center=(hid_x, hid_y, 2.74), radius=0.12, height=0.12, segments=16, mat_index=idx_bronce_oro)
add_solid_cylinder(bm, center=(hid_x, hid_y, 2.90), radius=0.16, height=0.26, segments=20, mat_index=idx_bronce_oro)
add_solid_box(bm, center=(hid_x, hid_y + 0.06, 2.98), size=(0.22, 0.14, 0.08), mat_index=idx_bronce_oro)
add_solid_box(bm, center=(hid_x, hid_y + 0.15, 2.94), size=(0.18, 0.04, 0.03), mat_index=idx_bronce_oro)
add_solid_box(bm, center=(hid_x, hid_y + 0.20, 2.90), size=(0.06, 0.08, 0.11), mat_index=idx_bronce_oro)
add_solid_box(bm, center=(hid_x, hid_y + 0.16, 2.80), size=(0.14, 0.06, 0.08), mat_index=idx_bronce_oro)
add_solid_box(bm, center=(hid_x - 0.16, hid_y - 0.04, 2.86), size=(0.08, 0.22, 0.22), mat_index=idx_bronce_oro)
add_solid_box(bm, center=(hid_x + 0.16, hid_y - 0.04, 2.86), size=(0.08, 0.22, 0.22), mat_index=idx_bronce_oro)
add_solid_box(bm, center=(hid_x, hid_y - 0.14, 2.86), size=(0.26, 0.08, 0.22), mat_index=idx_bronce_oro)

# ------------------------------------------------------------------------------
# MONUMENTO 2: ESTATUA DE DON BENITO JUÁREZ (Sector Noreste)
# Orientado hacia la esquina Noreste (Av. Juárez y Ortiz Rubio, rot_z = -45°)
# ------------------------------------------------------------------------------
bj_x, bj_y = 32.0, 23.0
bj_rot = math.radians(135.0) # Apunta hacia la esquina exterior Noreste (+X, +Y)
ca_bj, sa_bj = math.cos(bj_rot), math.sin(bj_rot)

def rot_bj(lx, ly, lz):
    return (lx * ca_bj - ly * sa_bj + bj_x, lx * sa_bj + ly * ca_bj + bj_y, lz)

# 1. Podio amarillo ocre municipal
add_solid_box(bm, center=rot_bj(0.0, 0.0, 0.32), size=(6.80, 5.20, 0.65), rot_z=bj_rot, mat_index=idx_ocre)
add_solid_box(bm, center=rot_bj(-3.25, 0.0, 0.82), size=(0.30, 5.20, 0.36), rot_z=bj_rot, mat_index=idx_ocre)
add_solid_box(bm, center=rot_bj(3.25, 0.0, 0.82), size=(0.30, 5.20, 0.36), rot_z=bj_rot, mat_index=idx_ocre)
add_solid_box(bm, center=rot_bj(0.0, 2.45, 0.82), size=(6.80, 0.30, 0.36), rot_z=bj_rot, mat_index=idx_ocre)

# Escalinata frontal descendiendo hacia la esquina Noreste (4 escalones transitables)
for st in range(4):
    st_z = 0.08 + st * 0.16
    st_w = 4.40
    st_depth = 0.32
    st_ly = -2.60 - (3 - st) * st_depth
    add_solid_box(bm, center=rot_bj(0.0, st_ly, st_z), size=(st_w, st_depth, 0.16), rot_z=bj_rot, mat_index=idx_ocre)

# 2. Pedestal de cantera negra pulida
add_solid_box(bm, center=rot_bj(0.0, -0.20, 1.55), size=(1.65, 1.65, 1.80), rot_z=bj_rot, mat_index=idx_cantera_oscura)
add_solid_box(bm, center=rot_bj(0.0, -0.20, 2.48), size=(1.80, 1.80, 0.10), rot_z=bj_rot, mat_index=idx_cantera_oscura)

# Placa frontal con relieve: "EL RESPETO AL DERECHO AJENO ES LA PAZ"
add_solid_box(bm, center=rot_bj(0.0, -1.03, 1.55), size=(1.45, 0.03, 0.65), rot_z=bj_rot, mat_index=idx_letras_negras)
add_solid_box(bm, center=rot_bj(0.0, -1.05, 1.68), size=(1.25, 0.02, 0.08), rot_z=bj_rot, mat_index=idx_letras_doradas)
add_solid_box(bm, center=rot_bj(0.0, -1.05, 1.52), size=(0.95, 0.02, 0.08), rot_z=bj_rot, mat_index=idx_letras_doradas)
add_solid_box(bm, center=rot_bj(0.0, -1.05, 1.36), size=(0.55, 0.02, 0.08), rot_z=bj_rot, mat_index=idx_letras_doradas)

# 3. Estatua de cuerpo entero de Don Benito Juárez mirando a la esquina Noreste
stat_z = 2.53
stat_ly = -0.20
add_solid_box(bm, center=rot_bj(0.0, stat_ly, stat_z + 0.06), size=(0.95, 0.95, 0.12), rot_z=bj_rot, mat_index=idx_bronce)
# Zapatos solemnes de charol
add_solid_box(bm, center=rot_bj(-0.17, stat_ly - 0.06, stat_z + 0.16), size=(0.18, 0.38, 0.12), rot_z=bj_rot, mat_index=idx_bronce)
add_solid_box(bm, center=rot_bj(0.17, stat_ly - 0.06, stat_z + 0.16), size=(0.18, 0.38, 0.12), rot_z=bj_rot, mat_index=idx_bronce)
add_truncated_pyramid(bm, center=rot_bj(-0.17, stat_ly - 0.22, stat_z + 0.15), base_s=(0.18, 0.08), top_s=(0.12, 0.02), height=0.10, rot_z=bj_rot, mat_index=idx_bronce)
add_truncated_pyramid(bm, center=rot_bj(0.17, stat_ly - 0.22, stat_z + 0.15), base_s=(0.18, 0.08), top_s=(0.12, 0.02), height=0.10, rot_z=bj_rot, mat_index=idx_bronce)
# Pantalón recto
add_solid_cylinder(bm, center=rot_bj(-0.17, stat_ly, stat_z + 0.65), radius=0.12, height=0.82, segments=16, mat_index=idx_bronce)
add_solid_cylinder(bm, center=rot_bj(0.17, stat_ly, stat_z + 0.65), radius=0.12, height=0.82, segments=16, mat_index=idx_bronce)
# Faldones de la levita
add_solid_box(bm, center=rot_bj(-0.24, stat_ly + 0.02, stat_z + 1.25), size=(0.22, 0.36, 0.78), rot_z=bj_rot, mat_index=idx_bronce)
add_solid_box(bm, center=rot_bj(0.24, stat_ly + 0.02, stat_z + 1.25), size=(0.22, 0.36, 0.78), rot_z=bj_rot, mat_index=idx_bronce)
add_solid_box(bm, center=rot_bj(0.0, stat_ly + 0.12, stat_z + 1.25), size=(0.46, 0.16, 0.78), rot_z=bj_rot, mat_index=idx_bronce)
# Torso, chaleco y corbatín
add_solid_box(bm, center=rot_bj(0.0, stat_ly, stat_z + 1.70), size=(0.58, 0.36, 0.55), rot_z=bj_rot, mat_index=idx_bronce)
add_solid_box(bm, center=rot_bj(0.0, stat_ly - 0.17, stat_z + 1.58), size=(0.26, 0.04, 0.38), rot_z=bj_rot, mat_index=idx_cantera_oscura)
for btn_i in range(3):
    add_solid_box(bm, center=rot_bj(0.0, stat_ly - 0.195, stat_z + 1.48 + btn_i * 0.09), size=(0.03, 0.02, 0.03), rot_z=bj_rot, mat_index=idx_letras_doradas)
add_solid_box(bm, center=rot_bj(0.0, stat_ly - 0.17, stat_z + 1.82), size=(0.18, 0.03, 0.12), rot_z=bj_rot, mat_index=idx_blanco_camisa)
add_solid_box(bm, center=rot_bj(0.0, stat_ly - 0.19, stat_z + 1.83), size=(0.14, 0.03, 0.06), rot_z=bj_rot, mat_index=idx_letras_negras)
add_solid_box(bm, center=rot_bj(-0.18, stat_ly - 0.16, stat_z + 1.70), size=(0.12, 0.06, 0.44), rot_z=bj_rot, mat_index=idx_bronce)
add_solid_box(bm, center=rot_bj(0.18, stat_ly - 0.16, stat_z + 1.70), size=(0.12, 0.06, 0.44), rot_z=bj_rot, mat_index=idx_bronce)
# Brazo derecho solemne
add_solid_cylinder(bm, center=rot_bj(-0.34, stat_ly, stat_z + 1.62), radius=0.08, height=0.60, segments=12, mat_index=idx_bronce)
add_solid_box(bm, center=rot_bj(-0.32, stat_ly - 0.06, stat_z + 1.28), size=(0.10, 0.14, 0.14), rot_z=bj_rot, mat_index=idx_bronce)
# Brazo izquierdo sosteniendo la Constitución de 1857
add_solid_cylinder(bm, center=rot_bj(0.34, stat_ly, stat_z + 1.62), radius=0.08, height=0.60, segments=12, mat_index=idx_bronce)
add_solid_box(bm, center=rot_bj(0.32, stat_ly - 0.08, stat_z + 1.34), size=(0.12, 0.28, 0.32), rot_z=bj_rot, mat_index=idx_pedestal_blanco)
add_solid_box(bm, center=rot_bj(0.33, stat_ly - 0.08, stat_z + 1.34), size=(0.14, 0.30, 0.34), rot_z=bj_rot, mat_index=idx_cantera_oscura)
add_solid_box(bm, center=rot_bj(0.30, stat_ly - 0.06, stat_z + 1.26), size=(0.10, 0.14, 0.14), rot_z=bj_rot, mat_index=idx_bronce)
# Cabeza fisonómica juarista
add_solid_cylinder(bm, center=rot_bj(0.0, stat_ly, stat_z + 2.02), radius=0.11, height=0.14, segments=16, mat_index=idx_bronce)
add_solid_cylinder(bm, center=rot_bj(0.0, stat_ly, stat_z + 2.18), radius=0.16, height=0.26, segments=20, mat_index=idx_bronce)
add_solid_box(bm, center=rot_bj(0.0, stat_ly - 0.09, stat_z + 2.27), size=(0.24, 0.14, 0.10), rot_z=bj_rot, mat_index=idx_bronce)
add_solid_box(bm, center=rot_bj(0.0, stat_ly - 0.15, stat_z + 2.23), size=(0.20, 0.05, 0.04), rot_z=bj_rot, mat_index=idx_bronce)
add_solid_box(bm, center=rot_bj(0.0, stat_ly - 0.20, stat_z + 2.18), size=(0.06, 0.09, 0.11), rot_z=bj_rot, mat_index=idx_bronce)
add_solid_box(bm, center=rot_bj(0.0, stat_ly - 0.16, stat_z + 2.09), size=(0.16, 0.08, 0.08), rot_z=bj_rot, mat_index=idx_bronce)
add_solid_box(bm, center=rot_bj(0.0, stat_ly + 0.06, stat_z + 2.26), size=(0.31, 0.22, 0.16), rot_z=bj_rot, mat_index=idx_bronce)
add_solid_box(bm, center=rot_bj(-0.17, stat_ly, stat_z + 2.18), size=(0.04, 0.08, 0.10), rot_z=bj_rot, mat_index=idx_bronce)
add_solid_box(bm, center=rot_bj(0.17, stat_ly, stat_z + 2.18), size=(0.04, 0.08, 0.10), rot_z=bj_rot, mat_index=idx_bronce)

# 4. Caseta CROC tradicional verde detrás del podio
cas_lx, cas_ly = 1.80, 4.00
add_solid_box(bm, center=rot_bj(cas_lx, cas_ly, 1.25), size=(2.20, 1.80, 2.50), rot_z=bj_rot, mat_index=idx_caseta_verde)
add_solid_box(bm, center=rot_bj(cas_lx, cas_ly - 0.91, 1.30), size=(0.80, 0.04, 1.20), rot_z=bj_rot, mat_index=idx_forja)
add_truncated_pyramid(bm, center=rot_bj(cas_lx, cas_ly, 2.80), base_s=(2.60, 2.20), top_s=(2.20, 0.20), height=0.60, rot_z=bj_rot, mat_index=idx_teja_roja)

# ------------------------------------------------------------------------------
# MONUMENTO 3: MONUMENTO A DON LÁZARO CÁRDENAS (Sector Suroeste)
# Orientado hacia la esquina Suroeste (Cárdenas y Libertad, rot_z = 135°)
# ------------------------------------------------------------------------------
lc_x, lc_y = -36.0, -25.0
lc_rot = math.radians(-45.0) # Apunta hacia la esquina exterior Suroeste (-X, -Y)
ca_lc, sa_lc = math.cos(lc_rot), math.sin(lc_rot)

def rot_lc(lx, ly, lz):
    return (lx * ca_lc - ly * sa_lc + lc_x, lx * sa_lc + ly * ca_lc + lc_y, lz)

# 1. Muro blanco tipográfico frontal
add_solid_box(bm, center=rot_lc(0.0, 0.0, 0.70), size=(4.20, 0.40, 1.40), rot_z=lc_rot, mat_index=idx_pedestal_blanco)
add_solid_box(bm, center=rot_lc(0.0, 0.0, 0.08), size=(4.40, 0.50, 0.16), rot_z=lc_rot, mat_index=idx_cantera)

# Tipografía 3D modelada orientada hacia la esquina Suroeste:
cardenas_text = [
    "GRAL. LAZARO CARDENAS",
    "1895  -  1970",
    "MEXICO",
    "TECATE, B.C.  1973"
]
add_3d_text_letters(bm, cardenas_text, rot_lc(0.0, -0.22, 0.0)[0], rot_lc(0.0, -0.22, 0.0)[1],
                    base_z=1.12, rot_z=lc_rot, line_spacing=0.22, char_w=0.09, char_h=0.11, char_d=0.03, mat_idx=idx_letras_negras)

# 2. Pedestal y Busto de Lázaro Cárdenas integrado sobre el centro del muro
add_solid_box(bm, center=rot_lc(0.0, 0.0, 1.70), size=(0.95, 0.60, 0.70), rot_z=lc_rot, mat_index=idx_pedestal_blanco)
add_solid_box(bm, center=rot_lc(0.0, 0.0, 2.08), size=(1.05, 0.70, 0.10), rot_z=lc_rot, mat_index=idx_cantera)

busto_z = 2.13
add_solid_box(bm, center=rot_lc(0.0, 0.0, busto_z + 0.06), size=(0.65, 0.45, 0.12), rot_z=lc_rot, mat_index=idx_bronce)
add_truncated_pyramid(bm, center=rot_lc(0.0, 0.0, busto_z + 0.30), base_s=(0.72, 0.42), top_s=(0.48, 0.30), height=0.36, rot_z=lc_rot, mat_index=idx_bronce)
add_solid_box(bm, center=rot_lc(0.0, -0.18, busto_z + 0.35), size=(0.14, 0.04, 0.14), rot_z=lc_rot, mat_index=idx_blanco_camisa)
add_solid_box(bm, center=rot_lc(0.0, -0.20, busto_z + 0.32), size=(0.06, 0.03, 0.18), rot_z=lc_rot, mat_index=idx_letras_negras)
add_solid_cylinder(bm, center=rot_lc(0.0, 0.0, busto_z + 0.52), radius=0.12, height=0.12, segments=16, mat_index=idx_bronce)
add_solid_cylinder(bm, center=rot_lc(0.0, 0.0, busto_z + 0.70), radius=0.17, height=0.26, segments=20, mat_index=idx_bronce)
add_solid_box(bm, center=rot_lc(0.0, -0.12, busto_z + 0.78), size=(0.24, 0.12, 0.08), rot_z=lc_rot, mat_index=idx_bronce)
add_solid_box(bm, center=rot_lc(0.0, -0.21, busto_z + 0.70), size=(0.07, 0.09, 0.12), rot_z=lc_rot, mat_index=idx_bronce)
add_solid_box(bm, center=rot_lc(0.0, -0.18, busto_z + 0.62), size=(0.16, 0.08, 0.08), rot_z=lc_rot, mat_index=idx_bronce)
add_solid_box(bm, center=rot_lc(0.0, -0.19, busto_z + 0.65), size=(0.12, 0.03, 0.03), rot_z=lc_rot, mat_index=idx_letras_negras)
add_solid_box(bm, center=rot_lc(0.0, 0.06, busto_z + 0.78), size=(0.32, 0.20, 0.16), rot_z=lc_rot, mat_index=idx_bronce)

# 3. Murete curvo frontal amarillo ocre y jardinera semicircular orientada al Suroeste
r_curv = 2.80
n_curv = 24
for i in range(n_curv):
    ang1 = math.pi * (1.0 + i / n_curv)
    ang2 = math.pi * (1.0 + (i + 1) / n_curv)
    lx1 = r_curv * math.cos(ang1)
    ly1 = -0.20 + r_curv * math.sin(ang1)
    lx2 = r_curv * math.cos(ang2)
    ly2 = -0.20 + r_curv * math.sin(ang2)
    p1 = rot_lc(lx1, ly1, 0.22)
    p2 = rot_lc(lx2, ly2, 0.22)
    mx = (p1[0] + p2[0]) * 0.5
    my = (p1[1] + p2[1]) * 0.5
    seg_len = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    seg_ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    add_solid_box(bm, center=(mx, my, 0.22), size=(seg_len * 1.05, 0.28, 0.45), rot_z=seg_ang, mat_index=idx_ocre)

add_solid_cylinder(bm, center=rot_lc(0.0, -1.20, 0.10), radius=2.20, height=0.18, segments=24, mat_index=idx_tierra)

# ------------------------------------------------------------------------------
# MONUMENTO 4: OBELISCO CONMEMORATIVO DE CANTERA (Sector Este)
# ------------------------------------------------------------------------------
ob_x, ob_y = 38.0, -10.0
add_solid_box(bm, center=(ob_x, ob_y, 0.08), size=(4.20, 4.20, 0.16), mat_index=idx_cantera)
add_solid_box(bm, center=(ob_x, ob_y, 0.24), size=(3.40, 3.40, 0.16), mat_index=idx_cantera)
add_solid_box(bm, center=(ob_x, ob_y, 0.40), size=(2.60, 2.60, 0.16), mat_index=idx_cantera)
add_solid_box(bm, center=(ob_x, ob_y, 0.65), size=(1.60, 1.60, 0.35), mat_index=idx_cantera)
add_solid_box(bm, center=(ob_x, ob_y, 0.88), size=(1.40, 1.40, 0.12), mat_index=idx_cantera)
add_truncated_pyramid(bm, center=(ob_x, ob_y, 3.25), base_s=(1.25, 1.25), top_s=(0.46, 0.46), height=4.60, mat_index=idx_cantera)
add_truncated_pyramid(bm, center=(ob_x, ob_y, 5.75), base_s=(0.46, 0.46), top_s=(0.04, 0.04), height=0.40, mat_index=idx_cantera)
add_solid_box(bm, center=(ob_x, ob_y - 0.64, 1.50), size=(0.65, 0.03, 0.48), mat_index=idx_bronce)
add_solid_box(bm, center=(ob_x, ob_y + 0.64, 1.50), size=(0.65, 0.03, 0.48), mat_index=idx_bronce)
add_solid_box(bm, center=(ob_x - 0.64, ob_y, 1.50), size=(0.03, 0.65, 0.48), mat_index=idx_bronce)
add_solid_box(bm, center=(ob_x + 0.64, ob_y, 1.50), size=(0.03, 0.65, 0.48), mat_index=idx_bronce)

# ------------------------------------------------------------------------------
# MONUMENTO 5: CASETITA BLANCA CONMEMORATIVA (Borde del Andador Noroeste)
# Basada en evidencia fotográfica media_1790444944727.jpg
# ------------------------------------------------------------------------------
print("[PARQUE HIDALGO] Construyendo casetita blanca conmemorativa y murete curvo (media_1790444944727.jpg)...")
cas_w_x, cas_w_y = -17.0, 14.5
cas_rot = math.radians(-16.0) # Orientada hacia el andador diagonal Noroeste
ca_cw, sa_cw = math.cos(cas_rot), math.sin(cas_rot)

def rot_cw(lx, ly, lz):
    return (lx * ca_cw - ly * sa_cw + cas_w_x, lx * sa_cw + ly * ca_cw + cas_w_y, lz)

# Casetita blanca de estuco
add_solid_box(bm, center=rot_cw(0.0, 0.0, 1.25), size=(2.40, 1.80, 2.50), rot_z=cas_rot, mat_index=idx_pedestal_blanco)
# Losa de techo con cornisa y pequeño alero
add_solid_box(bm, center=rot_cw(0.0, 0.0, 2.54), size=(2.60, 2.00, 0.12), rot_z=cas_rot, mat_index=idx_pedestal_blanco)
# Friso superior con celosías caladas de ventilación (cuadros oscuros en relieve)
for v_i in range(3):
    add_solid_box(bm, center=rot_cw(-0.65 + v_i*0.65, -0.91, 2.30), size=(0.45, 0.03, 0.18), rot_z=cas_rot, mat_index=idx_forja)
# Marco conmemorativo vertical negro en fachada frontal con placa blanca
add_solid_box(bm, center=rot_cw(0.0, -0.91, 1.35), size=(0.60, 0.03, 0.90), rot_z=cas_rot, mat_index=idx_forja)
add_solid_box(bm, center=rot_cw(0.0, -0.92, 1.35), size=(0.50, 0.02, 0.80), rot_z=cas_rot, mat_index=idx_blanco_camisa)
# Puerta de madera entablerada café rústica en el lateral derecho
add_solid_box(bm, center=rot_cw(1.21, 0.0, 1.05), size=(0.04, 0.85, 1.95), rot_z=cas_rot, mat_index=idx_madera)
# Bote de basura negro adyacente a la puerta (media_1790444944727.jpg)
add_solid_cylinder(bm, center=rot_cw(1.50, -0.65, 0.45), radius=0.30, height=0.90, segments=12, mat_index=idx_forja)

# Murete blanco curvo/escalonado de contención frente a la casetita (media_1790444944727.jpg)
mur_pts = [
    rot_cw(-3.6, -1.8, 0.20),
    rot_cw(-2.4, -1.8, 0.35),
    rot_cw(-1.2, -1.8, 0.50),
    rot_cw(0.0, -1.8, 0.55),
    rot_cw(1.2, -1.8, 0.50),
    rot_cw(2.4, -1.8, 0.35),
    rot_cw(3.6, -1.8, 0.20)
]
for mi in range(len(mur_pts)-1):
    p1 = mur_pts[mi]
    p2 = mur_pts[mi+1]
    seg_m = ((p1[0]+p2[0])*0.5, (p1[1]+p2[1])*0.5, (p1[2]+p2[2])*0.5)
    seg_l = math.hypot(p2[0]-p1[0], p2[1]-p1[1])
    seg_a = math.atan2(p2[1]-p1[1], p2[0]-p1[0])
    seg_h = max(0.40, seg_m[2]*2.0)
    add_solid_box(bm, center=(seg_m[0], seg_m[1], seg_h*0.5), size=(seg_l*1.05, 0.28, seg_h), rot_z=seg_a, mat_index=idx_pedestal_blanco)

# Remate semicircular central decorativo en el murete blanco
add_solid_cylinder(bm, center=rot_cw(0.0, -1.8, 0.95), radius=0.35, height=0.28, segments=16, mat_index=idx_pedestal_blanco)

# ==============================================================================
# 5. ALCORQUES ANULARES ELEVADOS Y ÁRBOLES ACOPLADOS 1:1
# ==============================================================================
print("[PARQUE HIDALGO] Generando alcorques anulares con árboles 1:1 acoplados...")

def add_foliage_sphere(bm, center, radius, mat_index=idx_follaje):
    res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=radius, matrix=Matrix.Translation(center))
    for v in res['verts']:
        dist = 1.0 + 0.08 * math.sin(v.co.x * 3.0) * math.cos(v.co.y * 3.0)
        v.co = Vector(center) + (v.co - Vector(center)) * dist
    faces = set(f for v in res['verts'] for f in v.link_faces)
    for f in faces:
        f.smooth = True
        f.material_index = mat_index
    assign_uvs(list(faces), 1.0)

def add_organic_tree(bm, pos_xy, trunk_h=3.5, trunk_r=0.45, crown_r=4.0, crown_h=5.5):
    tx, ty = pos_xy
    add_solid_cylinder(bm, center=(tx, ty, trunk_h*0.5), radius=trunk_r, height=trunk_h, segments=12, mat_index=idx_corteza)
    add_solid_cylinder(bm, center=(tx, ty, 0.25), radius=trunk_r * 1.35, height=0.50, segments=12, mat_index=idx_corteza)

    for b_i in range(3):
        b_ang = b_i * (2.0 * math.pi / 3.0)
        bx = math.cos(b_ang) * 0.45
        by = math.sin(b_ang) * 0.45
        add_solid_cylinder(bm, center=(tx + bx, ty + by, trunk_h + 0.8), radius=trunk_r*0.45, height=1.8, segments=8, mat_index=idx_corteza)

    cz_base = trunk_h + crown_h * 0.45
    add_foliage_sphere(bm, (tx, ty, cz_base + 0.5), radius=crown_r * 0.85)
    for c_i in range(5):
        c_ang = c_i * (2.0 * math.pi / 5.0)
        clx = tx + math.cos(c_ang) * (crown_r * 0.52)
        cly = ty + math.sin(c_ang) * (crown_r * 0.52)
        clz = cz_base + (c_i % 2) * 0.7 - 0.2
        add_foliage_sphere(bm, (clx, cly, clz), radius=crown_r * 0.65)

def add_tree_with_planter(bm, center_xy, r_ext=1.60, r_int=1.25, height=0.38):
    cx, cy = center_xy
    add_solid_ring(bm, center=(cx, cy, height*0.5), r_ext=r_ext, r_int=r_int, height=height, segments=24, mat_index=idx_ocre, smooth=True)
    add_solid_cylinder(bm, center=(cx, cy, height - 0.06), radius=r_int, height=0.12, segments=20, mat_index=idx_tierra)
    # Acoplamiento estricto 1:1: cada alcorque tiene exactamente un árbol
    add_organic_tree(bm, center_xy, trunk_h=3.4, trunk_r=0.40, crown_r=3.5, crown_h=5.0)

# Lista única de alcorques elevados con árbol acoplado (ubicados en bordes de andadores)
alcorques_specs = [
    # Andador Norte (costados)
    (-3.4, 22.0), (3.4, 22.0), (-3.4, 30.0), (3.4, 30.0),
    # Andador Sur (costados)
    (-3.4, -15.0), (3.4, -15.0), (-3.4, -29.0), (3.4, -29.0),
    # Andador Este (costados)
    (20.0, 3.6), (20.0, -3.6), (32.0, 3.6), (32.0, -5.5),
    # Andador Poniente (costados)
    (-18.0, 3.5), (-18.0, -3.5),
    # Plaza de la Fuente (borde exterior, según panorama real)
    (-24.5, 14.5)
]
for apos in alcorques_specs:
    add_tree_with_planter(bm, apos)

# Árboles monumentales de sombra ÚNICAMENTE dentro de las praderas interiores de césped:
monumental_trees_in_gardens = [
    # Cuadrante Noreste
    (14.0, 14.0), (20.0, 10.0), (12.0, 26.0), (24.0, 16.0),
    # Cuadrante Sureste (despejados del andador diagonal SE que va hacia 34, -24)
    (18.0, -5.5), (26.0, -7.0), (14.0, -23.0), (22.0, -27.0),
    # Cuadrante Suroeste
    (-14.0, -14.0), (-20.0, -10.0), (-20.0, -20.0), (-26.0, -16.0),
    # Cuadrante Noroeste (lejos de la casetita blanca y de la fuente)
    (-12.0, 24.0), (-18.0, 6.0), (-26.0, 6.0)
]
for mt in monumental_trees_in_gardens:
    add_organic_tree(bm, mt, trunk_h=4.2, trunk_r=0.50, crown_r=4.5, crown_h=6.5)

# ==============================================================================
# 6. MOBILIARIO URBANO (BANCAS Y FAROLAS EN COSTADOS, PASO CENTRAL 100% DESPEJADO)
# ==============================================================================
print("[PARQUE HIDALGO] Generando mobiliario urbano (bancas, farolas y mesas)...")

def add_ornamental_bench(bm, pos_xy, angle_rad=0.0):
    px, py = pos_xy
    ca = math.cos(angle_rad)
    sa = math.sin(angle_rad)

    def rot(lx, ly, lz):
        return (lx * ca - ly * sa + px, lx * sa + ly * ca + py, lz)

    for side_x in [-0.90, 0.90]:
        add_solid_box(bm, center=rot(side_x, 0.0, 0.22), size=(0.08, 0.60, 0.44), rot_z=angle_rad, mat_index=idx_forja)
        add_solid_box(bm, center=rot(side_x, -0.24, 0.58), size=(0.06, 0.08, 0.52), rot_z=angle_rad, mat_index=idx_forja)
        add_solid_box(bm, center=rot(side_x, 0.0, 0.48), size=(0.08, 0.52, 0.06), rot_z=angle_rad, mat_index=idx_forja)
        add_solid_cylinder(bm, center=rot(side_x, -0.05, 0.52), radius=0.08, height=0.06, segments=12, mat_index=idx_forja)

    add_solid_box(bm, center=rot(0.0, -0.25, 0.68), size=(1.80, 0.04, 0.38), rot_z=angle_rad, mat_index=idx_forja)
    add_solid_box(bm, center=rot(0.0, -0.25, 0.92), size=(0.32, 0.06, 0.22), rot_z=angle_rad, mat_index=idx_forja)
    add_solid_cylinder(bm, center=rot(0.0, -0.25, 0.96), radius=0.14, height=0.04, segments=16, mat_index=idx_forja)

    for sy, sz in [(-0.16, 0.42), (-0.05, 0.43), (0.07, 0.44), (0.19, 0.44)]:
        add_solid_box(bm, center=rot(0.0, sy, sz), size=(1.76, 0.10, 0.035), rot_z=angle_rad, mat_index=idx_madera)

benches_specs = [
    # Andador Norte (x=0, ancho 4.8m -> bancas en x=±1.95m viendo al centro x=0)
    ((-1.95, 18.0), -math.pi * 0.5), # Oeste viendo al Este (+X)
    ((1.95, 18.0), math.pi * 0.5),   # Este viendo al Oeste (-X)
    ((-1.95, 28.0), -math.pi * 0.5),
    ((1.95, 28.0), math.pi * 0.5),

    # Andador Sur (x=0, ancho 4.8m -> bancas en x=±1.95m viendo al centro x=0)
    ((-1.95, -15.0), -math.pi * 0.5),
    ((1.95, -15.0), math.pi * 0.5),
    ((-1.95, -28.0), -math.pi * 0.5),
    ((1.95, -28.0), math.pi * 0.5),

    # Andador Este (y=0, ancho 5.2m -> bancas en y=±2.10m viendo al centro y=0)
    ((18.0, 2.10), math.pi),  # Norte viendo al Sur (-Y)
    ((18.0, -2.10), 0.0),      # Sur viendo al Norte (+Y)
    ((30.0, 2.10), math.pi),
    ((30.0, -2.10), 0.0),

    # Andador Poniente (y=0, ancho 5.0m -> bancas en y=±2.00m viendo al centro y=0)
    ((-18.0, 2.00), math.pi),
    ((-18.0, -2.00), 0.0),
    ((-30.0, 2.00), math.pi),
    ((-30.0, -2.00), 0.0),

    # Glorieta Central (R=10.5m viendo hacia el interior del Kiosko)
    ((10.5 * math.cos(math.radians(25)), 10.5 * math.sin(math.radians(25))), math.atan2(10.5 * math.cos(math.radians(25)), -10.5 * math.sin(math.radians(25)))),
    ((10.5 * math.cos(math.radians(65)), 10.5 * math.sin(math.radians(65))), math.atan2(10.5 * math.cos(math.radians(65)), -10.5 * math.sin(math.radians(65)))),
    ((10.5 * math.cos(math.radians(115)), 10.5 * math.sin(math.radians(115))), math.atan2(10.5 * math.cos(math.radians(115)), -10.5 * math.sin(math.radians(115)))),
    ((10.5 * math.cos(math.radians(155)), 10.5 * math.sin(math.radians(155))), math.atan2(10.5 * math.cos(math.radians(155)), -10.5 * math.sin(math.radians(155)))),
    ((10.5 * math.cos(math.radians(205)), 10.5 * math.sin(math.radians(205))), math.atan2(10.5 * math.cos(math.radians(205)), -10.5 * math.sin(math.radians(205)))),
    ((10.5 * math.cos(math.radians(245)), 10.5 * math.sin(math.radians(245))), math.atan2(10.5 * math.cos(math.radians(245)), -10.5 * math.sin(math.radians(245)))),
    ((10.5 * math.cos(math.radians(295)), 10.5 * math.sin(math.radians(295))), math.atan2(10.5 * math.cos(math.radians(295)), -10.5 * math.sin(math.radians(295)))),
    ((10.5 * math.cos(math.radians(335)), 10.5 * math.sin(math.radians(335))), math.atan2(10.5 * math.cos(math.radians(335)), -10.5 * math.sin(math.radians(335)))),

    # Dos bancas coloniales frente a la casetita blanca (media_1790444944727.jpg)
    (rot_cw(-1.5, -2.8, 0.0)[:2], cas_rot + math.pi),
    (rot_cw(1.5, -2.8, 0.0)[:2], cas_rot + math.pi)
]
for bp, bang in benches_specs:
    add_ornamental_bench(bm, bp, bang)

def add_triple_colonial_lamp(bm, pos_xy):
    lx, ly = pos_xy
    add_solid_cylinder(bm, center=(lx, ly, 0.25), radius=0.30, height=0.50, segments=8, mat_index=idx_forja)
    add_solid_cylinder(bm, center=(lx, ly, 2.00), radius=0.08, height=3.00, segments=12, mat_index=idx_forja)
    add_solid_cylinder(bm, center=(lx, ly, 3.55), radius=0.16, height=0.20, segments=12, mat_index=idx_forja)

    for arm in range(3):
        ang = arm * (2.0 * math.pi / 3.0)
        ax = math.cos(ang) * 0.65
        ay = math.sin(ang) * 0.65
        add_solid_box(bm, center=(lx + ax*0.5, ly + ay*0.5, 3.65), size=(0.06, 0.06, 0.24), mat_index=idx_forja)
        fx, fy = lx + ax, ly + ay
        add_solid_cylinder(bm, center=(fx, fy, 3.82), radius=0.22, height=0.36, segments=6, mat_index=idx_forja)
        add_truncated_pyramid(bm, center=(fx, fy, 4.08), base_s=(0.36, 0.36), top_s=(0.06, 0.06), height=0.26, mat_index=idx_forja)

# Farolas en los costados de los andadores (paso central 100% expedito y transitable)
lamp_positions = [
    # Esquinas de chaflán de la glorieta central
    (-9.5, 9.5), (9.5, 9.5), (-9.5, -9.5), (9.5, -9.5),
    # Andador Norte (costados)
    (-2.15, 23.0), (2.15, 31.0),
    # Andador Sur (costados)
    (-2.15, -16.0), (2.15, -31.0),
    # Andador Este (costados)
    (22.0, 2.30), (32.0, -2.30),
    # Andador Poniente (costados)
    (-19.0, 2.20), (-29.0, -2.20)
]
for lp in lamp_positions:
    add_triple_colonial_lamp(bm, lp)

# Mesas de ajedrez / picnic de concreto ÚNICAMENTE en la explanada Este (media_1790414528108.jpg)
def add_chess_table(bm, pos_xy):
    tx, ty = pos_xy
    add_solid_cylinder(bm, center=(tx, ty, 0.38), radius=0.24, height=0.76, segments=12, mat_index=idx_cantera)
    add_solid_box(bm, center=(tx, ty, 0.78), size=(1.10, 1.10, 0.08), mat_index=idx_cantera)
    add_solid_box(bm, center=(tx, ty, 0.825), size=(0.55, 0.55, 0.01), mat_index=idx_letras_negras)
    for bx, by in [(-0.85, 0), (0.85, 0)]:
        add_solid_box(bm, center=(tx + bx, ty + by, 0.22), size=(0.32, 0.90, 0.44), mat_index=idx_cantera)
    for bx, by in [(0, -0.85), (0, 0.85)]:
        add_solid_box(bm, center=(tx + bx, ty + by, 0.22), size=(0.90, 0.32, 0.44), mat_index=idx_cantera)

# Mesas de ajedrez / picnic de concreto en la explanada Este (media_1790414528108.jpg)
for cp in [(44.0, 4.5), (44.0, 8.0), (48.0, 4.5), (48.0, 8.0)]:
    add_chess_table(bm, cp)

# Botes de basura de forja cilíndricos
for tp in [(-2.8, 15.0), (2.8, 15.0), (-2.8, -17.0), (2.8, -17.0), (15.0, 2.8), (15.0, -2.8), (-15.0, 2.8), (-15.0, -2.8)]:
    add_solid_cylinder(bm, center=(tp[0], tp[1], 0.42), radius=0.22, height=0.85, segments=12, mat_index=idx_forja)

# Tambos azules de basura de 200L característicos de 2009 (media_1790414493637.jpg)
def add_blue_trash_drum(bm, pos_xy):
    tx, ty = pos_xy
    add_solid_cylinder(bm, center=(tx, ty, 0.46), radius=0.30, height=0.92, segments=18, mat_index=idx_azul_tambo)
    add_solid_ring(bm, center=(tx, ty, 0.46), r_ext=0.315, r_int=0.295, height=0.04, segments=18, mat_index=idx_azul_tambo)
    add_solid_ring(bm, center=(tx, ty, 0.86), r_ext=0.315, r_int=0.295, height=0.04, segments=18, mat_index=idx_azul_tambo)
    add_solid_ring(bm, center=(tx, ty, 0.08), r_ext=0.315, r_int=0.295, height=0.04, segments=18, mat_index=idx_azul_tambo)

blue_drum_positions = [
    (-10.0, 12.0), (10.0, 12.0), (-10.0, -12.0), (10.0, -12.0),
    (36.0, 3.0), (-38.0, 3.0)
]
for bdp in blue_drum_positions:
    add_blue_trash_drum(bm, bdp)


# ==============================================================================
# 8. FINALIZACIÓN DE MALLA Y EXPORTACIÓN GLTF
# ==============================================================================
print("[PARQUE HIDALGO] Calculando normales y finalizando BMesh...")
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(mesh_parque)
bm.free()
mesh_parque.update()

for p in mesh_parque.polygons:
    p.use_smooth = True

print(f"[PARQUE HIDALGO] Exportando archivo GLB a {GLB_OUT_PATH}...")
bpy.ops.object.select_all(action='DESELECT')
obj_parque.select_set(True)
bpy.context.view_layer.objects.active = obj_parque

bpy.ops.export_scene.gltf(
    filepath=GLB_OUT_PATH,
    export_format='GLB',
    use_selection=True,
    export_apply=True,
    export_yup=True
)

bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT_PATH)
print(f"[PARQUE HIDALGO] Archivo .blend guardado en {BLEND_OUT_PATH}")

# ==============================================================================
# 9. GENERACIÓN DE ESCENA GODOT 4 (.TSCN) CON COLISIONES ANALÍTICAS
# Sincronización canónica: Z_godot = -Y_blender
# ==============================================================================
print(f"[PARQUE HIDALGO] Escribiendo escena Godot con colisiones analíticas en {TSCN_OUT_PATH}...")

tscn_content = f"""[gd_scene load_steps=13 format=3 uid="uid://b8parquehidalgo2009"]

[ext_resource type="PackedScene" path="res://assets/parque_miguel_hidalgo.glb" id="1_mesh"]

[sub_resource type="BoxShape3D" id="Shape_Plataforma_General"]
size = Vector3({park_w:.1f}, 1.5, {park_d:.1f})

[sub_resource type="BoxShape3D" id="Shape_Andador_Norte"]
size = Vector3(5.0, 0.4, 26.0)

[sub_resource type="BoxShape3D" id="Shape_Andador_Sur"]
size = Vector3(5.0, 0.4, 27.0)

[sub_resource type="BoxShape3D" id="Shape_Andador_Este"]
size = Vector3(46.0, 0.4, 5.5)

[sub_resource type="BoxShape3D" id="Shape_Andador_Oeste"]
size = Vector3(32.0, 0.4, 5.2)

[sub_resource type="BoxShape3D" id="Shape_Podio_Juarez"]
size = Vector3(7.0, 0.7, 5.5)

[sub_resource type="BoxShape3D" id="Shape_Pedestal_Juarez"]
size = Vector3(1.8, 2.0, 1.8)

[sub_resource type="CylinderShape3D" id="Shape_Medallon_Hidalgo"]
height = 0.2
radius = 3.4

[sub_resource type="BoxShape3D" id="Shape_Pedestal_Hidalgo"]
size = Vector3(1.4, 2.2, 1.4)

[sub_resource type="BoxShape3D" id="Shape_Obelisco_Base"]
size = Vector3(4.4, 0.6, 4.4)

[sub_resource type="BoxShape3D" id="Shape_Obelisco_Fuste"]
size = Vector3(1.4, 6.0, 1.4)

[sub_resource type="BoxShape3D" id="Shape_Muro_Cardenas"]
size = Vector3(4.4, 1.5, 0.6)

[sub_resource type="BoxShape3D" id="Shape_Caseta_Blanca"]
size = Vector3(2.6, 2.6, 2.0)

[node name="ParqueMiguelHidalgo" type="Node3D"]

[node name="VisualMesh" parent="." instance=ExtResource("1_mesh")]

[node name="StaticBody3D" type="StaticBody3D" parent="."]
collision_layer = 1
collision_mask = 0

# 1. Plataforma basal enterrada transitable
[node name="Col_Plataforma" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {park_cx:.2f}, -0.75, {-park_cy:.2f})
shape = SubResource("Shape_Plataforma_General")

# 2. Andadores principales transitables
[node name="Col_Andador_N" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.0, 0.2, -25.0)
shape = SubResource("Shape_Andador_Norte")

[node name="Col_Andador_S" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.0, 0.2, 25.5)
shape = SubResource("Shape_Andador_Sur")

[node name="Col_Andador_E" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 35.0, 0.2, 0.0)
shape = SubResource("Shape_Andador_Este")

[node name="Col_Andador_W" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -28.0, 0.2, 0.0)
shape = SubResource("Shape_Andador_Oeste")

# 3. Colisiones del Monumento a Benito Juárez (Noreste)
[node name="Col_Podio_Juarez" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(-0.707107, 0, -0.707107, 0, 1, 0, 0.707107, 0, -0.707107, {bj_x:.1f}, 0.35, {-bj_y:.1f})
shape = SubResource("Shape_Podio_Juarez")

[node name="Col_Pedestal_Juarez" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(-0.707107, 0, -0.707107, 0, 1, 0, 0.707107, 0, -0.707107, {bj_x:.1f}, 1.65, {-bj_y:.1f})
shape = SubResource("Shape_Pedestal_Juarez")

# 4. Colisiones del Monumento a Miguel Hidalgo (Sur)
[node name="Col_Medallon_Hidalgo" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {hid_x:.1f}, 0.1, {-hid_y:.1f})
shape = SubResource("Shape_Medallon_Hidalgo")

[node name="Col_Pedestal_Hidalgo" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {hid_x:.1f}, 1.2, {-hid_y:.1f})
shape = SubResource("Shape_Pedestal_Hidalgo")

# 5. Colisiones del Obelisco Conmemorativo (Este)
[node name="Col_Obelisco_Base" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {ob_x:.1f}, 0.3, {-ob_y:.1f})
shape = SubResource("Shape_Obelisco_Base")

[node name="Col_Obelisco_Fuste" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {ob_x:.1f}, 3.2, {-ob_y:.1f})
shape = SubResource("Shape_Obelisco_Fuste")

# 6. Colisiones del Monumento a Lázaro Cárdenas (Suroeste)
[node name="Col_Muro_Cardenas" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(0.707107, 0, 0.707107, 0, 1, 0, -0.707107, 0, 0.707107, {lc_x:.1f}, 0.75, {-lc_y:.1f})
shape = SubResource("Shape_Muro_Cardenas")

# 7. Colisiones de la Casetita Blanca Conmemorativa (Noroeste)
[node name="Col_Caseta_Blanca" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(0.961262, 0, -0.275637, 0, 1, 0, 0.275637, 0, 0.961262, {cas_w_x:.1f}, 1.3, {-cas_w_y:.1f})
shape = SubResource("Shape_Caseta_Blanca")
"""

with open(TSCN_OUT_PATH, "w", encoding="utf-8") as f:
    f.write(tscn_content)

# ==============================================================================
# 10. BATERÍA DE 8 CÁMARAS CON LOOK_AT FRONTAL Y RENDERIZADO CYCLES
# ==============================================================================
print("[PARQUE HIDALGO] Configurando iluminación Cycles y 8 cámaras frontales...")

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 64
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

light_data = bpy.data.lights.new(name="Sol_Tecate", type='SUN')
light_data.energy = 5.0
light_data.angle = math.radians(1.5)
light_obj = bpy.data.objects.new("Sol_Tecate", light_data)
scene.collection.objects.link(light_obj)
light_obj.rotation_euler = Euler((math.radians(52.0), math.radians(18.0), math.radians(-42.0)), 'XYZ')

world = bpy.data.worlds.new("Cielo_Tecate")
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs['Color'].default_value = (0.70, 0.82, 0.96, 1.0)
    bg_node.inputs['Strength'].default_value = 1.3
scene.world = world

def setup_camera(name, loc, target, lens=35.0):
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = lens
    cam_obj = bpy.data.objects.new(name, cam_data)
    scene.collection.objects.link(cam_obj)
    cam_obj.location = loc

    dir_vec = Vector(target) - Vector(loc)
    rot_quat = dir_vec.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()
    return cam_obj

cameras_specs = [
    {
        "name": "Cam_01_Cenital_Top",
        "loc": (park_cx, park_cy, 110.0),
        "target": (park_cx, park_cy, 0.0),
        "lens": 28.0,
        "filename": "parque_01_cenital_top.png"
    },
    {
        "name": "Cam_02_Acceso_Norte_Juarez",
        "loc": (0.0, 42.0, 2.5),
        "target": (0.0, 10.0, 1.5),
        "lens": 28.0,
        "filename": "parque_02_acceso_norte_juarez.png"
    },
    {
        "name": "Cam_03_Busto_Hidalgo_Sur",
        "loc": (0.0, -28.0, 1.8),
        "target": (hid_x, hid_y, 2.2),
        "lens": 32.0,
        "filename": "parque_03_busto_hidalgo_sur.png"
    },
    {
        # Vista frontal a Juárez: cámara colocada hacia la esquina Noreste mirando de frente a la estatua
        "name": "Cam_04_Monumento_Juarez_NE",
        "loc": (bj_x + 5.8, bj_y + 5.8, 2.2),
        "target": (bj_x, bj_y, 3.0),
        "lens": 32.0,
        "filename": "parque_04_monumento_juarez_ne.png"
    },
    {
        # Vista frontal a Cárdenas: cámara colocada hacia la esquina Suroeste mirando de frente al muro y busto
        "name": "Cam_05_Monumento_Cardenas_SO",
        "loc": (lc_x - 5.5, lc_y - 5.5, 1.8),
        "target": (lc_x, lc_y, 1.6),
        "lens": 32.0,
        "filename": "parque_05_monumento_cardenas_so.png"
    },
    {
        "name": "Cam_06_Obelisco_Cantera_E",
        "loc": (46.0, -10.0, 2.8),
        "target": (ob_x, ob_y, 3.0),
        "lens": 32.0,
        "filename": "parque_06_obelisco_cantera_e.png"
    },
    {
        # Vista peatonal sobre el andador mostrando las bancas y farolas en los costados
        "name": "Cam_07_Peatonal_Andador_Bancas",
        "loc": (0.80, 33.0, 1.65),
        "target": (0.0, 10.0, 1.2),
        "lens": 30.0,
        "filename": "parque_07_peatonal_andador_bancas.png"
    },
    {
        # Vista hacia la Casetita Blanca en el borde del andador Noroeste (media_1790444944727.jpg)
        "name": "Cam_08_Casetita_Blanca_NW",
        "loc": (-19.2, 8.0, 2.1),
        "target": (-17.0, 14.5, 1.35),
        "lens": 28.0,
        "filename": "parque_08_casetita_blanca_nw.png"
    }
]

for cam_info in cameras_specs:
    cam_obj = setup_camera(cam_info["name"], cam_info["loc"], cam_info["target"], cam_info["lens"])
    scene.camera = cam_obj
    render_out = os.path.join(RENDERS_DIR, cam_info["filename"])
    scene.render.filepath = render_out

    print(f"[PARQUE HIDALGO] Renderizando vista '{cam_info['name']}' -> {cam_info['filename']}...")
    bpy.ops.render.render(write_still=True)

print("[PARQUE HIDALGO] ¡Generación procedural fotorrealista y validación cerradas con éxito!")

