# World Streaming

## Purpose

World streaming keeps the runtime small by loading prepared world tiles near the player and unloading distant tiles. It operates only on packaged data generated offline.

The streaming system does not ingest raw GIS, interpret OSM, build terrain from DEM, or generate final geometry at runtime.

## Ownership

Runtime owner:

- `godot/systems/TileStreamingSystem.cs`

Toolchain owners:

- `tools/packaging/package-tiles.ts`
- `tools/validation/validate-tile-structure.ts`

Data contracts:

- `schemas/tile-manifest.schema.json`
- `schemas/tile-package.schema.json`

## Coordinate System

The project uses WGS84 latitude and longitude for source metadata and a local meter coordinate space for runtime.

Runtime coordinates use:

- `+X`: east;
- `+Z`: south;
- `+Y`: up;
- units: meters;
- origin: a documented point near the first-iteration corridor center.

The origin is defined in `data/metadata/project-area.json`. All prepared packages must record the origin used during conversion.

## Tile Identity

Tile identifiers use this format:

```text
tecate_core_z{zoom}_x{x}_y{y}
```

Example:

```text
tecate_core_z16_x11818_y27892
```

Rules:

- lowercase ASCII;
- no spaces;
- no street names inside tile IDs;
- no semantic labels that can drift over time;
- stable across regeneration when bounds and zoom remain unchanged.

## Tile Contents

A tile may contain references to:

- terrain mesh;
- road mesh;
- building exterior mesh;
- landmark mesh;
- vegetation scatter package;
- navigation data;
- lighting probes or baked lighting metadata;
- audio zones;
- future interior links.

Tiles do not own raw source data. They own runtime-ready references and package metadata.

## Loading Radius

The initial streaming policy uses three rings:

```text
active ring:      player tile and immediately adjacent tiles
warm ring:        next ring kept indexed or prepared for load
cold ring:        known in manifest but not loaded
```

Default starting values:

- active radius: 1 tile;
- warm radius: 2 tiles;
- unload radius: 3 tiles.

These values are conservative for the initial corridor. They should be tuned after terrain and building density exist.

## Streaming Lifecycle

1. Runtime loads the tile package manifest.
2. Player position is converted to a tile coordinate.
3. Active, warm, and cold sets are computed.
4. Missing active tiles are loaded from prepared packages.
5. Warm tiles may prefetch metadata.
6. Tiles beyond unload radius are removed.
7. Runtime emits debug state for validation.

Each tile state must be explicit:

- `missing`: listed but no package file available;
- `cold`: known and unloaded;
- `warm`: metadata available;
- `loading`: load requested;
- `active`: visible or interactive;
- `unloading`: unload requested;
- `failed`: load failed with diagnostic.

## Memory Strategy

The runtime must avoid holding raw input data. It should hold:

- the package manifest;
- small tile metadata;
- loaded Godot scenes or resources for active tiles;
- cached metadata for warm tiles;
- debug counters.

The runtime should not keep:

- OSM source extracts;
- DEM rasters;
- satellite images;
- raw GeoJSON FeatureCollections;
- intermediate converter outputs not required for rendering.

## Packaging

Tile packages are generated under `generated/packages/`. A package manifest records:

- package version;
- project origin;
- tile IDs;
- file references;
- checksums;
- source data lineage;
- generation timestamp;
- tool versions;
- compatibility target.

The Godot runtime reads only package manifests and runtime-ready file references.

## Future Interior Streaming

Buildings may reference optional interior packages. Interior loading is independent from exterior tile loading.

Exterior tile streaming must preserve:

- stable building IDs;
- entrance anchor metadata;
- transition zone references;
- optional interior package identifiers;
- a way to unload interiors without unloading the exterior tile.

No building tile format may assume that an exterior shell is the complete permanent representation of a building.

