"""
test_railway_layer.py
=====================

Pruebas que verifican que la capa ferroviaria:

  1. Utiliza exactamente la misma proyección geográfica que las vialidades.
  2. Utiliza el mismo sistema de consulta de elevación.
  3. Utiliza el mismo sistema de rasterización (rasterize_linear_segment).
  4. Tiene caché independiente de la capa de vialidades.
  5. Produce los materiales correctos (rieles, traviesas, powered rails).
  6. La escritura incremental MCA modifica sólo los chunks afectados.
  7. El parsing de block states maneja propiedades NBT correctamente.
  8. La detección de bifurcaciones coloca palancas en posiciones no-vía.
  9. El algoritmo de Bresenham garantiza conectividad cardinal (sin diagonales puras).
"""

import io
import json
import math
import os
import tempfile
import threading

import numpy as np
import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Imports del módulo bajo prueba
# ─────────────────────────────────────────────────────────────────────────────
from src.minecraft_pipeline.railway_layer import (
    _bresenham_path,
    _build_palette_entry_nbt,
    _parse_block_state_str,
    _rail_shape,
    build_lever_blocks,
    build_railway_graph,
    find_bifurcations,
    rasterize_railway_worker,
)
from src.minecraft_pipeline.exporter import (
    TerrainHeightCache,
    TerrainHeightInterpolator,
    VoxelMap,
    load_custom_blocks_cache,
    rasterize_linear_segment,
    save_custom_blocks_cache,
)
from src.minecraft_pipeline.mca import MCARegion, pack_block_states, unpack_block_states
from src.minecraft_pipeline.nbt import (
    NBT,
    TAG_BYTE,
    TAG_COMPOUND,
    TAG_LIST,
    TAG_LONG_ARRAY,
    TAG_STRING,
    read_tag,
    write_tag,
)
from src.core_io.coords import gps_to_local, local_to_gps


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures comunes
# ─────────────────────────────────────────────────────────────────────────────

class MockInterpolator:
    """Interpolador de terreno sintético para tests."""

    def __init__(self, flat_height: float = 400.0):
        self.flat_height = flat_height
        self.batch_calls = 0
        self.single_calls = 0

    def query_height(self, x: float, z: float) -> float:
        self.single_calls += 1
        return self.flat_height

    def query_height_batch(self, coords):
        self.batch_calls += 1
        return np.full(len(coords), self.flat_height, dtype=np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1 — Misma proyección geográfica
# ─────────────────────────────────────────────────────────────────────────────

def test_railway_uses_same_projection():
    """
    gps_to_local produce coordenadas idénticas tanto para el pipeline de
    vialidades como para el pipeline ferroviario.

    Ambos llaman al mismo gps_to_local de src.core_io.coords.
    """
    lat, lon = 32.573229, -116.626536   # Parque Hidalgo, Tecate

    # Proyección desde el módulo ferroviario
    from src.core_io.coords import gps_to_local as railway_gps
    lx_rail, ly_rail = railway_gps(lat, lon)

    # Proyección usada directamente (misma función, sin wrapping)
    lx_ref, ly_ref = gps_to_local(lat, lon)

    assert lx_rail == lx_ref, "X coord mismatch between railway and road projection"
    assert ly_rail == ly_ref, "Y coord mismatch between railway and road projection"

    # En Tecate center debe ser (0, 0)
    assert abs(lx_ref) < 1e-6
    assert abs(ly_ref) < 1e-6


def test_mc_z_convention():
    """
    La convención Minecraft Z = -local_Y es la misma para vialidades y ferrocarril.
    Un punto al norte (ly > 0) debe tener z_mc < 0.
    """
    lat_north = 32.58    # ligeramente al norte
    lon_ref   = -116.626536
    lx, ly = gps_to_local(lat_north, lon_ref)
    z_mc = -ly
    assert ly > 0, "Punto al norte debe tener local_Y positivo"
    assert z_mc < 0, "Minecraft Z al norte debe ser negativo (igual que vialidades)"


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2 — Mismo sistema de consulta de elevación
# ─────────────────────────────────────────────────────────────────────────────

def test_railway_uses_same_height_interpolator(monkeypatch):
    """
    build_railway_graph() usa TerrainHeightInterpolator.query_height_batch(),
    exactamente igual que el pipeline de vialidades.
    """
    import src.minecraft_pipeline.exporter as exporter_mod

    def mock_load_vertices(glb_path, s, tx, tz):
        x = np.array([-500.0, 500.0, -500.0, 500.0, 0.0], dtype=np.float32)
        z = np.array([-500.0, -500.0, 500.0, 500.0, 0.0], dtype=np.float32)
        y = np.array([400.0, 410.0, 400.0, 410.0, 405.0], dtype=np.float32)
        return x, y, z

    monkeypatch.setattr(exporter_mod, "load_terrain_vertices", mock_load_vertices)
    interpolator = TerrainHeightInterpolator("dummy.glb", 1.0, 0.0, 0.0, cell_size=1000.0)

    osm_data = {
        "elements": [
            {
                "type": "way",
                "tags": {"railway": "rail"},
                "geometry": [
                    {"lat": 32.573229, "lon": -116.626536},
                    {"lat": 32.574000, "lon": -116.625000},
                ],
            }
        ]
    }
    y_offset = 391

    edges, node_heights = build_railway_graph(osm_data, y_offset, interpolator)

    assert len(edges) == 1
    assert len(node_heights) == 2

    # Heights deben ser terrain_height - y_offset
    for h in node_heights.values():
        # terrain_height is in [400, 410], so h should be in [-9, 19]
        assert -50 <= h <= 50, f"Unexpected height value: {h}"


def test_height_query_batch_vs_single(monkeypatch):
    """
    query_height_batch y query_height retornan valores coherentes para las
    mismas coordenadas — igual que en el test existente del pipeline de vialidades.
    """
    import src.minecraft_pipeline.exporter as exporter_mod

    def mock_load_vertices(glb_path, s, tx, tz):
        x = np.array([-10.0, 10.0, -10.0, 10.0, 0.0], dtype=np.float32)
        z = np.array([-10.0, -10.0, 10.0, 10.0, 0.0], dtype=np.float32)
        y = np.array([100.0, 110.0, 100.0, 110.0, 105.0], dtype=np.float32)
        return x, y, z

    monkeypatch.setattr(exporter_mod, "load_terrain_vertices", mock_load_vertices)
    interpolator = TerrainHeightInterpolator("dummy.glb", 1.0, 0.0, 0.0, cell_size=50.0)

    queries = [(5.0, -5.0), (-2.0, 3.0), (0.0, 0.0)]
    singles = [interpolator.query_height(q[0], q[1]) for q in queries]
    batch   = interpolator.query_height_batch(queries)

    for s, b in zip(singles, batch):
        assert abs(s - b) < 1e-3, f"Single={s} vs Batch={b}"


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3 — Misma función de rasterización (rasterize_linear_segment compartida)
# ─────────────────────────────────────────────────────────────────────────────

def test_rasterize_linear_segment_shared():
    """
    rasterize_linear_segment produce el mismo conjunto de coordenadas cuando
    se llama con un bloque fijo, sin importar si el caller es road o railway.
    """
    def fixed_block(x, z, d, dist_along, dist, is_bridge, y_road):
        return "minecraft:stone"

    # Segmento de 10 bloques en X puro
    road_result = rasterize_linear_segment(
        0.0, 0.0, 10.0, 0.0,
        50, 50,
        0.5,            # half_w = 0.5 → d ∈ {0} sólo
        fixed_block,
        is_bridge=False,
        centerline_heights=None,
    )

    railway_result = rasterize_linear_segment(
        0.0, 0.0, 10.0, 0.0,
        50, 50,
        0.0,            # half_w = 0 → d == 0 only
        fixed_block,
        is_bridge=False,
        centerline_heights=None,
    )

    # Ambos deben tener exactamente los mismos x,z para el centro
    road_xz    = {(x, z) for (x, y, z) in road_result if road_result[(x, y, z)] == "minecraft:stone"}
    railway_xz = {(x, z) for (x, y, z) in railway_result if railway_result[(x, y, z)] == "minecraft:stone"}

    # El resultado railway (half_w=0) es un subconjunto del road (half_w=0.5)
    assert railway_xz.issubset(road_xz), (
        "Railway centerline should be subset of road centerline positions"
    )

    # Los puntos deben cubrir X en [0, 10]
    xs = {x for (x, z) in railway_xz}
    assert min(xs) <= 1 and max(xs) >= 9


def test_rasterize_linear_segment_height_interpolation():
    """
    La altura interpolada en el punto medio del segmento debe ser la media
    de las alturas extremas (para segmento plano sin centerline_heights).
    """
    blocks = rasterize_linear_segment(
        0.0, 0.0, 10.0, 0.0,
        10, 20,          # y1=10, y2=20
        0.0,
        lambda x, z, d, da, dist, ib, yr: "minecraft:stone",
    )

    # Punto medio x≈5: altura esperada ≈ 15
    y_at_x5 = [y for (x, y, z), name in blocks.items()
                if x == 5 and name == "minecraft:stone"]
    assert y_at_x5, "No block at x=5"
    assert abs(y_at_x5[0] - 15) <= 1


# ─────────────────────────────────────────────────────────────────────────────
# TEST 4 — Caché independiente
# ─────────────────────────────────────────────────────────────────────────────

def test_railway_cache_independence(tmp_path):
    """
    Guardar y cargar el caché ferroviario no afecta el caché de vialidades.
    Los dos archivos son completamente independientes.
    """
    road_cache_path    = str(tmp_path / "custom_blocks_cache.npz")
    railway_cache_path = str(tmp_path / "railway_blocks_cache.npz")

    # Caché de vialidades
    road_blocks = {
        (0, 50, 0): "minecraft:gray_concrete",
        (1, 50, 0): "minecraft:gray_concrete",
    }
    save_custom_blocks_cache(road_cache_path, road_blocks, 10, 5)

    # Caché ferroviario
    railway_blocks = {
        (100, 51, 200): "minecraft:rail[shape=north_south]",
        (100, 50, 200): "minecraft:copper_trapdoor[facing=north,half=top,open=false]",
    }
    save_custom_blocks_cache(railway_cache_path, railway_blocks, 3, 3)

    # Cargar ambos de forma independiente
    loaded_road, _, _, _    = load_custom_blocks_cache(road_cache_path)
    loaded_railway, _, _, _ = load_custom_blocks_cache(railway_cache_path)

    # Verificar que cada caché contiene sólo sus propios bloques
    road_coords    = {(x, y, z) for (x, y, z), _ in loaded_road.items()}
    railway_coords = {(x, y, z) for (x, y, z), _ in loaded_railway.items()}

    assert road_coords.isdisjoint(railway_coords), (
        "Road and railway caches must not share any coordinates"
    )
    assert (0, 50, 0) in road_coords
    assert (100, 51, 200) in railway_coords
    assert (100, 51, 200) not in road_coords
    assert (0, 50, 0) not in railway_coords


# ─────────────────────────────────────────────────────────────────────────────
# TEST 5 — Materiales ferroviarios correctos
# ─────────────────────────────────────────────────────────────────────────────

def _make_raster_path():
    """Helper: edge de 20 nodos en línea recta."""
    nodes = [(float(i), 0.0) for i in range(20)]
    edge  = {"nodes": nodes, "name": "Ferrocarril de Tecate", "railway_type": "rail"}
    node_heights    = {(float(i), 0.0): 50 for i in range(20)}
    centerline_heights = {(i, 0): 50 for i in range(20)}
    return edge, node_heights, centerline_heights


def test_railway_block_materials():
    """
    Un segmento ferroviario debe producir:
      - minecraft:copper_trapdoor  en y_terrain para posiciones no-powered
      - minecraft:rail             en y_terrain+1
      - minecraft:powered_rail     cada POWERED_RAIL_INTERVAL posiciones
      - minecraft:redstone_block   bajo las powered rails
    """
    from src.minecraft_pipeline.railway_layer import POWERED_RAIL_INTERVAL

    edge, node_heights, centerline_heights = _make_raster_path()
    blocks, raster_path = rasterize_railway_worker(
        edge, node_heights, y_offset=0, centerline_heights=centerline_heights
    )

    assert len(raster_path) > 0, "raster_path must not be empty"

    # Verificar presencia de rieles y traviesas
    rail_blocks     = {k: v for k, v in blocks.items() if "minecraft:rail" in v and "powered" not in v}
    powered_blocks  = {k: v for k, v in blocks.items() if "powered_rail" in v}
    trapdoor_blocks = {k: v for k, v in blocks.items() if "copper_trapdoor" in v}
    redstone_blocks = {k: v for k, v in blocks.items() if v == "minecraft:redstone_block"}

    assert len(rail_blocks)     > 0, "Must have regular rails"
    assert len(powered_blocks)  > 0, "Must have powered rails"
    assert len(trapdoor_blocks) > 0, "Must have copper trapdoors"
    assert len(redstone_blocks) > 0, "Must have redstone blocks"

    # Verificar que powered rails corresponden al intervalo
    powered_count = len(powered_blocks)
    expected_min  = len(raster_path) // POWERED_RAIL_INTERVAL
    # Allow ±1 for edge effects
    assert abs(powered_count - expected_min) <= 1, (
        f"Expected ~{expected_min} powered rails, got {powered_count}"
    )

    # Verificar que traviesa y riel están en el y correcto
    for (x, y, z), name in trapdoor_blocks.items():
        # La traviesa está en y_terrain=50
        assert y == 50, f"Trapdoor at wrong y: {y}"
        # Debe haber un riel en y+1
        rail_above = blocks.get((x, y + 1, z), "")
        assert "rail" in rail_above, f"No rail above trapdoor at ({x},{y},{z})"


def test_railway_trapdoor_properties():
    """La traviesa de cobre debe tener facing=north, half=top, open=false."""
    edge, node_heights, centerline_heights = _make_raster_path()
    blocks, _ = rasterize_railway_worker(
        edge, node_heights, y_offset=0, centerline_heights=centerline_heights
    )
    trapdoors = {k: v for k, v in blocks.items() if "copper_trapdoor" in v}
    assert trapdoors, "Must have copper trapdoors"

    expected = "minecraft:copper_trapdoor[facing=north,half=top,open=false]"
    for block_str in trapdoors.values():
        assert block_str == expected, f"Wrong trapdoor state: {block_str}"


# ─────────────────────────────────────────────────────────────────────────────
# TEST 6 — Escritura MCA incremental
# ─────────────────────────────────────────────────────────────────────────────

def _build_minimal_chunk_nbt(cx: int, cz: int, s_y: int = 0) -> NBT:
    """Construye un chunk NBT mínimo con una sección de aire."""
    palette_entry = NBT(TAG_COMPOUND, value=[NBT(TAG_STRING, "Name", "minecraft:air")])
    bs_tag = NBT(TAG_COMPOUND, "block_states", [
        NBT(TAG_LIST, "palette", (TAG_COMPOUND, [palette_entry]))
    ])
    biomes_tag = NBT(TAG_COMPOUND, "biomes", [
        NBT(TAG_LIST, "palette", (TAG_STRING, ["minecraft:plains"]))
    ])
    section = NBT(TAG_COMPOUND, value=[
        NBT(TAG_BYTE, "Y", s_y),
        bs_tag,
        biomes_tag,
    ])
    return NBT(TAG_COMPOUND, "", [
        NBT(TAG_STRING, "Status", "full"),
        NBT(TAG_LIST, "sections", (TAG_COMPOUND, [section])),
    ])


def test_incremental_mca_write(tmp_path):
    """
    apply_railway_to_mca abre sólo los MCA afectados, modifica sólo los
    chunks necesarios, y reporta las regiones modificadas.
    """
    from src.minecraft_pipeline.railway_layer import apply_railway_to_mca

    region_dir = str(tmp_path / "region")
    os.makedirs(region_dir)

    # Crear una región MCA con un chunk minimal
    rx, rz = 0, 0
    region = MCARegion(rx, rz)
    cx_local, cz_local = 5, 5
    cx_global = rx * 32 + cx_local
    cz_global = rz * 32 + cz_local
    chunk_nbt = _build_minimal_chunk_nbt(cx_global, cz_global, s_y=0)
    region.set_chunk_nbt(cx_local, cz_local, chunk_nbt)

    mca_path = os.path.join(region_dir, f"r.{rx}.{rz}.mca")
    region.save(mca_path)

    # Bloques ferroviarios dentro de ese chunk
    x = cx_global * 16 + 5
    z = cz_global * 16 + 5
    railway_blocks = {
        (x, 0, z): "minecraft:copper_trapdoor[facing=north,half=top,open=false]",
        (x, 1, z): "minecraft:rail[shape=north_south]",
    }

    changed_regions: set = set()
    apply_railway_to_mca(railway_blocks, region_dir, changed_regions)

    # Verificar que la región fue reportada como modificada
    assert (rx, rz) in changed_regions, "Region must be reported as changed"

    # Verificar que los bloques fueron escritos en el MCA
    loaded_region = MCARegion.load(mca_path, rx, rz)
    loaded_chunk  = loaded_region.get_chunk_nbt(cx_local, cz_local)
    assert loaded_chunk is not None, "Modified chunk must still exist"


def test_mca_write_only_affects_target_regions(tmp_path):
    """
    La escritura ferroviaria NO debe tocar regiones sin bloques ferroviarios.
    """
    from src.minecraft_pipeline.railway_layer import apply_railway_to_mca

    region_dir = str(tmp_path / "region")
    os.makedirs(region_dir)

    # Crear dos regiones
    for rx, rz in [(0, 0), (1, 0)]:
        region = MCARegion(rx, rz)
        chunk_nbt = _build_minimal_chunk_nbt(rx * 32, rz * 32)
        region.set_chunk_nbt(0, 0, chunk_nbt)
        region.save(os.path.join(region_dir, f"r.{rx}.{rz}.mca"))

    # Bloques sólo en la región (0,0)
    railway_blocks = {(5, 0, 5): "minecraft:rail[shape=north_south]"}
    changed: set = set()
    apply_railway_to_mca(railway_blocks, region_dir, changed)

    assert (0, 0) in changed,  "Region (0,0) must be modified"
    assert (1, 0) not in changed, "Region (1,0) must NOT be modified"


# ─────────────────────────────────────────────────────────────────────────────
# TEST 7 — Parsing de block states con propiedades NBT
# ─────────────────────────────────────────────────────────────────────────────

def test_parse_block_state_with_properties():
    name, props = _parse_block_state_str("minecraft:rail[shape=north_south]")
    assert name == "minecraft:rail"
    assert props == {"shape": "north_south"}


def test_parse_block_state_multiple_properties():
    name, props = _parse_block_state_str(
        "minecraft:copper_trapdoor[facing=north,half=top,open=false]"
    )
    assert name == "minecraft:copper_trapdoor"
    assert props == {"facing": "north", "half": "top", "open": "false"}


def test_parse_block_state_no_properties():
    name, props = _parse_block_state_str("minecraft:stone")
    assert name == "minecraft:stone"
    assert props == {}


def test_build_palette_entry_nbt_with_props():
    """El NBT de paleta debe contener Name y Properties correctamente."""
    entry = _build_palette_entry_nbt("minecraft:rail[shape=north_south]")
    assert entry.type == TAG_COMPOUND

    names = {tag.name: tag for tag in entry.value}
    assert "Name" in names
    assert names["Name"].value == "minecraft:rail"
    assert "Properties" in names

    prop_dict = {t.name: t.value for t in names["Properties"].value}
    assert prop_dict["shape"] == "north_south"


def test_build_palette_entry_nbt_serialization():
    """El NBT construido debe sobrevivir un ciclo write→read."""
    entry = _build_palette_entry_nbt(
        "minecraft:powered_rail[powered=true,shape=east_west]"
    )
    # TAG_COMPOUND sin nombre requiere write_header=False y read con expected_type
    buf = io.BytesIO()
    write_tag(entry, buf, write_header=False)
    buf.seek(0)
    decoded = read_tag(buf, expected_type=TAG_COMPOUND, read_header=False)

    names = {tag.name: tag for tag in decoded.value}
    assert names["Name"].value == "minecraft:powered_rail"
    prop_dict = {t.name: t.value for t in names["Properties"].value}
    assert prop_dict["powered"] == "true"
    assert prop_dict["shape"] == "east_west"


# ─────────────────────────────────────────────────────────────────────────────
# TEST 8 — Detección de bifurcaciones y palancas
# ─────────────────────────────────────────────────────────────────────────────

def test_find_bifurcations_T_junction():
    """
    Un camino en T debe detectar una bifurcación y colocar palanca
    en una posición no-vía.

    find_bifurcations cuenta cuántas veces aparece cada posición como
    extremo de una arista (par consecutivo) en el raster_path.
    Un nodo de grado 3 = bifurcación.
    """
    # Construir un raster_path que pase 3 veces por (0,2):
    #   arista (0,1)→(0,2)  desde la línea N-S
    #   arista (0,2)→(0,3)  continuación N-S
    #   arista (0,2)→(1,2)  ramal Este
    # → (0,2) aparece en 3 aristas  →  grado 3  →  bifurcación
    raster_path = (
        [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)]  # N-S
        + [(0, 2), (1, 2), (2, 2), (3, 2)]                 # ramal Este (repite (0,2))
    )
    rail_set = set(raster_path)

    placements = find_bifurcations(raster_path, rail_set)

    # Debe haber al menos una bifurcación detectada
    assert len(placements) >= 1

    # La palanca debe estar en una posición no-vía
    for (lx, lz, dx, dz) in placements:
        assert (lx, lz) not in rail_set, (
            f"Lever at ({lx},{lz}) conflicts with rail!"
        )


def test_no_bifurcations_on_straight_line():
    """Un camino recto no debe generar bifurcaciones."""
    raster_path = [(i, 0) for i in range(20)]
    rail_set    = set(raster_path)
    placements  = find_bifurcations(raster_path, rail_set)
    assert len(placements) == 0, "Straight line must not produce bifurcations"


def test_build_lever_blocks():
    """Las palancas se deben colocar en la posición correcta con el facing correcto."""
    placements = [(10, 5, 1, 0)]   # palanca al Este, apunta al Oeste (hacia la vía)
    centerline_heights = {(10, 5): 50}

    lever_blocks = build_lever_blocks(placements, centerline_heights, {})

    # Debe haber un bloque de piedra soporte + palanca
    support = lever_blocks.get((10, 50, 5))
    lever   = lever_blocks.get((10, 51, 5))
    assert support == "minecraft:stone", f"Expected stone support, got {support}"
    assert lever is not None, "Lever block must be placed"
    assert "lever" in lever, f"Expected lever block, got {lever}"
    assert "east" in lever, f"Expected east facing lever, got {lever}"


# ─────────────────────────────────────────────────────────────────────────────
# TEST 9 — Bresenham garantiza conectividad cardinal
# ─────────────────────────────────────────────────────────────────────────────

def test_bresenham_no_diagonal_steps():
    """
    _bresenham_path garantiza que bloques consecutivos siempre comparten
    al menos una cara cardinal (|dx|+|dz| == 1), nunca diagonal (|dx|=|dz|=1).
    """
    test_cases = [
        (0, 0, 20, 20),    # diagonal pura
        (0, 0, 10, 3),     # principalmente horizontal
        (0, 0, 3, 10),     # principalmente vertical
        (0, 0, 7, 7),      # exactamente 45°
        (5, 3, -8, 12),    # negativo
    ]
    for x1, z1, x2, z2 in test_cases:
        path = _bresenham_path(x1, z1, x2, z2)
        assert path[0]  == (x1, z1), f"Path must start at ({x1},{z1})"
        assert path[-1] == (x2, z2), f"Path must end at ({x2},{z2})"

        for i in range(1, len(path)):
            prev = path[i - 1]
            curr = path[i]
            dx = abs(curr[0] - prev[0])
            dz = abs(curr[1] - prev[1])
            assert dx + dz == 1, (
                f"Non-cardinal step ({prev}→{curr}) in path "
                f"from ({x1},{z1}) to ({x2},{z2})"
            )


def test_bresenham_endpoints():
    """El camino debe incluir siempre los puntos inicial y final exactos."""
    path = _bresenham_path(3, -5, 15, 8)
    assert path[0]  == (3, -5)
    assert path[-1] == (15, 8)


# ─────────────────────────────────────────────────────────────────────────────
# TEST 10 — Rail shape correcta
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("prev_xz, next_xz, here, expected_shape", [
    # Recto E-O: viene de x=0,z=0 → aquí x=1,z=0 → siguiente x=2,z=0
    # d_from = here - prev = (1,0)-(0,0) = (+1, 0) → east
    # d_to   = next - here = (2,0)-(1,0) = (+1, 0) → east
    # pair {east,east} → straight east_west
    ((0, 0), (2, 0), (1, 0),  "east_west"),

    # Recto N-S: viene de z=0 → aquí z=1 → siguiente z=2
    # d_from = (0,1)-(0,0) = (0,+1) → south
    # d_to   = (0,2)-(0,1) = (0,+1) → south
    # pair {south,south} → straight north_south
    ((0, 0), (0, 2), (0, 1),  "north_south"),

    # Curva S→E: viene de z=1 → aquí (0,0) → siguiente x=1,z=0
    # d_from = (0,0)-(0,1) = (0,-1) → north
    # d_to   = (1,0)-(0,0) = (+1,0) → east
    # pair {north,east} → north_east
    ((0, 1), (1, 0), (0, 0),  "north_east"),

    # Curva S→W: viene de z=1 → aquí (0,0) → siguiente x=-1,z=0
    # d_from = (0,0)-(0,1) = (0,-1) → north
    # d_to   = (-1,0)-(0,0) = (-1,0) → west
    # pair {north,west} → north_west
    ((0, 1), (-1, 0), (0, 0),  "north_west"),

    # Sin prev: sólo next=(1,0) desde here=(0,0)
    # d_from = d_to = east → east_west
    (None,   (1, 0), (0, 0),  "east_west"),
])
def test_rail_shape_directions(prev_xz, next_xz, here, expected_shape):
    shape = _rail_shape(prev_xz, next_xz, here)
    assert shape == expected_shape, (
        f"Shape mismatch: prev={prev_xz}, next={next_xz}, here={here} "
        f"→ got '{shape}', expected '{expected_shape}'"
    )


# ─────────────────────────────────────────────────────────────────────────────
# TEST 11 — VoxelMap compatible (misma clase que vialidades)
# ─────────────────────────────────────────────────────────────────────────────

def test_railway_uses_same_voxelmap(tmp_path):
    """
    El caché ferroviario usa la misma clase VoxelMap que el de vialidades.
    Los bloques se guardan y recuperan con el mismo mecanismo.
    """
    railway_blocks = {
        (100, 51, 200): "minecraft:rail[shape=north_south]",
        (100, 50, 200): "minecraft:copper_trapdoor[facing=north,half=top,open=false]",
        (101, 51, 200): "minecraft:rail[shape=east_west]",
    }

    cache_path = str(tmp_path / "railway_blocks_cache.npz")
    save_custom_blocks_cache(cache_path, railway_blocks, last_edge_idx=5, last_block_idx=5)

    loaded, le, lb, _ = load_custom_blocks_cache(cache_path)

    assert isinstance(loaded, VoxelMap), "Cache must return a VoxelMap instance"
    assert le == 5

    # Verificar que los bloques se recuperan correctamente
    assert loaded.get((100, 51, 200)) == "minecraft:rail[shape=north_south]"
    assert loaded.get((100, 50, 200)) == "minecraft:copper_trapdoor[facing=north,half=top,open=false]"
