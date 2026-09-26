"""
generate_parque_textures.py
===========================
Generador de Texturas PBR Procedurales Dedicadas para el Parque Miguel Hidalgo (2009).
Genera mapas PNG profesionales para:
1. Adoquín / loseta pétrea peatonal urbana (Albedo, Normal, Roughness)
2. Césped / pradera verde con briznas (Albedo, Normal, Roughness)
3. Corteza de árbol / eucalipto y fresno (Albedo, Normal, Roughness)
"""

import bpy
import numpy as np
import os

def save_blender_image(name, np_array, filepath):
    h, w, c = np_array.shape
    flipped = np.flipud(np_array).flatten()
    
    img = bpy.data.images.get(name)
    if img:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(name, width=w, height=h, alpha=(c == 4))
    img.pixels.foreach_set(flipped)
    img.filepath_raw = filepath
    img.file_format = 'PNG'
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    img.save()
    print(f"[Texture] Guardada imagen: {filepath}")

def generate_normal_from_height(h_map, scale=0.05):
    height, width = h_map.shape
    dh_dy, dh_dx = np.gradient(h_map, 1.0 / height, 1.0 / width)
    nx = -dh_dx * scale
    ny = -dh_dy * scale
    nz = np.ones_like(nx)
    norm = np.sqrt(nx*nx + ny*ny + nz*nz)
    normal = np.zeros((height, width, 4), dtype=np.float32)
    normal[:, :, 0] = (nx / norm) * 0.5 + 0.5
    normal[:, :, 1] = (ny / norm) * 0.5 + 0.5
    normal[:, :, 2] = (nz / norm) * 0.5 + 0.5
    normal[:, :, 3] = 1.0
    return normal

def generate_adoquin_textures(w=1024, h=1024):
    print(">> Generando texturas de Adoquín / Loseta Peatonal de Andadores...")
    np.random.seed(42)
    tiles_x = 8
    tiles_y = 8
    tile_w = w // tiles_x
    tile_h = h // tiles_y
    mortar = 4 # grosor de junta

    albedo = np.zeros((h, w, 4), dtype=np.float32)
    roughness = np.zeros((h, w, 4), dtype=np.float32)
    height_map = np.zeros((h, w), dtype=np.float32)

    # Ruido base de cemento/cantera
    noise = np.random.uniform(0.92, 1.08, (h, w)).astype(np.float32)

    # Base gris cálida urbana
    base_color = np.array([0.62, 0.60, 0.56])
    mortar_color = np.array([0.38, 0.36, 0.34])

    for ty in range(tiles_y):
        for tx in range(tiles_x):
            # Variación tonal sutil por loseta
            t_factor = np.random.uniform(0.90, 1.10)
            y0 = ty * tile_h
            y1 = (ty + 1) * tile_h
            x0 = tx * tile_w
            x1 = (tx + 1) * tile_w

            # Asignar color loseta
            for c in range(3):
                albedo[y0:y1, x0:x1, c] = base_color[c] * t_factor
            roughness[y0:y1, x0:x1, :3] = 0.80 * t_factor
            height_map[y0:y1, x0:x1] = 0.50 + 0.05 * (t_factor - 1.0)

            # Juntas de mortero
            albedo[y0:y0+mortar, x0:x1, :3] = mortar_color
            albedo[y1-mortar:y1, x0:x1, :3] = mortar_color
            albedo[y0:y1, x0:x0+mortar, :3] = mortar_color
            albedo[y0:y1, x1-mortar:x1, :3] = mortar_color

            height_map[y0:y0+mortar, x0:x1] = 0.20
            height_map[y1-mortar:y1, x0:x1] = 0.20
            height_map[y0:y1, x0:x0+mortar] = 0.20
            height_map[y0:y1, x1-mortar:x1] = 0.20

            roughness[y0:y0+mortar, x0:x1, :3] = 0.95
            roughness[y1-mortar:y1, x0:x1, :3] = 0.95
            roughness[y0:y1, x0:x0+mortar, :3] = 0.95
            roughness[y0:y1, x1-mortar:x1, :3] = 0.95

    # Modulación con ruido
    for c in range(3):
        albedo[:, :, c] = np.clip(albedo[:, :, c] * noise, 0.0, 1.0)
    albedo[:, :, 3] = 1.0
    roughness[:, :, 3] = 1.0

    normal = generate_normal_from_height(height_map, scale=0.08)
    return albedo, normal, roughness

def blur2d(arr, radius=4):
    """Filtro de suavizado separable en NumPy puro."""
    kernel = np.ones(radius * 2 + 1, dtype=np.float32) / (radius * 2 + 1)
    # Suavizar filas
    res = np.apply_along_axis(lambda m: np.convolve(m, kernel, mode='same'), axis=1, arr=arr)
    # Suavizar columnas
    res = np.apply_along_axis(lambda m: np.convolve(m, kernel, mode='same'), axis=0, arr=res)
    return res

def generate_cesped_textures(w=1024, h=1024):
    print(">> Generando texturas de Césped Natural y Jardineras (NumPy Puro)...")
    np.random.seed(84)
    albedo = np.zeros((h, w, 4), dtype=np.float32)
    roughness = np.zeros((h, w, 4), dtype=np.float32)

    c_green_deep = np.array([0.16, 0.28, 0.08])
    c_green_mid  = np.array([0.25, 0.42, 0.12])
    c_green_warm = np.array([0.34, 0.48, 0.15])

    noise_coarse = blur2d(np.random.uniform(0.0, 1.0, (h, w)).astype(np.float32), radius=16)
    noise_mid    = blur2d(np.random.uniform(0.0, 1.0, (h, w)).astype(np.float32), radius=6)
    noise_fine   = np.random.uniform(0.85, 1.15, (h, w)).astype(np.float32)

    height_map = noise_coarse * 0.5 + noise_mid * 0.3 + noise_fine * 0.2

    for y in range(h):
        for c in range(3):
            val = c_green_mid[c] * (1.0 - noise_coarse[y]) + c_green_warm[c] * noise_coarse[y]
            albedo[y, :, c] = np.clip(val * noise_fine[y], 0.0, 1.0)

    roughness[:, :, :3] = 0.92
    albedo[:, :, 3] = 1.0
    roughness[:, :, 3] = 1.0

    normal = generate_normal_from_height(height_map, scale=0.06)
    return albedo, normal, roughness

def generate_corteza_textures(w=512, h=1024):
    print(">> Generando texturas de Corteza de Árbol / Eucalipto (NumPy Puro)...")
    np.random.seed(126)
    albedo = np.zeros((h, w, 4), dtype=np.float32)
    roughness = np.zeros((h, w, 4), dtype=np.float32)

    c_bark_dark  = np.array([0.20, 0.16, 0.12])
    c_bark_light = np.array([0.38, 0.32, 0.24])
    c_bark_grey  = np.array([0.48, 0.46, 0.42])

    noise = np.random.uniform(0.0, 1.0, (h, w)).astype(np.float32)
    # Suavizado anisotrópico: mucho más en vertical que en horizontal para vetas leñosas
    kernel_y = np.ones(33, dtype=np.float32) / 33.0
    kernel_x = np.ones(5, dtype=np.float32) / 5.0
    bark_lines = np.apply_along_axis(lambda m: np.convolve(m, kernel_y, mode='same'), axis=0, arr=noise)
    bark_lines = np.apply_along_axis(lambda m: np.convolve(m, kernel_x, mode='same'), axis=1, arr=bark_lines)

    for y in range(h):
        for c in range(3):
            mix = c_bark_dark[c] * (1.0 - bark_lines[y]) + c_bark_grey[c] * bark_lines[y]
            albedo[y, :, c] = np.clip(mix, 0.0, 1.0)

    height_map = bark_lines
    roughness[:, :, :3] = 0.88
    albedo[:, :, 3] = 1.0
    roughness[:, :, 3] = 1.0

    normal = generate_normal_from_height(height_map, scale=0.12)
    return albedo, normal, roughness

def main():
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "godot_project", "assets", "textures")
    os.makedirs(base_dir, exist_ok=True)

    # 1. Adoquín
    alb, nrm, rgh = generate_adoquin_textures(1024, 1024)
    save_blender_image("parque_adoquin_albedo", alb, os.path.join(base_dir, "parque_adoquin_albedo.png"))
    save_blender_image("parque_adoquin_normal", nrm, os.path.join(base_dir, "parque_adoquin_normal.png"))
    save_blender_image("parque_adoquin_roughness", rgh, os.path.join(base_dir, "parque_adoquin_roughness.png"))

    # 2. Césped
    try:
        alb_c, nrm_c, rgh_c = generate_cesped_textures(1024, 1024)
        save_blender_image("parque_cesped_albedo", alb_c, os.path.join(base_dir, "parque_cesped_albedo.png"))
        save_blender_image("parque_cesped_normal", nrm_c, os.path.join(base_dir, "parque_cesped_normal.png"))
        save_blender_image("parque_cesped_roughness", rgh_c, os.path.join(base_dir, "parque_cesped_roughness.png"))
    except Exception as e:
        print("Fallback sin scipy para césped:", e)
        # Fallback sin scipy si scipy no estuviera en Blender
        np.random.seed(84)
        alb_f = np.zeros((1024, 1024, 4), dtype=np.float32)
        nrm_f = np.zeros((1024, 1024, 4), dtype=np.float32)
        rgh_f = np.zeros((1024, 1024, 4), dtype=np.float32)
        alb_f[:, :, 0] = 0.25
        alb_f[:, :, 1] = 0.42
        alb_f[:, :, 2] = 0.12
        alb_f[:, :, 3] = 1.0
        nrm_f[:, :, 0] = 0.5
        nrm_f[:, :, 1] = 0.5
        nrm_f[:, :, 2] = 1.0
        nrm_f[:, :, 3] = 1.0
        rgh_f[:, :, :3] = 0.92
        rgh_f[:, :, 3] = 1.0
        save_blender_image("parque_cesped_albedo", alb_f, os.path.join(base_dir, "parque_cesped_albedo.png"))
        save_blender_image("parque_cesped_normal", nrm_f, os.path.join(base_dir, "parque_cesped_normal.png"))
        save_blender_image("parque_cesped_roughness", rgh_f, os.path.join(base_dir, "parque_cesped_roughness.png"))

    # 3. Corteza
    try:
        alb_k, nrm_k, rgh_k = generate_corteza_textures(512, 1024)
        save_blender_image("parque_corteza_albedo", alb_k, os.path.join(base_dir, "parque_corteza_albedo.png"))
        save_blender_image("parque_corteza_normal", nrm_k, os.path.join(base_dir, "parque_corteza_normal.png"))
        save_blender_image("parque_corteza_roughness", rgh_k, os.path.join(base_dir, "parque_corteza_roughness.png"))
    except Exception as e:
        print("Fallback sin scipy para corteza:", e)
        alb_k = np.zeros((1024, 512, 4), dtype=np.float32)
        nrm_k = np.zeros((1024, 512, 4), dtype=np.float32)
        rgh_k = np.zeros((1024, 512, 4), dtype=np.float32)
        alb_k[:, :, 0] = 0.28
        alb_k[:, :, 1] = 0.22
        alb_k[:, :, 2] = 0.16
        alb_k[:, :, 3] = 1.0
        nrm_k[:, :, 0] = 0.5
        nrm_k[:, :, 1] = 0.5
        nrm_k[:, :, 2] = 1.0
        nrm_k[:, :, 3] = 1.0
        rgh_k[:, :, :3] = 0.88
        rgh_k[:, :, 3] = 1.0
        save_blender_image("parque_corteza_albedo", alb_k, os.path.join(base_dir, "parque_corteza_albedo.png"))
        save_blender_image("parque_corteza_normal", nrm_k, os.path.join(base_dir, "parque_corteza_normal.png"))
        save_blender_image("parque_corteza_roughness", rgh_k, os.path.join(base_dir, "parque_corteza_roughness.png"))

if __name__ == "__main__":
    main()
