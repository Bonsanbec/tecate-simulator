import path from "node:path";
import { fileURLToPath } from "node:url";

export type CliArgs = Record<string, string | boolean>;

export function parseArgs(argv = process.argv.slice(2)): CliArgs {
  const args: CliArgs = {};

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token?.startsWith("--")) {
      continue;
    }

    const key = token.slice(2);
    const next = argv[index + 1];

    if (next === undefined || next.startsWith("--")) {
      args[key] = true;
      continue;
    }

    args[key] = next;
    index += 1;
  }

  return args;
}

export function workspaceRoot(): string {
  return path.resolve(fileURLToPath(new URL("../..", import.meta.url)));
}

export function resolveWorkspacePath(inputPath: string): string {
  return path.isAbsolute(inputPath)
    ? inputPath
    : path.resolve(workspaceRoot(), inputPath);
}

export function getStringArg(args: CliArgs, name: string, fallback?: string): string {
  const value = args[name];
  if (typeof value === "string" && value.length > 0) {
    return value;
  }

  if (fallback !== undefined) {
    return fallback;
  }

  throw new Error(`Missing required argument --${name}`);
}

export function getNumberArg(args: CliArgs, name: string, fallback?: number): number {
  const value = args[name];

  if (typeof value === "string") {
    const numericValue = Number(value);
    if (Number.isFinite(numericValue)) {
      return numericValue;
    }
    throw new Error(`Argument --${name} must be a finite number`);
  }

  if (fallback !== undefined) {
    return fallback;
  }

  throw new Error(`Missing required numeric argument --${name}`);
}

