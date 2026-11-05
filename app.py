import streamlit as st
import cv2
import numpy as np
import base64
import io
import zipfile
from pathlib import Path
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from shapely.affinity import translate
import svgwrite

st.set_page_config(page_title="Generador de Llaveros de Acrílico", layout="wide")

st.markdown("""
    <style>
    .stSelectbox div[data-baseweb="select"] > div {
        border-color: #ff4b4b !important;
    }
    </style>
""", unsafe_allow_html=True)

TEXTOS = {
    "es": {
        "titulo": "Generador de Llaveros de Acrílico",
        "global_params": "Parámetros Globales (Predeterminados)",
        "diametro": "Tamaño Total del Llavero (mm)",
        "margen": "Margen de Acrílico Transparente (mm)",
        "pos_ojal": "Posición Ojal",
        "radio_oreja": "Tamaño de Ojal / Oreja - Radio (mm)",
        "radio_interno": "Tamaño del Agujero para Argolla - Radio (mm)",
        "color_base": "Color de Fondo (Base Blanca)",
        "btn_reset_global": "Restablecer Valores de Fábrica",
        "confirm_reset": "¿Confirma que desea restablecer los parámetros globales?",
        "yes": "Sí, restablecer",
        "no": "Cancelar",
        "subir": "Cargar Imágenes para Llaveros (PNG, JPG)",
        "ajuste_ind": "Ajustes Específicos de este Archivo",
        "usar_individual": "Usar valores personalizados para este archivo",
        "capas_opciones": ["Vista Completa", "Capa 1: Imagen Principal", "Capa 2: Fondo de Color",
                           "Capa 3: Imagen Frontal", "Capa 4: Línea de Corte"],
        "orden_capas": "Orden de Impresión y Corte (Z-Index)",
        "error_capas": "Hay capas duplicadas en la jerarquía.",
        "descargas": "Descargas",
        "descargar_uno": "Descargar SVG",
        "descargar_zip": "Descargar ZIP",
        "label_offset_x": "Posición Ojal X (mm)",
        "label_offset_y": "Posición Ojal Y (mm)",
        "label_ind_margen": "Margen de Acrílico (mm)",
        "label_ind_oreja": "Tamaño de Ojal - Radio (mm)",
        "label_ind_hueco": "Tamaño de Agujero - Radio (mm)",
        "label_ind_color": "Color de Fondo Específico",
        "reset_defaults": "Volver a usar Valores Globales"
    },
    "en": {
        "titulo": "Acrylic Keychain Generator",
        "global_params": "Global Parameters (Default)",
        "diametro": "Total Keychain Size (mm)",
        "margen": "Transparent Acrylic Margin (mm)",
        "pos_ojal": "Hanger Position",
        "radio_oreja": "Hanger / Ear Size - Radius (mm)",
        "radio_interno": "Ring Hole Size - Radius (mm)",
        "color_base": "Background Color (White Base)",
        "btn_reset_global": "Reset Factory Defaults",
        "confirm_reset": "Confirm reset of global parameters?",
        "yes": "Yes, reset",
        "no": "Cancel",
        "subir": "Upload Keychain Images (PNG, JPG)",
        "ajuste_ind": "Specific Settings for this File",
        "usar_individual": "Use custom values for this file",
        "capas_opciones": ["Full View", "Layer 1: Main Image", "Layer 2: Color Background", "Layer 3: Front Image",
                           "Layer 4: Cut Path"],
        "orden_capas": "Printing & Cutting Order (Z-Index)",
        "error_capas": "Duplicate layers found in the hierarchy.",
        "descargas": "Downloads",
        "descargar_uno": "Download SVG",
        "descargar_zip": "Download ZIP",
        "label_offset_x": "Hanger X Position (mm)",
        "label_offset_y": "Hanger Y Position (mm)",
        "label_ind_margen": "Acrylic Margin (mm)",
        "label_ind_oreja": "Hanger Size - Radius (mm)",
        "label_ind_hueco": "Ring Hole Size - Radius (mm)",
        "label_ind_color": "Specific Background Color",
        "reset_defaults": "Use Global Values Again"
    }
}

col_title, col_lang = st.columns([5, 1])

with col_lang:
    idioma_sel = st.selectbox("", ["ES", "EN"], label_visibility="collapsed")
    lang = "es" if idioma_sel == "ES" else "en"

t = TEXTOS[lang]

with col_title:
    st.title(t["titulo"])

st.sidebar.markdown("---")
st.sidebar.header(t["global_params"])

if "g_diametro" not in st.session_state: st.session_state.g_diametro = 60.0
if "g_margen" not in st.session_state: st.session_state.g_margen = 3.0
if "g_oreja_x" not in st.session_state: st.session_state.g_oreja_x = 0.0
if "g_oreja_y" not in st.session_state: st.session_state.g_oreja_y = 2.0
if "g_radio_oreja" not in st.session_state: st.session_state.g_radio_oreja = 7.0
if "g_radio_interno" not in st.session_state: st.session_state.g_radio_interno = 2.5
if "g_color_base" not in st.session_state: st.session_state.g_color_base = "#FFFFFF"

if "g_orden_capas" not in st.session_state:
    st.session_state.g_orden_capas = ["1 imagen", "2 base blanca", "3 imagen", "4 corte"]

if "confirm_reset_global" not in st.session_state:
    st.session_state.confirm_reset_global = False

st.session_state.g_diametro = st.sidebar.number_input(t["diametro"], 40.0, 100.0, float(st.session_state.g_diametro),
                                                      1.0, key="input_g_diametro")
st.session_state.g_margen = st.sidebar.number_input(t["margen"], 1.0, 10.0, float(st.session_state.g_margen), 0.5,
                                                    key="input_g_margen")

st.sidebar.markdown(f"**{t['pos_ojal']}**")
st.session_state.g_oreja_x = st.sidebar.number_input(t["label_offset_x"], -15.0, 15.0,
                                                     float(st.session_state.g_oreja_x), 0.5, key="input_g_oreja_x")
st.session_state.g_oreja_y = st.sidebar.number_input(t["label_offset_y"], -10.0, 15.0,
                                                     float(st.session_state.g_oreja_y), 0.5, key="input_g_oreja_y")

st.session_state.g_radio_oreja = st.sidebar.number_input(t["radio_oreja"], 4.0, 10.0,
                                                         float(st.session_state.g_radio_oreja), 0.5,
                                                         key="input_g_oreja")
st.session_state.g_radio_interno = st.sidebar.number_input(t["radio_interno"], 1.0, 5.0,
                                                           float(st.session_state.g_radio_interno), 0.5,
                                                           key="input_g_interno")
st.session_state.g_color_base = st.sidebar.color_picker(t["color_base"], st.session_state.g_color_base,
                                                        key="input_g_color")

if st.sidebar.button(t["btn_reset_global"]):
    st.session_state.confirm_reset_global = True

if st.session_state.confirm_reset_global:
    st.sidebar.warning(t["confirm_reset"])
    col_c1, col_c2 = st.sidebar.columns(2)
    if col_c1.button(t["yes"]):
        st.session_state.g_diametro = 60.0
        st.session_state.g_margen = 3.0
        st.session_state.g_oreja_x = 0.0
        st.session_state.g_oreja_y = 2.0
        st.session_state.g_radio_oreja = 7.0
        st.session_state.g_radio_interno = 2.5
        st.session_state.g_color_base = "#FFFFFF"
        st.session_state.confirm_reset_global = False
        st.rerun()
    if col_c2.button(t["no"]):
        st.session_state.confirm_reset_global = False
        st.rerun()

archivos_subidos = st.file_uploader(t["subir"], type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if archivos_subidos:
    if "configs" not in st.session_state:
        st.session_state.configs = {}
    if "archivo_idx" not in st.session_state:
        st.session_state.archivo_idx = 0

    for archivo in archivos_subidos:
        if archivo.name not in st.session_state.configs:
            st.session_state.configs[archivo.name] = {
                "custom_enabled": False,
                "oreja_x": st.session_state.g_oreja_x,
                "oreja_y": st.session_state.g_oreja_y,
                "radio_oreja": st.session_state.g_radio_oreja,
                "radio_hueco": st.session_state.g_radio_interno,
                "margen": st.session_state.g_margen,
                "color_base": st.session_state.g_color_base
            }
        else:
            conf = st.session_state.configs[archivo.name]
            if not conf["custom_enabled"]:
                conf["oreja_x"] = st.session_state.g_oreja_x
                conf["oreja_y"] = st.session_state.g_oreja_y
                conf["radio_oreja"] = st.session_state.g_radio_oreja
                conf["radio_hueco"] = st.session_state.g_radio_interno
                conf["margen"] = st.session_state.g_margen
                conf["color_base"] = st.session_state.g_color_base

    if st.session_state.archivo_idx >= len(archivos_subidos):
        st.session_state.archivo_idx = 0

    nombres_archivos = [a.name for a in archivos_subidos]
    archivo_seleccionado = nombres_archivos[st.session_state.archivo_idx]

    st.sidebar.markdown("---")
    st.sidebar.header(t["ajuste_ind"])
    st.sidebar.text(f"Asset: {archivo_seleccionado}")

    conf_actual = st.session_state.configs[archivo_seleccionado]

    usar_ind = st.sidebar.checkbox(t["usar_individual"], value=conf_actual["custom_enabled"],
                                   key=f"toggle_custom_{archivo_seleccionado}")
    conf_actual["custom_enabled"] = usar_ind

    if usar_ind:
        conf_actual["oreja_x"] = st.sidebar.number_input(t["label_offset_x"], -15.0, 15.0,
                                                         float(conf_actual["oreja_x"]), 0.5,
                                                         key=f"ind_ox_{archivo_seleccionado}")
        conf_actual["oreja_y"] = st.sidebar.number_input(t["label_offset_y"], -10.0, 15.0,
                                                         float(conf_actual["oreja_y"]), 0.5,
                                                         key=f"ind_oy_{archivo_seleccionado}")
        conf_actual["margen"] = st.sidebar.number_input(t["label_ind_margen"], 1.0, 10.0, float(conf_actual["margen"]),
                                                        0.5, key=f"ind_margen_{archivo_seleccionado}")
        conf_actual["radio_oreja"] = st.sidebar.number_input(t["label_ind_oreja"], 4.0, 10.0,
                                                             float(conf_actual["radio_oreja"]), 0.5,
                                                             key=f"ind_oreja_{archivo_seleccionado}")
        conf_actual["radio_hueco"] = st.sidebar.number_input(t["label_ind_hueco"], 1.0, 5.0,
                                                             float(conf_actual["radio_hueco"]), 0.5,
                                                             key=f"ind_hueco_{archivo_seleccionado}")
        conf_actual["color_base"] = st.sidebar.color_picker(t["label_ind_color"], conf_actual["color_base"],
                                                            key=f"ind_color_{archivo_seleccionado}")
    else:
        conf_actual["oreja_x"] = st.session_state.g_oreja_x
        conf_actual["oreja_y"] = st.session_state.g_oreja_y
        conf_actual["radio_oreja"] = st.session_state.g_radio_oreja
        conf_actual["radio_hueco"] = st.session_state.g_radio_interno
        conf_actual["margen"] = st.session_state.g_margen
        conf_actual["color_base"] = st.session_state.g_color_base

    st.markdown("---")

    col_flecha_izq, col_preview, col_flecha_der, col2 = st.columns([0.5, 3.5, 0.5, 2])

    with col_flecha_izq:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        if st.button("<", key="prev_arrow", help="Anterior") and st.session_state.archivo_idx > 0:
            st.session_state.archivo_idx -= 1
            st.rerun()

    with col_flecha_der:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        if st.button(">", key="next_arrow", help="Siguiente") and st.session_state.archivo_idx < len(
                archivos_subidos) - 1:
            st.session_state.archivo_idx += 1
            st.rerun()

    svgs_generados = {}
    capas_base = ["1 imagen", "2 base blanca", "3 imagen", "4 corte"]

    for archivo in archivos_subidos:
        bytes_data = archivo.read()
        np_arr = np.frombuffer(bytes_data, np.uint8)
        img_raw = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)

        if img_raw is None:
            continue

        if img_raw.shape[2] == 3:
            gray = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
            b, g, r = cv2.split(img_raw)
            img = cv2.merge([b, g, r, mask])
        else:
            img = img_raw

        h_orig, w_orig = img.shape[:2]
        alpha_orig = img[:, :, 3]

        y_indices, x_indices = np.where(alpha_orig > 10)
        if len(x_indices) == 0:
            continue
        centro_x_orig = np.mean(x_indices)
        centro_y_orig = np.mean(y_indices)
        radio_orig = np.max(np.sqrt((x_indices - centro_x_orig) ** 2 + (y_indices - centro_y_orig) ** 2))

        dpi = 300
        c_conf = st.session_state.configs[archivo.name]
        pixels_offset = (c_conf["margen"] / 25.4) * dpi
        diametro_objetivo_px = (st.session_state.g_diametro / 25.4) * dpi
        radio_objetivo_px = (diametro_objetivo_px / 2.0) - pixels_offset
        scale_factor = radio_objetivo_px / radio_orig if radio_orig > 0 else 1.0

        new_w = max(1, int(w_orig * scale_factor))
        new_h = max(1, int(h_orig * scale_factor))
        img_resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

        h, w = img_resized.shape[:2]
        alpha = img_resized[:, :, 3]
        _, thresh_raw = cv2.threshold(alpha, 50, 255, cv2.THRESH_BINARY)

        contours_base, _ = cv2.findContours(thresh_raw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        poligonos_base = [Polygon(cnt.reshape(-1, 2)).buffer(0) for cnt in contours_base if cv2.contourArea(cnt) > 5]
        forma_base_blanca = unary_union(poligonos_base)

        kernel_puente = np.ones((25, 25), np.uint8)
        alpha_unificado = cv2.morphologyEx(thresh_raw, cv2.MORPH_CLOSE, kernel_puente)

        contours_corte, hierarchy = cv2.findContours(alpha_unificado, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        poligonos_corte = []
        if contours_corte:
            for i, cnt in enumerate(contours_corte):
                if hierarchy[0][i][3] == -1 and cv2.contourArea(cnt) > 100:
                    p = Polygon(cnt.reshape(-1, 2)).buffer(0)
                    if not p.is_empty:
                        poligonos_corte.append(p)

        forma_principal = max(poligonos_corte, key=lambda poly: poly.area) if poligonos_corte else Polygon()

        forma_expandida = forma_principal.buffer(pixels_offset, join_style=1).buffer(-0.5, join_style=1).buffer(0.5,
                                                                                                                join_style=1)

        minx, miny, maxx, maxy = forma_expandida.bounds
        centro_x_base = (minx + maxx) / 2.0
        top_y = miny

        offset_x_px = (c_conf["oreja_x"] / 25.4) * dpi
        offset_y_px = (c_conf["oreja_y"] / 25.4) * dpi

        centro_oreja_x = centro_x_base + offset_x_px
        centro_oreja_y = top_y + offset_y_px

        radio_oreja_px = (c_conf["radio_oreja"] / 25.4) * dpi
        radio_hueco_px = (c_conf["radio_hueco"] / 25.4) * dpi

        oreja = Point(centro_oreja_x, centro_oreja_y).buffer(radio_oreja_px, resolution=40)
        hueco = Point(centro_oreja_x, centro_oreja_y).buffer(radio_hueco_px, resolution=40)

        forma_final_corte = unary_union([forma_expandida, oreja]).difference(hueco)

        minx_c, miny_c, maxx_c, maxy_c = forma_final_corte.bounds
        shift_y = 20.0 - miny_c if miny_c < 20.0 else 0.0

        if shift_y > 0:
            h_nuevo = int(h + shift_y)
            img_canvas = np.zeros((h_nuevo, w, 4), dtype=np.uint8)
            img_canvas[int(shift_y):int(shift_y) + h, 0:w] = img_resized

            forma_base_blanca = translate(forma_base_blanca, xoff=0, yoff=shift_y)
            forma_final_corte = translate(forma_final_corte, xoff=0, yoff=shift_y)

            img_resized = img_canvas
            h = h_nuevo

        if archivo.name == archivo_seleccionado:
            with col_preview:
                header_col1, header_col2 = st.columns([4, 1])
                with header_col1:
                    st.subheader(f"{archivo.name} ({st.session_state.archivo_idx + 1}/{len(archivos_subidos)})")
                with header_col2:
                    with st.popover("⚙"):
                        st.markdown(f"**{t['orden_capas']}**")

                        try:
                            act_orden = st.session_state.g_orden_capas
                            if len(set(act_orden)) != 4:
                                act_orden = ["1 imagen", "2 base blanca", "3 imagen", "4 corte"]
                        except Exception:
                            act_orden = ["1 imagen", "2 base blanca", "3 imagen", "4 corte"]

                        sel_1 = st.selectbox("Capa 1", capas_base, index=capas_base.index(act_orden[0]),
                                             key=f"p1_{archivo.name}")
                        sel_2 = st.selectbox("Capa 2", capas_base, index=capas_base.index(act_orden[1]),
                                             key=f"p2_{archivo.name}")
                        sel_3 = st.selectbox("Capa 3", capas_base, index=capas_base.index(act_orden[2]),
                                             key=f"p3_{archivo.name}")
                        sel_4 = st.selectbox("Capa 4", capas_base, index=capas_base.index(act_orden[3]),
                                             key=f"p4_{archivo.name}")

                        candidatas = [sel_1, sel_2, sel_3, sel_4]
                        duplicados = {x for x in candidatas if candidatas.count(x) > 1}

                        if len(set(candidatas)) != 4:
                            st.error(t["error_capas"])
                            st.session_state.g_orden_capas = ["1 imagen", "2 base blanca", "3 imagen", "4 corte"]
                        else:
                            st.session_state.g_orden_capas = candidatas

                capa_activa = st.radio(
                    "Capas",
                    t["capas_opciones"],
                    horizontal=True,
                    label_visibility="collapsed",
                    key=f"radio_capas_{archivo.name}"
                )

        # --- PREVISUALIZACION CON PADDING AMPLIADO PARA QUE NO SE CORTEN LOS BORDES ---
        padding_canvas = 60
        h_pad = h + (padding_canvas * 2)
        w_pad = w + (padding_canvas * 2)

        img_preview = np.zeros((h_pad, w_pad, 4), dtype=np.uint8)
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGRA2RGBA)
        img_preview[padding_canvas:padding_canvas + h, padding_canvas:padding_canvas + w] = img_rgb

        forma_corte_desplazada = translate(forma_final_corte, xoff=padding_canvas, yoff=padding_canvas)
        forma_base_desplazada = translate(forma_base_blanca, xoff=padding_canvas, yoff=padding_canvas)

        capa_activa = st.session_state.get(f"radio_capas_{archivo.name}", t["capas_opciones"][0])

        hex_color = c_conf["color_base"].lstrip('#')
        rgb_base = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

        if capa_activa == t["capas_opciones"][0]:
            img_preview = np.zeros((h_pad, w_pad, 4), dtype=np.uint8)
            img_preview[padding_canvas:padding_canvas + h, padding_canvas:padding_canvas + w] = img_rgb
            if forma_corte_desplazada.geom_type == 'Polygon':
                cv2.polylines(img_preview, [np.array(forma_corte_desplazada.exterior.coords, dtype=np.int32)],
                              isClosed=True, color=(255, 0, 255, 255), thickness=2)
                for inter in forma_corte_desplazada.interiors:
                    cv2.polylines(img_preview, [np.array(inter.coords, dtype=np.int32)], isClosed=True,
                                  color=(255, 0, 255, 255), thickness=2)
            elif forma_corte_desplazada.geom_type == 'MultiPolygon':
                for geom in forma_corte_desplazada.geoms:
                    cv2.polylines(img_preview, [np.array(geom.exterior.coords, dtype=np.int32)], isClosed=True,
                                  color=(255, 0, 255, 255), thickness=2)

        elif capa_activa == t["capas_opciones"][1]:
            img_preview = np.zeros((h_pad, w_pad, 4), dtype=np.uint8)
            img_preview[padding_canvas:padding_canvas + h, padding_canvas:padding_canvas + w] = img_rgb

        elif capa_activa == t["capas_opciones"][2]:
            mask_base = np.zeros((h_pad, w_pad), dtype=np.uint8)


            def pintar_geom(geom):
                if geom.geom_type == 'Polygon':
                    pts = np.array(geom.exterior.coords, dtype=np.int32)
                    cv2.fillPoly(mask_base, [pts], 255)
                    for inter in geom.interiors:
                        cv2.fillPoly(mask_base, [np.array(inter.coords, dtype=np.int32)], 0)
                elif geom.geom_type in ['MultiPolygon', 'GeometryCollection']:
                    for g in geom.geoms: pintar_geom(g)


            pintar_geom(forma_base_desplazada)
            img_preview = cv2.cvtColor(mask_base, cv2.COLOR_GRAY2RGBA)
            img_preview[mask_base == 255] = [rgb_base[0], rgb_base[1], rgb_base[2], 255]

        elif capa_activa == t["capas_opciones"][3]:
            img_preview = np.zeros((h_pad, w_pad, 4), dtype=np.uint8)
            img_preview[padding_canvas:padding_canvas + h, padding_canvas:padding_canvas + w] = img_rgb

        elif capa_activa == t["capas_opciones"][4]:
            if forma_corte_desplazada.geom_type == 'Polygon':
                cv2.polylines(img_preview, [np.array(forma_corte_desplazada.exterior.coords, dtype=np.int32)],
                              isClosed=True, color=(255, 0, 255, 255), thickness=3)
                for inter in forma_corte_desplazada.interiors:
                    cv2.polylines(img_preview, [np.array(inter.coords, dtype=np.int32)], isClosed=True,
                                  color=(255, 0, 255, 255), thickness=3)
            elif forma_corte_desplazada.geom_type == 'MultiPolygon':
                for geom in forma_corte_desplazada.geoms:
                    cv2.polylines(img_preview, [np.array(geom.exterior.coords, dtype=np.int32)], isClosed=True,
                                  color=(255, 0, 255, 255), thickness=3)

        if archivo.name == archivo_seleccionado:
            with col_preview:
                st.image(img_preview, use_container_width=True)

        success, encoded_img = cv2.imencode('.png', img_resized)
        data_uri = f"data:image/png;base64,{base64.b64encode(encoded_img).decode('utf-8')}"

        dwg = svgwrite.Drawing(profile='tiny', size=(w, h), debug=False)
        elementos_capas = {}

        g1 = dwg.g(id='1_imagen')
        g1.add(dwg.image(href=data_uri, insert=(0, 0), size=(w, h)))
        elementos_capas["1 imagen"] = g1


        def geom_a_path(geom):
            path_data = []
            if geom.is_empty: return ""
            if geom.geom_type == 'Polygon':
                ext = geom.exterior.coords
                path_data.append(f"M {ext[0][0]} {ext[0][1]}")
                for pt in ext[1:]: path_data.append(f"L {pt[0]} {pt[1]}")
                path_data.append("Z")
                for inter in geom.interiors:
                    inte = inter.coords
                    path_data.append(f"M {inte[0][0]} {inte[0][1]}")
                    for pt in inte[1:]: path_data.append(f"L {pt[0]} {pt[1]}")
                    path_data.append("Z")
            elif geom.geom_type in ['MultiPolygon', 'GeometryCollection']:
                for g in geom.geoms: path_data.append(geom_a_path(g))
            return " ".join(path_data)


        g2 = dwg.g(id='2_base_blanca')
        p_base = geom_a_path(forma_base_blanca)
        if p_base:
            g2.add(dwg.path(d=p_base, fill=c_conf["color_base"], stroke='none', style="fill-rule: evenodd;"))
        elementos_capas["2 base blanca"] = g2

        g3 = dwg.g(id='3_imagen')
        g3.add(dwg.image(href=data_uri, insert=(0, 0), size=(w, h)))
        elementos_capas["3 imagen"] = g3

        g4 = dwg.g(id='4_corte')
        p_corte = geom_a_path(forma_final_corte)
        g4.add(dwg.path(d=p_corte, fill='none', stroke='#FF00FF', stroke_width=1.5, style="fill-rule: evenodd;"))
        elementos_capas["4 corte"] = g4

        try:
            orden_actual = st.session_state.g_orden_capas
            if len(set(orden_actual)) != 4:
                orden_actual = ["1 imagen", "2 base blanca", "3 imagen", "4 corte"]
        except Exception:
            orden_actual = ["1 imagen", "2 base blanca", "3 imagen", "4 corte"]

        for nombre_capa in orden_actual:
            if nombre_capa in elementos_capas:
                dwg.add(elementos_capas[nombre_capa])

        svgs_generados[f"{Path(archivo.name).stem}.svg"] = dwg.tostring()

    with col2:
        st.subheader(t["descargas"])

        if len(svgs_generados) > 1:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for nombre_svg, contenido_svg in svgs_generados.items():
                    zip_file.writestr(nombre_svg, contenido_svg)

            st.download_button(
                label=t["descargar_zip"],
                data=zip_buffer.getvalue(),
                file_name="llaveros_svg.zip",
                mime="application/zip"
            )

        for nombre_svg, contenido_svg in svgs_generados.items():
            st.download_button(
                label=f"{t['descargar_uno']}: {nombre_svg}",
                data=contenido_svg,
                file_name=nombre_svg,
                mime="image/svg+xml"
            )