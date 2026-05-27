# Interior Readiness

## Purpose

The first iteration does not implement full interiors, but every building system must preserve the option to add interiors later.

## Building Representation

A building is a persistent entity with separate layers:

- identity;
- exterior geometry;
- optional interior package;
- semantic metadata;
- entrance anchors;
- streaming state;
- future interaction hooks.

Exterior geometry is not the complete definition of a building.

## Stable Identity

Building IDs must remain stable across regeneration when source geometry remains equivalent. IDs must be recorded in metadata before runtime packaging.

Stable identity supports:

- future interior reconstruction;
- semantic annotation;
- landmark review;
- narrative extensions;
- source lineage tracking;
- targeted manual corrections.

## Interior Package Concept

An interior package may contain:

- interior scene reference;
- room metadata;
- interior navigation data;
- localized audio zones;
- interior lighting data;
- transition anchors;
- loading policy.

Interior packages are optional and must be streamable independently from exterior tiles.

## Transition Zones

Transition zones connect exterior and interior spaces. They should be represented by metadata, not hardcoded scene assumptions.

A transition zone must know:

- building ID;
- exterior anchor;
- optional interior package ID;
- required interaction type;
- player spawn transform;
- loading priority.

## Prohibited Assumptions

Do not assume:

- every building is non-enterable;
- exterior mesh is immutable;
- facade generation owns interior layout;
- interior and exterior lighting are the same system;
- building interaction requires final interiors to exist.

