"""
=============================================================================
Generador de Texturas PBR Hiperrealistas para Axel (Tecate Simulator)
=============================================================================
Sintetiza mapas PBR en resolución 1024x1024 (Albedo, Normal OpenGL, ORM)
fieles a la identidad fotográfica de Axel ('scratch/humans/axel.png'):
- Piel con gradiente dérmico, poros micro-estructurales, sombra de barba juvenil,
  cejas densas arqueadas y labios definidos (sin ojos 2D pintados).
- Textura dedicada para globos oculares 3D (esclera, iris castaño oscuro, pupila, brillo).
- Gorro beanie con tejido acanalado de lana verde oliva.
- Chamarra acolchada azul marino profundo con franjas y cremallera.
- Pantalón de mezclilla oscura (denim) y calzado urbano.
- Cero accesorios que no sean indumentaria (sin micrófono).
=============================================================================
"""

import os
import bpy
import numpy as np

OUTPUT_DIR = "godot_project/assets/characters/textures"
RES = 1024

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
    dx = np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)
    dy = np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)
    
    nx = -dx * strength
    ny = dy * strength
    nz = np.ones((h, w), dtype=np.float32)
    
    norm = np.sqrt(nx**2 + ny**2 + nz**2)
    norm[norm == 0] = 1.0
    nx /= norm
    ny /= norm
    nz /= norm
    
    res = np.zeros((h, w, 4), dtype=np.float32)
    res[:, :, 0] = nx * 0.5 + 0.5
    res[:, :, 1] = ny * 0.5 + 0.5
    res[:, :, 2] = nz * 0.5 + 0.5
    res[:, :, 3] = 1.0
    return res

def generate_skin_textures():
    print("-> Generando suite de texturas PBR para Piel de Axel...")
    h, w = RES, RES
    
    # 1. Albedo: Tez apiñonada natural con gradientes faciales anatómicos
    albedo = np.zeros((h, w, 4), dtype=np.float32)
    base_skin = np.array([0.76, 0.58, 0.48]) # Tono base apiñonado de Axel
    warm_tone = np.array([0.82, 0.50, 0.42]) # Nariz, mejillas, labios
    shadow_tone = np.array([0.64, 0.50, 0.44]) # Cuencas orbitarias, pliegues
    
    y = np.linspace(0, 1, h)[:, None]
    x = np.linspace(0, 1, w)[None, :]
    
    # Gradiente vertical de iluminación dérmica
    face_warmth = np.exp(-((x - 0.5)**2 / 0.08 + (y - 0.52)**2 / 0.10))
    pores = generate_noise_2d(h, w, freq=64) * 0.03 - 0.015
    
    for c in range(3):
        albedo[:, :, c] = base_skin[c] * (1.0 - face_warmth * 0.25) + warm_tone[c] * (face_warmth * 0.25) + pores

    # Cejas masculinas densas y arqueadas de Axel (en Y ~ 0.68)
    eyebrow_l = np.exp(-((x - 0.38)**2 / 0.0035 + (y - 0.68)**2 / 0.0007))
    eyebrow_r = np.exp(-((x - 0.62)**2 / 0.0035 + (y - 0.68)**2 / 0.0007))
    eyebrow_mask = np.clip(eyebrow_l + eyebrow_r, 0.0, 1.0)
    brow_color = np.array([0.10, 0.08, 0.06])
    for c in range(3):
        albedo[:, :, c] = albedo[:, :, c] * (1.0 - eyebrow_mask * 0.94) + brow_color[c] * (eyebrow_mask * 0.94)

    # Cuencas oculares y pliegues de párpados (sombra anatómica suave, sin ojos 2D)
    for eye_cx in [0.38, 0.62]:
        orbit_dist = np.sqrt(((x - eye_cx) / 0.06)**2 + ((y - 0.58) / 0.04)**2)
        orbit_shade = np.clip(1.0 - orbit_dist, 0.0, 1.0)**2 * 0.35
        for c in range(3):
            albedo[:, :, c] = albedo[:, :, c] * (1.0 - orbit_shade) + shadow_tone[c] * orbit_shade

    # Labios anatómicos con bermellón suave y pliegue de comisura (en Y ~ 0.38)
    lip_mask = np.exp(-((x - 0.50)**2 / 0.007 + (y - 0.38)**2 / 0.0012))
    lip_split = np.exp(-((x - 0.50)**2 / 0.006 + (y - 0.38)**2 / 0.00015))
    lip_color = np.array([0.68, 0.40, 0.36])
    for c in range(3):
        albedo[:, :, c] = albedo[:, :, c] * (1.0 - lip_mask * 0.65) + lip_color[c] * (lip_mask * 0.65)
        albedo[:, :, c] = albedo[:, :, c] * (1.0 - lip_split * 0.80) + 0.12 * (lip_split * 0.80)

    # Sombra sutil de barba / mandíbula juvenil (5 o'clock shadow fiel a axel.png)
    jaw_stubble = np.exp(-((x - 0.50)**2 / 0.06 + (y - 0.25)**2 / 0.020)) * (y < 0.42)
    stubble_col = np.array([0.62, 0.48, 0.42])
    for c in range(3):
        albedo[:, :, c] = albedo[:, :, c] * (1.0 - jaw_stubble * 0.22) + stubble_col[c] * (jaw_stubble * 0.22)

    albedo[:, :, 3] = 1.0
    albedo = np.clip(albedo, 0.0, 1.0)

    # 2. Normal Map: microporos y relieve sutil de cejas/labios
    pore_map = generate_noise_2d(h, w, freq=128) * 0.15
    feature_height = (eyebrow_mask * 0.35) + (lip_mask * 0.25) - (lip_split * 0.30) + pore_map
    normal = height_to_normal(feature_height, strength=1.5)

    # 3. ORM: Ambient Occlusion, Roughness, Metallic
    orm = np.zeros((h, w, 4), dtype=np.float32)
    orm[:, :, 0] = 1.0 - (lip_split * 0.40) # AO en comisura
    orm[:, :, 1] = 0.55 - (face_warmth * 0.08) + (generate_noise_2d(h, w, freq=16) * 0.05)
    orm[:, :, 1] = orm[:, :, 1] * (1.0 - lip_mask * 0.30) # Labios ligeramente más húmedos
    orm[:, :, 2] = 0.0 # No metálico
    orm[:, :, 3] = 1.0
    orm = np.clip(orm, 0.0, 1.0)

    save_numpy_image("axel_skin_albedo", albedo, f"{OUTPUT_DIR}/axel_skin_albedo.png")
    save_numpy_image("axel_skin_normal", normal, f"{OUTPUT_DIR}/axel_skin_normal.png")
    save_numpy_image("axel_skin_orm", orm, f"{OUTPUT_DIR}/axel_skin_orm.png")

def generate_eyes_textures():
    print("-> Generando suite de texturas PBR para Globos Oculares 3D...")
    h, w = 512, 512
    
    y = np.linspace(-1, 1, h)[:, None]
    x = np.linspace(-1, 1, w)[None, :]
    r = np.sqrt(x**2 + y**2)
    
    # 1. Albedo: Esclera blanca marfil con anillo limbal e iris castaño oscuro
    albedo = np.zeros((h, w, 4), dtype=np.float32)
    sclera_col = np.array([0.94, 0.93, 0.92])
    iris_col = np.array([0.18, 0.12, 0.08]) # Castaño oscuro profundo de Axel
    iris_highlight = np.array([0.28, 0.19, 0.13])
    pupil_col = np.array([0.02, 0.02, 0.02])
    
    r_iris = 0.45
    r_pupil = 0.16
    
    # Fibra radial del iris
    theta = np.arctan2(y, x)
    fibers = (np.sin(theta * 32.0) + 1.0) * 0.5 * 0.15
    
    for c in range(3):
        albedo[:, :, c] = sclera_col[c]
    
    # Máscara iris con degradado limbal
    iris_mask = np.clip((r_iris - r) / 0.04, 0.0, 1.0)
    for c in range(3):
        albedo[:, :, c] = albedo[:, :, c] * (1.0 - iris_mask) + (iris_col[c] + fibers * iris_highlight[c]) * iris_mask
        
    # Pupila central negra
    pupil_mask = np.clip((r_pupil - r) / 0.03, 0.0, 1.0)
    for c in range(3):
        albedo[:, :, c] = albedo[:, :, c] * (1.0 - pupil_mask) + pupil_col[c] * pupil_mask
        
    albedo[:, :, 3] = 1.0
    albedo = np.clip(albedo, 0.0, 1.0)
    
    # 2. Normal: Curvatura corneal
    cornea_bump = np.clip(1.0 - (r / r_iris)**2, 0.0, 1.0) * (r < r_iris) * 0.4
    normal = height_to_normal(cornea_bump, strength=2.0)
    
    # 3. ORM: Ojo hiperhúmedo de alta reflectividad
    orm = np.zeros((h, w, 4), dtype=np.float32)
    orm[:, :, 0] = 1.0 # AO
    orm[:, :, 1] = 0.05 # Muy brillante / húmedo (Roughness ultra-baja)
    orm[:, :, 2] = 0.0 # No metálico
    orm[:, :, 3] = 1.0
    
    save_numpy_image("axel_eyes_albedo", albedo, f"{OUTPUT_DIR}/axel_eyes_albedo.png")
    save_numpy_image("axel_eyes_normal", normal, f"{OUTPUT_DIR}/axel_eyes_normal.png")
    save_numpy_image("axel_eyes_orm", orm, f"{OUTPUT_DIR}/axel_eyes_orm.png")

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
    orm[:, :, 0] = 0.85 + (ribs * 0.15)
    orm[:, :, 1] = 0.94 # Rugosidad alta
    orm[:, :, 2] = 0.0
    orm[:, :, 3] = 1.0
    
    save_numpy_image("axel_beanie_albedo", albedo, f"{OUTPUT_DIR}/axel_beanie_albedo.png")
    save_numpy_image("axel_beanie_normal", normal, f"{OUTPUT_DIR}/axel_beanie_normal.png")
    save_numpy_image("axel_beanie_orm", orm, f"{OUTPUT_DIR}/axel_beanie_orm.png")

def generate_jacket_textures():
    print("-> Generando suite de texturas PBR para Chamarra de Axel...")
    h, w = RES, RES
    
    # 1. Albedo: Azul marino técnico elegante con acolchado
    albedo = np.zeros((h, w, 4), dtype=np.float32)
    base_navy = np.array([0.10, 0.12, 0.18]) # Azul marino de axel.png
    baffle_highlight = np.array([0.14, 0.17, 0.24])
    
    y = np.linspace(0, 1, h)[:, None]
    x = np.linspace(0, 1, w)[None, :]
    
    baffles = (np.sin(y * 8 * np.pi) + 1.0) * 0.5
    micro_weave = generate_noise_2d(h, w, freq=64) * 0.03
    
    for c in range(3):
        albedo[:, :, c] = base_navy[c] * (1.0 - baffles * 0.15) + baffle_highlight[c] * (baffles * 0.15) + micro_weave
        
    zipper_mask = (np.abs(x - 0.5) < 0.012)[0]
    albedo[:, zipper_mask, :3] = np.array([0.28, 0.29, 0.30])
    
    albedo[:, :, 3] = 1.0
    albedo = np.clip(albedo, 0.0, 1.0)
    
    # 2. Normal: Ondulación suave de acolchado
    height = baffles.repeat(w, axis=1) * 0.4 + generate_noise_2d(h, w, freq=80) * 0.04
    normal = height_to_normal(height, strength=1.5)
    
    # 3. ORM: Brillo de nylon técnico
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
    base_charcoal = np.array([0.12, 0.13, 0.16])
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
    albedo[:, :, :3] = np.array([0.10, 0.10, 0.10])
    
    y = np.linspace(0, 1, h)[:, None]
    sole_mask = (y < 0.25)[:, 0]
    albedo[sole_mask, :, :3] = np.array([0.16, 0.16, 0.16])
    albedo[:, :, 3] = 1.0
    
    x = np.linspace(0, 1, w)[None, :]
    tread = (np.sin(x * 32 * np.pi) * (y < 0.20)) * 0.4
    normal = height_to_normal(tread + generate_noise_2d(h, w, freq=64) * 0.05, strength=2.5)
    
    orm = np.zeros((h, w, 4), dtype=np.float32)
    orm[:, :, 0] = 0.92
    orm[:, :, 1] = 0.55
    orm[sole_mask, :, 1] = 0.82
    orm[:, :, 2] = 0.0
    orm[:, :, 3] = 1.0
    
    save_numpy_image("axel_shoes_albedo", albedo, f"{OUTPUT_DIR}/axel_shoes_albedo.png")
    save_numpy_image("axel_shoes_normal", normal, f"{OUTPUT_DIR}/axel_shoes_normal.png")
    save_numpy_image("axel_shoes_orm", orm, f"{OUTPUT_DIR}/axel_shoes_orm.png")

def main():
    print("==================================================")
    print("INICIANDO GENERACIÓN DE SUITE PBR PARA AXEL")
    print("==================================================")
    ensure_dir(OUTPUT_DIR)
    
    generate_skin_textures()
    generate_eyes_textures()
    generate_beanie_textures()
    generate_jacket_textures()
    generate_pants_textures()
    generate_shoes_textures()
    
    print("==================================================")
    print("TODAS LAS TEXTURAS PBR DE AXEL GENERADAS CON ÉXITO")
    print("==================================================")

if __name__ == "__main__":
    main()
