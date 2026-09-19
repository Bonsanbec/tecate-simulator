---
name: reconstruccion-edificios-3d
description: >-
  Guía operativa y runbook paso a paso para la reconstrucción procedural de edificios
  y assets 3D en Tecate Simulator usando Blender Python headless y exportación a Godot 4.
  Activar siempre que el usuario solicite crear, modelar, rectificar o integrar un edificio,
  fachada o elemento arquitectónico en el simulador.
---

# Reconstrucción Procedural de Edificios 3D — Tecate Simulator

Esta habilidad guía al agente en la ejecución del *pipeline* estándar de 7 fases para reconstrucción de inmuebles en Tecate.

## Lectura Obligatoria Previa
Antes de generar código o ejecutar cómputo, consulta el estándar universal completo:
- [`docs/metodologia_reconstruccion_edificios.md`](../../docs/metodologia_reconstruccion_edificios.md)

## Flujo Operativo en 7 Fases

1. **Fase 1: Ingesta de Verdad de Terreno**:
   - Consultar `panoramas_cache.json` para ubicar las capturas de la manzana objetivo.
   - Transferir imágenes mediante `scp Usuario@host:... local_staging/` hacia `scratch/staging/[edificio]/`.
   - **Regla crítica**: Prohibido listar o buscar directamente en `/Volumes/tecate-backup/data/` (previene congelamiento por latencia).

2. **Fase 2: Contrato Cartesiano Canónico y Matriz de Alturas**:
   - Fijar origen $(0,0,0)$ en la esquina principal del predio a ras de suelo.
   - Definir zócalo enterrado en $Z \in [-1.20\text{ m},\, 0.00\text{ m}]$ para absorción de pendientes de banqueta.

3. **Fase 3: Script Procedural Modular (Blender Python `bpy` + `bmesh`)**:
   - Usar `add_box` para volúmenes ortogonales estándar.
   - Usar `add_oriented_box` para columnas, repisas, dinteles y marcos sobre muros curvos o en chaflán.
   - Orientar textos con su normal local $+Z$ hacia la fachada exterior para erradicar el efecto espejo.

4. **Fase 4: Validación Closed-Loop con Renders**:
   - Configurar batería de cámaras fijas (Frontal A, Frontal B, Esquina 45º, Cenital Z=48m para azotea hermética y Acercamiento Peatonal).
   - Renderizar mediante Cycles CPU en modo *headless*.
   - Inspeccionar obligatoriamente las imágenes con `view_file` antes de certificar la volumetría.

5. **Fase 5: Exportación a Godot 4**:
   - Exportar archivo `.glb` limpio (sin incluir banquetas, cordones ni asfalto).
   - Generar programáticamente la escena `.tscn` con colisionadores analíticos `BoxShape3D` transitables.

6. **Fase 6: Integración Urbana**:
   - Instanciar en `main.tscn` usando rotaciones cardinales ortogonales puras ($0^\circ, 90^\circ, 180^\circ, 270^\circ$) para preservar el paralelismo vial.

7. **Fase 7: Protocolo /grill-me**:
   - Ante ambigüedades en fachadas traseras o patios interiores sin visibilidad fotográfica, activar entrevista interactiva antes de programar geometrías especulativas.
