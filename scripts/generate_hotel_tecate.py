"""
=============================================================================
GENERADOR PROCEDURAL 3D UNIVERSAL: HOTEL TECATE (ÉPOCA HISTÓRICA 2009)
=============================================================================
Reconstrucción fidedigna con consenso multi-perspectiva y verdad de terreno histórica (2009):
  - Ubicación: Pdte. Lázaro Cárdenas 133 / Callejón Libertad, Centro, Tecate, B.C.
  - Frente al Parque Miguel Hidalgo.
  - Coordenadas geográficas: 32.572763, -116.626927

Contrato Cartesiano Canónico (Primer Cuadrante Ortogonal):
  - Origen (0,0,0): Intersección proyectada de alineaciones de fachada
                    (Calle Lázaro Cárdenas y Callejón Libertad)
  - Eje +X: Hacia el Sur (paralelo a Calle Presidente Lázaro Cárdenas, longitud 28.60 m)
  - Eje +Y: Hacia el Oriente (paralelo a Callejón Libertad / Parque Hidalgo, longitud 20.40 m)
  - Eje +Z: Cota vertical (Normal de suelo hacia el cenit)
  - Zócalo basal enterrado: Z en [-1.20 m, 0.00 m] para absorción topográfica sin flotar.

Ejecución headless:
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/generate_hotel_tecate.py
=============================================================================
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Euler

# ---------------------------------------------------------------------------
# 1. Utilidades y Configuración de Escena
# ---------------------------------------------------------------------------

def clean_scene():
    """Inicializa la escena vacía y crea la colección raíz."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)
    root_col = bpy.data.collections.new("Hotel_Tecate_Root")
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
    bm.faces.new((verts[0], verts[1], verts[2], verts[3])) # -Z Bottom
    bm.faces.new((verts[4], verts[7], verts[6], verts[5])) # +Z Top
    bm.faces.new((verts[0], verts[4], verts[5], verts[1])) # -Y
    bm.faces.new((verts[1], verts[5], verts[6], verts[2])) # +X
    bm.faces.new((verts[2], verts[6], verts[7], verts[3])) # +Y
    bm.faces.new((verts[3], verts[7], verts[4], verts[0])) # -X
    return verts

def add_oriented_box(bm, center_xy, tangent_xy, normal_xy, s_min, s_max, n_min, n_max, z_min, z_max):
    """Construye una caja orientada según un marco ortonormal 2D."""
    verts = []
    for s in (s_min, s_max):
        for n in (n_min, n_max):
            for z in (z_min, z_max):
                vx = center_xy[0] + s * tangent_xy[0] + n * normal_xy[0]
                vy = center_xy[1] + s * tangent_xy[1] + n * normal_xy[1]
                verts.append(bm.verts.new((vx, vy, z)))
    faces = [
        (0, 1, 3, 2), (4, 6, 7, 5), # Tapas longitudinales
        (0, 4, 5, 1), (2, 3, 7, 6), # Caras interior / exterior
        (0, 2, 6, 4), (1, 5, 7, 3)  # Tapas inferior / superior
    ]
    for f in faces:
        bm.faces.new((verts[f[0]], verts[f[1]], verts[f[2]], verts[f[3]]))
    return verts

def create_mesh_object(name, bm, mat, col):
    """Crea un objeto Mesh en Blender a partir de un BMesh y asigna su material."""
    me = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(me)
    bm.free()
    me.update()
    obj = bpy.data.objects.new(name, me)
    if mat:
        obj.data.materials.append(mat)
    col.objects.link(obj)
    return obj

def create_3d_text(name, text_string, size, extrude, mat, col):
    """Crea una entidad de texto 3D con espesor y material."""
    t_curve = bpy.data.curves.new(type="FONT", name=name + "_Curve")
    t_curve.body = text_string
    t_curve.size = size
    t_curve.extrude = extrude
    t_curve.align_x = 'CENTER'
    t_curve.align_y = 'CENTER'
    obj = bpy.data.objects.new(name, t_curve)
    if mat:
        obj.data.materials.append(mat)
    col.objects.link(obj)
    return obj

# ---------------------------------------------------------------------------
# 2. Creación de la Paleta de Materiales PBR
# ---------------------------------------------------------------------------

def create_materials():
    """Genera todos los materiales PBR calibrados para la época histórica 2009."""
    mats = {}

    def _make_mat(name, color, rough=0.8, metal=0.0, transmission=0.0, ior=1.45):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = color
            bsdf.inputs["Roughness"].default_value = rough
            bsdf.inputs["Metallic"].default_value = metal
            if "Transmission Weight" in bsdf.inputs:
                bsdf.inputs["Transmission Weight"].default_value = transmission
            elif "Transmission" in bsdf.inputs:
                bsdf.inputs["Transmission"].default_value = transmission
            bsdf.inputs["IOR"].default_value = ior
        return mat

    # 1. Estuco Terracota / Salmón Principal del Hotel Tecate (2009 Ground Truth)
    m_stucco = _make_mat("M_Estuco_Terracota", (0.83, 0.46, 0.31, 1.0), rough=0.88)
    nodes = m_stucco.node_tree.nodes
    links = m_stucco.node_tree.links
    bsdf_st = nodes.get("Principled BSDF")
    if bsdf_st:
        tex_noise = nodes.new('ShaderNodeTexNoise')
        tex_noise.inputs['Scale'].default_value = 180.0
        bump_st = nodes.new('ShaderNodeBump')
        bump_st.inputs['Strength'].default_value = 0.20
        links.new(tex_noise.outputs['Fac'], bump_st.inputs['Height'])
        links.new(bump_st.outputs['Normal'], bsdf_st.inputs['Normal'])
    mats["estuco"] = m_stucco

    # 2. Zócalo Basal Subterráneo (Concreto Grafito Oscuro)
    mats["zocalo"] = _make_mat("M_Zocalo_Basal", (0.05, 0.05, 0.055, 1.0), rough=0.92)

    # 3. Mampostería Molduras / Remate Beige Claro
    mats["moldura"] = _make_mat("M_Moldura_Beige", (0.88, 0.85, 0.78, 1.0), rough=0.75)

    # 4. Cancelería Aluminio Blanco (Ventanales Superiores)
    mats["alum_blanco"] = _make_mat("M_Aluminio_Blanco", (0.92, 0.92, 0.92, 1.0), rough=0.30, metal=0.10)

    # 5. Cancelería Aluminio Oscuro (Escaparates y Puertas de Acceso)
    mats["alum_oscuro"] = _make_mat("M_Aluminio_Oscuro", (0.025, 0.025, 0.028, 1.0), rough=0.25, metal=0.85)

    # 6. Vidrio Reflectante Comercial
    mats["vidrio"] = _make_mat("M_Vidrio_Comercial", (0.06, 0.10, 0.14, 1.0), rough=0.05, transmission=0.85, ior=1.52)

    # 7. Cortinas Metálicas Enrollables (Persianas de Comercios)
    mats["cortina_metalica"] = _make_mat("M_Cortina_Metalica", (0.32, 0.32, 0.33, 1.0), rough=0.50, metal=0.60)

    # 8. Pavés / Bloques de Vidrio Translúcidos (Sobre Zaguán)
    mats["paves"] = _make_mat("M_Paves_Vidrio", (0.55, 0.72, 0.76, 1.0), rough=0.35, transmission=0.70, ior=1.45)

    # 9. Hierro Forjado Negro (Barandal de Balcón)
    mats["hierro_forjado"] = _make_mat("M_Hierro_Forjado", (0.015, 0.015, 0.018, 1.0), rough=0.45, metal=0.85)

    # 10. Toldo Lona Beige Festoneada (Crujía 4)
    mats["toldo_beige"] = _make_mat("M_Toldo_Beige", (0.78, 0.72, 0.60, 1.0), rough=0.90)

    # 11. Toldo Vinílico Azul (Internet World Crujía 6)
    mats["toldo_azul"] = _make_mat("M_Toldo_Azul", (0.04, 0.18, 0.62, 1.0), rough=0.55)

    # 12. Toldo Curvo Verde (Callejón Libertad)
    mats["toldo_verde"] = _make_mat("M_Toldo_Verde", (0.05, 0.32, 0.15, 1.0), rough=0.80)

    # 13. Franquicia SUBWAY (Amarillo Dorado y Verde Institucional)
    mats["subway_amarillo"] = _make_mat("M_Subway_Amarillo", (0.98, 0.82, 0.05, 1.0), rough=0.30)
    mats["subway_verde"] = _make_mat("M_Subway_Verde", (0.02, 0.42, 0.18, 1.0), rough=0.30)

    # 14. Rótulo Hotel Tecate y Letreros
    mats["panel_blanco"] = _make_mat("M_Panel_Blanco", (0.95, 0.95, 0.95, 1.0), rough=0.25)
    mats["texto_rojo"] = _make_mat("M_Texto_Rojo", (0.85, 0.04, 0.04, 1.0), rough=0.30)
    mats["texto_azul"] = _make_mat("M_Texto_Azul", (0.05, 0.15, 0.70, 1.0), rough=0.30)
    mats["rotulo_plata"] = _make_mat("M_Rotulo_Plata", (0.80, 0.80, 0.83, 1.0), rough=0.25, metal=0.85)

    # 15. Azotea Impermeabilizada Asfáltica
    mats["azotea"] = _make_mat("M_Azotea_Asfalto", (0.04, 0.04, 0.045, 1.0), rough=0.95)

    # 16. Piso Interior Concreto Zaguán
    mats["piso_interior"] = _make_mat("M_Piso_Interior", (0.22, 0.22, 0.24, 1.0), rough=0.75)

    return mats

# ---------------------------------------------------------------------------
# 3. Construcción de Cuerpos Arquitectónicos
# ---------------------------------------------------------------------------

def build_zocalo_basal(mats, col):
    """Construye el zócalo basal subterráneo continuo (Z en [-1.20, 0.00 m])."""
    bm = bmesh.new()
    
    # 1. Zócalo Fachada Oeste (Cárdenas)
    add_box(bm, 2.80, 28.60, -0.05, 0.35, -1.20, 0.00)
    
    # 2. Zócalo Fachada Norte (Callejón Libertad)
    add_box(bm, -0.05, 0.35, 2.80, 20.40, -1.20, 0.00)
    
    # 3. Zócalo Ochava a 45º
    center_xy = (1.40, 1.40)
    tangent_xy = (-0.7071, 0.7071)
    normal_xy = (-0.7071, -0.7071)
    add_oriented_box(bm, center_xy, tangent_xy, normal_xy, -2.10, 2.10, -0.05, 0.35, -1.20, 0.00)
    
    # 4. Zócalos Medianeros (Sur y Oriente)
    add_box(bm, 28.25, 28.65, 0.00, 20.40, -1.20, 0.00)
    add_box(bm, 0.00, 28.65, 20.05, 20.45, -1.20, 0.00)
    
    return create_mesh_object("Zocalo_Basal_Subterraneo", bm, mats["zocalo"], col)

def build_west_facade_cardenas(mats, col):
    """
    Construye la Fachada Oeste sobre Calle Presidente Lázaro Cárdenas (X: 2.80 a 28.60 m).
    6 Crujías con vanos reales de fenestración superior, zaguán transitable y cancelería.
    """
    bm_wall = bmesh.new()
    bm_dark = bmesh.new()
    bm_glass = bmesh.new()
    bm_white = bmesh.new()
    bm_shutter = bmesh.new()
    bm_paves = bmesh.new()
    bm_awning_b = bmesh.new()
    bm_awning_bl = bmesh.new()
    bm_interior = bmesh.new()

    # Muro base inferior de planta alta (Antepecho Z: 3.20 a 4.55 m):
    # Crujías 1 a 4 (X: 2.80 a 20.00 m)
    add_box(bm_wall, 2.80, 20.00, 0.00, 0.35, 3.20, 4.55)
    # Crujía 6 (X: 24.80 a 28.60 m)
    add_box(bm_wall, 24.80, 28.60, 0.00, 0.35, 3.20, 4.55)

    # Muro dintel corrido sobre ventanas de planta alta (Z: 6.25 a 7.15 m):
    add_box(bm_wall, 2.80, 28.60, 0.00, 0.35, 6.25, 7.15)
    # Pretil y albardilla superior
    add_box(bm_wall, 2.80, 28.60, -0.05, 0.40, 7.05, 7.25)
    add_box(bm_wall, 2.75, 28.65, -0.08, 0.43, 7.25, 7.32)

    # Crujía 5 (ZAGUÁN TÚNEL X: 20.00 a 24.80 m):
    # PB totalmente abierta de Z = 0.0 a 3.20 m para paso vehicular/peatonal!
    # Franja de pavés / bloques de vidrio (Z: 3.20 a 3.80 m)
    add_box(bm_paves, 20.05, 24.75, 0.05, 0.30, 3.25, 3.75)
    add_box(bm_dark, 20.00, 24.80, 0.02, 0.33, 3.20, 3.25)
    add_box(bm_dark, 20.00, 24.80, 0.02, 0.33, 3.75, 3.80)
    # Antepecho zaguán (Z: 3.80 a 4.65 m)
    add_box(bm_wall, 20.00, 24.80, 0.00, 0.35, 3.80, 4.65)
    
    # Frontón escalonado ornamental central sobre el zaguán
    add_box(bm_wall, 21.80, 23.00, -0.06, 0.41, 7.25, 7.60)
    add_box(bm_wall, 22.10, 22.70, -0.08, 0.43, 7.60, 7.80)

    # Muros laterales del túnel interior
    add_box(bm_wall, 19.70, 20.00, 0.35, 10.00, 0.00, 3.50) # Muro norte túnel
    add_box(bm_wall, 24.80, 25.10, 0.35, 10.00, 0.00, 3.50) # Muro sur túnel
    add_box(bm_wall, 20.00, 24.80, 0.35, 10.00, 3.20, 3.50) # Techo túnel
    add_box(bm_interior, 20.00, 24.80, 0.00, 10.00, 0.00, 0.05) # Piso túnel

    # Pilares en PB y pilastras sobresalientes corridas hasta el pretil
    pilares_x = [
        (2.80, 3.20),   # Inicio C1
        (6.80, 7.20),   # Entre C1 y C2
        (11.10, 11.50), # Entre C2 y C3
        (15.40, 15.80), # Entre C3 y C4
        (19.60, 20.00), # Entre C4 y Túnel
        (24.80, 25.20), # Entre Túnel y C6
        (28.20, 28.60)  # Fin C6 / Medianera Sur
    ]
    for px1, px2 in pilares_x:
        add_box(bm_wall, px1, px2, 0.00, 0.35, 0.00, 3.20)
        # Pilastras adosadas
        add_box(bm_wall, px1 - 0.05, px2 + 0.05, -0.12, 0.02, 0.00, 7.55)
        add_box(bm_wall, px1 - 0.10, px2 + 0.10, -0.16, 0.05, 7.45, 7.60)

    # -----------------------------------------------------------------------
    # Machones y Ventanería en Planta Alta (Z: 4.55 a 6.25 m)
    # -----------------------------------------------------------------------

    # Crujía 1 (X: 3.20 a 6.80 m):
    add_box(bm_wall, 3.20, 3.90, 0.00, 0.35, 4.55, 6.25) # Machón izq
    add_box(bm_wall, 5.70, 6.00, 0.00, 0.35, 4.55, 6.25) # Machón centro
    add_box(bm_wall, 6.55, 6.80, 0.00, 0.35, 4.55, 6.25) # Machón der
    # Ventana 1a: Corredera doble (X: 3.90 a 5.70 m)
    add_box(bm_white, 3.90, 5.70, 0.10, 0.16, 4.55, 6.25)
    add_box(bm_white, 4.75, 4.85, 0.12, 0.18, 4.60, 6.20)
    add_box(bm_glass, 3.95, 5.65, 0.13, 0.15, 4.60, 6.20)
    # Ventana 1b: Auxiliar (X: 6.00 a 6.55 m)
    add_box(bm_white, 6.00, 6.55, 0.10, 0.16, 5.10, 5.80)
    add_box(bm_glass, 6.05, 6.50, 0.13, 0.15, 5.15, 5.75)
    # PB Crujía 1:
    add_box(bm_dark, 3.30, 6.70, 0.08, 0.12, 0.20, 2.90)
    add_box(bm_shutter, 3.35, 6.65, 0.10, 0.12, 0.25, 2.85)
    add_box(bm_white, 3.40, 4.20, -0.32, -0.02, 3.45, 4.05) # Minisplit

    # Crujía 2 (X: 7.20 a 11.10 m):
    add_box(bm_wall, 7.20, 7.80, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 9.60, 11.10, 0.00, 0.35, 4.55, 6.25)
    # Ventana 2: (X: 7.80 a 9.60 m)
    add_box(bm_white, 7.80, 9.60, 0.10, 0.16, 4.55, 6.25)
    add_box(bm_white, 8.65, 8.75, 0.12, 0.18, 4.60, 6.20)
    add_box(bm_glass, 7.85, 9.55, 0.13, 0.15, 4.60, 6.20)
    # PB Crujía 2:
    add_box(bm_dark, 7.30, 11.00, 0.08, 0.12, 0.20, 2.90)
    add_box(bm_shutter, 7.35, 10.95, 0.10, 0.12, 0.25, 2.85)
    add_box(bm_dark, 8.95, 9.35, -0.08, 0.02, 3.45, 3.85)
    add_box(bm_white, 9.00, 9.30, -0.10, -0.06, 3.50, 3.80)

    # Crujía 3 (X: 11.50 a 15.40 m):
    add_box(bm_wall, 11.50, 12.00, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 13.60, 14.10, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 15.10, 15.40, 0.00, 0.35, 4.55, 6.25)
    # Ventanas 3a y 3b:
    add_box(bm_white, 12.00, 13.60, 0.10, 0.16, 4.70, 6.20)
    add_box(bm_glass, 12.05, 13.55, 0.13, 0.15, 4.75, 6.15)
    add_box(bm_white, 14.10, 15.10, 0.10, 0.16, 4.90, 5.90)
    add_box(bm_glass, 14.15, 15.05, 0.13, 0.15, 4.95, 5.85)
    # PB Crujía 3:
    add_box(bm_dark, 11.60, 12.80, 0.06, 0.12, 0.00, 2.60)
    add_box(bm_dark, 12.90, 15.30, 0.08, 0.12, 0.20, 2.90)
    add_box(bm_shutter, 12.95, 15.25, 0.10, 0.12, 0.25, 2.85)

    # Crujía 4 (X: 15.80 a 19.60 m):
    add_box(bm_wall, 15.80, 16.20, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 17.60, 18.00, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 19.40, 19.60, 0.00, 0.35, 4.55, 6.25)
    # Ventanas gemelas 4a y 4b:
    add_box(bm_white, 16.20, 17.60, 0.10, 0.16, 4.65, 6.15)
    add_box(bm_glass, 16.25, 17.55, 0.13, 0.15, 4.70, 6.10)
    add_box(bm_white, 18.00, 19.40, 0.10, 0.16, 4.65, 6.15)
    add_box(bm_glass, 18.05, 19.35, 0.13, 0.15, 4.70, 6.10)
    # PB Crujía 4:
    add_box(bm_dark, 16.00, 19.40, 0.08, 0.12, 0.00, 2.90)
    add_box(bm_glass, 16.05, 19.35, 0.09, 0.11, 0.10, 2.80)
    add_box(bm_awning_b, 15.70, 19.70, -1.25, 0.05, 2.80, 3.35)
    add_box(bm_awning_b, 15.70, 19.70, -1.30, -1.25, 2.55, 2.80)

    # Crujía 5 (Zaguán PA X: 20.00 a 24.80 m):
    add_box(bm_wall, 20.00, 20.60, 0.00, 0.35, 4.65, 6.25)
    add_box(bm_wall, 22.00, 22.80, 0.00, 0.35, 4.65, 6.25)
    add_box(bm_wall, 24.20, 24.80, 0.00, 0.35, 4.65, 6.25)
    # Ventanas zaguán:
    add_box(bm_white, 20.60, 22.00, 0.10, 0.16, 4.65, 6.15)
    add_box(bm_glass, 20.65, 21.95, 0.13, 0.15, 4.70, 6.10)
    add_box(bm_white, 22.80, 24.20, 0.10, 0.16, 4.65, 6.15)
    add_box(bm_glass, 22.85, 24.15, 0.13, 0.15, 4.70, 6.10)
    # PB Zaguán taquería:
    add_box(bm_white, 20.20, 22.60, 0.40, 1.80, 0.00, 1.00)
    add_box(bm_awning_b, 20.10, 22.70, 0.20, 2.00, 2.10, 2.30)

    # Crujía 6 (Internet World X: 25.20 a 28.20 m):
    add_box(bm_wall, 24.80, 25.70, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 27.90, 28.60, 0.00, 0.35, 4.55, 6.25)
    # Gran ventana triple:
    add_box(bm_white, 25.70, 27.90, 0.10, 0.16, 4.60, 6.25)
    add_box(bm_white, 26.40, 26.50, 0.12, 0.18, 4.65, 6.20)
    add_box(bm_white, 27.10, 27.20, 0.12, 0.18, 4.65, 6.20)
    add_box(bm_glass, 25.75, 27.85, 0.13, 0.15, 4.65, 6.20)
    # PB Crujía 6:
    add_box(bm_dark, 25.30, 28.10, 0.08, 0.12, 0.00, 2.80)
    add_box(bm_glass, 25.35, 28.05, 0.09, 0.11, 0.10, 2.70)
    add_box(bm_awning_bl, 25.10, 28.30, -1.15, 0.05, 2.75, 3.25)
    add_box(bm_awning_bl, 25.10, 28.30, -1.20, -1.15, 2.50, 2.75)

    # Objetos en la escena
    obj_wall = create_mesh_object("Fachada_Oeste_Muro", bm_wall, mats["estuco"], col)
    obj_dark = create_mesh_object("Fachada_Oeste_AlumOscuro", bm_dark, mats["alum_oscuro"], col)
    obj_glass = create_mesh_object("Fachada_Oeste_Vidrio", bm_glass, mats["vidrio"], col)
    obj_white = create_mesh_object("Fachada_Oeste_AlumBlanco", bm_white, mats["alum_blanco"], col)
    obj_shutter = create_mesh_object("Fachada_Oeste_Cortinas", bm_shutter, mats["cortina_metalica"], col)
    obj_paves = create_mesh_object("Fachada_Oeste_Paves", bm_paves, mats["paves"], col)
    obj_toldo_b = create_mesh_object("Fachada_Oeste_ToldoBeige", bm_awning_b, mats["toldo_beige"], col)
    obj_toldo_bl = create_mesh_object("Fachada_Oeste_ToldoAzul", bm_awning_bl, mats["toldo_azul"], col)
    obj_int = create_mesh_object("Zaguan_PisoInterior", bm_interior, mats["piso_interior"], col)

    # Letreros en Fachada Oeste (Orientación corregida a (90°, 0°, 0°) para lectura izquierda a derecha hacia -Y)
    t_net = create_3d_text("Texto_InternetWorld", "INTERNET WORLD", 0.28, 0.03, mats["panel_blanco"], col)
    t_net.location = Vector((26.70, -1.21, 2.95))
    t_net.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    t_rep = create_3d_text("Texto_Reparacion", "VENTA Y REPARACION DE COMPUTADORAS", 0.13, 0.02, mats["panel_blanco"], col)
    t_rep.location = Vector((26.70, -1.21, 2.62))
    t_rep.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    return [obj_wall, obj_dark, obj_glass, obj_white, obj_shutter, obj_paves, obj_toldo_b, obj_toldo_bl, obj_int, t_net, t_rep]

def build_north_facade_libertad(mats, col):
    """
    Construye la Fachada Norte sobre Callejón Libertad (Y: 2.80 a 20.40 m).
    Vanos reales para Subway, canceles comerciales, toldo verde y pilastras.
    """
    bm_wall = bmesh.new()
    bm_dark = bmesh.new()
    bm_glass = bmesh.new()
    bm_white = bmesh.new()
    bm_shutter = bmesh.new()
    bm_awning_g = bmesh.new()

    # Muro base inferior PA (Antepecho Z: 3.20 a 4.55 m):
    add_box(bm_wall, 0.00, 0.35, 2.80, 20.40, 3.20, 4.55)

    # Muro dintel corrido sobre ventanas PA (Z: 6.25 a 7.15 m):
    add_box(bm_wall, 0.00, 0.35, 2.80, 20.40, 6.25, 7.15)
    # Pretil y albardilla corrida
    add_box(bm_wall, -0.05, 0.40, 2.80, 20.40, 7.05, 7.25)
    add_box(bm_wall, -0.08, 0.43, 2.75, 20.45, 7.25, 7.32)

    # Pilares en PB y pilastras
    pilares_y = [
        (2.80, 3.20),   # Inicio junto a ochava
        (7.00, 7.40),   # Entre N1 y Subway
        (12.00, 12.40), # Fin Subway / Reja servicio
        (15.20, 15.60), # Entre servicio y toldo verde
        (20.00, 20.40)  # Fin / Medianera Oriente
    ]
    for py1, py2 in pilares_y:
        add_box(bm_wall, 0.00, 0.35, py1, py2, 0.00, 3.20)
        add_box(bm_wall, -0.12, 0.02, py1 - 0.05, py2 + 0.05, 0.00, 7.55)
        add_box(bm_wall, -0.16, 0.05, py1 - 0.10, py2 + 0.10, 7.45, 7.60)

    # -----------------------------------------------------------------------
    # Machones y Ventanería en Planta Alta (Z: 4.55 a 6.25 m)
    # -----------------------------------------------------------------------

    # Crujía N1 (Y: 3.20 a 7.00 m):
    add_box(bm_wall, 0.00, 0.35, 3.20, 4.40, 4.55, 6.25)
    add_box(bm_wall, 0.00, 0.35, 6.20, 7.00, 4.55, 6.25)
    # Ventana N1 (Y: 4.40 a 6.20 m):
    add_box(bm_white, 0.10, 0.16, 4.40, 6.20, 4.55, 6.25)
    add_box(bm_white, 0.12, 0.18, 5.25, 5.35, 4.60, 6.20)
    add_box(bm_glass, 0.13, 0.15, 4.45, 6.15, 4.60, 6.20)
    # PB Crujía N1:
    add_box(bm_dark, 0.08, 0.12, 3.30, 6.90, 0.20, 2.85)
    add_box(bm_shutter, 0.10, 0.12, 3.35, 6.85, 0.25, 2.80)
    add_box(bm_white, -0.32, -0.02, 3.45, 4.25, 3.45, 4.05) # Minisplit
    add_box(bm_dark, -0.08, 0.02, 4.60, 5.10, 3.60, 3.90) # Corona oval

    # Crujía N2 — Franquicia SUBWAY (Y: 7.00 a 12.00 m):
    add_box(bm_wall, 0.00, 0.35, 7.00, 7.80, 4.55, 6.25)
    add_box(bm_wall, 0.00, 0.35, 9.80, 10.40, 4.55, 6.25)
    add_box(bm_wall, 0.00, 0.35, 11.40, 12.00, 4.55, 6.25)
    # Ventana Subway grande N2a:
    add_box(bm_white, 0.10, 0.16, 7.80, 9.80, 4.55, 6.25)
    add_box(bm_glass, 0.13, 0.15, 7.85, 9.75, 4.60, 6.20)
    # Ventana pequeña N2b:
    add_box(bm_white, 0.10, 0.16, 10.40, 11.40, 4.80, 5.80)
    add_box(bm_glass, 0.13, 0.15, 10.45, 11.35, 4.85, 5.75)
    # PB Subway:
    add_box(bm_dark, 0.08, 0.12, 7.50, 11.90, 0.00, 2.90)
    add_box(bm_glass, 0.09, 0.11, 7.55, 11.85, 0.10, 2.80)
    add_box(bm_shutter, 0.10, 0.12, 7.60, 11.80, 2.00, 2.80)

    # Crujía N3 (Y: 12.00 a 15.20 m):
    # Muro superior ciego:
    add_box(bm_wall, 0.00, 0.35, 12.00, 15.20, 4.55, 6.25)
    # PB Reja metálica de servicio:
    add_box(bm_dark, 0.06, 0.12, 12.60, 14.00, 0.00, 2.80)
    for ry in [12.80, 13.10, 13.40, 13.70]:
        add_box(bm_dark, 0.08, 0.10, ry - 0.02, ry + 0.02, 0.10, 2.70)
    add_box(bm_wall, 0.00, 0.35, 14.00, 15.20, 0.00, 3.20)

    # Crujía N4 (Y: 15.20 a 20.40 m):
    add_box(bm_wall, 0.00, 0.35, 15.20, 16.80, 4.55, 6.25)
    add_box(bm_wall, 0.00, 0.35, 18.60, 20.40, 4.55, 6.25)
    # Ventana N4:
    add_box(bm_white, 0.10, 0.16, 16.80, 18.60, 4.60, 6.20)
    add_box(bm_glass, 0.13, 0.15, 16.85, 18.55, 4.65, 6.15)
    # PB Toldo verde semicilíndrico:
    add_box(bm_dark, 0.08, 0.12, 15.80, 19.80, 0.00, 2.85)
    add_box(bm_shutter, 0.10, 0.12, 15.85, 19.75, 0.10, 2.80)
    add_box(bm_awning_g, -1.30, 0.05, 15.60, 20.00, 2.60, 3.35)

    # Objetos en la escena
    obj_wall_n = create_mesh_object("Fachada_Norte_Muro", bm_wall, mats["estuco"], col)
    obj_dark_n = create_mesh_object("Fachada_Norte_AlumOscuro", bm_dark, mats["alum_oscuro"], col)
    obj_glass_n = create_mesh_object("Fachada_Norte_Vidrio", bm_glass, mats["vidrio"], col)
    obj_white_n = create_mesh_object("Fachada_Norte_AlumBlanco", bm_white, mats["alum_blanco"], col)
    obj_shutter_n = create_mesh_object("Fachada_Norte_Cortinas", bm_shutter, mats["cortina_metalica"], col)
    obj_toldo_g = create_mesh_object("Fachada_Norte_ToldoVerde", bm_awning_g, mats["toldo_verde"], col)

    # Logotipo 3D SUBWAY
    t_subway = create_3d_text("Texto_Subway", "SUBWAY", 0.65, 0.08, mats["subway_amarillo"], col)
    t_subway.location = Vector((-0.08, 9.70, 3.50))
    t_subway.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))

    bm_sub_bg = bmesh.new()
    add_box(bm_sub_bg, -0.04, 0.02, 7.60, 11.80, 3.30, 4.25)
    obj_sub_bg = create_mesh_object("Subway_Fascia_Verde", bm_sub_bg, mats["subway_verde"], col)

    return [obj_wall_n, obj_dark_n, obj_glass_n, obj_white_n, obj_shutter_n, obj_toldo_g, t_subway, obj_sub_bg]

def build_ochava_corner(mats, col):
    """
    Construye la Ochava a 45º con vano real en balcón, puerta francesa acristalada,
    cancel PB con puertas dobles, remate colonial acampanado y letrero Hotel Tecate.
    """
    bm_wall = bmesh.new()
    bm_balcony = bmesh.new()
    bm_iron = bmesh.new()
    bm_dark = bmesh.new()
    bm_white = bmesh.new()
    bm_glass = bmesh.new()
    bm_sign = bmesh.new()

    center_xy = (1.40, 1.40)
    tangent_xy = (-0.7071, 0.7071)  # Paralelo al chaflán
    normal_xy = (-0.7071, -0.7071)  # Normal exterior hacia la esquina del parque

    # 1. Muro de la ochava con vano abierto para balcón en Planta Alta
    # Muros laterales en PA (Z: 3.65 a 6.25 m):
    add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, -1.98, -1.00, 0.00, 0.35, 3.65, 6.25)
    add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, 1.00, 1.98, 0.00, 0.35, 3.65, 6.25)
    # Dintel corrido PA sobre puerta francesa (Z: 6.25 a 7.30 m):
    add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, -1.98, 1.98, 0.00, 0.35, 6.25, 7.30)
    
    # Muros laterales en PB (Z: 0.00 a 2.85 m):
    add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, -1.98, -1.25, 0.00, 0.35, 0.00, 2.85)
    add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, 1.25, 1.98, 0.00, 0.35, 0.00, 2.85)
    # Dintel PB (Z: 2.85 a 3.45 m):
    add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, -1.98, 1.98, 0.00, 0.35, 2.85, 3.45)

    # 2. Cancel Comercial en Planta Baja ("MOCHO RESTAURANT"):
    # Marco perimetral oscuro
    add_oriented_box(bm_dark, center_xy, tangent_xy, normal_xy, -1.25, -1.15, -0.05, 0.10, 0.00, 2.85)
    add_oriented_box(bm_dark, center_xy, tangent_xy, normal_xy, 1.15, 1.25, -0.05, 0.10, 0.00, 2.85)
    add_oriented_box(bm_dark, center_xy, tangent_xy, normal_xy, -1.25, 1.25, -0.05, 0.10, 2.75, 2.85)
    add_oriented_box(bm_dark, center_xy, tangent_xy, normal_xy, -0.05, 0.05, -0.05, 0.10, 0.00, 2.85) # Parteluz
    # Vidrios de puerta doble comercial
    add_oriented_box(bm_glass, center_xy, tangent_xy, normal_xy, -1.15, -0.05, -0.02, 0.02, 0.15, 2.75)
    add_oriented_box(bm_glass, center_xy, tangent_xy, normal_xy, 0.05, 1.15, -0.02, 0.02, 0.15, 2.75)
    # Marquesina metálica curva / rótulo "MOCHO RESTAURANT" en voladizo exterior
    add_oriented_box(bm_sign, center_xy, tangent_xy, normal_xy, -1.45, 1.45, 0.00, 0.35, 2.90, 3.40)

    # 3. Balcón en Voladizo en Planta Alta (Z = 3.45 a 3.65 m)
    # Losa de balcón saliente 1.15 m hacia afuera (+n hacia la calle)
    add_oriented_box(bm_balcony, center_xy, tangent_xy, normal_xy, -2.15, 2.15, -0.05, 1.15, 3.45, 3.65)
    add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, -1.95, 1.95, -0.10, 0.95, 3.25, 3.45)

    # Barandal de hierro forjado ornamental exterior (Z: 3.65 a 4.70 m, altura 1.05 m)
    # Pasamanos frontal y zócalo inferior
    add_oriented_box(bm_iron, center_xy, tangent_xy, normal_xy, -2.15, 2.15, 1.10, 1.15, 4.65, 4.70)
    add_oriented_box(bm_iron, center_xy, tangent_xy, normal_xy, -2.15, 2.15, 1.10, 1.15, 3.65, 3.70)
    # Laterales del barandal
    add_oriented_box(bm_iron, center_xy, tangent_xy, normal_xy, -2.15, -2.10, 0.00, 1.15, 3.65, 4.70)
    add_oriented_box(bm_iron, center_xy, tangent_xy, normal_xy, 2.10, 2.15, 0.00, 1.15, 3.65, 4.70)
    # Barrotes verticales de forja frontales
    for s_bar in [-1.90, -1.50, -1.10, -0.70, -0.30, 0.10, 0.50, 0.90, 1.30, 1.70]:
        add_oriented_box(bm_iron, center_xy, tangent_xy, normal_xy, s_bar - 0.03, s_bar + 0.03, 1.11, 1.14, 3.70, 4.65)

    # Puerta francesa hacia el balcón (Z: 3.65 a 6.25 m)
    add_oriented_box(bm_white, center_xy, tangent_xy, normal_xy, -0.95, 0.95, -0.10, 0.02, 3.65, 6.25) # Marco
    add_oriented_box(bm_white, center_xy, tangent_xy, normal_xy, -0.04, 0.04, -0.08, 0.02, 3.65, 6.25) # Parteluz
    for hz in [4.25, 4.85, 5.45]:
        add_oriented_box(bm_white, center_xy, tangent_xy, normal_xy, -0.90, 0.90, -0.08, 0.00, hz - 0.03, hz + 0.03)
    add_oriented_box(bm_glass, center_xy, tangent_xy, normal_xy, -0.90, -0.04, -0.05, -0.02, 3.75, 6.15)
    add_oriented_box(bm_glass, center_xy, tangent_xy, normal_xy, 0.04, 0.90, -0.05, -0.02, 3.75, 6.15)

    # 4. Remate Colonial Acampanado / Espadaña en el Pretil
    steps = 18
    for i in range(steps):
        t1 = -1.0 + 2.0 * i / steps
        t2 = -1.0 + 2.0 * (i + 1) / steps
        s1 = t1 * 1.98
        s2 = t2 * 1.98
        h1 = 7.30 + 1.40 * math.cos(t1 * math.pi * 0.5)
        h2 = 7.30 + 1.40 * math.cos(t2 * math.pi * 0.5)
        h_max = max(h1, h2)
        add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, s1, s2, 0.00, 0.35, 7.25, h_max)

    # Alvéolo / ventanilla cuadrada central de ventilación
    add_oriented_box(bm_dark, center_xy, tangent_xy, normal_xy, -0.30, 0.30, 0.05, 0.30, 7.80, 8.20)
    add_oriented_box(bm_iron, center_xy, tangent_xy, normal_xy, -0.25, 0.25, 0.02, 0.06, 7.85, 8.15)

    # 5. Rótulo Volado "HOTEL TECATE Tel. 654-11-16"
    # Mástil metálico
    add_box(bm_sign, 2.55, 2.65, -1.80, 0.10, 4.85, 4.95)
    # Panel blanco de doble cara
    add_box(bm_sign, 2.58, 2.62, -1.80, -0.20, 4.00, 5.20)

    obj_wall_o = create_mesh_object("Ochava_Muro_Remate", bm_wall, mats["estuco"], col)
    obj_balcony = create_mesh_object("Ochava_Balcon_Losa", bm_balcony, mats["moldura"], col)
    obj_iron = create_mesh_object("Ochava_Barandal_Forja", bm_iron, mats["hierro_forjado"], col)
    obj_dark_o = create_mesh_object("Ochava_Canceleria_Oscura", bm_dark, mats["alum_oscuro"], col)
    obj_white_o = create_mesh_object("Ochava_Canceleria_Blanca", bm_white, mats["alum_blanco"], col)
    obj_glass_o = create_mesh_object("Ochava_Vidrio", bm_glass, mats["vidrio"], col)
    obj_sign_panel = create_mesh_object("Ochava_Rotulo_Panel", bm_sign, mats["panel_blanco"], col)

    # Rótulos en texto 3D sobre el cartel en voladizo
    # Cara Norte (Normal -X local hacia Callejón Libertad: (90°, 0°, -90°))
    t_h_norte = create_3d_text("Texto_Hotel_Norte", "HOTEL\nTECATE", 0.36, 0.015, mats["texto_rojo"], col)
    t_h_norte.location = Vector((2.55, -1.00, 4.80))
    t_h_norte.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))

    t_tel_norte = create_3d_text("Texto_Tel_Norte", "Tel. 654-11-16", 0.13, 0.012, mats["texto_azul"], col)
    t_tel_norte.location = Vector((2.55, -1.00, 4.20))
    t_tel_norte.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))

    # Cara Sur (Normal +X local hacia Cárdenas: (90°, 0°, 90°))
    t_h_sur = create_3d_text("Texto_Hotel_Sur", "HOTEL\nTECATE", 0.36, 0.015, mats["texto_rojo"], col)
    t_h_sur.location = Vector((2.65, -1.00, 4.80))
    t_h_sur.rotation_euler = (math.radians(90.0), 0.0, math.radians(90.0))

    t_tel_sur = create_3d_text("Texto_Tel_Sur", "Tel. 654-11-16", 0.13, 0.012, mats["texto_azul"], col)
    t_tel_sur.location = Vector((2.65, -1.00, 4.20))
    t_tel_sur.rotation_euler = (math.radians(90.0), 0.0, math.radians(90.0))

    return [obj_wall_o, obj_balcony, obj_iron, obj_dark_o, obj_white_o, obj_glass_o, obj_sign_panel, t_h_norte, t_tel_norte, t_h_sur, t_tel_sur]

def build_courtyard_rear_and_roof(mats, col):
    """
    Construye las fachadas medianeras posteriores, el patio interior y la azotea hermética.
    """
    bm_wall = bmesh.new()
    bm_roof = bmesh.new()
    bm_corridor = bmesh.new()
    bm_iron = bmesh.new()

    # 1. Muro Medianero Sur (Colindancia con Dulcería El Molino en X = 28.60 m)
    add_box(bm_wall, 28.25, 28.60, 0.00, 20.40, 0.00, 7.30)

    # 2. Muro Medianero Oriente (Colindancia con vecinos en Y = 20.40 m)
    add_box(bm_wall, 0.00, 28.60, 20.05, 20.40, 0.00, 7.30)

    # 3. Alas Interiores y Patio Central:
    # Patio Central abierto en X: 8.00 a 20.00 m, Y: 6.00 a 14.00 m
    # Ala Norte:
    add_box(bm_wall, 7.70, 8.00, 6.00, 20.05, 0.00, 7.10)
    # Ala Oeste:
    add_box(bm_wall, 8.00, 19.70, 5.70, 6.00, 0.00, 7.10)
    # Ala Sur:
    add_box(bm_wall, 24.80, 25.10, 6.00, 20.05, 0.00, 7.10)
    # Ala Oriente:
    add_box(bm_wall, 8.00, 24.80, 14.00, 14.30, 0.00, 7.10)

    # Pasillo exterior techado en Planta Alta
    add_box(bm_corridor, 8.00, 19.70, 6.00, 7.20, 3.45, 3.55)
    add_box(bm_iron, 8.00, 19.70, 7.15, 7.20, 3.55, 4.55)

    # 4. Sellado Hermético Total de Azotea (Losa Impermeabilizada en Z = 6.95 m)
    # Ala Oeste (a lo largo de Cárdenas):
    add_box(bm_roof, 2.80, 28.60, 0.35, 6.00, 6.90, 7.00)
    # Ala Norte (a lo largo de Callejón Libertad):
    add_box(bm_roof, 0.35, 8.00, 2.80, 20.40, 6.90, 7.00)
    # Esquina diagonal Ochava (triángulo ortogonal sellado):
    # Entre X=0.35..2.80 y Y=0.35..2.80
    add_box(bm_roof, 0.35, 2.80, 0.35, 2.80, 6.90, 7.00)
    # Ala Sur (junto a Dulcería):
    add_box(bm_roof, 24.80, 28.60, 6.00, 20.40, 6.90, 7.00)
    # Ala Oriente:
    add_box(bm_roof, 8.00, 24.80, 14.00, 20.40, 6.90, 7.00)
    # Techo sobre el túnel en planta alta:
    add_box(bm_roof, 19.70, 24.80, 0.35, 6.00, 6.90, 7.00)

    # Casetas de servicio y tinacos en azotea
    add_box(bm_wall, 10.00, 13.00, 16.00, 18.50, 7.00, 9.20)
    add_box(bm_roof, 9.85, 13.15, 15.85, 18.65, 9.15, 9.25)
    add_box(bm_wall, 14.00, 15.50, 16.50, 18.00, 7.00, 8.60)

    # Antenas parabólicas satelitales en azotea norte (Ground Truth fotográfico)
    for dx, dy in [(4.50, 5.50), (6.20, 8.80)]:
        add_box(bm_wall, dx - 0.04, dx + 0.04, dy - 0.04, dy + 0.04, 7.00, 7.65) # Mástil tubular
        add_box(bm_corridor, dx - 0.35, dx + 0.35, dy - 0.05, dy + 0.05, 7.50, 8.20) # Plato parabólico

    obj_rear_wall = create_mesh_object("Interior_Muros_Patio", bm_wall, mats["estuco"], col)
    obj_roof = create_mesh_object("Azotea_Losa_Hermetica", bm_roof, mats["azotea"], col)
    obj_corridor = create_mesh_object("Pasillo_PlantaAlta", bm_corridor, mats["moldura"], col)
    obj_iron_p = create_mesh_object("Pasillo_Barandal", bm_iron, mats["hierro_forjado"], col)

    return [obj_rear_wall, obj_roof, obj_corridor, obj_iron_p]

# ---------------------------------------------------------------------------
# 4. Configuración de Iluminación y Batería de Validación (6 Cámaras)
# ---------------------------------------------------------------------------

def setup_lighting_and_render(col):
    """Configura Cycles CPU, iluminación solar diurna frontal y las 6 cámaras fijas."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    if hasattr(scene.cycles, 'device'):
        scene.cycles.device = 'CPU'
    scene.cycles.samples = 64

    # Iluminación ambiental de cielo claro diurno de Tecate
    if scene.world:
        scene.world.use_nodes = True
        bg_node = scene.world.node_tree.nodes.get("Background")
        if bg_node:
            bg_node.inputs["Color"].default_value = (0.72, 0.84, 0.96, 1.0)
            bg_node.inputs["Strength"].default_value = 0.85

    # Luz de Sol principal iluminando las fachadas frontales (Norte y Oeste)
    sun_data = bpy.data.lights.new("Sun_Main", type='SUN')
    sun_data.energy = 4.5
    sun_data.angle = math.radians(1.0)
    sun_obj = bpy.data.objects.new("Sun_Main", sun_data)
    # Orientado hacia el Sureste (+X, +Y), incidiendo de frente sobre ambas calles:
    sun_obj.rotation_euler = (math.radians(48.0), math.radians(-15.0), math.radians(130.0))
    col.objects.link(sun_obj)

    # Luz de relleno celeste diurna suave
    fill_data = bpy.data.lights.new("Sun_Fill", type='SUN')
    fill_data.energy = 1.8
    fill_data.color = (0.75, 0.85, 1.0)
    fill_obj = bpy.data.objects.new("Sun_Fill", fill_data)
    fill_obj.rotation_euler = (math.radians(70.0), 0.0, math.radians(-50.0))
    col.objects.link(fill_obj)

    # Cámaras técnicas de validación universal
    cameras_config = [
        # 1. Ochava 45º (Vista directa a balcón, cancel y remate colonial)
        ("ochava_45", (-12.5, -12.5, 4.5), (1.4, 1.4, 4.2), 32.0),
        # 2. Fachada Norte (Subway y Callejón Libertad frente al parque)
        ("subway_north", (-18.0, 11.5, 4.2), (0.0, 11.5, 4.0), 38.0),
        # 3. Fachada Oeste (Calle Presidente Lázaro Cárdenas frontal completa)
        ("cardenas_west", (15.7, -24.0, 4.5), (15.7, 0.0, 4.0), 34.0),
        # 4. Zaguán Túnel Closeup (Paso transitable a taquería y pavés)
        ("zaguan_closeup", (22.4, -9.0, 2.1), (22.4, 0.0, 2.2), 40.0),
        # 5. Colindancia Dulcería El Molino (Extremo sur / Internet World)
        ("dulceria_border", (27.0, -12.0, 3.2), (27.0, 0.0, 3.5), 42.0),
        # 6. Vista Aérea Cenital (Verificación de hermeticidad de azotea Z=48m)
        ("aerial_top", (14.3, 10.2, 48.0), (14.3, 10.2, 0.0), 50.0)
    ]

    cams = {}
    for cam_name, pos, tgt, lens in cameras_config:
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
# 5. Generación de Escena Godot 4 (.tscn) con Colisiones Analíticas
# ---------------------------------------------------------------------------

def generate_godot_tscn(tscn_path, glb_resource_path):
    """
    Escribe el archivo de escena de Godot 4 con colisionadores analíticos BoxShape3D.
    Garantiza que el zaguán túnel central sea transitable sin paredes invisibles.
    """
    tscn_content = f"""[gd_scene load_steps=12 format=3 uid="uid://hotel_tecate_2009_001"]

[ext_resource type="PackedScene" path="{glb_resource_path}" id="1_mesh"]

[sub_resource type="BoxShape3D" id="BoxShape3D_oeste_norte"]
size = Vector3(17.20, 7.30, 0.40)

[sub_resource type="BoxShape3D" id="BoxShape3D_oeste_sur"]
size = Vector3(3.80, 7.30, 0.40)

[sub_resource type="BoxShape3D" id="BoxShape3D_dintel_zaguan"]
size = Vector3(4.80, 4.10, 0.40)

[sub_resource type="BoxShape3D" id="BoxShape3D_norte_cardenas"]
size = Vector3(0.40, 7.30, 17.60)

[sub_resource type="BoxShape3D" id="BoxShape3D_ochava"]
size = Vector3(0.40, 7.30, 3.96)

[sub_resource type="BoxShape3D" id="BoxShape3D_medianera_sur"]
size = Vector3(0.40, 7.30, 20.40)

[sub_resource type="BoxShape3D" id="BoxShape3D_medianera_oriente"]
size = Vector3(28.60, 7.30, 0.40)

[sub_resource type="BoxShape3D" id="BoxShape3D_tunel_muro_norte"]
size = Vector3(0.30, 3.20, 9.65)

[sub_resource type="BoxShape3D" id="BoxShape3D_tunel_muro_sur"]
size = Vector3(0.30, 3.20, 9.65)

[node name="Hotel_Tecate" type="StaticBody3D"]

[node name="ModelInstance" parent="." instance=ExtResource("1_mesh")]

[node name="Col_Oeste_Norte" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 11.40, 3.65, -0.18)
shape = SubResource("BoxShape3D_oeste_norte")

[node name="Col_Oeste_Sur" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 26.70, 3.65, -0.18)
shape = SubResource("BoxShape3D_oeste_sur")

[node name="Col_Dintel_Zaguan" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 22.40, 5.25, -0.18)
shape = SubResource("BoxShape3D_dintel_zaguan")

[node name="Col_Norte_Libertad" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.18, 3.65, -11.60)
shape = SubResource("BoxShape3D_norte_cardenas")

[node name="Col_Ochava" type="CollisionShape3D" parent="."]
transform = Transform3D(0.707107, 0, 0.707107, 0, 1, 0, -0.707107, 0, 0.707107, 1.40, 3.65, -1.40)
shape = SubResource("BoxShape3D_ochava")

[node name="Col_Medianera_Sur" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 28.40, 3.65, -10.20)
shape = SubResource("BoxShape3D_medianera_sur")

[node name="Col_Medianera_Oriente" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 14.30, 3.65, -20.20)
shape = SubResource("BoxShape3D_medianera_oriente")

[node name="Col_Tunel_Muro_Norte" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 19.85, 1.60, -5.18)
shape = SubResource("BoxShape3D_tunel_muro_norte")

[node name="Col_Tunel_Muro_Sur" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 24.95, 1.60, -5.18)
shape = SubResource("BoxShape3D_tunel_muro_sur")
"""
    with open(tscn_path, "w", encoding="utf-8") as f:
        f.write(tscn_content)
    print(f"--> Escena Godot generada con éxito: {tscn_path}")

# ---------------------------------------------------------------------------
# 6. Función Principal de Orquestación
# ---------------------------------------------------------------------------

def main():
    print("================================================================")
    print(" GENERADOR PROCEDURAL 3D: HOTEL TECATE (2009 GROUND-TRUTH)       ")
    print(" (V2.0: Vanos reales de ventanas, sol frontal y zero espejeado) ")
    print("================================================================")

    root_col = clean_scene()
    mats = create_materials()

    # 1. Zócalo basal continuo enterrado (-1.20 m)
    obj_zocalo = build_zocalo_basal(mats, root_col)

    # 2. Fachada Oeste (Calle Presidente Lázaro Cárdenas, 6 Crujías)
    objs_west = build_west_facade_cardenas(mats, root_col)

    # 3. Fachada Norte (Callejón Libertad, Subway)
    objs_north = build_north_facade_libertad(mats, root_col)

    # 4. Ochava a 45º (Balcón forjado, remate colonial acampanado y letrero)
    objs_ochava = build_ochava_corner(mats, root_col)

    # 5. Patio interior, cuerpos traseros y azotea hermética
    objs_rear = build_courtyard_rear_and_roof(mats, root_col)

    # 6. Iluminación y batería de 6 cámaras de validación
    cams = setup_lighting_and_render(root_col)

    # 7. Guardar archivo maestro Blender (.blend)
    blend_path = "blender_assets/buildings/hotel_tecate.blend"
    os.makedirs(os.path.dirname(blend_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"--> Archivo maestro Blender guardado: {blend_path}")

    # 8. Exportar asset limpio GLB para Godot 4 (sin banquetas)
    glb_path = "godot_project/assets/buildings/hotel_tecate.glb"
    os.makedirs(os.path.dirname(glb_path), exist_ok=True)

    bpy.ops.object.select_all(action='DESELECT')
    render_types = {'MESH', 'CURVE', 'FONT'}
    for o in root_col.objects:
        if o.type in render_types:
            o.select_set(True)
    bpy.context.view_layer.objects.active = obj_zocalo

    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_materials='EXPORT',
        export_yup=True
    )
    print(f"--> Asset limpio GLB exportado: {glb_path}")

    # 9. Generar escena Godot .tscn
    tscn_path = "godot_project/assets/buildings/hotel_tecate.tscn"
    generate_godot_tscn(tscn_path, "res://assets/buildings/hotel_tecate.glb")

    # 10. Ejecutar batería de renders técnicos de validación
    scene = bpy.context.scene
    renders = [
        ("ochava_45", "docs/images/hotel_tecate/hotel_tecate_ochava_45.png", 1280, 720),
        ("subway_north", "docs/images/hotel_tecate/hotel_tecate_subway_north.png", 1280, 720),
        ("cardenas_west", "docs/images/hotel_tecate/hotel_tecate_cardenas_west.png", 1280, 720),
        ("zaguan_closeup", "docs/images/hotel_tecate/hotel_tecate_zaguan_closeup.png", 1280, 720),
        ("dulceria_border", "docs/images/hotel_tecate/hotel_tecate_dulceria_border.png", 1280, 720),
        ("aerial_top", "docs/images/hotel_tecate/hotel_tecate_aerial_top.png", 1024, 1024)
    ]

    for cam_key, out_path, rx, ry in renders:
        abs_out = os.path.abspath(out_path)
        os.makedirs(os.path.dirname(abs_out), exist_ok=True)
        scene.camera = cams[cam_key]
        scene.render.resolution_x = rx
        scene.render.resolution_y = ry
        scene.render.filepath = abs_out
        bpy.ops.render.render(write_still=True)
        print(f"--> Render {cam_key} generado con éxito en: {abs_out}")

    print("================================================================")
    print(" GENERACIÓN PROCEDURAL HOTEL TECATE V2.0 CONCLUIDA EXITOSAMENTE ")
    print("================================================================")

if __name__ == "__main__":
    main()
