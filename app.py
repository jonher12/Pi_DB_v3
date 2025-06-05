import streamlit as st
import pandas as pd
import urllib.request
import gspread
from google.oauth2.service_account import Credentials
import hashlib
from datetime import datetime
import pytz
import unicodedata

st.set_page_config(page_title="📘 Pi DB v3", page_icon="📘", layout="wide")

# IDs de hojas desde secrets
SHEET_IDS = {
    "PharmD": st.secrets["SHEET_ID_PHARMD"].strip(),
    "PhD": st.secrets["SHEET_ID_PHD"].strip()
}
FOLDER_LINKS = {
    "PharmD": st.secrets["FOLDER_LINK_PHARMD"],
    "PhD": st.secrets["FOLDER_LINK_PHD"]
}
DRIVE_LINK_SHEET_ID = st.secrets["DRIVE_LINK_SHEET_ID"].strip()
USERS_SHEET_ID = st.secrets["USERS_SHEET_ID"].strip()
LOG_SHEET_ID = st.secrets["LOG_SHEET_ID"].strip()

# 🔐 Funciones
# ... (rest of the code remains unchanged)

    # Cargar datos
    df = load_sheet(SHEET_IDS[programa])
    df_links = load_sheet(DRIVE_LINK_SHEET_ID)

    df_filtrado = df.copy()
    curso = None
    palabra_clave = st.session_state.get("palabra_clave", "")

    if tipo_filtro == "Por código":
        codigo_sel = st.sidebar.selectbox("Selecciona el código del curso:", sorted(df["Codificación"].dropna().unique()))
        if codigo_sel:
            df_filtrado = df[df["Codificación"] == codigo_sel]
            st.sidebar.success(f"📌 Código seleccionado: `{codigo_sel}`")
            register_log(st.session_state["username"], f"search: code = {codigo_sel}")

    elif tipo_filtro == "Por título del curso":
        titulo_sel = st.sidebar.selectbox("Selecciona el título del curso:", sorted(df["TítuloCompletoEspañol"].dropna().unique()))
        if titulo_sel:
            df_filtrado = df[df["TítuloCompletoEspañol"] == titulo_sel]
            st.sidebar.success(f"📌 Título seleccionado: **{titulo_sel}**")
            register_log(st.session_state["username"], f"search: title = {titulo_sel}")

    elif tipo_filtro == "🔍 Búsqueda Avanzada":
        columnas_busqueda = [
            "Codificación", "TítuloCompletoEspañol", "TítuloCompletoInglés",
            "Descripción", "Comentarios", "AnejosComentarios",
            "CursosPrerrequisitos", "CursosCorrequisitos"
        ]
        campo_sel = st.sidebar.selectbox("Buscar en:", columnas_busqueda, index=1, key="campo_sel")
        palabra_clave = st.sidebar.text_input("Ingresa una palabra clave:", key="palabra_clave")

        if campo_sel and palabra_clave.strip():
            def normalizar(texto):
                return unicodedata.normalize("NFKD", str(texto)).encode("ASCII", "ignore").decode("utf-8").lower()

            df_filtrado = df[df[campo_sel].astype(str).apply(normalizar).str.contains(normalizar(palabra_clave))]
            if not df_filtrado.empty:
                st.sidebar.success(f"📌 Búsqueda de _{palabra_clave}_ en **{campo_sel}**")
                register_log(st.session_state["username"], f"search: {campo_sel} ~ {palabra_clave}")

    mostrar_dropdown = False
    opciones_dropdown = []

    if not df_filtrado.empty:
        if len(df_filtrado) == 1:
            curso = df_filtrado.iloc[0]
        elif tipo_filtro == "🔍 Búsqueda Avanzada" and palabra_clave.strip():
            opciones_dropdown = df_filtrado["Codificación"] + " — " + df_filtrado["TítuloCompletoEspañol"]
            mostrar_dropdown = True
        else:
            curso = df_filtrado.iloc[0]
    else:
        st.warning("⚠️ No se encontraron cursos con ese filtro.")
        st.stop()

    st.markdown("<h1 style='text-align: center;'>Bienvenido a Pi v3</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center;'>📚 Base de Datos de Cursos ({programa})</h2>", unsafe_allow_html=True)
    st.markdown("---")

    if mostrar_dropdown and len(opciones_dropdown) > 1:
        st.markdown("""
            <h3 style='color: red; margin-bottom: -0.3rem;'>Selecciona el curso que deseas consultar:</h3>
            <div style='margin-top: -1.1rem;'>
        """, unsafe_allow_html=True)
        seleccion = st.selectbox("", opciones_dropdown, key="dropdown_b_avanzada")
        st.markdown("</div><div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        cod_seleccionado = seleccion.split(" — ")[0]
        curso = df_filtrado[df_filtrado["Codificación"] == cod_seleccionado].iloc[0]
    elif mostrar_dropdown and len(opciones_dropdown) == 1:
        curso = df_filtrado.iloc[0]

    if "viewed_course" not in st.session_state or st.session_state["viewed_course"] != curso["Codificación"]:
        register_log(st.session_state["username"], f"view_course: {curso['Codificación']}")
        st.session_state["viewed_course"] = curso["Codificación"]

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"""
        <div style="font-size: 18px; line-height: 1.8;">
        <b>Codificación:</b> {curso['Codificación']}<br>
        <b>Estado:</b> {'Activo' if curso['Estatus'] == 1 else 'Inactivo'}<br>
        <b>Título (ES):</b> {curso['TítuloCompletoEspañol']}<br>
        <b>Título (EN):</b> {curso['TítuloCompletoInglés']}<br>
        <b>Créditos:</b> {curso['Créditos']}<br>
        <b>Horas Contacto:</b> {curso['HorasContacto']}<br>
        <b>Año:</b> {curso['Año']}<br>
        <b>Semestre:</b> {curso['Semestre']}<br>
        <b>Fecha Revisión:</b> {curso['FechaÚltimaRevisión']}<br>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📎 Upload & Download de Documentos")
        folder_row = df_links[(df_links["Codificación"] == curso['Codificación']) & (df_links["Programa"] == programa)]

        if not folder_row.empty:
            folder_id = folder_row.iloc[0]["FolderID"]
            st.markdown(f"[📂 Abrir carpeta del curso {curso['Codificación']}]({f'https://drive.google.com/drive/folders/{folder_id}'})")
        else:
            st.warning("⚠️ No se encontró el enlace directo para este curso.")

    with col2:
        st.markdown("### 📝 Descripción del Curso")
        descripcion = st.text_area("Descripción", value=curso["Descripción"], height=300)
        if descripcion != curso["Descripción"]:
            update_course_field(SHEET_IDS[programa], curso["Codificación"], "Descripción", descripcion)

        st.markdown("### 🗒️ Comentarios")
        comentarios = st.text_area("Comentarios", value=curso["Comentarios"], height=300)
        if comentarios != curso["Comentarios"]:
            update_course_field(SHEET_IDS[programa], curso["Codificación"], "Comentarios", comentarios)

    # Pie de página
    st.markdown("---")
    st.caption("División de Evaluación de la Efectividad Curricular e Institucional. Todos los derechos reservados. JHA 2025©. Administrador: Jonathan Hernández-Agosto, EdD, GCG.")
