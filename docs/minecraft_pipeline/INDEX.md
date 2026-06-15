# Documentación Técnica: Minecraft Pipeline

> **Fuente de verdad:** Derivado exclusivamente del código en `src/minecraft_pipeline/`.  
> **Fecha de análisis:** Junio 2026.

---

## Documentos en esta suite

| Archivo | Contenido |
|---------|-----------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Arquitectura general, módulos, dependencias y puntos de entrada |
| [SPATIAL_MODEL.md](./SPATIAL_MODEL.md) | Sistemas de coordenadas, transformaciones cartográficas y geométricas |
| [PIPELINE_EXPORT.md](./PIPELINE_EXPORT.md) | Pipeline completo de exportación: de JSON geográfico a mundo Minecraft |
| [PIPELINE_IMPORT.md](./PIPELINE_IMPORT.md) | Pipeline de importación: de mundo Minecraft editado a modelo 3D |
| [BLOCK_SEMANTICS.md](./BLOCK_SEMANTICS.md) | Significado geográfico de cada bloque Minecraft colocado |
| [FORMATS.md](./FORMATS.md) | Formatos de entrada/salida, estructuras de datos |
| [EXTENSIONS.md](./EXTENSIONS.md) | Guía para extender, importar, exportar y usar el mundo como SIG |

---

## Lectura recomendada

Para comprender el sistema completo, leer en este orden:

1. **ARCHITECTURE.md** — qué hace cada módulo y cómo se conectan
2. **SPATIAL_MODEL.md** — cómo se proyectan coordenadas geográficas a Minecraft
3. **PIPELINE_EXPORT.md** — el flujo completo de generación
4. **BLOCK_SEMANTICS.md** — qué significa cada bloque en términos geográficos
5. **PIPELINE_IMPORT.md** — cómo extraer información del mundo editado
6. **FORMATS.md** — referencia de estructuras de datos
7. **EXTENSIONS.md** — cómo extender el sistema

---

## Resumen ejecutivo

El Minecraft Pipeline transforma información geográfica de Tecate, B.C., México en un mundo Minecraft 1.20+ habitable y editable. El proceso consiste en:

1. Leer la geometría urbana reconstruida (`reconstruction_export.json`) y el modelo de terreno 3D (`tecate.glb`).
2. Proyectar coordenadas GPS → Cartesianas locales → Minecraft usando una transformación lineal calibrada.
3. Rasterizar calles, manzanas y cuerpos de agua en bloques individuales (1 bloque = ~1 m²).
4. Generar el relieve del terreno interpolando vértices del TIN del GLB.
5. Escribir archivos `.mca` (formato de región Minecraft) con la estructura NBT correcta.
6. Opcionalmente, volver a importar ediciones del jugador como diferencial geoespacial.

El mundo resultante es una representación espacialmente coherente de Tecate donde **cada bloque tiene un significado geográfico determinístico y reversible**.
