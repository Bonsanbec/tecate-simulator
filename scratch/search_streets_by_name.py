import json

with open("data/tecate_osm_cache.json", "r", encoding="utf-8") as f:
    data = json.load(f)

search_terms = ["juarez", "libertad", "revolucion", "tamesis", "támesis"]

for term in search_terms:
    print(f"\nSearching for '{term}':")
    matches = 0
    for edge in data["edges"]:
        name = edge.get("name", "").lower()
        if term in name:
            u_node = data["nodes"][edge["u"]]
            v_node = data["nodes"][edge["v"]]
            print(f"  Edge {edge['id']}: name='{edge['name']}', u=({u_node['lat']:.6f}, {u_node['lon']:.6f}), v=({v_node['lat']:.6f}, {v_node['lon']:.6f})")
            matches += 1
    print(f"Found {matches} matches.")
