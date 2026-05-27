# Tecate Corridors

## Purpose

This file defines the first-iteration corridor scope. It is a reference contract for data collection, generation, validation, and LLM prompts.

## Scope

The first iteration covers:

- boulevard Juarez;
- avenida Revolucion;
- avenida Miguel Hidalgo;
- avenida Nuevo Leon.

Other streets may appear only where needed to support intersections, visibility, tile continuity, or immediate context.

## Boulevard Juarez

Perceptual role:

- primary urban corridor;
- strong commercial identity;
- major continuity reference for pedestrian orientation;
- high importance for scale, signage, traffic edge, and storefront rhythm.

Data priorities:

- road alignment;
- sidewalk continuity;
- commercial frontage;
- intersections with the other priority corridors;
- sightlines toward regional terrain.

## Avenida Revolucion

Perceptual role:

- central urban reference;
- strong relationship to Tecate's civic and commercial memory;
- important for mixed-use density and corridor identity.

Data priorities:

- street width and alignment;
- building frontage;
- landmarks and recognizable businesses where documented;
- pedestrian crossing logic;
- visual connection to adjacent corridors.

## Avenida Miguel Hidalgo

Perceptual role:

- connective corridor with local identity;
- useful for reading the grid and slope changes;
- important for residential/commercial transitions.

Data priorities:

- continuity across intersections;
- terrain relationship;
- building scale variation;
- corner conditions;
- linkage to boulevard Juarez and avenida Revolucion.

## Avenida Nuevo Leon

Perceptual role:

- corridor edge and transition reference;
- important for spatial variety and neighborhood texture;
- useful for testing lower-density completion rules.

Data priorities:

- road geometry;
- adjacent building density;
- vegetation and open-edge conditions;
- visibility relationships;

## Landmark Handling

Relevant landmarks must be curated, not procedurally invented. A landmark record should contain:

- stable ID;
- name;
- corridor relationship;
- coordinates or anchor;
- source notes;
- target-era confidence;
- exterior representation status;
- future interior eligibility.

Montaña Cuchumá is a regional landmark and terrain anchor, not a decorative backdrop.

## Corridor Validation

Each corridor should be validated for:

- road continuity;
- approximate width;
- terrain slope;
- frontage density;
- landmark placement;
- pedestrian readability;
- horizon coherence;
- absence of generic procedural city patterns.
