"""
=============================================================================
GENERADOR PROCEDURAL 3D: COMPLEJO COMERCIAL PDTE. LÁZARO CÁRDENAS 33
(ÉPOCA: HISTÓRICO 2009 - VERSIÓN GROUND-TRUTH FOTORREALISTA V4.1)
=============================================================================
Reconstrucción fidedigna basada en evidencia fotográfica directa de alta resolución:
  - media_1790243320877.png & media_1790241121751.png (Fachada Cárdenas completa)
  - media_1790243423150.jpg (Florería Orquídea y esquina Libertad)
  - DcOz2fF61YH1bc6cN7zlrA_yaw_354.12.png (Foto Estudio Curiel y Libertad)
  - v-LOQBvBVPSdc4raGN4FeQ_yaw_174.12.png (Reverso estacionamiento BBVA)

Calibraciones clave V4.1:
  1. Iluminación diurna completa con cielo azul y luz de rebote ambiental en todas las fachadas.
  2. Corrección de orientación relativa de elementos en Bar Diana (puerta a la derecha/sur,
     Diana Cazadora a la izquierda/norte, cóctel a la derecha/sur).
  3. Corrección de orientación relativa en Party Rentals (puerta a la derecha/sur, notas musicales
     al centro, lona de inflables a la izquierda/norte).
  4. Florería Orquídea: Frontón monumental de 6.20 m con marco biselado blanco, mosaico verde salvia
     moteado, gran letrero con greca perimetral roja y cámara calibrada con luz frontal.
  5. Foto Estudio Curiel: Fachada blanca Streamline Moderne con 3 estrías metálicas, rótulos y tótem rojo.
  6. Librería España: Frente vidriado con libros y revistas, murete mostaza brillante, fascia marrón
     con teléfonos dorados y espectacular de azotea Tecate / Bar Diana en diagonal visible.
=============================================================================
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Euler, Matrix

# ---------------------------------------------------------------------------
# 1. Utilidades Geométricas
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
    """Genera una caja ortogonal cerrada con normales hacia el exterior."""
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

def create_mesh_object(name, bm, material, col):
    """Convierte un BMesh en objeto Mesh de Blender, asigna material y vincula a colección."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(f"Mesh_{name}")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    if material:
        obj.data.materials.append(material)
    col.objects.link(obj)
    return obj

def add_3d_text(name, body, size, extrude, loc, rot_euler, mat, col, align_x='CENTER'):
    """Crea un objeto de texto 3D procedural anti-espejo."""
    f_curve = bpy.data.curves.new(type="FONT", name=f"Font_{name}")
    f_curve.body = body
    f_curve.size = size
    f_curve.extrude = extrude
    f_curve.align_x = align_x
    obj = bpy.data.objects.new(name, f_curve)
    obj.location = Vector(loc)
    obj.rotation_euler = Euler(rot_euler, 'XYZ')
    if mat:
        obj.data.materials.append(mat)
    col.objects.link(obj)
    return obj

# ---------------------------------------------------------------------------
# 2. Materiales PBR
# ---------------------------------------------------------------------------

def make_pbr(name, base_color, roughness=0.85, metallic=0.0, alpha=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (base_color[0], base_color[1], base_color[2], 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if alpha < 1.0:
        bsdf.inputs['Alpha'].default_value = alpha
        mat.blend_method = 'BLEND'
    mat.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def create_materials():
    mats = {}
    # Muros base y estructura
    mats["estuco_ocre"] = make_pbr("M_Estuco_Ocre_Continuo", (0.835, 0.730, 0.525), roughness=0.85)     # #D5BA86 Ocre mostaza suave
    mats["zocalo_marron"] = make_pbr("M_Zocalo_Marron_Chocolate", (0.314, 0.165, 0.122), roughness=0.90) # #502A1F
    mats["concreto_marquesina"] = make_pbr("M_Concreto_Marquesina", (0.88, 0.86, 0.83), roughness=0.70)
    mats["concreto_blanco"] = make_pbr("M_Concreto_Blanco_Remates", (0.96, 0.96, 0.96), roughness=0.55)
    mats["zocalo_basal"] = make_pbr("M_Zocalo_Basal_Enterrado", (0.16, 0.16, 0.16), roughness=0.95)

    # Bar Diana
    mats["fachaleta_diana"] = make_pbr("M_Fachaleta_Laja_Blanca", (0.92, 0.90, 0.86), roughness=0.65) # Piedra blanca apilada
    mats["verde_menta_diana"] = make_pbr("M_Verde_Menta_Diana", (0.824, 0.867, 0.835), roughness=0.85)   # #D2DDD5
    mats["herreria_verde_diana"] = make_pbr("M_Herreria_Verde_Diana", (0.41, 0.45, 0.30), roughness=0.45, metallic=0.6)
    mats["panel_rotulo_diana"] = make_pbr("M_Panel_Rotulo_Diana", (0.97, 0.97, 0.96), roughness=0.25)
    mats["rotulo_diana_dorado"] = make_pbr("M_Rotulo_Diana_Dorado", (0.83, 0.69, 0.22), roughness=0.30, metallic=0.7)
    mats["rotulo_diana_azul"] = make_pbr("M_Rotulo_Diana_Azul", (0.12, 0.25, 0.50), roughness=0.35)

    # Annita's Boutique
    mats["caja_grafito_anita"] = make_pbr("M_Caja_Grafito_Anita", (0.13, 0.15, 0.16), roughness=0.30, metallic=0.2) # #22252A
    mats["ovalo_plata_anita"] = make_pbr("M_Ovalo_Plata_Anita", (0.88, 0.89, 0.90), roughness=0.25, metallic=0.5)
    mats["ovalo_azul_anita"] = make_pbr("M_Ovalo_Azul_Anita", (0.20, 0.30, 0.38), roughness=0.35)
    mats["letras_anita_blanco"] = make_pbr("M_Letras_Anita_Blanco", (0.98, 0.98, 0.98), roughness=0.20)
    mats["persianas_madera"] = make_pbr("M_Persianas_Madera_Anita", (0.50, 0.33, 0.20), roughness=0.55)
    mats["espectacular_azul_renta"] = make_pbr("M_Espectacular_Azul_Renta", (0.05, 0.17, 0.33), roughness=0.35)
    mats["espectacular_rojo_renta"] = make_pbr("M_Espectacular_Rojo_Renta", (0.75, 0.13, 0.13), roughness=0.30)
    mats["espectacular_blanco_renta"] = make_pbr("M_Espectacular_Blanco_Renta", (0.95, 0.95, 0.95), roughness=0.25)

    # Party Rentals
    mats["panel_blanco_party"] = make_pbr("M_Panel_Blanco_Party", (0.96, 0.96, 0.96), roughness=0.25)
    mats["letras_verdes_party"] = make_pbr("M_Letras_Verdes_Party", (0.10, 0.55, 0.20), roughness=0.30)
    mats["letras_azules_party"] = make_pbr("M_Letras_Azules_Party", (0.12, 0.30, 0.65), roughness=0.30)
    mats["logo_kuroky_magenta"] = make_pbr("M_Logo_Kuroky_Magenta", (0.75, 0.10, 0.50), roughness=0.30)
    mats["lona_fotos_party"] = make_pbr("M_Lona_Fotos_Party", (0.90, 0.40, 0.20), roughness=0.35)
    mats["notas_musicales"] = make_pbr("M_Notas_Musicales_Vidrio", (0.95, 0.95, 0.95), roughness=0.15)
    mats["buzones_amarillos"] = make_pbr("M_Buzones_Amarillos_Poste", (0.90, 0.75, 0.10), roughness=0.40, metallic=0.3)

    # Librería España
    mats["murete_mostaza_lib"] = make_pbr("M_Murete_Mostaza_Libreria", (0.90, 0.70, 0.22), roughness=0.75) # #E5B239
    mats["fascia_marron_lib"] = make_pbr("M_Fascia_Marron_Libreria", (0.24, 0.14, 0.10), roughness=0.50)
    mats["letras_doradas_lib"] = make_pbr("M_Letras_Doradas_Libreria", (0.88, 0.75, 0.25), roughness=0.30, metallic=0.7)
    mats["panel_rotulo_lib"] = make_pbr("M_Panel_Rotulo_Libreria", (0.96, 0.96, 0.95), roughness=0.25)
    mats["letras_negras_lib"] = make_pbr("M_Letras_Negras_Libreria", (0.10, 0.10, 0.12), roughness=0.30)
    mats["letras_rojas_lib"] = make_pbr("M_Letras_Rojas_Libreria", (0.80, 0.12, 0.12), roughness=0.30)
    mats["revistas_exhibidor"] = make_pbr("M_Revistas_Libros_Color", (0.85, 0.75, 0.65), roughness=0.60)

    # Espectacular Tecate de Azotea
    mats["lona_blanca_tecate"] = make_pbr("M_Lona_Blanca_Tecate", (0.95, 0.95, 0.95), roughness=0.40)
    mats["logo_rojo_tecate"] = make_pbr("M_Logo_Rojo_Tecate", (0.82, 0.08, 0.08), roughness=0.30)
    mats["acero_estructura"] = make_pbr("M_Acero_Estructural_Azotea", (0.35, 0.37, 0.40), roughness=0.45, metallic=0.85)

    # Florería Orquídea
    mats["mosaico_orquidea"] = make_pbr("M_Mosaico_Terrazo_Verde", (0.557, 0.655, 0.550), roughness=0.30) # #8EA78C moteado verde salvia
    mats["laja_rustica_orquidea"] = make_pbr("M_Laja_Rustica_Cafe", (0.55, 0.33, 0.26), roughness=0.95) # #8C5542
    mats["panel_rotulo_orquidea"] = make_pbr("M_Panel_Rotulo_Orquidea", (0.96, 0.96, 0.96), roughness=0.25)
    mats["greca_roja_orquidea"] = make_pbr("M_Greca_Roja_Orquidea", (0.75, 0.12, 0.12), roughness=0.30)
    mats["letras_purpura_orquidea"] = make_pbr("M_Letras_Purpura_Orquidea", (0.18, 0.10, 0.28), roughness=0.30)
    mats["estuco_blanco_orquidea"] = make_pbr("M_Estuco_Blanco_Orquidea", (0.95, 0.95, 0.93), roughness=0.80)

    # Foto Estudio Curiel
    mats["estuco_blanco_curiel"] = make_pbr("M_Estuco_Blanco_Curiel", (0.96, 0.96, 0.96), roughness=0.75)
    mats["moldura_streamline"] = make_pbr("M_Moldura_Streamline_Plata", (0.85, 0.87, 0.88), roughness=0.30, metallic=0.6)
    mats["letras_azul_curiel"] = make_pbr("M_Letras_Azul_Curiel", (0.12, 0.25, 0.65), roughness=0.30)
    mats["letras_dorado_curiel"] = make_pbr("M_Letras_Dorado_Curiel", (0.78, 0.60, 0.20), roughness=0.35, metallic=0.6)
    mats["totem_rojo_curiel"] = make_pbr("M_Totem_Rojo_Curiel", (0.73, 0.09, 0.11), roughness=0.35, metallic=0.2)

    # Vidrios, carpintería y techo
    mats["vidrio_comercial"] = make_pbr("M_Vidrio_Comercial_Limpio", (0.80, 0.88, 0.92), roughness=0.08, alpha=0.30)
    mats["vidrio_ahumado"] = make_pbr("M_Vidrio_Ahumado_Diana", (0.15, 0.18, 0.20), roughness=0.10, alpha=0.75)
    mats["aluminio_blanco"] = make_pbr("M_Aluminio_Blanco_Canceles", (0.95, 0.95, 0.95), roughness=0.35, metallic=0.8)
    mats["aluminio_negro"] = make_pbr("M_Aluminio_Negro_Marcos", (0.15, 0.15, 0.15), roughness=0.40, metallic=0.85)
    mats["techo_impermeable"] = make_pbr("M_Azotea_Impermeabilizante", (0.70, 0.68, 0.65), roughness=0.90)

    return mats

# ---------------------------------------------------------------------------
# 3. Construcción del Frente Cárdenas
# ---------------------------------------------------------------------------

def build_cardenas_facade(mats, col):
    """Construye minuciosamente la fachada sobre Calle Cárdenas."""
    objects = []
    rot_cardenas = (math.radians(90.0), 0.0, math.radians(-90.0))

    # 0. ZÓCALO BASAL ENTERRADO (-1.20 a 0.00 m)
    bm_zocalo = bmesh.new()
    add_box(bm_zocalo, -0.30, 16.50, -0.10, 24.60, -1.20, 0.00)
    obj_zocalo = create_mesh_object("Cardenas_Zocalo_Basal_Enterrado", bm_zocalo, mats["zocalo_basal"], col)
    objects.append(obj_zocalo)

    # 1. CUERPO CONTINUO CENTRAL (Bar Diana, Annita's, Party Rentals: Y in [4.80, 19.30])
    # Zócalo marrón inferior (Z in [0.00, 0.40 m])
    bm_zoc_c = bmesh.new()
    add_box(bm_zoc_c, -0.05, 0.40, 9.10, 19.30, 0.00, 0.40)
    obj_zoc_c = create_mesh_object("Cardenas_Zocalo_Marron_Continuo", bm_zoc_c, mats["zocalo_marron"], col)
    objects.append(obj_zoc_c)

    # Muros ocre mostaza continuo (#D5BA86)
    bm_ocre = bmesh.new()
    # Pretil superior continuo (Z in [2.95, 3.90 m], Y in [9.10, 19.30 m])
    add_box(bm_ocre, 0.00, 0.40, 9.10, 19.30, 2.95, 3.90)
    # Pared Party Rentals
    add_box(bm_ocre, 0.00, 0.40, 14.20, 15.60, 0.40, 2.75) # Machón divisorio y murete
    add_box(bm_ocre, 0.00, 0.40, 15.60, 18.80, 0.40, 0.85) # Murete bajo ventana notas
    # Pared Annita's
    add_box(bm_ocre, 0.00, 0.40, 10.50, 14.10, 0.40, 0.65) # Murete bajo persianas
    add_box(bm_ocre, 0.00, 0.40, 10.35, 10.55, 0.40, 2.75) # Machón puerta-vitrina
    add_box(bm_ocre, 0.00, 0.40, 9.00, 9.30, 0.00, 2.75)   # Machón divisorio Diana-Annita
    obj_ocre = create_mesh_object("Cardenas_Muro_Ocre_Continuo", bm_ocre, mats["estuco_ocre"], col)
    objects.append(obj_ocre)

    # Marquesina corrida en voladizo (Z in [2.75, 2.95 m], vuela 0.70 m hacia la calle)
    bm_marq = bmesh.new()
    add_box(bm_marq, -0.70, 0.40, 4.80, 19.30, 2.75, 2.95)
    add_box(bm_marq, -0.75, -0.68, 4.80, 19.30, 2.70, 2.98) # Moldura frontal goterón
    obj_marq = create_mesh_object("Cardenas_Marquesina_Corrida", bm_marq, mats["concreto_marquesina"], col)
    objects.append(obj_marq)

    # Pilastra / aleta vertical saliente en esquina con remate oblicuo (Y in [19.15, 19.45])
    bm_aleta = bmesh.new()
    v_al = [
        bm_aleta.verts.new((-0.20, 19.15, 0.00)), bm_aleta.verts.new((0.45, 19.15, 0.00)),
        bm_aleta.verts.new((0.45, 19.45, 0.00)), bm_aleta.verts.new((-0.20, 19.45, 0.00)),
        bm_aleta.verts.new((-0.20, 19.15, 4.80)), bm_aleta.verts.new((0.45, 19.15, 4.80)),
        bm_aleta.verts.new((0.45, 19.45, 3.90)), bm_aleta.verts.new((-0.20, 19.45, 3.90))
    ]
    bm_aleta.faces.new((v_al[0], v_al[1], v_al[2], v_al[3]))
    bm_aleta.faces.new((v_al[4], v_al[7], v_al[6], v_al[5]))
    bm_aleta.faces.new((v_al[0], v_al[4], v_al[5], v_al[1]))
    bm_aleta.faces.new((v_al[1], v_al[5], v_al[6], v_al[2]))
    bm_aleta.faces.new((v_al[2], v_al[6], v_al[7], v_al[3]))
    bm_aleta.faces.new((v_al[3], v_al[7], v_al[4], v_al[0]))
    obj_aleta = create_mesh_object("Cardenas_Aleta_Vertical_Esquina", bm_aleta, mats["concreto_blanco"], col)
    objects.append(obj_aleta)

    # -----------------------------------------------------------------------
    # 2. BAR TURÍSTICO DIANA (Y in [4.80, 9.10])
    # -----------------------------------------------------------------------
    # A. Puerta doble de herrería verde olivo a la DERECHA (menor Y, hacia Librería España: Y in [4.90, 5.90])
    bm_diana_p = bmesh.new()
    add_box(bm_diana_p, 0.02, 0.12, 4.90, 5.90, 2.40, 2.46)
    add_box(bm_diana_p, 0.02, 0.12, 4.90, 4.96, 0.00, 2.40)
    add_box(bm_diana_p, 0.02, 0.12, 5.84, 5.90, 0.00, 2.40)
    add_box(bm_diana_p, 0.02, 0.12, 5.38, 5.42, 0.00, 2.40)
    for by in range(12):
        pos_y = 4.98 + by * 0.072
        add_box(bm_diana_p, 0.04, 0.07, pos_y, pos_y + 0.02, 0.00, 2.40)
    obj_diana_p = create_mesh_object("Diana_Puerta_Herreria_Verde", bm_diana_p, mats["herreria_verde_diana"], col)
    objects.append(obj_diana_p)

    # B. Zócalo de fachaleta de piedra laja blanca apilada (Y in [5.90, 9.05], Z in [0.00, 0.85 m])
    bm_diana_laja = bmesh.new()
    add_box(bm_diana_laja, -0.04, 0.40, 5.90, 9.05, 0.00, 0.85)
    obj_diana_laja = create_mesh_object("Diana_Zocalo_Fachaleta_Blanca", bm_diana_laja, mats["fachaleta_diana"], col)
    objects.append(obj_diana_laja)

    # C. Muro verde menta pastel (#D2DDD5) de Z = 0.85 a 2.35 m
    bm_diana_m = bmesh.new()
    add_box(bm_diana_m, 0.00, 0.40, 5.90, 9.05, 0.85, 2.35)
    obj_diana_m = create_mesh_object("Diana_Muro_Verde_Menta", bm_diana_m, mats["verde_menta_diana"], col)
    objects.append(obj_diana_m)

    # D. Clereestorio horizontal superior con vidrio ahumado (Z in [2.35, 2.70 m])
    bm_diana_cl = bmesh.new()
    add_box(bm_diana_cl, 0.05, 0.15, 5.95, 9.00, 2.35, 2.70)
    add_box(bm_diana_cl, 0.03, 0.17, 5.90, 9.05, 2.32, 2.36)
    add_box(bm_diana_cl, 0.03, 0.17, 5.90, 9.05, 2.69, 2.73)
    obj_diana_cl = create_mesh_object("Diana_Clereestorio_Ahumado", bm_diana_cl, mats["vidrio_ahumado"], col)
    objects.append(obj_diana_cl)

    # E. PANEL PRINCIPAL DE BAR DIANA SOBRE LA MARQUESINA (Y in [4.90, 8.95], Z in [2.95, 4.10 m])
    bm_diana_rot = bmesh.new()
    add_box(bm_diana_rot, -0.15, -0.05, 4.90, 8.95, 2.95, 4.10)
    # Marco negro perimetral
    add_box(bm_diana_rot, -0.17, -0.03, 4.88, 8.97, 2.93, 2.97)
    add_box(bm_diana_rot, -0.17, -0.03, 4.88, 8.97, 4.08, 4.12)
    add_box(bm_diana_rot, -0.17, -0.03, 4.88, 4.92, 2.93, 4.12)
    add_box(bm_diana_rot, -0.17, -0.03, 8.93, 8.97, 2.93, 4.12)
    obj_diana_rot = create_mesh_object("Diana_Panel_Rotulo_Blanco", bm_diana_rot, mats["panel_rotulo_diana"], col)
    objects.append(obj_diana_rot)

    # Silueta de la Diana Cazadora dorada a la IZQUIERDA (mayor Y, hacia Annita's: Y in [8.10, 8.75])
    bm_diana_stat = bmesh.new()
    add_box(bm_diana_stat, -0.18, -0.14, 8.25, 8.55, 3.05, 3.25) # Pedestal
    add_box(bm_diana_stat, -0.18, -0.14, 8.32, 8.48, 3.25, 3.75) # Cuerpo
    add_box(bm_diana_stat, -0.18, -0.14, 8.15, 8.40, 3.55, 3.98) # Arco al cenit
    obj_diana_stat = create_mesh_object("Diana_Silueta_Cazadora_Dorada", bm_diana_stat, mats["rotulo_diana_dorado"], col)
    objects.append(obj_diana_stat)

    # Letras caligráficas centrales 'Bar TURISTICO Diana'
    t_d1 = add_3d_text("Diana_Txt_Bar", "Bar", 0.30, 0.02, (-0.17, 7.35, 3.65), rot_cardenas, mats["rotulo_diana_dorado"], col, 'RIGHT')
    t_d2 = add_3d_text("Diana_Txt_Turistico", "TURISTICO", 0.16, 0.015, (-0.17, 6.45, 3.75), rot_cardenas, mats["rotulo_diana_azul"], col, 'RIGHT')
    t_d3 = add_3d_text("Diana_Txt_Diana", "Diana", 0.42, 0.025, (-0.17, 7.20, 3.25), rot_cardenas, mats["rotulo_diana_dorado"], col, 'RIGHT')
    t_d4 = add_3d_text("Diana_Txt_Desde", "DESDE / SINCE 1957", 0.09, 0.01, (-0.17, 7.00, 3.08), rot_cardenas, mats["letras_negras_lib"], col, 'RIGHT')
    objects.extend([t_d1, t_d2, t_d3, t_d4])

    # Ilustración cóctel y botellas a la DERECHA (menor Y, hacia Librería España: Y in [5.10, 5.65])
    bm_coctel = bmesh.new()
    add_box(bm_coctel, -0.18, -0.14, 5.15, 5.35, 3.20, 3.75)
    add_box(bm_coctel, -0.18, -0.14, 5.40, 5.55, 3.15, 3.85)
    obj_coctel = create_mesh_object("Diana_Ilustracion_Coctel", bm_coctel, mats["espectacular_rojo_renta"], col)
    objects.append(obj_coctel)

    # -----------------------------------------------------------------------
    # 3. ANNITA'S BOUTIQUE (Y in [9.10, 14.20])
    # -----------------------------------------------------------------------
    # Puerta comercial a la DERECHA (menor Y: Y in [9.30, 10.35], Z in [0.00, 2.70 m])
    bm_anita_p = bmesh.new()
    add_box(bm_anita_p, 0.02, 0.12, 9.30, 10.35, 2.65, 2.70)
    add_box(bm_anita_p, 0.02, 0.12, 9.30, 9.36, 0.00, 2.65)
    add_box(bm_anita_p, 0.02, 0.12, 10.29, 10.35, 0.00, 2.65)
    add_box(bm_anita_p, 0.04, 0.06, 9.36, 10.29, 0.00, 2.65) # Vidrio
    for py in range(6):
        py_pos = 9.42 + py * 0.14
        add_box(bm_anita_p, 0.07, 0.09, py_pos, py_pos + 0.02, 0.00, 2.65) # Reja de protección
    obj_anita_p = create_mesh_object("Anita_Puerta_Canceleria", bm_anita_p, mats["aluminio_blanco"], col)
    objects.append(obj_anita_p)

    # Vitrina con persianas venecianas de madera a la IZQUIERDA (mayor Y: Y in [10.55, 14.10], Z in [0.65, 2.70 m])
    bm_pers = bmesh.new()
    add_box(bm_pers, 0.02, 0.15, 10.55, 14.10, 0.65, 0.70)
    add_box(bm_pers, 0.02, 0.15, 10.55, 14.10, 2.65, 2.70)
    add_box(bm_pers, 0.02, 0.15, 10.55, 10.60, 0.70, 2.65)
    add_box(bm_pers, 0.02, 0.15, 14.05, 14.10, 0.70, 2.65)
    add_box(bm_pers, 0.04, 0.06, 10.60, 14.05, 0.70, 2.65) # Vidrio
    for l in range(24):
        zl = 0.72 + l * 0.08
        add_box(bm_pers, 0.08, 0.16, 10.62, 14.03, zl, zl + 0.02) # Lamas madera
    obj_pers = create_mesh_object("Anita_Vitrina_Persianas_Madera", bm_pers, mats["persianas_madera"], col)
    objects.append(obj_pers)

    # CAJA RECTANGULAR GRAFITO SOBRE MARQUESINA (Y in [9.50, 13.80], Z in [3.05, 3.80 m])
    bm_anita_caja = bmesh.new()
    add_box(bm_anita_caja, -0.15, -0.05, 9.50, 13.80, 3.05, 3.80)
    add_box(bm_anita_caja, -0.17, -0.03, 9.47, 13.83, 3.03, 3.07)
    add_box(bm_anita_caja, -0.17, -0.03, 9.47, 13.83, 3.78, 3.82)
    add_box(bm_anita_caja, -0.17, -0.03, 9.47, 9.51, 3.03, 3.82)
    add_box(bm_anita_caja, -0.17, -0.03, 13.79, 13.83, 3.03, 3.82)
    obj_anita_caja = create_mesh_object("Anita_Caja_Grafito_Rotulo", bm_anita_caja, mats["caja_grafito_anita"], col)
    objects.append(obj_anita_caja)

    # Óvalo horizontal plateado y azul pizarra
    bm_anita_ov = bmesh.new()
    add_box(bm_anita_ov, -0.18, -0.14, 10.50, 12.80, 3.15, 3.70)
    obj_anita_ov = create_mesh_object("Anita_Ovalo_Plateado", bm_anita_ov, mats["ovalo_plata_anita"], col)
    objects.append(obj_anita_ov)

    t_an1 = add_3d_text("Anita_Txt_Annitas", "Annita's", 0.30, 0.02, (-0.20, 11.65, 3.42), rot_cardenas, mats["letras_anita_blanco"], col, 'CENTER')
    t_an2 = add_3d_text("Anita_Txt_Boutique", "Boutique", 0.12, 0.015, (-0.20, 11.65, 3.25), rot_cardenas, mats["letras_anita_blanco"], col, 'CENTER')
    objects.extend([t_an1, t_an2])

    # ESPECTACULAR VERTICAL DE AZOTEA: RENTA MESAS SILLAS (Y in [11.20, 12.80], Z in [3.90, 6.90 m])
    bm_renta = bmesh.new()
    add_box(bm_renta, 0.10, 0.20, 11.20, 12.80, 5.70, 6.90) # Panel superior blanco
    obj_renta_sup = create_mesh_object("Renta_Panel_Blanco_Superior", bm_renta, mats["espectacular_blanco_renta"], col)
    objects.append(obj_renta_sup)

    bm_renta_b = bmesh.new()
    add_box(bm_renta_b, 0.10, 0.20, 11.20, 12.80, 3.90, 5.70) # Panel inferior azul
    obj_renta_inf = create_mesh_object("Renta_Panel_Azul_Inferior", bm_renta_b, mats["espectacular_azul_renta"], col)
    objects.append(obj_renta_inf)

    bm_renta_st = bmesh.new()
    add_box(bm_renta_st, 0.05, 0.25, 11.15, 11.25, 3.90, 6.95)
    add_box(bm_renta_st, 0.05, 0.25, 12.75, 12.85, 3.90, 6.95)
    add_box(bm_renta_st, 0.05, 0.25, 11.15, 12.85, 6.90, 6.95)
    obj_renta_est = create_mesh_object("Renta_Estructura_Acero", bm_renta_st, mats["acero_estructura"], col)
    objects.append(obj_renta_est)

    t_r1 = add_3d_text("Renta_Txt_RENTA", "RENTA", 0.55, 0.025, (0.07, 12.00, 6.00), rot_cardenas, mats["espectacular_rojo_renta"], col, 'CENTER')
    t_r2 = add_3d_text("Renta_Txt_MESAS", "MESAS", 0.48, 0.025, (0.07, 12.00, 5.15), rot_cardenas, mats["espectacular_blanco_renta"], col, 'CENTER')
    t_r3 = add_3d_text("Renta_Txt_SILLAS", "SILLAS", 0.48, 0.025, (0.07, 12.00, 4.55), rot_cardenas, mats["espectacular_blanco_renta"], col, 'CENTER')
    t_r4 = add_3d_text("Renta_Txt_Tels", "TELS:\n654-4036\n654-0853", 0.16, 0.015, (0.07, 12.00, 4.05), rot_cardenas, mats["espectacular_blanco_renta"], col, 'CENTER')
    objects.extend([t_r1, t_r2, t_r3, t_r4])

    # -----------------------------------------------------------------------
    # 4. PARTY RENTALS (KUROKY) (Y in [14.20, 19.30])
    # -----------------------------------------------------------------------
    # Puerta comercial a la DERECHA (menor Y: Y in [14.40, 15.45], Z in [0.00, 2.70 m])
    bm_party_p = bmesh.new()
    add_box(bm_party_p, 0.02, 0.12, 14.40, 15.45, 2.65, 2.70)
    add_box(bm_party_p, 0.02, 0.12, 14.40, 14.46, 0.00, 2.65)
    add_box(bm_party_p, 0.02, 0.12, 15.39, 15.45, 0.00, 2.65)
    add_box(bm_party_p, 0.04, 0.06, 14.46, 15.39, 0.00, 2.65)
    obj_party_p = create_mesh_object("Party_Puerta_Canceleria", bm_party_p, mats["aluminio_blanco"], col)
    objects.append(obj_party_p)

    # Ventanal con notas musicales al CENTRO / IZQUIERDA (Y in [15.60, 18.80], Z in [0.85, 2.70 m])
    bm_party_v = bmesh.new()
    add_box(bm_party_v, 0.04, 0.06, 15.60, 18.80, 0.85, 2.70)
    add_box(bm_party_v, 0.02, 0.15, 15.60, 18.80, 0.85, 0.90)
    add_box(bm_party_v, 0.02, 0.15, 15.60, 18.80, 2.65, 2.70)
    add_box(bm_party_v, 0.02, 0.15, 15.60, 15.65, 0.90, 2.65)
    add_box(bm_party_v, 0.02, 0.15, 18.75, 18.80, 0.90, 2.65)
    obj_party_v = create_mesh_object("Party_Vitrina_Vidrio", bm_party_v, mats["vidrio_comercial"], col)
    objects.append(obj_party_v)

    # Notas musicales impresas en el cristal
    bm_notas = bmesh.new()
    for franja in range(3):
        zn = 1.20 + franja * 0.48
        for nota in range(7):
            yn = 15.80 + nota * 0.42
            add_box(bm_notas, 0.03, 0.05, yn, yn + 0.04, zn, zn + 0.04)
            add_box(bm_notas, 0.03, 0.05, yn + 0.03, yn + 0.04, zn + 0.04, zn + 0.12)
            add_box(bm_notas, 0.03, 0.05, yn + 0.03, yn + 0.07, zn + 0.10, zn + 0.12)
    obj_notas = create_mesh_object("Party_Notas_Musicales_Vidrio", bm_notas, mats["notas_musicales"], col)
    objects.append(obj_notas)

    # Buzones amarillos en la acera
    bm_buzones = bmesh.new()
    add_box(bm_buzones, -0.40, -0.25, 14.60, 14.72, 0.00, 0.95)
    add_box(bm_buzones, -0.40, -0.25, 14.78, 14.90, 0.00, 0.85)
    obj_buzones = create_mesh_object("Party_Buzones_Amarillos", bm_buzones, mats["buzones_amarillos"], col)
    objects.append(obj_buzones)

    # PANEL RECTANGULAR BLANCO DE PARTY RENTALS (Y in [14.30, 19.10], Z in [3.05, 3.85 m])
    bm_party_rot = bmesh.new()
    add_box(bm_party_rot, -0.15, -0.05, 14.30, 19.10, 3.05, 3.85)
    obj_party_rot = create_mesh_object("Party_Panel_Rotulo_Blanco", bm_party_rot, mats["panel_blanco_party"], col)
    objects.append(obj_party_rot)

    # Lona publicitaria colorida con fotos a la IZQUIERDA (mayor Y: Y in [17.70, 19.00])
    bm_party_lona = bmesh.new()
    add_box(bm_party_lona, -0.17, -0.14, 17.70, 19.00, 3.10, 3.80)
    obj_party_lona = create_mesh_object("Party_Lona_Colorida_Fiestas", bm_party_lona, mats["lona_fotos_party"], col)
    objects.append(obj_party_lona)

    # Textos Party Rentals
    t_p1 = add_3d_text("Party_Txt_Title", "PARTY RENTALS", 0.28, 0.02, (-0.18, 16.10, 3.55), rot_cardenas, mats["letras_verdes_party"], col, 'CENTER')
    t_p2 = add_3d_text("Party_Txt_Kuroky", "KUROKY", 0.16, 0.015, (-0.18, 16.10, 3.35), rot_cardenas, mats["logo_kuroky_magenta"], col, 'CENTER')
    t_p3 = add_3d_text("Party_Txt_Col1", "SONIDO\nLUCES\nPANTALLAS", 0.08, 0.01, (-0.18, 14.75, 3.25), rot_cardenas, mats["letras_azules_party"], col, 'LEFT')
    t_p4 = add_3d_text("Party_Txt_Col2", "MESAS\nSILLAS\nMANTELES", 0.08, 0.01, (-0.18, 17.45, 3.25), rot_cardenas, mats["letras_azules_party"], col, 'RIGHT')
    objects.extend([t_p1, t_p2, t_p3, t_p4])

    # -----------------------------------------------------------------------
    # 5. LIBRERÍA ESPAÑA (Y in [0.00, 4.80])
    # -----------------------------------------------------------------------
    # Zócalo marrón y murete mostaza brillante (#E5B239)
    bm_lib_mur = bmesh.new()
    add_box(bm_lib_mur, -0.05, 0.42, 0.00, 4.80, 0.00, 0.15) # Zócalo marrón
    obj_lib_zoc = create_mesh_object("Libreria_Zocalo_Marron", bm_lib_mur, mats["zocalo_marron"], col)
    objects.append(obj_lib_zoc)

    bm_lib_mostaza = bmesh.new()
    add_box(bm_lib_mostaza, 0.00, 0.40, 1.10, 4.80, 0.15, 0.60) # Murete mostaza
    obj_lib_mostaza = create_mesh_object("Libreria_Murete_Mostaza", bm_lib_mostaza, mats["murete_mostaza_lib"], col)
    objects.append(obj_lib_mostaza)

    # Frente vidriado con libros y revistas (Y in [1.10, 4.75], Z in [0.60, 3.10 m])
    bm_lib_v = bmesh.new()
    add_box(bm_lib_v, 0.04, 0.06, 1.10, 4.75, 0.60, 3.10)
    add_box(bm_lib_v, 0.02, 0.12, 1.10, 4.75, 0.58, 0.62)
    add_box(bm_lib_v, 0.02, 0.12, 1.10, 4.75, 3.08, 3.12)
    add_box(bm_lib_v, 0.02, 0.12, 1.10, 1.15, 0.60, 3.10)
    add_box(bm_lib_v, 0.02, 0.12, 4.70, 4.75, 0.60, 3.10)
    add_box(bm_lib_v, 0.02, 0.12, 2.90, 2.95, 0.60, 3.10)
    obj_lib_v = create_mesh_object("Libreria_Escaparate_Vidrio", bm_lib_v, mats["vidrio_comercial"], col)
    objects.append(obj_lib_v)

    # Exhibidor de libros y revistas
    bm_lib_rev = bmesh.new()
    for row in range(5):
        zr = 0.70 + row * 0.45
        for col_i in range(8):
            yr = 1.25 + col_i * 0.42
            add_box(bm_lib_rev, 0.08, 0.15, yr, yr + 0.35, zr, zr + 0.38)
    add_box(bm_lib_rev, 0.07, 0.10, 1.20, 1.70, 1.50, 2.80) # Póster Virgen
    obj_lib_rev = create_mesh_object("Libreria_Exhibidor_Revistas", bm_lib_rev, mats["revistas_exhibidor"], col)
    objects.append(obj_lib_rev)

    # Puerta de acceso comercial peatonal (Y in [0.20, 1.10])
    bm_lib_p = bmesh.new()
    add_box(bm_lib_p, 0.02, 0.12, 0.20, 1.10, 3.08, 3.12)
    add_box(bm_lib_p, 0.02, 0.12, 0.20, 0.26, 0.00, 3.08)
    add_box(bm_lib_p, 0.02, 0.12, 1.04, 1.10, 0.00, 3.08)
    add_box(bm_lib_p, 0.04, 0.06, 0.26, 1.04, 0.00, 3.08)
    obj_lib_p = create_mesh_object("Libreria_Puerta_Aluminio", bm_lib_p, mats["aluminio_blanco"], col)
    objects.append(obj_lib_p)

    # Fascia marrón con textos dorados (Z in [3.10, 3.45 m])
    bm_lib_f = bmesh.new()
    add_box(bm_lib_f, -0.08, 0.42, 0.00, 4.80, 3.10, 3.45)
    obj_lib_f = create_mesh_object("Libreria_Fascia_Marron", bm_lib_f, mats["fascia_marron_lib"], col)
    objects.append(obj_lib_f)

    t_lib_f1 = add_3d_text("Libreria_Txt_Direccion", "PRESIDENTE CARDENAS 95-B Z.C. - TECATE, B.C.", 0.10, 0.01, (-0.10, 2.40, 3.25), rot_cardenas, mats["letras_doradas_lib"], col, 'CENTER')
    objects.append(t_lib_f1)

    # Letrero superior blanco enmarcado (Z in [3.45, 4.25 m])
    bm_lib_r = bmesh.new()
    add_box(bm_lib_r, -0.15, -0.05, 0.00, 4.80, 3.45, 4.25)
    add_box(bm_lib_r, -0.17, -0.03, -0.02, 4.82, 3.43, 3.47)
    add_box(bm_lib_r, -0.17, -0.03, -0.02, 4.82, 4.23, 4.27)
    add_box(bm_lib_r, -0.17, -0.03, -0.02, 0.02, 3.43, 4.27)
    add_box(bm_lib_r, -0.17, -0.03, 4.78, 4.82, 3.43, 4.27)
    obj_lib_r = create_mesh_object("Libreria_Panel_Rotulo_Blanco", bm_lib_r, mats["panel_rotulo_lib"], col)
    objects.append(obj_lib_r)

    t_lib1 = add_3d_text("Libreria_Txt_Nombre", "Librería España", 0.36, 0.025, (-0.18, 2.40, 3.82), rot_cardenas, mats["letras_negras_lib"], col, 'CENTER')
    t_lib2 = add_3d_text("Libreria_Txt_Sub", "• LIBROS • REVISTAS Y PERIODICOS •", 0.12, 0.015, (-0.18, 2.40, 3.56), rot_cardenas, mats["letras_rojas_lib"], col, 'CENTER')
    objects.extend([t_lib1, t_lib2])

    # Espectacular triangular de azotea: Cerveza Tecate / Bar Diana en diagonal (Y in [3.80, 4.80], Z in [4.30, 8.20 m])
    bm_tec = bmesh.new()
    add_box(bm_tec, 0.20, 0.35, 3.80, 4.75, 4.30, 8.20)
    add_box(bm_tec, 1.50, 1.65, 3.80, 4.75, 4.30, 8.20)
    add_box(bm_tec, 0.15, 0.30, 3.85, 4.70, 4.60, 8.10)
    obj_tec = create_mesh_object("Azotea_Espectacular_Tecate_Lona", bm_tec, mats["lona_blanca_tecate"], col)
    objects.append(obj_tec)

    bm_tec_l = bmesh.new()
    add_box(bm_tec_l, 0.12, 0.16, 4.10, 4.45, 7.30, 7.85)
    obj_tec_l = create_mesh_object("Azotea_Logo_Rojo_Tecate", bm_tec_l, mats["logo_rojo_tecate"], col)
    objects.append(obj_tec_l)

    t_tec1 = add_3d_text("Tecate_Txt_BarDiana", "Bar Diana\n1957\nCocktails", 0.20, 0.02, (0.10, 4.28, 5.80), rot_cardenas, mats["letras_negras_lib"], col, 'CENTER')
    objects.append(t_tec1)

    # -----------------------------------------------------------------------
    # 6. FLORERÍA ORQUÍDEA (Y in [19.30, 24.50])
    # -----------------------------------------------------------------------
    bm_orq_laja = bmesh.new()
    add_box(bm_orq_laja, -0.05, 0.45, 19.30, 24.50, 0.00, 0.65) # Zócalo laja café rojiza
    obj_orq_laja = create_mesh_object("Orquidea_Zocalo_Laja_Cafe", bm_orq_laja, mats["laja_rustica_orquidea"], col)
    objects.append(obj_orq_laja)

    bm_orq_pb = bmesh.new()
    add_box(bm_orq_pb, 0.04, 0.06, 19.45, 23.50, 0.65, 2.70)
    add_box(bm_orq_pb, 0.02, 0.15, 19.45, 23.50, 0.63, 0.67)
    add_box(bm_orq_pb, 0.02, 0.15, 19.45, 23.50, 2.68, 2.72)
    add_box(bm_orq_pb, 0.02, 0.15, 19.45, 19.50, 0.65, 2.70)
    add_box(bm_orq_pb, 0.02, 0.15, 23.45, 23.50, 0.65, 2.70)
    obj_orq_pb = create_mesh_object("Orquidea_Escaparate_PB", bm_orq_pb, mats["vidrio_comercial"], col)
    objects.append(obj_orq_pb)

    bm_flores = bmesh.new()
    for fl in range(6):
        yf = 19.80 + fl * 0.60
        add_box(bm_flores, 0.10, 0.25, yf, yf + 0.40, 0.80, 1.80)
    obj_flores = create_mesh_object("Orquidea_Arreglos_Florales", bm_flores, mats["mosaico_orquidea"], col)
    objects.append(obj_flores)

    return objects

# ---------------------------------------------------------------------------
# 4. Construcción de Fachada Libertad y Frontón Monumental
# ---------------------------------------------------------------------------

def build_libertad_facade(mats, col):
    """Construye minuciosamente la fachada sobre Callejón Libertad."""
    objects = []
    rot_libertad = (math.radians(90.0), 0.0, math.radians(180.0))

    # 1. FRONTÓN MONUMENTAL FLORERÍA ORQUÍDEA (H = 6.20 m, orientado al norte sobre Libertad)
    bm_fronton_m = bmesh.new()
    add_box(bm_fronton_m, -0.15, 0.45, 24.40, 24.85, 2.70, 6.20)  # Pilastra izquierda
    add_box(bm_fronton_m, 4.10, 4.60, 24.40, 24.85, 2.70, 6.20)   # Pilastra derecha
    add_box(bm_fronton_m, -0.20, 4.65, 24.40, 24.95, 5.75, 6.25)  # Dintel biselado
    add_box(bm_fronton_m, -0.20, 4.65, 24.40, 24.90, 2.65, 2.85)  # Marquesina
    obj_fronton_m = create_mesh_object("Orquidea_Fronton_Marco_Blanco", bm_fronton_m, mats["concreto_blanco"], col)
    objects.append(obj_fronton_m)

    bm_fronton_mos = bmesh.new()
    add_box(bm_fronton_mos, 0.45, 4.10, 24.45, 24.65, 2.85, 5.75) # Mosaico verde salvia moteado
    obj_fronton_mos = create_mesh_object("Orquidea_Fronton_Mosaico_Verde", bm_fronton_mos, mats["mosaico_orquidea"], col)
    objects.append(obj_fronton_mos)

    # Letrero de Florería Orquídea con greca perimetral roja
    bm_orq_rot = bmesh.new()
    add_box(bm_orq_rot, 1.10, 3.60, 24.66, 24.76, 3.30, 4.90) # Panel blanco
    # Greca roja perimetral
    add_box(bm_orq_rot, 1.05, 3.65, 24.74, 24.78, 3.25, 3.32)
    add_box(bm_orq_rot, 1.05, 3.65, 24.74, 24.78, 4.88, 4.95)
    add_box(bm_orq_rot, 1.05, 1.12, 24.74, 24.78, 3.25, 4.95)
    add_box(bm_orq_rot, 3.58, 3.65, 24.74, 24.78, 3.25, 4.95)
    obj_orq_rot = create_mesh_object("Orquidea_Panel_Rotulo_Blanco", bm_orq_rot, mats["panel_rotulo_orquidea"], col)
    objects.append(obj_orq_rot)

    t_or1 = add_3d_text("Orquidea_Txt_Floreria", "FLORERIA", 0.35, 0.02, (2.35, 24.80, 4.35), rot_libertad, mats["letras_purpura_orquidea"], col, 'CENTER')
    t_or2 = add_3d_text("Orquidea_Txt_Orquidea", "ORQUIDEA", 0.40, 0.025, (2.35, 24.80, 3.80), rot_libertad, mats["letras_purpura_orquidea"], col, 'CENTER')
    t_or3 = add_3d_text("Orquidea_Txt_Tel", "Teléfono 654-10-51", 0.10, 0.01, (2.35, 24.80, 3.45), rot_libertad, mats["letras_purpura_orquidea"], col, 'CENTER')
    objects.extend([t_or1, t_or2, t_or3])

    # Puerta acristalada y zócalo sobre Libertad
    bm_orq_lib_p = bmesh.new()
    add_box(bm_orq_lib_p, 2.40, 3.80, 24.40, 24.55, 2.60, 2.65)
    add_box(bm_orq_lib_p, 2.40, 2.46, 24.40, 24.55, 0.00, 2.60)
    add_box(bm_orq_lib_p, 3.74, 3.80, 24.40, 24.55, 0.00, 2.60)
    add_box(bm_orq_lib_p, 3.07, 3.13, 24.40, 24.55, 0.00, 2.60)
    add_box(bm_orq_lib_p, 2.46, 3.74, 24.45, 24.48, 0.00, 2.60)
    add_box(bm_orq_lib_p, 0.00, 2.40, 24.35, 24.60, 0.00, 0.65) # Laja café rojiza
    obj_orq_lib_p = create_mesh_object("Orquidea_PB_Libertad", bm_orq_lib_p, mats["aluminio_blanco"], col)
    objects.append(obj_orq_lib_p)

    # 2. FOTO ESTUDIO CURIEL (X in [4.50, 16.50 m], Y = 24.50 m)
    bm_curiel_m = bmesh.new()
    add_box(bm_curiel_m, 4.50, 16.50, 24.00, 24.50, 0.00, 4.30) # Muro blanco estuco
    obj_curiel_m = create_mesh_object("Curiel_Muro_Blanco", bm_curiel_m, mats["estuco_blanco_curiel"], col)
    objects.append(obj_curiel_m)

    bm_cur_zoc = bmesh.new()
    add_box(bm_cur_zoc, 4.50, 16.50, 24.00, 24.55, 0.00, 0.20) # Zócalo marrón
    obj_cur_zoc = create_mesh_object("Curiel_Zocalo_Marron", bm_cur_zoc, mats["zocalo_marron"], col)
    objects.append(obj_cur_zoc)

    # Marquesina Streamline con 3 estrías metálicas
    bm_curiel_marq = bmesh.new()
    add_box(bm_curiel_marq, 4.40, 16.50, 24.50, 25.40, 2.70, 2.95)
    for est in range(3):
        ze = 2.73 + est * 0.07
        add_box(bm_curiel_marq, 4.35, 16.55, 25.40, 25.45, ze, ze + 0.03)
    obj_curiel_marq = create_mesh_object("Curiel_Marquesina_Streamline", bm_curiel_marq, mats["moldura_streamline"], col)
    objects.append(obj_curiel_marq)

    # Puerta y vitrina PB
    bm_curiel_pb = bmesh.new()
    add_box(bm_curiel_pb, 6.50, 12.00, 24.45, 24.55, 1.00, 2.45)
    add_box(bm_curiel_pb, 13.50, 14.80, 24.45, 24.55, 0.00, 2.65)
    obj_curiel_pb = create_mesh_object("Curiel_Canceleria_PB", bm_curiel_pb, mats["vidrio_comercial"], col)
    objects.append(obj_curiel_pb)

    # Rótulos Foto Estudio Curiel
    t_c1 = add_3d_text("Curiel_Txt_FotoStudio", "FOTO STUDIO", 0.35, 0.025, (10.50, 24.55, 3.75), rot_libertad, mats["letras_azul_curiel"], col, 'CENTER')
    t_c2 = add_3d_text("Curiel_Txt_Curiel", "CURIEL", 0.42, 0.03, (10.50, 24.55, 3.25), rot_libertad, mats["letras_dorado_curiel"], col, 'CENTER')
    t_c3 = add_3d_text("Curiel_Txt_Muro", "FOTO STUDIO\nCURIEL", 0.18, 0.015, (12.80, 24.55, 1.95), rot_libertad, mats["totem_rojo_curiel"], col, 'CENTER')
    objects.extend([t_c1, t_c2, t_c3])

    # Tótem vertical rojo bermellón en esquina
    bm_totem = bmesh.new()
    add_box(bm_totem, 15.45, 15.55, 24.55, 24.65, 0.00, 1.80)
    add_box(bm_totem, 15.25, 15.75, 24.50, 24.80, 1.80, 4.50)
    obj_totem = create_mesh_object("Curiel_Totem_Rojo", bm_totem, mats["totem_rojo_curiel"], col)
    objects.append(obj_totem)

    t_tot1 = add_3d_text("Curiel_Txt_Totem_N", "F\nO\nT\nO", 0.40, 0.02, (15.50, 24.82, 3.10), rot_libertad, mats["concreto_blanco"], col, 'CENTER')
    rot_sur = (math.radians(90.0), 0.0, 0.0)
    t_tot2 = add_3d_text("Curiel_Txt_Totem_S", "F\nO\nT\nO", 0.40, 0.02, (15.50, 24.48, 3.10), rot_sur, mats["concreto_blanco"], col, 'CENTER')
    objects.extend([t_tot1, t_tot2])

    return objects

# ---------------------------------------------------------------------------
# 5. Fachada Posterior (Estacionamiento BBVA)
# ---------------------------------------------------------------------------

def build_rear_parking_facade(mats, col):
    """Construye la fachada poniente (X = 16.50 m) visible desde el estacionamiento interior del BBVA."""
    objects = []
    rot_estacionamiento = (math.radians(90.0), 0.0, math.radians(90.0))

    bm_rear = bmesh.new()
    add_box(bm_rear, 16.20, 16.50, 0.00, 24.50, 0.00, 4.20)
    obj_rear = create_mesh_object("Posterior_Muro_Servicio", bm_rear, mats["estuco_blanco_curiel"], col)
    objects.append(obj_rear)

    bm_rear_marq = bmesh.new()
    add_box(bm_rear_marq, 16.50, 17.80, 4.80, 9.10, 2.70, 2.90)
    add_box(bm_rear_marq, 16.48, 16.55, 6.50, 7.80, 0.00, 2.20)
    obj_rear_marq = create_mesh_object("Posterior_Marquesina_Diana", bm_rear_marq, mats["concreto_marquesina"], col)
    objects.append(obj_rear_marq)

    t_salida = add_3d_text("Posterior_Txt_Salida", "Salida", 0.18, 0.015, (16.55, 7.15, 2.35), rot_estacionamiento, mats["greca_roja_orquidea"], col, 'CENTER')
    t_diana_post = add_3d_text("Posterior_Txt_BarDiana", "BAR TURISTICO Diana", 0.28, 0.02, (16.55, 6.95, 3.65), rot_estacionamiento, mats["rotulo_diana_dorado"], col, 'CENTER')
    objects.extend([t_salida, t_diana_post])

    bm_reja = bmesh.new()
    add_box(bm_reja, 16.50, 20.80, 6.95, 7.05, 0.00, 1.80)
    add_box(bm_reja, 16.50, 20.80, 13.95, 14.05, 0.00, 1.80)
    add_box(bm_reja, 20.75, 20.85, 7.00, 14.00, 0.00, 1.80)
    for rx in range(14):
        pos_rx = 16.60 + rx * 0.30
        add_box(bm_reja, pos_rx, pos_rx + 0.04, 6.95, 7.05, 0.00, 1.80)
        add_box(bm_reja, pos_rx, pos_rx + 0.04, 13.95, 14.05, 0.00, 1.80)
    for ry in range(22):
        pos_ry = 7.10 + ry * 0.31
        add_box(bm_reja, 20.75, 20.85, pos_ry, pos_ry + 0.04, 0.00, 1.80)
    obj_reja = create_mesh_object("Posterior_Reja_Terraza", bm_reja, mats["aluminio_negro"], col)
    objects.append(obj_reja)

    bm_med = bmesh.new()
    add_box(bm_med, 0.00, 16.50, -0.05, 0.05, 0.00, 4.30) # Medianera continua
    obj_med = create_mesh_object("Medianera_Sur_Enrase_BBVA", bm_med, mats["estuco_blanco_curiel"], col)
    objects.append(obj_med)

    bm_techo = bmesh.new()
    add_box(bm_techo, 0.00, 16.50, 0.00, 24.50, 3.80, 3.90)
    obj_techo = create_mesh_object("Azotea_Cubierta_Impermeable", bm_techo, mats["techo_impermeable"], col)
    objects.append(obj_techo)

    return objects

# ---------------------------------------------------------------------------
# 6. Iluminación Diurna y Cámaras Calibradas
# ---------------------------------------------------------------------------

def setup_lighting_and_cameras(col):
    """Configura iluminación diurna con cielo brillante y luz de rebote para eliminar sombras negras."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720

    # 1. Cielo Diurno (World Environment)
    world = bpy.data.worlds.new("World_Tecate_Day")
    scene.world = world
    world.use_nodes = True
    w_nodes = world.node_tree.nodes
    w_nodes.clear()
    w_out = w_nodes.new(type='ShaderNodeOutputWorld')
    w_bg = w_nodes.new(type='ShaderNodeBackground')
    w_bg.inputs['Color'].default_value = (0.58, 0.76, 0.95, 1.0) # Azul cielo diurno
    w_bg.inputs['Strength'].default_value = 1.4
    world.node_tree.links.new(w_bg.outputs['Background'], w_out.inputs['Surface'])

    # 2. Sol Cenital Exterior
    sun_data = bpy.data.lights.new(name="Sun_Exterior", type='SUN')
    sun_data.energy = 4.0
    sun_data.color = (1.0, 0.98, 0.94)
    sun_obj = bpy.data.objects.new("Sun_Exterior", sun_data)
    col.objects.link(sun_obj)
    sun_obj.location = Vector((-10.0, 12.0, 20.0))
    sun_obj.rotation_euler = Euler((math.radians(45.0), math.radians(20.0), math.radians(-35.0)), 'XYZ')

    # 3. Luz de Relleno Frontal (elimina sombras oscuras bajo marquesinas)
    fill_data = bpy.data.lights.new(name="Sun_Fill_Frontal", type='SUN')
    fill_data.energy = 2.0
    fill_data.color = (0.90, 0.94, 1.0)
    fill_obj = bpy.data.objects.new("Sun_Fill_Frontal", fill_data)
    col.objects.link(fill_obj)
    fill_obj.location = Vector((-20.0, 12.0, 5.0))
    fill_obj.rotation_euler = Euler((math.radians(15.0), 0.0, math.radians(-90.0)), 'XYZ')

    # 4. Luz de Relleno Norte (ilumina fachada de Libertad)
    north_data = bpy.data.lights.new(name="Sun_Fill_North", type='SUN')
    north_data.energy = 2.5
    north_data.color = (0.92, 0.95, 1.0)
    north_obj = bpy.data.objects.new("Sun_Fill_North", north_data)
    col.objects.link(north_obj)
    north_obj.location = Vector((8.0, 35.0, 15.0))
    north_obj.rotation_euler = Euler((math.radians(-35.0), 0.0, math.radians(180.0)), 'XYZ')

    # Batería de 6 cámaras calibradas:
    cams_config = [
        # 1. Frontal completa idéntica a media_1790243320877.png y media_1790241121751.png
        ("Cam_Cardenas_Frontal_V4", (-15.5, 12.5, 2.6), (0.0, 12.5, 2.6), 30.0),
        # 2. Encuadre exacto de Florería Orquídea idéntico a media_1790243423150.jpg
        ("Cam_Orquidea_Libertad_V4", (2.35, 33.5, 2.8), (2.35, 24.5, 3.4), 38.0),
        # 3. Encuadre de Foto Estudio Curiel idéntico a DcOz2fF61YH1bc6cN7zlrA_yaw_354.12.png
        ("Cam_Curiel_Libertad_V4", (10.5, 33.5, 2.8), (10.5, 24.5, 2.8), 32.0),
        # 4. Acercamiento detallado a Bar Diana (fachaleta, puerta verde, Diana Cazadora)
        ("Cam_Diana_Closeup_V4", (-7.5, 7.0, 2.3), (0.0, 7.0, 2.5), 42.0),
        # 5. Acercamiento detallado a Librería España (revistas, libros, fascia y Tecate)
        ("Cam_Libreria_Espana_V4", (-8.0, 2.4, 3.2), (0.0, 2.4, 3.2), 38.0),
        # 6. Vista posterior desde el estacionamiento interior del BBVA
        ("Cam_Reverso_Estacionamiento_V4", (24.0, 10.0, 5.0), (16.5, 10.0, 2.5), 32.0),
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
# 7. Generación de Escena Godot 4 (.tscn)
# ---------------------------------------------------------------------------

def generate_godot_tscn(tscn_path, glb_path_rel):
    """Genera la escena de Godot 4 con colisionadores BoxShape3D analíticos en Z negativo concordante."""
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
size = Vector3(9.2, 6.5, 5.2)

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
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 4.60, 3.25, -21.90)
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
# 8. Función Principal
# ---------------------------------------------------------------------------

def main():
    print("=== INICIANDO RECONSTRUCCIÓN PROCEDURAL: PDTE. LÁZARO CÁRDENAS 33 V4.1 ===")
    root_col = clean_scene()
    mats = create_materials()

    objs_cardenas = build_cardenas_facade(mats, root_col)
    objs_libertad = build_libertad_facade(mats, root_col)
    objs_rear = build_rear_parking_facade(mats, root_col)
    print(f"[OK] Cuerpos arquitectónicos construidos ({len(objs_cardenas) + len(objs_libertad) + len(objs_rear)} objetos)")

    cams = setup_lighting_and_cameras(root_col)
    print(f"[OK] Cámaras y luces configuradas ({len(cams)} cámaras)")

    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    blend_path = os.path.join(base_dir, "blender_assets", "buildings", "edificio_cardenas_33.blend")
    glb_path = os.path.join(base_dir, "godot_project", "assets", "buildings", "edificio_cardenas_33.glb")
    tscn_path = os.path.join(base_dir, "godot_project", "assets", "buildings", "edificio_cardenas_33.tscn")
    images_dir = os.path.join(base_dir, "docs", "images", "cardenas_33")
    os.makedirs(images_dir, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"[OK] Archivo maestro Blender guardado: {blend_path}")

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

    generate_godot_tscn(tscn_path, "res://assets/buildings/edificio_cardenas_33.glb")

    scene = bpy.context.scene
    for cam_name, cam_obj in cams.items():
        render_output = os.path.join(images_dir, f"{cam_name}.png")
        scene.camera = cam_obj
        scene.render.filepath = render_output
        print(f"Renderizando {cam_name} -> {render_output}...")
        bpy.ops.render.render(write_still=True)
        print(f"[OK] Render completado: {render_output}")

    print("=== RECONSTRUCCIÓN PROCEDURAL COMPLETADA EXITOSAMENTE V4.1 ===")

if __name__ == "__main__":
    main()
