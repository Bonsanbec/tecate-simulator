import argparse
import os
import math
import json
import subprocess
import sys
import shutil
import glob
from PIL import Image

from src.core_io.io_manager import ensure_dir
from src.gis_graph.graph_builder import TecateGraphBuilder
from src.reconstruction.prism_generator import UrbanBlockReconstructor

def is_wsl():
    """Detects if Python is running under Windows Subsystem for Linux (WSL)."""
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/version", "r") as f:
                content = f.read().lower()
                return "microsoft" in content or "wsl" in content
        except Exception:
            pass
    return False

def is_headless_by_default():
    """Determines if the Playwright browser should launch in headless mode by default."""
    if is_wsl():
        return True
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return True
    return False

def get_windows_path(wsl_path):
    """Converts a WSL path to a Windows path using the wslpath utility."""
    try:
        res = subprocess.run(["wslpath", "-w", wsl_path], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return wsl_path

def translate_paths_to_windows(source_json_path, dest_json_path):
    """
    Reads the exported JSON, translates all WSL absolute paths
    to Windows absolute paths (UNC or drive-letter based),
    and writes them to the destination JSON file.
    """
    if not os.path.exists(source_json_path):
        return False
        
    try:
        repo_dir = os.path.abspath(".")
        windows_repo_dir = get_windows_path(repo_dir)
        if windows_repo_dir == repo_dir:
            # Conversion failed, do not translate
            return False
            
        def to_win_path(path):
            if not path:
                return path
            # If it's already a Windows path, return as is
            if ":" in path or path.startswith("\\\\"):
                return path
            try:
                rel = os.path.relpath(path, repo_dir)
                win_path = os.path.join(windows_repo_dir, rel).replace("/", "\\")
                return win_path
            except Exception:
                return path
                
        with open(source_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if "blocks" in data:
            for block in data["blocks"]:
                if "texture_atlas_path" in block:
                    block["texture_atlas_path"] = to_win_path(block["texture_atlas_path"])
                if "facade_textures" in block:
                    new_textures = {}
                    for k, v in block["facade_textures"].items():
                        new_textures[k] = to_win_path(v)
                    block["facade_textures"] = new_textures
                    
        with open(dest_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        return True
    except Exception as e:
        print(f"[Warning] Error translating paths for Windows Blender: {e}")
        return False

def run_blender_export(args=None):
    """Locates and runs the Blender background script to compile geometry.gltf."""
    blender_path = "blender"
    is_running_wsl = is_wsl()
    
    if is_running_wsl:
        # Check if blender.exe is available in PATH (WSL can run .exe files directly)
        blender_path = shutil.which("blender.exe")
        if not blender_path:
            # Look in standard Windows program files directories mounted in WSL
            win_paths = sorted(
                glob.glob("/mnt/c/Program Files/Blender Foundation/Blender */blender.exe"),
                reverse=True
            )
            if win_paths:
                blender_path = win_paths[0]
            else:
                blender_path = "blender.exe"  # Last resort fallback
    elif sys.platform == "win32":
        # Native Windows
        blender_path = shutil.which("blender") or shutil.which("blender.exe")
        if not blender_path:
            win_paths = sorted(
                glob.glob("C:/Program Files/Blender Foundation/Blender */blender.exe"),
                reverse=True
            )
            if win_paths:
                blender_path = win_paths[0]
            else:
                blender_path = "blender"
    elif sys.platform == "darwin":
        # macOS
        blender_path = "blender"
        mac_paths = [
            "/Applications/Blender.app/Contents/MacOS/Blender",
            "/Applications/Blender.app/Contents/MacOS/blender",
            os.path.expanduser("~/Applications/Blender.app/Contents/MacOS/Blender")
        ]
        for path in mac_paths:
            if os.path.exists(path):
                blender_path = path
                break
    else:
        # Linux / other
        blender_path = shutil.which("blender") or "blender"
                
    print(f"[Blender Compiler] Compiling geometry.gltf using Blender: '{blender_path}'")
    
    python_script = "blender_script.py"
    import_json = "export/reconstruction_export.json"
    
    # Gather extra culling and camera arguments to pass to the script
    extra_args = []
    if hasattr(args, "no_cull") and args.no_cull:
        extra_args.append("--no-cull")
    if hasattr(args, "cam_loc") and args.cam_loc:
        extra_args.extend(["--cam-loc", args.cam_loc])
    if hasattr(args, "cam_rot") and args.cam_rot:
        extra_args.extend(["--cam-rot", args.cam_rot])
    if hasattr(args, "fov_deg") and args.fov_deg:
        extra_args.extend(["--fov-deg", str(args.fov_deg)])
    if hasattr(args, "max_dist") and args.max_dist:
        extra_args.extend(["--max-dist", str(args.max_dist)])
    
    if is_running_wsl:
        # Translate JSON paths for Windows Blender
        win_import_json = "export/reconstruction_export_win.json"
        if translate_paths_to_windows(import_json, win_import_json):
            import_json = win_import_json
            
        # Convert script and JSON paths to Windows paths
        win_python_script = get_windows_path(os.path.abspath(python_script))
        win_import_json_path = get_windows_path(os.path.abspath(import_json))
        
        cmd = [
            blender_path,
            "--background",
            "--python",
            win_python_script,
            "--",
            "--import",
            win_import_json_path
        ] + extra_args
    else:
        cmd = [
            blender_path,
            "--background",
            "--python",
            python_script,
            "--",
            "--import",
            import_json
        ] + extra_args
        
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if res.returncode == 0:
            print("[Blender Compiler] Successfully compiled geometry.gltf!")
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
        reprocess=args.reprocess,
        skip_scraper=args.skip_scraper,
        harvest_only=args.harvest_only,
        parallel=args.parallel
    )
    blocks_data, scene_doc = reconstructor.reconstruct_blocks_and_texture()
    
    if args.harvest_only:
        print("[Harvest Mode] Scraping and caching complete. Skipped scene document export and Blender compilation as requested.")
        return
        
    export_filepath = "export/reconstruction_export.json"
    with open(export_filepath, "w", encoding="utf-8") as f:
        json.dump(scene_doc, f, indent=4)
    print(f"[Reconstruction] Exported block prism meshes and graph metadata to: {export_filepath}")

    print("-" * 60)
    print("Pipeline Execution Complete!")
    print("Texture Atlas PNGs generated in: export/textures/")
    
    # 3. TRIGGER BLENDER COMPILATION
    run_blender_export(args)
    
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tecate 2009 Historical Urban Reconstruction Pipeline CLI")
    parser.add_argument("--headless", action="store_true", default=is_headless_by_default(),
                        help="Run Playwright Chromium browser in headless mode (defaults to True on WSL/headless Linux, False on Mac)")
    parser.add_argument("--skip-scraper", action="store_true", default=False,
                        help="Bypass Playwright browser crawling and load directly from cached structural_graph nodes")
    parser.add_argument("--harvest-only", action="store_true", default=False,
                        help="Harvest data mode: performs scraping/crawling but skips all processing, filtering, and 3D reconstruction.")
    parser.add_argument("--reprocess", action="store_true", default=False,
                        help="Reprocess cached screenshots (crop, align, stitch) without redownloading them.")
    parser.add_argument("--radius", type=float, default=-1,
                        help="Safety radius centered at (0, 0) in meters. Set to -1 to process the whole city of Tecate.")
    
    # Camera Viewport Culling parameters
    parser.add_argument("--parallel", type=int, default=4,
                        help="Number of concurrent threads for image processing and texturing (default: 4, set to 1 for sequential)")
    parser.add_argument("--no-cull", action="store_true", default=False,
                        help="Disable camera FOV/frustum culling in Blender scene construction")
    parser.add_argument("--cam-loc", type=str, default="0.0,-120.0,110.0",
                        help="Blender camera location (comma-separated x,y,z)")
    parser.add_argument("--cam-rot", type=str, default="48.0,0.0,0.0",
                        help="Blender camera rotation in degrees (comma-separated rx,ry,rz)")
    parser.add_argument("--fov-deg", type=float, default=90.0,
                        help="Blender camera horizontal FOV in degrees")
    parser.add_argument("--max-dist", type=float, default=250.0,
                        help="Blender camera maximum view distance in meters")
    
    args = parser.parse_args()
    run_pipeline(args)
