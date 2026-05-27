# AI Collaboration

## Purpose

This repository is designed for repeated assistance by Gemini and other LLMs. The project must not depend on hidden conversation state.

Every prompt should reference stable files, explicit constraints, and exact ownership boundaries.

## Prompt Rules

Effective prompts should include:

- the target file or subsystem;
- the exact corridor or tile scope;
- the source data being used;
- the expected output format;
- the prohibited changes;
- the validation command to run.

Example:

```text
Update tools/generators/generate-basic-chunks.ts so it emits tile IDs matching docs/architecture/world-streaming.md. Do not change runtime C# code. Validate with npm run tiles:validate.
```

## Context Reduction

Do not paste the entire repository into an LLM prompt. Reference these files instead:

- `README.md` for project overview;
- `docs/conventions/naming.md` for terminology;
- `docs/architecture/runtime-vs-toolchain.md` for responsibility boundaries;
- `docs/architecture/world-streaming.md` for tile behavior;
- `docs/state/current-world-state.md` for current status.

## Avoiding Drift

Before accepting generated output, check:

- Does it use `boulevard` or `blvd` consistently?
- Does it preserve the four first-iteration corridors?
- Does it keep heavy processing out of the runtime?
- Does it preserve stable building identity?
- Does it avoid invented landmarks?
- Does it avoid treating Montaña Cuchumá as only a skybox?
- Does it add a new synonym for an existing concept?

## File Ownership

LLM-generated changes should be scoped to one responsibility at a time.

Preferred task boundaries:

- one documentation file;
- one TypeScript tool;
- one schema;
- one Godot runtime system;
- one validation command.

Avoid prompts that ask for broad simultaneous changes across runtime, pipeline, art direction, and gameplay.

## Metadata Discipline

When an LLM creates or edits data, it must preserve:

- source;
- confidence;
- date;
- coordinate system;
- corridor scope;
- review status.

If the source is unknown, write `unknown` explicitly and mark the item for review. Do not invent certainty.

## Review Checklist

Every AI-assisted contribution should answer:

- What files changed?
- Which stable contract was used?
- Which validation ran?
- What assumptions are now recorded in metadata?
- What remains manual or uncertain?
