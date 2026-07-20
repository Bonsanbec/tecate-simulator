import json

with open("data/tecate_osm_cache.json", "r") as f:
    osm_data = json.load(f)

edges = osm_data.get("edges", [])
print(f"Edges list count: {len(edges)}")
named_edges = 0
for e in edges:
    if isinstance(e, dict) and e.get("name"):
        named_edges += 1
        if named_edges <= 10:
            print(" Edge with name:", e.get("name"), "highway:", e.get("highway"), "bridge:", e.get("bridge"), "railway:", e.get("railway"))

print(f"Total named edges: {named_edges}")

print("\n--- Inspecting blocks_cache.json ---")
with open("data/blocks_cache.json", "r") as f:
    blocks_data = json.load(f)

print("Blocks count:", len(blocks_data))
named_blocks = 0
for bid, binfo in blocks_data.items():
    if isinstance(binfo, dict):
        keys = list(binfo.keys())
        if "name" in binfo or "label" in binfo or "building" in binfo or "amenity" in binfo:
            named_blocks += 1
            if named_blocks <= 10:
                print(" Block info:", bid, binfo)

print("Sample Block Keys:", list(list(blocks_data.values())[0].keys()) if blocks_data else [])

