import { getNumberArg, parseArgs, resolveWorkspacePath } from "../lib/cli.js";
import { readJsonFile, writeJsonFile } from "../lib/fs.js";
import { createTileManifest, type ProjectArea } from "../lib/tile.js";

const args = parseArgs();
const projectAreaPath = resolveWorkspacePath("data/metadata/project-area.json");
const outputPath = resolveWorkspacePath("generated/tiles/tile-manifest.json");
const debugSummaryPath = resolveWorkspacePath("generated/debug/tile-summary.json");

const projectArea = await readJsonFile<ProjectArea>(projectAreaPath);
const zoom = getNumberArg(args, "zoom", projectArea.initialTileZoom);
const manifest = createTileManifest(projectArea, zoom);

await writeJsonFile(outputPath, manifest);
await writeJsonFile(debugSummaryPath, {
  schemaVersion: "0.1.0",
  generatedAt: manifest.generatedAt,
  tileCount: manifest.tiles.length,
  corridorTileCounts: Object.fromEntries(
    projectArea.corridors.map((corridor) => [
      corridor.id,
      manifest.tiles.filter((tile) => tile.corridorIds.includes(corridor.id)).length
    ])
  )
});

console.log(`Generated ${manifest.tiles.length} planned tiles at ${outputPath}`);

