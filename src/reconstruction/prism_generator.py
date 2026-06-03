import os
import sys
import json
import math
import numpy as np
import networkx as nx
import cv2
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from src.core_io.coords import gps_to_local, local_to_gps
from src.core_io.io_manager import ensure_dir, load_json, save_json

class UrbanBlockReconstructor:
    """
    Orchestrates the historical urban block reconstruction pipeline.
    Extracts block polygons, divides long facades collinear segments,
    matches each segment to the best Layer 2 frontal facade observation,
    performs standard 2D perspective homography warping onto block vertical quads,
    and exports procedurally compiled textured glTF geometry for Blender.
    """
    def __init__(self, G: nx.MultiGraph, export_dir: str = "export", data_dir: str = "data", headless: bool = False, radius: float = None, reprocess: bool = False, skip_scraper: bool = False, harvest_only: bool = False, parallel: int = 4):
        self.G = G
        self.export_dir = export_dir
        self.data_dir = data_dir
        self.textures_dir = os.path.join(export_dir, "textures")
        self.debug_dir = os.path.join(export_dir, "debug")
        self.headless = headless
        self.radius = radius
        self.reprocess = reprocess
        self.skip_scraper = skip_scraper
        self.harvest_only = harvest_only
        self.parallel = parallel
        
        import threading
        self.cache_lock = threading.Lock()
        self.scraper_lock = threading.Lock()
        
        ensure_dir(self.textures_dir)
        ensure_dir(self.debug_dir)
        
        # Load Tecate polygon
        self.tecate_poly = []
        polygon_path = os.path.join("reference", "tecate-polygon.json")
        if os.path.exists(polygon_path):
            try:
                with open(polygon_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                features = data.get("features", [])
                if features:
                    geometry = features[0].get("geometry", {})
                    geom_type = geometry.get("type")
                    coords = geometry.get("coordinates", [])
                    if geom_type == "Polygon":
                        self.tecate_poly = coords[0]
                    elif geom_type == "MultiPolygon":
                        self.tecate_poly = coords[0][0]
                print(f"[Reconstruction] Loaded municipal polygon boundary with {len(self.tecate_poly)} vertices.")
            except Exception as e:
                print(f"[Warning] Failed to load municipal polygon: {e}")
        
        # Load stitching cache to enable fast incremental reconstruction
        self.stitching_cache_path = os.path.join(data_dir, "stitching_cache.json")
        self.stitching_cache = {}
        self.stitching_cache_changed = False
        if os.path.exists(self.stitching_cache_path):
            try:
                self.stitching_cache = load_json(self.stitching_cache_path)
            except Exception as e:
                print(f"[Warning] Failed to load stitching cache: {e}")
                
        # Initialize relational cache file paths
        self.blocks_cache_path = os.path.join(data_dir, "blocks_cache.json")
        self.panoramas_cache_path = os.path.join(data_dir, "panoramas_cache.json")
        self.facades_cache_path = os.path.join(data_dir, "facades_cache.json")
        
        # Load blocks
        self.blocks_cache = {}
        self.blocks_cache_changed = False
        if os.path.exists(self.blocks_cache_path):
            try:
                self.blocks_cache = load_json(self.blocks_cache_path)
                print(f"[Cache Load] Loaded {len(self.blocks_cache)} blocks from blocks_cache.json")
            except Exception as e:
                print(f"[Warning] Failed to load blocks cache: {e}")
        
        # Load panoramas
        self.panoramas_cache = {}
        self.panoramas_cache_changed = False
        if os.path.exists(self.panoramas_cache_path):
            try:
                self.panoramas_cache = load_json(self.panoramas_cache_path)
            except Exception as e:
                print(f"[Warning] Failed to load panoramas cache: {e}")
                
        # Load facades
        self.facades_cache = {}
        self.facades_cache_changed = False
        if os.path.exists(self.facades_cache_path):
            try:
                self.facades_cache = load_json(self.facades_cache_path)
            except Exception as e:
                print(f"[Warning] Failed to load facades cache: {e}")
                
        # Initialize and load metadata cache
        self.metadata_cache = {}
        
        if self.facades_cache:
            # Reconstruct the virtual metadata_cache in-memory for 100% backward-compatibility
            for f_id, f_data in self.facades_cache.items():
                p_id = f_data.get("pano_id")
                p_data = self.panoramas_cache.get(p_id, {})
                combined = {}
                combined.update(f_data)
                combined.update(p_data)
                combined["pano_id"] = p_id
                
                # Reconstruct derived properties dynamically using physical parameters from panoramas_cache
                lat = p_data.get("latitude")
                lon = p_data.get("longitude")
                if lat is not None and lon is not None:
                    # 1. Camera position local
                    cx, cy = gps_to_local(lat, lon)
                    combined["camera_position_local"] = [float(cx), float(cy), None]
                    
                    # 2. Camera rotation matrix
                    heading = f_data.get("captured_heading", f_data.get("heading", 0.0))
                    if heading is not None:
                        yaw_rad = math.radians(heading)
                        rot_matrix = [
                            [math.cos(yaw_rad), -math.sin(yaw_rad), 0.0],
                            [math.sin(yaw_rad), math.cos(yaw_rad), 0.0],
                            [0.0, 0.0, 1.0]
                        ]
                        combined["camera_rotation_matrix"] = rot_matrix
                        
                    # 3. Camera alignment diagnostics
                    mx_my = f_data.get("facade_midpoint_local")
                    vertices = f_data.get("facade_segment_vertices_local")
                    if mx_my and vertices and len(vertices) == 2:
                        mx, my = mx_my
                        look_vector = [float(mx - cx), float(my - cy)]
                        
                        dx = vertices[1][0] - vertices[0][0]
                        dy = vertices[1][1] - vertices[0][1]
                        length = math.sqrt(dx*dx + dy*dy)
                        if length > 0:
                            normal = [-dy / length, dx / length]
                        else:
                            normal = [0.0, 1.0]
                            
                        dot_prod = float(look_vector[0] * normal[0] + look_vector[1] * normal[1])
                        combined["camera_alignment_diagnostics"] = {
                            "look_vector": look_vector,
                            "facade_normal": [float(normal[0]), float(normal[1])],
                            "dot_product": dot_prod,
                            "is_correct_side": bool(dot_prod < 0)
                        }
                        
                    # 4. Captured URL
                    heading_val = heading if heading is not None else 0.0
                    combined["captured_url"] = f"https://www.google.com/maps?layer=c&cbll={lat},{lon}&panoid={p_id}&cbp=11,{heading_val:.2f},,0,0"

                self.metadata_cache[f_id] = combined
                
        # Bootstrap metadata cache from export/metadata.json if empty/missing
        if not self.metadata_cache:
            export_meta_path = os.path.join(export_dir, "metadata.json")
            if os.path.exists(export_meta_path):
                print(f"[Metadata Cache Bootstrap] Bootstrapping metadata cache from {export_meta_path}...")
                try:
                    export_meta = load_json(export_meta_path)
                    prov = export_meta.get("provenance", {})
                    bootstrapped = 0
                    for facade_id, data in prov.items():
                        normal = data.get("facade_normal", [0.0, 1.0])
                        heading = math.degrees(math.atan2(-normal[0], -normal[1])) % 360.0
                        self.metadata_cache[facade_id] = {
                            "pano_id": data.get("source_pano_id"),
                            "latitude": data.get("source_lat_lon", [0.0, 0.0])[0],
                            "longitude": data.get("source_lat_lon", [0.0, 0.0])[1],
                            "heading": heading,
                            "date": data.get("source_date", "")
                        }
                        bootstrapped += 1
                    if bootstrapped > 0:
                        self.save_metadata_cache()
                        print(f"[Metadata Cache Bootstrap] Successfully bootstrapped {bootstrapped} entries and saved to relational format.")
                except Exception as e:
                    print(f"[Warning] Failed to bootstrap metadata cache: {e}")

        # Load Layer 1 adjacency mapping to know which panos belong to which road edges
        self.pano_to_edge = {}
        adj_path = os.path.join(data_dir, "structural_graph", "adjacency.json")
        if os.path.exists(adj_path):
            try:
                adj = load_json(adj_path)
                for edge_id, panos in adj.get("edge_to_pano_index", {}).items():
                    for p in panos:
                        self.pano_to_edge[p] = edge_id
            except Exception as e:
                print(f"[Warning] Failed to load adjacency for reconstruction: {e}")
                
        # Initialize GoogleStreetViewScraper for direct headed/headless screenshot capturing
        if self.skip_scraper:
            self.scraper = None
            print("[Reconstruction] Running in --skip-scraper mode. Playwright browser crawling will be completely bypassed.")
        else:
            from src.data_acquisition.browser_scraper import GoogleStreetViewScraper
            self.scraper = GoogleStreetViewScraper(headless=self.headless, G=self.G)

        # Register graceful Ctrl+C handler
        import signal
        self.shutdown_in_progress = False
        self.current_blocks_data = []
        self.current_provenance = {}
        self.current_diagnostics = {}
        self.current_diag_facades = []
        def handle_sigint(signum, frame):
            if self.shutdown_in_progress:
                print("\n[Ctrl+C] Force exiting instantly!")
                import os
                os._exit(1)
                
            self.shutdown_in_progress = True
            self.graceful_shutdown()
            
        signal.signal(signal.SIGINT, handle_sigint)



        # Load existing reconstruction export to enable block-level incremental skipping
        self.existing_export_blocks = {}
        self.reconstruction_export_path = os.path.join(self.export_dir, "reconstruction_export.json")
        if not self.reprocess and os.path.exists(self.reconstruction_export_path):
            try:
                existing_data = load_json(self.reconstruction_export_path)
                if isinstance(existing_data, dict) and "blocks" in existing_data:
                    for block in existing_data["blocks"]:
                        b_id = block.get("block_id")
                        if b_id:
                            self.existing_export_blocks[b_id] = block
                print(f"[Incremental Resume] Found {len(self.existing_export_blocks)} already reconstructed blocks in {self.reconstruction_export_path}")
            except Exception as e:
                print(f"[Warning] Failed to load existing reconstruction export: {e}")

    def is_point_in_polygon(self, x: float, y: float, polygon: list) -> bool:
        """
        Ray-casting algorithm to determine if a point (x, y) is inside a polygon.
        Here, polygon is a list of [lon, lat] points, and the point is [lon, lat].
        """
        inside = False
        n = len(polygon)
        if n < 3:
            return False
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xints:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def save_stitching_cache(self):
        if not self.stitching_cache_changed:
            return
        try:
            save_json(self.stitching_cache, self.stitching_cache_path, indent=None)
            self.stitching_cache_changed = False
            print(f"[Cache Auto-Save] Stitching cache written to: {self.stitching_cache_path}")
        except Exception as e:
            print(f"[Warning] Failed to save stitching cache: {e}")

    def save_panoramas_cache(self):
        if not self.panoramas_cache_changed:
            return
        try:
            save_json(self.panoramas_cache, self.panoramas_cache_path, indent=None)
            self.panoramas_cache_changed = False
            print(f"[Cache Auto-Save] Panoramas cache written to: {self.panoramas_cache_path}")
        except Exception as e:
            print(f"[Warning] Failed to save panoramas cache: {e}")

    def save_facades_cache(self):
        if not self.facades_cache_changed:
            return
        try:
            save_json(self.facades_cache, self.facades_cache_path, indent=None)
            self.facades_cache_changed = False
            print(f"[Cache Auto-Save] Facades cache written to: {self.facades_cache_path}")
        except Exception as e:
            print(f"[Warning] Failed to save facades cache: {e}")
            
    def save_blocks_cache(self):
        if not self.blocks_cache_changed:
            return
        try:
            save_json(self.blocks_cache, self.blocks_cache_path, indent=None)
            self.blocks_cache_changed = False
            print(f"[Cache Auto-Save] Blocks cache written to: {self.blocks_cache_path}")
        except Exception as e:
            print(f"[Warning] Failed to save blocks cache: {e}")

    def _decompose_metadata_cache(self):
        """
        Decomposes the virtual in-memory self.metadata_cache into
        the two relational caches: self.panoramas_cache and self.facades_cache.
        """
        with self.cache_lock:
            for f_id, entry in self.metadata_cache.items():
                if not entry:
                    continue
                # 1. Panorama Cache
                p_id = entry.get("pano_id")
                if p_id:
                    pano_updates = {
                        "latitude": entry.get("latitude"),
                        "longitude": entry.get("longitude"),
                        "altitude": entry.get("altitude"),
                        "date": entry.get("date", ""),
                        "pitch": entry.get("pitch"),
                        "roll": entry.get("roll"),
                        "projection_yaw": entry.get("projection_yaw"),
                        "pano_yaw": entry.get("pano_yaw"),
                        "road_name": entry.get("road_name", ""),
                        "adjacent_links": entry.get("adjacent_links", []),
                        "timeline": entry.get("timeline", []),
                    }
                    if p_id not in self.panoramas_cache:
                        self.panoramas_cache[p_id] = {}
                        self.panoramas_cache_changed = True
                    for k, v in pano_updates.items():
                        if self.panoramas_cache[p_id].get(k) != v:
                            self.panoramas_cache[p_id][k] = v
                            self.panoramas_cache_changed = True
                    
                # 2. Facade Cache (Disk Optimization)
                if f_id not in self.facades_cache:
                    self.facades_cache[f_id] = {}
                    self.facades_cache_changed = True
                    
                # Wipe out only the requested optimized keys that are not stored on disk
                for key in ["camera_position_local", "image_filename", "offset_search_point_local"]:
                    if key in self.facades_cache[f_id]:
                        self.facades_cache[f_id].pop(key)
                        self.facades_cache_changed = True
                    
                facade_updates = {
                    "pano_id": p_id,
                    "block_id": entry.get("block_id"),
                    "facade_index": entry.get("facade_index"),
                    "heading": entry.get("heading"),
                    "captured_heading": entry.get("captured_heading", entry.get("heading")),
                    "resolution": entry.get("resolution", {
                        "screenshot_width": 1280,
                        "screenshot_height": 720,
                        "slice_width": 512,
                        "slice_height": 256
                    }),
                    "camera_rotation_matrix": entry.get("camera_rotation_matrix"),
                    "road_relation": entry.get("road_relation"),
                    "facade_midpoint_local": entry.get("facade_midpoint_local"),
                    "offset_search_point_gps": entry.get("offset_search_point_gps"),
                    "search_query_url": entry.get("search_query_url"),
                    "captured_url": entry.get("captured_url"),
                    "modern_pano_id": entry.get("modern_pano_id"),
                    "camera_alignment_diagnostics": entry.get("camera_alignment_diagnostics"),
                    "facade_segment_vertices_local": entry.get("facade_segment_vertices_local"),
                    "roof_color": entry.get("roof_color")
                }
                for k, v in facade_updates.items():
                    if self.facades_cache[f_id].get(k) != v:
                        self.facades_cache[f_id][k] = v
                        self.facades_cache_changed = True

    def save_metadata_cache(self):
        self._decompose_metadata_cache()
        self.save_panoramas_cache()
        self.save_facades_cache()
        self.save_blocks_cache()

    def graceful_shutdown(self):
        print("\n[Ctrl+C] Graceful shutdown triggered by user. Saving current caches...")
        self.save_stitching_cache()
        self.save_metadata_cache()
        
        # Check if we have active reconstruction progress to export
        if getattr(self, "current_blocks_data", None):
            print("[Ctrl+C] Generating coverage map and scene export files for current progress...")
            try:
                # 1. Save reconstruction_export.json
                flat_nodes = []
                for n, data in self.G.nodes(data=True):
                    flat_nodes.append({"id": n, "x": data["x"], "y": data["y"]})
                    
                flat_edges = []
                for u, v, data in self.G.edges(data=True):
                    flat_edges.append({"u": u, "v": v})
                    
                scene_doc = {
                    "road_graph": {
                        "nodes": flat_nodes,
                        "edges": flat_edges
                    },
                    "blocks": self.current_blocks_data
                }
                
                export_filepath = os.path.join(self.export_dir, "reconstruction_export.json")
                save_json(scene_doc, export_filepath)
                
                # 2. Save metadata.json
                total_facades = sum(len(bl["polygon"]) - 1 for bl in self.current_blocks_data)
                textured_facades = len(self.current_provenance)
                coverage_pct = (textured_facades / total_facades * 100.0) if total_facades > 0 else 0.0
                
                meta_out = {
                    "total_blocks": len(self.current_blocks_data),
                    "total_facades": total_facades,
                    "textured_facades": textured_facades,
                    "coverage_percentage": coverage_pct,
                    "provenance": self.current_provenance
                }
                save_json(meta_out, os.path.join(self.export_dir, "metadata.json"))
                
                # 3. Save reconstruction_diagnostics.json
                save_json(self.current_diagnostics, os.path.join(self.debug_dir, "reconstruction_diagnostics.json"))
                
                # 4. Generate coverage map
                self.generate_diagnostic_visualization(scene_doc, self.current_diag_facades, coverage_pct)
                
                # 5. Compile Blender GLB
                print("[Ctrl+C] Triggering background Blender compilation...")
                from src.main import run_blender_export
                run_blender_export()
            except Exception as e:
                print(f"[Warning] Failed to generate intermediate outputs: {e}")
                
        print("[Ctrl+C] Graceful shutdown complete. Exiting safely.")
        os._exit(0)

    def build_all_facade_segments(self) -> dict:
        """
        Builds a map of all facade segment geometries for all blocks.
        Returns a dict mapping facade_id -> {
            "A": A, "B": B, "mx": mx, "my": my, "normal": normal, "block_id": b_id, "height": height_meters, "length": norm_len
        }
        """
        raw_blocks = self.extract_block_polygons()
        facades = {}
        for rb in raw_blocks:
            b_id = rb["block_id"]
            raw_poly = rb["polygon"]
            shrunk_poly = self.shrink_polygon(raw_poly, d=6.0)
            num_verts = len(shrunk_poly) - 1
            
            centroid_x = sum(pt[0] for pt in shrunk_poly[:-1]) / num_verts
            centroid_y = sum(pt[1] for pt in shrunk_poly[:-1]) / num_verts
            dist_to_center = math.sqrt(centroid_x**2 + centroid_y**2)
            if dist_to_center < 50.0:
                height_meters = 1.0
            else:
                h = hash(b_id) % 100
                height_meters = 7.0 + (h % 3) * 2.0
                
            # Resume block parameters from blocks_cache.json if available
            if self.blocks_cache and b_id in self.blocks_cache:
                cached_block = self.blocks_cache[b_id]
                height_meters = cached_block.get("height_meters", height_meters)
                
            for f_idx in range(num_verts):
                facade_id = f"{b_id}_facade_{f_idx}"
                A = shrunk_poly[f_idx]
                B = shrunk_poly[f_idx + 1]
                mx = (A[0] + B[0]) / 2.0
                my = (A[1] + B[1]) / 2.0
                
                dx = B[0] - A[0]
                dy = B[1] - A[1]
                normal = np.array([dy, -dx])
                norm_len = np.linalg.norm(normal)
                if norm_len > 1e-5:
                    normal = normal / norm_len
                else:
                    normal = np.array([0.0, 1.0])
                    
                facades[facade_id] = {
                    "A": A,
                    "B": B,
                    "mx": mx,
                    "my": my,
                    "normal": normal,
                    "block_id": b_id,
                    "height": height_meters,
                    "length": norm_len,
                    "centroid": [centroid_x, centroid_y],
                    "raw_poly": raw_poly,
                    "shrunk_poly": shrunk_poly,
                    "facade_index": f_idx
                }
        return facades



    def extract_block_polygons(self) -> list[dict]:
        """
        Extracts closed cycles from the road graph G using planar CCW traversal,
        or resumes them from the local blocks_cache.json if available to prevent recalculation.
        """
        if self.blocks_cache:
            print(f"[Cache Resume] Resuming and filtering blocks from blocks_cache.json...")
            blocks = []
            resumed_count = 0
            for b_id, b_data in self.blocks_cache.items():
                poly = b_data["polygon"]
                if len(poly) < 3:
                    continue
                num_verts = len(poly) - 1
                centroid_x = sum(pt[0] for pt in poly[:-1]) / num_verts
                centroid_y = sum(pt[1] for pt in poly[:-1]) / num_verts
                
                # 1. Filter by active safety radius if set
                if self.radius is not None and self.radius > 0:
                    dist_to_center = math.sqrt(centroid_x**2 + centroid_y**2)
                    if dist_to_center > self.radius:
                        continue
                        
                # 2. Filter by municipal polygon boundary if loaded
                if self.tecate_poly:
                    centroid_lat, centroid_lon = local_to_gps(centroid_x, centroid_y)
                    if not self.is_point_in_polygon(centroid_lon, centroid_lat, self.tecate_poly):
                        continue
                        
                blocks.append({
                    "block_id": b_id,
                    "polygon": poly,
                    "area_sq_meters": b_data.get("area_sq_meters", 100.0),
                    "is_external": b_data.get("is_external", False)
                })
                resumed_count += 1
            print(f"[Cache Resume] Successfully resumed {resumed_count} blocks (filtered from {len(self.blocks_cache)} cache entries).")
            return blocks

        print("[Reconstruction] Trimming road network to extract urban block cycles...")
        temp_G = nx.Graph(self.G)
        
        # Prune only isolated nodes (degree == 0)
        isolated_nodes = [n for n in temp_G.nodes() if temp_G.degree(n) == 0]
        temp_G.remove_nodes_from(isolated_nodes)
        
        # Remove small isolated components (size <= 2)
        components = list(nx.connected_components(temp_G))
        for comp in components:
            if len(comp) <= 2:
                temp_G.remove_nodes_from(comp)
                
        print(f"[Reconstruction] Graph pruned. Nodes: {temp_G.number_of_nodes()}, Edges: {temp_G.number_of_edges()}")
        
        if temp_G.number_of_nodes() < 3:
            print("[Warning] Too few nodes in pruned graph to form cycles.")
            return []
            
        sorted_neighbors = {}
        for u in temp_G.nodes():
            neighbors = list(temp_G.neighbors(u))
            ux, uy = temp_G.nodes[u]["x"], temp_G.nodes[u]["y"]
            
            def get_angle(v):
                vx, vy = temp_G.nodes[v]["x"], temp_G.nodes[v]["y"]
                return math.atan2(vy - uy, vx - ux)
                
            neighbors.sort(key=get_angle)
            sorted_neighbors[u] = neighbors
            
        half_edges = []
        for u, v in temp_G.edges():
            half_edges.append((u, v))
            half_edges.append((v, u))
            
        visited = set()
        blocks = []
        
        for u, v in half_edges:
            if (u, v) not in visited:
                loop = [u]
                curr_u, curr_v = u, v
                
                while (curr_u, curr_v) not in visited:
                    visited.add((curr_u, curr_v))
                    loop.append(curr_v)
                    
                    neighbors = sorted_neighbors[curr_v]
                    try:
                        idx = neighbors.index(curr_u)
                        next_v = neighbors[(idx + 1) % len(neighbors)]
                        curr_u, curr_v = curr_v, next_v
                    except ValueError:
                        break
                        
                if len(loop) >= 4:
                    x = [temp_G.nodes[n]["x"] for n in loop]
                    y = [temp_G.nodes[n]["y"] for n in loop]
                    signed_area = 0.5 * sum(x[i] * y[(i+1)%len(loop)] - x[(i+1)%len(loop)] * y[i] for i in range(len(loop)))
                    
                    if 50.0 < abs(signed_area) < 2500000.0:
                        poly_verts = [(temp_G.nodes[n]["x"], temp_G.nodes[n]["y"]) for n in loop]
                        if signed_area < 0:
                            poly_verts.reverse()
                            
                        # Subdivide long street facades into smaller collinear segments
                        segmented_verts = self.segment_long_polygon_edges(poly_verts)
                        
                        # Calculate centroid
                        centroid_x = sum(pt[0] for pt in poly_verts[:-1]) / (len(poly_verts) - 1)
                        centroid_y = sum(pt[1] for pt in poly_verts[:-1]) / (len(poly_verts) - 1)
                        centroid_lat, centroid_lon = local_to_gps(centroid_x, centroid_y)
                        
                        # Filter by municipal boundary
                        if self.tecate_poly:
                            if not self.is_point_in_polygon(centroid_lon, centroid_lat, self.tecate_poly):
                                continue
                                
                        # Filter by radius if active
                        if self.radius is not None and self.radius > 0:
                            dist_to_center = math.sqrt(centroid_x**2 + centroid_y**2)
                            if dist_to_center > self.radius:
                                continue
                                
                        block_id = f"block_lat_{centroid_lat:.5f}_lon_{centroid_lon:.5f}"
                        
                        self.blocks_cache[block_id] = {
                            "polygon": segmented_verts,
                            "area_sq_meters": abs(signed_area),
                            "is_external": (signed_area > 0)
                        }
                        
                        blocks.append({
                            "block_id": block_id,
                            "polygon": segmented_verts,
                            "area_sq_meters": abs(signed_area),
                            "is_external": (signed_area > 0)
                        })
                        
        print(f"[Reconstruction] Detected {len(blocks)} valid urban blocks (manzanas) inside boundary.")
        if blocks:
            self.save_blocks_cache()
        return blocks

    def segment_long_polygon_edges(self, poly: list[tuple[float, float]], max_length: float = 5.0) -> list[tuple[float, float]]:
        """
        Spatially segments polygon edges longer than max_length.
        Inserts intermediate collinear vertices so they are processed as independent facade quads.
        """
        unique_verts = poly[:-1]
        N = len(unique_verts)
        new_verts = []
        
        for i in range(N):
            curr_v = unique_verts[i]
            next_v = unique_verts[(i + 1) % N]
            
            dx = next_v[0] - curr_v[0]
            dy = next_v[1] - curr_v[1]
            length = math.sqrt(dx*dx + dy*dy)
            
            new_verts.append(curr_v)
            if length > max_length:
                K = int(math.ceil(length / max_length))
                for k in range(1, K):
                    t = k / K
                    inter_v = (curr_v[0] + t * dx, curr_v[1] + t * dy)
                    new_verts.append(inter_v)
                    
        return new_verts + [new_verts[0]]

    def shrink_polygon(self, poly: list[tuple[float, float]], d: float = 6.0) -> list[tuple[float, float]]:
        """
        Offsets a 2D CCW polygon inward by d meters to represent real street standoffs,
        preserving street widths and urban spacing.
        """
        unique_verts = poly[:-1]
        N = len(unique_verts)
        new_verts = []
        
        for i in range(N):
            curr_v = np.array(unique_verts[i])
            prev_v = np.array(unique_verts[(i - 1) % N])
            next_v = np.array(unique_verts[(i + 1) % N])
            
            e1 = curr_v - prev_v
            e2 = next_v - curr_v
            
            len1 = np.linalg.norm(e1)
            len2 = np.linalg.norm(e2)
            
            if len1 < 1e-5 or len2 < 1e-5:
                new_verts.append(unique_verts[i])
                continue
                
            n1 = e1 / len1
            n2 = e2 / len2
            
            normal1 = np.array([-n1[1], n1[0]])
            normal2 = np.array([-n2[1], n2[0]])
            
            bisector = normal1 + normal2
            norm_bis = np.linalg.norm(bisector)
            
            if norm_bis < 1e-5:
                bisector = normal1
            else:
                bisector = bisector / norm_bis
                
            cos_theta = np.dot(bisector, normal1)
            cos_theta = max(0.1, cos_theta)
            offset_dist = d / cos_theta
            
            new_v = curr_v + offset_dist * bisector
            new_verts.append((float(new_v[0]), float(new_v[1])))
            
        return new_verts + [new_verts[0]]

    def get_road_distance(self, mx: float, my: float) -> tuple[float, str]:
        """
        Computes the minimum perpendicular distance from facade center M(mx, my) to all road segments in G
        using a high-performance spatial grid index.
        """
        if not hasattr(self, "grid_cells"):
            self.grid_cells = {}
            self.grid_size = 50.0 # Cell size in meters
            x_coords = [data["x"] for n, data in self.G.nodes(data=True)]
            y_coords = [data["y"] for n, data in self.G.nodes(data=True)]
            if x_coords and y_coords:
                self.xmin_g, self.xmax_g = min(x_coords), max(x_coords)
                self.ymin_g, self.ymax_g = min(y_coords), max(y_coords)
            else:
                self.xmin_g, self.xmax_g = -1000.0, 1000.0
                self.ymin_g, self.ymax_g = -1000.0, 1000.0
                
            for u, v, data in self.G.edges(data=True):
                ux, uy = self.G.nodes[u]["x"], self.G.nodes[u]["y"]
                vx, vy = self.G.nodes[v]["x"], self.G.nodes[v]["y"]
                x_min_e = min(ux, vx) - 20.0
                x_max_e = max(ux, vx) + 20.0
                y_min_e = min(uy, vy) - 20.0
                y_max_e = max(uy, vy) + 20.0
                cx_min = int(math.floor(x_min_e / self.grid_size))
                cx_max = int(math.floor(x_max_e / self.grid_size))
                cy_min = int(math.floor(y_min_e / self.grid_size))
                cy_max = int(math.floor(y_max_e / self.grid_size))
                for cx in range(cx_min, cx_max + 1):
                    for cy in range(cy_min, cy_max + 1):
                        cell_key = (cx, cy)
                        if cell_key not in self.grid_cells:
                            self.grid_cells[cell_key] = []
                        self.grid_cells[cell_key].append((u, v, data))

        cell_x = int(math.floor(mx / self.grid_size))
        cell_y = int(math.floor(my / self.grid_size))
        
        candidate_edges = []
        seen_edges = set()
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                cell_key = (cell_x + dx, cell_y + dy)
                if cell_key in self.grid_cells:
                    for u, v, data in self.grid_cells[cell_key]:
                        edge_key = (u, v, data.get("id"))
                        if edge_key not in seen_edges:
                            seen_edges.add(edge_key)
                            candidate_edges.append((u, v, data))
                            
        if not candidate_edges:
            candidate_edges = list(self.G.edges(data=True))
            
        min_dist = float("inf")
        best_edge_id = None
        
        for u, v, data in candidate_edges:
            ux, uy = self.G.nodes[u]["x"], self.G.nodes[u]["y"]
            vx, vy = self.G.nodes[v]["x"], self.G.nodes[v]["y"]
            
            dx = vx - ux
            dy = vy - uy
            seg_len_sq = dx*dx + dy*dy
            
            if seg_len_sq < 1e-5:
                dist = math.sqrt((mx - ux)**2 + (my - uy)**2)
            else:
                t = ((mx - ux) * dx + (my - uy) * dy) / seg_len_sq
                t = max(0.0, min(1.0, t))
                proj_x = ux + t * dx
                proj_y = uy + t * dy
                dist = math.sqrt((mx - proj_x)**2 + (my - proj_y)**2)
                
            if dist < min_dist:
                min_dist = dist
                best_edge_id = data.get("id")
                
        return min_dist, best_edge_id



    def extract_rectified_facade_observation_texture(
        self, 
        obs: dict, 
        A: tuple[float, float], 
        B: tuple[float, float], 
        height_meters: float,
        width: int = 512,
        height: int = 512
    ) -> Image.Image:
        """
        Projects 3D wall vertices into the flat perspective camera space of the
        frontal observation, and warps the quad region using perspective homography.
        """
        if isinstance(obs["image_path"], Image.Image):
            frontal_img = obs["image_path"].convert("RGBA")
        else:
            frontal_img = Image.open(obs["image_path"]).convert("RGBA")
            
        proj = obs["projection"]
        cam_x = proj["camera_x"]
        cam_y = proj["camera_y"]
        cam_z = proj["camera_z"]
        cam_yaw = math.radians(proj["yaw_degrees"])
        cam_fov = proj["fov_degrees"]
        W_obs = proj["image_width"]
        H_obs = proj["image_height"]
        
        # Pinhole perspective projection camera matrices
        f = (W_obs - 1) / (2.0 * math.tan(math.radians(cam_fov) / 2.0))
        
        # Orthonormal camera look, right, and up vectors
        v_look = np.array([math.sin(cam_yaw), math.cos(cam_yaw), 0.0])
        v_right = np.array([math.cos(cam_yaw), -math.sin(cam_yaw), 0.0])
        v_up = np.array([0.0, 0.0, 1.0])
        
        # 3D vertices of the flat vertical wall in world space (BL, BR, TR, TL)
        world_pts = [
            (A[0], A[1], 0.0),           # Bottom-Left
            (B[0], B[1], 0.0),           # Bottom-Right
            (B[0], B[1], height_meters),  # Top-Right
            (A[0], A[1], height_meters)   # Top-Left
        ]
        
        img_pts = []
        for X, Y, Z in world_pts:
            # Displacement relative to camera
            dx = X - cam_x
            dy = Y - cam_y
            dz = Z - cam_z
            
            # Project onto camera basis
            x_c = dx * v_right[0] + dy * v_right[1] + dz * v_right[2]
            y_c = dx * v_up[0] + dy * v_up[1] + dz * v_up[2]
            z_c = dx * v_look[0] + dy * v_look[1] + dz * v_look[2]
            
            if z_c <= 0.05:  # Point is behind or extremely close to the camera plane
                return frontal_img.resize((width, height), Image.Resampling.BILINEAR)
                
            # Perform perspective division to get pixel coordinates
            px = (W_obs - 1) / 2.0 + f * (x_c / z_c)
            py = (H_obs - 1) / 2.0 - f * (y_c / z_c)
            
            img_pts.append([px, py])
            
        # Target coordinate mapping in standard widthxheight facade texture slice
        target_pts = np.float32([
            [0, height - 1],            # Bottom-Left
            [width - 1, height - 1],    # Bottom-Right
            [width - 1, 0],      # Top-Right
            [0, 0]               # Top-Left
        ])
        
        source_pts = np.float32(img_pts)
        
        # Compute perspective homography transform matrix
        M = cv2.getPerspectiveTransform(source_pts, target_pts)
        
        # Warp perspective to straighten texture slice (Border is transparent)
        np_frontal = np.array(frontal_img)
        np_warped = cv2.warpPerspective(np_frontal, M, (width, height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        
        return Image.fromarray(np_warped, "RGBA")

    def generate_transparent_fallback(self, width=512, height=512) -> Image.Image:
        # Cache per (width, height) to avoid redundant image creation
        cache_key = (width, height)
        if not hasattr(self, "_cached_transparent_dict"):
            self._cached_transparent_dict = {}
        if cache_key not in self._cached_transparent_dict:
            self._cached_transparent_dict[cache_key] = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        return self._cached_transparent_dict[cache_key].copy()


    def crop_facade(self, img_bytes: bytes, A: tuple[float, float], B: tuple[float, float], cx: float, cy: float, heading: float) -> Image.Image:
        # Load screenshot bytes as PIL Image
        img = Image.open(BytesIO(img_bytes))
        # Ensure it is resized to 1280x720 first to be completely system-independent
        if img.size != (1280, 720):
            img = img.resize((1280, 720), Image.Resampling.BILINEAR)
            
        # Automated color-based sky and pavement auto-cropper (Normalization Step)
        np_img = np.array(img)
        H, W, C = np_img.shape
        
        # Scan from top downwards for sky (converting to int32 to avoid uint8 overflow)
        y_top = 0
        for y in range(H):
            row = np_img[y, :, 0:3].astype(np.int32)
            r, g, b = row[:, 0], row[:, 1], row[:, 2]
            sky_mask = (b > r + 25) & (b > g + 10) & (r < 120) & (g < 150) & (b > 110)
            sky_pct = np.sum(sky_mask) / W
            if sky_pct < 0.15:
                y_top = y
                break
                
        # Scan from bottom upwards for pavement
        y_bottom = H - 1
        for y in range(H - 1, -1, -1):
            row = np_img[y, :, 0:3].astype(np.int32)
            r, g, b = row[:, 0], row[:, 1], row[:, 2]
            pave_mask = (np.abs(r - g) < 20) & (np.abs(g - b) < 30) & (110 < r) & (r < 210) & (105 < g) & (g < 200) & (95 < b) & (b < 190)
            pave_pct = np.sum(pave_mask) / W
            if pave_pct < 0.15:
                y_bottom = y
                break
                
        # Apply padding and bounds checking
        y_top_crop = max(0, y_top - 15)
        if y_top_crop > H // 2:
            y_top_crop = 180  # safe default
            
        y_bottom_crop = min(H - 1, y_bottom + 15)
        if y_bottom_crop < H // 2:
            y_bottom_crop = 540  # safe default
            
        # Compute exact horizontal bounds of segment AB via perspective projection
        cam_yaw = math.radians(heading)
        cam_fov = 75.0 
        f = (W - 1) / (2.0 * math.tan(math.radians(cam_fov) / 2.0))
        
        v_look = np.array([math.sin(cam_yaw), math.cos(cam_yaw)])
        v_right = np.array([math.cos(cam_yaw), -math.sin(cam_yaw)])
        
        # Project A
        dx_A = A[0] - cx
        dy_A = A[1] - cy
        x_c_A = dx_A * v_right[0] + dy_A * v_right[1]
        z_c_A = dx_A * v_look[0] + dy_A * v_look[1]
        
        # Project B
        dx_B = B[0] - cx
        dy_B = B[1] - cy
        x_c_B = dx_B * v_right[0] + dy_B * v_right[1]
        z_c_B = dx_B * v_look[0] + dy_B * v_look[1]
        
        # Perspective projection to pixel columns
        px_A = (W - 1) / 2.0 + f * (x_c_A / max(0.1, z_c_A))
        px_B = (W - 1) / 2.0 + f * (x_c_B / max(0.1, z_c_B))
        
        x_start = int(max(0, min(px_A, px_B)))
        x_end = int(min(W - 1, max(px_A, px_B)))
        
        # Safe fallback if projection returns degenerate width
        if x_end - x_start < 50:
            x_start = 0
            x_end = W - 1
            
        # Crop the isolated, horizontally aligned facade strip
        cropped = img.crop((x_start, y_top_crop, x_end, y_bottom_crop))
        
        # Resize to standard texture size 512x256 (RGBA)
        return cropped.resize((512, 256), Image.Resampling.BILINEAR).convert("RGBA")

    def estimate_facade_segment_height(self, p_id: str, heading_val: float, seg: dict) -> float:
        """
        Lightweight helper to estimate the building height for a single segment from its panorama.
        """
        # Get panorama screenshot path
        pano_filename = f"{p_id}_yaw_{heading_val:.2f}.png"
        pano_screenshot_path = os.path.abspath(os.path.join(self.data_dir, "screenshots", "pano", pano_filename))
        if not os.path.exists(pano_screenshot_path):
            return 4.0
            
        try:
            img = Image.open(pano_screenshot_path).convert("RGBA")
            W, H = img.size
            np_img = np.array(img)
            
            cam_z = 2.5
            cam_yaw = math.radians(heading_val)
            cam_fov = 75.0
            c_x = (W - 1) / 2.0
            c_y = (H - 1) / 2.0
            f = (W - 1) / (2.0 * math.tan(math.radians(cam_fov) / 2.0))
            
            v_look = np.array([math.sin(cam_yaw), math.cos(cam_yaw)])
            v_right = np.array([math.cos(cam_yaw), -math.sin(cam_yaw)])
            
            p_data = self.panoramas_cache[p_id]
            cx, cy = gps_to_local(p_data["latitude"], p_data["longitude"])
            
            # Project endpoints to get column range
            img_columns = []
            for pt in [seg["A"], seg["B"]]:
                dx = pt[0] - cx
                dy = pt[1] - cy
                x_c = dx * v_right[0] + dy * v_right[1]
                z_c = dx * v_look[0] + dy * v_look[1]
                if z_c > 0.05:
                    px = c_x + f * (x_c / z_c)
                    img_columns.append(px)
            
            if img_columns:
                col_min = int(max(0, min(img_columns)))
                col_max = int(min(W - 1, max(img_columns)))
            else:
                return 4.0
                
            if col_max - col_min < 10:
                col_min = 0
                col_max = W - 1
                
            scanned_columns = range(col_min, col_max + 1, 8)
            solved_heights = []
            
            for x in scanned_columns:
                # Local sky profile
                x_start = max(0, x - 5)
                x_end = min(W - 1, x + 5)
                sky_local = np_img[0:15, x_start:x_end, 0:3]
                sky_mean = np.mean(sky_local, axis=(0, 1))
                
                detected_y = None
                y_max_search = int(H * 0.7)
                if y_max_search > 15:
                    colors = np_img[15:y_max_search, x, 0:3].astype(float)
                    next_colors = np_img[16:y_max_search+1, x, 0:3].astype(float)
                    dists = np.linalg.norm(colors - sky_mean, axis=1)
                    grads = np.linalg.norm(next_colors - colors, axis=1)
                    valid_indices = np.where((dists > 35.0) & (grads > 15.0))[0]
                    if len(valid_indices) > 0:
                        detected_y = 15 + valid_indices[0]
                        
                if detected_y is not None:
                    # Ray direction and depth solving
                    r = (x - c_x) / f
                    Vx = r * v_right[0] + v_look[0]
                    Vy = r * v_right[1] + v_look[1]
                    
                    A, B = seg["A"], seg["B"]
                    Ux = B[0] - A[0]
                    Uy = B[1] - A[1]
                    dx_cam = A[0] - cx
                    dy_cam = A[1] - cy
                    
                    det = Ux * Vy - Uy * Vx
                    z_c_x = None
                    if abs(det) > 1e-5:
                        s_val = (dy_cam * Ux - dx_cam * Uy) / det
                        t_val = (Vx * dy_cam - Vy * dx_cam) / det
                        if 0.0 <= t_val <= 1.0 and s_val > 0.05:
                            pt_x = A[0] + t_val * Ux
                            pt_y = A[1] + t_val * Uy
                            z_c_x = (pt_x - cx) * v_look[0] + (pt_y - cy) * v_look[1]
                            
                    if z_c_x is None:
                        mx = seg["mx"]
                        my = seg["my"]
                        z_c_x = (mx - cx) * v_look[0] + (my - cy) * v_look[1]
                        
                    if z_c_x < 0.1:
                        z_c_x = 0.1
                        
                    H_solved = cam_z + z_c_x * ((c_y - detected_y) / f)
                    solved_heights.append(H_solved)
                    
            if solved_heights:
                return float(np.clip(np.median(solved_heights), 3.2, 6.5))
        except Exception:
            pass
            
        return 4.0

    def mask_sky_in_panorama(
        self,
        image_path: str,
        cx: float,
        cy: float,
        heading: float,
        height_meters: float,
        group_segments: list[dict]
    ) -> Image.Image:
        """
        Traces the roofline boundary based on the unified block height_meters and local sky color,
        and masks the sky by setting its alpha channel to zero.
        """
        img = Image.open(image_path).convert("RGBA")
        W, H = img.size
        np_img = np.array(img)
        
        cam_z = 2.5
        cam_yaw = math.radians(heading)
        cam_fov = 75.0
        c_x = (W - 1) / 2.0
        c_y = (H - 1) / 2.0
        f = (W - 1) / (2.0 * math.tan(math.radians(cam_fov) / 2.0))
        
        v_look = np.array([math.sin(cam_yaw), math.cos(cam_yaw)])
        v_right = np.array([math.cos(cam_yaw), -math.sin(cam_yaw)])
        
        # Calculate roofline column projection for the height_meters
        img_columns = []
        for seg in group_segments:
            for pt in [seg["A"], seg["B"]]:
                dx = pt[0] - cx
                dy = pt[1] - cy
                x_c = dx * v_right[0] + dy * v_right[1]
                z_c = dx * v_look[0] + dy * v_look[1]
                if z_c > 0.05:
                    px = c_x + f * (x_c / z_c)
                    img_columns.append(px)
                    
        if img_columns:
            col_min = int(max(0, min(img_columns)))
            col_max = int(min(W - 1, max(img_columns)))
        else:
            col_min = 0
            col_max = W - 1
            
        if col_max - col_min < 20:
            col_min = 0
            col_max = W - 1
            
        # We trace the roofline per column
        y_roof_all = np.zeros(W)
        scanned_columns = range(col_min, col_max + 1, 8)
        y_roofs_dict = {}
        
        for x in scanned_columns:
            r = (x - c_x) / f
            Vx = r * v_right[0] + v_look[0]
            Vy = r * v_right[1] + v_look[1]
            
            z_c_x = None
            for seg in group_segments:
                A, B = seg["A"], seg["B"]
                Ux = B[0] - A[0]
                Uy = B[1] - A[1]
                dx_cam = A[0] - cx
                dy_cam = A[1] - cy
                
                det = Ux * Vy - Uy * Vx
                if abs(det) > 1e-5:
                    s_val = (dy_cam * Ux - dx_cam * Uy) / det
                    t_val = (Vx * dy_cam - Vy * dx_cam) / det
                    if 0.0 <= t_val <= 1.0 and s_val > 0.05:
                        pt_x = A[0] + t_val * Ux
                        pt_y = A[1] + t_val * Uy
                        z_c_x = (pt_x - cx) * v_look[0] + (pt_y - cy) * v_look[1]
                        break
                        
            if z_c_x is None:
                mx_val = group_segments[0]["mx"]
                my_val = group_segments[0]["my"]
                z_c_x = (mx_val - cx) * v_look[0] + (my_val - cy) * v_look[1]
                
            if z_c_x < 0.1:
                z_c_x = 0.1
                
            y_proj = c_y - f * ((height_meters - cam_z) / z_c_x)
            
            x_start = max(0, x - 5)
            x_end = min(W - 1, x + 5)
            sky_local = np_img[0:15, x_start:x_end, 0:3]
            sky_mean = np.mean(sky_local, axis=(0, 1))
            
            refined_y = int(np.clip(y_proj, 15, H * 0.7))
            
            best_y = refined_y
            y_min = max(15, refined_y - 25)
            y_max = min(H - 2, refined_y + 25)
            if y_max > y_min:
                colors = np_img[y_min:y_max, x, 0:3].astype(float)
                next_colors = np_img[y_min+1:y_max+1, x, 0:3].astype(float)
                dists = np.linalg.norm(colors - sky_mean, axis=1)
                grads = np.linalg.norm(next_colors - colors, axis=1)
                valid_indices = np.where((dists > 35.0) & (grads > 15.0))[0]
                if len(valid_indices) > 0:
                    best_y = y_min + valid_indices[0]
                        
            y_roofs_dict[x] = best_y
            
        if len(y_roofs_dict) >= 2:
            sorted_x = sorted(y_roofs_dict.keys())
            sorted_y = [y_roofs_dict[x] for x in sorted_x]
            y_roof_all = np.interp(np.arange(W), sorted_x, sorted_y)
        elif len(y_roofs_dict) == 1:
            y_roof_all[:] = list(y_roofs_dict.values())[0]
        else:
            mx_val = group_segments[0]["mx"]
            my_val = group_segments[0]["my"]
            D = max(0.1, (mx_val - cx) * v_look[0] + (my_val - cy) * v_look[1])
            y_fallback = c_y - f * ((height_meters - cam_z) / D)
            y_roof_all[:] = np.clip(y_fallback, 15, H * 0.7)
            
        for x in range(W):
            y_roof_limit = int(y_roof_all[x])
            np_img[0:y_roof_limit, x, 3] = 0
            
        return Image.fromarray(np_img, "RGBA")

    def is_block_complete(self, b_id: str) -> bool:
        """
        Checks if a block in self.existing_export_blocks has any street-facing facades
        that are missing from self.facades_cache, or are in cache but missing from disk.
        """
        if b_id not in self.existing_export_blocks:
            return False
            
        existing_block = self.existing_export_blocks[b_id]
        poly = existing_block["polygon"]
        num_verts = len(poly) - 1
        for f_idx in range(num_verts):
            f_id = f"{b_id}_facade_{f_idx}"
            tex_path = existing_block.get("facade_textures", {}).get(f_id)
            if not tex_path or "transparent_facade.png" in tex_path or tex_path == "untextured":
                A = poly[f_idx]
                B = poly[f_idx + 1]
                mx = (A[0] + B[0]) / 2.0
                my = (A[1] + B[1]) / 2.0
                road_dist, _ = self.get_road_distance(mx, my)
                if road_dist <= 20.0:
                    with self.cache_lock:
                        f_cache = self.facades_cache.get(f_id)
                    if not f_cache:
                        return False
                    p_id = f_cache.get("pano_id")
                    if p_id:
                        heading_val = f_cache.get("captured_heading", f_cache.get("heading", 0.0))
                        pano_filename = f"{p_id}_yaw_{heading_val:.2f}.png"
                        pano_screenshot_path = os.path.join(self.data_dir, "screenshots", "pano", pano_filename)
                        if not os.path.exists(pano_screenshot_path):
                            return False
        return True

    def resolve_almost_adjacent_fallback_segments(self, block_segments_info: list[dict], fallback_path: str) -> None:
        """
        Scans block segments to find fallback segments (pano_id is None) that are within distance of 2
        from a textured segment, and assigns them to the best adjacent panorama.
        """
        N = len(block_segments_info)
        
        # We repeat for a couple of passes to allow absorption of runs of up to 2 fallback segments
        for pass_idx in range(2):
            for i in range(N):
                seg = block_segments_info[i]
                if seg["pano_id"] is not None:
                    continue
                    
                # Find nearest textured neighbors circularly
                left_seg = None
                for step in range(1, 3):
                    idx = (i - step) % N
                    if block_segments_info[idx]["pano_id"] is not None:
                        left_seg = block_segments_info[idx]
                        break
                        
                right_seg = None
                for step in range(1, 3):
                    idx = (i + step) % N
                    if block_segments_info[idx]["pano_id"] is not None:
                        right_seg = block_segments_info[idx]
                        break
                        
                if left_seg is None and right_seg is None:
                    continue
                    
                best_neighbor = None
                if left_seg is not None and right_seg is None:
                    best_neighbor = left_seg
                elif right_seg is not None and left_seg is None:
                    best_neighbor = right_seg
                else:
                    # Both L and R are available! Choose the one with the better camera look-angle alignment (higher dot product)
                    try:
                        dot_L = abs(np.dot(left_seg["normal"], [math.sin(math.radians(left_seg["heading"])), math.cos(math.radians(left_seg["heading"]))]))
                        dot_R = abs(np.dot(right_seg["normal"], [math.sin(math.radians(right_seg["heading"])), math.cos(math.radians(right_seg["heading"]))]))
                        
                        if dot_L >= dot_R:
                            best_neighbor = left_seg
                        else:
                            best_neighbor = right_seg
                    except Exception:
                        best_neighbor = left_seg
                        
                if best_neighbor is not None:
                    seg["pano_id"] = best_neighbor["pano_id"]
                    seg["heading"] = best_neighbor["heading"]
                    # Add to facades_cache relationally so it is persisted and resumed cleanly
                    facade_id = seg["facade_id"]
                    with self.cache_lock:
                        self.facades_cache[facade_id] = {
                            "pano_id": seg["pano_id"],
                            "heading": seg["heading"],
                            "captured_heading": seg["heading"]
                        }
                        self.facades_cache_changed = True
                        self.metadata_cache[facade_id] = {}
                        self.metadata_cache[facade_id].update(self.facades_cache[facade_id])
                        self.metadata_cache[facade_id].update(self.panoramas_cache[seg["pano_id"]])

    def cardinal_from_normal(self, normal):
        nx, ny = normal[0], normal[1]
        if abs(nx) > abs(ny):
            return "east" if nx > 0 else "west"
        else:
            return "north" if ny > 0 else "south"

    def save_checkpoint_helper(self, blocks_data, provenance, diagnostics, textured_facades):
        print(f"[Checkpoint] Auto-saving progress...")
        flat_nodes = []
        for n, data in self.G.nodes(data=True):
            flat_nodes.append({"id": n, "x": data["x"], "y": data["y"]})
        flat_edges = []
        for u, v, data in self.G.edges(data=True):
            flat_edges.append({"u": u, "v": v})
        scene_doc = {
            "road_graph": {
                "nodes": flat_nodes,
                "edges": flat_edges
            },
            "blocks": blocks_data
        }
        save_json(scene_doc, self.reconstruction_export_path)
        
        temp_total_facades = sum(len(bl["polygon"]) - 1 for bl in blocks_data)
        temp_meta_out = {
            "total_blocks": len(blocks_data),
            "total_facades": temp_total_facades,
            "textured_facades": textured_facades,
            "coverage_percentage": (textured_facades / temp_total_facades * 100.0) if temp_total_facades > 0 else 0.0,
            "provenance": provenance
        }
        save_json(temp_meta_out, os.path.join(self.export_dir, "metadata.json"))
        
        save_json(diagnostics, os.path.join(self.debug_dir, "reconstruction_diagnostics.json"))
        self.save_stitching_cache()
        self.save_metadata_cache()

    def reconstruct_single_block(self, rb, fallback_path) -> dict:
        b_id = rb["block_id"]
        
        # 1. External boundary check
        if rb.get("is_external", False):
            return None
            
        # 2. Incremental block skipping check
        with self.cache_lock:
            in_existing = b_id in self.existing_export_blocks
        if not self.reprocess and in_existing:
            should_skip = True
            if not self.skip_scraper:
                should_skip = self.is_block_complete(b_id)
            if should_skip:
                with self.cache_lock:
                    existing_block = self.existing_export_blocks[b_id]
                
                blocks_data_entry = existing_block
                local_provenance = {}
                local_diagnostics = {}
                local_diag_facades = []
                
                poly = existing_block["polygon"]
                num_verts = len(poly) - 1
                
                # Recover provenance
                facade_textures = existing_block.get("facade_textures", {})
                for f_id, tex_path in facade_textures.items():
                    if "transparent_facade.png" not in tex_path:
                        with self.cache_lock:
                            f_cache = self.facades_cache.get(f_id) or {}
                            p_id = f_cache.get("pano_id")
                            p_data = self.panoramas_cache.get(p_id, {}) if p_id else {}
                        
                        if p_id:
                            f_idx = int(f_id.split("_")[-1])
                            A = poly[f_idx]
                            B = poly[f_idx+1]
                            dx = B[0] - A[0]
                            dy = B[1] - A[1]
                            length = math.sqrt(dx*dx + dy*dy)
                            normal = [dy / length, -dx / length] if length > 0 else [0.0, 1.0]
                            
                            prov = {
                                "source_pano_id": p_id,
                                "source_date": p_data.get("date", ""),
                                "source_lat_lon": [p_data.get("latitude", 0.0), p_data.get("longitude", 0.0)],
                                "facade_normal": normal,
                                "projection_parameters": {
                                    "cam_z": 2.5,
                                    "height_meters": float(existing_block.get("height_meters", 8.0)),
                                    "facade_length": float(length)
                                }
                            }
                            local_provenance[f_id] = prov
                            
                # Reconstruct diagnostics for this block
                for f_idx in range(num_verts):
                    f_id = f"{b_id}_facade_{f_idx}"
                    with self.cache_lock:
                        f_cache = self.facades_cache.get(f_id) or {}
                        p_id = f_cache.get("pano_id")
                        p_data = self.panoramas_cache.get(p_id, {}) if p_id else {}
                    
                    is_textured = (f_id in local_provenance)
                    status = "textured" if is_textured else "fallback"
                    
                    A = poly[f_idx]
                    B = poly[f_idx + 1]
                    mx = (A[0] + B[0]) / 2.0
                    my = (A[1] + B[1]) / 2.0
                    dx = B[0] - A[0]
                    dy = B[1] - A[1]
                    length = math.sqrt(dx*dx + dy*dy)
                    normal_list = [dy / length, -dx / length] if length > 0 else [0.0, 1.0]
                    
                    local_diag_facades.append({
                        "facade_id": f_id,
                        "A": A, "B": B, "mx": mx, "my": my, "normal": normal_list,
                        "status": status,
                        "best_obs": {
                            "metadata": {
                                "latitude": p_data.get("latitude", 0.0),
                                "longitude": p_data.get("longitude", 0.0)
                            }
                        } if is_textured else None
                    })
                    local_diagnostics[f_id] = {
                        "facade_id": f_id,
                        "midpoint": [float(mx), float(my)],
                        "normal": normal_list,
                        "is_street_facing": True,
                        "road_distance_meters": (f_cache.get("road_relation") or {}).get("road_distance_meters", 0.0),
                        "status": status
                    }
                    
                return {
                    "block_data": blocks_data_entry,
                    "provenance": local_provenance,
                    "diagnostics": local_diagnostics,
                    "diag_facades": local_diag_facades,
                    "newly_resolved": False
                }

        raw_poly = rb["polygon"]
        local_diag_facades = []
        local_provenance = {}
        local_diagnostics = {}
        
        # Shrink polygon inward by 6.0m to establish street setback boundaries
        shrunk_poly = self.shrink_polygon(raw_poly, d=6.0)
        num_verts = len(shrunk_poly) - 1
        centroid_x = sum(pt[0] for pt in shrunk_poly[:-1]) / num_verts
        centroid_y = sum(pt[1] for pt in shrunk_poly[:-1]) / num_verts
        
        dist_to_center = math.sqrt(centroid_x**2 + centroid_y**2)
        h = hash(b_id) % 100
        height_meters = 7.0 + (h % 3) * 2.0
        
        with self.cache_lock:
            if self.blocks_cache and b_id in self.blocks_cache:
                height_meters = self.blocks_cache[b_id].get("height_meters", height_meters)
        
        facade_textures_map = {}
        uv_mappings = {}
        
        # Pre-pass: Resolve and cache all targeted facade segments for the block
        block_segments_info = []
        for f_idx in range(num_verts):
            facade_id = f"{b_id}_facade_{f_idx}"
            A = shrunk_poly[f_idx]
            B = shrunk_poly[f_idx + 1]
            mx = (A[0] + B[0]) / 2.0
            my = (A[1] + B[1]) / 2.0
            dx = B[0] - A[0]
            dy = B[1] - A[1]
            normal = np.array([dy, -dx])
            norm_len = np.linalg.norm(normal)
            if norm_len > 1e-5:
                normal = normal / norm_len
            else:
                normal = np.array([0.0, 1.0])
                
            with self.cache_lock:
                is_cached = facade_id in self.facades_cache
            
            # We always compute road_dist and best_edge_id dynamically from the road graph
            road_dist, best_edge_id = self.get_road_distance(mx, my)
            is_street_facing = (road_dist <= 20.0)
            
            if is_cached:
                with self.cache_lock:
                    entry = self.facades_cache[facade_id]
                pano_id = entry.get("pano_id")
                heading = entry.get("captured_heading", entry.get("heading"))
                if heading is not None:
                    heading = round(heading, 2)
            else:
                pano_id = None
                heading = None
            
            # Check if this segment belongs to a block within active radius or is cached
            if is_cached or (is_street_facing and (self.radius is None or self.radius < 0 or dist_to_center <= self.radius)):
                if is_cached:
                    with self.cache_lock:
                        entry = self.facades_cache[facade_id]
                        p_data = self.panoramas_cache.get(pano_id, {})
                    
                    cam_lat = p_data.get("latitude")
                    cam_lon = p_data.get("longitude")
                    if cam_lat is not None and cam_lon is not None:
                        cx, cy = gps_to_local(cam_lat, cam_lon)
                        yaw_rad = math.radians(heading)
                        rot_matrix = [
                            [math.cos(yaw_rad), -math.sin(yaw_rad), 0.0],
                            [math.sin(yaw_rad), math.cos(yaw_rad), 0.0],
                            [0.0, 0.0, 1.0]
                        ]
                        with self.cache_lock:
                            road_name_val = self.road_name_by_id.get(best_edge_id, "")
                                    
                        look_vector = [float(mx - cx), float(my - cy)]
                        dot_prod = float(look_vector[0] * normal[0] + look_vector[1] * normal[1])
                        is_correct_side = bool(dot_prod < 0)
                        
                        search_x = mx + 8.0 * normal[0]
                        search_y = my + 8.0 * normal[1]
                        lat, lon = local_to_gps(search_x, search_y)
                        search_query_url = f"https://maps.googleapis.com/maps/api/js/GeoPhotoService.SingleImageSearch?pb=!1m5!1sapiv3!5sUS!11m2!1m1!1b0!2m4!1m2!3d{lat:.6f}!4d{lon:.6f}!2d50.0!3m10!2m2!1ses!2sMX!9m1!1e2!11m4!1m3!1e2!2b1!3e2!4m9!1e1!1e2!1e3!1e4!1e6!1e8!1e12!5m0!6m0&callback=_xdc_._v2mub5"
                        captured_url = f"https://www.google.com/maps?layer=c&cbll={cam_lat},{cam_lon}&panoid={pano_id}&cbp=11,{heading:.2f},,0,0"
                        
                        with self.cache_lock:
                            self.facades_cache[facade_id] = {
                                "pano_id": pano_id,
                                "block_id": b_id,
                                "facade_index": int(f_idx),
                                "heading": heading,
                                "captured_heading": heading,
                                "resolution": {
                                    "screenshot_width": 1280,
                                    "screenshot_height": 720,
                                    "slice_width": 512,
                                    "slice_height": 256
                                },
                                "camera_position_local": [float(cx), float(cy), None],
                                "camera_rotation_matrix": rot_matrix,
                                "road_relation": {
                                    "road_name": road_name_val,
                                    "road_distance_meters": float(road_dist),
                                    "road_edge_id": best_edge_id
                                },
                                "facade_midpoint_local": [float(mx), float(my)],
                                "offset_search_point_local": [float(search_x), float(search_y)],
                                "offset_search_point_gps": [float(lat), float(lon)],
                                "search_query_url": search_query_url,
                                "captured_url": captured_url,
                                "modern_pano_id": entry.get("modern_pano_id", pano_id),
                                "camera_alignment_diagnostics": {
                                    "look_vector": look_vector,
                                    "facade_normal": [float(normal[0]), float(normal[1])],
                                    "dot_product": dot_prod,
                                    "is_correct_side": is_correct_side
                                },
                                "facade_segment_vertices_local": [A, B]
                            }
                            self.facades_cache_changed = True
                            self.metadata_cache[facade_id] = {}
                            self.metadata_cache[facade_id].update(self.facades_cache[facade_id])
                            self.metadata_cache[facade_id].update(self.panoramas_cache[pano_id])
                else:
                    search_x = mx + 8.0 * normal[0]
                    search_y = my + 8.0 * normal[1]
                    lat, lon = local_to_gps(search_x, search_y)
                    heading = math.degrees(math.atan2(-normal[0], -normal[1])) % 360.0
                    heading = round(heading, 2)
                    
                    meta = None
                    if self.scraper is not None:
                        with self.scraper_lock:
                            print(f"[API Query] Fetching metadata for new target {facade_id}...")
                            meta = self.scraper.fetch_public_metadata(lat=lat, lon=lon)
                            
                        if meta:
                            pano_id = meta["pano_id"]
                            cam_lat = meta["latitude"]
                            cam_lon = meta["longitude"]
                            
                            timeline = meta.get("timeline", [])
                            oldest_pano_id = pano_id
                            oldest_date = meta.get("date", "9999-12")
                            for tl in timeline:
                                tl_id = tl["pano_id"]
                                tl_date = tl["date"]
                                if tl_date and tl_date < oldest_date:
                                    oldest_pano_id = tl_id
                                    oldest_date = tl_date
                                    
                            if oldest_pano_id != pano_id:
                                print(f"[Temporal Chronology] Found older timeline state: {oldest_pano_id} ({oldest_date}) replaces modern {pano_id}.")
                                with self.scraper_lock:
                                    oldest_meta = self.scraper.fetch_public_metadata(pano_id=oldest_pano_id)
                                if oldest_meta:
                                    meta = oldest_meta
                                    pano_id = oldest_pano_id
                                    cam_lat = meta["latitude"]
                                    cam_lon = meta["longitude"]
                                    
                            cx, cy = gps_to_local(cam_lat, cam_lon)
                            yaw_rad = math.radians(heading)
                            rot_matrix = [
                                [math.cos(yaw_rad), -math.sin(yaw_rad), 0.0],
                                [math.sin(yaw_rad), math.cos(yaw_rad), 0.0],
                                [0.0, 0.0, 1.0]
                            ]
                            
                            with self.cache_lock:
                                self.panoramas_cache[pano_id] = {
                                    "latitude": cam_lat,
                                    "longitude": cam_lon,
                                    "altitude": meta.get("altitude"),
                                    "date": meta.get("date", ""),
                                    "pitch": meta.get("pitch"),
                                    "roll": meta.get("roll"),
                                    "projection_yaw": meta.get("projection_yaw"),
                                    "pano_yaw": meta.get("projection_yaw"),
                                    "road_name": meta.get("road_name", ""),
                                    "adjacent_links": meta.get("adjacent_links", []),
                                    "timeline": meta.get("timeline", []),
                                }
                                self.panoramas_cache_changed = True
                                
                                road_name_val = self.road_name_by_id.get(best_edge_id, "")
                                            
                                look_vector = [float(mx - cx), float(my - cy)]
                                dot_prod = float(look_vector[0] * normal[0] + look_vector[1] * normal[1])
                                is_correct_side = bool(dot_prod < 0)
                                
                                search_query_url = f"https://maps.googleapis.com/maps/api/js/GeoPhotoService.SingleImageSearch?pb=!1m5!1sapiv3!5sUS!11m2!1m1!1b0!2m4!1m2!3d{lat:.6f}!4d{lon:.6f}!2d50.0!3m10!2m2!1ses!2sMX!9m1!1e2!11m4!1m3!1e2!2b1!3e2!4m9!1e1!1e2!1e3!1e4!1e6!1e8!1e12!5m0!6m0&callback=_xdc_._v2mub5"
                                captured_url = f"https://www.google.com/maps?layer=c&cbll={cam_lat},{cam_lon}&panoid={pano_id}&cbp=11,{heading:.2f},,0,0"
                                
                                self.facades_cache[facade_id] = {
                                    "pano_id": pano_id,
                                    "block_id": b_id,
                                    "facade_index": int(f_idx),
                                    "heading": heading,
                                    "captured_heading": heading,
                                    "resolution": {
                                        "screenshot_width": 1280,
                                        "screenshot_height": 720,
                                        "slice_width": 512,
                                        "slice_height": 256
                                    },
                                    "camera_position_local": [float(cx), float(cy), None],
                                    "camera_rotation_matrix": rot_matrix,
                                    "road_relation": {
                                        "road_name": road_name_val,
                                        "road_distance_meters": float(road_dist),
                                        "road_edge_id": best_edge_id
                                    },
                                    "facade_midpoint_local": [float(mx), float(my)],
                                    "offset_search_point_local": [float(search_x), float(search_y)],
                                    "offset_search_point_gps": [float(lat), float(lon)],
                                    "search_query_url": search_query_url,
                                    "captured_url": captured_url,
                                    "modern_pano_id": meta.get("pano_id"),
                                    "camera_alignment_diagnostics": {
                                        "look_vector": look_vector,
                                        "facade_normal": [float(normal[0]), float(normal[1])],
                                        "dot_product": dot_prod,
                                        "is_correct_side": is_correct_side
                                    },
                                    "facade_segment_vertices_local": [A, B]
                                }
                                self.facades_cache_changed = True
                                self.metadata_cache[facade_id] = {}
                                self.metadata_cache[facade_id].update(self.facades_cache[facade_id])
                                self.metadata_cache[facade_id].update(self.panoramas_cache[pano_id])
            
            with self.cache_lock:
                has_facade_entry = facade_id in self.facades_cache
            block_segments_info.append({
                "f_idx": f_idx,
                "facade_id": facade_id,
                "A": A,
                "B": B,
                "mx": mx,
                "my": my,
                "normal": normal,
                "norm_len": norm_len,
                "road_dist": road_dist,
                "best_edge_id": best_edge_id,
                "is_street_facing": is_street_facing,
                "pano_id": pano_id if has_facade_entry else None,
                "heading": heading if has_facade_entry else None
            })
            
        block_solved_heights = []
        for seg in block_segments_info:
            if seg["pano_id"] is not None and seg["heading"] is not None:
                h_val = self.estimate_facade_segment_height(seg["pano_id"], seg["heading"], seg)
                if h_val != 4.0:
                    block_solved_heights.append(h_val)
                    
        if block_solved_heights:
            height_meters = float(np.median(block_solved_heights)) * 2.0
        else:
            with self.cache_lock:
                in_blocks_cache = self.blocks_cache and b_id in self.blocks_cache
                if in_blocks_cache:
                    h_cached = self.blocks_cache[b_id].get("height_meters", 4.0)
                    if h_cached < 6.5:
                        height_meters = h_cached * 2.0
                    else:
                        height_meters = h_cached
                else:
                    height_meters = 8.0
                    
        if self.harvest_only:
            return {
                "block_id": b_id,
                "newly_resolved": True,
                "harvest_only": True
            }
            
        for f_idx in range(num_verts):
            uv_mappings[f"{b_id}_facade_{f_idx}"] = [
                [0.0, 0.0],
                [1.0, 0.0],
                [1.0, 1.0],
                [0.0, 1.0]
            ]
        uv_mappings[f"{b_id}_roof"] = [[0.0, 0.0]] * num_verts
        
        self.resolve_almost_adjacent_fallback_segments(block_segments_info, fallback_path)
        
        def angular_difference(h1, h2):
            if h1 is None or h2 is None:
                return 180.0
            diff = abs(h1 - h2)
            return min(diff, 360.0 - diff)
            
        start_idx = 0
        for i in range(num_verts):
            prev_idx = (i - 1) % num_verts
            p_i = block_segments_info[i]["pano_id"]
            p_prev = block_segments_info[prev_idx]["pano_id"]
            h_i = block_segments_info[i]["heading"]
            h_prev = block_segments_info[prev_idx]["heading"]
            if p_i != p_prev or angular_difference(h_i, h_prev) > 20.0:
                start_idx = i
                break
                
        groups = []
        curr_group = []
        for step in range(num_verts):
            curr_idx = (start_idx + step) % num_verts
            segment_info = block_segments_info[curr_idx]
            if not curr_group:
                curr_group.append(segment_info)
            else:
                g_pano = curr_group[0]["pano_id"]
                g_heading = curr_group[0]["heading"]
                s_pano = segment_info["pano_id"]
                s_heading = segment_info["heading"]
                if s_pano == g_pano and s_pano is not None and angular_difference(s_heading, g_heading) <= 20.0:
                    curr_group.append(segment_info)
                else:
                    groups.append(curr_group)
                    curr_group = [segment_info]
        if curr_group:
            groups.append(curr_group)
            
        for group_idx, group in enumerate(groups):
            p_id = group[0]["pano_id"]
            headings = [seg["heading"] for seg in group if seg["heading"] is not None]
            if headings:
                x_sum = sum(math.cos(math.radians(h)) for h in headings)
                y_sum = sum(math.sin(math.radians(h)) for h in headings)
                heading_val = round(math.degrees(math.atan2(y_sum, x_sum)) % 360.0, 2)
            else:
                heading_val = 0.0
                
            if p_id is None:
                for seg in group:
                    f_id = seg["facade_id"]
                    facade_textures_map[f_id] = os.path.abspath(fallback_path) if fallback_path else None
                    status = "fallback"
                    local_diag_facades.append({
                        "facade_id": f_id,
                        "A": seg["A"], "B": seg["B"], "mx": seg["mx"], "my": seg["my"], "normal": seg["normal"],
                        "status": status
                    })
                    local_diagnostics[f_id] = {
                        "facade_id": f_id,
                        "midpoint": [float(seg["mx"]), float(seg["my"])],
                        "normal": [float(seg["normal"][0]), float(seg["normal"][1])],
                        "is_street_facing": seg["is_street_facing"],
                        "road_distance_meters": float(seg["road_dist"]),
                        "status": status
                    }
                continue
                
            A_combined = group[0]["A"]
            B_combined = group[-1]["B"]
            K = len(group)
            
            pano_filename = f"{p_id}_yaw_{heading_val:.2f}.png"
            pano_screenshot_path = os.path.abspath(os.path.join(self.data_dir, "screenshots", "pano", pano_filename))
            virtual_tex_filename = f"{b_id}_virtual_{self.cardinal_from_normal(group[0]['normal'])}_{group_idx}.png"
            virtual_tex_path = os.path.abspath(os.path.join(self.textures_dir, virtual_tex_filename))
            
            status = "fallback"
            warped_img = None
            
            if os.path.exists(virtual_tex_path):
                status = "textured"
                warped_img = True
                print(f"[Incremental] Found existing virtual facade texture: {virtual_tex_filename}. Skipping sky masking, warping, and blurring.")
                sys.stdout.flush()
            else:
                # Scrape if not on disk
                if not os.path.exists(pano_screenshot_path) and self.scraper is not None:
                    with self.scraper_lock:
                        p_data = self.panoramas_cache[p_id]
                        screenshot_bytes = self.scraper.capture_facade_screenshot(
                            lat=p_data["latitude"],
                            lon=p_data["longitude"],
                            heading=heading_val,
                            pano_id=p_id,
                            slice_id=f"temp_capture_{p_id}"
                        )
                    if screenshot_bytes:
                        ensure_dir(os.path.dirname(pano_screenshot_path))
                        with open(pano_screenshot_path, "wb") as f_img:
                            f_img.write(screenshot_bytes)
                            
                if os.path.exists(pano_screenshot_path):
                    try:
                        with self.cache_lock:
                            p_data = self.panoramas_cache[p_id]
                        cx_pano, cy_pano = gps_to_local(p_data["latitude"], p_data["longitude"])
                        
                        masked_img = self.mask_sky_in_panorama(
                            image_path=pano_screenshot_path,
                            cx=cx_pano,
                            cy=cy_pano,
                            heading=heading_val,
                            height_meters=height_meters / 2.0,
                            group_segments=group
                        )
                        
                        obs = {
                            "image_path": masked_img,
                            "projection": {
                                "camera_x": cx_pano,
                                "camera_y": cy_pano,
                                "camera_z": 2.5,
                                "yaw_degrees": heading_val,
                                "fov_degrees": 75.0,
                                "image_width": 1280,
                                "image_height": 720
                            }
                        }
                        
                        midpoint = [
                            (A_combined[0] + B_combined[0]) / 2.0,
                            (A_combined[1] + B_combined[1]) / 2.0
                        ]
                        vec = [
                            B_combined[0] - A_combined[0],
                            B_combined[1] - A_combined[1]
                        ]
                        A_virtual = [midpoint[0] - vec[0], midpoint[1] - vec[1]]
                        B_virtual = [midpoint[0] + vec[0], midpoint[1] + vec[1]]
                        
                        warped_img = self.extract_rectified_facade_observation_texture(
                            obs,
                            A=A_virtual,
                            B=B_virtual,
                            height_meters=height_meters / 2.0,
                            width=K * 512 * 2,
                            height=512
                        )
                        
                        np_warped = np.array(warped_img)
                        h_img, w_img, c_img = np_warped.shape
                        quarter = w_img // 4
                        if quarter > 0:
                            left_roi = np_warped[:, :quarter]
                            blurred_left = cv2.GaussianBlur(left_roi, (25, 25), 0)
                            np_warped[:, :quarter] = blurred_left
                            
                            right_roi = np_warped[:, -quarter:]
                            blurred_right = cv2.GaussianBlur(right_roi, (25, 25), 0)
                            np_warped[:, -quarter:] = blurred_right
                            
                            warped_img = Image.fromarray(np_warped, "RGBA")
                            
                        status = "textured"
                        warped_img.save(virtual_tex_path)
                        print(f"[Virtual Facade] Successfully warped, blurred, and saved {K}-segment virtual facade to: {virtual_tex_filename} with height {height_meters:.2f}m (storefront {height_meters/2.0:.2f}m)")
                        sys.stdout.flush()
                    except Exception as warp_err:
                        print(f"[Warning] Failed unified warping for group: {warp_err}")
                        
            p_data = None
            L_lengths = [seg["norm_len"] for seg in group]
            L_total = sum(L_lengths) if sum(L_lengths) > 1e-5 else 1.0
            cum_L = 0.0
            for i, seg in enumerate(group):
                f_id = seg["facade_id"]
                if status == "textured" and warped_img is not None:
                    u_seg_start = 0.375 + 0.25 * (cum_L / L_total)
                    cum_L += L_lengths[i]
                    u_seg_end = 0.375 + 0.25 * (cum_L / L_total)
                    
                    uv_mappings[f_id] = [
                        [u_seg_start, 0.0],
                        [u_seg_end, 0.0],
                        [u_seg_end, 1.0],
                        [u_seg_start, 1.0]
                    ]
                    facade_textures_map[f_id] = virtual_tex_path
                    
                    with self.cache_lock:
                        p_data = self.panoramas_cache[p_id]
                    prov = {
                        "source_pano_id": p_id,
                        "source_date": p_data.get("date", ""),
                        "source_lat_lon": [p_data["latitude"], p_data["longitude"]],
                        "facade_normal": [float(seg["normal"][0]), float(seg["normal"][1])],
                        "projection_parameters": {
                            "cam_z": 2.5,
                            "height_meters": float(height_meters),
                            "facade_length": float(seg["norm_len"])
                        }
                    }
                    local_provenance[f_id] = prov
                else:
                    facade_textures_map[f_id] = os.path.abspath(fallback_path) if fallback_path else None
                    
                local_diag_facades.append({
                    "facade_id": f_id,
                    "A": seg["A"], "B": seg["B"], "mx": seg["mx"], "my": seg["my"], "normal": seg["normal"],
                    "status": status,
                    "best_obs": {
                        "metadata": {
                            "latitude": p_data["latitude"],
                            "longitude": p_data["longitude"]
                        }
                    } if (status == "textured" and p_data is not None) else None
                })
                local_diagnostics[f_id] = {
                    "facade_id": f_id,
                    "midpoint": [float(seg["mx"]), float(seg["my"])],
                    "normal": [float(seg["normal"][0]), float(seg["normal"][1])],
                    "is_street_facing": seg["is_street_facing"],
                    "road_distance_meters": float(seg["road_dist"]),
                    "status": status
                }
                
        # Calculate roof color
        roof_color_val = self.calculate_predominant_roof_color(facade_textures_map)
        
        # Persist block & facade properties
        with self.cache_lock:
            if b_id not in self.blocks_cache:
                self.blocks_cache[b_id] = {}
                self.blocks_cache_changed = True
            
            block_updates = {
                "polygon": raw_poly,
                "height_meters": height_meters,
                "roof_color": roof_color_val
            }
            for k, v in block_updates.items():
                if self.blocks_cache[b_id].get(k) != v:
                    self.blocks_cache[b_id][k] = v
                    self.blocks_cache_changed = True
                    
            for f_idx in range(num_verts):
                f_id = f"{b_id}_facade_{f_idx}"
                if f_id in self.facades_cache:
                    if self.facades_cache[f_id].get("roof_color") != roof_color_val:
                        self.facades_cache[f_id]["roof_color"] = roof_color_val
                        self.facades_cache_changed = True
                if f_id in self.metadata_cache:
                    self.metadata_cache[f_id]["roof_color"] = roof_color_val
                    
        block_data = {
            "block_id": b_id,
            "polygon": shrunk_poly,
            "height_meters": height_meters,
            "centroid": [centroid_x, centroid_y],
            "texture_atlas_path": os.path.abspath(fallback_path) if fallback_path else None,
            "texture_atlas_filename": "transparent_facade.png" if fallback_path else None,
            "facade_textures": facade_textures_map,
            "uv_mappings": uv_mappings,
            "roof_color": roof_color_val,
            "traceability": [
                {
                    "facade_idx": f_idx,
                    "source": "image" if k in local_provenance else "fallback"
                }
                for f_idx, k in enumerate([f"{b_id}_facade_{i}" for i in range(num_verts)])
            ]
        }
        
        return {
            "block_data": block_data,
            "provenance": local_provenance,
            "diagnostics": local_diagnostics,
            "diag_facades": local_diag_facades,
            "newly_resolved": True
        }

    def reconstruct_blocks_and_texture(self) -> tuple[list[dict], dict]:
        """
        Densely reconstructs and textures building block volumes.
        Groups contiguous segments sharing the same panorama and heading,
        projecting and warping only once to eliminate visual seams.
        """
        # Fallback textures are removed completely; Blender will render untextured solid cream color.
        fallback_path = None
        
        # Build O(1) road name dictionary to avoid nested loops over edges
        self.road_name_by_id = {}
        for u, v, data in self.G.edges(data=True):
            eid = data.get("id")
            if eid:
                self.road_name_by_id[eid] = data.get("name", "")

        # Pre-initialize spatial grid index sequentially in main thread to ensure thread safety
        self.get_road_distance(0.0, 0.0)

        raw_blocks = self.extract_block_polygons()
        
        # Sort blocks by proximity to Parque Hidalgo (0, 0)
        def block_distance(bl):
            poly = bl["polygon"]
            cx = sum(pt[0] for pt in poly[:-1]) / (len(poly) - 1)
            cy = sum(pt[1] for pt in poly[:-1]) / (len(poly) - 1)
            return math.sqrt(cx**2 + cy**2)
            
        raw_blocks.sort(key=block_distance)
        print(f"[Reconstruction] Prioritized {len(raw_blocks)} blocks by geographic proximity to city center (Parque Hidalgo).")
        
        # --- PRE-PASS: SEQUENTIAL METADATA RESOLUTION & SCREENSHOT SCRAPING ---
        if not self.skip_scraper and self.scraper is not None:
            print("[Reconstruction] Starting sequential pre-pass on the main thread to resolve metadata and cache screenshots...")
            sys.stdout.flush()
            
            for idx, rb in enumerate(raw_blocks):
                b_id = rb["block_id"]
                if rb.get("is_external", False):
                    continue
                if not self.reprocess and b_id in self.existing_export_blocks:
                    if self.is_block_complete(b_id):
                        continue
                    
                raw_poly = rb["polygon"]
                shrunk_poly = self.shrink_polygon(raw_poly, d=6.0)
                num_verts = len(shrunk_poly) - 1
                centroid_x = sum(pt[0] for pt in shrunk_poly[:-1]) / num_verts
                centroid_y = sum(pt[1] for pt in shrunk_poly[:-1]) / num_verts
                dist_to_center = math.sqrt(centroid_x**2 + centroid_y**2)
                
                block_segments_info = []
                
                # 1. Resolve metadata for all segments sequentially
                for f_idx in range(num_verts):
                    facade_id = f"{b_id}_facade_{f_idx}"
                    A = shrunk_poly[f_idx]
                    B = shrunk_poly[f_idx + 1]
                    mx = (A[0] + B[0]) / 2.0
                    my = (A[1] + B[1]) / 2.0
                    dx = B[0] - A[0]
                    dy = B[1] - A[1]
                    normal = np.array([dy, -dx])
                    norm_len = np.linalg.norm(normal)
                    if norm_len > 1e-5:
                        normal = normal / norm_len
                    else:
                        normal = np.array([0.0, 1.0])
                        
                    is_cached = facade_id in self.facades_cache
                    road_dist, best_edge_id = self.get_road_distance(mx, my)
                    is_street_facing = (road_dist <= 20.0)
                    
                    if not is_cached and (is_street_facing and (self.radius is None or self.radius < 0 or dist_to_center <= self.radius)):
                        # Scrape metadata sequentially on main thread
                        search_x = mx + 8.0 * normal[0]
                        search_y = my + 8.0 * normal[1]
                        lat, lon = local_to_gps(search_x, search_y)
                        heading = math.degrees(math.atan2(-normal[0], -normal[1])) % 360.0
                        heading = round(heading, 2)
                        
                        print(f"[Pre-pass API Query] Fetching metadata for {facade_id}...")
                        meta = self.scraper.fetch_public_metadata(lat=lat, lon=lon)
                        if meta:
                            pano_id = meta["pano_id"]
                            cam_lat = meta["latitude"]
                            cam_lon = meta["longitude"]
                            
                            # Chronology selection
                            timeline = meta.get("timeline", [])
                            oldest_pano_id = pano_id
                            oldest_date = meta.get("date", "9999-12")
                            for tl in timeline:
                                tl_id = tl["pano_id"]
                                tl_date = tl["date"]
                                if tl_date and tl_date < oldest_date:
                                    oldest_pano_id = tl_id
                                    oldest_date = tl_date
                                    
                            if oldest_pano_id != pano_id:
                                print(f"[Temporal Chronology] Found older timeline state: {oldest_pano_id} ({oldest_date}) replaces modern {pano_id}.")
                                oldest_meta = self.scraper.fetch_public_metadata(pano_id=oldest_pano_id)
                                if oldest_meta:
                                    meta = oldest_meta
                                    pano_id = oldest_pano_id
                                    cam_lat = meta["latitude"]
                                    cam_lon = meta["longitude"]
                                    
                            cx, cy = gps_to_local(cam_lat, cam_lon)
                            yaw_rad = math.radians(heading)
                            rot_matrix = [
                                [math.cos(yaw_rad), -math.sin(yaw_rad), 0.0],
                                [math.sin(yaw_rad), math.cos(yaw_rad), 0.0],
                                [0.0, 0.0, 1.0]
                            ]
                            
                            self.panoramas_cache[pano_id] = {
                                "latitude": cam_lat,
                                "longitude": cam_lon,
                                "altitude": meta.get("altitude"),
                                "date": meta.get("date", ""),
                                "pitch": meta.get("pitch"),
                                "roll": meta.get("roll"),
                                "projection_yaw": meta.get("projection_yaw"),
                                "pano_yaw": meta.get("projection_yaw"),
                                "road_name": meta.get("road_name", ""),
                                "adjacent_links": meta.get("adjacent_links", []),
                                "timeline": meta.get("timeline", []),
                            }
                            self.panoramas_cache_changed = True
                            
                            road_name_val = self.road_name_by_id.get(best_edge_id, "")
                            look_vector = [float(mx - cx), float(my - cy)]
                            dot_prod = float(look_vector[0] * normal[0] + look_vector[1] * normal[1])
                            is_correct_side = bool(dot_prod < 0)
                            
                            search_query_url = f"https://maps.googleapis.com/maps/api/js/GeoPhotoService.SingleImageSearch?pb=!1m5!1sapiv3!5sUS!11m2!1m1!1b0!2m4!1m2!3d{lat:.6f}!4d{lon:.6f}!2d50.0!3m10!2m2!1ses!2sMX!9m1!1e2!11m4!1m3!1e2!2b1!3e2!4m9!1e1!1e2!1e3!1e4!1e6!1e8!1e12!5m0!6m0&callback=_xdc_._v2mub5"
                            captured_url = f"https://www.google.com/maps?layer=c&cbll={cam_lat},{cam_lon}&panoid={pano_id}&cbp=11,{heading:.2f},,0,0"
                            
                            self.facades_cache[facade_id] = {
                                "pano_id": pano_id,
                                "block_id": b_id,
                                "facade_index": int(f_idx),
                                "heading": heading,
                                "captured_heading": heading,
                                "resolution": {
                                    "screenshot_width": 1280,
                                    "screenshot_height": 720,
                                    "slice_width": 512,
                                    "slice_height": 256
                                },
                                "camera_position_local": [float(cx), float(cy), None],
                                "camera_rotation_matrix": rot_matrix,
                                "road_relation": {
                                    "road_name": road_name_val,
                                    "road_distance_meters": float(road_dist),
                                    "road_edge_id": best_edge_id
                                },
                                "facade_midpoint_local": [float(mx), float(my)],
                                "offset_search_point_local": [float(search_x), float(search_y)],
                                "offset_search_point_gps": [float(lat), float(lon)],
                                "search_query_url": search_query_url,
                                "captured_url": captured_url,
                                "modern_pano_id": meta.get("pano_id"),
                                "camera_alignment_diagnostics": {
                                    "look_vector": look_vector,
                                    "facade_normal": [float(normal[0]), float(normal[1])],
                                    "dot_product": dot_prod,
                                    "is_correct_side": is_correct_side
                                },
                                "facade_segment_vertices_local": [A, B]
                            }
                            self.facades_cache_changed = True
                            self.metadata_cache[facade_id] = {}
                            self.metadata_cache[facade_id].update(self.facades_cache[facade_id])
                            self.metadata_cache[facade_id].update(self.panoramas_cache[pano_id])
                            
                    if facade_id in self.facades_cache:
                        entry = self.facades_cache[facade_id]
                        block_segments_info.append({
                            "pano_id": entry["pano_id"],
                            "heading": entry.get("captured_heading", entry.get("heading")),
                            "normal": normal
                        })
                        
                # 2. Resolve groups and download screenshots sequentially on main thread
                if block_segments_info:
                    num_verts_info = len(block_segments_info)
                    
                    def angular_difference(h1, h2):
                        if h1 is None or h2 is None:
                            return 180.0
                        diff = abs(h1 - h2)
                        return min(diff, 360.0 - diff)
                        
                    start_idx = 0
                    for i in range(num_verts_info):
                        prev_idx = (i - 1) % num_verts_info
                        p_i = block_segments_info[i]["pano_id"]
                        p_prev = block_segments_info[prev_idx]["pano_id"]
                        h_i = block_segments_info[i]["heading"]
                        h_prev = block_segments_info[prev_idx]["heading"]
                        if p_i != p_prev or angular_difference(h_i, h_prev) > 20.0:
                            start_idx = i
                            break
                            
                    groups = []
                    curr_group = []
                    for step in range(num_verts_info):
                        curr_idx = (start_idx + step) % num_verts_info
                        segment_info = block_segments_info[curr_idx]
                        if not curr_group:
                            curr_group.append(segment_info)
                        else:
                            g_pano = curr_group[0]["pano_id"]
                            g_heading = curr_group[0]["heading"]
                            s_pano = segment_info["pano_id"]
                            s_heading = segment_info["heading"]
                            if s_pano == g_pano and s_pano is not None and angular_difference(s_heading, g_heading) <= 20.0:
                                curr_group.append(segment_info)
                            else:
                                groups.append(curr_group)
                                curr_group = [segment_info]
                    if curr_group:
                        groups.append(curr_group)
                        
                    for group in groups:
                        p_id = group[0]["pano_id"]
                        if p_id is not None:
                            headings = [seg["heading"] for seg in group if seg["heading"] is not None]
                            if headings:
                                x_sum = sum(math.cos(math.radians(h)) for h in headings)
                                y_sum = sum(math.sin(math.radians(h)) for h in headings)
                                heading_val = round(math.degrees(math.atan2(y_sum, x_sum)) % 360.0, 2)
                            else:
                                heading_val = 0.0
                                
                            pano_filename = f"{p_id}_yaw_{heading_val:.2f}.png"
                            pano_screenshot_path = os.path.abspath(os.path.join(self.data_dir, "screenshots", "pano", pano_filename))
                            
                            if not os.path.exists(pano_screenshot_path):
                                print(f"[Pre-pass Scraper] Capturing panorama screenshot: {pano_filename}...")
                                p_data = self.panoramas_cache[p_id]
                                screenshot_bytes = self.scraper.capture_facade_screenshot(
                                    lat=p_data["latitude"],
                                    lon=p_data["longitude"],
                                    heading=heading_val,
                                    pano_id=p_id,
                                    slice_id=f"temp_capture_{p_id}"
                                )
                                if screenshot_bytes:
                                    ensure_dir(os.path.dirname(pano_screenshot_path))
                                    with open(pano_screenshot_path, "wb") as f_img:
                                        f_img.write(screenshot_bytes)
                                        
            # Save final caches after scraping pre-pass completes
            self.save_metadata_cache()
            print("[Reconstruction] Pre-pass completed successfully! All required metadata and screenshots are cached on disk.")
            sys.stdout.flush()

        # Close persistent scraper session on main thread before running workers
        if self.scraper:
            self.scraper.close()
            self.scraper = None  # Ensure threads never attempt to query browser/network
        
        self.current_blocks_data = []
        self.current_provenance = {}
        self.current_diagnostics = {}
        self.current_diag_facades = []
        
        blocks_data = self.current_blocks_data
        provenance = self.current_provenance
        diagnostics = self.current_diagnostics
        diag_facades = self.current_diag_facades
        newly_resolved_count = 0

        # Concurrent thread execution when self.parallel > 1
        if self.parallel > 1:
            import concurrent.futures
            print(f"[Reconstruction] Parallel execution enabled with {self.parallel} worker threads.")
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.parallel) as executor:
                futures = {executor.submit(self.reconstruct_single_block, rb, fallback_path): rb for rb in raw_blocks}
                for idx, future in enumerate(concurrent.futures.as_completed(futures)):
                    rb = futures[future]
                    try:
                        res = future.result()
                        if res:
                            if res.get("harvest_only"):
                                continue
                            blocks_data.append(res["block_data"])
                            provenance.update(res["provenance"])
                            diagnostics.update(res["diagnostics"])
                            diag_facades.extend(res["diag_facades"])
                            if res["newly_resolved"]:
                                newly_resolved_count += 1
                                
                            # Autoguardado checkpoints every 25 newly resolved blocks
                            if newly_resolved_count > 0 and newly_resolved_count % 25 == 0:
                                self.save_checkpoint_helper(blocks_data, provenance, diagnostics, len(provenance))
                    except Exception as e:
                        print(f"[Error] Thread execution failed for block {rb['block_id']}: {e}")
                        import traceback
                        traceback.print_exc()
        else:
            print("[Reconstruction] Running in sequential mode.")
            for idx, rb in enumerate(raw_blocks):
                res = self.reconstruct_single_block(rb, fallback_path)
                if res:
                    if res.get("harvest_only"):
                        continue
                    blocks_data.append(res["block_data"])
                    provenance.update(res["provenance"])
                    diagnostics.update(res["diagnostics"])
                    diag_facades.extend(res["diag_facades"])
                    if res["newly_resolved"]:
                        newly_resolved_count += 1
                        
                    # Autoguardado checkpoints every 25 newly resolved blocks
                    if newly_resolved_count > 0 and newly_resolved_count % 25 == 0:
                        self.save_checkpoint_helper(blocks_data, provenance, diagnostics, len(provenance))

        # Check for harvest_only early exit
        if self.harvest_only:
            print("[Harvest Mode] Scraping and metadata caching complete. Skipping all 3D reconstruction and Blender rendering.")
            if self.scraper:
                self.scraper.close()
            self.save_stitching_cache()
            self.save_metadata_cache()
            return [], {}

        total_facades = sum(len(bl["polygon"]) - 1 for bl in blocks_data)
        textured_facades = len(provenance)

        metadata_filepath = os.path.join(self.export_dir, "metadata.json")
        meta_out = {
            "total_blocks": len(blocks_data),
            "total_facades": total_facades,
            "textured_facades": textured_facades,
            "coverage_percentage": (textured_facades / total_facades * 100.0) if total_facades > 0 else 0.0,
            "provenance": provenance
        }
        save_json(meta_out, metadata_filepath)
        
        diagnostics_filepath = os.path.join(self.debug_dir, "reconstruction_diagnostics.json")
        save_json(diagnostics, diagnostics_filepath)
        print(f"[Reconstruction] Deep diagnostics log successfully written to: {diagnostics_filepath}")
        
        # Build clean structural network topology output for Blender
        flat_nodes = []
        for n, data in self.G.nodes(data=True):
            flat_nodes.append({"id": n, "x": data["x"], "y": data["y"]})
            
        flat_edges = []
        for u, v, data in self.G.edges(data=True):
            flat_edges.append({"u": u, "v": v})
            
        scene_doc = {
            "road_graph": {
                "nodes": flat_nodes,
                "edges": flat_edges
            },
            "blocks": blocks_data
        }
        
        # Save stitching cache back to disk (Incremental processing)
        self.save_stitching_cache()
        
        # Save metadata cache back to disk (Incremental processing)
        self.save_metadata_cache()
        print(f"[Reconstruction] Metadata caches successfully updated in relational format.")
        
        # Compile global observation map
        self.generate_diagnostic_visualization(scene_doc, diag_facades, meta_out["coverage_percentage"])
        
        return blocks_data, scene_doc

    def calculate_predominant_roof_color(self, facade_textures: dict) -> list[float]:
        """
        Computes the predominant (average) color of all custom storefront textures in the block.
        Falls back to the stucco cream color if no custom textures exist.
        Returns a list of 3 normalized floats [R, G, B] in [0.0, 1.0].
        """
        fallback_abs = os.path.abspath(os.path.join(self.textures_dir, "transparent_facade.png"))
        unique_paths = set(p for p in facade_textures.values() if p and p != fallback_abs and os.path.exists(p))
        
        if not unique_paths:
            # Fallback to warm cream stucco base color
            return [238 / 255.0, 232 / 255.0, 220 / 255.0]
            
        r_sum, g_sum, b_sum = 0.0, 0.0, 0.0
        count = 0
        
        for path in unique_paths:
            try:
                with Image.open(path) as img:
                    # Resize to 1x1 to average the pixels quickly
                    tiny = img.resize((1, 1), Image.Resampling.BILINEAR)
                    r, g, b = tiny.getpixel((0, 0))[:3]
                    r_sum += r
                    g_sum += g
                    b_sum += b
                    count += 1
            except Exception as e:
                print(f"[Warning] Failed to calculate predominant color for {path}: {e}")
                
        if count > 0:
            return [r_sum / count / 255.0, g_sum / count / 255.0, b_sum / count / 255.0]
            
        return [238 / 255.0, 232 / 255.0, 220 / 255.0]

    def generate_diagnostic_visualization(self, scene_doc: dict, diag_facades: list[dict], coverage_pct: float):
        """
        Compiles a premium light visual diagnostic map (global_observation_map.png) to export/debug/
        mapping the entire road network, block polygons filled with their dynamic roof colors,
        and green highlighted textured facade edges.
        """
        width, height = 1920, 1080
        margin = 80
        
        xmin, ymin = float("inf"), float("inf")
        xmax, ymax = float("-inf"), float("-inf")
        
        for nd in scene_doc["road_graph"]["nodes"]:
            x, y = nd["x"], nd["y"]
            xmin, ymin = min(xmin, x), min(ymin, y)
            xmax, ymax = max(xmax, x), max(ymax, y)
            
        dx = max(100.0, xmax - xmin)
        dy = max(100.0, ymax - ymin)
        
        xmin -= 50.0
        ymin -= 50.0
        dx += 100.0
        dy += 100.0
        
        # Available drawing area
        avail_w = width - 2 * margin
        avail_h = height - 2 * margin
        
        # Scale factors (pixels per meter)
        scale_x = avail_w / dx
        scale_y = avail_h / dy
        scale = min(scale_x, scale_y) # Maintain a perfect 1:1 aspect ratio (perpendicular view)
        
        # Center the bounding box within the available canvas space
        offset_x = margin + (avail_w - dx * scale) / 2
        offset_y = margin + (avail_h - dy * scale) / 2
        
        def to_pix(x, y):
            px = int(offset_x + (x - xmin) * scale)
            py = int(height - offset_y - (y - ymin) * scale)
            return px, py
            
        # Clean light mode background
        canvas = Image.new("RGB", (width, height), (245, 246, 248))
        draw = ImageDraw.Draw(canvas, "RGBA")
        
        # Try to load a clean modern TrueType font for high-fidelity text rendering
        font_large = None
        font_medium = None
        font_small = None
        
        font_paths = []
        if sys.platform == "win32":
            win_dir = os.environ.get("WINDIR", "C:\\Windows")
            font_paths = [
                os.path.join(win_dir, "Fonts", "arialbd.ttf"),
                os.path.join(win_dir, "Fonts", "arial.ttf"),
            ]
        elif sys.platform == "darwin":
            font_paths = [
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/System/Library/Fonts/Supplemental/Helvetica.ttf",
            ]
        else:
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
            ]
            
        from PIL import ImageFont
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    font_large = ImageFont.truetype(fp, 18)
                    font_medium = ImageFont.truetype(fp, 13)
                    font_small = ImageFont.truetype(fp, 11)
                    break
                except Exception:
                    pass
                    
        # 1. Draw entire road network skeleton (bounding box streets)
        node_map = {n["id"]: (n["x"], n["y"]) for n in scene_doc["road_graph"]["nodes"]}
        for ed in scene_doc["road_graph"]["edges"]:
            p1 = node_map.get(ed["u"])
            p2 = node_map.get(ed["v"])
            if p1 and p2:
                # Slightly darker and thicker for high visibility
                draw.line([to_pix(*p1), to_pix(*p2)], fill=(185, 190, 195, 255), width=2)
                
        # Create block ID mapping to quickly look up roof colors
        block_colors = {}
        for bl in scene_doc["blocks"]:
            roof_color = bl.get("roof_color", [238/255.0, 232/255.0, 220/255.0])
            rgb = tuple(int(c * 255) for c in roof_color)
            block_colors[bl["block_id"]] = rgb
            
        # 2. Draw block polygons colored by their roof color
        for bl in scene_doc["blocks"]:
            poly = bl["polygon"]
            pixel_poly = [to_pix(pt[0], pt[1]) for pt in poly]
            rgb = block_colors.get(bl["block_id"], (238, 232, 220))
            draw.polygon(pixel_poly, fill=(rgb[0], rgb[1], rgb[2], 180), outline=(150, 155, 165, 255))
            
        # 3. Draw facades (highlight textured ones in green)
        for f in diag_facades:
            p_a = to_pix(*f["A"])
            p_b = to_pix(*f["B"])
            
            if f["status"] == "textured":
                col = (46, 204, 113, 255)  # Premium emerald green
                width_line = 4
            else:
                col = (180, 185, 190, 150)  # Thicker, slightly darker gray for better visibility
                width_line = 2
                
            draw.line([p_a, p_b], fill=col, width=width_line)
            
        # Draw HUD dashboard in top-left
        draw.rectangle([50, 50, 480, 230], fill=(255, 255, 255, 245), outline=(200, 204, 208, 255), width=2)
        
        draw.text((70, 65), "TECATE RECONSTRUCTION COVERAGE", fill=(44, 62, 80, 255), font=font_large)
        draw.text((70, 92), "Historical Urban Simulation Project", fill=(52, 152, 219, 255), font=font_medium)
        draw.text((70, 110), "-" * 52, fill=(200, 204, 208, 100), font=font_small)
        
        draw.text((70, 128), f"Total Simulated Blocks: {len(scene_doc['blocks'])}", fill=(127, 140, 141, 255), font=font_medium)
        draw.text((70, 153), f"Historical Texturing: {coverage_pct:.1f}%", fill=(46, 204, 113, 255), font=font_large or font_medium)
        draw.text((70, 185), f"Center Radius: {'Unlimited' if self.radius is None or self.radius < 0 else f'{self.radius}m'}", fill=(127, 140, 141, 255), font=font_medium)
        
        # Draw Legend (Simbología) in bottom-left
        draw.rectangle([50, height - 260, 480, height - 50], fill=(255, 255, 255, 245), outline=(200, 204, 208, 255), width=2)
        
        draw.text((70, height - 245), "SIMBOLOGÍA", fill=(44, 62, 80, 255), font=font_large)
        draw.text((70, height - 225), "-" * 52, fill=(200, 204, 208, 100), font=font_small)
        
        legend = [
            ("Textured Facade Slice (NCC)", (46, 204, 113), "line"),
            ("Untextured Stucco Fallback", (180, 185, 190), "line"),
            ("Urban Block (Roof Color)", (180, 190, 200), "rect"),
            ("Road Network Segment", (185, 190, 195), "line")
        ]
        ly = height - 205
        for name, col_leg, geom in legend:
            if geom == "line":
                draw.line([70, ly + 8, 90, ly + 8], fill=col_leg, width=3)
            elif geom == "rect":
                draw.rectangle([70, ly + 2, 90, ly + 14], fill=(col_leg[0], col_leg[1], col_leg[2], 180), outline=(150, 155, 165))
                
            draw.text((105, ly), name, fill=(44, 62, 80, 255), font=font_medium)
            ly += 25
            
        debug_filepath = os.path.join(self.debug_dir, "global_observation_map.png")
        canvas.save(debug_filepath)
        print(f"[Reconstruction] Premium light diagnostic map saved to: {debug_filepath}")
