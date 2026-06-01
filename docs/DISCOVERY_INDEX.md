# DISCOVERY_INDEX.md — Tecate Simulator Technical Discovery

**Repository**: `Bonsanbec/tecate-simulator`  
**Discovery date**: 2026-06-01  
**Document set**: 7 deliverables (A–G)

---

## Document Set

| # | Document | Description |
|---|----------|-------------|
| A | [REPOSITORY_OVERVIEW.md](./REPOSITORY_OVERVIEW.md) | Architecture, directory tree, module map, CLI, pipeline summary, constants |
| B | [DATA_MODEL.md](./DATA_MODEL.md) | All datasets: schemas, field definitions, record counts, ER diagram |
| C | [GEOSPATIAL_MODEL.md](./GEOSPATIAL_MODEL.md) | Coordinate systems, projection math, camera model, UV layout |
| D | [ASSET_INVENTORY.md](./ASSET_INVENTORY.md) | Complete inventory of terrain models, caches, textures, exports |
| E | [PIPELINE_RECONSTRUCTION.md](./PIPELINE_RECONSTRUCTION.md) | Step-by-step pipeline: all 6 stages with method citations |
| F | [CODEBASE_ANALYSIS.md](./CODEBASE_ANALYSIS.md) | Module APIs, design patterns, known bugs, algorithmic choices |
| G | [RECONSTRUCTION_READINESS.md](./RECONSTRUCTION_READINESS.md) | What is operational, data quality assessment, limitations |
| H | [UNKNOWNS_AND_GAPS.md](./UNKNOWNS_AND_GAPS.md) | All unknowns, gaps, and open questions (21 items, severity-graded) |

---

## Critical Findings Summary

### Confirmed Operational
- Full pipeline from OSM → glTF is functional and has produced output
- 4,239 city blocks detected; 159 currently reconstructed at **99.84% facade coverage**
- 3,906 panoramas cached; **~80% from 2009** epoch
- Three terrain GLB variants available; largest is 95.5 MB with buildings

### Critical Gaps
1. **Terrain-reconstruction coordinate alignment is undefined** (A-1 in UNKNOWNS)
2. **~19% of panoramas are post-2009** — temporal leakage is unmitigated (C-1)
3. **`TemporalVisualClassifier` exists but is not wired** into the live pipeline (B-1)
4. **Only 3.75% of city blocks are in the current export** (processing is ongoing)

### Known Bug
- `get_road_distance()` has a typo (`my - my` instead of `my - uy`) causing incorrect road distance calculations for diagonal street segments

### Key Architecture Facts
- All geometry in **local Cartesian meters** relative to Parque Hidalgo (32.573229°N, 116.626536°W)
- Three-table relational cache: `panoramas_cache` (3,906) + `facades_cache` (22,289) + `blocks_cache` (4,239)
- Pipeline sorts blocks by distance from center — city core reconstructed first
- Blender embedded script enables real-time viewport culling with a dedicated N-panel UI

---

## Quick Reference: File Locations

```
data/
  tecate_osm_cache.json     82k nodes, 87k edges (OSM road graph)
  blocks_cache.json         4,239 blocks (polygons + heights)
  facades_cache.json        22,289 facades (observations)
  panoramas_cache.json      3,906 panoramas (metadata + dates)

export/
  reconstruction_export.json  159 blocks, 37 MB (scene document)
  metadata.json               coverage 99.84%, provenance (9 MB)
  geometry.gltf               final 3D scene (glTF separate)
  textures/                   per-block RGBA facade PNGs

models/tecate/
  glb/  (3 terrain variants, 86–95 MB each)
  babylon/  (3 terrain variants, 273–325 MB each)

src/
  main.py                     CLI entry point
  reconstruction/prism_generator.py   core (2,673 lines)
  data_acquisition/browser_scraper.py  Playwright + photometa (701 lines)
  gis_graph/graph_builder.py          OSM graph builder
  temporal_filter/classifier.py       CV temporal classifier (unused)
  core_io/coords.py                   GPS ↔ local transform
```
