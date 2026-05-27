# Montaña Cuchumá

## Role

Montaña Cuchumá is a protected regional terrain landmark. It is part of the spatial identity of Tecate and must be handled as geospatial structure, not as decoration.

## Representation Rule

The primary representation must be distant terrain geometry or a regional mesh aligned to the project coordinate system.

A skybox may contribute atmosphere, but it must not be the primary representation of the mountain silhouette.

## Required Preservation

Preserve:

- relative position in the horizon;
- approximate apparent scale from the four priority corridors;
- recognizable silhouette;
- altitude relationship between urban Tecate and the mountain;
- visibility continuity through streets and intersections where source data supports it;
- participation in lighting, fog, and time-of-day systems.

Avoid:

- cinematic exaggeration;
- compressed horizon distance;
- treating the mountain as a flat painted backdrop;
- sacrificing silhouette recognition for terrain microdetail.

## Validation Viewpoints

The first terrain validation pass should include viewpoints from:

- boulevard Juarez;
- avenida Revolucion;
- avenida Miguel Hidalgo;
- avenida Nuevo Leon.

Each viewpoint should record:

- local runtime position;
- WGS84 estimate;
- looking direction;
- expected horizon placement;
- screenshot or debug capture path when available;
- review status.

## Data Requirements

The terrain pipeline must document:

- DEM source;
- source date;
- resolution;
- vertical datum if known;
- processing extent;
- downsampling method;
- generated mesh bounds;
- silhouette review status.

