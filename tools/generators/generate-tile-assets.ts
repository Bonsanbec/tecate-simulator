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
      let roadsObj = `# Roads and Streetscape mesh for ${tile.id}\n`;
      
      let vertexCount = 0;

      // Group buffers
      let vertsObj = "";
      let asphaltFaces = "";
      let sidewalkFaces = "";
      let dividerFaces = "";
      let polesFaces = "";

      // Utility pole concrete cylinder box helper
      function addConcretePole(cx: number, yb: number, cz: number) {
        const w = 0.3; // Rectangular pole thickness
        const h = 8.0; // 8 meters tall
        const halfW = w / 2;
        const yt = yb + h;

        // 8 vertices for rectangular utility column
        const p = [
          { x: cx - halfW, y: yb, z: cz - halfW },
          { x: cx + halfW, y: yb, z: cz - halfW },
          { x: cx + halfW, y: yb, z: cz + halfW },
          { x: cx - halfW, y: yb, z: cz + halfW },
          { x: cx - halfW, y: yt, z: cz - halfW },
          { x: cx + halfW, y: yt, z: cz - halfW },
          { x: cx + halfW, y: yt, z: cz + halfW },
          { x: cx - halfW, y: yt, z: cz + halfW }
        ];

        for (const v of p) {
          vertsObj += `v ${v.x.toFixed(3)} ${v.y.toFixed(3)} ${v.z.toFixed(3)}\n`;
        }

        const startIdx = vertexCount + 1;
        // 6 faces (12 triangles)
        // bottom
        polesFaces += `f ${startIdx} ${startIdx + 3} ${startIdx + 2}\n`;
        polesFaces += `f ${startIdx + 2} ${startIdx + 1} ${startIdx}\n`;
        // top
        polesFaces += `f ${startIdx + 4} ${startIdx + 5} ${startIdx + 6}\n`;
        polesFaces += `f ${startIdx + 6} ${startIdx + 7} ${startIdx + 4}\n`;
        // front
        polesFaces += `f ${startIdx} ${startIdx + 1} ${startIdx + 5}\n`;
        polesFaces += `f ${startIdx + 5} ${startIdx + 4} ${startIdx}\n`;
        // back
        polesFaces += `f ${startIdx + 2} ${startIdx + 3} ${startIdx + 7}\n`;
        polesFaces += `f ${startIdx + 7} ${startIdx + 6} ${startIdx + 2}\n`;
        // left
        polesFaces += `f ${startIdx + 3} ${startIdx} ${startIdx + 4}\n`;
        polesFaces += `f ${startIdx + 4} ${startIdx + 7} ${startIdx + 3}\n`;
        // right
        polesFaces += `f ${startIdx + 1} ${startIdx + 2} ${startIdx + 6}\n`;
        polesFaces += `f ${startIdx + 6} ${startIdx + 5} ${startIdx + 1}\n`;

        vertexCount += 8;
      }

      for (const road of roads) {
        const coords = road.geometry.coordinates as [number, number][];
        const isJuarez = road.properties.name?.toLowerCase().includes("juarez") || road.properties.highway === "primary";
        const roadWidth = isJuarez ? 12.0 : 8.0;

        let accumulatedLength = 0;

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

          accumulatedLength += len;

          // Normal direction perpendicular to road in XZ plane
          const nx = -dz / len;
          const nz = dx / len;

          const halfW = roadWidth / 2;

          // Helper to resolve elevation offsets relative to terrain base
          const getElev = (x: number, z: number, verticalOffset: number) => {
            const lonLat = {
              longitude: origin.longitude + (x / 6378137.0) * (180.0 / Math.PI),
              latitude: origin.latitude - (z / 6378137.0) * (180.0 / Math.PI)
            };
            return getElevation(lonLat.longitude, lonLat.latitude) - origin.elevationMeters + verticalOffset;
          };

          // ----------------------------------------------------
          // A. Generate Asphalt Road Vertices
          // ----------------------------------------------------
          const r0_x = p0.x - nx * halfW;
          const r0_z = p0.z - nz * halfW;
          const r1_x = p0.x + nx * halfW;
          const r1_z = p0.z + nz * halfW;
          const r2_x = p1.x + nx * halfW;
          const r2_z = p1.z + nz * halfW;
          const r3_x = p1.x - nx * halfW;
          const r3_z = p1.z - nz * halfW;

          const y0_r = getElev(r0_x, r0_z, 0.05);
          const y1_r = getElev(r1_x, r1_z, 0.05);
          const y2_r = getElev(r2_x, r2_z, 0.05);
          const y3_r = getElev(r3_x, r3_z, 0.05);

          vertsObj += `v ${r0_x.toFixed(3)} ${y0_r.toFixed(3)} ${r0_z.toFixed(3)}\n`;
          vertsObj += `v ${r1_x.toFixed(3)} ${y1_r.toFixed(3)} ${r1_z.toFixed(3)}\n`;
          vertsObj += `v ${r2_x.toFixed(3)} ${y2_r.toFixed(3)} ${r2_z.toFixed(3)}\n`;
          vertsObj += `v ${r3_x.toFixed(3)} ${y3_r.toFixed(3)} ${r3_z.toFixed(3)}\n`;

          const ar0 = vertexCount + 1;
          const ar1 = vertexCount + 2;
          const ar2 = vertexCount + 3;
          const ar3 = vertexCount + 4;

          asphaltFaces += `f ${ar0} ${ar1} ${ar2}\n`;
          asphaltFaces += `f ${ar2} ${ar3} ${ar0}\n`;

          vertexCount += 4;

          // ----------------------------------------------------
          // B. Generate raised concrete curbs & sidewalks (banquetas)
          // ----------------------------------------------------
          const sW = 2.0; // Sidewalk width 2 meters
          const curbH = 0.15; // Raised sidewalk height

          // Left Sidewalk
          const sl0_out_x = p0.x - nx * (halfW + sW);
          const sl0_out_z = p0.z - nz * (halfW + sW);
          const sl0_in_x = p0.x - nx * halfW;
          const sl0_in_z = p0.z - nz * halfW;
          const sl1_in_x = p1.x - nx * halfW;
          const sl1_in_z = p1.z - nz * halfW;
          const sl1_out_x = p1.x - nx * (halfW + sW);
          const sl1_out_z = p1.z - nz * (halfW + sW);

          const yl0_out = getElev(sl0_out_x, sl0_out_z, 0.05 + curbH);
          const yl0_in = getElev(sl0_in_x, sl0_in_z, 0.05 + curbH);
          const yl1_in = getElev(sl1_in_x, sl1_in_z, 0.05 + curbH);
          const yl1_out = getElev(sl1_out_x, sl1_out_z, 0.05 + curbH);

          vertsObj += `v ${sl0_out_x.toFixed(3)} ${yl0_out.toFixed(3)} ${sl0_out_z.toFixed(3)}\n`;
          vertsObj += `v ${sl0_in_x.toFixed(3)} ${yl0_in.toFixed(3)} ${sl0_in_z.toFixed(3)}\n`;
          vertsObj += `v ${sl1_in_x.toFixed(3)} ${yl1_in.toFixed(3)} ${sl1_in_z.toFixed(3)}\n`;
          vertsObj += `v ${sl1_out_x.toFixed(3)} ${yl1_out.toFixed(3)} ${sl1_out_z.toFixed(3)}\n`;

          const sL0 = vertexCount + 1;
          const sL1 = vertexCount + 2;
          const sL2 = vertexCount + 3;
          const sL3 = vertexCount + 4;

          sidewalkFaces += `f ${sL0} ${sL1} ${sL2}\n`;
          sidewalkFaces += `f ${sL2} ${sL3} ${sL0}\n`;

          vertexCount += 4;

          // Right Sidewalk
          const sr0_in_x = p0.x + nx * halfW;
          const sr0_in_z = p0.z + nz * halfW;
          const sr0_out_x = p0.x + nx * (halfW + sW);
          const sr0_out_z = p0.z + nz * (halfW + sW);
          const sr1_out_x = p1.x + nx * (halfW + sW);
          const sr1_out_z = p1.z + nz * (halfW + sW);
          const sr1_in_x = p1.x + nx * halfW;
          const sr1_in_z = p1.z + nz * halfW;

          const yr0_in = getElev(sr0_in_x, sr0_in_z, 0.05 + curbH);
          const yr0_out = getElev(sr0_out_x, sr0_out_z, 0.05 + curbH);
          const yr1_out = getElev(sr1_out_x, sr1_out_z, 0.05 + curbH);
          const yr1_in = getElev(sr1_in_x, sr1_in_z, 0.05 + curbH);

          vertsObj += `v ${sr0_in_x.toFixed(3)} ${yr0_in.toFixed(3)} ${sr0_in_z.toFixed(3)}\n`;
          vertsObj += `v ${sr0_out_x.toFixed(3)} ${yr0_out.toFixed(3)} ${sr0_out_z.toFixed(3)}\n`;
          vertsObj += `v ${sr1_out_x.toFixed(3)} ${yr1_out.toFixed(3)} ${sr1_out_z.toFixed(3)}\n`;
          vertsObj += `v ${sr1_in_x.toFixed(3)} ${yr1_in.toFixed(3)} ${sr1_in_z.toFixed(3)}\n`;

          const sR0 = vertexCount + 1;
          const sR1 = vertexCount + 2;
          const sR2 = vertexCount + 3;
          const sR3 = vertexCount + 4;

          sidewalkFaces += `f ${sR0} ${sR1} ${sR2}\n`;
          sidewalkFaces += `f ${sR2} ${sR3} ${sR0}\n`;

          vertexCount += 4;

          // ----------------------------------------------------
          // C. Generate raised yellow lane divider for Boulevard Juárez
          // ----------------------------------------------------
          if (isJuarez) {
            const divW = 0.15; // 15cm yellow divider
            const d0_x = p0.x - nx * (divW / 2);
            const d0_z = p0.z - nz * (divW / 2);
            const d1_x = p0.x + nx * (divW / 2);
            const d1_z = p0.z + nz * (divW / 2);
            const d2_x = p1.x + nx * (divW / 2);
            const d2_z = p1.z + nz * (divW / 2);
            const d3_x = p1.x - nx * (divW / 2);
            const d3_z = p1.z - nz * (divW / 2);

            const yd0 = getElev(d0_x, d0_z, 0.07); // Raised slightly (+2cm) above road
            const yd1 = getElev(d1_x, d1_z, 0.07);
            const yd2 = getElev(d2_x, d2_z, 0.07);
            const yd3 = getElev(d3_x, d3_z, 0.07);

            vertsObj += `v ${d0_x.toFixed(3)} ${yd0.toFixed(3)} ${d0_z.toFixed(3)}\n`;
            vertsObj += `v ${d1_x.toFixed(3)} ${yd1.toFixed(3)} ${d1_z.toFixed(3)}\n`;
            vertsObj += `v ${d2_x.toFixed(3)} ${yd2.toFixed(3)} ${d2_z.toFixed(3)}\n`;
            vertsObj += `v ${d3_x.toFixed(3)} ${yd3.toFixed(3)} ${d3_z.toFixed(3)}\n`;

            const dr0 = vertexCount + 1;
            const dr1 = vertexCount + 2;
            const dr2 = vertexCount + 3;
            const dr3 = vertexCount + 4;

            dividerFaces += `f ${dr0} ${dr1} ${dr2}\n`;
            dividerFaces += `f ${dr2} ${dr3} ${dr0}\n`;

            vertexCount += 4;
          }

          // ----------------------------------------------------
          // D. Generate concrete utility poles every 30 meters
          // ----------------------------------------------------
          if (accumulatedLength >= 30.0) {
            // Place concrete poles on the outer margin of the sidewalks
            const leftPoleX = p0.x - nx * (halfW + sW - 0.2);
            const leftPoleZ = p0.z - nz * (halfW + sW - 0.2);
            const yLeft = getElev(leftPoleX, leftPoleZ, 0.05 + curbH);

            const rightPoleX = p0.x + nx * (halfW + sW - 0.2);
            const rightPoleZ = p0.z + nz * (halfW + sW - 0.2);
            const yRight = getElev(rightPoleX, rightPoleZ, 0.05 + curbH);

            addConcretePole(leftPoleX, yLeft, leftPoleZ);
            addConcretePole(rightPoleX, yRight, rightPoleZ);

            accumulatedLength = 0; // reset
          }
        }
      }

      if (vertexCount > 0) {
        // To prevent Godot OBJ import failures and surface index shifting,
        // we must ensure all 4 groups (asphalt, sidewalks, yellow_divider, utility_poles)
        // are present and non-empty. If any group has no faces, we insert a tiny hidden dummy
        // triangle 100 meters underground at the origin.
        if (asphaltFaces.length === 0) {
          const vIdx = vertexCount + 1;
          vertsObj += `v 0.000 -100.000 0.000\n`;
          vertsObj += `v 0.001 -100.000 0.000\n`;
          vertsObj += `v 0.000 -100.000 0.001\n`;
          asphaltFaces += `f ${vIdx} ${vIdx + 1} ${vIdx + 2}\n`;
          vertexCount += 3;
        }
        if (sidewalkFaces.length === 0) {
          const vIdx = vertexCount + 1;
          vertsObj += `v 0.000 -100.000 0.000\n`;
          vertsObj += `v 0.001 -100.000 0.000\n`;
          vertsObj += `v 0.000 -100.000 0.001\n`;
          sidewalkFaces += `f ${vIdx} ${vIdx + 1} ${vIdx + 2}\n`;
          vertexCount += 3;
        }
        if (dividerFaces.length === 0) {
          const vIdx = vertexCount + 1;
          vertsObj += `v 0.000 -100.000 0.000\n`;
          vertsObj += `v 0.001 -100.000 0.000\n`;
          vertsObj += `v 0.000 -100.000 0.001\n`;
          dividerFaces += `f ${vIdx} ${vIdx + 1} ${vIdx + 2}\n`;
          vertexCount += 3;
        }
        if (polesFaces.length === 0) {
          const vIdx = vertexCount + 1;
          vertsObj += `v 0.000 -100.000 0.000\n`;
          vertsObj += `v 0.001 -100.000 0.000\n`;
          vertsObj += `v 0.000 -100.000 0.001\n`;
          polesFaces += `f ${vIdx} ${vIdx + 1} ${vIdx + 2}\n`;
          vertexCount += 3;
        }

        // Concatenate all vertices first, followed by group faces!
        roadsObj += vertsObj;
        roadsObj += `g asphalt\n` + asphaltFaces;
        roadsObj += `g sidewalks\n` + sidewalkFaces;
        roadsObj += `g yellow_divider\n` + dividerFaces;
        roadsObj += `g utility_poles\n` + polesFaces;

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
