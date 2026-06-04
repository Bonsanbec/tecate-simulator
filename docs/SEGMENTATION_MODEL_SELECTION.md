# SEGMENTATION_MODEL_SELECTION.md
## Target Model: nvidia/segformer-b0-finetuned-ade-512-512

---

## 1. Selected Model Architecture

| Attribute | Value |
|-----------|-------|
| Model Name | `nvidia/segformer-b0-finetuned-ade-512-512` |
| Backbone | SegFormer-B0 (MiT-B0) |
| Parameters | ~3.7 Million (extremely lightweight, CPU-friendly) |
| Pre-training Dataset | ImageNet-1K |
| Fine-tuning Dataset | ADE20K (150 semantic classes) |
| Framework | PyTorch (Hugging Face Transformers) |
| License | NVIDIA Proprietary (Non-commercial / Evaluation, compatible with academic/MVP replication) |

---

## 2. Rationale for Selection

1. **CPU Inference Time**: The MiT-B0 backbone is designed for real-time inference. On standard CPU environments, it runs in **< 0.5 seconds per image**, comfortably satisfying the QG-05 requirement of < 30 seconds per image.
2. **ADE20K Semantic Classes**: The model is fine-tuned on ADE20K, which contains precise annotations for `wall`, `building`, `windowpane` (window), `door`, and `sky`. This maps directly to our target classes for historical Tecate facade parsing.
3. **Robustness to Low Resolution**: Street View screenshots from 2009 can be noisy, but SegFormer's hierarchical Transformer encoder preserves high-frequency structural details better than traditional CNN models.

---

## 3. Class Index Mapping

We map the 150 ADE20K semantic classes to the target subset required for Tecate reconstruction:

| Target Class | ID | ADE20K Source Classes | ADE20K Index |
|--------------|----|-----------------------|--------------|
| `wall` | 0 | `wall`, `building` | 0, 1 |
| `window` | 1 | `windowpane` | 8 |
| `door` | 2 | `door`, `screen door` | 14, 58 |
| `sky` | 3 | `sky` | 2 |
| `other` | 4 | All remaining classes | * (all others) |

---

## 4. Weight Cache Configuration

The model weights and configuration will be cached locally at:
```
models/segmentation/
```
To ensure offline reproducibility and prevent repeated downloads in production.
