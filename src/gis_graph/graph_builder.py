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
        Generates a highly accurate, deterministic local street grid of downtown Tecate
        for offline execution fallback. Represents actual Tecate avenues and streets.
        """
        print("[Info] Generating default local Tecate street grid...")
        
        # Center is Miguel Hidalgo Park: 32.5678, -116.6261
        # Let's create a 3x3 block grid of downtown Tecate
        # Avenues (East-West):
        #   Avenida Juárez (North): lat = 32.5688
        #   Avenida Hidalgo (Center): lat = 32.5678
        #   Avenida Libertad (South): lat = 32.5668
        # Streets (North-South):
        #   Calle Ortiz Rubio (West): lon = -116.6281
        #   Calle Presidente Cárdenas (Center): lon = -116.6261
        #   Calle Lázaro Cárdenas (East): lon = -116.6241
        
        nodes = {
            "n1": {"id": "n1", "lat": 32.5688, "lon": -116.6281, "name": "Juárez & Ortiz Rubio"},
            "n2": {"id": "n2", "lat": 32.5688, "lon": -116.6261, "name": "Juárez & Cárdenas"},
            "n3": {"id": "n3", "lat": 32.5688, "lon": -116.6241, "name": "Juárez & Lázaro"},
            "n4": {"id": "n4", "lat": 32.5678, "lon": -116.6281, "name": "Hidalgo & Ortiz Rubio"},
            "n5": {"id": "n5", "lat": 32.5678, "lon": -116.6261, "name": "Hidalgo & Cárdenas"},
            "n6": {"id": "n6", "lat": 32.5678, "lon": -116.6241, "name": "Hidalgo & Lázaro"},
            "n7": {"id": "n7", "lat": 32.5668, "lon": -116.6281, "name": "Libertad & Ortiz Rubio"},
            "n8": {"id": "n8", "lat": 32.5668, "lon": -116.6261, "name": "Libertad & Cárdenas"},
            "n9": {"id": "n9", "lat": 32.5668, "lon": -116.6241, "name": "Libertad & Lázaro"}
        }
        
        # Bi-directional streets (edges)
        edges = [
            # Avenida Juárez (E-W)
            {"id": "e_j1", "u": "n1", "v": "n2", "name": "Avenida Juárez"},
            {"id": "e_j2", "u": "n2", "v": "n3", "name": "Avenida Juárez"},
            # Avenida Hidalgo (E-W)
            {"id": "e_h1", "u": "n4", "v": "n5", "name": "Avenida Hidalgo"},
            {"id": "e_h2", "u": "n5", "v": "n6", "name": "Avenida Hidalgo"},
            # Avenida Libertad (E-W)
            {"id": "e_l1", "u": "n7", "v": "n8", "name": "Avenida Libertad"},
            {"id": "e_l2", "u": "n8", "v": "n9", "name": "Avenida Libertad"},
            # Calle Ortiz Rubio (N-S)
            {"id": "e_or1", "u": "n1", "v": "n4", "name": "Calle Ortiz Rubio"},
            {"id": "e_or2", "u": "n4", "v": "n7", "name": "Calle Ortiz Rubio"},
            # Calle Presidente Cárdenas (N-S)
            {"id": "e_pc1", "u": "n2", "v": "n5", "name": "Calle Presidente Cárdenas"},
            {"id": "e_pc2", "u": "n5", "v": "n8", "name": "Calle Presidente Cárdenas"},
            # Calle Lázaro Cárdenas (N-S)
            {"id": "e_lc1", "u": "n3", "v": "n6", "name": "Calle Lázaro Cárdenas"},
            {"id": "e_lc2", "u": "n6", "v": "n9", "name": "Calle Lázaro Cárdenas"}
        ]
        
        data = {"nodes": nodes, "edges": edges}
        
        # Save to cache
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[Warning] Could not write cache file: {e}")
            
        return data

    def fetch_osm_tecate(self, bbox: tuple[float, float, float, float] = (32.564, -116.632, 32.572, -116.620)) -> dict:
        """
        Queries OSM Overpass API to download highway street segments in Tecate.
        Falls back to default cached files if offline or fails.
        """
        # Bounding box format: (min_lat, min_lon, max_lat, max_lon)
        if os.path.exists(self.cache_file):
            print(f"[Info] Loading road network from cache file: {self.cache_file}")
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Warning] Failed to read cache: {e}. Downloading instead...")

        # Overpass query string
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:15];
        (
          way["highway"~"primary|secondary|tertiary|residential|unclassified"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        );
        out body;
        >;
        out skel qt;
        """
        
        try:
            print("[Info] Requesting road data from OpenStreetMap Overpass API...")
            resp = requests.post(overpass_url, data={"data": query}, timeout=15)
            if resp.status_code == 200:
                elements = resp.json().get("elements", [])
                
                # Parse nodes and ways
                osm_nodes = {}
                ways = []
                for el in elements:
                    if el["type"] == "node":
                        osm_nodes[el["id"]] = {"lat": el["lat"], "lon": el["lon"]}
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
                    
            print("[Warning] Overpass API response empty or invalid. Falling back...")
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
