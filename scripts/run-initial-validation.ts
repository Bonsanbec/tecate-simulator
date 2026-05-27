import { spawnSync } from "node:child_process";

const commands = [
  ["npm", ["run", "structure:validate"]],
  ["npm", ["run", "metadata:validate"]],
  ["npm", ["run", "data:integrity"]],
  ["npm", ["run", "tiles:validate"]]
] as const;

for (const [command, args] of commands) {
  const result = spawnSync(command, args, { stdio: "inherit" });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

