import { parseArgs, getNumberArg, resolveWorkspacePath } from "../lib/cli.js";
import { localMetersFromLonLat, lonLatFromLocalMeters, lonLatToWebMercator } from "../lib/geo.js";
import { readJsonFile } from "../lib/fs.js";
import type { ProjectArea } from "../lib/tile.js";

const args = parseArgs();
const metadataPath = resolveWorkspacePath("data/metadata/project-area.json");
const projectArea = await readJsonFile<ProjectArea>(metadataPath);

const origin = {
  latitude: getNumberArg(args, "origin-lat", projectArea.coordinateOriginWgs84.latitude),
  longitude: getNumberArg(args, "origin-lon", projectArea.coordinateOriginWgs84.longitude)
};

if (args.x !== undefined || args.z !== undefined) {
  const localPoint = {
    x: getNumberArg(args, "x"),
    z: getNumberArg(args, "z")
  };

  const wgs84 = lonLatFromLocalMeters(localPoint, origin);
  console.log(JSON.stringify({ origin, localMeters: localPoint, wgs84 }, null, 2));
} else {
  const point = {
    latitude: getNumberArg(args, "lat"),
    longitude: getNumberArg(args, "lon")
  };

  console.log(JSON.stringify({
    origin,
    wgs84: point,
    webMercator: lonLatToWebMercator(point),
    localMeters: localMetersFromLonLat(point, origin)
  }, null, 2));
}

