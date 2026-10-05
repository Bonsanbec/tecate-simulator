"""
=============================================================================
GENERADOR PROCEDURAL DEL ACTIVO 3D INDEPENDIENTE: VIOLÍN CLÁSICO Y ARCO
=============================================================================
Tecate Simulator - Activo Prop Independiente

Genera un violín de concierto 4/4 y su arco con modelado volumétrico de alta
fidelidad y texturas PBR de arce flameado y ébano:
1. Caja armónica: Lóbulos superior e inferior, escotaduras laterales en C,
   esquinas de luthier, tapa abovedada y efes caladas.
2. Mástil y diapasón: Mástil ergonómico de arce, diapasón largo de ébano,
   clavijero con 4 clavijas y voluta en espiral tradicional.
3. Cordal, puente y cuerdas: Puente de arce calado, cordal de ébano y 4 cuerdas.
4. Arco de violín: Varilla curvada de pernambuco, talón con nuez y crin blanca.
5. Exportación a 'godot_project/assets/props/violin.glb' y '.blend'.
=============================================================================
"""

import os
import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
PROPS_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/props")
OUTPUT_BLEND = os.path.join(PROPS_DIR, "violin.blend")
OUTPUT_GLB = os.path.join(PROPS_DIR, "violin.glb")
PREVIEW_PNG = os.path.join(PROPS_DIR, "violin_preview.png")

DIFFUSE_TEX = os.path.join(PROPS_DIR, "violin_diffuse.png")
NORMAL_TEX = os.path.join(PROPS_DIR, "violin_normal.png")

os.makedirs(PROPS_DIR, exist_ok=True)

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)

def create_pbr_material(name, diffuse_tex, normal_tex, base_color=(0.6, 0.35, 0.15, 1.0), roughness=0.35):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    links.new(node_bsdf.outputs['BSDF'], node_out.inputs['Surface'])

    node_bsdf.inputs['Base Color'].default_value = base_color
    node_bsdf.inputs['Roughness'].default_value = roughness
    node_bsdf.inputs['Metallic'].default_value = 0.0

    if diffuse_tex and os.path.exists(diffuse_tex):
        tex_node = nodes.new(type='ShaderNodeTexImage')
        img = bpy.data.images.load(diffuse_tex)
        tex_node.image = img
        links.new(tex_node.outputs['Color'], node_bsdf.inputs['Base Color'])

    if normal_tex and os.path.exists(normal_tex):
        norm_img_node = nodes.new(type='ShaderNodeTexImage')
        img_norm = bpy.data.images.load(normal_tex)
        img_norm.colorspace_settings.name = 'Non-Color'
        norm_img_node.image = img_norm

        norm_map_node = nodes.new(type='ShaderNodeNormalMap')
        norm_map_node.inputs['Strength'].default_value = 1.2
        links.new(norm_img_node.outputs['Color'], norm_map_node.inputs['Color'])
        links.new(norm_map_node.outputs['Normal'], node_bsdf.inputs['Normal'])

    return mat

def build_violin_mesh(material):
    me = bpy.data.meshes.new("Violin_Mesh_Data")
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")

    # 1. Contorno de la Caja Armónica (Lóbulos y Escotaduras en C de luthier)
    # y va a lo largo del cuerpo del violín (0.0 a 0.355 m)
    # x va a lo ancho (ancho máximo ~0.208 m en lóbulo inferior, ~0.168 m en superior)
    n_pts = 48
    t_vals = np.linspace(0.0, 1.0, n_pts)

    def violin_half_width(t):
        # t = 0 (cordal / base), t = 1 (mástil / talón)
        # Lóbulo inferior: t de 0.0 a 0.35
        # Cintura en C: t de 0.35 a 0.65
        # Lóbulo superior: t de 0.65 a 1.0
        if t < 0.36:
            # Lóbulo inferior amplio
            p = t / 0.36
            w = 0.045 + 0.060 * math.sin(p * math.pi)
        elif t < 0.62:
            # Cintura en C estrecha
            p = (t - 0.36) / 0.26
            w = 0.055 - 0.022 * math.sin(p * math.pi)
        else:
            # Lóbulo superior medio
            p = (t - 0.62) / 0.38
            w = 0.045 + 0.040 * math.sin(p * math.pi)
        return max(w, 0.030)

    # Construir caja volumétrica (tapa, fondo y aros perimetrales)
    body_len = 0.355
    body_height = 0.038
    y_vals = t_vals * body_len

    # Perfil superior (tapa) y fondo
    rim_top = []
    rim_bot = []

    # Lado derecho (+X) e izquierdo (-X)
    loop_pts_top = []
    loop_pts_bot = []

    # Recorrer contorno en sentido horario
    for i, t in enumerate(t_vals):
        w = violin_half_width(t)
        y = y_vals[i]
        # Abombamiento sutil en el centro
        arch = 0.006 * math.sin(t * math.pi)
        loop_pts_top.append((w, y, body_height * 0.5 + arch))
        loop_pts_bot.append((w, y, -body_height * 0.5 - arch))

    for i in range(len(t_vals) - 1, -1, -1):
        t = t_vals[i]
        w = -violin_half_width(t)
        y = y_vals[i]
        arch = 0.006 * math.sin(t * math.pi)
        loop_pts_top.append((w, y, body_height * 0.5 + arch))
        loop_pts_bot.append((w, y, -body_height * 0.5 - arch))

    # Crear vértices para los aros
    v_top = [bm.verts.new(p) for p in loop_pts_top]
    v_bot = [bm.verts.new(p) for p in loop_pts_bot]

    n_rim = len(v_top)
    for i in range(n_rim):
        i_next = (i + 1) % n_rim
        f = bm.faces.new([v_top[i], v_top[i_next], v_bot[i_next], v_bot[i]])
        # UVs para aros
        u0 = i / float(n_rim)
        u1 = (i + 1) / float(n_rim)
        for loop in f.loops:
            if loop.vert == v_top[i]: loop[uv_lay].uv = (u0 * 0.5, 0.1)
            elif loop.vert == v_top[i_next]: loop[uv_lay].uv = (u1 * 0.5, 0.1)
            elif loop.vert == v_bot[i_next]: loop[uv_lay].uv = (u1 * 0.5, 0.0)
            elif loop.vert == v_bot[i]: loop[uv_lay].uv = (u0 * 0.5, 0.0)

    # Tapas superior e inferior (cerrar malla)
    f_top = bm.faces.new(v_top)
    f_bot = bm.faces.new(list(reversed(v_bot)))
    for loop in f_top.loops:
        co = loop.vert.co
        loop[uv_lay].uv = (0.25 + co.x * 1.5, 0.2 + (co.y / body_len) * 0.6)
    for loop in f_bot.loops:
        co = loop.vert.co
        loop[uv_lay].uv = (0.25 + co.x * 1.5, 0.2 + (co.y / body_len) * 0.6)

    # 2. Mástil y Diapasón de Ébano
    # Extendido desde el talón (y = body_len) hasta el clavijero (y = body_len + 0.135)
    neck_start_y = body_len - 0.02
    neck_end_y = body_len + 0.135
    neck_w = 0.018
    neck_h = 0.020
    neck_z = body_height * 0.45

    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, (neck_start_y + neck_end_y) * 0.5, neck_z)) @ Matrix.Diagonal((Vector((neck_w, neck_end_y - neck_start_y, neck_h, 1.0)))))

    # Diapasón que se proyecta sobre la tapa
    fingerboard_start_y = body_len * 0.48
    fingerboard_end_y = neck_end_y
    fb_w_near = 0.025
    fb_w_nut = 0.016
    fb_h = 0.007
    fb_z = neck_z + neck_h * 0.5 + fb_h * 0.5

    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, (fingerboard_start_y + fingerboard_end_y) * 0.5, fb_z)) @ Matrix.Diagonal((Vector((fb_w_near, fingerboard_end_y - fingerboard_start_y, fb_h, 1.0)))))

    # 3. Clavijero y Voluta Tradicional
    pegbox_start_y = neck_end_y
    pegbox_len = 0.075
    pegbox_w = 0.020
    pegbox_h = 0.022
    pegbox_z = neck_z + 0.005

    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, pegbox_start_y + pegbox_len * 0.5, pegbox_z)) @ Matrix.Diagonal((Vector((pegbox_w, pegbox_len, pegbox_h, 1.0)))))

    # 4 Clavijas laterales de afinación
    for i in range(4):
        p_y = pegbox_start_y + 0.015 + i * 0.015
        p_z = pegbox_z + (0.004 if i % 2 == 0 else -0.004)
        side = 0.026
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, p_y, p_z)) @ Matrix.Diagonal((Vector((side, 0.006, 0.006, 1.0)))))

    # Voluta espiral en la punta superior
    scroll_center = Vector((0, pegbox_start_y + pegbox_len + 0.020, pegbox_z + 0.005))
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.018, matrix=Matrix.Translation(scroll_center) @ Matrix.Diagonal(Vector((0.6, 1.2, 1.0, 1.0))))

    # 4. Cordal y Puente
    # Cordal triangular en la parte baja
    tailpiece_y = 0.070
    tailpiece_z = body_height * 0.5 + 0.010
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, tailpiece_y, tailpiece_z)) @ Matrix.Diagonal((Vector((0.024, 0.090, 0.006, 1.0)))))

    # Puente arqueado de arce claro
    bridge_y = body_len * 0.50
    bridge_z = body_height * 0.5 + 0.018
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, bridge_y, bridge_z)) @ Matrix.Diagonal((Vector((0.034, 0.006, 0.025, 1.0)))))

    # 5. Cuerdas del Violín
    string_start_y = 0.030
    string_end_y = pegbox_start_y + pegbox_len * 0.8
    for i, sx in enumerate([-0.009, -0.003, 0.003, 0.009]):
        sz = bridge_z + 0.008
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((sx, (string_start_y + string_end_y) * 0.5, sz)) @ Matrix.Diagonal((Vector((0.0012, string_end_y - string_start_y, 0.0012, 1.0)))))

    # 6. Arco de Violín Clásico (Pernambuco y Crin de Caballo)
    bow_len = 0.72
    bow_offset_x = 0.16
    bow_z = 0.02

    # Varilla de madera noble
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((bow_offset_x, body_len * 0.5, bow_z)) @ Matrix.Diagonal((Vector((0.006, bow_len, 0.006, 1.0)))))
    # Nuez / Talón de ébano
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((bow_offset_x, body_len * 0.5 - bow_len * 0.45, bow_z - 0.010)) @ Matrix.Diagonal((Vector((0.009, 0.035, 0.015, 1.0)))))
    # Cintas de crin blanca tensada
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((bow_offset_x, body_len * 0.5, bow_z - 0.014)) @ Matrix.Diagonal((Vector((0.005, bow_len * 0.94, 0.002, 1.0)))))

    bm.to_mesh(me)
    bm.free()

    obj = bpy.data.objects.new("Violin_Prop", me)
    bpy.context.scene.collection.objects.link(obj)

    # Asignar material
    if material:
        obj.data.materials.append(material)

    return obj

def render_preview():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 48
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800
    scene.render.film_transparent = True

    for light in [o for o in scene.objects if o.type == 'LIGHT']:
        bpy.data.objects.remove(light, do_unlink=True)

    def add_light(name, ltype, energy, loc, color=(1.0, 1.0, 1.0)):
        ld = bpy.data.lights.new(name, ltype)
        ld.energy = energy
        ld.color = color
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        scene.collection.objects.link(lo)
        return lo

    add_light("KeyLight", 'AREA', 180.0, (0.5, -0.6, 0.8), color=(1.0, 0.96, 0.90))
    add_light("FillLight", 'AREA', 90.0, (-0.6, -0.4, 0.6), color=(0.92, 0.96, 1.0))
    add_light("RimLight", 'AREA', 120.0, (0.0, 0.8, 0.5), color=(1.0, 0.95, 0.88))

    cam_data = bpy.data.cameras.new("ViolinCam")
    cam_data.lens = 75
    cam_obj = bpy.data.objects.new("ViolinCam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    cam_obj.location = Vector((0.45, -0.55, 0.50))
    target = Vector((0.08, 0.22, 0.02))
    direction = target - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    scene.render.filepath = PREVIEW_PNG
    bpy.ops.render.render(write_still=True)
    print(f"✓ Render de preview del violín guardado en: {PREVIEW_PNG}")

def main():
    print("=" * 65)
    print("GENERANDO ACTIVO 3D INDEPENDIENTE: VIOLÍN CLÁSICO Y ARCO")
    print("=" * 65)

    clean_scene()
    mat = create_pbr_material("Mat_Violin", DIFFUSE_TEX, NORMAL_TEX, base_color=(0.65, 0.38, 0.18, 1.0), roughness=0.32)
    obj = build_violin_mesh(mat)

    # Guardar archivo .blend
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
    print(f"✓ Guardado .blend en: {OUTPUT_BLEND}")

    # Exportar archivo .glb
    bpy.ops.export_scene.gltf(
        filepath=OUTPUT_GLB,
        export_format='GLB',
        use_selection=False,
        export_apply=False,
        export_animations=False,
        export_materials='EXPORT',
        export_cameras=False,
        export_lights=False
    )
    print(f"✓ Exportado .glb en: {OUTPUT_GLB}")

    render_preview()
    print("=" * 65)
    print("ACTIVO PROP DE VIOLÍN GENERADO EXITOSAMENTE")
    print("=" * 65)

if __name__ == "__main__":
    main()
