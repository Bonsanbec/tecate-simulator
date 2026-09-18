# Especificación y Documentación Técnica: Kiosco Octagonal Tradicional de Tecate, B.C. (Parque Miguel Hidalgo) - v2.0

Este documento detalla el diseño, modelado paramétrico 3D, mapas de texturas PBR procedurales, colisiones optimizadas y guía de integración en motor (Godot Engine 4) del **Kiosco Octagonal Tradicional del Parque Miguel Hidalgo**, el elemento arquitectónico y cívico central de la plaza principal de Tecate, Baja California (Pueblo Mágico).

---

## 1. Contexto Urbano, Histórico y Simbólico

El **Parque Miguel Hidalgo** constituye el corazón geográfico, social e histórico de la ciudad de Tecate. En el sistema de coordenadas de este simulador (`tecate-simulator`), dicho parque se encuentra anclado como el origen cartesiano absoluto $(0, 0, 0)$ de la reconstrucción urbana (`32.573229°N, -116.626536°W`).

En el centro exacto de la plaza arbolada se erige este kiosco tradicional, escenario cívico utilizado a lo largo de las décadas para:
- Serenatas dominicales y presentaciones de orquestas o bandas locales.
- Eventos oficiales, ceremonias de las Fiestas Patrias y coronación de reinas de festividades tecatenses.
- Punto de encuentro comunitario y descanso cotidiano bajo la sombra de los fresnos y coníferas del parque.

### Rasgos Morfológicos Distintivos de Tecate (Revisión v2.0)
A diferencia de los kioscos metálicos afrancesados o de fundición porfiriana predominantes en el centro y sur de México, el kiosco de Tecate presenta una identidad arquitectónica híbrida de fuerte arraigo regional de Baja California:
1. **Zócalo de Mampostería de Laja**: Pedestal octagonal de $1.20\text{ m}$ de altura construido con mampostería vista de piedra laja dorada/ocre irregular, con mapa de normales de relieve profundo y juntas de mortero de cemento y cal.
2. **Cornisa Perimetral de Remate**: Moldura corrida en voladizo ($+0.12\text{ m}$) en estuco blanco cálido que remata la plataforma y sirve de base a las columnas.
3. **Escalinata Frontal con Alfardas**: Escalera de 7 peldaños rectos de cantera clara ($1.60\text{ m}$ de ancho libre) con arista redondeada (*bullnose nosing*), confinada entre alfardas sólidas de mampostería en pendiente y protegida por barandales de herrería forjada.
4. **Registro Subterráneo de Servicio**: Nicho rectangular ($0.65 \times 0.85\text{ m}$) empotrado en la cara lateral contigua a la escalinata (cara a -45°), provisto de marco de ángulo de hierro y compuerta de chapa negra con manija.
5. **Columnata de Ladrillo Cocido**: 8 pilares macizos de $0.45 \times 0.45\text{ m}$ dispuestos en radio de $3.05\text{ m}$, levantados con hiladas horizontales de ladrillo rojo tecatense y juntas rehundidas de mortero claro.
6. **Capiteles Ensanchados**: Capiteles en corona escalonada de estuco blanco con sección ensanchada ($0.58 \times 0.58\text{ m}$) para recibir y acunar de manera anatómicamente continua el anillo circular superior.
7. **Faroles Coloniales de Forja**: Apliques de herrería negra fijados a $Z = 3.10\text{ m}$ en las caras exteriores de las 8 columnas, con soporte en escuadra, caja trapezoidal de 4 caras de vidrio ámbar cálido, tejadillo piramidal y pináculo.
8. **Herrería Perimetral con Cenefa de Aros**: 7 vanos cerrados con barandales de forja a $0.90\text{ m}$ de altura, caracterizados por una franja superior de aros circulares de $\varnothing\ 0.08\text{ m}$ bajo el pasamanos y balaustres verticales cada $0.11\text{ m}$.
9. **Arcos Calados Superiores**: 8 arcos escarzanos suspendidos entre columnas ($Z = 3.50 \to 3.90\text{ m}$) con crestería de barrotes colgantes de longitud decreciente y volutas decorativas en las enjutas de unión con los pilares.
10. **Anillo de Corona Cilíndrico Continuo (Entablamento)**: Viga de corona cilíndrica lisa de 96 subdivisiones ($\varnothing\ 7.40\text{ m}$, $H = 0.55\text{ m}$) en estuco blanco, que genera un marcado y elegante contraste circular con la base octagonal.
11. **Cielo Interior Abovedado (Plafón / Soffit)**: Bóveda interior cónica enyesada en blanco cálido marfil ($Z = 4.00 \to 4.60\text{ m}$) que asciende suavemente desde la viga cilíndrica.
12. **Cubierta Cónica de Teja Colonial (Canal y Cobija)**: Tejado cónico de 48 sectores radiales con alero festoneado ondulado, tejas curvas de barro cocido terracota enriquecidas con mapas de normales y rugosidad, y remate cónico cerámico en la cúspide ($Z = 5.66\text{ m}$).

---

## 2. Renders Técnicos Oficiales de Inspección (v2.0)

Renders generados en resolución nativa con el motor **Cycles CPU** de Blender 5.1 con iluminación balanceada de 3 puntos (Key Sun 3.6, Fill Sun 2.2, Rim Sun 2.6):

| Vista General Axonométrica (5.66 m, Ø 7.80 m) | Detalle de Escalinata y Puerta de Servicio |
| :---: | :---: |
| ![Vista General](images/kiosko_preview.png) | ![Detalle Acceso](images/kiosko_acceso.png) |
| **Detalle de Columnas, Capiteles, Faroles y Arcos** | **Detalle de Entablamento Circular y Tejado de Teja** |
| ![Detalle Columnas](images/kiosko_columnas_arcos.png) | ![Detalle Techo](images/kiosko_techo.png) |

---

## 3. Jerarquía Morfológica del Modelo

El modelo está construido a escala métrica real 1:1, con pivote de origen en el centro geométrico al nivel del suelo `(0, 0, 0)`.

```
Kiosco_Root (Node3D / Empty en 0,0,0)
├── Base_Octagonal (Prisma octagonal regular H = 1.20 m, R_in = 3.35 m, R_circ = 3.626 m)
│   ├── Mamposteria_Laja (Muros de piedra irregular con mapeo UV y mapas PBR)
│   ├── Moldura_Perimetral_Piso (Cornisa saliente +0.12 m, Z = 1.10 a 1.22 m)
│   ├── Piso_Interior_Cantera (Pavimento en losetas con mapa de normales)
│   └── Puerta_Servicio (Compuerta de chapa negra de 0.65 x 0.85 m en cara lateral a -45°)
├── Escalinata (7 peldaños al frente -Y: huellas cantera 0.32 m x contrahuellas 0.1714 m)
│   ├── Alfardas_Laterales (Muros de confinamiento en declive de piedra laja)
│   └── Barandales_Escalera (2 pasamanos tubulares oblicuos a 0.90 m con balaustres)
├── Columnas_Octeto (8 unidades radiales en R = 3.05 m, espaciadas a 45°)
│   ├── Plintos_Base (Prismas cuadrados de 0.55 x 0.55 x 0.20 m con chaflán 45°)
│   ├── Fustes_Ladrillo (28 hiladas de ladrillo rojo aparente 0.45 x 0.45 m x 2.35 m)
│   ├── Llagas_Mortero (Juntas rehundidas horizontales de cemento/cal gris)
│   ├── Capiteles_Blanco_Ensanchados (Molduras de ábaco de 0.58 x 0.58 x 0.15 m para asentar el anillo)
│   └── Faroles_Pared (8 faroles coloniales en Z = 3.10 m con vidrio ámbar y forja)
├── Herreria_Perimetral (7 módulos de 0.90 m de alto entre columnas)
│   ├── Pasamanos_Superior (Tubular de 5 x 2.5 cm a Z = 2.10 m)
│   ├── Cenefa_Aros (Franja de anillos circulares de Ø 0.08 m entre Z = 1.98 y 2.10 m)
│   └── Balaustres_Verticales (Barras de forja espaciadas cada 0.11 m)
├── Arcos_Calados_Herreria (8 vanos superiores entre Z = 3.50 y 3.90 m)
│   ├── Arcos_Escarzanos (Curvas rebajadas con flecha central en Z = 3.50 m)
│   ├── Cresteria_Colgante (Barrotes verticales de longitud graduada)
│   └── Volutas_Enjutas (Espirales ornamentales en las esquinas superiores)
├── Anillo_Entablamento (Viga continua cilíndrica de estuco blanco Ø ext 7.40 m, Ø int 6.30 m, H = 0.55 m)
│   └── Plafon_Interior (Cielo abovedado cónico enlucido que asciende de Z = 4.00 a 4.60 m)
└── Cubierta_Conica (Tejado cónico de teja colonial cocida Z = 4.35 a 5.55 m, pendiente 18°)
    ├── Alero_Festoneado (Borde ondulado de teja canal y cobija, Ø 7.80 m)
    ├── Limatesas_Radiales (48 canales de teja radiales con mapas de normales)
    └── Remate_Cuspide (Pináculo cerámico en la cúspide a Z = 5.66 m)
```

---

## 4. Cotas y Dimensiones Métricas

| Cota Vertical ($Z$) | Componente Arquitectónico | Geometría y Dimensiones Nominales | Tolerancia |
| :--- | :--- | :--- | :--- |
| **$0.00\text{ m}$** | Nivel de Suelo / Banqueta de Plaza | Punto de contacto y plano basal del zócalo | $\pm 0.00\text{ m}$ |
| **$0.00 \to 1.20\text{ m}$** | Pedestal / Base Octagonal | Prisma 8 lados: $R_{\text{in}} = 3.35\text{ m}$, $R_{\text{circ}} = 3.626\text{ m}$, $H = 1.20\text{ m}$ | $\pm 0.01\text{ m}$ |
| **$1.10 \to 1.22\text{ m}$** | Moldura / Cornisa Perimetral | Saliente perimetral $+0.12\text{ m}$, espesor $0.10\text{ m}$ | $\pm 0.005\text{ m}$ |
| **$0.15 \to 1.00\text{ m}$** | Puerta de Registro de Servicio | Vano rectangular $0.65\text{ m}$ ancho $\times 0.85\text{ m}$ alto en cara lateral (-45°) | $\pm 0.01\text{ m}$ |
| **$0.00 \to 1.20\text{ m}$** | Escalinata de 7 Peldaños | 7 contrahuellas de $0.1714\text{ m}$, 7 huellas de $0.32\text{ m}$, ancho libre $1.60\text{ m}$ | $\pm 0.005\text{ m}$ |
| **$1.20 \to 1.40\text{ m}$** | Plintos de Columnas (8x) | Prisma cuadrado $0.55 \times 0.55\text{ m}$, chaflán a 45° en últimos $0.06\text{ m}$ | $\pm 0.005\text{ m}$ |
| **$1.40 \to 3.75\text{ m}$** | Fustes de Ladrillo Aparente (8x) | Sección cuadrada $0.45 \times 0.45\text{ m}$, $H = 2.35\text{ m}$ con 28 hiladas | $\pm 0.005\text{ m}$ |
| **$3.75 \to 3.90\text{ m}$** | Capiteles de Estuco Blanco (8x) | Moldura ampliada $0.58 \times 0.58\text{ m}$, altura $0.15\text{ m}$ para acunar el anillo | $\pm 0.005\text{ m}$ |
| **$3.10\text{ m}$** | Faroles Coloniales (8x) | Aplique de forja a $Z = 3.10\text{ m}$ saliente $0.26\text{ m}$ de la cara exterior | $\pm 0.01\text{ m}$ |
| **$1.20 \to 2.10\text{ m}$** | Barandales Perimetrales (7x) | Altura neta $0.90\text{ m}$ (solera $Z = 1.28$, sub-solera $1.98$, pasamanos $2.10\text{ m}$) | $\pm 0.005\text{ m}$ |
| **$3.50 \to 3.90\text{ m}$** | Arcos Calados de Herrería (8x) | Flecha inferior en $Z = 3.50\text{ m}$, solera superior en $Z = 3.88\text{ m}$ | $\pm 0.01\text{ m}$ |
| **$3.85 \to 4.40\text{ m}$** | Anillo de Corona / Entablamento | Cilindro continuo: $\varnothing_{\text{ext}} = 7.40\text{ m}$, $\varnothing_{\text{int}} = 6.30\text{ m}$, alto $0.55\text{ m}$ | $\pm 0.01\text{ m}$ |
| **$4.00 \to 4.60\text{ m}$** | Plafón Interior Abovedado | Bóveda cónica suave en estuco blanco | $\pm 0.01\text{ m}$ |
| **$4.35 \to 5.55\text{ m}$** | Cubierta Cónica de Teja | Pendiente $18^\circ$, radio basal $R = 3.90\text{ m}$ ($\varnothing = 7.80\text{ m}$), 48 canales radiales | $\pm 0.02\text{ m}$ |
| **$5.55 \to 5.66\text{ m}$** | Remate Cónico de la Cúspide | Pináculo cerámico tradicional | $\pm 0.01\text{ m}$ |

---

## 5. Especificación de Materiales PBR y Texturas Embebidas

Los materiales están configurados mediante `Principled BSDF` calibrados para el motor de sombreado físicamente basado (PBR/ORM) de Godot 4:

| Material | Texturas Asignadas | Albedo Base | Roughness | Metallic | Normal Map |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `M_Piedra_Base` | `kiosko_laja_albedo.png`, `kiosko_laja_normal.png`, `kiosko_laja_roughness.png` | Laja ocre dorado (`#A3855C`) | 0.88 (Textura) | 0.00 | Sí (Fuerza 1.50) |
| `M_Piso_Cantera` | `kiosko_cantera_albedo.png`, `kiosko_cantera_normal.png` | Cantera beige arena (`#C7C2B5`) | 0.65 | 0.00 | Sí (Fuerza 0.80) |
| `M_Teja_Terracota` | `kiosko_teja_albedo.png`, `kiosko_teja_normal.png`, `kiosko_teja_roughness.png` | Terracota colonial (`#8B351E`) | 0.78 (Textura) | 0.00 | Sí (Fuerza 1.20) |
| `M_Ladrillo_Pilar` | Procedural PBR | Terracota cocido (`#9E4026`) | 0.80 | 0.00 | No |
| `M_Mortero_Gris` | Procedural PBR | Cemento gris claro (`#C2BDAF`) | 0.92 | 0.00 | No |
| `M_Estuco_Blanco` | Procedural PBR | Blanco marfil cálido (`#E6E3DC`) | 0.65 | 0.00 | No |
| `M_Herreria_Negra` | Procedural PBR | Negro grafito martillado (`#0A0A0A`)| 0.45 | 0.85 | No |
| `M_Vidrio_Farol` | Procedural PBR | Ámbar translúcido (`#F2E6C7`) | 0.25 | 0.10 | No |

---

## 6. Arquitectura de Colisiones y Optimización en Godot 4

En lugar de utilizar mallas cóncavas pesadas (`ConcavePolygonShape3D`) que saturan la memoria física del motor y causan tirones de colisión al caminar el jugador, se entrega la escena lista para producción:

**`godot_project/assets/kiosko_parque_hidalgo.tscn`**

```
Kiosko_Parque_Hidalgo (StaticBody3D)
├── Kiosko_Model (Instance: kiosko_parque_hidalgo.glb)
├── Collision_Base (CollisionShape3D -> CylinderShape3D, R = 3.35 m, H = 1.20 m)
├── Collision_Step_0 a 6 (7x CollisionShape3D -> BoxShape3D ajustados a cada peldaño)
└── Collision_Columna_0 a 7 (8x CollisionShape3D -> BoxShape3D de 0.50 x 2.70 x 0.50 m)
```

### Ventajas Técnicas:
1. **Rendimiento Máximo**: El motor de física resuelve las colisiones mediante intersecciones analíticas de cilindros y cajas (separating axis theorem) a $60\text{ FPS}$ constantes.
2. **Escalado de Peldaños Suave**: El jugador puede ascender por la escalinata con un `CharacterBody3D` estándar sin quedar atorado en aristas microscópicas de la cantería.
3. **Pivote en `(0, 0, 0)`**: Al instanciar la escena en la raíz del mundo de Godot, asienta directamente sobre la cota del terreno sin requerir offsets manuales.

---

## 7. Guía de Instanciación en Godot 4

Para colocar el kiosco en el centro del Parque Hidalgo dentro de `main.tscn`:

```gdscript
# Opción A: Mediante la interfaz de Godot
# Arrastrar "res://assets/kiosko_parque_hidalgo.tscn" al árbol de la escena principal (MainScene).
# Asignar posición Vector3(0, 0, 0).

# Opción B: Carga dinámica por código en GDScript
var kiosko_scene = preload("res://assets/kiosko_parque_hidalgo.tscn")
var kiosko_instance = kiosko_scene.instantiate()
kiosko_instance.position = Vector3(0, 0, 0)
add_child(kiosko_instance)
```

---

## 8. Inventario de Archivos Entregados

1. **`blender_assets/kiosko_parque_hidalgo.blend`**:
   - Archivo maestro nativo de Blender 5.1.
   - Jerarquía completa de colecciones, pivote en `(0, 0, 0)`, materiales PBR calibrados, iluminación de estudio, suelo receptor de sombras y 4 cámaras de inspección.
2. **`godot_project/assets/kiosko_parque_hidalgo.glb`**:
   - Archivo binario glTF 2.0 optimizado (~8.8 MB con texturas PBR embebidas).
   - Estructura limpia de mallas principales agrupadas bajo el nodo raíz `Kiosco_Root`.
3. **`godot_project/assets/kiosko_parque_hidalgo.tscn`**:
   - Escena de Godot 4 configurada con nodo raíz `StaticBody3D` y colisionadores analíticos simplificados (`CylinderShape3D` y `BoxShape3D`).
4. **`godot_project/assets/textures/`**:
   - `kiosko_laja_albedo.png`, `kiosko_laja_normal.png`, `kiosko_laja_roughness.png`
   - `kiosko_cantera_albedo.png`, `kiosko_cantera_normal.png`
   - `kiosko_teja_albedo.png`, `kiosko_teja_normal.png`, `kiosko_teja_roughness.png`
5. **Scripts de Generación**:
   - `scripts/generate_textures.py`: Genera mapas de laja y cantera.
   - `scripts/generate_roof_textures.py`: Genera mapas de teja colonial.
   - `scripts/generate_kiosko_tecate.py`: Genera geometría completa, aplica materiales PBR, exporta `.blend` y `.glb`, y renderiza vistas oficiales.
6. **Galería de Renders (`docs/images/`)**:
   - `kiosko_preview.png`: Vista general axonométrica de conjunto.
   - `kiosko_acceso.png`: Detalle de escalinata de 7 peldaños, alfardas y puerta de servicio.
   - `kiosko_columnas_arcos.png`: Detalle de fustes de ladrillo con llagas, plintos, faroles coloniales y arcos calados.
   - `kiosko_techo.png`: Detalle de entablamento circular y cubierta cónica de teja colonial.
