#!/usr/bin/env python3
"""
scripts/bake_pipeline.py
========================
Unified pipeline manager for the Tecate Digital Twin 3D GIS layers.

Key Architecture:
1. Decoupled Stages:
   - Authoring (.blend): Lives exclusively in `blender_assets/`.
   - Runtime (.glb): Lives in `godot_project/assets/`.
   - Godot has ZERO Blender dependency or overhead during import or execution.
2. Hash-Cached Auto-Baking:
   - Computes SHA-256 hash of each `.blend` file.
   - Compares with `blender_assets/.bake_manifest.json`.
   - If a `.blend` file is unmodified and `.glb` exists -> SKIPS in <0.01s.
   - If a `.blend` file changed or `.glb` is missing -> Invokes headless Blender to bake GLB.
3. Modular GIS Layers:
   - osm2world   : 3,552 3D buildings, power towers, wind turbines, tree canopies.
   - roadways    : Continuous vector asphalt ribbons, curbs, sidewalks, lane widths.
   - railways    : Ferrocarril Tijuana-Tecate (3D ballast bed, timber sleepers, steel rails).
   - waterways   : Lakes, reservoirs (Presa Las Auras), and rivers (Río Tecate).
   - bridges     : Suspended elevated bridge decks, guardrails, and concrete support piers.
   - manzanas    : Urban lot platforms and sidewalk concrete for developed city blocks.
"""

import os
import sys
import time
import json
import hashlib
import argparse
import subprocess
import shutil
import glob
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────────────────────
# Constants & Paths
# ─────────────────────────────────────────────────────────────────────────────

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLENDER_ASSETS_DIR = os.path.join(WORKSPACE_ROOT, "blender_assets")
RUNTIME_ASSETS_DIR = os.path.join(WORKSPACE_ROOT, "godot_project", "assets")
MANIFEST_PATH = os.path.join(BLENDER_ASSETS_DIR, ".bake_manifest.json")
OSM_CACHE_DIR = os.path.join(RUNTIME_ASSETS_DIR, "osm_cache")
TERRAIN_GLB = os.path.join(RUNTIME_ASSETS_DIR, "tecate.glb")

LAYERS = {
    "osm2world": {
        "description": "3D Buildings, transmission towers, wind turbines & tree canopies",
        "blend": os.path.join(BLENDER_ASSETS_DIR, "osm2world_adjusted.blend"),
        "glb": os.path.join(RUNTIME_ASSETS_DIR, "osm2world_baked.glb"),
    },
    "roadways": {
        "description": "Continuous asphalt ribbons with lane widths, curbs & sidewalks",
        "blend": os.path.join(BLENDER_ASSETS_DIR, "roadways_adjusted.blend"),
        "glb": os.path.join(RUNTIME_ASSETS_DIR, "roadways_baked.glb"),
    },
    "railways": {
        "description": "Ferrocarril Tijuana-Tecate (3D ballast, timber ties, steel rails)",
        "blend": os.path.join(BLENDER_ASSETS_DIR, "railways_adjusted.blend"),
        "glb": os.path.join(RUNTIME_ASSETS_DIR, "railways_baked.glb"),
    },
    "waterways": {
        "description": "Presa Las Auras, lakes, basins & Río Tecate water surfaces",
        "blend": os.path.join(BLENDER_ASSETS_DIR, "waterways_adjusted.blend"),
        "glb": os.path.join(RUNTIME_ASSETS_DIR, "waterways_baked.glb"),
    },
    "bridges": {
        "description": "Elevated bridge decks spanning river valleys with support piers",
        "blend": os.path.join(BLENDER_ASSETS_DIR, "bridges_adjusted.blend"),
        "glb": os.path.join(RUNTIME_ASSETS_DIR, "bridges_baked.glb"),
    },
    "manzanas": {
        "description": "Urban lot platforms and sidewalks for developed city blocks",
        "blend": os.path.join(BLENDER_ASSETS_DIR, "manzanas_adjusted.blend"),
        "glb": os.path.join(RUNTIME_ASSETS_DIR, "manzanas_baked.glb"),
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def locate_blender():
    """Locates Blender executable across macOS, Linux, and Windows."""
    if sys.platform == "darwin":
        candidates = [
            "/Applications/Blender.app/Contents/MacOS/Blender",
            "/Applications/Blender.app/Contents/MacOS/blender",
            os.path.expanduser("~/Applications/Blender.app/Contents/MacOS/Blender")
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
    elif sys.platform == "win32":
        w_paths = sorted(glob.glob("C:/Program Files/Blender Foundation/Blender */blender.exe"), reverse=True)
        if w_paths:
            return w_paths[0]
    return shutil.which("blender") or "blender"

def compute_sha256(filepath):
    """Computes fast chunked SHA-256 hash of a file."""
    if not os.path.exists(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1048576): # 1MB chunks
            h.update(chunk)
    return h.hexdigest()

def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Manifest Warning] Could not read manifest: {e}")
    return {"version": "1.0", "layers": {}}

def save_manifest(manifest):
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    manifest["last_update_utc"] = datetime.now(timezone.utc).isoformat()
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)

# ─────────────────────────────────────────────────────────────────────────────
# Core Pipeline Operations
# ─────────────────────────────────────────────────────────────────────────────

def bake_single_glb(layer_name, blend_path, glb_path, blender_bin):
    """Runs headless Blender to export an authoritative GLB from a .blend file."""
    t0 = time.time()
    os.makedirs(os.path.dirname(glb_path), exist_ok=True)
    
    # Clean export command (purging unshaded billboard trees/forests if osm2world)
    if layer_name == "osm2world":
        py_expr = (
            "import bpy, os; "
            "tree_objs = [o for o in bpy.data.objects if o.name.startswith('Tree') or o.name.startswith('Forest')]; "
            "[bpy.data.objects.remove(o, do_unlink=True) for o in tree_objs]; "
            f"bpy.ops.export_scene.gltf(filepath=r'{os.path.abspath(glb_path)}', export_format='GLB', export_apply=True, export_materials='EXPORT')"
        )
    else:
        py_expr = f"import bpy; bpy.ops.export_scene.gltf(filepath=r'{os.path.abspath(glb_path)}', export_format='GLB', export_apply=True, export_materials='EXPORT')"

    cmd = [
        blender_bin,
        "-b", blend_path,
        "--python-expr",
        py_expr
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[Bake Error] Failed to export {layer_name}:")
        print(res.stderr or res.stdout)
        return False
    
    file_size_mb = os.path.getsize(glb_path) / (1024 * 1024)
    print(f"  -> Exported: {os.path.basename(glb_path)} ({file_size_mb:.2f} MB in {time.time() - t0:.2f}s)")
    return True

def run_bake_pipeline(selected_layers=None, force=False):
    """Checks file hashes and bakes out-of-date GLB files."""
    blender_bin = locate_blender()
    print("=" * 70)
    print("TECATE DIGITAL TWIN: HASH-CACHED GLB BAKE PIPELINE")
    print(f"Blender binary: {blender_bin}")
    print(f"Manifest:       {os.path.relpath(MANIFEST_PATH, WORKSPACE_ROOT)}")
    print("=" * 70)

    manifest = load_manifest()
    layers_to_check = selected_layers or list(LAYERS.keys())
    
    baked_count = 0
    skipped_count = 0
    start_time = time.time()

    for name in layers_to_check:
        if name not in LAYERS:
            print(f"[Warning] Unknown layer: {name}. Skipping.")
            continue

        cfg = LAYERS[name]
        blend_file = cfg["blend"]
        glb_file = cfg["glb"]
        desc = cfg["description"]

        if not os.path.exists(blend_file):
            print(f"[{name.upper()}] Blend file not found: {os.path.relpath(blend_file, WORKSPACE_ROOT)} (Skipped)")
            continue

        current_blend_hash = compute_sha256(blend_file)
        cached_entry = manifest.get("layers", {}).get(name, {})
        cached_hash = cached_entry.get("blend_hash")
        glb_exists = os.path.exists(glb_file)

        # Check if baking is required
        needs_bake = force or (not glb_exists) or (current_blend_hash != cached_hash)

        if not needs_bake:
            print(f"[{name.upper()}] [UP-TO-DATE] {os.path.basename(glb_file)} (SHA: {current_blend_hash[:10]}...)")
            skipped_count += 1
            continue

        reason = "Forced" if force else ("Missing GLB" if not glb_exists else "Hash changed")
        print(f"[{name.upper()}] [BAKING] Reason: {reason} | {desc}")
        
        success = bake_single_glb(name, blend_file, glb_file, blender_bin)
        if success:
            manifest.setdefault("layers", {})[name] = {
                "description": desc,
                "blend_file": os.path.relpath(blend_file, WORKSPACE_ROOT),
                "glb_file": os.path.relpath(glb_file, WORKSPACE_ROOT),
                "blend_hash": current_blend_hash,
                "blend_mtime": os.path.getmtime(blend_file),
                "last_bake_utc": datetime.now(timezone.utc).isoformat(),
                "glb_size_bytes": os.path.getsize(glb_file)
            }
            baked_count += 1

    save_manifest(manifest)
    print("=" * 70)
    print(f"SUMMARY: {baked_count} baked, {skipped_count} up-to-date in {time.time() - start_time:.2f}s.")
    print("=" * 70)

def show_status():
    manifest = load_manifest()
    print("=" * 70)
    print("GIS LAYERS STATUS & HASH MANIFEST")
    print("=" * 70)
    for name, cfg in LAYERS.items():
        blend_file = cfg["blend"]
        glb_file = cfg["glb"]
        
        blend_exists = os.path.exists(blend_file)
        glb_exists = os.path.exists(glb_file)
        
        cur_hash = compute_sha256(blend_file) if blend_exists else "N/A"
        cached_hash = manifest.get("layers", {}).get(name, {}).get("blend_hash", "NONE")
        
        is_synced = blend_exists and glb_exists and (cur_hash == cached_hash)
        status_tag = "SYNCED" if is_synced else ("OUT_OF_DATE" if blend_exists else "MISSING_BLEND")
        
        b_size = f"{os.path.getsize(blend_file)/(1024*1024):.1f} MB" if blend_exists else "N/A"
        g_size = f"{os.path.getsize(glb_file)/(1024*1024):.1f} MB" if glb_exists else "N/A"
        
        print(f"{name:<12} | Status: {status_tag:<11} | Blend: {b_size:<7} | GLB: {g_size:<7} | Hash: {str(cur_hash)[:8]}")
    print("=" * 70)

# ─────────────────────────────────────────────────────────────────────────────
# CLI Parser
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="Unified GIS Layer & Bake Pipeline Manager")
    parser.add_argument("--force", action="store_true", help="Force re-bake GLBs regardless of hash")
    parser.add_argument("--layer", type=str, default=None, help="Target a specific layer (roadways, railways, waterways, bridges, manzanas, osm2world)")
    parser.add_argument("--status", action="store_true", help="Display hash and synchronization status of all layers")
    parser.add_argument("--generate-all", action="store_true", help="Re-generate all procedural .blend layers from OSM and bake GLBs")
    return parser.parse_args()

def main():
    args = parse_args()
    
    if args.status:
        show_status()
        return

    if args.generate_all:
        blender_bin = locate_blender()
        gen_script = os.path.join(WORKSPACE_ROOT, "scripts", "generate_godot_layers.py")
        print(f"[Pipeline] Running full procedural generator: {gen_script}...")
        res = subprocess.run([blender_bin, "-b", "--python", gen_script])
        if res.returncode != 0:
            print("[Pipeline Error] Procedural generation failed.")
            sys.exit(1)
        # Move generated blends from godot_project/assets to blender_assets if needed
        for name, cfg in LAYERS.items():
            if name == "osm2world": continue
            base = os.path.basename(cfg["blend"])
            legacy_loc = os.path.join(RUNTIME_ASSETS_DIR, base)
            if os.path.exists(legacy_loc):
                shutil.move(legacy_loc, cfg["blend"])

    selected = [args.layer] if args.layer else None
    run_bake_pipeline(selected_layers=selected, force=args.force)

if __name__ == "__main__":
    main()
