import path from "node:path";
import { resolveWorkspacePath } from "../lib/cli.js";
import { pathExists, readJsonFile } from "../lib/fs.js";
import { addError, addWarning, failOnErrors, printIssues, type ValidationIssue } from "../lib/validation.js";
import type { TileManifest } from "../lib/tile.js";

interface SourceInventory {
  sources: Array<{ id: string }>;
}

interface ProvenanceData {
  source?: "dem" | "osm" | "imagery" | "inferred";
  confidence?: number;
  method?: "direct" | "extruded" | "interpolated" | "heuristic";
  sourceId?: string;
}

const issues: ValidationIssue[] = [];
const manifestPath = resolveWorkspacePath("generated/tiles/tile-manifest.json");
const sourceInventoryPath = resolveWorkspacePath("data/metadata/source-inventory.json");

if (!await pathExists(manifestPath)) {
  addWarning(issues, "No tile manifest exists yet. Run npm run tiles:generate before packaging.", "generated/tiles/tile-manifest.json");
  printIssues("Tile structure validation", issues);
  failOnErrors(issues);
} else {
  const manifest = await readJsonFile<TileManifest>(manifestPath);
  const tileIdPattern = /^tecate_core_z\d+_x\d+_y\d+$/;
  const seenTileIds = new Set<string>();

  let validSourceIds = new Set<string>();
  if (await pathExists(sourceInventoryPath)) {
    try {
      const inventory = await readJsonFile<SourceInventory>(sourceInventoryPath);
      validSourceIds = new Set(inventory.sources.map(src => src.id));
    } catch (err) {
      addError(issues, `Failed to read source inventory: ${(err as Error).message}`, "data/metadata/source-inventory.json");
    }
  } else {
    addError(issues, "Missing data/metadata/source-inventory.json", "data/metadata/source-inventory.json");
  }

  if (!Array.isArray(manifest.tiles) || manifest.tiles.length === 0) {
    addError(issues, "Tile manifest must contain at least one tile", "generated/tiles/tile-manifest.json");
  }

  for (const tile of manifest.tiles) {
    if (!tileIdPattern.test(tile.id)) {
      addError(issues, `Invalid tile id ${tile.id}`, "generated/tiles/tile-manifest.json");
    }

    if (seenTileIds.has(tile.id)) {
      addError(issues, `Duplicate tile id ${tile.id}`, "generated/tiles/tile-manifest.json");
    }
    seenTileIds.add(tile.id);

    if (tile.z !== manifest.zoom) {
      addError(issues, `Tile ${tile.id} zoom does not match manifest`, "generated/tiles/tile-manifest.json");
    }

    if (tile.boundsWgs84.west >= tile.boundsWgs84.east || tile.boundsWgs84.south >= tile.boundsWgs84.north) {
      addError(issues, `Tile ${tile.id} has invalid bounds`, "generated/tiles/tile-manifest.json");
    }

    for (const [kind, relativePath] of Object.entries(tile.files)) {
      const absolutePath = resolveWorkspacePath(relativePath);
      if (!await pathExists(absolutePath)) {
        addError(issues, `Tile ${tile.id} references missing file ${relativePath}`, "generated/tiles/tile-manifest.json");
        continue;
      }

      // Validate provenance for geometry/spatial files
      const isGeometry = ["terrain", "roads", "buildings"].includes(kind) || 
                         [".obj", ".gltf", ".glb", ".mesh", ".json"].includes(path.extname(absolutePath).toLowerCase());

      if (isGeometry) {
        const provenancePath = `${absolutePath}.provenance.json`;
        if (!await pathExists(provenancePath)) {
          addWarning(issues, `Geometry file "${relativePath}" for tile ${tile.id} is missing a companion .provenance.json file. It will be treated as inferred in packages.`, "generated/tiles/tile-manifest.json");
        } else {
          try {
            const provenance = await readJsonFile<ProvenanceData>(provenancePath);
            if (!provenance) {
              addWarning(issues, `Provenance file for "${relativePath}" is empty or invalid.`, "generated/tiles/tile-manifest.json");
            } else {
              if (provenance.source !== undefined) {
                const validSources = ["dem", "osm", "imagery", "inferred"];
                if (!validSources.includes(provenance.source)) {
                  addWarning(issues, `Provenance source "${provenance.source}" in "${path.basename(provenancePath)}" is invalid. Must be one of: ${validSources.join(", ")}`, "generated/tiles/tile-manifest.json");
                }
                if (typeof provenance.confidence !== "number" || provenance.confidence < 0 || provenance.confidence > 1) {
                  addWarning(issues, `Provenance confidence in "${path.basename(provenancePath)}" must be a number between 0.0 and 1.0`, "generated/tiles/tile-manifest.json");
                }
                const validMethods = ["direct", "extruded", "interpolated", "heuristic"];
                if (provenance.method === undefined || !validMethods.includes(provenance.method)) {
                  addWarning(issues, `Provenance method in "${path.basename(provenancePath)}" is invalid or missing. Must be one of: ${validMethods.join(", ")}`, "generated/tiles/tile-manifest.json");
                }
              }

              if (provenance.sourceId !== undefined && !validSourceIds.has(provenance.sourceId)) {
                addWarning(issues, `Provenance sourceId "${provenance.sourceId}" in "${path.basename(provenancePath)}" is not listed in data/metadata/source-inventory.json`, "generated/tiles/tile-manifest.json");
              }

              if (provenance.source === undefined && provenance.sourceId === undefined) {
                addWarning(issues, `Provenance file for "${relativePath}" lacks both "source" and "sourceId" fields`, "generated/tiles/tile-manifest.json");
              }
            }
          } catch (err) {
            addWarning(issues, `Failed to validate provenance for "${relativePath}": ${(err as Error).message}`, "generated/tiles/tile-manifest.json");
          }
        }
      }
    }
  }

  printIssues("Tile structure validation", issues);
  failOnErrors(issues);
}


