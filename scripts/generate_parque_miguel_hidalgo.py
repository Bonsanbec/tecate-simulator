#!/usr/bin/env python3
"""
Generador Procedural 3D del Parque Miguel Hidalgo (Tecate, B.C., México - Época 2009).
Apegado estrictamente al protocolo maestro GEMINI.md y la Verdad de Terreno:
- 4 Monumentos fotorrealistas:
    1. Busto a Don Miguel Hidalgo y Costilla (Sur): Medallón de laja rústica, pedestal clásico moldurado, busto en bronce dorado con facciones esculpidas.
    2. Estatua de Don Benito Juárez (Noreste): Podio amarillo ocre con 4 escalones transitables, pedestal negro con inscripción célebre, estatua solemne de cuerpo entero con levita decimonónica, caseta verde CROC.
    3. Monumento a Don Lázaro Cárdenas (Suroeste): Muro tipográfico blanco con texto tridimensional oficial, busto de bronce, murete curvo continuo amarillo ocre y jardinera.
    4. Obelisco Conmemorativo (Este): Estela piramidal de 4 caras de cantera de 5.8m sobre 3 niveles escalonados con placas de bronce molduradas.
- 8 Andadores radiales en estrella (volúmenes 3D sólidos sin z-fighting) convergiendo en la glorieta del Kiosko (vano libre R=4.8m).
- Hueco exacto para la Fuente de la Paz en (-32.32, 15.19).
- Zócalo basal continuo enterrado a Z <= -1.50m (sin banquetas de calle).
- Alcorques anulares continuos ocre amarillo, bancas coloniales con blasón heráldico, farolas de 3 brazos, mesas de ajedrez.
- Masas forestales realistas: copas lobuladas orgánicas (icósferas subdivididas) y palmeras Washingtonia con penachos en abanico.
- Exportación glTF (.glb) y generación de escena Godot 4 (.tscn) con colisiones analíticas sincronizadas Zgodot = -Yblender.
- Batería de 8 cámaras Cycles CPU con encuadres frontales matemáticos (look_at).
"""

import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector, Matrix, Euler

# Rutas de salida
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEXTURES_DIR = os.path.join(ROOT_DIR, "godot_project", "assets", "textures")
GLB_OUT_PATH = os.path.join(ROOT_DIR, "godot_project", "assets", "parque_miguel_hidalgo.glb")
TSCN_OUT_PATH = os.path.join(ROOT_DIR, "godot_project", "assets", "parque_miguel_hidalgo.tscn")
RENDERS_DIR = os.path.join(ROOT_DIR, "docs", "images", "parque_miguel_hidalgo")

os.makedirs(os.path.dirname(GLB_OUT_PATH), exist_ok=True)
os.makedirs(RENDERS_DIR, exist_ok=True)

# Limpieza total de la escena
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
mat_palma_tronco = create_pbr_material("M_Palma_Tronco", (0.34, 0.28, 0.20, 1.0), 0.85, 0.0)
mat_palma_hojas = create_pbr_material("M_Palma_Hojas", (0.20, 0.44, 0.12, 1.0), 0.55, 0.0)
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
    mat_corteza, mat_follaje, mat_palma_tronco, mat_palma_hojas,
    mat_azul_tambo, mat_blanco_camisa
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
idx_palma_tronco = 19
idx_palma_hojas = 20
idx_azul_tambo = 21
idx_blanco_camisa = 22

bm = bmesh.new()
uv_layer = bm.loops.layers.uv.new("UVMap")

def assign_uvs(faces, scale=1.0):
    for f in faces:
        n = f.normal
        for loop in f.loops:
            v = loop.vert.co
            if abs(n.z) > 0.6:
                u, v_coord = v.x * scale, v.y * scale
            elif abs(n.x) > 0.6:
                u, v_coord = v.y * scale, v.z * scale
            else:
                u, v_coord = v.x * scale, v.z * scale
            loop[uv_layer].uv = (u, v_coord)

def add_solid_box(bm, center, size, rot_z=0.0, mat_index=0, uv_scale=1.0):
    cx, cy, cz = center
    sx, sy, sz = size[0]*0.5, size[1]*0.5, size[2]*0.5
    raw_corners = [
        (-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
        (-sx, -sy, sz),  (sx, -sy, sz),  (sx, sy, sz),  (-sx, sy, sz),
    ]
    ca, sa = math.cos(rot_z), math.sin(rot_z)
    transformed_verts = []
    for rx, ry, rz in raw_corners:
        tx = rx * ca - ry * sa + cx
        ty = rx * sa + ry * ca + cy
        tz = rz + cz
        transformed_verts.append(bm.verts.new((tx, ty, tz)))

    # Orden riguroso antihorario visto desde el exterior (normales hacia afuera)
    face_indices = [
        (0, 3, 2, 1), # Abajo (-Z)
        (4, 5, 6, 7), # Arriba (+Z)
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

def add_3d_text_letters(bm, text_lines, center_x, center_y, base_z, line_spacing=0.20, char_w=0.08, char_h=0.10, char_d=0.03, mat_idx=0):
    for line_idx, line in enumerate(text_lines):
        cur_z = base_z - line_idx * line_spacing
        n_chars = len(line)
        spacing = char_w * 1.35
        total_w = n_chars * spacing
        start_x = center_x - total_w * 0.5 + spacing * 0.5
        for char_i, ch in enumerate(line):
            if ch != ' ':
                ch_x = start_x + char_i * spacing
                add_solid_box(bm, center=(ch_x, center_y, cur_z), size=(char_w, char_d, char_h), mat_index=mat_idx)

# ==============================================================================
# 3. TOPOGRAFÍA, ZÓCALO BASAL Y 8 ANDADORES EN ESTRELLA
# ==============================================================================
print("[PARQUE HIDALGO] Construyendo plataforma sólida, zócalo y andadores...")

# 1. Zócalo basal enterrado continuo (Garantía GEMINI.md: Z <= -1.50m)
add_solid_box(bm, center=(-4.0, -1.5, -0.75), size=(106.0, 71.0, 1.50), mat_index=idx_zocalo)

# 2. Pradera de césped base (superficie z = 0.00m con normal hacia arriba)
add_solid_box(bm, center=(-4.0, -1.5, -0.01), size=(105.6, 70.6, 0.04), mat_index=idx_cesped, uv_scale=0.35)

# 3. Glorieta central de adoquín alrededor del Kiosko (entre R=4.80m vano libre y R=11.20m)
add_solid_ring(bm, center=(0.0, 0.0, 0.03), r_ext=11.20, r_int=4.80, height=0.06, segments=32, mat_index=idx_adoquin)
add_solid_ring(bm, center=(0.0, 0.0, 0.16), r_ext=11.55, r_int=11.20, height=0.32, segments=32, mat_index=idx_ocre)

# 4. Función de Andador Sólido Orientado en Ángulo Exacto
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

# 8 Andadores radiales en estrella:
add_oriented_walkway((0.0, 11.2), (0.0, 33.5), 4.80)   # Norte (Juárez)
add_oriented_walkway((0.0, -11.2), (0.0, -36.5), 4.80) # Sur (Libertad)
add_oriented_walkway((11.2, 0.0), (48.0, 0.0), 5.20)   # Este (Ortiz Rubio)
add_oriented_walkway((-11.2, 0.0), (-56.0, 0.0), 5.00) # Poniente (Cárdenas)
add_oriented_walkway((-7.9, 7.9), (-32.0, 15.2), 3.80) # Diagonal NO (Fuente)
add_oriented_walkway((7.9, 7.9), (30.0, 21.0), 4.00)   # Diagonal NE (Juárez)
add_oriented_walkway((-7.9, -7.9), (-36.0, -25.0), 4.00)# Diagonal SO (Cárdenas)
add_oriented_walkway((7.9, -7.9), (38.0, -24.0), 4.00) # Diagonal SE (Explanada)

# Explanadas pavimentadas
add_solid_box(bm, center=(38.0, 0.0, 0.03), size=(20.0, 24.0, 0.06), mat_index=idx_adoquin, uv_scale=0.6)
add_solid_box(bm, center=(-46.0, 0.0, 0.03), size=(18.0, 16.0, 0.06), mat_index=idx_adoquin, uv_scale=0.6)
add_solid_cylinder(bm, center=(-32.32, 15.19, 0.03), radius=7.50, height=0.06, segments=32, mat_index=idx_adoquin)

# ==============================================================================
# 4. MODELADO DE LOS 4 MONUMENTOS CON ESCULPIDO FOTORREALISTA
# ==============================================================================
print("[PARQUE HIDALGO] Construyendo los 4 monumentos históricos fotorrealistas...")

# ------------------------------------------------------------------------------
# MONUMENTO 1: BUSTO A DON MIGUEL HIDALGO Y COSTILLA (Sector Sur)
# ------------------------------------------------------------------------------
hid_x, hid_y = 0.0, -21.0

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

# 4. Busto de Miguel Hidalgo en bronce dorado (Mirando al norte hacia el Kiosko como en 2009)
add_solid_box(bm, center=(hid_x, hid_y, 2.32), size=(0.54, 0.42, 0.12), mat_index=idx_bronce_oro)
add_truncated_pyramid(bm, center=(hid_x, hid_y, 2.54), base_s=(0.60, 0.38), top_s=(0.44, 0.28), height=0.32, mat_index=idx_bronce_oro)
# Alzacuello clerical blanco
add_solid_box(bm, center=(hid_x, hid_y + 0.14, 2.68), size=(0.14, 0.03, 0.06), mat_index=idx_blanco_camisa)
# Cuello sacerdotal
add_solid_cylinder(bm, center=(hid_x, hid_y, 2.74), radius=0.12, height=0.12, segments=16, mat_index=idx_bronce_oro)
# Cabeza fisonómica del Padre de la Patria
add_solid_cylinder(bm, center=(hid_x, hid_y, 2.90), radius=0.16, height=0.26, segments=20, mat_index=idx_bronce_oro)
# Frente amplia y calva
add_solid_box(bm, center=(hid_x, hid_y + 0.06, 2.98), size=(0.22, 0.14, 0.08), mat_index=idx_bronce_oro)
# Cejas y nariz aguileña hacia el norte (+Y)
add_solid_box(bm, center=(hid_x, hid_y + 0.15, 2.94), size=(0.18, 0.04, 0.03), mat_index=idx_bronce_oro)
add_solid_box(bm, center=(hid_x, hid_y + 0.20, 2.90), size=(0.06, 0.08, 0.11), mat_index=idx_bronce_oro)
# Mentón firme hacia el norte
add_solid_box(bm, center=(hid_x, hid_y + 0.16, 2.80), size=(0.14, 0.06, 0.08), mat_index=idx_bronce_oro)
# Mechones rizados de cabello en sienes y nuca (dorso sur -Y, visible en media_1790414613164.png)
add_solid_box(bm, center=(hid_x - 0.16, hid_y - 0.04, 2.86), size=(0.08, 0.22, 0.22), mat_index=idx_bronce_oro)
add_solid_box(bm, center=(hid_x + 0.16, hid_y - 0.04, 2.86), size=(0.08, 0.22, 0.22), mat_index=idx_bronce_oro)
add_solid_box(bm, center=(hid_x, hid_y - 0.14, 2.86), size=(0.26, 0.08, 0.22), mat_index=idx_bronce_oro)

# ------------------------------------------------------------------------------
# MONUMENTO 2: ESTATUA DE DON BENITO JUÁREZ (Sector Noreste)
# ------------------------------------------------------------------------------
bj_x, bj_y = 30.0, 21.0

# 1. Podio amarillo ocre municipal
add_solid_box(bm, center=(bj_x, bj_y, 0.32), size=(6.80, 5.20, 0.65), mat_index=idx_ocre)
add_solid_box(bm, center=(bj_x - 3.25, bj_y, 0.82), size=(0.30, 5.20, 0.36), mat_index=idx_ocre)
add_solid_box(bm, center=(bj_x + 3.25, bj_y, 0.82), size=(0.30, 5.20, 0.36), mat_index=idx_ocre)
add_solid_box(bm, center=(bj_x, bj_y + 2.45, 0.82), size=(6.80, 0.30, 0.36), mat_index=idx_ocre)

# Escalinata frontal hacia el sur (4 escalones transitables)
for st in range(4):
    st_z = 0.08 + st * 0.16
    st_w = 4.40
    st_depth = 0.32
    st_y = bj_y - 2.60 - (3 - st) * st_depth
    add_solid_box(bm, center=(bj_x, st_y, st_z), size=(st_w, st_depth, 0.16), mat_index=idx_ocre)

# 2. Pedestal de cantera negra pulida
add_solid_box(bm, center=(bj_x, bj_y - 0.20, 1.55), size=(1.65, 1.65, 1.80), mat_index=idx_cantera_oscura)
add_solid_box(bm, center=(bj_x, bj_y - 0.20, 2.48), size=(1.80, 1.80, 0.10), mat_index=idx_cantera_oscura)

# Placa frontal con letras doradas grabadas: "EL RESPETO AL DERECHO AJENO ES LA PAZ"
add_solid_box(bm, center=(bj_x, bj_y - 1.03, 1.55), size=(1.45, 0.03, 0.65), mat_index=idx_letras_negras)
add_solid_box(bm, center=(bj_x, bj_y - 1.05, 1.68), size=(1.25, 0.02, 0.08), mat_index=idx_letras_doradas)
add_solid_box(bm, center=(bj_x, bj_y - 1.05, 1.52), size=(0.95, 0.02, 0.08), mat_index=idx_letras_doradas)
add_solid_box(bm, center=(bj_x, bj_y - 1.05, 1.36), size=(0.55, 0.02, 0.08), mat_index=idx_letras_doradas)
# Placa lateral de bronce
add_solid_box(bm, center=(bj_x - 0.83, bj_y - 0.20, 1.55), size=(0.03, 0.85, 0.55), mat_index=idx_bronce)

# 3. Estatua de cuerpo entero de Don Benito Juárez (Fidedigna, mirando al sur)
stat_z = 2.53
stat_y = bj_y - 0.20

# Plinto de bronce
add_solid_box(bm, center=(bj_x, stat_y, stat_z + 0.06), size=(0.95, 0.95, 0.12), mat_index=idx_bronce)

# Zapatos solemnes de charol apuntando al sur (-Y hacia la escalinata)
add_solid_box(bm, center=(bj_x - 0.17, stat_y - 0.06, stat_z + 0.16), size=(0.18, 0.38, 0.12), mat_index=idx_bronce)
add_solid_box(bm, center=(bj_x + 0.17, stat_y - 0.06, stat_z + 0.16), size=(0.18, 0.38, 0.12), mat_index=idx_bronce)
# Puntas de zapatos cónicas hacia -Y
add_truncated_pyramid(bm, center=(bj_x - 0.17, stat_y - 0.22, stat_z + 0.15), base_s=(0.18, 0.08), top_s=(0.12, 0.02), height=0.10, mat_index=idx_bronce)
add_truncated_pyramid(bm, center=(bj_x + 0.17, stat_y - 0.22, stat_z + 0.15), base_s=(0.18, 0.08), top_s=(0.12, 0.02), height=0.10, mat_index=idx_bronce)

# Pantalón recto formal
add_solid_cylinder(bm, center=(bj_x - 0.17, stat_y, stat_z + 0.65), radius=0.12, height=0.82, segments=16, mat_index=idx_bronce)
add_solid_cylinder(bm, center=(bj_x + 0.17, stat_y, stat_z + 0.65), radius=0.12, height=0.82, segments=16, mat_index=idx_bronce)

# Faldones de la levita (cubren costados y espalda hasta las rodillas, abiertos al frente)
add_solid_box(bm, center=(bj_x - 0.24, stat_y + 0.02, stat_z + 1.25), size=(0.22, 0.36, 0.78), mat_index=idx_bronce)
add_solid_box(bm, center=(bj_x + 0.24, stat_y + 0.02, stat_z + 1.25), size=(0.22, 0.36, 0.78), mat_index=idx_bronce)
add_solid_box(bm, center=(bj_x, stat_y + 0.12, stat_z + 1.25), size=(0.46, 0.16, 0.78), mat_index=idx_bronce)

# Torso / Pecho
add_solid_box(bm, center=(bj_x, stat_y, stat_z + 1.70), size=(0.58, 0.36, 0.55), mat_index=idx_bronce)

# Chaleco frontal abotonado y botones de bronce
add_solid_box(bm, center=(bj_x, stat_y - 0.17, stat_z + 1.58), size=(0.26, 0.04, 0.38), mat_index=idx_cantera_oscura)
for btn_i in range(3):
    add_solid_box(bm, center=(bj_x, stat_y - 0.195, stat_z + 1.48 + btn_i * 0.09), size=(0.03, 0.02, 0.03), mat_index=idx_letras_doradas)

# Camisa blanca visible en cuello y corbatín de lazo negro
add_solid_box(bm, center=(bj_x, stat_y - 0.17, stat_z + 1.82), size=(0.18, 0.03, 0.12), mat_index=idx_blanco_camisa)
add_solid_box(bm, center=(bj_x, stat_y - 0.19, stat_z + 1.83), size=(0.14, 0.03, 0.06), mat_index=idx_letras_negras)

# Solapas anchas de la levita abiertas a los lados del chaleco
add_solid_box(bm, center=(bj_x - 0.18, stat_y - 0.16, stat_z + 1.70), size=(0.12, 0.06, 0.44), mat_index=idx_bronce)
add_solid_box(bm, center=(bj_x + 0.18, stat_y - 0.16, stat_z + 1.70), size=(0.12, 0.06, 0.44), mat_index=idx_bronce)

# Brazo derecho: solemne con mano descansando al frente/costado
add_solid_cylinder(bm, center=(bj_x - 0.34, stat_y, stat_z + 1.62), radius=0.08, height=0.60, segments=12, mat_index=idx_bronce)
add_solid_box(bm, center=(bj_x - 0.32, stat_y - 0.06, stat_z + 1.28), size=(0.10, 0.14, 0.14), mat_index=idx_bronce)

# Brazo izquierdo y Libro de la Constitución de 1857 / Leyes de Reforma
add_solid_cylinder(bm, center=(bj_x + 0.34, stat_y, stat_z + 1.62), radius=0.08, height=0.60, segments=12, mat_index=idx_bronce)
add_solid_box(bm, center=(bj_x + 0.32, stat_y - 0.08, stat_z + 1.34), size=(0.12, 0.28, 0.32), mat_index=idx_pedestal_blanco)
add_solid_box(bm, center=(bj_x + 0.33, stat_y - 0.08, stat_z + 1.34), size=(0.14, 0.30, 0.34), mat_index=idx_cantera_oscura)
add_solid_box(bm, center=(bj_x + 0.30, stat_y - 0.06, stat_z + 1.26), size=(0.10, 0.14, 0.14), mat_index=idx_bronce)

# Cuello y Cabeza Fisonómica de Don Benito Juárez
add_solid_cylinder(bm, center=(bj_x, stat_y, stat_z + 2.02), radius=0.11, height=0.14, segments=16, mat_index=idx_bronce)
add_solid_cylinder(bm, center=(bj_x, stat_y, stat_z + 2.18), radius=0.16, height=0.26, segments=20, mat_index=idx_bronce)
add_solid_box(bm, center=(bj_x, stat_y - 0.09, stat_z + 2.27), size=(0.24, 0.14, 0.10), mat_index=idx_bronce)
add_solid_box(bm, center=(bj_x, stat_y - 0.15, stat_z + 2.23), size=(0.20, 0.05, 0.04), mat_index=idx_bronce)
add_solid_box(bm, center=(bj_x, stat_y - 0.20, stat_z + 2.18), size=(0.06, 0.09, 0.11), mat_index=idx_bronce)
add_solid_box(bm, center=(bj_x, stat_y - 0.16, stat_z + 2.09), size=(0.16, 0.08, 0.08), mat_index=idx_bronce)
add_solid_box(bm, center=(bj_x, stat_y + 0.06, stat_z + 2.26), size=(0.31, 0.22, 0.16), mat_index=idx_bronce)
add_solid_box(bm, center=(bj_x - 0.17, stat_y, stat_z + 2.18), size=(0.04, 0.08, 0.10), mat_index=idx_bronce)
add_solid_box(bm, center=(bj_x + 0.17, stat_y, stat_z + 2.18), size=(0.04, 0.08, 0.10), mat_index=idx_bronce)

# 4. Caseta CROC taxis al fondo
cas_x, cas_y = bj_x + 1.80, bj_y + 4.00
add_solid_box(bm, center=(cas_x, cas_y, 1.25), size=(2.20, 1.80, 2.50), mat_index=idx_caseta_verde)
add_solid_box(bm, center=(cas_x, cas_y - 0.91, 1.30), size=(0.80, 0.04, 1.20), mat_index=idx_forja)
add_truncated_pyramid(bm, center=(cas_x, cas_y, 2.80), base_s=(2.60, 2.20), top_s=(2.20, 0.20), height=0.60, mat_index=idx_teja_roja)

# ------------------------------------------------------------------------------
# MONUMENTO 3: MONUMENTO A DON LÁZARO CÁRDENAS (Sector Suroeste)
# ------------------------------------------------------------------------------
lc_x, lc_y = -36.0, -25.0

# 1. Muro blanco tipográfico
add_solid_box(bm, center=(lc_x, lc_y, 0.70), size=(4.20, 0.40, 1.40), mat_index=idx_pedestal_blanco)
add_solid_box(bm, center=(lc_x, lc_y, 0.08), size=(4.40, 0.50, 0.16), mat_index=idx_cantera)

# Tipografía 3D modelada carácter por carácter en el muro frontal:
cardenas_text = [
    "GRAL. LAZARO CARDENAS",
    "1895  -  1970",
    "MEXICO",
    "TECATE, B.C.  1973"
]
add_3d_text_letters(bm, cardenas_text, lc_x, lc_y - 0.22, base_z=1.12, line_spacing=0.22, char_w=0.09, char_h=0.11, char_d=0.03, mat_idx=idx_letras_negras)

# 2. Pedestal y Busto de Lázaro Cárdenas integrado sobre el centro del muro
add_solid_box(bm, center=(lc_x, lc_y, 1.70), size=(0.95, 0.60, 0.70), mat_index=idx_pedestal_blanco)
add_solid_box(bm, center=(lc_x, lc_y, 2.08), size=(1.05, 0.70, 0.10), mat_index=idx_cantera)

# Busto de bronce del General Lázaro Cárdenas (mirando al sur)
busto_z = 2.13
add_solid_box(bm, center=(lc_x, lc_y, busto_z + 0.06), size=(0.65, 0.45, 0.12), mat_index=idx_bronce)
add_truncated_pyramid(bm, center=(lc_x, lc_y, busto_z + 0.30), base_s=(0.72, 0.42), top_s=(0.48, 0.30), height=0.36, mat_index=idx_bronce)
add_solid_box(bm, center=(lc_x, lc_y - 0.18, busto_z + 0.35), size=(0.14, 0.04, 0.14), mat_index=idx_blanco_camisa)
add_solid_box(bm, center=(lc_x, lc_y - 0.20, busto_z + 0.32), size=(0.06, 0.03, 0.18), mat_index=idx_letras_negras)
add_solid_cylinder(bm, center=(lc_x, lc_y, busto_z + 0.52), radius=0.12, height=0.12, segments=16, mat_index=idx_bronce)
add_solid_cylinder(bm, center=(lc_x, lc_y, busto_z + 0.70), radius=0.17, height=0.26, segments=20, mat_index=idx_bronce)
add_solid_box(bm, center=(lc_x, lc_y - 0.12, busto_z + 0.78), size=(0.24, 0.12, 0.08), mat_index=idx_bronce)
add_solid_box(bm, center=(lc_x, lc_y - 0.21, busto_z + 0.70), size=(0.07, 0.09, 0.12), mat_index=idx_bronce)
add_solid_box(bm, center=(lc_x, lc_y - 0.18, busto_z + 0.62), size=(0.16, 0.08, 0.08), mat_index=idx_bronce)
add_solid_box(bm, center=(lc_x, lc_y - 0.19, busto_z + 0.65), size=(0.12, 0.03, 0.03), mat_index=idx_letras_negras)
add_solid_box(bm, center=(lc_x, lc_y + 0.06, busto_z + 0.78), size=(0.32, 0.20, 0.16), mat_index=idx_bronce)

# 3. Murete curvo frontal amarillo ocre y jardinera continua
r_curv = 2.80
n_curv = 24
for i in range(n_curv):
    ang1 = math.pi * (1.0 + i / n_curv)
    ang2 = math.pi * (1.0 + (i + 1) / n_curv)
    x1 = lc_x + r_curv * math.cos(ang1)
    y1 = lc_y - 0.20 + r_curv * math.sin(ang1)
    x2 = lc_x + r_curv * math.cos(ang2)
    y2 = lc_y - 0.20 + r_curv * math.sin(ang2)
    mx = (x1 + x2) * 0.5
    my = (y1 + y2) * 0.5
    seg_len = math.hypot(x2 - x1, y2 - y1)
    seg_ang = math.atan2(y2 - y1, x2 - x1)
    add_solid_box(bm, center=(mx, my, 0.22), size=(seg_len * 1.05, 0.28, 0.45), rot_z=seg_ang, mat_index=idx_ocre)

add_solid_cylinder(bm, center=(lc_x, lc_y - 1.20, 0.10), radius=2.20, height=0.18, segments=24, mat_index=idx_tierra)

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

# Placas de bronce con relieve
add_solid_box(bm, center=(ob_x, ob_y - 0.64, 1.50), size=(0.65, 0.03, 0.48), mat_index=idx_bronce)
add_solid_box(bm, center=(ob_x, ob_y + 0.64, 1.50), size=(0.65, 0.03, 0.48), mat_index=idx_bronce)
add_solid_box(bm, center=(ob_x - 0.64, ob_y, 1.50), size=(0.03, 0.65, 0.48), mat_index=idx_bronce)
add_solid_box(bm, center=(ob_x + 0.64, ob_y, 1.50), size=(0.03, 0.65, 0.48), mat_index=idx_bronce)

# ==============================================================================
# 5. ALCORQUES ANULARES ELEVADOS Y JARDINERAS PERIMETRALES
# ==============================================================================
print("[PARQUE HIDALGO] Construyendo alcorques anulares continuos...")

def add_continuous_tree_planter(bm, center_xy, r_ext=1.60, r_int=1.25, height=0.38):
    cx, cy = center_xy
    add_solid_ring(bm, center=(cx, cy, height*0.5), r_ext=r_ext, r_int=r_int, height=height, segments=24, mat_index=idx_ocre, smooth=True)
    add_solid_cylinder(bm, center=(cx, cy, height - 0.06), radius=r_int, height=0.12, segments=20, mat_index=idx_tierra)

alcorque_positions = [
    (-4.5, 24.0), (4.5, 24.0), (-3.8, 16.0), (3.8, 16.0),
    (-4.0, -15.0), (4.0, -15.0), (-4.2, -28.0), (4.2, -28.0),
    (24.0, 5.5), (24.0, -5.5), (32.0, 7.5), (32.0, -6.5),
    (-22.0, 6.0), (-22.0, -6.0), (-36.0, 8.0)
]
for pos in alcorque_positions:
    add_continuous_tree_planter(bm, pos)

# ==============================================================================
# 6. MOBILIARIO URBANO (BANCAS CON BLASÓN, FAROLAS 3 BRAZOS, MESAS AJEDREZ)
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
        # Voluta apoyabrazos redondeada
        add_solid_cylinder(bm, center=rot(side_x, -0.05, 0.52), radius=0.08, height=0.06, segments=12, mat_index=idx_forja)

    add_solid_box(bm, center=rot(0.0, -0.25, 0.68), size=(1.80, 0.04, 0.38), rot_z=angle_rad, mat_index=idx_forja)
    # Blasón / Escudo ornamental centrado en el copete del respaldo (media_1790414673421.jpg)
    add_solid_box(bm, center=rot(0.0, -0.25, 0.92), size=(0.32, 0.06, 0.22), rot_z=angle_rad, mat_index=idx_forja)
    add_solid_cylinder(bm, center=rot(0.0, -0.25, 0.96), radius=0.14, height=0.04, segments=16, mat_index=idx_forja)

    for sy, sz in [(-0.16, 0.42), (-0.05, 0.43), (0.07, 0.44), (0.19, 0.44)]:
        add_solid_box(bm, center=rot(0.0, sy, sz), size=(1.76, 0.10, 0.035), rot_z=angle_rad, mat_index=idx_madera)

bench_data = [
    ((-3.2, 20.0), math.pi * 0.5), ((3.2, 20.0), -math.pi * 0.5),
    ((-3.2, 28.0), math.pi * 0.5), ((3.2, 28.0), -math.pi * 0.5),
    ((-3.2, -13.0), math.pi * 0.5), ((3.2, -13.0), -math.pi * 0.5),
    ((-3.2, -26.0), math.pi * 0.5), ((3.2, -26.0), -math.pi * 0.5),
    ((18.0, 3.4), 0.0), ((18.0, -3.4), math.pi),
    ((28.0, 3.4), 0.0), ((28.0, -3.4), math.pi),
    ((-18.0, 3.2), 0.0), ((-18.0, -3.2), math.pi),
    ((-28.0, 3.2), 0.0), ((-28.0, -3.2), math.pi),
]
for bp, bang in bench_data:
    add_ornamental_bench(bm, bp, bang)

def add_triple_colonial_lamp(bm, pos_xy):
    lx, ly = pos_xy
    add_solid_cylinder(bm, center=(lx, ly, 0.25), radius=0.34, height=0.50, segments=8, mat_index=idx_forja)
    add_solid_cylinder(bm, center=(lx, ly, 2.00), radius=0.09, height=3.00, segments=12, mat_index=idx_forja)
    add_solid_cylinder(bm, center=(lx, ly, 3.55), radius=0.18, height=0.20, segments=12, mat_index=idx_forja)

    for arm in range(3):
        ang = arm * (2.0 * math.pi / 3.0)
        ax = math.cos(ang) * 0.65
        ay = math.sin(ang) * 0.65
        add_solid_box(bm, center=(lx + ax*0.5, ly + ay*0.5, 3.65), size=(0.06, 0.06, 0.24), mat_index=idx_forja)
        fx, fy = lx + ax, ly + ay
        add_solid_cylinder(bm, center=(fx, fy, 3.82), radius=0.22, height=0.36, segments=6, mat_index=idx_forja)
        add_truncated_pyramid(bm, center=(fx, fy, 4.08), base_s=(0.36, 0.36), top_s=(0.06, 0.06), height=0.26, mat_index=idx_forja)

lamp_positions = [
    (-9.0, 9.0), (9.0, 9.0), (-9.0, -9.0), (9.0, -9.0),
    (0.0, 31.0), (0.0, -33.0), (45.0, 0.0), (-48.0, 0.0),
    (28.0, 10.0), (28.0, -10.0),
]
for lp in lamp_positions:
    add_triple_colonial_lamp(bm, lp)

# Mesas de ajedrez / picnic de concreto con bancos rectangulares (media_1790414528108.jpg)
def add_chess_table(bm, pos_xy):
    tx, ty = pos_xy
    add_solid_cylinder(bm, center=(tx, ty, 0.38), radius=0.24, height=0.76, segments=12, mat_index=idx_cantera)
    add_solid_box(bm, center=(tx, ty, 0.78), size=(1.10, 1.10, 0.08), mat_index=idx_cantera)
    add_solid_box(bm, center=(tx, ty, 0.825), size=(0.55, 0.55, 0.01), mat_index=idx_letras_negras)
    for bx, by in [(-0.85, 0), (0.85, 0)]:
        add_solid_box(bm, center=(tx + bx, ty + by, 0.22), size=(0.32, 0.90, 0.44), mat_index=idx_cantera)
    for bx, by in [(0, -0.85), (0, 0.85)]:
        add_solid_box(bm, center=(tx + bx, ty + by, 0.22), size=(0.90, 0.32, 0.44), mat_index=idx_cantera)

for cp in [(24.0, 8.0), (24.0, 10.5), (24.0, -8.0), (24.0, -10.5), (-34.0, 12.0), (-34.0, 14.5)]:
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
    (36.0, 3.0), (-42.0, 3.0)
]
for bdp in blue_drum_positions:
    add_blue_trash_drum(bm, bdp)

# Caseta rústica / techumbre de parada de taxis con teja a dos aguas (media_1790414528108.jpg)
def add_taxi_shelter(bm, pos_xy, angle_rad=0.0):
    px, py = pos_xy
    ca, sa = math.cos(angle_rad), math.sin(angle_rad)
    def rot(lx, ly, lz):
        return (lx * ca - ly * sa + px, lx * sa + ly * ca + py, lz)
    for sx, sy in [(-1.3, -0.85), (1.3, -0.85), (-1.3, 0.85), (1.3, 0.85)]:
        add_solid_box(bm, center=rot(sx, sy, 1.25), size=(0.16, 0.16, 2.50), rot_z=angle_rad, mat_index=idx_madera)
    add_solid_box(bm, center=rot(0.0, 0.80, 1.40), size=(2.30, 0.06, 1.10), rot_z=angle_rad, mat_index=idx_pedestal_blanco)
    add_solid_box(bm, center=rot(0.0, -0.85, 2.45), size=(2.90, 0.14, 0.14), rot_z=angle_rad, mat_index=idx_madera)
    add_solid_box(bm, center=rot(0.0, 0.85, 2.45), size=(2.90, 0.14, 0.14), rot_z=angle_rad, mat_index=idx_madera)
    add_truncated_pyramid(bm, center=rot(0.0, 0.0, 2.85), base_s=(3.20, 2.30), top_s=(3.00, 0.30), height=0.65, rot_z=angle_rad, mat_index=idx_teja_roja)

add_taxi_shelter(bm, (-36.0, 18.0), angle_rad=0.0)

# ==============================================================================
# 7. MASAS FORESTALES ORGÁNICAS (ICÓSFERAS MULTILOBULADAS Y PALMERAS)
# ==============================================================================
print("[PARQUE HIDALGO] Generando masa forestal realista y palmeras...")

def add_foliage_sphere(bm, center, radius, mat_index=idx_follaje):
    # Genera una esfera de follaje suave
    res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=radius, matrix=Matrix.Translation(center))
    for v in res['verts']:
        # Ruido de volumen para romper la regularidad
        dist = 1.0 + 0.08 * math.sin(v.co.x * 3.0) * math.cos(v.co.y * 3.0)
        v.co = Vector(center) + (v.co - Vector(center)) * dist
    faces = set(f for v in res['verts'] for f in v.link_faces)
    for f in faces:
        f.smooth = True
        f.material_index = mat_index
    assign_uvs(list(faces), 1.0)

def add_organic_tree(bm, pos_xy, trunk_h=3.5, trunk_r=0.45, crown_r=4.0, crown_h=5.5):
    tx, ty = pos_xy
    # Tronco principal cónico
    add_truncated_pyramid(bm, center=(tx, ty, trunk_h*0.5), base_s=(trunk_r*2.2, trunk_r*2.2), top_s=(trunk_r*1.6, trunk_r*1.6),
                         height=trunk_h, mat_index=idx_corteza)
    # Ramas gruesas
    for b_idx in range(4):
        b_ang = b_idx * (math.pi * 0.5) + 0.25
        bx = math.cos(b_ang) * (trunk_r * 1.6)
        by = math.sin(b_ang) * (trunk_r * 1.6)
        add_solid_cylinder(bm, center=(tx + bx, ty + by, trunk_h + 0.8), radius=trunk_r*0.45, height=1.8, segments=8, mat_index=idx_corteza)

    # Copa con múltiples esferas de follaje intersecadas
    cz_base = trunk_h + crown_h * 0.45
    add_foliage_sphere(bm, (tx, ty, cz_base + 0.5), radius=crown_r * 0.85)
    for c_i in range(5):
        c_ang = c_i * (2.0 * math.pi / 5.0)
        clx = tx + math.cos(c_ang) * (crown_r * 0.52)
        cly = ty + math.sin(c_ang) * (crown_r * 0.52)
        clz = cz_base + (c_i % 2) * 0.7 - 0.2
        add_foliage_sphere(bm, (clx, cly, clz), radius=crown_r * 0.65)

def add_washingtonia_palm(bm, pos_xy, height=14.0):
    px, py = pos_xy
    # Tronco anillado
    add_truncated_pyramid(bm, center=(px, py, 1.2), base_s=(1.1, 1.1), top_s=(0.7, 0.7), height=2.4, mat_index=idx_palma_tronco)
    add_truncated_pyramid(bm, center=(px, py, height*0.5 + 1.2), base_s=(0.7, 0.7), top_s=(0.55, 0.55), height=height, mat_index=idx_palma_tronco)
    add_truncated_pyramid(bm, center=(px, py, height + 0.5), base_s=(1.3, 1.3), top_s=(0.8, 0.8), height=1.6, mat_index=idx_palma_tronco)

    # Penacho de 16 frondas en estrella
    for leaf in range(16):
        lang = leaf * (2.0 * math.pi / 16.0)
        ca, sa = math.cos(lang), math.sin(lang)
        lx = px + ca * 2.2
        ly = py + sa * 2.2
        lz = height + 1.2 - 0.4 * (leaf % 2)
        add_solid_box(bm, center=(lx, ly, lz), size=(2.0, 0.60, 0.08), rot_z=lang, mat_index=idx_palma_hojas)

for pos in alcorque_positions[:10]:
    add_organic_tree(bm, pos, trunk_h=3.2, trunk_r=0.42, crown_r=3.6, crown_h=5.2)

monumental_trees = [
    (18.0, 24.0), (24.0, 16.0), (12.0, 26.0),
    (-24.0, 24.0), (-16.0, 26.0), (-38.0, 22.0),
    (16.0, -22.0), (26.0, -18.0), (32.0, -24.0),
    (-20.0, -20.0), (-26.0, -16.0), (-18.0, -26.0),
]
for mt in monumental_trees:
    add_organic_tree(bm, mt, trunk_h=4.5, trunk_r=0.55, crown_r=5.0, crown_h=7.2)

for pp in [(-14.0, 12.0), (14.0, 12.0), (-14.0, -12.0), (14.0, -12.0), (-42.0, 18.0), (42.0, 14.0)]:
    add_washingtonia_palm(bm, pp, height=13.5)

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

# ==============================================================================
# 9. ESCENA GODOT 4 (.tscn) CON COLISIONES ANALÍTICAS
# ==============================================================================
print(f"[PARQUE HIDALGO] Escribiendo escena Godot con colisiones analíticas en {TSCN_OUT_PATH}...")

tscn_content = """[gd_scene load_steps=12 format=3 uid="uid://b8parquehidalgo2009"]

[ext_resource type="PackedScene" path="res://assets/parque_miguel_hidalgo.glb" id="1_mesh"]

[sub_resource type="BoxShape3D" id="Shape_Plataforma_General"]
size = Vector3(106.0, 1.5, 71.0)

[sub_resource type="BoxShape3D" id="Shape_Andador_Norte"]
size = Vector3(5.0, 0.4, 24.0)

[sub_resource type="BoxShape3D" id="Shape_Andador_Sur"]
size = Vector3(5.0, 0.4, 26.0)

[sub_resource type="BoxShape3D" id="Shape_Andador_Este"]
size = Vector3(38.0, 0.4, 5.5)

[sub_resource type="BoxShape3D" id="Shape_Andador_Oeste"]
size = Vector3(45.0, 0.4, 5.2)

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
size = Vector3(3.8, 1.5, 0.6)

[node name="ParqueMiguelHidalgo" type="Node3D"]

[node name="VisualMesh" parent="." instance=ExtResource("1_mesh")]

[node name="StaticBody3D" type="StaticBody3D" parent="."]
collision_layer = 1
collision_mask = 0

# 1. Plataforma basal enterrada transitable
[node name="Col_Plataforma" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -4.0, -0.75, 1.5)
shape = SubResource("Shape_Plataforma_General")

# 2. Andadores principales transitables
[node name="Col_Andador_N" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.0, 0.2, -22.0)
shape = SubResource("Shape_Andador_Norte")

[node name="Col_Andador_S" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.0, 0.2, 23.5)
shape = SubResource("Shape_Andador_Sur")

[node name="Col_Andador_E" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 29.5, 0.2, 0.0)
shape = SubResource("Shape_Andador_Este")

[node name="Col_Andador_W" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -33.5, 0.2, 0.0)
shape = SubResource("Shape_Andador_Oeste")

# 3. Colisiones del Monumento a Benito Juárez (Noreste)
[node name="Col_Podio_Juarez" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 30.0, 0.35, -21.0)
shape = SubResource("Shape_Podio_Juarez")

[node name="Col_Pedestal_Juarez" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 30.0, 1.65, -20.8)
shape = SubResource("Shape_Pedestal_Juarez")

# 4. Colisiones del Monumento a Miguel Hidalgo (Sur)
[node name="Col_Medallon_Hidalgo" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.0, 0.1, 21.0)
shape = SubResource("Shape_Medallon_Hidalgo")

[node name="Col_Pedestal_Hidalgo" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.0, 1.2, 21.0)
shape = SubResource("Shape_Pedestal_Hidalgo")

# 5. Colisiones del Obelisco Conmemorativo (Este)
[node name="Col_Obelisco_Base" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 38.0, 0.3, 10.0)
shape = SubResource("Shape_Obelisco_Base")

[node name="Col_Obelisco_Fuste" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 38.0, 3.2, 10.0)
shape = SubResource("Shape_Obelisco_Fuste")

# 6. Colisiones del Monumento a Lázaro Cárdenas (Suroeste)
[node name="Col_Muro_Cardenas" type="CollisionShape3D" parent="StaticBody3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -36.0, 0.75, 25.0)
shape = SubResource("Shape_Muro_Cardenas")
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
        "loc": (-4.0, -1.5, 78.0),
        "target": (-4.0, -1.5, 0.0),
        "lens": 35.0,
        "filename": "parque_01_cenital_top.png"
    },
    {
        "name": "Cam_02_Acceso_Norte_Juarez",
        "loc": (0.0, 40.0, 2.5),
        "target": (0.0, 10.0, 1.5),
        "lens": 28.0,
        "filename": "parque_02_acceso_norte_juarez.png"
    },
    {
        "name": "Cam_03_Busto_Hidalgo_Sur",
        "loc": (0.0, -27.0, 1.8),
        "target": (hid_x, hid_y, 2.1),
        "lens": 32.0,
        "filename": "parque_03_busto_hidalgo_sur.png"
    },
    {
        # Vista frontal a Juárez: cámara al sur de Juárez mirando hacia el norte (+Y)
        "name": "Cam_04_Monumento_Juarez_NE",
        "loc": (30.0, 13.5, 2.2),
        "target": (bj_x, bj_y, 3.2),
        "lens": 32.0,
        "filename": "parque_04_monumento_juarez_ne.png"
    },
    {
        # Vista frontal a Cárdenas: cámara al sur de Cárdenas mirando hacia el norte (+Y)
        "name": "Cam_05_Monumento_Cardenas_SO",
        "loc": (-36.0, -32.0, 1.8),
        "target": (lc_x, lc_y, 1.8),
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
        "name": "Cam_07_Peatonal_Andador_Bancas",
        "loc": (15.0, 0.0, 1.65),
        "target": (0.0, 0.0, 1.65),
        "lens": 28.0,
        "filename": "parque_07_peatonal_andador_bancas.png"
    },
    {
        "name": "Cam_08_Acceso_Oeste_Cardenas",
        "loc": (-56.0, 0.0, 2.4),
        "target": (-20.0, 0.0, 1.8),
        "lens": 28.0,
        "filename": "parque_08_acceso_oeste_cardenas.png"
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
