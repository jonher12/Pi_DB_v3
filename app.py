import streamlit as st
import pandas as pd
import requests

# --- CONFIGURACION DE LA PAGINA ---
st.set_page_config(page_title="Pi DB v3", layout="wide")

# --- FUNCIONES AUXILIARES ---
def cargar_sheet(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    return pd.read_csv(url)

# --- CARGA DE DATOS ---
SHEET_ID_PHARMD = st.secrets["SHEET_ID_PHARMD"]
SHEET_ID_PHD = st.secrets["SHEET_ID_PHD"]
DRIVE_LINKS_ID = st.secrets["DRIVE_LINK_SHEET_ID"]

df_pharmd = cargar_sheet(SHEET_ID_PHARMD)
df_phd = cargar_sheet(SHEET_ID_PHD)
df_links = cargar_sheet(DRIVE_LINKS_ID)

# --- BARRA LATERAL: SELECCION DE PROGRAMA ---
st.sidebar.title("Navegación")
programa = st.sidebar.radio("Selecciona el programa:", ["PharmD", "PhD"])

df = df_pharmd if programa == "PharmD" else df_phd
folder_base = st.secrets["FOLDER_LINK_PHARMD"] if programa == "PharmD" else st.secrets["FOLDER_LINK_PHD"]

# --- FILTROS Y ESTADO ---
st.sidebar.markdown("---")
st.sidebar.subheader("Filtros de búsqueda")

# Inicializar estado si no existe
for key in ["cod_sel", "tit_sel", "clave"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# Opciones para los selectbox
codigos = df["Codificación"].dropna().unique().tolist()
titulos = df["TítuloCompletoEspañol"].dropna().unique().tolist()

# --- FILTRO: CODIGO ---
cod_sel = st.sidebar.selectbox("Seleccionar código:", [""] + codigos, index=([""] + codigos).index(st.session_state.cod_sel) if st.session_state.cod_sel in codigos else 0, key="cod_sel")
if st.sidebar.button("Limpiar Filtro", key="clear_cod"):
    st.session_state.cod_sel = ""
    st.rerun()

# --- FILTRO: TITULO ---
tit_sel = st.sidebar.selectbox("Título del curso:", [""] + titulos, index=([""] + titulos).index(st.session_state.tit_sel) if st.session_state.tit_sel in titulos else 0, key="tit_sel")
if st.sidebar.button("Limpiar Filtro", key="clear_tit"):
    st.session_state.tit_sel = ""
    st.rerun()

# --- FILTRO: PALABRA CLAVE ---
clave = st.sidebar.text_input("Palabra clave:", value=st.session_state.clave, key="clave")
if st.sidebar.button("Limpiar Filtro", key="clear_clave"):
    st.session_state.clave = ""
    st.rerun()

# --- FILTRADO ---
df_filtrado = df.copy()
if st.session_state.cod_sel:
    df_filtrado = df_filtrado[df_filtrado["Codificación"] == st.session_state.cod_sel]
elif st.session_state.tit_sel:
    df_filtrado = df_filtrado[df_filtrado["TítuloCompletoEspañol"] == st.session_state.tit_sel]
elif st.session_state.clave:
    palabra = st.session_state.clave.lower()
    df_filtrado = df_filtrado[df_filtrado.apply(lambda row: palabra in str(row).lower(), axis=1)]

# --- UI PRINCIPAL ---
st.title("📘 Bienvenido a Pi DB v3")
st.header(f"📚 Base de Datos de Cursos ({programa})")

if not df_filtrado.empty:
    curso = df_filtrado.iloc[0]
    cod = curso["Codificación"]

    st.subheader(f"Selecciona un curso: {cod}")
    st.markdown(f"**Codificación:** {cod}  **Estado:** {'Activo' if curso['Estatus'] else 'Inactivo'}")
    st.markdown(f"**Título (ES):** {curso['TítuloCompletoEspañol']}")
    st.markdown(f"**Título (EN):** {curso['TítuloCompletoInglés']}")

    st.markdown(f"**Créditos:** {int(curso['Créditos'])}  **Horas Contacto:** {int(curso['HorasContacto'])}")
    st.markdown(f"**Año:** {int(curso['Año'])}  **Semestre:** {int(curso['Semestre'])}")
    st.markdown(f"**Fecha Revisión:** {curso['FechaUltimaRevisión']}")

    st.markdown("---")
    st.subheader("📄 Descripción del Curso")
    st.info(curso["Descripción"])

    st.markdown("---")
    st.subheader("📝 Comentarios")
    st.code(curso["Comentarios"], language="text")

    st.markdown("---")
    st.subheader("📎 Archivos disponibles (Drive)")

    link_folder = folder_base
    folder_row = df_links[df_links["Codificación"] == cod]
    if not folder_row.empty:
        folder_code = folder_row.iloc[0]["Link"]
        st.markdown(f"📁 [Abrir carpeta del curso]({folder_code})")
        st.markdown("_Sugerencia: busca el subfolder llamado **{cod}** en esa carpeta para ver los documentos._")
    else:
        st.warning("No se encontró carpeta compartida para este curso.")
else:
    st.warning("No se encontraron cursos que coincidan con los filtros seleccionados.")
