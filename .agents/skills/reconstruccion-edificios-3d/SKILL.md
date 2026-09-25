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
   - Definir zócalo enterrado continuo en $Z \in [-1.50\text{ m},\, 0.00\text{ m}]$ ($Z \le -1.20\text{ m}$) para absorción de pendientes de banqueta.
   - Para cubiertas a cuatro aguas (hip roof), calcular previamente las cotas de cumbrera y las ecuaciones de las limaoyas diagonales para remates herméticos.

3. **Fase 3: Script Procedural Modular (Blender Python `bpy` + `bmesh`)**:
   - Usar `add_box` para volúmenes ortogonales estándar.
   - Usar `add_oriented_box` para columnas, repisas, dinteles y marcos sobre muros curvos o en chaflán.
   - **Cubiertas y Tejas**: En techos inclinados a cuatro aguas, usar `add_sloped_roof_hip_end` para los testeros y recortar analíticamente las hiladas de teja (`add_teja_ribs`) contra la limaoya diagonal ($x_{\text{ridge}} = x_{\text{eave}} + \Delta y$) para erradicar tejas o canes que vuelen en el aire.
   - **Shaders PBR Calibrados**: Desacoplar el canal de albedo (`use_tex_albedo=False`) cuando las texturas existentes contengan tintes cromáticos discordantes con la época histórica, preservando los mapas de normales y rugosidad para el relieve superficial.
   - **Porches y Accesos**: Modelar vanos de paso diáfanos con su carpintería y puertas interiores visibles al fondo; prohibido sellar accesos peatonales con cajas sólidas.
   - Orientar textos con su normal local $+Z$ hacia la fachada exterior para erradicar el efecto espejo.

4. **Fase 4: Validación Closed-Loop con Renders**:
   - Configurar batería perimetral completa de 8 cámaras técnicas diurnas:
     1. Frontal Perspectiva Extremo Norte (45°).
     2. Frontal Centro (ortogonal a media distancia).
     3. Frontal Perspectiva Extremo Sur (45°).
     4. Fachada Lateral Norte / Callejón.
     5. Fachada Lateral Sur / Avenida.
     6. Volúmenes Adosados / Restaurantes / Patios.
     7. Fachada Posterior / Estacionamiento.
     8. Vista Cenital Superior ($Z \ge 60\text{ m}$) para certificar hermeticidad de cubiertas y azoteas.
   - Renderizar mediante Cycles CPU en modo *headless*.
   - Inspeccionar obligatoriamente las imágenes con `view_file` antes de certificar la volumetría.

5. **Fase 5: Exportación a Godot 4**:
   - Exportar archivo `.glb` limpio (sin incluir banquetas, cordones ni asfalto).
   - Generar programáticamente la escena `.tscn` con colisionadores analíticos `BoxShape3D` transitables, invirtiendo obligatoriamente el eje de profundidad ($Z_{\text{godot}} = -Y_{\text{blender}}$).

6. **Fase 6: Integración Urbana**:
   - Instanciar en `main.tscn` heredando la matriz de rotación e inclinación topográfica (`Transform3D`) calibrada del corredor vial correspondiente (ej. Lázaro Cárdenas, Juárez, Hidalgo) para asegurar continuidad milimétrica entre manzanas colindantes.

7. **Fase 7: Protocolo /grill-me**:
   - Ante ambigüedades en fachadas traseras o patios interiores sin visibilidad fotográfica, activar entrevista interactiva antes de programar geometrías especulativas.

---

## Plantilla Paramétrica Canónica de Solicitud de Reconstrucción 3D

Copia y parametriza esta plantilla estándar para solicitar la reconstrucción fidedigna de cualquier inmueble o complejo en Tecate Simulator:

```markdown
El edificio o complejo a reconstruir como asset 3D se ubica aproximadamente en:
- **Inmueble / Denominación**: ${NOMBRE_INMUEBLE_O_COMPLEJO}
- **Dirección**: ${DIRECCION_COMPLETA} (${CALLE}, ${NUMERO}, ${COLONIA}, ${CODIGO_POSTAL}, Tecate, B.C., México).
- **Coordenadas GPS**: ${LATITUD}, ${LONGITUD}.
- **Época Histórica**: ${ANIO_EPOCA} (ej. 2009).

**Instrucciones Operativas y Límites de Alcance**:
1. **Identificación y Verdad de Terreno**:
   - Ubica los panoramas que escanearon su manzana identificándola en el caché local (`blocks_cache.json`, `panoramas_cache.json`).
   - Descarga imágenes exclusivamente mediante transferencia SCP directa a `scratch/staging/${CARPETA_EDIFICIO}/`. Prohibido listar el servidor remoto.
   - Elimina cualquier ambigüedad visual mediante triangulación cruzada (*cross-referencing*) de panoramas.

2. **Morfología y Programa Arquitectónico**:
   - Tipología: [CONTINUO COMERCIAL / VOLUMEN EXENTO / INMUEBLE EN ESQUINA].
   - Frente principal: Delimitado desde ${LIMITE_EXTREMO_A} (colindando con ${CALLE_COLINDANCIA_A}) hasta ${LIMITE_EXTREMO_B} (colindando con ${CALLE_COLINDANCIA_B}).
   - Ritmo de fachada: ${NUM_MODULOS_O_ARCOS} crujías/arcos frontales con sus ${NUM_SOPORTES} pilastras/columnas de [MATERIAL_SOPORTES].
   - Fachadas laterales y testeros: ${DETALLE_TESTERO_1} y ${DETALLE_TESTERO_2}.
   - Niveles y terrazas: ${DESCRIPCION_NIVELES_Y_BALCONES}.
   - Cancelerías y locales comerciales: Vitrinas retranqueadas con rotulación y tipografía 3D de la época (${LISTADO_LOCALES_O_DEPENDENCIAS}).

3. **Volúmenes Secundarios y Áreas Exteriores**:
   - Incluye ${VOLUMEN_SECUNDARIO_O_RESTAURANTE} en el scope a completo detalle artesanal (volumetría, espadaña/coronamiento, porche ochavado/zaguán de acceso diáfano, carpintería rústica, rejería y azotea técnica).
   - Incluye todos los lados visibles del edificio, auxiliándote del caché para ver los laterales y el reverso, así como todo su [ESTACIONAMIENTO / PATIO DE SERVICIO] accesible desde ${CALLE_ACCESO}.

4. **Restricciones Normativas y Calidad de Producción**:
   - No se aceptarán trabajos mediocres ni pruebas de concepto. El asset final debe mantenerse fotorrealista.
   - Prohibición de banquetas embebidas en el `.glb` (pertenecen a capas GIS).
   - Zócalo basal enterrado continuo a $Z \le -1.20\text{ m}$ para absorber la topografía de las calles sin flotar.
   - Colisiones analíticas descompuestas (`BoxShape3D`) con inversión canónica glTF ($Z_{\text{godot}} = -Y_{\text{blender}}$).
   - Validación closed-loop mediante batería perimetral de 8 cámaras en Cycles CPU inspeccionadas con `view_file`.
   - /plan previo obligatorio antes de codificar en Python.
```
