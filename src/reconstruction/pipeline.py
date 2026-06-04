# Purpose: Configurable reconstruction pipeline class wrapping road graph builder, block reconstruction, validation, and export.
# Inputs: Path to a JSON configuration file, or a configuration dictionary.
# Outputs: Path to the generated reconstruction_export.json, schema validation status.
# Responsibilities: Manages GIS database query, coordinates UrbanBlockReconstructor execution, validates output schema, and handles relative path verification.
# Dependencies: json, os, math, src.gis_graph.graph_builder, src.reconstruction.prism_generator

import json
import os
import math
from src.core_io.io_manager import ensure_dir
from src.gis_graph.graph_builder import TecateGraphBuilder
from src.reconstruction.prism_generator import UrbanBlockReconstructor

class ReconstructionPipeline:
    """
    Main entry point for running urban block reconstruction under configurable options.
    """
    def __init__(self, config_data_or_path):
        if isinstance(config_data_or_path, str):
            with open(config_data_or_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = config_data_or_path
            
        # Extract configuration options
        self.export_dir = self.config.get("export_dir", "export")
        self.data_dir = self.config.get("data_dir", "data")
        self.headless = self.config.get("headless", True)
        self.radius = self.config.get("radius", -1.0)
        self.reprocess = self.config.get("reprocess", False)
        self.skip_scraper = self.config.get("skip_scraper", False)
        self.harvest_only = self.config.get("harvest_only", False)
        self.parallel = self.config.get("parallel", 4)
        
    def run(self) -> str:
        """
        Executes the reconstruction pipeline.
        Returns:
            str: Absolute path to the generated reconstruction_export.json.
        """
        print(f"[Pipeline] Starting run. Radius: {self.radius}m, Reprocess: {self.reprocess}, Skip Scraper: {self.skip_scraper}")
        ensure_dir(self.export_dir)
        ensure_dir(os.path.join(self.export_dir, "textures"))
        
        # 1. GIS Road Graph Construction
        print("[Pipeline] Loading road graph network...")
        builder = TecateGraphBuilder(cache_dir=self.data_dir)
        osm_data = builder.fetch_osm_tecate()
        G = builder.build_networkx_graph(osm_data)
        
        # 2. Block Reconstruction & Texturing
        print("[Pipeline] Reconstructing urban block structures...")
        reconstructor = UrbanBlockReconstructor(
            G,
            export_dir=self.export_dir,
            data_dir=self.data_dir,
            headless=self.headless,
            radius=self.radius if self.radius >= 0 else None,
            reprocess=self.reprocess,
            skip_scraper=self.skip_scraper,
            harvest_only=self.harvest_only,
            parallel=self.parallel
        )
        blocks_data, scene_doc = reconstructor.reconstruct_blocks_and_texture()
        
        # 3. Export
        export_path = os.path.join(self.export_dir, "reconstruction_export.json")
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(scene_doc, f, indent=4)
        print(f"[Pipeline] Scene document exported to {export_path}")
        
        # 4. Schema and Format Validation (QG-04)
        self.validate_schema(export_path)
        self.validate_relative_paths(export_path)
        
        return os.path.abspath(export_path)

    def validate_schema(self, export_path: str):
        """
        Validates the output JSON structure against the config_schema.json definition.
        Falls back to custom manual checks if the jsonschema package is unavailable.
        """
        schema_path = os.path.join(os.path.dirname(__file__), "config_schema.json")
        if not os.path.exists(schema_path):
            print(f"[Pipeline Warning] Schema file not found: {schema_path}. Skipping schema verification.")
            return

        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        try:
            import jsonschema
            with open(schema_path, "r", encoding="utf-8") as sf:
                schema = json.load(sf)
            jsonschema.validate(instance=data, schema=schema)
            print("[Pipeline Validation] jsonschema verification: PASS")
        except ImportError:
            print("[Pipeline Info] jsonschema package not found. Running fallback verification...")
            self._manual_schema_validation(data)
            print("[Pipeline Validation] Fallback manual verification: PASS")

    def _manual_schema_validation(self, data: dict):
        """Perform custom schema checks to ensure format compatibility."""
        if "road_graph" not in data or "blocks" not in data:
            raise KeyError("Output JSON must contain 'road_graph' and 'blocks' top-level keys.")
            
        road_graph = data["road_graph"]
        if "nodes" not in road_graph or "edges" not in road_graph:
            raise KeyError("'road_graph' must contain 'nodes' and 'edges' lists.")
            
        blocks = data["blocks"]
        if not isinstance(blocks, list):
            raise TypeError("'blocks' must be a list of block elements.")
            
        for block in blocks:
            for key in ["block_id", "polygon", "height_meters", "centroid", "facade_textures", "uv_mappings", "roof_color"]:
                if key not in block:
                    raise KeyError(f"Block {block.get('block_id', 'unknown')} is missing required key: {key}")
                    
            if not isinstance(block["polygon"], list) or len(block["polygon"]) < 3:
                raise ValueError(f"Block {block['block_id']} must have a valid polygon vertex list.")
            if len(block["centroid"]) != 2:
                raise ValueError(f"Block {block['block_id']} centroid must be a [x, y] coordinate pair.")
            if len(block["roof_color"]) != 3:
                raise ValueError(f"Block {block['block_id']} roof_color must be an [R, G, B] color tuple.")

    def validate_relative_paths(self, export_path: str):
        """
        Validates that all texture paths in facade_textures are relative (not absolute)
        and point to files that exist within the export directory.
        """
        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        blocks = data.get("blocks", [])
        for block in blocks:
            b_id = block["block_id"]
            textures = block.get("facade_textures", {})
            for f_id, tex_path in textures.items():
                if not tex_path:
                    continue
                    
                # 1. Verify no absolute paths
                if tex_path.startswith("/") or (len(tex_path) > 1 and tex_path[1] == ":"):
                    raise ValueError(f"Path verification failed: Block {b_id} facade {f_id} uses absolute texture path: {tex_path}")
                    
                # 2. Verify file exists relative to export directory
                full_path = os.path.join(self.export_dir, tex_path)
                if not os.path.exists(full_path):
                    # We might skip checking fallback transparent image if it's packaged in a different location,
                    # but fallback texture should exist too.
                    if "transparent_facade.png" in tex_path:
                        # Ensure fallback texture exists
                        ensure_dir(os.path.dirname(full_path))
                        # Create a dummy transparent facade if missing on disk
                        if not os.path.exists(full_path):
                            from PIL import Image
                            img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
                            img.save(full_path)
                            print(f"[Pipeline] Created missing transparent fallback texture at: {full_path}")
                    else:
                        raise FileNotFoundError(f"Path verification failed: Block {b_id} facade {f_id} texture not found: {full_path}")
                        
        print("[Pipeline Validation] Relative paths verification: PASS")
