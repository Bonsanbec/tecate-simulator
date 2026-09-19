"""
=============================================================================
Generador 3D Paramétrico V5.0: Banco BBVA Tecate Centro (2009 Ground-Truth)
=============================================================================
Reconstrucción fidedigna con consenso multi-perspectiva y verdad de terreno histórica (2009):
- Esquina Ochavada a 45º: Torreón 'EDIFICIO LIC. JOSE F. GUAJARDO 1956'
  en trapecio rocoso desgastado con mosaico veneciano añil, letras de bronce,
  acceso principal en PB y espectacular de azotea 2009 (recuadro BBVA + Bancomer + RED Cajero).
- Fachada Oeste (Calle Presidente Lázaro Cárdenas): Edificio continuo hasta DENTISTA
  (longitud 27.2 m), alero continuo con canecillos/ménsulas, portal de cajero exterior
  con marquesina luminosa, despachos jurídicos y contables, y consultorio dental.
- Fachada Sur (Avenida Benito Juárez): Fascia azul cobalto 2009 con recuadro blanco BBVA,
  4 crujías exactas con despachos en PA ('CASAS TERRENOS RANCHOS' y 'JUAN VARGAS R'),
  mansarda de tejas y cancelería Tintex con persianas.
- Fachada Este (Estacionamiento): Muro detallado con 4 vanos en PA ('LICENCIADO EN DERECHO'),
  ventanales y puerta peatonal con luminaria en PB. Caseta blanca y letrero 'ENTRADA BBVA ->'
  reubicados ortogonalmente hacia Av. Juárez.
- Desacoplamiento de Banqueta: El asset del edificio no incluye la banqueta (apoya a Z = 0.0).

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
    """Crea la paleta PBR arquitectónica completa para la época 2009."""
    mats = {}
    
    # 1. Torreón Guajardo: Mosaico Vítreo / Piedra Meteorizada Violeta-Gris Desgastada
    mat_mosaico = bpy.data.materials.new(name="M_Guajardo_Mosaico")
    mat_mosaico.use_nodes = True
    nodes_m = mat_mosaico.node_tree.nodes
    links_m = mat_mosaico.node_tree.links
    bsdf_m = nodes_m.get("Principled BSDF")
    if bsdf_m:
        # Tono violeta-grisáceo pizarra desgastado por la intemperie (Ground Truth media_1789777326353)
        bsdf_m.inputs["Base Color"].default_value = (0.16, 0.15, 0.19, 1.0)
        bsdf_m.inputs["Metallic"].default_value = 0.02
        bsdf_m.inputs["Roughness"].default_value = 0.75
        tex_vor = nodes_m.new('ShaderNodeTexVoronoi')
        tex_vor.inputs['Scale'].default_value = 140.0
        bump_node = nodes_m.new('ShaderNodeBump')
        bump_node.inputs['Strength'].default_value = 0.35
        links_m.new(tex_vor.outputs['Distance'], bump_node.inputs['Height'])
        links_m.new(bump_node.outputs['Normal'], bsdf_m.inputs['Normal'])
    mats["mosaico_guajardo"] = mat_mosaico

    # Remate de piedra desgastada en la cúspide del torreón (coping)
    mat_coping = bpy.data.materials.new(name="M_Guajardo_Coping")
    mat_coping.use_nodes = True
    bsdf_cp = mat_coping.node_tree.nodes.get("Principled BSDF")
    if bsdf_cp:
        bsdf_cp.inputs["Base Color"].default_value = (0.32, 0.31, 0.30, 1.0)
        bsdf_cp.inputs["Roughness"].default_value = 0.80
    mats["coping_rocoso"] = mat_coping

    # 2. Rótulo de Bronce Fundido Guajardo (Latón/Bronce con pátina dorada clara y legible)
    mat_bronce = bpy.data.materials.new(name="M_Guajardo_Bronce")
    mat_bronce.use_nodes = True
    bsdf_b = mat_bronce.node_tree.nodes.get("Principled BSDF")
    if bsdf_b:
        bsdf_b.inputs["Base Color"].default_value = (0.85, 0.70, 0.22, 1.0)
        bsdf_b.inputs["Metallic"].default_value = 0.85
        bsdf_b.inputs["Roughness"].default_value = 0.20
    mats["bronce"] = mat_bronce

    # 3. Fascia y Espectacular 2009: Azul Cobalto BBVA Bancomer (#00288E)
    mat_fascia = bpy.data.materials.new(name="M_BBVA_Fascia_Cobalto_2009")
    mat_fascia.use_nodes = True
    bsdf_f = mat_fascia.node_tree.nodes.get("Principled BSDF")
    if bsdf_f:
        bsdf_f.inputs["Base Color"].default_value = (0.012, 0.045, 0.280, 1.0)
        bsdf_f.inputs["Metallic"].default_value = 0.20
        bsdf_f.inputs["Roughness"].default_value = 0.30
    mats["fascia"] = mat_fascia

    # Letras BBVA azules dentro del recuadro blanco (#00288E)
    mat_bbva_blue = bpy.data.materials.new(name="M_BBVA_Letras_Azul")
    mat_bbva_blue.use_nodes = True
    bsdf_bbl = mat_bbva_blue.node_tree.nodes.get("Principled BSDF")
    if bsdf_bbl:
        bsdf_bbl.inputs["Base Color"].default_value = (0.012, 0.045, 0.280, 1.0)
        bsdf_bbl.inputs["Roughness"].default_value = 0.20
    mats["bbva_azul"] = mat_bbva_blue

    # 4. Fascia Metálica Plateada (Sección Dentista / Despachos en Cárdenas)
    mat_silver = bpy.data.materials.new(name="M_Fascia_Silver_Alucobond")
    mat_silver.use_nodes = True
    bsdf_sil = mat_silver.node_tree.nodes.get("Principled BSDF")
    if bsdf_sil:
        bsdf_sil.inputs["Base Color"].default_value = (0.50, 0.52, 0.55, 1.0)
        bsdf_sil.inputs["Metallic"].default_value = 0.70
        bsdf_sil.inputs["Roughness"].default_value = 0.30
    mats["fascia_silver"] = mat_silver

    # Letrero DENTISTA (Azul marino oscuro comercial #0C1635)
    mat_dent = bpy.data.materials.new(name="M_Letrero_Dentista")
    mat_dent.use_nodes = True
    bsdf_dn = mat_dent.node_tree.nodes.get("Principled BSDF")
    if bsdf_dn:
        bsdf_dn.inputs["Base Color"].default_value = (0.008, 0.015, 0.045, 1.0)
        bsdf_dn.inputs["Roughness"].default_value = 0.35
    mats["letrero_dentista"] = mat_dent

    # Letras 3D DENTISTA en relieve (Oro/latón dorado brillante, Ground Truth media_1789778345732)
    mat_oro = bpy.data.materials.new(name="M_Dentista_Oro")
    mat_oro.use_nodes = True
    bsdf_oro = mat_oro.node_tree.nodes.get("Principled BSDF")
    if bsdf_oro:
        bsdf_oro.inputs["Base Color"].default_value = (0.88, 0.72, 0.28, 1.0)
        bsdf_oro.inputs["Metallic"].default_value = 0.85
        bsdf_oro.inputs["Roughness"].default_value = 0.22
    mats["oro_letras"] = mat_oro

    # Texto rojo secundario rótulo colgante Dr. Álvarez
    mat_rojo_txt = bpy.data.materials.new(name="M_Dentista_Txt_Rojo")
    mat_rojo_txt.use_nodes = True
    bsdf_rt = mat_rojo_txt.node_tree.nodes.get("Principled BSDF")
    if bsdf_rt:
        bsdf_rt.inputs["Base Color"].default_value = (0.65, 0.05, 0.05, 1.0)
        bsdf_rt.inputs["Roughness"].default_value = 0.30
    mats["rojo_letras"] = mat_rojo_txt

    # Póster institucional Bancomer en PB (Crujía 2)
    mat_pos = bpy.data.materials.new(name="M_Bancomer_Poster")
    mat_pos.use_nodes = True
    bsdf_pos = mat_pos.node_tree.nodes.get("Principled BSDF")
    if bsdf_pos:
        bsdf_pos.inputs["Base Color"].default_value = (0.012, 0.045, 0.280, 1.0)
        bsdf_pos.inputs["Roughness"].default_value = 0.30
    mats["poster_azul"] = mat_pos

    # Concreto peldaños escalera Dentista
    mat_esc = bpy.data.materials.new(name="M_Escalera_Concreto")
    mat_esc.use_nodes = True
    bsdf_esc = mat_esc.node_tree.nodes.get("Principled BSDF")
    if bsdf_esc:
        bsdf_esc.inputs["Base Color"].default_value = (0.55, 0.53, 0.50, 1.0)
        bsdf_esc.inputs["Roughness"].default_value = 0.85
    mats["escalera_dentista"] = mat_esc

    # Muros interiores zaguán Dentista (crema cálido)
    mat_hall = bpy.data.materials.new(name="M_Hall_Dentista")
    mat_hall.use_nodes = True
    bsdf_hl = mat_hall.node_tree.nodes.get("Principled BSDF")
    if bsdf_hl:
        bsdf_hl.inputs["Base Color"].default_value = (0.80, 0.77, 0.70, 1.0)
        bsdf_hl.inputs["Roughness"].default_value = 0.85
    mats["interior_hall"] = mat_hall

    # Bolardo amarillo de estacionamiento
    mat_bol = bpy.data.materials.new(name="M_Bolardo_Amarillo")
    mat_bol.use_nodes = True
    bsdf_bol = mat_bol.node_tree.nodes.get("Principled BSDF")
    if bsdf_bol:
        bsdf_bol.inputs["Base Color"].default_value = (0.90, 0.75, 0.05, 1.0)
        bsdf_bol.inputs["Roughness"].default_value = 0.40
    mats["bolardo_amarillo"] = mat_bol

    # 5. Caja de Luz Cajero Automático Exterior (#001C58)
    mat_atm_box = bpy.data.materials.new(name="M_ATM_Caja_Azul")
    mat_atm_box.use_nodes = True
    bsdf_atm = mat_atm_box.node_tree.nodes.get("Principled BSDF")
    if bsdf_atm:
        bsdf_atm.inputs["Base Color"].default_value = (0.006, 0.020, 0.120, 1.0)
        bsdf_atm.inputs["Roughness"].default_value = 0.25
    mats["atm_caja"] = mat_atm_box

    # 6. Logotipo RED (Rojo #C8102E)
    mat_red = bpy.data.materials.new(name="M_RED_Logo_Rojo")
    mat_red.use_nodes = True
    bsdf_rd = mat_red.node_tree.nodes.get("Principled BSDF")
    if bsdf_rd:
        bsdf_rd.inputs["Base Color"].default_value = (0.58, 0.02, 0.04, 1.0)
        bsdf_rd.inputs["Roughness"].default_value = 0.25
    mats["red_logo"] = mat_red

    # 7. Verde Cajero Automático (#006B35)
    mat_verde = bpy.data.materials.new(name="M_BBVA_Cajero_Verde")
    mat_verde.use_nodes = True
    bsdf_g = mat_verde.node_tree.nodes.get("Principled BSDF")
    if bsdf_g:
        bsdf_g.inputs["Base Color"].default_value = (0.005, 0.18, 0.055, 1.0)
        bsdf_g.inputs["Roughness"].default_value = 0.25
    mats["cajero_verde"] = mat_verde

    # 8. Muro Estuco Blanco Cálido (#F0EDE8)
    mat_muro = bpy.data.materials.new(name="M_BBVA_Muro_Blanco")
    mat_muro.use_nodes = True
    bsdf_w = mat_muro.node_tree.nodes.get("Principled BSDF")
    if bsdf_w:
        bsdf_w.inputs["Base Color"].default_value = (0.87, 0.85, 0.82, 1.0)
        bsdf_w.inputs["Metallic"].default_value = 0.0
        bsdf_w.inputs["Roughness"].default_value = 0.82
    mats["muro"] = mat_muro

    # 9. Vidrio Tintex Reflectivo Oscuro (#0B1520)
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

    # 10. Cancelería de Aluminio Natural (#A4A8AD)
    mat_alum = bpy.data.materials.new(name="M_BBVA_Canceleria")
    mat_alum.use_nodes = True
    bsdf_a = mat_alum.node_tree.nodes.get("Principled BSDF")
    if bsdf_a:
        bsdf_a.inputs["Base Color"].default_value = (0.42, 0.44, 0.47, 1.0)
        bsdf_a.inputs["Metallic"].default_value = 0.85
        bsdf_a.inputs["Roughness"].default_value = 0.35
    mats["aluminio"] = mat_alum

    # 11. Zócalo Concreto Gris Grafito (#252729)
    mat_zocalo = bpy.data.materials.new(name="M_BBVA_Zocalo")
    mat_zocalo.use_nodes = True
    bsdf_z = mat_zocalo.node_tree.nodes.get("Principled BSDF")
    if bsdf_z:
        bsdf_z.inputs["Base Color"].default_value = (0.04, 0.045, 0.05, 1.0)
        bsdf_z.inputs["Roughness"].default_value = 0.90
    mats["zocalo"] = mat_zocalo

    # 12. Tejas Coloniales de Barro Terracota (#8C341E)
    mat_teja = bpy.data.materials.new(name="M_BBVA_Teja")
    mat_teja.use_nodes = True
    nodes_t = mat_teja.node_tree.nodes
    links_t = mat_teja.node_tree.links
    bsdf_t = nodes_t.get("Principled BSDF")
    if bsdf_t:
        bsdf_t.inputs["Base Color"].default_value = (0.28, 0.055, 0.022, 1.0)
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

    # 13. Rótulos y Gráfica Blanca (#FFFFFF)
    mat_blanco = bpy.data.materials.new(name="M_BBVA_Rotulo_Blanco")
    mat_blanco.use_nodes = True
    bsdf_w2 = mat_blanco.node_tree.nodes.get("Principled BSDF")
    if bsdf_w2:
        bsdf_w2.inputs["Base Color"].default_value = (0.95, 0.95, 0.95, 1.0)
        bsdf_w2.inputs["Roughness"].default_value = 0.20
    mats["rotulo_blanco"] = mat_blanco

    # 14. Persianas Verticales (#D6D3CB)
    mat_persianas = bpy.data.materials.new(name="M_BBVA_Persianas")
    mat_persianas.use_nodes = True
    bsdf_p = mat_persianas.node_tree.nodes.get("Principled BSDF")
    if bsdf_p:
        bsdf_p.inputs["Base Color"].default_value = (0.68, 0.66, 0.61, 1.0)
        bsdf_p.inputs["Roughness"].default_value = 0.90
    mats["persianas"] = mat_persianas

    # 15. Señalización Azul Entrada (#003E8A)
    mat_senal = bpy.data.materials.new(name="M_BBVA_Senal_Azul")
    mat_senal.use_nodes = True
    bsdf_s = mat_senal.node_tree.nodes.get("Principled BSDF")
    if bsdf_s:
        bsdf_s.inputs["Base Color"].default_value = (0.005, 0.048, 0.24, 1.0)
        bsdf_s.inputs["Roughness"].default_value = 0.30
    mats["senal_azul"] = mat_senal

    # 16. Barandilla Metálica Blanca (#EAEAEA)
    mat_barandal = bpy.data.materials.new(name="M_BBVA_Barandal_Blanco")
    mat_barandal.use_nodes = True
    bsdf_bar = mat_barandal.node_tree.nodes.get("Principled BSDF")
    if bsdf_bar:
        bsdf_bar.inputs["Base Color"].default_value = (0.82, 0.82, 0.82, 1.0)
        bsdf_bar.inputs["Metallic"].default_value = 0.65
        bsdf_bar.inputs["Roughness"].default_value = 0.35
    mats["barandal"] = mat_barandal

    # 17. Azotea Asfáltica (#1E1E1E)
    mat_azotea = bpy.data.materials.new(name="M_BBVA_Azotea")
    mat_azotea.use_nodes = True
    bsdf_az = mat_azotea.node_tree.nodes.get("Principled BSDF")
    if bsdf_az:
        bsdf_az.inputs["Base Color"].default_value = (0.045, 0.045, 0.045, 1.0)
        bsdf_az.inputs["Roughness"].default_value = 0.95
    mats["azotea"] = mat_azotea

    # 18. Acero Estructural (#2B2C2E)
    mat_acero = bpy.data.materials.new(name="M_BBVA_Acero_Estructural")
    mat_acero.use_nodes = True
    bsdf_st = mat_acero.node_tree.nodes.get("Principled BSDF")
    if bsdf_st:
        bsdf_st.inputs["Base Color"].default_value = (0.08, 0.085, 0.09, 1.0)
        bsdf_st.inputs["Metallic"].default_value = 0.70
        bsdf_st.inputs["Roughness"].default_value = 0.45
    mats["acero"] = mat_acero

    # 19. Cordón Rojo Banqueta (#A02020)
    mat_cordon = bpy.data.materials.new(name="M_BBVA_Cordon_Rojo")
    mat_cordon.use_nodes = True
    bsdf_cr = mat_cordon.node_tree.nodes.get("Principled BSDF")
    if bsdf_cr:
        bsdf_cr.inputs["Base Color"].default_value = (0.55, 0.08, 0.08, 1.0)
        bsdf_cr.inputs["Roughness"].default_value = 0.85
    mats["cordon_rojo"] = mat_cordon

    # 20. Concreto Banqueta (#96948E)
    mat_sw = bpy.data.materials.new(name="M_BBVA_Banqueta_Concreto")
    mat_sw.use_nodes = True
    bsdf_sw = mat_sw.node_tree.nodes.get("Principled BSDF")
    if bsdf_sw:
        bsdf_sw.inputs["Base Color"].default_value = (0.35, 0.34, 0.32, 1.0)
        bsdf_sw.inputs["Roughness"].default_value = 0.80
    mats["banqueta"] = mat_sw

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
        bm.faces.new((v1, v2, v6, v5)),
        bm.faces.new((v2, v3, v7, v6)),
        bm.faces.new((v3, v4, v8, v7)),
        bm.faces.new((v4, v1, v5, v8)),
    ]
    return faces

def build_45deg_guajardo_corner(mats, col):
    """Construye el chaflán a 45º con el Torreón Guajardo 1956 en TRAPECIO rocoso desgastado, ventanales laterales y espectacular 2009."""
    bm_tower = bmesh.new()
    bm_glass = bmesh.new()
    bm_blind = bmesh.new()
    H_tower = 9.05
    
    # Retorno Norte (Y = 4.20, X de -0.40 a 0.40)
    add_box(bm_tower, -0.40, 0.40, 4.15, 4.25, 0.0, H_tower)
    # Retorno Este (X = 4.20, Y de -0.40 a 0.40)
    add_box(bm_tower, 4.15, 4.25, -0.40, 0.40, 0.0, H_tower)
    
    # Muros interiores para sellar el prisma hacia adentro
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
    
    # 1. Trapecio rocoso desgastado de mosaico veneciano (Z = 3.20 a H_tower = 9.05)
    # Base inferior estrecha en Z = 3.20: ancho de 4.60 m (desde (0.27, 3.53) hasta (3.53, 0.27))
    # Base superior ancha en Z = 9.05: ancho de 5.80 m (desde (-0.15, 3.95) hasta (3.95, -0.15))
    # "The larger base on top and narrow base on bottom" (Comentario Guajardo)
    th = 0.45
    nx = 0.70710678 * th
    ny = 0.70710678 * th
    
    v1 = bm_tower.verts.new((0.27, 3.53, 3.20))
    v2 = bm_tower.verts.new((3.53, 0.27, 3.20))
    v3 = bm_tower.verts.new((3.95, -0.15, H_tower))
    v4 = bm_tower.verts.new((-0.15, 3.95, H_tower))
    v5 = bm_tower.verts.new((0.27 + nx, 3.53 + ny, 3.20))
    v6 = bm_tower.verts.new((3.53 + nx, 0.27 + ny, 3.20))
    v7 = bm_tower.verts.new((3.95 + nx, -0.15 + ny, H_tower))
    v8 = bm_tower.verts.new((-0.15 + nx, 3.95 + ny, H_tower))
    
    bm_tower.faces.new((v1, v2, v3, v4)) # Frente del trapecio (mosaico)
    bm_tower.faces.new((v6, v5, v8, v7)) # Dorso
    bm_tower.faces.new((v4, v8, v5, v1)) # Arista inclinada izquierda
    bm_tower.faces.new((v2, v6, v7, v3)) # Arista inclinada derecha
    bm_tower.faces.new((v4, v3, v7, v8)) # Tapa superior
    bm_tower.faces.new((v1, v5, v6, v2)) # Fondo inferior
    
    # Albardilla / Coping pétreo superior coronando la base ancha superior (Z = H_tower a H_tower + 0.12)
    th_c = 0.55
    cx_c = 0.70710678 * th_c
    cy_c = 0.70710678 * th_c
    cv1 = bm_tower.verts.new((-0.20, 4.00, H_tower - 0.05))
    cv2 = bm_tower.verts.new((4.00, -0.20, H_tower - 0.05))
    cv3 = bm_tower.verts.new((4.00, -0.20, H_tower + 0.12))
    cv4 = bm_tower.verts.new((-0.20, 4.00, H_tower + 0.12))
    cv5 = bm_tower.verts.new((-0.20 + cx_c, 4.00 + cy_c, H_tower - 0.05))
    cv6 = bm_tower.verts.new((4.00 + cx_c, -0.20 + cy_c, H_tower - 0.05))
    cv7 = bm_tower.verts.new((4.00 + cx_c, -0.20 + cy_c, H_tower + 0.12))
    cv8 = bm_tower.verts.new((-0.20 + cx_c, 4.00 + cy_c, H_tower + 0.12))
    bm_tower.faces.new((cv1, cv2, cv3, cv4))
    bm_tower.faces.new((cv6, cv5, cv8, cv7))
    bm_tower.faces.new((cv4, cv8, cv5, cv1))
    bm_tower.faces.new((cv2, cv6, cv7, cv3))
    bm_tower.faces.new((cv4, cv3, cv7, cv8))
    bm_tower.faces.new((cv1, cv5, cv6, cv2))
    
    # 2. Viga dintel de concreto sobre todo el chaflán en PB (Z = 2.85 a 3.20)
    add_wall_segment(bm_tower, -0.42, 4.22, 4.22, -0.42, 2.85, 3.20, thickness=0.50)
    
    # 3. Planta baja del chaflán: Puertas dobles en el centro Y VENTANALES a ambos lados (Comentario 9)
    # Plinto basal (zócalo oscuro Z = 0.0 a 0.40)
    add_wall_segment(bm_tower, -0.40, 4.20, 4.20, -0.40, 0.0, 0.40, thickness=0.45)
    
    # --- Vano Izquierdo: Ventanal vidriado (desde (-0.20, 4.00) hasta (1.10, 2.70)) ---
    # Cancelería de aluminio
    add_wall_segment(bm_tower, -0.20, 4.00, 1.10, 2.70, 0.40, 0.46, thickness=0.12) # Umbral
    add_wall_segment(bm_tower, -0.20, 4.00, 1.10, 2.70, 2.79, 2.85, thickness=0.12) # Dintel
    add_wall_segment(bm_tower, -0.20, 4.00, -0.14, 3.94, 0.40, 2.85, thickness=0.12) # Jamba izq
    add_wall_segment(bm_tower, 1.04, 2.76, 1.10, 2.70, 0.40, 2.85, thickness=0.12) # Jamba der
    add_wall_segment(bm_tower, 0.42, 3.38, 0.48, 3.32, 0.40, 2.85, thickness=0.12) # Montante central
    # Vidrio Tintex y persianas
    add_wall_segment(bm_glass, -0.14, 3.94, 1.04, 2.76, 0.46, 2.79, thickness=0.02)
    add_wall_segment(bm_blind, -0.12, 3.92, 1.02, 2.78, 0.48, 2.77, thickness=0.02)
    
    # --- Vano Central: Puertas dobles de acceso vidriadas (desde (1.10, 2.70) hasta (2.70, 1.10)) ---
    add_wall_segment(bm_tower, 1.10, 2.70, 2.70, 1.10, 0.0, 0.08, thickness=0.12) # Umbral
    add_wall_segment(bm_tower, 1.10, 2.70, 2.70, 1.10, 2.77, 2.85, thickness=0.12) # Dintel
    add_wall_segment(bm_tower, 1.10, 2.70, 2.70, 1.10, 2.12, 2.18, thickness=0.12) # Travesaño
    add_wall_segment(bm_tower, 1.10, 2.70, 1.16, 2.64, 0.0, 2.85, thickness=0.12) # Jamba izq
    add_wall_segment(bm_tower, 2.64, 1.16, 2.70, 1.10, 0.0, 2.85, thickness=0.12) # Jamba der
    add_wall_segment(bm_tower, 1.87, 1.93, 1.93, 1.87, 0.0, 2.15, thickness=0.12) # Parteluz central
    # Jaladeras tubulares
    add_wall_segment(bm_tower, 1.80, 1.92, 1.84, 1.88, 0.90, 1.25, thickness=0.04)
    add_wall_segment(bm_tower, 1.96, 1.76, 2.00, 1.72, 0.90, 1.25, thickness=0.04)
    # Vidrios de las puertas y montante
    add_wall_segment(bm_glass, 1.16, 2.64, 2.64, 1.16, 0.08, 2.12, thickness=0.02)
    add_wall_segment(bm_glass, 1.16, 2.64, 2.64, 1.16, 2.18, 2.77, thickness=0.02)
    
    # --- Vano Derecho: Ventanal vidriado (desde (2.70, 1.10) hasta (4.00, -0.20)) ---
    add_wall_segment(bm_tower, 2.70, 1.10, 4.00, -0.20, 0.40, 0.46, thickness=0.12) # Umbral
    add_wall_segment(bm_tower, 2.70, 1.10, 4.00, -0.20, 2.79, 2.85, thickness=0.12) # Dintel
    add_wall_segment(bm_tower, 2.70, 1.10, 2.76, 1.04, 0.40, 2.85, thickness=0.12) # Jamba izq
    add_wall_segment(bm_tower, 3.94, -0.14, 4.00, -0.20, 0.40, 2.85, thickness=0.12) # Jamba der
    add_wall_segment(bm_tower, 3.32, 0.48, 3.38, 0.42, 0.40, 2.85, thickness=0.12) # Montante central
    # Vidrio Tintex y persianas
    add_wall_segment(bm_glass, 2.76, 1.04, 3.94, -0.14, 0.46, 2.79, thickness=0.02)
    add_wall_segment(bm_blind, 2.78, 1.02, 3.92, -0.12, 0.48, 2.77, thickness=0.02)
    
    # Asignar materiales
    bmesh.ops.recalc_face_normals(bm_tower, faces=bm_tower.faces)
    m_tower = bpy.data.meshes.new("Mesh_Guajardo_Torreon")
    bm_tower.to_mesh(m_tower)
    bm_tower.free()
    obj_tower = bpy.data.objects.new("Guajardo_Torreon_45", m_tower)
    col.objects.link(obj_tower)
    obj_tower.data.materials.append(mats["mosaico_guajardo"]) # 0
    obj_tower.data.materials.append(mats["coping_rocoso"])    # 1 (remate rocoso)
    obj_tower.data.materials.append(mats["muro"])             # 2 (muro/dintel blanco)
    obj_tower.data.materials.append(mats["zocalo"])           # 3 (zócalo basal)
    obj_tower.data.materials.append(mats["aluminio"])         # 4 (cancelería)
    
    for p in m_tower.polygons:
        c_z = sum(m_tower.vertices[v].co.z for v in p.vertices) / len(p.vertices)
        c_x = sum(m_tower.vertices[v].co.x for v in p.vertices) / len(p.vertices)
        c_y = sum(m_tower.vertices[v].co.y for v in p.vertices) / len(p.vertices)
        if c_z < 0.42:
            p.material_index = 3 # Zócalo basal
        elif c_z >= H_tower - 0.02:
            p.material_index = 1 # Remate rocoso desgastado
        elif c_z >= 2.84 and c_z <= 3.22:
            p.material_index = 2 # Dintel estucado blanco
        elif c_z < 2.85:
            p.material_index = 4 # Cancelería de aluminio
        elif c_x > 4.10 or c_y > 4.10:
            p.material_index = 2 # Retornos laterales estucados
        else:
            p.material_index = 0 # Trapecio de mosaico vítreo pizarra meteorizada
            
    bmesh.ops.recalc_face_normals(bm_glass, faces=bm_glass.faces)
    m_g = bpy.data.meshes.new("Mesh_Guajardo_Vidrio")
    bm_glass.to_mesh(m_g)
    bm_glass.free()
    obj_glass = bpy.data.objects.new("Guajardo_Vidrio_Acceso", m_g)
    col.objects.link(obj_glass)
    obj_glass.data.materials.append(mats["vidrio"])

    # 5. Rótulos Históricos de Bronce (Año 1956 exacto según media_1789774890984)
    x_c = 1.90 - 0.035 * 0.7071
    y_c = 1.90 - 0.035 * 0.7071
    
    texts_guaj = []
    labels = [
        ("EDIFICIO", 0.28, 8.00),
        ("LIC. JOSE F. GUAJARDO", 0.35, 7.35),
        ("1956", 0.24, 6.75)  # <-- AÑO 1956 CONFIRMADO
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

    # 6. Espectacular de Azotea 2009 sobre el Torreón
    bm_steel = bmesh.new()
    bm_blue = bmesh.new()
    bm_white_sq = bmesh.new()
    bm_white_panel = bmesh.new()
    
    # Columna estructural central gruesa
    add_box(bm_steel, 1.75, 2.05, 1.75, 2.05, H_tower, 9.95)
    bmesh.ops.recalc_face_normals(bm_steel, faces=bm_steel.faces)
    m_st = bpy.data.meshes.new("Mesh_Totem_Acero")
    bm_steel.to_mesh(m_st)
    bm_steel.free()
    obj_steel = bpy.data.objects.new("BBVA_Totem_Poste_Central", m_st)
    col.objects.link(obj_steel)
    obj_steel.data.materials.append(mats["acero"])
    
    # Caja de luz: panel superior azul cobalto 2009 (rotado 45º para quedar paralelo a Cárdenas, Comentario 7)
    add_box(bm_blue, -1.80, 1.80, -0.16, 0.16, 10.65, 12.30)
    bmesh.ops.recalc_face_normals(bm_blue, faces=bm_blue.faces)
    m_b = bpy.data.meshes.new("Mesh_Totem_Azul")
    bm_blue.to_mesh(m_b)
    bm_blue.free()
    obj_blue = bpy.data.objects.new("BBVA_Totem_Panel_Azul", m_b)
    col.objects.link(obj_blue)
    obj_blue.location = (1.90, 1.90, 0.0)
    obj_blue.rotation_euler = (0.0, 0.0, math.radians(-90.0))
    obj_blue.data.materials.append(mats["fascia"])

    # Recuadro blanco BBVA 2009 centrado en la parte superior (sobresale a ambas caras Este y Oeste)
    add_box(bm_white_sq, -0.70, 0.70, -0.17, 0.17, 11.50, 12.20)
    bmesh.ops.recalc_face_normals(bm_white_sq, faces=bm_white_sq.faces)
    m_wsq = bpy.data.meshes.new("Mesh_Totem_Recuadro_Blanco")
    bm_white_sq.to_mesh(m_wsq)
    bm_white_sq.free()
    obj_wsq = bpy.data.objects.new("BBVA_Totem_Recuadro_BBVA", m_wsq)
    col.objects.link(obj_wsq)
    obj_wsq.location = (1.90, 1.90, 0.0)
    obj_wsq.rotation_euler = (0.0, 0.0, math.radians(-90.0))
    obj_wsq.data.materials.append(mats["rotulo_blanco"])

    # Panel inferior blanco (Cajero Automático / RED)
    add_box(bm_white_panel, -1.80, 1.80, -0.16, 0.16, 9.50, 10.65)
    bmesh.ops.recalc_face_normals(bm_white_panel, faces=bm_white_panel.faces)
    m_w = bpy.data.meshes.new("Mesh_Totem_Blanco")
    bm_white_panel.to_mesh(m_w)
    bm_white_panel.free()
    obj_white = bpy.data.objects.new("BBVA_Totem_Panel_Blanco", m_w)
    col.objects.link(obj_white)
    obj_white.location = (1.90, 1.90, 0.0)
    obj_white.rotation_euler = (0.0, 0.0, math.radians(-90.0))
    obj_white.data.materials.append(mats["rotulo_blanco"])

    # --- Cara Oeste (mirando hacia Cárdenas, normal hacia -X) ---
    x_t_w = 1.90 - 0.18
    y_t = 1.90
    rot_totem_txt_w = (math.radians(90.0), 0.0, math.radians(-90.0))
    
    # 1. Letras azules 'BBVA' dentro del recuadro blanco Oeste
    f_b1_w = bpy.data.curves.new(type="FONT", name="Font_T_BBVA_West")
    f_b1_w.body = "BBVA"
    f_b1_w.size = 0.40
    f_b1_w.extrude = 0.02
    f_b1_w.align_x = 'CENTER'
    o_b1_w = bpy.data.objects.new("Totem_Txt_BBVA_Azul_West", f_b1_w)
    col.objects.link(o_b1_w)
    o_b1_w.location = (x_t_w - 0.015, y_t, 11.65)
    o_b1_w.rotation_euler = rot_totem_txt_w
    o_b1_w.data.materials.append(mats["bbva_azul"])

    # 2. Texto blanco 'Bancomer' debajo del recuadro Oeste
    f_b2_w = bpy.data.curves.new(type="FONT", name="Font_T_Bancomer_West")
    f_b2_w.body = "Bancomer"
    f_b2_w.size = 0.36
    f_b2_w.extrude = 0.02
    f_b2_w.align_x = 'CENTER'
    o_b2_w = bpy.data.objects.new("Totem_Txt_Bancomer_Blanco_West", f_b2_w)
    col.objects.link(o_b2_w)
    o_b2_w.location = (x_t_w, y_t, 10.90)
    o_b2_w.rotation_euler = rot_totem_txt_w
    o_b2_w.data.materials.append(mats["rotulo_blanco"])

    # 3. Logotipo 'RED' a la izquierda del panel inferior (mirando hacia +X, izquierda es +Y)
    f_red_w = bpy.data.curves.new(type="FONT", name="Font_T_RED_West")
    f_red_w.body = "RED"
    f_red_w.size = 0.24
    f_red_w.extrude = 0.015
    f_red_w.align_x = 'CENTER'
    o_red_w = bpy.data.objects.new("Totem_Txt_RED_West", f_red_w)
    col.objects.link(o_red_w)
    o_red_w.location = (x_t_w, y_t + 0.85, 10.00)
    o_red_w.rotation_euler = rot_totem_txt_w
    o_red_w.data.materials.append(mats["red_logo"])

    # 4. Texto verde 'CAJERO AUTOMATICO' a la derecha (derecha es -Y)
    f_b3_w = bpy.data.curves.new(type="FONT", name="Font_T_ATM_West")
    f_b3_w.body = "CAJERO\nAUTOMATICO"
    f_b3_w.size = 0.18
    f_b3_w.extrude = 0.015
    f_b3_w.align_x = 'CENTER'
    o_b3_w = bpy.data.objects.new("Totem_Txt_ATM_Verde_West", f_b3_w)
    col.objects.link(o_b3_w)
    o_b3_w.location = (x_t_w, y_t - 0.55, 10.20)
    o_b3_w.rotation_euler = rot_totem_txt_w
    o_b3_w.data.materials.append(mats["cajero_verde"])

    # --- Cara Este (mirando hacia el estacionamiento, normal hacia +X) ---
    x_t_e = 1.90 + 0.18
    rot_totem_txt_e = (math.radians(90.0), 0.0, math.radians(90.0))

    # 5. Letras azules 'BBVA' dentro del recuadro blanco Este
    f_b1_e = bpy.data.curves.new(type="FONT", name="Font_T_BBVA_East")
    f_b1_e.body = "BBVA"
    f_b1_e.size = 0.40
    f_b1_e.extrude = 0.02
    f_b1_e.align_x = 'CENTER'
    o_b1_e = bpy.data.objects.new("Totem_Txt_BBVA_Azul_East", f_b1_e)
    col.objects.link(o_b1_e)
    o_b1_e.location = (x_t_e + 0.015, y_t, 11.65)
    o_b1_e.rotation_euler = rot_totem_txt_e
    o_b1_e.data.materials.append(mats["bbva_azul"])

    # 6. Texto blanco 'Bancomer' debajo del recuadro Este
    f_b2_e = bpy.data.curves.new(type="FONT", name="Font_T_Bancomer_East")
    f_b2_e.body = "Bancomer"
    f_b2_e.size = 0.36
    f_b2_e.extrude = 0.02
    f_b2_e.align_x = 'CENTER'
    o_b2_e = bpy.data.objects.new("Totem_Txt_Bancomer_Blanco_East", f_b2_e)
    col.objects.link(o_b2_e)
    o_b2_e.location = (x_t_e, y_t, 10.90)
    o_b2_e.rotation_euler = rot_totem_txt_e
    o_b2_e.data.materials.append(mats["rotulo_blanco"])

    # 7. Logotipo 'RED' a la izquierda del panel inferior Este (mirando desde el oriente hacia -X, izquierda es -Y)
    f_red_e = bpy.data.curves.new(type="FONT", name="Font_T_RED_East")
    f_red_e.body = "RED"
    f_red_e.size = 0.24
    f_red_e.extrude = 0.015
    f_red_e.align_x = 'CENTER'
    o_red_e = bpy.data.objects.new("Totem_Txt_RED_East", f_red_e)
    col.objects.link(o_red_e)
    o_red_e.location = (x_t_e, y_t - 0.85, 10.00)
    o_red_e.rotation_euler = rot_totem_txt_e
    o_red_e.data.materials.append(mats["red_logo"])

    # 8. Texto verde 'CAJERO AUTOMATICO' a la derecha del panel inferior Este (derecha es +Y)
    f_b3_e = bpy.data.curves.new(type="FONT", name="Font_T_ATM_East")
    f_b3_e.body = "CAJERO\nAUTOMATICO"
    f_b3_e.size = 0.18
    f_b3_e.extrude = 0.015
    f_b3_e.align_x = 'CENTER'
    o_b3_e = bpy.data.objects.new("Totem_Txt_ATM_Verde_East", f_b3_e)
    col.objects.link(o_b3_e)
    o_b3_e.location = (x_t_e, y_t + 0.55, 10.20)
    o_b3_e.rotation_euler = rot_totem_txt_e
    o_b3_e.data.materials.append(mats["cajero_verde"])

    totem_texts = [o_b1_w, o_b2_w, o_red_w, o_b3_w, o_b1_e, o_b2_e, o_red_e, o_b3_e]
    return obj_tower, obj_glass, [obj_steel, obj_blue, obj_wsq, obj_white], texts_guaj, totem_texts

def build_south_facade_juarez(mats, col):
    """Construye la Fachada Sur (Av. Benito Juárez) con 4 vanos exactos, rótulos de despachos y fascia 2009."""
    bm_struct = bmesh.new()
    bm_alum = bmesh.new()
    bm_glass = bmesh.new()
    bm_blind = bmesh.new()
    
    X_start = 4.20
    X_end = 22.80
    H_wall = 7.10
    
    # 1. Plinto basal (Z = 0.0 a 0.40)
    add_box(bm_struct, X_start, X_end, -0.05, 0.40, 0.0, 0.40)
    
    # 2. Machones / Pilastras verticales
    col_x = [4.20, 8.60, 13.00, 17.40]
    for cx in col_x:
        add_box(bm_struct, cx, cx + 0.60, -0.04, 0.35, 0.40, H_wall)
        
    # Muros horizontales rehundidos (rematan en X = 21.80 donde inicia el machón oriental)
    add_box(bm_struct, X_start, 21.80, 0.02, 0.30, 3.20, 3.30)
    # Dintel blanco de Crujía 4 en Av. Juárez (sección de fascia que no lleva alucobond azul en 2009 según media_1789774756138)
    add_box(bm_struct, 17.40, 21.80, -0.14, 0.30, 3.20, 4.30)
    add_box(bm_struct, X_start, 21.80, 0.02, 0.30, 4.30, 5.10)
    add_box(bm_struct, X_start, 21.80, 0.02, 0.30, 6.75, H_wall)
    
    # Machón sólido oriental de remate (X = 21.80 a 22.80)
    add_box(bm_struct, 21.80, 22.80, -0.04, 0.40, 0.40, H_wall)
    
    # Cornisa corrida blanca
    add_box(bm_struct, X_start, X_end + 0.20, -0.20, 0.40, 7.10, 7.25)
    add_box(bm_struct, X_start, X_end + 0.40, -0.40, 0.85, 7.25, 7.45)
    
    # 3. Cancelería de 4 crujías en Av. Juárez
    bays = [
        (4.80, 8.60),   # Crujía 1 (2 hojas anchas)
        (9.20, 13.00),  # Crujía 2 (3 hojas con montantes)
        (13.60, 17.40), # Crujía 3 (3 hojas con 'CASAS TERRENOS RANCHOS')
        (18.00, 21.80)  # Crujía 4 (4 hojas con 'JUAN VARGAS R')
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
        
    # Planta Alta (Z = 5.10 a 6.75) con montantes superiores
    for idx, (x1, x2) in enumerate(bays):
        w_f2 = 0.04
        add_box(bm_alum, x1, x1 + w_f2, 0.04, 0.10, 5.10, 6.75)
        add_box(bm_alum, x2 - w_f2, x2, 0.04, 0.10, 5.10, 6.75)
        add_box(bm_alum, x1, x2, 0.04, 0.10, 5.10, 5.10 + w_f2)
        add_box(bm_alum, x1, x2, 0.04, 0.10, 6.75 - w_f2, 6.75)
        add_box(bm_alum, x1, x2, 0.04, 0.10, 6.25, 6.25 + 0.03) # Montante horizontal
        
        n_divs = 2 if idx == 0 else (4 if idx == 3 else 3)
        step = (x2 - x1) / float(n_divs)
        for i in range(1, n_divs):
            mx = x1 + i * step
            add_box(bm_alum, mx - 0.02, mx + 0.02, 0.04, 0.10, 5.10, 6.75)
        add_box(bm_glass, x1 + w_f2, x2 - w_f2, 0.065, 0.075, 5.10 + w_f2, 6.75 - w_f2)

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

    # 4. Rótulos en vidrios de despachos (Ground Truth media_1789774756138)
    f_d1 = bpy.data.curves.new(type="FONT", name="Font_J_Despacho1")
    f_d1.body = "CASAS  TERRENOS  RANCHOS"
    f_d1.size = 0.16
    f_d1.extrude = 0.01
    f_d1.align_x = 'CENTER'
    o_d1 = bpy.data.objects.new("Juarez_Txt_Despacho1", f_d1)
    col.objects.link(o_d1)
    o_d1.location = (15.50, 0.055, 6.45)
    o_d1.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    o_d1.data.materials.append(mats["rotulo_blanco"])

    f_d2 = bpy.data.curves.new(type="FONT", name="Font_J_Despacho2")
    f_d2.body = "JUAN VARGAS R"
    f_d2.size = 0.20
    f_d2.extrude = 0.01
    f_d2.align_x = 'CENTER'
    o_d2 = bpy.data.objects.new("Juarez_Txt_Despacho2", f_d2)
    col.objects.link(o_d2)
    o_d2.location = (19.80, 0.055, 6.42)
    o_d2.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    o_d2.data.materials.append(mats["rotulo_blanco"])

    # 5. Fascia azul cobalto 2009 con logotipo BBVA Bancomer
    # Termina en X = 17.40 antes de Crujía 4 (Crujía 4 tiene fascia blanca estucada según media_1789774756138)
    bm_fascia = bmesh.new()
    add_box(bm_fascia, X_start, 17.40, -0.14, 0.02, 3.20, 4.30)
    bmesh.ops.recalc_face_normals(bm_fascia, faces=bm_fascia.faces)
    m_fa = bpy.data.meshes.new("Mesh_Juarez_Fascia")
    bm_fascia.to_mesh(m_fa)
    bm_fascia.free()
    obj_fascia = bpy.data.objects.new("Juarez_Fascia_Azul_2009", m_fa)
    col.objects.link(obj_fascia)
    obj_fascia.data.materials.append(mats["fascia"])

    # Filetes blancos horizontales a izquierda y derecha
    bm_stripe = bmesh.new()
    add_box(bm_stripe, X_start + 0.40, 7.60, -0.148, -0.138, 3.72, 3.76)
    # Filete derecho inicia en X = 11.80 (27 cm a la derecha de 'Bancomer' que termina en 11.53) y termina en 17.20 (antes de X = 17.40)
    add_box(bm_stripe, 11.80, 17.20, -0.148, -0.138, 3.72, 3.76)
    bmesh.ops.recalc_face_normals(bm_stripe, faces=bm_stripe.faces)
    m_str = bpy.data.meshes.new("Mesh_Juarez_Stripe")
    bm_stripe.to_mesh(m_str)
    bm_stripe.free()
    obj_stripe = bpy.data.objects.new("Juarez_Fascia_Stripe", m_str)
    col.objects.link(obj_stripe)
    obj_stripe.data.materials.append(mats["rotulo_blanco"])

    # Recuadro blanco BBVA 2009
    bm_rec = bmesh.new()
    add_box(bm_rec, 7.80, 9.30, -0.148, -0.138, 3.35, 4.15)
    bmesh.ops.recalc_face_normals(bm_rec, faces=bm_rec.faces)
    m_rc = bpy.data.meshes.new("Mesh_Juarez_Recuadro_BBVA")
    bm_rec.to_mesh(m_rc)
    bm_rec.free()
    obj_rec = bpy.data.objects.new("Juarez_Recuadro_BBVA", m_rc)
    col.objects.link(obj_rec)
    obj_rec.data.materials.append(mats["rotulo_blanco"])

    # Letras azules BBVA dentro del recuadro
    f_bbva = bpy.data.curves.new(type="FONT", name="Font_J_BBVA")
    f_bbva.body = "BBVA"
    f_bbva.size = 0.44
    f_bbva.extrude = 0.015
    f_bbva.align_x = 'CENTER'
    o_bbva = bpy.data.objects.new("Juarez_Txt_BBVA", f_bbva)
    col.objects.link(o_bbva)
    o_bbva.location = (8.55, -0.155, 3.55)
    o_bbva.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    o_bbva.data.materials.append(mats["bbva_azul"])

    # Texto blanco 'Bancomer' a la derecha
    f_bancomer = bpy.data.curves.new(type="FONT", name="Font_J_Bancomer")
    f_bancomer.body = "Bancomer"
    f_bancomer.size = 0.48
    f_bancomer.extrude = 0.02
    o_bancomer = bpy.data.objects.new("Juarez_Txt_Bancomer", f_bancomer)
    col.objects.link(o_bancomer)
    o_bancomer.location = (9.55, -0.155, 3.52)
    o_bancomer.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    o_bancomer.data.materials.append(mats["rotulo_blanco"])

    # 6. Mansarda de Tejas Coloniales de Barro Terracota
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

    return obj_struct, obj_alum, obj_glass, obj_blind, [obj_fascia, obj_stripe, obj_rec, o_bbva, o_bancomer], [o_d1, o_d2], obj_tejas

def build_west_facade_cardenas(mats, col):
    """Construye la Fachada Oeste continua de 6 crujías hasta DENTISTA (longitud 30.00 m) según Ground Truth media_1789778253725 y media_1789778345732."""
    bm_struct = bmesh.new()
    bm_alum = bmesh.new()
    bm_glass = bmesh.new()
    bm_blind = bmesh.new()
    bm_corbels = bmesh.new()
    bm_dent_stair = bmesh.new()
    bm_dent_canopy = bmesh.new()
    bm_dent_mosaic = bmesh.new()
    
    Y_start = 4.20
    Y_end = 29.40   # 6 crujías de 4.20 m: 4.20 a 29.40 m
    Y_max = 30.00   # Con machón norte
    H_wall = 7.10
    
    # 1. Plinto basal continuo (Z = 0.0 a 0.40)
    # Excluye el vano de la escalera de Dentista en [25.80, 28.20]
    add_box(bm_struct, -0.05, 0.40, Y_start, 25.80, 0.0, 0.40)
    add_box(bm_struct, -0.05, 0.40, 28.20, Y_max, 0.0, 0.40)
    
    # 2. Machones / Pilastras verticales a lo largo de las 6 crujías
    # 7 machones: 6 delimitan las 5 crujías + machón 7 de remate norte
    col_y = [4.20, 8.40, 12.60, 16.80, 21.00, 25.20]
    for cy in col_y:
        add_box(bm_struct, -0.04, 0.35, cy, cy + 0.60, 0.40, H_wall)
        
    # Machón norte de remate (Y = 29.40 a 30.00): Recubierto de mosaico vítreo oscuro (Ground Truth media_1789778345732)
    add_box(bm_dent_mosaic, -0.05, 0.40, 29.40, Y_max, 0.0, H_wall)
    
    # Muros rehundidos horizontales
    add_box(bm_struct, 0.02, 0.30, Y_start, Y_max, 3.20, 3.30)
    add_box(bm_struct, 0.02, 0.30, Y_start, Y_max, 4.30, 5.10)
    add_box(bm_struct, 0.02, 0.30, Y_start, Y_max, 6.75, H_wall)
    
    # Muro medianero norte que cierra el inmueble (Y = 30.00)
    add_box(bm_struct, -0.05, 16.0, Y_max, Y_max + 0.30, 0.0, H_wall)
    
    # Cornisa corrida blanca a lo largo de los 30 metros
    add_box(bm_struct, -0.20, 0.40, Y_start, Y_max + 0.20, 7.10, 7.25)
    add_box(bm_struct, -0.40, 0.85, Y_start, Y_max + 0.20, 7.25, 7.45)
    
    # 3. Ménsulas / Canecillos de concreto en voladizo (Corbels) en los 7 machones
    all_col_y = [4.20, 8.40, 12.60, 16.80, 21.00, 25.20, 29.40]
    for cy in all_col_y:
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

    # 4. Cancelería de las 6 crujías en Calle Cárdenas
    bays_y = [
        (4.80, 8.40),    # Crujía 1 (Banco Esquina)
        (9.00, 12.60),   # Crujía 2 (Banco con póster Bancomer)
        (13.20, 16.80),  # Crujía 3 (Banco Centro-Norte / Despacho Contable)
        (17.40, 21.00),  # Crujía 4 (Banco Norte con Acceso a Cajero Automático)
        (21.60, 25.20),  # Crujía 5 (Oficinas Dentista con fascia gris)
        (25.80, 29.40)   # Crujía 6 (Acceso DENTISTA con zaguán, escalera y marquesina)
    ]
    
    # Objetos y elementos de rotulación a compilar
    text_objs = []
    
    for idx, (y1, y2) in enumerate(bays_y):
        w_f = 0.05
        # Planta Baja
        if idx == 2:
            # Crujía 3: PORTAL DE ACCESO A CAJERO AUTOMÁTICO (Ground Truth media_1789778253725)
            # "Estos elementos van 1 ventanal a la derecha. Entre el cajero y el dentista hay 2 ventanales. El cajero va en el lado izquierdo de su ventanal."
            # Puerta acristalada en el lado izquierdo (norte) del vano: y in [15.20, 16.60]
            add_box(bm_alum, 0.04, 0.14, 15.20, 16.60, 0.40, 0.46)
            add_box(bm_alum, 0.04, 0.14, 15.20, 16.60, 2.70, 2.76)
            add_box(bm_alum, 0.04, 0.14, 15.20, 15.26, 0.40, 2.76)
            add_box(bm_alum, 0.04, 0.14, 16.54, 16.60, 0.40, 2.76)
            add_box(bm_glass, 0.08, 0.09, 15.26, 16.54, 0.46, 2.70)
            # Jaladera tubular de la puerta
            add_box(bm_alum, -0.02, 0.06, 15.32, 15.36, 1.00, 1.40)
            
            # Ventana lateral con persianas en el resto del vano: y in [13.20, 15.10]
            add_box(bm_alum, 0.04, 0.12, 13.20, 15.10, 0.40, 0.45)
            add_box(bm_alum, 0.04, 0.12, 13.20, 15.10, 3.15, 3.20)
            add_box(bm_alum, 0.04, 0.12, 13.20, 13.25, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, 15.05, 15.10, 0.40, 3.20)
            add_box(bm_glass, 0.075, 0.085, 13.25, 15.05, 0.45, 3.15)
            add_box(bm_blind, 0.135, 0.145, 13.25, 15.05, 0.45, 3.15)
            
        elif idx == 5:
            # Crujía 6: ACCESO DENTISTA (Ground Truth media_1789778345732)
            # Zaguán rehundido hacia el interior (X = 0.0 a 3.20, Y = [25.80, 28.20])
            # Escalera de 4 peldaños de concreto
            stair_w = (25.85, 28.15)
            add_box(bm_dent_stair, 0.20, 3.20, stair_w[0], stair_w[1], 0.0, 0.18)
            add_box(bm_dent_stair, 0.60, 3.20, stair_w[0], stair_w[1], 0.18, 0.36)
            add_box(bm_dent_stair, 1.00, 3.20, stair_w[0], stair_w[1], 0.36, 0.54)
            add_box(bm_dent_stair, 1.40, 3.20, stair_w[0], stair_w[1], 0.54, 0.72)
            
            # Muros interiores del zaguán
            add_box(bm_dent_stair, 0.0, 3.20, 25.75, 25.85, 0.0, 3.20) # Muro sur zaguán
            add_box(bm_dent_stair, 0.0, 3.20, 28.15, 28.25, 0.0, 3.20) # Muro norte zaguán
            add_box(bm_dent_stair, 0.0, 3.20, 25.75, 28.25, 3.20, 3.30) # Techo falso zaguán
            
            # Puerta acristalada interior al fondo del zaguán (X = 3.15, Y = [26.40, 27.80])
            add_box(bm_alum, 3.12, 3.18, 26.40, 27.80, 0.72, 2.72)
            add_box(bm_glass, 3.14, 3.16, 26.46, 27.74, 0.78, 2.66)
            
            # Ventanal lateral exterior a la derecha del acceso: Y in [28.25, 29.35]
            add_box(bm_alum, 0.04, 0.12, 28.25, 29.35, 0.40, 0.45)
            add_box(bm_alum, 0.04, 0.12, 28.25, 29.35, 3.15, 3.20)
            add_box(bm_alum, 0.04, 0.12, 28.25, 28.30, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, 29.30, 29.35, 0.40, 3.20)
            add_box(bm_glass, 0.075, 0.085, 28.30, 29.30, 0.45, 3.15)
            add_box(bm_blind, 0.135, 0.145, 28.30, 29.30, 0.45, 3.15)
            
        else:
            # Crujías 1, 2, 4 y 5: Cristaleras estándar (se eliminó el recuadro blanco de Crujía 2 según Comentario 2)
            n_divs_pb = 2 if (idx == 3 or idx == 4) else 3
            add_box(bm_alum, 0.04, 0.12, y1, y1 + w_f, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, y2 - w_f, y2, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, y1, y2, 0.40, 0.40 + w_f)
            add_box(bm_alum, 0.04, 0.12, y1, y2, 3.20 - w_f, 3.20)
            step = (y2 - y1) / float(n_divs_pb)
            for d in range(1, n_divs_pb):
                mx_pb = y1 + d * step
                add_box(bm_alum, 0.04, 0.12, mx_pb - 0.025, mx_pb + 0.025, 0.40, 3.20)
            add_box(bm_glass, 0.075, 0.085, y1 + w_f, y2 - w_f, 0.40 + w_f, 3.20 - w_f)
            add_box(bm_blind, 0.135, 0.145, y1 + w_f, y2 - w_f, 0.42, 3.18)
        
        # Planta Alta (2 hojas amplias con montante horizontal en Z = 6.25)
        w_f2 = 0.04
        add_box(bm_alum, 0.04, 0.10, y1, y1 + w_f2, 5.10, 6.75)
        add_box(bm_alum, 0.04, 0.10, y2 - w_f2, y2, 5.10, 6.75)
        add_box(bm_alum, 0.04, 0.10, y1, y2, 5.10, 5.10 + w_f2)
        add_box(bm_alum, 0.04, 0.10, y1, y2, 6.75 - w_f2, 6.75)
        add_box(bm_alum, 0.04, 0.10, y1, y2, 6.25, 6.28) # Montante horizontal
        my = (y1 + y2) * 0.5
        add_box(bm_alum, 0.04, 0.10, my - 0.025, my + 0.025, 5.10, 6.75)
        add_box(bm_glass, 0.065, 0.075, y1 + w_f2, y2 - w_f2, 5.10 + w_f2, 6.75 - w_f2)
        add_box(bm_blind, 0.120, 0.130, y1 + w_f2, y2 - w_f2, 5.12, 6.73)

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

    # Machón norte con mosaico
    bmesh.ops.recalc_face_normals(bm_dent_mosaic, faces=bm_dent_mosaic.faces)
    m_dm = bpy.data.meshes.new("Mesh_Dentista_Columna_Mosaico")
    bm_dent_mosaic.to_mesh(m_dm)
    bm_dent_mosaic.free()
    obj_mosaic_col = bpy.data.objects.new("Dentista_Columna_Mosaico", m_dm)
    col.objects.link(obj_mosaic_col)
    obj_mosaic_col.data.materials.append(mats["mosaico_guajardo"])

    # Escalera y zaguán de Dentista
    bmesh.ops.recalc_face_normals(bm_dent_stair, faces=bm_dent_stair.faces)
    m_ds = bpy.data.meshes.new("Mesh_Dentista_Escalera")
    bm_dent_stair.to_mesh(m_ds)
    bm_dent_stair.free()
    obj_stair = bpy.data.objects.new("Dentista_Escalera_Zaguan", m_ds)
    col.objects.link(obj_stair)
    obj_stair.data.materials.append(mats["escalera_dentista"])
    obj_stair.data.materials.append(mats["interior_hall"])
    for p in m_ds.polygons:
        c_z = sum(m_ds.vertices[v].co.z for v in p.vertices) / len(p.vertices)
        if c_z < 0.75:
            p.material_index = 0 # Escalones
        else:
            p.material_index = 1 # Muros y techo zaguán

    # Cancelería
    bmesh.ops.recalc_face_normals(bm_alum, faces=bm_alum.faces)
    m_al_w = bpy.data.meshes.new("Mesh_Cardenas_Canceleria")
    bm_alum.to_mesh(m_al_w)
    bm_alum.free()
    obj_alum = bpy.data.objects.new("Cardenas_Canceleria", m_al_w)
    col.objects.link(obj_alum)
    obj_alum.data.materials.append(mats["aluminio"])

    # Vidrio
    bmesh.ops.recalc_face_normals(bm_glass, faces=bm_glass.faces)
    m_gl_w = bpy.data.meshes.new("Mesh_Cardenas_Vidrio")
    bm_glass.to_mesh(m_gl_w)
    bm_glass.free()
    obj_glass = bpy.data.objects.new("Cardenas_Vidrio", m_gl_w)
    col.objects.link(obj_glass)
    obj_glass.data.materials.append(mats["vidrio"])

    # Persianas
    bmesh.ops.recalc_face_normals(bm_blind, faces=bm_blind.faces)
    m_bl_w = bpy.data.meshes.new("Mesh_Cardenas_Persianas")
    bm_blind.to_mesh(m_bl_w)
    bm_blind.free()
    obj_blind = bpy.data.objects.new("Cardenas_Persianas", m_bl_w)
    col.objects.link(obj_blind)
    obj_blind.data.materials.append(mats["persianas"])

    # 5. Rótulos en vidrios de despachos (Ground Truth media_1789778253725)
    # Crujía 2: Despacho Contable Fiscal Lic. Ramón Quezada (Y in [9.00, 12.60])
    f_q2 = bpy.data.curves.new(type="FONT", name="Font_C_Quezada2")
    f_q2.body = "DESPACHO CONTABLE FISCAL\nLOCAL Nº 4\nLIC. RAMON QUEZADA LOPEZ\nABOGADO"
    f_q2.size = 0.13
    f_q2.extrude = 0.008
    f_q2.align_x = 'CENTER'
    o_q2 = bpy.data.objects.new("Cardenas_Txt_Despacho_Contable", f_q2)
    col.objects.link(o_q2)
    o_q2.location = (0.055, 10.80, 6.35)
    o_q2.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_q2.data.materials.append(mats["rotulo_blanco"])
    text_objs.append(o_q2)

    # Crujía 3: Despacho Jurídico Quezada (Y in [13.20, 16.80], sobre el cajero automático)
    f_q1 = bpy.data.curves.new(type="FONT", name="Font_C_Quezada1")
    f_q1.body = "DESPACHO JURIDICO\nQUEZADA Y ASOCIADOS\nTel. 52-22"
    f_q1.size = 0.15
    f_q1.extrude = 0.008
    f_q1.align_x = 'CENTER'
    o_q1 = bpy.data.objects.new("Cardenas_Txt_Despacho_Juridico", f_q1)
    col.objects.link(o_q1)
    o_q1.location = (0.055, 15.00, 6.35)
    o_q1.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_q1.data.materials.append(mats["rotulo_blanco"])
    text_objs.append(o_q1)

    # Crujía 6: Rótulo ABIERTO en ventana PA Dentista
    f_ab = bpy.data.curves.new(type="FONT", name="Font_C_Abierto")
    f_ab.body = "ABIERTO"
    f_ab.size = 0.12
    f_ab.extrude = 0.005
    f_ab.align_x = 'CENTER'
    o_ab = bpy.data.objects.new("Cardenas_Txt_Abierto", f_ab)
    col.objects.link(o_ab)
    o_ab.location = (0.055, 27.60, 6.20)
    o_ab.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_ab.data.materials.append(mats["rojo_letras"])
    text_objs.append(o_ab)

    # 6. Fascias: Azul Cobalto para Banco BBVA (Crujías 1 a 3, Y = 4.20 a 17.40) + Plateada para Crujías 4 y 5 (Y = 17.40 a 25.80)
    # Fascia Banco BBVA (Y = 4.20 a 17.40)
    bm_fascia_b = bmesh.new()
    add_box(bm_fascia_b, -0.14, 0.02, Y_start, 17.40, 3.20, 4.30)
    # Área azul sobre la fachada misma en Crujía 6 arriba del alero (Comentario 5: "DENTISTA va sobre la fachada del edificio mismo, arriba de donde empieza este ala. Esa área va del mismo azul.")
    add_box(bm_fascia_b, -0.14, 0.02, 25.75, 28.25, 3.25, 4.30)
    bmesh.ops.recalc_face_normals(bm_fascia_b, faces=bm_fascia_b.faces)
    m_fa_b = bpy.data.meshes.new("Mesh_Cardenas_Fascia_Banco")
    bm_fascia_b.to_mesh(m_fa_b)
    bm_fascia_b.free()
    obj_fascia_b = bpy.data.objects.new("Cardenas_Fascia_Azul_2009", m_fa_b)
    col.objects.link(obj_fascia_b)
    obj_fascia_b.data.materials.append(mats["fascia"])

    # Filetes blancos horizontales en fascia del banco
    bm_stripe_c = bmesh.new()
    # Filete sur (hacia Guajardo): desde 4.60 hasta 9.80 (Bancomer empieza en 10.07, margen de 0.27 m sin solapamiento)
    add_box(bm_stripe_c, -0.148, -0.138, 4.60, 9.80, 3.72, 3.76)
    # Filete norte (sobre cajero): desde 13.85 (BBVA recuadro termina en 13.60, margen de 0.25 m) hasta 17.20
    add_box(bm_stripe_c, -0.148, -0.138, 13.85, 17.20, 3.72, 3.76)
    bmesh.ops.recalc_face_normals(bm_stripe_c, faces=bm_stripe_c.faces)
    m_str_c = bpy.data.meshes.new("Mesh_Cardenas_Stripe")
    bm_stripe_c.to_mesh(m_str_c)
    bm_stripe_c.free()
    obj_stripe_c = bpy.data.objects.new("Cardenas_Fascia_Stripe", m_str_c)
    col.objects.link(obj_stripe_c)
    obj_stripe_c.data.materials.append(mats["rotulo_blanco"])

    # Recuadro blanco BBVA 2009 entre Crujías 2 y 3 (Y = 12.30 a 13.60)
    bm_rec_c = bmesh.new()
    add_box(bm_rec_c, -0.148, -0.138, 12.30, 13.60, 3.35, 4.15)
    bmesh.ops.recalc_face_normals(bm_rec_c, faces=bm_rec_c.faces)
    m_rc_c = bpy.data.meshes.new("Mesh_Cardenas_Recuadro_BBVA")
    bm_rec_c.to_mesh(m_rc_c)
    bm_rec_c.free()
    obj_rec_c = bpy.data.objects.new("Cardenas_Recuadro_BBVA", m_rc_c)
    col.objects.link(obj_rec_c)
    obj_rec_c.data.materials.append(mats["rotulo_blanco"])

    # Letras BBVA azules (centradas en el recuadro blanco Y = 12.95)
    f_bbva_c = bpy.data.curves.new(type="FONT", name="Font_C_BBVA")
    f_bbva_c.body = "BBVA"
    f_bbva_c.size = 0.44
    f_bbva_c.extrude = 0.015
    f_bbva_c.align_x = 'CENTER'
    o_bbva_c = bpy.data.objects.new("Cardenas_Txt_BBVA", f_bbva_c)
    col.objects.link(o_bbva_c)
    o_bbva_c.location = (-0.155, 12.95, 3.55)
    o_bbva_c.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_bbva_c.data.materials.append(mats["bbva_azul"])
    text_objs.append(o_bbva_c)

    # Texto blanco 'Bancomer' adyacente a BBVA (inicia en Y = 12.05, extiende hacia -Y hasta 10.07)
    f_bancomer_c = bpy.data.curves.new(type="FONT", name="Font_C_Bancomer")
    f_bancomer_c.body = "Bancomer"
    f_bancomer_c.size = 0.48
    f_bancomer_c.extrude = 0.02
    o_bancomer_c = bpy.data.objects.new("Cardenas_Txt_Bancomer", f_bancomer_c)
    col.objects.link(o_bancomer_c)
    o_bancomer_c.location = (-0.155, 12.05, 3.52)
    o_bancomer_c.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_bancomer_c.data.materials.append(mats["rotulo_blanco"])
    text_objs.append(o_bancomer_c)

    # Fascia Metálica Plateada para Crujías 4 y 5 de Despachos (Y = 17.40 a 25.80, 2 ventanales continuos)
    bm_fascia_s = bmesh.new()
    add_box(bm_fascia_s, -0.13, 0.02, 17.40, 25.80, 3.20, 4.30)
    bmesh.ops.recalc_face_normals(bm_fascia_s, faces=bm_fascia_s.faces)
    m_fa_s = bpy.data.meshes.new("Mesh_Cardenas_Fascia_Silver")
    bm_fascia_s.to_mesh(m_fa_s)
    bm_fascia_s.free()
    obj_fascia_s = bpy.data.objects.new("Cardenas_Fascia_Silver", m_fa_s)
    col.objects.link(obj_fascia_s)
    obj_fascia_s.data.materials.append(mats["fascia_silver"])

    # 7. Rótulo Luminoso de Acceso a Cajero Automático en Crujía 3 (lado izquierdo, Y = [15.20, 16.60])
    bm_atm = bmesh.new()
    add_box(bm_atm, -0.18, -0.02, 15.20, 16.60, 2.76, 3.16)
    # Cuadro rojo RED a la izquierda (en vista frontal desde el poniente, izquierda es +Y)
    add_box(bm_atm, -0.19, -0.18, 16.10, 16.55, 2.80, 3.12)
    bmesh.ops.recalc_face_normals(bm_atm, faces=bm_atm.faces)
    m_ab = bpy.data.meshes.new("Mesh_ATM_Portal_Box")
    bm_atm.to_mesh(m_ab)
    bm_atm.free()
    obj_atm_box = bpy.data.objects.new("Cardenas_ATM_Portal_Box", m_ab)
    col.objects.link(obj_atm_box)
    obj_atm_box.data.materials.append(mats["atm_caja"])
    obj_atm_box.data.materials.append(mats["red_logo"])
    for p in m_ab.polygons:
        c_y = sum(m_ab.vertices[v].co.y for v in p.vertices) / len(p.vertices)
        if c_y > 16.05:
            p.material_index = 1 # Cuadro rojo RED
        else:
            p.material_index = 0 # Caja azul marino

    f_atm_p = bpy.data.curves.new(type="FONT", name="Font_C_ATM_Portal")
    f_atm_p.body = "CAJERO\nAUTOMATICO"
    f_atm_p.size = 0.11
    f_atm_p.extrude = 0.01
    f_atm_p.align_x = 'CENTER'
    o_atm_p = bpy.data.objects.new("Cardenas_ATM_Portal_Txt", f_atm_p)
    col.objects.link(o_atm_p)
    o_atm_p.location = (-0.20, 15.65, 2.85)
    o_atm_p.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_atm_p.data.materials.append(mats["rotulo_blanco"])
    text_objs.append(o_atm_p)

    f_red_p = bpy.data.curves.new(type="FONT", name="Font_C_RED")
    f_red_p.body = "RED"
    f_red_p.size = 0.12
    f_red_p.extrude = 0.01
    f_red_p.align_x = 'CENTER'
    o_red_p = bpy.data.objects.new("Cardenas_RED_Txt", f_red_p)
    col.objects.link(o_red_p)
    o_red_p.location = (-0.20, 16.32, 2.92)
    o_red_p.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_red_p.data.materials.append(mats["rotulo_blanco"])
    text_objs.append(o_red_p)

    # 8. MARQUESINA Y ELEMENTOS DENTISTA EN CRUJÍA 6 (Ground Truth media_1789778345732)
    # Alero volado (tejadillo shelf horizontal saliente 1.15 m sobre la banqueta, centrado en X = -0.55)
    # X de -1.15 a 0.05, Y de 25.75 a 28.25, Z de 3.05 a 3.25
    add_box(bm_dent_canopy, -1.15, 0.05, 25.75, 28.25, 3.05, 3.25)
    
    # Rótulo colgante a 90º bajo la marquesina (centrado bajo el voladizo en X in [-1.05, -0.05], centro X = -0.55)
    # Se sitúa perpendicular a la fachada en Y = 26.05, Z in [2.35, 2.98]
    add_box(bm_dent_canopy, -1.05, -0.05, 26.03, 26.07, 2.35, 2.98)
    
    # Foco / Cámara de seguridad sobre esquina de marquesina
    add_box(bm_dent_canopy, -0.15, 0.05, 28.15, 28.35, 3.25, 3.55)
    add_box(bm_dent_canopy, -0.25, -0.10, 28.20, 28.30, 3.35, 3.45)

    bmesh.ops.recalc_face_normals(bm_dent_canopy, faces=bm_dent_canopy.faces)
    m_dcan = bpy.data.meshes.new("Mesh_Dentista_Canopy")
    bm_dent_canopy.to_mesh(m_dcan)
    bm_dent_canopy.free()
    obj_canopy = bpy.data.objects.new("Dentista_Marquesina_Volada", m_dcan)
    col.objects.link(obj_canopy)
    obj_canopy.data.materials.append(mats["letrero_dentista"])
    obj_canopy.data.materials.append(mats["rotulo_blanco"])
    obj_canopy.data.materials.append(mats["aluminio"])
    for p in m_dcan.polygons:
        c_x = sum(m_dcan.vertices[v].co.x for v in p.vertices) / len(p.vertices)
        c_z = sum(m_dcan.vertices[v].co.z for v in p.vertices) / len(p.vertices)
        if c_z < 3.00:
            p.material_index = 1 # Rótulo colgante blanco a 90º
        elif c_x > -0.20 and c_z > 3.25:
            p.material_index = 2 # Foco seguridad
        else:
            p.material_index = 0 # Alero azul marino

    # Comentario 5: "DENTISTA va sobre la fachada del edificio mismo, o sea, arriba de donde empieza este ala. Esa área va del mismo azul."
    # Letras 3D DENTISTA en oro montadas sobre la pared de fachada azul en X = -0.16, centradas en Y = 27.00, Z = 3.65
    f_d3d = bpy.data.curves.new(type="FONT", name="Font_C_Dentista_3D")
    f_d3d.body = "DENTISTA"
    f_d3d.size = 0.38
    f_d3d.extrude = 0.035
    f_d3d.align_x = 'CENTER'
    o_d3d = bpy.data.objects.new("Dentista_Txt_3D_Oro", f_d3d)
    col.objects.link(o_d3d)
    o_d3d.location = (-0.16, 27.00, 3.65)
    o_d3d.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    o_d3d.data.materials.append(mats["oro_letras"])
    text_objs.append(o_d3d)

    # Textos del rótulo colgante a 90º (centrado en X = -0.55 bajo el alero)
    # Cara Sur (mirando hacia -Y, para peatones que vienen de Av. Juárez):
    rot_hang_s = (math.radians(90.0), 0.0, 0.0)
    y_hang_s = 26.015
    h_labels_s = [
        ("Dr. Eduardo R. Álvarez Ocampo", 0.050, 2.84, mats["rojo_letras"]),
        ("DENTISTA", 0.085, 2.71, mats["letrero_dentista"]),
        ("LOCAL - 1    RX   Tel: 654-11-57", 0.045, 2.58, mats["zocalo"]),
        ("SE ACEPTAN ASEGURANZAS U.S.A.", 0.042, 2.48, mats["zocalo"]),
        ("ATENCION ESPECIAL A NIÑOS - ORTODONCIA", 0.035, 2.39, mats["zocalo"])
    ]
    for text_line, sz, z_pos, mat_t in h_labels_s:
        f_lbl = bpy.data.curves.new(type="FONT", name=f"Font_C_HS_{text_line[:6]}")
        f_lbl.body = text_line
        f_lbl.size = sz
        f_lbl.extrude = 0.005
        f_lbl.align_x = 'CENTER'
        o_lbl = bpy.data.objects.new(f"Dentista_Txt_S_{text_line[:6]}", f_lbl)
        col.objects.link(o_lbl)
        o_lbl.location = (-0.55, y_hang_s, z_pos)
        o_lbl.rotation_euler = rot_hang_s
        o_lbl.data.materials.append(mat_t)
        text_objs.append(o_lbl)

    # Cara Norte (mirando hacia +Y, para peatones que vienen de Calle 1ra):
    rot_hang_n = (math.radians(90.0), 0.0, math.radians(180.0))
    y_hang_n = 26.085
    for text_line, sz, z_pos, mat_t in h_labels_s:
        f_lbl_n = bpy.data.curves.new(type="FONT", name=f"Font_C_HN_{text_line[:6]}")
        f_lbl_n.body = text_line
        f_lbl_n.size = sz
        f_lbl_n.extrude = 0.005
        f_lbl_n.align_x = 'CENTER'
        o_lbl_n = bpy.data.objects.new(f"Dentista_Txt_N_{text_line[:6]}", f_lbl_n)
        col.objects.link(o_lbl_n)
        o_lbl_n.location = (-0.55, y_hang_n, z_pos)
        o_lbl_n.rotation_euler = rot_hang_n
        o_lbl_n.data.materials.append(mat_t)
        text_objs.append(o_lbl_n)

    # 9. Mansarda de Tejas a lo largo de toda la fachada continua (30.00 m)
    bm_tejas = bmesh.new()
    Z_start = 7.45
    Z_end = 8.15
    dx = 0.85 - (-0.42)
    dz = Z_end - Z_start
    L = math.hypot(dx, dz)
    nx = -dz / L
    nz = dx / L
    n_tejas_y = 58
    step_y = (Y_max - Y_start + 0.40) / float(n_tejas_y)
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
        vb = bm_tejas.verts.new((0.85 + dx_r, Y_max + 0.20, Z_end + dz_r))
        if s > 0:
            bm_tejas.faces.new((v_r_a, va, vb, v_r_b))
        v_r_a, v_r_b = va, vb

    # Base sólida
    v1 = bm_tejas.verts.new((-0.42, Y_start, Z_start))
    v2 = bm_tejas.verts.new((-0.42, Y_max + 0.20, Z_start))
    v3 = bm_tejas.verts.new((0.85, Y_max + 0.20, Z_end))
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

    fascia_group = [obj_fascia_b, obj_stripe_c, obj_rec_c, obj_fascia_s, obj_atm_box, obj_canopy, obj_mosaic_col, obj_stair]
    return obj_struct, obj_corbels, obj_alum, obj_glass, obj_blind, fascia_group, text_objs, obj_tejas

def build_east_facade_and_parking(mats, col):
    """Construye la Fachada Este y patio trasero de estacionamiento (Ground Truth media_1789778429624):
    Ventanales modulares PA, puertas de servicio PB, cuerpo semicilíndrico, casetas HVAC y muro perimetral con [E] BBVA."""
    bm_east = bmesh.new()
    bm_alum = bmesh.new()
    bm_glass = bmesh.new()
    bm_blind = bmesh.new()
    bm_hvac = bmesh.new()
    bm_curve = bmesh.new()
    
    X_east = 22.80
    Y_max = 30.00
    H_wall = 7.10
    
    # 1. Muro Este principal del cuerpo bancario (Z = 0.0 a 7.10, Y = 0.40 a 16.0 para no solapar con el machón sur)
    add_box(bm_east, X_east - 0.40, X_east, 0.40, 16.0, 0.0, 0.40) # Zócalo
    add_box(bm_east, X_east - 0.40, X_east, 0.40, 16.0, 3.20, 5.10) # Faja intermedia
    add_box(bm_east, X_east - 0.40, X_east, 0.40, 16.0, 6.75, H_wall) # Remate
    
    # Losa interior de azotea hermética
    add_box(bm_east, 4.20, X_east, 0.40, 16.0, 7.00, 7.25)
    add_box(bm_east, 0.40, 4.20, 4.20, 16.0, 7.00, 7.25)
    add_box(bm_east, 0.40, 16.0, 16.0, Y_max, 7.00, 7.25) # Azotea Ala Norte extendida a 30.00 m
    
    # Muro posterior este del Ala Norte (X = 15.60 a 16.0, Y = 16.0 a 30.00) (Ground Truth media_1789778429624)
    add_box(bm_east, 15.60, 16.0, 16.0, Y_max, 0.0, 0.40) # Zócalo
    add_box(bm_east, 15.60, 16.0, 16.0, Y_max, 3.20, 5.10) # Faja intermedia
    add_box(bm_east, 15.60, 16.0, 16.0, Y_max, 6.75, H_wall) # Remate
    
    # Ventanales de Planta Alta en la fachada trasera del Ala Norte (5 módulos horizontales)
    rear_bays = [
        (16.60, 18.60),
        (19.20, 21.20),
        (21.80, 23.80),
        (24.40, 26.40),
        (27.00, 29.00)
    ]
    for ry1, ry2 in rear_bays:
        add_box(bm_alum, 15.65, 15.95, ry1, ry2, 5.10, 5.15)
        add_box(bm_alum, 15.65, 15.95, ry1, ry2, 6.70, 6.75)
        add_box(bm_alum, 15.65, 15.95, ry1, ry1 + 0.04, 5.10, 6.75)
        add_box(bm_alum, 15.65, 15.95, ry2 - 0.04, ry2, 5.10, 6.75)
        m_ry = (ry1 + ry2) * 0.5
        add_box(bm_alum, 15.65, 15.95, m_ry - 0.02, m_ry + 0.02, 5.10, 6.75)
        add_box(bm_glass, 15.75, 15.85, ry1 + 0.04, ry2 - 0.04, 5.15, 6.70)
        
    # Planta Baja trasera: Puertas metálicas de servicio y ventanales tintados (Ground Truth media_1789778429624)
    # Ventanal 1
    add_box(bm_alum, 15.65, 15.95, 17.20, 19.40, 0.40, 3.20)
    add_box(bm_glass, 15.75, 15.85, 17.25, 19.35, 0.45, 3.15)
    # Puerta de servicio metálica grafito 1
    add_box(bm_alum, 15.65, 15.95, 20.20, 21.60, 0.0, 2.80)
    # Ventanal 2
    add_box(bm_alum, 15.65, 15.95, 22.40, 24.60, 0.40, 3.20)
    add_box(bm_glass, 15.75, 15.85, 22.45, 24.55, 0.45, 3.15)
    
    # 2. Ventanales de Planta Alta en Fachada Este (5 vanos según media_1789774721368 y media_1789781403754)
    e_bays = [
        (0.80, 3.40),
        (3.80, 6.40),
        (6.80, 9.40),
        (9.80, 12.40),
        (12.80, 15.20)
    ]
    
    # Machones entre ventanas en planta alta
    add_box(bm_east, X_east - 0.40, X_east, 0.40, 0.80, 5.10, 6.75)
    for i in range(len(e_bays) - 1):
        add_box(bm_east, X_east - 0.40, X_east, e_bays[i][1], e_bays[i+1][0], 5.10, 6.75)
    add_box(bm_east, X_east - 0.40, X_east, 15.20, 16.0, 5.10, 6.75)
    
    # Cancelería y vidrios en PA Este (3 hojas verticales y travesaño horizontal en Z = 6.25 según media_1789781403754)
    for y1, y2 in e_bays:
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y2, 5.10, 5.15)
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y2, 6.70, 6.75)
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y1 + 0.04, 5.10, 6.75)
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, y2 - 0.04, y2, 5.10, 6.75)
        # Travesaño horizontal en tercio superior
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y2, 6.25, 6.28)
        # 2 montantes verticales dividiendo en 3 hojas
        step_e = (y2 - y1) / 3.0
        m1 = y1 + step_e
        m2 = y1 + 2.0 * step_e
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, m1 - 0.02, m1 + 0.02, 5.10, 6.75)
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, m2 - 0.02, m2 + 0.02, 5.10, 6.75)
        add_box(bm_glass, X_east - 0.07, X_east - 0.05, y1 + 0.04, y2 - 0.04, 5.15, 6.70)
        
    # 3. Planta Baja Este: Pilastras continuas alineadas con PA, ventanales con persianas, puerta y luminarias (media_1789781403754)
    # Pilastras de PB (alineadas exactamente con las de PA)
    add_box(bm_east, X_east - 0.40, X_east, 0.40, 0.80, 0.40, 3.20)
    for i in range(len(e_bays) - 1):
        add_box(bm_east, X_east - 0.40, X_east, e_bays[i][1], e_bays[i+1][0], 0.40, 3.20)
    add_box(bm_east, X_east - 0.40, X_east, 15.20, 16.0, 0.40, 3.20)
    
    # Ventanales y puerta en PB
    for idx_pb, (y1, y2) in enumerate(e_bays):
        if idx_pb == 2:
            # Crujía 3: Puerta peatonal con marco y montante de vidrio (media_1789781403754)
            add_box(bm_east, X_east - 0.40, X_east, y1, y2, 3.15, 3.20)
            door_y1 = y1 + 0.25
            door_y2 = y2 - 0.25
            add_box(bm_east, X_east - 0.40, X_east, y1, door_y1, 0.40, 3.20)
            add_box(bm_east, X_east - 0.40, X_east, door_y2, y2, 0.40, 3.20)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, door_y1, door_y2, 0.40, 0.45)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, door_y1, door_y2, 2.55, 2.60)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, door_y1, door_y2, 3.10, 3.15)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, door_y1, door_y1 + 0.04, 0.40, 3.15)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, door_y2 - 0.04, door_y2, 0.40, 3.15)
            add_box(bm_glass, X_east - 0.07, X_east - 0.05, door_y1 + 0.04, door_y2 - 0.04, 0.45, 2.55)
            add_box(bm_glass, X_east - 0.07, X_east - 0.05, door_y1 + 0.04, door_y2 - 0.04, 2.60, 3.10)
        else:
            # Ventanales comerciales con montante central y persianas verticales
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y2, 0.40, 0.45)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y2, 3.15, 3.20)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y1 + 0.04, 0.40, 3.20)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, y2 - 0.04, y2, 0.40, 3.20)
            my_pb = (y1 + y2) * 0.5
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, my_pb - 0.025, my_pb + 0.025, 0.40, 3.20)
            add_box(bm_glass, X_east - 0.07, X_east - 0.05, y1 + 0.04, y2 - 0.04, 0.45, 3.15)
            add_box(bm_blind, X_east - 0.14, X_east - 0.13, y1 + 0.04, y2 - 0.04, 0.45, 3.15)

    # Luminarias tipo aplique / sconce exterior sobre los machones de PB (Ground Truth media_1789781403754)
    for y_lamp in [3.60, 6.60, 9.60, 12.60]:
        add_box(bm_alum, X_east - 0.02, X_east + 0.10, y_lamp - 0.03, y_lamp + 0.03, 2.68, 2.72)
        add_box(bm_alum, X_east + 0.08, X_east + 0.22, y_lamp - 0.06, y_lamp + 0.06, 2.58, 2.78)

    # 4. Cuerpo arquitectónico semicilíndrico trasero (núcleo de escalera) (Ground Truth media_1789778429624)
    # Ubicado en la esquina noreste interior: centro (16.0, 27.50), radio 2.20 m
    cx_cyl, cy_cyl = 16.0, 27.50
    r_cyl = 2.20
    n_cyl_segs = 12
    v_prev_bot, v_prev_top = None, None
    for s in range(n_cyl_segs + 1):
        ang = -0.5 * math.pi + math.pi * (s / float(n_cyl_segs)) # Semicírculo hacia +X
        px = cx_cyl + r_cyl * math.cos(ang)
        py = cy_cyl + r_cyl * math.sin(ang)
        v_b = bm_curve.verts.new((px, py, 0.0))
        v_t = bm_curve.verts.new((px, py, H_wall))
        if s > 0:
            bm_curve.faces.new((v_prev_bot, v_b, v_t, v_prev_top))
        v_prev_bot, v_prev_top = v_b, v_t

    # Losa superior del semicilindro
    v_center_top = bm_curve.verts.new((cx_cyl, cy_cyl, H_wall))
    # Cerrar techo
    v_prev = None
    for s in range(n_cyl_segs + 1):
        ang = -0.5 * math.pi + math.pi * (s / float(n_cyl_segs))
        px = cx_cyl + r_cyl * math.cos(ang)
        py = cy_cyl + r_cyl * math.sin(ang)
        vt = bm_curve.verts.new((px, py, H_wall))
        if s > 0:
            bm_curve.faces.new((v_center_top, v_prev, vt))
        v_prev = vt

    bmesh.ops.recalc_face_normals(bm_curve, faces=bm_curve.faces)
    for f in bm_curve.faces:
        f.smooth = True
    m_crv = bpy.data.meshes.new("Mesh_Rear_Cylinder")
    bm_curve.to_mesh(m_crv)
    bm_curve.free()
    obj_curve = bpy.data.objects.new("Rear_Staircase_Cylinder", m_crv)
    col.objects.link(obj_curve)
    obj_curve.data.materials.append(mats["muro"])

    # 5. Casetas HVAC y Equipos Técnicos en Azotea (Ground Truth media_1789778429624)
    # Caseta de elevador / extracción
    add_box(bm_hvac, 7.00, 11.50, 18.00, 22.50, 7.15, 8.65)
    # Equipos de aire acondicionado exteriores
    add_box(bm_hvac, 8.50, 10.50, 12.00, 14.50, 7.15, 8.10)
    add_box(bm_hvac, 11.00, 13.00, 12.00, 14.50, 7.15, 8.10)

    bmesh.ops.recalc_face_normals(bm_hvac, faces=bm_hvac.faces)
    m_hv = bpy.data.meshes.new("Mesh_Roof_HVAC")
    bm_hvac.to_mesh(m_hv)
    bm_hvac.free()
    obj_hvac = bpy.data.objects.new("Roof_HVAC_Units", m_hv)
    col.objects.link(obj_hvac)
    obj_hvac.data.materials.append(mats["acero"])

    # Convertir muro este a objeto
    bmesh.ops.recalc_face_normals(bm_east, faces=bm_east.faces)
    m_east = bpy.data.meshes.new("Mesh_East_Wall")
    bm_east.to_mesh(m_east)
    bm_east.free()
    obj_east = bpy.data.objects.new("East_Parking_Estructura", m_east)
    col.objects.link(obj_east)
    obj_east.data.materials.append(mats["muro"])
    obj_east.data.materials.append(mats["zocalo"])
    obj_east.data.materials.append(mats["azotea"])
    for p in m_east.polygons:
        c_z = sum(m_east.vertices[v].co.z for v in p.vertices) / len(p.vertices)
        if c_z > 7.05:
            p.material_index = 2
        elif c_z < 0.42:
            p.material_index = 1
        else:
            p.material_index = 0

    # Convertir cancelería y vidrios este
    bmesh.ops.recalc_face_normals(bm_alum, faces=bm_alum.faces)
    m_al_e = bpy.data.meshes.new("Mesh_East_Canceleria")
    bm_alum.to_mesh(m_al_e)
    bm_alum.free()
    obj_al_e = bpy.data.objects.new("East_Canceleria", m_al_e)
    col.objects.link(obj_al_e)
    obj_al_e.data.materials.append(mats["aluminio"])

    bmesh.ops.recalc_face_normals(bm_glass, faces=bm_glass.faces)
    m_gl_e = bpy.data.meshes.new("Mesh_East_Vidrio")
    bm_glass.to_mesh(m_gl_e)
    bm_glass.free()
    obj_gl_e = bpy.data.objects.new("East_Vidrio", m_gl_e)
    col.objects.link(obj_gl_e)
    obj_gl_e.data.materials.append(mats["vidrio"])

    bmesh.ops.recalc_face_normals(bm_blind, faces=bm_blind.faces)
    m_bl_e = bpy.data.meshes.new("Mesh_East_Persianas")
    bm_blind.to_mesh(m_bl_e)
    bm_blind.free()
    obj_bl_e = bpy.data.objects.new("East_Persianas", m_bl_e)
    col.objects.link(obj_bl_e)
    obj_bl_e.data.materials.append(mats["persianas"])

    # Rótulo de despacho en PA ventana 1 ('LICENCIADO EN DERECHO', Ground Truth media_1789781403754)
    # Ubicado en la Crujía 1 (Y in [0.80, 3.40]), hoja izquierda superior
    f_ed = bpy.data.curves.new(type="FONT", name="Font_E_Despacho")
    f_ed.body = "LICENCIADO EN DERECHO"
    f_ed.size = 0.10
    f_ed.extrude = 0.006
    f_ed.align_x = 'CENTER'
    o_ed = bpy.data.objects.new("East_Txt_Despacho", f_ed)
    col.objects.link(o_ed)
    o_ed.location = (X_east + 0.02, 1.65, 6.42)
    o_ed.rotation_euler = (math.radians(90.0), 0.0, math.radians(90.0))
    o_ed.data.materials.append(mats["rotulo_blanco"])

    # 6. Elementos del Estacionamiento: Suelo, Cajones, Bolardos, Rampa, Caseta y Muro Perimetral
    # Rampa descendente
    bm_ramp = bmesh.new()
    add_box(bm_ramp, X_east + 0.60, X_east + 4.50, 0.0, 14.0, -0.45, 0.05)
    rx = X_east + 4.55
    add_box(bm_ramp, rx - 0.15, rx, 0.0, 14.0, 0.0, 0.90) # Murete
    bmesh.ops.recalc_face_normals(bm_ramp, faces=bm_ramp.faces)
    m_rp = bpy.data.meshes.new("Mesh_Rampa_Suelo")
    bm_ramp.to_mesh(m_rp)
    bm_ramp.free()
    obj_ramp = bpy.data.objects.new("Rampa_Estacionamiento", m_rp)
    col.objects.link(obj_ramp)
    obj_ramp.data.materials.append(mats["zocalo"])

    # Barandilla de acero blanco
    bm_rail = bmesh.new()
    add_box(bm_rail, rx - 0.09, rx - 0.06, 0.0, 14.0, 1.65, 1.70)
    add_box(bm_rail, rx - 0.08, rx - 0.07, 0.0, 14.0, 1.25, 1.28)
    for py in [0.4, 3.4, 6.4, 9.4, 12.4, 13.9]:
        add_box(bm_rail, rx - 0.10, rx - 0.05, py - 0.03, py + 0.03, 0.90, 1.65)
    bmesh.ops.recalc_face_normals(bm_rail, faces=bm_rail.faces)
    m_rl = bpy.data.meshes.new("Mesh_Rampa_Barandal")
    bm_rail.to_mesh(m_rl)
    bm_rail.free()
    obj_rail = bpy.data.objects.new("Rampa_Barandal_Blanco", m_rl)
    col.objects.link(obj_rail)
    obj_rail.data.materials.append(mats["barandal"])

    # Caseta de vigilancia blanca
    bm_caseta = bmesh.new()
    add_box(bm_caseta, X_east + 4.80, X_east + 7.00, 6.0, 8.8, 0.0, 2.70)
    add_box(bm_caseta, X_east + 4.65, X_east + 7.15, 5.85, 8.95, 2.70, 2.85) # Tejadillo
    bmesh.ops.recalc_face_normals(bm_caseta, faces=bm_caseta.faces)
    m_cs = bpy.data.meshes.new("Mesh_Caseta_Blanca")
    bm_caseta.to_mesh(m_cs)
    bm_caseta.free()
    obj_caseta = bpy.data.objects.new("Caseta_Vigilancia_Blanca", m_cs)
    col.objects.link(obj_caseta)
    obj_caseta.data.materials.append(mats["muro"])

    # Muro perimetral del estacionamiento con portón de servicio (Ground Truth media_1789778429624)
    bm_pwall = bmesh.new()
    # Muro blanco este con reja
    add_box(bm_pwall, X_east + 7.20, X_east + 12.50, 5.80, 6.05, 0.0, 2.40)
    # Placa azul en el muro: [E] BBVA ESTACIONAMIENTO EXCLUSIVO
    add_box(bm_pwall, X_east + 8.20, X_east + 9.80, 5.75, 5.82, 1.40, 1.95)
    
    # Bolardos y topes amarillos en el pavimento del estacionamiento
    for by in [17.50, 20.00, 22.50, 25.00]:
        add_box(bm_pwall, 17.50, 17.65, by, by + 1.80, 0.0, 0.12) # Tope de llantas
        add_box(bm_pwall, 17.10, 17.20, by + 0.90, by + 1.00, 0.0, 0.85) # Bolardo vertical
        
    bmesh.ops.recalc_face_normals(bm_pwall, faces=bm_pwall.faces)
    m_pw = bpy.data.meshes.new("Mesh_Parking_Wall")
    bm_pwall.to_mesh(m_pw)
    bm_pwall.free()
    obj_pwall = bpy.data.objects.new("Parking_Perimeter_Wall", m_pw)
    col.objects.link(obj_pwall)
    obj_pwall.data.materials.append(mats["muro"])
    obj_pwall.data.materials.append(mats["senal_azul"])
    obj_pwall.data.materials.append(mats["bolardo_amarillo"])
    for p in m_pw.polygons:
        c_x = sum(m_pw.vertices[v].co.x for v in p.vertices) / len(p.vertices)
        c_y = sum(m_pw.vertices[v].co.y for v in p.vertices) / len(p.vertices)
        if c_x < 18.0:
            p.material_index = 2 # Bolardos amarillos
        elif c_y < 5.85 and c_x > X_east + 8.0:
            p.material_index = 1 # Placa azul BBVA
        else:
            p.material_index = 0

    # Letrero oficial 'ENTRADA BBVA ->' ortogonal hacia Av. Juárez
    bm_sign = bmesh.new()
    sx = X_east + 5.90
    sy = 3.50
    add_box(bm_sign, sx - 0.04, sx + 0.04, sy - 0.04, sy + 0.04, 0.0, 2.20)
    add_box(bm_sign, sx - 0.60, sx + 0.60, sy - 0.03, sy + 0.03, 1.70, 2.30)
    bmesh.ops.recalc_face_normals(bm_sign, faces=bm_sign.faces)
    m_sn = bpy.data.meshes.new("Mesh_Senal_Entrada_Ortogonal")
    bm_sign.to_mesh(m_sn)
    bm_sign.free()
    obj_sign = bpy.data.objects.new("Senal_Entrada_BBVA_Ortogonal", m_sn)
    col.objects.link(obj_sign)
    obj_sign.data.materials.append(mats["senal_azul"])

    f_sign = bpy.data.curves.new(type="FONT", name="Font_Senal_Rampa_Ort")
    f_sign.body = "ENTRADA\nBBVA ➔"
    f_sign.size = 0.16
    f_sign.extrude = 0.01
    f_sign.align_x = 'CENTER'
    o_sign = bpy.data.objects.new("Texto_Senal_Rampa_Ort", f_sign)
    col.objects.link(o_sign)
    o_sign.location = (sx, sy - 0.04, 2.10)
    o_sign.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    o_sign.data.materials.append(mats["rotulo_blanco"])

    return obj_east, [obj_al_e, obj_gl_e, obj_bl_e, o_ed, obj_curve, obj_hvac, obj_pwall], obj_ramp, obj_rail, obj_caseta, obj_sign, o_sign

def build_optional_sidewalk(mats, col):
    """Crea la banqueta urbana como un asset modular independiente (NO incluido en el glb del edificio)."""
    bm_sw = bmesh.new()
    X_east = 22.80
    Y_cardenas = 30.00
    
    # Banqueta perimetral
    add_box(bm_sw, -3.80, X_east + 8.00, -3.80, 0.0, 0.0, 0.18)
    add_box(bm_sw, -3.80, 0.0, 0.0, Y_cardenas + 2.00, 0.0, 0.18)
    # Cordón rojo
    add_box(bm_sw, -3.88, X_east + 8.00, -3.88, -3.76, 0.0, 0.20)
    add_box(bm_sw, -3.88, -3.76, -3.88, Y_cardenas + 2.00, 0.0, 0.20)
    
    bmesh.ops.recalc_face_normals(bm_sw, faces=bm_sw.faces)
    m_sw = bpy.data.meshes.new("Mesh_Banqueta_Modular")
    bm_sw.to_mesh(m_sw)
    bm_sw.free()
    obj_sw = bpy.data.objects.new("Banqueta_BBVA_Modular", m_sw)
    col.objects.link(obj_sw)
    obj_sw.data.materials.append(mats["banqueta"])
    obj_sw.data.materials.append(mats["cordon_rojo"])
    for p in m_sw.polygons:
        c_x = sum(m_sw.vertices[v].co.x for v in p.vertices) / len(p.vertices)
        c_y = sum(m_sw.vertices[v].co.y for v in p.vertices) / len(p.vertices)
        if c_y < -3.72 or (c_x < -3.72 and c_y > 0):
            p.material_index = 1
        else:
            p.material_index = 0
    return obj_sw

def setup_lighting_and_render(col):
    """Configura iluminación diurna y 6 cámaras calibradas para cubrir todas las caras del edificio."""
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
    
    # 1. Cámara 'Guajardo_45': Perspectiva frontal directa al chaflán a 45º
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

    # 2. Cámara 'Juarez_Frontal': Elevación de la Fachada Sur (Av. Juárez)
    c2_data = bpy.data.cameras.new("Cam_Juarez_Frontal")
    c2_data.lens = 28
    c2 = bpy.data.objects.new("Cam_Juarez_Frontal", c2_data)
    col.objects.link(c2)
    c2.location = (13.50, -22.00, 4.80)
    c2.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    cams["juarez_frontal"] = c2

    # 3. Cámara 'Cardenas_West': Elevación de la Fachada Oeste por Calle Lázaro Cárdenas (6 crujías, 30 m)
    c3_data = bpy.data.cameras.new("Cam_Cardenas_West")
    c3_data.lens = 26
    c3 = bpy.data.objects.new("Cam_Cardenas_West", c3_data)
    col.objects.link(c3)
    c3.location = (-27.00, 17.00, 4.80)
    c3.rotation_euler = (math.radians(90.0), 0.0, math.radians(-90.0))
    cams["cardenas_west"] = c3

    # 4. Cámara 'East_Parking': Perspectiva de rampa, caseta y letrero ENTRADA BBVA
    c4_data = bpy.data.cameras.new("Cam_East_Parking")
    c4_data.lens = 28
    c4 = bpy.data.objects.new("Cam_East_Parking", c4_data)
    col.objects.link(c4)
    loc4 = Vector((36.00, -8.00, 4.50))
    tgt4 = Vector((23.50, 6.00, 3.20))
    dir4 = tgt4 - loc4
    c4.location = loc4
    c4.rotation_euler = dir4.to_track_quat('-Z', 'Y').to_euler()
    cams["east_parking"] = c4

    # 5. Cámara 'Aerial_Top': Vista aérea cenital
    c5_data = bpy.data.cameras.new("Cam_Aerial_Top")
    c5_data.lens = 42
    c5 = bpy.data.objects.new("Cam_Aerial_Top", c5_data)
    col.objects.link(c5)
    c5.location = (13.00, 15.00, 48.00)
    c5.rotation_euler = (0.0, 0.0, math.radians(-90.0))
    cams["aerial_top"] = c5

    # 6. Cámara 'Dentista_Closeup': Acercamiento en perspectiva angular capturando el letrero a 90º y las letras DENTISTA en fachada
    c6_data = bpy.data.cameras.new("Cam_Dentista_Closeup")
    c6_data.lens = 30
    c6 = bpy.data.objects.new("Cam_Dentista_Closeup", c6_data)
    col.objects.link(c6)
    loc6 = Vector((-5.60, 23.40, 2.15)) # Vista desde el sur hacia el norte-noreste como en media_1789778345732
    tgt6 = Vector((-0.35, 26.85, 2.95))
    dir6 = tgt6 - loc6
    c6.location = loc6
    c6.rotation_euler = dir6.to_track_quat('-Z', 'Y').to_euler()
    cams["dentista_closeup"] = c6

    # 7. Cámara 'East_Ground_Truth': Perspectiva exacta matching media_1789781403754
    c7_data = bpy.data.cameras.new("Cam_East_Ground_Truth")
    c7_data.lens = 28
    c7 = bpy.data.objects.new("Cam_East_Ground_Truth", c7_data)
    col.objects.link(c7)
    loc7 = Vector((29.50, 0.20, 2.25))
    tgt7 = Vector((22.80, 7.80, 4.30))
    dir7 = tgt7 - loc7
    c7.location = loc7
    c7.rotation_euler = dir7.to_track_quat('-Z', 'Y').to_euler()
    cams["east_ground_truth"] = c7

    return cams

def generate_godot_tscn(tscn_path, glb_rel_path):
    """Genera la escena .tscn de Godot 4 con StaticBody3D y colisiones analíticas precisas sin barreras invisibles."""
    tscn_content = f"""[gd_scene load_steps=9 format=3 uid="uid://bbva_tecate_centro_008"]

[ext_resource type="PackedScene" path="{glb_rel_path}" id="1_mesh"]
[ext_resource type="PackedScene" path="res://assets/buildings/banqueta_bbva_tecate.glb" id="2_banqueta"]

[sub_resource type="BoxShape3D" id="BoxShape3D_juarez"]
size = Vector3(18.6, 7.3, 16.0)

[sub_resource type="BoxShape3D" id="BoxShape3D_cardenas"]
size = Vector3(16.0, 7.3, 25.8)

[sub_resource type="BoxShape3D" id="BoxShape3D_puertas"]
size = Vector3(5.8, 9.1, 0.35)

[sub_resource type="BoxShape3D" id="BoxShape3D_rampa"]
size = Vector3(4.5, 1.2, 14.0)

[sub_resource type="BoxShape3D" id="BoxShape3D_banqueta_juarez"]
size = Vector3(34.6, 0.18, 3.8)

[sub_resource type="BoxShape3D" id="BoxShape3D_banqueta_cardenas"]
size = Vector3(3.8, 0.18, 32.0)

[node name="BBVA_Tecate" type="StaticBody3D"]

[node name="ModelInstance" parent="." instance=ExtResource("1_mesh")]

[node name="BanquetaInstance" parent="." instance=ExtResource("2_banqueta")]

[node name="Col_Juarez" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 13.5, 3.65, -8.0)
shape = SubResource("BoxShape3D_juarez")

[node name="Col_Cardenas" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 8.0, 3.65, -17.1)
shape = SubResource("BoxShape3D_cardenas")

[node name="Col_Puertas_Chamfer" type="CollisionShape3D" parent="."]
transform = Transform3D(0.707107, 0, 0.707107, 0, 1, 0, -0.707107, 0, 0.707107, 2.12, 4.55, -2.12)
shape = SubResource("BoxShape3D_puertas")

[node name="Col_Rampa" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 25.0, 0.6, -7.0)
shape = SubResource("BoxShape3D_rampa")

[node name="Col_Banqueta_Juarez" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 13.5, 0.09, 1.9)
shape = SubResource("BoxShape3D_banqueta_juarez")

[node name="Col_Banqueta_Cardenas" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -1.9, 0.09, -16.0)
shape = SubResource("BoxShape3D_banqueta_cardenas")
"""
    with open(tscn_path, "w", encoding="utf-8") as f:
        f.write(tscn_content)
    print(f"--> Escena Godot generada: {tscn_path}")

def main():
    print("================================================================")
    print(" GENERADOR PROCEDURAL 3D V5.0: BANCO BBVA TECATE CENTRO (2009)  ")
    print(" (Ochava 1956, Cárdenas continua a Dentista, Fascia 2009)       ")
    print("================================================================")
    
    root_col = clean_scene()
    mats = create_materials()
    
    # 1. Esquina ochavada a 45º: Torreón Guajardo 1956 y espectacular 2009
    obj_tower, obj_t_glass, objs_steel, texts_guaj, texts_totem = build_45deg_guajardo_corner(mats, root_col)
    
    # 2. Fachada Sur (Av. Benito Juárez)
    obj_juarez_st, obj_j_alum, obj_j_gl, obj_j_bl, objs_j_fa, texts_j_desp, obj_j_tj = build_south_facade_juarez(mats, root_col)
    
    # 3. Fachada Oeste (Calle Presidente Lázaro Cárdenas continua hasta DENTISTA)
    obj_card_st, obj_c_cb, obj_c_al, obj_c_gl, obj_c_bl, objs_c_fa, texts_c_desp, obj_c_tj = build_west_facade_cardenas(mats, root_col)
    
    # 4. Fachada Este (Estacionamiento), rampa, caseta y letrero ortogonal
    obj_east, objs_east_win, obj_ramp, obj_rail, obj_caseta, obj_sign, o_sign_r = build_east_facade_and_parking(mats, root_col)
    
    # 5. Banqueta modular independiente (opcional)
    obj_banqueta = build_optional_sidewalk(mats, root_col)
    
    # 6. Iluminación y 5 cámaras técnicas calibradas
    cams = setup_lighting_and_render(root_col)
    
    # 7. Guardar archivo maestro Blender (.blend)
    blend_path = "blender_assets/buildings/bbva_tecate_centro.blend"
    os.makedirs(os.path.dirname(blend_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"--> Archivo maestro Blender guardado: {blend_path}")
    
    # 8. Exportar GLB para Godot 4 (EXCLUYENDO la banqueta según instrucción del usuario)
    glb_path = "godot_project/assets/buildings/bbva_tecate_centro.glb"
    os.makedirs(os.path.dirname(glb_path), exist_ok=True)
    
    bpy.ops.object.select_all(action='DESELECT')
    render_types = {'MESH', 'CURVE', 'FONT'}
    for o in root_col.objects:
        if o.type in render_types and o != obj_banqueta:
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
    print(f"--> Asset Godot exportado (sin banqueta): {glb_path}")
    
    # Exportar asset modular de banqueta por separado
    sw_glb_path = "godot_project/assets/buildings/banqueta_bbva_tecate.glb"
    bpy.ops.object.select_all(action='DESELECT')
    obj_banqueta.select_set(True)
    bpy.context.view_layer.objects.active = obj_banqueta
    bpy.ops.export_scene.gltf(
        filepath=sw_glb_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_materials='EXPORT',
        export_yup=True
    )
    print(f"--> Asset modular de banqueta exportado: {sw_glb_path}")
    
    # 9. Generar escena Godot .tscn
    tscn_path = "godot_project/assets/buildings/bbva_tecate_centro.tscn"
    generate_godot_tscn(tscn_path, "res://assets/buildings/bbva_tecate_centro.glb")
    
    # 10. Renderizar las 5 vistas técnicas de validación
    scene = bpy.context.scene
    renders = [
        ("guajardo_45", "docs/images/bbva/bbva_guajardo_45.png", 1280, 720),
        ("juarez_frontal", "docs/images/bbva/bbva_juarez_frontal.png", 1280, 720),
        ("cardenas_west", "docs/images/bbva/bbva_cardenas_west.png", 1280, 720),
        ("dentista_closeup", "docs/images/bbva/bbva_dentista_closeup.png", 1280, 720),
        ("east_parking", "docs/images/bbva/bbva_east_parking.png", 1280, 720),
        ("east_ground_truth", "docs/images/bbva/bbva_east_ground_truth.png", 1280, 720),
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
    print(" GENERACIÓN V5.0 FINALIZADA CON ÉXITO                           ")
    print("================================================================")

if __name__ == "__main__":
    main()
