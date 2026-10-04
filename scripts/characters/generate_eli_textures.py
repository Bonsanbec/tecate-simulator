"""
=============================================================================
Generador de Texturas PBR Procedurales de Alta Fidelidad para Eli
=============================================================================
Sintetiza mapas PBR (Albedo y Normal Map OpenGL) basados fidedignamente en la
fotografía de referencia 'scratch/humans/eli.png':
1. Rostro y Piel:
   - Tez cálida apiñonada con subtonos dérmicos naturales y rubor facial suave.
   - Barba cerrada completa corta y bigote recortado orgánicos (sin patrones de muaré).
   - Cejas masculinas pobladas bien definidas y cuencas orbitarias suaves (sin ojos 2D pintados).
   - Labios sonrientes con bermellón natural.
2. Globos Oculares 3D:
   - Esclerótica clara, anillo limbal definido, iris castaño cálido con estriaciones y pupila profunda.
3. Indumentaria Formal Beige ("formal_beige"):
   - Saco sastre y pantalón beige arena en tejido twill fino de lino/algodón.
   - Camisa de vestir formal blanco-hielo / celeste muy suave.
   - Corbata de seda vino tinto / borgoña con micro-motas Jacquard.
   - Cinturón y zapatos Oxford en cuero café oscuro / coñac pulido.
   - Montura de gafas en acetato negro satinado.
=============================================================================
"""

import os
import bpy
import numpy as np

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
TEXTURES_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/textures")
CITIZENS_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/citizens")

os.makedirs(TEXTURES_DIR, exist_ok=True)
os.makedirs(CITIZENS_DIR, exist_ok=True)

def save_numpy_image(img_name, arr_rgba, out_paths):
    """Guarda una matriz NumPy (H, W, 4) en formato PNG mediante la API interna de Blender."""
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
        print(f"✓ Textura PBR generada: {out_path} ({w}x{h})")

def height_to_normal_map(height, scale=1.5):
    """Calcula el mapa de normales en espacio tangente OpenGL (+Y hacia arriba)."""
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
# 1. ROSTRO ANATÓMICO Y PIEL DE ALTA DEFINICIÓN (2048x2048)
# =============================================================================
def generate_face_textures():
    print("-> Generando texturas PBR faciales orgánicas para Eli...")
    w, h = 2048, 2048
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    x = np.linspace(0.0, 1.0, w)[None, :]
    y = np.linspace(0.0, 1.0, h)[:, None]

    # 1. Base dérmica: Tez cálida apiñonada de Eli (scratch/humans/eli.png)
    base_skin = np.array([0.79, 0.62, 0.51], dtype=np.float32)
    warm_cheek = np.array([0.84, 0.52, 0.44], dtype=np.float32)
    shadow_tone = np.array([0.65, 0.49, 0.40], dtype=np.float32)

    for c in range(3):
        diffuse[:, :, c] = base_skin[c]
    diffuse[:, :, 3] = 1.0

    # Resalte y calidez en pómulos, nariz y frente
    cheeks_l = np.exp(-((x - 0.38)**2 / 0.012 + (y - 0.53)**2 / 0.010))
    cheeks_r = np.exp(-((x - 0.62)**2 / 0.012 + (y - 0.53)**2 / 0.010))
    nose_bridge = np.exp(-((x - 0.50)**2 / 0.0018 + (y - 0.52)**2 / 0.025))
    forehead_warmth = np.exp(-((x - 0.50)**2 / 0.040 + (y - 0.78)**2 / 0.015))

    facial_warmth = np.clip(cheeks_l + cheeks_r + nose_bridge * 0.6 + forehead_warmth * 0.4, 0.0, 1.0)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - facial_warmth * 0.28) + warm_cheek[c] * (facial_warmth * 0.28)

    # 2. Cuencas orbitarias suaves (sombra anatómica natural; SIN OJOS 2D PINTADOS)
    for eye_cx in [0.38, 0.62]:
        orbit_dist = np.sqrt(((x - eye_cx) / 0.065)**2 + ((y - 0.63)**2 / 0.038**2))
        orbit_shade = np.clip(1.0 - orbit_dist, 0.0, 1.0)**2 * 0.28
        for c in range(3):
            diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - orbit_shade) + shadow_tone[c] * orbit_shade

    # 3. Cejas masculinas densas, arqueadas y naturales de Eli (Y ~ 0.70 - 0.72)
    dx_brow_l = (x - 0.39) / 0.065
    arch_l = -0.5 * (dx_brow_l**2)
    dy_brow_l = (y - (0.710 + arch_l * 0.020)) / 0.018
    brow_l = np.clip(1.0 - np.sqrt(dx_brow_l**2 + dy_brow_l**2), 0.0, 1.0)**1.5

    dx_brow_r = (x - 0.61) / 0.065
    arch_r = -0.5 * (dx_brow_r**2)
    dy_brow_r = (y - (0.710 + arch_r * 0.020)) / 0.018
    brow_r = np.clip(1.0 - np.sqrt(dx_brow_r**2 + dy_brow_r**2), 0.0, 1.0)**1.5

    eyebrows = np.clip(np.maximum(brow_l, brow_r), 0.0, 1.0)
    brow_col = np.array([0.11, 0.08, 0.06], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - eyebrows * 0.94) + brow_col[c] * (eyebrows * 0.94)

    # 4. Barba completa corta y bigote bien perfilado de Eli (scratch/humans/eli.png)
    dx_jaw = np.abs(x - 0.50)
    # Mandíbula redondeada continua (curva parabólica suave con base en mentón Z ~ 0.27)
    y_jaw_curve = 0.27 + 0.35 * np.maximum(0.0, (dx_jaw - 0.05) / 0.22)**1.8
    # Relleno del mentón completo (cubriendo barbilla de Y=0.22 a Y=0.34)
    chin_fill = np.clip(1.0 - np.sqrt((dx_jaw / 0.08)**2 + ((y - 0.28) / 0.065)**2), 0.0, 1.0)**1.3
    # Faja mandibular continua hacia las sienes
    jaw_strip = np.clip(1.0 - np.abs(y - y_jaw_curve) / 0.055, 0.0, 1.0)**1.3 * (dx_jaw < 0.27)

    # Bigote continuo sobre labio superior (Y ~ 0.42 - 0.46)
    dx_stache = dx_jaw / 0.085
    dy_stache = (y - 0.442) / 0.024
    stache_base = np.clip(1.0 - np.sqrt(dx_stache**2 + dy_stache**2), 0.0, 1.0)**1.3
    stache_base *= np.clip(dx_jaw / 0.006, 0.3, 1.0)

    # Comisuras continuas que unen bigote con la mandíbula
    commissure_l = np.clip(1.0 - np.sqrt(((x - 0.425) / 0.024)**2 + ((y - 0.385) / 0.045)**2), 0.0, 1.0)**1.3
    commissure_r = np.clip(1.0 - np.sqrt(((x - 0.575) / 0.024)**2 + ((y - 0.385) / 0.045)**2), 0.0, 1.0)**1.3

    # Patillas laterales conectando con el cabello
    burns_l = np.clip(1.0 - np.sqrt(((x - 0.27) / 0.024)**2 + ((y - 0.49) / 0.060)**2), 0.0, 1.0)**1.3
    burns_r = np.clip(1.0 - np.sqrt(((x - 0.73) / 0.024)**2 + ((y - 0.49) / 0.060)**2), 0.0, 1.0)**1.3

    beard_total = np.clip(np.maximum.reduce([chin_fill, jaw_strip, stache_base, commissure_l, commissure_r, burns_l, burns_r]), 0.0, 1.0)
    beard_col = np.array([0.13, 0.10, 0.08], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - beard_total * 0.92) + beard_col[c] * (beard_total * 0.92)

    # 5. Labios sonrientes con bermellón suave (Y ~ 0.38 - 0.41)
    dx_lip = (x - 0.50) / 0.065
    dy_lip = (y - 0.392) / 0.020
    lip_mask = np.clip(1.0 - np.sqrt(dx_lip**2 + dy_lip**2), 0.0, 1.0)**1.3
    smile_curve = 0.005 * (1.0 - dx_lip**2)
    dy_split = np.abs(y - (0.390 + smile_curve)) / 0.004
    lip_split = np.clip(1.0 - dy_split, 0.0, 1.0) * (np.abs(dx_lip) < 0.8)

    lip_col = np.array([0.72, 0.44, 0.40], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lip_mask * 0.60) + lip_col[c] * (lip_mask * 0.60)
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lip_split * 0.65) + 0.18 * (lip_split * 0.65)

    # Aletas nasales suaves
    nostril_l = np.clip(1.0 - np.sqrt(((x - 0.485) / 0.012)**2 + ((y - 0.51) / 0.008)**2), 0.0, 1.0)**2
    nostril_r = np.clip(1.0 - np.sqrt(((x - 0.515) / 0.012)**2 + ((y - 0.51) / 0.008)**2), 0.0, 1.0)**2
    nostrils = np.maximum(nostril_l, nostril_r)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - nostrils * 0.35) + shadow_tone[c] * (nostrils * 0.35)

    # 6. Microporos sutiles y relieve de normales
    xx = np.linspace(0, 48 * np.pi, w)[None, :]
    yy = np.linspace(0, 48 * np.pi, h)[:, None]
    subtle_pore = (np.sin(xx * 2.2 + yy * 3.1) * 0.03 + np.cos(xx * 3.5 - yy * 2.7) * 0.03)

    height = (eyebrows * 0.25) + (beard_total * 0.20) + (lip_mask * 0.15) - (lip_split * 0.20) + subtle_pore
    normal = height_to_normal_map(height, scale=1.4)

    paths_d = [os.path.join(TEXTURES_DIR, "eli_face_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_face_diffuse.png")]
    paths_n = [os.path.join(TEXTURES_DIR, "eli_face_normal.png"), os.path.join(CITIZENS_DIR, "eli_face_normal.png")]
    save_numpy_image("eli_face_diffuse", diffuse, paths_d)
    save_numpy_image("eli_face_normal", normal, paths_n)

# =============================================================================
# 2. GLOBO OCULAR 3D HIPERREALISTA (1024x1024)
# =============================================================================
def generate_eye_texture():
    print("-> Generando textura PBR para Ojos de Eli...")
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    x = np.linspace(-1.0, 1.0, w)[None, :]
    y = np.linspace(-1.0, 1.0, h)[:, None]
    r = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)

    r_pupil = 0.18
    r_iris = 0.54
    r_limbus = 0.60

    col_sclera = np.array([0.96, 0.95, 0.94], dtype=np.float32)
    col_iris_dark = np.array([0.22, 0.13, 0.07], dtype=np.float32)
    col_iris_warm = np.array([0.48, 0.30, 0.16], dtype=np.float32)
    col_limbus = np.array([0.09, 0.05, 0.03], dtype=np.float32)
    col_pupil = np.array([0.01, 0.01, 0.01], dtype=np.float32)

    striations = (np.sin(theta * 36.0) * 0.25 +
                  np.sin(theta * 72.0 + r * 12.0) * 0.20 +
                  np.sin(theta * 18.0) * 0.15 + 0.5)

    # Máscaras radiales
    m_pupil = (r < r_pupil)
    m_iris = (r >= r_pupil) & (r < r_iris)
    m_limbus = (r >= r_iris) & (r < r_limbus)
    m_sclera = (r >= r_limbus)

    # Asignación continua
    for c in range(3):
        diffuse[:, :, c] = col_sclera[c]

    t_iris = np.clip((r - r_pupil) / (r_iris - r_pupil), 0.0, 1.0)
    iris_blend = col_iris_dark[:, None, None] * (1.0 - t_iris * 0.60) + col_iris_warm[:, None, None] * (t_iris * 0.80 * striations)
    for c in range(3):
        diffuse[:, :, c] = np.where(m_iris, iris_blend[c], diffuse[:, :, c])

    t_limbus = np.clip((r - r_iris) / (r_limbus - r_iris), 0.0, 1.0)
    limbus_blend = col_limbus[:, None, None] * (1.0 - t_limbus) + col_sclera[:, None, None] * t_limbus
    for c in range(3):
        diffuse[:, :, c] = np.where(m_limbus, limbus_blend[c], diffuse[:, :, c])
        diffuse[:, :, c] = np.where(m_pupil, col_pupil[c], diffuse[:, :, c])

    diffuse[:, :, 3] = 1.0
    paths = [os.path.join(TEXTURES_DIR, "eli_eye_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_eye_diffuse.png")]
    save_numpy_image("eli_eye_diffuse", diffuse, paths)

# =============================================================================
# 3. SACO SASTRE Y PANTALÓN FORMAL BEIGE (Lino/Algodón Arena)
# =============================================================================
def generate_suit_and_pants_textures():
    print("-> Generando texturas PBR para Traje Formal Beige (Saco y Pantalón)...")
    w, h = 1024, 1024

    x = np.linspace(0, 1, w)[None, :]
    y = np.linspace(0, 1, h)[:, None]

    # Tono beige arena / lino cálido calibrado de Eli (scratch/humans/eli.png)
    base_beige = np.array([0.83, 0.78, 0.71], dtype=np.float32)

    # Trama sastre de tejido twill fino
    xx = np.linspace(0, 64 * np.pi, w)[None, :]
    yy = np.linspace(0, 64 * np.pi, h)[:, None]
    twill = (np.sin(xx + yy) * 0.015 + np.sin(xx - yy) * 0.015)

    # Saco
    suit_diffuse = np.zeros((h, w, 4), dtype=np.float32)
    for c in range(3):
        suit_diffuse[:, :, c] = base_beige[c] + twill
    suit_diffuse[:, :, 3] = 1.0

    suit_height = twill * 0.6
    suit_norm = height_to_normal_map(suit_height, scale=1.3)

    save_numpy_image("eli_suit_diffuse", suit_diffuse,
                     [os.path.join(TEXTURES_DIR, "eli_suit_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_suit_diffuse.png")])
    save_numpy_image("eli_suit_normal", suit_norm,
                     [os.path.join(TEXTURES_DIR, "eli_suit_normal.png"), os.path.join(CITIZENS_DIR, "eli_suit_normal.png")])

    # Pantalón (a juego con raya sastre suave)
    pants_diffuse = np.zeros((h, w, 4), dtype=np.float32)
    crease = np.exp(-((x - 0.50)**2 / 0.003)) * 0.03
    for c in range(3):
        pants_diffuse[:, :, c] = base_beige[c] + twill + crease
    pants_diffuse[:, :, 3] = 1.0

    pants_height = twill * 0.6 + crease * 0.8
    pants_norm = height_to_normal_map(pants_height, scale=1.3)

    save_numpy_image("eli_pants_diffuse", pants_diffuse,
                     [os.path.join(TEXTURES_DIR, "eli_pants_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_pants_diffuse.png")])
    save_numpy_image("eli_pants_normal", pants_norm,
                     [os.path.join(TEXTURES_DIR, "eli_pants_normal.png"), os.path.join(CITIZENS_DIR, "eli_pants_normal.png")])

# =============================================================================
# 4. CAMISA DE VESTIR Y CORBATA DE SEDA VINO TINTO
# =============================================================================
def generate_shirt_and_tie_textures():
    print("-> Generando texturas PBR para Camisa y Corbata...")
    w, h = 1024, 1024

    # Camisa de vestir celeste muy pálido / blanco hielo (eli.png)
    shirt_diffuse = np.zeros((h, w, 4), dtype=np.float32)
    base_shirt = np.array([0.91, 0.94, 0.97], dtype=np.float32)
    xx = np.linspace(0, 80 * np.pi, w)[None, :]
    yy = np.linspace(0, 80 * np.pi, h)[:, None]
    poplin = (np.sin(xx) * 0.008 + np.cos(yy) * 0.008)
    for c in range(3):
        shirt_diffuse[:, :, c] = base_shirt[c] + poplin
    shirt_diffuse[:, :, 3] = 1.0
    shirt_norm = height_to_normal_map(poplin, scale=1.1)

    save_numpy_image("eli_shirt_diffuse", shirt_diffuse,
                     [os.path.join(TEXTURES_DIR, "eli_shirt_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_shirt_diffuse.png")])
    save_numpy_image("eli_shirt_normal", shirt_norm,
                     [os.path.join(TEXTURES_DIR, "eli_shirt_normal.png"), os.path.join(CITIZENS_DIR, "eli_shirt_normal.png")])

    # Corbata de seda vino tinto / borgoña con micro-motas Jacquard de seda
    tie_diffuse = np.zeros((h, w, 4), dtype=np.float32)
    base_burgundy = np.array([0.45, 0.08, 0.15], dtype=np.float32)
    dot_col = np.array([0.72, 0.35, 0.42], dtype=np.float32)

    x = np.linspace(0, 1, w)[None, :]
    y = np.linspace(0, 1, h)[:, None]
    dot_u = np.mod(x * 24.0 + y * 12.0, 1.0) - 0.5
    dot_v = np.mod(-x * 12.0 + y * 24.0, 1.0) - 0.5
    r_dot = np.sqrt(dot_u**2 + dot_v**2)
    dot_mask = np.clip(1.0 - r_dot / 0.16, 0.0, 1.0)**2

    silk_grain = np.sin((x + y) * 120.0 * np.pi) * 0.015
    for c in range(3):
        tie_diffuse[:, :, c] = base_burgundy[c] * (1.0 - dot_mask) + dot_col[c] * dot_mask + silk_grain
    tie_diffuse[:, :, 3] = 1.0

    tie_height = dot_mask * 0.20 + silk_grain * 0.4
    tie_norm = height_to_normal_map(tie_height, scale=1.4)

    save_numpy_image("eli_tie_diffuse", tie_diffuse,
                     [os.path.join(TEXTURES_DIR, "eli_tie_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_tie_diffuse.png")])
    save_numpy_image("eli_tie_normal", tie_norm,
                     [os.path.join(TEXTURES_DIR, "eli_tie_normal.png"), os.path.join(CITIZENS_DIR, "eli_tie_normal.png")])

# =============================================================================
# 5. ZAPATOS OXFORD, CINTURÓN Y GAFAS DE ACETATO
# =============================================================================
def generate_accessories_textures():
    print("-> Generando texturas PBR para Accesorios (Zapatos, Cinturón, Gafas)...")
    w, h = 512, 512

    # Cuero café oscuro / coñac pulido
    shoes_diffuse = np.zeros((h, w, 4), dtype=np.float32)
    base_leather = np.array([0.22, 0.12, 0.08], dtype=np.float32)
    xx = np.linspace(0, 32 * np.pi, w)[None, :]
    yy = np.linspace(0, 32 * np.pi, h)[:, None]
    leather_grain = (np.sin(xx * 2.0 + yy * 3.0) * 0.015 + np.cos(xx * 3.0 - yy * 2.0) * 0.015)
    for c in range(3):
        shoes_diffuse[:, :, c] = base_leather[c] + leather_grain
    shoes_diffuse[:, :, 3] = 1.0
    shoes_norm = height_to_normal_map(leather_grain, scale=1.2)

    save_numpy_image("eli_shoes_diffuse", shoes_diffuse,
                     [os.path.join(TEXTURES_DIR, "eli_shoes_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_shoes_diffuse.png")])
    save_numpy_image("eli_shoes_normal", shoes_norm,
                     [os.path.join(TEXTURES_DIR, "eli_shoes_normal.png"), os.path.join(CITIZENS_DIR, "eli_shoes_normal.png")])

    # Cinturón
    belt_diffuse = np.zeros((h, w, 4), dtype=np.float32)
    base_belt = np.array([0.20, 0.10, 0.06], dtype=np.float32)
    for c in range(3):
        belt_diffuse[:, :, c] = base_belt[c] + leather_grain
    belt_diffuse[:, :, 3] = 1.0

    save_numpy_image("eli_belt_diffuse", belt_diffuse,
                     [os.path.join(TEXTURES_DIR, "eli_belt_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_belt_diffuse.png")])
    save_numpy_image("eli_belt_normal", shoes_norm,
                     [os.path.join(TEXTURES_DIR, "eli_belt_normal.png"), os.path.join(CITIZENS_DIR, "eli_belt_normal.png")])

    # Montura de gafas (Acetato negro satinado moderno)
    glasses_diffuse = np.zeros((h, w, 4), dtype=np.float32)
    base_acetate = np.array([0.06, 0.06, 0.07], dtype=np.float32)
    for c in range(3):
        glasses_diffuse[:, :, c] = base_acetate[c]
    glasses_diffuse[:, :, 3] = 1.0
    glasses_norm = np.zeros((h, w, 4), dtype=np.float32)
    glasses_norm[:, :, 0] = 0.5
    glasses_norm[:, :, 1] = 0.5
    glasses_norm[:, :, 2] = 1.0
    glasses_norm[:, :, 3] = 1.0

    save_numpy_image("eli_glasses_diffuse", glasses_diffuse,
                     [os.path.join(TEXTURES_DIR, "eli_glasses_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_glasses_diffuse.png")])
    save_numpy_image("eli_glasses_normal", glasses_norm,
                     [os.path.join(TEXTURES_DIR, "eli_glasses_normal.png"), os.path.join(CITIZENS_DIR, "eli_glasses_normal.png")])

def main():
    print("==================================================")
    print("GENERANDO SUITE CANÓNICA DE TEXTURAS PBR PARA ELI")
    print("==================================================")
    generate_face_textures()
    generate_eye_texture()
    generate_suit_and_pants_textures()
    generate_shirt_and_tie_textures()
    generate_accessories_textures()
    print("==================================================")
    print("✓ TODAS LAS TEXTURAS PBR DE ELI GENERADAS CON ÉXITO")
    print("==================================================")

if __name__ == "__main__":
    main()
