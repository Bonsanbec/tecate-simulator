import json
import os
import subprocess
import sys
from src.core_io.io_manager import ensure_dir

def main():
    print("[build_case_study_block] Preparing case study block scene document...")
    
    # 1. Load target facade details
    with open("data/case_study/target_facade.json", "r", encoding="utf-8") as f:
        target_facade = json.load(f)
    block_id = target_facade["block_id"]
    target_indices = target_facade["target_facade_indices"]
    
    # 2. Load the original block data from export/reconstruction_export.json
    with open("export/reconstruction_export.json", "r", encoding="utf-8") as f:
        export_data = json.load(f)
        
    target_block = None
    for block in export_data.get("blocks", []):
        if block["block_id"] == block_id:
            target_block = block
            break
            
    if not target_block:
        raise ValueError(f"Target block {block_id} not found in reconstruction_export.json!")
        
    # Copy block data to avoid modifying in-place
    block_copy = json.loads(json.dumps(target_block))
    
    # Use absolute or relative path for texture
    texture_rel_path = "export/case_study/target_facade_texture.png"
    texture_abs_path = os.path.abspath(texture_rel_path)
    
    # 3. Update facade textures and UV mappings for target segments
    K = len(target_indices)
    if "facade_textures" not in block_copy:
        block_copy["facade_textures"] = {}
    if "uv_mappings" not in block_copy:
        block_copy["uv_mappings"] = {}
        
    for i, idx in enumerate(target_indices):
        f_id = f"{block_id}_facade_{idx}"
        block_copy["facade_textures"][f_id] = texture_abs_path
        
        # Stitched UV mapping
        col_start = i / float(K)
        col_end = (i + 1) / float(K)
        block_copy["uv_mappings"][f_id] = [
            [col_start, 0.0],
            [col_end, 0.0],
            [col_end, 1.0],
            [col_start, 1.0]
        ]
        
    # 4. Save target_block_scene.json
    scene_doc = {
        "road_graph": {
            "nodes": [],
            "edges": []
        },
        "blocks": [block_copy]
    }
    
    ensure_dir("export/case_study")
    scene_json_path = "export/case_study/target_block_scene.json"
    with open(scene_json_path, "w", encoding="utf-8") as f:
        json.dump(scene_doc, f, indent=4)
    print(f"[build_case_study_block] Saved scene document to {scene_json_path}")
    
    # 5. Create a temporary Blender execution script
    blender_exec_script = "export/case_study/temp_blender_script.py"
    with open(blender_exec_script, "w", encoding="utf-8") as f:
        f.write(f"""import bpy
import json
import os
import sys

# Append tecate-simulator root to sys.path so we can import helper modules
sys.path.append("{os.path.abspath('.')}")

from blender_script import clear_scene, build_block_meshes, setup_lighting_and_camera, configure_gpu_acceleration

def run():
    print("[Blender Subprocess] Starting case study assembly...")
    with open("{os.path.abspath(scene_json_path)}", "r", encoding="utf-8") as f_in:
        scene = json.load(f_in)
        
    configure_gpu_acceleration()
    clear_scene()
    
    # Build geometry and apply textures
    build_block_meshes(scene.get("blocks", []), cull_fov=False)
    
    # Setup lighting and camera
    setup_lighting_and_camera()
    
    # Save the blend file
    blend_path = "export/case_study/target_block.blend"
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("[Blender Subprocess] Saved mainfile to:", blend_path)
    
    # Export fully textured GLB
    glb_path = "export/case_study/target_block.glb"
    print("[Blender Subprocess] Exporting to GLB:", glb_path)
    try:
        bpy.ops.export_scene.gltf(
            filepath=glb_path,
            export_format='GLB',
            export_copyright="Tecate Simulator Case Study",
            export_texcoords=True,
            export_normals=True,
            export_materials='EXPORT',
            export_image_format='AUTO',
            use_selection=False
        )
        print("[Blender Subprocess] GLB Export Successful!")
    except Exception as e:
        print("[Blender Subprocess Error] GLB Export failed:", e)
        sys.exit(1)

if __name__ == '__main__':
    run()
""")
        
    print("[build_case_study_block] Temporary Blender execution script created.")
    
    # 6. Locate Blender executable
    blender_path = "blender"
    mac_paths = [
        "/Applications/Blender.app/Contents/MacOS/Blender",
        "/Applications/Blender.app/Contents/MacOS/blender",
        os.path.expanduser("~/Applications/Blender.app/Contents/MacOS/Blender")
    ]
    for path in mac_paths:
        if os.path.exists(path):
            blender_path = path
            break
            
    print(f"[build_case_study_block] Launching Blender: '{blender_path}'...")
    cmd = [
        blender_path,
        "--background",
        "--python",
        blender_exec_script
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    print(res.stderr)
    
    if res.returncode == 0:
        print("[build_case_study_block] Successfully compiled target_block.glb and target_block.blend!")
    else:
        print(f"[Error] Blender execution failed with return code {res.returncode}")
        sys.exit(1)
        
if __name__ == "__main__":
    main()
