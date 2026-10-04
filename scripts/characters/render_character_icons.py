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
from mathutils import Vector, Euler

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
AXEL_BLEND = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/citizens/axel.blend")
ELI_BLEND = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/citizens/eli.blend")
ICONS_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/icons")

def ensure_icons_dir():
    os.makedirs(ICONS_DIR, exist_ok=True)

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

    # Pose de Axel fiel a scratch/humans/axel2.png:
    # 1. Torso en ligero giro de 3/4 hacia su derecha
    arm.pose.bones['Chest'].rotation_euler = (0, math.radians(-14), 0)

    # 2. Cabeza orientada con aplomo mirando hacia el horizonte a su derecha
    arm.pose.bones['Head'].rotation_euler = (math.radians(-4), math.radians(-26), math.radians(2))

    # 3. Brazo derecho flexionado con la mano apoyada sobre el chaleco sartorial
    arm.pose.bones['UpperArm.R'].rotation_euler = (math.radians(-20), math.radians(30), math.radians(-20))
    arm.pose.bones['Forearm.R'].rotation_euler = (math.radians(102), math.radians(20), math.radians(20))
    arm.pose.bones['Hand.R'].rotation_euler = (math.radians(-8), math.radians(24), math.radians(5))

    # 4. Brazo izquierdo relajado cayendo al costado
    arm.pose.bones['UpperArm.L'].rotation_euler = (math.radians(8), 0, math.radians(8))

    clear_lights_and_cameras(scene)

    # Cámara calibrada para encuadre tipo ícono de busto (sombrero a cinturón)
    cam_data = bpy.data.cameras.new("AxelIconCamera")
    cam_data.lens = 72.0
    cam_obj = bpy.data.objects.new("AxelIconCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    cam_obj.location = Vector((0.24, 2.15, 1.28))
    target = Vector((0.02, 0.0, 1.25))
    cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

    # Esquema de iluminación de estudio con acento dorado cálido de atardecer
    head_t = (0.02, 0.0, 1.48)
    chest_t = (0.02, 0.0, 1.18)

    add_directed_light(scene, 'GoldenSunKey', 'AREA', 230.0, (1.2, 1.6, 1.6), chest_t, (1.0, 0.88, 0.72), size=1.2)
    add_directed_light(scene, 'SoftFill', 'AREA', 100.0, (-1.2, 1.6, 1.3), head_t, (0.92, 0.96, 1.0), size=2.2)
    add_directed_light(scene, 'RimLight', 'SPOT', 170.0, (-0.2, -1.3, 1.9), head_t, (1.0, 0.98, 0.92))
    add_directed_light(scene, 'DetailFill', 'AREA', 50.0, (0.1, 2.0, 1.2), chest_t, (1.0, 0.98, 0.96), size=1.0)

    # 1. Render Ícono Transparente RGBA
    setup_render_engine(scene, resolution=1024, samples=48, transparent=True)
    out_icon = os.path.join(ICONS_DIR, "axel_icon.png")
    scene.render.filepath = out_icon
    bpy.ops.render.render(write_still=True)
    print(f"✓ Ícono transparente guardado en: {out_icon}")

    # 2. Render Tarjeta con Fondo de Estudio Cinemático
    create_studio_backdrop(scene, center_z=1.25, color=(0.05, 0.06, 0.09, 1.0))
    setup_render_engine(scene, resolution=1024, samples=48, transparent=False)
    out_card = os.path.join(ICONS_DIR, "axel_card.png")
    scene.render.filepath = out_card
    bpy.ops.render.render(write_still=True)
    print(f"✓ Tarjeta de estudio guardada en: {out_card}")

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
    arm.pose.bones['Chest'].rotation_euler = (0, math.radians(-10), 0)

    # 2. Cabeza mirando de frente con inclinación carismática hacia su hombro derecho
    arm.pose.bones['Head'].rotation_euler = (math.radians(-3), math.radians(10), math.radians(6))

    # 3. Brazo derecho señalando a través del pecho hacia la derecha del encuadre
    arm.pose.bones['UpperArm.R'].rotation_euler = (math.radians(-6), math.radians(34), math.radians(-32))
    arm.pose.bones['Forearm.R'].rotation_euler = (math.radians(98), math.radians(18), math.radians(14))
    arm.pose.bones['Hand.R'].rotation_euler = (math.radians(-8), math.radians(22), math.radians(8))

    # 4. Brazo izquierdo relajado
    arm.pose.bones['UpperArm.L'].rotation_euler = (math.radians(7), 0, math.radians(7))

    clear_lights_and_cameras(scene)

    cam_data = bpy.data.cameras.new("EliIconCamera")
    cam_data.lens = 70.0
    cam_obj = bpy.data.objects.new("EliIconCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    cam_obj.location = Vector((-0.02, 2.15, 1.28))
    target = Vector((0.0, 0.0, 1.25))
    cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

    head_t = (0.0, 0.0, 1.48)
    chest_t = (0.0, 0.0, 1.22)

    # Iluminación calibrada para el rostro, sonrisa y camisa de lino (atenuada para evitar sobreexposición/blanqueado)
    add_directed_light(scene, 'KeyLight', 'AREA', 135.0, (0.8, 1.6, 1.6), chest_t, (1.0, 0.98, 0.94), size=1.4)
    add_directed_light(scene, 'FillLight', 'AREA', 65.0, (-1.0, 1.5, 1.4), head_t, (0.94, 0.97, 1.0), size=2.0)
    add_directed_light(scene, 'FaceLight', 'AREA', 24.0, (0.0, 1.8, 1.48), head_t, (1.0, 0.99, 0.97), size=1.4)
    add_directed_light(scene, 'RimLight', 'SPOT', 115.0, (0.0, -1.3, 1.9), head_t, (1.0, 0.98, 0.95))

    # 1. Render Ícono Transparente RGBA (Pose Señalando)
    setup_render_engine(scene, resolution=1024, samples=48, transparent=True)
    out_icon = os.path.join(ICONS_DIR, "eli_icon.png")
    scene.render.filepath = out_icon
    bpy.ops.render.render(write_still=True)
    print(f"✓ Ícono transparente señalando guardado en: {out_icon}")

    # 2. Render Tarjeta con Fondo de Estudio Cinemático (Pose Señalando)
    create_studio_backdrop(scene, center_z=1.25, color=(0.05, 0.06, 0.09, 1.0))
    setup_render_engine(scene, resolution=1024, samples=48, transparent=False)
    out_card = os.path.join(ICONS_DIR, "eli_card.png")
    scene.render.filepath = out_card
    bpy.ops.render.render(write_still=True)
    print(f"✓ Tarjeta de estudio señalando guardada en: {out_card}")

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

def main():
    ensure_icons_dir()
    render_axel()
    render_eli()
    print("=" * 60)
    print("✓ TODOS LOS RENDERS DE ÍCONOS DE PERSONAJES HAN SIDO GENERADOS EXITOSAMENTE")
    print("=" * 60)

if __name__ == "__main__":
    main()
