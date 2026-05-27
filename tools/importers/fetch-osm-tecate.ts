import { promises as fs } from "node:fs";
import { resolveWorkspacePath } from "../lib/cli.js";
import { readJsonFile } from "../lib/fs.js";
import type { ProjectArea } from "../lib/tile.js";

interface OverpassNode {
  type: "node";
  id: number;
  lat: number;
  lon: number;
}

interface OverpassWay {
  type: "way";
  id: number;
  nodes: number[];
  tags?: Record<string, string>;
}

interface OverpassResponse {
  elements: Array<OverpassNode | OverpassWay>;
}

async function main() {
  const projectAreaPath = resolveWorkspacePath("data/metadata/project-area.json");
  const projectArea = await readJsonFile<ProjectArea>(projectAreaPath);
  const bounds = projectArea.boundsWgs84;

  const query = `[out:json][timeout:90];
(
  way["highway"](${bounds.south},${bounds.west},${bounds.north},${bounds.east});
  way["building"](${bounds.south},${bounds.west},${bounds.north},${bounds.east});
);
out body;
>;
out skel qt;`;

  console.log("Fetching OSM data from Overpass API (this may take a few seconds)...");
  const response = await fetch("https://overpass-api.de/api/interpreter", {
    method: "POST",
    body: "data=" + encodeURIComponent(query),
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "User-Agent": "TecateSpatialMemorySimulator/0.1.0 (hakkindavid@github.com)"
    }
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch OSM data: ${response.statusText} (${response.status})`);
  }

  const data = (await response.json()) as OverpassResponse;
  console.log(`Received ${data.elements.length} elements from Overpass.`);

  // Separate nodes and ways
  const nodes = new Map<number, [number, number]>();
  const ways: OverpassWay[] = [];

  for (const element of data.elements) {
    if (element.type === "node") {
      nodes.set(element.id, [element.lon, element.lat]);
    } else if (element.type === "way") {
      ways.push(element);
    }
  }

  console.log(`Found ${nodes.size} nodes and ${ways.length} ways.`);

  // Convert to GeoJSON FeatureCollection
  const features = [];

  for (const way of ways) {
    const coords = way.nodes
      .map((nodeId) => nodes.get(nodeId))
      .filter((coord): coord is [number, number] => coord !== undefined);

    if (coords.length < 2) {
      continue; // Skips invalid geometries
    }

    const tags = way.tags || {};
    const isBuilding = tags.building !== undefined;

    if (isBuilding) {
      const cStart = coords[0]!;
      const cEnd = coords[coords.length - 1]!;
      if (
        cStart[0] !== cEnd[0] ||
        cStart[1] !== cEnd[1]
      ) {
        coords.push([cStart[0], cStart[1]]);
      }

      features.push({
        type: "Feature",
        id: way.id,
        properties: {
          id: `building_${way.id}`,
          building: tags.building,
          name: tags.name || "",
          levels: tags["building:levels"] || tags["building:levels:underground"] || "1"
        },
        geometry: {
          type: "Polygon",
          coordinates: [coords]
        }
      });
    } else {
      features.push({
        type: "Feature",
        id: way.id,
        properties: {
          id: `road_${way.id}`,
          highway: tags.highway,
          name: tags.name || ""
        },
        geometry: {
          type: "LineString",
          coordinates: coords
        }
      });
    }
  }

  const geojson = {
    type: "FeatureCollection",
    features
  };

  const outputPath = resolveWorkspacePath("data/raw/tecate-osm.geojson");
  await fs.writeFile(outputPath, JSON.stringify(geojson, null, 2), "utf8");
  console.log(`Saved ${features.length} GeoJSON features to ${outputPath}`);
}

main().catch((err) => {
  console.error("OSM Ingestion failed:", err);
  process.exit(1);
});
