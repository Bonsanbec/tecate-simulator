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

def load_terrain_model() -> list:
    """Imports the existing detailed georeferenced terrain GLB model into the scene."""
    terrain_dir = "models/tecate/glb"
    candidates = [
        "tecate (detallado sin edificios).glb",
        "tecate (detallado sin edificios ni vegetación).glb",
        "tecate (detallado con edificios).glb"
    ]
    
    filepath = None
    for name in candidates:
        path = os.path.join(terrain_dir, name)
        if os.path.exists(path):
            filepath = path
            break
            
    if filepath is None:
        if os.path.exists(terrain_dir):
            for f in os.listdir(terrain_dir):
                if f.endswith(".glb"):
                    filepath = os.path.join(terrain_dir, f)
                    break
                    
    if filepath and os.path.exists(filepath):
        print(f"[Blender] Importing georeferenced terrain model from: {filepath}")
        try:
            # Load glb
            bpy.ops.import_scene.gltf(filepath=filepath)
            print("[Blender] Terrain imported successfully.")
            
            # Gather all imported mesh objects
            terrain_objs = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
            return terrain_objs
        except Exception as e:
            print(f"[Warning] Failed to import terrain model via gltf: {e}")
    else:
        print("[Warning] No terrain GLB found. Reconstructing buildings at default z = 0.")
        
    return []

def find_terrain_elevation(x: float, y: float, terrain_objs: list) -> float:
    """Raycasts downwards from (x, y, 1000) onto the terrain meshes to find the exact Z elevation."""
    if not terrain_objs:
        return 0.0
        
    best_z = 0.0
    found = False
    
    ray_origin = (x, y, 1000.0)
    ray_direction = (0.0, 0.0, -1.0)
    
    for obj in terrain_objs:
        # Transform ray origin and direction to object local coordinates
        matrix_inv = obj.matrix_world.inverted()
        local_origin = matrix_inv @ mathutils.Vector(ray_origin)
        local_direction = matrix_inv.to_3x3() @ mathutils.Vector(ray_direction)
        local_direction.normalize()
        
        success, location, normal, face_index = obj.ray_cast(local_origin, local_direction)
        if success:
            world_location = obj.matrix_world @ location
            if not found or world_location.z > best_z:
                best_z = world_location.z
                found = True
                
    return best_z if found else 0.0

def create_road_graph_mesh(graph_data: dict, terrain_objs: list = None):
    """Visualizes the road network skeleton as an unrendered wireframe mesh, projected onto terrain."""
    print("[Blender] Constructing road graph skeleton...")
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    
    node_id_map = {}
    verts = []
    
    for idx, nd in enumerate(nodes):
        # Snap road intersection heights to terrain elevation
        z_elevation = 0.05
        if terrain_objs:
            z_elevation = find_terrain_elevation(nd["x"], nd["y"], terrain_objs) + 0.05
            
        verts.append((nd["x"], nd["y"], z_elevation))
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

def create_point_cloud_object(points_data: list):
    """Spawns the sparse SfM point cloud in Blender, applying vertex colors."""
    if not points_data:
        return
        
    print(f"[Blender] Triangulating {len(points_data)} sparse points...")
    verts = []
    colors = []
    
    for pt in points_data:
        verts.append(pt["coord"])
        colors.append(pt["color"] + [1.0])
        
    mesh = bpy.data.meshes.new(name="SfMPointCloud_Mesh")
    mesh.from_pydata(verts, [], [])
    mesh.update()
    
    obj = bpy.data.objects.new("SfM_PointCloud", mesh)
    bpy.context.scene.collection.objects.link(obj)
    
    color_layer = mesh.attributes.new(name="Color", type='FLOAT_COLOR', domain='POINT')
    for idx, col in enumerate(colors):
        color_layer.data[idx].color = col
        
    mat = bpy.data.materials.new(name="PointCloud_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    for node in list(nodes):
        nodes.remove(node)
        
    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_emission = nodes.new(type='ShaderNodeEmission')
    node_attribute = nodes.new(type='ShaderNodeAttribute')
    node_attribute.attribute_name = "Color"
    
    links.new(node_attribute.outputs['Color'], node_emission.inputs['Color'])
    links.new(node_emission.outputs['Emission'], node_out.inputs['Surface'])
    
    obj.data.materials.append(mat)
    obj.display_type = 'TEXTURED'

def build_block_meshes(blocks_data: list, terrain_objs: list = None):
    """
    Constructs the 3D block (manzana) volumes, loads texture atlases,
    and maps UV coordinates on facade/roof loops.
    Snaps buildings base level precisely to the terrain elevation.
    """
    print(f"[Blender] Building {len(blocks_data)} urban blocks (manzanas)...")
    
    for bl in blocks_data:
        b_id = bl["block_id"]
        poly = bl["polygon"]
        height = bl["height_meters"]
        
        num_verts = len(poly) - 1
        centroid_x, centroid_y = bl["centroid"]
        
        # Snapping base to the terrain GLB
        z_base = 0.0
        if terrain_objs:
            z_base = find_terrain_elevation(centroid_x, centroid_y, terrain_objs)
            print(f"[Blender] Snapping block {b_id} base to terrain Z: {z_base:.2f}m")
            
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
                    
        # 5. Set up Material Shader and Bind Stitched Texture Atlas
        atlas_path = bl.get("texture_atlas_path")
        if atlas_path and os.path.exists(atlas_path):
            mat = bpy.data.materials.new(name=f"{b_id}_Material")
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            
            bsdf = nodes.get("Principled BSDF")
            node_tex = nodes.new(type='ShaderNodeTexImage')
            
            try:
                img = bpy.data.images.load(atlas_path)
                node_tex.image = img
            except Exception as e:
                print(f"[Warning] Failed to load texture atlas {atlas_path}: {e}")
                
            if bsdf:
                links.new(node_tex.outputs['Color'], bsdf.inputs['Base Color'])
                
            obj.data.materials.append(mat)
        else:
            mat = bpy.data.materials.new(name=f"{b_id}_Material_Fallback")
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs['Base Color'].default_value = (0.8, 0.76, 0.72, 1.0)
            obj.data.materials.append(mat)

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
    
    # 1. Import pre-existing georeferenced detailed terrain model
    terrain_objs = load_terrain_model()
    
    # 2. Reconstruct modules snapped to topography
    create_road_graph_mesh(scene_doc.get("road_graph", {}), terrain_objs)
    create_point_cloud_object(scene_doc.get("sparse_point_cloud", []))
    build_block_meshes(scene_doc.get("blocks", []), terrain_objs)
    setup_lighting_and_camera()
    
    # Save blend file
    save_path = "tecate_reconstruction.blend"
    bpy.ops.wm.save_as_mainfile(filepath=save_path)
    print(f"[Blender] Reconstructed 3D City successfully saved to: {os.path.abspath(save_path)}")

if __name__ == "__main__":
    main()
