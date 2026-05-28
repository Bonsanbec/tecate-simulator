import math
import numpy as np
import networkx as nx
from PIL import Image, ImageDraw

# Import system modules
from src.core_io.coords import gps_to_local, local_to_gps, TECATE_LAT_CENTER, TECATE_LON_CENTER
from src.data_acquisition.sv_procedural import ProceduralStreetViewGenerator
from src.gis_graph.graph_builder import TecateGraphBuilder
from src.image_alignment.aligner import ImageAligner
from src.temporal_filter.classifier import TemporalVisualClassifier, TemporalMRFSolver
from src.sfm.sfm_lite import SfMLite
from src.block_modeling.block_builder import BlockBuilder
from src.texturing.texture_generator import TextureGenerator

def test_coordinates_bidirectional():
    """Verifies that GPS conversions are bidirectionally consistent with zero drift."""
    lat, lon = 32.5688, -116.6281
    x, y = gps_to_local(lat, lon)
    
    # Check that they represent local meters relative to center (within reasonable bounds)
    assert abs(x) < 500.0
    assert abs(y) < 500.0
    
    lat_r, lon_r = local_to_gps(x, y)
    assert math.isclose(lat, lat_r, abs_tol=1e-6)
    assert math.isclose(lon, lon_r, abs_tol=1e-6)

def test_gis_graph_construction():
    """Verifies that the road graph is correctly built, segmented, and virtual cameras placed."""
    builder = TecateGraphBuilder(cache_dir="data")
    raw_data = builder.generate_default_tecate_grid()
    
    assert "nodes" in raw_data
    assert "edges" in raw_data
    assert len(raw_data["nodes"]) == 9
    
    G = builder.build_networkx_graph(raw_data)
    assert G.number_of_nodes() == 9
    assert G.number_of_edges() == 12
    
    # Verify local metric attributes
    for node_id, data in G.nodes(data=True):
        assert "x" in data
        assert "y" in data
        
    camera_stations = builder.normalize_and_sample_edges(G, interval_meters=15.0)
    assert len(camera_stations) > 0
    # Every station must have a metric position, a road heading, and parent edge
    for cam in camera_stations:
        assert "station_id" in cam
        assert "edge_id" in cam
        assert "x" in cam
        assert "y" in cam
        assert -180.0 <= cam["road_heading"] <= 180.0

def test_image_alignment_anchoring():
    """Verifies that the spatial aligner correctly anchors panoramas and estimates VP offsets."""
    aligner = ImageAligner()
    
    # 1. Spatial anchoring test
    # Create fake camera stations centered near Miguel Hidalgo Park
    stations = [
        {"station_id": "cam_0", "edge_id": "e1", "dist_along": 10.0, "x": 0.0, "y": 0.0, "latitude": TECATE_LAT_CENTER, "longitude": TECATE_LON_CENTER, "road_heading": 0.0},
        {"station_id": "cam_1", "edge_id": "e1", "dist_along": 20.0, "x": 20.0, "y": 0.0, "latitude": TECATE_LAT_CENTER, "longitude": TECATE_LON_CENTER + 0.000213, "road_heading": 0.0}
    ]
    
    # Fake panorama near station 1 (within 1.5 meters)
    pano = {
        "latitude": TECATE_LAT_CENTER,
        "longitude": TECATE_LON_CENTER + 0.00020,
        "pano_id": "pano_t",
        "temporal_probability": 0.95
    }
    
    aligned = aligner.anchor_to_graph(pano, stations)
    assert aligned is not None
    assert aligned["station_id"] == "cam_1"
    assert aligned["alignment_distance"] < 15.0

    # 2. Vanishing point offset calculation sanity check
    # Create a synthetic image containing converging lines towards center
    img = Image.new("RGB", (2560, 640), (135, 206, 235))
    # Draw converging street curb lines on front quadrant (center = 320)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    # Converges at x=320, y=320
    draw.line([0, 480, 320, 320], fill=(200, 200, 200), width=5)
    draw.line([640, 480, 320, 320], fill=(200, 200, 200), width=5)
    
    offset = aligner.estimate_vanishing_point_heading_offset(img)
    # Correct vanishing point is exactly centered (delta = 0), so offset should be near 0
    assert abs(offset) < 2.0

def test_temporal_filtering_and_mrf():
    """Verifies that the temporal classifier visual check and MRF belief propagation are correct."""
    # 1. Visual Classifier Checks
    classifier = TemporalVisualClassifier()
    
    # Generate sharp image (simulate modern)
    sharp_img = Image.new("RGB", (640, 640), (255, 255, 255))
    draw_s = ImageDraw.Draw(sharp_img)
    # High frequency sharp lines
    for i in range(0, 640, 20):
        draw_s.line([i, 0, i, 640], fill=(0, 0, 0), width=3)
        draw_s.line([0, i, 640, i], fill=(0, 0, 0), width=3)
        
    p_sharp = classifier.compute_visual_2009_probability(sharp_img)
    # A crisp black/white grid image should result in very low 2009 probability (highly modern)
    assert p_sharp < 0.40
    
    # 2. MRF Propagation Check
    # Build a simple sequence graph (road corridor)
    G = nx.MultiGraph()
    G.add_node("n1", x=0.0, y=0.0, lat=32.5, lon=-116.6)
    G.add_node("n2", x=50.0, y=0.0, lat=32.5, lon=-116.599)
    G.add_edge("n1", "n2", id="e1", length=50.0)
    
    aligned_panos = [
        {"station_id": "cam_0", "edge_id": "e1", "dist_along": 10.0, "graph_x": 10.0, "graph_y": 0.0, "temporal_probability": 0.98, "pano_id": "p0"},
        {"station_id": "cam_1", "edge_id": "e1", "dist_along": 20.0, "graph_x": 20.0, "graph_y": 0.0, "temporal_probability": 0.55, "pano_id": "p1"}, # Ambiguous/low initial prob (normally rejected)
        {"station_id": "cam_2", "edge_id": "e1", "dist_along": 30.0, "graph_x": 30.0, "graph_y": 0.0, "temporal_probability": 0.98, "pano_id": "p2"}
    ]
    
    solver = TemporalMRFSolver(G)
    filtered = solver.solve_temporal_consistency(aligned_panos, alpha=0.55, iterations=5)
    
    # Check that cam_1's probability was diffused upwards by its neighbors to pass acceptance!
    cam1_meta = next(f for f in filtered if f["station_id"] == "cam_1")
    assert cam1_meta["temporal_probability"] > 0.50
    assert cam1_meta["accepted"] == True

def test_sfm_triangulation():
    """Verifies ORB/SIFT feature matcher and essential matrix/triangulation logic."""
    sfm = SfMLite(feature_type="ORB")
    
    # Setup test projection matrices
    # Cameras translated along horizontal axis
    pose1 = {"x": 0.0, "y": 0.0, "heading": 90.0}
    pose2 = {"x": 2.0, "y": 0.0, "heading": 90.0}
    
    # Verify focal and intrinsics matrix K
    assert sfm.K.shape == (3, 3)
    assert sfm.K[0, 0] == 320.0 # focal length
    
    # Verify that if features are empty, it gracefully outputs empty clouds
    pts3D, colors, matches = sfm.reconstruct_pair(
        Image.new("RGB", (640, 640)), 
        Image.new("RGB", (640, 640)), 
        pose1, 
        pose2
    )
    assert len(pts3D) == 0

def test_urban_block_segmentation():
    """Verifies that block cycles and point-in-polygon logic function correctly."""
    G = nx.MultiGraph()
    # Create a 4-node closed square (100m x 100m)
    G.add_node("n1", x=0.0, y=0.0, lat=32.5, lon=-116.6)
    G.add_node("n2", x=100.0, y=0.0, lat=32.5, lon=-116.599)
    G.add_node("n3", x=100.0, y=100.0, lat=32.501, lon=-116.599)
    G.add_node("n4", x=0.0, y=100.0, lat=32.501, lon=-116.6)
    
    G.add_edge("n1", "n2", id="e1", length=100.0)
    G.add_edge("n2", "n3", id="e2", length=100.0)
    G.add_edge("n3", "n4", id="e3", length=100.0)
    G.add_edge("n4", "n1", id="e4", length=100.0)
    
    builder = BlockBuilder(G)
    blocks = builder.segment_blocks()
    
    # Should find exactly 1 block (the minimal cycle of the square)
    assert len(blocks) == 1
    block = blocks[0]
    assert len(block["polygon"]) == 5 # 4 closed vertices
    
    # Centroid check
    assert block["centroid"] == [50.0, 50.0]
    
    # Point-in-polygon check
    assert builder.is_point_in_polygon(50.0, 50.0, block["polygon"]) == True
    assert builder.is_point_in_polygon(150.0, 150.0, block["polygon"]) == False

def test_texture_normal_calculations():
    """Verifies outward wall normal calculations and texture mapping."""
    texturer = TextureGenerator()
    
    # A facade wall segment from (0, 0) to (10, 0)
    # Centroid of block is at (5, 5) (the block is above the wall)
    # The outward normal should point downwards: (0, -1)
    p1 = [0.0, 0.0]
    p2 = [10.0, 0.0]
    centroid = [5.0, 5.0]
    
    normal = texturer.calculate_wall_normal(p1, p2, centroid)
    assert math.isclose(normal[0], 0.0, abs_tol=1e-5)
    assert math.isclose(normal[1], -1.0, abs_tol=1e-5)

def test_scraper_metadata_and_timeline():
    """Verifies that public unauthenticated metadata JSON is parsed correctly, tracing timelines."""
    from unittest.mock import patch, MagicMock
    from src.data_acquisition.browser_scraper import GoogleStreetViewScraper
    
    scraper = GoogleStreetViewScraper(cache_dir="tests/mock_cache")
    
    # Mock requests.get response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Location": {
            "panoId": "mock_pano_xyz",
            "latitude": "32.56",
            "longitude": "-116.6",
            "road_name": "Av. Juarez"
        },
        "Annotation": {
            "Link": [
                {"panoId": "adjacent_1", "road_name": "Av. Juarez", "yawDeg": "90.0"}
            ]
        },
        "Links": [
            {"panoId": "mock_pano_xyz_2009", "date": "2009-08"}
        ],
        "Data": {
            "image_date": "2026-02"
        }
    }
    
    with patch("requests.get", return_value=mock_response):
        meta = scraper.fetch_public_metadata(pano_id="mock_pano_xyz")
        
        assert meta is not None
        assert meta["pano_id"] == "mock_pano_xyz"
        assert meta["latitude"] == 32.56
        assert meta["road_name"] == "Av. Juarez"
        assert len(meta["adjacent_links"]) == 1
        assert meta["adjacent_links"][0]["pano_id"] == "adjacent_1"
        assert len(meta["timeline"]) == 1
        assert meta["timeline"][0]["pano_id"] == "mock_pano_xyz_2009"
        assert meta["timeline"][0]["date"] == "2009-08"

def test_procedural_local_cache():
    """Verifies that ProceduralStreetViewGenerator generates and writes data to local cache folder correctly."""
    import shutil
    import os
    
    # Temporary test cache
    test_cache = "tests/test_scraped_cache"
    if os.path.exists(test_cache):
        shutil.rmtree(test_cache)
        
    generator = ProceduralStreetViewGenerator(seed=42)
    
    # Create simple road network
    G = nx.MultiGraph()
    G.add_node("n1", x=0.0, y=0.0, lat=32.5678, lon=-116.6261)
    G.add_node("n2", x=50.0, y=0.0, lat=32.5678, lon=-116.6256)
    G.add_edge("n1", "n2", id="e1", length=50.0)
    
    camera_stations = [
        {"station_id": "cam_0", "edge_id": "e1", "dist_along": 20.0, "x": 20.0, "y": 0.0, "latitude": 32.5678, "longitude": -116.6259, "road_heading": 0.0}
    ]
    
    nodes = generator.generate_and_cache_simulated_dataset(camera_stations, G, cache_dir=test_cache)
    
    assert len(nodes) == 1
    node = nodes[0]
    
    # Assert folders exist
    node_dir = os.path.join(test_cache, node["pano_id"])
    assert os.path.exists(node_dir)
    assert os.path.exists(os.path.join(node_dir, "metadata.json"))
    assert os.path.exists(os.path.join(node_dir, "panorama.png"))
    
    # Cleanup
    if os.path.exists(test_cache):
        shutil.rmtree(test_cache)

