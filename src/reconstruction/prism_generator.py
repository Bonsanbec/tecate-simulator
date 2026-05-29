import os
import json
import math
import numpy as np
import networkx as nx
from PIL import Image, ImageDraw, ImageFont
from src.core_io.coords import gps_to_local, local_to_gps

class UrbanBlockReconstructor:
    """
    Orchestrates the historical urban block reconstruction pipeline.
    Extracts block polygons from the road segment graph, segments long facades,
    filters road-facing edges, and reprojects Street View panoramas onto vertical
    prism walls using a virtual perspective camera model with weighted scoring.
    """
    def __init__(self, G: nx.MultiGraph, accepted_panos: list[dict], export_dir: str = "export"):
        self.G = G
        self.accepted_panos = accepted_panos
        self.export_dir = export_dir
        self.textures_dir = os.path.join(export_dir, "textures")
        self.debug_dir = os.path.join(export_dir, "debug")
        
        os.makedirs(self.textures_dir, exist_ok=True)
        os.makedirs(self.debug_dir, exist_ok=True)
        
        # Load the PIL images for accepted panoramas
        self.pano_cache = {}
        for pano in accepted_panos:
            p_id = pano["pano_id"]
            if "image" in pano:
                self.pano_cache[p_id] = pano["image"]
            else:
                img_path = pano.get("image_path")
                if img_path and os.path.exists(img_path):
                    try:
                        self.pano_cache[p_id] = Image.open(img_path)
                    except Exception as e:
                        print(f"[Warning] Failed to load panorama image {img_path}: {e}")

    def extract_block_polygons(self) -> list[dict]:
        """
        Extracts closed cycles from the road graph G using planar CCW traversal.
        Trims dead-ends first to ensure a stable cycle set.
        """
        print("[Reconstruction] Trimming road network to extract urban block cycles...")
        
        # Convert MultiGraph to simple Graph to remove parallel edge complexities
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
            
        # For each node, sort its outgoing neighbors counter-clockwise by angle
        sorted_neighbors = {}
        for u in temp_G.nodes():
            neighbors = list(temp_G.neighbors(u))
            ux, uy = temp_G.nodes[u]["x"], temp_G.nodes[u]["y"]
            
            # Sort function by CCW angle
            def get_angle(v):
                vx, vy = temp_G.nodes[v]["x"], temp_G.nodes[v]["y"]
                return math.atan2(vy - uy, vx - ux)
                
            neighbors.sort(key=get_angle)
            sorted_neighbors[u] = neighbors
            
        # Create the set of directed half-edges
        half_edges = []
        for u, v in temp_G.edges():
            half_edges.append((u, v))
            half_edges.append((v, u))
            
        visited = set()
        blocks = []
        block_counter = 0
        
        for u, v in half_edges:
            if (u, v) not in visited:
                # Trace planar face
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
                    # Calculate signed area
                    x = [temp_G.nodes[n]["x"] for n in loop]
                    y = [temp_G.nodes[n]["y"] for n in loop]
                    
                    signed_area = 0.5 * sum(x[i] * y[(i+1)%len(loop)] - x[(i+1)%len(loop)] * y[i] for i in range(len(loop)))
                    
                    # Exclude the unbounded outer face and very small artifact faces.
                    if 50.0 < abs(signed_area) < 2500000.0:
                        poly_verts = [(temp_G.nodes[n]["x"], temp_G.nodes[n]["y"]) for n in loop]
                        
                        # If traced clockwise, reverse to CCW
                        if signed_area < 0:
                            poly_verts.reverse()
                        
                        # Add segmented edges to prevent single panorama dominance
                        segmented_verts = self.segment_long_polygon_edges(poly_verts)
                        
                        blocks.append({
                            "block_id": f"block_{block_counter}",
                            "polygon": segmented_verts,
                            "area_sq_meters": abs(signed_area)
                        })
                        block_counter += 1
                        
        print(f"[Reconstruction] Detected {len(blocks)} valid urban blocks (manzanas) from planar road network.")
        return blocks

    def segment_long_polygon_edges(self, poly: list[tuple[float, float]], max_length: float = 10.0) -> list[tuple[float, float]]:
        """
        Spatially segments polygon edges longer than max_length.
        Inserts intermediate collinear vertices so they are processed as independent facade quads,
        preventing stretched textures and single-panorama dominance.
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
                # Divide segment
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
            
            # Inward normal rotating CCW 90 degrees: (x, y) -> (-y, x)
            normal1 = np.array([-n1[1], n1[0]])
            normal2 = np.array([-n2[1], n2[0]])
            
            # Bisector direction
            bisector = normal1 + normal2
            norm_bis = np.linalg.norm(bisector)
            
            if norm_bis < 1e-5:
                bisector = normal1
            else:
                bisector = bisector / norm_bis
                
            # Offset distance scaled by angle
            cos_theta = np.dot(bisector, normal1)
            cos_theta = max(0.1, cos_theta)
            offset_dist = d / cos_theta
            
            # Apply offset
            new_v = curr_v + offset_dist * bisector
            new_verts.append((float(new_v[0]), float(new_v[1])))
            
        return new_verts + [new_verts[0]]

    def get_road_distance(self, mx: float, my: float) -> float:
        """
        Computes the minimum perpendicular distance from facade center M(mx, my) to all road segments in G.
        Used to identify street-facing walls vs courtyard/internal walls.
        """
        min_dist = float("inf")
        for u, v, data in self.G.edges(data=True):
            ux, uy = self.G.nodes[u]["x"], self.G.nodes[u]["y"]
            vx, vy = self.G.nodes[v]["x"], self.G.nodes[v]["y"]
            
            # Perpendicular distance to segment
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
                
        return min_dist

    def score_panorama_candidate(self, mx: float, my: float, normal: np.ndarray, pano: dict) -> float:
        """
        Calculates a robust alignment-and-distance score for a panorama relative to a facade center.
        Pano must be in front of the facade. Relaxed distance decay used to cover wide areas.
        """
        cam_x = pano["graph_x"]
        cam_y = pano["graph_y"]
        
        dx = cam_x - mx
        dy = cam_y - my
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < 1e-3:
            return 0.0
            
        # Vector from facade center to camera
        v_facade_to_cam = np.array([dx / dist, dy / dist])
        
        # Alignment dot product: must be positive (facing camera, with perpendicularity restriction cos(theta) >= 0.40)
        alignment = np.dot(v_facade_to_cam, normal)
        
        if alignment < 0.40:
            return 0.0
            
        # Relaxed distance decay (45m characteristic scale) to prevent strict local match errors
        score_dist = math.exp(-dist / 45.0)
        
        # Weighted product score
        score = score_dist * alignment
        return score

    def generate_no_data_texture(self) -> Image.Image:
        """
        Creates an explicit debug checkerboard texture (black & grey) with a bright neon orange
        NO_DATA indicator text and diagonal cross to preserve data transparency.
        """
        width, height = 512, 256
        img = Image.new("RGB", (width, height), (30, 30, 30))
        draw = ImageDraw.Draw(img)
        
        # Draw checkerboard
        square_size = 32
        for y in range(0, height, square_size):
            for x in range(0, width, square_size):
                if ((x // square_size) + (y // square_size)) % 2 == 0:
                    draw.rectangle([x, y, x + square_size, y + square_size], fill=(55, 55, 55))
                    
        # Draw a bold neon orange diagnostic warning border and diagonal cross
        orange = (255, 100, 0)
        draw.rectangle([0, 0, width - 1, height - 1], outline=orange, width=4)
        draw.line([0, 0, width, height], fill=orange, width=3)
        draw.line([0, height, width, 0], fill=orange, width=3)
        
        # Draw "NO DATA" text in the center
        # Since standard fonts might not be available, we manually draw a robust vector-line indicator box
        draw.rectangle([150, 100, 362, 156], fill=(15, 15, 15), outline=orange, width=2)
        
        # Try to load default font
        try:
            font = ImageFont.load_default()
            draw.text((215, 120), "NO DATA", fill=orange, font=font)
        except Exception:
            # Fallback text draw
            draw.text((215, 120), "NO DATA", fill=orange)
            
        return img

    def extract_rectified_facade_texture(self, pano_id: str, A: tuple[float, float], B: tuple[float, float], height_meters: float, facade_id: str = None) -> Image.Image:
        """
        Invokes a virtual perspective camera projection on the flat facade quad A-B,
        reprojecting and flattening spherical/equirectangular coordinates into a planar texture.
        If facade_id is provided, applies Semantic Edge & Color Profiling (SECP) to segment
        and isolate building facades, rejecting sky, road, cars, and foliage.
        """
        pano_meta = None
        for p in self.accepted_panos:
            if p["pano_id"] == pano_id:
                pano_meta = p
                break
                
        if not pano_meta or pano_id not in self.pano_cache:
            return self.generate_no_data_texture()
            
        pano_img = self.pano_cache[pano_id]
        
        # Pinhole perspective mapping parameters
        cam_x = pano_meta["graph_x"]
        cam_y = pano_meta["graph_y"]
        cam_z = 2.5  # standard Street View camera height in meters
        
        is_sim = pano_id.startswith("sim_pano")
        
        # Camera center column alignment heading
        if is_sim:
            cam_orientation_yaw = pano_meta["corrected_road_heading"]
        else:
            cam_orientation_yaw = 180.0  # standard absolute North-aligned panoramas
            
        W_tex, H_tex = 512, 256
        W_pano, H_pano = pano_img.size
        
        # Vectorized projection mapping using NumPy
        cols = np.arange(W_tex)
        rows = np.arange(H_tex)
        col_grid, row_grid = np.meshgrid(cols, rows)
        
        u = col_grid / (W_tex - 1)
        v = 1.0 - (row_grid / (H_tex - 1))
        
        # 3D points on the flat vertical quad in world meters
        x_w = A[0] + u * (B[0] - A[0])
        y_w = A[1] + u * (B[1] - A[1])
        z_w = v * height_meters
        
        # Displacement relative to camera
        dx = x_w - cam_x
        dy = y_w - cam_y
        dz = z_w - cam_z
        
        # Cylindrical projection calculations
        d_xy = np.sqrt(dx*dx + dy*dy)
        d_xy = np.clip(d_xy, 1e-5, None)  # Prevent division by zero
        
        heading_rad = np.arctan2(dx, dy)
        heading_deg = np.degrees(heading_rad)
        heading_deg = (heading_deg + 360.0) % 360.0
        
        # Convert absolute compass heading to relative panorama pixels
        rel_heading = (heading_deg - cam_orientation_yaw) % 360.0
        col_img = (((rel_heading + 180.0) % 360.0) / 360.0 * W_pano).astype(np.int32)
        col_img = np.clip(col_img, 0, W_pano - 1)
        
        pitch = np.arctan2(dz, d_xy)
        
        # Handle perspective camera model vs equirectangular camera strip
        if is_sim:
            # Pinhole tangent mapping
            row_img = (320.0 - np.tan(pitch) * 450.0).astype(np.int32)
        else:
            # Equirectangular linear pitch mapping based on crop coordinates (y = 680 to 1704)
            row_img = (1280.0 * (0.16796875 - pitch / np.pi)).astype(np.int32)
            
        row_img = np.clip(row_img, 0, H_pano - 1)
        
        # Sample pixels
        np_pano = np.array(pano_img)
        np_facade = np_pano[row_img, col_img]
        raw_proj = Image.fromarray(np_facade)
        
        if facade_id:
            try:
                return self.process_facade_cv(raw_proj, pano_img, cam_x, cam_y, cam_orientation_yaw, A, B, facade_id)
            except Exception as e:
                print(f"[Warning] SECP Facade Extraction failed for {facade_id}: {e}. Falling back to raw projection.")
                
        return raw_proj

    def process_facade_cv(self, raw_proj: Image.Image, pano_img: Image.Image, 
                          cam_x: float, cam_y: float, cam_orientation_yaw: float, 
                          A: tuple[float, float], B: tuple[float, float], facade_id: str) -> Image.Image:
        """
        Applies Semantic Edge & Color Profiling (SECP) to segment and isolate the dominant 
        vertical facade from a raw perspective projection. Rejects sky, asphalt road, vehicles,
        and green foliage, replacing foreground/background clutter with local average wall colors.
        Generates a 5-panel horizontal debug image for the pipeline's inspectability.
        """
        import cv2
        
        # Convert raw_proj to numpy array (RGB)
        np_img = np.array(raw_proj)
        H_tex, W_tex = np_img.shape[:2]
        
        # 1. Color space conversions
        hsv = cv2.cvtColor(np_img, cv2.COLOR_RGB2HSV)
        gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
        
        # 2. Semantic feature masking
        # Blue/bright sky detection in the top 65% of the image
        sky_mask = np.zeros((H_tex, W_tex), dtype=bool)
        top_sky_limit = int(0.65 * H_tex)
        for y in range(top_sky_limit):
            for x in range(W_tex):
                h, s, v = hsv[y, x]
                is_blue_sky = (90 <= h <= 145) and (s >= 30) and (v >= 90)
                is_bright_sky = (s < 40) and (v >= 180)
                if is_blue_sky or is_bright_sky:
                    sky_mask[y, x] = True
                    
        # Asphalt/road gray detection in the bottom 50% of the image
        road_mask = np.zeros((H_tex, W_tex), dtype=bool)
        bottom_road_limit = int(0.50 * H_tex)
        for y in range(bottom_road_limit, H_tex):
            for x in range(W_tex):
                h, s, v = hsv[y, x]
                is_road_gray = (s < 55) and (45 <= v <= 165)
                if is_road_gray:
                    road_mask[y, x] = True
                    
        # Foliage (green trees/bushes) detection
        foliage_mask = (hsv[:, :, 0] >= 30) & (hsv[:, :, 0] <= 85) & (hsv[:, :, 1] >= 40) & (hsv[:, :, 2] >= 40)
        
        # Vehicles (high saturation or extreme highlights/shadows in the lower portion)
        car_mask = np.zeros((H_tex, W_tex), dtype=bool)
        for y in range(int(0.50 * H_tex), int(0.95 * H_tex)):
            for x in range(W_tex):
                h, s, v = hsv[y, x]
                if s > 70 or (s < 20 and (v > 230 or v < 30)):
                    car_mask[y, x] = True
                    
        # 3. Vertical profile analysis for roofline and base/sidewalk detection
        # Calculate horizontal gradient density (Sobel X to get vertical lines/edges of facade structures)
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        abs_sobel_x = np.absolute(sobel_x)
        row_edges = np.sum(abs_sobel_x, axis=1)
        max_edge = np.max(row_edges) if np.max(row_edges) > 0 else 1.0
        row_edges_norm = row_edges / max_edge
        
        row_sky_pct = np.mean(sky_mask, axis=1)
        row_road_pct = np.mean(road_mask, axis=1)
        
        # Facade score combines edge density and avoidance of sky/road
        row_scores = row_edges_norm * (1.0 - row_sky_pct) * (1.0 - row_road_pct)
        
        # Smooth scores with a 5-pixel moving average
        smoothed_scores = np.convolve(row_scores, np.ones(5)/5, mode='same')
        
        # Find roofline (y_top): transition from sky to building structure
        y_top = 0
        for y in range(int(0.55 * H_tex)):
            if smoothed_scores[y] > 0.10 and row_sky_pct[y] < 0.15:
                y_top = y
                break
                
        # Find baseline/ground (y_bottom): transition from facade to road/sidewalk
        y_bottom = H_tex - 1
        for y in range(H_tex - 1, int(0.45 * H_tex), -1):
            if smoothed_scores[y] > 0.10 and row_road_pct[y] < 0.20:
                y_bottom = y
                break
                
        # Safe fallback if detection is too small or invalid
        if y_bottom - y_top < int(0.35 * H_tex):
            y_top = int(0.12 * H_tex)
            y_bottom = int(0.85 * H_tex)
            
        # 4. Crop and clean the facade band
        facade_band = np_img[y_top:y_bottom, :]
        facade_hsv = hsv[y_top:y_bottom, :]
        
        # Mask of invalid pixels (foliage, cars, sky, road remnants) inside the cropped facade band
        invalid_mask = np.zeros(facade_band.shape[:2], dtype=bool)
        invalid_mask[foliage_mask[y_top:y_bottom, :]] = True
        invalid_mask[car_mask[y_top:y_bottom, :]] = True
        invalid_mask[road_mask[y_top:y_bottom, :]] = True
        invalid_mask[sky_mask[y_top:y_bottom, :]] = True
        
        # Compute local average color of valid facade pixels
        valid_pixels = facade_band[~invalid_mask]
        if len(valid_pixels) > 0:
            avg_color = np.mean(valid_pixels, axis=0).astype(np.uint8)
        else:
            avg_color = np.array([125, 115, 105], dtype=np.uint8) # Default historical warm stucco gray
            
        # Inpaint/replace invalid pixels with local average color
        clean_facade_band = facade_band.copy()
        clean_facade_band[invalid_mask] = avg_color
        
        # Resize clean facade back to original standard texture size (512x256)
        rectified_facade_np = cv2.resize(clean_facade_band, (W_tex, H_tex), interpolation=cv2.INTER_LINEAR)
        rectified_facade_img = Image.fromarray(rectified_facade_np)
        
        # 5. Compile 5-Panel Visual Debug Preview Image
        # Panel 1: Original panorama view (cropped context window centered at the facade direction)
        W_pano, H_pano = pano_img.size
        mx = (A[0] + B[0]) / 2.0
        my = (A[1] + B[1]) / 2.0
        dx = mx - cam_x
        dy = my - cam_y
        heading_rad = math.atan2(dx, dy)
        heading_deg = (math.degrees(heading_rad) + 360.0) % 360.0
        rel_heading = (heading_deg - cam_orientation_yaw) % 360.0
        
        center_col = int((rel_heading / 360.0) * W_pano)
        crop_w = int(H_pano / 2)
        crop_h = int(H_pano / 2)
        
        left = center_col - crop_w // 2
        right = center_col + crop_w // 2
        
        # Handle equirectangular wrap-around
        if left < 0:
            part2 = pano_img.crop((left + W_pano, int(H_pano * 0.25), W_pano, int(H_pano * 0.75)))
            part1 = pano_img.crop((0, int(H_pano * 0.25), right, int(H_pano * 0.75)))
            pano_crop = Image.new("RGB", (crop_w, crop_h))
            pano_crop.paste(part2, (0, 0))
            pano_crop.paste(part1, (part2.size[0], 0))
        elif right > W_pano:
            part1 = pano_img.crop((left, int(H_pano * 0.25), W_pano, int(H_pano * 0.75)))
            part2 = pano_img.crop((0, int(H_pano * 0.25), right - W_pano, int(H_pano * 0.75)))
            pano_crop = Image.new("RGB", (crop_w, crop_h))
            pano_crop.paste(part1, (0, 0))
            pano_crop.paste(part2, (part1.size[0], 0))
        else:
            pano_crop = pano_img.crop((left, int(H_pano * 0.25), right, int(H_pano * 0.75)))
            
        pano_crop_resized = pano_crop.resize((256, 256), Image.Resampling.BILINEAR)
        
        # Panel 2: Raw unsegmented perspective projection resized to 256x256
        raw_proj_resized = raw_proj.resize((256, 256), Image.Resampling.BILINEAR)
        
        # Panel 3: Color-coded semantic mask
        mask_viz = np_img.copy() # Start with background
        
        # Apply color overlays using NumPy vectorized blending
        mask_viz[sky_mask] = (0.3 * mask_viz[sky_mask] + 0.7 * np.array([0, 120, 255])).astype(np.uint8)
        mask_viz[road_mask] = (0.3 * mask_viz[road_mask] + 0.7 * np.array([80, 80, 80])).astype(np.uint8)
        mask_viz[foliage_mask] = (0.3 * mask_viz[foliage_mask] + 0.7 * np.array([0, 200, 80])).astype(np.uint8)
        mask_viz[car_mask] = (0.3 * mask_viz[car_mask] + 0.7 * np.array([255, 40, 40])).astype(np.uint8)
        
        # Highlight facade band
        mask_viz[y_top:y_bottom, :] = (0.6 * mask_viz[y_top:y_bottom, :] + 0.4 * np.array([255, 180, 0])).astype(np.uint8)
        
        # Draw white dividing lines for roof/ground lines
        cv2.line(mask_viz, (0, y_top), (W_tex - 1, y_top), (255, 255, 255), 2)
        cv2.line(mask_viz, (0, y_bottom), (W_tex - 1, y_bottom), (255, 255, 255), 2)
        
        mask_viz_resized = Image.fromarray(mask_viz).resize((256, 256), Image.Resampling.NEAREST)
        
        # Panel 4: Rectified isolated facade texture resized to 256x256
        rectified_resized = rectified_facade_img.resize((256, 256), Image.Resampling.BILINEAR)
        
        # Panel 5: Warped 3D wall quad preview
        src_pts = np.float32([[0, 0], [0, H_tex - 1], [W_tex - 1, H_tex - 1], [W_tex - 1, 0]])
        dst_pts = np.float32([[30, 40], [30, 216], [226, 176], [226, 80]])
        H_mat = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warp_preview = cv2.warpPerspective(rectified_facade_np, H_mat, (256, 256), borderValue=(20, 22, 28))
        # Draw quad border
        cv2.polylines(warp_preview, [np.int32(dst_pts)], isClosed=True, color=(0, 235, 235), thickness=2)
        warp_preview_img = Image.fromarray(warp_preview)
        
        # Assemble composite image (1280 x 286 px)
        composite = Image.new("RGB", (1280, 286), (15, 17, 22))
        draw = ImageDraw.Draw(composite)
        
        panels = [pano_crop_resized, raw_proj_resized, mask_viz_resized, rectified_resized, warp_preview_img]
        titles = ["1. Pano Context", "2. Raw Perspective", "3. Semantic Mask", "4. Rectified Facade", "5. 3D Wall Preview"]
        
        for idx, (panel, title) in enumerate(zip(panels, titles)):
            composite.paste(panel, (idx * 256, 30))
            # Draw titles
            draw.text((idx * 256 + 10, 8), title.upper(), fill=(0, 235, 235))
            if idx > 0:
                # Draw border lines
                draw.line([idx * 256, 0, idx * 256, 286], fill=(40, 50, 70), width=2)
                
        # Save to export/debug/facade_detection/
        facade_debug_dir = os.path.join(self.export_dir, "debug", "facade_detection")
        os.makedirs(facade_debug_dir, exist_ok=True)
        composite.save(os.path.join(facade_debug_dir, f"{facade_id}.png"))
        
        return rectified_facade_img

    def reconstruct_blocks_and_texture(self) -> tuple[list[dict], dict]:
        """
        Executes the main block generation, polygon shrinking, weighted scoring assignment,
        perspective rectification, texture atlas packing, and diagnostic map compilation.
        """
        raw_blocks = self.extract_block_polygons()
        blocks_data = []
        provenance = {}
        diagnostics = {}
        
        # Coverage statistics
        total_facades = 0
        textured_facades = 0
        
        # Visualization diagnostics details
        diag_facades = []
        
        for idx, rb in enumerate(raw_blocks):
            b_id = rb["block_id"]
            raw_poly = rb["polygon"]
            
            # Apply uniform inward mathematical polygon buffer
            shrunk_poly = self.shrink_polygon(raw_poly, d=6.0)
            
            # Assures deterministic approximate heights (6.0m to 12.0m height distribution)
            h = hash(b_id) % 100
            height_meters = 7.0 + (h % 3) * 2.0  # Heights are 7.0, 9.0, or 11.0 meters
            
            num_verts = len(shrunk_poly) - 1
            centroid_x = sum(pt[0] for pt in shrunk_poly[:-1]) / num_verts
            centroid_y = sum(pt[1] for pt in shrunk_poly[:-1]) / num_verts
            
            facade_textures = []
            uv_mappings = {}
            atlas_slices = []
            
            # Process each individual facade edge
            for f_idx in range(num_verts):
                A = shrunk_poly[f_idx]
                B = shrunk_poly[f_idx + 1]
                
                # Facade midpoint and normal
                mx = (A[0] + B[0]) / 2.0
                my = (A[1] + B[1]) / 2.0
                
                dx = B[0] - A[0]
                dy = B[1] - A[1]
                
                # Facade normal pointing outward (rotating B-A vector right: (dx, dy) -> (dy, -dx))
                normal = np.array([dy, -dx])
                norm_len = np.linalg.norm(normal)
                if norm_len > 1e-5:
                    normal = normal / norm_len
                else:
                    normal = np.array([0.0, 1.0])
                    
                total_facades += 1
                
                # 1. Road Closeness Check (Relaxed from 15m to 25m)
                road_dist = self.get_road_distance(mx, my)
                is_street_facing = (road_dist <= 25.0)
                
                best_pano_id = None
                best_score = 0.0
                candidates_log = []
                
                # 2. Weighted Panorama Scoring
                if is_street_facing:
                    for pano in self.accepted_panos:
                        score = self.score_panorama_candidate(mx, my, normal, pano)
                        
                        # Gather candidate details for diagnostics
                        cam_x = pano["graph_x"]
                        cam_y = pano["graph_y"]
                        cdx = cam_x - mx
                        cdy = cam_y - my
                        dist = math.sqrt(cdx*cdx + cdy*cdy)
                        v_facade_to_cam = np.array([cdx / dist, cdy / dist]) if dist > 1e-3 else np.array([0.0, 0.0])
                        alignment = float(np.dot(v_facade_to_cam, normal))
                        
                        outcome = "evaluated"
                        if alignment <= 0.05:
                            outcome = "rejected_not_in_front"
                        elif score < 0.005:
                            outcome = "below_minimal_score"
                            
                        candidates_log.append({
                            "pano_id": pano["pano_id"],
                            "distance_meters": float(dist),
                            "alignment_dot": float(alignment),
                            "total_score": float(score),
                            "outcome": outcome
                        })
                        
                        if score > best_score:
                            best_score = score
                            best_pano_id = pano["pano_id"]
                            
                # Enforce minimal score threshold (Relaxed from 0.15 to 0.005)
                rejection_reason = None
                if best_score < 0.005:
                    if best_pano_id is not None:
                        rejection_reason = f"highest_score_{best_score:.6f}_below_threshold"
                    else:
                        rejection_reason = "no_eligible_candidate"
                    best_pano_id = None
                    
                facade_id = f"{b_id}_facade_{f_idx}"
                diagnostics[facade_id] = {
                    "facade_id": facade_id,
                    "midpoint": [float(mx), float(my)],
                    "normal": [float(normal[0]), float(normal[1])],
                    "is_street_facing": is_street_facing,
                    "road_distance_meters": float(road_dist),
                    "selected_pano_id": best_pano_id,
                    "selected_score": float(best_score),
                    "rejection_reason": rejection_reason if not best_pano_id else None,
                    "candidates_evaluated": candidates_log
                }
                
                # 3. Facade Rectified Reprojection
                if best_pano_id:
                    facade_img = self.extract_rectified_facade_texture(best_pano_id, A, B, height_meters, facade_id=facade_id)
                    textured_facades += 1
                    status = "textured"
                    
                    # Save intermediate perspective-rectified PNG sample BEFORE UV mapping
                    # Bounded to the first 200 samples to prevent performance/disk bloat
                    if textured_facades <= 200:
                        samples_dir = os.path.join(self.debug_dir, "facade_samples")
                        os.makedirs(samples_dir, exist_ok=True)
                        sample_path = os.path.join(samples_dir, f"{facade_id}.png")
                        facade_img.save(sample_path)
                    
                    # Record provenance metadata
                    pano_meta = next(p for p in self.accepted_panos if p["pano_id"] == best_pano_id)
                    prov = {
                        "source_pano_id": best_pano_id,
                        "source_date": pano_meta.get("date", ""),
                        "source_lat_lon": [pano_meta["latitude"], pano_meta["longitude"]],
                        "selected_score": float(best_score),
                        "yaw_deg": float(pano_meta.get("corrected_road_heading", pano_meta.get("road_heading", 0.0))),
                        "facade_normal": [float(normal[0]), float(normal[1])],
                        "projection_parameters": {
                            "cam_z": 2.5,
                            "height_meters": float(height_meters),
                            "facade_length": float(norm_len)
                        }
                    }
                    provenance[facade_id] = prov
                else:
                    facade_img = self.generate_no_data_texture()
                    status = "no_data" if is_street_facing else "internal"
                    
                facade_textures.append(facade_img)
                diag_facades.append({
                    "facade_id": f"{b_id}_f{f_idx}",
                    "A": A, "B": B, "mx": mx, "my": my, "normal": normal,
                    "status": status, "best_pano_id": best_pano_id
                })
                
            # 4. Stitch vertical block atlas image
            W_atlas = 512
            H_slice = 256
            H_atlas = num_verts * H_slice
            
            atlas_img = Image.new("RGB", (W_atlas, H_atlas))
            for f_idx, tex in enumerate(facade_textures):
                atlas_img.paste(tex, (0, f_idx * H_slice))
                
            atlas_filename = f"{b_id}_atlas.png"
            atlas_path = os.path.join(self.textures_dir, atlas_filename)
            atlas_img.save(atlas_path)
            
            # 5. Define UV coordinates mapping
            for f_idx in range(num_verts):
                y_start = f_idx * H_slice
                y_end = (f_idx + 1) * H_slice
                
                v_bottom = y_start / H_atlas
                v_top = y_end / H_atlas
                
                # Blender quad vertex loop mapping:
                # 1. Bottom-start: [0.0, v_bottom]
                # 2. Bottom-end: [1.0, v_bottom]
                # 3. Top-end: [1.0, v_top]
                # 4. Top-start: [0.0, v_top]
                uv_mappings[f"{b_id}_facade_{f_idx}"] = [
                    [0.0, v_bottom],
                    [1.0, v_bottom],
                    [1.0, v_top],
                    [0.0, v_top]
                ]
                
            # Map flat roof to tiny untextured/default black region [0,0]
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
            
        # Write metadata.json including full provenance tracking
        metadata_filepath = os.path.join(self.export_dir, "metadata.json")
        meta_out = {
            "total_blocks": len(blocks_data),
            "total_facades": total_facades,
            "textured_facades": textured_facades,
            "coverage_percentage": (textured_facades / total_facades * 100.0) if total_facades > 0 else 0.0,
            "provenance": provenance
        }
        with open(metadata_filepath, "w", encoding="utf-8") as f:
            json.dump(meta_out, f, indent=4)
            
        print(f"[Reconstruction] Reconstructed {len(blocks_data)} blocks, textured {textured_facades}/{total_facades} facades ({meta_out['coverage_percentage']:.1f}% coverage).")
        
        # Write reconstruction_diagnostics.json to make facade assignment 100% diagnosable
        diagnostics_filepath = os.path.join(self.debug_dir, "reconstruction_diagnostics.json")
        with open(diagnostics_filepath, "w", encoding="utf-8") as f:
            json.dump(diagnostics, f, indent=4)
        print(f"[Reconstruction] Deep diagnostics log successfully written to: {diagnostics_filepath}")
        
        # Compile G road graph structure for compatibility with Blender road mesh builder
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
        
        # Generate diagnostic debug map
        self.generate_diagnostic_visualization(scene_doc, diag_facades, meta_out["coverage_percentage"])
        
        return blocks_data, scene_doc

    def generate_diagnostic_visualization(self, scene_doc: dict, diag_facades: list[dict], coverage_pct: float):
        """
        Compiles a premium visual diagnostic map (debug_reconstruction_map.png) to export/debug/
        mapping road network, block polygons, normal arrows, assignment lines, and coverage statistics.
        """
        width, height = 1920, 1080
        margin = 80
        
        # Calculate local metric boundaries
        xmin, ymin = float("inf"), float("inf")
        xmax, ymax = float("-inf"), float("-inf")
        
        for nd in scene_doc["road_graph"]["nodes"]:
            x, y = nd["x"], nd["y"]
            xmin, ymin = min(xmin, x), min(ymin, y)
            xmax, ymax = max(xmax, x), max(ymax, y)
            
        dx = max(100.0, xmax - xmin)
        dy = max(100.0, ymax - ymin)
        
        # Expand bounds slightly
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
        
        # Background radial glow
        center_px, center_py = to_pix(0, 0)
        draw.ellipse([center_px - 800, center_py - 800, center_px + 800, center_py + 800], fill=(28, 52, 94, 30))
        
        # Draw road network segments (thin grey lines)
        node_map = {n["id"]: (n["x"], n["y"]) for n in scene_doc["road_graph"]["nodes"]}
        for ed in scene_doc["road_graph"]["edges"]:
            p1 = node_map.get(ed["u"])
            p2 = node_map.get(ed["v"])
            if p1 and p2:
                draw.line([to_pix(*p1), to_pix(*p2)], fill=(60, 65, 75, 120), width=2)
                
        # Draw shrunk block boundaries
        for bl in scene_doc["blocks"]:
            poly = bl["polygon"]
            pixel_poly = [to_pix(pt[0], pt[1]) for pt in poly]
            draw.polygon(pixel_poly, fill=(40, 50, 70, 40), outline=(80, 110, 150, 80))
            
        # Draw facades, normals, and projection rays
        for f in diag_facades:
            p_a = to_pix(*f["A"])
            p_b = to_pix(*f["B"])
            p_m = to_pix(f["mx"], f["my"])
            
            # Select color based on texturing status
            if f["status"] == "textured":
                col = (40, 255, 120, 255)  # neon green
                width_line = 3
            elif f["status"] == "no_data":
                col = (255, 100, 0, 255)  # neon orange
                width_line = 3
            else:
                col = (130, 135, 145, 120)  # grey for internal/courtyard
                width_line = 1
                
            draw.line([p_a, p_b], fill=col, width=width_line)
            
            # Draw normals (small arrows) pointing outwards
            norm_end_x = f["mx"] + f["normal"][0] * 6.0
            norm_end_y = f["my"] + f["normal"][1] * 6.0
            p_norm = to_pix(norm_end_x, norm_end_y)
            draw.line([p_m, p_norm], fill=(0, 235, 235, 180), width=2)
            
            # Draw a tiny arrowhead for the normal
            # Arrow head corners rotating normal left and right by 135 deg
            arrow_angle = math.atan2(f["normal"][1], f["normal"][0])
            a1_x = norm_end_x + 1.8 * math.cos(arrow_angle + 3.0 * math.pi / 4.0)
            a1_y = norm_end_y + 1.8 * math.sin(arrow_angle + 3.0 * math.pi / 4.0)
            a2_x = norm_end_x + 1.8 * math.cos(arrow_angle - 3.0 * math.pi / 4.0)
            a2_y = norm_end_y + 1.8 * math.sin(arrow_angle - 3.0 * math.pi / 4.0)
            draw.line([p_norm, to_pix(a1_x, a1_y)], fill=(0, 235, 235, 180), width=1)
            draw.line([p_norm, to_pix(a2_x, a2_y)], fill=(0, 235, 235, 180), width=1)
            
            # Draw projection link lines to camera
            best_id = f["best_pano_id"]
            if best_id:
                # Find panorama camera station coordinates
                pano_meta = next(p for p in self.accepted_panos if p["pano_id"] == best_id)
                p_cam = to_pix(pano_meta["graph_x"], pano_meta["graph_y"])
                draw.line([p_m, p_cam], fill=(0, 235, 235, 100), width=2)
                
            # Draw facade text ID labels at their midpoint
            try:
                draw.text((p_m[0] + 5, p_m[1] - 5), f["facade_id"], fill=(255, 235, 120, 220))
            except Exception:
                pass
                
        # Draw accepted panorama stations and their heading indicators (visibility directions)
        for pano in self.accepted_panos:
            p_cam = to_pix(pano["graph_x"], pano["graph_y"])
            # Draw camera point
            draw.ellipse([p_cam[0] - 6, p_cam[1] - 6, p_cam[0] + 6, p_cam[1] + 6], fill=(0, 235, 235), outline=(255, 255, 255))
            
            # Draw heading pointer
            heading_deg = pano.get("corrected_road_heading", pano.get("road_heading", 0.0))
            heading_rad = math.radians(heading_deg)
            # Compass heading where 0 is North (Y axis) and 90 is East (X axis)
            indicator_len = 12.0
            idx = pano["graph_x"] + indicator_len * math.sin(heading_rad)
            idy = pano["graph_y"] + indicator_len * math.cos(heading_rad)
            p_ind = to_pix(idx, idy)
            draw.line([p_cam, p_ind], fill=(255, 235, 0, 220), width=2)
            
        # Draw HUD dashboard
        draw.rectangle([50, 50, 550, 280], fill=(20, 25, 35, 230), outline=(80, 110, 150, 120), width=2)
        draw.text((70, 70), "TECATE RECONSTRUCTION DIAGNOSTICS", fill=(255, 255, 255, 255))
        draw.text((70, 95), "Perspective Reprojection & UV Pack Map", fill=(80, 180, 255, 255))
        draw.text((70, 120), "-" * 48, fill=(80, 110, 150, 100))
        
        legend = [
            ("Textured street facade (Real 2009 Pano)", (40, 255, 120), "line"),
            ("Untextured street facade (Missing NO_DATA)", (255, 100, 0), "line"),
            ("Internal/Courtyard boundaries (No texture)", (130, 135, 145), "line"),
            ("Active Camera Panorama station", (0, 235, 235), "circle"),
            ("Reprojection camera assignment link", (0, 235, 235, 80), "dash")
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
            
        # Statistics Panel (bottom left)
        draw.rectangle([50, height - 200, 450, height - 50], fill=(20, 25, 35, 230), outline=(80, 110, 150, 120), width=2)
        draw.text((70, height - 180), "COVERAGE METRICS", fill=(255, 255, 255, 255))
        draw.text((70, height - 150), f"Total Blocks: {len(scene_doc['blocks'])}", fill=(160, 180, 210, 255))
        draw.text((70, height - 125), f"Historical Texturing Coverage: {coverage_pct:.1f}%", fill=(0, 235, 235, 255))
        draw.text((70, height - 100), f"Camera Stations: {len(self.accepted_panos)} nodes", fill=(160, 180, 210, 255))
        
        # Save debug visual map
        debug_filepath = os.path.join(self.debug_dir, "debug_reconstruction_map.png")
        canvas.save(debug_filepath)
        print(f"[Reconstruction] Premium diagnostic map saved to: {debug_filepath}")
