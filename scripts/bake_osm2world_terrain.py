#!/usr/bin/env python3
"""
bake_osm2world_terrain.py

Unifies OSM2World alignment and terrain height baking into an offline pipeline:
1. Loads tecate.glb TIN terrain and builds a high-speed BVHTree.
2. Loads models/tecate/osm2world.blend in read-only mode (never modified).
3. Translates objects horizontally to align Parque Hidalgo to (0, 0):
   dx = +34865.68 m, dy = -31820.16 m.
4. Bakes elevation directly into world coordinates on object geometry:
   - Rigid objects (Buildings, Towers, Trees, Props): raycasts foundation centroid
     and elevates rigidly so the building base rests snugly on the ground.
   - Ground/linear networks (Roads, Junctions, Railways, Waterways): drapes vertices
     smoothly onto the terrain surface, preserving bridge/ramp clearance.
5. Applies world transforms directly into mesh vertices and flattens node hierarchy.
6. Culls out-of-bounds geometry beyond the specified radius or terrain bounds.
7. Exports a single optimized, prebaked GLB for Godot Engine.
"""

import sys
import os
import argparse
import json
import struct
import math
import time

def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = argv[1:]

    parser = argparse.ArgumentParser(description="Prebake OSM2World alignment and elevation onto Tecate terrain.")
    parser.add_argument("--blend-path", default="blender_assets/osm2world_adjusted.blend", help="Input OSM2World blend file")
    parser.add_argument("--terrain-glb", default="godot_project/assets/tecate.glb", help="Input terrain GLB file")
    parser.add_argument("--output-glb", default="godot_project/assets/osm2world_baked.glb", help="Output baked GLB file")
    parser.add_argument("--radius", type=float, default=3000.0, help="Culling radius in meters from Parque Hidalgo (-1 for all)")
    parser.add_argument("--road-z-offset", type=float, default=0.08, help="Z offset in meters for draped road surfaces")
    parser.add_argument("--building-z-offset", type=float, default=0.0, help="Additional Z offset in meters for buildings")
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

    mesh = gltf["meshes"][1]  # mesh 1 is tinMesh
    prim = mesh["primitives"][0]
    pos_idx = prim["attributes"]["POSITION"]
    ind_idx = prim["indices"]

    pos_acc = gltf["accessors"][pos_idx]
    pos_bv = gltf["bufferViews"][pos_acc["bufferView"]]
    pos_offset = pos_bv.get("byteOffset", 0) + pos_acc.get("byteOffset", 0)
    pos_count = pos_acc["count"]
    positions = np.frombuffer(binary_data[pos_offset:pos_offset + pos_count * 12], dtype=np.float32).reshape(pos_count, 3)

    ind_acc = gltf["accessors"][ind_idx]
    ind_bv = gltf["bufferViews"][ind_acc["bufferView"]]
    ind_offset = ind_bv.get("byteOffset", 0) + ind_acc.get("byteOffset", 0)
    ind_count = ind_acc["count"]
    indices = np.frombuffer(binary_data[ind_offset:ind_offset + ind_count * 4], dtype=np.uint32).reshape(-1, 3)

    # Calibrated terrain alignment constants
    s = 0.8427785648661434
    tx = 28052.404303473268
    tz = -16620.3853885848

    x_loc = s * positions[:, 0] + tx
    y_loc = s * (-positions[:, 2]) + tz
    z_loc = s * positions[:, 1]

    verts = [mathutils.Vector((x_loc[i], y_loc[i], z_loc[i])) for i in range(len(positions))]
    polys = [tuple(tri) for tri in indices]

    print(f"[Terrain] Building BVHTree from {len(verts):,} vertices and {len(polys):,} triangles...")
    t0 = time.time()
    bvh = BVHTree.FromPolygons(verts, polys)
    print(f"[Terrain] BVHTree built in {time.time() - t0:.2f}s")
    return bvh

def get_terrain_z(bvh, x, y, default=None):
    """Raycasts vertically downward to find the terrain surface Z coordinate at (x, y)."""
    import mathutils
    ray_origin = mathutils.Vector((x, y, 3000.0))
    ray_dir = mathutils.Vector((0.0, 0.0, -1.0))
    hit, _, _, _ = bvh.ray_cast(ray_origin, ray_dir)
    if hit:
        return hit.z
    return default

def bake_scene(args):
    import bpy
    import mathutils

    # Exact geometric alignment centered at Parque Miguel Hidalgo (32.573229°N, -116.626536°W)
    # Calibrated across 437 OSM road junctions within 1 km of the city center:
    # (Mean residual error: 2.75m / Median: 2.50m across all downtown intersections)
    # Resolves the ~24m SW offset caused by asymmetric park perimeter nodes.
    DX = 34976.59
    DY = -31879.03
    MAX_R_SQ = args.radius * args.radius if args.radius > 0 else float("inf")

    # 1. Build terrain BVHTree
    bvh = build_terrain_bvh(args.terrain_glb)

    # 2. Open OSM2World blend file
    print(f"[OSM2World] Loading: {args.blend_path} (READ-ONLY)")
    if not os.path.exists(args.blend_path):
        raise FileNotFoundError(f"Blend file not found: {args.blend_path}")

    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args.blend_path))

    # Apply horizontal shift to root object
    root = bpy.data.objects.get("OSM2World scene")
    if root:
        root.location.x += DX
        root.location.y += DY
        bpy.context.view_layer.update()

    # Classification lists
    RIGID_PREFIXES = (
        "Building", "Tree", "HighVoltagePowerTower", "WindTurbine",
        "TrafficSignGroup", "AreaFountain", "PoleFence", "Helipad", "BusStop"
    )

    objects_to_delete = []
    mesh_objects = [o for o in bpy.data.objects if o.type == "MESH"]
    print(f"[OSM2World] Total mesh objects in blend: {len(mesh_objects):,}")

    t0 = time.time()
    rigid_count = 0
    continuous_count = 0
    culled_count = 0
    for obj in mesh_objects:
        # Purge default Blender startup items or unshaded billboard trees/forests
        if obj.name in ("Cube", "Camera", "Light") or obj.name.startswith("Tree_") or obj.name.startswith("Forest_"):
            objects_to_delete.append(obj)
            continue

        if len(obj.data.vertices) == 0:
            objects_to_delete.append(obj)
            continue

        mat = obj.matrix_world.copy()
        
        # Determine centroid in shifted world coordinates
        world_verts = [mat @ v.co for v in obj.data.vertices]
        cx = sum(v.x for v in world_verts) / len(world_verts)
        cy = sum(v.y for v in world_verts) / len(world_verts)

        # Radius filter
        dist_sq = cx * cx + cy * cy
        if dist_sq > MAX_R_SQ:
            objects_to_delete.append(obj)
            culled_count += 1
            continue

        # Check category by tracing parent hierarchy
        cat_name = obj.name
        curr = obj
        while curr.parent and curr.parent != root:
            curr = curr.parent
            cat_name = curr.name

        is_rigid = any(cat_name.startswith(p) for p in RIGID_PREFIXES)

        # Ensure mesh datablock is unique before modifying vertices
        if obj.data.users > 1:
            obj.data = obj.data.copy()

        # Check if vertices are already draped on terrain (Z > 200m in Tecate)
        is_already_draped = any(w.z > 200.0 for w in world_verts)

        if is_already_draped:
            for idx, v in enumerate(obj.data.vertices):
                v.co = world_verts[idx]
            if is_rigid:
                rigid_count += 1
            else:
                continuous_count += 1
        elif is_rigid:
            terrain_z = get_terrain_z(bvh, cx, cy)
            if terrain_z is None:
                objects_to_delete.append(obj)
                culled_count += 1
                continue

            # Original baseline is Z = -1.0
            delta_z = (terrain_z - (-1.0)) + args.building_z_offset
            for idx, v in enumerate(obj.data.vertices):
                w = world_verts[idx]
                v.co = mathutils.Vector((w.x, w.y, w.z + delta_z))

            rigid_count += 1
        else:
            valid_hits = 0
            for idx, v in enumerate(obj.data.vertices):
                w = world_verts[idx]
                t_z = get_terrain_z(bvh, w.x, w.y)
                if t_z is not None:
                    valid_hits += 1
                    rel_h = w.z - (-1.0)
                    new_z = t_z + rel_h + args.road_z_offset
                    v.co = mathutils.Vector((w.x, w.y, new_z))
                else:
                    v.co = w

            if valid_hits == 0:
                objects_to_delete.append(obj)
                culled_count += 1
                continue

            continuous_count += 1

        # Flatten object transform so vertices are strictly in world coordinates
        obj.parent = None
        obj.matrix_world = mathutils.Matrix.Identity(4)
        obj.data.update()

    print(f"[Bake] Processed objects: {rigid_count} rigid, {continuous_count} continuous, {culled_count} culled in {time.time() - t0:.2f}s")

    # Remove culled objects
    print(f"[Cleanup] Removing {len(objects_to_delete):,} culled mesh objects...")
    for obj in objects_to_delete:
        bpy.data.objects.remove(obj, do_unlink=True)

    # Clean up empty objects
    empty_objs = [o for o in bpy.data.objects if o.type == "EMPTY"]
    for o in empty_objs:
        bpy.data.objects.remove(o, do_unlink=True)

    # Export to GLB
    output_path = os.path.abspath(args.output_glb)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"[Export] Exporting baked scene to: {output_path}")

    t_exp = time.time()
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format="GLB",
        use_selection=False,
        export_apply=True,
        export_materials="EXPORT",
        export_yup=True
    )
    print(f"[Export] GLB export completed in {time.time() - t_exp:.2f}s")
    print(f"[Export] Output file size: {os.path.getsize(output_path) / (1024 * 1024):.2f} MB")

def main():
    args = parse_args()
    bake_scene(args)

if __name__ == "__main__":
    main()
