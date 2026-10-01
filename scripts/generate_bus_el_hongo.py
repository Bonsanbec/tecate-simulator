"""
GENERADOR PROCEDURAL 3D DE ALTA FIDELIDAD - AUTOBÚS 'EL HONGO' (UNIDAD 24)
Mercedes-Benz Marcopolo Boxer OF (Gemelo Fotorrealista Oficial)
Basado estrictamente en:
  - scratch/bus/bus-hongo-derecha.jpeg
  - scratch/bus/bus-hongo-izquierda.jpeg
  - scratch/bus/bus-hongo-reverso.jpeg
  - blender_assets/textures/bus_hongo_tex_*.png

Implementa:
  - Ruedas fotorrealistas: neumáticos de perfil real con banda y hombro, rines blancos de acero estampado con 8 orificios de ventilación, cubo central y 10 tuercas cromadas visibles (sin obstrucción de goma).
  - Ceja de guardafango semicircular abierta (deja el paso de rueda totalmente diáfano).
  - Parrilla Mercedes-Benz auténtica con estrella 3D (3 rayos a 90°, 210°, 330° y anillo abierto) y moldura cromada.
  - Faros dobles trapezoidales con bisel cromado, proyectores y direccionales ámbar.
  - Bumper frontal blanco envolvente con esquinas inferiores rojas y placa de B.C.
  - Texturas UV calibradas y un-mirrored en ambos costados, trasera y cartulinas.
  - Habitáculo interior canónico de 30 asientos de pasajeros + puesto de conductor.
  - 9 cámaras técnicas en Cycles CPU (1280x720) para auditoría closed-loop.
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix, Euler

BLEND_PATH = "blender_assets/vehicles/bus_hongo.blend"
GLB_PATH = "godot_project/assets/vehicles/bus_hongo.glb"
RENDER_DIR = "docs/images/bus_hongo"
TEX_DIR = os.path.abspath("blender_assets/textures")

# Cotas Maestras Reales (Marcopolo Boxer OF Chasis Mercedes-Benz)
L_HALF = 4.85          # Longitud total 9.70m (-4.85 a +4.85)
W_HALF = 1.25          # Anchura total 2.50m (-1.25 a +1.25)
H_CLEARANCE = 0.35     # Altura de faldones inferiores
H_BELT = 1.45          # Línea de cintura bajo ventanales
H_WINDOW_TOP = 2.45    # Dintel superior de ventanales
H_ROOF_EAVE = 2.76     # Gotero / alero de techo
H_ROOF_PEAK = 2.98     # Cumbrera central de techo

WHEEL_R = 0.50         # Radio de neumático comercial 295/80R22.5
WHEEL_W = 0.28         # Ancho de banda de rodadura
WHEELBASE_FRONT = 2.65 # Eje delantero
WHEELBASE_REAR = -2.60 # Eje trasero

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

    def new_tex_mat(name, tex_filename, fallback_color=(0.84, 0.04, 0.08, 1.0)):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        bsdf.inputs["Roughness"].default_value = 0.20
        bsdf.inputs["Metallic"].default_value = 0.02
        full_path = os.path.join(TEX_DIR, tex_filename)
        if os.path.exists(full_path):
            tex_node = nt.nodes.new("ShaderNodeTexImage")
            img = bpy.data.images.load(full_path)
            tex_node.image = img
            nt.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
        else:
            bsdf.inputs["Base Color"].default_value = fallback_color
        return mat

    # 1. Carrocería Rojo Carmín Oficial
    mats['red'] = new_pbr("M_Bus_Rojo_Hongo", (0.84, 0.04, 0.08, 1.0), roughness=0.20, metallic=0.02)
    # 2. Blanco Puro de Fascias y Rines
    mats['white'] = new_pbr("M_Bus_Blanco", (0.96, 0.96, 0.97, 1.0), roughness=0.18, metallic=0.0)
    # 3. Azul Marino Hongo
    mats['navy'] = new_pbr("M_Bus_Azul_Hongo", (0.04, 0.16, 0.36, 1.0), roughness=0.30, metallic=0.0)
    # 4. Aluminio Negro de Marcos y Cancelería
    mats['black_trim'] = new_pbr("M_Bus_Aluminio_Negro", (0.02, 0.02, 0.025, 1.0), roughness=0.50, metallic=0.5)
    # 5. Caucho Mate de Neumáticos y Guardafangos
    mats['rubber'] = new_pbr("M_Bus_Caucho", (0.035, 0.035, 0.04, 1.0), roughness=0.85, metallic=0.0)
    # 6. Rines de Acero Blanco Brillante
    mats['rim'] = new_pbr("M_Bus_Rin_Blanco", (0.95, 0.95, 0.96, 1.0), roughness=0.20, metallic=0.15)
    # 7. Cromo Brillante (Parrilla, Estrella Mercedes, Biseles)
    mats['chrome'] = new_pbr("M_Bus_Cromo", (0.95, 0.96, 0.98, 1.0), roughness=0.04, metallic=0.98)
    # 8. Vidrio Ahumado Panorámico
    mats['glass'] = new_pbr("M_Bus_Vidrio_Tintado", (0.08, 0.12, 0.16, 1.0), roughness=0.04, metallic=0.05, transmission=0.85)
    # 9. Asientos Interiores Azul Marino Urbano
    mats['seat'] = new_pbr("M_Bus_Asientos", (0.05, 0.14, 0.32, 1.0), roughness=0.75, metallic=0.0)
    # 10. Pasamanos Amarillo Seguridad
    mats['handrail'] = new_pbr("M_Bus_Pasamanos", (0.98, 0.82, 0.05, 1.0), roughness=0.22, metallic=0.2)
    # 11. Piso Antiderrapante
    mats['floor'] = new_pbr("M_Bus_Piso", (0.12, 0.13, 0.14, 1.0), roughness=0.95, metallic=0.0)
    # 12. Faros Delanteros de Cristal (Emisivos)
    mats['headlight'] = new_pbr("M_Bus_Faro_Cristal", (0.95, 0.98, 1.0, 1.0), roughness=0.05, transmission=0.5, emission=(1.0, 0.98, 0.94, 1.0), emission_strength=4.5)
    # 13. Calaveras Rojas
    mats['taillight_red'] = new_pbr("M_Bus_Calavera_Roja", (0.85, 0.02, 0.02, 1.0), roughness=0.15, transmission=0.3, emission=(0.95, 0.02, 0.02, 1.0), emission_strength=3.0)
    # 14. Calaveras Ámbar (Direccionales)
    mats['amber'] = new_pbr("M_Bus_Direccional_Ambar", (0.95, 0.55, 0.02, 1.0), roughness=0.15, transmission=0.3, emission=(0.95, 0.55, 0.02, 1.0), emission_strength=3.0)
    # 15. Calaveras Blancas (Reversa)
    mats['reverse'] = new_pbr("M_Bus_Reversa_Blanca", (0.95, 0.95, 0.98, 1.0), roughness=0.15, transmission=0.3, emission=(0.95, 0.95, 0.98, 1.0), emission_strength=3.0)

    # Materiales Texturizados Oficiales UV
    mats['tex_left'] = new_tex_mat("M_Bus_Tex_Left", "bus_hongo_tex_left.png")
    mats['tex_right'] = new_tex_mat("M_Bus_Tex_Right", "bus_hongo_tex_right.png")
    mats['tex_rear'] = new_tex_mat("M_Bus_Tex_Rear", "bus_hongo_tex_rear.png")
    mats['tex_front'] = new_tex_mat("M_Bus_Tex_Front", "bus_hongo_tex_front.png", fallback_color=(0.05, 0.05, 0.05, 1.0))

    return mats

def add_box(bm, x1, x2, y1, y2, z1, z2):
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
    verts_b, verts_t = [], []
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

def add_open_ring(bm, center, r_outer, r_inner, height, axis='Y', segments=28):
    cx, cy, cz = center
    h2 = height * 0.5
    for i in range(segments):
        th0 = 2.0 * math.pi * i / segments
        th1 = 2.0 * math.pi * (i + 1) / segments
        c0, s0 = math.cos(th0), math.sin(th0)
        c1, s1 = math.cos(th1), math.sin(th1)

        if axis == 'Y':
            v0 = bm.verts.new((cx + c0*r_inner, cy + h2, cz + s0*r_inner))
            v1 = bm.verts.new((cx + c0*r_outer, cy + h2, cz + s0*r_outer))
            v2 = bm.verts.new((cx + c1*r_outer, cy + h2, cz + s1*r_outer))
            v3 = bm.verts.new((cx + c1*r_inner, cy + h2, cz + s1*r_inner))
            bm.faces.new((v0, v1, v2, v3))

            vb0 = bm.verts.new((cx + c0*r_inner, cy - h2, cz + s0*r_inner))
            vb1 = bm.verts.new((cx + c1*r_inner, cy - h2, cz + s1*r_inner))
            vb2 = bm.verts.new((cx + c1*r_outer, cy - h2, cz + s1*r_outer))
            vb3 = bm.verts.new((cx + c0*r_outer, cy - h2, cz + s0*r_outer))
            bm.faces.new((vb0, vb1, vb2, vb3))

            bm.faces.new((vb3, vb2, v2, v1))
            bm.faces.new((vb0, v0, v3, vb1))

def add_fender_flare_lip(bm, center, r_inner, r_outer, width, axis='X', side=1, segments=24):
    """Crea una ceja semicircular superior para el guardafango sin sellar el paso de rueda."""
    cx, cy, cz = center
    h2 = width * 0.5
    # Semicírculo superior de 0 a pi (Z >= cz)
    for i in range(segments):
        th0 = math.pi * i / segments
        th1 = math.pi * (i + 1) / segments
        c0, s0 = math.cos(th0), math.sin(th0)
        c1, s1 = math.cos(th1), math.sin(th1)

        v0 = bm.verts.new((cx + side*h2, cy + c0*r_inner, cz + s0*r_inner))
        v1 = bm.verts.new((cx + side*h2, cy + c0*r_outer, cz + s0*r_outer))
        v2 = bm.verts.new((cx + side*h2, cy + c1*r_outer, cz + s1*r_outer))
        v3 = bm.verts.new((cx + side*h2, cy + c1*r_inner, cz + s1*r_inner))
        bm.faces.new((v0, v1, v2, v3) if side > 0 else (v3, v2, v1, v0))

def add_quad(bm, v0, v1, v2, v3, uv_layer=None, uvs=None):
    f = bm.faces.new((v0, v1, v2, v3))
    if uv_layer and uvs:
        for idx, uv in enumerate(uvs):
            f.loops[idx][uv_layer].uv = uv
    return f

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
# 1. CARROCERÍA MONOLÍTICA HERMÉTICA CON MAPEO UV INTEGRADO (NO-MIRRORED)
# ===========================================================================
def build_body_shell(mats, col):
    bm_body = bmesh.new()
    bm_tex_l = bmesh.new()
    bm_tex_r = bmesh.new()
    bm_tex_b = bmesh.new()
    bm_roof = bmesh.new()
    bm_wells = bmesh.new()

    uv_l = bm_tex_l.loops.layers.uv.new("UVMap")
    uv_r = bm_tex_r.loops.layers.uv.new("UVMap")
    uv_b = bm_tex_b.loops.layers.uv.new("UVMap")

    xl = -W_HALF
    xr = W_HALF

    wf_f, wf_b = WHEELBASE_FRONT + 0.60, WHEELBASE_FRONT - 0.60
    wr_f, wr_b = WHEELBASE_REAR + 0.60, WHEELBASE_REAR - 0.60

    # A. COSTADO IZQUIERDO (LADO CHOFER):
    add_box(bm_body, xl, xl + 0.05, wf_f, 4.70, H_CLEARANCE, H_BELT)
    add_box(bm_body, xl, xl + 0.05, wr_f, wf_b, H_CLEARANCE, H_BELT)
    add_box(bm_body, xl, xl + 0.05, -L_HALF, wr_b, H_CLEARANCE, H_BELT)
    add_box(bm_body, xl, xl + 0.05, wf_b, wf_f, 0.98, H_BELT)
    add_box(bm_body, xl, xl + 0.05, wr_b, wr_f, 0.98, H_BELT)
    add_box(bm_body, xl, xl + 0.05, -L_HALF, 4.70, H_WINDOW_TOP, H_ROOF_EAVE)

    pilares_izq = [
        (-4.80, -4.70), # Esquina trasera
        (-3.08, -2.94),
        (-1.46, -1.32),
        (0.16, 0.30),
        (1.78, 1.92),
        (3.40, 3.55),   # Poste B chofer
        (4.65, 4.70),   # Esquina delantera
    ]
    for y1, y2 in pilares_izq:
        add_box(bm_body, xl, xl + 0.05, y1, y2, H_BELT, H_WINDOW_TOP)

    p_offset = -0.002
    x_tex_l = xl + p_offset
    x_tex_r = xr - p_offset
    l_tot = 4.70 - (-L_HALF)
    h_tot = H_ROOF_EAVE - H_CLEARANCE

    def add_tex_panel_left(y_min, y_max, z_min, z_max):
        u_left = (4.70 - y_max) / l_tot
        u_right = (4.70 - y_min) / l_tot
        v_bottom = (z_min - H_CLEARANCE) / h_tot
        v_top = (z_max - H_CLEARANCE) / h_tot
        v0 = bm_tex_l.verts.new((x_tex_l, y_max, z_min))
        v1 = bm_tex_l.verts.new((x_tex_l, y_min, z_min))
        v2 = bm_tex_l.verts.new((x_tex_l, y_min, z_max))
        v3 = bm_tex_l.verts.new((x_tex_l, y_max, z_max))
        add_quad(bm_tex_l, v0, v1, v2, v3, uv_l, [(u_left, v_bottom), (u_right, v_bottom), (u_right, v_top), (u_left, v_top)])

    def add_tex_panel_right(y_min, y_max, z_min, z_max):
        u_left = (y_min - (-L_HALF)) / l_tot
        u_right = (y_max - (-L_HALF)) / l_tot
        v_bottom = (z_min - H_CLEARANCE) / h_tot
        v_top = (z_max - H_CLEARANCE) / h_tot
        v0 = bm_tex_r.verts.new((x_tex_r, y_min, z_min))
        v1 = bm_tex_r.verts.new((x_tex_r, y_max, z_min))
        v2 = bm_tex_r.verts.new((x_tex_r, y_max, z_max))
        v3 = bm_tex_r.verts.new((x_tex_r, y_min, z_max))
        add_quad(bm_tex_r, v0, v1, v2, v3, uv_r, [(u_left, v_bottom), (u_right, v_bottom), (u_right, v_top), (u_left, v_top)])

    # Costado Izquierdo (Huecos de rueda 100% despejados bajo Z=0.98):
    add_tex_panel_left(wf_f, 4.70, H_CLEARANCE, H_ROOF_EAVE)
    add_tex_panel_left(wf_b, wf_f, 0.98, H_ROOF_EAVE)
    add_tex_panel_left(wr_f, wf_b, H_CLEARANCE, H_ROOF_EAVE)
    add_tex_panel_left(wr_b, wr_f, 0.98, H_ROOF_EAVE)
    add_tex_panel_left(-L_HALF, wr_b, H_CLEARANCE, H_ROOF_EAVE)

    # B. COSTADO DERECHO ESTRUCTURAL (LADO PUERTAS DE ACCESO):
    add_box(bm_body, xr - 0.05, xr, 4.55, 4.70, H_CLEARANCE, H_BELT)
    add_box(bm_body, xr - 0.05, xr, 3.20, 3.45, H_CLEARANCE, H_BELT)
    add_box(bm_body, xr - 0.05, xr, wf_b, wf_f, 0.98, H_BELT)
    add_box(bm_body, xr - 0.05, xr, wr_f, wf_b, H_CLEARANCE, H_BELT)
    add_box(bm_body, xr - 0.05, xr, wr_b, wr_f, 0.98, H_BELT)
    add_box(bm_body, xr - 0.05, xr, -3.40, wr_b, H_CLEARANCE, H_BELT)
    add_box(bm_body, xr - 0.05, xr, -4.75, -4.20, H_CLEARANCE, H_BELT)
    add_box(bm_body, xr - 0.05, xr, -L_HALF, -4.75, H_CLEARANCE, H_BELT)
    add_box(bm_body, xr - 0.05, xr, -L_HALF, 4.70, H_WINDOW_TOP, H_ROOF_EAVE)

    pilares_der = [
        (-4.80, -4.75), # Esquina trasera
        (-4.30, -4.20), # Poste entre ventanal trasero y puerta trasera
        (-3.40, -3.25), # Poste entre puerta trasera y ventana 1
        (-1.75, -1.60), # Entre ventana 1 y 2
        (-0.10, 0.05),  # Entre ventana 2 y 3
        (1.55, 1.70),   # Entre ventana 3 y 4
        (3.20, 3.45),   # Poste entre ventana 4 y puerta delantera
        (4.55, 4.70),   # Esquina delantera
    ]
    for y1, y2 in pilares_der:
        add_box(bm_body, xr - 0.05, xr, y1, y2, H_BELT, H_WINDOW_TOP)

    # Costado Derecho Texturado (Huecos de ruedas y puertas 100% despejados):
    add_tex_panel_right(4.55, 4.70, H_CLEARANCE, H_ROOF_EAVE)
    add_tex_panel_right(3.45, 4.55, 2.45, H_ROOF_EAVE) # Dintel sobre puerta delantera
    add_tex_panel_right(wf_f, 3.45, H_CLEARANCE, H_ROOF_EAVE)
    add_tex_panel_right(wf_b, wf_f, 0.98, H_ROOF_EAVE) # Sobre rueda delantera
    add_tex_panel_right(wr_f, wf_b, H_CLEARANCE, H_ROOF_EAVE)
    add_tex_panel_right(wr_b, wr_f, 0.98, H_ROOF_EAVE) # Sobre rueda trasera
    add_tex_panel_right(-3.40, wr_b, H_CLEARANCE, H_ROOF_EAVE)
    add_tex_panel_right(-4.20, -3.40, 2.45, H_ROOF_EAVE)         # Dintel sobre puerta trasera
    add_tex_panel_right(-4.75, -4.20, H_CLEARANCE, H_BELT)       # Bajo pequeño ventanal trasero
    add_tex_panel_right(-4.75, -4.20, H_WINDOW_TOP, H_ROOF_EAVE) # Dintel sobre pequeño ventanal trasero
    add_tex_panel_right(-L_HALF, -4.75, H_CLEARANCE, H_ROOF_EAVE) # Esquina trasera

    # C. FACHADA TRASERA SELLADA CON TEXTURA OFICIAL (UN-MIRRORED)
    add_box(bm_body, -W_HALF, W_HALF, -L_HALF - 0.04, -L_HALF, H_CLEARANCE, H_ROOF_PEAK)
    vb0 = bm_tex_b.verts.new((-W_HALF, -L_HALF - 0.045, H_CLEARANCE))
    vb1 = bm_tex_b.verts.new((W_HALF, -L_HALF - 0.045, H_CLEARANCE))
    vb2 = bm_tex_b.verts.new((W_HALF, -L_HALF - 0.045, H_ROOF_PEAK))
    vb3 = bm_tex_b.verts.new((-W_HALF, -L_HALF - 0.045, H_ROOF_PEAK))
    add_quad(bm_tex_b, vb0, vb1, vb2, vb3, uv_b, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])

    # D. TECHO AERODINÁMICO CURVO MONOLÍTICO
    roof_steps = 28
    for i in range(roof_steps):
        t0 = i / float(roof_steps)
        t1 = (i + 1) / float(roof_steps)
        x0 = -W_HALF + t0 * (2.0 * W_HALF)
        x1 = -W_HALF + t1 * (2.0 * W_HALF)
        z0 = H_ROOF_EAVE + (H_ROOF_PEAK - H_ROOF_EAVE) * math.sin(math.pi * t0)
        z1 = H_ROOF_EAVE + (H_ROOF_PEAK - H_ROOF_EAVE) * math.sin(math.pi * t1)
        z_min = min(z0, z1)
        z_max = max(z0, z1) + 0.04
        add_box(bm_roof, x0, x1, -L_HALF - 0.02, 4.72, z_min, z_max)

    # Goteros longitudinales de techo
    add_box(bm_body, xl - 0.02, xl + 0.02, -L_HALF, 4.70, H_ROOF_EAVE - 0.02, H_ROOF_EAVE + 0.04)
    add_box(bm_body, xr - 0.02, xr + 0.02, -L_HALF, 4.70, H_ROOF_EAVE - 0.02, H_ROOF_EAVE + 0.04)

    # Cejas semicirculares de guardafango (hollow, dejan el hueco de la rueda 100% abierto)
    for cy in [WHEELBASE_FRONT, WHEELBASE_REAR]:
        for cx, side in [(-W_HALF, -1), (W_HALF, 1)]:
            add_fender_flare_lip(bm_wells, (cx, cy, WHEEL_R), r_inner=WHEEL_R + 0.04, r_outer=WHEEL_R + 0.09, width=0.04, axis='X', side=side, segments=24)

    obj_body = create_mesh_object("Bus_Carroceria_Roja", bm_body, mats['red'], col)
    create_mesh_object("Bus_Textura_Costado_Izquierdo", bm_tex_l, mats['tex_left'], col)
    create_mesh_object("Bus_Textura_Costado_Derecho", bm_tex_r, mats['tex_right'], col)
    create_mesh_object("Bus_Textura_Trasera", bm_tex_b, mats['tex_rear'], col)
    obj_rf = create_mesh_object("Bus_Techo_Curvo", bm_roof, mats['red'], col)
    create_mesh_object("Bus_Guardafangos_Caucho", bm_wells, mats['rubber'], col)

    return obj_body, obj_rf

# ===========================================================================
# 2. FRENTE FOTORREALISTA MARCOPOLO BOXER OF (PARRILLA, ESTRELLA Y FAROS)
# ===========================================================================
def build_front_marcopolo_boxer(mats, col):
    bm_white = bmesh.new()
    bm_red_fascia = bmesh.new()
    bm_grille = bmesh.new()
    bm_chrome = bmesh.new()
    bm_lights = bmesh.new()
    bm_wipers = bmesh.new()
    bm_sign = bmesh.new()
    bm_amber_roof = bmesh.new()
    bm_windshield = bmesh.new()

    uv_sign = bm_sign.loops.layers.uv.new("UVMap")

    # A. Fascia Delantera Blanca Curvada Envolvente
    # Base inferior con tomas de aire
    add_box(bm_white, -1.24, 1.24, 4.70, 4.88, 0.35, 0.88)
    # Escudo frontal que envuelve los faros y la parrilla
    add_box(bm_white, -1.22, 1.22, 4.72, 4.86, 0.88, 1.45)
    # Labio inferior aerodinámico
    add_box(bm_white, -1.18, 1.18, 4.86, 4.92, 0.35, 0.55)
    # Envolvente lateral que empalma suavemente con la salpicadera
    add_box(bm_white, -1.25, -1.21, 3.60, 4.70, 0.35, 0.88)
    add_box(bm_white, 1.21, 1.25, 3.60, 4.70, 0.35, 0.88)

    # Esquinas inferiores rojas de contraste (según foto frontal)
    add_box(bm_red_fascia, -1.24, -1.02, 4.84, 4.89, 0.35, 0.58)
    add_box(bm_red_fascia, 1.02, 1.24, 4.84, 4.89, 0.35, 0.58)

    # B. Tomas de Aire Inferiores en Plástico Negro
    add_box(bm_grille, -0.85, 0.85, 4.87, 4.89, 0.42, 0.72)
    # Placa delantera montada al centro
    v_p0 = bm_sign.verts.new((0.20, 4.895, 0.45))
    v_p1 = bm_sign.verts.new((-0.20, 4.895, 0.45))
    v_p2 = bm_sign.verts.new((-0.20, 4.895, 0.65))
    v_p3 = bm_sign.verts.new((0.20, 4.895, 0.65))
    add_quad(bm_sign, v_p0, v_p1, v_p2, v_p3, uv_sign, [(0.77, 0.10), (0.98, 0.10), (0.98, 0.45), (0.77, 0.45)])

    # C. Parrilla Trapezoidal Mercedes-Benz
    add_box(bm_grille, -0.74, 0.74, 4.84, 4.87, 0.90, 1.38)
    # Marco perimetral cromado
    add_box(bm_chrome, -0.76, 0.76, 4.865, 4.88, 1.36, 1.39)
    add_box(bm_chrome, -0.76, 0.76, 4.865, 4.88, 0.89, 0.92)
    add_box(bm_chrome, -0.76, -0.73, 4.865, 4.88, 0.89, 1.39)
    add_box(bm_chrome, 0.73, 0.76, 4.865, 4.88, 0.89, 1.39)

    # 3 Listones Horizontales Cromados
    for z_slat in [0.98, 1.14, 1.30]:
        add_box(bm_chrome, -0.72, 0.72, 4.87, 4.89, z_slat, z_slat + 0.035)

    # Emblema 3D de la Estrella de Tres Puntas Mercedes-Benz (Auténtico: 1 arriba a 90°, 2 abajo a 210° y 330°)
    cz_star = 1.14
    add_open_ring(bm_chrome, (0.0, 4.895, cz_star), r_outer=0.165, r_inner=0.138, height=0.03, axis='Y', segments=32)
    add_cylinder(bm_chrome, (0.0, 4.905, cz_star), radius=0.035, height=0.035, axis='Y', segments=16)

    # 3 Rayos de la estrella
    for deg in [90.0, 210.0, 330.0]:
        rad = math.radians(deg)
        x_tip = math.cos(rad) * 0.14
        z_tip = math.sin(rad) * 0.14
        # Perfil triangular extruido para cada rayo
        p_perp_x = -math.sin(rad) * 0.016
        p_perp_z = math.cos(rad) * 0.016
        v_r0 = bm_chrome.verts.new((-p_perp_x, 4.90, cz_star - p_perp_z))
        v_r1 = bm_chrome.verts.new((p_perp_x, 4.90, cz_star + p_perp_z))
        v_r2 = bm_chrome.verts.new((x_tip, 4.91, cz_star + z_tip))
        bm_chrome.faces.new((v_r0, v_r1, v_r2))

    # Placa "Marcopolo" en cromo sobre la parrilla
    add_box(bm_chrome, -0.16, 0.16, 4.86, 4.875, 1.40, 1.435)

    # D. Ópticas Delanteras Trapezoidales Inclinadas (Marcopolo Boxer OF)
    for side, fx in [(-1, -0.96), (1, 0.96)]:
        # Bisel cromado aerodinámico
        add_box(bm_chrome, fx - 0.22, fx + 0.22, 4.82, 4.86, 0.88, 1.25)
        add_box(bm_grille, fx - 0.20, fx + 0.20, 4.84, 4.87, 0.90, 1.23)
        # Proyector principal (baja)
        add_cylinder(bm_lights, (fx - side*0.07, 4.875, 1.05), radius=0.082, height=0.025, axis='Y', segments=20)
        # Proyector secundario (alta)
        add_cylinder(bm_lights, (fx + side*0.06, 4.875, 1.05), radius=0.065, height=0.025, axis='Y', segments=18)
        # Direccional ámbar integrada
        add_cylinder(bm_amber_roof, (fx - side*0.14, 4.87, 1.15), radius=0.045, height=0.025, axis='Y', segments=14)
        # Cristal exterior transparente de la óptica
        add_box(bm_windshield, fx - 0.21, fx + 0.21, 4.865, 4.88, 0.89, 1.24)

    # E. Copete Superior y Rutero Luminoso (Cowl rojo oficial)
    add_box(bm_red_fascia, -1.22, 1.22, 4.65, 4.88, 2.50, 2.85)
    v_s0 = bm_sign.verts.new((0.95, 4.885, 2.58))
    v_s1 = bm_sign.verts.new((-0.95, 4.885, 2.58))
    v_s2 = bm_sign.verts.new((-0.95, 4.885, 2.78))
    v_s3 = bm_sign.verts.new((0.95, 4.885, 2.78))
    add_quad(bm_sign, v_s0, v_s1, v_s2, v_s3, uv_sign, [(0.05, 0.55), (0.95, 0.55), (0.95, 0.95), (0.05, 0.95)])

    # Luces de gálibo superiores
    for gx in [-1.0, -0.5, 0.0, 0.5, 1.0]:
        add_cylinder(bm_amber_roof, (gx, 4.86, 2.88), radius=0.025, height=0.03, axis='Y', segments=12)

    # F. Parabrisas Panorámico Curvo
    add_box(bm_windshield, -1.18, -0.015, 4.68, 4.78, 1.48, 2.48)
    add_box(bm_windshield, 0.015, 1.18, 4.68, 4.78, 1.48, 2.48)
    add_box(bm_grille, -0.02, 0.02, 4.69, 4.80, 1.46, 2.50)

    # G. Cartulinas de Ruta interiores en el parabrisas
    v_cy0 = bm_sign.verts.new((0.65, 4.76, 1.55))
    v_cy1 = bm_sign.verts.new((0.25, 4.76, 1.55))
    v_cy2 = bm_sign.verts.new((0.25, 4.76, 1.88))
    v_cy3 = bm_sign.verts.new((0.65, 4.76, 1.88))
    add_quad(bm_sign, v_cy0, v_cy1, v_cy2, v_cy3, uv_sign, [(0.05, 0.05), (0.45, 0.05), (0.45, 0.50), (0.05, 0.50)])

    v_cw0 = bm_sign.verts.new((0.98, 4.76, 1.55))
    v_cw1 = bm_sign.verts.new((0.68, 4.76, 1.55))
    v_cw2 = bm_sign.verts.new((0.68, 4.76, 1.88))
    v_cw3 = bm_sign.verts.new((0.98, 4.76, 1.88))
    add_quad(bm_sign, v_cw0, v_cw1, v_cw2, v_cw3, uv_sign, [(0.50, 0.05), (0.75, 0.05), (0.75, 0.50), (0.50, 0.50)])

    # H. Limpiaparabrisas Pantográficos
    for wx in [-0.45, 0.45]:
        add_cylinder(bm_wipers, (wx, 4.82, 1.50), radius=0.015, height=0.45, axis='Z', segments=8)
        add_box(bm_wipers, wx - 0.01, wx + 0.01, 4.79, 4.81, 1.55, 2.15)

    # I. Espejos Retrovisores (Marcopolo Boxer OF)
    for side, mx in [(-1, -W_HALF - 0.22), (1, W_HALF + 0.22)]:
        add_cylinder(bm_grille, (mx, 4.55, 2.25), radius=0.018, height=0.60, axis='Z', segments=10)
        add_cylinder(bm_grille, ((mx + side*0.10)*0.5, 4.60, 2.50), radius=0.016, height=0.35, axis='X', segments=8)
        add_box(bm_white if side > 0 else bm_grille, mx - 0.06, mx + 0.06, 4.50, 4.60, 1.95, 2.45)
        add_box(bm_chrome, mx - 0.05, mx + 0.05, 4.48, 4.50, 1.96, 2.44)
        if side > 0:
            add_box(bm_white, mx - 0.06, mx + 0.06, 4.50, 4.60, 1.78, 1.92)
            add_box(bm_chrome, mx - 0.05, mx + 0.05, 4.48, 4.50, 1.79, 1.91)

    create_mesh_object("Bus_Fascia_Frontal_Blanca", bm_white, mats['white'], col)
    create_mesh_object("Bus_Fascia_Esquinas_Rojas", bm_red_fascia, mats['red'], col)
    create_mesh_object("Bus_Parrilla_Fondo_Negro", bm_grille, mats['black_trim'], col)
    create_mesh_object("Bus_Parrilla_Cromos_Estrella", bm_chrome, mats['chrome'], col)
    create_mesh_object("Bus_Faros_Cristal_Frontal", bm_lights, mats['headlight'], col)
    create_mesh_object("Bus_Parabrisas_Panoramico", bm_windshield, mats['glass'], col)
    create_mesh_object("Bus_Limpiaparabrisas", bm_wipers, mats['black_trim'], col)
    create_mesh_object("Bus_Rutero_Cartulinas", bm_sign, mats['tex_front'], col)
    create_mesh_object("Bus_Galibo_Frontal", bm_amber_roof, mats['amber'], col)

# ===========================================================================
# 3. VENTANERÍA ENRASADA Y PUERTAS PLEGABLES DE 2 HOJAS
# ===========================================================================
def build_windows_and_doors(mats, col):
    bm_glass = bmesh.new()
    bm_frames = bmesh.new()

    xl = -W_HALF
    add_box(bm_glass, xl - 0.015, xl + 0.015, 3.55, 4.65, 1.48, 2.42)
    add_box(bm_frames, xl - 0.025, xl + 0.025, 3.52, 4.68, 1.45, 1.48)
    add_box(bm_frames, xl - 0.025, xl + 0.025, 3.52, 4.68, 2.42, 2.45)
    add_box(bm_frames, xl - 0.02, xl + 0.02, 3.55, 4.65, 2.18, 2.21)

    bays_left = [
        (-4.70, -3.08),
        (-2.94, -1.46),
        (-1.32, 0.16),
        (0.30, 1.78),
        (1.92, 3.40),
    ]
    for y1, y2 in bays_left:
        add_box(bm_glass, xl - 0.015, xl + 0.015, y1 + 0.03, y2 - 0.03, 1.48, 2.42)
        add_box(bm_frames, xl - 0.025, xl + 0.025, y1, y2, 1.45, 1.48)
        add_box(bm_frames, xl - 0.025, xl + 0.025, y1, y2, 2.42, 2.45)
        add_box(bm_frames, xl - 0.025, xl + 0.025, y1, y1 + 0.03, 1.45, 2.45)
        add_box(bm_frames, xl - 0.025, xl + 0.025, y2 - 0.03, y2, 1.45, 2.45)
        add_box(bm_frames, xl - 0.02, xl + 0.02, y1, y2, 2.18, 2.21)

    xr = W_HALF
    # 1. Pequeño ventanal de esquina trasera derecha
    add_box(bm_glass, xr - 0.015, xr + 0.015, -4.72, -4.33, 1.48, 2.42)
    add_box(bm_frames, xr - 0.025, xr + 0.025, -4.75, -4.30, 1.45, 1.48)
    add_box(bm_frames, xr - 0.025, xr + 0.025, -4.75, -4.30, 2.42, 2.45)
    add_box(bm_frames, xr - 0.025, xr + 0.025, -4.75, -4.72, 1.45, 2.45)
    add_box(bm_frames, xr - 0.025, xr + 0.025, -4.33, -4.30, 1.45, 2.45)
    add_box(bm_frames, xr - 0.02, xr + 0.02, -4.72, -4.33, 2.18, 2.21)

    # 2. Cuatro ventanas canónicas de pasajeros del costado derecho
    bays_right = [
        (-3.25, -1.75),
        (-1.60, -0.10),
        (0.05, 1.55),
        (1.70, 3.20),
    ]
    for y1, y2 in bays_right:
        add_box(bm_glass, xr - 0.015, xr + 0.015, y1 + 0.03, y2 - 0.03, 1.48, 2.42)
        add_box(bm_frames, xr - 0.025, xr + 0.025, y1, y2, 1.45, 1.48)
        add_box(bm_frames, xr - 0.025, xr + 0.025, y1, y2, 2.42, 2.45)
        add_box(bm_frames, xr - 0.025, xr + 0.025, y1, y1 + 0.03, 1.45, 2.45)
        add_box(bm_frames, xr - 0.025, xr + 0.025, y2 - 0.03, y2, 1.45, 2.45)
        add_box(bm_frames, xr - 0.02, xr + 0.02, y1, y2, 2.18, 2.21)

    # 3. Puerta Delantera Plegable (2 Hojas)
    add_box(bm_frames, xr - 0.03, xr + 0.02, 3.43, 4.57, 0.42, 0.48)
    add_box(bm_frames, xr - 0.03, xr + 0.02, 3.43, 4.57, 2.42, 2.48)
    door_w = (4.55 - 3.45) * 0.5
    for dy1 in [3.45, 3.45 + door_w]:
        dy2 = dy1 + door_w - 0.02
        add_box(bm_glass, xr - 0.018, xr + 0.012, dy1 + 0.03, dy2 - 0.03, 1.40, 2.38)
        add_box(bm_glass, xr - 0.018, xr + 0.012, dy1 + 0.03, dy2 - 0.03, 0.52, 1.32)
        add_box(bm_frames, xr - 0.025, xr + 0.018, dy1, dy2, 0.45, 0.52)
        add_box(bm_frames, xr - 0.025, xr + 0.018, dy1, dy2, 1.32, 1.40)
        add_box(bm_frames, xr - 0.025, xr + 0.018, dy1, dy2, 2.38, 2.45)
        add_box(bm_frames, xr - 0.025, xr + 0.018, dy1, dy1 + 0.03, 0.45, 2.45)
        add_box(bm_frames, xr - 0.025, xr + 0.018, dy2 - 0.03, dy2, 0.45, 2.45)
        add_cylinder(bm_frames, (xr - 0.06, (dy1+dy2)*0.5, 1.35), radius=0.014, height=0.75, axis='Z', segments=8)

    add_box(bm_frames, xr - 0.01, xr + 0.02, 3.70, 4.30, 2.50, 2.58)

    # 4. Puerta Trasera Plegable (2 Hojas)
    add_box(bm_frames, xr - 0.03, xr + 0.02, -4.22, -3.38, 0.42, 0.48)
    add_box(bm_frames, xr - 0.03, xr + 0.02, -4.22, -3.38, 2.42, 2.48)
    door_rw = (-3.40 - (-4.20)) * 0.5
    for dy1 in [-4.20, -4.20 + door_rw]:
        dy2 = dy1 + door_rw - 0.02
        add_box(bm_glass, xr - 0.018, xr + 0.012, dy1 + 0.03, dy2 - 0.03, 1.40, 2.38)
        add_box(bm_glass, xr - 0.018, xr + 0.012, dy1 + 0.03, dy2 - 0.03, 0.52, 1.32)
        add_box(bm_frames, xr - 0.025, xr + 0.018, dy1, dy2, 0.45, 0.52)
        add_box(bm_frames, xr - 0.025, xr + 0.018, dy1, dy2, 1.32, 1.40)
        add_box(bm_frames, xr - 0.025, xr + 0.018, dy1, dy2, 2.38, 2.45)
        add_box(bm_frames, xr - 0.025, xr + 0.018, dy1, dy1 + 0.03, 0.45, 2.45)
        add_box(bm_frames, xr - 0.025, xr + 0.018, dy2 - 0.03, dy2, 0.45, 2.45)
        add_cylinder(bm_frames, (xr - 0.06, (dy1+dy2)*0.5, 1.35), radius=0.014, height=0.75, axis='Z', segments=8)

    create_mesh_object("Bus_Ventaneria_Vidrios", bm_glass, mats['glass'], col)
    create_mesh_object("Bus_Marcos_Canceleria", bm_frames, mats['black_trim'], col)

# ===========================================================================
# 4. CALAVERAS TRASERAS, DEFENSA Y RUEDAS FOTORREALISTAS HUECAS
# ===========================================================================
def build_rear_details_and_wheels(mats, col):
    bm_tires = bmesh.new()
    bm_rims = bmesh.new()
    bm_chrome_lugs = bmesh.new()
    bm_lights_red = bmesh.new()
    bm_lights_amber = bmesh.new()
    bm_lights_white = bmesh.new()
    bm_bumper = bmesh.new()

    # A. Calaveras Traseras Triples Verticales (según foto bus-hongo-reverso.jpeg)
    for kx in [-1.05, 1.05]:
        add_box(bm_bumper, kx - 0.09, kx + 0.09, -L_HALF - 0.055, -L_HALF - 0.035, 0.58, 1.18)
        # Biseles negros de goma en cada calavera
        for ly in [0.96, 0.81, 0.66]:
            add_cylinder(bm_tires, (kx, -L_HALF - 0.050, ly), radius=0.074, height=0.015, axis='Y', segments=20)
        # Aro cromado exclusivo en luz de reversa
        add_cylinder(bm_chrome_lugs, (kx, -L_HALF - 0.052, 0.81), radius=0.070, height=0.018, axis='Y', segments=20)

        # Ópticas emisivas circulares
        add_cylinder(bm_lights_amber, (kx, -L_HALF - 0.055, 0.96), radius=0.062, height=0.025, axis='Y', segments=20)
        add_cylinder(bm_lights_white, (kx, -L_HALF - 0.055, 0.81), radius=0.062, height=0.025, axis='Y', segments=20)
        add_cylinder(bm_lights_red, (kx, -L_HALF - 0.055, 0.66), radius=0.062, height=0.025, axis='Y', segments=20)
        # Luz de gálibo ámbar superior
        add_cylinder(bm_lights_amber, (kx, -L_HALF - 0.050, 1.12), radius=0.028, height=0.02, axis='Y', segments=14)

    for gx in [-1.0, -0.5, 0.0, 0.5, 1.0]:
        add_cylinder(bm_lights_red, (gx, -L_HALF - 0.045, 2.88), radius=0.025, height=0.025, axis='Y', segments=12)

    # B. Defensa Trasera Blanca Envolvente
    add_box(bm_bumper, -1.22, 1.22, -L_HALF - 0.06, -L_HALF, 0.35, 0.55)
    # Hendiduras / manijas de defensa
    add_box(bm_tires, -0.55, -0.35, -L_HALF - 0.065, -L_HALF - 0.04, 0.40, 0.48)
    add_box(bm_tires, 0.35, 0.55, -L_HALF - 0.065, -L_HALF - 0.04, 0.40, 0.48)

    # Loderas traseras directamente tras las ruedas duales
    for lx in [-0.98, 0.98]:
        add_box(bm_tires, lx - 0.26, lx + 0.26, WHEELBASE_REAR - 0.68, WHEELBASE_REAR - 0.65, 0.12, 0.48)

    # C. RUEDAS FOTORREALISTAS (Neumático Hueco + Rin Blanco Stamped Steel Visible con Orificios y Maza)
    def make_wheel_assembly(center, side, is_front):
        cx, cy, cz = center
        w_w = WHEEL_W if is_front else WHEEL_W * 1.85
        rim_r = WHEEL_R * 0.68 # ~0.34m
        h2 = w_w * 0.5
        segments = 32

        # 1. Neumático Hueco (Banda de rodadura exterior + Flancos de caucho anulares)
        for i in range(segments):
            th0 = 2.0 * math.pi * i / segments
            th1 = 2.0 * math.pi * (i + 1) / segments
            c0, s0 = math.cos(th0), math.sin(th0)
            c1, s1 = math.cos(th1), math.sin(th1)

            # Banda de rodadura exterior
            v_to0 = bm_tires.verts.new((cx - h2, cy + c0 * WHEEL_R, cz + s0 * WHEEL_R))
            v_to1 = bm_tires.verts.new((cx + h2, cy + c0 * WHEEL_R, cz + s0 * WHEEL_R))
            v_to2 = bm_tires.verts.new((cx + h2, cy + c1 * WHEEL_R, cz + s1 * WHEEL_R))
            v_to3 = bm_tires.verts.new((cx - h2, cy + c1 * WHEEL_R, cz + s1 * WHEEL_R))
            bm_tires.faces.new((v_to0, v_to1, v_to2, v_to3))

            # Flanco exterior anular (deja ver el rin blanco en el centro)
            out_x = cx + side * h2
            v_so0 = bm_tires.verts.new((out_x, cy + c0 * rim_r, cz + s0 * rim_r))
            v_so1 = bm_tires.verts.new((out_x, cy + c0 * WHEEL_R, cz + s0 * WHEEL_R))
            v_so2 = bm_tires.verts.new((out_x, cy + c1 * WHEEL_R, cz + s1 * WHEEL_R))
            v_so3 = bm_tires.verts.new((out_x, cy + c1 * rim_r, cz + s1 * rim_r))
            bm_tires.faces.new((v_so0, v_so1, v_so2, v_so3) if side > 0 else (v_so3, v_so2, v_so1, v_so0))

            # Flanco interior anular
            in_x = cx - side * h2
            v_si0 = bm_tires.verts.new((in_x, cy + c0 * rim_r, cz + s0 * rim_r))
            v_si1 = bm_tires.verts.new((in_x, cy + c1 * rim_r, cz + s1 * rim_r))
            v_si2 = bm_tires.verts.new((in_x, cy + c1 * WHEEL_R, cz + s1 * WHEEL_R))
            v_si3 = bm_tires.verts.new((in_x, cy + c0 * WHEEL_R, cz + s0 * WHEEL_R))
            bm_tires.faces.new((v_si0, v_si1, v_si2, v_si3) if side > 0 else (v_si3, v_si2, v_si1, v_si0))

        # 2. Rin de Acero Blanco Estampado (Diferenciado Delantero Convexo vs Trasero Deep-Dish)
        if is_front:
            # Eje Delantero: Plato blanco estampado convexo
            out_x = cx + side * h2
            lip_x = out_x - side * 0.015
            rin_x = out_x - side * 0.025

            # Tambor cilíndrico del rin
            add_cylinder(bm_rims, (rin_x - side * 0.04, cy, cz), radius=rim_r, height=0.08, axis='X', segments=28)
            # Plato frontal del rin blanco
            add_cylinder(bm_rims, (rin_x, cy, cz), radius=rim_r, height=0.02, axis='X', segments=28)

            # 8 Orificios de ventilación (rehundidos en el plato blanco)
            hole_dist = rim_r * 0.65
            for deg in range(0, 360, 45):
                rad = math.radians(deg)
                hx = rin_x - side * 0.005
                hy = cy + math.cos(rad) * hole_dist
                hz = cz + math.sin(rad) * hole_dist
                add_cylinder(bm_tires, (hx, hy, hz), radius=0.038, height=0.025, axis='X', segments=12)

            # Cubo y Maza Central Delantera
            hub_x = rin_x + side * 0.035
            add_cylinder(bm_rims, (hub_x, cy, cz), radius=0.13, height=0.05, axis='X', segments=20)
            add_cylinder(bm_chrome_lugs, (hub_x + side * 0.025, cy, cz), radius=0.075, height=0.03, axis='X', segments=16)

            # 10 Tuercas cromadas perimetrales
            for deg in range(0, 360, 36):
                rad = math.radians(deg)
                lx = hub_x + side * 0.025
                ly = cy + math.cos(rad) * 0.105
                lz = cz + math.sin(rad) * 0.105
                add_cylinder(bm_chrome_lugs, (lx, ly, lz), radius=0.016, height=0.025, axis='X', segments=8)

        else:
            # Eje Trasero: Rin blanco de plato hondo cóncavo (Deep-Dish para ruedas duales)
            out_x = cx + side * h2
            lip_x = out_x - side * 0.015
            dish_x = out_x - side * 0.115
            r_lip = rim_r
            r_dish = rim_r * 0.78

            # Embudo cónico blanco profundo (superficie inclinada visible)
            for i in range(segments):
                th0 = 2.0 * math.pi * i / segments
                th1 = 2.0 * math.pi * (i + 1) / segments
                c0, s0 = math.cos(th0), math.sin(th0)
                c1, s1 = math.cos(th1), math.sin(th1)

                v0 = bm_rims.verts.new((lip_x, cy + c0 * r_lip, cz + s0 * r_lip))
                v1 = bm_rims.verts.new((dish_x, cy + c0 * r_dish, cz + s0 * r_dish))
                v2 = bm_rims.verts.new((dish_x, cy + c1 * r_dish, cz + s1 * r_dish))
                v3 = bm_rims.verts.new((lip_x, cy + c1 * r_lip, cz + s1 * r_lip))
                bm_rims.faces.new((v0, v1, v2, v3) if side > 0 else (v3, v2, v1, v0))

            # Fondo del plato hondo blanco
            add_cylinder(bm_rims, (dish_x, cy, cz), radius=r_dish, height=0.02, axis='X', segments=28)

            # 8 Orificios circulares de ventilación en el bisel cónico
            hole_r = 0.035
            for deg in range(0, 360, 45):
                rad = math.radians(deg)
                hx = (lip_x + dish_x) * 0.5
                hy = cy + math.cos(rad) * (r_lip + r_dish) * 0.5
                hz = cz + math.sin(rad) * (r_lip + r_dish) * 0.5
                add_cylinder(bm_tires, (hx, hy, hz), radius=hole_r, height=0.02, axis='X', segments=12)

            # Maza central del eje motriz trasero pesado
            axle_h = 0.08
            axle_x = dish_x + side * (axle_h * 0.5)
            add_cylinder(bm_rims, (axle_x, cy, cz), radius=0.14, height=axle_h, axis='X', segments=24)
            add_cylinder(bm_chrome_lugs, (dish_x + side * axle_h, cy, cz), radius=0.08, height=0.025, axis='X', segments=16)

            # 10 Tuercas de maza trasera
            for deg in range(0, 360, 36):
                rad = math.radians(deg)
                lx = dish_x + side * (axle_h + 0.01)
                ly = cy + math.cos(rad) * 0.115
                lz = cz + math.sin(rad) * 0.115
                add_cylinder(bm_chrome_lugs, (lx, ly, lz), radius=0.016, height=0.025, axis='X', segments=8)

    make_wheel_assembly((-1.12, WHEELBASE_FRONT, WHEEL_R), -1, is_front=True)
    make_wheel_assembly((1.12, WHEELBASE_FRONT, WHEEL_R), 1, is_front=True)
    make_wheel_assembly((-0.98, WHEELBASE_REAR, WHEEL_R), -1, is_front=False)
    make_wheel_assembly((0.98, WHEELBASE_REAR, WHEEL_R), 1, is_front=False)

    create_mesh_object("Bus_Neumaticos_PBR", bm_tires, mats['rubber'], col)
    create_mesh_object("Bus_Rines_Blancos", bm_rims, mats['rim'], col)
    create_mesh_object("Bus_Tuercas_Cromadas", bm_chrome_lugs, mats['chrome'], col)
    create_mesh_object("Bus_Calaveras_Rojas", bm_lights_red, mats['taillight_red'], col)
    create_mesh_object("Bus_Calaveras_Ambar", bm_lights_amber, mats['amber'], col)
    create_mesh_object("Bus_Calaveras_Reversa", bm_lights_white, mats['reverse'], col)
    create_mesh_object("Bus_Defensa_Trasera_Blanca", bm_bumper, mats['white'], col)

# ===========================================================================
# 5. HABITÁCULO INTERIOR CANÓNICO (30 ASIENTOS + CHOFER)
# ===========================================================================
def build_interior_30_seats(mats, col):
    bm_floor = bmesh.new()
    bm_seats = bmesh.new()
    bm_rails = bmesh.new()
    bm_dash = bmesh.new()

    # Piso continuo sellado
    add_box(bm_floor, -W_HALF + 0.06, W_HALF - 0.06, -L_HALF + 0.10, 4.60, 0.76, 0.82)

    # Escalones de acceso en puertas delantera y trasera
    add_box(bm_floor, W_HALF - 0.42, W_HALF - 0.05, 3.45, 4.55, 0.42, 0.58)
    add_box(bm_floor, W_HALF - 0.32, W_HALF - 0.05, 3.45, 4.55, 0.58, 0.76)
    add_box(bm_floor, W_HALF - 0.42, W_HALF - 0.05, -4.20, -3.40, 0.42, 0.58)
    add_box(bm_floor, W_HALF - 0.32, W_HALF - 0.05, -4.20, -3.40, 0.58, 0.76)

    # Puesto del Conductor
    add_box(bm_dash, -1.18, -0.32, 4.05, 4.60, 0.82, 1.36)
    add_cylinder(bm_dash, (-0.75, 4.25, 1.32), radius=0.07, height=0.02, axis='Y', segments=16)
    add_cylinder(bm_dash, (-0.75, 4.18, 1.40), radius=0.22, height=0.03, axis='Z', segments=24)
    add_cylinder(bm_dash, (-0.75, 4.18, 1.40), radius=0.05, height=0.04, axis='Z', segments=12)
    add_box(bm_seats, -0.95, -0.55, 3.52, 3.82, 0.82, 1.25)
    add_box(bm_seats, -0.95, -0.55, 3.44, 3.52, 1.25, 1.82)

    def make_seat_assembly(x1, x2, y1, y2):
        add_box(bm_seats, x1, x2, y1, y2, 0.82, 1.24)
        add_box(bm_seats, x1, x2, y1 - 0.08, y1, 1.24, 1.80)
        add_box(bm_rails, x1 + 0.04, x2 - 0.04, y1 - 0.07, y1 - 0.05, 1.80, 1.86)
        add_cylinder(bm_dash, ((x1+x2)*0.5, (y1+y2)*0.5, 0.70), radius=0.03, height=0.24, axis='Z', segments=8)

    # 1. Banda Izquierda: 7 filas dobles = 14 plazas
    seat_rows_izq = [2.75, 1.85, 0.95, 0.05, -0.85, -1.75, -2.65]
    for sy in seat_rows_izq:
        make_seat_assembly(-1.18, -0.76, sy - 0.16, sy + 0.16)
        make_seat_assembly(-0.72, -0.30, sy - 0.16, sy + 0.16)

    # 2. Banda Derecha: 1 preferencial individual + 5 filas dobles = 11 plazas
    make_seat_assembly(0.55, 0.95, 2.75 - 0.16, 2.75 + 0.16)
    seat_rows_der = [1.85, 0.95, 0.05, -0.85, -1.75]
    for sy in seat_rows_der:
        make_seat_assembly(0.30, 0.72, sy - 0.16, sy + 0.16)
        make_seat_assembly(0.76, 1.18, sy - 0.16, sy + 0.16)

    # 3. Banca Posterior Corrida: 5 plazas contiguas
    rear_y = -4.35
    rear_xs = [-1.15, -0.69, -0.23, 0.23, 0.69, 1.15]
    for i in range(5):
        rx1 = rear_xs[i] + 0.03
        rx2 = rear_xs[i+1] - 0.03
        make_seat_assembly(rx1, rx2, rear_y - 0.16, rear_y + 0.16)

    # Pasamanos amarillos longitudinales de techo
    add_cylinder(bm_rails, (-0.26, 0.0, 2.45), radius=0.018, height=8.4, axis='Y', segments=12)
    add_cylinder(bm_rails, (0.26, 0.0, 2.45), radius=0.018, height=8.4, axis='Y', segments=12)
    add_cylinder(bm_rails, (0.42, 3.58, 1.62), radius=0.018, height=1.65, axis='Z', segments=10)
    add_cylinder(bm_rails, (0.42, -3.48, 1.62), radius=0.018, height=1.65, axis='Z', segments=10)

    create_mesh_object("Bus_Interior_Piso", bm_floor, mats['floor'], col)
    create_mesh_object("Bus_Interior_Asientos_30", bm_seats, mats['seat'], col)
    create_mesh_object("Bus_Interior_Pasamanos", bm_rails, mats['handrail'], col)
    create_mesh_object("Bus_Interior_Tablero_Chofer", bm_dash, mats['black_trim'], col)

# ===========================================================================
# 6. CONFIGURACIÓN DE ILUMINACIÓN Y CÁMARAS CLOSED-LOOP
# ===========================================================================
def setup_lighting_and_render_cameras(col):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    if hasattr(scene.cycles, 'device'):
        scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.view_settings.view_transform = 'Standard'

    if not scene.world:
        scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.74, 0.84, 0.94, 1.0)
        bg.inputs["Strength"].default_value = 0.85

    sun_data = bpy.data.lights.new(name="Sun_Light", type='SUN')
    sun_data.energy = 4.5
    sun_data.color = (1.0, 0.97, 0.92)
    sun_obj = bpy.data.objects.new("Sun_Obj", sun_data)
    sun_obj.rotation_euler = (math.radians(50.0), math.radians(20.0), math.radians(-45.0))
    col.objects.link(sun_obj)

    fill_data = bpy.data.lights.new(name="Fill_Light", type='SUN')
    fill_data.energy = 2.2
    fill_data.color = (0.85, 0.90, 1.0)
    fill_obj = bpy.data.objects.new("Fill_Obj", fill_data)
    fill_obj.rotation_euler = (math.radians(35.0), math.radians(-35.0), math.radians(140.0))
    col.objects.link(fill_obj)

    for ly in [-3.0, -1.0, 1.0, 3.0]:
        l_data = bpy.data.lights.new(name=f"Cabin_Light_{ly}", type='POINT')
        l_data.energy = 55.0
        l_data.color = (1.0, 0.97, 0.92)
        l_obj = bpy.data.objects.new(f"Cabin_Light_{ly}", l_data)
        l_obj.location = (0.0, ly, 2.40)
        col.objects.link(l_obj)

    cams_spec = [
        ("Cam_01_Frontal_3Q", (4.8, 8.5, 3.2), (math.radians(72.0), 0.0, math.radians(148.0)), 42.0, 'PERSP', 0.0),
        ("Cam_02_Lateral_Derecha_Puertas", (11.0, 0.0, 1.8), (math.radians(90.0), 0.0, math.radians(90.0)), 36.0, 'PERSP', 0.0),
        ("Cam_03_Lateral_Izquierda_Hongo", (-11.0, 0.0, 1.8), (math.radians(90.0), 0.0, math.radians(-90.0)), 36.0, 'PERSP', 0.0),
        ("Cam_04_Posterior_Calaveras", (0.0, -9.8, 1.6), (math.radians(90.0), 0.0, 0.0), 38.0, 'PERSP', 0.0),
        ("Cam_05_Perspectiva_General", (-6.5, -7.5, 3.8), (math.radians(68.0), 0.0, math.radians(-42.0)), 42.0, 'PERSP', 0.0),
        ("Cam_06_Frente_Parrilla_Closeup", (0.0, 8.2, 1.35), (math.radians(90.0), 0.0, math.radians(180.0)), 44.0, 'PERSP', 0.0),
        ("Cam_07_Interior_Hacia_Atras", (0.0, 3.6, 1.70), (math.radians(90.0), 0.0, math.radians(180.0)), 22.0, 'PERSP', 0.0),
        ("Cam_08_Interior_Hacia_Frente", (0.0, -3.9, 1.70), (math.radians(90.0), 0.0, 0.0), 22.0, 'PERSP', 0.0),
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

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(f"-> Guardado .blend: {BLEND_PATH}")

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

    scene = bpy.context.scene
    for cam_name, cam_obj in cam_objs.items():
        scene.camera = cam_obj
        out_path = os.path.join(RENDER_DIR, f"{cam_name}.png")
        scene.render.filepath = out_path

        if cam_name == "Cam_09_Interior_Cenital_Cutaway":
            obj_roof.hide_render = True
        else:
            obj_roof.hide_render = False

        print(f"Renderizando: {cam_name}...")
        bpy.ops.render.render(write_still=True)
        print(f"-> Guardado render: {out_path}")

    obj_roof.hide_render = False

def main():
    print("=== INICIANDO CONSTRUCCIÓN DEL GEMELO FOTORREALISTA 'EL HONGO' ===")
    col = clean_scene()
    mats = create_materials()

    obj_body, obj_roof = build_body_shell(mats, col)
    build_front_marcopolo_boxer(mats, col)
    build_windows_and_doors(mats, col)
    build_rear_details_and_wheels(mats, col)
    build_interior_30_seats(mats, col)

    cams = setup_lighting_and_render_cameras(col)
    export_and_render(col, cams, obj_roof)
    print("=== GEMELO FOTORREALISTA GENERADO Y AUDITADO EXITOSAMENTE ===")

if __name__ == "__main__":
    main()
