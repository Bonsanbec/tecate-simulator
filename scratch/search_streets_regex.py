import json

with open("data/tecate_osm_cache.json", "r", encoding="utf-8") as f:
    data = json.load(f)

keywords = ["benito", "juarez", "juárez", "revol", "tamesis", "támesis"]

for kw in keywords:
    print(f"\nSearching for '{kw}':")
    matched_names = set()
    for edge in data["edges"]:
        name = edge.get("name", "")
        if kw.lower() in name.lower():
            matched_names.add(name)
    print(f"Matched names: {matched_names}")
