"""
=============================================================================
Generador 3D Paramétrico V4.1: Banco BBVA Tecate Centro (Ground-Truth Perfeccionado)
=============================================================================
Reconstrucción fidedigna con consenso multi-perspectiva y validación aérea:
- Esquina Ochavada a 45º LIMPIA: Torreón 'EDIFICIO LIC. JOSE F. GUAJARDO 1954'
  con mosaico veneciano añil, rótulo en bronce, acceso principal en planta baja
  y anuncio espectacular 'BBVA Bancomer / CAJERO AUTOMATICO' en azotea.
- Fachada Sur (Avenida Benito Juárez): 4 crujías modulares, cancelerías Tintex,
  fascia azul Alucobond (#16215B), mansarda de tejas de barro y cornisa moldurada.
- Fachada Oeste (Calle Presidente Lázaro Cárdenas): crujías comerciales con
  ménsulas/canecillos de concreto en voladizo (corbels), cajero exterior y tejas.
- Fachada Este (Callejón / Estacionamiento): Murete de confinamiento de rampa,
  barandilla de acero blanco, caseta de vigilancia y letrero oficial 'ENTRADA BBVA ->'.

Ejecución headless:
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/generate_bbva_tecate.py
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Euler

def clean_scene():
    """Limpia todos los objetos y colecciones de la escena."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)
    root_col = bpy.data.collections.new("BBVA_Tecate_Root")
    bpy.context.scene.collection.children.link(root_col)
    return root_col

def create_materials():
    """Crea la paleta PBR arquitectónica completa."""
    mats = {}
    
    # 1. Torreón Guajardo: Mosaico Vítreo Añil / Purpúreo (#2A2F48)
    mat_mosaico = bpy.data.materials.new(name="M_Guajardo_Mosaico")
    mat_mosaico.use_nodes = True
    nodes_m = mat_mosaico.node_tree.nodes
    links_m = mat_mosaico.node_tree.links
    bsdf_m = nodes_m.get("Principled BSDF")
    if bsdf_m:
        bsdf_m.inputs["Base Color"].default_value = (0.024, 0.032, 0.085, 1.0)
        bsdf_m.inputs["Metallic"].default_value = 0.05
        bsdf_m.inputs["Roughness"].default_value = 0.32
        tex_vor = nodes_m.new('ShaderNodeTexVoronoi')
        tex_vor.inputs['Scale'].default_value = 160.0
        bump_node = nodes_m.new('ShaderNodeBump')
        bump_node.inputs['Strength'].default_value = 0.35
        links_m.new(tex_vor.outputs['Distance'], bump_node.inputs['Height'])
        links_m.new(bump_node.outputs['Normal'], bsdf_m.inputs['Normal'])
    mats["mosaico_guajardo"] = mat_mosaico

    # 2. Rótulo de Bronce / Latón Dorado Guajardo (#D4AF37)
    mat_bronce = bpy.data.materials.new(name="M_Guajardo_Bronce")
    mat_bronce.use_nodes = True
    bsdf_b = mat_bronce.node_tree.nodes.get("Principled BSDF")
    if bsdf_b:
        bsdf_b.inputs["Base Color"].default_value = (0.68, 0.50, 0.16, 1.0)
        bsdf_b.inputs["Metallic"].default_value = 0.90
        bsdf_b.inputs["Roughness"].default_value = 0.25
    mats["bronce"] = mat_bronce

    # 3. Fascia y Espectacular: Azul Marino Corporativo BBVA (#16215B)
    mat_fascia = bpy.data.materials.new(name="M_BBVA_Fascia_Azul")
    mat_fascia.use_nodes = True
    bsdf_f = mat_fascia.node_tree.nodes.get("Principled BSDF")
    if bsdf_f:
        bsdf_f.inputs["Base Color"].default_value = (0.010, 0.018, 0.110, 1.0)
        bsdf_f.inputs["Metallic"].default_value = 0.15
        bsdf_f.inputs["Roughness"].default_value = 0.25
    mats["fascia"] = mat_fascia

    # 4. Muro Estuco Blanco Cálido (#F2EFEA)
    mat_muro = bpy.data.materials.new(name="M_BBVA_Muro_Blanco")
    mat_muro.use_nodes = True
    bsdf_w = mat_muro.node_tree.nodes.get("Principled BSDF")
    if bsdf_w:
        bsdf_w.inputs["Base Color"].default_value = (0.88, 0.86, 0.82, 1.0)
        bsdf_w.inputs["Metallic"].default_value = 0.0
        bsdf_w.inputs["Roughness"].default_value = 0.80
    mats["muro"] = mat_muro

    # 5. Vidrio Tintex Oscuro Reflectivo (#0B1520)
    mat_vidrio = bpy.data.materials.new(name="M_BBVA_Vidrio")
    mat_vidrio.use_nodes = True
    bsdf_v = mat_vidrio.node_tree.nodes.get("Principled BSDF")
    if bsdf_v:
        bsdf_v.inputs["Base Color"].default_value = (0.010, 0.024, 0.040, 1.0)
        bsdf_v.inputs["Metallic"].default_value = 0.35
        bsdf_v.inputs["Roughness"].default_value = 0.05
        if "Transmission Weight" in bsdf_v.inputs:
            bsdf_v.inputs["Transmission Weight"].default_value = 0.25
        elif "Transmission" in bsdf_v.inputs:
            bsdf_v.inputs["Transmission"].default_value = 0.25
    mats["vidrio"] = mat_vidrio

    # 6. Cancelería de Aluminio Natural (#A4A8AD)
    mat_alum = bpy.data.materials.new(name="M_BBVA_Canceleria")
    mat_alum.use_nodes = True
    bsdf_a = mat_alum.node_tree.nodes.get("Principled BSDF")
    if bsdf_a:
        bsdf_a.inputs["Base Color"].default_value = (0.42, 0.44, 0.47, 1.0)
        bsdf_a.inputs["Metallic"].default_value = 0.85
        bsdf_a.inputs["Roughness"].default_value = 0.35
    mats["aluminio"] = mat_alum

    # 7. Zócalo Concreto Gris Grafito (#36383B)
    mat_zocalo = bpy.data.materials.new(name="M_BBVA_Zocalo")
    mat_zocalo.use_nodes = True
    bsdf_z = mat_zocalo.node_tree.nodes.get("Principled BSDF")
    if bsdf_z:
        bsdf_z.inputs["Base Color"].default_value = (0.09, 0.10, 0.11, 1.0)
        bsdf_z.inputs["Metallic"].default_value = 0.0
        bsdf_z.inputs["Roughness"].default_value = 0.88
    mats["zocalo"] = mat_zocalo

    # 8. Tejas Coloniales de Barro Terracota (#8C341E)
    mat_teja = bpy.data.materials.new(name="M_BBVA_Teja")
    mat_teja.use_nodes = True
    nodes_t = mat_teja.node_tree.nodes
    links_t = mat_teja.node_tree.links
    bsdf_t = nodes_t.get("Principled BSDF")
    if bsdf_t:
        bsdf_t.inputs["Base Color"].default_value = (0.28, 0.055, 0.022, 1.0)
        bsdf_t.inputs["Metallic"].default_value = 0.0
        bsdf_t.inputs["Roughness"].default_value = 0.78
        norm_path = "godot_project/assets/textures/kiosko_teja_normal.png"
        if os.path.exists(norm_path):
            img_norm = bpy.data.images.load(os.path.abspath(norm_path))
            img_norm.colorspace_settings.name = 'Non-Color'
            node_norm_tex = nodes_t.new('ShaderNodeTexImage')
            node_norm_tex.image = img_norm
            node_norm_map = nodes_t.new('ShaderNodeNormalMap')
            node_norm_map.inputs['Strength'].default_value = 1.3
            links_t.new(node_norm_tex.outputs['Color'], node_norm_map.inputs['Color'])
            links_t.new(node_norm_map.outputs['Normal'], bsdf_t.inputs['Normal'])
    mats["teja"] = mat_teja

    # 9. Rótulos y Gráfica Blanca (#FFFFFF)
    mat_blanco = bpy.data.materials.new(name="M_BBVA_Rotulo_Blanco")
    mat_blanco.use_nodes = True
    bsdf_w2 = mat_blanco.node_tree.nodes.get("Principled BSDF")
    if bsdf_w2:
        bsdf_w2.inputs["Base Color"].default_value = (0.95, 0.95, 0.95, 1.0)
        bsdf_w2.inputs["Metallic"].default_value = 0.05
        bsdf_w2.inputs["Roughness"].default_value = 0.20
    mats["rotulo_blanco"] = mat_blanco

    # 10. Persianas Verticales (#DCD9D0)
    mat_persianas = bpy.data.materials.new(name="M_BBVA_Persianas")
    mat_persianas.use_nodes = True
    bsdf_p = mat_persianas.node_tree.nodes.get("Principled BSDF")
    if bsdf_p:
        bsdf_p.inputs["Base Color"].default_value = (0.70, 0.68, 0.63, 1.0)
        bsdf_p.inputs["Roughness"].default_value = 0.90
    mats["persianas"] = mat_persianas

    # 11. Señalización Azul Entrada (#004481)
    mat_senal = bpy.data.materials.new(name="M_BBVA_Senal_Azul")
    mat_senal.use_nodes = True
    bsdf_s = mat_senal.node_tree.nodes.get("Principled BSDF")
    if bsdf_s:
        bsdf_s.inputs["Base Color"].default_value = (0.005, 0.058, 0.22, 1.0)
        bsdf_s.inputs["Roughness"].default_value = 0.30
    mats["senal_azul"] = mat_senal

    # 12. Logotipo Verde Cajero Automático (#008F4C)
    mat_verde = bpy.data.materials.new(name="M_BBVA_Cajero_Verde")
    mat_verde.use_nodes = True
    bsdf_g = mat_verde.node_tree.nodes.get("Principled BSDF")
    if bsdf_g:
        bsdf_g.inputs["Base Color"].default_value = (0.005, 0.28, 0.075, 1.0)
        bsdf_g.inputs["Roughness"].default_value = 0.30
    mats["cajero_verde"] = mat_verde

    # 13. Barandilla Metálica Blanca (#EAEAEA)
    mat_barandal = bpy.data.materials.new(name="M_BBVA_Barandal_Blanco")
    mat_barandal.use_nodes = True
    bsdf_bar = mat_barandal.node_tree.nodes.get("Principled BSDF")
    if bsdf_bar:
        bsdf_bar.inputs["Base Color"].default_value = (0.82, 0.82, 0.82, 1.0)
        bsdf_bar.inputs["Metallic"].default_value = 0.65
        bsdf_bar.inputs["Roughness"].default_value = 0.35
    mats["barandal"] = mat_barandal

    # 14. Cordón Rojo Banqueta (#B22222)
    mat_cordon = bpy.data.materials.new(name="M_BBVA_Cordon_Rojo")
    mat_cordon.use_nodes = True
    bsdf_c = mat_cordon.node_tree.nodes.get("Principled BSDF")
    if bsdf_c:
        bsdf_c.inputs["Base Color"].default_value = (0.45, 0.04, 0.04, 1.0)
        bsdf_c.inputs["Roughness"].default_value = 0.85
    mats["cordon_rojo"] = mat_cordon

    # 15. Azotea / Membrana Asfáltica (#252525)
    mat_azotea = bpy.data.materials.new(name="M_BBVA_Azotea")
    mat_azotea.use_nodes = True
    bsdf_az = mat_azotea.node_tree.nodes.get("Principled BSDF")
    if bsdf_az:
        bsdf_az.inputs["Base Color"].default_value = (0.06, 0.06, 0.06, 1.0)
        bsdf_az.inputs["Roughness"].default_value = 0.95
    mats["azotea"] = mat_azotea

    # 16. Acero Estructural (#2B2C2E)
    mat_acero = bpy.data.materials.new(name="M_BBVA_Acero_Estructural")
    mat_acero.use_nodes = True
    bsdf_st = mat_acero.node_tree.nodes.get("Principled BSDF")
    if bsdf_st:
        bsdf_st.inputs["Base Color"].default_value = (0.08, 0.085, 0.09, 1.0)
        bsdf_st.inputs["Metallic"].default_value = 0.70
        bsdf_st.inputs["Roughness"].default_value = 0.45
    mats["acero"] = mat_acero

    return mats

def add_box(bm, x_min, x_max, y_min, y_max, z_min, z_max):
    """Crea una caja prismática axial limpia con normales exteriores."""
    v1 = bm.verts.new((x_min, y_min, z_min))
    v2 = bm.verts.new((x_max, y_min, z_min))
    v3 = bm.verts.new((x_max, y_max, z_min))
    v4 = bm.verts.new((x_min, y_max, z_min))
    v5 = bm.verts.new((x_min, y_min, z_max))
    v6 = bm.verts.new((x_max, y_min, z_max))
    v7 = bm.verts.new((x_max, y_max, z_max))
    v8 = bm.verts.new((x_min, y_max, z_max))
    faces = [
        bm.faces.new((v4, v3, v2, v1)), # Bottom
        bm.faces.new((v5, v6, v7, v8)), # Top
        bm.faces.new((v1, v2, v6, v5)), # Front
        bm.faces.new((v2, v3, v7, v6)), # Right
        bm.faces.new((v3, v4, v8, v7)), # Back
        bm.faces.new((v4, v1, v5, v8)), # Left
    ]
    return faces

def add_wall_segment(bm, x1, y1, x2, y2, z_min, z_max, thickness=0.40):
    """Crea un segmento de muro orientado de (x1,y1) a (x2,y2) con espesor hacia el interior (+X,+Y)."""
    dx = x2 - x1
    dy = y2 - y1
    L = math.hypot(dx, dy)
    if L < 1e-6:
        return []
    # Vector normal perpendicular hacia el interior del edificio:
    nx = -dy / L * thickness
    ny = dx / L * thickness
    
    v1 = bm.verts.new((x1, y1, z_min))
    v2 = bm.verts.new((x2, y2, z_min))
    v3 = bm.verts.new((x2 + nx, y2 + ny, z_min))
    v4 = bm.verts.new((x1 + nx, y1 + ny, z_min))
    v5 = bm.verts.new((x1, y1, z_max))
    v6 = bm.verts.new((x2, y2, z_max))
    v7 = bm.verts.new((x2 + nx, y2 + ny, z_max))
    v8 = bm.verts.new((x1 + nx, y1 + ny, z_max))
    
    faces = [
        bm.faces.new((v4, v3, v2, v1)),
        bm.faces.new((v5, v6, v7, v8)),
        bm.faces.new((v1, v2, v6, v5)), # Cara exterior visible
        bm.faces.new((v2, v3, v7, v6)),
        bm.faces.new((v3, v4, v8, v7)),
        bm.faces.new((v4, v1, v5, v8)),
    ]
    return faces

def build_45deg_guajardo_corner(mats, col):
    """Construye el chaflán a 45º LIMPIO con el Torreón Guajardo, rótulos en bronce y espectacular en azotea."""
    # Torreón prismático de 5 lados que resuelve la esquina ochavada y recibe limpiamente las cornisas:
    # P1: (-0.40, 4.20)  [esquina frontal oeste]
    # P2: (4.20, -0.40)  [esquina frontal sur]
    # P4: (4.20, 0.40)   [retorno este interior]
    # P5: (4.20, 4.20)   [esquina posterior interior]
    # P3: (0.40, 4.20)   [retorno norte interior]
    
    bm_tower = bmesh.new()
    bm_glass = bmesh.new()
    H_tower = 9.00
    
    # 1. Muro principal del chaflán a 45º (P1 a P2)
    # Planta baja: Z = 0.0 a 3.20; Planta alta (mosaico): Z = 3.20 a H_tower
    p1 = (-0.40, 4.20)
    p2 = (4.20, -0.40)
    
    # Retornos laterales donde rematan las fachadas Juárez y Cárdenas
    # Retorno Norte (Y = 4.20, X de -0.40 a 0.40)
    add_box(bm_tower, -0.40, 0.40, 4.15, 4.25, 0.0, H_tower)
    # Retorno Este (X = 4.20, Y de -0.40 a 0.40)
    add_box(bm_tower, 4.15, 4.25, -0.40, 0.40, 0.0, H_tower)
    
    # Muros interiores para sellar el prisma
    add_box(bm_tower, 0.40, 4.20, 4.15, 4.25, 0.0, H_tower)
    add_box(bm_tower, 4.15, 4.25, 0.40, 4.20, 0.0, H_tower)
    
    # Losa de azotea del torreón (5 lados)
    v_top = [
        bm_tower.verts.new((-0.40, 4.20, H_tower)),
        bm_tower.verts.new((4.20, -0.40, H_tower)),
        bm_tower.verts.new((4.20, 0.40, H_tower)),
        bm_tower.verts.new((4.20, 4.20, H_tower)),
        bm_tower.verts.new((0.40, 4.20, H_tower))
    ]
    bm_tower.faces.new(v_top)
    
    # Cornisa de remate superior sobre el chaflán (Z = H_tower a H_tower + 0.18)
    add_wall_segment(bm_tower, -0.45, 4.25, 4.25, -0.45, H_tower, H_tower + 0.18, thickness=0.60)
    
    # Muro superior de mosaico vítreo añil (Z = 3.20 a H_tower)
    add_wall_segment(bm_tower, -0.40, 4.20, 4.20, -0.40, 3.20, H_tower, thickness=0.45)
    
    # Viga dintel horizontal de concreto blanco (Z = 2.90 a 3.20)
    add_wall_segment(bm_tower, -0.42, 4.22, 4.22, -0.42, 2.90, 3.20, thickness=0.50)
    
    # Planta baja del chaflán: Acceso principal con cancelería de aluminio y vidrio
    # Centro en (1.90, 1.90). Ancho del vano de acceso = 2.40 m
    # Tangente unitaria: (0.7071, -0.7071). Puerta va de t = -1.20 a +1.20
    # Puerta izquierda: (1.90 - 1.20*0.7071, 1.90 + 1.20*0.7071) = (1.051, 2.749)
    # Puerta derecha:   (1.90 + 1.20*0.7071, 1.90 - 1.20*0.7071) = (2.749, 1.051)
    
    # Muros/pilastras laterales de planta baja (con zócalo)
    add_wall_segment(bm_tower, -0.40, 4.20, 1.05, 2.75, 0.0, 2.90, thickness=0.45)
    add_wall_segment(bm_tower, 2.75, 1.05, 4.20, -0.40, 0.0, 2.90, thickness=0.45)
    
    # Cancelería de aluminio del acceso (Z = 0.0 a 2.90)
    # Marco superior e inferior
    add_wall_segment(bm_tower, 1.05, 2.75, 2.75, 1.05, 0.0, 0.08, thickness=0.12)
    add_wall_segment(bm_tower, 1.05, 2.75, 2.75, 1.05, 2.82, 2.90, thickness=0.12)
    # Jambas laterales y poste central divisor de puertas dobles
    add_wall_segment(bm_tower, 1.05, 2.75, 1.12, 2.68, 0.0, 2.90, thickness=0.12)
    add_wall_segment(bm_tower, 2.68, 1.12, 2.75, 1.05, 0.0, 2.90, thickness=0.12)
    add_wall_segment(bm_tower, 1.86, 1.94, 1.94, 1.86, 0.0, 2.90, thickness=0.12)
    
    # Puertas dobles de vidrio templado
    add_wall_segment(bm_glass, 1.12, 2.68, 2.68, 1.12, 0.08, 2.82, thickness=0.02)
    
    # Asignación de materiales al torreón
    bmesh.ops.recalc_face_normals(bm_tower, faces=bm_tower.faces)
    m_tower = bpy.data.meshes.new("Mesh_Guajardo_Torreon")
    bm_tower.to_mesh(m_tower)
    bm_tower.free()
    obj_tower = bpy.data.objects.new("Guajardo_Torreon_45", m_tower)
    col.objects.link(obj_tower)
    obj_tower.data.materials.append(mats["mosaico_guajardo"]) # 0
    obj_tower.data.materials.append(mats["muro"])             # 1
    obj_tower.data.materials.append(mats["zocalo"])           # 2
    obj_tower.data.materials.append(mats["aluminio"])         # 3
    
    for p in m_tower.polygons:
        c_z = sum(m_tower.vertices[v].co.z for v in p.vertices) / len(p.vertices)
        c_x = sum(m_tower.vertices[v].co.x for v in p.vertices) / len(p.vertices)
        c_y = sum(m_tower.vertices[v].co.y for v in p.vertices) / len(p.vertices)
        if c_z < 0.42:
            p.material_index = 2 # Zócalo basal
        elif c_z >= H_tower:
            p.material_index = 1 # Cornisa superior blanca
        elif c_z >= 2.88 and c_z <= 3.22:
            p.material_index = 1 # Viga dintel blanca
        elif c_z < 2.90:
            p.material_index = 3 # Cancelería de aluminio
        elif c_x > 4.10 or c_y > 4.10:
            p.material_index = 1 # Retornos laterales estucados
        else:
            p.material_index = 0 # Mosaico vítreo añil
            
    bmesh.ops.recalc_face_normals(bm_glass, faces=bm_glass.faces)
    m_g = bpy.data.meshes.new("Mesh_Guajardo_Vidrio")
    bm_glass.to_mesh(m_g)
    bm_glass.free()
    obj_glass = bpy.data.objects.new("Guajardo_Vidrio_Acceso", m_g)
    col.objects.link(obj_glass)
    obj_glass.data.materials.append(mats["vidrio"])

    # 6. Rótulos Históricos de Bronce en el chaflán a 45º
    # Normal exterior hacia la calle: (-0.7071, -0.7071)
    # Centro en el chaflán: (1.90, 1.90)
    # Desplazamos 0.035 m hacia afuera en dirección normal:
    x_c = 1.90 - 0.035 * 0.7071
    y_c = 1.90 - 0.035 * 0.7071
    
    texts_guaj = []
    labels = [
        ("EDIFICIO", 0.28, 8.00),
        ("LIC. JOSE F. GUAJARDO", 0.35, 7.35),
        ("1954", 0.24, 6.75)
    ]
    for text_body, f_size, f_z in labels:
        f_curve = bpy.data.curves.new(type="FONT", name=f"Font_{text_body[:6]}")
        f_curve.body = text_body
        f_curve.size = f_size
        f_curve.extrude = 0.025
        f_curve.align_x = 'CENTER'
        o_txt = bpy.data.objects.new(f"Guajardo_Txt_{text_body[:6]}", f_curve)
        col.objects.link(o_txt)
        o_txt.location = (x_c, y_c, f_z)
        o_txt.rotation_euler = (math.radians(90.0), 0.0, math.radians(-45.0))
        o_txt.data.materials.append(mats["bronce"])
        texts_guaj.append(o_txt)

    # 7. Espectacular de Azotea a 45º sobre el Torreón
    bm_steel = bmesh.new()
    bm_blue = bmesh.new()
    bm_white = bmesh.new()
    
    # Postes de acero anclados sobre el pretil del torreón
    add_box(bm_steel, 1.10, 1.20, 1.10, 1.20, H_tower, 10.20)
    add_box(bm_steel, 2.55, 2.65, 2.55, 2.65, H_tower, 10.20)
    
    bmesh.ops.recalc_face_normals(bm_steel, faces=bm_steel.faces)
    m_st = bpy.data.meshes.new("Mesh_Totem_Acero")
    bm_steel.to_mesh(m_st)
    bm_steel.free()
    obj_steel = bpy.data.objects.new("BBVA_Totem_Postes", m_st)
    col.objects.link(obj_steel)
    obj_steel.data.materials.append(mats["acero"])
    
    # Caja de luz: panel superior azul BBVA
    add_box(bm_blue, -1.80, 1.80, -0.16, 0.16, 11.00, 12.65)
    bmesh.ops.recalc_face_normals(bm_blue, faces=bm_blue.faces)
    m_b = bpy.data.meshes.new("Mesh_Totem_Azul")
    bm_blue.to_mesh(m_b)
    bm_blue.free()
    obj_blue = bpy.data.objects.new("BBVA_Totem_Panel_Azul", m_b)
    col.objects.link(obj_blue)
    obj_blue.location = (1.90, 1.90, 0.0)
    obj_blue.rotation_euler = (0.0, 0.0, math.radians(-45.0))
    obj_blue.data.materials.append(mats["fascia"])

    # Panel inferior blanco Cajero Automático
    add_box(bm_white, -1.80, 1.80, -0.16, 0.16, 9.85, 11.00)
    bmesh.ops.recalc_face_normals(bm_white, faces=bm_white.faces)
    m_w = bpy.data.meshes.new("Mesh_Totem_Blanco")
    bm_white.to_mesh(m_w)
    bm_white.free()
    obj_white = bpy.data.objects.new("BBVA_Totem_Panel_Blanco", m_w)
    col.objects.link(obj_white)
    obj_white.location = (1.90, 1.90, 0.0)
    obj_white.rotation_euler = (0.0, 0.0, math.radians(-45.0))
    obj_white.data.materials.append(mats["rotulo_blanco"])

    # Textos del espectacular
    x_t = 1.90 - 0.18 * 0.7071
    y_t = 1.90 - 0.18 * 0.7071
    
    f_b1 = bpy.data.curves.new(type="FONT", name="Font_T_BBVA")
    f_b1.body = "BBVA"
    f_b1.size = 0.48
    f_b1.extrude = 0.02
    f_b1.align_x = 'CENTER'
    o_b1 = bpy.data.objects.new("Totem_Txt_BBVA", f_b1)
    col.objects.link(o_b1)
    o_b1.location = (x_t, y_t, 12.05)
    o_b1.rotation_euler = (math.radians(90.0), 0.0, math.radians(-45.0))
    o_b1.data.materials.append(mats["rotulo_blanco"])

    f_b2 = bpy.data.curves.new(type="FONT", name="Font_T_Bancomer")
    f_b2.body = "Bancomer"
    f_b2.size = 0.36
    f_b2.extrude = 0.02
    f_b2.align_x = 'CENTER'
    o_b2 = bpy.data.objects.new("Totem_Txt_Bancomer", f_b2)
    col.objects.link(o_b2)
    o_b2.location = (x_t, y_t, 11.25)
    o_b2.rotation_euler = (math.radians(90.0), 0.0, math.radians(-45.0))
    o_b2.data.materials.append(mats["rotulo_blanco"])

    f_b3 = bpy.data.curves.new(type="FONT", name="Font_T_ATM")
    f_b3.body = "CAJERO\nAUTOMATICO"
    f_b3.size = 0.20
    f_b3.extrude = 0.015
    f_b3.align_x = 'CENTER'
    o_b3 = bpy.data.objects.new("Totem_Txt_ATM", f_b3)
    col.objects.link(o_b3)
    o_b3.location = (x_t, y_t, 10.55)
    o_b3.rotation_euler = (math.radians(90.0), 0.0, math.radians(-45.0))
    o_b3.data.materials.append(mats["cajero_verde"])

    return obj_tower, obj_glass, [obj_steel, obj_blue, obj_white], texts_guaj, [o_b1, o_b2, o_b3]

def build_south_facade_juarez(mats, col):
    """Construye la Fachada Sur a lo largo de Av. Benito Juárez (Ground-Truth xB3bx-WBbz5e4GxAuGHGWw)."""
    bm_struct = bmesh.new()
    bm_alum = bmesh.new()
    bm_glass = bmesh.new()
    bm_blind = bmesh.new()
    
    X_start = 4.20
    X_end = 22.80
    H_wall = 7.10
    
    # 1. Plinto basal (Z = 0.0 a 0.40)
    add_box(bm_struct, X_start, X_end, -0.05, 0.40, 0.0, 0.40)
    
    # 2. Machones / Pilastras verticales frontales (5 pilastras en resalte hacia -Y)
    col_x = [4.20, 8.60, 13.00, 17.40, 22.20]
    for cx in col_x:
        add_box(bm_struct, cx, cx + 0.60, -0.04, 0.35, 0.40, H_wall)
        
    # Muros horizontales rehundidos (Y = 0.02 a 0.30)
    add_box(bm_struct, X_start, X_end, 0.02, 0.30, 3.20, 3.30)
    add_box(bm_struct, X_start, X_end, 0.02, 0.30, 4.30, 5.10)
    add_box(bm_struct, X_start, X_end, 0.02, 0.30, 6.75, H_wall)
    
    # Cornisa moldurada corrida blanca
    add_box(bm_struct, X_start, X_end + 0.20, -0.20, 0.40, 7.10, 7.25)
    add_box(bm_struct, X_start, X_end + 0.40, -0.40, 0.85, 7.25, 7.45)
    
    # 3. Cancelería de 4 crujías en Av. Juárez
    bays = [
        (4.80, 8.60),
        (9.20, 13.00),
        (13.60, 17.40),
        (18.00, 22.20)
    ]
    
    # Planta Baja (Z = 0.40 a 3.20)
    for x1, x2 in bays:
        w_f = 0.05
        add_box(bm_alum, x1, x1 + w_f, 0.04, 0.12, 0.40, 3.20)
        add_box(bm_alum, x2 - w_f, x2, 0.04, 0.12, 0.40, 3.20)
        add_box(bm_alum, x1, x2, 0.04, 0.12, 0.40, 0.40 + w_f)
        add_box(bm_alum, x1, x2, 0.04, 0.12, 3.20 - w_f, 3.20)
        step = (x2 - x1) / 3.0
        add_box(bm_alum, x1 + step - 0.025, x1 + step + 0.025, 0.04, 0.12, 0.40, 3.20)
        add_box(bm_alum, x1 + 2*step - 0.025, x1 + 2*step + 0.025, 0.04, 0.12, 0.40, 3.20)
        add_box(bm_glass, x1 + w_f, x2 - w_f, 0.075, 0.085, 0.40 + w_f, 3.20 - w_f)
        add_box(bm_blind, x1 + w_f, x2 - w_f, 0.135, 0.145, 0.42, 3.18)
        
    # Planta Alta (Z = 5.10 a 6.75)
    for x1, x2 in bays:
        w_f = 0.04
        add_box(bm_alum, x1, x1 + w_f, 0.04, 0.10, 5.10, 6.75)
        add_box(bm_alum, x2 - w_f, x2, 0.04, 0.10, 5.10, 6.75)
        add_box(bm_alum, x1, x2, 0.04, 0.10, 5.10, 5.10 + w_f)
        add_box(bm_alum, x1, x2, 0.04, 0.10, 6.75 - w_f, 6.75)
        step = (x2 - x1) / 3.0
        for i in range(1, 3):
            mx = x1 + i * step
            add_box(bm_alum, mx - 0.02, mx + 0.02, 0.04, 0.10, 5.10, 6.75)
        add_box(bm_glass, x1 + w_f, x2 - w_f, 0.065, 0.075, 5.10 + w_f, 6.75 - w_f)

    # Convertir a objetos
    bmesh.ops.recalc_face_normals(bm_struct, faces=bm_struct.faces)
    m_st = bpy.data.meshes.new("Mesh_Juarez_Estructura")
    bm_struct.to_mesh(m_st)
    bm_struct.free()
    obj_struct = bpy.data.objects.new("Juarez_Estructura", m_st)
    col.objects.link(obj_struct)
    obj_struct.data.materials.append(mats["muro"])
    obj_struct.data.materials.append(mats["zocalo"])
    for p in m_st.polygons:
        if sum(m_st.vertices[v].co.z for v in p.vertices) / len(p.vertices) < 0.42:
            p.material_index = 1
        else:
            p.material_index = 0

    bmesh.ops.recalc_face_normals(bm_alum, faces=bm_alum.faces)
    m_al = bpy.data.meshes.new("Mesh_Juarez_Canceleria")
    bm_alum.to_mesh(m_al)
    bm_alum.free()
    obj_alum = bpy.data.objects.new("Juarez_Canceleria", m_al)
    col.objects.link(obj_alum)
    obj_alum.data.materials.append(mats["aluminio"])

    bmesh.ops.recalc_face_normals(bm_glass, faces=bm_glass.faces)
    m_gl = bpy.data.meshes.new("Mesh_Juarez_Vidrio")
    bm_glass.to_mesh(m_gl)
    bm_glass.free()
    obj_glass = bpy.data.objects.new("Juarez_Vidrio", m_gl)
    col.objects.link(obj_glass)
    obj_glass.data.materials.append(mats["vidrio"])

    bmesh.ops.recalc_face_normals(bm_blind, faces=bm_blind.faces)
    m_bl = bpy.data.meshes.new("Mesh_Juarez_Persianas")
    bm_blind.to_mesh(m_bl)
    bm_blind.free()
    obj_blind = bpy.data.objects.new("Juarez_Persianas", m_bl)
    col.objects.link(obj_blind)
    obj_blind.data.materials.append(mats["persianas"])

    # 4. Fascia azul marino Alucobond (#16215B)
    bm_fascia = bmesh.new()
    add_box(bm_fascia, X_start, X_end, -0.14, 0.02, 3.20, 4.30)
    bmesh.ops.recalc_face_normals(bm_fascia, faces=bm_fascia.faces)
    m_fa = bpy.data.meshes.new("Mesh_Juarez_Fascia")
    bm_fascia.to_mesh(m_fa)
    bm_fascia.free()
    obj_fascia = bpy.data.objects.new("Juarez_Fascia_Azul", m_fa)
    col.objects.link(obj_fascia)
    obj_fascia.data.materials.append(mats["fascia"])

    # Filete blanco horizontal
    bm_stripe = bmesh.new()
    add_box(bm_stripe, X_start + 6.0, X_end - 0.20, -0.148, -0.138, 3.72, 3.76)
    bmesh.ops.recalc_face_normals(bm_stripe, faces=bm_stripe.faces)
    m_str = bpy.data.meshes.new("Mesh_Juarez_Stripe")
    bm_stripe.to_mesh(m_str)
    bm_stripe.free()
    obj_stripe = bpy.data.objects.new("Juarez_Fascia_Stripe", m_str)
    col.objects.link(obj_stripe)
    obj_stripe.data.materials.append(mats["rotulo_blanco"])

    # Texto "BBVA Bancomer" en fascia
    f_txt = bpy.data.curves.new(type="FONT", name="Font_Juarez_BBVA")
    f_txt.body = "BBVA Bancomer"
    f_txt.size = 0.50
    f_txt.extrude = 0.025
    o_txt = bpy.data.objects.new("Juarez_Texto_Fascia", f_txt)
    col.objects.link(o_txt)
    o_txt.location = (X_start + 0.80, -0.165, 3.50)
    o_txt.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    o_txt.data.materials.append(mats["rotulo_blanco"])

    # 5. Mansarda de Tejas Coloniales de Barro Terracota
    bm_tejas = bmesh.new()
    Z_start = 7.45
    Z_end = 8.15
    dy = 0.85 - (-0.42)
    dz = Z_end - Z_start
    L = math.hypot(dy, dz)
    ny = -dz / L
    nz = dy / L
    n_tejas_x = 42
    step_x = (X_end - X_start + 0.40) / float(n_tejas_x)
    r_teja = 0.065
    n_segs = 6
    
    for i in range(n_tejas_x):
        x_c = X_start + i * step_x + step_x * 0.5
        for j in range(3):
            t1 = j / 3.0
            t2 = (j + 1.0) / 3.0
            y_a = -0.42 + t1 * dy
            z_a = Z_start + t1 * dz
            y_b = -0.42 + t2 * dy
            z_b = Z_start + t2 * dz
            v_p_a, v_p_b = None, None
            for s in range(n_segs + 1):
                ang = math.pi * (s / float(n_segs))
                ox = r_teja * math.cos(ang)
                on = r_teja * math.sin(ang)
                va = bm_tejas.verts.new((x_c + ox, y_a + on * ny, z_a + on * nz))
                vb = bm_tejas.verts.new((x_c + ox, y_b + on * ny, z_b + on * nz))
                if s > 0:
                    bm_tejas.faces.new((v_p_a, va, vb, v_p_b))
                v_p_a, v_p_b = va, vb

    # Caballete de cumbrera
    r_ridge = 0.08
    v_r_a, v_r_b = None, None
    for s in range(n_segs + 1):
        ang = math.pi * (s / float(n_segs))
        dy_r = r_ridge * math.cos(ang)
        dz_r = r_ridge * math.sin(ang)
        va = bm_tejas.verts.new((X_start, 0.85 + dy_r, Z_end + dz_r))
        vb = bm_tejas.verts.new((X_end + 0.40, 0.85 + dy_r, Z_end + dz_r))
        if s > 0:
            bm_tejas.faces.new((v_r_a, va, vb, v_r_b))
        v_r_a, v_r_b = va, vb

    # Base sólida
    v1 = bm_tejas.verts.new((X_start, -0.42, Z_start))
    v2 = bm_tejas.verts.new((X_end + 0.40, -0.42, Z_start))
    v3 = bm_tejas.verts.new((X_end + 0.40, 0.85, Z_end))
    v4 = bm_tejas.verts.new((X_start, 0.85, Z_end))
    bm_tejas.faces.new((v1, v2, v3, v4))

    bmesh.ops.recalc_face_normals(bm_tejas, faces=bm_tejas.faces)
    for f in bm_tejas.faces:
        f.smooth = True
    m_tj = bpy.data.meshes.new("Mesh_Juarez_Tejas")
    bm_tejas.to_mesh(m_tj)
    bm_tejas.free()
    obj_tejas = bpy.data.objects.new("Juarez_Tejas_Mansarda", m_tj)
    col.objects.link(obj_tejas)
    obj_tejas.data.materials.append(mats["teja"])

    return obj_struct, obj_alum, obj_glass, obj_blind, obj_fascia, obj_stripe, o_txt, obj_tejas

def build_west_facade_cardenas(mats, col):
    """Construye la Fachada Oeste por Calle Lázaro Cárdenas (Ground-Truth media_1789772450504)."""
    bm_struct = bmesh.new()
    bm_alum = bmesh.new()
    bm_glass = bmesh.new()
    bm_blind = bmesh.new()
    bm_corbels = bmesh.new()
    
    Y_start = 4.20
    Y_end = 20.20
    H_wall = 7.10
    
    # 1. Plinto basal (Z = 0.0 a 0.40)
    add_box(bm_struct, -0.05, 0.40, Y_start, Y_end, 0.0, 0.40)
    
    # 2. Machones / Pilastras verticales en Calle Cárdenas (sobresalen 4 cm hacia -X)
    col_y = [4.20, 8.20, 12.20, 16.20, 19.80]
    for cy in col_y:
        add_box(bm_struct, -0.04, 0.35, cy, cy + 0.60, 0.40, H_wall)
        
    # Muros rehundidos (X = 0.02 a 0.30)
    add_box(bm_struct, 0.02, 0.30, Y_start, Y_end, 3.20, 3.30)
    add_box(bm_struct, 0.02, 0.30, Y_start, Y_end, 4.30, 5.10)
    add_box(bm_struct, 0.02, 0.30, Y_start, Y_end, 6.75, H_wall)
    
    # Cornisa corrida blanca
    add_box(bm_struct, -0.20, 0.40, Y_start, Y_end + 0.20, 7.10, 7.25)
    add_box(bm_struct, -0.40, 0.85, Y_start, Y_end + 0.20, 7.25, 7.45)
    
    # 3. Ménsulas / Canecillos de concreto en voladizo (Corbels)
    for cy in col_y:
        c_mid = cy + 0.30
        add_box(bm_corbels, -0.36, 0.02, c_mid - 0.12, c_mid + 0.12, 6.65, 7.25)
        add_box(bm_corbels, -0.26, 0.02, c_mid - 0.09, c_mid + 0.09, 6.45, 6.65)
        
    bmesh.ops.recalc_face_normals(bm_corbels, faces=bm_corbels.faces)
    m_cb = bpy.data.meshes.new("Mesh_Cardenas_Canecillos")
    bm_corbels.to_mesh(m_cb)
    bm_corbels.free()
    obj_corbels = bpy.data.objects.new("Cardenas_Canecillos_Alero", m_cb)
    col.objects.link(obj_corbels)
    obj_corbels.data.materials.append(mats["muro"])

    # 4. Cancelería de crujías en Calle Cárdenas
    bays_y = [
        (4.80, 8.20),
        (8.80, 12.20),
        (12.80, 16.20),
        (16.80, 19.80)
    ]
    
    for idx, (y1, y2) in enumerate(bays_y):
        # Planta baja
        w_f = 0.05
        add_box(bm_alum, 0.04, 0.12, y1, y1 + w_f, 0.40, 3.20)
        add_box(bm_alum, 0.04, 0.12, y2 - w_f, y2, 0.40, 3.20)
        add_box(bm_alum, 0.04, 0.12, y1, y2, 0.40, 0.40 + w_f)
        add_box(bm_alum, 0.04, 0.12, y1, y2, 3.20 - w_f, 3.20)
        step = (y2 - y1) / 3.0
        add_box(bm_alum, 0.04, 0.12, y1 + step - 0.025, y1 + step + 0.025, 0.40, 3.20)
        add_box(bm_alum, 0.04, 0.12, y1 + 2*step - 0.025, y1 + 2*step + 0.025, 0.40, 3.20)
        add_box(bm_glass, 0.075, 0.085, y1 + w_f, y2 - w_f, 0.40 + w_f, 3.20 - w_f)
        add_box(bm_blind, 0.135, 0.145, y1 + w_f, y2 - w_f, 0.42, 3.18)
        
        # Planta alta
        w_f2 = 0.04
        add_box(bm_alum, 0.04, 0.10, y1, y1 + w_f2, 5.10, 6.75)
        add_box(bm_alum, 0.04, 0.10, y2 - w_f2, y2, 5.10, 6.75)
        add_box(bm_alum, 0.04, 0.10, y1, y2, 5.10, 5.10 + w_f2)
        add_box(bm_alum, 0.04, 0.10, y1, y2, 6.75 - w_f2, 6.75)
        for i in range(1, 3):
            my = y1 + i * step
            add_box(bm_alum, 0.04, 0.10, my - 0.02, my + 0.02, 5.10, 6.75)
        add_box(bm_glass, 0.065, 0.075, y1 + w_f2, y2 - w_f2, 5.10 + w_f2, 6.75 - w_f2)

    # Convertir a objetos
    bmesh.ops.recalc_face_normals(bm_struct, faces=bm_struct.faces)
    m_st_w = bpy.data.meshes.new("Mesh_Cardenas_Estructura")
    bm_struct.to_mesh(m_st_w)
    bm_struct.free()
    obj_struct = bpy.data.objects.new("Cardenas_Estructura", m_st_w)
    col.objects.link(obj_struct)
    obj_struct.data.materials.append(mats["muro"])
    obj_struct.data.materials.append(mats["zocalo"])
    for p in m_st_w.polygons:
        if sum(m_st_w.vertices[v].co.z for v in p.vertices) / len(p.vertices) < 0.42:
            p.material_index = 1
        else:
            p.material_index = 0

    bmesh.ops.recalc_face_normals(bm_alum, faces=bm_alum.faces)
    m_al_w = bpy.data.meshes.new("Mesh_Cardenas_Canceleria")
    bm_alum.to_mesh(m_al_w)
    bm_alum.free()
    obj_alum = bpy.data.objects.new("Cardenas_Canceleria", m_al_w)
    col.objects.link(obj_alum)
    obj_alum.data.materials.append(mats["aluminio"])

    bmesh.ops.recalc_face_normals(bm_glass, faces=bm_glass.faces)
    m_gl_w = bpy.data.meshes.new("Mesh_Cardenas_Vidrio")
    bm_glass.to_mesh(m_gl_w)
    bm_glass.free()
    obj_glass = bpy.data.objects.new("Cardenas_Vidrio", m_gl_w)
    col.objects.link(obj_glass)
    obj_glass.data.materials.append(mats["vidrio"])

    bmesh.ops.recalc_face_normals(bm_blind, faces=bm_blind.faces)
    m_bl_w = bpy.data.meshes.new("Mesh_Cardenas_Persianas")
    bm_blind.to_mesh(m_bl_w)
    bm_blind.free()
    obj_blind = bpy.data.objects.new("Cardenas_Persianas", m_bl_w)
    col.objects.link(obj_blind)
    obj_blind.data.materials.append(mats["persianas"])

    # 5. Fascia azul marino Alucobond (#16215B)
    bm_fascia = bmesh.new()
    add_box(bm_fascia, -0.14, 0.02, Y_start, Y_end, 3.20, 4.30)
    bmesh.ops.recalc_face_normals(bm_fascia, faces=bm_fascia.faces)
    m_fa_w = bpy.data.meshes.new("Mesh_Cardenas_Fascia")
    bm_fascia.to_mesh(m_fa_w)
    bm_fascia.free()
    obj_fascia = bpy.data.objects.new("Cardenas_Fascia_Azul", m_fa_w)
    col.objects.link(obj_fascia)
    obj_fascia.data.materials.append(mats["fascia"])

    # Filete blanco horizontal
    bm_stripe = bmesh.new()
    add_box(bm_stripe, -0.148, -0.138, Y_start + 6.0, Y_end - 0.20, 3.72, 3.76)
    bmesh.ops.recalc_face_normals(bm_stripe, faces=bm_stripe.faces)
    m_str_w = bpy.data.meshes.new("Mesh_Cardenas_Stripe")
    bm_stripe.to_mesh(m_str_w)
    bm_stripe.free()
    obj_stripe = bpy.data.objects.new("Cardenas_Fascia_Stripe", m_str_w)
    col.objects.link(obj_stripe)
    obj_stripe.data.materials.append(mats["rotulo_blanco"])

    # Texto "BBVA Bancomer"
    f_txt_w = bpy.data.curves.new(type="FONT", name="Font_Cardenas_BBVA")
    f_txt_w.body = "BBVA Bancomer"
    f_txt_w.size = 0.50
    f_txt_w.extrude = 0.025
    o_txt_w = bpy.data.objects.new("Cardenas_Texto_Fascia", f_txt_w)
    col.objects.link(o_txt_w)
    o_txt_w.location = (-0.165, Y_start + 5.0, 3.50)
    o_txt_w.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_txt_w.data.materials.append(mats["rotulo_blanco"])

    # Rótulo de Cajero Exterior
    f_atm_w = bpy.data.curves.new(type="FONT", name="Font_Cardenas_ATM")
    f_atm_w.body = "CAJERO\nAUTOMATICO"
    f_atm_w.size = 0.12
    f_atm_w.extrude = 0.01
    o_atm_w = bpy.data.objects.new("Cardenas_ATM_Sign", f_atm_w)
    col.objects.link(o_atm_w)
    o_atm_w.location = (0.03, 5.40, 2.75)
    o_atm_w.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_atm_w.data.materials.append(mats["rotulo_blanco"])

    # 6. Mansarda de Tejas en Calle Cárdenas
    bm_tejas = bmesh.new()
    Z_start = 7.45
    Z_end = 8.15
    dx = 0.85 - (-0.42)
    dz = Z_end - Z_start
    L = math.hypot(dx, dz)
    nx = -dz / L
    nz = dx / L
    n_tejas_y = 36
    step_y = (Y_end - Y_start + 0.40) / float(n_tejas_y)
    r_teja = 0.065
    n_segs = 6
    
    for i in range(n_tejas_y):
        y_c = Y_start + i * step_y + step_y * 0.5
        for j in range(3):
            t1 = j / 3.0
            t2 = (j + 1.0) / 3.0
            x_a = -0.42 + t1 * dx
            z_a = Z_start + t1 * dz
            x_b = -0.42 + t2 * dx
            z_b = Z_start + t2 * dz
            v_p_a, v_p_b = None, None
            for s in range(n_segs + 1):
                ang = math.pi * (s / float(n_segs))
                oy = r_teja * math.cos(ang)
                on = r_teja * math.sin(ang)
                va = bm_tejas.verts.new((x_a + on * nx, y_c + oy, z_a + on * nz))
                vb = bm_tejas.verts.new((x_b + on * nx, y_c + oy, z_b + on * nz))
                if s > 0:
                    bm_tejas.faces.new((v_p_a, va, vb, v_p_b))
                v_p_a, v_p_b = va, vb

    # Caballete de cumbrera
    r_ridge = 0.08
    v_r_a, v_r_b = None, None
    for s in range(n_segs + 1):
        ang = math.pi * (s / float(n_segs))
        dx_r = r_ridge * math.cos(ang)
        dz_r = r_ridge * math.sin(ang)
        va = bm_tejas.verts.new((0.85 + dx_r, Y_start, Z_end + dz_r))
        vb = bm_tejas.verts.new((0.85 + dx_r, Y_end + 0.20, Z_end + dz_r))
        if s > 0:
            bm_tejas.faces.new((v_r_a, va, vb, v_r_b))
        v_r_a, v_r_b = va, vb

    # Base sólida
    v1 = bm_tejas.verts.new((-0.42, Y_start, Z_start))
    v2 = bm_tejas.verts.new((-0.42, Y_end + 0.20, Z_start))
    v3 = bm_tejas.verts.new((0.85, Y_end + 0.20, Z_end))
    v4 = bm_tejas.verts.new((0.85, Y_start, Z_end))
    bm_tejas.faces.new((v1, v2, v3, v4))

    bmesh.ops.recalc_face_normals(bm_tejas, faces=bm_tejas.faces)
    for f in bm_tejas.faces:
        f.smooth = True
    m_tj_w = bpy.data.meshes.new("Mesh_Cardenas_Tejas")
    bm_tejas.to_mesh(m_tj_w)
    bm_tejas.free()
    obj_tejas = bpy.data.objects.new("Cardenas_Tejas_Mansarda", m_tj_w)
    col.objects.link(obj_tejas)
    obj_tejas.data.materials.append(mats["teja"])

    # 7. Inmueble Colindante Norte (Consultorio Dental según Ground-Truth)
    bm_dent = bmesh.new()
    add_box(bm_dent, -0.15, 6.0, Y_end, Y_end + 5.50, 0.0, 5.20)
    bmesh.ops.recalc_face_normals(bm_dent, faces=bm_dent.faces)
    m_dt = bpy.data.meshes.new("Mesh_Colindancia_Norte")
    bm_dent.to_mesh(m_dt)
    bm_dent.free()
    obj_dent = bpy.data.objects.new("Colindancia_Norte_Dentista", m_dt)
    col.objects.link(obj_dent)
    obj_dent.data.materials.append(mats["muro"])

    return obj_struct, obj_corbels, obj_alum, obj_glass, obj_blind, obj_fascia, obj_stripe, [o_txt_w, o_atm_w], obj_tejas, obj_dent

def build_east_facade_and_parking(mats, col):
    """Construye la Fachada Este (Callejón/Estacionamiento), rampa, caseta y letrero ENTRADA BBVA."""
    bm = bmesh.new()
    X_east = 22.80
    
    # 1. Muro lateral este con antepecho y vanos altos
    add_box(bm, X_east - 0.60, X_east, 0.0, 16.0, 0.40, 7.10)
    # Losa interior de azotea (dividida en dos cuerpos para respetar el chaflán a 45º)
    add_box(bm, 4.20, X_east, 0.40, 16.0, 7.00, 7.25)
    add_box(bm, 0.40, 4.20, 4.20, 16.0, 7.00, 7.25)
    # Muro posterior interior
    add_box(bm, 0.40, X_east, 15.40, 16.0, 0.40, 7.10)
    
    # 2. Banqueta urbana envolvente (conecta Av. Juárez y Calle Cárdenas)
    add_box(bm, -3.80, X_east + 4.50, -3.80, 0.0, 0.0, 0.18)
    add_box(bm, -3.80, 0.0, 0.0, 24.0, 0.0, 0.18)
    # Cordón rojo oficial
    add_box(bm, -3.88, X_east + 4.50, -3.88, -3.76, 0.0, 0.20)
    add_box(bm, -3.88, -3.76, -3.88, 24.0, 0.0, 0.20)
    
    # 3. Murete de confinamiento de rampa hacia estacionamiento
    add_box(bm, X_east + 0.60, X_east + 0.85, 0.0, 12.0, 0.18, 1.10)
    # Suelo inclinado de rampa descendente
    add_box(bm, X_east + 0.85, X_east + 4.20, 0.0, 12.0, -0.45, 0.05)
    # Caseta de vigilancia
    add_box(bm, X_east + 1.20, X_east + 3.00, 1.5, 3.5, 0.18, 2.70)
    add_box(bm, X_east + 1.10, X_east + 3.10, 1.4, 3.6, 2.70, 2.85)
    
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    m_east = bpy.data.meshes.new("Mesh_East_Parking")
    bm.to_mesh(m_east)
    bm.free()
    obj_east = bpy.data.objects.new("East_Parking_Estructura", m_east)
    col.objects.link(obj_east)
    obj_east.data.materials.append(mats["muro"])
    obj_east.data.materials.append(mats["zocalo"])
    obj_east.data.materials.append(mats["cordon_rojo"])
    obj_east.data.materials.append(mats["azotea"])
    
    for p in m_east.polygons:
        c_x = sum(m_east.vertices[v].co.x for v in p.vertices) / len(p.vertices)
        c_y = sum(m_east.vertices[v].co.y for v in p.vertices) / len(p.vertices)
        c_z = sum(m_east.vertices[v].co.z for v in p.vertices) / len(p.vertices)
        if c_z > 7.15:
            p.material_index = 3
        elif c_y < -3.72 or (c_x < -3.72 and c_y > 0):
            p.material_index = 2
        elif c_z < 0.42:
            p.material_index = 1
        else:
            p.material_index = 0

    # 4. Barandilla de acero blanco sobre murete de rampa
    bm_rail = bmesh.new()
    rx = X_east + 0.72
    add_box(bm_rail, rx - 0.02, rx + 0.02, 0.0, 12.0, 1.85, 1.90)
    add_box(bm_rail, rx - 0.015, rx + 0.015, 0.0, 12.0, 1.45, 1.48)
    for py in [0.2, 2.2, 4.2, 6.2, 8.2, 10.2, 11.9]:
        add_box(bm_rail, rx - 0.03, rx + 0.03, py - 0.03, py + 0.03, 1.10, 1.85)
    bmesh.ops.recalc_face_normals(bm_rail, faces=bm_rail.faces)
    m_rl = bpy.data.meshes.new("Mesh_Rampa_Barandal")
    bm_rail.to_mesh(m_rl)
    bm_rail.free()
    obj_rail = bpy.data.objects.new("Rampa_Barandal_Blanco", m_rl)
    col.objects.link(obj_rail)
    obj_rail.data.materials.append(mats["barandal"])

    # 5. Letrero oficial 'ENTRADA BBVA ->' fijado sobre el murete de rampa
    bm_sign = bmesh.new()
    add_box(bm_sign, rx - 0.03, rx + 0.03, 0.60, 0.66, 1.10, 2.15)
    add_box(bm_sign, rx - 0.45, rx + 0.45, 0.61, 0.65, 1.70, 2.25)
    bmesh.ops.recalc_face_normals(bm_sign, faces=bm_sign.faces)
    m_sn = bpy.data.meshes.new("Mesh_Senal_Entrada")
    bm_sign.to_mesh(m_sn)
    bm_sign.free()
    obj_sign = bpy.data.objects.new("Senal_Entrada_BBVA", m_sn)
    col.objects.link(obj_sign)
    obj_sign.data.materials.append(mats["senal_azul"])

    f_sign = bpy.data.curves.new(type="FONT", name="Font_Senal_Rampa")
    f_sign.body = "ENTRADA\nBBVA ➔"
    f_sign.size = 0.12
    f_sign.extrude = 0.008
    o_sign = bpy.data.objects.new("Texto_Senal_Rampa", f_sign)
    col.objects.link(o_sign)
    o_sign.location = (rx - 0.38, 0.59, 2.05)
    o_sign.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    o_sign.data.materials.append(mats["rotulo_blanco"])

    return obj_east, obj_rail, obj_sign, o_sign

def setup_lighting_and_render(col):
    """Configura iluminación diurna y 5 cámaras para cubrir todas las caras del edificio."""
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World_Tecate")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs["Color"].default_value = (0.58, 0.76, 0.94, 1.0)
        bg_node.inputs["Strength"].default_value = 1.0

    # Sol principal diurno (ilumina Fachada Sur y Chaflán a 45º)
    sun_data = bpy.data.lights.new(name="Sol_Diurno", type='SUN')
    sun_data.energy = 4.8
    sun_data.color = (1.0, 0.98, 0.92)
    sun_obj = bpy.data.objects.new("Sol_Diurno", sun_data)
    col.objects.link(sun_obj)
    sun_obj.rotation_euler = (math.radians(52.0), math.radians(16.0), math.radians(-40.0))
    
    # Luz difusa de relleno (ilumina Fachada Oeste)
    fill_data = bpy.data.lights.new(name="Luz_Relleno", type='SUN')
    fill_data.energy = 2.4
    fill_data.color = (0.78, 0.88, 1.0)
    fill_obj = bpy.data.objects.new("Luz_Relleno", fill_data)
    col.objects.link(fill_obj)
    fill_obj.rotation_euler = (math.radians(115.0), math.radians(0.0), math.radians(135.0))

    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    if hasattr(scene.cycles, 'device'):
        scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'

    cams = {}
    
    # 1. Cámara 'Guajardo_45': Perspectiva frontal directa al chaflán a 45º (Ground-Truth media_1789772450504)
    c1_data = bpy.data.cameras.new("Cam_Guajardo_45")
    c1_data.lens = 26
    c1 = bpy.data.objects.new("Cam_Guajardo_45", c1_data)
    col.objects.link(c1)
    loc1 = Vector((-9.50, -9.50, 3.20))
    tgt1 = Vector((1.90, 1.90, 6.20))
    dir1 = tgt1 - loc1
    c1.location = loc1
    c1.rotation_euler = dir1.to_track_quat('-Z', 'Y').to_euler()
    cams["guajardo_45"] = c1

    # 2. Cámara 'Juarez_Frontal': Elevación de la Fachada Sur (Av. Juárez, Ground-Truth xB3bx)
    c2_data = bpy.data.cameras.new("Cam_Juarez_Frontal")
    c2_data.lens = 28
    c2 = bpy.data.objects.new("Cam_Juarez_Frontal", c2_data)
    col.objects.link(c2)
    c2.location = (13.50, -22.00, 4.80)
    c2.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    cams["juarez_frontal"] = c2

    # 3. Cámara 'Cardenas_West': Elevación de la Fachada Oeste por Calle Lázaro Cárdenas
    c3_data = bpy.data.cameras.new("Cam_Cardenas_West")
    c3_data.lens = 28
    c3 = bpy.data.objects.new("Cam_Cardenas_West", c3_data)
    col.objects.link(c3)
    c3.location = (-18.00, 12.00, 4.80)
    c3.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    cams["cardenas_west"] = c3

    # 4. Cámara 'East_Parking': Perspectiva de rampa, caseta y letrero ENTRADA BBVA
    c4_data = bpy.data.cameras.new("Cam_East_Parking")
    c4_data.lens = 30
    c4 = bpy.data.objects.new("Cam_East_Parking", c4_data)
    col.objects.link(c4)
    loc4 = Vector((30.00, -8.00, 4.20))
    tgt4 = Vector((22.80, 4.00, 2.80))
    dir4 = tgt4 - loc4
    c4.location = loc4
    c4.rotation_euler = dir4.to_track_quat('-Z', 'Y').to_euler()
    cams["east_parking"] = c4

    # 5. Cámara 'Aerial_Top': Vista aérea cenital que reproduce la imagen satelital media_1789772893709
    c5_data = bpy.data.cameras.new("Cam_Aerial_Top")
    c5_data.lens = 45
    c5 = bpy.data.objects.new("Cam_Aerial_Top", c5_data)
    col.objects.link(c5)
    c5.location = (11.00, 9.00, 38.00)
    c5.rotation_euler = (0.0, 0.0, math.radians(-90.0))
    cams["aerial_top"] = c5

    return cams

def generate_godot_tscn(tscn_path, glb_rel_path):
    """Genera la escena .tscn de Godot 4 con StaticBody3D y colisiones analíticas precisas."""
    tscn_content = f"""[gd_scene load_steps=5 format=3 uid="uid://bbva_tecate_centro_004"]

[ext_resource type="PackedScene" path="{glb_rel_path}" id="1_mesh"]

[sub_resource type="BoxShape3D" id="BoxShape3D_cuerpo"]
size = Vector3(22.8, 7.3, 16.0)

[sub_resource type="BoxShape3D" id="BoxShape3D_torreon"]
size = Vector3(6.0, 9.0, 6.0)

[sub_resource type="BoxShape3D" id="BoxShape3D_rampa"]
size = Vector3(3.0, 1.2, 12.0)

[node name="BBVA_Tecate" type="StaticBody3D"]

[node name="ModelInstance" parent="." instance=ExtResource("1_mesh")]

[node name="Col_Cuerpo" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 11.4, 3.65, 8.0)
shape = SubResource("BoxShape3D_cuerpo")

[node name="Col_Torreon" type="CollisionShape3D" parent="."]
transform = Transform3D(0.707107, 0, -0.707107, 0, 1, 0, 0.707107, 0, 0.707107, 2.1, 4.5, 2.1)
shape = SubResource("BoxShape3D_torreon")

[node name="Col_Rampa" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 24.5, 0.6, 6.0)
shape = SubResource("BoxShape3D_rampa")
"""
    with open(tscn_path, "w", encoding="utf-8") as f:
        f.write(tscn_content)
    print(f"--> Escena Godot generada: {tscn_path}")

def main():
    print("================================================================")
    print(" GENERADOR PROCEDURAL 3D V4.1: BANCO BBVA TECATE CENTRO         ")
    print(" (Ochava 45º limpia, Fachadas Juárez, Cárdenas y Estacionamiento)")
    print("================================================================")
    
    root_col = clean_scene()
    mats = create_materials()
    
    # 1. Esquina ochavada a 45º: Torreón Guajardo 1954 y espectacular en azotea
    obj_tower, obj_t_glass, objs_steel, texts_guaj, texts_totem = build_45deg_guajardo_corner(mats, root_col)
    
    # 2. Fachada Sur (Av. Benito Juárez)
    obj_juarez_st, obj_j_alum, obj_j_gl, obj_j_bl, obj_j_fa, obj_j_str, o_j_txt, obj_j_tj = build_south_facade_juarez(mats, root_col)
    
    # 3. Fachada Oeste (Calle Presidente Lázaro Cárdenas)
    obj_card_st, obj_c_cb, obj_c_al, obj_c_gl, obj_c_bl, obj_c_fa, obj_c_str, texts_c_atm, obj_c_tj, obj_dent = build_west_facade_cardenas(mats, root_col)
    
    # 4. Fachada Este (Estacionamiento), rampa, caseta y letrero ENTRADA BBVA
    obj_east, obj_rail, obj_sign, o_sign_r = build_east_facade_and_parking(mats, root_col)
    
    # 5. Iluminación y 5 cámaras técnicas calibradas
    cams = setup_lighting_and_render(root_col)
    
    # 6. Guardar archivo maestro Blender (.blend)
    blend_path = "blender_assets/buildings/bbva_tecate_centro.blend"
    os.makedirs(os.path.dirname(blend_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"--> Archivo maestro Blender guardado: {blend_path}")
    
    # 7. Exportar GLB para Godot 4
    glb_path = "godot_project/assets/buildings/bbva_tecate_centro.glb"
    os.makedirs(os.path.dirname(glb_path), exist_ok=True)
    
    bpy.ops.object.select_all(action='DESELECT')
    render_types = {'MESH', 'CURVE', 'FONT'}
    for o in root_col.objects:
        if o.type in render_types:
            o.select_set(True)
    bpy.context.view_layer.objects.active = obj_tower
    
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_materials='EXPORT',
        export_yup=True
    )
    print(f"--> Asset Godot exportado: {glb_path}")
    
    # 8. Generar escena Godot .tscn
    tscn_path = "godot_project/assets/buildings/bbva_tecate_centro.tscn"
    generate_godot_tscn(tscn_path, "res://assets/buildings/bbva_tecate_centro.glb")
    
    # 9. Renderizar las 5 vistas técnicas de validación
    scene = bpy.context.scene
    renders = [
        ("guajardo_45", "docs/images/bbva/bbva_guajardo_45.png", 1280, 720),
        ("juarez_frontal", "docs/images/bbva/bbva_juarez_frontal.png", 1280, 720),
        ("cardenas_west", "docs/images/bbva/bbva_cardenas_west.png", 1280, 720),
        ("east_parking", "docs/images/bbva/bbva_east_parking.png", 1280, 720),
        ("aerial_top", "docs/images/bbva/bbva_aerial_top.png", 1024, 1024)
    ]
    
    for cam_key, out_path, rx, ry in renders:
        abs_out = os.path.abspath(out_path)
        os.makedirs(os.path.dirname(abs_out), exist_ok=True)
        scene.camera = cams[cam_key]
        scene.render.resolution_x = rx
        scene.render.resolution_y = ry
        scene.render.filepath = abs_out
        bpy.ops.render.render(write_still=True)
        print(f"--> Render {cam_key} guardado en: {abs_out}")

    print("================================================================")
    print(" GENERACIÓN V4.1 FINALIZADA CON ÉXITO                           ")
    print("================================================================")

if __name__ == "__main__":
    main()
