# Framework Metodológico: Aprendizajes, Plantilla de Especificación y Prompting para Assets Arquitectónicos Complejos

Este documento sintetiza **todo lo logrado**, los **aprendizajes clave** derivados del ciclo iterativo de diseño (v1.0 → v2.0 → v3.0 → v3.1) y el **framework refinado (plantilla + prompt)** para la reconstrucción procedural y modular de monumentos y edificios patrimoniales en `tecate-simulator` (Godot Engine 4 / Blender).

---

## 1. Síntesis de Todo lo Logrado: El Kiosco del Parque Miguel Hidalgo

El **Kiosco Octagonal del Parque Miguel Hidalgo** no es un elemento genérico; constituye el origen cartesiano absoluto $(0, 0, 0)$ (`32.573229°N, -116.626536°W`) de todo el simulador urbano de Tecate, Baja California.

### A. Resultados Técnicos Entregados
1. **Archivo Maestro Blender (`blender_assets/kiosko_parque_hidalgo.blend`)**:
   - Escala real 1:1 métrica, pivote exacto en el suelo `(0, 0, 0)`.
   - 7 mallas principales limpias agrupadas bajo `Kiosco_Root`.
   - Setup de iluminación Cycles calibrado (3 puntos + cielo diurno) y 4 cámaras de inspección.
2. **Asset de Producción Runtime (`godot_project/assets/kiosko_parque_hidalgo.glb`)**:
   - Archivo binario glTF 2.0 optimizado (~13 MB) con texturas PBR embebidas.
   - Sombreado híbrido (Smooth en tambor y tejas, Flat en cantería y ladrillos).
3. **Escena con Física Analítica (`godot_project/assets/kiosko_parque_hidalgo.tscn`)**:
   - Nodo raíz `StaticBody3D` optimizado para 60 FPS estables.
   - Colisionador cilíndrico (`CylinderShape3D`) para el pedestal octagonal ($R = 3.35\text{ m}$, $H = 1.20\text{ m}$).
   - 7 colisionadores de caja (`BoxShape3D`) escalonados analíticos para ascenso suave del jugador.
   - 8 colisionadores de caja para las columnas de ladrillo.
4. **Suite de Texturas PBR Procedurales Dedicadas (`godot_project/assets/textures/`)**:
   - `kiosko_laja_albedo.png`, `kiosko_laja_normal.png`, `kiosko_laja_roughness.png`: Mampostería de laja dorada/ocre con juntas de mortero de cal.
   - `kiosko_ladrillo_albedo.png`, `kiosko_ladrillo_normal.png`, `kiosko_ladrillo_roughness.png`: Ladrillo artesanal decimonónico en tonos arcilla marrón-terracota (`#5C3624`), juntas oscuras y pátina de cocción.
   - `kiosko_cantera_albedo.png`, `kiosko_cantera_normal.png`: Cantera beige arena para huellas y plataforma.
   - `kiosko_teja_albedo.png`, `kiosko_teja_normal.png`, `kiosko_teja_roughness.png`: Terracota colonial cocida (`#8B351E`).
5. **Generadores Automatizados y Reproducibles**:
   - `scripts/generate_kiosko_tecate.py`: Genera geometría, asigna materiales, exporta formatos y procesa renders.
   - `scripts/generate_textures.py`: Genera mapas de laja y cantera.
   - `scripts/generate_brick_texture.py`: Genera mapas de ladrillo decimonónico.
   - `scripts/generate_roof_textures.py`: Genera mapas de teja colonial.
6. **Galería Oficial de Renders de Alta Resolución (`docs/images/`)**:
   - `kiosko_preview.png`: Vista general axonométrica de conjunto.
   - `kiosko_acceso.png`: Detalle de escalinata, puerta de servicio y mampostería.
   - `kiosko_columnas_arcos.png`: Detalle de fustes decimonónicos y arcos calados `|_^_|`.
   - `kiosko_techo.png`: Detalle de tejas 3D volumétricas y entablamento cilíndrico.

---

## 2. Los 6 Aprendizajes Críticos del Ciclo Iterativo

La evolución del kiosco desde una maqueta genérica hasta un facsímil histórico fidedigno arrojó seis aprendizajes fundamentales:

```
                  ┌─────────────────────────────────────────────────────────┐
                  │          LOS 6 APRENDIZAJES ARQUITECTÓNICOS             │
                  └─────────────────────────────────────────────────────────┘
                                               │
     ┌──────────────────────┬──────────────────┴────────────────┬──────────────────────┐
     ▼                      ▼                                   ▼                      ▼
1. GEOMETRÍA REAL      2. SEMÁNTICA ESPACIAL               3. CONTINUIDAD         4. TECTÓNICA REAL
   VS NORMAL MAP          (DIAGRAMAS ASCII)                   TOPOLÓGICA             (SAW-TOOTH)
   Tejas 3D con           Arcos superiores                    Barandilla pisa        Escalinata abierta
   volumen y labios       ascendentes |_^_|                   losa + cierre          sin muro ciego
                          (no catenaria \_/)                  con pilares            al suelo
                                       │                        │
                                       ▼                        ▼
                                5. CROMÁTICA HISTÓRICA    6. LATERALIDAD
                                   Ladrillo XIX oscuro;      Puerta de servicio
                                   mortero en sombra         en +45° (derecha),
                                   (sin bandas blancas)      no en -45°
```

### Aprendizaje 1: Geometría Volumétrica Real vs Ilusión de Textura (Tejas Coloniales)
- **Problema**: En la versión inicial se intentó resolver el tejado de teja canal y cobija únicamente con mapas de normales y ondulaciones en los vértices del cono. Aunque la textura simulaba las estrías, el alero quedaba plano y cortado como papel, rompiendo la inmersión al ver el kiosco desde abajo o de perfil.
- **Solución**: Las tejas coloniales requieren **geometría física apilada**. Se programaron 40 sectores radiales y 6 hiladas concéntricas de cilindros abiertos: las cobijas (arcos convexos) montan sobre los canales (arcos cóncavos), con solape longitudinal real ($4\text{ - }6\text{ cm}$), espesor físico en el labio frontal ($1.6\text{ cm}$) y faldón de entablado inferior para bloquear fugas de luz.

### Aprendizaje 2: Semántica Espacial y el Valor del Diagrama ASCII (`|_^_|`)
- **Problema**: La instrucción inicial pedía "arcos de herrería entre columnas". El agente interpretó un arco colgante hacia abajo tipo catenaria (`\___/`). El usuario corrigió mediante un diagrama conceptual esquemático: `|_^_|`.
- **Solución**: La forja superior colonial mexicana no cuelga hacia el centro del vano (lo cual reduciría la altura libre de paso y golpearía la cabeza de los transeúntes); se compone de una solera superior horizontal fija bajo la cornisa, montantes verticales junto a las columnas (`|`), tramos de arranque horizontal (`_`) y un **arco que apunta hacia ARRIBA** (`^`), con barrotes verticales que llenan las enjutas superiores dejando el vano de paso diáfano. Los diagramas ASCII son el método más infalible de comunicación geométrica espacial entre usuario y modelo de lenguaje.

### Aprendizaje 3: Continuidad Topológica y Cierre de Seguridad en Barandales
- **Problema**: Al omitir el vano frontal para dar paso a la escalera, quedaron huecos abiertos de $0.59\text{ m}$ a cada lado entre la columna de ladrillo y la escalera. Asimismo, el pasamanos de la escalera terminaba flotando en el aire sobre la arista del suelo.
- **Solución**: En cualquier acceso público real:
  1. El pasamanos debe **ingresar en la plataforma** y clavar su poste maestro directamente sobre la losa superior (`pisar el octágono`).
  2. En la cara frontal deben insertarse **tramos cortos de barandilla perimetral** desde las caras interiores de las columnas hasta encontrarse con el pasamanos de la escalera, cerrando el perímetro de protección.

### Aprendizaje 4: Tectónica de la Escalinata (Saw-Tooth vs Alfardas Macizas)
- **Problema**: En la primera versión se modelaron dos enormes muros triangulares de confinamiento (alfardas) que bajaban diagonalmente hasta el suelo, ocultando el perfil de los escalones.
- **Solución**: La fotografía de terreno demostró que la escalinata de Tecate es abierta: cada peldaño es un bloque de roca/cantera maciza cuyo perfil lateral es un **escalonado en saw-tooth (dientes de sierra)**, con espacio libre e iluminado por debajo.

### Aprendizaje 5: Cromática Histórica y Juntas de Mortero (Ladrillo Siglo XIX)
- **Problema**: En las primeras iteraciones, las columnas parecían hechas de ladrillo hueco industrial moderno con juntas blancas brillantes y espaciadas, produciendo un efecto óptico de "rejilla blanca" o "cebra".
- **Solución**: El ladrillo decimonónico artesanal de Tecate se horneaba con leña:
  1. **Tono**: Arcilla marrón-terracota cálida tostada (`#5C3624`), con variaciones naturales de quema.
  2. **Juntas**: Las hiladas son gruesas ($13\text{ cm}$ de paso), asientan casi a tope con apenas $3\text{ mm}$ de hendidura, y el mortero es **oscuro, terroso y en sombra profunda** (`#201411`), nunca blanco ni claro.
  3. **Geometría**: Se eliminaron los cubos independientes de mortero blanco y se confió en hiladas sólidas con variación UV por nivel.

### Aprendizaje 6: Lateralidad y Orientación de Elementos Asimétricos
- **Problema**: La puerta de registro de servicio del sótano existe únicamente en una de las caras laterales del kiosco. Un signo negativo en la rotación (`math.radians(-45)`) la colocó en la cara izquierda, haciéndola invisible en la cámara frontal-derecha de acceso.
- **Solución**: Orientada a $+45^\circ$ ($+X, -Y$), coincide con la cara lateral derecha mostrada en las fotos históricas junto a la escalinata. Las fichas técnicas deben declarar explícitamente la orientación de accesorios asimétricos respecto al observador situado frente al acceso principal.

---

## 3. Plantilla Estandarizada para Assets Arquitectónicos y Monumentos

Usa esta plantilla para comisionar cualquier futuro monumento o edificio de Tecate (ej. Kiosco, Parroquia de Guadalupe, Estación de Tren, Palacio Municipal, Monumento a la Madre):

```markdown
# FICHA TÉCNICA ARQUITECTÓNICA: [Nombre del Edificio/Monumento]

## 1. Contexto, Ubicación y Origen Cartesiano
- **Nombre Oficial**: [Ej. Kiosco del Parque Miguel Hidalgo]
- **Ubicación en Tecate**: [Ej. Centro de la Plaza Principal, Av. Hidalgo y Cárdenas]
- **Coordenadas / Origen Local**: [Ej. Vector3(0, 0, 0) absoluto de la escena / nivel de banqueta]
- **Función en el Simulador**: [Ej. Hito cívico central, escenario de música y punto de reunión]

## 2. Dimensiones Globales y Jerarquía de Volúmenes
- **Pivote de Origen**: Base basal en contacto con el suelo (Z = 0.000 m).
- **Altura Total**: [Ej. 5.68 m hasta la cúspide del pináculo]
- **Huella en Suelo / Envergadura**: [Ej. Diámetro base 7.25 m, diámetro alero 7.84 m, profundidad con escalinata 9.22 m]
- **Simetría y Geometría Primaria**: [Ej. Octagonal regular en base y columnas (45°), cilíndrico continuo en entablamento, cónico en cubierta]

## 3. Despiece Anatómico por Niveles (Bottom-Up)
### Nivel 1: Cimentación y Plataforma Basal (Z = [0.00 a 1.20 m])
- **Forma y Material**: [Ej. Pedestal octagonal de mampostería de laja dorada rústica]
- **Cornisa de Piso**: [Ej. Moldura en voladizo en estuco blanco a Z = 1.10 a 1.22 m]
- **Accesorios Asimétricos**: [Ej. Puerta de registro metálica de 0.65 x 0.85 m situada en la cara lateral DERECHA (+45°) de la escalinata]

### Nivel 2: Circulación y Accesos (Z = [0.00 a 1.20 m])
- **Tipo de Escalinata**: [Ej. Escalinata frontal abierta de 7 peldaños de cantera y roca]
- **Tectónica Lateral**: [IMPORTANTE: Declarar si tiene alfardas macizas al suelo O peldaños abiertos en saw-tooth]
- **Desembarque de Barandales**: [IMPORTANTE: El pasamanos debe pisar la losa del piso con poste maestro y conectarse con barandillas laterales]

### Nivel 3: Columnata y Soportes (Z = [1.20 a 3.92 m])
- **Disposición**: [Ej. 8 columnas cuadradas de 0.45 x 0.45 m dispuestas radialmente a R = 3.05 m]
- **Plintos**: [Ej. Plinto blanco moldurado de 0.55 x 0.55 x 0.20 m con chaflán 45°]
- **Fustes**: [Ej. 18 hiladas gruesas de ladrillo artesanal siglo XIX, color terracota-marrón cocido, juntas de mortero oscuras y delgadas]
- **Capiteles**: [Ej. Moldura escalonada blanca ensanchada de 0.58 x 0.58 m para acunar el entablamento circular]
- **Luminarias**: [Ej. 8 faroles coloniales de forja negra con vidrio ámbar en Z = 3.10 m]

### Nivel 4: Entablamento y Cielos Interiores (Z = [3.85 a 4.60 m])
- **Viga de Corona**: [IMPORTANTE: Declarar si es facetada O anillo cilíndrico continuo perfecto. Ej. Anillo cilíndrico continuo Ø 7.50 m, H = 0.55 m]
- **Plafón / Soffit**: [Ej. Bóveda cónica interior enlucida en yeso blanco marfil que asciende a Z = 4.60 m]

### Nivel 5: Herrería Superior y Tránsitos (Z = [3.52 a 3.86 m])
- **Morfología del Vano**: [IMPORTANTE: Proveer diagrama ASCII. Ej. Solera superior horizontal, montantes laterales y arco que apunta hacia arriba |_^_|]
- **Calado**: [Ej. Barrotes verticales superiores espaciados cada 0.09 m]

### Nivel 6: Techumbre y Cubierta (Z = [4.38 a 5.68 m])
- **Geometría de Cubierta**: [Ej. Cono a 18° de pendiente con 40 sectores radiales y 6 hiladas concéntricas]
- **Tipo de Teja**: [IMPORTANTE: Declarar si requiere geometría 3D física O textura. Ej. Tejas curvas coloniales 3D apiladas canal y cobija con solape real y espesor en labio frontal]
- **Alero y Remate**: [Ej. Alero festoneado ondulado sobresaliente y pináculo cerámico cónico en cúspide]

## 4. Especificación de Materiales PBR
| Material | Elementos Asignados | Tipo de Mapa / Textura | Albedo / Color Base | Roughness | Metallic | Normal Map |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| `M_Piedra_Base` | Mampostería pedestal | Textura procedural PBR | Ocre dorado / arena | 0.88 | 0.00 | Sí (Fuerza 1.4) |
| `M_Ladrillo_Pilar`| Fustes de columnas | Textura PBR decimonónica | Terracota tostado (`#5C3624`) | 0.85 | 0.00 | Sí (Fuerza 1.6) |
| `M_Estuco_Blanco` | Plintos, capiteles, tambor | Procedural PBR | Blanco marfil cálido (`#E6E3DC`) | 0.65 | 0.00 | No |
| `M_Teja_Terracota`| Tejas 3D y pináculo | Textura PBR teja | Terracota colonial (`#8B351E`) | 0.78 | 0.00 | Sí (Fuerza 1.3) |
| `M_Herreria_Negra`| Barandales, arcos, farol | Procedural PBR | Negro grafito martillado | 0.45 | 0.85 | No |
| `M_Piso_Cantera` | Plataforma y huellas | Textura PBR cantera | Beige arena (`#C7C2B5`) | 0.60 | 0.00 | Sí (Fuerza 0.8) |

## 5. Cámaras de Inspección Obligatorias (Setup de Validación)
1. **Vista General Axonométrica**: Captura de conjunto en 45° mostrando base, escalinata, tambor y techumbre completa.
2. **Detalle de Acceso y Fachada Principal**: Encuadre centrado en la escalinata, mostrando barandales pisando el firme, perfil de peldaños y accesorios laterales.
3. **Detalle de Columnata y Forja**: Acercamiento a la textura de los fustes, plintos, capiteles y al arco superior |_^_|.
4. **Detalle de Cubierta y Aleros**: Toma en contrapicado o rasante del alero para verificar el volumen físico 3D de las tejas.

## 6. Colisiones y Arquitectura en Godot 4
- Nodo raíz `StaticBody3D`.
- Colisionador primario cilíndrico/prismático para la base.
- Colisionadores tipo caja escalonados analíticos para peldaños (sin mallas cóncavas pesadas).
- Colisionadores tipo caja para cada columna de soporte.
```

---

## 4. Guía de "Prompt Engineering" para Modelado Arquitectónico 3D

Para lograr que un agente de IA genere un monumento con fidelidad absoluta al primer intento, sigue estas **5 reglas de oro de redacción de prompts**:

### Regla 1: Proporcionar la Ficha Estructurada (Bottom-Up)
Nunca pidas: *"Crea el kiosco del parque de Tecate"*. 
Siempre proporciona el desglose de cotas verticales ($Z$), radios ($R$) y número de lados/columnas.

### Regla 2: Emplear Restricciones Negativas Explícitas
Los modelos de lenguaje tienen sesgos hacia "soluciones genéricas". Es indispensable declarar lo que **NO** debe hacerse:
- *"NO uses texturas planas o normal maps para las tejas; genera geometría física 3D con solape de hiladas y grosor visible en el alero."*
- *"NO modeles alfardas macizas triangulares que rellenen la escalera hasta el suelo; los escalones deben tener perfil visto en saw-tooth con espacio abierto inferior."*
- *"NO uses mortero blanco ni líneas claras entre ladrillos; el ladrillo es decimonónico tostado con mortero oscuro en sombra profunda."*
- *"NO diseñes el tambor superior facetado u octagonal; debe ser un cilindro continuo suave."*

### Regla 3: Incluir Diagramas Esquemáticos ASCII para Perfiles y Vános
Cuando una forma sea ambigua, el diagrama ASCII resuelve cualquier duda espacial:
```
Vano superior de herrería:
+-------------------------------+  <- Solera superior horizontal
| | | /                   \ | | |  <- Barrotes verticales en enjutas
| |  /                     \  | |
+---+                       +---+  <- Arranque inferior horizontal
| <------- Hueco libre -------> |  <- Perfil |_^_| apuntando hacia arriba
```

### Regla 4: Especificar la Lateralidad y la Orientación respecto al Acceso
Declarar siempre las coordenadas relativas:
- *"La puerta de servicio de chapa metálica está en la cara lateral DERECHA contigua a la escalinata (+45°, +X, -Y respecto al frente principal)."*
- *"El pasamanos de la escalera debe avanzar 0.20 m sobre la losa y plantar su poste superior directamente sobre el suelo del octágono."*

### Regla 5: Exigir Inspección Visual Autónoma
Incluye en el prompt la instrucción de generar renders de prueba y visualizarlos:
- *"Configura 4 cámaras de inspección Cycles (General, Acceso con puerta, Columnas con arcos y Cubierta con tejas 3D). Renderiza en segundo plano y visualiza las imágenes con `view_file` para certificar las proporciones antes de dar por concluida la tarea."*
