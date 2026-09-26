"""
Generador de Texturas PBR para Lámina Acanalada (Corrugated Metal) y Tejuela de Azotea (Shingles)
Para su aplicación fotorrealista en:
- Dulcería Prisci (lámina ondulada roja vertical)
- Terminal de Autobuses (fascia acanalada vertical amarilla mostaza)
- Dársenas de Autobuses (techumbre acanalada industrial)
- Restaurante Flor de Michoacán (tejuela/shingle)
"""
import bpy
import numpy as np
import os

TEXTURES_DIR = os.path.abspath("godot_project/assets/textures")
os.makedirs(TEXTURES_DIR, exist_ok=True)

def generate_corrugated_textures(width=1024, height=1024):
    print("Generando mapas PBR de lámina acanalada...")
    # Genera ondas sinusoidales/trapezoidales a lo largo del eje X (canales verticales)
    x = np.linspace(0, 32 * 2 * np.pi, width, dtype=np.float32) # 32 costillas por metro de textura
    wave = np.sin(x) # Rango [-1, 1]
    
    # Perfil con costilla redondeada
    height_map = (wave * 0.5 + 0.5).reshape(1, width).repeat(height, axis=0)
    
    # Calcular derivadas para Normal Map (Espacio Tangente)
    # dx = d(height)/dx
    dx = np.gradient(height_map, axis=1) * 25.0
    dy = np.zeros_like(dx)
    dz = np.ones_like(dx)
    
    # Normalizar vectores
    norm = np.sqrt(dx**2 + dy**2 + dz**2)
    nx = -dx / norm
    ny = -dy / norm
    nz = dz / norm
    
    # Convertir a espacio de color RGB de normal map [0, 1] (X=R, Y=G, Z=B)
    r = (nx * 0.5 + 0.5)
    g = (ny * 0.5 + 0.5)
    b = (nz * 0.5 + 0.5)
    a = np.ones_like(r)
    
    rgba = np.stack([r, g, b, a], axis=-1).astype(np.float32)
    
    # Guardar Normal Map usando bpy
    img_name = "corrugated_metal_normal.png"
    img = bpy.data.images.new("Corrugated_Normal", width=width, height=height, alpha=True, float_buffer=False)
    img.pixels.foreach_set(rgba.flatten())
    out_path = os.path.join(TEXTURES_DIR, img_name)
    img.filepath_raw = out_path
    img.file_format = 'PNG'
    img.save()
    print(f"Guardado: {out_path}")
    
    # Roughness Map (metal pintado con ligero desgaste en crestas)
    roughness = 0.35 + 0.15 * (1.0 - height_map)
    r_rgba = np.stack([roughness, roughness, roughness, a], axis=-1).astype(np.float32)
    img_r = bpy.data.images.new("Corrugated_Roughness", width=width, height=height, alpha=True, float_buffer=False)
    img_r.pixels.foreach_set(r_rgba.flatten())
    out_r_path = os.path.join(TEXTURES_DIR, "corrugated_metal_roughness.png")
    img_r.filepath_raw = out_r_path
    img_r.file_format = 'PNG'
    img_r.save()
    print(f"Guardado: {out_r_path}")

def generate_shingle_textures(width=1024, height=1024):
    print("Generando mapas PBR de tejuela asfáltica (shingles)...")
    np.random.seed(42)
    num_rows = 16
    row_h = height / num_rows
    cols = 8
    col_w = width / cols
    
    y_indices, x_indices = np.indices((height, width), dtype=np.float32)
    row_idx = np.floor(y_indices / row_h).astype(np.int32)
    y_in_row = (y_indices - row_idx * row_h) / row_h # [0, 1]
    
    x_offset = (row_idx % 2) * (col_w * 0.5)
    x_shifted = (x_indices + x_offset) % width
    col_idx = np.floor(x_shifted / col_w).astype(np.int32)
    x_in_col = (x_shifted - col_idx * col_w) / col_w
    
    # Relieve de solape (sawtooth en Y)
    h_y = y_in_row
    # Ranura vertical entre tejuelas
    slot_width = 0.05
    dist_slot = np.minimum(x_in_col, 1.0 - x_in_col)
    slot_mask = np.clip(dist_slot / slot_width, 0.0, 1.0)
    
    granules = np.random.uniform(-0.06, 0.06, (height, width)).astype(np.float32)
    h_total = np.clip(h_y * slot_mask + granules, 0.0, 1.0)
    
    dx = np.gradient(h_total, axis=1) * 12.0
    dy = np.gradient(h_total, axis=0) * 12.0
    dz = np.ones_like(dx)
    norm = np.sqrt(dx**2 + dy**2 + dz**2)
    
    nx = -dx / norm
    ny = -dy / norm
    nz = dz / norm
    
    rgba = np.stack([nx*0.5+0.5, ny*0.5+0.5, nz*0.5+0.5, np.ones_like(nx)], axis=-1).astype(np.float32)
    
    img = bpy.data.images.new("Shingle_Normal", width=width, height=height, alpha=True, float_buffer=False)
    img.pixels.foreach_set(rgba.flatten())
    out_path = os.path.join(TEXTURES_DIR, "shingle_roof_normal.png")
    img.filepath_raw = out_path
    img.file_format = 'PNG'
    img.save()
    print(f"Guardado: {out_path}")

if __name__ == "__main__":
    generate_corrugated_textures()
    generate_shingle_textures()
