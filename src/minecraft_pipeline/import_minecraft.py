import os
import json
import sys

try:
    import bpy
    import mathutils
except ImportError:
    print("[Error] This script must be run inside Blender's python environment.")
    sys.exit(1)

def clear_scene():
    """Clears all default objects, meshes, materials, and lights from the scene."""
    print("[Blender] Clearing active scene...")
    if hasattr(bpy.ops.object, "select_all"):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
    for block in [bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.cameras, bpy.data.lights]:
        for item in list(block):
            block.remove(item)

def build_voxels_mesh(boxes_data, output_dir):
    """
    Groups boxes by block type, constructs meshes, merges vertices,
    and sets up basic colored materials.
    """
    # Group boxes by block type
    grouped_boxes = {}
    for box in boxes_data:
        b_type = box["block_type"]
        grouped_boxes.setdefault(b_type, []).append(box)
        
    print(f"[Blender] Compiling {len(grouped_boxes)} unique block types...")
    
    for b_type, boxes in grouped_boxes.items():
        mesh_name = f"mesh_{b_type.replace(':', '_')}"
        obj_name = f"obj_{b_type.replace(':', '_')}"
        
        verts = []
        faces = []
        
        # We'll use a unified list of vertices.
        # To make it simple, each box contributes 8 vertices.
        # Blender's remove_doubles will merge them later.
        for idx, box in enumerate(boxes):
            b_min = box["min"]
            b_max = box["max"]
            
            # The 8 corners of the box
            x0, y0, z0 = b_min
            x1, y1, z1 = b_max
            
            v_idx = len(verts)
            verts.extend([
                (x0, y0, z0), # 0
                (x1, y0, z0), # 1
                (x1, y1, z0), # 2
                (x0, y1, z0), # 3
                (x0, y0, z1), # 4
                (x1, y0, z1), # 5
                (x1, y1, z1), # 6
                (x0, y1, z1)  # 7
            ])
            
            # The 6 faces of the box (quads)
            faces.extend([
                [v_idx + 0, v_idx + 1, v_idx + 2, v_idx + 3], # Bottom
                [v_idx + 4, v_idx + 5, v_idx + 6, v_idx + 7], # Top
                [v_idx + 0, v_idx + 1, v_idx + 5, v_idx + 4], # Front
                [v_idx + 1, v_idx + 2, v_idx + 6, v_idx + 5], # Right
                [v_idx + 2, v_idx + 3, v_idx + 7, v_idx + 6], # Back
                [v_idx + 3, v_idx + 0, v_idx + 4, v_idx + 7]  # Left
            ])
            
        # Create Mesh and Object
        mesh = bpy.data.meshes.new(name=mesh_name)
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        
        obj = bpy.data.objects.new(obj_name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        
        # Apply Material
        color = boxes[0]["color"] # RGB float array
        mat_name = f"mat_{b_type.replace(':', '_')}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
            bsdf.inputs['Roughness'].default_value = 0.8
        obj.data.materials.append(mat)
        
        # Optimize mesh by removing duplicate vertices and hidden faces
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        
        try:
            bpy.ops.object.mode_set(mode='EDIT')
            # Merges overlapping vertices
            bpy.ops.mesh.remove_doubles(threshold=0.0001)
            # Recalculate normals to face outward
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception as err:
            print(f"[Warning] Failed to optimize mesh {obj_name}: {err}")
            if obj.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
                
        obj.select_set(False)

def setup_scene_rendering():
    """Sets up default lighting and camera views in the scene."""
    # Add a simple sun light
    light_data = bpy.data.lights.new(name="Sun", type='SUN')
    light_data.energy = 2.0
    light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
    bpy.context.scene.collection.objects.link(light_obj)
    light_obj.location = (0.0, 0.0, 100.0)
    light_obj.rotation_euler = (0.5, 0.2, 0.8)

def main():
    args = []
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        
    import_json = ""
    output_dir = "."
    
    for idx, arg in enumerate(args):
        if arg == "--import" and idx + 1 < len(args):
            import_json = args[idx + 1]
        elif arg == "--output-dir" and idx + 1 < len(args):
            output_dir = args[idx + 1]
            
    if not import_json or not os.path.exists(import_json):
        print(f"[Error] Target import JSON '{import_json}' does not exist. Aborting.")
        sys.exit(1)
        
    print(f"[Blender] Starting import from: {import_json}")
    with open(import_json, 'r', encoding='utf-8') as f:
        boxes_data = json.load(f)
        
    clear_scene()
    build_voxels_mesh(boxes_data, output_dir)
    setup_scene_rendering()
    
    # Save standard .blend file
    save_path = os.path.join(output_dir, "tecate_reimported.blend")
    bpy.ops.wm.save_as_mainfile(filepath=save_path)
    print(f"[Blender] Saved .blend file to: {os.path.abspath(save_path)}")
    
    # Export optimized glTF/GLB model
    gltf_path = os.path.join(output_dir, "geometry_reimported.glb")
    try:
        bpy.ops.export_scene.gltf(
            filepath=gltf_path,
            export_format='GLB',
            export_copyright="Tecate Simulator Reimported",
            export_materials='EXPORT',
            export_image_format='AUTO',
            use_selection=False
        )
        print(f"[Blender] Saved .glb file to: {os.path.abspath(gltf_path)}")
    except Exception as gltf_err:
        print(f"[Error] Failed to export glTF model: {gltf_err}")

if __name__ == "__main__":
    main()
