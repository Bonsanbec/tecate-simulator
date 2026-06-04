# Purpose: Integration test to verify that the generalized reconstruction pipeline runs on multiple blocks, produces valid relative paths, and conforms to the output schema.
# Inputs: Test runner triggers, uses data from data/ directory and config_schema.json.
# Outputs: Test assertions and execution metrics.
# Responsibilities: Configures localized pipeline run, validates exported scene files, and asserts QG-04 compliance.
# Dependencies: pytest, os, json, src.reconstruction.pipeline

import os
import json
import pytest
from src.reconstruction.pipeline import ReconstructionPipeline

def test_pipeline_generalized_run():
    # 1. Configure the pipeline for a fast, localized run (150m radius around Parque Hidalgo)
    # This ensures that we reconstruct the target block and several neighboring blocks offline.
    config = {
        "export_dir": "export/test_pipeline",
        "data_dir": "data",
        "headless": True,
        "radius": 150.0,
        "reprocess": True,
        "skip_scraper": True,
        "harvest_only": False,
        "parallel": 2
    }
    
    # Clean up previous test runs if any
    test_export_dir = config["export_dir"]
    import shutil
    if os.path.exists(test_export_dir):
        shutil.rmtree(test_export_dir)
        
    pipeline = ReconstructionPipeline(config)
    export_path = pipeline.run()
    
    # 2. Verify file output exists
    assert os.path.exists(export_path), "reconstruction_export.json was not created!"
    
    with open(export_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # 3. Verify at least 5 blocks are reconstructed
    blocks = data.get("blocks", [])
    print(f"Reconstructed {len(blocks)} blocks in integration test.")
    assert len(blocks) >= 5, f"Expected at least 5 blocks to be reconstructed, but only got {len(blocks)}!"
    
    # 4. Verify no absolute paths in texture references
    for block in blocks:
        textures = block.get("facade_textures", {})
        for f_id, tex_path in textures.items():
            if tex_path:
                assert not tex_path.startswith("/"), f"Absolute Unix path found: {tex_path} in block {block['block_id']}"
                assert ":" not in tex_path, f"Absolute Windows path found: {tex_path} in block {block['block_id']}"
                
                # Check that file exists relative to the test export directory
                full_path = os.path.join(test_export_dir, tex_path)
                assert os.path.exists(full_path), f"Texture file not found on disk: {full_path}"
                
    # 5. Schema verification passes (QG-04)
    # The run() method internally executes schema validation. We will verify here as well.
    pipeline.validate_schema(export_path)
    
    print("Integration test passed: QG-04 criteria met.")
