"""
Renderiza un preview de estudio fotográfico de Axel para inspección visual
"""
import bpy
import os
import math
from mathutils import Vector

def render_preview():
    # Cargar la escena de axel.blend
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath("godot_project/assets/characters/citizens/axel.blend"))
    scene = bpy.context.scene

    # Configurar motor de render Cycles de alta definición
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.device = 'CPU'
    scene.render.resolution_x = 720
    scene.render.resolution_y = 1280
    scene.render.resolution_percentage = 100

    # Crear Cámara de Estudio
    cam_data = bpy.data.cameras.new("StudioCamera")
    cam_data.lens = 55.0 # Lente retrato para encuadre natural sin distorsión de perspectiva
    cam_obj = bpy.data.objects.new("StudioCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # Posición: encuadre frontal suave a la altura del pecho que abarca rostro, chamarra, cinturón y ambas manos
    cam_obj.location = Vector((0.08, 1.95, 1.25))
    cam_obj.rotation_euler = (math.radians(88.5), 0.0, math.radians(178.0))

    # Luces de estudio suaves calibradas (3-point lighting suave)
    # 1. Key Light (luz principal cálida a 45 grados)
    key_data = bpy.data.lights.new("KeyLight", type='AREA')
    key_data.energy = 85.0
    key_data.size = 1.4
    key_data.color = (1.0, 0.98, 0.95)
    key_obj = bpy.data.objects.new("KeyLight", key_data)
    key_obj.location = Vector((-0.8, 1.5, 1.7))
    key_obj.rotation_euler = (math.radians(55.0), 0.0, math.radians(-145.0))
    scene.collection.objects.link(key_obj)

    # 2. Fill Light (luz de relleno suave azulada)
    fill_data = bpy.data.lights.new("FillLight", type='AREA')
    fill_data.energy = 38.0
    fill_data.size = 1.6
    fill_data.color = (0.92, 0.96, 1.0)
    fill_obj = bpy.data.objects.new("FillLight", fill_data)
    fill_obj.location = Vector((1.0, 1.5, 1.3))
    scene.collection.objects.link(fill_obj)

    # 3. Rim Light (luz de contra suave para silueta de hombros y gorro)
    rim_data = bpy.data.lights.new("RimLight", type='SPOT')
    rim_data.energy = 45.0
    rim_data.spot_size = math.radians(65.0)
    rim_data.color = (1.0, 1.0, 1.0)
    rim_obj = bpy.data.objects.new("RimLight", rim_data)
    rim_obj.location = Vector((0.0, -1.2, 1.9))
    rim_obj.rotation_euler = (math.radians(-50.0), 0.0, 0.0)
    scene.collection.objects.link(rim_obj)

    output_path = os.path.abspath("godot_project/assets/characters/axel_preview.png")
    scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"✓ Render preview guardado en: {output_path}")

if __name__ == "__main__":
    render_preview()
