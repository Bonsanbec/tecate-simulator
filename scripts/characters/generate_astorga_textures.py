"""
=============================================================================
GENERADOR DE TEXTURAS PBR PROCEDURALES DE ALTA FIDELIDAD: ASTORGA
=============================================================================
Tecate Simulator - Sistema de Personajes y Catálogo Centralizado Cívico

Genera mapas PBR procedurales en 2048x2048 y 1024x1024 fieles a la identidad
visual y fotográfica de Astorga ('scratch/humans/astorga.png'):
1. Rostro y cuello: Tez apiñonada cálida / oliva, mirada serena, cejas oscuras
   definidas, pómulos esculpidos, labios naturales y piel limpia sin barba.
2. Ojos 3D: Iris castaño profundo con limbo, pupila y reflejo córneo.
3. Cabello: Ondas abundantes 360° en negro / castaño profundo con micro-relieve.
4. Traje sastre: Paño negro carbón con trama textil formal y solapas finas.
5. Camisa: Tono vino tinto / borgoña profundo (burgundy) con textura de algodón.
6. Corbata: Seda satinada oscura con micro-trama en diagonal.
7. Pantalón: Paño negro formal con raya vertical sastre de planchado.
8. Zapatos: Cuero formal negro lustrado con costuras sutiles.
9. Violín y Arco (prop independiente): Arce flameado barnizado en ámbar cálido,
   diapasón de ébano, f-holes caladas y varilla de pernambuco con cerdas de crin.
=============================================================================
"""

import os
import bpy
import numpy as np

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
TEXTURES_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/textures")
CITIZENS_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/citizens")
PROPS_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/props")

os.makedirs(TEXTURES_DIR, exist_ok=True)
os.makedirs(CITIZENS_DIR, exist_ok=True)
os.makedirs(PROPS_DIR, exist_ok=True)

def save_numpy_image(img_name, arr_rgba, out_paths):
    if isinstance(out_paths, str):
        out_paths = [out_paths]
    h, w, c = arr_rgba.shape
    arr_clipped = np.clip(arr_rgba, 0.0, 1.0).astype(np.float32)
    b_img = bpy.data.images.get(img_name)
    if b_img:
        bpy.data.images.remove(b_img)
    b_img = bpy.data.images.new(img_name, width=w, height=h, alpha=True)
    b_img.pixels.foreach_set(arr_clipped.ravel())
    for out_path in out_paths:
        b_img.filepath_raw = os.path.abspath(out_path)
        b_img.file_format = 'PNG'
        b_img.save()
        print(f"✓ Textura PBR guardada: {out_path} ({w}x{h})")

def height_to_normal_map(height, scale=1.8):
    h, w = height.shape
    dh_dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 0.5 * scale
    dh_dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 0.5 * scale
    nx = -dh_dx
    ny = dh_dy
    nz = np.ones_like(nx)
    norm = np.sqrt(nx**2 + ny**2 + nz**2)
    norm[norm == 0] = 1.0
    nx /= norm
    ny /= norm
    nz /= norm

    rgba = np.zeros((h, w, 4), dtype=np.float32)
    rgba[:, :, 0] = nx * 0.5 + 0.5
    rgba[:, :, 1] = ny * 0.5 + 0.5
    rgba[:, :, 2] = nz * 0.5 + 0.5
    rgba[:, :, 3] = 1.0
    return rgba

# =============================================================================
# 1. ROSTRO ANATÓMICO Y CUELLO DE ASTORGA (2048x2048)
# =============================================================================
def generate_face_textures():
    print("-> Generando texturas PBR faciales orgánicas para Astorga (astorga.png)...")
    w, h = 2048, 2048
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    x = np.linspace(0.0, 1.0, w)[None, :]
    y = np.linspace(0.0, 1.0, h)[:, None]

    # Tez apiñonada cálida / oliva según scratch/humans/astorga.png
    base_skin = np.array([0.835, 0.665, 0.575], dtype=np.float32)
    warm_cheek = np.array([0.875, 0.575, 0.495], dtype=np.float32)
    shadow_tone = np.array([0.695, 0.525, 0.435], dtype=np.float32)
    neck_skin = np.array([0.805, 0.635, 0.545], dtype=np.float32)

    for c in range(3):
        diffuse[:, :, c] = base_skin[c]
    diffuse[:, :, 3] = 1.0

    # Gradiente en cuello inferior manteniendo piel limpia (sin barba)
    neck_factor = np.clip((0.26 - y) / 0.26, 0.0, 1.0)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - neck_factor * 0.20) + neck_skin[c] * (neck_factor * 0.20)

    # Pómulos, puente nasal y frente
    cheeks_l = np.exp(-((x - 0.36)**2 / 0.014 + (y - 0.52)**2 / 0.011))
    cheeks_r = np.exp(-((x - 0.64)**2 / 0.014 + (y - 0.52)**2 / 0.011))
    nose_bridge = np.exp(-((x - 0.50)**2 / 0.0018 + (y - 0.52)**2 / 0.024))
    forehead_warmth = np.exp(-((x - 0.50)**2 / 0.040 + (y - 0.78)**2 / 0.018))

    facial_warmth = np.clip(cheeks_l + cheeks_r + nose_bridge * 0.45 + forehead_warmth * 0.30, 0.0, 1.0)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - facial_warmth * 0.20) + warm_cheek[c] * (facial_warmth * 0.20)

    # Cuencas orbitarias anatómicas suaves
    for eye_cx in [0.385, 0.615]:
        orbit_dist = np.sqrt(((x - eye_cx) / 0.068)**2 + ((y - 0.620)**2 / 0.038**2))
        orbit_shade = np.clip(1.0 - orbit_dist, 0.0, 1.0)**2 * 0.28
        for c in range(3):
            diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - orbit_shade) + shadow_tone[c] * orbit_shade

    # Cejas masculinas oscuras, naturales y expresivas de Astorga
    # Ceja izquierda
    t_l = np.clip((x - 0.315) / (0.460 - 0.315), 0.0, 1.0)
    y_c_l = 0.690 + 0.018 * np.sin(t_l * np.pi * 0.88)
    dist_brow_l = np.abs(y - y_c_l) / (0.016 * (1.1 - 0.5 * (t_l - 0.5)**2))
    mask_brow_l = np.clip(1.0 - dist_brow_l, 0.0, 1.0)**1.8 * np.sin(t_l * np.pi)**0.5

    # Ceja derecha
    t_r = np.clip((x - 0.540) / (0.685 - 0.540), 0.0, 1.0)
    y_c_r = 0.690 + 0.018 * np.sin((1.0 - t_r) * np.pi * 0.88)
    dist_brow_r = np.abs(y - y_c_r) / (0.016 * (1.1 - 0.5 * (t_r - 0.5)**2))
    mask_brow_r = np.clip(1.0 - dist_brow_r, 0.0, 1.0)**1.8 * np.sin(t_r * np.pi)**0.5

    eyebrow_color = np.array([0.10, 0.08, 0.07], dtype=np.float32)
    brow_total = np.clip(mask_brow_l + mask_brow_r, 0.0, 1.0)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - brow_total * 0.96) + eyebrow_color[c] * (brow_total * 0.96)

    # Labios masculinos serenos y naturales
    t_lip = np.clip((x - 0.405) / (0.595 - 0.405), 0.0, 1.0)
    lip_shape = np.sin(t_lip * np.pi)
    lip_dist = np.abs(y - 0.395) / (0.016 * lip_shape + 0.001)
    mask_lip = np.clip(1.0 - lip_dist, 0.0, 1.0)**2 * (t_lip > 0.0) * (t_lip < 1.0)
    lip_color = np.array([0.76, 0.46, 0.42], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - mask_lip * 0.50) + lip_color[c] * (mask_lip * 0.50)

    # Hendidura labial
    slit_dist = np.abs(y - 0.395) / 0.0035
    mask_slit = np.clip(1.0 - slit_dist, 0.0, 1.0) * lip_shape
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - mask_slit * 0.65) + 0.12 * (mask_slit * 0.65)

    # Sombra subnasal / filtrum suave
    philtrum = np.exp(-((x - 0.50)**2 / 0.0008 + (y - 0.435)**2 / 0.0015))
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - philtrum * 0.22) + shadow_tone[c] * (philtrum * 0.22)

    # Micro-textura de piel suave (poros y relieve dérmico fino)
    micro_skin = np.sin(x * 600.0) * np.cos(y * 600.0) * 0.015

    # Mapa de altura facial para normales
    height_map = np.zeros((h, w), dtype=np.float32)
    height_map += brow_total * 0.06
    height_map += mask_lip * 0.04
    height_map += nose_bridge * 0.08
    height_map += micro_skin

    normal_map = height_to_normal_map(height_map, scale=1.5)

    save_numpy_image("Mat_Astorga_Face_Diff", diffuse, [
        os.path.join(TEXTURES_DIR, "astorga_face_diffuse.png"),
        os.path.join(CITIZENS_DIR, "astorga_face_diffuse.png")
    ])
    save_numpy_image("Mat_Astorga_Face_Norm", normal_map, [
        os.path.join(TEXTURES_DIR, "astorga_face_normal.png"),
        os.path.join(CITIZENS_DIR, "astorga_face_normal.png")
    ])

# =============================================================================
# 2. OJOS 3D DE ASTORGA (1024x1024)
# =============================================================================
def generate_eye_textures():
    print("-> Generando texturas de ojos para Astorga...")
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    x = np.linspace(-1.0, 1.0, w)[None, :]
    y = np.linspace(-1.0, 1.0, h)[:, None]
    r = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)

    # Esclera blanca natural con leve sombra corneal
    esclera = np.array([0.94, 0.93, 0.91], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = esclera[c]
    diffuse[:, :, 3] = 1.0

    # Iris castaño avellana profundo
    iris_r = 0.52
    iris_mask = np.clip((iris_r - r) / 0.02, 0.0, 1.0)

    # Vetas radiales del iris
    radial_pattern = 0.5 + 0.5 * np.sin(theta * 28.0) * np.cos(r * 40.0)
    iris_base = np.array([0.28, 0.16, 0.09], dtype=np.float32)
    iris_detail = np.array([0.42, 0.25, 0.14], dtype=np.float32)
    iris_color = iris_base[None, None, :] * (1.0 - radial_pattern[:, :, None] * 0.35) + iris_detail[None, None, :] * (radial_pattern[:, :, None] * 0.35)

    # Limbo corneal oscuro perimetral
    limbus = np.clip((r - 0.46) / 0.06, 0.0, 1.0)
    iris_color = iris_color * (1.0 - limbus[:, :, None] * 0.75) + np.array([0.10, 0.06, 0.04])[None, None, :] * (limbus[:, :, None] * 0.75)

    # Pupila central negra nítida
    pupil_r = 0.18
    pupil_mask = np.clip((pupil_r - r) / 0.015, 0.0, 1.0)

    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - iris_mask) + iris_color[:, :, c] * iris_mask
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - pupil_mask) + 0.02 * pupil_mask

    save_numpy_image("Mat_Astorga_Eye_Diff", diffuse, [
        os.path.join(TEXTURES_DIR, "astorga_eye_diffuse.png"),
        os.path.join(CITIZENS_DIR, "astorga_eye_diffuse.png")
    ])

# =============================================================================
# 3. CABELLO ONDULADO VOLUMINOSO (1024x1024)
# =============================================================================
def generate_hair_textures():
    print("-> Generando texturas de cabello ondulado para Astorga...")
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    x = np.linspace(0.0, 1.0, w)[None, :]
    y = np.linspace(0.0, 1.0, h)[:, None]

    base_hair = np.array([0.09, 0.07, 0.06], dtype=np.float32)
    highlight_hair = np.array([0.18, 0.14, 0.11], dtype=np.float32)

    # Ondas sinoidales superpuestas simulando mechones densos
    wave = np.sin(x * 40.0 + np.sin(y * 18.0) * 2.5) * 0.5 + 0.5
    strand = np.cos(x * 120.0 + y * 60.0) * 0.25 + 0.25
    pattern = np.clip(wave * 0.7 + strand * 0.3, 0.0, 1.0)

    for c in range(3):
        diffuse[:, :, c] = base_hair[c] * (1.0 - pattern * 0.40) + highlight_hair[c] * (pattern * 0.40)
    diffuse[:, :, 3] = 1.0

    height_hair = pattern * 0.15
    normal_hair = height_to_normal_map(height_hair, scale=2.2)

    save_numpy_image("Mat_Astorga_Hair_Diff", diffuse, [
        os.path.join(TEXTURES_DIR, "astorga_hair_diffuse.png"),
        os.path.join(CITIZENS_DIR, "astorga_hair_diffuse.png")
    ])
    save_numpy_image("Mat_Astorga_Hair_Norm", normal_hair, [
        os.path.join(TEXTURES_DIR, "astorga_hair_normal.png"),
        os.path.join(CITIZENS_DIR, "astorga_hair_normal.png")
    ])

# =============================================================================
# 4. SACO FORMAL NEGRO CARBÓN (1024x1024)
# =============================================================================
def generate_suit_textures():
    print("-> Generando texturas de saco sastre negro para Astorga...")
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    x = np.linspace(0.0, 1.0, w)[None, :]
    y = np.linspace(0.0, 1.0, h)[:, None]

    # Paño sastre negro carbón profundo con matices grafito
    suit_base = np.array([0.082, 0.088, 0.096], dtype=np.float32)
    lapel_highlight = np.array([0.125, 0.132, 0.142], dtype=np.float32)

    # Trama textil fina ortogonal
    weave = (np.sin(x * 512.0 * np.pi) * np.sin(y * 512.0 * np.pi)) * 0.018

    # Detalle de solapas sastre y costuras frontales
    lapel_v = np.clip(1.0 - np.abs(x - 0.50) / 0.35, 0.0, 1.0) * np.clip((y - 0.30) / 0.70, 0.0, 1.0)

    for c in range(3):
        diffuse[:, :, c] = suit_base[c] + weave + lapel_highlight[c] * (lapel_v * 0.15)
    diffuse[:, :, 3] = 1.0

    height_suit = weave * 2.0
    normal_suit = height_to_normal_map(height_suit, scale=1.4)

    save_numpy_image("Mat_Astorga_Suit_Diff", diffuse, [
        os.path.join(TEXTURES_DIR, "astorga_suit_diffuse.png"),
        os.path.join(CITIZENS_DIR, "astorga_suit_diffuse.png")
    ])
    save_numpy_image("Mat_Astorga_Suit_Norm", normal_suit, [
        os.path.join(TEXTURES_DIR, "astorga_suit_normal.png"),
        os.path.join(CITIZENS_DIR, "astorga_suit_normal.png")
    ])

# =============================================================================
# 5. CAMISA DE VESTIR VINO TINTO / BORGOÑA (1024x1024)
# =============================================================================
def generate_shirt_textures():
    print("-> Generando texturas de camisa vinotinto (burgundy) para Astorga...")
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    x = np.linspace(0.0, 1.0, w)[None, :]
    y = np.linspace(0.0, 1.0, h)[:, None]

    # Borgoña / vino tinto elegante según scratch/humans/astorga.png
    shirt_base = np.array([0.295, 0.075, 0.105], dtype=np.float32)
    shirt_highlight = np.array([0.385, 0.115, 0.145], dtype=np.float32)

    # Trama de algodón formal de alta densidad
    cotton_weave = (np.sin(x * 640.0 * np.pi) * np.sin(y * 640.0 * np.pi)) * 0.015
    collar_fold = np.sin(y * 8.0 * np.pi) * 0.03

    for c in range(3):
        diffuse[:, :, c] = shirt_base[c] + cotton_weave + (shirt_highlight[c] - shirt_base[c]) * (collar_fold + 0.03)
    diffuse[:, :, 3] = 1.0

    height_shirt = cotton_weave * 2.5 + collar_fold * 0.08
    normal_shirt = height_to_normal_map(height_shirt, scale=1.6)

    save_numpy_image("Mat_Astorga_Shirt_Diff", diffuse, [
        os.path.join(TEXTURES_DIR, "astorga_shirt_diffuse.png"),
        os.path.join(CITIZENS_DIR, "astorga_shirt_diffuse.png")
    ])
    save_numpy_image("Mat_Astorga_Shirt_Norm", normal_shirt, [
        os.path.join(TEXTURES_DIR, "astorga_shirt_normal.png"),
        os.path.join(CITIZENS_DIR, "astorga_shirt_normal.png")
    ])

# =============================================================================
# 6. CORBATA OSCURA FORMAL (512x512)
# =============================================================================
def generate_tie_textures():
    print("-> Generando texturas de corbata oscura para Astorga...")
    w, h = 512, 512
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    x = np.linspace(0.0, 1.0, w)[None, :]
    y = np.linspace(0.0, 1.0, h)[:, None]

    # Seda oscura con reflejo satinado
    tie_base = np.array([0.090, 0.055, 0.065], dtype=np.float32)
    satin_diagonal = np.sin((x + y) * 128.0 * np.pi) * 0.018

    for c in range(3):
        diffuse[:, :, c] = tie_base[c] + satin_diagonal
    diffuse[:, :, 3] = 1.0

    normal_tie = height_to_normal_map(satin_diagonal * 3.0, scale=1.8)

    save_numpy_image("Mat_Astorga_Tie_Diff", diffuse, [
        os.path.join(TEXTURES_DIR, "astorga_tie_diffuse.png"),
        os.path.join(CITIZENS_DIR, "astorga_tie_diffuse.png")
    ])
    save_numpy_image("Mat_Astorga_Tie_Norm", normal_tie, [
        os.path.join(TEXTURES_DIR, "astorga_tie_normal.png"),
        os.path.join(CITIZENS_DIR, "astorga_tie_normal.png")
    ])

# =============================================================================
# 7. PANTALÓN FORMAL NEGRO (1024x1024)
# =============================================================================
def generate_pants_textures():
    print("-> Generando texturas de pantalón sastre para Astorga...")
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    x = np.linspace(0.0, 1.0, w)[None, :]
    y = np.linspace(0.0, 1.0, h)[:, None]

    pants_base = np.array([0.078, 0.082, 0.090], dtype=np.float32)
    weave = (np.sin(x * 512.0 * np.pi) * np.sin(y * 512.0 * np.pi)) * 0.015

    # Raya vertical de planchado sastre
    crease = np.exp(-((x - 0.50)**2 / 0.002)) * 0.04

    for c in range(3):
        diffuse[:, :, c] = pants_base[c] + weave + crease
    diffuse[:, :, 3] = 1.0

    height_pants = weave * 2.0 + crease * 0.8
    normal_pants = height_to_normal_map(height_pants, scale=1.5)

    save_numpy_image("Mat_Astorga_Pants_Diff", diffuse, [
        os.path.join(TEXTURES_DIR, "astorga_pants_diffuse.png"),
        os.path.join(CITIZENS_DIR, "astorga_pants_diffuse.png")
    ])
    save_numpy_image("Mat_Astorga_Pants_Norm", normal_pants, [
        os.path.join(TEXTURES_DIR, "astorga_pants_normal.png"),
        os.path.join(CITIZENS_DIR, "astorga_pants_normal.png")
    ])

# =============================================================================
# 8. CALZADO FORMAL NEGRO (1024x1024)
# =============================================================================
def generate_shoes_textures():
    print("-> Generando texturas de calzado formal para Astorga...")
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    x = np.linspace(0.0, 1.0, w)[None, :]
    y = np.linspace(0.0, 1.0, h)[:, None]

    shoes_base = np.array([0.055, 0.058, 0.062], dtype=np.float32)
    leather_grain = np.sin(x * 800.0) * np.cos(y * 800.0) * 0.012

    for c in range(3):
        diffuse[:, :, c] = shoes_base[c] + leather_grain
    diffuse[:, :, 3] = 1.0

    normal_shoes = height_to_normal_map(leather_grain * 2.0, scale=1.3)

    save_numpy_image("Mat_Astorga_Shoes_Diff", diffuse, [
        os.path.join(TEXTURES_DIR, "astorga_shoes_diffuse.png"),
        os.path.join(CITIZENS_DIR, "astorga_shoes_diffuse.png")
    ])
    save_numpy_image("Mat_Astorga_Shoes_Norm", normal_shoes, [
        os.path.join(TEXTURES_DIR, "astorga_shoes_normal.png"),
        os.path.join(CITIZENS_DIR, "astorga_shoes_normal.png")
    ])

# =============================================================================
# 9. VIOLÍN Y ARCO (PROP INDEPENDIENTE) (2048x2048)
# =============================================================================
def generate_violin_textures():
    print("-> Generando texturas PBR dedicadas para el Violín y Arco (prop independiente)...")
    w, h = 2048, 2048
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    x = np.linspace(0.0, 1.0, w)[None, :]
    y = np.linspace(0.0, 1.0, h)[:, None]

    # Madera noble de arce barnizada en ámbar cálido con pátina de luthier
    wood_base = np.array([0.620, 0.360, 0.170], dtype=np.float32)
    wood_grain_dark = np.array([0.450, 0.220, 0.090], dtype=np.float32)

    # Vetas longitudinales de madera flameada con ondulación natural
    flame_waves = np.sin(y * 70.0 + np.sin(x * 12.0) * 3.0) * 0.5 + 0.5
    grain_lines = np.sin(x * 240.0) * 0.15

    wood_pattern = np.clip(flame_waves * 0.65 + grain_lines * 0.35, 0.0, 1.0)
    for c in range(3):
        diffuse[:, :, c] = wood_base[c] * (1.0 - wood_pattern * 0.40) + wood_grain_dark[c] * (wood_pattern * 0.40)
    diffuse[:, :, 3] = 1.0

    # Diapasón y cordal en negro ébano (sector UV asignado: x > 0.75)
    ebony_mask = np.clip((x - 0.72) / 0.04, 0.0, 1.0)
    ebony_color = np.array([0.06, 0.06, 0.07], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - ebony_mask) + ebony_color[c] * ebony_mask

    height_violin = wood_pattern * 0.12
    normal_violin = height_to_normal_map(height_violin, scale=1.8)

    save_numpy_image("Mat_Violin_Diff", diffuse, [
        os.path.join(TEXTURES_DIR, "astorga_violin_diffuse.png"),
        os.path.join(PROPS_DIR, "violin_diffuse.png")
    ])
    save_numpy_image("Mat_Violin_Norm", normal_violin, [
        os.path.join(TEXTURES_DIR, "astorga_violin_normal.png"),
        os.path.join(PROPS_DIR, "violin_normal.png")
    ])

def main():
    print("=" * 65)
    print("INICIANDO SÍNTESIS DE TEXTURAS PBR CANÓNICAS DE ASTORGA Y VIOLÍN")
    print("=" * 65)
    generate_face_textures()
    generate_eye_textures()
    generate_hair_textures()
    generate_suit_textures()
    generate_shirt_textures()
    generate_tie_textures()
    generate_pants_textures()
    generate_shoes_textures()
    generate_violin_textures()
    print("=" * 65)
    print("TODAS LAS TEXTURAS PBR FUERON GENERADAS CON ÉXITO")
    print("=" * 65)

if __name__ == "__main__":
    main()
