# Project Philosophy

## Definition

Tecate Spatial Memory Simulator is a pedestrian urban simulation focused on the perceived spatial memory of Tecate, Baja California, Mexico, around 2000-2010.

The project reconstructs a believable walkable environment from real-derived data, curated references, and restrained offline generation. Its success is measured by perceptual authenticity, continuity, and urban identity rather than documentary completeness.

## What The Project Is

- A spatial memory reconstruction.
- A pedestrian-scale urban simulator.
- A data-first reconstruction pipeline.
- A Godot 4.x C# runtime that loads prepared packages.
- A long-term architecture for curated corridors, landmarks, terrain, and optional future interiors.
- A project designed for repeated assistance by Gemini and other LLMs without depending on conversational memory.

## What The Project Is Not

- It is not an archival historical database.
- It is not a 1:1 legal survey.
- It is not a procedural city generator.
- It is not a satellite imagery viewer.
- It is not a photogrammetry-only reconstruction.
- It is not a multiplayer or systems-simulation project.
- It is not a stylized sandbox.
- It is not a public gameplay demo at initialization.

## Target Era

The target era is approximately 2000-2010. The project may use current data as geometric scaffolding when older data is unavailable, but the visual interpretation must be corrected toward the target era through metadata, references, and manual review.

When a source reflects a date outside 2000-2010, that date must be documented in metadata. Tooling should never silently treat current data as period-correct.

## Perceptual Priority Order

1. Urban scale.
2. Terrain relief.
3. Road continuity.
4. Real landmarks.
5. Geometry derived from real data.
6. Visual density.
7. Microdetail.

This order governs conflicts. For example, a less detailed building footprint that preserves corridor scale is preferable to a high-detail invented block that damages road continuity.

## Procedural Role

Procedural generation is a repair and completion tool. It may:

- fill low-confidence gaps;
- complete secondary volumes from footprints;
- extrapolate non-landmark facades;
- scatter secondary props according to corridor rules;
- extend low-priority background density;
- generate debug geometry for validation.

Procedural generation must not:

- invent landmarks;
- move roads;
- reinterpret terrain;
- replace known building identity;
- create arbitrary district plans;
- override curated metadata;
- compress the regional horizon for cinematic effect.

## Montaña Cuchumá

Montaña Cuchumá is a critical spatial identity landmark. It must be represented as geospatially anchored regional terrain or a distant terrain mesh aligned with the world coordinate system. It must not be represented primarily as a painted static skybox.

The silhouette must preserve its approximate real relative position, horizon placement, and apparent scale from boulevard Juarez, avenida Revolucion, avenida Miguel Hidalgo, and avenida Nuevo Leon. Microdetail is secondary to silhouette recognizability and altitude relationship.

## Design Philosophy

The project favors:

- stable contracts over clever one-off logic;
- offline baking over runtime computation;
- explicit metadata over implicit interpretation;
- small runtime systems over broad generalized frameworks;
- real-derived anchors over procedural invention;
- incremental validation over late manual correction.

Each future contribution should reduce ambiguity for the next contributor.
