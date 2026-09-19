"""
=============================================================================
GENERADOR PROCEDURAL 3D UNIVERSAL: HOTEL TECATE (VERSIÓN 4.0 GROUND-TRUTH)
=============================================================================
Reconstrucción fidedigna con consenso multi-perspectiva de alta resolución:
  - Ubicación: Pdte. Lázaro Cárdenas 133 / Callejón Libertad, Centro, Tecate, B.C.
  - Frente al Parque Miguel Hidalgo.
  - Coordenadas geográficas: 32.572763, -116.626927

Novedades V4.0 (Ground-Truth 2026 Refinado):
  - Ochava a 45º: Torreón peraltado semicircular puro con golas cóncavas de transición,
    arco/dintel ornamental en relieve de bloques de vidrio translúcido (pavés) en PA,
    ménsulas escalonadas de concreto bajo la losa del balcón, barandal forjado,
    marquesina volada en PB y mástil de luminaria vertical.
  - Fachada Norte (Callejón Libertad): 5 crujías moduladas por dados en pretil,
    rótulo 3D SUBWAY en relieve institucional directo sobre el estuco salmón,
    toldo negro rectangular Casa Paris, local La Michoacana con persiana y reja de servicio,
    terraza con carpas rojas y logotipo Tecate.
  - Fachada Oeste (Calle Pdte. Lázaro Cárdenas): Pilastras con dados en pretil,
    ventanería exacta con ventanitas gemelas [][], compresor minisplit A/C en fachada,
    dos toldos contiguos inclinados color arena/beige, franja continua de pavés,
    toldo rojo Coca-Cola de Taquería Los Gallos y zaguán transitable.
  - Materiales PBR Fotorrealistas: Estuco salmón cálido (#BE6D55) con shader dual de
    micro-grano y textura de llana, pavés translúcido refractante, lonas vinílicas,
    cancelería de aluminio blanco y oscuro con micro-ranuras, y persianas metálicas acanaladas.
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
# 2. Paleta de Materiales PBR Fotorrealistas
# ---------------------------------------------------------------------------

def create_materials():
    """Genera materiales PBR calibrados con shaders complejos y fotorrealismo táctil."""
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

    # 1. Estuco Terracota Salmón Cálido Fotorrealista PBR (media_1789814168997)
    albedo_path = os.path.abspath("godot_project/assets/textures/hotel_tecate_stucco_albedo.png")
    normal_path = os.path.abspath("godot_project/assets/textures/hotel_tecate_stucco_normal.png")
    rough_path = os.path.abspath("godot_project/assets/textures/hotel_tecate_stucco_roughness.png")

    m_stucco = _make_mat("M_Estuco_Terracota", (0.70, 0.62, 0.58, 1.0), rough=0.86)
    nodes = m_stucco.node_tree.nodes
    links = m_stucco.node_tree.links
    bsdf_st = nodes.get("Principled BSDF")
    if bsdf_st and os.path.exists(albedo_path):
        tex_coord = nodes.new('ShaderNodeTexCoord')
        mapping = nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (0.60, 0.60, 0.60)
        links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])

        # Albedo map
        img_alb = bpy.data.images.load(albedo_path)
        node_alb = nodes.new('ShaderNodeTexImage')
        node_alb.image = img_alb
        node_alb.projection = 'BOX'
        node_alb.projection_blend = 0.25
        links.new(mapping.outputs['Vector'], node_alb.inputs['Vector'])
        links.new(node_alb.outputs['Color'], bsdf_st.inputs['Base Color'])

        # Normal map
        if os.path.exists(normal_path):
            img_nrm = bpy.data.images.load(normal_path)
            img_nrm.colorspace_settings.name = 'Non-Color'
            node_nrm = nodes.new('ShaderNodeTexImage')
            node_nrm.image = img_nrm
            node_nrm.projection = 'BOX'
            node_nrm.projection_blend = 0.25
            links.new(mapping.outputs['Vector'], node_nrm.inputs['Vector'])

            nrm_map = nodes.new('ShaderNodeNormalMap')
            nrm_map.inputs['Strength'].default_value = 0.90
            links.new(node_nrm.outputs['Color'], nrm_map.inputs['Color'])
            links.new(nrm_map.outputs['Normal'], bsdf_st.inputs['Normal'])

        # Roughness map
        if os.path.exists(rough_path):
            img_rgh = bpy.data.images.load(rough_path)
            img_rgh.colorspace_settings.name = 'Non-Color'
            node_rgh = nodes.new('ShaderNodeTexImage')
            node_rgh.image = img_rgh
            node_rgh.projection = 'BOX'
            node_rgh.projection_blend = 0.25
            links.new(mapping.outputs['Vector'], node_rgh.inputs['Vector'])
            links.new(node_rgh.outputs['Color'], bsdf_st.inputs['Roughness'])
    mats["estuco"] = m_stucco

    # 2. Zócalo Basal Subterráneo (Concreto Grafito Oscuro)
    mats["zocalo"] = _make_mat("M_Zocalo_Basal", (0.05, 0.05, 0.055, 1.0), rough=0.92)

    # 3. Bloques de Vidrio Translúcido (Pavés)
    m_paves = _make_mat("M_Paves_Glass", (0.72, 0.86, 0.83, 1.0), rough=0.18, transmission=0.82, ior=1.52)
    nodes_p = m_paves.node_tree.nodes
    links_p = m_paves.node_tree.links
    bsdf_p = nodes_p.get("Principled BSDF")
    if bsdf_p:
        bump_p = nodes_p.new('ShaderNodeBump')
        bump_p.inputs['Strength'].default_value = 0.25
        tex_w = nodes_p.new('ShaderNodeTexWave')
        tex_w.inputs['Scale'].default_value = 35.0
        links_p.new(tex_w.outputs['Fac'], bump_p.inputs['Height'])
        links_p.new(bump_p.outputs['Normal'], bsdf_p.inputs['Normal'])
    mats["paves"] = m_paves

    # 4. Mampostería Molduras / Remate Beige Claro
    mats["moldura"] = _make_mat("M_Moldura_Beige", (0.86, 0.83, 0.75, 1.0), rough=0.78)

    # 5. Ménsulas de Concreto Escalonadas
    mats["mensula"] = _make_mat("M_Mensula_Concreto", (0.70, 0.66, 0.60, 1.0), rough=0.85)

    # 6. Cancelería Aluminio Blanco (Ventanales Superiores)
    mats["alum_blanco"] = _make_mat("M_Aluminio_Blanco", (0.93, 0.93, 0.93, 1.0), rough=0.25, metal=0.12)

    # 7. Cancelería Aluminio Oscuro (Escaparates y Puertas de PB)
    mats["alum_oscuro"] = _make_mat("M_Aluminio_Oscuro", (0.04, 0.04, 0.045, 1.0), rough=0.28, metal=0.80)

    # 8. Vidrio Reflectante Comercial
    mats["vidrio"] = _make_mat("M_Vidrio_Comercial", (0.05, 0.09, 0.13, 1.0), rough=0.04, transmission=0.86, ior=1.52)

    # 9. Cortinas Metálicas Enrollables (Lámina Acanalada Galvanizada)
    m_shutter = _make_mat("M_Cortina_Metalica", (0.24, 0.22, 0.21, 1.0), rough=0.48, metal=0.65)
    nodes_s = m_shutter.node_tree.nodes
    links_s = m_shutter.node_tree.links
    bsdf_s = nodes_s.get("Principled BSDF")
    if bsdf_s:
        bump_s = nodes_s.new('ShaderNodeBump')
        bump_s.inputs['Strength'].default_value = 0.35
        tex_ws = nodes_s.new('ShaderNodeTexWave')
        tex_ws.wave_type = 'BANDS'
        tex_ws.bands_direction = 'Z' if hasattr(tex_ws, 'bands_direction') else 'DIAGONAL'
        tex_ws.inputs['Scale'].default_value = 65.0
        links_s.new(tex_ws.outputs['Fac'], bump_s.inputs['Height'])
        links_s.new(bump_s.outputs['Normal'], bsdf_s.inputs['Normal'])
    mats["cortina_metalica"] = m_shutter

    # 10. Hierro Forjado Negro (Barandales)
    mats["hierro_forjado"] = _make_mat("M_Hierro_Forjado", (0.015, 0.015, 0.018, 1.0), rough=0.35, metal=0.90)

    # 11. Toldos Contiguos Color Arena / Beige (Calle Cárdenas)
    mats["toldo_arena"] = _make_mat("M_Toldo_Arena", (0.75, 0.69, 0.52, 1.0), rough=0.72)

    # 12. Toldo Rojo Coca-Cola Taquería Los Gallos (Zaguán)
    mats["toldo_rojo"] = _make_mat("M_Toldo_Rojo_Taqueria", (0.85, 0.02, 0.03, 1.0), rough=0.55)

    # 13. Toldo Rectangular Negro Casa Paris (Callejón Libertad)
    mats["toldo_negro"] = _make_mat("M_Toldo_Negro_Paris", (0.08, 0.08, 0.09, 1.0), rough=0.65)

    # 14. Toldo Verde Oscuro / Azul Marino (Internet World)
    mats["toldo_verde_oscuro"] = _make_mat("M_Toldo_Verde_Oscuro", (0.05, 0.16, 0.11, 1.0), rough=0.68)

    # 15. Franquicia SUBWAY (Verde institucional, Blanco y Amarillo Dorado)
    mats["subway_verde"] = _make_mat("M_Subway_Verde", (0.00, 0.45, 0.18, 1.0), rough=0.35, metal=0.05)
    mats["subway_blanco"] = _make_mat("M_Subway_Blanco", (0.95, 0.95, 0.95, 1.0), rough=0.25, metal=0.05)
    mats["subway_amarillo"] = _make_mat("M_Subway_Amarillo", (1.00, 0.76, 0.05, 1.0), rough=0.25, metal=0.05)

    # 16. Carpas / Sombrillas Rojas de Terraza
    mats["sombrilla_roja"] = _make_mat("M_Sombrilla_Roja", (0.85, 0.04, 0.05, 1.0), rough=0.55)

    # 17. Chasis de Minisplit A/C
    mats["minisplit_chasis"] = _make_mat("M_Minisplit_Chasis", (0.91, 0.90, 0.87, 1.0), rough=0.35)
    mats["minisplit_rejilla"] = _make_mat("M_Minisplit_Rejilla", (0.16, 0.16, 0.17, 1.0), rough=0.50, metal=0.30)

    # 18. Rótulos y Letreros
    mats["panel_blanco"] = _make_mat("M_Panel_Blanco", (0.95, 0.95, 0.95, 1.0), rough=0.25)
    mats["texto_rojo"] = _make_mat("M_Texto_Rojo", (0.85, 0.04, 0.04, 1.0), rough=0.30)
    mats["texto_azul"] = _make_mat("M_Texto_Azul", (0.05, 0.15, 0.70, 1.0), rough=0.30)
    mats["acero_espejo"] = _make_mat("M_Acero_Espejo", (0.88, 0.88, 0.90, 1.0), rough=0.08, metal=0.95)

    # 19. Azotea Impermeabilizada Asfáltica
    mats["azotea"] = _make_mat("M_Azotea_Asfalto", (0.04, 0.04, 0.045, 1.0), rough=0.95)

    # 20. Piso Interior Concreto Zaguán
    mats["piso_interior"] = _make_mat("M_Piso_Interior", (0.22, 0.22, 0.24, 1.0), rough=0.75)

    # 21. Nicho Interior Oscuro de Ventanas (Profundidad Tridimensional)
    mats["nicho_interior"] = _make_mat("M_Nicho_Interior", (0.04, 0.04, 0.045, 1.0), rough=0.95)

    # 22. Cortinas y Persianas Interiores
    mats["cortina_interior"] = _make_mat("M_Cortina_Interior", (0.88, 0.86, 0.82, 1.0), rough=0.60)

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

def build_ochava_corner(mats, col):
    """
    Construye la Ochava a 45º según Ground-Truth fotográfico media_1789813043362:
      - Torreón peraltado semicircular puro con golas de enlace hacia el pretil.
      - Arco/dintel de bloques de vidrio translúcido (pavés) sobre puerta de balcón.
      - Balcón volado con ménsulas de concreto escalonadas y barandal forjado.
      - Marquesina volada con placa de acero pulido y puertas oscuras en PB.
      - Mástil de luminaria vertical exterior.
    """
    bm_wall = bmesh.new()
    bm_paves = bmesh.new()
    bm_balcony = bmesh.new()
    bm_mensula = bmesh.new()
    bm_iron = bmesh.new()
    bm_dark = bmesh.new()
    bm_white = bmesh.new()
    bm_glass = bmesh.new()
    bm_mirror = bmesh.new()
    bm_sign = bmesh.new()

    center_xy = (1.40, 1.40)
    tangent_xy = (-0.7071, 0.7071)  # Paralelo a la ochava
    normal_xy = (-0.7071, -0.7071)  # Normal exterior hacia el parque

    # 1. Paredes de la Ochava en Planta Alta (Z: 3.65 a 7.10 m)
    # Machones laterales
    add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, -1.98, -1.05, 0.00, 0.35, 3.65, 7.10)
    add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, 1.05, 1.98, 0.00, 0.35, 3.65, 7.10)
    # Dintel corrido sobre puerta y pavés
    add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, -1.98, 1.98, 0.00, 0.35, 6.55, 7.15)

    # 2. Arco / Enmarque Ornamental de Pavés (Bloques de vidrio) sobre la puerta del balcón
    # Franja horizontal superior de pavés (Z: 5.85 a 6.45 m)
    add_oriented_box(bm_paves, center_xy, tangent_xy, normal_xy, -1.00, 1.00, 0.06, 0.30, 5.85, 6.45)
    # Moldura de enmarque de mortero
    add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, -1.05, 1.05, 0.02, 0.33, 6.45, 6.55)
    add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, -1.05, -0.98, 0.02, 0.33, 5.80, 6.45)
    add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, 0.98, 1.05, 0.02, 0.33, 5.80, 6.45)

    # 3. Puerta Francesa hacia el Balcón (Z: 3.65 a 5.85 m)
    add_oriented_box(bm_white, center_xy, tangent_xy, normal_xy, -0.95, 0.95, -0.06, 0.04, 3.65, 5.85) # Marco exterior blanco
    add_oriented_box(bm_dark, center_xy, tangent_xy, normal_xy, -0.90, 0.90, -0.05, 0.02, 3.70, 5.80)  # Cancelería oscura
    add_oriented_box(bm_dark, center_xy, tangent_xy, normal_xy, -0.04, 0.04, -0.06, 0.03, 3.70, 5.80)  # Parteluz central
    add_oriented_box(bm_glass, center_xy, tangent_xy, normal_xy, -0.85, -0.04, -0.02, 0.01, 3.75, 5.75)
    add_oriented_box(bm_glass, center_xy, tangent_xy, normal_xy, 0.04, 0.85, -0.02, 0.01, 3.75, 5.75)

    # 4. Losa de Balcón en Voladizo y Ménsulas de Concreto
    # Losa curva/ochavada saliente 1.15 m (+normal hacia afuera)
    add_oriented_box(bm_balcony, center_xy, tangent_xy, normal_xy, -2.15, 2.15, -0.05, 1.15, 3.45, 3.65)
    # Peana moldurada inferior
    add_oriented_box(bm_balcony, center_xy, tangent_xy, normal_xy, -2.00, 2.00, -0.10, 0.95, 3.30, 3.45)

    # Dos Ménsulas / Canecillos de concreto escalonadas bajo la losa
    for s_men in [-1.15, 1.15]:
        # Cuerpo principal de ménsula
        add_oriented_box(bm_mensula, center_xy, tangent_xy, normal_xy, s_men - 0.16, s_men + 0.16, 0.00, 0.80, 2.65, 3.30)
        # Escalonamiento inferior
        add_oriented_box(bm_mensula, center_xy, tangent_xy, normal_xy, s_men - 0.12, s_men + 0.12, 0.00, 0.55, 2.35, 2.65)

    # Barandal de hierro forjado ornamental (Z: 3.65 a 4.70 m, H = 1.05 m)
    add_oriented_box(bm_iron, center_xy, tangent_xy, normal_xy, -2.15, 2.15, 1.10, 1.15, 4.65, 4.70) # Pasamanos superior
    add_oriented_box(bm_iron, center_xy, tangent_xy, normal_xy, -2.15, 2.15, 1.10, 1.15, 3.65, 3.70) # Zócalo inferior
    add_oriented_box(bm_iron, center_xy, tangent_xy, normal_xy, -2.15, -2.10, 0.00, 1.15, 3.65, 4.70) # Lateral izq
    add_oriented_box(bm_iron, center_xy, tangent_xy, normal_xy, 2.10, 2.15, 0.00, 1.15, 3.65, 4.70)  # Lateral der
    for s_bar in [-1.90, -1.50, -1.10, -0.70, -0.30, 0.10, 0.50, 0.90, 1.30, 1.70]:
        add_oriented_box(bm_iron, center_xy, tangent_xy, normal_xy, s_bar - 0.025, s_bar + 0.025, 1.11, 1.14, 3.70, 4.65)

    # 5. Torreón Peraltado Semicircular Puro con Golas Cóncavas en Pretil
    # Modelado por franjas de alta resolución:
    steps = 32
    r_dome = 1.25
    h_base = 7.15
    h_apex = 9.15
    for i in range(steps):
        t1 = -1.98 + 3.96 * i / steps
        t2 = -1.98 + 3.96 * (i + 1) / steps
        # Altura según zona central semicircular o gola lateral cóncava
        def get_height(s):
            if abs(s) <= r_dome:
                # Torreón semicircular peraltado
                val = 1.0 - (s / r_dome)**2
                return h_base + 0.50 + (h_apex - (h_base + 0.50)) * math.sqrt(max(0.0, val))
            else:
                # Gola cóncava que desciende hacia el pretil recto
                u = (abs(s) - r_dome) / (1.98 - r_dome)
                return (h_base + 0.50) - 0.50 * (u**1.5)

        h1 = get_height(t1)
        h2 = get_height(t2)
        add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, t1, t2, 0.00, 0.35, 7.15, max(h1, h2))

    # Ventila / Rejilla rectangular superior de ventilación en el torreón
    add_oriented_box(bm_dark, center_xy, tangent_xy, normal_xy, -0.25, 0.25, 0.04, 0.32, 7.85, 8.35)
    add_oriented_box(bm_iron, center_xy, tangent_xy, normal_xy, -0.22, 0.22, 0.02, 0.06, 7.90, 8.30)

    # 6. Planta Baja: Marquesina Volada de Acero Espejo y Puertas Correderas Oscuras
    # Paredes laterales PB (Z: 0.00 a 2.85 m)
    add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, -1.98, -1.30, 0.00, 0.35, 0.00, 2.85)
    add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, 1.30, 1.98, 0.00, 0.35, 0.00, 2.85)
    add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, -1.98, 1.98, 0.00, 0.35, 2.80, 3.45)

    # Marquesina volada metálica con placa de acero espejo pulido
    add_oriented_box(bm_mirror, center_xy, tangent_xy, normal_xy, -1.35, 1.35, 0.05, 0.40, 2.85, 3.35)
    # Ménsula de estuco en el flanco izquierdo de la marquesina
    add_oriented_box(bm_wall, center_xy, tangent_xy, normal_xy, -1.45, -1.35, 0.00, 0.38, 2.70, 3.35)

    # Puertas correderas de cristal templado en PB
    add_oriented_box(bm_dark, center_xy, tangent_xy, normal_xy, -1.25, 1.25, -0.05, 0.08, 0.00, 2.80) # Marco
    add_oriented_box(bm_dark, center_xy, tangent_xy, normal_xy, -0.04, 0.04, -0.05, 0.08, 0.00, 2.80) # Parteluz
    add_oriented_box(bm_glass, center_xy, tangent_xy, normal_xy, -1.20, -0.04, -0.02, 0.02, 0.10, 2.70)
    add_oriented_box(bm_glass, center_xy, tangent_xy, normal_xy, 0.04, 1.20, -0.02, 0.02, 0.10, 2.70)

    # Respaldo opaco interior para erradicar transparencias en ochava
    add_oriented_box(bm_dark, center_xy, tangent_xy, normal_xy, -0.95, 0.95, -0.16, -0.06, 3.65, 5.85)
    add_oriented_box(bm_dark, center_xy, tangent_xy, normal_xy, -1.25, 1.25, -0.16, -0.06, 0.00, 2.80)

    # 7. Mástil y Luminaria Vertical en Fachada
    # Mástil tubular
    add_box(bm_white, 0.20, 0.28, 2.45, 2.53, 4.40, 6.20)
    # Luminaria rectangular blanca
    add_box(bm_white, 0.15, 0.33, 2.40, 2.58, 4.60, 5.80)

    # 8. Rótulo Volado "HOTEL TECATE Tel. 654-11-16"
    add_box(bm_sign, 2.55, 2.65, -1.80, 0.10, 4.85, 4.95)
    add_box(bm_sign, 2.58, 2.62, -1.80, -0.20, 4.00, 5.20)

    obj_wall_o = create_mesh_object("Ochava_Muro_Remate", bm_wall, mats["estuco"], col)
    obj_paves = create_mesh_object("Ochava_Paves_Arco", bm_paves, mats["paves"], col)
    obj_balcony = create_mesh_object("Ochava_Balcon_Losa", bm_balcony, mats["moldura"], col)
    obj_mensula = create_mesh_object("Ochava_Mensulas_Concreto", bm_mensula, mats["mensula"], col)
    obj_iron = create_mesh_object("Ochava_Barandal_Forja", bm_iron, mats["hierro_forjado"], col)
    obj_dark_o = create_mesh_object("Ochava_Canceleria_Oscura", bm_dark, mats["alum_oscuro"], col)
    obj_white_o = create_mesh_object("Ochava_Canceleria_Blanca", bm_white, mats["alum_blanco"], col)
    obj_glass_o = create_mesh_object("Ochava_Vidrio", bm_glass, mats["vidrio"], col)
    obj_mirror = create_mesh_object("Ochava_Marquesina_Espejo", bm_mirror, mats["acero_espejo"], col)
    obj_sign_panel = create_mesh_object("Ochava_Rotulo_Panel", bm_sign, mats["panel_blanco"], col)

    # Rótulos en texto 3D sobre cartel volado
    t_h_norte = create_3d_text("Texto_Hotel_Norte", "HOTEL\nTECATE", 0.36, 0.015, mats["texto_rojo"], col)
    t_h_norte.location = Vector((2.55, -1.00, 4.80))
    t_h_norte.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))

    t_tel_norte = create_3d_text("Texto_Tel_Norte", "Tel. 654-11-16", 0.13, 0.012, mats["texto_azul"], col)
    t_tel_norte.location = Vector((2.55, -1.00, 4.20))
    t_tel_norte.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))

    t_h_sur = create_3d_text("Texto_Hotel_Sur", "HOTEL\nTECATE", 0.36, 0.015, mats["texto_rojo"], col)
    t_h_sur.location = Vector((2.65, -1.00, 4.80))
    t_h_sur.rotation_euler = (math.radians(90.0), 0.0, math.radians(90.0))

    t_tel_sur = create_3d_text("Texto_Tel_Sur", "Tel. 654-11-16", 0.13, 0.012, mats["texto_azul"], col)
    t_tel_sur.location = Vector((2.65, -1.00, 4.20))
    t_tel_sur.rotation_euler = (math.radians(90.0), 0.0, math.radians(90.0))

    return [obj_wall_o, obj_paves, obj_balcony, obj_mensula, obj_iron, obj_dark_o, obj_white_o, obj_glass_o, obj_mirror, obj_sign_panel, t_h_norte, t_tel_norte, t_h_sur, t_tel_sur]

def build_north_facade_libertad(mats, col):
    """
    Construye la Fachada Norte sobre Callejón Libertad (Y: 2.80 a 20.40 m) según media_1789812951496:
      - 5 crujías completas moduladas por dados sobresalientes en pretil.
      - Crujía N5: Toldo negro Casa Paris y ventana superior grande.
      - Crujía N4: SUBWAY con letras 3D institucionales directas al muro, ventana vertical + ventana ancha.
      - Crujía N3: La Michoacana con persiana enrollable, reja de servicio y ventanita vertical.
      - Crujía N2: Ventana doble centrada y persiana comercial cerrada.
      - Crujía N1: Ventana doble + ventanita compañera, escudo Tecate y sombrillas rojas de terraza.
    """
    bm_wall = bmesh.new()
    bm_dark = bmesh.new()
    bm_glass = bmesh.new()
    bm_white = bmesh.new()
    bm_shutter = bmesh.new()
    bm_toldo_negro = bmesh.new()
    bm_sombrillas = bmesh.new()

    # -----------------------------------------------------------------------
    # Planta Baja: Muros Macizos Continuos y Dinteles (Z: 0.00 a 3.20 m)
    # -----------------------------------------------------------------------
    # Paños ciegos entre locales de PB:
    add_box(bm_wall, 0.00, 0.35, 2.80, 3.10, 0.00, 3.20)   # Junto a Ochava
    add_box(bm_wall, 0.00, 0.35, 6.10, 6.60, 0.00, 3.20)   # Entre Casa Paris y Subway
    add_box(bm_wall, 0.00, 0.35, 7.60, 7.80, 0.00, 3.20)   # Entre puerta Subway y escaparate
    add_box(bm_wall, 0.00, 0.35, 10.60, 11.00, 0.00, 3.20)  # Entre Subway y Michoacana
    add_box(bm_wall, 0.00, 0.35, 14.00, 14.40, 0.00, 3.20)  # Entre Michoacana y N2
    add_box(bm_wall, 0.00, 0.35, 17.30, 17.70, 0.00, 3.20)  # Entre N2 y N1 (Lolos)
    add_box(bm_wall, 0.00, 0.35, 20.20, 20.40, 0.00, 3.20)  # Extremo oriente

    # Dinteles sobre vanos comerciales de PB:
    add_box(bm_wall, 0.00, 0.35, 3.10, 6.10, 2.80, 3.20)    # Sobre Casa Paris
    add_box(bm_wall, 0.00, 0.35, 6.60, 7.60, 2.75, 3.20)    # Sobre puerta acceso Subway
    add_box(bm_wall, 0.00, 0.35, 7.80, 10.60, 2.75, 3.20)   # Sobre escaparate Subway
    add_box(bm_wall, 0.00, 0.35, 11.00, 14.00, 2.75, 3.20)  # Sobre Michoacana
    add_box(bm_wall, 0.00, 0.35, 14.40, 17.30, 2.75, 3.20)  # Sobre N2
    add_box(bm_wall, 0.00, 0.35, 17.70, 20.20, 2.75, 3.20)  # Sobre Lolos

    # Muro base antepecho PA (Z: 3.20 a 4.55 m)
    add_box(bm_wall, 0.00, 0.35, 2.80, 20.40, 3.20, 4.55)
    # Dintel superior corrido PA (Z: 6.25 a 7.15 m)
    add_box(bm_wall, 0.00, 0.35, 2.80, 20.40, 6.25, 7.15)
    # Pretil corrido horizontal
    add_box(bm_wall, -0.05, 0.40, 2.80, 20.40, 7.05, 7.25)
    add_box(bm_wall, -0.08, 0.43, 2.75, 20.45, 7.25, 7.32)

    # Pilastras verticales y dados cúbicos sobresalientes en pretil
    pilastras_y = [2.80, 6.40, 10.80, 14.20, 17.50, 20.40]
    for py in pilastras_y:
        # Pilastra adosada en fachada
        add_box(bm_wall, -0.10, 0.02, py - 0.18, py + 0.18, 0.00, 7.45)
        # Dado cúbico almenado que sobresale por encima del pretil
        add_box(bm_wall, -0.14, 0.05, py - 0.22, py + 0.22, 7.45, 7.62)

    # -----------------------------------------------------------------------
    # Crujía N5 (Junto a Ochava, Y: 2.80 a 6.40 m)
    # -----------------------------------------------------------------------
    # Machones PA
    add_box(bm_wall, 0.00, 0.35, 2.80, 3.60, 4.55, 6.25)
    add_box(bm_wall, 0.00, 0.35, 5.60, 6.40, 4.55, 6.25)
    # Ventana corredera grande N5 (Y: 3.60 a 5.60 m)
    add_box(bm_white, 0.10, 0.16, 3.60, 5.60, 4.55, 6.25)
    add_box(bm_white, 0.12, 0.18, 4.55, 4.65, 4.60, 6.20)
    add_box(bm_glass, 0.13, 0.15, 3.65, 5.55, 4.60, 6.20)
    # Respaldo opaco interior ventana N5
    add_box(bm_dark, 0.30, 0.35, 3.55, 5.65, 4.50, 6.30)

    # PB: Cancel comercial y Toldo Negro Casa Paris
    add_box(bm_dark, 0.08, 0.12, 3.10, 6.10, 0.00, 2.80)
    add_box(bm_glass, 0.09, 0.11, 3.15, 6.05, 0.10, 2.70)
    add_box(bm_dark, 0.30, 0.35, 3.05, 6.15, 0.00, 2.85) # Respaldo opaco PB
    # Toldo rectangular negro
    add_box(bm_toldo_negro, -0.95, 0.05, 3.00, 6.20, 2.80, 3.35)
    add_box(bm_toldo_negro, -1.00, -0.95, 3.00, 6.20, 2.55, 2.80)

    # -----------------------------------------------------------------------
    # Crujía N4 — Franquicia SUBWAY (Y: 6.40 a 10.80 m)
    # -----------------------------------------------------------------------
    # Machones PA
    add_box(bm_wall, 0.00, 0.35, 6.40, 6.90, 4.55, 6.25)
    add_box(bm_wall, 0.00, 0.35, 7.80, 8.30, 4.55, 6.25)
    add_box(bm_wall, 0.00, 0.35, 10.30, 10.80, 4.55, 6.25)
    # Relleno de muro macizo arriba/abajo de ventana vertical N4a (Z: 4.60 a 6.20 m)
    add_box(bm_wall, 0.00, 0.35, 6.90, 7.80, 4.55, 4.60)
    add_box(bm_wall, 0.00, 0.35, 6.90, 7.80, 6.20, 6.25)
    add_box(bm_white, 0.10, 0.16, 6.90, 7.80, 4.60, 6.20)
    add_box(bm_glass, 0.13, 0.15, 6.95, 7.75, 4.65, 6.15)
    add_box(bm_dark, 0.30, 0.35, 6.85, 7.85, 4.55, 6.25)

    # Relleno de muro macizo arriba/abajo de ventana ancha N4b (Z: 4.70 a 6.10 m)
    add_box(bm_wall, 0.00, 0.35, 8.30, 10.30, 4.55, 4.70)
    add_box(bm_wall, 0.00, 0.35, 8.30, 10.30, 6.10, 6.25)
    add_box(bm_white, 0.10, 0.16, 8.30, 10.30, 4.70, 6.10)
    add_box(bm_white, 0.12, 0.18, 9.25, 9.35, 4.75, 6.05)
    add_box(bm_glass, 0.13, 0.15, 8.35, 10.25, 4.75, 6.05)
    add_box(bm_dark, 0.30, 0.35, 8.25, 10.35, 4.65, 6.15)

    # PB Subway: Puerta vidriada izq + escaparate con persiana enrollable
    add_box(bm_dark, 0.08, 0.12, 6.60, 7.60, 0.00, 2.75) # Puerta acceso vidriada
    add_box(bm_glass, 0.09, 0.11, 6.65, 7.55, 0.10, 2.65)
    add_box(bm_dark, 0.30, 0.35, 6.55, 7.65, 0.00, 2.80)
    add_box(bm_dark, 0.08, 0.12, 7.80, 10.60, 0.00, 2.75) # Escaparate
    add_box(bm_glass, 0.09, 0.11, 7.85, 10.55, 0.10, 2.10)
    add_box(bm_shutter, 0.10, 0.12, 7.85, 10.55, 2.10, 2.75) # Persiana semi-abierta
    add_box(bm_dark, 0.30, 0.35, 7.75, 10.65, 0.00, 2.80)

    # -----------------------------------------------------------------------
    # Crujía N3 — La Michoacana / Reja de Servicio (Y: 10.80 a 14.20 m)
    # -----------------------------------------------------------------------
    add_box(bm_wall, 0.00, 0.35, 10.80, 12.20, 4.55, 6.25)
    add_box(bm_wall, 0.00, 0.35, 12.80, 14.20, 4.55, 6.25)
    # Relleno de muro macizo en ventanita N3 (Z: 4.85 a 5.85 m)
    add_box(bm_wall, 0.00, 0.35, 12.20, 12.80, 4.55, 4.85)
    add_box(bm_wall, 0.00, 0.35, 12.20, 12.80, 5.85, 6.25)
    add_box(bm_white, 0.10, 0.16, 12.20, 12.80, 4.85, 5.85)
    add_box(bm_glass, 0.13, 0.15, 12.25, 12.75, 4.90, 5.80)
    add_box(bm_dark, 0.30, 0.35, 12.15, 12.85, 4.80, 5.90)
    # PB: Reja metálica de servicio y Local Michoacana
    add_box(bm_dark, 0.06, 0.12, 11.00, 11.80, 0.00, 2.75)
    for ry in [11.20, 11.40, 11.60]:
        add_box(bm_dark, 0.08, 0.10, ry - 0.02, ry + 0.02, 0.10, 2.65)
    add_box(bm_dark, 0.30, 0.35, 10.95, 11.85, 0.00, 2.80)
    add_box(bm_shutter, 0.10, 0.12, 12.00, 14.00, 0.10, 2.75)
    add_box(bm_dark, 0.30, 0.35, 11.95, 14.05, 0.00, 2.80)
    # Rótulo verde La Michoacana
    add_box(bm_wall, -0.06, 0.02, 11.90, 14.10, 2.80, 3.25)

    # -----------------------------------------------------------------------
    # Crujía N2 (Y: 14.20 a 17.50 m)
    # -----------------------------------------------------------------------
    add_box(bm_wall, 0.00, 0.35, 14.20, 15.20, 4.55, 6.25)
    add_box(bm_wall, 0.00, 0.35, 16.60, 17.50, 4.55, 6.25)
    # Ventana doble PA (Y: 15.20 a 16.60 m)
    add_box(bm_white, 0.10, 0.16, 15.20, 16.60, 4.55, 6.25)
    add_box(bm_white, 0.12, 0.18, 15.85, 15.95, 4.60, 6.20)
    add_box(bm_glass, 0.13, 0.15, 15.25, 16.55, 4.60, 6.20)
    add_box(bm_dark, 0.30, 0.35, 15.15, 16.65, 4.50, 6.30)
    # PB Persiana metálica cerrada
    add_box(bm_dark, 0.08, 0.12, 14.40, 17.30, 0.00, 2.75)
    add_box(bm_shutter, 0.10, 0.12, 14.45, 17.25, 0.10, 2.70)
    add_box(bm_dark, 0.30, 0.35, 14.35, 17.35, 0.00, 2.80)

    # -----------------------------------------------------------------------
    # Crujía N1 (Oriente, Y: 17.50 a 20.40 m)
    # -----------------------------------------------------------------------
    add_box(bm_wall, 0.00, 0.35, 17.50, 17.80, 4.55, 6.25)
    add_box(bm_wall, 0.00, 0.35, 19.10, 19.40, 4.55, 6.25)
    add_box(bm_wall, 0.00, 0.35, 19.90, 20.40, 4.55, 6.25)
    # Ventana doble N1a (Y: 17.80 a 19.10 m)
    add_box(bm_white, 0.10, 0.16, 17.80, 19.10, 4.55, 6.25)
    add_box(bm_glass, 0.13, 0.15, 17.85, 19.05, 4.60, 6.20)
    add_box(bm_dark, 0.30, 0.35, 17.75, 19.15, 4.50, 6.30)
    # Relleno de muro macizo en ventanita auxiliar N1b (Z: 4.80 a 5.80 m)
    add_box(bm_wall, 0.00, 0.35, 19.40, 19.90, 4.55, 4.80)
    add_box(bm_wall, 0.00, 0.35, 19.40, 19.90, 5.80, 6.25)
    add_box(bm_white, 0.10, 0.16, 19.40, 19.90, 4.80, 5.80)
    add_box(bm_glass, 0.13, 0.15, 19.45, 19.85, 4.85, 5.75)
    add_box(bm_dark, 0.30, 0.35, 19.35, 19.95, 4.75, 5.85)

    # Escudo / Logotipo Tecate "T" en muro (Z = 3.60 a 4.15 m)
    add_box(bm_dark, -0.06, 0.02, 18.20, 18.75, 3.60, 4.15)
    # PB: Local LOLOS y Terraza con sombrillas rojas
    add_box(bm_dark, 0.08, 0.12, 17.70, 20.20, 0.00, 2.75)
    add_box(bm_glass, 0.09, 0.11, 17.75, 20.15, 0.10, 2.70)
    add_box(bm_dark, 0.30, 0.35, 17.65, 20.25, 0.00, 2.80)
    # Sombrillas rojas exteriores
    for sy in [18.20, 19.60]:
        add_box(bm_sombrillas, -1.80, -0.60, sy - 0.60, sy + 0.60, 2.30, 2.50)
        add_box(bm_sombrillas, -1.50, -0.90, sy - 0.30, sy + 0.30, 2.50, 2.80)
        add_box(bm_dark, -1.25, -1.15, sy - 0.05, sy + 0.05, 0.00, 2.30) # Mástil sombrilla

    # -----------------------------------------------------------------------
    # Logotipo Institucional SUBWAY 3D (Silueta Verde, SUB Blanco, WAY Amarillo, Flechas)
    # -----------------------------------------------------------------------
    bm_subway_green = bmesh.new()
    bm_arrow_w = bmesh.new()
    bm_arrow_y = bmesh.new()

    # 1. Silueta verde biselada / Contorno (#008938)
    add_box(bm_subway_green, -0.06, 0.01, 7.60, 10.45, 3.32, 4.02)
    add_box(bm_subway_green, -0.07, -0.04, 7.56, 10.49, 3.28, 4.06)

    # 2. Flechas 3D canónicas del logotipo:
    def add_arrow_left(bm, x_min, x_max, y_tip, y_base, z_center, z_half):
        v1 = bm.verts.new((x_min, y_tip, z_center))
        v2 = bm.verts.new((x_min, y_base, z_center + z_half))
        v3 = bm.verts.new((x_min, y_base, z_center - z_half))
        v4 = bm.verts.new((x_max, y_tip, z_center))
        v5 = bm.verts.new((x_max, y_base, z_center + z_half))
        v6 = bm.verts.new((x_max, y_base, z_center - z_half))
        bm.faces.new((v1, v2, v3))
        bm.faces.new((v4, v6, v5))
        bm.faces.new((v1, v4, v5, v2))
        bm.faces.new((v2, v5, v6, v3))
        bm.faces.new((v3, v6, v4, v1))

    def add_arrow_right(bm, x_min, x_max, y_tip, y_base, z_center, z_half):
        v1 = bm.verts.new((x_min, y_tip, z_center))
        v2 = bm.verts.new((x_min, y_base, z_center - z_half))
        v3 = bm.verts.new((x_min, y_base, z_center + z_half))
        v4 = bm.verts.new((x_max, y_tip, z_center))
        v5 = bm.verts.new((x_max, y_base, z_center - z_half))
        v6 = bm.verts.new((x_max, y_base, z_center + z_half))
        bm.faces.new((v1, v2, v3))
        bm.faces.new((v4, v6, v5))
        bm.faces.new((v1, v4, v5, v2))
        bm.faces.new((v2, v5, v6, v3))
        bm.faces.new((v3, v6, v4, v1))

    # Flecha izquierda blanca en 'S' (Y: 10.15 a 10.35, Z = 3.86, apunta hacia +Y/izquierda)
    add_arrow_left(bm_arrow_w, -0.12, -0.06, 10.35, 10.15, 3.86, 0.10)
    # Flecha derecha amarilla en 'Y' (Y: 7.65 a 7.85, Z = 3.86, apunta hacia -Y/derecha)
    add_arrow_right(bm_arrow_y, -0.12, -0.06, 7.65, 7.85, 3.86, 0.10)

    # Objetos de malla
    obj_wall_n = create_mesh_object("Fachada_Norte_Muro", bm_wall, mats["estuco"], col)
    obj_dark_n = create_mesh_object("Fachada_Norte_AlumOscuro", bm_dark, mats["alum_oscuro"], col)
    obj_glass_n = create_mesh_object("Fachada_Norte_Vidrio", bm_glass, mats["vidrio"], col)
    obj_white_n = create_mesh_object("Fachada_Norte_AlumBlanco", bm_white, mats["alum_blanco"], col)
    obj_shutter_n = create_mesh_object("Fachada_Norte_Cortinas", bm_shutter, mats["cortina_metalica"], col)
    obj_toldo_n = create_mesh_object("Fachada_Norte_ToldoNegro", bm_toldo_negro, mats["toldo_negro"], col)
    obj_somb = create_mesh_object("Fachada_Norte_Sombrillas", bm_sombrillas, mats["sombrilla_roja"], col)
    obj_sub_plate = create_mesh_object("Subway_Placa_Verde", bm_subway_green, mats["subway_verde"], col)
    obj_arr_w = create_mesh_object("Subway_Flecha_S", bm_arrow_w, mats["subway_blanco"], col)
    obj_arr_y = create_mesh_object("Subway_Flecha_Y", bm_arrow_y, mats["subway_amarillo"], col)

    # Textos 3D Subway (SUB a la izquierda en blanco, WAY a la derecha en amarillo)
    t_sub = create_3d_text("Texto_SUB", "SUB", 0.52, 0.05, mats["subway_blanco"], col)
    t_sub.location = Vector((-0.07, 10.18, 3.42))
    t_sub.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))

    t_way = create_3d_text("Texto_WAY", "WAY", 0.52, 0.05, mats["subway_amarillo"], col)
    t_way.location = Vector((-0.07, 9.08, 3.42))
    t_way.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))

    # Rótulo Casa Paris en toldo negro
    t_paris = create_3d_text("Texto_CasaParis", "CASA PARIS", 0.16, 0.02, mats["panel_blanco"], col)
    t_paris.location = Vector((-1.01, 4.60, 2.68))
    t_paris.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))

    return [obj_wall_n, obj_dark_n, obj_glass_n, obj_white_n, obj_shutter_n, obj_toldo_n, obj_somb, obj_sub_plate, obj_arr_w, obj_arr_y, t_sub, t_way, t_paris]

def build_west_facade_cardenas(mats, col):
    """
    Construye la Fachada Oeste sobre Calle Presidente Lázaro Cárdenas (X: 2.80 a 28.60 m) según media_1789812991532:
      - Pilastras verticales completas con dados almenados sobre pretil.
      - Módulo 1 (Ochava): Ventana grande + ventanita + compresor minisplit A/C en fachada.
      - Módulo 2: Ventana alargada horizontal + ventana vertical + ventana grande doble + ventanita. PB con cancel, display circular y puerta ciega.
      - Módulo 3: Ventana vertical + ventana horizontal + par de ventanitas gemelas [][]. PB con dos toldos contiguos inclinados color arena.
      - Módulo 4: Ventanas variadas en PA, franja corrida de pavés y Toldo Rojo Coca-Cola Taquería Los Gallos sobre zaguán transitable.
      - Módulo 5 (Sur): Ventana corredera grande en PA, toldo verde oscuro / azul marino y rótulos Internet World en PB.
    """
    bm_wall = bmesh.new()
    bm_dark = bmesh.new()
    bm_glass = bmesh.new()
    bm_white = bmesh.new()
    bm_shutter = bmesh.new()
    bm_paves = bmesh.new()
    bm_toldo_arena = bmesh.new()
    bm_toldo_rojo = bmesh.new()
    bm_toldo_azul = bmesh.new()
    bm_minisplit = bmesh.new()
    bm_interior = bmesh.new()

    # Muro base antepecho PA (Z: 3.20 a 4.55 m)
    add_box(bm_wall, 2.80, 20.00, 0.00, 0.35, 3.20, 4.55)
    add_box(bm_wall, 24.80, 28.60, 0.00, 0.35, 3.20, 4.55)
    # Dintel corrido PA (Z: 6.25 a 7.15 m)
    add_box(bm_wall, 2.80, 28.60, 0.00, 0.35, 6.25, 7.15)
    # Pretil corrido horizontal
    add_box(bm_wall, 2.80, 28.60, -0.05, 0.40, 7.05, 7.25)
    add_box(bm_wall, 2.75, 28.65, -0.08, 0.43, 7.25, 7.32)

    # Pilastras verticales y dados almenados sobre pretil
    pilastras_x = [2.80, 6.80, 11.20, 16.00, 20.00, 24.80, 28.60]
    for px in pilastras_x:
        add_box(bm_wall, px - 0.18, px + 0.18, -0.10, 0.02, 0.00, 7.45)
        add_box(bm_wall, px - 0.22, px + 0.22, -0.14, 0.05, 7.45, 7.62)

    # -----------------------------------------------------------------------
    # Módulo 1 (X: 2.80 a 6.80 m)
    # -----------------------------------------------------------------------
    add_box(bm_wall, 2.80, 3.30, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 4.80, 5.20, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 5.80, 6.20, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 6.70, 6.80, 0.00, 0.35, 4.55, 6.25)
    # Relleno de muros ciegos en PA sobre y bajo vanos
    add_box(bm_wall, 5.20, 5.80, 0.00, 0.35, 4.55, 5.20)
    add_box(bm_wall, 5.20, 5.80, 0.00, 0.35, 5.80, 6.25)
    add_box(bm_wall, 6.20, 6.70, 0.00, 0.35, 4.55, 4.70)
    add_box(bm_wall, 6.20, 6.70, 0.00, 0.35, 5.70, 6.25)
    # Ventana 1a: Corredera grande blanca (X: 3.30 a 4.80 m)
    add_box(bm_white, 3.30, 4.80, 0.10, 0.16, 4.55, 6.25)
    add_box(bm_white, 4.00, 4.10, 0.12, 0.18, 4.60, 6.20)
    add_box(bm_glass, 3.35, 4.75, 0.13, 0.15, 4.60, 6.20)
    add_box(bm_dark, 3.25, 4.85, 0.30, 0.35, 4.50, 6.30)
    # Ventanita 1b: Cuadrada alta (X: 5.20 a 5.80 m)
    add_box(bm_white, 5.20, 5.80, 0.10, 0.16, 5.20, 5.80)
    add_box(bm_glass, 5.25, 5.75, 0.13, 0.15, 5.25, 5.75)
    add_box(bm_dark, 5.15, 5.85, 0.30, 0.35, 5.15, 5.85)
    # Compresor Minisplit A/C en fachada (debajo de ventanita 1b)
    add_box(bm_minisplit, 5.05, 5.85, -0.42, -0.05, 3.75, 4.35)
    add_box(bm_dark, 5.45, 5.80, -0.44, -0.41, 3.82, 4.28) # Rejilla ventilador
    # Ventanita 1c: Vertical (X: 6.20 a 6.70 m)
    add_box(bm_white, 6.20, 6.70, 0.10, 0.16, 4.70, 5.70)
    add_box(bm_glass, 6.25, 6.65, 0.13, 0.15, 4.75, 5.65)
    add_box(bm_dark, 6.15, 6.75, 0.30, 0.35, 4.65, 5.75)
    # PB Módulo 1: Muro continuo, cancel y dintel
    add_box(bm_wall, 2.80, 3.10, 0.00, 0.35, 0.00, 3.20)
    add_box(bm_wall, 3.10, 6.50, 0.00, 0.35, 2.80, 3.20)
    add_box(bm_wall, 6.50, 6.80, 0.00, 0.35, 0.00, 3.20)
    add_box(bm_dark, 3.10, 6.50, 0.08, 0.12, 0.00, 2.80)
    add_box(bm_glass, 3.15, 6.45, 0.09, 0.11, 0.10, 2.20)
    add_box(bm_shutter, 3.15, 6.45, 0.10, 0.12, 2.20, 2.80)
    add_box(bm_dark, 3.05, 6.55, 0.30, 0.35, 0.00, 2.80)

    # -----------------------------------------------------------------------
    # Módulo 2 (X: 6.80 a 11.20 m)
    # -----------------------------------------------------------------------
    add_box(bm_wall, 6.80, 7.10, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 7.80, 8.10, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 8.80, 9.20, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 10.60, 10.80, 0.00, 0.35, 4.55, 6.25)
    # Relleno de muros ciegos en PA
    add_box(bm_wall, 7.10, 7.80, 0.00, 0.35, 4.55, 5.20)
    add_box(bm_wall, 7.10, 7.80, 0.00, 0.35, 5.70, 6.25)
    add_box(bm_wall, 8.10, 8.80, 0.00, 0.35, 4.55, 4.60)
    add_box(bm_wall, 8.10, 8.80, 0.00, 0.35, 6.10, 6.25)
    add_box(bm_wall, 10.80, 11.15, 0.00, 0.35, 4.55, 4.80)
    add_box(bm_wall, 10.80, 11.15, 0.00, 0.35, 5.70, 6.25)
    # Ventanita 2a: Horizontal alargada (X: 7.10 a 7.80 m)
    add_box(bm_white, 7.10, 7.80, 0.10, 0.16, 5.20, 5.70)
    add_box(bm_glass, 7.15, 7.75, 0.13, 0.15, 5.25, 5.65)
    add_box(bm_dark, 7.05, 7.85, 0.30, 0.35, 5.15, 5.75)
    # Ventana 2b: Vertical corredera (X: 8.10 a 8.80 m)
    add_box(bm_white, 8.10, 8.80, 0.10, 0.16, 4.60, 6.10)
    add_box(bm_glass, 8.15, 8.75, 0.13, 0.15, 4.65, 6.05)
    add_box(bm_dark, 8.05, 8.85, 0.30, 0.35, 4.55, 6.15)
    # Ventana 2c: Doble grande blanca (X: 9.20 a 10.60 m)
    add_box(bm_white, 9.20, 10.60, 0.10, 0.16, 4.55, 6.25)
    add_box(bm_white, 9.85, 9.95, 0.12, 0.18, 4.60, 6.20)
    add_box(bm_glass, 9.25, 10.55, 0.13, 0.15, 4.60, 6.20)
    add_box(bm_dark, 9.15, 10.65, 0.30, 0.35, 4.50, 6.30)
    # Ventanita 2d: Vertical delgada (X: 10.80 a 11.15 m)
    add_box(bm_white, 10.80, 11.15, 0.10, 0.16, 4.80, 5.70)
    add_box(bm_glass, 10.85, 11.10, 0.13, 0.15, 4.85, 5.65)
    add_box(bm_dark, 10.75, 11.20, 0.30, 0.35, 4.75, 5.75)
    # PB Módulo 2: Muro macizo, cancel comercial, display circular y puerta ciega
    add_box(bm_wall, 6.80, 7.10, 0.00, 0.35, 0.00, 3.20)
    add_box(bm_wall, 7.10, 9.50, 0.00, 0.35, 2.80, 3.20)
    add_box(bm_wall, 9.50, 10.30, 0.00, 0.35, 0.00, 3.20)
    add_box(bm_wall, 10.30, 11.10, 0.00, 0.35, 2.40, 3.20)
    add_box(bm_wall, 11.10, 11.20, 0.00, 0.35, 0.00, 3.20)
    add_box(bm_dark, 7.10, 9.50, 0.08, 0.12, 0.00, 2.80)
    add_box(bm_glass, 7.15, 9.45, 0.09, 0.11, 0.10, 2.20)
    add_box(bm_shutter, 7.15, 9.45, 0.10, 0.12, 2.20, 2.80)
    add_box(bm_dark, 7.05, 9.55, 0.30, 0.35, 0.00, 2.80)
    # Display circular negro en pared (X = 9.80, Z = 3.20)
    add_box(bm_dark, 9.60, 10.00, -0.06, 0.02, 3.00, 3.40)
    add_box(bm_white, 9.65, 9.95, -0.08, -0.05, 3.05, 3.35)
    # Puerta peatonal ciega
    add_box(bm_dark, 10.30, 11.10, 0.06, 0.12, 0.00, 2.40)
    add_box(bm_dark, 10.25, 11.15, 0.30, 0.35, 0.00, 2.40)

    # -----------------------------------------------------------------------
    # Módulo 3 (X: 11.20 a 16.00 m)
    # -----------------------------------------------------------------------
    add_box(bm_wall, 11.20, 11.40, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 11.90, 12.20, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 13.40, 13.70, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 14.15, 14.25, 0.00, 0.35, 4.55, 6.25) # Entre ventanitas gemelas
    add_box(bm_wall, 14.70, 15.00, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 15.80, 16.00, 0.00, 0.35, 4.55, 6.25)
    # Rellenos de muros ciegos en PA sobre y bajo vanos
    add_box(bm_wall, 11.40, 11.90, 0.00, 0.35, 4.55, 4.80)
    add_box(bm_wall, 11.40, 11.90, 0.00, 0.35, 5.80, 6.25)
    add_box(bm_wall, 12.20, 13.40, 0.00, 0.35, 4.55, 4.70)
    add_box(bm_wall, 12.20, 13.40, 0.00, 0.35, 6.00, 6.25)
    add_box(bm_wall, 13.70, 14.70, 0.00, 0.35, 4.55, 4.90)
    add_box(bm_wall, 13.70, 14.70, 0.00, 0.35, 5.60, 6.25)
    # Ventanita 3a: Vertical (X: 11.40 a 11.90 m)
    add_box(bm_white, 11.40, 11.90, 0.10, 0.16, 4.80, 5.80)
    add_box(bm_glass, 11.45, 11.85, 0.13, 0.15, 4.85, 5.75)
    add_box(bm_dark, 11.35, 11.95, 0.30, 0.35, 4.75, 5.85)
    # Ventana 3b: Horizontal (X: 12.20 a 13.40 m)
    add_box(bm_white, 12.20, 13.40, 0.10, 0.16, 4.70, 6.00)
    add_box(bm_glass, 12.25, 13.35, 0.13, 0.15, 4.75, 5.95)
    add_box(bm_dark, 12.15, 13.45, 0.30, 0.35, 4.65, 6.05)
    # Par de ventanitas gemelas cuadradas [][]:
    add_box(bm_white, 13.70, 14.15, 0.10, 0.16, 4.90, 5.60)
    add_box(bm_glass, 13.75, 14.10, 0.13, 0.15, 4.95, 5.55)
    add_box(bm_white, 14.25, 14.70, 0.10, 0.16, 4.90, 5.60)
    add_box(bm_glass, 14.30, 14.65, 0.13, 0.15, 4.95, 5.55)
    add_box(bm_dark, 13.65, 14.75, 0.30, 0.35, 4.85, 5.65)
    # Ventana 3c: Rectangular con persianas verticales interiores (X: 15.00 a 15.80 m)
    add_box(bm_white, 15.00, 15.80, 0.10, 0.16, 4.55, 6.25)
    add_box(bm_glass, 15.05, 15.75, 0.13, 0.15, 4.60, 6.20)
    add_box(bm_dark, 14.95, 15.85, 0.30, 0.35, 4.50, 6.30)
    # PB Módulo 3: Muros continuos, persiana cerrada y DOS TOLDOS CONTIGUOS COLOR ARENA
    add_box(bm_wall, 11.20, 11.30, 0.00, 0.35, 0.00, 3.20)
    add_box(bm_wall, 11.30, 12.60, 0.00, 0.35, 2.75, 3.20)
    add_box(bm_wall, 12.60, 12.75, 0.00, 0.35, 0.00, 3.20)
    add_box(bm_wall, 12.75, 14.30, 0.00, 0.35, 2.65, 3.20)
    add_box(bm_wall, 14.30, 14.50, 0.00, 0.35, 0.00, 3.20)
    add_box(bm_wall, 14.50, 15.90, 0.00, 0.35, 2.65, 3.20)
    add_box(bm_wall, 15.90, 16.00, 0.00, 0.35, 0.00, 3.20)
    add_box(bm_dark, 11.30, 12.60, 0.08, 0.12, 0.00, 2.75)
    add_box(bm_shutter, 11.35, 12.55, 0.10, 0.12, 0.10, 2.70)
    add_box(bm_dark, 11.25, 12.65, 0.30, 0.35, 0.00, 2.80)
    # Toldo Arena 1 (X: 12.70 a 14.35 m, saliente 1.15 m)
    add_box(bm_toldo_arena, 12.70, 14.35, -1.15, 0.05, 2.75, 3.25)
    add_box(bm_toldo_arena, 12.70, 14.35, -1.20, -1.15, 2.50, 2.75)
    add_box(bm_dark, 12.75, 14.30, 0.08, 0.12, 0.00, 2.65)
    add_box(bm_glass, 12.80, 14.25, 0.09, 0.11, 0.10, 2.55)
    add_box(bm_dark, 12.70, 14.35, 0.30, 0.35, 0.00, 2.70)
    # Toldo Arena 2 (X: 14.45 a 15.95 m, saliente 1.15 m)
    add_box(bm_toldo_arena, 14.45, 15.95, -1.15, 0.05, 2.75, 3.25)
    add_box(bm_toldo_arena, 14.45, 15.95, -1.20, -1.15, 2.50, 2.75)
    add_box(bm_dark, 14.50, 15.90, 0.08, 0.12, 0.00, 2.65)
    add_box(bm_glass, 14.55, 15.85, 0.09, 0.11, 0.10, 2.55)
    add_box(bm_dark, 14.45, 15.95, 0.30, 0.35, 0.00, 2.70)

    # -----------------------------------------------------------------------
    # Módulo 4 (Zaguán y Taquería Los Gallos, X: 16.00 a 24.80 m)
    # -----------------------------------------------------------------------
    add_box(bm_wall, 16.00, 16.30, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 17.50, 17.80, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 18.30, 18.60, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 19.30, 19.80, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 21.20, 21.80, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 23.40, 24.80, 0.00, 0.35, 4.55, 6.25)
    # Rellenos de muros ciegos en PA sobre y bajo vanos
    add_box(bm_wall, 17.80, 18.30, 0.00, 0.35, 4.55, 5.00)
    add_box(bm_wall, 17.80, 18.30, 0.00, 0.35, 5.60, 6.25)
    add_box(bm_wall, 18.60, 19.30, 0.00, 0.35, 4.55, 4.60)
    add_box(bm_wall, 18.60, 19.30, 0.00, 0.35, 6.10, 6.25)
    # Ventanas PA:
    # 4a (X: 16.30 a 17.50 m)
    add_box(bm_white, 16.30, 17.50, 0.10, 0.16, 4.55, 6.25)
    add_box(bm_glass, 16.35, 17.45, 0.13, 0.15, 4.60, 6.20)
    add_box(bm_dark, 16.25, 17.55, 0.30, 0.35, 4.50, 6.30)
    # 4b (X: 17.80 a 18.30 m)
    add_box(bm_white, 17.80, 18.30, 0.10, 0.16, 5.00, 5.60)
    add_box(bm_glass, 17.85, 18.25, 0.13, 0.15, 5.05, 5.55)
    add_box(bm_dark, 17.75, 18.35, 0.30, 0.35, 4.95, 5.65)
    # 4c (X: 18.60 a 19.30 m)
    add_box(bm_white, 18.60, 19.30, 0.10, 0.16, 4.60, 6.10)
    add_box(bm_glass, 18.65, 19.25, 0.13, 0.15, 4.65, 6.05)
    add_box(bm_dark, 18.55, 19.35, 0.30, 0.35, 4.55, 6.15)
    # 4d (X: 19.80 a 21.20 m)
    add_box(bm_white, 19.80, 21.20, 0.10, 0.16, 4.55, 6.25)
    add_box(bm_glass, 19.85, 21.15, 0.13, 0.15, 4.60, 6.20)
    add_box(bm_dark, 19.75, 21.25, 0.30, 0.35, 4.50, 6.30)
    # 4e (X: 21.80 a 23.40 m)
    add_box(bm_white, 21.80, 23.40, 0.10, 0.16, 4.55, 6.25)
    add_box(bm_glass, 21.85, 23.35, 0.13, 0.15, 4.60, 6.20)
    add_box(bm_dark, 21.75, 23.45, 0.30, 0.35, 4.50, 6.30)

    # Franja superior corrida de pavés sobre el zaguán (Z: 3.20 a 3.80 m)
    add_box(bm_paves, 20.05, 24.75, 0.05, 0.30, 3.25, 3.75)
    add_box(bm_dark, 20.00, 24.80, 0.02, 0.33, 3.20, 3.25)
    add_box(bm_dark, 20.00, 24.80, 0.02, 0.33, 3.75, 3.80)
    add_box(bm_dark, 20.00, 24.80, 0.30, 0.35, 3.20, 3.80) # Respaldo interior oscuro pavés
    # Antepecho macizo de estuco sobre pavés y bajo ventanas 4d/4e (Z: 3.80 a 4.55 m)
    add_box(bm_wall, 20.00, 24.80, 0.00, 0.35, 3.80, 4.55)
    # Frontón ornamental escalonado central sobre zaguán
    add_box(bm_wall, 21.80, 23.00, -0.06, 0.41, 7.25, 7.60)
    add_box(bm_wall, 22.10, 22.70, -0.08, 0.43, 7.60, 7.80)

    # PB Módulo 4: Muro macizo antes de zaguán
    add_box(bm_wall, 16.00, 20.00, 0.00, 0.35, 0.00, 3.20)

    # PB Zaguán Túnel Transitable:
    add_box(bm_wall, 19.70, 20.00, 0.35, 10.00, 0.00, 3.50) # Muro norte
    add_box(bm_wall, 24.80, 25.10, 0.35, 10.00, 0.00, 3.50) # Muro sur
    add_box(bm_wall, 20.00, 24.80, 0.35, 10.00, 3.20, 3.50) # Techo
    add_box(bm_interior, 20.00, 24.80, 0.00, 10.00, 0.00, 0.05) # Piso interior
    # Mostrador de Taquería y Toldo Rojo Coca-Cola Taquería Los Gallos
    add_box(bm_white, 20.20, 23.20, 0.35, 1.60, 0.00, 1.05) # Mostrador
    add_box(bm_toldo_rojo, 20.00, 24.60, -1.20, 0.30, 2.30, 2.85) # Carpa inclinada
    add_box(bm_toldo_rojo, 20.00, 24.60, -1.25, -1.20, 2.05, 2.30) # Faldón

    # -----------------------------------------------------------------------
    # Módulo 5 (Sur / Internet World, X: 24.80 a 28.60 m)
    # -----------------------------------------------------------------------
    add_box(bm_wall, 24.80, 25.60, 0.00, 0.35, 4.55, 6.25)
    add_box(bm_wall, 27.80, 28.60, 0.00, 0.35, 4.55, 6.25)
    # Ventana triple blanca grande en PA (X: 25.60 a 27.80 m)
    add_box(bm_white, 25.60, 27.80, 0.10, 0.16, 4.55, 6.25)
    add_box(bm_white, 26.30, 26.40, 0.12, 0.18, 4.60, 6.20)
    add_box(bm_white, 27.00, 27.10, 0.12, 0.18, 4.60, 6.20)
    add_box(bm_glass, 25.65, 27.75, 0.13, 0.15, 4.60, 6.20)
    add_box(bm_dark, 25.55, 27.85, 0.30, 0.35, 4.50, 6.30)
    # PB Módulo 5: Muros macizos, cancel comercial y Toldo Verde Oscuro / Azul Marino
    add_box(bm_wall, 24.80, 25.20, 0.00, 0.35, 0.00, 3.20)
    add_box(bm_wall, 25.20, 28.20, 0.00, 0.35, 2.80, 3.20)
    add_box(bm_wall, 28.20, 28.60, 0.00, 0.35, 0.00, 3.20)
    add_box(bm_dark, 25.20, 28.20, 0.08, 0.12, 0.00, 2.80)
    add_box(bm_glass, 25.25, 28.15, 0.09, 0.11, 0.10, 2.70)
    add_box(bm_dark, 25.15, 28.25, 0.30, 0.35, 0.00, 2.80)
    add_box(bm_toldo_azul, 25.00, 28.40, -1.20, 0.05, 2.75, 3.25)
    add_box(bm_toldo_azul, 25.00, 28.40, -1.25, -1.20, 2.50, 2.75)

    # Objetos en escena
    obj_wall = create_mesh_object("Fachada_Oeste_Muro", bm_wall, mats["estuco"], col)
    obj_dark = create_mesh_object("Fachada_Oeste_AlumOscuro", bm_dark, mats["alum_oscuro"], col)
    obj_glass = create_mesh_object("Fachada_Oeste_Vidrio", bm_glass, mats["vidrio"], col)
    obj_white = create_mesh_object("Fachada_Oeste_AlumBlanco", bm_white, mats["alum_blanco"], col)
    obj_shutter = create_mesh_object("Fachada_Oeste_Cortinas", bm_shutter, mats["cortina_metalica"], col)
    obj_paves = create_mesh_object("Fachada_Oeste_Paves", bm_paves, mats["paves"], col)
    obj_toldo_a = create_mesh_object("Fachada_Oeste_ToldoArena", bm_toldo_arena, mats["toldo_arena"], col)
    obj_toldo_r = create_mesh_object("Fachada_Oeste_ToldoRojo", bm_toldo_rojo, mats["toldo_rojo"], col)
    obj_toldo_az = create_mesh_object("Fachada_Oeste_ToldoAzul", bm_toldo_azul, mats["toldo_verde_oscuro"], col)
    obj_mini = create_mesh_object("Fachada_Oeste_Minisplit", bm_minisplit, mats["minisplit_chasis"], col)
    obj_int = create_mesh_object("Zaguan_PisoInterior", bm_interior, mats["piso_interior"], col)

    # Rótulos en Fachada Oeste
    t_net = create_3d_text("Texto_InternetWorld", "INTERNET WORLD", 0.28, 0.03, mats["panel_blanco"], col)
    t_net.location = Vector((26.70, -1.26, 2.95))
    t_net.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    t_rep = create_3d_text("Texto_Reparacion", "VENTA Y REPARACION DE COMPUTADORAS", 0.13, 0.02, mats["panel_blanco"], col)
    t_rep.location = Vector((26.70, -1.26, 2.62))
    t_rep.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    # Rótulo Taquería Los Gallos sobre toldo rojo
    t_taq = create_3d_text("Texto_Taqueria", "TAQUERIA LOS GALLOS", 0.18, 0.02, mats["panel_blanco"], col)
    t_taq.location = Vector((22.30, -1.26, 2.18))
    t_taq.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    return [obj_wall, obj_dark, obj_glass, obj_white, obj_shutter, obj_paves, obj_toldo_a, obj_toldo_r, obj_toldo_az, obj_mini, obj_int, t_net, t_rep, t_taq]

def build_courtyard_rear_and_roof(mats, col):
    """Construye las medianeras posteriores, el patio interior y la azotea hermética."""
    bm_wall = bmesh.new()
    bm_roof = bmesh.new()
    bm_corridor = bmesh.new()
    bm_iron = bmesh.new()

    # 1. Muro Medianero Sur (Colindancia con Dulcería El Molino en X = 28.60 m)
    add_box(bm_wall, 28.25, 28.60, 0.00, 20.40, 0.00, 7.30)
    # 2. Muro Medianero Oriente (Colindancia con vecinos en Y = 20.40 m)
    add_box(bm_wall, 0.00, 28.60, 20.05, 20.40, 0.00, 7.30)

    # 3. Alas Interiores y Patio Central (X: 8.00 a 20.00 m, Y: 6.00 a 14.00 m)
    add_box(bm_wall, 7.70, 8.00, 6.00, 20.05, 0.00, 7.10)  # Ala Norte
    add_box(bm_wall, 8.00, 19.70, 5.70, 6.00, 0.00, 7.10)  # Ala Oeste PB y PA
    add_box(bm_wall, 19.70, 24.80, 5.70, 6.00, 3.20, 7.10) # Ala Oeste PA (sobre el túnel del zaguán)
    add_box(bm_wall, 24.80, 25.10, 6.00, 20.05, 0.00, 7.10) # Ala Sur
    add_box(bm_wall, 8.00, 24.80, 14.00, 14.30, 0.00, 7.10) # Ala Oriente

    # Pasillo exterior techado en PA
    add_box(bm_corridor, 8.00, 19.70, 6.00, 7.20, 3.45, 3.55)
    add_box(bm_iron, 8.00, 19.70, 7.15, 7.20, 3.55, 4.55)

    # 3b. Entrepisos Horizontales Opacos (Aislamiento vertical hermético entre PB y PA)
    # Ala Oeste (Cárdenas): X: 2.80 a 28.60, Y: 0.00 a 6.00, Z: 3.20 a 3.45 m
    add_box(bm_roof, 2.80, 28.60, 0.00, 6.00, 3.20, 3.45)
    # Ala Norte (Libertad): X: 0.00 a 8.00, Y: 2.80 a 20.40, Z: 3.20 a 3.45 m
    add_box(bm_roof, 0.00, 8.00, 2.80, 20.40, 3.20, 3.45)
    # Esquina Ochavada
    center_xy = (1.40, 1.40)
    tangent_xy = (-0.7071, 0.7071)
    normal_xy = (-0.7071, -0.7071)
    add_oriented_box(bm_roof, center_xy, tangent_xy, normal_xy, -1.98, 1.98, -2.80, 0.35, 3.20, 3.45)

    # 4. Sellado Hermético Total de Azotea (Losa Impermeabilizada en Z = 6.95 m)
    add_box(bm_roof, 2.80, 28.60, 0.35, 6.00, 6.90, 7.00)
    add_box(bm_roof, 0.35, 8.00, 2.80, 20.40, 6.90, 7.00)
    add_box(bm_roof, 24.80, 28.60, 6.00, 20.40, 6.90, 7.00)
    add_box(bm_roof, 8.00, 24.80, 14.00, 20.40, 6.90, 7.00)
    # Sellado de la esquina ochavada hacia el interior
    add_oriented_box(bm_roof, center_xy, tangent_xy, normal_xy, -1.98, 1.98, -2.80, -0.35, 6.90, 7.00)

    obj_wall_rear = create_mesh_object("Interior_Muros_Patio", bm_wall, mats["estuco"], col)
    obj_roof = create_mesh_object("Azotea_Losa_Hermetica", bm_roof, mats["azotea"], col)
    obj_corridor = create_mesh_object("Pasillo_PlantaAlta", bm_corridor, mats["piso_interior"], col)
    obj_iron_corridor = create_mesh_object("Pasillo_Barandal", bm_iron, mats["hierro_forjado"], col)

    return [obj_wall_rear, obj_roof, obj_corridor, obj_iron_corridor]

# ---------------------------------------------------------------------------
# 4. Iluminación y Batería de Validación (6 Cámaras Canónicas)
# ---------------------------------------------------------------------------

def setup_lighting_and_render(col):
    """Configura sol solar Cycles CPU y 6 cámaras canónicas de inspección técnica."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True

    # Sol frontal natural de media tarde de Tecate
    sun_data = bpy.data.lights.new(name="Sun_Light", type='SUN')
    sun_data.energy = 4.2
    sun_data.angle = math.radians(1.5)
    sun_obj = bpy.data.objects.new("Sun_Light", sun_data)
    sun_obj.rotation_euler = (math.radians(52.0), math.radians(24.0), math.radians(-42.0))
    col.objects.link(sun_obj)

    # Cielo ambiental suave
    world = bpy.data.worlds.new("World_Tecate")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.76, 0.85, 0.96, 1.0)
        bg.inputs["Strength"].default_value = 1.15

    # 6 Cámaras Canónicas con Encuadre Fidedigno
    cameras_def = [
        ("ochava_45", (-10.5, -10.5, 5.0), (1.4, 1.4, 4.8), 48.0),
        ("subway_north", (-19.5, 11.6, 4.4), (0.0, 11.6, 4.0), 62.0),
        ("cardenas_west", (15.7, -25.0, 4.6), (15.7, 0.0, 4.0), 64.0),
        ("zaguan_closeup", (22.4, -7.5, 2.5), (22.4, 1.0, 2.3), 44.0),
        ("dulceria_border", (34.0, -9.0, 4.8), (28.0, 1.5, 3.8), 48.0),
        ("aerial_top", (14.0, 10.0, 46.0), (14.0, 10.0, 0.0), 55.0)
    ]

    cams = {}
    for cam_name, pos, look_at, fov_deg in cameras_def:
        c_data = bpy.data.cameras.new(cam_name + "_Data")
        c_data.lens_unit = 'FOV'
        c_data.angle = math.radians(fov_deg)
        c_obj = bpy.data.objects.new(cam_name + "_Cam", c_data)
        c_obj.location = Vector(pos)
        direction = Vector(look_at) - Vector(pos)
        rot_quat = direction.to_track_quat('-Z', 'Y')
        c_obj.rotation_euler = rot_quat.to_euler()
        col.objects.link(c_obj)
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
    print(" GENERADOR PROCEDURAL 3D: HOTEL TECATE (V4.0 GROUND-TRUTH)      ")
    print("================================================================")

    root_col = clean_scene()
    mats = create_materials()

    # 1. Zócalo basal continuo subterráneo (-1.20 m)
    obj_zocalo = build_zocalo_basal(mats, root_col)

    # 2. Fachada Oeste (Calle Presidente Lázaro Cárdenas)
    objs_west = build_west_facade_cardenas(mats, root_col)

    # 3. Fachada Norte (Callejón Libertad)
    objs_north = build_north_facade_libertad(mats, root_col)

    # 4. Ochava a 45º (Torreón semicircular, pavés, balcón y marquesina)
    objs_ochava = build_ochava_corner(mats, root_col)

    # 5. Patio interior, cuerpos traseros y azotea hermética
    objs_rear = build_courtyard_rear_and_roof(mats, root_col)

    # 6. Iluminación y batería de 6 cámaras canónicas de validación
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

    # 10. Batería de renders técnicos de validación Cycles CPU
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
    print(" GENERACIÓN PROCEDURAL HOTEL TECATE V4.0 CONCLUIDA EXITOSAMENTE ")
    print("================================================================")

if __name__ == "__main__":
    main()
