import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

class ProceduralStreetViewGenerator:
    """
    Generates high-fidelity, geometrically correct synthetic Street View panoramas.
    Simulates physical storefronts, camera noise, compression artifacts, and temporal differences
    (2009 vs. Modern) to test spatial and temporal filters.
    """
    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)

    def generate_facade_elements(self, edge_id: str, length_meters: float) -> list[dict]:
        """
        Deterministically creates storefront elements (windows, doors, signs) along an edge facade.
        Each element has a fixed world coordinate (distance along the street, height, size).
        """
        # Deterministic generation per edge using hash of edge_id
        h = hash(edge_id) % 10000
        rng = np.random.default_rng(h)
        
        elements = []
        # Place elements every 4 to 8 meters on both left (-W) and right (+W) sides
        for side in [-1, 1]:
            curr_dist = 2.0
            while curr_dist < length_meters - 2.0:
                el_type = rng.choice(["storefront", "residence", "blank"])
                
                if el_type == "storefront":
                    elements.append({
                        "side": side,  # -1 is Left (270 deg), +1 is Right (90 deg)
                        "dist_along": curr_dist,
                        "width": 3.5,
                        "height": 2.8,
                        "color": tuple(rng.integers(50, 220, size=3)),
                        "sign_text": f"TECATE {rng.choice(['Abarrotes', 'Tacos', 'Farmacia', 'Cerveza', 'Taller'])}",
                        "sign_color": tuple(rng.integers(10, 100, size=3))
                    })
                elif el_type == "residence":
                    elements.append({
                        "side": side,
                        "dist_along": curr_dist,
                        "width": 2.5,
                        "height": 2.2,
                        "color": tuple(rng.integers(150, 240, size=3)),
                        "sign_text": None
                    })
                curr_dist += rng.uniform(5.0, 9.0)
                
        return elements

    def render_panorama(self, 
                        camera_dist_along: float, 
                        edge_id: str, 
                        edge_length: float, 
                        elements: list[dict],
                        is_2009: bool) -> Image.Image:
        """
        Renders a 2560x640 equirectangular panorama.
        Projects facade elements onto the cylindrical panorama sphere using:
        theta = arctan2(side * W, dist_along - camera_dist_along)
        """
        width, height = 2560, 640
        img = Image.new("RGB", (width, height), (135, 206, 235))  # Sky blue background
        draw = ImageDraw.Draw(img)
        
        # 1. Draw Road and Sidewalk
        # Cylindrical projection: horizon is y = 320 (center)
        # Ground covers the lower half (y > 320)
        draw.rectangle([0, 320, width, height], fill=(80, 80, 80))  # Grey asphalt
        
        # Draw curb and sidewalk (in wide panorama, the sidewalks run along the left/right boundaries)
        # Left wall is at theta = 270 deg (-pi/2), Right wall is at theta = 90 deg (pi/2)
        # Let's draw horizontal bands representing standard sidewalks and curb lines
        draw.rectangle([0, 480, width, 520], fill=(150, 150, 150))  # Concrete sidewalk
        
        # Facade wall thickness/standoff W
        W = 6.0  # meters from street center
        
        # 2. Render Facade Walls
        # We project each facade element.
        # An element is at (dist_along, side * W, height_offset)
        for el in elements:
            side = el["side"]  # -1 = Left (theta ≈ 3pi/2), +1 = Right (theta ≈ pi/2)
            y_wall = side * W
            x_wall = el["dist_along"]
            
            # Subdivide each wall element into small vertical segments to handle wide-angle panoramic distortion
            seg_step = 0.1  # meters
            el_start = x_wall - el["width"]/2.0
            el_end = x_wall + el["width"]/2.0
            
            x_coords = np.arange(el_start, el_end, seg_step)
            
            for xc in x_coords:
                # World direction vector relative to camera
                dx = xc - camera_dist_along
                dy = y_wall
                
                # Angle around the cylinder (theta ranges from -pi to +pi)
                # Yaw orientation: 0 is straight forward along the street (dx > 0, dy = 0)
                theta = math.atan2(dy, dx)
                
                # Map theta [-pi, pi] to pixel x [0, width]
                px = int(((theta + math.pi) / (2 * math.pi)) * width)
                
                # Distance to element segment in 2D plane
                dist = math.sqrt(dx*dx + dy*dy)
                
                # Standard perspective height projection (height is inversely proportional to distance)
                proj_height = int((el["height"] / dist) * 450)
                
                y_center = 320  # Horizon
                y_top = y_center - int(proj_height * 0.4)
                y_bottom = y_center + int(proj_height * 0.6)
                
                # Draw the wall slice
                draw.line([px, y_top, px, y_bottom], fill=el["color"], width=2)
                
                # Draw storefront window/door features on the slice
                # If we are near the center of the element, draw a door/window
                rel_pos = (xc - el_start) / el["width"]
                if 0.15 < rel_pos < 0.45: # Window zone
                    w_top = y_center - int(proj_height * 0.1)
                    w_bottom = y_center + int(proj_height * 0.2)
                    draw.line([px, w_top, px, w_bottom], fill=(200, 230, 255), width=2) # Glass blue
                elif 0.55 < rel_pos < 0.85: # Door zone
                    d_top = y_center + int(proj_height * 0.1)
                    d_bottom = y_center + int(proj_height * 0.55)
                    draw.line([px, d_top, px, d_bottom], fill=(60, 40, 20), width=2) # Wood brown
                    
                # Draw commercial sign board at the top of the storefront
                if el["sign_text"] and 0.1 < rel_pos < 0.9:
                    s_top = y_center - int(proj_height * 0.35)
                    s_bottom = y_center - int(proj_height * 0.18)
                    draw.line([px, s_top, px, s_bottom], fill=el["sign_color"], width=2)

        # 3. Add SIFT/ORB texture features (random historical posters, stone textures)
        # Drawing small lines, squares, and dots along the walls to make feature-matching authentic
        for _ in range(30):
            fx = self.rng.integers(0, width)
            fy = self.rng.integers(250, 480)
            f_color = tuple(self.rng.integers(0, 50, size=3))
            draw.rectangle([fx, fy, fx+4, fy+4], fill=f_color)

        # 4. Apply Temporal Degraded Visual Signatures (2009 vs Modern)
        if is_2009:
            # 2009 Era: Lower resolution sensor, higher compression, yellowish vintage color shift
            # Resize down and up to simulate low-resolution CCD sensors (Gen 1 / Gen 2 streetview)
            img_small = img.resize((1280, 320), Image.Resampling.BILINEAR)
            img = img_small.resize((width, height), Image.Resampling.NEAREST)
            
            # Apply standard camera sensor noise (Gaussian/Uniform)
            np_img = np.array(img, dtype=np.float32)
            noise = self.rng.normal(0, 12, np_img.shape)  # Stronger sensor noise
            np_img = np.clip(np_img + noise, 0, 255).astype(np.uint8)
            img = Image.fromarray(np_img)
            
            # Vintage color cast: increase Red/Yellow, decrease Blue slightly
            r, g, b = img.split()
            r = r.point(lambda p: min(255, int(p * 1.12)))
            g = g.point(lambda p: min(255, int(p * 1.05)))
            b = b.point(lambda p: int(p * 0.88))
            img = Image.merge("RGB", (r, g, b))
            
            # Add lens blur
            img = img.filter(ImageFilter.GaussianBlur(1.0))
        else:
            # Modern Era: High resolution, sharp crisp edges, neutral clean colors, low sensor noise
            np_img = np.array(img, dtype=np.float32)
            noise = self.rng.normal(0, 2, np_img.shape)  # Minimal noise
            np_img = np.clip(np_img + noise, 0, 255).astype(np.uint8)
            img = Image.fromarray(np_img)
            
        return img

    def generate_and_cache_simulated_dataset(self, 
                                             camera_stations: list[dict], 
                                             G, 
                                             cache_dir: str = "data/raw_scraped") -> list[dict]:
        """
        Generates simulated Street View panoramas and structural metadata,
        saving them directly to the local cache folder. Mimics the exact folder
        footprint of the browser scraper.
        """
        import os
        import json
        
        # Sort camera stations along edges to build adjacent navigation links
        edge_stations = {}
        for cam in camera_stations:
            e_id = cam["edge_id"]
            if e_id not in edge_stations:
                edge_stations[e_id] = []
            edge_stations[e_id].append(cam)
            
        for e_id in edge_stations:
            edge_stations[e_id].sort(key=lambda c: c["dist_along"])
            
        cached_nodes = []
        
        for idx, station in enumerate(camera_stations):
            s_id = station["station_id"]
            edge_id = station["edge_id"]
            dist_along = station["dist_along"]
            
            # Find edge length
            edge_len = 80.0
            for u, v, data in G.edges(data=True):
                if data["id"] == edge_id:
                    edge_len = data["length"]
                    break
                    
            # 1. Establish temporal split
            is_modern_segment = (edge_id in ["e_j2", "e_pc2"])
            
            # We generate both the 2009 version AND the 2026 version of each panorama!
            # This is beautiful because it populates a rich historical timeline at each physical node!
            for year in [2009, 2026]:
                is_2009 = (year == 2009)
                
                # Check if this node matches the primary temporal split or acts as timeline state
                pano_id = f"sim_pano_{idx:03d}_{'2009' if is_2009 else '2026'}"
                alt_pano_id = f"sim_pano_{idx:03d}_{'2026' if is_2009 else '2009'}"
                
                node_dir = os.path.join(cache_dir, pano_id)
                metadata_path = os.path.join(node_dir, "metadata.json")
                panorama_path = os.path.join(node_dir, "panorama.png")
                
                # Setup cache folder
                os.makedirs(node_dir, exist_ok=True)
                
                # Render panorama if not cached
                if not os.path.exists(panorama_path):
                    facade_elements = self.generate_facade_elements(edge_id, edge_len)
                    pano_img = self.render_panorama(dist_along, edge_id, edge_len, facade_elements, is_2009)
                    pano_img.save(panorama_path)
                    
                # 2. Build mock adjacency links along the edge segment
                adjacent_links = []
                # Find index along this edge
                curr_edge_list = edge_stations[edge_id]
                station_idx_in_edge = curr_edge_list.index(station)
                
                if station_idx_in_edge > 0:
                    prev_station = curr_edge_list[station_idx_in_edge - 1]
                    adjacent_links.append({
                        "pano_id": f"sim_pano_{camera_stations.index(prev_station):03d}_{'2009' if is_2009 else '2026'}",
                        "road_name": f"Street_{edge_id}",
                        "yaw_deg": (station["road_heading"] + 180.0) % 360.0
                    })
                    
                if station_idx_in_edge < len(curr_edge_list) - 1:
                    next_station = curr_edge_list[station_idx_in_edge + 1]
                    adjacent_links.append({
                        "pano_id": f"sim_pano_{camera_stations.index(next_station):03d}_{'2009' if is_2009 else '2026'}",
                        "road_name": f"Street_{edge_id}",
                        "yaw_deg": station["road_heading"]
                    })
                    
                # 3. Create mock timeline state (temporal lineage connection)
                timeline = [{
                    "pano_id": alt_pano_id,
                    "date": "2026-02" if is_2009 else "2009-08"
                }]
                
                meta = {
                    "pano_id": pano_id,
                    "latitude": float(station["latitude"]),
                    "longitude": float(station["longitude"]),
                    "date": "2009-08" if is_2009 else "2026-02",
                    "road_name": f"Street_{edge_id}",
                    "adjacent_links": adjacent_links,
                    "timeline": timeline,
                    "image_path": os.path.abspath(panorama_path)
                }
                
                # Save metadata JSON
                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=4)
                    
                # We only return the primary temporal node to the main orchestrator loop
                # representing what a standard single traversal crawl captures.
                is_primary_crawl_node = (is_modern_segment and not is_2009) or (not is_modern_segment and is_2009)
                if is_primary_crawl_node:
                    cached_nodes.append(meta)
                    
        print(f"[Procedural Cache] Generated and cached {len(cached_nodes)*2} simulated nodes in '{cache_dir}/'.")
        return cached_nodes
