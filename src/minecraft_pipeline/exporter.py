import os
import json
import math
import struct
import sys
import threading
import concurrent.futures
import hashlib
import time
import numpy as np
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
from .nbt import NBT, TAG_COMPOUND, TAG_LIST, TAG_STRING, TAG_INT, TAG_LONG, TAG_BYTE, TAG_DOUBLE, TAG_LONG_ARRAY, save_gzip
from .mca import MCARegion, pack_block_states
from .road_metadata_cache import get_edge_key, extract_and_cache_road_metadata, get_default_metadata

def save_custom_blocks_cache(cache_path, custom_blocks, last_edge_idx, last_block_idx, existing_data_tuple=None):
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        
        if existing_data_tuple is not None:
            ex_x, ex_y, ex_z, ex_block_ids, ex_palette = existing_data_tuple
            ex_palette_strings = []
            for p in ex_palette:
                if isinstance(p, bytes):
                    ex_palette_strings.append(p.decode('utf-8'))
                else:
                    ex_palette_strings.append(str(p))
        else:
            ex_x, ex_y, ex_z, ex_block_ids, ex_palette_strings = None, None, None, None, []
            
        # Build unified palette by appending new unique names to existing palette list
        unified_palette = list(ex_palette_strings)
        palette_map = {name: idx for idx, name in enumerate(unified_palette)}
        
        new_palette_entries = set(custom_blocks.values())
        for name in new_palette_entries:
            if name not in palette_map:
                palette_map[name] = len(unified_palette)
                unified_palette.append(name)
                
        n_new = len(custom_blocks)
        x_new = np.empty(n_new, dtype=np.int32)
        y_new = np.empty(n_new, dtype=np.int32)
        z_new = np.empty(n_new, dtype=np.int32)
        block_ids_new = np.empty(n_new, dtype=np.uint8)
        
        for idx, ((x, y, z), name) in enumerate(custom_blocks.items()):
            x_new[idx] = x
            y_new[idx] = y
            z_new[idx] = z
            block_ids_new[idx] = palette_map[name]
            
        if ex_x is not None and len(ex_x) > 0:
            x_arr = np.concatenate([ex_x, x_new])
            y_arr = np.concatenate([ex_y, y_new])
            z_arr = np.concatenate([ex_z, z_new])
            block_ids = np.concatenate([ex_block_ids, block_ids_new])
        else:
            x_arr = x_new
            y_arr = y_new
            z_arr = z_new
            block_ids = block_ids_new
            
        np.savez_compressed(
            cache_path,
            x=x_arr,
            y=y_arr,
            z=z_arr,
            block_ids=block_ids,
            palette=np.array(unified_palette),
            last_edge_idx=np.array(last_edge_idx),
            last_block_idx=np.array(last_block_idx)
        )
        print(f"[Exporter] Cache saved successfully: {cache_path} (edge progress: {last_edge_idx}, block progress: {last_block_idx}, total blocks: {len(x_arr)})")
    except Exception as e:
        print(f"[Exporter Warning] Failed to save custom blocks cache: {e}")

def load_custom_blocks_cache_raw(cache_path):
    if not os.path.exists(cache_path):
        return None, 0, 0
        
    print(f"[Exporter] Loading pre-rasterized geometry arrays from cache: {cache_path}")
    start_time = time.time()
    try:
        with np.load(cache_path) as data:
            x_arr = data['x']
            y_arr = data['y']
            z_arr = data['z']
            block_ids = data['block_ids']
            palette = data['palette']
            last_edge_idx = int(data.get('last_edge_idx', 0))
            last_block_idx = int(data.get('last_block_idx', 0))
            
        print(f"[Exporter] Loaded arrays from cache in {time.time() - start_time:.2f} seconds (progress: edge {last_edge_idx}, block {last_block_idx}).")
        return (x_arr, y_arr, z_arr, block_ids, palette), last_edge_idx, last_block_idx
    except Exception as e:
        print(f"[Exporter Warning] Failed to load custom blocks cache: {e}. Re-rasterizing from scratch...")
        return None, 0, 0

class BlockProvider:
    def __init__(self, custom_blocks_dict=None, custom_blocks_data=None):
        self.dict = custom_blocks_dict
        self.data = custom_blocks_data
        
    def get_blocks_and_pts_for_region(self, rx, rz):
        if self.dict is not None:
            region_blocks = {}
            pts = []
            for (x, y, z), name in self.dict.items():
                if rx * 512 <= x < (rx + 1) * 512 and rz * 512 <= z < (rz + 1) * 512:
                    region_blocks[(x, y, z)] = name
                    pts.append((x, y, z))
            return region_blocks, pts
        elif self.data is not None:
            x_arr, y_arr, z_arr, block_ids, palette = self.data
            mask = (x_arr >= rx * 512) & (x_arr < (rx + 1) * 512) & (z_arr >= rz * 512) & (z_arr < (rz + 1) * 512)
            
            rx_arr = x_arr[mask]
            ry_arr = y_arr[mask]
            rz_arr = z_arr[mask]
            rblock_ids = block_ids[mask]
            
            x_list = rx_arr.tolist()
            y_list = ry_arr.tolist()
            z_list = rz_arr.tolist()
            block_ids_list = rblock_ids.tolist()
            palette_list = [str(p) for p in palette]
            
            palette_map = [palette_list[bid] for bid in block_ids_list]
            keys = list(zip(x_list, y_list, z_list))
            
            region_blocks = dict(zip(keys, palette_map))
            pts = keys
            return region_blocks, pts
        return {}, []


def rasterize_single_block(b, get_mc_terrain_y, cancel_event):
    local_blocks = {}
    poly = b["polygon"]
    poly_mc = [[pt[0], -pt[1]] for pt in poly]
    
    xs_poly = [pt[0] for pt in poly_mc]
    zs_poly = [pt[1] for pt in poly_mc]
    if not xs_poly or not zs_poly:
        return local_blocks
        
    min_x_p = int(math.floor(min(xs_poly)))
    max_x_p = int(math.ceil(max(xs_poly)))
    min_z_p = int(math.floor(min(zs_poly)))
    max_z_p = int(math.ceil(max(zs_poly)))
    
    for x_mc in range(min_x_p, max_x_p + 1):
        if cancel_event.is_set():
            return local_blocks
        for z_mc in range(min_z_p, max_z_p + 1):
            if point_in_polygon(x_mc, z_mc, poly_mc):
                d_boundary = distance_to_polygon_boundary(x_mc, z_mc, poly_mc)
                y_mc = get_mc_terrain_y(x_mc, z_mc)
                
                y_platform = y_mc + 1
                
                if d_boundary <= 2.0:
                    if d_boundary <= 1.0:
                        block_name = "minecraft:polished_andesite"
                    else:
                        block_name = "minecraft:smooth_stone"
                else:
                    block_name = "minecraft:light_gray_concrete"
                    
                local_blocks[(x_mc, y_platform, z_mc)] = block_name
                local_blocks[(x_mc, y_mc, z_mc)] = "minecraft:dirt"
    return local_blocks

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

    def query_height_batch(self, coords):
        """
        Performs batch queries of coordinates (x, z), grouping them by cell to do
        highly efficient vectorized cell-based interpolations in SciPy.
        """
        coords_arr = np.array(coords, dtype=np.float32)
        results = np.empty(len(coords_arr), dtype=np.float32)
        if len(coords_arr) == 0:
            return results
            
        cell_groups = {}
        for idx, (x, z) in enumerate(coords_arr):
            cx = int(math.floor(x / self.cell_size))
            cz = int(math.floor(z / self.cell_size))
            cell_groups.setdefault((cx, cz), []).append(idx)
            
        for (cx, cz), indices in cell_groups.items():
            lin_interp, near_interp = self.get_interpolator(cx, cz)
            cell_coords = coords_arr[indices]
            
            if near_interp is None:
                results[indices] = 400.0
                continue
                
            cell_h = np.empty(len(indices), dtype=np.float32)
            cell_h.fill(np.nan)
            
            if lin_interp is not None:
                try:
                    cell_h = lin_interp(cell_coords)
                except Exception:
                    try:
                        cell_h = lin_interp(cell_coords[:, 0], cell_coords[:, 1])
                    except Exception:
                        pass
                        
            nan_mask = np.isnan(cell_h)
            if np.any(nan_mask):
                try:
                    near_h = near_interp(cell_coords[nan_mask])
                except Exception:
                    near_h = near_interp(cell_coords[nan_mask, 0], cell_coords[nan_mask, 1])
                cell_h[nan_mask] = near_h
                
            results[indices] = cell_h
            
        return results

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

def point_in_polygon(x, z, polygon):
    inside = False
    n = len(polygon)
    if n == 0:
        return False
    p1x, p1z = polygon[0]
    for i in range(n + 1):
        p2x, p2z = polygon[i % n]
        if z > min(p1z, p2z):
            if z <= max(p1z, p2z):
                if x <= max(p1x, p2x):
                    if p1z != p2z:
                        xinters = (z - p1z) * (p2x - p1x) / (p2z - p1z) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1z = p2x, p2z
    return inside

def distance_to_polygon_boundary(x, z, polygon):
    min_dist = float('inf')
    n = len(polygon)
    if n == 0:
        return 0.0
    for i in range(n):
        ax, az = polygon[i]
        bx, bz = polygon[(i + 1) % n]
        dx = bx - ax
        dz = bz - az
        len2 = dx*dx + dz*dz
        if len2 < 1e-8:
            dist = math.sqrt((x - ax)**2 + (z - az)**2)
        else:
            t = ((x - ax) * dx + (z - az) * dz) / len2
            t = max(0.0, min(1.0, t))
            proj_x = ax + t * dx
            proj_z = az + t * dz
            dist = math.sqrt((x - proj_x)**2 + (z - proj_z)**2)
        if dist < min_dist:
            min_dist = dist
    return min_dist

def get_deterministic_choice(x, y, z, choices, weights):
    """Deterministically selects a choice based on coordinates hash."""
    hash_str = f"{x},{y},{z}"
    val = int(hashlib.md5(hash_str.encode()).hexdigest(), 16)
    normalized = (val % 1000) / 1000.0
    
    cumulative = 0.0
    for choice, weight in zip(choices, weights):
        cumulative += weight
        if normalized <= cumulative:
            return choice
    return choices[-1]

def print_progress(label, completed, total):
    """Prints a highly efficient text-based progress bar on a single line."""
    if total <= 0:
        return
    pct = int(100 * completed / total)
    filled = int(30 * completed / total)
    bar = "=" * filled + " " * (30 - filled)
    sys.stdout.write(f"\r{label}: [{bar}] {pct}% ({completed}/{total})")
    sys.stdout.flush()
    if completed >= total:
        sys.stdout.write("\n")
        sys.stdout.flush()

def export_single_region(rx, rz, pts, mca_path, custom_blocks, interpolator, y_offset, height_cache, cancel_event=None):
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
                    
    # Pre-resolve all terrain heights for the region in batch to optimize SciPy calls
    missing_queries = []
    for (cx_local, cz_local) in region_chunks:
        cx_global = rx * 32 + cx_local
        cz_global = rz * 32 + cz_local
        for dx in range(16):
            for dz in range(16):
                x_val = cx_global * 16 + dx
                z_val = cz_global * 16 + dz
                if height_cache.get(x_val, z_val) is None:
                    missing_queries.append((x_val, -z_val))
                    
    if missing_queries:
        batch_heights = interpolator.query_height_batch(missing_queries)
        for (x_q, mz_q), h_real in zip(missing_queries, batch_heights):
            z_val = -mz_q
            cached_h = int(round(h_real)) - y_offset
            height_cache.set(x_q, z_val, cached_h)
                    
    for (cx_local, cz_local) in region_chunks:
        if cancel_event is not None and cancel_event.is_set():
            return
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
    
    # Load existing metadata if available for incremental consistency
    metadata_path = os.path.join(world_dir, "tecate_metadata.json")
    existing_metadata = None
    y_offset_override = None
    existing_bbox = None
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                existing_metadata = json.load(f)
            y_offset_override = existing_metadata.get("vertical_offset")
            existing_bbox = existing_metadata.get("bbox")
            print(f"[Exporter] Loaded existing metadata. Reusing vertical offset Y_offset = {y_offset_override}m.")
        except Exception as e:
            print(f"[Exporter Warning] Failed to load existing metadata: {e}")
            
    s = 0.84277856
    tx = 28057.9043
    tz = 16614.8854
    
    cancel_event = threading.Event()
    height_cache = TerrainHeightCache()
    
    # Pre-define helper as None to prevent UnboundLocalError during early Ctrl+C
    resolver_ready = False
    y_offset = 0
    min_x, max_x, min_y, max_y = 0.0, 0.0, 0.0, 0.0
    custom_blocks_data = None
    custom_blocks = {}
    last_edge_idx = 0
    last_block_idx = 0
    
    try:
        print(f"[Exporter] Loading reconstruction data from: {reconstruction_json_path}")
        with open(reconstruction_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        blocks = data.get("blocks", [])
        road_graph = data.get("road_graph", {})
        
        # Extract and cache road metadata
        export_dir = os.path.dirname(reconstruction_json_path)
        road_metadata_path = os.path.join(export_dir, "road_metadata.json")
        road_metadata = extract_and_cache_road_metadata(reconstruction_json_path, road_metadata_path)
        edge_metadata = road_metadata.get("edges", {})
        
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
        if y_offset_override is not None:
            y_offset = y_offset_override
        else:
            y_offset = int(math.floor(min_height)) + 60
            print(f"[Exporter] Minimum terrain height: {min_height:.2f}m. Set vertical offset Y_offset = {y_offset}m (baseline Y = -60).")
        
        # Define height resolver using pre-built cell interpolators
        def get_mc_terrain_y(x_mc, z_mc):
            h = height_cache.get(x_mc, z_mc)
            if h is None:
                h_real = interpolator.query_height(x_mc, -z_mc)
                h = int(round(h_real)) - y_offset
                height_cache.set(x_mc, z_mc, h)
            return h
        
        resolver_ready = True
    
        print("[Exporter] Rasterizing road networks and custom block lot platforms...")
        
        nodes = road_graph.get("nodes", [])
        edges = road_graph.get("edges", [])
        num_edges = len(edges)
        num_blocks = len(blocks)
        
        cache_path = os.path.join(output_dir, "custom_blocks_cache.npz")
        custom_blocks_data, last_edge_idx, last_block_idx = load_custom_blocks_cache_raw(cache_path)
        custom_blocks = {}
        
        # A. Rasterize road graph (first, so block platforms can overwrite/clip them)
        node_map = {nd["id"]: nd for nd in nodes}
        
        if last_edge_idx < num_edges:
            print(f"[Exporter] Rasterizing road network starting from index {last_edge_idx}...")
            for idx in range(last_edge_idx, num_edges):
                if cancel_event.is_set():
                    raise KeyboardInterrupt()
                ed = edges[idx]
                if (idx + 1) % 20 == 0 or idx + 1 == num_edges:
                    print_progress("[Exporter] Rasterizing road network", idx + 1, num_edges)
                u_nd = node_map.get(ed["u"])
                v_nd = node_map.get(ed["v"])
                if u_nd and v_nd:
                    x1, z1 = u_nd["x"], -u_nd["y"]
                    x2, z2 = v_nd["x"], -v_nd["y"]
                    
                    key = get_edge_key(ed["u"], ed["v"])
                    meta = edge_metadata.get(key, {})
                    hw = meta.get("highway", "residential")
                    lanes = meta.get("lanes", 2)
                    width = meta.get("width", 6.0)
                    surface = meta.get("surface", "asphalt")
                    
                    is_rural = (surface in ["gravel", "dirt", "earth", "ground", "sand", "grass"]) or (hw in ["track", "path", "bridleway"])
                    
                    dx = x2 - x1
                    dz = z2 - z1
                    dist = math.sqrt(dx*dx + dz*dz)
                    if dist < 1e-5:
                        continue
                        
                    perp_x = -dz / dist
                    perp_z = dx / dist
                    
                    # Add padding to ensure road overlaps block boundaries and gets clipped perfectly
                    w_adjusted = width + 3
                    half_w = w_adjusted / 2.0
                    
                    steps = int(math.ceil(dist * 2))
                    for step in range(steps + 1):
                        t = step / steps
                        cx = x1 + t * dx
                        cz = z1 + t * dz
                        
                        dist_along = t * dist
                        is_near_intersection = (dist_along < 4.0) or ((dist - dist_along) < 4.0)
                        
                        d_min = int(math.floor(-half_w))
                        d_max = int(math.ceil(half_w))
                        for d in range(d_min, d_max + 1):
                            px = cx + d * perp_x
                            pz = cz + d * perp_z
                            
                            x_mc = int(round(px))
                            z_mc = int(round(pz))
                            y_mc = get_mc_terrain_y(x_mc, z_mc)
                            
                            if is_rural:
                                # Rural/historical road materials
                                choices = [
                                    "minecraft:gravel",
                                    "minecraft:cobblestone",
                                    "minecraft:coarse_dirt",
                                    "minecraft:andesite",
                                    "minecraft:mossy_cobblestone"
                                ]
                                weights = [0.5, 0.25, 0.15, 0.05, 0.05]
                                block_name = get_deterministic_choice(x_mc, y_mc, z_mc, choices, weights)
                                
                                # Roadside vegetation just outside the boundary
                                if abs(d) == d_max:
                                    veg_x = int(round(cx + (d + (1 if d > 0 else -1)) * perp_x))
                                    veg_z = int(round(cz + (d + (1 if d > 0 else -1)) * perp_z))
                                    veg_y = get_mc_terrain_y(veg_x, veg_z)
                                    
                                    veg_choices = [None, "minecraft:short_grass", "minecraft:fern", "minecraft:dandelion", "minecraft:poppy"]
                                    veg_weights = [0.8, 0.1, 0.05, 0.025, 0.025]
                                    veg_block = get_deterministic_choice(veg_x, veg_y, veg_z, veg_choices, veg_weights)
                                    if veg_block:
                                        custom_blocks[(veg_x, veg_y + 1, veg_z)] = veg_block
                            else:
                                # Modern asphalt road materials
                                is_marking = False
                                block_name = None
                                
                                # Center yellow line
                                if lanes == 2 and abs(d) < 0.5 and not is_near_intersection:
                                    if int(math.floor(dist_along)) % 4 < 2:
                                        block_name = "minecraft:yellow_concrete"
                                        is_marking = True
                                        
                                # Side white lines
                                edge_d = max(1.0, math.floor(width / 2.0) - 1.0)
                                if not is_marking and abs(abs(d) - edge_d) < 0.5 and not is_near_intersection:
                                    block_name = "minecraft:white_concrete"
                                    is_marking = True
                                    
                                if not is_marking:
                                    choices = [
                                        "minecraft:gray_concrete_powder",
                                        "minecraft:black_concrete_powder",
                                        "minecraft:smooth_basalt",
                                        "minecraft:cobbled_deepslate",
                                        "minecraft:coal_block"
                                    ]
                                    weights = [0.6, 0.25, 0.05, 0.05, 0.05]
                                    block_name = get_deterministic_choice(x_mc, y_mc, z_mc, choices, weights)
                                    
                            custom_blocks[(x_mc, y_mc, z_mc)] = block_name
                last_edge_idx = idx + 1
        else:
            print("[Exporter] Road network rasterization already fully completed.")
                        
        # B. Rasterize block lots (manzanas) with perimetral sidewalks (overwriting road overlaps)
        num_blocks = len(blocks)
        if last_block_idx < num_blocks:
            workers = parallel_workers if parallel_workers > 0 else (os.cpu_count() or 4)
            print(f"[Exporter] Rasterizing block platforms in parallel using {workers} threads...")
            
            completed_flags = [False] * num_blocks
            for i in range(last_block_idx):
                completed_flags[i] = True
                
            progress_lock = threading.Lock()
            completed_count = last_block_idx
            
            def progress_callback(block_idx):
                nonlocal last_block_idx, completed_count
                completed_flags[block_idx] = True
                with progress_lock:
                    completed_count += 1
                    while last_block_idx < num_blocks and completed_flags[last_block_idx]:
                        last_block_idx += 1
                    if completed_count % 50 == 0 or completed_count == num_blocks:
                        print_progress("[Exporter] Rasterizing block platforms", completed_count, num_blocks)
                        
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=workers)
            try:
                futures = {}
                for idx in range(last_block_idx, num_blocks):
                    if cancel_event.is_set():
                        break
                    b = blocks[idx]
                    f = executor.submit(
                        rasterize_single_block,
                        b, get_mc_terrain_y, cancel_event
                    )
                    futures[f] = idx
                    
                active_futures = list(futures.keys())
                while active_futures:
                    if cancel_event.is_set():
                        break
                    done, not_done = concurrent.futures.wait(
                        active_futures,
                        timeout=0.2,
                        return_when=concurrent.futures.FIRST_COMPLETED
                    )
                    for f in done:
                        block_idx = futures[f]
                        try:
                            res = f.result()
                            custom_blocks.update(res)
                        except Exception as e:
                            print(f"\n[Exporter Error] Failed to rasterize block {block_idx}: {e}")
                        progress_callback(block_idx)
                        active_futures.remove(f)
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
                
            # We computed new blocks, save the cache
            if not cancel_event.is_set():
                save_custom_blocks_cache(cache_path, custom_blocks, num_edges, num_blocks, custom_blocks_data)
        else:
            print("[Exporter] Block platforms rasterization already fully completed.")
                        
        # Instantiate block provider
        if custom_blocks:
            # We rasterized new blocks and saved them to cache. Let's reload to get the combined data.
            custom_blocks_data, _, _ = load_custom_blocks_cache_raw(cache_path)
            
        if custom_blocks_data is not None:
            provider = BlockProvider(custom_blocks_data=custom_blocks_data)
            print(f"[Exporter] Utilizing memory-optimized BlockProvider with pre-rasterized geometry arrays.")
        else:
            provider = BlockProvider(custom_blocks_dict=custom_blocks)
            print(f"[Exporter] Rasterized {len(custom_blocks)} custom geometry blocks.")
        
        regions = {}
        if provider.dict is not None:
            for (x, y, z) in provider.dict.keys():
                rx = int(math.floor(x / 512.0))
                rz = int(math.floor(z / 512.0))
                regions.setdefault((rx, rz), []).append((x, y, z))
        elif provider.data is not None:
            x_arr, y_arr, z_arr, block_ids, palette = provider.data
            rx_arr = (x_arr // 512).astype(np.int32)
            rz_arr = (z_arr // 512).astype(np.int32)
            coords = np.column_stack((rx_arr, rz_arr))
            unique_regions = np.unique(coords, axis=0)
            for rx, rz in unique_regions:
                regions[(int(rx), int(rz))] = None
            
        os.makedirs(region_dir, exist_ok=True)
        
        # Prioritize regions by proximity to Parque Hidalgo (0, 0)
        def region_distance(item):
            rx, rz = item[0]
            cx = rx * 512 + 256
            cz = rz * 512 + 256
            return math.sqrt(cx**2 + cz**2)
            
        sorted_regions = sorted(regions.items(), key=region_distance)
        print(f"[Exporter] Prioritized {len(sorted_regions)} regions by geographic proximity to city center.")
        
        regions_to_generate = []
        skipped_regions = 0
        for (rx, rz), _ in sorted_regions:
            mca_path = os.path.join(region_dir, f"r.{rx}.{rz}.mca")
            if os.path.exists(mca_path):
                try:
                    test_reg = MCARegion.load(mca_path, rx, rz)
                    if len(test_reg.chunks) > 0:
                        skipped_regions += 1
                        continue
                except Exception:
                    print(f"[Exporter Warning] Region r.{rx}.{rz}.mca on disk is corrupted. Re-generating...")
            regions_to_generate.append((rx, rz))
            
        if skipped_regions > 0:
            print(f"[Exporter] Incremental export: skipped {skipped_regions} already generated valid region files.")
            
        workers = parallel_workers if parallel_workers > 0 else (os.cpu_count() or 4)
        
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=workers)
        try:
            futures = {}
            for (rx, rz) in regions_to_generate:
                mca_path = os.path.join(region_dir, f"r.{rx}.{rz}.mca")
                region_blocks, pts = provider.get_blocks_and_pts_for_region(rx, rz)
                f = executor.submit(
                    export_single_region,
                    rx, rz, pts, mca_path, region_blocks, interpolator, y_offset, height_cache, cancel_event
                )
                futures[f] = (rx, rz)
                
            completed_regions = 0
            total_regions = len(futures)
            if total_regions > 0:
                print_progress("[Exporter] Generating region MCA files", 0, total_regions)
                active_futures = list(futures.keys())
                while active_futures:
                    if cancel_event.is_set():
                        break
                    done, not_done = concurrent.futures.wait(
                        active_futures,
                        timeout=0.2,
                        return_when=concurrent.futures.FIRST_COMPLETED
                    )
                    for future in done:
                        rx, rz = futures[future]
                        try:
                            future.result()
                        except Exception as e:
                            print(f"\n[Exporter Error] Failed to generate region r.{rx}.{rz}: {e}")
                        completed_regions += 1
                        print_progress("[Exporter] Generating region MCA files", completed_regions, total_regions)
                        active_futures.remove(future)
            else:
                print("[Exporter] All regions are already generated and valid. Nothing to do.")
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
                
        # Exit validation of ALL active regions
        print("[Exporter] Validating all region files on disk...")
        corrupted_regions = 0
        for (rx, rz), _ in sorted_regions:
            mca_path = os.path.join(region_dir, f"r.{rx}.{rz}.mca")
            if os.path.exists(mca_path):
                try:
                    test_reg = MCARegion.load(mca_path, rx, rz)
                    if len(test_reg.chunks) == 0:
                        raise ValueError("No chunks found in region file")
                except Exception as e:
                    print(f"[Exporter Error] Region file r.{rx}.{rz}.mca is corrupted: {e}")
                    corrupted_regions += 1
                    
        if corrupted_regions == 0:
            print("[Exporter] Validation SUCCESS: All region files are valid.")
        else:
            print(f"[Exporter Warning] Validation finished: {corrupted_regions} region files are corrupted.")
            
    except KeyboardInterrupt:
        print("\n[Exporter] Ctrl+C interrupt detected! Saving checkpoint and cache to disk...")
        cancel_event.set()
        if 'executor' in locals():
            executor.shutdown(wait=False, cancel_futures=True)
        if 'cache_path' in locals() and 'custom_blocks' in locals() and custom_blocks:
            save_custom_blocks_cache(cache_path, custom_blocks, last_edge_idx, last_block_idx, custom_blocks_data)
            
    # Always save height cache
    height_cache.save()
    
    # 5. Write level.dat and metadata if we calculated y_offset and resolver
    if resolver_ready:
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
        
        # Calculate final merged bounding box BBox
        final_min_x = min_x
        final_max_x = max_x
        final_min_y = min_y
        final_max_y = max_y
        if existing_bbox is not None:
            final_min_x = min(final_min_x, existing_bbox.get("min_local_x", final_min_x))
            final_max_x = max(final_max_x, existing_bbox.get("max_local_x", final_max_x))
            final_min_y = min(final_min_y, existing_bbox.get("min_local_y", final_min_y))
            final_max_y = max(final_max_y, existing_bbox.get("max_local_y", final_max_y))
            
        # 6. Save metadata file
        metadata_path = os.path.join(world_dir, "tecate_metadata.json")
        metadata = {
            "vertical_offset": y_offset,
            "bbox": {
                "min_local_x": final_min_x,
                "max_local_x": final_max_x,
                "min_local_y": final_min_y,
                "max_local_y": final_max_y
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
