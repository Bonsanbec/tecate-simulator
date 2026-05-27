import { resolveWorkspacePath } from "../lib/cli.js";
import { readJsonFile } from "../lib/fs.js";
import { addError, failOnErrors, printIssues, type ValidationIssue } from "../lib/validation.js";
import type { ProjectArea } from "../lib/tile.js";

const issues: ValidationIssue[] = [];
const metadataPath = resolveWorkspacePath("data/metadata/project-area.json");
const projectArea = await readJsonFile<ProjectArea & { targetEra?: { startYear: number; endYear: number }; regionalLandmarks?: Array<{ id: string }> }>(metadataPath);

if (projectArea.projectId !== "tecate_spatial_memory") {
  addError(issues, "projectId must be tecate_spatial_memory", "data/metadata/project-area.json");
}

if (projectArea.targetEra?.startYear !== 2000 || projectArea.targetEra.endYear !== 2010) {
  addError(issues, "targetEra must be 2000-2010", "data/metadata/project-area.json");
}

const requiredCorridors = new Set([
  "road_boulevard_juarez",
  "road_avenida_revolucion",
  "road_avenida_miguel_hidalgo",
  "road_avenida_nuevo_leon"
]);

const corridorIds = new Set(projectArea.corridors.map((corridor) => corridor.id));
for (const corridorId of requiredCorridors) {
  if (!corridorIds.has(corridorId)) {
    addError(issues, `Missing required corridor ${corridorId}`, "data/metadata/project-area.json");
  }
}

for (const corridor of projectArea.corridors) {
  if (!corridor.displayName.includes("avenida") && !corridor.displayName.includes("boulevard")) {
    addError(issues, `Corridor displayName must use canonical road terminology: ${corridor.displayName}`, "data/metadata/project-area.json");
  }

  if (corridor.boundsWgs84.west >= corridor.boundsWgs84.east || corridor.boundsWgs84.south >= corridor.boundsWgs84.north) {
    addError(issues, `Invalid bounds for ${corridor.id}`, "data/metadata/project-area.json");
  }
}

if (!projectArea.regionalLandmarks?.some((landmark) => landmark.id === "landmark_montana_cuchuma")) {
  addError(issues, "Missing protected regional landmark landmark_montana_cuchuma", "data/metadata/project-area.json");
}

printIssues("Metadata validation", issues);
failOnErrors(issues);

