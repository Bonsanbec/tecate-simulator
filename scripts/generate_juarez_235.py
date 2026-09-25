"""
=============================================================================
GENERADOR PROCEDURAL 3D UNIVERSAL: CONJUNTO COMERCIAL AV. BENITO JUÁREZ 235
(ÉPOCA HISTÓRICA: 2009 - VERSIÓN DE PRODUCCIÓN FOTORREALISTA GROUND-TRUTH V2.0)
=============================================================================
Inmueble continuo comercial en Tecate, B.C., Manzana block_lat_32.57381_lon_-116.62658:
  - Crujía completa de 104.43 m sobre Av. Benito Juárez, frente al Parque Miguel Hidalgo.
  - Límites: Desde el Poniente en Pdte. Lázaro Cárdenas (EL BARATERO / PRI) hasta
    el Oriente en Pdte. Pascual Ortiz Rubio (LA MICHOACANA).
  - Incluye los 10 edificios continuos con su volumetría real, vanos, cancelerías,
    marquesinas, techumbres de teja, toldos de lona y rótulos 3D de 2009.
  - Callejón central vehicular diáfano transitable hacia el patio y estacionamiento interior.
  - Alzados laterales completos en Cárdenas (nave verde y pilastras magenta) y
    Ortiz Rubio (San Diego Beauty Salon, Cerrajería Murillo's, barda y accesos).
  - Fachadas posteriores/reversas selladas hacia el patio interior y Callejón Libertad.
  - Zócalo perimetral continuo enterrado a Z <= -1.30 m para absorción de pendiente vial.
  - Cero banquetas embebidas en el modelo .glb (pertenecen a capas GIS).
  - Colisiones analíticas en Godot 4 (.tscn) con inversión canónica Z_godot = -Y_blender.
  - Iluminación diurna Cycles con luz solar y domo de cielo suave para sombras naturales.
  - Batería de 8 cámaras técnicas para validación closed-loop.
=============================================================================
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Euler, Matrix

# ---------------------------------------------------------------------------
# 0. Rutas Canónicas del Proyecto
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLEND_OUT = os.path.join(BASE_DIR, "blender_assets", "buildings", "edificio_juarez_235.blend")
GLB_OUT = os.path.join(BASE_DIR, "godot_project", "assets", "buildings", "edificio_juarez_235.glb")
TSCN_OUT = os.path.join(BASE_DIR, "godot_project", "assets", "buildings", "edificio_juarez_235.tscn")
RENDERS_DIR = os.path.join(BASE_DIR, "docs", "images", "juarez_235")
TEXTURES_DIR = os.path.join(BASE_DIR, "godot_project", "assets", "textures")

# ---------------------------------------------------------------------------
# 1. Utilidades Geométricas Procedurales y Mapeo UV
# ---------------------------------------------------------------------------

def clean_scene(collection_name="Juarez_235_Root"):
    """Inicializa la escena vacía y crea la colección raíz."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)
    root_col = bpy.data.collections.new(collection_name)
    scene.collection.children.link(root_col)
    return root_col

def add_box(bm, x1, x2, y1, y2, z1, z2):
    """Genera una caja cerrada ortogonal con normales hacia el exterior."""
    xmin, xmax = min(x1, x2), max(x1, x2)
    ymin, ymax = min(y1, y2), max(y1, y2)
    zmin, zmax = min(z1, z2), max(z1, z2)

    verts = [
        bm.verts.new((xmin, ymin, zmin)), bm.verts.new((xmax, ymin, zmin)),
        bm.verts.new((xmax, ymax, zmin)), bm.verts.new((xmin, ymax, zmin)),
        bm.verts.new((xmin, ymin, zmax)), bm.verts.new((xmax, ymin, zmax)),
        bm.verts.new((xmax, ymax, zmax)), bm.verts.new((xmin, ymax, zmax))
    ]
    bm.faces.new((verts[0], verts[1], verts[2], verts[3])) # -Z
    bm.faces.new((verts[4], verts[7], verts[6], verts[5])) # +Z
    bm.faces.new((verts[0], verts[4], verts[5], verts[1])) # -Y (Frontal Sur)
    bm.faces.new((verts[1], verts[5], verts[6], verts[2])) # +X (Oriente)
    bm.faces.new((verts[2], verts[6], verts[7], verts[3])) # +Y (Trasera Norte)
    bm.faces.new((verts[3], verts[7], verts[4], verts[0])) # -X (Poniente)
    return verts

def auto_uv_bmesh(bm, scale_u=0.5, scale_v=0.5):
    """Genera coordenadas UV triplanares en TEXCOORD_0."""
    uv_layer = bm.loops.layers.uv.verify()
    for face in bm.faces:
        n = face.normal
        nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)
        for loop in face.loops:
            v = loop.vert.co
            if nx >= ny and nx >= nz:
                u = v.y * scale_u
                w = v.z * scale_v
            elif ny >= nx and ny >= nz:
                u = v.x * scale_u
                w = v.z * scale_v
            else:
                u = v.x * scale_u
                w = v.y * scale_v
            loop[uv_layer].uv = (u, w)

def add_teja_ribs_x(bm, x_start, x_end, y_eave, y_ridge, z_eave, z_ridge, spacing=0.45):
    """Genera hiladas longitudinales de teja colonial curva a lo largo de X."""
    num_ribs = max(1, int((x_end - x_start) / spacing))
    delta_y = abs(y_ridge - y_eave)
    for i in range(num_ribs):
        xc = x_start + (i + 0.5) * spacing
        zr = z_eave + (z_ridge - z_eave)
        v0 = bm.verts.new((xc - 0.12, y_eave, z_eave + 0.04))
        v1 = bm.verts.new((xc + 0.12, y_eave, z_eave + 0.04))
        v2 = bm.verts.new((xc + 0.12, y_ridge, zr + 0.04))
        v3 = bm.verts.new((xc - 0.12, y_ridge, zr + 0.04))
        v_top0 = bm.verts.new((xc, y_eave, z_eave + 0.12))
        v_top1 = bm.verts.new((xc, y_ridge, zr + 0.12))

        bm.faces.new((v0, v1, v_top0))
        bm.faces.new((v1, v2, v_top1, v_top0))
        bm.faces.new((v2, v3, v_top1))
        bm.faces.new((v3, v0, v_top0, v_top1))

def add_canopy_quarter_round(bm, x1, x2, y_back, y_front, z_bot, z_top, segments=8):
    """Construye un toldo semicircular/curvo de lona (quarter round canopy)."""
    r_y = abs(y_front - y_back)
    r_z = abs(z_top - z_bot)

    pts = []
    for i in range(segments + 1):
        angle = (math.pi * 0.5) * (i / segments)
        y = y_back - r_y * math.cos(angle)
        z = z_top - r_z * (1.0 - math.sin(angle))
        pts.append((y, z))

    for i in range(segments):
        y0, z0 = pts[i]
        y1, z1 = pts[i+1]
        v_bl = bm.verts.new((x1, y0, z0))
        v_br = bm.verts.new((x2, y0, z0))
        v_tr = bm.verts.new((x2, y1, z1))
        v_tl = bm.verts.new((x1, y1, z1))
        bm.faces.new((v_bl, v_br, v_tr, v_tl))

    # Tapas laterales izquierda y derecha
    for x_cap, is_left in [(x1, True), (x2, False)]:
        verts_cap = [bm.verts.new((x_cap, y, z)) for y, z in pts]
        v_origin = bm.verts.new((x_cap, y_back, z_top))
        for i in range(segments):
            if is_left:
                bm.faces.new((v_origin, verts_cap[i], verts_cap[i+1]))
            else:
                bm.faces.new((v_origin, verts_cap[i+1], verts_cap[i]))

def add_arch_spandrel_x(bm, y_min, y_max, x_start, x_end, z_spring, z_crown, z_top, segments=12):
    """Construye un arco rebajado a lo largo del eje X con dovelas en relieve."""
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

def create_mesh_object(name, bm, material, col, uv_scale=0.5):
    """Mapea UVs, recalcula normales, crea el objeto Mesh y lo vincula."""
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
    """Crea tipografía tridimensional orientada anti-espejo."""
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
# 2. Especificación y Calibración de Shaders PBR Nativos
# ---------------------------------------------------------------------------

def make_pbr(name, base_color, roughness=0.85, metallic=0.0, alpha=1.0, tex_prefix=None, use_tex_albedo=True):
    """Crea un material Principled BSDF PBR calibrado."""
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

    if tex_prefix:
        alb_path = os.path.join(TEXTURES_DIR, f"{tex_prefix}_albedo.png")
        norm_path = os.path.join(TEXTURES_DIR, f"{tex_prefix}_normal.png")
        rough_path = os.path.join(TEXTURES_DIR, f"{tex_prefix}_roughness.png")

        tex_coord = nodes.new(type='ShaderNodeTexCoord')

        if use_tex_albedo and os.path.exists(alb_path):
            t_alb = nodes.new(type='ShaderNodeTexImage')
            t_alb.image = bpy.data.images.load(alb_path)
            mat.node_tree.links.new(tex_coord.outputs['UV'], t_alb.inputs['Vector'])
            mat.node_tree.links.new(t_alb.outputs['Color'], bsdf.inputs['Base Color'])

        if os.path.exists(rough_path):
            t_rgh = nodes.new(type='ShaderNodeTexImage')
            t_rgh.image = bpy.data.images.load(rough_path)
            t_rgh.image.colorspace_settings.name = 'Non-Color'
            mat.node_tree.links.new(tex_coord.outputs['UV'], t_rgh.inputs['Vector'])
            mat.node_tree.links.new(t_rgh.outputs['Color'], bsdf.inputs['Roughness'])

        if os.path.exists(norm_path):
            t_nrm = nodes.new(type='ShaderNodeTexImage')
            t_nrm.image = bpy.data.images.load(norm_path)
            t_nrm.image.colorspace_settings.name = 'Non-Color'
            n_node = nodes.new(type='ShaderNodeNormalMap')
            n_node.inputs['Strength'].default_value = 0.85
            mat.node_tree.links.new(tex_coord.outputs['UV'], t_nrm.inputs['Vector'])
            mat.node_tree.links.new(t_nrm.outputs['Color'], n_node.inputs['Color'])
            mat.node_tree.links.new(n_node.outputs['Normal'], bsdf.inputs['Normal'])

    mat.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def create_materials():
    """Genera la suite completa de materiales PBR fotorrealistas de época 2009."""
    mats = {}
    mats["stucco_blanco"] = make_pbr("M_Stucco_Blanco", (0.86, 0.86, 0.85), roughness=0.88, tex_prefix="hotel_tecate_stucco", use_tex_albedo=False)
    mats["stucco_blanco_puro"] = make_pbr("M_Stucco_Blanco_Puro", (0.94, 0.94, 0.93), roughness=0.85)
    mats["zocalo_basal"] = make_pbr("M_Zocalo_Basal_Enterrado", (0.12, 0.13, 0.14), roughness=0.95)
    mats["concreto_piso"] = make_pbr("M_Concreto_Piso_Callejon", (0.70, 0.69, 0.67), roughness=0.85)
    mats["azotea_asfalto"] = make_pbr("M_Azotea_Asfalto", (0.18, 0.18, 0.20), roughness=0.92)

    # Inmueble 1: El Baratero & PRI
    mats["baratero_fascia_purpura"] = make_pbr("M_Baratero_Fascia_Purpura", (0.42, 0.08, 0.35), roughness=0.40)
    mats["baratero_txt_blanco"] = make_pbr("M_Baratero_Txt_Blanco", (0.98, 0.98, 0.98), roughness=0.20)
    mats["baratero_txt_rosa"] = make_pbr("M_Baratero_Txt_Rosa", (0.88, 0.20, 0.65), roughness=0.30)
    mats["aluminio_azul_baratero"] = make_pbr("M_Aluminio_Azul_Baratero", (0.06, 0.24, 0.48), roughness=0.35, metallic=0.75)
    mats["pri_verde_institucional"] = make_pbr("M_PRI_Verde_Institucional", (0.08, 0.52, 0.20), roughness=0.60)
    mats["pri_rojo_logo"] = make_pbr("M_PRI_Rojo_Logo", (0.85, 0.08, 0.08), roughness=0.40)
    mats["persianas_blancas"] = make_pbr("M_Persianas_Blancas", (0.90, 0.90, 0.88), roughness=0.60)
    mats["bodega_verde_cardenas"] = make_pbr("M_Bodega_Verde_Cardenas", (0.28, 0.46, 0.34), roughness=0.88)
    mats["pilastras_magenta"] = make_pbr("M_Pilastras_Magenta", (0.58, 0.12, 0.32), roughness=0.75)
    mats["puerta_chapa_roja"] = make_pbr("M_Puerta_Chapa_Roja", (0.68, 0.18, 0.12), roughness=0.65, metallic=0.4)

    # Inmueble 2: Restaurant D'Arce
    mats["darce_stucco_terracota"] = make_pbr("M_Darce_Stucco_Terracota", (0.75, 0.42, 0.28), roughness=0.85, tex_prefix="hotel_tecate_stucco", use_tex_albedo=False)
    mats["teja_colonial"] = make_pbr("M_Teja_Colonial_3D", (0.56, 0.22, 0.14), roughness=0.80, tex_prefix="kiosko_teja")
    mats["madera_vigas_oscuras"] = make_pbr("M_Madera_Vigas_Oscuras", (0.22, 0.14, 0.09), roughness=0.70)
    mats["darce_tablero_azul"] = make_pbr("M_Darce_Tablero_Azul", (0.06, 0.14, 0.32), roughness=0.35)
    mats["darce_txt_blanco"] = make_pbr("M_Darce_Txt_Blanco", (0.95, 0.95, 0.95), roughness=0.20)
    mats["aluminio_oscuro"] = make_pbr("M_Aluminio_Oscuro_Canceleria", (0.06, 0.06, 0.06), roughness=0.30, metallic=0.85)

    # Inmuebles 3 y 4: Local Blanco y Dulcería La Fuente
    mats["fuente_azul_molduras"] = make_pbr("M_Fuente_Azul_Molduras", (0.08, 0.32, 0.68), roughness=0.50)
    mats["fuente_txt_rojo"] = make_pbr("M_Fuente_Txt_Rojo", (0.86, 0.10, 0.12), roughness=0.30)
    mats["cortina_verde"] = make_pbr("M_Cortina_Verde_Local", (0.12, 0.48, 0.24), roughness=0.80)

    # Inmueble 5: Bar Rodeo / Celosías
    mats["rodeo_verde_menta"] = make_pbr("M_Rodeo_Verde_Menta", (0.42, 0.72, 0.58), roughness=0.75)
    mats["herreria_negra_celosia"] = make_pbr("M_Herreria_Negra_Celosia", (0.04, 0.04, 0.04), roughness=0.40, metallic=0.85)
    mats["rodeo_rotulo_mural"] = make_pbr("M_Rodeo_Rotulo_Mural", (0.15, 0.15, 0.15), roughness=0.90)

    # Inmueble 6: Restaurante Comida China Hing Kang
    mats["hingkang_rojo_bermellon"] = make_pbr("M_HingKang_Rojo_Bermellon", (0.82, 0.08, 0.08), roughness=0.45)
    mats["lona_roja_canopy"] = make_pbr("M_Lona_Roja_Canopy", (0.85, 0.06, 0.06), roughness=0.50)
    mats["hingkang_tablero_negro"] = make_pbr("M_HingKang_Tablero_Negro", (0.05, 0.05, 0.05), roughness=0.30)
    mats["hingkang_txt_blanco"] = make_pbr("M_HingKang_Txt_Blanco", (0.98, 0.98, 0.98), roughness=0.15)
    mats["totem_acero"] = make_pbr("M_Totem_Acero_Azotea", (0.35, 0.37, 0.40), roughness=0.40, metallic=0.80)

    # Inmuebles 7, 8 y 9: SKY, Arco Tradicional y Joyería
    mats["sky_marquesina_azul"] = make_pbr("M_SKY_Marquesina_Azul", (0.05, 0.35, 0.75), roughness=0.35)
    mats["ladrillo_arco"] = make_pbr("M_Ladrillo_Arco_Tradicional", (0.62, 0.28, 0.18), roughness=0.85, tex_prefix="kiosko_ladrillo")
    mats["toldo_anillos_rayas"] = make_pbr("M_Toldo_Anillos_Rayas", (0.88, 0.88, 0.85), roughness=0.60)

    # Inmueble 10: La Michoacana & Locales Ortiz Rubio
    mats["michoacana_amarillo"] = make_pbr("M_Michoacana_Amarillo_Cromo", (0.96, 0.78, 0.08), roughness=0.35)
    mats["michoacana_verde_base"] = make_pbr("M_Michoacana_Verde_Base", (0.10, 0.65, 0.22), roughness=0.50)
    mats["michoacana_txt_rojo"] = make_pbr("M_Michoacana_Txt_Rojo", (0.90, 0.05, 0.05), roughness=0.20)
    mats["michoacana_txt_azul"] = make_pbr("M_Michoacana_Txt_Azul", (0.05, 0.35, 0.85), roughness=0.20)
    mats["espectacular_lienzo"] = make_pbr("M_Espectacular_Lienzo_Blanco", (0.92, 0.92, 0.90), roughness=0.50)
    mats["espectacular_celosia"] = make_pbr("M_Espectacular_Celosia_Acero", (0.25, 0.25, 0.28), roughness=0.60, metallic=0.75)
    mats["beauty_salon_salmon"] = make_pbr("M_Beauty_Salon_Salmon", (0.84, 0.52, 0.38), roughness=0.80)
    mats["cerrajeria_azul"] = make_pbr("M_Cerrajeria_Azul", (0.08, 0.40, 0.70), roughness=0.60)

    # Vidrio comercial universal
    mats["vidrio_comercial"] = make_pbr("M_Vidrio_Comercial", (0.85, 0.90, 0.95), roughness=0.08, alpha=0.35)

    return mats

# ---------------------------------------------------------------------------
# 3. Modelado Procedural por Inmueble
# ---------------------------------------------------------------------------

def build_el_baratero(mats, col):
    """Inmueble 1: El Baratero & Sede PRI (X: 0.00 a 26.50 m, Y: 0.00 a 36.00 m)."""
    objects = []
    Z_BASE = -1.30

    bm_muro = bmesh.new()
    bm_fascia = bmesh.new()
    bm_vidrio = bmesh.new()
    bm_alum = bmesh.new()
    bm_pri = bmesh.new()
    bm_persiana = bmesh.new()
    bm_bodega = bmesh.new()
    bm_magenta = bmesh.new()
    bm_puertas = bmesh.new()

    # Zócalo basal enterrado en todo el perímetro
    add_box(bm_muro, 0.00, 26.50, -0.05, 16.00, Z_BASE, 0.00)
    add_box(bm_bodega, 0.00, 26.50, 16.00, 36.00, Z_BASE, 0.00)

    # 1. PLANTA BAJA: EL BARATERO (Z: 0.00 a 3.30 m)
    add_box(bm_muro, 0.00, 0.40, 0.00, 16.00, 0.00, 3.30)
    add_box(bm_muro, 26.10, 26.50, 0.00, 16.00, 0.00, 3.30)
    add_box(bm_muro, 0.00, 26.50, 15.60, 16.00, 0.00, 3.30)

    # Fachada Frontal (Y = 0.00 m) - Cancelería azul y escaparates
    add_box(bm_alum, 0.00, 26.50, -0.10, 0.00, 0.00, 0.35)
    add_box(bm_alum, 0.00, 26.50, -0.10, 0.00, 2.95, 3.30)
    add_box(bm_vidrio, 0.40, 26.10, -0.05, -0.01, 0.35, 2.95)

    # 7 Montantes verticales de aluminio azul
    for i in range(8):
        xm = 0.40 + i * (25.70 / 7.0)
        add_box(bm_alum, xm - 0.08, xm + 0.08, -0.12, 0.02, 0.35, 2.95)

    # Fascia volada púrpura de El Baratero (Z: 3.10 a 3.75 m)
    add_box(bm_fascia, -0.20, 26.70, -0.35, 0.05, 3.10, 3.75)

    # 2. PLANTA ALTA: SEDE PRI (Z: 3.75 a 6.70 m)
    add_box(bm_muro, 0.00, 0.40, 0.00, 16.00, 3.75, 6.70)
    add_box(bm_muro, 26.10, 26.50, 0.00, 16.00, 3.75, 6.70)
    add_box(bm_muro, 0.00, 26.50, 15.60, 16.00, 3.75, 6.70)

    # Ventanería corrida institucional (Z: 4.15 a 6.10 m)
    add_box(bm_muro, 0.00, 26.50, -0.08, 0.00, 3.75, 4.15)
    add_box(bm_vidrio, 0.40, 26.10, -0.04, 0.00, 4.15, 6.10)
    add_box(bm_persiana, 0.40, 26.10, 0.02, 0.08, 4.15, 6.10)
    for i in range(12):
        xv = 0.40 + i * (25.70 / 11.0)
        add_box(bm_alum, xv - 0.04, xv + 0.04, -0.06, 0.02, 4.15, 6.10)

    # Fascia superior verde institucional PRI (Z: 6.10 a 6.70 m)
    add_box(bm_pri, -0.15, 26.65, -0.20, 0.05, 6.10, 6.70)

    # 3. NIVEL 3: ATTIQUE CIEGO / ESTRUCTURA DE CARTELERA (Z: 6.70 a 11.50 m)
    add_box(bm_muro, 0.00, 26.50, -0.10, 0.40, 6.70, 10.80)
    v_gable = [
        bm_muro.verts.new((0.00, -0.10, 10.80)), bm_muro.verts.new((26.50, -0.10, 10.80)),
        bm_muro.verts.new((13.25, -0.10, 11.50)),
        bm_muro.verts.new((0.00, 0.40, 10.80)), bm_muro.verts.new((26.50, 0.40, 10.80)),
        bm_muro.verts.new((13.25, 0.40, 11.50))
    ]
    bm_muro.faces.new((v_gable[0], v_gable[1], v_gable[2]))
    bm_muro.faces.new((v_gable[4], v_gable[3], v_gable[5]))
    bm_muro.faces.new((v_gable[0], v_gable[3], v_gable[5], v_gable[2]))
    bm_muro.faces.new((v_gable[2], v_gable[5], v_gable[4], v_gable[1]))

    add_box(bm_muro, 0.00, 0.40, 0.40, 16.00, 6.70, 10.50)
    add_box(bm_muro, 26.10, 26.50, 0.40, 16.00, 6.70, 10.50)
    add_box(bm_muro, 0.00, 26.50, 0.00, 16.00, 6.60, 6.75) # Losa azotea

    # 4. CUERPO TRASERO: NAVE PONIENTE SOBRE CÁRDENAS (Y: 16.00 a 36.00 m, Z: 0.00 a 9.20 m)
    add_box(bm_bodega, 0.00, 26.50, 16.00, 36.00, 0.00, 9.20)
    add_box(bm_muro, 0.00, 26.50, 16.00, 36.00, 9.15, 9.35) # Azotea hermética

    # Muro Poniente (X = 0.00 m): 6 Pilastras magenta y vigas
    for ip in range(6):
        yp = 16.00 + ip * 4.00
        add_box(bm_magenta, -0.22, 0.02, yp - 0.25, yp + 0.25, 0.00, 9.20)
    add_box(bm_magenta, -0.15, 0.02, 16.00, 36.00, 3.30, 3.65)
    add_box(bm_magenta, -0.15, 0.02, 16.00, 36.00, 6.50, 6.85)

    # Dos portones dobles de chapa roja sobre Cárdenas
    add_box(bm_puertas, -0.05, 0.05, 18.50, 21.50, 0.00, 3.10)
    add_box(bm_puertas, -0.05, 0.05, 23.50, 26.50, 0.00, 3.10)

    # Puerta peatonal acceso oficinas PRI en Cárdenas
    add_box(bm_puertas, -0.06, 0.04, 2.80, 4.20, 0.00, 2.40)

    # Anuncio espectacular de banqueta de El Baratero en la esquina
    add_box(bm_alum, 1.40, 1.60, -1.80, -1.60, 0.00, 4.50) # Poste metálico
    add_box(bm_fascia, 0.20, 2.80, -1.85, -1.55, 3.20, 4.40) # Tablero rosa

    objects.append(create_mesh_object("Baratero_Muros", bm_muro, mats["stucco_blanco"], col))
    objects.append(create_mesh_object("Baratero_Fascia_Purpura", bm_fascia, mats["baratero_fascia_purpura"], col))
    objects.append(create_mesh_object("Baratero_Vidrios", bm_vidrio, mats["vidrio_comercial"], col))
    objects.append(create_mesh_object("Baratero_Aluminio_Azul", bm_alum, mats["aluminio_azul_baratero"], col))
    objects.append(create_mesh_object("Baratero_PRI_Verde", bm_pri, mats["pri_verde_institucional"], col))
    objects.append(create_mesh_object("Baratero_Persianas", bm_persiana, mats["persianas_blancas"], col))
    objects.append(create_mesh_object("Baratero_Bodega_Verde", bm_bodega, mats["bodega_verde_cardenas"], col))
    objects.append(create_mesh_object("Baratero_Pilastras_Magenta", bm_magenta, mats["pilastras_magenta"], col))
    objects.append(create_mesh_object("Baratero_Puertas_Chapa", bm_puertas, mats["puerta_chapa_roja"], col))

    rot_south = (math.radians(90.0), 0.0, 0.0)
    t1 = add_3d_text("Baratero_Txt_Main", "EL BARATERO", 0.60, 0.04, (13.25, -0.38, 3.52), rot_south, mats["baratero_txt_blanco"], col)
    t2 = add_3d_text("Baratero_Txt_Sub", "ROPA • CALZADO • ACCESORIOS", 0.20, 0.02, (13.25, -0.38, 3.24), rot_south, mats["baratero_txt_rosa"], col)
    t3 = add_3d_text("PRI_Txt_Main", "Partido Revolucionario Institucional", 0.35, 0.03, (13.25, -0.22, 6.40), rot_south, mats["baratero_txt_blanco"], col)

    # Rótulo de banqueta El Baratero
    t_totem_b = add_3d_text("Baratero_Totem_Txt", "EL BARATERO", 0.28, 0.03, (1.50, -1.86, 3.80), rot_south, mats["baratero_txt_blanco"], col)

    # Rótulo de azotea 1, 2, 3, 4
    for il in range(4):
        t_num = add_3d_text(f"Baratero_Num_{il+1}", str(il+1), 0.40, 0.02, (13.25, -0.12, 10.20 - il * 0.95), rot_south, mats["aluminio_oscuro"], col)
        objects.append(t_num)

    # Rótulo PRI en fachada poniente (Cárdenas)
    rot_west = (math.radians(90.0), 0.0, math.radians(-90.0))
    t_pri_w = add_3d_text("PRI_Txt_West", "P R I", 0.65, 0.03, (-0.12, 3.50, 5.80), rot_west, mats["pri_rojo_logo"], col)
    objects.extend([t1, t2, t3, t_totem_b, t_pri_w])

    return objects

def build_darce_restaurant(mats, col):
    """Inmueble 2: Restaurant D'Arce (X: 26.50 a 37.00 m, Y: 0.00 a 14.50 m)."""
    objects = []
    Z_BASE = -1.30

    bm_muro = bmesh.new()
    bm_teja = bmesh.new()
    bm_madera = bmesh.new()
    bm_vidrio = bmesh.new()
    bm_alum = bmesh.new()
    bm_rotulo = bmesh.new()

    # Zócalo y muros principales
    add_box(bm_muro, 26.50, 37.00, 0.00, 14.50, Z_BASE, 3.80)
    add_box(bm_muro, 26.50, 37.00, 0.00, 14.50, 3.80, 4.10) # Pretil azotea
    add_box(bm_muro, 26.50, 37.00, 0.00, 14.50, 3.75, 3.85) # Losa azotea

    # Puerta central (X: 30.50 a 33.00 m, Z: 0.00 a 2.40 m)
    add_box(bm_vidrio, 30.60, 32.90, -0.05, 0.00, 0.00, 2.40)
    add_box(bm_alum, 30.50, 33.00, -0.08, 0.02, 2.35, 2.45)
    add_box(bm_alum, 31.70, 31.80, -0.08, 0.02, 0.00, 2.40)

    # Ventanales laterales (X: 27.20 a 29.80 m y X: 33.70 a 36.30 m)
    for xw1, xw2 in [(27.20, 29.80), (33.70, 36.30)]:
        add_box(bm_vidrio, xw1, xw2, -0.04, 0.00, 0.70, 2.40)
        add_box(bm_alum, xw1 - 0.05, xw2 + 0.05, -0.06, 0.02, 0.65, 0.72)
        add_box(bm_alum, xw1 - 0.05, xw2 + 0.05, -0.06, 0.02, 2.38, 2.45)

    # Marquesina volada con canes de madera oscura y tejas coloniales
    for i in range(14):
        xv = 26.70 + i * 0.78
        add_box(bm_madera, xv - 0.06, xv + 0.06, -0.90, 0.10, 2.70, 2.85)

    # Plano base de tejadillo inclinado
    add_box(bm_teja, 26.40, 37.10, -0.95, 0.05, 2.85, 3.45)
    # Hiladas de tejas curvas en relieve
    add_teja_ribs_x(bm_teja, 26.40, 37.10, -0.95, 0.05, 2.85, 3.45, spacing=0.45)

    # Tablero de rótulo D'Arce
    add_box(bm_rotulo, 29.20, 34.30, -0.98, -0.90, 3.65, 4.45)

    objects.append(create_mesh_object("Darce_Muros", bm_muro, mats["darce_stucco_terracota"], col))
    objects.append(create_mesh_object("Darce_Tejas", bm_teja, mats["teja_colonial"], col, uv_scale=1.5))
    objects.append(create_mesh_object("Darce_Madera", bm_madera, mats["madera_vigas_oscuras"], col))
    objects.append(create_mesh_object("Darce_Vidrios", bm_vidrio, mats["vidrio_comercial"], col))
    objects.append(create_mesh_object("Darce_Aluminio", bm_alum, mats["aluminio_oscuro"], col))
    objects.append(create_mesh_object("Darce_Tablero", bm_rotulo, mats["darce_tablero_azul"], col))

    rot_south = (math.radians(90.0), 0.0, 0.0)
    t_darce = add_3d_text("Darce_Txt_Main", "D'ARCE", 0.48, 0.04, (31.75, -1.00, 4.12), rot_south, mats["darce_txt_blanco"], col)
    t_darce_sub = add_3d_text("Darce_Txt_Sub", "RESTAURANT", 0.18, 0.02, (31.75, -1.00, 3.80), rot_south, mats["darce_txt_blanco"], col)
    objects.extend([t_darce, t_darce_sub])

    return objects

def build_dulceria_la_fuente(mats, col):
    """Inmuebles 3 y 4: Local Blanco y Dulcería La Fuente (X: 37.00 a 49.50 m, Y: 0.00 a 14.00 m)."""
    objects = []
    Z_BASE = -1.30

    bm_muro = bmesh.new()
    bm_azul = bmesh.new()
    bm_teja = bmesh.new()
    bm_vidrio = bmesh.new()
    bm_alum = bmesh.new()

    # Inmueble 3: Local Blanco (X: 37.00 a 41.50 m, Z: 0.00 a 3.50 m)
    add_box(bm_muro, 37.00, 41.50, 0.00, 12.00, Z_BASE, 3.50)
    add_box(bm_vidrio, 38.00, 40.50, -0.04, 0.00, 0.00, 2.40)
    add_box(bm_alum, 37.90, 40.60, -0.06, 0.02, 2.38, 2.45)

    # Inmueble 4: Dulcería La Fuente (X: 41.50 a 49.50 m, Z: 0.00 a 4.20 m)
    add_box(bm_muro, 41.50, 49.50, 0.00, 14.00, Z_BASE, 3.60)
    add_box(bm_azul, 41.45, 49.55, -0.05, 0.05, 0.00, 0.50)
    add_box(bm_azul, 41.45, 49.55, -0.05, 0.05, 3.45, 3.65)

    # Frontón triangular del porche
    v_fronton = [
        bm_muro.verts.new((43.50, -0.30, 3.60)), bm_muro.verts.new((47.50, -0.30, 3.60)),
        bm_muro.verts.new((45.50, -0.30, 4.30)),
        bm_muro.verts.new((43.50, 0.10, 3.60)), bm_muro.verts.new((47.50, 0.10, 3.60)),
        bm_muro.verts.new((45.50, 0.10, 4.30))
    ]
    bm_muro.faces.new((v_fronton[0], v_fronton[1], v_fronton[2]))
    bm_muro.faces.new((v_fronton[4], v_fronton[3], v_fronton[5]))
    bm_muro.faces.new((v_fronton[0], v_fronton[3], v_fronton[5], v_fronton[2]))
    bm_muro.faces.new((v_fronton[2], v_fronton[5], v_fronton[4], v_fronton[1]))

    add_box(bm_teja, 43.30, 47.70, -0.40, 0.15, 4.15, 4.40)

    # Puerta y ventana colonial con cuarterones
    add_box(bm_vidrio, 44.20, 45.40, -0.05, 0.00, 0.00, 2.40)
    add_box(bm_vidrio, 46.20, 47.80, -0.04, 0.00, 0.90, 2.20)
    add_box(bm_azul, 46.10, 47.90, -0.06, 0.02, 0.85, 0.92)
    add_box(bm_azul, 46.10, 47.90, -0.06, 0.02, 2.18, 2.25)

    objects.append(create_mesh_object("Fuente_Muros", bm_muro, mats["stucco_blanco"], col))
    objects.append(create_mesh_object("Fuente_Azul", bm_azul, mats["fuente_azul_molduras"], col))
    objects.append(create_mesh_object("Fuente_Tejas", bm_teja, mats["teja_colonial"], col, uv_scale=1.5))
    objects.append(create_mesh_object("Fuente_Vidrios", bm_vidrio, mats["vidrio_comercial"], col))
    objects.append(create_mesh_object("Fuente_Aluminio", bm_alum, mats["aluminio_oscuro"], col))

    rot_south = (math.radians(90.0), 0.0, 0.0)
    t_fuente = add_3d_text("Fuente_Txt_Main", "DULCERIA", 0.32, 0.03, (47.00, -0.15, 3.90), rot_south, mats["fuente_azul_molduras"], col)
    t_fuente_sub = add_3d_text("Fuente_Txt_Name", "\"La Fuente\"", 0.40, 0.04, (47.00, -0.15, 3.35), rot_south, mats["fuente_txt_rojo"], col)
    objects.extend([t_fuente, t_fuente_sub])

    return objects

def build_rodeo_karaoke(mats, col):
    """Inmueble 5: Bar Rodeo / Celosías (X: 49.50 a 63.00 m, Y: 0.00 a 16.00 m)."""
    objects = []
    Z_BASE = -1.30

    bm_muro = bmesh.new()
    bm_menta = bmesh.new()
    bm_celosia = bmesh.new()
    bm_vidrio = bmesh.new()

    add_box(bm_muro, 49.50, 63.00, 0.00, 16.00, Z_BASE, 4.40)
    add_box(bm_muro, 49.50, 63.00, 0.00, 16.00, 4.35, 4.65)
    add_box(bm_menta, 49.45, 63.05, -0.05, 16.05, 0.00, 1.15)

    # Dos grandes ventanales con celosías de herrería geométrica en relieve
    for xw1, xw2 in [(50.80, 54.20), (57.50, 61.50)]:
        add_box(bm_vidrio, xw1, xw2, -0.04, 0.00, 1.25, 2.75)
        add_box(bm_celosia, xw1 - 0.06, xw2 + 0.06, -0.10, 0.02, 1.20, 2.80)
        for ib in range(6):
            xb = xw1 + ib * ((xw2 - xw1) / 5.0)
            add_box(bm_celosia, xb - 0.02, xb + 0.02, -0.08, 0.00, 1.25, 2.75)

    # Puerta central
    add_box(bm_vidrio, 54.90, 56.70, -0.06, 0.00, 0.00, 2.60)
    add_box(bm_celosia, 54.80, 56.80, -0.08, 0.02, 2.55, 2.65)

    objects.append(create_mesh_object("Rodeo_Muros", bm_muro, mats["stucco_blanco"], col))
    objects.append(create_mesh_object("Rodeo_Menta", bm_menta, mats["rodeo_verde_menta"], col))
    objects.append(create_mesh_object("Rodeo_Celosias", bm_celosia, mats["herreria_negra_celosia"], col))
    objects.append(create_mesh_object("Rodeo_Vidrios", bm_vidrio, mats["vidrio_comercial"], col))

    rot_east_wall = (math.radians(90.0), 0.0, math.radians(90.0))
    t_rodeo1 = add_3d_text("Rodeo_Txt_Mural1", "KARAOKE  &  DANCE", 0.45, 0.02, (63.05, 8.00, 3.80), rot_east_wall, mats["rodeo_rotulo_mural"], col)
    t_rodeo2 = add_3d_text("Rodeo_Txt_Mural2", "RODEO  BAR", 0.38, 0.02, (63.05, 8.00, 3.20), rot_east_wall, mats["rodeo_rotulo_mural"], col)
    t_rodeo3 = add_3d_text("Rodeo_Txt_Mural3", "ESTACIONAMIENTO", 0.28, 0.02, (63.05, 8.00, 2.60), rot_east_wall, mats["rodeo_rotulo_mural"], col)
    objects.extend([t_rodeo1, t_rodeo2, t_rodeo3])

    return objects

def build_patio_y_callejon(mats, col):
    """Callejón intermedio y patio central de estacionamiento (X: 63.00 a 69.50 m, Y: 0.00 a 36.00 m)."""
    objects = []
    bm_piso = bmesh.new()
    bm_barda = bmesh.new()
    bm_reja = bmesh.new()

    add_box(bm_piso, 63.00, 69.50, 0.00, 36.00, -0.15, 0.02)
    add_box(bm_piso, 26.50, 69.50, 16.00, 36.00, -0.15, 0.02)

    add_box(bm_barda, 26.50, 63.50, 35.80, 36.20, -1.30, 2.40)
    add_box(bm_barda, 69.00, 102.00, 35.80, 36.20, -1.30, 2.40)
    add_box(bm_reja, 63.50, 69.00, 35.95, 36.05, 0.00, 2.20)

    objects.append(create_mesh_object("Callejon_Piso", bm_piso, mats["concreto_piso"], col))
    objects.append(create_mesh_object("Callejon_Bardas", bm_barda, mats["stucco_blanco"], col))
    objects.append(create_mesh_object("Callejon_Rejas", bm_reja, mats["herreria_negra_celosia"], col))

    # Letrero de estacionamiento legible desde el callejón (orientado hacia el Sur)
    rot_south = (math.radians(90.0), 0.0, 0.0)
    t_park = add_3d_text("Parking_Txt_Sign", "PARKING  $15", 0.40, 0.03, (66.25, 35.75, 1.80), rot_south, mats["pri_verde_institucional"], col)
    objects.append(t_park)

    return objects

def build_restaurante_hing_kang(mats, col):
    """Inmueble 6: Restaurante Comida China Hing Kang (X: 69.50 a 82.50 m, Y: 0.00 a 15.00 m)."""
    objects = []
    Z_BASE = -1.30

    bm_muro = bmesh.new()
    bm_rojo = bmesh.new()
    bm_canopy = bmesh.new()
    bm_vidrio = bmesh.new()
    bm_alum = bmesh.new()
    bm_tablero = bmesh.new()
    bm_totem = bmesh.new()

    add_box(bm_muro, 69.50, 82.50, 0.00, 15.00, Z_BASE, 4.40)
    add_box(bm_muro, 69.50, 82.50, 0.00, 15.00, 4.35, 4.65)
    add_box(bm_rojo, 69.45, 82.55, -0.05, 15.05, 0.00, 1.35)

    # Dos grandes ventanales con toldos de lona roja semicirculares reales
    for xw1, xw2 in [(71.00, 75.50), (76.50, 81.00)]:
        add_box(bm_vidrio, xw1, xw2, -0.04, 0.00, 1.40, 2.90)
        add_box(bm_alum, xw1 - 0.06, xw2 + 0.06, -0.08, 0.02, 1.35, 1.42)
        add_box(bm_alum, xw1 - 0.06, xw2 + 0.06, -0.08, 0.02, 2.88, 2.95)

        # Toldo semicircular curvado
        add_canopy_quarter_round(bm_canopy, xw1 - 0.20, xw2 + 0.20, 0.02, -0.90, 2.65, 3.45)

    # Puerta lateral izquierda en arco hacia el callejón
    add_box(bm_vidrio, 69.46, 69.54, 1.50, 3.20, 0.00, 2.40)

    # Tablero de fachada principal Hing Kang
    add_box(bm_tablero, 73.00, 79.50, -0.15, -0.05, 3.65, 4.35)

    # Tótem espectacular en azotea con estructura de perfiles
    add_box(bm_totem, 74.80, 75.10, 0.50, 0.80, 4.40, 7.20)
    add_box(bm_totem, 76.90, 77.20, 0.50, 0.80, 4.40, 7.20)
    add_box(bm_tablero, 73.80, 78.20, 0.45, 0.85, 5.40, 7.00)

    objects.append(create_mesh_object("HingKang_Muros", bm_muro, mats["stucco_blanco"], col))
    objects.append(create_mesh_object("HingKang_Rojo", bm_rojo, mats["hingkang_rojo_bermellon"], col))
    objects.append(create_mesh_object("HingKang_Canopies", bm_canopy, mats["lona_roja_canopy"], col))
    objects.append(create_mesh_object("HingKang_Vidrios", bm_vidrio, mats["vidrio_comercial"], col))
    objects.append(create_mesh_object("HingKang_Aluminio", bm_alum, mats["aluminio_oscuro"], col))
    objects.append(create_mesh_object("HingKang_Tablero", bm_tablero, mats["hingkang_tablero_negro"], col))
    objects.append(create_mesh_object("HingKang_Totem", bm_totem, mats["totem_acero"], col))

    rot_south = (math.radians(90.0), 0.0, 0.0)
    t_hk1 = add_3d_text("HingKang_Txt_Main", "HING KANG", 0.46, 0.04, (76.25, -0.18, 4.08), rot_south, mats["hingkang_txt_blanco"], col)
    t_hk2 = add_3d_text("HingKang_Txt_Sub", "RESTAURANTE COMIDA CHINA", 0.17, 0.02, (76.25, -0.18, 3.78), rot_south, mats["hingkang_rojo_bermellon"], col)

    t_coke1 = add_3d_text("Coke_Txt_Canopy1", "Coca-Cola", 0.18, 0.02, (73.25, -0.92, 2.75), rot_south, mats["hingkang_txt_blanco"], col)
    t_coke2 = add_3d_text("Coke_Txt_Canopy2", "Coca-Cola", 0.18, 0.02, (78.75, -0.92, 2.75), rot_south, mats["hingkang_txt_blanco"], col)

    t_roof_hk = add_3d_text("HingKang_Txt_Roof", "RESTAURANTE COMIDA CHINA PARKING", 0.24, 0.03, (76.00, 0.40, 6.20), rot_south, mats["hingkang_rojo_bermellon"], col)
    objects.extend([t_hk1, t_hk2, t_coke1, t_coke2, t_roof_hk])

    return objects

def build_locales_intermedios(mats, col):
    """Inmuebles 7, 8 y 9: SKY, Arco Tradicional y Joyería (X: 82.50 a 102.00 m, Y: 0.00 a 12.00 m)."""
    objects = []
    Z_BASE = -1.30

    bm_muro = bmesh.new()
    bm_sky = bmesh.new()
    bm_arco = bmesh.new()
    bm_vigas = bmesh.new()
    bm_toldo = bmesh.new()
    bm_vidrio = bmesh.new()
    bm_alum = bmesh.new()

    add_box(bm_muro, 82.50, 102.00, 0.00, 12.00, Z_BASE, 3.80)
    add_box(bm_muro, 82.50, 102.00, 0.00, 12.00, 3.80, 4.10)

    # 1. LOCAL SKY (X: 82.50 a 89.00 m)
    add_box(bm_sky, 82.35, 89.15, -0.45, 0.05, 3.10, 3.80)
    add_box(bm_vidrio, 83.50, 88.00, -0.04, 0.00, 0.00, 2.40)
    add_box(bm_alum, 83.40, 88.10, -0.06, 0.02, 2.38, 2.45)

    # 2. LOCAL ARCO TRADICIONAL (X: 89.00 a 97.00 m)
    # Arco de ladrillo real en relieve
    add_arch_spandrel_x(bm_arco, -0.15, 0.05, 90.50, 95.50, 2.20, 2.95, 3.20)
    add_box(bm_vidrio, 91.00, 95.00, -0.04, 0.00, 0.00, 2.20)
    for iv in range(7):
        xv = 89.60 + iv * 1.05
        add_box(bm_vigas, xv - 0.08, xv + 0.08, -0.45, 0.08, 3.40, 3.55)

    # 3. LOCAL JOYERÍA ANILLOS (X: 97.00 a 102.00 m)
    add_box(bm_toldo, 97.20, 101.80, -0.65, 0.05, 2.50, 3.10)
    add_box(bm_vidrio, 97.50, 101.50, -0.04, 0.00, 0.00, 2.40)

    objects.append(create_mesh_object("Locales_Muros", bm_muro, mats["stucco_blanco"], col))
    objects.append(create_mesh_object("Locales_SKY", bm_sky, mats["sky_marquesina_azul"], col))
    objects.append(create_mesh_object("Locales_Arco", bm_arco, mats["ladrillo_arco"], col))
    objects.append(create_mesh_object("Locales_Vigas", bm_vigas, mats["madera_vigas_oscuras"], col))
    objects.append(create_mesh_object("Locales_Toldo", bm_toldo, mats["toldo_anillos_rayas"], col))
    objects.append(create_mesh_object("Locales_Vidrios", bm_vidrio, mats["vidrio_comercial"], col))
    objects.append(create_mesh_object("Locales_Aluminio", bm_alum, mats["aluminio_oscuro"], col))

    rot_south = (math.radians(90.0), 0.0, 0.0)
    t_sky1 = add_3d_text("SKY_Txt_Main", "SKY", 0.55, 0.04, (85.75, -0.48, 3.52), rot_south, mats["baratero_txt_blanco"], col)
    t_sky2 = add_3d_text("SKY_Txt_Sub", "DISTRIBUIDOR AUTORIZADO", 0.16, 0.02, (85.75, -0.48, 3.25), rot_south, mats["baratero_txt_blanco"], col)
    t_joya = add_3d_text("Joya_Txt_Toldo", "ANILLOS DE GRADUACION", 0.18, 0.02, (99.50, -0.66, 2.70), rot_south, mats["pri_rojo_logo"], col)
    objects.extend([t_sky1, t_sky2, t_joya])

    return objects

def build_la_michoacana(mats, col):
    """Inmueble 10: La Michoacana y locales sobre Ortiz Rubio (X: 102.00 a 112.50 m, Y: 0.00 a 22.00 m)."""
    objects = []
    Z_BASE = -1.30

    bm_amarillo = bmesh.new()
    bm_verde = bmesh.new()
    bm_muro = bmesh.new()
    bm_vidrio = bmesh.new()
    bm_mostrador = bmesh.new()
    bm_espectacular = bmesh.new()
    bm_celosia = bmesh.new()
    bm_beauty = bmesh.new()
    bm_cerrajeria = bmesh.new()

    # Muros base de La Michoacana
    add_box(bm_muro, 102.00, 112.50, 0.00, 22.00, Z_BASE, 4.10)
    add_box(bm_amarillo, 101.90, 112.60, -0.15, 22.10, 0.00, 4.10)
    add_box(bm_verde, 101.85, 112.65, -0.20, 22.15, 0.00, 0.90)

    # Galería abierta en esquina
    add_box(bm_amarillo, 111.90, 112.45, -0.15, 0.40, 0.00, 3.30)
    add_box(bm_amarillo, 111.90, 112.45, 5.50, 6.05, 0.00, 3.30)

    # Mostradores de helados y vitrinas curvas
    add_box(bm_mostrador, 104.50, 110.50, 0.80, 1.60, 0.00, 1.10)
    add_box(bm_vidrio, 104.50, 110.50, 0.80, 1.60, 1.10, 1.55)

    # Gran fascia corrida ondulada amarilla
    add_box(bm_amarillo, 101.80, 112.70, -0.30, 7.50, 3.10, 4.10)

    # Locales sobre Pdte. Pascual Ortiz Rubio
    add_box(bm_beauty, 112.45, 112.85, 7.50, 13.50, 0.00, 3.80)
    add_box(bm_vidrio, 112.80, 112.86, 9.00, 12.50, 0.80, 2.40)
    add_box(bm_cerrajeria, 112.45, 112.85, 13.50, 22.00, 0.00, 3.50)

    # Gran cartelera espectacular en azotea sobre celosía metálica
    for i in range(5):
        xs = 103.50 + i * 2.00
        add_box(bm_celosia, xs - 0.08, xs + 0.08, 1.50, 1.66, 4.10, 10.50)
        add_box(bm_celosia, xs - 0.08, xs + 0.08, 4.00, 4.16, 4.10, 10.50)
    add_box(bm_celosia, 103.40, 111.60, 1.50, 1.65, 5.50, 5.65)
    add_box(bm_celosia, 103.40, 111.60, 1.50, 1.65, 8.20, 8.35)
    add_box(bm_celosia, 103.40, 111.60, 4.00, 4.15, 5.50, 5.65)

    add_box(bm_espectacular, 102.80, 112.20, 1.35, 1.50, 5.50, 10.40)

    objects.append(create_mesh_object("Michoacana_Amarillo", bm_amarillo, mats["michoacana_amarillo"], col))
    objects.append(create_mesh_object("Michoacana_Verde", bm_verde, mats["michoacana_verde_base"], col))
    objects.append(create_mesh_object("Michoacana_Muros", bm_muro, mats["stucco_blanco"], col))
    objects.append(create_mesh_object("Michoacana_Mostradores", bm_mostrador, mats["aluminio_azul_baratero"], col))
    objects.append(create_mesh_object("Michoacana_Vidrios", bm_vidrio, mats["vidrio_comercial"], col))
    objects.append(create_mesh_object("Michoacana_Espectacular", bm_espectacular, mats["espectacular_lienzo"], col))
    objects.append(create_mesh_object("Michoacana_Celosia", bm_celosia, mats["espectacular_celosia"], col))
    objects.append(create_mesh_object("Michoacana_Beauty", bm_beauty, mats["beauty_salon_salmon"], col))
    objects.append(create_mesh_object("Michoacana_Cerrajeria", bm_cerrajeria, mats["cerrajeria_azul"], col))

    rot_south = (math.radians(90.0), 0.0, 0.0)
    t_mich1 = add_3d_text("Mich_Txt_Main", "LA MICHOACANA", 0.52, 0.04, (107.25, -0.32, 3.75), rot_south, mats["michoacana_txt_rojo"], col)
    t_mich2 = add_3d_text("Mich_Txt_Sub", "PALETERIA  Y  NEVERIA", 0.22, 0.02, (107.25, -0.32, 3.28), rot_south, mats["michoacana_txt_azul"], col)

    rot_east = (math.radians(90.0), 0.0, math.radians(90.0))
    t_mich_east = add_3d_text("Mich_Txt_East", "LA MICHOACANA", 0.42, 0.03, (112.75, 4.00, 3.75), rot_east, mats["michoacana_txt_rojo"], col)
    t_beauty = add_3d_text("Beauty_Txt_Sign", "San Diego Beauty Salon", 0.28, 0.02, (112.90, 10.50, 3.40), rot_east, mats["baratero_txt_blanco"], col)
    t_cerraj = add_3d_text("Cerraj_Txt_Sign", "MURILLO'S CERRAJERIA", 0.26, 0.02, (112.90, 16.50, 3.10), rot_east, mats["baratero_txt_blanco"], col)

    t_espect = add_3d_text("Espect_Txt_Ad", "CAEM  •  GRUPO SIESA", 0.58, 0.03, (107.50, 1.30, 8.00), rot_south, mats["baratero_txt_rosa"], col)
    objects.extend([t_mich1, t_mich2, t_mich_east, t_beauty, t_cerraj, t_espect])

    return objects

# ---------------------------------------------------------------------------
# 4. Configuración de Cámaras y Renderizado Cycles Headless
# ---------------------------------------------------------------------------

def setup_cameras_and_render(col):
    """Configura la batería perimetral diurna de 8 cámaras técnicas con sol y domo de cielo suave."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    if hasattr(scene.cycles, 'device'):
        scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.image_settings.file_format = 'PNG'

    # 1. Configurar Domo de Cielo Suave (World Background) para erradicar sombras negras puras
    world = scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        scene.world = world
    world.use_nodes = True
    w_nodes = world.node_tree.nodes
    w_nodes.clear()
    node_w_out = w_nodes.new(type='ShaderNodeOutputWorld')
    node_w_bg = w_nodes.new(type='ShaderNodeBackground')
    node_w_bg.inputs['Color'].default_value = (0.76, 0.85, 0.98, 1.0) # Azul diurno suave
    node_w_bg.inputs['Strength'].default_value = 1.35
    world.node_tree.links.new(node_w_bg.outputs['Background'], node_w_out.inputs['Surface'])

    # 2. Luz de sol diurno cálido
    sun_data = bpy.data.lights.new(name="Sun_Diurno", type='SUN')
    sun_data.energy = 4.0
    sun_data.color = (1.0, 0.98, 0.92)
    sun_obj = bpy.data.objects.new("Sun_Diurno", sun_data)
    sun_obj.location = (50.0, -40.0, 60.0)
    sun_obj.rotation_euler = (math.radians(45.0), math.radians(15.0), math.radians(-30.0))
    col.objects.link(sun_obj)

    # 3. Batería perimetral completa de 8 cámaras calibradas
    cam_configs = [
        ("Cam_01_Frontal_Baratero_45", ( -10.0, -22.0, 5.5 ), ( 13.0, 4.0, 4.0 ), 35),
        ("Cam_02_Frontal_Centro_Oeste", ( 38.0, -22.0, 4.5 ), ( 38.0, 4.0, 3.2 ), 32),
        ("Cam_03_Callejon_Estacionamiento", ( 66.25, -16.0, 3.2 ), ( 66.25, 20.0, 2.5 ), 45),
        ("Cam_04_Frontal_Centro_Este", ( 84.0, -20.0, 4.5 ), ( 84.0, 4.0, 3.2 ), 35),
        ("Cam_05_Frontal_Michoacana_45", ( 120.0, -18.0, 5.5 ), ( 107.0, 6.0, 4.0 ), 35),
        ("Cam_06_Lateral_Cardenas_Oeste", ( -20.0, 20.0, 5.5 ), ( 0.0, 20.0, 4.0 ), 32),
        ("Cam_07_Lateral_OrtizRubio_Este", ( 126.0, 12.0, 5.0 ), ( 112.5, 12.0, 3.5 ), 35),
        ("Cam_08_Cenital_Azoteas_Z60", ( 56.0, 16.0, 65.0 ), ( 56.0, 16.0, 0.0 ), 28),
    ]

    cams = {}
    for cam_name, pos, tgt, lens in cam_configs:
        c_data = bpy.data.cameras.new(cam_name)
        c_data.lens = lens
        c_data.clip_end = 500.0
        c_obj = bpy.data.objects.new(cam_name, c_data)
        col.objects.link(c_obj)
        c_obj.location = Vector(pos)
        direction = Vector(tgt) - Vector(pos)
        c_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        cams[cam_name] = c_obj

    return cams

def execute_validation_renders(cams):
    """Ejecuta los renders técnicos diurnos y los guarda en docs/images/juarez_235/."""
    os.makedirs(RENDERS_DIR, exist_ok=True)
    scene = bpy.context.scene

    for cam_name, cam_obj in cams.items():
        print(f"Renderizando vista técnica: {cam_name}...")
        scene.camera = cam_obj
        render_path = os.path.join(RENDERS_DIR, f"{cam_name}.png")
        scene.render.filepath = render_path
        bpy.ops.render.render(write_still=True)
        print(f"  Guardado render: {render_path}")

# ---------------------------------------------------------------------------
# 5. Generación Programática de Escena Godot 4 (.tscn)
# ---------------------------------------------------------------------------

def generate_godot_scene(tscn_path, glb_path):
    """Genera la escena Godot 4 con colisiones analíticas descompuestas e inversión Z_godot = -Y_blender."""
    rel_glb_path = "res://assets/buildings/edificio_juarez_235.glb"

    tscn_content = f"""[gd_scene load_steps=15 format=3 uid="uid://edificio_juarez_235_prod"]

[ext_resource type="PackedScene" path="{rel_glb_path}" id="1_mesh"]

# ---------------------------------------------------------------------------
# Definición de Colisionadores Analíticos BoxShape3D
# Sincronización Canónica glTF: X_godot = X_blender, Y_godot = Z_blender, Z_godot = -Y_blender
# ---------------------------------------------------------------------------

# 1. El Baratero & PRI
[sub_resource type="BoxShape3D" id="BoxShape3D_baratero_comercial"]
size = Vector3(26.50, 7.50, 16.00)

[sub_resource type="BoxShape3D" id="BoxShape3D_baratero_nave_cardenas"]
size = Vector3(26.50, 9.40, 20.00)

# 2. Restaurant D'Arce
[sub_resource type="BoxShape3D" id="BoxShape3D_darce"]
size = Vector3(10.50, 4.30, 14.50)

# 3. Local Blanco
[sub_resource type="BoxShape3D" id="BoxShape3D_local_blanco"]
size = Vector3(4.50, 3.80, 12.00)

# 4. Dulcería La Fuente
[sub_resource type="BoxShape3D" id="BoxShape3D_la_fuente"]
size = Vector3(8.00, 4.30, 14.00)

# 5. Bar Rodeo / Celosías
[sub_resource type="BoxShape3D" id="BoxShape3D_rodeo_bar"]
size = Vector3(13.50, 4.65, 16.00)

# [VANO LIBRE X in [63.00, 69.50]: CERO COLISIONADORES - PASO DIÁFANO HACIA ESTACIONAMIENTO]

# 6. Restaurante Hing Kang
[sub_resource type="BoxShape3D" id="BoxShape3D_hing_kang"]
size = Vector3(13.00, 4.65, 15.00)

# 7. SKY Distribuidor
[sub_resource type="BoxShape3D" id="BoxShape3D_sky"]
size = Vector3(6.50, 4.10, 12.00)

# 8. Local Arco Tradicional
[sub_resource type="BoxShape3D" id="BoxShape3D_arco_tradicional"]
size = Vector3(8.00, 4.20, 12.00)

# 9. Joyería Anillos
[sub_resource type="BoxShape3D" id="BoxShape3D_joyeria"]
size = Vector3(5.00, 3.90, 11.00)

# 10. La Michoacana y locales Ortiz Rubio
[sub_resource type="BoxShape3D" id="BoxShape3D_michoacana"]
size = Vector3(10.50, 4.30, 7.50)

[sub_resource type="BoxShape3D" id="BoxShape3D_beauty_salon"]
size = Vector3(8.50, 3.90, 6.00)

[sub_resource type="BoxShape3D" id="BoxShape3D_cerrajeria"]
size = Vector3(8.50, 3.60, 8.50)

# Bardas perimetrales de patio
[sub_resource type="BoxShape3D" id="BoxShape3D_barda_norte_1"]
size = Vector3(37.00, 2.50, 0.40)

[sub_resource type="BoxShape3D" id="BoxShape3D_barda_norte_2"]
size = Vector3(33.00, 2.50, 0.40)

# ---------------------------------------------------------------------------
# Jerarquía del Nodo Raíz StaticBody3D
# ---------------------------------------------------------------------------

[node name="Edificio_Juarez_235" type="StaticBody3D"]

[node name="ModelInstance" parent="." instance=ExtResource("1_mesh")]

# 1. El Baratero
[node name="Col_Baratero_Frontal" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 13.25, 3.75, -8.00)
shape = SubResource("BoxShape3D_baratero_comercial")

[node name="Col_Baratero_Nave" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 13.25, 4.70, -26.00)
shape = SubResource("BoxShape3D_baratero_nave_cardenas")

# 2. Restaurant D'Arce
[node name="Col_Darce" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 31.75, 2.15, -7.25)
shape = SubResource("BoxShape3D_darce")

# 3. Local Blanco
[node name="Col_Local_Blanco" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 39.25, 1.90, -6.00)
shape = SubResource("BoxShape3D_local_blanco")

# 4. Dulcería La Fuente
[node name="Col_La_Fuente" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 45.50, 2.15, -7.00)
shape = SubResource("BoxShape3D_la_fuente")

# 5. Bar Rodeo
[node name="Col_Rodeo_Bar" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 56.25, 2.32, -8.00)
shape = SubResource("BoxShape3D_rodeo_bar")

# [VANO LIBRE X in [63.00, 69.50]: CERO COLISIONADORES FRONTALES - PASO DIÁFANO]

# 6. Restaurante Hing Kang
[node name="Col_Hing_Kang" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 76.00, 2.32, -7.50)
shape = SubResource("BoxShape3D_hing_kang")

# 7. SKY Distribuidor
[node name="Col_SKY" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 85.75, 2.05, -6.00)
shape = SubResource("BoxShape3D_sky")

# 8. Local Arco Tradicional
[node name="Col_Arco_Tradicional" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 93.00, 2.10, -6.00)
shape = SubResource("BoxShape3D_arco_tradicional")

# 9. Joyería Anillos
[node name="Col_Joyeria" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 99.50, 1.95, -5.50)
shape = SubResource("BoxShape3D_joyeria")

# 10. La Michoacana y locales Ortiz Rubio
[node name="Col_Michoacana" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 107.25, 2.15, -3.75)
shape = SubResource("BoxShape3D_michoacana")

[node name="Col_Beauty_Salon" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 108.25, 1.95, -10.50)
shape = SubResource("BoxShape3D_beauty_salon")

[node name="Col_Cerrajeria" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 108.25, 1.80, -17.75)
shape = SubResource("BoxShape3D_cerrajeria")

# Bardas perimetrales norte
[node name="Col_Barda_Norte_1" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 45.00, 1.25, -36.00)
shape = SubResource("BoxShape3D_barda_norte_1")

[node name="Col_Barda_Norte_2" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 85.50, 1.25, -36.00)
shape = SubResource("BoxShape3D_barda_norte_2")
"""

    os.makedirs(os.path.dirname(tscn_path), exist_ok=True)
    with open(tscn_path, "w", encoding="utf-8") as f:
        f.write(tscn_content)
    print(f"Escena Godot .tscn generada con éxito: {tscn_path}")

# ---------------------------------------------------------------------------
# 6. Función Principal de Orquestación
# ---------------------------------------------------------------------------

def main():
    print("=" * 75)
    print("INICIANDO RECONSTRUCCIÓN PROCEDURAL 3D: CONJUNTO AV. BENITO JUÁREZ 235 V2.0")
    print("=" * 75)

    root_col = clean_scene("Juarez_235_Root")
    mats = create_materials()

    print("-> 1. Generando Inmueble 1: El Baratero & PRI (3 Niveles, L=26.50 m, Nave Cárdenas)...")
    objs_baratero = build_el_baratero(mats, root_col)

    print("-> 2. Generando Inmueble 2: Restaurant D'Arce (Tejas Coloniales, Canes, L=10.50 m)...")
    objs_darce = build_darce_restaurant(mats, root_col)

    print("-> 3. Generando Inmuebles 3 y 4: Local Blanco y Dulcería La Fuente (Frontón a dos aguas)...")
    objs_fuente = build_dulceria_la_fuente(mats, root_col)

    print("-> 4. Generando Inmueble 5: Bar Rodeo / Celosías y Rótulo Mural Este...")
    objs_rodeo = build_rodeo_karaoke(mats, root_col)

    print("-> 5. Generando Callejón Central Diáfano, Patio y Bardas de Estacionamiento...")
    objs_patio = build_patio_y_callejon(mats, root_col)

    print("-> 6. Generando Inmueble 6: Restaurante Comida China Hing Kang (Toldos Canopies y Tótem)...")
    objs_hingkang = build_restaurante_hing_kang(mats, root_col)

    print("-> 7. Generando Inmuebles 7, 8 y 9: SKY, Arco Tradicional de Ladrillo y Joyería...")
    objs_locales = build_locales_intermedios(mats, root_col)

    print("-> 8. Generando Inmueble 10: La Michoacana (Ochava en Esquina, Cartelera y Locales Ortiz Rubio)...")
    objs_michoacana = build_la_michoacana(mats, root_col)

    total_objs = len(objs_baratero) + len(objs_darce) + len(objs_fuente) + len(objs_rodeo) + len(objs_patio) + len(objs_hingkang) + len(objs_locales) + len(objs_michoacana)
    print(f"Total de objetos generados: {total_objs}")

    # Guardar archivo maestro Blender (.blend)
    os.makedirs(os.path.dirname(BLEND_OUT), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
    print(f"Archivo maestro guardado: {BLEND_OUT}")

    # Exportar modelo de producción GLB limpio
    os.makedirs(os.path.dirname(GLB_OUT), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=GLB_OUT,
        export_format='GLB',
        use_selection=False,
        export_cameras=False,
        export_lights=False,
        export_apply=True,
    )
    print(f"Modelo glTF de producción exportado: {GLB_OUT}")

    # Generar escena Godot 4 (.tscn) con física analítica transitable
    generate_godot_scene(TSCN_OUT, GLB_OUT)

    # Configurar cámaras y ejecutar renders diurnos de validación
    print("-> Configurando suite de 8 cámaras técnicas y renderizando...")
    cams = setup_cameras_and_render(root_col)
    execute_validation_renders(cams)

    print("=" * 75)
    print("PROCESO PROCEDURAL V2.0 FINALIZADO EXITOSAMENTE")
    print("=" * 75)

if __name__ == "__main__":
    main()
