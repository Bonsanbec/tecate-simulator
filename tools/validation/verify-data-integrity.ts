import { promises as fs } from "node:fs";
import path from "node:path";
import { resolveWorkspacePath } from "../lib/cli.js";
import { listFilesRecursive } from "../lib/fs.js";
import { addError, failOnErrors, printIssues, type ValidationIssue } from "../lib/validation.js";

const issues: ValidationIssue[] = [];
const roots = ["data", "generated", "schemas"];

for (const root of roots) {
  for (const filePath of await listFilesRecursive(resolveWorkspacePath(root))) {
    const relativePath = path.relative(resolveWorkspacePath("."), filePath);
    const stat = await fs.stat(filePath);

    if (stat.size === 0) {
      addError(issues, "Empty file is not allowed", relativePath);
      continue;
    }

    if (path.extname(filePath) === ".json") {
      try {
        JSON.parse(await fs.readFile(filePath, "utf8"));
      } catch (error) {
        addError(issues, `Invalid JSON: ${(error as Error).message}`, relativePath);
      }
    }
  }
}

printIssues("Data integrity validation", issues);
failOnErrors(issues);

