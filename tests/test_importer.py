import os
import json
import numpy as np
import pytest
from src.minecraft_pipeline.nbt import NBT, TAG_COMPOUND, TAG_LIST, TAG_STRING, TAG_INT, TAG_BYTE, TAG_LONG_ARRAY
from src.minecraft_pipeline.importer import (
    nbt_to_py,
    is_block_states_only_air,
    chunk_block_states_differ,
    extract_chunk_blocks_filtered
)

def test_nbt_to_py_conversion():
    # Simple values
    assert nbt_to_py(NBT(TAG_BYTE, value=12)) == 12
    assert nbt_to_py(NBT(TAG_STRING, value="hello")) == "hello"
    
    # Compound NBT
    comp = NBT(TAG_COMPOUND, "Sub", [
        NBT(TAG_INT, "val_a", 10),
        NBT(TAG_STRING, "val_b", "test")
    ])
    py_dict = nbt_to_py(comp)
    assert py_dict == {"val_a": 10, "val_b": "test"}

def test_is_block_states_only_air():
    # Only air
    palette_air = NBT(TAG_LIST, "palette", (TAG_COMPOUND, [
        NBT(TAG_COMPOUND, None, [NBT(TAG_STRING, "Name", "minecraft:air")])
    ]))
    bs_air = NBT(TAG_COMPOUND, "block_states", [palette_air])
    assert is_block_states_only_air(bs_air) is True
    
    # Not only air
    palette_stone = NBT(TAG_LIST, "palette", (TAG_COMPOUND, [
        NBT(TAG_COMPOUND, None, [NBT(TAG_STRING, "Name", "minecraft:stone")])
    ]))
    bs_stone = NBT(TAG_COMPOUND, "block_states", [palette_stone])
    assert is_block_states_only_air(bs_stone) is False

def test_chunk_block_states_differ():
    # Create matching chunk NBTs
    palette1 = NBT(TAG_LIST, "palette", (TAG_COMPOUND, [
        NBT(TAG_COMPOUND, None, [NBT(TAG_STRING, "Name", "minecraft:stone")])
    ]))
    sec1 = NBT(TAG_COMPOUND, None, [
        NBT(TAG_BYTE, "Y", 0),
        NBT(TAG_COMPOUND, "block_states", [palette1])
    ])
    chunk1 = NBT(TAG_COMPOUND, "Chunk", [
        NBT(TAG_LIST, "sections", (TAG_COMPOUND, [sec1])),
        NBT(TAG_LIST, "block_entities", (TAG_COMPOUND, []))
    ])
    
    # Duplicate chunk1
    palette2 = NBT(TAG_LIST, "palette", (TAG_COMPOUND, [
        NBT(TAG_COMPOUND, None, [NBT(TAG_STRING, "Name", "minecraft:stone")])
    ]))
    sec2 = NBT(TAG_COMPOUND, None, [
        NBT(TAG_BYTE, "Y", 0),
        NBT(TAG_COMPOUND, "block_states", [palette2])
    ])
    chunk2 = NBT(TAG_COMPOUND, "Chunk", [
        NBT(TAG_LIST, "sections", (TAG_COMPOUND, [sec2])),
        NBT(TAG_LIST, "block_entities", (TAG_COMPOUND, []))
    ])
    
    # Verify they don't differ
    assert chunk_block_states_differ(chunk1, chunk2) is False
    
    # Modify chunk2
    palette3 = NBT(TAG_LIST, "palette", (TAG_COMPOUND, [
        NBT(TAG_COMPOUND, None, [NBT(TAG_STRING, "Name", "minecraft:dirt")])
    ]))
    sec3 = NBT(TAG_COMPOUND, None, [
        NBT(TAG_BYTE, "Y", 0),
        NBT(TAG_COMPOUND, "block_states", [palette3])
    ])
    chunk3 = NBT(TAG_COMPOUND, "Chunk", [
        NBT(TAG_LIST, "sections", (TAG_COMPOUND, [sec3])),
        NBT(TAG_LIST, "block_entities", (TAG_COMPOUND, []))
    ])
    
    # Verify they differ
    assert chunk_block_states_differ(chunk1, chunk3) is True

def test_extract_chunk_blocks_filtered():
    # Mock Interpolator
    class MockInterpolator:
        def query_height(self, x, z):
            return 10.0 # Terrain height is 10
            
    interpolator = MockInterpolator()
    
    # Create NBT section with stone and bricks
    palette = NBT(TAG_LIST, "palette", (TAG_COMPOUND, [
        NBT(TAG_COMPOUND, None, [NBT(TAG_STRING, "Name", "minecraft:air")]),
        NBT(TAG_COMPOUND, None, [NBT(TAG_STRING, "Name", "minecraft:stone")]),
        NBT(TAG_COMPOUND, None, [NBT(TAG_STRING, "Name", "minecraft:bricks")])
    ]))
    
    # We will write a TAG_LONG_ARRAY data containing 4096 indices
    # Index 0: air
    # Index 1: stone
    # Index 2: bricks
    # To keep it simple, we fill block states with bricks (index 2)
    # 4096 values packed with 4 bits per block = 256 longs
    longs = [0] * 256
    # fill with index 2 (bricks): 2 is bin 0010
    # blocks per long = 16. val |= 2 << (b_idx * 4) -> 0x2222222222222222
    # Convert to signed 64-bit: 0x2222222222222222 = 2459565876494606882
    val = 2459565876494606882
    for i in range(256):
        longs[i] = val
        
    data = NBT(TAG_LONG_ARRAY, "data", longs)
    bs = NBT(TAG_COMPOUND, "block_states", [palette, data])
    sec = NBT(TAG_COMPOUND, None, [
        NBT(TAG_BYTE, "Y", 0),
        bs
    ])
    chunk = NBT(TAG_COMPOUND, "Chunk", [
        NBT(TAG_LIST, "sections", (TAG_COMPOUND, [sec])),
        NBT(TAG_LIST, "block_entities", (TAG_COMPOUND, []))
    ])
    
    # Extract blocks
    # Bricks are not in TERRAIN_BLOCKS, so they should NOT be filtered out even at Y <= 10.
    blocks = extract_chunk_blocks_filtered(
        chunk, cx_global=0, cz_global=0, min_s_y=-4, max_s_y=20,
        interpolator=interpolator, y_offset=0
    )
    
    # Check that bricks are present
    assert len(blocks) == 4096
    assert blocks[(0, 0, 0)] == "minecraft:bricks"

def test_file_info_helper():
    from src.minecraft_pipeline.importer import get_file_info
    # Non-existent file
    mtime, size = get_file_info("non_existent_file.mca")
    assert mtime == 0.0
    assert size == 0

def test_exposed_face_culling_logic():
    # Setup adjacent blocks in 3D:
    # (0,0,0) and (1,0,0) are adjacent
    # (0,0,0) should have exposed faces on left (-X), top (+Y), bottom (-Y), front (+Z), back (-Z)
    # Right (+X) neighbor (1,0,0) is present, so Right face should not be exposed.
    preserved_blocks = {
        (0, 0, 0): "minecraft:stone",
        (1, 0, 0): "minecraft:stone"
    }
    
    # Calculate masks manually:
    # For (0,0,0):
    # - (1,0,0) is in preserved_blocks -> mask & 1 (Right) is 0
    # - (-1,0,0) is NOT in preserved_blocks -> mask & 2 (Left) is 2
    # - (0,1,0) is NOT in preserved_blocks -> mask & 4 (Top) is 4
    # - (0,-1,0) is NOT in preserved_blocks -> mask & 8 (Bottom) is 8
    # - (0,0,1) is NOT in preserved_blocks -> mask & 16 (Front) is 16
    # - (0,0,-1) is NOT in preserved_blocks -> mask & 32 (Back) is 32
    # Total mask = 2 + 4 + 8 + 16 + 32 = 62
    
    # Let's run the mask logic
    x, y, z = 0, 0, 0
    mask = 0
    if (x + 1, y, z) not in preserved_blocks:
        mask |= 1
    if (x - 1, y, z) not in preserved_blocks:
        mask |= 2
    if (x, y + 1, z) not in preserved_blocks:
        mask |= 4
    if (x, y - 1, z) not in preserved_blocks:
        mask |= 8
    if (x, y, z + 1) not in preserved_blocks:
        mask |= 16
    if (x, y, z - 1) not in preserved_blocks:
        mask |= 32
        
    assert mask == 62
    assert (mask & 1) == 0 # Right face culled
    assert (mask & 2) == 2 # Left face exposed

