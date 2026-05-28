# Tecate Terrain Model

## Overview

This repository contains the primary terrain model used for the Tecate Simulator project. The model represents the geographical and environmental structure of the region surrounding Tecate, Baja California, including terrain elevation, roads, vegetation, water bodies, and partial urban geometry.

The model was generated from official geographic boundary data obtained from INEGI and projected onto a topographic terrain source to produce a spatially coherent 3D environment.

The purpose of this asset is not strict administrative representation. Its function is to reproduce the spatial and visual experience of the region.

---

## Source Data

Primary geographic reference:

- INEGI municipal polygon dataset
- Coordinate system preserved from original GeoJSON source
- Original polygon stored without modification

The original GeoJSON acts as the canonical geospatial reference for the project.

---

## Boundary Extension

One polygon vertex was intentionally modified before mesh extraction.

The original upper-left vertex of the INEGI polygon was displaced toward Donohue Mountain in order to include the complete silhouette of Cerro Cuchumá inside the rendered environment.

This modification exists exclusively to improve environmental continuity and long-range visual coherence inside the simulator.

No other polygon vertices were modified.

The resulting terrain model therefore represents an extended experiential domain rather than a strict municipal boundary.

---

## Model Characteristics

Current versions of the model may include:

- Terrain elevation
- Satellite or terrain textures
- Roads and pathways
- Water bodies
- Vegetation layers
- Partial building geometry

Building geometry is considered provisional and non-authoritative. Terrain and spatial layout are treated as the stable foundation of the simulation.

---

## Spatial Integrity

The model preserves alignment with the original INEGI polygon except for the single documented boundary extension.

The GeoJSON source should always be treated as the primary coordinate reference.

The GLB model should be treated as a derived asset.

---

## Intended Usage

This model is intended for:

- Real-time rendering
- Terrain streaming
- Spatial simulation
- Environmental visualization
- Navigation systems
- Historical or temporal urban overlays

The terrain base is designed to remain stable across multiple simulated time periods.

---

## Recommended Pipeline

1. Load original GeoJSON boundary data.
2. Apply documented boundary extension.
3. Generate terrain projection.
4. Apply texture and environmental layers.
5. Export GLB terrain asset.
6. Split terrain into streaming tiles if required.

---

## Repository Notes

Large GLB files should eventually be partitioned into smaller spatial chunks for streaming and runtime performance.

Future versions may separate terrain, vegetation, water, roads, and structures into independent layers.

The original source polygon must remain preserved for reproducibility and GIS compatibility.