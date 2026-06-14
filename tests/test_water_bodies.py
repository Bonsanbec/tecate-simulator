import os
import math
import numpy as np
import pytest
from src.minecraft_pipeline.exporter import TerrainWaterInterpolator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_interp(triangles, cell_size=200.0):
    """Build a mock TerrainWaterInterpolator from a list of (A, B, C) tuples
    where each vertex is (x, y, z). Spatial grid is built automatically."""
    interp = TerrainWaterInterpolator.__new__(TerrainWaterInterpolator)
    interp.cell_size = cell_size
    interp.triangles = list(triangles)
    interp.grid = {}
    for tri_idx, (a, b, c) in enumerate(interp.triangles):
        min_x = min(a[0], b[0], c[0])
        max_x = max(a[0], b[0], c[0])
        min_z = min(a[2], b[2], c[2])
        max_z = max(a[2], b[2], c[2])
        c_x_min = int(math.floor(min_x / cell_size))
        c_x_max = int(math.floor(max_x / cell_size))
        c_z_min = int(math.floor(min_z / cell_size))
        c_z_max = int(math.floor(max_z / cell_size))
        for cx in range(c_x_min, c_x_max + 1):
            for cz in range(c_z_min, c_z_max + 1):
                interp.grid.setdefault((cx, cz), []).append(tri_idx)
    return interp


def _square_water(x0, z0, x1, z1, y=5.0):
    """Two triangles forming an axis-aligned rectangular water body in xz space."""
    A = (x0, y, z0)
    B = (x1, y, z0)
    C = (x1, y, z1)
    D = (x0, y, z1)
    return [(A, B, C), (A, C, D)]


def _local_poly(x0, z0, x1, z1):
    """Rectangle polygon in raw local JSON format [[lx, ly], ...].

    lot_overlaps_water converts each vertex as: xw = lx, zw = -ly.
    So to cover water-space rectangle (x0..x1, z0..z1) we need:
        lx ∈ [x0..x1],  -ly ∈ [z0..z1]  →  ly ∈ [-z1..-z0]
    """
    return [
        [x0, -z0],
        [x1, -z0],
        [x1, -z1],
        [x0, -z1],
    ]


# ---------------------------------------------------------------------------
# query_water unit tests
# ---------------------------------------------------------------------------

def test_water_interpolator_math():
    """Single triangle: inside point gets correct barycentric height, outside is False."""
    interp = TerrainWaterInterpolator.__new__(TerrainWaterInterpolator)
    interp.cell_size = 100.0
    # XZ plane: A=(0,0), B=(10,0), C=(0,10) ; y heights: 10, 20, 30
    interp.triangles = [
        ((0.0, 10.0, 0.0), (10.0, 20.0, 0.0), (0.0, 30.0, 10.0))
    ]
    interp.grid = {(0, 0): [0]}

    # Point inside at (2, 2): y = 10 + 0.2*(30-10) + 0.2*(20-10) = 16
    is_w, y_w = interp.query_water(2.0, 2.0)
    assert is_w
    assert abs(y_w - 16.0) < 1e-5

    # Point outside at (8, 8): x+z > 10, outside triangle
    is_w_out, _ = interp.query_water(8.0, 8.0)
    assert not is_w_out


def test_water_interpolator_glb():
    """Smoke test against real GLB file if present."""
    glb_path = "models/tecate/glb/tecate.glb"
    if os.path.exists(glb_path):
        interp = TerrainWaterInterpolator(
            glb_path,
            s=0.8427785648661434,
            tx=28052.404303473268,
            tz=-16620.3853885848,
        )
        assert len(interp.triangles) > 0
        assert len(interp.grid) > 0
        is_w, _ = interp.query_water(0.0, 0.0)
        assert not is_w


# ---------------------------------------------------------------------------
# lot_overlaps_water unit tests
# ---------------------------------------------------------------------------

def test_lot_fully_inside_water():
    """All interior blocks of the lot are inside a water body → True."""
    interp = _make_interp(_square_water(0, 0, 100, 100))
    poly = _local_poly(20, 20, 40, 40)
    assert interp.lot_overlaps_water(poly) is True


def test_lot_fully_outside_water():
    """No interior block is near any water triangle → False."""
    interp = _make_interp(_square_water(0, 0, 50, 50))
    poly = _local_poly(200, 200, 250, 250)   # far away
    assert interp.lot_overlaps_water(poly) is False


def test_lot_partially_overlapping_water_corner():
    """Lot overlaps water only at one corner — still True."""
    interp = _make_interp(_square_water(0, 0, 50, 50))
    # Lot [40..80]×[40..80] shares corner [40..50]×[40..50] with water
    poly = _local_poly(40, 40, 80, 80)
    assert interp.lot_overlaps_water(poly) is True


def test_lot_adjacent_but_not_overlapping():
    """Lot that starts exactly one block past the water boundary → False."""
    interp = _make_interp(_square_water(0, 0, 50, 50))
    poly = _local_poly(51, 51, 100, 100)
    assert interp.lot_overlaps_water(poly) is False


def test_lot_enclosing_water_body():
    """A large lot fully enclosing a small water triangle inside → True."""
    interp = _make_interp([
        ((40.0, 5.0, 40.0), (60.0, 5.0, 40.0), (50.0, 5.0, 60.0))
    ])
    poly = _local_poly(0, 0, 200, 200)
    assert interp.lot_overlaps_water(poly) is True


def test_lot_overlaps_water_no_triangles():
    """No triangles → always False (short-circuit)."""
    interp = _make_interp([])
    poly = _local_poly(0, 0, 100, 100)
    assert interp.lot_overlaps_water(poly) is False


def test_lot_overlaps_water_degenerate_polygon():
    """Fewer than 3 vertices → no interior → False."""
    interp = _make_interp(_square_water(0, 0, 100, 100))
    assert interp.lot_overlaps_water([[0, 0], [10, 0]]) is False
    assert interp.lot_overlaps_water([]) is False


def test_lot_overlaps_water_thin_strip():
    """Thin water strip: lot entirely clear misses; lot crossing the strip hits."""
    interp = _make_interp(_square_water(0, 50, 200, 55))

    poly_clear = _local_poly(0, 0, 100, 45)     # entirely below strip
    assert interp.lot_overlaps_water(poly_clear) is False

    poly_cross = _local_poly(0, 40, 100, 60)    # crosses the strip
    assert interp.lot_overlaps_water(poly_cross) is True


def test_lot_overlaps_water_spatial_grid_miss():
    """Spatial grid short-circuit: no candidate cells means False without scanning interior."""
    # Water at very large positive coordinates, lot at origin
    interp = _make_interp(_square_water(10000, 10000, 10100, 10100))
    poly = _local_poly(0, 0, 50, 50)
    assert interp.lot_overlaps_water(poly) is False
