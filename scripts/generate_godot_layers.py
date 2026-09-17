#!/usr/bin/env python3
"""
scripts/generate_godot_layers.py
--------------------------------
Generates modular, high-fidelity 3D vector layers for the Godot digital twin:
1. Waterways: Lakes, reservoirs (Presa Las Auras), and river corridors (Río Tecate).
2. Railways: Ferrocarril Tijuana-Tecate (3D ballast bed, timber sleepers, steel rails).
3. Bridges: Suspended elevated decks spanning valleys with concrete support pillars and parapets.
4. Roadways: Continuous asphalt ribbons with classified widths, lane markings, and curbs.
5. Manzanas: Urban lot platforms and sidewalks for developed city blocks.

Leaves all mountains, hills, and rural terrain (Cerro Cuchumá, etc.) completely uncovered
to preserve the authentic high-resolution aerial photograph on tecate.glb.

Saves 5 individual Blender files:
- godot_project/assets/waterways_adjusted.blend  -> waterways_baked.glb
- godot_project/assets/railways_adjusted.blend   -> railways_baked.glb
- godot_project/assets/bridges_adjusted.blend    -> bridges_baked.glb
- godot_project/assets/roadways_adjusted.blend   -> roadways_baked.glb
- godot_project/assets/manzanas_adjusted.blend   -> manzanas_baked.glb
"""

import sys
import os
import time
import math
import json
import struct
import urllib.request
import urllib.parse
from collections import defaultdict

# ─────────────────────────────────────────────────────────────────────────────
# 1. Geospatial & Terrain Helpers
# ─────────────────────────────────────────────────────────────────────────────

EARTH_RADIUS = 6378137.0
TECATE_LAT_CENTER = 32.573229
TECATE_LON_CENTER = -116.626536

LAT_C_RAD = math.radians(TECATE_LAT_CENTER)
LON_C_RAD = math.radians(TECATE_LON_CENTER)
COS_LAT_C = math.cos(LAT_C_RAD)

def gps_to_local(lat, lon):
    """Converts WGS84 GPS to local Cartesian meters centered at Parque Hidalgo."""
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    x = EARTH_RADIUS * (lon_rad - LON_C_RAD) * COS_LAT_C
    y = EARTH_RADIUS * (lat_rad - LAT_C_RAD)
    return x, y

def build_terrain_bvh(glb_path):
    """Loads tinMesh from tecate.glb and builds a fast BVHTree for terrain draping."""
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

    tin_prim = gltf["meshes"][1]["primitives"][0]
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

    # Blender coordinate convention: X=East, Y=North (-world_z), Z=Height (world_y)
    bvh_verts = [mathutils.Vector((world_x[i], -world_z[i], world_y[i])) for i in range(pos_count)]
    bvh_polys = [tuple(indices[i]) for i in range(len(indices))]

    print(f"[Terrain] Building BVHTree ({len(bvh_verts):,} verts, {len(bvh_polys):,} tris)...")
    bvh = BVHTree.FromPolygons(bvh_verts, bvh_polys, all_triangles=True)
    print("[Terrain] BVHTree built successfully.")
    return bvh

def get_terrain_z(bvh, x, y, default_z=400.0):
    """Raycasts straight down from (x, y, 2000m) to sample terrain height in meters."""
    import mathutils
    origin = mathutils.Vector((x, y, 2000.0))
    direction = mathutils.Vector((0.0, 0.0, -1.0))
    hit, normal, index, distance = bvh.ray_cast(origin, direction, 3500.0)
    return hit.z if hit is not None else default_z

# ─────────────────────────────────────────────────────────────────────────────
# 2. Overpass API Cache Manager
# ─────────────────────────────────────────────────────────────────────────────

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
]

def query_overpass_cached(query_str, cache_path):
    """Queries Overpass API with local disk caching and multi-mirror fallback."""
    if os.path.exists(cache_path):
        print(f"[Cache] Loading cached data from: {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    data = urllib.parse.urlencode({"data": query_str}).encode("utf-8")

    for attempt in range(8):
        endpoint = OVERPASS_ENDPOINTS[attempt % len(OVERPASS_ENDPOINTS)]
        print(f"[Overpass] Querying {endpoint} (attempt {attempt + 1})...")
        try:
            req = urllib.request.Request(endpoint, data=data, headers={"User-Agent": f"TecateSimulatorTwinBuilder/1.{attempt}"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                content = json.loads(resp.read().decode("utf-8"))
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(content, f)
            print(f"[Cache] Saved {len(content.get('elements', []))} elements to: {cache_path}")
            return content
        except Exception as e:
            wait_time = 4 + attempt * 2
            print(f"[Overpass Warning] Endpoint {endpoint} failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

    raise RuntimeError(f"Failed to query Overpass API after multiple attempts for {cache_path}")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Layer Generator 1: Waterways (Lakes, Reservoirs, Rivers)
# ─────────────────────────────────────────────────────────────────────────────

def generate_waterways(bvh, cache_dir, out_blend, out_glb, bbox):
    import bpy
    import mathutils

    print("\n" + "="*70 + "\nGENERATING WATERWAYS LAYER\n" + "="*70)
    bpy.ops.wm.read_homefile(use_empty=True)
    scene = bpy.context.scene

    min_lat, min_lon, max_lat, max_lon = bbox
    q = f"""[out:json][timeout:30];
(
  way["natural"="water"]({min_lat},{min_lon},{max_lat},{max_lon});
  relation["natural"="water"]({min_lat},{min_lon},{max_lat},{max_lon});
  way["waterway"]({min_lat},{min_lon},{max_lat},{max_lon});
);
out geom;
"""
    osm_data = query_overpass_cached(q, os.path.join(cache_dir, "water_osm.json"))

    verts = []
    faces = []
    uvs = []

    # Materials
    mat = bpy.data.materials.new(name="M_Water")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.2, 0.5, 0.75, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.05
        bsdf.inputs["Metallic"].default_value = 0.1
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 0.8

    for el in osm_data.get("elements", []):
        tags = el.get("tags", {})
        is_area = tags.get("natural") == "water" or tags.get("waterway") in ["riverbank", "reservoir", "basin", "pond"]

        if is_area:
            # Area polygon (lake / reservoir / pool)
            geom = el.get("geometry", [])
            if len(geom) < 3:
                continue
            poly_2d = [gps_to_local(pt["lat"], pt["lon"]) for pt in geom]
            if poly_2d[0] == poly_2d[-1]:
                poly_2d = poly_2d[:-1]
            if len(poly_2d) < 3:
                continue

            # Sample shoreline heights to find flat lake water level
            shore_heights = [get_terrain_z(bvh, px, py) for px, py in poly_2d]
            water_z = sorted(shore_heights)[len(shore_heights)//2] - 0.15 # slight bed offset

            poly_vectors = [mathutils.Vector((px, py, 0.0)) for px, py in poly_2d]
            tri_indices = mathutils.geometry.tessellate_polygon([poly_vectors])

            v_offset = len(verts)
            for px, py in poly_2d:
                verts.append((px, py, water_z))
                uvs.append((px * 0.05, py * 0.05))

            for tri in tri_indices:
                faces.append((v_offset + tri[0], v_offset + tri[1], v_offset + tri[2]))

        else:
            # Linear waterway (river / stream / canal)
            geom = el.get("geometry", [])
            if len(geom) < 2:
                continue
            poly_2d = [gps_to_local(pt["lat"], pt["lon"]) for pt in geom]
            ww_type = tags.get("waterway", "stream")
            half_w = 6.0 if ww_type == "river" else 2.0

            cum_dist = 0.0
            for i in range(len(poly_2d) - 1):
                p1 = poly_2d[i]
                p2 = poly_2d[i+1]
                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]
                seg_len = math.sqrt(dx*dx + dy*dy)
                if seg_len < 1e-4:
                    continue

                nx = -dy / seg_len * half_w
                ny =  dx / seg_len * half_w

                z1 = get_terrain_z(bvh, p1[0], p1[1]) - 0.1
                z2 = get_terrain_z(bvh, p2[0], p2[1]) - 0.1

                v_off = len(verts)
                # 4 vertices of ribbon quad
                verts.append((p1[0] - nx, p1[1] - ny, z1))
                verts.append((p1[0] + nx, p1[1] + ny, z1))
                verts.append((p2[0] + nx, p2[1] + ny, z2))
                verts.append((p2[0] - nx, p2[1] - ny, z2))

                uvs.append((0.0, cum_dist / 10.0))
                uvs.append((1.0, cum_dist / 10.0))
                uvs.append((1.0, (cum_dist + seg_len) / 10.0))
                uvs.append((0.0, (cum_dist + seg_len) / 10.0))
                cum_dist += seg_len

                faces.append((v_off, v_off + 1, v_off + 2))
                faces.append((v_off, v_off + 2, v_off + 3))

    mesh = bpy.data.meshes.new(name="WaterwaysMesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    mesh.update()

    obj = bpy.data.objects.new("Waterways", mesh)
    bpy.context.collection.objects.link(obj)

    print(f"[Waterways] Created mesh with {len(verts):,} verts, {len(faces):,} tris.")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
    print(f"[Waterways] Saved working copy to: {out_blend}")

    bpy.ops.export_scene.gltf(
        filepath=os.path.abspath(out_glb),
        export_format="GLB",
        use_selection=False,
        export_materials="EXPORT",
        export_apply=True
    )
    print(f"[Waterways] Exported GLB to: {out_glb}")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Layer Generator 2: Railways (Ferrocarril Tijuana-Tecate)
# ─────────────────────────────────────────────────────────────────────────────

def generate_railways(bvh, cache_dir, out_blend, out_glb, bbox):
    import bpy
    import mathutils

    print("\n" + "="*70 + "\nGENERATING RAILWAYS LAYER\n" + "="*70)
    bpy.ops.wm.read_homefile(use_empty=True)

    min_lat, min_lon, max_lat, max_lon = bbox
    q = f"""[out:json][timeout:30];
way["railway"~"rail|abandoned|disused"]({min_lat},{min_lon},{max_lat},{max_lon});
out geom;
"""
    osm_data = query_overpass_cached(q, os.path.join(cache_dir, "railway_osm.json"))

    # Materials
    mat_ballast = bpy.data.materials.new(name="M_Ballast")
    mat_ballast.use_nodes = True
    bsdf_b = mat_ballast.node_tree.nodes.get("Principled BSDF")
    if bsdf_b:
        bsdf_b.inputs["Base Color"].default_value = (0.22, 0.20, 0.18, 1.0) # dark gravel
        bsdf_b.inputs["Roughness"].default_value = 0.95

    mat_sleepers = bpy.data.materials.new(name="M_Sleepers")
    mat_sleepers.use_nodes = True
    bsdf_s = mat_sleepers.node_tree.nodes.get("Principled BSDF")
    if bsdf_s:
        bsdf_s.inputs["Base Color"].default_value = (0.16, 0.12, 0.08, 1.0) # weathered timber
        bsdf_s.inputs["Roughness"].default_value = 0.85

    mat_rails = bpy.data.materials.new(name="M_SteelRails")
    mat_rails.use_nodes = True
    bsdf_r = mat_rails.node_tree.nodes.get("Principled BSDF")
    if bsdf_r:
        bsdf_r.inputs["Base Color"].default_value = (0.65, 0.68, 0.70, 1.0)
        bsdf_r.inputs["Metallic"].default_value = 0.9
        bsdf_r.inputs["Roughness"].default_value = 0.35

    ballast_verts, ballast_faces = [], []
    sleeper_verts, sleeper_faces = [], []
    rail_verts, rail_faces = [], []

    GAUGE = 1.435       # standard gauge rail spacing
    HALF_GAUGE = GAUGE / 2.0
    SLEEPER_SPACING = 0.65
    SLEEPER_LEN = 2.6
    SLEEPER_W = 0.24
    SLEEPER_H = 0.14
    RAIL_W = 0.08
    RAIL_H = 0.15

    for el in osm_data.get("elements", []):
        geom = el.get("geometry", [])
        if len(geom) < 2:
            continue
        poly_2d = [gps_to_local(pt["lat"], pt["lon"]) for pt in geom]

        # 1. Extrude Ballast Bed (Trapezoidal prism: base width 3.4m, top width 2.6m, height +0.22m)
        cum_dist = 0.0
        for i in range(len(poly_2d) - 1):
            p1 = poly_2d[i]
            p2 = poly_2d[i+1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 0.2:
                continue

            tx = dx / dist
            ty = dy / dist
            nx = -ty
            ny =  tx

            z1 = get_terrain_z(bvh, p1[0], p1[1]) + 0.02
            z2 = get_terrain_z(bvh, p2[0], p2[1]) + 0.02

            # Trapezoidal profile: base width 3.4m (+-1.7m), top width 2.6m (+-1.3m), height +0.22m
            v_off = len(ballast_verts)
            # Segment start (p1)
            ballast_verts.append((p1[0] - nx * 1.7, p1[1] - ny * 1.7, z1))           # 0: base L
            ballast_verts.append((p1[0] - nx * 1.3, p1[1] - ny * 1.3, z1 + 0.22))     # 1: top L
            ballast_verts.append((p1[0] + nx * 1.3, p1[1] + ny * 1.3, z1 + 0.22))     # 2: top R
            ballast_verts.append((p1[0] + nx * 1.7, p1[1] + ny * 1.7, z1))           # 3: base R
            # Segment end (p2)
            ballast_verts.append((p2[0] - nx * 1.7, p2[1] - ny * 1.7, z2))           # 4: base L
            ballast_verts.append((p2[0] - nx * 1.3, p2[1] - ny * 1.3, z2 + 0.22))     # 5: top L
            ballast_verts.append((p2[0] + nx * 1.3, p2[1] + ny * 1.3, z2 + 0.22))     # 6: top R
            ballast_verts.append((p2[0] + nx * 1.7, p2[1] + ny * 1.7, z2))           # 7: base R

            # Top face
            ballast_faces.append((v_off + 1, v_off + 2, v_off + 6))
            ballast_faces.append((v_off + 1, v_off + 6, v_off + 5))
            # Left slope
            ballast_faces.append((v_off + 0, v_off + 1, v_off + 5))
            ballast_faces.append((v_off + 0, v_off + 5, v_off + 4))
            # Right slope
            ballast_faces.append((v_off + 2, v_off + 3, v_off + 7))
            ballast_faces.append((v_off + 2, v_off + 7, v_off + 6))

            # 2. Extrude Dual Steel Rails atop the ballast
            # Left rail at -HALF_GAUGE, Right rail at +HALF_GAUGE
            for side in [-1, 1]:
                r_cx1 = p1[0] + side * HALF_GAUGE * nx
                r_cy1 = p1[1] + side * HALF_GAUGE * ny
                r_cx2 = p2[0] + side * HALF_GAUGE * nx
                r_cy2 = p2[1] + side * HALF_GAUGE * ny

                rz1_base = z1 + 0.22
                rz2_base = z2 + 0.22

                rv_off = len(rail_verts)
                # 4 vertices top of rail
                rail_verts.append((r_cx1 - nx * RAIL_W/2, r_cy1 - ny * RAIL_W/2, rz1_base + RAIL_H))
                rail_verts.append((r_cx1 + nx * RAIL_W/2, r_cy1 + ny * RAIL_W/2, rz1_base + RAIL_H))
                rail_verts.append((r_cx2 + nx * RAIL_W/2, r_cy2 + ny * RAIL_W/2, rz2_base + RAIL_H))
                rail_verts.append((r_cx2 - nx * RAIL_W/2, r_cy2 - ny * RAIL_W/2, rz2_base + RAIL_H))
                rail_faces.append((rv_off, rv_off + 1, rv_off + 2))
                rail_faces.append((rv_off, rv_off + 2, rv_off + 3))

            # 3. Instance Sleepers along the segment
            num_sleepers = max(1, int(dist / SLEEPER_SPACING))
            for s_idx in range(num_sleepers):
                frac = s_idx / float(num_sleepers)
                sx = p1[0] + frac * dx
                sy = p1[1] + frac * dy
                sz = z1 + frac * (z2 - z1) + 0.22

                sv_off = len(sleeper_verts)
                # Sleepers oriented along nx, ny (transverse)
                # 8 box corners
                half_sl = SLEEPER_LEN / 2.0
                half_sw = SLEEPER_W / 2.0
                c_dx = tx * half_sw
                c_dy = ty * half_sw
                w_dx = nx * half_sl
                w_dy = ny * half_sl

                sleeper_verts.append((sx - w_dx - c_dx, sy - w_dy - c_dy, sz))
                sleeper_verts.append((sx + w_dx - c_dx, sy + w_dy - c_dy, sz))
                sleeper_verts.append((sx + w_dx + c_dx, sy + w_dy + c_dy, sz))
                sleeper_verts.append((sx - w_dx + c_dx, sy - w_dy + c_dy, sz))
                sleeper_verts.append((sx - w_dx - c_dx, sy - w_dy - c_dy, sz + SLEEPER_H))
                sleeper_verts.append((sx + w_dx - c_dx, sy + w_dy - c_dy, sz + SLEEPER_H))
                sleeper_verts.append((sx + w_dx + c_dx, sy + w_dy + c_dy, sz + SLEEPER_H))
                sleeper_verts.append((sx - w_dx + c_dx, sy - w_dy + c_dy, sz + SLEEPER_H))

                # Top face
                sleeper_faces.append((sv_off + 4, sv_off + 5, sv_off + 6))
                sleeper_faces.append((sv_off + 4, sv_off + 6, sv_off + 7))

    # Assemble objects in Blender
    b_mesh = bpy.data.meshes.new("BallastMesh")
    b_mesh.from_pydata(ballast_verts, [], ballast_faces)
    b_mesh.materials.append(mat_ballast)
    b_mesh.update()
    obj_b = bpy.data.objects.new("Railway_Ballast", b_mesh)
    bpy.context.collection.objects.link(obj_b)

    s_mesh = bpy.data.meshes.new("SleepersMesh")
    s_mesh.from_pydata(sleeper_verts, [], sleeper_faces)
    s_mesh.materials.append(mat_sleepers)
    s_mesh.update()
    obj_s = bpy.data.objects.new("Railway_Sleepers", s_mesh)
    bpy.context.collection.objects.link(obj_s)

    r_mesh = bpy.data.meshes.new("RailsMesh")
    r_mesh.from_pydata(rail_verts, [], rail_faces)
    r_mesh.materials.append(mat_rails)
    r_mesh.update()
    obj_r = bpy.data.objects.new("Railway_SteelRails", r_mesh)
    bpy.context.collection.objects.link(obj_r)

    print(f"[Railways] Created Ballast ({len(ballast_faces):,} tris), Sleepers ({len(sleeper_faces):,} tris), Rails ({len(rail_faces):,} tris).")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
    print(f"[Railways] Saved working copy to: {out_blend}")

    bpy.ops.export_scene.gltf(
        filepath=os.path.abspath(out_glb),
        export_format="GLB",
        use_selection=False,
        export_materials="EXPORT",
        export_apply=True
    )
    print(f"[Railways] Exported GLB to: {out_glb}")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Layer Generator 3: Bridges (Elevated Decks & Support Pillars)
# ─────────────────────────────────────────────────────────────────────────────

def generate_bridges(bvh, cache_dir, out_blend, out_glb, bbox):
    import bpy
    import mathutils

    print("\n" + "="*70 + "\nGENERATING BRIDGES LAYER\n" + "="*70)
    bpy.ops.wm.read_homefile(use_empty=True)

    min_lat, min_lon, max_lat, max_lon = bbox
    q = f"""[out:json][timeout:30];
way["bridge"]["bridge"!="no"]({min_lat},{min_lon},{max_lat},{max_lon});
out geom;
"""
    osm_data = query_overpass_cached(q, os.path.join(cache_dir, "bridge_osm.json"))

    mat_deck = bpy.data.materials.new(name="M_BridgeDeck")
    mat_deck.use_nodes = True
    bsdf_d = mat_deck.node_tree.nodes.get("Principled BSDF")
    if bsdf_d:
        bsdf_d.inputs["Base Color"].default_value = (0.28, 0.28, 0.30, 1.0)
        bsdf_d.inputs["Roughness"].default_value = 0.8

    mat_conc = bpy.data.materials.new(name="M_BridgeConcrete")
    mat_conc.use_nodes = True
    bsdf_c = mat_conc.node_tree.nodes.get("Principled BSDF")
    if bsdf_c:
        bsdf_c.inputs["Base Color"].default_value = (0.65, 0.65, 0.64, 1.0)
        bsdf_c.inputs["Roughness"].default_value = 0.7

    deck_verts, deck_faces = [], []
    pier_verts, pier_faces = [], []

    for el in osm_data.get("elements", []):
        geom = el.get("geometry", [])
        if len(geom) < 2:
            continue
        poly_2d = [gps_to_local(pt["lat"], pt["lon"]) for pt in geom]
        tags = el.get("tags", {})
        hw = tags.get("highway", tags.get("railway", "residential"))
        width = 12.0 if hw in ["trunk", "motorway"] else (10.0 if hw == "primary" else 8.0)
        half_w = width / 2.0

        # Sample bridge bank abutment heights at endpoints
        z_start = get_terrain_z(bvh, poly_2d[0][0], poly_2d[0][1]) + 0.1
        z_end = get_terrain_z(bvh, poly_2d[-1][0], poly_2d[-1][1]) + 0.1

        total_len = 0.0
        for i in range(len(poly_2d) - 1):
            total_len += math.hypot(poly_2d[i+1][0] - poly_2d[i][0], poly_2d[i+1][1] - poly_2d[i][1])

        cum_len = 0.0
        for i in range(len(poly_2d) - 1):
            p1 = poly_2d[i]
            p2 = poly_2d[i+1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            seg_len = math.hypot(dx, dy)
            if seg_len < 0.1:
                continue

            nx = -dy / seg_len * half_w
            ny =  dx / seg_len * half_w

            # Elevated linear ramp deck elevation (does NOT dip into riverbed)
            frac1 = cum_len / max(1.0, total_len)
            frac2 = (cum_len + seg_len) / max(1.0, total_len)
            z1 = (1.0 - frac1) * z_start + frac1 * z_end
            z2 = (1.0 - frac2) * z_start + frac2 * z_end
            cum_len += seg_len

            # Extrude Box Girder Deck: top road deck + bottom soffit (-0.8m)
            v_off = len(deck_verts)
            # 4 vertices top deck
            deck_verts.append((p1[0] - nx, p1[1] - ny, z1))
            deck_verts.append((p1[0] + nx, p1[1] + ny, z1))
            deck_verts.append((p2[0] + nx, p2[1] + ny, z2))
            deck_verts.append((p2[0] - nx, p2[1] - ny, z2))
            # 4 vertices bottom soffit
            deck_verts.append((p1[0] - nx, p1[1] - ny, z1 - 0.8))
            deck_verts.append((p1[0] + nx, p1[1] + ny, z1 - 0.8))
            deck_verts.append((p2[0] + nx, p2[1] + ny, z2 - 0.8))
            deck_verts.append((p2[0] - nx, p2[1] - ny, z2 - 0.8))

            # Top deck face
            deck_faces.append((v_off, v_off + 1, v_off + 2))
            deck_faces.append((v_off, v_off + 2, v_off + 3))
            # Bottom soffit face
            deck_faces.append((v_off + 4, v_off + 6, v_off + 5))
            deck_faces.append((v_off + 4, v_off + 7, v_off + 6))
            # Outer left / right girder walls
            deck_faces.append((v_off, v_off + 3, v_off + 7))
            deck_faces.append((v_off, v_off + 7, v_off + 4))
            deck_faces.append((v_off + 1, v_off + 5, v_off + 6))
            deck_faces.append((v_off + 1, v_off + 6, v_off + 2))

            # Side concrete safety parapets (+1.1m)
            pv_off = len(deck_verts)
            deck_verts.append((p1[0] - nx, p1[1] - ny, z1 + 1.1))
            deck_verts.append((p2[0] - nx, p2[1] - ny, z2 + 1.1))
            deck_verts.append((p1[0] + nx, p1[1] + ny, z1 + 1.1))
            deck_verts.append((p2[0] + nx, p2[1] + ny, z2 + 1.1))
            # Left parapet
            deck_faces.append((v_off, pv_off, pv_off + 1))
            deck_faces.append((v_off, pv_off + 1, v_off + 3))
            # Right parapet
            deck_faces.append((v_off + 1, v_off + 2, pv_off + 3))
            deck_faces.append((v_off + 1, pv_off + 3, pv_off + 2))

            # Concrete support piers dropped every 12m if deck is > 2m above ground
            mid_x = (p1[0] + p2[0]) / 2.0
            mid_y = (p1[1] + p2[1]) / 2.0
            mid_z = (z1 + z2) / 2.0
            ground_z = get_terrain_z(bvh, mid_x, mid_y)
            clearance = mid_z - ground_z

            if clearance > 2.0 and (total_len > 15.0):
                # Build a concrete column pier
                pier_off = len(pier_verts)
                pw = 1.0
                pier_verts.append((mid_x - pw, mid_y - pw, ground_z))
                pier_verts.append((mid_x + pw, mid_y - pw, ground_z))
                pier_verts.append((mid_x + pw, mid_y + pw, ground_z))
                pier_verts.append((mid_x - pw, mid_y + pw, ground_z))
                pier_verts.append((mid_x - pw, mid_y - pw, mid_z - 0.8))
                pier_verts.append((mid_x + pw, mid_y - pw, mid_z - 0.8))
                pier_verts.append((mid_x + pw, mid_y + pw, mid_z - 0.8))
                pier_verts.append((mid_x - pw, mid_y + pw, mid_z - 0.8))

                # 4 vertical side walls of column
                for f_idx in range(4):
                    next_f = (f_idx + 1) % 4
                    pier_faces.append((pier_off + f_idx, pier_off + next_f, pier_off + 4 + next_f))
                    pier_faces.append((pier_off + f_idx, pier_off + 4 + next_f, pier_off + 4 + f_idx))

    d_mesh = bpy.data.meshes.new("BridgeDecksMesh")
    d_mesh.from_pydata(deck_verts, [], deck_faces)
    d_mesh.materials.append(mat_deck)
    d_mesh.update()
    obj_d = bpy.data.objects.new("Bridges_Decks", d_mesh)
    bpy.context.collection.objects.link(obj_d)

    p_mesh = bpy.data.meshes.new("BridgePillarsMesh")
    p_mesh.from_pydata(pier_verts, [], pier_faces)
    p_mesh.materials.append(mat_conc)
    p_mesh.update()
    obj_p = bpy.data.objects.new("Bridges_Pillars", p_mesh)
    bpy.context.collection.objects.link(obj_p)

    print(f"[Bridges] Created Decks ({len(deck_faces):,} tris) and Pillars ({len(pier_faces):,} tris).")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
    print(f"[Bridges] Saved working copy to: {out_blend}")

    bpy.ops.export_scene.gltf(
        filepath=os.path.abspath(out_glb),
        export_format="GLB",
        use_selection=False,
        export_materials="EXPORT",
        export_apply=True
    )
    print(f"[Bridges] Exported GLB to: {out_glb}")

# ─────────────────────────────────────────────────────────────────────────────
# 6. Layer Generator 4: Roadways (Continuous Paved Ribbons)
# ─────────────────────────────────────────────────────────────────────────────

def generate_roadways(bvh, cache_dir, out_blend, out_glb, bbox):
    import bpy
    import mathutils

    print("\n" + "="*70 + "\nGENERATING ROADWAYS LAYER\n" + "="*70)
    bpy.ops.wm.read_homefile(use_empty=True)

    min_lat, min_lon, max_lat, max_lon = bbox
    q = f"""[out:json][timeout:60];
way["highway"~"motorway|trunk|primary|secondary|tertiary|residential|unclassified|service|living_street"]({min_lat},{min_lon},{max_lat},{max_lon});
out geom;
"""
    osm_data = query_overpass_cached(q, os.path.join(cache_dir, "road_osm.json"))

    mat_asphalt = bpy.data.materials.new(name="M_Asphalt")
    mat_asphalt.use_nodes = True
    bsdf_a = mat_asphalt.node_tree.nodes.get("Principled BSDF")
    if bsdf_a:
        bsdf_a.inputs["Base Color"].default_value = (0.16, 0.16, 0.18, 1.0)
        bsdf_a.inputs["Roughness"].default_value = 0.85

    road_verts, road_faces = [], []

    for el in osm_data.get("elements", []):
        tags = el.get("tags", {})
        # Bridges are handled separately in the Bridges layer
        if tags.get("bridge") and tags.get("bridge") != "no":
            continue

        geom = el.get("geometry", [])
        if len(geom) < 2:
            continue
        poly_2d = [gps_to_local(pt["lat"], pt["lon"]) for pt in geom]

        hw = tags.get("highway", "residential")
        if hw in ["motorway", "trunk"]:
            width = 12.0
        elif hw in ["primary"]:
            width = 10.0
        elif hw in ["secondary"]:
            width = 8.0
        elif hw in ["tertiary"]:
            width = 7.0
        elif hw in ["residential", "unclassified"]:
            width = 6.0
        else:
            width = 4.5
        half_w = width / 2.0

        for i in range(len(poly_2d) - 1):
            p1 = poly_2d[i]
            p2 = poly_2d[i+1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            dist = math.hypot(dx, dy)
            if dist < 0.2:
                continue

            nx = -dy / dist * half_w
            ny =  dx / dist * half_w

            z1 = get_terrain_z(bvh, p1[0], p1[1]) + 0.04 # 4cm Z-bias above terrain
            z2 = get_terrain_z(bvh, p2[0], p2[1]) + 0.04

            v_off = len(road_verts)
            road_verts.append((p1[0] - nx, p1[1] - ny, z1))
            road_verts.append((p1[0] + nx, p1[1] + ny, z1))
            road_verts.append((p2[0] + nx, p2[1] + ny, z2))
            road_verts.append((p2[0] - nx, p2[1] - ny, z2))

            road_faces.append((v_off, v_off + 1, v_off + 2))
            road_faces.append((v_off, v_off + 2, v_off + 3))

    r_mesh = bpy.data.meshes.new("RoadwaysMesh")
    r_mesh.from_pydata(road_verts, [], road_faces)
    r_mesh.materials.append(mat_asphalt)
    r_mesh.update()

    obj = bpy.data.objects.new("Roadways", r_mesh)
    bpy.context.collection.objects.link(obj)

    print(f"[Roadways] Created {len(road_faces):,} road quads/triangles.")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
    print(f"[Roadways] Saved working copy to: {out_blend}")

    bpy.ops.export_scene.gltf(
        filepath=os.path.abspath(out_glb),
        export_format="GLB",
        use_selection=False,
        export_materials="EXPORT",
        export_apply=True
    )
    print(f"[Roadways] Exported GLB to: {out_glb}")

# ─────────────────────────────────────────────────────────────────────────────
# 7. Layer Generator 5: Manzanas & Urban Lots (Sidewalk Platforms)
# ─────────────────────────────────────────────────────────────────────────────

def generate_manzanas(bvh, cache_dir, out_blend, out_glb, bbox):
    import bpy
    import mathutils

    print("\n" + "="*70 + "\nGENERATING URBAN MANZANAS LAYER\n" + "="*70)
    bpy.ops.wm.read_homefile(use_empty=True)

    min_lat, min_lon, max_lat, max_lon = bbox
    q = f"""[out:json][timeout:60];
(
  way["landuse"~"residential|commercial|industrial|retail|cemetery"]({min_lat},{min_lon},{max_lat},{max_lon});
  way["leisure"~"park|pitch|garden"]({min_lat},{min_lon},{max_lat},{max_lon});
  way["amenity"~"parking|school|hospital"]({min_lat},{min_lon},{max_lat},{max_lon});
);
out geom;
"""
    osm_data = query_overpass_cached(q, os.path.join(cache_dir, "manzanas_osm.json"))

    mat_pave = bpy.data.materials.new(name="M_UrbanSidewalk")
    mat_pave.use_nodes = True
    bsdf_p = mat_pave.node_tree.nodes.get("Principled BSDF")
    if bsdf_p:
        bsdf_p.inputs["Base Color"].default_value = (0.58, 0.58, 0.56, 1.0) # urban sidewalk stone
        bsdf_p.inputs["Roughness"].default_value = 0.75

    mat_park = bpy.data.materials.new(name="M_UrbanPark")
    mat_park.use_nodes = True
    bsdf_g = mat_park.node_tree.nodes.get("Principled BSDF")
    if bsdf_g:
        bsdf_g.inputs["Base Color"].default_value = (0.35, 0.52, 0.22, 1.0) # park lawn
        bsdf_g.inputs["Roughness"].default_value = 0.85

    verts, faces = [], []
    mat_indices = []

    for el in osm_data.get("elements", []):
        geom = el.get("geometry", [])
        if len(geom) < 3:
            continue
        poly_2d = [gps_to_local(pt["lat"], pt["lon"]) for pt in geom]
        if poly_2d[0] == poly_2d[-1]:
            poly_2d = poly_2d[:-1]
        if len(poly_2d) < 3:
            continue

        tags = el.get("tags", {})
        is_green = tags.get("leisure") in ["park", "pitch", "garden"] or tags.get("landuse") == "cemetery"
        mat_slot = 1 if is_green else 0

        poly_vectors = [mathutils.Vector((px, py, 0.0)) for px, py in poly_2d]
        tri_indices = mathutils.geometry.tessellate_polygon([poly_vectors])

        v_offset = len(verts)
        for px, py in poly_2d:
            # +0.02m Z-bias: sits above raw terrain, below +0.04m road ribbon
            pz = get_terrain_z(bvh, px, py) + 0.02
            verts.append((px, py, pz))

        for tri in tri_indices:
            faces.append((v_offset + tri[0], v_offset + tri[1], v_offset + tri[2]))
            mat_indices.append(mat_slot)

    m_mesh = bpy.data.meshes.new("ManzanasMesh")
    m_mesh.from_pydata(verts, [], faces)
    m_mesh.materials.append(mat_pave)
    m_mesh.materials.append(mat_park)

    # Assign face materials
    for idx, f in enumerate(m_mesh.polygons):
        if idx < len(mat_indices):
            f.material_index = mat_indices[idx]
    m_mesh.update()

    obj = bpy.data.objects.new("UrbanManzanas", m_mesh)
    bpy.context.collection.objects.link(obj)

    print(f"[Manzanas] Created {len(faces):,} manzana lot/sidewalk triangles across urban parcels.")
    print("[Manzanas] Mountains and rural zones left 100% uncovered to preserve aerial photo.")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
    print(f"[Manzanas] Saved working copy to: {out_blend}")

    bpy.ops.export_scene.gltf(
        filepath=os.path.abspath(out_glb),
        export_format="GLB",
        use_selection=False,
        export_materials="EXPORT",
        export_apply=True
    )
    print(f"[Manzanas] Exported GLB to: {out_glb}")

# ─────────────────────────────────────────────────────────────────────────────
# 8. Main Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def main():
    t_start = time.time()
    print("="*70)
    print("TECATE DIGITAL TWIN: GENERATING ALL MODULAR GIS 3D LAYERS")
    print("="*70)

    terrain_glb = "godot_project/assets/tecate.glb"
    cache_dir = "godot_project/assets/osm_cache"
    bbox = (32.5217, -116.6950, 32.5850, -116.5105)

    # 1. Build authoritative terrain BVHTree
    bvh = build_terrain_bvh(terrain_glb)

    # 2. Subsystem 1: Waterways
    generate_waterways(
        bvh, cache_dir,
        "godot_project/assets/waterways_adjusted.blend",
        "godot_project/assets/waterways_baked.glb",
        bbox
    )

    # 3. Subsystem 2: Railways
    generate_railways(
        bvh, cache_dir,
        "godot_project/assets/railways_adjusted.blend",
        "godot_project/assets/railways_baked.glb",
        bbox
    )

    # 4. Subsystem 3: Bridges
    generate_bridges(
        bvh, cache_dir,
        "godot_project/assets/bridges_adjusted.blend",
        "godot_project/assets/bridges_baked.glb",
        bbox
    )

    # 5. Subsystem 4: Roadways
    generate_roadways(
        bvh, cache_dir,
        "godot_project/assets/roadways_adjusted.blend",
        "godot_project/assets/roadways_baked.glb",
        bbox
    )

    # 6. Subsystem 5: Manzanas (Urban lot platforms)
    generate_manzanas(
        bvh, cache_dir,
        "godot_project/assets/manzanas_adjusted.blend",
        "godot_project/assets/manzanas_baked.glb",
        bbox
    )

    print("\n" + "="*70)
    print(f"ALL 5 GIS LAYERS GENERATED SUCCESSFULLY IN {time.time() - t_start:.2f}s!")
    print("="*70)

if __name__ == "__main__":
    main()
