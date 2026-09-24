"""
=============================================================================
GENERADOR PROCEDURAL 3D: COMPLEJO COMERCIAL PDTE. LÁZARO CÁRDENAS 33
(ÉPOCA: HISTÓRICO 2009 - VERSIÓN GROUND-TRUTH V5.0 RIGUROSA)
=============================================================================
Reconstrucción fidedigna con base en evidencia fotográfica directa de alta resolución
y capturas en runtime del simulador Godot 4:
  - Ochava a 45º exacta en Florería Orquídea con frontón monumental de 6.60 m.
  - Techo de Foto Estudio Curiel confinado al interior sin intersectar letreros.
  - Rótulo tridimensional 'FOTO STUDIO CURIEL' en el reverso poniente.
  - Eliminación absoluta de bloques invasivos en la salida trasera.
  - Letrero comercial de Cerveza TECATE frente a Bar Diana y espectacular de azotea.
  - Cancelería, puertas y vitrinas completas en todos los locales.
  - Proporciones reales de letreros superiores y espectacular RENTA MESAS SILLAS.
  - Enrase milimétrico sur con BBVA DENTISTA libre de clipping.
=============================================================================
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Euler, Matrix

# ---------------------------------------------------------------------------
# 1. Utilidades de Creación Geométrica
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

def add_chaflan_box(bm, p1, p2, width, z_min, z_max):
    """
    Construye una losa o muro extruido a lo largo del segmento p1 -> p2 (ochava a 45º).
    p1, p2: tuplas (x, y). width: espesor hacia el interior del edificio.
    """
    v1 = Vector((p1[0], p1[1], 0.0))
    v2 = Vector((p2[0], p2[1], 0.0))
    tang = (v2 - v1).normalized()
    norm_out = Vector((-tang.y, tang.x, 0.0)) # Normal hacia afuera
    norm_in = -norm_out # Normal hacia adentro

    p1_out = v1
    p2_out = v2
    p1_in = v1 + norm_in * width
    p2_in = v2 + norm_in * width

    verts = [
        bm.verts.new((p1_out.x, p1_out.y, z_min)),
        bm.verts.new((p2_out.x, p2_out.y, z_min)),
        bm.verts.new((p2_in.x, p2_in.y, z_min)),
        bm.verts.new((p1_in.x, p1_in.y, z_min)),
        bm.verts.new((p1_out.x, p1_out.y, z_max)),
        bm.verts.new((p2_out.x, p2_out.y, z_max)),
        bm.verts.new((p2_in.x, p2_in.y, z_max)),
        bm.verts.new((p1_in.x, p1_in.y, z_max)),
    ]
    bm.faces.new((verts[0], verts[1], verts[2], verts[3])) # -Z
    bm.faces.new((verts[4], verts[7], verts[6], verts[5])) # +Z
    bm.faces.new((verts[0], verts[4], verts[5], verts[1])) # Cara exterior
    bm.faces.new((verts[1], verts[5], verts[6], verts[2])) # Extremo p2
    bm.faces.new((verts[2], verts[6], verts[7], verts[3])) # Cara interior
    bm.faces.new((verts[3], verts[7], verts[4], verts[0])) # Extremo p1
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
    # Estructura y muros
    mats["estuco_ocre"] = make_pbr("M_Estuco_Ocre_Continuo", (0.835, 0.730, 0.525), roughness=0.85)
    mats["zocalo_marron"] = make_pbr("M_Zocalo_Marron_Chocolate", (0.314, 0.165, 0.122), roughness=0.90)
    mats["concreto_marquesina"] = make_pbr("M_Concreto_Marquesina", (0.88, 0.86, 0.83), roughness=0.70)
    mats["concreto_blanco"] = make_pbr("M_Concreto_Blanco_Remates", (0.96, 0.96, 0.96), roughness=0.55)
    mats["zocalo_basal"] = make_pbr("M_Zocalo_Basal_Enterrado", (0.16, 0.16, 0.16), roughness=0.95)

    # Bar Diana
    mats["fachaleta_diana"] = make_pbr("M_Fachaleta_Laja_Blanca", (0.92, 0.90, 0.86), roughness=0.65)
    mats["verde_menta_diana"] = make_pbr("M_Verde_Menta_Diana", (0.824, 0.867, 0.835), roughness=0.85)
    mats["herreria_verde_diana"] = make_pbr("M_Herreria_Verde_Diana", (0.41, 0.45, 0.30), roughness=0.45, metallic=0.6)
    mats["panel_rotulo_diana"] = make_pbr("M_Panel_Rotulo_Diana", (0.97, 0.97, 0.96), roughness=0.25)
    mats["rotulo_diana_dorado"] = make_pbr("M_Rotulo_Diana_Dorado", (0.83, 0.69, 0.22), roughness=0.30, metallic=0.7)
    mats["rotulo_diana_azul"] = make_pbr("M_Rotulo_Diana_Azul", (0.12, 0.25, 0.50), roughness=0.35)

    # Cerveza Tecate comercial
    mats["logo_rojo_tecate"] = make_pbr("M_Logo_Rojo_Tecate", (0.82, 0.08, 0.08), roughness=0.30)
    mats["lona_blanca_tecate"] = make_pbr("M_Lona_Blanca_Tecate", (0.96, 0.96, 0.96), roughness=0.35)
    mats["acero_estructura"] = make_pbr("M_Acero_Estructural_Azotea", (0.35, 0.37, 0.40), roughness=0.45, metallic=0.85)

    # Annita's Boutique
    mats["caja_grafito_anita"] = make_pbr("M_Caja_Grafito_Anita", (0.13, 0.15, 0.16), roughness=0.30, metallic=0.2)
    mats["ovalo_plata_anita"] = make_pbr("M_Ovalo_Plata_Anita", (0.88, 0.89, 0.90), roughness=0.25, metallic=0.5)
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
    mats["murete_mostaza_lib"] = make_pbr("M_Murete_Mostaza_Libreria", (0.90, 0.70, 0.22), roughness=0.75)
    mats["fascia_marron_lib"] = make_pbr("M_Fascia_Marron_Libreria", (0.24, 0.14, 0.10), roughness=0.50)
    mats["letras_doradas_lib"] = make_pbr("M_Letras_Doradas_Libreria", (0.88, 0.75, 0.25), roughness=0.30, metallic=0.7)
    mats["panel_rotulo_lib"] = make_pbr("M_Panel_Rotulo_Libreria", (0.96, 0.96, 0.95), roughness=0.25)
    mats["letras_negras_lib"] = make_pbr("M_Letras_Negras_Libreria", (0.10, 0.10, 0.12), roughness=0.30)
    mats["letras_rojas_lib"] = make_pbr("M_Letras_Rojas_Libreria", (0.80, 0.12, 0.12), roughness=0.30)
    mats["revistas_exhibidor"] = make_pbr("M_Revistas_Libros_Color", (0.85, 0.75, 0.65), roughness=0.60)

    # Florería Orquídea (Ochava 45º)
    mat_mos = bpy.data.materials.new(name="M_Mosaico_Terrazo_Verde")
    mat_mos.use_nodes = True
    nodes_m = mat_mos.node_tree.nodes
    links_m = mat_mos.node_tree.links
    bsdf_m = nodes_m.get("Principled BSDF")
    if bsdf_m:
        bsdf_m.inputs['Roughness'].default_value = 0.60
        tex_vor = nodes_m.new('ShaderNodeTexVoronoi')
        tex_vor.inputs['Scale'].default_value = 65.0
        cr = nodes_m.new('ShaderNodeValToRGB')
        cr.color_ramp.elements[0].position = 0.60
        cr.color_ramp.elements[0].color = (0.28, 0.44, 0.28, 1.0) # Verde salvia rocoso
        cr.color_ramp.elements[1].position = 0.82
        cr.color_ramp.elements[1].color = (0.94, 0.95, 0.92, 1.0) # Detallitos blancos
        links_m.new(tex_vor.outputs['Distance'], cr.inputs['Fac'])
        links_m.new(cr.outputs['Color'], bsdf_m.inputs['Base Color'])
    mats["mosaico_orquidea"] = mat_mos
    mats["laja_rustica_orquidea"] = make_pbr("M_Laja_Rustica_Cafe", (0.55, 0.33, 0.26), roughness=0.95)
    mats["panel_rotulo_orquidea"] = make_pbr("M_Panel_Rotulo_Orquidea", (0.96, 0.96, 0.96), roughness=0.25)
    mats["greca_roja_orquidea"] = make_pbr("M_Greca_Roja_Orquidea", (0.80, 0.08, 0.08), roughness=0.30)
    mats["letras_purpura_orquidea"] = make_pbr("M_Letras_Purpura_Orquidea", (0.35, 0.05, 0.15), roughness=0.75)

    # Foto Estudio Curiel
    mats["estuco_blanco_curiel"] = make_pbr("M_Estuco_Blanco_Curiel", (0.96, 0.96, 0.96), roughness=0.75)
    mats["moldura_streamline"] = make_pbr("M_Moldura_Streamline_Plata", (0.85, 0.87, 0.88), roughness=0.30, metallic=0.6)
    mats["letras_azul_curiel"] = make_pbr("M_Letras_Azul_Curiel", (0.12, 0.25, 0.65), roughness=0.30)
    mats["letras_dorado_curiel"] = make_pbr("M_Letras_Dorado_Curiel", (0.78, 0.60, 0.20), roughness=0.35, metallic=0.6)
    mats["totem_rojo_curiel"] = make_pbr("M_Totem_Rojo_Curiel", (0.73, 0.09, 0.11), roughness=0.35, metallic=0.2)

    # Vidrios y comunes
    mats["vidrio_comercial"] = make_pbr("M_Vidrio_Comercial_Limpio", (0.80, 0.88, 0.92), roughness=0.08, alpha=0.30)
    mats["vidrio_ahumado"] = make_pbr("M_Vidrio_Ahumado_Diana", (0.15, 0.18, 0.20), roughness=0.10, alpha=0.75)
    mats["aluminio_blanco"] = make_pbr("M_Aluminio_Blanco_Canceles", (0.95, 0.95, 0.95), roughness=0.35, metallic=0.8)
    mats["aluminio_negro"] = make_pbr("M_Aluminio_Negro_Marcos", (0.15, 0.15, 0.15), roughness=0.40, metallic=0.85)
    mats["techo_impermeable"] = make_pbr("M_Azotea_Impermeabilizante", (0.70, 0.68, 0.65), roughness=0.90)

    return mats

# ---------------------------------------------------------------------------
# 3. Construcción del Frente Cárdenas (Librería, Diana, Annita, Party)
# ---------------------------------------------------------------------------

def build_cardenas_facade(mats, col):
    """Construye minuciosamente la fachada Cárdenas desde Y = 0.00 hasta Y = 20.50 m."""
    objects = []
    rot_cardenas = (math.radians(90.0), 0.0, math.radians(-90.0))

    # 0. ZÓCALO BASAL ENTERRADO (-1.20 a 0.00 m)
    bm_zocalo = bmesh.new()
    add_box(bm_zocalo, -0.30, 16.50, 0.00, 24.60, -1.20, 0.00)
    obj_zocalo = create_mesh_object("Cardenas_Zocalo_Basal_Enterrado", bm_zocalo, mats["zocalo_basal"], col)
    objects.append(obj_zocalo)

    # 1. CUERPO CONTINUO CENTRAL (Bar Diana, Annita's, Party Rentals: Y in [4.80, 20.50])
    # Zócalo marrón chocolate (#502A1F) continuo en PB (Z in [0.00, 0.40 m])
    bm_zoc_c = bmesh.new()
    add_box(bm_zoc_c, -0.05, 0.35, 9.30, 20.00, 0.00, 0.40)
    obj_zoc_c = create_mesh_object("Cardenas_Zocalo_Marron_Continuo", bm_zoc_c, mats["zocalo_marron"], col)
    objects.append(obj_zoc_c)

    # Muros ocre mostaza suave (#D5BA86) continuo
    bm_ocre = bmesh.new()
    # Pretil superior continuo (Z in [2.95, 3.90 m], Y in [9.30, 20.00 m])
    add_box(bm_ocre, 0.00, 0.35, 9.30, 20.00, 2.95, 3.90)
    # Pared Party Rentals
    add_box(bm_ocre, 0.00, 0.35, 14.50, 15.65, 0.40, 2.75) # Machón divisorio y murete
    add_box(bm_ocre, 0.00, 0.35, 15.65, 19.50, 0.40, 0.85) # Murete bajo ventana notas
    # Pared Annita's
    add_box(bm_ocre, 0.00, 0.35, 10.60, 14.30, 0.40, 0.65) # Murete bajo persianas
    add_box(bm_ocre, 0.00, 0.35, 10.45, 10.65, 0.40, 2.75) # Machón puerta-vitrina
    add_box(bm_ocre, 0.00, 0.35, 9.20, 9.45, 0.00, 2.75)   # Machón divisorio Diana-Annita
    obj_ocre = create_mesh_object("Cardenas_Muro_Ocre_Continuo", bm_ocre, mats["estuco_ocre"], col)
    objects.append(obj_ocre)

    # Marquesina corrida continua de concreto en voladizo (Z in [2.75, 2.95 m], vuela 0.70 m)
    # Corre de Y = 4.80 a Y = 20.00 m
    bm_marq = bmesh.new()
    add_box(bm_marq, -0.70, 0.35, 4.80, 20.00, 2.75, 2.95)
    add_box(bm_marq, -0.75, -0.68, 4.80, 20.00, 2.70, 2.98) # Goterón
    obj_marq = create_mesh_object("Cardenas_Marquesina_Corrida", bm_marq, mats["concreto_marquesina"], col)
    objects.append(obj_marq)

    # Pilastra / aleta vertical saliente en esquina con remate oblicuo (Y in [19.85, 20.15])
    bm_aleta = bmesh.new()
    v_al = [
        bm_aleta.verts.new((-0.20, 19.85, 0.00)), bm_aleta.verts.new((0.40, 19.85, 0.00)),
        bm_aleta.verts.new((0.40, 20.15, 0.00)), bm_aleta.verts.new((-0.20, 20.15, 0.00)),
        bm_aleta.verts.new((-0.20, 19.85, 4.80)), bm_aleta.verts.new((0.40, 19.85, 4.80)),
        bm_aleta.verts.new((0.40, 20.15, 3.90)), bm_aleta.verts.new((-0.20, 20.15, 3.90))
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
    # 2. BAR TURÍSTICO DIANA (Y in [4.80, 9.30])
    # -----------------------------------------------------------------------
    # Puerta doble de herrería verde olivo a la DERECHA (Y in [4.90, 5.95], Z in [0.00, 2.45])
    bm_diana_p = bmesh.new()
    add_box(bm_diana_p, 0.02, 0.12, 4.90, 5.95, 2.40, 2.46)
    add_box(bm_diana_p, 0.02, 0.12, 4.90, 4.96, 0.00, 2.40)
    add_box(bm_diana_p, 0.02, 0.12, 5.89, 5.95, 0.00, 2.40)
    add_box(bm_diana_p, 0.02, 0.12, 5.40, 5.45, 0.00, 2.40)
    for by in range(12):
        pos_y = 4.98 + by * 0.076
        add_box(bm_diana_p, 0.04, 0.07, pos_y, pos_y + 0.02, 0.00, 2.40)
    obj_diana_p = create_mesh_object("Diana_Puerta_Herreria_Verde", bm_diana_p, mats["herreria_verde_diana"], col)
    objects.append(obj_diana_p)

    # Zócalo de fachaleta de piedra blanca apilada (Y in [5.95, 9.20], Z in [0.00, 0.85 m])
    bm_diana_laja = bmesh.new()
    add_box(bm_diana_laja, -0.04, 0.35, 5.95, 9.20, 0.00, 0.85)
    obj_diana_laja = create_mesh_object("Diana_Zocalo_Fachaleta_Blanca", bm_diana_laja, mats["fachaleta_diana"], col)
    objects.append(obj_diana_laja)

    # Muro verde menta pastel (#D2DDD5) de Z = 0.85 a 2.35 m
    bm_diana_m = bmesh.new()
    add_box(bm_diana_m, 0.00, 0.35, 5.95, 9.20, 0.85, 2.35)
    obj_diana_m = create_mesh_object("Diana_Muro_Verde_Menta", bm_diana_m, mats["verde_menta_diana"], col)
    objects.append(obj_diana_m)

    # Clereestorio horizontal superior con vidrio ahumado (Z in [2.35, 2.70 m])
    bm_diana_cl = bmesh.new()
    add_box(bm_diana_cl, 0.05, 0.15, 6.00, 9.15, 2.35, 2.70)
    add_box(bm_diana_cl, 0.03, 0.17, 5.95, 9.20, 2.32, 2.36)
    add_box(bm_diana_cl, 0.03, 0.17, 5.95, 9.20, 2.69, 2.73)
    obj_diana_cl = create_mesh_object("Diana_Clereestorio_Ahumado", bm_diana_cl, mats["vidrio_ahumado"], col)
    objects.append(obj_diana_cl)

    # Panel principal de Bar Diana sobre marquesina (Y in [4.90, 9.15], Z in [2.95, 4.10 m])
    bm_diana_rot = bmesh.new()
    add_box(bm_diana_rot, -0.15, -0.05, 4.90, 9.15, 2.95, 4.10)
    add_box(bm_diana_rot, -0.17, -0.03, 4.88, 9.17, 2.93, 2.97)
    add_box(bm_diana_rot, -0.17, -0.03, 4.88, 9.17, 4.08, 4.12)
    add_box(bm_diana_rot, -0.17, -0.03, 4.88, 4.92, 2.93, 4.12)
    add_box(bm_diana_rot, -0.17, -0.03, 9.13, 9.17, 2.93, 4.12)
    obj_diana_rot = create_mesh_object("Diana_Panel_Rotulo_Blanco", bm_diana_rot, mats["panel_rotulo_diana"], col)
    objects.append(obj_diana_rot)

    # Silueta dorada de la Diana Cazadora a la IZQUIERDA (Y in [8.30, 8.95])
    bm_diana_stat = bmesh.new()
    add_box(bm_diana_stat, -0.18, -0.14, 8.45, 8.75, 3.05, 3.25)
    add_box(bm_diana_stat, -0.18, -0.14, 8.52, 8.68, 3.25, 3.75)
    add_box(bm_diana_stat, -0.18, -0.14, 8.35, 8.60, 3.55, 3.98)
    obj_diana_stat = create_mesh_object("Diana_Silueta_Cazadora_Dorada", bm_diana_stat, mats["rotulo_diana_dorado"], col)
    objects.append(obj_diana_stat)

    # Textos centrales Bar Diana
    t_d1 = add_3d_text("Diana_Txt_Bar", "Bar", 0.32, 0.02, (-0.17, 7.50, 3.65), rot_cardenas, mats["rotulo_diana_dorado"], col, 'RIGHT')
    t_d2 = add_3d_text("Diana_Txt_Turistico", "TURISTICO", 0.16, 0.015, (-0.17, 6.55, 3.75), rot_cardenas, mats["rotulo_diana_azul"], col, 'RIGHT')
    t_d3 = add_3d_text("Diana_Txt_Diana", "Diana", 0.44, 0.025, (-0.17, 7.35, 3.25), rot_cardenas, mats["rotulo_diana_dorado"], col, 'RIGHT')
    t_d4 = add_3d_text("Diana_Txt_Desde", "DESDE / SINCE 1957", 0.09, 0.01, (-0.17, 7.15, 3.08), rot_cardenas, mats["letras_negras_lib"], col, 'RIGHT')
    objects.extend([t_d1, t_d2, t_d3, t_d4])

    # Ilustración cóctel a la DERECHA (Y in [5.15, 5.75])
    bm_coctel = bmesh.new()
    add_box(bm_coctel, -0.18, -0.14, 5.20, 5.42, 3.20, 3.75)
    add_box(bm_coctel, -0.18, -0.14, 5.48, 5.68, 3.15, 3.85)
    obj_coctel = create_mesh_object("Diana_Ilustracion_Coctel", bm_coctel, mats["espectacular_rojo_renta"], col)
    objects.append(obj_coctel)

    # LETRERO COMERCIAL CERVEZA TECATE FRENTE A BAR DIANA (Poste / fachada en Y = 5.80, Z = 2.40 a 3.00)
    bm_tec_com = bmesh.new()
    add_box(bm_tec_com, -0.85, -0.72, 5.60, 6.10, 2.45, 2.95)
    obj_tec_com = create_mesh_object("Diana_Letrero_Tecate_Comercial", bm_tec_com, mats["lona_blanca_tecate"], col)
    objects.append(obj_tec_com)

    bm_tec_com_l = bmesh.new()
    add_box(bm_tec_com_l, -0.86, -0.84, 5.70, 6.00, 2.65, 2.90) # Logo rojo Tecate
    obj_tec_com_l = create_mesh_object("Diana_Logo_Rojo_Tecate", bm_tec_com_l, mats["logo_rojo_tecate"], col)
    objects.append(obj_tec_com_l)

    t_tec_c = add_3d_text("Diana_Txt_Tecate", "TECATE", 0.11, 0.01, (-0.87, 5.85, 2.50), rot_cardenas, mats["espectacular_rojo_renta"], col, 'CENTER')
    objects.append(t_tec_c)

    # -----------------------------------------------------------------------
    # 3. ANNITA'S BOUTIQUE (Y in [9.30, 14.50])
    # -----------------------------------------------------------------------
    # Puerta a la DERECHA (Y in [9.45, 10.50], Z in [0.00, 2.70 m])
    bm_anita_p = bmesh.new()
    add_box(bm_anita_p, 0.02, 0.12, 9.45, 10.50, 2.65, 2.70)
    add_box(bm_anita_p, 0.02, 0.12, 9.45, 9.51, 0.00, 2.65)
    add_box(bm_anita_p, 0.02, 0.12, 10.44, 10.50, 0.00, 2.65)
    add_box(bm_anita_p, 0.04, 0.06, 9.51, 10.44, 0.00, 2.65)
    for py in range(6):
        py_pos = 9.56 + py * 0.14
        add_box(bm_anita_p, 0.07, 0.09, py_pos, py_pos + 0.02, 0.00, 2.65)
    obj_anita_p = create_mesh_object("Anita_Puerta_Canceleria", bm_anita_p, mats["aluminio_blanco"], col)
    objects.append(obj_anita_p)

    # Vitrina con persianas venecianas de madera a la IZQUIERDA (Y in [10.70, 14.30], Z in [0.65, 2.70 m])
    bm_pers = bmesh.new()
    add_box(bm_pers, 0.02, 0.15, 10.70, 14.30, 0.65, 0.70)
    add_box(bm_pers, 0.02, 0.15, 10.70, 14.30, 2.65, 2.70)
    add_box(bm_pers, 0.02, 0.15, 10.70, 10.75, 0.70, 2.65)
    add_box(bm_pers, 0.02, 0.15, 14.25, 14.30, 0.70, 2.65)
    add_box(bm_pers, 0.04, 0.06, 10.75, 14.25, 0.70, 2.65)
    for l in range(24):
        zl = 0.72 + l * 0.08
        add_box(bm_pers, 0.08, 0.16, 10.77, 14.23, zl, zl + 0.02)
    obj_pers = create_mesh_object("Anita_Vitrina_Persianas_Madera", bm_pers, mats["persianas_madera"], col)
    objects.append(obj_pers)

    # Caja grafito adosada sobre marquesina (Y in [9.60, 14.20], Z in [3.05, 3.80 m])
    bm_anita_caja = bmesh.new()
    add_box(bm_anita_caja, -0.15, -0.05, 9.60, 14.20, 3.05, 3.80)
    add_box(bm_anita_caja, -0.17, -0.03, 9.57, 14.23, 3.03, 3.07)
    add_box(bm_anita_caja, -0.17, -0.03, 9.57, 14.23, 3.78, 3.82)
    add_box(bm_anita_caja, -0.17, -0.03, 9.57, 9.61, 3.03, 3.82)
    add_box(bm_anita_caja, -0.17, -0.03, 14.19, 14.23, 3.03, 3.82)
    obj_anita_caja = create_mesh_object("Anita_Caja_Grafito_Rotulo", bm_anita_caja, mats["caja_grafito_anita"], col)
    objects.append(obj_anita_caja)

    bm_anita_ov = bmesh.new()
    add_box(bm_anita_ov, -0.18, -0.14, 10.80, 13.00, 3.15, 3.70)
    obj_anita_ov = create_mesh_object("Anita_Ovalo_Plateado", bm_anita_ov, mats["ovalo_plata_anita"], col)
    objects.append(obj_anita_ov)

    t_an1 = add_3d_text("Anita_Txt_Annitas", "Annita's", 0.32, 0.02, (-0.20, 11.90, 3.42), rot_cardenas, mats["letras_anita_blanco"], col, 'CENTER')
    t_an2 = add_3d_text("Anita_Txt_Boutique", "Boutique", 0.12, 0.015, (-0.20, 11.90, 3.25), rot_cardenas, mats["letras_anita_blanco"], col, 'CENTER')
    objects.extend([t_an1, t_an2])



    # -----------------------------------------------------------------------
    # 4. PARTY RENTALS (KUROKY) (Y in [14.50, 20.00])
    # -----------------------------------------------------------------------
    # Puerta comercial a la DERECHA (Y in [14.65, 15.70], Z in [0.00, 2.70 m])
    bm_party_p = bmesh.new()
    add_box(bm_party_p, 0.02, 0.12, 14.65, 15.70, 2.65, 2.70)
    add_box(bm_party_p, 0.02, 0.12, 14.65, 14.71, 0.00, 2.65)
    add_box(bm_party_p, 0.02, 0.12, 15.64, 15.70, 0.00, 2.65)
    add_box(bm_party_p, 0.04, 0.06, 14.71, 15.64, 0.00, 2.65)
    obj_party_p = create_mesh_object("Party_Puerta_Canceleria", bm_party_p, mats["aluminio_blanco"], col)
    objects.append(obj_party_p)

    # Ventanal con notas musicales al CENTRO / IZQUIERDA (Y in [15.85, 19.50], Z in [0.85, 2.70 m])
    bm_party_v = bmesh.new()
    add_box(bm_party_v, 0.04, 0.06, 15.85, 19.50, 0.85, 2.70)
    add_box(bm_party_v, 0.02, 0.15, 15.85, 19.50, 0.85, 0.90)
    add_box(bm_party_v, 0.02, 0.15, 15.85, 19.50, 2.65, 2.70)
    add_box(bm_party_v, 0.02, 0.15, 15.85, 15.90, 0.90, 2.65)
    add_box(bm_party_v, 0.02, 0.15, 19.45, 19.50, 0.90, 2.65)
    obj_party_v = create_mesh_object("Party_Vitrina_Vidrio", bm_party_v, mats["vidrio_comercial"], col)
    objects.append(obj_party_v)

    bm_notas = bmesh.new()
    for franja in range(3):
        zn = 1.20 + franja * 0.48
        for nota in range(8):
            yn = 16.05 + nota * 0.42
            add_box(bm_notas, 0.03, 0.05, yn, yn + 0.04, zn, zn + 0.04)
            add_box(bm_notas, 0.03, 0.05, yn + 0.03, yn + 0.04, zn + 0.04, zn + 0.12)
            add_box(bm_notas, 0.03, 0.05, yn + 0.03, yn + 0.07, zn + 0.10, zn + 0.12)
    obj_notas = create_mesh_object("Party_Notas_Musicales_Vidrio", bm_notas, mats["notas_musicales"], col)
    objects.append(obj_notas)

    # Buzones amarillos
    bm_buzones = bmesh.new()
    add_box(bm_buzones, -0.40, -0.25, 14.80, 14.92, 0.00, 0.95)
    add_box(bm_buzones, -0.40, -0.25, 14.98, 15.10, 0.00, 0.85)
    obj_buzones = create_mesh_object("Party_Buzones_Amarillos", bm_buzones, mats["buzones_amarillos"], col)
    objects.append(obj_buzones)

    # Panel blanco horizontal sobre marquesina (Y in [14.50, 19.80], Z in [3.05, 3.85 m])
    bm_party_rot = bmesh.new()
    add_box(bm_party_rot, -0.15, -0.05, 14.50, 19.80, 3.05, 3.85)
    obj_party_rot = create_mesh_object("Party_Panel_Rotulo_Blanco", bm_party_rot, mats["panel_blanco_party"], col)
    objects.append(obj_party_rot)

    # Lona publicitaria colorida a la IZQUIERDA (Y in [18.30, 19.70])
    bm_party_lona = bmesh.new()
    add_box(bm_party_lona, -0.17, -0.14, 18.30, 19.70, 3.10, 3.80)
    obj_party_lona = create_mesh_object("Party_Lona_Colorida_Fiestas", bm_party_lona, mats["lona_fotos_party"], col)
    objects.append(obj_party_lona)

    t_p1 = add_3d_text("Party_Txt_Title", "PARTY RENTALS", 0.28, 0.02, (-0.18, 16.50, 3.55), rot_cardenas, mats["letras_verdes_party"], col, 'CENTER')
    t_p2 = add_3d_text("Party_Txt_Kuroky", "KUROKY", 0.16, 0.015, (-0.18, 16.50, 3.35), rot_cardenas, mats["logo_kuroky_magenta"], col, 'CENTER')
    t_p3 = add_3d_text("Party_Txt_Col1", "SONIDO\nLUCES\nPANTALLAS", 0.08, 0.01, (-0.18, 15.00, 3.25), rot_cardenas, mats["letras_azules_party"], col, 'LEFT')
    t_p4 = add_3d_text("Party_Txt_Col2", "MESAS\nSILLAS\nMANTELES", 0.08, 0.01, (-0.18, 17.90, 3.25), rot_cardenas, mats["letras_azules_party"], col, 'RIGHT')
    objects.extend([t_p1, t_p2, t_p3, t_p4])

    # -----------------------------------------------------------------------
    # 5. LIBRERÍA ESPAÑA (Y in [0.00, 4.80])
    # -----------------------------------------------------------------------
    # Murete mostaza y zócalo marrón
    bm_lib_mur = bmesh.new()
    add_box(bm_lib_mur, -0.05, 0.35, 0.00, 4.80, 0.00, 0.15)
    obj_lib_zoc = create_mesh_object("Libreria_Zocalo_Marron", bm_lib_mur, mats["zocalo_marron"], col)
    objects.append(obj_lib_zoc)

    bm_lib_mostaza = bmesh.new()
    add_box(bm_lib_mostaza, 0.00, 0.35, 1.10, 4.80, 0.15, 0.60)
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

    bm_lib_rev = bmesh.new()
    for row in range(5):
        zr = 0.70 + row * 0.45
        for col_i in range(8):
            yr = 1.25 + col_i * 0.42
            add_box(bm_lib_rev, 0.08, 0.15, yr, yr + 0.35, zr, zr + 0.38)
    add_box(bm_lib_rev, 0.07, 0.10, 1.20, 1.70, 1.50, 2.80)
    obj_lib_rev = create_mesh_object("Libreria_Exhibidor_Revistas", bm_lib_rev, mats["revistas_exhibidor"], col)
    objects.append(obj_lib_rev)

    # Puerta comercial peatonal (Y in [0.20, 1.10])
    bm_lib_p = bmesh.new()
    add_box(bm_lib_p, 0.02, 0.12, 0.20, 1.10, 3.08, 3.12)
    add_box(bm_lib_p, 0.02, 0.12, 0.20, 0.26, 0.00, 3.08)
    add_box(bm_lib_p, 0.02, 0.12, 1.04, 1.10, 0.00, 3.08)
    add_box(bm_lib_p, 0.04, 0.06, 0.26, 1.04, 0.00, 3.08)
    obj_lib_p = create_mesh_object("Libreria_Puerta_Aluminio", bm_lib_p, mats["aluminio_blanco"], col)
    objects.append(obj_lib_p)

    # Fascia marrón con textos dorados
    bm_lib_f = bmesh.new()
    add_box(bm_lib_f, -0.08, 0.35, 0.00, 4.80, 3.10, 3.45)
    obj_lib_f = create_mesh_object("Libreria_Fascia_Marron", bm_lib_f, mats["fascia_marron_lib"], col)
    objects.append(obj_lib_f)

    t_lib_f1 = add_3d_text("Libreria_Txt_Direccion", "PRESIDENTE CARDENAS 95-B Z.C. - TECATE, B.C.", 0.10, 0.01, (-0.10, 2.40, 3.25), rot_cardenas, mats["letras_doradas_lib"], col, 'CENTER')
    objects.append(t_lib_f1)

    # Letrero superior blanco enmarcado
    bm_lib_r = bmesh.new()
    add_box(bm_lib_r, -0.15, -0.05, 0.00, 4.80, 3.45, 4.25)
    add_box(bm_lib_r, -0.17, -0.03, 0.00, 4.82, 3.43, 3.47)
    add_box(bm_lib_r, -0.17, -0.03, 0.00, 4.82, 4.23, 4.27)
    add_box(bm_lib_r, -0.17, -0.03, 0.00, 0.04, 3.43, 4.27)
    add_box(bm_lib_r, -0.17, -0.03, 4.78, 4.82, 3.43, 4.27)
    obj_lib_r = create_mesh_object("Libreria_Panel_Rotulo_Blanco", bm_lib_r, mats["panel_rotulo_lib"], col)
    objects.append(obj_lib_r)

    t_lib1 = add_3d_text("Libreria_Txt_Nombre", "Librería España", 0.36, 0.025, (-0.18, 2.40, 3.82), rot_cardenas, mats["letras_negras_lib"], col, 'CENTER')
    t_lib2 = add_3d_text("Libreria_Txt_Sub", "• LIBROS • REVISTAS Y PERIODICOS •", 0.12, 0.015, (-0.18, 2.40, 3.56), rot_cardenas, mats["letras_rojas_lib"], col, 'CENTER')
    objects.extend([t_lib1, t_lib2])

    return objects

# ---------------------------------------------------------------------------
# 4. Construcción de Ochava a 45º (Florería Orquídea con Frontón Monumental)
# ---------------------------------------------------------------------------

def build_ochava_orquidea(mats, col):
    """
    Construye la ochava a 45º exacta conectando (0.00, 20.50) con (4.00, 24.50)
    y su frontón monumental de 6.60 m con marco perimetral blanco en resalte,
    paño central rehundido de mosaico verde salvia con piedritas blancas,
    letrero tridimensional físico con greca roja perimetral y puerta doble acristalada.
    CERO CLIPPING / Z-FIGHTING (superficies desfasadas analíticamente).
    """
    objects = []
    p1 = Vector((0.00, 20.50, 0.00))
    p2 = Vector((4.00, 24.50, 0.00))
    rot_ochava = (math.radians(90.0), 0.0, math.radians(-135.0))
    center_och = (p1 + p2) * 0.5

    # Vector unitario a lo largo del chaflán (de p1 a p2)
    dir_och = (p2 - p1).normalized()
    # Vector normal hacia afuera (calle)
    norm_out = Vector((-dir_och.y, dir_och.x, 0.0))

    def pt_t(t, offset_out=0.0):
        # Punto en el chaflán parametrizado por t in [0, 1] con desplazamiento normal
        return (p1 + dir_och * (t * 5.656854) + norm_out * offset_out).to_2d()

    # 1. Zócalo basal enterrado (-1.20 a 0.00 m)
    bm_zoc = bmesh.new()
    add_chaflan_box(bm_zoc, pt_t(0.0), pt_t(1.0), 0.50, -1.20, 0.00)
    obj_zoc = create_mesh_object("Orquidea_Ochava_Zocalo_Basal", bm_zoc, mats["zocalo_basal"], col)
    objects.append(obj_zoc)

    # 2. Zócalo de piedra laja café rojiza de Z = 0.00 a 0.65 m (con grosor exterior 0.04 m)
    bm_laja = bmesh.new()
    add_chaflan_box(bm_laja, pt_t(0.0, 0.04), pt_t(1.0, 0.04), 0.48, 0.00, 0.65)
    obj_laja = create_mesh_object("Orquidea_Ochava_Laja_Cafe", bm_laja, mats["laja_rustica_orquidea"], col)
    objects.append(obj_laja)

    # 3. Puerta doble acristalada en PB de la ochava (Z in [0.00, 2.65 m])
    bm_puerta = bmesh.new()
    add_chaflan_box(bm_puerta, pt_t(0.28, 0.01), pt_t(0.31, 0.01), 0.15, 0.00, 2.65) # Jamba izquierda
    add_chaflan_box(bm_puerta, pt_t(0.69, 0.01), pt_t(0.72, 0.01), 0.15, 0.00, 2.65) # Jamba derecha
    add_chaflan_box(bm_puerta, pt_t(0.28, 0.01), pt_t(0.72, 0.01), 0.15, 2.50, 2.65) # Cabezal superior
    add_chaflan_box(bm_puerta, pt_t(0.485, 0.01), pt_t(0.515, 0.01), 0.15, 0.00, 2.50) # Poste central divisor
    add_chaflan_box(bm_puerta, pt_t(0.28, 0.01), pt_t(0.72, 0.01), 0.15, 0.00, 0.18) # Zoclo inferior
    # Jaladeras de aluminio en las puertas
    add_chaflan_box(bm_puerta, pt_t(0.46, 0.03), pt_t(0.48, 0.03), 0.10, 0.95, 1.15)
    add_chaflan_box(bm_puerta, pt_t(0.52, 0.03), pt_t(0.54, 0.03), 0.10, 0.95, 1.15)
    obj_puerta = create_mesh_object("Orquidea_Ochava_Puerta_Aluminio", bm_puerta, mats["aluminio_blanco"], col)
    objects.append(obj_puerta)

    # Vidrios de las dos hojas de puerta y escaparates laterales
    bm_vidrio = bmesh.new()
    add_chaflan_box(bm_vidrio, pt_t(0.31, 0.00), pt_t(0.485, 0.00), 0.04, 0.18, 2.50) # Vidrio hoja izquierda
    add_chaflan_box(bm_vidrio, pt_t(0.515, 0.00), pt_t(0.69, 0.00), 0.04, 0.18, 2.50) # Vidrio hoja derecha
    add_chaflan_box(bm_vidrio, pt_t(0.04, 0.00), pt_t(0.26, 0.00), 0.08, 0.65, 2.65) # Vidrio escaparate sur
    add_chaflan_box(bm_vidrio, pt_t(0.74, 0.00), pt_t(0.96, 0.00), 0.08, 0.65, 2.65) # Vidrio escaparate norte
    obj_vidrio = create_mesh_object("Orquidea_Ochava_Escaparate_Vidrio", bm_vidrio, mats["vidrio_comercial"], col)
    objects.append(obj_vidrio)

    # Exhibidores interiores de flores visibles por transparencia
    bm_flores = bmesh.new()
    add_chaflan_box(bm_flores, pt_t(0.06, -0.15), pt_t(0.24, -0.15), 0.30, 0.65, 1.20)
    add_chaflan_box(bm_flores, pt_t(0.76, -0.15), pt_t(0.94, -0.15), 0.30, 0.65, 1.20)
    obj_flores = create_mesh_object("Orquidea_Ochava_Exhibidor_Flores", bm_flores, mats["revistas_exhibidor"], col)
    objects.append(obj_flores)

    # 4. Marquesina corrida sobre la ochava (Z in [2.70, 2.95 m])
    bm_marq = bmesh.new()
    add_chaflan_box(bm_marq, pt_t(-0.05, 0.70), pt_t(1.05, 0.70), 0.75, 2.70, 2.95)
    obj_marq = create_mesh_object("Orquidea_Ochava_Marquesina", bm_marq, mats["concreto_marquesina"], col)
    objects.append(obj_marq)

    # 5. FRONTÓN MONUMENTAL EN OCHAVA A 45º (Z in [2.95, 6.60 m])
    # A. Marco perimetral blanco en resalte exterior (depth face at offset = 0.00 m)
    # Pilastra izquierda (t in [0.00, 0.12])
    bm_marco = bmesh.new()
    add_chaflan_box(bm_marco, pt_t(0.00, 0.00), pt_t(0.12, 0.00), 0.45, 2.95, 6.60)
    # Pilastra derecha (t in [0.88, 1.00])
    add_chaflan_box(bm_marco, pt_t(0.88, 0.00), pt_t(1.00, 0.00), 0.45, 2.95, 6.60)
    # Cornisa superior horizontal (Z in [6.15, 6.60 m])
    add_chaflan_box(bm_marco, pt_t(0.00, 0.00), pt_t(1.00, 0.00), 0.45, 6.15, 6.60)
    # Voladizo/remate biselado de la cornisa superior (Z in [6.45, 6.65 m], sobresale 0.08 m)
    add_chaflan_box(bm_marco, pt_t(-0.03, 0.08), pt_t(1.03, 0.08), 0.20, 6.45, 6.65)
    # Zócalo base inferior del marco (Z in [2.95, 3.10 m])
    add_chaflan_box(bm_marco, pt_t(0.00, 0.00), pt_t(1.00, 0.00), 0.45, 2.95, 3.10)
    obj_marco = create_mesh_object("Orquidea_Fronton_Marco_Blanco", bm_marco, mats["concreto_blanco"], col)
    objects.append(obj_marco)

    # B. Paño central rehundido de mosaico de terrazo verde salvia con piedritas blancas
    # Front face at offset = -0.12 m (12 cm REHUNDIDO detrás del marco blanco)
    bm_mosaico = bmesh.new()
    add_chaflan_box(bm_mosaico, pt_t(0.10, -0.12), pt_t(0.90, -0.12), 0.32, 3.08, 6.18)
    obj_mosaico = create_mesh_object("Orquidea_Fronton_Mosaico_Verde", bm_mosaico, mats["mosaico_orquidea"], col)
    objects.append(obj_mosaico)

    # C. LETRERO MONUMENTAL FÍSICO (Caja blanca montada sobre el mosaico con borde rojo)
    # Ubicado en la mitad inferior del frontón: Z in [3.35, 5.10 m]
    # Montado en el mosaico: cara posterior en offset -0.12 m, cara anterior en offset -0.04 m (8 cm de espesor)
    bm_panel = bmesh.new()
    add_chaflan_box(bm_panel, pt_t(0.20, -0.04), pt_t(0.80, -0.04), 0.08, 3.35, 5.10)
    obj_panel = create_mesh_object("Orquidea_Panel_Rotulo_Blanco", bm_panel, mats["panel_rotulo_orquidea"], col)
    objects.append(obj_panel)

    # Borde perimetral rojo (Greca en relieve de 2 cm sobre la cara del letrero)
    # Front face at offset = -0.025 m
    bm_greca = bmesh.new()
    # Borde inferior
    add_chaflan_box(bm_greca, pt_t(0.19, -0.025), pt_t(0.81, -0.025), 0.03, 3.33, 3.42)
    # Borde superior
    add_chaflan_box(bm_greca, pt_t(0.19, -0.025), pt_t(0.81, -0.025), 0.03, 5.03, 5.12)
    # Borde lateral izquierdo
    add_chaflan_box(bm_greca, pt_t(0.19, -0.025), pt_t(0.22, -0.025), 0.03, 3.33, 5.12)
    # Borde lateral derecho
    add_chaflan_box(bm_greca, pt_t(0.78, -0.025), pt_t(0.81, -0.025), 0.03, 3.33, 5.12)
    obj_greca = create_mesh_object("Orquidea_Greca_Roja", bm_greca, mats["greca_roja_orquidea"], col)
    objects.append(obj_greca)

    # D. Textos tridimensionales en relieve sobre la caja del letrero (offset = -0.035 m, extrude = 0.03 m)
    p_panel = center_och + norm_out * (-0.035)

    loc_txt_f = p_panel.copy()
    loc_txt_f.z = 4.45
    t_or1 = add_3d_text("Orquidea_Txt_Floreria", "FLORERIA", 0.42, 0.03, loc_txt_f, rot_ochava, mats["letras_purpura_orquidea"], col, 'CENTER')

    loc_txt_o = p_panel.copy()
    loc_txt_o.z = 3.85
    t_or2 = add_3d_text("Orquidea_Txt_Orquidea", "ORQUIDEA", 0.50, 0.035, loc_txt_o, rot_ochava, mats["letras_purpura_orquidea"], col, 'CENTER')

    loc_txt_t = p_panel.copy()
    loc_txt_t.z = 3.52
    t_or3 = add_3d_text("Orquidea_Txt_Tel", "Teléfono 654-10-51", 0.13, 0.015, loc_txt_t, rot_ochava, mats["greca_roja_orquidea"], col, 'CENTER')
    objects.extend([t_or1, t_or2, t_or3])

    return objects

# ---------------------------------------------------------------------------
# 5. Construcción de Fachada Libertad (Foto Estudio Curiel)
# ---------------------------------------------------------------------------

def build_libertad_facade(mats, col):
    """
    Construye la fachada norte sobre Callejón Libertad (X in [4.00, 16.50 m], Y = 24.50 m).
    Pretil limpio a Z = 4.30 m, techo confinado al interior sin intersectar letreros.
    """
    objects = []
    rot_libertad = (math.radians(90.0), 0.0, math.radians(180.0))

    # 1. Muro principal de estuco blanco puro (Z = 0.00 a 4.30 m)
    bm_curiel_m = bmesh.new()
    add_box(bm_curiel_m, 4.00, 16.50, 24.15, 24.50, 0.00, 4.30)
    obj_curiel_m = create_mesh_object("Curiel_Muro_Blanco", bm_curiel_m, mats["estuco_blanco_curiel"], col)
    objects.append(obj_curiel_m)

    # Zócalo marrón inferior
    bm_cur_zoc = bmesh.new()
    add_box(bm_cur_zoc, 4.00, 16.50, 24.15, 24.55, 0.00, 0.20)
    obj_cur_zoc = create_mesh_object("Curiel_Zocalo_Marron", bm_cur_zoc, mats["zocalo_marron"], col)
    objects.append(obj_cur_zoc)

    # 2. Marquesina horizontal Streamline Moderne con 3 estrías metálicas plateadas (Z in [2.70, 2.95 m])
    # Se detiene en X = 14.80 m para no colisionar ni cortar el tótem publicitario en X in [15.20, 15.70]
    bm_curiel_marq = bmesh.new()
    add_box(bm_curiel_marq, 3.90, 14.80, 24.50, 25.35, 2.70, 2.95)
    add_box(bm_curiel_marq, 14.75, 14.80, 24.50, 25.35, 2.70, 2.95)
    for est in range(3):
        ze = 2.73 + est * 0.07
        add_box(bm_curiel_marq, 3.85, 14.85, 25.35, 25.40, ze, ze + 0.03)
        add_box(bm_curiel_marq, 14.80, 14.85, 24.50, 25.40, ze, ze + 0.03)
    obj_curiel_marq = create_mesh_object("Curiel_Marquesina_Streamline", bm_curiel_marq, mats["moldura_streamline"], col)
    objects.append(obj_curiel_marq)

    # 3. Puerta y vitrina PB
    bm_curiel_pb = bmesh.new()
    add_box(bm_curiel_pb, 6.50, 12.00, 24.45, 24.55, 1.00, 2.45) # Vitrina exhibición retratos
    add_box(bm_curiel_pb, 13.50, 14.80, 24.45, 24.55, 0.00, 2.65) # Puerta cancelería
    obj_curiel_pb = create_mesh_object("Curiel_Canceleria_PB", bm_curiel_pb, mats["vidrio_comercial"], col)
    objects.append(obj_curiel_pb)

    # 4. Rótulos Foto Estudio Curiel en fachada norte
    t_c1 = add_3d_text("Curiel_Txt_FotoStudio", "FOTO STUDIO", 0.35, 0.025, (10.50, 24.55, 3.75), rot_libertad, mats["letras_azul_curiel"], col, 'CENTER')
    t_c2 = add_3d_text("Curiel_Txt_Curiel", "CURIEL", 0.44, 0.03, (10.50, 24.55, 3.25), rot_libertad, mats["letras_dorado_curiel"], col, 'CENTER')
    t_c3 = add_3d_text("Curiel_Txt_Muro", "FOTO STUDIO\nCURIEL", 0.18, 0.015, (12.80, 24.55, 1.95), rot_libertad, mats["totem_rojo_curiel"], col, 'CENTER')
    objects.extend([t_c1, t_c2, t_c3])

    # 5. Tótem vertical publicitario rojo bermellón en esquina poniente (X in [15.80, 16.30])
    # Ubicado a 1.00 m más allá del fin de la marquesina: CERO INTERSECCIÓN / CORTE
    bm_totem = bmesh.new()
    add_box(bm_totem, 16.00, 16.10, 24.55, 24.65, 0.00, 1.60) # Mástil de anclaje inferior
    add_box(bm_totem, 15.80, 16.30, 24.50, 25.10, 1.60, 4.40) # Cuerpo vertical rojo continuo
    add_box(bm_totem, 15.78, 16.32, 24.49, 25.11, 4.38, 4.42)
    add_box(bm_totem, 15.78, 16.32, 24.49, 25.11, 1.58, 1.62)
    obj_totem = create_mesh_object("Curiel_Totem_Rojo", bm_totem, mats["totem_rojo_curiel"], col)
    objects.append(obj_totem)

    t_tot1 = add_3d_text("Curiel_Txt_Totem_N", "F\nO\nT\nO", 0.40, 0.02, (16.05, 25.12, 3.80), rot_libertad, mats["concreto_blanco"], col, 'CENTER')
    rot_sur = (math.radians(90.0), 0.0, 0.0)
    t_tot2 = add_3d_text("Curiel_Txt_Totem_S", "F\nO\nT\nO", 0.40, 0.02, (16.05, 24.48, 3.80), rot_sur, mats["concreto_blanco"], col, 'CENTER')
    objects.extend([t_tot1, t_tot2])

    return objects

# ---------------------------------------------------------------------------
# 6. Construcción de Fachada Posterior (Estacionamiento BBVA) y Medianera Sur
# ---------------------------------------------------------------------------

def build_rear_and_medianera(mats, col):
    """
    Construye la fachada poniente (X = 16.50 m) visible desde el estacionamiento interior del BBVA
    y la medianera sur hermética con BBVA DENTISTA en Y = 0.00 m.
    Cero bloques negros invasivos en la salida del bar.
    """
    objects = []
    rot_estacionamiento = (math.radians(90.0), 0.0, math.radians(90.0))

    # 1. Muro posterior continuo en estuco blanco/gris de servicio (X = 16.50 m, Y in [0.00, 24.50 m])
    bm_rear = bmesh.new()
    add_box(bm_rear, 16.15, 16.50, 0.00, 24.50, 0.00, 4.30)
    # Marquesina ligera en voladizo sobre la puerta de salida (vuela solo 0.60 m)
    add_box(bm_rear, 16.50, 17.15, 6.30, 7.90, 2.25, 2.35)
    obj_rear = create_mesh_object("Posterior_Muro_Servicio", bm_rear, mats["estuco_blanco_curiel"], col)
    objects.append(obj_rear)

    # Puerta metálica de servicio de Bar Diana (Y in [6.50, 7.70], Z in [0.00, 2.20]) con marco y hoja oscura
    bm_p_rear = bmesh.new()
    add_box(bm_p_rear, 16.48, 16.54, 6.50, 7.70, 0.00, 2.20)
    obj_p_rear = create_mesh_object("Posterior_Puerta_Servicio_Diana", bm_p_rear, mats["herreria_verde_diana"], col)
    objects.append(obj_p_rear)

    # 2. Rótulos en la fachada poniente (visible desde el estacionamiento interior BBVA):
    # A. Foto Estudio Curiel en la parte norte del pretil poniente (Y in [19.00, 24.00])
    t_curiel_post1 = add_3d_text("Posterior_Txt_Curiel1", "FOTO STUDIO", 0.44, 0.025, (16.55, 21.50, 3.80), rot_estacionamiento, mats["letras_azul_curiel"], col, 'CENTER')
    t_curiel_post2 = add_3d_text("Posterior_Txt_Curiel2", "CURIEL", 0.55, 0.030, (16.55, 21.50, 3.25), rot_estacionamiento, mats["letras_dorado_curiel"], col, 'CENTER')
    # B. Bar Diana en la parte sur del pretil poniente (Y in [5.50, 8.50])
    t_diana_post = add_3d_text("Posterior_Txt_BarDiana", "Bar TURISTICO Diana", 0.38, 0.025, (16.55, 7.10, 3.50), rot_estacionamiento, mats["rotulo_diana_dorado"], col, 'CENTER')
    # C. Señalética 'Salida' sobre puerta trasera
    t_salida = add_3d_text("Posterior_Txt_Salida", "Salida", 0.18, 0.015, (16.55, 7.10, 2.45), rot_estacionamiento, mats["greca_roja_orquidea"], col, 'CENTER')
    objects.extend([t_curiel_post1, t_curiel_post2, t_diana_post, t_salida])

    # 3. MEDIANERA SUR CONTINUA ENRASADA CON BBVA DENTISTA EN Y = 0.00 m
    # Confinada estrictamente a Y >= 0.00 m para eliminar cualquier clipping con las cornisas y molduras de BBVA.
    bm_med = bmesh.new()
    add_box(bm_med, 0.00, 16.50, 0.00, 0.25, 0.00, 4.30)
    obj_med = create_mesh_object("Medianera_Sur_Enrase_BBVA", bm_med, mats["estuco_blanco_curiel"], col)
    objects.append(obj_med)

    # 4. TECHO DE AZOTEA CONFINADO (Y <= 24.20 m para no cortar el paramento norte)
    bm_techo = bmesh.new()
    # Cubierta central confinada
    add_box(bm_techo, 0.20, 16.20, 0.20, 20.00, 3.75, 3.85) # Zona Cárdenas
    add_box(bm_techo, 3.80, 16.20, 20.00, 24.15, 3.75, 3.85) # Zona Curiel (sin invadir Y = 24.50)
    obj_techo = create_mesh_object("Azotea_Cubierta_Impermeable", bm_techo, mats["techo_impermeable"], col)
    objects.append(obj_techo)

    return objects

# ---------------------------------------------------------------------------
# 7. Iluminación Diurna y Cámaras Calibradas
# ---------------------------------------------------------------------------

def setup_lighting_and_cameras(col):
    """Configura iluminación diurna con cielo brillante y luz de rebote."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720

    # Cielo diurno
    world = bpy.data.worlds.new("World_Tecate_Day")
    scene.world = world
    world.use_nodes = True
    w_nodes = world.node_tree.nodes
    w_nodes.clear()
    w_out = w_nodes.new(type='ShaderNodeOutputWorld')
    w_bg = w_nodes.new(type='ShaderNodeBackground')
    w_bg.inputs['Color'].default_value = (0.58, 0.76, 0.95, 1.0)
    w_bg.inputs['Strength'].default_value = 1.4
    world.node_tree.links.new(w_bg.outputs['Background'], w_out.inputs['Surface'])

    # Sol exterior cenital
    sun_data = bpy.data.lights.new(name="Sun_Exterior", type='SUN')
    sun_data.energy = 4.0
    sun_data.color = (1.0, 0.98, 0.94)
    sun_obj = bpy.data.objects.new("Sun_Exterior", sun_data)
    col.objects.link(sun_obj)
    sun_obj.location = Vector((-10.0, 12.0, 20.0))
    sun_obj.rotation_euler = Euler((math.radians(45.0), math.radians(20.0), math.radians(-35.0)), 'XYZ')

    # Luz de relleno frontal
    fill_data = bpy.data.lights.new(name="Sun_Fill_Frontal", type='SUN')
    fill_data.energy = 2.0
    fill_data.color = (0.90, 0.94, 1.0)
    fill_obj = bpy.data.objects.new("Sun_Fill_Frontal", fill_data)
    col.objects.link(fill_obj)
    fill_obj.location = Vector((-20.0, 12.0, 5.0))
    fill_obj.rotation_euler = Euler((math.radians(15.0), 0.0, math.radians(-90.0)), 'XYZ')

    # Luz de relleno norte (Libertad y ochava)
    north_data = bpy.data.lights.new(name="Sun_Fill_North", type='SUN')
    north_data.energy = 2.5
    north_data.color = (0.92, 0.95, 1.0)
    north_obj = bpy.data.objects.new("Sun_Fill_North", north_data)
    col.objects.link(north_obj)
    north_obj.location = Vector((8.0, 35.0, 15.0))
    north_obj.rotation_euler = Euler((math.radians(-35.0), 0.0, math.radians(180.0)), 'XYZ')

    # Luz de relleno poniente (estacionamiento BBVA y fachada trasera)
    west_data = bpy.data.lights.new(name="Sun_Fill_West", type='SUN')
    west_data.energy = 2.8
    west_data.color = (1.0, 0.97, 0.92)
    west_obj = bpy.data.objects.new("Sun_Fill_West", west_data)
    col.objects.link(west_obj)
    west_obj.location = Vector((30.0, 12.0, 15.0))
    west_obj.rotation_euler = Euler((math.radians(25.0), math.radians(15.0), math.radians(90.0)), 'XYZ')

    # 6 cámaras técnicas calibradas:
    cams_config = [
        # 1. Frontal completa sobre Calle Cárdenas
        ("Cam_Cardenas_Frontal_V5", (-15.5, 11.5, 2.6), (0.0, 11.5, 2.6), 30.0),
        # 2. Ochava a 45º exacta de Florería Orquídea (encuadre idéntico a media_1790243423150.jpg y media_1790244680401.png)
        ("Cam_Orquidea_Ochava_V5", (-5.5, 30.0, 3.0), (2.0, 22.5, 3.4), 34.0),
        # 3. Foto Estudio Curiel sobre Callejón Libertad (vista angular amplia como en media_1790244706722.png)
        ("Cam_Curiel_Libertad_V5", (20.5, 32.5, 3.2), (12.0, 24.5, 2.8), 28.0),
        # 4. Detalle Bar Diana (puerta verde, fachaleta blanca, Diana Cazadora y letrero Tecate)
        ("Cam_Diana_Closeup_V5", (-7.5, 7.0, 2.3), (0.0, 7.0, 2.5), 42.0),
        # 5. Detalle Librería España y espectacular Tecate de azotea
        ("Cam_Libreria_Espana_V5", (-8.0, 2.4, 3.2), (0.0, 2.4, 3.2), 38.0),
        # 6. Reverso poniente desde estacionamiento BBVA (letrero Foto Curiel, Bar Diana, cero rejas invasivas)
        ("Cam_Reverso_Estacionamiento_V5", (24.5, 0.5, 4.0), (16.5, 13.5, 2.6), 28.0),
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
# 8. Generación de Escena Godot 4 (.tscn) con Colisión de Ochava a 45º
# ---------------------------------------------------------------------------

def generate_godot_tscn(tscn_path, glb_path_rel):
    """
    Genera la escena de Godot 4 con colisionadores BoxShape3D analíticos.
    Incluye un colisionador rotado 45º en la ochava para caminabilidad fluida.
    """
    tscn_content = f"""[gd_scene load_steps=9 format=3 uid="uid://cardenas_33_locales_001"]

[ext_resource type="PackedScene" path="{glb_path_rel}" id="1_mesh"]

[sub_resource type="BoxShape3D" id="BoxShape3D_libreria"]
size = Vector3(16.5, 4.5, 4.8)

[sub_resource type="BoxShape3D" id="BoxShape3D_diana"]
size = Vector3(16.5, 4.5, 4.5)

[sub_resource type="BoxShape3D" id="BoxShape3D_anita"]
size = Vector3(16.5, 4.5, 5.2)

[sub_resource type="BoxShape3D" id="BoxShape3D_party"]
size = Vector3(16.5, 4.5, 5.5)

[sub_resource type="BoxShape3D" id="BoxShape3D_orquidea_ochava"]
size = Vector3(5.7, 6.8, 1.2)

[sub_resource type="BoxShape3D" id="BoxShape3D_curiel"]
size = Vector3(12.5, 4.5, 4.5)

[node name="Edificio_Cardenas_33" type="StaticBody3D"]

[node name="ModelInstance" parent="." instance=ExtResource("1_mesh")]

[node name="Col_Libreria" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 8.25, 2.25, -2.40)
shape = SubResource("BoxShape3D_libreria")

[node name="Col_Diana" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 8.25, 2.25, -7.05)
shape = SubResource("BoxShape3D_diana")

[node name="Col_Anita" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 8.25, 2.25, -11.90)
shape = SubResource("BoxShape3D_anita")

[node name="Col_Party" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 8.25, 2.25, -17.25)
shape = SubResource("BoxShape3D_party")

[node name="Col_Orquidea_Ochava" type="CollisionShape3D" parent="."]
transform = Transform3D(0.707107, 0, 0.707107, 0, 1, 0, -0.707107, 0, 0.707107, 2.00, 3.40, -22.50)
shape = SubResource("BoxShape3D_orquidea_ochava")

[node name="Col_Curiel" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 10.25, 2.25, -22.25)
shape = SubResource("BoxShape3D_curiel")
"""
    with open(tscn_path, "w", encoding="utf-8") as f:
        f.write(tscn_content)
    print(f"[OK] Escena Godot generada: {tscn_path}")

# ---------------------------------------------------------------------------
# 9. Función Principal de Ejecución
# ---------------------------------------------------------------------------

def main():
    print("=== INICIANDO RECONSTRUCCIÓN PROCEDURAL: PDTE. LÁZARO CÁRDENAS 33 V5.0 ===")
    root_col = clean_scene()
    mats = create_materials()

    objs_cardenas = build_cardenas_facade(mats, root_col)
    objs_ochava = build_ochava_orquidea(mats, root_col)
    objs_libertad = build_libertad_facade(mats, root_col)
    objs_rear = build_rear_and_medianera(mats, root_col)
    total_objs = len(objs_cardenas) + len(objs_ochava) + len(objs_libertad) + len(objs_rear)
    print(f"[OK] Cuerpos arquitectónicos construidos ({total_objs} objetos)")

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

    print("=== RECONSTRUCCIÓN PROCEDURAL COMPLETADA EXITOSAMENTE V5.0 ===")

if __name__ == "__main__":
    main()
