#!/usr/bin/env python3
"""
scripts/apply_historical_corrections_2009.py
Aplica correcciones declarativas de 2009 a los datos viales del simulador.
Restituye el tramo vehicular de Calle Presidente Lázaro Cárdenas entre Juárez y Libertad.
"""

import json
import os
import sys

CORRECTIONS_FILE = "godot_project/assets/gis/historical_corrections_2009.json"
ROAD_OSM_FILE = "godot_project/assets/osm_cache/road_osm.json"

def apply_corrections():
    if not os.path.exists(CORRECTIONS_FILE):
        print(f"[Error] No se encontró el archivo de correcciones: {CORRECTIONS_FILE}")
        sys.exit(1)
        
    if not os.path.exists(ROAD_OSM_FILE):
        print(f"[Error] No se encontró el archivo vial OSM: {ROAD_OSM_FILE}")
        sys.exit(1)

    with open(CORRECTIONS_FILE, "r", encoding="utf-8") as f:
        corrections = json.load(f)

    with open(ROAD_OSM_FILE, "r", encoding="utf-8") as f:
        osm_data = json.load(f)

    elements = osm_data.get("elements", [])
    existing_ids = {el.get("id") for el in elements}
    
    injected_count = 0
    for via in corrections.get("vias_restituidas", []):
        way_id = via["id"]
        if way_id in existing_ids:
            print(f"[Info] La vía {way_id} ({via['nombre']}) ya existe en {ROAD_OSM_FILE}. Actualizando...")
            # Reemplazar existente
            elements = [el for el in elements if el.get("id") != way_id]

        pts = via["puntos_gps"]
        lats = [p["lat"] for p in pts]
        lons = [p["lon"] for p in pts]
        
        new_way = {
            "type": "way",
            "id": way_id,
            "bounds": {
                "minlat": min(lats),
                "minlon": min(lons),
                "maxlat": max(lats),
                "maxlon": max(lons)
            },
            "nodes": [via["id"] * 10 + i for i in range(len(pts))],
            "geometry": [{"lat": p["lat"], "lon": p["lon"]} for p in pts],
            "tags": via["tags"]
        }
        elements.append(new_way)
        injected_count += 1
        print(f"[Éxito] Inyectado tramo histórico 2009: {via['nombre']} (ID: {way_id})")

    osm_data["elements"] = elements
    with open(ROAD_OSM_FILE, "w", encoding="utf-8") as f:
        json.dump(osm_data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Se aplicaron {injected_count} correcciones viales históricas a {ROAD_OSM_FILE}.")

if __name__ == "__main__":
    apply_corrections()
