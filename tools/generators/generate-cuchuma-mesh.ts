import { promises as fs } from "node:fs";
import path from "node:path";
import { resolveWorkspacePath } from "../lib/cli.js";
import { pathExists } from "../lib/fs.js";

async function main() {
  const worldDir = resolveWorkspacePath("godot/world");
  if (!await pathExists(worldDir)) {
    await fs.mkdir(worldDir, { recursive: true });
  }

  // True geographic offsets relative to the origin coordinate (32.5668°N, -116.6253°W, 540m)
  const peakX = -5972.0; // 6 km west
  const peakZ = -1414.0; // 1.4 km north
  const peakY = 900.0;   // Height exaggerated to 900m to match human eye's perceptual scale down corridors
  const radius = 4000.0;  // Spans a massive 4 km radius

  const gridResolution = 64; // 65x65 grid for smoother ridgelines and fewer visual artifacts
  const stride = gridResolution + 1;
  const totalVertices = stride * stride;

  // Phase 1: Generate vertex positions
  const positions: { x: number; y: number; z: number }[] = [];

  for (let gz = 0; gz <= gridResolution; gz += 1) {
    const z = peakZ - radius + (gz / gridResolution) * (2 * radius);
    for (let gx = 0; gx <= gridResolution; gx += 1) {
      const x = peakX - radius + (gx / gridResolution) * (2 * radius);

      const dx = x - peakX;
      const dz = z - peakZ;
      const dist = Math.sqrt(dx * dx + dz * dz);

      // A. East-West Geological Ridge Line Core Profile
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

      positions.push({ x, y, z });
    }
  }

  // Phase 2: Compute per-vertex normals by averaging adjacent face normals
  const normals: { x: number; y: number; z: number }[] = new Array(totalVertices).fill(null).map(() => ({ x: 0, y: 0, z: 0 }));

  function cross(ax: number, ay: number, az: number, bx: number, by: number, bz: number) {
    return { x: ay * bz - az * by, y: az * bx - ax * bz, z: ax * by - ay * bx };
  }

  for (let gz = 0; gz < gridResolution; gz += 1) {
    for (let gx = 0; gx < gridResolution; gx += 1) {
      const i0 = gz * stride + gx;
      const i1 = gz * stride + (gx + 1);
      const i2 = (gz + 1) * stride + (gx + 1);
      const i3 = (gz + 1) * stride + gx;

      const p0 = positions[i0]!;
      const p1 = positions[i1]!;
      const p2 = positions[i2]!;
      const p3 = positions[i3]!;

      // Triangle 1: i0, i1, i2 (CCW from above → normal points UP)
      const e1x = p1.x - p0.x, e1y = p1.y - p0.y, e1z = p1.z - p0.z;
      const e2x = p2.x - p0.x, e2y = p2.y - p0.y, e2z = p2.z - p0.z;
      const n1 = cross(e1x, e1y, e1z, e2x, e2y, e2z);

      // Triangle 2: i0, i2, i3 (CCW from above → normal points UP)
      const e3x = p2.x - p0.x, e3y = p2.y - p0.y, e3z = p2.z - p0.z;
      const e4x = p3.x - p0.x, e4y = p3.y - p0.y, e4z = p3.z - p0.z;
      const n2 = cross(e3x, e3y, e3z, e4x, e4y, e4z);

      // Accumulate face normals to each vertex
      for (const idx of [i0, i1, i2]) {
        normals[idx]!.x += n1.x;
        normals[idx]!.y += n1.y;
        normals[idx]!.z += n1.z;
      }
      for (const idx of [i0, i2, i3]) {
        normals[idx]!.x += n2.x;
        normals[idx]!.y += n2.y;
        normals[idx]!.z += n2.z;
      }
    }
  }

  // Normalize all normals
  for (const n of normals) {
    const len = Math.sqrt(n.x * n.x + n.y * n.y + n.z * n.z);
    if (len > 0.0001) {
      n.x /= len;
      n.y /= len;
      n.z /= len;
    } else {
      n.x = 0;
      n.y = 1;
      n.z = 0;
    }
  }

  // Phase 3: Build OBJ with vertex positions, normals, and corrected face winding
  let obj = `# Montaña Cuchumá (Kuuchamaa Mountain) Regional Horizon Landmark Mesh\n`;
  obj += `# Generated with explicit normals and consistent CCW face winding\n`;
  obj += `# Grid: ${stride}x${stride} = ${totalVertices} vertices\n\n`;

  // Vertices
  for (const p of positions) {
    obj += `v ${p.x.toFixed(3)} ${p.y.toFixed(3)} ${p.z.toFixed(3)}\n`;
  }

  obj += `\n`;

  // Vertex normals
  for (const n of normals) {
    obj += `vn ${n.x.toFixed(4)} ${n.y.toFixed(4)} ${n.z.toFixed(4)}\n`;
  }

  obj += `\n`;

  // Faces with consistent CCW winding (normal points UP/outward)
  // Using v//vn format since we have normals but no UVs
  for (let gz = 0; gz < gridResolution; gz += 1) {
    for (let gx = 0; gx < gridResolution; gx += 1) {
      // OBJ is 1-indexed
      const idx0 = gz * stride + gx + 1;
      const idx1 = gz * stride + (gx + 1) + 1;
      const idx2 = (gz + 1) * stride + (gx + 1) + 1;
      const idx3 = (gz + 1) * stride + gx + 1;

      // Triangle 1: i0 → i1 → i2 (CCW from above)
      obj += `f ${idx0}//${idx0} ${idx1}//${idx1} ${idx2}//${idx2}\n`;
      // Triangle 2: i0 → i2 → i3 (CCW from above) — FIXED from i2→i3→i0
      obj += `f ${idx0}//${idx0} ${idx2}//${idx2} ${idx3}//${idx3}\n`;
    }
  }

  // Phase 4: Generate skirt (a ring of vertices at elevation 0 connecting to the perimeter)
  // This prevents the mountain from appearing to "float" above the terrain
  obj += `\n# Skirt geometry to anchor mountain to ground plane\n`;

  const skirtBaseY = -5.0; // Slightly below ground to ensure seamless connection
  let skirtVertStart = totalVertices + 1; // OBJ 1-indexed
  const perimeterIndices: number[] = [];

  // Collect perimeter vertex indices (top row, bottom row, left col, right col)
  // Top row (gz=0)
  for (let gx = 0; gx <= gridResolution; gx += 1) {
    perimeterIndices.push(gx); // 0-indexed
  }
  // Right column (gx=gridResolution), skip first (already added)
  for (let gz = 1; gz <= gridResolution; gz += 1) {
    perimeterIndices.push(gz * stride + gridResolution);
  }
  // Bottom row (gz=gridResolution), right to left, skip first (already added)
  for (let gx = gridResolution - 1; gx >= 0; gx -= 1) {
    perimeterIndices.push(gridResolution * stride + gx);
  }
  // Left column (gx=0), bottom to top, skip first and last (already added)
  for (let gz = gridResolution - 1; gz >= 1; gz -= 1) {
    perimeterIndices.push(gz * stride);
  }

  // Emit skirt vertices (at ground level, same XZ as perimeter vertices)
  for (const pIdx of perimeterIndices) {
    const p = positions[pIdx]!;
    obj += `v ${p.x.toFixed(3)} ${skirtBaseY.toFixed(3)} ${p.z.toFixed(3)}\n`;
  }

  // Emit skirt normals (pointing outward horizontally — approximate)
  for (const pIdx of perimeterIndices) {
    const p = positions[pIdx]!;
    const dx = p.x - peakX;
    const dz = p.z - peakZ;
    const len = Math.sqrt(dx * dx + dz * dz);
    if (len > 0.01) {
      obj += `vn ${(dx / len).toFixed(4)} 0.0000 ${(dz / len).toFixed(4)}\n`;
    } else {
      obj += `vn 0.0000 -1.0000 0.0000\n`;
    }
  }

  // Emit skirt faces connecting perimeter to ground ring
  const numPerimeter = perimeterIndices.length;
  const skirtNormalStart = totalVertices + 1; // 1-indexed in the normal array

  for (let i = 0; i < numPerimeter; i += 1) {
    const nextI = (i + 1) % numPerimeter;

    // Upper vertices (on the mountain surface) — 1-indexed
    const upper0 = perimeterIndices[i]! + 1;
    const upper1 = perimeterIndices[nextI]! + 1;

    // Lower vertices (skirt at ground) — 1-indexed
    const lower0 = skirtVertStart + i;
    const lower1 = skirtVertStart + nextI;

    // Skirt normal indices
    const sn0 = skirtNormalStart + i;
    const sn1 = skirtNormalStart + nextI;

    // Two triangles forming a quad, both facing outward
    obj += `f ${upper0}//${sn0} ${lower0}//${sn0} ${lower1}//${sn1}\n`;
    obj += `f ${lower1}//${sn1} ${upper1}//${sn1} ${upper0}//${sn0}\n`;
  }

  const outputPath = path.join(worldDir, "landmark_montana_cuchuma.obj");
  await fs.writeFile(outputPath, obj, "utf8");
  console.log(`Successfully generated Cerro Cuchumá landmark mesh at ${outputPath}`);
  console.log(`  Grid: ${stride}×${stride} = ${totalVertices} vertices`);
  console.log(`  Perimeter skirt: ${numPerimeter} vertices`);
  console.log(`  Total vertices: ${totalVertices + numPerimeter}`);
}

main().catch((err) => {
  console.error("Cuchumá mesh generation failed:", err);
  process.exit(1);
});
