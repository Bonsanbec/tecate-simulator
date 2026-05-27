# Player Experience

## Goal

The player experience is a slow pedestrian traversal through a believable Tecate corridor. The experience prioritizes spatial continuity, scale, terrain, and urban identity.

The first iteration is not a mission system and not a gameplay prototype with complex mechanics.

## Movement

Baseline movement targets:

- walking speed: 1.4 m/s;
- brisk walking speed: 2.2 m/s;
- sprinting: not required for first iteration;
- jump: not required unless needed for controller testing;
- crouch: not required;
- vehicle movement: out of scope.

Movement should be stable, grounded, and human-scaled.

## Camera

Camera goals:

- human eye height around 1.65 m;
- gentle head movement only if it improves perception;
- no exaggerated field of view;
- no cinematic shake;
- horizon readable during movement;
- mountain sightlines preserved.

Suggested starting values:

- vertical eye height: 1.65 m;
- horizontal FOV: 75-85 degrees depending on Godot camera settings;
- mouse/controller sensitivity tuned for slow inspection.

## Navigation

Navigation should support:

- walking along sidewalks and roadside edges;
- crossing intersections;
- reading corridor direction visually;
- reaching landmarks and visible anchors;
- avoiding abrupt invisible barriers in the first corridor.

Temporary collision boundaries are allowed only when documented as debug constraints.

## Interaction

The first iteration requires minimal interaction:

- inspectable debug labels in development builds;
- future-ready building interaction hooks;
- optional entrance trigger metadata for future interiors;
- no inventory;
- no dialogue system;
- no quest system.

## Audio

Audio is initially architectural:

- ambient city bed;
- localized street activity zones in future passes;
- interior audio zones reserved for future packages;
- no complex simulation.

## Experience Success Criteria

The first traversal should make the player feel:

- road continuity;
- local slope and terrain relief;
- a commercial/residential Tecate rhythm;
- a coherent east/southeast mountain horizon;
- believable block-by-block progression;
- enough density to support memory without overwhelming navigation.

