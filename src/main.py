import argparse
import os
import math
import json
import subprocess
from PIL import Image

from src.core_io.coords import gps_to_local, local_to_gps
from src.core_io.io_manager import ensure_dir
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
    cache_dir = "data/raw_scraped"
    ensure_dir(cache_dir)

    # 1. BUILD ROAD GRAPH FROM OSM
    builder = TecateGraphBuilder(cache_dir="data")
    osm_data = builder.fetch_osm_tecate()
    G = builder.build_networkx_graph(osm_data)
    camera_stations = builder.normalize_and_sample_edges(G, interval_meters=10)
    
    print(f"[GIS] Loaded road graph: {G.number_of_nodes()} intersections, {G.number_of_edges()} road segments.")
    print(f"[GIS] Placed {len(camera_stations)} virtual camera stations along segments.")

    # 2. ACQUIRE STREET VIEW PANORAMAS (PUBLIC WEB SCRAPER & LOCAL ARCHIVAL CACHE)
    raw_panos = []
    pano_registry = {}  # Map station_id -> panorama details
    discovered_nodes = []
    
    if not args.skip_scraper:
        print("[Acquisition] Running Chromium Playwright scraper and public graph crawler...")
        # Start crawler seed exactly at Parque Hidalgo
        seed_lat = 32.573229
        seed_lon = -116.626536
        scraper = GoogleStreetViewScraper(cache_dir=cache_dir, headless=args.headless)
        
        # Crawl priority network centered on Parque Hidalgo within the bounding box
        discovered_nodes = scraper.crawl_priority_network(seed_lat, seed_lon, max_nodes=25)
    else:
        print("[Acquisition] Skipping active Playwright crawling as requested. Using cached raw_scraped nodes.")
        
    # Load ALL existing cached nodes under raw_scraped to utilize full 11GB footprint
    cached_nodes = []
    if os.path.exists(cache_dir):
        for d in os.listdir(cache_dir):
            meta_path = os.path.join(cache_dir, d, "metadata.json")
            image_path = os.path.join(cache_dir, d, "panorama.png")
            if os.path.exists(meta_path) and os.path.exists(image_path):
                 try:
                     with open(meta_path, "r", encoding="utf-8") as f:
                         cached_nodes.append(json.load(f))
                 except Exception:
                     pass
    print(f"[Acquisition] Loaded {len(cached_nodes)} nodes from local cache directory.")
    
    # Merge newly discovered nodes and cached nodes, ensuring uniqueness by pano_id
    unique_nodes = {n["pano_id"]: n for n in cached_nodes}
    for n in discovered_nodes:
        unique_nodes[n["pano_id"]] = n
    discovered_nodes = list(unique_nodes.values())
    
    print(f"[Acquisition] Total unique observational nodes for reconstruction: {len(discovered_nodes)}")
    
    # Distribute unique panoramas back to their closest camera station on the GIS graph
    # (Observation-Driven Sparse Reconstruction: each panorama maps to at most one unique station, preventing duplicates)
    assigned_stations = {}
    for node in discovered_nodes:
        node_x, node_y = gps_to_local(node["latitude"], node["longitude"])
        best_station = None
        min_dist = float("inf")
        
        for station in camera_stations:
            dist = math.sqrt((station["x"] - node_x)**2 + (station["y"] - node_y)**2)
            if dist < min_dist:
                min_dist = dist
                best_station = station
                
        if best_station and min_dist < 45.0:
            s_id = best_station["station_id"]
            if s_id not in assigned_stations or min_dist < assigned_stations[s_id][0]:
                assigned_stations[s_id] = (min_dist, node, best_station)
                
    print(f"[Acquisition] Aligned {len(assigned_stations)} unique observations directly to road graph stations.")
    for s_id, (dist, node, station) in assigned_stations.items():
        image_path = os.path.join(cache_dir, node["pano_id"], "panorama.png")
        if os.path.exists(image_path):
            pano_img = Image.open(image_path)
            
            # Establish metadata temporal probability based on date
            captured_date = node.get("date", "")
            init_prob = 0.05
            if captured_date:
                try:
                    year = int(captured_date.split("-")[0])
                    if year == 2009 or year < 2010:
                        init_prob = 0.90
                except Exception:
                    pass
                    
            pano_data = {
                "latitude": node["latitude"],
                "longitude": node["longitude"],
                "pano_id": node["pano_id"],
                "date": captured_date,
                "temporal_probability": init_prob,
                "image": pano_img,
                "station_id": station["station_id"],
                "edge_id": station["edge_id"],
                "dist_along": station["dist_along"],
                "adjacent_links": node.get("adjacent_links", []),
                "timeline": node.get("timeline", [])
            }
            raw_panos.append(pano_data)
            pano_registry[station["station_id"]] = pano_data

    # 3. IMAGE ANCHORING & ALIGNMENT
    aligner = ImageAligner()
    aligned_panos = []
    
    print("[Alignment] Geospatially anchoring and correcting camera orientations...")
    for pano in raw_panos:
        # Find closest graph coordinates
        aligned_meta = aligner.anchor_to_graph(pano, camera_stations)
        if aligned_meta:
            # Re-estimate vanishing point to correct yaw heading offsets!
            # Since our procedural generator maps lines correctly, we can verify it
            offset = aligner.estimate_vanishing_point_heading_offset(pano["image"])
            aligned_meta["heading_correction"] = float(offset)
            
            # Update registered pose heading
            aligned_meta["corrected_road_heading"] = (aligned_meta["road_heading"] + offset) % 360.0
            
            aligned_panos.append(aligned_meta)
            
    print(f"[Alignment] Successfully anchored {len(aligned_panos)} panoramas to graph. Vanishing point heading offsets evaluated.")

    # 4. TEMPORAL FILTERING LAYER (STRICT 2009 CONSTRAINT)
    print("[Temporal Filter] Applying strict circa 2009 temporal classifier...")
    visual_classifier = TemporalVisualClassifier()
    
    # Update probabilities using visual analysis first (simulates missing timestamps)
    for idx, pano in enumerate(aligned_panos):
        s_id = pano["station_id"]
        raw_pano_img = pano_registry[s_id]["image"]
        
        # Calculate visual 2009 probability from SIFT/ORB/Laplacian metrics
        v_prob = visual_classifier.compute_visual_2009_probability(raw_pano_img)
        
        # Unify: metadata probability + visual probability
        combined_prob = 0.85 * pano["temporal_probability"] + 0.15 * v_prob
        pano["temporal_probability"] = combined_prob
        
    # Solve graph neighborhood consistency using Markov Random Field belief propagation
    mrf_solver = TemporalMRFSolver(G)
    filtered_panos = mrf_solver.solve_temporal_consistency(aligned_panos, alpha=0.55, iterations=8)
    
    # Re-build our registry to only contain accepted 2009-consistent panoramas
    accepted_registry = {}
    for fp in filtered_panos:
        s_id = fp["station_id"]
        if fp["accepted"]:
            pano_details = dict(pano_registry[s_id])
            pano_details["graph_x"] = fp["graph_x"]
            pano_details["graph_y"] = fp["graph_y"]
            pano_details["corrected_road_heading"] = fp["corrected_road_heading"]
            accepted_registry[s_id] = pano_details
            
    print(f"[Temporal Filter] Enforced strict 2009 constraint. Filtered out non-2009. Accepted: {len(accepted_registry)} / {len(aligned_panos)} panoramas.")
    
    # 5. HISTORICAL URBAN BLOCK RECONSTRUCTION & PRISM TEXTURE EXPORT
    print("[Reconstruction] Running prism reconstruction and perspective facade extraction...")
    reconstructor = UrbanBlockReconstructor(G, list(accepted_registry.values()), export_dir="export")
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
                        help="Bypass Playwright browser crawling and load directly from 3,512 cached raw_scraped nodes")
    
    args = parser.parse_args()
    run_pipeline(args)
