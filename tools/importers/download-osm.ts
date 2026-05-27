import fs from "node:fs/promises";
import path from "node:path";
import { resolveWorkspacePath } from "../lib/cli.js";
import { ensureDirectory } from "../lib/fs.js";

// Bounding box for 300m radius around 32.5730141, -116.6332319
const bbox = {
  south: 32.5703141,
  west: -116.6364319,
  north: 32.5757141,
  east: -116.6300319
};

const query = `[out:json][timeout:30];
(
  node(${bbox.south},${bbox.west},${bbox.north},${bbox.east});
  way(${bbox.south},${bbox.west},${bbox.north},${bbox.east});
  relation(${bbox.south},${bbox.west},${bbox.north},${bbox.east});
);
out body;
>;
out skel qt;`;

const endpoint = "https://overpass-api.de/api/interpreter";

async function main() {
  console.log("Downloading OSM data from Overpass API...");
  console.log(`Bounding Box: S:${bbox.south}, W:${bbox.west}, N:${bbox.north}, E:${bbox.east}`);

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "TecateSimulatorVerticalSlice/1.0 (hakkindavid@github)"
      },
      body: `data=${encodeURIComponent(query)}`
    });

    if (!response.ok) {
      throw new Error(`Overpass API responded with HTTP status ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    const outputPath = resolveWorkspacePath("data/raw/osm_tecate.json");
    await ensureDirectory(path.dirname(outputPath));
    await fs.writeFile(outputPath, JSON.stringify(data, null, 2), "utf8");

    console.log(`OSM data downloaded successfully to ${outputPath}`);
    console.log(`Found ${(data as any).elements?.length || 0} OSM elements.`);
  } catch (error) {
    console.error("Failed to download OSM data:", error);
    process.exit(1);
  }
}

main();
