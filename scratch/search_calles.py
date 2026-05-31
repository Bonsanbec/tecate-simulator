import json

with open("data/tecate_osm_cache.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for edge in data["edges"]:
    name = edge.get("name", "")
    if "calles" in name.lower():
        u_node = data["nodes"][edge["u"]]
        v_node = data["nodes"][edge["v"]]
        print(f"  Edge {edge['id']}: name='{edge['name']}', u=({u_node['lat']:.6f}, {u_node['lon']:.6f}), v=({v_node['lat']:.6f}, {v_node['lon']:.6f})")
