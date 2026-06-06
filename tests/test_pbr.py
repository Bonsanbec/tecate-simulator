import os
import numpy as np
from PIL import Image
import pytest

from src.reconstruction.segmentation_processor import SegmentationProcessor
from src.reconstruction.pbr_generator import PBRGenerator

def test_segmentation_processor():
    # Create a small dummy image
    img = Image.new("RGB", (64, 64), color=(255, 255, 255))
    processor = SegmentationProcessor()
    mask = processor.segment_image(img)
    
    assert mask.shape == (64, 64)
    assert mask.dtype in (np.int32, np.int64, np.uint8)

def test_pbr_generator():
    # Create dummy image and mask
    img = Image.new("RGB", (64, 64), color=(255, 255, 255))
    mask = np.zeros((64, 64), dtype=np.int32)
    # Put a window in the middle
    mask[20:40, 20:40] = 8
    
    pbr_gen = PBRGenerator()
    albedo_rough, normal_height = pbr_gen.generate_maps(img, mask, facade_id="test_facade")
    
    assert albedo_rough.size == (64, 64)
    assert albedo_rough.mode == "RGBA"
    assert normal_height.size == (64, 64)
    assert normal_height.mode == "RGBA"
    
    ar_np = np.array(albedo_rough)
    nh_np = np.array(normal_height)
    
    # Check that roughness (alpha channel of albedo_rough) is low for windows
    # Window roughness should be 0.1 (*255 = 25)
    # Wall roughness should be 0.8 (*255 = 204)
    roughness_vals = ar_np[..., 3]
    assert roughness_vals[30, 30] == int(0.1 * 255)
    assert roughness_vals[10, 10] == int(0.8 * 255)
    
    # Check that height (alpha channel of normal_height) is recessed for windows
    # Window height should be 0.85 (*255 = 216)
    # Wall height should be 1.0 (*255 = 255)
    height_vals = nh_np[..., 3]
    assert height_vals[30, 30] == int(0.85 * 255)
    assert height_vals[10, 10] == int(1.0 * 255)
    
    # Check that normal map is computed
    # Flat areas should have normal pointing straight up (blue-ish, close to [127, 127, 255])
    normal_rgb = nh_np[..., :3]
    assert normal_rgb[10, 10, 2] > 200  # Blue channel should be strong
