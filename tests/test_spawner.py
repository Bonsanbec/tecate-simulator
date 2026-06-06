import numpy as np
import pytest

from src.reconstruction.prop_spawner import PropSpawner

def test_prop_spawner_initialization():
    spawner = PropSpawner()
    assert spawner.pixel_per_meter == 100.0
    assert spawner.label_window == 8
    assert spawner.label_door == 14

def test_prop_spawner_extraction():
    spawner = PropSpawner()
    
    # Create 200x200 mask
    mask = np.zeros((200, 200), dtype=np.uint8)
    # Draw a window (rect of label 8)
    mask[50:100, 20:80] = 8
    # Draw a door (rect of label 14)
    mask[120:190, 110:150] = 14
    
    # Facade segment: from (0,0) to (10,0)
    A = [0.0, 0.0, 0.0]
    B = [10.0, 0.0, 0.0]
    base_z = 0.0
    height = 3.0
    
    props = spawner.extract_props(mask, A, B, base_z, height, facade_id="test_facade")
    
    # Should find window (sill, maybe awning) and door (sign)
    assert len(props) > 0
    
    types = [p["prop_type"] for p in props]
    assert "window_sill" in types
    assert "sign" in types
    
    # Check window sill position:
    # u_ctr of window (20 to 80) is (20+80)/2 = 50 -> 50 / 200 = 0.25
    # Along AB (from 0 to 10), horizontal position should be 0.25 * 10 = 2.5
    # v_max is 100 -> 100 / 200 = 0.5
    # vertical height of sill should be base_z + (1 - v_max)*height = 0 + (1 - 0.5)*3 = 1.5
    sill = [p for p in props if p["prop_type"] == "window_sill"][0]
    assert abs(sill["position"][0] - 2.5) < 0.01
    assert abs(sill["position"][1] - 0.0) < 0.01
    assert abs(sill["position"][2] - 1.5) < 0.01
