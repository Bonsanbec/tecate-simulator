# Current World State

## Project Status

The project is degraded to a clean base completely free of geographic heuristics, synthetic terrain elevation, or generative spatial assumptions. It exists as a professional geospatial pipeline scaffold. No synthetic, procedural, or approximate geometry exists in the pipeline or runtime.

All structural geometry (terrain relief, road networks, building footprints) is strictly required to derive directly from real GIS/DEM/OSM data. Procedural generation is permitted strictly and exclusively for vegetation, textures, and non-structural microdetail.

## Existing Systems

Documentation:
- project philosophy (updated to data-first geospatial reconstruction principles);
- architecture boundaries (runtime vs toolchain offline boundaries);
- world streaming design (WGS84 boundaries and tile-based streaming lifecycle);
- naming conventions (boulevard/avenida normalization);
- AI collaboration rules (standardized LLM guidelines);
- spatial identity notes (visual focus on the real Tecate landscape);
- data ingestion pipeline (updated to enforce `.provenance.json` checks for all spatial meshes);
- player experience definition;
- corridor reference notes;
- procedural generation boundaries (establishing absolute boundaries restricting procedurality);
- first iteration roadmap.

Tooling scaffold:
- TypeScript project configuration;
- repository structure validation (structure:validate checks);
- metadata validation (metadata:validate checks);
- tile structure validation (tiles:validate updated to strictly verify sidecar `.provenance.json` matching raw source inventory);
- GeoJSON importer (generating traceable source metadata);
- coordinate converter;
- tile package generator (tiles:package updated to block packaging on missing or invalid `.provenance.json` geometry data);
- data integrity checker.

Runtime scaffold:
- Godot 4.x C# project structure;
- main scene entry point;
- streaming system skeleton;
- world coordinate support;
- package manifest models.

## Pending Systems (Data-First Ingestion Phase)

- real OSM extraction for the priority corridors (required to generate any road/building meshes);
- real DEM acquisition and processing (required to generate any terrain relief meshes);
- terrain mesh generation (must derive 100% from acquired DEM);
- road mesh generation (must derive 100% from acquired OSM);
- building footprint normalization;
- building massing generation;
- landmark curation;
- Cerro Cuchumá regional terrain package (strictly derived from acquired DEM);
- navigation generation;
- material library;
- audio zone strategy;
- lighting pass.

## Current Scope

The active scope remains focused on:
- boulevard Juarez;
- avenida Miguel Hidalgo;
- avenida Revolucion;
- avenida Nuevo Leon;
- regional terrain relationship to Cerro Cuchumá (must be reconstructed strictly from DEM).

## Active Controls & Provenance Enforcement

- **Flexible & Non-Blocking Ingestion**: Validation processes raise detailed warnings rather than failing the build or blocking tile packaging when companion `.provenance.json` metadata is missing or incomplete.
- **Inferred Data Fallback**: Missing spatial/geometry data defaults to controlled inference (interpolated/extruded/heuristic) with confidence scored at `0.0`, ensuring a fully navigable, robustly renderable world.
- **Full Metadata Transparency**: Outlining quality, coverage, and uncertainty per tile via `dataQuality` metrics embedded in both `tile-manifest.json` and generated packaged outputs.
- **Source Inventory Verification**: Validation checks raise warnings if custom source IDs are not listed in `data/metadata/source-inventory.json`.
- **Naming Terminology Enforcement**: Structure validation ensures only correct, normalized boulevard and avenida nomenclature is used.
