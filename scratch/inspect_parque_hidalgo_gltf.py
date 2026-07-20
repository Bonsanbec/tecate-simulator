import json

gltf_file = "godot_project/assets/blocks/manzanas/block_lat_32.57293_lon_-116.62685.gltf"
with open(gltf_file, "r") as f:
    gltf = json.load(f)

print(f"Inspecting {gltf_file}:")
print("Nodes:")
for n in gltf.get("nodes", []):
    print("  Node name:", n.get("name"))
    print("    translation:", n.get("translation"))
    print("    rotation:", n.get("rotation"))
    print("    scale:", n.get("scale"))
    print("    mesh:", n.get("mesh"))

