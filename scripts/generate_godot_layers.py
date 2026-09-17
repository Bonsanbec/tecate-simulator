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

def point_in_poly(x, y, poly):
    """Raycasting algorithm to test if point (x, y) is inside 2D polygon."""
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y) and y <= max(p1y, p2y):
            if x <= max(p1x, p2x):
                if p1y != p2y:
                    xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                if p1x == p2x or x <= xinters:
                    inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def get_normalized_street_name(name):
    """Normalizes street name by stripping diacritics, prefixes and punctuation."""
    if not name:
        return ""
    import unicodedata
    name_ascii = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower().strip()
    words = name_ascii.split()
    filtered_words = []
    ignored_words = {
        "calle", "callejon", "avenida", "av", "boulevard", "blvd", "blvrd",
        "carretera", "carr", "camino", "privada", "calzada", "presidente", "pdte"
    }
    for w in words:
        w_clean = "".join(c for c in w if c.isalnum())
        if w_clean not in ignored_words and w_clean != "":
            filtered_words.append(w_clean)
    return " ".join(filtered_words).strip()

def resolve_road_properties(name, highway_type, footway_type=None):
    """
    Classifies road according to Minecraft pipeline rules:
    returns width, surface, is_rural, marking_type, is_pedestrian.
    """
    hw = highway_type or "residential"
    fw = footway_type or ""
    name_norm = (name or "").lower().strip()

    is_pedestrian = (hw in ["footway", "steps", "pedestrian", "path"] or fw in ["sidewalk", "crossing"])
    if is_pedestrian:
        return {
            "width": 1.8 if (fw == "sidewalk" or hw in ["footway", "steps"]) else 2.5,
            "surface": "concrete",
            "is_rural": False,
            "marking_type": "none",
            "is_pedestrian": True
        }

    is_expressway = (
        "carr" in name_norm or
        "carretera" in name_norm or
        "autop" in name_norm or
        "autopista" in name_norm or
        hw in ["motorway", "motorway_link", "trunk", "trunk_link"]
    )
    is_blvd = ("blvd" in name_norm or "boulevard" in name_norm or "blvrd" in name_norm)
    is_avenida = ("av" in name_norm or "avenida" in name_norm or "paseo" in name_norm)
    is_calle = ("calle" in name_norm or "callejon" in name_norm or "privada" in name_norm or "calzada" in name_norm)
    is_unnamed_minor = (not name_norm and hw in ["unclassified", "service", "living_street", "track", "path", "bridleway"])

    if is_expressway:
        width = 12.0
        lanes = 4
        surface = "asphalt"
        is_rural = False
        marking_type = "highway"
    elif is_blvd:
        width = 14.0
        lanes = 4
        surface = "asphalt_clean"
        is_rural = False
        marking_type = "boulevard"
    elif is_avenida:
        width = 9.0
        lanes = 2
        surface = "asphalt"
        is_rural = False
        marking_type = "avenida"
    elif is_unnamed_minor:
        width = 4.0
        lanes = 1
        surface = "gravel"
        is_rural = True
        marking_type = "none"
    elif is_calle:
        width = 6.0
        lanes = 2
        surface = "asphalt_light"
        is_rural = False
        marking_type = "calle"
    else:
        if hw in ["primary", "primary_link"]:
            width = 10.0
            surface = "asphalt"
            is_rural = False
            marking_type = "avenida"
        elif hw in ["secondary", "secondary_link"]:
            width = 8.0
            surface = "asphalt"
            is_rural = False
            marking_type = "calle"
        elif hw in ["tertiary", "tertiary_link"]:
            width = 7.0
            surface = "asphalt"
            is_rural = False
            marking_type = "calle"
        else:
            width = 6.0
            surface = "asphalt"
            is_rural = False
            marking_type = "calle"

    return {
        "width": width,
        "surface": surface,
        "is_rural": is_rural,
        "marking_type": marking_type,
        "is_pedestrian": False
    }

# ─────────────────────────────────────────────────────────────────────────────
# 3. Layer Generator 1: Waterways (Lakes, Reservoirs, Rivers & Dams)
# ─────────────────────────────────────────────────────────────────────────────

def generate_waterways(bvh, cache_dir, out_blend, out_glb, bbox):
    import bpy
    import mathutils

    print("\n" + "="*70 + "\nGENERATING WATERWAYS LAYER\n" + "="*70)
    bpy.ops.wm.read_homefile(use_empty=True)

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
    mat_indices = []

    # Materials
    mat_water = bpy.data.materials.new(name="M_Water")
    mat_water.use_nodes = True
    bsdf_w = mat_water.node_tree.nodes.get("Principled BSDF")
    if bsdf_w:
        bsdf_w.inputs["Base Color"].default_value = (0.15, 0.45, 0.70, 1.0)
        bsdf_w.inputs["Roughness"].default_value = 0.08
        bsdf_w.inputs["Metallic"].default_value = 0.05
        if "Transmission Weight" in bsdf_w.inputs:
            bsdf_w.inputs["Transmission Weight"].default_value = 0.85

    mat_dam = bpy.data.materials.new(name="M_DamConcrete")
    mat_dam.use_nodes = True
    bsdf_d = mat_dam.node_tree.nodes.get("Principled BSDF")
    if bsdf_d:
        bsdf_d.inputs["Base Color"].default_value = (0.65, 0.65, 0.62, 1.0)
        bsdf_d.inputs["Roughness"].default_value = 0.75

    for el in osm_data.get("elements", []):
        tags = el.get("tags", {})
        is_area = tags.get("natural") == "water" or tags.get("waterway") in ["riverbank", "reservoir", "basin", "pond"]
        is_dam = tags.get("waterway") == "dam"

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

            # Check if this is a large reservoir (like Presa Las Auras)
            shore_heights = [get_terrain_z(bvh, px, py) for px, py in poly_2d]
            median_shore = sorted(shore_heights)[len(shore_heights)//2]

            xs = [p[0] for p in poly_2d]
            ys = [p[1] for p in poly_2d]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            span = max(max_x - min_x, max_y - min_y)

            # Build 2D Delaunay mesh with internal points for smooth bed fitting
            pts = [mathutils.Vector((p[0], p[1])) for p in poly_2d]
            edges = [(i, (i + 1) % len(poly_2d)) for i in range(len(poly_2d))]

            grid_step = 12.0 if span > 100.0 else 6.0
            grid_pts = []
            if span > 15.0:
                for gx in [min_x + i * grid_step for i in range(int((max_x - min_x) / grid_step) + 1)]:
                    for gy in [min_y + j * grid_step for j in range(int((max_y - min_y) / grid_step) + 1)]:
                        if point_in_poly(gx, gy, poly_2d):
                            grid_pts.append(mathutils.Vector((gx, gy)))

            all_pts = pts + grid_pts
            try:
                res = mathutils.geometry.delaunay_2d_cdt(all_pts, edges, [], 0, 1e-4)
                out_pts, out_edges, out_faces, _, _, _ = res

                v_offset = len(verts)
                # Compute elevation: water level is flat up to median shoreline, with a subtle Z bias
                for pt_idx, opt in enumerate(out_pts):
                    terr_z = get_terrain_z(bvh, opt.x, opt.y)
                    # For reservoirs and ponds, water stays horizontal or at bed level if higher
                    wz = max(median_shore, terr_z + 0.05)
                    verts.append((opt.x, opt.y, wz))
                    uvs.append((opt.x * 0.05, opt.y * 0.05))

                for f in out_faces:
                    cx = (out_pts[f[0]].x + out_pts[f[1]].x + out_pts[f[2]].x) / 3.0
                    cy = (out_pts[f[0]].y + out_pts[f[1]].y + out_pts[f[2]].y) / 3.0
                    if point_in_poly(cx, cy, poly_2d):
                        faces.append((v_offset + f[0], v_offset + f[1], v_offset + f[2]))
                        mat_indices.append(0)
            except Exception:
                # Fallback to polygon fan
                poly_vectors = [mathutils.Vector((px, py, 0.0)) for px, py in poly_2d]
                tri_indices = mathutils.geometry.tessellate_polygon([poly_vectors])
                v_offset = len(verts)
                for px, py in poly_2d:
                    verts.append((px, py, median_shore))
                    uvs.append((px * 0.05, py * 0.05))
                for tri in tri_indices:
                    faces.append((v_offset + tri[0], v_offset + tri[1], v_offset + tri[2]))
                    mat_indices.append(0)

            # Perimeter vertical water skirt (-2.0m downward) to seal shoreline completely
            skirt_offset = len(verts)
            for i, (px, py) in enumerate(poly_2d):
                sz = get_terrain_z(bvh, px, py)
                top_z = max(median_shore, sz + 0.08)
                verts.append((px, py, top_z))
                verts.append((px, py, sz - 2.0))
                uvs.append((px * 0.05, py * 0.05))
                uvs.append((px * 0.05, py * 0.05))
                if i > 0:
                    i0 = skirt_offset + (i - 1) * 2
                    i1 = skirt_offset + i * 2
                    faces.append((i0, i1, i1 + 1))
                    faces.append((i0, i1 + 1, i0 + 1))
                    mat_indices.append(0)
                    mat_indices.append(0)
            if len(poly_2d) > 2:
                i_last = skirt_offset + (len(poly_2d) - 1) * 2
                i_first = skirt_offset
                faces.append((i_last, i_first, i_first + 1))
                faces.append((i_last, i_first + 1, i_last + 1))
                mat_indices.append(0)
                mat_indices.append(0)

        elif is_dam:
            # Physical concrete dam structure (e.g. Presa Las Auras)
            geom = el.get("geometry", [])
            if len(geom) < 2:
                continue
            poly_2d = [gps_to_local(pt["lat"], pt["lon"]) for pt in geom]
            dam_w = 5.0
            for i in range(len(poly_2d) - 1):
                p1, p2 = poly_2d[i], poly_2d[i+1]
                dx, dy = p2[0] - p1[0], p2[1] - p1[1]
                dist = math.hypot(dx, dy)
                if dist < 0.2: continue
                nx = -dy / dist * dam_w / 2.0
                ny =  dx / dist * dam_w / 2.0

                z1 = get_terrain_z(bvh, p1[0], p1[1])
                z2 = get_terrain_z(bvh, p2[0], p2[1])
                crest_z = max(z1, z2) + 2.5 # Dam crest height

                v_off = len(verts)
                # Crest vertices
                verts.append((p1[0] - nx, p1[1] - ny, crest_z))
                verts.append((p1[0] + nx, p1[1] + ny, crest_z))
                verts.append((p2[0] + nx, p2[1] + ny, crest_z))
                verts.append((p2[0] - nx, p2[1] - ny, crest_z))
                # Base vertices anchored into bedrock
                verts.append((p1[0] - nx, p1[1] - ny, z1 - 2.0))
                verts.append((p1[0] + nx, p1[1] + ny, z1 - 2.0))
                verts.append((p2[0] + nx, p2[1] + ny, z2 - 2.0))
                verts.append((p2[0] - nx, p2[1] - ny, z2 - 2.0))

                for _ in range(8):
                    uvs.append((0.0, 0.0))

                # Crest face
                faces.append((v_off, v_off + 1, v_off + 2))
                faces.append((v_off, v_off + 2, v_off + 3))
                mat_indices.extend([1, 1])
                # Upstream / Downstream face
                faces.append((v_off, v_off + 3, v_off + 7))
                faces.append((v_off, v_off + 7, v_off + 4))
                mat_indices.extend([1, 1])
                faces.append((v_off + 1, v_off + 5, v_off + 6))
                faces.append((v_off + 1, v_off + 6, v_off + 2))
                mat_indices.extend([1, 1])

        else:
            # Linear waterway (Río Tecate / streams / canals)
            geom = el.get("geometry", [])
            if len(geom) < 2:
                continue
            poly_2d = [gps_to_local(pt["lat"], pt["lon"]) for pt in geom]
            ww_type = tags.get("waterway", "stream")
            half_w = 6.0 if ww_type == "river" else 2.5

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

                # Subdivide into <= 4m segments and sample both banks + center independently
                sub_steps = max(1, int(math.ceil(seg_len / 4.0)))
                for s_step in range(sub_steps):
                    frac_a = s_step / float(sub_steps)
                    frac_b = (s_step + 1) / float(sub_steps)

                    sp1_x = p1[0] + frac_a * dx
                    sp1_y = p1[1] + frac_a * dy
                    sp2_x = p1[0] + frac_b * dx
                    sp2_y = p1[1] + frac_b * dy

                    # INDEPENDENT TRANSVERSE SAMPLING FOR ZERO CLIPPING:
                    # Sample left bank, right bank, and center
                    z_l1 = get_terrain_z(bvh, sp1_x - nx, sp1_y - ny) + 0.04
                    z_r1 = get_terrain_z(bvh, sp1_x + nx, sp1_y + ny) + 0.04
                    z_l2 = get_terrain_z(bvh, sp2_x - nx, sp2_y - ny) + 0.04
                    z_r2 = get_terrain_z(bvh, sp2_x + nx, sp2_y + ny) + 0.04

                    uv_y1 = (cum_dist + frac_a * seg_len) / 10.0
                    uv_y2 = (cum_dist + frac_b * seg_len) / 10.0

                    v_off = len(verts)
                    # 4 vertices conforming to the true transverse slope of the riverbed
                    verts.append((sp1_x - nx, sp1_y - ny, z_l1))
                    verts.append((sp1_x + nx, sp1_y + ny, z_r1))
                    verts.append((sp2_x + nx, sp2_y + ny, z_r2))
                    verts.append((sp2_x - nx, sp2_y - ny, z_l2))

                    uvs.append((0.0, uv_y1))
                    uvs.append((1.0, uv_y1))
                    uvs.append((1.0, uv_y2))
                    uvs.append((0.0, uv_y2))

                    faces.append((v_off, v_off + 1, v_off + 2))
                    faces.append((v_off, v_off + 2, v_off + 3))
                    mat_indices.append(0)
                    mat_indices.append(0)

                cum_dist += seg_len

    mesh = bpy.data.meshes.new(name="WaterwaysMesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat_water)
    mesh.materials.append(mat_dam)

    for idx, poly in enumerate(mesh.polygons):
        if idx < len(mat_indices):
            poly.material_index = mat_indices[idx]
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

def get_edge_key(u, v):
    return f"{min(u, v)},{max(u, v)}"

def _merge_bridge_gaps(edges, edge_metadata, node_map, max_gap_ratio=1.2, angle_threshold_deg=35.0):
    """
    Promotes non-bridge gap segments between same-name bridge segments to bridges.
    Mirrors _merge_bridge_gaps from src/minecraft_pipeline/exporter.py.
    """
    adj = {}
    for ed in edges:
        u, v = ed["u"], ed["v"]
        k = get_edge_key(u, v)
        adj.setdefault(u, []).append((v, k))
        adj.setdefault(v, []).append((u, k))

    def _node_dist(a_id, b_id):
        a, b = node_map.get(a_id), node_map.get(b_id)
        if not a or not b:
            return 0.0
        return math.hypot(b["x"] - a["x"], b["y"] - a["y"])

    def _edge_angle(a_id, b_id):
        a, b = node_map.get(a_id), node_map.get(b_id)
        if not a or not b:
            return 0.0
        return math.atan2(b["y"] - a["y"], b["x"] - a["x"])

    def _angles_collinear(alpha, beta, thr):
        diff = abs((alpha - beta + math.pi) % (2 * math.pi) - math.pi)
        return diff <= thr or abs(diff - math.pi) <= thr

    thr_rad = math.radians(angle_threshold_deg)
    promoted = 0

    for ed in edges:
        u, v = ed["u"], ed["v"]
        key = get_edge_key(u, v)
        meta = edge_metadata.get(key, {})
        bridge_tag = meta.get("bridge", "")
        if bridge_tag and bridge_tag != "no":
            continue
        name = meta.get("name", "")
        norm_name = get_normalized_street_name(name)
        if not norm_name:
            continue

        gap_len = _node_dist(u, v)
        seg_angle = _edge_angle(u, v)

        def _find_flanking_bridge(node_id):
            for (other_id, ek) in adj.get(node_id, []):
                if ek == key:
                    continue
                emeta = edge_metadata.get(ek, {})
                if not (emeta.get("bridge", "") not in ("", "no")):
                    continue
                enorm = get_normalized_street_name(emeta.get("name", ""))
                if enorm != norm_name:
                    continue
                flank_angle = _edge_angle(node_id, other_id)
                if _angles_collinear(seg_angle, flank_angle, thr_rad):
                    return _node_dist(node_id, other_id)
            return None

        len_u = _find_flanking_bridge(u)
        len_v = _find_flanking_bridge(v)

        if len_u is not None and len_v is not None:
            max_allowed = max_gap_ratio * min(len_u, len_v)
            if gap_len <= max_allowed:
                meta["bridge"] = "yes"
                promoted += 1

    if promoted > 0:
        print(f"[Bridges] Promoted {promoted} gap segments to bridges via _merge_bridge_gaps.")

def build_unified_road_network(cache_dir, bbox):
    """
    Loads road and bridge OSM cache files, builds a unified node and edge graph,
    promotes gap segments with _merge_bridge_gaps, resolves road styles with
    Minecraft taxonomy, and segments paths into road_ways and bridge_ways sharing
    exact (X, Y) connection nodes.
    """
    min_lat, min_lon, max_lat, max_lon = bbox

    q_road = f"""[out:json][timeout:60];
way["highway"~"motorway|trunk|primary|secondary|tertiary|residential|unclassified|service|living_street"]({min_lat},{min_lon},{max_lat},{max_lon});
out geom;
"""
    roads_data = query_overpass_cached(q_road, os.path.join(cache_dir, "road_osm.json"))

    q_bridge = f"""[out:json][timeout:30];
way["bridge"]["bridge"!="no"]({min_lat},{min_lon},{max_lat},{max_lon});
out geom;
"""
    bridges_data = query_overpass_cached(q_bridge, os.path.join(cache_dir, "bridge_osm.json"))

    elements_by_id = {}
    for el in roads_data.get("elements", []):
        elements_by_id[el["id"]] = el
    for el in bridges_data.get("elements", []):
        if el["id"] not in elements_by_id:
            elements_by_id[el["id"]] = el
        else:
            elements_by_id[el["id"]].setdefault("tags", {}).update(el.get("tags", {}))

    node_map = {}
    edges = []
    edge_metadata = {}

    for el in elements_by_id.values():
        geom = el.get("geometry", [])
        nodes = el.get("nodes", [])
        if len(geom) < 2 or len(nodes) != len(geom):
            continue
        tags = el.get("tags", {})
        for i in range(len(nodes)):
            nid = nodes[i]
            if nid not in node_map:
                lx, ly = gps_to_local(geom[i]["lat"], geom[i]["lon"])
                node_map[nid] = {"x": lx, "y": ly}
        for i in range(len(nodes) - 1):
            u, v = nodes[i], nodes[i+1]
            k = get_edge_key(u, v)
            edges.append({"u": u, "v": v})
            edge_metadata[k] = dict(tags)

    # Merge bridge gaps
    _merge_bridge_gaps(edges, edge_metadata, node_map)

    # Propagate styles across normalized street names
    def style_rank(s):
        if s["is_rural"] or s["surface"] == "gravel": return 0
        m = s["marking_type"]
        if m == "calle": return 1
        if m == "avenida": return 2
        if m == "boulevard": return 3
        if m == "highway": return 4
        return 1

    # Build node-to-edges map for topological connectivity
    node_to_edges = {}
    for ed in edges:
        node_to_edges.setdefault(ed["u"], []).append(ed)
        node_to_edges.setdefault(ed["v"], []).append(ed)

    name_groups = {}
    raw_edge_styles = {}
    for ed in edges:
        k = get_edge_key(ed["u"], ed["v"])
        meta = edge_metadata.get(k, {})
        hw = meta.get("highway", meta.get("railway", "residential"))
        name = meta.get("name", "")
        fw = meta.get("footway", "")
        st = resolve_road_properties(name, hw, footway_type=fw)
        raw_edge_styles[k] = dict(st)
        norm_name = get_normalized_street_name(name)
        if norm_name:
            name_groups.setdefault(norm_name, []).append((k, st))

    edge_styles = dict(raw_edge_styles)
    for norm_name, items in name_groups.items():
        highest = max(items, key=lambda x: style_rank(x[1]))[1]
        if style_rank(highest) > 0:
            for k, _ in items:
                edge_styles[k] = dict(highest)

    # Inherit bridge width & style from connected roads for unnamed / unclassified bridges (e.g. Xochimilco)
    for ed in edges:
        k = get_edge_key(ed["u"], ed["v"])
        meta = edge_metadata.get(k, {})
        if meta.get("bridge") not in (None, "", "no"):
            current_st = edge_styles[k]
            if not current_st.get("is_pedestrian", False):
                # Check connected non-bridge edges at endpoints u and v
                connected_widths = []
                connected_styles = []
                for end_node in [ed["u"], ed["v"]]:
                    for conn_ed in node_to_edges.get(end_node, []):
                        conn_k = get_edge_key(conn_ed["u"], conn_ed["v"])
                        if conn_k != k and edge_metadata.get(conn_k, {}).get("bridge") in (None, "", "no"):
                            c_st = edge_styles.get(conn_k, {})
                            if not c_st.get("is_pedestrian", False):
                                connected_widths.append(c_st.get("width", 6.0))
                                connected_styles.append(c_st)
                if connected_widths:
                    max_w = max(connected_widths)
                    if max_w > current_st.get("width", 0):
                        best_style = max(connected_styles, key=lambda s: s.get("width", 6.0))
                        edge_styles[k] = dict(best_style)
                        edge_styles[k]["width"] = max_w

    # Adjacency of bridges to distinguish internal bridge connections from terminal abutments
    bridge_adj = {}
    for ed in edges:
        u, v = ed["u"], ed["v"]
        k = get_edge_key(u, v)
        if edge_metadata[k].get("bridge") not in (None, "", "no"):
            bridge_adj.setdefault(u, set()).add(v)
            bridge_adj.setdefault(v, set()).add(u)

    road_ways = []
    bridge_ways = []

    for el in elements_by_id.values():
        nodes = el.get("nodes", [])
        geom = el.get("geometry", [])
        if len(nodes) < 2 or len(nodes) != len(geom):
            continue

        curr_nodes = [nodes[0]]
        curr_pts = [node_map[nodes[0]]]
        first_k = get_edge_key(nodes[0], nodes[1])
        curr_is_bridge = (edge_metadata.get(first_k, {}).get("bridge") not in (None, "", "no"))
        curr_style = edge_styles.get(first_k)

        for i in range(len(nodes) - 1):
            u, v = nodes[i], nodes[i+1]
            k = get_edge_key(u, v)
            is_b = (edge_metadata.get(k, {}).get("bridge") not in (None, "", "no"))
            st = edge_styles.get(k)

            if is_b == curr_is_bridge:
                curr_nodes.append(v)
                curr_pts.append(node_map[v])
            else:
                target = bridge_ways if curr_is_bridge else road_ways
                target.append({
                    "nodes": curr_nodes,
                    "pts": curr_pts,
                    "style": curr_style,
                    "is_bridge": curr_is_bridge,
                    "start_is_internal": (curr_nodes[0] in bridge_adj and len(bridge_adj[curr_nodes[0]]) > 1) if curr_is_bridge else False,
                    "end_is_internal": (curr_nodes[-1] in bridge_adj and len(bridge_adj[curr_nodes[-1]]) > 1) if curr_is_bridge else False,
                })
                curr_nodes = [u, v]
                curr_pts = [node_map[u], node_map[v]]
                curr_is_bridge = is_b
                curr_style = st

        target = bridge_ways if curr_is_bridge else road_ways
        target.append({
            "nodes": curr_nodes,
            "pts": curr_pts,
            "style": curr_style,
            "is_bridge": curr_is_bridge,
            "start_is_internal": (curr_nodes[0] in bridge_adj and len(bridge_adj[curr_nodes[0]]) > 1) if curr_is_bridge else False,
            "end_is_internal": (curr_nodes[-1] in bridge_adj and len(bridge_adj[curr_nodes[-1]]) > 1) if curr_is_bridge else False,
        })

    # Connect detached pedestrian footbridges (e.g. 968895089 near Paseo de las Águilas) to the road network with approach ramps
    for b_way in bridge_ways:
        b_style = b_way.get("style", {})
        if b_style.get("is_pedestrian", False):
            start_nid = b_way["nodes"][0]
            end_nid = b_way["nodes"][-1]
            p_start = b_way["pts"][0]
            p_end = b_way["pts"][-1]

            for term_nid, term_p in [(start_nid, p_start), (end_nid, p_end)]:
                # Check if this node already connects to a non-bridge way
                has_road_conn = any(term_nid in rw["nodes"] for rw in road_ways)
                if not has_road_conn:
                    # Find nearest road node within 25 meters
                    nearest_dist = 999.0
                    nearest_nid = None
                    nearest_pt = None
                    for rw in road_ways:
                        for rn, rpt in zip(rw["nodes"], rw["pts"]):
                            d = math.hypot(rpt["x"] - term_p["x"], rpt["y"] - term_p["y"])
                            if d < nearest_dist and d < 25.0:
                                nearest_dist = d
                                nearest_nid = rn
                                nearest_pt = rpt

                    if nearest_nid is not None and nearest_pt is not None:
                        # Add a pedestrian approach ramp way connecting road to bridge
                        road_ways.append({
                            "nodes": [nearest_nid, term_nid],
                            "pts": [nearest_pt, term_p],
                            "style": {
                                "width": 1.8,
                                "surface": "concrete",
                                "is_rural": False,
                                "marking_type": "none",
                                "is_pedestrian": True
                            },
                            "is_bridge": False,
                            "start_is_internal": False,
                            "end_is_internal": False
                        })
                        print(f"[Network] Connected footbridge node {term_nid} to road node {nearest_nid} (approach distance {nearest_dist:.2f}m).")

    return {
        "road_ways": road_ways,
        "bridge_ways": bridge_ways,
        "node_map": node_map
    }

def generate_bridges(bvh, cache_dir, out_blend, out_glb, bbox, prebuilt_network=None):
    import bpy
    import mathutils

    print("\n" + "="*70 + "\nGENERATING BRIDGES LAYER (FAITHFUL 3D SUSPENDED DECKS & ABUTMENTS)\n" + "="*70)
    bpy.ops.wm.read_homefile(use_empty=True)

    if prebuilt_network is None:
        net = build_unified_road_network(cache_dir, bbox)
    else:
        net = prebuilt_network

    bridge_ways = net["bridge_ways"]

    # Materials
    mat_deck = bpy.data.materials.new(name="M_BridgeDeck")
    mat_deck.use_nodes = True
    bsdf_d = mat_deck.node_tree.nodes.get("Principled BSDF")
    if bsdf_d:
        bsdf_d.inputs["Base Color"].default_value = (0.20, 0.20, 0.22, 1.0)
        bsdf_d.inputs["Roughness"].default_value = 0.80

    mat_conc = bpy.data.materials.new(name="M_BridgeConcrete")
    mat_conc.use_nodes = True
    bsdf_c = mat_conc.node_tree.nodes.get("Principled BSDF")
    if bsdf_c:
        bsdf_c.inputs["Base Color"].default_value = (0.70, 0.70, 0.68, 1.0)
        bsdf_c.inputs["Roughness"].default_value = 0.70

    mat_yellow = bpy.data.materials.new(name="M_RoadMarkingYellow")
    mat_yellow.use_nodes = True
    bsdf_y = mat_yellow.node_tree.nodes.get("Principled BSDF")
    if bsdf_y:
        bsdf_y.inputs["Base Color"].default_value = (0.95, 0.75, 0.10, 1.0)
        bsdf_y.inputs["Roughness"].default_value = 0.50

    mat_white = bpy.data.materials.new(name="M_RoadMarkingWhite")
    mat_white.use_nodes = True
    bsdf_w = mat_white.node_tree.nodes.get("Principled BSDF")
    if bsdf_w:
        bsdf_w.inputs["Base Color"].default_value = (0.92, 0.92, 0.92, 1.0)
        bsdf_w.inputs["Roughness"].default_value = 0.50

    # Mesh buffers: Slot 0: deck, Slot 1: conc, Slot 2: yellow, Slot 3: white
    verts, faces = [], []
    mat_indices = []

    for b_way in bridge_ways:
        pts = b_way["pts"]
        if len(pts) < 2:
            continue
        poly_2d = [(p["x"], p["y"]) for p in pts]
        style = b_way["style"] or resolve_road_properties("", "residential")
        width = style.get("width", 8.0)
        half_w = width / 2.0
        marking_type = style.get("marking_type", "calle")
        is_ped = style.get("is_pedestrian", False)

        start_internal = b_way.get("start_is_internal", False)
        end_internal = b_way.get("end_is_internal", False)

        seg_lens = []
        total_len = 0.0
        for i in range(len(poly_2d) - 1):
            sl = math.hypot(poly_2d[i+1][0] - poly_2d[i][0], poly_2d[i+1][1] - poly_2d[i][1])
            seg_lens.append(sl)
            total_len += sl

        if total_len < 1.0:
            continue

        z_start_ground = get_terrain_z(bvh, poly_2d[0][0], poly_2d[0][1]) + (0.25 if is_ped else 0.15)
        z_end_ground = get_terrain_z(bvh, poly_2d[-1][0], poly_2d[-1][1]) + (0.25 if is_ped else 0.15)

        elev_target = 3.5 if total_len > 30.0 else 1.8
        ramp_len = min(14.0, total_len / 3.0)

        def calc_deck_z(s, sp_x, sp_y):
            t = s / max(1.0, total_len)
            z_base = (1.0 - t) * z_start_ground + t * z_end_ground
            z_g = get_terrain_z(bvh, sp_x, sp_y)
            z_target = z_base + elev_target

            if not start_internal and s < ramp_len:
                u = s / ramp_len
                ease = u * u * (3.0 - 2.0 * u)
                z = (1.0 - ease) * z_start_ground + ease * z_target
                return max(z, z_g + (0.25 if is_ped else 0.15))
            elif not end_internal and s > (total_len - ramp_len):
                u = (total_len - s) / ramp_len
                ease = u * u * (3.0 - 2.0 * u)
                z = (1.0 - ease) * z_end_ground + ease * z_target
                return max(z, z_g + (0.25 if is_ped else 0.15))
            else:
                return max(z_target, z_g + 1.2)

        # Abutment at start if terminal (meeting road approach with 0 gap and flared wingwalls)
        if not start_internal:
            dx = poly_2d[1][0] - poly_2d[0][0]
            dy = poly_2d[1][1] - poly_2d[0][1]
            dist = math.hypot(dx, dy) or 1.0
            nx = -dy / dist * (half_w + 0.3)
            ny =  dx / dist * (half_w + 0.3)
            p0 = poly_2d[0]
            z0 = z_start_ground
            v_ab = len(verts)
            verts.append((p0[0] - nx, p0[1] - ny, z0))
            verts.append((p0[0] + nx, p0[1] + ny, z0))
            verts.append((p0[0] + nx, p0[1] + ny, z0 - 3.0))
            verts.append((p0[0] - nx, p0[1] - ny, z0 - 3.0))
            faces.append((v_ab, v_ab + 1, v_ab + 2))
            faces.append((v_ab, v_ab + 2, v_ab + 3))
            mat_indices.extend([1, 1])

            # Flared concrete wingwalls (+1.2m outward)
            fw_x = -dy / dist * (half_w + 1.2)
            fw_y =  dx / dist * (half_w + 1.2)
            # Left wingwall
            v_ww1 = len(verts)
            verts.append((p0[0] - nx, p0[1] - ny, z0))
            verts.append((p0[0] - fw_x, p0[1] - fw_y, z0 - 0.5))
            verts.append((p0[0] - fw_x, p0[1] - fw_y, z0 - 3.0))
            verts.append((p0[0] - nx, p0[1] - ny, z0 - 3.0))
            faces.append((v_ww1, v_ww1 + 1, v_ww1 + 2))
            faces.append((v_ww1, v_ww1 + 2, v_ww1 + 3))
            mat_indices.extend([1, 1])
            # Right wingwall
            v_ww2 = len(verts)
            verts.append((p0[0] + nx, p0[1] + ny, z0))
            verts.append((p0[0] + fw_x, p0[1] + fw_y, z0 - 0.5))
            verts.append((p0[0] + fw_x, p0[1] + fw_y, z0 - 3.0))
            verts.append((p0[0] + nx, p0[1] + ny, z0 - 3.0))
            faces.append((v_ww2, v_ww2 + 1, v_ww2 + 2))
            faces.append((v_ww2, v_ww2 + 2, v_ww2 + 3))
            mat_indices.extend([1, 1])

        # Abutment at end if terminal
        if not end_internal:
            dx = poly_2d[-1][0] - poly_2d[-2][0]
            dy = poly_2d[-1][1] - poly_2d[-2][1]
            dist = math.hypot(dx, dy) or 1.0
            nx = -dy / dist * (half_w + 0.3)
            ny =  dx / dist * (half_w + 0.3)
            pn = poly_2d[-1]
            zn = z_end_ground
            v_ab = len(verts)
            verts.append((pn[0] - nx, pn[1] - ny, zn))
            verts.append((pn[0] + nx, pn[1] + ny, zn))
            verts.append((pn[0] + nx, pn[1] + ny, zn - 3.0))
            verts.append((pn[0] - nx, pn[1] - ny, zn - 3.0))
            faces.append((v_ab, v_ab + 1, v_ab + 2))
            faces.append((v_ab, v_ab + 2, v_ab + 3))
            mat_indices.extend([1, 1])

            # Flared concrete wingwalls (+1.2m outward)
            fw_x = -dy / dist * (half_w + 1.2)
            fw_y =  dx / dist * (half_w + 1.2)
            # Left wingwall
            v_ww1 = len(verts)
            verts.append((pn[0] - nx, pn[1] - ny, zn))
            verts.append((pn[0] - fw_x, pn[1] - fw_y, zn - 0.5))
            verts.append((pn[0] - fw_x, pn[1] - fw_y, zn - 3.0))
            verts.append((pn[0] - nx, pn[1] - ny, zn - 3.0))
            faces.append((v_ww1, v_ww1 + 1, v_ww1 + 2))
            faces.append((v_ww1, v_ww1 + 2, v_ww1 + 3))
            mat_indices.extend([1, 1])
            # Right wingwall
            v_ww2 = len(verts)
            verts.append((pn[0] + nx, pn[1] + ny, zn))
            verts.append((pn[0] + fw_x, pn[1] + fw_y, zn - 0.5))
            verts.append((pn[0] + fw_x, pn[1] + fw_y, zn - 3.0))
            verts.append((pn[0] + nx, pn[1] + ny, zn - 3.0))
            faces.append((v_ww2, v_ww2 + 1, v_ww2 + 2))
            faces.append((v_ww2, v_ww2 + 2, v_ww2 + 3))
            mat_indices.extend([1, 1])

        # Polyline sweep
        cum_len = 0.0
        for i in range(len(poly_2d) - 1):
            p1 = poly_2d[i]
            p2 = poly_2d[i+1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            seg_len = seg_lens[i]
            if seg_len < 0.1:
                continue

            nx = -dy / seg_len * half_w
            ny =  dx / seg_len * half_w

            steps = max(1, int(math.ceil(seg_len / 3.0)))
            for s_idx in range(steps):
                f_a = s_idx / float(steps)
                f_b = (s_idx + 1) / float(steps)

                dist_a = cum_len + f_a * seg_len
                dist_b = cum_len + f_b * seg_len

                sp1_x = p1[0] + f_a * dx
                sp1_y = p1[1] + f_a * dy
                sp2_x = p1[0] + f_b * dx
                sp2_y = p1[1] + f_b * dy

                z1 = calc_deck_z(dist_a, sp1_x, sp1_y)
                z2 = calc_deck_z(dist_b, sp2_x, sp2_y)

                # 1. Deck surface (Pedestrian deck uses M_BridgeConcrete slot 1, vehicular uses M_BridgeDeck slot 0)
                deck_slot = 1 if is_ped else 0
                soffit_depth = 0.35 if is_ped else 0.80

                v_d = len(verts)
                verts.append((sp1_x - nx, sp1_y - ny, z1))
                verts.append((sp1_x + nx, sp1_y + ny, z1))
                verts.append((sp2_x + nx, sp2_y + ny, z2))
                verts.append((sp2_x - nx, sp2_y - ny, z2))

                # Soffit (bottom of box girder)
                verts.append((sp1_x - nx, sp1_y - ny, z1 - soffit_depth))
                verts.append((sp1_x + nx, sp1_y + ny, z1 - soffit_depth))
                verts.append((sp2_x + nx, sp2_y + ny, z2 - soffit_depth))
                verts.append((sp2_x - nx, sp2_y - ny, z2 - soffit_depth))

                # Deck face
                faces.append((v_d, v_d + 1, v_d + 2))
                faces.append((v_d, v_d + 2, v_d + 3))
                mat_indices.extend([deck_slot, deck_slot])

                # Soffit face
                faces.append((v_d + 4, v_d + 6, v_d + 5))
                faces.append((v_d + 4, v_d + 7, v_d + 6))
                mat_indices.extend([1, 1])

                # Girder sides
                faces.append((v_d, v_d + 3, v_d + 7))
                faces.append((v_d, v_d + 7, v_d + 4))
                faces.append((v_d + 1, v_d + 5, v_d + 6))
                faces.append((v_d + 1, v_d + 6, v_d + 2))
                mat_indices.extend([1, 1, 1, 1])

                # 2. Side parapets / railings (+1.1m)
                v_p = len(verts)
                verts.append((sp1_x - nx, sp1_y - ny, z1 + 1.1))
                verts.append((sp2_x - nx, sp2_y - ny, z2 + 1.1))
                verts.append((sp1_x + nx, sp1_y + ny, z1 + 1.1))
                verts.append((sp2_x + nx, sp2_y + ny, z2 + 1.1))

                faces.append((v_d, v_p, v_p + 1))
                faces.append((v_d, v_p + 1, v_d + 3))
                faces.append((v_d + 1, v_d + 2, v_p + 3))
                faces.append((v_d + 1, v_p + 3, v_p + 2))
                mat_indices.extend([1, 1, 1, 1])

                # 3. Center road marking on deck (ONLY on vehicular bridges)
                if not is_ped:
                    is_marking_on = (int(math.floor(dist_a)) % 4 < 2) if marking_type != "highway" else True
                    if is_marking_on:
                        cw = 0.12 if marking_type == "calle" else 0.18
                        v_m = len(verts)
                        verts.append((sp1_x - nx / half_w * cw, sp1_y - ny / half_w * cw, z1 + 0.005))
                        verts.append((sp1_x + nx / half_w * cw, sp1_y + ny / half_w * cw, z1 + 0.005))
                        verts.append((sp2_x + nx / half_w * cw, sp2_y + ny / half_w * cw, z2 + 0.005))
                        verts.append((sp2_x - nx / half_w * cw, sp2_y - ny / half_w * cw, z2 + 0.005))
                        faces.append((v_m, v_m + 1, v_m + 2))
                        faces.append((v_m, v_m + 2, v_m + 3))
                        m_slot = 3 if marking_type == "calle" else 2
                        mat_indices.extend([m_slot, m_slot])

                # 4. Pillars placed every 12m where clearance > 1.4m
                mid_d = (dist_a + dist_b) / 2.0
                if ramp_len < mid_d < (total_len - ramp_len) and (int(mid_d) % 12 < 3) and (s_idx == 0):
                    mid_x = (sp1_x + sp2_x) / 2.0
                    mid_y = (sp1_y + sp2_y) / 2.0
                    deck_z = (z1 + z2) / 2.0
                    g_z = get_terrain_z(bvh, mid_x, mid_y)
                    if (deck_z - soffit_depth - g_z) > 1.4:
                        pw = 0.4 if is_ped else 0.6
                        v_pil = len(verts)
                        verts.append((mid_x - pw, mid_y - pw, g_z - 0.5))
                        verts.append((mid_x + pw, mid_y - pw, g_z - 0.5))
                        verts.append((mid_x + pw, mid_y + pw, g_z - 0.5))
                        verts.append((mid_x - pw, mid_y + pw, g_z - 0.5))
                        verts.append((mid_x - pw, mid_y - pw, deck_z - soffit_depth))
                        verts.append((mid_x + pw, mid_y - pw, deck_z - soffit_depth))
                        verts.append((mid_x + pw, mid_y + pw, deck_z - soffit_depth))
                        verts.append((mid_x - pw, mid_y + pw, deck_z - soffit_depth))
                        for f_idx in range(4):
                            next_f = (f_idx + 1) % 4
                            faces.append((v_pil + f_idx, v_pil + next_f, v_pil + 4 + next_f))
                            faces.append((v_pil + f_idx, v_pil + 4 + next_f, v_pil + 4 + f_idx))
                            mat_indices.extend([1, 1])

            cum_len += seg_len

    b_mesh = bpy.data.meshes.new("BridgesMesh")
    b_mesh.from_pydata(verts, [], faces)
    b_mesh.materials.append(mat_deck)
    b_mesh.materials.append(mat_conc)
    b_mesh.materials.append(mat_yellow)
    b_mesh.materials.append(mat_white)

    for idx, poly in enumerate(b_mesh.polygons):
        if idx < len(mat_indices):
            poly.material_index = mat_indices[idx]
    b_mesh.update()

    obj_b = bpy.data.objects.new("Bridges", b_mesh)
    bpy.context.collection.objects.link(obj_b)

    print(f"[Bridges] Created unified Bridges mesh ({len(faces):,} triangles) with continuous elevated decks and grounded abutments.")
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
# 6. Layer Generator 4: Roadways (4-Corner Transverse Sampling & Markings)
# ─────────────────────────────────────────────────────────────────────────────

def generate_roadways(bvh, cache_dir, out_blend, out_glb, bbox, prebuilt_network=None):
    import bpy
    import mathutils

    print("\n" + "="*70 + "\nGENERATING ROADWAYS LAYER (4-CORNER TRANSVERSE TERRAIN-SNAPPING &\nMINECRAFT TAXONOMY MARKINGS)\n" + "="*70)
    bpy.ops.wm.read_homefile(use_empty=True)

    if prebuilt_network is None:
        net = build_unified_road_network(cache_dir, bbox)
    else:
        net = prebuilt_network

    road_ways = net["road_ways"]

    # Materials
    mat_asphalt = bpy.data.materials.new(name="M_Asphalt")
    mat_asphalt.use_nodes = True
    bsdf_a = mat_asphalt.node_tree.nodes.get("Principled BSDF")
    if bsdf_a:
        bsdf_a.inputs["Base Color"].default_value = (0.16, 0.16, 0.18, 1.0)
        bsdf_a.inputs["Roughness"].default_value = 0.85

    mat_clean = bpy.data.materials.new(name="M_AsphaltClean")
    mat_clean.use_nodes = True
    bsdf_c = mat_clean.node_tree.nodes.get("Principled BSDF")
    if bsdf_c:
        bsdf_c.inputs["Base Color"].default_value = (0.22, 0.22, 0.24, 1.0)
        bsdf_c.inputs["Roughness"].default_value = 0.75

    mat_rural = bpy.data.materials.new(name="M_RuralGravel")
    mat_rural.use_nodes = True
    bsdf_r = mat_rural.node_tree.nodes.get("Principled BSDF")
    if bsdf_r:
        bsdf_r.inputs["Base Color"].default_value = (0.45, 0.40, 0.35, 1.0)
        bsdf_r.inputs["Roughness"].default_value = 0.95

    mat_curb = bpy.data.materials.new(name="M_CurbConcrete")
    mat_curb.use_nodes = True
    bsdf_cu = mat_curb.node_tree.nodes.get("Principled BSDF")
    if bsdf_cu:
        bsdf_cu.inputs["Base Color"].default_value = (0.68, 0.68, 0.66, 1.0)
        bsdf_cu.inputs["Roughness"].default_value = 0.70

    mat_yellow = bpy.data.materials.new(name="M_RoadMarkingYellow")
    mat_yellow.use_nodes = True
    bsdf_y = mat_yellow.node_tree.nodes.get("Principled BSDF")
    if bsdf_y:
        bsdf_y.inputs["Base Color"].default_value = (0.95, 0.75, 0.10, 1.0)
        bsdf_y.inputs["Roughness"].default_value = 0.50

    mat_white = bpy.data.materials.new(name="M_RoadMarkingWhite")
    mat_white.use_nodes = True
    bsdf_w = mat_white.node_tree.nodes.get("Principled BSDF")
    if bsdf_w:
        bsdf_w.inputs["Base Color"].default_value = (0.92, 0.92, 0.92, 1.0)
        bsdf_w.inputs["Roughness"].default_value = 0.50

    # Material slots:
    # 0: M_Asphalt
    # 1: M_AsphaltClean
    # 2: M_RuralGravel
    # 3: M_CurbConcrete
    # 4: M_RoadMarkingYellow
    # 5: M_RoadMarkingWhite

    verts, faces = [], []
    mat_indices = []

    for r_way in road_ways:
        pts = r_way["pts"]
        if len(pts) < 2:
            continue
        poly_2d = [(p["x"], p["y"]) for p in pts]
        style = r_way["style"] or resolve_road_properties("", "residential")
        width = style.get("width", 8.0)
        half_w = width / 2.0
        surface = style.get("surface", "asphalt")
        is_rural = style.get("is_rural", False)
        marking_type = style.get("marking_type", "calle")

        is_ped = style.get("is_pedestrian", False)

        if is_ped:
            base_slot = 3  # M_CurbConcrete / sidewalk concrete
            elev_top = 0.25
        elif is_rural:
            base_slot = 2  # M_RuralGravel
            elev_top = 0.12
        elif marking_type == "boulevard":
            base_slot = 1  # M_AsphaltClean
            elev_top = 0.15
        else:
            base_slot = 0  # M_Asphalt
            elev_top = 0.15

        seg_lens = []
        total_len = 0.0
        for i in range(len(poly_2d) - 1):
            sl = math.hypot(poly_2d[i+1][0] - poly_2d[i][0], poly_2d[i+1][1] - poly_2d[i][1])
            seg_lens.append(sl)
            total_len += sl

        if total_len < 0.5:
            continue

        cum_len = 0.0
        for i in range(len(poly_2d) - 1):
            p1 = poly_2d[i]
            p2 = poly_2d[i+1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            seg_len = seg_lens[i]
            if seg_len < 0.1:
                continue

            nx = -dy / seg_len
            ny =  dx / seg_len

            steps = max(1, int(math.ceil(seg_len / 3.0)))
            for s_idx in range(steps):
                f_a = s_idx / float(steps)
                f_b = (s_idx + 1) / float(steps)

                dist_a = cum_len + f_a * seg_len
                dist_b = cum_len + f_b * seg_len

                sp1_x = p1[0] + f_a * dx
                sp1_y = p1[1] + f_a * dy
                sp2_x = p1[0] + f_b * dx
                sp2_y = p1[1] + f_b * dy

                is_near_inter = (dist_a < 4.0) or ((total_len - dist_b) < 4.0)

                # ── 1. INDEPENDENT 4-CORNER + CENTERLINE TERRAIN SAMPLING ──
                l1_x, l1_y = sp1_x - nx * half_w, sp1_y - ny * half_w
                r1_x, r1_y = sp1_x + nx * half_w, sp1_y + ny * half_w
                c1_x, c1_y = sp1_x, sp1_y

                l2_x, l2_y = sp2_x - nx * half_w, sp2_y - ny * half_w
                r2_x, r2_y = sp2_x + nx * half_w, sp2_y + ny * half_w
                c2_x, c2_y = sp2_x, sp2_y

                zg_l1 = get_terrain_z(bvh, l1_x, l1_y)
                zg_r1 = get_terrain_z(bvh, r1_x, r1_y)
                zg_c1 = get_terrain_z(bvh, c1_x, c1_y)

                zg_l2 = get_terrain_z(bvh, l2_x, l2_y)
                zg_r2 = get_terrain_z(bvh, r2_x, r2_y)
                zg_c2 = get_terrain_z(bvh, c2_x, c2_y)

                z_l1 = zg_l1 + elev_top
                z_r1 = zg_r1 + elev_top
                z_c1 = zg_c1 + elev_top + (0.005 if not is_ped else 0.0)

                z_l2 = zg_l2 + elev_top
                z_r2 = zg_r2 + elev_top
                z_c2 = zg_c2 + elev_top + (0.005 if not is_ped else 0.0)

                # 6 vertices for road segment top surface (conforms to camber + transverse slope)
                v_rd = len(verts)
                verts.append((l1_x, l1_y, z_l1)) # 0
                verts.append((c1_x, c1_y, z_c1)) # 1
                verts.append((r1_x, r1_y, z_r1)) # 2
                verts.append((l2_x, l2_y, z_l2)) # 3
                verts.append((c2_x, c2_y, z_c2)) # 4
                verts.append((r2_x, r2_y, z_r2)) # 5

                # Left half
                faces.append((v_rd + 0, v_rd + 1, v_rd + 4))
                faces.append((v_rd + 0, v_rd + 4, v_rd + 3))
                # Right half
                faces.append((v_rd + 1, v_rd + 2, v_rd + 5))
                faces.append((v_rd + 1, v_rd + 5, v_rd + 4))
                mat_indices.extend([base_slot, base_slot, base_slot, base_slot])

                # ── SIDE SKIRTS (-0.20m penetrating into terrain for 0 clipping) ──
                # Left skirt: from top edge down to bedrock
                v_sk_l = len(verts)
                verts.append((l1_x, l1_y, z_l1))
                verts.append((l2_x, l2_y, z_l2))
                verts.append((l2_x, l2_y, zg_l2 - 0.20))
                verts.append((l1_x, l1_y, zg_l1 - 0.20))
                faces.append((v_sk_l, v_sk_l + 1, v_sk_l + 2))
                faces.append((v_sk_l, v_sk_l + 2, v_sk_l + 3))
                mat_indices.extend([base_slot, base_slot])

                # Right skirt
                v_sk_r = len(verts)
                verts.append((r1_x, r1_y, z_r1))
                verts.append((r1_x, r1_y, zg_r1 - 0.20))
                verts.append((r2_x, r2_y, zg_r2 - 0.20))
                verts.append((r2_x, r2_y, z_r2))
                faces.append((v_sk_r, v_sk_r + 1, v_sk_r + 2))
                faces.append((v_sk_r, v_sk_r + 2, v_sk_r + 3))
                mat_indices.extend([base_slot, base_slot])

                # ── 2. CONCRETE CURBS (+0.25m platform curb edge, 10cm lip above asphalt) ──
                if not is_rural and not is_ped and width >= 6.0:
                    curb_w = 0.25
                    curb_elev = 0.25
                    # Left curb top
                    v_lc = len(verts)
                    in_l1_x, in_l1_y = sp1_x - nx * (half_w - curb_w), sp1_y - ny * (half_w - curb_w)
                    in_l2_x, in_l2_y = sp2_x - nx * (half_w - curb_w), sp2_y - ny * (half_w - curb_w)
                    verts.append((l1_x, l1_y, zg_l1 + curb_elev))
                    verts.append((in_l1_x, in_l1_y, zg_l1 + curb_elev))
                    verts.append((in_l2_x, in_l2_y, zg_l2 + curb_elev))
                    verts.append((l2_x, l2_y, zg_l2 + curb_elev))
                    faces.append((v_lc, v_lc + 1, v_lc + 2))
                    faces.append((v_lc, v_lc + 2, v_lc + 3))
                    mat_indices.extend([3, 3])

                    # Right curb top
                    v_rc = len(verts)
                    in_r1_x, in_r1_y = sp1_x + nx * (half_w - curb_w), sp1_y + ny * (half_w - curb_w)
                    in_r2_x, in_r2_y = sp2_x + nx * (half_w - curb_w), sp2_y + ny * (half_w - curb_w)
                    verts.append((in_r1_x, in_r1_y, zg_r1 + curb_elev))
                    verts.append((r1_x, r1_y, zg_r1 + curb_elev))
                    verts.append((r2_x, r2_y, zg_r2 + curb_elev))
                    verts.append((in_r2_x, in_r2_y, zg_r2 + curb_elev))
                    faces.append((v_rc, v_rc + 1, v_rc + 2))
                    faces.append((v_rc, v_rc + 2, v_rc + 3))
                    mat_indices.extend([3, 3])

                # ── 3. MINECRAFT TAXONOMY ROAD MARKINGS ──
                if not is_rural and not is_ped and not is_near_inter:
                    def add_ribbon(d_start, d_end, slot, z_bias=0.155):
                        vx_1a, vy_1a = sp1_x + nx * d_start, sp1_y + ny * d_start
                        vx_1b, vy_1b = sp1_x + nx * d_end,   sp1_y + ny * d_end
                        vx_2b, vy_2b = sp2_x + nx * d_end,   sp2_y + ny * d_end
                        vx_2a, vy_2a = sp2_x + nx * d_start, sp2_y + ny * d_start

                        vz_1a = get_terrain_z(bvh, vx_1a, vy_1a) + z_bias
                        vz_1b = get_terrain_z(bvh, vx_1b, vy_1b) + z_bias
                        vz_2b = get_terrain_z(bvh, vx_2b, vy_2b) + z_bias
                        vz_2a = get_terrain_z(bvh, vx_2a, vy_2a) + z_bias

                        v_rb = len(verts)
                        verts.append((vx_1a, vy_1a, vz_1a))
                        verts.append((vx_1b, vy_1b, vz_1b))
                        verts.append((vx_2b, vy_2b, vz_2b))
                        verts.append((vx_2a, vy_2a, vz_2a))
                        faces.append((v_rb, v_rb + 1, v_rb + 2))
                        faces.append((v_rb, v_rb + 2, v_rb + 3))
                        mat_indices.extend([slot, slot])

                    is_dash_on = (int(math.floor(dist_a)) % 4 < 2)

                    # Centerline markings
                    if marking_type == "highway":
                        # Double yellow solid lines
                        add_ribbon(-0.25, -0.10, 4)
                        add_ribbon( 0.10,  0.25, 4)
                    elif marking_type in ["boulevard", "avenida"]:
                        # Dashed yellow line
                        if is_dash_on:
                            add_ribbon(-0.10, 0.10, 4)
                    elif marking_type == "calle":
                        # Dashed white line
                        if is_dash_on:
                            add_ribbon(-0.08, 0.08, 5)

                    # Boulevard lane divider markings (dashed white at +-3.2m)
                    if marking_type == "boulevard" and width >= 12.0:
                        if is_dash_on:
                            add_ribbon(-3.25, -3.10, 5)
                            add_ribbon( 3.10,  3.25, 5)

                    # Edge white lines
                    if marking_type in ["highway", "boulevard", "avenida"]:
                        edge_d = half_w - 0.45
                        if edge_d > 1.0:
                            add_ribbon(-edge_d - 0.15, -edge_d, 5)
                            add_ribbon( edge_d,  edge_d + 0.15, 5)

            cum_len += seg_len

    r_mesh = bpy.data.meshes.new("RoadwaysMesh")
    r_mesh.from_pydata(verts, [], faces)
    r_mesh.materials.append(mat_asphalt) # 0
    r_mesh.materials.append(mat_clean)   # 1
    r_mesh.materials.append(mat_rural)   # 2
    r_mesh.materials.append(mat_curb)    # 3
    r_mesh.materials.append(mat_yellow)  # 4
    r_mesh.materials.append(mat_white)   # 5

    for idx, poly in enumerate(r_mesh.polygons):
        if idx < len(mat_indices):
            poly.material_index = mat_indices[idx]
    r_mesh.update()

    obj_r = bpy.data.objects.new("Roadways", r_mesh)
    bpy.context.collection.objects.link(obj_r)

    print(f"[Roadways] Created {len(faces):,} road triangles with 4-corner transverse slope sampling and full Minecraft taxonomy markings.")
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
# 7. Layer Generator 5: Manzanas & Urban Lots (Delaunay Conformal Platforms)
# ─────────────────────────────────────────────────────────────────────────────

def generate_manzanas(bvh, cache_dir, out_blend, out_glb, bbox):
    import bpy
    import mathutils

    print("\n" + "="*70 + "\nGENERATING URBAN MANZANAS LAYER (6M DELAUNAY DRAPING & MOUNTAIN PRESERVATION)\n" + "="*70)
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
        bsdf_p.inputs["Base Color"].default_value = (0.58, 0.58, 0.56, 1.0)
        bsdf_p.inputs["Roughness"].default_value = 0.75

    mat_park = bpy.data.materials.new(name="M_UrbanPark")
    mat_park.use_nodes = True
    bsdf_g = mat_park.node_tree.nodes.get("Principled BSDF")
    if bsdf_g:
        bsdf_g.inputs["Base Color"].default_value = (0.35, 0.52, 0.22, 1.0)
        bsdf_g.inputs["Roughness"].default_value = 0.85

    verts, faces = [], []
    mat_indices = []

    # ── 1. OSM Landuse / Leisure Polygons (Parks, Schools, Green Areas) ──
    polygon_candidates = []
    for el in osm_data.get("elements", []):
        geom = el.get("geometry", [])
        if len(geom) < 3:
            continue
        poly_2d = [gps_to_local(pt["lat"], pt["lon"]) for pt in geom]
        if poly_2d[0] == poly_2d[-1]:
            poly_2d = poly_2d[:-1]
        if len(poly_2d) < 3:
            continue

        xs = [p[0] for p in poly_2d]
        ys = [p[1] for p in poly_2d]
        span_x = max(xs) - min(xs)
        span_y = max(ys) - min(ys)
        area = 0.5 * abs(sum(poly_2d[i][0] * poly_2d[(i + 1) % len(poly_2d)][1] - poly_2d[(i + 1) % len(poly_2d)][0] * poly_2d[i][1] for i in range(len(poly_2d))))
        if area > 60000.0 or area < 25.0 or span_x > 350.0 or span_y > 350.0:
            continue

        tags = el.get("tags", {})
        is_green = tags.get("leisure") in ["park", "pitch", "garden"] or tags.get("landuse") in ["cemetery", "forest", "grass"]
        mat_slot = 1 if is_green else 0
        polygon_candidates.append({"poly": poly_2d, "slot": mat_slot, "area": area})

    print(f"[Manzanas] Loaded {len(polygon_candidates)} OSM landuse/leisure polygons.")

    # ── 2. Road Network Planar Cycles (True City Blocks / Manzanas as in Minecraft pipeline) ──
    road_cache_path = os.path.join(cache_dir, "road_osm.json")
    if os.path.exists(road_cache_path):
        with open(road_cache_path, "r", encoding="utf-8") as f:
            roads_data = json.load(f)

        adj = {}
        node_coords = {}
        for r in roads_data.get("elements", []):
            nodes = r.get("nodes", [])
            geom = r.get("geometry", [])
            if len(nodes) < 2 or len(nodes) != len(geom):
                continue
            for i in range(len(nodes)):
                nid = nodes[i]
                if nid not in node_coords:
                    node_coords[nid] = gps_to_local(geom[i]["lat"], geom[i]["lon"])
            for i in range(len(nodes) - 1):
                u, v = nodes[i], nodes[i+1]
                adj.setdefault(u, set()).add(v)
                adj.setdefault(v, set()).add(u)

        # Sort neighbors angularly
        sorted_neighbors = {}
        for u, nbrs in adj.items():
            ux, uy = node_coords[u]
            sorted_neighbors[u] = sorted(list(nbrs), key=lambda v: math.atan2(node_coords[v][1] - uy, node_coords[v][0] - ux))

        visited_half_edges = set()
        cycle_blocks = []
        for u, nbrs in sorted_neighbors.items():
            for v in nbrs:
                if (u, v) in visited_half_edges:
                    continue
                loop = [u]
                curr_u, curr_v = u, v
                step = 0
                while (curr_u, curr_v) not in visited_half_edges and step < 500:
                    visited_half_edges.add((curr_u, curr_v))
                    loop.append(curr_v)
                    nbrs_v = sorted_neighbors.get(curr_v, [])
                    if len(nbrs_v) <= 1:
                        break
                    try:
                        idx = nbrs_v.index(curr_u)
                        next_v = nbrs_v[(idx + 1) % len(nbrs_v)]
                        curr_u, curr_v = curr_v, next_v
                        step += 1
                    except ValueError:
                        break

                if len(loop) >= 4 and loop[0] == loop[-1]:
                    poly = [node_coords[n] for n in loop[:-1]]
                    signed_area = 0.5 * sum(poly[i][0]*poly[(i+1)%len(poly)][1] - poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly)))
                    # Interior planar faces in this traversal have signed_area < 0
                    if signed_area < 0:
                        abs_area = abs(signed_area)
                        # Filter out huge polygons > 60,000 m2 (e.g. Cerro Cuchumá perimeter) and tiny artifacts < 50 m2
                        if 50.0 < abs_area < 60000.0:
                            xs = [p[0] for p in poly]
                            ys = [p[1] for p in poly]
                            if (max(xs) - min(xs) < 400.0) and (max(ys) - min(ys) < 400.0):
                                cycle_blocks.append({"poly": poly, "slot": 0, "area": abs_area})

        print(f"[Manzanas] Extracted {len(cycle_blocks)} planar city block cycles from road network graph.")

        # Avoid duplicates: add cycle blocks whose centroids are not inside an already classified OSM park/landuse
        added_cycles = 0
        for cb in cycle_blocks:
            c_poly = cb["poly"]
            cx = sum(p[0] for p in c_poly) / len(c_poly)
            cy = sum(p[1] for p in c_poly) / len(c_poly)
            is_inside_existing = any(point_in_poly(cx, cy, cand["poly"]) for cand in polygon_candidates)
            if not is_inside_existing:
                polygon_candidates.append(cb)
                added_cycles += 1

        print(f"[Manzanas] Combined total: {len(polygon_candidates)} urban blocks and landuse platforms ({added_cycles} from road cycles).")

    # ── 3. Triangulation and Mesh Generation ──
    for cand in polygon_candidates:
        poly_2d = cand["poly"]
        mat_slot = cand["slot"]

        xs = [p[0] for p in poly_2d]
        ys = [p[1] for p in poly_2d]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # Delaunay grid points (6m) to hug terrain curves with 0 clipping
        pts = [mathutils.Vector((p[0], p[1])) for p in poly_2d]
        edges = [(i, (i + 1) % len(poly_2d)) for i in range(len(poly_2d))]

        grid_step = 6.0
        grid_pts = []
        x_steps = int((max_x - min_x) / grid_step) + 1
        y_steps = int((max_y - min_y) / grid_step) + 1
        for i in range(x_steps):
            gx = min_x + i * grid_step
            for j in range(y_steps):
                gy = min_y + j * grid_step
                if point_in_poly(gx, gy, poly_2d):
                    grid_pts.append(mathutils.Vector((gx, gy)))

        all_pts = pts + grid_pts
        try:
            res = mathutils.geometry.delaunay_2d_cdt(all_pts, edges, [], 0, 1e-4)
            out_pts, out_edges, out_faces, _, _, _ = res

            v_offset = len(verts)
            # Elevation: +0.25m curb platform height (matching sidewalk level above asphalt)
            for opt in out_pts:
                pz = get_terrain_z(bvh, opt.x, opt.y) + 0.25
                verts.append((opt.x, opt.y, pz))

            for f in out_faces:
                cx = (out_pts[f[0]].x + out_pts[f[1]].x + out_pts[f[2]].x) / 3.0
                cy = (out_pts[f[0]].y + out_pts[f[1]].y + out_pts[f[2]].y) / 3.0
                if point_in_poly(cx, cy, poly_2d):
                    faces.append((v_offset + f[0], v_offset + f[1], v_offset + f[2]))
                    mat_indices.append(mat_slot)
        except Exception:
            # Fallback
            poly_vectors = [mathutils.Vector((px, py, 0.0)) for px, py in poly_2d]
            tri_indices = mathutils.geometry.tessellate_polygon([poly_vectors])
            v_offset = len(verts)
            for px, py in poly_2d:
                pz = get_terrain_z(bvh, px, py) + 0.25
                verts.append((px, py, pz))
            for tri in tri_indices:
                faces.append((v_offset + tri[0], v_offset + tri[1], v_offset + tri[2]))
                mat_indices.append(mat_slot)

        # Perimeter vertical curb skirt down to -0.25m below terrain (50cm total thickness) to seal edges completely
        skirt_off = len(verts)
        for i, (px, py) in enumerate(poly_2d):
            pz = get_terrain_z(bvh, px, py)
            verts.append((px, py, pz + 0.25))
            verts.append((px, py, pz - 0.25))
            if i > 0:
                i0 = skirt_off + (i - 1) * 2
                i1 = skirt_off + i * 2
                faces.append((i0, i1, i1 + 1))
                faces.append((i0, i1 + 1, i0 + 1))
                mat_indices.extend([mat_slot, mat_slot])
        if len(poly_2d) > 2:
            i_last = skirt_off + (len(poly_2d) - 1) * 2
            i_first = skirt_off
            faces.append((i_last, i_first, i_first + 1))
            faces.append((i_last, i_first + 1, i_last + 1))
            mat_indices.extend([mat_slot, mat_slot])

    m_mesh = bpy.data.meshes.new("ManzanasMesh")
    m_mesh.from_pydata(verts, [], faces)
    m_mesh.materials.append(mat_pave)
    m_mesh.materials.append(mat_park)

    for idx, f in enumerate(m_mesh.polygons):
        if idx < len(mat_indices):
            f.material_index = mat_indices[idx]
    m_mesh.update()

    obj = bpy.data.objects.new("UrbanManzanas", m_mesh)
    bpy.context.collection.objects.link(obj)

    print(f"[Manzanas] Created {len(faces):,} dense draped manzana triangles (+0.25m platform, -0.25m physical skirts, 0% clipping).")
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

    # Build unified road network graph (shared between bridges & roadways)
    print("\n[Network] Building unified road and bridge topological graph...")
    net = build_unified_road_network(cache_dir, bbox)
    print(f"[Network] Ready: {len(net['road_ways'])} road ways, {len(net['bridge_ways'])} bridge ways.")

    # 4. Subsystem 3: Bridges
    generate_bridges(
        bvh, cache_dir,
        "godot_project/assets/bridges_adjusted.blend",
        "godot_project/assets/bridges_baked.glb",
        bbox,
        prebuilt_network=net
    )

    # 5. Subsystem 4: Roadways
    generate_roadways(
        bvh, cache_dir,
        "godot_project/assets/roadways_adjusted.blend",
        "godot_project/assets/roadways_baked.glb",
        bbox,
        prebuilt_network=net
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
