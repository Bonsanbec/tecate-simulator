import time
from src.core_io.io_manager import save_json

class BlenderSceneExporter:
    """
    Formulates and writes the structured JSON intermediate representation 
    of the reconstructed 3D city scene for direct consumption by Blender.
    """
    def __init__(self, export_path: str = "export/reconstruction_export.json"):
        self.export_path = export_path

    def export_scene(self, 
                     G, 
                     camera_stations: list[dict], 
                     aligned_panos: list[dict], 
                     point_cloud: list[dict], 
                     blocks: list[dict], 
                     block_texture_atlases: list[dict]) -> str:
        """
        Gathers all modules' outputs, builds a cohesive JSON structure, and writes to disk.
        """
        # 1. Format Road Network Graph
        export_nodes = []
        for n_id, data in G.nodes(data=True):
            export_nodes.append({
                "id": n_id,
                "x": float(data["x"]),
                "y": float(data["y"]),
                "latitude": float(data["lat"]),
                "longitude": float(data["lon"]),
                "name": data.get("name", "")
            })
            
        export_edges = []
        for u, v, data in G.edges(data=True):
            export_edges.append({
                "u": u,
                "v": v,
                "id": data["id"],
                "name": data.get("name", ""),
                "length_meters": float(data["length"])
            })
            
        # 2. Format Camera Poses
        # Link aligned panoramas and virtual cameras
        pano_lookup = {p["station_id"]: p for p in aligned_panos}
        export_cameras = []
        for cam in camera_stations:
            s_id = cam["station_id"]
            pano = pano_lookup.get(s_id)
            
            export_cameras.append({
                "station_id": s_id,
                "edge_id": cam["edge_id"],
                "x": float(cam["x"]),
                "y": float(cam["y"]),
                "latitude": float(cam["latitude"]),
                "longitude": float(cam["longitude"]),
                "road_heading": float(cam["road_heading"]),
                "pano_id": pano["pano_id"] if pano else "none",
                "temporal_probability": float(pano["temporal_probability"]) if pano else 0.0,
                "accepted": bool(pano["accepted"]) if pano else False
            })

        # 3. Format Blocks (Manzanas) and Texture Mappings
        atlas_lookup = {a["block_id"]: a for a in block_texture_atlases}
        export_blocks = []
        
        for bl in blocks:
            b_id = bl["block_id"]
            atlas = atlas_lookup.get(b_id)
            
            export_blocks.append({
                "block_id": b_id,
                "polygon": [[float(pt[0]), float(pt[1])] for pt in bl["polygon"]],
                "centroid": [float(bl["centroid"][0]), float(bl["centroid"][1])],
                "height_meters": float(bl["height"]),
                "point_count": len(bl["point_cloud"]),
                "point_cloud": bl["point_cloud"], # List of {coord: [x,y,z], color: [r,g,b]}
                "texture_atlas_filename": atlas["atlas_filename"] if atlas else "none",
                "texture_atlas_path": atlas["atlas_path"] if atlas else "none",
                "uv_mappings": atlas["uv_mappings"] if atlas else {},
                "traceability": atlas["traceability"] if atlas else []
            })

        # 4. Master Orchestration Document
        scene_doc = {
            "system": "Tecate 2009 Urban Reconstruction",
            "export_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "domain": "Tecate, Baja California, Mexico",
            "road_graph": {
                "nodes": export_nodes,
                "edges": export_edges
            },
            "cameras": export_cameras,
            "sparse_point_cloud": point_cloud,  # Full global point cloud list of {coord: [x,y,z], color: [r,g,b]}
            "blocks": export_blocks
        }
        
        save_json(scene_doc, self.export_path)
        print(f"[Export] Reconstructed scene successfully exported to: {self.export_path}")
        return self.export_path
