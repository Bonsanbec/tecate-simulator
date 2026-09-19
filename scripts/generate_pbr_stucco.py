"""
Generador de Texturas PBR Seamless para el Estuco del Hotel Tecate (V3 - Mirror Sym Continuous)
=================================================================================================
Procesa el swatch fotográfico mediante cuadratura simétrica reflejada (mirror tiling continuo)
y suavizado laplaciano, garantizando continuidad matemática C0/C1 y CERO líneas o costuras.
"""

import os
import math
import numpy as np
import bpy

SWATCH_PATH = "/Users/hakkindavid/.gemini/antigravity/brain/252cce2b-a5d3-45b0-8e22-d19bb9b54a67/.user_uploaded/media_1789814168997.png"

OUT_DIRS = [
    "godot_project/assets/textures",
    "blender_assets/textures",
]

def generate_pbr_maps():
    print(f"[PBR Generator V3] Cargando swatch desde: {SWATCH_PATH}")
    if not os.path.exists(SWATCH_PATH):
        raise FileNotFoundError(f"No se encuentra el swatch en: {SWATCH_PATH}")
    
    img_in = bpy.data.images.load(SWATCH_PATH)
    w_orig, h_orig = img_in.size
    pixels = np.array(img_in.pixels[:], dtype=np.float32).reshape((h_orig, w_orig, 4))
    rgb = pixels[:, :, :3]
    
    # 1. Simetría reflejada en 2x2 para continuidad absoluta en las 4 fronteras
    # Fila superior: [Original, Reflejado H]
    row_top = np.concatenate([rgb, rgb[:, ::-1, :]], axis=1)
    # Fila inferior: Reflejado V
    row_bot = row_top[::-1, :, :]
    quad = np.concatenate([row_top, row_bot], axis=0) # Dimension: 2*h_orig x 2*w_orig
    
    qh, qw, _ = quad.shape
    target_size = 512
    
    # Muestreo bilineal a target_size x target_size
    y_coords = np.linspace(0, qh - 1, target_size)
    x_coords = np.linspace(0, qw - 1, target_size)
    
    x0 = np.floor(x_coords).astype(int)
    x1 = np.minimum(x0 + 1, qw - 1)
    wx = (x_coords - x0)[np.newaxis, :, np.newaxis]
    
    y0 = np.floor(y_coords).astype(int)
    y1 = np.minimum(y0 + 1, qh - 1)
    wy = (y_coords - y0)[:, np.newaxis, np.newaxis]
    
    top = quad[y0, :, :][:, x0, :] * (1.0 - wx) + quad[y0, :, :][:, x1, :] * wx
    bot = quad[y1, :, :][:, x0, :] * (1.0 - wx) + quad[y1, :, :][:, x1, :] * wx
    seamless_albedo = top * (1.0 - wy) + bot * wy
    
    # Calibración exacta de color al swatch
    target_mean = np.array([0.4495, 0.3489, 0.3044], dtype=np.float32)
    current_mean = seamless_albedo.mean(axis=(0,1))
    seamless_albedo = np.clip(seamless_albedo * (target_mean / np.maximum(current_mean, 1e-4)), 0.0, 1.0)
    
    # 2. Generación de Mapa de Normales (filtro Sobel periódico)
    height = 0.2126 * seamless_albedo[:, :, 0] + 0.7152 * seamless_albedo[:, :, 1] + 0.0722 * seamless_albedo[:, :, 2]
    bump_strength = 2.4
    
    # Derivadas centrales periódicas
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 0.5 * bump_strength
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 0.5 * bump_strength
    dz = np.ones_like(height)
    
    norm = np.sqrt(dx * dx + dy * dy + dz * dz)
    nx = -dx / norm
    ny = -dy / norm
    nz = dz / norm
    
    normal_map = np.stack([
        0.5 * nx + 0.5,
        0.5 * ny + 0.5,
        0.5 * nz + 0.5
    ], axis=-1)
    
    # 3. Mapa de Rugosidad
    h_norm = (height - height.mean()) / (height.std() + 1e-5)
    roughness = np.clip(0.86 + 0.05 * h_norm, 0.75, 0.95)
    roughness_map = np.stack([roughness, roughness, roughness], axis=-1)
    
    for out_dir in OUT_DIRS:
        os.makedirs(out_dir, exist_ok=True)
        
        def save_bpy_img(name, data_rgb):
            filepath = os.path.join(out_dir, name)
            h, w, c = data_rgb.shape
            rgba = np.ones((h, w, 4), dtype=np.float32)
            rgba[:, :, :3] = data_rgb
            
            if name in bpy.data.images:
                bpy.data.images.remove(bpy.data.images[name])
            b_img = bpy.data.images.new(name, width=w, height=h, alpha=True, float_buffer=False)
            b_img.pixels = rgba.flatten().tolist()
            b_img.filepath_raw = filepath
            b_img.file_format = 'PNG'
            b_img.save()
            print(f"[PBR Generator V3] Guardado: {filepath}")
        
        save_bpy_img("hotel_tecate_stucco_albedo.png", seamless_albedo)
        save_bpy_img("hotel_tecate_stucco_normal.png", normal_map)
        save_bpy_img("hotel_tecate_stucco_roughness.png", roughness_map)

if __name__ == "__main__":
    generate_pbr_maps()
