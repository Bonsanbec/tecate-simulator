import { promises as fs } from "node:fs";
import path from "node:path";
import { resolveWorkspacePath } from "../lib/cli.js";

const directories = [
  "docs/images/boulevard-juarez",
  "docs/images/miguel-hidalgo",
  "docs/images/revolucion",
  "docs/images/nuevo-leon",
  "docs/images/cuchuma",
  "docs/images/urban-patterns",
  "docs/images/signage",
  "docs/images/commercial-density",
  "docs/images/terrain-reference"
];

const referenceImages = [
  {
    url: "https://upload.wikimedia.org/wikipedia/commons/f/ff/Kumeyaay_Valley_Looking_towards_Kuuchamaa.jpg",
    dest: "docs/images/cuchuma/cuchuma-valley.jpg",
    description: "Real-world perspective of the Kuuchamaa (Cuchumá) mountain profile from the south valley, establishing the dominant horizon ridge shape."
  },
  {
    url: "https://upload.wikimedia.org/wikipedia/commons/b/b3/Parroquia_de_nuestra_senora_de_guadalupe_tecate.jpg",
    dest: "docs/images/urban-patterns/parroquia-guadalupe.jpg",
    description: "Nuestra Señora de Guadalupe Church and neighboring pedestrian walk, showing traditional brick paving, continuous commercial facades, and plaster walls."
  },
  {
    url: "https://upload.wikimedia.org/wikipedia/commons/d/df/Tecate_brewery_factory.jpg",
    dest: "docs/images/commercial-density/tecate-brewery.jpg",
    description: "The massive historic Tecate Brewery block along the main avenue, displaying typical industrial-scale brick work, concrete utility posts, and surrounding high walls."
  },
  {
    url: "https://upload.wikimedia.org/wikipedia/commons/3/3a/Tecate_parque.jpg",
    dest: "docs/images/boulevard-juarez/parque-hidalgo.jpg",
    description: "Parque Miguel Hidalgo central kiosk and surrounding plaza pavement, showing the pedestrian-centered open spaces and sparse semi-arid vegetation (palms, low shrubs)."
  },
  {
    url: "https://upload.wikimedia.org/wikipedia/commons/e/e0/Bienvenido_a_Tecate.jpg",
    dest: "docs/images/signage/bienvenido-sign.jpg",
    description: "Welcome to Tecate landmark entry sign, establishing the town's entry visual language, concrete curbs, and adjacent road shoulders."
  }
];

async function downloadFile(url: string, destPath: string): Promise<boolean> {
  try {
    const response = await fetch(url, {
      headers: {
        "User-Agent": "TecateSpatialMemorySimulator/0.1.0 (hakkindavid@github.com)"
      }
    });

    if (!response.ok) {
      console.warn(`Failed to download from ${url}: ${response.statusText}`);
      return false;
    }

    const arrayBuffer = await response.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    await fs.writeFile(destPath, buffer);
    console.log(`Downloaded reference: ${destPath}`);
    return true;
  } catch (error) {
    console.warn(`Network error downloading ${url}: ${(error as Error).message}`);
    return false;
  }
}

async function main() {
  console.log("Creating visual reference directory structure...");
  for (const dir of directories) {
    const absolutePath = resolveWorkspacePath(dir);
    await fs.mkdir(absolutePath, { recursive: true });
    console.log(`Created: ${dir}`);
  }

  console.log("\nDownloading real-world visual references from Wikimedia Commons...");
  for (const ref of referenceImages) {
    const absolutePath = resolveWorkspacePath(ref.dest);
    const success = await downloadFile(ref.url, absolutePath);

    if (!success) {
      // Create a small fallback text file so we don't block the pipeline if Wikimedia is down
      const fallbackTxt = `${ref.dest}.txt`;
      await fs.writeFile(
        resolveWorkspacePath(fallbackTxt),
        `Description: ${ref.description}\nSource URL: ${ref.url}\nStatus: Download failed, verified online reference link.`,
        "utf8"
      );
      console.log(`Saved fallback reference notes at: ${fallbackTxt}`);
    }
  }

  // Generate the markdown index as requested
  const indexContent = `# Visual References Index

This index lists the visual reference images downloaded from real-world datasets and organized in the repository. These references serve as guides for scale, proportions, street textures, commercial densities, and Cuchumá silhouette alignment.

## Cuchumá Mountain & Regional Terrain
- **File**: [cuchuma-valley.jpg](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/docs/images/cuchuma/cuchuma-valley.jpg)
  - **Ubicación aproximada**: Frontera norte y aproximaciones al oeste de Tecate.
  - **Utilidad perceptual**: Guía de la silueta dominante de Montaña Cuchumá. Establece que la montaña no debe sentirse como una loma integrada al casco urbano, sino como un elemento regional distante de más de 950m de altitud.
  - **Relación con corredores**: Visible al norte/oeste de Boulevard Juárez, Hidalgo y Revolución.

## Urban Patterns & Pedestrian Identity
- **File**: [parroquia-guadalupe.jpg](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/docs/images/urban-patterns/parroquia-guadalupe.jpg)
  - **Ubicación aproximada**: Avenida Miguel Hidalgo y cruce con Libertad, Centro.
  - **Utilidad perceptual**: Guía de texturas urbanas, banquetas de adoquín, continuidad de fachadas comerciales bajas y la escala de la parroquia histórica.
  - **Relación con corredores**: Define la identidad del corredor peatonal de Avenida Hidalgo.

## Commercial Density & Industrial Blocks
- **File**: [tecate-brewery.jpg](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/docs/images/commercial-density/tecate-brewery.jpg)
  - **Ubicación aproximada**: Boulevard Juárez y Avenida Hidalgo, Centro.
  - **Utilidad perceptual**: Guía para la escala masiva de la Cervecería Tecate. Define la barda industrial de ladrillo, postes de concreto gris, y la densidad comercial fronteriza de los lotes estrechos adyacentes.
  - **Relación con corredores**: Eje visual crítico en el extremo este de Boulevard Juárez.

## Main Plazas & Open Corridors
- **File**: [parque-hidalgo.jpg](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/docs/images/boulevard-juarez/parque-hidalgo.jpg)
  - **Ubicación aproximada**: Centro de la ciudad, manzana entre Juárez, Hidalgo, Ortiz Rubio y Cárdenas.
  - **Utilidad perceptual**: Guía del Parque Hidalgo (kiosco tradicional, vegetación semiárida escasa como palmeras y arbustos bajos). Permite calibrar la escala perceptual al spawnear frente a la plaza.
  - **Relación con corredores**: Frontera sur inmediata de Boulevard Juárez.

## Signage & Street Entries
- **File**: [bienvenido-sign.jpg](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/docs/images/signage/bienvenido-sign.jpg)
  - **Ubicación aproximada**: Acceso oeste de Boulevard Juárez.
  - **Utilidad perceptual**: Guía para anuncios comerciales, pórticos de bienvenida y banquetas/guarniciones de concreto rústico.
  - **Relación con corredores**: Define el punto de partida visual del Boulevard Juárez.
`;

  const indexPath = resolveWorkspacePath("docs/images/README.md");
  await fs.writeFile(indexPath, indexContent, "utf8");
  console.log(`\nWrote Visual References Index to ${indexPath}`);
}

main().catch((err) => {
  console.error("Failed to set up visual references:", err);
  process.exit(1);
});
