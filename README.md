# Tecate Spatial Memory Simulator

Tecate Spatial Memory Simulator is a Godot 4.x C# project for a pedestrian urban simulation set in Tecate, Baja California, Mexico, with an approximate spatial memory target of 2000-2010.

The project does not pursue perfect archival reconstruction. It pursues a convincing spatial memory of Tecate through real-derived terrain, roads, buildings, corridor continuity, regional landmarks, and disciplined gap-filling. The first iteration is limited to boulevard Juarez, avenida Miguel Hidalgo, avenida Revolucion, and avenida Nuevo Leon.

## Vision

The player should perceive:

- continuous walkable urban space;
- the border-city commercial and residential mix of Tecate;
- irregular Mexican architectural massing;
- light local topography and long sightlines;
- authentic regional density without AAA hyperrealism;
- a coherent east/southeast horizon dominated by the real relative presence of Montaña Cuchumá.

The world must not read as:

- a generic procedural city;
- a United States suburb;
- a stylized sandbox;
- a technology demo;
- a fully invented reinterpretation of Tecate.

## Perceptual Priorities

1. Urban scale.
2. Terrain relief.
3. Road continuity.
4. Real landmarks.
5. Geometry derived from real data.
6. Visual density.
7. Microdetail.

Procedural systems are subordinate to real-derived structure. They may fill gaps, complete secondary geometry, extrapolate missing facade detail, and extend low-priority areas. They must not invent landmarks, alter important buildings, redefine roads, replace critical geometry, or reinterpret terrain.

## Technical Stack

- Engine runtime: Godot 4.x with C#.
- Game runtime language: C#.
- GDScript: allowed only for narrow Godot integration cases where C# is not practical.
- Tooling language: TypeScript running on Node.js.
- Local SDK pin: .NET 8 through `global.json`.
- Runtime targets: macOS and Windows.
- Source control: Git.
- Data sources: OpenStreetMap, DEM terrain data, GIS extracts, imagery references, and curated street-level references.
- Future compatibility: possible Cesium or additional GIS tooling integration.

## Runtime And Toolchain Boundary

The Godot runtime is responsible only for rendering, streaming, navigation, interaction, audio, lighting, and loading prepared packages.

The development toolchain is responsible for scraping, GIS ingestion, coordinate conversion, geometry preparation, procedural derivation, baking, packaging, validation, and metadata generation.

Heavy processing must happen offline. The final executable should load prepared data and packaged assets. It must not download data, scrape web sources, reconstruct raw GIS, or perform expensive parsing at runtime.

## Repository Layout

```text
docs/        Permanent project knowledge, design rules, pipeline contracts, and state.
tools/       TypeScript importers, converters, generators, packaging, validation, and debug utilities.
data/        Source and intermediate data organized by domain.
assets/      Authored runtime assets organized by type. Binary assets are intentionally absent at initialization.
generated/   Offline generated outputs, tile data, packages, and debug artifacts.
godot/       Godot 4.x C# runtime project.
scripts/     Developer entry points that coordinate tooling without hiding core logic.
schemas/     JSON schemas and data contracts used by tooling and runtime packages.
```

## Initial Workflow

1. Place raw GIS, DEM, imagery notes, or reference manifests under `data/`.
2. Normalize external data with TypeScript importers in `tools/importers/`.
3. Convert coordinates and bounds with `tools/converters/`.
4. Generate coarse chunks, derived geometry, and navigation inputs with `tools/generators/`.
5. Validate metadata and generated structure with `tools/validation/`.
6. Package prepared tile data with `tools/packaging/`.
7. Load only prepared packages from the Godot runtime.

## First Iteration Scope

The first iteration ends when the project can support:

- a navigable urban corridor across the four priority streets;
- approximate real terrain relief;
- functional tile streaming;
- buildings derived from real data;
- basic manually curated landmarks;
- fluid pedestrian navigation;
- basic lighting and atmospheric consistency;
- recognizable Tecate spatial identity.

It does not include multiplayer, networking, complex AI, advanced physics, full interiors, final 3D art, final photogrammetry, or a playable public demo.

## Building Identity And Future Interiors

Buildings must keep stable identifiers. Exterior representation, optional interior representation, metadata layers, streaming state, and future interaction hooks are separate concerns.

The first iteration does not include full interiors, but the architecture must preserve future support for:

- linked interior scenes;
- interior lighting packages;
- room metadata;
- localized audio zones;
- entry and exit transition zones;
- semantic building labels;
- future LLM-assisted interior annotation.

No system may assume that all buildings are permanently non-enterable.

## Core Documentation

- [Project Philosophy](docs/vision/project-philosophy.md)
- [Runtime vs Toolchain](docs/architecture/runtime-vs-toolchain.md)
- [World Streaming](docs/architecture/world-streaming.md)
- [Procedural Generation](docs/architecture/procedural-generation.md)
- [Naming Conventions](docs/conventions/naming.md)
- [AI Collaboration](docs/conventions/ai-collaboration.md)
- [Spatial Identity](docs/world/spatial-identity.md)
- [Data Ingestion](docs/pipelines/data-ingestion.md)
- [Player Experience](docs/gameplay/player-experience.md)
- [Tecate Corridors](docs/references/tecate-corridors.md)
- [Montaña Cuchumá](docs/references/montana-cuchuma.md)
- [Current World State](docs/state/current-world-state.md)
- [First Iteration Plan](docs/roadmap/first-iteration-plan.md)
- [Development Environment](docs/setup/development-environment.md)
