import json

with open("data/tecate_osm_cache.json", "r") as f:
    osm_data = json.load(f)

print("OSM Data Keys:", list(osm_data.keys()) if isinstance(osm_data, dict) else type(osm_data))

elements = osm_data.get("elements", []) if isinstance(osm_data, dict) else osm_data
print(f"Total OSM elements: {len(elements)}")

named_elements = 0
named_buildings = 0
sample_named = []

for elem in elements:
    tags = elem.get("tags", {})
    if "name" in tags:
        named_elements += 1
        if "building" in tags or tags.get("amenity") or tags.get("shop") or tags.get("office"):
            named_buildings += 1
            if len(sample_named) < 15:
                sample_named.append(tags)

print(f"Named elements count: {named_elements}")
print(f"Named buildings/POIs count: {named_buildings}")
print("\nSample Named Buildings / POIs in Tecate:")
for s in sample_named:
    print(" ", s)
