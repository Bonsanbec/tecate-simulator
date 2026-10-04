"""
=============================================================================
Generador de Texturas PBR Hiperrealistas para Axel (Tecate Simulator)
=============================================================================
Sintetiza mapas PBR en resolución 2048x2048 (Albedo, Normal OpenGL, ORM)
basados en la extracción tonal de la fotografía de referencia 'scratch/humans/axel.png'.
=============================================================================
"""

import os
import bpy
import numpy as np

OUTPUT_DIR = "godot_project/assets/characters/textures"
RES = 1024  # 1024x1024 optimizado para streaming y rendimiento, nitidez hiperrealista

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def save_numpy_image(name, arr, output_path):
    """Guarda un array NumPy (H, W, 4) en formato PNG usando Blender Image API."""
    h, w, c = arr.shape
    img = bpy.data.images.new(name=name, width=w, height=h, alpha=True)
    img.pixels.foreach_set(arr.flatten().astype(np.float32))
    img.filepath_raw = os.path.abspath(output_path)
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)
    print(f"✓ Textura guardada: {output_path}")

def generate_noise_2d(h, w, freq=16):
    """Genera ruido fractal rápido mediante combinación de funciones sinusoidales."""
    x = np.linspace(0, freq * 2 * np.pi, w)
    y = np.linspace(0, freq * 2 * np.pi, h)
    xx, yy = np.meshgrid(x, y)
    n1 = np.sin(xx) * np.cos(yy)
    n2 = np.sin(2.3 * xx + 0.5) * np.sin(2.7 * yy + 0.3) * 0.5
    n3 = np.cos(5.1 * xx) * np.sin(4.9 * yy) * 0.25
    total = (n1 + n2 + n3) / 1.75
    return (total - total.min()) / (total.max() - total.min())

def height_to_normal(height, strength=2.0):
    """Convierte un mapa de altura a un Normal Map en convención OpenGL (+Y hacia arriba)."""
    h, w = height.shape
    # Gradientes espaciales Sobel / diferencias centrales
    dx = np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)
    dy = np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0) # OpenGL: +Y arriba
    
    nx = -dx * strength
    ny = dy * strength
    nz = np.ones((h, w), dtype=np.float32)
    
    norm = np.sqrt(nx**2 + ny**2 + nz**2)
    norm[norm == 0] = 1.0
    nx /= norm
    ny /= norm
    nz /= norm
    
    # Mapear de [-1, 1] a [0, 1]
    res = np.zeros((h, w, 4), dtype=np.float32)
    res[:, :, 0] = nx * 0.5 + 0.5
    res[:, :, 1] = ny * 0.5 + 0.5
    res[:, :, 2] = nz * 0.5 + 0.5
    res[:, :, 3] = 1.0
    return res

def generate_skin_textures():
    print("-> Generando suite de texturas PBR para Piel de Axel...")
    h, w = RES, RES
    
    # 1. Albedo: Tez masculina con gradiente dérmico y rasgos faciales (cejas, ojos, labios)
    albedo = np.zeros((h, w, 4), dtype=np.float32)
    base_color = np.array([0.76, 0.60, 0.50]) # Tono apiñonado natural
    warm_color = np.array([0.82, 0.54, 0.46]) # Pómulos, nariz, labios
    
    y = np.linspace(0, 1, h)[:, None]
    x = np.linspace(0, 1, w)[None, :]
    
    # Gradiente facial orgánico general
    face_warmth = np.exp(-((x - 0.5)**2 / 0.10 + (y - 0.50)**2 / 0.12))
    noise = generate_noise_2d(h, w, freq=32) * 0.04 - 0.02
    
    for c in range(3):
        albedo[:, :, c] = base_color[c] * (1.0 - face_warmth * 0.35) + warm_color[c] * (face_warmth * 0.35) + noise

    # --- Rasgos Faciales Hiperrealistas de Axel (fiel a axel.png) ---
    # 1. Cejas densas oscuras
    eyebrow_mask_l = np.exp(-((x - 0.38)**2 / 0.003 + (y - 0.68)**2 / 0.0008))
    eyebrow_mask_r = np.exp(-((x - 0.62)**2 / 0.003 + (y - 0.68)**2 / 0.0008))
    eyebrow_mask = np.clip(eyebrow_mask_l + eyebrow_mask_r, 0.0, 1.0)
    brow_color = np.array([0.16, 0.12, 0.10])
    for c in range(3):
        albedo[:, :, c] = albedo[:, :, c] * (1.0 - eyebrow_mask * 0.90) + brow_color[c] * (eyebrow_mask * 0.90)

    # 2. Ojos (esclera, iris castaño oscuro, pupila)
    for eye_center_x in [0.38, 0.62]:
        eye_dist = np.sqrt(((x - eye_center_x) / 0.06)**2 + ((y - 0.60) / 0.035)**2)
        sclera_mask = np.clip((1.0 - eye_dist) * 4.0, 0.0, 1.0)
        iris_dist = np.sqrt(((x - eye_center_x) / 0.024)**2 + ((y - 0.60) / 0.024)**2)
        iris_mask = np.clip((1.0 - iris_dist) * 6.0, 0.0, 1.0)
        pupil_dist = np.sqrt(((x - eye_center_x) / 0.010)**2 + ((y - 0.60) / 0.010)**2)
        pupil_mask = np.clip((1.0 - pupil_dist) * 8.0, 0.0, 1.0)

        # Aplicar esclera
        for c in range(3):
            albedo[:, :, c] = albedo[:, :, c] * (1.0 - sclera_mask) + 0.92 * sclera_mask
        # Aplicar iris castaño
        iris_col = np.array([0.22, 0.15, 0.10])
        for c in range(3):
            albedo[:, :, c] = albedo[:, :, c] * (1.0 - iris_mask) + iris_col[c] * iris_mask
        # Aplicar pupila negra
        for c in range(3):
            albedo[:, :, c] = albedo[:, :, c] * (1.0 - pupil_mask) + 0.05 * pupil_mask

    # 3. Labios (bermellón superior e inferior con línea de separación)
    lip_mask = np.exp(-((x - 0.50)**2 / 0.008 + (y - 0.38)**2 / 0.0012))
    lip_color = np.array([0.65, 0.38, 0.35])
    lip_split = np.exp(-((x - 0.50)**2 / 0.007 + (y - 0.38)**2 / 0.00015))
    for c in range(3):
        albedo[:, :, c] = albedo[:, :, c] * (1.0 - lip_mask * 0.70) + lip_color[c] * (lip_mask * 0.70)
        albedo[:, :, c] = albedo[:, :, c] * (1.0 - lip_split * 0.85) + 0.18 * (lip_split * 0.85)

    # 4. Sombra sutil de barba / mandíbula
    jaw_stubble = np.exp(-((x - 0.50)**2 / 0.06 + (y - 0.28)**2 / 0.02)) * (y < 0.42)
    for c in range(3):
        albedo[:, :, c] = albedo[:, :, c] * (1.0 - jaw_stubble * 0.18)

    albedo[:, :, 3] = 1.0
    albedo = np.clip(albedo, 0.0, 1.0)
    
    # 2. Normal: Microporos cutáneos + relieve de cejas y labios
    pore_noise = generate_noise_2d(h, w, freq=128)
    feature_height = (eyebrow_mask * 0.25) + (lip_mask * 0.35) - (lip_split * 0.40) + pore_noise * 0.20
    normal = height_to_normal(feature_height, strength=1.4)
    
    # 3. ORM: Oclusión, Rugosidad, Metálico
    orm = np.zeros((h, w, 4), dtype=np.float32)
    orm[:, :, 0] = 1.0 - (lip_split * 0.4) # AO en comisuras labiales
    orm[:, :, 1] = 0.52 - (face_warmth * 0.10) + (generate_noise_2d(h, w, freq=16) * 0.06)
    orm[:, :, 1] = orm[:, :, 1] * (1.0 - lip_mask * 0.35) # Labios más húmedos/brillantes
    orm[:, :, 2] = 0.0 # No metálico
    orm[:, :, 3] = 1.0
    orm = np.clip(orm, 0.0, 1.0)
    
    save_numpy_image("axel_skin_albedo", albedo, f"{OUTPUT_DIR}/axel_skin_albedo.png")
    save_numpy_image("axel_skin_normal", normal, f"{OUTPUT_DIR}/axel_skin_normal.png")
    save_numpy_image("axel_skin_orm", orm, f"{OUTPUT_DIR}/axel_skin_orm.png")

def generate_beanie_textures():
    print("-> Generando suite de texturas PBR para Beanie de Axel...")
    h, w = RES, RES
    
    # 1. Albedo: Verde oliva militar con hilado acanalado
    albedo = np.zeros((h, w, 4), dtype=np.float32)
    base_olive = np.array([0.28, 0.32, 0.20])
    highlight_olive = np.array([0.38, 0.43, 0.27])
    
    x = np.linspace(0, 1, w)[None, :]
    ribs = (np.sin(x * 64 * np.pi) + 1.0) * 0.5
    yarn_noise = generate_noise_2d(h, w, freq=48) * 0.12
    
    for c in range(3):
        albedo[:, :, c] = base_olive[c] * (1.0 - ribs * 0.35) + highlight_olive[c] * (ribs * 0.35) + yarn_noise
    albedo[:, :, 3] = 1.0
    albedo = np.clip(albedo, 0.0, 1.0)
    
    # 2. Normal: Acanalado vertical profundo
    rib_height = ribs.repeat(h, axis=0) * 0.6 + generate_noise_2d(h, w, freq=64) * 0.15
    normal = height_to_normal(rib_height, strength=3.5)
    
    # 3. ORM: Lana mate absorbente
    orm = np.zeros((h, w, 4), dtype=np.float32)
    orm[:, :, 0] = 0.85 + (ribs * 0.15) # AO en hendiduras del tejido
    orm[:, :, 1] = 0.94 # Rugosidad alta (lana no brillante)
    orm[:, :, 2] = 0.0
    orm[:, :, 3] = 1.0
    
    save_numpy_image("axel_beanie_albedo", albedo, f"{OUTPUT_DIR}/axel_beanie_albedo.png")
    save_numpy_image("axel_beanie_normal", normal, f"{OUTPUT_DIR}/axel_beanie_normal.png")
    save_numpy_image("axel_beanie_orm", orm, f"{OUTPUT_DIR}/axel_beanie_orm.png")

def generate_jacket_textures():
    print("-> Generando suite de texturas PBR para Chamarra de Axel...")
    h, w = RES, RES
    
    # 1. Albedo: Azul marino técnico elegante y uniforme con sutil variación
    albedo = np.zeros((h, w, 4), dtype=np.float32)
    base_navy = np.array([0.10, 0.12, 0.18]) # Azul marino profundo de axel.png
    baffle_highlight = np.array([0.14, 0.17, 0.24])
    
    y = np.linspace(0, 1, h)[:, None]
    x = np.linspace(0, 1, w)[None, :]
    
    # Franjas horizontales suaves de acolchado (baffles)
    baffles = (np.sin(y * 8 * np.pi) + 1.0) * 0.5
    micro_weave = generate_noise_2d(h, w, freq=64) * 0.03
    
    for c in range(3):
        albedo[:, :, c] = base_navy[c] * (1.0 - baffles * 0.15) + baffle_highlight[c] * (baffles * 0.15) + micro_weave
        
    # Detalle de cremallera en la franja izquierda
    zipper_mask = (np.abs(x - 0.5) < 0.012)[0]
    albedo[:, zipper_mask, :3] = np.array([0.28, 0.29, 0.30]) # Cremallera grafito
    
    albedo[:, :, 3] = 1.0
    albedo = np.clip(albedo, 0.0, 1.0)
    
    # 2. Normal: Ondulación suave de acolchado
    height = baffles.repeat(w, axis=1) * 0.4 + generate_noise_2d(h, w, freq=80) * 0.04
    normal = height_to_normal(height, strength=1.5)
    
    # 3. ORM: Brillo de nylon técnico (Roughness ~0.62)
    orm = np.zeros((h, w, 4), dtype=np.float32)
    orm[:, :, 0] = 0.95
    orm[:, :, 1] = 0.62 - (baffles * 0.06)
    orm[:, :, 2] = 0.02
    orm[:, zipper_mask, 1] = 0.28
    orm[:, zipper_mask, 2] = 0.85
    orm[:, :, 3] = 1.0
    
    save_numpy_image("axel_jacket_albedo", albedo, f"{OUTPUT_DIR}/axel_jacket_albedo.png")
    save_numpy_image("axel_jacket_normal", normal, f"{OUTPUT_DIR}/axel_jacket_normal.png")
    save_numpy_image("axel_jacket_orm", orm, f"{OUTPUT_DIR}/axel_jacket_orm.png")

def generate_pants_textures():
    print("-> Generando suite de texturas PBR para Pantalón de Axel...")
    h, w = RES, RES
    
    albedo = np.zeros((h, w, 4), dtype=np.float32)
    base_charcoal = np.array([0.12, 0.13, 0.16]) # Denim carbón oscuro
    fabric_noise = generate_noise_2d(h, w, freq=64) * 0.03
    
    for c in range(3):
        albedo[:, :, c] = base_charcoal[c] + fabric_noise
    albedo[:, :, 3] = 1.0
    albedo = np.clip(albedo, 0.0, 1.0)
    
    normal = height_to_normal(fabric_noise * 2.0, strength=1.2)
    
    orm = np.zeros((h, w, 4), dtype=np.float32)
    orm[:, :, 0] = 0.96
    orm[:, :, 1] = 0.88 # Denim áspero mate
    orm[:, :, 2] = 0.0
    orm[:, :, 3] = 1.0
    
    save_numpy_image("axel_pants_albedo", albedo, f"{OUTPUT_DIR}/axel_pants_albedo.png")
    save_numpy_image("axel_pants_normal", normal, f"{OUTPUT_DIR}/axel_pants_normal.png")
    save_numpy_image("axel_pants_orm", orm, f"{OUTPUT_DIR}/axel_pants_orm.png")

def generate_shoes_textures():
    print("-> Generando suite de texturas PBR para Calzado de Axel...")
    h, w = RES, RES
    
    albedo = np.zeros((h, w, 4), dtype=np.float32)
    # Suela negra y empeine oscuro urbano
    albedo[:, :, :3] = np.array([0.10, 0.10, 0.10])
    
    y = np.linspace(0, 1, h)[:, None]
    sole_mask = (y < 0.25)[:, 0]
    albedo[sole_mask, :, :3] = np.array([0.16, 0.16, 0.16]) # Goma de suela
    albedo[:, :, 3] = 1.0
    
    # Dibujo de huella / tracción
    x = np.linspace(0, 1, w)[None, :]
    tread = (np.sin(x * 32 * np.pi) * (y < 0.20)) * 0.4
    normal = height_to_normal(tread + generate_noise_2d(h, w, freq=64) * 0.05, strength=2.5)
    
    orm = np.zeros((h, w, 4), dtype=np.float32)
    orm[:, :, 0] = 0.92
    orm[:, :, 1] = 0.55 # Cuero/sintético
    orm[sole_mask, :, 1] = 0.82 # Goma vulcanizada
    orm[:, :, 2] = 0.0
    orm[:, :, 3] = 1.0
    
    save_numpy_image("axel_shoes_albedo", albedo, f"{OUTPUT_DIR}/axel_shoes_albedo.png")
    save_numpy_image("axel_shoes_normal", normal, f"{OUTPUT_DIR}/axel_shoes_normal.png")
    save_numpy_image("axel_shoes_orm", orm, f"{OUTPUT_DIR}/axel_shoes_orm.png")

def generate_mic_textures():
    print("-> Generando suite de texturas PBR para Micrófono de Axel...")
    h, w = RES, RES
    
    albedo = np.zeros((h, w, 4), dtype=np.float32)
    y = np.linspace(0, 1, h)[:, None]
    x = np.linspace(0, 1, w)[None, :]
    
    # Parte superior (rejilla plateada SM58) vs mango negro mate
    is_grille = (y > 0.50)[:, 0]
    albedo[:, :, :3] = np.array([0.14, 0.14, 0.15]) # Mango negro
    albedo[is_grille, :, :3] = np.array([0.72, 0.74, 0.76]) # Rejilla metálica
    albedo[:, :, 3] = 1.0
    
    # Malla de alambre entrecruzada para la rejilla
    mesh_pattern = (np.sin((x + y) * 64 * np.pi) * np.sin((x - y) * 64 * np.pi) * (y > 0.50)) * 0.5
    normal = height_to_normal(mesh_pattern, strength=3.0)
    
    orm = np.zeros((h, w, 4), dtype=np.float32)
    orm[:, :, 0] = 0.90
    orm[:, :, 1] = 0.45 # Mango con fricción
    orm[is_grille, :, 1] = 0.22 # Rejilla brillante pulida
    orm[is_grille, :, 2] = 0.95 # Rejilla 100% metálica
    orm[:, :, 3] = 1.0
    
    save_numpy_image("axel_mic_albedo", albedo, f"{OUTPUT_DIR}/axel_mic_albedo.png")
    save_numpy_image("axel_mic_normal", normal, f"{OUTPUT_DIR}/axel_mic_normal.png")
    save_numpy_image("axel_mic_orm", orm, f"{OUTPUT_DIR}/axel_mic_orm.png")

def main():
    print("==================================================")
    print("INICIANDO GENERACIÓN DE SUITE PBR PARA AXEL")
    print("==================================================")
    ensure_dir(OUTPUT_DIR)
    
    generate_skin_textures()
    generate_beanie_textures()
    generate_jacket_textures()
    generate_pants_textures()
    generate_shoes_textures()
    generate_mic_textures()
    
    print("==================================================")
    print("TODAS LAS TEXTURAS PBR DE AXEL GENERADAS CON ÉXITO")
    print("==================================================")

if __name__ == "__main__":
    main()
