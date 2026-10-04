"""
Generador de Texturas PBR Procedurales de Alta Fidelidad para Eli
Basado estrictamente en las referencias 'scratch/humans/eli2.png' y 'scratch/humans/eli3.png'.
Sintetiza mapas PBR 100% procedurales (sin fotos directas).
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

def height_to_normal_map(height, scale=1.5):
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
# 1. ROSTRO ANATÓMICO CALIBRADO SEGÚN ELI3.PNG (2048x2048)
# =============================================================================
def generate_face_textures():
    print("-> Generando texturas PBR faciales orgánicas para Eli basadas en eli3.png...")
    w, h = 2048, 2048
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    x = np.linspace(0.0, 1.0, w)[None, :]
    y = np.linspace(0.0, 1.0, h)[:, None]

    # Tez apiñonada cálida / oliva según eli3.png
    base_skin = np.array([0.865, 0.685, 0.605], dtype=np.float32)
    warm_cheek = np.array([0.895, 0.585, 0.515], dtype=np.float32)
    shadow_tone = np.array([0.725, 0.550, 0.470], dtype=np.float32)
    neck_skin = np.array([0.840, 0.660, 0.580], dtype=np.float32)

    for c in range(3):
        diffuse[:, :, c] = base_skin[c]
    diffuse[:, :, 3] = 1.0

    # Gradiente de sombra en el cuello inferior (y < 0.25) manteniendo PIEL LIMPIA (SIN BARBA)
    neck_factor = np.clip((0.26 - y) / 0.26, 0.0, 1.0)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - neck_factor * 0.25) + neck_skin[c] * (neck_factor * 0.25)

    # Resalte y calidez en pómulos, puente nasal y frente
    cheeks_l = np.exp(-((x - 0.36)**2 / 0.012 + (y - 0.53)**2 / 0.010))
    cheeks_r = np.exp(-((x - 0.64)**2 / 0.012 + (y - 0.53)**2 / 0.010))
    nose_bridge = np.exp(-((x - 0.50)**2 / 0.0016 + (y - 0.53)**2 / 0.022))
    forehead_warmth = np.exp(-((x - 0.50)**2 / 0.038 + (y - 0.79)**2 / 0.016))

    facial_warmth = np.clip(cheeks_l + cheeks_r + nose_bridge * 0.5 + forehead_warmth * 0.35, 0.0, 1.0)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - facial_warmth * 0.22) + warm_cheek[c] * (facial_warmth * 0.22)

    # Cuencas orbitarias suaves (sombra anatómica; sin ojos 2D)
    for eye_cx in [0.38, 0.62]:
        orbit_dist = np.sqrt(((x - eye_cx) / 0.065)**2 + ((y - 0.625)**2 / 0.036**2))
        orbit_shade = np.clip(1.0 - orbit_dist, 0.0, 1.0)**2 * 0.26
        for c in range(3):
            diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - orbit_shade) + shadow_tone[c] * orbit_shade

    # Cejas masculinas densas, arqueadas y naturales de Eli (eli3.png)
    # Ceja izquierda
    t_l = np.clip((x - 0.315) / (0.455 - 0.315), 0.0, 1.0)
    y_c_l = 0.698 + 0.020 * np.sin(t_l * np.pi * 0.85)
    dy_l = np.abs(y - y_c_l) / (0.009 + 0.015 * t_l)
    brow_l = np.clip(1.0 - dy_l, 0.0, 1.0)**0.85 * (x >= 0.315) * (x <= 0.455) * np.clip((x - 0.315)/0.016, 0.0, 1.0) * np.clip((0.455 - x)/0.012, 0.0, 1.0)

    # Ceja derecha
    t_r = np.clip((0.685 - x) / (0.685 - 0.545), 0.0, 1.0)
    y_c_r = 0.698 + 0.020 * np.sin(t_r * np.pi * 0.85)
    dy_r = np.abs(y - y_c_r) / (0.009 + 0.015 * t_r)
    brow_r = np.clip(1.0 - dy_r, 0.0, 1.0)**0.85 * (x >= 0.545) * (x <= 0.685) * np.clip((0.685 - x)/0.016, 0.0, 1.0) * np.clip((x - 0.545)/0.012, 0.0, 1.0)

    eyebrows = np.clip(np.maximum(brow_l, brow_r), 0.0, 1.0)
    brow_col = np.array([0.090, 0.070, 0.055], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - eyebrows * 0.95) + brow_col[c] * (eyebrows * 0.95)

    # Barba perfilada y bigote completos fieles a eli3.png:
    # Delimitación precisa: LA BARBA TERMINA EN LA LÍNEA MANDIBULAR (y >= 0.26)
    dx_jaw = np.abs(x - 0.50)

    # Límite inferior estricto en la mandíbula (bajo la mandíbula es piel limpia)
    y_jaw_bone = 0.265 + 0.38 * np.maximum(0.0, (dx_jaw - 0.04) / 0.23)**1.5
    lower_mask = np.clip((y - (y_jaw_bone - 0.025)) / 0.020, 0.0, 1.0)

    # Límite superior en las mejillas: desciende suavemente de patillas a comisuras
    t_cheek = np.clip((dx_jaw - 0.06) / 0.18, 0.0, 1.0)
    y_cheek_upper = 0.395 + 0.125 * (t_cheek**1.1)
    upper_mask = np.clip((y_cheek_upper - y) / 0.025, 0.0, 1.0)

    # Límite lateral en patillas
    lat_mask = np.clip((0.265 - dx_jaw) / 0.020, 0.0, 1.0)

    # Hendidura anatómica entre labio inferior y mentón
    lip_gap = np.clip(1.0 - np.sqrt((dx_jaw / 0.038)**2 + ((y - 0.362) / 0.018)**2), 0.0, 1.0) * (y > 0.33) * (dx_jaw > 0.015)

    # Mosca / Soul Patch centrado bajo el labio inferior (eli3.png)
    soul_patch = np.clip(1.0 - np.sqrt((dx_jaw / 0.018)**2 + ((y - 0.345) / 0.022)**2), 0.0, 1.0)**1.3

    # Masa completa de barba en mentón, mandíbula y mejilla
    beard_mass = lower_mask * upper_mask * lat_mask * (1.0 - lip_gap * 0.95)

    # Bigote continuo sobre labio superior con hendidura en filtrum (eli3.png)
    dx_stache = dx_jaw / 0.085
    dy_stache = (y - 0.442) / 0.024
    stache_base = np.clip(1.0 - np.sqrt(dx_stache**2 + dy_stache**2), 0.0, 1.0)**1.2
    stache_gap = np.clip(dx_jaw / 0.010, 0.40, 1.0)
    stache_base *= stache_gap

    # Comisuras que unen bigote con la mandíbula
    comm_l = np.clip(1.0 - np.sqrt(((x - 0.425) / 0.024)**2 + ((y - 0.385) / 0.042)**2), 0.0, 1.0)**1.2
    comm_r = np.clip(1.0 - np.sqrt(((x - 0.575) / 0.024)**2 + ((y - 0.385) / 0.042)**2), 0.0, 1.0)**1.2

    beard_total = np.clip(np.maximum.reduce([beard_mass, soul_patch, stache_base, comm_l, comm_r]), 0.0, 1.0)

    # Color de barba y vello facial de Eli: castaño muy oscuro natural
    beard_col = np.array([0.115, 0.085, 0.068], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - beard_total * 0.93) + beard_col[c] * (beard_total * 0.93)

    # Labios con sonrisa suave y bermellón natural (y ~ 0.385 - 0.415)
    dx_lip = (x - 0.50) / 0.065
    dy_lip = (y - 0.392) / 0.018
    lip_mask = np.clip(1.0 - np.sqrt(dx_lip**2 + dy_lip**2), 0.0, 1.0)**1.3
    smile_curve = 0.005 * (1.0 - np.clip(dx_lip**2, 0.0, 1.0))
    dy_split = np.abs(y - (0.391 + smile_curve)) / 0.004
    lip_split = np.clip(1.0 - dy_split, 0.0, 1.0) * (np.abs(dx_lip) < 0.85)

    lip_col = np.array([0.76, 0.47, 0.42], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lip_mask * 0.58) + lip_col[c] * (lip_mask * 0.58)
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lip_split * 0.60) + 0.16 * (lip_split * 0.60)

    # Aletas nasales
    nostril_l = np.clip(1.0 - np.sqrt(((x - 0.486) / 0.011)**2 + ((y - 0.510) / 0.007)**2), 0.0, 1.0)**2
    nostril_r = np.clip(1.0 - np.sqrt(((x - 0.514) / 0.011)**2 + ((y - 0.510) / 0.007)**2), 0.0, 1.0)**2
    nostrils = np.maximum(nostril_l, nostril_r)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - nostrils * 0.40) + shadow_tone[c] * (nostrils * 0.40)

    # Microporos y micro-textura de vello
    xx = np.linspace(0, 56 * np.pi, w)[None, :]
    yy = np.linspace(0, 56 * np.pi, h)[:, None]
    pore_noise = (np.sin(xx * 2.3 + yy * 3.1) * 0.020 + np.cos(xx * 3.7 - yy * 2.5) * 0.020)
    stubble_noise = (np.sin(xx * 5.2 + yy * 6.8) * 0.035 + np.cos(xx * 6.5 - yy * 5.1) * 0.035) * beard_total

    height = (eyebrows * 0.28) + (beard_total * 0.20) + (lip_mask * 0.14) - (lip_split * 0.20) + pore_noise + stubble_noise
    normal = height_to_normal_map(height, scale=1.4)

    paths_d = [os.path.join(TEXTURES_DIR, "eli_face_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_face_diffuse.png")]
    paths_n = [os.path.join(TEXTURES_DIR, "eli_face_normal.png"), os.path.join(CITIZENS_DIR, "eli_face_normal.png")]
    save_numpy_image("eli_face_diffuse", diffuse, paths_d)
    save_numpy_image("eli_face_normal", normal, paths_n)

# =============================================================================
# 2. PECHO ANATÓMICO CON VELLO PECTORAL PROCEDURAL SEGÚN ELI2.PNG (1024x1024)
# =============================================================================
def generate_chest_textures():
    print("-> Sintetizando mapas PBR para Pecho y Vello Pectoral de Eli basados en eli2.png...")
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    u = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :]
    v = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]

    np.random.seed(505)

    # Base dérmica del pecho idéntica a la piel de Eli
    base_skin = np.array([0.865, 0.685, 0.605], dtype=np.float32)
    warm_chest = np.array([0.885, 0.620, 0.540], dtype=np.float32)

    for c in range(3):
        diffuse[:, :, c] = base_skin[c]
    diffuse[:, :, 3] = 1.0

    # Sombra del esternón / hendidura interpectoral en el centro (u = 0.50)
    du_mid = np.abs(u - 0.50)
    sternum_shade = np.exp(-(du_mid**2 / 0.005 + (v - 0.45)**2 / 0.25)) * 0.12
    for c in range(3):
        diffuse[:, :, c] -= sternum_shade

    # Calidez sobre la masa pectoral izquierda y derecha
    pec_l = np.exp(-((u - 0.32)**2 / 0.016 + (v - 0.55)**2 / 0.040))
    pec_r = np.exp(-((u - 0.68)**2 / 0.016 + (v - 0.55)**2 / 0.040))
    pec_warmth = np.clip(pec_l + pec_r, 0.0, 1.0)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - pec_warmth * 0.15) + warm_chest[c] * (pec_warmth * 0.15)

    # Generación de hebras de vello pectoral natural (eli2.png)
    # Cerca de 1400 hebras curvas rizadas distribuidas orgánicamente
    hair_layer = np.zeros((h, w), dtype=np.float32)
    num_strands = 1400
    for _ in range(num_strands):
        # Mayor densidad en la línea del esternón y zona pectoral media/alta
        cx = np.random.normal(0.50, 0.12)
        cy = np.random.uniform(0.12, 0.92)
        if cx < 0.10 or cx > 0.90:
            continue
        length = np.random.uniform(0.018, 0.042)
        angle = np.random.uniform(-np.pi, np.pi)
        curl = np.random.uniform(-3.8, 3.8)

        t_steps = 18
        t_arr = np.linspace(0, 1, t_steps)
        px = cx + length * (t_arr * np.cos(angle) + curl * 0.25 * (t_arr**2) * np.sin(angle))
        py = cy + length * (t_arr * np.sin(angle) - curl * 0.25 * (t_arr**2) * np.cos(angle))

        ix = np.clip((px * (w - 1)).astype(np.int32), 0, w - 1)
        iy = np.clip((py * (h - 1)).astype(np.int32), 0, h - 1)
        hair_layer[iy, ix] = 1.0

    # Dilatar hebras para grosor perceptible de 1-2 píxeles
    hair_strands = np.maximum.reduce([
        hair_layer,
        np.roll(hair_layer, 1, axis=0),
        np.roll(hair_layer, -1, axis=0),
        np.roll(hair_layer, 1, axis=1),
        np.roll(hair_layer, -1, axis=1)
    ])

    # Envolvente anatómica de distribución del vello pectoral (eli2.png):
    # Centrado en el esternón, extendiéndose en el escote en V
    envelope = np.exp(-(du_mid**2 / 0.042)) * np.clip(1.0 - (v - 0.72)**2 / 0.22, 0.30, 1.0)
    hair_final = np.clip(hair_strands * envelope * 0.96, 0.0, 1.0)

    hair_dark = np.array([0.095, 0.070, 0.052], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - hair_final * 0.94) + hair_dark[c] * (hair_final * 0.94)

    # Relieve de hebras en el Normal Map
    pore_noise = (np.sin(u * 80.0) * np.cos(v * 80.0)) * 0.015
    chest_height = hair_final * 0.35 + pore_noise - sternum_shade * 0.15
    chest_normal = height_to_normal_map(chest_height, scale=1.7)

    paths_d = [os.path.join(TEXTURES_DIR, "eli_chest_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_chest_diffuse.png")]
    paths_n = [os.path.join(TEXTURES_DIR, "eli_chest_normal.png"), os.path.join(CITIZENS_DIR, "eli_chest_normal.png")]
    save_numpy_image("eli_chest_diffuse", diffuse, paths_d)
    save_numpy_image("eli_chest_normal", chest_normal, paths_n)

# =============================================================================
# 3. CAMISA RESORT / CUELLO CAMP EN V (LINO CREMA / MARFIL SEGÚN ELI2.PNG)
# =============================================================================
def generate_resort_shirt_textures():
    print("-> Generando texturas PBR para Camisa Resort de Lino Crema en V (eli2.png)...")
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)

    # Tono lino crema / marfil cálido calibrado de eli2.png
    base_linen = np.array([0.865, 0.855, 0.785], dtype=np.float32)

    # Trama textil fina de lino con ligeras variaciones de hilado (slubs)
    xx = np.linspace(0, 96 * np.pi, w)[None, :]
    yy = np.linspace(0, 96 * np.pi, h)[:, None]
    linen_weave = (np.sin(xx) * 0.012 + np.cos(yy) * 0.012)
    slubs = (np.sin(xx * 0.25 + yy * 0.33) * 0.010 + np.cos(xx * 0.45 - yy * 0.20) * 0.008)

    for c in range(3):
        diffuse[:, :, c] = base_linen[c] + linen_weave + slubs
    diffuse[:, :, 3] = 1.0

    shirt_height = linen_weave * 0.7 + slubs * 0.5
    shirt_normal = height_to_normal_map(shirt_height, scale=1.2)

    # Guardar tanto en eli_resort_shirt como en eli_shirt para máxima compatibilidad
    for base_name in ["eli_resort_shirt", "eli_shirt"]:
        save_numpy_image(f"{base_name}_diffuse", diffuse,
                         [os.path.join(TEXTURES_DIR, f"{base_name}_diffuse.png"),
                          os.path.join(CITIZENS_DIR, f"{base_name}_diffuse.png")])
        save_numpy_image(f"{base_name}_normal", shirt_normal,
                         [os.path.join(TEXTURES_DIR, f"{base_name}_normal.png"),
                          os.path.join(CITIZENS_DIR, f"{base_name}_normal.png")])

# =============================================================================
# 4. PANTALÓN CHINO Y ACCESORIOS (ZAPATOS, CINTURÓN, GAFAS, BOTONES)
# =============================================================================
def generate_pants_and_accessories():
    print("-> Generando texturas PBR para Pantalón Chino y Accesorios...")
    w, h = 1024, 1024

    # Pantalón chino en tono arena cálido / caqui elegante
    pants_diffuse = np.zeros((h, w, 4), dtype=np.float32)
    base_pants = np.array([0.760, 0.710, 0.635], dtype=np.float32)
    xx = np.linspace(0, 64 * np.pi, w)[None, :]
    yy = np.linspace(0, 64 * np.pi, h)[:, None]
    twill = (np.sin(xx + yy) * 0.014 + np.sin(xx - yy) * 0.014)
    for c in range(3):
        pants_diffuse[:, :, c] = base_pants[c] + twill
    pants_diffuse[:, :, 3] = 1.0
    pants_normal = height_to_normal_map(twill, scale=1.3)

    save_numpy_image("eli_pants_diffuse", pants_diffuse,
                     [os.path.join(TEXTURES_DIR, "eli_pants_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_pants_diffuse.png")])
    save_numpy_image("eli_pants_normal", pants_normal,
                     [os.path.join(TEXTURES_DIR, "eli_pants_normal.png"), os.path.join(CITIZENS_DIR, "eli_pants_normal.png")])

    # Zapatos casuales / mocasines en cuero café pulido
    shoes_diffuse = np.zeros((512, 512, 4), dtype=np.float32)
    base_leather = np.array([0.22, 0.12, 0.08], dtype=np.float32)
    sxx = np.linspace(0, 32 * np.pi, 512)[None, :]
    syy = np.linspace(0, 32 * np.pi, 512)[:, None]
    lgrain = (np.sin(sxx * 2.0 + syy * 3.0) * 0.015 + np.cos(sxx * 3.0 - syy * 2.0) * 0.015)
    for c in range(3):
        shoes_diffuse[:, :, c] = base_leather[c] + lgrain
    shoes_diffuse[:, :, 3] = 1.0
    shoes_normal = height_to_normal_map(lgrain, scale=1.2)

    save_numpy_image("eli_shoes_diffuse", shoes_diffuse,
                     [os.path.join(TEXTURES_DIR, "eli_shoes_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_shoes_diffuse.png")])
    save_numpy_image("eli_shoes_normal", shoes_normal,
                     [os.path.join(TEXTURES_DIR, "eli_shoes_normal.png"), os.path.join(CITIZENS_DIR, "eli_shoes_normal.png")])

    # Cinturón
    save_numpy_image("eli_belt_diffuse", shoes_diffuse,
                     [os.path.join(TEXTURES_DIR, "eli_belt_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_belt_diffuse.png")])
    save_numpy_image("eli_belt_normal", shoes_normal,
                     [os.path.join(TEXTURES_DIR, "eli_belt_normal.png"), os.path.join(CITIZENS_DIR, "eli_belt_normal.png")])

    # Gafas de acetato negro satinado (eli2.png)
    glasses_diffuse = np.zeros((512, 512, 4), dtype=np.float32)
    for c in range(3):
        glasses_diffuse[:, :, c] = 0.05
    glasses_diffuse[:, :, 3] = 1.0
    glasses_normal = np.zeros((512, 512, 4), dtype=np.float32)
    glasses_normal[:, :, 0] = 0.5
    glasses_normal[:, :, 1] = 0.5
    glasses_normal[:, :, 2] = 1.0
    glasses_normal[:, :, 3] = 1.0

    save_numpy_image("eli_glasses_diffuse", glasses_diffuse,
                     [os.path.join(TEXTURES_DIR, "eli_glasses_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_glasses_diffuse.png")])
    save_numpy_image("eli_glasses_normal", glasses_normal,
                     [os.path.join(TEXTURES_DIR, "eli_glasses_normal.png"), os.path.join(CITIZENS_DIR, "eli_glasses_normal.png")])

    # Botones nacarados / de hueso para la camisa
    btn_diffuse = np.zeros((256, 256, 4), dtype=np.float32)
    btn_col = np.array([0.91, 0.89, 0.84], dtype=np.float32)
    for c in range(3):
        btn_diffuse[:, :, c] = btn_col[c]
    btn_diffuse[:, :, 3] = 1.0
    save_numpy_image("eli_button_diffuse", btn_diffuse,
                     [os.path.join(TEXTURES_DIR, "eli_button_diffuse.png"), os.path.join(CITIZENS_DIR, "eli_button_diffuse.png")])

# =============================================================================
# 5. OJOS 3D (ESCLERÓTICA, IRIS CASTAÑO CÁLIDO, PUPILA)
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

    m_pupil = (r < r_pupil)
    m_iris = (r >= r_pupil) & (r < r_iris)
    m_limbus = (r >= r_iris) & (r < r_limbus)

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

def main():
    print("================================================================")
    print("SINTETIZANDO SUITE CANÓNICA DE TEXTURAS PBR PROCEDURALES DE ELI")
    print("================================================================")
    generate_face_textures()
    generate_chest_textures()
    generate_resort_shirt_textures()
    generate_pants_and_accessories()
    generate_eye_texture()
    print("================================================================")
    print("✓ SUITE DE TEXTURAS PBR DE ELI COMPLETADA EXITOSAMENTE")
    print("================================================================")

if __name__ == "__main__":
    main()
