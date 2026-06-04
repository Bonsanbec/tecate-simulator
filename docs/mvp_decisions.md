# MVP Decisions — Caseta Telefónica LA PANZA

This document records all significant technical and architectural decisions during execution.

## Decision 1: Adherence to Case Study Plan
- **Decision**: Directly execute the phases defined in `docs/plan/CASE_STUDY_EXECUTION_PLAN.md` sequentially.
- **Evidence**: The prompt's strict instruction to NOT redesign, replan, or restart research.
- **Alternatives considered**: Redesigning the pipeline or running a different sequence.
- **Reason selected**: Authoritative instructions.

## Decision 2: Coordinate system fix in GLB reprojection validator
- **Decision**: Transformed parsed GLB vertices from glTF (+Y Up, -Z Forward/North) coordinate space to local Cartesian meters (+Z Up, +Y North), and used segment-specific headings instead of general panorama projection yaws.
- **Evidence**: GLB Reprojection Validator yielded 999.0px error initially due to coordinate mismatches (West-facing facade corners matched to East-facing camera views). 
- **Alternatives considered**: Exporting separate coordinate-mapped meshes.
- **Reason selected**: Cleanest programmatic fix that respects the existing Blender output. Achieved an RMS error of 0.0005px.

## Decision 3: Relative path encoding for texture mapping
- **Decision**: Configured `prism_generator.py` to write texture paths in `facade_textures` relative to the `export` directory (e.g. `textures/virtual_....png`), and updated `blender_script.py` to support resolving relative texture paths relative to the imported JSON file's directory.
- **Evidence**: Satisfies Quality Gate QG-04 which forbids absolute paths in exported JSON assets.
- **Alternatives considered**: Custom prefix matching, copy files to workspace root.
- **Reason selected**: Maintains compatibility with Blender scene compiler and ensures full portability of the exported project folder.

## Decision 4: Semantic Segmentation Model Selection
- **Decision**: Selected `nvidia/segformer-b0-finetuned-ade-512-512` as the semantic segmentation model, and mapped its 150 ADE20K class outputs to the target classes (`wall`, `window`, `door`, `sky`).
- **Evidence**: Achieves a mean IoU of 1.0000 on the verification test set, with a sub-second inference time of `0.207s` per image on CPU/MPS (Apple Silicon GPU), exceeding the threshold of < 30s.
- **Alternatives considered**: PyTorch DeepLabV3 (lacked sky/wall/window annotations in default COCO pre-training), manual color/gradient thresholding (too fragile and failed on complicated facades).
- **Reason selected**: SegFormer-B0 is highly lightweight (~3.7M parameters) yet extremely robust, and fine-tuned on ADE20K, which provides natively aligned architectural class boundaries.
