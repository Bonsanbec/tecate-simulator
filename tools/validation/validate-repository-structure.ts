import { promises as fs } from "node:fs";
import path from "node:path";
import { resolveWorkspacePath } from "../lib/cli.js";
import { listFilesRecursive, pathExists } from "../lib/fs.js";
import { addError, failOnErrors, printIssues, type ValidationIssue } from "../lib/validation.js";

const requiredDirectories = [
  "docs/vision",
  "docs/architecture",
  "docs/gameplay",
  "docs/world",
  "docs/pipelines",
  "docs/conventions",
  "docs/state",
  "docs/references",
  "docs/roadmap",
  "tools/importers",
  "tools/converters",
  "tools/debug",
  "tools/packaging",
  "tools/validation",
  "data/raw",
  "data/gis",
  "data/terrain",
  "data/roads",
  "data/buildings",
  "data/imagery",
  "data/metadata",
  "assets/materials",
  "assets/textures",
  "assets/models",
  "assets/audio",
  "assets/vegetation",
  "generated/terrain",
  "generated/buildings",
  "generated/navigation",
  "generated/tiles",
  "generated/debug",
  "generated/packages",
  "godot/scenes",
  "godot/scripts",
  "godot/resources",
  "godot/world",
  "godot/systems",
  "godot/shaders",
  "scripts",
  "schemas"
];

const requiredFiles = [
  "README.md",
  ".gitignore",
  "package.json",
  "tsconfig.json",
  "docs/vision/project-philosophy.md",
  "docs/architecture/world-streaming.md",
  "docs/architecture/runtime-vs-toolchain.md",
  "docs/architecture/procedural-generation.md",
  "docs/conventions/naming.md",
  "docs/conventions/ai-collaboration.md",
  "docs/world/spatial-identity.md",
  "docs/pipelines/data-ingestion.md",
  "docs/state/current-world-state.md",
  "docs/gameplay/player-experience.md",
  "docs/references/tecate-corridors.md",
  "docs/roadmap/first-iteration-plan.md",
  "data/metadata/project-area.json"
];

const issues: ValidationIssue[] = [];

for (const directory of requiredDirectories) {
  const absolutePath = resolveWorkspacePath(directory);
  if (!await pathExists(absolutePath)) {
    addError(issues, "Missing required directory", directory);
  }
}

for (const file of requiredFiles) {
  const absolutePath = resolveWorkspacePath(file);
  if (!await pathExists(absolutePath)) {
    addError(issues, "Missing required file", file);
  }
}

const prohibited = ["bul", "evar"].join("");
const textExtensions = new Set([".md", ".json", ".ts", ".cs", ".csproj", ".sln", ".godot", ".tscn", ".gdshader", ".sh"]);

for (const filePath of await listFilesRecursive(resolveWorkspacePath("."))) {
  if (!textExtensions.has(path.extname(filePath))) {
    continue;
  }

  const content = await fs.readFile(filePath, "utf8");
  if (content.toLowerCase().includes(prohibited)) {
    addError(issues, "Prohibited boulevard terminology variant found", path.relative(resolveWorkspacePath("."), filePath));
  }
}

printIssues("Repository structure validation", issues);
failOnErrors(issues);

