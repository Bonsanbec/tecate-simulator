# Runtime vs Toolchain

## Principle

The runtime presents prepared content. The toolchain creates prepared content.

This boundary exists to keep the executable small, predictable, and portable across macOS and Windows. It also keeps expensive and ambiguous work in versioned, inspectable, repeatable offline steps.

## Runtime Responsibilities

The Godot runtime is responsible for:

- rendering;
- tile streaming;
- player navigation;
- camera behavior;
- basic interaction hooks;
- audio playback;
- lighting and fog;
- loading packaged assets;
- reporting debug state;
- preserving runtime IDs for buildings, landmarks, and tiles.

## Runtime Non-Responsibilities

The Godot runtime must not:

- download data;
- scrape web pages;
- ingest raw OSM;
- process DEM rasters;
- parse large GeoJSON inputs;
- generate authoritative roads;
- rebuild terrain;
- perform expensive mesh processing;
- infer landmark identity;
- rewrite source metadata.

## Toolchain Responsibilities

The TypeScript toolchain is responsible for:

- scraping and reference capture where permitted;
- GIS ingestion;
- OSM extraction;
- DEM processing coordination;
- coordinate conversion;
- road normalization;
- terrain preparation;
- building footprint normalization;
- volume derivation;
- facade extrapolation metadata;
- tile chunk generation;
- package creation;
- checksum generation;
- metadata validation;
- source lineage tracking.

## Baking Philosophy

Anything expensive, source-dependent, or ambiguous should be baked before runtime. Baking steps must output deterministic files whenever inputs are unchanged.

If data is incomplete or missing, the toolchain must perform **controlled inference** (e.g. height interpolation, building extrusions, road continuation) and mark the geometry as `inferred` rather than failing or blocking the build. This ensures progressive degradation and a constantly renderable/navigable world.

Valid baked outputs include:

- normalized GeoJSON;
- local-coordinate feature sets;
- terrain chunks;
- building volume descriptors;
- navigation meshes or inputs;
- tile manifests with inline data quality metrics;
- runtime package manifests containing flexible provenance metadata;
- debug overlays;
- source lineage reports.

## Final Package Contract

The final executable should load from generated packages, not from development source data.

A package must include enough metadata for:

- runtime compatibility checks;
- debugging missing tiles;
- tracing source lineage with confidence scores;
- identifying inferred vs. real geometry layers;
- validating coordinate origin;
- detecting outdated package versions.

## Interior Readiness

Future interiors remain optional. The runtime may load an exterior building without an interior, but the data model must allow an interior to be attached later.

The boundary is:

- exterior identity and entrance anchors are part of the exterior world package;
- room layout, interior lighting, interior audio, and interior navigation are part of optional interior packages;
- transition triggers connect exterior and interior packages.

This prevents early exterior geometry from blocking later enterable buildings.

