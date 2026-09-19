import re

with open("scripts/generate_bbva_tecate.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update Guajardo corner plinth to -1.20 m
code = code.replace(
    "add_wall_segment(bm_tower, -0.40, 4.20, 4.20, -0.40, 0.0, 0.40, thickness=0.45)",
    "add_wall_segment(bm_tower, -0.40, 4.20, 4.20, -0.40, -1.20, 0.40, thickness=0.45)"
)
code = code.replace(
    "add_box(bm_tower, -0.40, 0.40, 4.15, 4.25, 0.0, H_tower)",
    "add_box(bm_tower, -0.40, 0.40, 4.15, 4.25, -1.20, H_tower)"
)
code = code.replace(
    "add_box(bm_tower, 4.15, 4.25, -0.40, 0.40, 0.0, H_tower)",
    "add_box(bm_tower, 4.15, 4.25, -0.40, 0.40, -1.20, H_tower)"
)

# 2. Update Juárez facade plinth to -1.20 m
code = code.replace(
    "add_box(bm_struct, X_start, X_end, -0.05, 0.40, 0.0, 0.40)",
    "add_box(bm_struct, X_start, X_end, -0.05, 0.40, -1.20, 0.40)"
)
code = code.replace(
    "add_box(bm_struct, 21.80, 22.80, -0.04, 0.40, 0.40, H_wall)",
    "add_box(bm_struct, 21.80, 22.80, -0.04, 0.40, -1.20, H_wall)"
)

# 3. Update Cárdenas facade: plinth, Cajero enclosure, Dentista enclosure
old_cardenas_plinth = """    # 1. Plinto basal continuo (Z = 0.0 a 0.40)
    # Excluye el vano de la escalera de Dentista en [25.80, 28.20]
    add_box(bm_struct, -0.05, 0.40, Y_start, 25.80, 0.0, 0.40)
    add_box(bm_struct, -0.05, 0.40, 28.20, Y_max, 0.0, 0.40)"""

new_cardenas_plinth = """    # 1. Plinto basal continuo enterrado (Z = -1.20 a 0.40 para absorber pendiente de Cárdenas)
    # Excluye el vano de la escalera de Dentista en [25.80, 28.20]
    add_box(bm_struct, -0.05, 0.40, Y_start, 25.80, -1.20, 0.40)
    add_box(bm_struct, -0.05, 0.40, 28.20, Y_max, -1.20, 0.40)"""

code = code.replace(old_cardenas_plinth, new_cardenas_plinth)

code = code.replace(
    'add_box(bm_dent_mosaic, -0.05, 0.40, 29.40, Y_max, 0.0, H_wall)',
    'add_box(bm_dent_mosaic, -0.05, 0.40, 29.40, Y_max, -1.20, H_wall)'
)

code = code.replace(
    'add_box(bm_struct, -0.05, 16.0, Y_max, Y_max + 0.30, 0.0, H_wall)',
    'add_box(bm_struct, -0.05, 4.20, Y_max, Y_max + 0.30, -1.20, H_wall)'
)

# 3.1 Cajero and Dentista bay enclosures in build_west_facade_cardenas
old_cardenas_bays = """        # Planta Baja
        if idx == 2:
            # Crujía 3: PORTAL DE ACCESO A CAJERO AUTOMÁTICO (Ground Truth media_1789778253725)
            # "Estos elementos van 1 ventanal a la derecha. Entre el cajero y el dentista hay 2 ventanales. El cajero va en el lado izquierdo de su ventanal."
            # Puerta acristalada en el lado izquierdo (norte) del vano: y in [15.20, 16.60]
            add_box(bm_alum, 0.04, 0.14, 15.20, 16.60, 0.40, 0.46)
            add_box(bm_alum, 0.04, 0.14, 15.20, 16.60, 2.70, 2.76)
            add_box(bm_alum, 0.04, 0.14, 15.20, 15.26, 0.40, 2.76)
            add_box(bm_alum, 0.04, 0.14, 16.54, 16.60, 0.40, 2.76)
            add_box(bm_glass, 0.08, 0.09, 15.26, 16.54, 0.46, 2.70)
            # Jaladera tubular de la puerta
            add_box(bm_alum, -0.02, 0.06, 15.32, 15.36, 1.00, 1.40)
            
            # Ventana lateral con persianas en el resto del vano: y in [13.20, 15.10]
            add_box(bm_alum, 0.04, 0.12, 13.20, 15.10, 0.40, 0.45)
            add_box(bm_alum, 0.04, 0.12, 13.20, 15.10, 3.15, 3.20)
            add_box(bm_alum, 0.04, 0.12, 13.20, 13.25, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, 15.05, 15.10, 0.40, 3.20)
            add_box(bm_glass, 0.075, 0.085, 13.25, 15.05, 0.45, 3.15)
            add_box(bm_blind, 0.135, 0.145, 13.25, 15.05, 0.45, 3.15)
            
        elif idx == 5:
            # Crujía 6: ACCESO DENTISTA (Ground Truth media_1789778345732)
            # Zaguán rehundido hacia el interior (X = 0.0 a 3.20, Y = [25.80, 28.20])
            # Escalera de 4 peldaños de concreto
            stair_w = (25.85, 28.15)
            add_box(bm_dent_stair, 0.20, 3.20, stair_w[0], stair_w[1], 0.0, 0.18)
            add_box(bm_dent_stair, 0.60, 3.20, stair_w[0], stair_w[1], 0.18, 0.36)
            add_box(bm_dent_stair, 1.00, 3.20, stair_w[0], stair_w[1], 0.36, 0.54)
            add_box(bm_dent_stair, 1.40, 3.20, stair_w[0], stair_w[1], 0.54, 0.72)
            
            # Muros interiores del zaguán
            add_box(bm_dent_stair, 0.0, 3.20, 25.75, 25.85, 0.0, 3.20) # Muro sur zaguán
            add_box(bm_dent_stair, 0.0, 3.20, 28.15, 28.25, 0.0, 3.20) # Muro norte zaguán
            add_box(bm_dent_stair, 0.0, 3.20, 25.75, 28.25, 3.20, 3.30) # Techo falso zaguán
            
            # Puerta acristalada interior al fondo del zaguán (X = 3.15, Y = [26.40, 27.80])
            add_box(bm_alum, 3.12, 3.18, 26.40, 27.80, 0.72, 2.72)
            add_box(bm_glass, 3.14, 3.16, 26.46, 27.74, 0.78, 2.66)
            
            # Ventanal lateral exterior a la derecha del acceso: Y in [28.25, 29.35]
            add_box(bm_alum, 0.04, 0.12, 28.25, 29.35, 0.40, 0.45)
            add_box(bm_alum, 0.04, 0.12, 28.25, 29.35, 3.15, 3.20)
            add_box(bm_alum, 0.04, 0.12, 28.25, 28.30, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, 29.30, 29.35, 0.40, 3.20)
            add_box(bm_glass, 0.075, 0.085, 28.30, 29.30, 0.45, 3.15)
            add_box(bm_blind, 0.135, 0.145, 28.30, 29.30, 0.45, 3.15)"""

new_cardenas_bays = """        # Planta Baja
        if idx == 2:
            # Crujía 3: PORTAL DE ACCESO A CAJERO AUTOMÁTICO (Sellado hermético sin aberturas)
            # Ventana lateral con persianas en lado sur: y in [13.20, 15.20]
            add_box(bm_alum, 0.04, 0.12, 13.20, 15.20, 0.40, 0.45)
            add_box(bm_alum, 0.04, 0.12, 13.20, 15.20, 3.15, 3.20)
            add_box(bm_alum, 0.04, 0.12, 13.20, 13.25, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, 15.15, 15.20, 0.40, 3.20)
            my_atm_w = (13.20 + 15.20) * 0.5
            add_box(bm_alum, 0.04, 0.12, my_atm_w - 0.02, my_atm_w + 0.02, 0.40, 3.20)
            add_box(bm_glass, 0.075, 0.085, 13.25, 15.15, 0.45, 3.15)
            add_box(bm_blind, 0.135, 0.145, 13.25, 15.15, 0.45, 3.15)

            # Puerta acristalada de acceso a cajeros: y in [15.20, 16.60], Z in [0.40, 2.65]
            add_box(bm_alum, 0.04, 0.14, 15.20, 16.60, 0.40, 0.46)
            add_box(bm_alum, 0.04, 0.14, 15.20, 16.60, 2.65, 2.71)
            add_box(bm_alum, 0.04, 0.14, 15.20, 15.26, 0.40, 2.65)
            add_box(bm_alum, 0.04, 0.14, 16.54, 16.60, 0.40, 2.65)
            add_box(bm_glass, 0.08, 0.09, 15.26, 16.54, 0.46, 2.65)
            # Jaladera tubular de la puerta
            add_box(bm_alum, -0.02, 0.06, 15.32, 15.36, 1.00, 1.40)
            
            # Montante superior de vidrio sobre la puerta: Z in [2.71, 3.20] (cierra el hueco superior)
            add_box(bm_alum, 0.04, 0.14, 15.20, 16.60, 3.15, 3.20)
            add_box(bm_alum, 0.04, 0.14, 15.20, 15.26, 2.71, 3.20)
            add_box(bm_alum, 0.04, 0.14, 16.54, 16.60, 2.71, 3.20)
            add_box(bm_glass, 0.08, 0.09, 15.26, 16.54, 2.71, 3.15)
            
            # Machón derecho de crujía: y in [16.60, 16.80]
            add_box(bm_struct, 0.0, 0.35, 16.60, 16.80, 0.40, 3.20)
            # Muro ciego interior detrás de portal cajero: Z in [2.65, 4.30] (evita ver el interior abierto)
            add_box(bm_struct, 0.05, 0.30, 15.15, 16.65, 2.65, 4.30)
            
        elif idx == 5:
            # Crujía 6: ACCESO DENTISTA (Sellado hermético continuo y recibidor con peldaños)
            # Muro ciego en estuco blanco continuo de PB a PA en X in [0.0, 0.35], Y in [25.80, 29.40] detrás de fascia
            add_box(bm_struct, 0.0, 0.35, 25.80, 29.40, 3.20, 5.10)
            
            # Recibidor / zaguán rehundido hacia el interior (X in [0.0, 3.15], Y in [25.80, 28.20])
            stair_w = (25.85, 28.15)
            add_box(bm_dent_stair, 0.20, 3.15, stair_w[0], stair_w[1], 0.0, 0.18)
            add_box(bm_dent_stair, 0.60, 3.15, stair_w[0], stair_w[1], 0.18, 0.36)
            add_box(bm_dent_stair, 1.00, 3.15, stair_w[0], stair_w[1], 0.36, 0.54)
            add_box(bm_dent_stair, 1.40, 3.15, stair_w[0], stair_w[1], 0.54, 0.72)
            
            # Muros interiores y techo del zaguán
            add_box(bm_dent_stair, 0.0, 3.20, 25.75, 25.85, 0.0, 3.20) # Muro sur zaguán
            add_box(bm_dent_stair, 0.0, 3.20, 28.15, 28.25, 0.0, 3.20) # Muro norte zaguán
            add_box(bm_dent_stair, 0.0, 3.20, 25.75, 28.25, 3.20, 3.30) # Techo falso zaguán
            
            # Fondo del zaguán (X = 3.15): Muro con puerta acristalada interior (X = 3.15, Y in [26.40, 27.80])
            add_box(bm_dent_stair, 3.15, 3.30, 25.80, 26.40, 0.72, 3.20) # Muro izq fondo
            add_box(bm_dent_stair, 3.15, 3.30, 27.80, 28.20, 0.72, 3.20) # Muro der fondo
            add_box(bm_dent_stair, 3.15, 3.30, 26.40, 27.80, 2.70, 3.20) # Dintel sobre puerta interior
            add_box(bm_alum, 3.12, 3.18, 26.40, 27.80, 0.72, 2.70)
            add_box(bm_glass, 3.14, 3.16, 26.46, 27.74, 0.78, 2.65)
            
            # Ventanal lateral exterior a la derecha del acceso: Y in [28.25, 29.35]
            add_box(bm_alum, 0.04, 0.12, 28.25, 29.35, 0.40, 0.45)
            add_box(bm_alum, 0.04, 0.12, 28.25, 29.35, 3.15, 3.20)
            add_box(bm_alum, 0.04, 0.12, 28.25, 28.30, 0.40, 3.20)
            add_box(bm_alum, 0.04, 0.12, 29.30, 29.35, 0.40, 3.20)
            add_box(bm_glass, 0.075, 0.085, 28.30, 29.30, 0.45, 3.15)
            add_box(bm_blind, 0.135, 0.145, 28.30, 29.30, 0.45, 3.15)"""

code = code.replace(old_cardenas_bays, new_cardenas_bays)

# 3.2 Extend cobalt blue fascia across full width of Crujía 6 (behind and beside DENTISTA)
old_cardenas_dent_fascia = """    # Área azul sobre la fachada misma en Crujía 6 arriba del alero (Comentario 5: "DENTISTA va sobre la fachada del edificio mismo, arriba de donde empieza este ala. Esa área va del mismo azul.")
    add_box(bm_fascia_b, -0.14, 0.02, 25.75, 28.25, 3.25, 4.30)"""

new_cardenas_dent_fascia = """    # Área azul continua en Crujía 6 cubriendo toda la pared detrás y al lado de DENTISTA (Y in [25.75, 29.40])
    add_box(bm_fascia_b, -0.14, 0.02, 25.75, 29.40, 3.20, 4.30)"""

code = code.replace(old_cardenas_dent_fascia, new_cardenas_dent_fascia)

# 4. Replace build_east_facade_and_parking and add build_south_and_inward_arc_facade
old_east_def_start = "def build_east_facade_and_parking(mats, col):"
old_sidewalk_def_start = "def build_optional_sidewalk(mats, col):"

idx1 = code.find(old_east_def_start)
idx2 = code.find(old_sidewalk_def_start)

new_east_and_south_code = '''def build_east_facade_and_parking(mats, col):
    """Construye la Fachada Este ampliada proporcionalmente a 25.20 m (Cárdenas menos Dentista)
    con 7 crujías modulares en PA y PB, sin aberturas traseras ni estructuras parásitas (Ground Truth media_1789783721505)."""
    bm_east = bmesh.new()
    bm_alum = bmesh.new()
    bm_glass = bmesh.new()
    bm_blind = bmesh.new()
    bm_hvac = bmesh.new()
    
    X_east = 22.80
    Y_east_max = 25.20  # Ampliada exactamente a 25.20 m (Cárdenas 30.00 m - Dentista 4.80 m)
    H_wall = 7.10
    
    # 1. Muro Este principal (Z = -1.20 a 7.10, Y = 0.40 a 25.20)
    add_box(bm_east, X_east - 0.40, X_east, 0.40, Y_east_max, -1.20, 0.40) # Zócalo enterrado continuo
    add_box(bm_east, X_east - 0.40, X_east, 0.40, Y_east_max, 3.20, 5.10)  # Faja intermedia
    add_box(bm_east, X_east - 0.40, X_east, 0.40, Y_east_max, 6.75, H_wall) # Remate
    add_box(bm_east, X_east - 0.45, X_east + 0.05, 0.40, Y_east_max, 7.10, 7.25) # Albardilla coping
    
    # Losa interior de azotea hermética para el bloque principal
    add_box(bm_east, 4.20, X_east, 0.40, Y_east_max, 7.00, 7.25)
    add_box(bm_east, 0.40, 4.20, 4.20, 30.00, 7.00, 7.25) # Losa ala Cárdenas
    
    # 2. 7 Crujías modulares a lo largo de los 25.20 m
    e_bays = [
        (0.80, 3.60),
        (4.20, 7.00),
        (7.60, 10.40),
        (11.00, 13.80),
        (14.40, 17.20),
        (17.80, 20.60),
        (21.20, 24.60)
    ]
    
    # Machones en planta alta y planta baja
    add_box(bm_east, X_east - 0.40, X_east, 0.40, 0.80, 0.40, H_wall)
    for i in range(len(e_bays) - 1):
        add_box(bm_east, X_east - 0.40, X_east, e_bays[i][1], e_bays[i+1][0], 0.40, H_wall)
    add_box(bm_east, X_east - 0.40, X_east, 24.60, Y_east_max, 0.40, H_wall)
    
    # Cancelería y vidrios en PA Este (3 hojas verticales y travesaño horizontal en Z = 6.25)
    for y1, y2 in e_bays:
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y2, 5.10, 5.15)
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y2, 6.70, 6.75)
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y1 + 0.04, 5.10, 6.75)
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, y2 - 0.04, y2, 5.10, 6.75)
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y2, 6.25, 6.28) # Travesaño horizontal
        step_e = (y2 - y1) / 3.0
        m1 = y1 + step_e
        m2 = y1 + 2.0 * step_e
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, m1 - 0.02, m1 + 0.02, 5.10, 6.75)
        add_box(bm_alum, X_east - 0.10, X_east - 0.02, m2 - 0.02, m2 + 0.02, 5.10, 6.75)
        add_box(bm_glass, X_east - 0.07, X_east - 0.05, y1 + 0.04, y2 - 0.04, 5.15, 6.70)
        
    # Planta Baja Este: Escaparates comerciales y puerta peatonal de servicio en Crujía 3
    for idx_pb, (y1, y2) in enumerate(e_bays):
        if idx_pb == 2:
            # Crujía 3: Puerta peatonal de servicio con montante de vidrio
            add_box(bm_east, X_east - 0.40, X_east, y1, y2, 3.15, 3.20)
            door_y1 = y1 + 0.35
            door_y2 = y2 - 0.35
            add_box(bm_east, X_east - 0.40, X_east, y1, door_y1, 0.40, 3.20)
            add_box(bm_east, X_east - 0.40, X_east, door_y2, y2, 0.40, 3.20)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, door_y1, door_y2, 0.40, 0.45)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, door_y1, door_y2, 2.55, 2.60)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, door_y1, door_y2, 3.10, 3.15)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, door_y1, door_y1 + 0.04, 0.40, 3.15)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, door_y2 - 0.04, door_y2, 0.40, 3.15)
            add_box(bm_glass, X_east - 0.07, X_east - 0.05, door_y1 + 0.04, door_y2 - 0.04, 0.45, 2.55)
            add_box(bm_glass, X_east - 0.07, X_east - 0.05, door_y1 + 0.04, door_y2 - 0.04, 2.60, 3.10)
        else:
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y2, 0.40, 0.45)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y2, 3.15, 3.20)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, y1, y1 + 0.04, 0.40, 3.20)
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, y2 - 0.04, y2, 0.40, 3.20)
            my_pb = (y1 + y2) * 0.5
            add_box(bm_alum, X_east - 0.10, X_east - 0.02, my_pb - 0.025, my_pb + 0.025, 0.40, 3.20)
            add_box(bm_glass, X_east - 0.07, X_east - 0.05, y1 + 0.04, y2 - 0.04, 0.45, 3.15)
            add_box(bm_blind, X_east - 0.14, X_east - 0.13, y1 + 0.04, y2 - 0.04, 0.45, 3.15)

    # Luminarias tipo aplique / sconce exterior sobre los machones de PB
    for y_lamp in [3.90, 7.30, 10.70, 14.10, 17.50, 20.90]:
        add_box(bm_alum, X_east - 0.02, X_east + 0.10, y_lamp - 0.03, y_lamp + 0.03, 2.68, 2.72)
        add_box(bm_alum, X_east + 0.08, X_east + 0.22, y_lamp - 0.06, y_lamp + 0.06, 2.58, 2.78)

    # Casetas HVAC en azotea
    add_box(bm_hvac, 7.00, 11.50, 15.00, 19.50, 7.15, 8.65)
    add_box(bm_hvac, 8.50, 10.50, 9.00, 11.50, 7.15, 8.10)
    add_box(bm_hvac, 11.00, 13.00, 9.00, 11.50, 7.15, 8.10)

    bmesh.ops.recalc_face_normals(bm_hvac, faces=bm_hvac.faces)
    m_hv = bpy.data.meshes.new("Mesh_Roof_HVAC")
    bm_hvac.to_mesh(m_hv)
    bm_hvac.free()
    obj_hvac = bpy.data.objects.new("Roof_HVAC_Units", m_hv)
    col.objects.link(obj_hvac)
    obj_hvac.data.materials.append(mats["acero"])

    # Convertir muro este a objeto
    bmesh.ops.recalc_face_normals(bm_east, faces=bm_east.faces)
    m_east = bpy.data.meshes.new("Mesh_East_Wall")
    bm_east.to_mesh(m_east)
    bm_east.free()
    obj_east = bpy.data.objects.new("East_Parking_Estructura", m_east)
    col.objects.link(obj_east)
    obj_east.data.materials.append(mats["muro"])
    obj_east.data.materials.append(mats["zocalo"])
    obj_east.data.materials.append(mats["azotea"])
    for p in m_east.polygons:
        c_z = sum(m_east.vertices[v].co.z for v in p.vertices) / len(p.vertices)
        if c_z > 7.05:
            p.material_index = 2
        elif c_z < 0.42:
            p.material_index = 1
        else:
            p.material_index = 0

    # Convertir cancelería y vidrios este
    bmesh.ops.recalc_face_normals(bm_alum, faces=bm_alum.faces)
    m_al_e = bpy.data.meshes.new("Mesh_East_Canceleria")
    bm_alum.to_mesh(m_al_e)
    bm_alum.free()
    obj_al_e = bpy.data.objects.new("East_Canceleria", m_al_e)
    col.objects.link(obj_al_e)
    obj_al_e.data.materials.append(mats["aluminio"])

    bmesh.ops.recalc_face_normals(bm_glass, faces=bm_glass.faces)
    m_gl_e = bpy.data.meshes.new("Mesh_East_Vidrio")
    bm_glass.to_mesh(m_gl_e)
    bm_glass.free()
    obj_gl_e = bpy.data.objects.new("East_Vidrio", m_gl_e)
    col.objects.link(obj_gl_e)
    obj_gl_e.data.materials.append(mats["vidrio"])

    bmesh.ops.recalc_face_normals(bm_blind, faces=bm_blind.faces)
    m_bl_e = bpy.data.meshes.new("Mesh_East_Persianas")
    bm_blind.to_mesh(m_bl_e)
    bm_blind.free()
    obj_bl_e = bpy.data.objects.new("East_Persianas", m_bl_e)
    col.objects.link(obj_bl_e)
    obj_bl_e.data.materials.append(mats["persianas"])

    # Rótulo de despacho en PA ventana 1 ('LICENCIADO EN DERECHO')
    f_ed = bpy.data.curves.new(type="FONT", name="Font_E_Despacho")
    f_ed.body = "LICENCIADO EN DERECHO"
    f_ed.size = 0.10
    f_ed.extrude = 0.006
    f_ed.align_x = 'CENTER'
    o_ed = bpy.data.objects.new("East_Txt_Despacho", f_ed)
    col.objects.link(o_ed)
    o_ed.location = (X_east + 0.02, 1.75, 6.42)
    o_ed.rotation_euler = (math.radians(90.0), 0.0, math.radians(90.0))
    o_ed.data.materials.append(mats["rotulo_blanco"])

    # 3. Elementos del Estacionamiento: Rampa peatonal/vehicular, barandal, caseta y muro perimetral
    bm_ramp = bmesh.new()
    add_box(bm_ramp, X_east + 0.60, X_east + 4.50, 0.0, 14.0, -0.45, 0.05)
    rx = X_east + 4.55
    add_box(bm_ramp, rx - 0.15, rx, 0.0, 14.0, 0.0, 0.90) # Murete lateral
    bmesh.ops.recalc_face_normals(bm_ramp, faces=bm_ramp.faces)
    m_rp = bpy.data.meshes.new("Mesh_Rampa_Suelo")
    bm_ramp.to_mesh(m_rp)
    bm_ramp.free()
    obj_ramp = bpy.data.objects.new("Rampa_Estacionamiento", m_rp)
    col.objects.link(obj_ramp)
    obj_ramp.data.materials.append(mats["zocalo"])

    # Barandilla de acero blanco
    bm_rail = bmesh.new()
    add_box(bm_rail, rx - 0.09, rx - 0.06, 0.0, 14.0, 1.65, 1.70)
    add_box(bm_rail, rx - 0.08, rx - 0.07, 0.0, 14.0, 1.25, 1.28)
    for py in [0.4, 3.4, 6.4, 9.4, 12.4, 13.9]:
        add_box(bm_rail, rx - 0.10, rx - 0.05, py - 0.03, py + 0.03, 0.90, 1.65)
    bmesh.ops.recalc_face_normals(bm_rail, faces=bm_rail.faces)
    m_rl = bpy.data.meshes.new("Mesh_Rampa_Barandal")
    bm_rail.to_mesh(m_rl)
    bm_rail.free()
    obj_rail = bpy.data.objects.new("Rampa_Barandal_Blanco", m_rl)
    col.objects.link(obj_rail)
    obj_rail.data.materials.append(mats["barandal"])

    # Caseta de vigilancia blanca
    bm_caseta = bmesh.new()
    add_box(bm_caseta, X_east + 4.80, X_east + 7.00, 6.0, 8.8, 0.0, 2.70)
    add_box(bm_caseta, X_east + 4.65, X_east + 7.15, 5.85, 8.95, 2.70, 2.85) # Tejadillo
    bmesh.ops.recalc_face_normals(bm_caseta, faces=bm_caseta.faces)
    m_cs = bpy.data.meshes.new("Mesh_Caseta_Blanca")
    bm_caseta.to_mesh(m_cs)
    bm_caseta.free()
    obj_caseta = bpy.data.objects.new("Caseta_Vigilancia_Blanca", m_cs)
    col.objects.link(obj_caseta)
    obj_caseta.data.materials.append(mats["muro"])

    # Muro perimetral del estacionamiento
    bm_pwall = bmesh.new()
    add_box(bm_pwall, X_east + 7.20, X_east + 12.50, 5.80, 6.05, 0.0, 2.40)
    add_box(bm_pwall, X_east + 8.20, X_east + 9.80, 5.75, 5.82, 1.40, 1.95)
    bmesh.ops.recalc_face_normals(bm_pwall, faces=bm_pwall.faces)
    m_pw = bpy.data.meshes.new("Mesh_Parking_Wall")
    bm_pwall.to_mesh(m_pw)
    bm_pwall.free()
    obj_pwall = bpy.data.objects.new("Parking_Perimeter_Wall", m_pw)
    col.objects.link(obj_pwall)
    obj_pwall.data.materials.append(mats["muro"])
    obj_pwall.data.materials.append(mats["senal_azul"])
    for p in m_pw.polygons:
        c_x = sum(m_pw.vertices[v].co.x for v in p.vertices) / len(p.vertices)
        if c_x > X_east + 8.0:
            p.material_index = 1
        else:
            p.material_index = 0

    # Letrero oficial 'ENTRADA BBVA ->' ortogonal hacia Av. Juárez
    bm_sign = bmesh.new()
    sx = X_east + 5.90
    sy = 3.50
    add_box(bm_sign, sx - 0.04, sx + 0.04, sy - 0.04, sy + 0.04, 0.0, 2.20)
    add_box(bm_sign, sx - 0.60, sx + 0.60, sy - 0.03, sy + 0.03, 1.70, 2.30)
    bmesh.ops.recalc_face_normals(bm_sign, faces=bm_sign.faces)
    m_sn = bpy.data.meshes.new("Mesh_Senal_Entrada_Ortogonal")
    bm_sign.to_mesh(m_sn)
    bm_sign.free()
    obj_sign = bpy.data.objects.new("Senal_Entrada_BBVA_Ortogonal", m_sn)
    col.objects.link(obj_sign)
    obj_sign.data.materials.append(mats["senal_azul"])

    f_sign = bpy.data.curves.new(type="FONT", name="Font_Senal_Rampa_Ort")
    f_sign.body = "ENTRADA\\nBBVA ➔"
    f_sign.size = 0.16
    f_sign.extrude = 0.01
    f_sign.align_x = 'CENTER'
    o_sign = bpy.data.objects.new("Texto_Senal_Rampa_Ort", f_sign)
    col.objects.link(o_sign)
    o_sign.location = (sx, sy - 0.04, 2.10)
    o_sign.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    o_sign.data.materials.append(mats["rotulo_blanco"])

    return obj_east, [obj_al_e, obj_gl_e, obj_bl_e, o_ed, obj_hvac, obj_pwall], obj_ramp, obj_rail, obj_caseta, obj_sign, o_sign

def build_south_and_inward_arc_facade(mats, col):
    """Construye la Fachada Sur lisa (X in [0.0, 17.40], Y = 25.20) y la pared en arco cóncava
    hacia adentro que sella con la fachada del estacionamiento (X in [17.40, 22.80]),
    con pilar central delgado y 2 ventanas rectangulares superiores (Ground Truth media_1789784140324)."""
    bm_south = bmesh.new()
    bm_alum = bmesh.new()
    bm_glass = bmesh.new()
    bm_roof_arc = bmesh.new()
    
    Y_south = 25.20
    X_east = 22.80
    X_arc_start = 17.40
    H_wall = 7.10
    
    # 1. FACHADA SUR LISA (X = 0.0 a 17.40, Y = 25.20)
    # Longitud exacta 17.40 m (idéntica a la distancia donde termina el azul BBVA en Juárez)
    # Plinto basal enterrado (Z = -1.20 a 0.40)
    add_box(bm_south, 0.0, X_arc_start, Y_south - 0.35, Y_south + 0.05, -1.20, 0.40)
    # Muro liso de estuco blanco continuo (Z = 0.40 a H_wall = 7.10)
    add_box(bm_south, 0.0, X_arc_start, Y_south - 0.35, Y_south, 0.40, H_wall)
    # Moldura intermedia horizontal a Z = 3.20 (visible en Ground Truth media_1789784140324)
    add_box(bm_south, -0.05, X_arc_start + 0.05, Y_south - 0.02, Y_south + 0.10, 3.20, 3.32)
    # Albardilla / Coping superior del pretil (Z = 7.10 a 7.25)
    add_box(bm_south, -0.05, X_arc_start + 0.05, Y_south - 0.40, Y_south + 0.05, 7.10, 7.25)
    
    # 2. PARED EN ARCO HACIA ADENTRO (CÓNCAVA) (X = 17.40 a 22.80, ancho = 5.40 m)
    # Sagitta / flecha hacia adentro en -Y: profundidad de 1.35 m
    n_segs = 16
    arc_pts = []
    for s in range(n_segs + 1):
        u = s / float(n_segs)
        px = X_arc_start + (X_east - X_arc_start) * u
        py = Y_south - 1.35 * math.sin(math.pi * u)
        arc_pts.append((px, py))
        
    thick = 0.35
    for s in range(n_segs):
        x1, y1 = arc_pts[s]
        x2, y2 = arc_pts[s + 1]
        
        dx = x2 - x1
        dy = y2 - y1
        L = math.hypot(dx, dy)
        if L > 0:
            nx = -dy / L * thick
            ny = dx / L * thick
        else:
            nx, ny = 0.0, -thick
            
        # Plinto basal (Z = -1.20 a 0.40)
        v_b1 = bm_south.verts.new((x1, y1, -1.20))
        v_b2 = bm_south.verts.new((x2, y2, -1.20))
        v_b3 = bm_south.verts.new((x2 + nx, y2 + ny, -1.20))
        v_b4 = bm_south.verts.new((x1 + nx, y1 + ny, -1.20))
        
        v_t1 = bm_south.verts.new((x1, y1, 0.40))
        v_t2 = bm_south.verts.new((x2, y2, 0.40))
        v_t3 = bm_south.verts.new((x2 + nx, y2 + ny, 0.40))
        v_t4 = bm_south.verts.new((x1 + nx, y1 + ny, 0.40))
        
        bm_south.faces.new((v_b1, v_b2, v_t2, v_t1))
        bm_south.faces.new((v_b2, v_b3, v_t3, v_t2))
        bm_south.faces.new((v_b3, v_b4, v_t4, v_t3))
        bm_south.faces.new((v_b4, v_b1, v_t1, v_t4))
        
        # Muro principal (Z = 0.40 a 7.10)
        v_w1 = bm_south.verts.new((x1, y1, H_wall))
        v_w2 = bm_south.verts.new((x2, y2, H_wall))
        v_w3 = bm_south.verts.new((x2 + nx, y2 + ny, H_wall))
        v_w4 = bm_south.verts.new((x1 + nx, y1 + ny, H_wall))
        
        bm_south.faces.new((v_t1, v_t2, v_w2, v_w1))
        bm_south.faces.new((v_t2, v_t3, v_w3, v_w2))
        bm_south.faces.new((v_t3, v_t4, v_w4, v_w3))
        bm_south.faces.new((v_t4, v_t1, v_w1, v_w4))
        bm_south.faces.new((v_w1, v_w2, v_w3, v_w4)) # Tapa pretil
        
        # Losa de techo detrás del arco (sellado hermético de azotea Z = 7.00 - 7.25)
        vr1 = bm_roof_arc.verts.new((x1 + nx, y1 + ny, 7.00))
        vr2 = bm_roof_arc.verts.new((x2 + nx, y2 + ny, 7.00))
        vr3 = bm_roof_arc.verts.new((x2 + nx, Y_south, 7.00))
        vr4 = bm_roof_arc.verts.new((x1 + nx, Y_south, 7.00))
        bm_roof_arc.faces.new((vr1, vr2, vr3, vr4))
        vr1t = bm_roof_arc.verts.new((x1 + nx, y1 + ny, 7.25))
        vr2t = bm_roof_arc.verts.new((x2 + nx, y2 + ny, 7.25))
        vr3t = bm_roof_arc.verts.new((x2 + nx, Y_south, 7.25))
        vr4t = bm_roof_arc.verts.new((x1 + nx, Y_south, 7.25))
        bm_roof_arc.faces.new((vr4t, vr3t, vr2t, vr1t))

    # 3. PILAR DELGADO EN MEDIO (Ground Truth media_1789784140324)
    px_mid = 20.10
    py_mid = 23.85
    add_box(bm_south, px_mid - 0.16, px_mid + 0.16, py_mid - 0.35, py_mid + 0.20, -1.20, 7.35)

    # 4. DOS VENTANAS RECTANGULARES PEQUEÑAS EN PLANTA ALTA (Ground Truth media_1789784140324)
    # Ventana 1 (Izquierda / Oeste del pilar)
    w1_x1, w1_x2 = 18.35, 19.55
    w1_y = 24.32
    add_box(bm_south, w1_x1 - 0.08, w1_x2 + 0.08, w1_y - 0.10, w1_y + 0.15, 5.30, 5.42)
    add_box(bm_alum, w1_x1, w1_x2, w1_y - 0.05, w1_y + 0.05, 5.42, 5.46)
    add_box(bm_alum, w1_x1, w1_x2, w1_y - 0.05, w1_y + 0.05, 6.30, 6.35)
    add_box(bm_alum, w1_x1, w1_x1 + 0.04, w1_y - 0.05, w1_y + 0.05, 5.42, 6.35)
    add_box(bm_alum, w1_x2 - 0.04, w1_x2, w1_y - 0.05, w1_y + 0.05, 5.42, 6.35)
    add_box(bm_glass, w1_x1 + 0.04, w1_x2 - 0.04, w1_y + 0.02, w1_y + 0.10, 5.48, 6.28)

    # Ventana 2 (Derecha / Este del pilar)
    w2_x1, w2_x2 = 20.65, 21.85
    w2_y = 24.32
    add_box(bm_south, w2_x1 - 0.08, w2_x2 + 0.08, w2_y - 0.10, w2_y + 0.15, 5.30, 5.42)
    add_box(bm_alum, w2_x1, w2_x2, w2_y - 0.05, w2_y + 0.05, 5.42, 5.46)
    add_box(bm_alum, w2_x1, w2_x2, w2_y - 0.05, w2_y + 0.05, 6.30, 6.35)
    add_box(bm_alum, w2_x1, w2_x1 + 0.04, w2_y - 0.05, w2_y + 0.05, 5.42, 6.35)
    add_box(bm_alum, w2_x2 - 0.04, w2_x2, w2_y - 0.05, w2_y + 0.05, 5.42, 6.35)
    add_box(bm_glass, w2_x1 + 0.04, w2_x2 - 0.04, w2_y - 0.02, w2_y + 0.02, 5.48, 6.28)

    bmesh.ops.recalc_face_normals(bm_south, faces=bm_south.faces)
    m_sth = bpy.data.meshes.new("Mesh_South_Inward_Arc")
    bm_south.to_mesh(m_sth)
    bm_south.free()
    obj_south = bpy.data.objects.new("South_Inward_Arc_Wall", m_sth)
    col.objects.link(obj_south)
    obj_south.data.materials.append(mats["muro"])
    obj_south.data.materials.append(mats["zocalo"])
    for p in m_sth.polygons:
        c_z = sum(m_sth.vertices[v].co.z for v in p.vertices) / len(p.vertices)
        if c_z < 0.42:
            p.material_index = 1
        else:
            p.material_index = 0
            
    bmesh.ops.recalc_face_normals(bm_roof_arc, faces=bm_roof_arc.faces)
    m_rf = bpy.data.meshes.new("Mesh_Roof_Arc_Closure")
    bm_roof_arc.to_mesh(m_rf)
    bm_roof_arc.free()
    obj_rf = bpy.data.objects.new("Roof_Arc_Closure", m_rf)
    col.objects.link(obj_rf)
    obj_rf.data.materials.append(mats["azotea"])
    
    bmesh.ops.recalc_face_normals(bm_alum, faces=bm_alum.faces)
    m_al = bpy.data.meshes.new("Mesh_South_Arc_Canceleria")
    bm_alum.to_mesh(m_al)
    bm_alum.free()
    obj_al = bpy.data.objects.new("South_Arc_Canceleria", m_al)
    col.objects.link(obj_al)
    obj_al.data.materials.append(mats["aluminio"])
    
    bmesh.ops.recalc_face_normals(bm_glass, faces=bm_glass.faces)
    m_gl = bpy.data.meshes.new("Mesh_South_Arc_Vidrio")
    bm_glass.to_mesh(m_gl)
    bm_glass.free()
    obj_gl = bpy.data.objects.new("South_Arc_Vidrio", m_gl)
    col.objects.link(obj_gl)
    obj_gl.data.materials.append(mats["vidrio"])
    
    return obj_south, [obj_rf, obj_al, obj_gl]

'''

code = code[:idx1] + new_east_and_south_code + code[idx2:]

# 5. Update build_optional_sidewalk: skirt to -1.20 m
code = code.replace(
    "add_box(bm_sw, -3.80, X_east + 8.00, -3.80, 0.0, 0.0, 0.18)",
    "add_box(bm_sw, -3.80, X_east + 8.00, -3.80, 0.0, -1.20, 0.18)"
)
code = code.replace(
    "add_box(bm_sw, -3.80, 0.0, 0.0, Y_cardenas + 2.00, 0.0, 0.18)",
    "add_box(bm_sw, -3.80, 0.0, 0.0, Y_cardenas + 2.00, -1.20, 0.18)"
)
code = code.replace(
    "add_box(bm_sw, -3.88, X_east + 8.00, -3.88, -3.76, 0.0, 0.20)",
    "add_box(bm_sw, -3.88, X_east + 8.00, -3.88, -3.76, -1.20, 0.20)"
)
code = code.replace(
    "add_box(bm_sw, -3.88, -3.76, -3.88, Y_cardenas + 2.00, 0.0, 0.20)",
    "add_box(bm_sw, -3.88, -3.76, -3.88, Y_cardenas + 2.00, -1.20, 0.20)"
)

# 6. Add camera c8 in setup_lighting_and_render
old_c7_code = """    c7 = bpy.data.objects.new("Cam_East_GT", cam_data)
    col.objects.link(c7)
    c7.location = (32.0, 5.0, 2.2)
    dir7 = Vector((22.8, 12.0, 3.8)) - c7.location
    c7.rotation_euler = dir7.to_track_quat('-Z', 'Y').to_euler()
    cams["east_ground_truth"] = c7

    return cams"""

new_c7_and_c8_code = """    c7 = bpy.data.objects.new("Cam_East_GT", cam_data)
    col.objects.link(c7)
    c7.location = (32.0, 5.0, 2.2)
    dir7 = Vector((22.8, 12.0, 3.8)) - c7.location
    c7.rotation_euler = dir7.to_track_quat('-Z', 'Y').to_euler()
    cams["east_ground_truth"] = c7

    # Cámara 8: Perspectiva Sur hacia el Arco Cóncavo (Ground Truth media_1789784140324)
    c8 = bpy.data.objects.new("Cam_South_Arc", cam_data)
    col.objects.link(c8)
    c8.location = (20.10, 32.50, 4.20)
    dir8 = Vector((20.10, 24.20, 3.80)) - c8.location
    c8.rotation_euler = dir8.to_track_quat('-Z', 'Y').to_euler()
    cams["south_inward_arc"] = c8

    return cams"""

code = code.replace(old_c7_code, new_c7_and_c8_code)

# 7. Update generate_godot_tscn
old_tscn_func_start = "def generate_godot_tscn(tscn_path, glb_rel_path):"
old_main_func_start = "def main():"
idx_tscn = code.find(old_tscn_func_start)
idx_main = code.find(old_main_func_start)

new_tscn_code = '''def generate_godot_tscn(tscn_path, glb_rel_path):
    """Genera la escena .tscn de Godot 4 con StaticBody3D y colisiones analíticas precisas sin barreras invisibles."""
    tscn_content = f"""[gd_scene load_steps=22 format=3 uid="uid://bbva_tecate_centro_009"]

[ext_resource type="PackedScene" path="{glb_rel_path}" id="1_mesh"]
[ext_resource type="PackedScene" path="res://assets/buildings/banqueta_bbva_tecate.glb" id="2_banqueta"]

[sub_resource type="BoxShape3D" id="BoxShape3D_juarez"]
size = Vector3(18.6, 8.5, 16.0)

[sub_resource type="BoxShape3D" id="BoxShape3D_cardenas_bank"]
size = Vector3(16.0, 8.5, 21.0)

[sub_resource type="BoxShape3D" id="BoxShape3D_dentista_south"]
size = Vector3(3.2, 8.5, 0.6)

[sub_resource type="BoxShape3D" id="BoxShape3D_dentista_north"]
size = Vector3(3.2, 8.5, 1.8)

[sub_resource type="BoxShape3D" id="BoxShape3D_dentista_back"]
size = Vector3(12.8, 8.5, 4.8)

[sub_resource type="BoxShape3D" id="BoxShape3D_dentista_step_1"]
size = Vector3(0.40, 0.18, 2.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_dentista_step_2"]
size = Vector3(0.40, 0.36, 2.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_dentista_step_3"]
size = Vector3(0.40, 0.54, 2.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_dentista_step_4"]
size = Vector3(1.75, 0.72, 2.30)

[sub_resource type="BoxShape3D" id="BoxShape3D_puertas"]
size = Vector3(5.8, 9.1, 0.35)

[sub_resource type="BoxShape3D" id="BoxShape3D_south_wall"]
size = Vector3(17.4, 8.5, 0.4)

[sub_resource type="BoxShape3D" id="BoxShape3D_inward_arc_1"]
size = Vector3(3.0, 8.5, 0.4)

[sub_resource type="BoxShape3D" id="BoxShape3D_inward_arc_2"]
size = Vector3(3.0, 8.5, 0.4)

[sub_resource type="BoxShape3D" id="BoxShape3D_east_wall"]
size = Vector3(0.4, 8.5, 25.2)

[sub_resource type="BoxShape3D" id="BoxShape3D_rampa_murete"]
size = Vector3(0.3, 1.7, 14.0)

[sub_resource type="BoxShape3D" id="BoxShape3D_rampa_floor"]
size = Vector3(4.4, 0.2, 14.0)

[sub_resource type="BoxShape3D" id="BoxShape3D_banqueta_juarez"]
size = Vector3(34.6, 0.18, 3.8)

[sub_resource type="BoxShape3D" id="BoxShape3D_banqueta_cardenas"]
size = Vector3(3.8, 0.18, 32.0)

[node name="BBVA_Tecate" type="StaticBody3D"]

[node name="ModelInstance" parent="." instance=ExtResource("1_mesh")]

[node name="BanquetaInstance" parent="." instance=ExtResource("2_banqueta")]

[node name="Col_Juarez" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 13.5, 3.05, -8.0)
shape = SubResource("BoxShape3D_juarez")

[node name="Col_Cardenas_Bank" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 8.0, 3.05, -14.7)
shape = SubResource("BoxShape3D_cardenas_bank")

[node name="Col_Dentista_South" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.6, 3.05, -25.5)
shape = SubResource("BoxShape3D_dentista_south")

[node name="Col_Dentista_North" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.6, 3.05, -29.1)
shape = SubResource("BoxShape3D_dentista_north")

[node name="Col_Dentista_Interior" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 9.6, 3.05, -27.6)
shape = SubResource("BoxShape3D_dentista_back")

[node name="Col_Dentista_Step_1" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.40, 0.09, -27.0)
shape = SubResource("BoxShape3D_dentista_step_1")

[node name="Col_Dentista_Step_2" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.80, 0.18, -27.0)
shape = SubResource("BoxShape3D_dentista_step_2")

[node name="Col_Dentista_Step_3" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 1.20, 0.27, -27.0)
shape = SubResource("BoxShape3D_dentista_step_3")

[node name="Col_Dentista_Step_4" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 2.275, 0.36, -27.0)
shape = SubResource("BoxShape3D_dentista_step_4")

[node name="Col_Puertas_Chamfer" type="CollisionShape3D" parent="."]
transform = Transform3D(0.707107, 0, 0.707107, 0, 1, 0, -0.707107, 0, 0.707107, 2.12, 4.55, -2.12)
shape = SubResource("BoxShape3D_puertas")

[node name="Col_South_Wall" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 8.7, 3.05, -25.0)
shape = SubResource("BoxShape3D_south_wall")

[node name="Col_Inward_Arc_1" type="CollisionShape3D" parent="."]
transform = Transform3D(0.9063, 0, -0.4226, 0, 1, 0, 0.4226, 0, 0.9063, 18.75, 3.05, -24.5)
shape = SubResource("BoxShape3D_inward_arc_1")

[node name="Col_Inward_Arc_2" type="CollisionShape3D" parent="."]
transform = Transform3D(0.9063, 0, 0.4226, 0, 1, 0, -0.4226, 0, 0.9063, 21.45, 3.05, -24.5)
shape = SubResource("BoxShape3D_inward_arc_2")

[node name="Col_East_Wall" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 22.6, 3.05, -12.6)
shape = SubResource("BoxShape3D_east_wall")

[node name="Col_Rampa_Murete" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 27.35, 0.85, -7.0)
shape = SubResource("BoxShape3D_rampa_murete")

[node name="Col_Rampa_Floor" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 25.0, -0.1, -7.0)
shape = SubResource("BoxShape3D_rampa_floor")

[node name="Col_Banqueta_Juarez" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 13.5, 0.09, 1.9)
shape = SubResource("BoxShape3D_banqueta_juarez")

[node name="Col_Banqueta_Cardenas" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -1.9, 0.09, -16.0)
shape = SubResource("BoxShape3D_banqueta_cardenas")
"""
    with open(tscn_path, "w", encoding="utf-8") as f:
        f.write(tscn_content)
    print(f"--> Escena Godot generada: {tscn_path}")

'''

code = code[:idx_tscn] + new_tscn_code + code[idx_main:]

# 8. Update main() to invoke build_south_and_inward_arc_facade and add south_inward_arc render
old_main_calls = """    # 4. Fachada Este (Estacionamiento), rampa, caseta y letrero ortogonal
    obj_east, objs_east_win, obj_ramp, obj_rail, obj_caseta, obj_sign, o_sign_r = build_east_facade_and_parking(mats, root_col)
    
    # 5. Banqueta modular independiente (opcional)"""

new_main_calls = """    # 4. Fachada Este (Estacionamiento), rampa, caseta y letrero ortogonal
    obj_east, objs_east_win, obj_ramp, obj_rail, obj_caseta, obj_sign, o_sign_r = build_east_facade_and_parking(mats, root_col)
    
    # 5. Fachada Sur lisa y pared en arco hacia adentro (Ground Truth media_1789784140324)
    obj_south, objs_south_arc = build_south_and_inward_arc_facade(mats, root_col)
    
    # 6. Banqueta modular independiente (opcional)"""

code = code.replace(old_main_calls, new_main_calls)

# Add south_inward_arc to renders in main()
old_renders_list = """        ("east_ground_truth", "docs/images/bbva/bbva_east_ground_truth.png", 1280, 720),
        ("aerial_top", "docs/images/bbva/bbva_aerial_top.png", 1024, 1024)"""

new_renders_list = """        ("east_ground_truth", "docs/images/bbva/bbva_east_ground_truth.png", 1280, 720),
        ("south_inward_arc", "docs/images/bbva/bbva_south_inward_arc.png", 1280, 720),
        ("aerial_top", "docs/images/bbva/bbva_aerial_top.png", 1024, 1024)"""

code = code.replace(old_renders_list, new_renders_list)

with open("scripts/generate_bbva_tecate.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Successfully applied V7.0 changes to scripts/generate_bbva_tecate.py")
