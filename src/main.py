import argparse
import sys
import os
import math
import numpy as np
from PIL import Image

from src.core_io.coords import gps_to_local, local_to_gps
from src.core_io.io_manager import ensure_dir
from src.data_acquisition.sv_downloader import StreetViewDownloader
from src.data_acquisition.sv_procedural import ProceduralStreetViewGenerator
from src.gis_graph.graph_builder import TecateGraphBuilder
from src.image_alignment.aligner import ImageAligner
from src.temporal_filter.classifier import TemporalVisualClassifier, TemporalMRFSolver
from src.sfm.sfm_lite import SfMLite
from src.block_modeling.block_builder import BlockBuilder
from src.texturing.texture_generator import TextureGenerator
from src.blender_export.exporter import BlenderSceneExporter

def run_pipeline(args):
    print("=" * 60)
    print("      TECATE 2009 HISTORICAL URBAN RECONSTRUCTION PIPELINE")
    print("=" * 60)
    print(f"Mode: {args.mode.upper()}")
    print(f"Sampling Interval: {args.interval} meters")
    print(f"Feature Extractor: {args.feature_type}")
    print(f"Output File: {args.output}")
    print("-" * 60)

    # Make sure output directories exist
    ensure_dir("export/textures")

    # 1. BUILD ROAD GRAPH FROM OSM
    builder = TecateGraphBuilder(cache_dir="data")
    osm_data = builder.fetch_osm_tecate()
    G = builder.build_networkx_graph(osm_data)
    camera_stations = builder.normalize_and_sample_edges(G, interval_meters=args.interval)
    
    print(f"[GIS] Loaded road graph: {G.number_of_nodes()} intersections, {G.number_of_edges()} road segments.")
    print(f"[GIS] Placed {len(camera_stations)} virtual camera stations along segments.")

    # 2. ACQUIRE STREET VIEW PANORAMAS
    raw_panos = []
    pano_registry = {}  # Map station_id -> panorama details
    
    if args.mode == "real":
        downloader = StreetViewDownloader(api_key=args.api_key)
        if not downloader.has_api_key():
            print("[Error] A valid Google Street View API key is required for 'real' mode.")
            print("Please supply it via --api-key or use '--mode simulated'.")
            sys.exit(1)
            
        print("[Acquisition] Running real scraper pipeline from Google Street View...")
        for station in camera_stations:
            lat = station["latitude"]
            lon = station["longitude"]
            pano = downloader.fetch_full_panorama(lat, lon)
            if pano:
                # Store the station alignment directly
                pano["station_id"] = station["station_id"]
                raw_panos.append(pano)
                pano_registry[station["station_id"]] = pano
                print(f" -> Acquired real panorama {pano['pano_id']} for {station['station_id']} (Captured: {pano['date']})")
    else:
        # SIMULATED MODE
        print("[Acquisition] Running procedural generator for simulated Tecate Street View...")
        generator = ProceduralStreetViewGenerator(seed=42)
        
        # We will generate panoramas for each camera station.
        # To test our temporal filtering module, we will intentionally tag a few camera stations
        # as modern (e.g., stations along edge 'e_j2' or 'e_pc2') and others as circa 2009.
        for idx, station in enumerate(camera_stations):
            edge_id = station["edge_id"]
            dist_along = station["dist_along"]
            
            # Retrieve the length of the edge from the graph
            # In MultiGraph, G.edges(u, v, key) or we can search by edge attribute
            edge_len = 80.0
            for u, v, data in G.edges(data=True):
                if data["id"] == edge_id:
                    edge_len = data["length"]
                    break
            
            # Generate deterministic facade elements along the street edge
            facade_elements = generator.generate_facade_elements(edge_id, edge_len)
            
            # Let's inject a strict temporal split to test the pipeline:
            # We set one specific avenue (e_j2: Avenida Juárez East) and street (e_pc2: Calle Cárdenas South)
            # to be Modern (captured in 2026), and all other streets to be historical (2009).
            is_modern_segment = (edge_id in ["e_j2", "e_pc2"])
            is_2009 = not is_modern_segment
            
            pano_img = generator.render_panorama(dist_along, edge_id, edge_len, facade_elements, is_2009)
            
            pano_id = f"sim_pano_{idx:03d}_{'2009' if is_2009 else '2026'}"
            date_str = "2009-08" if is_2009 else "2026-02"
            
            # Set initial metadata probability
            # 2009 panoramas have high probability; modern have near 0.05
            init_prob = 0.90 if is_2009 else 0.05
            
            pano_data = {
                "latitude": station["latitude"],
                "longitude": station["longitude"],
                "pano_id": pano_id,
                "date": date_str,
                "temporal_probability": init_prob,
                "image": pano_img,
                "station_id": station["station_id"],
                "edge_id": edge_id,
                "dist_along": dist_along
            }
            raw_panos.append(pano_data)
            pano_registry[station["station_id"]] = pano_data
            
        print(f"[Acquisition] Procedurally generated {len(raw_panos)} high-fidelity panoramas of Tecate facades.")

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
            accepted_registry[s_id] = pano_registry[s_id]
            
    print(f"[Temporal Filter] Enforced strict 2009 constraint. Filtered out non-2009. Accepted: {len(accepted_registry)} / {len(aligned_panos)} panoramas.")

    # 5. OpenCV STRUCTURE-FROM-MOTION LITE
    print("[SfM] Commencing classical vision Structure-from-Motion pipeline...")
    sfm = SfMLite(feature_type=args.feature_type)
    global_point_cloud = []
    
    # Gather pairs of adjacent cameras along the same edges
    # Sort aligned panoramas along edges
    edge_panos = {}
    for fp in filtered_panos:
        if not fp["accepted"]:
            continue
        edge_id = fp["edge_id"]
        if edge_id not in edge_panos:
            edge_panos[edge_id] = []
        edge_panos[edge_id].append(fp)
        
    # Run SfM on adjacent frames along each street segment
    for edge_id, panos_list in edge_panos.items():
        panos_list.sort(key=lambda x: x["dist_along"])
        
        if len(panos_list) < 2:
            continue
            
        print(f" -> Reconstructing corridor {edge_id} ({len(panos_list)} stations)...")
        for i in range(len(panos_list) - 1):
            p1_meta = panos_list[i]
            p2_meta = panos_list[i+1]
            
            s1_id = p1_meta["station_id"]
            s2_id = p2_meta["station_id"]
            
            # Gathers Left (-90 deg) and Right (+90 deg) viewpoint images for stereo-triangulation
            # In a 2560x640 equirectangular image, the left quadrant is pixels [1920, 2560]
            # and the right quadrant is pixels [640, 1280]
            img1 = accepted_registry[s1_id]["image"]
            img2 = accepted_registry[s2_id]["image"]
            
            for side in ["left", "right"]:
                heading_offset = -90.0 if side == "left" else 90.0
                
                # Render perspective viewpoints from the panorama quadrant
                # We crop the quadrant as perspective images of size 640x640
                if side == "left":
                    quad1 = img1.crop((1920, 0, 2560, 640))
                    quad2 = img2.crop((1920, 0, 2560, 640))
                else:
                    quad1 = img1.crop((640, 0, 1280, 640))
                    quad2 = img2.crop((640, 0, 1280, 640))
                    
                # Define global camera poses for coordinate mapping
                pose1 = {
                    "x": p1_meta["graph_x"],
                    "y": p1_meta["graph_y"],
                    "heading": p1_meta["corrected_road_heading"] + heading_offset
                }
                pose2 = {
                    "x": p2_meta["graph_x"],
                    "y": p2_meta["graph_y"],
                    "heading": p2_meta["corrected_road_heading"] + heading_offset
                }
                
                # Recover relative camera motion and triangulate 3D points
                pts3D, colors, matches = sfm.reconstruct_pair(quad1, quad2, pose1, pose2)
                
                if len(pts3D) > 0:
                    for pt, col in zip(pts3D, colors):
                        global_point_cloud.append({
                            "coord": [float(pt[0]), float(pt[1]), float(pt[2])],
                            "color": [float(c) for c in col]
                        })
                        
    print(f"[SfM] Sparse structure-from-motion complete. Triangulated {len(global_point_cloud)} 3D points.")

    # 6. URBAN BLOCK (MANZANA) SEGMENTATION
    print("[Block Modeling] Extracting planar urban block footprints...")
    block_builder = BlockBuilder(G)
    blocks = block_builder.segment_blocks()
    
    # Distribute sparse point clouds and virtual cameras to corresponding urban blocks
    blocks = block_builder.aggregate_points_and_cameras(
        blocks=blocks,
        camera_stations=camera_stations,
        point_cloud=np.array([pt["coord"] for pt in global_point_cloud]) if len(global_point_cloud) > 0 else np.zeros((0, 3)),
        point_colors=np.array([pt["color"] for pt in global_point_cloud]) if len(global_point_cloud) > 0 else np.zeros((0, 3))
    )

    # 7. FACADE TEXTURE RECONSTRUCTION (ATLAS ASSEMBLY)
    print("[Texturing] Running facade texture projection and atlas generation...")
    texturer = TextureGenerator(export_dir="export/textures")
    block_texture_atlases = []
    
    for bl in blocks:
        atlas_data = texturer.process_block_textures(bl, accepted_registry)
        block_texture_atlases.append(atlas_data)
        
    print(f"[Texturing] Assembled {len(block_texture_atlases)} block facade texture atlases from historical imagery.")

    # 8. SCENE EXPORT (INTERMEDIATE REPRESENTATION)
    print("[Export] Packaging output dataset into Blender structured JSON...")
    exporter = BlenderSceneExporter(export_path=args.output)
    export_filepath = exporter.export_scene(
        G=G,
        camera_stations=camera_stations,
        aligned_panos=filtered_panos,
        point_cloud=global_point_cloud,
        blocks=blocks,
        block_texture_atlases=block_texture_atlases
    )
    
    print("-" * 60)
    print("Pipeline Execution Complete!")
    print(f"Structured JSON output saved to: {export_filepath}")
    print("Texture Atlas PNGs generated in: export/textures/")
    print("Proceed to run the Blender import python script inside Blender.")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tecate 2009 Historical Urban Reconstruction Pipeline CLI")
    parser.add_argument("--mode", type=str, choices=["simulated", "real"], default="simulated",
                        help="Execution mode: 'simulated' (procedural dataset) or 'real' (scrapes Google Street View)")
    parser.add_argument("--api-key", type=str, default="",
                        help="Google Street View API Developer Key (required in 'real' mode)")
    parser.add_argument("--interval", type=float, default=10.0,
                        help="Interpolated distance interval between camera positions in meters (default: 10.0)")
    parser.add_argument("--feature-type", type=str, choices=["ORB", "SIFT"], default="ORB",
                        help="Classical CV feature extractor (default: 'ORB')")
    parser.add_argument("--output", type=str, default="export/reconstruction_export.json",
                        help="Output JSON file destination (default: export/reconstruction_export.json)")
    
    args = parser.parse_args()
    run_pipeline(args)
