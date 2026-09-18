# Especificación y Documentación Técnica: Kiosco Octagonal Tradicional de Tecate, B.C. (Parque Miguel Hidalgo) - v3.0

Este documento detalla el diseño, modelado paramétrico 3D, mapas de texturas PBR decimonónicas, colisiones optimizadas y guía de integración en motor (Godot Engine 4) del **Kiosco Octagonal Tradicional del Parque Miguel Hidalgo**, el elemento arquitectónico y cívico central de la plaza principal de Tecate, Baja California (Pueblo Mágico).

---

## 1. Contexto Urbano, Histórico y Simbólico

El **Parque Miguel Hidalgo** constituye el corazón geográfico, social e histórico de la ciudad de Tecate. En el sistema de coordenadas de este simulador (`tecate-simulator`), dicho parque se encuentra anclado como el origen cartesiano absoluto $(0, 0, 0)$ de la reconstrucción urbana (`32.573229°N, -116.626536°W`).

En el centro exacto de la plaza arbolada se erige este kiosco tradicional, escenario cívico utilizado a lo largo de las décadas para serenatas dominicales, conciertos cívicos y punto de encuentro comunitario.

### Rasgos Morfológicos Distintivos de Tecate (Revisión v3.0)
1. **Zócalo de Mampostería de Laja**: Pedestal octagonal de $1.20\text{ m}$ de altura construido con mampostería vista de piedra laja dorada/ocre irregular con relieve normal y mortero de cal/cemento.
2. **Escalinata Abierta Escalonada (Saw-Tooth)**: 7 peldaños individuales de roca y cantera con perfil lateral escalonado (huella y contrahuella visibles) y espacio abierto inferior sin muros ciegos que obstruyan el paso visual hacia el suelo.
3. **Barandilla Frontal con Desembarque en Octágono**: Los pasamanos de la escalera ingresan en la plataforma y asientan sus postes terminales directamente sobre el firme del octágono, complementándose con tramos cortos de barandilla perimetral que van desde las columnas frontales para cerrar el perímetro de seguridad.
4. **Columnata de Ladrillo Artesanal del Siglo XIX**: 8 pilares de $0.45 \times 0.45\text{ m}$ estructurados en 18 hiladas gruesas de ladrillo decimonónico de barro cocido rústico con variaciones tonales de horno de leña (`kiosko_ladrillo_*`), juntas anchas de mortero y capiteles ensanchados de $0.58 \times 0.58\text{ m}$.
5. **Arcos Calados Superiores Ascendentes (`|_^_|`)**: 8 vanos superiores de forja bajo el entablamento conformados por solera superior horizontal ($Z = 3.86\text{ m}$), montantes verticales laterales (`|`), tramos horizontales de arranque (`_`) y un arco central que asciende hacia arriba (`^`), con barrotes verticales que llenan la crestería y dejan el vano inferior de paso libre.
6. **Entablamento Cilíndrico Continuo**: Tambor circular liso de 96 subdivisiones ($\varnothing\ 7.50\text{ m}$, $H = 0.55\text{ m}$) en estuco blanco pulido, contrastando formalmente con la base octagonal, acompañado por plafón abovedado cónico interior ($Z = 4.00 \to 4.60\text{ m}$).
7. **Cubierta Cónica con Tejas Curvas 3D Volumétricas**: Techumbre cónica a $18^\circ$ de pendiente conformada por 40 sectores radiales y 6 hiladas concéntricas de tejas cerámicas coloniales físicas 3D (canal y cobija) con solape escalonado real, labios frontales con espesor físico ($1.6\text{ cm}$), alero ondulado sobresaliente y remate cónico cerámico en la cúspide ($Z = 5.68\text{ m}$).

---

## 2. Renders Técnicos Oficiales de Inspección (v3.0)

Renders generados en resolución nativa ($1600 \times 1200$) con el motor **Cycles CPU** de Blender 5.1 con iluminación balanceada de 3 puntos y cielo diurno:

| Vista General Axonométrica (5.68 m, Ø 7.84 m) | Detalle de Escalinata, Barandillas y Roca |
| :---: | :---: |
| ![Vista General](images/kiosko_preview.png) | ![Detalle Acceso](images/kiosko_acceso.png) |
| **Detalle de Columnas Siglo XIX y Arcos |_^_|** | **Detalle de Tejas 3D y Entablamento Cilíndrico** |
| ![Detalle Columnas y Arcos](images/kiosko_columnas_arcos.png) | ![Detalle Techo](images/kiosko_techo.png) |

---

## 3. Jerarquía Morfológica del Modelo

```
Kiosco_Root (Node3D / Empty en 0,0,0)
├── Base_Octagonal (Prisma octagonal regular H = 1.20 m, R_in = 3.35 m, R_circ = 3.626 m)
│   ├── Mamposteria_Laja (Muros de piedra irregular con mapeo UV y mapas PBR)
│   ├── Moldura_Perimetral_Piso (Cornisa saliente +0.12 m, Z = 1.10 a 1.22 m)
│   ├── Piso_Interior_Cantera (Pavimento en losetas con mapa de normales)
│   └── Puerta_Servicio (Compuerta de chapa negra de 0.65 x 0.85 m en cara lateral a -45°)
├── Escalinata (7 peldaños escalonados en saw-tooth con perfil lateral libre al suelo)
│   └── Barandales_Escalera (Desembarque superior pisando el octágono a Z = 1.20 m)
├── Columnas_Octeto (8 unidades radiales en R = 3.05 m, espaciadas a 45°)
│   ├── Plintos_Base (Prismas cuadrados de 0.55 x 0.55 x 0.20 m con chaflán 45°)
│   ├── Fustes_Ladrillo_XIX (18 hiladas gruesas de ladrillo artesanal decimonónico con mapas PBR)
│   ├── Capiteles_Blanco_Ensanchados (Molduras de ábaco de 0.58 x 0.58 x 0.18 m para asentar el anillo)
│   └── Faroles_Pared (8 faroles coloniales en Z = 3.10 m con vidrio ámbar y forja)
├── Herreria_Perimetral (7 módulos estándar + 2 tramos de encuentro frontal con la escalera)
│   ├── Pasamanos_Superior (Tubular de 5 x 2.5 cm a Z = 2.10 m)
│   ├── Cenefa_Aros (Franja de anillos circulares de Ø 0.08 m)
│   └── Balaustres_Verticales (Barras de forja espaciadas cada 0.11 m)
├── Arcos_Calados_Herreria (8 vanos superiores |_^_| entre Z = 3.52 y 3.86 m)
│   ├── Solera_Superior_Horizontal (Z = 3.86 m)
│   ├── Montantes_Laterales (Z = 3.52 a 3.86 m)
│   ├── Arco_Ascendente_Inferior (Arranque horizontal en Z = 3.52 m, cúspide en Z = 3.78 m)
│   └── Cresteria_Vertical (Barrotes superiores que conectan el arco con la solera)
├── Anillo_Entablamento (Viga cilíndrica continua de estuco blanco Ø ext 7.50 m, H = 0.55 m)
│   └── Plafon_Interior (Cielo abovedado cónico enlucido que asciende de Z = 4.00 a 4.60 m)
└── Cubierta_Conica (Tejas curvas coloniales 3D apiladas con volumen real)
    ├── Canales_Cobijas_3D (40 sectores radiales x 6 hiladas concéntricas con solape escalonado)
    ├── Alero_Sobresaliente_Ondulado (Labio frontal con espesor físico de 1.6 cm)
    ├── Entablado_Soporte_Oscuro (Faldón cónico bajo las tejas)
    └── Remate_Cuspide (Pináculo cerámico en la cúspide a Z = 5.68 m)
```

---

## 4. Cotas y Dimensiones Métricas Nominales

| Cota Vertical ($Z$) | Componente Arquitectónico | Geometría y Dimensiones Nominales |
| :--- | :--- | :--- |
| **$0.00\text{ m}$** | Nivel de Suelo / Banqueta de Plaza | Punto de contacto y plano basal del zócalo |
| **$0.00 \to 1.20\text{ m}$** | Pedestal / Base Octagonal | Prisma 8 lados: $R_{\text{in}} = 3.35\text{ m}$, $R_{\text{circ}} = 3.626\text{ m}$, $H = 1.20\text{ m}$ |
| **$1.10 \to 1.22\text{ m}$** | Moldura / Cornisa Perimetral | Saliente perimetral $+0.12\text{ m}$, espesor $0.10\text{ m}$ |
| **$0.00 \to 1.20\text{ m}$** | Escalinata Escalonada | 7 peldaños: huella $0.32\text{ m}$, contrahuella $0.1714\text{ m}$, ancho $1.60\text{ m}$, perfil libre |
| **$1.20 \to 1.40\text{ m}$** | Plintos de Columnas (8x) | Prisma cuadrado $0.55 \times 0.55\text{ m}$, chaflán a 45° |
| **$1.40 \to 3.74\text{ m}$** | Fustes de Ladrillo Siglo XIX (8x) | Sección cuadrada $0.45 \times 0.45\text{ m}$, 18 hiladas gruesas artesanales |
| **$3.74 \to 3.92\text{ m}$** | Capiteles de Estuco Blanco (8x) | Moldura ampliada $0.58 \times 0.58\text{ m}$, altura $0.18\text{ m}$ |
| **$3.10\text{ m}$** | Faroles Coloniales (8x) | Aplique de forja a $Z = 3.10\text{ m}$ con jaula de vidrio ámbar |
| **$1.20 \to 2.10\text{ m}$** | Barandales Perimetrales | Altura neta $0.90\text{ m}$, pasamanos a $2.10\text{ m}$, cierre continuo con escalera |
| **$3.52 \to 3.86\text{ m}$** | Arcos Calados Superiores `|_^_|` | Solera superior a $3.86\text{ m}$, montantes a $3.52\text{ m}$, arco sube a $3.78\text{ m}$ |
| **$3.85 \to 4.40\text{ m}$** | Anillo de Corona / Entablamento | Cilindro continuo: $\varnothing_{\text{ext}} = 7.50\text{ m}$, alto $0.55\text{ m}$ |
| **$4.00 \to 4.60\text{ m}$** | Plafón Interior Abovedado | Bóveda cónica suave en estuco blanco |
| **$4.38 \to 5.50\text{ m}$** | Cubierta Cónica de Tejas 3D | Pendiente $18^\circ$, 40 radiales $\times$ 6 hiladas solapadas físicamente |
| **$5.50 \to 5.68\text{ m}$** | Pináculo Cerámico de Cúspide | Remate cónico tradicional |

---

## 5. Especificación de Materiales PBR

| Material | Texturas Asignadas | Propiedades Clave |
| :--- | :--- | :--- |
| `M_Piedra_Base` | `kiosko_laja_albedo.png`, `kiosko_laja_normal.png`, `kiosko_laja_roughness.png` | Laja ocre irregular con relieve de juntas |
| `M_Ladrillo_Pilar` | `kiosko_ladrillo_albedo.png`, `kiosko_ladrillo_normal.png`, `kiosko_ladrillo_roughness.png` | Ladrillo artesanal decimonónico con pátina |
| `M_Teja_Terracota` | `kiosko_teja_albedo.png`, `kiosko_teja_normal.png`, `kiosko_teja_roughness.png` | Arcilla roja colonial cocida (`#8B351E`) |
| `M_Piso_Cantera` | `kiosko_cantera_albedo.png`, `kiosko_cantera_normal.png` | Cantera beige arena con juntas rehundidas |
| `M_Estuco_Blanco` | Procedural PBR | Blanco marfil cálido (`#E6E3DC`) |
| `M_Herreria_Negra` | Procedural PBR | Hierro forjado martillado (`Metallic: 0.85`) |
| `M_Vidrio_Farol` | Procedural PBR | Ámbar translúcido cálido |

---

## 6. Inventario de Entregables

1. **`blender_assets/kiosko_parque_hidalgo.blend`**: Archivo maestro nativo Blender 5.1 con geometría 3D completa y setup Cycles.
2. **`godot_project/assets/kiosko_parque_hidalgo.glb`**: Asset de producción runtime (~13 MB) con tejas 3D y texturas PBR embebidas.
3. **`godot_project/assets/kiosko_parque_hidalgo.tscn`**: Escena lista para Godot 4 con nodo `StaticBody3D` y colisionadores analíticos.
4. **`scripts/generate_brick_texture.py`**: Generador de mapas PBR para ladrillo decimonónico.
5. **`scripts/generate_kiosko_tecate.py`**: Script de generación automatizada v3.0.
6. **`docs/images/kiosko_*.png`**: Renders oficiales de alta resolución.
