"""
=============================================================================
GENERADOR DE RENDERS DE ÍCONOS DE SELECCIÓN DE PERSONAJE: AXEL Y ELI
=============================================================================
Tecate Simulator - Sistema de Personajes y Menú de Selección Cívica

Genera renders fotográficos de alta fidelidad estilo ícono / avatar para el
menú de selección de personaje, respetando con precisión milimétrica las poses
canónicas presentes en las imágenes de referencia del proyecto:

1. Axel (scratch/humans/axel2.png):
   - Pose estilizada de 3/4 con la mano derecha apoyada con garbo sobre el
     chaleco sartorial a la altura del plexo solar, exhibiendo los anillos.
   - Cabeza orientada con giro sutil hacia su derecha y mentón ligeramente
     alzado, proyectando aplomo y confianza con su sombrero fedora y rizos 360°.
   - Brazo izquierdo descansando relajado al costado del torso.
   - Iluminación de estudio con calidez solar dorada que evoca el atardecer
     de la fotografía de referencia.

2. Eli - Pose Principal (scratch/humans/eli.png):
   - Pose emblemática y carismática señalando con el brazo derecho cruzado
     frente al pecho hacia la derecha del encuadre.
   - Rostro sonriente y cálido de frente a la cámara con leve inclinación lateral,
     gafas finas iluminadas y cuello resort en V de lino marfil.
   - Iluminación frontal calibrada para resaltar la expresión facial y vello pectoral.

3. Eli - Pose Alternativa de Retrato (scratch/humans/eli2.png):
   - Pose frontal distendida con sonrisa abierta y postura relajada.

Salidas producidas en godot_project/assets/characters/icons/:
- axel_icon.png: Ícono transparente RGBA (1024x1024) para botones y tarjetas UI.
- axel_card.png: Retrato completo sobre fondo de estudio cinemático oscuro.
- eli_icon.png: Ícono transparente RGBA (1024x1024) en pose de señalización.
- eli_card.png: Retrato sobre fondo de estudio cinemático oscuro.
- eli_icon_portrait.png: Ícono transparente RGBA (1024x1024) en pose frontal relajada.
=============================================================================
"""

import bpy
import os
import math
import subprocess
import numpy as np
from mathutils import Vector, Euler

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
AXEL_BLEND = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/citizens/axel.blend")
ELI_BLEND = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/citizens/eli.blend")
ASTORGA_BLEND = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/citizens/astorga.blend")
VIOLIN_GLB = os.path.join(PROJECT_ROOT, "godot_project/assets/props/violin.glb")
ICONS_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/icons")
SCRATCH_DIR = os.path.join(PROJECT_ROOT, "scratch")

def ensure_icons_dir():
    os.makedirs(ICONS_DIR, exist_ok=True)

def crop_to_fit_numpy(arr, target_w=1024, target_h=1024):
    h, w, c = arr.shape
    side = min(w, h)
    x0 = (w - side) // 2
    y0 = (h - side) // 2
    cropped = arr[y0:y0+side, x0:x0+side, :]
    y_idx = (np.linspace(0, side - 1, target_h)).astype(int)
    x_idx = (np.linspace(0, side - 1, target_w)).astype(int)
    return cropped[y_idx[:, None], x_idx[None, :], :]

def prepare_axel_background():
    axel_tiff = os.path.join(PROJECT_ROOT, "scratch/fondo_axel.tiff")
    return axel_tiff

def prepare_eli_background():
    eli_bg = os.path.join(PROJECT_ROOT, "scratch/fondo_eli_triangulos.png")
    if not os.path.exists(eli_bg):
        gen_script = os.path.join(PROJECT_ROOT, "scripts/characters/generate_eli_abstract_background.py")
        subprocess.run([
            "/Applications/Blender.app/Contents/MacOS/Blender", "-b", "--python", gen_script
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return eli_bg

def prepare_astorga_background():
    astorga_tiff = os.path.join(PROJECT_ROOT, "scratch/fondo_astorga.tiff")
    return astorga_tiff

def composite_card_with_background(fg_png_path, bg_image_path, out_card_path):
    assert os.path.exists(fg_png_path), f"No existe foreground: {fg_png_path}"
    assert os.path.exists(bg_image_path), f"No existe background: {bg_image_path}"

    img_fg = bpy.data.images.load(fg_png_path)
    img_bg = bpy.data.images.load(bg_image_path)

    target_w, target_h = img_fg.size[0], img_fg.size[1]
    bg_w, bg_h = img_bg.size[0], img_bg.size[1]

    fg_pixels = np.empty(target_w * target_h * 4, dtype=np.float32)
    bg_pixels = np.empty(bg_w * bg_h * 4, dtype=np.float32)

    img_fg.pixels.foreach_get(fg_pixels)
    img_bg.pixels.foreach_get(bg_pixels)

    fg = fg_pixels.reshape((target_h, target_w, 4))
    bg_raw = bg_pixels.reshape((bg_h, bg_w, 4))

    # Crop to fit centrado y escalado al tamaño exacto del render
    bg = crop_to_fit_numpy(bg_raw, target_w, target_h)

    alpha = fg[:, :, 3:4]
    comp = np.empty_like(fg)
    comp[:, :, :3] = fg[:, :, :3] * alpha + bg[:, :, :3] * (1.0 - alpha)
    comp[:, :, 3] = 1.0

    img_out = bpy.data.images.new("CompCardTemp", width=target_w, height=target_h, alpha=False)
    img_out.pixels.foreach_set(comp.flatten())
    img_out.filepath_raw = out_card_path
    img_out.file_format = 'PNG'
    img_out.save()

    bpy.data.images.remove(img_fg)
    bpy.data.images.remove(img_bg)
    bpy.data.images.remove(img_out)
    print(f"✓ Tarjeta compuesta con fondo guardada en: {out_card_path}")

def clear_lights_and_cameras(scene):
    for obj in list(scene.objects):
        if obj.type in {'LIGHT', 'CAMERA'}:
            bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.name.startswith("Backdrop"):
            bpy.data.meshes.remove(mesh, do_unlink=True)

def add_directed_light(scene, name, ltype, energy, loc, target, color=(1.0, 1.0, 1.0), size=1.0, spot_size_deg=65.0):
    ld = bpy.data.lights.new(name, ltype)
    ld.energy = energy
    ld.color = color
    if hasattr(ld, 'size'):
        ld.size = size
    if ltype == 'SPOT':
        ld.spot_size = math.radians(spot_size_deg)
        ld.spot_blend = 0.4
    lo = bpy.data.objects.new(name, ld)
    lo.location = Vector(loc)
    dir_vec = Vector(target) - Vector(loc)
    lo.rotation_euler = dir_vec.to_track_quat('-Z', 'Y').to_euler()
    scene.collection.objects.link(lo)
    return lo

def create_studio_backdrop(scene, center_z=1.25, color=(0.04, 0.05, 0.07, 1.0)):
    # Crear un fondo curvo suave de estudio detrás del personaje
    mesh = bpy.data.meshes.new("BackdropMesh")
    obj = bpy.data.objects.new("Backdrop", mesh)
    scene.collection.objects.link(obj)

    verts = [
        Vector((-1.8, -1.0, center_z - 1.2)),
        Vector(( 1.8, -1.0, center_z - 1.2)),
        Vector(( 1.8, -1.0, center_z + 1.2)),
        Vector((-1.8, -1.0, center_z + 1.2)),
    ]
    faces = [(0, 1, 2, 3)]
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    mat = bpy.data.materials.new("Mat_Studio_Backdrop")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = 0.85
    obj.data.materials.append(mat)
    return obj

def setup_render_engine(scene, resolution=1024, samples=48, transparent=True):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = transparent
    scene.view_settings.exposure = -0.15

# =============================================================================
# 1. RENDER DE AXEL (scratch/humans/axel2.png)
# =============================================================================
def render_axel():
    print("-" * 60)
    print("CONFIGURANDO Y RENDERIZANDO ÍCONO DE AXEL (axel2.png)")
    print("-" * 60)
    bpy.ops.wm.open_mainfile(filepath=AXEL_BLEND)
    scene = bpy.context.scene
    arm = bpy.data.objects.get("Skeleton3D")
    assert arm is not None, "Skeleton3D no encontrado en axel.blend"

    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    # Restablecer todas las transformaciones de huesos
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)

    # Pose de Axel fiel a scratch/humans/axel2.png (espejada canónicamente):
    # 1. Torso en ligero giro de 3/4 hacia su izquierda (lado izquierdo en encuadre)
    arm.pose.bones['Chest'].rotation_euler = (0, math.radians(14), 0)

    # 2. Cabeza orientada con aplomo mirando hacia el horizonte a su derecha (lado derecho en encuadre)
    arm.pose.bones['Head'].rotation_euler = (math.radians(-4), math.radians(26), math.radians(-2))

    # 3. Brazo izquierdo flexionado con la mano apoyada sobre el chaleco sartorial
    arm.pose.bones['UpperArm.L'].rotation_euler = (math.radians(-20), math.radians(-30), math.radians(20))
    arm.pose.bones['Forearm.L'].rotation_euler = (math.radians(102), math.radians(-20), math.radians(-20))
    arm.pose.bones['Hand.L'].rotation_euler = (math.radians(-8), math.radians(-24), math.radians(-5))

    # 4. Brazo derecho relajado cayendo al costado
    arm.pose.bones['UpperArm.R'].rotation_euler = (math.radians(8), 0, math.radians(-8))

    clear_lights_and_cameras(scene)

    # Cámara calibrada para encuadre tipo ícono de busto (sombrero a cinturón)
    cam_data = bpy.data.cameras.new("AxelIconCamera")
    cam_data.lens = 72.0
    cam_obj = bpy.data.objects.new("AxelIconCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    cam_obj.location = Vector((-0.24, 2.15, 1.28))
    target = Vector((-0.02, 0.0, 1.25))
    cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

    # Esquema de iluminación de estudio con acento dorado cálido de atardecer
    head_t = (-0.02, 0.0, 1.48)
    chest_t = (-0.02, 0.0, 1.18)

    add_directed_light(scene, 'GoldenSunKey', 'AREA', 230.0, (-1.2, 1.6, 1.6), chest_t, (1.0, 0.88, 0.72), size=1.2)
    add_directed_light(scene, 'SoftFill', 'AREA', 100.0, (1.2, 1.6, 1.3), head_t, (0.92, 0.96, 1.0), size=2.2)
    add_directed_light(scene, 'RimLight', 'SPOT', 170.0, (0.2, -1.3, 1.9), head_t, (1.0, 0.98, 0.92))
    add_directed_light(scene, 'DetailFill', 'AREA', 50.0, (-0.1, 2.0, 1.2), chest_t, (1.0, 0.98, 0.96), size=1.0)

    # 1. Render Ícono Transparente RGBA
    setup_render_engine(scene, resolution=1024, samples=48, transparent=True)
    out_icon = os.path.join(ICONS_DIR, "axel_icon.png")
    scene.render.filepath = out_icon
    bpy.ops.render.render(write_still=True)
    print(f"✓ Ícono transparente guardado en: {out_icon}")

    # 2. Render Tarjeta con Fondo de scratch/fondo_axel.tiff (Crop to Fit)
    bg_axel = prepare_axel_background()
    out_card = os.path.join(ICONS_DIR, "axel_card.png")
    composite_card_with_background(out_icon, bg_axel, out_card)

# =============================================================================
# 2. RENDER DE ELI (scratch/humans/eli.png y eli2.png)
# =============================================================================
def render_eli():
    print("-" * 60)
    print("CONFIGURANDO Y RENDERIZANDO ÍCONOS DE ELI (eli.png y eli2.png)")
    print("-" * 60)
    bpy.ops.wm.open_mainfile(filepath=ELI_BLEND)
    scene = bpy.context.scene
    arm = bpy.data.objects.get("Skeleton3D")
    assert arm is not None, "Skeleton3D no encontrado en eli.blend"

    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    # A. POSE 1: SEÑALANDO (eli.png)
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)

    # 1. Torso en ángulo sutil
    arm.pose.bones['Chest'].rotation_euler = (0, math.radians(10), 0)

    # 2. Cabeza mirando de frente con inclinación carismática hacia su hombro izquierdo
    arm.pose.bones['Head'].rotation_euler = (math.radians(-3), math.radians(-10), math.radians(-6))

    # 3. Brazo izquierdo señalando a través del pecho hacia la derecha del encuadre
    arm.pose.bones['UpperArm.L'].rotation_euler = (math.radians(-6), math.radians(-34), math.radians(32))
    arm.pose.bones['Forearm.L'].rotation_euler = (math.radians(98), math.radians(-18), math.radians(-14))
    arm.pose.bones['Hand.L'].rotation_euler = (math.radians(-8), math.radians(-22), math.radians(-8))

    # 4. Brazo derecho relajado
    arm.pose.bones['UpperArm.R'].rotation_euler = (math.radians(7), 0, math.radians(-7))

    clear_lights_and_cameras(scene)

    cam_data = bpy.data.cameras.new("EliIconCamera")
    cam_data.lens = 70.0
    cam_obj = bpy.data.objects.new("EliIconCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    cam_obj.location = Vector((0.02, 2.15, 1.28))
    target = Vector((0.0, 0.0, 1.25))
    cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

    head_t = (0.0, 0.0, 1.48)
    chest_t = (0.0, 0.0, 1.22)

    # Iluminación calibrada para el rostro, sonrisa y camisa de lino
    add_directed_light(scene, 'KeyLight', 'AREA', 135.0, (-0.8, 1.6, 1.6), chest_t, (1.0, 0.98, 0.94), size=1.4)
    add_directed_light(scene, 'FillLight', 'AREA', 65.0, (1.0, 1.5, 1.4), head_t, (0.94, 0.97, 1.0), size=2.0)
    add_directed_light(scene, 'FaceLight', 'AREA', 24.0, (0.0, 1.8, 1.48), head_t, (1.0, 0.99, 0.97), size=1.4)
    add_directed_light(scene, 'RimLight', 'SPOT', 115.0, (0.0, -1.3, 1.9), head_t, (1.0, 0.98, 0.95))

    # 1. Render Ícono Transparente RGBA (Pose Señalando)
    setup_render_engine(scene, resolution=1024, samples=48, transparent=True)
    out_icon = os.path.join(ICONS_DIR, "eli_icon.png")
    scene.render.filepath = out_icon
    bpy.ops.render.render(write_still=True)
    print(f"✓ Ícono transparente señalando guardado en: {out_icon}")

    # 2. Render Tarjeta con Fondo Abstracto de Triángulos (Diseño Moderno)
    bg_eli = prepare_eli_background()
    out_card = os.path.join(ICONS_DIR, "eli_card.png")
    composite_card_with_background(out_icon, bg_eli, out_card)

    # B. POSE 2: RETRATO DISTENDIDO (eli2.png)
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)

    arm.pose.bones['Chest'].rotation_euler = (0, 0, 0)
    arm.pose.bones['Head'].rotation_euler = (0, 0, math.radians(5))
    arm.pose.bones['UpperArm.R'].rotation_euler = (math.radians(6), 0, math.radians(-6))
    arm.pose.bones['UpperArm.L'].rotation_euler = (math.radians(6), 0, math.radians(6))

    # Remover fondo para ícono transparente de retrato
    clear_lights_and_cameras(scene)

    cam_obj = bpy.data.objects.new("EliPortraitCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    cam_obj.location = Vector((0.0, 2.05, 1.30))
    target_p = Vector((0.0, 0.0, 1.28))
    cam_obj.rotation_euler = (target_p - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

    add_directed_light(scene, 'KeyLight', 'AREA', 135.0, (0.8, 1.6, 1.6), chest_t, (1.0, 0.98, 0.94), size=1.4)
    add_directed_light(scene, 'FillLight', 'AREA', 65.0, (-1.0, 1.5, 1.4), head_t, (0.94, 0.97, 1.0), size=2.0)
    add_directed_light(scene, 'FaceLight', 'AREA', 24.0, (0.0, 1.8, 1.48), head_t, (1.0, 0.99, 0.97), size=1.4)
    add_directed_light(scene, 'RimLight', 'SPOT', 115.0, (0.0, -1.3, 1.9), head_t, (1.0, 0.98, 0.95))

    setup_render_engine(scene, resolution=1024, samples=48, transparent=True)
    out_portrait = os.path.join(ICONS_DIR, "eli_icon_portrait.png")
    scene.render.filepath = out_portrait
    bpy.ops.render.render(write_still=True)
    print(f"✓ Ícono transparente retrato guardado en: {out_portrait}")

# =============================================================================
# 3. RENDER DE ASTORGA (scratch/humans/astorga.png)
# =============================================================================
def render_astorga():
    print("-" * 60)
    print("CONFIGURANDO Y RENDERIZANDO ÍCONO DE ASTORGA (scratch/humans/astorga.png)")
    print("-" * 60)
    bpy.ops.wm.open_mainfile(filepath=ASTORGA_BLEND)
    scene = bpy.context.scene
    arm = bpy.data.objects.get("Skeleton3D")
    assert arm is not None, "Skeleton3D no encontrado en astorga.blend"

    # Forzar sombreado suave en todas las mallas
    for o in bpy.data.objects:
        if o.type == 'MESH':
            for p in o.data.polygons:
                p.use_smooth = True

    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)

    # Pose canónica de Astorga según scratch/humans/astorga.png:
    # 1. Torso y cabeza con porte natural y sereno
    arm.pose.bones['Spine'].rotation_euler = (math.radians(-1), math.radians(-1), math.radians(1))
    arm.pose.bones['Chest'].rotation_euler = (math.radians(-2), math.radians(-3), math.radians(2))
    arm.pose.bones['Head'].rotation_euler = (math.radians(-1), math.radians(4), math.radians(1))

    # 2. Brazo violinista (Hand.R, -X, en pantalla a la derecha):
    # Sostiene el mástil del violín junto al hombro derecho/mejilla, enmarcando el rostro con orgullo
    arm.pose.bones['Shoulder.R'].rotation_euler = (math.radians(2), math.radians(4), math.radians(-4))
    arm.pose.bones['UpperArm.R'].rotation_euler = (math.radians(34), math.radians(8), math.radians(-38))
    arm.pose.bones['Forearm.R'].rotation_euler = (math.radians(98), math.radians(12), math.radians(-14))
    arm.pose.bones['Hand.R'].rotation_euler = (math.radians(12), math.radians(-8), math.radians(32))

    # 3. Brazo del arco (Hand.L, +X, en pantalla a la izquierda):
    # Sostiene el arco junto a la cintura/cadera, con la mano orientada de modo que los dedos envuelvan la vara
    arm.pose.bones['Shoulder.L'].rotation_euler = (math.radians(-1), math.radians(-2), math.radians(1))
    arm.pose.bones['UpperArm.L'].rotation_euler = (math.radians(14), math.radians(-6), math.radians(10))
    arm.pose.bones['Forearm.L'].rotation_euler = (math.radians(28), math.radians(-4), math.radians(4))
    arm.pose.bones['Hand.L'].rotation_euler = (math.radians(18), math.radians(14), math.radians(-12))

    # 4. Postura natural de piernas (contrapposto sutil):
    arm.pose.bones['UpperLeg.L'].rotation_euler = (math.radians(-3), math.radians(2), math.radians(4))
    arm.pose.bones['LowerLeg.L'].rotation_euler = (math.radians(5), 0, 0)
    arm.pose.bones['Foot.L'].rotation_euler = (math.radians(-2), math.radians(-3), math.radians(-4))

    arm.pose.bones['UpperLeg.R'].rotation_euler = (math.radians(1), math.radians(-1), math.radians(-2))
    arm.pose.bones['Foot.R'].rotation_euler = (math.radians(-1), math.radians(2), math.radians(2))

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()

    # Cálculo de contacto milimétrico exacto usando la malla evaluada en pose
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_obj = bpy.data.objects.get("Player_Body_Mesh")
    body_eval = body_obj.evaluated_get(depsgraph)
    mesh_eval = body_eval.to_mesh()

    vg_r = body_obj.vertex_groups.get("Hand.R")
    hand_r_verts = [v.co for v in mesh_eval.vertices if any(g.group == vg_r.index and g.weight > 0.4 for g in body_obj.data.vertices[v.index].groups)]
    avg_hand_r = sum(hand_r_verts, Vector((0,0,0))) / max(1, len(hand_r_verts))

    vg_l = body_obj.vertex_groups.get("Hand.L")
    hand_l_verts = [v.co for v in mesh_eval.vertices if any(g.group == vg_l.index and g.weight > 0.4 for g in body_obj.data.vertices[v.index].groups)]
    avg_hand_l = sum(hand_l_verts, Vector((0,0,0))) / max(1, len(hand_l_verts))
    body_eval.to_mesh_clear()

    # Cargar Violín y Arco independientes
    VIOLIN_BLEND = os.path.join(PROJECT_ROOT, "godot_project/assets/props/violin.blend")
    if os.path.exists(VIOLIN_BLEND):
        with bpy.data.libraries.load(VIOLIN_BLEND, link=False) as (data_from, data_to):
            data_to.objects = [o for o in data_from.objects if o in ("Violin_Prop", "Violin_Bow")]
        for o in data_to.objects:
            if o:
                scene.collection.objects.link(o)
                for p in o.data.polygons:
                    p.use_smooth = True
                if o.name == "Violin_Prop":
                    o.scale = (0.76, 0.76, 0.76)
                    rot_v = Euler((math.radians(-70), math.radians(160), math.radians(24)), 'XYZ')
                    o.rotation_euler = rot_v
                    neck_local = Vector((0.0, 0.44, 0.012))
                    neck_world_vec = rot_v.to_matrix() @ (Vector(o.scale) * neck_local)
                    o.location = avg_hand_r - neck_world_vec + Vector((0.000, 0.005, -0.008))
                elif o.name == "Violin_Bow":
                    o.scale = (0.72, 0.72, 0.72)
                    rot_b = Euler((math.radians(40), math.radians(-22), math.radians(50)), 'XYZ')
                    o.rotation_euler = rot_b
                    grip_local = Vector((0.0, 0.06, 0.006))
                    grip_world_vec = rot_b.to_matrix() @ (Vector(o.scale) * grip_local)
                    o.location = avg_hand_l - grip_world_vec + Vector((-0.002, 0.018, -0.012))

    clear_lights_and_cameras(scene)

    cam_data = bpy.data.cameras.new("AstorgaIconCamera")
    cam_data.lens = 72.0
    cam_obj = bpy.data.objects.new("AstorgaIconCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    cam_obj.location = Vector((0.0, 2.15, 1.25))
    target = Vector((0.0, 0.0, 1.22))
    cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

    head_t = (0.0, 0.0, 1.48)
    chest_t = (0.0, 0.0, 1.20)

    add_directed_light(scene, 'KeyWarm', 'AREA', 140.0, (-0.8, 1.6, 1.6), chest_t, (1.0, 0.94, 0.88), size=1.4)
    add_directed_light(scene, 'FillHall', 'AREA', 65.0, (1.1, 1.5, 1.4), head_t, (0.92, 0.95, 1.0), size=2.0)
    add_directed_light(scene, 'RimHair', 'SPOT', 125.0, (0.1, -1.3, 1.9), head_t, (1.0, 0.97, 0.92))
    add_directed_light(scene, 'ViolinLight', 'AREA', 60.0, (-0.45, 1.7, 1.28), (-0.15, 0, 1.25), (1.0, 0.95, 0.88), size=1.0)

    # 1. Render Ícono Transparente RGBA
    setup_render_engine(scene, resolution=1024, samples=48, transparent=True)
    out_icon = os.path.join(ICONS_DIR, "astorga_icon.png")
    scene.render.filepath = out_icon
    bpy.ops.render.render(write_still=True)
    print(f"✓ Ícono transparente guardado en: {out_icon}")

    # 2. Render Tarjeta con Fondo de scratch/fondo_astorga.tiff (Crop to Fit)
    bg_astorga = prepare_astorga_background()
    out_card = os.path.join(ICONS_DIR, "astorga_card.png")
    composite_card_with_background(out_icon, bg_astorga, out_card)

    # 3. Render de Cuerpo Completo en Pose (800x1200) para inspección de piernas y calzado
    cam_data.lens = 52.0
    cam_obj.location = Vector((0.0, 2.50, 0.96))
    target_fb = Vector((0.0, 0.0, 0.88))
    cam_obj.rotation_euler = (target_fb - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
    setup_render_engine(scene, resolution=1200, samples=48, transparent=True)
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1200
    out_fb_icon = os.path.join(SCRATCH_DIR, "astorga_fullbody_pose_icon.png")
    scene.render.filepath = out_fb_icon
    bpy.ops.render.render(write_still=True)

    out_fb_card = os.path.join(SCRATCH_DIR, "astorga_fullbody_pose.png")
    composite_card_with_background(out_fb_icon, bg_astorga, out_fb_card)
    print(f"✓ Render de cuerpo completo en pose guardado en: {out_fb_card}")

def main():
    import sys
    ensure_icons_dir()
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    target = args[0].lower() if args else "all"

    if target in ("axel", "all"):
        render_axel()
    if target in ("eli", "all"):
        render_eli()
    if target in ("astorga", "all"):
        render_astorga()

    print("=" * 60)
    print("✓ RENDERS DE ÍCONOS DE PERSONAJES PROCESADOS EXITOSAMENTE")
    print("=" * 60)

if __name__ == "__main__":
    main()
