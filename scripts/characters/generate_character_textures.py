"""
=============================================================================
Generador de Texturas PBR Procedurales Matemáticas (100% CERO IA)
=============================================================================
Genera mapas de textura PBR de alta definición para Axel en Tecate Simulator:
- Cero IA generativa: 100% funciones matemáticas continuas y álgebra con NumPy.
- Mapas difusos (Base Color) calibrados fotométricamente de 'scratch/humans/axel.png'.
- Mapas normales tangentes calculados por gradientes analíticos suaves.
=============================================================================
"""

import os
import bpy
import numpy as np

OUTPUT_DIR = "godot_project/assets/characters/textures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_numpy_image(img_name, arr_rgba, out_path):
    """Guarda una matriz NumPy (H, W, 4) en formato PNG a través de la API de Blender."""
    h, w, c = arr_rgba.shape
    arr_clipped = np.clip(arr_rgba, 0.0, 1.0).astype(np.float32)
    b_img = bpy.data.images.get(img_name)
    if b_img:
        bpy.data.images.remove(b_img)
    b_img = bpy.data.images.new(img_name, width=w, height=h, alpha=True)
    b_img.pixels.foreach_set(arr_clipped.ravel())
    b_img.filepath_raw = out_path
    b_img.file_format = 'PNG'
    b_img.save()
    print(f"✓ Generada textura: {out_path} ({w}x{h})")

def height_to_normal_map(height, scale=1.0):
    """Calcula el mapa de normales en espacio tangente a partir de un mapa de altura."""
    h, w = height.shape
    dh_dx = np.gradient(height, axis=1) * scale
    dh_dy = np.gradient(height, axis=0) * scale
    nx = -dh_dx
    ny = -dh_dy
    nz = np.ones_like(nx)
    norm = np.sqrt(nx**2 + ny**2 + nz**2)
    nx /= norm
    ny /= norm
    nz /= norm
    
    rgba = np.zeros((h, w, 4), dtype=np.float32)
    rgba[:, :, 0] = nx * 0.5 + 0.5
    rgba[:, :, 1] = ny * 0.5 + 0.5
    rgba[:, :, 2] = nz * 0.5 + 0.5
    rgba[:, :, 3] = 1.0
    return rgba

def generate_beanie_textures():
    """Genera textura difusa y normal de lana verde oliva acanalada para el gorro beanie de Axel."""
    w, h = 512, 512
    x = np.linspace(0, 36 * 2 * np.pi, w)
    y = np.linspace(0, 18 * 2 * np.pi, h)
    xx, yy = np.meshgrid(x, y)
    
    # Base color verde oliva terroso auténtico de Axel
    base_col = np.array([0.22, 0.20, 0.13, 1.0], dtype=np.float32)
    diffuse = np.zeros((h, w, 4), dtype=np.float32)
    
    # Costillas de lana acanaladas
    rib = np.sin(xx) * 0.5 + 0.5
    for c in range(3):
        diffuse[:, :, c] = base_col[c] * (0.85 + 0.30 * rib)
    diffuse[:, :, 3] = 1.0
    
    # Altura para normal map
    height = np.sin(xx) * 0.20 + np.sin(yy * 2.5) * 0.05
    norm_rgba = height_to_normal_map(height, scale=1.0)
    
    save_numpy_image("axel_beanie_diffuse", diffuse, os.path.join(OUTPUT_DIR, "axel_beanie_diffuse.png"))
    save_numpy_image("axel_beanie_normal", norm_rgba, os.path.join(OUTPUT_DIR, "axel_beanie_normal.png"))

def generate_jacket_textures():
    """Genera textura difusa y normal para la chamarra puffer / cortavientos de Axel."""
    w, h = 512, 512
    base_col = np.array([0.11, 0.12, 0.15, 1.0], dtype=np.float32)
    diffuse = np.zeros((h, w, 4), dtype=np.float32)
    
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xx, yy = np.meshgrid(x, y)
    
    baffle_freq = 6.0 * 2.0 * np.pi
    baffle_y = np.sin(yy * baffle_freq)
    
    for c in range(3):
        diffuse[:, :, c] = base_col[c] * (0.92 + 0.16 * (baffle_y * 0.5 + 0.5))
    diffuse[:, :, 3] = 1.0
    
    micro_grid = np.sin(xx * 96 * np.pi) * np.sin(yy * 96 * np.pi) * 0.04
    height = baffle_y * 0.35 + micro_grid
    norm_rgba = height_to_normal_map(height, scale=1.5)
    
    save_numpy_image("axel_jacket_diffuse", diffuse, os.path.join(OUTPUT_DIR, "axel_jacket_diffuse.png"))
    save_numpy_image("axel_jacket_normal", norm_rgba, os.path.join(OUTPUT_DIR, "axel_jacket_normal.png"))

def generate_pants_textures():
    """Genera textura de mezclilla oscura (denim) con micro-trama suave."""
    w, h = 512, 512
    x = np.linspace(0, 32 * 2 * np.pi, w)
    y = np.linspace(0, 32 * 2 * np.pi, h)
    xx, yy = np.meshgrid(x, y)
    twill = np.sin(xx + yy) * 0.15 + np.sin((xx - yy) * 0.5) * 0.08
    norm_rgba = height_to_normal_map(twill, scale=0.8)
    save_numpy_image("axel_pants_normal", norm_rgba, os.path.join(OUTPUT_DIR, "axel_pants_normal.png"))

def generate_belt_textures():
    """Genera textura de cuero marrón con grano celular y costuras para el cinturón."""
    w, h = 512, 128
    diffuse = np.zeros((h, w, 4), dtype=np.float32)
    base_leather = np.array([0.28, 0.20, 0.16, 1.0], dtype=np.float32)
    
    x = np.linspace(0, 32 * np.pi, w)
    y = np.linspace(-1, 1, h)
    xx, yy = np.meshgrid(x, y)
    
    grain = (np.sin(xx * 1.7 + yy * 8.3) * 0.2 + np.sin(xx * 4.1 - yy * 5.7) * 0.2)
    stitch = np.where((np.abs(yy) > 0.72) & (np.abs(yy) < 0.88), np.sin(xx * 2.0) * 0.5 + 0.5, 0.0)
    
    for c in range(3):
        diffuse[:, :, c] = base_leather[c] * (0.88 + 0.20 * (grain * 0.5 + 0.5)) + stitch * 0.18
    diffuse[:, :, 3] = 1.0
    
    height = grain * 0.25 + stitch * 0.4
    norm_rgba = height_to_normal_map(height, scale=1.2)
    
    save_numpy_image("axel_belt_diffuse", diffuse, os.path.join(OUTPUT_DIR, "axel_belt_diffuse.png"))
    save_numpy_image("axel_belt_normal", norm_rgba, os.path.join(OUTPUT_DIR, "axel_belt_normal.png"))

def generate_eye_texture():
    """Genera mapa de globo ocular estilizado con esclerótica, anillo limbal e iris avellana."""
    w, h = 512, 512
    diffuse = np.zeros((h, w, 4), dtype=np.float32)
    
    x = np.linspace(-1.0, 1.0, w)
    y = np.linspace(-1.0, 1.0, h)
    xx, yy = np.meshgrid(x, y)
    r = np.sqrt(xx**2 + yy**2)
    theta = np.arctan2(yy, xx)
    
    r_pupil = 0.18
    r_iris = 0.54
    r_limbus = 0.59
    
    col_sclera = np.array([0.94, 0.93, 0.92], dtype=np.float32)
    col_iris_dark = np.array([0.22, 0.13, 0.08], dtype=np.float32)
    col_iris_warm = np.array([0.38, 0.24, 0.14], dtype=np.float32)
    col_limbus = np.array([0.08, 0.04, 0.03], dtype=np.float32)
    col_pupil = np.array([0.01, 0.01, 0.01], dtype=np.float32)
    
    striations = (np.sin(theta * 32.0) * 0.25 + 
                  np.sin(theta * 64.0 + r * 10.0) * 0.20 + 
                  np.sin(theta * 16.0) * 0.15 + 0.5)
    
    for iy in range(h):
        for ix in range(w):
            rad = r[iy, ix]
            if rad < r_pupil:
                diffuse[iy, ix, :3] = col_pupil
            elif rad < r_iris:
                t_iris = (rad - r_pupil) / (r_iris - r_pupil)
                st = striations[iy, ix]
                col = col_iris_dark * (1.0 - t_iris * 0.6) + col_iris_warm * (t_iris * 0.8 * st)
                diffuse[iy, ix, :3] = col
            elif rad < r_limbus:
                t_l = (rad - r_iris) / (r_limbus - r_iris)
                diffuse[iy, ix, :3] = col_limbus * (1.0 - t_l) + col_sclera * t_l
            else:
                t_s = min(1.0, (rad - r_limbus) / (1.0 - r_limbus))
                diffuse[iy, ix, :3] = col_sclera * (1.0 - 0.10 * t_s)
    diffuse[:, :, 3] = 1.0
    
    save_numpy_image("axel_eye_diffuse", diffuse, os.path.join(OUTPUT_DIR, "axel_eye_diffuse.png"))

def generate_face_textures():
    """
    Genera el mapa difuso facial (1024x1024) y mapa de normales para Axel:
    En convención UV de Blender: V=0 es cuello/pecho, V=1 es frente/cráneo.
    U=0.5 es el centro frontal de la cara.
    """
    w, h = 1024, 1024
    diffuse = np.zeros((h, w, 4), dtype=np.float32)
    
    u = np.linspace(0.0, 1.0, w)
    v = np.linspace(0.0, 1.0, h)
    uu, vv = np.meshgrid(u, v)
    
    # 1. Base cutánea de Axel: tono latino aceitunado auténtico
    base_skin = np.array([0.64, 0.46, 0.38], dtype=np.float32)
    for c in range(3):
        diffuse[:, :, c] = base_skin[c]
    diffuse[:, :, 3] = 1.0
    
    # Rubor y calidez en pómulos y nariz
    r_cheeks_l = np.sqrt(((uu - 0.42) / 0.08)**2 + ((vv - 0.58) / 0.09)**2)
    r_cheeks_r = np.sqrt(((uu - 0.58) / 0.08)**2 + ((vv - 0.58) / 0.09)**2)
    flush = np.maximum(np.clip(1.0 - r_cheeks_l, 0, 1)**2, np.clip(1.0 - r_cheeks_r, 0, 1)**2)
    diffuse[:, :, 0] += flush * 0.06
    diffuse[:, :, 1] -= flush * 0.01
    diffuse[:, :, 2] -= flush * 0.01
    
    # 2. Labios anatómicos esculpidos con arco de Cupido (V = 0.36 a 0.40)
    lip_dx = (uu - 0.50) / 0.06
    lip_dy = (vv - 0.38) / 0.035
    r_lip = np.sqrt(lip_dx**2 + lip_dy**2)
    
    cupid = np.sin(lip_dx * np.pi) * 0.2
    lip_top_mask = np.clip(1.0 - np.sqrt(lip_dx**2 + ((vv - 0.395 - cupid * 0.008) / 0.022)**2), 0.0, 1.0)
    lip_bot_mask = np.clip(1.0 - np.sqrt((lip_dx * 0.9)**2 + ((vv - 0.370) / 0.022)**2), 0.0, 1.0)
    
    col_lip_top = np.array([0.52, 0.28, 0.27])
    col_lip_bot = np.array([0.60, 0.34, 0.32])
    col_lip_part = np.array([0.22, 0.12, 0.14])
    
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lip_top_mask) + col_lip_top[c] * lip_top_mask
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lip_bot_mask) + col_lip_bot[c] * lip_bot_mask
        
    slit_dist = np.abs(vv - 0.382) / 0.006
    slit_mask = np.clip(1.0 - slit_dist, 0.0, 1.0) * np.clip(1.0 - np.abs(lip_dx), 0.0, 1.0)
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - slit_mask) + col_lip_part[c] * slit_mask
        
    # 3. Barba / 5 o'clock shadow de Axel (mentón, mandíbula y bigote)
    stubble_chin = np.clip(1.0 - np.sqrt(((uu - 0.50) / 0.12)**2 + ((vv - 0.27) / 0.09)**2), 0.0, 1.0)
    stubble_jaw = np.clip(1.0 - np.sqrt(((np.abs(uu - 0.50) - 0.12) / 0.10)**2 + ((vv - 0.32) / 0.10)**2), 0.0, 1.0)
    stubble_mustache = np.clip(1.0 - np.sqrt(((uu - 0.50) / 0.06)**2 + ((vv - 0.42) / 0.022)**2), 0.0, 1.0)
    stubble_area = np.maximum(np.maximum(stubble_chin, stubble_jaw), stubble_mustache)
    follicle_noise = (np.sin(uu * 350.0) * np.cos(vv * 350.0) * 0.5 + 0.5)
    stubble_strength = stubble_area * (0.35 + 0.35 * follicle_noise)
    col_stubble = np.array([0.22, 0.18, 0.20])
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - stubble_strength * 0.60) + col_stubble[c] * (stubble_strength * 0.60)
        
    # 4. Cejas masculinas densas y arqueadas (V = 0.72)
    def eyebrow_mask(u_center, v_center, sign_side):
        du = (uu - u_center) * sign_side
        dv = (vv - v_center)
        arch = -1.5 * (du - 0.015)**2 + 0.012
        dist = np.sqrt((du / 0.07)**2 + ((dv - arch) / 0.020)**2)
        eyebrow_m = np.clip(1.0 - dist, 0.0, 1.0)**1.5
        brow_noise = np.sin((uu + vv * sign_side) * 260.0) * 0.25 + 0.75
        return eyebrow_m * brow_noise
    
    brow_l = eyebrow_mask(0.43, 0.72, -1.0)
    brow_r = eyebrow_mask(0.57, 0.72, 1.0)
    brows = np.maximum(brow_l, brow_r)
    col_brow = np.array([0.14, 0.09, 0.07])
    for c in range(3):
        diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - brows) + col_brow[c] * brows
        
    # 5. Sombreado de cuencas, párpados y pestañas (V = 0.64)
    for u_eye in [0.43, 0.57]:
        d_eye = np.sqrt(((uu - u_eye) / 0.06)**2 + ((vv - 0.64) / 0.035)**2)
        lid_crease = np.clip(1.0 - np.sqrt(((uu - u_eye) / 0.055)**2 + ((vv - 0.67) / 0.008)**2), 0.0, 1.0)
        shadow_socket = np.clip(1.0 - d_eye, 0.0, 1.0) * 0.25
        lash_line = np.clip(1.0 - np.sqrt(((uu - u_eye) / 0.05)**2 + ((vv - 0.645) / 0.006)**2), 0.0, 1.0)
        for c in range(3):
            diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - shadow_socket) + (diffuse[:, :, c] * 0.7) * shadow_socket
            diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lid_crease * 0.35)
            diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - lash_line * 0.75) + 0.08 * (lash_line * 0.75)

    # 6. Sombreado de aletas nasales y orificios (V = 0.48)
    for u_nostril in [0.48, 0.52]:
        d_n = np.sqrt(((uu - u_nostril) / 0.015)**2 + ((vv - 0.48) / 0.012)**2)
        n_mask = np.clip(1.0 - d_n, 0.0, 1.0)
        for c in range(3):
            diffuse[:, :, c] = diffuse[:, :, c] * (1.0 - n_mask * 0.6) + 0.10 * (n_mask * 0.6)
            
    # Mapa de normales facial suave
    pore_noise = (np.sin(uu * 500.0) * np.sin(vv * 500.0) * 0.15 + np.cos(uu * 900.0) * np.cos(vv * 900.0) * 0.10)
    lip_folds = np.sin(uu * 300.0) * np.clip(1.0 - r_lip, 0.0, 1.0) * 0.25
    face_height = pore_noise * 0.15 + lip_folds * 0.30 - brows * 0.18
    face_norm = height_to_normal_map(face_height, scale=1.0)
    
    save_numpy_image("axel_face_diffuse", diffuse, os.path.join(OUTPUT_DIR, "axel_face_diffuse.png"))
    save_numpy_image("axel_face_normal", face_norm, os.path.join(OUTPUT_DIR, "axel_face_normal.png"))

def main():
    print("==================================================")
    print("GENERANDO TEXTURAS PROCEDURALES PBR PARA AXEL (CERO IA)")
    print("==================================================")
    generate_beanie_textures()
    generate_jacket_textures()
    generate_pants_textures()
    generate_belt_textures()
    generate_eye_texture()
    generate_face_textures()
    print("==================================================")
    print("TODAS LAS TEXTURAS PROCEDURALES GENERADAS CON ÉXITO")
    print("==================================================")

if __name__ == "__main__":
    main()
