import json
import os
import math
import subprocess

def main():
    json_path = 'export/reconstruction_export.json'
    if not os.path.exists(json_path):
        print(f"Error: {json_path} does not exist!")
        return
        
    print(f"Loading {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    blocks = data.get('blocks', [])
    print(f"Total blocks: {len(blocks)}")
    
    active_textures = set()
    active_block_ids = []
    
    for b in blocks:
        poly = b['polygon']
        num_verts = len(poly) - 1
        cx = sum(p[0] for p in poly[:-1]) / num_verts
        cy = sum(p[1] for p in poly[:-1]) / num_verts
        dist = math.sqrt(cx**2 + cy**2)
        
        # 150 meters radius
        if dist <= 150.0:
            active_block_ids.append(b['block_id'])
            for tex in b.get('facade_textures', {}).values():
                if tex and tex != 'untextured':
                    active_textures.add(os.path.basename(tex))
                    # Also add normal maps
                    norm = os.path.basename(tex).replace('.png', '_normal_height.png')
                    active_textures.add(norm)
                    
    print(f"Active blocks within 150m: {len(active_block_ids)}")
    print(f"Active textures to copy: {len(active_textures)}")
    
    # Save the list of textures
    txt_path = 'export/active_textures.txt'
    with open(txt_path, 'w', encoding='utf-8') as f:
        for t in sorted(list(active_textures)):
            f.write(t + '\n')
    print(f"Saved active texture list to {txt_path}")
    
    # Pack into a tarball
    # Files to pack:
    # export/geometry_textureless.gltf, export/geometry_textureless.bin
    # export/geometry.gltf, export/geometry.bin (if they exist)
    # and all the active textures from export/textures/
    tar_files = []
    for fn in ['geometry_textureless.gltf', 'geometry_textureless.bin', 'geometry.gltf', 'geometry.bin']:
        p = os.path.join('export', fn)
        if os.path.exists(p):
            tar_files.append(p)
            
    for t in active_textures:
        p = os.path.join('export/textures', t)
        if os.path.exists(p):
            tar_files.append(p)
        else:
            print(f"Warning: Texture {p} not found!")
            
    print(f"Packing {len(tar_files)} files...")
    # Write file list to a temp file
    list_path = 'export/pack_list.txt'
    with open(list_path, 'w', encoding='utf-8') as f:
        for tf in tar_files:
            f.write(tf + '\n')
            
    # Run tar
    tar_path = 'export/active_assets.tar.gz'
    # Use -T to read files from list_path
    cmd = f"tar -czf {tar_path} -T {list_path}"
    subprocess.run(cmd, shell=True, check=True)
    print(f"Successfully created tarball at {tar_path}")

if __name__ == '__main__':
    main()
