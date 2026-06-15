"""
railway_layer.py — Capa Ferroviaria Incremental del Ferrocarril de Tecate
=========================================================================

Implementa una capa ferroviaria que se aplica sobre regiones MCA ya generadas
sin regenerar el terreno, agua, vialidades ni manzanas.

Reutiliza exactamente los mismos mecanismos que la capa de vialidades:

  • Proyección geográfica  → gps_to_local() / local_to_gps()
  • Interpolación de altura → TerrainHeightInterpolator (mismo objeto)
  • Caché de altura        → TerrainHeightCache (path independiente)
  • Mapa de vóxeles        → VoxelMap (misma clase)
  • Serialización de caché → save_custom_blocks_cache / load_custom_blocks_cache
  • Rasterización lineal   → rasterize_linear_segment() (función compartida)
  • Escritura MCA          → MCARegion.load / set_chunk_nbt / save (mismas clases)

Arquitectura
------------
Fuente OSM (railway=rail)
  → load_railway_osm()              [Overpass + mirrors + GeoJSON fallback]
  → gps_to_local()                  [MISMA proyección que vialidades]
  → build_railway_graph()           [nodos y edges locales]
  → TerrainHeightInterpolator       [MISMO objeto que vialidades]
  → rasterize_railway_worker()
      → rasterize_linear_segment()  [función COMPARTIDA con vialidades]
  → VoxelMap + save_custom_blocks_cache()   [MISMAS funciones, paths distintos]
  → apply_railway_to_mca()          [escritura incremental sobre MCA existente]
      → MCARegion.load / set_chunk_nbt / save

Representación en Minecraft
---------------------------
Cada posición de vía (x, z) recibe:
  - (x, y_terrain,   z): minecraft:copper_trapdoor[facing=north,half=top,open=false]
                         (traviesa incrustada en la mitad superior del bloque de suelo)
  - (x, y_terrain+1, z): minecraft:rail[shape=<dir>]
                         (riel encima de la traviesa, a nivel del suelo visible)

  Cada 7 posiciones:
  - (x, y_terrain,   z): minecraft:redstone_block   (alimenta el powered rail)
  - (x, y_terrain+1, z): minecraft:powered_rail[powered=true,shape=<dir>]

  En bifurcaciones:
  - Bloque de piedra + palanca colocada al lado de la vía

Caché independiente
-------------------
  export/railway_osm_cache.json         — geometría OSM cruda
  export/minecraft_world/railway_blocks_cache.npz — VoxelMap de bloques rasterizados
  export/minecraft_world/railway_height_cache.json — alturas consultadas

Ninguno de estos archivos afecta ni es afectado por:
  custom_blocks_cache.npz, terrain_height_cache.json, water_osm_cache.json
"""

from __future__ import annotations

import json
import math
import os
import time
import concurrent.futures
import threading
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Optional

import numpy as np
import requests

from .mca import MCARegion, pack_block_states, unpack_block_states
from .nbt import (
    NBT,
    TAG_BYTE,
    TAG_COMPOUND,
    TAG_LIST,
    TAG_LONG_ARRAY,
    TAG_STRING,
)
from .exporter import (
    TerrainHeightCache,
    TerrainHeightInterpolator,
    VoxelMap,
    load_custom_blocks_cache,
    print_progress,
    rasterize_linear_segment,
    save_custom_blocks_cache,
)
from src.core_io.coords import gps_to_local, local_to_gps

# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────

OVERPASS_ENDPOINTS: List[str] = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
]

# Tipos de vía ferroviaria que se consultan en OSM
RAILWAY_TAGS = ["rail", "light_rail", "narrow_gauge", "preserved", "tram"]

# Intervalo (en bloques) entre powered rails (1 powered + 6 regular)
POWERED_RAIL_INTERVAL = 7

# ─────────────────────────────────────────────────────────────────────────────
# Adquisición de datos geográficos
# ─────────────────────────────────────────────────────────────────────────────

def _build_overpass_query(bbox: Tuple[float, float, float, float], timeout: int = 60) -> str:
    min_lat, min_lon, max_lat, max_lon = bbox
    tag_filters = "\n".join(
        f'  way["railway"="{t}"]({min_lat},{min_lon},{max_lat},{max_lon});'
        for t in RAILWAY_TAGS
    )
    return (
        f'[out:json][timeout:{timeout}];\n(\n{tag_filters}\n);\nout body geom;\n'
    )


def _query_overpass_railway(
    bbox: Tuple[float, float, float, float],
    timeout: int = 60,
) -> Optional[dict]:
    """
    Consulta la API Overpass para vías ferroviarias en el bbox.
    Intenta múltiples mirrors con fallback secuencial.
    Retorna JSON bruto o None si todos los endpoints fallan.
    """
    query = _build_overpass_query(bbox, timeout)
    headers = {
        "User-Agent": "TecateSimulatorMinecraftPipeline/1.0 (contact: hakkindavid@github)"
    }
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            print(f"[Railway] Querying Overpass: {endpoint} ...")
            resp = requests.post(
                endpoint,
                data={"data": query},
                headers=headers,
                timeout=timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("elements"):
                    print(
                        f"[Railway] Overpass OK — {len(data['elements'])} element(s) from {endpoint}"
                    )
                    return data
                print(f"[Railway] Overpass returned 0 elements from {endpoint}. Trying next mirror...")
            else:
                print(
                    f"[Railway] HTTP {resp.status_code} from {endpoint}. Trying next mirror..."
                )
        except Exception as exc:
            print(f"[Railway] Endpoint {endpoint} failed ({exc}). Trying next mirror...")
    return None


def _load_fallback_geojson(path: str) -> Optional[dict]:
    """
    Carga geometría ferroviaria desde un GeoJSON local.
    Formato esperado: FeatureCollection con LineString / MultiLineString.
    Retorna un dict con la clave "elements" compatible con la estructura OSM,
    o None si el archivo no existe o no tiene datos.
    """
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            geojson = json.load(f)
        elements: List[dict] = []
        for feature in geojson.get("features", []):
            geom = feature.get("geometry", {})
            props = feature.get("properties", {}) or {}
            lines: List[List] = []
            if geom.get("type") == "LineString":
                lines = [geom["coordinates"]]
            elif geom.get("type") == "MultiLineString":
                lines = geom["coordinates"]
            for line in lines:
                geometry = [{"lat": c[1], "lon": c[0]} for c in line]
                elements.append(
                    {
                        "type": "way",
                        "id": abs(hash(str(line))),
                        "tags": {
                            "railway": props.get("railway", "rail"),
                            "name": props.get("name", ""),
                        },
                        "geometry": geometry,
                    }
                )
        if elements:
            print(
                f"[Railway] Loaded {len(elements)} element(s) from fallback GeoJSON: {path}"
            )
            return {"elements": elements}
        print(f"[Railway] Fallback GeoJSON at {path} has no LineString features.")
    except Exception as exc:
        print(f"[Railway] Failed to load fallback GeoJSON {path}: {exc}")
    return None


def load_railway_osm(
    bbox: Tuple[float, float, float, float],
    cache_path: str = "export/railway_osm_cache.json",
    fallback_geojson: str = "data/railway_fallback.geojson",
) -> dict:
    """
    Carga datos OSM de vías ferroviarias para el bbox especificado.

    Estrategia en orden de prioridad:
      1. Caché en disco (cache_path)
      2. Overpass API (múltiples mirrors)
      3. GeoJSON local (fallback_geojson)

    Parameters
    ----------
    bbox : (min_lat, min_lon, max_lat, max_lon)
    cache_path : str    Ruta al archivo caché JSON.
    fallback_geojson : str   Ruta al GeoJSON local de respaldo.

    Returns
    -------
    dict con clave "elements" (lista de ways OSM) o {"elements": []}.
    """
    cache_dir = os.path.dirname(os.path.abspath(cache_path))
    os.makedirs(cache_dir, exist_ok=True)

    # 1. Caché en disco
    if os.path.exists(cache_path):
        try:
            print(f"[Railway] Loading OSM data from cache: {cache_path}")
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if cached.get("elements"):
                print(
                    f"[Railway] Cache hit — {len(cached['elements'])} element(s)."
                )
                return cached
            print("[Railway] Cached data is empty. Re-fetching...")
        except Exception as exc:
            print(f"[Railway] Failed to read cache ({exc}). Re-fetching...")

    # 2. Overpass API
    osm_data = _query_overpass_railway(bbox)
    if osm_data and osm_data.get("elements"):
        _save_json_cache(osm_data, cache_path)
        return osm_data

    # 3. GeoJSON local
    print(
        "[Railway] Overpass unavailable or returned no data. "
        "Trying local GeoJSON fallback..."
    )
    fallback = _load_fallback_geojson(fallback_geojson)
    if fallback and fallback.get("elements"):
        _save_json_cache(fallback, cache_path)
        return fallback

    print("[Railway] WARNING: No railway data found from any source.")
    return {"elements": []}


def _save_json_cache(data: dict, path: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        print(f"[Railway] Saved OSM cache → {path}")
    except Exception as exc:
        print(f"[Railway] Warning: Could not save cache to {path}: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Construcción del grafo ferroviario
# ─────────────────────────────────────────────────────────────────────────────

def build_railway_graph(
    osm_data: dict,
    y_offset: int,
    interpolator: TerrainHeightInterpolator,
) -> Tuple[List[dict], Dict[Tuple[float, float], int]]:
    """
    Convierte elementos OSM en una lista de edges con coordenadas locales Minecraft.

    Reutiliza exactamente la misma proyección que las vialidades:
      x_mc  = lx           (local_x, Este)
      z_mc  = -ly          (Minecraft Z = -local_Y Norte)

    Cada edge:
      {
        "nodes": [(x1,z1), (x2,z2), ...],   # coords Minecraft locales (float)
        "name": str,
        "railway_type": str,
      }

    Parameters
    ----------
    osm_data : dict    Datos OSM con clave "elements".
    y_offset : int     Mismo offset vertical que el mundo generado.
    interpolator : TerrainHeightInterpolator

    Returns
    -------
    edges : List[dict]
    node_heights : Dict[(x_mc, z_mc), int]   Altura MC (terreno - y_offset)
    """
    edges: List[dict] = []
    all_interp_coords: List[Tuple[float, float]] = []   # (x, -z) para el interpolador
    all_mc_coords: List[Tuple[float, float]] = []       # (x, z) Minecraft

    for el in osm_data.get("elements", []):
        if el.get("type") != "way":
            continue
        geom = el.get("geometry", [])
        if len(geom) < 2:
            continue
        tags = el.get("tags", {})

        mc_coords: List[Tuple[float, float]] = []
        for pt in geom:
            lx, ly = gps_to_local(pt["lat"], pt["lon"])
            x_mc = lx
            z_mc = -ly          # misma convención que vialidades
            mc_coords.append((x_mc, z_mc))
            all_interp_coords.append((x_mc, -z_mc))   # interpolador usa (x, -z_mc)
            all_mc_coords.append((x_mc, z_mc))

        edges.append(
            {
                "nodes": mc_coords,
                "name": tags.get("name", ""),
                "railway_type": tags.get("railway", "rail"),
            }
        )

    print(f"[Railway] Built {len(edges)} railway edge(s) from OSM data.")

    # Consulta en lote de alturas (MISMO mecanismo que vialidades)
    node_heights: Dict[Tuple[float, float], int] = {}
    if all_interp_coords and interpolator is not None:
        print(
            f"[Railway] Batch querying heights for {len(all_interp_coords)} railway node(s)..."
        )
        heights_raw = interpolator.query_height_batch(all_interp_coords)
        for (x_mc, z_mc), (x_interp, neg_z_interp), h_raw in zip(
            all_mc_coords, all_interp_coords, heights_raw
        ):
            node_heights[(x_mc, z_mc)] = int(round(float(h_raw))) - y_offset

    return edges, node_heights


# ─────────────────────────────────────────────────────────────────────────────
# Rasterización
# ─────────────────────────────────────────────────────────────────────────────

def _bresenham_path(
    x1: float, z1: float, x2: float, z2: float
) -> List[Tuple[int, int]]:
    """
    Genera la secuencia de bloques enteros (x, z) entre dos puntos usando
    el algoritmo de Bresenham. Garantiza que bloques consecutivos comparten
    al menos una cara cardinal (no diagonales puras), insertando pasos
    intermedios cuando sea necesario.

    Esto es necesario porque los rieles Minecraft no pueden conectarse
    entre bloques que sólo comparten esquinas.
    """
    x1, z1 = int(round(x1)), int(round(z1))
    x2, z2 = int(round(x2)), int(round(z2))

    if x1 == x2 and z1 == z2:
        return [(x1, z1)]

    points: List[Tuple[int, int]] = []
    dx = abs(x2 - x1)
    dz = abs(z2 - z1)
    sx = 1 if x2 > x1 else -1
    sz = 1 if z2 > z1 else -1
    x, z = x1, z1

    if dx >= dz:
        err = dx // 2
        while x != x2:
            points.append((x, z))
            err -= dz
            if err < 0:
                z += sz
                err += dx
            x += sx
    else:
        err = dz // 2
        while z != z2:
            points.append((x, z))
            err -= dx
            if err < 0:
                x += sx
                err += dz
            z += sz
    points.append((x2, z2))

    # Eliminar diagonales puras: insertar bloque intermedio
    fixed: List[Tuple[int, int]] = [points[0]]
    for i in range(1, len(points)):
        prev = fixed[-1]
        curr = points[i]
        ddx = curr[0] - prev[0]
        ddz = curr[1] - prev[1]
        if abs(ddx) == 1 and abs(ddz) == 1:
            # Preferir paso horizontal primero
            intermediate = (prev[0] + ddx, prev[1])
            fixed.append(intermediate)
        fixed.append(curr)

    return fixed


def _rail_shape(
    from_xz: Optional[Tuple[int, int]],
    to_xz: Optional[Tuple[int, int]],
    here: Tuple[int, int],
) -> str:
    """
    Determina la forma (shape) correcta del bloque de riel en la posición `here`
    dado el bloque anterior (from_xz) y el siguiente (to_xz).

    Shapes planas válidas:
      north_south, east_west,
      north_east, north_west, south_east, south_west
    """
    def _cardinal(ox: int, oz: int) -> Optional[str]:
        if oz < 0:
            return "north"
        if oz > 0:
            return "south"
        if ox > 0:
            return "east"
        if ox < 0:
            return "west"
        return None

    d_from = _cardinal(here[0] - from_xz[0], here[1] - from_xz[1]) if from_xz else None
    d_to   = _cardinal(to_xz[0]  - here[0],  to_xz[1]  - here[1])  if to_xz   else None

    # Si sólo tenemos una dirección, riel recto en esa dirección
    if d_from is None and d_to is None:
        return "north_south"
    if d_from is None:
        d_from = d_to
    if d_to is None:
        d_to = d_from

    # Straight track: same or opposite cardinal direction
    if d_from in {"north", "south"} and d_to in {"north", "south"}:
        return "north_south"
    if d_from in {"east", "west"} and d_to in {"east", "west"}:
        return "east_west"

    # Curved track: two different orthogonal directions
    curves = {
        frozenset({"north", "east"}): "north_east",
        frozenset({"north", "west"}): "north_west",
        frozenset({"south", "east"}): "south_east",
        frozenset({"south", "west"}): "south_west",
    }
    return curves.get(frozenset({d_from, d_to}), "north_south")


def rasterize_railway_worker(
    edge: dict,
    node_heights: Dict[Tuple[float, float], int],
    y_offset: int,
    centerline_heights: Dict[Tuple[int, int], int],
) -> Tuple[Dict[Tuple[int, int, int], str], List[Tuple[int, int]]]:
    """
    Rasteriza un edge ferroviario en bloques Minecraft.

    Utiliza la misma convención de coordenadas que rasterize_roads_worker:
      - x_mc, z_mc en espacio Cartesiano local Minecraft
      - y_mc = altura del terreno en bloques MC (ya aplicado y_offset)

    Representación por bloque (x, z):
      y_terrain   : minecraft:copper_trapdoor[facing=north,half=top,open=false]
      y_terrain+1 : minecraft:rail[shape=<dir>]
      (cada POWERED_RAIL_INTERVAL posiciones, se sustituye por powered rail + redstone block)

    Returns
    -------
    local_blocks : {(x, y, z): block_name}
    raster_path  : [(x, z), ...]  orden de posiciones de riel
    """
    local_blocks: Dict[Tuple[int, int, int], str] = {}
    raster_path: List[Tuple[int, int]] = []
    rail_positions: List[Tuple[int, int, int]] = []   # (x, y_rail, z)

    nodes = edge["nodes"]
    if len(nodes) < 2:
        return local_blocks, raster_path

    for seg_idx in range(len(nodes) - 1):
        x1, z1 = nodes[seg_idx]
        x2, z2 = nodes[seg_idx + 1]

        y1_mc = node_heights.get((x1, z1), 0)
        y2_mc = node_heights.get((x2, z2), 0)

        seg_path = _bresenham_path(x1, z1, x2, z2)
        n_seg = max(1, len(seg_path) - 1)

        for path_idx, (px, pz) in enumerate(seg_path):
            if raster_path and raster_path[-1] == (px, pz):
                continue    # evitar duplicados en uniones de segmentos

            # Altura del terreno en este bloque (mismo mecanismo que vialidades)
            if (px, pz) in centerline_heights:
                y_terrain = centerline_heights[(px, pz)]
            else:
                t = path_idx / n_seg
                y_terrain = int(round(y1_mc + t * (y2_mc - y1_mc)))

            y_trapdoor = y_terrain          # bloque de suelo que reemplazamos
            y_rail     = y_terrain + 1      # riel encima de la traviesa

            raster_path.append((px, pz))
            block_counter = len(raster_path)

            is_powered = (block_counter % POWERED_RAIL_INTERVAL == 0)

            if is_powered:
                # Redstone block debajo alimenta el powered rail desde abajo
                local_blocks[(px, y_trapdoor - 1, pz)] = "minecraft:redstone_block"
                local_blocks[(px, y_trapdoor,     pz)] = "minecraft:redstone_block"
                # Shape se fijará después
                local_blocks[(px, y_rail, pz)] = "minecraft:powered_rail[powered=true,shape=north_south]"
            else:
                local_blocks[(px, y_trapdoor, pz)] = (
                    "minecraft:copper_trapdoor[facing=north,half=top,open=false]"
                )
                local_blocks[(px, y_rail, pz)] = "minecraft:rail[shape=north_south]"

            rail_positions.append((px, y_rail, pz))

            # Limpiar 2 bloques de aire sobre el riel
            for ya in range(y_rail + 1, y_rail + 3):
                key = (px, ya, pz)
                if key not in local_blocks:
                    local_blocks[key] = "minecraft:air"

    # Corregir shapes de rieles según la dirección real del camino
    _fix_rail_shapes(local_blocks, raster_path)

    return local_blocks, raster_path


def _fix_rail_shapes(
    blocks: Dict[Tuple[int, int, int], str],
    raster_path: List[Tuple[int, int]],
) -> None:
    """
    Actualiza in-place los block states de shape de rieles usando la dirección
    real del camino en cada bloque.
    """
    if len(raster_path) < 1:
        return

    # Mapa rápido posición→primer índice en el path
    pos_to_idx: Dict[Tuple[int, int], int] = {}
    for i, pos in enumerate(raster_path):
        if pos not in pos_to_idx:
            pos_to_idx[pos] = i

    for i, (x, z) in enumerate(raster_path):
        prev_xz = raster_path[i - 1] if i > 0 else None
        next_xz = raster_path[i + 1] if i < len(raster_path) - 1 else None

        # Ignorar duplicado consecutivo
        if prev_xz == (x, z):
            prev_xz = None
        if next_xz == (x, z):
            next_xz = None

        shape = _rail_shape(prev_xz, next_xz, (x, z))

        # Actualizar todos los bloques de riel en esta columna (x, z)
        for (bx, by, bz) in list(blocks.keys()):
            if bx != x or bz != z:
                continue
            name = blocks[(bx, by, bz)]
            if "powered_rail" in name:
                blocks[(bx, by, bz)] = f"minecraft:powered_rail[powered=true,shape={shape}]"
            elif "minecraft:rail" in name and "powered" not in name:
                blocks[(bx, by, bz)] = f"minecraft:rail[shape={shape}]"


# ─────────────────────────────────────────────────────────────────────────────
# Detección de bifurcaciones y palancas
# ─────────────────────────────────────────────────────────────────────────────

def find_bifurcations(
    raster_path: List[Tuple[int, int]],
    rail_set: Set[Tuple[int, int]],
) -> List[Tuple[int, int, int, int]]:
    """
    Detecta bifurcaciones (nodos con grado > 2) en el camino rasterizado
    y retorna las posiciones sugeridas para colocar palancas.

    La palanca se coloca en el primer vecino cardinal de la bifurcación
    que no sea vía ferroviaria.

    Returns
    -------
    List of (lever_x, lever_z, dx, dz)
      donde (dx, dz) es la dirección hacia la vía desde la palanca.
    """
    conn: Counter = Counter()
    for i in range(len(raster_path) - 1):
        a, b = raster_path[i], raster_path[i + 1]
        conn[a] += 1
        conn[b] += 1

    switches = [pos for pos, c in conn.items() if c > 2]
    lever_placements: List[Tuple[int, int, int, int]] = []

    CARDINAL = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for (sx, sz) in switches:
        for (dx, dz) in CARDINAL:
            candidate = (sx + dx, sz + dz)
            if candidate not in rail_set:
                lever_placements.append((sx + dx, sz + dz, -dx, -dz))
                break    # sólo una palanca por bifurcación

    if lever_placements:
        print(f"[Railway] Detected {len(lever_placements)} bifurcation(s) → levers placed.")
    return lever_placements


def build_lever_blocks(
    lever_placements: List[Tuple[int, int, int, int]],
    centerline_heights: Dict[Tuple[int, int], int],
    node_heights: Dict[Tuple[float, float], int],
) -> Dict[Tuple[int, int, int], str]:
    """
    Genera bloques de soporte (piedra) y palanca para cada bifurcación.

    La palanca se mira hacia la vía para que el jugador la active fácilmente.

    Returns
    -------
    {(x, y, z): block_name}
    """
    _face = {
        (1,  0): "east",   # palanca al E, mira al W (hacia la vía al W)
        (-1, 0): "west",
        (0,  1): "south",
        (0, -1): "north",
    }
    lever_blocks: Dict[Tuple[int, int, int], str] = {}

    for (lx, lz, towards_dx, towards_dz) in lever_placements:
        # Altura en la posición de la palanca
        y_base = centerline_heights.get(
            (lx, lz),
            next(
                (h for (nx, nz), h in node_heights.items()
                 if abs(nx - lx) < 20 and abs(nz - lz) < 20),
                0,
            ),
        )
        facing = _face.get((towards_dx, towards_dz), "north")
        lever_blocks[(lx, y_base,     lz)] = "minecraft:stone"
        lever_blocks[(lx, y_base + 1, lz)] = (
            f"minecraft:lever[face=floor,facing={facing},powered=false]"
        )

    return lever_blocks


# ─────────────────────────────────────────────────────────────────────────────
# Escritura incremental sobre MCA
# ─────────────────────────────────────────────────────────────────────────────

def _parse_block_state_str(
    block_str: str,
) -> Tuple[str, Dict[str, str]]:
    """
    Parsea 'minecraft:rail[shape=north_south]'
    → ('minecraft:rail', {'shape': 'north_south'})
    """
    if "[" in block_str and block_str.endswith("]"):
        name, props_raw = block_str.split("[", 1)
        props: Dict[str, str] = {}
        for pair in props_raw[:-1].split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                props[k.strip()] = v.strip()
        return name, props
    return block_str, {}


def _build_palette_entry_nbt(block_str: str) -> NBT:
    """
    Construye un TAG_COMPOUND de paleta NBT desde un string de block state.
    Ejemplo:
      'minecraft:rail[shape=north_south]'
      → {Name: "minecraft:rail", Properties: {shape: "north_south"}}
    """
    name, props = _parse_block_state_str(block_str)
    tags = [NBT(TAG_STRING, "Name", name)]
    if props:
        prop_tags = [NBT(TAG_STRING, k, v) for k, v in sorted(props.items())]
        tags.append(NBT(TAG_COMPOUND, "Properties", prop_tags))
    return NBT(TAG_COMPOUND, value=tags)


def _read_palette_from_section(bs_tag: NBT) -> List[str]:
    """
    Lee la paleta de un TAG_COMPOUND block_states y retorna lista de strings
    en formato 'minecraft:block[prop=val,...]'.
    """
    palette: List[str] = []
    children = bs_tag.value if isinstance(bs_tag.value, list) else []
    for child in children:
        if child.name != "palette":
            continue
        item_type, items = child.value  # TAG_LIST → (type, [NBT...])
        for entry in items:
            block_name = ""
            props: Dict[str, str] = {}
            for tag in entry.value:
                if tag.name == "Name":
                    block_name = tag.value
                elif tag.name == "Properties":
                    for ptag in tag.value:
                        props[ptag.name] = ptag.value
            if props:
                prop_str = ",".join(f"{k}={v}" for k, v in sorted(props.items()))
                palette.append(f"{block_name}[{prop_str}]")
            else:
                palette.append(block_name)
    return palette


def _apply_blocks_to_chunk_nbt(
    chunk_nbt: NBT,
    blocks_to_apply: Dict[Tuple[int, int, int], str],
    cx_global: int,
    cz_global: int,
) -> NBT:
    """
    Inyecta bloques adicionales en un chunk NBT existente.

    Para cada sección Y afectada:
      1. Lee la paleta y datos empaquetados actuales.
      2. Desempaqueta los 4096 índices de bloques.
      3. Aplica los bloques nuevos (actualizando la paleta si es necesario).
      4. Reempaqueta y reconstruye el section NBT.

    Los bloques no afectados permanecen intactos.

    Parameters
    ----------
    chunk_nbt : NBT    Chunk descomprimido retornado por MCARegion.get_chunk_nbt().
    blocks_to_apply : {(x, y, z): block_state_str}
    cx_global, cz_global : int   Coordenadas globales del chunk.

    Returns
    -------
    NBT   Chunk modificado listo para MCARegion.set_chunk_nbt().
    """
    # Separar la tag "sections" del resto
    sections_tag: Optional[NBT] = None
    other_tags: List[NBT] = []
    for tag in chunk_nbt.value:
        if tag.name == "sections":
            sections_tag = tag
        else:
            other_tags.append(tag)

    if sections_tag is None:
        return chunk_nbt   # chunk sin secciones, no tocamos nada

    item_type, existing_sections = sections_tag.value   # TAG_LIST → (TAG_COMPOUND, [...])

    # Índice de secciones por Y
    section_by_y: Dict[int, NBT] = {}
    for sec in existing_sections:
        for tag in sec.value:
            if tag.name == "Y":
                section_by_y[tag.value] = sec
                break

    # Agrupar bloques nuevos por sección Y
    blocks_by_section: Dict[int, Dict[Tuple[int, int, int], str]] = defaultdict(dict)
    for (bx, by, bz), block_str in blocks_to_apply.items():
        blocks_by_section[by // 16][(bx, by, bz)] = block_str

    # Copiar lista de secciones para modificar
    new_sections = list(existing_sections)

    for s_y, section_blocks in sorted(blocks_by_section.items()):
        if s_y in section_by_y:
            # ── Sección existente ──────────────────────────────────────
            sec_nbt = section_by_y[s_y]
            bs_tag: Optional[NBT] = None
            biomes_tag: Optional[NBT] = None
            other_sec: List[NBT] = []

            for tag in sec_nbt.value:
                if tag.name == "block_states":
                    bs_tag = tag
                elif tag.name == "biomes":
                    biomes_tag = tag
                elif tag.name == "Y":
                    pass   # reconstruiremos el Y
                else:
                    other_sec.append(tag)

            # Leer paleta y datos actuales
            palette: List[str] = []
            data_longs: List[int] = []
            if bs_tag is not None:
                palette = _read_palette_from_section(bs_tag)
                for child in (bs_tag.value if isinstance(bs_tag.value, list) else []):
                    if child.name == "data":
                        data_longs = child.value

            if not palette:
                palette = ["minecraft:air"]

            # Desempaquetar índices
            if len(palette) > 1 and data_longs:
                bits = max(4, int(math.ceil(math.log2(len(palette)))))
                block_indices = list(unpack_block_states(data_longs, bits))
            else:
                block_indices = [0] * 4096

            # Aplicar bloques nuevos
            palette_map = {name: idx for idx, name in enumerate(palette)}
            for (bx, by, bz), block_str in section_blocks.items():
                lx = bx - cx_global * 16
                ly = by - s_y * 16
                lz = bz - cz_global * 16
                if not (0 <= lx < 16 and 0 <= ly < 16 and 0 <= lz < 16):
                    continue
                flat = ly * 256 + lz * 16 + lx
                if block_str not in palette_map:
                    palette_map[block_str] = len(palette)
                    palette.append(block_str)
                block_indices[flat] = palette_map[block_str]

            new_sec = _rebuild_section_nbt(
                s_y, palette, block_indices, biomes_tag, other_sec
            )

            # Reemplazar en la lista
            old_idx = new_sections.index(section_by_y[s_y])
            new_sections[old_idx] = new_sec

        else:
            # ── Nueva sección (no existía en el chunk) ─────────────────
            palette = ["minecraft:air"]
            block_indices = [0] * 4096
            palette_map = {"minecraft:air": 0}

            for (bx, by, bz), block_str in section_blocks.items():
                lx = bx - cx_global * 16
                ly = by - s_y * 16
                lz = bz - cz_global * 16
                if not (0 <= lx < 16 and 0 <= ly < 16 and 0 <= lz < 16):
                    continue
                flat = ly * 256 + lz * 16 + lx
                if block_str not in palette_map:
                    palette_map[block_str] = len(palette)
                    palette.append(block_str)
                block_indices[flat] = palette_map[block_str]

            biomes_nbt = NBT(
                TAG_COMPOUND,
                "biomes",
                [NBT(TAG_LIST, "palette", (TAG_STRING, ["minecraft:plains"]))],
            )
            new_sec = _rebuild_section_nbt(s_y, palette, block_indices, biomes_nbt, [])
            new_sections.append(new_sec)

    # Reconstruir chunk NBT
    new_sections_tag = NBT(TAG_LIST, "sections", (TAG_COMPOUND, new_sections))
    return NBT(TAG_COMPOUND, chunk_nbt.name, other_tags + [new_sections_tag])


def _rebuild_section_nbt(
    s_y: int,
    palette: List[str],
    block_indices: List[int],
    biomes_tag: Optional[NBT],
    other_tags: List[NBT],
) -> NBT:
    """Reconstruye el NBT de una sección con paleta y datos actualizados."""
    palette_nbt = [_build_palette_entry_nbt(b) for b in palette]
    bs_children = [NBT(TAG_LIST, "palette", (TAG_COMPOUND, palette_nbt))]

    if len(palette) > 1:
        bits = max(4, int(math.ceil(math.log2(len(palette)))))
        longs = pack_block_states(block_indices, bits)
        bs_children.append(NBT(TAG_LONG_ARRAY, "data", longs))

    sec_tags = [
        NBT(TAG_BYTE, "Y", s_y),
        NBT(TAG_COMPOUND, "block_states", bs_children),
    ]
    if biomes_tag is not None:
        sec_tags.append(biomes_tag)
    sec_tags.extend(other_tags)

    return NBT(TAG_COMPOUND, value=sec_tags)


def apply_railway_to_mca(
    railway_blocks: Dict[Tuple[int, int, int], str],
    region_dir: str,
    changed_regions: Set[Tuple[int, int]],
) -> None:
    """
    Aplica bloques ferroviarios sobre archivos MCA existentes de forma incremental.

    - Abre únicamente los chunks afectados.
    - Modifica únicamente los bloques necesarios.
    - No regenera regiones completas.
    - No destruye construcciones existentes.
    - Reporta qué regiones fueron modificadas.

    Parameters
    ----------
    railway_blocks : {(x, y, z): block_name}
    region_dir : str    Ruta al directorio region/ del mundo.
    changed_regions : set   Se actualiza con (rx, rz) de cada región modificada.
    """
    print("[Railway] Applying railway blocks to MCA files (incremental write)...")

    # Agrupar bloques por región → chunk local
    by_region: Dict[
        Tuple[int, int],
        Dict[Tuple[int, int], Dict[Tuple[int, int, int], str]],
    ] = defaultdict(lambda: defaultdict(dict))

    for (x, y, z), block_name in railway_blocks.items():
        cx = int(math.floor(x / 16))
        cz = int(math.floor(z / 16))
        rx = int(math.floor(cx / 32))
        rz = int(math.floor(cz / 32))
        cx_local = cx - rx * 32
        cz_local = cz - rz * 32
        by_region[(rx, rz)][(cx_local, cz_local)][(x, y, z)] = block_name

    total_regions = len(by_region)
    processed = 0
    t0 = time.time()

    for (rx, rz), chunks_dict in sorted(by_region.items()):
        mca_path = os.path.join(region_dir, f"r.{rx}.{rz}.mca")
        if not os.path.exists(mca_path):
            print(
                f"[Railway] WARNING: r.{rx}.{rz}.mca not found — "
                "run main export first. Skipping."
            )
            processed += 1
            continue

        region = MCARegion.load(mca_path, rx, rz)
        region_modified = False

        for (cx_local, cz_local), chunk_blocks in chunks_dict.items():
            cx_global = rx * 32 + cx_local
            cz_global = rz * 32 + cz_local

            chunk_nbt = region.get_chunk_nbt(cx_local, cz_local)
            if chunk_nbt is None:
                print(
                    f"[Railway] WARNING: Chunk ({cx_global},{cz_global}) "
                    f"not found in r.{rx}.{rz} — skipping chunk."
                )
                continue

            modified_nbt = _apply_blocks_to_chunk_nbt(
                chunk_nbt, chunk_blocks, cx_global, cz_global
            )
            region.set_chunk_nbt(cx_local, cz_local, modified_nbt)
            region_modified = True

        if region_modified:
            region.save(mca_path)
            changed_regions.add((rx, rz))

        processed += 1
        print_progress("[Railway] Applying to MCA", processed, total_regions, t0)

    print(f"\n[Railway] MCA write complete. {len(changed_regions)} region(s) modified.")


# ─────────────────────────────────────────────────────────────────────────────
# Punto de entrada principal
# ─────────────────────────────────────────────────────────────────────────────

def get_region_dir(world_dir):
    """Locates the Minecraft region folder, supporting custom overworld dimensions (Higher Heights)."""
    custom_path = os.path.join(world_dir, "dimensions", "minecraft", "overworld", "region")
    if os.path.exists(custom_path):
        return custom_path
    return os.path.join(world_dir, "region")

def export_railway_layer(
    world_dir: str,
    glb_path: str,
    output_dir: str,
    parallel_workers: int = 0,
) -> Set[Tuple[int, int]]:
    """
    Pipeline principal de la capa ferroviaria.

    Aplica el Ferrocarril de Tecate sobre un mundo Minecraft ya generado,
    sin tocar el terreno, agua, vialidades ni manzanas.

    Parámetros
    ----------
    world_dir : str    Ruta a TecateWorld/ (contiene region/, tecate_metadata.json).
    glb_path : str     Ruta al GLB de terreno.
    output_dir : str   Directorio padre de TecateWorld/ (donde vive el caché).
    parallel_workers : int   0 = automático.

    Retorna
    -------
    changed_regions : set de (rx, rz) con las regiones modificadas.
    """
    # ── 1. Cargar metadatos del mundo ─────────────────────────────────────
    metadata_path = os.path.join(world_dir, "tecate_metadata.json")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(
            f"[Railway] tecate_metadata.json not found at {metadata_path}. "
            "Run the main world export first."
        )

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    y_offset: int = metadata["vertical_offset"]
    align = metadata.get("terrain_alignment", {})
    s:  float = align.get("scale",         0.8427785648661434)
    tx: float = align.get("translation_x", 28052.404303473268)
    tz: float = align.get("translation_z", -16620.3853885848)

    print(f"[Railway] World metadata: y_offset={y_offset}, scale={s:.6f}")

    region_dir = get_region_dir(world_dir)
    if not os.path.exists(region_dir):
        raise FileNotFoundError(f"[Railway] Region dir not found: {region_dir}")

    # ── 2. Caché de altura independiente ─────────────────────────────────
    height_cache_path = os.path.join(output_dir, "railway_height_cache.json")
    height_cache = TerrainHeightCache(cache_path=height_cache_path)

    # ── 3. Interpolador de terreno (MISMO mecanismo que vialidades) ───────
    print("[Railway] Loading terrain height interpolator...")
    interpolator = TerrainHeightInterpolator(glb_path, s, tx, tz)

    # ── 4. Determinar bbox GPS desde el mundo existente ───────────────────
    bbox_meta = metadata.get("bbox", {})
    min_lx = bbox_meta.get("min_local_x", -3000.0)
    max_lx = bbox_meta.get("max_local_x",  3000.0)
    min_ly = bbox_meta.get("min_local_y", -3000.0)
    max_ly = bbox_meta.get("max_local_y",  3000.0)

    lat1, lon1 = local_to_gps(min_lx, min_ly)
    lat2, lon2 = local_to_gps(max_lx, max_ly)
    osm_bbox = (
        min(lat1, lat2) - 0.01,
        min(lon1, lon2) - 0.01,
        max(lat1, lat2) + 0.01,
        max(lon1, lon2) + 0.01,
    )
    print(f"[Railway] GPS bbox for OSM query: {osm_bbox}")

    # ── 5. Cargar datos OSM (caché + Overpass + GeoJSON fallback) ─────────
    osm_cache_path = os.path.join(output_dir, "railway_osm_cache.json")
    osm_data = load_railway_osm(osm_bbox, cache_path=osm_cache_path)

    n_elements = len(osm_data.get("elements", []))
    if n_elements == 0:
        print("[Railway] No railway elements found. Nothing to do.")
        return set()
    print(f"[Railway] {n_elements} railway element(s) to process.")

    # ── 6. Construir grafo ferroviario ─────────────────────────────────────
    edges, node_heights = build_railway_graph(osm_data, y_offset, interpolator)
    if not edges:
        print("[Railway] No valid railway edges after graph build. Exiting.")
        return set()

    # ── 7. Consulta en lote de alturas de la línea central ────────────────
    print("[Railway] Batch querying centerline heights for all railway segments...")
    centerline_coords_set: Set[Tuple[int, int]] = set()
    edge_paths: List[List[Tuple[int, int]]] = []

    for edge in edges:
        edge_full_path: List[Tuple[int, int]] = []
        nodes = edge["nodes"]
        for i in range(len(nodes) - 1):
            x1, z1 = nodes[i]
            x2, z2 = nodes[i + 1]
            seg = _bresenham_path(x1, z1, x2, z2)
            for pt in seg:
                centerline_coords_set.add(pt)
                edge_full_path.append(pt)
        edge_paths.append(edge_full_path)

    unique_cl_coords = list(centerline_coords_set)
    # Mismo formato que vialidades: (x, -z) para query_height_batch
    interp_coords = [(px, -pz) for (px, pz) in unique_cl_coords]
    cl_heights_raw = interpolator.query_height_batch(interp_coords)

    centerline_heights: Dict[Tuple[int, int], int] = {
        (px, pz): int(round(float(h))) - y_offset
        for (px, pz), h in zip(unique_cl_coords, cl_heights_raw)
    }
    print(f"[Railway] {len(centerline_heights)} centerline height(s) resolved.")

    # ── 8. Cargar caché ferroviario independiente ─────────────────────────
    railway_cache_path = os.path.join(output_dir, "railway_blocks_cache.npz")
    railway_voxel, last_edge_idx, _, _ = load_custom_blocks_cache(railway_cache_path)
    initial_edge_idx = last_edge_idx

    all_railway_blocks: Dict[Tuple[int, int, int], str] = {}
    all_raster_paths:   List[Tuple[int, int]] = []

    # ── 9. Rasterización paralela (MISMO mecanismo que vialidades) ────────
    edges_to_process = edges[last_edge_idx:]

    if edges_to_process:
        workers = parallel_workers if parallel_workers > 0 else (os.cpu_count() or 4)
        print(
            f"[Railway] Rasterizing {len(edges_to_process)} edge(s) "
            f"using {workers} thread(s)..."
        )
        t_raster = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    rasterize_railway_worker,
                    edge, node_heights, y_offset, centerline_heights,
                ): i
                for i, edge in enumerate(edges_to_process)
            }
            done_count = 0
            for fut in concurrent.futures.as_completed(futures):
                try:
                    local_blocks, raster_path = fut.result()
                    all_railway_blocks.update(local_blocks)
                    all_raster_paths.extend(raster_path)
                    last_edge_idx += 1
                except Exception as exc:
                    print(f"\n[Railway Error] Edge {futures[fut]}: {exc}")
                done_count += 1
                print_progress(
                    "[Railway] Rasterizing edges",
                    done_count,
                    len(edges_to_process),
                    t_raster,
                )

        print(
            f"\n[Railway] Rasterization done in {time.time()-t_raster:.2f}s — "
            f"{len(all_railway_blocks)} block(s) generated."
        )

        # Guardar caché ferroviario
        railway_voxel.update(all_railway_blocks)
        save_custom_blocks_cache(
            railway_cache_path, railway_voxel, last_edge_idx, last_edge_idx
        )
        print(f"[Railway] Railway cache saved → {railway_cache_path}")

    else:
        print("[Railway] Rasterization already complete (loaded from cache).")
        for coord, name in railway_voxel.items():
            all_railway_blocks[coord] = name

    # ── 10. Detectar bifurcaciones y añadir palancas ──────────────────────
    rail_set: Set[Tuple[int, int]] = {
        (x, z)
        for (x, y, z) in all_railway_blocks
        if "rail" in all_railway_blocks[(x, y, z)]
    }
    lever_placements = find_bifurcations(all_raster_paths, rail_set)
    lever_blocks = build_lever_blocks(lever_placements, centerline_heights, node_heights)
    all_railway_blocks.update(lever_blocks)

    # ── 11. Escritura incremental sobre MCA ──────────────────────────────
    changed_regions: Set[Tuple[int, int]] = set()
    apply_railway_to_mca(all_railway_blocks, region_dir, changed_regions)

    height_cache.save()

    # ── 12. Reporte final ─────────────────────────────────────────────────
    if changed_regions:
        print(
            f"\n[Railway] ✓ Pipeline complete. "
            f"{len(changed_regions)} region(s) modified:"
        )
        for rx, rz in sorted(changed_regions):
            print(f"    r.{rx}.{rz}.mca")
    else:
        print("\n[Railway] Pipeline complete. No regions were modified.")

    return changed_regions


# ─────────────────────────────────────────────────────────────────────────────
# CLI de línea de comandos (mismo patrón que exporter.py)
# ─────────────────────────────────────────────────────────────────────────────

def _load_env(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k not in os.environ:
                os.environ[k] = v


if __name__ == "__main__":
    import argparse
    import sys

    _load_env()

    parser = argparse.ArgumentParser(
        description="Tecate Railroad Layer — Incremental MCA exporter"
    )
    parser.add_argument(
        "--world-dir",
        default=None,
        help="Path to TecateWorld/ directory (falls back to FRESH_WORLD env var)",
    )
    parser.add_argument(
        "--glb-path",
        default=None,
        help="Path to terrain GLB (falls back to GLB_PATH env var)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory parent of TecateWorld/ (falls back to OUTPUT_DIR env var)",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=0,
        help="Number of worker threads (0 = auto)",
    )
    args = parser.parse_args()

    world_dir  = args.world_dir  or os.getenv("FRESH_WORLD")  or "export/minecraft_world/TecateWorld"
    glb_path   = args.glb_path   or os.getenv("GLB_PATH")     or "models/tecate/glb/tecate.glb"
    output_dir = args.output_dir or os.getenv("OUTPUT_DIR")   or "export/minecraft_world"

    if not os.path.exists(world_dir):
        print(f"[Railway] ERROR: world_dir does not exist: {world_dir}")
        sys.exit(1)
    if not os.path.exists(glb_path):
        print(f"[Railway] ERROR: glb_path does not exist: {glb_path}")
        sys.exit(1)

    changed = export_railway_layer(world_dir, glb_path, output_dir, args.parallel)
    sys.exit(0 if changed is not None else 1)
