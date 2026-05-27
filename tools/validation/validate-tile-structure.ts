import { resolveWorkspacePath } from "../lib/cli.js";
import { pathExists, readJsonFile } from "../lib/fs.js";
import { addError, addWarning, failOnErrors, printIssues, type ValidationIssue } from "../lib/validation.js";
import type { TileManifest } from "../lib/tile.js";

const issues: ValidationIssue[] = [];
const manifestPath = resolveWorkspacePath("generated/tiles/tile-manifest.json");

if (!await pathExists(manifestPath)) {
  addWarning(issues, "No tile manifest exists yet. Run npm run tiles:generate before packaging.", "generated/tiles/tile-manifest.json");
  printIssues("Tile structure validation", issues);
  failOnErrors(issues);
} else {
  const manifest = await readJsonFile<TileManifest>(manifestPath);
  const tileIdPattern = /^tecate_core_z\d+_x\d+_y\d+$/;
  const seenTileIds = new Set<string>();

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

    for (const relativePath of Object.values(tile.files)) {
      if (!await pathExists(resolveWorkspacePath(relativePath))) {
        addError(issues, `Tile ${tile.id} references missing file ${relativePath}`, "generated/tiles/tile-manifest.json");
      }
    }
  }

  printIssues("Tile structure validation", issues);
  failOnErrors(issues);
}

