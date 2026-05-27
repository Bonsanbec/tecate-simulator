import path from "node:path";
import { getStringArg, parseArgs, resolveWorkspacePath } from "../lib/cli.js";
import { readJsonFile, writeJsonFile } from "../lib/fs.js";
import type { Wgs84Bounds } from "../lib/geo.js";

type GeoJsonGeometry = {
  type: string;
  coordinates: unknown;
};

type GeoJsonFeature = {
  type: "Feature";
  id?: string | number;
  properties?: Record<string, unknown> | null;
  geometry: GeoJsonGeometry | null;
};

type GeoJsonFeatureCollection = {
  type: "FeatureCollection";
  features: GeoJsonFeature[];
};

function expandBounds(bounds: Wgs84Bounds | undefined, longitude: number, latitude: number): Wgs84Bounds {
  if (!bounds) {
    return { west: longitude, south: latitude, east: longitude, north: latitude };
  }

  return {
    west: Math.min(bounds.west, longitude),
    south: Math.min(bounds.south, latitude),
    east: Math.max(bounds.east, longitude),
    north: Math.max(bounds.north, latitude)
  };
}

function walkCoordinates(value: unknown, callback: (longitude: number, latitude: number) => void): void {
  if (!Array.isArray(value)) {
    return;
  }

  if (typeof value[0] === "number" && typeof value[1] === "number") {
    callback(value[0], value[1]);
    return;
  }

  for (const child of value) {
    walkCoordinates(child, callback);
  }
}

function featureBounds(feature: GeoJsonFeature): Wgs84Bounds | undefined {
  let bounds: Wgs84Bounds | undefined;
  walkCoordinates(feature.geometry?.coordinates, (longitude, latitude) => {
    bounds = expandBounds(bounds, longitude, latitude);
  });
  return bounds;
}

const args = parseArgs();
const inputPath = resolveWorkspacePath(getStringArg(args, "input"));
const outputDirectory = resolveWorkspacePath(getStringArg(args, "out-dir", "data/gis/imported"));
const inputName = path.basename(inputPath, path.extname(inputPath));

const geojson = await readJsonFile<GeoJsonFeatureCollection>(inputPath);

if (geojson.type !== "FeatureCollection" || !Array.isArray(geojson.features)) {
  throw new Error("Input must be a GeoJSON FeatureCollection");
}

let collectionBounds: Wgs84Bounds | undefined;

const features = geojson.features.map((feature, index) => {
  const boundsWgs84 = featureBounds(feature);
  if (boundsWgs84) {
    collectionBounds = expandBounds(collectionBounds, boundsWgs84.west, boundsWgs84.south);
    collectionBounds = expandBounds(collectionBounds, boundsWgs84.east, boundsWgs84.north);
  }

  return {
    id: String(feature.id ?? `${inputName}_${index.toString().padStart(5, "0")}`),
    geometryType: feature.geometry?.type ?? "Null",
    properties: feature.properties ?? {},
    boundsWgs84,
    geometry: feature.geometry
  };
});

const outputPath = path.join(outputDirectory, `${inputName}.features.json`);
await writeJsonFile(outputPath, {
  schemaVersion: "0.1.0",
  source: {
    inputPath,
    importedAt: new Date().toISOString(),
    status: "normalized-from-geojson"
  },
  featureCount: features.length,
  boundsWgs84: collectionBounds,
  features
});

console.log(`Imported ${features.length} features to ${outputPath}`);

