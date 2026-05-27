# First Iteration Plan

## Definition

The first iteration delivers a prepared, navigable urban corridor foundation for Tecate around the 2000-2010 spatial memory target. It does not deliver a public demo, final art pass, final interiors, or complete city reconstruction.

## Phase 1: Repository And Contracts

Deliverables:

- repository structure;
- documentation baseline;
- naming conventions;
- AI collaboration rules;
- TypeScript tooling scaffold;
- Godot C# runtime scaffold;
- metadata schemas;
- validation scripts.

Success criteria:

- required directories exist;
- required documents contain useful content;
- validation scripts are runnable after dependency install;
- runtime/toolchain boundary is documented.

## Phase 2: Source Data Acquisition

Deliverables:

- OSM extract notes;
- DEM source notes;
- imagery reference metadata;
- street-level reference inventory;
- project origin confirmation;
- corridor bounds confirmation.

Success criteria:

- every source has date, license note, bounds, and confidence;
- first-iteration corridors are traceable in metadata;
- Montaña Cuchumá terrain source is identified.

## Phase 3: Normalization

Deliverables:

- normalized road data;
- normalized building footprints;
- local-coordinate feature sets;
- terrain processing metadata;
- source lineage report.

Success criteria:

- coordinate conversion is reproducible;
- road continuity can be inspected in debug outputs;
- building IDs are stable;
- raw sources remain separate from normalized outputs.

## Phase 4: Terrain And Horizon

Deliverables:

- urban terrain prototype;
- regional terrain package for Montaña Cuchumá;
- horizon validation views;
- elevation relationship report.

Success criteria:

- Tecate urban altitude and Montaña Cuchumá relationship are plausible;
- mountain silhouette remains coherent from all four priority corridors;
- no static skybox is used as the primary mountain representation.

## Phase 5: Corridor Geometry

Deliverables:

- road meshes;
- sidewalks and curbs;
- building exterior massing;
- basic manually curated landmarks;
- collision boundaries;
- debug overlays.

Success criteria:

- player can traverse the corridor without spatial breaks;
- roads and intersections remain legible;
- procedural gap-filling does not alter primary roads or landmarks.

## Phase 6: Runtime Streaming

Deliverables:

- tile manifest;
- packaged tile data;
- active/warm/cold streaming states;
- debug telemetry;
- memory baseline.

Success criteria:

- tiles load and unload predictably;
- package validation passes;
- runtime does not read raw GIS or DEM data;
- missing tile errors are explicit.

## Phase 7: Experience Pass

Deliverables:

- pedestrian movement tuning;
- camera tuning;
- basic lighting;
- fog and atmospheric perspective;
- initial audio zones if available;
- spatial identity review.

Success criteria:

- walking feels human-scaled;
- terrain is perceptible;
- corridor identity is recognizable;
- Montaña Cuchumá remains coherent in the horizon;
- visual density supports memory without obscuring navigation.

## MVP Definition

The first MVP is a local development build with:

- one continuous navigable corridor network across the four priority streets;
- real-derived terrain;
- tile streaming;
- real-derived building massing;
- protected landmark metadata;
- Montaña Cuchumá represented as distant terrain geometry;
- basic lighting and atmosphere;
- validation commands for package integrity.

## Key Risks

- insufficient target-era references;
- inconsistent coordinate origins;
- mountain silhouette mismatch;
- overuse of procedural facade generation;
- unstable building identifiers;
- unvalidated package references;
- runtime scope creep.

## Milestones

1. Repository initialized and validated.
2. Source inventory complete.
3. Normalized corridor data complete.
4. Terrain and mountain horizon validated.
5. First packaged tile set generated.
6. Runtime streaming verified.
7. Pedestrian corridor review complete.
