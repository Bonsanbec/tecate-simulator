# Reglas del Proyecto: Tecate Simulator

## Protocolo Obligatorio para Modelado y Reconstrucción de Assets 3D

Siempre que se te solicite crear, modificar, auditar o integrar un modelo 3D, edificio, fachada, elemento urbano o escena arquitectónica (Blender, Python `bpy`, archivos `.glb`, `.tscn` o mallas de colisión), DEBES cumplir estrictamente las siguientes reglas:

1. **Consulta Previa Obligatoria de Documentación**:
   - Antes de escribir cualquier script generador o modificar geometría, DEBES leer con `view_file` el documento maestro:
     [`docs/metodologia_reconstruccion_edificios.md`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/docs/metodologia_reconstruccion_edificios.md)
   - Si la tarea involucra mobiliario o activos históricos específicos, consulta también:
     [`docs/APRENDIZAJES_Y_PLANTILLA_ASSETS_ARQUITECTONICOS.md`](file:///Users/hakkindavid/Documents/GitHub/tecate-simulator/docs/APRENDIZAJES_Y_PLANTILLA_ASSETS_ARQUITECTONICOS.md)

2. **Protocolo SCP Anti-Congelamiento (Infraestructura Remota)**:
   - NUNCA listes, explores ni abras en tiempo de ejecución rutas dentro de `/Volumes/tecate-backup/data/` (servidor SMB de 82 GB vía Tailscale).
   - Consulta únicamente los índices JSON locales (`panoramas_cache.json`, `facades_cache.json`, `blocks_cache.json`) y descarga imágenes exclusivamente mediante transferencia directa:
     `scp Usuario@host:.../screenshots/pano/[nombre].png /ruta/scratch/staging/[edificio]/`

3. **Prohibición de Banquetas Embebidas**:
   - Ninguna malla de edificio (`.glb`) debe contener banquetas, guarniciones ni vialidades. Las banquetas pertenecen a capas GIS independientes del simulador (`Roadways`, `Manzanas`).

4. **Zócalo Basal Enterrado Obligatorio**:
   - Todo muro perimetral debe descender subterráneamente a $Z \le -1.20\text{ m}$ para absorber la pendiente topográfica de las calles sin flotar.

5. **Colisiones Estáticas en Tiempo de Importación y Cero Paredes Invisibles**:
   - Prohibido el uso de mallas de colisión envolventes globales (*Convex Hull*) o macro-cajas manuales monolíticas que sellen vanos. Las colisiones deben derivarse en tiempo de importación mediante `res://tools/building_post_import.gd` a partir de las submallas estructurales reales del `.glb`.

6. **Desacoplamiento Semántica-Código y Plan Previo**:
   - Redacta y valida primero la especificación de cotas y fenestración en un plan antes de generar código en Python.

7. **Acentuación Ortográfica Estricta**:
   - Toda documentación, reporte o mensaje al usuario en español debe contar con acentuación ortográfica completa y rigurosa.

8. **Prohibición de Cajas Manuales en Archivos `.tscn`**:
   - Queda terminantemente prohibido redactar listas manuales de colisionadores `BoxShape3D` en cadenas de texto de escenas `.tscn`.
   - Las colisiones físicas deben generarse automáticamente en tiempo de importación a partir de las submallas estructurales del archivo `.glb`.
   - Las submallas decorativas y rótulos tipográficos (`Txt_`, `Texto_`) deben excluirse de colisión para garantizar caminabilidad peatonal fluida y permitir al jugador aproximarse a escasos centímetros de las fachadas y escaparates sin obstáculos invisibles.

