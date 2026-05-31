import json
import os
import math
import requests
import networkx as nx
import numpy as np
from src.core_io.coords import gps_to_local, local_to_gps

class TecateGraphBuilder:
    """
    Acquires, constructs, and normalizes the deterministic road network of Tecate.
    Segments highways, places virtual cameras, and calculates local metric coordinates.
    """
    def __init__(self, cache_dir: str = "data"):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "tecate_osm_cache.json")
        os.makedirs(cache_dir, exist_ok=True)

    def generate_default_tecate_grid(self) -> dict:
        """
        Generates a highly dense, realistic city-scale local street network grid
        for central Tecate to satisfy large-scale traversal requirements offline.
        """
        print("[Info] Generating large-scale, high-density Tecate street grid (15x15)...")
        
        # We generate a 15x15 grid of avenues and streets centered near Parque Hidalgo (32.5732, -116.6265)
        # Spaced by 0.0015 degrees (approx 160 meters, a standard city block)
        base_lat = 32.563
        base_lon = -116.637
        spacing = 0.0015
        
        nodes = {}
        edges = []
        edge_counter = 0
        
        # 1. Spawn 225 intersections
        for r in range(15):
            for c in range(15):
                node_id = f"n_{r}_{c}"
                lat = base_lat + r * spacing
                lon = base_lon + c * spacing
                nodes[node_id] = {
                    "id": node_id,
                    "lat": lat,
                    "lon": lon,
                    "name": f"Calle_{r} & Avenida_{c}"
                }
                
        # 2. Spawn 420 bi-directional road segments
        for r in range(15):
            for c in range(15):
                curr_id = f"n_{r}_{c}"
                # Connect horizontally (East-West avenues)
                if c < 14:
                    next_id = f"n_{r}_{c+1}"
                    edges.append({
                        "id": f"e_h_{edge_counter}",
                        "u": curr_id,
                        "v": next_id,
                        "name": f"Avenida_{r}"
                    })
                    edge_counter += 1
                # Connect vertically (North-South streets)
                if r < 14:
                    next_id = f"n_{r+1}_{c}"
                    edges.append({
                        "id": f"e_v_{edge_counter}",
                        "u": curr_id,
                        "v": next_id,
                        "name": f"Calle_{c}"
                    })
                    edge_counter += 1
                    
        data = {"nodes": nodes, "edges": edges}
        return data

    def load_tecate_polygon(self) -> list:
        polygon_path = "reference/tecate-polygon.json"
        if not os.path.exists(polygon_path):
            print(f"[Warning] Polygon file not found at: {polygon_path}")
            return []
        try:
            with open(polygon_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            features = data.get("features", [])
            if not features:
                return []
            geometry = features[0].get("geometry", {})
            geom_type = geometry.get("type")
            coords = geometry.get("coordinates", [])
            
            rings = []
            if geom_type == "Polygon":
                rings.append(coords[0])
            elif geom_type == "MultiPolygon":
                rings.append(coords[0][0])
            return rings[0] if rings else []
        except Exception as e:
            print(f"[Warning] Failed to load polygon: {e}")
            return []

    def fetch_osm_tecate(self, bbox: tuple[float, float, float, float] = (32.521704, -116.681499, 32.580233, -116.510525)) -> dict:
        """
        Queries OSM Overpass API to download highway street segments inside Tecate municipal polygon.
        Falls back to default cached files if offline or fails.
        """
        if os.path.exists(self.cache_file):
            print(f"[Info] Loading road network from cache file: {self.cache_file}")
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Warning] Failed to read cache: {e}. Downloading instead...")

        overpass_url = "https://overpass-api.de/api/interpreter"
        
        # Load municipal polygon
        poly_coords = self.load_tecate_polygon()
        if poly_coords:
            print(f"[Info] Constructing Overpass query using Tecate municipal polygon boundary...")
            # Sample every 2nd coordinate to keep query compact and 100% safe
            sampled = poly_coords[::2]
            if sampled[-1] != poly_coords[-1]:
                sampled.append(poly_coords[-1])
            # GeoJSON coordinates are [longitude, latitude], Overpass expects latitude longitude
            poly_str = " ".join([f"{pt[1]:.6f} {pt[0]:.6f}" for pt in sampled])
            
            query = f"""[out:json][timeout:60];
(
  way["highway"~"motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link|residential|unclassified|service|living_street"](poly:"{poly_str}");
);
out body;
>;
out skel qt;"""
        else:
            print(f"[Warning] Falling back to default bounding box rectangular query...")
            query = f"""[out:json][timeout:30];
(
  way["highway"~"motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link|residential|unclassified|service|living_street"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
);
out body;
>;
out skel qt;"""
        
        headers = {
            "User-Agent": "TecateSimulatorReconstructor/1.0 (contact: hakkindavid@github)"
        }
        
        try:
            print("[Info] Requesting road data from OpenStreetMap Overpass API...")
            resp = requests.post(overpass_url, data={"data": query}, headers=headers, timeout=60)
            if resp.status_code == 200:
                elements = resp.json().get("elements", [])
                
                # Parse nodes and ways
                osm_nodes = {}
                ways = []
                for el in elements:
                    if el["type"] == "node":
                        osm_nodes[str(el["id"])] = {"lat": el["lat"], "lon": el["lon"]}
                    elif el["type"] == "way":
                        ways.append(el)
                        
                # Convert to our clean nodes/edges structure
                nodes = {}
                edges = []
                edge_counter = 0
                
                for w in ways:
                    w_nodes = w.get("nodes", [])
                    w_name = w.get("tags", {}).get("name", f"Street_{w['id']}")
                    for i in range(len(w_nodes) - 1):
                        u_id = str(w_nodes[i])
                        v_id = str(w_nodes[i+1])
                        
                        if u_id in osm_nodes and v_id in osm_nodes:
                            nodes[u_id] = {"id": u_id, "lat": osm_nodes[u_id]["lat"], "lon": osm_nodes[u_id]["lon"], "name": ""}
                            nodes[v_id] = {"id": v_id, "lat": osm_nodes[v_id]["lat"], "lon": osm_nodes[v_id]["lon"], "name": ""}
                            
                            edges.append({
                                "id": f"e_{edge_counter}",
                                "u": u_id,
                                "v": v_id,
                                "name": w_name
                            })
                            edge_counter += 1
                            
                if len(nodes) > 0:
                    data = {"nodes": nodes, "edges": edges}
                    with open(self.cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4)
                    print(f"[Info] Downloaded road network and saved cache to {self.cache_file}")
                    return data
                    
            print(f"[Warning] Overpass API response empty or invalid (Status: {resp.status_code}). Falling back...")
        except Exception as e:
            print(f"[Warning] Failed to fetch data from OSM Overpass: {e}")
            
        return self.generate_default_tecate_grid()

    def build_networkx_graph(self, raw_data: dict) -> nx.MultiGraph:
        """
        Builds a NetworkX graph with metric coordinates (x, y) relative to Tecate center.
        """
        G = nx.MultiGraph()
        
        # Add nodes
        for node_id, nd in raw_data["nodes"].items():
            x, y = gps_to_local(nd["lat"], nd["lon"])
            G.add_node(
                node_id, 
                lat=nd["lat"], 
                lon=nd["lon"], 
                x=x, 
                y=y, 
                name=nd.get("name", "")
            )
            
        # Add edges
        for ed in raw_data["edges"]:
            u, v = ed["u"], ed["v"]
            # Retrieve node coordinates to compute edge length in meters
            x1, y1 = G.nodes[u]["x"], G.nodes[u]["y"]
            x2, y2 = G.nodes[v]["x"], G.nodes[v]["y"]
            length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            
            G.add_edge(
                u, v, 
                id=ed["id"], 
                name=ed["name"], 
                length=length
            )
            
        return G

    def normalize_and_sample_edges(self, G: nx.MultiGraph, interval_meters: float = 10.0) -> list[dict]:
        """
        Normalizes street segments into regular sampling intervals.
        Generates virtual camera stations along each edge oriented along and orthogonal to the street.
        """
        camera_stations = []
        station_id_counter = 0
        
        for u, v, key, data in G.edges(keys=True, data=True):
            edge_id = data["id"]
            x1, y1 = G.nodes[u]["x"], G.nodes[u]["y"]
            x2, y2 = G.nodes[v]["x"], G.nodes[v]["y"]
            length = data["length"]
            
            # Divide edge into increments
            num_steps = int(max(1, math.floor(length / interval_meters)))
            steps = np.linspace(0, 1, num_steps + 1)
            
            # Heading of the road segment (in degrees from x-axis)
            dx = x2 - x1
            dy = y2 - y1
            road_heading_rad = math.atan2(dy, dx)
            road_heading_deg = math.degrees(road_heading_rad)
            
            for t in steps[1:-1]:  # Skip starting and ending nodes to avoid duplicates at intersections
                cx = x1 + t * dx
                cy = y1 + t * dy
                dist_along = t * length
                
                # Reverse translate back to lat/lon for metadata conformity
                clat, clon = local_to_gps(cx, cy)
                
                # Each position has 4 viewpoint directions:
                # 0 = Forward along road, 90 = Right, 180 = Backward, 270 = Left
                # These are extremely useful for our camera stitching and block boundary projections!
                camera_stations.append({
                    "station_id": f"cam_{station_id_counter}",
                    "edge_id": edge_id,
                    "dist_along": dist_along,
                    "x": cx,
                    "y": cy,
                    "latitude": clat,
                    "longitude": clon,
                    "road_heading": road_heading_deg,
                    "keypoints": []
                })
                station_id_counter += 1
                
        return camera_stations
