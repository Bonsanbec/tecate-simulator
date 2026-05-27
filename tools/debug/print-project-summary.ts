import { resolveWorkspacePath } from "../lib/cli.js";
import { pathExists, readJsonFile } from "../lib/fs.js";
import type { ProjectArea, TileManifest } from "../lib/tile.js";

const projectArea = await readJsonFile<ProjectArea>(resolveWorkspacePath("data/metadata/project-area.json"));
const tileManifestPath = resolveWorkspacePath("generated/tiles/tile-manifest.json");
const tileManifest = await pathExists(tileManifestPath)
  ? await readJsonFile<TileManifest>(tileManifestPath)
  : undefined;

console.log(JSON.stringify({
  projectId: projectArea.projectId,
  origin: projectArea.coordinateOriginWgs84,
  targetCorridors: projectArea.corridors.map((corridor) => corridor.displayName),
  regionalLandmarks: ["landmark_montana_cuchuma"],
  tileManifest: tileManifest
    ? { zoom: tileManifest.zoom, tileCount: tileManifest.tiles.length }
    : "not-generated"
}, null, 2));

