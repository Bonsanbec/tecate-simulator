import json
import os
import requests

def test_polygon_download():
    polygon_path = "reference/tecate-polygon.json"
    if not os.path.exists(polygon_path):
        print(f"Error: {polygon_path} not found.")
        return
        
    with open(polygon_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    features = data.get("features", [])
    if not features:
        return
        
    geometry = features[0].get("geometry", {})
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates", [])
    
    # Extract linear ring
    ring = []
    if geom_type == "Polygon":
        ring = coords[0]
    elif geom_type == "MultiPolygon":
        ring = coords[0][0]
        
    # Sample every 2nd vertex to keep Overpass query compact
    sampled_ring = ring[::2]
    if sampled_ring[-1] != ring[-1]:
        sampled_ring.append(ring[-1])
        
    # Format for Overpass: latitude longitude
    poly_str = " ".join([f"{pt[1]:.6f} {pt[0]:.6f}" for pt in sampled_ring])
    
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""[out:json][timeout:60];
(
  way["highway"~"motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link|residential|unclassified|service|living_street"](poly:"{poly_str}");
);
out body;
>;
out skel qt;"""
    
    headers = {
        "User-Agent": "TecateSimulatorReconstructor/1.0 (contact: hakkindavid@github)"
    }
    
    print(f"Sending Overpass query with {len(sampled_ring)} polygon vertices...")
    try:
        resp = requests.post(overpass_url, data={"data": query}, headers=headers, timeout=60)
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
                    
            print(f"Successfully downloaded road network inside polygon!")
            print(f"Nodes: {len(osm_nodes)}, Ways: {len(ways)}")
            
            # Check a few street names
            names = set()
            for w in ways:
                name = w.get("tags", {}).get("name")
                if name:
                    names.add(name)
            print(f"Unique street names found: {len(names)}")
            print(f"Sample street names: {list(names)[:10]}")
        else:
            print(f"Overpass failed with status code {resp.status_code}")
            print(resp.text[:500])
    except Exception as e:
        print(f"Failed to fetch data: {e}")

if __name__ == "__main__":
    test_polygon_download()
