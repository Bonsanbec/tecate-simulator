import path from "node:path";
import { resolveWorkspacePath } from "../lib/cli.js";
import { pathExists, readJsonFile, sha256File, writeJsonFile } from "../lib/fs.js";
import type { TileManifest } from "../lib/tile.js";

const manifestPath = resolveWorkspacePath("generated/tiles/tile-manifest.json");
const outputPath = resolveWorkspacePath("generated/packages/tecate-core-tile-package.json");
const workspaceRootPath = resolveWorkspacePath(".");

if (!await pathExists(manifestPath)) {
  throw new Error("Missing generated/tiles/tile-manifest.json. Run npm run tiles:generate first.");
}

const manifest = await readJsonFile<TileManifest>(manifestPath);

const packagedTiles = [];

for (const tile of manifest.tiles) {
  const files = [];

  for (const [kind, relativePath] of Object.entries(tile.files)) {
    const absolutePath = resolveWorkspacePath(relativePath);
    if (!await pathExists(absolutePath)) {
      continue;
    }

    files.push({
      kind,
      path: path.relative(workspaceRootPath, absolutePath),
      sha256: await sha256File(absolutePath)
    });
  }

  packagedTiles.push({
    id: tile.id,
    state: files.length > 0 ? "packaged" : tile.state,
    files
  });
}

await writeJsonFile(outputPath, {
  schemaVersion: "0.1.0",
  packageId: "tecate_core_tiles",
  projectId: manifest.projectId,
  createdBy: "tools/packaging/package-tiles.ts",
  createdAt: new Date().toISOString(),
  coordinateOriginWgs84: manifest.coordinateOriginWgs84,
  tiles: packagedTiles
});

console.log(`Wrote package manifest to ${outputPath}`);

