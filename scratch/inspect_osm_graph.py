import json

with open("data/tecate_osm_cache.json", "r") as f:
    osm_data = json.load(f)

nodes = osm_data.get("nodes", {})
print("Nodes count:", len(nodes))
sample_node_keys = list(nodes.keys())[:5]
for k in sample_node_keys:
    print(k, nodes[k])

edges = osm_data.get("edges", {})
print("Edges count:", len(edges))
sample_edge_keys = list(edges.keys())[:5]
for k in sample_edge_keys:
    print(k, edges[k])
