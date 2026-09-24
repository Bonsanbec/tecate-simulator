"""
=============================================================================
GENERADOR PROCEDURAL 3D: COMPLEJO COMERCIAL PDTE. LÁZARO CÁRDENAS 33
(ÉPOCA: HISTÓRICO 2009 - VERSIÓN GROUND-TRUTH ALTA DEFINICIÓN FOTORREALISTA V3.0)
=============================================================================
Reconstrucción fidedigna del conjunto continuo de comercios en Tecate, B.C.:
  1. Librería España (colindante con DENTISTA de BBVA) + Espectacular Bar Diana
  2. Bar Turístico Diana (con marquesina, Diana Cazadora y puerta dorada)
  3. Annita's Boutique (con panel negro, óvalo turquesa, vitrina y espectacular RENTA MESAS)
  4. Party Rentals Kuroky (con rótulo completo verde/morado, cartelera, ventanal notas musicales y buzones)
  5. Florería Orquídea (esquina en ochava a 45º, frontón Art Déco con mosaico verde y rótulo fucsia)
  6. Callejón Libertad / Libertad: Florería Orquídea ala norte y Foto Estudio Curiel
     (marquesina Streamline con estrías, letrero 3D, letrero en muro, tótem vertical)
  7. Fachada Poniente / Reverso hacia estacionamiento: Posterior Foto Estudio Curiel,
     marquesina angulada Bar Diana, puerta de servicio y terraza cercada con reja negra.
  8. Medianera Sur: Enrase liso continuo con BBVA DENTISTA en Y = 0.00 m.

Contrato Cartesiano Canónico:
  - Origen (0, 0, 0): Esquina Sur-Oriente a nivel de banqueta en Cárdenas (límite BBVA DENTISTA)
  - Eje +X: Profundidad hacia el interior de la manzana / Poniente (0.00 a 16.50 m)
  - Eje +Y: Longitud de fachada hacia el Norte sobre Calle Pdte. Lázaro Cárdenas (0.00 a 24.50 m)
  - Eje +Z: Cota vertical (Normal de rasante al cenit)
  - Zócalo Basal Enterrado: Z in [-1.20, 0.00 m]
=============================================================================
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Euler, Matrix

# ---------------------------------------------------------------------------
# 1. Utilidades y Configuración de Escena
# ---------------------------------------------------------------------------

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)
    root_col = bpy.data.collections.new("Cardenas_33_Root")
    scene.collection.children.link(root_col)
    return root_col

def add_box(bm, x1, x2, y1, y2, z1, z2):
    """Genera una caja cerrada orientada con normales hacia el exterior."""
    xmin, xmax = min(x1, x2), max(x1, x2)
    ymin, ymax = min(y1, y2), max(y1, y2)
    zmin, zmax = min(z1, z2), max(z1, z2)

    verts = [
        bm.verts.new((xmin, ymin, zmin)), bm.verts.new((xmax, ymin, zmin)),
        bm.verts.new((xmax, ymax, zmin)), bm.verts.new((xmin, ymax, zmin)),
        bm.verts.new((xmin, ymin, zmax)), bm.verts.new((xmax, ymin, zmax)),
        bm.verts.new((xmax, ymax, zmax)), bm.verts.new((xmin, ymax, zmax))
    ]
    bm.faces.new((verts[0], verts[1], verts[2], verts[3])) # Inferior (-Z)
    bm.faces.new((verts[4], verts[7], verts[6], verts[5])) # Superior (+Z)
    bm.faces.new((verts[0], verts[4], verts[5], verts[1])) # Frontal (-Y)
    bm.faces.new((verts[1], verts[5], verts[6], verts[2])) # Derecha (+X)
    bm.faces.new((verts[2], verts[6], verts[7], verts[3])) # Trasera (+Y)
    bm.faces.new((verts[3], verts[7], verts[4], verts[0])) # Izquierda (-X)
    return verts

def add_oriented_box(bm, center_xy, tangent_xy, normal_xy, s_min, s_max, n_min, n_max, z_min, z_max):
    """Construye una caja orientada según un marco ortonormal 2D (tangente, normal exterior)."""
    verts = []
    for s in (s_min, s_max):
        for n in (n_min, n_max):
            for z in (z_min, z_max):
                vx = center_xy[0] + s * tangent_xy[0] + n * normal_xy[0]
                vy = center_xy[1] + s * tangent_xy[1] + n * normal_xy[1]
                verts.append(bm.verts.new((vx, vy, z)))
    faces = [
        (0, 1, 3, 2), # s_min
        (4, 6, 7, 5), # s_max
        (0, 4, 5, 1), # n_min interior
        (2, 3, 7, 6), # n_max exterior
        (0, 2, 6, 4), # z_min
        (1, 5, 7, 3), # z_max
    ]
    for f in faces:
        bm.faces.new((verts[f[0]], verts[f[1]], verts[f[2]], verts[f[3]]))

def create_mesh_object(name, bm, mat, col):
    """Crea un objeto Mesh en Blender a partir de un BMesh y asigna su material."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(me)
    bm.free()
    me.update()
    obj = bpy.data.objects.new(name, me)
    if mat:
        obj.data.materials.append(mat)
    col.objects.link(obj)
    return obj

def create_3d_text(name, text_string, size, extrude, pos, rot_euler, mat, col, align_x='CENTER'):
    """Crea una entidad tipográfica 3D orientada con su normal hacia el exterior (cero efecto espejo)."""
    t_curve = bpy.data.curves.new(type="FONT", name=name + "_Curve")
    t_curve.body = text_string
    t_curve.size = size
    t_curve.extrude = extrude
    t_curve.align_x = align_x
    t_curve.align_y = 'CENTER'
    obj = bpy.data.objects.new(name, t_curve)
    obj.location = Vector(pos)
    obj.rotation_euler = Euler(rot_euler, 'XYZ')
    if mat:
        obj.data.materials.append(mat)
    col.objects.link(obj)
    return obj

# ---------------------------------------------------------------------------
# 2. Materiales PBR Calibrados
# ---------------------------------------------------------------------------

def create_materials():
    mats = {}

    def _make_mat(name, color, rough=0.8, metal=0.0, transmission=0.0, ior=1.45):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = color
            bsdf.inputs["Roughness"].default_value = rough
            bsdf.inputs["Metallic"].default_value = metal
            if transmission > 0.0:
                if "Transmission Weight" in bsdf.inputs:
                    bsdf.inputs["Transmission Weight"].default_value = transmission
                elif "Transmission" in bsdf.inputs:
                    bsdf.inputs["Transmission"].default_value = transmission
                bsdf.inputs["IOR"].default_value = ior
        return mat

    # Estucos y mampostería
    mats["estuco_marfil"] = _make_mat("M_Estuco_Marfil", (0.88, 0.87, 0.83, 1.0), rough=0.80)
    mats["estuco_blanco"] = _make_mat("M_Estuco_Blanco", (0.95, 0.95, 0.93, 1.0), rough=0.65)
    mats["estuco_arena"] = _make_mat("M_Estuco_Arena", (0.82, 0.78, 0.68, 1.0), rough=0.80)
    mats["zocalo_basal"] = _make_mat("M_Zocalo_Basal", (0.04, 0.045, 0.05, 1.0), rough=0.90)
    mats["cantera_rustica"] = _make_mat("M_Cantera_Rustica", (0.42, 0.30, 0.20, 1.0), rough=0.85)
    mats["mosaico_verde"] = _make_mat("M_Mosaico_Verde", (0.08, 0.35, 0.18, 1.0), rough=0.30)
    mats["concreto_marquesina"] = _make_mat("M_Concreto_Marquesina", (0.88, 0.87, 0.83, 1.0), rough=0.70)

    # Rótulos comerciales y acentos
    mats["diana_blanco"] = _make_mat("M_Diana_Blanco", (0.96, 0.94, 0.90, 1.0), rough=0.40)
    mats["diana_oro"] = _make_mat("M_Diana_Oro", (0.88, 0.72, 0.22, 1.0), rough=0.18, metal=0.90)
    mats["diana_cursiva_naranja"] = _make_mat("M_Diana_Naranja", (0.92, 0.46, 0.06, 1.0), rough=0.25)
    mats["anita_negro"] = _make_mat("M_Anita_Negro", (0.02, 0.022, 0.025, 1.0), rough=0.30, metal=0.10)
    mats["anita_turquesa"] = _make_mat("M_Anita_Turquesa", (0.00, 0.62, 0.54, 1.0), rough=0.20)
    mats["letras_rojas"] = _make_mat("M_Letras_Rojas", (0.80, 0.04, 0.03, 1.0), rough=0.25)
    mats["azul_comercial"] = _make_mat("M_Azul_Comercial", (0.02, 0.14, 0.55, 1.0), rough=0.30)
    mats["azul_curiel_3d"] = _make_mat("M_Azul_Curiel_3D", (0.04, 0.20, 0.70, 1.0), rough=0.20, metal=0.25)
    mats["verde_party"] = _make_mat("M_Verde_Party", (0.06, 0.52, 0.15, 1.0), rough=0.25)
    mats["morado_kuroky"] = _make_mat("M_Morado_Kuroky", (0.42, 0.08, 0.55, 1.0), rough=0.25)
    mats["orquidea_fucsia"] = _make_mat("M_Orquidea_Fucsia", (0.88, 0.06, 0.40, 1.0), rough=0.25)

    # Herrería, marcos y elementos de fachada
    mats["herreria_negra"] = _make_mat("M_Herreria_Negra", (0.03, 0.03, 0.035, 1.0), rough=0.45, metal=0.85)
    mats["canceleria_alum"] = _make_mat("M_Canceleria_Alum", (0.06, 0.07, 0.08, 1.0), rough=0.30, metal=0.80)
    mats["aluminio_blanco"] = _make_mat("M_Aluminio_Blanco", (0.92, 0.92, 0.92, 1.0), rough=0.35, metal=0.40)
    mats["vidrio_reflect"] = _make_mat("M_Vidrio_Reflect", (0.05, 0.09, 0.14, 1.0), rough=0.08, transmission=0.85, ior=1.52)
    mats["vidrio_oscuro"] = _make_mat("M_Vidrio_Oscuro", (0.02, 0.03, 0.05, 1.0), rough=0.10, transmission=0.40, ior=1.52)
    mats["persianas"] = _make_mat("M_Persianas", (0.72, 0.68, 0.60, 1.0), rough=0.65)
    mats["madera_puerta"] = _make_mat("M_Madera_Puerta", (0.58, 0.40, 0.18, 1.0), rough=0.55)
    mats["revistas_collage"] = _make_mat("M_Revistas_Collage", (0.78, 0.72, 0.66, 1.0), rough=0.75)

    # Zócalos y detalles de banqueta
    mats["zocalo_chocolate"] = _make_mat("M_Zocalo_Chocolate", (0.22, 0.12, 0.08, 1.0), rough=0.80)
    mats["amarillo_mostaza"] = _make_mat("M_Amarillo_Mostaza", (0.75, 0.52, 0.08, 1.0), rough=0.65)
    mats["buzon_amarillo"] = _make_mat("M_Buzon_Amarillo", (0.92, 0.64, 0.04, 1.0), rough=0.40)
    mats["telefono_rojo"] = _make_mat("M_Telefono_Rojo", (0.78, 0.09, 0.06, 1.0), rough=0.40)
    mats["lamina_acero"] = _make_mat("M_Lamina_Acero", (0.65, 0.68, 0.70, 1.0), rough=0.35, metal=0.75)
    mats["azotea_asfalto"] = _make_mat("M_Azotea_Asfalto", (0.04, 0.04, 0.045, 1.0), rough=0.95)

    return mats

# ---------------------------------------------------------------------------
# 3. Modelado Fachada Este (Pdte. Lázaro Cárdenas: Y = 0.00 a 24.50 m)
# ---------------------------------------------------------------------------

def build_cardenas_facade(mats, col):
    """Construye todos los comercios frontales sobre Cárdenas:
    Librería España, Bar Diana, Annita's Boutique, Party Rentals y Florería Orquídea."""

    bm_walls = bmesh.new()
    bm_zocalo = bmesh.new()
    bm_canopy = bmesh.new()
    bm_frames = bmesh.new()
    bm_glass = bmesh.new()
    bm_blinds = bmesh.new()
    bm_metal = bmesh.new()
    bm_wood = bmesh.new()
    bm_details = bmesh.new()
    bm_roof = bmesh.new()
    bm_mosaico = bmesh.new()
    bm_anita_negro = bmesh.new()
    bm_anita_turq = bmesh.new()
    bm_party_panel = bmesh.new()

    # Zócalo basal enterrado perimetral obligatorio (Z = -1.20 a 0.00 m)
    add_box(bm_zocalo, -0.30, 16.50, -0.10, 24.60, -1.20, 0.00)

    # -----------------------------------------------------------------------
    # CRUJÍA 1: LIBRERÍA ESPAÑA (Y: 0.00 a 4.80 m, colindancia con BBVA en Y=0.00)
    # -----------------------------------------------------------------------
    y_lib_0, y_lib_1 = 0.00, 4.80
    
    add_box(bm_walls, -0.15, 0.00, y_lib_0, y_lib_1, 0.00, 4.15)
    # Muro medianero Sur liso hermético con BBVA en Y = 0.00 m
    add_box(bm_walls, 0.00, 16.50, -0.05, 0.05, 0.00, 4.15)

    # Zócalo amarillo mostaza en fachada baja
    add_box(bm_details, -0.18, -0.10, y_lib_0, y_lib_1, 0.00, 0.65)

    # Gran escaparate de revistas (Y: 1.20 a 4.70 m, Z: 0.65 a 3.05 m)
    add_box(bm_frames, -0.16, -0.12, 1.20, 4.70, 0.65, 0.70)
    add_box(bm_frames, -0.16, -0.12, 1.20, 4.70, 3.00, 3.05)
    add_box(bm_frames, -0.16, -0.12, 1.20, 1.25, 0.65, 3.05)
    add_box(bm_frames, -0.16, -0.12, 4.65, 4.70, 0.65, 3.05)
    add_box(bm_frames, -0.16, -0.12, 2.35, 2.40, 0.65, 3.05)
    add_box(bm_frames, -0.16, -0.12, 3.50, 3.55, 0.65, 3.05)
    add_box(bm_glass, -0.14, -0.13, 1.25, 4.65, 0.70, 3.00)
    # Exhibidores interiores de revistas
    add_box(bm_details, 0.05, 0.40, 1.30, 4.60, 0.65, 2.80)

    # Puerta peatonal vidriada (Y: 0.20 a 1.15 m, Z: 0.00 a 2.50 m)
    add_box(bm_frames, -0.16, -0.12, 0.20, 1.15, 0.00, 0.05)
    add_box(bm_frames, -0.16, -0.12, 0.20, 1.15, 2.45, 2.50)
    add_box(bm_frames, -0.16, -0.12, 0.20, 0.25, 0.00, 2.50)
    add_box(bm_frames, -0.16, -0.12, 1.10, 1.15, 0.00, 2.50)
    add_box(bm_glass, -0.14, -0.13, 0.25, 1.10, 0.05, 2.45)
    add_box(bm_frames, -0.16, -0.12, 0.20, 1.15, 3.00, 3.05)
    add_box(bm_glass, -0.14, -0.13, 0.25, 1.10, 2.50, 3.00)

    # Fascia superior y letrero Librería España (Z: 3.10 a 4.10 m)
    add_box(bm_frames, -0.20, -0.16, y_lib_0 + 0.10, y_lib_1 - 0.10, 3.10, 4.10)
    add_box(bm_details, -0.19, -0.17, y_lib_0 + 0.15, y_lib_1 - 0.15, 3.35, 4.05)
    add_box(bm_frames, -0.19, -0.17, y_lib_0 + 0.15, y_lib_1 - 0.15, 3.15, 3.35)

    rot_cardenas = (math.radians(90.0), 0.0, math.radians(-90.0))
    create_3d_text("Txt_Lib_Espana", "Libreria Espana", 0.30, 0.025, (-0.21, 2.45, 3.68), rot_cardenas, mats["azul_comercial"], col)
    create_3d_text("Txt_Lib_Sub", "LIBROS - REVISTAS - PERIODICOS", 0.11, 0.015, (-0.21, 2.45, 3.24), rot_cardenas, mats["herreria_negra"], col)

    # Espectacular de azotea sobre Librería España / Bar Diana
    add_box(bm_metal, 0.20, 0.26, 1.50, 1.56, 4.15, 7.80)
    add_box(bm_metal, 0.20, 0.26, 4.20, 4.26, 4.15, 7.80)
    add_box(bm_metal, 0.20, 0.26, 1.50, 4.26, 7.74, 7.80)
    add_box(bm_details, 0.22, 0.25, 1.40, 4.30, 5.20, 7.70)

    # -----------------------------------------------------------------------
    # CRUJÍA 2: BAR TURÍSTICO DIANA (Y: 4.80 a 9.10 m)
    # -----------------------------------------------------------------------
    y_dia_0, y_dia_1 = 4.80, 9.10

    add_box(bm_walls, -0.15, 0.00, y_dia_0, y_dia_1, 0.00, 4.15)
    add_box(bm_details, -0.17, -0.14, y_dia_0, y_dia_1, 0.00, 0.40)

    # Puerta doble de dos hojas de herrería y madera dorada (Y: 7.00 a 8.40 m, Z: 0.00 a 2.50 m)
    add_box(bm_frames, -0.18, -0.12, 7.00, 8.40, 0.00, 2.55)
    add_box(bm_wood, -0.16, -0.13, 7.05, 7.68, 0.05, 2.50)
    add_box(bm_wood, -0.16, -0.13, 7.72, 8.35, 0.05, 2.50)
    add_box(bm_details, -0.17, -0.15, 7.20, 7.53, 1.20, 1.90)
    add_box(bm_details, -0.17, -0.15, 7.87, 8.20, 1.20, 1.90)

    # Ventanal alto corrido horizontal (Y: 4.95 a 6.90 m, Z: 2.30 a 2.85 m)
    add_box(bm_frames, -0.16, -0.12, 4.95, 6.90, 2.30, 2.85)
    add_box(bm_glass, -0.14, -0.13, 5.00, 6.85, 2.35, 2.80)

    # Marquesina de concreto en voladizo (vuela 0.95 m sobre banqueta, X in [-0.95, 0.00])
    add_box(bm_canopy, -0.95, 0.00, y_dia_0, y_dia_1, 2.95, 3.25)
    add_box(bm_canopy, -0.98, -0.95, y_dia_0, y_dia_1, 2.90, 3.27)

    # Rótulo blanco en relieve Bar Turístico Diana sobre la marquesina (Z: 3.25 a 4.15 m)
    add_box(bm_frames, -0.45, -0.38, y_dia_0 + 0.15, y_dia_1 - 0.15, 3.25, 4.15)
    add_box(bm_details, -0.47, -0.44, y_dia_0 + 0.20, y_dia_1 - 0.20, 3.30, 4.10)

    # Silueta dorada 3D de Diana Cazadora con arco
    add_box(bm_details, -0.49, -0.46, y_dia_0 + 0.50, y_dia_0 + 0.75, 3.35, 4.05)
    add_box(bm_details, -0.50, -0.46, y_dia_0 + 0.45, y_dia_0 + 0.85, 3.65, 3.85)

    create_3d_text("Txt_Diana_Bar", "Bar TURISTICO", 0.22, 0.020, (-0.49, 7.20, 3.82), rot_cardenas, mats["diana_cursiva_naranja"], col)
    create_3d_text("Txt_Diana_Nom", "Diana", 0.34, 0.025, (-0.49, 7.20, 3.52), rot_cardenas, mats["diana_cursiva_naranja"], col)
    create_3d_text("Txt_Diana_Ano", "DESDE / SINCE 1957", 0.09, 0.015, (-0.49, 7.20, 3.34), rot_cardenas, mats["herreria_negra"], col)

    # -----------------------------------------------------------------------
    # CRUJÍA 3: ANNITA'S BOUTIQUE (Y: 9.10 a 14.20 m)
    # -----------------------------------------------------------------------
    y_ani_0, y_ani_1 = 9.10, 14.20

    add_box(bm_walls, -0.15, 0.00, y_ani_0, y_ani_1, 0.00, 4.15)
    add_box(bm_details, -0.18, -0.12, y_ani_0, y_ani_1, 0.00, 0.45)

    # Gran vitrina acristalada (Y: 10.30 a 14.05 m, Z: 0.45 a 2.95 m)
    add_box(bm_frames, -0.17, -0.12, 10.30, 14.05, 0.45, 0.50)
    add_box(bm_frames, -0.17, -0.12, 10.30, 14.05, 2.90, 2.95)
    add_box(bm_frames, -0.17, -0.12, 10.30, 10.35, 0.45, 2.95)
    add_box(bm_frames, -0.17, -0.12, 14.00, 14.05, 0.45, 2.95)
    add_box(bm_frames, -0.17, -0.12, 12.15, 12.20, 0.45, 2.95)
    add_box(bm_glass, -0.14, -0.13, 10.35, 14.00, 0.50, 2.90)

    for b_z in [0.8, 1.1, 1.4, 1.7, 2.0, 2.3, 2.6]:
        add_box(bm_blinds, 0.05, 0.07, 10.40, 13.95, b_z, b_z + 0.02)
    add_box(bm_details, 0.15, 0.35, 11.00, 11.35, 0.45, 1.85)
    add_box(bm_details, 0.15, 0.35, 13.00, 13.35, 0.45, 1.85)

    # Puerta vidriada (Y: 9.25 a 10.20 m)
    add_box(bm_frames, -0.17, -0.12, 9.25, 10.20, 0.00, 2.50)
    add_box(bm_glass, -0.14, -0.13, 9.30, 10.15, 0.05, 2.45)
    add_box(bm_frames, -0.17, -0.12, 9.25, 10.20, 2.50, 2.95)
    add_box(bm_glass, -0.14, -0.13, 9.30, 10.15, 2.55, 2.90)

    # Marquesina continua de concreto
    add_box(bm_canopy, -0.95, 0.00, y_ani_0, y_ani_1, 2.95, 3.25)
    add_box(bm_canopy, -0.98, -0.95, y_ani_0, y_ani_1, 2.90, 3.27)

    # Rótulo rectangular NEGRO MATE de Annita's Boutique (Z: 3.25 a 4.10 m)
    add_box(bm_frames, -0.22, -0.16, y_ani_0 + 0.10, y_ani_1 - 0.10, 3.25, 4.10)
    add_box(bm_anita_negro, -0.24, -0.20, y_ani_0 + 0.15, y_ani_1 - 0.15, 3.28, 4.07) # Fondo negro mate
    add_box(bm_anita_turq, -0.26, -0.23, 10.50, 12.80, 3.40, 3.95) # Óvalo turquesa

    create_3d_text("Txt_Anitas_Nom", "Annita's", 0.32, 0.025, (-0.27, 11.65, 3.70), rot_cardenas, mats["estuco_blanco"], col)
    create_3d_text("Txt_Anitas_Bou", "boutique", 0.11, 0.015, (-0.27, 11.65, 3.45), rot_cardenas, mats["estuco_blanco"], col)

    # Espectacular vertical de azotea 'RENTA MESAS SILLAS'
    add_box(bm_metal, -0.10, 0.20, 13.20, 13.26, 4.15, 6.85)
    add_box(bm_metal, -0.10, 0.20, 14.14, 14.20, 4.15, 6.85)
    add_box(bm_metal, -0.10, 0.20, 13.20, 14.20, 6.80, 6.86)
    add_box(bm_details, -0.05, 0.15, 13.25, 14.15, 4.20, 6.80)

    create_3d_text("Txt_Renta_Mesas_1", "RENTA", 0.28, 0.020, (-0.08, 13.70, 6.45), rot_cardenas, mats["letras_rojas"], col)
    create_3d_text("Txt_Renta_Mesas_2", "MESAS", 0.26, 0.020, (-0.08, 13.70, 5.95), rot_cardenas, mats["estuco_blanco"], col)
    create_3d_text("Txt_Renta_Mesas_3", "SILLAS", 0.24, 0.020, (-0.08, 13.70, 5.48), rot_cardenas, mats["estuco_blanco"], col)
    create_3d_text("Txt_Renta_Mesas_T1", "TELS:", 0.13, 0.015, (-0.08, 13.70, 5.12), rot_cardenas, mats["amarillo_mostaza"], col)
    create_3d_text("Txt_Renta_Mesas_T2", "654-4036", 0.14, 0.015, (-0.08, 13.70, 4.78), rot_cardenas, mats["estuco_blanco"], col)
    create_3d_text("Txt_Renta_Mesas_T3", "654-0853", 0.14, 0.015, (-0.08, 13.70, 4.45), rot_cardenas, mats["estuco_blanco"], col)

    # -----------------------------------------------------------------------
    # CRUJÍA 4: PARTY RENTALS (KUROKY) (Y: 14.20 a 19.30 m)
    # -----------------------------------------------------------------------
    y_par_0, y_par_1 = 14.20, 19.30

    add_box(bm_walls, -0.15, 0.00, y_par_0, y_par_1, 0.00, 4.15)
    add_box(bm_details, -0.17, -0.12, y_par_0, y_par_1, 0.00, 0.45)

    # Ventanal comercial con notas musicales (Y: 15.80 a 17.70 m, Z: 0.50 a 2.95 m)
    add_box(bm_frames, -0.16, -0.12, 15.80, 17.70, 0.50, 2.95)
    add_box(bm_glass, -0.14, -0.13, 15.85, 17.65, 0.55, 2.90)
    for ny in [16.2, 16.7, 17.2]:
        add_box(bm_details, -0.15, -0.135, ny, ny + 0.12, 1.80, 1.95)
        add_box(bm_details, -0.15, -0.135, ny + 0.10, ny + 0.12, 1.95, 2.30)

    # Puerta de acceso de Party Rentals (Y: 17.80 a 18.80 m)
    add_box(bm_frames, -0.16, -0.12, 17.80, 18.80, 0.00, 2.50)
    add_box(bm_glass, -0.14, -0.13, 17.85, 18.75, 0.05, 2.45)

    # Cartelera comunitaria a la izquierda (Y: 14.40 a 15.60 m)
    add_box(bm_frames, -0.18, -0.14, 14.40, 15.60, 0.80, 2.50)
    add_box(bm_details, -0.19, -0.17, 14.45, 15.55, 0.85, 2.45)

    # Dos buzones / mostradores amarillos prismáticos sobre banqueta
    add_box(bm_details, -0.65, -0.30, 15.10, 15.55, 0.00, 1.05)
    add_box(bm_details, -0.65, -0.30, 15.70, 16.15, 0.00, 1.05)

    # Marquesina continua de concreto
    add_box(bm_canopy, -0.95, 0.00, y_par_0, y_par_1, 2.95, 3.25)
    add_box(bm_canopy, -0.98, -0.95, y_par_0, y_par_1, 2.90, 3.27)

    # Rótulo de Party Rentals en fascia
    add_box(bm_frames, -0.22, -0.16, y_par_0 + 0.10, y_par_1 - 0.10, 3.25, 4.10)
    add_box(bm_party_panel, -0.24, -0.20, y_par_0 + 0.15, y_par_1 - 0.15, 3.28, 4.07)
    add_box(bm_details, -0.26, -0.22, 14.30, 15.60, 3.35, 4.02)

    create_3d_text("Txt_Party_Main", "PARTY RENTALS", 0.28, 0.025, (-0.26, 17.50, 3.82), rot_cardenas, mats["verde_party"], col)
    create_3d_text("Txt_Party_Kur", "kuroky", 0.22, 0.020, (-0.26, 17.50, 3.52), rot_cardenas, mats["morado_kuroky"], col)
    create_3d_text("Txt_Party_Sonido", "SONIDO - LUCES - PANTALLAS", 0.08, 0.015, (-0.26, 16.30, 3.75), rot_cardenas, mats["azul_comercial"], col)
    create_3d_text("Txt_Party_Mesas", "MESAS - SILLAS - MANTELES", 0.08, 0.015, (-0.26, 18.70, 3.75), rot_cardenas, mats["azul_comercial"], col)
    create_3d_text("Txt_Party_Tels", "TELS. 654-4036 / 654-0853", 0.09, 0.015, (-0.26, 17.50, 3.32), rot_cardenas, mats["herreria_negra"], col)

    # Caseta de madera en azotea
    add_box(bm_wood, 1.50, 3.50, 16.20, 18.20, 3.30, 4.35)
    add_box(bm_canopy, 1.30, 3.70, 16.00, 18.40, 4.35, 4.45)

    # -----------------------------------------------------------------------
    # CRUJÍA 5: FLORERÍA ORQUÍDEA (OCHAVA ESQUINERA) (Y: 19.30 a 24.50 m)
    # -----------------------------------------------------------------------
    p_orq_a = (0.00, 21.50)
    p_orq_b = (3.80, 24.50)
    dx_o = p_orq_b[0] - p_orq_a[0] # +3.80
    dy_o = p_orq_b[1] - p_orq_a[1] # +3.00
    len_och = math.hypot(dx_o, dy_o) # ~4.84 m
    t_och = (dx_o / len_och, dy_o / len_och)
    # Normal exterior hacia afuera: (-dy/L, dx/L) = (-0.619, +0.785)
    n_och = (-dy_o / len_och, dx_o / len_och)
    c_och = ((p_orq_a[0] + p_orq_b[0]) * 0.5, (p_orq_a[1] + p_orq_b[1]) * 0.5)

    # Muro base de ochava en estuco blanco
    add_oriented_box(bm_walls, c_och, t_och, n_och, -len_och*0.5, len_och*0.5, -0.30, 0.00, 0.00, 4.15)

    # Frontón Art Déco con MOSAICO VERDE ESMERALDA DEDICADO
    add_oriented_box(bm_mosaico, c_och, t_och, n_och, -len_och*0.48, len_och*0.48, -0.05, 0.05, 4.10, 5.80)
    # Moldura perimetral blanca ascendente en inglete
    add_oriented_box(bm_canopy, c_och, t_och, n_och, -len_och*0.52, -len_och*0.46, -0.10, 0.12, 4.10, 5.85)
    add_oriented_box(bm_canopy, c_och, t_och, n_och, len_och*0.46, len_och*0.52, -0.10, 0.12, 4.10, 5.85)
    add_oriented_box(bm_canopy, c_och, t_och, n_och, -len_och*0.50, len_och*0.50, -0.10, 0.14, 5.75, 5.92)

    # Rótulo de Florería Orquídea sobre el mosaico verde
    add_oriented_box(bm_details, c_och, t_och, n_och, -1.50, 1.50, 0.06, 0.12, 4.40, 5.40)

    # REGLA RIGUROSA ANTI-ESPEJO EN OCHAVA:
    # Para que el observador situado de frente en la calle vea el texto de izquierda a derecha:
    # Eje X local = vector de lectura de izquierda a derecha.
    # El observador mira en la dirección opuesta a la normal (-n_och).
    # Su vector horizontal "a su derecha" es (0, 0, 1) x (-n_och) = (n_y, -n_x, 0) = -t_och.
    # Por tanto, el vector de lectura de izquierda a derecha es: (-t_och[0], -t_och[1], 0).
    m_rot_och = Matrix([
        [-t_och[0], 0.0, n_och[0], 0.0],
        [-t_och[1], 0.0, n_och[1], 0.0],
        [0.0,       1.0, 0.0,      0.0],
        [0.0,       0.0, 0.0,      1.0]
    ])
    rot_och_euler = m_rot_och.to_euler()

    pos_txt_orq1 = (c_och[0] + 0.15 * n_och[0], c_och[1] + 0.15 * n_och[1], 5.08)
    pos_txt_orq2 = (c_och[0] + 0.15 * n_och[0], c_och[1] + 0.15 * n_och[1], 4.72)
    pos_txt_orq3 = (c_och[0] + 0.15 * n_och[0], c_och[1] + 0.15 * n_och[1], 4.45)
    create_3d_text("Txt_Orquidea_1", "FLORERIA", 0.28, 0.025, pos_txt_orq1, rot_och_euler, mats["orquidea_fucsia"], col)
    create_3d_text("Txt_Orquidea_2", "ORQUIDEA", 0.32, 0.025, pos_txt_orq2, rot_och_euler, mats["orquidea_fucsia"], col)
    create_3d_text("Txt_Orquidea_Tel", "Tel: 654-10-51", 0.11, 0.015, pos_txt_orq3, rot_och_euler, mats["herreria_negra"], col)

    # Puerta esquinera doble de aluminio blanco vidriada
    add_oriented_box(bm_frames, c_och, t_och, n_och, -1.00, 1.00, -0.05, 0.02, 0.00, 2.50)
    add_oriented_box(bm_glass, c_och, t_och, n_och, -0.92, 0.92, -0.02, 0.00, 0.05, 2.45)

    # Teléfono público rojo en pedestal
    p_tel = (c_och[0] + 1.20 * n_och[0] + 0.80 * t_och[0], c_och[1] + 1.20 * n_och[1] + 0.80 * t_och[1])
    add_box(bm_metal, p_tel[0] - 0.05, p_tel[0] + 0.05, p_tel[1] - 0.05, p_tel[1] + 0.05, 0.00, 1.10)
    add_box(bm_details, p_tel[0] - 0.18, p_tel[0] + 0.18, p_tel[1] - 0.15, p_tel[1] + 0.15, 1.10, 1.65)

    # Losa de azotea asfáltica hermética continua
    add_box(bm_roof, 0.00, 16.50, 0.00, 24.50, 3.20, 3.35)

    obj_w = create_mesh_object("Cardenas_Walls", bm_walls, mats["estuco_marfil"], col)
    obj_z = create_mesh_object("Cardenas_Zocalo", bm_zocalo, mats["zocalo_basal"], col)
    obj_c = create_mesh_object("Cardenas_Canopy", bm_canopy, mats["concreto_marquesina"], col)
    obj_f = create_mesh_object("Cardenas_Frames", bm_frames, mats["canceleria_alum"], col)
    obj_g = create_mesh_object("Cardenas_Glass", bm_glass, mats["vidrio_reflect"], col)
    obj_b = create_mesh_object("Cardenas_Blinds", bm_blinds, mats["persianas"], col)
    obj_m = create_mesh_object("Cardenas_Metal", bm_metal, mats["herreria_negra"], col)
    obj_wd = create_mesh_object("Cardenas_Wood", bm_wood, mats["madera_puerta"], col)
    obj_d = create_mesh_object("Cardenas_Details", bm_details, mats["estuco_blanco"], col)
    obj_r = create_mesh_object("Cardenas_Roof", bm_roof, mats["azotea_asfalto"], col)
    obj_mos = create_mesh_object("Cardenas_Mosaico", bm_mosaico, mats["mosaico_verde"], col)
    obj_an = create_mesh_object("Cardenas_Anita_Panel", bm_anita_negro, mats["anita_negro"], col)
    obj_at = create_mesh_object("Cardenas_Anita_Oval", bm_anita_turq, mats["anita_turquesa"], col)
    obj_pp = create_mesh_object("Cardenas_Party_Panel", bm_party_panel, mats["diana_blanco"], col)

    return [obj_w, obj_z, obj_c, obj_f, obj_g, obj_b, obj_m, obj_wd, obj_d, obj_r, obj_mos, obj_an, obj_at, obj_pp]

# ---------------------------------------------------------------------------
# 4. Modelado Fachada Norte (Callejón Libertad: X = 3.80 a 16.50 m, Y = 24.50 m)
# ---------------------------------------------------------------------------

def build_libertad_facade(mats, col):
    """Construye el ala de Florería Orquídea sobre Libertad y Foto Estudio Curiel completo."""

    bm_walls = bmesh.new()
    bm_stone = bmesh.new()
    bm_canopy = bmesh.new()
    bm_frames = bmesh.new()
    bm_glass = bmesh.new()
    bm_metal = bmesh.new()
    bm_details = bmesh.new()

    y_lib = 24.50

    # 1. FLORERÍA ORQUÍDEA (ALA LIBERTAD: X in [3.80, 9.20 m])
    add_box(bm_stone, 3.80, 9.20, y_lib - 0.05, y_lib + 0.15, 0.00, 0.70)
    add_box(bm_walls, 3.80, 9.20, y_lib - 0.30, y_lib, 0.70, 3.35)
    add_box(bm_canopy, 3.80, 9.20, y_lib - 0.35, y_lib + 0.18, 3.25, 3.40)

    add_box(bm_frames, 4.10, 6.30, y_lib - 0.08, y_lib + 0.02, 0.70, 2.85)
    add_box(bm_glass, 4.15, 6.25, y_lib - 0.04, y_lib, 0.75, 2.80)
    add_box(bm_frames, 6.60, 8.90, y_lib - 0.08, y_lib + 0.02, 0.70, 2.85)
    add_box(bm_glass, 6.65, 8.85, y_lib - 0.04, y_lib, 0.75, 2.80)
    add_box(bm_details, 4.40, 5.00, y_lib - 0.40, y_lib - 0.15, 0.70, 1.40)
    add_box(bm_details, 7.00, 7.60, y_lib - 0.40, y_lib - 0.15, 0.70, 1.40)

    # 2. FOTO ESTUDIO CURIEL (X in [9.20, 16.50 m])
    add_box(bm_walls, 9.20, 16.50, y_lib - 0.30, y_lib, 0.00, 4.30)
    add_box(bm_stone, 9.20, 16.50, y_lib - 0.32, y_lib + 0.05, 0.00, 0.40)

    # Marquesina Streamline Art Déco con 3 estrías redondeadas
    add_box(bm_canopy, 9.20, 16.50, y_lib, y_lib + 0.90, 2.90, 3.20)
    add_box(bm_canopy, 9.20, 16.55, y_lib + 0.90, y_lib + 0.94, 2.92, 2.98)
    add_box(bm_canopy, 9.20, 16.55, y_lib + 0.90, y_lib + 0.94, 3.02, 3.08)
    add_box(bm_canopy, 9.20, 16.55, y_lib + 0.90, y_lib + 0.94, 3.12, 3.18)

    # Puerta de acceso de Foto Estudio Curiel
    add_box(bm_frames, 14.70, 16.00, y_lib - 0.12, y_lib + 0.02, 0.00, 2.50)
    add_box(bm_metal, 14.75, 15.95, y_lib - 0.08, y_lib - 0.02, 0.05, 2.45)
    add_box(bm_glass, 14.80, 15.90, y_lib - 0.10, y_lib - 0.06, 0.10, 2.40)

    # Ventanal lateral
    add_box(bm_frames, 10.00, 14.20, y_lib - 0.10, y_lib + 0.02, 0.60, 2.70)
    add_box(bm_glass, 10.05, 14.15, y_lib - 0.06, y_lib - 0.02, 0.65, 2.65)

    # Rotación para normal Norte exterior n = (0, +1, 0): (90º, 0, 180º)
    rot_libertad = (math.radians(90.0), 0.0, math.radians(180.0))
    create_3d_text("Txt_Curiel_Pared1", "FOTO STUDIO", 0.18, 0.015, (13.50, y_lib + 0.03, 2.55), rot_libertad, mats["letras_rojas"], col)
    create_3d_text("Txt_Curiel_Pared2", "CURIEL", 0.22, 0.015, (13.50, y_lib + 0.03, 2.30), rot_libertad, mats["letras_rojas"], col)

    create_3d_text("Txt_Curiel_3D_Top", "FOTO STUDIO", 0.32, 0.035, (12.80, y_lib + 0.05, 3.85), rot_libertad, mats["azul_curiel_3d"], col)
    create_3d_text("Txt_Curiel_3D_Bot", "CURIEL", 0.38, 0.040, (12.80, y_lib + 0.05, 3.42), rot_libertad, mats["diana_oro"], col)

    # Tótem vertical rojo saliente a 90º (perpendicular a Libertad)
    add_box(bm_metal, 16.38, 16.44, y_lib + 0.85, y_lib + 0.95, 0.00, 3.80)
    add_box(bm_details, 16.36, 16.46, y_lib + 0.95, y_lib + 2.10, 2.20, 3.75)
    
    # Cara Oeste del tótem (mira hacia el poniente / estacionamiento, normal = (+1, 0, 0) local):
    rot_totem_w = (math.radians(90.0), 0.0, math.radians(-90.0))
    create_3d_text("Txt_Totem_W1", "FOTO STUDIO", 0.16, 0.015, (16.34, y_lib + 1.50, 3.40), rot_totem_w, mats["estuco_blanco"], col)
    create_3d_text("Txt_Totem_W2", "CURIEL", 0.22, 0.015, (16.34, y_lib + 1.50, 2.80), rot_totem_w, mats["diana_oro"], col)
    
    # Cara Este del tótem (mira hacia Cárdenas / oriente, normal = (+1, 0, 0)):
    rot_totem_e = (math.radians(90.0), 0.0, math.radians(90.0))
    create_3d_text("Txt_Totem_E1", "FOTO STUDIO", 0.16, 0.015, (16.48, y_lib + 1.50, 3.40), rot_totem_e, mats["estuco_blanco"], col)
    create_3d_text("Txt_Totem_E2", "CURIEL", 0.22, 0.015, (16.48, y_lib + 1.50, 2.80), rot_totem_e, mats["diana_oro"], col)

    # Caseta técnica de azotea
    add_box(bm_walls, 11.20, 14.80, y_lib - 3.50, y_lib - 0.80, 3.35, 4.55)
    add_box(bm_canopy, 11.00, 15.00, y_lib - 3.70, y_lib - 0.60, 4.55, 4.65)

    obj_lw = create_mesh_object("Libertad_Walls", bm_walls, mats["estuco_blanco"], col)
    obj_ls = create_mesh_object("Libertad_Stone", bm_stone, mats["cantera_rustica"], col)
    obj_lc = create_mesh_object("Libertad_Canopy", bm_canopy, mats["concreto_marquesina"], col)
    obj_lf = create_mesh_object("Libertad_Frames", bm_frames, mats["canceleria_alum"], col)
    obj_lg = create_mesh_object("Libertad_Glass", bm_glass, mats["vidrio_reflect"], col)
    obj_lm = create_mesh_object("Libertad_Metal", bm_metal, mats["herreria_negra"], col)
    obj_ld = create_mesh_object("Libertad_Details", bm_details, mats["letras_rojas"], col)

    return [obj_lw, obj_ls, obj_lc, obj_lf, obj_lg, obj_lm, obj_ld]

# ---------------------------------------------------------------------------
# 5. Modelado Fachada Poniente / Reverso hacia Estacionamiento (X = 16.50 m)
# ---------------------------------------------------------------------------

def build_rear_parking_facade(mats, col):
    """Construye la fachada poniente completa visible desde el estacionamiento interior del BBVA:
    Posterior de Foto Estudio Curiel con rótulo, posterior de Bar Diana con marquesina angulada,
    puerta de servicio y terraza cercada con reja metálica negra y letrero Salida."""

    bm_walls = bmesh.new()
    bm_canopy = bmesh.new()
    bm_frames = bmesh.new()
    bm_metal = bmesh.new()
    bm_details = bmesh.new()

    x_rear = 16.50

    # 1. POSTERIOR DE FOTO ESTUDIO CURIEL (Y in [18.00, 24.50 m])
    add_box(bm_walls, x_rear - 0.30, x_rear, 18.00, 24.50, 0.00, 4.25)
    add_box(bm_walls, x_rear, x_rear + 0.12, 19.50, 19.80, 0.00, 4.25)
    add_box(bm_walls, x_rear, x_rear + 0.12, 21.50, 21.80, 0.00, 4.25)
    add_box(bm_walls, x_rear, x_rear + 0.12, 23.50, 23.80, 0.00, 4.25)

    rot_rear = (math.radians(90.0), 0.0, math.radians(90.0))
    create_3d_text("Txt_Curiel_Rear1", "FOTO STUDIO", 0.22, 0.020, (x_rear + 0.02, 21.20, 3.85), rot_rear, mats["azul_curiel_3d"], col)
    create_3d_text("Txt_Curiel_Rear2", "CURIEL", 0.26, 0.020, (x_rear + 0.02, 21.20, 3.50), rot_rear, mats["diana_oro"], col)

    # Acometida eléctrica
    add_box(bm_frames, x_rear + 0.02, x_rear + 0.18, 23.90, 24.30, 1.20, 2.10)

    # 2. POSTERIOR DE BAR TURÍSTICO DIANA (Y in [6.50, 18.00 m])
    add_box(bm_walls, x_rear - 0.30, x_rear, 6.50, 18.00, 0.00, 3.80)
    add_box(bm_canopy, x_rear, x_rear + 0.85, 8.50, 17.50, 2.90, 3.20)
    add_box(bm_canopy, x_rear + 0.85, x_rear + 0.90, 8.50, 17.50, 2.85, 3.22)

    # Puerta metálica de servicio
    add_box(bm_frames, x_rear - 0.05, x_rear + 0.05, 14.50, 15.60, 0.00, 2.45)
    add_box(bm_metal, x_rear + 0.01, x_rear + 0.04, 14.55, 15.55, 0.05, 2.40)

    # Ventanal posterior
    add_box(bm_frames, x_rear - 0.05, x_rear + 0.05, 11.20, 13.50, 1.20, 2.50)

    create_3d_text("Txt_Diana_Rear", "BAR TURISTICO Diana", 0.26, 0.025, (x_rear + 0.03, 13.00, 3.48), rot_rear, mats["diana_cursiva_naranja"], col)

    # 3. TERRAZA / CORRALÓN DE SERVICIO CERCADO CON REJA METÁLICA NEGRA
    add_box(bm_canopy, 16.50, 20.80, 6.95, 7.05, 0.00, 0.20)
    add_box(bm_canopy, 20.75, 20.85, 7.00, 14.00, 0.00, 0.20)
    add_box(bm_canopy, 16.50, 20.80, 13.95, 14.05, 0.00, 0.20)

    for bx in [16.6, 17.0, 17.4, 17.8, 18.2, 18.6, 19.0, 19.4, 19.8, 20.2, 20.6]:
        add_box(bm_metal, bx - 0.02, bx + 0.02, 13.98, 14.02, 0.20, 1.80)
    add_box(bm_metal, 16.50, 20.80, 13.97, 14.03, 1.78, 1.84)

    for by in [7.2, 7.6, 8.0, 8.4, 8.8, 9.2, 9.6, 10.0, 11.5, 11.9, 12.3, 12.7, 13.1, 13.5, 13.9]:
        add_box(bm_metal, 20.78, 20.82, by - 0.02, by + 0.02, 0.20, 1.80)
    add_box(bm_metal, 20.77, 20.83, 7.00, 20.80, 1.78, 1.84)

    add_box(bm_metal, 20.76, 20.84, 10.20, 11.30, 0.10, 2.05)
    add_box(bm_details, 20.83, 20.87, 10.45, 11.05, 1.45, 1.70)
    create_3d_text("Txt_Salida_Reja", "Salida", 0.12, 0.015, (20.89, 10.75, 1.57), rot_rear, mats["estuco_blanco"], col)

    for bx in [16.6, 17.0, 17.4, 17.8, 18.2, 18.6, 19.0, 19.4, 19.8, 20.2, 20.6]:
        add_box(bm_metal, bx - 0.02, bx + 0.02, 6.98, 7.02, 0.20, 1.80)
    add_box(bm_metal, 16.50, 20.80, 6.97, 7.03, 1.78, 1.84)

    # 4. MEDIANERA SUR CONTINUA ENRASADA CON BBVA DENTISTA (Y = 0.00 m)
    add_box(bm_walls, 0.00, 16.50, -0.05, 0.05, 0.00, 4.15)

    obj_rw = create_mesh_object("Rear_Walls", bm_walls, mats["estuco_blanco"], col)
    obj_rc = create_mesh_object("Rear_Canopy", bm_canopy, mats["concreto_marquesina"], col)
    obj_rf = create_mesh_object("Rear_Frames", bm_frames, mats["canceleria_alum"], col)
    obj_rm = create_mesh_object("Rear_Metal", bm_metal, mats["herreria_negra"], col)
    obj_rd = create_mesh_object("Rear_Details", bm_details, mats["azul_comercial"], col)

    return [obj_rw, obj_rc, obj_rf, obj_rm, obj_rd]

# ---------------------------------------------------------------------------
# 6. Configuración de Iluminación y Cámaras Cycles Headless
# ---------------------------------------------------------------------------

def setup_lighting_and_cameras(col):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    if hasattr(scene.cycles, 'device'):
        scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.film_transparent = False

    # Sol diurno frontal desde Cárdenas (-X, -Y, +Z)
    sun_data = bpy.data.lights.new(name="Sun_Diurno", type='SUN')
    sun_data.energy = 5.2
    sun_data.color = (1.0, 0.98, 0.94)
    sun_obj = bpy.data.objects.new("Sun_Diurno", sun_data)
    col.objects.link(sun_obj)
    sun_obj.location = (-28.0, 5.0, 28.0)
    sun_obj.rotation_euler = (math.radians(35.0), math.radians(-25.0), math.radians(-40.0))

    # Luz de relleno suave desde el cielo y poniente (+X, +Y, +Z)
    fill_data = bpy.data.lights.new(name="Fill_Sky", type='SUN')
    fill_data.energy = 2.8
    fill_data.color = (0.80, 0.88, 1.0)
    fill_obj = bpy.data.objects.new("Fill_Sky", fill_data)
    col.objects.link(fill_obj)
    fill_obj.location = (25.0, 35.0, 25.0)
    fill_obj.rotation_euler = (math.radians(45.0), math.radians(20.0), math.radians(145.0))

    # Luz de ambiente cenital
    hemi_data = bpy.data.lights.new(name="Hemi_Ambient", type='SUN')
    hemi_data.energy = 1.6
    hemi_data.color = (0.92, 0.94, 0.96)
    hemi_obj = bpy.data.objects.new("Hemi_Ambient", hemi_data)
    col.objects.link(hemi_obj)
    hemi_obj.location = (0.0, 0.0, 40.0)
    hemi_obj.rotation_euler = (0.0, 0.0, 0.0)

    # Batería de 6 cámaras fijas canónicas de validación closed-loop
    cams_config = [
        # 1. Frontal completa sobre Cárdenas (Librería España a Florería Orquídea)
        ("Cam_Cardenas_Frontal", (-18.5, 12.25, 2.2), (0.0, 12.25, 2.4), 22),
        # 2. Ochava a 45º esquina Florería Orquídea y Callejón Libertad
        ("Cam_Esquina_Ochava", (-11.0, 30.5, 2.3), (1.9, 23.0, 2.8), 26),
        # 3. Frontal de Foto Estudio Curiel sobre Callejón Libertad
        ("Cam_Libertad_Curiel", (12.8, 33.5, 2.0), (12.8, 24.5, 2.4), 24),
        # 4. Vista de fachada posterior desde el estacionamiento BBVA
        ("Cam_Reverso_Estacionamiento", (26.5, 14.5, 2.3), (16.5, 14.5, 2.2), 24),
        # 5. Acercamiento rasante a los letreros de Bar Diana y Annita's Boutique
        ("Cam_Closeup_Rotulos", (-6.5, 9.5, 3.2), (0.0, 9.5, 3.4), 32),
        # 6. Vista cenital superior de azoteas herméticas (Z = 45 m)
        ("Cam_Cenital_Azotea", (8.25, 12.25, 42.0), (8.25, 12.25, 0.0), 20),
    ]

    cams = {}
    for cam_name, pos, tgt, lens in cams_config:
        c_data = bpy.data.cameras.new(cam_name)
        c_data.lens = lens
        c_obj = bpy.data.objects.new(cam_name, c_data)
        col.objects.link(c_obj)
        c_obj.location = Vector(pos)
        direction = Vector(tgt) - Vector(pos)
        c_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        cams[cam_name] = c_obj

    return cams

# ---------------------------------------------------------------------------
# 7. Generación de Escena Godot 4 (.tscn) con Colisiones Analíticas
# ---------------------------------------------------------------------------

def generate_godot_tscn(tscn_path, glb_path_rel):
    """Genera la escena de Godot 4 con colisionadores BoxShape3D analíticos transitables."""
    tscn_content = f"""[gd_scene load_steps=10 format=3 uid="uid://cardenas_33_locales_001"]

[ext_resource type="PackedScene" path="{glb_path_rel}" id="1_mesh"]

[sub_resource type="BoxShape3D" id="BoxShape3D_libreria"]
size = Vector3(16.5, 4.5, 4.8)

[sub_resource type="BoxShape3D" id="BoxShape3D_diana"]
size = Vector3(16.5, 4.5, 4.3)

[sub_resource type="BoxShape3D" id="BoxShape3D_anita"]
size = Vector3(16.5, 4.5, 5.1)

[sub_resource type="BoxShape3D" id="BoxShape3D_party"]
size = Vector3(16.5, 4.5, 5.1)

[sub_resource type="BoxShape3D" id="BoxShape3D_orquidea"]
size = Vector3(9.2, 4.5, 5.2)

[sub_resource type="BoxShape3D" id="BoxShape3D_curiel"]
size = Vector3(7.3, 4.5, 6.5)

[sub_resource type="BoxShape3D" id="BoxShape3D_terraza"]
size = Vector3(4.3, 2.0, 7.0)

[node name="Edificio_Cardenas_33" type="StaticBody3D"]

[node name="ModelInstance" parent="." instance=ExtResource("1_mesh")]

[node name="Col_Libreria" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 8.25, 2.25, -2.40)
shape = SubResource("BoxShape3D_libreria")

[node name="Col_Diana" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 8.25, 2.25, -6.95)
shape = SubResource("BoxShape3D_diana")

[node name="Col_Anita" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 8.25, 2.25, -11.65)
shape = SubResource("BoxShape3D_anita")

[node name="Col_Party" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 8.25, 2.25, -16.75)
shape = SubResource("BoxShape3D_party")

[node name="Col_Orquidea" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 4.60, 2.25, -21.90)
shape = SubResource("BoxShape3D_orquidea")

[node name="Col_Curiel" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 12.85, 2.25, -21.25)
shape = SubResource("BoxShape3D_curiel")

[node name="Col_Terraza_Reja" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 18.65, 1.00, -10.50)
shape = SubResource("BoxShape3D_terraza")
"""
    with open(tscn_path, "w", encoding="utf-8") as f:
        f.write(tscn_content)
    print(f"[OK] Escena Godot generada: {tscn_path}")

# ---------------------------------------------------------------------------
# 8. Función Principal de Generación y Ejecución
# ---------------------------------------------------------------------------

def main():
    print("=== INICIANDO RECONSTRUCCIÓN PROCEDURAL: PDTE. LÁZARO CÁRDENAS 33 V3.0 ===")
    root_col = clean_scene()
    mats = create_materials()

    # 1. Construir las 3 fachadas principales y reverso
    objs_cardenas = build_cardenas_facade(mats, root_col)
    objs_libertad = build_libertad_facade(mats, root_col)
    objs_rear = build_rear_parking_facade(mats, root_col)
    print(f"[OK] Cuerpos arquitectónicos construidos ({len(objs_cardenas) + len(objs_libertad) + len(objs_rear)} objetos)")

    # 2. Configurar iluminación y batería de validación
    cams = setup_lighting_and_cameras(root_col)
    print(f"[OK] Cámaras y luces Cycles configuradas ({len(cams)} cámaras)")

    # Rutas absolutas del proyecto
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    blend_path = os.path.join(base_dir, "blender_assets", "buildings", "edificio_cardenas_33.blend")
    glb_path = os.path.join(base_dir, "godot_project", "assets", "buildings", "edificio_cardenas_33.glb")
    tscn_path = os.path.join(base_dir, "godot_project", "assets", "buildings", "edificio_cardenas_33.tscn")
    images_dir = os.path.join(base_dir, "docs", "images", "cardenas_33")
    os.makedirs(images_dir, exist_ok=True)

    # 3. Guardar archivo maestro .blend
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"[OK] Archivo maestro Blender guardado: {blend_path}")

    # 4. Exportar runtime GLB para Godot (excluyendo cámaras y luces)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in root_col.objects:
        if obj.type in ['MESH', 'FONT']:
            obj.select_set(True)

    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        use_selection=True,
        export_format='GLB',
        export_apply=True,
        export_yup=True
    )
    print(f"[OK] Runtime GLB exportado: {glb_path}")

    # 5. Generar archivo de escena Godot 4 .tscn
    generate_godot_tscn(tscn_path, "res://assets/buildings/edificio_cardenas_33.glb")

    # 6. Renderizar batería de 6 imágenes de validación closed-loop
    scene = bpy.context.scene
    for cam_name, cam_obj in cams.items():
        render_output = os.path.join(images_dir, f"{cam_name}.png")
        scene.camera = cam_obj
        scene.render.filepath = render_output
        print(f"Renderizando {cam_name} -> {render_output}...")
        bpy.ops.render.render(write_still=True)
        print(f"[OK] Render completado: {render_output}")

    print("=== RECONSTRUCCIÓN PROCEDURAL COMPLETADA EXITOSAMENTE V3.0 ===")

if __name__ == "__main__":
    main()
