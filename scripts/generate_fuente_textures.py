"""
Generador de Texturas PBR Procedurales Dedicadas para la Fuente del Parque Hidalgo (2009)
Genera mapas PNG profesionales para:
1. Azulejos Talavera mexicanos (Albedo, Normal, Roughness)
2. Cantera pétrea para cascada, mochetas y copa (Albedo, Normal, Roughness)
3. Estuco ocre municipal con buña terracota (Albedo, Normal, Roughness)
4. Albardilla de cotto terracota mate para banca (Albedo, Normal, Roughness)
5. Mosaico vítreo turquesa para fondo de estanque (Albedo, Normal)
6. Agua translúcida con perturbación de ondas (Albedo RGBA, Normal)
"""

import bpy
import numpy as np
import os

def save_blender_image(name, np_array, filepath):
    h, w, c = np_array.shape
    # Inversión vertical para coordenadas UV estándar
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

def generate_normal_from_height(h_map, scale=0.04):
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

def generate_talavera_textures(w=1024, h=1024):
    print(">> Generando texturas de Azulejos Talavera Mexicanos...")
    np.random.seed(101)
    grid_n = 4 # 4x4 azulejos en la textura repetible
    tile_w = w // grid_n
    tile_h = h // grid_n

    albedo = np.zeros((h, w, 4), dtype=np.float32)
    roughness = np.zeros((h, w, 4), dtype=np.float32)
    height_map = np.zeros((h, w), dtype=np.float32)

    # Colores Talavera históricos
    c_azul = np.array([0.07, 0.16, 0.38])   # Azul cobalto profundo artesanal
    c_oro  = np.array([0.78, 0.52, 0.16])   # Ocre dorado / terracota quemado
    c_crema = np.array([0.90, 0.86, 0.76])  # Blanco hueso esmalte
    c_mortero = np.array([0.38, 0.36, 0.34])# Lechada de junta oscura

    mortar_border = int(tile_w * 0.05)

    for i in range(grid_n):
        for j in range(grid_n):
            y0 = i * tile_h
            y1 = (i + 1) * tile_h
            x0 = j * tile_w
            x1 = (j + 1) * tile_w

            is_azul = ((i + j) % 2 == 0)
            base_col = c_azul if is_azul else c_oro
            # Variación tonal sutil por azulejo artesanal
            base_col = base_col * (0.92 + 0.16 * np.random.rand(3))

            ty, tx = np.meshgrid(np.linspace(0, 1, tile_h), np.linspace(0, 1, tile_w), indexing='ij')
            # Distancia a los bordes de la celda
            d_edge = np.minimum(np.minimum(tx, 1.0 - tx), np.minimum(ty, 1.0 - ty))
            m_border = np.clip(d_edge / (mortar_border / tile_w), 0.0, 1.0)

            # Abombado / pillowing del azulejo vidriado artesanal
            pillow = np.sin(np.pi * tx) * np.sin(np.pi * ty)
            h_tile = (pillow ** 0.35) * m_border
            height_map[y0:y1, x0:x1] = h_tile

            # Ruido cerámico vidriado
            noise = (np.random.rand(tile_h, tile_w, 1) - 0.5) * 0.04
            tile_rgb = base_col.reshape(1, 1, 3) + noise

            # Motivo floral/geométrico ornamental sutil al centro de cada azulejo Talavera
            dist_c = np.sqrt((tx - 0.5)**2 + (ty - 0.5)**2)
            # Florón central
            flor_mask = (dist_c < 0.22) * np.clip(np.cos(dist_c * np.pi * 4.5), 0.0, 1.0)
            flor_color = c_crema if is_azul else c_azul
            tile_rgb = tile_rgb * (1.0 - flor_mask[:, :, None] * 0.55) + flor_color.reshape(1, 1, 3) * (flor_mask[:, :, None] * 0.55)

            # Combinar con lechada de mortero
            for c in range(3):
                albedo[y0:y1, x0:x1, c] = tile_rgb[:, :, c] * m_border + c_mortero[c] * (1.0 - m_border)

            # Roughness: azulejo muy vidriado brillante (0.16), lechada mate rugosa (0.85)
            r_val = 0.16 * m_border + 0.85 * (1.0 - m_border)
            roughness[y0:y1, x0:x1, 0] = r_val
            roughness[y0:y1, x0:x1, 1] = r_val
            roughness[y0:y1, x0:x1, 2] = r_val

    albedo[:, :, 3] = 1.0
    roughness[:, :, 3] = 1.0
    albedo = np.clip(albedo, 0.0, 1.0)
    roughness = np.clip(roughness, 0.0, 1.0)

    normal = generate_normal_from_height(height_map, scale=0.035)

    save_blender_image("fuente_talavera_albedo", albedo, "godot_project/assets/textures/fuente_talavera_albedo.png")
    save_blender_image("fuente_talavera_normal", normal, "godot_project/assets/textures/fuente_talavera_normal.png")
    save_blender_image("fuente_talavera_roughness", roughness, "godot_project/assets/textures/fuente_talavera_roughness.png")

def generate_cantera_textures(w=1024, h=1024):
    print(">> Generando texturas de Cantera pétrea para cascada...")
    np.random.seed(202)
    # Base pétrea beige perla / gris cantera colonial
    c_cantera = np.array([0.24, 0.12, 0.045, 1.0])
    
    # Ruido multifractal simulado
    x = np.linspace(0, 8, w)
    y = np.linspace(0, 8, h)
    gx, gy = np.meshgrid(x, y)
    
    noise_grain = np.random.rand(h, w) * 0.12 - 0.06
    veins = 0.05 * np.sin(gx * 2.0 + gy * 3.0 + np.random.rand(h, w) * 0.5)
    patina = 0.08 * np.sin(gx * 0.5) * np.cos(gy * 0.7) # Manchas suaves de humedad
    
    h_map = (noise_grain + veins + patina) * 0.5 + 0.5
    normal = generate_normal_from_height(h_map, scale=0.02)
    
    albedo = np.zeros((h, w, 4), dtype=np.float32)
    for c in range(3):
        albedo[:, :, c] = c_cantera[c] + noise_grain * 0.8 + veins * 0.5 - patina * 0.6
    albedo[:, :, 3] = 1.0
    albedo = np.clip(albedo, 0.0, 1.0)
    
    roughness = np.zeros((h, w, 4), dtype=np.float32)
    r_val = 0.78 + noise_grain * 0.3
    for c in range(3):
        roughness[:, :, c] = r_val
    roughness[:, :, 3] = 1.0
    roughness = np.clip(roughness, 0.0, 1.0)
    
    save_blender_image("fuente_cantera_albedo", albedo, "godot_project/assets/textures/fuente_cantera_albedo.png")
    save_blender_image("fuente_cantera_normal", normal, "godot_project/assets/textures/fuente_cantera_normal.png")
    save_blender_image("fuente_cantera_roughness", roughness, "godot_project/assets/textures/fuente_cantera_roughness.png")

def generate_murete_textures(w=1024, h=512):
    print(">> Generando texturas de Murete exterior (estuco ocre con franja terracota)...")
    np.random.seed(303)
    # Color estuco ocre arena de cal
    c_ocre = np.array([0.78, 0.69, 0.51])
    # Color franja buña terracota
    c_buña = np.array([0.58, 0.28, 0.18])

    y = np.linspace(0, 1, h)
    x = np.linspace(0, 4, w)
    gx, gy = np.meshgrid(x, y)

    noise_stucco = (np.random.rand(h, w) - 0.5) * 0.10

    # Franja horizontal centrada en V = 0.68 a 0.76 (donde está la buña)
    buña_mask = np.clip(1.0 - (np.abs(gy - 0.72) / 0.06)**4, 0.0, 1.0)

    albedo = np.zeros((h, w, 4), dtype=np.float32)
    for c in range(3):
        col_mix = c_ocre[c] * (1.0 - buña_mask) + c_buña[c] * buña_mask
        albedo[:, :, c] = col_mix + noise_stucco
    albedo[:, :, 3] = 1.0
    albedo = np.clip(albedo, 0.0, 1.0)

    h_map = noise_stucco * 0.7 - buña_mask * 0.4
    normal = generate_normal_from_height(h_map, scale=0.025)

    roughness = np.zeros((h, w, 4), dtype=np.float32)
    roughness[:, :, :3] = 0.85
    roughness[:, :, 3] = 1.0

    save_blender_image("fuente_murete_albedo", albedo, "godot_project/assets/textures/fuente_murete_albedo.png")
    save_blender_image("fuente_murete_normal", normal, "godot_project/assets/textures/fuente_murete_normal.png")
    save_blender_image("fuente_murete_roughness", roughness, "godot_project/assets/textures/fuente_murete_roughness.png")

def generate_banca_textures(w=512, h=512):
    print(">> Generando texturas de Albardilla de banca (cotto terracota mate)...")
    np.random.seed(404)
    # Terracota cocida mate
    c_cotto = np.array([0.54, 0.32, 0.23])
    noise = (np.random.rand(h, w) - 0.5) * 0.08

    albedo = np.zeros((h, w, 4), dtype=np.float32)
    for c in range(3):
        albedo[:, :, c] = c_cotto[c] + noise
    albedo[:, :, 3] = 1.0
    albedo = np.clip(albedo, 0.0, 1.0)

    h_map = noise * 0.8
    normal = generate_normal_from_height(h_map, scale=0.015)

    roughness = np.zeros((h, w, 4), dtype=np.float32)
    roughness[:, :, :3] = 0.82 # Muy mate, mineral
    roughness[:, :, 3] = 1.0

    save_blender_image("fuente_banca_albedo", albedo, "godot_project/assets/textures/fuente_banca_albedo.png")
    save_blender_image("fuente_banca_normal", normal, "godot_project/assets/textures/fuente_banca_normal.png")
    save_blender_image("fuente_banca_roughness", roughness, "godot_project/assets/textures/fuente_banca_roughness.png")

def generate_mosaico_textures(w=512, h=512):
    print(">> Generando texturas de Mosaico de fondo sumergido...")
    np.random.seed(505)
    grid_n = 16 # Mosaico veneciano menudo
    tile_w = w // grid_n
    tile_h = h // grid_n

    albedo = np.zeros((h, w, 4), dtype=np.float32)
    c_turquesa = np.array([0.10, 0.42, 0.54])
    c_junta = np.array([0.18, 0.28, 0.32])

    for i in range(grid_n):
        for j in range(grid_n):
            y0, y1 = i * tile_h, (i + 1) * tile_h
            x0, x1 = j * tile_w, (j + 1) * tile_w
            var = (np.random.rand(3) - 0.5) * 0.12
            col = c_turquesa + var

            ty, tx = np.meshgrid(np.linspace(0, 1, tile_h), np.linspace(0, 1, tile_w), indexing='ij')
            d_edge = np.minimum(np.minimum(tx, 1.0 - tx), np.minimum(ty, 1.0 - ty))
            m_border = np.clip(d_edge / 0.08, 0.0, 1.0)

            for c in range(3):
                albedo[y0:y1, x0:x1, c] = col[c] * m_border + c_junta[c] * (1.0 - m_border)

    albedo[:, :, 3] = 1.0
    albedo = np.clip(albedo, 0.0, 1.0)
    save_blender_image("fuente_mosaico_albedo", albedo, "godot_project/assets/textures/fuente_mosaico_albedo.png")

def generate_agua_textures(w=512, h=512):
    print(">> Generando texturas de Agua translúcida con ondas...")
    x = np.linspace(0, 12, w)
    y = np.linspace(0, 12, h)
    gx, gy = np.meshgrid(x, y)

    # Ondas superficiales sinusoidales
    w1 = np.sin(gx * 1.5 + gy * 1.2)
    w2 = np.cos(gx * 2.2 - gy * 1.8)
    waves = (w1 + w2) * 0.5

    h_map = waves * 0.5 + 0.5
    normal = generate_normal_from_height(h_map, scale=0.03)

    albedo = np.zeros((h, w, 4), dtype=np.float32)
    # Tinte aguamarina
    albedo[:, :, 0] = 0.20 + waves * 0.03
    albedo[:, :, 1] = 0.55 + waves * 0.04
    albedo[:, :, 2] = 0.68 + waves * 0.05
    # Alpha de transparencia: 0.60 para permitir ver el fondo y refracción
    albedo[:, :, 3] = 0.62
    albedo = np.clip(albedo, 0.0, 1.0)

    save_blender_image("fuente_agua_albedo", albedo, "godot_project/assets/textures/fuente_agua_albedo.png")
    save_blender_image("fuente_agua_normal", normal, "godot_project/assets/textures/fuente_agua_normal.png")

def main():
    generate_talavera_textures()
    generate_cantera_textures()
    generate_murete_textures()
    generate_banca_textures()
    generate_mosaico_textures()
    generate_agua_textures()
    print(">>> TODAS LAS TEXTURAS PBR DE LA FUENTE GENERADAS EXITOSAMENTE.")

if __name__ == "__main__":
    main()
