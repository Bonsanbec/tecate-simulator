"""
=============================================================================
GENERADOR PROCEDURAL 3D UNIVERSAL: COMPLEJO COMERCIAL CONTINUO ABELARDO L. RODRÍGUEZ
(ÉPOCA: SEPTIEMBRE 2009 - VERSIÓN GROUND-TRUTH ALTA RESOLUCIÓN)
=============================================================================
Reconstrucción fidedigna de la crujía continua de 5 locales comerciales:
  - Ubicación: Pdte. Abelardo L. Rodríguez (entre Calle Libertad y límite sur)
  - Manzana: block_lat_32.57255_lon_-116.62529 (Tecate, B.C.)
  - Contrato Cartesiano Canónico:
      * Origen (0, 0, 0): Esquina inferior izquierda (límite sur con portón verde)
      * Eje +X: Longitud de fachada hacia el Norte a lo largo de Abelardo L. Rodríguez (26.00 m)
      * Eje +Y: Profundidad hacia el interior de la manzana / Poniente (14.50 m)
      * Eje +Z: Cota vertical (Normal de rasante al cenit)
  - Locales incluidos:
      1. Saldos de Telas y Retazos (X: 0.00 a 4.75 m)
      2. Electrónica Hidalgo / Electrónica Imán (X: 4.75 a 9.35 m)
      3. LA PANZA: Caseta Telefónica y Centro de Nutrición (X: 9.35 a 16.90 m)
      4. Lonchería Conchita (X: 16.90 a 21.20 m)
      5. Bienes Raíces / Belrom Asesorías (X: 21.20 a 26.00 m + retorno en Calle Libertad)
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
    root_col = bpy.data.collections.new("Continuo_La_Panza_Root")
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
    bm.faces.new((verts[0], verts[4], verts[5], verts[1])) # -Y Front
    bm.faces.new((verts[1], verts[5], verts[6], verts[2])) # +X Right
    bm.faces.new((verts[2], verts[6], verts[7], verts[3])) # +Y Rear
    bm.faces.new((verts[3], verts[7], verts[4], verts[0])) # -X Left
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

def create_3d_text(name, text_string, size, extrude, pos, rot_euler, mat, col, align_x='CENTER'):
    """Crea una entidad tipográfica 3D orientada con su normal hacia la calle."""
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
    """Genera la suite de materiales PBR fotorrealistas para la crujía comercial."""
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

    # Estucos de Fachada
    mats["estuco_blanco"] = _make_mat("M_Estuco_Blanco", (0.92, 0.91, 0.88, 1.0), rough=0.85)
    mats["estuco_morado"] = _make_mat("M_Estuco_Morado_LaPanza", (0.35, 0.12, 0.52, 1.0), rough=0.78)
    mats["estuco_ocre"] = _make_mat("M_Estuco_Ocre_Electronica", (0.75, 0.45, 0.22, 1.0), rough=0.88)
    mats["estuco_crema"] = _make_mat("M_Estuco_Crema_BienesRaices", (0.86, 0.83, 0.76, 1.0), rough=0.82)
    mats["cantera_rosada"] = _make_mat("M_Cantera_Rosada", (0.72, 0.50, 0.45, 1.0), rough=0.75)

    # Zócalo Basal Subterráneo
    mats["zocalo_basal"] = _make_mat("M_Zocalo_Basal", (0.18, 0.16, 0.20, 1.0), rough=0.92)

    # Metales y Cancelería
    mats["aluminio_oscuro"] = _make_mat("M_Aluminio_Oscuro", (0.05, 0.05, 0.055, 1.0), rough=0.35, metal=0.85)
    mats["aluminio_blanco"] = _make_mat("M_Aluminio_Blanco", (0.85, 0.85, 0.85, 1.0), rough=0.40, metal=0.70)
    mats["chapa_galvanizada"] = _make_mat("M_Chapa_Galvanizada", (0.65, 0.67, 0.69, 1.0), rough=0.45, metal=0.75)
    mats["cortina_metalica"] = _make_mat("M_Cortina_Metalica", (0.55, 0.56, 0.58, 1.0), rough=0.50, metal=0.65)
    mats["herreria_negra"] = _make_mat("M_Herreria_Negra", (0.04, 0.04, 0.04, 1.0), rough=0.40, metal=0.90)

    # Vidrio
    mats["vidrio_comercial"] = _make_mat("M_Vidrio_Comercial", (0.10, 0.15, 0.18, 1.0), rough=0.08, transmission=0.85, ior=1.52)

    # Toldos y Lonas
    mats["toldo_amarillo"] = _make_mat("M_Toldo_Amarillo_Iman", (0.88, 0.65, 0.12, 1.0), rough=0.65)
    mats["toldo_conchita"] = _make_mat("M_Toldo_Rojo_Conchita", (0.75, 0.12, 0.10, 1.0), rough=0.60)
    mats["marquesina_rayada"] = _make_mat("M_Marquesina_Rayada", (0.85, 0.45, 0.45, 1.0), rough=0.70)

    # Colores Tipográficos
    mats["texto_rojo"] = _make_mat("M_Texto_Rojo", (0.82, 0.08, 0.06, 1.0), rough=0.50)
    mats["texto_morado"] = _make_mat("M_Texto_Morado", (0.32, 0.09, 0.48, 1.0), rough=0.50)
    mats["texto_verde"] = _make_mat("M_Texto_Verde", (0.08, 0.55, 0.18, 1.0), rough=0.50)
    mats["texto_verde_limon"] = _make_mat("M_Texto_Verde_Limon", (0.12, 0.75, 0.22, 1.0), rough=0.45)
    mats["texto_azul"] = _make_mat("M_Texto_Azul", (0.06, 0.22, 0.62, 1.0), rough=0.50)
    mats["texto_blanco"] = _make_mat("M_Texto_Blanco", (0.95, 0.95, 0.95, 1.0), rough=0.40)
    mats["texto_negro"] = _make_mat("M_Texto_Negro", (0.02, 0.02, 0.02, 1.0), rough=0.50)
    mats["amarillo_cubeta"] = _make_mat("M_Amarillo_Cubeta", (0.92, 0.75, 0.08, 1.0), rough=0.60)
    mats["panel_blanco_cartel"] = _make_mat("M_Panel_Blanco_Cartel", (0.96, 0.96, 0.94, 1.0), rough=0.30)

    # Azotea y Cubierta
    mats["azotea_asfalto"] = _make_mat("M_Azotea_Asfalto", (0.12, 0.12, 0.13, 1.0), rough=0.95)
    mats["piso_comercial"] = _make_mat("M_Piso_Interior", (0.75, 0.72, 0.68, 1.0), rough=0.55)

    return mats

# ---------------------------------------------------------------------------
# 3. Módulos Arquitectónicos Procedurales
# ---------------------------------------------------------------------------

def build_zocalo_basal(mats, col):
    """Zócalo basal subterráneo continuo (Z = -1.20 m a 0.00 m) para absorber la rasante."""
    bm = bmesh.new()
    # Muros perimetrales enterrados
    # Frente este (Y = 0)
    add_box(bm, -0.05, 26.05, -0.05, 0.35, -1.20, 0.00)
    # Lateral norte (X = 26.0)
    add_box(bm, 25.70, 26.05, 0.00, 14.55, -1.20, 0.00)
    # Fondo oeste (Y = 14.50)
    add_box(bm, -0.05, 26.05, 14.20, 14.55, -1.20, 0.00)
    # Medianera sur (X = 0)
    add_box(bm, -0.05, 0.35, 0.00, 14.55, -1.20, 0.00)
    # Firme subterráneo base
    add_box(bm, 0.00, 26.00, 0.00, 14.50, -1.20, -1.05)
    return create_mesh_object("Zocalo_Basal_Subterraneo", bm, mats["zocalo_basal"], col)

def build_envolvente_y_azotea(mats, col):
    """Cuerpo estructural principal, muros posteriores, medianeros y azotea hermética."""
    bm_walls = bmesh.new()
    bm_roof = bmesh.new()
    bm_crown = bmesh.new()

    # Muro medianero sur (X = 0)
    add_box(bm_walls, 0.00, 0.25, 0.00, 14.50, 0.00, 4.70)
    # Muro posterior oeste (Y = 14.50)
    add_box(bm_walls, 0.00, 26.00, 14.25, 14.50, 0.00, 4.35)

    # Losa de azotea continua con pendiente suave hacia el fondo
    # Z = 4.40 m al frente (Y=0.25) descendiendo a Z = 4.10 m atrás (Y=14.25)
    n_divs = 12
    dy = 14.0 / n_divs
    for i in range(n_divs):
        y_start = 0.25 + i * dy
        y_end = y_start + dy
        z_start = 4.40 - (i / n_divs) * 0.30
        z_end = 4.40 - ((i + 1) / n_divs) * 0.30
        add_box(bm_roof, 0.25, 25.75, y_start, y_end, z_end - 0.15, z_start)

    # Albardilla corrida de chapa galvanizada plateada en la corona del pretil
    # Frente este (Y=0)
    add_box(bm_crown, -0.05, 26.08, -0.08, 0.32, 4.65, 4.75)
    # Lateral norte (calle Libertad)
    add_box(bm_crown, 25.75, 26.08, 0.00, 14.55, 4.65, 4.75)

    obj_w = create_mesh_object("Muros_Envolvente", bm_walls, mats["estuco_blanco"], col)
    obj_r = create_mesh_object("Azotea_Hermetica", bm_roof, mats["azotea_asfalto"], col)
    obj_c = create_mesh_object("Albardilla_Pretil_Galvanizada", bm_crown, mats["chapa_galvanizada"], col)
    return obj_w, obj_r, obj_c

def build_modulo_1_saldos_telas(mats, col):
    """Módulo 1: Saldos de Telas y Retazos (X = 0.00 a 4.75 m)."""
    bm_wall = bmesh.new()
    bm_shutter = bmesh.new()

    # Pretil blanco
    add_box(bm_wall, 0.00, 4.75, -0.02, 0.25, 2.65, 4.65)
    # Jambas laterales y caja de cortina
    add_box(bm_wall, 0.00, 0.45, -0.02, 0.25, 0.00, 2.65)
    add_box(bm_wall, 4.35, 4.75, -0.02, 0.25, 0.00, 2.65)
    add_box(bm_wall, 0.45, 4.35, -0.02, 0.25, 2.40, 2.65) # Dintel caja

    # Gran cortina metálica cerrada acanalada
    n_slats = 24
    dz = 2.40 / n_slats
    for i in range(n_slats):
        z_min = i * dz
        z_max = z_min + dz * 0.90
        add_box(bm_shutter, 0.45, 4.35, 0.04, 0.08, z_min, z_max)

    create_mesh_object("Mod1_Muros_SaldosTelas", bm_wall, mats["estuco_blanco"], col)
    create_mesh_object("Mod1_Cortina_SaldosTelas", bm_shutter, mats["cortina_metalica"], col)

    # Rótulo tipográfico 3D en pretil (Normal hacia -Y)
    create_3d_text("Texto_SaldosTelas_L1", "SALDOS DE TELAS Y RETAZOS", 0.26, 0.02,
                   (2.40, -0.04, 4.05), (math.radians(90), 0, 0), mats["texto_rojo"], col)
    create_3d_text("Texto_SaldosTelas_L2", "Texturas Finas  •  Para Fiestas", 0.16, 0.015,
                   (2.40, -0.04, 3.60), (math.radians(90), 0, 0), mats["texto_azul"], col)
    create_3d_text("Texto_SaldosTelas_L3", "Para Ropa, Tapicería, Cortinas y Botones", 0.13, 0.015,
                   (2.40, -0.04, 3.25), (math.radians(90), 0, 0), mats["texto_azul"], col)

def build_modulo_2_electronica_hidalgo(mats, col):
    """Módulo 2: Electrónica Hidalgo / Electrónica Imán (X = 4.75 a 9.35 m)."""
    bm_wall = bmesh.new()
    bm_glass = bmesh.new()
    bm_frame = bmesh.new()
    bm_awning = bmesh.new()

    # Pretil estuco ocre anaranjado desgastado
    add_box(bm_wall, 4.75, 9.35, -0.02, 0.25, 2.70, 4.65)
    # Zócalo bajo de antepecho y jambas
    add_box(bm_wall, 4.75, 9.35, -0.02, 0.25, 0.00, 0.45)
    add_box(bm_wall, 4.75, 4.95, -0.02, 0.25, 0.45, 2.70)
    add_box(bm_wall, 9.15, 9.35, -0.02, 0.25, 0.45, 2.70)

    # Cancelería de aluminio y vidriería fija/corrediza
    add_box(bm_glass, 4.95, 9.15, 0.08, 0.10, 0.45, 2.45)
    # Marco perimetral y parteluces
    add_box(bm_frame, 4.93, 9.17, 0.06, 0.12, 0.43, 0.47)
    add_box(bm_frame, 4.93, 9.17, 0.06, 0.12, 2.43, 2.47)
    for x_p in (6.35, 7.75):
        add_box(bm_frame, x_p - 0.03, x_p + 0.03, 0.06, 0.12, 0.45, 2.45)

    # Toldo abovedado semicircular amarillo (Cuarto de cilindro)
    # X: 4.90 a 9.20 m, Y: -0.85 a 0.00 m, Z: 2.15 a 2.95 m
    n_arc = 12
    r_y = 0.85
    r_z = 0.70
    z_center = 2.25
    y_center = 0.00
    for i in range(n_arc):
        th1 = (i / n_arc) * (math.pi / 2.0)
        th2 = ((i + 1) / n_arc) * (math.pi / 2.0)
        y1 = y_center - r_y * math.cos(th1)
        z1 = z_center + r_z * math.sin(th1)
        y2 = y_center - r_y * math.cos(th2)
        z2 = z_center + r_z * math.sin(th2)
        add_box(bm_awning, 4.90, 9.20, min(y1, y2), max(y1, y2), min(z1, z2), max(z1, z2))
    # Faldón perimetral vertical del toldo
    add_box(bm_awning, 4.90, 9.20, -0.88, -0.84, 2.05, 2.25)
    add_box(bm_awning, 4.88, 4.92, -0.85, 0.00, 2.05, 2.25)
    add_box(bm_awning, 9.18, 9.22, -0.85, 0.00, 2.05, 2.25)

    create_mesh_object("Mod2_Muros_Electronica", bm_wall, mats["estuco_ocre"], col)
    create_mesh_object("Mod2_Vidrio_Electronica", bm_glass, mats["vidrio_comercial"], col)
    create_mesh_object("Mod2_Canceleria_Electronica", bm_frame, mats["aluminio_blanco"], col)
    create_mesh_object("Mod2_Toldo_Amarillo", bm_awning, mats["toldo_amarillo"], col)

    # Rótulos de pretil y toldo
    create_3d_text("Texto_Electronica_Hidalgo", "Electronica Hidalgo", 0.32, 0.025,
                   (7.05, -0.04, 3.90), (math.radians(90), 0, 0), mats["texto_azul"], col)
    create_3d_text("Texto_Toldo_Iman", "ELECTRONICA IMAN", 0.16, 0.015,
                   (7.05, -0.89, 2.15), (math.radians(90), 0, 0), mats["texto_blanco"], col)

def build_modulo_3_la_panza(mats, col):
    """Módulo 3: LA PANZA (Caseta Telefónica y Centro de Nutrición) (X = 9.35 a 16.90 m)."""
    bm_white = bmesh.new()
    bm_purple = bmesh.new()
    bm_glass = bmesh.new()
    bm_frame = bmesh.new()
    bm_shutter = bmesh.new()
    bm_interior = bmesh.new()
    bm_panels = bmesh.new()
    bm_cables = bmesh.new()

    # Pretil blanco principal
    add_box(bm_white, 9.55, 16.70, -0.02, 0.25, 2.70, 4.55)
    # Marco morado perimetral superior
    add_box(bm_purple, 9.35, 16.90, -0.03, 0.26, 4.55, 4.68)
    add_box(bm_purple, 9.35, 16.90, -0.03, 0.26, 2.65, 2.75) # Franja divisoria

    # Jambas y Machón Central Morados
    add_box(bm_purple, 9.35, 9.55, -0.03, 0.26, 0.00, 4.68)   # Jamba Izquierda
    add_box(bm_purple, 12.85, 13.20, -0.03, 0.26, 0.00, 4.68) # Machón Central (Nº 330)
    add_box(bm_purple, 16.70, 16.90, -0.03, 0.26, 0.00, 4.68) # Jamba Derecha

    # Zócalo bajo morado en antepechos
    add_box(bm_purple, 9.55, 10.95, -0.02, 0.25, 0.00, 0.75)  # Bajo ventana izq
    add_box(bm_purple, 15.05, 16.70, -0.02, 0.25, 0.00, 0.45) # Bajo vitrina der

    # Bahía Izquierda: Ventana con cortina metálica acanalada y pasadores
    n_sl = 18
    dz = (2.35 - 0.75) / n_sl
    for i in range(n_sl):
        z_m = 0.75 + i * dz
        add_box(bm_shutter, 9.60, 10.90, 0.04, 0.08, z_m, z_m + dz * 0.85)
    # Visera superior blanca sobre la ventana
    add_box(bm_white, 9.55, 10.95, -0.06, 0.06, 2.35, 2.42)
    # Dos pasadores/cerraduras horizontales oscuras en la cortina metálica
    add_box(bm_frame, 9.75, 10.75, -0.03, 0.05, 1.25, 1.29)
    add_box(bm_frame, 9.75, 10.75, -0.03, 0.05, 1.75, 1.79)

    # Puerta vidriada izquierda de ARTÍCULOS (X: 10.95 a 12.85 m)
    add_box(bm_glass, 11.00, 12.80, 0.06, 0.08, 0.00, 2.35)
    # Cancelería de aluminio blanco / anodizado claro
    add_box(bm_frame, 10.96, 12.84, 0.04, 0.10, 0.00, 0.05) # Zócalo puerta
    add_box(bm_frame, 10.96, 12.84, 0.04, 0.10, 2.32, 2.37) # Dintel puerta
    add_box(bm_frame, 10.96, 11.02, 0.04, 0.10, 0.00, 2.35) # Jamba izq cancel
    add_box(bm_frame, 12.78, 12.84, 0.04, 0.10, 0.00, 2.35) # Jamba der cancel
    add_box(bm_frame, 11.87, 11.93, 0.04, 0.10, 0.00, 2.35) # Montante central
    # Dos manijas tubulares de aluminio
    add_box(bm_frame, 11.84, 11.87, -0.02, 0.04, 0.95, 1.25)
    add_box(bm_frame, 11.93, 11.96, -0.02, 0.04, 0.95, 1.25)
    # Dintel morado sobre puerta izquierda
    add_box(bm_purple, 10.95, 12.85, -0.02, 0.25, 2.35, 2.65)
    # Caja de cortina superior sobre puerta
    add_box(bm_shutter, 10.95, 12.85, -0.06, 0.12, 2.65, 2.75)

    # Bahía Derecha: Acceso Peatonal Principal Transitable (X: 13.20 a 15.05 m)
    # ¡VANO LIBRE A NIVEL DE SUELO!
    # Caja de cortina enrollada arriba en el dintel
    add_box(bm_shutter, 13.20, 15.05, -0.08, 0.15, 2.35, 2.65)

    # Cartel vertical en la jamba interior izquierda de la entrada (junto al machón)
    add_box(bm_panels, 13.24, 13.26, 0.05, 0.35, 1.05, 2.30)

    # Escaparate vidriado derecho (X: 15.05 a 16.70 m)
    add_box(bm_glass, 15.10, 16.65, 0.06, 0.08, 0.45, 2.35)
    # Marco de cancelería de aluminio anodizado claro
    add_box(bm_frame, 15.05, 16.70, 0.04, 0.10, 0.43, 0.47)
    add_box(bm_frame, 15.05, 16.70, 0.04, 0.10, 2.33, 2.38)
    add_box(bm_frame, 15.05, 15.10, 0.04, 0.10, 0.45, 2.35)
    add_box(bm_frame, 16.65, 16.70, 0.04, 0.10, 0.45, 2.35)
    add_box(bm_frame, 15.82, 15.88, 0.04, 0.10, 0.45, 2.35) # Parteluz divisorio de vitrina
    add_box(bm_purple, 15.05, 16.70, -0.02, 0.25, 2.35, 2.65)

    # Paneles de fondo blanco esmaltado para los carteles de la vitrina derecha
    add_box(bm_panels, 15.12, 15.80, 0.055, 0.06, 0.50, 2.30) # Panel mayoreo
    add_box(bm_panels, 15.90, 16.63, 0.055, 0.06, 0.50, 2.30) # Panel tarifario

    # Interior comercial visible (Suelo, mostrador, cubeta y anaqueles)
    add_box(bm_interior, 13.00, 16.80, 0.25, 4.50, 0.00, 0.02) # Piso cerámico
    # Mostrador en escuadra con faldón morado
    add_box(bm_purple, 13.80, 16.20, 1.80, 2.40, 0.02, 1.05)
    add_box(bm_interior, 13.78, 16.22, 1.78, 2.42, 1.04, 1.08) # Cubierta mostrador
    add_box(bm_purple, 16.00, 16.50, 2.40, 4.00, 0.02, 1.05)
    # Cubeta / bote amarillo de servicio en el rincón del suelo
    for i in range(12):
        ang1 = (i / 12) * 2 * math.pi
        ang2 = ((i + 1) / 12) * 2 * math.pi
        b_x = 13.45 + 0.12 * math.cos(ang1)
        b_y = 0.55 + 0.12 * math.sin(ang1)
        b_x2 = 13.45 + 0.12 * math.cos(ang2)
        b_y2 = 0.55 + 0.12 * math.sin(ang2)
        add_box(bm_interior, min(b_x, b_x2, 13.45), max(b_x, b_x2, 13.45), min(b_y, b_y2, 0.55), max(b_y, b_y2, 0.55), 0.00, 0.38)
    # Anaqueles de productos nutricionales en pared posterior
    for z_st in (0.80, 1.30, 1.80):
        add_box(bm_interior, 13.20, 16.60, 4.20, 4.45, z_st, z_st + 0.04)

    # ACOMETIDA ELÉCTRICA Y MAZO DE CABLES EN FACHADA (Sobre la 'A' de 'LA' izquierda)
    # Mufa / tubo conduit vertical
    add_box(bm_cables, 10.45, 10.49, -0.06, -0.02, 4.20, 4.68)
    # Aisladores cerámicos y caja de acometida
    add_box(bm_cables, 10.40, 10.54, -0.08, -0.02, 4.40, 4.55)
    # Mazo de cables negros trenzados en abanico
    for c_dx in (-0.18, -0.08, 0.05, 0.15):
        add_box(bm_cables, 10.45 + c_dx - 0.015, 10.45 + c_dx + 0.015, -0.07, -0.03, 4.05, 4.45)

    # LETRERO VOLANTE BANDEROLA PERPENDICULAR (X = 13.025 m)
    bm_volante = bmesh.new()
    bm_brazos = bmesh.new()
    # Caja central blanca esmaltada
    add_box(bm_volante, 12.98, 13.07, -0.95, -0.05, 3.15, 4.45)
    # Marco morado exterior de la caja
    add_box(bm_purple, 12.96, 13.09, -0.96, -0.04, 4.43, 4.47)
    add_box(bm_purple, 12.96, 13.09, -0.96, -0.04, 3.13, 3.17)
    add_box(bm_purple, 12.96, 13.09, -0.97, -0.94, 3.15, 4.45)
    # Brazos de anclaje de herrería negra hacia el machón
    add_box(bm_brazos, 12.97, 13.08, -0.90, -0.02, 4.30, 4.35)
    add_box(bm_brazos, 12.97, 13.08, -0.90, -0.02, 3.25, 3.30)
    add_box(bm_brazos, 12.97, 13.08, -0.55, -0.02, 3.30, 4.30)

    create_mesh_object("Mod3_Muros_Blancos_LaPanza", bm_white, mats["estuco_blanco"], col)
    create_mesh_object("Mod3_Marcos_Morados_LaPanza", bm_purple, mats["estuco_morado"], col)
    create_mesh_object("Mod3_Vidrio_LaPanza", bm_glass, mats["vidrio_comercial"], col)
    create_mesh_object("Mod3_Canceleria_LaPanza", bm_frame, mats["aluminio_blanco"], col)
    create_mesh_object("Mod3_Cortinas_LaPanza", bm_shutter, mats["cortina_metalica"], col)
    create_mesh_object("Mod3_Paneles_Carteles", bm_panels, mats["panel_blanco_cartel"], col)
    create_mesh_object("Mod3_Interior_LaPanza", bm_interior, mats["piso_comercial"], col)
    create_mesh_object("Mod3_Cables_Acometida", bm_cables, mats["herreria_negra"], col)
    create_mesh_object("Mod3_Letrero_Volante_Caja", bm_volante, mats["estuco_blanco"], col)
    create_mesh_object("Mod3_Brazos_Herreria", bm_brazos, mats["herreria_negra"], col)

    # -----------------------------------------------------------------------
    # Rótulos Tipográficos 3D Fotorrealistas
    # -----------------------------------------------------------------------
    # 1. Fachada Frontal - Bahía Izquierda
    create_3d_text("Texto_LP_Izq_L1", "CASETA TELEFONICA", 0.18, 0.015,
                   (11.20, -0.04, 4.25), (math.radians(90), 0, 0), mats["texto_rojo"], col)
    create_3d_text("Texto_LP_Izq_L2", "LA PANZA", 0.34, 0.025,
                   (11.20, -0.04, 3.75), (math.radians(90), 0, 0), mats["texto_morado"], col)
    create_3d_text("Texto_LP_Izq_L3", "CENTRO de NUTRICION", 0.18, 0.015,
                   (11.20, -0.04, 3.30), (math.radians(90), 0, 0), mats["texto_verde"], col)

    # 2. Fachada Frontal - Bahía Derecha
    create_3d_text("Texto_LP_Der_L1", "CASETA TELEFONICA", 0.18, 0.015,
                   (14.95, -0.04, 4.25), (math.radians(90), 0, 0), mats["texto_rojo"], col)
    create_3d_text("Texto_LP_Der_L2", "LA PANZA", 0.34, 0.025,
                   (14.95, -0.04, 3.75), (math.radians(90), 0, 0), mats["texto_morado"], col)
    create_3d_text("Texto_LP_Der_L3", "CENTRO de NUTRICION", 0.18, 0.015,
                   (14.95, -0.04, 3.30), (math.radians(90), 0, 0), mats["texto_verde"], col)

    # 3. Machón Central: Número Oficial "Nº 330" en cursiva
    create_3d_text("Texto_LP_Numero330", "Nº 330", 0.12, 0.01,
                   (13.025, -0.04, 2.45), (math.radians(90), 0, 0), mats["texto_blanco"], col)

    # 4. Puerta Izquierda: Dintel "ARTICULOS"
    create_3d_text("Texto_LP_Articulos", "ARTICULOS", 0.16, 0.012,
                   (11.90, -0.04, 2.50), (math.radians(90), 0, 0), mats["texto_azul"], col)

    # 5. Puerta Izquierda: Vinilos pintados en cristales ($4.00 y $6.00 / PRECIO ESPECIAL POR MAYOREO)
    create_3d_text("Texto_LP_Precio4", "$4", 0.44, 0.01,
                   (11.45, -0.02, 1.65), (math.radians(90), 0, 0), mats["texto_rojo"], col)
    create_3d_text("Texto_LP_Sup4", ".00", 0.18, 0.008,
                   (11.75, -0.02, 1.82), (math.radians(90), 0, 0), mats["texto_rojo"], col)
    create_3d_text("Texto_LP_Y_Central", "y", 0.18, 0.008,
                   (11.90, -0.02, 1.55), (math.radians(90), 0, 0), mats["texto_morado"], col)
    create_3d_text("Texto_LP_Precio6", "$6", 0.44, 0.01,
                   (12.35, -0.02, 1.65), (math.radians(90), 0, 0), mats["texto_rojo"], col)
    create_3d_text("Texto_LP_Sup6", ".00", 0.18, 0.008,
                   (12.65, -0.02, 1.82), (math.radians(90), 0, 0), mats["texto_rojo"], col)
    # Textos inferiores en verde limón
    create_3d_text("Texto_LP_Precio", "PRECIO", 0.13, 0.008,
                   (11.45, -0.02, 1.15), (math.radians(90), 0, 0), mats["texto_verde_limon"], col)
    create_3d_text("Texto_LP_Por", "POR", 0.13, 0.008,
                   (11.45, -0.02, 0.95), (math.radians(90), 0, 0), mats["texto_verde_limon"], col)
    create_3d_text("Texto_LP_Especial", "ESPECIAL", 0.13, 0.008,
                   (12.35, -0.02, 1.15), (math.radians(90), 0, 0), mats["texto_verde_limon"], col)
    create_3d_text("Texto_LP_Mayoreo", "MAYOREO", 0.13, 0.008,
                   (12.35, -0.02, 0.95), (math.radians(90), 0, 0), mats["texto_verde_limon"], col)

    # 6. Cartel en la Jamba Interior Izquierda de la Entrada (Rotación hacia +X para ver desde la entrada)
    rot_jamba = (math.radians(90), 0, math.radians(90))
    create_3d_text("Texto_Jamba_Articulos", "ARTICULOS", 0.075, 0.006,
                   (13.27, 0.20, 2.15), rot_jamba, mats["texto_rojo"], col)
    create_3d_text("Texto_Jamba_Hogar", "HOGAR", 0.075, 0.006,
                   (13.27, 0.20, 1.95), rot_jamba, mats["texto_azul"], col)
    create_3d_text("Texto_Jamba_Bisuteria", "BISUTERIA", 0.075, 0.006,
                   (13.27, 0.20, 1.75), rot_jamba, mats["texto_verde"], col)
    create_3d_text("Texto_Jamba_Papeleria", "PAPELERIA", 0.075, 0.006,
                   (13.27, 0.20, 1.55), rot_jamba, mats["texto_rojo"], col)
    create_3d_text("Texto_Jamba_Juguetes", "JUGUETES", 0.075, 0.006,
                   (13.27, 0.20, 1.35), rot_jamba, mats["texto_azul"], col)

    # 7. Escaparate Derecho - Panel Izquierdo: PRECIO ESPECIAL POR MAYOREO 4.00 y 6.00
    create_3d_text("Texto_Vit_Der_Precio", "PRECIO", 0.065, 0.006,
                   (15.45, -0.03, 2.15), (math.radians(90), 0, 0), mats["texto_azul"], col)
    create_3d_text("Texto_Vit_Der_Especial", "ESPECIAL", 0.065, 0.006,
                   (15.45, -0.03, 2.02), (math.radians(90), 0, 0), mats["texto_azul"], col)
    create_3d_text("Texto_Vit_Der_Por", "POR", 0.065, 0.006,
                   (15.45, -0.03, 1.89), (math.radians(90), 0, 0), mats["texto_azul"], col)
    create_3d_text("Texto_Vit_Der_Mayoreo", "MAYOREO", 0.065, 0.006,
                   (15.45, -0.03, 1.76), (math.radians(90), 0, 0), mats["texto_azul"], col)
    create_3d_text("Texto_Vit_Der_Num4", "4.00", 0.24, 0.008,
                   (15.35, -0.03, 1.40), (math.radians(90), 0, 0), mats["texto_rojo"], col)
    create_3d_text("Texto_Vit_Der_Y", "y", 0.10, 0.006,
                   (15.55, -0.03, 1.30), (math.radians(90), 0, 0), mats["texto_morado"], col)
    create_3d_text("Texto_Vit_Der_Num6", "6.00", 0.24, 0.008,
                   (15.55, -0.03, 1.05), (math.radians(90), 0, 0), mats["texto_rojo"], col)

    # 8. Escaparate Derecho - Panel Derecho: TABLA TARIFARIA COMPLETA
    create_3d_text("Texto_Tarifa_Titulo", "LLAMADA :", 0.075, 0.006,
                   (16.25, -0.03, 2.18), (math.radians(90), 0, 0), mats["texto_verde"], col)
    tarifas = [
        ("LOCAL", "$ 1.00", 2.03),
        ("NACIONAL", "$ 2.00", 1.89),
        ("CEL. LOCAL", "$ 4.00", 1.75),
        ("CELULAR L.D.", "$ 4.00", 1.61),
        ("USA", "$ 4.00", 1.47),
        ("CENTRO AMERICA", "$ 6.00", 1.33),
        ("SUD AMERICA", "$ 8.00", 1.19),
        ("RESTO DEL MUNDO", "$ 10.00", 1.05),
    ]
    for dest, precio, z_pos in tarifas:
        create_3d_text("Tarifa_Dest_" + dest[:4], dest, 0.046, 0.004,
                       (16.08, -0.03, z_pos), (math.radians(90), 0, 0), mats["texto_azul"], col, align_x='RIGHT')
        create_3d_text("Tarifa_Precio_" + dest[:4], precio, 0.052, 0.004,
                       (16.42, -0.03, z_pos), (math.radians(90), 0, 0), mats["texto_rojo"], col, align_x='LEFT')

    # 9. LETRERO VOLANTE - Cara Sur (Normal hacia -X)
    rot_sur = (math.radians(90), 0, math.radians(-90))
    create_3d_text("Texto_Volante_Sur_L1", "CASETA TELEFONICA", 0.09, 0.008,
                   (12.95, -0.50, 4.20), rot_sur, mats["texto_rojo"], col)
    create_3d_text("Texto_Volante_Sur_L2", "LA PANZA", 0.18, 0.012,
                   (12.95, -0.50, 3.80), rot_sur, mats["texto_morado"], col)
    create_3d_text("Texto_Volante_Sur_L3", "CENTRO de NUTRICION", 0.08, 0.008,
                   (12.95, -0.50, 3.40), rot_sur, mats["texto_verde"], col)

    # 10. LETRERO VOLANTE - Cara Norte (Normal hacia +X)
    rot_norte = (math.radians(90), 0, math.radians(90))
    create_3d_text("Texto_Volante_Norte_L1", "CASETA TELEFONICA", 0.09, 0.008,
                   (13.10, -0.50, 4.20), rot_norte, mats["texto_rojo"], col)
    create_3d_text("Texto_Volante_Norte_L2", "LA PANZA", 0.18, 0.012,
                   (13.10, -0.50, 3.80), rot_norte, mats["texto_morado"], col)
    create_3d_text("Texto_Volante_Norte_L3", "CENTRO de NUTRICION", 0.08, 0.008,
                   (13.10, -0.50, 3.40), rot_norte, mats["texto_verde"], col)

def build_modulo_4_loncheria_conchita(mats, col):
    """Módulo 4: Lonchería Conchita (X = 16.90 a 21.20 m)."""
    bm_wall = bmesh.new()
    bm_red = bmesh.new()
    bm_black = bmesh.new()
    bm_glass = bmesh.new()
    bm_frame = bmesh.new()
    bm_awning = bmesh.new()

    # Pretil general
    add_box(bm_wall, 16.90, 21.20, -0.02, 0.25, 2.70, 4.65)
    # Jambas y antepecho
    add_box(bm_wall, 16.90, 17.15, -0.02, 0.25, 0.00, 2.70)
    add_box(bm_wall, 20.95, 21.20, -0.02, 0.25, 0.00, 2.70)
    add_box(bm_wall, 17.15, 20.95, -0.02, 0.25, 0.00, 0.40) # Zócalo

    # Fascia comercial: Franja negra superior, franja roja Coca-Cola central, franja negra inferior
    add_box(bm_black, 16.90, 21.20, -0.03, 0.26, 4.25, 4.55) # Franja negra sup
    add_box(bm_red, 16.90, 21.20, -0.03, 0.26, 3.25, 4.25)   # Franja roja Coca-Cola
    add_box(bm_black, 16.90, 21.20, -0.03, 0.26, 2.95, 3.25) # Franja negra inf

    # Marquesina / toldo bajo rayado
    add_box(bm_awning, 17.10, 21.00, -0.55, 0.00, 2.45, 2.65)

    # Ventanería y puerta de lonchería
    add_box(bm_glass, 17.15, 20.95, 0.06, 0.08, 0.40, 2.45)
    add_box(bm_frame, 17.12, 20.98, 0.04, 0.10, 0.38, 0.42)
    add_box(bm_frame, 17.12, 20.98, 0.04, 0.10, 2.43, 2.47)
    add_box(bm_frame, 18.80, 18.86, 0.04, 0.10, 0.00, 2.45) # Parteluz acceso

    create_mesh_object("Mod4_Muros_Conchita", bm_wall, mats["estuco_blanco"], col)
    create_mesh_object("Mod4_Fascia_Roja", bm_red, mats["toldo_conchita"], col)
    create_mesh_object("Mod4_Fascia_Negra", bm_black, mats["texto_negro"], col)
    create_mesh_object("Mod4_Marquesina_Conchita", bm_awning, mats["marquesina_rayada"], col)
    create_mesh_object("Mod4_Vidrio_Conchita", bm_glass, mats["vidrio_comercial"], col)
    create_mesh_object("Mod4_Canceleria_Conchita", bm_frame, mats["aluminio_oscuro"], col)

    # Textos de fascia
    create_3d_text("Texto_Conchita_L1", "LONCHERIA CONCHITA", 0.20, 0.015,
                   (19.05, -0.04, 4.38), (math.radians(90), 0, 0), mats["texto_blanco"], col)
    create_3d_text("Texto_Conchita_CocaCola", "Coca-Cola", 0.32, 0.02,
                   (19.05, -0.04, 3.75), (math.radians(90), 0, 0), mats["texto_blanco"], col)
    create_3d_text("Texto_Conchita_L3", "CALDOS DE POLLO RES Y COMIDAS CORRIDAS", 0.11, 0.01,
                   (19.05, -0.04, 3.10), (math.radians(90), 0, 0), mats["texto_blanco"], col)

def build_modulo_5_esquina_bienes_raices(mats, col):
    """Módulo 5: Esquina Norte 'Bienes Raíces / Belrom Asesorías' (X = 21.20 a 26.00 m)."""
    bm_wall = bmesh.new()
    bm_stone = bmesh.new()
    bm_glass = bmesh.new()
    bm_frame = bmesh.new()
    bm_clock = bmesh.new()
    bm_billboard = bmesh.new()

    # Pretil y fachada este en estuco crema
    add_box(bm_wall, 21.20, 26.00, -0.02, 0.25, 2.70, 4.65)
    # Jambas este
    add_box(bm_wall, 21.20, 21.90, -0.02, 0.25, 0.00, 2.70)
    add_box(bm_wall, 25.30, 26.00, -0.02, 0.25, 0.00, 2.70)
    add_box(bm_wall, 21.90, 25.30, -0.02, 0.25, 0.00, 0.50) # Zócalo bajo vitrina

    # GRAN ARCO DE MEDIO PUNTO EN CANTERA ROSADA
    # Centro en X = 23.60 m, Z = 2.40 m. Radio interior = 1.30 m, radio exterior = 1.65 m
    c_x = 23.60
    c_z = 2.40
    r_in = 1.30
    r_out = 1.65
    n_seg = 18
    for i in range(n_seg):
        a1 = (i / n_seg) * math.pi
        a2 = ((i + 1) / n_seg) * math.pi
        # Vértices del segmento de arco
        p1_x = c_x - r_out * math.cos(a1)
        p1_z = c_z + r_out * math.sin(a1)
        p2_x = c_x - r_out * math.cos(a2)
        p2_z = c_z + r_out * math.sin(a2)
        p3_x = c_x - r_in * math.cos(a2)
        p3_z = c_z + r_in * math.sin(a2)
        p4_x = c_x - r_in * math.cos(a1)
        p4_z = c_z + r_in * math.sin(a1)
        add_box(bm_stone, min(p1_x, p2_x, p3_x, p4_x), max(p1_x, p2_x, p3_x, p4_x),
                -0.08, 0.00, min(p1_z, p2_z, p3_z, p4_z), max(p1_z, p2_z, p3_z, p4_z))

    # Columnas / machones verticales de cantera rosada a los lados del arco
    add_box(bm_stone, 21.95, 22.30, -0.08, 0.00, 0.00, 2.40)
    add_box(bm_stone, 24.90, 25.25, -0.08, 0.00, 0.00, 2.40)

    # RELOJ ANALÓGICO CIRCULAR EN EL TÍMPANO DEL ARCO
    # Centro en X = 23.60 m, Z = 3.35 m, Radio = 0.35 m
    r_clock = 0.35
    for i in range(16):
        ang1 = (i / 16) * 2 * math.pi
        ang2 = ((i + 1) / 16) * 2 * math.pi
        x1 = c_x + r_clock * math.cos(ang1)
        z1 = 3.35 + r_clock * math.sin(ang1)
        x2 = c_x + r_clock * math.cos(ang2)
        z2 = 3.35 + r_clock * math.sin(ang2)
        add_box(bm_clock, min(x1, x2, c_x), max(x1, x2, c_x), -0.08, -0.02, min(z1, z2, 3.35), max(z1, z2, 3.35))
    
    # Marco anular exterior oscuro del reloj (anillo abierto para dejar visible la esfera blanca)
    r_f_out = 0.39
    r_f_in = 0.35
    for i in range(16):
        ang1 = (i / 16) * 2 * math.pi
        ang2 = ((i + 1) / 16) * 2 * math.pi
        p1x = c_x + r_f_out * math.cos(ang1)
        p1z = 3.35 + r_f_out * math.sin(ang1)
        p2x = c_x + r_f_out * math.cos(ang2)
        p2z = 3.35 + r_f_out * math.sin(ang2)
        p3x = c_x + r_f_in * math.cos(ang2)
        p3z = 3.35 + r_f_in * math.sin(ang2)
        p4x = c_x + r_f_in * math.cos(ang1)
        p4z = 3.35 + r_f_in * math.sin(ang1)
        add_box(bm_frame, min(p1x, p2x, p3x, p4x), max(p1x, p2x, p3x, p4x),
                -0.10, -0.06, min(p1z, p2z, p3z, p4z), max(p1z, p2z, p3z, p4z))

    # Manecillas del reloj en negro
    add_box(bm_frame, c_x - 0.015, c_x + 0.015, -0.11, -0.08, 3.35, 3.60) # Minutero (hacia las 12)
    add_box(bm_frame, c_x, c_x + 0.18, -0.11, -0.08, 3.335, 3.365)        # Horario (hacia las 3)

    # Vitrina inferior de Bienes Raíces
    add_box(bm_glass, 22.35, 24.85, 0.06, 0.08, 0.50, 2.35)
    add_box(bm_frame, 22.30, 24.90, 0.04, 0.10, 0.48, 0.52)
    add_box(bm_frame, 22.30, 24.90, 0.04, 0.10, 2.33, 2.37)

    # FACHADA LATERAL NORTE (CALLE LIBERTAD, X = 26.00 m)
    # Muro principal sobre Libertad
    add_box(bm_wall, 25.75, 26.02, 0.00, 14.50, 2.70, 4.65)
    add_box(bm_wall, 25.75, 26.02, 0.00, 1.20, 0.00, 2.70)
    add_box(bm_wall, 25.75, 26.02, 4.80, 14.50, 0.00, 2.70)
    add_box(bm_wall, 25.75, 26.02, 1.20, 4.80, 0.00, 0.60) # Antepecho bajo vitrina

    # Marco de cantera rosada para el escaparate de Joyería en Libertad
    add_box(bm_stone, 26.02, 26.10, 1.15, 4.85, 0.55, 0.65)
    add_box(bm_stone, 26.02, 26.10, 1.15, 4.85, 2.35, 2.45)
    add_box(bm_stone, 26.02, 26.10, 1.15, 1.30, 0.60, 2.40)
    add_box(bm_stone, 26.02, 26.10, 4.70, 4.85, 0.60, 2.40)

    # Vidrio de vitrina Joyería
    add_box(bm_glass, 25.90, 25.95, 1.30, 4.70, 0.65, 2.35)

    # Marco rectangular biselado para el rótulo "BELROM ASESORIAS" sobre Libertad
    add_box(bm_wall, 26.02, 26.08, 1.00, 5.00, 3.20, 4.30)

    # ANUNCIO ESPECTACULAR EN AZOTEA (BELROM)
    # Estructura reticular metálica en azotea (X: 22.5 a 25.5 m, Y: 1.0 a 3.5 m)
    add_box(bm_billboard, 22.80, 22.90, 1.20, 1.30, 4.40, 6.80)
    add_box(bm_billboard, 25.20, 25.30, 1.20, 1.30, 4.40, 6.80)
    add_box(bm_billboard, 22.80, 22.90, 3.20, 3.30, 4.40, 5.80)
    add_box(bm_billboard, 25.20, 25.30, 3.20, 3.30, 4.40, 5.80)
    # Tirantes diagonales
    add_box(bm_billboard, 22.80, 25.30, 1.20, 1.28, 5.30, 5.38)
    add_box(bm_billboard, 22.80, 25.30, 1.20, 1.28, 6.70, 6.78)
    # Gran cartel inclinado
    add_box(bm_wall, 22.50, 25.60, 1.15, 1.25, 5.10, 6.75)

    create_mesh_object("Mod5_Muros_BienesRaices", bm_wall, mats["estuco_crema"], col)
    create_mesh_object("Mod5_Cantera_Arco_BienesRaices", bm_stone, mats["cantera_rosada"], col)
    create_mesh_object("Mod5_Reloj_BienesRaices", bm_clock, mats["estuco_blanco"], col)
    create_mesh_object("Mod5_Vidrio_BienesRaices", bm_glass, mats["vidrio_comercial"], col)
    create_mesh_object("Mod5_Canceleria_BienesRaices", bm_frame, mats["aluminio_oscuro"], col)
    create_mesh_object("Mod5_Estructura_Espectacular", bm_billboard, mats["herreria_negra"], col)

    # Rótulo 3D "BIENES RAICES" sobre el arco en fachada este
    create_3d_text("Texto_BienesRaices", "BIENES RAICES", 0.28, 0.025,
                   (23.60, -0.04, 4.15), (math.radians(90), 0, 0), mats["texto_negro"], col)

    # Rótulo 3D "BELROM ASESORIAS" sobre Calle Libertad (Normal hacia +X)
    rot_libertad = (math.radians(90), 0, math.radians(90))
    create_3d_text("Texto_Belrom_Libertad", "BELROM", 0.40, 0.03,
                   (26.10, 3.00, 3.85), rot_libertad, mats["texto_negro"], col)
    create_3d_text("Texto_Asesorias_Libertad", "ASESORIAS", 0.24, 0.02,
                   (26.10, 3.00, 3.45), rot_libertad, mats["texto_negro"], col)

    # Rótulo "JOYERIA" sobre el escaparate en Calle Libertad
    create_3d_text("Texto_Joyeria_Libertad", "JOYERIA", 0.18, 0.015,
                   (26.10, 3.00, 2.20), rot_libertad, mats["texto_rojo"], col)

    # Cartel espectacular en azotea
    create_3d_text("Texto_Espectacular_Belrom", "BELROM", 0.55, 0.03,
                   (24.05, 1.10, 5.95), (math.radians(90), 0, 0), mats["texto_negro"], col)

# ---------------------------------------------------------------------------
# 4. Configuración de Iluminación y Cámaras de Validación Closed-Loop
# ---------------------------------------------------------------------------

def setup_lighting_and_render(col):
    """Configura el sol diurno de Tecate, luz de cielo ambiental y la batería de cámaras fijas de inspección."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    if hasattr(scene.cycles, 'device'):
        scene.cycles.device = 'CPU'
    scene.cycles.samples = 64

    # Luz de cielo ambiental (World Background) para eliminar sombras negras
    if scene.world is None:
        scene.world = bpy.data.worlds.new("Tecate_World")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.78, 0.86, 0.96, 1.0) # Azul cielo diurno
        bg.inputs["Strength"].default_value = 1.4

    # Sol diurno natural principal (orientado desde el Sur-Oriente)
    sun_data = bpy.data.lights.new(name="Sol_Diurno_Tecate", type='SUN')
    sun_data.energy = 4.2
    sun_data.color = (1.0, 0.97, 0.92)
    sun_obj = bpy.data.objects.new("Sol_Diurno", sun_data)
    sun_obj.rotation_euler = (math.radians(45.0), math.radians(15.0), math.radians(-35.0))
    col.objects.link(sun_obj)

    # Luz de relleno diurna suave hacia la fachada norte (Calle Libertad)
    fill_data = bpy.data.lights.new(name="Luz_Relleno_Libertad", type='SUN')
    fill_data.energy = 2.0
    fill_data.color = (0.85, 0.92, 1.0)
    fill_obj = bpy.data.objects.new("Luz_Relleno_Libertad", fill_data)
    fill_obj.rotation_euler = (math.radians(55.0), math.radians(-25.0), math.radians(115.0))
    col.objects.link(fill_obj)

    # Batería de 9 cámaras de validación técnica
    cameras_config = [
        # (Nombre, Posición XYZ, Target XYZ, Focal mm)
        ("cam_general_este", (13.0, -18.0, 4.5), (13.0, 2.0, 2.6), 28.0),
        ("cam_la_panza_closeup", (13.1, -7.5, 2.4), (13.1, 0.0, 2.5), 35.0),
        ("cam_puerta_articulos", (11.85, -3.6, 1.60), (11.85, 0.0, 1.60), 38.0),
        ("cam_vitrina_tarifario", (15.20, -3.6, 1.60), (15.20, 0.0, 1.60), 38.0),
        ("cam_letrero_volante", (15.5, -4.8, 2.6), (13.0, -0.5, 3.8), 35.0),
        ("cam_esquina_bienes_raices", (29.5, -9.5, 3.8), (23.6, 1.5, 3.2), 32.0),
        ("cam_libertad_norte", (33.0, 4.2, 3.0), (26.0, 4.2, 2.6), 32.0),
        ("cam_sur_electronica_telas", (4.5, -8.0, 2.4), (4.5, 0.0, 2.4), 35.0),
        ("cam_cenital_top", (13.0, 7.25, 36.0), (13.0, 7.25, 0.0), 30.0)
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
# 5. Generador Programático de Escena Godot 4 (.tscn)
# ---------------------------------------------------------------------------

def generate_godot_tscn(tscn_path, glb_path):
    """Escribe la escena de Godot 4 con colisionadores analíticos BoxShape3D sin paredes invisibles."""
    tscn_content = f"""[gd_scene load_steps=12 format=3 uid="uid://edificio_continuo_la_panza_2009"]

[ext_resource type="PackedScene" path="{glb_path}" id="1_glb"]

[sub_resource type="BoxShape3D" id="BoxShape3D_saldos_telas"]
size = Vector3(4.75, 4.70, 0.50)

[sub_resource type="BoxShape3D" id="BoxShape3D_electronica"]
size = Vector3(4.60, 4.70, 0.50)

[sub_resource type="BoxShape3D" id="BoxShape3D_lp_izq"]
size = Vector3(3.50, 4.70, 0.50)

[sub_resource type="BoxShape3D" id="BoxShape3D_lp_machon"]
size = Vector3(0.35, 4.70, 0.50)

[sub_resource type="BoxShape3D" id="BoxShape3D_lp_dintel_acceso"]
size = Vector3(1.85, 2.35, 0.50)

[sub_resource type="BoxShape3D" id="BoxShape3D_lp_der"]
size = Vector3(1.85, 4.70, 0.50)

[sub_resource type="BoxShape3D" id="BoxShape3D_conchita"]
size = Vector3(4.30, 4.70, 0.50)

[sub_resource type="BoxShape3D" id="BoxShape3D_bienes_raices_este"]
size = Vector3(4.80, 4.70, 0.50)

[sub_resource type="BoxShape3D" id="BoxShape3D_libertad_norte"]
size = Vector3(0.50, 4.70, 14.50)

[sub_resource type="BoxShape3D" id="BoxShape3D_muro_posterior"]
size = Vector3(26.00, 4.35, 0.50)

[sub_resource type="BoxShape3D" id="BoxShape3D_medianera_sur"]
size = Vector3(0.50, 4.70, 14.50)

[node name="Edificio_Continuo_LaPanza" type="StaticBody3D"]

[node name="ModelInstance" parent="." instance=ExtResource("1_glb")]

[node name="Col_SaldosTelas" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.375, 2.35, 0.10)
shape = SubResource("BoxShape3D_saldos_telas")

[node name="Col_Electronica" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 7.05, 2.35, 0.10)
shape = SubResource("BoxShape3D_electronica")

[node name="Col_LP_BahiaIzq" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 11.10, 2.35, 0.10)
shape = SubResource("BoxShape3D_lp_izq")

[node name="Col_LP_MachonCentral" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 13.025, 2.35, 0.10)
shape = SubResource("BoxShape3D_lp_machon")

# Acceso peatonal de La Panza (X: 13.20 a 15.05): ¡LIBRE DE COLISIONADOR A RAS DE SUELO!
[node name="Col_LP_DintelAcceso" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 14.125, 3.525, 0.10)
shape = SubResource("BoxShape3D_lp_dintel_acceso")

[node name="Col_LP_BahiaDer" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 15.975, 2.35, 0.10)
shape = SubResource("BoxShape3D_lp_der")

[node name="Col_LoncheriaConchita" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 19.05, 2.35, 0.10)
shape = SubResource("BoxShape3D_conchita")

[node name="Col_BienesRaices_Este" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 23.60, 2.35, 0.10)
shape = SubResource("BoxShape3D_bienes_raices_este")

[node name="Col_Libertad_Norte" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 25.85, 2.35, 7.25)
shape = SubResource("BoxShape3D_libertad_norte")

[node name="Col_Muro_Posterior" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 13.00, 2.175, 14.35)
shape = SubResource("BoxShape3D_muro_posterior")

[node name="Col_Medianera_Sur" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.125, 2.35, 7.25)
shape = SubResource("BoxShape3D_medianera_sur")
"""
    with open(tscn_path, "w", encoding="utf-8") as f:
        f.write(tscn_content)
    print(f"--> Escena Godot generada con éxito: {tscn_path}")

# ---------------------------------------------------------------------------
# 6. Orquestación Principal
# ---------------------------------------------------------------------------

def main():
    print("================================================================")
    print(" GENERADOR PROCEDURAL: CONTINUO LA PANZA (2009 GROUND-TRUTH)    ")
    print("================================================================")

    root_col = clean_scene()
    mats = create_materials()

    # 1. Cimentación y Zócalo Basal Enterrado (-1.20 m)
    obj_zocalo = build_zocalo_basal(mats, root_col)

    # 2. Envolvente, Muros y Azotea Hermética
    obj_w, obj_r, obj_c = build_envolvente_y_azotea(mats, root_col)

    # 3. Módulos Comerciales (Sur a Norte)
    build_modulo_1_saldos_telas(mats, root_col)
    build_modulo_2_electronica_hidalgo(mats, root_col)
    build_modulo_3_la_panza(mats, root_col)
    build_modulo_4_loncheria_conchita(mats, root_col)
    build_modulo_5_esquina_bienes_raices(mats, root_col)

    # 4. Iluminación y Batería de Cámaras de Validación
    cams = setup_lighting_and_render(root_col)

    # 5. Guardar Archivo Maestro Blender (.blend)
    blend_path = "blender_assets/buildings/edificio_continuo_la_panza.blend"
    os.makedirs(os.path.dirname(blend_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"--> Archivo maestro Blender guardado: {blend_path}")

    # 6. Exportar Asset Limpio GLB para Godot 4 (Sin banquetas)
    glb_path = "godot_project/assets/buildings/edificio_continuo_la_panza.glb"
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

    # 7. Generar Escena Godot 4 (.tscn)
    tscn_path = "godot_project/assets/buildings/edificio_continuo_la_panza.tscn"
    generate_godot_tscn(tscn_path, "res://assets/buildings/edificio_continuo_la_panza.glb")

    # 8. Batería de Renders Técnicos de Validación Cycles CPU
    scene = bpy.context.scene
    renders = [
        ("cam_general_este", "docs/images/la_panza/render_general_este.png", 1280, 720),
        ("cam_la_panza_closeup", "docs/images/la_panza/render_la_panza_closeup.png", 1280, 720),
        ("cam_puerta_articulos", "docs/images/la_panza/render_puerta_articulos.png", 1280, 720),
        ("cam_vitrina_tarifario", "docs/images/la_panza/render_vitrina_tarifario.png", 1280, 720),
        ("cam_letrero_volante", "docs/images/la_panza/render_letrero_volante.png", 1280, 720),
        ("cam_esquina_bienes_raices", "docs/images/la_panza/render_esquina_bienes_raices.png", 1280, 720),
        ("cam_libertad_norte", "docs/images/la_panza/render_libertad_norte.png", 1280, 720),
        ("cam_sur_electronica_telas", "docs/images/la_panza/render_sur_electronica_telas.png", 1280, 720),
        ("cam_cenital_top", "docs/images/la_panza/render_cenital_top.png", 1024, 1024)
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
    print(" GENERACIÓN PROCEDURAL CONTINUO LA PANZA CONCLUIDA EXITOSAMENTE ")
    print("================================================================")

if __name__ == "__main__":
    main()
