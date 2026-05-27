# Tecate Walking Simulator

## Contexto

Simulador peatonal de memoria espacial convincente de Tecate, Baja California entre 2000–2010.

Prioridades:
- continuidad espacial,
- relieve correcto,
- landmarks reales,
- coherencia urbana,
- runtime ligero,
- datos derivados de fuentes reales.

La proceduralidad solo rellena huecos secundarios.

## Restricciones críticas

- Preservar coherencia geoespacial del Cerro Cuchumá.
- Runtime ligero.
- Procesamiento pesado únicamente offline.
- Mantener soporte futuro para interiores explorables.
- Mantener identificadores estables.
- Mantener coherencia terminológica.

## Documentos obligatorios

Leer antes de modificar:
- /docs/vision/project-philosophy.md
- /docs/architecture/world-streaming.md
- /docs/architecture/runtime-vs-toolchain.md
- /docs/conventions/naming.md
- /docs/state/current-world-state.md

## Política de iteración

Objetivo:
Llegar al primer ejecutable MVP funcional.

El MVP debe incluir:
- terreno,
- navegación,
- tile streaming,
- boulevard Juárez parcial,
- edificios básicos,
- iluminación diurna,
- silueta correcta del Cerro Cuchumá,
- carga offline de datos.

Flujo obligatorio:
1. leer documentación,
2. identificar siguiente milestone mínimo,
3. implementar incrementalmente,
4. compilar,
5. validar,
6. actualizar estado del proyecto.

Nunca:
- renombrar sistemas arbitrariamente,
- introducir arquitectura innecesaria,
- modificar demasiados sistemas simultáneamente,
- romper compilación,
- introducir placeholders vacíos.