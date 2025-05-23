import streamlit as st
import pandas as pd
import urllib.request

st.set_page_config(page_title="📘 Pi DB v3", layout="wide")

SHEET_IDS = {
    "PharmD": st.secrets["SHEET_ID_PHARMD"].strip(),
    "PhD": st.secrets["SHEET_ID_PHD"].strip()
}

FOLDER_LINKS = {
    "PharmD": st.secrets["FOLDER_LINK_PHARMD"],
    "PhD": st.secrets["FOLDER_LINK_PHD"]
}

DRIVE_LINK_SHEET_ID = st.secrets["DRIVE_LINK_SHEET_ID"].strip()

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
                try:
                    df[col] = df[col].fillna(0).astype(int)
                except:
                    df[col] = df[col].astype(str)
        return df
    except Exception as e:
        st.error(f"❌ Error al intentar leer Google Sheet: {e}")
        return pd.DataFrame()

# ---- LOGIN ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # Encabezado con logos e ícono π
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.image("logo RCM.png", width=100)
    with col2:
        st.markdown("<h1 style='text-align: center; display: flex; align-items: center; justify-content: center;'>"
                    "<img src='pi.png' width='40' style='margin-right: 10px;'> Bienvenido a Pi DB v3</h1>", unsafe_allow_html=True)
    with col3:
        st.image("Farmacia 110 ESP.png", width=140)

    st.markdown("<hr style='margin-top: -10px;'>", unsafe_allow_html=True)

    # Login box estilo pop-up
    col_login, _, _ = st.columns([2, 1, 1])
    with col_login:
        with st.container(border=True):
            st.markdown("### 🔐 Iniciar sesión")
            with st.form("login"):
                user = st.text_input("Usuario:")
                password = st.text_input("Contraseña:", type="password")
                if st.form_submit_button("Ingresar"):
                    if user == "j" and password == "1":
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas")
            # Nota legal
            st.markdown(
                "<div style='text-align: center; margin-top: 10px;'>"
                "<small>División de Evaluación de la Efectividad Curricular e Institucional. "
                "Todos los derechos reservados. JHA 2025©. Administrador: Jonathan Hernández-Agosto, EdD, GCG.</small>"
                "</div>",
                unsafe_allow_html=True
            )
    st.stop()

# App body
st.sidebar.title("Navegación")
programa = st.sidebar.radio("Selecciona el programa:", ["PharmD", "PhD"], key="programa")
df = load_sheet(SHEET_IDS[programa])
df_links = load_sheet(DRIVE_LINK_SHEET_ID)

if df.empty or df_links.empty:
    st.stop()

for key in ["cod_sel", "tit_sel", "clave_sel"]:
    if key not in st.session_state:
        st.session_state[key] = ""

st.sidebar.markdown("---")
st.sidebar.markdown("### Filtros de búsqueda")
st.sidebar.caption("ℹ️ Para utilizar un filtro diferente, primero pulsa 'Limpiar Filtro'.")

if st.sidebar.button("🔄 Limpiar todos los filtros", key="btn_clear_all"):
    st.session_state["cod_sel"] = ""
    st.session_state["tit_sel"] = ""
    st.session_state["clave_sel"] = ""
    st.rerun()

codigos = sorted(df["Codificación"].dropna().unique().tolist())
titulos = sorted(df["TítuloCompletoEspañol"].dropna().unique().tolist())

st.sidebar.markdown("#### Seleccionar código:")
st.sidebar.selectbox("Seleccionar código:", codigos, index=codigos.index(st.session_state["cod_sel"]) if st.session_state["cod_sel"] in codigos else 0, key="cod_sel")

st.sidebar.markdown("#### Título del curso:")
st.sidebar.selectbox("Título del curso:", titulos, index=titulos.index(st.session_state["tit_sel"]) if st.session_state["tit_sel"] in titulos else 0, key="tit_sel")

st.sidebar.markdown("#### Palabra clave:")
st.sidebar.text_input("Palabra clave:", value=st.session_state["clave_sel"], key="clave_sel")

df_filtrado = df.copy()
if st.session_state["cod_sel"]:
    df_filtrado = df[df["Codificación"] == st.session_state["cod_sel"]]
elif st.session_state["tit_sel"]:
    df_filtrado = df[df["TítuloCompletoEspañol"] == st.session_state["tit_sel"]]
elif st.session_state["clave_sel"]:
    df_filtrado = df[df.apply(lambda row: st.session_state["clave_sel"].lower() in str(row).lower(), axis=1)]

curso = df_filtrado.iloc[0] if not df_filtrado.empty else df.iloc[0]

st.markdown("<h1 style='text-align: center;'>Bienvenido a Pi DB v3</h1>", unsafe_allow_html=True)
st.markdown(f"<h2 style='text-align: center;'>📚 Base de Datos de Cursos ({programa})</h2>", unsafe_allow_html=True)
st.markdown("---")

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
    <b>Fecha Revisión:</b> {curso['FechaUltimaRevisión']}<br>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("### 📝 Descripción del Curso")
    st.text_area("", value=curso["Descripción"], height=220)

    st.markdown("### 🗒️ Comentarios")
    st.text_area("", value=curso["Comentarios"], height=180)

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
st.caption("División de Evaluación de la Efectividad Curricular e Institucional. Todos los derechos reservados. JHA 2025©. Administrador: Jonathan Hernández-Agosto, EdD, GCG.")

