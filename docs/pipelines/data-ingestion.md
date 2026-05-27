# Data Ingestion

## Purpose

The ingestion pipeline turns external source data into normalized, documented, offline-prepared project data. It does not create runtime behavior directly.

## Source Categories

Initial source categories:

- OpenStreetMap road and building data;
- DEM terrain data;
- satellite imagery references;
- street-level references;
- manually curated landmark notes;
- corridor metadata;
- era notes for 2000-2010 interpretation.

## GIS Ingestion

GIS inputs enter under `data/raw/` or `data/gis/` depending on their processing state.

Raw inputs should be preserved with source notes. Normalized outputs must document:

- source file;
- source date;
- coordinate system;
- processing tool;
- bounds;
- confidence;
- review status.

## OSM Ingestion

OSM is used for road continuity, building footprints, and coarse urban structure. It is not automatically period-correct for 2000-2010.

OSM-derived records must keep:

- OSM element ID when available;
- tags used;
- extraction date;
- corridor relationship;
- whether the feature requires era review.

## DEM Processing

DEM terrain data defines the altitude relationship between Tecate urban terrain and Montaña Cuchumá.

DEM processing must preserve:

- source resolution;
- vertical datum if known;
- processing extent;
- downsampling method;
- terrain origin;
- elevation range;
- confidence notes.

Runtime terrain must be generated from prepared meshes or height data packages, not raw DEM rasters.

## Imagery References

Imagery references are used for visual validation and manual interpretation. They are not automatically runtime assets.

Imagery metadata should include:

- source;
- capture date or approximate date;
- license or usage note;
- corridor coverage;
- visible landmarks;
- reliability for target era.

## Street-Level References

Street-level references are used to interpret facade rhythm, signage density, materials, and pedestrian perspective.

They should be organized by corridor and approximate location. If dates are outside 2000-2010, the difference must be documented.

## Volumetric Derivation

Building footprints may be converted into simple massing when no curated model exists.

The derivation output must record:

- footprint source;
- estimated height;
- height rule;
- facade rule;
- confidence;
- manual review flag;
- stable building ID.

## Offline Packaging

After normalization and generation, packages are written under `generated/packages/`.

Package validation must check:

- tile ID format;
- required metadata;
- file references;
- checksums;
- coordinate origin;
- schema version;
- prohibited terminology drift.
