import argparse
import os
import math
import json
import subprocess
from PIL import Image

from src.core_io.io_manager import ensure_dir
from src.gis_graph.graph_builder import TecateGraphBuilder
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
    
    print(f"[GIS] Loaded road graph: {G.number_of_nodes()} intersections, {G.number_of_edges()} road segments.")

    # 2. RUN URBAN BLOCK RECONSTRUCTION
    print("[Reconstruction] Running dense orthogonal block prism reconstruction...")
    reconstructor = UrbanBlockReconstructor(
        G, 
        export_dir="export", 
        headless=args.headless,
        radius=args.radius if args.radius >= 0 else None,
        reprocess=args.reprocess
    )
    blocks_data, scene_doc = reconstructor.reconstruct_blocks_and_texture()
    
    export_filepath = "export/reconstruction_export.json"
    with open(export_filepath, "w", encoding="utf-8") as f:
        json.dump(scene_doc, f, indent=4)
    print(f"[Reconstruction] Exported block prism meshes and graph metadata to: {export_filepath}")

    print("-" * 60)
    print("Pipeline Execution Complete!")
    print("Texture Atlas PNGs generated in: export/textures/")
    
    # 3. TRIGGER BLENDER COMPILATION
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
    parser.add_argument("--reprocess", action="store_true", default=False,
                        help="Reprocess cached screenshots (crop, align, stitch) without redownloading them.")
    parser.add_argument("--radius", type=float, default=-1,
                        help="Safety radius centered at (0, 0) in meters. Set to -1 to process the whole city of Tecate.")
    
    args = parser.parse_args()
    run_pipeline(args)
