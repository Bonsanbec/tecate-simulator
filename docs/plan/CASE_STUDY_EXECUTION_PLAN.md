# CASE_STUDY_EXECUTION_PLAN.md
## Reconstruction Target: Caseta Telefónica LA PANZA

---

## 1. Target Identification

| Attribute | Value |
|-----------|-------|
| Building name | Caseta Telefónica LA PANZA |
| Street | Pdte. Abelardo L. Rodríguez |
| City | Tecate, Baja California, Mexico |
| Reference GPS (camera) | 32.5728966°N, 116.6245526°W |
| Reference heading | 263.88° (nearly due West) |
| Reference pitch | 80.92° (angled downward) |
| Reference FOV parameter | 75y (75° FOV) |
| Google Maps reference URL | `@32.5728966,-116.6245526,3a,75y,263.88h,80.92t` |
| Target epoch | 2009 (historical) |

---

## 2. Confirmed Repository Status (From Inspection)

The following facts were confirmed from direct data file inspection on 2026-06-01:

### 2.1 Block Identification

| Property | Value | Confidence |
|----------|-------|-----------|
| Target block_id | `block_lat_32.57293_lon_-116.62389` | HIGH — nearest block to reference GPS |
| Block centroid local | (248.77m, -19.81m) | HIGH |
| Distance from reference GPS | ~65m | HIGH — centroid-to-target, not face-to-camera |
| Block in reconstruction_export.json | YES | HIGH |
| Block polygon vertices | 194 (pre-shrink) | HIGH |
| Block height estimate | 8.37m | HIGH |
| Block area | 19,435 m² | HIGH |

**Important**: The block contains the ENTIRE city block (manzana), not just the Caseta Telefónica building. The target facade is one or more segments of this large polygon.

### 2.2 Facade Data Status

| Property | Value | Confidence |
|----------|-------|-----------|
| Facade entries in facades_cache | 193 | HIGH |
| `facade_midpoint_local` populated | NO — all null | HIGH (confirmed by inspection) |
| Facade textures in reconstruction_export | 193/193 real (no transparent fallback) | HIGH |
| Panorama dates for this block | 2009-08, 2009-09 (from sample) | HIGH |
| `road_relation` field | Null for this block | HIGH |

### 2.3 Road Identification

| Property | Value | Confidence |
|----------|-------|-----------|
| Road name | "Calle Presidente Abelardo L. Rodriguez" | HIGH |
| OSM edge IDs | `e_1367` through `e_1385` (19 edges) | HIGH |
| Road direction | Runs approximately East-West | MEDIUM (from edge endpoints) |

### 2.4 Image Coverage

| Property | Value | Confidence |
|----------|-------|-----------|
| Screenshots available for this block | Unknown — not directly inspected | LOW |
| Pano_ids for target facades | Multiple — from 2009-08, 2009-09 batches | MEDIUM |
| Expected heading range for W-facing facade | 260–270° (confirming camera faces East to view W-facing facade) | HIGH |

---

## 3. Prerequisite Verification Checklist

Before beginning reconstruction, verify each item:

```
[ ] QG-01 PASS: tests/unit/test_coords.py all pass
[ ] P00-T001 DONE: prism_generator.py line 766 fixed (my - my → my - uy)
[ ] block_lat_32.57293_lon_-116.62389 exists in data/blocks_cache.json
[ ] 193 facade entries exist in data/facades_cache.json with prefix block_lat_32.57293_lon_-116.62389
[ ] data/case_study/ directory created
[ ] data/case_study/target_facade.json created (P01-T007)
[ ] data/case_study/recomputed_midpoints.json created (P01-T008)
[ ] data/case_study/target_panoramas.json created (P01-T009)
[ ] At least 1 image in data/case_study/target_images/ (P01-T010)
[ ] QG-02 PASS: data/case_study/QG02_report.json status = PASS
```

---

## 4. Step-by-Step Execution Plan

### STEP 1: Identify Target Facade Segments (P01-T007)

**Command**:
```bash
PYTHONPATH=. python3 scripts/identify_target_facade.py
```

**Expected output**: `data/case_study/target_facade.json` with:
- `target_facade_indices`: list of 5–20 consecutive facade indices
- `heading_to_face_facade`: approximately 83–87° (inward heading of E-facing facade, camera looks from East)
- `alignment_dot_product`: > 0.7 (high alignment with reference heading 263.88° = looking West)
- `associated_road_name`: contains "Abelardo" or "Rodriguez"

**Technical note on heading geometry**:
- Reference heading = 263.88° (camera pointing West, toward a West-facing facade)
- Wait — a camera at heading 263.88° is looking West. For a facade to be visible from this heading, the facade must have its **outward normal pointing East** (because the camera is West of the facade, looking East at it)
- Outward normal direction: approximately `[1, 0]` (East = positive X in local coords)
- Inward heading (camera direction to face the facade): `atan2(-1, -0) * 180/π + 360 = 270°`
- Confirmation: 263.88° ≈ 270° — **consistent** with a facade whose outward normal points East
- Therefore: target facades are the **East-facing** segments of the block polygon
- Use `cardinal_from_normal([nx, ny])`: facade segments where `nx > abs(ny)` are East-facing

### STEP 2: Recompute Midpoints (P01-T008)

**Command**:
```bash
PYTHONPATH=. python3 scripts/recompute_midpoints.py
```

**Expected output**: All 193 facade entries updated in `data/facades_cache.json`

### STEP 3: Collect Images (P01-T009 + P01-T010)

**Command**:
```bash
PYTHONPATH=. python3 scripts/collect_case_study_images.py
```

**Expected**: At least 1 PNG in `data/case_study/target_images/`

### STEP 4: Validate Dataset (P01-T011 → QG-02)

**Command**:
```bash
PYTHONPATH=. python3 scripts/evaluate_qg02.py
cat data/case_study/QG02_report.json | python3 -c "import json,sys; r=json.load(sys.stdin); print(r['status'])"
```

**Expected**: `PASS`

### STEP 5: Camera Pose Validation (P02-T012)

**Command**:
```bash
PYTHONPATH=. python3 -c "
from src.reconstruction.pose_validator import PoseValidator
import json
panos = json.load(open('data/case_study/target_panoramas.json'))
facade = json.load(open('data/case_study/target_facade.json'))
pv = PoseValidator()
for p in panos['panoramas']:
    result = pv.validate(p, facade)
    print(result['pano_id'], result['status'], result['alignment_dot_product'])
"
```

**Expected**: At least 1 entry with status=VALID

### STEP 6: Extract Facade Texture (P02-T013)

**Command**:
```bash
PYTHONPATH=. python3 scripts/extract_case_study_texture.py
```

**Expected output**: `export/case_study/target_facade_texture.png` with coverage_pct ≥ 50%

### STEP 7: Build 3D Block Mesh (P02-T014)

**Command**:
```bash
PYTHONPATH=. python3 scripts/build_case_study_block.py
# This script will internally call Blender in headless mode
```

**Expected output**: `export/case_study/target_block.glb` > 10KB

### STEP 8: Reprojection Validation (P02-T015 → QG-03)

**Command**:
```bash
PYTHONPATH=. python3 -c "
from src.qa.reprojection_validator import ReprojectionValidator
import json
panos = json.load(open('data/case_study/target_panoramas.json'))
facade = json.load(open('data/case_study/target_facade.json'))
rv = ReprojectionValidator()
result = rv.validate('export/case_study/target_block.glb', panos, facade)
print('RMS:', result['rms_reprojection_error_px'])
print('Status:', result['status'])
"
```

**Expected**: `rms_reprojection_error_px < 5.0`, status = PASS

### STEP 9: Final Quality Report (P02-T016)

**Command**:
```bash
PYTHONPATH=. python3 scripts/generate_phase2_report.py
cat export/case_study/phase2_quality_report.json | python3 -c "import json,sys; r=json.load(sys.stdin); print(r['overall_status'])"
```

**Expected**: `PASS`

---

## 5. Expected Output Files Summary

After successful completion of the case study execution plan:

```
data/case_study/
├── case_study_manifest.json           # Dataset manifest
├── QG02_report.json                   # QG-02 pass report
├── target_facade.json                 # Identified facade segments
├── target_panoramas.json              # Camera parameters
├── recomputed_midpoints.json          # Facade midpoints
├── pose_validation_report.json        # Camera pose validation
└── target_images/
    └── {pano_id}_yaw_*.png           # Source images

export/case_study/
├── target_facade_texture.png          # 512×512 RGBA facade texture
├── texture_extraction_report.json     # Coverage + quality
├── target_block_scene.json            # Single-block scene document
├── target_block.glb                   # 3D block mesh
├── reprojection_validation.png        # Projection overlay
├── reprojection_report.json           # QG-03 metrics
└── phase2_quality_report.json         # Aggregated quality report
```

---

## 6. Known Uncertainties Specific to This Target

1. **The block is large** (19,435 m²) — it encompasses the entire manzana (city block), not just La Panza. The target facade is a subset of the 193 total facades. This makes facade identification in P01-T007 non-trivial.

2. **The pitch in the reference URL is 80.92°** — this indicates the reference camera was looking steeply upward (near-vertical), which is unusual for a typical facade capture. This may mean the actual SV photo of the facade is taken from a different position with a different heading. The 263.88° heading is the primary reference for facade normal orientation.

3. **The block_id centroid is 65m from the reference GPS** — this is expected for a block-level identifier; the facade face itself is much closer to the reference GPS (within ~5–15m).

4. **Facade textures are already in reconstruction_export.json** — the existing pipeline has already produced textures for this block. The case study execution plan will produce a *separate*, *explicitly documented* version of these textures with full traceability metadata. This is intentional for validation purposes.
