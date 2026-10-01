#!/usr/bin/env python3
"""
scratch/download_osm_full_terrain.py
Descarga robusta y estructurada de datos de OpenStreetMap para todas las capas
del terreno completo de Tecate Simulator.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
]

# BBox Maestro del terreno completo tecate2.glb
MIN_LAT = 32.211873
MIN_LON = -116.780761
MAX_LAT = 32.636077
MAX_LON = -115.874121

CACHE_DIR = "godot_project/assets/osm_cache"

def query_overpass(query_str, timeout=120):
    data = urllib.parse.urlencode({"data": query_str}).encode("utf-8")
    for attempt in range(8):
        endpoint = OVERPASS_ENDPOINTS[attempt % len(OVERPASS_ENDPOINTS)]
        print(f"  [Overpass] Querying {endpoint} (intento {attempt+1})...")
        try:
            req = urllib.request.Request(
                endpoint,
                data=data,
                headers={"User-Agent": f"TecateSimulatorRegionalBuilder/1.{attempt}"}
            )
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                content = json.loads(resp.read().decode("utf-8"))
            elapsed = time.time() - t0
            elems = content.get("elements", [])
            print(f"  [Overpass] Exito en {elapsed:.2f}s ({len(elems)} elementos recibidos).")
            return content
        except Exception as e:
            wait = 5 + attempt * 3
            print(f"  [Overpass Warning] Error en {endpoint}: {e}. Reintentando en {wait}s...")
            time.sleep(wait)
    raise RuntimeError("Fallo Overpass tras múltiples intentos.")

def download_railways():
    dest = os.path.join(CACHE_DIR, "railway_osm.json")
    print(f"\n[1/5] Descargando Ferrocarril (railway_osm.json)...")
    q = f"""[out:json][timeout:60];
way["railway"~"rail|abandoned|disused"]({MIN_LAT},{MIN_LON},{MAX_LAT},{MAX_LON});
out geom;
"""
    data = query_overpass(q, timeout=60)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"  -> Guardado en {dest} ({len(data.get('elements', []))} elementos).")

def download_bridges():
    dest = os.path.join(CACHE_DIR, "bridge_osm.json")
    print(f"\n[2/5] Descargando Puentes (bridge_osm.json)...")
    q = f"""[out:json][timeout:60];
way["bridge"]["bridge"!="no"]({MIN_LAT},{MIN_LON},{MAX_LAT},{MAX_LON});
out geom;
"""
    data = query_overpass(q, timeout=60)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"  -> Guardado en {dest} ({len(data.get('elements', []))} elementos).")

def download_waterways():
    dest = os.path.join(CACHE_DIR, "water_osm.json")
    print(f"\n[3/5] Descargando Cuerpos de Agua (water_osm.json)...")
    q = f"""[out:json][timeout:120];
(
  way["natural"="water"]({MIN_LAT},{MIN_LON},{MAX_LAT},{MAX_LON});
  relation["natural"="water"]({MIN_LAT},{MIN_LON},{MAX_LAT},{MAX_LON});
  way["waterway"~"river|stream|canal"]({MIN_LAT},{MIN_LON},{MAX_LAT},{MAX_LON});
);
out geom;
"""
    data = query_overpass(q, timeout=120)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"  -> Guardado en {dest} ({len(data.get('elements', []))} elementos).")

def download_manzanas():
    dest = os.path.join(CACHE_DIR, "manzanas_osm.json")
    print(f"\n[4/5] Descargando Manzanas y Uso de Suelo (manzanas_osm.json)...")
    q = f"""[out:json][timeout:120];
(
  way["landuse"~"residential|commercial|industrial|retail|cemetery"]({MIN_LAT},{MIN_LON},{MAX_LAT},{MAX_LON});
  way["leisure"~"park|pitch|garden"]({MIN_LAT},{MIN_LON},{MAX_LAT},{MAX_LON});
  way["amenity"~"parking|school|hospital"]({MIN_LAT},{MIN_LON},{MAX_LAT},{MAX_LON});
);
out geom;
"""
    data = query_overpass(q, timeout=120)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"  -> Guardado en {dest} ({len(data.get('elements', []))} elementos).")

def download_roads():
    dest = os.path.join(CACHE_DIR, "road_osm.json")
    print(f"\n[5/5] Descargando Red Vial Completa (road_osm.json)...")
    # Particionamos en dos franjas de longitud para garantizar cero timeouts:
    # Franja Oeste-Centro: [-116.780761, -116.45] (Tecate metropolitano y entronque oeste)
    # Franja Este: [-116.45, -115.874121] (El Hongo, La Rumorosa y descenso Mexicali)
    mid_lon = -116.450000

    hw_types = "motorway|trunk|primary|secondary|tertiary|residential|unclassified|service|living_street"

    q_west = f"""[out:json][timeout:90];
way["highway"~"{hw_types}"]({MIN_LAT},{MIN_LON},{MAX_LAT},{mid_lon});
out geom;
"""
    print("  -> Franja 1 (Poniente y Centro)...")
    data_west = query_overpass(q_west, timeout=90)

    q_east = f"""[out:json][timeout:90];
way["highway"~"{hw_types}"]({MIN_LAT},{mid_lon},{MAX_LAT},{MAX_LON});
out geom;
"""
    print("  -> Franja 2 (Oriente: El Hongo, La Rumorosa y descenso)...")
    data_east = query_overpass(q_east, timeout=90)

    # Fusionar por ID de elemento
    merged_elements = {}
    for el in data_west.get("elements", []):
        merged_elements[el["id"]] = el
    for el in data_east.get("elements", []):
        merged_elements[el["id"]] = el

    combined_data = {
        "version": 0.6,
        "generator": "TecateSimulatorRegionalBuilder",
        "elements": list(merged_elements.values())
    }

    with open(dest, "w", encoding="utf-8") as f:
        json.dump(combined_data, f)
    print(f"  -> Guardado en {dest} ({len(combined_data['elements'])} elementos consolidados).")

def main():
    os.makedirs(CACHE_DIR, exist_ok=True)
    t_start = time.time()
    print("="*70)
    print(f"DESCARGANDO CACHÉ OSM PARA TODO EL TERRENO ({MIN_LAT}, {MIN_LON}) -> ({MAX_LAT}, {MAX_LON})")
    print("="*70)

    download_railways()
    download_bridges()
    download_waterways()
    download_manzanas()
    download_roads()

    print("\n" + "="*70)
    print(f"TODAS LAS CAPAS DESCARGADAS CON ÉXITO EN {time.time()-t_start:.1f}s")
    print("="*70)

if __name__ == "__main__":
    main()
