"""
apply_manifest_update.py
========================
Actualiza blender_assets/manifest_edificios.json al nuevo modelo geodésico universal (v2.0.0).

Aplica:
1. Origen WGS84 exacto: lat0 = 32.5732357, lon0 = -116.6265288.
2. Factores de escala métricos invariables: METERS_PER_DEG_LAT = 111323.6051, METERS_PER_DEG_LON = 93810.7490.
3. Coordenadas Godot (gx, gy, gz) y Blender (bx, by, bz) con idempotencia matemática.
4. Validación topológica analítica de pertenencia a manzana (is_inside_polygon).
5. Cálculo de normal exterior de fachada, heading geográfico y cardinal.
6. Generación de Transform3D analítico listo para Godot 4 (.tscn).
"""

import json
import time
from pathlib import Path
from scripts.spatial_utils import (
    SpatialContext,
    ORIGIN_LAT, ORIGIN_LON,
    METERS_PER_DEG_LAT, METERS_PER_DEG_LON,
    DEG_LAT_PER_METER, DEG_LON_PER_METER,
    normal_to_godot_transform3d,
    point_in_polygon, distance_point_to_edge, Vec2
)

BASE = Path("/Users/hakkindavid/Documents/GitHub/tecate-simulator")
MANIFEST_PATH = BASE / "blender_assets" / "manifest_edificios.json"
BACKUP_PATH = BASE / "blender_assets" / "manifest_edificios.json.bak"

print("Cargando contexto espacial...")
t0 = time.time()
ctx = SpatialContext.load()
print(f"Contexto cargado en {time.time() - t0:.2f} s")

print(f"Leyendo manifiesto original desde {MANIFEST_PATH}...")
with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    manifest = json.load(f)

entries = manifest["entries"]
total_entries = len(entries)
print(f"Total entradas a actualizar: {total_entries}")

# Backup previo
if not BACKUP_PATH.exists():
    print(f"Creando respaldo en {BACKUP_PATH}...")
    with open(BACKUP_PATH, "w", encoding="utf-8") as f_bak:
        json.dump(manifest, f_bak)

# Contadores estadísticos
pip_count = 0
outside_count = 0
no_block_count = 0

t_start = time.time()
for idx, e in enumerate(entries):
    # Coordenadas centroid Blender
    bbox = e.get("blender_bbox", {})
    c = bbox.get("centroid", [0.0, 0.0, 400.0])
    bx = float(c[0])
    by = float(c[1])
    bz = float(c[2])

    # 1. Coordenadas Godot exactas (glTF Y-up)
    gx = round(bx, 4)
    gy = round(bz, 4)
    gz = round(-by, 4)
    e["godot_centroid"] = [gx, gy, gz]

    # 2. Geoposición WGS84 precisa
    new_lat = round(ORIGIN_LAT + by * DEG_LAT_PER_METER, 7)
    new_lon = round(ORIGIN_LON + bx * DEG_LON_PER_METER, 7)
    e["geoposition"] = {
        "lat": new_lat,
        "lon": new_lon,
        "altitude_msnm": round(bz, 2),
        "source": "wgs84_universal_municipal_model"
    }

    # 3. Validación topológica sobre el polígono de la manzana
    pos = Vec2(gx, gz)
    block_id = e.get("block_id")
    is_inside = False
    primary_edge = None

    if block_id and block_id in ctx._godot_polygons:
        poly = ctx._godot_polygons[block_id]
        is_inside = point_in_polygon(pos, poly)
        edges = ctx.get_block_edges(block_id)
        if edges:
            primary_edge = min(edges, key=lambda edge: distance_point_to_edge(pos, edge)[0])

    if not is_inside and not block_id:
        # Intentar localizar manzana en cuadrícula
        found_bid = ctx.find_block_at_point(pos)
        if found_bid:
            block_id = found_bid
            e["block_id"] = found_bid
            e["block_match_method"] = "point_in_polygon"
            is_inside = True
            edges = ctx.get_block_edges(found_bid)
            if edges:
                primary_edge = min(edges, key=lambda edge: distance_point_to_edge(pos, edge)[0])

    e["is_inside_polygon"] = is_inside

    if is_inside:
        pip_count += 1
    elif block_id:
        outside_count += 1
    else:
        no_block_count += 1

    # 4. Cálculo de normal exterior, heading y Transform3D
    if primary_edge:
        e["primary_facade_heading_deg"] = round(primary_edge.heading_deg, 2)
        e["primary_facade_cardinal"] = primary_edge.cardinal
        e["transform3d_tscn"] = normal_to_godot_transform3d(primary_edge.outward_normal, gx, gy, gz)
    else:
        e["primary_facade_heading_deg"] = None
        e["primary_facade_cardinal"] = None
        e["transform3d_tscn"] = f"Transform3D(1, 0, 0,  0, 1, 0,  0, 0, 1,  {gx:.4f}, {gy:.4f}, {gz:.4f})"

# 5. Actualizar Metadata Global
manifest["meta"] = {
    "schema_version": "2.0.0",
    "blend_file": "blender_assets/osm2world_adjusted.blend",
    "total_meshes_in_blend": total_entries,
    "total_entries_in_manifest": total_entries,
    "topological_match_stats": {
        "point_in_polygon_verified": pip_count,
        "outside_block_polygon": outside_count,
        "infrastructure_without_block": no_block_count
    },
    "coordinate_reference": {
        "system": "WGS84 Universal Municipal Projection (osm2world calibrated)",
        "origin_lat": ORIGIN_LAT,
        "origin_lon": ORIGIN_LON,
        "meters_per_deg_lat": METERS_PER_DEG_LAT,
        "meters_per_deg_lon": METERS_PER_DEG_LON,
        "cos_lat0": 0.842704,
        "description": "Origen (0, 0, 0) métrico en osm2world / Godot, calibrado sobre 4,239 manzanas del municipio de Tecate."
    },
    "cache_files_used": {
        "blocks_cache": "blocks_cache.json",
        "facades_cache": "facades_cache.json",
        "panoramas_cache": "panoramas_cache.json"
    },
    "blocks_indexed": len(ctx.blocks),
    "facades_indexed": len(ctx.facades),
    "panoramas_available": len(ctx.panoramas),
    "updated_at": "2026-09-23"
}

print(f"Actualización completada en {time.time() - t_start:.2f} s")
print(f"  • Verificados dentro de polígono: {pip_count}")
print(f"  • Fuera de polígono (calles/límites): {outside_count}")
print(f"  • Sin manzana (infraestructura rural): {no_block_count}")

print(f"Guardando nuevo manifiesto en {MANIFEST_PATH}...")
with open(MANIFEST_PATH, "w", encoding="utf-8") as f_out:
    json.dump(manifest, f_out, indent=2, ensure_ascii=False)

mb = MANIFEST_PATH.stat().st_size / 1024 / 1024
print(f"✅ Manifiesto guardado exitosamente. Tamaño: {mb:.1f} MB")
