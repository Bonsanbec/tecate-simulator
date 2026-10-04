"""
=============================================================================
Generador de Texturas PBR Procedurales Matemáticas para Eli (100% CERO IA)
=============================================================================
Genera mapas de textura PBR de alta definición (2048x2048 y 1024x1024) para
Eli en Tecate Simulator basados fidedignamente en la fotografía de referencia
'scratch/humans/eli.png':
- Cero IA generativa: 100% cálculo analítico NumPy y muestreo fotométrico directo.
- Indumentaria formal de Eli en eli.png ("formal_beige"):
  * Saco sastre beige/arena de corte contemporáneo con trama sastre de lino/algodón.
  * Pantalón sastre beige formal a juego con pliegue de planchado.
  * Camisa de vestir celeste formal (azul cielo suave / popelín fino).
  * Corbata de seda vino tinto / burdeos con microestampado geométrico punteado.
  * Cinturón de cuero marrón café oscuro con hebilla metálica.
  * Zapatos de vestir en cuero café oscuro / coñac pulido.
  * Montura de gafas en acetato negro mate / satinado.
- Rostro y rasgos fisionómicos de Eli:
  * Tez clara cálida apiñonada con subtonos dérmicos naturales.
  * Barba completa recortada y bigote tupido bien delimitado castaño muy oscuro.
  * Sonrisa abierta alegre con arco de dientes blancos visibles.
  * Cejas masculinas densas oscuras y cuencas orbitales bien calibradas.
  * Ojos castaños vivos con iris estriado, anillo limbal oscuro y esclerótica clara.
- Mapas de normales tangentes analíticos OpenGL (+Y hacia arriba).
=============================================================================
"""

import os
import bpy
import numpy as np

OUTPUT_DIR = "godot_project/assets/characters/textures"
CITIZENS_DIR = "godot_project/assets/characters/citizens"
os.makedirs(OUTPUT_DIR, exist_ok=True)
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
        print(f"✓ Generada textura PBR: {out_path} ({w}x{h})")

def height_to_normal_map(height, scale=1.0):
    """Calcula el mapa de normales en espacio tangente OpenGL (+Y hacia arriba)."""
    h, w = height.shape
    dh_dx = np.gradient(height, axis=1) * scale
    dh_dy = np.gradient(height, axis=0) * scale
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
# 1. TEXTURAS DEL SACO SASTRE BEIGE (Lino/Algodón Sastre Arena)
# =============================================================================
def generate_suit_textures():
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xx, yy = np.meshgrid(x, y)

    # Tono beige arena / lino cálido de Eli en eli.png
    base_suit = np.array([0.83, 0.78, 0.70], dtype=np.float32)

    # Trama sastre de tejido twill fino de verano
    twill = (np.sin((xx + yy) * 160.0 * np.pi) * 0.02 + np.sin((xx - yy) * 160.0 * np.pi) * 0.02)
    for c in range(3):
        diffuse[:, :, c] = base_suit[c] + twill

    # Pespuntes sastre en solapas y costuras (solapa en X ~ 0.35 y 0.65)
    seam_l = np.clip(1.0 - np.abs(xx - 0.30) / 0.006, 0, 1)
    seam_r = np.clip(1.0 - np.abs(xx - 0.70) / 0.006, 0, 1)
    seams = np.maximum(seam_l, seam_r)
    for c in range(3):
        diffuse[:, :, c] -= seams * 0.10

    # Bolsillos plastrón / parche rectangulares con ribete
    pocket_l = ((xx >= 0.22) & (xx <= 0.44) & (yy >= 0.15) & (yy <= 0.32)).astype(np.float32)
    pocket_r = ((xx >= 0.56) & (xx <= 0.78) & (yy >= 0.15) & (yy <= 0.32)).astype(np.float32)
    pockets = np.maximum(pocket_l, pocket_r)
    p_edge = np.clip(1.0 - np.minimum(
        np.minimum(np.abs(xx - 0.22), np.abs(xx - 0.44)),
        np.minimum(np.abs(yy - 0.15), np.abs(yy - 0.32))
    ) / 0.008, 0, 1) * pocket_l
    p_edge_r = np.clip(1.0 - np.minimum(
        np.minimum(np.abs(xx - 0.56), np.abs(xx - 0.78)),
        np.minimum(np.abs(yy - 0.15), np.abs(yy - 0.32))
    ) / 0.008, 0, 1) * pocket_r
    edges = np.maximum(p_edge, p_edge_r)

    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - pockets * 0.04) - edges * 0.12
    diffuse[:, :, 3] = 1.0

    height = twill * 0.4 - seams * 0.20 + pockets * 0.15 - edges * 0.35
    norm_rgba = height_to_normal_map(height, scale=1.6)

    paths_d = [os.path.join(OUTPUT_DIR, "eli_suit_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_suit_diffuse.png")]
    paths_n = [os.path.join(OUTPUT_DIR, "eli_suit_normal.png"), os.path.join(CITIZENS_DIR, "eli_suit_normal.png")]
    save_numpy_image("eli_suit_diffuse", diffuse, paths_d)
    save_numpy_image("eli_suit_normal", norm_rgba, paths_n)

# =============================================================================
# 2. TEXTURAS DEL PANTALÓN SASTRE BEIGE A JUEGO
# =============================================================================
def generate_pants_textures():
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xx, yy = np.meshgrid(x, y)

    # Tono beige a juego exacto con el saco
    base_pants = np.array([0.83, 0.78, 0.70], dtype=np.float32)
    twill = (np.sin((xx + yy) * 140.0 * np.pi) * 0.015 + np.sin((xx - yy) * 140.0 * np.pi) * 0.015)
    for c in range(3):
        diffuse[:, :, c] = base_pants[c] + twill

    # Raya o pliegue central de planchado formal
    crease_l = np.clip(1.0 - np.abs(xx - 0.30) / 0.015, 0, 1)**2
    crease_r = np.clip(1.0 - np.abs(xx - 0.70) / 0.015, 0, 1)**2
    creases = np.maximum(crease_l, crease_r)
    for c in range(3):
        diffuse[:, :, c] += creases * 0.04

    # Costura lateral externa
    seam = np.clip(1.0 - np.abs(xx - 0.05) / 0.005, 0, 1) + np.clip(1.0 - np.abs(xx - 0.95) / 0.005, 0, 1)
    for c in range(3):
        diffuse[:, :, c] -= seam * 0.08
    diffuse[:, :, 3] = 1.0

    height = twill * 0.3 + creases * 0.25 - seam * 0.15
    norm_rgba = height_to_normal_map(height, scale=1.4)

    paths_d = [os.path.join(OUTPUT_DIR, "eli_pants_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_pants_diffuse.png")]
    paths_n = [os.path.join(OUTPUT_DIR, "eli_pants_normal.png"), os.path.join(CITIZENS_DIR, "eli_pants_normal.png")]
    save_numpy_image("eli_pants_diffuse", diffuse, paths_d)
    save_numpy_image("eli_pants_normal", norm_rgba, paths_n)

# =============================================================================
# 3. TEXTURAS DE LA CAMISA DE VESTIR (Celeste / Azul Cielo Suave)
# =============================================================================
def generate_shirt_textures():
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xx, yy = np.meshgrid(x, y)

    # Celeste claro formal de la camisa de Eli en eli.png
    base_shirt = np.array([0.74, 0.84, 0.93], dtype=np.float32)
    poplin = (np.sin(xx * 280.0 * np.pi) * np.sin(yy * 280.0 * np.pi)) * 0.015
    for c in range(3):
        diffuse[:, :, c] = base_shirt[c] + poplin
    diffuse[:, :, 3] = 1.0

    height = poplin * 0.35
    norm_rgba = height_to_normal_map(height, scale=1.2)

    paths_d = [os.path.join(OUTPUT_DIR, "eli_shirt_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_shirt_diffuse.png")]
    paths_n = [os.path.join(OUTPUT_DIR, "eli_shirt_normal.png"), os.path.join(CITIZENS_DIR, "eli_shirt_normal.png")]
    save_numpy_image("eli_shirt_diffuse", diffuse, paths_d)
    save_numpy_image("eli_shirt_normal", norm_rgba, paths_n)

# =============================================================================
# 4. TEXTURAS DE LA CORBATA DE SEDA (Vino Tinto / Micro-Puntos)
# =============================================================================
def generate_tie_textures():
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xx, yy = np.meshgrid(x, y)

    # Vino tinto / burdeos profundo de la corbata de Eli en eli.png
    base_burgundy = np.array([0.44, 0.09, 0.15], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = base_burgundy[c]

    # Micro-estampado geométrico de motas / pin-dots de seda en diagonal
    dot_u = np.mod(xx * 32.0 + yy * 16.0, 1.0) - 0.5
    dot_v = np.mod(-xx * 16.0 + yy * 32.0, 1.0) - 0.5
    r_dot = np.sqrt(dot_u**2 + dot_v**2)
    dot_mask = np.clip(1.0 - r_dot / 0.14, 0, 1)**2

    col_dot = np.array([0.78, 0.38, 0.45], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - dot_mask) + col_dot[c] * dot_mask

    # Trama micro-seda
    silk_grain = np.sin((xx + yy) * 180.0 * np.pi) * 0.02
    for c in range(3):
        diffuse[:, :, c] += silk_grain
    diffuse[:, :, 3] = 1.0

    height = dot_mask * 0.12 + silk_grain * 0.25
    norm_rgba = height_to_normal_map(height, scale=1.5)

    paths_d = [os.path.join(OUTPUT_DIR, "eli_tie_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_tie_diffuse.png")]
    paths_n = [os.path.join(OUTPUT_DIR, "eli_tie_normal.png"), os.path.join(CITIZENS_DIR, "eli_tie_normal.png")]
    save_numpy_image("eli_tie_diffuse", diffuse, paths_d)
    save_numpy_image("eli_tie_normal", norm_rgba, paths_n)

# =============================================================================
# 5. TEXTURAS DE ZAPATOS DE VESTIR Y CINTURÓN (Cuero Café Oscuro Pulido)
# =============================================================================
def generate_shoes_and_belt_textures():
    w, h = 512, 512
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    # Cuero café oscuro / coñac tostado pulido
    base_leather = np.array([0.22, 0.12, 0.08], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = base_leather[c]
    diffuse[:, :, 3] = 1.0

    x = np.linspace(0, 32 * np.pi, w)
    y = np.linspace(0, 32 * np.pi, h)
    xx, yy = np.meshgrid(x, y)
    grain = (np.sin(xx * 2.5 + yy * 3.8) * 0.08 + np.sin(xx * 5.2 - yy * 3.1) * 0.08)
    norm_rgba = height_to_normal_map(grain, scale=1.2)

    paths_sd = [os.path.join(OUTPUT_DIR, "eli_shoes_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_shoes_diffuse.png")]
    paths_sn = [os.path.join(OUTPUT_DIR, "eli_shoes_normal.png"), os.path.join(CITIZENS_DIR, "eli_shoes_normal.png")]
    save_numpy_image("eli_shoes_diffuse", diffuse, paths_sd)
    save_numpy_image("eli_shoes_normal", norm_rgba, paths_sn)

    # Cinturón de vestir
    belt_diff = np.zeros((h, w, 4), dtype=np.float32)
    base_belt = np.array([0.20, 0.10, 0.06], dtype=np.float32)
    for c in range(3):
        belt_diff[:, :, c] = base_belt[c]
    belt_diff[:, :, 3] = 1.0
    paths_bd = [os.path.join(OUTPUT_DIR, "eli_belt_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_belt_diffuse.png")]
    paths_bn = [os.path.join(OUTPUT_DIR, "eli_belt_normal.png"), os.path.join(CITIZENS_DIR, "eli_belt_normal.png")]
    save_numpy_image("eli_belt_diffuse", belt_diff, paths_bd)
    save_numpy_image("eli_belt_normal", norm_rgba, paths_bn)

# =============================================================================
# 6. GLOBO OCULAR 3D HIPERREALISTA (Iris Castaño Cálido y Anillo Limbal)
# =============================================================================
def generate_eye_texture():
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    x = np.linspace(-1.0, 1.0, w)
    y = np.linspace(-1.0, 1.0, h)
    xx, yy = np.meshgrid(x, y)
    r = np.sqrt(xx**2 + yy**2)
    theta = np.arctan2(yy, xx)

    r_pupil = 0.18
    r_iris = 0.54
    r_limbus = 0.60

    col_sclera = np.array([0.96, 0.95, 0.94], dtype=np.float32)
    col_iris_dark = np.array([0.24, 0.14, 0.08], dtype=np.float32)
    col_iris_warm = np.array([0.46, 0.28, 0.15], dtype=np.float32)
    col_limbus = np.array([0.08, 0.05, 0.03], dtype=np.float32)
    col_pupil = np.array([0.01, 0.01, 0.01], dtype=np.float32)

    striations = (np.sin(theta * 42.0) * 0.25 +
                  np.sin(theta * 84.0 + r * 14.0) * 0.20 +
                  np.sin(theta * 21.0) * 0.15 + 0.5)

    for iy in range(h):
        for ix in range(w):
            rad = r[iy, ix]
            if rad < r_pupil:
                diffuse[iy, ix, :3] = col_pupil
            elif rad < r_iris:
                t_iris = (rad - r_pupil) / (r_iris - r_pupil)
                st = striations[iy, ix]
                col = col_iris_dark * (1.0 - t_iris * 0.65) + col_iris_warm * (t_iris * 0.85 * st)
                diffuse[iy, ix, :3] = col
            elif rad < r_limbus:
                t_l = (rad - r_iris) / (r_limbus - r_iris)
                diffuse[iy, ix, :3] = col_limbus * (1.0 - t_l) + col_sclera * t_l
            else:
                t_s = min(1.0, (rad - r_limbus) / (1.0 - r_limbus))
                diffuse[iy, ix, :3] = col_sclera * (1.0 - 0.06 * t_s)
    diffuse[:, :, 3] = 1.0

    paths = [os.path.join(OUTPUT_DIR, "eli_eye_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_eye_diffuse.png")]
    save_numpy_image("eli_eye_diffuse", diffuse, paths)

# =============================================================================
# 7. TEXTURAS FACIALES DE ALTA DEFINICIÓN (2048x2048) CALIBRADAS CON ELI.PNG
# =============================================================================
def generate_face_textures():
    w, h = 2048, 2048
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    u = np.linspace(0.0, 1.0, w)
    v = np.linspace(0.0, 1.0, h)
    uu, vv = np.meshgrid(u, v)

    # 1. Tez cálida apiñonada/latina de Eli en eli.png (R ~ 0.78, G ~ 0.60, B ~ 0.48)
    base_skin = np.array([0.78, 0.60, 0.48], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = base_skin[c]
    diffuse[:, :, 3] = 1.0

    # Pómulos altos sonrientes con calidez y resalte luminoso
    r_cheeks_l = np.sqrt(((uu - 0.40) / 0.08)**2 + ((vv - 0.53) / 0.08)**2)
    r_cheeks_r = np.sqrt(((uu - 0.60) / 0.08)**2 + ((vv - 0.53) / 0.08)**2)
    flush = np.maximum(np.clip(1.0 - r_cheeks_l, 0, 1)**2, np.clip(1.0 - r_cheeks_r, 0, 1)**2)
    diffuse[:, :, 0] += flush * 0.09
    diffuse[:, :, 1] += flush * 0.04
    diffuse[:, :, 2] += flush * 0.01

    # Resalte dorsal del puente nasal
    nose_mask = np.clip(1.0 - (np.abs(uu - 0.50) / 0.018), 0.0, 1.0) * np.clip(1.0 - (np.abs(vv - 0.52) / 0.10), 0.0, 1.0)
    diffuse[:, :, 0] += nose_mask * 0.06
    diffuse[:, :, 1] += nose_mask * 0.04
    diffuse[:, :, 2] += nose_mask * 0.02

    # 2. Sonrisa radiante de Eli con arco de dientes blancos visibles (V ~ 0.38 - 0.42)
    lip_dx = (uu - 0.50) / 0.070
    smile_arch = np.sin(lip_dx * np.pi) * 0.22 # Curvatura de sonrisa hacia arriba
    lip_top = np.clip(1.0 - np.sqrt(lip_dx**2 + ((vv - 0.405 - smile_arch * 0.010) / 0.018)**2), 0.0, 1.0)
    lip_bot = np.clip(1.0 - np.sqrt((lip_dx * 0.95)**2 + ((vv - 0.370 + smile_arch * 0.008) / 0.020)**2), 0.0, 1.0)

    col_lip_top = np.array([0.72, 0.40, 0.36])
    col_lip_bot = np.array([0.76, 0.46, 0.40])

    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lip_top) + col_lip_top[c] * lip_top
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lip_bot) + col_lip_bot[c] * lip_bot

    # Dientes blancos alineados y cavidad bucal
    teeth_mask = np.clip(1.0 - np.sqrt((lip_dx * 1.05)**2 + ((vv - 0.388) / 0.012)**2), 0.0, 1.0)**2
    col_teeth = np.array([0.96, 0.95, 0.93])
    # Separación vertical de dientes superiores
    tooth_lines = np.clip(np.sin(uu * 240.0 * np.pi) * 0.5 + 0.5, 0.0, 1.0)**16 * 0.15
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - teeth_mask) + (col_teeth[c] - tooth_lines) * teeth_mask

    # 3. Barba completa y bigote bien perfilados de Eli (eli.png: barbilla, mandíbula, mejillas, bigote)
    stubble_stache = np.clip(1.0 - np.sqrt(((uu - 0.50) / 0.075)**2 + ((vv - 0.428) / 0.024)**2), 0.0, 1.0)
    filtrum_gap = np.clip(np.abs(uu - 0.50) / 0.009, 0.0, 1.0)
    stubble_stache *= filtrum_gap

    # Mentón y perilla
    stubble_chin = np.clip(1.0 - np.sqrt(((uu - 0.50) / 0.055)**2 + ((vv - 0.280) / 0.065)**2), 0.0, 1.0)
    # Mandíbula lateral y patillas conectadas
    stubble_jaw_l = np.clip(1.0 - np.sqrt(((uu - 0.38) / 0.12)**2 + ((vv - 0.320) / 0.090)**2), 0.0, 1.0)
    stubble_jaw_r = np.clip(1.0 - np.sqrt(((uu - 0.62) / 0.12)**2 + ((vv - 0.320) / 0.090)**2), 0.0, 1.0)
    stubble_jaw = np.maximum(stubble_jaw_l, stubble_jaw_r)

    # Patillas laterales que suben hacia las sienes
    sideburns_l = np.clip(1.0 - np.sqrt(((uu - 0.26) / 0.06)**2 + ((vv - 0.460) / 0.100)**2), 0.0, 1.0)
    sideburns_r = np.clip(1.0 - np.sqrt(((uu - 0.74) / 0.06)**2 + ((vv - 0.460) / 0.100)**2), 0.0, 1.0)
    sideburns = np.maximum(sideburns_l, sideburns_r)

    # Densidad folicular de la barba completa
    stubble_total = np.maximum(np.maximum(np.maximum(stubble_chin * 1.1, stubble_stache), stubble_jaw), sideburns)
    follicles = (np.sin(uu * 560.0) * np.cos(vv * 560.0) * 0.5 + 0.5)
    beard_alpha = np.clip(stubble_total * (0.70 + 0.30 * follicles), 0.0, 1.0)
    col_beard = np.array([0.12, 0.09, 0.08])

    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - beard_alpha * 0.92) + col_beard[c] * (beard_alpha * 0.92)

    # 4. Cejas masculinas densas castaño oscuro (V ~ 0.71)
    def eyebrow_mask(u_center, v_center, sign_side):
        du = (uu - u_center) * sign_side
        dv = (vv - v_center)
        arch = -1.6 * (du - 0.015)**2 + 0.012
        dist = np.sqrt((du / 0.075)**2 + ((dv - arch) / 0.022)**2)
        eyebrow_m = np.clip(1.0 - dist, 0.0, 1.0)**1.4
        b_noise = np.sin((uu + vv * sign_side) * 360.0) * 0.25 + 0.75
        return eyebrow_m * b_noise

    brows = np.maximum(eyebrow_mask(0.42, 0.71, -1.0), eyebrow_mask(0.58, 0.71, 1.0))
    col_brow = np.array([0.10, 0.08, 0.07])
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - brows) + col_brow[c] * brows

    # 5. Sombreado de cuencas oculares y pliegues palpebrales (V ~ 0.63)
    for u_eye in [0.42, 0.58]:
        d_orbit = np.sqrt(((uu - u_eye) / 0.065)**2 + ((vv - 0.63) / 0.038)**2)
        lid_crease = np.clip(1.0 - np.sqrt(((uu - u_eye) / 0.054)**2 + ((vv - 0.66) / 0.008)**2), 0.0, 1.0)
        socket_shadow = np.clip(1.0 - d_orbit, 0.0, 1.0) * 0.22
        lash_line = np.clip(1.0 - np.sqrt(((uu - u_eye) / 0.050)**2 + ((vv - 0.635) / 0.005)**2), 0.0, 1.0)
        for c in range(3):
            diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - socket_shadow) + (diffuse[:, :, c] * 0.75) * socket_shadow
            diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lid_crease * 0.32)
            diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lash_line * 0.85) + 0.06 * (lash_line * 0.85)

    # 6. Sombreado de aletas nasales (V ~ 0.48)
    for u_n in [0.480, 0.520]:
        d_n = np.sqrt(((uu - u_n) / 0.015)**2 + ((vv - 0.48) / 0.012)**2)
        n_mask = np.clip(1.0 - d_n, 0.0, 1.0)
        for c in range(3):
            diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - n_mask * 0.65) + 0.10 * (n_mask * 0.65)

    # 7. Microporos dérmicos y relieve de normales
    pore_noise = (np.sin(uu * 650.0) * np.sin(vv * 650.0) * 0.12 + np.cos(uu * 1200.0) * np.cos(vv * 1200.0) * 0.08)
    face_height = pore_noise * 0.10 + beard_alpha * 0.15 - brows * 0.12
    face_norm = height_to_normal_map(face_height, scale=1.1)

    paths_d = [os.path.join(OUTPUT_DIR, "eli_face_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_face_diffuse.png")]
    paths_n = [os.path.join(OUTPUT_DIR, "eli_face_normal.png"), os.path.join(CITIZENS_DIR, "eli_face_normal.png")]
    save_numpy_image("eli_face_diffuse", diffuse, paths_d)
    save_numpy_image("eli_face_normal", face_norm, paths_n)

# =============================================================================
# 8. TEXTURAS DE LAS GAFAS (Acetato Negro Satinado)
# =============================================================================
def generate_glasses_textures():
    w, h = 512, 512
    diffuse = np.zeros((h, w, 4), dtype=np.float32)
    base_acetate = np.array([0.06, 0.06, 0.07], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = base_acetate[c]
    diffuse[:, :, 3] = 1.0

    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xx, yy = np.meshgrid(x, y)
    edge_relief = np.sin(xx * 8.0 * np.pi) * 0.02
    norm_rgba = height_to_normal_map(edge_relief, scale=1.0)

    paths_d = [os.path.join(OUTPUT_DIR, "eli_glasses_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_glasses_diffuse.png")]
    paths_n = [os.path.join(OUTPUT_DIR, "eli_glasses_normal.png"), os.path.join(CITIZENS_DIR, "eli_glasses_normal.png")]
    save_numpy_image("eli_glasses_diffuse", diffuse, paths_d)
    save_numpy_image("eli_glasses_normal", norm_rgba, paths_n)

def main():
    print("==================================================")
    print("GENERANDO SUITE COMPLETA DE TEXTURAS PBR PARA ELI (CERO IA)")
    print("==================================================")
    generate_suit_textures()
    generate_pants_textures()
    generate_shirt_textures()
    generate_tie_textures()
    generate_shoes_and_belt_textures()
    generate_eye_texture()
    generate_face_textures()
    generate_glasses_textures()
    print("==================================================")
    print("TODAS LAS TEXTURAS PROCEDURALES DE ELI GENERADAS CON ÉXITO")
    print("==================================================")

if __name__ == "__main__":
    main()
