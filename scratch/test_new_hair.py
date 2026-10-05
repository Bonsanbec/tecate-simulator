import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Euler

# Clean scene
bpy.ops.wm.read_factory_settings(use_empty=True)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# Build a test hair volume
bm = bmesh.new()

# Hair cap/mass profile layers (z, rx, ry_front, ry_back, y_offset, open_front_angle)
# open_front_angle is the angular range in radians in the front that is open for the face
hair_layers = [
    # z,      rx,    ry_f,  ry_b,  y_off,  open_ang (from -X to +X in front)
    (1.635,  0.048, 0.040, 0.052, -0.012, 0.0),            # 0: Coronilla / Cúpula superior
    (1.615,  0.072, 0.058, 0.076, -0.010, 0.22 * math.pi), # 1: Bóveda superior
    (1.585,  0.088, 0.070, 0.088, -0.008, 0.38 * math.pi), # 2: Frente alta / nacimiento
    (1.550,  0.098, 0.076, 0.096, -0.006, 0.44 * math.pi), # 3: Sienes / frente media
    (1.510,  0.106, 0.078, 0.100, -0.004, 0.46 * math.pi), # 4: Nivel ojos y orejas (máximo volumen lateral 70s)
    (1.470,  0.102, 0.072, 0.096, -0.004, 0.48 * math.pi), # 5: Nivel pómulos / lóbulo oreja
    (1.430,  0.088, 0.058, 0.088, -0.006, 0.52 * math.pi), # 6: Mandíbula / cuello medio
    (1.395,  0.068, 0.044, 0.074, -0.008, 0.56 * math.pi), # 7: Nuca inferior / sobre cuello de camisa
]

n_pts = 32
layer_verts = []

for l_idx, (z, rx, ry_f, ry_b, y_off, open_ang) in enumerate(hair_layers):
    cur_layer = []
    # Angulo va desde open_ang/2 hasta 2*pi - open_ang/2 pasando por detrás
    # donde pi/2 es el frente (+Y) y 3*pi/2 es la espalda (-Y).
    # Frente es ang = pi/2.
    # Si open_ang > 0, la abertura facial está centrada en pi/2: [pi/2 - open_ang/2, pi/2 + open_ang/2]
    # El cabello cubre desde pi/2 + open_ang/2 (lado izquierdo) -> pi (espalda) -> 0 -> pi/2 - open_ang/2 (lado derecho)
    span = (2.0 * math.pi) - open_ang
    start_ang = 0.5 * math.pi + 0.5 * open_ang
    for i in range(n_pts):
        ang = start_ang + span * (i / float(n_pts - 1))
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        x = rx * cos_a
        y = (ry_f if sin_a >= 0 else ry_b) * sin_a + y_off
        
        # Modulaciones de ondulación orgánica sutil en la superficie
        wave = 0.0035 * math.sin(ang * 5.0 + z * 18.0)
        x += wave * cos_a
        y += wave * sin_a
        
        v = bm.verts.new((x, y, z))
        cur_layer.append(v)
    layer_verts.append(cur_layer)

# Conectar capas en quads
for l_idx in range(len(hair_layers) - 1):
    r1 = layer_verts[l_idx]
    r2 = layer_verts[l_idx + 1]
    for i in range(n_pts - 1):
        bm.faces.new((r1[i], r1[i+1], r2[i+1], r2[i]))

# Cerrar la coronilla superior con un abanico suave
top_center = bm.verts.new((0.0, -0.012, 1.642))
r0 = layer_verts[0]
for i in range(n_pts - 1):
    bm.faces.new((r0[i+1], r0[i], top_center))

# Ahora añadir mechones de flequillo y ondas laterales que caen fluidas
def add_hair_ribbon(p_start, p_end, p_ctrl, w_base=0.026, th=0.007, n_seg=7):
    p0 = Vector(p_start)
    p1 = Vector(p_ctrl)
    p2 = Vector(p_end)
    prev_verts = None
    for s in range(n_seg + 1):
        t = s / float(n_seg)
        # Bézier cuadrática
        p = (1.0 - t)**2 * p0 + 2.0 * (1.0 - t) * t * p1 + t**2 * p2
        tang = (2.0 * (1.0 - t) * (p1 - p0) + 2.0 * t * (p2 - p1)).normalized()
        up = Vector((0, 0, 1))
        side = tang.cross(up)
        if side.length < 0.001: side = Vector((1, 0, 0))
        else: side.normalize()
        nor = side.cross(tang).normalized()
        
        w_cur = w_base * (1.0 - 0.45 * t)
        th_cur = th * (1.0 - 0.45 * t)
        
        # Ribbon de 4 vértices
        v1 = bm.verts.new(p - side * (w_cur * 0.5) - nor * (th_cur * 0.5))
        v2 = bm.verts.new(p + side * (w_cur * 0.5) - nor * (th_cur * 0.5))
        v3 = bm.verts.new(p + side * (w_cur * 0.5) + nor * (th_cur * 0.5))
        v4 = bm.verts.new(p - side * (w_cur * 0.5) + nor * (th_cur * 0.5))
        c_verts = [v1, v2, v3, v4]
        
        if prev_verts:
            bm.faces.new((prev_verts[0], prev_verts[1], c_verts[1], c_verts[0]))
            bm.faces.new((prev_verts[1], prev_verts[2], c_verts[2], c_verts[1]))
            bm.faces.new((prev_verts[2], prev_verts[3], c_verts[3], c_verts[2]))
            bm.faces.new((prev_verts[3], prev_verts[0], c_verts[0], c_verts[3]))
        prev_verts = c_verts

# Mechones de raya y flequillo ondulado elegante hacia los lados
# Izquierda (mirando de frente: X > 0)
add_hair_ribbon((0.005, 0.065, 1.585), (0.075, 0.045, 1.515), (0.045, 0.078, 1.565), w_base=0.024, th=0.006)
add_hair_ribbon((0.015, 0.062, 1.595), (0.092, 0.030, 1.500), (0.065, 0.072, 1.560), w_base=0.026, th=0.006)
add_hair_ribbon((0.060, 0.042, 1.560), (0.105, 0.005, 1.465), (0.095, 0.045, 1.515), w_base=0.028, th=0.007)

# Derecha (mirando de frente: X < 0)
add_hair_ribbon((-0.005, 0.065, 1.585), (-0.075, 0.045, 1.515), (-0.045, 0.078, 1.565), w_base=0.024, th=0.006)
add_hair_ribbon((-0.015, 0.062, 1.595), (-0.092, 0.030, 1.500), (-0.065, 0.072, 1.560), w_base=0.026, th=0.006)
add_hair_ribbon((-0.060, 0.042, 1.560), (-0.105, 0.005, 1.465), (-0.095, 0.045, 1.515), w_base=0.028, th=0.007)

bm.normal_update()
for f in bm.faces: f.smooth = True

me = bpy.data.meshes.new("TestHair")
bm.to_mesh(me)
bm.free()

obj = bpy.data.objects.new("TestHair", me)
bpy.context.scene.collection.objects.link(obj)

mat = bpy.data.materials.new("HairMat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.08, 0.06, 0.05, 1.0)
bsdf.inputs["Roughness"].default_value = 0.65
me.materials.append(mat)

print("Hair volume created successfully with", len(me.vertices), "vertices")
