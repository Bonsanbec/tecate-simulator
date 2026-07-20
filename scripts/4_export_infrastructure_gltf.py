#!/usr/bin/env python3
import json
import os
import math
import sys

try:
    import bpy
    import mathutils
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False

def run_infrastructure_export():
    if not HAS_BLENDER:
        print("Error: This script must be run inside Blender python environment.")
        print("Usage: blender --background --python scripts/4_export_infrastructure_gltf.py")
        sys.exit(1)

    print("=" * 60)
    print("  STEP 3: INFRASTRUCTURE (ROADS, BRIDGES, RAILWAYS) EXPORT PIPELINE")
    print("=" * 60)

    blend_file = "models/tecate/osm2world.blend"
    osm_cache_file = "data/tecate_osm_cache.json"
    output_dir = "godot_project/assets/infrastructure"
    translation = mathutils.Vector((34975.75, -31878.95, 0.0))
    T_mat = mathutils.Matrix.Translation(translation)

    os.makedirs(output_dir, exist_ok=True)

    # 1. Open osm2world.blend to extract high-fidelity Road, Rail, and Bridge objects
    if os.path.exists(blend_file):
        print(f"[1/4] Loading {blend_file} for infrastructure surface extraction...")
        bpy.ops.wm.open_mainfile(filepath=blend_file)

        road_materials = {'ASPHALT', 'ASPHALT.001', 'PAVING_STONE', 'ROAD_MARKING', 'ROAD_MARKING.001', 'road_marking_crossing', 'road_marking_dash'}
        rail_materials = {'RAIL_BALLAST'}
        bridge_keywords = {'bridge', 'overpass', 'viaduct'}

        road_objs = []
        rail_objs = []
        bridge_objs = []

        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                is_road = False
                is_rail = False
                is_bridge = False

                for slot in obj.material_slots:
                    if slot.material:
                        mname = slot.material.name
                        if mname in road_materials:
                            is_road = True
                        elif mname in rail_materials:
                            is_rail = True

                if any(bk in obj.name.lower() for bk in bridge_keywords):
                    is_bridge = True

                if is_road or is_rail or is_bridge:
                    # Bake spatial translation into mesh vertex data
                    full_matrix = T_mat @ obj.matrix_world
                    obj.data.transform(full_matrix)
                    obj.matrix_world = mathutils.Matrix.Identity(4)

                    if is_bridge:
                        bridge_objs.append(obj)
                    elif is_rail:
                        rail_objs.append(obj)
                    else:
                        road_objs.append(obj)

        bpy.context.view_layer.update()

        print(f"  Extracted from Blender: {len(road_objs)} road meshes, {len(rail_objs)} rail meshes, {len(bridge_objs)} bridge meshes.")

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
meshes/ensure_tangents=true
meshes/generate_lods=false
meshes/create_shadow_meshes=false
"""

        print("[2/4] Exporting Infrastructure GLTF models...")
        for obj_list, fname in [(road_objs, "roads.gltf"), (rail_objs, "railways.gltf"), (bridge_objs, "bridges.gltf")]:
            if obj_list:
                bpy.ops.object.select_all(action='DESELECT')
                for o in obj_list:
                    o.select_set(True)

                out_gltf = os.path.join(output_dir, fname)
                out_import = os.path.join(output_dir, f"{fname}.import")

                bpy.ops.export_scene.gltf(
                    filepath=out_gltf,
                    export_format='GLTF_SEPARATE',
                    export_copyright="Tecate Infrastructure Layer",
                    use_selection=True
                )
                with open(out_import, "w") as f:
                    f.write(import_template)
                print(f"  Exported {fname}: {len(obj_list)} meshes.")

    # 2. Also generate OSM road network ribbons if osm_cache exists
    if os.path.exists(osm_cache_file):
        print(f"[3/4] Generating fallback OSM road network ribbons from {osm_cache_file}...")
        with open(osm_cache_file, "r") as f:
            osm_data = json.load(f)

        nodes = osm_data.get("nodes", {})
        edges = osm_data.get("edges", [])

        LAT_REF = 32.573229
        LON_REF = -116.626536
        METERS_PER_DEG_LAT = 110900.0
        METERS_PER_DEG_LON = 93800.0

        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene

        verts = []
        faces = []

        for e in edges:
            if isinstance(e, dict):
                u_id = str(e.get("u"))
                v_id = str(e.get("v"))
                if u_id in nodes and v_id in nodes:
                    u_node = nodes[u_id]
                    v_node = nodes[v_id]
                    ux = (u_node["lon"] - LON_REF) * METERS_PER_DEG_LON
                    uy = (u_node["lat"] - LAT_REF) * METERS_PER_DEG_LAT
                    vx = (v_node["lon"] - LON_REF) * METERS_PER_DEG_LON
                    vy = (v_node["lat"] - LAT_REF) * METERS_PER_DEG_LAT

                    w = 3.5  # 7m width total
                    dx = vx - ux
                    dy = vy - uy
                    length = math.hypot(dx, dy)
                    if length > 0.01:
                        nx = -dy / length * w
                        ny = dx / length * w

                        idx = len(verts)
                        verts.append((ux + nx, uy + ny, 0.05))
                        verts.append((ux - nx, uy - ny, 0.05))
                        verts.append((vx - nx, vy - ny, 0.05))
                        verts.append((vx + nx, vy + ny, 0.05))
                        faces.append([idx, idx + 1, idx + 2, idx + 3])

        if verts:
            mesh = bpy.data.meshes.new("OSMRoadsMesh")
            obj = bpy.data.objects.new("OSMRoadNetwork", mesh)
            scene.collection.objects.link(obj)
            mesh.from_pydata(verts, [], faces)
            mesh.update()

            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)

            out_gltf = os.path.join(output_dir, "osm_road_network.gltf")
            out_import = os.path.join(output_dir, "osm_road_network.gltf.import")

            bpy.ops.export_scene.gltf(
                filepath=out_gltf,
                export_format='GLTF_SEPARATE',
                export_copyright="Tecate OSM Road Network",
                use_selection=True
            )
            with open(out_import, "w") as f:
                f.write(import_template)
            print(f"  Exported osm_road_network.gltf: {len(faces)} quad road segments.")

    print("=" * 60)
    print("  Infrastructure Export Complete!")
    print(f"  Output directory: {output_dir}")
    print("=" * 60)

if __name__ == "__main__":
    run_infrastructure_export()
