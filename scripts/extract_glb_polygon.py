#!/usr/bin/env python3
"""
extract_glb_polygon.py

Extracts the exact 2D boundary polygon from tecate.glb (Mesh 3: clippedBottom),
converts the vertices from Web Mercator to WGS84 (EPSG:4326), and outputs a valid GeoJSON.
This represents the facsimile area used to generate the terrain model, including
the intentional boundary displacement toward Donohue Mountain.
"""

import os
import sys
import json
import math
import struct
import argparse
import numpy as np

# Calibrated Web Mercator center coordinates for tecate.glb
X_CENTER_GLB = -12949516.38
Y_CENTER_GLB = 3819082.83

def extract_boundary_loop(glb_path: str) -> np.ndarray:
    """Reads clippedBottom from the GLB, traces boundary edges, and returns ordered 2D vertices."""
    with open(glb_path, "rb") as f:
        f.read(12)
        chunk_len, _ = struct.unpack("<II", f.read(8))
        gltf = json.loads(f.read(chunk_len).decode("utf-8"))
        f.seek(12 + 8 + chunk_len)
        f.read(8)
        binary_data = f.read()

    # Find node named clippedBottom and get its mesh index
    clipped_idx = 2
    for node in gltf.get("nodes", []):
        if node.get("name") == "clippedBottom":
            clipped_idx = node.get("mesh", 2)
            break

    mesh = gltf["meshes"][clipped_idx]
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
    ind_comp_type = ind_acc["componentType"]

    if ind_comp_type == 5123:  # UNSIGNED_SHORT
        indices = np.frombuffer(binary_data[ind_offset:ind_offset + ind_count * 2], dtype=np.uint16)
    elif ind_comp_type == 5125:  # UNSIGNED_INT
        indices = np.frombuffer(binary_data[ind_offset:ind_offset + ind_count * 4], dtype=np.uint32)
    else:
        raise ValueError(f"Unsupported index component type: {ind_comp_type}")

    triangles = indices.reshape(-1, 3)

    # Build boundary edge map
    edges = {}
    for tri in triangles:
        for i in range(3):
            u, v = min(tri[i], tri[(i + 1) % 3]), max(tri[i], tri[(i + 1) % 3])
            edges[(u, v)] = edges.get((u, v), 0) + 1

    boundary_edges = [edge for edge, count in edges.items() if count == 1]

    adj = {}
    for u, v in boundary_edges:
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)

    # Trace closed loop
    start = list(adj.keys())[0]
    loop = [start]
    prev, curr = None, start
    while True:
        neighbors = adj[curr]
        next_node = neighbors[0] if neighbors[0] != prev else neighbors[1]
        if next_node == start:
            break
        loop.append(next_node)
        prev, curr = curr, next_node
        if len(loop) > len(adj):
            break

    # positions: (X, Z) in GLB
    loop_pts = positions[loop][:, [0, 2]]
    return loop_pts

def glb_to_gps(px: float, pz: float) -> tuple[float, float]:
    """Converts GLB coordinates (px, pz) to WGS84 GPS (lon, lat)."""
    xm = px + X_CENTER_GLB
    ym = -pz + Y_CENTER_GLB
    lon = xm * 180.0 / 20037508.34
    lat = math.degrees(2.0 * math.atan(math.exp(ym * math.pi / 20037508.34)) - math.pi / 2.0)
    return lon, lat

def export_geojson(glb_path: str, output_path: str):
    print(f"[Extractor] Reading boundary from: {glb_path}")
    loop_pts = extract_boundary_loop(glb_path)
    print(f"[Extractor] Extracted {len(loop_pts):,} boundary vertices.")

    coords = []
    for pt in loop_pts:
        lon, lat = glb_to_gps(float(pt[0]), float(pt[1]))
        coords.append([round(lon, 7), round(lat, 7)])

    # Ensure polygon is closed
    if coords[0] != coords[-1]:
        coords.append(coords[0])

    geojson_data = {
        "type": "FeatureCollection",
        "name": "tecate_facsimile_polygon",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "description": "Tecate terrain facsimile boundary extracted from tecate.glb clippedBottom mesh. "
                                   "Contains the official INEGI boundary with intentional NW displacement toward Donohue Mountain.",
                    "source_asset": os.path.basename(glb_path),
                    "vertex_count": len(coords),
                    "bounds_lon": [min(c[0] for c in coords), max(c[0] for c in coords)],
                    "bounds_lat": [min(c[1] for c in coords), max(c[1] for c in coords)]
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coords]
                }
            }
        ]
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, indent=2)

    print(f"[Extractor] Successfully saved GeoJSON to: {output_path}")
    print(f"  Longitude range: {geojson_data['features'][0]['properties']['bounds_lon']}")
    print(f"  Latitude range:  {geojson_data['features'][0]['properties']['bounds_lat']}")

def main():
    parser = argparse.ArgumentParser(description="Extract facsimile boundary GeoJSON from tecate.glb.")
    parser.add_argument("--glb-path", default="godot_project/assets/tecate2.glb", help="Path to terrain GLB")
    parser.add_argument("--output-path", default="godot_project/assets/tecate_facsimile_polygon.geojson", help="Output GeoJSON path")
    args = parser.parse_args()

    export_geojson(args.glb_path, args.output_path)

if __name__ == "__main__":
    main()
