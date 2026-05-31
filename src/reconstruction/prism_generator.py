import os
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
    def __init__(self, G: nx.MultiGraph, accepted_panos: list[dict] = None, export_dir: str = "export", data_dir: str = "data", headless: bool = False, radius: float = None, reprocess: bool = False, skip_scraper: bool = False, harvest_only: bool = False):
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
        
        ensure_dir(self.textures_dir)
        ensure_dir(self.debug_dir)
        
        # Load stitching cache to enable fast incremental reconstruction
        self.stitching_cache_path = os.path.join(data_dir, "stitching_cache.json")
        self.stitching_cache = {}
        if os.path.exists(self.stitching_cache_path):
            try:
                self.stitching_cache = load_json(self.stitching_cache_path)
            except Exception as e:
                print(f"[Warning] Failed to load stitching cache: {e}")
                
        # Initialize relational cache file paths
        self.panoramas_cache_path = os.path.join(data_dir, "panoramas_cache.json")
        self.blocks_cache_path = os.path.join(data_dir, "blocks_cache.json")
        self.facades_cache_path = os.path.join(data_dir, "facades_cache.json")
        
        # Load panoramas
        self.panoramas_cache = {}
        if os.path.exists(self.panoramas_cache_path):
            try:
                self.panoramas_cache = load_json(self.panoramas_cache_path)
            except Exception as e:
                print(f"[Warning] Failed to load panoramas cache: {e}")
                
        # Load blocks
        self.blocks_cache = {}
        if os.path.exists(self.blocks_cache_path):
            try:
                self.blocks_cache = load_json(self.blocks_cache_path)
            except Exception as e:
                print(f"[Warning] Failed to load blocks cache: {e}")
                
        # Load facades
        self.facades_cache = {}
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
                b_id = f_data.get("block_id")
                p_data = self.panoramas_cache.get(p_id, {})
                b_data = self.blocks_cache.get(b_id, {})
                combined = {}
                combined.update(f_data)
                combined.update(p_data)
                combined.update(b_data)
                combined["pano_id"] = p_id
                combined["block_id"] = b_id
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
        def handle_sigint(signum, frame):
            if self.shutdown_in_progress:
                print("\n[Ctrl+C] Force exiting instantly!")
                import os
                os._exit(1)
                
            self.shutdown_in_progress = True
            self.graceful_shutdown()
            
        signal.signal(signal.SIGINT, handle_sigint)

        # Run unified migration of existing cache entries to enriched format
        self.migrate_metadata_cache()

    def save_stitching_cache(self):
        try:
            save_json(self.stitching_cache, self.stitching_cache_path)
            print(f"[Cache Auto-Save] Stitching cache written to: {self.stitching_cache_path}")
        except Exception as e:
            print(f"[Warning] Failed to save stitching cache: {e}")

    def save_panoramas_cache(self):
        try:
            save_json(self.panoramas_cache, self.panoramas_cache_path)
            print(f"[Cache Auto-Save] Panoramas cache written to: {self.panoramas_cache_path}")
        except Exception as e:
            print(f"[Warning] Failed to save panoramas cache: {e}")

    def save_blocks_cache(self):
        try:
            save_json(self.blocks_cache, self.blocks_cache_path)
            print(f"[Cache Auto-Save] Blocks cache written to: {self.blocks_cache_path}")
        except Exception as e:
            print(f"[Warning] Failed to save blocks cache: {e}")

    def save_facades_cache(self):
        try:
            save_json(self.facades_cache, self.facades_cache_path)
            print(f"[Cache Auto-Save] Facades cache written to: {self.facades_cache_path}")
        except Exception as e:
            print(f"[Warning] Failed to save facades cache: {e}")

    def _decompose_metadata_cache(self):
        """
        Decomposes the virtual in-memory self.metadata_cache into
        the three relational caches: self.panoramas_cache, self.blocks_cache, and self.facades_cache.
        """
        for f_id, entry in self.metadata_cache.items():
            if not entry:
                continue
            # 1. Panorama Cache
            p_id = entry.get("pano_id")
            if p_id:
                if p_id not in self.panoramas_cache:
                    self.panoramas_cache[p_id] = {}
                self.panoramas_cache[p_id].update({
                    "latitude": entry.get("latitude"),
                    "longitude": entry.get("longitude"),
                    "altitude": entry.get("altitude"),
                    "date": entry.get("date"),
                    "pitch": entry.get("pitch"),
                    "roll": entry.get("roll"),
                    "hfov": entry.get("hfov"),
                    "vfov": entry.get("vfov"),
                    "focal_length_px": entry.get("focal_length_px"),
                    "optical_center": entry.get("optical_center"),
                    "intrinsic_matrix": entry.get("intrinsic_matrix"),
                    "camera_height_m": entry.get("camera_height_m")
                })
                
            # 2. Block Cache
            b_id = entry.get("block_id")
            if b_id:
                if b_id not in self.blocks_cache:
                    self.blocks_cache[b_id] = {}
                    
                # Derive centroid if not explicitly stored
                raw_poly = entry.get("block_polygon_vertices_raw_local")
                shrunk_poly = entry.get("block_polygon_vertices_shrunk_local")
                centroid = entry.get("centroid")
                if not centroid:
                    if shrunk_poly and len(shrunk_poly) > 1:
                        num_verts = len(shrunk_poly) - 1
                        cx = sum(pt[0] for pt in shrunk_poly[:-1]) / num_verts
                        cy = sum(pt[1] for pt in shrunk_poly[:-1]) / num_verts
                        centroid = [cx, cy]
                    elif raw_poly and len(raw_poly) > 1:
                        num_verts = len(raw_poly) - 1
                        cx = sum(pt[0] for pt in raw_poly[:-1]) / num_verts
                        cy = sum(pt[1] for pt in raw_poly[:-1]) / num_verts
                        centroid = [cx, cy]
                        
                dist_to_center = entry.get("distance_to_center_m")
                if dist_to_center is None and centroid:
                    dist_to_center = math.sqrt(centroid[0]**2 + centroid[1]**2)
                    
                height_meters = entry.get("height_meters")
                if height_meters is None and dist_to_center is not None:
                    if dist_to_center < 50.0:
                        height_meters = 1.0
                    else:
                        h = hash(b_id) % 100
                        height_meters = 7.0 + (h % 3) * 2.0
                        
                roof_color = entry.get("roof_color")
                if roof_color is None:
                    roof_color = self.blocks_cache[b_id].get("roof_color")
                    
                self.blocks_cache[b_id].update({
                    "distance_to_center_m": dist_to_center,
                    "centroid": centroid,
                    "height_meters": height_meters,
                    "block_polygon_vertices_raw_local": raw_poly,
                    "block_polygon_vertices_shrunk_local": shrunk_poly,
                    "block_shrink_distance_m": entry.get("block_shrink_distance_m", 6.0),
                    "normal_offset_distance_m": entry.get("normal_offset_distance_m", 8.0),
                    "roof_color": roof_color
                })
                
            # 3. Facade Cache
            if f_id not in self.facades_cache:
                self.facades_cache[f_id] = {}
            self.facades_cache[f_id].update({
                "pano_id": p_id,
                "block_id": b_id,
                "facade_index": entry.get("facade_index"),
                "heading": entry.get("heading"),
                "resolution": entry.get("resolution", {
                    "screenshot_width": 1280,
                    "screenshot_height": 720,
                    "slice_width": 512,
                    "slice_height": 256
                }),
                "camera_position_local": entry.get("camera_position_local"),
                "camera_rotation_matrix": entry.get("camera_rotation_matrix"),
                "road_relation": entry.get("road_relation"),
                "facade_midpoint_local": entry.get("facade_midpoint_local"),
                "offset_search_point_local": entry.get("offset_search_point_local"),
                "offset_search_point_gps": entry.get("offset_search_point_gps"),
                "search_query_url": entry.get("search_query_url"),
                "captured_url": entry.get("captured_url"),
                "modern_pano_id": entry.get("modern_pano_id"),
                "camera_alignment_diagnostics": entry.get("camera_alignment_diagnostics"),
                "image_filename": entry.get("image_filename"),
                "facade_segment_vertices_local": entry.get("facade_segment_vertices_local")
            })

    def save_metadata_cache(self):
        self._decompose_metadata_cache()
        self.save_panoramas_cache()
        self.save_blocks_cache()
        self.save_facades_cache()

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

    def migrate_metadata_cache(self):
        """
        Migrates the existing metadata cache to the new unified high-fidelity structure
        containing all parameters from Point 1 and 2, without deleting or overwriting
        already collected raw parameters.
        """
        if not self.metadata_cache:
            return
            
        print("[Metadata Cache Migration] Starting migration of existing cache entries to unified format...")
        facades_geom = self.build_all_facade_segments()
        
        migrated_count = 0
        for facade_id, entry in list(self.metadata_cache.items()):
            # Check if it needs migration (if typical new key like "intrinsic_matrix" is missing)
            if "intrinsic_matrix" in entry:
                continue
                
            lat = entry.get("latitude")
            lon = entry.get("longitude")
            heading = entry.get("heading")
            pano_id = entry.get("pano_id")
            date_str = entry.get("date", "")
            
            if lat is None or lon is None or heading is None or not pano_id:
                continue
                
            # Derive parameters
            geom = facades_geom.get(facade_id)
            if geom:
                road_dist, best_edge_id = self.get_road_distance(geom["mx"], geom["my"])
            else:
                road_dist, best_edge_id = 0.0, None
                
            # Fetch road name from G or default
            road_name = ""
            if best_edge_id:
                for u, v, key, data in self.G.edges(keys=True, data=True):
                    if data.get("id") == best_edge_id:
                        road_name = data.get("name", "")
                        break
                        
            cx, cy = gps_to_local(lat, lon)
            
            # Rotation matrix from yaw (heading)
            yaw_rad = math.radians(heading)
            rot_matrix = [
                [math.cos(yaw_rad), -math.sin(yaw_rad), 0.0],
                [math.sin(yaw_rad), math.cos(yaw_rad), 0.0],
                [0.0, 0.0, 1.0]
            ]
            
            # Clean up any previously saved placeholder/invented parameters
            entry.pop("gps_accuracy_m", None)
            entry.pop("orientation_accuracy_deg", None)
            
            # Query the unauthenticated metadata API at this coordinate to fetch the real pitch, roll, and altitude
            altitude_val = None
            pitch_val = None
            roll_val = None
            if self.scraper:
                print(f"[Migration Query] Refetching real projection parameters for {facade_id} from API...")
                meta = self.scraper.fetch_public_metadata(lat=lat, lon=lon)
                if meta:
                    altitude_val = meta.get("altitude")
                    pitch_val = meta.get("pitch")
                    roll_val = meta.get("roll")
            else:
                print(f"[Migration Query] Bypassing network query for {facade_id} due to --skip-scraper flag.")
            
            # Geometry derivations
            mx, my = 0.0, 0.0
            centroid_coords = [0.0, 0.0]
            dist_to_center = 0.0
            normal_val = [0.0, 1.0]
            search_x, search_y = lat, lon
            search_lat, search_lon = lat, lon
            
            if geom:
                mx = geom["mx"]
                my = geom["my"]
                centroid_coords = geom["centroid"]
                dist_to_center = math.sqrt(centroid_coords[0]**2 + centroid_coords[1]**2)
                normal_val = [float(geom["normal"][0]), float(geom["normal"][1])]
                search_x = mx + 8.0 * geom["normal"][0]
                search_y = my + 8.0 * geom["normal"][1]
                search_lat, search_lon = local_to_gps(search_x, search_y)
                
            look_vector = [float(mx - cx), float(my - cy)]
            dot_prod = float(look_vector[0] * normal_val[0] + look_vector[1] * normal_val[1])
            is_correct_side = bool(dot_prod < 0)
            
            # Request and Capture URLs
            search_query_url = f"https://maps.googleapis.com/maps/api/js/GeoPhotoService.SingleImageSearch?pb=!1m5!1sapiv3!5sUS!11m2!1m1!1b0!2m4!1m2!3d{search_lat:.6f}!4d{search_lon:.6f}!2d50.0!3m10!2m2!1ses!2sMX!9m1!1e2!11m4!1m3!1e2!2b1!3e2!4m9!1e1!1e2!1e3!1e4!1e6!1e8!1e12!5m0!6m0&callback=_xdc_._v2mub5"
            captured_url = f"https://www.google.com/maps?layer=c&cbll={lat},{lon}&panoid={pano_id}&cbp=11,{heading:.2f},,0,0"

            # Update entry in-place with new high-fidelity parameters
            entry["altitude"] = altitude_val
            entry["pitch"] = pitch_val
            entry["roll"] = roll_val
            entry["hfov"] = None
            entry["vfov"] = None
            entry["focal_length_px"] = None
            entry["resolution"] = {
                "screenshot_width": 1280,
                "screenshot_height": 720,
                "slice_width": 512,
                "slice_height": 256
            }
            entry["optical_center"] = None
            entry["intrinsic_matrix"] = None
            entry["camera_height_m"] = None
            entry["camera_position_local"] = [float(cx), float(cy), None]
            entry["camera_rotation_matrix"] = rot_matrix
            entry["road_relation"] = {
                "road_name": road_name,
                "road_distance_meters": float(road_dist),
                "road_edge_id": best_edge_id
            }
            entry["distance_to_center_m"] = float(dist_to_center)
            entry["facade_midpoint_local"] = [float(mx), float(my)]
            entry["offset_search_point_local"] = [float(search_x), float(search_y)]
            entry["offset_search_point_gps"] = [float(search_lat), float(search_lon)]
            entry["search_query_url"] = search_query_url
            entry["captured_url"] = captured_url
            entry["modern_pano_id"] = None
            entry["camera_alignment_diagnostics"] = {
                "look_vector": look_vector,
                "facade_normal": normal_val,
                "dot_product": dot_prod,
                "is_correct_side": is_correct_side
            }
            entry["image_filename"] = f"{facade_id}.png"
            entry["block_id"] = geom["block_id"] if geom else None
            entry["facade_index"] = geom["facade_index"] if geom else None
            entry["facade_segment_vertices_local"] = [geom["A"], geom["B"]] if geom else None
            entry["facade_normal_vector"] = normal_val
            entry["block_polygon_vertices_raw_local"] = geom["raw_poly"] if geom else None
            entry["block_polygon_vertices_shrunk_local"] = geom["shrunk_poly"] if geom else None
            entry["normal_offset_distance_m"] = 8.0
            entry["block_shrink_distance_m"] = 6.0
            
            migrated_count += 1
            
        if migrated_count > 0:
            self.save_metadata_cache()
            print(f"[Metadata Cache Migration] Successfully migrated {migrated_count} cache entries to the enriched unified format.")
        elif self.metadata_cache and not os.path.exists(self.facades_cache_path):
            print("[Metadata Cache Migration] Relational cache files do not exist. Decomposing and saving legacy cache now...")
            self.save_metadata_cache()

    def extract_block_polygons(self) -> list[dict]:
        """
        Extracts closed cycles from the road graph G using planar CCW traversal.
        Trims dead-ends first to ensure a stable cycle set.
        """
        print("[Reconstruction] Trimming road network to extract urban block cycles...")
        temp_G = nx.Graph(self.G)
        
        # Iteratively trim dead-ends (degree < 2)
        changed = True
        while changed:
            changed = False
            nodes_to_remove = [n for n in temp_G.nodes() if temp_G.degree(n) < 2]
            if nodes_to_remove:
                temp_G.remove_nodes_from(nodes_to_remove)
                changed = True
                
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
        block_counter = 0
        
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
                        
                        blocks.append({
                            "block_id": f"block_{block_counter}",
                            "polygon": segmented_verts,
                            "area_sq_meters": abs(signed_area),
                            "is_external": (signed_area > 0)
                        })
                        block_counter += 1
                        
        print(f"[Reconstruction] Detected {len(blocks)} valid urban blocks (manzanas) from planar road network.")
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
        Computes the minimum perpendicular distance from facade center M(mx, my) to all road segments in G.
        """
        min_dist = float("inf")
        best_edge_id = None
        
        for u, v, data in self.G.edges(data=True):
            ux, uy = self.G.nodes[u]["x"], self.G.nodes[u]["y"]
            vx, vy = self.G.nodes[v]["x"], self.G.nodes[v]["y"]
            
            dx = vx - ux
            dy = vy - uy
            seg_len_sq = dx*dx + dy*dy
            
            if seg_len_sq < 1e-5:
                dist = math.sqrt((mx - ux)**2 + (my - uy)**2)
            else:
                t = ((mx - ux) * dx + (my - my) * dy) / seg_len_sq
                t = max(0.0, min(1.0, t))
                proj_x = ux + t * dx
                proj_y = uy + t * dy
                dist = math.sqrt((mx - proj_x)**2 + (my - proj_y)**2)
                
            if dist < min_dist:
                min_dist = dist
                best_edge_id = data["id"]
                
        return min_dist, best_edge_id

    def score_observation_candidate(self, mx: float, my: float, normal: np.ndarray, obs: dict, wall_edge_id: str) -> float:
        """
        Evaluates a candidate Layer 2 observation for matching a wall segment.
        Strictly prioritizes normal alignment, road containment, and visibility quality.
        """
        proj = obs["projection"]
        prov = obs["provenance"]
        meta = obs["metadata"]
        
        cx = proj["camera_x"]
        cy = proj["camera_y"]
        cam_yaw = math.radians(proj["yaw_degrees"])
        
        # Camera look vector
        v_cam = np.array([math.sin(cam_yaw), math.cos(cam_yaw)])
        
        # Alignment dot product: camera should face opposite to the outward wall normal
        alignment = -np.dot(v_cam, normal)
        if alignment <= 0.05:  # Camera is facing away from facade
            return 0.0
            
        dx = cx - mx
        dy = cy - my
        dist = math.sqrt(dx*dx + dy*dy)
        if dist < 1e-3:
            return 0.0
            
        # 1. Normal alignment multiplier
        score_align = alignment
        
        # 2. Relaxed Euclidean distance decay
        score_dist = math.exp(-dist / 35.0)
        
        # 3. Same Road Segment bonus
        source_pano_id = prov["source_pano_id"]
        obs_edge_id = self.pano_to_edge.get(source_pano_id)
        same_road_bonus = 1.8 if (obs_edge_id == wall_edge_id and wall_edge_id is not None) else 1.0
        
        # 4. Frontal Visibility Quality
        visibility_quality = meta.get("quality_score", 0.5)
        
        # 5. Combined Score
        score = score_align * score_dist * same_road_bonus * visibility_quality
        return score

    def extract_rectified_facade_observation_texture(
        self, 
        obs: dict, 
        A: tuple[float, float], 
        B: tuple[float, float], 
        height_meters: float
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
                return frontal_img.resize((512, 256), Image.BILINEAR)
                
            # Perform perspective division to get pixel coordinates
            px = (W_obs - 1) / 2.0 + f * (x_c / z_c)
            py = (H_obs - 1) / 2.0 - f * (y_c / z_c)
            
            img_pts.append([px, py])
            
        # Target coordinate mapping in standard 512x256 facade texture slice
        target_pts = np.float32([
            [0, 255],      # Bottom-Left
            [511, 255],    # Bottom-Right
            [511, 0],      # Top-Right
            [0, 0]         # Top-Left
        ])
        
        source_pts = np.float32(img_pts)
        
        # Compute perspective homography transform matrix
        M = cv2.getPerspectiveTransform(source_pts, target_pts)
        
        # Warp perspective to straighten texture slice (Border is transparent)
        np_frontal = np.array(frontal_img)
        np_warped = cv2.warpPerspective(np_frontal, M, (512, 256), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        
        return Image.fromarray(np_warped, "RGBA")

    def generate_transparent_fallback(self, width=512, height=256) -> Image.Image:
        if getattr(self, "_cached_transparent", None) is not None:
            return self._cached_transparent.copy()
            
        # Fully transparent RGBA fallback image
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        self._cached_transparent = img
        return self._cached_transparent.copy()
    def find_horizontal_overlap_offset(self, img1: Image.Image, img2: Image.Image) -> int:
        """
        Finds the optimal horizontal starting offset of img2 relative to img1.
        Both images are assumed to be PIL Images of size 512x256.
        Uses coarse-to-fine Normalized Cross-Correlation (NCC) template matching on grayscale conversions.
        """
        gray1 = cv2.cvtColor(np.array(img1), cv2.COLOR_RGB2GRAY)
        gray2 = cv2.cvtColor(np.array(img2), cv2.COLOR_RGB2GRAY)
        
        best_s = 350  # Default fallback shift (around 30% overlap)
        best_score = -1.0
        
        # 1. Coarse search with step of 5
        for s in range(100, 460, 5):
            w_overlap = 512 - s
            strip1 = gray1[:, s:512]
            strip2 = gray2[:, 0:w_overlap]
            
            score = cv2.matchTemplate(strip1, strip2, cv2.TM_CCOEFF_NORMED)[0, 0]
            if score > best_score:
                best_score = score
                best_s = s
                
        # 2. Fine search with step of 1 around best coarse shift
        coarse_best = best_s
        for s in range(max(100, coarse_best - 4), min(460, coarse_best + 5)):
            w_overlap = 512 - s
            strip1 = gray1[:, s:512]
            strip2 = gray2[:, 0:w_overlap]
            
            score = cv2.matchTemplate(strip1, strip2, cv2.TM_CCOEFF_NORMED)[0, 0]
            if score > best_score:
                best_score = score
                best_s = s
                
        # If the match score is too low, fall back to a reasonable default overlap (e.g. 350)
        if best_score < 0.35:
            return 350
            
        return best_s

    def stitch_facades_with_similarity(self, group: list) -> tuple[Image.Image, list[int]]:
        """
        Stitches a list of sequential facade images using template matching overlaps and linear blending.
        Each item in the group is: (f_idx, tex_img, status, f_id).
        Returns the final stitched Image and a list of horizontal starting coordinates (offsets) for each image.
        """
        N = len(group)
        if N == 1:
            return group[0][1].convert("RGBA"), [0]
            
        # Calculate shifts between adjacent images
        shifts = []
        for i in range(N - 1):
            img1 = group[i][1]
            img2 = group[i+1][1]
            status1 = group[i][2]
            status2 = group[i+1][2]
            
            if status1 == "textured" and status2 == "textured":
                s = self.find_horizontal_overlap_offset(img1, img2)
            else:
                s = 512  # If either is transparent fallback, do not overlap-blend
            shifts.append(s)
            
        # Compute absolute horizontal positions (offsets)
        offsets = [0]
        curr = 0
        for s in shifts:
            curr += s
            offsets.append(curr)
            
        W_final = offsets[-1] + 512
        H_final = 256
        
        # Build the final image by pasting and blending (4 channels for RGBA)
        accum = np.zeros((H_final, W_final, 4), dtype=np.float32)
        weight = np.zeros((H_final, W_final), dtype=np.float32)
        
        for i, (f_idx, img, status, f_id) in enumerate(group):
            img_rgba = img.convert("RGBA")
            img_np = np.array(img_rgba, dtype=np.float32)
            x_start = offsets[i]
            x_end = x_start + 512
            
            # Determine the overlap regions to apply a linear ramp blend
            mask = np.ones((H_final, 512), dtype=np.float32)
            
            # Left overlap blending ramp
            if i > 0:
                left_overlap = 512 - shifts[i-1]
                if left_overlap > 0:
                    for col in range(left_overlap):
                        mask[:, col] = col / float(left_overlap)
                        
            # Right overlap blending ramp
            if i < N - 1:
                right_overlap = 512 - shifts[i]
                if right_overlap > 0:
                    for col in range(right_overlap):
                        mask[:, 512 - right_overlap + col] = 1.0 - (col / float(right_overlap))
                        
            # Add to accumulators across all 4 channels
            for c in range(4):
                accum[:, x_start:x_end, c] += img_np[:, :, c] * mask
            weight[:, x_start:x_end] += mask
            
        # Normalize by weights to get blended image
        weight = np.maximum(weight, 1e-5)
        for c in range(4):
            accum[:, :, c] /= weight
            
        final_np = np.clip(accum, 0, 255).astype(np.uint8)
        return Image.fromarray(final_np, "RGBA"), offsets

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

    def reconstruct_blocks_and_texture(self) -> tuple[list[dict], dict]:
        """
        Densely reconstructs and textures building block volumes.
        Identifies block_19 (Bancomer) dynamically and harvests orthogonal screenshots
        from Playwright Google Street View for its street-facing facades, selecting the oldest 2009 timeline captures.
        All other facades and blocks receive a procedural transparent texture fallback.
        """
        # Generate and save transparent_facade.png to disk for fallbacks in Blender
        fallback_img = self.generate_transparent_fallback()
        fallback_path = os.path.join(self.textures_dir, "transparent_facade.png")
        os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
        fallback_img.save(fallback_path)
        print(f"[Reconstruction] Transparent fallback texture saved to: {fallback_path}")

        raw_blocks = self.extract_block_polygons()
        
        # No synthetic splitting post-process - let them be generated by the same cycle method as the others
        
        blocks_data = []
        provenance = {}
        diagnostics = {}
        
        total_facades = 0
        textured_facades = 0
        diag_facades = []
        
        self.current_blocks_data = blocks_data
        self.current_provenance = provenance
        self.current_diagnostics = diagnostics
        self.current_diag_facades = diag_facades
        
        # 1. Resolve Bancomer Block dynamically
        BANCOMER_LAT = 32.573484
        BANCOMER_LON = -116.627276
        target_x, target_y = gps_to_local(BANCOMER_LAT, BANCOMER_LON)
        
        closest_block_id = None
        min_dist = float("inf")
        
        for block in raw_blocks:
            poly = block["polygon"]
            centroid_x = sum(pt[0] for pt in poly[:-1]) / (len(poly) - 1)
            centroid_y = sum(pt[1] for pt in poly[:-1]) / (len(poly) - 1)
            dist = math.sqrt((centroid_x - target_x)**2 + (centroid_y - target_y)**2)
            if dist < min_dist:
                min_dist = dist
                closest_block_id = block["block_id"]
                
        print(f"[Reconstruction] Target Bancomer Block resolved dynamically as: '{closest_block_id}' (Distance: {min_dist:.2f} meters).")

        for idx, rb in enumerate(raw_blocks):
            b_id = rb["block_id"]
            if rb.get("is_external", False):
                print(f"[Reconstruction] Skipping external boundary mega-manzana: '{b_id}'")
                continue
                
            raw_poly = rb["polygon"]
            local_diag_facades = []
            
            # Shrink polygon inward by 6.0m to establish street setback boundaries
            shrunk_poly = self.shrink_polygon(raw_poly, d=6.0)
            
            num_verts = len(shrunk_poly) - 1
            centroid_x = sum(pt[0] for pt in shrunk_poly[:-1]) / num_verts
            centroid_y = sum(pt[1] for pt in shrunk_poly[:-1]) / num_verts
            
            dist_to_center = math.sqrt(centroid_x**2 + centroid_y**2)
            # If the block is centered near (0, 0) (within 50 meters), it represents Parque Hidalgo (low park square)
            if dist_to_center < 50.0:
                height_meters = 1.0  # Parque Hidalgo is a low park level
            else:
                h = hash(b_id) % 100
                height_meters = 7.0 + (h % 3) * 2.0
            
            facade_textures = []
            uv_mappings = {}
            
            # Pre-compute facade cardinals and cache hit status at the block level for siblings/restitching checks
            facade_cardinals = {}
            facade_is_cached = {}
            for f_idx_sib in range(num_verts):
                sib_A = shrunk_poly[f_idx_sib]
                sib_B = shrunk_poly[f_idx_sib + 1]
                sib_dx = sib_B[0] - sib_A[0]
                sib_dy = sib_B[1] - sib_A[1]
                sib_normal = np.array([sib_dy, -sib_dx])
                sib_norm_len = np.linalg.norm(sib_normal)
                if sib_norm_len > 1e-5:
                    sib_normal = sib_normal / sib_norm_len
                else:
                    sib_normal = np.array([0.0, 1.0])
                sib_nx, sib_ny = sib_normal[0], sib_normal[1]
                if abs(sib_nx) > abs(sib_ny):
                    card = "East" if sib_nx > 0 else "West"
                else:
                    card = "North" if sib_ny > 0 else "South"
                
                f_id = f"{b_id}_facade_{f_idx_sib}"
                facade_cardinals[f_id] = card
                facade_is_cached[f_id] = os.path.exists(f"data/screenshots/facades/{f_id}.png") and f_id in self.metadata_cache
            
            for f_idx in range(num_verts):
                A = shrunk_poly[f_idx]
                B = shrunk_poly[f_idx + 1]
                
                mx = (A[0] + B[0]) / 2.0
                my = (A[1] + B[1]) / 2.0
                
                dx = B[0] - A[0]
                dy = B[1] - A[1]
                
                # Compute segment outward-pointing normal (rotate B-A right: dx, dy -> dy, -dx)
                normal = np.array([dy, -dx])
                norm_len = np.linalg.norm(normal)
                if norm_len > 1e-5:
                    normal = normal / norm_len
                else:
                    normal = np.array([0.0, 1.0])
                    
                total_facades += 1
                facade_id = f"{b_id}_facade_{f_idx}"
                
                # Check distance to closest road segment
                road_dist, best_edge_id = self.get_road_distance(mx, my)
                
                # Compute cardinal direction of normal
                nx, ny = normal[0], normal[1]
                if abs(nx) > abs(ny):
                    cardinal = "East" if nx > 0 else "West"
                else:
                    cardinal = "North" if ny > 0 else "South"
                    
                is_street_facing = (road_dist <= 20.0)
                
                facade_img = None
                status = "fallback"
                prov = None
                meta = None
                
                # Check if the panorama for this cardinally-grouped face is already stitched and cached on disk
                cache_key = f"{b_id}_{cardinal.lower()}"
                panorama_filename = f"{b_id}_{cardinal.lower()}_facade.png"
                panorama_path = os.path.abspath(os.path.join(self.textures_dir, panorama_filename))
                
                cached_info = self.stitching_cache.get(cache_key)
                is_pano_cached = False
                if not self.reprocess and cached_info and os.path.exists(panorama_path):
                    # Check if any sibling is now textured but was not textured in the cached stitching
                    previously_textured = set(cached_info.get("textured_facades", []))
                    siblings = [fid for fid, card in facade_cardinals.items() if card == cardinal]
                    
                    restitch_needed = False
                    for sib_id in siblings:
                        sib_is_cached = facade_is_cached[sib_id]
                        sib_will_be_crawled = False
                        if not sib_is_cached and self.scraper is not None:
                            sib_idx = int(sib_id.split("_")[-1])
                            sib_A = shrunk_poly[sib_idx]
                            sib_B = shrunk_poly[sib_idx + 1]
                            sib_mx = (sib_A[0] + sib_B[0]) / 2.0
                            sib_my = (sib_A[1] + sib_B[1]) / 2.0
                            sib_road_dist, _ = self.get_road_distance(sib_mx, sib_my)
                            if sib_road_dist <= 20.0 and (self.radius is None or self.radius < 0 or dist_to_center <= self.radius):
                                sib_will_be_crawled = True
                                
                        if (sib_is_cached or sib_will_be_crawled) and sib_id not in previously_textured:
                            restitch_needed = True
                            break
                            
                    if not restitch_needed:
                        is_pano_cached = True
                        
                if is_pano_cached:
                    status = "textured"
                    facade_img = self.generate_transparent_fallback()  # simple fast placeholder, overridden by stitched panorama
                    
                    cached_entry = self.metadata_cache.get(facade_id, {})
                    meta = {
                        "latitude": cached_entry.get("latitude", 0.0),
                        "longitude": cached_entry.get("longitude", 0.0),
                        "pano_id": cached_entry.get("pano_id", ""),
                        "date": cached_entry.get("date", "")
                    }
                    prov = {
                        "source_pano_id": meta["pano_id"],
                        "source_date": meta["date"],
                        "source_lat_lon": [meta["latitude"], meta["longitude"]],
                        "facade_normal": [float(normal[0]), float(normal[1])],
                        "projection_parameters": {
                            "cam_z": 2.5,
                            "height_meters": float(height_meters),
                            "facade_length": float(norm_len)
                        }
                    }
                    provenance[facade_id] = prov
                    textured_facades += 1
                    
                    # Early escape for already cached panoramas
                    facade_textures.append(facade_img)
                    local_diag_facades.append({
                        "facade_id": facade_id,
                        "A": A, "B": B, "mx": mx, "my": my, "normal": normal,
                        "status": status, "best_obs": {
                            "metadata": {
                                "latitude": meta["latitude"],
                                "longitude": meta["longitude"]
                            }
                        }
                    })
                    diagnostics[facade_id] = {
                        "facade_id": facade_id,
                        "midpoint": [float(mx), float(my)],
                        "normal": [float(normal[0]), float(normal[1])],
                        "is_street_facing": is_street_facing,
                        "road_distance_meters": float(road_dist),
                        "status": status
                    }
                    continue
                
                # Check if this segment belongs to a block within the safety radius AND is street-facing
                dist_to_center = math.sqrt(centroid_x**2 + centroid_y**2)
                
                # Safety radius should only restrict the live scraper network crawls.
                # If already cached on disk and in metadata cache, we ALWAYS load and texture it, regardless of --radius!
                is_cached = os.path.exists(f"data/screenshots/facades/{facade_id}.png") and facade_id in self.metadata_cache
                
                if is_cached or (is_street_facing and (self.radius is None or self.radius < 0 or dist_to_center <= self.radius)):
                    print(f"\n[Scraper Target] Processing target facade slice: {facade_id} (Road distance: {road_dist:.2f} meters, Distance to center: {dist_to_center:.1f} meters).")
                    
                    # Offset the search coordinate by 8.0 meters outward along the facade normal vector
                    # to position the search query inside the street in front of the facade
                    search_x = mx + 8.0 * normal[0]
                    search_y = my + 8.0 * normal[1]
                    lat, lon = local_to_gps(search_x, search_y)
                    
                    print(f"[Coordinates Offset] Facade Midpoint: ({mx:.2f}, {my:.2f}) -> Offset Search Point: ({search_x:.2f}, {search_y:.2f})")
                    
                    cached_shot_path = f"data/screenshots/facades/{facade_id}.png"
                    screenshot_bytes = None
                    meta = None
                    pano_id = None
                    cam_lat = None
                    cam_lon = None
                    cx, cy = 0.0, 0.0
                    heading = 0.0
                    
                    # 1. Try to load from metadata_cache if screenshot exists on disk
                    if os.path.exists(cached_shot_path) and facade_id in self.metadata_cache:
                        print(f"[Offline Cache Hit] Found cached metadata and screenshot for {facade_id}. Bypassing network queries completely.")
                        try:
                            with open(cached_shot_path, "rb") as f_img:
                                screenshot_bytes = f_img.read()
                            
                            cached_entry = self.metadata_cache[facade_id]
                            pano_id = cached_entry.get("pano_id")
                            cam_lat = cached_entry.get("latitude")
                            cam_lon = cached_entry.get("longitude")
                            heading = cached_entry.get("heading")
                            cx, cy = gps_to_local(cam_lat, cam_lon)
                            
                            meta = {
                                "pano_id": pano_id,
                                "latitude": cam_lat,
                                "longitude": cam_lon,
                                "heading": heading,
                                "date": cached_entry.get("date", "")
                            }
                        except Exception as cache_err:
                            print(f"[Warning] Failed to read cached file or metadata: {cache_err}")
                            screenshot_bytes = None
                            
                    # 2. If not cached, perform live scraper & network lookup
                    if not screenshot_bytes and self.scraper is not None:
                        meta = self.scraper.fetch_public_metadata(lat=lat, lon=lon)
                        if meta:
                            pano_id = meta["pano_id"]
                            cam_lat = meta["latitude"]
                            cam_lon = meta["longitude"]
                            
                            # Find the oldest capture in the timeline
                            timeline = meta.get("timeline", [])
                            oldest_pano_id = pano_id
                            oldest_date = meta.get("date", "9999-12")
                            
                            for tl in timeline:
                                tl_id = tl["pano_id"]
                                tl_date = tl["date"]
                                # Enforce pre-2010 circa-2009 timeline selection
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
                            
                            # Compute perfectly perpendicular horizontal looking heading (directly along the inward normal vector -normal)
                            cx, cy = gps_to_local(cam_lat, cam_lon)
                            heading = math.degrees(math.atan2(-normal[0], -normal[1])) % 360.0
                            
                            # Mathematically verify camera alignment relative to facade
                            vx = mx - cx
                            vy = my - cy
                            dot_prod = vx * normal[0] + vy * normal[1]
                            is_correct_side = "YES" if dot_prod < 0 else "NO (behind block/obtuse)"
                            print(f"[Camera Alignment Diagnostics] Camera: ({cx:.2f}, {cy:.2f}), Midpoint: ({mx:.2f}, {my:.2f})")
                            print(f"                               Look Vector: ({vx:.2f}, {vy:.2f}), Normal: ({normal[0]:.2f}, {normal[1]:.2f})")
                            print(f"                               Dot Product (Outward Normal * Look Vector): {dot_prod:.2f} (In-front side verification: {is_correct_side})")
                            
                            # Check again if screenshot is on disk
                            if os.path.exists(cached_shot_path):
                                print(f"[Cache Hit] Loading cached screenshot for {facade_id} from {cached_shot_path}")
                                try:
                                    with open(cached_shot_path, "rb") as f_img:
                                        screenshot_bytes = f_img.read()
                                except Exception as cache_err:
                                    print(f"[Warning] Failed to read cached file: {cache_err}")
                                    
                            if not screenshot_bytes:
                                # Capture clean Playwright screenshot
                                print(f"[Playwright] Capturing orthogonal screenshot from ({cam_lat}, {cam_lon}) looking at {heading:.1f}°")
                                screenshot_bytes = self.scraper.capture_facade_screenshot(
                                    lat=cam_lat, 
                                    lon=cam_lon, 
                                    heading=heading, 
                                    pano_id=pano_id, 
                                    slice_id=facade_id
                                )
                                
                            # Update self.metadata_cache
                            cx, cy = gps_to_local(cam_lat, cam_lon)
                            yaw_rad = math.radians(heading)
                            rot_matrix = [
                                [math.cos(yaw_rad), -math.sin(yaw_rad), 0.0],
                                [math.sin(yaw_rad), math.cos(yaw_rad), 0.0],
                                [0.0, 0.0, 1.0]
                            ]
                            
                            road_name_val = ""
                            if best_edge_id:
                                for u_e, v_e, key_e, data_e in self.G.edges(keys=True, data=True):
                                    if data_e.get("id") == best_edge_id:
                                        road_name_val = data_e.get("name", "")
                                        break
                                        
                            # Geometry derivations matching the exact logs output
                            look_vector = [float(mx - cx), float(my - cy)]
                            dot_prod = float(look_vector[0] * normal[0] + look_vector[1] * normal[1])
                            is_correct_side = bool(dot_prod < 0)
                            
                            search_query_url = f"https://maps.googleapis.com/maps/api/js/GeoPhotoService.SingleImageSearch?pb=!1m5!1sapiv3!5sUS!11m2!1m1!1b0!2m4!1m2!3d{lat:.6f}!4d{lon:.6f}!2d50.0!3m10!2m2!1ses!2sMX!9m1!1e2!11m4!1m3!1e2!2b1!3e2!4m9!1e1!1e2!1e3!1e4!1e6!1e8!1e12!5m0!6m0&callback=_xdc_._v2mub5"
                            captured_url = f"https://www.google.com/maps?layer=c&cbll={cam_lat},{cam_lon}&panoid={pano_id}&cbp=11,{heading:.2f},,0,0"

                            self.metadata_cache[facade_id] = {
                                "pano_id": pano_id,
                                "latitude": cam_lat,
                                "longitude": cam_lon,
                                "altitude": meta.get("altitude") if meta else None,
                                "date": meta.get("date", "") if meta else "",
                                "heading": heading,
                                "pitch": meta.get("pitch") if meta else None,
                                "roll": meta.get("roll") if meta else None,
                                "hfov": None,
                                "vfov": None,
                                "focal_length_px": None,
                                "resolution": {
                                    "screenshot_width": 1280,
                                    "screenshot_height": 720,
                                    "slice_width": 512,
                                    "slice_height": 256
                                },
                                "optical_center": None,
                                "intrinsic_matrix": None,
                                "camera_height_m": None,
                                "camera_position_local": [float(cx), float(cy), None],
                                "camera_rotation_matrix": rot_matrix,
                                "road_relation": {
                                    "road_name": road_name_val,
                                    "road_distance_meters": float(road_dist),
                                    "road_edge_id": best_edge_id
                                },
                                "distance_to_center_m": float(dist_to_center),
                                "facade_midpoint_local": [float(mx), float(my)],
                                "offset_search_point_local": [float(search_x), float(search_y)],
                                "offset_search_point_gps": [float(lat), float(lon)],
                                "search_query_url": search_query_url,
                                "captured_url": captured_url,
                                "modern_pano_id": meta.get("pano_id") if meta else None,
                                "camera_alignment_diagnostics": {
                                    "look_vector": look_vector,
                                    "facade_normal": [float(normal[0]), float(normal[1])],
                                    "dot_product": dot_prod,
                                    "is_correct_side": is_correct_side
                                },
                                "image_filename": f"{facade_id}.png",
                                "block_id": b_id,
                                "facade_index": int(f_idx),
                                "facade_segment_vertices_local": [A, B],
                                "facade_normal_vector": [float(normal[0]), float(normal[1])],
                                "block_polygon_vertices_raw_local": raw_poly,
                                "block_polygon_vertices_shrunk_local": shrunk_poly,
                                "normal_offset_distance_m": 8.0,
                                "block_shrink_distance_m": 6.0
                            }
                            self.save_metadata_cache()
                            
                    if screenshot_bytes:
                        try:
                            facade_img = self.crop_facade(
                                screenshot_bytes,
                                A=A,
                                B=B,
                                cx=cx,
                                cy=cy,
                                heading=heading
                            )
                            status = "textured"
                            textured_facades += 1
                            
                            prov = {
                                "source_pano_id": pano_id,
                                "source_date": meta.get("date", ""),
                                "source_lat_lon": [cam_lat, cam_lon],
                                "facade_normal": [float(normal[0]), float(normal[1])],
                                "projection_parameters": {
                                    "cam_z": 2.5,
                                    "height_meters": float(height_meters),
                                    "facade_length": float(norm_len)
                                }
                            }
                            provenance[facade_id] = prov
                            print(f"[Success] Facade successfully resolved and cropped for: {facade_id}")
                        except Exception as crop_err:
                            print(f"[Warning] Failed to crop screenshot: {crop_err}")
                
                # If scraping failed, or this is non-targeted facade, generate transparent fallback
                if facade_img is None:
                    facade_img = self.generate_transparent_fallback()
                    
                facade_textures.append(facade_img)
                local_diag_facades.append({
                    "facade_id": facade_id,
                    "A": A, "B": B, "mx": mx, "my": my, "normal": normal,
                    "status": status, "best_obs": {
                        "metadata": {
                            "latitude": meta["latitude"] if (status == "textured" and meta) else 0.0,
                            "longitude": meta["longitude"] if (status == "textured" and meta) else 0.0
                        }
                    } if status == "textured" else None
                })
                
                diagnostics[facade_id] = {
                    "facade_id": facade_id,
                    "midpoint": [float(mx), float(my)],
                    "normal": [float(normal[0]), float(normal[1])],
                    "is_street_facing": is_street_facing,
                    "road_distance_meters": float(road_dist),
                    "status": status
                }
                
            if self.harvest_only:
                # In harvest-only mode, we don't process geometry, UV mappings, similarity stitching, or Blender texturing
                continue
                
            # Stitch block atlas image
            W_atlas = 512
            H_slice = 256
            H_atlas = num_verts * H_slice
            
            atlas_img = Image.new("RGB", (W_atlas, H_atlas))
            for f_idx, tex in enumerate(facade_textures):
                atlas_img.paste(tex, (0, f_idx * H_slice))
                
            atlas_filename = f"{b_id}_atlas.png"
            atlas_path = os.path.join(self.textures_dir, atlas_filename)
            try:
                # Bypassed writing atlas to disk per user instructions
                pass
            except Exception as e:
                print(f"[Warning] Bypassed atlas save: {e}")
            
            # Initialize all UV coordinates to fallback full-texture mapping
            for f_idx in range(num_verts):
                uv_mappings[f"{b_id}_facade_{f_idx}"] = [
                    [0.0, 0.0],
                    [1.0, 0.0],
                    [1.0, 1.0],
                    [0.0, 1.0]
                ]
                
            uv_mappings[f"{b_id}_roof"] = [[0.0, 0.0]] * num_verts
            
            # Group slices by their cardinal normal direction to stitch same-face scans horizontally
            face_groups = {"South": [], "East": [], "North": [], "West": []}
            for f_idx, (tex, status, f_id) in enumerate(zip(facade_textures, [local_diag_facades[i]["status"] for i in range(num_verts)], [local_diag_facades[i]["facade_id"] for i in range(num_verts)])):
                normal = local_diag_facades[f_idx]["normal"]
                nx, ny = normal[0], normal[1]
                if abs(nx) > abs(ny):
                    cardinal = "East" if nx > 0 else "West"
                else:
                    cardinal = "North" if ny > 0 else "South"
                face_groups[cardinal].append((f_idx, tex, status, f_id))
                
            # Build specific texture path mapping per facade slice
            facade_textures_map = {}
            for f_idx in range(num_verts):
                f_id = f"{b_id}_facade_{f_idx}"
                facade_textures_map[f_id] = os.path.abspath(os.path.join(self.textures_dir, "transparent_facade.png"))
                
            for cardinal, group in face_groups.items():
                if len(group) == 0:
                    continue
                # Sort by f_idx to ensure sequential order along the edge
                group.sort(key=lambda x: x[0])
                
                # Check if this face has any successfully textured slices
                has_textured = any(x[2] == "textured" for x in group)
                if has_textured:
                    try:
                        panorama_filename = f"{b_id}_{cardinal.lower()}_facade.png"
                        panorama_path = os.path.abspath(os.path.join(self.textures_dir, panorama_filename))
                        debug_pano_path = os.path.join("data/screenshots/facades", panorama_filename)
                        
                        cache_key = f"{b_id}_{cardinal.lower()}"
                        
                        # Incremental Processing: check if pre-stitched panorama exists and we are NOT reprocessing
                        if not self.reprocess and cache_key in self.stitching_cache and os.path.exists(panorama_path):
                            cached_info = self.stitching_cache[cache_key]
                            offsets = cached_info["offsets"]
                            W_final = cached_info["width"]
                            print(f"[Incremental Edge Stitcher] Using pre-stitched cached panorama for {b_id} {cardinal} (offsets loaded).")
                        else:
                            # Stitch adjacent slices using template matching and linear blending (similarity merging)
                            panorama_img, offsets = self.stitch_facades_with_similarity(group)
                            W_final = panorama_img.width
                            
                            os.makedirs(os.path.dirname(panorama_path), exist_ok=True)
                            panorama_img.save(panorama_path)
                            panorama_img.save(debug_pano_path)
                            print(f"[Edge Stitcher] Successfully stitched and similarity-merged {len(group)} slices into panorama: {debug_pano_path}")
                            
                            # Save to stitching cache with details of which facades are textured in it
                            self.stitching_cache[cache_key] = {
                                "offsets": offsets,
                                "width": W_final,
                                "textured_facades": [x[3] for x in group if x[2] == "textured"]
                            }
                            self.save_stitching_cache()
                        
                        # Set up horizontal panorama UV coordinates and texture path overrides
                        for i, (f_idx, tex, status, f_id) in enumerate(group):
                            u_start = offsets[i] / W_final
                            u_end = (offsets[i] + 512) / W_final
                            uv_mappings[f_id] = [
                                [u_start, 0.0],
                                [u_end, 0.0],
                                [u_end, 1.0],
                                [u_start, 1.0]
                            ]
                            facade_textures_map[f_id] = panorama_path
                    except Exception as stitch_err:
                        print(f"[Warning] Failed similarity stitching, falling back to basic concatenation: {stitch_err}")
                        K = len(group)
                        panorama_img = Image.new("RGBA", (K * 512, 256), (0, 0, 0, 0))
                        for i, (f_idx, tex, status, f_id) in enumerate(group):
                            panorama_img.paste(tex.convert("RGBA"), (i * 512, 0))
                            
                        panorama_filename = f"{b_id}_{cardinal.lower()}_facade.png"
                        panorama_path = os.path.abspath(os.path.join(self.textures_dir, panorama_filename))
                        debug_pano_path = os.path.join("data/screenshots/facades", panorama_filename)
                        
                        try:
                            os.makedirs(os.path.dirname(panorama_path), exist_ok=True)
                            panorama_img.save(panorama_path)
                            panorama_img.save(debug_pano_path)
                            print(f"[Edge Stitcher Fallback] Successfully stitched and georeferenced {K} slices into panorama: {debug_pano_path}")
                            
                            for i, (f_idx, tex, status, f_id) in enumerate(group):
                                u_start = i / K
                                u_end = (i + 1) / K
                                uv_mappings[f_id] = [
                                    [u_start, 0.0],
                                    [u_end, 0.0],
                                    [u_end, 1.0],
                                    [u_start, 1.0]
                                ]
                                facade_textures_map[f_id] = panorama_path
                        except Exception as fallback_err:
                            print(f"[Warning] Failed fallback stitching: {fallback_err}")
            
            roof_color_val = self.calculate_predominant_roof_color(facade_textures_map)
            
            # Persist roof_color in blocks_cache and virtual metadata_cache
            if b_id not in self.blocks_cache:
                self.blocks_cache[b_id] = {}
            self.blocks_cache[b_id]["roof_color"] = roof_color_val
            
            for f_idx in range(num_verts):
                f_id = f"{b_id}_facade_{f_idx}"
                if f_id in self.metadata_cache:
                    self.metadata_cache[f_id]["roof_color"] = roof_color_val
                    
            blocks_data.append({
                "block_id": b_id,
                "polygon": shrunk_poly,
                "height_meters": height_meters,
                "centroid": [centroid_x, centroid_y],
                "texture_atlas_path": os.path.abspath(atlas_path),
                "texture_atlas_filename": atlas_filename,
                "facade_textures": facade_textures_map,
                "uv_mappings": uv_mappings,
                "roof_color": roof_color_val,
                "traceability": [
                    {
                        "facade_idx": f_idx,
                        "source": "image" if k in provenance else "fallback"
                    }
                    for f_idx, k in enumerate([f"{b_id}_facade_{i}" for i in range(num_verts)])
                ]
            })
            diag_facades.extend(local_diag_facades)
            
        if self.harvest_only:
            print("[Harvest Mode] Scraping and metadata caching complete. Skipping all 3D reconstruction and Blender rendering.")
            if self.scraper:
                self.scraper.close()
            # Save stitching cache back to disk (Incremental processing)
            save_json(self.stitching_cache, self.stitching_cache_path)
            self.save_metadata_cache()
            return [], {}

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
        
        # Close persistent scraper session
        if self.scraper:
            self.scraper.close()
        
        # Save stitching cache back to disk (Incremental processing)
        save_json(self.stitching_cache, self.stitching_cache_path)
        print(f"[Reconstruction] Stitching cache successfully updated at: {self.stitching_cache_path}")
        
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
        
        def to_pix(x, y):
            px = margin + int(((x - xmin) / dx) * (width - 2 * margin))
            py = height - margin - int(((y - ymin) / dy) * (height - 2 * margin))
            return px, py
            
        # Clean light mode background
        canvas = Image.new("RGB", (width, height), (245, 246, 248))
        draw = ImageDraw.Draw(canvas, "RGBA")
        
        # 1. Draw entire road network skeleton (bounding box streets)
        node_map = {n["id"]: (n["x"], n["y"]) for n in scene_doc["road_graph"]["nodes"]}
        for ed in scene_doc["road_graph"]["edges"]:
            p1 = node_map.get(ed["u"])
            p2 = node_map.get(ed["v"])
            if p1 and p2:
                draw.line([to_pix(*p1), to_pix(*p2)], fill=(200, 204, 208, 255), width=2)
                
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
            draw.polygon(pixel_poly, fill=(rgb[0], rgb[1], rgb[2], 180), outline=(160, 165, 175, 255))
            
        # 3. Draw facades (highlight textured ones in green)
        for f in diag_facades:
            p_a = to_pix(*f["A"])
            p_b = to_pix(*f["B"])
            
            if f["status"] == "textured":
                col = (46, 204, 113, 255)  # Premium emerald green
                width_line = 4
            else:
                col = (200, 200, 200, 100)  # Subtle gray
                width_line = 1
                
            draw.line([p_a, p_b], fill=col, width=width_line)
            
        # Draw HUD dashboard in a clean modern light container
        draw.rectangle([50, 50, 550, 280], fill=(255, 255, 255, 240), outline=(200, 204, 208, 255), width=2)
        
        draw.text((70, 70), "TECATE RECONSTRUCTION COVERAGE MAP", fill=(44, 62, 80, 255))
        draw.text((70, 95), "Natural Cycles & Roof Color Mapping", fill=(52, 152, 219, 255))
        draw.text((70, 120), "-" * 48, fill=(200, 204, 208, 100))
        
        legend = [
            ("Textured Facade Slice (NCC Blended)", (46, 204, 113), "line"),
            ("Untextured Stucco Fallback Facade", (200, 200, 200), "line"),
            ("Urban Block (Colored by Roof Tint)", (180, 190, 200), "rect"),
            ("Road network segment", (200, 204, 208), "line")
        ]
        ly = 135
        for name, col_leg, geom in legend:
            if geom == "line":
                draw.line([70, ly + 8, 90, ly + 8], fill=col_leg, width=3)
            elif geom == "rect":
                draw.rectangle([70, ly + 2, 90, ly + 14], fill=(col_leg[0], col_leg[1], col_leg[2], 180), outline=(160, 165, 175))
                
            draw.text((105, ly), name, fill=(44, 62, 80, 255))
            ly += 22
            
        # Coverage metrics container
        draw.rectangle([50, height - 200, 450, height - 50], fill=(255, 255, 255, 240), outline=(200, 204, 208, 255), width=2)
        draw.text((70, height - 180), "COVERAGE METRICS", fill=(44, 62, 80, 255))
        draw.text((70, height - 150), f"Total Natural Blocks: {len(scene_doc['blocks'])}", fill=(127, 140, 141, 255))
        draw.text((70, height - 125), f"Historical Texturing: {coverage_pct:.1f}%", fill=(46, 204, 113, 255))
        draw.text((70, height - 100), f"Center Radius: {'Unlimited' if self.radius is None or self.radius < 0 else f'{self.radius}m'}", fill=(127, 140, 141, 255))
        
        debug_filepath = os.path.join(self.debug_dir, "global_observation_map.png")
        canvas.save(debug_filepath)
        print(f"[Reconstruction] Premium light diagnostic map saved to: {debug_filepath}")
