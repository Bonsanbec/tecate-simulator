#!/usr/bin/env python3
"""
scratch/apply_roof_and_cam_fix.py
1. Corrige las losas de azotea para que sellen herméticamente toda la planta sin huecos visibles en vista cenital.
2. Calibra Cam_South_Inward_Arc para capturar la cara sur, el arco con pilar y ventanas, y el cierre angulado a 45º matching media_1789784140324.
"""

def main():
    script_path = "scripts/generate_bbva_tecate.py"
    with open(script_path, "r", encoding="utf-8") as f:
        code = f.read()

    # 1. Losas de azotea en build_east_facade_and_parking
    old_east_slabs = '''    # Losa interior de azotea hermética
    add_box(bm_east, 4.20, X_east, 0.40, Y_east_max, 7.00, 7.25)
    add_box(bm_east, 0.40, 4.20, 4.20, 30.00, 7.00, 7.25) # Losa ala Cárdenas'''

    new_east_slabs = '''    # Losa interior de azotea hermética
    # Bloque Sur hasta la pared sur lisa (X = 4.20 a 17.40, Y = 0.40 a 25.20)
    add_box(bm_east, 4.20, 17.40, 0.40, 25.20, 7.00, 7.25)
    # Bloque Este hasta la fachada este (X = 17.40 a X_east, Y = 0.40 a Y_east_max)
    add_box(bm_east, 17.40, X_east, 0.40, Y_east_max, 7.00, 7.25)
    # Losa ala Cárdenas (X = 0.40 a 4.20, Y = 4.20 a 30.00)
    add_box(bm_east, 0.40, 4.20, 4.20, 30.00, 7.00, 7.25)'''

    if old_east_slabs in code:
        code = code.replace(old_east_slabs, new_east_slabs)
        print("Losas este actualizadas correctamente.")
    else:
        print("ADVERTENCIA: old_east_slabs no encontrado.")

    # 2. Losas de azotea en build_south_and_inward_arc_facade
    old_arc_roof = '''        # Losa de azotea hermética detrás del arco
        vr1 = bm_roof_arc.verts.new((x1, y1, 7.00))
        vr2 = bm_roof_arc.verts.new((x2, y2, 7.00))
        vr3 = bm_roof_arc.verts.new((x2, Y_south, 7.00))
        vr4 = bm_roof_arc.verts.new((x1, Y_south, 7.00))
        bm_roof_arc.faces.new((vr1, vr2, vr3, vr4))
        vr1t = bm_roof_arc.verts.new((x1, y1, 7.25))
        vr2t = bm_roof_arc.verts.new((x2, y2, 7.25))
        vr3t = bm_roof_arc.verts.new((x2, Y_south, 7.25))
        vr4t = bm_roof_arc.verts.new((x1, Y_south, 7.25))
        bm_roof_arc.faces.new((vr4t, vr3t, vr2t, vr1t))'''

    new_arc_roof = '''        # Losa de azotea hermética detrás del arco (conecta con Y = 20.80 de la losa este)
        vr1 = bm_roof_arc.verts.new((x1, y1, 7.00))
        vr2 = bm_roof_arc.verts.new((x2, y2, 7.00))
        vr3 = bm_roof_arc.verts.new((x2, 20.80, 7.00))
        vr4 = bm_roof_arc.verts.new((x1, 20.80, 7.00))
        bm_roof_arc.faces.new((vr1, vr2, vr3, vr4))
        vr1t = bm_roof_arc.verts.new((x1, y1, 7.25))
        vr2t = bm_roof_arc.verts.new((x2, y2, 7.25))
        vr3t = bm_roof_arc.verts.new((x2, 20.80, 7.25))
        vr4t = bm_roof_arc.verts.new((x1, 20.80, 7.25))
        bm_roof_arc.faces.new((vr4t, vr3t, vr2t, vr1t))'''

    if old_arc_roof in code:
        code = code.replace(old_arc_roof, new_arc_roof)
        print("Losa de arco actualizada correctamente.")
    else:
        print("ADVERTENCIA: old_arc_roof no encontrado.")

    # 3. Cámara Cam_South_Inward_Arc
    old_c8 = '''    # 8. Cámara 'South_Inward_Arc': Perspectiva hacia el arco cóncavo posterior y cierre angulado a 45º
    c8_data = bpy.data.cameras.new("Cam_South_Inward_Arc")
    c8_data.lens = 30
    c8 = bpy.data.objects.new("Cam_South_Inward_Arc", c8_data)
    col.objects.link(c8)
    loc8 = Vector((15.20, 32.50, 2.50))
    tgt8 = Vector((19.80, 22.80, 3.80))
    dir8 = tgt8 - loc8
    c8.location = loc8
    c8.rotation_euler = dir8.to_track_quat('-Z', 'Y').to_euler()
    cams["south_inward_arc"] = c8'''

    new_c8 = '''    # 8. Cámara 'South_Inward_Arc': Perspectiva hacia el arco cóncavo posterior y cierre angulado a 45º
    c8_data = bpy.data.cameras.new("Cam_South_Inward_Arc")
    c8_data.lens = 28
    c8 = bpy.data.objects.new("Cam_South_Inward_Arc", c8_data)
    col.objects.link(c8)
    loc8 = Vector((17.50, 34.50, 2.40))
    tgt8 = Vector((19.80, 22.50, 3.80))
    dir8 = tgt8 - loc8
    c8.location = loc8
    c8.rotation_euler = dir8.to_track_quat('-Z', 'Y').to_euler()
    cams["south_inward_arc"] = c8'''

    if old_c8 in code:
        code = code.replace(old_c8, new_c8)
        print("Cámara 8 actualizada correctamente.")
    else:
        print("ADVERTENCIA: old_c8 no encontrado.")

    with open(script_path, "w", encoding="utf-8") as f:
        f.write(code)
    print("Script scripts/generate_bbva_tecate.py actualizado.")

if __name__ == "__main__":
    main()
