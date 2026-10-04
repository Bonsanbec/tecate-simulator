"""
Prueba de generación de cabeza de Axel con UVs analíticos exactos
y mapeo directo de texturas procedurales (piel, ojos, rizos, fedora).
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix, Euler

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
TEXTURES_DIR = os.path.join(PROJECT_ROOT, "godot_project/assets/characters/textures")
PREVIEW_PNG = os.path.join(PROJECT_ROOT, "scratch/test_head_preview.png")

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)

def create_pbr_mat(name, base_color=(1,1,1,1), roughness=0.5, diffuse_path=None, normal_path=None):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    bsdf.inputs['Base Color'].default_value = base_color
    bsdf.inputs['Roughness'].default_value = roughness

    if diffuse_path and os.path.exists(diffuse_path):
        t_node = nodes.new(type='ShaderNodeTexImage')
        t_node.image = bpy.data.images.load(diffuse_path)
        links.new(t_node.outputs['Color'], bsdf.inputs['Base Color'])

    if normal_path and os.path.exists(normal_path):
        n_img = nodes.new(type='ShaderNodeTexImage')
        n_img.image = bpy.data.images.load(normal_path)
        n_img.image.colorspace_settings.name = 'Non-Color'
        n_map = nodes.new(type='ShaderNodeNormalMap')
        n_map.inputs['Strength'].default_value = 0.85
        links.new(n_img.outputs['Color'], n_map.inputs['Color'])
        links.new(n_map.outputs['Normal'], bsdf.inputs['Normal'])

    return mat

def build_head():
    me = bpy.data.meshes.new("Head_Data")
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")

    # Niveles Z anatómicos realistas compactos (cuello de 8 cm, barbilla a Z=1.48, ojos a Z=1.62)
    # Z, rx, ry_front, ry_back, y_offset, v_coord
    levels = [
        (1.40, 0.052, 0.048, 0.052, 0.010, 0.15), # Base cuello
        (1.43, 0.050, 0.046, 0.050, 0.015, 0.22), # Cuello medio / nuez
        (1.46, 0.050, 0.042, 0.052, 0.015, 0.30), # Garganta retraída
        (1.485, 0.060, 0.076, 0.062, 0.020, 0.37),# Mentón prominente
        (1.505, 0.063, 0.068, 0.066, 0.018, 0.41),# Surco mentolabial
        (1.525, 0.066, 0.078, 0.072, 0.015, 0.45),# Labio inferior
        (1.540, 0.067, 0.076, 0.074, 0.012, 0.48),# Comisura boca
        (1.555, 0.068, 0.079, 0.076, 0.010, 0.51),# Labio superior (arco de Cupido)
        (1.570, 0.069, 0.088, 0.078, 0.008, 0.54),# Punta nariz prominente
        (1.590, 0.070, 0.080, 0.080, 0.005, 0.58),# Puente nasal
        (1.615, 0.072, 0.064, 0.084, 0.002, 0.63),# Cuencas oculares
        (1.640, 0.073, 0.068, 0.085, 0.000, 0.70),# Arco superciliar / cejas
        (1.670, 0.074, 0.065, 0.084, -0.003, 0.78),# Frente
        (1.700, 0.070, 0.058, 0.078, -0.006, 0.86),# Frente alta
        (1.730, 0.058, 0.045, 0.064, -0.008, 0.94),# Bóveda craneal
        (1.750, 0.035, 0.025, 0.040, -0.010, 0.98),# Coronilla
    ]
    
    n_ring = 32
    ring_data = [] # lista de (verts, u_coords, v_coord)
    
    for l_idx, (z, rx, ry_f, ry_b, y_off, v_c) in enumerate(levels):
        cur_verts = []
        cur_u = []
        for i in range(n_ring):
            ang = (2.0 * math.pi * i) / n_ring
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            
            x = rx * cos_a
            y = (ry_f if sin_a >= 0 else ry_b) * sin_a + y_off
            
            # Nariz en l_idx 7, 8, 9
            if l_idx in (7, 8, 9) and 0.4 * math.pi <= ang <= 0.6 * math.pi:
                nw = max(0.0, 1.0 - abs(ang - 0.5 * math.pi) / 0.22)
                y += (0.016 if l_idx == 8 else 0.008) * nw
                
            # Mentón en l_idx 3
            if l_idx == 3 and 0.35 * math.pi <= ang <= 0.65 * math.pi:
                cw = max(0.0, 1.0 - abs(ang - 0.5 * math.pi) / 0.30)
                y += 0.014 * cw
                
            # Cuencas oculares en l_idx 10
            if l_idx == 10 and (0.28 * math.pi <= ang <= 0.42 * math.pi or 0.58 * math.pi <= ang <= 0.72 * math.pi):
                y -= 0.010
                
            v = bm.verts.new((x, y, z))
            cur_verts.append(v)
            
            # Cálculo de U centrado en el rostro:
            # ang = pi/2 -> frente (+Y) -> u = 0.50
            # ang = 0 -> izquierda (+X) -> u = 0.25
            # ang = -pi/2 -> atrás (-Y) -> u = 0.0 (o 1.0)
            # ang = pi -> derecha (-X) -> u = 0.75
            # Mapeo: u = (ang + pi/2) / (2pi) mod 1.0
            u_val = (ang - 0.5 * math.pi) / (2.0 * math.pi)
            if u_val < 0.0:
                u_val += 1.0
            # Queremos que la cara esté en el centro (0.5), así que:
            u_face = 1.0 - u_val # simetría natural
            cur_u.append(u_face)
            
        ring_data.append((cur_verts, cur_u, v_c))
        
    for l_idx in range(len(levels) - 1):
        r1, u1, v1 = ring_data[l_idx]
        r2, u2, v2 = ring_data[l_idx + 1]
        for i in range(n_ring):
            i_next = (i + 1) % n_ring
            f = bm.faces.new((r1[i], r1[i_next], r2[i_next], r2[i]))
            f.material_index = 0 # Piel
            # Asignar coordenadas UV a cada loop
            for loop in f.loops:
                if loop.vert == r1[i]:
                    loop[uv_lay].uv = (u1[i], v1)
                elif loop.vert == r1[i_next]:
                    # Evitar costura UV cruzada en el borde
                    u_adj = u1[i_next]
                    if abs(u_adj - u1[i]) > 0.5:
                        u_adj = u_adj + 1.0 if u1[i] > 0.5 else u_adj - 1.0
                    loop[uv_lay].uv = (u_adj, v1)
                elif loop.vert == r2[i_next]:
                    u_adj = u2[i_next]
                    if abs(u_adj - u2[i]) > 0.5:
                        u_adj = u_adj + 1.0 if u2[i] > 0.5 else u_adj - 1.0
                    loop[uv_lay].uv = (u_adj, v2)
                elif loop.vert == r2[i]:
                    loop[uv_lay].uv = (u2[i], v2)

    # 2. Ojos 3D con textura de iris avellana
    eye_pos = [(0.033, 0.052, 1.615), (-0.033, 0.052, 1.615)]
    for pos in eye_pos:
        e_bm = bmesh.new()
        bmesh.ops.create_uvsphere(e_bm, u_segments=16, v_segments=12, radius=0.0135)
        # Rotar para que el polo del iris mire hacia +Y
        bmesh.ops.rotate(e_bm, verts=e_bm.verts, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(-90), 4, 'X'))
        bmesh.ops.translate(e_bm, verts=e_bm.verts, vec=pos)
        
        v_map = {v: bm.verts.new(v.co) for v in e_bm.verts}
        for f in e_bm.faces:
            nf = bm.faces.new([v_map[v] for v in f.verts])
            nf.material_index = 1 # Ojos
            # UV planar polar para iris
            for loop in nf.loops:
                co = loop.vert.co - Vector(pos)
                u_eye = 0.5 + co.x / (2.0 * 0.0135)
                v_eye = 0.5 + co.z / (2.0 * 0.0135)
                loop[uv_lay].uv = (u_eye, v_eye)
        e_bm.free()

    bm.normal_update()
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()

    obj = bpy.data.objects.new("Test_Head", me)
    bpy.context.scene.collection.objects.link(obj)
    return obj

def main():
    clean_scene()
    mat_skin = create_pbr_mat("Mat_Skin", (0.80, 0.63, 0.52, 1.0), roughness=0.48,
                              diffuse_path=os.path.join(TEXTURES_DIR, "axel_face_diffuse.png"),
                              normal_path=os.path.join(TEXTURES_DIR, "axel_face_normal.png"))
    mat_eye = create_pbr_mat("Mat_Eye", (1, 1, 1, 1), roughness=0.1,
                             diffuse_path=os.path.join(TEXTURES_DIR, "axel_eye_diffuse.png"))

    head_obj = build_head()
    head_obj.data.materials.append(mat_skin)
    head_obj.data.materials.append(mat_eye)

    # Cámara enfocada en el rostro
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    scene.cycles.device = 'CPU'
    
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 85.0
    cam = bpy.data.objects.new("Cam", cam_data)
    cam.location = Vector((0.0, 1.15, 1.58))
    cam.rotation_euler = (math.radians(90), 0, math.radians(180))
    scene.collection.objects.link(cam)
    scene.camera = cam

    # Iluminación
    light_data = bpy.data.lights.new("Sun", type='SUN')
    light_data.energy = 3.5
    light = bpy.data.objects.new("Sun", light_data)
    light.rotation_euler = (math.radians(40), math.radians(20), math.radians(-130))
    scene.collection.objects.link(light)

    scene.render.resolution_x = 720
    scene.render.resolution_y = 720
    scene.render.filepath = PREVIEW_PNG
    bpy.ops.render.render(write_still=True)
    print("Render guardado en:", PREVIEW_PNG)

if __name__ == "__main__":
    main()
