import json

with open("data/tecate_osm_cache.json", "r") as f:
    osm_data = json.load(f)

edges = osm_data.get("edges")
print("Edges type:", type(edges))

if isinstance(edges, dict):
    print("Edges count (dict):", len(edges))
    k1 = list(edges.keys())[0]
    print("Sample edge item:", k1, edges[k1])
elif isinstance(edges, list):
    print("Edges count (list):", len(edges))
    print("Sample edge item:", edges[0])

