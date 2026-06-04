import bpy
import json
import os
import sys

# Append tecate-simulator root to sys.path so we can import helper modules
sys.path.append("/Users/hakkindavid/Documents/GitHub/tecate-simulator")

from blender_script import clear_scene, build_block_meshes, setup_lighting_and_camera, configure_gpu_acceleration

def run():
    print("[Blender Subprocess] Starting case study assembly...")
    with open("/Users/hakkindavid/Documents/GitHub/tecate-simulator/export/case_study/target_block_scene.json", "r", encoding="utf-8") as f_in:
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
