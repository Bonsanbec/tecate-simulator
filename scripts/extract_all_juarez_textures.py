"""
Extractor y Generador de Texturas Históricas Fotorrealistas para Av. Benito Juárez 235 (2009)
=============================================================================================
Extrae quirúrgicamente swatches, rótulos, fascias y murales fotográficos de alta fidelidad
de los panoramas de terreno de 2009 almacenados en scratch/staging/juarez_235/ y los exporta a
godot_project/assets/textures/ y blender_assets/textures/.
"""

import os
import bpy
import numpy as np

OUT_DIRS = [
    os.path.abspath("godot_project/assets/textures"),
    os.path.abspath("blender_assets/textures"),
]

for d in OUT_DIRS:
    os.makedirs(d, exist_ok=True)

def get_pixels(path):
    if not os.path.exists(path):
        print(f"ADVERTENCIA: No se encuentra {path}")
        return None, 0, 0
    img = bpy.data.images.load(os.path.abspath(path))
    w, h = img.size
    p = np.array(img.pixels[:], dtype=np.float32).reshape((h, w, 4))
    # Invertir verticalmente para que fila 0 sea la parte superior
    return p[::-1, :, :], w, h

def save_crop(arr_top_down, name):
    p_blender = arr_top_down[::-1, :, :]
    h, w, c = p_blender.shape
    for out_dir in OUT_DIRS:
        filepath = os.path.join(out_dir, name)
        if name in bpy.data.images:
            bpy.data.images.remove(bpy.data.images[name])
        b_img = bpy.data.images.new(name, width=w, height=h, alpha=True, float_buffer=False)
        b_img.pixels = p_blender.flatten().tolist()
        b_img.filepath_raw = filepath
        b_img.file_format = 'PNG'
        b_img.save()
        print(f"  Guardado: {filepath} ({w}x{h})")

def main():
    print("=== INICIANDO EXTRACCIÓN QUIRÚRGICA DE TEXTURAS FOTORREALISTAS 2009 ===")

    # ---------------------------------------------------------------------------
    # 1. Alzado Este (Calle Ortiz Rubio): 7laxM5lGf7BzIkMARiFeXA_yaw_263.89.png
    # ---------------------------------------------------------------------------
    p_ortiz, w, h = get_pixels("scratch/staging/juarez_235/7laxM5lGf7BzIkMARiFeXA_yaw_263.89.png")
    if p_ortiz is not None:
        # Cartelera Espectacular CAEM
        save_crop(p_ortiz[0:240, 285:685, :], "juarez_caem_billboard.png")
        # San Diego Beauty Salon
        save_crop(p_ortiz[245:330, 530:680, :], "juarez_beauty_salon_sign.png")
        # San Diego Beauty Salon Escaparate y Muro
        save_crop(p_ortiz[350:530, 480:740, :], "juarez_beauty_salon_facade.png")
        # Murillo's Cerrajería Rótulo
        save_crop(p_ortiz[250:330, 830:965, :], "juarez_cerrajeria_sign.png")
        # Murillo's Cerrajería Mural Llaves
        save_crop(p_ortiz[350:500, 790:940, :], "juarez_cerrajeria_mural.png")
        # La Michoacana Fascia Frutas Este
        save_crop(p_ortiz[245:335, 195:450, :], "juarez_michoacana_east_fascia.png")
        # La Michoacana Mostrador Este
        save_crop(p_ortiz[350:520, 290:475, :], "juarez_michoacana_east_counter.png")

    # ---------------------------------------------------------------------------
    # 2. Fachada Sur Oriente (Juárez Este): 77oLGonvBikDtblS1_QOVQ_yaw_353.44.png
    # ---------------------------------------------------------------------------
    p_juarez_e, w, h = get_pixels("scratch/staging/juarez_235/77oLGonvBikDtblS1_QOVQ_yaw_353.44.png")
    if p_juarez_e is not None:
        # Restaurante Hing Kang: Gran letrero con comida china, Hing Kang y Cerveza Tecate
        save_crop(p_juarez_e[310:345, 260:460, :], "juarez_hingkang_sign.png")
        # Restaurante Hing Kang: Toldos Coca-Cola
        save_crop(p_juarez_e[345:375, 245:350, :], "juarez_hingkang_canopy_left.png")
        save_crop(p_juarez_e[345:375, 370:475, :], "juarez_hingkang_canopy_right.png")
        # Restaurante Hing Kang: Fachada y zócalo rojo
        save_crop(p_juarez_e[375:445, 260:480, :], "juarez_hingkang_facade.png")
        # Distribuidor SKY: Marquesina curva azul
        save_crop(p_juarez_e[320:348, 510:645, :], "juarez_sky_sign.png")
        # Distribuidor SKY: Fachada comercial
        save_crop(p_juarez_e[350:440, 515:640, :], "juarez_sky_facade.png")
        # Local del Arco Tradicional (Local 8): Arco de ladrillo con zócalo verde
        save_crop(p_juarez_e[325:440, 642:798, :], "juarez_arco_facade.png")
        # Local Joyería Anillos de Graduación: Toldo
        save_crop(p_juarez_e[340:375, 805:890, :], "juarez_joyeria_toldo.png")
        # Local Joyería: Fachada azul
        save_crop(p_juarez_e[375:440, 805:875, :], "juarez_joyeria_facade.png")
        # La Michoacana Fachada Sur: Fascia y mostrador
        save_crop(p_juarez_e[305:345, 885:1120, :], "juarez_michoacana_south_fascia.png")
        save_crop(p_juarez_e[345:445, 875:1060, :], "juarez_michoacana_south_counter.png")
        # Rodeo Bar / Callejón: Mural lateral en muro blanco
        save_crop(p_juarez_e[335:450, 140:260, :], "juarez_rodeo_callejon_mural.png")
        # Tótem Tecate Azotea
        save_crop(p_juarez_e[225:290, 470:505, :], "juarez_totem_tecate_roof.png")

    # ---------------------------------------------------------------------------
    # 3. Fachada Sur Poniente (Juárez Oeste): rylIDyzHWu3yI9gXza7M5g_yaw_353.44.png
    # ---------------------------------------------------------------------------
    p_juarez_w, w, h = get_pixels("scratch/staging/juarez_235/rylIDyzHWu3yI9gXza7M5g_yaw_353.44.png")
    if p_juarez_w is not None:
        # Restaurant D'Arce: Letrero azul D'Arce Restaurant Bar
        save_crop(p_juarez_w[310:350, 190:290, :], "juarez_darce_sign.png")
        # Restaurant D'Arce: Fachada completa con cancelería
        save_crop(p_juarez_w[355:460, 130:345, :], "juarez_darce_facade.png")
        # Dulcería La Fuente: Rótulo pintado y porche
        save_crop(p_juarez_w[320:455, 515:685, :], "juarez_lafuente_facade.png")
        # Bar Rodeo: Fachada con celosías y zócalo verde menta
        save_crop(p_juarez_w[340:445, 720:930, :], "juarez_rodeo_front_facade.png")
        # El Baratero: Muro cortina PB y PA
        save_crop(p_juarez_w[330:455, 0:130, :], "juarez_baratero_front.png")
        # El Baratero: Frontispicio Nivel 3 con marcas numéricas 1-4
        save_crop(p_juarez_w[140:275, 0:295, :], "juarez_baratero_tower.png")

    # ---------------------------------------------------------------------------
    # 4. Espectacular SIESA (Frente Sur): GHOVd1crq0yfHHkIiAJ_xQ_yaw_353.44.png
    # ---------------------------------------------------------------------------
    p_siesa, w, h = get_pixels("scratch/staging/juarez_235/GHOVd1crq0yfHHkIiAJ_xQ_yaw_353.44.png")
    if p_siesa is not None:
        # Cartelera Espectacular Grupo SIESA Cara Sur
        save_crop(p_siesa[145:265, 260:455, :], "juarez_siesa_billboard.png")

    # ---------------------------------------------------------------------------
    # 5. Alzado Poniente (Calle Cárdenas): NMwyXMgDo3P_G-_Ki0FQwQ_yaw_85.44.png
    # ---------------------------------------------------------------------------
    p_cardenas_s, w, h = get_pixels("scratch/staging/juarez_235/NMwyXMgDo3P_G-_Ki0FQwQ_yaw_85.44.png")
    if p_cardenas_s is not None:
        # Logotipo Oficial PRI
        save_crop(p_cardenas_s[120:215, 470:570, :], "juarez_pri_logo_cardenas.png")
        # Anuncio Espectacular de Esquina El Baratero
        save_crop(p_cardenas_s[310:370, 850:945, :], "juarez_baratero_corner_totem.png")
        # Zócalo Cárdenas con grafiti auténtico CHG RIMO NEGRO
        save_crop(p_cardenas_s[390:525, 415:830, :], "juarez_cardenas_pri_facade.png")

    # ---------------------------------------------------------------------------
    # 6. Nave Norte Cárdenas: dLpIP7mhA_uWXcQGSH2--Q_yaw_85.44.png
    # ---------------------------------------------------------------------------
    p_cardenas_n, w, h = get_pixels("scratch/staging/juarez_235/dLpIP7mhA_uWXcQGSH2--Q_yaw_85.44.png")
    if p_cardenas_n is not None:
        # Muro verde con pilastras fucsias y grafitis
        save_crop(p_cardenas_n[0:530, 20:1040, :], "juarez_cardenas_nave_facade.png")

    # ---------------------------------------------------------------------------
    # 7. Reverso Norte / Estacionamiento: 2KekTprWvuWa36FCHZaUQA y vhSRNerOnomo5Yoo6CjMug
    # ---------------------------------------------------------------------------
    p_norte_1, w, h = get_pixels("scratch/staging/juarez_235/2KekTprWvuWa36FCHZaUQA_yaw_174.36.png")
    if p_norte_1 is not None:
        save_crop(p_norte_1[420:550, 0:410, :], "juarez_buonappetito_north.png")

    p_norte_2, w, h = get_pixels("scratch/staging/juarez_235/vhSRNerOnomo5Yoo6CjMug_yaw_174.36.png")
    if p_norte_2 is not None:
        save_crop(p_norte_2[540:650, 1070:1210, :], "juarez_parking_north_sign.png")

    print("=== EXTRACCIÓN DE TEXTURAS FOTORREALISTAS COMPLETADA CON ÉXITO ===")

if __name__ == "__main__":
    main()
