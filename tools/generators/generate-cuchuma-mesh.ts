import { promises as fs } from "node:fs";
import path from "node:path";
import { resolveWorkspacePath } from "../lib/cli.js";
import { pathExists } from "../lib/fs.js";

async function main() {
  const worldDir = resolveWorkspacePath("godot/world");
  if (!await pathExists(worldDir)) {
    await fs.mkdir(worldDir, { recursive: true });
  }

  // True geographic offsets relative to the origin coordinate
  const peakX = -5972.0; // 6 km west
  const peakZ = -1414.0; // 1.4 km north
  const peakY = 900.0;   // Height exaggerated to 900m to match human eye's perceptual scale down corridors
  const radius = 4000.0;  // Spans a massive 4 km radius

  const gridResolution = 49; // 50x50 grid (2,500 vertices) for detailed ridgelines
  let obj = `# Montaña Cuchumá (Kuuchamaa Mountain) Regional Horizon Landmark Mesh\n`;

  // Vertices
  for (let gz = 0; gz <= gridResolution; gz += 1) {
    const z = peakZ - radius + (gz / gridResolution) * (2 * radius);
    for (let gx = 0; gx <= gridResolution; gx += 1) {
      const x = peakX - radius + (gx / gridResolution) * (2 * radius);

      const dx = x - peakX;
      const dz = z - peakZ;
      const dist = Math.sqrt(dx * dx + dz * dz);

      // A. East-West Geological Ridge Line Core Profile
      const ridgeLength = 3000.0;
      // Distance along E-W ridge (-1.0 to 1.0)
      const tRidge = Math.max(-1.0, Math.min(1.0, (x - peakX) / 2000.0));
      const ridgeX = peakX + tRidge * 2000.0;

      // Ridge elevation profile: peaks at main summit, drops to western twin sub-peak (shoulder)
      let ridgeElev = peakY;
      if (tRidge < 0) {
        // Western flank: includes a prominent sub-peak (shoulder) representing Kuuchamaa's iconic twin peak shape
        const shoulderFactor = 0.88 + 0.12 * Math.sin(tRidge * Math.PI * 2.0);
        ridgeElev = peakY * (1.0 - Math.abs(tRidge) * 0.35) * shoulderFactor;
      } else {
        // Eastern flank: drops off more rapidly towards the border valley
        ridgeElev = peakY * (1.0 - tRidge * 0.55);
      }

      // Distance to the E-W ridge axis
      const distToRidge = Math.sqrt((x - ridgeX) * (x - ridgeX) + (z - peakZ) * (z - peakZ));
      let y = ridgeElev * Math.exp(-(distToRidge * distToRidge) / (2 * 1200 * 1200));

      // B. Layered noise to generate realistic rocky ridges, crevices, and steep slopes
      const noise1 = Math.sin(x * 0.005) * Math.cos(z * 0.005) * 80;
      const noise2 = Math.sin(x * 0.015) * Math.cos(z * 0.01) * 30;
      const detail = Math.cos(x * 0.03) * Math.sin(z * 0.03) * 10;
      
      const mountainNoise = (noise1 + noise2 + detail) * Math.exp(-(distToRidge * distToRidge) / (2 * 1600 * 1600));
      y += mountainNoise;

      // C. Soft fadeout to local valley floor (0.0 relative to 540m origin)
      if (dist > radius - 600) {
        const factor = (radius - dist) / 600;
        y *= Math.max(0, factor);
      }
      y = Math.max(0.0, y);

      obj += `v ${x.toFixed(3)} ${y.toFixed(3)} ${z.toFixed(3)}\n`;
    }
  }

  // Faces (1-indexed)
  const stride = gridResolution + 1;
  for (let gz = 0; gz < gridResolution; gz += 1) {
    for (let gx = 0; gx < gridResolution; gx += 1) {
      const idx0 = gz * stride + gx + 1;
      const idx1 = gz * stride + (gx + 1) + 1;
      const idx2 = (gz + 1) * stride + (gx + 1) + 1;
      const idx3 = (gz + 1) * stride + gx + 1;

      // Triangulate grid quads
      obj += `f ${idx0} ${idx1} ${idx2}\n`;
      obj += `f ${idx2} ${idx3} ${idx0}\n`;
    }
  }

  const outputPath = path.join(worldDir, "landmark_montana_cuchuma.obj");
  await fs.writeFile(outputPath, obj, "utf8");
  console.log(`Successfully generated Cerro Cuchumá landmark mesh at ${outputPath}`);
}

main().catch((err) => {
  console.error("Cuchumá mesh generation failed:", err);
  process.exit(1);
});
