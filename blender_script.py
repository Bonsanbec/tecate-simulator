import os
import json
import sys
import math

try:
    import bpy
    import mathutils
except ImportError:
    print("[Error] This script must be run inside Blender's python environment.")
    print("Usage: blender --background --python blender_script.py -- --import export/reconstruction_export.json")
    sys.exit(1)

def clear_scene():
    """Clears all objects, meshes, materials, and textures from the active Blender scene."""
    print("[Blender] Clearing default scene items...")
    if hasattr(bpy.ops.object, "select_all"):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        
    # Clear unused meshes, materials, and images to prevent bloat
    for block in [bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.cameras, bpy.data.lights]:
        for item in list(block):
            block.remove(item)

def create_road_graph_mesh(graph_data: dict):
    """Visualizes the road network skeleton as an unrendered wireframe mesh at z = 0.05."""
    print("[Blender] Constructing road graph skeleton...")
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    
    node_id_map = {}
    verts = []
    
    for idx, nd in enumerate(nodes):
        verts.append((nd["x"], nd["y"], 0.05))
        node_id_map[nd["id"]] = idx
        
    line_edges = []
    for ed in edges:
        u_idx = node_id_map.get(ed["u"])
        v_idx = node_id_map.get(ed["v"])
        if u_idx is not None and v_idx is not None:
            line_edges.append((u_idx, v_idx))
            
    mesh = bpy.data.meshes.new(name="RoadNetwork_Mesh")
    mesh.from_pydata(verts, line_edges, [])
    mesh.update()
    
    obj = bpy.data.objects.new("RoadNetwork", mesh)
    bpy.context.scene.collection.objects.link(obj)
    
    mat = bpy.data.materials.new(name="Road_Material")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.05, 0.05, 0.05, 1.0)
    obj.data.materials.append(mat)

def build_block_meshes(blocks_data: list):
    """
    Constructs the 3D block (manzana) volumes, loads texture atlases,
    and maps UV coordinates on facade/roof loops.
    """
    print(f"[Blender] Building {len(blocks_data)} urban blocks (manzanas)...")
    
    for bl in blocks_data:
        b_id = bl["block_id"]
        poly = bl["polygon"]
        height = bl["height_meters"]
        
        num_verts = len(poly) - 1
        centroid_x, centroid_y = bl["centroid"]
        
        z_base = 0.0
        verts = []
        faces = []
        
        # 1. Spawn vertices
        # Bottom ring (z = z_base)
        for i in range(num_verts):
            verts.append((poly[i][0], poly[i][1], z_base))
        # Top ring (z = z_base + height)
        for i in range(num_verts):
            verts.append((poly[i][0], poly[i][1], z_base + height))
            
        # 2. Spawn vertical facade faces
        for i in range(num_verts):
            next_idx = (i + 1) % num_verts
            face = [i, next_idx, next_idx + num_verts, i + num_verts]
            faces.append(face)
            
        # 3. Spawn roof face (top polygon)
        roof_face = list(range(num_verts, 2 * num_verts))
        roof_face.reverse()
        faces.append(roof_face)
        
        # Create Blender Mesh
        mesh = bpy.data.meshes.new(name=f"{b_id}_Mesh")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        
        obj = bpy.data.objects.new(b_id, mesh)
        bpy.context.scene.collection.objects.link(obj)
        
        # 4. Map UV coordinates
        uv_mappings = bl.get("uv_mappings", {})
        if uv_mappings:
            uv_layer = mesh.uv_layers.new(name="UVMap")
            
            for f_idx, face in enumerate(mesh.polygons):
                if f_idx < num_verts:
                    surface_id = f"{b_id}_facade_{f_idx}"
                    uvs = uv_mappings.get(surface_id, [[0.0, 0.0]] * 4)
                else:
                    surface_id = f"{b_id}_roof"
                    uvs = uv_mappings.get(surface_id, [[0.0, 0.0]] * num_verts)
                    
                for loop_idx, loop_corner in enumerate(face.loop_indices):
                    uv_layer.data[loop_corner].uv = uvs[loop_idx % len(uvs)]
                    
        # 5. Set up Material Shader and Bind Stitched Textures per face
        facade_tex_dict = bl.get("facade_textures", {})
        loaded_materials = {}
        
        for f_idx in range(num_verts):
            face = mesh.polygons[f_idx]
            surface_id = f"{b_id}_facade_{f_idx}"
            tex_path = facade_tex_dict.get(surface_id)
            
            if not tex_path or not os.path.exists(tex_path):
                tex_path = os.path.abspath("export/textures/transparent_facade.png")
                
            if tex_path not in loaded_materials:
                mat_name = f"{b_id}_mat_{os.path.basename(tex_path).replace('.', '_')}"
                mat = bpy.data.materials.new(name=mat_name)
                mat.use_nodes = True
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links
                
                bsdf = nodes.get("Principled BSDF")
                node_tex = nodes.new(type='ShaderNodeTexImage')
                
                try:
                    img = bpy.data.images.load(tex_path)
                    node_tex.image = img
                except Exception as e:
                    print(f"[Warning] Failed to load texture {tex_path}: {e}")
                    
                if bsdf:
                    links.new(node_tex.outputs['Color'], bsdf.inputs['Base Color'])
                    if 'Alpha' in node_tex.outputs and 'Alpha' in bsdf.inputs:
                        links.new(node_tex.outputs['Alpha'], bsdf.inputs['Alpha'])
                    try:
                        mat.blend_method = 'BLEND'
                    except AttributeError:
                        pass
                    try:
                        mat.shadow_method = 'NONE'
                    except AttributeError:
                        pass
                    
                obj.data.materials.append(mat)
                loaded_materials[tex_path] = len(obj.data.materials) - 1
                
            face.material_index = loaded_materials[tex_path]
            
        # 6. Assign dynamic predominant roof color material to the roof
        roof_color = bl.get("roof_color", [238 / 255.0, 232 / 255.0, 220 / 255.0])
        roof_mat_name = f"{b_id}_roof_material"
        mat = bpy.data.materials.new(name=roof_mat_name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = (roof_color[0], roof_color[1], roof_color[2], 1.0)
            
        obj.data.materials.append(mat)
        roof_face = mesh.polygons[num_verts]
        roof_face.material_index = len(obj.data.materials) - 1

def setup_lighting_and_camera():
    """Sets up standard illumination and a convenient top-down camera views."""
    print("[Blender] Configures lighting and default bird's-eye camera...")
    # Add a Sun light
    light_data = bpy.data.lights.new(name="SunLight", type='SUN')
    light_data.energy = 3.5
    light_obj = bpy.data.objects.new(name="SunLight", object_data=light_data)
    bpy.context.scene.collection.objects.link(light_obj)
    
    light_obj.location = (0.0, 0.0, 150.0)
    light_obj.rotation_euler = (math.radians(35.0), math.radians(20.0), math.radians(45.0))
    
    # Add an ambient light
    light_data2 = bpy.data.lights.new(name="HemiLight", type='POINT')
    light_data2.energy = 8000.0
    light_obj2 = bpy.data.objects.new(name="HemiLight", object_data=light_data2)
    bpy.context.scene.collection.objects.link(light_obj2)
    light_obj2.location = (0.0, 0.0, 80.0)
    
    # Add a camera
    cam_data = bpy.data.cameras.new(name="OrthoCamera")
    cam_obj = bpy.data.objects.new(name="OrthoCamera", object_data=cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    
    cam_obj.location = (0.0, -120.0, 110.0)
    cam_obj.rotation_euler = (math.radians(48.0), 0.0, 0.0)
    bpy.context.scene.camera = cam_obj

def main():
    args = []
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        
    export_json = "export/reconstruction_export.json"
    
    for idx, arg in enumerate(args):
        if arg == "--import" and idx + 1 < len(args):
            export_json = args[idx + 1]
            break
            
    print(f"[Blender] Starting import from: {export_json}")
    
    if not os.path.exists(export_json):
        print(f"[Error] Target export file {export_json} does not exist. Aborting.")
        sys.exit(1)
        
    with open(export_json, "r", encoding="utf-8") as f:
        scene_doc = json.load(f)
        
    clear_scene()
    
    # Reconstruct modulesSnapped strictly to ground plane Z=0 (ignoring large terrain)
    create_road_graph_mesh(scene_doc.get("road_graph", {}))
    build_block_meshes(scene_doc.get("blocks", []))
    setup_lighting_and_camera()
    
    # Save standard blend file
    save_path = "tecate_reconstruction.blend"
    bpy.ops.wm.save_as_mainfile(filepath=save_path)
    print(f"[Blender] Reconstructed 3D City successfully saved to: {os.path.abspath(save_path)}")
    
    # Export fully textured GLB asset to export/geometry.glb
    glb_path = "export/geometry.glb"
    print(f"[Blender] Exporting scene to self-contained GLB asset: {glb_path}")
    try:
        # standard gltf operator exports all meshes, materials, and textures embedded
        bpy.ops.export_scene.gltf(
            filepath=glb_path,
            export_format='GLB',
            export_copyright="Tecate Simulator",
            export_texcoords=True,
            export_normals=True,
            export_materials='EXPORT',
            use_selection=False
        )
        print(f"[Blender] Successfully exported: {os.path.abspath(glb_path)}")
    except Exception as glb_err:
        print(f"[Error] Failed to export GLB model: {glb_err}")

if __name__ == "__main__":
    main()
