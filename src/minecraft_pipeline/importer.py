import os
import json
import math
import struct
import glob
import shutil
import subprocess
import sys
import threading
import concurrent.futures
import numpy as np
from .nbt import read_tag
from .mca import MCARegion, unpack_block_states
from .exporter import TerrainHeightInterpolator, TerrainHeightCache

TERRAIN_BLOCKS = {
    "minecraft:grass_block",
    "minecraft:dirt",
    "minecraft:stone",
    "minecraft:deepslate",
    "minecraft:bedrock",
    "minecraft:sand",
    "minecraft:gravel",
    "minecraft:clay",
    "minecraft:water"
}

BLOCK_COLORS = {
    "minecraft:yellow_concrete": [0.95, 0.8, 0.1],
    "minecraft:red_concrete": [0.8, 0.1, 0.1],
    "minecraft:light_blue_concrete": [0.2, 0.6, 0.85],
    "minecraft:gray_concrete": [0.3, 0.3, 0.35],
    "minecraft:stone": [0.5, 0.5, 0.5],
    "minecraft:dirt": [0.45, 0.3, 0.15],
    "minecraft:grass_block": [0.4, 0.6, 0.2],
    "minecraft:white_concrete": [0.9, 0.9, 0.9],
    "minecraft:orange_concrete": [0.9, 0.5, 0.1],
    "minecraft:magenta_concrete": [0.75, 0.25, 0.7],
    "minecraft:lime_concrete": [0.4, 0.75, 0.1],
    "minecraft:pink_concrete": [0.9, 0.5, 0.65],
    "minecraft:cyan_concrete": [0.1, 0.55, 0.6],
    "minecraft:purple_concrete": [0.5, 0.15, 0.65],
    "minecraft:blue_concrete": [0.15, 0.2, 0.6],
    "minecraft:brown_concrete": [0.35, 0.2, 0.15],
    "minecraft:green_concrete": [0.3, 0.4, 0.15],
    "minecraft:black_concrete": [0.08, 0.08, 0.1]
}

def locate_blender():
    """Robustly locates the Blender executable across macOS, Windows, WSL, and Linux."""
    blender_path = "blender"
    if sys.platform == "darwin":
        mac_paths = [
            "/Applications/Blender.app/Contents/MacOS/Blender",
            "/Applications/Blender.app/Contents/MacOS/blender",
            os.path.expanduser("~/Applications/Blender.app/Contents/MacOS/Blender")
        ]
        for path in mac_paths:
            if os.path.exists(path):
                return path
    elif sys.platform == "win32":
        blender_path = shutil.which("blender") or shutil.which("blender.exe")
        if not blender_path:
            win_paths = sorted(
                glob.glob("C:/Program Files/Blender Foundation/Blender */blender.exe"),
                reverse=True
            )
            if win_paths:
                return win_paths[0]
    else:
        blender_path = shutil.which("blender") or "blender"
    return blender_path

def import_single_region(filepath, rx, rz, interpolator, y_offset, height_cache):
    """Parses a single region file and filters out terrain blocks (runs in a worker thread)."""
    local_preserved = {}
    mca = MCARegion.load(filepath, rx, rz)
    
    for (cx_local, cz_local), compressed in mca.chunks.items():
        cx_global = rx * 32 + cx_local
        cz_global = rz * 32 + cz_local
        
        chunk_nbt = mca.get_chunk_nbt(cx_local, cz_local)
        if not chunk_nbt:
            continue
            
        sections = []
        for tag in chunk_nbt.value:
            if tag.name == "sections":
                sections = tag.value[1]
                break
                
        for sec in sections:
            s_y = None
            block_states = None
            for t in sec.value:
                if t.name == "Y":
                    s_y = t.value
                elif t.name == "block_states":
                    block_states = t.value
                    
            if s_y is None or block_states is None:
                continue
                
            palette = []
            data_longs = None
            for t in block_states:
                if t.name == "palette":
                    palette_tags = t.value[1]
                    for p_tag in palette_tags:
                        for member in p_tag.value:
                            if member.name == "Name":
                                palette.append(member.value)
                elif t.name == "data":
                    data_longs = t.value
                    
            if not palette:
                continue
                
            if len(palette) == 1:
                indices = [0] * 4096
            elif data_longs is not None:
                bits_per_block = max(4, int(math.ceil(math.log2(len(palette)))))
                indices = unpack_block_states(data_longs, bits_per_block)
            else:
                indices = [0] * 4096
                
            y_min_sec = s_y * 16
            for dy in range(16):
                y_val = y_min_sec + dy
                for dz in range(16):
                    z_val = cz_global * 16 + dz
                    for dx in range(16):
                        x_val = cx_global * 16 + dx
                        flat_idx = dy * 256 + dz * 16 + dx
                        p_idx = indices[flat_idx]
                        if p_idx >= len(palette):
                            continue
                        block_name = palette[p_idx]
                        
                        if block_name == "minecraft:air":
                            continue
                            
                        # Snap height query (always hits lazy cell cache)
                        cached_h = height_cache.get(x_val, z_val)
                        if cached_h is None:
                            h_real = interpolator.query_height(x_val, -z_val)
                            cached_h = int(round(h_real)) - y_offset
                            height_cache.set(x_val, z_val, cached_h)
                            
                        y_terrain = cached_h
                        
                        if block_name in TERRAIN_BLOCKS and y_val <= y_terrain:
                            continue
                            
                        local_preserved[(x_val, y_val, z_val)] = block_name
                        
    del mca
    return local_preserved

def import_world(world_dir, glb_path, output_dir, parallel_workers=0):
    metadata_path = os.path.join(world_dir, "tecate_metadata.json")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found in world directory: {metadata_path}")
        
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
        
    y_offset = metadata["vertical_offset"]
    align = metadata["terrain_alignment"]
    s, tx, tz = align["scale"], align["translation_x"], align["translation_z"]
    
    interpolator = TerrainHeightInterpolator(glb_path, s, tx, tz)
    height_cache = TerrainHeightCache()
    
    region_dir = os.path.join(world_dir, "region")
    mca_files = glob.glob(os.path.join(region_dir, "r.*.*.mca"))
    print(f"[Importer] Found {len(mca_files)} region files.")
    
    preserved_blocks = {}
    workers = parallel_workers if parallel_workers > 0 else (os.cpu_count() or 4)
    
    try:
        print(f"[Importer] Reading regions in parallel utilizing {workers} threads...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {}
            for filepath in mca_files:
                filename = os.path.basename(filepath)
                parts = filename.split('.')
                rx, rz = int(parts[1]), int(parts[2])
                
                f_obj = executor.submit(
                    import_single_region,
                    filepath, rx, rz, interpolator, y_offset, height_cache
                )
                futures[f_obj] = filepath
                
            for future in concurrent.futures.as_completed(futures):
                path = futures[future]
                try:
                    res = future.result()
                    preserved_blocks.update(res)
                except Exception as e:
                    print(f"[Importer Error] Failed to read region {path}: {e}")
                    
    except KeyboardInterrupt:
        print("\n[Importer] Ctrl+C interrupt detected! Saving checkpoint of data parsed so far...")
        if 'executor' in locals():
            executor.shutdown(wait=False, cancel_futures=True)
            
    # Always save height cache
    height_cache.save()
    
    print(f"[Importer] Extracted {len(preserved_blocks)} preserved blocks (terrain subtracted).")
    
    # 3. Perform Voxel Face Culling
    print("[Importer] Optimizing voxel geometry (face culling)...")
    culled_blocks = {}
    for (x, y, z), name in preserved_blocks.items():
        neighbors = [
            (x + 1, y, z), (x - 1, y, z),
            (x, y + 1, z), (x, y - 1, z),
            (x, y, z + 1), (x, y, z - 1)
        ]
        all_present = all(n in preserved_blocks for n in neighbors)
        if not all_present:
            culled_blocks[(x, y, z)] = name
            
    print(f"[Importer] Optimized voxel mesh contains {len(culled_blocks)} blocks (culled {len(preserved_blocks) - len(culled_blocks)} internal blocks).")
    
    # 4. Generate box list
    boxes = []
    for (x, y, z), name in culled_blocks.items():
        loc_x = float(x)
        loc_y = float(-z)
        loc_z = float(y + y_offset)
        
        color = BLOCK_COLORS.get(name, [0.8, 0.8, 0.8])
        boxes.append({
            "min": [loc_x, loc_y, loc_z],
            "max": [loc_x + 1.0, loc_y + 1.0, loc_z + 1.0],
            "block_type": name,
            "color": color
        })
        
    os.makedirs(output_dir, exist_ok=True)
    json_out_path = os.path.join(output_dir, "boxes.json")
    with open(json_out_path, 'w', encoding='utf-8') as f:
        json.dump(boxes, f, indent=4)
    print(f"[Importer] Saved boxes to JSON: {json_out_path}")
    
    # 5. Invoke Blender background compilation
    blender_bin = locate_blender()
    print(f"[Importer] Triggering background Blender compiler using: '{blender_bin}'")
    
    script_path = os.path.join(os.path.dirname(__file__), "import_minecraft.py")
    cmd = [
        blender_bin,
        "--background",
        "--python",
        script_path,
        "--",
        "--import",
        json_out_path,
        "--output-dir",
        output_dir
    ]
    
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if res.returncode == 0:
            print("[Importer] Blender compilation: SUCCESS!")
            print(f"Generated Blend file: {os.path.join(output_dir, 'tecate_reimported.blend')}")
            print(f"Generated GLB model: {os.path.join(output_dir, 'geometry_reimported.glb')}")
        else:
            print(f"[Importer Warning] Blender compilation failed with exit code: {res.returncode}")
            print(res.stdout)
            print(res.stderr)
    except Exception as e:
        print(f"[Importer Error] Failed to run Blender compiler: {e}")
        
    return json_out_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Minecraft World to Blender Importer")
    parser.add_argument("--world-dir", default="export/minecraft_world/TecateWorld", help="Path to Minecraft save world")
    parser.add_argument("--glb-path", default="models/tecate/glb/tecate.glb", help="Path to terrain GLB")
    parser.add_argument("--output-dir", default="export/minecraft_world", help="Output directory for generated Blend/GLB models")
    parser.add_argument("--parallel", type=int, default=0, help="Number of thread workers (0 = auto)")
    args = parser.parse_args()
    
    import_world(args.world_dir, args.glb_path, args.output_dir, args.parallel)
