import json
import math

with open("data/tecate_osm_cache.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Find all nodes on Revolución and Juárez
revolucion_nodes = []
for edge in data["edges"]:
    if "revolución" in edge.get("name", "").lower():
        revolucion_nodes.extend([edge["u"], edge["v"]])
revolucion_nodes = list(set(revolucion_nodes))

juarez_nodes = []
for edge in data["edges"]:
    if "juárez" in edge.get("name", "").lower():
        juarez_nodes.extend([edge["u"], edge["v"]])
juarez_nodes = list(set(juarez_nodes))

print(f"Revolución nodes count: {len(revolucion_nodes)}")
print(f"Juárez nodes count: {len(juarez_nodes)}")

# Compute closest pairs
min_dist = float("inf")
best_r = None
best_j = None

for rn in revolucion_nodes:
    r_node = data["nodes"][rn]
    for jn in juarez_nodes:
        j_node = data["nodes"][jn]
        # Distance in meters
        dy = (r_node["lat"] - j_node["lat"]) * 111000
        dx = (r_node["lon"] - j_node["lon"]) * 111000 * math.cos(math.radians(r_node["lat"]))
        dist = math.sqrt(dx**2 + dy**2)
        if dist < min_dist:
            min_dist = dist
            best_r = (rn, r_node)
            best_j = (jn, j_node)

print(f"\nClosest distance between Revolución and Juárez in graph: {min_dist:.2f} meters")
if best_r and best_j:
    print(f"  Revolución Node {best_r[0]}: ({best_r[1]['lat']:.6f}, {best_r[1]['lon']:.6f})")
    print(f"  Juárez Node {best_j[0]}: ({best_j[1]['lat']:.6f}, {best_j[1]['lon']:.6f})")
