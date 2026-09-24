"""
build_building_manifest.py
Cruza blend_objects_raw.json con blocks_cache.json, facades_cache.json
y panoramas_cache.json para generar el manifiesto consolidado.

Estrategia:
  - El .blend usa coordenadas métricas de osm2world (proyección de Mercator local).
  - Los cachés usan coordenadas geográficas WGS-84 (lat/lon).
  - El origen de osm2world en este proyecto está anclado al centroide de Tecate.
  - Se usa la transformación conocida del proyecto para convertir de Blender a lat/lon.
  - Cruce por cercanía geográfica con manzanas (blocks_cache.json).
  - Cruce por nombres de calle para fachadas.

Ejecutar con Python estándar (no Blender):
    python3 scratch/build_building_manifest.py
"""

import json
import os
import math
import re
from pathlib import Path

BASE = Path("/Users/hakkindavid/Documents/GitHub/tecate-simulator")
SCRATCH = BASE / "scratch"
CACHE = SCRATCH / "cache"

BLEND_OBJECTS_PATH = SCRATCH / "blend_objects_raw.json"
BLOCKS_CACHE_PATH = CACHE / "blocks_cache.json"
FACADES_CACHE_PATH = CACHE / "facades_cache.json"
PANORAMAS_CACHE_PATH = CACHE / "panoramas_cache.json"
OUTPUT_PATH = SCRATCH / "manifest_edificios.json"

# ---------------------------------------------------------------------------
# 1. Transformación de coordenadas Blender → WGS-84
# ---------------------------------------------------------------------------
# Del proyecto: el origen de osm2world está anclado en las coordenadas del
# parque Hidalgo de Tecate. La transformación aprendida del proyecto:
#   lat = REF_LAT + (blender_y * SCALE_Y)   [Y de Blender → Norte]
#   lon = REF_LON + (blender_x * SCALE_X)   [X de Blender → Este]
# Referencia validada en inspect_osm2world.py y blender_script.py.

# Coordenadas de referencia del parque Hidalgo (centro del proyecto):
REF_LAT = 32.5182    # °N
REF_LON = -116.6272  # °W

# Escala métrica: 1 unidad Blender ≈ 1 metro en la proyección local
# Factor de conversión: 1 m ≈ 8.98e-6 ° lat, ≈ 1.07e-5 ° lon (a lat ~32°)
LAT_PER_METER = 8.98e-6    # °/m
LON_PER_METER = 1.068e-5   # °/m (ajustado por cos(lat))


def blender_to_latlon(bx, by):
    """Convierte centroide Blender (x, y) a (lat, lon) WGS-84 aproximado."""
    lat = REF_LAT + by * LAT_PER_METER
    lon = REF_LON + bx * LON_PER_METER
    return round(lat, 7), round(lon, 7)


def haversine_m(lat1, lon1, lat2, lon2):
    """Distancia en metros entre dos puntos WGS-84."""
    R = 6_371_000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# 2. Carga de datos
# ---------------------------------------------------------------------------

def load_json(path):
    print(f"  Cargando {path.name} ({path.stat().st_size // 1024 // 1024} MB)...")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


print("=== Cargando archivos ===")
blend_data = load_json(BLEND_OBJECTS_PATH)
blocks_data = load_json(BLOCKS_CACHE_PATH)
facades_data = load_json(FACADES_CACHE_PATH)
panoramas_data = load_json(PANORAMAS_CACHE_PATH)

print(f"  Objetos en .blend: {blend_data['total_objects']}")
print(f"  Tipo histogram: {blend_data['type_histogram']}")

# ---------------------------------------------------------------------------
# 3. Preparar índice de manzanas (blocks_cache)
# ---------------------------------------------------------------------------

print("\n=== Analizando estructura de blocks_cache.json ===")

# Descubrir estructura
sample_keys = list(blocks_data.keys())[:5]
print(f"  Claves raíz (muestra): {sample_keys}")

blocks_index = {}  # block_id → {lat, lon, streets, polygon, ...}

if isinstance(blocks_data, dict):
    for block_id, block_info in blocks_data.items():
        if isinstance(block_info, dict):
            # Extraer centroide del bloque
            lat = block_info.get("lat") or block_info.get("centroid_lat") or block_info.get("center_lat")
            lon = block_info.get("lon") or block_info.get("centroid_lon") or block_info.get("center_lon")

            # Buscar polígono o bounds
            polygon = block_info.get("polygon") or block_info.get("geometry") or block_info.get("bounds")
            streets = block_info.get("streets") or block_info.get("calles") or block_info.get("ways") or []
            name = block_info.get("name") or block_info.get("nombre") or ""

            blocks_index[block_id] = {
                "block_id": block_id,
                "lat": lat,
                "lon": lon,
                "name": name,
                "streets": streets,
                "polygon": polygon,
                "raw_keys": list(block_info.keys())[:10],
            }
elif isinstance(blocks_data, list):
    for block_info in blocks_data:
        block_id = str(block_info.get("id") or block_info.get("block_id") or block_info.get("osm_id", ""))
        lat = block_info.get("lat") or block_info.get("centroid_lat")
        lon = block_info.get("lon") or block_info.get("centroid_lon")
        streets = block_info.get("streets") or block_info.get("calles") or []
        blocks_index[block_id] = {
            "block_id": block_id,
            "lat": lat,
            "lon": lon,
            "streets": streets,
            "raw_keys": list(block_info.keys())[:10],
        }

print(f"  Manzanas indexadas: {len(blocks_index)}")
if blocks_index:
    sample_block = next(iter(blocks_index.values()))
    print(f"  Muestra de manzana: {sample_block}")


# ---------------------------------------------------------------------------
# 4. Preparar índice de fachadas (facades_cache)
# ---------------------------------------------------------------------------

print("\n=== Analizando estructura de facades_cache.json ===")

facades_sample_keys = list(facades_data.keys())[:5] if isinstance(facades_data, dict) else []
print(f"  Claves raíz (muestra): {facades_sample_keys}")

facades_index = {}  # Indexar por alguna coordenada o ID

if isinstance(facades_data, dict):
    for key, value in facades_data.items():
        if isinstance(value, dict):
            lat = value.get("lat") or value.get("latitude")
            lon = value.get("lon") or value.get("longitude")
            street = value.get("street") or value.get("calle") or value.get("way_name") or ""
            block_id = str(value.get("block_id") or value.get("manzana_id") or "")
            facades_index[key] = {
                "facade_id": key,
                "lat": lat,
                "lon": lon,
                "street": street,
                "block_id": block_id,
                "raw_keys": list(value.keys())[:10],
            }

print(f"  Fachadas indexadas: {len(facades_index)}")
if facades_index:
    sample_facade = next(iter(facades_index.values()))
    print(f"  Muestra de fachada: {sample_facade}")


# ---------------------------------------------------------------------------
# 5. Preparar índice de panoramas
# ---------------------------------------------------------------------------

print("\n=== Analizando estructura de panoramas_cache.json ===")

pano_sample_keys = list(panoramas_data.keys())[:3] if isinstance(panoramas_data, dict) else []
print(f"  Claves raíz (muestra): {pano_sample_keys}")

panos_index = []  # Lista de panoramas con lat/lon

if isinstance(panoramas_data, dict):
    for pano_id, pano_info in panoramas_data.items():
        if isinstance(pano_info, dict):
            lat = pano_info.get("lat") or pano_info.get("latitude")
            lon = pano_info.get("lon") or pano_info.get("longitude")
            if lat and lon:
                panos_index.append({
                    "pano_id": pano_id,
                    "lat": lat,
                    "lon": lon,
                    "yaw": pano_info.get("yaw") or pano_info.get("heading"),
                    "filename": pano_info.get("filename") or pano_info.get("file"),
                    "raw_keys": list(pano_info.keys())[:8],
                })
elif isinstance(panoramas_data, list):
    for p in panoramas_data:
        lat = p.get("lat") or p.get("latitude")
        lon = p.get("lon") or p.get("longitude")
        if lat and lon:
            panos_index.append({
                "pano_id": str(p.get("id") or p.get("pano_id", "")),
                "lat": lat,
                "lon": lon,
                "yaw": p.get("yaw") or p.get("heading"),
                "filename": p.get("filename") or p.get("file"),
            })

print(f"  Panoramas con coords: {len(panos_index)}")


# ---------------------------------------------------------------------------
# 6. Función para hallar el bloque más cercano
# ---------------------------------------------------------------------------

def find_nearest_block(lat, lon, max_dist_m=200):
    """Encuentra el bloque más cercano al punto dado."""
    best_id = None
    best_dist = float("inf")
    for block_id, block in blocks_index.items():
        blat = block.get("lat")
        blon = block.get("lon")
        if blat is None or blon is None:
            continue
        d = haversine_m(lat, lon, blat, blon)
        if d < best_dist:
            best_dist = d
            best_id = block_id
    if best_dist <= max_dist_m:
        return best_id, round(best_dist, 1)
    return None, None


def find_nearby_facades(lat, lon, max_dist_m=50):
    """Encuentra fachadas cercanas."""
    results = []
    for fid, facade in facades_index.items():
        flat = facade.get("lat")
        flon = facade.get("lon")
        if flat is None or flon is None:
            continue
        d = haversine_m(lat, lon, flat, flon)
        if d <= max_dist_m:
            results.append({
                "facade_id": fid,
                "street": facade.get("street", ""),
                "block_id": facade.get("block_id", ""),
                "dist_m": round(d, 1),
            })
    results.sort(key=lambda x: x["dist_m"])
    return results[:5]


def find_nearby_panoramas(lat, lon, max_dist_m=80):
    """Encuentra panoramas cercanos."""
    results = []
    for p in panos_index:
        d = haversine_m(lat, lon, p["lat"], p["lon"])
        if d <= max_dist_m:
            results.append({
                "pano_id": p["pano_id"],
                "filename": p.get("filename"),
                "yaw": p.get("yaw"),
                "dist_m": round(d, 1),
            })
    results.sort(key=lambda x: x["dist_m"])
    return results[:4]


# ---------------------------------------------------------------------------
# 7. Generar manifiesto consolidado
# ---------------------------------------------------------------------------

print("\n=== Generando manifiesto de edificios ===")

objects = blend_data["objects"]

# Filtrar solo MESHes con vértices (excluir planos sin geometría)
meshes = [o for o in objects if o["type"] == "MESH" and o["vertex_count"] > 0]
print(f"  Mallas con geometría: {len(meshes)}")

manifest_entries = []

for obj in meshes:
    name = obj["name"]
    bbox = obj.get("bbox_blender")
    if not bbox:
        continue

    cx = bbox["cx"]
    cy = bbox["cy"]
    cz = bbox["cz"]

    # Convertir centroide a lat/lon
    lat, lon = blender_to_latlon(cx, cy)

    # Cruce con manzanas
    block_id, block_dist_m = find_nearest_block(lat, lon)
    block_info = blocks_index.get(block_id, {}) if block_id else {}

    # Cruce con fachadas
    nearby_facades = find_nearby_facades(lat, lon)

    # Extraer calles de fachadas
    streets_on_facade = list({f["street"] for f in nearby_facades if f["street"]})

    # Cruce con panoramas
    nearby_panos = find_nearby_panoramas(lat, lon)

    entry = {
        "name": name,
        "collections": obj.get("collections", []),
        "parent": obj.get("parent"),
        "materials": obj.get("materials", []),
        "custom_properties": obj.get("custom_properties", {}),
        "vertex_count": obj["vertex_count"],
        "face_count": obj["face_count"],
        "blender_bbox": {
            "x": [round(bbox["x_min"], 3), round(bbox["x_max"], 3)],
            "y": [round(bbox["y_min"], 3), round(bbox["y_max"], 3)],
            "z": [round(bbox["z_min"], 3), round(bbox["z_max"], 3)],
            "dimensions_m": {
                "width_x": round(bbox["width_x"], 2),
                "depth_y": round(bbox["depth_y"], 2),
                "height_z": round(bbox["height_z"], 2),
            }
        },
        "godot_centroid": obj.get("godot_centroid"),
        "geoposition": {
            "lat": lat,
            "lon": lon,
            "method": "osm2world_projection_estimate",
        },
        "block_id": block_id,
        "block_dist_m": block_dist_m,
        "block_name": block_info.get("name", ""),
        "block_streets": block_info.get("streets", []),
        "facade_streets": streets_on_facade,
        "nearby_facades": nearby_facades,
        "nearby_panoramas": nearby_panos,
        "is_building_hint": obj.get("is_building_hint", False),
        "visible": obj.get("visible"),
        "hide_viewport": obj.get("hide_viewport"),
        "hide_render": obj.get("hide_render"),
    }

    manifest_entries.append(entry)

# Ordenar: primero edificios, luego por nombre
manifest_entries.sort(key=lambda e: (0 if e["is_building_hint"] else 1, e["name"]))

manifest = {
    "meta": {
        "blend_file": "blender_assets/osm2world_adjusted.blend",
        "total_meshes_in_blend": len(meshes),
        "total_entries_in_manifest": len(manifest_entries),
        "coordinate_reference": {
            "ref_lat": REF_LAT,
            "ref_lon": REF_LON,
            "description": "Origen anclado al Parque Miguel Hidalgo, Tecate, B.C.",
            "projection": "osm2world local Mercator, 1 unidad Blender ≈ 1 metro",
        },
        "cache_files_used": {
            "blocks_cache": str(BLOCKS_CACHE_PATH),
            "facades_cache": str(FACADES_CACHE_PATH),
            "panoramas_cache": str(PANORAMAS_CACHE_PATH),
        },
        "blocks_indexed": len(blocks_index),
        "facades_indexed": len(facades_index),
        "panoramas_indexed": len(panos_index),
    },
    "entries": manifest_entries,
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f"\n✅ Manifiesto generado: {OUTPUT_PATH}")
print(f"   Total entradas: {len(manifest_entries)}")
print(f"   Con block_id asignado: {sum(1 for e in manifest_entries if e['block_id'])}")
print(f"   Con fachadas cruzadas: {sum(1 for e in manifest_entries if e['nearby_facades'])}")
print(f"   Con panoramas cercanos: {sum(1 for e in manifest_entries if e['nearby_panoramas'])}")
