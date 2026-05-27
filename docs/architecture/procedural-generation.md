# Procedural Generation

## Purpose

Procedural generation exists to complete and repair the world after real-derived data has established the primary spatial structure.

It is not a world authoring authority. It is a controlled offline tool.

## Allowed Use

Procedural generation may be used for:

- missing secondary building height estimates;
- simple massing from known footprints;
- non-landmark facade rhythm extrapolation;
- roof equipment and minor rooftop forms;
- curb and sidewalk completion where road geometry is known;
- low-priority background building fill;
- vegetation scatter based on documented corridor rules;
- utility poles, signs, and street furniture as secondary density;
- debug geometry for validation.

## Prohibited Use

Procedural generation must not:

- invent new landmarks;
- modify curated landmarks;
- move or reshape primary roads;
- override terrain elevation;
- replace real-derived building footprints when available;
- merge identifiable buildings without metadata;
- create false historic claims;
- alter the silhouette, position, or scale of Montaña Cuchumá;
- generate final photogrammetry;
- make runtime-only irreversible decisions.

## Building Completion

Building completion may convert a footprint and metadata into a simple exterior volume. The output must preserve:

- stable building ID;
- source footprint reference;
- confidence level;
- estimated height source;
- corridor classification;
- exterior package reference;
- optional future interior package reference.

Unknown buildings are not anonymous. They receive stable IDs based on source geometry and tile identity.

## Facade Extrapolation

Facade extrapolation may infer repeated doors, windows, awnings, shutters, signs, and material zones for non-landmark buildings.

Facade extrapolation must record:

- source confidence;
- rule set version;
- corridor context;
- era assumption;
- whether manual review is required.

Facade output is secondary and may be replaced by curated assets later.

## Secondary Geometry

Secondary geometry includes:

- sidewalks;
- curbs;
- low walls;
- fences;
- signage supports;
- poles;
- benches;
- planters;
- small roof structures;
- generic shopfront density.

Secondary geometry must respect roads, parcels, building entrances, and visibility corridors.

## Scatter Systems

Scatter systems may place vegetation and minor props using deterministic seeds. Scatter must be restricted by metadata zones and must not block pedestrian navigation.

Initial scatter categories:

- dry regional vegetation;
- urban trees;
- small commercial props;
- utility infrastructure;
- sidewalk detail.

## Landmark Preservation

Landmarks are curated assets or curated geometry packages. Procedural tools may generate helper data around landmarks, but they may not alter landmark identity or shape without a manual landmark update.

Montaña Cuchumá is treated as regional terrain with landmark status. Its silhouette is protected.
