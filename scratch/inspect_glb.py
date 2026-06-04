import json
import struct
import numpy as np

def inspect_glb_vertices(glb_path):
    with open(glb_path, "rb") as f:
        header = f.read(12)
        magic, version, length = struct.unpack("<4sII", header)
        
        chunk_header = f.read(8)
        chunk_len, chunk_type = struct.unpack("<II", chunk_header)
        json_data = f.read(chunk_len).decode("utf-8")
        gltf = json.loads(json_data)
        
        chunk_header2 = f.read(8)
        chunk_len2, chunk_type2 = struct.unpack("<II", chunk_header2)
        bin_data = f.read(chunk_len2)
        
    print("=== MESH DETAILS ===")
    for mesh_idx, mesh in enumerate(gltf.get("meshes", [])):
        print(f"\nMesh {mesh_idx}: {mesh.get('name')}")
        for prim_idx, prim in enumerate(mesh.get("primitives", [])):
            attrs = prim.get("attributes", {})
            pos_idx = attrs.get("POSITION")
            if pos_idx is None:
                continue
                
            accessor = gltf["accessors"][pos_idx]
            bv = gltf["bufferViews"][accessor["bufferView"]]
            
            offset = bv.get("byteOffset", 0) + accessor.get("byteOffset", 0)
            count = accessor["count"]
            
            print(f"  Primitive {prim_idx}: Position accessor index {pos_idx}, count {count}")
            
            verts = []
            if accessor.get("componentType") == 5126 and accessor.get("type") == "VEC3":
                for idx in range(min(count, 5)):
                    x, y, z = struct.unpack_from("<fff", bin_data, offset + idx * 12)
                    verts.append((x, y, z))
                print(f"  First 5 verts: {verts}")
                
                # Check min/max
                all_verts = []
                for idx in range(count):
                    x, y, z = struct.unpack_from("<fff", bin_data, offset + idx * 12)
                    all_verts.append((x, y, z))
                all_verts = np.array(all_verts)
                print(f"  Min coordinates: {all_verts.min(axis=0)}")
                print(f"  Max coordinates: {all_verts.max(axis=0)}")
                print(f"  Centroid: {all_verts.mean(axis=0)}")

if __name__ == "__main__":
    inspect_glb_vertices("export/case_study/target_block.glb")
