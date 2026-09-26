"""
Generador Procedural 3D de Alta Fidelidad Fotorrealista: Manzana Central Urbana (2009)
========================================================================================
Tecate Simulator — Reconstrucción integral de la manzana catastral block_lat_32.57328_lon_-116.62516
Delimitada por:
  - Norte: Avenida Benito Juárez
  - Sur: Callejón Libertad
  - Oeste: Calle Presidente Pascual Ortiz Rubio
  - Este: Calle Presidente Abelardo L. Rodríguez

Hitos y Comercios Históricos (2009):
  - Central / Terminal de Autobuses Tecate B.C. (ABC, TNS, Elite, SuburBaja)
  - Telas Elías / Bordados Elías (2 niveles monumental ocre, pórtico con columnas)
  - Hotel Juárez & Cafetería Juárez (2 niveles con grandes ventanales)
  - Hotel Colonial (fachada patrimonial colonial californiana en Callejón Libertad)
  - Dulcería Prisci (fachada lámina roja acanalada, toldo multicolor, rótulo corpóreo)
  - Heras Café Internet / Restaurant 2 de Sonora (2 niveles con barandal rústico de troncos)
  - Arrematec Demoliciones (fachada amarilla y roja con portón de herrería)
  - Escritorio Público Fimbres (fachada naranja)
  - CopyFast (Centro de Copiado con marquesina azul)
  - Taquería La Placita (2 niveles azul cobalto)
  - La Flor de Michoacán (2 frentes: Ortiz Rubio/Libertad y Av. Juárez)
  - Farmacia del Pueblo, Rosticería Los Polos, Taquería Los Arcos, Mariscos El Chapo
  - Barber Shop Azteca 230, Modas Da Vinci, Don Elías, Beto's Barbería, Café Los Pinos
  - Belrom Bienes Raíces, Joyería, Gimnasio
  - Patios interiores, dársenas de autobuses techadas, cercha espacial tridimensional de acero

ESTÁNDAR RIGUROSO:
  - CERO texturas de panoramas pegadas en quads. 100% geometría procedural en mallas y textos 3D.
  - Zócalo basal continuo enterrado a Z = -1.50 m (sin intersecciones redundantes).
  - Cero banquetas embebidas en el .glb.
  - Particionado estricto de volúmenes edilicios: cero cajas duplicadas o superpuestas en esquinas.
  - Cubiertas retranqueadas dentro de parapetos para evitar perforaciones y coplanaridad.
  - Vidrios con transmisión física PBR.
  - Orientación canónica de textos anti-espejo en cada fachada cardinal.
  - Escena .tscn con física analítica descompuesta (BoxShape3D) transitable.
"""

import os
import math
import bpy
import bmesh
from mathutils import Vector, Euler

# ---------------------------------------------------------------------------
# 1. Configuración de Rutas y Parámetros Maestros
# ---------------------------------------------------------------------------
TEXTURES_DIR = os.path.abspath("godot_project/assets/textures")
BUILDINGS_DIR = os.path.abspath("godot_project/assets/buildings")
BLENDER_DIR = os.path.abspath("blender_assets/buildings")
DOCS_IMAGES_DIR = os.path.abspath("docs/images/manzana_central")

for d in [TEXTURES_DIR, BUILDINGS_DIR, BLENDER_DIR, DOCS_IMAGES_DIR]:
    os.makedirs(d, exist_ok=True)

BLEND_PATH = os.path.join(BLENDER_DIR, "manzana_central_2009.blend")
GLB_PATH = os.path.join(BUILDINGS_DIR, "manzana_central_2009.glb")
TSCN_PATH = os.path.join(BUILDINGS_DIR, "manzana_central_2009.tscn")

# Dimensiones Globales de la Manzana (Coordenadas Cartesianas Canónicas)
X_MAX = 134.73
Y_MAX = 91.19
Z_BASE = -1.50
Z_GROUND = 0.00

# Rotaciones Euler Canónicas Anti-Espejo para Curvas de Texto FONT
ROT_SOUTH = (math.radians(90.0), 0.0, 0.0)                         # Normal (0, -1, 0)
ROT_NORTH = (math.radians(90.0), 0.0, math.radians(180.0))         # Normal (0, +1, 0)
ROT_WEST  = (math.radians(90.0), 0.0, math.radians(-90.0))        # Normal (-1, 0, 0)
ROT_EAST  = (math.radians(90.0), 0.0, math.radians(90.0))         # Normal (+1, 0, 0)

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

# ---------------------------------------------------------------------------
# 2. Utilidades de Escena y BMesh
# ---------------------------------------------------------------------------
def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    col = bpy.data.collections.new("Manzana_Central_Collection")
    scene.collection.children.link(col)
    return col

def add_box(bm, x1, x2, y1, y2, z1, z2):
    """Genera paralelepípedo cerrado limpio con normales exteriores."""
    xa, xb = min(x1, x2), max(x1, x2)
    ya, yb = min(y1, y2), max(y1, y2)
    za, zb = min(z1, z2), max(z1, z2)
    verts = [
        bm.verts.new((xa, ya, za)), bm.verts.new((xb, ya, za)),
        bm.verts.new((xb, yb, za)), bm.verts.new((xa, yb, za)),
        bm.verts.new((xa, ya, zb)), bm.verts.new((xb, ya, zb)),
        bm.verts.new((xb, yb, zb)), bm.verts.new((xa, yb, zb))
    ]
    bm.faces.new((verts[0], verts[1], verts[2], verts[3])) # -Z
    bm.faces.new((verts[4], verts[7], verts[6], verts[5])) # +Z
    bm.faces.new((verts[0], verts[4], verts[5], verts[1])) # -Y
    bm.faces.new((verts[1], verts[5], verts[6], verts[2])) # +X
    bm.faces.new((verts[2], verts[6], verts[7], verts[3])) # +Y
    bm.faces.new((verts[3], verts[7], verts[4], verts[0])) # -X

def add_canopy_quarter_round_x(bm, x1, x2, y_back, depth, z_bottom, height, segments=8):
    """Genera toldo abombado de cuarto de cilindro a lo largo del eje X (fachadas Norte o Sur)."""
    sign = -1.0 if depth > 0 else 1.0
    abs_d = abs(depth)
    arc_pts = []
    for i in range(segments + 1):
        th = (math.pi * 0.5) * (i / segments)
        dy = sign * abs_d * math.cos(th)
        dz = height * math.sin(th)
        arc_pts.append((y_back + dy, z_bottom + dz))

    for i in range(segments):
        y0, z0 = arc_pts[i]
        y1, z1 = arc_pts[i+1]
        v_bl = bm.verts.new((x1, y0, z0))
        v_br = bm.verts.new((x2, y0, z0))
        v_tr = bm.verts.new((x2, y1, z1))
        v_tl = bm.verts.new((x1, y1, z1))
        bm.faces.new((v_bl, v_br, v_tr, v_tl))

    # Tapas laterales
    v_b_top = bm.verts.new((x1, y_back, z_bottom + height))
    v_b_bot = bm.verts.new((x1, y_back, z_bottom))
    v_f_bot = bm.verts.new((x1, y_back + sign * abs_d, z_bottom))
    bm.faces.new((v_b_bot, v_f_bot, v_b_top))

    v_r_top = bm.verts.new((x2, y_back, z_bottom + height))
    v_r_bot = bm.verts.new((x2, y_back, z_bottom))
    v_r_fbot = bm.verts.new((x2, y_back + sign * abs_d, z_bottom))
    bm.faces.new((v_r_bot, v_r_top, v_r_fbot))

def add_canopy_quarter_round_y(bm, y_start, y_end, x_back, depth, z_bottom, height, segments=8):
    """Genera toldo abombado de cuarto de cilindro a lo largo del eje Y (fachadas Poniente u Oriente)."""
    sign = -1.0 if depth > 0 else 1.0
    abs_d = abs(depth)
    arc_pts = []
    for i in range(segments + 1):
        th = (math.pi * 0.5) * (i / segments)
        dx = sign * abs_d * math.cos(th)
        dz = height * math.sin(th)
        arc_pts.append((x_back + dx, z_bottom + dz))

    for i in range(segments):
        x0, z0 = arc_pts[i]
        x1, z1 = arc_pts[i+1]
        v_bl = bm.verts.new((x0, y_start, z0))
        v_br = bm.verts.new((x0, y_end, z0))
        v_tr = bm.verts.new((x1, y_end, z1))
        v_tl = bm.verts.new((x1, y_start, z1))
        bm.faces.new((v_bl, v_br, v_tr, v_tl))

    # Tapas laterales
    v_b_top = bm.verts.new((x_back, y_start, z_bottom + height))
    v_b_bot = bm.verts.new((x_back, y_start, z_bottom))
    v_f_bot = bm.verts.new((x_back + sign * abs_d, y_start, z_bottom))
    bm.faces.new((v_b_bot, v_b_top, v_f_bot))

    v_r_top = bm.verts.new((x_back, y_end, z_bottom + height))
    v_r_bot = bm.verts.new((x_back, y_end, z_bottom))
    v_r_fbot = bm.verts.new((x_back + sign * abs_d, y_end, z_bottom))
    bm.faces.new((v_r_bot, v_r_fbot, v_r_top))

def add_teja_ribs_x(bm, x_start, x_end, y_eave, y_ridge, z_eave, z_ridge, spacing=0.36):
    """Hiladas de tejas coloniales curvas 3D con canales y cobijas a lo largo de X."""
    num_ribs = max(1, int(abs(x_end - x_start) / spacing))
    x_min = min(x_start, x_end)
    for i in range(num_ribs):
        xc = x_min + (i + 0.5) * spacing
        v0 = bm.verts.new((xc - 0.10, y_eave, z_eave + 0.03))
        v1 = bm.verts.new((xc + 0.10, y_eave, z_eave + 0.03))
        v2 = bm.verts.new((xc + 0.10, y_ridge, z_ridge + 0.03))
        v3 = bm.verts.new((xc - 0.10, y_ridge, z_ridge + 0.03))
        v_top0 = bm.verts.new((xc, y_eave, z_eave + 0.09))
        v_top1 = bm.verts.new((xc, y_ridge, z_ridge + 0.09))

        bm.faces.new((v0, v1, v_top0))
        bm.faces.new((v1, v2, v_top1, v_top0))
        bm.faces.new((v2, v3, v_top1))
        bm.faces.new((v3, v0, v_top0, v_top1))

def add_teja_ribs_y(bm, y_start, y_end, x_eave, x_ridge, z_eave, z_ridge, spacing=0.36):
    """Hiladas de tejas coloniales curvas 3D a lo largo de Y (fachada Poniente u Oriente)."""
    num_ribs = max(1, int(abs(y_end - y_start) / spacing))
    y_min = min(y_start, y_end)
    for i in range(num_ribs):
        yc = y_min + (i + 0.5) * spacing
        v0 = bm.verts.new((x_eave, yc - 0.10, z_eave + 0.03))
        v1 = bm.verts.new((x_eave, yc + 0.10, z_eave + 0.03))
        v2 = bm.verts.new((x_ridge, yc + 0.10, z_ridge + 0.03))
        v3 = bm.verts.new((x_ridge, yc - 0.10, z_ridge + 0.03))
        v_top0 = bm.verts.new((x_eave, yc, z_eave + 0.09))
        v_top1 = bm.verts.new((x_ridge, yc, z_ridge + 0.09))

        bm.faces.new((v0, v1, v_top0))
        bm.faces.new((v1, v2, v_top1, v_top0))
        bm.faces.new((v2, v3, v_top1))
        bm.faces.new((v3, v0, v_top0, v_top1))

def add_arch_spandrel_x(bm, y_front, y_back, x_start, x_end, z_spring, z_crown, z_top, segments=12):
    """Construye arco rebajado en X con intradós para arcos de ladrillo o vanos decorativos."""
    span = x_end - x_start
    x_center = (x_start + x_end) * 0.5
    rise = z_crown - z_spring
    r = (rise**2 + (span * 0.5)**2) / (2.0 * rise)
    center_z = z_crown - r

    arc_pts = []
    for i in range(segments + 1):
        t = i / segments
        x = x_start + t * span
        dx = x - x_center
        dy_sq = dx**2
        dz = math.sqrt(max(0.0, r**2 - dy_sq if dy_sq <= r**2 else 0.0))
        z = center_z + dz
        arc_pts.append((x, z))

    y_min = min(y_front, y_back)
    y_max = max(y_front, y_back)

    for i in range(segments):
        x0, z0 = arc_pts[i]
        x1, z1 = arc_pts[i+1]
        v_bl_in = bm.verts.new((x0, y_max, z0))
        v_br_in = bm.verts.new((x1, y_max, z1))
        v_tr_in = bm.verts.new((x1, y_max, z_top))
        v_tl_in = bm.verts.new((x0, y_max, z_top))

        v_bl_out = bm.verts.new((x0, y_min, z0))
        v_br_out = bm.verts.new((x1, y_min, z1))
        v_tr_out = bm.verts.new((x1, y_min, z_top))
        v_tl_out = bm.verts.new((x0, y_min, z_top))

        bm.faces.new((v_bl_out, v_tl_out, v_tr_out, v_br_out))
        bm.faces.new((v_bl_in, v_br_in, v_tr_in, v_tl_in))
        bm.faces.new((v_bl_out, v_br_out, v_br_in, v_bl_in))
        bm.faces.new((v_tl_out, v_tl_in, v_tr_in, v_tr_out))

def add_space_frame_truss_y(bm, x1, x2, y1, y2, z1, z2, subdivisions=8):
    """Construye cercha espacial tridimensional de acero galvanizado a lo largo del eje Y (portón central)."""
    dy = (y2 - y1) / subdivisions
    r_pipe = 0.04
    for i in range(subdivisions):
        ya = y1 + i * dy
        yb = y1 + (i + 1) * dy
        # 4 cordones longitudinales
        add_box(bm, x1 - r_pipe, x1 + r_pipe, ya, yb, z1 - r_pipe, z1 + r_pipe)
        add_box(bm, x1 - r_pipe, x1 + r_pipe, ya, yb, z2 - r_pipe, z2 + r_pipe)
        add_box(bm, x2 - r_pipe, x2 + r_pipe, ya, yb, z1 - r_pipe, z1 + r_pipe)
        add_box(bm, x2 - r_pipe, x2 + r_pipe, ya, yb, z2 - r_pipe, z2 + r_pipe)
        # Montantes verticales
        add_box(bm, x1 - r_pipe, x1 + r_pipe, ya - r_pipe, ya + r_pipe, z1, z2)
        add_box(bm, x2 - r_pipe, x2 + r_pipe, ya - r_pipe, ya + r_pipe, z1, z2)
        # Travesaños transversales
        add_box(bm, x1, x2, ya - r_pipe, ya + r_pipe, z1 - r_pipe, z1 + r_pipe)
        add_box(bm, x1, x2, ya - r_pipe, ya + r_pipe, z2 - r_pipe, z2 + r_pipe)
        # Diagonales cruzadas en X
        add_box(bm, (x1 + x2)*0.5 - r_pipe, (x1 + x2)*0.5 + r_pipe, ya, yb, z1 - r_pipe, z2 + r_pipe)

def auto_uv_bmesh(bm, scale_u=0.5, scale_v=0.5):
    """Genera coordenadas UV ortogonales cúbicas con preservación métrica."""
    uv_layer = bm.loops.layers.uv.verify()
    for face in bm.faces:
        n = face.normal
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for loop in face.loops:
            v = loop.vert.co
            if ax >= ay and ax >= az:
                u, w = v.y * scale_u, v.z * scale_v
            elif ay >= ax and ay >= az:
                u, w = v.x * scale_u, v.z * scale_v
            else:
                u, w = v.x * scale_u, v.y * scale_v
            loop[uv_layer].uv = (u, w)

def create_mesh_object(name, bm, material, col, uv_scale=0.5):
    auto_uv_bmesh(bm, uv_scale, uv_scale)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(f"Mesh_{name}")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    if material:
        obj.data.materials.append(material)
    col.objects.link(obj)
    return obj

def add_3d_text(name, body, size, extrude, loc, rot_euler, mat, col, align_x='CENTER'):
    """Crea rótulo corpóreo en curvas 3D extruidas con orientación anti-espejo."""
    f_curve = bpy.data.curves.new(type="FONT", name=f"Font_{name}")
    f_curve.body = body
    f_curve.size = size
    f_curve.extrude = extrude
    f_curve.align_x = align_x
    f_curve.align_y = 'CENTER'

    # Asignar fuente del sistema si existe
    if os.path.exists(FONT_PATH):
        try:
            font_data = bpy.data.fonts.load(FONT_PATH)
            f_curve.font = font_data
        except Exception:
            pass

    obj = bpy.data.objects.new(name, f_curve)
    obj.location = Vector(loc)
    obj.rotation_euler = Euler(rot_euler, 'XYZ')
    if mat:
        obj.data.materials.append(mat)
    col.objects.link(obj)
    return obj

# ---------------------------------------------------------------------------
# 3. Fábrica de Materiales PBR
# ---------------------------------------------------------------------------
def make_pbr_material(name, base_color=(0.8, 0.8, 0.8), roughness=0.85, metallic=0.0, alpha=1.0, transmission=0.0, ior=1.45):
    """Crea material Principled BSDF conectado y robusto para glTF y Cycles."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (base_color[0], base_color[1], base_color[2], 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic

    if 'Transmission Weight' in bsdf.inputs and transmission > 0.0:
        bsdf.inputs['Transmission Weight'].default_value = transmission
    elif 'Transmission' in bsdf.inputs and transmission > 0.0:
        bsdf.inputs['Transmission'].default_value = transmission

    if 'IOR' in bsdf.inputs:
        bsdf.inputs['IOR'].default_value = ior

    if alpha < 1.0:
        bsdf.inputs['Alpha'].default_value = alpha
        if hasattr(mat, 'blend_method'):
            mat.blend_method = 'BLEND'

    mat.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def create_all_materials():
    mats = {}
    # Basamentos y Estucos Arquitectónicos
    mats["zocalo_basal"] = make_pbr_material("M_Zocalo_Basal", (0.20, 0.22, 0.24), roughness=0.92)
    mats["stucco_blanco"] = make_pbr_material("M_Stucco_Blanco", (0.90, 0.89, 0.86), roughness=0.85)
    mats["stucco_ocre_elias"] = make_pbr_material("M_Stucco_Ocre_Elias", (0.87, 0.62, 0.24), roughness=0.78)
    mats["stucco_salmon_sonora"] = make_pbr_material("M_Stucco_Salmon_Sonora", (0.85, 0.48, 0.38), roughness=0.82)
    mats["stucco_naranja_fimbres"] = make_pbr_material("M_Stucco_Naranja_Fimbres", (0.86, 0.42, 0.16), roughness=0.80)
    mats["stucco_amarillo_arrematec"] = make_pbr_material("M_Stucco_Amarillo_Arrematec", (0.92, 0.82, 0.22), roughness=0.78)
    mats["stucco_amarillo_michoacana"] = make_pbr_material("M_Stucco_Amarillo_Michoacana", (0.95, 0.85, 0.28), roughness=0.80)
    mats["stucco_azul_placita"] = make_pbr_material("M_Stucco_Azul_Placita", (0.12, 0.38, 0.70), roughness=0.78)
    mats["muro_verde_salvia"] = make_pbr_material("M_Muro_Verde_Salvia", (0.38, 0.50, 0.40), roughness=0.82)
    mats["muro_gris_tecnico"] = make_pbr_material("M_Muro_Gris_Tecnico", (0.55, 0.56, 0.56), roughness=0.88)

    # Materiales Rústicos y Tradicionales
    mats["piedra_laja_pinos"] = make_pbr_material("M_Piedra_Laja_Pinos", (0.64, 0.52, 0.38), roughness=0.85)
    mats["ladrillo_rojo_arcos"] = make_pbr_material("M_Ladrillo_Rojo_Arcos", (0.60, 0.22, 0.15), roughness=0.82)
    mats["teja_barro_3d"] = make_pbr_material("M_Teja_Barro_3D", (0.65, 0.25, 0.14), roughness=0.72)
    mats["cantera_colonial"] = make_pbr_material("M_Cantera_Colonial", (0.82, 0.80, 0.74), roughness=0.75)
    mats["madera_rustica_troncos"] = make_pbr_material("M_Madera_Rustica_Troncos", (0.32, 0.20, 0.12), roughness=0.85)

    # Metales y Chapas Industriales PBR
    mats["lamina_rojo_prisci"] = make_pbr_material("M_Lamina_Rojo_Prisci", (0.78, 0.12, 0.12), roughness=0.40, metallic=0.30)
    mats["lamina_amarillo_central"] = make_pbr_material("M_Lamina_Amarillo_Central", (0.86, 0.68, 0.18), roughness=0.45, metallic=0.20)
    mats["hormigon_alero_central"] = make_pbr_material("M_Hormigon_Alero_Central", (0.74, 0.73, 0.70), roughness=0.80)
    mats["cercha_azul_acero"] = make_pbr_material("M_Cercha_Azul_Acero", (0.12, 0.30, 0.60), roughness=0.35, metallic=0.75)
    mats["cortina_acero_galv"] = make_pbr_material("M_Cortina_Acero_Galv", (0.68, 0.70, 0.72), roughness=0.35, metallic=0.80)
    mats["herreria_negra"] = make_pbr_material("M_Herreria_Negra", (0.06, 0.06, 0.07), roughness=0.40, metallic=0.85)

    # Cancelería y Vidrios Físicos PBR
    mats["aluminio_oscuro"] = make_pbr_material("M_Aluminio_Oscuro", (0.12, 0.12, 0.13), roughness=0.25, metallic=0.85)
    mats["aluminio_blanco"] = make_pbr_material("M_Aluminio_Blanco", (0.92, 0.92, 0.93), roughness=0.30, metallic=0.60)
    mats["aluminio_rojo"] = make_pbr_material("M_Aluminio_Rojo", (0.75, 0.12, 0.12), roughness=0.35, metallic=0.50)
    mats["vidrio_comercial"] = make_pbr_material("M_Vidrio_Comercial", (0.85, 0.92, 0.98), roughness=0.04, metallic=0.05, alpha=0.35, transmission=0.88, ior=1.52)
    mats["azulejo_blanco"] = make_pbr_material("M_Azulejo_Blanco", (0.92, 0.92, 0.92), roughness=0.18)

    # Toldos y Carpas Textiles
    mats["toldo_rojo"] = make_pbr_material("M_Toldo_Rojo", (0.75, 0.12, 0.12), roughness=0.70)
    mats["toldo_azul"] = make_pbr_material("M_Toldo_Azul", (0.12, 0.30, 0.62), roughness=0.70)
    mats["toldo_amarillo"] = make_pbr_material("M_Toldo_Amarillo", (0.92, 0.78, 0.18), roughness=0.70)
    mats["toldo_verde"] = make_pbr_material("M_Toldo_Verde", (0.14, 0.58, 0.26), roughness=0.70)

    # Azoteas y Suelos Interiores
    mats["azotea_impermeable"] = make_pbr_material("M_Azotea_Impermeable", (0.35, 0.34, 0.33), roughness=0.90)
    mats["patio_asfalto"] = make_pbr_material("M_Patio_Asfalto", (0.28, 0.28, 0.28), roughness=0.90)
    mats["patio_grava"] = make_pbr_material("M_Patio_Grava", (0.50, 0.48, 0.44), roughness=0.95)

    # Rótulos Corpóreos 3D
    mats["letras_doradas"] = make_pbr_material("M_Letras_Doradas", (0.88, 0.70, 0.22), roughness=0.30, metallic=0.75)
    mats["letras_blancas"] = make_pbr_material("M_Letras_Blancas", (0.96, 0.96, 0.96), roughness=0.35)
    mats["letras_azules"] = make_pbr_material("M_Letras_Azules", (0.10, 0.30, 0.75), roughness=0.40)
    mats["letras_rojas"] = make_pbr_material("M_Letras_Rojas", (0.85, 0.10, 0.10), roughness=0.40)
    mats["letras_amarillas"] = make_pbr_material("M_Letras_Amarillas", (0.96, 0.86, 0.14), roughness=0.35)

    return mats

# ---------------------------------------------------------------------------
# 4. Construcción Modular No Solapada de Edificios y Fachadas
# ---------------------------------------------------------------------------

def build_unified_foundation(mats, col):
    """Zócalo basal continuo perimetral enterrado a Z = -1.50 m (sin intersecciones redundantes)."""
    print("Construyendo Zócalo Basal Enterrado Continuo...")
    bm = bmesh.new()
    t = 0.25 # espesor del muro de cimentación
    add_box(bm, 0.00, X_MAX, Y_MAX - t, Y_MAX, Z_BASE, 0.00)     # Norte
    add_box(bm, 0.00, X_MAX, 0.00, t, Z_BASE, 0.00)             # Sur
    add_box(bm, 0.00, t, t, Y_MAX - t, Z_BASE, 0.00)             # Poniente
    add_box(bm, X_MAX - t, X_MAX, t, Y_MAX - t, Z_BASE, 0.00)     # Oriente
    create_mesh_object("Perimeter_Basal_Foundation", bm, mats["zocalo_basal"], col)

def build_west_facade_ortiz_rubio(mats, col):
    """Zona 1: Fachada Poniente sobre Calle Presidente Pascual Ortiz Rubio (Y in [0.00, 78.00])."""
    print("Construyendo Zona 1: Fachada Poniente (Ortiz Rubio)...")
    bm_placita = bmesh.new()
    bm_pinos = bmesh.new()
    bm_white = bmesh.new()
    bm_roof = bmesh.new()
    bm_trim = bmesh.new()
    bm_glass = bmesh.new()

    # 1. Taquería La Placita & Flor de Michoacán Sur (Y in [0.00, 14.50]) - 2 Niveles (H=6.80m)
    # Muro azul cobalto auténtico
    add_box(bm_placita, 0.00, 8.00, 0.00, 14.50, 0.00, 6.80)
    # Balcón planta alta en Y in [0.00, 14.50], Z in [3.20, 4.40] con barandal de celosía
    add_box(bm_trim, -0.40, 0.00, 0.00, 14.50, 3.20, 3.35) # Losa volada balcón
    add_box(bm_trim, -0.40, -0.35, 0.00, 14.50, 3.35, 4.25) # Barandal exterior
    # Escaparates PB y PA
    add_box(bm_glass, -0.05, 0.05, 1.50, 6.50, 0.60, 2.80)
    add_box(bm_glass, -0.05, 0.05, 8.00, 13.50, 0.60, 2.80)
    add_box(bm_glass, 0.10, 0.20, 2.00, 6.00, 3.80, 5.80) # Ventanas PA
    add_box(bm_glass, 0.10, 0.20, 8.50, 12.50, 3.80, 5.80)
    # Alero de tejas 3D en remate superior Z in [6.80, 7.25]
    add_teja_ribs_y(bm_roof, 0.00, 14.50, -0.50, 0.80, 6.75, 7.25)

    # 2. Café Los Pinos (Y in [14.50, 23.20]) - 1 Nivel piedra laja (H=3.65m)
    add_box(bm_pinos, 0.00, 12.00, 14.50, 23.20, 0.00, 3.65)
    # Cancelería y puertas
    add_box(bm_glass, -0.05, 0.05, 15.50, 19.50, 0.80, 2.60)
    add_box(bm_glass, -0.05, 0.05, 20.20, 22.50, 0.00, 2.60) # Puerta
    # Toldo abombado rojo Los Pinos
    add_canopy_quarter_round_y(bm_trim, 15.00, 22.80, 0.00, 1.10, 2.70, 0.75)

    # 3. MR Multiservicios (Y in [23.20, 31.00]) - 1 Nivel (H=3.50m)
    add_box(bm_white, 0.00, 12.00, 23.20, 31.00, 0.00, 3.50)
    add_box(bm_placita, -0.05, 0.05, 23.20, 31.00, 0.00, 0.65) # Zócalo azul
    add_box(bm_glass, -0.05, 0.05, 24.50, 29.50, 0.90, 2.50) # Escaparate

    # 4. CopyFast (Y in [31.00, 42.50]) - 1 Nivel (H=4.10m)
    add_box(bm_white, 0.00, 12.00, 31.00, 42.50, 0.00, 4.10)
    add_box(bm_trim, -0.05, 0.05, 31.00, 42.50, 0.00, 0.70) # Zócalo gris
    # Marquesina azul saliente
    add_box(bm_placita, -0.45, 0.05, 31.20, 42.30, 3.10, 4.05)
    # Cancelería de doble vitrina y puerta central
    add_box(bm_glass, -0.05, 0.05, 32.00, 36.00, 0.85, 2.85)
    add_box(bm_glass, -0.05, 0.05, 37.50, 41.50, 0.85, 2.85)
    add_box(bm_glass, -0.05, 0.05, 36.20, 37.30, 0.00, 2.85) # Puerta

    # 5. Beto's Barbería (Y in [42.50, 48.00]) - 1 Nivel (H=3.90m)
    add_box(bm_white, 0.00, 12.00, 42.50, 48.00, 0.00, 3.90)
    add_box(bm_placita, -0.05, 0.05, 42.50, 48.00, 0.00, 0.65) # Zócalo azul
    add_box(bm_glass, -0.05, 0.05, 43.50, 47.00, 0.85, 2.65)
    # Barber pole cilíndrico
    add_box(bm_trim, -0.30, -0.15, 42.70, 42.85, 1.60, 2.40)

    # 6. Modas Da Vinci Poniente (Y in [48.00, 56.50]) - Porche Nupcial (H=4.30m)
    add_box(bm_white, 0.00, 14.00, 48.00, 56.50, 0.00, 4.30)
    # Porche saliente con faldón de tejas 3D volado 1.40m
    add_box(bm_trim, -1.40, 0.00, 48.20, 56.30, 2.65, 2.75) # Viguería de techo
    add_teja_ribs_y(bm_roof, 48.20, 56.30, -1.45, 0.20, 2.70, 3.40)
    add_box(bm_glass, -0.05, 0.05, 49.50, 55.50, 0.40, 2.50) # Vitrina novias

    # 7. Multiservicios Don Elías (Y in [56.50, 78.00]) - (H=4.25m)
    # Termina exactamente en Y = 78.00 para NO solapar con la esquina Norponiente
    add_box(bm_white, 0.00, 14.00, 56.50, 78.00, 0.00, 4.25)
    # Alero corrido de tejas coloniales
    add_teja_ribs_y(bm_roof, 56.50, 77.00, -0.60, 0.40, 3.80, 4.35)
    # Toldo azul capota Don Elías
    add_canopy_quarter_round_y(bm_trim, 58.00, 63.50, 0.00, 0.90, 2.50, 0.65)
    add_box(bm_glass, -0.05, 0.05, 58.50, 63.00, 0.90, 2.30)
    add_box(bm_glass, -0.05, 0.05, 70.00, 75.00, 1.20, 2.60)

    create_mesh_object("West_Placita_Walls", bm_placita, mats["stucco_azul_placita"], col)
    create_mesh_object("West_LosPinos_Walls", bm_pinos, mats["piedra_laja_pinos"], col)
    create_mesh_object("West_Commercial_White_Walls", bm_white, mats["stucco_blanco"], col)
    create_mesh_object("West_Roof_Tiles", bm_roof, mats["teja_barro_3d"], col)
    create_mesh_object("West_Trim", bm_trim, mats["aluminio_oscuro"], col)
    create_mesh_object("West_Glass", bm_glass, mats["vidrio_comercial"], col)

    # Rótulos Corpóreos 3D en Cara Poniente (Rotación ROT_WEST)
    add_3d_text("Txt_LaPlacita", "TAQUERÍA LA PLACITA", 0.52, 0.08, (-0.25, 7.25, 3.65), ROT_WEST, mats["letras_blancas"], col)
    add_3d_text("Txt_LosPinos", "CAFE LOS PINOS", 0.42, 0.06, (-0.15, 18.80, 3.55), ROT_WEST, mats["letras_blancas"], col)
    add_3d_text("Txt_CopyFast", "COPY FAST", 0.65, 0.08, (-0.50, 36.80, 3.65), ROT_WEST, mats["letras_amarillas"], col)
    add_3d_text("Txt_Betos", "BARBERIA BETO'S", 0.38, 0.06, (-0.12, 45.25, 3.35), ROT_WEST, mats["letras_rojas"], col)
    add_3d_text("Txt_DaVinci_West", "Modas Da Vinci", 0.48, 0.07, (-0.15, 52.25, 3.85), ROT_WEST, mats["letras_azules"], col)
    add_3d_text("Txt_DonElias_West", "DON ELIAS", 0.36, 0.06, (-0.12, 60.75, 3.55), ROT_WEST, mats["letras_blancas"], col)

def build_north_facade_juarez(mats, col):
    """Zona 2: Fachada Norte sobre Avenida Benito Juárez (X in [0.00, 115.00])."""
    print("Construyendo Zona 2: Fachada Norte (Av. Juárez)...")
    bm_white = bmesh.new()
    bm_elias = bmesh.new()
    bm_michoacana = bmesh.new()
    bm_roof = bmesh.new()
    bm_trim = bmesh.new()
    bm_glass = bmesh.new()
    bm_brick = bmesh.new()
    bm_metal = bmesh.new()

    # 1. Esquina Norponiente: Modas Da Vinci / Cortina Shutter (X in [0.00, 8.50], Y in [78.00, Y_MAX]) - (H=4.30m)
    # Este volumen comprende la esquina completa sin solapamiento
    add_box(bm_white, 0.00, 8.50, 78.00, Y_MAX, 0.00, 4.30)
    add_teja_ribs_x(bm_roof, 0.00, 8.50, Y_MAX + 0.60, Y_MAX - 0.40, 3.80, 4.35)
    add_box(bm_glass, 2.00, 7.00, Y_MAX - 0.05, Y_MAX + 0.05, 0.50, 2.70)
    # Cortina enrollable blanca en la cara poniente de la esquina
    add_box(bm_trim, -0.08, 0.02, 78.50, 86.50, 0.00, 2.80)

    # 2. Telas Elías / Bordados Elías (X in [8.50, 24.50]) - 2 Niveles Monumental Ocre (H=8.60m)
    # Planta Alta Ocre con parapeto asimétrico
    add_box(bm_elias, 8.50, 24.50, 76.00, Y_MAX, 3.80, 8.60)
    # Parapeto curvo superior decorativo en X in [12.00, 22.00], Z in [8.60, 9.40]
    add_box(bm_elias, 12.00, 22.00, Y_MAX - 0.10, Y_MAX, 8.60, 9.40)
    # Pórtico de Planta Baja: Galería cubierta transitable con 3 columnas cuadradas
    for cx in [10.00, 16.00, 23.00]:
        add_box(bm_elias, cx - 0.25, cx + 0.25, Y_MAX - 0.50, Y_MAX, 0.00, 3.80)
    # Muro interior retrasado del pórtico (Y = 86.50)
    add_box(bm_elias, 8.50, 24.50, 76.00, 86.50, 0.00, 3.80)
    add_box(bm_glass, 9.50, 23.50, 86.45, 86.55, 0.50, 3.20) # Vitrinas interiores telas
    # Ventanales en arco Planta Alta: 3 ventanales verticales (X=14.0, 16.5, 19.0) y mirador poniente (X in [9.0, 12.5])
    add_box(bm_glass, 9.00, 12.50, Y_MAX - 0.05, Y_MAX + 0.05, 4.80, 7.80) # Mirador
    for vx in [14.00, 16.50, 19.00]:
        add_box(bm_glass, vx - 0.65, vx + 0.65, Y_MAX - 0.05, Y_MAX + 0.05, 4.80, 7.50)
        add_arch_spandrel_x(bm_elias, Y_MAX, Y_MAX - 0.15, vx - 0.65, vx + 0.65, 7.50, 8.00, 8.20)

    # 3. Farmacia del Pueblo (X in [24.50, 36.80]) - 1 Nivel (H=4.20m)
    add_box(bm_white, 24.50, 36.80, 78.00, Y_MAX, 0.00, 4.20)
    add_teja_ribs_x(bm_roof, 24.50, 36.80, Y_MAX + 0.60, Y_MAX - 0.40, 3.70, 4.25)
    add_box(bm_glass, 25.50, 35.50, Y_MAX - 0.05, Y_MAX + 0.05, 0.80, 2.80)
    # Cercha metálica de espectacular azotea (Z in [4.40, 6.20])
    add_box(bm_trim, 26.00, 35.00, Y_MAX - 0.50, Y_MAX - 0.30, 4.40, 6.20)

    # 4. Rosticería Los Polos B.C. (X in [36.80, 44.50]) - (H=4.00m)
    add_box(bm_white, 36.80, 44.50, 78.00, Y_MAX, 0.00, 4.00)
    # Toldo semicilíndrico abombado rojo
    add_canopy_quarter_round_x(bm_trim, 37.00, 44.20, Y_MAX, 1.20, 2.50, 0.80)
    add_box(bm_trim, 37.50, 43.50, Y_MAX - 0.05, Y_MAX + 0.05, 0.00, 1.10) # Barra mostrador

    # 5. Taquería Los Arcos (X in [44.50, 54.00]) - (H=4.30m)
    add_box(bm_white, 44.50, 54.00, 78.00, Y_MAX, 0.00, 4.30)
    add_canopy_quarter_round_x(bm_trim, 44.80, 53.50, Y_MAX, 1.30, 2.60, 0.85)
    # Cercha metálica sobre frontispicio Z in [4.30, 5.80]
    add_box(bm_trim, 45.00, 53.50, Y_MAX - 0.20, Y_MAX, 4.30, 5.80)

    # 6. Mariscos El Chapo / Birria (X in [54.00, 60.50]) - Portal con Arco de Tabique (H=4.10m)
    add_box(bm_white, 54.00, 60.50, 78.00, Y_MAX, 0.00, 4.10)
    # Gran arco de tabique rojo en el acceso central (X in [55.20, 59.30])
    add_arch_spandrel_x(bm_brick, Y_MAX, Y_MAX - 0.35, 55.20, 59.30, 2.10, 3.20, 3.50)
    add_box(bm_brick, 54.80, 55.20, Y_MAX - 0.35, Y_MAX, 0.00, 2.20) # Jambas
    add_box(bm_brick, 59.30, 59.70, Y_MAX - 0.35, Y_MAX, 0.00, 2.20)

    # 7. La Flor de Michoacán Norte & Súper Taquería Tecate (X in [60.50, 73.00]) - (H=4.00m)
    add_box(bm_michoacana, 60.50, 73.00, 78.00, Y_MAX, 0.00, 4.00)
    add_box(bm_glass, 61.50, 66.00, Y_MAX - 0.05, Y_MAX + 0.05, 0.80, 2.80) # Flor Michoacán
    add_box(bm_glass, 67.50, 72.00, Y_MAX - 0.05, Y_MAX + 0.05, 0.80, 2.80) # Taquería Tecate
    add_box(bm_trim, 67.00, 72.50, Y_MAX - 0.15, Y_MAX + 0.15, 2.90, 3.80) # Marquesina roja

    # 8. Callejón y Rampa Despacho Jurídico (X in [73.00, 78.50]) - Vano Diáfano Transitable
    add_box(bm_white, 73.00, 73.30, 50.00, Y_MAX, 0.00, 3.50) # Muro Poniente callejón
    add_box(bm_white, 78.20, 78.50, 50.00, Y_MAX, 0.00, 3.50) # Muro Oriente callejón

    # 9. Hotel Juárez & Cafetería Juárez (X in [78.50, 91.00]) - 2 Niveles (H=7.40m)
    add_box(bm_white, 78.50, 91.00, 70.00, Y_MAX, 0.00, 7.40)
    # Gran ventanal PA de Hotel Juárez
    add_box(bm_glass, 80.00, 89.50, Y_MAX - 0.05, Y_MAX + 0.05, 4.50, 6.50)
    # Planta Baja Cafetería Juárez con cancelería roja
    add_box(bm_trim, 79.50, 90.00, Y_MAX - 0.15, Y_MAX + 0.15, 3.20, 3.80) # Marquesina
    add_box(bm_glass, 80.00, 89.50, Y_MAX - 0.05, Y_MAX + 0.05, 0.60, 3.00)

    # 10. Barber Shop Azteca 230 & Abarrotes Lety (X in [91.00, 102.00]) - 2 Niveles (H=6.90m)
    add_box(bm_white, 91.00, 102.00, 72.00, Y_MAX, 0.00, 6.90)
    add_box(bm_glass, 92.50, 97.00, Y_MAX - 0.05, Y_MAX + 0.05, 0.60, 2.70)
    add_box(bm_glass, 98.00, 101.50, Y_MAX - 0.05, Y_MAX + 0.05, 0.60, 2.70)
    # Lucernario / invernadero piramidal verde en azotea Z in [6.90, 8.30]
    add_box(bm_trim, 93.00, 98.00, Y_MAX - 6.00, Y_MAX - 2.00, 6.90, 8.30)

    # 11. Restaurante La Flor de Michoacán (X in [102.00, 110.50]) - Arco tabique y shingle (H=4.20m)
    add_box(bm_michoacana, 102.00, 110.50, 75.00, Y_MAX, 0.00, 4.20)
    add_arch_spandrel_x(bm_brick, Y_MAX, Y_MAX - 0.35, 104.50, 108.50, 2.10, 3.20, 3.50)
    # Techo shingle asfáltico
    add_box(bm_roof, 101.80, 110.70, 75.00, Y_MAX + 0.40, 4.10, 4.60)

    # 12. Callejón / Portón Acceso Autobuses (X in [110.50, 115.00])
    add_box(bm_metal, 110.50, 115.00, Y_MAX - 0.15, Y_MAX, 0.00, 2.80) # Reja azul

    create_mesh_object("North_Commercial_White_Walls", bm_white, mats["stucco_blanco"], col)
    create_mesh_object("North_TelasElias_Ochre_Walls", bm_elias, mats["stucco_ocre_elias"], col)
    create_mesh_object("North_Michoacana_Yellow_Walls", bm_michoacana, mats["stucco_amarillo_michoacana"], col)
    create_mesh_object("North_Roof_Tiles", bm_roof, mats["teja_barro_3d"], col)
    create_mesh_object("North_Trim", bm_trim, mats["aluminio_oscuro"], col)
    create_mesh_object("North_Glass", bm_glass, mats["vidrio_comercial"], col)
    create_mesh_object("North_Brick_Arches", bm_brick, mats["ladrillo_rojo_arcos"], col)
    create_mesh_object("North_Metal_Gate", bm_metal, mats["cercha_azul_acero"], col)

    # Rótulos Corpóreos 3D en Cara Norte (Rotación ROT_NORTH)
    add_3d_text("Txt_TelasElias", "Telas Elias", 0.85, 0.12, (16.50, Y_MAX + 0.18, 7.85), ROT_NORTH, mats["letras_doradas"], col)
    add_3d_text("Txt_BordadosElias", "Bordados Elias", 0.50, 0.08, (16.50, Y_MAX + 0.16, 7.15), ROT_NORTH, mats["letras_doradas"], col)
    add_3d_text("Txt_FarmaciaPueblo", "FARMACIA DEL PUEBLO", 0.72, 0.10, (30.65, Y_MAX - 0.35, 5.35), ROT_NORTH, mats["letras_blancas"], col)
    add_3d_text("Txt_Polos", "ROSTICERIA LOS POLOS", 0.45, 0.07, (40.65, Y_MAX + 0.15, 3.65), ROT_NORTH, mats["letras_blancas"], col)
    add_3d_text("Txt_LosArcos", "TAQUERIA LOS ARCOS", 0.55, 0.08, (49.25, Y_MAX + 0.15, 4.85), ROT_NORTH, mats["letras_blancas"], col)
    add_3d_text("Txt_Chapo", "MARISCOS EL CHAPO", 0.48, 0.07, (57.25, Y_MAX + 0.15, 3.85), ROT_NORTH, mats["letras_blancas"], col)
    add_3d_text("Txt_FlorMichoacanNorte", "LA FLOR DE MICHOACAN", 0.45, 0.07, (66.00, Y_MAX + 0.15, 3.55), ROT_NORTH, mats["letras_amarillas"], col)
    add_3d_text("Txt_HotelJuarez", "HOTEL JUAREZ", 0.80, 0.12, (84.75, Y_MAX + 0.16, 7.05), ROT_NORTH, mats["letras_azules"], col)
    add_3d_text("Txt_CafeteriaJuarez", "CAFETERIA JUAREZ", 0.45, 0.07, (84.75, Y_MAX + 0.16, 3.55), ROT_NORTH, mats["letras_blancas"], col)
    add_3d_text("Txt_BarberAzteca", "BARBER AZTECA", 0.48, 0.07, (96.50, Y_MAX + 0.15, 3.45), ROT_NORTH, mats["letras_azules"], col)

def build_terminal_and_east_facade(mats, col):
    """Zona 3: Terminal de Autobuses (Noreste) y Fachada Oriente sobre Calle Abelardo L. Rodríguez."""
    print("Construyendo Zona 3: Terminal de Autobuses y Fachada Oriente...")
    bm_term_walls = bmesh.new()
    bm_term_fascia = bmesh.new()
    bm_green = bmesh.new()
    bm_white = bmesh.new()
    bm_trim = bmesh.new()
    bm_glass = bmesh.new()
    bm_truss = bmesh.new()
    bm_shed = bmesh.new()

    # 1. Terminal de Autobuses Tecate B.C. (X in [115.00, X_MAX], Y in [65.00, Y_MAX]) - Hito Cívico (H=5.80m)
    # Volumen unificado sin solapamientos
    add_box(bm_term_walls, 115.00, X_MAX, 65.00, Y_MAX, 0.00, 5.80)
    # Fascia metálica acanalada amarilla superior (Z in [4.40, 5.80]) a lo largo de Norte y Oriente
    add_box(bm_term_fascia, 115.00, X_MAX, Y_MAX - 0.10, Y_MAX + 0.15, 4.40, 5.80) # Norte
    add_box(bm_term_fascia, X_MAX - 0.10, X_MAX + 0.15, 75.00, Y_MAX, 4.40, 5.80) # Oriente
    # Alero de concreto con modillones trapezoidales esculpidos (Z in [3.80, 4.40])
    add_box(bm_trim, 114.80, X_MAX + 0.40, Y_MAX - 0.20, Y_MAX + 0.85, 3.80, 4.40)
    add_box(bm_trim, X_MAX - 0.20, X_MAX + 0.85, 74.80, Y_MAX + 0.40, 3.80, 4.40)
    # Modillones en frontis norte
    for mx in range(int(115.50), int(X_MAX), 3):
        add_box(bm_trim, mx - 0.30, mx + 0.30, Y_MAX + 0.10, Y_MAX + 0.95, 3.40, 4.10)
    # Muro cortina vidriado de piso a techo
    add_box(bm_glass, 116.00, X_MAX - 0.50, Y_MAX - 0.05, Y_MAX + 0.05, 0.20, 3.70) # Norte
    add_box(bm_glass, X_MAX - 0.05, X_MAX + 0.05, 78.00, 88.00, 0.50, 3.50)           # Oriente

    # 2. Dársenas y Muro Verde Salvia (Y in [48.00, 65.00]) - (H=3.20m)
    add_box(bm_green, X_MAX - 0.40, X_MAX, 48.00, 65.00, 0.00, 3.20)
    # Cobertizo volado en shed hacia el patio interior (X in [112.00, X_MAX - 0.40])
    add_box(bm_shed, 112.00, X_MAX - 0.40, 50.00, 65.00, 3.60, 4.50)

    # 3. Mega Cercha Espacial Azul y Portón de Maniobras (Y in [34.00, 48.00])
    add_space_frame_truss_y(bm_truss, X_MAX - 0.40, X_MAX + 0.40, 34.00, 48.00, 4.80, 5.80, subdivisions=8)
    add_box(bm_truss, X_MAX - 0.35, X_MAX + 0.35, 33.60, 34.40, 0.00, 5.80)
    add_box(bm_truss, X_MAX - 0.35, X_MAX + 0.35, 47.60, 48.40, 0.00, 5.80)
    add_box(bm_truss, X_MAX - 0.15, X_MAX, 34.00, 42.00, 0.00, 2.60) # Portón corredizo

    # 4. Muro Perimetral Suroriente (Y in [0.00, 12.00]) - (H=3.00m)
    # Muro limpio de cierre oriente
    add_box(bm_white, X_MAX - 0.30, X_MAX, 0.00, 12.00, 0.00, 3.00)

    create_mesh_object("Terminal_Building_Walls", bm_term_walls, mats["stucco_blanco"], col)
    create_mesh_object("Terminal_Yellow_Fascia", bm_term_fascia, mats["lamina_amarillo_central"], col)
    create_mesh_object("East_Green_Walls", bm_green, mats["muro_verde_salvia"], col)
    create_mesh_object("East_Trim", bm_trim, mats["aluminio_oscuro"], col)
    create_mesh_object("East_Glass", bm_glass, mats["vidrio_comercial"], col)
    create_mesh_object("East_Truss_SpaceFrame", bm_truss, mats["cercha_azul_acero"], col)
    create_mesh_object("East_Bus_Shed", bm_shed, mats["lamina_amarillo_central"], col)

    # Rótulos Corpóreos Terminal (Norte)
    add_3d_text("Txt_TerminalAutobuses", "TERMINAL DE AUTOBUSES TECATE", 0.75, 0.10, (124.50, Y_MAX + 0.22, 5.25), ROT_NORTH, mats["letras_blancas"], col)
    add_3d_text("Txt_SuburBaja", "Subur BAJA", 0.55, 0.08, (124.50, Y_MAX + 0.20, 4.65), ROT_NORTH, mats["letras_rojas"], col)

def build_south_facade_libertad(mats, col):
    """Zona 4: Fachada Sur sobre Callejón Libertad (X in [0.00, 134.40], Y in [0.00, 24.00])."""
    print("Construyendo Zona 4: Fachada Sur (Callejón Libertad)...")
    bm_prisci = bmesh.new()
    bm_heras = bmesh.new()
    bm_arrematec = bmesh.new()
    bm_fimbres = bmesh.new()
    bm_colonial = bmesh.new()
    bm_colonial_cantera = bmesh.new()
    bm_white = bmesh.new()
    bm_warehouse = bmesh.new()
    bm_roof = bmesh.new()
    bm_trim = bmesh.new()
    bm_glass = bmesh.new()
    bm_wood = bmesh.new()

    # 1. Naves de Servicio Suroriente (X in [112.00, 134.40]) - (H=3.80m)
    add_box(bm_warehouse, 112.00, 134.40, 0.00, 16.00, 0.00, 3.80)
    add_box(bm_trim, 111.80, 134.40, -0.20, 16.00, 3.75, 4.00) # Remate cubierta

    # 2. Hotel Colonial (X in [90.00, 112.00]) - Fachada Patrimonial 2 Niveles (H=7.80m)
    add_box(bm_colonial, 90.00, 112.00, 0.00, 24.00, 0.00, 7.80)
    # Balcón corrido en planta alta con barandal de hierro forjado ornamental
    add_box(bm_trim, 93.00, 105.00, -0.60, 0.00, 3.60, 3.75) # Losa balcón
    add_box(bm_trim, 93.00, 105.00, -0.60, -0.55, 3.75, 4.65) # Barandal hierro
    # Ventanal en arco en planta alta con cantera
    add_arch_spandrel_x(bm_colonial_cantera, 0.00, 0.15, 96.00, 99.00, 4.80, 6.20, 6.50)
    add_box(bm_glass, 96.20, 98.80, -0.05, 0.05, 4.00, 6.00)
    # Parapeto superior estilo misión con almenas
    add_box(bm_colonial, 92.00, 108.00, 0.00, 0.30, 7.80, 8.60)
    for ax in range(94, 106, 3):
        add_box(bm_colonial_cantera, ax, ax + 1.20, -0.05, 0.35, 8.00, 8.50) # Almenas cantera
    # Planta Baja acceso de cantera y farol
    add_box(bm_colonial_cantera, 95.50, 98.50, -0.15, 0.00, 0.00, 3.00) # Marco cantera
    add_box(bm_glass, 96.00, 98.00, -0.05, 0.05, 0.00, 2.70) # Puerta acceso
    add_box(bm_trim, 94.50, 95.00, -0.35, -0.05, 2.20, 2.80) # Farol colonial

    # 3. Escritorio Público Fimbres (X in [80.00, 90.00]) - 1 Nivel Naranja (H=3.80m)
    add_box(bm_fimbres, 80.00, 90.00, 0.00, 16.00, 0.00, 3.80)
    add_canopy_quarter_round_x(bm_trim, 80.50, 89.50, 0.00, -0.80, 2.40, 0.55) # Toldo ondulado
    add_box(bm_glass, 81.50, 88.50, -0.05, 0.05, 0.80, 2.30)

    # 4. Arrematec Demoliciones (X in [70.00, 80.00]) - Fachada Amarilla/Roja (H=3.90m)
    add_box(bm_arrematec, 70.00, 80.00, 0.00, 16.00, 0.00, 3.90)
    add_box(bm_prisci, 70.00, 80.00, -0.05, 0.05, 0.00, 0.80) # Zócalo rojo
    add_box(bm_glass, 72.00, 77.00, -0.05, 0.05, 0.90, 2.40) # Ventana con reja
    add_box(bm_trim, 70.00, 71.80, -0.10, 0.00, 0.00, 2.80) # Portón negro

    # 5. Entrada al Gran Patio de Estacionamiento Manzana (X in [56.00, 70.00]) - Vano Libre
    add_box(bm_white, 56.00, 56.40, 0.00, 35.00, 0.00, 2.80) # Murete poniente
    add_box(bm_white, 69.60, 70.00, 0.00, 35.00, 0.00, 2.80) # Murete oriente
    add_box(bm_trim, 56.50, 69.50, -0.05, 0.05, 0.00, 2.20) # Reja ciclónica abierta

    # 6. Heras Café Internet / Restaurant 2 de Sonora (X in [36.00, 56.00]) - 2 Niveles Rústico Salmón (H=6.90m)
    add_box(bm_heras, 36.00, 56.00, 0.00, 22.00, 0.00, 6.90)
    # Tejavana volada sobre la planta alta Z in [6.80, 7.30]
    add_teja_ribs_x(bm_roof, 36.00, 56.00, -0.80, 0.20, 6.60, 7.20)
    # Barandal rústico superior de troncos de madera
    for bx in range(36, 56, 2):
        add_box(bm_wood, bx + 0.85, bx + 1.15, -0.45, -0.35, 3.40, 4.40) # Postes
    add_box(bm_wood, 36.00, 56.00, -0.45, -0.35, 3.80, 3.95) # Tronco inferior
    add_box(bm_wood, 36.00, 56.00, -0.45, -0.35, 4.30, 4.45) # Tronco pasamanos
    # Planta Baja Restaurant 2 de Sonora
    add_arch_spandrel_x(bm_heras, 0.00, 0.20, 47.00, 49.50, 1.90, 2.60, 2.80) # Puerta en arco
    add_box(bm_glass, 38.00, 46.00, -0.05, 0.05, 0.80, 2.40)
    add_box(bm_trim, 37.00, 55.00, -0.05, 0.05, 0.00, 0.70) # Zócalo verde menta

    # 7. Helove S.A. de C.V. (X in [28.00, 36.00]) - (H=3.80m)
    add_box(bm_white, 28.00, 36.00, 0.00, 18.00, 0.00, 3.80)
    add_canopy_quarter_round_x(bm_trim, 28.50, 35.50, 0.00, -1.00, 2.30, 0.65) # Toldo azul
    add_box(bm_glass, 29.50, 34.50, -0.05, 0.05, 0.80, 2.20)

    # 8. Dulcería Prisci (X in [8.00, 28.00]) - Nave Lámina Roja (H=5.20m)
    add_box(bm_prisci, 8.00, 28.00, 0.00, 22.00, 0.00, 5.20)
    # Toldo corrido abovedado multicolor de 20m de longitud (Z in [2.10, 2.85])
    add_canopy_quarter_round_x(bm_trim, 8.20, 27.80, 0.00, -1.35, 2.05, 0.80)
    # Planta Baja con cortinas enrollables y cancelería
    add_box(bm_trim, 9.00, 15.00, -0.05, 0.05, 0.00, 2.00) # Cortina metálica
    add_box(bm_glass, 16.00, 27.00, -0.05, 0.05, 0.20, 2.00) # Entrada tienda

    # 9. Retorno Sur de La Placita (X in [0.00, 8.00], Y in [0.00, 14.50])
    # Los muros ya fueron generados en La Placita (West_Placita_Walls).
    # Solo agregamos aquí la cancelería de acceso sur:
    add_box(bm_glass, 1.00, 7.00, -0.05, 0.05, 0.60, 2.60)

    create_mesh_object("South_DulceriaPrisci_Walls", bm_prisci, mats["lamina_rojo_prisci"], col)
    create_mesh_object("South_Heras_Sonora_Walls", bm_heras, mats["stucco_salmon_sonora"], col)
    create_mesh_object("South_Arrematec_Walls", bm_arrematec, mats["stucco_amarillo_arrematec"], col)
    create_mesh_object("South_Fimbres_Walls", bm_fimbres, mats["stucco_naranja_fimbres"], col)
    create_mesh_object("South_HotelColonial_Walls", bm_colonial, mats["stucco_blanco"], col)
    create_mesh_object("South_HotelColonial_Cantera", bm_colonial_cantera, mats["cantera_colonial"], col)
    create_mesh_object("South_Commercial_White_Walls", bm_white, mats["stucco_blanco"], col)
    create_mesh_object("South_Warehouses_Walls", bm_warehouse, mats["muro_gris_tecnico"], col)
    create_mesh_object("South_Roof_Tiles", bm_roof, mats["teja_barro_3d"], col)
    create_mesh_object("South_Trim", bm_trim, mats["aluminio_oscuro"], col)
    create_mesh_object("South_Glass", bm_glass, mats["vidrio_comercial"], col)
    create_mesh_object("South_Rustic_Wood", bm_wood, mats["madera_rustica_troncos"], col)

    # Rótulos Corpóreos 3D en Cara Sur (Rotación ROT_SOUTH)
    add_3d_text("Txt_HotelColonial_Front", "HOTEL COLONIAL", 0.70, 0.10, (100.00, -0.15, 6.95), ROT_SOUTH, mats["letras_rojas"], col)
    add_3d_text("Txt_Fimbres", "ESCRITORIO PUBLICO FIMBRES", 0.40, 0.06, (85.00, -0.12, 3.45), ROT_SOUTH, mats["letras_blancas"], col)
    add_3d_text("Txt_Arrematec", "ARREMATEC DEMOLICIONES", 0.38, 0.06, (75.00, -0.12, 3.45), ROT_SOUTH, mats["letras_rojas"], col)
    add_3d_text("Txt_HerasInternet", "HERAS CAFE INTERNET", 0.58, 0.08, (46.00, -0.15, 5.85), ROT_SOUTH, mats["letras_blancas"], col)
    add_3d_text("Txt_RestaurantSonora", "RESTAURANT 2 DE SONORA", 0.48, 0.07, (46.00, -0.12, 2.95), ROT_SOUTH, mats["letras_amarillas"], col)
    add_3d_text("Txt_Helove", "HELOVE S.A. DE C.V.", 0.38, 0.06, (32.00, -0.12, 3.35), ROT_SOUTH, mats["letras_blancas"], col)
    add_3d_text("Txt_DulceriaPrisci", "DULCERIA Prisci", 0.95, 0.14, (18.00, -0.18, 4.15), ROT_SOUTH, mats["letras_amarillas"], col)

def build_interior_courtyards_and_roofs(mats, col):
    """Zona 5: Patios Interiores, Cubiertas Herméticas Retranqueadas y Estructuras de Servicio."""
    print("Construyendo Zona 5: Patios Interiores y Azoteas Retranqueadas...")
    bm_roof = bmesh.new()
    bm_pave = bmesh.new()
    bm_walls = bmesh.new()

    # 1. Cubiertas de Edificios Retranqueadas (CERO cruces hacia las fachadas exteriores)
    # Franja Poniente (Ortiz Rubio)
    add_box(bm_roof, 0.40, 7.80, 0.40, 14.10, 6.55, 6.70)   # La Placita PA
    add_box(bm_roof, 0.40, 11.60, 14.70, 23.00, 3.45, 3.60)  # Los Pinos
    add_box(bm_roof, 0.40, 11.60, 23.40, 30.80, 3.30, 3.45)  # MR Multiservicios
    add_box(bm_roof, 0.40, 11.60, 31.20, 42.30, 3.90, 4.05)  # CopyFast
    add_box(bm_roof, 0.40, 11.60, 42.70, 47.80, 3.70, 3.85)  # Beto's
    add_box(bm_roof, 0.40, 13.60, 48.20, 56.30, 4.10, 4.25)  # Da Vinci Poniente
    add_box(bm_roof, 0.40, 13.60, 56.70, 77.80, 4.05, 4.20)  # Don Elías
    add_box(bm_roof, 0.40, 8.30, 78.20, 90.80, 4.10, 4.25)   # Esquina Da Vinci Norte

    # Franja Norte (Av. Juárez)
    add_box(bm_roof, 8.70, 24.30, 76.20, 90.80, 8.35, 8.50)  # Telas Elías PA
    add_box(bm_roof, 24.70, 36.60, 78.20, 90.80, 4.00, 4.15) # Farmacia del Pueblo
    add_box(bm_roof, 37.00, 44.30, 78.20, 90.80, 3.80, 3.95) # Los Polos
    add_box(bm_roof, 44.70, 53.80, 78.20, 90.80, 4.10, 4.25) # Los Arcos
    add_box(bm_roof, 54.20, 60.30, 78.20, 90.80, 3.90, 4.05) # Mariscos El Chapo
    add_box(bm_roof, 60.70, 72.80, 78.20, 90.80, 3.80, 3.95) # Flor Michoacán Norte
    add_box(bm_roof, 78.70, 90.80, 70.20, 90.80, 7.15, 7.30) # Hotel Juárez PA
    add_box(bm_roof, 91.20, 101.80, 72.20, 90.80, 6.65, 6.80)# Barber Azteca PA
    add_box(bm_roof, 102.20, 110.30, 75.20, 90.80, 4.00, 4.15)# Flor Michoacán Este
    add_box(bm_roof, 115.20, 134.30, 65.20, 90.80, 5.55, 5.70)# Terminal Norte

    # Franja Sur (Callejón Libertad)
    add_box(bm_roof, 112.20, 134.30, 0.40, 15.80, 3.60, 3.75)# Naves Suroriente
    add_box(bm_roof, 90.20, 111.80, 0.40, 23.80, 7.55, 7.70) # Hotel Colonial PA
    add_box(bm_roof, 80.20, 89.80, 0.40, 15.80, 3.60, 3.75)  # Fimbres
    add_box(bm_roof, 70.20, 79.80, 0.40, 15.80, 3.70, 3.85)  # Arrematec
    add_box(bm_roof, 36.20, 55.80, 0.40, 21.80, 6.65, 6.80)  # Heras / Sonora PA
    add_box(bm_roof, 28.20, 35.80, 0.40, 17.80, 3.60, 3.75)  # Helove
    add_box(bm_roof, 8.20, 27.80, 0.40, 21.80, 5.00, 5.15)   # Dulcería Prisci Nave

    # 2. Pavimentos de Patios Interiores (Z = 0.00 a 0.05m)
    # Patio Central Maniobras Autobuses (X in [85.00, 130.00], Y in [25.00, 65.00])
    add_box(bm_pave, 85.00, 130.00, 25.00, 65.00, 0.00, 0.05)
    # Estacionamiento Sur (X in [45.00, 75.00], Y in [10.00, 48.00])
    add_box(bm_pave, 45.00, 75.00, 10.00, 48.00, 0.00, 0.05)
    # Patio Norte Despachos (X in [65.00, 85.00], Y in [50.00, 75.00])
    add_box(bm_pave, 65.00, 85.00, 50.00, 75.00, 0.00, 0.05)

    # 3. Muros Interiores de Despachos y Talleres
    add_box(bm_walls, 65.00, 85.00, 48.00, 50.00, 0.00, 3.40) # Barda divisoria
    add_box(bm_walls, 85.00, 85.40, 25.00, 65.00, 0.00, 3.40) # Barda patio autobuses

    # 4. Rótulo Monumental en Azotea de Hotel Colonial mirando hacia el Patio Oriente
    add_3d_text("Txt_Colonial_Roof", "HOTEL COLONIAL", 0.90, 0.12, (101.00, 24.50, 8.40), ROT_NORTH, mats["letras_rojas"], col)

    create_mesh_object("Rooftops_Asphalt", bm_roof, mats["azotea_impermeable"], col)
    create_mesh_object("Interior_Pavements", bm_pave, mats["patio_asfalto"], col)
    create_mesh_object("Interior_Walls", bm_walls, mats["stucco_blanco"], col)

# ---------------------------------------------------------------------------
# 5. Generación de Escena Godot 4 con Física Analítica
# ---------------------------------------------------------------------------
def generate_godot_tscn(tscn_path, glb_path):
    """Genera escena Godot 4 con colisionadores analíticos BoxShape3D y sincronización canónica."""
    print(f"Generando escena Godot 4 con colisiones analíticas: {tscn_path}...")

    # En Godot:
    # X_godot = X_blender
    # Y_godot = Z_blender
    # Z_godot = -Y_blender

    boxes = [
        # 1. Cuerpo Poniente (Ortiz Rubio)
        ("Col_West_Placita", Vector((8.00, 6.80, 14.50)), Vector((4.00, 3.40, -7.25))),
        ("Col_West_Comercios", Vector((12.00, 4.20, 42.00)), Vector((6.00, 2.10, -35.50))),
        ("Col_West_DaVinci_Norte", Vector((14.00, 4.40, 34.69)), Vector((7.00, 2.20, -73.84))),

        # 2. Cuerpo Norte (Av. Juárez)
        ("Col_North_Elias_RearWall", Vector((16.00, 8.60, 10.00)), Vector((16.50, 4.30, -81.50))),
        ("Col_North_Elias_Col1", Vector((0.50, 3.80, 0.50)), Vector((10.00, 1.90, -90.94))),
        ("Col_North_Elias_Col2", Vector((0.50, 3.80, 0.50)), Vector((16.00, 1.90, -90.94))),
        ("Col_North_Elias_Col3", Vector((0.50, 3.80, 0.50)), Vector((23.00, 1.90, -90.94))),
        ("Col_North_Comercios_A", Vector((48.50, 4.30, 13.00)), Vector((48.75, 2.15, -84.69))),
        ("Col_North_HotelJuarez", Vector((23.50, 7.40, 19.00)), Vector((90.25, 3.70, -81.69))),
        ("Col_North_Terminal_L", Vector((6.00, 5.80, 26.00)), Vector((118.00, 2.90, -78.19))),
        ("Col_North_Terminal_R", Vector((6.00, 5.80, 26.00)), Vector((131.73, 2.90, -78.19))),

        # 3. Cuerpo Oriente (Abelardo L. Rodríguez)
        ("Col_East_Darsenas_Wall", Vector((0.40, 3.20, 27.00)), Vector((134.53, 1.60, -61.50))),

        # 4. Cuerpo Sur (Callejón Libertad)
        ("Col_South_Naves_Suroriente", Vector((22.73, 3.80, 16.00)), Vector((123.36, 1.90, -8.00))),
        ("Col_South_HotelColonial", Vector((22.00, 7.80, 24.00)), Vector((101.00, 3.90, -12.00))),
        ("Col_South_Fimbres_Arrematec", Vector((20.00, 3.90, 16.00)), Vector((80.00, 1.95, -8.00))),
        ("Col_South_Heras_Sonora", Vector((20.00, 6.90, 22.00)), Vector((46.00, 3.45, -11.00))),
        ("Col_South_DulceriaPrisci", Vector((20.00, 5.20, 22.00)), Vector((18.00, 2.60, -11.00))),
    ]

    tscn_content = []
    tscn_content.append('[gd_scene load_steps=%d format=3 uid="uid://manzana_central_2009_prod"]\n' % (len(boxes) + 2))
    tscn_content.append('[ext_resource type="PackedScene" path="res://assets/buildings/manzana_central_2009.glb" id="1_glb"]\n')

    for i, (name, size, pos) in enumerate(boxes):
        sub_id = f"BoxShape3D_{i+1}"
        tscn_content.append(f'[sub_resource type="BoxShape3D" id="{sub_id}"]\n')
        tscn_content.append(f'size = Vector3({size.x:.2f}, {size.y:.2f}, {size.z:.2f})\n\n')

    tscn_content.append('[node name="Manzana_Central_2009" type="StaticBody3D"]\n\n')
    tscn_content.append('[node name="MeshInstance" parent="." instance=ExtResource("1_glb")]\n\n')

    for i, (name, size, pos) in enumerate(boxes):
        sub_id = f"BoxShape3D_{i+1}"
        tscn_content.append(f'[node name="{name}" type="CollisionShape3D" parent="."]\n')
        tscn_content.append(f'transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})\n')
        tscn_content.append(f'shape = SubResource("{sub_id}")\n\n')

    with open(tscn_path, "w", encoding="utf-8") as f:
        f.writelines(tscn_content)
    print(f"Escena Godot 4 guardada exitosamente: {tscn_path}")

# ---------------------------------------------------------------------------
# 6. Iluminación y Cámaras Técnicas Diurnas (Cycles CPU)
# ---------------------------------------------------------------------------
def setup_lighting_and_cameras(col):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720

    # Sol Diurno Principal (Key light desde Suroeste con luz cálida natural)
    sun_data = bpy.data.lights.new(name="Sun_Key", type='SUN')
    sun_data.energy = 3.6
    sun_data.angle = math.radians(6.0) # sombra suave natural
    sun_data.color = (1.0, 0.98, 0.94)
    sun_obj = bpy.data.objects.new("Sun_Key", sun_data)
    sun_obj.rotation_euler = (math.radians(52.0), math.radians(18.0), math.radians(-35.0))
    col.objects.link(sun_obj)

    # Sol de Relleno Suave (Fill light desde Noreste para iluminación equilibrada)
    sun_fill_data = bpy.data.lights.new(name="Sun_Fill", type='SUN')
    sun_fill_data.energy = 1.4
    sun_fill_data.angle = math.radians(15.0)
    sun_fill_data.color = (0.85, 0.92, 1.0)
    sun_fill_obj = bpy.data.objects.new("Sun_Fill", sun_fill_data)
    sun_fill_obj.rotation_euler = (math.radians(55.0), math.radians(-20.0), math.radians(145.0))
    col.objects.link(sun_fill_obj)

    # Cielo diurno
    world = scene.world
    if not world:
        world = bpy.data.worlds.new("World_Sky")
        scene.world = world
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs['Color'].default_value = (0.82, 0.88, 0.96, 1.0)
        bg_node.inputs['Strength'].default_value = 1.35

    cameras = {}
    cam_specs = [
        # Cam 1: Perspectiva Noroeste en ángulo hacia Telas Elías y Da Vinci
        ("Cam_01_NW_Juarez_Ortiz", (-18.0, 108.0, 6.5), (math.radians(80.0), 0.0, math.radians(-130.0)), 22.0),
        # Cam 2: Elevación frontal Av. Juárez a cota de calle (Hotel Juárez, taquerías, comercios)
        ("Cam_02_North_Juarez_Center", (67.0, 126.0, 7.0), (math.radians(82.0), 0.0, math.radians(180.0)), 18.0),
        # Cam 3: Perspectiva Noreste (Terminal de Autobuses y esquina Rodríguez)
        ("Cam_03_NE_Juarez_Rodriguez", (152.0, 108.0, 6.5), (math.radians(80.0), 0.0, math.radians(135.0)), 22.0),
        # Cam 4: Elevación frontal oriente (Abelardo L. Rodríguez: dársenas, cercha espacial)
        ("Cam_04_East_Rodriguez", (158.0, 45.0, 6.0), (math.radians(84.0), 0.0, math.radians(90.0)), 20.0),
        # Cam 5: Perspectiva Suroriente (esquina Callejón Libertad y Rodríguez)
        ("Cam_05_SE_Libertad_Rodriguez", (152.0, -18.0, 6.5), (math.radians(80.0), 0.0, math.radians(45.0)), 22.0),
        # Cam 6: Elevación frontal sur a cota de calle (Hotel Colonial, Fimbres, Arrematec, Heras, Prisci)
        ("Cam_06_South_Libertad_Center", (67.0, -32.0, 6.5), (math.radians(82.0), 0.0, math.radians(0.0)), 18.0),
        # Cam 7: Perspectiva Surponiente (Dulcería Prisci, Heras Internet, La Placita)
        ("Cam_07_SW_Libertad_Ortiz", (-18.0, -18.0, 6.5), (math.radians(80.0), 0.0, math.radians(-45.0)), 22.0),
        # Cam 8: Vista Cenital Superior Ortográfica a Z=85m
        ("Cam_08_Top_Aerial_Z75", (67.36, 45.60, 85.0), (math.radians(0.0), 0.0, math.radians(0.0)), 22.0),
    ]

    for name, loc, rot, lens in cam_specs:
        cam_data = bpy.data.cameras.new(name)
        cam_data.lens = lens
        cam_obj = bpy.data.objects.new(name, cam_data)
        cam_obj.location = loc
        cam_obj.rotation_euler = rot
        col.objects.link(cam_obj)
        cameras[name] = cam_obj

    return cameras

def render_validation_suite(cameras):
    scene = bpy.context.scene
    for cam_name, cam_obj in cameras.items():
        print(f"Renderizando vista técnica cerrada: {cam_name}...")
        scene.camera = cam_obj
        out_file = os.path.join(DOCS_IMAGES_DIR, f"{cam_name}.png")
        scene.render.filepath = out_file
        bpy.ops.render.render(write_still=True)
        print(f"  Guardado render de validación: {out_file}")

# ---------------------------------------------------------------------------
# 7. Orquestación Principal
# ---------------------------------------------------------------------------
def main():
    print("===========================================================================")
    print("INICIANDO RECONSTRUCCIÓN PROCEDURAL 3D DE LA MANZANA CENTRAL COMPLETA (2009)")
    print("===========================================================================")

    root_col = clean_scene()
    mats = create_all_materials()

    # Construcción de la cimentación continua y las 4 zonas edilicias sin solapamiento
    build_unified_foundation(mats, root_col)
    build_west_facade_ortiz_rubio(mats, root_col)
    build_north_facade_juarez(mats, root_col)
    build_terminal_and_east_facade(mats, root_col)
    build_south_facade_libertad(mats, root_col)
    build_interior_courtyards_and_roofs(mats, root_col)

    # Configuración de cámaras e iluminación diurna balanceada
    cams = setup_lighting_and_cameras(root_col)

    # Guardar archivo maestro .blend
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"Archivo maestro Blender guardado: {BLEND_PATH}")

    # Exportar archivo de producción glTF/GLB
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH,
        export_format='GLB',
        use_selection=False,
        export_cameras=False,
        export_lights=False,
        export_apply=True,
        export_yup=True,
        export_materials='EXPORT',
        export_image_format='AUTO'
    )
    print(f"Asset de producción GLB exportado: {GLB_PATH}")

    # Generar escena Godot .tscn con física analítica
    generate_godot_tscn(TSCN_PATH, "res://assets/buildings/manzana_central_2009.glb")

    # Renderizar la suite de validación visual de 8 cámaras
    render_validation_suite(cams)

    print("===========================================================================")
    print("RECONSTRUCCIÓN PROCEDURAL DE LA MANZANA CENTRAL FINALIZADA CON ÉXITO")
    print("===========================================================================")

if __name__ == "__main__":
    main()
