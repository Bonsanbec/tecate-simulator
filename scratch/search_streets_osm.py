import json
import math

def search():
    target_lat = 32.573484
    target_lon = -116.627276
    
    with open("data/tecate_osm_cache.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print("Nodes within 100 meters of Bancomer:")
    close_nodes = {}
    for nid, node in data["nodes"].items():
        lat = node["lat"]
        lon = node["lon"]
        # Compute distance in meters (approx)
        d_lat = (lat - target_lat) * 111000
        d_lon = (lon - target_lon) * 111000 * math.cos(math.radians(target_lat))
        dist = math.sqrt(d_lat**2 + d_lon**2)
        if dist < 100:
            print(f"  Node {nid}: lat={lat:.6f}, lon={lon:.6f}, dist={dist:.1f}m, name='{node['name']}'")
            close_nodes[nid] = dist
            
    print("\nEdges within 100 meters of Bancomer:")
    for edge in data["edges"]:
        u = edge["u"]
        v = edge["v"]
        if u in close_nodes or v in close_nodes:
            # Get node coordinates
            unode = data["nodes"][u]
            vnode = data["nodes"][v]
            print(f"  Edge {edge['id']}: u={u} ({unode['lat']:.6f}, {unode['lon']:.6f}) -> v={v} ({vnode['lat']:.6f}, {vnode['lon']:.6f}), name='{edge['name']}'")

if __name__ == "__main__":
    search()
