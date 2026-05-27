import path from "node:path";
import { resolveWorkspacePath } from "../lib/cli.js";
import { pathExists, readJsonFile, sha256File, writeJsonFile } from "../lib/fs.js";
import type { TileManifest, TileRecord } from "../lib/tile.js";

interface SourceInventory {
  sources: Array<{ id: string }>;
}

interface ProvenanceData {
  source: "dem" | "osm" | "imagery" | "inferred";
  confidence: number;
  method: "direct" | "extruded" | "interpolated" | "heuristic";
  sourceId?: string;
  importedAt?: string;
  lineage?: unknown;
}

const manifestPath = resolveWorkspacePath("generated/tiles/tile-manifest.json");
const sourceInventoryPath = resolveWorkspacePath("data/metadata/source-inventory.json");
const outputPath = resolveWorkspacePath("generated/packages/tecate-core-tile-package.json");
const workspaceRootPath = resolveWorkspacePath(".");

if (!await pathExists(manifestPath)) {
  throw new Error("Missing generated/tiles/tile-manifest.json. Run npm run tiles:generate first.");
}

const manifest = await readJsonFile<TileManifest>(manifestPath);

// Load source inventory to validate source IDs
if (!await pathExists(sourceInventoryPath)) {
  throw new Error("Missing data/metadata/source-inventory.json. Ensure project metadata is present.");
}
const inventory = await readJsonFile<SourceInventory>(sourceInventoryPath);
const validSourceIds = new Set(inventory.sources.map(src => src.id));

const packagedTiles = [];
const updatedManifestTiles: TileRecord[] = [];

console.log("Starting flexible tile packaging pipeline...");

for (const tile of manifest.tiles) {
  const files = [];
  let totalConfidence = 0;
  let fileCount = 0;
  let hasInferredData = false;

  for (const [kind, relativePath] of Object.entries(tile.files)) {
    const absolutePath = resolveWorkspacePath(relativePath);
    if (!await pathExists(absolutePath)) {
      console.warn(`[Warning] Tile "${tile.id}" references file "${relativePath}" which does not exist on disk. Skipping.`);
      continue;
    }

    fileCount++;

    // Geometry/spatial files validation (terrain, roads, buildings, or standard mesh extensions)
    const isGeometry = ["terrain", "roads", "buildings"].includes(kind) || 
                       [".obj", ".gltf", ".glb", ".mesh", ".json"].includes(path.extname(absolutePath).toLowerCase());

    let fileProvenance: ProvenanceData;

    if (isGeometry) {
      const provenancePath = `${absolutePath}.provenance.json`;
      if (!await pathExists(provenancePath)) {
        console.warn(`[Warning] Geometry file "${relativePath}" for tile "${tile.id}" lacks a provenance sidecar. Treating as inferred.`);
        fileProvenance = {
          source: "inferred",
          confidence: 0.0,
          method: kind === "buildings" ? "extruded" : "interpolated",
          importedAt: new Date().toISOString()
        };
      } else {
        try {
          const rawProvenance = await readJsonFile<any>(provenancePath);
          if (!rawProvenance) {
            throw new Error("Empty provenance file");
          }

          // Map legacy or incomplete provenance metadata structures
          if (rawProvenance.source !== undefined) {
            fileProvenance = {
              source: rawProvenance.source,
              confidence: typeof rawProvenance.confidence === "number" ? rawProvenance.confidence : 1.0,
              method: rawProvenance.method || "direct",
              sourceId: rawProvenance.sourceId,
              importedAt: rawProvenance.importedAt || new Date().toISOString(),
              lineage: rawProvenance.lineage
            };
          } else if (typeof rawProvenance.sourceId === "string") {
            // Legacy mapping
            const sourceId = rawProvenance.sourceId;
            let source: ProvenanceData["source"] = "inferred";
            let method: ProvenanceData["method"] = "direct";
            
            if (sourceId.includes("dem")) {
              source = "dem";
            } else if (sourceId.includes("osm")) {
              source = "osm";
            } else if (sourceId.includes("imagery") || sourceId.includes("satellite")) {
              source = "imagery";
            }

            if (kind === "buildings") {
              method = "extruded";
            }

            fileProvenance = {
              source,
              confidence: 1.0,
              method,
              sourceId,
              importedAt: rawProvenance.importedAt || new Date().toISOString(),
              lineage: rawProvenance.lineage
            };
          } else {
            fileProvenance = {
              source: "inferred",
              confidence: 0.0,
              method: "heuristic",
              importedAt: new Date().toISOString()
            };
          }

          // Verify source inventory reference if provided
          if (fileProvenance.sourceId && !validSourceIds.has(fileProvenance.sourceId)) {
            console.warn(`[Warning] Provenance sourceId "${fileProvenance.sourceId}" in "${path.basename(provenancePath)}" is not listed in data/metadata/source-inventory.json.`);
          }
        } catch (err) {
          console.warn(`[Warning] Failed to validate provenance sidecar for "${relativePath}": ${(err as Error).message}. Treating as inferred.`);
          fileProvenance = {
            source: "inferred",
            confidence: 0.0,
            method: "heuristic",
            importedAt: new Date().toISOString()
          };
        }
      }
    } else {
      // Non-geometry files default provenance
      fileProvenance = {
        source: "imagery",
        confidence: 1.0,
        method: "direct",
        importedAt: new Date().toISOString()
      };
    }

    totalConfidence += fileProvenance.confidence;
    if (fileProvenance.source === "inferred" || fileProvenance.confidence < 1.0) {
      hasInferredData = true;
    }

    files.push({
      kind,
      path: path.relative(workspaceRootPath, absolutePath),
      sha256: await sha256File(absolutePath),
      provenance: fileProvenance
    });
  }

  // Calculate Data Quality Metrics for the Tile
  const expectedCount = Math.max(1, Object.keys(tile.files).length);
  const coverage = fileCount / expectedCount;
  const confidence = fileCount > 0 ? totalConfidence / fileCount : 1.0;

  const dataQuality = {
    coverage,
    confidence,
    hasInferredData: hasInferredData || fileCount < expectedCount
  };

  packagedTiles.push({
    id: tile.id,
    state: files.length > 0 ? "packaged" : tile.state,
    files
  });

  // Track data quality in tile manifest
  updatedManifestTiles.push({
    ...tile,
    dataQuality
  });
}

// In-place update of the source tile-manifest.json to persist quality metrics
await writeJsonFile(manifestPath, {
  ...manifest,
  tiles: updatedManifestTiles
});
console.log("Updated tile-manifest.json with computed data quality metrics.");

// Save final package contract
await writeJsonFile(outputPath, {
  schemaVersion: "0.1.0",
  packageId: "tecate_core_tiles",
  projectId: manifest.projectId,
  createdBy: "tools/packaging/package-tiles.ts",
  createdAt: new Date().toISOString(),
  coordinateOriginWgs84: manifest.coordinateOriginWgs84,
  tiles: packagedTiles
});

console.log(`Wrote package manifest to ${outputPath}`);
