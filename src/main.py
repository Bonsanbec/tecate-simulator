import argparse
import os
import math
import json
import subprocess
from PIL import Image

from src.core_io.coords import gps_to_local, local_to_gps
from src.core_io.io_manager import ensure_dir, load_json
from src.data_acquisition.browser_scraper import GoogleStreetViewScraper
from src.data_acquisition.sv_procedural import ProceduralStreetViewGenerator
from src.gis_graph.graph_builder import TecateGraphBuilder
from src.image_alignment.aligner import ImageAligner
from src.temporal_filter.classifier import TemporalVisualClassifier, TemporalMRFSolver
from src.reconstruction.prism_generator import UrbanBlockReconstructor

def run_blender_export():
    """Locates and runs the Blender background script to compile geometry.glb."""
    blender_path = "blender"
    
    # Common macOS paths for Blender
    mac_paths = [
        "/Applications/Blender.app/Contents/MacOS/Blender",
        "/Applications/Blender.app/Contents/MacOS/blender",
        os.path.expanduser("~/Applications/Blender.app/Contents/MacOS/Blender")
    ]
    for path in mac_paths:
        if os.path.exists(path):
            blender_path = path
            break
            
    print(f"[Blender Compiler] Compiling geometry.glb using Blender: '{blender_path}'")
    try:
        res = subprocess.run(
            [blender_path, "--background", "--python", "blender_script.py", "--", "--import", "export/reconstruction_export.json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if res.returncode == 0:
            print("[Blender Compiler] Successfully compiled geometry.glb!")
        else:
            print(f"[Warning] Blender compilation returned non-zero exit code: {res.returncode}")
            print(res.stdout)
            print(res.stderr)
    except Exception as e:
        print(f"[Warning] Failed to automatically run Blender compiler: {e}")
        print("Please run manually: blender --background --python blender_script.py -- --import export/reconstruction_export.json")

def run_pipeline(args):
    print("=" * 60)
    print("      TECATE 2009 HISTORICAL URBAN RECONSTRUCTION PIPELINE")
    print("=" * 60)
    print("-" * 60)

    # Make sure output directories exist
    ensure_dir("export/textures")

    # 1. BUILD ROAD GRAPH FROM OSM
    builder = TecateGraphBuilder(cache_dir="data")
    osm_data = builder.fetch_osm_tecate()
    G = builder.build_networkx_graph(osm_data)
    camera_stations = builder.normalize_and_sample_edges(G, interval_meters=10)
    
    print(f"[GIS] Loaded road graph: {G.number_of_nodes()} intersections, {G.number_of_edges()} road segments.")
    print(f"[GIS] Placed {len(camera_stations)} virtual camera stations along segments.")

    # 2. ACQUIRE STREET VIEW PANORAMAS (CRAWLER TRAVERSAL)
    discovered_nodes = []
    scraper = None
    if not args.skip_scraper:
        print("[Acquisition] Running Playwright scraper and public graph crawler...")
        seed_lat = 32.573229
        seed_lon = -116.626536
        scraper = GoogleStreetViewScraper(headless=args.headless, G=G)
        discovered_nodes = scraper.crawl_priority_network(seed_lat, seed_lon, max_nodes=25)
    else:
        print("[Acquisition] Skipping active Playwright crawling. Proceeding to migrate cache.")
        
    if args.harvest_only:
        print("\n" + "="*60)
        visited_count = len(scraper.visited_panos) if scraper else 0
        print(f"[Harvest Mode] Scraping and data harvesting complete. Scraped and cached {visited_count} total nodes under Layer 1/2 structures.")
        print("[Harvest Mode] Skipping all downstream filtering, homography mapping, and Blender 3D reconstruction.")
        print("="*60 + "\n")
        return

    # 3. RUN LAYER 1 & LAYER 2 ARCHIVAL DATA MIGRATION
    # Idempotent, deterministic migration. Will transiently stitch new crawler nodes
    # and extract Layer 2 frontal observations, deprecating persistent raw panoramas.
    from src.core_io.migration import ArchivalDataMigrator
    migrator = ArchivalDataMigrator(raw_cache_dir="data/raw_scraped", data_dir="data")
    # Cap processing to prevent time limits
    migrator.run_migration(max_observations_to_process=120)

    # Load migrated Layer 1 structures
    intersections = load_json("data/structural_graph/intersections.json")
    road_graph = load_json("data/structural_graph/road_graph.json")
    adjacency = load_json("data/structural_graph/adjacency.json")

    # 4. TEMPORAL FILTERING LAYER (STRICT 2009 CONSTRAINT)
    print("[Temporal Filter] Applying strict circa 2009 temporal classifier...")
    
    # Construct the panorama structural graph nodes to run MRF belief propagation
    # We collect all raw scraped nodes metadata from the structural graph panos directory
    mrf_nodes = []
    pano_meta_dir = "data/structural_graph/panos"
    scraped_meta_files = os.listdir(pano_meta_dir) if os.path.exists(pano_meta_dir) else []
    
    for f_name in scraped_meta_files:
        if f_name.endswith(".json"):
            m_path = os.path.join(pano_meta_dir, f_name)
            if os.path.exists(m_path):
                try:
                    meta = load_json(m_path)
                    p_id = meta["pano_id"]
                    
                    # Establish metadata temporal probability based on date
                    captured_date = meta.get("date", "")
                    init_prob = 0.05
                    if captured_date:
                        try:
                            year = int(captured_date.split("-")[0])
                            if year == 2009 or year < 2010:
                                init_prob = 0.90
                        except Exception:
                            pass
                            
                    # Determine its spatial position
                    node_x, node_y = gps_to_local(meta["latitude"], meta["longitude"])
                    
                    # Assign to closest camera station
                    best_station = None
                    min_dist = float("inf")
                    for station in camera_stations:
                        dist = math.sqrt((station["x"] - node_x)**2 + (station["y"] - node_y)**2)
                        if dist < min_dist:
                            min_dist = dist
                            best_station = station
                            
                    if best_station and min_dist < 45.0:
                        mrf_nodes.append({
                            "pano_id": p_id,
                            "station_id": best_station["station_id"],
                            "edge_id": best_station["edge_id"],
                            "dist_along": best_station["dist_along"],
                            "graph_x": best_station["x"],
                            "graph_y": best_station["y"],
                            "latitude": meta["latitude"],
                            "longitude": meta["longitude"],
                            "temporal_probability": init_prob,
                            "road_heading": best_station["road_heading"],
                            "corrected_road_heading": best_station["road_heading"],
                            "adjacent_links": meta.get("adjacent_links", [])
                        })
                except Exception:
                    pass

    print(f"[Temporal Filter] Running MRF Solver over {len(mrf_nodes)} structural reference nodes...")
    mrf_solver = TemporalMRFSolver(G)
    filtered_panos = mrf_solver.solve_temporal_consistency(mrf_nodes, alpha=0.55, iterations=8)
    
    # Register accepted panoramas
    accepted_pano_ids = set([fp["pano_id"] for fp in filtered_panos if fp.get("accepted", False)])
    print(f"[Temporal Filter] Accepted {len(accepted_pano_ids)} / {len(mrf_nodes)} panoramas as circa-2009 consistent.")

    # 5. HISTORICAL URBAN BLOCK RECONSTRUCTION (FACADE-OBSERVATION-NATIVE)
    print("[Reconstruction] Running facade-observation-native block prism reconstruction...")
    
    reconstructor = UrbanBlockReconstructor(G, export_dir="export")
    # Filter reconstructor panoramas to only keep accepted temporal ones
    reconstructor.panoramas = [p for p in reconstructor.panoramas if p["pano_id"] in accepted_pano_ids]
    
    print(f"[Reconstruction] Feeding {len(reconstructor.panoramas)} accepted panoramas to geometry generator.")
    blocks_data, scene_doc = reconstructor.reconstruct_blocks_and_texture()
    
    export_filepath = "export/reconstruction_export.json"
    with open(export_filepath, "w", encoding="utf-8") as f:
        json.dump(scene_doc, f, indent=4)
    print(f"[Reconstruction] Exported block prism meshes and graph metadata to: {export_filepath}")

    # LAST. GENERATE SPATIAL DIAGNOSTIC VISUALIZATION (coverage_map.png)
    try:
        from src.visualization.coverage import SpatialCoverageVisualizer
        visualizer = SpatialCoverageVisualizer()
        visualizer.draw_coverage_map(
            G=G,
            panoramas=filtered_panos,
            blocks=blocks_data,
            output_path="coverage_map.png"
        )
    except Exception as viz_err:
        print(f"[Warning] Failed to generate spatial coverage map: {viz_err}")
    
    print("-" * 60)
    print("Pipeline Execution Complete!")
    print("Texture Atlas PNGs generated in: export/textures/")
    
    # 6. TRIGGER BLENDER COMPILATION
    run_blender_export()
    
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tecate 2009 Historical Urban Reconstruction Pipeline CLI")
    parser.add_argument("--headless", action="store_true", default=False,
                        help="Run Playwright Chromium browser in headless mode (default: False to support WebGL on Mac)")
    parser.add_argument("--skip-scraper", action="store_true", default=False,
                        help="Bypass Playwright browser crawling and load directly from cached structural_graph nodes")
    parser.add_argument("--harvest-only", action="store_true", default=False,
                        help="Harvest data mode: performs scraping/crawling but skips all processing, filtering, and 3D reconstruction.")
    
    args = parser.parse_args()
    run_pipeline(args)
