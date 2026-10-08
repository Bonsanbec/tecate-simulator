#!/usr/bin/env python3
"""
Prueba de alta fidelidad: Manos de 5 dedos, Agarre canónico y Cabello favorito de Astorga.
Renderiza close-ups de ambas manos y la pose completa para verificación visual rigurosa.
"""
import os
import sys
import math
import bpy
import bmesh
from mathutils import Vector, Euler, Matrix

PROJECT_ROOT = "/Users/hakkindavid/Documents/GitHub/tecate-simulator"
SCRATCH_DIR = os.path.join(PROJECT_ROOT, "scratch")
VIOLIN_BLEND = os.path.join(PROJECT_ROOT, "godot_project/assets/props/violin.blend")

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 32
    scene.render.film_transparent = True
    return scene

def create_materials():
    mats = {}
    defs = {
        "Suit":        ((0.015, 0.015, 0.016, 1.0), 0.85),
        "Pants":       ((0.015, 0.015, 0.016, 1.0), 0.88),
        "Shoes":       ((0.005, 0.005, 0.006, 1.0), 0.20),
        "Skin":        ((0.720, 0.490, 0.380, 1.0), 0.55),
        "ShirtWine":   ((0.260, 0.035, 0.055, 1.0), 0.70),
        "TieBlack":    ((0.008, 0.008, 0.010, 1.0), 0.65),
        "GoldBuckle":  ((0.850, 0.680, 0.180, 1.0), 0.25),
        "HairBlack":   ((0.022, 0.018, 0.016, 1.0), 0.85),
        "EyeWhite":    ((0.920, 0.920, 0.900, 1.0), 0.20),
        "EyeIris":     ((0.140, 0.080, 0.050, 1.0), 0.30),
    }
    for name, (col, rough) in defs.items():
        m = bpy.data.materials.new(name=name)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = col
            bsdf.inputs['Roughness'].default_value = rough
        mats[name] = m
    return mats

def build_head(mats):
    me = bpy.data.meshes.new("Player_Head_Mesh")
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")

    # Cráneo / rostro
    head_rings = [
        (1.410, 0.040, 0.044, -0.010),
        (1.440, 0.062, 0.066, -0.008),
        (1.480, 0.076, 0.080, -0.006),
        (1.520, 0.080, 0.084, -0.005),
        (1.560, 0.076, 0.080, -0.006),
        (1.595, 0.062, 0.066, -0.008),
        (1.618, 0.038, 0.040, -0.010),
    ]
    n_ring = 24
    rings = []
    for z, rx, ry, y_off in head_rings:
        r = []
        for i in range(n_ring):
            ang = (2.0 * math.pi * i) / n_ring
            x = rx * math.cos(ang)
            y = ry * math.sin(ang) + y_off
            r.append(bm.verts.new((x, y, z)))
        rings.append(r)

    for l_idx in range(len(head_rings) - 1):
        r1, r2 = rings[l_idx], rings[l_idx + 1]
        for i in range(n_ring):
            inxt = (i + 1) % n_ring
            f = bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))
            f.material_index = 0
            for loop in f.loops:
                loop[uv_lay].uv = (0.5 + loop.vert.co.x * 2.5, 0.5 + (loop.vert.co.z - 1.50) * 2.0)

    apex_top = bm.verts.new((0.0, -0.010, 1.624))
    r_top = rings[-1]
    for i in range(n_ring):
        inxt = (i + 1) % n_ring
        f = bm.faces.new((r_top[inxt], r_top[i], apex_top))
        f.material_index = 0
        for loop in f.loops:
            loop[uv_lay].uv = (0.5 + loop.vert.co.x * 2.5, 0.5 + (loop.vert.co.z - 1.50) * 2.0)

    # Ojos 3D
    eye_radius = 0.0125
    eye_z = 1.508
    eye_x = 0.033
    eye_y = 0.064
    for sign in (1.0, -1.0):
        eye_bm = bmesh.new()
        bmesh.ops.create_uvsphere(eye_bm, u_segments=16, v_segments=12, radius=eye_radius)
        bmesh.ops.translate(eye_bm, verts=eye_bm.verts, vec=(sign * eye_x, eye_y, eye_z))
        v_map = {v: bm.verts.new(v.co) for v in eye_bm.verts}
        for f in eye_bm.faces:
            nf = bm.faces.new([v_map[v] for v in f.verts])
            nf.material_index = 1
        eye_bm.free()

    # -------------------------------------------------------------------------
    # MELENA SETENTERA CANÓNICA ORIGINAL (commit 45957b5: 'fix hair astorga')
    # -------------------------------------------------------------------------
    hair_bm = bmesh.new()
    hair_rings_spec = [
        (1.636, 0.035, 0.030, 0.035, -0.010, 0.00),
        (1.618, 0.070, 0.055, 0.075, -0.010, 0.00),
        (1.592, 0.098, 0.074, 0.102, -0.008, 0.00),
        (1.562, 0.118, 0.080, 0.114, -0.006, 0.20),
        (1.528, 0.126, 0.068, 0.122, -0.006, 0.50),
        (1.490, 0.124, 0.054, 0.120, -0.008, 0.68),
        (1.450, 0.114, 0.040, 0.116, -0.010, 0.80),
        (1.412, 0.098, 0.026, 0.108, -0.012, 0.88),
        (1.380, 0.082, 0.012, 0.098, -0.014, 0.94),
    ]
    n_hverts = 32
    h_rings = []
    for l_idx, (hz, hrx, hry_f, hry_b, hy_off, f_open) in enumerate(hair_rings_spec):
        cur_ring = []
        for i in range(n_hverts):
            ang = (2.0 * math.pi * i) / n_hverts
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            wave = 0.006 * math.sin(ang * 4.0 + l_idx * 0.75) + 0.003 * math.cos(ang * 6.0)
            hx = (hrx + wave) * cos_a
            hy_base = (hry_f if sin_a >= 0 else hry_b) + wave
            hy = hy_base * sin_a + hy_off
            if f_open > 0 and sin_a > 0:
                center_factor = math.exp(-((cos_a / 0.52)**2))
                hy -= f_open * 0.060 * center_factor
                hx *= (1.0 + f_open * 0.14 * center_factor)
            hz_eff = hz + (0.008 * math.sin(ang * 5.0)**2 if l_idx == len(hair_rings_spec) - 1 else 0.0)
            v = hair_bm.verts.new((hx, hy, hz_eff))
            cur_ring.append(v)
        h_rings.append(cur_ring)

    for l_idx in range(len(hair_rings_spec) - 1):
        r1, r2 = h_rings[l_idx], h_rings[l_idx + 1]
        for i in range(n_hverts):
            inxt = (i + 1) % n_hverts
            hair_bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i])).material_index = 2

    apex_hair = hair_bm.verts.new((0.0, -0.010, 1.640))
    r_top_h = h_rings[0]
    for i in range(n_hverts):
        inxt = (i + 1) % n_hverts
        hair_bm.faces.new((r_top_h[i], apex_hair, r_top_h[inxt])).material_index = 2

    def add_bang_layer(p_start, p_mid, p_end, w0=0.030, w1=0.038, w2=0.015, thick=0.010):
        n_s = 6
        p0 = Vector(p_start)
        p1 = Vector(p_mid)
        p2 = Vector(p_end)
        prev_v = None
        for s in range(n_s + 1):
            t = s / float(n_s)
            p = (1.0 - t)**2 * p0 + 2.0 * (1.0 - t) * t * p1 + t**2 * p2
            tang = (2.0 * (1.0 - t) * (p1 - p0) + 2.0 * t * (p2 - p1)).normalized()
            up = Vector((0, 0, 1))
            side = tang.cross(up).normalized()
            nor = side.cross(tang).normalized()
            w = w0 + (w1 - w0) * math.sin(t * math.pi)
            tk = thick * (1.0 - 0.3 * t)
            v_l = hair_bm.verts.new(p - side * (w * 0.5))
            v_c = hair_bm.verts.new(p + nor * tk)
            v_r = hair_bm.verts.new(p + side * (w * 0.5))
            cur_v = [v_l, v_c, v_r]
            if prev_v:
                hair_bm.faces.new((prev_v[0], prev_v[1], cur_v[1], cur_v[0])).material_index = 2
                hair_bm.faces.new((prev_v[1], prev_v[2], cur_v[2], cur_v[1])).material_index = 2
            prev_v = cur_v

    add_bang_layer(( 0.005, 0.064, 1.585), ( 0.045, 0.076, 1.550), ( 0.088, 0.055, 1.510), w0=0.034, w1=0.044, w2=0.020)
    add_bang_layer((-0.005, 0.064, 1.585), (-0.045, 0.076, 1.550), (-0.088, 0.055, 1.510), w0=0.034, w1=0.044, w2=0.020)
    add_bang_layer(( 0.020, 0.062, 1.590), ( 0.065, 0.072, 1.545), ( 0.100, 0.042, 1.490), w0=0.032, w1=0.042, w2=0.020)
    add_bang_layer((-0.020, 0.062, 1.590), (-0.065, 0.072, 1.545), (-0.100, 0.042, 1.490), w0=0.032, w1=0.042, w2=0.020)
    add_bang_layer((-0.010, 0.068, 1.580), ( 0.015, 0.078, 1.555), ( 0.045, 0.068, 1.525), w0=0.024, w1=0.032, w2=0.016)
    add_bang_layer(( 0.075, 0.042, 1.550), ( 0.108, 0.035, 1.500), ( 0.096, 0.015, 1.430), w0=0.028, w1=0.036, w2=0.018, thick=0.012)
    add_bang_layer((-0.075, 0.042, 1.550), (-0.108, 0.035, 1.500), (-0.096, 0.015, 1.430), w0=0.028, w1=0.036, w2=0.018, thick=0.012)

    v_map_h = {v: bm.verts.new(v.co) for v in hair_bm.verts}
    for f in hair_bm.faces:
        nf = bm.faces.new([v_map_h[v] for v in f.verts])
        nf.material_index = 2
        for loop in nf.loops:
            loop[uv_lay].uv = (0.5 + loop.vert.co.x * 2.2, 0.5 + (loop.vert.co.z - 1.50) * 2.2)
    hair_bm.free()

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    for f in bm.faces: f.smooth = True
    bm.to_mesh(me)
    bm.free()

    me.materials.append(mats["Skin"])
    me.materials.append(mats["EyeWhite"])
    me.materials.append(mats["HairBlack"])

    obj = bpy.data.objects.new("Player_Head_Mesh", me)
    bpy.context.scene.collection.objects.link(obj)
    return obj

def build_body_and_hands(mats):
    mesh_graph = bpy.data.meshes.new("Graph_Body")
    obj_body = bpy.data.objects.new("Player_Body_Mesh", mesh_graph)
    bpy.context.scene.collection.objects.link(obj_body)

    # Esqueleto estructural para Skin Modifier
    # Detenemos el brazo en la muñeca (Z = 0.84) para generar las manos y 5 dedos limpios en BMesh
    nodes = [
        # Torso
        ( 0.000, 0.002, 0.76, 0.098, 0.082), # 0: Pelvis
        ( 0.000, 0.002, 0.94, 0.092, 0.078), # 1: Cintura
        ( 0.000, 0.002, 1.08, 0.102, 0.084), # 2: Pecho bajo
        ( 0.000, 0.000, 1.20, 0.114, 0.088), # 3: Pecho medio
        ( 0.000, 0.000, 1.30, 0.118, 0.086), # 4: Clavícula
        ( 0.000, 0.000, 1.34, 0.046, 0.044), # 5: Cuello
        ( 0.000, 0.000, 1.40, 0.042, 0.040), # 6: Cabeza base

        # Brazo L (+X)
        ( 0.180, 0.002, 1.30, 0.052, 0.048), # 7: Hombro L
        ( 0.245, 0.002, 1.26, 0.044, 0.042), # 8: Deltoides L
        ( 0.260, 0.002, 1.12, 0.038, 0.036), # 9: Codo L
        ( 0.270, 0.005, 1.05, 0.034, 0.032), # 10: Codo inf L
        ( 0.280, 0.008, 0.98, 0.030, 0.028), # 11: Antebrazo L
        ( 0.285, 0.010, 0.90, 0.026, 0.024), # 12: Antebrazo bajo L
        ( 0.285, 0.010, 0.84, 0.022, 0.018), # 13: Muñeca L (fin de manga)

        # Brazo R (-X)
        (-0.180, 0.002, 1.30, 0.052, 0.048), # 14: Hombro R
        (-0.245, 0.002, 1.26, 0.044, 0.042), # 15: Deltoides R
        (-0.260, 0.002, 1.12, 0.038, 0.036), # 16: Codo R
        (-0.270, 0.005, 1.05, 0.034, 0.032), # 17: Codo inf R
        (-0.280, 0.008, 0.98, 0.030, 0.028), # 18: Antebrazo R
        (-0.285, 0.010, 0.90, 0.026, 0.024), # 19: Antebrazo bajo R
        (-0.285, 0.010, 0.84, 0.022, 0.018), # 20: Muñeca R (fin de manga)

        # Pierna L (+X)
        ( 0.088, 0.002, 0.76, 0.076, 0.074), # 21: Cadera sup L
        ( 0.090, 0.002, 0.60, 0.070, 0.068), # 22: Muslo medio L
        ( 0.092, 0.000, 0.44, 0.062, 0.060), # 23: Rodilla L
        ( 0.094, 0.000, 0.28, 0.056, 0.054), # 24: Pantorrilla L
        ( 0.096, 0.002, 0.12, 0.048, 0.048), # 25: Tobillo L
        ( 0.096, 0.045, 0.03, 0.050, 0.105), # 26: Zapato formal L

        # Pierna R (-X)
        (-0.088, 0.002, 0.76, 0.076, 0.074), # 27: Cadera sup R
        (-0.090, 0.002, 0.60, 0.070, 0.068), # 28: Muslo medio R
        (-0.092, 0.000, 0.44, 0.062, 0.060), # 29: Rodilla R
        (-0.094, 0.000, 0.28, 0.056, 0.054), # 30: Pantorrilla R
        (-0.096, 0.002, 0.12, 0.048, 0.048), # 31: Tobillo R
        (-0.096, 0.045, 0.03, 0.050, 0.105), # 32: Zapato formal R
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6),
        (4, 7), (7, 8), (8, 9), (9, 10), (10, 11), (11, 12), (12, 13),
        (4, 14), (14, 15), (15, 16), (16, 17), (17, 18), (18, 19), (19, 20),
        (0, 21), (21, 22), (22, 23), (23, 24), (24, 25), (25, 26),
        (0, 27), (27, 28), (28, 29), (29, 30), (30, 31), (31, 32),
    ]

    verts = [Vector((n[0], n[1], n[2])) for n in nodes]
    mesh_graph.from_pydata(verts, edges, [])
    mesh_graph.update()

    bpy.context.view_layer.objects.active = obj_body
    mod_skin = obj_body.modifiers.new(name="Skin", type='SKIN')
    skin_data = mesh_graph.skin_vertices[0].data
    for i, n in enumerate(nodes):
        skin_data[i].radius = (n[3], n[4])

    bpy.ops.object.modifier_apply(modifier="Skin")
    mod_sub = obj_body.modifiers.new(name="Subsurf", type='SUBSURF')
    mod_sub.levels = 1
    bpy.ops.object.modifier_apply(modifier="Subsurf")

    bm = bmesh.new()
    bm.from_mesh(obj_body.data)
    uv_lay = bm.loops.layers.uv.new("UVMap")

    # Asignar materiales: 0: Suit, 1: Pants, 2: Shoes, 3: Skin, 4: Shirt, 5: Tie, 6: Gold
    for p in bm.faces:
        c_median = p.calc_center_median()
        cz, cx, cy = c_median.z, abs(c_median.x), c_median.y
        if cz < 0.12:
            p.material_index = 2 # Zapatos
        elif cz < 0.94 and cx < 0.20:
            p.material_index = 1 # Pantalón
        elif cx > 0.16 or (cz > 1.24 and cx > 0.05):
            if cz < 0.86 and cx > 0.22:
                p.material_index = 4 # Puño vinotinto asomando
            else:
                p.material_index = 0 # Saco
        else:
            if cy > 0.01 and cx < 0.07 and cz >= 0.94:
                p.material_index = 4 # Camisa vinotinto
            else:
                p.material_index = 0
        for loop in p.loops:
            loop[uv_lay].uv = (loop.vert.co.x * 2.0 + 0.5, loop.vert.co.z * 1.5)

    # Cinturón negro y hebilla dorada
    n_pelv = 24
    belt_ring = []
    for i in range(n_pelv):
        ang = (2.0 * math.pi * i) / n_pelv
        vx = 0.124 * math.cos(ang)
        vy = 0.084 * math.sin(ang)
        belt_ring.append(bm.verts.new((vx, vy, 0.942)))
        belt_ring.append(bm.verts.new((vx * 1.012, vy * 1.012, 0.954)))
    for i in range(0, len(belt_ring) - 2, 2):
        bm.faces.new((belt_ring[i], belt_ring[i+1], belt_ring[i+3], belt_ring[i+2])).material_index = 2
    bm.faces.new((belt_ring[-2], belt_ring[-1], belt_ring[1], belt_ring[0])).material_index = 2

    buckle_bm = bmesh.new()
    bmesh.ops.create_cube(buckle_bm, size=1.0)
    bmesh.ops.scale(buckle_bm, verts=buckle_bm.verts, vec=(0.014, 0.003, 0.010))
    bmesh.ops.translate(buckle_bm, verts=buckle_bm.verts, vec=(0.0, 0.088, 0.948))
    for f in buckle_bm.faces:
        nf = bm.faces.new([bm.verts.new(v.co) for v in f.verts])
        nf.material_index = 6
    buckle_bm.free()

    # Cuello y solapas
    n_c = 18
    c_bot, c_top = [], []
    for i in range(n_c):
        ang = (2.0 * math.pi * i) / n_c
        cx = 0.048 * math.cos(ang)
        cy = 0.048 * math.sin(ang) + 0.002
        c_bot.append(bm.verts.new((cx, cy, 1.350)))
        c_top.append(bm.verts.new((cx * 1.08, cy * 1.08, 1.390)))
    for i in range(n_c):
        inxt = (i + 1) % n_c
        bm.faces.new((c_bot[i], c_bot[inxt], c_top[inxt], c_top[i])).material_index = 4

    wing_l = [bm.verts.new((0.005, 0.054, 1.385)), bm.verts.new((0.038, 0.046, 1.378)), bm.verts.new((0.020, 0.068, 1.338))]
    wing_r = [bm.verts.new((-0.005, 0.054, 1.385)), bm.verts.new((-0.020, 0.068, 1.338)), bm.verts.new((-0.038, 0.046, 1.378))]
    bm.faces.new(wing_l).material_index = 4
    bm.faces.new(wing_r).material_index = 4

    # Corbata negra Windsor
    knot_v = [
        bm.verts.new((-0.013, 0.056, 1.380)),
        bm.verts.new(( 0.013, 0.056, 1.380)),
        bm.verts.new(( 0.010, 0.076, 1.340)),
        bm.verts.new((-0.010, 0.076, 1.340)),
        bm.verts.new(( 0.000, 0.084, 1.360)),
    ]
    bm.faces.new((knot_v[0], knot_v[1], knot_v[4])).material_index = 5
    bm.faces.new((knot_v[1], knot_v[2], knot_v[4])).material_index = 5
    bm.faces.new((knot_v[2], knot_v[3], knot_v[4])).material_index = 5
    bm.faces.new((knot_v[3], knot_v[0], knot_v[4])).material_index = 5

    tie_profile = [
        (1.340, 0.010, 0.076),
        (1.270, 0.012, 0.088),
        (1.200, 0.013, 0.092),
        (1.130, 0.013, 0.090),
        (1.070, 0.011, 0.084),
        (1.030, 0.010, 0.080),
        (0.960, 0.008, 0.080),
    ]
    tie_rows = []
    for tz, thw, ty in tie_profile:
        vl = bm.verts.new((-thw, ty, tz))
        vm = bm.verts.new(( 0.000, ty + 0.003, tz))
        vr = bm.verts.new(( thw, ty, tz))
        tie_rows.append((vl, vm, vr))
    for idx in range(len(tie_rows) - 1):
        la, ma, ra = tie_rows[idx]
        lb, mb, rb = tie_rows[idx + 1]
        bm.faces.new((la, ma, mb, lb)).material_index = 5
        bm.faces.new((ma, ra, rb, mb)).material_index = 5

    # Saco sastre exterior 3D separado (Smoking negro)
    suit_specs = [
        (0.74,  0.138,  0.096,   0.096,    0.002,  0.078),
        (0.84,  0.136,  0.094,   0.094,    0.002,  0.052),
        (0.94,  0.132,  0.090,   0.090,    0.002,  0.026),
        (1.00,  0.130,  0.089,   0.089,    0.000,  0.010),
        (1.05,  0.131,  0.090,   0.090,    0.000,  0.005),
        (1.14,  0.138,  0.096,   0.094,   -0.002,  0.026),
        (1.24,  0.146,  0.100,   0.098,   -0.004,  0.048),
        (1.33,  0.146,  0.096,   0.094,   -0.004,  0.064),
    ]
    n_suit_pts = 25
    suit_levels_verts = []
    for (sz, srx, sry_b, sry_f, sy_off, x_op) in suit_specs:
        cur_row = []
        alpha = math.asin(min(0.95, x_op / srx))
        for i in range(n_suit_pts):
            t = i / float(n_suit_pts - 1)
            phi = -alpha - t * (2.0 * math.pi - 2.0 * alpha)
            vx = srx * math.sin(phi)
            ca = math.cos(phi)
            vy = (sry_f if ca >= 0 else sry_b) * ca + sy_off
            cur_row.append(bm.verts.new((vx, vy, sz)))
        suit_levels_verts.append(cur_row)

    for l_idx in range(len(suit_specs) - 1):
        r1, r2 = suit_levels_verts[l_idx], suit_levels_verts[l_idx + 1]
        for i in range(n_suit_pts - 1):
            f = bm.faces.new((r1[i], r1[i+1], r2[i+1], r2[i]))
            f.material_index = 0
            for loop in f.loops:
                loop[uv_lay].uv = (loop.vert.co.x * 2.0 + 0.5, loop.vert.co.z * 1.5)

    for l_idx in range(len(suit_specs) - 1):
        v1_r = suit_levels_verts[l_idx][0]
        v2_r = suit_levels_verts[l_idx + 1][0]
        v1_in = bm.verts.new((v1_r.co.x * 0.95, v1_r.co.y - 0.005, v1_r.co.z))
        v2_in = bm.verts.new((v2_r.co.x * 0.95, v2_r.co.y - 0.005, v2_r.co.z))
        f_r = bm.faces.new((v1_r, v2_r, v2_in, v1_in))
        f_r.material_index = 0

        v1_l = suit_levels_verts[l_idx][-1]
        v2_l = suit_levels_verts[l_idx + 1][-1]
        v1_lin = bm.verts.new((v1_l.co.x * 0.95, v1_l.co.y - 0.005, v1_l.co.z))
        v2_lin = bm.verts.new((v2_l.co.x * 0.95, v2_l.co.y - 0.005, v2_l.co.z))
        f_l = bm.faces.new((v1_l, v1_lin, v2_lin, v2_l))
        f_l.material_index = 0

    r_bot = suit_levels_verts[0]
    for i in range(n_suit_pts - 1):
        v1, v2 = r_bot[i], r_bot[i+1]
        v1_in = bm.verts.new((v1.co.x * 0.96, v1.co.y * 0.96, v1.co.z + 0.006))
        v2_in = bm.verts.new((v2.co.x * 0.96, v2.co.y * 0.96, v2.co.z + 0.006))
        bm.faces.new((v1, v2, v2_in, v1_in)).material_index = 0

    # Solapas notch
    for s_side in (1.0, -1.0):
        lapel_v = [
            bm.verts.new((s_side * 0.040, 0.046, 1.365)),
            bm.verts.new((s_side * 0.088, 0.078, 1.315)),
            bm.verts.new((s_side * 0.092, 0.088, 1.275)),
            bm.verts.new((s_side * 0.078, 0.090, 1.258)),
            bm.verts.new((s_side * 0.088, 0.098, 1.238)),
            bm.verts.new((s_side * 0.016, 0.086, 1.050)),
            bm.verts.new((s_side * 0.034, 0.090, 1.220)),
        ]
        if s_side > 0:
            f1 = bm.faces.new((lapel_v[0], lapel_v[1], lapel_v[2], lapel_v[3]))
            f2 = bm.faces.new((lapel_v[0], lapel_v[3], lapel_v[6]))
            f3 = bm.faces.new((lapel_v[3], lapel_v[4], lapel_v[5], lapel_v[6]))
        else:
            f1 = bm.faces.new((lapel_v[1], lapel_v[0], lapel_v[3], lapel_v[2]))
            f2 = bm.faces.new((lapel_v[3], lapel_v[0], lapel_v[6]))
            f3 = bm.faces.new((lapel_v[4], lapel_v[3], lapel_v[6], lapel_v[5]))
        for f in (f1, f2, f3):
            f.material_index = 0
            for loop in f.loops:
                loop[uv_lay].uv = (loop.vert.co.x * 2.0 + 0.5, loop.vert.co.z * 1.5)

    # Botón de cierre
    btn_bm = bmesh.new()
    bmesh.ops.create_uvsphere(btn_bm, u_segments=8, v_segments=6, radius=0.005)
    bmesh.ops.scale(btn_bm, verts=btn_bm.verts, vec=(1.0, 0.30, 1.0))
    bmesh.ops.translate(btn_bm, verts=btn_bm.verts, vec=(0.006, 0.090, 1.050))
    v_map_b = {v: bm.verts.new(v.co) for v in btn_bm.verts}
    for f in btn_bm.faces:
        bm.faces.new([v_map_b[v] for v in f.verts]).material_index = 6
    btn_bm.free()

    # =========================================================================
    # CONSTRUCCIÓN DE LAS MANOS Y 5 DEDOS ANATÓMICOS DE ALTA RESOLUCIÓN
    # =========================================================================
    # Para cada mano construimos una palma prismática limpia con conexión a la
    # muñeca (Z = 0.84) y 5 dedos diferenciados:
    # - Pulgar: nace a mitad de la palma, grueso (r=0.0072), 2 falanges, oponible
    # - Índice: r=0.0058, largo=0.068
    # - Medio: r=0.0062, largo=0.078 (el más largo con diferencia)
    # - Anular: r=0.0056, largo=0.070
    # - Meñique: r=0.0048, largo=0.052 (visiblemente más corto y estilizado)
    # =========================================================================

    def create_finger_mesh(base_pt, dir_vec, length, radius, n_segments=3, lateral_normal=Vector((1,0,0))):
        """Genera un dedo poligonal de 6 lados con falanges y engrosamiento en nudillos."""
        f_rings = []
        dir_norm = dir_vec.normalized()
        up_norm = dir_norm.cross(lateral_normal).normalized()
        lat_norm = up_norm.cross(dir_norm).normalized()

        for s in range(n_segments + 1):
            t = s / float(n_segments)
            # Conicidad anatómica y sutil curvatura articular
            cur_pt = base_pt + dir_norm * (length * t)
            # Radio decreciente hacia la yema (con pequeño engrosamiento en articulaciones)
            joint_bulge = 0.0006 * math.sin(t * math.pi * (n_segments))
            r_cur = radius * (1.0 - 0.28 * t) + joint_bulge

            ring_v = []
            for k in range(6):
                ang = (2.0 * math.pi * k) / 6.0
                rad_offset = lat_norm * (r_cur * math.cos(ang)) + up_norm * (r_cur * math.sin(ang))
                ring_v.append(bm.verts.new(cur_pt + rad_offset))
            f_rings.append(ring_v)

        for s in range(n_segments):
            r1, r2 = f_rings[s], f_rings[s+1]
            for k in range(6):
                knxt = (k + 1) % 6
                bm.faces.new((r1[k], r1[knxt], r2[knxt], r2[k])).material_index = 3

        # Punta redondeada
        tip_pt = base_pt + dir_norm * (length + radius * 0.40)
        tip_v = bm.verts.new(tip_pt)
        r_last = f_rings[-1]
        for k in range(6):
            knxt = (k + 1) % 6
            bm.faces.new((r_last[knxt], r_last[k], tip_v)).material_index = 3

    for is_l in (True, False):
        sign = 1.0 if is_l else -1.0
        # Muñeca base
        w_center = Vector((sign * 0.285, 0.010, 0.840))

        # 1. Palma de la mano (anatómicamente sólida)
        # Altura: Z = 0.840 a Z = 0.775 (6.5 cm)
        # Ancho Y: -0.030 a +0.030 (6.0 cm)
        # Grosor X: ±0.012 (2.4 cm)
        palm_z_top = 0.840
        palm_z_bot = 0.775

        # Generar prisma de palma conectado
        p_verts = []
        p_corners = [
            # Base muñeca (top)
            Vector((sign * 0.285 - 0.012, -0.018, palm_z_top)),
            Vector((sign * 0.285 + 0.012, -0.018, palm_z_top)),
            Vector((sign * 0.285 + 0.012,  0.022, palm_z_top)),
            Vector((sign * 0.285 - 0.012,  0.022, palm_z_top)),
            # Línea de nudillos (bottom)
            Vector((sign * 0.285 - 0.010, -0.032, palm_z_bot)),
            Vector((sign * 0.285 + 0.010, -0.032, palm_z_bot)),
            Vector((sign * 0.285 + 0.010,  0.032, palm_z_bot)),
            Vector((sign * 0.285 - 0.010,  0.032, palm_z_bot)),
        ]
        bm_p = [bm.verts.new(v) for v in p_corners]

        # Caras laterales de la palma
        bm.faces.new((bm_p[0], bm_p[1], bm_p[5], bm_p[4])).material_index = 3 # Posterior / meñique
        bm.faces.new((bm_p[1], bm_p[2], bm_p[6], bm_p[5])).material_index = 3 # Dorso
        bm.faces.new((bm_p[2], bm_p[3], bm_p[7], bm_p[6])).material_index = 3 # Anterior / índice
        bm.faces.new((bm_p[3], bm_p[0], bm_p[4], bm_p[7])).material_index = 3 # Palma interna
        bm.faces.new((bm_p[0], bm_p[3], bm_p[2], bm_p[1])).material_index = 3 # Tapa muñeca

        # 2. Los 4 Dedos Principales (Meñique, Anular, Medio, Índice)
        # Nacen a lo largo de la línea de nudillos en Z = 0.775
        # En reposo anatómico, los dedos se proyectan hacia abajo (-Z) con suave flexión palmar (-X para mano L, +X para mano R)
        if is_l:
            # Mano L (arco): dedos semi-cerrados envolviendo la nuez del arco
            # Flexión hacia el interior (-X) y ligeramente hacia adelante (+Y)
            f_curl_dir = Vector((-0.55, 0.15, -0.82)).normalized()
            th_dir = Vector((-0.25, -0.40, -0.88)).normalized()
        else:
            # Mano R (violín): dedos flexionados en garra elegante abrazando el mástil
            # Se curvan hacia el interior (+X) y hacia adelante (+Y)
            f_curl_dir = Vector((0.60, 0.25, -0.75)).normalized()
            th_dir = Vector((-0.30, 0.40, -0.86)).normalized()

        # Especificaciones de los 4 dedos: (Nombre, dy_nudillo, largo, radio)
        fingers = [
            ("Pinky",  -0.024, 0.052, 0.0048),
            ("Ring",   -0.008, 0.068, 0.0055),
            ("Middle",  0.008, 0.078, 0.0062),
            ("Index",   0.024, 0.068, 0.0058),
        ]

        for fname, dy, f_len, f_rad in fingers:
            knuckle_pt = Vector((sign * 0.285, dy, palm_z_bot))
            create_finger_mesh(knuckle_pt, f_curl_dir, f_len, f_rad, n_segments=3,
                               lateral_normal=Vector((0, 1, 0)))

        # 3. Quinto Dedo: Pulgar Oponible (Thumb)
        # Nace a mitad de la palma en la cara interna/anterior (Z = 0.815, Y = 0.016)
        th_base = Vector((sign * 0.285 - sign * 0.010, 0.016, 0.815))
        create_finger_mesh(th_base, th_dir, 0.050, 0.0072, n_segments=2,
                           lateral_normal=Vector((0, 0, 1)))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    for f in bm.faces: f.smooth = True

    bm.to_mesh(obj_body.data)
    bm.free()

    for mat_name in ["Suit", "Pants", "Shoes", "Skin", "ShirtWine", "TieBlack", "GoldBuckle"]:
        obj_body.data.materials.append(mats[mat_name])

    return obj_body

def build_skeleton():
    arm_data = bpy.data.armatures.new("Skeleton3D")
    arm_obj = bpy.data.objects.new("Skeleton3D", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = arm_data.edit_bones

    bones_def = [
        ("Root",        None,          (0, 0, 0.00),      (0, 0, 0.76)),
        ("Hips",        "Root",        (0, 0, 0.76),      (0, 0, 0.94)),
        ("Spine",       "Hips",        (0, 0, 0.94),      (0, 0, 1.14)),
        ("Chest",       "Spine",       (0, 0, 1.14),      (0, 0, 1.30)),
        ("Neck",        "Chest",       (0, 0, 1.30),      (0, 0, 1.37)),
        ("Head",        "Neck",        (0, 0, 1.37),      (0, 0, 1.63)),

        ("Shoulder.L",  "Chest",       (0.04, 0, 1.30),   (0.180, 0, 1.300)),
        ("UpperArm.L",  "Shoulder.L",  (0.180, 0, 1.300), (0.245, 0.002, 1.120)),
        ("Forearm.L",   "UpperArm.L",  (0.245, 0.002, 1.120),(0.285, 0.008, 0.900)),
        ("Hand.L",      "Forearm.L",   (0.285, 0.008, 0.900),(0.285, 0.008, 0.74)),

        ("Shoulder.R",  "Chest",       (-0.04, 0, 1.30),  (-0.180, 0, 1.300)),
        ("UpperArm.R",  "Shoulder.R",  (-0.180, 0, 1.300), (-0.245, 0.002, 1.120)),
        ("Forearm.R",   "UpperArm.R",  (-0.245, 0.002, 1.120),(-0.285, 0.008, 0.900)),
        ("Hand.R",      "Forearm.R",   (-0.285, 0.008, 0.900),(-0.285, 0.008, 0.74)),

        ("UpperLeg.L",  "Hips",        (0.088, 0, 0.76),  (0.092, 0, 0.44)),
        ("LowerLeg.L",  "UpperLeg.L",  (0.092, 0, 0.44),  (0.096, 0, 0.12)),
        ("Foot.L",      "LowerLeg.L",  (0.096, 0, 0.12),  (0.096, 0.05, 0.03)),
        ("Toes.L",      "Foot.L",      (0.096, 0.05, 0.03),(0.096, 0.10, 0.00)),

        ("UpperLeg.R",  "Hips",        (-0.088, 0, 0.76), (-0.092, 0, 0.44)),
        ("LowerLeg.R",  "UpperLeg.R",  (-0.092, 0, 0.44), (-0.096, 0, 0.12)),
        ("Foot.R",      "LowerLeg.R",  (-0.096, 0, 0.12), (-0.096, 0.05, 0.03)),
        ("Toes.R",      "Foot.R",      (-0.096, 0.05, 0.03),(-0.096, 0.10, 0.00)),
    ]
    created = {}
    for name, parent, head, tail in bones_def:
        b = edit_bones.new(name)
        b.head = head
        b.tail = tail
        created[name] = b
    for name, parent, head, tail in bones_def:
        if parent: created[name].parent = created[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

def assign_weights(obj, is_head=False):
    bone_names = [
        "Root", "Hips", "Spine", "Chest", "Neck", "Head",
        "Shoulder.L", "UpperArm.L", "Forearm.L", "Hand.L",
        "Shoulder.R", "UpperArm.R", "Forearm.R", "Hand.R",
        "UpperLeg.L", "LowerLeg.L", "Foot.L", "Toes.L",
        "UpperLeg.R", "LowerLeg.R", "Foot.R", "Toes.R"
    ]
    for b in bone_names:
        if b not in obj.vertex_groups: obj.vertex_groups.new(name=b)

    if is_head:
        for v in obj.data.vertices:
            co = v.co
            if co.z < 1.37:
                obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')
            elif co.z < 1.41:
                t = (co.z - 1.37) / 0.04
                obj.vertex_groups["Neck"].add([v.index], 1.0 - t, 'REPLACE')
                obj.vertex_groups["Head"].add([v.index], t, 'REPLACE')
            else:
                obj.vertex_groups["Head"].add([v.index], 1.0, 'REPLACE')
        return

    for v in obj.data.vertices:
        co = v.co
        idx = v.index
        ax = abs(co.x)

        # 1. PIES Y DEDOS
        if co.z < 0.04 and ax <= 0.20:
            obj.vertex_groups["Toes.L" if co.x > 0 else "Toes.R"].add([idx], 1.0, 'REPLACE')
        elif co.z < 0.10 and ax <= 0.20:
            obj.vertex_groups["Foot.L" if co.x > 0 else "Foot.R"].add([idx], 1.0, 'REPLACE')
        elif co.z < 0.14 and ax <= 0.20:
            t_f = (co.z - 0.10) / 0.04
            side = ".L" if co.x > 0 else ".R"
            obj.vertex_groups["Foot" + side].add([idx], 1.0 - t_f, 'REPLACE')
            obj.vertex_groups["LowerLeg" + side].add([idx], t_f, 'REPLACE')

        # 2. EXTREMIDADES SUPERIORES (BRAZOS Y MANOS CON DEDOS)
        elif ax > 0.16 and co.z < 1.38:
            side = ".L" if co.x > 0 else ".R"
            if co.z < 0.85:
                # TODA la mano (palma y 5 dedos) sujeta rígidamente al hueso Hand
                obj.vertex_groups["Hand" + side].add([idx], 1.0, 'REPLACE')
            elif co.z < 0.88:
                t_w = (co.z - 0.85) / 0.03
                obj.vertex_groups["Forearm" + side].add([idx], t_w, 'REPLACE')
                obj.vertex_groups["Hand" + side].add([idx], 1.0 - t_w, 'REPLACE')
            elif co.z < 1.08:
                obj.vertex_groups["Forearm" + side].add([idx], 1.0, 'REPLACE')
            elif co.z < 1.16:
                t_e = (co.z - 1.08) / 0.08
                obj.vertex_groups["Forearm" + side].add([idx], 1.0 - t_e, 'REPLACE')
                obj.vertex_groups["UpperArm" + side].add([idx], t_e, 'REPLACE')
            else:
                obj.vertex_groups["UpperArm" + side].add([idx], 1.0, 'REPLACE')

        # 3. EXTREMIDADES INFERIORES (PIERNAS)
        elif co.z < 0.40:
            obj.vertex_groups["LowerLeg.L" if co.x > 0 else "LowerLeg.R"].add([idx], 1.0, 'REPLACE')
        elif co.z < 0.48:
            t_k = (co.z - 0.40) / 0.08
            side = ".L" if co.x > 0 else ".R"
            obj.vertex_groups["LowerLeg" + side].add([idx], 1.0 - t_k, 'REPLACE')
            obj.vertex_groups["UpperLeg" + side].add([idx], t_k, 'REPLACE')
        elif co.z < 0.76 and ax > 0.02:
            obj.vertex_groups["UpperLeg.L" if co.x > 0 else "UpperLeg.R"].add([idx], 1.0, 'REPLACE')

        # 4. PELVIS, COLUMNA Y PECHO
        elif co.z < 0.94:
            obj.vertex_groups["Hips"].add([idx], 1.0, 'REPLACE')
        elif co.z < 1.14:
            obj.vertex_groups["Spine"].add([idx], 1.0, 'REPLACE')
        else:
            obj.vertex_groups["Chest"].add([idx], 1.0, 'REPLACE')

def attach_armature(obj, arm_obj):
    mod = obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj
    obj.parent = arm_obj

def apply_pose_and_setup_scene():
    scene = bpy.context.scene
    arm = bpy.data.objects["Skeleton3D"]
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)

    # 1. Torso y cabeza con porte natural y sereno
    arm.pose.bones['Spine'].rotation_euler = (math.radians(-1), math.radians(-1), math.radians(1))
    arm.pose.bones['Chest'].rotation_euler = (math.radians(-2), math.radians(-3), math.radians(2))
    arm.pose.bones['Head'].rotation_euler = (math.radians(-1), math.radians(4), math.radians(1))

    # 2. Brazo violinista (Hand.R, -X, en pantalla a la derecha):
    # Sostiene el mástil del violín erguido junto al hombro/cuello
    # Orientamos la mano para que el dorso y los 4 dedos miren hacia el frente (cámara)
    arm.pose.bones['Shoulder.R'].rotation_euler = (math.radians(2), math.radians(3), math.radians(-3))
    arm.pose.bones['UpperArm.R'].rotation_euler = (math.radians(40), math.radians(18), math.radians(-28))
    arm.pose.bones['Forearm.R'].rotation_euler = (math.radians(96), math.radians(22), math.radians(-12))
    arm.pose.bones['Hand.R'].rotation_euler = (math.radians(24), math.radians(-12), math.radians(45))

    # 3. Brazo del arco (Hand.L, +X, en pantalla a la izquierda):
    # Sostiene el arco junto a la cintura/cadera
    arm.pose.bones['Shoulder.L'].rotation_euler = (math.radians(-1), math.radians(-2), math.radians(1))
    arm.pose.bones['UpperArm.L'].rotation_euler = (math.radians(12), math.radians(-4), math.radians(8))
    arm.pose.bones['Forearm.L'].rotation_euler = (math.radians(26), math.radians(-6), math.radians(4))
    arm.pose.bones['Hand.L'].rotation_euler = (math.radians(14), math.radians(12), math.radians(-8))

    # 4. Piernas en contrapposto sutil
    arm.pose.bones['UpperLeg.L'].rotation_euler = (math.radians(-3), math.radians(2), math.radians(4))
    arm.pose.bones['LowerLeg.L'].rotation_euler = (math.radians(5), 0, 0)
    arm.pose.bones['Foot.L'].rotation_euler = (math.radians(-2), math.radians(-3), math.radians(-4))

    arm.pose.bones['UpperLeg.R'].rotation_euler = (math.radians(1), math.radians(-1), math.radians(-2))
    arm.pose.bones['Foot.R'].rotation_euler = (math.radians(-1), math.radians(2), math.radians(2))

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_obj = bpy.data.objects["Player_Body_Mesh"]
    body_eval = body_obj.evaluated_get(depsgraph)
    mesh_eval = body_eval.to_mesh()

    vg_r = body_obj.vertex_groups.get("Hand.R")
    hand_r_verts = [v.co for v in mesh_eval.vertices if any(g.group == vg_r.index and g.weight > 0.4 for g in body_obj.data.vertices[v.index].groups)]
    avg_hand_r = sum(hand_r_verts, Vector((0,0,0))) / max(1, len(hand_r_verts))

    vg_l = body_obj.vertex_groups.get("Hand.L")
    hand_l_verts = [v.co for v in mesh_eval.vertices if any(g.group == vg_l.index and g.weight > 0.4 for g in body_obj.data.vertices[v.index].groups)]
    avg_hand_l = sum(hand_l_verts, Vector((0,0,0))) / max(1, len(hand_l_verts))
    body_eval.to_mesh_clear()

    # Cargar Violín y Arco
    if os.path.exists(VIOLIN_BLEND):
        with bpy.data.libraries.load(VIOLIN_BLEND, link=False) as (data_from, data_to):
            data_to.objects = [o for o in data_from.objects if o in ("Violin_Prop", "Violin_Bow")]
        for o in data_to.objects:
            if o:
                scene.collection.objects.link(o)
                for p in o.data.polygons: p.use_smooth = True
                if o.name == "Violin_Prop":
                    o.scale = (0.76, 0.76, 0.76)
                    rot_v = Euler((math.radians(-72), math.radians(164), math.radians(22)), 'XYZ')
                    o.rotation_euler = rot_v
                    # Calibración milimétrica: el mástil descansa en la palma y los 4 dedos abrazan el frente
                    neck_local = Vector((0.0, 0.42, 0.010))
                    neck_world_vec = rot_v.to_matrix() @ (Vector(o.scale) * neck_local)
                    # Colocar el violín ligeramente desplazado hacia la izquierda del personaje (-X) para que los dedos queden al frente
                    o.location = avg_hand_r - neck_world_vec + Vector((-0.016, -0.012, -0.010))
                elif o.name == "Violin_Bow":
                    o.scale = (0.72, 0.72, 0.72)
                    rot_b = Euler((math.radians(44), math.radians(-24), math.radians(52)), 'XYZ')
                    o.rotation_euler = rot_b
                    # La vara pasa por el interior de los 4 dedos cerrados y el pulgar
                    grip_local = Vector((0.0, 0.07, 0.0))
                    grip_world_vec = rot_b.to_matrix() @ (Vector(o.scale) * grip_local)
                    o.location = avg_hand_l - grip_world_vec + Vector((0.005, 0.006, 0.002))

    return avg_hand_r, avg_hand_l

def setup_lights(scene):
    # Luces de estudio
    head_t = (-0.02, 0.0, 1.48)
    chest_t = (-0.02, 0.0, 1.18)

    def add_light(name, ltype, power, loc, target, col=(1,1,1), size=1.0):
        l_data = bpy.data.lights.new(name, ltype)
        l_data.energy = power
        l_data.color = col
        if ltype == 'AREA': l_data.size = size
        l_obj = bpy.data.objects.new(name, l_data)
        scene.collection.objects.link(l_obj)
        l_obj.location = Vector(loc)
        l_obj.rotation_euler = (Vector(target) - l_obj.location).to_track_quat('-Z', 'Y').to_euler()
        return l_obj

    add_light('KeyLight', 'AREA', 240.0, (-1.2, 1.8, 1.6), chest_t, (1.0, 0.88, 0.72), size=1.2)
    add_light('FillLight', 'AREA', 110.0, (1.2, 1.8, 1.3), head_t, (0.92, 0.96, 1.0), size=2.0)
    add_light('RimLight', 'SPOT', 180.0, (0.2, -1.3, 1.9), head_t, (1.0, 0.98, 0.92))
    add_light('DetailLight', 'AREA', 60.0, (-0.1, 2.0, 1.2), chest_t, (1.0, 0.98, 0.96), size=1.0)

def main():
    scene = reset_scene()
    mats = create_materials()
    head = build_head(mats)
    body = build_body_and_hands(mats)
    arm = build_skeleton()

    assign_weights(head, is_head=True)
    assign_weights(body, is_head=False)
    attach_armature(head, arm)
    attach_armature(body, arm)

    avg_hand_r, avg_hand_l = apply_pose_and_setup_scene()
    setup_lights(scene)

    cam_data = bpy.data.cameras.new("TestCam")
    cam_data.lens = 75.0
    cam_obj = bpy.data.objects.new("TestCam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # 1. Close-up de la Mano del Violín (Hand.R)
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800
    cam_obj.location = avg_hand_r + Vector((-0.15, 0.70, 0.05))
    cam_obj.rotation_euler = (avg_hand_r - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
    out_violin_hand = os.path.join(SCRATCH_DIR, "test_hand_violin_closeup.png")
    scene.render.filepath = out_violin_hand
    bpy.ops.render.render(write_still=True)
    print(f"✓ Close-up mano violín: {out_violin_hand}")

    # 2. Close-up de la Mano del Arco (Hand.L)
    cam_obj.location = avg_hand_l + Vector((0.15, 0.70, 0.05))
    cam_obj.rotation_euler = (avg_hand_l - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
    out_bow_hand = os.path.join(SCRATCH_DIR, "test_hand_bow_closeup.png")
    scene.render.filepath = out_bow_hand
    bpy.ops.render.render(write_still=True)
    print(f"✓ Close-up mano arco: {out_bow_hand}")

    # 3. Vista de Busto / Tarjeta
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    cam_obj.location = Vector((-0.22, 2.15, 1.25))
    target = Vector((-0.02, 0.0, 1.22))
    cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
    out_icon = os.path.join(SCRATCH_DIR, "test_astorga_icon_v2.png")
    scene.render.filepath = out_icon
    bpy.ops.render.render(write_still=True)
    print(f"✓ Vista icono v2: {out_icon}")

if __name__ == "__main__":
    main()
