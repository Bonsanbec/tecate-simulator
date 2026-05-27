import { promises as fs } from "node:fs";
import { resolveWorkspacePath } from "../lib/cli.js";
import { readJsonFile } from "../lib/fs.js";
import type { ProjectArea } from "../lib/tile.js";

async function main() {
  const projectAreaPath = resolveWorkspacePath("data/metadata/project-area.json");
  const projectArea = await readJsonFile<ProjectArea>(projectAreaPath);
  const bounds = projectArea.boundsWgs84;
  const origin = projectArea.coordinateOriginWgs84;

  const resolution = 257;
  const grid: number[][] = [];

  const peakLon = -116.6322;
  const peakLat = 32.5776;
  const peakElevation = 957; // Peak altitude in meters
  const valleyBase = 530; // Valley floor base elevation in meters

  // First, let's calculate the unadjusted height at the origin
  const originDx = origin.longitude - peakLon;
  const originDy = origin.latitude - peakLat;
  const originDist = Math.sqrt(originDx * originDx + originDy * originDy);
  const originMountain = (peakElevation - valleyBase) * Math.exp(-(originDist * originDist) / (2 * 0.007 * 0.007));
  const originDetail = Math.sin(origin.longitude * 1500) * Math.cos(origin.latitude * 1500) * 8 + Math.sin(origin.longitude * 400) * 12;
  const rawOriginHeight = valleyBase + originMountain + originDetail;
  const offset = origin.elevationMeters - rawOriginHeight; // Offset to ensure exact matching of origin elevation (540m)

  // Generate the height grid
  for (let i = 0; i < resolution; i += 1) {
    const row: number[] = [];
    const lat = bounds.south + (i / (resolution - 1)) * (bounds.north - bounds.south);

    for (let j = 0; j < resolution; j += 1) {
      const lon = bounds.west + (j / (resolution - 1)) * (bounds.east - bounds.west);

      // Distance from Cuchumá peak
      const dx = lon - peakLon;
      const dy = lat - peakLat;
      const dist = Math.sqrt(dx * dx + dy * dy);

      // Cuchumá mountain profile (Gaussian peak with standard deviation of ~0.007 degrees)
      const mountain = (peakElevation - valleyBase) * Math.exp(-(dist * dist) / (2 * 0.007 * 0.007));

      // Local undulating terrain and detail noise
      const detail = Math.sin(lon * 1500) * Math.cos(lat * 1500) * 8 + Math.sin(lon * 400) * 12;

      // Combine and adjust with offset
      const elevation = valleyBase + mountain + detail + offset;
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
