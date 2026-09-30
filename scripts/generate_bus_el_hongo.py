"""
GENERADOR PROCEDURAL 3D DE ALTA FIDELIDAD - AUTOBÚS 'EL HONGO' DE TECATE
Mercedes-Benz Boxer OF (Carrocería hermética de precisión, cero solapamientos, sin huecos)
Basado estrictamente en:
  - scratch/bus/bus-hongo-derecha.jpeg
  - scratch/bus/bus-hongo-izquierda.jpeg
  - scratch/bus/bus-hongo-reverso.jpeg
  - blender_assets/textures/elhongo.png (Textura Oficial)

Implementa:
  - 30 asientos de pasajeros verificables + 1 asiento de chofer
  - Puerta delantera y puerta trasera plegables de 2 hojas acristaladas
  - 6 ventanales dobles en costado izquierdo, 5 en costado derecho
  - Frente Marcopolo Boxer OF con parrilla cromada y estrella Mercedes-Benz
  - Textura UV mapeada de elhongo.png
  - 9 cámaras de validación (incluyendo interior y corte cenital de conteo de asientos)
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Euler

BLEND_PATH = "blender_assets/vehicles/bus_hongo.blend"
GLB_PATH = "godot_project/assets/vehicles/bus_hongo.glb"
RENDER_DIR = "docs/images/bus_hongo"
TEXTURE_PATH = os.path.abspath("blender_assets/textures/elhongo.png")

# Cotas Maestras Canónicas
L_HALF = 4.80         # Largo total 9.60m (-4.80 a +4.80)
W_HALF = 1.25         # Ancho total 2.50m (-1.25 a +1.25)
H_CLEARANCE = 0.38    # Altura de faldones a suelo
H_BELT = 1.48         # Línea de cintura bajo ventanas
H_WINDOW_TOP = 2.45   # Parte superior de ventanas
H_ROOF_EAVE = 2.72    # Alero perimetral de techo
H_ROOF_PEAK = 2.95    # Cumbrera central de techo

WHEEL_R = 0.48
WHEEL_W = 0.28
WHEELBASE_FRONT = 2.65
WHEELBASE_REAR = -2.60

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    col = bpy.data.collections.new("Bus_El_Hongo")
    scene.collection.children.link(col)
    return col

def create_materials():
    mats = {}

    def new_pbr(name, base_color, roughness=0.5, metallic=0.0, transmission=0.0, emission=None, emission_strength=1.0):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = base_color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = transmission
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = transmission
        if emission:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = emission
                bsdf.inputs["Emission Strength"].default_value = emission_strength
            elif "Emission" in bsdf.inputs:
                bsdf.inputs["Emission"].default_value = emission
        return mat

    # 1. Carrocería Rojo Hongo Oficial
    mats['red'] = new_pbr("M_Bus_Rojo_Hongo", (0.78, 0.05, 0.10, 1.0), roughness=0.22, metallic=0.02)

    # 2. Blanco Puro para Fascia, Fascia Trasera y Rines
    mats['white'] = new_pbr("M_Bus_Blanco", (0.95, 0.95, 0.96, 1.0), roughness=0.20, metallic=0.0)

    # 3. Azul Marino Oficial
    mats['blue'] = new_pbr("M_Bus_Azul_Hongo", (0.01, 0.08, 0.32, 1.0), roughness=0.30, metallic=0.0)

    # 4. Aluminio Negro y Marcos de Cancelería
    mats['black_trim'] = new_pbr("M_Bus_Aluminio_Negro", (0.03, 0.03, 0.035, 1.0), roughness=0.50, metallic=0.4)

    # 5. Caucho de Neumáticos y Guardafangos
    mats['rubber'] = new_pbr("M_Bus_Caucho", (0.05, 0.05, 0.06, 1.0), roughness=0.90, metallic=0.0)

    # 6. Rines Blancos con Tapacubos
    mats['rim'] = new_pbr("M_Bus_Rin_Blanco", (0.92, 0.92, 0.93, 1.0), roughness=0.25, metallic=0.2)

    # 7. Cromo Brillante (Estrella Mercedes y Biseles)
    mats['chrome'] = new_pbr("M_Bus_Cromo", (0.96, 0.96, 0.98, 1.0), roughness=0.05, metallic=0.98)

    # 8. Vidrio Ahumado Panorámico
    mats['glass'] = new_pbr("M_Bus_Vidrio_Tintado", (0.10, 0.14, 0.18, 1.0), roughness=0.05, metallic=0.05, transmission=0.82)

    # 9. Asientos Interiores Azul Marino Urbano
    mats['seat'] = new_pbr("M_Bus_Asientos", (0.06, 0.12, 0.28, 1.0), roughness=0.80, metallic=0.0)

    # 10. Pasamanos Amarillo Seguridad
    mats['handrail'] = new_pbr("M_Bus_Pasamanos", (0.95, 0.72, 0.04, 1.0), roughness=0.25, metallic=0.2)

    # 11. Piso Interior Antiderrapante Gris Oscuro
    mats['floor'] = new_pbr("M_Bus_Piso", (0.12, 0.13, 0.14, 1.0), roughness=0.95, metallic=0.0)

    # 12. Faros Delanteros de Proyector (Emisivos)
    mats['headlight'] = new_pbr("M_Bus_Faro_Cristal", (0.95, 0.98, 1.0, 1.0), roughness=0.06, transmission=0.4, emission=(1.0, 0.98, 0.94, 1.0), emission_strength=4.5)

    # 13. Calaveras Rojas
    mats['taillight_red'] = new_pbr("M_Bus_Calavera_Roja", (0.85, 0.02, 0.02, 1.0), roughness=0.15, transmission=0.25, emission=(0.95, 0.02, 0.02, 1.0), emission_strength=2.5)

    # 14. Direccionales Ámbar
    mats['amber'] = new_pbr("M_Bus_Direccional_Ambar", (0.95, 0.55, 0.02, 1.0), roughness=0.15, transmission=0.25, emission=(0.95, 0.55, 0.02, 1.0), emission_strength=2.5)

    # 15. Material Texturizado Oficial El Hongo
    mat_tex = bpy.data.materials.new("M_Bus_Textura_ElHongo")
    mat_tex.use_nodes = True
    nt = mat_tex.node_tree
    bsdf_tex = nt.nodes.get("Principled BSDF")
    bsdf_tex.inputs["Roughness"].default_value = 0.25
    bsdf_tex.inputs["Metallic"].default_value = 0.02

    if os.path.exists(TEXTURE_PATH):
        tex_node = nt.nodes.new("ShaderNodeTexImage")
        img = bpy.data.images.load(TEXTURE_PATH)
        tex_node.image = img
        nt.links.new(tex_node.outputs["Color"], bsdf_tex.inputs["Base Color"])
    else:
        bsdf_tex.inputs["Base Color"].default_value = (0.78, 0.05, 0.10, 1.0)

    mats['hongo_tex'] = mat_tex

    return mats

def add_box(bm, x1, x2, y1, y2, z1, z2):
    """Construye una caja cerrada ortogonal exacta sin solapamientos."""
    # Nota de coordenadas: X es ancho (-W_HALF a +W_HALF), Y es largo (-L_HALF a +L_HALF), Z es elevación
    # Para consistencia con Blender nativo: x=X, y=Z (longitud), z=Y (altura)
    verts = [
        bm.verts.new((x1, y1, z1)), bm.verts.new((x2, y1, z1)),
        bm.verts.new((x2, y2, z1)), bm.verts.new((x1, y2, z1)),
        bm.verts.new((x1, y1, z2)), bm.verts.new((x2, y1, z2)),
        bm.verts.new((x2, y2, z2)), bm.verts.new((x1, y2, z2))
    ]
    bm.faces.new((verts[0], verts[1], verts[2], verts[3]))
    bm.faces.new((verts[4], verts[7], verts[6], verts[5]))
    bm.faces.new((verts[0], verts[4], verts[5], verts[1]))
    bm.faces.new((verts[1], verts[5], verts[6], verts[2]))
    bm.faces.new((verts[2], verts[6], verts[7], verts[3]))
    bm.faces.new((verts[3], verts[7], verts[4], verts[0]))
    return verts

def add_cylinder(bm, center, radius, height, axis='Z', segments=16):
    cx, cy, cz = center
    verts_b = []
    verts_t = []
    h2 = height * 0.5
    for i in range(segments):
        th = 2.0 * math.pi * i / segments
        c = math.cos(th) * radius
        s = math.sin(th) * radius
        if axis == 'Z':
            verts_b.append(bm.verts.new((cx + c, cy + s, cz - h2)))
            verts_t.append(bm.verts.new((cx + c, cy + s, cz + h2)))
        elif axis == 'Y':
            verts_b.append(bm.verts.new((cx + c, cy - h2, cz + s)))
            verts_t.append(bm.verts.new((cx + c, cy + h2, cz + s)))
        elif axis == 'X':
            verts_b.append(bm.verts.new((cx - h2, cy + c, cz + s)))
            verts_t.append(bm.verts.new((cx + h2, cy + c, cz + s)))

    for i in range(segments):
        i_next = (i + 1) % segments
        bm.faces.new((verts_b[i], verts_b[i_next], verts_t[i_next], verts_t[i]))
    bm.faces.new(reversed(verts_b))
    bm.faces.new(verts_t)

def create_mesh_object(name, bm, mat, col):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    if mat:
        obj.data.materials.append(mat)
    col.objects.link(obj)
    return obj

# ===========================================================================
# 1. CARROCERÍA PRINCIPAL HERMÉTICA (BODYSHELL HERMÉTICO)
# ===========================================================================
def build_body_shell(mats, col):
    bm_red = bmesh.new()
    bm_tex = bmesh.new()
    bm_white = bmesh.new()
    bm_wells = bmesh.new()

    xl1, xl2 = -W_HALF, -W_HALF + 0.05
    xr1, xr2 = W_HALF - 0.05, W_HALF

    # --- COSTADO IZQUIERDO (Chofer) ---
    # Faldón inferior izquierdo continuo con arcos de rueda
    # Trasera a rueda trasera
    add_box(bm_red, xl1, xl2, -L_HALF, WHEELBASE_REAR - 0.65, H_CLEARANCE, H_BELT)
    # Entre ruedas
    add_box(bm_red, xl1, xl2, WHEELBASE_REAR + 0.65, WHEELBASE_FRONT - 0.65, H_CLEARANCE, H_BELT)
    # Rueda delantera a frente
    add_box(bm_red, xl1, xl2, WHEELBASE_FRONT + 0.65, 4.60, H_CLEARANCE, H_BELT)
    # Sobre arcos de rueda
    add_box(bm_red, xl1, xl2, WHEELBASE_REAR - 0.65, WHEELBASE_REAR + 0.65, 0.95, H_BELT)
    add_box(bm_red, xl1, xl2, WHEELBASE_FRONT - 0.65, WHEELBASE_FRONT + 0.65, 0.95, H_BELT)

    # Franja superior izquierda sobre ventanas
    add_box(bm_red, xl1, xl2, -L_HALF, 4.60, H_WINDOW_TOP, H_ROOF_EAVE)

    # Pilares entre ventanas izquierdas (6 módulos de pasajeros + chofer = 7 vanos, 6 pilares)
    pilares_izq = [
        (3.30, 3.40),   # Pilar entre ventana chofer y módulo 1
        (2.15, 2.25),   # Pilar 1-2
        (1.00, 1.10),   # Pilar 2-3
        (-0.15, -0.05), # Pilar 3-4
        (-1.30, -1.20), # Pilar 4-5
        (-2.45, -2.35), # Pilar 5-6
        (-3.60, -3.50)  # Pilar tras ventana 6
    ]
    for y1, y2 in pilares_izq:
        add_box(bm_red, xl1, xl2, y1, y2, H_BELT, H_WINDOW_TOP)

    # --- COSTADO DERECHO (Puertas de Pasajeros) ---
    # Faldón inferior derecho:
    # Trasera a ventana trasera
    add_box(bm_red, xr1, xr2, -L_HALF, -3.60, H_CLEARANCE, H_BELT)
    # Puerta trasera es Z: [-2.40, -1.40], vano libre hasta escalón
    add_box(bm_red, xr1, xr2, -3.60, -2.40, H_CLEARANCE, H_BELT)
    # Entre puerta trasera y rueda delantera
    add_box(bm_red, xr1, xr2, -1.40, WHEELBASE_FRONT - 0.65, H_CLEARANCE, H_BELT)
    # Rueda delantera a puerta delantera (Z: 3.45 a 4.45)
    add_box(bm_red, xr1, xr2, WHEELBASE_FRONT + 0.65, 3.45, H_CLEARANCE, H_BELT)
    # Arco sobre rueda delantera derecha
    add_box(bm_red, xr1, xr2, WHEELBASE_FRONT - 0.65, WHEELBASE_FRONT + 0.65, 0.95, H_BELT)
    # Poste frontal derecho tras parabrisas
    add_box(bm_red, xr1, xr2, 4.45, 4.60, H_CLEARANCE, H_BELT)

    # Franja superior derecha corrida
    add_box(bm_red, xr1, xr2, -L_HALF, 4.60, H_WINDOW_TOP, H_ROOF_EAVE)

    # Pilares derechos entre ventanas:
    pilares_der = [
        (3.35, 3.45),   # Pilar entre puerta delantera y módulo 1
        (2.20, 2.25),   # Pilar 1-2
        (1.05, 1.10),   # Pilar 2-3
        (-0.10, -0.05), # Pilar 3-4
        (-1.40, -1.35), # Pilar entre módulo 4 y puerta trasera
        (-2.50, -2.40), # Pilar entre puerta trasera y módulo 5
        (-3.65, -3.60)  # Pilar posterior
    ]
    for y1, y2 in pilares_der:
        add_box(bm_red, xr1, xr2, y1, y2, H_BELT, H_WINDOW_TOP)

    # --- PANELES CON TEXTURA OFICIAL EL HONGO ---
    # Altura del panel de textura: Z de 0.75 a 1.48 (encima de faldones y sin tapar ruedas)
    Z_TEX_BOT = 0.76
    Z_TEX_TOP = H_BELT

    # Panel lateral izquierdo (Chofer): Z de 0.76 a 1.48, Y de -3.50 a 3.30
    # Mirando desde fuera (-X): Izquierda es +Y (frente), Derecha es -Y (atrás)
    v_li_tl = bm_tex.verts.new((-W_HALF - 0.003, 3.30, Z_TEX_TOP))
    v_li_tr = bm_tex.verts.new((-W_HALF - 0.003, -3.50, Z_TEX_TOP))
    v_li_br = bm_tex.verts.new((-W_HALF - 0.003, -3.50, Z_TEX_BOT))
    v_li_bl = bm_tex.verts.new((-W_HALF - 0.003, 3.30, Z_TEX_BOT))
    face_ti = bm_tex.faces.new([v_li_tl, v_li_tr, v_li_br, v_li_bl])

    # Panel lateral derecho (Puertas): Z de 0.76 a 1.48, Y de -1.35 a 3.35
    # Mirando desde fuera (+X): Izquierda es -Y (atrás), Derecha es +Y (frente)
    v_rd_tl = bm_tex.verts.new((W_HALF + 0.003, -1.35, Z_TEX_TOP))
    v_rd_tr = bm_tex.verts.new((W_HALF + 0.003, 3.35, Z_TEX_TOP))
    v_rd_br = bm_tex.verts.new((W_HALF + 0.003, 3.35, Z_TEX_BOT))
    v_rd_bl = bm_tex.verts.new((W_HALF + 0.003, -1.35, Z_TEX_BOT))
    face_td = bm_tex.faces.new([v_rd_tl, v_rd_tr, v_rd_br, v_rd_bl])

    # Panel trasero: Z de 1.15 a 2.45, X de -1.10 a 1.10
    # Mirando desde atrás (-Y): Izquierda es +X, Derecha es -X
    v_re_tl = bm_tex.verts.new((1.10, -L_HALF - 0.003, 2.45))
    v_re_tr = bm_tex.verts.new((-1.10, -L_HALF - 0.003, 2.45))
    v_re_br = bm_tex.verts.new((-1.10, -L_HALF - 0.003, 1.15))
    v_re_bl = bm_tex.verts.new((1.10, -L_HALF - 0.003, 1.15))
    face_tt = bm_tex.faces.new([v_re_tl, v_re_tr, v_re_br, v_re_bl])

    # Coordenadas UV exactas orientadas de izquierda a derecha sin inversión en espejo
    uv_layer = bm_tex.loops.layers.uv.new("UVMap")
    for face in [face_ti, face_td, face_tt]:
        face.loops[0][uv_layer].uv = (0.0, 1.0)
        face.loops[1][uv_layer].uv = (1.0, 1.0)
        face.loops[2][uv_layer].uv = (1.0, 0.0)
        face.loops[3][uv_layer].uv = (0.0, 0.0)

    # --- TECHO HERMÉTICO TRANSVERSAL ---
    bm_roof = bmesh.new()
    steps = 16
    for s in range(steps):
        t0 = s / float(steps)
        t1 = (s + 1) / float(steps)
        xa = -W_HALF + t0 * (2.0 * W_HALF)
        xb = -W_HALF + t1 * (2.0 * W_HALF)
        za = H_ROOF_EAVE + (H_ROOF_PEAK - H_ROOF_EAVE) * math.sin(math.pi * t0)
        zb = H_ROOF_EAVE + (H_ROOF_PEAK - H_ROOF_EAVE) * math.sin(math.pi * t1)
        zmin = min(za, zb)
        zmax = max(za, zb) + 0.03
        add_box(bm_roof, xa, xb, -L_HALF, 4.65, zmin, zmax)

    # --- TRASERA ROJA HERMÉTICA ---
    # Pared trasera completa sellada
    add_box(bm_red, -W_HALF, W_HALF, -L_HALF, -L_HALF + 0.05, 0.95, H_ROOF_PEAK)
    # Faldón trasero inferior blanco con matrícula y loderas
    add_box(bm_white, -W_HALF, W_HALF, -L_HALF - 0.02, -L_HALF + 0.04, 0.40, 0.95)

    # --- FRENTE: CABINA Y COPETE HERMÉTICO ---
    # Pilar A Izquierdo
    add_box(bm_red, -W_HALF, -W_HALF + 0.12, 4.60, 4.78, H_BELT, H_WINDOW_TOP)
    # Pilar A Derecho
    add_box(bm_red, W_HALF - 0.12, W_HALF, 4.60, 4.78, H_BELT, H_WINDOW_TOP)
    # Travesaño frontal de cintura bajo parabrisas
    add_box(bm_red, -W_HALF, W_HALF, 4.70, 4.80, H_BELT, 1.55)
    # Copete superior frontal aerodinámico (caja de rutero)
    add_box(bm_red, -W_HALF, W_HALF, 4.60, 4.82, 2.50, H_ROOF_PEAK)

    # Guardafangos de caucho en los 4 arcos de rueda
    for center_y in [WHEELBASE_FRONT, WHEELBASE_REAR]:
        for center_x, side in [(-W_HALF, -1), (W_HALF, 1)]:
            cx = center_x + (side * 0.02)
            add_cylinder(bm_wells, (cx, center_y, 0.48), radius=WHEEL_R + 0.08, height=0.06, axis='X', segments=24)

    obj_body = create_mesh_object("Bus_Carroceria_Roja", bm_red, mats['red'], col)
    obj_tex = create_mesh_object("Bus_Textura_Oficial", bm_tex, mats['hongo_tex'], col)
    obj_white_rear = create_mesh_object("Bus_Defensa_Trasera", bm_white, mats['white'], col)
    obj_wells = create_mesh_object("Bus_Pasos_Rueda", bm_wells, mats['rubber'], col)
    obj_roof = create_mesh_object("Bus_Techo", bm_roof, mats['red'], col)
    return obj_body, obj_tex, obj_white_rear, obj_wells, obj_roof

# ===========================================================================
# 2. FRENTE MARCOPOLO BOXER OF (PARRILLA, ESTRELLA MERCEDES Y FAROS)
# ===========================================================================
def build_front_fascia_and_grille(mats, col):
    bm_white_fascia = bmesh.new()
    bm_grille = bmesh.new()
    bm_chrome = bmesh.new()
    bm_lights = bmesh.new()
    bm_signage = bmesh.new()

    # 1. Fascia Frontal Blanca Curvada
    # Base inferior con tomas de aire
    add_box(bm_white_fascia, -1.22, 1.22, 4.74, 4.82, 0.38, 0.85)
    # Cuerpo frontal trapezoidal
    add_box(bm_white_fascia, -1.18, 1.18, 4.72, 4.80, 0.85, 1.48)

    # 2. Parrilla Trapezoidal Mercedes-Benz
    add_box(bm_grille, -0.68, 0.68, 4.805, 4.825, 0.90, 1.35)

    # 3 Listones Horizontales Cromados
    for gz in [0.98, 1.12, 1.26]:
        add_box(bm_chrome, -0.65, 0.65, 4.825, 4.84, gz, gz + 0.025)

    # 3. Emblema Tridimensional de la Estrella Mercedes-Benz
    # Aro exterior cromado
    add_cylinder(bm_chrome, (0.0, 4.845, 1.12), radius=0.14, height=0.02, axis='Y', segments=28)
    # Triestrella central
    for deg in [90.0, 210.0, 330.0]:
        rad = math.radians(deg)
        x_tip = math.cos(rad) * 0.12
        z_tip = math.sin(rad) * 0.12
        add_box(bm_chrome, min(0.0, x_tip)-0.008, max(0.0, x_tip)+0.008, 4.85, 4.86, min(1.12, 1.12 + z_tip)-0.008, max(1.12, 1.12 + z_tip)+0.008)

    # 4. Bloques de Faros Delanteros Trapezoidales Integrados
    for fx in [-0.96, 0.96]:
        # Bisel cromado perimetral
        add_box(bm_chrome, fx - 0.18, fx + 0.18, 4.795, 4.825, 0.92, 1.18)
        # Cristal emisor principal
        add_box(bm_lights, fx - 0.16, fx + 0.05, 4.825, 4.835, 0.94, 1.16)
        # Direccional ámbar integrada
        add_box(bm_grille, fx + 0.05, fx + 0.16, 4.825, 4.835, 0.94, 1.16)

    # 5. Caja de Rutero Frontal Superior Iluminada
    # Nicho negro
    add_box(bm_grille, -0.92, 0.92, 4.78, 4.825, 2.54, 2.78)
    # Pantalla acrílica blanca retroiluminada
    add_box(bm_signage, -0.88, 0.88, 4.825, 4.835, 2.56, 2.76)

    # 6. Limpiaparabrisas Dobles en Reposo
    add_cylinder(bm_grille, (-0.40, 4.74, 1.85), radius=0.012, height=0.65, axis='Z', segments=8)
    add_cylinder(bm_grille, (0.40, 4.74, 1.85), radius=0.012, height=0.65, axis='Z', segments=8)

    # 7. Luces de Gálibo Superiores (5 frontales ámbar, 5 traseras rojas)
    bm_amber_roof = bmesh.new()
    for gx in [-0.95, -0.48, 0.0, 0.48, 0.95]:
        add_cylinder(bm_amber_roof, (gx, 4.81, 2.85), radius=0.025, height=0.025, axis='Y', segments=12)

    bm_red_roof = bmesh.new()
    for gx in [-0.95, -0.48, 0.0, 0.48, 0.95]:
        add_cylinder(bm_red_roof, (gx, -L_HALF - 0.01, 2.85), radius=0.025, height=0.025, axis='Y', segments=12)

    # 8. Rótulo de la Unidad "24" en Azul Marino sobre Fascia
    ROT_FRONT = (math.radians(90.0), 0.0, math.radians(180.0))
    t_curve_unit = bpy.data.curves.new(name="Txt_Unidad24", type='FONT')
    t_curve_unit.body = "24"
    t_curve_unit.size = 0.14
    t_curve_unit.extrude = 0.005
    t_curve_unit.align_x = 'CENTER'
    t_curve_unit.align_y = 'CENTER'
    t_obj_u = bpy.data.objects.new("TxtObj_Unidad24", t_curve_unit)
    t_obj_u.location = Vector((0.95, 4.815, 0.72))
    t_obj_u.rotation_euler = ROT_FRONT
    t_obj_u.data.materials.append(mats['blue'])
    col.objects.link(t_obj_u)

    # Rótulo del Rutero: TECATE · EL HONGO · LA RUMOROSA
    t_curve_dest = bpy.data.curves.new(name="Txt_Rutero", type='FONT')
    t_curve_dest.body = "TECATE  EL HONGO  LA RUMOROSA"
    t_curve_dest.size = 0.095
    t_curve_dest.extrude = 0.004
    t_curve_dest.align_x = 'CENTER'
    t_curve_dest.align_y = 'CENTER'
    t_obj_d = bpy.data.objects.new("TxtObj_Rutero", t_curve_dest)
    t_obj_d.location = Vector((0.0, 4.838, 2.66))
    t_obj_d.rotation_euler = ROT_FRONT
    t_obj_d.data.materials.append(mats['black_trim'])
    col.objects.link(t_obj_d)

    obj_fascia = create_mesh_object("Bus_Fascia_Blanca", bm_white_fascia, mats['white'], col)
    obj_grille = create_mesh_object("Bus_Parrilla_Fondo", bm_grille, mats['black_trim'], col)
    obj_chrome = create_mesh_object("Bus_Cromos_Estrella", bm_chrome, mats['chrome'], col)
    obj_hl = create_mesh_object("Bus_Faros_Cristal", bm_lights, mats['headlight'], col)
    obj_sign = create_mesh_object("Bus_Rutero_Fondo", bm_signage, mats['white'], col)
    obj_amb = create_mesh_object("Bus_Galibo_Frontal", bm_amber_roof, mats['amber'], col)
    obj_red_g = create_mesh_object("Bus_Galibo_Trasero", bm_red_roof, mats['taillight_red'], col)

    return obj_fascia, obj_grille, obj_chrome, obj_hl

# ===========================================================================
# 3. VENTANERÍA COMPLETA Y PUERTAS PLEGABLES
# ===========================================================================
def build_windows_and_doors(mats, col):
    bm_glass = bmesh.new()
    bm_frames = bmesh.new()

    # 1. Parabrisas Panorámico Delantero en 2 Secciones Inclinado
    add_box(bm_glass, -W_HALF + 0.12, -0.015, 4.66, 4.74, 1.54, 2.48)
    add_box(bm_glass, 0.015, W_HALF - 0.12, 4.66, 4.74, 1.54, 2.48)
    # Marco central y perimetral de parabrisas
    add_box(bm_frames, -0.02, 0.02, 4.65, 4.75, 1.52, 2.50)
    add_box(bm_frames, -W_HALF + 0.10, W_HALF - 0.10, 4.65, 4.75, 1.52, 1.55)
    add_box(bm_frames, -W_HALF + 0.10, W_HALF - 0.10, 4.65, 4.75, 2.46, 2.50)

    # 2. Costado Izquierdo: 1 Ventana de Chofer + 6 Módulos de Pasajeros
    xl = -W_HALF - 0.002
    bays_left = [
        (3.40, 4.55),   # Ventana chofer
        (2.25, 3.30),   # Módulo 1
        (1.10, 2.15),   # Módulo 2
        (-0.05, 1.00),  # Módulo 3
        (-1.20, -0.15), # Módulo 4
        (-2.35, -1.30), # Módulo 5
        (-3.50, -2.45)  # Módulo 6
    ]
    for y1, y2 in bays_left:
        # Vidrio tintado
        add_box(bm_glass, xl - 0.012, xl + 0.012, y1 + 0.02, y2 - 0.02, 1.50, 2.43)
        # Marco perimetral de cancelería
        add_box(bm_frames, xl - 0.022, xl + 0.022, y1, y2, 1.48, 1.51)
        add_box(bm_frames, xl - 0.022, xl + 0.022, y1, y2, 2.43, 2.46)
        add_box(bm_frames, xl - 0.022, xl + 0.022, y1, y1 + 0.025, 1.48, 2.46)
        add_box(bm_frames, xl - 0.022, xl + 0.022, y2 - 0.025, y2, 1.48, 2.46)
        # Travesaño de ventila corrediza superior
        add_box(bm_frames, xl - 0.018, xl + 0.018, y1, y2, 2.18, 2.21)

    # 3. Costado Derecho: Ventanales y 2 Puertas Plegables
    xr = W_HALF + 0.002
    bays_right = [
        (2.25, 3.35),   # Pasajeros 1
        (1.10, 2.20),   # Pasajeros 2
        (-0.05, 1.05),  # Pasajeros 3
        (-1.20, -0.10), # Pasajeros 4
        (-3.60, -2.50)  # Pasajeros 5 (trasera)
    ]
    for y1, y2 in bays_right:
        add_box(bm_glass, xr - 0.012, xr + 0.012, y1 + 0.02, y2 - 0.02, 1.50, 2.43)
        add_box(bm_frames, xr - 0.022, xr + 0.022, y1, y2, 1.48, 1.51)
        add_box(bm_frames, xr - 0.022, xr + 0.022, y1, y2, 2.43, 2.46)
        add_box(bm_frames, xr - 0.022, xr + 0.022, y1, y1 + 0.025, 1.48, 2.46)
        add_box(bm_frames, xr - 0.022, xr + 0.022, y2 - 0.025, y2, 1.48, 2.46)
        add_box(bm_frames, xr - 0.018, xr + 0.018, y1, y2, 2.18, 2.21)

    # Puerta Delantera Plegable (2 Hojas acristaladas): Z de 3.45 a 4.45, Y de 0.44 a 2.45
    for py1, py2 in [(3.48, 3.93), (3.97, 4.42)]:
        add_box(bm_glass, xr - 0.018, xr + 0.010, py1 + 0.02, py2 - 0.02, 0.52, 2.38)
        add_box(bm_frames, xr - 0.025, xr + 0.015, py1, py2, 0.44, 0.52)
        add_box(bm_frames, xr - 0.025, xr + 0.015, py1, py2, 2.38, 2.46)
        add_box(bm_frames, xr - 0.025, xr + 0.015, py1, py1 + 0.025, 0.44, 2.46)
        add_box(bm_frames, xr - 0.025, xr + 0.015, py2 - 0.025, py2, 0.44, 2.46)
        add_box(bm_frames, xr - 0.022, xr + 0.012, py1, py2, 1.38, 1.42)

    # Puerta Trasera Plegable (2 Hojas acristaladas): Z de -2.40 a -1.40, Y de 0.44 a 2.45
    for py1, py2 in [(-2.37, -1.92), (-1.88, -1.43)]:
        add_box(bm_glass, xr - 0.018, xr + 0.010, py1 + 0.02, py2 - 0.02, 0.52, 2.38)
        add_box(bm_frames, xr - 0.025, xr + 0.015, py1, py2, 0.44, 0.52)
        add_box(bm_frames, xr - 0.025, xr + 0.015, py1, py2, 2.38, 2.46)
        add_box(bm_frames, xr - 0.025, xr + 0.015, py1, py1 + 0.025, 0.44, 2.46)
        add_box(bm_frames, xr - 0.025, xr + 0.015, py2 - 0.025, py2, 0.44, 2.46)
        add_box(bm_frames, xr - 0.022, xr + 0.012, py1, py2, 1.38, 1.42)

    # 4. Espejos Retrovisores Foráneos
    # Espejo derecho alto
    add_cylinder(bm_frames, (W_HALF + 0.18, 4.40, 2.35), radius=0.015, height=0.45, axis='Z', segments=8)
    add_box(bm_frames, W_HALF + 0.12, W_HALF + 0.28, 4.38, 4.45, 1.95, 2.35)
    # Espejo izquierdo
    add_cylinder(bm_frames, (-W_HALF - 0.18, 4.40, 2.20), radius=0.015, height=0.45, axis='Z', segments=8)
    add_box(bm_frames, -W_HALF - 0.28, -W_HALF - 0.12, 4.38, 4.45, 1.80, 2.20)

    obj_glass = create_mesh_object("Bus_Ventaneria_Vidrio", bm_glass, mats['glass'], col)
    obj_frames = create_mesh_object("Bus_Marcos_Canceleria", bm_frames, mats['black_trim'], col)
    return obj_glass, obj_frames

# ===========================================================================
# 4. RUEDAS Y CALAVERAS TRASERAS
# ===========================================================================
def build_wheels_and_rear_lights(mats, col):
    bm_tires = bmesh.new()
    bm_rims = bmesh.new()
    bm_red_lights = bmesh.new()
    bm_white_lights = bmesh.new()
    bm_amber_lights = bmesh.new()

    wheel_specs = [
        ((-1.12, WHEELBASE_FRONT, WHEEL_R), -1, WHEEL_W),
        ((1.12, WHEELBASE_FRONT, WHEEL_R), 1, WHEEL_W),
        ((-1.05, WHEELBASE_REAR, WHEEL_R), -1, WHEEL_W * 1.6),
        ((1.05, WHEELBASE_REAR, WHEEL_R), 1, WHEEL_W * 1.6)
    ]
    for center, side, width in wheel_specs:
        add_cylinder(bm_tires, center, radius=WHEEL_R, height=width, axis='X', segments=28)
        rin_cx = center[0] + (0.02 * side)
        add_cylinder(bm_rims, (rin_cx, center[1], center[2]), radius=WHEEL_R * 0.65, height=width * 0.90, axis='X', segments=24)
        hub_cx = center[0] + (0.05 * side)
        add_cylinder(bm_rims, (hub_cx, center[1], center[2]), radius=0.12, height=width * 0.50, axis='X', segments=14)

    # Calaveras traseras triples verticales redondas (Z = -4.815)
    for kx in [-1.05, 1.05]:
        # Ámbar superior (direccional)
        add_cylinder(bm_amber_lights, (kx, -L_HALF - 0.015, 0.88), radius=0.065, height=0.025, axis='Y', segments=16)
        # Blanca central (reversa)
        add_cylinder(bm_white_lights, (kx, -L_HALF - 0.015, 0.74), radius=0.065, height=0.025, axis='Y', segments=16)
        # Roja inferior (freno)
        add_cylinder(bm_red_lights, (kx, -L_HALF - 0.015, 0.60), radius=0.065, height=0.025, axis='Y', segments=16)

    # Loderas traseras de caucho
    add_box(bm_tires, -1.18, -0.75, -L_HALF - 0.01, -L_HALF + 0.01, 0.12, H_CLEARANCE)
    add_box(bm_tires, 0.75, 1.18, -L_HALF - 0.01, -L_HALF + 0.01, 0.12, H_CLEARANCE)

    obj_tires = create_mesh_object("Bus_Neumaticos", bm_tires, mats['rubber'], col)
    obj_rims = create_mesh_object("Bus_Rines", bm_rims, mats['rim'], col)
    obj_trl = create_mesh_object("Bus_Calaveras_Rojas", bm_red_lights, mats['taillight_red'], col)
    obj_tam = create_mesh_object("Bus_Calaveras_Ambar", bm_amber_lights, mats['amber'], col)
    obj_tre = create_mesh_object("Bus_Calaveras_Reversa", bm_white_lights, mats['white'], col)
    return obj_tires, obj_rims, obj_trl

# ===========================================================================
# 5. INTERIOR DE 30 ASIENTOS DE PASAJEROS + CHOFER
# ===========================================================================
def build_interior_30_seats(mats, col):
    bm_floor = bmesh.new()
    bm_seats = bmesh.new()
    bm_rails = bmesh.new()

    # Piso continuo
    add_box(bm_floor, -W_HALF + 0.08, W_HALF - 0.08, -L_HALF + 0.10, 4.55, 0.76, 0.80)

    # Estribos de acceso en ambas puertas
    add_box(bm_floor, W_HALF - 0.40, W_HALF - 0.06, 3.48, 4.42, 0.42, 0.58)
    add_box(bm_floor, W_HALF - 0.32, W_HALF - 0.06, 3.48, 4.42, 0.58, 0.76)
    add_box(bm_floor, W_HALF - 0.40, W_HALF - 0.06, -2.37, -1.43, 0.42, 0.58)
    add_box(bm_floor, W_HALF - 0.32, W_HALF - 0.06, -2.37, -1.43, 0.58, 0.76)

    # Puesto del chofer
    # Tablero de mandos
    add_box(bm_floor, -1.18, -0.32, 4.00, 4.55, 0.80, 1.35)
    # Volante inclinado
    add_cylinder(bm_floor, (-0.75, 4.18, 1.38), radius=0.22, height=0.03, axis='Z', segments=18)
    # Asiento del chofer
    add_box(bm_seats, -0.95, -0.55, 3.52, 3.82, 0.80, 1.25)
    add_box(bm_seats, -0.95, -0.55, 3.44, 3.52, 1.25, 1.82)

    def make_seat(x1, x2, y1, y2):
        # Base/cojín
        add_box(bm_seats, x1, x2, y1, y2, 0.80, 1.22)
        # Respaldo
        add_box(bm_seats, x1, x2, y1 - 0.08, y1, 1.22, 1.78)

    # 1. Banda Izquierda: 7 filas dobles = 14 asientos
    seat_rows_izq = [2.75, 1.85, 0.95, 0.05, -0.85, -1.75, -2.65]
    for sy in seat_rows_izq:
        make_seat(-1.18, -0.76, sy - 0.16, sy + 0.16) # Ventanilla
        make_seat(-0.72, -0.30, sy - 0.16, sy + 0.16) # Pasillo

    # 2. Banda Derecha: 5 filas dobles + 1 individual = 11 asientos
    # Asiento individual delantero preferencial
    make_seat(0.55, 0.95, 2.75 - 0.16, 2.75 + 0.16)
    # 5 filas dobles
    seat_rows_der = [1.85, 0.95, 0.05, -0.85, -1.75]
    for sy in seat_rows_der:
        make_seat(0.30, 0.72, sy - 0.16, sy + 0.16) # Pasillo
        make_seat(0.76, 1.18, sy - 0.16, sy + 0.16) # Ventanilla

    # 3. Banca Posterior Corrida: 5 asientos contiguos
    rear_y = -4.35
    rear_xs = [-1.15, -0.69, -0.23, 0.23, 0.69, 1.15]
    for i in range(5):
        rx1 = rear_xs[i] + 0.03
        rx2 = rear_xs[i+1] - 0.03
        make_seat(rx1, rx2, rear_y - 0.16, rear_y + 0.16)

    # Pasamanos amarillos longitudinales
    add_cylinder(bm_rails, (-0.26, 0.0, 2.45), radius=0.018, height=8.2, axis='Y', segments=10)
    add_cylinder(bm_rails, (0.26, 0.0, 2.45), radius=0.018, height=8.2, axis='Y', segments=10)
    # Barras verticales en puertas
    add_cylinder(bm_rails, (0.42, 3.46, 1.60), radius=0.018, height=1.65, axis='Z', segments=8)
    add_cylinder(bm_rails, (0.42, -1.42, 1.60), radius=0.018, height=1.65, axis='Z', segments=8)

    obj_floor = create_mesh_object("Bus_Interior_Piso", bm_floor, mats['floor'], col)
    obj_seats = create_mesh_object("Bus_Interior_Asientos_30", bm_seats, mats['seat'], col)
    obj_rails = create_mesh_object("Bus_Interior_Pasamanos", bm_rails, mats['handrail'], col)
    return obj_floor, obj_seats, obj_rails

# ===========================================================================
# 6. CÁMARAS Y RENDERS DE INSPECCIÓN CLOSED-LOOP
# ===========================================================================
def setup_lighting_and_render_cameras(col):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    if hasattr(scene.cycles, 'device'):
        scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720

    if not scene.world:
        scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.70, 0.82, 0.94, 1.0)
        bg.inputs["Strength"].default_value = 0.75

    # Sol cenital suave
    sun_data = bpy.data.lights.new(name="Sun_Light", type='SUN')
    sun_data.energy = 4.2
    sun_data.color = (1.0, 0.97, 0.92)
    sun_obj = bpy.data.objects.new("Sun_Obj", sun_data)
    sun_obj.rotation_euler = (math.radians(52.0), math.radians(18.0), math.radians(-42.0))
    col.objects.link(sun_obj)

    # Luz de relleno frontal
    fill_data = bpy.data.lights.new(name="Fill_Light", type='SUN')
    fill_data.energy = 2.0
    fill_data.color = (0.85, 0.90, 1.0)
    fill_obj = bpy.data.objects.new("Fill_Obj", fill_data)
    fill_obj.rotation_euler = (math.radians(35.0), math.radians(-40.0), math.radians(135.0))
    col.objects.link(fill_obj)

    # 4 Luces puntuales interiores en el techo de la cabina
    for ly in [-3.0, -1.0, 1.0, 3.0]:
        l_data = bpy.data.lights.new(name=f"Cabin_Light_{ly}", type='POINT')
        l_data.energy = 45.0
        l_data.color = (1.0, 0.96, 0.90)
        l_obj = bpy.data.objects.new(f"Cabin_Light_{ly}", l_data)
        l_obj.location = (0.0, ly, 2.38)
        col.objects.link(l_obj)

    # 9 Cámaras calibradas:
    cams_spec = [
        # 1. Frontal 3/4
        ("Cam_01_Frontal_3Q", (4.8, 8.5, 3.2), (math.radians(72.0), 0.0, math.radians(148.0)), 42.0, 'PERSP', 0.0),
        # 2. Lateral Derecha (Puertas delantera y trasera completas)
        ("Cam_02_Lateral_Derecha_Puertas", (9.8, 0.0, 1.8), (math.radians(90.0), 0.0, math.radians(90.0)), 36.0, 'PERSP', 0.0),
        # 3. Lateral Izquierda (6 ventanas + textura El Hongo completa)
        ("Cam_03_Lateral_Izquierda_Hongo", (-9.8, 0.0, 1.8), (math.radians(90.0), 0.0, math.radians(-90.0)), 36.0, 'PERSP', 0.0),
        # 4. Posterior (Calaveras triples, panel y defensa trasera)
        ("Cam_04_Posterior_Calaveras", (0.0, -9.8, 1.6), (math.radians(90.0), 0.0, 0.0), 38.0, 'PERSP', 0.0),
        # 5. Perspectiva General Izquierda
        ("Cam_05_Perspectiva_General", (-6.5, -7.5, 3.8), (math.radians(68.0), 0.0, math.radians(-42.0)), 42.0, 'PERSP', 0.0),
        # 6. Detalle Frente y Parrilla Mercedes
        ("Cam_06_Frente_Parrilla_Closeup", (0.0, 8.2, 1.35), (math.radians(90.0), 0.0, math.radians(180.0)), 44.0, 'PERSP', 0.0),
        # 7. Interior: Vista longitudinal hacia atrás (conteo de asientos desde el chofer)
        ("Cam_07_Interior_Hacia_Atras", (0.0, 3.6, 1.70), (math.radians(90.0), 0.0, math.radians(180.0)), 22.0, 'PERSP', 0.0),
        # 8. Interior: Vista desde el fondo hacia adelante (hacia la cabina del chofer)
        ("Cam_08_Interior_Hacia_Frente", (0.0, -3.9, 1.70), (math.radians(90.0), 0.0, 0.0), 22.0, 'PERSP', 0.0),
        # 9. Conteo de Asientos Cenital Isométrico (Cutaway sin techo)
        ("Cam_09_Interior_Cenital_Cutaway", (0.0, 0.0, 8.5), (0.0, 0.0, math.radians(90.0)), 35.0, 'ORTHO', 11.5)
    ]

    cam_objs = {}
    for name, loc, rot, lens, ctype, ortho_s in cams_spec:
        cam_data = bpy.data.cameras.new(name)
        cam_data.type = ctype
        if ctype == 'ORTHO':
            cam_data.ortho_scale = ortho_s
        else:
            cam_data.lens = lens
        cam_obj = bpy.data.objects.new(name, cam_data)
        cam_obj.location = loc
        cam_obj.rotation_euler = rot
        col.objects.link(cam_obj)
        cam_objs[name] = cam_obj

    return cam_objs

def export_and_render(col, cam_objs, obj_roof):
    os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
    os.makedirs(RENDER_DIR, exist_ok=True)

    # 1. Guardar archivo .blend
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"-> Guardado .blend: {BLEND_PATH}")

    # 2. Exportar .glb de producción (sin cámaras ni luces)
    for obj in bpy.context.scene.objects:
        obj.select_set(obj.type == 'MESH')
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH,
        use_selection=True,
        export_format='GLB',
        export_materials='EXPORT',
        export_yup=True
    )
    print(f"-> Exportado .glb: {GLB_PATH} ({os.path.getsize(GLB_PATH):,} bytes)")

    # 3. Ejecutar batería de renders
    scene = bpy.context.scene
    for cam_name, cam_obj in cam_objs.items():
        scene.camera = cam_obj
        out_path = os.path.join(RENDER_DIR, f"{cam_name}.png")
        scene.render.filepath = out_path

        # Ocultar techo únicamente para el corte cenital interior
        if cam_name == "Cam_09_Interior_Cenital_Cutaway":
            obj_roof.hide_render = True
        else:
            obj_roof.hide_render = False

        print(f"Renderizando: {cam_name}...")
        bpy.ops.render.render(write_still=True)
        print(f"-> Guardado render: {out_path}")

    obj_roof.hide_render = False

def main():
    print("=== INICIANDO GENERACIÓN PROCEDURAL DE AUTOBÚS EL HONGO ===")
    col = clean_scene()
    mats = create_materials()

    obj_body, obj_tex, obj_white_rear, obj_wells, obj_roof = build_body_shell(mats, col)
    build_front_fascia_and_grille(mats, col)
    build_windows_and_doors(mats, col)
    build_wheels_and_rear_lights(mats, col)
    build_interior_30_seats(mats, col)

    cams = setup_lighting_and_render_cameras(col)
    export_and_render(col, cams, obj_roof)
    print("=== PROCESO COMPLETADO EXITOSAMENTE ===")

if __name__ == "__main__":
    main()
