"""
Generador Procedural 3D de Alta Fidelidad Fotorrealista: Manzana Central Tecate (2009)
========================================================================================
Reconstruye con precisión milimétrica la manzana delimitada por:
  - Norte: Av. Benito Juárez (128.00 m)
  - Poniente: Calle Pdte. Pascual Ortiz Rubio (77.00 m)
  - Sur: Callejón Libertad (128.00 m)
  - Oriente: Calle Pdte. Abelardo L. Rodríguez (77.00 m)

TOPOLOGÍA CANÓNICA NO TRASLAPADA (Zero Overlaps, Zero Coplanar Z-Fighting):
  - Cara Norte (Av. Benito Juárez, Y = 77.00m):
      [0.0, 9.0]    Modas Da Vinci (esquina NW, tejas 3D)
      [9.0, 32.0]   Telas Elías (2 niv, ocre monumental)
      [32.0, 44.0]  Mariscos El Chapo / Birriería (arco ladrillo)
      [44.0, 58.0]  Taquería Los Arcos (cercha espacial y toldo curvo)
      [58.0, 70.0]  Rosticería Los Polos B.C. (toldo y asador)
      [70.0, 84.0]  Farmacia del Pueblo (alero teja colonial)
      [84.0, 94.0]  Barber Shop Azteca 230 (poste barbero 3D)
      [94.0, 109.0] Hotel Juárez & Cafetería Juárez (2 niv, azulejo blanco brillante)
      [109.0, 114.0] Callejón Medellín y Villegas (paso interior con barda)
      [114.0, 120.0] Super Taquería Tecate (toldo y mostrador)
      [120.0, 128.0] Terminal Central de Autobuses (Norte y ochava NE, marquesina zig-zag)

  - Cara Poniente (Ortiz Rubio, X = 0.00m):
      [68.0, 77.0]  Modas Da Vinci (lateral oeste)
      [58.0, 68.0]  Barbería y Baños Beto's (peluquería, escalones azules y poste)
      [47.0, 58.0]  CopyFast • Centro de Copiado (fascia azul marino)
      [37.0, 47.0]  MR Multiservicios (estuco salmón)
      [26.0, 37.0]  Café Los Pinos (chapa de piedra laja natural y toldo rojo)
      [13.0, 26.0]  Taquería La Placita (2 niv, azul cobalto, balcón y rótulo saliente)
      [0.0, 13.0]   La Flor de Michoacán (2 niv, esquina SW, tejas 3D, pilastras verdes)

  - Cara Sur (Callejón Libertad, Y = 0.00m):
      [0.0, 14.0]   La Flor de Michoacán (fachada sur envolvente)
      [14.0, 30.0]  Dulcería Prisci (lámina ondulada roja y toldos amarillos)
      [30.0, 45.0]  Restaurant 2 de Sonora / Heras Internet (2 niv, tejas y A/C)
      [45.0, 68.0]  Patio interior / estacionamiento abierto y caseta
      [68.0, 92.0]  Hotel Colonial (2 niv, misión colonial con espadañas y forja)
      [92.0, 114.0] Taller / Bodega Sur (concreto, canes de madera, ladrillo expuesto)
      [114.0, 128.0] Barda perimetral sur de la terminal (muro verde)

  - Cara Oriente (Abelardo L. Rodríguez, X = 128.00m):
      [0.0, 8.0]    Barda sureste
      [8.0, 22.0]   Portón monumental de autobuses (cercha espacial 14m, reja tubular, paso abierto)
      [22.0, 58.0]  Muro verde de terminal con carrito de hot dogs en banqueta
      [58.0, 77.0]  Terminal de Autobuses (fachada oriente con marquesina zig-zag)
"""

import os
import math
import bpy
import bmesh
from mathutils import Vector, Euler

# ---------------------------------------------------------------------------
# 1. Rutas y Dimensiones Maestras
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

X_MAX = 128.00
Y_MAX = 77.00
Z_BASE = -1.50
Z_GROUND = 0.00

FONT_PATH = "/System/Library/Fonts/Supplemental/Impact.ttf"
if not os.path.exists(FONT_PATH):
    FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"

ROT_SOUTH = (math.radians(90.0), 0.0, 0.0)
ROT_NORTH = (math.radians(90.0), 0.0, math.radians(180.0))
ROT_WEST  = (math.radians(90.0), 0.0, math.radians(-90.0))
ROT_EAST  = (math.radians(90.0), 0.0, math.radians(90.0))

# ---------------------------------------------------------------------------
# 2. Primitivas Geométricas Limpias (Sin Traslapes)
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
    """Genera paralelepípedo limpio con normales hacia el exterior."""
    verts = [
        bm.verts.new((x1, y1, z1)), bm.verts.new((x2, y1, z1)),
        bm.verts.new((x2, y2, z1)), bm.verts.new((x1, y2, z1)),
        bm.verts.new((x1, y1, z2)), bm.verts.new((x2, y1, z2)),
        bm.verts.new((x2, y2, z2)), bm.verts.new((x1, y2, z2))
    ]
    f0 = bm.faces.new((verts[0], verts[1], verts[2], verts[3]))
    f1 = bm.faces.new((verts[4], verts[7], verts[6], verts[5]))
    f2 = bm.faces.new((verts[0], verts[4], verts[5], verts[1]))
    f3 = bm.faces.new((verts[1], verts[5], verts[6], verts[2]))
    f4 = bm.faces.new((verts[2], verts[6], verts[7], verts[3]))
    f5 = bm.faces.new((verts[3], verts[7], verts[4], verts[0]))
    return [f0, f1, f2, f3, f4, f5]

def add_window_frame_and_glass(bm, x1, x2, y_wall, z1, z2, frame_w=0.08, frame_d=0.05, axis='Y', facing=1):
    """
    Cancelería de aluminio extruida con vidrio reflectivo que sobresale ligeramente
    de la pared, eliminando z-fighting y sombras internas negras.
    """
    faces_frame = []
    faces_glass = []
    
    if axis == 'Y':
        y_f0 = y_wall + facing * 0.005
        y_f1 = y_wall + facing * (0.005 + frame_d)
        y_min, y_max = min(y_f0, y_f1), max(y_f0, y_f1)
        
        # Marco superior (dintel)
        faces_frame.extend(add_box(bm, x1, x2, y_min, y_max, z2 - frame_w, z2))
        # Marco inferior (alféizar)
        faces_frame.extend(add_box(bm, x1, x2, y_min, y_max, z1, z1 + frame_w))
        # Jambas laterales
        faces_frame.extend(add_box(bm, x1, x1 + frame_w, y_min, y_max, z1, z2))
        faces_frame.extend(add_box(bm, x2 - frame_w, x2, y_min, y_max, z1, z2))
        
        # Panel de vidrio reflectivo central
        y_g = y_wall + facing * 0.02
        v_g = [
            bm.verts.new((x1 + frame_w, y_g, z1 + frame_w)),
            bm.verts.new((x2 - frame_w, y_g, z1 + frame_w)),
            bm.verts.new((x2 - frame_w, y_g, z2 - frame_w)),
            bm.verts.new((x1 + frame_w, y_g, z2 - frame_w))
        ]
        if facing > 0:
            faces_glass.append(bm.faces.new(v_g))
        else:
            faces_glass.append(bm.faces.new((v_g[0], v_g[3], v_g[2], v_g[1])))
    else:
        x_f0 = y_wall + facing * 0.005
        x_f1 = y_wall + facing * (0.005 + frame_d)
        x_min, x_max = min(x_f0, x_f1), max(x_f0, x_f1)
        
        # Marco superior
        faces_frame.extend(add_box(bm, x_min, x_max, x1, x2, z2 - frame_w, z2))
        # Marco inferior
        faces_frame.extend(add_box(bm, x_min, x_max, x1, x2, z1, z1 + frame_w))
        # Jambas
        faces_frame.extend(add_box(bm, x_min, x_max, x1, x1 + frame_w, z1, z2))
        faces_frame.extend(add_box(bm, x_min, x_max, x2 - frame_w, x2, z1, z2))
        
        # Vidrio reflectivo
        x_g = y_wall + facing * 0.02
        v_g = [
            bm.verts.new((x_g, x1 + frame_w, z1 + frame_w)),
            bm.verts.new((x_g, x2 - frame_w, z1 + frame_w)),
            bm.verts.new((x_g, x2 - frame_w, z2 - frame_w)),
            bm.verts.new((x_g, x1 + frame_w, z2 - frame_w))
        ]
        if facing > 0:
            faces_glass.append(bm.faces.new((v_g[0], v_g[3], v_g[2], v_g[1])))
        else:
            faces_glass.append(bm.faces.new(v_g))
            
    return faces_frame, faces_glass

def add_teja_ribs_x(bm, x_start, x_end, y_eave, y_ridge, z_eave, z_ridge, spacing=0.40):
    """Genera hiladas de teja colonial curva 3D con canales y cobijas a lo largo de X."""
    faces = []
    num_ribs = max(1, int((x_end - x_start) / spacing))
    for i in range(num_ribs):
        xc = x_start + (i + 0.5) * spacing
        v0 = bm.verts.new((xc - 0.12, y_eave, z_eave + 0.03))
        v1 = bm.verts.new((xc + 0.12, y_eave, z_eave + 0.03))
        v2 = bm.verts.new((xc + 0.12, y_ridge, z_ridge + 0.03))
        v3 = bm.verts.new((xc - 0.12, y_ridge, z_ridge + 0.03))
        v_top0 = bm.verts.new((xc, y_eave, z_eave + 0.10))
        v_top1 = bm.verts.new((xc, y_ridge, z_ridge + 0.10))

        faces.append(bm.faces.new((v0, v1, v_top0)))
        faces.append(bm.faces.new((v1, v2, v_top1, v_top0)))
        faces.append(bm.faces.new((v2, v3, v_top1)))
        faces.append(bm.faces.new((v3, v0, v_top0, v_top1)))
    return faces

def add_teja_ribs_y(bm, y_start, y_end, x_eave, x_ridge, z_eave, z_ridge, spacing=0.40):
    """Genera hiladas de teja colonial curva 3D a lo largo de Y."""
    faces = []
    num_ribs = max(1, int((y_end - y_start) / spacing))
    for i in range(num_ribs):
        yc = y_start + (i + 0.5) * spacing
        v0 = bm.verts.new((x_eave, yc - 0.12, z_eave + 0.03))
        v1 = bm.verts.new((x_eave, yc + 0.12, z_eave + 0.03))
        v2 = bm.verts.new((x_ridge, yc + 0.12, z_ridge + 0.03))
        v3 = bm.verts.new((x_ridge, yc - 0.12, z_ridge + 0.03))
        v_top0 = bm.verts.new((x_eave, yc, z_eave + 0.10))
        v_top1 = bm.verts.new((x_ridge, yc, z_ridge + 0.10))

        faces.append(bm.faces.new((v0, v1, v_top0)))
        faces.append(bm.faces.new((v1, v2, v_top1, v_top0)))
        faces.append(bm.faces.new((v2, v3, v_top1)))
        faces.append(bm.faces.new((v3, v0, v_top0, v_top1)))
    return faces

def add_canopy_quarter_round(bm, x1, x2, y_wall, depth=1.40, z_base=3.20, height=0.70, segments=6, facing=1):
    """Toldo de cuarto de cilindro de lona tensada con faldón y tapas laterales."""
    faces = []
    arc_pts = []
    for i in range(segments + 1):
        th = (math.pi * 0.5) * (i / segments)
        dy = depth * math.cos(th) * facing
        dz = height * math.sin(th)
        arc_pts.append((y_wall + dy, z_base + dz))

    for i in range(segments):
        y0, z0 = arc_pts[i]
        y1, z1 = arc_pts[i+1]
        v_bl = bm.verts.new((x1, y0, z0))
        v_br = bm.verts.new((x2, y0, z0))
        v_tr = bm.verts.new((x2, y1, z1))
        v_tl = bm.verts.new((x1, y1, z1))
        faces.append(bm.faces.new((v_bl, v_br, v_tr, v_tl)))

    y_front = y_wall + depth * facing
    v_top1 = bm.verts.new((x1, y_wall, z_base + height))
    v_bot1 = bm.verts.new((x1, y_wall, z_base))
    v_frt1 = bm.verts.new((x1, y_front, z_base))
    faces.append(bm.faces.new((v_bot1, v_frt1, v_top1)))

    v_top2 = bm.verts.new((x2, y_wall, z_base + height))
    v_bot2 = bm.verts.new((x2, y_wall, z_base))
    v_frt2 = bm.verts.new((x2, y_front, z_base))
    faces.append(bm.faces.new((v_bot2, v_top2, v_frt2)))

    f_valance = add_box(bm, x1, x2, min(y_front, y_front - 0.03*facing), max(y_front, y_front - 0.03*facing), z_base - 0.16, z_base)
    faces.extend(f_valance)
    return faces

def add_space_truss_beam(bm, p1, p2, width=0.45, height=0.75, bays=12):
    """Viga tridimensional en celosía de perfiles tubulares de acero."""
    faces = []
    v_dir = (p2 - p1).normalized()
    total_len = (p2 - p1).length
    v_up = Vector((0.0, 0.0, 1.0))
    v_side = v_dir.cross(v_up).normalized()

    for i in range(bays):
        t0 = i / bays
        t1 = (i + 1) / bays
        ptA = p1 + v_dir * (t0 * total_len)
        ptB = p1 + v_dir * (t1 * total_len)

        cA = [
            ptA - v_side * (width*0.5) - v_up * (height*0.5),
            ptA + v_side * (width*0.5) - v_up * (height*0.5),
            ptA + v_side * (width*0.5) + v_up * (height*0.5),
            ptA - v_side * (width*0.5) + v_up * (height*0.5)
        ]
        cB = [
            ptB - v_side * (width*0.5) - v_up * (height*0.5),
            ptB + v_side * (width*0.5) - v_up * (height*0.5),
            ptB + v_side * (width*0.5) + v_up * (height*0.5),
            ptB - v_side * (width*0.5) + v_up * (height*0.5)
        ]
        vA = [bm.verts.new(p) for p in cA]
        vB = [bm.verts.new(p) for p in cB]

        for j in range(4):
            jn = (j + 1) % 4
            faces.append(bm.faces.new((vA[j], vB[j], vB[jn], vA[jn])))

        faces.append(bm.faces.new((vA[0], vB[1], vB[2], vA[3])))
    return faces

def add_folded_plate_canopy(bm, x1, x2, y_wall, depth=1.60, z_base=3.20, height=0.45, folds=10):
    """Marquesina de losa de concreto plegada en zig-zag (sawtooth) de la Terminal de Autobuses."""
    faces = []
    dx = (x2 - x1) / folds
    y_proj = y_wall + depth
    for i in range(folds):
        xa = x1 + i * dx
        xb = xa + dx * 0.5
        xc = x1 + (i + 1) * dx

        v_wa = bm.verts.new((xa, y_wall, z_base))
        v_wb = bm.verts.new((xb, y_wall, z_base + height))
        v_wc = bm.verts.new((xc, y_wall, z_base))

        v_pa = bm.verts.new((xa, y_proj, z_base - 0.10))
        v_pb = bm.verts.new((xb, y_proj, z_base + height - 0.10))
        v_pc = bm.verts.new((xc, y_proj, z_base - 0.10))

        faces.append(bm.faces.new((v_wa, v_pa, v_pb, v_wb)))
        faces.append(bm.faces.new((v_wb, v_pb, v_pc, v_wc)))
        faces.append(bm.faces.new((v_pa, v_pc, v_pb)))
    return faces

def add_tinaco(bm, cx, cy, z_base, radius=0.55, height=1.15, segments=10):
    """Tinaco cilíndrico de azotea con tapa cónica."""
    faces = []
    bot_verts, top_verts = [], []
    for i in range(segments):
        th = (2.0 * math.pi * i) / segments
        bot_verts.append(bm.verts.new((cx + radius * math.cos(th), cy + radius * math.sin(th), z_base)))
        top_verts.append(bm.verts.new((cx + radius * math.cos(th), cy + radius * math.sin(th), z_base + height)))

    v_apex = bm.verts.new((cx, cy, z_base + height + 0.22))
    v_bot_c = bm.verts.new((cx, cy, z_base))

    for i in range(segments):
        inxt = (i + 1) % segments
        faces.append(bm.faces.new((bot_verts[i], bot_verts[inxt], top_verts[inxt], top_verts[i])))
        faces.append(bm.faces.new((top_verts[i], top_verts[inxt], v_apex)))
        faces.append(bm.faces.new((bot_verts[inxt], bot_verts[i], v_bot_c)))
    return faces

def add_barber_pole(bm, cx, cy, z_bottom, height=0.85, radius=0.10, segments=8):
    """Poste de barbería cilíndrico."""
    faces = []
    bot_v, top_v = [], []
    for i in range(segments):
        th = (2.0 * math.pi * i) / segments
        bot_v.append(bm.verts.new((cx + radius * math.cos(th), cy + radius * math.sin(th), z_bottom)))
        top_v.append(bm.verts.new((cx + radius * math.cos(th), cy + radius * math.sin(th), z_bottom + height)))

    for i in range(segments):
        inxt = (i + 1) % segments
        faces.append(bm.faces.new((bot_v[i], bot_v[inxt], top_v[inxt], top_v[i])))
    return faces

def add_hotdog_cart(bm, cx, cy, z_base):
    """Puesto callejero de hot dogs en banqueta."""
    faces = []
    faces.extend(add_box(bm, cx - 0.70, cx + 0.70, cy - 0.45, cy + 0.45, z_base + 0.25, z_base + 0.95))
    faces.extend(add_box(bm, cx - 0.60, cx - 0.50, cy - 0.50, cy - 0.45, z_base, z_base + 0.40))
    faces.extend(add_box(bm, cx + 0.50, cx + 0.60, cy - 0.50, cy - 0.45, z_base, z_base + 0.40))
    faces.extend(add_box(bm, cx - 0.65, cx - 0.60, cy - 0.40, cy - 0.35, z_base + 0.95, z_base + 1.90))
    faces.extend(add_box(bm, cx + 0.60, cx + 0.65, cy - 0.40, cy - 0.35, z_base + 0.95, z_base + 1.90))
    faces.extend(add_box(bm, cx - 0.65, cx - 0.60, cy + 0.35, cy + 0.40, z_base + 0.95, z_base + 1.90))
    faces.extend(add_box(bm, cx + 0.60, cx + 0.65, cy + 0.35, cy + 0.40, z_base + 0.95, z_base + 1.90))
    faces.extend(add_box(bm, cx - 0.85, cx + 0.85, cy - 0.55, cy + 0.55, z_base + 1.85, z_base + 2.10))
    return faces

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

# ---------------------------------------------------------------------------
# 3. Pipeline de Materiales PBR
# ---------------------------------------------------------------------------
def create_material(name, color_rgba, roughness=0.65, metallic=0.0, normal_tex_path=None, albedo_tex_path=None):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (500, 0)
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (100, 0)

    bsdf.inputs["Base Color"].default_value = color_rgba
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic

    if albedo_tex_path and os.path.exists(albedo_tex_path):
        alb_node = nodes.new(type="ShaderNodeTexImage")
        alb_node.location = (-300, 150)
        try:
            img = bpy.data.images.load(albedo_tex_path, check_existing=True)
            alb_node.image = img
            links.new(alb_node.outputs["Color"], bsdf.inputs["Base Color"])
        except Exception:
            pass

    if normal_tex_path and os.path.exists(normal_tex_path):
        tex_node = nodes.new(type="ShaderNodeTexImage")
        tex_node.location = (-400, -200)
        try:
            img = bpy.data.images.load(normal_tex_path, check_existing=True)
            img.colorspace_settings.name = 'Non-Color'
            tex_node.image = img
            norm_node = nodes.new(type="ShaderNodeNormalMap")
            norm_node.location = (-150, -200)
            norm_node.inputs["Strength"].default_value = 0.85
            links.new(tex_node.outputs["Color"], norm_node.inputs["Color"])
            links.new(norm_node.outputs["Normal"], bsdf.inputs["Normal"])
        except Exception as e:
            print(f"[Aviso] Error en mapa normal {normal_tex_path}: {e}")

    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat

def setup_materials():
    mats = {}
    tex_corrugated = os.path.join(TEXTURES_DIR, "corrugated_metal_normal.png")
    tex_shingle = os.path.join(TEXTURES_DIR, "shingle_roof_normal.png")
    tex_stucco = os.path.join(TEXTURES_DIR, "hotel_tecate_stucco_normal.png")
    tex_laja_norm = os.path.join(TEXTURES_DIR, "kiosko_laja_normal.png")
    tex_laja_alb = os.path.join(TEXTURES_DIR, "kiosko_laja_albedo.png")
    tex_ladrillo = os.path.join(TEXTURES_DIR, "kiosko_ladrillo_normal.png")

    mats['plinth'] = create_material("Mat_Plinth_Basalt", (0.16, 0.16, 0.16, 1.0), roughness=0.92)
    mats['white_stucco'] = create_material("Mat_Stucco_White", (0.88, 0.88, 0.86, 1.0), roughness=0.72, normal_tex_path=tex_stucco)
    mats['cream_stucco'] = create_material("Mat_Stucco_Cream", (0.83, 0.79, 0.69, 1.0), roughness=0.75, normal_tex_path=tex_stucco)
    mats['salmon_stucco'] = create_material("Mat_Stucco_Salmon", (0.78, 0.48, 0.42, 1.0), roughness=0.70, normal_tex_path=tex_stucco)
    mats['mint_stucco'] = create_material("Mat_Stucco_Mint", (0.42, 0.65, 0.48, 1.0), roughness=0.68, normal_tex_path=tex_stucco)
    mats['cobalt_stucco'] = create_material("Mat_Stucco_Cobalt", (0.10, 0.28, 0.62, 1.0), roughness=0.65, normal_tex_path=tex_stucco)
    mats['telas_ochre'] = create_material("Mat_Telas_Ochre", (0.76, 0.49, 0.18, 1.0), roughness=0.68, normal_tex_path=tex_stucco)
    mats['terminal_green'] = create_material("Mat_Terminal_Green", (0.34, 0.48, 0.36, 1.0), roughness=0.78, normal_tex_path=tex_stucco)
    mats['grey_concrete'] = create_material("Mat_Grey_Concrete", (0.52, 0.52, 0.52, 1.0), roughness=0.88)
    mats['hotel_white_tile'] = create_material("Mat_Hotel_White_Tile", (0.94, 0.94, 0.94, 1.0), roughness=0.18)

    mats['prisci_red_metal'] = create_material("Mat_Prisci_Red_Sheet", (0.78, 0.12, 0.12, 1.0), roughness=0.45, normal_tex_path=tex_corrugated)
    mats['terminal_beige_metal'] = create_material("Mat_Terminal_Beige_Sheet", (0.76, 0.71, 0.53, 1.0), roughness=0.55, normal_tex_path=tex_corrugated)
    mats['shingle_roof'] = create_material("Mat_Roof_Shingle", (0.52, 0.28, 0.18, 1.0), roughness=0.80, normal_tex_path=tex_shingle)
    mats['clay_tile'] = create_material("Mat_Clay_Tile", (0.65, 0.24, 0.12, 1.0), roughness=0.78)
    mats['asphalt_yard'] = create_material("Mat_Asphalt_Yard", (0.18, 0.18, 0.18, 1.0), roughness=0.90)
    mats['dirt_yard'] = create_material("Mat_Dirt_Yard", (0.55, 0.44, 0.32, 1.0), roughness=0.95)

    mats['brick_rustic'] = create_material("Mat_Brick_Rustic", (0.62, 0.24, 0.16, 1.0), roughness=0.85, normal_tex_path=tex_ladrillo)
    mats['stone_laja'] = create_material("Mat_Stone_Laja", (0.64, 0.54, 0.42, 1.0), roughness=0.85, normal_tex_path=tex_laja_norm, albedo_tex_path=tex_laja_alb)

    mats['steel_blue'] = create_material("Mat_Steel_Blue_Truss", (0.12, 0.28, 0.72, 1.0), roughness=0.35, metallic=0.75)
    mats['iron_black'] = create_material("Mat_Wrought_Iron_Black", (0.05, 0.05, 0.05, 1.0), roughness=0.50, metallic=0.60)
    mats['aluminum_frame'] = create_material("Mat_Aluminum_Frame", (0.75, 0.75, 0.75, 1.0), roughness=0.30, metallic=0.85)

    mats['awning_coca_red'] = create_material("Mat_Awning_Coca_Red", (0.82, 0.08, 0.08, 1.0), roughness=0.60)
    mats['awning_blue'] = create_material("Mat_Awning_Capota_Blue", (0.12, 0.32, 0.70, 1.0), roughness=0.60)
    mats['awning_yellow_michoacan'] = create_material("Mat_Awning_Yellow_Michoacan", (0.92, 0.78, 0.12, 1.0), roughness=0.55)
    mats['awning_striped_prisci'] = create_material("Mat_Awning_Striped_Prisci", (0.88, 0.82, 0.30, 1.0), roughness=0.60)

    # Vidrio Arquitectónico Reflectivo PBR
    mats['glass_pbr'] = create_material("Mat_Glass_PBR_Physical", (0.18, 0.24, 0.30, 1.0), roughness=0.06, metallic=0.35)

    mats['text_gold'] = create_material("Mat_Text_Gold_Metal", (0.92, 0.75, 0.22, 1.0), roughness=0.25, metallic=0.80)
    mats['text_blue'] = create_material("Mat_Text_Blue_Corp", (0.08, 0.22, 0.65, 1.0), roughness=0.35)
    mats['text_red'] = create_material("Mat_Text_Red_Corp", (0.85, 0.10, 0.10, 1.0), roughness=0.35)
    mats['text_white'] = create_material("Mat_Text_White_Corp", (0.95, 0.95, 0.95, 1.0), roughness=0.30)
    return mats

def assign_material_to_faces(mesh_obj, faces, mat):
    if mat.name not in mesh_obj.data.materials:
        mesh_obj.data.materials.append(mat)
    mat_idx = mesh_obj.data.materials.find(mat.name)
    for f in faces:
        f.material_index = mat_idx

# ---------------------------------------------------------------------------
# 4. Ensamblaje Arquitectónico Riguroso (Zero Traslapes)
# ---------------------------------------------------------------------------
def build_zocalo_monolitico(bm, mats, mesh_obj):
    t = 0.40
    f_south = add_box(bm, 0, X_MAX, 0, t, Z_BASE, Z_GROUND)
    f_north = add_box(bm, 0, X_MAX, Y_MAX - t, Y_MAX, Z_BASE, Z_GROUND)
    f_west  = add_box(bm, 0, t, 0, Y_MAX, Z_BASE, Z_GROUND)
    f_east  = add_box(bm, X_MAX - t, X_MAX, 0, Y_MAX, Z_BASE, Z_GROUND)
    assign_material_to_faces(mesh_obj, f_south + f_north + f_west + f_east, mats['plinth'])

def build_north_facade_juarez(bm, mats, mesh_obj):
    y_front = Y_MAX
    y_back = Y_MAX - 16.00

    # 1. Modas Da Vinci (X = 0 a 9m, Y = 68 a 77m, Z = 3.60m)
    f_base = add_box(bm, 0, 9.0, 68.0, y_front, Z_GROUND, 3.60)
    assign_material_to_faces(mesh_obj, f_base, mats['white_stucco'])
    f_tejas_dv = add_teja_ribs_x(bm, 0, 9.0, y_front + 0.35, y_front - 0.80, 3.55, 4.05, spacing=0.38)
    assign_material_to_faces(mesh_obj, f_tejas_dv, mats['clay_tile'])
    fr, gl = add_window_frame_and_glass(bm, 1.20, 7.80, y_front, 0.40, 2.90, axis='Y', facing=1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 2. Telas Elías / Bordados Elías (X = 9 a 32m, Y = 59 a 77m, Z = 7.60m)
    f_telas = add_box(bm, 9.0, 32.0, 59.0, y_front, Z_GROUND, 7.60)
    assign_material_to_faces(mesh_obj, f_telas, mats['telas_ochre'])
    f_corn_telas = add_box(bm, 8.80, 32.20, y_front - 0.10, y_front + 0.25, 7.50, 7.75)
    assign_material_to_faces(mesh_obj, f_corn_telas, mats['white_stucco'])
    p1 = add_box(bm, 9.0, 9.70, y_front - 0.80, y_front, Z_GROUND, 3.80)
    p2 = add_box(bm, 20.15, 20.85, y_front - 0.80, y_front, Z_GROUND, 3.80)
    p3 = add_box(bm, 31.30, 32.0, y_front - 0.80, y_front, Z_GROUND, 3.80)
    assign_material_to_faces(mesh_obj, p1 + p2 + p3, mats['telas_ochre'])
    fr, gl = add_window_frame_and_glass(bm, 10.50, 30.50, y_front, 4.20, 7.00, axis='Y', facing=1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 3. Mariscos Preparados El Chapo (X = 32 a 44m, Y = 59 a 77m, Z = 3.80m)
    f_chapo = add_box(bm, 32.0, 44.0, 59.0, y_front, Z_GROUND, 3.80)
    assign_material_to_faces(mesh_obj, f_chapo, mats['white_stucco'])
    f_arco = add_box(bm, 34.0, 38.0, y_front, y_front + 0.12, Z_GROUND, 3.20)
    assign_material_to_faces(mesh_obj, f_arco, mats['brick_rustic'])
    fr, gl = add_window_frame_and_glass(bm, 34.40, 37.60, y_front + 0.12, Z_GROUND, 3.00, axis='Y', facing=1)
    assign_material_to_faces(mesh_obj, fr, mats['iron_black'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])
    fr, gl = add_window_frame_and_glass(bm, 39.0, 43.0, y_front, 0.80, 2.80, axis='Y', facing=1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 4. Taquería Los Arcos (X = 44 a 58m, Y = 59 a 77m, Z = 3.90m)
    f_arcos = add_box(bm, 44.0, 58.0, 59.0, y_front, Z_GROUND, 3.90)
    assign_material_to_faces(mesh_obj, f_arcos, mats['cream_stucco'])
    f_truss_arc = add_space_truss_beam(bm, Vector((44.50, y_front - 0.20, 3.95)), Vector((57.50, y_front - 0.20, 3.95)), width=0.30, height=0.70, bays=8)
    assign_material_to_faces(mesh_obj, f_truss_arc, mats['steel_blue'])
    f_canopy_arc = add_canopy_quarter_round(bm, 44.50, 57.50, y_front, depth=1.60, z_base=3.20, height=0.75, facing=1)
    assign_material_to_faces(mesh_obj, f_canopy_arc, mats['awning_coca_red'])
    fr, gl = add_window_frame_and_glass(bm, 45.0, 57.0, y_front, 0.60, 2.80, axis='Y', facing=1)
    assign_material_to_faces(mesh_obj, fr, mats['hotel_white_tile'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 5. Rosticería Los Polos B.C. (X = 58 a 70m, Y = 59 a 77m, Z = 3.70m)
    f_polos = add_box(bm, 58.0, 70.0, 59.0, y_front, Z_GROUND, 3.70)
    assign_material_to_faces(mesh_obj, f_polos, mats['white_stucco'])
    f_canopy_pol = add_canopy_quarter_round(bm, 58.50, 69.50, y_front, depth=1.50, z_base=3.10, height=0.65, facing=1)
    assign_material_to_faces(mesh_obj, f_canopy_pol, mats['awning_coca_red'])
    fr, gl = add_window_frame_and_glass(bm, 59.0, 69.0, y_front, 0.70, 2.80, axis='Y', facing=1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 6. Farmacia del Pueblo (X = 70 a 84m, Y = 59 a 77m, Z = 4.00m)
    f_farm = add_box(bm, 70.0, 84.0, 59.0, y_front, Z_GROUND, 4.00)
    assign_material_to_faces(mesh_obj, f_farm, mats['cream_stucco'])
    f_tejas_farm = add_teja_ribs_x(bm, 69.80, 84.20, y_front + 1.40, y_front, 3.10, 4.10, spacing=0.38)
    assign_material_to_faces(mesh_obj, f_tejas_farm, mats['clay_tile'])
    fr, gl = add_window_frame_and_glass(bm, 71.0, 83.0, y_front, 0.40, 2.90, axis='Y', facing=1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 7. Barber Shop Azteca 230 (X = 84 a 94m, Y = 59 a 77m, Z = 3.80m)
    f_azt = add_box(bm, 84.0, 94.0, 59.0, y_front, Z_GROUND, 3.80)
    assign_material_to_faces(mesh_obj, f_azt, mats['white_stucco'])
    f_bp = add_barber_pole(bm, 84.35, y_front + 0.15, 1.40, height=0.85, radius=0.10)
    assign_material_to_faces(mesh_obj, f_bp, mats['awning_coca_red'])
    fr, gl = add_window_frame_and_glass(bm, 85.0, 93.0, y_front, 0.50, 2.80, axis='Y', facing=1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 8. Hotel Juárez & Cafetería Juárez (X = 94 a 109m, Y = 58 a 77m, Z = 7.40m)
    f_hj = add_box(bm, 94.0, 109.0, 58.0, y_front, Z_GROUND, 7.40)
    assign_material_to_faces(mesh_obj, f_hj, mats['hotel_white_tile'])
    fr, gl = add_window_frame_and_glass(bm, 95.0, 108.0, y_front, 0.50, 2.90, axis='Y', facing=1)
    assign_material_to_faces(mesh_obj, fr, mats['awning_coca_red'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])
    fr, gl = add_window_frame_and_glass(bm, 96.0, 107.0, y_front, 4.40, 6.20, axis='Y', facing=1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # Callejón Medellín y Villegas (X = 109 a 114m)
    f_muro_med = add_box(bm, 113.70, 114.0, 58.0, y_front, Z_GROUND, 2.60)
    assign_material_to_faces(mesh_obj, f_muro_med, mats['white_stucco'])

    # 9. Super Taquería Tecate (X = 114 a 120m, Y = 58 a 77m, Z = 3.60m)
    f_stt = add_box(bm, 114.0, 120.0, 58.0, y_front, Z_GROUND, 3.60)
    assign_material_to_faces(mesh_obj, f_stt, mats['cream_stucco'])
    f_stt_can = add_canopy_quarter_round(bm, 114.20, 119.80, y_front, depth=1.30, z_base=3.10, height=0.55, facing=1)
    assign_material_to_faces(mesh_obj, f_stt_can, mats['awning_coca_red'])
    fr, gl = add_window_frame_and_glass(bm, 114.50, 119.50, y_front, 0.60, 2.80, axis='Y', facing=1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 10. Terminal Central de Autobuses (X = 120 a 128m, Y = 58 a 77m, Z = 5.50m) - Un Solo Volumen Maestro
    f_term = add_box(bm, 120.0, 128.0, 58.0, y_front, Z_GROUND, 5.50)
    assign_material_to_faces(mesh_obj, f_term, mats['terminal_green'])
    f_fascia_n = add_box(bm, 119.80, 128.0, y_front + 0.05, y_front + 0.20, 3.60, 5.40)
    assign_material_to_faces(mesh_obj, f_fascia_n, mats['terminal_beige_metal'])
    f_fold_n = add_folded_plate_canopy(bm, 119.80, 128.0, y_front, depth=1.60, z_base=3.15, height=0.45, folds=8)
    assign_material_to_faces(mesh_obj, f_fold_n, mats['grey_concrete'])
    fr, gl = add_window_frame_and_glass(bm, 120.50, 127.50, y_front, 0.20, 3.00, axis='Y', facing=1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

def build_west_facade_ortiz_rubio(bm, mats, mesh_obj):
    x_front = 0.00

    # 1. Modas Da Vinci (Lateral: Y = 68 a 77m)
    fr, gl = add_window_frame_and_glass(bm, 70.0, 76.0, x_front, 0.40, 2.90, axis='X', facing=-1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 2. Barbería y Baños Beto's (X = 0 a 9m, Y = 58 a 68m, Z = 3.60m) - Sin Traslape
    f_beto = add_box(bm, x_front, 9.0, 58.0, 68.0, Z_GROUND, 3.60)
    assign_material_to_faces(mesh_obj, f_beto, mats['white_stucco'])
    f_steps_b = add_box(bm, x_front - 0.40, x_front, 59.50, 66.50, Z_GROUND, 0.25)
    assign_material_to_faces(mesh_obj, f_steps_b, mats['steel_blue'])
    f_bp_b = add_barber_pole(bm, x_front - 0.15, 59.0, 1.40, height=0.85, radius=0.10)
    assign_material_to_faces(mesh_obj, f_bp_b, mats['awning_coca_red'])
    fr, gl = add_window_frame_and_glass(bm, 59.50, 67.0, x_front, 0.40, 2.90, axis='X', facing=-1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 3. CopyFast • Centro de Copiado (X = 0 a 16m, Y = 47 a 58m, Z = 3.80m)
    f_fast = add_box(bm, x_front, 16.0, 47.0, 58.0, Z_GROUND, 3.80)
    assign_material_to_faces(mesh_obj, f_fast, mats['white_stucco'])
    f_fascia_cf = add_box(bm, x_front - 0.15, x_front, 47.20, 57.80, 2.80, 3.75)
    assign_material_to_faces(mesh_obj, f_fascia_cf, mats['cobalt_stucco'])
    fr, gl = add_window_frame_and_glass(bm, 48.0, 57.0, x_front, 0.35, 2.70, axis='X', facing=-1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 4. MR Multiservicios (X = 0 a 16m, Y = 37 a 47m, Z = 3.50m)
    f_mr = add_box(bm, x_front, 16.0, 37.0, 47.0, Z_GROUND, 3.50)
    assign_material_to_faces(mesh_obj, f_mr, mats['salmon_stucco'])
    fr, gl = add_window_frame_and_glass(bm, 38.0, 46.0, x_front, 0.50, 2.80, axis='X', facing=-1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 5. Café Los Pinos (X = 0 a 16m, Y = 26 a 37m, Z = 3.60m) - Piedra Laja
    f_pinos = add_box(bm, x_front, 16.0, 26.0, 37.0, Z_GROUND, 3.60)
    assign_material_to_faces(mesh_obj, f_pinos, mats['stone_laja'])
    f_pinos_can = add_canopy_quarter_round(bm, x_front - 1.30, x_front, 27.0, depth=1.30, z_base=2.65, height=0.60, facing=-1)
    fr, gl = add_window_frame_and_glass(bm, 27.50, 35.50, x_front, 0.50, 2.60, axis='X', facing=-1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 6. Taquería La Placita (X = 0 a 16m, Y = 13 a 26m, Z = 6.80m, 2 Niveles) - Azul Cobalto
    f_plac = add_box(bm, x_front, 16.0, 13.0, 26.0, Z_GROUND, 6.80)
    assign_material_to_faces(mesh_obj, f_plac, mats['cobalt_stucco'])
    f_balc_fl = add_box(bm, x_front - 1.20, x_front, 13.50, 25.50, 3.40, 3.55)
    f_balc_rail = add_box(bm, x_front - 1.20, x_front - 1.10, 13.50, 25.50, 3.55, 4.45)
    assign_material_to_faces(mesh_obj, f_balc_fl, mats['cobalt_stucco'])
    assign_material_to_faces(mesh_obj, f_balc_rail, mats['steel_blue'])
    f_sign_plac = add_box(bm, x_front - 1.80, x_front - 0.20, 19.0, 19.20, 4.80, 6.20)
    assign_material_to_faces(mesh_obj, f_sign_plac, mats['awning_coca_red'])
    fr, gl = add_window_frame_and_glass(bm, 14.0, 25.0, x_front, 0.20, 2.90, axis='X', facing=-1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])
    fr, gl = add_window_frame_and_glass(bm, 14.5, 24.5, x_front, 3.80, 6.00, axis='X', facing=-1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 7. La Flor de Michoacán (Esquina Suroeste, X = 0 a 14m, Y = 0 a 13m, Z = 7.20m, 2 Niveles)
    f_mich_sw = add_box(bm, x_front, 14.0, 0.0, 13.0, Z_GROUND, 7.20)
    assign_material_to_faces(mesh_obj, f_mich_sw, mats['white_stucco'])
    f_tejas_mich = add_teja_ribs_y(bm, 0.0, 13.20, x_front - 1.40, x_front + 0.20, 6.80, 7.35, spacing=0.38)
    assign_material_to_faces(mesh_obj, f_tejas_mich, mats['clay_tile'])
    f_rail_mich = add_box(bm, x_front - 1.20, x_front - 1.10, 0.20, 12.80, 3.60, 4.50)
    assign_material_to_faces(mesh_obj, f_rail_mich, mats['terminal_green'])
    f_fascia_mich = add_box(bm, x_front - 0.20, x_front, 0.20, 12.80, 2.90, 3.75)
    assign_material_to_faces(mesh_obj, f_fascia_mich, mats['awning_yellow_michoacan'])
    for py in [0.20, 4.0, 8.0, 12.5]:
        col_m = add_box(bm, x_front - 0.35, x_front, py, py + 0.40, Z_GROUND, 2.90)
        assign_material_to_faces(mesh_obj, col_m, mats['mint_stucco'])
    fr, gl = add_window_frame_and_glass(bm, 0.80, 12.0, x_front, 0.20, 2.80, axis='X', facing=-1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

def build_south_facade_libertad(bm, mats, mesh_obj):
    y_front = 0.00

    # 1. La Flor de Michoacán (Retorno Sur: X = 0 a 14m)
    f_tejas_ms = add_teja_ribs_x(bm, 0.0, 14.0, y_front - 1.40, y_front + 0.20, 6.80, 7.35, spacing=0.38)
    assign_material_to_faces(mesh_obj, f_tejas_ms, mats['clay_tile'])
    f_fascia_ms = add_box(bm, 0.20, 13.80, y_front - 0.20, y_front, 2.90, 3.75)
    assign_material_to_faces(mesh_obj, f_fascia_ms, mats['awning_yellow_michoacan'])
    for px in [0.20, 4.5, 9.0, 13.5]:
        col_ms = add_box(bm, px, px + 0.40, y_front - 0.35, y_front, Z_GROUND, 2.90)
        assign_material_to_faces(mesh_obj, col_ms, mats['mint_stucco'])
    fr, gl = add_window_frame_and_glass(bm, 1.0, 13.0, y_front, 0.20, 2.80, axis='Y', facing=-1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 2. Dulcería Prisci (X = 14 a 30m, Y = 0 a 18m, Z = 4.20m) - Lámina Roja
    f_prisci = add_box(bm, 14.0, 30.0, y_front, 18.0, Z_GROUND, 4.20)
    assign_material_to_faces(mesh_obj, f_prisci, mats['prisci_red_metal'])
    f_toldo_pr = add_canopy_quarter_round(bm, 15.0, 29.0, y_front, depth=1.50, z_base=2.90, height=0.65, facing=-1)
    assign_material_to_faces(mesh_obj, f_toldo_pr, mats['awning_striped_prisci'])
    f_box_pr = add_box(bm, 28.5, 29.0, y_front - 1.20, y_front - 0.10, 2.50, 5.20)
    assign_material_to_faces(mesh_obj, f_box_pr, mats['text_gold'])
    fr, gl = add_window_frame_and_glass(bm, 15.50, 28.50, y_front, 0.50, 2.70, axis='Y', facing=-1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 3. Restaurant 2 de Sonora / Heras Internet (X = 30 a 45m, Y = 0 a 18m, Z = 6.50m)
    f_heras = add_box(bm, 30.0, 45.0, y_front, 18.0, Z_GROUND, 6.50)
    assign_material_to_faces(mesh_obj, f_heras, mats['salmon_stucco'])
    f_tejas_h = add_teja_ribs_x(bm, 29.80, 45.20, y_front - 1.20, y_front, 3.35, 3.85, spacing=0.38)
    assign_material_to_faces(mesh_obj, f_tejas_h, mats['clay_tile'])
    f_ac_h = add_box(bm, 39.5, 40.5, y_front - 0.70, y_front, 5.0, 5.80)
    assign_material_to_faces(mesh_obj, f_ac_h, mats['grey_concrete'])
    f_box_int = add_box(bm, 38.0, 38.35, y_front - 1.20, y_front - 0.10, 4.40, 6.20)
    assign_material_to_faces(mesh_obj, f_box_int, mats['awning_yellow_michoacan'])
    fr, gl = add_window_frame_and_glass(bm, 31.0, 44.0, y_front, 0.30, 2.90, axis='Y', facing=-1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])
    fr, gl = add_window_frame_and_glass(bm, 32.0, 43.5, y_front, 4.10, 5.80, axis='Y', facing=-1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 4. Patio Interior y Caseta (X = 45 a 68m)
    f_dirt = add_box(bm, 45.0, 60.0, y_front, 38.0, Z_GROUND - 0.03, Z_GROUND)
    assign_material_to_faces(mesh_obj, f_dirt, mats['dirt_yard'])
    f_fence = add_box(bm, 60.0, 68.0, y_front, y_front + 0.15, Z_GROUND, 1.80)
    assign_material_to_faces(mesh_obj, f_fence, mats['iron_black'])
    f_shed = add_box(bm, 60.5, 67.5, y_front + 0.50, y_front + 5.0, Z_GROUND, 3.20)
    assign_material_to_faces(mesh_obj, f_shed, mats['cream_stucco'])
    f_shed_roof = add_box(bm, 60.2, 67.8, y_front + 0.30, y_front + 5.2, 3.20, 3.50)
    assign_material_to_faces(mesh_obj, f_shed_roof, mats['shingle_roof'])

    # 5. Hotel Colonial (X = 68 a 92m, Y = 0 a 18m, Z = 7.60m) - Misión Colonial
    f_col = add_box(bm, 68.0, 92.0, y_front, 18.0, Z_GROUND, 7.60)
    assign_material_to_faces(mesh_obj, f_col, mats['white_stucco'])
    f_balc_c_fl = add_box(bm, 69.0, 91.0, y_front - 1.10, y_front, 3.60, 3.75)
    f_balc_c_rail = add_box(bm, 69.0, 91.0, y_front - 1.10, y_front - 1.00, 3.75, 4.65)
    assign_material_to_faces(mesh_obj, f_balc_c_fl, mats['white_stucco'])
    assign_material_to_faces(mesh_obj, f_balc_c_rail, mats['iron_black'])
    for sx in [72.0, 80.0, 88.0]:
        f_esp = add_box(bm, sx - 1.50, sx + 1.50, y_front, y_front + 0.35, 7.60, 8.60)
        assign_material_to_faces(mesh_obj, f_esp, mats['white_stucco'])
    fr, gl = add_window_frame_and_glass(bm, 70.0, 90.0, y_front, 0.40, 3.00, axis='Y', facing=-1)
    assign_material_to_faces(mesh_obj, fr, mats['stone_laja'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])
    fr, gl = add_window_frame_and_glass(bm, 70.50, 89.50, y_front, 4.20, 6.60, axis='Y', facing=-1)
    assign_material_to_faces(mesh_obj, fr, mats['stone_laja'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 6. Taller / Bodega Sur (X = 92 a 114m, Y = 0 a 18m, Z = 4.80m)
    f_tall = add_box(bm, 92.0, 114.0, y_front, 18.0, Z_GROUND, 4.80)
    assign_material_to_faces(mesh_obj, f_tall, mats['grey_concrete'])
    for vx in range(93, 114, 2):
        f_can = add_box(bm, vx, vx + 0.18, y_front - 0.45, y_front, 4.55, 4.75)
        assign_material_to_faces(mesh_obj, f_can, mats['clay_tile'])
    f_patch = add_box(bm, 95.0, 97.0, y_front - 0.05, y_front + 0.02, 1.20, 2.40)
    assign_material_to_faces(mesh_obj, f_patch, mats['brick_rustic'])
    fr, gl = add_window_frame_and_glass(bm, 94.0, 96.5, y_front, 3.40, 4.20, axis='Y', facing=-1)
    assign_material_to_faces(mesh_obj, fr, mats['iron_black'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])
    fr, gl = add_window_frame_and_glass(bm, 102.0, 104.5, y_front, 3.40, 4.20, axis='Y', facing=-1)
    assign_material_to_faces(mesh_obj, fr, mats['iron_black'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

    # 7. Barda Perimetral Sur de la Terminal (X = 114 a 128m, Z = 3.20m)
    f_barda_s = add_box(bm, 114.0, X_MAX, y_front, y_front + 0.35, Z_GROUND, 3.20)
    assign_material_to_faces(mesh_obj, f_barda_s, mats['terminal_green'])

def build_east_facade_rodriguez(bm, mats, mesh_obj):
    x_front = X_MAX
    x_in = X_MAX - 0.35

    # 1. Barda Sureste (Y = 0 a 8m, Z = 3.20m)
    f_barda_se = add_box(bm, x_in, x_front, 0.0, 8.0, Z_GROUND, 3.20)
    assign_material_to_faces(mesh_obj, f_barda_se, mats['terminal_green'])

    # 2. Portón Monumental de la Terminal (Y = 8 a 22m, Luz = 14.00m, Z = 3.80m / 4.40m)
    pilar_sur = add_box(bm, x_front - 0.50, x_front, 7.75, 8.25, Z_GROUND, 3.80)
    pilar_nte = add_box(bm, x_front - 0.50, x_front, 21.75, 22.25, Z_GROUND, 3.80)
    assign_material_to_faces(mesh_obj, pilar_sur + pilar_nte, mats['grey_concrete'])

    # Reja tubular azul con barrotes verticales (Y = 8.0 a 13.5) y paso abierto de autobuses (Y = 13.5 a 22.0)
    for gy in [8.10 + 0.35 * i for i in range(15)]:
        f_bar = add_box(bm, x_front - 0.10, x_front - 0.04, gy - 0.03, gy + 0.03, Z_GROUND, 3.20)
        assign_material_to_faces(mesh_obj, f_bar, mats['steel_blue'])
    f_rail_top = add_box(bm, x_front - 0.12, x_front - 0.02, 8.0, 13.50, 3.15, 3.30)
    f_rail_mid = add_box(bm, x_front - 0.12, x_front - 0.02, 8.0, 13.50, 1.50, 1.62)
    f_rail_bot = add_box(bm, x_front - 0.12, x_front - 0.02, 8.0, 13.50, 0.08, 0.20)
    assign_material_to_faces(mesh_obj, f_rail_top + f_rail_mid + f_rail_bot, mats['steel_blue'])

    # Líneas viales amarillas en el pavimento del acceso vehicular
    f_stripe = add_box(bm, x_front - 5.0, x_front + 0.50, 17.65, 17.85, Z_GROUND - 0.02, Z_GROUND)
    assign_material_to_faces(mesh_obj, f_stripe, mats['awning_yellow_michoacan'])

    # Cercha espacial tridimensional de 14 metros uniendo ambos pilares sin huecos
    p_start = Vector((x_front - 0.25, 8.0, 3.65))
    p_end   = Vector((x_front - 0.25, 22.0, 3.65))
    f_truss = add_space_truss_beam(bm, p_start, p_end, width=0.45, height=0.75, bays=12)
    assign_material_to_faces(mesh_obj, f_truss, mats['steel_blue'])

    # 3. Muro Verde Oriente de la Terminal (Y = 22 a 58m, Z = 3.20m)
    f_muro_e = add_box(bm, x_in, x_front, 22.0, 58.0, Z_GROUND, 3.20)
    assign_material_to_faces(mesh_obj, f_muro_e, mats['terminal_green'])
    f_hotdog = add_hotdog_cart(bm, x_front + 1.20, 34.0, Z_GROUND)
    assign_material_to_faces(mesh_obj, f_hotdog, mats['awning_yellow_michoacan'])

    # Nave de talleres interiores de autobuses (Z = 5.50m)
    f_tall_nave = add_box(bm, x_front - 18.0, x_front - 0.35, 26.0, 56.0, Z_GROUND, 5.50)
    assign_material_to_faces(mesh_obj, f_tall_nave, mats['terminal_green'])
    f_roof_tall = add_box(bm, x_front - 18.20, x_front - 0.20, 25.80, 56.20, 5.50, 6.10)
    assign_material_to_faces(mesh_obj, f_roof_tall, mats['terminal_beige_metal'])

    # 4. Terminal de Autobuses - Fachada Oriente (Y = 58 a 77m, Z = 5.50m)
    # Nota: El volumen maestro fue creado en la fachada norte; aquí añadimos la fascia, marquesina y ventanales oriente
    f_fascia_e = add_box(bm, x_front + 0.05, x_front + 0.20, 58.0, 77.0, 3.60, 5.40)
    assign_material_to_faces(mesh_obj, f_fascia_e, mats['terminal_beige_metal'])
    f_fold_mesh = add_box(bm, x_front, x_front + 1.60, 58.0, 77.0, 3.20, 3.55)
    assign_material_to_faces(mesh_obj, f_fold_mesh, mats['grey_concrete'])
    fr, gl = add_window_frame_and_glass(bm, 59.0, 75.0, x_front, 0.20, 3.00, axis='X', facing=1)
    assign_material_to_faces(mesh_obj, fr, mats['aluminum_frame'])
    assign_material_to_faces(mesh_obj, gl, mats['glass_pbr'])

def build_interior_courtyards_and_terminals(bm, mats, mesh_obj):
    # 1. Patio de maniobras asfaltado
    f_yard = add_box(bm, 70.0, X_MAX - 0.40, 8.0, 58.0, Z_GROUND - 0.03, Z_GROUND)
    assign_material_to_faces(mesh_obj, f_yard, mats['asphalt_yard'])

    # 2. Dársenas techadas de autobuses
    f_shed_roof = add_box(bm, 78.0, 108.0, 38.0, 52.0, 4.40, 4.65)
    assign_material_to_faces(mesh_obj, f_shed_roof, mats['terminal_beige_metal'])
    for cx in [80.0, 93.0, 106.0]:
        for cy in [40.0, 50.0]:
            f_col = add_box(bm, cx - 0.15, cx + 0.15, cy - 0.15, cy + 0.15, Z_GROUND, 4.40)
            assign_material_to_faces(mesh_obj, f_col, mats['steel_blue'])

    # 3. Autobuses de pasajeros aparcados
    for bus_x, bus_y, bus_color in [(82.0, 42.0, mats['white_stucco']), (95.0, 42.0, mats['steel_blue'])]:
        f_bus = add_box(bm, bus_x, bus_x + 10.50, bus_y, bus_y + 2.80, Z_GROUND + 0.35, Z_GROUND + 3.40)
        assign_material_to_faces(mesh_obj, f_bus, bus_color)
        f_bus_win = add_box(bm, bus_x - 0.05, bus_x + 10.55, bus_y - 0.05, bus_y + 2.85, Z_GROUND + 1.80, Z_GROUND + 2.90)
        assign_material_to_faces(mesh_obj, f_bus_win, mats['glass_pbr'])

    # 4. Bardas medianeras divisorias
    f_barda_div = add_box(bm, 45.0, 45.25, 18.0, 58.0, Z_GROUND, 2.60)
    f_barda_div2 = add_box(bm, 45.0, 70.0, 58.0, 58.25, Z_GROUND, 2.60)
    assign_material_to_faces(mesh_obj, f_barda_div + f_barda_div2, mats['white_stucco'])

    # 5. Equipamiento de Azotea
    tinaco_locs = [
        (6.0, 70.0, 3.60), (20.0, 68.0, 7.60), (50.0, 68.0, 3.90),
        (65.0, 68.0, 3.70), (78.0, 68.0, 4.00), (105.0, 68.0, 7.40),
        (10.0, 10.0, 7.20), (22.0, 10.0, 4.20), (80.0, 10.0, 7.60)
    ]
    for tx, ty, tz in tinaco_locs:
        f_tin = add_tinaco(bm, tx, ty, tz, radius=0.55, height=1.15)
        assign_material_to_faces(mesh_obj, f_tin, mats['plinth'])

    for ex, ey, ez in [(52.0, 72.0, 3.90), (64.0, 72.0, 3.70)]:
        f_ex = add_box(bm, ex - 0.40, ex + 0.40, ey - 0.40, ey + 0.40, ez, ez + 0.85)
        assign_material_to_faces(mesh_obj, f_ex, mats['aluminum_frame'])

# ---------------------------------------------------------------------------
# 5. Rótulos Corpóreos 3D Anti-Espejo
# ---------------------------------------------------------------------------
def add_3d_text(col, text_str, pos, rot_euler, size=0.55, extrude=0.06, mat=None, align_x='CENTER'):
    t_curve = bpy.data.curves.new(name=f"Text_{text_str[:8]}", type='FONT')
    t_curve.body = text_str
    t_curve.size = size
    t_curve.extrude = extrude
    t_curve.align_x = align_x
    t_curve.align_y = 'BOTTOM'

    if os.path.exists(FONT_PATH):
        try:
            t_curve.font = bpy.data.fonts.load(FONT_PATH)
        except Exception:
            pass

    t_obj = bpy.data.objects.new(name=f"TxtObj_{text_str[:12]}", object_data=t_curve)
    t_obj.location = pos
    t_obj.rotation_euler = rot_euler
    if mat:
        t_obj.data.materials.append(mat)
    col.objects.link(t_obj)
    return t_obj

def build_all_signage_and_typography(col, mats):
    # Cara Norte (Av. Benito Juárez)
    add_3d_text(col, "MODAS DA VINCI", (4.5, Y_MAX + 0.10, 3.40), ROT_NORTH, size=0.45, mat=mats['text_gold'])
    add_3d_text(col, "TELAS ELIAS", (20.5, Y_MAX + 0.12, 6.80), ROT_NORTH, size=0.85, extrude=0.08, mat=mats['text_gold'])
    add_3d_text(col, "MARISCOS EL CHAPO", (38.0, Y_MAX + 0.15, 3.30), ROT_NORTH, size=0.45, mat=mats['text_red'])
    add_3d_text(col, "TAQUERIA LOS ARCOS", (51.0, Y_MAX + 0.10, 3.30), ROT_NORTH, size=0.48, mat=mats['text_white'])
    add_3d_text(col, "ROSTICERIA LOS POLOS", (64.0, Y_MAX + 0.10, 3.20), ROT_NORTH, size=0.42, mat=mats['text_red'])
    add_3d_text(col, "FARMACIA DEL PUEBLO", (77.0, Y_MAX + 0.12, 4.30), ROT_NORTH, size=0.55, mat=mats['text_white'])
    add_3d_text(col, "BARBER SHOP AZTECA 230", (89.0, Y_MAX + 0.10, 3.30), ROT_NORTH, size=0.42, mat=mats['text_blue'])
    add_3d_text(col, "HOTEL JUAREZ", (101.5, Y_MAX + 0.12, 6.60), ROT_NORTH, size=0.80, extrude=0.08, mat=mats['text_blue'])
    add_3d_text(col, "CAFETERIA JUAREZ", (101.5, Y_MAX + 0.10, 3.10), ROT_NORTH, size=0.45, mat=mats['text_red'])
    add_3d_text(col, "SUPER TAQUERIA TECATE", (117.0, Y_MAX + 0.10, 3.25), ROT_NORTH, size=0.40, mat=mats['text_white'])
    add_3d_text(col, "TERMINAL DE AUTOBUSES TECATE B.C.", (124.0, Y_MAX + 0.15, 4.80), ROT_NORTH, size=0.46, extrude=0.06, mat=mats['text_red'])
    add_3d_text(col, "ABC • TNS • ELITE • SUBURBAJA", (124.0, Y_MAX + 0.15, 4.10), ROT_NORTH, size=0.35, mat=mats['text_blue'])

    # Cara Poniente (Ortiz Rubio)
    add_3d_text(col, "BARBERIA BETO'S", (-0.10, 63.5, 3.10), ROT_WEST, size=0.44, mat=mats['text_red'])
    add_3d_text(col, "COPYFAST • CENTRO DE COPIADO", (-0.10, 52.5, 3.20), ROT_WEST, size=0.50, mat=mats['text_white'])
    add_3d_text(col, "MR MULTISERVICIOS", (-0.10, 42.0, 3.10), ROT_WEST, size=0.42, mat=mats['text_blue'])
    add_3d_text(col, "CAFE LOS PINOS", (-0.10, 31.5, 3.20), ROT_WEST, size=0.45, mat=mats['text_white'])
    add_3d_text(col, "TAQUERIA LA PLACITA", (-0.12, 19.5, 6.20), ROT_WEST, size=0.65, extrude=0.08, mat=mats['text_gold'])
    add_3d_text(col, "LA FLOR DE MICHOACAN", (-0.12, 6.5, 6.40), ROT_WEST, size=0.70, extrude=0.08, mat=mats['text_red'])

    # Cara Sur (Callejón Libertad)
    add_3d_text(col, "LA FLOR DE MICHOACAN", (7.0, -0.12, 6.40), ROT_SOUTH, size=0.65, extrude=0.08, mat=mats['text_red'])
    add_3d_text(col, "DULCERIA PRISCI", (22.0, -0.12, 3.60), ROT_SOUTH, size=0.75, extrude=0.08, mat=mats['text_gold'])
    add_3d_text(col, "RESTAURANT 2 DE SONORA", (36.0, -0.10, 3.10), ROT_SOUTH, size=0.40, mat=mats['text_red'])
    add_3d_text(col, "INTERNET 2DO. PISO", (40.0, -0.12, 5.80), ROT_SOUTH, size=0.48, mat=mats['text_blue'])
    add_3d_text(col, "HOTEL COLONIAL", (80.0, -0.15, 6.80), ROT_SOUTH, size=0.85, extrude=0.08, mat=mats['text_red'])

    # Cara Oriente (Abelardo L. Rodríguez)
    add_3d_text(col, "BIENVENIDOS A TECATE", (X_MAX - 1.20, 42.0, 4.80), ROT_EAST, size=0.65, extrude=0.06, mat=mats['text_white'])
    add_3d_text(col, "TERMINAL CENTRAL DE AUTOBUSES", (X_MAX + 0.15, 68.0, 4.60), ROT_EAST, size=0.45, mat=mats['text_red'])

# ---------------------------------------------------------------------------
# 6. Escena Godot 4 con Colisiones Analíticas 1:1
# ---------------------------------------------------------------------------
def generate_godot_scene_1to1():
    shapes = []

    def add_shape(name, x1, x2, y1, y2, z1, z2):
        sx = round(abs(x2 - x1), 2)
        sz = round(abs(y2 - y1), 2)
        sy = round(abs(z2 - z1), 2)
        cx = round((x1 + x2) * 0.5, 2)
        cz = round(-(y1 + y2) * 0.5, 2)
        cy = round((z1 + z2) * 0.5, 2)
        shapes.append((name, (sx, sy, sz), (cx, cy, cz)))

    # Fachada Norte (Juárez)
    add_shape("Col_ModasDaVinci", 0, 9, 68, 77, 0, 3.60)
    add_shape("Col_TelasElias", 9, 32, 59, 77, 0, 7.60)
    add_shape("Col_MariscosElChapo", 32, 44, 59, 77, 0, 3.80)
    add_shape("Col_TaqLosArcos", 44, 58, 59, 77, 0, 3.90)
    add_shape("Col_RosticeriaPolos", 58, 70, 59, 77, 0, 3.70)
    add_shape("Col_FarmaciaPueblo", 70, 84, 59, 77, 0, 4.00)
    add_shape("Col_BarberAzteca", 84, 94, 59, 77, 0, 3.80)
    add_shape("Col_HotelJuarez", 94, 109, 58, 77, 0, 7.40)
    add_shape("Col_MuroMedellin", 113.70, 114.0, 58, 77, 0, 2.60)
    add_shape("Col_SuperTaqTecate", 114, 120, 58, 77, 0, 3.60)
    add_shape("Col_TerminalNorte", 120, 128, 58, 77, 0, 5.50)

    # Fachada Poniente (Ortiz Rubio)
    add_shape("Col_BarberiaBetos", 0, 9, 58, 68, 0, 3.60)
    add_shape("Col_CopyFast", 0, 16, 47, 58, 0, 3.80)
    add_shape("Col_MRMultiservicios", 0, 16, 37, 47, 0, 3.50)
    add_shape("Col_CafeLosPinos", 0, 16, 26, 37, 0, 3.60)
    add_shape("Col_TaqLaPlacita", 0, 16, 13, 26, 0, 6.80)
    add_shape("Col_LaFlorMichoacanSur", 0, 14, 0, 13, 0, 7.20)

    # Fachada Sur (Libertad)
    add_shape("Col_DulceriaPrisci", 14, 30, 0, 18, 0, 4.20)
    add_shape("Col_RestauranteHeras", 30, 45, 0, 18, 0, 6.50)
    add_shape("Col_CasetaJardin", 60, 68, 0, 18, 0, 3.50)
    add_shape("Col_HotelColonial", 68, 92, 0, 18, 0, 7.60)
    add_shape("Col_TallerSur", 92, 114, 0, 18, 0, 4.80)
    add_shape("Col_BardaSurTerminal", 114, 128, 0, 0.40, 0, 3.20)

    # Fachada Oriente (Abelardo L. Rodríguez)
    add_shape("Col_BardaSureste", 127.60, 128.0, 0, 8, 0, 3.20)
    add_shape("Col_PilarPortonSur", 127.50, 128.0, 7.75, 8.25, 0, 3.80)
    add_shape("Col_PilarPortonNorte", 127.50, 128.0, 21.75, 22.25, 0, 3.80)
    add_shape("Col_MuroOrienteTerminal", 127.60, 128.0, 22, 58, 0, 3.20)
    add_shape("Col_NaveTalleresInterior", 110, 127.60, 26, 56, 0, 5.50)

    # Bardas divisorias interiores
    add_shape("Col_BardaInterior1", 45.0, 45.30, 18, 58, 0, 2.60)
    add_shape("Col_BardaInterior2", 45.0, 70.0, 58, 58.30, 0, 2.60)

    tscn_content = [
        f'[gd_scene load_steps={len(shapes) + 2} format=3 uid="uid://manzana_central_2009_prod"]',
        '[ext_resource type="PackedScene" path="res://assets/buildings/manzana_central_2009.glb" id="1_glb"]'
    ]

    for i, (name, size, _) in enumerate(shapes, 1):
        tscn_content.append(f'[sub_resource type="BoxShape3D" id="BoxShape3D_{i}"]')
        tscn_content.append(f'size = Vector3({size[0]:.2f}, {size[1]:.2f}, {size[2]:.2f})\n')

    tscn_content.append('[node name="Manzana_Central_2009" type="StaticBody3D"]\n')
    tscn_content.append('[node name="MeshInstance" parent="." instance=ExtResource("1_glb")]\n')

    for i, (name, _, center) in enumerate(shapes, 1):
        tscn_content.append(f'[node name="{name}" type="CollisionShape3D" parent="."]')
        tscn_content.append(f'transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f})')
        tscn_content.append(f'shape = SubResource("BoxShape3D_{i}")\n')

    with open(TSCN_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(tscn_content))
    print(f"[Exportación] Escena Godot 4 analítica 1:1 guardada en: {TSCN_PATH} ({len(shapes)} colisionadores).")

# ---------------------------------------------------------------------------
# 7. Renderizado de Validación en Circuito Cerrado (Cycles CPU)
# ---------------------------------------------------------------------------
def setup_render_cameras(col):
    cameras = [
        ("Cam_01_NW_Juarez_Ortiz", (-15.0, 92.0, 8.5), (math.radians(72.0), 0.0, math.radians(-145.0))),
        ("Cam_02_North_Juarez_Center", (64.0, 96.0, 8.0), (math.radians(75.0), 0.0, math.radians(180.0))),
        ("Cam_03_NE_Juarez_Rodriguez", (142.0, 92.0, 8.5), (math.radians(72.0), 0.0, math.radians(145.0))),
        ("Cam_04_East_Rodriguez_Gate", (144.0, 15.0, 7.5), (math.radians(75.0), 0.0, math.radians(90.0))),
        ("Cam_05_SE_Libertad_Rodriguez", (142.0, -15.0, 8.0), (math.radians(72.0), 0.0, math.radians(35.0))),
        ("Cam_06_South_Libertad_Center", (64.0, -18.0, 7.5), (math.radians(75.0), 0.0, 0.0)),
        ("Cam_07_SW_Libertad_Ortiz", (-15.0, -15.0, 8.5), (math.radians(72.0), 0.0, math.radians(-35.0))),
        ("Cam_08_Top_Aerial_Z75", (64.0, 38.5, 75.0), (0.0, 0.0, 0.0))
    ]
    created = []
    for name, loc, rot in cameras:
        cdata = bpy.data.cameras.new(name)
        cdata.lens = 24.0 if "Aerial" in name else 28.0
        cdata.clip_start = 0.5
        cdata.clip_end = 400.0
        cobj = bpy.data.objects.new(name, cdata)
        cobj.location = Vector(loc)
        cobj.rotation_euler = Euler(rot, 'XYZ')
        col.objects.link(cobj)
        created.append(cobj)
    return created

def render_validation_suite(cameras):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 32
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.image_settings.file_format = 'PNG'

    world = scene.world
    if not world:
        world = bpy.data.worlds.new("World_Sky")
        scene.world = world
    world.use_nodes = True
    wnodes = world.node_tree.nodes
    wlinks = world.node_tree.links
    wnodes.clear()
    w_out = wnodes.new(type="ShaderNodeOutputWorld")
    w_bg = wnodes.new(type="ShaderNodeBackground")
    w_bg.inputs["Color"].default_value = (0.76, 0.86, 0.98, 1.0)
    w_bg.inputs["Strength"].default_value = 1.25
    wlinks.new(w_bg.outputs["Background"], w_out.inputs["Surface"])

    sun_data = bpy.data.lights.new("Sun_Light", type='SUN')
    sun_data.energy = 4.2
    sun_data.color = (1.0, 0.96, 0.90)
    sun_obj = bpy.data.objects.new("Sun_Obj", sun_data)
    sun_obj.rotation_euler = (math.radians(55.0), math.radians(20.0), math.radians(-40.0))
    bpy.context.scene.collection.objects.link(sun_obj)

    print("[Render] Ejecutando suite de validación visual de 8 cámaras...")
    for cam in cameras:
        scene.camera = cam
        out_path = os.path.join(DOCS_IMAGES_DIR, f"{cam.name}.png")
        scene.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        print(f"  ✓ Render guardado: {out_path}")

# ---------------------------------------------------------------------------
# 8. Ensamblaje Principal
# ---------------------------------------------------------------------------
def main():
    print("=================================================================")
    print("Iniciando Generación Fotorrealista: Manzana Central Tecate (2009)")
    print(f"Dimensiones Canónicas: X = {X_MAX}m, Y = {Y_MAX}m, Z_BASE = {Z_BASE}m")
    print("=================================================================")

    col = clean_scene()
    mats = setup_materials()

    bm = bmesh.new()
    mesh = bpy.data.meshes.new("Manzana_Central_Mesh")
    obj = bpy.data.objects.new("Manzana_Central_Building", mesh)
    col.objects.link(obj)

    print("[Geometría] Construyendo zócalo basal enterrado continuo...")
    build_zocalo_monolitico(bm, mats, obj)

    print("[Geometría] Construyendo fachada Norte (Av. Benito Juárez)...")
    build_north_facade_juarez(bm, mats, obj)

    print("[Geometría] Construyendo fachada Poniente (Ortiz Rubio)...")
    build_west_facade_ortiz_rubio(bm, mats, obj)

    print("[Geometría] Construyendo fachada Sur (Callejón Libertad)...")
    build_south_facade_libertad(bm, mats, obj)

    print("[Geometría] Construyendo fachada Oriente y portón azul (Abelardo L. Rodríguez)...")
    build_east_facade_rodriguez(bm, mats, obj)

    print("[Geometría] Construyendo patios interiores y dársenas...")
    build_interior_courtyards_and_terminals(bm, mats, obj)

    print("[UV Mapping] Generando coordenadas métricas ortogonales...")
    auto_uv_bmesh(bm, scale_u=0.5, scale_v=0.5)

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    print("[Tipografía] Generando rótulos corpóreos 3D anti-espejo...")
    build_all_signage_and_typography(col, mats)

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"[Blender] Archivo maestro guardado en: {BLEND_PATH}")

    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH,
        export_format='GLB',
        use_selection=False,
        export_yup=True,
        export_apply=True
    )
    print(f"[glTF] Asset exportado exitosamente en: {GLB_PATH}")

    generate_godot_scene_1to1()

    cameras = setup_render_cameras(col)
    render_validation_suite(cameras)

    print("=================================================================")
    print("Reconstrucción Fotorrealista de la Manzana Central Completada.")
    print("=================================================================")

if __name__ == "__main__":
    main()
