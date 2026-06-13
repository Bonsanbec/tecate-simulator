import os
import json
import math
import struct
import glob
import shutil
import subprocess
import sys
import concurrent.futures
import numpy as np
from .nbt import (
    NBT, TAG_COMPOUND, TAG_LIST, TAG_STRING, TAG_INT, TAG_LONG,
    TAG_BYTE, TAG_DOUBLE, TAG_LONG_ARRAY, TAG_BYTE_ARRAY, TAG_INT_ARRAY, TAG_END,
    read_tag
)
from .mca import MCARegion, unpack_block_states

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

def nbt_to_py(tag):
    """Converts NBT tags recursively to standard, sortable, and comparable Python structures."""
    if not isinstance(tag, NBT):
        return tag
    t = tag.type
    val = tag.value
    if t == TAG_COMPOUND:
        return {m.name: nbt_to_py(m) for m in sorted(val, key=lambda x: x.name or "")}
    elif t == TAG_LIST:
        item_type, items = val
        return (item_type, [nbt_to_py(item) for item in items])
    elif t in (TAG_BYTE_ARRAY, TAG_INT_ARRAY, TAG_LONG_ARRAY):
        return tuple(val)
    else:
        return val

def get_sections_and_entities(nbt_tag):
    sections_list = []
    block_entities_list = []
    if not nbt_tag or not hasattr(nbt_tag, 'value'):
        return sections_list, block_entities_list
    for tag in nbt_tag.value:
        if tag.name == "sections":
            sections_list = tag.value[1]
        elif tag.name == "block_entities":
            block_entities_list = tag.value[1]
    return sections_list, block_entities_list

def is_block_states_only_air(bs_tag):
    if not bs_tag or bs_tag.type != TAG_COMPOUND:
        return True
    palette = None
    for tag in bs_tag.value:
        if tag.name == "palette":
            palette = tag.value[1]
            break
    if not palette:
        return True
    if len(palette) == 1:
        first_tag = palette[0]
        for tag in first_tag.value:
            if tag.name == "Name" and tag.value == "minecraft:air":
                return True
    return False

def chunk_block_states_differ(nbt1, nbt2):
    """Detects if block states or block entities differ between two chunk NBT structures."""
    sec1, ent1 = get_sections_and_entities(nbt1)
    sec2, ent2 = get_sections_and_entities(nbt2)
    
    sec_dict1 = {}
    for s in sec1:
        y_val = None
        block_states = None
        for tag in s.value:
            if tag.name == "Y":
                y_val = tag.value
            elif tag.name == "block_states":
                block_states = tag
        if y_val is not None:
            sec_dict1[y_val] = block_states
            
    sec_dict2 = {}
    for s in sec2:
        y_val = None
        block_states = None
        for tag in s.value:
            if tag.name == "Y":
                y_val = tag.value
            elif tag.name == "block_states":
                block_states = tag
        if y_val is not None:
            sec_dict2[y_val] = block_states
            
    all_ys = set(sec_dict1.keys()) | set(sec_dict2.keys())
    for y_val in all_ys:
        bs1 = sec_dict1.get(y_val)
        bs2 = sec_dict2.get(y_val)
        
        if (bs1 is None) != (bs2 is None):
            non_empty_bs = bs1 if bs1 is not None else bs2
            if not is_block_states_only_air(non_empty_bs):
                return True
        elif bs1 is not None and bs2 is not None:
            if nbt_to_py(bs1) != nbt_to_py(bs2):
                return True
                
    py_ent1 = sorted([nbt_to_py(e) for e in ent1], key=lambda d: (d.get("x", 0), d.get("y", 0), d.get("z", 0)))
    py_ent2 = sorted([nbt_to_py(e) for e in ent2], key=lambda d: (d.get("x", 0), d.get("y", 0), d.get("z", 0)))
    
    if py_ent1 != py_ent2:
        return True
        
    return False

def extract_chunk_all_blocks(chunk_nbt, cx_global, cz_global, min_s_y, max_s_y):
    """Extracts all non-air blocks from the chunk's sections within vertical bounds."""
    blocks = {}
    sections, _ = get_sections_and_entities(chunk_nbt)
            
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
            
        if s_y < min_s_y or s_y >= max_s_y:
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
                    
                    if block_name != "minecraft:air":
                        blocks[(x_val, y_val, z_val)] = block_name
                        
    return blocks

def diff_single_region_process(rx, rz, fresh_mca_path, modified_mca_path, min_s_y, max_s_y):
    active_chunks = set()
    block_data = {}
    
    # Tier 1: Fast file-level content comparison
    if os.path.exists(fresh_mca_path) and os.path.exists(modified_mca_path):
        try:
            import filecmp
            if filecmp.cmp(fresh_mca_path, modified_mca_path, shallow=False):
                return active_chunks, block_data
        except Exception:
            pass
            
    fresh_mca = MCARegion.load(fresh_mca_path, rx, rz) if os.path.exists(fresh_mca_path) else None
    modified_mca = MCARegion.load(modified_mca_path, rx, rz) if os.path.exists(modified_mca_path) else None
    
    if not modified_mca:
        return active_chunks, block_data
        
    for (cx_local, cz_local), comp_modified in modified_mca.chunks.items():
        cx_global = rx * 32 + cx_local
        cz_global = rz * 32 + cz_local
        
        comp_fresh = fresh_mca.chunks.get((cx_local, cz_local)) if fresh_mca else None
        
        is_changed = False
        if comp_fresh is None:
            is_changed = True
        else:
            # Tier 2: Fast chunk-level compressed byte comparison
            if comp_fresh == comp_modified:
                is_changed = False
            else:
                # Fallback to deep NBT comparison
                fresh_nbt = fresh_mca.get_chunk_nbt(cx_local, cz_local)
                modified_nbt = modified_mca.get_chunk_nbt(cx_local, cz_local)
                if not modified_nbt:
                    is_changed = (fresh_nbt is not None)
                elif not fresh_nbt:
                    is_changed = True
                else:
                    is_changed = chunk_block_states_differ(fresh_nbt, modified_nbt)
                    
        if is_changed:
            active_chunks.add((cx_global, cz_global))
            fresh_nbt = fresh_mca.get_chunk_nbt(cx_local, cz_local) if fresh_mca else None
            modified_nbt = modified_mca.get_chunk_nbt(cx_local, cz_local)
            
            if modified_nbt:
                fresh_blocks = extract_chunk_all_blocks(fresh_nbt, cx_global, cz_global, min_s_y, max_s_y) if fresh_nbt else {}
                modified_blocks = extract_chunk_all_blocks(modified_nbt, cx_global, cz_global, min_s_y, max_s_y)
                
                # Compare modified blocks directly with fresh reference blocks
                all_coords = set(fresh_blocks.keys()) | set(modified_blocks.keys())
                for coord in all_coords:
                    b_fresh = fresh_blocks.get(coord, "minecraft:air")
                    b_mod = modified_blocks.get(coord, "minecraft:air")
                    if b_mod != b_fresh:
                        # Only export blocks added or modified (solid non-air in modified world)
                        if b_mod != "minecraft:air":
                            block_data[coord] = b_mod
                            
    return active_chunks, block_data

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

def get_region_dir(world_dir):
    """Locates the Minecraft region folder, supporting custom overworld dimensions (Higher Heights)."""
    custom_path = os.path.join(world_dir, "dimensions", "minecraft", "overworld", "region")
    if os.path.exists(custom_path):
        return custom_path
    return os.path.join(world_dir, "region")

def get_file_info(filepath):
    if not os.path.exists(filepath):
        return 0.0, 0
    stat = os.stat(filepath)
    return stat.st_mtime, stat.st_size

def import_world(fresh_world_dir, modified_world_dir, glb_path=None, output_dir="export/minecraft_world", cache_path=None, parallel_workers=0):
    metadata_path = os.path.join(modified_world_dir, "tecate_metadata.json")
    if not os.path.exists(metadata_path):
        metadata_path = os.path.join(fresh_world_dir, "tecate_metadata.json")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file tecate_metadata.json not found in either world directory.")
        
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
        
    y_offset = metadata["vertical_offset"]
    
    # Safe vertical limits covering the maximum potential range of the Higher Heights datapack
    min_s_y = -16
    max_s_y = 80
    
    fresh_region_dir = get_region_dir(fresh_world_dir)
    modified_region_dir = get_region_dir(modified_world_dir)
    
    fresh_mcas = glob.glob(os.path.join(fresh_region_dir, "r.*.*.mca"))
    modified_mcas = glob.glob(os.path.join(modified_region_dir, "r.*.*.mca"))
    
    regions = set()
    for path in fresh_mcas + modified_mcas:
        filename = os.path.basename(path)
        parts = filename.split('.')
        if len(parts) == 4:
            rx, rz = int(parts[1]), int(parts[2])
            regions.add((rx, rz))
            
    # Load scan checkpoint if available
    checkpoint_path = os.path.join(output_dir, "importer_checkpoint.json")
    checkpoint = {"mtimes": {}, "modified_blocks": {}}
    if os.path.exists(checkpoint_path):
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            print(f"[Importer] Loaded checkpoint. Found {len(checkpoint.get('modified_blocks', {}))} previously scanned regions.")
        except Exception as e:
            print(f"[Importer Warning] Failed to load checkpoint: {e}")
            
    regions_to_scan = []
    final_modified_blocks = {}
    
    for (rx, rz) in sorted(regions):
        fresh_path = os.path.join(fresh_region_dir, f"r.{rx}.{rz}.mca")
        mod_path = os.path.join(modified_region_dir, f"r.{rx}.{rz}.mca")
        
        fresh_mtime, fresh_size = get_file_info(fresh_path)
        mod_mtime, mod_size = get_file_info(mod_path)
        
        region_key = f"r.{rx}.{rz}"
        cached_info = checkpoint.get("mtimes", {}).get(region_key)
        
        if cached_info and cached_info == [fresh_mtime, fresh_size, mod_mtime, mod_size]:
            # Reuse parsed blocks from checkpoint
            region_blocks = checkpoint.get("modified_blocks", {}).get(region_key, {})
            # Convert string coordinates back to tuples
            final_modified_blocks[region_key] = {
                tuple(map(int, k.split(','))): v for k, v in region_blocks.items()
            }
        else:
            regions_to_scan.append(((rx, rz), fresh_path, mod_path, fresh_mtime, fresh_size, mod_mtime, mod_size))
            
    print(f"[Importer] {len(regions_to_scan)} / {len(regions)} regions need to be scanned.")
    
    workers = parallel_workers if parallel_workers > 0 else (os.cpu_count() or 4)
    active_chunks = set()
    
    if regions_to_scan:
        print(f"[Importer] Scanning changed regions in parallel using {workers} processes...")
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {}
            for (rx, rz), fresh_path, mod_path, fm, fs, mm, ms in regions_to_scan:
                f = executor.submit(
                    diff_single_region_process,
                    rx, rz, fresh_path, mod_path, min_s_y, max_s_y
                )
                futures[f] = (rx, rz, fm, fs, mm, ms)
                
            for future in concurrent.futures.as_completed(futures):
                rx, rz, fm, fs, mm, ms = futures[future]
                region_key = f"r.{rx}.{rz}"
                try:
                    chunks, blocks = future.result()
                    active_chunks.update(chunks)
                    final_modified_blocks[region_key] = blocks
                    
                    # Update checkpoint in-memory
                    checkpoint.setdefault("mtimes", {})[region_key] = [fm, fs, mm, ms]
                    checkpoint.setdefault("modified_blocks", {})[region_key] = {
                        f"{k[0]},{k[1]},{k[2]}": v for k, v in blocks.items()
                    }
                except Exception as e:
                    print(f"[Importer Error] Failed to scan region r.{rx}.{rz}: {e}")
                    
        # Save updated checkpoint back to disk
        try:
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, indent=4)
            print(f"[Importer] Saved checkpoint to: {checkpoint_path}")
        except Exception as e:
            print(f"[Importer Warning] Failed to save checkpoint: {e}")
            
    # Combine all player modifications
    preserved_blocks = {}
    for r_blocks in final_modified_blocks.values():
        preserved_blocks.update(r_blocks)
        
    print(f"[Importer] Diff model contains {len(preserved_blocks)} player-built modification blocks.")
    
    # 3. Perform Exposed Face Culling & Group by region
    print("[Importer] Optimizing voxel geometry (exposed face culling)...")
    region_data = {}
    total_culled = 0
    total_exposed = 0
    
    for (x, y, z), name in preserved_blocks.items():
        mask = 0
        if (x + 1, y, z) not in preserved_blocks:
            mask |= 1
        if (x - 1, y, z) not in preserved_blocks:
            mask |= 2
        if (x, y + 1, z) not in preserved_blocks:
            mask |= 4
        if (x, y - 1, z) not in preserved_blocks:
            mask |= 8
        if (x, y, z + 1) not in preserved_blocks:
            mask |= 16
        if (x, y, z - 1) not in preserved_blocks:
            mask |= 32
            
        if mask == 0:
            total_culled += 1
            continue
            
        total_exposed += 1
        rx = int(math.floor(x / 512.0))
        rz = int(math.floor(z / 512.0))
        region_key = f"r.{rx}.{rz}"
        
        loc_x = float(x)
        loc_y = float(-z)
        loc_z = float(y + y_offset)
        
        color = BLOCK_COLORS.get(name, [0.8, 0.8, 0.8])
        region_data.setdefault(region_key, []).append({
            "pos": [loc_x, loc_y, loc_z],
            "mask": mask,
            "block_type": name,
            "color": color
        })
        
    print(f"[Importer] Optimization finished: culled {total_culled} internal blocks, kept {total_exposed} exposed blocks.")
    
    os.makedirs(output_dir, exist_ok=True)
    json_out_path = os.path.join(output_dir, "boxes.json")
    with open(json_out_path, 'w', encoding='utf-8') as f:
        json.dump({"region_data": region_data}, f, indent=4)
    print(f"[Importer] Saved optimized exposed faces to JSON: {json_out_path}")
    
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
    parser.add_argument("--fresh-world", required=True, help="Path to the fresh reference world directory")
    parser.add_argument("--modified-world", required=True, help="Path to the player-modified world directory")
    parser.add_argument("--glb-path", default=None, help="Path to terrain GLB (ignored)")
    parser.add_argument("--output-dir", default="export/minecraft_world", help="Output directory for generated Blend/GLB models")
    parser.add_argument("--cache-path", default=None, help="Path to custom_blocks_cache.npz (ignored)")
    parser.add_argument("--parallel", type=int, default=0, help="Number of process workers (0 = auto)")
    args = parser.parse_args()
    
    import_world(
        args.fresh_world,
        args.modified_world,
        glb_path=args.glb_path,
        output_dir=args.output_dir,
        cache_path=args.cache_path,
        parallel_workers=args.parallel
    )
