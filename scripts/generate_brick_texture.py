"""
Generador de Texturas PBR para Ladrillo Artesanal Siglo XIX
- kiosko_ladrillo_albedo.png
- kiosko_ladrillo_normal.png
- kiosko_ladrillo_roughness.png
"""
import bpy
import numpy as np
import os

def generate_19th_century_brick_textures(width=1024, height=1024):
    print("Generando texturas de ladrillo artesanal siglo XIX...")
    np.random.seed(1890)
    
    # 1. Configuración de hiladas decimonónicas
    # ~10 hiladas gruesas en 1024 px de alto
    num_rows = 10
    row_h = height / num_rows
    
    # Cada ladrillo mide aprox 2.4 veces su alto
    bricks_per_row = 4
    brick_w = width / bricks_per_row
    
    mortar_thickness = 14.0 # pixels de mortero grueso (~1.5 - 2 cm)
    
    # Grid de coordenadas
    y_indices, x_indices = np.indices((height, width), dtype=np.float32)
    
    # Coordenadas de fila
    row_idx = np.floor(y_indices / row_h).astype(np.int32)
    y_in_row = y_indices - row_idx * row_h
    
    # Desplazamiento de hilada (running bond con pequeña imperfección)
    x_offset = (row_idx % 2) * (brick_w * 0.5)
    x_shifted = (x_indices + x_offset) % width
    
    col_idx = np.floor(x_shifted / brick_w).astype(np.int32)
    x_in_brick = x_shifted - col_idx * brick_w
    
    # Identificador único de cada ladrillo para variación individual
    brick_id = row_idx * 17 + col_idx * 31
    
    # Distancia a los bordes del ladrillo
    dist_left = x_in_brick
    dist_right = brick_w - x_in_brick
    dist_bottom = y_in_row
    dist_top = row_h - y_in_row
    
    # Añadir ondulación/imperfección artesanal a las juntas
    noise_x = 4.0 * np.sin(y_indices * 0.05) + 2.0 * np.cos(y_indices * 0.12)
    noise_y = 3.0 * np.cos(x_indices * 0.05) + 1.5 * np.sin(x_indices * 0.15)
    
    dx_edge = np.minimum(dist_left + noise_x, dist_right - noise_x)
    dy_edge = np.minimum(dist_bottom + noise_y, dist_top - noise_y)
    
    edge_dist = np.minimum(dx_edge, dy_edge)
    
    # Máscara de mortero vs ladrillo
    mortar_mask = np.clip(1.0 - (edge_dist - mortar_thickness * 0.5) / (mortar_thickness * 0.5), 0.0, 1.0)
    # Suavizado de bordes redondeados artesanales
    brick_bevel = np.clip(edge_dist / 22.0, 0.0, 1.0)
    brick_bevel = np.sin(brick_bevel * np.pi * 0.5)
    
    # Paleta de arcilla cocida decimonónica (Baja California / estilo siglo XIX)
    # Ladrillos quemados en horno tradicional de leña con manchas de fuego y tonos ocres/rojizos
    base_tones = [
        [0.48, 0.18, 0.10], # Terracota rojizo intenso
        [0.42, 0.15, 0.08], # Pardo terracota quemado
        [0.52, 0.22, 0.12], # Arcilla cocida clara
        [0.36, 0.13, 0.07], # Ladrillo cocido oscuro (clinker)
        [0.45, 0.19, 0.11], # Terracota estándar
        [0.32, 0.11, 0.06], # Ahumado de carbón
    ]
    
    # Generar tabla de colores por ID de ladrillo
    unique_ids = np.unique(brick_id)
    id_to_color = {}
    for uid in unique_ids:
        c_idx = np.random.randint(len(base_tones))
        jitter = (np.random.rand(3) - 0.5) * 0.08
        col = np.clip(np.array(base_tones[c_idx]) + jitter, 0.05, 0.85)
        id_to_color[uid] = col
        
    brick_albedo = np.zeros((height, width, 3), dtype=np.float32)
    for uid in unique_ids:
        mask = (brick_id == uid)
        brick_albedo[mask] = id_to_color[uid]
        
    # Microtextura de poro y grano del barro artesanal
    clay_grain = np.random.normal(0.0, 0.04, (height, width, 1)).astype(np.float32)
    brick_albedo = np.clip(brick_albedo + clay_grain, 0.0, 1.0)
    
    # Color del mortero rústico de cal y arena de río
    mortar_grain = np.random.normal(0.0, 0.03, (height, width, 1)).astype(np.float32)
    mortar_col = np.array([0.72, 0.69, 0.63], dtype=np.float32) + mortar_grain # Gris cal cálido
    
    # Mezcla final de albedo
    m_factor = mortar_mask[..., np.newaxis]
    albedo = brick_albedo * (1.0 - m_factor) + mortar_col * m_factor
    
    # Altura (Height Map) para mapa de normales
    height_map = brick_bevel * (1.0 - mortar_mask * 0.85)
    height_map += np.squeeze(clay_grain) * 0.15 * (1.0 - mortar_mask)
    height_map += np.squeeze(mortar_grain) * 0.10 * mortar_mask
    
    # Derivadas para Normal Map (Sobel filter)
    grad_y, grad_x = np.gradient(height_map)
    strength = 6.0
    norm_x = -grad_x * strength
    norm_y = -grad_y * strength
    norm_z = np.ones_like(height_map)
    
    len_norm = np.sqrt(norm_x**2 + norm_y**2 + norm_z**2)
    norm_x /= len_norm
    norm_y /= len_norm
    norm_z /= len_norm
    
    normal_rgb = np.zeros((height, width, 3), dtype=np.float32)
    normal_rgb[..., 0] = norm_x * 0.5 + 0.5
    normal_rgb[..., 1] = norm_y * 0.5 + 0.5
    normal_rgb[..., 2] = norm_z * 0.5 + 0.5
    
    # Rugosidad (Roughness)
    roughness = 0.82 * (1.0 - mortar_mask) + 0.96 * mortar_mask
    roughness += np.squeeze(clay_grain) * 0.4
    roughness = np.clip(roughness, 0.5, 1.0)
    
    # Guardar imágenes mediante Blender
    out_dir = "godot_project/assets/textures"
    os.makedirs(out_dir, exist_ok=True)
    
    def save_img(data, name, is_rgb=True):
        filepath = os.path.join(out_dir, name)
        if name in bpy.data.images:
            bpy.data.images.remove(bpy.data.images[name])
        img = bpy.data.images.new(name, width=width, height=height, alpha=False)
        
        if is_rgb:
            rgba = np.ones((height, width, 4), dtype=np.float32)
            rgba[..., :3] = data
            img.pixels.foreach_set(rgba.ravel())
        else:
            rgba = np.ones((height, width, 4), dtype=np.float32)
            rgba[..., 0] = data
            rgba[..., 1] = data
            rgba[..., 2] = data
            img.pixels.foreach_set(rgba.ravel())
            
        img.filepath_raw = filepath
        img.file_format = "PNG"
        img.save()
        print(f"--> Guardado: {filepath}")
        
    save_img(albedo, "kiosko_ladrillo_albedo.png", is_rgb=True)
    save_img(normal_rgb, "kiosko_ladrillo_normal.png", is_rgb=True)
    save_img(roughness, "kiosko_ladrillo_roughness.png", is_rgb=False)
    print("Texturas de ladrillo artesanal siglo XIX generadas con éxito.")

if __name__ == "__main__":
    generate_19th_century_brick_textures()
