"""
=============================================================================
GENERADOR PROCEDURAL 3D: COMPLEJO COMERCIAL PDTE. LÁZARO CÁRDENAS 25
(ÉPOCA: HISTÓRICO 2009 - VERSIÓN DE PRODUCCIÓN FOTORREALISTA V5.0 GROUND-TRUTH)
=============================================================================
Inmueble continuo Neocolonial / Colonial Californiano en Tecate, B.C.:
  - Fachada Este (Cárdenas): 13 arcos frontales continuos y 14 pilastras de laja (Longitud calibrada 67.60 m).
  - Entablamento / arquitrabe continuo sobre arcos con capiteles moldurados de conexión.
  - Galería porticada transitable en Planta Baja (X in [0.00, 2.20 m]).
  - Cancelerías retranqueadas y locales históricos de 2009:
      Santander (1-4), La Michoacana (5-6), Escalera Central Transitable (7),
      Casa Musical Tecate (8), Óptica San Martín (9), Clínicas (10-11),
      Telas y Novedades Vero (12), Regalos Brisa (13).
  - Planta Alta: Balcón corrido con barandales de forja negra conectados a 90° en esquina norte,
    viguería maestra sobre postes metálicos y canes tallados que sustentan la techumbre de tejas curvas.
  - Fachada Norte (Libertad):
      - Portal peatonal de esquina 100% diáfano y transitable.
      - 3 arcos sobre muro Santander: 2 ciegos con zócalo de laja dorada rehundido y el 3.er arco
        albergando el Cajero Automático Santander (ATM) con cancelería oscura, puertas dobles,
        rótulo vertical rojo y puerta de servicio contigua.
      - 3 grandes ventanales superiores en arco, balcón volado con ménsulas y panel de La Salamandra.
      - Cierre testero perpendicular hermético en X = 14.50 m (cero pestañas abiertas).
  - Fachada Sur (Hidalgo):
      - Portal transitable abierto hacia Hidalgo en PB con pilar esquinero masivo de laja.
      - Muro sur de Regalos Brisa con 2 arcos de medio punto con dovelas de ladrillo en relieve,
        tímpanos macizos estucados cerrados (cero huecos negros), escaparates con maniquíes volumétricos,
        machón de esquina sellado, farol colonial, banco de medidores CFE, y en PA 2 grandes ventanales
        con rótulo 'Seguridad Comercial Tecate'.
  - La Parrilla Restaurant Bar & Grill: Estructura envolvente en 'L' que ABRAZA el estacionamiento:
      - Frente norte en Libertad con espadaña misional curvilínea y porche ochavado.
      - Ala este con 3 ventanas rústicas con tejadillos de teja y losa de azotea hermética continua.
      - Cuerpo sur aporticado con vanos calados que revelan muros interiores turquesas, chimenea anclada.
  - Explanada de estacionamiento: Firme confinado con barda poniente de La Tradición y rótulos orientados
    correctamente hacia el patio (rot_barda_tradicion = Euler(90°, -90°, 0°)).
  - Shaders PBR nativos con coordenadas UV en todas las mallas para compatibilidad plena glTF 2.0 y Godot 4.
  - Física analítica 1:1 en Godot 4 (.tscn) con cero barreras invisibles.
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
# 1. Utilidades de Geometría Procedural y Mapeo UV
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

def auto_uv_bmesh(bm, scale_u=0.5, scale_v=0.5):
    """Genera coordenadas UV ortogonales (triplanar) en TEXCOORD_0 para exportación glTF PBR."""
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

    # Tapas laterales en y_start y y_end para evitar huecos en los extremos
    v_s_bl = bm.verts.new((x_min, y_start, z_spring))
    v_s_tl = bm.verts.new((x_min, y_start, z_top))
    v_s_tr = bm.verts.new((x_max, y_start, z_top))
    v_s_br = bm.verts.new((x_max, y_start, z_spring))
    bm.faces.new((v_s_bl, v_s_tl, v_s_tr, v_s_br))

    v_e_bl = bm.verts.new((x_min, y_end, z_spring))
    v_e_tl = bm.verts.new((x_min, y_end, z_top))
    v_e_tr = bm.verts.new((x_max, y_end, z_top))
    v_e_br = bm.verts.new((x_max, y_end, z_spring))
    bm.faces.new((v_e_bl, v_e_br, v_e_tr, v_e_tl))

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

    # Tapas laterales en x_start y x_end
    v_sx_bl = bm.verts.new((x_start, y_min, z_spring))
    v_sx_tl = bm.verts.new((x_start, y_min, z_top))
    v_sx_tr = bm.verts.new((x_start, y_max, z_top))
    v_sx_br = bm.verts.new((x_start, y_max, z_spring))
    bm.faces.new((v_sx_bl, v_sx_br, v_sx_tr, v_sx_tl))

    v_ex_bl = bm.verts.new((x_end, y_min, z_spring))
    v_ex_tl = bm.verts.new((x_end, y_min, z_top))
    v_ex_tr = bm.verts.new((x_end, y_max, z_top))
    v_ex_br = bm.verts.new((x_end, y_max, z_spring))
    bm.faces.new((v_ex_bl, v_ex_tl, v_ex_tr, v_ex_br))

def add_sloped_roof_hip(bm, x_eave, x_ridge, y_start, y_end, z_eave, z_ridge, hip_y_start=None, hip_y_end=None):
    """Construye un plano inclinado de cubierta con remate de limaoya (hip)."""
    y0_eave = y_start if hip_y_start is None else hip_y_start
    y1_eave = y_end if hip_y_end is None else hip_y_end
    y0_ridge = y_start + (x_ridge - x_eave) if hip_y_start is not None else y_start
    y1_ridge = y_end - (x_ridge - x_eave) if hip_y_end is not None else y_end

    v_eave_l = bm.verts.new((x_eave, y0_eave, z_eave))
    v_eave_r = bm.verts.new((x_eave, y1_eave, z_eave))
    v_ridge_r = bm.verts.new((x_ridge, y1_ridge, z_ridge))
    v_ridge_l = bm.verts.new((x_ridge, y0_ridge, z_ridge))

    bm.faces.new((v_eave_l, v_eave_r, v_ridge_r, v_ridge_l))

    # Cierre inferior de plafón machihembrado
    v_soff_l = bm.verts.new((x_eave, y0_eave, z_eave - 0.14))
    v_soff_r = bm.verts.new((x_eave, y1_eave, z_eave - 0.14))
    v_soff_rr = bm.verts.new((x_ridge, y1_ridge, z_ridge - 0.14))
    v_soff_rl = bm.verts.new((x_ridge, y0_ridge, z_ridge - 0.14))

    bm.faces.new((v_soff_l, v_soff_rl, v_soff_rr, v_soff_r))
    bm.faces.new((v_eave_l, v_soff_l, v_soff_r, v_eave_r))

def add_sloped_roof_hip_end(bm, x_eave_front, x_ridge, y_eave_end, y_ridge_hip, z_eave, z_ridge, is_north=True):
    """Construye el faldón inclinado de cierre testero (hip end) en Norte o Sur."""
    v_corner_front = bm.verts.new((x_eave_front, y_eave_end, z_eave))
    v_ridge = bm.verts.new((x_ridge, y_ridge_hip, z_ridge))
    v_corner_back = bm.verts.new((x_ridge, y_eave_end, z_eave))

    if is_north:
        bm.faces.new((v_corner_front, v_corner_back, v_ridge))
    else:
        bm.faces.new((v_corner_front, v_ridge, v_corner_back))

    v_soff_front = bm.verts.new((x_eave_front, y_eave_end, z_eave - 0.14))
    v_soff_ridge = bm.verts.new((x_ridge, y_ridge_hip, z_ridge - 0.14))
    v_soff_back = bm.verts.new((x_ridge, y_eave_end, z_eave - 0.14))

    if is_north:
        bm.faces.new((v_soff_front, v_soff_ridge, v_soff_back))
        bm.faces.new((v_corner_front, v_soff_front, v_soff_back, v_corner_back))
    else:
        bm.faces.new((v_soff_front, v_soff_back, v_soff_ridge))
        bm.faces.new((v_corner_front, v_corner_back, v_soff_back, v_soff_front))

def add_teja_ribs(bm, x_eave, x_ridge, y_start, y_end, z_eave, z_ridge, spacing=0.45, hip_y_start=None, hip_y_end=None):
    """Genera hiladas longitudinales de teja colonial con volumen curvo recortadas en las limaoyas."""
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
        v0 = bm.verts.new((x_eave, yc - 0.10, z_eave + 0.05))
        v1 = bm.verts.new((x_eave, yc + 0.10, z_eave + 0.05))
        v2 = bm.verts.new((xr, yc + 0.10, zr + 0.05))
        v3 = bm.verts.new((xr, yc - 0.10, zr + 0.05))
        v_top0 = bm.verts.new((x_eave, yc, z_eave + 0.11))
        v_top1 = bm.verts.new((xr, yc, zr + 0.11))

        bm.faces.new((v0, v1, v_top0))
        bm.faces.new((v1, v2, v_top1, v_top0))
        bm.faces.new((v2, v3, v_top1))
        bm.faces.new((v3, v0, v_top0, v_top1))

def add_sloped_roof_hip_x(bm, x_start, x_end, y_eave, y_ridge, z_eave, z_ridge, hip_x_start=None, hip_x_end=None):
    """Construye un plano inclinado de cubierta a lo largo del eje X con remates de limaoya (hip)."""
    delta_y = abs(y_ridge - y_eave)
    x0_eave = x_start
    x1_eave = x_end
    x0_ridge = x_start + delta_y if hip_x_start is not None else x_start
    x1_ridge = x_end - delta_y if hip_x_end is not None else x_end

    v_eave_l = bm.verts.new((x0_eave, y_eave, z_eave))
    v_eave_r = bm.verts.new((x1_eave, y_eave, z_eave))
    v_ridge_r = bm.verts.new((x1_ridge, y_ridge, z_ridge))
    v_ridge_l = bm.verts.new((x0_ridge, y_ridge, z_ridge))

    bm.faces.new((v_eave_l, v_eave_r, v_ridge_r, v_ridge_l))

    # Cierre inferior de plafón machihembrado
    v_soff_l = bm.verts.new((x0_eave, y_eave, z_eave - 0.14))
    v_soff_r = bm.verts.new((x1_eave, y_eave, z_eave - 0.14))
    v_soff_rr = bm.verts.new((x1_ridge, y_ridge, z_ridge - 0.14))
    v_soff_rl = bm.verts.new((x0_ridge, y_ridge, z_ridge - 0.14))

    bm.faces.new((v_soff_l, v_soff_rl, v_soff_rr, v_soff_r))
    bm.faces.new((v_eave_l, v_soff_l, v_soff_r, v_eave_r))

    # Hip end en el extremo poniente si aplica
    if hip_x_end is not None:
        v_corner_back = bm.verts.new((x1_eave, y_ridge, z_eave))
        bm.faces.new((v_eave_r, v_ridge_r, v_corner_back))
        v_soff_cb = bm.verts.new((x1_eave, y_ridge, z_eave - 0.14))
        bm.faces.new((v_soff_r, v_soff_cb, v_soff_rr))
        bm.faces.new((v_eave_r, v_corner_back, v_soff_cb, v_soff_r))

def add_teja_ribs_x(bm, x_start, x_end, y_eave, y_ridge, z_eave, z_ridge, spacing=0.45, hip_x_start=None, hip_x_end=None):
    """Genera hiladas de teja colonial a lo largo del eje X recortadas en las limaoyas."""
    num_ribs = int((x_end - x_start) / spacing)
    delta_y = abs(y_ridge - y_eave)
    for i in range(num_ribs):
        xc = x_start + i * spacing
        yr = y_ridge
        if hip_x_start is not None and xc < x_start + delta_y:
            yr = y_eave + max(0.15, xc - x_start) if y_eave < y_ridge else y_eave - max(0.15, xc - x_start)
        elif hip_x_end is not None and xc > x_end - delta_y:
            yr = y_ridge - max(0.15, x_end - xc) if y_eave < y_ridge else y_ridge + max(0.15, x_end - xc)

        if abs(yr - y_eave) <= 0.20:
            continue

        zr = z_eave + (z_ridge - z_eave) * (abs(yr - y_eave) / delta_y)
        v0 = bm.verts.new((xc - 0.10, y_eave, z_eave + 0.05))
        v1 = bm.verts.new((xc + 0.10, y_eave, z_eave + 0.05))
        v2 = bm.verts.new((xc + 0.10, yr, zr + 0.05))
        v3 = bm.verts.new((xc - 0.10, yr, zr + 0.05))
        v_top0 = bm.verts.new((xc, y_eave, z_eave + 0.11))
        v_top1 = bm.verts.new((xc, yr, zr + 0.11))

        bm.faces.new((v0, v1, v_top0))
        bm.faces.new((v1, v2, v_top1, v_top0))
        bm.faces.new((v2, v3, v_top1))
        bm.faces.new((v3, v0, v_top0, v_top1))

def create_mesh_object(name, bm, material, col, uv_scale=0.5):
    """Aplica UVs ortogonales, convierte BMesh en Mesh, asigna material y vincula a la colección."""
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
# 2. Materiales PBR Calibrados con UV Compatibles con glTF 2.0 y Godot 4
# ---------------------------------------------------------------------------

def make_pbr(name, base_color, roughness=0.85, metallic=0.0, alpha=1.0, tex_prefix=None, use_tex_albedo=True):
    """Crea un material Principled BSDF calibrado usando TEXCOORD_0 para compatibilidad plena con glTF."""
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
    mats = {}
    mats["estuco_ocre"] = make_pbr("M_Estuco_Ocre_Colonial", (0.84, 0.79, 0.70), roughness=0.88, tex_prefix="hotel_tecate_stucco", use_tex_albedo=False)
    mats["pilastra_laja"] = make_pbr("M_Piedra_Laja_Pilastras", (0.75, 0.62, 0.45), roughness=0.90, tex_prefix="kiosko_laja")
    mats["ladrillo_dovelas"] = make_pbr("M_Ladrillo_Dovelas_Arcos", (0.55, 0.28, 0.20), roughness=0.85, tex_prefix="kiosko_ladrillo")
    mats["piso_terracota"] = make_pbr("M_Piso_Terracota_Portal", (0.68, 0.26, 0.18), roughness=0.70)
    mats["teja_colonial"] = make_pbr("M_Teja_Colonial_Cubierta", (0.58, 0.22, 0.14), roughness=0.80, tex_prefix="kiosko_teja")
    mats["madera_canes"] = make_pbr("M_Madera_Canes_Alero", (0.24, 0.15, 0.10), roughness=0.65)
    mats["herreria_negra"] = make_pbr("M_Herreria_Negra_Forja", (0.05, 0.05, 0.05), roughness=0.40, metallic=0.85)
    mats["zocalo_basal"] = make_pbr("M_Zocalo_Basal_Enterrado", (0.12, 0.13, 0.14), roughness=0.95)
    mats["concreto_losa"] = make_pbr("M_Concreto_Fascia_Terraza", (0.86, 0.84, 0.80), roughness=0.60)
    mats["vidrio_comercial"] = make_pbr("M_Vidrio_Comercial", (0.82, 0.88, 0.92), roughness=0.08, alpha=0.35)
    mats["vidrio_oscuro"] = make_pbr("M_Vidrio_Oscuro_ATM", (0.10, 0.11, 0.13), roughness=0.10, alpha=0.90)
    mats["aluminio_negro"] = make_pbr("M_Aluminio_Negro_Canceles", (0.08, 0.08, 0.08), roughness=0.30, metallic=0.85)
    mats["aluminio_blanco"] = make_pbr("M_Aluminio_Blanco", (0.95, 0.95, 0.95), roughness=0.25, metallic=0.50)
    mats["persianas_blancas"] = make_pbr("M_Persianas_Verticales", (0.92, 0.92, 0.92), roughness=0.60)
    mats["azotea_asfalto"] = make_pbr("M_Azotea_Asfalto", (0.20, 0.20, 0.22), roughness=0.92)
    mats["muro_posterior_cardenas"] = make_pbr("M_Muro_Posterior_Cardenas", (0.80, 0.76, 0.68), roughness=0.88)
    mats["puerta_servicio_gris"] = make_pbr("M_Puerta_Servicio_Gris", (0.45, 0.47, 0.50), roughness=0.40, metallic=0.6)
    # Complementos ATM y servicio
    mats["atm_pantalla"] = make_pbr("M_ATM_Pantalla", (0.05, 0.40, 0.70), roughness=0.15)
    mats["atm_acero"] = make_pbr("M_ATM_Acero_Inox", (0.78, 0.80, 0.82), roughness=0.20, metallic=0.90)
    mats["puerta_crema"] = make_pbr("M_Puerta_Servicio_Crema", (0.88, 0.86, 0.80), roughness=0.50)

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
    mats["parrilla_verde_interior"] = make_pbr("M_Parrilla_Verde_Interior", (0.11, 0.37, 0.35), roughness=0.85)
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
    """Construye las 13 crujías frontales sobre Pdte. Lázaro Cárdenas con entablamento y capiteles."""
    objects = []
    bay_count = 13
    total_y = 67.60
    bay_w = total_y / bay_count # 5.20 m
    pilar_w = 0.65
    pilar_d = 0.65
    rot_cardenas = (math.radians(90.0), 0.0, math.radians(-90.0))

    # A. ZÓCALO BASAL ENTERRADO (-1.50 a 0.00 m)
    bm_zocalo = bmesh.new()
    add_box(bm_zocalo, -0.40, 11.40, -0.40, total_y + 0.40, -1.50, 0.00)
    obj_zocalo = create_mesh_object("Cardenas_Zocalo_Basal_Enterrado", bm_zocalo, mats["zocalo_basal"], col)
    objects.append(obj_zocalo)

    # B. 14 PILASTRAS DE MAMPOSTERÍA DE LAJA DORADA CON CAPITELES MOLDURADOS
    bm_pil = bmesh.new()
    for i in range(bay_count + 1):
        yc = i * bay_w
        y1 = max(0.00, yc - pilar_w * 0.5)
        y2 = min(total_y, yc + pilar_w * 0.5)
        # Fuste de laja
        add_box(bm_pil, -0.02, pilar_d + 0.02, y1 - 0.02, y2 + 0.02, 0.00, 1.40)
        # Moldura de transición
        add_box(bm_pil, -0.04, pilar_d + 0.04, y1 - 0.04, y2 + 0.04, 1.40, 1.48)
        # Fuste superior estucado
        add_box(bm_pil, 0.00, pilar_d, y1, y2, 1.48, 2.45)
        # CAPITEL TOXANO / ÁBACO DE ARRANQUE QUE CONECTA CON DOVELAS Y ENTABLAMENTO
        add_box(bm_pil, -0.06, pilar_d + 0.06, y1 - 0.06, y2 + 0.06, 2.45, 2.58)
    obj_pil = create_mesh_object("Cardenas_14_Pilastras_Laja", bm_pil, mats["pilastra_laja"], col, uv_scale=0.8)
    objects.append(obj_pil)

    # C. 13 ARCOS REBAJADOS CON DOVELAS DE LADRILLO EN RELIEVE REAL Y ENJUTAS (Z in [2.50, 3.55 m])
    bm_arcos = bmesh.new()
    bm_dovelas = bmesh.new()
    bm_entablamento = bmesh.new()

    for i in range(bay_count):
        y_start = i * bay_w + pilar_w * 0.5
        y_end = (i + 1) * bay_w - pilar_w * 0.5
        add_arch_spandrel(bm_arcos, 0.00, pilar_d, y_start, y_end, 2.50, 3.30, 3.55, segments=16)
        # Rosca de dovelas de ladrillo con resalte volumétrico de 5 cm hacia la calle
        add_arch_spandrel(bm_dovelas, -0.05, 0.00, y_start, y_end, 2.50, 3.30, 3.48, segments=16)

    # SELLADO MACIZO DE MAMPOSTERÍA SOBRE CADA PILASTRA (ELIMINA EL HUECO ENTRE ARCOS)
    for i in range(bay_count + 1):
        yc = i * bay_w
        y1 = max(0.00, yc - pilar_w * 0.5)
        y2 = min(total_y, yc + pilar_w * 0.5)
        # Muro macizo estucado que une las enjutas a ambos lados sobre la pilastra
        add_box(bm_arcos, 0.00, pilar_d, y1, y2, 2.50, 3.65)
        # Franja de resalte de dovelas de ladrillo en la coronación de la pilastra
        add_box(bm_dovelas, -0.05, 0.00, y1, y2, 2.50, 2.65)

    # ENTABLAMENTO / ARQUITRABE CONTINUO QUE VINCULA PILASTRAS Y ARCOS CON LA LOSA DEL BALCÓN
    add_box(bm_entablamento, -0.08, pilar_d + 0.05, 0.00, total_y, 3.45, 3.65)
    # Cornisa de coronación bajo balcón
    add_box(bm_entablamento, -0.10, pilar_d + 0.06, 0.00, total_y, 3.58, 3.65)

    obj_arcos = create_mesh_object("Cardenas_13_Arcos_Enjutas", bm_arcos, mats["estuco_ocre"], col)
    obj_dov = create_mesh_object("Cardenas_13_Arcos_DovelasLadrillo", bm_dovelas, mats["ladrillo_dovelas"], col, uv_scale=1.2)
    obj_ent = create_mesh_object("Cardenas_Entablamento_Arquitrabe", bm_entablamento, mats["concreto_losa"], col)
    objects.extend([obj_arcos, obj_dov, obj_ent])

    # D. GALERÍA PORTICADA: FIRME DE TERRACOTA Y CIELO / VIGUERÍA DE TECHO (X in [0.00, 2.20 m])
    bm_piso = bmesh.new()
    add_box(bm_piso, 0.00, 2.20, 0.00, total_y, 0.00, 0.06)
    obj_piso = create_mesh_object("Cardenas_Portal_Piso_Terracota", bm_piso, mats["piso_terracota"], col, uv_scale=1.5)
    objects.append(obj_piso)

    bm_cielo = bmesh.new()
    # Plafón cerrado continuo bajo el balcón (elimina huecos vistos desde abajo)
    add_box(bm_cielo, pilar_d, 2.20, 0.00, total_y, 3.45, 3.55)
    # Vigas transversales de madera bajo el portal
    for i in range(bay_count + 1):
        yc = i * bay_w
        add_box(bm_cielo, pilar_d - 0.02, 2.18, yc - 0.10, yc + 0.10, 3.32, 3.48)
    obj_cie = create_mesh_object("Cardenas_Portal_Cielo_Vigas", bm_cielo, mats["madera_canes"], col)
    objects.append(obj_cie)

    # E. CANCELERÍAS RETRANQUEADAS Y FACHADA COMERCIAL INTERIOR (X = 2.20 m)
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
            step_h = 3.60 / step_count
            step_d = 2.20 / step_count
            for s in range(step_count):
                x_s1 = 2.20 + s * step_d
                x_s2 = 2.20 + (s + 1) * step_d
                z_s = (s + 1) * step_h
                add_box(bm_esc, x_s1, x_s2, y_bay1 + 0.60, y_bay2 - 0.60, 0.00, z_s)
            obj_esc = create_mesh_object("Cardenas_Escalera_Central_Peldaños", bm_esc, mats["concreto_losa"], col)
            objects.append(obj_esc)
            continue

        # Muro base y cancelería comercial en X = 2.20 m
        add_box(bm_canceles, 2.15, 2.28, y_bay1, y_bay2, 0.00, 0.40)
        add_box(bm_canceles, 2.15, 2.28, y_bay1, y_bay2, 3.20, 3.65) # Dintel
        add_box(bm_canceles, 2.15, 2.28, y_bay1, y_bay1 + 0.40, 0.40, 3.20)
        add_box(bm_canceles, 2.15, 2.28, y_bay2 - 0.40, y_bay2, 0.40, 3.20)

        add_box(bm_canceles, 2.16, 2.26, y_mid - 0.05, y_mid + 0.05, 0.40, 3.20)
        add_box(bm_canceles, 2.16, 2.26, y_bay1 + 0.40, y_bay2 - 0.40, 2.15, 2.22)

        add_box(bm_vidrio, 2.18, 2.22, y_bay1 + 0.45, y_mid - 0.06, 0.45, 3.15)
        add_box(bm_vidrio, 2.18, 2.22, y_mid + 0.06, y_bay2 - 0.45, 0.45, 3.15)

        if i in [0, 1, 2, 3]:
            add_box(bm_persianas, 2.23, 2.25, y_bay1 + 0.50, y_mid - 0.10, 0.50, 3.10)
            add_box(bm_persianas, 2.23, 2.25, y_mid + 0.10, y_bay2 - 0.50, 0.50, 3.10)

        if i == 7:
            add_box(bm_murales, 2.23, 2.26, y_mid - 1.20, y_mid + 1.20, 0.80, 2.60)

    obj_can = create_mesh_object("Cardenas_Canceles_PB", bm_canceles, mats["aluminio_blanco"], col)
    obj_vid = create_mesh_object("Cardenas_Vidrios_PB", bm_vidrio, mats["vidrio_comercial"], col)
    obj_per = create_mesh_object("Cardenas_Persianas_Santander", bm_persianas, mats["persianas_blancas"], col)
    obj_mur = create_mesh_object("Cardenas_Mural_Guitarra", bm_murales, mats["mural_guitarra"], col)
    objects.extend([obj_can, obj_vid, obj_per, obj_mur])

    # F. RÓTULOS COMERCIALES HISTÓRICOS DE PLANTA BAJA (2009)
    # Santander
    bm_sant = bmesh.new()
    add_box(bm_sant, -0.15, 0.12, 7.00, 13.80, 3.30, 3.90)
    obj_sant = create_mesh_object("Santander_Caja_Rojo", bm_sant, mats["santander_rojo"], col)
    objects.append(obj_sant)
    t_sant = add_3d_text("Santander_Txt", "Santander", 0.44, 0.03, (-0.18, 10.40, 3.60), rot_cardenas, mats["santander_blanco"], col)
    objects.append(t_sant)

    # La Michoacana
    bm_mich = bmesh.new()
    add_box(bm_mich, -0.10, 0.08, 21.50, 30.50, 3.30, 3.85)
    obj_mich = create_mesh_object("Michoacana_Panel_Fascia", bm_mich, mats["michoacana_blanco"], col)
    objects.append(obj_mich)
    t_m1 = add_3d_text("Michoacana_Txt_Paleteria", "LA MICHOACANA", 0.36, 0.03, (-0.12, 26.00, 3.65), rot_cardenas, mats["michoacana_rosa"], col)
    t_m2 = add_3d_text("Michoacana_Txt_Sub", "PALETERIA  Y  NEVERIA", 0.20, 0.02, (-0.12, 26.00, 3.42), rot_cardenas, mats["michoacana_azul"], col)
    objects.extend([t_m1, t_m2])

    # Casa Musical Tecate
    bm_mus = bmesh.new()
    add_box(bm_mus, -0.08, 0.06, 37.00, 41.00, 3.00, 3.45)
    obj_mus = create_mesh_object("CasaMusical_Panel", bm_mus, mats["casa_musical_amarillo"], col)
    objects.append(obj_mus)
    t_mus = add_3d_text("CasaMusical_Txt", "GUITARRAS\nCASA MUSICAL TECATE", 0.20, 0.025, (-0.10, 39.00, 3.22), rot_cardenas, mats["casa_musical_letras"], col)
    objects.append(t_mus)

    # Óptica San Martín
    bm_opt = bmesh.new()
    add_box(bm_opt, -0.40, 0.05, 43.00, 45.60, 3.25, 3.70)
    obj_opt = create_mesh_object("Optica_Caja_Bandera", bm_opt, mats["optica_blanco"], col)
    objects.append(obj_opt)
    t_opt = add_3d_text("Optica_Txt", "OPTICA\nSAN MARTIN", 0.18, 0.02, (-0.42, 44.30, 3.45), rot_cardenas, mats["optica_azul"], col)
    objects.append(t_opt)

    # Consultorios
    t_dent = add_3d_text("Dentista_Txt", "DENTISTA / GINECOLOGA", 0.20, 0.02, (2.16, 49.40, 3.15), rot_cardenas, mats["clinica_azul"], col)
    objects.append(t_dent)

    # Telas y Novedades Vero
    bm_vero = bmesh.new()
    add_box(bm_vero, -0.08, 0.06, 57.50, 62.00, 3.30, 3.85)
    obj_vero = create_mesh_object("TelasVero_Panel", bm_vero, mats["brisa_blanco"], col)
    objects.append(obj_vero)
    t_v1 = add_3d_text("TelasVero_Txt1", "TELAS Y NOVEDADES", 0.22, 0.02, (-0.10, 59.75, 3.65), rot_cardenas, mats["telas_vero_rojo"], col)
    t_v2 = add_3d_text("TelasVero_Txt2", "VERO", 0.32, 0.03, (-0.10, 59.75, 3.42), rot_cardenas, mats["telas_vero_celeste"], col)
    objects.extend([t_v1, t_v2])

    # Regalos Brisa
    bm_brisa = bmesh.new()
    add_box(bm_brisa, -0.12, 0.10, 62.80, 67.40, 3.30, 3.95)
    obj_brisa = create_mesh_object("RegalosBrisa_Panel", bm_brisa, mats["brisa_blanco"], col)
    objects.append(obj_brisa)
    t_b1 = add_3d_text("Brisa_Txt1", "REGALOS BRISA", 0.36, 0.03, (-0.14, 65.10, 3.70), rot_cardenas, mats["brisa_azul"], col)
    t_b2 = add_3d_text("Brisa_Txt2", "ROPA DE BAUTIZO • RECUERDOS • RAMOS • PRIMERA COMUNION", 0.12, 0.015, (-0.14, 65.10, 3.45), rot_cardenas, mats["brisa_azul"], col)
    objects.extend([t_b1, t_b2])

    # G. PLANTA ALTA: TERRAZA TRANSITABLE Y VENTANALES (Z in [3.60, 6.45 m])
    bm_terraza = bmesh.new()
    add_box(bm_terraza, 0.00, 2.20, 0.00, total_y, 3.55, 3.65)
    add_box(bm_terraza, -0.08, 0.02, 0.00, total_y, 3.50, 3.68)
    obj_ter = create_mesh_object("Cardenas_Terraza_Piso", bm_terraza, mats["concreto_losa"], col)
    objects.append(obj_ter)

    bm_barandal = bmesh.new()
    add_box(bm_barandal, -0.03, 0.03, 0.00, total_y, 4.55, 4.60)
    add_box(bm_barandal, -0.02, 0.02, 0.00, total_y, 3.68, 3.72)
    for i in range(int(total_y / 0.15)):
        y_bar = i * 0.15
        add_box(bm_barandal, -0.012, 0.012, y_bar - 0.012, y_bar + 0.012, 3.70, 4.55)
    obj_bar = create_mesh_object("Cardenas_Barandal_Terraza", bm_barandal, mats["herreria_negra"], col)
    objects.append(obj_bar)

    # Muro y Ventanales en Arco de Planta Alta (X = 2.20 m)
    bm_muro_pa = bmesh.new()
    bm_vidrio_pa = bmesh.new()
    bm_arcos_pa = bmesh.new()

    for i in range(bay_count):
        y_bay1 = i * bay_w
        y_bay2 = (i + 1) * bay_w
        y_mid = (y_bay1 + y_bay2) * 0.5
        w_van = 3.40
        y_v1 = y_mid - w_van * 0.5
        y_v2 = y_mid + w_van * 0.5

        add_box(bm_muro_pa, 2.15, 2.30, y_bay1, y_v1, 3.65, 6.45)
        add_box(bm_muro_pa, 2.15, 2.30, y_v2, y_bay2, 3.65, 6.45)
        add_box(bm_muro_pa, 2.15, 2.30, y_v1, y_v2, 3.65, 4.35)
        add_box(bm_muro_pa, 2.15, 2.30, y_v1, y_v2, 6.05, 6.45)

        add_box(bm_vidrio_pa, 2.18, 2.22, y_v1, y_v2, 4.35, 6.00)
        add_arch_spandrel(bm_arcos_pa, 2.14, 2.26, y_v1, y_v2, 5.30, 6.00, 6.15, segments=12)

    obj_mpa = create_mesh_object("Cardenas_Muros_PA", bm_muro_pa, mats["estuco_ocre"], col)
    obj_vpa = create_mesh_object("Cardenas_Vidrios_PA", bm_vidrio_pa, mats["vidrio_comercial"], col)
    obj_apa = create_mesh_object("Cardenas_Arcos_Ladrillo_PA", bm_arcos_pa, mats["ladrillo_dovelas"], col, uv_scale=1.2)
    objects.extend([obj_mpa, obj_vpa, obj_apa])

    # Rótulos en Planta Alta
    t_rent = add_3d_text("SeRenta_Txt", "SE RENTA\n654-79-88", 0.26, 0.02, (2.14, 7.80, 5.20), rot_cardenas, mats["telas_vero_rojo"], col)
    objects.append(t_rent)

    bm_sie1 = bmesh.new()
    add_box(bm_sie1, 2.13, 2.17, 11.20, 14.60, 4.80, 5.60)
    obj_sie1 = create_mesh_object("Siesa1_Panel", bm_sie1, mats["siesa_azul"], col)
    objects.append(obj_sie1)
    t_sie1 = add_3d_text("Siesa1_Txt", "GRUPO SIESA\nSOLICITA GUARDIAS", 0.20, 0.02, (2.12, 12.90, 5.20), rot_cardenas, mats["siesa_dorado"], col)
    objects.append(t_sie1)

    bm_sie2 = bmesh.new()
    add_box(bm_sie2, 2.13, 2.17, 16.40, 19.80, 4.80, 5.60)
    obj_sie2 = create_mesh_object("Siesa2_Panel", bm_sie2, mats["siesa_azul"], col)
    objects.append(obj_sie2)
    t_sie2 = add_3d_text("Siesa2_Txt", "GRUPO SIESA\nVIDEOPORTEROS / CCTV", 0.20, 0.02, (2.12, 18.10, 5.20), rot_cardenas, mats["siesa_dorado"], col)
    objects.append(t_sie2)

    bm_cal = bmesh.new()
    add_box(bm_cal, 2.13, 2.17, 58.20, 61.60, 4.80, 5.60)
    obj_cal = create_mesh_object("Calavera_Panel", bm_cal, mats["calavera_negro"], col)
    objects.append(obj_cal)
    t_cal = add_3d_text("Calavera_Txt", "CALAVERA\ntattoo studio", 0.24, 0.02, (2.12, 59.90, 5.20), rot_cardenas, mats["calavera_dorado"], col)
    objects.append(t_cal)

    # H. ESTRUCTURA PORTANTE DE PLANTA ALTA: COLUMNAS METÁLICAS, TRABE MAESTRA Y CANES
    bm_postes = bmesh.new()
    bm_trabe = bmesh.new()
    bm_canes = bmesh.new()
    bm_techo = bmesh.new()

    for i in range(bay_count + 1):
        yc = i * bay_w
        add_box(bm_postes, 0.02, 0.10, yc - 0.04, yc + 0.04, 3.65, 6.45)

    add_box(bm_trabe, 0.00, 0.12, 0.00, total_y, 6.35, 6.50)

    for i in range(int(total_y / 0.65)):
        yc = i * 0.65
        add_box(bm_canes, -0.70, 2.25, yc - 0.06, yc + 0.06, 6.32, 6.46)

    obj_pst = create_mesh_object("Cardenas_Postes_Terraza", bm_postes, mats["herreria_negra"], col)
    obj_trb = create_mesh_object("Cardenas_Trabe_Maestra_Madera", bm_trabe, mats["madera_canes"], col)
    obj_cns = create_mesh_object("Cardenas_Canes_Madera", bm_canes, mats["madera_canes"], col)
    objects.extend([obj_pst, obj_trb, obj_cns])

    add_sloped_roof_hip(bm_techo, -0.70, 2.30, -1.50, total_y + 0.70, 6.46, 7.45, hip_y_start=-1.50, hip_y_end=total_y + 0.70)
    add_teja_ribs(bm_techo, -0.70, 2.30, -1.50, total_y + 0.70, 6.46, 7.45, spacing=0.45, hip_y_start=-1.50, hip_y_end=total_y + 0.70)
    obj_tch = create_mesh_object("Cardenas_Techo_Tejas_Colonial", bm_techo, mats["teja_colonial"], col, uv_scale=1.5)
    objects.append(obj_tch)

    # Cubierta plana hermética de azotea principal
    bm_azot = bmesh.new()
    add_box(bm_azot, 2.20, 11.20, 0.00, total_y, 6.30, 6.45)
    add_box(bm_azot, 11.00, 11.35, 0.00, total_y, 6.45, 6.85)
    # Losa de azotea y pretiles para la crujía de Santander en Libertad (X in [11.20, 14.50 m])
    add_box(bm_azot, 11.20, 14.50, 0.00, 4.50, 6.30, 6.45)
    add_box(bm_azot, 14.35, 14.65, 0.00, 4.50, 6.45, 6.85)
    add_box(bm_azot, 11.20, 14.50, 4.35, 4.65, 6.45, 6.85)
    for tin_y in [10.0, 26.0, 42.0, 60.0]:
        add_box(bm_azot, 5.00, 6.40, tin_y - 0.70, tin_y + 0.70, 6.45, 7.95)
    obj_az = create_mesh_object("Cardenas_Azotea_Asfalto_Tinacos", bm_azot, mats["azotea_asfalto"], col)
    objects.append(obj_az)

    return objects

# ---------------------------------------------------------------------------
# 4. Construcción de Fachadas Norte (Libertad) y Sur (Hidalgo)
# ---------------------------------------------------------------------------

def build_north_libertad_facade(mats, col):
    """
    Construye la fachada norte sobre Callejón Libertad (V6.0 Ground-Truth):
      - CERO HUECOS LATERALES: Muros macizos continuos con enjutas selladas y machones completos.
      - Portal peatonal de esquina 100% abierto y transitable en PB (X in [0.65, 2.20 m]).
      - 2 arcos ciegos rehundidos con zócalo de laja dorada y paños estucados con pátina.
      - 3.er arco con CAJERO AUTOMÁTICO SANTANDER (ATM) 2009 fidedigno: cancelería negra,
        doble puerta de cristal ahumado, tiradores de acero inox, rótulo vertical, vestíbulo
        rehundido con cajero ATM tridimensional y puerta de servicio contigua acanalada.
      - PLANTA ALTA: 3 ventanales en arco sin huecos laterales, balcón corrido con barandales a 90°.
      - CUBIERTA VOLADA CONTINUA: Faldón de tejas coloniales que CUBRE LA TOTALIDAD DEL BALCÓN DE LIBERTAD
        (X in [-0.70, 14.80 m], Y in [-1.50, 0.50 m]) con postes de sustentación, trabe maestra y canes de madera.
      - Cierre testero perpendicular hermético en X = 14.50 m.
    """
    objects = []
    rot_north = (math.radians(90.0), 0.0, 0.0)

    bm_muro = bmesh.new()
    bm_ladrillo = bmesh.new()
    bm_atm_vid = bmesh.new()
    bm_atm_alu = bmesh.new()
    bm_atm_acero = bmesh.new()
    bm_sant_rojo = bmesh.new()
    bm_atm_scr = bmesh.new()
    bm_puer_crema = bmesh.new()
    bm_balcon = bmesh.new()
    bm_techo_n = bmesh.new()
    bm_postes_n = bmesh.new()
    bm_trabe_n = bmesh.new()
    bm_canes_n = bmesh.new()

    # 1. PLANTA BAJA (Callejón Libertad, Y = 0.00 m, Z in [0.00, 3.65 m])
    add_box(bm_muro, 2.20, 14.50, -0.15, 0.15, 0.00, 0.40)
    add_box(bm_muro, 0.00, 14.50, -0.15, 0.15, 3.30, 3.65)

    # A. Vano peatonal de esquina: X in [0.65, 2.20 m]
    add_arch_spandrel_x(bm_muro, -0.15, 0.15, 0.65, 2.20, 2.45, 3.25, 3.65, segments=10)

    # Pilar esquinero (X in [0.00, 0.65 m]):
    add_box(bm_muro, 0.00, 0.65, -0.18, 0.18, 0.00, 1.40) # Laja
    add_box(bm_muro, -0.02, 0.67, -0.20, 0.20, 1.40, 1.48) # Moldura
    add_box(bm_muro, 0.00, 0.65, -0.15, 0.15, 1.48, 3.65) # Estuco continuo

    # Machón de retorno vertical (conecta portal de esquina con arco 1):
    add_box(bm_muro, 2.20, 2.45, -0.15, 0.15, 0.00, 3.65)

    # Pilastras intermedias sólidas de piso a techo:
    for xp1, xp2 in [(5.60, 6.25), (9.65, 10.30), (13.85, 14.50)]:
        add_box(bm_muro, xp1, xp2, -0.18, 0.22, 0.00, 1.40) # Laja
        add_box(bm_muro, xp1 - 0.02, xp2 + 0.02, -0.20, 0.24, 1.40, 1.48) # Moldura
        add_box(bm_muro, xp1, xp2, -0.16, 0.20, 1.48, 2.45) # Fuste
        add_box(bm_muro, xp1 - 0.03, xp2 + 0.03, -0.19, 0.23, 2.45, 2.58) # Capitel
        add_box(bm_muro, xp1, xp2, -0.15, 0.15, 2.58, 3.65) # Mampostería hasta dintel

    # Arcos 1 y 2 (Ciegos con nichos rehundidos y tímpanos cerrados):
    for x1, x2 in [(2.45, 5.60), (6.25, 9.65)]:
        add_arch_spandrel_x(bm_ladrillo, -0.20, -0.14, x1, x2, 2.30, 3.05, 3.30, segments=14)
        add_box(bm_muro, x1, x2, -0.15, 0.15, 3.05, 3.65)
        add_box(bm_muro, x1, x2, -0.06, 0.15, 0.00, 3.05)
        add_box(bm_muro, x1, x2, -0.09, 0.15, 0.00, 0.95)

    # Arco 3 (Cajero Automático Santander - ATM, X in [10.30, 13.85 m]):
    add_arch_spandrel_x(bm_ladrillo, -0.20, -0.14, 10.30, 13.85, 2.30, 3.05, 3.30, segments=14)
    add_box(bm_muro, 10.30, 13.85, -0.15, 0.15, 2.45, 3.65)

    # Vestíbulo interior rehundido (X in [10.30, 12.65 m], Y in [-0.15, 0.75 m])
    add_box(bm_muro, 10.30, 12.65, -0.15, 0.75, 0.00, 0.05) # Suelo granito
    add_box(bm_muro, 10.30, 12.65, -0.15, 0.75, 2.40, 2.45) # Plafón
    add_box(bm_muro, 10.30, 12.65, 0.70, 0.75, 0.00, 2.45)  # Muro trasero
    add_box(bm_muro, 10.25, 10.30, -0.15, 0.75, 0.00, 2.45) # Muro lateral izq
    add_box(bm_muro, 12.65, 12.70, -0.15, 0.75, 0.00, 2.45) # Muro divisor der

    # Cancelería de aluminio anodizado negro y doble puerta en Y = -0.10 m
    add_box(bm_atm_alu, 10.30, 12.65, -0.13, -0.07, 0.00, 2.45) # Cerco exterior
    add_box(bm_atm_alu, 10.30, 12.65, -0.14, -0.06, 0.00, 0.12) # Zócalo
    add_box(bm_atm_alu, 10.30, 12.65, -0.14, -0.06, 2.32, 2.45) # Dintel
    add_box(bm_atm_alu, 11.45, 11.50, -0.14, -0.06, 0.12, 2.32) # Montante central

    # Doble puerta acristalada ahumada oscura
    add_box(bm_atm_vid, 10.35, 11.45, -0.11, -0.09, 0.12, 2.32)
    add_box(bm_atm_vid, 11.50, 12.60, -0.11, -0.09, 0.12, 2.32)

    # Tiradores tubulares verticales de acero inoxidable (60 cm)
    add_box(bm_atm_acero, 11.38, 11.42, -0.18, -0.14, 0.85, 1.45)
    add_box(bm_atm_acero, 11.53, 11.57, -0.18, -0.14, 0.85, 1.45)

    # Terminal ATM Santander en el interior del vestíbulo (empotrado en pared trasera en Y = 0.68 m)
    add_box(bm_muro, 10.70, 12.25, 0.45, 0.70, 0.00, 1.95) # Carcasa
    add_box(bm_sant_rojo, 10.75, 12.20, 0.42, 0.46, 0.55, 1.90) # Frontal rojo Santander
    add_box(bm_sant_rojo, 10.85, 12.10, 0.40, 0.44, 1.65, 1.85) # Marquesina luminosa
    add_box(bm_atm_scr, 11.10, 11.85, 0.40, 0.43, 1.25, 1.55)   # Pantalla interactiva
    add_box(bm_atm_acero, 11.15, 11.80, 0.35, 0.44, 1.02, 1.08) # Repisa teclado numérico
    add_box(bm_atm_acero, 11.20, 11.75, 0.40, 0.44, 0.82, 0.90) # Ranura de efectivo

    # Puerta de servicio contigua en X in [12.70, 13.85 m]
    add_box(bm_muro, 12.70, 13.85, -0.14, 0.02, 0.00, 2.35) # Marco de acero
    add_box(bm_puer_crema, 12.75, 13.80, -0.12, -0.04, 0.05, 2.30) # Hoja de puerta
    add_box(bm_atm_acero, 12.80, 12.85, -0.16, -0.11, 0.95, 1.05)  # Picaporte

    # 2. PLANTA ALTA: BALCÓN CORRIDO Y VENTANALES SIN HUECOS (Z in [3.65, 6.45 m])
    add_box(bm_muro, 0.00, 14.50, -0.15, 0.15, 3.65, 4.30)
    add_box(bm_muro, 0.00, 14.50, -0.15, 0.15, 6.10, 6.45)

    # Machones macizos verticales entre ventanas (SELLAN LOS HUECOS LATERALES)
    add_box(bm_muro, 0.00, 0.60, -0.15, 0.15, 4.30, 6.10)
    add_box(bm_muro, 4.00, 5.00, -0.15, 0.15, 4.30, 6.10)
    add_box(bm_muro, 8.40, 9.40, -0.15, 0.15, 4.30, 6.10)
    add_box(bm_muro, 12.80, 14.50, -0.15, 0.15, 4.30, 6.10)

    # 3 grandes ventanales en arco
    for x1, x2 in [(0.60, 4.00), (5.00, 8.40), (9.40, 12.80)]:
        add_arch_spandrel_x(bm_ladrillo, -0.16, -0.12, x1, x2, 5.20, 5.90, 6.10, segments=12)
        add_box(bm_muro, x1, x2, -0.15, 0.15, 5.80, 6.10) # Tímpano cerrado
        add_box(bm_atm_vid, x1 + 0.10, x2 - 0.10, -0.12, -0.08, 4.30, 5.80)
        xmid = (x1 + x2) * 0.5
        add_box(bm_muro, xmid - 0.04, xmid + 0.04, -0.14, -0.06, 4.30, 5.80)

    # Losa de piso en voladizo (X in [0.00, 14.50 m], Y in [-1.20, 0.00 m])
    add_box(bm_balcon, 0.00, 14.50, -1.20, 0.00, 3.55, 3.65)
    add_box(bm_balcon, 0.00, 14.50, -1.25, -1.18, 3.50, 3.68)
    add_box(bm_balcon, -0.08, 0.02, -1.25, 0.00, 3.50, 3.68)

    # Ménsulas estructurales de apoyo bajo el balcón
    for im in range(7):
        xm = 1.00 + im * 2.10
        add_box(bm_muro, xm - 0.12, xm + 0.12, -1.15, 0.10, 3.10, 3.55)

    # Barandal corrido de forja negra a lo largo de Libertad (Y = -1.20 m)
    add_box(bm_balcon, 0.00, 14.50, -1.22, -1.18, 4.55, 4.60)
    add_box(bm_balcon, 0.00, 14.50, -1.21, -1.19, 3.68, 3.72)
    for i in range(int(14.50 / 0.15)):
        xb = i * 0.15
        add_box(bm_balcon, xb - 0.012, xb + 0.012, -1.21, -1.19, 3.70, 4.55)

    # Unión a 90° de barandales en esquina norte
    add_box(bm_balcon, -0.02, 0.02, -1.20, 0.00, 4.55, 4.60)
    add_box(bm_balcon, -0.015, 0.015, -1.20, 0.00, 3.68, 3.72)
    for i in range(int(1.20 / 0.15)):
        yb = -i * 0.15
        add_box(bm_balcon, -0.012, 0.012, yb - 0.012, yb + 0.012, 3.70, 4.55)

    # Cierre perpendicular testero en X = 14.50 m
    add_box(bm_muro, 14.35, 14.65, -0.15, 4.50, 0.00, 6.45)
    add_box(bm_muro, 11.20, 14.50, 4.35, 4.65, 0.00, 6.45)

    # 3. CUBIERTA VOLADA CONTINUA DE TEJAS SOBRE TODO EL BALCÓN DE LIBERTAD
    # Postes de sustentación verticales en Y = -1.15 m
    for xp in [0.00, 4.65, 9.30, 14.50]:
        add_box(bm_postes_n, xp - 0.05, xp + 0.05, -1.18, -1.12, 3.65, 6.46)

    # Trabe maestra corrida en Y = -1.15 m
    add_box(bm_trabe_n, -0.70, 14.80, -1.20, -1.10, 6.35, 6.48)

    # Viguería transversal y canes de madera cada 0.65 m en X
    for i in range(int((14.80 - (-0.70)) / 0.65) + 1):
        xc = -0.70 + i * 0.65
        add_box(bm_canes_n, xc - 0.06, xc + 0.06, -1.50, 0.10, 6.32, 6.46)

    # Faldón inclinado de tejas que vuela 30 cm sobre el barandal (Y in [-1.50, 1.50 m])
    add_sloped_roof_hip_x(bm_techo_n, -0.70, 14.80, -1.50, 1.50, 6.46, 7.45, hip_x_start=-0.70, hip_x_end=14.80)
    add_teja_ribs_x(bm_techo_n, -0.70, 14.80, -1.50, 1.50, 6.46, 7.45, spacing=0.45, hip_x_start=-0.70, hip_x_end=14.80)

    # Hilada de caballete sobre la limatesa diagonal de encuentro noroeste
    for s in range(14):
        u = s / 13.0
        xh = -0.70 + u * (2.30 - (-0.70))
        yh = -1.50 + u * (1.50 - (-1.50))
        zh = 6.46 + u * (7.45 - 6.46) + 0.08
        add_box(bm_techo_n, xh - 0.16, xh + 0.16, yh - 0.16, yh + 0.16, zh, zh + 0.10)

    # Creación de objetos visuales y vinculación a colección
    obj_mn = create_mesh_object("Libertad_Muro_Norte", bm_muro, mats["estuco_ocre"], col)
    obj_ln = create_mesh_object("Libertad_Arcos_Ladrillo", bm_ladrillo, mats["ladrillo_dovelas"], col, uv_scale=1.2)
    obj_avid = create_mesh_object("Libertad_ATM_Vidrios", bm_atm_vid, mats["vidrio_oscuro"], col)
    obj_aalu = create_mesh_object("Libertad_ATM_Canceleria", bm_atm_alu, mats["aluminio_negro"], col)
    obj_aace = create_mesh_object("Libertad_ATM_Herrajes", bm_atm_acero, mats["atm_acero"], col)
    obj_snt = create_mesh_object("Libertad_ATM_Santander_Front", bm_sant_rojo, mats["santander_rojo"], col)
    obj_ascr = create_mesh_object("Libertad_ATM_Pantalla", bm_atm_scr, mats["atm_pantalla"], col)
    obj_apue = create_mesh_object("Libertad_Puerta_Servicio", bm_puer_crema, mats["puerta_crema"], col)
    obj_bal = create_mesh_object("Libertad_Balcon_Terraza_Corrida", bm_balcon, mats["herreria_negra"], col)
    obj_tn = create_mesh_object("Libertad_Techo_Tejas_Hip", bm_techo_n, mats["teja_colonial"], col, uv_scale=1.5)
    obj_pst_n = create_mesh_object("Libertad_Postes_Techo", bm_postes_n, mats["herreria_negra"], col)
    obj_trb_n = create_mesh_object("Libertad_Trabe_Madera", bm_trabe_n, mats["madera_canes"], col)
    obj_cns_n = create_mesh_object("Libertad_Canes_Madera", bm_canes_n, mats["madera_canes"], col)
    objects.extend([obj_mn, obj_ln, obj_avid, obj_aalu, obj_aace, obj_snt, obj_ascr, obj_apue, obj_bal, obj_tn, obj_pst_n, obj_trb_n, obj_cns_n])

    # Rótulos en relieve Santander y vertical CAJERO AUTOMATICO
    t_atm_sant = add_3d_text("Libertad_Txt_Santander_ATM", "Santander", 0.28, 0.025, (11.70, -0.19, 2.72), rot_north, mats["santander_rojo"], col)
    t_atm = add_3d_text("Libertad_Txt_Cajero", "CAJERO\nAUTOMATICO", 0.18, 0.02, (10.40, -0.20, 1.65), rot_north, mats["santander_blanco"], col)
    objects.extend([t_atm_sant, t_atm])

    # Letrero de Fraccionamiento La Salamandra colgado en el balcón
    bm_sal_b = bmesh.new()
    add_box(bm_sal_b, 1.20, 4.20, -1.24, -1.21, 3.85, 4.50)
    obj_sal_p = create_mesh_object("Libertad_Panel_Salamandra", bm_sal_b, mats["salamandra_amarillo"], col)
    objects.append(obj_sal_p)
    t_sal_b = add_3d_text("Libertad_Txt_Salamandra", "FRACCIONAMIENTO\nLA SALAMANDRA\nLOTES EN ABONOS", 0.16, 0.02, (2.70, -1.26, 4.18), rot_north, mats["salamandra_letras"], col)
    objects.append(t_sal_b)

    # Portón de servicio de reja gris (X in [14.50, 17.50 m])
    bm_reja = bmesh.new()
    add_box(bm_reja, 14.50, 17.50, -0.10, -0.05, 0.00, 2.40)
    for i in range(int(3.0 / 0.15)):
        xr = 14.50 + i * 0.15
        add_box(bm_reja, xr - 0.015, xr + 0.015, -0.11, -0.04, 0.00, 2.45)
    obj_rej = create_mesh_object("Libertad_Reja_Servicio", bm_reja, mats["puerta_servicio_gris"], col)
    objects.append(obj_rej)

    return objects

def build_south_hidalgo_facade(mats, col):
    """
    Construye la fachada sur sobre Av. Miguel Hidalgo:
      - CERO HUECOS: Tímpanos cerrados con mampostería estucada y machón de esquina sellado.
      - Portal peatonal abierto en PB hacia Hidalgo (X in [0.00, 2.20 m]).
      - 2 arcos con dovelas de ladrillo en relieve y escaparates de Regalos Brisa con maniquíes volumétricos.
      - 2 ventanales superiores en arco con rótulo 'Seguridad Comercial Tecate', farol colonial y medidores CFE.
    """
    objects = []
    total_y = 67.60
    rot_south = (math.radians(90.0), 0.0, math.radians(180.0))

    bm_muro_s = bmesh.new()
    bm_dov_s = bmesh.new()
    bm_vid_s = bmesh.new()
    bm_maniqui = bmesh.new()
    bm_med = bmesh.new()
    bm_farol = bmesh.new()
    bm_techo_s = bmesh.new()
    bm_balcon_s = bmesh.new()

    # 1. PLANTA BAJA (Regalos Brisa - X in [2.20, 11.20 m], Y = total_y)
    # Zócalo y dintel continuo
    add_box(bm_muro_s, 2.20, 11.20, total_y - 0.15, total_y + 0.15, 0.00, 0.40)
    add_box(bm_muro_s, 2.20, 11.20, total_y - 0.15, total_y + 0.15, 3.30, 3.65)

    # SELLADO DEL MACHÓN VERTICAL DE ESQUINA (elimina el hueco con el portal en X = 2.20 m)
    add_box(bm_muro_s, 2.15, 2.35, total_y - 0.65, total_y + 0.15, 0.00, 3.65)
    # Machones frontal sur
    add_box(bm_muro_s, 2.20, 2.60, total_y - 0.15, total_y + 0.15, 0.40, 3.30)
    add_box(bm_muro_s, 5.80, 6.40, total_y - 0.15, total_y + 0.15, 0.40, 3.30)
    add_box(bm_muro_s, 9.60, 11.20, total_y - 0.15, total_y + 0.15, 0.40, 3.30)

    # 2 amplios arcos con dovelas de ladrillo en relieve (5 cm) y escaparates de aluminio blanco
    # Escaparate 1: X in [2.60, 5.80 m]
    # Escaparate 2: X in [6.40, 9.60 m]
    for x1, x2 in [(2.60, 5.80), (6.40, 9.60)]:
        add_arch_spandrel_x(bm_dov_s, total_y + 0.15, total_y + 0.20, x1, x2, 2.30, 3.05, 3.30, segments=14)
        # SELLADO MACIZO DEL TÍMPANO SUPERIOR (elimina el hueco negro sobre la ventana)
        add_box(bm_muro_s, x1, x2, total_y - 0.10, total_y + 0.14, 2.50, 3.30)
        # Marco de aluminio blanco del escaparate
        add_box(bm_muro_s, x1, x2, total_y + 0.10, total_y + 0.14, 0.40, 0.45)
        add_box(bm_muro_s, x1, x2, total_y + 0.10, total_y + 0.14, 2.45, 2.52)
        # Vidrio transparente reflectante
        add_box(bm_vid_s, x1 + 0.05, x2 - 0.05, total_y + 0.11, total_y + 0.13, 0.45, 2.45)

    # Maniquíes volumétricos tridimensionales reales en el interior de los escaparates
    add_box(bm_maniqui, 3.20, 3.70, total_y - 0.40, total_y - 0.05, 0.45, 1.65)
    add_box(bm_maniqui, 4.40, 4.90, total_y - 0.40, total_y - 0.05, 0.45, 1.85)
    add_box(bm_maniqui, 7.00, 7.50, total_y - 0.40, total_y - 0.05, 0.45, 1.85)
    add_box(bm_maniqui, 8.20, 8.70, total_y - 0.40, total_y - 0.05, 0.45, 1.65)

    # Farol colonial de forja hexagonal en el machón central (X = 6.10 m)
    add_box(bm_farol, 6.02, 6.18, total_y + 0.15, total_y + 0.42, 2.30, 2.75)
    add_box(bm_farol, 6.04, 6.16, total_y + 0.20, total_y + 0.38, 2.35, 2.70)

    # Banco de medidores de CFE en el extremo poniente (X in [9.80, 10.80 m])
    add_box(bm_med, 9.80, 10.80, total_y + 0.15, total_y + 0.32, 0.60, 2.10)

    # 2. PLANTA ALTA: 2 GRANDES VENTANALES EN ARCO (SEGURIDAD COMERCIAL TECATE)
    add_box(bm_muro_s, 2.20, 11.20, total_y - 0.15, total_y + 0.15, 3.65, 4.30)
    add_box(bm_muro_s, 2.20, 11.20, total_y - 0.15, total_y + 0.15, 6.10, 6.45)
    # Machones macizos que sellan por completo los laterales de las ventanas en PA
    add_box(bm_muro_s, 2.20, 2.60, total_y - 0.15, total_y + 0.15, 4.30, 6.10) # Machón oriente sellado
    add_box(bm_muro_s, 5.80, 6.40, total_y - 0.15, total_y + 0.15, 4.30, 6.10) # Machón central
    add_box(bm_muro_s, 9.60, 11.20, total_y - 0.15, total_y + 0.15, 4.30, 6.10) # Machón poniente

    for x1, x2 in [(2.60, 5.80), (6.40, 9.60)]:
        add_arch_spandrel_x(bm_dov_s, total_y + 0.15, total_y + 0.20, x1, x2, 5.20, 5.95, 6.10, segments=12)
        add_box(bm_vid_s, x1 + 0.05, x2 - 0.05, total_y + 0.11, total_y + 0.14, 4.30, 5.90)
        xmid = (x1 + x2) * 0.5
        add_box(bm_muro_s, xmid - 0.03, xmid + 0.03, total_y + 0.10, total_y + 0.15, 4.30, 5.85)
        add_box(bm_muro_s, x1 + 0.05, x2 - 0.05, total_y + 0.10, total_y + 0.15, 5.05, 5.12)

    # 3. CIERRE DEL BALCÓN EN EL EXTREMO SUR (X in [0.00, 2.20 m], Y = total_y)
    add_box(bm_balcon_s, 0.00, 2.20, total_y - 0.05, total_y, 4.55, 4.60)
    add_box(bm_balcon_s, 0.00, 2.20, total_y - 0.04, total_y, 3.68, 3.72)
    for i in range(int(2.20 / 0.15)):
        xb = i * 0.15
        add_box(bm_balcon_s, xb - 0.012, xb + 0.012, total_y - 0.04, total_y - 0.01, 3.70, 4.55)

    # Hip return hermético de la cubierta de tejas sobre el frente sur
    add_sloped_roof_hip_end(bm_techo_s, -0.70, 2.30, total_y + 0.70, total_y + 0.70 - 3.00, 6.46, 7.45, is_north=False)

    obj_ms = create_mesh_object("Hidalgo_Muro_Sur", bm_muro_s, mats["estuco_ocre"], col)
    obj_ds = create_mesh_object("Hidalgo_Arcos_Ladrillo", bm_dov_s, mats["ladrillo_dovelas"], col, uv_scale=1.2)
    obj_vs = create_mesh_object("Hidalgo_Vidrios_Brisa", bm_vid_s, mats["vidrio_comercial"], col)
    obj_mq = create_mesh_object("Hidalgo_Maniquies_Gala", bm_maniqui, mats["vestido_blanco"], col)
    obj_far = create_mesh_object("Hidalgo_Farol_Colonial", bm_farol, mats["farol_metal"], col)
    obj_med = create_mesh_object("Hidalgo_Medidores_CFE", bm_med, mats["medidores_cfe"], col)
    obj_bs = create_mesh_object("Hidalgo_Balcon_Retorno", bm_balcon_s, mats["herreria_negra"], col)
    obj_ts = create_mesh_object("Hidalgo_Techo_Tejas_Hip", bm_techo_s, mats["teja_colonial"], col, uv_scale=1.5)
    objects.extend([obj_ms, obj_ds, obj_vs, obj_mq, obj_far, obj_med, obj_bs, obj_ts])

    t_seg = add_3d_text("Hidalgo_Txt_Seguridad", "SEGURIDAD COMERCIAL TECATE", 0.18, 0.02, (8.00, total_y + 0.18, 5.25), rot_south, mats["aluminio_blanco"], col)
    objects.append(t_seg)

    return objects

# ---------------------------------------------------------------------------
# 5. Muro Posterior Continuo de Cierre (X = 11.20 m)
# ---------------------------------------------------------------------------

def build_rear_facade(mats, col):
    """Construye el muro posterior continuo de cierre para erradicar totalmente la visión hueca."""
    objects = []
    total_y = 67.60

    bm_rear = bmesh.new()
    bm_puertas = bmesh.new()

    add_box(bm_rear, 11.10, 11.35, 0.00, total_y, -1.50, 6.85)

    for y_door in [9.50, 25.50, 39.00, 59.50]:
        add_box(bm_puertas, 11.34, 11.38, y_door - 0.50, y_door + 0.50, 0.00, 2.15)
        add_box(bm_rear, 11.33, 11.40, y_door - 0.55, y_door + 0.55, 2.15, 2.22)
        add_box(bm_rear, 11.33, 11.40, y_door - 0.58, y_door - 0.50, 0.00, 2.22)
        add_box(bm_rear, 11.33, 11.40, y_door + 0.50, y_door + 0.58, 0.00, 2.22)

    for y_pipe in [8.0, 25.0, 42.0, 59.0]:
        add_box(bm_rear, 11.34, 11.44, y_pipe - 0.06, y_pipe + 0.06, 0.00, 6.70)

    obj_rf = create_mesh_object("Cardenas_Muro_Posterior_Cierre", bm_rear, mats["muro_posterior_cardenas"], col)
    obj_puer = create_mesh_object("Cardenas_Puertas_Servicio_Posterior", bm_puertas, mats["puerta_servicio_gris"], col)
    objects.extend([obj_rf, obj_puer])

    return objects

# ---------------------------------------------------------------------------
# 6. La Parrilla Restaurant Bar & Grill (Estructura Envolvente en "L")
# ---------------------------------------------------------------------------

def build_la_parrilla_complete(mats, col):
    """
    Construye La Parrilla como estructura edificada continua y hermética que envuelve el estacionamiento:
      - CERO ENTRADAS HUECAS: Cerramiento perimetral macizo completo en Este (hasta Y=32), Sur (Y=32),
        Oeste (X=68) y Fachada Norte hacia el patio (Y=18).
      - Frente Norte sobre Callejón Libertad con espadaña misional, porche ochavado y zaguán.
      - Ala Este con 3 ventanas rústicas, rejas coloniales, tejadillos y cubierta hermética.
      - Gran Cuerpo Sur de 2 niveles completamente cerrado con ventanas, rejas, puertas y losas de azotea continuas.
      - Chimenea anclada sólidamente en azotea.
    """
    objects = []
    rot_north = (math.radians(90.0), 0.0, 0.0)
    rot_west_wall = (math.radians(90.0), 0.0, math.radians(90.0))

    bm_muro = bmesh.new()
    bm_espadaña = bmesh.new()
    bm_vigas = bmesh.new()
    bm_ventanas = bmesh.new()
    bm_rejas = bmesh.new()
    bm_salones = bmesh.new()
    bm_tejas_p = bmesh.new()

    # Zócalo basal enterrado de La Parrilla (-1.50 a 0.00 m)
    add_box(bm_muro, 17.50, 68.15, -0.20, 32.20, -1.50, 0.00)

    # -----------------------------------------------------------------------
    # 1. CUERPO NORTE (FRENTE A CALLEJÓN LIBERTAD, Y = 0.00 m)
    # -----------------------------------------------------------------------
    # Marquesina rústica izquierda (X in [17.50, 24.00 m])
    add_box(bm_muro, 17.50, 18.20, -0.15, 0.20, 0.00, 3.80)
    add_box(bm_muro, 23.00, 24.00, -0.15, 0.20, 0.00, 3.80)
    add_box(bm_muro, 18.20, 23.00, -0.15, 0.20, 0.00, 0.90)
    add_box(bm_muro, 18.20, 23.00, -0.15, 0.20, 2.60, 3.80)

    add_box(bm_ventanas, 18.20, 23.00, -0.12, 0.12, 0.90, 2.60)
    for i in range(int((23.00 - 18.20) / 0.18)):
        xb = 18.30 + i * 0.18
        add_box(bm_rejas, xb - 0.015, xb + 0.015, -0.22, -0.14, 0.85, 2.65)

    for i in range(9):
        xb = 17.60 + i * 0.75
        add_box(bm_vigas, xb - 0.08, xb + 0.08, -0.75, 0.40, 3.45, 3.60)

    add_box(bm_rejas, 17.80, 23.40, -0.10, 0.00, 4.00, 5.20)

    # Cuerpo con Espadaña Misional Ondulada (X in [24.00, 32.50 m])
    add_box(bm_muro, 24.00, 30.50, -0.15, 0.20, 0.00, 3.80)
    add_box(bm_espadaña, 24.00, 31.00, -0.15, 0.15, 3.80, 4.25)
    add_box(bm_espadaña, 25.20, 29.80, -0.15, 0.15, 4.25, 4.85)
    add_box(bm_espadaña, 26.20, 28.80, -0.15, 0.15, 4.85, 5.20)

    add_box(bm_ventanas, 24.80, 27.50, -0.14, 0.14, 1.10, 2.40)
    add_box(bm_rejas, 24.75, 27.55, -0.26, -0.12, 1.05, 2.45)

    # Porche en esquina ochavada con zaguán diáfano de doble arco (X in [30.50, 32.50 m], Y in [0.00, 2.20 m])
    add_box(bm_muro, 30.50, 32.30, -0.15, 0.15, 2.60, 3.80)
    add_box(bm_muro, 30.30, 30.60, -0.15, 0.15, 0.00, 2.60)
    add_box(bm_muro, 32.20, 32.50, -0.15, 0.15, 0.00, 2.60)
    add_box(bm_muro, 32.35, 32.55, 0.00, 2.20, 2.60, 3.80)
    add_box(bm_muro, 32.35, 32.55, 2.00, 2.30, 0.00, 2.60)

    add_box(bm_muro, 30.50, 32.40, 0.00, 2.20, 0.00, 0.06)
    for ib in range(3):
        yb = 0.55 + ib * 0.60
        add_box(bm_vigas, 30.55, 32.35, yb - 0.06, yb + 0.06, 2.65, 2.78)

    add_box(bm_muro, 30.50, 32.30, 2.15, 2.35, 2.40, 3.80)
    add_box(bm_ventanas, 30.75, 32.05, 2.18, 2.28, 0.00, 2.35)

    # -----------------------------------------------------------------------
    # 2. ALA ESTE DEL ESTACIONAMIENTO (X = 32.50 m, CONTINUA DE Y = 0 A 32 m)
    # -----------------------------------------------------------------------
    # Muro perimetral oriental continuo de piso a techo (SELLADO COMPLETO HASTA Y = 32.00 m)
    add_box(bm_muro, 32.35, 32.65, 2.20, 32.00, 0.00, 4.20)
    add_box(bm_muro, 32.35, 32.65, 18.00, 32.00, 4.20, 6.90)

    # Losa maciza de azotea del ala este
    add_box(bm_muro, 28.00, 32.65, 0.00, 18.00, 3.70, 3.85)
    add_box(bm_muro, 32.35, 32.65, 0.00, 18.00, 3.85, 4.30) # Pretil

    # 3 Ventanas coloniales rústicas hacia el patio
    for i in range(3):
        yw1 = 4.00 + i * 4.60
        yw2 = yw1 + 2.10
        ymid = (yw1 + yw2) * 0.5
        add_box(bm_ventanas, 32.36, 32.56, yw1, yw2, 1.10, 2.30)
        add_box(bm_rejas, 32.54, 32.68, yw1, yw2, 1.05, 2.35)
        add_box(bm_tejas_p, 32.52, 33.20, yw1 - 0.15, yw2 + 0.15, 2.40, 2.65)
        add_box(bm_vigas, 32.25, 33.15, ymid - 0.08, ymid + 0.08, 2.30, 2.42)

    add_box(bm_espadaña, 32.35, 32.65, 16.00, 18.00, 3.80, 4.45)

    # -----------------------------------------------------------------------
    # 3. GRAN CUERPO SUR ENVOLVENTE (X in [32.50, 68.00 m], Y in [18.00, 32.00 m])
    # -----------------------------------------------------------------------
    # A. Muro Frontal Norte hacia el Patio (Y = 18.00 m): Fachada de 2 niveles sólida y cerrada
    add_box(bm_muro, 32.35, 68.15, 17.85, 18.15, 0.00, 3.90) # Planta baja sólida
    add_box(bm_ventanas, 36.00, 38.50, 17.82, 18.18, 0.00, 2.40) # Puerta de acceso rústica
    add_box(bm_ventanas, 44.00, 47.00, 17.82, 18.18, 1.10, 2.30) # Ventana 1
    add_box(bm_rejas, 43.90, 47.10, 17.75, 17.85, 1.05, 2.35)
    add_box(bm_ventanas, 54.00, 57.00, 17.82, 18.18, 1.10, 2.30) # Ventana 2
    add_box(bm_rejas, 53.90, 57.10, 17.75, 17.85, 1.05, 2.35)

    # Planta Alta sólida de fachada norte (Y = 18.00 m, Z in [3.90, 6.90 m])
    add_box(bm_muro, 32.35, 68.15, 17.85, 18.15, 3.90, 6.90)
    for iwin in range(4):
        xw1 = 35.00 + iwin * 7.50
        xw2 = xw1 + 4.50
        # Carpintería y vidrios rústicos cerrados (cero huecos abiertos hacia el interior)
        add_box(bm_ventanas, xw1, xw2, 17.80, 18.20, 4.40, 6.20)
        add_box(bm_rejas, xw1 + 0.10, xw2 - 0.10, 17.74, 17.84, 4.35, 6.25)

    # B. Muro Sur Testero Continuo de Cerramiento (Y = 32.00 m, X in [32.35, 68.15 m])
    # SELLA POR COMPLETO EL REVERSO DE LA PARRILLA
    add_box(bm_muro, 32.35, 68.15, 31.85, 32.15, 0.00, 6.90)

    # C. Muro Poniente de Confinamiento (X = 68.00 m, Y in [18.00, 32.00 m])
    add_box(bm_muro, 67.85, 68.15, 18.00, 32.00, 0.00, 6.90)

    # D. Cubierta Hermética Continua de Azotea y Pretiles
    add_box(bm_muro, 32.35, 68.15, 18.00, 32.00, 6.70, 6.90) # Losa maciza
    add_box(bm_muro, 32.35, 68.15, 17.85, 18.15, 6.90, 7.40) # Pretil norte
    add_box(bm_muro, 32.35, 68.15, 31.85, 32.15, 6.90, 7.40) # Pretil sur
    add_box(bm_muro, 67.85, 68.15, 18.00, 32.00, 6.90, 7.40) # Pretil oeste
    add_box(bm_muro, 32.35, 32.65, 18.00, 32.00, 6.90, 7.40) # Pretil este

    # E. Chimenea anclada sólidamente en azotea
    add_box(bm_muro, 41.00, 43.20, 24.50, 26.70, 6.70, 8.50)
    add_box(bm_rejas, 40.80, 43.40, 24.30, 26.90, 8.50, 8.90)

    # Creación de objetos visuales
    obj_parr_m = create_mesh_object("LaParrilla_Muros_Terracota", bm_muro, mats["parrilla_terracota"], col)
    obj_parr_e = create_mesh_object("LaParrilla_Espadaña_Misional", bm_espadaña, mats["parrilla_terracota"], col)
    obj_parr_v = create_mesh_object("LaParrilla_Vigas_Canes", bm_vigas, mats["parrilla_madera_vigas"], col)
    obj_parr_win = create_mesh_object("LaParrilla_Ventanas_Madera", bm_ventanas, mats["parrilla_madera_vigas"], col)
    obj_parr_rej = create_mesh_object("LaParrilla_Rejas_Hierro", bm_rejas, mats["parrilla_reja_negra"], col)
    obj_parr_tej = create_mesh_object("LaParrilla_Tejadillos_Teja", bm_tejas_p, mats["teja_colonial"], col, uv_scale=1.5)
    objects.extend([obj_parr_m, obj_parr_e, obj_parr_v, obj_parr_win, obj_parr_rej, obj_parr_tej])

    # 4. RÓTULOS EN RELIEVE 3D DE LA PARRILLA
    t_parr1 = add_3d_text("LaParrilla_Txt_Nombre", "La Parrilla", 0.58, 0.04, (28.20, -0.15, 4.45), rot_north, mats["parrilla_rojo_letras"], col)
    t_parr2 = add_3d_text("LaParrilla_Txt_Sub", "Restaurant  Bar  &  Grill", 0.22, 0.02, (28.20, -0.15, 4.05), rot_north, mats["herreria_negra"], col)

    bm_adt = bmesh.new()
    add_box(bm_adt, 30.60, 31.00, -0.16, -0.14, 2.90, 3.30)
    obj_adt = create_mesh_object("LaParrilla_Placa_ADT", bm_adt, mats["adt_azul"], col)
    objects.extend([t_parr1, t_parr2, obj_adt])

    t_parr_lat = add_3d_text("LaParrilla_Txt_Lateral", "La Parrilla\nBar & Grill", 0.28, 0.03, (32.68, 18.00, 4.15), rot_west_wall, mats["parrilla_rojo_letras"], col)
    objects.append(t_parr_lat)

    return objects

def build_parking_and_grounds(mats, col):
    """Construye el patio interior de estacionamiento y barda poniente con texto orientado canónicamente."""
    objects = []
    # Orientación matemática canónica para texto en barda poniente vista desde el patio:
    # Local X -> (0, -1, 0), Local Y -> (0, 0, 1), Normal -> (-1, 0, 0)
    rot_barda_tradicion = (math.radians(90.0), 0.0, math.radians(-90.0))

    bm_asf = bmesh.new()
    add_box(bm_asf, 32.50, 68.00, 0.00, 18.00, -0.05, 0.00)
    obj_asf = create_mesh_object("Estacionamiento_Pavimento_Asfalto", bm_asf, mats["asfalto_estacionamiento"], col, uv_scale=0.5)
    objects.append(obj_asf)

    # Barda Poniente de La Tradición (X = 68.00 m, Y in [0.00, 18.00 m])
    bm_barda = bmesh.new()
    add_box(bm_barda, 67.85, 68.15, 0.00, 18.00, 0.00, 2.40)
    add_box(bm_barda, 67.80, 68.20, 0.00, 18.00, 2.35, 2.48)
    add_box(bm_barda, 67.80, 68.20, 14.50, 17.50, 2.40, 3.40)
    obj_brd = create_mesh_object("Estacionamiento_Barda_Tradicion", bm_barda, mats["barda_tradicion_blanca"], col)
    objects.append(obj_brd)

    # Rótulo comercial en barda orientado de forma impecable hacia el patio (resuelve Comentario 5)
    t_trad1 = add_3d_text("Tradicion_Txt_Nombre", "La Tradición", 0.32, 0.02, (67.75, 9.00, 1.85), rot_barda_tradicion, mats["brisa_azul"], col)
    t_trad2 = add_3d_text("Tradicion_Txt_Sub", "ESTACIONAMIENTO\nEXCLUSIVO", 0.22, 0.02, (67.75, 9.00, 1.35), rot_barda_tradicion, mats["calavera_negro"], col)
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

    # Luz puntual interior suave en el vestíbulo del cajero automático Santander
    atm_light_data = bpy.data.lights.new(name="ATM_Santander_Interior_Light", type='POINT')
    atm_light_data.energy = 85.0
    atm_light_data.color = (1.0, 0.95, 0.88)
    atm_light_data.shadow_soft_size = 0.20
    atm_light_obj = bpy.data.objects.new("ATM_Santander_Interior_Light", atm_light_data)
    atm_light_obj.location = (11.50, 0.40, 2.30)
    col.objects.link(atm_light_obj)

    # 10 Cámaras técnicas calibradas de validación pericial
    cam_configs = [
        ("Cam_Cardenas_Norte_45", (-20.0, -8.0, 5.8), (6.0, 14.0, 3.5), 30.0),
        ("Cam_Cardenas_Centro", (-28.0, 33.8, 4.5), (0.0, 33.8, 3.5), 32.0),
        ("Cam_Cardenas_Sur_45", (-20.0, 75.0, 5.8), (6.0, 54.0, 3.5), 30.0),
        ("Cam_Libertad_Norte", (7.0, -18.0, 3.8), (7.0, 0.0, 3.0), 28.0),
        ("Cam_Cajero_Santander", (11.5, -6.5, 1.75), (11.5, 0.0, 1.75), 35.0),
        ("Cam_Hidalgo_Sur", (5.6, 85.0, 3.8), (5.6, 67.6, 3.0), 28.0),
        ("Cam_Parrilla_Libertad", (26.0, -18.0, 4.0), (26.0, 0.0, 3.2), 28.0),
        ("Cam_Estacionamiento_Reverso", (50.0, 5.0, 5.5), (28.0, 15.0, 3.0), 26.0),
        ("Cam_Estacionamiento_Barda", (46.0, 9.0, 2.0), (68.0, 9.0, 1.8), 28.0),
        ("Cam_Cenital_Top", (28.0, 33.8, 95.0), (28.0, 33.8, 0.0), 24.0),
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
    total_y = 67.60
    bay_w = total_y / bay_count # 5.20 m

    tscn_content = f"""[gd_scene load_steps=22 format=3 uid="uid://cardenas_25_complejo_001"]

[ext_resource type="PackedScene" path="{rel_glb}" id="1_mesh"]

[sub_resource type="BoxShape3D" id="BoxShape3D_pilastra"]
size = Vector3(0.65, 3.60, 0.65)

[sub_resource type="BoxShape3D" id="BoxShape3D_muro_local"]
size = Vector3(0.30, 3.60, 5.00)

[sub_resource type="BoxShape3D" id="BoxShape3D_escalon"]
size = Vector3(0.28, 0.20, 3.80)

[sub_resource type="BoxShape3D" id="BoxShape3D_terraza_piso"]
size = Vector3(2.20, 0.20, 67.60)

[sub_resource type="BoxShape3D" id="BoxShape3D_barandal_frontal"]
size = Vector3(0.06, 0.95, 67.60)

[sub_resource type="BoxShape3D" id="BoxShape3D_balcon_norte"]
size = Vector3(14.50, 0.20, 1.20)

[sub_resource type="BoxShape3D" id="BoxShape3D_barandal_norte"]
size = Vector3(14.50, 0.95, 0.06)

[sub_resource type="BoxShape3D" id="BoxShape3D_barandal_sur"]
size = Vector3(2.20, 0.95, 0.06)

[sub_resource type="BoxShape3D" id="BoxShape3D_muro_pa"]
size = Vector3(0.30, 3.20, 67.60)

[sub_resource type="BoxShape3D" id="BoxShape3D_muro_norte_pb"]
size = Vector3(12.30, 3.60, 0.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_muro_sur_pb"]
size = Vector3(9.00, 3.60, 0.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_muro_trasero"]
size = Vector3(0.30, 6.80, 67.60)

[sub_resource type="BoxShape3D" id="BoxShape3D_parrilla_norte"]
size = Vector3(15.00, 4.20, 0.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_parrilla_muro_este"]
size = Vector3(0.30, 6.90, 32.00)

[sub_resource type="BoxShape3D" id="BoxShape3D_parrilla_muro_sur"]
size = Vector3(35.80, 6.90, 0.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_parrilla_muro_oeste"]
size = Vector3(0.30, 6.90, 14.00)

[sub_resource type="BoxShape3D" id="BoxShape3D_parrilla_muro_patio"]
size = Vector3(35.80, 6.90, 0.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_barda_tradicion"]
size = Vector3(0.30, 2.40, 18.00)

[node name="Edificio_Cardenas_25" type="StaticBody3D"]

[node name="ModelInstance" parent="." instance=ExtResource("1_mesh")]

# 1. 14 Pilastras Frontales Analíticas Independientes (Galería Porticada Transitable)
"""
    for i in range(bay_count + 1):
        yc = i * bay_w
        tscn_content += f"""[node name="Col_Pilar_{i:02d}" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.325, 1.80, {-yc:.3f})
shape = SubResource("BoxShape3D_pilastra")

"""

    tscn_content += """# 2. Cancelerías de Locales Retranqueadas (Vano 6 libre para Escalera Central)
"""
    for i in range(bay_count):
        if i == 6:
            continue
        yc_mid = (i + 0.5) * bay_w
        tscn_content += f"""[node name="Col_Local_{i:02d}" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.25, 1.80, {-yc_mid:.3f})
shape = SubResource("BoxShape3D_muro_local")

"""

    tscn_content += """# 3. 18 Escalones Analíticos Transitables de Escalera Central (Arco 7)
"""
    step_count = 18
    step_h = 3.60 / step_count
    step_d = 2.20 / step_count
    y_esc_mid = 6.5 * bay_w
    for s in range(step_count):
        x_step = 2.20 + (s + 0.5) * step_d
        z_step = (s + 0.5) * step_h
        tscn_content += f"""[node name="Col_Escalon_{s:02d}" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {x_step:.3f}, {z_step:.3f}, {-y_esc_mid:.3f})
shape = SubResource("BoxShape3D_escalon")

"""

    tscn_content += f"""# 4. Terraza y Balcones Abiertos de Planta Alta (Cero Cierres Transversales)
[node name="Col_Piso_Terraza" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.10, 3.60, -33.80)
shape = SubResource("BoxShape3D_terraza_piso")

[node name="Col_Barandal_Frontal" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.00, 4.10, -33.80)
shape = SubResource("BoxShape3D_barandal_frontal")

[node name="Col_Balcon_Norte" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 7.25, 3.60, 0.60)
shape = SubResource("BoxShape3D_balcon_norte")

[node name="Col_Barandal_Norte" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 7.25, 4.10, 1.20)
shape = SubResource("BoxShape3D_barandal_norte")

[node name="Col_Barandal_Sur" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.10, 4.10, -67.60)
shape = SubResource("BoxShape3D_barandal_sur")

[node name="Col_Muro_PA" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.25, 5.00, -33.80)
shape = SubResource("BoxShape3D_muro_pa")

# 5. Muros Perimetrales PB y Cierre Posterior Continuo
[node name="Col_Muro_Norte_PB" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 8.35, 1.80, 0.00)
shape = SubResource("BoxShape3D_muro_norte_pb")

[node name="Col_Muro_Sur_PB" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 6.70, 1.80, -67.60)
shape = SubResource("BoxShape3D_muro_sur_pb")

[node name="Col_Muro_Trasero_Cierre" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 11.20, 3.40, -33.80)
shape = SubResource("BoxShape3D_muro_trasero")

# 6. La Parrilla Restaurant (Cerramiento Perimetral Completo e Impenetrable)
[node name="Col_Parrilla_Norte" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 25.00, 2.10, 0.00)
shape = SubResource("BoxShape3D_parrilla_norte")

[node name="Col_Parrilla_Muro_Este" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 32.50, 3.45, -16.00)
shape = SubResource("BoxShape3D_parrilla_muro_este")

[node name="Col_Parrilla_Muro_Sur" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 50.25, 3.45, -32.00)
shape = SubResource("BoxShape3D_parrilla_muro_sur")

[node name="Col_Parrilla_Muro_Oeste" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 68.00, 3.45, -25.00)
shape = SubResource("BoxShape3D_parrilla_muro_oeste")

[node name="Col_Parrilla_Muro_Patio" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 50.25, 3.45, -18.00)
shape = SubResource("BoxShape3D_parrilla_muro_patio")

# 7. Barda Poniente de La Tradición
[node name="Col_Barda_Tradicion" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 68.00, 1.20, -9.00)
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
    print("INICIANDO RECONSTRUCCIÓN PROCEDURAL V5.0 GROUND-TRUTH: CÁRDENAS 25")
    print("=" * 70)

    root_col = clean_scene()
    mats = create_materials()

    # 1. Cuerpos arquitectónicos principales
    print("-> 1. Generando Fachada Frontal Cárdenas (13 Arcos, Entablamento, Capiteles, L=67.60 m)...")
    objs_front = build_front_cardenas(mats, root_col)

    print("-> 2. Generando Fachada Norte Callejón Libertad (ATM Santander, Portal Abierto, 3 Arcos, Cierre X=14.5m)...")
    objs_north = build_north_libertad_facade(mats, root_col)

    print("-> 3. Generando Fachada Sur Av. Miguel Hidalgo (Tímpanos Macizos Cerrados, Cero Huecos)...")
    objs_south = build_south_hidalgo_facade(mats, root_col)

    print("-> 4. Generando Muro Posterior Continuo de Cierre (X=11.20 m, Cero Huecos)...")
    objs_rear = build_rear_facade(mats, root_col)

    print("-> 5. Generando La Parrilla (Estructura Envolvente en 'L' con Azotea Hermética Sellada)...")
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
    print("PROCESO PROCEDURAL V5.0 FINALIZADO EXITOSAMENTE")
    print("=" * 70)

if __name__ == "__main__":
    main()
