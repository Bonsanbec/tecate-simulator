"""
Generador de Textura PBR: Ladrillo Normativo Palacio Municipal de Tecate (2009)
Ladrillo industrial/normativo de fábrica, uniforme y regular.
Color: Rojo terracota medio oscuro, juntas de mortero grises visibles.
Output:
  godot_project/assets/palacio_ladrillo_albedo.png    (1024×1024)
  godot_project/assets/palacio_ladrillo_normal.png    (1024×1024)
  godot_project/assets/palacio_ladrillo_roughness.png (1024×1024)
Ejecución headless:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/generate_palacio_ladrillo_texture.py
"""

import bpy
import numpy as np
import os
import sys

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
    print(f"[Texture] Guardada: {filepath}")

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

def generate_palacio_ladrillo(w=1024, h=1024):
    """
    Ladrillo normativo / industrial de fábrica para el Palacio Municipal de Tecate (2009).
    Características:
      - Formato estándar mexicano 6x12 cm (relación 1:2)
      - Color: Rojo terracota uniforme, ligeramente oscuro (#7A2D1E linear)
      - Variación tonal: Mínima (ladrillo de fábrica, no artesanal)
      - Juntas: Mortero gris cemento visible, ancho ~12% del ladrillo
      - Sin irregularidades de quema ni variaciones fuertes entre piezas
    """
    np.random.seed(314)
    print(">> Generando textura de Ladrillo Normativo Palacio Municipal...")

    # Parámetros del aparejo: 8 filas × 16 columnas de ladrillos en la textura (1:2)
    n_cols = 16
    n_rows = 8
    brick_w = w // n_cols          # Ancho de cada ladrillo en píxeles
    brick_h = h // n_rows          # Alto de cada ladrillo en píxeles
    mortar_px_x = max(2, int(brick_w * 0.10))  # Junta horizontal ~10%
    mortar_px_y = max(2, int(brick_h * 0.12))  # Junta vertical ~12%

    # Color base ladrillo normativo (lineal sRGB)
    c_brick  = np.array([0.52, 0.20, 0.14])   # Rojo terracota uniforme
    c_mortar = np.array([0.52, 0.50, 0.48])   # Mortero gris cemento

    albedo   = np.zeros((h, w, 4), dtype=np.float32)
    height_m = np.zeros((h, w),    dtype=np.float32)
    rough    = np.zeros((h, w, 4), dtype=np.float32)

    for row in range(n_rows):
        y0 = row * brick_h
        y1 = (row + 1) * brick_h
        # Aparejo a soga: cada fila desplazada media pieza
        offset_col = (n_cols // 2) if (row % 2 == 1) else 0

        for col in range(n_cols + 1):   # +1 para cubrir el desplazamiento
            # Coordenadas X con desplazamiento de hilada
            x0 = (col - offset_col // n_cols) * brick_w - (offset_col * brick_w // n_cols)
            x0_raw = col * brick_w - (brick_w // 2 if row % 2 == 1 else 0)
            x1_raw = x0_raw + brick_w

            # Coordenadas internas reales del ladrillo (sin junta)
            ix0 = x0_raw + mortar_px_x
            ix1 = x1_raw - mortar_px_x
            iy0 = y0 + mortar_px_y
            iy1 = y1 - mortar_px_y

            # Recortar al canvas
            cix0 = max(0, ix0)
            cix1 = min(w, ix1)
            ciy0 = max(0, iy0)
            ciy1 = min(h, iy1)

            if cix1 <= cix0 or ciy1 <= ciy0:
                continue

            region_h = ciy1 - ciy0
            region_w = cix1 - cix0

            # Variación tonal muy sutil por ladrillo (ladrillo de fábrica)
            tone_var = np.random.uniform(-0.03, 0.03, 3)
            brick_color = np.clip(c_brick + tone_var, 0, 1)

            # Ruido de textura superficial (granulado de cocción, muy fino)
            grain = (np.random.rand(region_h, region_w, 1) - 0.5) * 0.025

            tile_rgb = brick_color.reshape(1, 1, 3) + grain

            # Mapa de altura: ladrillo ligeramente convexo (pillowing suave)
            ty_r, tx_r = np.meshgrid(
                np.linspace(0, 1, region_h),
                np.linspace(0, 1, region_w),
                indexing='ij'
            )
            pillow = np.sin(np.pi * tx_r) * np.sin(np.pi * ty_r) * 0.7

            albedo[ciy0:ciy1, cix0:cix1, :3] = np.clip(tile_rgb, 0, 1)
            albedo[ciy0:ciy1, cix0:cix1,  3] = 1.0
            height_m[ciy0:ciy1, cix0:cix1]   = pillow

            # Roughness del ladrillo: textura cerámica moderada
            rough[ciy0:ciy1, cix0:cix1, :3] = 0.78 + (np.random.rand(region_h, region_w, 1) - 0.5) * 0.05
            rough[ciy0:ciy1, cix0:cix1,  3] = 1.0

    # Rellenar con mortero las zonas no pintadas (juntas)
    mortar_mask = (albedo[:, :, 3] == 0.0)
    for c in range(3):
        albedo[:, :, c] = np.where(mortar_mask, c_mortar[c] + (np.random.rand(h, w) - 0.5) * 0.02, albedo[:, :, c])
    albedo[:, :, 3] = 1.0
    rough[:, :, :3] = np.where(mortar_mask[:, :, None], 0.88, rough[:, :, :3])  # Mortero más rugoso
    rough[:, :,  3] = 1.0

    # Altura de mortero = 0 (hundido respecto al ladrillo)
    height_m = np.where(mortar_mask, 0.0, height_m)

    albedo  = np.clip(albedo,  0.0, 1.0)
    rough   = np.clip(rough,   0.0, 1.0)
    normal  = generate_normal_from_height(height_m, scale=0.035)

    # Rutas de salida relativas al directorio de trabajo
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(root, "godot_project", "assets")

    save_blender_image("palacio_ladrillo_albedo",    albedo,  os.path.join(out_dir, "palacio_ladrillo_albedo.png"))
    save_blender_image("palacio_ladrillo_normal",    normal,  os.path.join(out_dir, "palacio_ladrillo_normal.png"))
    save_blender_image("palacio_ladrillo_roughness", rough,   os.path.join(out_dir, "palacio_ladrillo_roughness.png"))
    print("[Ladrillo Palacio] Texturas PBR generadas exitosamente.")

if __name__ == "__main__":
    generate_palacio_ladrillo()
