import streamlit as st
import pandas as pd
import urllib.request

st.set_page_config(page_title="📘 Pi DB v3", layout="wide")

# Load secrets
SHEET_IDS = {
    "PharmD": st.secrets["SHEET_ID_PHARMD"].strip(),
    "PhD": st.secrets["SHEET_ID_PHD"].strip()
}

FOLDER_LINKS = {
    "PharmD": st.secrets["FOLDER_LINK_PHARMD"],
    "PhD": st.secrets["FOLDER_LINK_PHD"]
}

DRIVE_LINK_SHEET_ID = st.secrets["DRIVE_LINK_SHEET_ID"].strip()

# Load sheet as DataFrame
def load_sheet(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        response = urllib.request.urlopen(url)
        if response.status != 200:
            st.error(f"❌ No se pudo acceder al Google Sheet. Código: {response.status}")
            return pd.DataFrame()
        df = pd.read_csv(url)
        for col in ["Créditos", "HorasContacto", "Año", "Semestre"]:
            if col in df.columns:
                df[col] = df[col].fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"❌ Error al intentar leer Google Sheet: {e}")
        return pd.DataFrame()

# --- Login ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("📘 Bienvenido a Pi DB v3")
    with st.form("login"):
        user = st.text_input("Usuario:")
        password = st.text_input("Contraseña:", type="password")
        if st.form_submit_button("Ingresar"):
            if user == "j" and password == "1":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas")
    st.stop()

# --- Navegación y carga de datos ---
st.sidebar.title("Navegación")
programa = st.sidebar.radio("Selecciona el programa:", ["PharmD", "PhD"], key="programa")
df = load_sheet(SHEET_IDS[programa])
df_links = load_sheet(DRIVE_LINK_SHEET_ID)

if df.empty or df_links.empty:
    st.stop()

# Estado inicial
for key in ["cod_sel", "tit_sel", "clave_sel"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# Captura de botones antes de instanciar widgets
clear_all = st.sidebar.button("🔄 Limpiar todos los filtros")
clear_cod = st.sidebar.button("Limpiar Filtro", key="clear_cod")
clear_tit = st.sidebar.button("Limpiar Filtro", key="clear_tit")
clear_kwd = st.sidebar.button("Limpiar Filtro", key="clear_kwd")

if clear_all or clear_cod or clear_tit or clear_kwd:
    if clear_all or clear_cod:
        st.session_state["cod_sel"] = ""
    if clear_all or clear_tit:
        st.session_state["tit_sel"] = ""
    if clear_all or clear_kwd:
        st.session_state["clave_sel"] = ""
    st.rerun()

# --- Filtros ---
st.sidebar.markdown("---")
st.sidebar.markdown("### Filtros de búsqueda")
st.sidebar.caption("ℹ️ Para utilizar un filtro diferente, primero pulsa 'Limpiar Filtro'.")

codigos = sorted(df["Codificación"].dropna().unique())
titulos = sorted(df["TítuloCompletoEspañol"].dropna().unique())

# Código
st.sidebar.markdown("#### Seleccionar código:")
cod_sel = st.sidebar.selectbox("Seleccionar código:", [""] + codigos, index=0 if st.session_state["cod_sel"] == "" else codigos.index(st.session_state["cod_sel"]) + 1, key="cod_sel")
st.sidebar.button("Limpiar Filtro", key="clear_cod_below")

# Título
st.sidebar.markdown("#### Título del curso:")
tit_sel = st.sidebar.selectbox("Título del curso:", [""] + titulos, index=0 if st.session_state["tit_sel"] == "" else titulos.index(st.session_state["tit_sel"]) + 1, key="tit_sel")
st.sidebar.button("Limpiar Filtro", key="clear_tit_below")

# Palabra clave
st.sidebar.markdown("#### Palabra clave:")
clave_sel = st.sidebar.text_input("Palabra clave:", value=st.session_state["clave_sel"], key="clave_sel")
st.sidebar.button("Limpiar Filtro", key="clear_kwd_below")

# --- Aplicar filtros ---
df_filtrado = df.copy()
if st.session_state["cod_sel"]:
    df_filtrado = df[df["Codificación"] == st.session_state["cod_sel"]]
elif st.session_state["tit_sel"]:
    df_filtrado = df[df["TítuloCompletoEspañol"] == st.session_state["tit_sel"]]
elif st.session_state["clave_sel"]:
    df_filtrado = df[df.apply(lambda row: st.session_state["clave_sel"].lower() in str(row).lower(), axis=1)]

curso = df_filtrado.iloc[0] if not df_filtrado.empty else df.iloc[0]

st.title("📘 Bienvenido a Pi DB v3")
st.header(f"📚 Base de Datos de Cursos ({programa})")

if curso is None:
    st.warning("No se encontraron cursos que coincidan con los filtros seleccionados.")
    st.stop()

st.markdown(f"""
**Codificación:** {curso['Codificación']} &nbsp;&nbsp;&nbsp; **Estado:** {'Activo' if curso['Estatus'] == 1 else 'Inactivo'}  
**Título (ES):** {curso['TítuloCompletoEspañol']}  
**Título (EN):** {curso['TítuloCompletoInglés']}  
**Créditos:** {curso['Créditos']} &nbsp;&nbsp;&nbsp; **Horas Contacto:** {curso['HorasContacto']}  
**Año:** {curso['Año']} &nbsp;&nbsp;&nbsp; **Semestre:** {curso['Semestre']}  
**Fecha Revisión:** {curso['FechaUltimaRevisión']}
""", unsafe_allow_html=True)

st.text_area("📄 Descripción del Curso", value=curso["Descripción"], height=150)
st.text_area("📑 Comentarios", value=curso["Comentarios"], height=150)

# --- Enlaces a documentos ---
st.markdown("---")
st.subheader("📎 Archivos disponibles (Drive)")
st.markdown("Consulta los documentos específicos del curso en su subcarpeta dedicada:")

folder_row = df_links[(df_links["Codificación"] == curso['Codificación']) & (df_links["Programa"] == programa)]
if not folder_row.empty:
    folder_id = folder_row.iloc[0]["FolderID"]
    subfolder_url = f"https://drive.google.com/drive/folders/{folder_id}"
    st.markdown(f"[📂 Abrir carpeta del curso {curso['Codificación']}]({subfolder_url})")
else:
    st.warning("⚠️ No se encontró el enlace directo para este curso.")

st.markdown("---")

