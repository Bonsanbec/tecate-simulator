# Current World State

## Project Status

The first walkable MVP milestone has been reached. The project is now a functional, playable first-person spatial memory simulator covering the Tecate urban core and priority corridors over a 25-tile grid. The simulator features dynamic tile streaming of real-derived 3D meshes (terrain, roads, and buildings), realistic physics collisions, premium daylight illumination, atmospheric fog, and a mathematically and geospatially correct silhouette of Montaña Cuchumá.

## Existing Systems

Documentation:

- project philosophy;
- architecture boundaries;
- world streaming design;
- procedural generation limits;
- naming conventions;
- AI collaboration rules;
- spatial identity notes;
- data ingestion pipeline;
- player experience definition;
- corridor reference notes;
- first iteration roadmap.

Tooling:

- TypeScript project configuration and full type-safety;
- repository structure, metadata, and tile manifest validation;
- Overpass API OpenStreetMap data fetcher (`fetch-osm-tecate.ts`);
- High-fidelity Digital Elevation Model generator (`generate-terrain-dem.ts`);
- GeoJSON feature normalized importer (`import-geojson.ts`);
- Offline 3D OBJ mesh tile generator (`generate-tile-assets.ts`) for terrain grids, road strips, and extruded building massing;
- Tile package manifest builder (`package-tiles.ts`) and data integrity checker.

Runtime:

- Godot 4.x C# project structure and compilation setup;
- Dynamic tile streaming system (`TileStreamingSystem.cs`) loading terrain, roads, and buildings OBJ meshes on-the-fly;
- Automated runtime physics collision generation using concave trimesh shapes;
- Self-contained first-person player controller (`PlayerRig.cs`) with mouse-look and keyboard walking physics;
- Ambient occlusion (SSAO), tonemapped daylight lighting, procedural sky, and exponential distance fog to frame the Cuchumá horizon.

## Pending Systems

- manual curation and high-fidelity modeling of historical landmarks;
- navigation mesh generation for pedestrian pathfinding;
- specialized target-era materials library;
- audio zone and ambient soundscapes strategy;
- interior package contracts and enterable building transitions.

## Current Scope

The active scope covers:

- boulevard Juarez;
- avenida Miguel Hidalgo;
- avenida Revolucion;
- avenida Nuevo Leon;
- Montaña Cuchumá silhouette alignment and horizon placement.

## Risks

- OSM data may include post-2010 changes which will require manual era-curation.
- High densities of building meshes can impact frame rate on lower-end devices if not properly instanced.
- Collision shapes on dense terrain meshes can cause micro-stuttering during active tile loads (may require asynchronous loading in the future).

## Next Priorities

1. **Materials Detailing**: Introduce specialized textures for pavement, sidewalks, and building walls.
2. **Landmark Curation**: Identify and replace procedural massing with detailed, period-correct historical models.
3. **Stand-alone Export**: Set up and test Godot export templates for seamless macOS and Windows executable generation.
4. **Audio Zones**: Implement localized audio zones for the corridor.
