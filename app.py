import streamlit as st
import pandas as pd
from urllib.parse import quote

# --- CONFIGURACIONES DE PÁGINA ---
st.set_page_config(page_title="Pi DB v3", layout="wide")

# --- FUNCIONES AUXILIARES ---
def cargar_hoja(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    return pd.read_csv(url)

def formatear_entero(valor):
    try:
        return int(round(valor))
    except:
        return valor

# --- VARIABLES DE CONFIGURACIÓN ---
SHEET_ID_PHARMD = st.secrets["SHEET_ID_PHARMD"]
SHEET_ID_PHD = st.secrets["SHEET_ID_PHD"]
DRIVE_LINKS_SHEET = st.secrets["DRIVE_LINK_SHEET_ID"]
FOLDER_PHARMD = st.secrets["FOLDER_LINK_PHARMD"]
FOLDER_PHD = st.secrets["FOLDER_LINK_PHD"]

# --- LOGIN SIMPLIFICADO ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("📘 Bienvenido a Pi DB v3")
    with st.form("login_form"):
        user = st.text_input("Usuario:")
        password = st.text_input("Contraseña:", type="password")
        submit = st.form_submit_button("Ingresar")
        if submit:
            if user == "j" and password == "1":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
else:
    # --- SELECCIÓN DE PROGRAMA ---
    st.sidebar.title("Navegación")
    programa = st.sidebar.radio("Selecciona el programa:", ["PharmD", "PhD"])
    sheet_id = SHEET_ID_PHARMD if programa == "PharmD" else SHEET_ID_PHD
    folder_base = FOLDER_PHARMD if programa == "PharmD" else FOLDER_PHD

    # --- CARGA DE DATOS ---
    df = cargar_hoja(sheet_id)
    df_links = cargar_hoja(DRIVE_LINKS_SHEET)

    codigos = df["Codificación"].dropna().unique().tolist()
    titulos = df["TítuloCompletoEspañol"].dropna().unique().tolist()

    st.sidebar.subheader("Filtros de búsqueda")

    if "cod_sel" not in st.session_state:
        st.session_state.cod_sel = ""
    if "tit_sel" not in st.session_state:
        st.session_state.tit_sel = ""
    if "palabra" not in st.session_state:
        st.session_state.palabra = ""

    cod_sel = st.sidebar.selectbox("Seleccionar código:", [""] + codigos, index=0, key="cod_sel")
    if st.sidebar.button("Limpiar Filtro", key="limpiar_cod"):
        st.session_state.cod_sel = ""
        st.rerun()

    tit_sel = st.sidebar.selectbox("Título del curso:", [""] + titulos, index=0, key="tit_sel")
    if st.sidebar.button("Limpiar Filtro", key="limpiar_tit"):
        st.session_state.tit_sel = ""
        st.rerun()

    palabra_clave = st.sidebar.text_input("Palabra clave:", value=st.session_state.palabra, key="palabra")
    if st.sidebar.button("Limpiar Filtro", key="limpiar_palabra"):
        st.session_state.palabra = ""
        st.rerun()

    df_filtrado = df.copy()
    if st.session_state.cod_sel:
        df_filtrado = df_filtrado[df_filtrado["Codificación"] == st.session_state.cod_sel]
    elif st.session_state.tit_sel:
        df_filtrado = df_filtrado[df_filtrado["TítuloCompletoEspañol"] == st.session_state.tit_sel]
    elif st.session_state.palabra:
        palabra = st.session_state.palabra.lower()
        df_filtrado = df_filtrado[df_filtrado.apply(lambda row: palabra in str(row).lower(), axis=1)]

    st.title("📘 Bienvenido a Pi DB v3")
    st.header(f"📚 Base de Datos de Cursos ({programa})")

    if df_filtrado.empty:
        st.warning("No se encontraron cursos que coincidan con los filtros seleccionados.")
    else:
        curso = df_filtrado.iloc[0]
        cod = curso["Codificación"]
        st.markdown(f"**Codificación:** {cod}  ")
        st.markdown(f"**Estado:** {curso['Estatus']}")
        st.markdown(f"**Título (ES):** {curso['TítuloCompletoEspañol']}")
        st.markdown(f"**Título (EN):** {curso['TítuloCompletoInglés']}")
        st.markdown(f"**Créditos:** {formatear_entero(curso['Créditos'])}  ")
        st.markdown(f"**Horas Contacto:** {formatear_entero(curso['HorasContacto'])}  ")
        st.markdown(f"**Año:** {formatear_entero(curso['Año'])}  ")
        st.markdown(f"**Semestre:** {formatear_entero(curso['Semestre'])}  ")
        st.markdown(f"**Fecha Revisión:** {curso['FechaUltimaRevisión']}")

        st.subheader("📝 Descripción del Curso")
        st.info(curso["Descripción"])

        st.subheader("🗂 Comentarios")
        st.code(curso["Comentarios"], language="markdown")

        st.subheader("📎 Archivos disponibles (Drive)")
        link_folder = df_links[df_links["Codificación"] == cod]["Link"].values
        if len(link_folder) > 0:
            st.markdown(f"🔗 [Abrir carpeta del curso]({link_folder[0]})")
            st.caption(f"*Sugerencia: busca el subfolder llamado* `{cod}` *en esa carpeta para ver los documentos.*")
        else:
            st.warning("No se encontró enlace a la carpeta del curso en Drive.")
