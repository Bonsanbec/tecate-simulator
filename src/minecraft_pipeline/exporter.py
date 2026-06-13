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
import cv2

try:
    from numba import njit
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator

def save_custom_blocks_cache(cache_path, custom_blocks, last_edge_idx, last_block_idx, completed_block_indices=None):
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        if isinstance(custom_blocks, VoxelMap):
            palette = list(custom_blocks.palette)
        else:
            palette = list(set(custom_blocks.values()))
        palette_map = {name: idx for idx, name in enumerate(palette)}
        
        n = len(custom_blocks)
        x_arr = np.empty(n, dtype=np.int32)
        y_arr = np.empty(n, dtype=np.int32)
        z_arr = np.empty(n, dtype=np.int32)
        block_ids = np.empty(n, dtype=np.uint8)
        
        for idx, ((x, y, z), name) in enumerate(custom_blocks.items()):
            x_arr[idx] = x
            y_arr[idx] = y
            z_arr[idx] = z
            block_ids[idx] = palette_map[name]
            
        kwargs = {
            'x': x_arr,
            'y': y_arr,
            'z': z_arr,
            'block_ids': block_ids,
            'palette': np.array(palette),
            'last_edge_idx': np.array(last_edge_idx),
            'last_block_idx': np.array(last_block_idx)
        }
        if completed_block_indices is not None:
            kwargs['completed_block_indices'] = np.array(list(completed_block_indices), dtype=np.int32)
            
        np.savez_compressed(cache_path, **kwargs)
        print(f"[Exporter] Cache saved successfully: {cache_path} (edge progress: {last_edge_idx}, block progress: {last_block_idx})")
    except Exception as e:
        print(f"[Exporter Warning] Failed to save custom blocks cache: {e}")

class VoxelMap:
    def __init__(self, x_arr, y_arr, z_arr, block_ids, palette):
        cx = x_arr // 16
        cz = z_arr // 16
        keys = (cx.astype(np.int64) << 32) | (cz.astype(np.int64) & 0xFFFFFFFF)
        
        sort_idx = np.argsort(keys)
        self.x_arr = x_arr[sort_idx]
        self.y_arr = y_arr[sort_idx]
        self.z_arr = z_arr[sort_idx]
        self.block_ids = block_ids[sort_idx]
        self.palette = palette
        
        sorted_keys = keys[sort_idx]
        unique_keys, first_indices = np.unique(sorted_keys, return_index=True)
        
        self.chunk_slices = {}
        n_unique = len(unique_keys)
        for i in range(n_unique):
            k = unique_keys[i]
            start = first_indices[i]
            end = first_indices[i+1] if i + 1 < n_unique else len(sorted_keys)
            cx_val = int(k >> 32)
            cz_val = int(k & 0xFFFFFFFF)
            if cz_val >= 0x80000000:
                cz_val -= 0x100000000
            self.chunk_slices[(cx_val, cz_val)] = (start, end)
            
        self.new_blocks_by_chunk = {}
        self._total_new_blocks = 0
        
    def __len__(self):
        return len(self.x_arr) + self._total_new_blocks

    def __setitem__(self, key, value):
        x, y, z = key
        cx = x // 16
        cz = z // 16
        chunk_dict = self.new_blocks_by_chunk.setdefault((cx, cz), {})
        if (x, y, z) not in chunk_dict:
            self._total_new_blocks += 1
        chunk_dict[(x, y, z)] = value

    def __contains__(self, key):
        x, y, z = key
        cx = x // 16
        cz = z // 16
        if (cx, cz) in self.new_blocks_by_chunk and (x, y, z) in self.new_blocks_by_chunk[(cx, cz)]:
            return True
        slice_info = self.chunk_slices.get((cx, cz))
        if slice_info is not None:
            # Check inside the chunk slice (small list/array lookups)
            start, end = slice_info
            xs = self.x_arr[start:end]
            ys = self.y_arr[start:end]
            zs = self.z_arr[start:end]
            for i in range(len(xs)):
                if xs[i] == x and ys[i] == y and zs[i] == z:
                    return True
        return False

    def get(self, key, default=None):
        x, y, z = key
        cx = x // 16
        cz = z // 16
        slice_info = self.chunk_slices.get((cx, cz))
        if slice_info is not None:
            start, end = slice_info
            xs = self.x_arr[start:end]
            ys = self.y_arr[start:end]
            zs = self.z_arr[start:end]
            for i in range(len(xs)):
                if xs[i] == x and ys[i] == y and zs[i] == z:
                    return self.palette[self.block_ids[start + i]]
        
        # Check newly rasterized blocks
        new_blocks = self.new_blocks_by_chunk.get((cx, cz))
        if new_blocks is not None and key in new_blocks:
            return new_blocks[key]
            
        return default

    def update(self, local_dict):
        for (x, y, z), name in local_dict.items():
            self[x, y, z] = name

    def get_chunk_dict(self, cx, cz):
        chunk_dict = {}
        
        slice_info = self.chunk_slices.get((cx, cz))
        if slice_info is not None:
            start, end = slice_info
            xs = self.x_arr[start:end]
            ys = self.y_arr[start:end]
            zs = self.z_arr[start:end]
            bids = self.block_ids[start:end]
            for i in range(len(xs)):
                chunk_dict[(xs[i], ys[i], zs[i])] = self.palette[bids[i]]
                
        new_blocks = self.new_blocks_by_chunk.get((cx, cz))
        if new_blocks is not None:
            chunk_dict.update(new_blocks)
            
        return chunk_dict

    def items(self):
        for i in range(len(self.x_arr)):
            yield (self.x_arr[i], self.y_arr[i], self.z_arr[i]), self.palette[self.block_ids[i]]
        for chunk_dict in self.new_blocks_by_chunk.values():
            for coord, name in chunk_dict.items():
                yield coord, name

    def keys(self):
        for coord, _ in self.items():
            yield coord

def load_custom_blocks_cache(cache_path):
    if not os.path.exists(cache_path):
        return {}, 0, 0, set()
        
    print(f"[Exporter] Loading pre-rasterized geometry from cache: {cache_path}")
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
            if 'completed_block_indices' in data:
                completed_block_indices = set(data['completed_block_indices'].tolist())
            else:
                completed_block_indices = set(range(last_block_idx))
            
        # Self-healing byte string decoder to prevent nested "b'b'...'" string issues
        palette_list = []
        for p in palette:
            if isinstance(p, bytes):
                val = p.decode('utf-8')
            elif hasattr(p, 'decode'):
                val = p.decode('utf-8')
            else:
                val = str(p)
                
            # If the string got double-stringified as "b'minecraft:...'"
            while (val.startswith("b'") and val.endswith("'")) or (val.startswith('b"') and val.endswith('"')):
                val = val[2:-1]
            palette_list.append(val)
        
        custom_blocks = VoxelMap(x_arr, y_arr, z_arr, block_ids, palette_list)
        print(f"[Exporter] Loaded {len(custom_blocks)} custom blocks from cache in {time.time() - start_time:.2f} seconds (progress: edge {last_edge_idx}, block {last_block_idx}).")
        return custom_blocks, last_edge_idx, last_block_idx, completed_block_indices
    except Exception as e:
        print(f"[Exporter Warning] Failed to load custom blocks cache: {e}. Re-rasterizing from scratch...")
        return {}, 0, 0, set()

def rasterize_single_block(b, get_mc_terrain_y, cancel_event, interpolator=None, y_offset=0, height_cache=None):
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
    
    # 1. Scan for inside points and distances using Numba/fallback scanner
    xs_in, zs_in, dists_in = find_inside_points(min_x_p, max_x_p, min_z_p, max_z_p, poly_mc)
    
    if len(xs_in) == 0:
        return local_blocks
        
    # 2. Pre-resolve missing heights in batch if interpolator and height_cache are provided
    if interpolator is not None and height_cache is not None:
        missing_queries = []
        for x_mc, z_mc in zip(xs_in, zs_in):
            if height_cache.get(x_mc, z_mc) is None:
                missing_queries.append((x_mc, -z_mc))
                
        if missing_queries:
            batch_heights = interpolator.query_height_batch(missing_queries)
            for (x_q, mz_q), h_real in zip(missing_queries, batch_heights):
                z_val = -mz_q
                cached_h = int(round(h_real)) - y_offset
                height_cache.set(x_q, z_val, cached_h)
                
    # 3. Generate block platforms
    inside_set = set(zip(xs_in, zs_in))
    for x_mc, z_mc, d_boundary in zip(xs_in, zs_in, dists_in):
        if cancel_event.is_set():
            return local_blocks

        y_mc = get_mc_terrain_y(x_mc, z_mc)
        y_platform = y_mc + 1

        if d_boundary <= 1.0:
            # Sidewalk perimeter: place outward-facing stairs
            facing = "north"  # default fallback
            if (x_mc + 1, z_mc) not in inside_set:
                facing = "east"
            elif (x_mc - 1, z_mc) not in inside_set:
                facing = "west"
            elif (x_mc, z_mc + 1) not in inside_set:
                facing = "south"
            elif (x_mc, z_mc - 1) not in inside_set:
                facing = "north"
            local_blocks[(x_mc, y_platform, z_mc)] = f"minecraft:stone_brick_stairs[facing={facing},half=bottom,shape=straight]"
        else:
            # Interior: place smooth stone
            local_blocks[(x_mc, y_platform, z_mc)] = "minecraft:smooth_stone"
        
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

    def get(self, x, z):
        with self.lock:
            return self.cache.get((x, z))

    def set(self, x, z, h):
        with self.lock:
            self.cache[(x, z)] = h
            self.changed = True

    def save(self):
        pass

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
        z_godot = s * (-positions[:, 2]) + tz
        y_godot = s * positions[:, 1]
        
        return x_godot, y_godot, z_godot

def resolve_road_properties(name, highway_type):
    """
    Heuristically resolves road properties (width, lanes, surface, markings, etc.)
    based on the road name prefix and OSM highway classification.
    """
    hw = highway_type or "residential"
    name_norm = (name or "").lower().strip()
    
    # 1. Expressways/Highways
    is_expressway = (
        "carr" in name_norm or 
        "carretera" in name_norm or 
        "autop" in name_norm or 
        "autopista" in name_norm or 
        hw in ["motorway", "motorway_link", "trunk", "trunk_link"]
    )
    
    # 2. Boulevards
    is_blvd = (
        "blvd" in name_norm or 
        "boulevard" in name_norm or 
        "blvrd" in name_norm
    )
    
    # 3. Avenidas / Avenues
    is_avenida = (
        "av" in name_norm or 
        "avenida" in name_norm or 
        "paseo" in name_norm
    )
    
    # 4. Streets / Calles
    is_calle = (
        "calle" in name_norm or 
        "callejón" in name_norm or
        "privada" in name_norm or
        "calzada" in name_norm
    )
    
    # 5. Unnamed minor roads / services
    is_unnamed_minor = (
        not name_norm and
        hw in ["unclassified", "service", "living_street", "track", "path", "bridleway"]
    )
    
    if is_expressway:
        width = 12.0
        lanes = 4
        surface = "asphalt"
        is_rural = False
        marking_type = "highway"
    elif is_blvd:
        width = 14.0
        lanes = 4
        surface = "asphalt_clean"
        is_rural = False
        marking_type = "boulevard"
    elif is_avenida:
        width = 9.0
        lanes = 2
        surface = "asphalt"
        is_rural = False
        marking_type = "avenida"
    elif is_unnamed_minor:
        width = 4.0
        lanes = 1
        surface = "gravel"
        is_rural = True
        marking_type = "none"
    elif is_calle:
        width = 6.0
        lanes = 2
        surface = "asphalt_light"
        is_rural = False
        marking_type = "calle"
    else:
        # Fallback default
        if hw in ["primary", "primary_link"]:
            width = 10.0
            lanes = 2
            surface = "asphalt"
            is_rural = False
            marking_type = "avenida"
        elif hw in ["secondary", "secondary_link"]:
            width = 8.0
            lanes = 2
            surface = "asphalt"
            is_rural = False
            marking_type = "calle"
        elif hw in ["tertiary", "tertiary_link"]:
            width = 7.0
            lanes = 2
            surface = "asphalt"
            is_rural = False
            marking_type = "calle"
        else:
            width = 6.0
            lanes = 2
            surface = "asphalt"
            is_rural = False
            marking_type = "calle"
            
    return {
        "width": width,
        "lanes": lanes,
        "surface": surface,
        "is_rural": is_rural,
        "marking_type": marking_type
    }

class TerrainWaterInterpolator:
    """
    Parses and indexes water meshes (nodes starting with 'water_') from the GLB.
    Builds a cell-based spatial index of 2D projected water triangles for fast O(1) query.
    """
    def __init__(self, glb_path, s, tx, tz, cell_size=200.0):
        self.cell_size = cell_size
        self.grid = {}
        self.triangles = []
        
        if not os.path.exists(glb_path):
            print(f"[WaterInterpolator Warning] GLB not found: {glb_path}")
            return
            
        print("[WaterInterpolator] Parsing water meshes from GLB...")
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
            
        # Find all water nodes
        water_nodes = []
        for idx, node in enumerate(gltf.get('nodes', [])):
            name = node.get('name', '')
            if name.startswith('water_'):
                water_nodes.append((name, node.get('mesh')))
                
        for name, mesh_idx in water_nodes:
            if mesh_idx is None:
                continue
            mesh = gltf['meshes'][mesh_idx]
            prim = mesh['primitives'][0]
            
            # Position accessor
            pos_idx = prim['attributes']['POSITION']
            pos_acc = gltf['accessors'][pos_idx]
            pos_bv = gltf['bufferViews'][pos_acc['bufferView']]
            pos_offset = pos_bv.get('byteOffset', 0) + pos_acc.get('byteOffset', 0)
            pos_count = pos_acc['count']
            positions = np.frombuffer(binary_data[pos_offset:pos_offset + pos_count * 12], dtype=np.float32).reshape(pos_count, 3)
            
            # Project vertices to MC space
            pts_mc = []
            for idx in range(pos_count):
                x_mc = s * positions[idx, 0] + tx
                z_mc = s * (-positions[idx, 2]) + tz
                y_mc = s * positions[idx, 1]
                pts_mc.append((x_mc, y_mc, z_mc))
                
            # Indices accessor
            indices_idx = prim.get('indices')
            if indices_idx is not None:
                ind_acc = gltf['accessors'][indices_idx]
                ind_bv = gltf['bufferViews'][ind_acc['bufferView']]
                ind_offset = ind_bv.get('byteOffset', 0) + ind_acc.get('byteOffset', 0)
                ind_count = ind_acc['count']
                component_type = ind_acc['componentType']
                
                dtype = np.uint16 if component_type == 5123 else np.uint32
                item_size = 2 if component_type == 5123 else 4
                indices = np.frombuffer(binary_data[ind_offset:ind_offset + ind_count * item_size], dtype=dtype)
                
                for idx in range(0, len(indices), 3):
                    if idx + 2 < len(indices):
                        a = pts_mc[indices[idx]]
                        b = pts_mc[indices[idx+1]]
                        c = pts_mc[indices[idx+2]]
                        self.triangles.append((a, b, c))
            else:
                for idx in range(0, len(pts_mc), 3):
                    if idx + 2 < len(pts_mc):
                        a = pts_mc[idx]
                        b = pts_mc[idx+1]
                        c = pts_mc[idx+2]
                        self.triangles.append((a, b, c))
                        
        # Index triangles in spatial grid
        print(f"[WaterInterpolator] Loaded {len(self.triangles)} water triangles. Building spatial grid...")
        for tri_idx, (a, b, c) in enumerate(self.triangles):
            min_x = min(a[0], b[0], c[0])
            max_x = max(a[0], b[0], c[0])
            min_z = min(a[2], b[2], c[2])
            max_z = max(a[2], b[2], c[2])
            
            c_x_min = int(math.floor(min_x / cell_size))
            c_x_max = int(math.floor(max_x / cell_size))
            c_z_min = int(math.floor(min_z / cell_size))
            c_z_max = int(math.floor(max_z / cell_size))
            
            for cx in range(c_x_min, c_x_max + 1):
                for cz in range(c_z_min, c_z_max + 1):
                    self.grid.setdefault((cx, cz), []).append(tri_idx)
        print(f"[WaterInterpolator] Spatial grid indexed in {len(self.grid)} cells.")

    def query_water(self, px, pz):
        """
        Checks if the 2D point (px, pz) lies inside any water triangle.
        Returns (is_water, y_water) where y_water is the barycentrically interpolated height.
        """
        cx = int(math.floor(px / self.cell_size))
        cz = int(math.floor(pz / self.cell_size))
        tri_indices = self.grid.get((cx, cz), [])
        
        highest_y = -9999.0
        found = False
        
        for tri_idx in tri_indices:
            a, b, c = self.triangles[tri_idx]
            
            v0x, v0z = c[0] - a[0], c[2] - a[2]
            v1x, v1z = b[0] - a[0], b[2] - a[2]
            v2x, v2z = px - a[0], pz - a[2]
            
            denom = v0x * v0x + v0z * v0z
            dot00 = denom
            dot01 = v0x * v1x + v0z * v1z
            dot02 = v0x * v2x + v0z * v2z
            dot11 = v1x * v1x + v1z * v1z
            dot12 = v1x * v2x + v1z * v2z
            
            denom = dot00 * dot11 - dot01 * dot01
            if abs(denom) < 1e-8:
                continue
                
            invDenom = 1.0 / denom
            u = (dot11 * dot02 - dot01 * dot12) * invDenom
            v = (dot00 * dot12 - dot01 * dot02) * invDenom
            
            if (u >= -1e-5) and (v >= -1e-5) and (u + v <= 1.0 + 1e-5):
                y_val = a[1] + u * (c[1] - a[1]) + v * (b[1] - a[1])
                if y_val > highest_y:
                    highest_y = y_val
                found = True
                
        if found:
            return True, highest_y
        return False, 0.0

class TerrainClassificationIndex:
    """
    Parses and indexes classification polygons (paved, dirt, grass) from OSM.
    Uses a 2D spatial grid for fast area-based lookup.
    """
    def __init__(self, json_path="export/terrain_classification.json", cell_size=200.0):
        self.cell_size = cell_size
        self.grid = {}
        self.polygons = []
        
        if not os.path.exists(json_path):
            print(f"[TerrainClassificationIndex Warning] File not found: {json_path}")
            return
            
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.polygons = json.load(f)
        except Exception as e:
            print(f"[TerrainClassificationIndex Error] Failed to read JSON: {e}")
            return
            
        # Precompute bounding boxes and approximate areas
        for poly in self.polygons:
            vertices = poly["vertices"]
            if not vertices:
                poly["bbox_area"] = 99999999.0
                poly["bbox"] = (0.0, 0.0, 0.0, 0.0)
                continue
            xs = [pt[0] for pt in vertices]
            zs = [pt[1] for pt in vertices]
            min_x, max_x = min(xs), max(xs)
            min_z, max_z = min(zs), max(zs)
            poly["bbox"] = (min_x, max_x, min_z, max_z)
            poly["bbox_area"] = (max_x - min_x) * (max_z - min_z)
            
        # Sort polygons by bounding box area ascending so that the most specific/smallest area wins
        self.polygons.sort(key=lambda p: p.get("bbox_area", 99999999.0))
        
        print(f"[TerrainClassificationIndex] Loaded {len(self.polygons)} polygons. Building spatial grid...")
        for poly_idx, poly in enumerate(self.polygons):
            if "bbox" not in poly:
                continue
            min_x, max_x, min_z, max_z = poly["bbox"]
            
            c_x_min = int(math.floor(min_x / cell_size))
            c_x_max = int(math.floor(max_x / cell_size))
            c_z_min = int(math.floor(min_z / cell_size))
            c_z_max = int(math.floor(max_z / cell_size))
            
            for cx in range(c_x_min, c_x_max + 1):
                for cz in range(c_z_min, c_z_max + 1):
                    self.grid.setdefault((cx, cz), []).append(poly_idx)
        print(f"[TerrainClassificationIndex] Spatial grid indexed in {len(self.grid)} cells.")

    def point_in_poly(self, px, pz, vertices):
        inside = False
        n = len(vertices)
        if n < 3:
            return False
        p1x, p1z = vertices[0]
        for i in range(1, n + 1):
            p2x, p2z = vertices[i % n]
            if pz > min(p1z, p2z):
                if pz <= max(p1z, p2z):
                    if px <= max(p1x, p2x):
                        if p1z != p2z:
                            xinters = (pz - p1z) * (p2x - p1x) / (p2z - p1z) + p1x
                        if p1x == p2x or px <= xinters:
                            inside = not inside
            p1x, p1z = p2x, p2z
        return inside

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

# Process-local globals for multiprocessing workers
_worker_interpolator = None
_worker_water_interpolator = None
_worker_classification_index = None
_worker_custom_blocks = None
_worker_y_offset = None

def init_worker_process(glb_path, s, tx, tz, custom_blocks, y_offset, classification_json_path=None):
    global _worker_interpolator, _worker_water_interpolator, _worker_classification_index, _worker_custom_blocks, _worker_y_offset
    _worker_interpolator = TerrainHeightInterpolator(glb_path, s, tx, tz)
    _worker_water_interpolator = TerrainWaterInterpolator(glb_path, s, tx, tz)
    _worker_classification_index = TerrainClassificationIndex(classification_json_path) if classification_json_path else None
    _worker_custom_blocks = custom_blocks
    _worker_y_offset = y_offset

def export_single_region_process_wrapper(rx, rz, pts, mca_path, min_s_y, max_s_y):
    global _worker_interpolator, _worker_water_interpolator, _worker_classification_index, _worker_custom_blocks, _worker_y_offset
    
    # Process-local cache for height coordinates
    local_cache = TerrainHeightCache()
    
    export_single_region(
        rx=rx,
        rz=rz,
        pts=pts,
        mca_path=mca_path,
        custom_blocks=_worker_custom_blocks,
        interpolator=_worker_interpolator,
        water_interpolator=_worker_water_interpolator,
        classification_index=_worker_classification_index,
        y_offset=_worker_y_offset,
        height_cache=local_cache,
        cancel_event=None,
        min_s_y=min_s_y,
        max_s_y=max_s_y
    )

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

@njit(nogil=True)
def _point_in_polygon_jit(x, z, polygon):
    inside = False
    n = len(polygon)
    if n == 0:
        return False
    p1x, p1z = polygon[0][0], polygon[0][1]
    for i in range(n + 1):
        p2x, p2z = polygon[i % n][0], polygon[i % n][1]
        if z > min(p1z, p2z):
            if z <= max(p1z, p2z):
                if x <= max(p1x, p2x):
                    if p1z != p2z:
                        xinters = (z - p1z) * (p2x - p1x) / (p2z - p1z) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1z = p2x, p2z
    return inside

def point_in_polygon(x, z, polygon):
    if HAS_NUMBA:
        if not isinstance(polygon, np.ndarray):
            polygon = np.array(polygon, dtype=np.float64)
        return _point_in_polygon_jit(float(x), float(z), polygon)
    
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

@njit(nogil=True)
def _distance_to_polygon_boundary_jit(x, z, polygon):
    min_dist = float('inf')
    n = len(polygon)
    if n == 0:
        return 0.0
    for i in range(n):
        ax, az = polygon[i][0], polygon[i][1]
        bx, bz = polygon[(i + 1) % n][0], polygon[(i + 1) % n][1]
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

def distance_to_polygon_boundary(x, z, polygon):
    if HAS_NUMBA:
        if not isinstance(polygon, np.ndarray):
            polygon = np.array(polygon, dtype=np.float64)
        return _distance_to_polygon_boundary_jit(float(x), float(z), polygon)
        
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

@njit(nogil=True)
def _find_inside_points_jit(min_x, max_x, min_z, max_z, polygon):
    max_pts = (max_x - min_x + 1) * (max_z - min_z + 1)
    xs = np.empty(max_pts, dtype=np.int32)
    zs = np.empty(max_pts, dtype=np.int32)
    dists = np.empty(max_pts, dtype=np.float64)
    
    count = 0
    for x in range(min_x, max_x + 1):
        for z in range(min_z, max_z + 1):
            if _point_in_polygon_jit(float(x), float(z), polygon):
                xs[count] = x
                zs[count] = z
                dists[count] = _distance_to_polygon_boundary_jit(float(x), float(z), polygon)
                count += 1
                
    return xs[:count], zs[:count], dists[:count]

def find_inside_points(min_x, max_x, min_z, max_z, polygon):
    if HAS_NUMBA:
        if not isinstance(polygon, np.ndarray):
            polygon = np.array(polygon, dtype=np.float64)
        return _find_inside_points_jit(min_x, max_x, min_z, max_z, polygon)
        
    xs = []
    zs = []
    dists = []
    for x in range(min_x, max_x + 1):
        for z in range(min_z, max_z + 1):
            if point_in_polygon(x, z, polygon):
                xs.append(x)
                zs.append(z)
                dists.append(distance_to_polygon_boundary(x, z, polygon))
    return np.array(xs, dtype=np.int32), np.array(zs, dtype=np.int32), np.array(dists, dtype=np.float64)

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

def print_progress(label, completed, total, start_time=None):
    """Prints a highly efficient text-based progress bar on a single line with optional speed indicator."""
    if total <= 0:
        return
    pct = int(100 * completed / total)
    filled = int(30 * completed / total)
    bar = "=" * filled + " " * (30 - filled)
    
    speed_str = ""
    if start_time is not None:
        elapsed = time.time() - start_time
        if elapsed > 0.05 and completed > 0:
            speed = completed / elapsed
            speed_str = f" @ {speed:.1f} items/s"
            
    sys.stdout.write(f"\r{label}: [{bar}] {pct}% ({completed}/{total}){speed_str}")
    sys.stdout.flush()
    if completed >= total:
        sys.stdout.write("\n")
        sys.stdout.flush()

def export_single_region(rx, rz, pts, mca_path, custom_blocks, interpolator, y_offset, height_cache, 
                         water_interpolator=None, classification_index=None, cancel_event=None, min_s_y=-4, max_s_y=20):
    """Generates MCA chunks for a single region (runs in worker thread)."""
    region = MCARegion(rx, rz)
    
    region_chunks = set()
    for cx_local in range(32):
        for cz_local in range(32):
            region_chunks.add((cx_local, cz_local))
                    
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
        
        # Load small chunk dictionary on demand to avoid OOM
        chunk_dict = custom_blocks.get_chunk_dict(cx_global, cz_global) if hasattr(custom_blocks, 'get_chunk_dict') else custom_blocks
        
        # Area-based optimization: check overlapping water triangles for this chunk
        has_chunk_water = False
        chunk_triangles = []
        if water_interpolator is not None:
            min_x_c = cx_global * 16
            max_x_c = min_x_c + 15
            min_z_c = cz_global * 16
            max_z_c = min_z_c + 15
            
            c_x_min = int(math.floor(min_x_c / water_interpolator.cell_size))
            c_x_max = int(math.floor(max_x_c / water_interpolator.cell_size))
            c_z_min = int(math.floor(min_z_c / water_interpolator.cell_size))
            c_z_max = int(math.floor(max_z_c / water_interpolator.cell_size))
            
            overlapping_tri_idx = set()
            for cx in range(c_x_min, c_x_max + 1):
                for cz in range(c_z_min, c_z_max + 1):
                    overlapping_tri_idx.update(water_interpolator.grid.get((cx, cz), []))
            
            if overlapping_tri_idx:
                chunk_triangles = [water_interpolator.triangles[idx] for idx in overlapping_tri_idx]
                has_chunk_water = True

        # Area-based optimization: check overlapping classification polygons for this chunk
        has_chunk_class = False
        chunk_polygons = []
        if classification_index is not None:
            min_x_c = cx_global * 16
            max_x_c = min_x_c + 15
            min_z_c = cz_global * 16
            max_z_c = min_z_c + 15
            
            c_x_min = int(math.floor(min_x_c / classification_index.cell_size))
            c_x_max = int(math.floor(max_x_c / classification_index.cell_size))
            c_z_min = int(math.floor(min_z_c / classification_index.cell_size))
            c_z_max = int(math.floor(max_z_c / classification_index.cell_size))
            
            overlapping_poly_idx = set()
            for cx in range(c_x_min, c_x_max + 1):
                for cz in range(c_z_min, c_z_max + 1):
                    overlapping_poly_idx.update(classification_index.grid.get((cx, cz), []))
            
            if overlapping_poly_idx:
                chunk_polygons = [classification_index.polygons[idx] for idx in overlapping_poly_idx]
                has_chunk_class = True
        
        # Pre-lookup all 256 heights, water, and class properties for this chunk
        local_heights = [0] * 256
        local_water = [None] * 256
        local_classes = [None] * 256
        
        for dz in range(16):
            z_val = cz_global * 16 + dz
            for dx in range(16):
                x_val = cx_global * 16 + dx
                cached_h = height_cache.get(x_val, z_val)
                if cached_h is None:
                    h_real = interpolator.query_height(x_val, -z_val)
                    cached_h = int(round(h_real)) - y_offset
                    height_cache.set(x_val, z_val, cached_h)
                
                is_water = False
                y_water_mc = 0
                if has_chunk_water:
                    highest_y = -9999.0
                    found = False
                    for a, b, c in chunk_triangles:
                        v0x, v0z = c[0] - a[0], c[2] - a[2]
                        v1x, v1z = b[0] - a[0], b[2] - a[2]
                        v2x, v2z = x_val - a[0], z_val - a[2]
                        
                        denom = v0x * v0x + v0z * v0z
                        dot00 = denom
                        dot01 = v0x * v1x + v0z * v1z
                        dot02 = v0x * v2x + v0z * v2z
                        dot11 = v1x * v1x + v1z * v1z
                        dot12 = v1x * v2x + v1z * v2z
                        
                        denom = dot00 * dot11 - dot01 * dot01
                        if abs(denom) < 1e-8:
                            continue
                            
                        invDenom = 1.0 / denom
                        u = (dot11 * dot02 - dot01 * dot12) * invDenom
                        v = (dot00 * dot12 - dot01 * dot02) * invDenom
                        
                        if (u >= -1e-5) and (v >= -1e-5) and (u + v <= 1.0 + 1e-5):
                            y_val = a[1] + u * (c[1] - a[1]) + v * (b[1] - a[1])
                            if y_val > highest_y:
                                highest_y = y_val
                            found = True
                            
                    if found:
                        is_water = True
                        y_water_mc = int(round(highest_y)) - y_offset
                        # Carve terrain so it is at least 3 blocks below the water surface
                        if cached_h >= y_water_mc - 2:
                            cached_h = y_water_mc - 3
                            height_cache.set(x_val, z_val, cached_h)
                            
                resolved_class = "grass"
                if has_chunk_class:
                    for poly in chunk_polygons:
                        min_x, max_x, min_z, max_z = poly["bbox"]
                        if x_val < min_x or x_val > max_x or z_val < min_z or z_val > max_z:
                            continue
                        if classification_index.point_in_poly(x_val, z_val, poly["vertices"]):
                            resolved_class = poly["class"]
                            break
                            
                local_heights[dz * 16 + dx] = cached_h
                if is_water:
                    local_water[dz * 16 + dx] = y_water_mc
                local_classes[dz * 16 + dx] = resolved_class
                
        has_custom = bool(chunk_dict)
        
        sections_nbt_list = []
        for s_y in range(min_s_y, max_s_y):
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
                        
                        block_name = chunk_dict.get((x_val, y_val, z_val)) if has_custom else None
                        if block_name is None:
                            y_terrain = local_heights[dz * 16 + dx]
                            y_water_mc = local_water[dz * 16 + dx]
                            resolved_class = local_classes[dz * 16 + dx]
                            
                            if y_water_mc is not None and y_val <= y_water_mc:
                                if y_val < y_terrain:
                                    if y_val < y_terrain - 3:
                                        block_name = "minecraft:stone"
                                    else:
                                        block_name = "minecraft:dirt"
                                elif y_val == y_terrain:
                                    block_name = "minecraft:sand"
                                else:
                                    block_name = "minecraft:water"
                            else:
                                if resolved_class == "paved":
                                    if y_val < y_terrain:
                                        block_name = "minecraft:stone"
                                    elif y_val == y_terrain:
                                        choices = ["minecraft:andesite", "minecraft:polished_andesite", "minecraft:stone_bricks"]
                                        weights = [0.6, 0.3, 0.1]
                                        block_name = get_deterministic_choice(x_val, y_val, z_val, choices, weights)
                                    else:
                                        block_name = "minecraft:air"
                                elif resolved_class == "dirt":
                                    if y_val < y_terrain - 3:
                                        block_name = "minecraft:stone"
                                    elif y_val < y_terrain:
                                        block_name = "minecraft:dirt"
                                    elif y_val == y_terrain:
                                        choices = ["minecraft:coarse_dirt", "minecraft:dirt", "minecraft:gravel"]
                                        weights = [0.6, 0.3, 0.1]
                                        block_name = get_deterministic_choice(x_val, y_val, z_val, choices, weights)
                                    else:
                                        block_name = "minecraft:air"
                                else:
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
            NBT(TAG_INT, "yPos", min_s_y),
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
            
    s = 0.8427785648661434
    tx = 28052.404303473268
    tz = -16620.3853885848
    
    cancel_event = threading.Event()
    height_cache = TerrainHeightCache()
    
    # Pre-define helper as None to prevent UnboundLocalError during early Ctrl+C
    resolver_ready = False
    y_offset = 0
    min_x, max_x, min_y, max_y = 0.0, 0.0, 0.0, 0.0
    
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
        
        final_min_x = min_x
        final_max_x = max_x
        final_min_y = min_y
        final_max_y = max_y
        if existing_bbox is not None:
            final_min_x = min(final_min_x, existing_bbox.get("min_local_x", final_min_x))
            final_max_x = max(final_max_x, existing_bbox.get("max_local_x", final_max_x))
            final_min_y = min(final_min_y, existing_bbox.get("min_local_y", final_min_y))
            final_max_y = max(final_max_y, existing_bbox.get("max_local_y", final_max_y))
        
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
        cache_path = os.path.join(output_dir, "custom_blocks_cache.npz")
        custom_blocks, last_edge_idx, last_block_idx, completed_block_indices = load_custom_blocks_cache(cache_path)
        initial_edge_idx = last_edge_idx
        initial_block_idx = last_block_idx
        
        # A. Rasterize road graph (first, so block platforms can overwrite/clip them)
        nodes = road_graph.get("nodes", [])
        edges = road_graph.get("edges", [])
        node_map = {nd["id"]: nd for nd in nodes}
        
        num_edges = len(edges)
        if last_edge_idx < num_edges:
            print(f"[Exporter] Rasterizing road network starting from index {last_edge_idx}...")
            t_start_road = time.time()
            for idx in range(last_edge_idx, num_edges):
                if cancel_event.is_set():
                    raise KeyboardInterrupt()
                ed = edges[idx]
                if (idx + 1) % 20 == 0 or idx + 1 == num_edges:
                    print_progress("[Exporter] Rasterizing road network", idx + 1, num_edges, t_start_road)
                u_nd = node_map.get(ed["u"])
                v_nd = node_map.get(ed["v"])
                if u_nd and v_nd:
                    x1, z1 = u_nd["x"], -u_nd["y"]
                    x2, z2 = v_nd["x"], -v_nd["y"]
                    
                    key = get_edge_key(ed["u"], ed["v"])
                    meta = edge_metadata.get(key, {})
                    hw = meta.get("highway", "residential")
                    name = meta.get("name", "")
                    bridge = meta.get("bridge", "")
                    layer = meta.get("layer", "")
                    is_bridge = (bridge == "yes") or (layer != "" and layer != "0" and not layer.startswith("-"))
                    
                    road_props = resolve_road_properties(name, hw)
                    width = road_props["width"]
                    lanes = road_props["lanes"]
                    surface = road_props["surface"]
                    is_rural = road_props["is_rural"]
                    marking_type = road_props["marking_type"]
                    
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
                                if not is_bridge and abs(d) == d_max:
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
                                
                                # Center markings
                                if marking_type in ["highway", "boulevard", "avenida"]:
                                    if abs(d) < 0.5 and not is_near_intersection:
                                        if marking_type == "highway":
                                            # Solid double yellow line
                                            block_name = "minecraft:yellow_concrete"
                                            is_marking = True
                                        else:
                                            # Dashed yellow line
                                            if int(math.floor(dist_along)) % 4 < 2:
                                                block_name = "minecraft:yellow_concrete"
                                                is_marking = True
                                                
                                elif marking_type == "calle":
                                    if abs(d) < 0.5 and not is_near_intersection:
                                        # Dashed white line
                                        if int(math.floor(dist_along)) % 4 < 2:
                                            block_name = "minecraft:white_concrete"
                                            is_marking = True
                                            
                                # Boulevard lane divider markings (dashed white)
                                if not is_marking and marking_type == "boulevard" and not is_near_intersection:
                                    if abs(abs(d) - 3.5) < 0.5:
                                        if int(math.floor(dist_along)) % 4 < 2:
                                            block_name = "minecraft:white_concrete"
                                            is_marking = True
                                            
                                # Side markings
                                if not is_marking and marking_type in ["highway", "boulevard", "avenida"] and not is_near_intersection:
                                    edge_d = max(1.0, math.floor(width / 2.0) - 1.0)
                                    if abs(abs(d) - edge_d) < 0.5:
                                        block_name = "minecraft:white_concrete"
                                        is_marking = True
                                        
                                if not is_marking:
                                    if surface == "asphalt_clean":
                                        choices = ["minecraft:gray_concrete", "minecraft:black_concrete"]
                                        weights = [0.8, 0.2]
                                    elif surface == "asphalt_light":
                                        choices = ["minecraft:gray_concrete_powder", "minecraft:andesite", "minecraft:gravel"]
                                        weights = [0.7, 0.2, 0.1]
                                    else:
                                        choices = [
                                            "minecraft:gray_concrete_powder",
                                            "minecraft:black_concrete_powder",
                                            "minecraft:smooth_basalt",
                                            "minecraft:cobbled_deepslate",
                                            "minecraft:coal_block"
                                        ]
                                        weights = [0.6, 0.25, 0.05, 0.05, 0.05]
                                    block_name = get_deterministic_choice(x_mc, y_mc, z_mc, choices, weights)
                                    
                            if is_bridge:
                                y_road = y_mc + 6
                                custom_blocks[(x_mc, y_road, z_mc)] = block_name
                                if (d == d_min or d == d_max) and (step % 8 == 0):
                                    for y_pil in range(y_mc, y_road):
                                        custom_blocks[(x_mc, y_pil, z_mc)] = "minecraft:cobblestone"
                            else:
                                custom_blocks[(x_mc, y_mc, z_mc)] = block_name
                last_edge_idx = idx + 1
        else:
            print("[Exporter] Road network rasterization already fully completed.")
                        
        # B. Rasterize block lots (manzanas) with perimetral sidewalks (overwriting road overlaps)
        num_blocks = len(blocks)
        completed_flags = [False] * num_blocks
        for i in completed_block_indices:
            if 0 <= i < num_blocks:
                completed_flags[i] = True
                
        if last_block_idx < num_blocks:
            workers = parallel_workers if parallel_workers > 0 else (os.cpu_count() or 4)
            print(f"[Exporter] Rasterizing block platforms in parallel using {workers} threads...")
            t_start_blocks = time.time()
            
            progress_lock = threading.Lock()
            completed_count = sum(completed_flags)
            
            # Print initial progress bar immediately
            print_progress("[Exporter] Rasterizing block platforms", completed_count, num_blocks, t_start_blocks)
            
            def progress_callback(block_idx):
                nonlocal last_block_idx, completed_count
                completed_flags[block_idx] = True
                with progress_lock:
                    completed_count += 1
                    while last_block_idx < num_blocks and completed_flags[last_block_idx]:
                        last_block_idx += 1
                    if completed_count % 50 == 0 or completed_count == num_blocks:
                        print_progress("[Exporter] Rasterizing block platforms", completed_count, num_blocks, t_start_blocks)
                        
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=workers)
            try:
                futures = {}
                for idx in range(num_blocks):
                    if completed_flags[idx]:
                        continue
                    if cancel_event.is_set():
                        break
                    b = blocks[idx]
                    f = executor.submit(
                        rasterize_single_block,
                        b, get_mc_terrain_y, cancel_event,
                        interpolator, y_offset, height_cache
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
            pass
        else:
            print("[Exporter] Block platforms rasterization already fully completed.")
            
        # Unified Cache Saving: Save if any new road edges or blocks were rasterized
        if not cancel_event.is_set():
            if last_edge_idx > initial_edge_idx or last_block_idx > initial_block_idx:
                completed_block_indices = {i for i, val in enumerate(completed_flags) if val}
                save_custom_blocks_cache(
                    cache_path, custom_blocks, last_edge_idx, last_block_idx,
                    completed_block_indices=completed_block_indices
                )
                        
        print(f"[Exporter] Rasterized {len(custom_blocks)} custom geometry blocks.")
        
        # Determine active chunk coordinates containing custom blocks
        if hasattr(custom_blocks, 'chunk_slices') and hasattr(custom_blocks, 'new_blocks_by_chunk'):
            active_chunks = set(custom_blocks.chunk_slices.keys()) | set(custom_blocks.new_blocks_by_chunk.keys())
        else:
            active_chunks = set()
            for (x, y, z) in custom_blocks.keys():
                active_chunks.add((int(math.floor(x / 16.0)), int(math.floor(z / 16.0))))
                
        regions = {}
        for (cx, cz) in active_chunks:
            rx = int(math.floor(cx / 32.0))
            rz = int(math.floor(cz / 32.0))
            regions.setdefault((rx, rz), []).append((cx * 16 + 8, 0, cz * 16 + 8))
            
        os.makedirs(region_dir, exist_ok=True)
        
        # Prioritize regions by proximity to Parque Hidalgo (0, 0)
        def region_distance(item):
            rx, rz = item[0]
            cx = rx * 512 + 256
            cz = rz * 512 + 256
            return math.sqrt(cx**2 + cz**2)
            
        sorted_regions = sorted(regions.items(), key=region_distance)
        print(f"[Exporter] Prioritized {len(sorted_regions)} regions by geographic proximity to city center.")
        
        # Determine the vertical range of the world dynamically from the GLB terrain vertices
        glb_min_y = float(interpolator.y_pts.min())
        glb_max_y = float(interpolator.y_pts.max())
        
        min_mc_y = glb_min_y - y_offset
        max_mc_y = glb_max_y - y_offset
        
        min_s_y = int(math.floor(min_mc_y / 16.0))
        max_s_y = int(math.ceil(max_mc_y / 16.0))
        
        print(f"[Exporter] Dynamic world height range: Y = [{min_s_y * 16}, {max_s_y * 16}] (Sections: {min_s_y} to {max_s_y})")

        regions_to_generate = []
        skipped_regions = 0
        for (rx, rz), pts in sorted_regions:
            mca_path = os.path.join(region_dir, f"r.{rx}.{rz}.mca")
            if os.path.exists(mca_path):
                try:
                    test_reg = MCARegion.load(mca_path, rx, rz)
                    if len(test_reg.chunks) > 0:
                        skipped_regions += 1
                        continue
                except Exception:
                    print(f"[Exporter Warning] Region r.{rx}.{rz}.mca on disk is corrupted. Re-generating...")
            regions_to_generate.append(((rx, rz), pts))
            
        if skipped_regions > 0:
            print(f"[Exporter] Incremental export: skipped {skipped_regions} already generated valid region files.")
            
        export_dir = os.path.dirname(reconstruction_json_path)
        classification_json_path = os.path.join(export_dir, "terrain_classification.json")
        from src.minecraft_pipeline.terrain_classifier import extract_and_cache_terrain_classification
        extract_and_cache_terrain_classification(reconstruction_json_path, classification_json_path)
        
        workers = parallel_workers if parallel_workers > 0 else (os.cpu_count() or 4)
        print(f"[Exporter] Generating region MCA files in parallel using {workers} processes...")
        executor = concurrent.futures.ProcessPoolExecutor(
            max_workers=workers,
            initializer=init_worker_process,
            initargs=(glb_path, s, tx, tz, custom_blocks, y_offset, classification_json_path)
        )
        try:
            futures = {}
            for (rx, rz), pts in regions_to_generate:
                mca_path = os.path.join(region_dir, f"r.{rx}.{rz}.mca")
                f = executor.submit(
                    export_single_region_process_wrapper,
                    rx, rz, pts, mca_path, min_s_y, max_s_y
                )
                futures[f] = (rx, rz)
                
            completed_regions = 0
            total_regions = len(futures)
            if total_regions > 0:
                t_start_regions = time.time()
                print_progress("[Exporter] Generating region MCA files", 0, total_regions, t_start_regions)
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
                        print_progress("[Exporter] Generating region MCA files", completed_regions, total_regions, t_start_regions)
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
        
        # Harvest completed blocks if interrupted during block platform loop
        if 'futures' in locals() and futures:
            try:
                first_val = next(iter(futures.values()))
                if isinstance(first_val, int):  # We are in the block platforms loop
                    done_futures = [f for f in futures.keys() if f.done()]
                    
                    # Merge completed block results
                    for f in done_futures:
                        b_idx = futures[f]
                        try:
                            res = f.result()
                            custom_blocks.update(res)
                            completed_flags[b_idx] = True
                        except Exception:
                            pass
                            
                    # Advance last_block_idx based on the newly merged contiguous prefix
                    while last_block_idx < num_blocks and completed_flags[last_block_idx]:
                        last_block_idx += 1
                    
                    completed_block_indices = {i for i, val in enumerate(completed_flags) if val}
            except Exception:
                pass
                
        cancel_event.set()
        if 'executor' in locals():
            executor.shutdown(wait=False, cancel_futures=True)
            
        if 'cache_path' in locals() and 'custom_blocks' in locals() and custom_blocks:
            if 'completed_block_indices' not in locals():
                if 'completed_flags' in locals():
                    completed_block_indices = {i for i, val in enumerate(completed_flags) if val}
                else:
                    completed_block_indices = None
            save_custom_blocks_cache(
                cache_path, custom_blocks, last_edge_idx, last_block_idx,
                completed_block_indices=completed_block_indices
            )
            
    # Always save height cache
    height_cache.save()
    
    # 5. Write level.dat and metadata if we calculated y_offset and resolver
    if resolver_ready:
        print("[Exporter] Finalizing level.dat settings...")
        
        # Copy the Higher Heights datapack into the world's datapacks directory first
        import shutil
        datapacks_dir = os.path.join(world_dir, "datapacks")
        os.makedirs(datapacks_dir, exist_ok=True)
        
        datapack_filename = None
        for item in os.listdir(output_dir):
            if item.endswith(".zip") and "HigherHeights" in item:
                src_path = os.path.join(output_dir, item)
                dst_path = os.path.join(datapacks_dir, item)
                shutil.copy2(src_path, dst_path)
                print(f"[Exporter] Activated Higher Heights datapack: {item}")
                datapack_filename = item
                
        # Build the datapacks NBT lists
        enabled_packs = ["vanilla"]
        if datapack_filename is not None:
            enabled_packs.append(f"file/{datapack_filename}")
            
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
            ]),
            NBT(TAG_COMPOUND, "DataPacks", [
                NBT(TAG_LIST, "Enabled", (TAG_STRING, enabled_packs)),
                NBT(TAG_LIST, "Disabled", (TAG_STRING, []))
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

def ensure_default_env(path=".env"):
    if not os.path.exists(path):
        import sys
        if sys.platform == "win32":
            userprofile = os.getenv("USERPROFILE", os.path.expanduser("~"))
            def_mod = os.path.join(userprofile, "AppData", "Roaming", ".minecraft", "saves", "TecateWorld")
        elif sys.platform == "darwin":
            def_mod = os.path.expanduser("~/Library/Application Support/minecraft/saves/TecateWorld")
        else:
            def_mod = os.path.expanduser("~/.minecraft/saves/TecateWorld")
            
        with open(path, 'w', encoding='utf-8') as f:
            f.write("# Minecraft Importer/Exporter Environment Configuration\n")
            f.write("IMPORT_JSON=export/reconstruction_export.json\n")
            f.write("GLB_PATH=models/tecate/glb/tecate.glb\n")
            f.write("FRESH_WORLD=export/minecraft_world/TecateWorld\n")
            f.write(f"MODIFIED_WORLD={def_mod.replace('\\\\', '/')}\n")
            f.write("OUTPUT_DIR=export/minecraft_world\n")
            f.write("REMOTE_HOST=HakkinDavid@hakkin.tail4b53f5.ts.net\n")
            f.write("REMOTE_PATH=~/tecate-simulator\n")
        print(f"[Exporter] Created default configuration file: {path}")

def load_env(path=".env"):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k not in os.environ:
                        os.environ[k] = v

if __name__ == "__main__":
    ensure_default_env()
    load_env()
    
    import argparse
    parser = argparse.ArgumentParser(description="Tecate to Minecraft World Exporter")
    parser.add_argument("--import-json", default=None, help="Path to reconstruction_export.json (falls back to IMPORT_JSON env var)")
    parser.add_argument("--glb-path", default=None, help="Path to terrain GLB (falls back to GLB_PATH env var)")
    parser.add_argument("--output-dir", default=None, help="Output directory for Minecraft saves (falls back to OUTPUT_DIR env var)")
    parser.add_argument("--parallel", type=int, default=0, help="Number of thread workers (0 = auto)")
    args = parser.parse_args()
    
    import_json = args.import_json or os.getenv("IMPORT_JSON") or "export/reconstruction_export.json"
    glb_path = args.glb_path or os.getenv("GLB_PATH") or "models/tecate/glb/tecate.glb"
    output_dir = args.output_dir or os.getenv("OUTPUT_DIR") or "export/minecraft_world"
    
    export_world(import_json, glb_path, output_dir, args.parallel)
