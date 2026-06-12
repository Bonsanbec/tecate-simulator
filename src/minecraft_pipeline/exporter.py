import os
import json
import math
import struct
import sys
import threading
import concurrent.futures
import numpy as np
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
from .nbt import NBT, TAG_COMPOUND, TAG_LIST, TAG_STRING, TAG_INT, TAG_LONG, TAG_BYTE, TAG_DOUBLE, TAG_LONG_ARRAY, save_gzip
from .mca import MCARegion, pack_block_states

class TerrainHeightCache:
    """
    A thread-safe caching system for terrain height lookups to avoid
    re-running heavy Delaunay/griddata calculations on duplicate columns.
    """
    def __init__(self, cache_path="data/terrain_height_cache.json"):
        self.cache_path = cache_path
        self.lock = threading.Lock()
        self.cache = {}
        self.changed = False
        
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        parts = k.split(',')
                        if len(parts) == 2:
                            self.cache[(int(parts[0]), int(parts[1]))] = v
                print(f"[TerrainHeightCache] Loaded {len(self.cache)} entries from {self.cache_path}")
            except Exception as e:
                print(f"[TerrainHeightCache Warning] Failed to load cache: {e}")

    def get(self, x, z):
        with self.lock:
            return self.cache.get((x, z))

    def set(self, x, z, h):
        with self.lock:
            self.cache[(x, z)] = h
            self.changed = True

    def save(self):
        with self.lock:
            if not self.changed:
                return
            try:
                os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
                data = {f"{k[0]},{k[1]}": v for k, v in self.cache.items()}
                with open(self.cache_path, 'w') as f:
                    json.dump(data, f)
                self.changed = False
                print(f"[TerrainHeightCache] Saved {len(data)} entries to {self.cache_path}")
            except Exception as e:
                print(f"[TerrainHeightCache Warning] Failed to save cache: {e}")

def load_terrain_vertices(glb_path, s, tx, tz):
    """Loads tinMesh (Mesh 1) vertices and projects them to local Cartesian space."""
    if not os.path.exists(glb_path):
        raise FileNotFoundError(f"Terrain GLB not found at: {glb_path}")
        
    with open(glb_path, "rb") as f:
        header = f.read(12)
        magic, version, length = struct.unpack('<III', header)
        if magic != 0x46546c67:
            raise ValueError("Invalid GLB magic number")
            
        chunk_header = f.read(8)
        chunk_length, chunk_type = struct.unpack('<II', chunk_header)
        json_bytes = f.read(chunk_length)
        gltf = json.loads(json_bytes.decode('utf-8'))
        
        f.seek(12 + 8 + chunk_length)
        chunk1_header = f.read(8)
        chunk1_len, chunk1_type = struct.unpack('<II', chunk1_header)
        binary_data = f.read(chunk1_len)
        
        # Mesh 1 is tinMesh (surface TIN)
        mesh = gltf['meshes'][1]
        prim = mesh['primitives'][0]
        pos_idx = prim['attributes']['POSITION']
        
        pos_acc = gltf['accessors'][pos_idx]
        pos_bv = gltf['bufferViews'][pos_acc['bufferView']]
        
        pos_offset = pos_bv.get('byteOffset', 0) + pos_acc.get('byteOffset', 0)
        pos_count = pos_acc['count']
        
        positions = np.frombuffer(binary_data[pos_offset:pos_offset + pos_count * 12], dtype=np.float32).reshape(pos_count, 3)
        
        x_godot = s * positions[:, 0] + tx
        z_godot = s * positions[:, 2] + tz
        y_godot = s * positions[:, 1]
        
        return x_godot, y_godot, z_godot

class TerrainHeightInterpolator:
    """
    Uses a 2D spatial grid index to lazily build and cache local Delaunay interpolators
    per cell, ensuring fast O(1) query lookups on-demand.
    """
    def __init__(self, glb_path, s, tx, tz, cell_size=500.0):
        print("[TerrainInterpolator] Loading terrain vertices...")
        self.x_pts, self.y_pts, self.z_pts = load_terrain_vertices(glb_path, s, tx, tz)
        self.cell_size = cell_size
        self.grid = {}
        self.interpolators = {}
        self.lock = threading.Lock()
        
        print("[TerrainInterpolator] Building spatial grid index...")
        for idx in range(len(self.x_pts)):
            cx = int(math.floor(self.x_pts[idx] / cell_size))
            cz = int(math.floor(self.z_pts[idx] / cell_size))
            self.grid.setdefault((cx, cz), []).append(idx)
        print(f"[TerrainInterpolator] Indexed {len(self.x_pts)} vertices in {len(self.grid)} cells.")

    def get_interpolator(self, cx, cz):
        """Lazily builds and caches linear and nearest-neighbor interpolators for the cell."""
        with self.lock:
            if (cx, cz) in self.interpolators:
                return self.interpolators[(cx, cz)]
                
            indices = []
            for dcz in [-1, 0, 1]:
                for dcx in [-1, 0, 1]:
                    indices.extend(self.grid.get((cx + dcx, cz + dcz), []))
                    
            if len(indices) < 3:
                for dcz in [-2, -1, 0, 1, 2]:
                    for dcx in [-2, -1, 0, 1, 2]:
                        if max(abs(dcx), abs(dcz)) > 1:
                            indices.extend(self.grid.get((cx + dcx, cz + dcz), []))
                            
            if len(indices) < 3:
                self.interpolators[(cx, cz)] = (None, None)
                return None, None
                
            pts_x = self.x_pts[indices]
            pts_z = self.z_pts[indices]
            pts_y = self.y_pts[indices]
            
            points = np.column_stack((pts_x, pts_z))
            
            try:
                lin_interp = LinearNDInterpolator(points, pts_y)
            except Exception:
                lin_interp = None
            near_interp = NearestNDInterpolator(points, pts_y)
            
            self.interpolators[(cx, cz)] = (lin_interp, near_interp)
            return lin_interp, near_interp

    def query_height(self, x, z):
        cx = int(math.floor(x / self.cell_size))
        cz = int(math.floor(z / self.cell_size))
        
        lin_interp, near_interp = self.get_interpolator(cx, cz)
        if near_interp is None:
            return 400.0
            
        h = None
        if lin_interp is not None:
            # Query the pre-built Delaunay triangulation instantly
            h = lin_interp(x, z)
            
        if h is None or np.isnan(h):
            h = near_interp(x, z)
            
        return float(h)

def draw_line_3d(x1, y1, z1, x2, y2, z2):
    pts = []
    dx = x2 - x1
    dy = y2 - y1
    dz = z2 - z1
    dist = math.sqrt(dx*dx + dy*dy + dz*dz)
    if dist < 1e-5:
        return [(int(round(x1)), int(round(y1)), int(round(z1)))]
        
    steps = int(math.ceil(dist))
    for step in range(steps + 1):
        t = step / steps
        x = x1 + t * dx
        y = y1 + t * dy
        z = z1 + t * dz
        pts.append((int(round(x)), int(round(y)), int(round(z))))
    return list(set(pts))

def export_single_region(rx, rz, pts, mca_path, custom_blocks, interpolator, y_offset, height_cache):
    """Generates MCA chunks for a single region (runs in worker thread)."""
    region = MCARegion(rx, rz)
    
    region_chunks = set()
    for pt in pts:
        cx = int(math.floor(pt[0] / 16.0))
        cz = int(math.floor(pt[2] / 16.0))
        cx_local = cx % 32
        cz_local = cz % 32
        for dcz in [-1, 0, 1]:
            for dcx in [-1, 0, 1]:
                ccx = (cx_local + dcx)
                ccz = (cz_local + dcz)
                if 0 <= ccx < 32 and 0 <= ccz < 32:
                    region_chunks.add((ccx, ccz))
                    
    for (cx_local, cz_local) in region_chunks:
        cx_global = rx * 32 + cx_local
        cz_global = rz * 32 + cz_local
        
        sections_nbt_list = []
        for s_y in range(-4, 20):
            y_min_sec = s_y * 16
            palette_map = {"minecraft:air": 0}
            palette_list = ["minecraft:air"]
            block_indices = [0] * 4096
            has_non_air = False
            
            for dy in range(16):
                y_val = y_min_sec + dy
                for dz in range(16):
                    z_val = cz_global * 16 + dz
                    for dx in range(16):
                        x_val = cx_global * 16 + dx
                        
                        block_name = custom_blocks.get((x_val, y_val, z_val))
                        if block_name is None:
                            # Use thread-safe height cache to speed up snaps
                            cached_h = height_cache.get(x_val, z_val)
                            if cached_h is None:
                                h_real = interpolator.query_height(x_val, -z_val)
                                cached_h = int(round(h_real)) - y_offset
                                height_cache.set(x_val, z_val, cached_h)
                                
                            y_terrain = cached_h
                            if y_val < y_terrain - 3:
                                block_name = "minecraft:stone"
                            elif y_val < y_terrain:
                                block_name = "minecraft:dirt"
                            elif y_val == y_terrain:
                                block_name = "minecraft:grass_block"
                            else:
                                block_name = "minecraft:air"
                                
                        if block_name != "minecraft:air":
                            has_non_air = True
                            
                        p_idx = palette_map.get(block_name)
                        if p_idx is None:
                            p_idx = len(palette_list)
                            palette_map[block_name] = p_idx
                            palette_list.append(block_name)
                            
                        flat_idx = dy * 256 + dz * 16 + dx
                        block_indices[flat_idx] = p_idx
                        
            if has_non_air:
                palette_comp_list = [
                    NBT(TAG_COMPOUND, value=[NBT(TAG_STRING, "Name", name)])
                    for name in palette_list
                ]
                block_states_comp = [
                    NBT(TAG_LIST, "palette", (TAG_COMPOUND, palette_comp_list))
                ]
                if len(palette_list) > 1:
                    bits_per_block = max(4, int(math.ceil(math.log2(len(palette_list)))))
                    longs = pack_block_states(block_indices, bits_per_block)
                    block_states_comp.append(NBT(TAG_LONG_ARRAY, "data", longs))
                    
                biomes_comp = NBT(TAG_COMPOUND, "biomes", [
                    NBT(TAG_LIST, "palette", (TAG_STRING, ["minecraft:plains"]))
                ])
                
                section_comp = NBT(TAG_COMPOUND, value=[
                    NBT(TAG_BYTE, "Y", s_y),
                    NBT(TAG_COMPOUND, "block_states", block_states_comp),
                    biomes_comp
                ])
                sections_nbt_list.append(section_comp)
                
        chunk_nbt = NBT(TAG_COMPOUND, "", [
            NBT(TAG_INT, "DataVersion", 3463),
            NBT(TAG_INT, "xPos", cx_global),
            NBT(TAG_INT, "zPos", cz_global),
            NBT(TAG_INT, "yPos", -4),
            NBT(TAG_STRING, "Status", "full"),
            NBT(TAG_LIST, "sections", (TAG_COMPOUND, sections_nbt_list))
        ])
        region.set_chunk_nbt(cx_local, cz_local, chunk_nbt)
        
    region.save(mca_path)
    print(f"[Exporter] Saved region file: {mca_path}")

def export_world(reconstruction_json_path, glb_path, output_dir, parallel_workers=0):
    world_dir = os.path.join(output_dir, "TecateWorld")
    region_dir = os.path.join(world_dir, "region")
    
    s = 0.84277856
    tx = 28057.9043
    tz = 16614.8854
    
    height_cache = TerrainHeightCache()
    
    # Pre-define helper as None to prevent UnboundLocalError during early Ctrl+C
    get_mc_terrain_y = None
    y_offset = 0
    min_x, max_x, min_y, max_y = 0.0, 0.0, 0.0, 0.0
    
    try:
        print(f"[Exporter] Loading reconstruction data from: {reconstruction_json_path}")
        with open(reconstruction_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        blocks = data.get("blocks", [])
        road_graph = data.get("road_graph", {})
        
        interpolator = TerrainHeightInterpolator(glb_path, s, tx, tz)
        
        print("[Exporter] Calculating active area bounds...")
        xs = []
        ys = []
        for b in blocks:
            for pt in b["polygon"]:
                xs.append(pt[0])
                ys.append(pt[1])
                
        if not xs or not ys:
            print("[Exporter Warning] No blocks found. Using origin.")
            xs = [0.0]
            ys = [0.0]
            
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        active_corners = [
            (min_x, min_y), (max_x, min_y),
            (min_x, max_y), (max_x, max_y),
            ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)
        ]
        corner_heights = [interpolator.query_height(c[0], -c[1]) for c in active_corners]
        min_height = min(corner_heights)
        y_offset = int(math.floor(min_height)) - 10
        print(f"[Exporter] Minimum terrain height: {min_height:.2f}m. Set vertical offset Y_offset = {y_offset}m.")
        
        # Define height resolver using pre-built cell interpolators
        def get_mc_terrain_y(x_mc, z_mc):
            h = height_cache.get(x_mc, z_mc)
            if h is None:
                h_real = interpolator.query_height(x_mc, -z_mc)
                h = int(round(h_real)) - y_offset
                height_cache.set(x_mc, z_mc, h)
            return h
    
        print("[Exporter] Rasterizing building wireframes and road networks...")
        custom_blocks = {}
        
        # A. Rasterize building blocks
        for idx, b in enumerate(blocks):
            poly = b["polygon"]
            height = int(round(b["height_meters"]))
            num_verts = len(poly) - 1
            
            vert_coords = []
            for pt in poly[:-1]:
                x_mc = int(round(pt[0]))
                z_mc = int(round(-pt[1]))
                y_mc = get_mc_terrain_y(x_mc, z_mc)
                vert_coords.append((x_mc, y_mc, z_mc))
                
            for i in range(num_verts):
                p1 = vert_coords[i]
                p2 = vert_coords[(i + 1) % num_verts]
                line_pts = draw_line_3d(p1[0], 0, p1[2], p2[0], 0, p2[2])
                for lp in line_pts:
                    x_mc, z_mc = lp[0], lp[2]
                    y_mc = get_mc_terrain_y(x_mc, z_mc)
                    custom_blocks[(x_mc, y_mc, z_mc)] = "minecraft:yellow_concrete"
    
            for i in range(num_verts):
                p = vert_coords[i]
                for y_step in range(p[1], p[1] + height + 1):
                    custom_blocks[(p[0], y_step, p[2])] = "minecraft:red_concrete"
                    
            for i in range(num_verts):
                p1 = vert_coords[i]
                p2 = vert_coords[(i + 1) % num_verts]
                line_pts = draw_line_3d(p1[0], p1[1] + height, p1[2], p2[0], p2[1] + height, p2[2])
                for lp in line_pts:
                    custom_blocks[lp] = "minecraft:light_blue_concrete"
    
        # B. Rasterize road graph
        nodes = road_graph.get("nodes", [])
        edges = road_graph.get("edges", [])
        node_map = {nd["id"]: nd for nd in nodes}
        
        for ed in edges:
            u_nd = node_map.get(ed["u"])
            v_nd = node_map.get(ed["v"])
            if u_nd and v_nd:
                x1, z1 = int(round(u_nd["x"])), int(round(-u_nd["y"]))
                x2, z2 = int(round(v_nd["x"])), int(round(-v_nd["y"]))
                
                line_pts = draw_line_3d(x1, 0, z1, x2, 0, z2)
                for lp in line_pts:
                    x_mc, z_mc = lp[0], lp[2]
                    y_mc = get_mc_terrain_y(x_mc, z_mc)
                    custom_blocks[(x_mc, y_mc, z_mc)] = "minecraft:gray_concrete"
                    
        print(f"[Exporter] Rasterized {len(custom_blocks)} custom geometry blocks.")
        
        regions = {}
        for (x, y, z) in custom_blocks.keys():
            rx = int(math.floor(x / 512.0))
            rz = int(math.floor(z / 512.0))
            regions.setdefault((rx, rz), []).append((x, y, z))
            
        os.makedirs(region_dir, exist_ok=True)
        
        workers = parallel_workers if parallel_workers > 0 else (os.cpu_count() or 4)
        print(f"[Exporter] Generating chunks for {len(regions)} regions using {workers} parallel threads...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {}
            for (rx, rz), pts in regions.items():
                mca_path = os.path.join(region_dir, f"r.{rx}.{rz}.mca")
                f = executor.submit(
                    export_single_region,
                    rx, rz, pts, mca_path, custom_blocks, interpolator, y_offset, height_cache
                )
                futures[f] = (rx, rz)
                
            for future in concurrent.futures.as_completed(futures):
                rx, rz = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"[Exporter Error] Failed to generate region r.{rx}.{rz}: {e}")
                    
    except KeyboardInterrupt:
        print("\n[Exporter] Ctrl+C interrupt detected! Saving checkpoint and cache to disk...")
        if 'executor' in locals():
            executor.shutdown(wait=False, cancel_futures=True)
            
    # Always save height cache
    height_cache.save()
    
    # 5. Write level.dat and metadata if we calculated y_offset and resolver
    if get_mc_terrain_y is not None:
        print("[Exporter] Finalizing level.dat settings...")
        level_dat_path = os.path.join(world_dir, "level.dat")
        spawn_y = get_mc_terrain_y(0, 0) + 2
        
        level_data_nbt = NBT(TAG_COMPOUND, "Data", [
            NBT(TAG_STRING, "LevelName", "Tecate Simulator"),
            NBT(TAG_STRING, "generatorName", "flat"),
            NBT(TAG_STRING, "generatorOptions", "minecraft:bedrock,2*minecraft:dirt,minecraft:grass_block;minecraft:plains"),
            NBT(TAG_INT, "SpawnX", 0),
            NBT(TAG_INT, "SpawnY", spawn_y),
            NBT(TAG_INT, "SpawnZ", 0),
            NBT(TAG_INT, "GameType", 1),
            NBT(TAG_BYTE, "Difficulty", 0),
            NBT(TAG_LONG, "Time", 6000),
            NBT(TAG_LONG, "DayTime", 6000),
            NBT(TAG_INT, "version", 19133),
            NBT(TAG_BYTE, "initialized", 1),
            NBT(TAG_COMPOUND, "GameRules", [
                NBT(TAG_STRING, "doMobSpawning", "false"),
                NBT(TAG_STRING, "keepInventory", "true"),
                NBT(TAG_STRING, "doDaylightCycle", "false")
            ])
        ])
        
        level_root = NBT(TAG_COMPOUND, "", [level_data_nbt])
        save_gzip(level_root, level_dat_path)
        
        # 6. Save metadata file
        metadata_path = os.path.join(world_dir, "tecate_metadata.json")
        metadata = {
            "vertical_offset": y_offset,
            "bbox": {
                "min_local_x": min_x,
                "max_local_x": max_x,
                "min_local_y": min_y,
                "max_local_y": max_y
            },
            "terrain_alignment": {
                "scale": s,
                "translation_x": tx,
                "translation_z": tz
            }
        }
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4)
            
        print(f"[Exporter] Save finished: {world_dir}")
    else:
        print("[Exporter Warning] Interrupted before setup completed. No level.dat or metadata generated.")
        
    return world_dir

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tecate to Minecraft World Exporter")
    parser.add_argument("--import-json", default="export/reconstruction_export.json", help="Path to reconstruction_export.json")
    parser.add_argument("--glb-path", default="models/tecate/glb/tecate.glb", help="Path to terrain GLB")
    parser.add_argument("--output-dir", default="export/minecraft_world", help="Output directory for Minecraft saves")
    parser.add_argument("--parallel", type=int, default=0, help="Number of thread workers (0 = auto)")
    args = parser.parse_args()
    
    export_world(args.import_json, args.glb_path, args.output_dir, args.parallel)
