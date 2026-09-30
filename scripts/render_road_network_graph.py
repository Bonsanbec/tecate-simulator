"""
RENDERIZADOR DEL GRAFO VIAL Y RUTAS DE AUTOBÚS (Tecate Simulator)
Genera una imagen PNG en alta resolución del mapa de todas las vialidades
del videojuego y proyecta el recorrido del autobús con diferenciación cromática
de ida, vuelta y estaciones de abordaje.

No requiere librerías externas (utiliza zlib y struct nativos de Python).
"""

import json
import math
import struct
import zlib
import os

STREETS_JSON = "godot_project/assets/street_segments.json"
ROUTE_JSON = "godot_project/assets/vehicles/bus_hongo_route.json"
OUTPUT_PNG = "docs/images/bus_hongo/mapa_ruta_el_hongo.png"

def write_png(filename, width, height, buffer_rgb):
    """Guarda un buffer de bytes RGB plano en formato PNG estándar sin dependencias externas."""
    # Cada scanline requiere 1 byte de filtro inicial (0 = None) + width * 3 bytes RGB
    raw_scanlines = bytearray()
    row_bytes = width * 3
    for y in range(height):
        raw_scanlines.append(0) # Filtro None
        start = y * row_bytes
        raw_scanlines.extend(buffer_rgb[start:start + row_bytes])

    compressed = zlib.compress(bytes(raw_scanlines), level=9)

    with open(filename, 'wb') as f:
        # Firma PNG
        f.write(b'\x89PNG\r\n\x1a\n')

        # Chunk IHDR
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
        f.write(struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc))

        # Chunk IDAT
        idat_len = len(compressed)
        idat_crc = zlib.crc32(b'IDAT' + compressed)
        f.write(struct.pack('>I', idat_len) + b'IDAT' + compressed + struct.pack('>I', idat_crc))

        # Chunk IEND
        iend_crc = zlib.crc32(b'IEND')
        f.write(struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc))

    print(f"[Mapa] Guardado exitosamente en: {filename} ({os.path.getsize(filename):,} bytes)")

def draw_line(buf, w, h, x0, y0, x1, y1, color, thickness=1):
    """Algoritmo de Bresenham con grosor configurable."""
    r, g, b = color
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    t_rad = thickness // 2

    while True:
        for ox in range(-t_rad, t_rad + 1):
            for oy in range(-t_rad, t_rad + 1):
                px = x0 + ox
                py = y0 + oy
                if 0 <= px < w and 0 <= py < h:
                    idx = (py * w + px) * 3
                    buf[idx] = r
                    buf[idx + 1] = g
                    buf[idx + 2] = b

        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

def draw_circle(buf, w, h, cx, cy, radius, color, fill=True):
    r, g, b = color
    for y in range(max(0, cy - radius), min(h, cy + radius + 1)):
        for x in range(max(0, cx - radius), min(w, cx + radius + 1)):
            d2 = (x - cx)**2 + (y - cy)**2
            if fill:
                if d2 <= radius**2:
                    idx = (y * w + x) * 3
                    buf[idx] = r
                    buf[idx + 1] = g
                    buf[idx + 2] = b
            else:
                if (radius - 1.5)**2 <= d2 <= (radius + 0.5)**2:
                    idx = (y * w + x) * 3
                    buf[idx] = r
                    buf[idx + 1] = g
                    buf[idx + 2] = b

def main():
    os.makedirs(os.path.dirname(OUTPUT_PNG), exist_ok=True)

    print("[Mapa 1/4] Leyendo segmentos de calle...")
    with open(STREETS_JSON, 'r', encoding='utf-8') as f:
        streets_data = json.load(f)
    segments = streets_data.get('segments', [])

    print("[Mapa 2/4] Leyendo ruta de autobús...")
    with open(ROUTE_JSON, 'r', encoding='utf-8') as f:
        route_data = json.load(f)
    waypoints = route_data.get('waypoints', [])
    stations = route_data.get('station_indices', route_data.get('stations', {}))

    # Definición del marco de proyección ajustado a la extensión real de la ruta y zona urbana
    # (X: -7200 a 12600, Z: -1200 a 6600)
    min_x, max_x = -7200.0, 12600.0
    min_z, max_z = -1200.0, 6600.0

    img_w = 2560
    img_h = 1080

    def world_to_screen(x, z):
        sx = int((x - min_x) / (max_x - min_x) * (img_w - 60) + 30)
        # Z en Godot va hacia el sur; en pantalla Y va hacia abajo
        sy = int((z - min_z) / (max_z - min_z) * (img_h - 60) + 30)
        return sx, sy

    # Inicializar búfer con fondo azul marino muy oscuro (#0D1117)
    buf = bytearray([13, 17, 23] * (img_w * img_h))

    print("[Mapa 3/4] Trazando la red de calles completa...")
    # Capa 1: Calles urbanas secundarias y locales
    color_street = (38, 48, 62)
    color_primary = (65, 80, 105)

    for s in segments:
        x0, z0 = s['x0'], s['z0']
        x1, z1 = s['x1'], s['z1']
        hw = s.get('hw', '')
        sx0, sy0 = world_to_screen(x0, z0)
        sx1, sy1 = world_to_screen(x1, z1)

        if hw in ('primary', 'trunk', 'motorway'):
            draw_line(buf, img_w, img_h, sx0, sy0, sx1, sy1, color_primary, thickness=2)
        else:
            draw_line(buf, img_w, img_h, sx0, sy0, sx1, sy1, color_street, thickness=1)

    print("[Mapa 4/4] Superponiendo ruta del Autobús El Hongo...")
    # Trazar recorrido del autobús:
    # Waypoints están secuenciados. Dividimos a la mitad para ida y vuelta.
    half_idx = len(waypoints) // 2

    # Ida: Azul cian eléctrico (#00D4FF)
    color_ida = (0, 212, 255)
    for i in range(half_idx):
        p0 = waypoints[i]
        p1 = waypoints[i + 1]
        sx0, sy0 = world_to_screen(p0[0], p0[2])
        sx1, sy1 = world_to_screen(p1[0], p1[2])
        draw_line(buf, img_w, img_h, sx0, sy0, sx1, sy1, color_ida, thickness=3)

    # Vuelta: Naranja coral vivo (#FF6B35)
    color_vuelta = (255, 107, 53)
    for i in range(half_idx, len(waypoints) - 1):
        p0 = waypoints[i]
        p1 = waypoints[i + 1]
        sx0, sy0 = world_to_screen(p0[0], p0[2])
        sx1, sy1 = world_to_screen(p1[0], p1[2])
        draw_line(buf, img_w, img_h, sx0, sy0, sx1, sy1, color_vuelta, thickness=2)

    # Marcar estaciones y puntos neurálgicos
    # Central de Autobuses y Parque Hidalgo
    parque_sx, parque_sy = world_to_screen(-6.68, 2.68)
    draw_circle(buf, img_w, img_h, parque_sx, parque_sy, 7, (46, 204, 113), fill=True) # Verde esmeralda

    for s_idx_str, s_name in stations.items():
        s_idx = int(s_idx_str)
        if s_idx < len(waypoints):
            wpt = waypoints[s_idx]
            sx, sy = world_to_screen(wpt[0], wpt[2])
            draw_circle(buf, img_w, img_h, sx, sy, 6, (255, 230, 0), fill=True)
            draw_circle(buf, img_w, img_h, sx, sy, 8, (255, 255, 255), fill=False)

    # Extremo Sur (Carretera Libre Tijuana - Segmento Sur)
    sur_sx, sur_sy = world_to_screen(-6309.9, 5838.1)
    draw_circle(buf, img_w, img_h, sur_sx, sur_sy, 9, (231, 76, 60), fill=True)

    # Extremo Este (La Rumorosa / Mexicali)
    e_sx, e_sy = world_to_screen(12118.1, 636.4)
    draw_circle(buf, img_w, img_h, e_sx, e_sy, 9, (155, 89, 182), fill=True)

    write_png(OUTPUT_PNG, img_w, img_h, buf)

if __name__ == "__main__":
    main()
