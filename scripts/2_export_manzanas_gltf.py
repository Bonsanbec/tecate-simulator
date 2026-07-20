#!/usr/bin/env python3
import json
import os
import sys

try:
    import bpy
    import mathutils
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False

def run_export():
    if not HAS_BLENDER:
        print("Error: This script must be run inside Blender python environment.")
        print("Usage: blender --background --python scripts/2_export_manzanas_gltf.py")
        sys.exit(1)

    print("=" * 60)
    print("  STEP 2: MANZANA GLTF & OVER-TERRAIN PLATFORM EXPORT PIPELINE")
    print("=" * 60)

    mapping_file = "data/building_manzana_mapping.json"
    blocks_file = "data/blocks_cache.json"
    blend_file = "models/tecate/osm2world.blend"
    output_dir = "godot_project/assets/blocks/manzanas"
    translation = mathutils.Vector((34975.75, -31878.95, 0.0))
    T_mat = mathutils.Matrix.Translation(translation)

    if not os.path.exists(mapping_file):
        print(f"Error: Mapping file not found at {mapping_file}. Run Step 1 first!")
        sys.exit(1)

    if not os.path.exists(blend_file):
        print(f"Error: Blend file not found at {blend_file}")
        sys.exit(1)

    print(f"[1/5] Loading {mapping_file}...")
    with open(mapping_file, "r") as f:
        mapping_data = json.load(f)

    manzanas = mapping_data.get("manzanas", {})
    print(f"  Found {len(manzanas)} unique manzanas to export.")

    blocks_data = {}
    if os.path.exists(blocks_file):
        with open(blocks_file, "r") as f:
            blocks_data = json.load(f)

    print(f"[2/5] Loading {blend_file}...")
    bpy.ops.wm.open_mainfile(filepath=blend_file)

    # 3. Bake spatial offset directly into mesh vertex data
    print(f"[3/5] Baking spatial offset {translation} directly into mesh vertex buffers...")
    all_building_names = set(mapping_data.get("buildings", {}).keys())
    for obj in bpy.data.objects:
        if obj.name in all_building_names and obj.type == 'MESH':
            full_matrix = T_mat @ obj.matrix_world
            obj.data.transform(full_matrix)
            obj.matrix_world = mathutils.Matrix.Identity(4)

    bpy.context.view_layer.update()

    os.makedirs(output_dir, exist_ok=True)

    import_template = """[remap]

importer="scene"
importer_version=1
type="PackedScene"

[params]

nodes/root_type=""
nodes/root_name=""
nodes/root_script=null
nodes/apply_root_scale=true
nodes/root_scale=1.0
nodes/import_as_skeleton_bones=false
nodes/use_name_suffixes=true
nodes/use_node_type_suffixes=true
meshes/ensure_tangents=true
meshes/generate_lods=false
meshes/create_shadow_meshes=false
meshes/light_baking=1
meshes/lightmap_texel_size=0.2
meshes/force_disable_compression=false
skins/use_named_skins=true
animation/import=false
import_script/path=""
materials/extract=0
materials/extract_format=0
materials/extract_path=""
_subresources={}
gltf/naming_version=2
gltf/embedded_image_handling=1
"""

    def create_platform_mesh(manzana_id, poly_pts):
        if len(poly_pts) < 3:
            return None
        mesh = bpy.data.meshes.new(f"PlatformMesh_{manzana_id}")
        obj = bpy.data.objects.new(f"Pavement_{manzana_id}", mesh)
        bpy.context.scene.collection.objects.link(obj)

        verts = []
        # Top and bottom faces for 0.4m thick elevated over-terrain pavement
        for x, y in poly_pts:
            verts.append((x, y, 0.2))
        for x, y in poly_pts:
            verts.append((x, y, -0.2))

        n_pts = len(poly_pts)
        faces = []
        # Top face
        faces.append([i for i in range(n_pts)])
        # Bottom face
        faces.append([i + n_pts for i in range(n_pts - 1, -1, -1)])
        # Side quad faces
        for i in range(n_pts):
            next_i = (i + 1) % n_pts
            faces.append([i, next_i, next_i + n_pts, i + n_pts])

        mesh.from_pydata(verts, [], faces)
        mesh.update()
        return obj

    print(f"[4/5] Exporting {len(manzanas)} manzanas to GLTF format...")
    exported_count = 0
    error_count = 0

    for manzana_id, b_list in manzanas.items():
        if not b_list:
            continue

        bpy.ops.object.select_all(action='DESELECT')

        valid_objs = []
        for b in b_list:
            bname = b["building_name"]
            if bname in bpy.data.objects:
                obj = bpy.data.objects[bname]
                obj.select_set(True)
                valid_objs.append(obj)

        # Create platform over-terrain mesh if polygon available
        platform_obj = None
        if manzana_id in blocks_data and "polygon" in blocks_data[manzana_id]:
            poly = blocks_data[manzana_id]["polygon"]
            platform_obj = create_platform_mesh(manzana_id, poly)
            if platform_obj:
                platform_obj.select_set(True)

        if not valid_objs and not platform_obj:
            continue

        out_gltf = os.path.join(output_dir, f"{manzana_id}.gltf")
        out_import = os.path.join(output_dir, f"{manzana_id}.gltf.import")

        try:
            bpy.ops.export_scene.gltf(
                filepath=out_gltf,
                export_format='GLTF_SEPARATE',
                export_copyright="Tecate Simulator Manzana Platform",
                export_texcoords=True,
                export_normals=True,
                export_materials='EXPORT',
                export_image_format='AUTO',
                use_selection=True
            )

            with open(out_import, "w") as f:
                f.write(import_template)

            exported_count += 1
            if exported_count % 50 == 0 or exported_count == len(manzanas):
                print(f"  Progress: {exported_count}/{len(manzanas)} manzanas exported...")

        except Exception as e:
            print(f"  [Error] Failed to export {manzana_id}: {e}")
            error_count += 1

        # Clean up temporary platform object
        if platform_obj:
            bpy.data.objects.remove(platform_obj, do_unlink=True)

    print("=" * 60)
    print(f"  Export Complete!")
    print(f"  Successfully exported: {exported_count} manzanas")
    print(f"  Errors: {error_count}")
    print(f"  Output directory: {output_dir}")
    print("=" * 60)

if __name__ == "__main__":
    run_export()
