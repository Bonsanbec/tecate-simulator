import { promises as fs } from "node:fs";
import { resolveWorkspacePath } from "../lib/cli.js";
import { readJsonFile } from "../lib/fs.js";
import type { ProjectArea } from "../lib/tile.js";

async function main() {
  const projectAreaPath = resolveWorkspacePath("data/metadata/project-area.json");
  const projectArea = await readJsonFile<ProjectArea>(projectAreaPath);
  const bounds = projectArea.boundsWgs84;
  const origin = projectArea.coordinateOriginWgs84;

  const valleyCenterLat = 32.5668;
  const resolution = 257;
  const grid: number[][] = [];

  // Calculate unadjusted height at origin to apply an exact offset
  const tOriginLon = (origin.longitude - bounds.west) / (bounds.east - bounds.west);
  const originLatDist = origin.latitude - valleyCenterLat;
  let originBase = 525.0 + tOriginLon * 30.0; // East-west sloped valley floor

  let originHill = 0.0;
  if (originLatDist > 0) {
    originHill = Math.pow(originLatDist / (bounds.north - valleyCenterLat), 2) * 25.0;
  } else {
    originHill = Math.pow(originLatDist / (valleyCenterLat - bounds.south), 2) * 35.0;
  }
  originBase += originHill;

  const originDetail = Math.sin(origin.longitude * 2000) * Math.cos(origin.latitude * 2000) * 4.0 + Math.sin(origin.longitude * 600) * 6.0;
  const rawOriginElevation = originBase + originDetail;
  const offset = origin.elevationMeters - rawOriginElevation; // Guarantees origin is exactly 540.0m

  // Generate the sloped valley basin
  for (let i = 0; i < resolution; i += 1) {
    const row: number[] = [];
    const lat = bounds.south + (i / (resolution - 1)) * (bounds.north - bounds.south);
    const latDist = lat - valleyCenterLat;
    const latDistFromCenter = Math.abs(latDist);

    for (let j = 0; j < resolution; j += 1) {
      const lon = bounds.west + (j / (resolution - 1)) * (bounds.east - bounds.west);
      const tLon = (lon - bounds.west) / (bounds.east - bounds.west);

      // 1. East-West Valley slope baseline (525m West to 555m East)
      let base = 525.0 + tLon * 30.0;

      // 2. North-South hills framing the valley basin
      // Introduce a completely flat central basin floor (1.6 km wide) where the city lies
      let hill = 0.0;
      const flatMargin = 0.015; // flat floor margin
      if (latDistFromCenter > flatMargin) {
        const excess = latDistFromCenter - flatMargin;
        if (latDist > 0) {
          hill = Math.pow(excess / (bounds.north - valleyCenterLat - flatMargin), 2) * 50.0; // rising north
        } else {
          hill = Math.pow(excess / (valleyCenterLat - bounds.south - flatMargin), 2) * 65.0; // rising south
        }
      }
      base += hill;

      // 3. Smooth dampening of procedural sin/cos noise in the city basin
      // Noise is mathematically 0 in the central basin and fades in smoothly towards the hills
      const dampening = Math.min(1.0, Math.pow(latDistFromCenter / 0.025, 2));
      const detail = (Math.sin(lon * 2000) * Math.cos(lat * 2000) * 4.0 + Math.sin(lon * 600) * 6.0) * dampening;

      // Combine and offset
      const elevation = base + detail + offset;
      row.push(elevation);
    }
    grid.push(row);
  }

  const outputPath = resolveWorkspacePath("data/terrain/tecate-terrain-dem.json");
  await fs.writeFile(
    outputPath,
    JSON.stringify(
      {
        schemaVersion: "0.1.0",
        projectId: projectArea.projectId,
        generatedAt: new Date().toISOString(),
        boundsWgs84: bounds,
        resolution,
        grid
      },
      null,
      2
    ),
    "utf8"
  );

  console.log(`Successfully generated mathematical DEM terrain heightmap at ${outputPath}`);
}

main().catch((err) => {
  console.error("DEM generation failed:", err);
  process.exit(1);
});
