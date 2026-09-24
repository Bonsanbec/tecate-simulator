"""
build_building_manifest_v3.py
Versión optimizada con cuadrícula espacial para el cruce punto-en-polígono.
Reduce complejidad de O(N*M) a O(N * k) donde k << M.

Ejecutar con Python estándar:
    python3 scratch/build_building_manifest_v3.py
"""

import json
import math
import re
from pathlib import Path
from collections import defaultdict

BASE = Path("/Users/hakkindavid/Documents/GitHub/tecate-simulator")
SCRATCH = BASE / "scratch"
CACHE = SCRATCH / "cache"

BLEND_OBJECTS_PATH = SCRATCH / "blend_objects_raw.json"
BLOCKS_CACHE_PATH  = CACHE / "blocks_cache.json"
FACADES_CACHE_PATH = CACHE / "facades_cache.json"
PANORAMAS_CACHE_PATH = CACHE / "panoramas_cache.json"
OUTPUT_PATH = SCRATCH / "manifest_edificios.json"

# ---------------------------------------------------------------------------
# Transformación de coordenadas
# ---------------------------------------------------------------------------
REF_LAT = 32.5182
REF_LON = -116.6272
LAT_PER_METER = 8.98e-6
LON_PER_METER = 1.068e-5

def blender_to_latlon(bx, by):
    return round(REF_LAT + by * LAT_PER_METER, 7), round(REF_LON + bx * LON_PER_METER, 7)

def parse_block_latlon(block_id: str):
    m = re.match(r"block_lat_([0-9.\-]+)_lon_([0-9.\-]+)", block_id)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None, None

# ---------------------------------------------------------------------------
# Geometría 2D
# ---------------------------------------------------------------------------

def point_in_polygon(px, py, polygon):
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

def polygon_bbox(polygon):
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return min(xs), max(xs), min(ys), max(ys)

def polygon_centroid(polygon):
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return sum(xs) / len(xs), sum(ys) / len(ys)

def dist2d(ax, ay, bx, by):
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)

# ---------------------------------------------------------------------------
# Cuadrícula espacial para búsqueda eficiente
# ---------------------------------------------------------------------------

GRID_CELL_SIZE = 200.0  # metros

class SpatialGrid:
    def __init__(self, cell_size=GRID_CELL_SIZE):
        self.cell_size = cell_size
        self.grid = defaultdict(list)

    def _cell(self, x, y):
        return (int(x // self.cell_size), int(y // self.cell_size))

    def insert_block(self, block_id, bx_min, bx_max, by_min, by_max, data):
        """Inserta el bloque en todas las celdas que toca su bbox."""
        cx0 = int(bx_min // self.cell_size)
        cx1 = int(bx_max // self.cell_size)
        cy0 = int(by_min // self.cell_size)
        cy1 = int(by_max // self.cell_size)
        for gx in range(cx0, cx1 + 1):
            for gy in range(cy0, cy1 + 1):
                self.grid[(gx, gy)].append((block_id, data))

    def candidates(self, px, py, radius_cells=1):
        """Devuelve candidatos en la celda del punto y vecinas."""
        cx, cy = int(px // self.cell_size), int(py // self.cell_size)
        seen = set()
        result = []
        for dx in range(-radius_cells, radius_cells + 1):
            for dy in range(-radius_cells, radius_cells + 1):
                for block_id, data in self.grid[(cx + dx, cy + dy)]:
                    if block_id not in seen:
                        seen.add(block_id)
                        result.append((block_id, data))
        return result


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------

print("=== Cargando archivos ===")

def load_json(path, label):
    mb = path.stat().st_size / 1024 / 1024
    print(f"  {label}: {mb:.1f} MB", flush=True)
    with open(path, encoding="utf-8") as f:
        return json.load(f)

blend_data     = load_json(BLEND_OBJECTS_PATH,  "blend_objects_raw.json")
blocks_data    = load_json(BLOCKS_CACHE_PATH,   "blocks_cache.json")
facades_data   = load_json(FACADES_CACHE_PATH,  "facades_cache.json")
panoramas_data = load_json(PANORAMAS_CACHE_PATH,"panoramas_cache.json")

print(f"\n  Objetos en .blend : {blend_data['total_objects']}")
print(f"  Bloques            : {len(blocks_data)}")
print(f"  Fachadas           : {len(facades_data)}")
print(f"  Panoramas          : {len(panoramas_data)}", flush=True)

# ---------------------------------------------------------------------------
# Índice de bloques + cuadrícula espacial
# ---------------------------------------------------------------------------

print("\n=== Construyendo índice espacial de bloques ===", flush=True)

blocks_index = {}
grid = SpatialGrid(cell_size=GRID_CELL_SIZE)

for block_id, bdata in blocks_data.items():
    polygon = bdata.get("polygon", [])
    if len(polygon) < 3:
        continue
    blat, blon = parse_block_latlon(block_id)
    bx_min, bx_max, by_min, by_max = polygon_bbox(polygon)
    poly_cx, poly_cy = polygon_centroid(polygon)
    bi = {
        "block_id": block_id,
        "lat": blat,
        "lon": blon,
        "poly_cx": poly_cx,
        "poly_cy": poly_cy,
        "bx_min": bx_min, "bx_max": bx_max,
        "by_min": by_min, "by_max": by_max,
        "area_sq_meters": bdata.get("area_sq_meters"),
        "is_external": bdata.get("is_external"),
        "height_meters": bdata.get("height_meters"),
        "roof_color": bdata.get("roof_color"),
        "polygon": polygon,
    }
    blocks_index[block_id] = bi
    grid.insert_block(block_id, bx_min, bx_max, by_min, by_max, bi)

print(f"  Bloques indexados: {len(blocks_index)}", flush=True)

# ---------------------------------------------------------------------------
# Índice de fachadas por block_id
# ---------------------------------------------------------------------------

print("\n=== Construyendo índice de fachadas ===", flush=True)

facades_by_block = defaultdict(list)
for facade_id, fdata in facades_data.items():
    m = re.match(r"(block_lat_[0-9.\-]+_lon_[0-9.\-]+)_facade_(\d+)", facade_id)
    if not m:
        continue
    block_id = m.group(1)
    facades_by_block[block_id].append({
        "facade_id": facade_id,
        "facade_n": int(m.group(2)),
        "pano_id": fdata.get("pano_id"),
        "heading": fdata.get("heading"),
    })

print(f"  Bloques con fachadas: {len(facades_by_block)}", flush=True)

# ---------------------------------------------------------------------------
# Helpers de panoramas
# ---------------------------------------------------------------------------

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
# Búsqueda de bloque para un punto (con cuadrícula)
# ---------------------------------------------------------------------------

def find_block_for_point(cx, cy):
    candidates = grid.candidates(cx, cy, radius_cells=1)

    # 1) Point-in-polygon
    inside = []
    for block_id, bi in candidates:
        # Filtro rápido por bbox
        if not (bi["bx_min"] <= cx <= bi["bx_max"] and bi["by_min"] <= cy <= bi["by_max"]):
            continue
        if point_in_polygon(cx, cy, bi["polygon"]):
            d = dist2d(cx, cy, bi["poly_cx"], bi["poly_cy"])
            inside.append((d, block_id, bi))

    if inside:
        inside.sort()
        _, block_id, bi = inside[0]
        return block_id, bi, "point_in_polygon"

    # 2) Fallback: centroide más cercano (ampliar radio de búsqueda si hace falta)
    all_cands = grid.candidates(cx, cy, radius_cells=3)
    best_dist = float("inf")
    best_id = None
    best_bi = None
    for block_id, bi in all_cands:
        d = dist2d(cx, cy, bi["poly_cx"], bi["poly_cy"])
        if d < best_dist:
            best_dist = d
            best_id = block_id
            best_bi = bi

    if best_id and best_dist < 1000:
        return best_id, best_bi, "nearest_centroid"
    return None, {}, "none"

# ---------------------------------------------------------------------------
# Generar manifiesto
# ---------------------------------------------------------------------------

print("\n=== Generando manifiesto ===", flush=True)

objects = blend_data["objects"]
meshes = [o for o in objects if o["type"] == "MESH" and o.get("vertex_count", 0) > 0]
print(f"  Mallas con geometría: {len(meshes)}", flush=True)

manifest_entries = []
stats = {"point_in_polygon": 0, "nearest_centroid": 0, "none": 0}

for idx, obj in enumerate(meshes):
    if idx % 200 == 0:
        print(f"  [{idx}/{len(meshes)}]...", flush=True)

    name = obj["name"]
    bbox = obj.get("bbox_blender")
    if not bbox:
        continue

    cx, cy, cz = bbox["cx"], bbox["cy"], bbox["cz"]

    block_id, bi, method = find_block_for_point(cx, cy)
    stats[method] = stats.get(method, 0) + 1

    # Fachadas del bloque
    facades_list = facades_by_block.get(block_id, []) if block_id else []
    road_names = []
    facades_enriched = []
    for facade in sorted(facades_list, key=lambda f: f["facade_n"]):
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

    est_lat, est_lon = blender_to_latlon(cx, cy)

    # Propiedades OSM embebidas en el objeto
    cprops = obj.get("custom_properties", {})
    osm_chain = cprops.get("osm_chain", "")
    # Extraer Node ID del chain: "Node_XXXXX -> Building Nombre"
    osm_node_id = None
    m_chain = re.match(r"Node_(\d+)", osm_chain)
    if m_chain:
        osm_node_id = int(m_chain.group(1))

    entry = {
        "name": name,
        "osm_node_id": osm_node_id,
        "osm_semantic_name": cprops.get("osm_semantic_name", ""),
        "osm_category": cprops.get("osm_category", ""),
        "osm_chain": osm_chain,
        "collections": obj.get("collections", []),
        "parent": obj.get("parent"),
        "materials": [m for m in (obj.get("materials") or []) if m],
        "vertex_count": obj["vertex_count"],
        "face_count": obj["face_count"],
        "blender_bbox": {
            "x": [round(bbox["x_min"], 3), round(bbox["x_max"], 3)],
            "y": [round(bbox["y_min"], 3), round(bbox["y_max"], 3)],
            "z": [round(bbox["z_min"], 3), round(bbox["z_max"], 3)],
            "centroid": [round(cx, 3), round(cy, 3), round(cz, 3)],
            "dimensions_m": {
                "width_x": round(bbox["width_x"], 2),
                "depth_y": round(bbox["depth_y"], 2),
                "height_z": round(bbox["height_z"], 2),
            },
        },
        "godot_centroid": obj.get("godot_centroid"),
        "geoposition": {
            "lat": est_lat,
            "lon": est_lon,
            "source": "blender_metric_projection_estimate",
        },
        "block_id": block_id,
        "block_match_method": method,
        "block_lat": bi.get("lat"),
        "block_lon": bi.get("lon"),
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

# Ordenar por block_id → nombre
manifest_entries.sort(key=lambda e: (e["block_id"] or "zzzz", e["name"]))

# ---------------------------------------------------------------------------
# Escribir salida
# ---------------------------------------------------------------------------

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
        },
        "cache_files_used": {
            "blocks_cache": "blocks_cache.json",
            "facades_cache": "facades_cache.json",
            "panoramas_cache": "panoramas_cache.json",
        },
        "blocks_indexed": len(blocks_index),
        "facades_indexed": sum(len(v) for v in facades_by_block.values()),
        "panoramas_available": len(panoramas_data),
    },
    "entries": manifest_entries,
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f"\n✅ Manifiesto generado: {OUTPUT_PATH}")
print(f"   Total entradas                : {len(manifest_entries)}")
print(f"   Point-in-polygon exacto       : {stats.get('point_in_polygon',0)}")
print(f"   Nearest centroid (fallback)   : {stats.get('nearest_centroid',0)}")
print(f"   Sin bloque asignado           : {stats.get('none',0)}")

with_roads = sum(1 for e in manifest_entries if e["facade_road_names"])
print(f"   Con road_names de fachadas    : {with_roads}")

from collections import Counter
all_roads = []
for e in manifest_entries:
    all_roads.extend(e["facade_road_names"])
road_counts = Counter(all_roads).most_common(25)
print("\n  Top calles en el manifiesto:")
for road, count in road_counts:
    if road:
        print(f"    {road}: {count}")
