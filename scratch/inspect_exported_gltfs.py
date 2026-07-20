import json
import os
import glob

gltf_files = glob.glob("godot_project/assets/blocks/manzanas/*.gltf")
print(f"Total exported GLTF files found: {len(gltf_files)}")

if gltf_files:
    sample_file = gltf_files[0]
    print(f"Inspecting sample GLTF: {sample_file}")
    with open(sample_file, "r") as f:
        gltf = json.load(f)
    print("GLTF Keys:", list(gltf.keys()))
    if "nodes" in gltf:
        print(f"Nodes count: {len(gltf['nodes'])}")
        for n in gltf['nodes'][:5]:
            print("  Node:", n)
    if "meshes" in gltf:
        print(f"Meshes count: {len(gltf['meshes'])}")

print("\n--- Inspecting manzana_manifest.json ---")
manifest_path = "godot_project/assets/blocks/manzana_manifest.json"
if os.path.exists(manifest_path):
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    print(f"Manifest entry count: {len(manifest)}")
    sample_key = list(manifest.keys())[0]
    print(f"Sample entry '{sample_key}':")
    print(json.dumps(manifest[sample_key], indent=2))
