# CASE_STUDY_BASELINE.md
## Reconstruction Baseline: Caseta Telefónica LA PANZA

This document establishes the verified baseline dataset for the reconstruction case study of the "Caseta Telefónica LA PANZA" building.

## 1. Study Case Metadata
- **Target Name**: Caseta Telefónica LA PANZA
- **Street**: Pdte. Abelardo L. Rodríguez (Calle Presidente Abelardo L. Rodriguez)
- **Reference GPS (Camera Location)**: 32.5728966°N, 116.6245526°W
- **Target Block ID**: `block_lat_32.57255_lon_-116.62529` (Enclosed by Libertad, Hidalgo, Abelardo and Ortiz)
- **Target Facade Indices**: `[68, 69, 70, 71, 72, 73, 74, 75, 76, 77]` (10 consecutive facade segments)
- **Target Epoch**: 2009 (historical Street View imagery)

## 2. Spatial and Geometric Constraints
- **Parque Hidalgo Local Origin**: `(32.573229, -116.626536)` (0m East, 0m North)
- **Reference Camera Local Position**: `(186.06m East, -37.00m North)`
- **Facade Segment Local Centroid**: `(180.50m East, -45.92m North)`
- **Minimum Distance to Reference GPS**: `6.95m` (at index 74)
- **Average Camera Face Heading**: `266.30°` (pointing nearly due West to capture the East-facing facades)

## 3. Panorama and Image Corpus
The dataset includes the following panoramas and corresponding image slices covering the target facade:

| Panorama Pano ID | Capture Date | Coordinates (GPS) | Camera Heading | Image File Path |
|---|---|---|---|---|
| `YABJGX-e_8PlcHtxqOeH_Q` | 2009-09 | `(32.57289656, -116.62455257)` | 266.40° | `data/case_study/target_images/YABJGX-e_8PlcHtxqOeH_Q_yaw_266.40.png` |
| `bG_8WXlp2kwvzG4-YGS8NA` | 2009-09 | `(32.57281392, -116.62450849)` | 266.36° | `data/case_study/target_images/bG_8WXlp2kwvzG4-YGS8NA_yaw_266.36.png` |
| `vN2_i6UDp-AIkbp92Eck1g` | 2009-09 | `(32.57294862, -116.62463991)` | 266.40° | `data/case_study/target_images/vN2_i6UDp-AIkbp92Eck1g_yaw_266.40.png` |
| `U3j8MuOuTzqh8AM3aETPKA` | 2009-09 | `(32.57303038, -116.62475459)` | 266.40° | `data/case_study/target_images/U3j8MuOuTzqh8AM3aETPKA_yaw_266.40.png` |
| `9P7D9fOAAmr6ulGfWIpgsg` | 2009-09 | `(32.57312108, -116.62489812)` | 266.40° | `data/case_study/target_images/9P7D9fOAAmr6ulGfWIpgsg_yaw_266.40.png` |

All 5 images are verified to be fully downloaded PNG files (1.2MB+ on disk) and are symlinked into `data/case_study/target_images/`.
