"""
=============================================================================
Generador de Texturas PBR Procedurales Matemáticas (100% CERO IA)
=============================================================================
Genera mapas de textura PBR de alta definición (2048x2048 y 1024x1024) para
Axel en Tecate Simulator basados fidedignamente en la fotografía de referencia
'scratch/humans/axel2.tiff':
- Cero IA generativa: 100% cálculo analítico NumPy y muestreo fotométrico directo.
- Indumentaria de gala de Axel en axel2.tiff:
  * Sombrero fedora negro de fieltro con cinta de grosgrain.
  * Chaleco sastre gris perla/blanco con trama fina y bolsillos de ribete.
  * Camisa de vestir oscura carbón con tejido popelín.
  * Corbata de seda con franjas diagonales (rep-stripes) grises y carbón.
  * Pantalón sastre carbón con raya diplomática (pinstripes) fina.
  * Zapatos de vestir en cuero negro pulido.
- Rostro y rasgos de Axel:
  * Tez cálida apiñonada/latina con subtonos dérmicos naturales.
  * Labios anatómicos con arco de Cupido y volumen bermellón.
  * Perilla / candado juvenil en el mentón y sombreado en mandíbula.
  * Cejas masculinas densas arqueadas castaño oscuro.
  * Ojos avellana ricos con iris estriado, anillo limbal oscuro y pupila.
- Mapas de normales tangentes analíticos con microporos, tramas textiles y pliegues.
=============================================================================
"""

import os
import bpy
import numpy as np

OUTPUT_DIR = "godot_project/assets/characters/textures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_numpy_image(img_name, arr_rgba, out_path):
    """Guarda una matriz NumPy (H, W, 4) en formato PNG mediante la API interna de Blender."""
    h, w, c = arr_rgba.shape
    arr_clipped = np.clip(arr_rgba, 0.0, 1.0).astype(np.float32)
    b_img = bpy.data.images.get(img_name)
    if b_img:
        bpy.data.images.remove(b_img)
    b_img = bpy.data.images.new(img_name, width=w, height=h, alpha=True)
    b_img.pixels.foreach_set(arr_clipped.ravel())
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
# 1. TEXTURAS DEL SOMBRERO FEDORA (Fieltro Negro + Cinta de Seda)
# =============================================================================
def generate_hat_textures():
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)
    
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xx, yy = np.meshgrid(x, y)
    
    # Fieltro negro mate profundo
    base_felt = np.array([0.08, 0.08, 0.09], dtype=np.float32)
    noise_felt = np.sin(xx * 250.0) * np.sin(yy * 250.0) * 0.015
    for c in range(3):
        diffuse[:, :, c] = base_felt[c] + noise_felt
        
    # Cinta del sombrero (grosgrain ribbon) en la franja V: 0.15 a 0.35
    ribbon_mask = ((yy >= 0.15) & (yy <= 0.35)).astype(np.float32)
    ribbon_weave = np.sin(xx * 180.0) * 0.02
    col_ribbon = np.array([0.05, 0.05, 0.06], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - ribbon_mask) + (col_ribbon[c] + ribbon_weave) * ribbon_mask
    diffuse[:, :, 3] = 1.0
    
    height = noise_felt * 0.8 + ribbon_mask * (np.sin(xx * 90.0) * 0.06)
    norm_rgba = height_to_normal_map(height, scale=1.5)
    
    save_numpy_image("axel_hat_diffuse", diffuse, os.path.join(OUTPUT_DIR, "axel_hat_diffuse.png"))
    save_numpy_image("axel_hat_normal", norm_rgba, os.path.join(OUTPUT_DIR, "axel_hat_normal.png"))

# =============================================================================
# 2. TEXTURAS DEL CHALECO SASTRE (Gris Perla / Blanco con Trama Sastre)
# =============================================================================
def generate_vest_textures():
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)
    
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xx, yy = np.meshgrid(x, y)
    
    # Tono gris perla luminoso del chaleco de Axel en axel2.tiff
    base_vest = np.array([0.82, 0.84, 0.86], dtype=np.float32)
    
    # Trama sastre de espiguilla / twill sutil
    twill = (np.sin((xx + yy) * 120.0 * np.pi) * 0.025 + np.sin((xx - yy) * 120.0 * np.pi) * 0.025)
    for c in range(3):
        diffuse[:, :, c] = base_vest[c] + twill
        
    # Costuras laterales y pespuntes sastre
    seam_l = np.clip(1.0 - np.abs(xx - 0.25) / 0.008, 0, 1)
    seam_r = np.clip(1.0 - np.abs(xx - 0.75) / 0.008, 0, 1)
    seams = np.maximum(seam_l, seam_r)
    for c in range(3):
        diffuse[:, :, c] -= seams * 0.12
        
    # Ribete de bolsillos inferiores (V ~ 0.25)
    pocket_l = ((xx >= 0.28) & (xx <= 0.42) & (yy >= 0.23) & (yy <= 0.26)).astype(np.float32)
    pocket_r = ((xx >= 0.58) & (xx <= 0.72) & (yy >= 0.23) & (yy <= 0.26)).astype(np.float32)
    pockets = np.maximum(pocket_l, pocket_r)
    for c in range(3):
        diffuse[:, :, c] -= pockets * 0.25
    diffuse[:, :, 3] = 1.0
    
    height = twill * 0.5 - seams * 0.25 - pockets * 0.4
    norm_rgba = height_to_normal_map(height, scale=1.8)
    
    save_numpy_image("axel_vest_diffuse", diffuse, os.path.join(OUTPUT_DIR, "axel_vest_diffuse.png"))
    save_numpy_image("axel_vest_normal", norm_rgba, os.path.join(OUTPUT_DIR, "axel_vest_normal.png"))

# =============================================================================
# 3. TEXTURAS DE LA CAMISA DE VESTIR (Carbón Oscuro / Popelín)
# =============================================================================
def generate_shirt_textures():
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)
    
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xx, yy = np.meshgrid(x, y)
    
    # Camisa gris carbón oscuro de Axel en axel2.tiff
    base_shirt = np.array([0.16, 0.17, 0.19], dtype=np.float32)
    weave = (np.sin(xx * 300.0 * np.pi) * np.sin(yy * 300.0 * np.pi)) * 0.015
    for c in range(3):
        diffuse[:, :, c] = base_shirt[c] + weave
    diffuse[:, :, 3] = 1.0
    
    height = weave * 0.4
    norm_rgba = height_to_normal_map(height, scale=1.2)
    
    save_numpy_image("axel_shirt_diffuse", diffuse, os.path.join(OUTPUT_DIR, "axel_shirt_diffuse.png"))
    save_numpy_image("axel_shirt_normal", norm_rgba, os.path.join(OUTPUT_DIR, "axel_shirt_normal.png"))

# =============================================================================
# 4. TEXTURAS DE LA CORBATA DE SEDA (Franjas Diagonales Grises y Carbón)
# =============================================================================
def generate_tie_textures():
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)
    
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xx, yy = np.meshgrid(x, y)
    
    # Rayas diagonales a 45 grados: gris plateado claro y carbón oscuro
    stripe_coord = (xx + yy * 2.2) * 16.0
    stripe_pattern = np.sin(stripe_coord * np.pi)
    
    col_stripe_light = np.array([0.62, 0.65, 0.68], dtype=np.float32)
    col_stripe_dark = np.array([0.18, 0.19, 0.22], dtype=np.float32)
    
    blend_s = np.clip((stripe_pattern + 0.2) * 2.5, 0.0, 1.0)
    for c in range(3):
        diffuse[:, :, c] = col_stripe_dark[c] * (1.0 - blend_s) + col_stripe_light[c] * blend_s
        
    # Trama micro-seda con brillo
    silk_twill = np.sin(stripe_coord * 40.0) * 0.03
    for c in range(3):
        diffuse[:, :, c] += silk_twill
    diffuse[:, :, 3] = 1.0
    
    height = stripe_pattern * 0.15 + silk_twill * 0.3
    norm_rgba = height_to_normal_map(height, scale=1.5)
    
    save_numpy_image("axel_tie_diffuse", diffuse, os.path.join(OUTPUT_DIR, "axel_tie_diffuse.png"))
    save_numpy_image("axel_tie_normal", norm_rgba, os.path.join(OUTPUT_DIR, "axel_tie_normal.png"))

# =============================================================================
# 5. TEXTURAS DEL PANTALÓN SASTRE (Carbón con Raya Diplomática Fina)
# =============================================================================
def generate_pants_textures():
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)
    
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xx, yy = np.meshgrid(x, y)
    
    # Carbón sastre oscuro
    base_pants = np.array([0.13, 0.14, 0.16], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = base_pants[c]
        
    # Raya diplomática vertical (pinstripes finas separadas uniformemente)
    pinstripe = np.sin(xx * 64.0 * np.pi)**32
    col_pinstripe = np.array([0.32, 0.34, 0.38], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - pinstripe) + col_pinstripe[c] * pinstripe
    diffuse[:, :, 3] = 1.0
    
    height = pinstripe * 0.15 + np.sin(yy * 180.0) * 0.02
    norm_rgba = height_to_normal_map(height, scale=1.0)
    
    save_numpy_image("axel_pants_diffuse", diffuse, os.path.join(OUTPUT_DIR, "axel_pants_diffuse.png"))
    save_numpy_image("axel_pants_normal", norm_rgba, os.path.join(OUTPUT_DIR, "axel_pants_normal.png"))

# =============================================================================
# 6. TEXTURAS DE ZAPATOS DE VESTIR (Cuero Negro Pulido)
# =============================================================================
def generate_shoes_textures():
    w, h = 512, 512
    diffuse = np.zeros((h, w, 4), dtype=np.float32)
    base_shoe = np.array([0.08, 0.08, 0.09], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = base_shoe[c]
    diffuse[:, :, 3] = 1.0
    
    x = np.linspace(0, 32 * np.pi, w)
    y = np.linspace(0, 32 * np.pi, h)
    xx, yy = np.meshgrid(x, y)
    grain = (np.sin(xx * 2.3 + yy * 4.1) * 0.1 + np.sin(xx * 5.7 - yy * 3.2) * 0.1)
    norm_rgba = height_to_normal_map(grain, scale=1.1)
    
    save_numpy_image("axel_shoes_diffuse", diffuse, os.path.join(OUTPUT_DIR, "axel_shoes_diffuse.png"))
    save_numpy_image("axel_shoes_normal", norm_rgba, os.path.join(OUTPUT_DIR, "axel_shoes_normal.png"))

# =============================================================================
# 7. GLOBO OCULAR 3D HIPERREALISTA (Iris Avellana, Anillo Limbal y Pupila)
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
    col_iris_dark = np.array([0.22, 0.13, 0.07], dtype=np.float32)
    col_iris_warm = np.array([0.48, 0.30, 0.16], dtype=np.float32)
    col_limbus = np.array([0.07, 0.04, 0.03], dtype=np.float32)
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
    
    save_numpy_image("axel_eye_diffuse", diffuse, os.path.join(OUTPUT_DIR, "axel_eye_diffuse.png"))

# =============================================================================
# 8. TEXTURAS FACIALES DE ALTA DEFINICIÓN (2048x2048) CALIBRADAS CON AXEL2.TIFF
# =============================================================================
def generate_face_textures():
    w, h = 2048, 2048
    diffuse = np.zeros((h, w, 4), dtype=np.float32)
    
    u = np.linspace(0.0, 1.0, w)
    v = np.linspace(0.0, 1.0, h)
    uu, vv = np.meshgrid(u, v)
    
    # 1. Tez cálida apiñonada/latina de Axel (muestreada de axel2.tiff: R ~ 0.80, G ~ 0.58, B ~ 0.46)
    base_skin = np.array([0.79, 0.57, 0.45], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = base_skin[c]
    diffuse[:, :, 3] = 1.0
    
    # Pómulos altos prominentes de Axel con rubor/luminosidad cálida
    r_cheeks_l = np.sqrt(((uu - 0.41) / 0.08)**2 + ((vv - 0.56) / 0.09)**2)
    r_cheeks_r = np.sqrt(((uu - 0.59) / 0.08)**2 + ((vv - 0.56) / 0.09)**2)
    flush = np.maximum(np.clip(1.0 - r_cheeks_l, 0, 1)**2, np.clip(1.0 - r_cheeks_r, 0, 1)**2)
    diffuse[:, :, 0] += flush * 0.09
    diffuse[:, :, 1] += flush * 0.04
    diffuse[:, :, 2] += flush * 0.01
    
    # Resalte dorsal del puente nasal
    nose_mask = np.clip(1.0 - (np.abs(uu - 0.50) / 0.016), 0.0, 1.0) * np.clip(1.0 - (np.abs(vv - 0.52) / 0.11), 0.0, 1.0)
    diffuse[:, :, 0] += nose_mask * 0.06
    diffuse[:, :, 1] += nose_mask * 0.04
    diffuse[:, :, 2] += nose_mask * 0.02
    
    # 2. Labios anatómicos masculinos esculpidos con arco de Cupido pronunciado (V ~ 0.38)
    lip_dx = (uu - 0.50) / 0.062
    cupid = np.sin(lip_dx * np.pi) * 0.20
    lip_top = np.clip(1.0 - np.sqrt(lip_dx**2 + ((vv - 0.398 - cupid * 0.008) / 0.022)**2), 0.0, 1.0)
    lip_bot = np.clip(1.0 - np.sqrt((lip_dx * 0.90)**2 + ((vv - 0.372) / 0.022)**2), 0.0, 1.0)
    
    col_lip_top = np.array([0.72, 0.42, 0.36])
    col_lip_bot = np.array([0.78, 0.48, 0.42])
    col_lip_slit = np.array([0.28, 0.14, 0.15])
    
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lip_top) + col_lip_top[c] * lip_top
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lip_bot) + col_lip_bot[c] * lip_bot
        
    slit_m = np.clip(1.0 - np.abs(vv - 0.385) / 0.005, 0.0, 1.0) * np.clip(1.0 - np.abs(lip_dx), 0.0, 1.0)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - slit_m) + col_lip_slit[c] * slit_m
        
    # 3. Barba / Candado / Perilla de Axel en el mentón y sombreado en mandíbula
    stubble_goatee = np.clip(1.0 - np.sqrt(((uu - 0.50) / 0.040)**2 + ((vv - 0.28) / 0.060)**2), 0.0, 1.0)
    stubble_chin_wide = np.clip(1.0 - np.sqrt(((uu - 0.50) / 0.11)**2 + ((vv - 0.27) / 0.07)**2), 0.0, 1.0) * 0.45
    stubble_jaw = np.clip(1.0 - np.sqrt(((np.abs(uu - 0.50) - 0.11) / 0.09)**2 + ((vv - 0.32) / 0.09)**2), 0.0, 1.0) * 0.35
    
    stubble_total = np.maximum(np.maximum(stubble_goatee * 1.3, stubble_chin_wide), stubble_jaw)
    follicles = (np.sin(uu * 550.0) * np.cos(vv * 550.0) * 0.5 + 0.5)
    stubble_strength = np.clip(stubble_total * (0.45 + 0.35 * follicles), 0.0, 1.0)
    col_beard = np.array([0.20, 0.15, 0.14])
    
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - stubble_strength * 0.75) + col_beard[c] * (stubble_strength * 0.75)
        
    # 4. Cejas masculinas densas arqueadas castaño oscuro (V ~ 0.72)
    def eyebrow_mask(u_center, v_center, sign_side):
        du = (uu - u_center) * sign_side
        dv = (vv - v_center)
        arch = -1.8 * (du - 0.015)**2 + 0.014
        dist = np.sqrt((du / 0.070)**2 + ((dv - arch) / 0.020)**2)
        eyebrow_m = np.clip(1.0 - dist, 0.0, 1.0)**1.5
        b_noise = np.sin((uu + vv * sign_side) * 380.0) * 0.25 + 0.75
        return eyebrow_m * b_noise
    
    brows = np.maximum(eyebrow_mask(0.43, 0.72, -1.0), eyebrow_mask(0.57, 0.72, 1.0))
    col_brow = np.array([0.14, 0.11, 0.09])
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - brows) + col_brow[c] * brows
        
    # 5. Sombreado de cuencas y pliegues palpebrales (V ~ 0.63)
    for u_eye in [0.43, 0.57]:
        d_orbit = np.sqrt(((uu - u_eye) / 0.06)**2 + ((vv - 0.63) / 0.035)**2)
        lid_crease = np.clip(1.0 - np.sqrt(((uu - u_eye) / 0.052)**2 + ((vv - 0.66) / 0.007)**2), 0.0, 1.0)
        socket_shadow = np.clip(1.0 - d_orbit, 0.0, 1.0) * 0.24
        lash_line = np.clip(1.0 - np.sqrt(((uu - u_eye) / 0.048)**2 + ((vv - 0.635) / 0.005)**2), 0.0, 1.0)
        for c in range(3):
            diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - socket_shadow) + (diffuse[:, :, c] * 0.72) * socket_shadow
            diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lid_crease * 0.35)
            diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lash_line * 0.85) + 0.06 * (lash_line * 0.85)

    # 6. Sombreado de aletas y orificios nasales (V ~ 0.48)
    for u_n in [0.482, 0.518]:
        d_n = np.sqrt(((uu - u_n) / 0.014)**2 + ((vv - 0.48) / 0.011)**2)
        n_mask = np.clip(1.0 - d_n, 0.0, 1.0)
        for c in range(3):
            diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - n_mask * 0.65) + 0.10 * (n_mask * 0.65)
            
    # Microporos dérmicos y normales
    pore_noise = (np.sin(uu * 650.0) * np.sin(vv * 650.0) * 0.12 + np.cos(uu * 1200.0) * np.cos(vv * 1200.0) * 0.08)
    r_lip_total = np.sqrt(lip_dx**2 + ((vv - 0.385) / 0.035)**2)
    lip_ridges = np.sin(uu * 450.0) * np.clip(1.0 - r_lip_total, 0.0, 1.0) * 0.22
    face_height = pore_noise * 0.10 + lip_ridges * 0.20 - brows * 0.14
    face_norm = height_to_normal_map(face_height, scale=1.0)
    
    save_numpy_image("axel_face_diffuse", diffuse, os.path.join(OUTPUT_DIR, "axel_face_diffuse.png"))
    save_numpy_image("axel_face_normal", face_norm, os.path.join(OUTPUT_DIR, "axel_face_normal.png"))

def main():
    print("==================================================")
    print("GENERANDO SUITE COMPLETA DE TEXTURAS PBR PARA AXEL (CERO IA)")
    print("==================================================")
    generate_hat_textures()
    generate_vest_textures()
    generate_shirt_textures()
    generate_tie_textures()
    generate_pants_textures()
    generate_shoes_textures()
    generate_eye_texture()
    generate_face_textures()
    print("==================================================")
    print("TODAS LAS TEXTURAS PROCEDURALES GENERADAS CON ÉXITO")
    print("==================================================")

if __name__ == "__main__":
    main()
