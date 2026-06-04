# Purpose: Implements semantic segmentation for facade imagery to detect wall, window, door, and sky pixels.
# Inputs: Image file path, or PIL Image object.
# Outputs: 2D uint8 numpy array containing segment class IDs (0: wall, 1: window, 2: door, 3: sky, 4: other).
# Responsibilities: Loads SegFormer-B0 model, performs pre-processing, runs inference, upsamples logits, and maps classes.
# Dependencies: torch, transformers, PIL, numpy, os

import os
import numpy as np
import torch
from PIL import Image
from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation

class FacadeSegmentationAgent:
    """
    Facade semantic segmentation agent utilizing a pre-trained SegFormer model.
    """
    def __init__(self, model_name: str = "nvidia/segformer-b0-finetuned-ade-512-512", cache_dir: str = "models/segmentation"):
        self.model_name = model_name
        self.cache_dir = cache_dir
        
        # Select device: GPU, macOS MPS, or CPU
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")
            
        print(f"[FacadeSegmentationAgent] Initializing on device: {self.device}")
        
        # Load processor and model
        self.processor = SegformerImageProcessor.from_pretrained(
            self.model_name, 
            cache_dir=self.cache_dir
        )
        self.model = SegformerForSemanticSegmentation.from_pretrained(
            self.model_name, 
            cache_dir=self.cache_dir
        ).to(self.device)
        self.model.eval()

    def predict(self, image_input) -> np.ndarray:
        """
        Runs semantic segmentation on the input image.
        Args:
            image_input (str or PIL.Image.Image): Path to image file or PIL Image object.
        Returns:
            np.ndarray: 2D uint8 array of shape (H, W) with mapped class IDs.
        """
        # Load image if path provided
        if isinstance(image_input, str):
            if not os.path.exists(image_input):
                raise FileNotFoundError(f"Image file not found: {image_input}")
            img = Image.open(image_input).convert("RGB")
        else:
            img = image_input.convert("RGB")
            
        w, h = img.size
        
        # Pre-process
        inputs = self.processor(images=img, return_tensors="pt").to(self.device)
        
        # Run inference
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        # Interpolate logits to original image size
        # logits shape: (batch_size, num_labels, height/4, width/4)
        logits = outputs.logits
        
        # Upsample logits to original size
        upsampled_logits = torch.nn.functional.interpolate(
            logits,
            size=(h, w),
            mode="bilinear",
            align_corners=False
        )
        
        # Get argmax classes
        pred_labels = upsampled_logits.argmax(dim=1)[0].cpu().numpy().astype(np.uint8)
        
        # Map ADE20K classes (150 labels) to our 5 target classes:
        # 0: wall (ADE20K 0: wall, 1: building)
        # 1: window (ADE20K 8: windowpane)
        # 2: door (ADE20K 14: door, 58: screen door)
        # 3: sky (ADE20K 2: sky)
        # 4: other (all other classes)
        mapped_labels = np.full_like(pred_labels, 4, dtype=np.uint8)
        
        mapped_labels[(pred_labels == 0) | (pred_labels == 1)] = 0  # wall
        mapped_labels[pred_labels == 8] = 1                         # window
        mapped_labels[(pred_labels == 14) | (pred_labels == 58)] = 2 # door
        mapped_labels[pred_labels == 2] = 3                         # sky
        
        return mapped_labels
