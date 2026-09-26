import json
import numpy as np
import math

with open('scratch/cache/blocks_cache.json') as f:
    blocks = json.load(f)

for k, v in blocks.items():
    if '32.57328' in k or '116.62516' in k:
        poly_blocks = [(p[0], -p[1]) for p in v['polygon']]
        break

poly = np.array(poly_blocks)

# Ángulo canónico de los headings:
# heading norte = 355.158° => ángulo con eje -Z = -4.842°
# En coordenadas Godot XZ: rotación theta_canonica
theta_can = math.radians(-4.842)
c = math.cos(theta_can)
s = math.sin(theta_can)

# Proyectar los vértices del polígono al marco propio de la manzana:
# u_long = (c, 0, s)   # eje longitudinal poniente -> oriente
# u_trans = (-s, 0, c) # eje transversal norte -> sur
# x_propio = x * c + z * s
# z_propio = -x * s + z * c

p_rot = np.zeros_like(poly)
p_rot[:, 0] = poly[:, 0] * c + poly[:, 1] * s
p_rot[:, 1] = -poly[:, 0] * s + poly[:, 1] * c

print("--- DIMENSIONES EN EL MARCO CANÓNICO GEODÉSICO (theta = -4.842°) ---")
print(f"X propio (longitud poniente a oriente): min={np.min(p_rot[:,0]):.3f}, max={np.max(p_rot[:,0]):.3f}, span={np.ptp(p_rot[:,0]):.3f} m")
print(f"Z propio (profundidad norte a sur)   : min={np.min(p_rot[:,1]):.3f}, max={np.max(p_rot[:,1]):.3f}, span={np.ptp(p_rot[:,1]):.3f} m")

# Identificar las caras:
# Frente Norte (Av. Juárez): puntos con Z propio mínimo
# Frente Sur (Callejón Libertad): puntos con Z propio máximo
# Lateral Poniente (Ortiz Rubio): puntos con X propio mínimo
# Lateral Oriente (Rodríguez): puntos con X propio máximo

z_norte_propio = np.min(p_rot[:, 1])
z_sur_propio = np.max(p_rot[:, 1])
x_oeste_propio = np.min(p_rot[:, 0])
x_este_propio = np.max(p_rot[:, 0])

print(f"\nLímites propios de la manzana:")
print(f"  Frente Norte (Av. Juárez)    : Z_propio = {z_norte_propio:.3f}")
print(f"  Frente Sur (Callejón Libertad): Z_propio = {z_sur_propio:.3f}")
print(f"  Costado Poniente (Ortiz R.)   : X_propio = {x_oeste_propio:.3f}")
print(f"  Costado Oriente (Rodríguez)   : X_propio = {x_este_propio:.3f}")

print(f"\nPROFUNDIDAD EXACTA DE LA MANZANA (Norte a Sur) : {z_sur_propio - z_norte_propio:.3f} m")
print(f"ANCHO EXACTO DE LA MANZANA (Poniente a Oriente): {x_este_propio - x_oeste_propio:.3f} m")

# Ahora comparar con el modelo manzana_central_2009.glb:
# En Blender: X_MAX = 134.73 m, Y_MAX = 91.19 m
# Relaciones de escala:
print("\n--- COMPARACIÓN CON EL MODELO ACTUAL (134.73 x 91.19) ---")
print(f"Relación en Ancho       : {np.ptp(p_rot[:,0]) / 134.73:.4f}")
print(f"Relación en Profundidad : {np.ptp(p_rot[:,1]) / 91.19:.4f}")

