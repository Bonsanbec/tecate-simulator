import json

with open("scratch/osm_test.json", "r") as f:
    data = json.load(f)

elements = data.get("elements", [])

# Parse nodes and ways
osm_nodes = {}
ways = []
for el in elements:
    if el["type"] == "node":
        osm_nodes[el["id"]] = {"lat": el["lat"], "lon": el["lon"]}
    elif el["type"] == "way":
        ways.append(el)
        
# Convert to clean format
nodes = {}
edges = []
edge_counter = 0

for w in ways:
    w_nodes = w.get("nodes", [])
    w_name = w.get("tags", {}).get("name", f"Street_{w['id']}")
    for i in range(len(w_nodes) - 1):
        u_id = w_nodes[i]
        v_id = w_nodes[i+1]
        
        if u_id in osm_nodes and v_id in osm_nodes:
            u_str = str(u_id)
            v_str = str(v_id)
            nodes[u_str] = {"id": u_str, "lat": osm_nodes[u_id]["lat"], "lon": osm_nodes[u_id]["lon"], "name": ""}
            nodes[v_str] = {"id": v_str, "lat": osm_nodes[v_id]["lat"], "lon": osm_nodes[v_id]["lon"], "name": ""}
            
            edges.append({
                "id": f"e_{edge_counter}",
                "u": u_str,
                "v": v_str,
                "name": w_name
            })
            edge_counter += 1

out_data = {"nodes": nodes, "edges": edges}
with open("data/tecate_osm_cache.json", "w") as f:
    json.dump(out_data, f, indent=4)

print(f"Successfully converted and saved {len(nodes)} nodes and {len(edges)} edges to data/tecate_osm_cache.json.")
