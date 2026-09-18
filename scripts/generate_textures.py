"""
Generador de Texturas PBR Procedurales para el Kiosco de Tecate
- Mampostería de Laja Irregular de Tecate (Albedo, Normal, Roughness)
- Cantera Beige de Piso y Escalones (Albedo, Normal)
"""

import bpy
import numpy as np
import math

def generate_laja_textures(width=1024, height=1024):
    print("Generando texturas de mampostería de laja...")
    np.random.seed(42)
    
    # 1. Puntos de Voronoi periódicos (envolventes) para piedras irregulares
    n_points = 55
    # Coordenadas en [0, 1]
    pts = np.random.rand(n_points, 2)
    
    # Malla de coordenadas
    x = np.linspace(0, 1, width, endpoint=False)
    y = np.linspace(0, 1, height, endpoint=False)
    grid_x, grid_y = np.meshgrid(x, y)
    
    # Paleta de piedras de Tecate (laja ocre, cantera dorada, arena, tostado, gris cálido)
    stone_colors = [
        [0.68, 0.54, 0.36], # Ocre dorado
        [0.72, 0.58, 0.40], # Arena cálida
        [0.60, 0.46, 0.32], # Pardo tostado
        [0.65, 0.52, 0.38], # Cantera dorada
        [0.56, 0.44, 0.33], # Tierra marrón
        [0.62, 0.56, 0.48], # Cantera grisáceo
        [0.70, 0.55, 0.37], # Ocre claro
    ]
    stone_col_array = np.array([stone_colors[np.random.randint(len(stone_colors))] for _ in range(n_points)])
    
    # Búsqueda de los 2 puntos más cercanos con condiciones periódicas
    min_dist1 = np.full((height, width), 999.0, dtype=np.float32)
    min_dist2 = np.full((height, width), 999.0, dtype=np.float32)
    min_idx = np.zeros((height, width), dtype=np.int32)
    
    # Evaluar vecinos periódicos en 3x3 celdas
    for ox in [-1, 0, 1]:
        for oy in [-1, 0, 1]:
            for p_idx in range(n_points):
                px = pts[p_idx, 0] + ox
                py = pts[p_idx, 1] + oy
                dx = grid_x - px
                dy = grid_y - py
                # Perturbación sutil para bordes de piedra orgánicos (no rectilíneos)
                d = np.sqrt(dx*dx + dy*dy) + 0.012 * np.sin(dx * 40.0) * np.cos(dy * 40.0)
                
                # Actualizar d1 y d2
                mask1 = d < min_dist1
                min_dist2 = np.where(mask1, min_dist1, np.minimum(min_dist2, d))
                min_dist1 = np.where(mask1, d, min_dist1)
                min_idx = np.where(mask1, p_idx, min_idx)
    
    # Diferencia entre d2 y d1 define las juntas de mortero
    edge_dist = min_dist2 - min_dist1
    mortar_width = 0.014
    
    # Máscara de mortero suave
    mortar_factor = np.clip(edge_dist / mortar_width, 0.0, 1.0)
    # Forma convexa de la piedra (pillowing)
    stone_height = np.clip(1.0 - (min_dist1 * 6.5)**2, 0.1, 1.0) * mortar_factor
    
    # Ruido microscópico de cantería
    noise = (np.random.rand(height, width) - 0.5) * 0.08
    
    # Color de mortero (cemento gris claro)
    mortar_color = np.array([0.76, 0.74, 0.70])
    
    # Asignar color de cada piedra
    albedo = np.zeros((height, width, 4), dtype=np.float32)
    for c in range(3):
        stone_c = stone_col_array[min_idx, c] + noise
        albedo[:, :, c] = mortar_color[c] * (1.0 - mortar_factor) + stone_c * mortar_factor
    albedo[:, :, 3] = 1.0
    albedo = np.clip(albedo, 0.0, 1.0)
    
    # Normal Map a partir del gradiente del mapa de altura
    h_map = stone_height + noise * 0.3
    dh_dy, dh_dx = np.gradient(h_map, 1.0 / height, 1.0 / width)
    scale = 0.04
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
    
    # Roughness: mortero más rugoso (0.92), piedra (0.84)
    roughness = np.zeros((height, width, 4), dtype=np.float32)
    r_val = 0.92 * (1.0 - mortar_factor) + (0.84 + noise * 0.5) * mortar_factor
    roughness[:, :, 0] = r_val
    roughness[:, :, 1] = r_val
    roughness[:, :, 2] = r_val
    roughness[:, :, 3] = 1.0
    roughness = np.clip(roughness, 0.0, 1.0)
    
    # Guardar mediante Blender API
    save_blender_image("kiosko_laja_albedo", albedo, "godot_project/assets/textures/kiosko_laja_albedo.png")
    save_blender_image("kiosko_laja_normal", normal, "godot_project/assets/textures/kiosko_laja_normal.png")
    save_blender_image("kiosko_laja_roughness", roughness, "godot_project/assets/textures/kiosko_laja_roughness.png")
    print("Texturas de laja generadas exitosamente.")

def generate_cantera_textures(width=512, height=512):
    print("Generando texturas de cantera de piso...")
    # Rejilla regular de 4x4 baldosas de cantera con biseles
    tiles = 4
    x = np.linspace(0, tiles, width, endpoint=False)
    y = np.linspace(0, tiles, height, endpoint=False)
    gx, gy = np.meshgrid(x, y)
    
    fx = gx % 1.0
    fy = gy % 1.0
    
    # Distancia a la junta de la baldosa
    dist_x = np.minimum(fx, 1.0 - fx)
    dist_y = np.minimum(fy, 1.0 - fy)
    dist_edge = np.minimum(dist_x, dist_y)
    
    joint_width = 0.035
    mortar_factor = np.clip(dist_edge / joint_width, 0.0, 1.0)
    
    # Variación sutil por baldosa
    tile_id = (np.floor(gx) + np.floor(gy) * tiles).astype(int)
    np.random.seed(99)
    tile_shades = 0.76 + (np.random.rand(tiles * tiles) - 0.5) * 0.06
    
    noise = (np.random.rand(height, width) - 0.5) * 0.04
    base_shade = tile_shades[tile_id % len(tile_shades)] + noise
    
    albedo = np.zeros((height, width, 4), dtype=np.float32)
    # Tono cantera beige clara
    albedo[:, :, 0] = (base_shade * 1.00) * mortar_factor + 0.65 * (1.0 - mortar_factor)
    albedo[:, :, 1] = (base_shade * 0.97) * mortar_factor + 0.64 * (1.0 - mortar_factor)
    albedo[:, :, 2] = (base_shade * 0.90) * mortar_factor + 0.61 * (1.0 - mortar_factor)
    albedo[:, :, 3] = 1.0
    albedo = np.clip(albedo, 0.0, 1.0)
    
    # Normal map suave
    h_map = mortar_factor * 0.8 + noise * 0.2
    dh_dy, dh_dx = np.gradient(h_map, 1.0 / height, 1.0 / width)
    scale = 0.02
    nx = -dh_dx * scale
    ny = -dh_dy * scale
    nz = np.ones_like(nx)
    norm = np.sqrt(nx*nx + ny*ny + nz*nz)
    normal = np.zeros((height, width, 4), dtype=np.float32)
    normal[:, :, 0] = (nx / norm) * 0.5 + 0.5
    normal[:, :, 1] = (ny / norm) * 0.5 + 0.5
    normal[:, :, 2] = (nz / norm) * 0.5 + 0.5
    normal[:, :, 3] = 1.0
    
    save_blender_image("kiosko_cantera_albedo", albedo, "godot_project/assets/textures/kiosko_cantera_albedo.png")
    save_blender_image("kiosko_cantera_normal", normal, "godot_project/assets/textures/kiosko_cantera_normal.png")
    print("Texturas de cantera generadas exitosamente.")

def save_blender_image(name, np_array, filepath):
    h, w, c = np_array.shape
    # Blender espera filas desde abajo hacia arriba (Y invertido)
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

def main():
    generate_laja_textures(1024, 1024)
    generate_cantera_textures(512, 512)

if __name__ == "__main__":
    main()
