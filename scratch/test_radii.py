import json
import math

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

def test_radii():
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
            osm_nodes[str(el["id"])] = {"lat": el["lat"], "lon": el["lon"]}
        elif el["type"] == "way":
            ways.append(el)
            
    print(f"Downloaded Nodes: {len(osm_nodes)}, Ways: {len(ways)}")
    
    # Calculate distances
    node_dists = {}
    for nid, node in osm_nodes.items():
        dx, dy = gps_to_local(node["lat"], node["lon"])
        dist = math.sqrt(dx**2 + dy**2)
        node_dists[nid] = dist
        
    radii = [1000.0, 1500.0, 2000.0, 2500.0, 3000.0, 4000.0, 5000.0]
    for r in radii:
        n_count = sum(1 for nid, d in node_dists.items() if d <= r)
        
        # Filter edges
        e_count = 0
        for w in ways:
            w_nodes = w.get("nodes", [])
            for i in range(len(w_nodes) - 1):
                u = str(w_nodes[i])
                v = str(w_nodes[i+1])
                if u in node_dists and v in node_dists:
                    if node_dists[u] <= r and node_dists[v] <= r:
                        e_count += 1
                        
        print(f"Radius {r/1000.0:.1f} km: Nodes={n_count}, Edges={e_count}")

if __name__ == "__main__":
    test_radii()
