"""
Generador de Textura PBR de Teja Colonial Curva (Spanish Barrel Tile)
Para la cubierta cónica del Kiosco de Tecate
"""

import bpy
import numpy as np

def generate_tile_texture(width=512, height=512):
    print("Generando textura de teja colonial española...")
    
    # Coordenadas UV [0, 1]
    u = np.linspace(0, 1, width, endpoint=False)
    v = np.linspace(0, 1, height, endpoint=False)
    gu, gv = np.meshgrid(u, v)
    
    # Perfil transversal de teja curva (canal y cobija):
    # u = 0.0 a 0.5: cobija semicircular convexa saliente
    # u = 0.5 a 1.0: canal cóncavo
    # Usamos una onda sinusoidal modificada para tejas árabes reales
    h_profile = 0.5 + 0.45 * np.sin(2.0 * np.pi * gu)
    
    # Perfil longitudinal (solape en V):
    # La teja tiene una ligera pendiente y un escalón de solape en v = 0.92
    v_slope = 0.15 * gv
    v_step = np.where(gv > 0.92, 0.25 * (1.0 - (gv - 0.92) / 0.08), 0.0)
    
    # Altura total
    height_map = h_profile + v_slope - v_step
    
    # Ruido sutil de arcilla cocida
    np.random.seed(77)
    noise = (np.random.rand(height, width) - 0.5) * 0.05
    height_map += noise
    
    # Normal Map mediante gradientes
    dh_dy, dh_dx = np.gradient(height_map, 1.0 / height, 1.0 / width)
    scale = 0.08
    nx = -dh_dx * scale
    ny = -dh_dy * scale
    nz = np.ones_like(nx)
    norm = np.sqrt(nx*nx + ny*ny + nz*nz)
    nx /= norm
    ny /= norm
    nz /= norm
    
    normal = np.zeros((height, width, 4), dtype=np.float32)
    normal[:, :, 0] = nx * 0.5 + 0.5
    normal[:, :, 1] = ny * 0.5 + 0.5
    normal[:, :, 2] = nz * 0.5 + 0.5
    normal[:, :, 3] = 1.0
    
    # Albedo: Terracota artesanal cocido con variaciones de tono
    # Las cobijas son más luminosas y expuestas, los canales acumulan sombra/tierra
    clay_base = np.array([0.55, 0.20, 0.11]) # Rojo teja terracota profundo
    clay_highlight = np.array([0.62, 0.25, 0.14]) # Cresta soleada
    clay_shadow = np.array([0.42, 0.15, 0.08]) # Canal y junta oscura
    
    factor = np.clip(h_profile + noise * 2.0, 0.0, 1.0)
    
    albedo = np.zeros((height, width, 4), dtype=np.float32)
    for c in range(3):
        col_c = np.where(factor > 0.5,
                         clay_base[c] + (clay_highlight[c] - clay_base[c]) * ((factor - 0.5) * 2.0),
                         clay_shadow[c] + (clay_base[c] - clay_shadow[c]) * (factor * 2.0))
        albedo[:, :, c] = col_c
    albedo[:, :, 3] = 1.0
    albedo = np.clip(albedo, 0.0, 1.0)
    
    # Roughness: arcilla cocida mate (0.75 a 0.85)
    roughness = np.zeros((height, width, 4), dtype=np.float32)
    r_val = 0.78 + noise * 0.5
    roughness[:, :, 0] = r_val
    roughness[:, :, 1] = r_val
    roughness[:, :, 2] = r_val
    roughness[:, :, 3] = 1.0
    roughness = np.clip(roughness, 0.0, 1.0)
    
    # Guardar imágenes
    save_blender_image("kiosko_teja_albedo", albedo, "godot_project/assets/textures/kiosko_teja_albedo.png")
    save_blender_image("kiosko_teja_normal", normal, "godot_project/assets/textures/kiosko_teja_normal.png")
    save_blender_image("kiosko_teja_roughness", roughness, "godot_project/assets/textures/kiosko_teja_roughness.png")
    print("Texturas de teja generadas exitosamente.")

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
    img.save()
    print(f"-> Guardada imagen: {filepath}")

if __name__ == "__main__":
    generate_tile_texture()
