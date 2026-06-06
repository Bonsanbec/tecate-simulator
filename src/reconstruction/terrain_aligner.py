import os
import json
import math
import struct
import numpy as np
from src.core_io.coords import gps_to_local, TECATE_LAT_CENTER, TECATE_LON_CENTER

class TerrainAligner:
    """
    Computes the Procrustes Least Squares transformation (scale, rotation, translation)
    to align the terrain GLB mesh with the local Cartesian coordinates (Equirectangular relative to Parque Hidalgo).
    """
    def __init__(self, geojson_path="reference/tecate-polygon.json", glb_path="models/tecate/glb/tecate.glb"):
        self.geojson_path = geojson_path
        self.glb_path = glb_path

    def load_geojson_boundary(self) -> np.ndarray:
        """
        Loads the WGS84 GeoJSON polygon boundary.
        """
        if not os.path.exists(self.geojson_path):
            raise FileNotFoundError(f"GeoJSON reference polygon not found at: {self.geojson_path}")
        with open(self.geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # MultiPolygon -> parts -> rings -> coords
        coords = np.array(data['features'][0]['geometry']['coordinates'][0][0])
        return coords

    def extract_glb_boundary_loop(self) -> np.ndarray:
        """
        Reads the clippedBottom mesh from the GLB file, extracts the boundary edges,
        and chains them to get the ordered 2D boundary vertices (X, Z).
        """
        if not os.path.exists(self.glb_path):
            raise FileNotFoundError(f"Terrain GLB not found at: {self.glb_path}")
            
        with open(self.glb_path, "rb") as f:
            # Read GLB header
            header = f.read(12)
            magic, version, length = struct.unpack('<III', header)
            if magic != 0x46546c67:
                raise ValueError("Invalid GLB magic number")
                
            # Read JSON chunk header
            chunk_header = f.read(8)
            chunk_length, chunk_type = struct.unpack('<II', chunk_header)
            if chunk_type != 0x4e4f534a:
                raise ValueError("First chunk must be JSON")
                
            json_bytes = f.read(chunk_length)
            gltf = json.loads(json_bytes.decode('utf-8'))
            
            # Find clippedBottom mesh (index 3 or name matches clippedBottom)
            clipped_bottom_mesh_idx = None
            for idx, mesh in enumerate(gltf.get('meshes', [])):
                node_name = gltf.get('nodes', [{}])[idx].get('name', '')
                if node_name == 'clippedBottom' or idx == 3:
                    clipped_bottom_mesh_idx = idx
                    break
                    
            if clipped_bottom_mesh_idx is None:
                raise ValueError("Could not find 'clippedBottom' mesh in GLB")
                
            mesh = gltf['meshes'][clipped_bottom_mesh_idx]
            prim = mesh['primitives'][0]
            pos_idx = prim['attributes']['POSITION']
            ind_idx = prim['indices']
            
            # Read POSITION and indices accessors
            accessors = gltf['accessors']
            pos_acc = accessors[pos_idx]
            ind_acc = accessors[ind_idx]
            
            buffer_views = gltf['bufferViews']
            pos_bv = buffer_views[pos_acc['bufferView']]
            ind_bv = buffer_views[ind_acc['bufferView']]
            
            pos_offset = pos_bv.get('byteOffset', 0) + pos_acc.get('byteOffset', 0)
            pos_count = pos_acc['count']
            
            ind_offset = ind_bv.get('byteOffset', 0) + ind_acc.get('byteOffset', 0)
            ind_count = ind_acc['count']
            ind_comp_type = ind_acc['componentType']
            
            # Seek to binary chunk (Chunk 1)
            f.seek(12 + 8 + chunk_length)
            chunk1_header = f.read(8)
            chunk1_len, chunk1_type = struct.unpack('<II', chunk1_header)
            binary_data = f.read(chunk1_len)
            
            # Unpack float positions (VEC3)
            positions = np.frombuffer(binary_data[pos_offset:pos_offset + pos_count * 12], dtype=np.float32).reshape(pos_count, 3)
            
            # Unpack indices (SCALAR)
            if ind_comp_type == 5123: # UNSIGNED_SHORT
                indices = np.frombuffer(binary_data[ind_offset:ind_offset + ind_count * 2], dtype=np.uint16)
            elif ind_comp_type == 5125: # UNSIGNED_INT
                indices = np.frombuffer(binary_data[ind_offset:ind_offset + ind_count * 4], dtype=np.uint32)
            else:
                raise ValueError(f"Unsupported index component type: {ind_comp_type}")
                
            triangles = indices.reshape(-1, 3)
            
            # Build boundary edge adjacency
            edges = {}
            for tri in triangles:
                for i in range(3):
                    u, v = tri[i], tri[(i+1)%3]
                    edge = (min(u, v), max(u, v))
                    edges[edge] = edges.get(edge, 0) + 1
                    
            boundary_edges = [edge for edge, count in edges.items() if count == 1]
            
            adj = {}
            for u, v in boundary_edges:
                adj.setdefault(u, []).append(v)
                adj.setdefault(v, []).append(u)
                
            # Trace the closed boundary loop
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
                    
            loop_pts = positions[loop][:, [0, 2]] # (X, Z)
            return loop_pts

    def wgs84_to_web_mercator(self, lon: float, lat: float) -> tuple[float, float]:
        """
        Converts WGS84 GPS (lon, lat) to Web Mercator (EPSG:3857) meters.
        """
        x = lon * 20037508.34 / 180.0
        y = math.log(math.tan((90.0 + lat) * math.pi / 360.0)) * 20037508.34 / math.pi
        return x, y

    def compute_alignment(self) -> dict:
        """
        Runs the Procrustes alignment process.
        Returns a dictionary containing the scale, rotation, translation, and validation RMSE.
        """
        # 1. Load datasets
        geojson_pts = self.load_geojson_boundary()
        loop_pts = self.extract_glb_boundary_loop()
        
        # 2. Project GeoJSON boundary to local Cartesian (tangent plane)
        local_pts = np.array([gps_to_local(pt[1], pt[0]) for pt in geojson_pts])
        
        # 3. Project GeoJSON boundary to Web Mercator for matching against terrain loop space
        merc_pts = np.array([self.wgs84_to_web_mercator(pt[0], pt[1]) for pt in geojson_pts])
        
        # Bounding box centers of the unmodified GeoJSON polygon (exclude NW corner)
        X_center = (-12997135.116 - 12899057.483) / 2.0
        Y_center = (3791066.798 + 3847098.858) / 2.0
        
        # Apply translation and Y-flip for rough alignment
        P_merc_aligned = np.zeros_like(merc_pts)
        P_merc_aligned[:, 0] = merc_pts[:, 0] - X_center + 1420.08
        P_merc_aligned[:, 1] = -(merc_pts[:, 1] - Y_center)
        
        # 4. Match closest points and filter outliers (distance < 100 meters)
        good_local_pts = []
        good_loop_pts = []
        for pt_m, pt_local in zip(P_merc_aligned, local_pts):
            dists = np.linalg.norm(loop_pts - pt_m, axis=1)
            idx = np.argmin(dists)
            if dists[idx] < 100.0:
                good_local_pts.append(pt_local)
                # Flip terrain Z coordinate (maps to Y-up in local tangent plane)
                flipped_loop_pt = np.array([loop_pts[idx][0], -loop_pts[idx][1]])
                good_loop_pts.append(flipped_loop_pt)
                
        good_local_pts = np.array(good_local_pts)
        good_loop_pts = np.array(good_loop_pts)
        
        if len(good_local_pts) < 10:
            raise ValueError("Too few matching points found between terrain loop and GeoJSON polygon.")
            
        # 5. Solve Procrustes alignment: local_pts = scale * loop_pts * R + translation
        c_loop = np.mean(good_loop_pts, axis=0)
        c_local = np.mean(good_local_pts, axis=0)
        
        P_l_centered = good_loop_pts - c_loop
        P_loc_centered = good_local_pts - c_local
        
        # SVD
        H = np.dot(P_l_centered.T, P_loc_centered)
        U, S_vals, Vt = np.linalg.svd(H)
        R = np.dot(U, Vt)
        if np.linalg.det(R) < 0:
            Vt[1, :] *= -1
            R = np.dot(U, Vt)
            
        # Scale
        scale = np.sum(np.dot(P_l_centered, R) * P_loc_centered) / np.sum(P_l_centered**2)
        
        # Translation
        translation = c_local - scale * np.dot(c_loop, R)
        
        # RMSE
        transformed = scale * np.dot(good_loop_pts, R) + translation
        errors = np.linalg.norm(transformed - good_local_pts, axis=1)
        rmse = np.sqrt(np.mean(errors**2))
        max_error = np.max(errors)
        
        # Compile result dictionary
        result = {
            "scale": float(scale),
            "rotation_matrix": R.tolist(),
            "rotation_angle_degrees": float(math.degrees(math.atan2(R[1, 0], R[0, 0]))),
            "translation_m": translation.tolist(),
            "rmse_m": float(rmse),
            "max_error_m": float(max_error),
            "reference_center_gps": [TECATE_LAT_CENTER, TECATE_LON_CENTER]
        }
        
        return result
        
    def save_alignment_to_json(self, export_path="export/terrain_alignment.json") -> str:
        """
        Computes the alignment and saves the resulting dictionary to export_path.
        """
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        alignment_data = self.compute_alignment()
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(alignment_data, f, indent=4)
        print(f"[TerrainAligner] Saved alignment matrix to: {export_path}")
        return export_path
