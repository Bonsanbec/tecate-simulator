# Purpose: Validates 3D mesh geometry by projecting it back into camera images and comparing it against expected facade coordinate boundaries.
# Inputs: GLB file path, target panoramas dictionary, target facade dictionary.
# Outputs: Reprojection validation report dictionary with RMS error.
# Responsibilities: Parses GLB files, matches 3D vertices, and computes camera perspective reprojection errors.
# Dependencies: json, os, math, struct, numpy

import json
import os
import math
import struct
import numpy as np

class ReprojectionValidator:
    """
    Validates 3D mesh geometry by projecting it back into camera images
    and comparing it against expected facade coordinate boundaries.
    """
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir

    def _gps_to_local(self, lat: float, lon: float) -> tuple[float, float]:
        TECATE_LAT_CENTER = 32.573229
        TECATE_LON_CENTER = -116.626536
        EARTH_RADIUS = 6378137.0
        
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        lat_c_rad = math.radians(TECATE_LAT_CENTER)
        lon_c_rad = math.radians(TECATE_LON_CENTER)
        
        dx = EARTH_RADIUS * (lon_rad - lon_c_rad) * math.cos(lat_c_rad)
        dy = EARTH_RADIUS * (lat_rad - lat_c_rad)
        return dx, dy

    def _parse_glb_vertices(self, glb_path: str) -> list[tuple[float, float, float]]:
        """Parses a GLB binary file and returns a list of unique vertex positions in local Cartesian meters."""
        if not os.path.exists(glb_path):
            raise FileNotFoundError(f"GLB file not found: {glb_path}")
            
        vertices = []
        with open(glb_path, "rb") as f:
            # Read header
            header = f.read(12)
            if len(header) < 12:
                return []
            magic, version, length = struct.unpack("<4sII", header)
            if magic != b"glTF":
                raise ValueError("Not a valid glTF/GLB file")
                
            # Read chunk 0 (JSON)
            chunk_header = f.read(8)
            if len(chunk_header) < 8:
                return []
            chunk_len, chunk_type = struct.unpack("<II", chunk_header)
            if chunk_type != 0x4E4F534A:
                raise ValueError("First chunk must be JSON")
                
            json_data = f.read(chunk_len).decode("utf-8")
            gltf_json = json.loads(json_data)
            
            # Read chunk 1 (BIN)
            chunk_header2 = f.read(8)
            if len(chunk_header2) < 8:
                return []
            chunk_len2, chunk_type2 = struct.unpack("<II", chunk_header2)
            if chunk_type2 != 0x004E4942:
                raise ValueError("Second chunk must be BIN")
                
            bin_data = f.read(chunk_len2)
            
        nodes = gltf_json.get("nodes", [])
        meshes = gltf_json.get("meshes", [])
        
        # Traverse nodes to parse mesh primitives and apply any transforms
        for node in nodes:
            mesh_idx = node.get("mesh")
            if mesh_idx is None:
                continue
                
            mesh = meshes[mesh_idx]
            
            # Construct transform matrix from node properties
            matrix = np.eye(4)
            if "matrix" in node:
                matrix = np.array(node["matrix"]).reshape(4, 4, order="F")
            else:
                t = node.get("translation", [0.0, 0.0, 0.0])
                r = node.get("rotation", [0.0, 0.0, 0.0, 1.0]) # x, y, z, w
                s = node.get("scale", [1.0, 1.0, 1.0])
                
                T = np.eye(4)
                T[:3, 3] = t
                
                R = np.eye(4)
                x, y, z, w = r
                R[0, 0] = 1 - 2*y*y - 2*z*z
                R[0, 1] = 2*x*y - 2*z*w
                R[0, 2] = 2*x*z + 2*y*w
                R[1, 0] = 2*x*y + 2*z*w
                R[1, 1] = 1 - 2*x*x - 2*z*z
                R[1, 2] = 2*y*z - 2*x*w
                R[2, 0] = 2*x*z - 2*y*w
                R[2, 1] = 2*y*z + 2*x*w
                R[2, 2] = 1 - 2*x*x - 2*y*y
                
                S = np.eye(4)
                S[0, 0] = s[0]
                S[1, 1] = s[1]
                S[2, 2] = s[2]
                
                matrix = T @ R @ S
                
            for prim in mesh.get("primitives", []):
                attrs = prim.get("attributes", {})
                pos_idx = attrs.get("POSITION")
                if pos_idx is None:
                    continue
                    
                accessor = gltf_json["accessors"][pos_idx]
                bv = gltf_json["bufferViews"][accessor["bufferView"]]
                
                offset = bv.get("byteOffset", 0) + accessor.get("byteOffset", 0)
                count = accessor["count"]
                
                if accessor.get("componentType") == 5126 and accessor.get("type") == "VEC3":
                    for idx in range(count):
                        x, y, z = struct.unpack_from("<fff", bin_data, offset + idx * 12)
                        
                        # Apply transform matrix
                        v_gltf = np.array([x, y, z, 1.0])
                        v_transformed = matrix @ v_gltf
                        tx, ty, tz = v_transformed[:3]
                        
                        # Convert from glTF coordinate system (+Y Up, -Z Forward/North) 
                        # to local Cartesian meters (+Z Up, +Y North)
                        local_x = tx
                        local_y = -tz
                        local_z = ty
                        
                        vertices.append((local_x, local_y, local_z))
                        
        # De-duplicate
        unique_verts = list(set(vertices))
        return unique_verts

    def validate(self, glb_path: str, panos: dict, facade: dict) -> dict:
        """
        Validates GLB geometry by projecting vertices back to cameras.
        """
        print(f"[ReprojectionValidator] Running reprojection test on {glb_path}...")
        
        # Parse GLB vertices
        glb_verts = self._parse_glb_vertices(glb_path)
        if not glb_verts:
            return {
                "rms_reprojection_error_px": 999.0,
                "status": "FAIL",
                "reason": "Could not extract vertices from GLB"
            }
            
        block_id = facade["block_id"]
        target_indices = facade["target_facade_indices"]
        
        # Load facades_cache.json
        with open("data/facades_cache.json", "r", encoding="utf-8") as f:
            facades_cache = json.load(f)
            
        # Get block height from blocks_cache.json
        with open("data/blocks_cache.json", "r", encoding="utf-8") as f:
            blocks_cache = json.load(f)
        block_data = blocks_cache.get(block_id)
        height = block_data.get("height_meters", 8.0)
        
        errors = []
        
        for p in panos["panoramas"]:
            pano_id = p["pano_id"]
            cx, cy = self._gps_to_local(p["latitude"], p["longitude"])
            
            # Camera parameters
            cam_z = 2.5
            cam_fov = 75.0
            W_obs = 1280
            H_obs = 720
            
            f_len = (W_obs - 1) / (2.0 * math.tan(math.radians(cam_fov) / 2.0))
            
            # Collect expected 3D points for segments captured by this panorama
            for idx in target_indices:
                f_id = f"{block_id}_facade_{idx}"
                f_data = facades_cache.get(f_id)
                if not f_data or f_data.get("pano_id") != pano_id:
                    continue
                    
                # Use segment-specific screenshot heading as camera yaw
                cam_yaw = math.radians(f_data["heading"])
                v_look = np.array([math.sin(cam_yaw), math.cos(cam_yaw), 0.0])
                v_right = np.array([math.cos(cam_yaw), -math.sin(cam_yaw), 0.0])
                v_up = np.array([0.0, 0.0, 1.0])
                
                verts = f_data["facade_segment_vertices_local"]
                A, B = verts[0], verts[1]
                
                # 3D corners of the facade quad
                corners = [
                    (A[0], A[1], 0.0),
                    (B[0], B[1], 0.0),
                    (B[0], B[1], height),
                    (A[0], A[1], height)
                ]
                
                # Match each corner to closest vertex in GLB
                for X, Y, Z in corners:
                    best_match = None
                    min_d = float("inf")
                    for vx, vy, vz in glb_verts:
                        d = math.sqrt((X - vx)**2 + (Y - vy)**2 + (Z - vz)**2)
                        if d < min_d:
                            min_d = d
                            best_match = (vx, vy, vz)
                            
                    # If match is close enough in 3D (within 0.5m), check reprojection
                    if min_d < 0.5:
                        mx, my, mz = best_match
                        
                        # Project GLB vertex to camera frame
                        dx = mx - cx
                        dy = my - cy
                        dz = mz - cam_z
                        
                        x_c = dx * v_right[0] + dy * v_right[1] + dz * v_right[2]
                        y_c = dx * v_up[0] + dy * v_up[1] + dz * v_up[2]
                        z_c = dx * v_look[0] + dy * v_look[1] + dz * v_look[2]
                        
                        if z_c > 0.1:
                            px = (W_obs - 1) / 2.0 + f_len * (x_c / z_c)
                            py = (H_obs - 1) / 2.0 - f_len * (y_c / z_c)
                            
                            # Project expected corner
                            edx = X - cx
                            edy = Y - cy
                            edz = Z - cam_z
                            
                            ex_c = edx * v_right[0] + edy * v_right[1] + edz * v_right[2]
                            ey_c = edx * v_up[0] + edy * v_up[1] + edz * v_up[2]
                            ez_c = edx * v_look[0] + edy * v_look[1] + edz * v_look[2]
                            
                            epx = (W_obs - 1) / 2.0 + f_len * (ex_c / ez_c)
                            epy = (H_obs - 1) / 2.0 - f_len * (ey_c / ez_c)
                            
                            err = math.sqrt((px - epx)**2 + (py - epy)**2)
                            errors.append(err)
                            
        if not errors:
            return {
                "rms_reprojection_error_px": 999.0,
                "status": "FAIL",
                "reason": "No matched vertices projected inside camera frustum"
            }
            
        rms = float(math.sqrt(np.mean([e**2 for e in errors])))
        status = "PASS" if rms < 5.0 else "FAIL"
        
        return {
            "rms_reprojection_error_px": rms,
            "status": status,
            "num_matched_corners": len(errors)
        }

