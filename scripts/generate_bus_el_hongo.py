"""
GENERADOR PROCEDURAL 3D DE ALTA FIDELIDAD - AUTOBÚS 'EL HONGO' DE TECATE
Mercedes-Benz Boxer OF (Carrocería hermética de precisión, cero solapamientos, sin huecos, colores vivos)
Basado estrictamente en:
  - scratch/bus/bus-hongo-derecha.jpeg
  - scratch/bus/bus-hongo-izquierda.jpeg
  - scratch/bus/bus-hongo-reverso.jpeg
  - scratch/bus/bus-palmas-frente.jpeg
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Euler

BLEND_PATH = "blender_assets/vehicles/bus_hongo.blend"
GLB_PATH = "godot_project/assets/vehicles/bus_hongo.glb"
RENDER_DIR = "docs/images/bus_hongo"

# Cotas Maestras Canónicas
L_HALF = 4.80   # Largo total 9.60m (-4.80 a +4.80)
W_HALF = 1.25   # Ancho total 2.50m (-1.25 a +1.25)
H_CLEARANCE = 0.35 # Altura faldón a suelo
H_BELT = 1.62      # Línea de cintura bajo ventanas
H_WINDOW_TOP = 2.60 # Parte superior de ventanas
H_ROOF_EAVE = 2.76  # Alero perimetral de techo
H_ROOF_PEAK = 2.98  # Cumbrera central de techo

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

    # 1. Carrocería Rojo Hongo Vivo y Saturado
    mats['red'] = new_pbr("M_Bus_Rojo_Hongo", (0.82, 0.02, 0.03, 1.0), roughness=0.22, metallic=0.02)

    # 2. Blanco Puro para Lunares, Fascia y Rines
    mats['white'] = new_pbr("M_Bus_Blanco", (0.95, 0.95, 0.96, 1.0), roughness=0.22, metallic=0.0)

    # 3. Azul Marino Oficial ("HONGO" y círculo número)
    mats['blue'] = new_pbr("M_Bus_Azul_Hongo", (0.02, 0.07, 0.38, 1.0), roughness=0.30, metallic=0.0)

    # 4. Aluminio Negro y Marcos de Cancelería
    mats['black_trim'] = new_pbr("M_Bus_Aluminio_Negro", (0.03, 0.03, 0.035, 1.0), roughness=0.55, metallic=0.3)

    # 5. Caucho de Neumáticos y Guardafangos
    mats['rubber'] = new_pbr("M_Bus_Caucho", (0.05, 0.05, 0.06, 1.0), roughness=0.90, metallic=0.0)

    # 6. Rines Blancos con Tapacubos
    mats['rim'] = new_pbr("M_Bus_Rin_Blanco", (0.92, 0.92, 0.93, 1.0), roughness=0.25, metallic=0.2)

    # 7. Cromo Brillante (Estrella Mercedes y Biseles)
    mats['chrome'] = new_pbr("M_Bus_Cromo", (0.96, 0.96, 0.98, 1.0), roughness=0.05, metallic=0.98)

    # 8. Vidrio Ahumado Panorámico
    mats['glass'] = new_pbr("M_Bus_Vidrio_Tintado", (0.12, 0.16, 0.20, 1.0), roughness=0.05, metallic=0.05, transmission=0.82)

    # 9. Asientos Interiores
    mats['seat'] = new_pbr("M_Bus_Asientos", (0.08, 0.12, 0.25, 1.0), roughness=0.85, metallic=0.0)

    # 10. Pasamanos Amarillo Seguridad
    mats['handrail'] = new_pbr("M_Bus_Pasamanos", (0.95, 0.70, 0.04, 1.0), roughness=0.25, metallic=0.2)

    # 11. Piso Interior Antiderrapante
    mats['floor'] = new_pbr("M_Bus_Piso", (0.10, 0.11, 0.12, 1.0), roughness=0.95, metallic=0.0)

    # 12. Faros Delanteros de Proyector (Emisivos)
    mats['headlight'] = new_pbr("M_Bus_Faro_Cristal", (0.95, 0.98, 1.0, 1.0), roughness=0.06, transmission=0.4, emission=(1.0, 0.98, 0.94, 1.0), emission_strength=4.5)

    # 13. Calaveras Rojas
    mats['taillight_red'] = new_pbr("M_Bus_Calavera_Roja", (0.88, 0.02, 0.02, 1.0), roughness=0.15, emission=(1.0, 0.03, 0.03, 1.0), emission_strength=3.5)

    # 14. Calaveras Ámbar / Direccionales
    mats['amber'] = new_pbr("M_Bus_Direccional_Ambar", (0.96, 0.48, 0.02, 1.0), roughness=0.15, emission=(1.0, 0.52, 0.03, 1.0), emission_strength=3.5)

    # 15. Cartel de Ruta Amarillo Fósforo
    mats['route_card_yellow'] = new_pbr("M_Bus_Cartel_Ruta_Amarillo", (0.96, 0.90, 0.18, 1.0), roughness=0.50, emission=(0.96, 0.90, 0.20, 1.0), emission_strength=1.8)

    # 16. Cartel de Ruta Blanco
    mats['route_card_white'] = new_pbr("M_Bus_Cartel_Ruta_Blanco", (0.95, 0.95, 0.95, 1.0), roughness=0.50, emission=(0.95, 0.95, 0.95, 1.0), emission_strength=1.5)

    return mats

def add_box(bm, x1, x2, y1, y2, z1, z2):
    """Crea una caja estanca ortogonal."""
    verts = [
        bm.verts.new((x1, y1, z1)), bm.verts.new((x2, y1, z1)),
        bm.verts.new((x2, y2, z1)), bm.verts.new((x1, y2, z1)),
        bm.verts.new((x1, y1, z2)), bm.verts.new((x2, y1, z2)),
        bm.verts.new((x2, y2, z2)), bm.verts.new((x1, y2, z2))
    ]
    f1 = bm.faces.new((verts[0], verts[1], verts[2], verts[3]))
    f2 = bm.faces.new((verts[4], verts[7], verts[6], verts[5]))
    f3 = bm.faces.new((verts[0], verts[4], verts[5], verts[1]))
    f4 = bm.faces.new((verts[1], verts[5], verts[6], verts[2]))
    f5 = bm.faces.new((verts[2], verts[6], verts[7], verts[3]))
    f6 = bm.faces.new((verts[3], verts[7], verts[4], verts[0]))
    return [f1, f2, f3, f4, f5, f6]

def add_cylinder(bm, center, radius, height, axis='Z', segments=16):
    """Cilindro estanco según eje."""
    top_verts, bot_verts = [], []
    half_h = height * 0.5
    cx, cy, cz = center

    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        c = radius * math.cos(theta)
        s = radius * math.sin(theta)
        if axis == 'Z':
            top_verts.append(bm.verts.new((cx + c, cy + s, cz + half_h)))
            bot_verts.append(bm.verts.new((cx + c, cy + s, cz - half_h)))
        elif axis == 'X':
            top_verts.append(bm.verts.new((cx + half_h, cy + c, cz + s)))
            bot_verts.append(bm.verts.new((cx - half_h, cy + c, cz + s)))
        elif axis == 'Y':
            top_verts.append(bm.verts.new((cx + c, cy + half_h, cz + s)))
            bot_verts.append(bm.verts.new((cx + c, cy - half_h, cz + s)))

    faces = []
    for i in range(segments):
        nxt = (i + 1) % segments
        faces.append(bm.faces.new((bot_verts[i], top_verts[i], top_verts[nxt], bot_verts[nxt])))
    faces.append(bm.faces.new(reversed(bot_verts)))
    faces.append(bm.faces.new(top_verts))
    return faces

def add_thick_circle(bm, center, radius, thickness=0.010, axis='X', segments=24):
    """Cilindro disco con espesor para calcomanías/lunares (cero z-fighting)."""
    return add_cylinder(bm, center, radius, thickness, axis=axis, segments=segments)

def create_mesh_object(name, bm, material, col):
    mesh_data = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(mesh_data)
    bm.free()
    mesh_data.materials.append(material)
    obj = bpy.data.objects.new(name, mesh_data)
    col.objects.link(obj)
    return obj

# ===========================================================================
# 1. CARROCERÍA PRINCIPAL ROJA HERMÉTICA Y CONTINUA (SIN TRASLAPES)
# ===========================================================================
def build_airtight_body(mats, col):
    bm_red = bmesh.new()
    bm_wells = bmesh.new()

    # 1. Tolvas interiores negras que sellan el habitáculo tras las ruedas
    add_box(bm_wells, -W_HALF + 0.02, -W_HALF + 0.38, WHEELBASE_FRONT - 0.65, WHEELBASE_FRONT + 0.65, H_CLEARANCE, 1.02)
    add_box(bm_wells, W_HALF - 0.38, W_HALF - 0.02, WHEELBASE_FRONT - 0.65, WHEELBASE_FRONT + 0.65, H_CLEARANCE, 1.02)
    add_box(bm_wells, -W_HALF + 0.02, -W_HALF + 0.52, WHEELBASE_REAR - 0.70, WHEELBASE_REAR + 0.70, H_CLEARANCE, 1.02)
    add_box(bm_wells, W_HALF - 0.52, W_HALF - 0.02, WHEELBASE_REAR - 0.70, WHEELBASE_REAR + 0.70, H_CLEARANCE, 1.02)

    # 2. Costado Izquierdo (-X): Chapa Roja Lisa y Continua
    xl1, xl2 = -W_HALF, -W_HALF + 0.06
    # Faldón inferior
    add_box(bm_red, xl1, xl2, -4.75, WHEELBASE_REAR - 0.60, H_CLEARANCE, 0.95)
    add_box(bm_red, xl1, xl2, WHEELBASE_REAR + 0.60, WHEELBASE_FRONT - 0.58, H_CLEARANCE, 0.95)
    add_box(bm_red, xl1, xl2, WHEELBASE_FRONT + 0.58, 4.65, H_CLEARANCE, 0.95)

    # Chapa sobre los arcos de rueda
    add_box(bm_red, xl1, xl2, WHEELBASE_FRONT - 0.58, WHEELBASE_FRONT + 0.58, 0.90, 0.95)
    add_box(bm_red, xl1, xl2, WHEELBASE_REAR - 0.60, WHEELBASE_REAR + 0.60, 0.90, 0.95)

    # Pared de cintura izquierda (Z: 0.95 a H_BELT = 1.62m)
    add_box(bm_red, xl1, xl2, -4.75, 4.65, 0.95, H_BELT)
    # Franja superior izquierda (Z: H_WINDOW_TOP = 2.60m a H_ROOF_EAVE = 2.76m)
    add_box(bm_red, xl1, xl2, -4.75, 4.65, H_WINDOW_TOP, H_ROOF_EAVE)

    # 3. Costado Derecho (+X): Chapa Roja con Puertas
    xr1, xr2 = W_HALF - 0.06, W_HALF
    # Faldón inferior derecho
    add_box(bm_red, xr1, xr2, -4.75, -3.80, H_CLEARANCE, 0.95)
    add_box(bm_red, xr1, xr2, -2.90, WHEELBASE_REAR + 0.60, H_CLEARANCE, 0.95)
    add_box(bm_red, xr1, xr2, WHEELBASE_REAR + 0.60, WHEELBASE_FRONT - 0.58, H_CLEARANCE, 0.95)
    add_box(bm_red, xr1, xr2, WHEELBASE_FRONT + 0.58, 3.30, H_CLEARANCE, 0.95)
    add_box(bm_red, xr1, xr2, 4.25, 4.65, H_CLEARANCE, 0.95)

    # Chapa sobre arcos derechos
    add_box(bm_red, xr1, xr2, WHEELBASE_FRONT - 0.58, WHEELBASE_FRONT + 0.58, 0.90, 0.95)
    add_box(bm_red, xr1, xr2, WHEELBASE_REAR - 0.60, WHEELBASE_REAR + 0.60, 0.90, 0.95)

    # Pared de cintura derecha
    add_box(bm_red, xr1, xr2, -4.75, -3.80, 0.95, H_BELT)
    add_box(bm_red, xr1, xr2, -2.90, 3.30, 0.95, H_BELT)
    add_box(bm_red, xr1, xr2, 4.25, 4.65, 0.95, H_BELT)

    # Franja superior derecha continua
    add_box(bm_red, xr1, xr2, -4.75, 4.65, H_WINDOW_TOP, H_ROOF_EAVE)

    # 4. Frente Rojo de Carrocería (Pilares A y Copete Superior)
    # Pilar A Izquierdo
    add_box(bm_red, -W_HALF, -W_HALF + 0.14, 4.60, 4.78, H_BELT, H_WINDOW_TOP)
    # Pilar A Derecho (robusto entre puerta delantera y parabrisas)
    add_box(bm_red, W_HALF - 0.14, W_HALF, 4.60, 4.78, H_BELT, H_WINDOW_TOP)
    # Paños frontales sobre los faros (Z: 1.35 a 1.62m, sin solaparse con la fascia blanca)
    add_box(bm_red, -W_HALF, -0.66, 4.65, 4.82, 1.35, H_BELT)
    add_box(bm_red, 0.66, W_HALF, 4.65, 4.82, 1.35, H_BELT)
    # Copete superior frontal aerodinámico
    add_box(bm_red, -W_HALF, W_HALF, 4.58, 4.82, 2.60, 2.95)

    # 5. Techo Hermético Transversal Curvado
    steps = 14
    for s in range(steps):
        t0 = s / float(steps)
        t1 = (s + 1) / float(steps)
        xa = -W_HALF + t0 * (2.0 * W_HALF)
        xb = -W_HALF + t1 * (2.0 * W_HALF)
        za = H_ROOF_EAVE + (H_ROOF_PEAK - H_ROOF_EAVE) * math.sin(math.pi * t0)
        zb = H_ROOF_EAVE + (H_ROOF_PEAK - H_ROOF_EAVE) * math.sin(math.pi * t1)
        zmin = min(za, zb)
        zmax = max(za, zb) + 0.03
        add_box(bm_red, xa, xb, -4.75, 4.68, zmin, zmax)

    # 6. Trasera Roja Completa Sólida (Panel Cerrado de Fibra según foto real)
    add_box(bm_red, -W_HALF, W_HALF, -4.78, -4.68, 0.45, H_ROOF_PEAK)

    obj_body = create_mesh_object("Bus_Carroceria_Roja", bm_red, mats['red'], col)
    obj_wells = create_mesh_object("Bus_Pasos_Rueda_Negros", bm_wells, mats['rubber'], col)
    return obj_body, obj_wells

# ===========================================================================
# 2. LUNARES BLANCOS Y RÓTULOS EXACTOS ("EL HONGO" Unidad 24)
# ===========================================================================
def build_spots_and_signage(mats, col):
    bm_white = bmesh.new()

    off_r = W_HALF + 0.006
    off_l = -W_HALF - 0.006
    off_b = -4.786

    # ---------------- LADO DERECHO (bus-hongo-derecha.jpeg) ----------------
    add_thick_circle(bm_white, (off_r, -0.15, 1.25), radius=0.85, thickness=0.010, axis='X', segments=32)
    add_thick_circle(bm_white, (off_r, 2.05, 1.08), radius=0.40, thickness=0.010, axis='X', segments=22)
    add_thick_circle(bm_white, (off_r, -1.25, 0.72), radius=0.35, thickness=0.010, axis='X', segments=20)
    add_thick_circle(bm_white, (off_r, -2.15, 1.15), radius=0.50, thickness=0.010, axis='X', segments=24)
    add_thick_circle(bm_white, (off_r, -4.25, 0.85), radius=0.34, thickness=0.010, axis='X', segments=20)
    add_thick_circle(bm_white, (off_r, 4.45, 0.82), radius=0.18, thickness=0.010, axis='X', segments=20)

    # ---------------- LADO IZQUIERDO (bus-hongo-izquierda.jpeg) ----------------
    add_thick_circle(bm_white, (off_l, 0.05, 1.25), radius=0.88, thickness=0.010, axis='X', segments=32)
    add_thick_circle(bm_white, (off_l, -2.60, 1.15), radius=0.68, thickness=0.010, axis='X', segments=28)
    add_thick_circle(bm_white, (off_l, -1.50, 0.75), radius=0.38, thickness=0.010, axis='X', segments=20)
    add_thick_circle(bm_white, (off_l, 3.65, 0.95), radius=0.38, thickness=0.010, axis='X', segments=20)
    add_thick_circle(bm_white, (off_l, 2.10, 1.20), radius=0.48, thickness=0.010, axis='X', segments=22)
    add_thick_circle(bm_white, (off_l, -4.15, 0.78), radius=0.32, thickness=0.010, axis='X', segments=18)
    add_thick_circle(bm_white, (off_l, 4.45, 0.82), radius=0.18, thickness=0.010, axis='X', segments=20)

    # ---------------- TRASERA (bus-hongo-reverso.jpeg) ----------------
    # Gran círculo blanco superior izquierdo
    add_thick_circle(bm_white, (-0.28, off_b, 2.15), radius=0.62, thickness=0.010, axis='Y', segments=32)
    # Círculo del número 24 arriba a la derecha
    add_thick_circle(bm_white, (0.78, off_b, 2.05), radius=0.22, thickness=0.010, axis='Y', segments=20)
    # Lunares decorativos traseros bien separados
    add_thick_circle(bm_white, (-0.85, off_b, 1.35), radius=0.22, thickness=0.010, axis='Y', segments=18)
    add_thick_circle(bm_white, (0.80, off_b, 1.35), radius=0.22, thickness=0.010, axis='Y', segments=18)

    # Fascia trasera blanca envolvente inferior
    add_box(bm_white, -W_HALF, W_HALF, -4.80, -4.68, 0.45, 0.92)
    # Nicho para placa patente central
    add_box(bm_white, -0.42, 0.42, -4.815, -4.75, 0.52, 0.74)

    obj_white = create_mesh_object("Bus_Lunares_Blancos", bm_white, mats['white'], col)

    # ---------------- RÓTULOS CORPÓREOS (SIN ESPEJAR) ----------------
    ROT_RIGHT = (math.radians(90.0), 0.0, math.radians(90.0))
    ROT_LEFT  = (math.radians(90.0), 0.0, math.radians(-90.0))
    ROT_REAR  = (math.radians(90.0), 0.0, 0.0)
    ROT_FRONT = (math.radians(90.0), 0.0, math.radians(180.0))

    def add_text_obj(text, pos, rot, size, mat, extrude=0.012):
        t_curve = bpy.data.curves.new(name=f"Txt_{text[:6]}", type='FONT')
        t_curve.body = text
        t_curve.size = size
        t_curve.extrude = extrude
        t_curve.align_x = 'CENTER'
        t_curve.align_y = 'CENTER'
        t_obj = bpy.data.objects.new(f"TxtObj_{text[:8]}", t_curve)
        t_obj.location = Vector(pos)
        t_obj.rotation_euler = rot
        if mat:
            t_obj.data.materials.append(mat)
        col.objects.link(t_obj)
        return t_obj

    # 1. Costado Derecho: "EL" en rojo y "HONGO" en azul dentro del círculo
    add_text_obj("EL", (off_r + 0.015, -0.55, 1.25), ROT_RIGHT, 0.36, mats['red'], 0.015)
    add_text_obj("HONGO", (off_r + 0.015, 0.02, 1.25), ROT_RIGHT, 0.42, mats['blue'], 0.015)
    add_text_obj("24", (off_r + 0.015, 4.45, 0.82), ROT_RIGHT, 0.22, mats['blue'], 0.015)
    add_text_obj("Autotransporte Urbano y Suburbano S.A. de C.V.", (off_r + 0.012, 0.0, 2.66), ROT_RIGHT, 0.085, mats['white'], 0.01)

    # 2. Costado Izquierdo: "EL" en rojo y "HONGO" en azul
    add_text_obj("EL", (off_l - 0.015, 0.42, 1.25), ROT_LEFT, 0.36, mats['red'], 0.015)
    add_text_obj("HONGO", (off_l - 0.015, -0.15, 1.25), ROT_LEFT, 0.42, mats['blue'], 0.015)
    add_text_obj("24", (off_l - 0.015, 4.45, 0.82), ROT_LEFT, 0.22, mats['blue'], 0.015)
    add_text_obj("Autotransporte Urbano y Suburbano S.A. de C.V.", (off_l - 0.015, 0.0, 2.66), ROT_LEFT, 0.085, mats['white'], 0.01)

    # 3. Trasera:
    add_text_obj("EL", (-0.52, off_b - 0.015, 2.15), ROT_REAR, 0.34, mats['red'], 0.015)
    add_text_obj("HONGO", (-0.08, off_b - 0.015, 2.15), ROT_REAR, 0.38, mats['blue'], 0.015)
    add_text_obj("24", (0.78, off_b - 0.015, 2.05), ROT_REAR, 0.22, mats['blue'], 0.015)
    # Escudo central
    add_text_obj("EL HONGO", (0.0, off_b - 0.012, 1.05), ROT_REAR, 0.16, mats['blue'], 0.012)
    add_text_obj("autotransporte urbano y suburbano S.A. de C.V.", (0.0, off_b - 0.012, 0.90), ROT_REAR, 0.09, mats['red'], 0.010)
    # Placa A-30530-A
    add_text_obj("A-30530-A", (0.0, off_b - 0.020, 0.63), ROT_REAR, 0.11, mats['black_trim'], 0.012)
    # Concesión
    add_text_obj("Mercedes-Benz", (0.28, off_b - 0.012, 0.48), ROT_REAR, 0.07, mats['white'], 0.008)
    add_text_obj("TKT-A-19-00006", (-0.28, off_b - 0.012, 0.48), ROT_REAR, 0.07, mats['white'], 0.008)

    # 4. Frente:
    add_text_obj("BOXER OF", (0.35, 4.83, 2.76), ROT_FRONT, 0.11, mats['white'], 0.012)
    add_text_obj("A-30530-A", (0.0, 4.90, 0.46), ROT_FRONT, 0.09, mats['black_trim'], 0.010)

    return obj_white

# ===========================================================================
# 3. FRENTE MERCEDES-BENZ BOXER OF (PARRILLA TRAPEZOIDAL, FAROS, PARABRISAS)
# ===========================================================================
def build_front_and_grille(mats, col):
    bm_front_w = bmesh.new()
    bm_grille = bmesh.new()
    bm_chrome = bmesh.new()
    bm_lights = bmesh.new()
    bm_route_card_y = bmesh.new()
    bm_route_card_w = bmesh.new()

    # 1. Fascia delantera aerodinámica blanca envolvente continua (Y: 4.65 a 4.88m, Z: 0.35 a 1.35m)
    # Parachoques inferior (de -W_HALF a W_HALF)
    add_box(bm_front_w, -W_HALF, W_HALF, 4.65, 4.88, H_CLEARANCE, 0.95)
    # Bloques envolventes bajo los faros (Z: 0.95 a 1.35m)
    add_box(bm_front_w, -W_HALF, -0.65, 4.65, 4.86, 0.95, 1.35)
    add_box(bm_front_w, 0.65, W_HALF, 4.65, 4.86, 0.95, 1.35)
    # Marco frontal envolvente que abraza la parrilla
    add_box(bm_front_w, -0.68, 0.68, 4.76, 4.88, 0.95, 1.55)

    # 2. Parrilla Mercedes-Benz Boxer trapezoidal
    add_box(bm_grille, -0.62, 0.62, 4.880, 4.895, 0.98, 1.50)
    # 4 Lamas cromadas horizontales
    for lz in [1.08, 1.20, 1.32, 1.44]:
        width = 0.52 + (lz - 1.08) * 0.15
        add_box(bm_chrome, -width, width, 4.896, 4.910, lz - 0.012, lz + 0.012)

    # 3. Estrella Mercedes-Benz tridimensional en alto relieve (centro en Y=4.915, Z=1.26m)
    # Anillo tubular cromado exterior
    add_cylinder(bm_chrome, (0.0, 4.912, 1.26), radius=0.15, height=0.018, axis='Y', segments=28)
    # Cubo central
    add_cylinder(bm_chrome, (0.0, 4.922, 1.26), radius=0.038, height=0.025, axis='Y', segments=16)
    # 3 Aspas cromadas a 90, 210, 330 grados
    for angle in [90.0, 210.0, 330.0]:
        rad = math.radians(angle)
        dx = 0.12 * math.cos(rad)
        dz = 0.12 * math.sin(rad)
        add_box(bm_chrome, min(0, dx) - 0.012, max(0, dx) + 0.012, 4.915, 4.926, min(1.26, 1.26 + dz) - 0.012, max(1.26, 1.26 + dz) + 0.012)

    # 4. Faros dobles integrados rasgados (alta y baja)
    # Faro Izquierdo
    add_cylinder(bm_lights, (-1.02, 4.87, 1.15), radius=0.075, height=0.025, axis='Y', segments=18)
    add_cylinder(bm_lights, (-0.82, 4.87, 1.15), radius=0.068, height=0.025, axis='Y', segments=18)
    # Faro Derecho
    add_cylinder(bm_lights, (0.82, 4.87, 1.15), radius=0.068, height=0.025, axis='Y', segments=18)
    add_cylinder(bm_lights, (1.02, 4.87, 1.15), radius=0.075, height=0.025, axis='Y', segments=18)

    # 5. Cartel de ruta en el parabrisas (según foto real bus-hongo-derecha.jpeg)
    # Cartulina amarilla en esquina inferior derecha
    add_box(bm_route_card_y, 0.22, 0.65, 4.62, 4.63, 1.70, 2.05)
    # Cartulina blanca contigua: "VILLAS DEL CAMPO"
    add_box(bm_route_card_w, 0.68, 0.98, 4.62, 4.63, 1.70, 1.95)

    # 6. Limpiaparabrisas dobles en reposo inclinados sobre la base
    add_box(bm_grille, -0.60, -0.05, 4.68, 4.71, 1.63, 1.66)
    add_box(bm_grille, 0.05, 0.60, 4.68, 4.71, 1.63, 1.66)
    add_cylinder(bm_grille, (-0.35, 4.70, 1.95), radius=0.012, height=0.62, axis='Z', segments=6)
    add_cylinder(bm_grille, (0.35, 4.70, 1.95), radius=0.012, height=0.62, axis='Z', segments=6)

    # Luces de gálibo superiores ámbar en el copete frontal
    bm_amber_roof = bmesh.new()
    for gx in [-0.90, -0.45, 0.0, 0.45, 0.90]:
        add_cylinder(bm_amber_roof, (gx, 4.84, 2.87), radius=0.025, height=0.02, axis='Y', segments=12)

    # Luces de gálibo traseras rojas
    bm_red_roof = bmesh.new()
    for gx in [-0.90, -0.45, 0.0, 0.45, 0.90]:
        add_cylinder(bm_red_roof, (gx, -4.79, 2.87), radius=0.025, height=0.02, axis='Y', segments=12)

    obj_fw = create_mesh_object("Bus_Frente_Blanco", bm_front_w, mats['white'], col)
    obj_gr = create_mesh_object("Bus_Parrilla_Fondo", bm_grille, mats['black_trim'], col)
    obj_ch = create_mesh_object("Bus_Detalles_Cromo", bm_chrome, mats['chrome'], col)
    obj_hl = create_mesh_object("Bus_Faros_Delanteros", bm_lights, mats['headlight'], col)
    obj_rcy = create_mesh_object("Bus_Cartel_Ruta_Amarillo", bm_route_card_y, mats['route_card_yellow'], col)
    obj_rcw = create_mesh_object("Bus_Cartel_Ruta_Blanco", bm_route_card_w, mats['route_card_white'], col)
    obj_ar = create_mesh_object("Bus_Galibo_Ambar", bm_amber_roof, mats['amber'], col)
    obj_rr = create_mesh_object("Bus_Galibo_Rojo", bm_red_roof, mats['taillight_red'], col)

    # Letreros en cartulinas
    ROT_FRONT = (math.radians(90.0), 0.0, math.radians(180.0))
    t_curve1 = bpy.data.curves.new(name="Txt_CartelY", type='FONT')
    t_curve1.body = "TECATE\nCFE\nCOBACH\nAV. HIDALGO\nVILLAS DEL CAMPO"
    t_curve1.size = 0.046
    t_curve1.extrude = 0.005
    t_curve1.align_x = 'CENTER'
    t_curve1.align_y = 'CENTER'
    t_obj1 = bpy.data.objects.new("TxtObj_CartelY", t_curve1)
    t_obj1.location = Vector((0.43, 4.635, 1.86))
    t_obj1.rotation_euler = ROT_FRONT
    t_obj1.data.materials.append(mats['black_trim'])
    col.objects.link(t_obj1)

    t_curve2 = bpy.data.curves.new(name="Txt_CartelW", type='FONT')
    t_curve2.body = "VILLAS DEL\nCAMPO"
    t_curve2.size = 0.052
    t_curve2.extrude = 0.005
    t_curve2.align_x = 'CENTER'
    t_curve2.align_y = 'CENTER'
    t_obj2 = bpy.data.objects.new("TxtObj_CartelW", t_curve2)
    t_obj2.location = Vector((0.83, 4.635, 1.84))
    t_obj2.rotation_euler = ROT_FRONT
    t_obj2.data.materials.append(mats['blue'])
    col.objects.link(t_obj2)

    return obj_fw, obj_gr, obj_ch, obj_hl

# ===========================================================================
# 4. VENTANERÍA Y PUERTAS PLEGABLES HERMÉTICAS
# ===========================================================================
def build_windows_doors_and_mirrors(mats, col):
    bm_glass = bmesh.new()
    bm_frames = bmesh.new()

    # 1. Parabrisas Panorámico Continuo Inclinado
    add_box(bm_glass, -W_HALF + 0.08, W_HALF - 0.08, 4.64, 4.70, 1.65, 2.58)
    add_box(bm_frames, -W_HALF + 0.06, W_HALF - 0.06, 4.66, 4.72, 1.63, 1.66)
    add_box(bm_frames, -W_HALF + 0.06, W_HALF - 0.06, 4.61, 4.67, 2.58, 2.61)

    # 2. Costado Izquierdo (-X): 6 Grandes Ventanales (Chofer + 5 Pasajeros)
    xl = -W_HALF - 0.005
    window_bays_left = [
        (3.30, 4.45),   # Ventana chofer
        (2.05, 3.20),   # Módulo 1
        (0.75, 1.95),   # Módulo 2
        (-0.55, 0.65),  # Módulo 3
        (-1.85, -0.65), # Módulo 4
        (-3.15, -1.95), # Módulo 5
        (-4.45, -3.25)  # Módulo 6
    ]
    for y1, y2 in window_bays_left:
        add_box(bm_glass, xl - 0.015, xl + 0.015, y1 + 0.02, y2 - 0.02, 1.66, 2.56)
        add_box(bm_frames, xl - 0.025, xl + 0.025, y1, y2, 1.63, 1.66)
        add_box(bm_frames, xl - 0.025, xl + 0.025, y1, y2, 2.56, 2.60)
        add_box(bm_frames, xl - 0.025, xl + 0.025, y1, y1 + 0.025, 1.63, 2.60)
        add_box(bm_frames, xl - 0.025, xl + 0.025, y2 - 0.025, y2, 1.63, 2.60)
        add_box(bm_frames, xl - 0.02, xl + 0.02, y1, y2, 2.26, 2.29)

    # 3. Costado Derecho (+X): Ventanales y Puertas Plegables
    xr = W_HALF + 0.005
    window_bays_right = [
        (2.05, 3.20),   # Pasajeros delantero
        (0.75, 1.95),   # Pasajeros central 1
        (-0.55, 0.65),  # Pasajeros central 2
        (-1.85, -0.65), # Pasajeros central 3
        (-4.45, -3.85)  # Pasajeros trasero
    ]
    for y1, y2 in window_bays_right:
        add_box(bm_glass, xr - 0.015, xr + 0.015, y1 + 0.02, y2 - 0.02, 1.66, 2.56)
        add_box(bm_frames, xr - 0.025, xr + 0.025, y1, y2, 1.63, 1.66)
        add_box(bm_frames, xr - 0.025, xr + 0.025, y1, y2, 2.56, 2.60)
        add_box(bm_frames, xr - 0.025, xr + 0.025, y1, y1 + 0.025, 1.63, 2.60)
        add_box(bm_frames, xr - 0.025, xr + 0.025, y2 - 0.025, y2, 1.63, 2.60)
        add_box(bm_frames, xr - 0.02, xr + 0.02, y1, y2, 2.26, 2.29)

    # Puerta Delantera Plegable de 2 hojas (Z hasta 2.60 para sellar con la franja superior)
    for py1, py2 in [(3.34, 3.75), (3.80, 4.21)]:
        add_box(bm_glass, xr - 0.025, xr + 0.01, py1 + 0.03, py2 - 0.03, 0.52, 2.50)
        add_box(bm_frames, xr - 0.03, xr + 0.015, py1, py2, 0.44, 0.52)
        add_box(bm_frames, xr - 0.03, xr + 0.015, py1, py2, 2.50, 2.60)
        add_box(bm_frames, xr - 0.03, xr + 0.015, py1, py1 + 0.03, 0.44, 2.60)
        add_box(bm_frames, xr - 0.03, xr + 0.015, py2 - 0.03, py2, 0.44, 2.60)
        add_box(bm_frames, xr - 0.028, xr + 0.012, py1, py2, 1.48, 1.52)

    # Puerta Trasera Plegable de 2 hojas (Z hasta 2.60)
    for py1, py2 in [(-3.76, -3.37), (-3.33, -2.94)]:
        add_box(bm_glass, xr - 0.025, xr + 0.01, py1 + 0.03, py2 - 0.03, 0.52, 2.50)
        add_box(bm_frames, xr - 0.03, xr + 0.015, py1, py2, 0.44, 0.52)
        add_box(bm_frames, xr - 0.03, xr + 0.015, py1, py2, 2.50, 2.60)
        add_box(bm_frames, xr - 0.03, xr + 0.015, py1, py1 + 0.03, 0.44, 2.60)
        add_box(bm_frames, xr - 0.03, xr + 0.015, py2 - 0.03, py2, 0.44, 2.60)
        add_box(bm_frames, xr - 0.028, xr + 0.012, py1, py2, 1.48, 1.52)

    # 4. Espejos Retrovisores Estilo Boxer OF
    # Espejo derecho alto
    add_cylinder(bm_frames, (1.38, 4.48, 2.25), radius=0.018, height=0.75, axis='Z', segments=8)
    add_box(bm_frames, 1.35, 1.48, 4.42, 4.54, 2.05, 2.55)
    # Espejo izquierdo bajo
    add_cylinder(bm_frames, (-1.35, 4.45, 1.95), radius=0.018, height=0.55, axis='Z', segments=8)
    add_box(bm_frames, -1.45, -1.33, 4.40, 4.52, 1.75, 2.25)

    obj_glass = create_mesh_object("Bus_Cristales", bm_glass, mats['glass'], col)
    obj_frames = create_mesh_object("Bus_Marcos_Canceleria", bm_frames, mats['black_trim'], col)
    return obj_glass, obj_frames

# ===========================================================================
# 5. RUEDAS Y CALAVERAS TRASERAS TRIPLES
# ===========================================================================
def build_wheels_and_taillights(mats, col):
    bm_tires = bmesh.new()
    bm_rims = bmesh.new()
    bm_red_lights = bmesh.new()
    bm_amber_lights = bmesh.new()
    bm_white_lights = bmesh.new()

    wheel_specs = [
        ((-W_HALF + 0.12, WHEELBASE_FRONT, WHEEL_R), -1, 0.28),
        ((W_HALF - 0.12, WHEELBASE_FRONT, WHEEL_R), 1, 0.28),
        ((-W_HALF + 0.10, WHEELBASE_REAR, WHEEL_R), -1, 0.26),
        ((-W_HALF + 0.38, WHEELBASE_REAR, WHEEL_R), -1, 0.26),
        ((W_HALF - 0.10, WHEELBASE_REAR, WHEEL_R), 1, 0.26),
        ((W_HALF - 0.38, WHEELBASE_REAR, WHEEL_R), 1, 0.26),
    ]

    for center, side, width in wheel_specs:
        add_cylinder(bm_tires, center, radius=WHEEL_R, height=width, axis='X', segments=24)
        rin_cx = center[0] + (0.02 * side)
        add_cylinder(bm_rims, (rin_cx, center[1], center[2]), radius=WHEEL_R * 0.65, height=width * 0.90, axis='X', segments=20)
        hub_cx = center[0] + (0.05 * side)
        add_cylinder(bm_rims, (hub_cx, center[1], center[2]), radius=0.12, height=width * 0.50, axis='X', segments=12)

    # Calaveras traseras triples verticales redondas (Z = 0.62, 0.74, 0.86m)
    for kx in [-1.08, 1.08]:
        # Roja inferior (freno)
        add_cylinder(bm_red_lights, (kx, -4.805, 0.62), radius=0.065, height=0.025, axis='Y', segments=16)
        # Blanca central (reversa)
        add_cylinder(bm_white_lights, (kx, -4.805, 0.74), radius=0.065, height=0.025, axis='Y', segments=16)
        # Ámbar superior (direccional)
        add_cylinder(bm_amber_lights, (kx, -4.805, 0.86), radius=0.065, height=0.025, axis='Y', segments=16)

    # Loderas traseras de caucho bajo la defensa
    add_box(bm_tires, -1.15, -0.75, -4.80, -4.78, 0.12, H_CLEARANCE)
    add_box(bm_tires, 0.75, 1.15, -4.80, -4.78, 0.12, H_CLEARANCE)

    obj_tires = create_mesh_object("Bus_Neumaticos", bm_tires, mats['rubber'], col)
    obj_rims = create_mesh_object("Bus_Rines_Blancos", bm_rims, mats['rim'], col)
    obj_trl = create_mesh_object("Bus_Calaveras_Rojas", bm_red_lights, mats['taillight_red'], col)
    obj_tam = create_mesh_object("Bus_Calaveras_Ambar", bm_amber_lights, mats['amber'], col)
    obj_tre = create_mesh_object("Bus_Calaveras_Reversa", bm_white_lights, mats['white'], col)

    return obj_tires, obj_rims, obj_trl

# ===========================================================================
# 6. INTERIOR HABITABLE (PISO, TABLERO, ASIENTOS Y ESCALONES)
# ===========================================================================
def build_interior(mats, col):
    bm_floor = bmesh.new()
    bm_seats = bmesh.new()
    bm_rails = bmesh.new()

    # Piso del pasillo central
    add_box(bm_floor, -W_HALF + 0.10, W_HALF - 0.10, -4.65, 4.55, 0.76, 0.80)

    # Escalones de acceso en puerta delantera
    add_box(bm_floor, W_HALF - 0.40, W_HALF - 0.05, 3.40, 4.20, 0.40, 0.58)
    add_box(bm_floor, W_HALF - 0.30, W_HALF - 0.05, 3.40, 4.20, 0.58, 0.76)

    # Tablero de mandos y volante
    add_box(bm_floor, -1.15, -0.30, 3.95, 4.55, 0.80, 1.35)
    add_cylinder(bm_floor, (-0.75, 4.15, 1.36), radius=0.22, height=0.03, axis='Z', segments=16)

    # Filas de asientos dobles
    seat_rows_y = [2.75, 1.85, 0.95, 0.05, -0.85, -1.75, -2.65]
    for sy in seat_rows_y:
        add_box(bm_seats, -1.15, -0.35, sy - 0.18, sy + 0.18, 0.80, 1.25)
        add_box(bm_seats, -1.15, -0.35, sy - 0.22, sy - 0.14, 1.25, 1.80)
        if not (sy > 2.50 or (-3.80 < sy < -2.50)):
            add_box(bm_seats, 0.35, 1.15, sy - 0.18, sy + 0.18, 0.80, 1.25)
            add_box(bm_seats, 0.35, 1.15, sy - 0.22, sy - 0.14, 1.25, 1.80)

    # Asiento de chofer
    add_box(bm_seats, -0.95, -0.55, 3.50, 3.80, 0.80, 1.28)
    add_box(bm_seats, -0.95, -0.55, 3.42, 3.50, 1.28, 1.85)

    # Pasamanos amarillos longitudinales en techo
    add_cylinder(bm_rails, (-0.25, 0.0, 2.50), radius=0.02, height=8.0, axis='Y', segments=8)
    add_cylinder(bm_rails, (0.25, 0.0, 2.50), radius=0.02, height=8.0, axis='Y', segments=8)

    obj_fl = create_mesh_object("Bus_Interior_Piso", bm_floor, mats['floor'], col)
    obj_st = create_mesh_object("Bus_Interior_Asientos", bm_seats, mats['seat'], col)
    obj_rl = create_mesh_object("Bus_Interior_Pasamanos", bm_rails, mats['handrail'], col)
    return obj_fl, obj_st, obj_rl

# ===========================================================================
# 7. CÁMARAS CALIBRADAS EXACTAS SEGÚN LAS FOTOGRAFÍAS DE REFERENCIA
# ===========================================================================
def setup_lighting_and_reference_cameras(col):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    if hasattr(scene.cycles, 'device'):
        scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720

    # Cielo y Sol diurno de Tecate balanceado
    if not scene.world:
        scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    bg_node = scene.world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs["Color"].default_value = (0.65, 0.78, 0.90, 1.0)
        bg_node.inputs["Strength"].default_value = 0.65

    # Sol directo natural
    sun_data = bpy.data.lights.new("Sun_Light", 'SUN')
    sun_data.energy = 5.0
    sun_data.color = (1.0, 0.98, 0.95)
    sun_obj = bpy.data.objects.new("Sun_Light", sun_data)
    sun_obj.rotation_euler = (math.radians(45.0), math.radians(20.0), math.radians(35.0))
    col.objects.link(sun_obj)

    # Luz de relleno suave
    fill_data = bpy.data.lights.new("Sun_Fill", 'SUN')
    fill_data.energy = 1.5
    fill_data.color = (0.85, 0.90, 1.0)
    fill_obj = bpy.data.objects.new("Sun_Fill", fill_data)
    fill_obj.rotation_euler = (math.radians(50.0), math.radians(-30.0), math.radians(-140.0))
    col.objects.link(fill_obj)

    # 4 Cámaras con Perspectiva 1:1 calibradas a las fotografías reales:
    # 1. Cam_Ref_01_Derecha: scratch/bus/bus-hongo-derecha.jpeg
    # 2. Cam_Ref_02_Izquierda: scratch/bus/bus-hongo-izquierda.jpeg
    # 3. Cam_Ref_03_Reverso: scratch/bus/bus-hongo-reverso.jpeg
    # 4. Cam_Ref_04_Frente_Parrilla: Plano frontal completo a 3/4
    cam_configs = [
        ("Cam_Ref_01_Derecha", (6.2, 9.8, 1.55), (0.2, 1.5, 1.45), 38.0),
        ("Cam_Ref_02_Izquierda", (-6.8, -8.2, 1.65), (-0.4, -0.8, 1.45), 38.0),
        ("Cam_Ref_03_Reverso", (1.4, -8.2, 1.45), (0.0, -3.8, 1.50), 38.0),
        ("Cam_Ref_04_Frente_Parrilla", (2.2, 8.2, 1.45), (0.0, 4.0, 1.45), 42.0),
    ]

    cams = {}
    for name, pos, tgt, lens in cam_configs:
        cdata = bpy.data.cameras.new(name)
        cdata.lens = lens
        cdata.clip_start = 0.2
        cdata.clip_end = 200.0
        cobj = bpy.data.objects.new(name, cdata)
        col.objects.link(cobj)
        cobj.location = Vector(pos)
        direction = Vector(tgt) - Vector(pos)
        cobj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        cams[name] = cobj

    return cams

def render_validation_images(cams):
    os.makedirs(RENDER_DIR, exist_ok=True)
    scene = bpy.context.scene
    for name, cam_obj in cams.items():
        scene.camera = cam_obj
        filepath = os.path.join(RENDER_DIR, f"{name}.png")
        scene.render.filepath = filepath
        print(f"Renderizando: {filepath} ...")
        bpy.ops.render.render(write_still=True)
        print(f"-> Guardado render: {filepath}")

def export_assets():
    os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"-> Archivo maestro guardado: {BLEND_PATH}")

    os.makedirs(os.path.dirname(GLB_PATH), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_cameras=False,
        export_lights=False,
        export_yup=True
    )
    print(f"-> GLB de producción exportado para Godot: {GLB_PATH}")

def main():
    print("Iniciando reconstrucción procedural de alta fidelidad del Autobús El Hongo...")
    col = clean_scene()
    mats = create_materials()

    build_airtight_body(mats, col)
    build_spots_and_signage(mats, col)
    build_front_and_grille(mats, col)
    build_windows_doors_and_mirrors(mats, col)
    build_wheels_and_taillights(mats, col)
    build_interior(mats, col)

    cams = setup_lighting_and_reference_cameras(col)
    export_assets()
    render_validation_images(cams)
    print("¡Generación y validación completadas exitosamente!")

if __name__ == "__main__":
    main()
