#!/usr/bin/env python3
"""
scripts/create_adjusted_blend.py
--------------------------------
Generates an authoritative, pre-adjusted working copy of osm2world.blend:
1. Opens models/tecate/osm2world.blend (READ-ONLY).
2. Propagates rich semantic metadata (OSM names, IDs, tags) from ancestor Empties onto mesh objects.
3. Purges all 22 flat 2D surface categories (Roads, Junctions, Rails, Waterways, Parking, etc.).
4. Applies calibrated horizontal alignment (DX = +34,976.59m, DY = -31,879.03m).
5. Raycasts against tecate.glb TIN mesh to bake ground elevation directly into vertex coordinates.
6. Extrudes 3.5m foundation skirts downward for all buildings to prevent sloped terrain gaps.
7. Normalizes all object scale/rotation hierarchies to clean world identity matrices.
8. Organizes surviving 3D structures into semantic Blender Collections.
9. Saves the working copy to godot_project/assets/osm2world_adjusted.blend.
10. Exports a clean, lightweight glTF 2.0 binary to godot_project/assets/osm2world_baked.glb.
"""

import sys
import os
import time
import argparse
import struct
import json
from collections import defaultdict

def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = argv[1:]

    parser = argparse.ArgumentParser(description="Create pre-adjusted OSM2World blend file.")
    parser.add_argument("--blend-path", default="models/tecate/osm2world.blend", help="Input read-only blend file")
    parser.add_argument("--terrain-glb", default="godot_project/assets/tecate2.glb", help="Input terrain GLB file")
    parser.add_argument("--output-blend", default="godot_project/assets/osm2world_adjusted.blend", help="Output adjusted blend file")
    parser.add_argument("--output-glb", default="godot_project/assets/osm2world_baked.glb", help="Output baked GLB file")
    parser.add_argument("--radius", type=float, default=-1.0, help="Culling radius in meters from Parque Hidalgo (-1 for all)")
    parser.add_argument("--skirt-depth", type=float, default=3.5, help="Foundation skirt downward extrusion depth in meters")
    parser.add_argument("--building-z-offset", type=float, default=0.0, help="Additional elevation offset for buildings")
    return parser.parse_args(argv)

def build_terrain_bvh(glb_path):
    """Loads tinMesh from tecate.glb, projects to local Cartesian space, and builds a BVHTree."""
    import numpy as np
    import mathutils
    from mathutils.bvhtree import BVHTree

    print(f"[Terrain] Reading terrain mesh from: {glb_path}")
    if not os.path.exists(glb_path):
        raise FileNotFoundError(f"Terrain GLB not found: {glb_path}")

    with open(glb_path, "rb") as f:
        f.read(12)
        chunk_len, chunk_type = struct.unpack("<II", f.read(8))
        gltf = json.loads(f.read(chunk_len).decode("utf-8"))
        f.seek(12 + 8 + chunk_len)
        f.read(8)
        binary_data = f.read()

    # Find tinMesh primitive dynamically
    tin_mesh_idx = 0
    for node in gltf.get("nodes", []):
        if node.get("name") == "tinMesh":
            tin_mesh_idx = node.get("mesh", 0)
            break
    tin_prim = gltf["meshes"][tin_mesh_idx]["primitives"][0]
    pos_acc = gltf["accessors"][tin_prim["attributes"]["POSITION"]]
    pos_bv = gltf["bufferViews"][pos_acc["bufferView"]]
    pos_offset = pos_bv.get("byteOffset", 0) + pos_acc.get("byteOffset", 0)
    pos_count = pos_acc["count"]
    raw_verts = np.frombuffer(
        binary_data[pos_offset : pos_offset + pos_count * 12],
        dtype=np.float32
    ).reshape(pos_count, 3)

    idx_acc = gltf["accessors"][tin_prim["indices"]]
    idx_bv = gltf["bufferViews"][idx_acc["bufferView"]]
    idx_offset = idx_bv.get("byteOffset", 0) + idx_acc.get("byteOffset", 0)
    idx_count = idx_acc["count"]
    indices = np.frombuffer(
        binary_data[idx_offset : idx_offset + idx_count * 4],
        dtype=np.uint32
    ).reshape(-1, 3)

    # Apply Godot Terrain Node transform:
    # Scale s = cos(32.573229°), tx = 28057.9043, tz = 16614.8854
    s = 0.8427785648661434
    tx = 28057.9043
    tz = 16614.8854

    world_x = s * raw_verts[:, 0] + tx
    world_y = s * raw_verts[:, 1]
    world_z = s * raw_verts[:, 2] + tz

    bvh_verts = [mathutils.Vector((world_x[i], -world_z[i], world_y[i])) for i in range(pos_count)]
    bvh_polys = [tuple(indices[i]) for i in range(len(indices))]

    print(f"[Terrain] Building BVHTree ({len(bvh_verts):,} verts, {len(bvh_polys):,} tris)...")
    bvh = BVHTree.FromPolygons(bvh_verts, bvh_polys, all_triangles=True)
    print("[Terrain] BVHTree built successfully.")
    return bvh

def get_terrain_z(bvh, x, y):
    """Raycasts straight down from (x, y, 2000m) to sample terrain height."""
    import mathutils
    origin = mathutils.Vector((x, y, 2000.0))
    direction = mathutils.Vector((0.0, 0.0, -1.0))
    hit, normal, index, distance = bvh.ray_cast(origin, direction, 3000.0)
    return hit.z if hit is not None else None

def get_semantic_info(obj):
    """Walks up the parent chain to the top empty under 'OSM2World scene'."""
    curr = obj
    chain = []
    while curr.parent and curr.parent.name != "OSM2World scene":
        curr = curr.parent
        chain.append(curr.name)
    top_name = curr.name
    category = top_name.split()[0] if top_name else "UNKNOWN"
    return top_name, category, chain

def main():
    import bpy
    import mathutils

    args = parse_args()
    print("=" * 80)
    print("CREATING PRE-ADJUSTED OSM2WORLD WORKING COPY")
    print(f"Source blend:   {args.blend_path} (READ-ONLY)")
    print(f"Terrain GLB:    {args.terrain_glb}")
    print(f"Output blend:   {args.output_blend}")
    print(f"Output GLB:     {args.output_glb}")
    print(f"Cull radius:    {args.radius} m")
    print(f"Skirt depth:    {args.skirt_depth} m")
    print("=" * 80)

    # 1. Calibrated horizontal alignment offsets (437-node regression)
    DX = 34976.59
    DY = -31879.03
    MAX_R_SQ = args.radius * args.radius if args.radius > 0 else float("inf")

    # Semantic categories representing 3D physical structures
    RETAIN_CATEGORIES = {
        "Building", "HighVoltagePowerTower", "Tree", "Forest",
        "WindTurbine", "PowerLine", "BusStop"
    }

    # 2. Build terrain BVHTree
    bvh = build_terrain_bvh(args.terrain_glb)

    # 3. Load OSM2World blend file
    print(f"[OSM2World] Loading: {args.blend_path}...")
    if not os.path.exists(args.blend_path):
        raise FileNotFoundError(f"Blend file not found: {args.blend_path}")

    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args.blend_path))

    # Shift root object
    root = bpy.data.objects.get("OSM2World scene")
    if root:
        root.location.x += DX
        root.location.y += DY
        bpy.context.view_layer.update()

    all_meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    print(f"[OSM2World] Total mesh objects loaded: {len(all_meshes):,}")

    objects_to_delete = []
    retained_objects = []
    category_counts = defaultdict(int)

    # Pre-pass: Identify metadata and filter flat 2D categories
    mesh_metadata = {}
    for obj in all_meshes:
        if obj.name in ("Cube", "Camera", "Light") or len(obj.data.vertices) == 0:
            objects_to_delete.append(obj)
            continue

        top_name, category, chain = get_semantic_info(obj)
        if category not in RETAIN_CATEGORIES:
            objects_to_delete.append(obj)
            continue

        mesh_metadata[obj] = (top_name, category, chain)

    print(f"[Filter] 3D structures identified: {len(mesh_metadata):,}. Purging {len(objects_to_delete):,} flat/irrelevant meshes.")

    # Process 3D structures
    t0 = time.time()
    culled_radius = 0
    culled_no_terrain = 0
    processed_count = 0

    # Track naming per parent to create unique part names
    parent_part_counter = defaultdict(int)

    for obj, (top_name, category, chain) in mesh_metadata.items():
        mat = obj.matrix_world.copy()
        world_verts = [mat @ v.co for v in obj.data.vertices]

        # Centroid in world coords
        cx = sum(v.x for v in world_verts) / len(world_verts)
        cy = sum(v.y for v in world_verts) / len(world_verts)

        # Radius check
        if (cx * cx + cy * cy) > MAX_R_SQ:
            objects_to_delete.append(obj)
            culled_radius += 1
            continue

        # Terrain elevation lookup
        terrain_z = get_terrain_z(bvh, cx, cy)
        if terrain_z is None:
            # Check if close to terrain boundary (e.g. within 500m)
            near_loc, near_norm, near_idx, near_dist = bvh.find_nearest(mathutils.Vector((cx, cy, 0.0)))
            if near_dist < 500.0:
                terrain_z = near_loc.z
            else:
                objects_to_delete.append(obj)
                culled_no_terrain += 1
                continue

        # Make mesh unique if shared
        if obj.data.users > 1:
            obj.data = obj.data.copy()

        # Delta from original baseline (Z = -1.0)
        delta_z = (terrain_z - (-1.0)) + args.building_z_offset

        # Find min Z in world coords for foundation skirt calculation
        min_world_z = min(w.z for w in world_verts)

        # Apply elevation and foundation skirts
        for idx, v in enumerate(obj.data.vertices):
            w = world_verts[idx]
            vert_z = w.z + delta_z

            # For buildings, extend ground-level vertices downward by skirt_depth
            if category == "Building" and args.skirt_depth > 0:
                if abs(w.z - min_world_z) < 0.15:
                    vert_z -= args.skirt_depth

            v.co = mathutils.Vector((w.x, w.y, vert_z))

        # Flatten object transforms to world identity
        obj.parent = None
        obj.matrix_world = mathutils.Matrix.Identity(4)
        obj.data.update()

        # Metadata propagation: Rename object with semantic name
        part_idx = parent_part_counter[top_name]
        parent_part_counter[top_name] += 1
        clean_name = top_name.replace(" ", "_")
        new_obj_name = clean_name if part_idx == 0 else f"{clean_name}_part{part_idx}"
        obj.name = new_obj_name
        obj.data.name = f"{new_obj_name}_Mesh"

        # Attach custom properties
        obj["osm_semantic_name"] = top_name
        obj["osm_category"] = category
        obj["osm_chain"] = " -> ".join(chain)
        obj.data["osm_semantic_name"] = top_name
        obj.data["osm_category"] = category

        # Extract OSM ID if present
        for token in top_name.split():
            if (token.startswith("w") or token.startswith("n")) and token[1:].isdigit():
                obj["osm_type"] = "way" if token.startswith("w") else "node"
                obj["osm_id"] = token[1:]
                obj.data["osm_id"] = token[1:]
                break

        retained_objects.append(obj)
        category_counts[category] += 1
        processed_count += 1

    print(f"[Processing] Completed in {time.time() - t0:.2f}s: {processed_count:,} retained ({culled_radius} culled by radius, {culled_no_terrain} out of terrain).")

    # Delete purged objects using native C++ batch removal (sub-second)
    t_clean = time.time()
    print(f"[Cleanup] Removing {len(objects_to_delete):,} culled and flat mesh objects via batch_remove...")
    if objects_to_delete:
        bpy.data.batch_remove(ids=objects_to_delete)

    # Delete all Empty objects
    empty_objs = [o for o in bpy.data.objects if o.type == "EMPTY"]
    print(f"[Cleanup] Removing {len(empty_objs):,} empty hierarchy nodes via batch_remove...")
    if empty_objs:
        bpy.data.batch_remove(ids=empty_objs)
    print(f"[Cleanup] Batch removal completed in {time.time() - t_clean:.2f}s.")

    # Organize into clean Blender Collections
    print("[Organization] Creating semantic collections...")
    collections_map = {
        "Building": "Buildings",
        "HighVoltagePowerTower": "PowerInfrastructure",
        "PowerLine": "PowerInfrastructure",
        "WindTurbine": "PowerInfrastructure",
        "Tree": "Vegetation",
        "Forest": "Vegetation",
        "BusStop": "CivicAmenities",
    }

    created_collections = {}
    for cat_name, coll_name in collections_map.items():
        if coll_name not in created_collections:
            c = bpy.data.collections.get(coll_name)
            if not c:
                c = bpy.data.collections.new(coll_name)
                bpy.context.scene.collection.children.link(c)
            created_collections[coll_name] = c

    # Link objects to appropriate collections
    for obj in retained_objects:
        cat = obj.get("osm_category", "Building")
        target_coll_name = collections_map.get(cat, "Buildings")
        target_coll = created_collections[target_coll_name]

        # Unlink from other collections
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        target_coll.objects.link(obj)

    # Remove default 'Collection' if empty
    default_coll = bpy.data.collections.get("Collection")
    if default_coll and len(default_coll.objects) == 0:
        bpy.data.collections.remove(default_coll)

    # Print summary of retained objects
    print("=" * 80)
    print("RETAINED OBJECTS BY CATEGORY:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:<25}: {count:,} meshes")
    print(f"  {'TOTAL':<25}: {len(retained_objects):,} meshes")
    print("=" * 80)

    # Save adjusted blend file
    output_blend_path = os.path.abspath(args.output_blend)
    os.makedirs(os.path.dirname(output_blend_path), exist_ok=True)
    print(f"[Save] Saving adjusted working copy to: {output_blend_path}...")
    bpy.ops.wm.save_as_mainfile(filepath=output_blend_path, compress=True)
    blend_size_mb = os.path.getsize(output_blend_path) / (1024 * 1024)
    print(f"[Save] Working copy blend file saved: {blend_size_mb:.2f} MB")

    # Export to GLB
    output_glb_path = os.path.abspath(args.output_glb)
    os.makedirs(os.path.dirname(output_glb_path), exist_ok=True)
    print(f"[Export] Exporting clean glTF 2.0 to: {output_glb_path}...")
    t_exp = time.time()
    bpy.ops.export_scene.gltf(
        filepath=output_glb_path,
        export_format="GLB",
        use_selection=False,
        export_apply=False,
        export_yup=True,
        export_materials="EXPORT",
        export_extras=True  # Preserves custom properties (osm_name, osm_id, etc.)
    )
    glb_size_mb = os.path.getsize(output_glb_path) / (1024 * 1024)
    print(f"[Export] glTF export completed in {time.time() - t_exp:.2f}s: {glb_size_mb:.2f} MB")
    print("=" * 80)
    print("ALL OPERATIONS COMPLETED SUCCESSFULLY.")

if __name__ == "__main__":
    main()
