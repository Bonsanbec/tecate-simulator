import pytest
from src.minecraft_pipeline.exporter import resolve_road_properties

def test_resolve_road_properties_expressway():
    # Expressway/Highway (from name or highway type)
    props1 = resolve_road_properties("Carretera Mexicali - Tijuana", "residential")
    assert props1["width"] == 12.0
    assert props1["lanes"] == 4
    assert props1["surface"] == "asphalt"
    assert props1["marking_type"] == "highway"
    assert not props1["is_rural"]

    props2 = resolve_road_properties("Autopista Centinela", "residential")
    assert props2["width"] == 12.0
    assert props2["lanes"] == 4
    
    props3 = resolve_road_properties("Unnamed Road", "motorway")
    assert props3["width"] == 12.0
    assert props3["lanes"] == 4

def test_resolve_road_properties_boulevard():
    # Boulevard
    props = resolve_road_properties("Boulevard Benito Juárez", "residential")
    assert props["width"] == 14.0
    assert props["lanes"] == 4
    assert props["surface"] == "asphalt_clean"
    assert props["marking_type"] == "boulevard"
    assert not props["is_rural"]

    props2 = resolve_road_properties("Blvrd. Federico", "residential")
    assert props2["width"] == 14.0

def test_resolve_road_properties_avenida():
    # Avenida / Paseo
    props = resolve_road_properties("Avenida 5 de Mayo", "residential")
    assert props["width"] == 9.0
    assert props["lanes"] == 2
    assert props["surface"] == "asphalt"
    assert props["marking_type"] == "avenida"
    assert not props["is_rural"]

    props2 = resolve_road_properties("Paseo Rio Tecate", "residential")
    assert props2["width"] == 9.0

def test_resolve_road_properties_calle():
    # Calle / Callejón
    props = resolve_road_properties("Calle 1 de Mayo", "residential")
    assert props["width"] == 6.0
    assert props["lanes"] == 2
    assert props["surface"] == "asphalt_light"
    assert props["marking_type"] == "calle"
    assert not props["is_rural"]

    props2 = resolve_road_properties("Callejón Libertad", "residential")
    assert props2["width"] == 6.0

def test_resolve_road_properties_unnamed_minor():
    # Unnamed and minor highway type -> rural/unpaved
    props = resolve_road_properties("", "service")
    assert props["width"] == 4.0
    assert props["lanes"] == 1
    assert props["surface"] == "gravel"
    assert props["marking_type"] == "none"
    assert props["is_rural"]

    props2 = resolve_road_properties("", "unclassified")
    assert props2["width"] == 4.0
    assert props2["is_rural"]

def test_resolve_road_properties_fallback():
    # Fallback to standard primary/secondary types
    props = resolve_road_properties("Something Else", "primary")
    assert props["width"] == 10.0
    assert props["lanes"] == 2
    assert props["marking_type"] == "avenida"

    props2 = resolve_road_properties("Something Else", "secondary")
    assert props2["width"] == 8.0
    assert props2["lanes"] == 2
    assert props2["marking_type"] == "calle"

def test_generate_street_signs():
    from src.minecraft_pipeline.exporter import generate_street_signs, VoxelMap
    import numpy as np
    
    # Mock road graph
    road_graph = {
        "nodes": [
            {"id": "n1", "x": 0.0, "y": 0.0},
            {"id": "n2", "x": 20.0, "y": 0.0},
            {"id": "n3", "x": 0.0, "y": 20.0},
            {"id": "n4", "x": 0.0, "y": -20.0}
        ],
        "edges": [
            {"u": "n1", "v": "n2"},
            {"u": "n1", "v": "n3"},
            {"u": "n1", "v": "n4"}
        ]
    }
    
    # Mock edge metadata
    edge_metadata = {
        "n1,n2": {"name": "Avenida Juarez", "highway": "primary"},
        "n1,n3": {"name": "Calle Libertad", "highway": "residential"},
        "n1,n4": {"name": "Calle Libertad", "highway": "residential"}
    }
    
    # Mock node heights
    node_heights = {"n1": 64, "n2": 64, "n3": 64, "n4": 64}
    
    # Mock custom blocks (VoxelMap)
    x_arr = np.array([], dtype=np.int32)
    y_arr = np.array([], dtype=np.int32)
    z_arr = np.array([], dtype=np.int32)
    block_ids = np.array([], dtype=np.int32)
    custom_blocks = VoxelMap(x_arr, y_arr, z_arr, block_ids, [])
    
    # Mock get_mc_terrain_y
    def get_mc_terrain_y(x, z):
        return 64
        
    generate_street_signs(
        road_graph=road_graph,
        edge_metadata=edge_metadata,
        node_heights=node_heights,
        y_offset=0,
        custom_blocks=custom_blocks,
        get_mc_terrain_y=get_mc_terrain_y
    )
    
    # Check that fence blocks and signs are generated
    assert len(custom_blocks.new_blocks_by_chunk) > 0
    
    # Verify that at least one sign was created with correct text
    has_pale_oak_fence = False
    has_wall_sign = False
    for chunk_dict in custom_blocks.new_blocks_by_chunk.values():
        for coord, block_name in chunk_dict.items():
            if "pale_oak_fence" in block_name:
                has_pale_oak_fence = True
            if "pale_oak_wall_sign" in block_name:
                has_wall_sign = True
                
    assert has_pale_oak_fence
    assert has_wall_sign
    assert len(custom_blocks.block_entities) > 0
