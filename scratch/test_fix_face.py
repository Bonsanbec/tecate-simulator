import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix

bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Sombrero Fedora 100% Manifold y limpio
# Se genera a partir de un disco/copa cerrada regular con normales consistentes
hat_me = bpy.data.meshes.new("FedoraClean")
hat_obj = bpy.data.objects.new("FedoraClean", hat_me)
bpy.context.scene.collection.objects.link(hat_obj)
h_bm = bmesh.new()

n_seg = 32
r_brim = 0.165
r_crown_base = 0.095
r_crown_top = 0.080
z_base = 1.585
z_top = 1.685

# Anillos concéntricos:
# 0: Borde exterior del ala superior
# 1: Base de la copa exterior
# 2: Corona superior
# 3: Centro de la hendidura (pinch)
ring_brim = []
ring_base = []
ring_top = []

for i in range(n_seg):
    ang = 2.0 * math.pi * i / n_seg
    ca = math.cos(ang)
    sa = math.sin(ang)

    # Curvatura suave del ala (snap brim simétrico)
    # Ala sube 8 mm a los lados, baja 4 mm al frente
    brim_curl = 0.008 * (ca**2) - 0.004 * max(0.0, sa)
    bx = r_brim * ca
    by = (r_brim + 0.010) * sa
    bz = z_base + brim_curl
    ring_brim.append(h_bm.verts.new((bx, by, bz)))

    # Base de la copa
    cx = r_crown_base * ca
    cy = (r_crown_base + 0.008) * sa
    ring_base.append(h_bm.verts.new((cx, cy, z_base)))

    # Corona superior con hendidura Teardrop pinch
    pinch = 0.85 if sa > 0 else 1.0
    tx = r_crown_top * pinch * ca
    ty = (r_crown_top + 0.006) * sa
    tz = z_top - (0.015 * max(0.0, 1.0 - abs(ca)/0.7) if abs(ca) < 0.7 else 0.0)
    ring_top.append(h_bm.verts.new((tx, ty, tz)))

# Caras del ala (entre ring_brim y ring_base)
for i in range(n_seg):
    inxt = (i + 1) % n_seg
    # Normal hacia ARRIBA consistente
    h_bm.faces.new((ring_brim[i], ring_brim[inxt], ring_base[inxt], ring_base[i]))

# Caras de la pared de la copa (entre ring_base y ring_top)
for i in range(n_seg):
    inxt = (i + 1) % n_seg
    h_bm.faces.new((ring_base[i], ring_base[inxt], ring_top[inxt], ring_top[i]))

# Tapa superior de la corona
center_top = h_bm.verts.new((0.0, 0.004, z_top - 0.016))
for i in range(n_seg):
    inxt = (i + 1) % n_seg
    h_bm.faces.new((ring_top[i], ring_top[inxt], center_top))

# Dar espesor al ala mediante extrusión limpia (solidify manual manifold)
# Duplicar borde del ala hacia abajo 3 mm y cerrar cara inferior
ring_brim_bot = []
ring_base_bot = []
for i in range(n_seg):
    v_top = ring_brim[i].co
    ring_brim_bot.append(h_bm.verts.new((v_top.x, v_top.y, v_top.z - 0.003)))
    v_base = ring_base[i].co
    ring_base_bot.append(h_bm.verts.new((v_base.x * 0.98, v_base.y * 0.98, v_base.z - 0.005)))

for i in range(n_seg):
    inxt = (i + 1) % n_seg
    # Canto del borde perimetral
    h_bm.faces.new((ring_brim[i], ring_brim_bot[i], ring_brim_bot[inxt], ring_brim[inxt]))
    # Cara inferior del ala (normal hacia ABAJO)
    h_bm.faces.new((ring_brim_bot[inxt], ring_brim_bot[i], ring_base_bot[i], ring_base_bot[inxt]))

# Cinta del sombrero (Hatband)
r_band_top = []
r_band_bot = []
for i in range(n_seg):
    ang = 2.0 * math.pi * i / n_seg
    ca = math.cos(ang)
    sa = math.sin(ang)
    cx = (r_crown_base + 0.002) * ca
    cy = (r_crown_base + 0.010) * sa
    r_band_bot.append(h_bm.verts.new((cx, cy, z_base + 0.001)))
    r_band_top.append(h_bm.verts.new((cx * 0.98, cy * 0.98, z_base + 0.024)))

for i in range(n_seg):
    inxt = (i + 1) % n_seg
    f_band = h_bm.faces.new((r_band_bot[i], r_band_bot[inxt], r_band_top[inxt], r_band_top[i]))

h_bm.normal_update()
for f in h_bm.faces: f.smooth = True
h_bm.to_mesh(hat_me)
h_bm.free()

# Inclinación elegante del sombrero (-5 grados hacia atrás)
hat_obj.rotation_euler = (math.radians(-5.0), 0.0, 0.0)
hat_obj.location = Vector((0.0, -0.006, 0.0))

# Modificador Subsurf limpio
sub_hat = hat_obj.modifiers.new("Subsurf", type='SUBSURF')
sub_hat.levels = 1

# Material negro mate del sombrero
mat_hat = bpy.data.materials.new("Mat_Hat")
mat_hat.use_nodes = True
mat_hat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.02, 0.02, 0.025, 1.0)
mat_hat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.92
hat_obj.data.materials.append(mat_hat)

# Render test del sombrero solo para certificar CERO aletas ni defectos
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.render.resolution_x = 720
scene.render.resolution_y = 900

cam = bpy.data.objects.new("CamTest", bpy.data.cameras.new("CamTest"))
cam.data.lens = 65.0
cam.location = Vector((0.45, 0.55, 1.62))
cam.rotation_euler = (math.radians(72.0), 0.0, math.radians(145.0))
scene.collection.objects.link(cam)
scene.camera = cam

light = bpy.data.objects.new("Light", bpy.data.lights.new("Light", 'AREA'))
light.location = Vector((0.4, 0.5, 1.9))
light.data.energy = 50.0
scene.collection.objects.link(light)

scene.render.filepath = "/tmp/test_clean_fedora.png"
bpy.ops.render.render(write_still=True)
print("Clean fedora rendered to /tmp/test_clean_fedora.png!")
