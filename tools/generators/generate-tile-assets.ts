import { promises as fs } from "node:fs";
import path from "node:path";
import { resolveWorkspacePath } from "../lib/cli.js";
import { readJsonFile, writeJsonFile, pathExists } from "../lib/fs.js";
import { localMetersFromLonLat, tileBoundsWgs84, boundsIntersect, type Wgs84Bounds } from "../lib/geo.js";
import type { TileManifest, TileRecord } from "../lib/tile.js";

interface Feature {
  id: string;
  geometryType: string;
  properties: Record<string, any>;
  boundsWgs84?: Wgs84Bounds;
  geometry: {
    type: string;
    coordinates: any;
  };
}

interface FeatureSet {
  features: Feature[];
}

interface DemData {
  boundsWgs84: Wgs84Bounds;
  resolution: number;
  grid: number[][];
}

async function main() {
  const manifestPath = resolveWorkspacePath("generated/tiles/tile-manifest.json");
  const demPath = resolveWorkspacePath("data/terrain/tecate-terrain-dem.json");
  const featuresPath = resolveWorkspacePath("data/gis/imported/tecate-osm.features.json");
  const tilesDir = resolveWorkspacePath("godot/world/tiles");

  // Ensure output directory exists
  if (!await pathExists(tilesDir)) {
    await fs.mkdir(tilesDir, { recursive: true });
  }

  console.log("Loading datasets...");
  const manifest = await readJsonFile<TileManifest>(manifestPath);
  const dem = await readJsonFile<DemData>(demPath);
  const featureSet = await readJsonFile<FeatureSet>(featuresPath);

  const origin = manifest.coordinateOriginWgs84;
  const tiles = manifest.tiles;

  // Bilinear sampling helper for terrain elevation
  function getElevation(lon: number, lat: number): number {
    const w = dem.boundsWgs84.west;
    const e = dem.boundsWgs84.east;
    const s = dem.boundsWgs84.south;
    const n = dem.boundsWgs84.north;

    const u = (lon - w) / (e - w);
    const v = (lat - s) / (n - s);

    if (u < 0 || u > 1 || v < 0 || v > 1) {
      return 540.0;
    }

    const resolution = dem.resolution;
    const px = u * (resolution - 1);
    const py = v * (resolution - 1);

    const x0 = Math.floor(px);
    const x1 = Math.min(resolution - 1, x0 + 1);
    const y0 = Math.floor(py);
    const y1 = Math.min(resolution - 1, y0 + 1);

    const fx = px - x0;
    const fy = py - y0;

    const rowY0 = dem.grid[y0]!;
    const rowY1 = dem.grid[y1]!;
    const h00 = rowY0[x0]!;
    const h10 = rowY0[x1]!;
    const h01 = rowY1[x0]!;
    const h11 = rowY1[x1]!;

    const h0 = h00 * (1 - fx) + h10 * fx;
    const h1 = h01 * (1 - fx) + h11 * fx;

    return h0 * (1 - fy) + h1 * fy;
  }

  console.log(`Generating 3D tile meshes for ${tiles.length} tiles...`);

  let tilesProcessed = 0;

  for (const tile of tiles) {
    const tileBounds = tile.boundsWgs84;

    // 1. Generate Terrain Mesh
    let terrainObj = `# Terrain mesh for ${tile.id}\n`;
    const gridSize = 16; // 17x17 grid

    for (let gy = 0; gy <= gridSize; gy += 1) {
      const lat = tileBounds.south + (gy / gridSize) * (tileBounds.north - tileBounds.south);
      for (let gx = 0; gx <= gridSize; gx += 1) {
        const lon = tileBounds.west + (gx / gridSize) * (tileBounds.east - tileBounds.west);
        const elevation = getElevation(lon, lat);
        const localPt = localMetersFromLonLat({ longitude: lon, latitude: lat }, origin);
        const y = elevation - origin.elevationMeters;
        terrainObj += `v ${localPt.x.toFixed(3)} ${y.toFixed(3)} ${localPt.z.toFixed(3)}\n`;
      }
    }

    // Faces (1-indexed)
    const stride = gridSize + 1;
    for (let gy = 0; gy < gridSize; gy += 1) {
      for (let gx = 0; gx < gridSize; gx += 1) {
        const idx0 = gy * stride + gx + 1;
        const idx1 = gy * stride + (gx + 1) + 1;
        const idx2 = (gy + 1) * stride + (gx + 1) + 1;
        const idx3 = (gy + 1) * stride + gx + 1;

        terrainObj += `f ${idx0} ${idx1} ${idx2}\n`;
        terrainObj += `f ${idx2} ${idx3} ${idx0}\n`;
      }
    }

    const terrainPath = path.join(tilesDir, `${tile.id}_terrain.obj`);
    await fs.writeFile(terrainPath, terrainObj, "utf8");
    tile.files["terrain_mesh"] = `godot/world/tiles/${tile.id}_terrain.obj`;

    // 2. Identify overlapping features
    const overlappingFeatures = featureSet.features.filter((f) => {
      if (!f.boundsWgs84) return false;
      return boundsIntersect(tileBounds, f.boundsWgs84);
    });

    const roads = overlappingFeatures.filter((f) => f.properties.highway !== undefined);
    const buildings = overlappingFeatures.filter((f) => f.properties.building !== undefined);

    // 3. Generate Roads Mesh
    if (roads.length > 0) {
      let roadsObj = `# Roads mesh for ${tile.id}\n`;
      let vertexCount = 0;

      for (const road of roads) {
        const coords = road.geometry.coordinates as [number, number][];
        const isJuarez = road.properties.name?.toLowerCase().includes("juarez") || road.properties.highway === "primary";
        const roadWidth = isJuarez ? 12.0 : 8.0;

        for (let i = 0; i < coords.length - 1; i += 1) {
          const c0 = coords[i]!;
          const c1 = coords[i + 1]!;

          // Compute midpoint WGS84 to see if the segment is inside the tile bounds
          const midLon = (c0[0]! + c1[0]!) / 2;
          const midLat = (c0[1]! + c1[1]!) / 2;

          if (
            midLon < tileBounds.west ||
            midLon > tileBounds.east ||
            midLat < tileBounds.south ||
            midLat > tileBounds.north
          ) {
            continue; // Skips segments not physically inside this tile
          }

          const p0 = localMetersFromLonLat({ longitude: c0[0]!, latitude: c0[1]! }, origin);
          const p1 = localMetersFromLonLat({ longitude: c1[0]!, latitude: c1[1]! }, origin);

          const dx = p1.x - p0.x;
          const dz = p1.z - p0.z;
          const len = Math.sqrt(dx * dx + dz * dz);
          if (len < 0.1) continue;

          // Normal direction perpendicular to road in XZ plane
          const nx = -dz / len;
          const nz = dx / len;

          const halfW = roadWidth / 2;
          const v0_x = p0.x - nx * halfW;
          const v0_z = p0.z - nz * halfW;
          const v1_x = p0.x + nx * halfW;
          const v1_z = p0.z + nz * halfW;
          const v2_x = p1.x + nx * halfW;
          const v2_z = p1.z + nz * halfW;
          const v3_x = p1.x - nx * halfW;
          const v3_z = p1.z - nz * halfW;

          // Resolve corner elevation and add small offset (0.05m) to avoid Z-fighting
          const getElevationOffset = (x: number, z: number) => {
            const lonLat = {
              longitude: origin.longitude + (x / 6378137.0) * (180.0 / Math.PI),
              latitude: origin.latitude - (z / 6378137.0) * (180.0 / Math.PI)
            };
            return getElevation(lonLat.longitude, lonLat.latitude) - origin.elevationMeters + 0.05;
          };

          const y0 = getElevationOffset(v0_x, v0_z);
          const y1 = getElevationOffset(v1_x, v1_z);
          const y2 = getElevationOffset(v2_x, v2_z);
          const y3 = getElevationOffset(v3_x, v3_z);

          roadsObj += `v ${v0_x.toFixed(3)} ${y0.toFixed(3)} ${v0_z.toFixed(3)}\n`;
          roadsObj += `v ${v1_x.toFixed(3)} ${y1.toFixed(3)} ${v1_z.toFixed(3)}\n`;
          roadsObj += `v ${v2_x.toFixed(3)} ${y2.toFixed(3)} ${v2_z.toFixed(3)}\n`;
          roadsObj += `v ${v3_x.toFixed(3)} ${y3.toFixed(3)} ${v3_z.toFixed(3)}\n`;

          const i0 = vertexCount + 1;
          const i1 = vertexCount + 2;
          const i2 = vertexCount + 3;
          const i3 = vertexCount + 4;

          roadsObj += `f ${i0} ${i1} ${i2}\n`;
          roadsObj += `f ${i2} ${i3} ${i0}\n`;

          vertexCount += 4;
        }
      }

      if (vertexCount > 0) {
        const roadsPath = path.join(tilesDir, `${tile.id}_roads.obj`);
        await fs.writeFile(roadsPath, roadsObj, "utf8");
        tile.files["roads_mesh"] = `godot/world/tiles/${tile.id}_roads.obj`;
      }
    }

    // 4. Generate Buildings Mesh
    if (buildings.length > 0) {
      let bldObj = `# Buildings mesh for ${tile.id}\n`;
      let vertexCount = 0;

      for (const building of buildings) {
        // Polygons are structured as coords[0] being the outer ring
        const rings = building.geometry.coordinates as [number, number][][];
        if (!rings || rings.length === 0) continue;
        const coords = rings[0]!;
        if (coords.length < 3) continue;

        // Calculate building center WGS84
        let sumLon = 0;
        let sumLat = 0;
        for (const coord of coords) {
          sumLon += coord[0]!;
          sumLat += coord[1]!;
        }
        const centerLon = sumLon / coords.length;
        const centerLat = sumLat / coords.length;

        // Get ground height
        const groundHeight = getElevation(centerLon, centerLat) - origin.elevationMeters;
        const levels = parseInt(building.properties.levels || "1", 10) || 1;
        const bldHeight = levels * 4.0;
        const roofHeight = groundHeight + bldHeight;

        // Collect footprint vertices in local coordinates
        const localPts = coords.map((c) => localMetersFromLonLat({ longitude: c[0]!, latitude: c[1]! }, origin));

        const n = localPts.length;
        // Output ground vertices (indices 1 to n)
        for (const p of localPts) {
          bldObj += `v ${p.x.toFixed(3)} ${groundHeight.toFixed(3)} ${p.z.toFixed(3)}\n`;
        }
        // Output roof vertices (indices n+1 to 2n)
        for (const p of localPts) {
          bldObj += `v ${p.x.toFixed(3)} ${roofHeight.toFixed(3)} ${p.z.toFixed(3)}\n`;
        }

        // Output walls (connecting ground and roof vertices)
        for (let i = 0; i < n - 1; i += 1) {
          const g0 = vertexCount + i + 1;
          const g1 = vertexCount + i + 2;
          const r0 = vertexCount + n + i + 1;
          const r1 = vertexCount + n + i + 2;

          // Wall quad (g0, g1, r1, r0)
          bldObj += `f ${g0} ${g1} ${r1}\n`;
          bldObj += `f ${r1} ${r0} ${g0}\n`;
        }

        // Triangulate roof using a simple peak center point (Triangle Fan)
        let sumLocalX = 0;
        let sumLocalZ = 0;
        for (const p of localPts) {
          sumLocalX += p.x;
          sumLocalZ += p.z;
        }
        const centerLocalX = sumLocalX / localPts.length;
        const centerLocalZ = sumLocalZ / localPts.length;

        // Output roof peak vertex (index 2n + 1)
        bldObj += `v ${centerLocalX.toFixed(3)} ${roofHeight.toFixed(3)} ${centerLocalZ.toFixed(3)}\n`;
        const peakIdx = vertexCount + 2 * n + 1;

        // Output roof triangles
        for (let i = 0; i < n - 1; i += 1) {
          const r0 = vertexCount + n + i + 1;
          const r1 = vertexCount + n + i + 2;
          bldObj += `f ${r0} ${r1} ${peakIdx}\n`;
        }

        vertexCount += 2 * n + 1;
      }

      if (vertexCount > 0) {
        const bldPath = path.join(tilesDir, `${tile.id}_buildings.obj`);
        await fs.writeFile(bldPath, bldObj, "utf8");
        tile.files["buildings_mesh"] = `godot/world/tiles/${tile.id}_buildings.obj`;
      }
    }

    tile.state = "generated";
    tilesProcessed += 1;
  }

  // Rewrite tile manifest with mesh file references
  await writeJsonFile(manifestPath, manifest);

  console.log(`Successfully generated OBJ meshes for ${tilesProcessed} tiles.`);
}

main().catch((err) => {
  console.error("Asset generation failed:", err);
  process.exit(1);
});
