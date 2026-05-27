# Naming Conventions

## Purpose

Consistent naming reduces ambiguity for humans, tools, and LLM collaborators. When a term is defined here, use it everywhere.

## Language

- File and folder names use English technical names.
- Code identifiers use English.
- Documentation may use local Spanish names for places and streets.
- Street names must preserve their proper names.

## Required Street Terminology

Use `boulevard` or `blvd`.

Do not use alternate Spanish spellings for this road type. The canonical project term is `boulevard`.

Canonical street names:

- `boulevard Juarez`
- `avenida Miguel Hidalgo`
- `avenida Revolucion`
- `avenida Nuevo Leon`

Accented display names may be used in user-facing prose when needed, but file names and IDs remain ASCII.

## Folder Naming

- lowercase;
- plural domain names when storing collections;
- hyphenated markdown names;
- no spaces;
- no date suffix unless the file is a dated source artifact;
- no vague folders such as `misc`, `stuff`, `old`, or `temp`.

## Code Naming

C#:

- `PascalCase` for types, methods, properties, and Godot node classes;
- `camelCase` for private locals;
- `_camelCase` for private fields;
- explicit domain names such as `TileStreamingSystem`, not broad names such as `Manager`.

TypeScript:

- `camelCase` for functions and variables;
- `PascalCase` for types and interfaces;
- one exported responsibility per script entry point;
- no hidden global state.

## Data IDs

Use stable, lowercase IDs:

```text
building_tecate_core_z16_x11818_y27892_00042
landmark_montana_cuchuma
road_boulevard_juarez
tile_tecate_core_z16_x11818_y27892
```

IDs must not encode temporary generation assumptions such as `new`, `test`, `final`, `v2`, or `gemini`.

## Prohibited Drift

Avoid synonyms that create parallel concepts. Use the canonical term:

| Canonical term | Do not introduce |
| --- | --- |
| tile | chunk, cell, sector when referring to streamed runtime units |
| package | bundle, pack, archive when referring to runtime-ready generated data |
| landmark | hero building, key asset, special object |
| corridor | route, strip, axis when referring to first-iteration streets |
| gap-filling | city generation, auto city, procedural replacement |
| exterior | shell when discussing building representation |
| interior | inside scene, indoor level |

## Version Naming

Use semantic versions for tools and package schemas. Use source dates only when identifying external data snapshots.

Examples:

```text
tile-package.schema.json
tecate-osm-2026-05-26.geojson
dem-usgs-2024-09-source-note.md
```

