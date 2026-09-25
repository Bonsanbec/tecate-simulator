"""
=============================================================================
GENERADOR PROCEDURAL 3D: COMPLEJO COMERCIAL PDTE. LÁZARO CÁRDENAS 25
(ÉPOCA: HISTÓRICO 2009 - VERSIÓN DE PRODUCCIÓN FOTORREALISTA V3.0 GROUND-TRUTH)
=============================================================================
Inmueble continuo Neocolonial / Colonial Californiano en Tecate, B.C.:
  - Fachada Este (Cárdenas): 13 arcos frontales continuos y 14 pilastras de laja (Longitud 70.20 m).
  - Galería porticada transitable en Planta Baja (X in [0.00, 2.40 m]).
  - Cancelerías retranqueadas y locales históricos de 2009:
      Santander (1-4), La Michoacana (5-6), Escalera Central Transitable (7),
      Casa Musical Tecate (8), Óptica San Martín (9), Clínicas (10-11),
      Telas y Novedades Vero (12), Regalos Brisa (13).
  - Planta Alta: Balcón volado corrido con barandales de forja negra y continuidad
    diáfana hacia Callejón Libertad (Norte) y retorno a 90° en Av. Hidalgo (Sur).
  - Fachada Norte (Libertad): Cajero Automático Santander (ATM) a detalle completo con
    cancelería oscura, puertas dobles, rótulo vertical tridimensional y puerta de servicio;
    2 arcos ciegos adosados con zócalo de laja; 3 grandes ventanales superiores y rótulo de La Salamandra.
  - Fachada Sur (Hidalgo): 2 grandes ventanales calados en PA con carpintería blanca de 4 paños
    y rótulo 'Seguridad Comercial Tecate'; en PB escaparates acristalados de Regalos Brisa con
    maniquíes en vestidos de gala (bautizo y quinceañera), farol colonial de forja y banco de medidores CFE.
  - Muro posterior de cierre continuo en X = 11.20 m: erradica 100% la visión hueca interior.
  - La Parrilla Restaurant Bar & Grill: Estructura envolvente en 'L'/'U' que ABRAZA el estacionamiento
    por sus costados Este y Sur (frente norte en Libertad, espadaña misional, porche ochavado con
    zaguán diáfano, ala este con ventanas rústicas, y gran cuerpo sur de dos niveles en terracota).
  - Explanada de estacionamiento: Patio interior confinado entre La Parrilla y la barda poniente de La Tradición.
  - Física analítica 1:1 en Godot 4 (.tscn) con cero barreras invisibles ni cajas perpendiculares fantasma.
=============================================================================
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Euler, Matrix

# ---------------------------------------------------------------------------
# 0. Rutas Canónicas
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLEND_OUT = os.path.join(BASE_DIR, "blender_assets", "buildings", "edificio_cardenas_25.blend")
GLB_OUT = os.path.join(BASE_DIR, "godot_project", "assets", "buildings", "edificio_cardenas_25.glb")
TSCN_OUT = os.path.join(BASE_DIR, "godot_project", "assets", "buildings", "edificio_cardenas_25.tscn")
RENDERS_DIR = os.path.join(BASE_DIR, "docs", "images", "cardenas_25")
TEXTURES_DIR = os.path.join(BASE_DIR, "godot_project", "assets", "textures")

# ---------------------------------------------------------------------------
# 1. Utilidades de Geometría Procedural
# ---------------------------------------------------------------------------

def clean_scene():
    """Limpia la escena y crea la colección raíz."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)
    root_col = bpy.data.collections.new("Cardenas_25_Root")
    scene.collection.children.link(root_col)
    return root_col

def add_box(bm, x1, x2, y1, y2, z1, z2):
    """Crea una caja ortogonal limpia de 8 vértices y 6 caras con normales exteriores."""
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
    bm.faces.new((verts[0], verts[4], verts[5], verts[1])) # -Y
    bm.faces.new((verts[1], verts[5], verts[6], verts[2])) # +X
    bm.faces.new((verts[2], verts[6], verts[7], verts[3])) # +Y
    bm.faces.new((verts[3], verts[7], verts[4], verts[0])) # -X
    return verts

def add_arch_spandrel(bm, x_min, x_max, y_start, y_end, z_spring, z_crown, z_top, segments=14):
    """Construye un arco rebajado a lo largo de Y con dovelas y rellena las enjutas superiores hasta z_top."""
    span = y_end - y_start
    y_center = (y_start + y_end) * 0.5
    rise = z_crown - z_spring
    r = (rise**2 + (span * 0.5)**2) / (2.0 * rise)
    center_z = z_crown - r

    arc_pts = []
    for i in range(segments + 1):
        t = i / segments
        y = y_start + t * span
        dy = y - y_center
        dz = math.sqrt(max(0.0, r**2 - dy**2))
        z = center_z + dz
        arc_pts.append((y, z))

    for i in range(segments):
        y0, z0 = arc_pts[i]
        y1, z1 = arc_pts[i+1]
        v_bl_in = bm.verts.new((x_max, y0, z0))
        v_br_in = bm.verts.new((x_max, y1, z1))
        v_tr_in = bm.verts.new((x_max, y1, z_top))
        v_tl_in = bm.verts.new((x_max, y0, z_top))

        v_bl_out = bm.verts.new((x_min, y0, z0))
        v_br_out = bm.verts.new((x_min, y1, z1))
        v_tr_out = bm.verts.new((x_min, y1, z_top))
        v_tl_out = bm.verts.new((x_min, y0, z_top))

        bm.faces.new((v_bl_out, v_tl_out, v_tr_out, v_br_out))
        bm.faces.new((v_bl_in, v_br_in, v_tr_in, v_tl_in))
        bm.faces.new((v_bl_out, v_br_out, v_br_in, v_bl_in))
        bm.faces.new((v_tl_out, v_tl_in, v_tr_in, v_tr_out))

def add_arch_spandrel_x(bm, y_min, y_max, x_start, x_end, z_spring, z_crown, z_top, segments=12):
    """Construye un arco a lo largo del eje X (para fachadas norte y sur)."""
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
        dz = math.sqrt(max(0.0, r**2 - dy_sq if (dy_sq := dx**2) <= r**2 else 0.0))
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

def add_sloped_roof_hip(bm, x_eave, x_ridge, y_start, y_end, z_eave, z_ridge, hip_y_start=None, hip_y_end=None):
    """Construye un plano inclinado de cubierta a cuatro aguas (faldón principal Cárdenas)."""
    y0_eave = y_start if hip_y_start is None else hip_y_start
    y1_eave = y_end if hip_y_end is None else hip_y_end
    y0_ridge = y_start + (x_ridge - x_eave) if hip_y_start is not None else y_start
    y1_ridge = y_end - (x_ridge - x_eave) if hip_y_end is not None else y_end

    v_eave_l = bm.verts.new((x_eave, y0_eave, z_eave))
    v_eave_r = bm.verts.new((x_eave, y1_eave, z_eave))
    v_ridge_r = bm.verts.new((x_ridge, y1_ridge, z_ridge))
    v_ridge_l = bm.verts.new((x_ridge, y0_ridge, z_ridge))

    bm.faces.new((v_eave_l, v_eave_r, v_ridge_r, v_ridge_l))

    # Cierre inferior de plafón
    v_soff_l = bm.verts.new((x_eave, y0_eave, z_eave - 0.12))
    v_soff_r = bm.verts.new((x_eave, y1_eave, z_eave - 0.12))
    v_soff_rr = bm.verts.new((x_ridge, y1_ridge, z_ridge - 0.12))
    v_soff_rl = bm.verts.new((x_ridge, y0_ridge, z_ridge - 0.12))

    bm.faces.new((v_soff_l, v_soff_rl, v_soff_rr, v_soff_r))
    bm.faces.new((v_eave_l, v_soff_l, v_soff_r, v_eave_r)) # Fascia frontal

def add_sloped_roof_hip_end(bm, x_eave_front, x_ridge, y_eave_end, y_ridge_hip, z_eave, z_ridge, is_north=True):
    """Construye el faldón inclinado de cierre testero (hip end) en Norte o Sur."""
    v_corner_front = bm.verts.new((x_eave_front, y_eave_end, z_eave))
    v_ridge = bm.verts.new((x_ridge, y_ridge_hip, z_ridge))
    v_corner_back = bm.verts.new((x_ridge, y_eave_end, z_eave))

    if is_north:
        bm.faces.new((v_corner_front, v_corner_back, v_ridge))
    else:
        bm.faces.new((v_corner_front, v_ridge, v_corner_back))

    v_soff_front = bm.verts.new((x_eave_front, y_eave_end, z_eave - 0.12))
    v_soff_ridge = bm.verts.new((x_ridge, y_ridge_hip, z_ridge - 0.12))
    v_soff_back = bm.verts.new((x_ridge, y_eave_end, z_eave - 0.12))

    if is_north:
        bm.faces.new((v_soff_front, v_soff_ridge, v_soff_back))
        bm.faces.new((v_corner_front, v_soff_front, v_soff_back, v_corner_back))
    else:
        bm.faces.new((v_soff_front, v_soff_back, v_soff_ridge))
        bm.faces.new((v_corner_front, v_corner_back, v_soff_back, v_soff_front))

def add_teja_ribs(bm, x_eave, x_ridge, y_start, y_end, z_eave, z_ridge, spacing=0.45, hip_y_start=None, hip_y_end=None):
    """Genera hiladas longitudinales de teja colonial con volumen físico recortadas en las limaoyas."""
    num_ribs = int((y_end - y_start) / spacing)
    delta_x = x_ridge - x_eave
    for i in range(num_ribs):
        yc = y_start + i * spacing
        xr = x_ridge
        if hip_y_start is not None and yc < hip_y_start + delta_x:
            xr = x_eave + max(0.15, yc - hip_y_start)
        elif hip_y_end is not None and yc > hip_y_end - delta_x:
            xr = x_eave + max(0.15, hip_y_end - yc)

        if xr <= x_eave + 0.20:
            continue

        zr = z_eave + (z_ridge - z_eave) * ((xr - x_eave) / delta_x)
        v0 = bm.verts.new((x_eave, yc - 0.08, z_eave + 0.04))
        v1 = bm.verts.new((x_eave, yc + 0.08, z_eave + 0.04))
        v2 = bm.verts.new((xr, yc + 0.08, zr + 0.04))
        v3 = bm.verts.new((xr, yc - 0.08, zr + 0.04))
        v_top0 = bm.verts.new((x_eave, yc, z_eave + 0.09))
        v_top1 = bm.verts.new((xr, yc, zr + 0.09))

        bm.faces.new((v0, v1, v_top0))
        bm.faces.new((v1, v2, v_top1, v_top0))
        bm.faces.new((v2, v3, v_top1))
        bm.faces.new((v3, v0, v_top0, v_top1))

def create_mesh_object(name, bm, material, col):
    """Convierte BMesh en Mesh, asigna material y vincula a la colección."""
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
    """Crea un objeto de texto 3D anti-espejo."""
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
# 2. Materiales PBR Calibrados
# ---------------------------------------------------------------------------

def make_pbr(name, base_color, roughness=0.85, metallic=0.0, alpha=1.0, tex_prefix=None, use_tex_albedo=True):
    """Crea un material Principled BSDF calibrado con enlace opcional de texturas."""
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
            mat.node_tree.links.new(tex_coord.outputs['Object'], t_alb.inputs['Vector'])
            mat.node_tree.links.new(t_alb.outputs['Color'], bsdf.inputs['Base Color'])

        if os.path.exists(rough_path):
            t_rgh = nodes.new(type='ShaderNodeTexImage')
            t_rgh.image = bpy.data.images.load(rough_path)
            t_rgh.image.colorspace_settings.name = 'Non-Color'
            mat.node_tree.links.new(tex_coord.outputs['Object'], t_rgh.inputs['Vector'])
            mat.node_tree.links.new(t_rgh.outputs['Color'], bsdf.inputs['Roughness'])

        if os.path.exists(norm_path):
            t_nrm = nodes.new(type='ShaderNodeTexImage')
            t_nrm.image = bpy.data.images.load(norm_path)
            t_nrm.image.colorspace_settings.name = 'Non-Color'
            n_node = nodes.new(type='ShaderNodeNormalMap')
            n_node.inputs['Strength'].default_value = 0.8
            mat.node_tree.links.new(tex_coord.outputs['Object'], t_nrm.inputs['Vector'])
            mat.node_tree.links.new(t_nrm.outputs['Color'], n_node.inputs['Color'])
            mat.node_tree.links.new(n_node.outputs['Normal'], bsdf.inputs['Normal'])

    mat.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def create_materials():
    mats = {}
    # Estructura principal
    mats["estuco_ocre"] = make_pbr("M_Estuco_Ocre_Colonial", (0.86, 0.81, 0.72), roughness=0.88, tex_prefix="hotel_tecate_stucco", use_tex_albedo=False)
    mats["pilastra_laja"] = make_pbr("M_Piedra_Laja_Pilastras", (0.75, 0.62, 0.45), roughness=0.90, tex_prefix="kiosko_laja")
    mats["ladrillo_dovelas"] = make_pbr("M_Ladrillo_Dovelas_Arcos", (0.55, 0.28, 0.20), roughness=0.85, tex_prefix="kiosko_ladrillo")
    mats["piso_terracota"] = make_pbr("M_Piso_Terracota_Portal", (0.68, 0.26, 0.18), roughness=0.70)
    mats["teja_colonial"] = make_pbr("M_Teja_Colonial_Cubierta", (0.58, 0.22, 0.14), roughness=0.80, tex_prefix="kiosko_teja")
    mats["madera_canes"] = make_pbr("M_Madera_Canes_Alero", (0.24, 0.15, 0.10), roughness=0.65)
    mats["herreria_negra"] = make_pbr("M_Herreria_Negra_Forja", (0.05, 0.05, 0.05), roughness=0.40, metallic=0.85)
    mats["zocalo_basal"] = make_pbr("M_Zocalo_Basal_Enterrado", (0.12, 0.13, 0.14), roughness=0.95)
    mats["concreto_losa"] = make_pbr("M_Concreto_Fascia_Terraza", (0.86, 0.84, 0.80), roughness=0.60)
    mats["vidrio_comercial"] = make_pbr("M_Vidrio_Comercial", (0.82, 0.88, 0.92), roughness=0.08, alpha=0.35)
    mats["vidrio_oscuro"] = make_pbr("M_Vidrio_Oscuro_ATM", (0.12, 0.13, 0.15), roughness=0.10, alpha=0.85)
    mats["aluminio_negro"] = make_pbr("M_Aluminio_Negro_Canceles", (0.10, 0.10, 0.10), roughness=0.30, metallic=0.80)
    mats["aluminio_blanco"] = make_pbr("M_Aluminio_Blanco", (0.95, 0.95, 0.95), roughness=0.25, metallic=0.50)
    mats["persianas_blancas"] = make_pbr("M_Persianas_Verticales", (0.92, 0.92, 0.92), roughness=0.60)
    mats["azotea_asfalto"] = make_pbr("M_Azotea_Asfalto", (0.20, 0.20, 0.22), roughness=0.92)
    mats["muro_posterior_cardenas"] = make_pbr("M_Muro_Posterior_Cardenas", (0.80, 0.76, 0.68), roughness=0.88)
    mats["puerta_servicio_gris"] = make_pbr("M_Puerta_Servicio_Gris", (0.45, 0.47, 0.50), roughness=0.40, metallic=0.6)

    # Rótulos Santander
    mats["santander_rojo"] = make_pbr("M_Santander_Rojo", (0.86, 0.00, 0.00), roughness=0.25)
    mats["santander_blanco"] = make_pbr("M_Santander_Letras", (0.98, 0.98, 0.98), roughness=0.15)
    mats["totem_acero"] = make_pbr("M_Totem_Acero", (0.30, 0.32, 0.35), roughness=0.30, metallic=0.90)

    # La Michoacana
    mats["michoacana_rosa"] = make_pbr("M_Michoacana_Rosa", (0.85, 0.15, 0.45), roughness=0.30)
    mats["michoacana_blanco"] = make_pbr("M_Michoacana_Blanco", (0.96, 0.96, 0.96), roughness=0.20)
    mats["michoacana_azul"] = make_pbr("M_Michoacana_Azul", (0.10, 0.40, 0.75), roughness=0.30)

    # Casa Musical y Óptica
    mats["casa_musical_amarillo"] = make_pbr("M_Casa_Musical_Amarillo", (0.92, 0.75, 0.12), roughness=0.30)
    mats["casa_musical_letras"] = make_pbr("M_Casa_Musical_Letras", (0.10, 0.10, 0.10), roughness=0.25)
    mats["mural_guitarra"] = make_pbr("M_Mural_Guitarra_Madera", (0.60, 0.32, 0.15), roughness=0.55)
    mats["optica_azul"] = make_pbr("M_Optica_Azul", (0.08, 0.22, 0.55), roughness=0.25)
    mats["optica_blanco"] = make_pbr("M_Optica_Blanco", (0.96, 0.96, 0.96), roughness=0.20)

    # Clínicas y Telas Vero
    mats["clinica_azul"] = make_pbr("M_Clinica_Azul", (0.12, 0.35, 0.60), roughness=0.30)
    mats["telas_vero_rojo"] = make_pbr("M_Telas_Vero_Rojo", (0.80, 0.10, 0.10), roughness=0.25)
    mats["telas_vero_celeste"] = make_pbr("M_Telas_Vero_Celeste", (0.20, 0.55, 0.85), roughness=0.25)
    mats["calavera_negro"] = make_pbr("M_Calavera_Tattoo_Negro", (0.08, 0.08, 0.09), roughness=0.35)
    mats["calavera_dorado"] = make_pbr("M_Calavera_Tattoo_Dorado", (0.85, 0.70, 0.22), roughness=0.30, metallic=0.7)

    # Regalos Brisa
    mats["brisa_azul"] = make_pbr("M_Regalos_Brisa_Azul", (0.15, 0.45, 0.80), roughness=0.25)
    mats["brisa_blanco"] = make_pbr("M_Regalos_Brisa_Blanco", (0.96, 0.96, 0.96), roughness=0.20)
    mats["vestido_blanco"] = make_pbr("M_Vestido_Bautizo_Blanco", (0.96, 0.96, 0.96), roughness=0.30)
    mats["vestido_verde"] = make_pbr("M_Vestido_Quince_Verde", (0.10, 0.65, 0.35), roughness=0.25)
    mats["vestido_rojo"] = make_pbr("M_Vestido_Gala_Rojo", (0.75, 0.10, 0.15), roughness=0.25)
    mats["farol_metal"] = make_pbr("M_Farol_Metal_Forja", (0.08, 0.08, 0.08), roughness=0.40, metallic=0.8)
    mats["farol_vidrio"] = make_pbr("M_Farol_Vidrio_Ambar", (0.95, 0.90, 0.60), roughness=0.15, alpha=0.70)

    # Rótulos Planta Alta
    mats["salamandra_amarillo"] = make_pbr("M_Salamandra_Amarillo", (0.92, 0.88, 0.50), roughness=0.40)
    mats["salamandra_letras"] = make_pbr("M_Salamandra_Letras", (0.75, 0.15, 0.10), roughness=0.30)
    mats["siesa_azul"] = make_pbr("M_Siesa_Azul", (0.08, 0.30, 0.70), roughness=0.25)
    mats["siesa_dorado"] = make_pbr("M_Siesa_Dorado", (0.90, 0.78, 0.15), roughness=0.30, metallic=0.5)

    # La Parrilla
    mats["parrilla_terracota"] = make_pbr("M_Parrilla_Terracota_Rustic", (0.85, 0.48, 0.28), roughness=0.88)
    mats["parrilla_rojo_letras"] = make_pbr("M_Parrilla_Rojo_Escarlata", (0.62, 0.12, 0.12), roughness=0.35)
    mats["parrilla_madera_vigas"] = make_pbr("M_Parrilla_Madera_Vigas", (0.28, 0.18, 0.12), roughness=0.75)
    mats["parrilla_reja_negra"] = make_pbr("M_Parrilla_Reja_Negra", (0.06, 0.06, 0.06), roughness=0.45, metallic=0.7)
    mats["parrilla_verde_interior"] = make_pbr("M_Parrilla_Verde_Interior", (0.12, 0.45, 0.35), roughness=0.85)
    mats["adt_azul"] = make_pbr("M_ADT_Azul_Logo", (0.05, 0.25, 0.65), roughness=0.25)

    # Estacionamiento y exteriores
    mats["asfalto_estacionamiento"] = make_pbr("M_Asfalto_Estacionamiento", (0.25, 0.24, 0.23), roughness=0.95)
    mats["barda_tradicion_blanca"] = make_pbr("M_Barda_Tradicion_Blanca", (0.92, 0.91, 0.88), roughness=0.85)
    mats["medidores_cfe"] = make_pbr("M_Medidores_CFE_Metal", (0.55, 0.58, 0.60), roughness=0.35, metallic=0.85)

    return mats

# ---------------------------------------------------------------------------
# 3. Construcción del Frente Principal (13 Arcos y 14 Pilastras)
# ---------------------------------------------------------------------------

def build_front_cardenas(mats, col):
    """Construye las 13 crujías frontales sobre Pdte. Lázaro Cárdenas (Longitud ajustada 70.20 m)."""
    objects = []
    bay_count = 13
    total_y = 70.20
    bay_w = total_y / bay_count # Exactamente 5.40 m
    pilar_w = 0.60
    pilar_d = 0.60
    rot_cardenas = (math.radians(90.0), 0.0, math.radians(-90.0))

    # A. ZÓCALO BASAL ENTERRADO (-1.50 a 0.00 m)
    bm_zocalo = bmesh.new()
    add_box(bm_zocalo, -0.40, 11.40, -0.40, total_y + 0.40, -1.50, 0.00)
    obj_zocalo = create_mesh_object("Cardenas_Zocalo_Basal_Enterrado", bm_zocalo, mats["zocalo_basal"], col)
    objects.append(obj_zocalo)

    # B. 14 PILASTRAS DE MAMPOSTERÍA DE LAJA DORADA (Z in [0.00, 2.35 m])
    bm_pil = bmesh.new()
    for i in range(bay_count + 1):
        yc = i * bay_w
        y1 = max(0.00, yc - pilar_w * 0.5)
        y2 = min(total_y, yc + pilar_w * 0.5)
        add_box(bm_pil, 0.00, pilar_d, y1, y2, 0.00, 2.25)
        add_box(bm_pil, -0.05, pilar_d + 0.05, y1 - 0.04, y2 + 0.04, 2.25, 2.35)
    obj_pil = create_mesh_object("Cardenas_14_Pilastras_Laja", bm_pil, mats["pilastra_laja"], col)
    objects.append(obj_pil)

    # C. 13 ARCOS REBAJADOS CON DOVELAS DE LADRILLO Y ENJUTAS (Z in [2.35, 3.40 m])
    bm_arcos = bmesh.new()
    bm_dovelas = bmesh.new()
    for i in range(bay_count):
        y_start = i * bay_w + pilar_w * 0.5
        y_end = (i + 1) * bay_w - pilar_w * 0.5
        add_arch_spandrel(bm_arcos, 0.00, pilar_d, y_start, y_end, 2.35, 3.10, 3.40, segments=14)
        add_arch_spandrel(bm_dovelas, -0.04, 0.00, y_start, y_end, 2.35, 3.10, 3.35, segments=14)

    obj_arcos = create_mesh_object("Cardenas_13_Arcos_Enjutas", bm_arcos, mats["estuco_ocre"], col)
    obj_dov = create_mesh_object("Cardenas_13_Arcos_DovelasLadrillo", bm_dovelas, mats["ladrillo_dovelas"], col)
    objects.extend([obj_arcos, obj_dov])

    # D. GALERÍA PORTICADA: FIRME DE TERRACOTA Y TECHO DE VIGAS (X in [0.00, 2.40 m])
    bm_piso = bmesh.new()
    add_box(bm_piso, 0.00, 2.40, 0.00, total_y, 0.00, 0.06)
    obj_piso = create_mesh_object("Cardenas_Portal_Piso_Terracota", bm_piso, mats["piso_terracota"], col)
    objects.append(obj_piso)

    bm_vigas_p = bmesh.new()
    for i in range(int(total_y * 1.5)):
        y_beam = i * 0.67
        if y_beam < total_y:
            add_box(bm_vigas_p, 0.60, 2.38, y_beam - 0.06, y_beam + 0.06, 3.22, 3.38)
    obj_vp = create_mesh_object("Cardenas_Portal_Vigas_Techo", bm_vigas_p, mats["madera_canes"], col)
    objects.append(obj_vp)

    # E. CANCELERÍAS RETRANQUEADAS Y FACHADA COMERCIAL INTERIOR (X = 2.40 m)
    bm_canceles = bmesh.new()
    bm_vidrio = bmesh.new()
    bm_persianas = bmesh.new()
    bm_murales = bmesh.new()

    for i in range(bay_count):
        y_bay1 = i * bay_w
        y_bay2 = (i + 1) * bay_w
        y_mid = (y_bay1 + y_bay2) * 0.5

        if i == 6:
            # Escalera central a planta alta (Arco 7, diáfano sin cancel)
            bm_esc = bmesh.new()
            step_count = 18
            step_h = 3.40 / step_count # 0.188 m
            step_d = 2.40 / step_count
            for s in range(step_count):
                x_s1 = 2.40 + s * step_d
                x_s2 = 2.40 + (s + 1) * step_d
                z_s = (s + 1) * step_h
                add_box(bm_esc, x_s1, x_s2, y_bay1 + 0.80, y_bay2 - 0.80, 0.00, z_s)
            obj_esc = create_mesh_object("Cardenas_Escalera_Central_Transitable", bm_esc, mats["concreto_losa"], col)
            objects.append(obj_esc)
            continue

        add_box(bm_canceles, 2.35, 2.50, y_bay1, y_bay2, 0.00, 0.40)
        add_box(bm_canceles, 2.35, 2.50, y_bay1, y_bay2, 2.90, 3.40)
        add_box(bm_canceles, 2.35, 2.50, y_bay1, y_bay1 + 0.20, 0.40, 2.90)
        add_box(bm_canceles, 2.35, 2.50, y_bay2 - 0.20, y_bay2, 0.40, 2.90)

        add_box(bm_vidrio, 2.38, 2.42, y_bay1 + 0.20, y_bay2 - 0.20, 0.40, 2.90)

        if i in [0, 2, 3]: # Santander oficinas: persianas
            add_box(bm_persianas, 2.43, 2.45, y_bay1 + 0.25, y_bay2 - 0.25, 0.45, 2.85)
        elif i == 1: # Santander acceso principal
            add_box(bm_canceles, 2.34, 2.48, y_mid - 0.90, y_mid + 0.90, 0.00, 2.60)
        elif i == 7: # Casa Musical Tecate: mural de guitarra en enjuta
            add_box(bm_murales, 2.37, 2.41, y_mid - 0.80, y_mid + 0.80, 2.20, 2.85)

    obj_canc = create_mesh_object("Cardenas_Canceles_PB", bm_canceles, mats["aluminio_negro"], col)
    obj_vid = create_mesh_object("Cardenas_Vidrios_PB", bm_vidrio, mats["vidrio_comercial"], col)
    obj_pers = create_mesh_object("Cardenas_Persianas_PB", bm_persianas, mats["persianas_blancas"], col)
    obj_mur = create_mesh_object("Cardenas_Mural_CasaMusical", bm_murales, mats["mural_guitarra"], col)
    objects.extend([obj_canc, obj_vid, obj_pers, obj_mur])

    # F. RÓTULOS COMERCIALES FRONTALES EN PLANTA BAJA (2009)
    # Santander: Marquesina roja monumental sobre Arco 2
    bm_sant = bmesh.new()
    add_box(bm_sant, -0.22, 0.15, 5.80, 10.40, 2.50, 3.25)
    obj_s_box = create_mesh_object("Santander_Caja_Marquesina", bm_sant, mats["santander_rojo"], col)
    objects.append(obj_s_box)
    t_sant = add_3d_text("Santander_Txt_Frontal", "Santander", 0.50, 0.04, (-0.24, 8.10, 2.82), rot_cardenas, mats["santander_blanco"], col)
    objects.append(t_sant)

    # Tótem Santander en banqueta (Arco 4)
    bm_totem = bmesh.new()
    add_box(bm_totem, -1.80, -1.65, 19.30, 19.50, 0.00, 5.80)
    add_box(bm_totem, -1.85, -1.60, 18.80, 20.00, 4.30, 5.75)
    obj_tot = create_mesh_object("Santander_Totem_Exterior", bm_totem, mats["santander_rojo"], col)
    objects.append(obj_tot)

    # La Michoacana: Fascia entrepiso sobre Arcos 5 y 6
    bm_mich = bmesh.new()
    add_box(bm_mich, -0.08, 0.08, 22.50, 31.80, 3.25, 3.75)
    obj_mich = create_mesh_object("Michoacana_Panel_Fascia", bm_mich, mats["michoacana_blanco"], col)
    objects.append(obj_mich)
    t_m1 = add_3d_text("Michoacana_Txt_Paleteria", "LA MICHOACANA", 0.38, 0.03, (-0.10, 27.15, 3.55), rot_cardenas, mats["michoacana_rosa"], col)
    t_m2 = add_3d_text("Michoacana_Txt_Sub", "PALETERIA  Y  NEVERIA", 0.22, 0.02, (-0.10, 27.15, 3.35), rot_cardenas, mats["michoacana_azul"], col)
    objects.extend([t_m1, t_m2])

    # Casa Musical Tecate: Rótulo sobre Arco 8
    bm_mus = bmesh.new()
    add_box(bm_mus, -0.06, 0.08, 38.20, 42.80, 2.95, 3.35)
    obj_mus = create_mesh_object("CasaMusical_Panel", bm_mus, mats["casa_musical_amarillo"], col)
    objects.append(obj_mus)
    t_mus = add_3d_text("CasaMusical_Txt", "GUITARRAS\nCASA MUSICAL TECATE", 0.22, 0.025, (-0.08, 40.50, 3.12), rot_cardenas, mats["casa_musical_letras"], col)
    objects.append(t_mus)

    # Óptica San Martín: Rótulo en bandera sobre Arco 9
    bm_opt = bmesh.new()
    add_box(bm_opt, -0.45, 0.05, 44.60, 47.20, 3.20, 3.65)
    obj_opt = create_mesh_object("Optica_Caja_Bandera", bm_opt, mats["optica_blanco"], col)
    objects.append(obj_opt)
    t_opt = add_3d_text("Optica_Txt", "OPTICA\nSAN MARTIN", 0.20, 0.02, (-0.46, 45.90, 3.40), rot_cardenas, mats["optica_azul"], col)
    objects.append(t_opt)

    # Consultorios: Rótulo sobre Arco 10
    t_dent = add_3d_text("Dentista_Txt", "DENTISTA / GINECOLOGA", 0.22, 0.02, (2.36, 51.30, 3.10), rot_cardenas, mats["clinica_azul"], col)
    objects.append(t_dent)

    # Telas y Novedades Vero: Rótulo sobre Arco 12
    bm_vero = bmesh.new()
    add_box(bm_vero, -0.06, 0.08, 59.80, 64.40, 3.25, 3.75)
    obj_vero = create_mesh_object("TelasVero_Panel", bm_vero, mats["brisa_blanco"], col)
    objects.append(obj_vero)
    t_v1 = add_3d_text("TelasVero_Txt1", "TELAS Y NOVEDADES", 0.24, 0.02, (-0.08, 62.10, 3.58), rot_cardenas, mats["telas_vero_rojo"], col)
    t_v2 = add_3d_text("TelasVero_Txt2", "VERO", 0.35, 0.03, (-0.08, 62.10, 3.38), rot_cardenas, mats["telas_vero_celeste"], col)
    objects.extend([t_v1, t_v2])

    # Regalos Brisa: Rótulo monumental sobre Arco 13
    bm_brisa = bmesh.new()
    add_box(bm_brisa, -0.10, 0.12, 65.00, 70.00, 3.25, 3.90)
    obj_brisa = create_mesh_object("RegalosBrisa_Panel", bm_brisa, mats["brisa_blanco"], col)
    objects.append(obj_brisa)
    t_b1 = add_3d_text("Brisa_Txt1", "REGALOS BRISA", 0.38, 0.03, (-0.12, 67.50, 3.65), rot_cardenas, mats["brisa_azul"], col)
    t_b2 = add_3d_text("Brisa_Txt2", "ROPA DE BAUTIZO • RECUERDOS • RAMOS • PRIMERA COMUNION", 0.13, 0.015, (-0.12, 67.50, 3.40), rot_cardenas, mats["brisa_azul"], col)
    objects.extend([t_b1, t_b2])

    # G. PLANTA ALTA: TERRAZA TRANSITABLE Y VENTANALES (Z in [3.40, 6.35 m])
    bm_terraza = bmesh.new()
    add_box(bm_terraza, 0.00, 2.40, 0.00, total_y, 3.35, 3.45)
    add_box(bm_terraza, -0.08, 0.02, 0.00, total_y, 3.30, 3.48)
    obj_ter = create_mesh_object("Cardenas_Terraza_Piso", bm_terraza, mats["concreto_losa"], col)
    objects.append(obj_ter)

    bm_barandal = bmesh.new()
    add_box(bm_barandal, -0.03, 0.03, 0.00, total_y, 4.35, 4.40)
    add_box(bm_barandal, -0.02, 0.02, 0.00, total_y, 3.48, 3.52)
    for i in range(int(total_y / 0.15)):
        y_bar = i * 0.15
        add_box(bm_barandal, -0.012, 0.012, y_bar - 0.012, y_bar + 0.012, 3.50, 4.35)
    obj_bar = create_mesh_object("Cardenas_Barandal_Terraza", bm_barandal, mats["herreria_negra"], col)
    objects.append(obj_bar)

    # Muro y Ventanales en Arco de Planta Alta (X = 2.40 m)
    bm_muro_pa = bmesh.new()
    bm_vidrio_pa = bmesh.new()
    bm_arcos_pa = bmesh.new()

    for i in range(bay_count):
        y_bay1 = i * bay_w
        y_bay2 = (i + 1) * bay_w
        y_mid = (y_bay1 + y_bay2) * 0.5
        w_van = 3.60
        y_v1 = y_mid - w_van * 0.5
        y_v2 = y_mid + w_van * 0.5

        add_box(bm_muro_pa, 2.35, 2.50, y_bay1, y_v1, 3.45, 6.35)
        add_box(bm_muro_pa, 2.35, 2.50, y_v2, y_bay2, 3.45, 6.35)
        add_box(bm_muro_pa, 2.35, 2.50, y_v1, y_v2, 3.45, 4.20)
        add_box(bm_muro_pa, 2.35, 2.50, y_v1, y_v2, 5.90, 6.35)

        add_box(bm_vidrio_pa, 2.38, 2.42, y_v1, y_v2, 4.20, 5.85)
        add_arch_spandrel(bm_arcos_pa, 2.34, 2.46, y_v1, y_v2, 5.20, 5.85, 6.00, segments=12)

    obj_mpa = create_mesh_object("Cardenas_Muros_PA", bm_muro_pa, mats["estuco_ocre"], col)
    obj_vpa = create_mesh_object("Cardenas_Vidrios_PA", bm_vidrio_pa, mats["vidrio_comercial"], col)
    obj_apa = create_mesh_object("Cardenas_Arcos_Ladrillo_PA", bm_arcos_pa, mats["ladrillo_dovelas"], col)
    objects.extend([obj_mpa, obj_vpa, obj_apa])

    # Rótulos en Planta Alta (2009)
    # Se Renta (Arco 2)
    t_rent = add_3d_text("SeRenta_Txt", "SE RENTA\n654-79-88", 0.28, 0.02, (2.35, 8.10, 5.10), rot_cardenas, mats["telas_vero_rojo"], col)
    objects.append(t_rent)

    # Grupo Siesa Guardias (Arco 3)
    bm_sie1 = bmesh.new()
    add_box(bm_sie1, 2.34, 2.38, 11.80, 15.20, 4.70, 5.50)
    obj_sie1 = create_mesh_object("Siesa1_Panel", bm_sie1, mats["siesa_azul"], col)
    objects.append(obj_sie1)
    t_sie1 = add_3d_text("Siesa1_Txt", "GRUPO SIESA\nSOLICITA GUARDIAS", 0.22, 0.02, (2.32, 13.50, 5.10), rot_cardenas, mats["siesa_dorado"], col)
    objects.append(t_sie1)

    # Grupo Siesa CCTV (Arco 4)
    bm_sie2 = bmesh.new()
    add_box(bm_sie2, 2.34, 2.38, 17.20, 20.80, 4.70, 5.50)
    obj_sie2 = create_mesh_object("Siesa2_Panel", bm_sie2, mats["siesa_azul"], col)
    objects.append(obj_sie2)
    t_sie2 = add_3d_text("Siesa2_Txt", "GRUPO SIESA\nVIDEOPORTEROS / CCTV", 0.22, 0.02, (2.32, 19.00, 5.10), rot_cardenas, mats["siesa_dorado"], col)
    objects.append(t_sie2)

    # Calavera Tattoo Studio (Arco 12)
    bm_cal = bmesh.new()
    add_box(bm_cal, 2.34, 2.38, 60.50, 64.00, 4.70, 5.50)
    obj_cal = create_mesh_object("Calavera_Panel", bm_cal, mats["calavera_negro"], col)
    objects.append(obj_cal)
    t_cal = add_3d_text("Calavera_Txt", "CALAVERA\ntattoo studio", 0.25, 0.02, (2.32, 62.25, 5.10), rot_cardenas, mats["calavera_dorado"], col)
    objects.append(t_cal)

    # H. TECHUMBRE DE TEJAS COLONIALES Y ALEROS VOLADOS (Z in [6.35, 7.35 m])
    bm_techo = bmesh.new()
    bm_canes = bmesh.new()
    bm_postes = bmesh.new()

    for i in range(bay_count + 1):
        yc = i * bay_w
        add_box(bm_postes, 0.02, 0.10, yc - 0.04, yc + 0.04, 4.35, 6.35)
    obj_pst = create_mesh_object("Cardenas_Postes_Terraza", bm_postes, mats["herreria_negra"], col)
    objects.append(obj_pst)

    for i in range(2, int(total_y / 0.70) - 1):
        yc = i * 0.70
        add_box(bm_canes, -0.85, 0.60, yc - 0.06, yc + 0.06, 6.22, 6.34)
    obj_cns = create_mesh_object("Cardenas_Canes_Madera", bm_canes, mats["madera_canes"], col)
    objects.append(obj_cns)

    add_sloped_roof_hip(bm_techo, -0.85, 3.20, -0.85, total_y + 0.85, 6.35, 7.35, hip_y_start=-0.85, hip_y_end=total_y + 0.85)
    add_teja_ribs(bm_techo, -0.85, 3.20, -0.85, total_y + 0.85, 6.35, 7.35, spacing=0.45, hip_y_start=-0.85, hip_y_end=total_y + 0.85)
    obj_tch = create_mesh_object("Cardenas_Techo_Tejas_Colonial", bm_techo, mats["teja_colonial"], col)
    objects.append(obj_tch)

    # Cubierta plana hermética de azotea principal (X in [3.20, 11.20 m])
    bm_azot = bmesh.new()
    add_box(bm_azot, 2.50, 11.20, 0.00, total_y, 6.20, 6.35)
    add_box(bm_azot, 11.00, 11.35, 0.00, total_y, 6.35, 6.75) # Pretil trasero

    # 4 Tinacos cilíndricos de azotea
    for tin_y in [11.0, 27.0, 44.0, 62.0]:
        add_box(bm_azot, 5.00, 6.40, tin_y - 0.70, tin_y + 0.70, 6.35, 7.85)
    obj_az = create_mesh_object("Cardenas_Azotea_Asfalto_Tinacos", bm_azot, mats["azotea_asfalto"], col)
    objects.append(obj_az)

    return objects

# ---------------------------------------------------------------------------
# 4. Construcción de Fachadas Norte (Libertad) y Sur (Hidalgo)
# ---------------------------------------------------------------------------

def build_north_libertad_facade(mats, col):
    """Construye la fachada norte sobre Callejón Libertad con balcón corrido diáfano y ATM detallado."""
    objects = []
    rot_north = (math.radians(90.0), 0.0, 0.0)

    bm_muro = bmesh.new()
    bm_ladrillo = bmesh.new()
    bm_atm = bmesh.new()
    bm_techo_n = bmesh.new()
    bm_balcon = bmesh.new()

    x_cardenas_end = 14.20 # Límite del edificio Cárdenas 25 en Libertad

    # 1. PLANTA BAJA: Muro base con arcos calados (X in [0.00, 14.20 m], Y = 0.00 m)
    add_box(bm_muro, 0.00, 14.20, -0.15, 0.20, 0.00, 0.40) # Zócalo
    add_box(bm_muro, 0.00, 14.20, -0.15, 0.20, 3.20, 3.40) # Dintel entrepiso

    # Arcos 1 y 2: Ciegos con zócalo de laja dorada (X in [0.40, 4.40] y [4.80, 8.80])
    for i in range(2):
        x1 = i * 4.40 + 0.40
        x2 = (i + 1) * 4.40 - 0.20
        add_arch_spandrel_x(bm_ladrillo, -0.18, -0.12, x1, x2, 2.20, 2.95, 3.20, segments=12)
        add_box(bm_muro, x1, x2, -0.16, -0.13, 0.40, 0.90) # Murete de laja
        add_box(bm_muro, x1, x2, -0.15, -0.14, 0.90, 2.20) # Paño ciego estucado

    # Arco 3 (Cajero Automático Santander - ATM, X in [9.00, 13.80 m]):
    add_arch_spandrel_x(bm_ladrillo, -0.18, -0.12, 9.00, 13.80, 2.20, 2.95, 3.20, segments=14)
    # Cancelería de perfiles negros y vidrio oscuro
    add_box(bm_atm, 9.10, 12.60, -0.16, -0.12, 0.00, 2.45)
    # Placa / rótulo vertical rojo Santander en pilastra
    add_box(bm_atm, 8.95, 9.15, -0.18, -0.14, 0.80, 2.35)
    # Puerta de servicio metálica gris junto al callejón
    add_box(bm_muro, 12.65, 13.75, -0.16, -0.13, 0.00, 2.30)

    # 2. PLANTA ALTA: BALCÓN CORRIDO DIÁFANO SOBRE CALLEJÓN LIBERTAD
    # Losa de piso en voladizo (X in [0.00, 14.20 m], Y in [-1.20, 0.00 m])
    add_box(bm_balcon, 0.00, 14.20, -1.20, 0.00, 3.35, 3.45)
    add_box(bm_balcon, 0.00, 14.20, -1.25, -1.18, 3.30, 3.48) # Sardinel

    # Barandal de herrería de forja negra corrida en Y = -1.20 m
    add_box(bm_balcon, 0.00, 14.20, -1.22, -1.18, 4.35, 4.40) # Pasamanos
    add_box(bm_balcon, 0.00, 14.20, -1.21, -1.19, 3.48, 3.52) # Pletina inferior
    for i in range(int(14.20 / 0.15)):
        xb = i * 0.15
        add_box(bm_balcon, xb - 0.012, xb + 0.012, -1.21, -1.19, 3.50, 4.35)

    # 3 grandes ventanales superiores en arco sobre el muro de PA (Y = 0.00 m)
    add_box(bm_muro, 0.00, 14.20, -0.15, 0.15, 3.45, 4.10) # Antepecho
    add_box(bm_muro, 0.00, 14.20, -0.15, 0.15, 6.00, 6.35) # Dintel superior
    for i in range(3):
        x1 = i * 4.40 + 0.60
        x2 = (i + 1) * 4.40 - 0.40
        add_arch_spandrel_x(bm_ladrillo, -0.16, -0.12, x1, x2, 5.10, 5.80, 6.00, segments=12)
        add_box(bm_atm, x1 + 0.10, x2 - 0.10, -0.14, -0.12, 4.10, 5.70) # Vidrio y cancelería blanca

    # Hip return hermético de la cubierta de tejas sobre el frente norte
    add_sloped_roof_hip_end(bm_techo_n, -0.85, 3.20, -0.85, 3.20, 6.35, 7.35, is_north=True)

    obj_mn = create_mesh_object("Libertad_Muro_Norte", bm_muro, mats["estuco_ocre"], col)
    obj_ln = create_mesh_object("Libertad_Arcos_Ladrillo", bm_ladrillo, mats["ladrillo_dovelas"], col)
    obj_atm = create_mesh_object("Libertad_ATM_Canceleria", bm_atm, mats["vidrio_oscuro"], col)
    obj_bal = create_mesh_object("Libertad_Balcon_Terraza_Corrida", bm_balcon, mats["herreria_negra"], col)
    obj_tn = create_mesh_object("Libertad_Techo_Tejas_Hip", bm_techo_n, mats["teja_colonial"], col)
    objects.extend([obj_mn, obj_ln, obj_atm, obj_bal, obj_tn])

    # Rótulo vertical tridimensional CAJERO AUTOMATICO
    t_atm = add_3d_text("Libertad_Txt_Cajero", "CAJERO\nAUTOMATICO", 0.18, 0.02, (9.05, -0.20, 1.65), rot_north, mats["aluminio_blanco"], col)
    objects.append(t_atm)

    # Letrero de Fraccionamiento La Salamandra colgado en el balcón
    bm_sal_b = bmesh.new()
    add_box(bm_sal_b, 1.20, 4.20, -1.24, -1.21, 3.65, 4.30)
    obj_sal_p = create_mesh_object("Libertad_Panel_Salamandra", bm_sal_b, mats["salamandra_amarillo"], col)
    objects.append(obj_sal_p)
    t_sal_b = add_3d_text("Libertad_Txt_Salamandra", "FRACCIONAMIENTO\nLA SALAMANDRA\nLOTES EN ABONOS", 0.16, 0.02, (2.70, -1.26, 3.98), rot_north, mats["salamandra_letras"], col)
    objects.append(t_sal_b)

    # Portón de servicio de reja gris (X in [14.20, 17.20 m])
    bm_reja = bmesh.new()
    add_box(bm_reja, 14.20, 17.20, -0.10, -0.05, 0.00, 2.40)
    for i in range(int(3.0 / 0.15)):
        xr = 14.20 + i * 0.15
        add_box(bm_reja, xr - 0.015, xr + 0.015, -0.11, -0.04, 0.00, 2.45)
    obj_rej = create_mesh_object("Libertad_Reja_Servicio", bm_reja, mats["puerta_servicio_gris"], col)
    objects.append(obj_rej)

    return objects

def build_south_hidalgo_facade(mats, col):
    """Construye la fachada sur sobre Av. Miguel Hidalgo con 2 grandes arcos y ventanales en PA."""
    objects = []
    total_y = 70.20
    rot_south = (math.radians(90.0), 0.0, math.radians(180.0))

    bm_muro_s = bmesh.new()
    bm_dov_s = bmesh.new()
    bm_vid_s = bmesh.new()
    bm_maniqui = bmesh.new()
    bm_med = bmesh.new()
    bm_farol = bmesh.new()
    bm_techo_s = bmesh.new()
    bm_balcon_s = bmesh.new()

    # 1. PLANTA BAJA (Regalos Brisa - X in [0.00, 11.20 m], Y = 70.20 m)
    add_box(bm_muro_s, 0.00, 11.20, total_y - 0.15, total_y + 0.15, 0.00, 0.40) # Zócalo
    add_box(bm_muro_s, 0.00, 11.20, total_y - 0.15, total_y + 0.15, 3.20, 3.40) # Dintel entrepiso
    add_box(bm_muro_s, 0.00, 0.40, total_y - 0.15, total_y + 0.15, 0.40, 3.20) # Machón oriente
    add_box(bm_muro_s, 5.20, 5.80, total_y - 0.15, total_y + 0.15, 0.40, 3.20) # Machón central
    add_box(bm_muro_s, 10.60, 11.20, total_y - 0.15, total_y + 0.15, 0.40, 3.20) # Machón poniente

    # 2 amplios arcos con dovelas de ladrillo y escaparates acristalados
    for i, (x1, x2) in enumerate([(0.40, 5.20), (5.80, 10.60)]):
        add_arch_spandrel_x(bm_dov_s, total_y + 0.15, total_y + 0.20, x1, x2, 2.20, 2.95, 3.20, segments=14)
        add_box(bm_vid_s, x1 + 0.10, x2 - 0.10, total_y + 0.12, total_y + 0.16, 0.40, 2.50)

    # Maniquíes con vestidos de gala en el interior del escaparate
    # Escaparate 1: Bautizo blanco bordado y quinceañera verde esmeralda
    add_box(bm_maniqui, 1.80, 2.40, total_y - 0.25, total_y + 0.05, 0.45, 1.65) # Blanco
    add_box(bm_maniqui, 3.40, 4.10, total_y - 0.25, total_y + 0.05, 0.45, 1.85) # Verde
    # Escaparate 2: Gala rojo rubí y blanco comunión
    add_box(bm_maniqui, 7.00, 7.70, total_y - 0.25, total_y + 0.05, 0.45, 1.85) # Rojo
    add_box(bm_maniqui, 8.80, 9.40, total_y - 0.25, total_y + 0.05, 0.45, 1.65) # Blanco

    # Farol colonial de forja hexagonal en el machón central (X = 5.50 m)
    add_box(bm_farol, 5.42, 5.58, total_y + 0.15, total_y + 0.42, 2.30, 2.75)
    add_box(bm_farol, 5.44, 5.56, total_y + 0.20, total_y + 0.38, 2.35, 2.70) # Linterna

    # Banco de medidores de CFE en el extremo poniente
    add_box(bm_med, 10.40, 11.10, total_y + 0.15, total_y + 0.32, 0.60, 2.10)

    # 2. PLANTA ALTA: 2 VENTANALES MONUMENTALES EN ARCO DE MEDIO PUNTO
    add_box(bm_muro_s, 0.00, 11.20, total_y - 0.15, total_y + 0.15, 3.45, 4.10) # Antepecho
    add_box(bm_muro_s, 0.00, 11.20, total_y - 0.15, total_y + 0.15, 6.00, 6.35) # Dintel superior
    add_box(bm_muro_s, 5.20, 5.80, total_y - 0.15, total_y + 0.15, 4.10, 6.00) # Machón central PA

    for i, (x1, x2) in enumerate([(0.60, 5.20), (5.80, 10.40)]):
        add_arch_spandrel_x(bm_dov_s, total_y + 0.15, total_y + 0.20, x1, x2, 5.00, 5.80, 6.00, segments=12)
        add_box(bm_vid_s, x1 + 0.10, x2 - 0.10, total_y + 0.12, total_y + 0.16, 4.10, 5.75)
        # Montantes de cancelería blanca de 4 paños
        xmid = (x1 + x2) * 0.5
        add_box(bm_muro_s, xmid - 0.04, xmid + 0.04, total_y + 0.11, total_y + 0.17, 4.10, 5.70)
        add_box(bm_muro_s, x1 + 0.10, x2 - 0.10, total_y + 0.11, total_y + 0.17, 4.90, 4.98)

    # Retorno a 90° del balcón de PA en la esquina hacia Hidalgo
    add_box(bm_balcon_s, 0.00, 2.40, total_y, total_y + 1.20, 3.35, 3.45)
    add_box(bm_balcon_s, 0.00, 2.40, total_y + 1.18, total_y + 1.22, 4.35, 4.40) # Pasamanos
    for i in range(int(2.40 / 0.15)):
        xb = i * 0.15
        add_box(bm_balcon_s, xb - 0.012, xb + 0.012, total_y + 1.19, total_y + 1.21, 3.50, 4.35)

    # Hip return hermético de la cubierta de tejas sobre el frente sur
    add_sloped_roof_hip_end(bm_techo_s, -0.85, 3.20, total_y + 0.85, total_y - 3.20, 6.35, 7.35, is_north=False)

    obj_ms = create_mesh_object("Hidalgo_Muro_Sur", bm_muro_s, mats["estuco_ocre"], col)
    obj_ds = create_mesh_object("Hidalgo_Arcos_Ladrillo", bm_dov_s, mats["ladrillo_dovelas"], col)
    obj_vs = create_mesh_object("Hidalgo_Vidrios_Brisa", bm_vid_s, mats["vidrio_comercial"], col)
    obj_mq = create_mesh_object("Hidalgo_Maniquies_Gala", bm_maniqui, mats["vestido_verde"], col)
    obj_far = create_mesh_object("Hidalgo_Farol_Colonial", bm_farol, mats["farol_metal"], col)
    obj_med = create_mesh_object("Hidalgo_Medidores_CFE", bm_med, mats["medidores_cfe"], col)
    obj_bs = create_mesh_object("Hidalgo_Balcon_Retorno", bm_balcon_s, mats["herreria_negra"], col)
    obj_ts = create_mesh_object("Hidalgo_Techo_Tejas_Hip", bm_techo_s, mats["teja_colonial"], col)
    objects.extend([obj_ms, obj_ds, obj_vs, obj_mq, obj_far, obj_med, obj_bs, obj_ts])

    # Rótulo de vinil blanco en ventana poniente: SEGURIDAD COMERCIAL TECATE
    t_seg = add_3d_text("Hidalgo_Txt_Seguridad", "SEGURIDAD COMERCIAL TECATE", 0.18, 0.02, (8.10, total_y + 0.22, 5.15), rot_south, mats["aluminio_blanco"], col)
    objects.append(t_seg)

    return objects

# ---------------------------------------------------------------------------
# 5. Muro Posterior Continuo de Cierre (X = 11.20 m)
# ---------------------------------------------------------------------------

def build_rear_facade(mats, col):
    """Construye el muro posterior continuo de cierre para eliminar al 100% la vista hueca interior."""
    objects = []
    total_y = 70.20
    rot_west = (math.radians(90.0), 0.0, math.radians(90.0))

    bm_rear = bmesh.new()
    bm_puertas = bmesh.new()

    # Muro macizo cerrado continuo (X = 11.20 m, Y in [0.00, 70.20 m], Z in [-1.50, 6.75 m])
    add_box(bm_rear, 11.10, 11.35, 0.00, total_y, -1.50, 6.75)

    # Puertas metálicas de evacuación y servicio en locales clave
    # Santander (Y = 10.0 m), Michoacana (Y = 26.5 m), Casa Musical (Y = 40.0 m), Telas Vero (Y = 62.0 m)
    for y_door in [10.0, 26.5, 40.0, 62.0]:
        add_box(bm_puertas, 11.34, 11.38, y_door - 0.50, y_door + 0.50, 0.00, 2.15)
        # Marco de puerta
        add_box(bm_rear, 11.33, 11.40, y_door - 0.55, y_door + 0.55, 2.15, 2.22)
        add_box(bm_rear, 11.33, 11.40, y_door - 0.58, y_door - 0.50, 0.00, 2.22)
        add_box(bm_rear, 11.33, 11.40, y_door + 0.50, y_door + 0.58, 0.00, 2.22)

    # Bajantes pluviales de PVC blanco cada 18 m
    for y_pipe in [8.0, 26.0, 44.0, 62.0]:
        add_box(bm_rear, 11.34, 11.44, y_pipe - 0.06, y_pipe + 0.06, 0.00, 6.65)

    obj_rf = create_mesh_object("Cardenas_Muro_Posterior_Cierre", bm_rear, mats["muro_posterior_cardenas"], col)
    obj_puer = create_mesh_object("Cardenas_Puertas_Servicio_Posterior", bm_puertas, mats["puerta_servicio_gris"], col)
    objects.extend([obj_rf, obj_puer])

    return objects

# ---------------------------------------------------------------------------
# 6. La Parrilla Restaurant Bar & Grill (Estructura Envolvente en "L" / "U")
# ---------------------------------------------------------------------------

def build_la_parrilla_complete(mats, col):
    """
    Construye La Parrilla como la estructura edificada continua que envuelve el estacionamiento:
      - Frente Norte sobre Callejón Libertad (X in [17.20, 32.50 m], Y = 0.00 m).
      - Ala Este del Estacionamiento (X = 32.50 m, Y in [0.00, 22.00 m]).
      - Gran Cuerpo Sur Envolvente de 2 niveles (X in [32.50, 72.00 m], Y in [20.00, 36.00 m]).
    """
    objects = []
    rot_north = (math.radians(90.0), 0.0, 0.0)
    rot_west = (math.radians(90.0), 0.0, math.radians(90.0))

    bm_muro = bmesh.new()
    bm_espadaña = bmesh.new()
    bm_vigas = bmesh.new()
    bm_ventanas = bmesh.new()
    bm_rejas = bmesh.new()

    # 1. CUERPO NORTE (FRENTE A CALLEJÓN LIBERTAD, Y = 0.00 m)
    # Zócalo basal enterrado (-1.50 a 0.00 m)
    add_box(bm_muro, 17.00, 32.70, -0.20, 22.20, -1.50, 0.00)

    # A. Marquesina rústica izquierda (X in [17.20, 24.00 m])
    add_box(bm_muro, 17.20, 18.20, -0.15, 0.20, 0.00, 3.80)
    add_box(bm_muro, 23.00, 24.00, -0.15, 0.20, 0.00, 3.80)
    add_box(bm_muro, 18.20, 23.00, -0.15, 0.20, 0.00, 0.90) # Antepecho
    add_box(bm_muro, 18.20, 23.00, -0.15, 0.20, 2.60, 3.80) # Dintel

    # Ventanal apaisado con reja negra
    add_box(bm_ventanas, 18.20, 23.00, -0.12, 0.12, 0.90, 2.60)
    for i in range(int((23.00 - 18.20) / 0.18)):
        xb = 18.30 + i * 0.18
        add_box(bm_rejas, xb - 0.015, xb + 0.015, -0.22, -0.14, 0.85, 2.65)

    # Marquesina de canes de madera
    for i in range(9):
        xb = 17.50 + i * 0.75
        add_box(bm_vigas, xb - 0.08, xb + 0.08, -0.75, 0.40, 3.45, 3.60)

    # Estructura metálica vacía de letrero en azotea
    add_box(bm_rejas, 17.80, 23.40, -0.10, 0.00, 4.00, 5.20)

    # B. Cuerpo con Espadaña Misional Ondulada (X in [24.00, 32.50 m])
    add_box(bm_muro, 24.00, 30.50, -0.15, 0.20, 0.00, 3.80) # Muro base
    # Espadaña ondulada central
    add_box(bm_espadaña, 24.00, 31.00, -0.15, 0.15, 3.80, 4.25)
    add_box(bm_espadaña, 25.20, 29.80, -0.15, 0.15, 4.25, 4.85)
    add_box(bm_espadaña, 26.20, 28.80, -0.15, 0.15, 4.85, 5.20)

    # Ventana con reja colonial en X in [24.80, 27.50 m]
    add_box(bm_ventanas, 24.80, 27.50, -0.14, 0.14, 1.10, 2.40)
    add_box(bm_rejas, 24.75, 27.55, -0.26, -0.12, 1.05, 2.45) # Pecho de paloma

    # Porche en esquina ochavada con zaguán diáfano de doble arco (X in [30.50, 32.50 m], Y in [0.00, 2.20 m])
    # Arco frontal en Libertad
    add_box(bm_muro, 30.50, 32.30, -0.15, 0.15, 2.60, 3.80)
    add_box(bm_muro, 30.30, 30.60, -0.15, 0.15, 0.00, 2.60)
    add_box(bm_muro, 32.20, 32.50, -0.15, 0.15, 0.00, 2.60)
    # Arco lateral hacia el estacionamiento
    add_box(bm_muro, 32.35, 32.55, 0.00, 2.20, 2.60, 3.80)
    add_box(bm_muro, 32.35, 32.55, 2.00, 2.30, 0.00, 2.60)

    # Firme y vigas del porche interior
    add_box(bm_muro, 30.50, 32.40, 0.00, 2.20, 0.00, 0.06)
    for ib in range(3):
        yb = 0.55 + ib * 0.60
        add_box(bm_vigas, 30.55, 32.35, yb - 0.06, yb + 0.06, 2.65, 2.78)

    # Puerta interior de madera con herraje (Y = 2.20 m)
    add_box(bm_muro, 30.50, 32.30, 2.15, 2.35, 2.40, 3.80)
    add_box(bm_ventanas, 30.75, 32.05, 2.18, 2.28, 0.00, 2.35)

    # Linternilla de forja colonial en esquina exterior
    add_box(bm_rejas, 32.35, 32.50, -0.25, -0.12, 2.35, 2.75)
    add_box(bm_ventanas, 32.37, 32.48, -0.23, -0.14, 2.40, 2.65)

    # 2. ALA ESTE DEL ESTACIONAMIENTO (X = 32.50 m, Y in [0.00, 22.00 m])
    add_box(bm_muro, 32.35, 32.55, 2.20, 22.00, 0.00, 3.80) # Muro corrido

    for i in range(3):
        yw1 = 4.20 + i * 4.40
        yw2 = yw1 + 2.00
        ymid = (yw1 + yw2) * 0.5
        add_box(bm_ventanas, 32.36, 32.56, yw1, yw2, 1.15, 2.35)
        add_box(bm_rejas, 32.54, 32.70, yw1, yw2, 1.15, 2.35) # Pecho de paloma
        add_box(bm_vigas, 32.20, 32.80, ymid - 0.09, ymid + 0.09, 3.45, 3.60) # Can de madera

    # Copete en esquina con frontón curvo en Y in [18.00, 22.00 m]
    add_box(bm_espadaña, 32.35, 32.65, 18.00, 22.00, 3.80, 4.45)
    add_box(bm_ventanas, 32.36, 32.58, 18.80, 20.40, 0.00, 2.30) # Puerta servicio

    # 3. GRAN CUERPO SUR ENVOLVENTE (X in [32.50, 72.00 m], Y in [20.00, 36.00 m])
    # Edificación masiva de 2 niveles (H = 6.80 m) que abraza el fondo sur del patio
    add_box(bm_muro, 32.50, 72.00, 20.00, 36.00, -1.50, 0.00) # Zócalo enterrado
    # Muro frontal hacia el patio del estacionamiento (Y = 20.00 m)
    add_box(bm_muro, 32.50, 72.00, 19.80, 20.20, 0.00, 3.80) # Nivel PB
    add_box(bm_muro, 32.50, 72.00, 19.80, 20.20, 3.80, 6.80) # Nivel PA
    # Muro posterior sur de cierre
    add_box(bm_muro, 32.50, 72.00, 35.80, 36.20, 0.00, 6.80)
    add_box(bm_muro, 71.80, 72.20, 20.00, 36.00, 0.00, 6.80) # Muro poniente de cierre

    # Vanos y ventanales de Planta Alta con acentos interiores verde esmeralda
    bm_salones = bmesh.new()
    for isal in range(6):
        xs1 = 34.50 + isal * 6.00
        xs2 = xs1 + 3.80
        add_box(bm_ventanas, xs1, xs2, 19.75, 20.25, 4.30, 5.90)
        # Acabado interior verde esmeralda visible
        add_box(bm_salones, xs1 + 0.10, xs2 - 0.10, 20.25, 22.00, 4.30, 6.20)

    # Tiro de chimenea de ladrillo refractario con sombrerete piramidal en azotea
    add_box(bm_muro, 40.00, 42.50, 26.00, 28.50, 6.80, 8.60)
    add_box(bm_rejas, 39.80, 42.70, 25.80, 28.70, 8.60, 9.00) # Sombrero

    obj_parr_m = create_mesh_object("LaParrilla_Muros_Terracota", bm_muro, mats["parrilla_terracota"], col)
    obj_parr_e = create_mesh_object("LaParrilla_Espadaña_Misional", bm_espadaña, mats["parrilla_terracota"], col)
    obj_parr_v = create_mesh_object("LaParrilla_Vigas_Canes", bm_vigas, mats["parrilla_madera_vigas"], col)
    obj_parr_win = create_mesh_object("LaParrilla_Ventanas_Madera", bm_ventanas, mats["parrilla_madera_vigas"], col)
    obj_parr_rej = create_mesh_object("LaParrilla_Rejas_Hierro", bm_rejas, mats["parrilla_reja_negra"], col)
    obj_sal_m = create_mesh_object("LaParrilla_Salones_Verde", bm_salones, mats["parrilla_verde_interior"], col)
    objects.extend([obj_parr_m, obj_parr_e, obj_parr_v, obj_parr_win, obj_parr_rej, obj_sal_m])

    # 4. RÓTULOS EN RELIEVE 3D DE LA PARRILLA
    t_parr1 = add_3d_text("LaParrilla_Txt_Nombre", "La Parrilla", 0.58, 0.04, (28.20, -0.15, 4.45), rot_north, mats["parrilla_rojo_letras"], col)
    t_parr2 = add_3d_text("LaParrilla_Txt_Sub", "Restaurant  Bar  &  Grill", 0.22, 0.02, (28.20, -0.15, 4.05), rot_north, mats["herreria_negra"], col)

    bm_adt = bmesh.new()
    add_box(bm_adt, 30.60, 31.00, -0.16, -0.14, 2.90, 3.30)
    obj_adt = create_mesh_object("LaParrilla_Placa_ADT", bm_adt, mats["adt_azul"], col)
    objects.extend([t_parr1, t_parr2, obj_adt])

    t_parr_lat = add_3d_text("LaParrilla_Txt_Lateral", "La Parrilla\nBar & Grill", 0.28, 0.03, (32.68, 20.00, 4.15), rot_west, mats["parrilla_rojo_letras"], col)
    objects.append(t_parr_lat)

    return objects

# ---------------------------------------------------------------------------
# 7. Explanada de Estacionamiento y Barda Poniente
# ---------------------------------------------------------------------------

def build_parking_and_grounds(mats, col):
    """Construye el patio interior de estacionamiento confinado entre La Parrilla y la barda poniente."""
    objects = []
    rot_west = (math.radians(90.0), 0.0, math.radians(90.0))

    # Explanada de estacionamiento: firme confinado (X in [32.50, 72.00 m], Y in [0.00, 20.00 m])
    bm_asf = bmesh.new()
    add_box(bm_asf, 32.50, 72.00, 0.00, 20.00, -0.05, 0.00)
    obj_asf = create_mesh_object("Estacionamiento_Pavimento_Asfalto", bm_asf, mats["asfalto_estacionamiento"], col)
    objects.append(obj_asf)

    # Barda Poniente de La Tradición (X = 72.00 m, Y in [0.00, 20.00 m])
    bm_barda = bmesh.new()
    add_box(bm_barda, 71.85, 72.15, 0.00, 20.00, 0.00, 2.40)
    add_box(bm_barda, 71.80, 72.20, 0.00, 20.00, 2.35, 2.48) # Moldura ochavada superior
    # Portón en arco blanco hacia predio contiguo
    add_box(bm_barda, 71.80, 72.20, 16.00, 19.50, 2.40, 3.40)
    obj_brd = create_mesh_object("Estacionamiento_Barda_Tradicion", bm_barda, mats["barda_tradicion_blanca"], col)
    objects.append(obj_brd)

    # Rótulo comercial histórico en barda: 'La Tradición / ESTACIONAMIENTO EXCLUSIVO'
    t_trad1 = add_3d_text("Tradicion_Txt_Nombre", "La Tradición", 0.32, 0.02, (71.78, 10.00, 1.85), rot_west, mats["brisa_azul"], col)
    t_trad2 = add_3d_text("Tradicion_Txt_Sub", "ESTACIONAMIENTO\nEXCLUSIVO", 0.22, 0.02, (71.78, 10.00, 1.35), rot_west, mats["calavera_negro"], col)
    objects.extend([t_trad1, t_trad2])

    return objects

# ---------------------------------------------------------------------------
# 8. Configuración de Cámaras de Validación Closed-Loop
# ---------------------------------------------------------------------------

def setup_cameras_and_render(col):
    """Configura iluminación ambiental diurna y 8 cámaras técnicas en Blender Cycles CPU."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    if hasattr(scene.cycles, 'device'):
        scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720

    world = bpy.data.worlds.new("World_Tecate_Day")
    scene.world = world
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs['Color'].default_value = (0.82, 0.88, 0.96, 1.0)
        bg_node.inputs['Strength'].default_value = 1.35

    light_data = bpy.data.lights.new(name="Sun_Diurno_Tecate", type='SUN')
    light_data.energy = 4.2
    light_data.color = (1.0, 0.98, 0.92)
    light_obj = bpy.data.objects.new("Sun_Diurno_Tecate", light_data)
    light_obj.rotation_euler = (math.radians(48.0), math.radians(16.0), math.radians(-38.0))
    col.objects.link(light_obj)

    fill_data = bpy.data.lights.new(name="Sun_Fill_Sur", type='SUN')
    fill_data.energy = 2.0
    fill_data.color = (0.92, 0.95, 1.0)
    fill_obj = bpy.data.objects.new("Sun_Fill_Sur", fill_data)
    fill_obj.rotation_euler = (math.radians(-35.0), math.radians(10.0), math.radians(140.0))
    col.objects.link(fill_obj)

    # 8 Cámaras técnicas calibradas
    cam_configs = [
        ("Cam_Cardenas_Norte_45", (-20.0, -8.0, 5.8), (6.0, 14.0, 3.5), 30.0),
        ("Cam_Cardenas_Centro", (-28.0, 35.1, 4.5), (0.0, 35.1, 3.5), 32.0),
        ("Cam_Cardenas_Sur_45", (-20.0, 78.0, 5.8), (6.0, 56.0, 3.5), 30.0),
        ("Cam_Libertad_Norte", (7.0, -18.0, 3.8), (7.0, 0.0, 3.0), 28.0),
        ("Cam_Hidalgo_Sur", (5.6, 88.0, 3.8), (5.6, 70.2, 3.0), 28.0),
        ("Cam_Parrilla_Libertad", (26.0, -18.0, 4.0), (26.0, 0.0, 3.2), 28.0),
        ("Cam_Estacionamiento_Reverso", (52.0, 6.0, 5.5), (28.0, 16.0, 3.0), 26.0),
        ("Cam_Cenital_Top", (28.0, 35.1, 100.0), (28.0, 35.1, 0.0), 24.0),
    ]

    cams = {}
    for name, pos, tgt, lens in cam_configs:
        c_data = bpy.data.cameras.new(name)
        c_data.lens = lens
        c_obj = bpy.data.objects.new(name, c_data)
        col.objects.link(c_obj)
        c_obj.location = Vector(pos)
        direction = Vector(tgt) - Vector(pos)
        c_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        cams[name] = c_obj

    return cams

def execute_validation_renders(cams):
    """Ejecuta el renderizado headless de las 8 cámaras y guarda los PNGs."""
    scene = bpy.context.scene
    os.makedirs(RENDERS_DIR, exist_ok=True)
    for cam_name, cam_obj in cams.items():
        scene.camera = cam_obj
        out_path = os.path.join(RENDERS_DIR, f"{cam_name}.png")
        scene.render.filepath = out_path
        print(f"Renderizando cámara de validación: {cam_name} -> {out_path}")
        bpy.ops.render.render(write_still=True)

# ---------------------------------------------------------------------------
# 9. Generación Programática de Escena Godot 4 (.tscn)
# ---------------------------------------------------------------------------

def generate_godot_scene(tscn_path, glb_path):
    """Genera la escena .tscn con física analítica 1:1, transitable y sin barreras invisibles."""
    rel_glb = "res://assets/buildings/edificio_cardenas_25.glb"
    bay_count = 13
    total_y = 70.20
    bay_w = total_y / bay_count # 5.40 m

    tscn_content = f"""[gd_scene load_steps=22 format=3 uid="uid://cardenas_25_complejo_001"]

[ext_resource type="PackedScene" path="{rel_glb}" id="1_mesh"]

[sub_resource type="BoxShape3D" id="BoxShape3D_pilastra"]
size = Vector3(0.60, 3.40, 0.60)

[sub_resource type="BoxShape3D" id="BoxShape3D_muro_local"]
size = Vector3(0.30, 3.40, 5.20)

[sub_resource type="BoxShape3D" id="BoxShape3D_escalon"]
size = Vector3(0.28, 0.188, 3.80)

[sub_resource type="BoxShape3D" id="BoxShape3D_terraza_piso"]
size = Vector3(2.40, 0.20, 70.20)

[sub_resource type="BoxShape3D" id="BoxShape3D_barandal_frontal"]
size = Vector3(0.06, 0.95, 70.20)

[sub_resource type="BoxShape3D" id="BoxShape3D_balcon_norte"]
size = Vector3(14.20, 0.20, 1.20)

[sub_resource type="BoxShape3D" id="BoxShape3D_barandal_norte"]
size = Vector3(14.20, 0.95, 0.06)

[sub_resource type="BoxShape3D" id="BoxShape3D_barandal_sur"]
size = Vector3(2.40, 0.95, 0.06)

[sub_resource type="BoxShape3D" id="BoxShape3D_muro_pa"]
size = Vector3(0.30, 3.20, 70.20)

[sub_resource type="BoxShape3D" id="BoxShape3D_muro_norte_pb"]
size = Vector3(14.20, 3.40, 0.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_muro_sur_pb"]
size = Vector3(11.20, 3.40, 0.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_muro_trasero"]
size = Vector3(0.30, 6.40, 70.20)

[sub_resource type="BoxShape3D" id="BoxShape3D_parrilla_norte"]
size = Vector3(15.30, 4.20, 0.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_parrilla_ala_este"]
size = Vector3(0.30, 3.80, 22.00)

[sub_resource type="BoxShape3D" id="BoxShape3D_parrilla_cuerpo_sur"]
size = Vector3(39.50, 6.80, 16.00)

[sub_resource type="BoxShape3D" id="BoxShape3D_barda_tradicion"]
size = Vector3(0.30, 2.40, 20.00)

[node name="Edificio_Cardenas_25" type="StaticBody3D"]

[node name="ModelInstance" parent="." instance=ExtResource("1_mesh")]

# 1. 14 Pilastras Frontales Analíticas Independientes (Galería Porticada Transitable)
"""
    for i in range(bay_count + 1):
        yc = i * bay_w
        tscn_content += f"""[node name="Col_Pilar_{i:02d}" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.30, 1.70, {-yc:.3f})
shape = SubResource("BoxShape3D_pilastra")

"""

    tscn_content += """# 2. Cancelerías de Locales Retranqueadas (Vano 6 libre para Escalera Central)
"""
    for i in range(bay_count):
        if i == 6:
            continue # Vano diáfano para la escalera
        yc_mid = (i + 0.5) * bay_w
        tscn_content += f"""[node name="Col_Local_{i:02d}" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.45, 1.70, {-yc_mid:.3f})
shape = SubResource("BoxShape3D_muro_local")

"""

    tscn_content += """# 3. 18 Escalones Analíticos Transitables de Escalera Central (Arco 7)
"""
    step_count = 18
    step_h = 3.40 / step_count
    step_d = 2.40 / step_count
    y_esc_mid = 6.5 * bay_w
    for s in range(step_count):
        x_step = 2.40 + (s + 0.5) * step_d
        z_step = (s + 0.5) * step_h
        tscn_content += f"""[node name="Col_Escalon_{s:02d}" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {x_step:.3f}, {z_step:.3f}, {-y_esc_mid:.3f})
shape = SubResource("BoxShape3D_escalon")

"""

    tscn_content += f"""# 4. Terraza y Balcones Abiertos de Planta Alta (Cero Cierres Transversales)
[node name="Col_Piso_Terraza" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.20, 3.40, -35.10)
shape = SubResource("BoxShape3D_terraza_piso")

[node name="Col_Barandal_Frontal" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.00, 3.90, -35.10)
shape = SubResource("BoxShape3D_barandal_frontal")

[node name="Col_Balcon_Norte" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 7.10, 3.40, 0.60)
shape = SubResource("BoxShape3D_balcon_norte")

[node name="Col_Barandal_Norte" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 7.10, 3.90, 1.20)
shape = SubResource("BoxShape3D_barandal_norte")

[node name="Col_Barandal_Sur" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.20, 3.90, -70.20)
shape = SubResource("BoxShape3D_barandal_sur")

[node name="Col_Muro_PA" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.45, 4.90, -35.10)
shape = SubResource("BoxShape3D_muro_pa")

# 5. Muros Perimetrales PB y Cierre Posterior Continuo
[node name="Col_Muro_Norte_PB" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 7.10, 1.70, 0.00)
shape = SubResource("BoxShape3D_muro_norte_pb")

[node name="Col_Muro_Sur_PB" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 5.60, 1.70, -70.20)
shape = SubResource("BoxShape3D_muro_sur_pb")

[node name="Col_Muro_Trasero_Cierre" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 11.20, 3.20, -35.10)
shape = SubResource("BoxShape3D_muro_trasero")

# 6. La Parrilla Restaurant (Estructura Envolvente)
[node name="Col_Parrilla_Norte" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 24.85, 2.10, 0.00)
shape = SubResource("BoxShape3D_parrilla_norte")

[node name="Col_Parrilla_Ala_Este" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 32.50, 1.90, -11.00)
shape = SubResource("BoxShape3D_parrilla_ala_este")

[node name="Col_Parrilla_Cuerpo_Sur" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 52.25, 3.40, -28.00)
shape = SubResource("BoxShape3D_parrilla_cuerpo_sur")

# 7. Barda Poniente de La Tradición
[node name="Col_Barda_Tradicion" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 72.00, 1.20, -10.00)
shape = SubResource("BoxShape3D_barda_tradicion")
"""

    os.makedirs(os.path.dirname(tscn_path), exist_ok=True)
    with open(tscn_path, "w", encoding="utf-8") as f:
        f.write(tscn_content)
    print(f"Escena Godot .tscn generada con éxito: {tscn_path}")

# ---------------------------------------------------------------------------
# 10. Función Principal de Orquestación
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("INICIANDO RECONSTRUCCIÓN PROCEDURAL V3.0 GROUND-TRUTH: CÁRDENAS 25")
    print("=" * 70)

    root_col = clean_scene()
    mats = create_materials()

    # 1. Cuerpos arquitectónicos principales
    print("-> 1. Generando Fachada Frontal Cárdenas (13 Arcos, 14 Pilastras, L=70.20 m)...")
    objs_front = build_front_cardenas(mats, root_col)

    print("-> 2. Generando Fachada Norte Callejón Libertad (ATM Santander, Balcón Corrido, 3 Arcos)...")
    objs_north = build_north_libertad_facade(mats, root_col)

    print("-> 3. Generando Fachada Sur Av. Miguel Hidalgo (2 Ventanales PA, Escaparates Brisa, Farol)...")
    objs_south = build_south_hidalgo_facade(mats, root_col)

    print("-> 4. Generando Muro Posterior Continuo de Cierre (X=11.20 m, Cero Huecos)...")
    objs_rear = build_rear_facade(mats, root_col)

    print("-> 5. Generando La Parrilla (Estructura Envolvente en 'L'/'U' con Salones de 2 Niveles)...")
    objs_parrilla = build_la_parrilla_complete(mats, root_col)

    print("-> 6. Generando Explanada de Estacionamiento y Barda Poniente La Tradición...")
    objs_parking = build_parking_and_grounds(mats, root_col)

    total_objs = len(objs_front) + len(objs_north) + len(objs_south) + len(objs_rear) + len(objs_parrilla) + len(objs_parking)
    print(f"Total de objetos arquitectónicos generados: {total_objs}")

    # 2. Guardar archivo maestro Blender (.blend)
    os.makedirs(os.path.dirname(BLEND_OUT), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
    print(f"Archivo maestro guardado: {BLEND_OUT}")

    # 3. Exportar modelo de producción GLB (excluyendo cámaras y luces)
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

    # 4. Generar escena Godot 4 (.tscn) con física analítica transitable
    generate_godot_scene(TSCN_OUT, GLB_OUT)

    # 5. Configurar cámaras y ejecutar renders diurnos de validación
    print("-> Configurando suite de 8 cámaras técnicas y renderizando...")
    cams = setup_cameras_and_render(root_col)
    execute_validation_renders(cams)

    print("=" * 70)
    print("PROCESO PROCEDURAL V3.0 FINALIZADO EXITOSAMENTE")
    print("=" * 70)

if __name__ == "__main__":
    main()
