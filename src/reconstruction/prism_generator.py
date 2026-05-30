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
    def __init__(self, G: nx.MultiGraph, accepted_panos: list[dict] = None, export_dir: str = "export", data_dir: str = "data", headless: bool = False):
        self.G = G
        self.export_dir = export_dir
        self.data_dir = data_dir
        self.textures_dir = os.path.join(export_dir, "textures")
        self.debug_dir = os.path.join(export_dir, "debug")
        self.headless = headless
        
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
                
        # Initialize GoogleStreetViewScraper for direct headed/headless screenshot capturing
        from src.data_acquisition.browser_scraper import GoogleStreetViewScraper
        self.scraper = GoogleStreetViewScraper(headless=self.headless, G=self.G)

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
        
        # Warp perspective to straighten texture slice
        np_frontal = np.array(frontal_img)
        np_warped = cv2.warpPerspective(np_frontal, M, (512, 256), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(30, 30, 30))
        
        return Image.fromarray(np_warped)

    def generate_procedural_stucco(self, width=512, height=256) -> Image.Image:
        if getattr(self, "_cached_stucco", None) is not None:
            return self._cached_stucco.copy()
            
        # Beautiful warm stucco (stucco beige/cream)
        base_color = (238, 232, 220)
        img = Image.new("RGB", (width, height), base_color)
        np_img = np.array(img, dtype=np.float32)
        # Subtle Gaussian noise to mimic organic stucco surface roughness
        noise = np.random.normal(0, 3.5, (height, width, 3))
        np_img = np.clip(np_img + noise, 0, 255).astype(np.uint8)
        self._cached_stucco = Image.fromarray(np_img)
        return self._cached_stucco.copy()
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
            return group[0][1], [0]
            
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
                s = 512  # If either is stucco fallback, do not overlap-blend
            shifts.append(s)
            
        # Compute absolute horizontal positions (offsets)
        offsets = [0]
        curr = 0
        for s in shifts:
            curr += s
            offsets.append(curr)
            
        W_final = offsets[-1] + 512
        H_final = 256
        
        # Build the final image by pasting and blending
        accum = np.zeros((H_final, W_final, 3), dtype=np.float32)
        weight = np.zeros((H_final, W_final), dtype=np.float32)
        
        for i, (f_idx, img, status, f_id) in enumerate(group):
            img_np = np.array(img, dtype=np.float32)
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
                        
            # Add to accumulators
            for c in range(3):
                accum[:, x_start:x_end, c] += img_np[:, :, c] * mask
            weight[:, x_start:x_end] += mask
            
        # Normalize by weights to get blended image
        weight = np.maximum(weight, 1e-5)
        for c in range(3):
            accum[:, :, c] /= weight
            
        final_np = np.clip(accum, 0, 255).astype(np.uint8)
        return Image.fromarray(final_np), offsets

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
        
        # Resize to standard texture size 512x256
        return cropped.resize((512, 256), Image.Resampling.BILINEAR)

    def reconstruct_blocks_and_texture(self) -> tuple[list[dict], dict]:
        """
        Densely reconstructs and textures building block volumes.
        Identifies block_19 (Bancomer) dynamically and harvests orthogonal screenshots
        from Playwright Google Street View for its street-facing facades, selecting the oldest 2009 timeline captures.
        All other facades and blocks receive a procedural warm stucco texture fallback.
        """
        # Generate and save stucco_facade.png to disk for fallbacks in Blender
        stucco_img = self.generate_procedural_stucco()
        stucco_path = os.path.join(self.textures_dir, "stucco_facade.png")
        os.makedirs(os.path.dirname(stucco_path), exist_ok=True)
        stucco_img.save(stucco_path)
        print(f"[Reconstruction] Procedural fallback stucco texture saved to: {stucco_path}")

        raw_blocks = self.extract_block_polygons()
        
        # No synthetic splitting post-process - let them be generated by the same cycle method as the others
        
        blocks_data = []
        provenance = {}
        diagnostics = {}
        
        total_facades = 0
        textured_facades = 0
        diag_facades = []
        
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
                
                # Check if this segment belongs to a block within the safety radius AND is street-facing
                dist_to_center = math.sqrt(centroid_x**2 + centroid_y**2)
                is_within_radius = (dist_to_center <= 350.0)
                
                if is_within_radius and is_street_facing:
                    print(f"\n[Scraper Target] Processing target facade slice: {facade_id} (Road distance: {road_dist:.2f} meters, Distance to center: {dist_to_center:.1f} meters).")
                    
                    # Offset the search coordinate by 8.0 meters outward along the facade normal vector
                    # to position the search query inside the street in front of the facade
                    search_x = mx + 8.0 * normal[0]
                    search_y = my + 8.0 * normal[1]
                    lat, lon = local_to_gps(search_x, search_y)
                    
                    print(f"[Coordinates Offset] Facade Midpoint: ({mx:.2f}, {my:.2f}) -> Offset Search Point: ({search_x:.2f}, {search_y:.2f})")
                    
                    # Query SingleImageSearch to find the closest panorama to the offset street point
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
                        
                        # Optimization: check if screenshot is already cached on disk
                        cached_shot_path = f"data/screenshots/facades/{facade_id}.png"
                        screenshot_bytes = None
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
                                print(f"[Playwright Success] Facade successfully scraped and cropped for: {facade_id}")
                            except Exception as crop_err:
                                print(f"[Warning] Failed to crop screenshot: {crop_err}")
                
                # If scraping failed, or this is non-targeted facade, generate premium procedural stucco fallback
                if facade_img is None:
                    facade_img = self.generate_procedural_stucco()
                    
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
                facade_textures_map[f_id] = os.path.abspath(os.path.join(self.textures_dir, "stucco_facade.png"))
                
            for cardinal, group in face_groups.items():
                if len(group) == 0:
                    continue
                # Sort by f_idx to ensure sequential order along the edge
                group.sort(key=lambda x: x[0])
                
                # Check if this face has any successfully textured slices
                has_textured = any(x[2] == "textured" for x in group)
                if has_textured:
                    try:
                        # Stitch adjacent slices using template matching and linear blending (similarity merging)
                        panorama_img, offsets = self.stitch_facades_with_similarity(group)
                        W_final = panorama_img.width
                        
                        panorama_filename = f"{b_id}_{cardinal.lower()}_facade.png"
                        panorama_path = os.path.abspath(os.path.join(self.textures_dir, panorama_filename))
                        debug_pano_path = os.path.join("data/screenshots/facades", panorama_filename)
                        
                        os.makedirs(os.path.dirname(panorama_path), exist_ok=True)
                        panorama_img.save(panorama_path)
                        panorama_img.save(debug_pano_path)
                        print(f"[Edge Stitcher] Successfully stitched and similarity-merged {len(group)} slices into panorama: {debug_pano_path}")
                        
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
                        panorama_img = Image.new("RGB", (K * 512, 256))
                        for i, (f_idx, tex, status, f_id) in enumerate(group):
                            panorama_img.paste(tex, (i * 512, 0))
                            
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
            
            blocks_data.append({
                "block_id": b_id,
                "polygon": shrunk_poly,
                "height_meters": height_meters,
                "centroid": [centroid_x, centroid_y],
                "texture_atlas_path": os.path.abspath(atlas_path),
                "texture_atlas_filename": atlas_filename,
                "facade_textures": facade_textures_map,
                "uv_mappings": uv_mappings,
                "traceability": [
                    {
                        "facade_idx": f_idx,
                        "source": "image" if k in provenance else "fallback"
                    }
                    for f_idx, k in enumerate([f"{b_id}_facade_{i}" for i in range(num_verts)])
                ]
            })
            diag_facades.extend(local_diag_facades)
            
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
        self.scraper.close()
        
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
