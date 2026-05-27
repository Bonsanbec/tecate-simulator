import { boundsIntersect, boundsToTileRange, tileBoundsWgs84, type Wgs84Bounds, type Wgs84Point } from "./geo.js";

export interface ProjectArea {
  schemaVersion: string;
  projectId: string;
  coordinateOriginWgs84: Wgs84Point & { elevationMeters: number };
  boundsWgs84: Wgs84Bounds;
  initialTileZoom: number;
  corridors: Array<{
    id: string;
    displayName: string;
    priority: number;
    boundsWgs84: Wgs84Bounds;
    status: string;
  }>;
}

export interface TileRecord {
  id: string;
  x: number;
  y: number;
  z: number;
  boundsWgs84: Wgs84Bounds;
  state: "planned" | "generated" | "packaged" | "failed";
  corridorIds: string[];
  files: Record<string, string>;
  dataQuality?: {
    coverage: number;
    confidence: number;
    hasInferredData: boolean;
  };
}

export interface TileManifest {
  schemaVersion: string;
  projectId: string;
  generatedBy: string;
  generatedAt: string;
  coordinateOriginWgs84: ProjectArea["coordinateOriginWgs84"];
  zoom: number;
  tiles: TileRecord[];
}

export function createTileId(z: number, x: number, y: number): string {
  return `tecate_core_z${z}_x${x}_y${y}`;
}

export function createTileManifest(projectArea: ProjectArea, zoom = projectArea.initialTileZoom): TileManifest {
  const range = boundsToTileRange(projectArea.boundsWgs84, zoom);
  const tiles: TileRecord[] = [];

  for (let y = range.minY; y <= range.maxY; y += 1) {
    for (let x = range.minX; x <= range.maxX; x += 1) {
      const boundsWgs84 = tileBoundsWgs84(x, y, zoom);
      const corridorIds = projectArea.corridors
        .filter((corridor) => boundsIntersect(boundsWgs84, corridor.boundsWgs84))
        .map((corridor) => corridor.id);

      tiles.push({
        id: createTileId(zoom, x, y),
        x,
        y,
        z: zoom,
        boundsWgs84,
        state: "planned",
        corridorIds,
        files: {}
      });
    }
  }

  return {
    schemaVersion: "0.1.0",
    projectId: projectArea.projectId,
    generatedBy: "tools/generators/generate-basic-chunks.ts",
    generatedAt: new Date().toISOString(),
    coordinateOriginWgs84: projectArea.coordinateOriginWgs84,
    zoom,
    tiles
  };
}

