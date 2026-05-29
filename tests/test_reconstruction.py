import os
import json
import math
import shutil
import numpy as np
import networkx as nx
from PIL import Image, ImageDraw

from src.core_io.coords import gps_to_local, local_to_gps, TECATE_LAT_CENTER, TECATE_LON_CENTER
from src.core_io.io_manager import load_json, save_json
from src.gis_graph.graph_builder import TecateGraphBuilder
from src.image_alignment.aligner import ImageAligner
from src.image_alignment.virtual_camera import project_rectilinear
from src.image_alignment.visibility_filter import analyze_visibility_quality
from src.core_io.migration import ArchivalDataMigrator
from src.temporal_filter.classifier import TemporalVisualClassifier, TemporalMRFSolver
from src.reconstruction.prism_generator import UrbanBlockReconstructor

def test_coordinates_bidirectional():
    """Verifies that GPS conversions are bidirectionally consistent with zero drift."""
    lat, lon = 32.5688, -116.6281
    x, y = gps_to_local(lat, lon)
    
    assert abs(x) < 2000.0
    assert abs(y) < 2000.0
    
    lat_r, lon_r = local_to_gps(x, y)
    assert math.isclose(lat, lat_r, abs_tol=1e-6)
    assert math.isclose(lon, lon_r, abs_tol=1e-6)

def test_gis_graph_construction():
    """Verifies that the road graph is correctly built and virtual cameras placed."""
    builder = TecateGraphBuilder(cache_dir="data")
    raw_data = builder.generate_default_tecate_grid()
    
    assert "nodes" in raw_data
    assert "edges" in raw_data
    assert len(raw_data["nodes"]) == 225
    
    G = builder.build_networkx_graph(raw_data)
    assert G.number_of_nodes() == 225
    assert G.number_of_edges() == 420
    
    camera_stations = builder.normalize_and_sample_edges(G, interval_meters=15.0)
    assert len(camera_stations) > 0
    for cam in camera_stations:
        assert "station_id" in cam
        assert "edge_id" in cam
        assert "x" in cam
        assert "y" in cam
        assert -180.0 <= cam["road_heading"] <= 180.0

def test_image_alignment_anchoring():
    """Verifies that the spatial aligner correctly anchors panoramas and estimates VP offsets."""
    aligner = ImageAligner()
    
    stations = [
        {"station_id": "cam_0", "edge_id": "e1", "dist_along": 10.0, "x": 0.0, "y": 0.0, "latitude": TECATE_LAT_CENTER, "longitude": TECATE_LON_CENTER, "road_heading": 0.0},
        {"station_id": "cam_1", "edge_id": "e1", "dist_along": 20.0, "x": 20.0, "y": 0.0, "latitude": TECATE_LAT_CENTER, "longitude": TECATE_LON_CENTER + 0.000213, "road_heading": 0.0}
    ]
    
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

    # Vanishing point offset calculation sanity check
    img = Image.new("RGB", (2560, 640), (135, 206, 235))
    draw = ImageDraw.Draw(img)
    # Converges at x=320, y=320 in front quadrant
    draw.line([0, 480, 320, 320], fill=(200, 200, 200), width=5)
    draw.line([640, 480, 320, 320], fill=(200, 200, 200), width=5)
    
    offset = aligner.estimate_vanishing_point_heading_offset(img)
    assert abs(offset) < 2.0

def test_temporal_filtering_and_mrf():
    """Verifies that the temporal classifier visual check and MRF belief propagation are correct."""
    classifier = TemporalVisualClassifier()
    
    # Generate sharp image (simulate modern)
    sharp_img = Image.new("RGB", (640, 640), (255, 255, 255))
    draw_s = ImageDraw.Draw(sharp_img)
    for i in range(0, 640, 20):
        draw_s.line([i, 0, i, 640], fill=(0, 0, 0), width=3)
        draw_s.line([0, i, 640, i], fill=(0, 0, 0), width=3)
        
    p_sharp = classifier.compute_visual_2009_probability(sharp_img)
    assert p_sharp < 0.40
    
    G = nx.MultiGraph()
    G.add_node("n1", x=0.0, y=0.0, lat=32.5, lon=-116.6)
    G.add_node("n2", x=50.0, y=0.0, lat=32.5, lon=-116.599)
    G.add_edge("n1", "n2", id="e1", length=50.0)
    
    aligned_panos = [
        {"station_id": "cam_0", "edge_id": "e1", "dist_along": 10.0, "graph_x": 10.0, "graph_y": 0.0, "temporal_probability": 0.98, "pano_id": "p0"},
        {"station_id": "cam_1", "edge_id": "e1", "dist_along": 20.0, "graph_x": 20.0, "graph_y": 0.0, "temporal_probability": 0.55, "pano_id": "p1"},
        {"station_id": "cam_2", "edge_id": "e1", "dist_along": 30.0, "graph_x": 30.0, "graph_y": 0.0, "temporal_probability": 0.98, "pano_id": "p2"}
    ]
    
    solver = TemporalMRFSolver(G)
    filtered = solver.solve_temporal_consistency(aligned_panos, alpha=0.55, iterations=5)
    
    cam1_meta = next(f for f in filtered if f["station_id"] == "cam_1")
    assert cam1_meta["temporal_probability"] > 0.50
    assert cam1_meta["accepted"] == True

def test_virtual_camera_projection():
    """Verifies that the rectilinear pinhole projection function correctly warps simulated and real formats."""
    # Create simple simulated panorama (2560x640)
    pano = Image.new("RGB", (2560, 640), (135, 206, 235))
    draw = ImageDraw.Draw(pano)
    draw.rectangle([0, 320, 2560, 640], fill=(80, 80, 80)) # asphalt ground
    
    # Project a frontal view
    rect_img = project_rectilinear(
        pano_img=pano,
        yaw_deg=0.0,
        pitch_deg=0.0,
        fov_deg=80.0,
        width=512,
        height=256,
        pano_yaw=0.0,
        is_sim=True
    )
    
    assert rect_img.size == (512, 256)
    # The top of the projected view should be sky (blue), bottom should be ground (grey)
    np_rect = np.array(rect_img)
    assert np.allclose(np_rect[50, 256], [135, 206, 235], atol=10) # Sky
    assert np.allclose(np_rect[200, 256], [80, 80, 80], atol=10) # Ground

def test_visibility_filtering():
    """Verifies that visibility analysis successfully detects sky, pavement, and scores quality."""
    img = Image.new("RGB", (512, 256), (135, 206, 235)) # pure sky
    draw = ImageDraw.Draw(img)
    # Draw some pavement at the bottom
    draw.rectangle([0, 200, 512, 256], fill=(80, 80, 80))
    
    score, diag = analyze_visibility_quality(img)
    
    assert score < 0.20 # Should have very low quality due to pure sky / no vertical building edges
    assert diag["sky_ratio"] > 0.50
    assert diag["pavement_ratio"] > 0.35

def test_migration_and_native_reconstruction():
    """Tests the idempotent migration and facade-observation-native block texturing pipeline together."""
    # Setup temporary mock directories
    test_cache = "tests/test_raw_scraped"
    shutil.rmtree(test_cache, ignore_errors=True)
    shutil.rmtree("tests/test_data", ignore_errors=True)
    shutil.rmtree("tests/test_export", ignore_errors=True)
    
    os.makedirs(test_cache, exist_ok=True)
    
    # Create simple simulated pano
    pano_id = "sim_pano_migration_test"
    node_dir = os.path.join(test_cache, pano_id)
    os.makedirs(node_dir, exist_ok=True)
    
    # Save simulated image and metadata
    pano_img = Image.new("RGB", (2560, 640), (135, 206, 235))
    draw = ImageDraw.Draw(pano_img)
    draw.rectangle([0, 320, 2560, 640], fill=(80, 80, 80))
    # Draw facade vertical lines to boost edge detection score
    for x in range(100, 2400, 150):
        draw.rectangle([x, 200, x+40, 480], fill=(200, 150, 100))
        
    pano_img.save(os.path.join(node_dir, "panorama.png"))
    
    meta = {
        "pano_id": pano_id,
        "latitude": TECATE_LAT_CENTER + 0.0008,
        "longitude": TECATE_LON_CENTER + 0.0008,
        "date": "2009-08",
        "road_name": "Calle A",
        "adjacent_links": [],
        "timeline": []
    }
    with open(os.path.join(node_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4)
        
    # Run migration
    migrator = ArchivalDataMigrator(raw_cache_dir=test_cache, data_dir="tests/test_data")
    res = migrator.run_migration(max_observations_to_process=1)
    
    assert res["processed"] == 1
    # Check that Layer 1 structural files were written
    assert os.path.exists("tests/test_data/structural_graph/intersections.json")
    assert os.path.exists("tests/test_data/structural_graph/road_graph.json")
    assert os.path.exists("tests/test_data/structural_graph/adjacency.json")
    
    # Check that Layer 1 consolidated panorama cache was successfully created
    assert os.path.exists(f"tests/test_data/structural_graph/panos/{pano_id}.png")
    assert os.path.exists(f"tests/test_data/structural_graph/panos/{pano_id}.json")
    
    # Run native block reconstruction
    # Create simple grid graph
    builder = TecateGraphBuilder(cache_dir="tests/test_data")
    raw_graph = builder.generate_default_tecate_grid()
    G = builder.build_networkx_graph(raw_graph)
    
    reconstructor = UrbanBlockReconstructor(G, export_dir="tests/test_export", data_dir="tests/test_data")
    blocks_data, scene_doc = reconstructor.reconstruct_blocks_and_texture()
    
    # Save the output geometry doc to tests/test_export/reconstruction_export.json
    save_json(scene_doc, "tests/test_export/reconstruction_export.json")
    
    assert len(blocks_data) > 0
    # Check that textures were written
    assert len(os.listdir("tests/test_export/textures")) > 0
    assert os.path.exists("tests/test_export/reconstruction_export.json")
    
    # Cleanup test files
    shutil.rmtree(test_cache, ignore_errors=True)
    shutil.rmtree("tests/test_data", ignore_errors=True)
    shutil.rmtree("tests/test_export", ignore_errors=True)


def test_scraper_transient_and_bypass():
    """Verifies that the scraper bypasses image downloads for structural intersections,
    stores longitudinal panoramas in-memory only, and generates Layer 2 observations directly."""
    from src.data_acquisition.browser_scraper import GoogleStreetViewScraper
    from unittest.mock import MagicMock
    
    # 1. Create a mock NetworkX graph G
    G = nx.MultiGraph()
    # Add an intersection node (degree 2) at Parque Hidalgo center
    G.add_node("n_inter", x=0.0, y=0.0, lat=TECATE_LAT_CENTER, lon=TECATE_LON_CENTER)
    G.add_node("n_endpoint1", x=0.0, y=50.0, lat=TECATE_LAT_CENTER + 0.00045, lon=TECATE_LON_CENTER)
    G.add_node("n_endpoint2", x=50.0, y=0.0, lat=TECATE_LAT_CENTER, lon=TECATE_LON_CENTER + 0.00045)
    
    G.add_edge("n_inter", "n_endpoint1", id="e1", length=50.0)
    G.add_edge("n_inter", "n_endpoint2", id="e2", length=50.0)
    
    # Initialize the scraper with the mock graph G
    test_cache = "tests/test_scraper_cache"
    shutil.rmtree(test_cache, ignore_errors=True)
    shutil.rmtree("data/structural_graph", ignore_errors=True)
    shutil.rmtree("data/facade_observations", ignore_errors=True)
    
    scraper = GoogleStreetViewScraper(headless=True, G=G)
    
    # 2. Mock fetch_public_metadata to return node coordinates close to the intersection
    def mock_fetch_public_metadata(pano_id, lat=None, lon=None):
        if pano_id == "pano_intersection":
            return {
                "pano_id": "pano_intersection",
                "latitude": TECATE_LAT_CENTER + 0.00005,  # within 15 meters
                "longitude": TECATE_LON_CENTER + 0.00005,
                "date": "2009-08",
                "adjacent_links": [],
                "timeline": []
            }
        elif pano_id == "pano_longitudinal":
            return {
                "pano_id": "pano_longitudinal",
                "latitude": TECATE_LAT_CENTER + 0.0003,   # ~33 meters away
                "longitude": TECATE_LON_CENTER + 0.0003,
                "date": "2009-08",
                "adjacent_links": [],
                "timeline": []
            }
        return None
        
    scraper.fetch_public_metadata = mock_fetch_public_metadata
    
    # Mock download_and_stitch_tiles to return a simulated image in-memory
    sim_pano = Image.new("RGB", (2560, 640), (135, 206, 235))
    draw = ImageDraw.Draw(sim_pano)
    draw.rectangle([0, 320, 2560, 640], fill=(80, 80, 80))
    for x in range(100, 2400, 150):
        draw.rectangle([x, 200, x+40, 480], fill=(200, 150, 100))
        
    scraper.download_and_stitch_tiles = MagicMock(return_value=sim_pano)
    scraper.save_state = MagicMock()
    
    # 3. Test intersection bypass
    scraper.crawl_queue = [{"pano_id": "pano_intersection", "latitude": TECATE_LAT_CENTER, "longitude": TECATE_LON_CENTER, "priority_distance": 0.0}]
    
    res = scraper.crawl_priority_network(TECATE_LAT_CENTER, TECATE_LON_CENTER, max_nodes=1)
    
    assert len(res) == 1
    assert "pano_intersection" in scraper.visited_panos
    # Assert that download_and_stitch_tiles was NOT called for intersection (zero images requested)
    scraper.download_and_stitch_tiles.assert_not_called()
    
    # Assert that it was registered in structural_graph/adjacency.json
    assert os.path.exists("data/structural_graph/adjacency.json")
    with open("data/structural_graph/adjacency.json", "r") as f:
        adj = json.load(f)
    assert "pano_intersection" in adj["intersection_panos"]
    
    # 4. Test longitudinal node (in-memory only and observation extraction)
    scraper.crawl_queue = [{"pano_id": "pano_longitudinal", "latitude": TECATE_LAT_CENTER + 0.0003, "longitude": TECATE_LON_CENTER + 0.0003, "priority_distance": 1.0}]
    
    res_long = scraper.crawl_priority_network(TECATE_LAT_CENTER, TECATE_LON_CENTER, max_nodes=1)
    
    assert len(res_long) == 1
    assert "pano_longitudinal" in scraper.visited_panos
    # Assert that download_and_stitch_tiles WAS called
    scraper.download_and_stitch_tiles.assert_called_once()
    
    # Assert that no panorama.png file exists on disk under raw cache
    assert not os.path.exists(os.path.join(test_cache, "pano_longitudinal", "panorama.png"))
    
    # Assert that the panorama exists under the consolidated structural cache
    assert os.path.exists("data/structural_graph/panos/pano_longitudinal.png")
    
    # 5. Test Cache Idempotency (running again loads from cache without calling download_and_stitch_tiles again)
    scraper.download_and_stitch_tiles.reset_mock()
    # Remove from visited so it re-crawls, but keep the cache file on disk
    scraper.visited_panos.remove("pano_longitudinal")
    scraper.crawl_queue = [{"pano_id": "pano_longitudinal", "latitude": TECATE_LAT_CENTER + 0.0003, "longitude": TECATE_LON_CENTER + 0.0003, "priority_distance": 1.0}]
    
    res_cached = scraper.crawl_priority_network(TECATE_LAT_CENTER, TECATE_LON_CENTER, max_nodes=1)
    
    assert len(res_cached) == 1
    # Assert that download_and_stitch_tiles was NOT called this time because it loaded from cache
    scraper.download_and_stitch_tiles.assert_not_called()
    
    # Clean up
    shutil.rmtree(test_cache, ignore_errors=True)
    shutil.rmtree("data/structural_graph", ignore_errors=True)
    shutil.rmtree("data/facade_observations", ignore_errors=True)

