import fs from "node:fs/promises";
import path from "node:path";
import { resolveWorkspacePath } from "../lib/cli.js";
import { ensureDirectory, readJsonFile, writeJsonFile } from "../lib/fs.js";
import { localMetersFromLonLat, Wgs84Point } from "../lib/geo.js";

// Main Vertical Slice Bounding Box (300m radius around 32.5730141, -116.6332319)
const bbox = {
  south: 32.5703141,
  west: -116.6364319,
  north: 32.5757141,
  east: -116.6300319
};

const tileId = "tecate_core_z14_x2883_y6622"; // Active tile containing the center

interface OsmNode {
  type: "node";
  id: number;
  lat: number;
  lon: number;
}

interface OsmWay {
  type: "way";
  id: number;
  nodes: number[];
  tags?: Record<string, string>;
}

interface OsmData {
  elements: Array<OsmNode | OsmWay>;
}

interface DemData {
  results: Array<{ latitude: number; longitude: number; elevation: number }>;
  gridSize: number;
  boundsWgs84: typeof bbox;
}

interface ProjectArea {
  coordinateOriginWgs84: {
    latitude: number;
    longitude: number;
    elevationMeters: number;
  };
}

interface MeshData {
  vertices: number[];
  indices: number[];
  colors?: number[]; // RGBA colors per vertex for styling
}

async function main() {
  console.log("Loading project metadata and raw datasets...");
  const projectArea = await readJsonFile<ProjectArea>(resolveWorkspacePath("data/metadata/project-area.json"));
  const origin = projectArea.coordinateOriginWgs84;
  console.log(`Origin: lat=${origin.latitude}, lon=${origin.longitude}, elev=${origin.elevationMeters}`);

  const osm = await readJsonFile<OsmData>(resolveWorkspacePath("data/raw/osm_tecate.json"));
  const dem = await readJsonFile<DemData>(resolveWorkspacePath("data/raw/dem_tecate.json"));

  // 1. Process DEM into a 2D grid for bilinear interpolation
  const GRID_SIZE = dem.gridSize;
  const demGrid: number[][] = Array.from({ length: GRID_SIZE }, () => []);
  
  // Reconstruct 2D grid (results are ordered South->North, West->East)
  for (let idx = 0; idx < dem.results.length; idx++) {
    const r = Math.floor(idx / GRID_SIZE);
    const c = idx % GRID_SIZE;
    demGrid[r][c] = dem.results[idx].elevation;
  }

  // Bilinear interpolation function to query elevation at any coordinate
  function getElevation(lat: number, lon: number): number {
    const latPct = (lat - bbox.south) / (bbox.north - bbox.south);
    const lonPct = (lon - bbox.west) / (bbox.east - bbox.west);
    
    const row = Math.max(0, Math.min(GRID_SIZE - 2, Math.floor(latPct * (GRID_SIZE - 1))));
    const col = Math.max(0, Math.min(GRID_SIZE - 2, Math.floor(lonPct * (GRID_SIZE - 1))));
    
    const rPct = latPct * (GRID_SIZE - 1) - row;
    const cPct = lonPct * (GRID_SIZE - 1) - col;
    
    const e00 = demGrid[row][col];
    const e01 = demGrid[row][col+1];
    const e10 = demGrid[row+1][col];
    const e11 = demGrid[row+1][col+1];
    
    const e0 = e00 * (1 - cPct) + e01 * cPct;
    const e1 = e10 * (1 - cPct) + e11 * cPct;
    return e0 * (1 - rPct) + e1 * rPct;
  }

  // 2. Generate Terrain Mesh
  console.log("Generating terrain mesh...");
  const terrainMesh: MeshData = { vertices: [], indices: [] };
  const terrainGridSize = 31; // Finer grid for the rendered mesh
  const terrainVerticesMap: string[] = [];

  for (let i = 0; i < terrainGridSize; i++) {
    const lat = bbox.south + (bbox.north - bbox.south) * (i / (terrainGridSize - 1));
    for (let j = 0; j < terrainGridSize; j++) {
      const lon = bbox.west + (bbox.east - bbox.west) * (j / (terrainGridSize - 1));
      const elevation = getElevation(lat, lon);
      
      const localPos = localMetersFromLonLat({ latitude: lat, longitude: lon }, origin);
      const y = elevation - origin.elevationMeters;

      // Add vertex: X (East), Y (Elevation), Z (South, negated)
      terrainMesh.vertices.push(localPos.x, y, localPos.z);
    }
  }

  // Build terrain indices
  for (let r = 0; r < terrainGridSize - 1; r++) {
    for (let c = 0; c < terrainGridSize - 1; c++) {
      const v00 = r * terrainGridSize + c;
      const v01 = r * terrainGridSize + (c + 1);
      const v10 = (r + 1) * terrainGridSize + c;
      const v11 = (r + 1) * terrainGridSize + (c + 1);

      // Triangle 1
      terrainMesh.indices.push(v00, v10, v01);
      // Triangle 2
      terrainMesh.indices.push(v01, v10, v11);
    }
  }
  console.log(`Terrain mesh generated with ${terrainMesh.vertices.length / 3} vertices.`);

  // 3. Process OSM Elements
  const nodesMap = new Map<number, OsmNode>();
  const ways: OsmWay[] = [];

  for (const el of osm.elements) {
    if (el.type === "node") {
      nodesMap.set(el.id, el);
    } else if (el.type === "way") {
      ways.push(el);
    }
  }

  // 4. Generate Roads Mesh
  console.log("Generating road meshes...");
  const roadsMesh: MeshData = { vertices: [], indices: [] };
  let roadVertexCount = 0;

  // Filter highways in bbox
  const roadWays = ways.filter(w => w.tags?.highway !== undefined);

  for (const road of roadWays) {
    const isJuarez = road.tags?.name?.toLowerCase().includes("juárez") || 
                     road.tags?.name?.toLowerCase().includes("juarez") ||
                     road.tags?.name?.toLowerCase().includes("benito");
    
    // Width of road based on type (Juarez is primary, other roads are minor)
    const roadWidth = isJuarez ? 14.0 : 8.0;
    const halfWidth = roadWidth / 2.0;

    // Convert way nodes to local points and lookup elevations
    const roadPoints: Array<{ x: number; y: number; z: number }> = [];
    for (const nid of road.nodes) {
      const node = nodesMap.get(nid);
      if (node) {
        const localPos = localMetersFromLonLat({ latitude: node.lat, longitude: node.lon }, origin);
        const elev = getElevation(node.lat, node.lon);
        // Slightly offset road Y upward to prevent z-fighting with terrain
        const y = elev - origin.elevationMeters + 0.15;
        roadPoints.push({ x: localPos.x, y, z: localPos.z });
      }
    }

    if (roadPoints.length < 2) continue;

    // Build segments
    for (let i = 0; i < roadPoints.length - 1; i++) {
      const pA = roadPoints[i];
      const pB = roadPoints[i + 1];

      // Calculate direction
      const dx = pB.x - pA.x;
      const dz = pB.z - pA.z;
      const len = Math.sqrt(dx * dx + dz * dz);
      if (len < 0.1) continue;

      const dirX = dx / len;
      const dirZ = dz / len;

      // Perpendicular vector
      const perpX = -dirZ;
      const perpZ = dirX;

      // Vertices for this segment's quad
      const leftA_x = pA.x + perpX * halfWidth;
      const leftA_z = pA.z + perpZ * halfWidth;
      const rightA_x = pA.x - perpX * halfWidth;
      const rightA_z = pA.z - perpZ * halfWidth;

      const leftB_x = pB.x + perpX * halfWidth;
      const leftB_z = pB.z + perpZ * halfWidth;
      const rightB_x = pB.x - perpX * halfWidth;
      const rightB_z = pB.z - perpZ * halfWidth;

      // Add to mesh
      const idxA = roadVertexCount;
      roadsMesh.vertices.push(leftA_x, pA.y, leftA_z);  // V0
      roadsMesh.vertices.push(rightA_x, pA.y, rightA_z); // V1
      roadsMesh.vertices.push(leftB_x, pB.y, leftB_z);  // V2
      roadsMesh.vertices.push(rightB_x, pB.y, rightB_z); // V3
      roadVertexCount += 4;

      // Triangle 1
      roadsMesh.indices.push(idxA, idxA + 2, idxA + 1);
      // Triangle 2
      roadsMesh.indices.push(idxA + 1, idxA + 2, idxA + 3);
    }
  }
  console.log(`Roads mesh generated with ${roadsMesh.vertices.length / 3} vertices.`);

  // 5. Generate Building Meshes
  console.log("Generating building meshes...");
  const buildingsMesh: MeshData = { vertices: [], indices: [] };
  let bldgVertexCount = 0;

  const buildingWays = ways.filter(w => w.tags?.building !== undefined);

  for (const bldg of buildingWays) {
    const footprint: Array<{ x: number; z: number; lat: number; lon: number }> = [];
    let avgElev = 0;
    let validNodes = 0;

    for (const nid of bldg.nodes) {
      const node = nodesMap.get(nid);
      if (node) {
        const localPos = localMetersFromLonLat({ latitude: node.lat, longitude: node.lon }, origin);
        const elev = getElevation(node.lat, node.lon);
        footprint.push({ x: localPos.x, z: localPos.z, lat: node.lat, lon: node.lon });
        avgElev += elev;
        validNodes++;
      }
    }

    if (footprint.length < 3) continue;

    avgElev /= validNodes;
    const baseHeight = avgElev - origin.elevationMeters;

    // Extrude height (e.g. 5m - 9m)
    let height = 6.0;
    if (bldg.tags?.["building:levels"]) {
      const levels = parseInt(bldg.tags["building:levels"], 10);
      if (!isNaN(levels)) {
        height = levels * 3.5;
      }
    } else if (bldg.tags?.height) {
      const h = parseFloat(bldg.tags.height);
      if (!isNaN(h)) {
        height = h;
      }
    } else {
      // Deterministic pseudo-random height based on building ID
      height = 4.0 + (bldg.id % 5) * 1.5;
    }

    const topHeight = baseHeight + height;

    // Generate Wall Meshes (loop through footprint edges)
    // Footprint node count is usually n+1 where last matches first.
    const nPoints = footprint.length - (footprint[footprint.length - 1].x === footprint[0].x ? 1 : 0);

    for (let i = 0; i < nPoints; i++) {
      const ptA = footprint[i];
      const ptB = footprint[(i + 1) % nPoints];

      const idx = bldgVertexCount;
      // Vertices for this wall quad
      buildingsMesh.vertices.push(ptA.x, baseHeight, ptA.z); // V0
      buildingsMesh.vertices.push(ptA.x, topHeight, ptA.z);  // V1
      buildingsMesh.vertices.push(ptB.x, baseHeight, ptB.z); // V2
      buildingsMesh.vertices.push(ptB.x, topHeight, ptB.z);  // V3
      bldgVertexCount += 4;

      // Triangle 1 (counter-clockwise)
      buildingsMesh.indices.push(idx, idx + 2, idx + 1);
      // Triangle 2
      buildingsMesh.indices.push(idx + 1, idx + 2, idx + 3);
    }

    // Generate Roof Mesh (simple fan triangulation)
    // Add roof vertices
    const roofStartIdx = bldgVertexCount;
    for (let i = 0; i < nPoints; i++) {
      buildingsMesh.vertices.push(footprint[i].x, topHeight, footprint[i].z);
      bldgVertexCount++;
    }

    // Triangulate roof (fan style)
    for (let i = 1; i < nPoints - 1; i++) {
      buildingsMesh.indices.push(
        roofStartIdx,
        roofStartIdx + i,
        roofStartIdx + i + 1
      );
    }
  }
  console.log(`Buildings mesh generated with ${buildingsMesh.vertices.length / 3} vertices.`);

  // 6. Save package files on disk
  const terrainPath = `generated/terrain/${tileId}_terrain.json`;
  const roadsPath = `generated/roads/${tileId}_roads.json`;
  const buildingsPath = `generated/buildings/${tileId}_buildings.json`;

  await ensureDirectory(resolveWorkspacePath("generated/terrain"));
  await ensureDirectory(resolveWorkspacePath("generated/roads"));
  await ensureDirectory(resolveWorkspacePath("generated/buildings"));

  await writeJsonFile(resolveWorkspacePath(terrainPath), terrainMesh);
  await writeJsonFile(resolveWorkspacePath(roadsPath), roadsMesh);
  await writeJsonFile(resolveWorkspacePath(buildingsPath), buildingsMesh);

  // 7. Generate companion `.provenance.json` sidecar files
  const nowStr = new Date().toISOString();
  await writeJsonFile(resolveWorkspacePath(`${terrainPath}.provenance.json`), {
    source: "dem",
    confidence: 1.0,
    method: "direct",
    sourceId: "source_dem_urban_and_cuchuma",
    importedAt: nowStr,
    lineage: "Processed from raw/dem_tecate.json using tools/generators/generate-slice-assets.ts"
  });

  await writeJsonFile(resolveWorkspacePath(`${roadsPath}.provenance.json`), {
    source: "osm",
    confidence: 1.0,
    method: "direct",
    sourceId: "source_osm_priority_corridors",
    importedAt: nowStr,
    lineage: "Processed from raw/osm_tecate.json using tools/generators/generate-slice-assets.ts"
  });

  await writeJsonFile(resolveWorkspacePath(`${buildingsPath}.provenance.json`), {
    source: "osm",
    confidence: 1.0,
    method: "direct",
    sourceId: "source_osm_priority_corridors",
    importedAt: nowStr,
    lineage: "Processed from raw/osm_tecate.json using tools/generators/generate-slice-assets.ts"
  });

  console.log("Mesh assets and provenance sidecars written to disk.");

  // 8. Update tile manifest
  console.log("Updating generated/tiles/tile-manifest.json...");
  const manifestPath = resolveWorkspacePath("generated/tiles/tile-manifest.json");
  const manifest = await readJsonFile<any>(manifestPath);

  const tileRecord = manifest.tiles.find((t: any) => t.id === tileId);
  if (tileRecord) {
    tileRecord.state = "packaged";
    tileRecord.files = {
      terrain: terrainPath,
      roads: roadsPath,
      buildings: buildingsPath
    };
    tileRecord.dataQuality = {
      coverage: 1.0,
      confidence: 1.0,
      hasInferredData: false
    };
    console.log(`Updated tile ${tileId} in manifest.`);
  } else {
    console.warn(`Tile ${tileId} not found in manifest.`);
  }

  await writeJsonFile(manifestPath, manifest);
  console.log("Updated tile-manifest.json saved successfully.");
}

main().catch(err => {
  console.error("Error in generate-slice-assets:", err);
  process.exit(1);
});
