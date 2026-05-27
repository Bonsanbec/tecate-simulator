import math
import networkx as nx
import numpy as np

class BlockBuilder:
    """
    Segments the city into urban blocks (manzanas) based on the road graph cycles.
    Associates cameras and SfM 3D points with their corresponding block.
    """
    def __init__(self, G: nx.MultiGraph):
        self.G = G

    def segment_blocks(self) -> list[dict]:
        """
        Extracts planar cycles from the road graph to serve as block footprints.
        Returns a list of block dictionaries.
        """
        # Convert MultiGraph to simple Graph for cycle basis extraction
        simple_G = nx.Graph(self.G)
        cycles = nx.cycle_basis(simple_G)
        
        blocks = []
        block_counter = 0
        
        # We only accept cycles with 3 or more nodes (representing polygon blocks)
        # In a perfect grid, these will be 4-node cycles (squares/rectangles)
        for cy in cycles:
            if len(cy) < 3:
                continue
                
            # Retrieve Cartesian coordinate polygon
            coords = []
            for n_id in cy:
                node = self.G.nodes[n_id]
                coords.append([node["x"], node["y"]])
                
            # Close the polygon loop by appending the first coordinate to the end
            coords_closed = coords + [coords[0]]
            
            # Calculate Centroid
            xs = [pt[0] for pt in coords]
            ys = [pt[1] for pt in coords]
            centroid_x = sum(xs) / len(xs)
            centroid_y = sum(ys) / len(ys)
            
            # Filter out massive cycles (like the outer boundary of the entire graph)
            # An urban block in Tecate typically has an area of less than 200m x 200m
            # Let's calculate the bounding box size
            dx = max(xs) - min(xs)
            dy = max(ys) - min(ys)
            if dx > 350.0 or dy > 350.0:
                print(f"[Info] Pruning oversized cycle (likely map boundary): size {dx:.1f}m x {dy:.1f}m")
                continue
                
            blocks.append({
                "block_id": f"block_{block_counter}",
                "nodes": cy,
                "polygon": coords_closed,
                "centroid": [centroid_x, centroid_y],
                "bounding_box": [min(xs), min(ys), max(xs), max(ys)],
                "height": 6.5,  # default block building height in meters (approx 2 stories)
                "camera_assignments": [],
                "point_cloud": []
            })
            block_counter += 1
            
        print(f"[Info] Successfully extracted {len(blocks)} urban blocks (manzanas) from the road network.")
        return blocks

    def is_point_in_polygon(self, x: float, y: float, polygon: list[list[float]]) -> bool:
        """
        Standard ray-casting algorithm to determine if point is inside a polygon.
        """
        n = len(polygon)
        inside = False
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

    def aggregate_points_and_cameras(self, 
                                     blocks: list[dict], 
                                     camera_stations: list[dict], 
                                     point_cloud: np.ndarray, 
                                     point_colors: np.ndarray) -> list[dict]:
        """
        Associates camera views and reconstructed 3D points with their corresponding block.
        Determines which viewpoint angle looks inward at the block facade.
        """
        # 1. Assign SfM points to blocks
        # A point is assigned to a block if it lies inside or very close (within 10 meters) of the boundary
        if point_cloud is not None and len(point_cloud) > 0:
            for i, pt in enumerate(point_cloud):
                px, py, pz = pt
                best_block = None
                min_dist = float("inf")
                
                for bl in blocks:
                    # Quick bounding box check
                    bbox = bl["bounding_box"]
                    # Add a 10m buffer to boundary check
                    if (bbox[0] - 10.0 <= px <= bbox[2] + 10.0) and (bbox[1] - 10.0 <= py <= bbox[3] + 10.0):
                        # Calculate distance to centroid as a fallback or do point in polygon
                        cx, cy = bl["centroid"]
                        dist = math.sqrt((px - cx)**2 + (py - cy)**2)
                        
                        # Check point in polygon
                        if self.is_point_in_polygon(px, py, bl["polygon"]):
                            best_block = bl
                            break
                        elif dist < min_dist:
                            min_dist = dist
                            best_block = bl
                            
                # If point was close to a block, append it to the block's point cloud
                if best_block:
                    best_block["point_cloud"].append({
                        "coord": [float(px), float(py), float(pz)],
                        "color": [float(c) for c in point_colors[i]]
                    })

        # 2. Assign Camera viewpoints to blocks
        # For each camera station on the road network, find which blocks lie to its left (-90 deg) or right (+90 deg)
        for station in camera_stations:
            cx, cy = station["x"], station["y"]
            road_heading = station["road_heading"] # in degrees
            
            # Check left and right directions (orthogonal to road heading)
            headings = {
                "right": (road_heading + 90.0) % 360.0,
                "left": (road_heading - 90.0) % 360.0
            }
            
            for side, view_angle in headings.items():
                # Cast a ray 8 meters in this viewpoint direction to find which block it hits
                rad = math.radians(view_angle)
                ray_x = cx + 8.0 * math.cos(rad)
                ray_y = cy + 8.0 * math.sin(rad)
                
                # Check which block contains this ray target
                for bl in blocks:
                    if self.is_point_in_polygon(ray_x, ray_y, bl["polygon"]):
                        # This camera viewpoint looks directly at this block!
                        # We save it as a candidate observation for texturing and facade modeling.
                        bl["camera_assignments"].append({
                            "station_id": station["station_id"],
                            "x": cx,
                            "y": cy,
                            "camera_heading": view_angle, # Global angle looking at the facade
                            "side": side,
                            "dist_along": station["dist_along"],
                            "edge_id": station["edge_id"]
                        })
                        break
                        
        return blocks
