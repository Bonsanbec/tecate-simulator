"""
build_building_manifest_v2.py
Cruza blend_objects_raw.json con blocks_cache.json, facades_cache.json
y panoramas_cache.json usando las estructuras reales descubiertas.

Estructura real de los cachés:
  blocks_cache.json:
    clave: "block_lat_{lat}_lon_{lon}"
    valor: { polygon: [[x,y],...], area_sq_meters, is_external, height_meters, roof_color }
    → polígono en coordenadas métricas osm2world (mismo espacio que .blend)

  facades_cache.json:
    clave: "block_lat_{lat}_lon_{lon}_facade_{N}"
    valor: { pano_id, heading, captured_heading, resolution }
    → no tiene coords propias, se vincula al bloque por prefijo de clave

  panoramas_cache.json:
    clave: pano_id (string)
    valor: { latitude, longitude, altitude, date, pitch, roll,
             projection_yaw, pano_yaw, road_name, adjacent_links, timeline }

Estrategia de cruce:
  1. Para cada malla Blender → centroide (cx, cy) en coords métricas.
  2. Test punto-en-polígono con todos los polígonos de blocks_cache.
     Si no está dentro de ninguno, asignar el más cercano por distancia al centroide del polígono.
  3. Extraer lat/lon del block_id (codificado en la clave).
  4. Vincular facades del mismo bloque.
  5. Para cada facade, buscar el panorama en panoramas_cache y extraer road_name.
  6. Convertir centroide Blender → lat/lon usando factor de escala del proyecto.
"""

import json
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
# 0. Transformación Blender ↔ lat/lon
# ---------------------------------------------------------------------------
# El proyecto fija el origen de osm2world en el centroide de Tecate.
# Las coordenadas del bloque en blocks_cache están en metros osm2world,
# cuyo origen (0,0) corresponde aproximadamente a:
REF_LAT = 32.5182     # °N — Parque Miguel Hidalgo
REF_LON = -116.6272   # °W
# Factores de conversión validados para lat ~32° N:
LAT_PER_METER = 8.98e-6
LON_PER_METER = 1.068e-5


def blender_to_latlon(bx, by):
    lat = REF_LAT + by * LAT_PER_METER
    lon = REF_LON + bx * LON_PER_METER
    return round(lat, 7), round(lon, 7)


def parse_block_latlon(block_id: str):
    """Extrae (lat, lon) del string 'block_lat_X_lon_Y'."""
    m = re.match(r"block_lat_([0-9.\-]+)_lon_([0-9.\-]+)", block_id)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None, None


# ---------------------------------------------------------------------------
# 1. Test punto-en-polígono (ray casting)
# ---------------------------------------------------------------------------

def point_in_polygon(px, py, polygon):
    """Devuelve True si (px,py) está dentro del polígono 2D."""
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def polygon_centroid(polygon):
    """Centroide simple del polígono."""
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def dist2d(ax, ay, bx, by):
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


# ---------------------------------------------------------------------------
# 2. Carga de datos
# ---------------------------------------------------------------------------

print("=== Cargando archivos ===")

def load_json(path, label):
    mb = path.stat().st_size / 1024 / 1024
    print(f"  {label}: {mb:.1f} MB")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

blend_data    = load_json(BLEND_OBJECTS_PATH, "blend_objects_raw.json")
blocks_data   = load_json(BLOCKS_CACHE_PATH,  "blocks_cache.json")
facades_data  = load_json(FACADES_CACHE_PATH, "facades_cache.json")
panoramas_data= load_json(PANORAMAS_CACHE_PATH,"panoramas_cache.json")

print(f"\n  Objetos en .blend : {blend_data['total_objects']}")
print(f"  Bloques            : {len(blocks_data)}")
print(f"  Fachadas           : {len(facades_data)}")
print(f"  Panoramas          : {len(panoramas_data)}")

# ---------------------------------------------------------------------------
# 3. Índice de bloques: centroide del polígono métrico + lat/lon del ID
# ---------------------------------------------------------------------------

print("\n=== Construyendo índice de bloques ===")

blocks_index = {}  # block_id → {lat, lon, poly_cx, poly_cy, polygon, area, ...}

for block_id, bdata in blocks_data.items():
    polygon = bdata.get("polygon", [])
    if len(polygon) < 3:
        continue
    blat, blon = parse_block_latlon(block_id)
    poly_cx, poly_cy = polygon_centroid(polygon)
    blocks_index[block_id] = {
        "block_id": block_id,
        "lat": blat,
        "lon": blon,
        "poly_cx": poly_cx,
        "poly_cy": poly_cy,
        "area_sq_meters": bdata.get("area_sq_meters"),
        "is_external": bdata.get("is_external"),
        "height_meters": bdata.get("height_meters"),
        "roof_color": bdata.get("roof_color"),
        "polygon": polygon,
    }

print(f"  Bloques indexados: {len(blocks_index)}")

# ---------------------------------------------------------------------------
# 4. Índice de fachadas: agrupar por block_id y guardar pano_ids
# ---------------------------------------------------------------------------

print("\n=== Construyendo índice de fachadas ===")

facades_by_block = {}  # block_id → [{facade_id, pano_id, heading, ...}]

for facade_id, fdata in facades_data.items():
    # Extraer block_id quitando el sufijo "_facade_N"
    m = re.match(r"(block_lat_[0-9.\-]+_lon_[0-9.\-]+)_facade_(\d+)", facade_id)
    if not m:
        continue
    block_id = m.group(1)
    facade_n = int(m.group(2))
    if block_id not in facades_by_block:
        facades_by_block[block_id] = []
    facades_by_block[block_id].append({
        "facade_id": facade_id,
        "facade_n": facade_n,
        "pano_id": fdata.get("pano_id"),
        "heading": fdata.get("heading"),
        "captured_heading": fdata.get("captured_heading"),
    })

print(f"  Bloques con fachadas: {len(facades_by_block)}")

# ---------------------------------------------------------------------------
# 5. Resolver road_name desde panoramas
# ---------------------------------------------------------------------------

def get_road_name(pano_id):
    if not pano_id:
        return ""
    p = panoramas_data.get(pano_id, {})
    return p.get("road_name") or ""


def get_pano_info(pano_id):
    if not pano_id:
        return {}
    p = panoramas_data.get(pano_id, {})
    return {
        "pano_id": pano_id,
        "latitude": p.get("latitude"),
        "longitude": p.get("longitude"),
        "date": p.get("date"),
        "road_name": p.get("road_name") or "",
    }


# ---------------------------------------------------------------------------
# 6. Función principal de cruce
# ---------------------------------------------------------------------------

def find_block_for_point(cx, cy):
    """
    Busca el bloque que contiene el punto (cx,cy) en coordenadas métricas.
    1) Prueba point_in_polygon exacto.
    2) Si no hay coincidencia, usa el bloque cuyo centroide de polígono
       esté más cerca (fallback).
    Retorna (block_id, method, dist_m)
    """
    # Paso 1: point-in-polygon exacto
    inside_candidates = []
    for block_id, bi in blocks_index.items():
        if point_in_polygon(cx, cy, bi["polygon"]):
            # Calcular distancia al centroide del polígono para desempate
            d = dist2d(cx, cy, bi["poly_cx"], bi["poly_cy"])
            inside_candidates.append((d, block_id))

    if inside_candidates:
        inside_candidates.sort()
        return inside_candidates[0][1], "point_in_polygon", round(inside_candidates[0][0], 1)

    # Paso 2: fallback por centroide más cercano
    best_dist = float("inf")
    best_id = None
    for block_id, bi in blocks_index.items():
        d = dist2d(cx, cy, bi["poly_cx"], bi["poly_cy"])
        if d < best_dist:
            best_dist = d
            best_id = block_id

    if best_id and best_dist < 500:
        return best_id, "nearest_centroid", round(best_dist, 1)
    return None, "none", None


# ---------------------------------------------------------------------------
# 7. Generar manifiesto
# ---------------------------------------------------------------------------

print("\n=== Generando manifiesto ===")

objects = blend_data["objects"]
meshes = [o for o in objects if o["type"] == "MESH" and o.get("vertex_count", 0) > 0]
print(f"  Mallas con geometría: {len(meshes)}")

manifest_entries = []
stats = {"point_in_polygon": 0, "nearest_centroid": 0, "none": 0}

for obj in meshes:
    name = obj["name"]
    bbox = obj.get("bbox_blender")
    if not bbox:
        continue

    cx = bbox["cx"]
    cy = bbox["cy"]

    # Cruce con bloque
    block_id, method, dist_m = find_block_for_point(cx, cy)
    stats[method] = stats.get(method, 0) + 1

    # Info del bloque
    bi = blocks_index.get(block_id, {}) if block_id else {}
    block_lat = bi.get("lat")
    block_lon = bi.get("lon")

    # Fachadas del bloque
    facades_list = facades_by_block.get(block_id, []) if block_id else []

    # Extraer road_names únicos de los panoramas de las fachadas
    road_names = []
    facades_enriched = []
    for facade in facades_list:
        pano_info = get_pano_info(facade.get("pano_id"))
        rn = pano_info.get("road_name", "")
        if rn and rn not in road_names:
            road_names.append(rn)
        facades_enriched.append({
            "facade_id": facade["facade_id"],
            "facade_n": facade["facade_n"],
            "pano_id": facade.get("pano_id"),
            "heading_deg": round(facade["heading"], 2) if facade.get("heading") else None,
            "road_name": rn,
            "pano_date": pano_info.get("date"),
            "pano_lat": pano_info.get("latitude"),
            "pano_lon": pano_info.get("longitude"),
        })

    # Geoposición del centroide de la malla (estimada desde coords Blender)
    est_lat, est_lon = blender_to_latlon(cx, cy)

    entry = {
        "name": name,
        "collections": obj.get("collections", []),
        "parent": obj.get("parent"),
        "materials": [m for m in (obj.get("materials") or []) if m],
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
            },
            "centroid_blender": [round(cx, 3), round(cy, 3), round(bbox["cz"], 3)],
        },
        "godot_centroid": obj.get("godot_centroid"),
        "geoposition_estimated": {
            "lat": est_lat,
            "lon": est_lon,
            "note": "Estimada desde proyección métrica osm2world; validar contra block_id",
        },
        "block_id": block_id,
        "block_match_method": method,
        "block_dist_to_centroid_m": dist_m,
        "block_lat": block_lat,
        "block_lon": block_lon,
        "block_area_sq_m": bi.get("area_sq_meters"),
        "block_height_m": bi.get("height_meters"),
        "block_is_external": bi.get("is_external"),
        "block_roof_color": bi.get("roof_color"),
        "facade_count": len(facades_enriched),
        "facade_road_names": road_names,
        "facades": facades_enriched,
        "visible": obj.get("visible"),
        "hide_viewport": obj.get("hide_viewport"),
        "hide_render": obj.get("hide_render"),
    }

    manifest_entries.append(entry)

# Ordenar: primero por block_id, luego por nombre
manifest_entries.sort(key=lambda e: (e["block_id"] or "zzzz", e["name"]))

manifest = {
    "meta": {
        "blend_file": "blender_assets/osm2world_adjusted.blend",
        "total_meshes_in_blend": len(meshes),
        "total_entries_in_manifest": len(manifest_entries),
        "match_stats": stats,
        "coordinate_reference": {
            "system": "osm2world local metric projection",
            "ref_lat": REF_LAT,
            "ref_lon": REF_LON,
            "description": "Origen ≈ Parque Miguel Hidalgo, Tecate, B.C., México",
            "note": "1 unidad Blender = 1 metro. Coordenadas Y=Norte, X=Este.",
        },
        "cache_files_used": {
            "blocks_cache": str(BLOCKS_CACHE_PATH.name),
            "facades_cache": str(FACADES_CACHE_PATH.name),
            "panoramas_cache": str(PANORAMAS_CACHE_PATH.name),
        },
    },
    "entries": manifest_entries,
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f"\n✅ Manifiesto generado: {OUTPUT_PATH}")
print(f"   Total entradas                : {len(manifest_entries)}")
print(f"   Con block_id (point-in-poly)  : {stats.get('point_in_polygon', 0)}")
print(f"   Con block_id (nearest)        : {stats.get('nearest_centroid', 0)}")
print(f"   Sin block_id                  : {stats.get('none', 0)}")

# Estadísticas de calles encontradas
with_roads = sum(1 for e in manifest_entries if e["facade_road_names"])
print(f"   Con road_names de fachadas    : {with_roads}")

# Top 20 nombres de calles
from collections import Counter
all_roads = []
for e in manifest_entries:
    all_roads.extend(e["facade_road_names"])
road_counts = Counter(all_roads).most_common(20)
print("\n  Top calles en el manifiesto:")
for road, count in road_counts:
    if road:
        print(f"    {road}: {count} mallas")
