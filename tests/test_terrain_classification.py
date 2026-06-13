import pytest
import os
import json
from src.minecraft_pipeline.exporter import TerrainClassificationIndex

def test_terrain_classification_math():
    # Construct a mock classification index with a single polygon
    # Polygon points in MC space:
    # A rectangle from X=[10, 20], Z=[10, 20]
    
    interp = TerrainClassificationIndex.__new__(TerrainClassificationIndex)
    interp.cell_size = 100.0
    interp.polygons = [
        {
            "vertices": [(10.0, 10.0), (20.0, 10.0), (20.0, 20.0), (10.0, 20.0)],
            "class": "paved",
            "bbox": (10.0, 20.0, 10.0, 20.0),
            "bbox_area": 100.0
        }
    ]
    interp.grid = {(0, 0): [0]}
    
    # Point inside: (15, 15)
    assert interp.point_in_poly(15.0, 15.0, interp.polygons[0]["vertices"])
    
    # Point outside: (5, 5)
    assert not interp.point_in_poly(5.0, 5.0, interp.polygons[0]["vertices"])

def test_terrain_classification_json():
    # Verify that the classifier index successfully loads from a real JSON file if present
    json_path = "export/terrain_classification.json"
    if os.path.exists(json_path):
        idx = TerrainClassificationIndex(json_path)
        assert len(idx.polygons) > 0
        assert len(idx.grid) > 0
