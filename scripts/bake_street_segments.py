#!/usr/bin/env python3
"""
bake_street_segments.py
=======================
Genera godot_project/assets/street_segments.json a partir del caché OSM de vialidades.

Salida: JSON con estructura optimizada para lookup espacial en GDScript:
  {
    "cell_size": 200.0,       # tamaño de celda en metros
    "segments": [             # lista plana de segmentos
      {"name": "Calle X", "hw": "residential",
       "x0": 100.0, "z0": -50.0, "x1": 140.0, "z1": -50.0},
      ...
    ],
    "grid": {                 # índice espacial: clave "cx,cz" → [índices en segments]
      "0,0": [3, 7, 12],
      ...
    }
  }

El GDScript calcula cuál celda contiene al jugador y busca solo entre
los segmentos de esa celda (y las 8 vecinas), en lugar de iterar los ~11 k.

Uso:
  python3 scripts/bake_street_segments.py
"""

import json
import math
import os

# ── Parámetros geodésicos ───────────────────────────────────────────────────
TECATE_LAT = 32.573229
TECATE_LON = -116.626536
EARTH_R    = 6378137.0

HIGHWAY_PRIORITY = {
    "motorway": 0, "trunk": 1, "primary": 2, "secondary": 3,
    "tertiary": 4, "residential": 5, "unclassified": 5,
    "living_street": 6, "service": 7,
    "motorway_link": 3, "trunk_link": 3,
    "primary_link": 3, "secondary_link": 4, "tertiary_link": 5,
}

CELL_SIZE = 200.0   # metros — equilibrio entre tamaño de JSON y velocidad de lookup

# ── Helpers ──────────────────────────────────────────────────────────────────

def gps_to_godot(lat: float, lon: float) -> tuple[float, float]:
    """Convierte WGS-84 → coordenadas locales de Godot (x=Este, z=Sur)."""
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    lat_c   = math.radians(TECATE_LAT)
    lon_c   = math.radians(TECATE_LON)
    x = EARTH_R * (lon_rad - lon_c) * math.cos(lat_c)
    # y_norte → z_godot: Norte es -Z en Godot (convención del proyecto)
    z = -EARTH_R * (lat_rad - lat_c)
    return x, z

def cell_key(x: float, z: float, cell_size: float) -> str:
    cx = int(math.floor(x / cell_size))
    cz = int(math.floor(z / cell_size))
    return f"{cx},{cz}"

# ── Pipeline ─────────────────────────────────────────────────────────────────

def main():
    input_path  = "godot_project/assets/osm_cache/road_osm.json"
    output_path = "godot_project/assets/street_segments.json"

    if not os.path.exists(input_path):
        print(f"[ERROR] No se encontró: {input_path}")
        return

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    segments: list[dict] = []
    seen_midpoints: set[tuple[float, float]] = set()

    for way in data["elements"]:
        tags = way.get("tags", {})
        name = tags.get("name", "").strip()
        if not name:
            continue
        hw = tags.get("highway", "")
        if hw not in HIGHWAY_PRIORITY:
            continue

        geometry = way.get("geometry", [])
        if len(geometry) < 2:
            continue

        for i in range(len(geometry) - 1):
            p0 = geometry[i]
            p1 = geometry[i + 1]
            x0, z0 = gps_to_godot(p0["lat"], p0["lon"])
            x1, z1 = gps_to_godot(p1["lat"], p1["lon"])

            # Deduplicar segmentos con midpoint idéntico (tras redondeo a 1 m)
            mx = round((x0 + x1) * 0.5)
            mz = round((z0 + z1) * 0.5)
            key = (mx, mz)
            if key in seen_midpoints:
                continue
            seen_midpoints.add(key)

            segments.append({
                "name": name,
                "hw":   hw,
                "x0":   round(x0, 1),
                "z0":   round(z0, 1),
                "x1":   round(x1, 1),
                "z1":   round(z1, 1),
            })

    print(f"[bake] Segmentos únicos generados: {len(segments)}")

    # ── Construcción del índice espacial ────────────────────────────────────
    grid: dict[str, list[int]] = {}

    for idx, seg in enumerate(segments):
        # Registrar el segmento en todas las celdas que toca su AABB
        x_min = min(seg["x0"], seg["x1"])
        x_max = max(seg["x0"], seg["x1"])
        z_min = min(seg["z0"], seg["z1"])
        z_max = max(seg["z0"], seg["z1"])

        cx0 = int(math.floor(x_min / CELL_SIZE))
        cx1 = int(math.floor(x_max / CELL_SIZE))
        cz0 = int(math.floor(z_min / CELL_SIZE))
        cz1 = int(math.floor(z_max / CELL_SIZE))

        for cx in range(cx0, cx1 + 1):
            for cz in range(cz0, cz1 + 1):
                ck = f"{cx},{cz}"
                grid.setdefault(ck, []).append(idx)

    print(f"[bake] Celdas de grilla: {len(grid)}")

    output = {
        "cell_size": CELL_SIZE,
        "segments":  segments,
        "grid":      grid,
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = os.path.getsize(output_path) / 1024
    print(f"[bake] Guardado en: {output_path}  ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
