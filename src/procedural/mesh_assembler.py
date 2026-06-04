# Purpose: Assembles detailed 3D facade mesh with procedural elements (windows, doors, cornices) using Blender.
# Inputs: element_detection_report.json, target_block_scene.json, facades_cache.json.
# Outputs: export/case_study/detailed_facade.glb.
# Responsibilities: Generates a Blender script to build detailed components, executes Blender in headless mode, and saves the detailed GLB.
# Dependencies: os, sys, json, subprocess, numpy

import os
import sys
import json
import subprocess
import numpy as np

class ProceduralMeshAssembler:
    """
    Assembles the final detailed 3D model of the building block with procedural elements.
    Generates a custom Blender Python script to create 3D window frames, recessed window panes,
    doors, and roof cornices, merges them with the base prism block, and exports the detailed GLB.
    """
    def __init__(self, data_dir: str = "data", export_dir: str = "export"):
        self.data_dir = data_dir
        self.export_dir = export_dir

    def assemble(self) -> str:
        """
        Runs the Blender compilation pipeline to generate export/case_study/detailed_facade.glb.
        """
        print("[ProceduralMeshAssembler] Preparing Detailed Facade compilation...")
        
        report_path = os.path.join(self.export_dir, "case_study", "element_detection_report.json")
        scene_json_path = os.path.join(self.export_dir, "case_study", "target_block_scene.json")
        facades_cache_path = os.path.join(self.data_dir, "facades_cache.json")
        
        if not os.path.exists(report_path):
            raise FileNotFoundError(f"Element detection report not found: {report_path}")
        if not os.path.exists(scene_json_path):
            raise FileNotFoundError(f"Base block scene document not found: {scene_json_path}")
            
        # Create a temporary Blender compilation script
        blender_exec_script = os.path.join(self.export_dir, "case_study", "temp_blender_detailed_script.py")
        os.makedirs(os.path.dirname(blender_exec_script), exist_ok=True)
        
        with open(blender_exec_script, "w", encoding="utf-8") as f:
            f.write(f"""import bpy
import json
import os
import sys
import math
import numpy as np

# Append tecate-simulator root to sys.path
sys.path.append("{os.path.abspath('.')}")

from blender_script import clear_scene, build_block_meshes, setup_lighting_and_camera, configure_gpu_acceleration

def run():
    print("[Blender Detailed Assembly] Starting detailed assembly...")
    
    # 1. Load scene and report data
    with open("{os.path.abspath(scene_json_path)}", "r", encoding="utf-8") as f_in:
        scene = json.load(f_in)
    with open("{os.path.abspath(report_path)}", "r", encoding="utf-8") as f_in:
        report = json.load(f_in)
    with open("{os.path.abspath(facades_cache_path)}", "r", encoding="utf-8") as f_in:
        facades_cache = json.load(f_in)
        
    configure_gpu_acceleration()
    clear_scene()
    
    # 2. Build base block geometry and apply texture
    build_block_meshes(scene.get("blocks", []), cull_fov=False)
    
    # 3. Create materials for procedural elements
    # Dark charcoal window/door frame material
    mat_frame = bpy.data.materials.new(name="mat_procedural_frame")
    mat_frame.use_nodes = True
    bsdf = mat_frame.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.15, 0.15, 0.15, 1.0)
        bsdf.inputs['Metallic'].default_value = 0.5
        bsdf.inputs['Roughness'].default_value = 0.4
        
    # Blue glossy glass material
    mat_glass = bpy.data.materials.new(name="mat_procedural_glass")
    mat_glass.use_nodes = True
    bsdf = mat_glass.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.05, 0.1, 0.2, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.1
        bsdf.inputs['Specular IOR Level'].default_value = 0.5
        
    # Stone/concrete cornice material (matching untextured stucco cream color)
    mat_cornice = bpy.data.materials.new(name="mat_procedural_cornice")
    mat_cornice.use_nodes = True
    bsdf = mat_cornice.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.8, 0.75, 0.7, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.8
        
    detailed_objects = []
    
    # 4. Generate 3D elements (Windows & Doors)
    elements = report.get("elements", [])
    print(f"[Blender Detailed Assembly] Adding {{len(elements)}} procedural elements...")
    
    for idx, elem in enumerate(elements):
        f_id = elem["facade_id"]
        f_data = facades_cache.get(f_id)
        if not f_data:
            continue
            
        # Get facade segment coordinates and orientation
        verts = f_data["facade_segment_vertices_local"]
        A = np.array(verts[0])
        B = np.array(verts[1])
        D = B - A
        L = np.linalg.norm(D)
        u_dir = D / L
        
        # Facade normal vector (3D unit vector)
        n_dir_2d = f_data["camera_alignment_diagnostics"]["facade_normal"]
        n_dir = np.array([n_dir_2d[0], n_dir_2d[1], 0.0])
        
        # Calculate horizontal bounds
        u_start = elem["u_start"]
        u_end = elem["u_end"]
        u_mid = (u_start + u_end) / 2.0
        w_elem = (u_end - u_start) * L
        
        # Calculate vertical bounds
        z_start = elem["z_start"]
        z_end = elem["z_end"]
        z_mid = (z_start + z_end) / 2.0
        h_elem = z_end - z_start
        
        # 3D surface center location
        c_surf = np.array([A[0] + u_mid * D[0], A[1] + u_mid * D[1], z_mid])
        
        elem_type = elem["type"]
        if elem_type == "window":
            # Windows are recessed
            d_elem = 0.15 # depth of window frame/casing
            # Shift center slightly inward along normal
            c_loc = c_surf - (d_elem / 2.0) * n_dir
            
            # Create Window Frame (Outer Box)
            bpy.ops.mesh.primitive_cube_add(size=1.0)
            frame_obj = bpy.context.active_object
            frame_obj.name = f"Window_Frame_{{f_id}}_{{idx}}"
            frame_obj.scale = (d_elem, w_elem, h_elem)
            frame_obj.rotation_euler = (0.0, 0.0, math.atan2(u_dir[1], u_dir[0]))
            frame_obj.location = tuple(c_loc)
            frame_obj.data.materials.append(mat_frame)
            detailed_objects.append(frame_obj)
            
            # Create Window Glass (Inner Box, slightly smaller and further recessed)
            bpy.ops.mesh.primitive_cube_add(size=1.0)
            glass_obj = bpy.context.active_object
            glass_obj.name = f"Window_Glass_{{f_id}}_{{idx}}"
            # Slightly smaller than frame horizontally and vertically, thinner depthwise
            glass_obj.scale = (d_elem * 0.4, w_elem * 0.85, h_elem * 0.85)
            glass_obj.rotation_euler = (0.0, 0.0, math.atan2(u_dir[1], u_dir[0]))
            # Recess further inward
            glass_loc = c_loc - (d_elem * 0.2) * n_dir
            glass_obj.location = tuple(glass_loc)
            glass_obj.data.materials.append(mat_glass)
            detailed_objects.append(glass_obj)
            
        elif elem_type == "door":
            # Doors are recessed at ground level
            d_elem = 0.12 # depth
            c_loc = c_surf - (d_elem / 2.0) * n_dir
            
            # Create Door Box
            bpy.ops.mesh.primitive_cube_add(size=1.0)
            door_obj = bpy.context.active_object
            door_obj.name = f"Door_{{f_id}}_{{idx}}"
            door_obj.scale = (d_elem, w_elem, h_elem)
            door_obj.rotation_euler = (0.0, 0.0, math.atan2(u_dir[1], u_dir[0]))
            door_obj.location = tuple(c_loc)
            door_obj.data.materials.append(mat_frame)
            detailed_objects.append(door_obj)
            
    # 5. Generate Roof Cornices
    # Add a horizontal projecting box along the top of each target facade segment
    print("[Blender Detailed Assembly] Adding horizontal roof cornices...")
    block = scene.get("blocks", [])[0]
    height_block = block["height_meters"]
    target_indices = report.get("target_facade_indices", [])
    block_id = report.get("block_id", "")
    
    for idx in target_indices:
        f_id = f"{{block_id}}_facade_{{idx}}"
        f_data = facades_cache.get(f_id)
        if not f_data:
            continue
            
        verts = f_data["facade_segment_vertices_local"]
        A = np.array(verts[0])
        B = np.array(verts[1])
        D = B - A
        L = np.linalg.norm(D)
        u_dir = D / L
        n_dir_2d = f_data["camera_alignment_diagnostics"]["facade_normal"]
        n_dir = np.array([n_dir_2d[0], n_dir_2d[1], 0.0])
        
        # Cornice dimensions
        d_cornice = 0.35 # depth (width pointing outward)
        h_cornice = 0.20 # thickness vertically
        w_cornice = L    # horizontal width
        
        # Center of cornice: top edge of segment wall
        # We shift it outward slightly so it overhangs the street
        c_surf = np.array([A[0] + 0.5 * D[0], A[1] + 0.5 * D[1], height_block - h_cornice/2.0])
        c_loc = c_surf + (0.25 - d_cornice/2.0) * n_dir
        
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        cornice_obj = bpy.context.active_object
        cornice_obj.name = f"Cornice_{{f_id}}"
        cornice_obj.scale = (d_cornice, w_cornice, h_cornice)
        cornice_obj.rotation_euler = (0.0, 0.0, math.atan2(u_dir[1], u_dir[0]))
        cornice_obj.location = tuple(c_loc)
        cornice_obj.data.materials.append(mat_cornice)
        detailed_objects.append(cornice_obj)
        
    # 6. Merge/Join all objects together into the detailed building representation
    # Select all newly created detailed objects and the base block objects
    bpy.ops.object.select_all(action='DESELECT')
    
    # We want to select the base facade mesh (if it exists) and our detailed components
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
            
    # Set the active object to the first selected mesh
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    if meshes:
        bpy.context.view_layer.objects.active = meshes[0]
        # Apply location, rotation, and scale transforms first to prevent distortion when joining
        try:
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            print("[Blender Detailed Assembly] Applied transforms to all meshes successfully.")
        except Exception as e:
            print("[Blender Detailed Assembly Warning] Could not apply transforms:", e)
            
        # Join into a single mesh object (retains multiple materials)
        try:
            bpy.ops.object.join()
            print("[Blender Detailed Assembly] Joined all mesh parts successfully.")
        except Exception as e:
            print("[Blender Detailed Assembly Warning] Could not join meshes:", e)
            
    # Setup lighting and camera
    setup_lighting_and_camera()
    
    # Save the blend file
    blend_path = "export/case_study/detailed_facade.blend"
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("[Blender Detailed Assembly] Saved detailed blend file to:", blend_path)
    
    # Export fully detailed GLB
    glb_path = "export/case_study/detailed_facade.glb"
    print("[Blender Detailed Assembly] Exporting to GLB:", glb_path)
    try:
        bpy.ops.export_scene.gltf(
            filepath=glb_path,
            export_format='GLB',
            export_copyright="Tecate Simulator Detailed Facade",
            export_texcoords=True,
            export_normals=True,
            export_materials='EXPORT',
            export_image_format='AUTO',
            use_selection=False
        )
        print("[Blender Detailed Assembly] GLB Export Successful!")
    except Exception as e:
        print("[Blender Detailed Assembly Error] GLB Export failed:", e)
        sys.exit(1)

if __name__ == '__main__':
    run()
""")
        print(f"[ProceduralMeshAssembler] Created Blender script: {blender_exec_script}")
        
        # 5. Locate Blender executable
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
                
        print(f"[ProceduralMeshAssembler] Launching Blender: '{blender_path}'...")
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
            print("[ProceduralMeshAssembler] Successfully generated detailed_facade.glb and detailed_facade.blend!")
            return os.path.join(self.export_dir, "case_study", "detailed_facade.glb")
        else:
            raise RuntimeError(f"Blender detailed facade compilation failed with code {res.returncode}")
