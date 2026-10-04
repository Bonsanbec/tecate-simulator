"""
Prueba de esculpido procedural de cabeza, cabello rizado y fedora de Axel V2
"""
import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix, Euler

def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)

clean_scene()

TEX_DIR = os.path.abspath("godot_project/assets/characters/textures")

def create_pbr_mat(name, base_color=(1, 1, 1, 1), roughness=0.5, metallic=0.0,
                   tex_diffuse=None, tex_normal=None, sss=0.0):
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
    bsdf.inputs['Metallic'].default_value = metallic
    
    if sss > 0.0:
        if 'Subsurface Weight' in bsdf.inputs:
            bsdf.inputs['Subsurface Weight'].default_value = sss
        elif 'Subsurface' in bsdf.inputs:
            bsdf.inputs['Subsurface'].default_value = sss
        if 'Subsurface Radius' in bsdf.inputs:
            bsdf.inputs['Subsurface Radius'].default_value = (0.04, 0.02, 0.01)
            
    if tex_diffuse and os.path.exists(tex_diffuse):
        img = bpy.data.images.load(tex_diffuse)
        t_node = nodes.new(type='ShaderNodeTexImage')
        t_node.image = img
        links.new(t_node.outputs['Color'], bsdf.inputs['Base Color'])
        
    if tex_normal and os.path.exists(tex_normal):
        n_img = bpy.data.images.load(tex_normal)
        n_img.colorspace_settings.name = 'Non-Color'
        n_node = nodes.new(type='ShaderNodeTexImage')
        n_node.image = n_img
        n_map = nodes.new(type='ShaderNodeNormalMap')
        links.new(n_node.outputs['Color'], n_map.inputs['Color'])
        links.new(n_map.outputs['Normal'], bsdf.inputs['Normal'])
        
    return mat

mat_skin = create_pbr_mat("Mat_Axel_Skin", (0.80, 0.58, 0.46, 1.0), roughness=0.45,
                          tex_diffuse=os.path.join(TEX_DIR, "axel_face_diffuse.png"),
                          tex_normal=os.path.join(TEX_DIR, "axel_face_normal.png"), sss=0.35)
mat_hat = create_pbr_mat("Mat_Axel_Hat", (0.08, 0.08, 0.09, 1.0), roughness=0.85,
                         tex_diffuse=os.path.join(TEX_DIR, "axel_hat_diffuse.png"),
                         tex_normal=os.path.join(TEX_DIR, "axel_hat_normal.png"))
mat_hair = create_pbr_mat("Mat_Axel_Hair", (0.09, 0.07, 0.06, 1.0), roughness=0.60, metallic=0.05)
mat_eyes = create_pbr_mat("Mat_Axel_Eyes", (1, 1, 1, 1), roughness=0.06,
                          tex_diffuse=os.path.join(TEX_DIR, "axel_eye_diffuse.png"))

print("Materiales creados con éxito.")
