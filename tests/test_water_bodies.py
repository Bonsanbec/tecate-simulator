import pytest
import os
from src.minecraft_pipeline.exporter import TerrainWaterInterpolator

def test_water_interpolator_math():
    # Construct a mock interpolator with a single triangle in X-Z space:
    # A = (0, 10.0, 0)
    # B = (10.0, 20.0, 0)
    # C = (0, 30.0, 10.0)
    # Projected onto X-Z plane: A=(0,0), B=(10,0), C=(0,10)
    
    interp = TerrainWaterInterpolator.__new__(TerrainWaterInterpolator)
    interp.cell_size = 100.0
    interp.triangles = [
        ((0.0, 10.0, 0.0), (10.0, 20.0, 0.0), (0.0, 30.0, 10.0))
    ]
    interp.grid = {(0, 0): [0]}
    
    # Point inside: (2, 2)
    # u = 0.2 (towards C), v = 0.2 (towards B)
    # y = 10.0 + 0.2*(30.0-10.0) + 0.2*(20.0-10.0) = 16.0
    is_w, y_w = interp.query_water(2.0, 2.0)
    assert is_w
    assert abs(y_w - 16.0) < 1e-5
    
    # Point outside: (8, 8)
    is_w_out, _ = interp.query_water(8.0, 8.0)
    assert not is_w_out

def test_water_interpolator_glb():
    glb_path = "models/tecate/glb/tecate.glb"
    if os.path.exists(glb_path):
        interp = TerrainWaterInterpolator(
            glb_path,
            s=0.8427785648661434,
            tx=28052.404303473268,
            tz=-16620.3853885848
        )
        assert len(interp.triangles) > 0
        assert len(interp.grid) > 0
        
        # Test query for a coordinate that is outside any water body
        is_w, _ = interp.query_water(0.0, 0.0)
        assert not is_w
