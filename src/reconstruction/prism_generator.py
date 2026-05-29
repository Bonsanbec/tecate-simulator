import os
import json
import math
import numpy as np
import networkx as nx
import cv2
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
    def __init__(self, G: nx.MultiGraph, accepted_panos: list[dict] = None, export_dir: str = "export", data_dir: str = "data"):
        self.G = G
        self.export_dir = export_dir
        self.data_dir = data_dir
        self.textures_dir = os.path.join(export_dir, "textures")
        self.debug_dir = os.path.join(export_dir, "debug")
        
        ensure_dir(self.textures_dir)
        ensure_dir(self.debug_dir)
        
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
                
        # Load Layer 1 consolidated panoramas natively
        self.panoramas = []
        panos_dir = os.path.join(data_dir, "structural_graph", "panos")
        if os.path.exists(panos_dir):
            for f in os.listdir(panos_dir):
                if f.endswith(".json"):
                    pano_id = f[:-5]
                    meta_path = os.path.join(panos_dir, f)
                    image_path = os.path.join(panos_dir, f"{pano_id}.png")
                    if os.path.exists(image_path):
                        try:
                            meta = load_json(meta_path)
                            self.panoramas.append({
                                "pano_id": pano_id,
                                "metadata": meta,
                                "image_path": os.path.abspath(image_path)
                            })
                        except Exception:
                            pass
        print(f"[Reconstruction] Loaded {len(self.panoramas)} Layer 1 consolidated panoramas natively.")

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
                            "area_sq_meters": abs(signed_area)
                        })
                        block_counter += 1
                        
        print(f"[Reconstruction] Detected {len(blocks)} valid urban blocks (manzanas) from planar road network.")
        return blocks

    def segment_long_polygon_edges(self, poly: list[tuple[float, float]], max_length: float = 20.0) -> list[tuple[float, float]]:
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
            frontal_img = obs["image_path"]
        else:
            frontal_img = Image.open(obs["image_path"])
            
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
        
        # Warp perspective to straighten texture slice
        np_frontal = np.array(frontal_img)
        np_warped = cv2.warpPerspective(np_frontal, M, (512, 256), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(30, 30, 30))
        
        return Image.fromarray(np_warped)

    def reconstruct_blocks_and_texture(self) -> tuple[list[dict], dict]:
        """
        Natively matches Layer 2 perspective observations, projects and warps
        them onto building blocks, compiles multi-slice atlases, and compiles
        the visual global observation map.
        """
        raw_blocks = self.extract_block_polygons()
        blocks_data = []
        provenance = {}
        diagnostics = {}
        
        total_facades = 0
        textured_facades = 0
        diag_facades = []
        assigned_panos_global = set()
        
        for idx, rb in enumerate(raw_blocks):
            b_id = rb["block_id"]
            raw_poly = rb["polygon"]
            
            shrunk_poly = self.shrink_polygon(raw_poly, d=6.0)
            h = hash(b_id) % 100
            height_meters = 7.0 + (h % 3) * 2.0
            
            num_verts = len(shrunk_poly) - 1
            centroid_x = sum(pt[0] for pt in shrunk_poly[:-1]) / num_verts
            centroid_y = sum(pt[1] for pt in shrunk_poly[:-1]) / num_verts
            
            facade_textures = []
            uv_mappings = {}
            
            for f_idx in range(num_verts):
                A = shrunk_poly[f_idx]
                B = shrunk_poly[f_idx + 1]
                
                mx = (A[0] + B[0]) / 2.0
                my = (A[1] + B[1]) / 2.0
                
                dx = B[0] - A[0]
                dy = B[1] - A[1]
                
                # Outward facade normal (rotate B-A right: dx, dy -> dy, -dx)
                normal = np.array([dy, -dx])
                norm_len = np.linalg.norm(normal)
                if norm_len > 1e-5:
                    normal = normal / norm_len
                else:
                    normal = np.array([0.0, 1.0])
                    
                total_facades += 1
                
                # Enforce local uniqueness of panorama assignments per block
                assigned_panos_local = set()
                
                # Calculate road closeness and edge ID
                road_dist, best_edge_id = self.get_road_distance(mx, my)
                is_street_facing = (road_dist <= 25.0)
                
                best_pano = None
                best_score = 0.0
                candidates_log = []
                
                if is_street_facing and hasattr(self, 'panoramas') and self.panoramas:
                    for p in self.panoramas:
                        p_id = p["pano_id"]
                        meta = p["metadata"]
                        px, py = gps_to_local(meta["latitude"], meta["longitude"])
                        
                        cdx = px - mx
                        cdy = py - my
                        dist = math.sqrt(cdx*cdx + cdy*cdy)
                        
                        if dist > 35.0:
                            continue
                            
                        # Cosine angle between normal and camera direction
                        # v_cam points from facade midpoint to camera
                        cos_angle = 0.0
                        if dist > 1e-3:
                            cos_angle = (cdx * normal[0] + cdy * normal[1]) / dist
                            
                        # Camera must be in front of the facade (street-facing)
                        if cos_angle < 0.1:
                            continue
                            
                        # Score calculation
                        score = math.exp(-dist / 15.0) * cos_angle
                        
                        # Apply penalty for repeated panoramas to maximize diversity
                        if p_id in assigned_panos_local:
                            score *= 0.1
                        elif p_id in assigned_panos_global:
                            score *= 0.3
                            
                        outcome = "evaluated"
                        candidates_log.append({
                            "pano_id": p_id,
                            "distance_meters": float(dist),
                            "total_score": float(score),
                            "outcome": outcome
                        })
                        
                        if score > best_score:
                            best_score = score
                            best_pano = p
                            
                rejection_reason = None
                if best_score < 0.05:
                    if best_pano is not None:
                        rejection_reason = f"highest_score_{best_score:.6f}_below_threshold"
                    else:
                        rejection_reason = "no_eligible_panorama"
                    best_pano = None
                    
                facade_id = f"{b_id}_facade_{f_idx}"
                diagnostics[facade_id] = {
                    "facade_id": facade_id,
                    "midpoint": [float(mx), float(my)],
                    "normal": [float(normal[0]), float(normal[1])],
                    "is_street_facing": is_street_facing,
                    "road_distance_meters": float(road_dist),
                    "selected_pano_id": best_pano["pano_id"] if best_pano else None,
                    "selected_score": float(best_score),
                    "rejection_reason": rejection_reason if not best_pano else None,
                    "candidates_evaluated": candidates_log
                }
                
                # 3. Facade Perspective Warping
                p_id = best_pano["pano_id"]
                assigned_panos_local.add(p_id)
                assigned_panos_global.add(p_id)
            
                pano_img = Image.open(best_pano["image_path"])
                # Determine camera look direction opposite to normal
                cam_yaw = (math.degrees(math.atan2(normal[0], normal[1])) + 180.0) % 360.0
                
                is_sim = p_id.startswith("sim_pano")
                # Match main.py road heading alignment
                best_heading = 0.0
                if self.pano_to_edge.get(p_id):
                    # Find road heading from stations
                    for station in getattr(self, 'camera_stations', []):
                        if station.get("station_id") == p_id or station.get("edge_id") == self.pano_to_edge[p_id]:
                            best_heading = station["road_heading"]
                            break
                
                pano_yaw = best_heading if is_sim else 180.0
                
                # Project rectilinear using py360convert.e2c cubemap projection
                from src.image_alignment.virtual_camera import project_rectilinear
                face_img = project_rectilinear(
                    pano_img=pano_img,
                    yaw_deg=cam_yaw,
                    pitch_deg=0.0,
                    fov_deg=90.0,
                    width=512,
                    height=512,
                    pano_yaw=pano_yaw,
                    is_sim=is_sim
                )
                
                # Warp using existing homography pipeline but passing the face image
                px, py = gps_to_local(best_pano["metadata"]["latitude"], best_pano["metadata"]["longitude"])
                obs_mock = {
                    "image_path": face_img,  # Directly pass PIL Image
                    "projection": {
                        "camera_x": px,
                        "camera_y": py,
                        "camera_z": 2.5,
                        "yaw_degrees": cam_yaw,
                        "fov_degrees": 90.0,
                        "image_width": 512,
                        "image_height": 512
                    }
                }
                
                facade_img = self.extract_rectified_facade_observation_texture(obs_mock, A, B, height_meters)
                textured_facades += 1
                status = "textured"
                
                # Save final diagnostics segment trace
                segment_debug_dir = os.path.join(self.debug_dir, "facade_observations", facade_id)
                ensure_dir(segment_debug_dir)
                facade_img.save(os.path.join(segment_debug_dir, "final_texture.png"))
                
                prov = {
                    "source_pano_id": p_id,
                    "source_date": best_pano["metadata"].get("date", ""),
                    "source_lat_lon": [best_pano["metadata"]["latitude"], best_pano["metadata"]["longitude"]],
                    "selected_score": float(best_score),
                    "facade_normal": [float(normal[0]), float(normal[1])],
                    "projection_parameters": {
                        "cam_z": 2.5,
                        "height_meters": float(height_meters),
                        "facade_length": float(norm_len)
                    }
                }
                provenance[facade_id] = prov
                
            facade_textures.append(facade_img)
            diag_facades.append({
                "facade_id": f"{b_id}_f{f_idx}",
                "A": A, "B": B, "mx": mx, "my": my, "normal": normal,
                "status": status, "best_obs": best_pano
            })
                
            # Stitch block atlas image
            W_atlas = 512
            H_slice = 256
            H_atlas = num_verts * H_slice
            
            atlas_img = Image.new("RGB", (W_atlas, H_atlas))
            for f_idx, tex in enumerate(facade_textures):
                atlas_img.paste(tex, (0, f_idx * H_slice))
                
            atlas_filename = f"{b_id}_atlas.png"
            atlas_path = os.path.join(self.textures_dir, atlas_filename)
            atlas_img.save(atlas_path)
            
            # Map UV coords
            for f_idx in range(num_verts):
                y_start = f_idx * H_slice
                y_end = (f_idx + 1) * H_slice
                
                v_bottom = y_start / H_atlas
                v_top = y_end / H_atlas
                
                uv_mappings[f"{b_id}_facade_{f_idx}"] = [
                    [0.0, v_bottom],
                    [1.0, v_bottom],
                    [1.0, v_top],
                    [0.0, v_top]
                ]
                
            uv_mappings[f"{b_id}_roof"] = [[0.0, 0.0]] * num_verts
            
            blocks_data.append({
                "block_id": b_id,
                "polygon": shrunk_poly,
                "height_meters": height_meters,
                "centroid": [centroid_x, centroid_y],
                "texture_atlas_path": os.path.abspath(atlas_path),
                "texture_atlas_filename": atlas_filename,
                "uv_mappings": uv_mappings,
                "traceability": [
                    {
                        "facade_idx": f_idx,
                        "source": "image" if k in provenance else "fallback"
                    }
                    for f_idx, k in enumerate([f"{b_id}_facade_{i}" for i in range(num_verts)])
                ]
            })
            
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
        
        # Compile global observation map
        self.generate_diagnostic_visualization(scene_doc, diag_facades, meta_out["coverage_percentage"])
        
        return blocks_data, scene_doc

    def generate_diagnostic_visualization(self, scene_doc: dict, diag_facades: list[dict], coverage_pct: float):
        """
        Compiles a premium visual diagnostic map (global_observation_map.png) to export/debug/
        mapping road network, block polygons, normal arrows, and assignment lines.
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
            
        canvas = Image.new("RGB", (width, height), (15, 17, 22))
        draw = ImageDraw.Draw(canvas, "RGBA")
        
        center_px, center_py = to_pix(0, 0)
        draw.ellipse([center_px - 800, center_py - 800, center_px + 800, center_py + 800], fill=(28, 52, 94, 30))
        
        node_map = {n["id"]: (n["x"], n["y"]) for n in scene_doc["road_graph"]["nodes"]}
        for ed in scene_doc["road_graph"]["edges"]:
            p1 = node_map.get(ed["u"])
            p2 = node_map.get(ed["v"])
            if p1 and p2:
                draw.line([to_pix(*p1), to_pix(*p2)], fill=(60, 65, 75, 120), width=2)
                
        for bl in scene_doc["blocks"]:
            poly = bl["polygon"]
            pixel_poly = [to_pix(pt[0], pt[1]) for pt in poly]
            draw.polygon(pixel_poly, fill=(40, 50, 70, 40), outline=(80, 110, 150, 80))
            
        for f in diag_facades:
            p_a = to_pix(*f["A"])
            p_b = to_pix(*f["B"])
            p_m = to_pix(f["mx"], f["my"])
            
            if f["status"] == "textured":
                col = (40, 255, 120, 255)
                width_line = 3
            elif f["status"] == "no_data":
                col = (255, 100, 0, 255)
                width_line = 3
            else:
                col = (130, 135, 145, 120)
                width_line = 1
                
            draw.line([p_a, p_b], fill=col, width=width_line)
            
            norm_end_x = f["mx"] + f["normal"][0] * 6.0
            norm_end_y = f["my"] + f["normal"][1] * 6.0
            p_norm = to_pix(norm_end_x, norm_end_y)
            draw.line([p_m, p_norm], fill=(0, 235, 235, 180), width=2)
            
            arrow_angle = math.atan2(f["normal"][1], f["normal"][0])
            a1_x = norm_end_x + 1.8 * math.cos(arrow_angle + 3.0 * math.pi / 4.0)
            a1_y = norm_end_y + 1.8 * math.sin(arrow_angle + 3.0 * math.pi / 4.0)
            a2_x = norm_end_x + 1.8 * math.cos(arrow_angle - 3.0 * math.pi / 4.0)
            a2_y = norm_end_y + 1.8 * math.sin(arrow_angle - 3.0 * math.pi / 4.0)
            draw.line([p_norm, to_pix(a1_x, a1_y)], fill=(0, 235, 235, 180), width=1)
            draw.line([p_norm, to_pix(a2_x, a2_y)], fill=(0, 235, 235, 180), width=1)
            
            best_obs = f["best_obs"]
            if best_obs:
                meta = best_obs["metadata"]
                px, py = gps_to_local(meta["latitude"], meta["longitude"])
                p_cam = to_pix(px, py)
                draw.line([p_m, p_cam], fill=(0, 235, 235, 100), width=2)
                
            try:
                draw.text((p_m[0] + 5, p_m[1] - 5), f["facade_id"], fill=(255, 235, 120, 220))
            except Exception:
                pass
                
        # Draw all active panorama camera positions
        if hasattr(self, 'panoramas') and self.panoramas:
            for p in self.panoramas:
                meta = p["metadata"]
                px, py = gps_to_local(meta["latitude"], meta["longitude"])
                p_cam = to_pix(px, py)
                draw.ellipse([p_cam[0] - 6, p_cam[1] - 6, p_cam[0] + 6, p_cam[1] + 6], fill=(0, 235, 235), outline=(255, 255, 255))
            
        # Draw HUD dashboard
        draw.rectangle([50, 50, 550, 280], fill=(20, 25, 35, 230), outline=(80, 110, 150, 120), width=2)
        draw.text((70, 70), "TECATE RECONSTRUCTION DIAGNOSTICS", fill=(255, 255, 255, 255))
        draw.text((70, 95), "Decoupled 2D Homography Perspective Warp", fill=(80, 180, 255, 255))
        draw.text((70, 120), "-" * 48, fill=(80, 110, 150, 100))
        
        legend = [
            ("Textured street facade (Layer 2 Obs)", (40, 255, 120), "line"),
            ("Untextured street facade (Missing NO_DATA)", (255, 100, 0), "line"),
            ("Internal/Courtyard boundaries (No texture)", (130, 135, 145), "line"),
            ("Active Frontal Camera observation position", (0, 235, 235), "circle"),
            ("Warp assignment projection link", (0, 235, 235, 80), "dash")
        ]
        ly = 135
        for name, col_leg, geom in legend:
            if geom == "line":
                draw.line([70, ly + 8, 90, ly + 8], fill=col_leg, width=3)
            elif geom == "circle":
                draw.ellipse([72, ly + 2, 84, ly + 14], fill=col_leg, outline=(255, 255, 255))
            elif geom == "dash":
                draw.line([70, ly + 8, 90, ly + 8], fill=col_leg, width=1)
                
            draw.text((105, ly), name, fill=(210, 220, 235, 255))
            ly += 22
            
        draw.rectangle([50, height - 200, 450, height - 50], fill=(20, 25, 35, 230), outline=(80, 110, 150, 120), width=2)
        draw.text((70, height - 180), "COVERAGE METRICS", fill=(255, 255, 255, 255))
        draw.text((70, height - 150), f"Total Blocks: {len(scene_doc['blocks'])}", fill=(160, 180, 210, 255))
        draw.text((70, height - 125), f"Historical Texturing Coverage: {coverage_pct:.1f}%", fill=(0, 235, 235, 255))
        draw.text((70, height - 100), f"Layer 1 Panoramas: {len(getattr(self, 'panoramas', []))} nodes", fill=(160, 180, 210, 255))
        
        debug_filepath = os.path.join(self.debug_dir, "global_observation_map.png")
        canvas.save(debug_filepath)
        print(f"[Reconstruction] Premium diagnostic map saved to: {debug_filepath}")
