import json
import math
import networkx as nx

# Reference center point for Tecate: Parque Hidalgo
TECATE_LAT_CENTER = 32.573229
TECATE_LON_CENTER = -116.626536
EARTH_RADIUS = 6378137.0

def gps_to_local(lat: float, lon: float) -> tuple[float, float]:
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    lat_c_rad = math.radians(TECATE_LAT_CENTER)
    lon_c_rad = math.radians(TECATE_LON_CENTER)
    dx = EARTH_RADIUS * (lon_rad - lon_c_rad) * math.cos(lat_c_rad)
    dy = EARTH_RADIUS * (lat_rad - lat_c_rad)
    return dx, dy

import requests

def test_filter():
    polygon_path = "reference/tecate-polygon.json"
    with open(polygon_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    features = data.get("features", [])
    geometry = features[0].get("geometry", {})
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates", [])
    ring = coords[0] if geom_type == "Polygon" else coords[0][0]
    sampled_ring = ring[::2]
    if sampled_ring[-1] != ring[-1]:
        sampled_ring.append(ring[-1])
    poly_str = " ".join([f"{pt[1]:.6f} {pt[0]:.6f}" for pt in sampled_ring])
    
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""[out:json][timeout:60];
(
  way["highway"~"motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link|residential|unclassified|service|living_street"](poly:"{poly_str}");
);
out body;
>;
out skel qt;"""
    
    headers = {"User-Agent": "TecateSimulatorReconstructor/1.0"}
    print("Fetching roads...")
    resp = requests.post(overpass_url, data={"data": query}, headers=headers, timeout=60)
    elements = resp.json().get("elements", [])
    
    osm_nodes = {}
    ways = []
    for el in elements:
        if el["type"] == "node":
            # Store keys as strings for uniform matching
            osm_nodes[str(el["id"])] = {"lat": el["lat"], "lon": el["lon"]}
        elif el["type"] == "way":
            ways.append(el)
            
    print(f"Downloaded Nodes: {len(osm_nodes)}, Ways: {len(ways)}")
    
    # Filter nodes within 7.0 km of Parque Hidalgo
    filtered_nodes = {}
    for nid, node in osm_nodes.items():
        dx, dy = gps_to_local(node["lat"], node["lon"])
        dist = math.sqrt(dx**2 + dy**2)
        if dist <= 7000.0:
            filtered_nodes[str(nid)] = {"lat": node["lat"], "lon": node["lon"], "x": dx, "y": dy}
            
    print(f"Nodes within 7.0 km: {len(filtered_nodes)}")
    
    # Filter edges
    filtered_edges = []
    for w in ways:
        w_nodes = w.get("nodes", [])
        w_name = w.get("tags", {}).get("name", f"Street_{w['id']}")
        for i in range(len(w_nodes) - 1):
            u = str(w_nodes[i])
            v = str(w_nodes[i+1])
            if u in filtered_nodes and v in filtered_nodes:
                filtered_edges.append((u, v, w_name))
                
    print(f"Edges within 7.0 km: {len(filtered_edges)}")
    
if __name__ == "__main__":
    test_filter()
