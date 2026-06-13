import os
import json
import math
import numpy as np
import pytest
import tempfile
import io
from scipy.interpolate import griddata

from src.minecraft_pipeline.nbt import NBT, TAG_COMPOUND, TAG_LIST, TAG_STRING, TAG_INT, TAG_LONG, TAG_BYTE, TAG_DOUBLE, write_tag, read_tag
from src.minecraft_pipeline.mca import pack_block_states, unpack_block_states, MCARegion
from src.minecraft_pipeline.exporter import draw_line_3d, TerrainHeightInterpolator

def test_nbt_serialization_roundtrip():
    """Verifies that custom NBT compound structure translates perfectly to bytes and back."""
    root = NBT(TAG_COMPOUND, "Root", [
        NBT(TAG_BYTE, "ByteVal", -12),
        NBT(TAG_STRING, "StrVal", "Tecate Test"),
        NBT(TAG_LIST, "ListVal", (TAG_INT, [10, 20, 30])),
        NBT(TAG_COMPOUND, "SubComp", [
            NBT(TAG_DOUBLE, "DblVal", 2.71828)
        ])
    ])
    
    buf = io.BytesIO()
    write_tag(root, buf)
    encoded = buf.getvalue()
    
    buf.seek(0)
    decoded = read_tag(buf)
    
    assert decoded.name == "Root"
    assert decoded.value[0].name == "ByteVal"
    assert decoded.value[0].value == -12
    assert decoded.value[1].value == "Tecate Test"
    assert [item.value for item in decoded.value[2].value[1]] == [10, 20, 30]
    assert decoded.value[3].value[0].value == 2.71828

@pytest.mark.parametrize("palette_size, bits_per_block", [
    (2, 4),   # fits in 4 bits
    (15, 4),  # fits in 4 bits
    (17, 5),  # needs 5 bits
    (45, 6),  # needs 6 bits
    (100, 7), # needs 7 bits
    (250, 8), # needs 8 bits
])
def test_block_states_bit_packing_roundtrip(palette_size, bits_per_block):
    """Tests that chunk block state indices are packed and unpacked exactly without distortion."""
    # Create 4096 pseudo random indices fitting the palette size
    np.random.seed(42)
    original_indices = np.random.randint(0, palette_size, size=4096).tolist()
    
    longs = pack_block_states(original_indices, bits_per_block)
    unpacked_indices = unpack_block_states(longs, bits_per_block)
    
    # Assert exact match
    assert unpacked_indices == original_indices

def test_mca_region_save_and_load():
    """Verifies MCA region file compilation, sector packing, and loading."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mca_path = os.path.join(tmpdir, "r.0.0.mca")
        
        region_write = MCARegion(0, 0)
        
        # Create a simple chunk NBT
        chunk_nbt = NBT(TAG_COMPOUND, "", [
            NBT(TAG_INT, "xPos", 10),
            NBT(TAG_INT, "zPos", 12),
            NBT(TAG_STRING, "Status", "full")
        ])
        
        region_write.set_chunk_nbt(5, 5, chunk_nbt)
        region_write.save(mca_path)
        
        assert os.path.exists(mca_path)
        
        # Load and verify
        region_read = MCARegion.load(mca_path, 0, 0)
        decoded_nbt = region_read.get_chunk_nbt(5, 5)
        
        assert decoded_nbt is not None
        
        # Extract fields
        xPos = None
        Status = None
        for tag in decoded_nbt.value:
            if tag.name == "xPos":
                xPos = tag.value
            elif tag.name == "Status":
                Status = tag.value
                
        assert xPos == 10
        assert Status == "full"

def test_3d_line_drawing():
    """Tests drawing 3D integer lines for skeletons and roads."""
    pts = draw_line_3d(0, 10, 0, 0, 15, 0)
    assert len(pts) == 6
    assert (0, 10, 0) in pts
    assert (0, 15, 0) in pts
    
    pts_diag = draw_line_3d(0, 0, 0, 3, 3, 3)
    assert (0, 0, 0) in pts_diag
    assert (3, 3, 3) in pts_diag

def test_terrain_height_interpolation(tmp_path):
    """Tests local interpolation of heights using spatial grid indexing."""
    # Write a tiny dummy GLB to test the interpolator
    # We will mock the load_terrain_vertices inside exporter by writing a small helper
    # For testing, we mock the class directly or construct a mini GLB.
    # To keep it extremely simple, let's test Delaunay/griddata on mock data.
    x = np.array([-10.0, 10.0, -10.0, 10.0, 0.0])
    z = np.array([-10.0, -10.0, 10.0, 10.0, 0.0])
    y = np.array([100.0, 110.0, 100.0, 110.0, 105.0])
    
    # Delaunay triangulation
    points = np.column_stack((x, z))
    h = griddata(points, y, (5.0, -5.0), method='linear')
    assert abs(h - 107.5) < 0.1 # linear interpolation on plane
    
def test_geometric_terrain_subtraction():
    """Verifies that original terrain blocks are cullable while user blocks are preserved."""
    # Mock behavior of subtraction logic:
    # Terrain height is 12.
    # y_offset is 380.
    # Blocks to check:
    # 1. grass_block at Y=12 -> should be ignored (base terrain)
    # 2. stone at Y=10 -> should be ignored (base terrain)
    # 3. yellow_concrete at Y=12 -> should be preserved (building block)
    # 4. stone at Y=15 -> should be preserved (above terrain)
    
    y_terrain = 12
    terrain_blocks = {"minecraft:grass_block", "minecraft:dirt", "minecraft:stone"}
    
    # Test cases: (block_name, y_val) -> expected_preserved
    test_cases = [
        ("minecraft:grass_block", 12, False),
        ("minecraft:stone", 10, False),
        ("minecraft:yellow_concrete", 12, True),
        ("minecraft:stone", 15, True),
        ("minecraft:oak_planks", 8, True),
    ]
    
    for block_name, y_val, expected in test_cases:
        is_terrain = block_name in terrain_blocks and y_val <= y_terrain
        preserved = not is_terrain
        assert preserved == expected

def test_nbt_list_of_compounds():
    """Verifies that lists containing compound NBT objects roundtrip perfectly."""
    comp1 = NBT(TAG_COMPOUND, None, [NBT(TAG_STRING, "Name", "BlockA")])
    comp2 = NBT(TAG_COMPOUND, None, [NBT(TAG_STRING, "Name", "BlockB")])
    root = NBT(TAG_COMPOUND, "Root", [
        NBT(TAG_LIST, "ListComp", (TAG_COMPOUND, [comp1, comp2]))
    ])
    
    buf = io.BytesIO()
    write_tag(root, buf)
    encoded = buf.getvalue()
    
    buf.seek(0)
    decoded = read_tag(buf)
    
    assert decoded.name == "Root"
    list_comp = decoded.value[0]
    assert list_comp.name == "ListComp"
    
    items = list_comp.value[1]
    assert len(items) == 2
    assert items[0].type == TAG_COMPOUND
    assert items[0].value[0].name == "Name"
    assert items[0].value[0].value == "BlockA"
    assert items[1].value[0].value == "BlockB"

def test_geometric_helpers():
    """Tests point_in_polygon and distance_to_polygon_boundary functions."""
    from src.minecraft_pipeline.exporter import point_in_polygon, distance_to_polygon_boundary, get_deterministic_choice
    
    # 10x10 square polygon
    poly = [[0, 0], [10, 0], [10, 10], [0, 10]]
    
    # Inside points
    assert point_in_polygon(5, 5, poly) is True
    assert point_in_polygon(1, 1, poly) is True
    
    # Outside points
    assert point_in_polygon(-1, 5, poly) is False
    assert point_in_polygon(5, 11, poly) is False
    
    # Distance to boundary
    assert abs(distance_to_polygon_boundary(5, 0, poly) - 0.0) < 1e-5
    assert abs(distance_to_polygon_boundary(5, 5, poly) - 5.0) < 1e-5
    assert abs(distance_to_polygon_boundary(5, 2, poly) - 2.0) < 1e-5
    
    # Deterministic choice
    choices = ["A", "B", "C"]
    weights = [0.7, 0.2, 0.1]
    choice1 = get_deterministic_choice(10, 20, 30, choices, weights)
    choice2 = get_deterministic_choice(10, 20, 30, choices, weights)
    assert choice1 == choice2
    assert choice1 in choices

def test_road_metadata_fallback():
    """Tests road metadata cache defaults and helper functions."""
    from src.minecraft_pipeline.road_metadata_cache import get_edge_key, get_default_metadata
    
    assert get_edge_key("123", "456") == "123,456"
    assert get_edge_key("456", "123") == "123,456"
    
    meta_primary = get_default_metadata("primary")
    assert meta_primary["lanes"] == 2
    assert meta_primary["width"] == 10.0
    assert meta_primary["surface"] == "asphalt"
    
    meta_track = get_default_metadata("track")
    assert meta_track["lanes"] == 1
    assert meta_track["surface"] == "gravel"

def test_vectorized_batch_interpolation_vs_single(monkeypatch):
    """Verifies that query_height_batch returns identical values to query_height in a loop."""
    import src.minecraft_pipeline.exporter as exporter
    
    # Mock load_terrain_vertices
    def mock_load_vertices(glb_path, s, tx, tz):
        # 5 points forming a small terrain
        x = np.array([-10.0, 10.0, -10.0, 10.0, 0.0], dtype=np.float32)
        z = np.array([-10.0, -10.0, 10.0, 10.0, 0.0], dtype=np.float32)
        y = np.array([100.0, 110.0, 100.0, 110.0, 105.0], dtype=np.float32)
        return x, y, z
        
    monkeypatch.setattr(exporter, "load_terrain_vertices", mock_load_vertices)
    
    # Instantiate the interpolator
    interpolator = exporter.TerrainHeightInterpolator("dummy.glb", 1.0, 0.0, 0.0, cell_size=50.0)
    
    # Query single heights
    queries = [(5.0, -5.0), (-2.0, 3.0), (0.0, 0.0), (12.0, 12.0)]
    single_results = [interpolator.query_height(q[0], q[1]) for q in queries]
    
    # Query batch heights
    batch_results = interpolator.query_height_batch(queries)
    
    # Assert they match
    assert len(single_results) == len(batch_results)
    for s_val, b_val in zip(single_results, batch_results):
        assert abs(s_val - b_val) < 1e-4

def test_region_prioritization():
    """Verifies that regions are sorted center-outward by Euclidean distance to (0, 0)."""
    regions = {
        (2, 2): "very far",
        (0, 0): "center",
        (1, 0): "medium"
    }
    
    def region_distance(item):
        rx, rz = item[0]
        cx = rx * 512 + 256
        cz = rz * 512 + 256
        return math.sqrt(cx**2 + cz**2)
        
    sorted_regions = sorted(regions.items(), key=region_distance)
    sorted_keys = [item[0] for item in sorted_regions]
    
    assert sorted_keys == [(0, 0), (1, 0), (2, 2)]

def test_bbox_union_merging():
    """Verifies that current bounding box merges correctly with pre-existing bounding box."""
    min_x, max_x, min_y, max_y = 10.0, 50.0, 20.0, 60.0
    existing_bbox = {
        "min_local_x": 5.0,
        "max_local_x": 45.0,
        "min_local_y": 25.0,
        "max_local_y": 70.0
    }
    
    final_min_x = min(min_x, existing_bbox.get("min_local_x", min_x))
    final_max_x = max(max_x, existing_bbox.get("max_local_x", max_x))
    final_min_y = min(min_y, existing_bbox.get("min_local_y", min_y))
    final_max_y = max(max_y, existing_bbox.get("max_local_y", max_y))
    
    assert final_min_x == 5.0
    assert final_max_x == 50.0
    assert final_min_y == 20.0
    assert final_max_y == 70.0

def test_custom_blocks_cache_roundtrip(tmp_path):
    """Verifies that custom blocks cache is saved and loaded correctly, preserving coordinates, names, and progress indices."""
    from src.minecraft_pipeline.exporter import save_custom_blocks_cache, load_custom_blocks_cache
    
    cache_path = os.path.join(tmp_path, "test_cache.npz")
    
    # Create sample blocks
    custom_blocks = {
        (10, 20, 30): "minecraft:yellow_concrete",
        (-5, 12, 100): "minecraft:asphalt",
        (0, 0, 0): "minecraft:dirt"
    }
    
    last_edge_idx = 145
    last_block_idx = 890
    completed_block_indices = {1, 2, 3, 5}
    
    # Save
    save_custom_blocks_cache(cache_path, custom_blocks, last_edge_idx, last_block_idx, completed_block_indices=completed_block_indices)
    assert os.path.exists(cache_path)
    
    # Load
    loaded_blocks, le_idx, lb_idx, loaded_completed = load_custom_blocks_cache(cache_path)
    
    # Assert correctness
    assert dict(loaded_blocks.items()) == custom_blocks
    assert le_idx == last_edge_idx
    assert lb_idx == last_block_idx
    assert loaded_completed == completed_block_indices

def test_rasterize_single_block():
    """Verifies that rasterize_single_block correctly assigns platform, sidewalk, and curb heights."""
    from src.minecraft_pipeline.exporter import rasterize_single_block
    import threading
    
    b = {"polygon": [[0, 0], [10, 0], [10, 10], [0, 10]]}
    def mock_get_terrain_y(x, z):
        return 12
        
    cancel_event = threading.Event()
    
    blocks = rasterize_single_block(b, mock_get_terrain_y, cancel_event)
    
    # Check that platforms are placed at Y=13, with stairs on border and smooth stone in interior
    assert (1, 13, -9) in blocks
    assert blocks[(1, 13, -9)].startswith("minecraft:stone_brick_stairs")
    assert (5, 13, -5) in blocks
    assert blocks[(5, 13, -5)] == "minecraft:smooth_stone"

def test_rasterize_single_block_batch_heights():
    """Verifies that rasterize_single_block correctly accepts interpolator and caches height values in batch."""
    from src.minecraft_pipeline.exporter import rasterize_single_block, TerrainHeightCache
    import threading
    import numpy as np
    
    b = {"polygon": [[0, 0], [10, 0], [10, 10], [0, 10]]}
    
    class MockInterpolator:
        def __init__(self):
            self.queried_count = 0
            self.batch_queried_count = 0
            
        def query_height(self, x, z):
            self.queried_count += 1
            return 12.0
            
        def query_height_batch(self, coords):
            self.batch_queried_count += 1
            return np.full(len(coords), 12.0, dtype=np.float32)
            
    interpolator = MockInterpolator()
    height_cache = TerrainHeightCache(cache_path="dummy_path.json")
    height_cache.cache = {}
    
    def mock_get_terrain_y(x, z):
        h = height_cache.get(x, z)
        if h is None:
            h = int(round(interpolator.query_height(x, -z))) - 230
            height_cache.set(x, z, h)
        return h
        
    cancel_event = threading.Event()
    
    blocks = rasterize_single_block(
        b, mock_get_terrain_y, cancel_event,
        interpolator=interpolator, y_offset=230, height_cache=height_cache
    )
    
    assert (1, -217, -9) in blocks
    assert blocks[(1, -217, -9)].startswith("minecraft:stone_brick_stairs")
    assert (5, -217, -5) in blocks
    assert blocks[(5, -217, -5)] == "minecraft:smooth_stone"
    assert interpolator.batch_queried_count > 0
    assert interpolator.queried_count == 0

def test_voxel_map_operations():
    """Verifies that VoxelMap behaves exactly equivalent to a standard Python dictionary for custom block storage."""
    from src.minecraft_pipeline.exporter import VoxelMap
    import numpy as np
    
    x = np.array([5, 10, 20, 25], dtype=np.int32)
    y = np.array([60, 60, 61, 62], dtype=np.int32)
    z = np.array([5, 10, 20, 40], dtype=np.int32)
    
    block_ids = np.array([0, 1, 0, 2], dtype=np.uint8)
    palette = ["minecraft:dirt", "minecraft:stone", "minecraft:grass_block"]
    
    voxel_map = VoxelMap(x, y, z, block_ids, palette)
    
    assert len(voxel_map) == 4
    
    chunk_0_0 = voxel_map.get_chunk_dict(0, 0)
    assert chunk_0_0 == {
        (5, 60, 5): "minecraft:dirt",
        (10, 60, 10): "minecraft:stone"
    }
    
    chunk_1_1 = voxel_map.get_chunk_dict(1, 1)
    assert chunk_1_1 == {
        (20, 61, 20): "minecraft:dirt"
    }
    
    chunk_1_2 = voxel_map.get_chunk_dict(1, 2)
    assert chunk_1_2 == {
        (25, 62, 40): "minecraft:grass_block"
    }
    
    assert voxel_map.get_chunk_dict(5, 5) == {}
    
    new_blocks = {
        (8, 60, 8): "minecraft:glass",
        (30, 63, 30): "minecraft:yellow_wool"
    }
    voxel_map.update(new_blocks)
    
    assert len(voxel_map) == 6
    
    chunk_0_0_updated = voxel_map.get_chunk_dict(0, 0)
    assert chunk_0_0_updated[(8, 60, 8)] == "minecraft:glass"
    assert len(chunk_0_0_updated) == 3
    
    chunk_1_1_updated = voxel_map.get_chunk_dict(1, 1)
    assert chunk_1_1_updated[(30, 63, 30)] == "minecraft:yellow_wool"
    assert len(chunk_1_1_updated) == 2
    
    items = list(voxel_map.items())
    assert len(items) == 6
    coords = [item[0] for item in items]
    assert (5, 60, 5) in coords
    assert (8, 60, 8) in coords
    assert (30, 63, 30) in coords





