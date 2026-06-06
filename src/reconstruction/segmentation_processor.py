import os
import torch
import numpy as np
from PIL import Image
from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation

class SegmentationProcessor:
    """
    Runs semantic segmentation using SegFormer-B0 finetuned on ADE20K.
    Used to locate walls, windows, and doors on facade images.
    """
    def __init__(self, model_name="nvidia/segformer-b0-finetuned-ade-512-512"):
        # Select device: use Apple Silicon MPS if available, otherwise CPU
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")
            
        print(f"[SegmentationProcessor] Initializing SegFormer model '{model_name}' on device: {self.device}")
        self.processor = SegformerImageProcessor.from_pretrained(model_name)
        self.model = SegformerForSemanticSegmentation.from_pretrained(model_name).to(self.device)
        self.model.eval()

    def segment_image(self, image: Image.Image) -> np.ndarray:
        """
        Segments a PIL image and returns an integer class map of the same spatial dimensions.
        """
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits  # shape (1, num_classes, height/4, width/4)
            
            # Interpolate logits to original image size (width, height) -> shape expected (height, width)
            upsampled_logits = torch.nn.functional.interpolate(
                logits,
                size=image.size[::-1],  # (height, width)
                mode="bilinear",
                align_corners=False
            )
            
            # Argmax over class dimension to get the mask
            mask = upsampled_logits.argmax(dim=1)[0].cpu().numpy()
            
        return mask
