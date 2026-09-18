"""
Generador de Texturas PBR para Ladrillo Decimonónico Tradicional de Tecate
Fiel a la referencia fotográfica real (media_1789717720582.png):
- Tono arcilla marrón/terracota envejecido de horneado artesanal (sin tonos blanquecinos).
- Juntas de mortero oscuras y rehundidas en sombra (sin líneas claras).
- Textura porosa y tacto rústico.
"""
import bpy
import numpy as np
import os

def generate_tecate_brick_textures(width=1024, height=1024):
    print("Generando texturas de ladrillo artesanal de Tecate (fiel a referencia)...")
    np.random.seed(1890)
    
    # 1. Configuración de hiladas gruesas decimonónicas
    num_rows = 10
    row_h = height / num_rows
    bricks_per_row = 4
    brick_w = width / bricks_per_row
    
    mortar_thickness = 8.0 # Junta delgada rehundida en sombra
    
    y_indices, x_indices = np.indices((height, width), dtype=np.float32)
    row_idx = np.floor(y_indices / row_h).astype(np.int32)
    y_in_row = y_indices - row_idx * row_h
    
    x_offset = (row_idx % 2) * (brick_w * 0.5)
    x_shifted = (x_indices + x_offset) % width
    col_idx = np.floor(x_shifted / brick_w).astype(np.int32)
    x_in_brick = x_shifted - col_idx * brick_w
    
    brick_id = row_idx * 17 + col_idx * 31
    
    dist_left = x_in_brick
    dist_right = brick_w - x_in_brick
    dist_bottom = y_in_row
    dist_top = row_h - y_in_row
    
    # Bordes redondeados rústicos
    noise_x = 3.0 * np.sin(y_indices * 0.06) + 1.5 * np.cos(y_indices * 0.14)
    noise_y = 2.5 * np.cos(x_indices * 0.06) + 1.2 * np.sin(x_indices * 0.18)
    
    dx_edge = np.minimum(dist_left + noise_x, dist_right - noise_x)
    dy_edge = np.minimum(dist_bottom + noise_y, dist_top - noise_y)
    edge_dist = np.minimum(dx_edge, dy_edge)
    
    mortar_mask = np.clip(1.0 - (edge_dist - mortar_thickness * 0.5) / (mortar_thickness * 0.5), 0.0, 1.0)
    
    # Redondeado suave de aristas (almohadillado sutil artesanal)
    brick_bevel = np.clip(edge_dist / 26.0, 0.0, 1.0)
    brick_bevel = np.sin(brick_bevel * np.pi * 0.5)
    
    # Paleta EXACTA de media_1789717720582.png:
    # Arcilla cocida marrón terracota cálida envejecida (sin naranjas brillantes ni blancos)
    base_tones = [
        [0.35, 0.20, 0.13], # Marrón terracota tostado
        [0.39, 0.23, 0.15], # Barro cocido medio
        [0.32, 0.18, 0.11], # Arcilla oscura
        [0.37, 0.22, 0.14], # Terracota envejecido
        [0.29, 0.16, 0.10], # Sombra de cocción
        [0.34, 0.20, 0.13], # Arcilla neutra
    ]
    
    unique_ids = np.unique(brick_id)
    id_to_color = {}
    for uid in unique_ids:
        c_idx = np.random.randint(len(base_tones))
        jitter = (np.random.rand(3) - 0.5) * 0.04
        col = np.clip(np.array(base_tones[c_idx]) + jitter, 0.05, 0.65)
        id_to_color[uid] = col
        
    brick_albedo = np.zeros((height, width, 3), dtype=np.float32)
    for uid in unique_ids:
        mask = (brick_id == uid)
        brick_albedo[mask] = id_to_color[uid]
        
    # Micrograno de barro cocido
    clay_grain = np.random.normal(0.0, 0.025, (height, width, 1)).astype(np.float32)
    brick_albedo = np.clip(brick_albedo + clay_grain, 0.0, 1.0)
    
    # Mortero OSCURO de cemento envejecido y sombra profunda (sin blancos)
    mortar_col = np.array([0.20, 0.14, 0.11], dtype=np.float32) + np.random.normal(0.0, 0.02, (height, width, 1))
    
    # Mezcla de albedo
    m_factor = mortar_mask[..., np.newaxis]
    albedo = brick_albedo * (1.0 - m_factor) + mortar_col * m_factor
    
    # Normal Map con bisel suave y juntas rehundidas oscuras
    height_map = brick_bevel * (1.0 - mortar_mask * 0.8)
    height_map += np.squeeze(clay_grain) * 0.15
    
    grad_y, grad_x = np.gradient(height_map)
    strength = 5.0
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
    
    # Roughness: mate y rústico (0.84 a 0.96)
    roughness = 0.84 * (1.0 - mortar_mask) + 0.95 * mortar_mask
    roughness += np.squeeze(clay_grain) * 0.3
    roughness = np.clip(roughness, 0.70, 1.0)
    
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
    print("Texturas de ladrillo artesanal siglo XIX actualizadas con éxito.")

if __name__ == "__main__":
    generate_tecate_brick_textures()
