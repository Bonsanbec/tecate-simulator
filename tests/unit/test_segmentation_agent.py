# Purpose: Unit tests for FacadeSegmentationAgent to verify prediction shapes, type correctness, and range safety.
# Inputs: Test runner triggers, dummy image inputs.
# Outputs: Test assertion results.
# Responsibilities: Asserts output shape matches input shape, verifies output dtype is uint8, and validates label mapping bounds.
# Dependencies: pytest, numpy, PIL, src.segmentation.segmentation_agent

import pytest
import numpy as np
from PIL import Image
from src.segmentation.segmentation_agent import FacadeSegmentationAgent

def test_segmentation_agent_prediction():
    # 1. Initialize agent (uses local cache models/segmentation)
    agent = FacadeSegmentationAgent()
    
    # 2. Create a dummy solid image (128x128 px)
    img_size = (128, 128)
    dummy_img = Image.new("RGB", img_size, color=(128, 128, 128))
    
    # 3. Predict mask
    mask = agent.predict(dummy_img)
    
    # 4. Assertions
    assert isinstance(mask, np.ndarray), "Output must be a numpy array!"
    assert mask.shape == (img_size[1], img_size[0]), f"Output shape {mask.shape} does not match input shape (128, 128)!"
    assert mask.dtype == np.uint8, "Output array dtype must be uint8!"
    
    # Assert values are within target bounds [0, 4]
    unique_vals = np.unique(mask)
    for val in unique_vals:
        assert 0 <= val <= 4, f"Found out-of-bounds label value: {val} (must be in range 0-4)"
        
    print("Unit test passed: segmentation prediction shape and types verified.")
