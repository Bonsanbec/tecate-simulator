import json
import math
import sys
import os

sys.path.append(os.path.abspath("scripts"))
from spatial import gps_to_local

# Load tecate_osm_cache.json edges
with open("data/tecate_osm_cache.json", "r") as f:
    osm_data = json.load(f)

nodes = osm_data.get("nodes", {})
edges = osm_data.get("edges", [])

road_segments = []
for e in edges:
    if isinstance(e, dict) and e.get("name"):
        u_id = str(e.get("u"))
        v_id = str(e.get("v"))
        if u_id in nodes and v_id in nodes:
            u_node = nodes[u_id]
            v_node = nodes[v_id]
            
            ux, uy = gps_to_local(u_node["lat"], u_node["lon"])
            vx, vy = gps_to_local(v_node["lat"], v_node["lon"])
            
            road_segments.append({
                "name": e["name"],
                "p1": (ux, uy),
                "p2": (vx, vy),
                "mid": ((ux + vx) / 2.0, (uy + vy) / 2.0)
            })

print(f"Loaded {len(road_segments)} road segments with names!")

# Test finding nearest street for Parque Hidalgo (0, 0)
def get_nearest_street(x, y):
    best_dist = float('inf')
    best_name = "Tecate Center"
    for r in road_segments:
        mx, my = r["mid"]
        d = math.hypot(x - mx, y - my)
        if d < best_dist:
            best_dist = d
            best_name = r["name"]
    return best_name, best_dist

print("Parque Hidalgo (0,0) nearest street:", get_nearest_street(0, 0))

