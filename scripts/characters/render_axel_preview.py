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

    # Configurar motor de render EEVEE_NEXT o Workbench/Cycles
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 16
    scene.cycles.device = 'CPU'
    scene.render.resolution_x = 720
    scene.render.resolution_y = 1280
    scene.render.resolution_percentage = 100

    # Crear Cámara de Estudio
    cam_data = bpy.data.cameras.new("StudioCamera")
    cam_data.lens = 55.0 # Lente retrato
    cam_obj = bpy.data.objects.new("StudioCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # Posición: frente a Axel, encuadre de cuerpo completo y medio cuerpo
    cam_obj.location = Vector((0.0, 2.8, 1.25))
    cam_obj.rotation_euler = (math.radians(88.0), 0.0, math.radians(180.0))

    # Luces de estudio (Key light, Fill light, Rim light)
    # 1. Key Light
    key_data = bpy.data.lights.new("KeyLight", type='AREA')
    key_data.energy = 350.0
    key_data.size = 1.2
    key_data.color = (1.0, 0.96, 0.92)
    key_obj = bpy.data.objects.new("KeyLight", key_data)
    key_obj.location = Vector((-1.2, 2.0, 2.2))
    key_obj.rotation_euler = (math.radians(65.0), 0.0, math.radians(-145.0))
    scene.collection.objects.link(key_obj)

    # 2. Fill Light
    fill_data = bpy.data.lights.new("FillLight", type='AREA')
    fill_data.energy = 150.0
    fill_data.size = 1.5
    fill_data.color = (0.85, 0.92, 1.0)
    fill_obj = bpy.data.objects.new("FillLight", fill_data)
    fill_obj.location = Vector((1.4, 2.2, 1.5))
    scene.collection.objects.link(fill_obj)

    # 3. Rim Light (Luz de contra para recortar silueta)
    rim_data = bpy.data.lights.new("RimLight", type='SPOT')
    rim_data.energy = 400.0
    rim_data.spot_size = math.radians(70.0)
    rim_data.color = (1.0, 1.0, 1.0)
    rim_obj = bpy.data.objects.new("RimLight", rim_data)
    rim_obj.location = Vector((0.0, -1.8, 2.4))
    rim_obj.rotation_euler = (math.radians(-45.0), 0.0, 0.0)
    scene.collection.objects.link(rim_obj)

    output_path = os.path.abspath("godot_project/assets/characters/axel_preview.png")
    scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"✓ Render preview guardado en: {output_path}")

if __name__ == "__main__":
    render_preview()
