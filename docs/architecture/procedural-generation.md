# Procedural Boundaries in Geospatial Reconstruction

## Principle

The project follows a strict **data-first architecture**. To ensure historical and geospatial authenticity, all structural geography (terrain elevation, road network layouts, building footprints, building massings, and landmarks) must be reconstructed directly from verified real-world sources (OpenStreetMap and Digital Elevation Models).

Procedural generation is **strictly prohibited** from synthesizing, predicting, or altering any structural features of the physical world.

## Permitted Procedural Scopes

Procedural generation may only be utilized as a deterministic decorator to add non-structural microdetail and visual fidelity. The permitted scopes are:

1. **Vegetation**: Scattering of trees, shrubs, and weeds based on satellite reference maps or density zones, provided it does not obscure road layouts or landmark visibility.
2. **Textures**: Materials, procedural shader detail, aging/weathering effects, color variation on surfaces, and micro-terrain noise (non-structural surface displacement under 15cm).
3. **Microdetail**: Non-structural props such as trash cans, utility poles, streetlights, fences, and clutter placed deterministically along road networks based on target era conventions.

## Prohibited Procedural Scopes

The system **must not** generate, infer, or synthesize:
- **Terrain Relief**: Terrain must be derived entirely from DEM data. No synthetic mountains or procedural hills (e.g., placeholder or simulated heightmaps for Cerro Cuchumá) are permitted.
- **Road Networks**: No road synthesis, network interpolation, or alignment correction without direct OSM or GIS sources.
- **Buildings and Footprints**: No procedural city generation, synthetic block planning, or fictitious building footprint generation. Volume derivation must be anchored entirely to verified raw footprints.
- **Landmarks**: Landmarks must not be synthesized, simplified, or placed procedurally.

## Provenance Enforcement

All generated/packaged meshes or features must trace directly back to a raw source listed in `/data/metadata/source-inventory.json`. Any pipeline step producing spatial components must output a companion `.provenance.json` sidecar detailing this lineage, which is checked at both validation and packaging boundaries.
