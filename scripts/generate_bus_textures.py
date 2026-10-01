"""
Generador de Texturas y Atlas Gráfico Fotorrealista para Autobús 'El Hongo' (Unidad 24)
Genera las texturas de alta resolución (PNG) mediante Blender Python y Cycles CPU:
  1. blender_assets/textures/bus_hongo_tex_left.png   (Costado Izquierdo)
  2. blender_assets/textures/bus_hongo_tex_right.png  (Costado Derecho)
  3. blender_assets/textures/bus_hongo_tex_rear.png   (Fachada Trasera Canónica)
  4. blender_assets/textures/bus_hongo_tex_front.png  (Rutero, Letreros y Placas)
"""

import bpy
import bmesh
import math
import os

TEXTURE_DIR = "blender_assets/textures"
os.makedirs(TEXTURE_DIR, exist_ok=True)

# Paleta cromática oficial fotorrealista (RGB lineal en Principled BSDF con Emisión)
COLOR_RED = (0.84, 0.04, 0.08, 1.0)       # Rojo Carmín Brillante Oficial (#D60A14)
COLOR_WHITE = (1.0, 1.0, 1.0, 1.0)         # Blanco Puro (#FFFFFF)
COLOR_NAVY = (0.004, 0.24, 0.31, 1.0)      # Azul Marino / Teal Oficial Hongo (#00384D)
COLOR_BLACK = (0.02, 0.02, 0.025, 1.0)      # Negro Moldura / Marcos (#050506)
COLOR_YELLOW = (0.98, 0.88, 0.22, 1.0)     # Amarillo Cartulina Ruta (#FADC38)
COLOR_CHROME = (0.92, 0.94, 0.96, 1.0)     # Cromo Rutero

def setup_canvas(width_px, height_px, aspect_ratio_x, aspect_ratio_y):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.render.resolution_x = width_px
    scene.render.resolution_y = height_px
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'

    cam_data = bpy.data.cameras.new("OrthoCam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = aspect_ratio_x
    cam_obj = bpy.data.objects.new("OrthoCam", cam_data)
    cam_obj.location = (aspect_ratio_x * 0.5, aspect_ratio_y * 0.5, 10.0)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    return scene

def make_emissive_mat(name, color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    em = nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = color
    em.inputs['Strength'].default_value = 1.0
    out = nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return mat

def add_plane(scene, x, y, w, h, z, mat):
    mesh = bpy.data.meshes.new("Plane")
    bm = bmesh.new()
    verts = [
        bm.verts.new((x, y, z)),
        bm.verts.new((x + w, y, z)),
        bm.verts.new((x + w, y + h, z)),
        bm.verts.new((x, y + h, z))
    ]
    bm.faces.new(verts)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("PlaneObj", mesh)
    obj.data.materials.append(mat)
    scene.collection.objects.link(obj)
    return obj

def add_disk(scene, cx, cy, radius, z, mat, segments=64):
    mesh = bpy.data.meshes.new("Disk")
    bm = bmesh.new()
    center_v = bm.verts.new((cx, cy, z))
    ring_verts = []
    for i in range(segments):
        ang = 2.0 * math.pi * i / segments
        vx = cx + math.cos(ang) * radius
        vy = cy + math.sin(ang) * radius
        ring_verts.append(bm.verts.new((vx, vy, z)))
    for i in range(segments):
        i_next = (i + 1) % segments
        bm.faces.new((center_v, ring_verts[i], ring_verts[i_next]))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("DiskObj", mesh)
    obj.data.materials.append(mat)
    scene.collection.objects.link(obj)
    return obj

def add_text(scene, text_str, cx, cy, size, z, mat, align_x='CENTER', align_y='CENTER', bold=True, offset=0.0):
    curve = bpy.data.curves.new(name="TextCurve", type='FONT')
    curve.body = text_str
    curve.size = size
    curve.align_x = align_x
    curve.align_y = align_y
    if offset > 0.0:
        curve.offset = offset
    elif bold:
        curve.shear = 0.0
    obj = bpy.data.objects.new("TextObj", curve)
    obj.location = (cx, cy, z)
    obj.data.materials.append(mat)
    scene.collection.objects.link(obj)
    return obj

def add_hongo_logo(scene, cx, cy, circle_radius, z_base, mat_white, mat_red, mat_navy):
    # 1. Círculo blanco grande
    add_disk(scene, cx, cy, circle_radius, z_base, mat_white)

    # 2. Tipografía Canónica Oficial "EL HONGO"
    # - "EL" es BLANCO sobre el fondo rojo (a la izquierda del círculo blanco)
    # - "HONGO" es 100% AZUL MARINO/TEAL (#00384D)
    # - Las dos letras "O" cabalgan sobre los perímetros opuestos del círculo blanco: mitad adentro y mitad afuera
    # - 'N' y 'G' van 100% en el interior blanco; 'H' y 'EL' van a la izquierda sobre el rojo
    fsize = circle_radius * 0.76
    y_txt = cy - fsize * 0.08
    spacing = 2.0 * circle_radius / 3.0  # Distancia uniforme entre O1 y O2 repartida en 3 tramos (O-N, N-G, G-O)

    # Letras de "HONGO" en azul marino íntegro
    add_text(scene, "O", cx - circle_radius, y_txt, fsize, z_base + 0.02, mat_navy, offset=0.012)
    add_text(scene, "N", cx - circle_radius + spacing, y_txt, fsize, z_base + 0.02, mat_navy, offset=0.012)
    add_text(scene, "G", cx - circle_radius + 2.0 * spacing, y_txt, fsize, z_base + 0.02, mat_navy, offset=0.012)
    add_text(scene, "O", cx + circle_radius, y_txt, fsize, z_base + 0.02, mat_navy, offset=0.012)
    add_text(scene, "H", cx - circle_radius - spacing * 0.90, y_txt, fsize, z_base + 0.02, mat_navy, offset=0.012)

    # "EL" en blanco sobre el fondo rojo exterior
    add_text(scene, "EL", cx - circle_radius - spacing * 2.05, y_txt, fsize, z_base + 0.02, mat_white, offset=0.012)

# ===========================================================================
# 1. GENERACIÓN: COSTADO IZQUIERDO (LADO CHOFER)
# ===========================================================================
def generate_texture_left():
    W, H = 2048, 512
    CW, CH = 9.80, 2.45
    scene = setup_canvas(W, H, CW, CH)

    m_red = make_emissive_mat("Red", COLOR_RED)
    m_white = make_emissive_mat("White", COLOR_WHITE)
    m_navy = make_emissive_mat("Navy", COLOR_NAVY)

    # Fondo Rojo Canónico
    add_plane(scene, 0, 0, CW, CH, 0.0, m_red)

    # Gran círculo principal con logotipo "EL HONGO"
    # Centrado perfectamente en el entre-eje (delantero X ~ 2.25, trasero X ~ 7.10)
    # Con r = 0.90, el logotipo mide ~3.0m de ancho y respeta holgura de 25cm a ambos lados de salpicaderas
    r_main = 0.90
    cx_main = 5.25
    cy_main = 0.82
    add_hongo_logo(scene, cx_main, cy_main, r_main, 0.01, m_white, m_red, m_navy)

    # Polka dots circundantes canónicos sin interferir con la tipografía (bus-hongo-izquierda.jpeg)
    dots = [
        (1.20, 1.50, 0.28),   # Bajo ventana chofer
        (1.85, 0.55, 0.38),   # Salpicadera delantera
        (2.45, 1.55, 0.36),   # Sobre arco de rueda delantero
        (4.45, 0.18, 0.24),   # Faldón inferior bajo la 'O'
        (6.75, 1.35, 0.55),   # Círculo mediano sobre rueda trasera
        (7.65, 0.85, 0.65),   # Gran círculo trasero tras el eje
        (8.55, 1.55, 0.42),   # Trasero superior
        (9.15, 0.70, 0.32),   # Extremo trasero
    ]
    for dx, dy, dr in dots:
        add_disk(scene, dx, dy, dr, 0.01, m_white)

    # Franja superior de razón social: autotransporte urbano y suburbano S.A. de C.V.
    add_text(scene, "autotransporte urbano y suburbano S.A. de C.V.", 5.20, 2.22, 0.105, 0.02, m_white, align_x='CENTER')

    # Rótulo de unidad "24" en círculo blanco con texto azul marino en la parte delantera inferior
    add_disk(scene, 1.25, 0.52, 0.22, 0.02, m_white)
    add_text(scene, "24", 1.25, 0.52, 0.26, 0.03, m_navy, align_x='CENTER', offset=0.01)

    out_path = os.path.join(TEXTURE_DIR, "bus_hongo_tex_left.png")
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f"-> Textura Costado Izquierdo generada: {out_path}")

# ===========================================================================
# 2. GENERACIÓN: COSTADO DERECHO (LADO PUERTAS)
# ===========================================================================
def generate_texture_right():
    W, H = 2048, 512
    CW, CH = 9.80, 2.45
    scene = setup_canvas(W, H, CW, CH)

    m_red = make_emissive_mat("Red", COLOR_RED)
    m_white = make_emissive_mat("White", COLOR_WHITE)
    m_navy = make_emissive_mat("Navy", COLOR_NAVY)

    # Fondo Rojo Canónico
    add_plane(scene, 0, 0, CW, CH, 0.0, m_red)

    # En el costado derecho, el círculo se sitúa en el entre-eje (X = 3.05 a 6.60)
    # Con r = 0.90, "EL HONGO" queda equilibrado y no colisiona con guardafangos: cx = 5.35
    r_main = 0.90
    cx_main = 5.35
    cy_main = 0.82
    add_hongo_logo(scene, cx_main, cy_main, r_main, 0.01, m_white, m_red, m_navy)

    # Polka dots laterales derechos (referencia bus-hongo-derecha.jpeg)
    dots = [
        (0.85, 1.55, 0.32),   # Alto sobre puerta trasera
        (1.50, 0.40, 0.26),   # Faldón bajo puerta trasera
        (2.40, 1.45, 0.38),   # Sobre arco de rueda trasero
        (4.45, 0.18, 0.24),   # Faldón bajo la 'O'
        (6.75, 1.40, 0.48),   # Alto delante del círculo
        (7.45, 0.85, 0.45),   # Sobre arco de rueda delantero
        (8.95, 0.50, 0.28),   # Faldón frontal bajo puerta delantera
    ]
    for dx, dy, dr in dots:
        add_disk(scene, dx, dy, dr, 0.01, m_white)

    # Franja superior de razón social
    add_text(scene, "autotransporte urbano y suburbano S.A. de C.V.", 5.00, 2.22, 0.105, 0.02, m_white, align_x='CENTER')

    # Número 24 en círculo blanco con texto azul marino en la puerta delantera (hacia el frente, X ~ 8.4)
    add_disk(scene, 8.40, 0.48, 0.22, 0.02, m_white)
    add_text(scene, "24", 8.40, 0.48, 0.26, 0.03, m_navy, align_x='CENTER', offset=0.01)

    out_path = os.path.join(TEXTURE_DIR, "bus_hongo_tex_right.png")
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f"-> Textura Costado Derecho generada: {out_path}")

# ===========================================================================
# 3. GENERACIÓN: FACHADA TRASERA (CANÓNICA SEGÚN FOTO bus-hongo-reverso.jpeg)
# ===========================================================================
def generate_texture_rear():
    W, H = 1024, 1024
    CW, CH = 2.50, 2.50
    scene = setup_canvas(W, H, CW, CH)

    m_red = make_emissive_mat("Red", COLOR_RED)
    m_white = make_emissive_mat("White", COLOR_WHITE)
    m_navy = make_emissive_mat("Navy", COLOR_NAVY)
    m_black = make_emissive_mat("Black", COLOR_BLACK)

    # Fondo Rojo Superior
    add_plane(scene, 0, 0, CW, CH, 0.0, m_red)

    # Mitad inferior blanca con corte ondulado característico
    add_plane(scene, 0, 0, CW, 1.15, 0.01, m_white)
    # Ondas ascendentes laterales
    add_disk(scene, 0.35, 1.15, 0.45, 0.015, m_white)
    add_disk(scene, CW - 0.35, 1.15, 0.45, 0.015, m_white)

    # Gran círculo blanco central en la mitad superior roja
    cx_rear = 1.25
    cy_rear = 1.82
    r_rear = 0.38
    add_hongo_logo(scene, cx_rear, cy_rear, r_rear, 0.02, m_white, m_red, m_navy)

    # Círculo blanco con número "24" en azul marino a la derecha inferior del círculo principal
    add_disk(scene, cx_rear + r_rear + 0.26, cy_rear - 0.16, 0.13, 0.03, m_white)
    add_text(scene, "24", cx_rear + r_rear + 0.26, cy_rear - 0.16, 0.16, 0.04, m_navy, align_x='CENTER', offset=0.01)

    # Lunares blancos satélite traseros
    rear_dots = [
        (0.40, 2.25, 0.18),
        (0.30, 1.65, 0.14),
        (2.15, 2.20, 0.16),
        (2.20, 1.55, 0.12),
        (0.65, 1.35, 0.22),
    ]
    for rx, ry, rr in rear_dots:
        add_disk(scene, rx, ry, rr, 0.02, m_white)

    # Textos institucionales sobre el faldón blanco
    add_text(scene, "EL HONGO", cx_rear, 1.20, 0.08, 0.03, m_navy, align_x='CENTER')
    add_text(scene, "autotransporte urbano y suburbano S.A. de C.V.", cx_rear, 1.08, 0.052, 0.03, m_navy, align_x='CENTER')

    # Placa oficial metálica de Baja California
    placa_w = 0.44
    placa_h = 0.22
    placa_x = cx_rear - placa_w * 0.5
    placa_y = 0.65
    add_plane(scene, placa_x - 0.02, placa_y - 0.02, placa_w + 0.04, placa_h + 0.04, 0.03, m_black)
    add_plane(scene, placa_x, placa_y, placa_w, placa_h, 0.035, m_white)
    # Franja azul superior de BC
    add_plane(scene, placa_x, placa_y + placa_h - 0.04, placa_w, 0.04, 0.04, m_navy)
    add_text(scene, "BAJA CALIFORNIA", cx_rear, placa_y + placa_h - 0.022, 0.026, 0.045, m_white, align_x='CENTER')
    add_text(scene, "A-30530-A", cx_rear, placa_y + 0.07, 0.075, 0.045, m_black, align_x='CENTER')

    # Concesión oficial y marca Mercedes-Benz
    add_text(scene, "Mercedes-Benz", cx_rear + 0.45, 0.58, 0.042, 0.03, m_black, align_x='CENTER')
    # Franja roja con número de concesión
    add_plane(scene, cx_rear - 0.55, 0.42, 1.10, 0.12, 0.03, m_red)
    add_text(scene, "TKT-A-19-00006", cx_rear, 0.48, 0.07, 0.04, m_white, align_x='CENTER')

    # Franjas diagonales rojas decorativas de precaución en la defensa izquierda (según foto bus-hongo-reverso.jpeg)
    for sx in [0.26, 0.38]:
        mesh_diag = bpy.data.meshes.new("DiagStripe")
        bm_diag = bmesh.new()
        sw, sh, slant = 0.035, 0.12, 0.04
        v0 = bm_diag.verts.new((sx, 0.04, 0.03))
        v1 = bm_diag.verts.new((sx + sw, 0.04, 0.03))
        v2 = bm_diag.verts.new((sx + sw + slant, 0.04 + sh, 0.03))
        v3 = bm_diag.verts.new((sx + slant, 0.04 + sh, 0.03))
        bm_diag.faces.new((v0, v1, v2, v3))
        bm_diag.to_mesh(mesh_diag)
        bm_diag.free()
        obj_diag = bpy.data.objects.new("DiagStripeObj", mesh_diag)
        obj_diag.data.materials.append(m_red)
        scene.collection.objects.link(obj_diag)

    out_path = os.path.join(TEXTURE_DIR, "bus_hongo_tex_rear.png")
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f"-> Textura Fachada Trasera generada: {out_path}")

# ===========================================================================
# 4. GENERACIÓN: RUTERO, LETREROS DE PARABRISAS Y PLACA DELANTERA
# ===========================================================================
def generate_texture_front_sign():
    W, H = 1024, 512
    CW, CH = 2.0, 1.0
    scene = setup_canvas(W, H, CW, CH)

    m_black = make_emissive_mat("Black", COLOR_BLACK)
    m_white = make_emissive_mat("White", COLOR_WHITE)
    m_yellow = make_emissive_mat("Yellow", COLOR_YELLOW)
    m_red = make_emissive_mat("Red", COLOR_RED)

    # Fondo general negro
    add_plane(scene, 0, 0, CW, CH, 0.0, m_black)

    # 1. Pantalla del Rutero Superior (mitad superior Y: 0.55 a 0.95)
    add_plane(scene, 0.05, 0.55, 1.90, 0.38, 0.01, m_black)
    add_text(scene, "TECATE   EL HONGO   LA RUMOROSA", 1.0, 0.74, 0.088, 0.02, m_white, align_x='CENTER')

    # 2. Cartulina amarilla de ruta (mitad inferior izquierda Y: 0.05 a 0.50, X: 0.05 a 0.90)
    add_plane(scene, 0.05, 0.05, 0.85, 0.45, 0.01, m_yellow)
    lineas_amarilla = [
        ("TECATE", 0.42, 0.075, m_red),
        ("CFE", 0.33, 0.065, m_black),
        ("COBACH", 0.25, 0.065, m_black),
        ("AV. HIDALGO", 0.17, 0.060, m_black),
        ("VILLAS DEL CAMPO", 0.09, 0.055, m_red)
    ]
    for txt, ly, lsize, lmat in lineas_amarilla:
        add_text(scene, txt, 0.475, ly, lsize, 0.02, lmat, align_x='CENTER')

    # 3. Cartulina blanca de destino secundario (X: 1.00 a 1.50)
    add_plane(scene, 0.98, 0.05, 0.50, 0.45, 0.01, m_white)
    add_text(scene, "VILLAS DEL", 1.23, 0.32, 0.065, 0.02, m_red, align_x='CENTER')
    add_text(scene, "CAMPO", 1.23, 0.18, 0.065, 0.02, m_red, align_x='CENTER')

    # 4. Placa delantera "A-30531-A" (X: 1.55 a 1.95)
    add_plane(scene, 1.54, 0.10, 0.42, 0.25, 0.01, m_white)
    add_plane(scene, 1.54, 0.30, 0.42, 0.05, 0.02, m_red)
    add_text(scene, "BAJA CALIFORNIA", 1.75, 0.325, 0.025, 0.03, m_white, align_x='CENTER')
    add_text(scene, "A-30531-A", 1.75, 0.18, 0.070, 0.03, m_black, align_x='CENTER')

    out_path = os.path.join(TEXTURE_DIR, "bus_hongo_tex_front.png")
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f"-> Textura Rutero y Letreros generada: {out_path}")

def main():
    print("=== GENERANDO TEXTURAS CANÓNICAS OFICIALES AUTOBÚS EL HONGO ===")
    generate_texture_left()
    generate_texture_right()
    generate_texture_rear()
    generate_texture_front_sign()
    print("=== GENERACIÓN DE TEXTURAS COMPLETADA ===")

if __name__ == "__main__":
    main()
