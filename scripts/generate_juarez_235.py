"""
Generador Procedural 3D de Alta Fidelidad Fotorrealista: Av. Benito Juárez 235 (V4.1 de Producción)
====================================================================================================
Reconstruye fidedignamente el complejo comercial continuo en Av. Benito Juárez 235, Zona Centro,
Tecate, B.C. (época histórica: 2009), desde El Baratero (poniente) hasta La Michoacana (oriente).

ESTÁNDAR DE PRODUCCIÓN RIGUROSO:
- CERO texturas fotográficas de panoramas en quads planos.
- 100% GEOMETRÍA PROCEDURAL EN MALLAS (MESHES) Y RÓTULOS CORPÓREOS 3D EXTRIUDOS.
- Cancelería extruida con marcos, alféizares, parteluces, zócalos de aluminio y tiradores tubulares de acero 3D.
- Hiladas reales de tejas coloniales curvas 3D (canales y cobijas de barro).
- Porche a dos aguas de La Fuente con tejas transversales que escurren hacia ambos lados.
- Cortina metálica enrollable con lamas acanaladas en relieve.
- Dovelas de ladrillo decimonónico en resalte radial de 6 cm con materiales PBR.
- Celosías de forja negra con barrotes cruzados tridimensionales.
- Cerchas espaciales trianguladas (space frame trusses) de tubos de acero para cartelera espectacular.
- Zócalo basal enterrado continuo a Z <= -1.30 m para absorción topográfica.
- Colisiones analíticas en Godot 4 (BoxShape3D) con paso libre diáfano en callejón (X in [63.00, 69.50]).
- Sincronización canónica glTF/Godot: Z_godot = -Y_blender.
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
DOCS_IMAGES_DIR = os.path.abspath("docs/images/juarez_235")

for d in [TEXTURES_DIR, BUILDINGS_DIR, BLENDER_DIR, DOCS_IMAGES_DIR]:
    os.makedirs(d, exist_ok=True)

BLEND_PATH = os.path.join(BLENDER_DIR, "edificio_juarez_235.blend")
GLB_PATH = os.path.join(BUILDINGS_DIR, "edificio_juarez_235.glb")
TSCN_PATH = os.path.join(BUILDINGS_DIR, "edificio_juarez_235.tscn")

# Cotas Maestras
Z_BASE = -2.00       # Zócalo basal subterráneo continuo extendido para absorción topográfica de 112m
Z_GROUND = 0.00     # Cota rasante peatonal
H_BARATERO_PB = 3.40
H_BARATERO_N2 = 7.20
H_BARATERO_N3 = 11.50
H_COMERCIAL = 4.20
H_CORONACION = 4.60
H_ESPECTACULAR = 13.50

# Rotaciones canónicas anti-espejo para curvas de texto FONT
ROT_SOUTH = (math.radians(90.0), 0.0, 0.0)
ROT_NORTH = (math.radians(90.0), 0.0, math.radians(180.0))
ROT_WEST  = (math.radians(90.0), 0.0, math.radians(-90.0))
ROT_EAST  = (math.radians(90.0), 0.0, math.radians(90.0))

# ---------------------------------------------------------------------------
# 2. Utilidades de Escena y BMesh
# ---------------------------------------------------------------------------
def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    col = bpy.data.collections.new("Juarez_235_Collection")
    scene.collection.children.link(col)
    return col

def add_box(bm, x1, x2, y1, y2, z1, z2):
    """Genera paralelepípedo limpio cerrado con normales hacia el exterior."""
    verts = [
        bm.verts.new((x1, y1, z1)), bm.verts.new((x2, y1, z1)),
        bm.verts.new((x2, y2, z1)), bm.verts.new((x1, y2, z1)),
        bm.verts.new((x1, y1, z2)), bm.verts.new((x2, y1, z2)),
        bm.verts.new((x2, y2, z2)), bm.verts.new((x1, y2, z2))
    ]
    bm.faces.new((verts[0], verts[1], verts[2], verts[3]))
    bm.faces.new((verts[4], verts[7], verts[6], verts[5]))
    bm.faces.new((verts[0], verts[4], verts[5], verts[1]))
    bm.faces.new((verts[1], verts[5], verts[6], verts[2]))
    bm.faces.new((verts[2], verts[6], verts[7], verts[3]))
    bm.faces.new((verts[3], verts[7], verts[4], verts[0]))

def add_teja_ribs_x(bm, x_start, x_end, y_eave, y_ridge, z_eave, z_ridge, spacing=0.38):
    """Genera hiladas de teja colonial curva 3D con canales y cobijas de barro a lo largo de X."""
    num_ribs = max(1, int((x_end - x_start) / spacing))
    for i in range(num_ribs):
        xc = x_start + (i + 0.5) * spacing
        v0 = bm.verts.new((xc - 0.11, y_eave, z_eave + 0.04))
        v1 = bm.verts.new((xc + 0.11, y_eave, z_eave + 0.04))
        v2 = bm.verts.new((xc + 0.11, y_ridge, z_ridge + 0.04))
        v3 = bm.verts.new((xc - 0.11, y_ridge, z_ridge + 0.04))
        v_top0 = bm.verts.new((xc, y_eave, z_eave + 0.11))
        v_top1 = bm.verts.new((xc, y_ridge, z_ridge + 0.11))

        bm.faces.new((v0, v1, v_top0))
        bm.faces.new((v1, v2, v_top1, v_top0))
        bm.faces.new((v2, v3, v_top1))
        bm.faces.new((v3, v0, v_top0, v_top1))

def add_teja_gable_porch(bm, x_left, x_center, x_right, y_front, y_back, z_eave, z_ridge, num_courses=5):
    """Genera tejas coloniales a dos aguas escurriendo hacia los lados (+X y -X) con cumbrera longitudinal en Y."""
    dy = (y_back - y_front) / num_courses
    for i in range(num_courses):
        y0 = y_front + i * dy
        y1 = y_front + (i + 1) * dy

        # Faldón Izquierdo (escurre hacia x_left)
        # Cobija curva sobre faldón izq
        v0 = bm.verts.new((x_left - 0.05, y0, z_eave))
        v1 = bm.verts.new((x_left - 0.05, y1, z_eave))
        v2 = bm.verts.new((x_center, y1, z_ridge))
        v3 = bm.verts.new((x_center, y0, z_ridge))
        v_c0 = bm.verts.new(((x_left + x_center)*0.5, y0, (z_eave + z_ridge)*0.5 + 0.08))
        v_c1 = bm.verts.new(((x_left + x_center)*0.5, y1, (z_eave + z_ridge)*0.5 + 0.08))
        bm.faces.new((v0, v1, v_c1, v_c0))
        bm.faces.new((v_c0, v_c1, v2, v3))

        # Faldón Derecho (escurre hacia x_right)
        v4 = bm.verts.new((x_right + 0.05, y0, z_eave))
        v5 = bm.verts.new((x_right + 0.05, y1, z_eave))
        v_c2 = bm.verts.new(((x_right + x_center)*0.5, y0, (z_eave + z_ridge)*0.5 + 0.08))
        v_c3 = bm.verts.new(((x_right + x_center)*0.5, y1, (z_eave + z_ridge)*0.5 + 0.08))
        bm.faces.new((v3, v2, v_c3, v_c2))
        bm.faces.new((v_c2, v_c3, v5, v4))

    # Caballete de cumbrera semicilíndrico superior
    add_box(bm, x_center - 0.10, x_center + 0.10, y_front - 0.05, y_back, z_ridge - 0.02, z_ridge + 0.10)

def add_canopy_quarter_round(bm, x1, x2, y_back, depth, z_bottom, height, segments=8):
    """Genera toldo abombado de cuarto de cilindro/esfera de lona tensada."""
    arc_pts = []
    for i in range(segments + 1):
        th = (math.pi * 0.5) * (i / segments)
        dy = depth * math.cos(th)
        dz = height * math.sin(th)
        arc_pts.append((y_back - dy, z_bottom + dz))

    for i in range(segments):
        y0, z0 = arc_pts[i]
        y1, z1 = arc_pts[i+1]
        v_bl = bm.verts.new((x1, y0, z0))
        v_br = bm.verts.new((x2, y0, z0))
        v_tr = bm.verts.new((x2, y1, z1))
        v_tl = bm.verts.new((x1, y1, z1))
        bm.faces.new((v_bl, v_br, v_tr, v_tl))

    # Tapas laterales
    v_back_top = bm.verts.new((x1, y_back, z_bottom + height))
    v_back_bot = bm.verts.new((x1, y_back, z_bottom))
    v_front_bot = bm.verts.new((x1, y_back - depth, z_bottom))
    bm.faces.new((v_back_bot, v_front_bot, v_back_top))

    v_r_bt = bm.verts.new((x2, y_back, z_bottom + height))
    v_r_bb = bm.verts.new((x2, y_back, z_bottom))
    v_r_fb = bm.verts.new((x2, y_back - depth, z_bottom))
    bm.faces.new((v_r_bb, v_r_bt, v_r_fb))

    # Faldón inferior festoneado vertical
    add_box(bm, x1, x2, y_back - depth - 0.02, y_back - depth, z_bottom - 0.16, z_bottom)

def add_arch_spandrel_x(bm, y_min, y_max, x_start, x_end, z_spring, z_crown, z_top, segments=16):
    """Construye arco rebajado en X con intradós y enjutas para dovelas de ladrillo."""
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

    # Tapas laterales de arranque
    v_s_bl = bm.verts.new((x_start, y_min, z_spring))
    v_s_tl = bm.verts.new((x_start, y_min, z_top))
    v_s_tr = bm.verts.new((x_start, y_max, z_top))
    v_s_br = bm.verts.new((x_start, y_max, z_spring))
    bm.faces.new((v_s_bl, v_s_tl, v_s_tr, v_s_br))

    v_e_bl = bm.verts.new((x_end, y_min, z_spring))
    v_e_tl = bm.verts.new((x_end, y_min, z_top))
    v_e_tr = bm.verts.new((x_end, y_max, z_top))
    v_e_br = bm.verts.new((x_end, y_max, z_spring))
    bm.faces.new((v_e_bl, v_e_br, v_e_tr, v_e_tl))

def add_space_frame_truss(bm, x1, x2, y1, y2, z1, z2, subdivisions=6):
    """Construye cercha tridimensional en tijera de perfiles de acero galvanizado."""
    dx = (x2 - x1) / subdivisions
    r_pipe = 0.035
    for i in range(subdivisions):
        xa = x1 + i * dx
        xb = x1 + (i + 1) * dx
        # Cordones horizontales longitudinales
        add_box(bm, xa, xb, y1 - r_pipe, y1 + r_pipe, z1 - r_pipe, z1 + r_pipe)
        add_box(bm, xa, xb, y1 - r_pipe, y1 + r_pipe, z2 - r_pipe, z2 + r_pipe)
        add_box(bm, xa, xb, y2 - r_pipe, y2 + r_pipe, z1 - r_pipe, z1 + r_pipe)
        add_box(bm, xa, xb, y2 - r_pipe, y2 + r_pipe, z2 - r_pipe, z2 + r_pipe)
        # Montantes verticales
        add_box(bm, xa - r_pipe, xa + r_pipe, y1 - r_pipe, y1 + r_pipe, z1, z2)
        add_box(bm, xa - r_pipe, xa + r_pipe, y2 - r_pipe, y2 + r_pipe, z1, z2)
        # Travesaños transversales
        add_box(bm, xa - r_pipe, xa + r_pipe, y1, y2, z1 - r_pipe, z1 + r_pipe)
        add_box(bm, xa - r_pipe, xa + r_pipe, y1, y2, z2 - r_pipe, z2 + r_pipe)
        # Diagonales cruzadas en X
        add_box(bm, min(xa, xb), max(xa, xb), y1 - r_pipe, y2 + r_pipe, (z1 + z2)*0.5 - r_pipe, (z1 + z2)*0.5 + r_pipe)

def auto_uv_bmesh(bm, scale_u=0.5, scale_v=0.5):
    """Genera coordenadas UV ortogonales cúbicas con preservación de escala métrica."""
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
def make_pbr_material(name, base_color=(0.8, 0.8, 0.8), roughness=0.85, metallic=0.0, alpha=1.0, tex_name=None, normal_prefix=None, uv_tiling=(1.0, 1.0)):
    """Crea material Principled BSDF conectado con UVs completas para glTF y Godot 4."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (base_color[0], base_color[1], base_color[2], 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic

    if alpha < 1.0:
        bsdf.inputs['Alpha'].default_value = alpha
        if hasattr(mat, 'blend_method'):
            mat.blend_method = 'BLEND'

    tex_coord = nodes.new(type='ShaderNodeTexCoord')
    mapping = nodes.new(type='ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (uv_tiling[0], uv_tiling[1], 1.0)
    mat.node_tree.links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

    # Textura de Albedo PBR procedural limpia
    if tex_name:
        tex_path = os.path.join(TEXTURES_DIR, tex_name)
        if os.path.exists(tex_path):
            t_alb = nodes.new(type='ShaderNodeTexImage')
            t_alb.image = bpy.data.images.load(tex_path)
            mat.node_tree.links.new(mapping.outputs['Vector'], t_alb.inputs['Vector'])
            mat.node_tree.links.new(t_alb.outputs['Color'], bsdf.inputs['Base Color'])

    # Normal map adicional (estuco, ladrillo, teja, laja)
    if normal_prefix:
        norm_path = os.path.join(TEXTURES_DIR, f"{normal_prefix}_normal.png")
        if os.path.exists(norm_path):
            t_nrm = nodes.new(type='ShaderNodeTexImage')
            t_nrm.image = bpy.data.images.load(norm_path)
            t_nrm.image.colorspace_settings.name = 'Non-Color'
            n_node = nodes.new(type='ShaderNodeNormalMap')
            n_node.inputs['Strength'].default_value = 0.85
            mat.node_tree.links.new(mapping.outputs['Vector'], t_nrm.inputs['Vector'])
            mat.node_tree.links.new(t_nrm.outputs['Color'], n_node.inputs['Color'])
            mat.node_tree.links.new(n_node.outputs['Normal'], bsdf.inputs['Normal'])

    mat.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def create_all_materials():
    mats = {}
    # 1. Muros y envolventes estucadas con normal maps de Tecate
    mats["zocalo_basal"] = make_pbr_material("M_Zocalo_Basal", (0.13, 0.14, 0.15), roughness=0.95)
    mats["stucco_blanco"] = make_pbr_material("M_Stucco_Blanco", (0.88, 0.87, 0.84), roughness=0.88, normal_prefix="hotel_tecate_stucco")
    mats["stucco_terracota"] = make_pbr_material("M_Stucco_Terracota", (0.68, 0.35, 0.22), roughness=0.85, normal_prefix="hotel_tecate_stucco")
    mats["stucco_menta"] = make_pbr_material("M_Stucco_Menta", (0.58, 0.76, 0.66), roughness=0.85, normal_prefix="hotel_tecate_stucco")
    mats["stucco_rojo"] = make_pbr_material("M_Stucco_Rojo", (0.75, 0.12, 0.12), roughness=0.75)
    mats["stucco_salmon"] = make_pbr_material("M_Stucco_Salmon", (0.84, 0.52, 0.40), roughness=0.85, normal_prefix="hotel_tecate_stucco")
    mats["stucco_azul"] = make_pbr_material("M_Stucco_Azul", (0.12, 0.32, 0.62), roughness=0.80, normal_prefix="hotel_tecate_stucco")
    mats["stucco_amarillo"] = make_pbr_material("M_Stucco_Amarillo", (0.95, 0.82, 0.42), roughness=0.80, normal_prefix="hotel_tecate_stucco")
    mats["muro_verde_oliva"] = make_pbr_material("M_Muro_Verde_Oliva", (0.35, 0.44, 0.36), roughness=0.85, normal_prefix="hotel_tecate_stucco")
    mats["pilastra_fucsia"] = make_pbr_material("M_Pilastra_Fucsia", (0.72, 0.32, 0.66), roughness=0.70)
    mats["porton_rojo"] = make_pbr_material("M_Porton_Rojo", (0.58, 0.16, 0.16), roughness=0.45, metallic=0.5)

    # 2. Materiales institucionales y comerciales
    mats["baratero_magenta"] = make_pbr_material("M_Baratero_Magenta", (0.65, 0.10, 0.40), roughness=0.40)
    mats["pri_verde"] = make_pbr_material("M_PRI_Verde", (0.04, 0.42, 0.22), roughness=0.45)
    mats["pri_rojo"] = make_pbr_material("M_PRI_Rojo", (0.84, 0.16, 0.16), roughness=0.45)
    mats["michoacana_rosa"] = make_pbr_material("M_Michoacana_Rosa", (0.88, 0.11, 0.47), roughness=0.35)
    mats["michoacana_mosaico"] = make_pbr_material("M_Michoacana_Mosaico", (0.12, 0.52, 0.30), roughness=0.30)
    mats["coca_cola_rojo"] = make_pbr_material("M_CocaCola_Rojo", (0.78, 0.08, 0.08), roughness=0.40)
    mats["coca_cola_blanco"] = make_pbr_material("M_CocaCola_Blanco", (0.92, 0.92, 0.92), roughness=0.45)
    mats["sky_azul"] = make_pbr_material("M_SKY_Azul", (0.00, 0.24, 0.65), roughness=0.40)
    mats["rodeo_madera"] = make_pbr_material("M_Rodeo_Madera", (0.32, 0.18, 0.12), roughness=0.70)

    # 3. Metales, cancelería y vidrio
    mats["aluminio_azul"] = make_pbr_material("M_Aluminio_Azul", (0.16, 0.38, 0.72), roughness=0.30, metallic=0.75)
    mats["aluminio_blanco"] = make_pbr_material("M_Aluminio_Blanco", (0.95, 0.95, 0.95), roughness=0.25, metallic=0.60)
    mats["aluminio_negro"] = make_pbr_material("M_Aluminio_Negro", (0.08, 0.08, 0.08), roughness=0.30, metallic=0.80)
    mats["acero_galvanizado"] = make_pbr_material("M_Acero_Galvanizado", (0.68, 0.70, 0.72), roughness=0.38, metallic=0.85)
    mats["acero_inoxidable"] = make_pbr_material("M_Acero_Inoxidable", (0.85, 0.88, 0.92), roughness=0.15, metallic=0.95)
    mats["vidrio_comercial"] = make_pbr_material("M_Vidrio_Comercial", (0.75, 0.84, 0.90), roughness=0.08, alpha=0.35)
    mats["herreria_negra"] = make_pbr_material("M_Herreria_Negra", (0.06, 0.06, 0.06), roughness=0.40, metallic=0.85)
    mats["herreria_verde"] = make_pbr_material("M_Herreria_Verde", (0.18, 0.62, 0.28), roughness=0.40, metallic=0.65)

    # 4. Materiales cerámicos, mampostería y madera
    mats["teja_colonial"] = make_pbr_material("M_Teja_Colonial", (0.55, 0.21, 0.12), roughness=0.80, tex_name="kiosko_teja_albedo.png", normal_prefix="kiosko_teja")
    mats["ladrillo_dovelas"] = make_pbr_material("M_Ladrillo_Dovelas", (0.58, 0.28, 0.18), roughness=0.82, tex_name="kiosko_ladrillo_albedo.png", normal_prefix="kiosko_ladrillo", uv_tiling=(2.5, 2.5))
    mats["madera_canes"] = make_pbr_material("M_Madera_Canes", (0.24, 0.14, 0.09), roughness=0.68)
    mats["concreto_piso"] = make_pbr_material("M_Concreto_Piso", (0.62, 0.63, 0.64), roughness=0.90)
    mats["asfalto_azotea"] = make_pbr_material("M_Asfalto_Azotea", (0.20, 0.20, 0.22), roughness=0.92)

    # 5. Letras corpóreas 3D
    mats["letras_blanco"] = make_pbr_material("M_Letras_Blanco", (0.98, 0.98, 0.98), roughness=0.25)
    mats["letras_dorado"] = make_pbr_material("M_Letras_Dorado", (0.92, 0.72, 0.22), roughness=0.25, metallic=0.65)
    mats["letras_amarillo"] = make_pbr_material("M_Letras_Amarillo", (1.00, 0.88, 0.05), roughness=0.30)
    mats["letras_rojo"] = make_pbr_material("M_Letras_Rojo", (0.85, 0.08, 0.08), roughness=0.30)
    mats["letras_azul"] = make_pbr_material("M_Letras_Azul", (0.05, 0.35, 0.75), roughness=0.30)
    mats["letras_verde_neon"] = make_pbr_material("M_Letras_Verde_Neon", (0.35, 0.95, 0.25), roughness=0.25)

    return mats

# ---------------------------------------------------------------------------
# 4. Construcción de Cuerpos Arquitectónicos en Mallas Procedurales Puras
# ---------------------------------------------------------------------------

def build_baratero_pri(mats, col):
    """Cuerpo 1: El Baratero y Sede Municipal del PRI (X in [0.00, 26.50 m], Y in [0.00, 36.00 m])."""
    # Muros base estructurales y pretiles
    bm_muros = bmesh.new()
    # Edificio frontal Juárez (blanco)
    add_box(bm_muros, 0.00, 26.50, 0.00, 16.00, Z_BASE, H_BARATERO_N3)
    # Pretil perimetral y albardilla
    add_box(bm_muros, -0.08, 26.58, -0.08, 16.08, H_BARATERO_N3, H_BARATERO_N3 + 0.40)
    create_mesh_object("Baratero_Muros_Estructura", bm_muros, mats["stucco_blanco"], col)

    # Nave posterior Cárdenas (Muro Verde Oliva)
    bm_nave_muro = bmesh.new()
    add_box(bm_nave_muro, 0.00, 26.50, 16.00, 36.00, Z_BASE, 9.40)
    add_box(bm_nave_muro, -0.08, 26.58, 16.00, 36.08, 9.40, 9.75)
    create_mesh_object("Baratero_Nave_Muro_Verde", bm_nave_muro, mats["muro_verde_oliva"], col)

    # 1. Fascia Magenta Frontal PB en Resalte Volumétrico Profundo
    bm_fascia = bmesh.new()
    add_box(bm_fascia, -0.08, 26.58, -0.45, -0.05, 2.65, 3.45)
    # Moldura superior e inferior en resalte de 6 cm
    add_box(bm_fascia, -0.12, 26.62, -0.50, -0.05, 3.42, 3.48)
    add_box(bm_fascia, -0.12, 26.62, -0.50, -0.05, 2.62, 2.68)
    create_mesh_object("Baratero_Fascia_PB", bm_fascia, mats["baratero_magenta"], col)

    # Rótulo Corpóreo 3D en Frontis de Fascia
    add_3d_text("Baratero_Txt_Main", "EL BARATERO", 0.54, 0.045, (13.25, -0.52, 3.12), ROT_SOUTH, mats["letras_blanco"], col)
    add_3d_text("Baratero_Txt_Sub", "ROPA • CALZADO • ACCESORIOS", 0.20, 0.025, (13.25, -0.52, 2.82), ROT_SOUTH, mats["letras_dorado"], col)

    # 2. Cancelería de Aluminio Azul PB y Puertas Dobles con Tiradores de Acero
    bm_alum = bmesh.new()
    bm_vid = bmesh.new()
    # Zoclo inferior corrido de 18 cm
    add_box(bm_alum, 0.00, 26.50, -0.10, 0.00, 0.00, 0.18)
    # 8 Crujías con montantes dobles
    num_bays = 8
    bay_w = 26.50 / num_bays
    for i in range(num_bays + 1):
        x = i * bay_w
        add_box(bm_alum, x - 0.06, x + 0.06, -0.12, 0.00, 0.18, 2.65)
    # Travesaño intermedio continuo
    add_box(bm_alum, 0.00, 26.50, -0.10, 0.00, 2.05, 2.12)
    # Paños de vidrio
    add_box(bm_vid, 0.04, 26.46, -0.05, -0.03, 0.18, 2.65)

    # Puerta Doble en Crujía Central (i=4)
    cx = 4 * bay_w
    add_box(bm_alum, cx - 1.10, cx + 1.10, -0.14, -0.02, 0.18, 2.30)
    add_box(bm_alum, cx - 0.05, cx + 0.05, -0.15, -0.02, 0.18, 2.30)

    # Tiradores Tubulares 3D de Acero Inoxidable
    bm_tir = bmesh.new()
    for hx in [cx - 0.12, cx + 0.12]:
        # Tubo vertical
        add_box(bm_tir, hx - 0.02, hx + 0.02, -0.25, -0.21, 0.75, 1.95)
        # Soportes horizontales de anclaje
        add_box(bm_tir, hx - 0.015, hx + 0.015, -0.25, -0.14, 0.85, 0.88)
        add_box(bm_tir, hx - 0.015, hx + 0.015, -0.25, -0.14, 1.82, 1.85)

    create_mesh_object("Baratero_Canceleria_Aluminio", bm_alum, mats["aluminio_azul"], col)
    create_mesh_object("Baratero_Vidrios_PB", bm_vid, mats["vidrio_comercial"], col)
    create_mesh_object("Baratero_Tiradores_Acero", bm_tir, mats["acero_inoxidable"], col)

    # 3. Planta Alta Oficinas PRI: Muro Cortina y Faja Institucional Verde
    bm_pri = bmesh.new()
    # Faja horizontal verde del PRI
    add_box(bm_pri, -0.06, 26.56, -0.26, -0.05, 6.40, 7.20)
    # Moldura de remate
    add_box(bm_pri, -0.10, 26.60, -0.30, -0.05, 7.15, 7.22)
    # Montantes verticales de muro cortina en PA
    for i in range(12):
        xp = i * (26.50 / 11)
        add_box(bm_pri, xp - 0.05, xp + 0.05, -0.15, -0.02, 3.45, 6.40)
    add_box(bm_pri, 0.00, 26.50, -0.12, -0.02, 4.85, 4.95) # Travesaño
    create_mesh_object("Baratero_PRI_Planta_Alta", bm_pri, mats["pri_verde"], col)

    # Ventanales de vidrio en PA
    bm_vid_pa = bmesh.new()
    add_box(bm_vid_pa, 0.04, 26.46, -0.08, -0.06, 3.45, 6.40)
    create_mesh_object("Baratero_Vidrios_PA", bm_vid_pa, mats["vidrio_comercial"], col)

    # Rótulo Corpóreo 3D del PRI en Planta Alta
    add_3d_text("PRI_Txt_Main", "PARTIDO REVOLUCIONARIO INSTITUCIONAL", 0.26, 0.03, (13.25, -0.28, 6.88), ROT_SOUTH, mats["letras_blanco"], col)
    add_3d_text("PRI_Txt_Sub", "COMITE DIRECTIVO MUNICIPAL • TECATE", 0.16, 0.02, (13.25, -0.28, 6.58), ROT_SOUTH, mats["letras_blanco"], col)

    # 4. Frontispicio Nivel 3 (Z: 7.20 a 11.50 m) con Pilastras y Marcas en Relieve 3D
    bm_n3 = bmesh.new()
    # 4 Pilastras verticales en relieve de 8 cm
    for xp in [0.0, 6.625, 13.25, 19.875, 26.50]:
        add_box(bm_n3, xp - 0.20, xp + 0.20, -0.14, -0.04, 7.20, H_BARATERO_N3)
    # Cornisa de coronación
    add_box(bm_n3, -0.15, 26.65, -0.22, 0.05, H_BARATERO_N3, H_BARATERO_N3 + 0.35)
    create_mesh_object("Baratero_Tower_Nivel3", bm_n3, mats["stucco_blanco"], col)

    # Placas / Identificadores 3D en las 4 Crujías
    for idx, cx in enumerate([3.31, 9.94, 16.56, 23.19], start=1):
        add_3d_text(f"Baratero_Num_{idx}", f"{idx}", 0.65, 0.04, (cx, -0.08, 9.50), ROT_SOUTH, mats["letras_dorado"], col)

    # 5. Alzado Poniente (Calle Presidente Lázaro Cárdenas, X = 0.00 m)
    # Tramo Sur PRI (Y: 0.00 a 16.00 m)
    add_3d_text("PRI_Txt_Cardenas_1", "PRI", 0.95, 0.05, (-0.08, 8.00, 5.40), ROT_WEST, mats["pri_rojo"], col)
    add_3d_text("PRI_Txt_Cardenas_2", "SEDE MUNICIPAL TECATE", 0.24, 0.025, (-0.08, 8.00, 4.40), ROT_WEST, mats["letras_blanco"], col)

    # Tramo Norte Nave Industrial Verde (Y: 16.00 a 36.00 m)
    bm_nave = bmesh.new()
    # 5 Pilastras verticales en resalte de 14 cm en color fucsia/magenta
    for yp in [16.0, 21.0, 26.0, 31.0, 36.0]:
        add_box(bm_nave, -0.20, -0.04, yp - 0.35, yp + 0.35, 0.00, 9.40)
    # Trabes horizontales fucsias
    add_box(bm_nave, -0.18, -0.04, 16.00, 36.00, 4.50, 4.95)
    add_box(bm_nave, -0.18, -0.04, 16.00, 36.00, 8.85, 9.40)
    create_mesh_object("Baratero_Cardenas_Reticula_Fucsia", bm_nave, mats["pilastra_fucsia"], col)

    # Portones Industriales Rojos en Cárdenas
    bm_port = bmesh.new()
    for yp_start in [18.00, 28.00]:
        # Marco metálico angular negro
        add_box(bm_port, -0.12, -0.04, yp_start - 0.08, yp_start + 2.58, 0.00, 3.48)
        # Portón rojo acanalado
        add_box(bm_port, -0.10, -0.06, yp_start, yp_start + 2.50, 0.02, 3.40)
        # Cerrojo y ventanilla
        add_box(bm_port, -0.14, -0.04, yp_start + 1.20, yp_start + 1.30, 1.40, 1.55)
    create_mesh_object("Baratero_Cardenas_Portones_Rojos", bm_port, mats["porton_rojo"], col)

    # 6. Mástil y Cartelera en Esquina Juárez y Cárdenas
    bm_totem = bmesh.new()
    add_box(bm_totem, -0.45, -0.25, -0.45, -0.25, 0.00, 4.60)
    add_box(bm_totem, -1.80, 0.15, -0.55, -0.22, 3.20, 4.40)
    create_mesh_object("Baratero_Corner_Totem_Box", bm_totem, mats["baratero_magenta"], col)
    add_3d_text("Totem_Txt_Front", "EL BARATERO", 0.28, 0.03, (-0.82, -0.58, 3.80), ROT_SOUTH, mats["letras_blanco"], col)

def build_restaurant_darce(mats, col):
    """Cuerpo 2: Restaurant D'Arce (X in [26.50, 37.00 m], Y in [0.00, 14.50 m])."""
    # Muros de estuco terracota y pretil
    bm_muros = bmesh.new()
    add_box(bm_muros, 26.50, 37.00, 0.00, 14.50, Z_BASE, 4.30)
    add_box(bm_muros, 26.45, 37.05, -0.05, 14.55, 4.30, 4.65)
    create_mesh_object("Darce_Muros_Terracota", bm_muros, mats["stucco_terracota"], col)

    # Marquesina volada con canes de madera y faldón de tejas coloniales 3D
    bm_marq = bmesh.new()
    # 7 Canes de vigas de madera oscura escuadrada
    for x in [27.0, 28.5, 30.0, 31.75, 33.5, 35.0, 36.5]:
        add_box(bm_marq, x - 0.09, x + 0.09, -1.35, 0.00, 2.90, 3.10)
    create_mesh_object("Darce_Canes_Madera", bm_marq, mats["madera_canes"], col)

    # Faldón inclinado de techumbre y tejas curvas 3D
    bm_tejas = bmesh.new()
    v_eave_l = bm_tejas.verts.new((26.40, -1.40, 2.95))
    v_eave_r = bm_tejas.verts.new((37.10, -1.40, 2.95))
    v_ridge_r = bm_tejas.verts.new((37.10, 0.00, 3.45))
    v_ridge_l = bm_tejas.verts.new((26.40, 0.00, 3.45))
    bm_tejas.faces.new((v_eave_l, v_eave_r, v_ridge_r, v_ridge_l))
    add_teja_ribs_x(bm_tejas, 26.50, 37.00, -1.40, 0.00, 2.95, 3.45, spacing=0.40)
    create_mesh_object("Darce_Marquesina_Tejas", bm_tejas, mats["teja_colonial"], col)

    # Gran Letrero en Caja Blanca con Marco Azul
    bm_rot = bmesh.new()
    # Marco azul exterior
    add_box(bm_rot, 29.15, 34.35, -0.22, -0.06, 3.48, 4.22)
    # Fondo blanco interior
    add_box(bm_rot, 29.25, 34.25, -0.24, -0.07, 3.55, 4.15)
    # Varillas tensoras metálicas
    add_box(bm_rot, 29.68, 29.72, -0.15, -0.05, 4.22, 4.55)
    add_box(bm_rot, 33.78, 33.82, -0.15, -0.05, 4.22, 4.55)
    create_mesh_object("Darce_Caja_Letrero", bm_rot, mats["aluminio_azul"], col)

    # Rótulo Corpóreo 3D D'ARCE RESTAURANT BAR
    add_3d_text("Darce_Txt_Main", "D'ARCE", 0.46, 0.035, (31.75, -0.26, 3.92), ROT_SOUTH, mats["letras_azul"], col)
    add_3d_text("Darce_Txt_Sub", "RESTAURANT  •  BAR", 0.18, 0.02, (31.75, -0.26, 3.65), ROT_SOUTH, mats["letras_dorado"], col)

    # Cancelería Comercial Negra y Vidrios
    bm_canc = bmesh.new()
    bm_vid = bmesh.new()
    # Ventanal 1 Izquierdo (X: 27.20 - 29.80) con marco y parteluz
    add_box(bm_canc, 27.15, 29.85, -0.08, 0.00, 0.85, 2.50)
    add_box(bm_canc, 28.45, 28.55, -0.10, -0.02, 0.85, 2.50)
    add_box(bm_vid, 27.20, 29.80, -0.04, -0.02, 0.90, 2.45)
    # Puerta Doble Central (X: 30.60 - 32.90) con montante central
    add_box(bm_canc, 30.55, 32.95, -0.10, 0.00, 0.00, 2.50)
    add_box(bm_canc, 31.70, 31.80, -0.12, 0.00, 0.00, 2.50)
    add_box(bm_vid, 30.60, 32.90, -0.04, -0.02, 0.05, 2.45)
    # Ventanal 2 Derecho (X: 33.70 - 36.30) con marco y parteluz
    add_box(bm_canc, 33.65, 36.35, -0.08, 0.00, 0.85, 2.50)
    add_box(bm_canc, 34.95, 35.05, -0.10, -0.02, 0.85, 2.50)
    add_box(bm_vid, 33.70, 36.30, -0.04, -0.02, 0.90, 2.45)
    create_mesh_object("Darce_Canceleria_Aluminio", bm_canc, mats["aluminio_negro"], col)
    create_mesh_object("Darce_Vidrios", bm_vid, mats["vidrio_comercial"], col)

    # 2 Faroles Coloniales de Forja Negra a los lados del acceso
    bm_farol = bmesh.new()
    for fx in [30.20, 33.30]:
        add_box(bm_farol, fx - 0.04, fx + 0.04, -0.28, -0.08, 1.85, 1.90) # Brazo
        add_box(bm_farol, fx - 0.10, fx + 0.10, -0.38, -0.18, 1.70, 2.05) # Linterna
    create_mesh_object("Darce_Faroles_Herreria", bm_farol, mats["herreria_negra"], col)

def build_local_blanco_lafuente(mats, col):
    """Cuerpos 3 y 4: Local Blanco y Dulcería La Fuente (X in [37.00, 49.50 m])."""
    # Muros base de estuco blanco
    bm_muros = bmesh.new()
    add_box(bm_muros, 37.00, 41.50, 0.00, 12.00, Z_BASE, 3.80)
    add_box(bm_muros, 41.50, 49.50, 0.00, 14.00, Z_BASE, 4.30)
    # Pretiles
    add_box(bm_muros, 36.95, 41.55, -0.05, 12.05, 3.80, 4.05)
    add_box(bm_muros, 41.45, 49.55, -0.05, 14.05, 4.30, 4.60)
    create_mesh_object("Locales_Muros_Blancos", bm_muros, mats["stucco_blanco"], col)

    # Local Blanco: Cortina metálica acanalada con lamas horizontales y marco de letrero
    bm_lblanco = bmesh.new()
    # Marco exterior
    add_box(bm_lblanco, 37.35, 41.15, -0.08, 0.00, 0.00, 2.55)
    # Lamas acanaladas horizontales en relieve
    for lz in range(13):
        z_lam = lz * 0.19
        add_box(bm_lblanco, 37.40, 41.10, -0.07, -0.02, z_lam + 0.02, z_lam + 0.17)
    # Marco superior de anuncio
    add_box(bm_lblanco, 37.30, 41.20, -0.12, -0.04, 2.70, 3.50)
    create_mesh_object("Local_Blanco_Cortina", bm_lblanco, mats["acero_galvanizado"], col)

    # Dulcería La Fuente: Porche tradicional a dos aguas con cumbrera en Y
    bm_porche = bmesh.new()
    x_c = 43.40
    # Vigas maestras y cumbrera longitudinal en Y
    add_box(bm_porche, 41.75, 41.95, -1.25, 0.00, 2.50, 2.65)
    add_box(bm_porche, 44.85, 45.05, -1.25, 0.00, 2.50, 2.65)
    add_box(bm_porche, x_c - 0.08, x_c + 0.08, -1.25, 0.00, 3.20, 3.35)
    create_mesh_object("Dulceria_Vigueria_Madera", bm_porche, mats["madera_canes"], col)

    # Tejas coloniales a dos aguas escurriendo a ambos lados
    bm_ftejas = bmesh.new()
    add_teja_gable_porch(bm_ftejas, 41.80, x_c, 45.00, -1.25, 0.00, 2.60, 3.35, num_courses=6)
    create_mesh_object("Dulceria_Tejas_Porche", bm_ftejas, mats["teja_colonial"], col)

    # Cancel de acceso con reja de hierro verde limón bajo el porche
    bm_reja = bmesh.new()
    add_box(bm_reja, 42.20, 44.60, -0.08, 0.00, 0.00, 2.45)
    # Puerta acristalada y barrotes verdes
    for bx in range(12):
        px = 42.30 + bx * 0.19
        add_box(bm_reja, px - 0.015, px + 0.015, -0.10, -0.06, 0.10, 2.40)
    create_mesh_object("Dulceria_Cancel_Reja_Verde", bm_reja, mats["herreria_verde"], col)

    # Ventana colonial derecha (X: 45.80 - 48.00) con cuarterones
    bm_vcol = bmesh.new()
    add_box(bm_vcol, 45.75, 48.05, -0.10, 0.00, 0.85, 2.25)
    # Alféizar moldurado de piedra
    add_box(bm_vcol, 45.70, 48.10, -0.15, 0.00, 0.80, 0.88)
    # Cuarterones de madera blanca (cruz)
    add_box(bm_vcol, 46.85, 46.95, -0.08, -0.02, 0.85, 2.25) # Montante
    add_box(bm_vcol, 45.75, 48.05, -0.08, -0.02, 1.50, 1.58) # Travesaño
    create_mesh_object("Dulceria_Ventana_Marco", bm_vcol, mats["aluminio_blanco"], col)

    # Vidrio de ventana colonial
    bm_vid_f = bmesh.new()
    add_box(bm_vid_f, 45.80, 48.00, -0.05, -0.03, 0.88, 2.22)
    create_mesh_object("Dulceria_Vidrio", bm_vid_f, mats["vidrio_comercial"], col)

    # Rótulo Corpóreo 3D DULCERIA "La Fuente"
    add_3d_text("Fuente_Txt_Dulceria", "DULCERIA", 0.36, 0.03, (47.00, -0.08, 3.85), ROT_SOUTH, mats["letras_azul"], col)
    add_3d_text("Fuente_Txt_Nombre", "\"La Fuente\"", 0.44, 0.035, (47.00, -0.08, 3.32), ROT_SOUTH, mats["letras_rojo"], col)

def build_rodeo_callejon(mats, col):
    """Cuerpo 5 y Callejón: Bar Rodeo / Karaoke y Paso al Estacionamiento (X in [49.50, 69.50 m])."""
    # Muros Bar Rodeo (X in [49.50, 63.00 m])
    bm_rodeo = bmesh.new()
    add_box(bm_rodeo, 49.50, 63.00, 0.00, 16.00, Z_BASE, 4.65)
    add_box(bm_rodeo, 49.45, 63.05, -0.05, 16.05, 4.65, 4.95) # Pretil
    create_mesh_object("Rodeo_Muros_Estructura", bm_rodeo, mats["stucco_blanco"], col)

    # Zócalo Verde Menta Pálido en PB en Resalte de 6 cm con Moldura de Pecho de Paloma
    bm_zoc = bmesh.new()
    add_box(bm_zoc, 49.45, 63.05, -0.08, 0.00, 0.00, 1.45)
    add_box(bm_zoc, 49.40, 63.10, -0.12, 0.00, 1.42, 1.50) # Moldura corrida
    create_mesh_object("Rodeo_Zocalo_Verde_Menta", bm_zoc, mats["stucco_menta"], col)

    # 2 Grandes Ventanales con Marcos y Celosías de Forja Negra 3D
    bm_cel = bmesh.new()
    bm_vid_r = bmesh.new()
    for xw1, xw2 in [(50.20, 55.40), (56.80, 62.00)]:
        # Marco de herrería
        add_box(bm_cel, xw1 - 0.06, xw2 + 0.06, -0.14, -0.02, 1.20, 3.20)
        # Vidrio interior
        add_box(bm_vid_r, xw1, xw2, -0.05, -0.03, 1.25, 3.15)
        # Retícula de barrotes cruzados de sección cuadrada (2.5 cm)
        num_bars = 9
        dx_bar = (xw2 - xw1) / num_bars
        for b in range(num_bars + 1):
            bx = xw1 + b * dx_bar
            add_box(bm_cel, bx - 0.015, bx + 0.015, -0.16, -0.04, 1.25, 3.15)
        for bz in [1.60, 2.05, 2.50, 2.95]:
            add_box(bm_cel, xw1, xw2, -0.16, -0.04, bz - 0.015, bz + 0.015)
    create_mesh_object("Rodeo_Celosias_Herreria", bm_cel, mats["herreria_negra"], col)
    create_mesh_object("Rodeo_Vidrios", bm_vid_r, mats["vidrio_comercial"], col)

    # Rótulo Corpóreo 3D RODEO BAR & KARAOKE en Fachada Frontal
    add_3d_text("Rodeo_Txt_Main", "RODEO BAR", 0.46, 0.04, (56.25, -0.10, 4.30), ROT_SOUTH, mats["rodeo_madera"], col)
    add_3d_text("Rodeo_Txt_Sub", "KARAOKE  &  DANCE", 0.22, 0.025, (56.25, -0.10, 3.82), ROT_SOUTH, mats["letras_blanco"], col)

    # Señalética Corpórea 3D en Testero del Callejón (X = 63.00 m)
    add_3d_text("Rodeo_Txt_Callejon_1", "ESTACIONAMIENTO PUBLICO", 0.28, 0.025, (63.08, 6.00, 3.80), ROT_EAST, mats["letras_blanco"], col)
    add_3d_text("Rodeo_Txt_Callejon_2", "KARAOKE  •  BILLAR  •  BAR", 0.20, 0.02, (63.08, 6.00, 3.35), ROT_EAST, mats["letras_dorado"], col)

    # Callejón de Estacionamiento: Firme de Concreto, Bardas y Portón al Fondo
    bm_call = bmesh.new()
    add_box(bm_call, 63.00, 69.50, 0.00, 36.00, -0.05, 0.02)
    # Bardas laterales de confinamiento de block
    add_box(bm_call, 62.85, 63.00, 16.00, 36.00, Z_BASE, 2.50)
    add_box(bm_call, 69.50, 69.65, 15.00, 36.00, Z_BASE, 2.50)
    # Albardillas de remate en bardas
    add_box(bm_call, 62.80, 63.05, 16.00, 36.00, 2.45, 2.55)
    add_box(bm_call, 69.45, 69.70, 15.00, 36.00, 2.45, 2.55)
    create_mesh_object("Callejon_Pavimento_Bardas", bm_call, mats["concreto_piso"], col)

    # Portón Corredizo de Reja Negra al Fondo del Callejón (Y = 36.00 m)
    bm_gate = bmesh.new()
    # Estructura de marco tubular
    add_box(bm_gate, 63.20, 69.30, 35.88, 36.05, 0.00, 2.80)
    # Rótulo de chapa metálica de Parking
    add_box(bm_gate, 64.50, 68.00, 35.85, 35.88, 2.10, 3.00)
    create_mesh_object("Callejon_Porton_Parking", bm_gate, mats["herreria_negra"], col)

    # Texto Corpóreo 3D PARKING $15 PESOS (Rotación ROT_SOUTH para el observador en el callejón)
    add_3d_text("Parking_Txt_North", "PARKING  $15  PESOS", 0.32, 0.025, (66.25, 35.82, 2.55), ROT_SOUTH, mats["letras_verde_neon"], col)

def build_hingkang_sky_locales(mats, col):
    """Cuerpos 6 a 9: Hing Kang, Distribuidor SKY, Local del Arco y Joyería (X in [69.50, 102.00 m])."""
    # Muros base de crujía comercial
    bm_muros = bmesh.new()
    add_box(bm_muros, 69.50, 82.50, 0.00, 15.00, Z_BASE, 4.65) # Hing Kang
    add_box(bm_muros, 82.50, 89.00, 0.00, 12.00, Z_BASE, 4.10) # SKY
    add_box(bm_muros, 89.00, 97.00, 0.00, 12.00, Z_BASE, 4.20) # Local del Arco
    add_box(bm_muros, 97.00, 102.00, 0.00, 11.00, Z_BASE, 3.90) # Joyería
    # Pretiles
    add_box(bm_muros, 69.45, 82.55, -0.05, 15.05, 4.65, 4.95)
    add_box(bm_muros, 82.45, 89.05, -0.05, 12.05, 4.10, 4.38)
    add_box(bm_muros, 88.95, 97.05, -0.05, 12.05, 4.20, 4.50)
    add_box(bm_muros, 96.95, 102.05, -0.05, 11.05, 3.90, 4.20)
    create_mesh_object("Comercial_Muros_Base", bm_muros, mats["stucco_blanco"], col)

    # Zócalo Rojo Bermellón de Hing Kang y SKY en PB (X: 69.50 - 89.00 m)
    bm_zoc_rojo = bmesh.new()
    add_box(bm_zoc_rojo, 69.45, 89.05, -0.08, 0.00, 0.00, 1.20)
    add_box(bm_zoc_rojo, 69.40, 89.10, -0.11, 0.00, 1.18, 1.24) # Moldura
    create_mesh_object("HingKang_Zocalo_Rojo", bm_zoc_rojo, mats["stucco_rojo"], col)

    # 1. Restaurante Hing Kang: Fascia de Caja Negra y Rótulos Corpóreos 3D
    bm_hk_sign = bmesh.new()
    # Caja portante negra
    add_box(bm_hk_sign, 70.00, 82.00, -0.28, -0.05, 3.42, 4.38)
    # Marco moldurado de aluminio
    add_box(bm_hk_sign, 69.95, 82.05, -0.30, -0.05, 4.35, 4.42)
    add_box(bm_hk_sign, 69.95, 82.05, -0.30, -0.05, 3.38, 3.45)
    create_mesh_object("HingKang_Caja_Letrero", bm_hk_sign, mats["aluminio_negro"], col)

    # Rótulos Corpóreos 3D Hing Kang y Comida China (Adelantados a Y = -0.33 m)
    add_3d_text("HingKang_Txt_Sub", "RESTAURANTE COMIDA CHINA", 0.22, 0.025, (76.00, -0.33, 4.15), ROT_SOUTH, mats["letras_dorado"], col)
    add_3d_text("HingKang_Txt_Main", "HING KANG", 0.54, 0.045, (76.00, -0.33, 3.65), ROT_SOUTH, mats["letras_rojo"], col)

    # Puerta en Arco de Medio Punto en PB
    bm_hk_door = bmesh.new()
    add_arch_spandrel_x(bm_hk_door, -0.12, 0.00, 74.80, 77.20, 1.40, 2.35, 2.50, segments=12)
    create_mesh_object("HingKang_Arco_Acceso", bm_hk_door, mats["stucco_rojo"], col)

    # Toldos Abombados Coca-Cola (Izquierdo y Derecho)
    bm_can_l = bmesh.new()
    add_canopy_quarter_round(bm_can_l, 70.20, 74.50, -0.10, 1.35, 1.85, 1.45)
    create_mesh_object("HingKang_Toldo_CocaCola_Izq", bm_can_l, mats["coca_cola_rojo"], col)

    bm_can_r = bmesh.new()
    add_canopy_quarter_round(bm_can_r, 77.50, 81.80, -0.10, 1.35, 1.85, 1.45)
    create_mesh_object("HingKang_Toldo_CocaCola_Der", bm_can_r, mats["coca_cola_rojo"], col)

    # Textos Corpóreos 3D Coca-Cola en Faldón Festoneado Blanco
    add_3d_text("Toldo_Txt_CocaCola_L", "Coca-Cola", 0.22, 0.02, (72.35, -1.48, 1.78), ROT_SOUTH, mats["letras_blanco"], col)
    add_3d_text("Toldo_Txt_CocaCola_R", "Coca-Cola", 0.22, 0.02, (79.65, -1.48, 1.78), ROT_SOUTH, mats["letras_blanco"], col)

    # Tótems de Azotea: Letrero Parking y Tótem Cerveza Tecate
    bm_hk_tot = bmesh.new()
    # Estructura de celosía del letrero Parking
    add_box(bm_hk_tot, 70.50, 73.50, 0.40, 0.60, 4.95, 6.45)
    add_box(bm_hk_tot, 70.95, 71.05, 0.45, 0.55, 4.65, 4.95)
    add_box(bm_hk_tot, 72.95, 73.05, 0.45, 0.55, 4.65, 4.95)
    # Tótem Cerveza Tecate
    add_box(bm_hk_tot, 82.20, 82.70, 0.30, 0.50, 4.80, 7.50)
    add_box(bm_hk_tot, 82.15, 82.75, 0.28, 0.52, 5.20, 7.45)
    create_mesh_object("HingKang_Totems_Azotea", bm_hk_tot, mats["acero_galvanizado"], col)

    add_3d_text("Totem_Txt_Tecate", "TECATE", 0.38, 0.035, (82.45, 0.24, 6.80), ROT_SOUTH, mats["letras_rojo"], col)
    add_3d_text("Totem_Txt_Parking", "PARKING", 0.28, 0.03, (72.00, 0.36, 5.70), ROT_SOUTH, mats["letras_blanco"], col)

    # 2. Distribuidor SKY: Marquesina Abovedada Azul y Rótulo Corpóreo 3D
    bm_sky = bmesh.new()
    add_canopy_quarter_round(bm_sky, 82.80, 88.60, -0.08, 0.85, 2.75, 0.90)
    create_mesh_object("SKY_Marquesina_Azul", bm_sky, mats["sky_azul"], col)

    # Rótulo Corpóreo 3D SKY
    add_3d_text("SKY_Txt_Main", "SKY", 0.48, 0.035, (85.70, -0.96, 3.32), ROT_SOUTH, mats["letras_blanco"], col)
    add_3d_text("SKY_Txt_Sub", "DISTRIBUIDOR AUTORIZADO", 0.16, 0.02, (85.70, -0.96, 2.92), ROT_SOUTH, mats["letras_blanco"], col)

    # Escaparate inferior de aluminio blanco
    bm_sky_canc = bmesh.new()
    add_box(bm_sky_canc, 82.80, 88.60, -0.10, 0.00, 0.00, 2.65)
    add_box(bm_sky_canc, 85.60, 85.80, -0.12, 0.00, 0.00, 2.65)
    create_mesh_object("SKY_Canceleria_Aluminio", bm_sky_canc, mats["aluminio_blanco"], col)

    bm_sky_vid = bmesh.new()
    add_box(bm_sky_vid, 82.85, 88.55, -0.05, -0.03, 0.20, 2.60)
    create_mesh_object("SKY_Vidrios", bm_sky_vid, mats["vidrio_comercial"], col)

    # 3. Local del Arco Tradicional: 5 Canes de Madera, Arco de Dovelas de Ladrillo y Mostrador de Madera
    bm_arco = bmesh.new()
    # 5 Canes de vigas de madera oscura salientes del pretil
    for x in [89.5, 91.0, 93.0, 95.0, 96.5]:
        add_box(bm_arco, x - 0.09, x + 0.09, -0.60, 0.00, 3.75, 3.95)
    create_mesh_object("Local_Arco_Canes_Madera", bm_arco, mats["madera_canes"], col)

    # Dovelas de ladrillo decimonónico en resalte volumétrico de 6 cm
    bm_dovelas = bmesh.new()
    add_arch_spandrel_x(bm_dovelas, -0.15, -0.04, 89.40, 96.60, 1.80, 2.90, 3.65, segments=16)
    create_mesh_object("Local_Arco_Dovelas_Ladrillo", bm_dovelas, mats["ladrillo_dovelas"], col, uv_scale=1.5)

    # Mostrador y ventanal interior tradicional de madera con vidrio
    bm_arco_canc = bmesh.new()
    bm_arco_vid = bmesh.new()
    # Barra baja tradicional de madera
    add_box(bm_arco_canc, 89.60, 96.40, -0.10, 0.00, 0.00, 1.10)
    # Montantes y travesaños de madera en vano
    add_box(bm_arco_canc, 89.60, 89.75, -0.10, 0.00, 1.10, 2.65)
    add_box(bm_arco_canc, 96.25, 96.40, -0.10, 0.00, 1.10, 2.65)
    add_box(bm_arco_canc, 92.90, 93.10, -0.10, 0.00, 1.10, 2.80)
    add_box(bm_arco_canc, 89.60, 96.40, -0.10, 0.00, 1.95, 2.05)
    # Vidrios
    add_box(bm_arco_vid, 89.75, 96.25, -0.06, -0.04, 1.10, 2.65)
    create_mesh_object("Local_Arco_Canceleria", bm_arco_canc, mats["madera_canes"], col)
    create_mesh_object("Local_Arco_Vidrios", bm_arco_vid, mats["vidrio_comercial"], col)

    # 4. Local Joyería: Toldo Festoneado y Rótulos Corpóreos 3D
    bm_joya = bmesh.new()
    add_canopy_quarter_round(bm_joya, 97.40, 101.60, -0.08, 0.95, 2.75, 0.75)
    create_mesh_object("Joyeria_Toldo_Azul", bm_joya, mats["sky_azul"], col)

    add_3d_text("Joyeria_Txt_Main", "JOYERIA", 0.34, 0.03, (99.50, -1.06, 3.22), ROT_SOUTH, mats["letras_dorado"], col)
    add_3d_text("Joyeria_Txt_Sub", "ANILLOS DE GRADUACION", 0.16, 0.02, (99.50, -1.06, 2.82), ROT_SOUTH, mats["letras_blanco"], col)

    # Escaparate acristalado de joyería
    bm_joya_canc = bmesh.new()
    add_box(bm_joya_canc, 97.40, 101.60, -0.10, 0.00, 0.00, 2.65)
    create_mesh_object("Joyeria_Canceleria_Aluminio", bm_joya_canc, mats["aluminio_blanco"], col)

    bm_joya_vid = bmesh.new()
    add_box(bm_joya_vid, 97.45, 101.55, -0.05, -0.03, 0.30, 2.60)
    create_mesh_object("Joyeria_Vidrios", bm_joya_vid, mats["vidrio_comercial"], col)

def build_michoacana_ortizrubio(mats, col):
    """Cuerpo 10: La Michoacana y locales sobre Ortiz Rubio (X in [102.00, 112.50 m], Y in [0.00, 22.00 m])."""
    # Muros base de La Michoacana y locales este
    bm_muros = bmesh.new()
    add_box(bm_muros, 102.00, 112.50, 0.00, 7.50, Z_BASE, 4.30) # La Michoacana
    add_box(bm_muros, 104.00, 112.50, 7.50, 13.50, Z_BASE, 3.90) # San Diego Beauty Salon
    add_box(bm_muros, 104.00, 112.50, 13.50, 22.00, Z_BASE, 3.60) # Murillo's Cerrajería
    # Pretiles
    add_box(bm_muros, 101.95, 112.55, -0.05, 7.55, 4.30, 4.60)
    add_box(bm_muros, 103.95, 112.55, 7.45, 13.55, 3.90, 4.20)
    add_box(bm_muros, 103.95, 112.55, 13.45, 22.05, 3.60, 3.90)
    create_mesh_object("Michoacana_Muros_Estructura", bm_muros, mats["stucco_amarillo"], col)

    # 1. La Michoacana Esquina: Mostrador en Escuadra y Fascia Rosa
    bm_mostrador = bmesh.new()
    # Barra baja en escuadra Juárez y Ortiz Rubio con azulejo verde
    add_box(bm_mostrador, 102.20, 112.40, -0.22, 0.00, 0.00, 1.15) # Tramo Sur
    add_box(bm_mostrador, 112.50, 112.72, 0.00, 7.20, 0.00, 1.15) # Tramo Este
    create_mesh_object("Michoacana_Barra_Mosaico", bm_mostrador, mats["michoacana_mosaico"], col)

    # Encimera y Tapas Cilíndricas de Acero Inoxidable para Nieve
    bm_tapas = bmesh.new()
    # Encimera superior de barra
    add_box(bm_tapas, 102.15, 112.45, -0.26, 0.04, 1.15, 1.20)
    add_box(bm_tapas, 112.46, 112.76, -0.04, 7.24, 1.15, 1.20)
    # Tapas redondas de botes de nieve incrustadas
    for tx in [103.5, 105.0, 106.5, 108.0, 109.5, 111.0]:
        add_box(bm_tapas, tx - 0.20, tx + 0.20, -0.22, -0.04, 1.20, 1.24)
    create_mesh_object("Michoacana_Encimera_AceroInox", bm_tapas, mats["acero_inoxidable"], col)

    # Columnas Cuadradas Amarillas en Esquina
    bm_cols = bmesh.new()
    for cx, cy in [(102.20, -0.10), (107.00, -0.10), (112.35, -0.10), (112.35, 3.60), (112.35, 7.20)]:
        add_box(bm_cols, cx - 0.22, cx + 0.22, cy - 0.22, cy + 0.22, 1.20, 3.20)
        # Capitel escalonado
        add_box(bm_cols, cx - 0.28, cx + 0.28, cy - 0.28, cy + 0.28, 3.12, 3.22)
    create_mesh_object("Michoacana_Columnas_Amarillas", bm_cols, mats["stucco_amarillo"], col)

    # Fascia Curva Magenta / Rosa Mexicano Envolvente
    bm_fas_m = bmesh.new()
    add_box(bm_fas_m, 101.90, 112.60, -0.36, -0.05, 3.20, 4.30)
    add_box(bm_fas_m, 112.50, 112.82, -0.05, 7.50, 3.20, 4.30)
    # Molduras de remate en fascia
    add_box(bm_fas_m, 101.85, 112.65, -0.40, -0.05, 4.25, 4.35)
    add_box(bm_fas_m, 112.50, 112.86, -0.05, 7.55, 4.25, 4.35)
    create_mesh_object("Michoacana_Fascia_Rosa", bm_fas_m, mats["michoacana_rosa"], col)

    # Rótulos Corpóreos 3D LA MICHOACANA en Fachada Sur y Este
    add_3d_text("Michoacana_Txt_South_1", "LA MICHOACANA", 0.52, 0.04, (107.25, -0.40, 3.85), ROT_SOUTH, mats["letras_amarillo"], col)
    add_3d_text("Michoacana_Txt_South_2", "PALETERIA  Y  NEVERIA", 0.20, 0.02, (107.25, -0.40, 3.45), ROT_SOUTH, mats["letras_blanco"], col)
    add_3d_text("Michoacana_Txt_East", "LA MICHOACANA", 0.44, 0.035, (112.86, 3.75, 3.85), ROT_EAST, mats["letras_amarillo"], col)

    # 2. Locales Este sobre Calle Pdte. Pascual Ortiz Rubio
    # San Diego Beauty Salon (Y: 7.50 a 13.50 m)
    bm_beauty = bmesh.new()
    # Muro salmón
    add_box(bm_beauty, 112.45, 112.55, 7.50, 13.50, 0.00, 3.90)
    # Caja letrero blanca
    add_box(bm_beauty, 112.50, 112.74, 7.80, 13.20, 2.85, 3.75)
    # Cancelería de aluminio blanco
    add_box(bm_beauty, 112.50, 112.62, 8.20, 12.80, 0.35, 2.65)
    create_mesh_object("Beauty_Salon_Estructura", bm_beauty, mats["stucco_salmon"], col)

    bm_beauty_vid = bmesh.new()
    add_box(bm_beauty_vid, 112.52, 112.56, 8.25, 12.75, 0.40, 2.60)
    create_mesh_object("Beauty_Salon_Vidrios", bm_beauty_vid, mats["vidrio_comercial"], col)

    add_3d_text("Beauty_Txt_Main", "SAN DIEGO", 0.38, 0.03, (112.76, 10.50, 3.42), ROT_EAST, mats["michoacana_rosa"], col)
    add_3d_text("Beauty_Txt_Sub", "BEAUTY SALON • ESTETICA UNISEX", 0.16, 0.02, (112.76, 10.50, 3.08), ROT_EAST, mats["herreria_negra"], col)

    # Murillo's Cerrajería (Y: 13.50 a 22.00 m)
    bm_cerraj = bmesh.new()
    # Muro azul
    add_box(bm_cerraj, 112.45, 112.55, 13.50, 22.00, 0.00, 3.60)
    # Caja letrero amarilla
    add_box(bm_cerraj, 112.50, 112.74, 14.00, 18.50, 2.65, 3.48)
    # Portón metálico de taller
    add_box(bm_cerraj, 112.50, 112.60, 14.20, 18.20, 0.00, 2.50)
    create_mesh_object("Cerrajeria_Estructura", bm_cerraj, mats["stucco_azul"], col)

    add_3d_text("Cerrajeria_Txt_Main", "CERRAJERIA MURILLO", 0.34, 0.03, (112.76, 16.25, 3.20), ROT_EAST, mats["letras_amarillo"], col)
    add_3d_text("Cerrajeria_Txt_Sub", "LLAVES CON CHIP • APERTURAS • DUPLICADOS", 0.15, 0.02, (112.76, 16.25, 2.85), ROT_EAST, mats["letras_blanco"], col)

    # 3. Monumental Cartelera Espectacular de Azotea a Dos Caras (SIESA y CAEM)
    bm_billboard = bmesh.new()
    # Cerchas espaciales tridimensionales de tubo galvanizado
    add_space_frame_truss(bm_billboard, 102.20, 112.20, 2.20, 4.80, 4.30, 8.50, subdivisions=6)
    # Pasarela de servicio y barandal de mantenimiento
    add_box(bm_billboard, 102.00, 112.40, 4.80, 5.60, 8.40, 8.55)
    add_box(bm_billboard, 102.00, 112.40, 5.55, 5.65, 8.55, 9.60) # Barandal
    # Bastidor del panel publicitario
    add_box(bm_billboard, 101.90, 112.50, 2.10, 2.30, 8.50, H_ESPECTACULAR)
    create_mesh_object("Espectacular_Estructura_Acero", bm_billboard, mats["acero_galvanizado"], col)

    # Paneles de Fondo de Cartelera
    bm_panel_s = bmesh.new()
    add_box(bm_panel_s, 102.00, 112.40, 2.08, 2.12, 8.55, H_ESPECTACULAR - 0.05)
    create_mesh_object("Espectacular_Panel_Sur", bm_panel_s, mats["stucco_azul"], col)

    bm_panel_n = bmesh.new()
    add_box(bm_panel_n, 102.00, 112.40, 2.28, 2.32, 8.55, H_ESPECTACULAR - 0.05)
    create_mesh_object("Espectacular_Panel_Norte", bm_panel_n, mats["stucco_blanco"], col)

    # Rótulos Corpóreos 3D Cara Sur: GRUPO SIESA
    add_3d_text("SIESA_Txt_Main", "GRUPO SIESA", 0.72, 0.045, (107.25, 2.04, 11.85), ROT_SOUTH, mats["letras_dorado"], col)
    add_3d_text("SIESA_Txt_Sub1", "SEGURIDAD PRIVADA • CCTV • GUARDIAS", 0.24, 0.025, (107.25, 2.04, 10.75), ROT_SOUTH, mats["letras_blanco"], col)
    add_3d_text("SIESA_Txt_Sub2", "TEL. 654-20-00", 0.22, 0.02, (107.25, 2.04, 9.85), ROT_SOUTH, mats["letras_blanco"], col)

    # Rótulos Corpóreos 3D Cara Norte: CAEM
    add_3d_text("CAEM_Txt_Main", "CAEM", 0.90, 0.045, (107.25, 2.36, 11.75), ROT_NORTH, mats["letras_rojo"], col)
    add_3d_text("CAEM_Txt_Sub1", "CENTRO DE ARTES Y ESTUDIOS MUSICALES", 0.22, 0.025, (107.25, 2.36, 10.55), ROT_NORTH, mats["herreria_negra"], col)
    add_3d_text("CAEM_Txt_Sub2", "CANTO • GUITARRA • PIANO • BATERIA", 0.18, 0.02, (107.25, 2.36, 9.75), ROT_NORTH, mats["letras_dorado"], col)

def build_rooftops_and_services(mats, col):
    """Instalaciones técnicas de azotea: A/C tipo minisplit, tinacos, chimeneas y bajantes."""
    bm_tech = bmesh.new()

    # 1. Unidades de Aire Acondicionado Minisplit y Paquete HVAC
    for ac_x, ac_y, ac_z in [(15.0, 8.0, 11.50), (32.0, 6.0, 4.30), (74.0, 6.0, 4.65), (93.0, 5.0, 4.20)]:
        # Condensador HVAC
        add_box(bm_tech, ac_x - 0.80, ac_x + 0.80, ac_y - 0.60, ac_y + 0.60, ac_z, ac_z + 0.95)
        # Soportes angulares de fierro
        add_box(bm_tech, ac_x - 0.85, ac_x - 0.75, ac_y - 0.65, ac_y + 0.65, ac_z - 0.15, ac_z)
        add_box(bm_tech, ac_x + 0.75, ac_x + 0.85, ac_y - 0.65, ac_y + 0.65, ac_z - 0.15, ac_z)

    # 2. Tinacos rotomoldeados negros en azotea
    for t_x, t_y, t_z in [(22.0, 10.0, 11.50), (45.0, 7.0, 4.30), (85.0, 6.0, 4.10)]:
        add_box(bm_tech, t_x - 0.65, t_x + 0.65, t_y - 0.65, t_y + 0.65, t_z, t_z + 1.40)

    # 3. Bajantes pluviales verticales de lámina galvanizada
    for bx, by, bz_top in [(26.40, -0.05, 7.20), (37.05, -0.05, 4.30), (62.95, -0.05, 4.65), (82.45, -0.05, 4.65)]:
        add_box(bm_tech, bx - 0.04, bx + 0.04, by - 0.08, by, 0.00, bz_top)

    create_mesh_object("Instalaciones_Azoteas_HVAC", bm_tech, mats["acero_galvanizado"], col)

# ---------------------------------------------------------------------------
# 5. Exportador Godot .tscn con Colisiones Analíticas BoxShape3D
# ---------------------------------------------------------------------------
def generate_godot_tscn(tscn_path, glb_path):
    """Escribe escena Godot 4 con colisionadores analíticos y sincronización canónica Z_godot = -Y_blender."""
    content = f"""[gd_scene load_steps=17 format=3 uid="uid://edificio_juarez_235_prod_v4"]

[ext_resource type="PackedScene" path="{glb_path}" id="1_mesh"]

[sub_resource type="BoxShape3D" id="Box_Baratero_Frontal"]
size = Vector3(26.50, 7.50, 16.00)

[sub_resource type="BoxShape3D" id="Box_Baratero_Nave"]
size = Vector3(26.50, 9.40, 20.00)

[sub_resource type="BoxShape3D" id="Box_Darce"]
size = Vector3(10.50, 4.30, 14.50)

[sub_resource type="BoxShape3D" id="Box_Local_Blanco"]
size = Vector3(4.50, 3.80, 12.00)

[sub_resource type="BoxShape3D" id="Box_La_Fuente"]
size = Vector3(8.00, 4.30, 14.00)

[sub_resource type="BoxShape3D" id="Box_Rodeo_Bar"]
size = Vector3(13.50, 4.65, 16.00)

[sub_resource type="BoxShape3D" id="Box_Hing_Kang"]
size = Vector3(13.00, 4.65, 15.00)

[sub_resource type="BoxShape3D" id="Box_SKY"]
size = Vector3(6.50, 4.10, 12.00)

[sub_resource type="BoxShape3D" id="Box_Arco_Tradicional"]
size = Vector3(8.00, 4.20, 12.00)

[sub_resource type="BoxShape3D" id="Box_Joyeria"]
size = Vector3(5.00, 3.90, 11.00)

[sub_resource type="BoxShape3D" id="Box_Michoacana"]
size = Vector3(10.50, 4.30, 7.50)

[sub_resource type="BoxShape3D" id="Box_Beauty_Salon"]
size = Vector3(8.50, 3.90, 6.00)

[sub_resource type="BoxShape3D" id="Box_Cerrajeria"]
size = Vector3(8.50, 3.60, 8.50)

[sub_resource type="BoxShape3D" id="Box_Barda_Norte_1"]
size = Vector3(37.00, 2.50, 0.40)

[sub_resource type="BoxShape3D" id="Box_Barda_Norte_2"]
size = Vector3(33.00, 2.50, 0.40)

[node name="Edificio_Juarez_235" type="StaticBody3D"]

[node name="ModelInstance" parent="." instance=ExtResource("1_mesh")]

[node name="Col_Baratero_Frontal" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 13.25, 3.75, -8.00)
shape = SubResource("Box_Baratero_Frontal")

[node name="Col_Baratero_Nave" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 13.25, 4.70, -26.00)
shape = SubResource("Box_Baratero_Nave")

[node name="Col_Darce" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 31.75, 2.15, -7.25)
shape = SubResource("Box_Darce")

[node name="Col_Local_Blanco" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 39.25, 1.90, -6.00)
shape = SubResource("Box_Local_Blanco")

[node name="Col_La_Fuente" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 45.50, 2.15, -7.00)
shape = SubResource("Box_La_Fuente")

[node name="Col_Rodeo_Bar" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 56.25, 2.32, -8.00)
shape = SubResource("Box_Rodeo_Bar")

[node name="Col_Hing_Kang" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 76.00, 2.32, -7.50)
shape = SubResource("Box_Hing_Kang")

[node name="Col_SKY" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 85.75, 2.05, -6.00)
shape = SubResource("Box_SKY")

[node name="Col_Arco_Tradicional" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 93.00, 2.10, -6.00)
shape = SubResource("Box_Arco_Tradicional")

[node name="Col_Joyeria" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 99.50, 1.95, -5.50)
shape = SubResource("Box_Joyeria")

[node name="Col_Michoacana" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 107.25, 2.15, -3.75)
shape = SubResource("Box_Michoacana")

[node name="Col_Beauty_Salon" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 108.25, 1.95, -10.50)
shape = SubResource("Box_Beauty_Salon")

[node name="Col_Cerrajeria" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 108.25, 1.80, -17.75)
shape = SubResource("Box_Cerrajeria")

[node name="Col_Barda_Norte_1" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 45.00, 1.25, -36.00)
shape = SubResource("Box_Barda_Norte_1")

[node name="Col_Barda_Norte_2" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 85.50, 1.25, -36.00)
shape = SubResource("Box_Barda_Norte_2")
"""
    with open(tscn_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Escena Godot .tscn generada con éxito: {tscn_path}")

# ---------------------------------------------------------------------------
# 6. Suite de 8 Cámaras Técnicas y Renderizado Closed-Loop
# ---------------------------------------------------------------------------
def setup_lighting_and_cameras(col):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720

    # Sol Diurno
    sun_data = bpy.data.lights.new(name="Sun_Light", type='SUN')
    sun_data.energy = 4.2
    sun_data.color = (1.0, 0.98, 0.94)
    sun_obj = bpy.data.objects.new("Sun", sun_data)
    sun_obj.rotation_euler = (math.radians(52.0), math.radians(18.0), math.radians(-35.0))
    col.objects.link(sun_obj)

    # Domo de Luz Ambiental Uniforme
    world = scene.world
    if not world:
        world = bpy.data.worlds.new("World_Sky")
        scene.world = world
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs['Color'].default_value = (0.75, 0.85, 0.95, 1.0)
        bg_node.inputs['Strength'].default_value = 1.35

    cameras = {}
    cam_specs = [
        # Cam 1: Vista Baratero completa abarcando PB, PA y frontispicio de 11.50m
        ("Cam_01_Frontal_Baratero_45", (13.25, -28.0, 6.8), (math.radians(78.0), 0.0, math.radians(0.0))),
        # Cam 2: Centro Oeste (D'Arce, Local Blanco, La Fuente)
        ("Cam_02_Frontal_Centro_Oeste", (40.0, -18.0, 3.8), (math.radians(82.0), 0.0, math.radians(0.0))),
        # Cam 3: Callejón y portón del fondo
        ("Cam_03_Callejon_Estacionamiento", (66.25, -14.0, 2.5), (math.radians(85.0), 0.0, math.radians(0.0))),
        # Cam 4: Centro Este (Hing Kang, SKY, Arco Tradicional, Joyería)
        ("Cam_04_Frontal_Centro_Este", (86.0, -19.0, 3.8), (math.radians(82.0), 0.0, math.radians(0.0))),
        # Cam 5: Michoacana y Cartelera Monumental de 13.50m (SIESA)
        ("Cam_05_Frontal_Michoacana_45", (107.0, -32.0, 7.5), (math.radians(78.0), 0.0, math.radians(10.0))),
        # Cam 6: Lateral Cárdenas abarcando toda la nave verde, pilastras fucsias y PRI
        ("Cam_06_Lateral_Cardenas_Oeste", (-40.0, 18.0, 6.5), (math.radians(78.0), 0.0, math.radians(-90.0))),
        # Cam 7: Lateral Ortiz Rubio (Michoacana, Beauty Salon, Cerrajería)
        ("Cam_07_Lateral_OrtizRubio_Este", (130.0, 10.0, 3.8), (math.radians(82.0), 0.0, math.radians(90.0))),
        # Cam 8: Cenital amplia de azoteas
        ("Cam_08_Cenital_Azoteas_Z60", (56.0, 18.0, 70.0), (math.radians(0.0), 0.0, math.radians(0.0)))
    ]

    for name, loc, rot in cam_specs:
        cam_data = bpy.data.cameras.new(name)
        cam_data.lens = 24.0 if "Michoacana" in name else (28.0 if ("Cenital" in name or "Baratero" in name) else 32.0)
        cam_obj = bpy.data.objects.new(name, cam_data)
        cam_obj.location = loc
        cam_obj.rotation_euler = rot
        col.objects.link(cam_obj)
        cameras[name] = cam_obj

    return cameras

def render_validation_suite(cameras):
    scene = bpy.context.scene
    for cam_name, cam_obj in cameras.items():
        print(f"Renderizando vista técnica fotorrealista: {cam_name}...")
        scene.camera = cam_obj
        out_file = os.path.join(DOCS_IMAGES_DIR, f"{cam_name}.png")
        scene.render.filepath = out_file
        bpy.ops.render.render(write_still=True)
        print(f"  Guardado render: {out_file}")

# ---------------------------------------------------------------------------
# 7. Función Principal de Orquestación
# ---------------------------------------------------------------------------
def main():
    print("===========================================================================")
    print("INICIANDO RECONSTRUCCIÓN PROCEDURAL 100% MESHES DE AV. BENITO JUÁREZ 235 (V4.1)")
    print("===========================================================================")

    root_col = clean_scene()
    mats = create_all_materials()

    # Construcción de cuerpos
    build_baratero_pri(mats, root_col)
    build_restaurant_darce(mats, root_col)
    build_local_blanco_lafuente(mats, root_col)
    build_rodeo_callejon(mats, root_col)
    build_hingkang_sky_locales(mats, root_col)
    build_michoacana_ortizrubio(mats, root_col)
    build_rooftops_and_services(mats, root_col)

    # Configuración de cámaras
    cams = setup_lighting_and_cameras(root_col)

    # Guardar archivo .blend maestro
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"Archivo .blend maestro guardado en: {BLEND_PATH}")

    # Exportar archivo de producción glTF/GLB (convirtiendo automáticamente textos a mallas)
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
    print(f"Modelo glTF de producción exportado: {GLB_PATH}")

    # Generar escena Godot .tscn
    generate_godot_tscn(TSCN_PATH, "res://assets/buildings/edificio_juarez_235.glb")

    # Ejecutar suite de validación visual
    render_validation_suite(cams)

    print("===========================================================================")
    print("PROCESO PROCEDURAL 100% MESHES FINALIZADO EXITOSAMENTE")
    print("===========================================================================")

if __name__ == "__main__":
    main()
