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

def get_block_centroid(poly):
    """Calculates the 2D centroid of a closed polygon."""
    num_verts = len(poly) - 1
    if num_verts <= 0:
        return (0.0, 0.0)
    sx = sum(poly[i][0] for i in range(num_verts))
    sy = sum(poly[i][1] for i in range(num_verts))
    return (sx / num_verts, sy / num_verts)

def build_block_meshes(blocks_data: list, cull_fov: bool = True, cam_loc: tuple = (0.0, -120.0, 110.0), cam_rot: tuple = (48.0, 0.0, 0.0), fov_deg: float = 90.0, max_dist: float = 250.0):
    """
    Constructs 3D block geometries grouped by material to optimize viewport
    rendering performance, bypass EEVEE shader memory leaks, and prevent
    GLB/glTF exporter duplication crashes. Reconstructs all blocks, but sets
    initial visibility based on camera FOV/frustum to protect memory.
    """
    num_total = len(blocks_data)
    
    # Calculate 2D camera look direction on XY plane
    look_dir_2d = mathutils.Vector((0.0, 1.0))
    if cull_fov:
        rx, ry, rz = math.radians(cam_rot[0]), math.radians(cam_rot[1]), math.radians(cam_rot[2])
        euler = mathutils.Euler((rx, ry, rz))
        # Local look vector is (0, 0, -1) in Blender camera space
        look_dir = euler.to_matrix() @ mathutils.Vector((0.0, 0.0, -1.0))
        look_dir_2d = mathutils.Vector((look_dir.x, look_dir.y))
        if look_dir_2d.length > 1e-5:
            look_dir_2d.normalize()
        else:
            # Fallback if camera is pointed straight down or up
            look_dir_2d = mathutils.Vector((0.0, 1.0))
            
        print(f"[Blender] Camera FOV Culling Active: Loc={cam_loc}, Look={tuple(look_dir_2d)}, FOV={fov_deg}°, MaxDist={max_dist}m")
    else:
        print("[Blender] Camera FOV Culling Disabled. Loading entire city...")

    # Global caches to prevent image and material duplication
    loaded_images = {}
    loaded_materials = {}
    loaded_roof_materials = {}
    
    # Pre-cache fallback texture path to avoid check in loop
    fallback_path = os.path.abspath("export/textures/transparent_facade.png")
    
    # Group geometries by material (tex_path for facades)
    facade_geometry = {}
    
    num_visible = 0
    num_hidden = 0
    
    for idx, bl in enumerate(blocks_data):
        b_id = bl["block_id"]
        poly = bl["polygon"]
        height = bl["height_meters"]
        
        # 1. Evaluate block's initial camera visibility
        is_visible = True
        centroid = get_block_centroid(poly)
        if cull_fov:
            cx, cy = cam_loc[0], cam_loc[1]
            bx, by = centroid[0], centroid[1]
            
            dx = bx - cx
            dy = by - cy
            dist = math.sqrt(dx*dx + dy*dy)
            
            # Check maximum distance culling
            if dist > max_dist:
                is_visible = False
            # Check horizontal FOV culling
            elif dist > 1e-5:
                disp_dir = mathutils.Vector((dx / dist, dy / dist))
                dot = disp_dir.dot(look_dir_2d)
                half_fov_rad = math.radians(fov_deg / 2.0)
                min_dot = math.cos(half_fov_rad)
                
                if dot < min_dot:
                    is_visible = False
                    
        if is_visible:
            num_visible += 1
        else:
            num_hidden += 1
            
        num_verts = len(poly) - 1
        z_base = 0.0
        
        # Pre-fetch UV coordinates and facade textures
        uv_mappings = bl.get("uv_mappings", {})
        facade_tex_dict = bl.get("facade_textures", {})
        
        # 2. Process vertical facade faces
        for i in range(num_verts):
            next_idx = (i + 1) % num_verts
            surface_id = f"{b_id}_facade_{i}"
            
            # Face vertices in world space (BL, BR, TR, TL)
            BL = (poly[i][0], poly[i][1], z_base)
            BR = (poly[next_idx][0], poly[next_idx][1], z_base)
            TR = (poly[next_idx][0], poly[next_idx][1], z_base + height)
            TL = (poly[i][0], poly[i][1], z_base + height)
            
            # Face UVs
            uvs = uv_mappings.get(surface_id, [[0.0, 0.0]] * 4)
            
            # Face texture path
            tex_path = facade_tex_dict.get(surface_id)
            if not tex_path or not os.path.exists(tex_path):
                tex_path = fallback_path
                
            if tex_path not in facade_geometry:
                facade_geometry[tex_path] = { "verts": [], "faces": [], "uvs": [], "is_visible": is_visible }
            else:
                facade_geometry[tex_path]["is_visible"] = facade_geometry[tex_path]["is_visible"] or is_visible
                
            geo = facade_geometry[tex_path]
            s_idx = len(geo["verts"])
            geo["verts"].extend([BL, BR, TR, TL])
            geo["faces"].append([s_idx, s_idx + 1, s_idx + 2, s_idx + 3])
            geo["uvs"].extend(uvs)
            
        # 3. Process and build individual roof object for this block
        roof_verts = [(poly[i][0], poly[i][1], z_base + height) for i in reversed(range(num_verts))]
        roof_color = bl.get("roof_color", [238 / 255.0, 232 / 255.0, 220 / 255.0])
        roof_key = tuple(round(c, 3) for c in roof_color)
        
        roof_mesh_name = f"roof_{b_id}_mesh"
        roof_mesh = bpy.data.meshes.new(name=roof_mesh_name)
        roof_mesh.from_pydata(roof_verts, [], [list(range(num_verts))])
        roof_mesh.update()
        
        # Get or create shared roof color material
        if roof_key not in loaded_roof_materials:
            roof_mat_name = f"roof_mat_{roof_key[0]:.3f}_{roof_key[1]:.3f}_{roof_key[2]:.3f}"
            mat = bpy.data.materials.get(roof_mat_name)
            if not mat:
                mat = bpy.data.materials.new(name=roof_mat_name)
                mat.use_nodes = True
                bsdf = mat.node_tree.nodes.get("Principled BSDF")
                if bsdf:
                    bsdf.inputs['Base Color'].default_value = (roof_key[0], roof_key[1], roof_key[2], 1.0)
            loaded_roof_materials[roof_key] = mat
            
        roof_mat = loaded_roof_materials[roof_key]
        
        # Create roof object
        roof_obj_name = f"roof_{b_id}"
        roof_obj = bpy.data.objects.new(roof_obj_name, roof_mesh)
        bpy.context.scene.collection.objects.link(roof_obj)
        roof_obj.data.materials.append(roof_mat)
        
        # Store block centroid on the object for super-fast dynamic culling
        roof_obj["centroid_x"] = centroid[0]
        roof_obj["centroid_y"] = centroid[1]
        
        # Apply initial visibility
        roof_obj.hide_viewport = not is_visible
        roof_obj.hide_render = not is_visible

    if cull_fov:
        print(f"[Blender] Reconstructed all {num_total} urban blocks ({num_visible} initially visible, {num_hidden} hidden outside FOV).")
    else:
        print(f"[Blender] Reconstructed all {num_total} urban blocks (all visible).")

    # 4. Create facade mesh objects in Blender (one object per unique material/texture)
    print(f"[Blender] Compiling {len(facade_geometry)} unique facade materials...")
    for tex_path, geo in facade_geometry.items():
        mat_name = f"mat_{os.path.basename(tex_path).replace('.', '_')}"
        mesh_name = f"facade_{os.path.basename(tex_path)}_mesh"
        
        mesh = bpy.data.meshes.new(name=mesh_name)
        mesh.from_pydata(geo["verts"], [], geo["faces"])
        mesh.update()
        
        # Apply UV coordinates mapping
        if geo["uvs"]:
            uv_layer = mesh.uv_layers.new(name="UVMap")
            for loop in mesh.loops:
                if loop.index < len(geo["uvs"]):
                    uv_layer.data[loop.index].uv = geo["uvs"][loop.index]
                    
        # Load image exactly once globally
        if tex_path not in loaded_images:
            try:
                img = bpy.data.images.load(tex_path)
                loaded_images[tex_path] = img
            except Exception as e:
                print(f"[Warning] Failed to load texture {tex_path}: {e}")
                loaded_images[tex_path] = None
                
        # Create material exactly once globally
        if tex_path not in loaded_materials:
            mat = bpy.data.materials.get(mat_name)
            if not mat:
                mat = bpy.data.materials.new(name=mat_name)
                mat.use_nodes = True
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links
                
                bsdf = nodes.get("Principled BSDF")
                node_tex = nodes.new(type='ShaderNodeTexImage')
                node_tex.image = loaded_images[tex_path]
                
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
            loaded_materials[tex_path] = mat
            
        mat = loaded_materials[tex_path]
        
        # Create Object and bind material
        obj_name = f"facades_{os.path.basename(tex_path).replace('.', '_')}"
        obj = bpy.data.objects.new(obj_name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.data.materials.append(mat)
        
        # Compute and cache centroid on the object for super-fast culling
        xs = [v[0] for v in geo["verts"]]
        ys = [v[1] for v in geo["verts"]]
        centroid_x = sum(xs) / len(xs)
        centroid_y = sum(ys) / len(ys)
        obj["centroid_x"] = centroid_x
        obj["centroid_y"] = centroid_y
        
        # Apply initial visibility
        obj.hide_viewport = not geo["is_visible"]
        obj.hide_render = not geo["is_visible"]

def setup_lighting_and_camera(cam_loc: tuple = (0.0, -120.0, 110.0), cam_rot: tuple = (48.0, 0.0, 0.0), fov_deg: float = 90.0):
    """Sets up standard illumination and a convenient top-down camera views."""
    print(f"[Blender] Configures lighting and default bird's-eye camera at {cam_loc} with rotation {cam_rot}...")
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
    
    # Add a camera with matching field of view angle
    cam_data = bpy.data.cameras.new(name="OrthoCamera")
    cam_data.angle = math.radians(fov_deg)
    cam_obj = bpy.data.objects.new(name="OrthoCamera", object_data=cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    
    cam_obj.location = cam_loc
    cam_obj.rotation_euler = (math.radians(cam_rot[0]), math.radians(cam_rot[1]), math.radians(cam_rot[2]))
    bpy.context.scene.camera = cam_obj

def embed_culling_utility_script(fov_deg: float, max_dist: float):
    """Embeds an interactive Python viewport culling utility inside the .blend file."""
    text_name = "Viewport_FOV_Cull_Utility.py"
    txt = bpy.data.texts.get(text_name)
    if txt:
        bpy.data.texts.remove(txt)
    txt = bpy.data.texts.new(name=text_name)
    
    script_content = f"""# TECATE SIMULATOR: VIEWPORT FOV CULLING UTILITY
#
# INSTRUCTIONS:
# This script has been automatically configured and registered to run on load.
# You will find a "Tecate Culler" tab in the 3D Viewport Sidebar (N-panel)!
# Toggle the auto-culling and adjust the distance/FOV sliders there in real-time.

import bpy
import math
import mathutils

class TecateCullerProperties(bpy.types.PropertyGroup):
    auto_cull: bpy.props.BoolProperty(
        name="Auto-Cull Viewport",
        description="Enable automatic viewport culling as you navigate",
        default=True,
        update=lambda self, context: update_culling_visibility()
    )
    max_dist: bpy.props.FloatProperty(
        name="Max Distance",
        description="Maximum culling distance in meters",
        default={max_dist},
        min=50.0,
        max=2000.0,
        update=lambda self, context: update_culling_visibility()
    )
    fov_deg: bpy.props.FloatProperty(
        name="FOV Angle",
        description="Horizontal culling FOV in degrees",
        default={fov_deg},
        min=30.0,
        max=180.0,
        update=lambda self, context: update_culling_visibility()
    )

def update_culling_visibility():
    if bpy.app.background:
        return
        
    scene = bpy.context.scene
    if not scene or not hasattr(scene, "tecate_culler"):
        return
        
    props = scene.tecate_culler
    
    if not props.auto_cull:
        for obj in bpy.data.objects:
            if obj.name.startswith("facades_") or obj.name.startswith("roofs_"):
                obj.hide_viewport = False
                obj.hide_render = False
        return
        
    region_3d = None
    if hasattr(bpy.context, "screen") and bpy.context.screen:
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        region_3d = space.region_3d
                        break
                if region_3d:
                    break
                    
    if not region_3d:
        return
        
    view_matrix_inv = region_3d.view_matrix.inverted()
    cam_loc = view_matrix_inv.to_translation()
    look_dir = view_matrix_inv.to_3x3() @ mathutils.Vector((0.0, 0.0, -1.0))
    look_dir_2d = mathutils.Vector((look_dir.x, look_dir.y))
    if look_dir_2d.length > 1e-5:
        look_dir_2d.normalize()
    else:
        look_dir_2d = mathutils.Vector((0.0, 1.0))
        
    max_dist = props.max_dist
    half_fov_rad = math.radians(props.fov_deg / 2.0)
    min_dot = math.cos(half_fov_rad)
    
    for obj in bpy.data.objects:
        if not (obj.name.startswith("facades_") or obj.name.startswith("roofs_")):
            continue
            
        if not obj.data or not hasattr(obj.data, "vertices") or len(obj.data.vertices) == 0:
            continue
            
        if "centroid_x" in obj:
            cx, cy = obj["centroid_x"], obj["centroid_y"]
        else:
            xs = [v.co.x for v in obj.data.vertices]
            ys = [v.co.y for v in obj.data.vertices]
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)
            obj["centroid_x"] = cx
            obj["centroid_y"] = cy
            
        dx = cx - cam_loc.x
        dy = cy - cam_loc.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        is_visible = True
        if dist > max_dist:
            is_visible = False
        elif dist > 1e-5:
            disp_dir = mathutils.Vector((dx / dist, dy / dist))
            dot = disp_dir.dot(look_dir_2d)
            if dot < min_dot:
                is_visible = False
                
        obj.hide_viewport = not is_visible
        obj.hide_render = not is_visible

last_cam_loc = mathutils.Vector((0.0, 0.0, 0.0))
last_look_dir = mathutils.Vector((0.0, 0.0, 0.0))

def tecate_culler_timer():
    if bpy.app.background:
        return 0.1
        
    global last_cam_loc, last_look_dir
    
    if not hasattr(bpy.context, "scene") or not bpy.context.scene:
        return 0.1
    if not hasattr(bpy.context.scene, "tecate_culler"):
        return 0.1
        
    props = bpy.context.scene.tecate_culler
    if not props.auto_cull:
        return 0.1
        
    region_3d = None
    if hasattr(bpy.context, "screen") and bpy.context.screen:
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        region_3d = space.region_3d
                        break
                if region_3d:
                    break
                    
    if not region_3d:
        return 0.1
        
    view_matrix_inv = region_3d.view_matrix.inverted()
    cam_loc = view_matrix_inv.to_translation()
    look_dir = view_matrix_inv.to_3x3() @ mathutils.Vector((0.0, 0.0, -1.0))
    
    loc_diff = (cam_loc - last_cam_loc).length
    dir_diff = (look_dir - last_look_dir).length
    
    if loc_diff > 0.5 or dir_diff > 0.01:
        last_cam_loc = cam_loc.copy()
        last_look_dir = look_dir.copy()
        update_culling_visibility()
        
    return 0.1

class VIEW3D_PT_tecate_culler(bpy.types.Panel):
    bl_label = "Tecate City Viewport Culler"
    bl_idname = "VIEW3D_PT_tecate_culler"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tecate Culler'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        if not hasattr(scene, "tecate_culler"):
            return
        props = scene.tecate_culler
        
        box = layout.box()
        box.label(text="Culling Controls", icon='VIEWZOOM')
        box.prop(props, "auto_cull", toggle=True, icon='HIDE_OFF' if props.auto_cull else 'HIDE_ON')
        
        if props.auto_cull:
            col = box.column(align=True)
            col.prop(props, "max_dist", slider=True)
            col.prop(props, "fov_deg", slider=True)
            
            visible_count = sum(1 for obj in bpy.data.objects if (obj.name.startswith("facades_") or obj.name.startswith("roofs_")) and not obj.hide_viewport)
            total_count = sum(1 for obj in bpy.data.objects if (obj.name.startswith("facades_") or obj.name.startswith("roofs_")))
            
            row = box.row()
            row.label(text=f"Visible Blocks: {{visible_count}} / {{total_count}}", icon='RENDER_RESULT')

classes = (
    TecateCullerProperties,
    VIEW3D_PT_tecate_culler,
)

def register():
    if bpy.app.background:
        return
        
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass
            
    bpy.types.Scene.tecate_culler = bpy.props.PointerProperty(type=TecateCullerProperties)
    
    if not bpy.app.timers.is_registered(tecate_culler_timer):
        bpy.app.timers.register(tecate_culler_timer)
        
    update_culling_visibility()

def unregister():
    if bpy.app.timers.is_registered(tecate_culler_timer):
        bpy.app.timers.unregister(tecate_culler_timer)
        
    if hasattr(bpy.types.Scene, "tecate_culler"):
        del bpy.types.Scene.tecate_culler
        
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

if __name__ == '__main__':
    register()
"""
    txt.from_string(script_content)
    txt.use_module = True # Run this text block automatically as a module on load!
    
    # Try to make our script the active text block in any open Text Editor spaces
    try:
        for area in bpy.context.screen.areas:
            if area.type == 'TEXT_EDITOR':
                for space in area.spaces:
                    if space.type == 'TEXT_EDITOR':
                        space.text = txt
    except Exception:
        pass
        
    print(f"[Blender] Embedded and registered auto-running utility script: {text_name}")

def main():
    args = []
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        
    export_json = "export/reconstruction_export.json"
    
    # Culling and Camera settings defaults
    cull_fov = True
    cam_loc = (0.0, -120.0, 110.0)
    cam_rot = (48.0, 0.0, 0.0)
    fov_deg = 90.0
    max_dist = 250.0
    
    # Parsing custom arguments
    for idx, arg in enumerate(args):
        if arg == "--import" and idx + 1 < len(args):
            export_json = args[idx + 1]
        elif arg == "--no-cull":
            cull_fov = False
        elif arg == "--cam-loc" and idx + 1 < len(args):
            try:
                cam_loc = tuple(float(x) for x in args[idx + 1].split(","))
            except Exception as e:
                print(f"[Warning] Failed to parse --cam-loc: {e}")
        elif arg == "--cam-rot" and idx + 1 < len(args):
            try:
                cam_rot = tuple(float(x) for x in args[idx + 1].split(","))
            except Exception as e:
                print(f"[Warning] Failed to parse --cam-rot: {e}")
        elif arg == "--fov-deg" and idx + 1 < len(args):
            try:
                fov_deg = float(args[idx + 1])
            except Exception as e:
                print(f"[Warning] Failed to parse --fov-deg: {e}")
        elif arg == "--max-dist" and idx + 1 < len(args):
            try:
                max_dist = float(args[idx + 1])
            except Exception as e:
                print(f"[Warning] Failed to parse --max-dist: {e}")
            
    print(f"[Blender] Starting import from: {export_json}")
    
    if not os.path.exists(export_json):
        print(f"[Error] Target export file {export_json} does not exist. Aborting.")
        sys.exit(1)
        
    with open(export_json, "r", encoding="utf-8") as f:
        scene_doc = json.load(f)
        
    clear_scene()
    
    # Reconstruct road skeleton
    create_road_graph_mesh(scene_doc.get("road_graph", {}))
    
    # Reconstruct blocks with dynamic culling
    build_block_meshes(
        scene_doc.get("blocks", []),
        cull_fov=cull_fov,
        cam_loc=cam_loc,
        cam_rot=cam_rot,
        fov_deg=fov_deg,
        max_dist=max_dist
    )
    
    # Configure lighting and camera
    setup_lighting_and_camera(
        cam_loc=cam_loc,
        cam_rot=cam_rot,
        fov_deg=fov_deg
    )
    
    # Embed the interactive culling script inside the blend file
    embed_culling_utility_script(fov_deg=fov_deg, max_dist=max_dist)
    
    # Save standard blend file
    save_path = "tecate_reconstruction.blend"
    bpy.ops.wm.save_as_mainfile(filepath=save_path)
    print(f"[Blender] Reconstructed 3D City successfully saved to: {os.path.abspath(save_path)}")
    
    # Export fully textured glTF asset to export/geometry.gltf
    gltf_path = "export/geometry.gltf"
    print(f"[Blender] Exporting scene to separate optimized glTF asset: {gltf_path}")
    try:
        # Standard gltf operator exports all meshes and materials, referencing textures relatively
        bpy.ops.export_scene.gltf(
            filepath=gltf_path,
            export_format='GLTF_SEPARATE',
            export_copyright="Tecate Simulator",
            export_texcoords=True,
            export_normals=True,
            export_materials='EXPORT',
            export_image_format='NONE', # Keep existing high-res textures as relative references on disk
            use_selection=False
        )
        print(f"[Blender] Successfully exported: {os.path.abspath(gltf_path)}")
    except Exception as gltf_err:
        print(f"[Error] Failed to export glTF model: {gltf_err}")

if __name__ == "__main__":
    main()
