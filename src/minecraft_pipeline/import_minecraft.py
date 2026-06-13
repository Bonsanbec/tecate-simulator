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

def get_or_create_relative_image(block_name):
    clean_name = block_name
    if ":" in clean_name:
        clean_name = clean_name.split(":")[-1]
    
    rel_path = f"//resource_pack/assets/minecraft/textures/block/{clean_name}.png"
    image_name = f"img_{clean_name}"
    img = bpy.data.images.get(image_name)
    if not img:
        img = bpy.data.images.new(image_name, width=16, height=16)
        img.filepath = rel_path
        img.source = 'FILE'
    return img

def setup_block_material(block_name, color):
    mat_name = block_name
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        
        # Clear default nodes
        mat.node_tree.nodes.clear()
        
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        output_node = nodes.new(type="ShaderNodeOutputMaterial")
        output_node.location = (400, 0)
        
        bsdf_node = nodes.new(type="ShaderNodeBsdfPrincipled")
        bsdf_node.location = (100, 0)
        
        # Set fallback color and roughness
        bsdf_node.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
        bsdf_node.inputs['Roughness'].default_value = 0.8
        
        # Create image texture node pointing to relative path
        tex_node = nodes.new(type="ShaderNodeTexImage")
        tex_node.location = (-200, 0)
        tex_node.image = get_or_create_relative_image(block_name)
        
        # Connect Image Texture -> Principled BSDF
        links.new(tex_node.outputs['Color'], bsdf_node.inputs['Base Color'])
        links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])
        
    return mat

def build_voxels_mesh(boxes_data, output_dir):
    """
    Groups boxes by region and block type, constructs meshes with exposed faces,
    merges vertices, and sets up relative texture shader materials.
    """
    region_data = boxes_data.get("region_data", {})
    
    print(f"[Blender] Parsing exposed geometry for {len(region_data)} regions...")
    
    for region_key, boxes in region_data.items():
        # Group boxes in this region by block type
        grouped_boxes = {}
        for box in boxes:
            b_type = box["block_type"]
            grouped_boxes.setdefault(b_type, []).append(box)
            
        for b_type, region_boxes in grouped_boxes.items():
            # Clean names for Blender identifiers
            clean_reg = region_key.replace('.', '_')
            clean_type = b_type.replace(':', '_')
            mesh_name = f"mesh_{clean_reg}_{clean_type}"
            obj_name = f"obj_{clean_reg}_{clean_type}"
            
            verts = []
            faces = []
            
            for idx, box in enumerate(region_boxes):
                b_pos = box["pos"]
                mask = box["mask"]
                
                cx, cy, cz = b_pos
                x0, y0, z0 = cx, cy, cz
                x1, y1, z1 = cx + 1.0, cy + 1.0, cz + 1.0
                
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
                
                # Add exposed faces based on bitmask
                # Right (+X)
                if mask & 1:
                    faces.append([v_idx + 1, v_idx + 2, v_idx + 6, v_idx + 5])
                # Left (-X)
                if mask & 2:
                    faces.append([v_idx + 3, v_idx + 0, v_idx + 4, v_idx + 7])
                # Top (+Z)
                if mask & 4:
                    faces.append([v_idx + 4, v_idx + 5, v_idx + 6, v_idx + 7])
                # Bottom (-Z)
                if mask & 8:
                    faces.append([v_idx + 0, v_idx + 3, v_idx + 2, v_idx + 1])
                # Front (-Y)
                if mask & 16:
                    faces.append([v_idx + 0, v_idx + 1, v_idx + 5, v_idx + 4])
                # Back (+Y)
                if mask & 32:
                    faces.append([v_idx + 2, v_idx + 3, v_idx + 7, v_idx + 6])
                    
            mesh = bpy.data.meshes.new(name=mesh_name)
            mesh.from_pydata(verts, [], faces)
            mesh.update()
            
            obj = bpy.data.objects.new(obj_name, mesh)
            bpy.context.scene.collection.objects.link(obj)
            
            # Apply Material
            color = region_boxes[0]["color"]
            mat = setup_block_material(b_type, color)
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
    """Sets up default lighting in the scene."""
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
