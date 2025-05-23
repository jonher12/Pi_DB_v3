import streamlit as st
import pandas as pd
import urllib.request

st.set_page_config(page_title="Pi DB v3", layout="wide")

SHEET_IDS = {
    "PharmD": st.secrets["SHEET_ID_PHARMD"].strip(),
    "PhD": st.secrets["SHEET_ID_PHD"].strip()
}

FOLDER_LINKS = {
    "PharmD": st.secrets["FOLDER_LINK_PHARMD"],
    "PhD": st.secrets["FOLDER_LINK_PHD"]
}

DRIVE_LINK_SHEET_ID = st.secrets["DRIVE_LINK_SHEET_ID"].strip()

# Load Google Sheet
@st.cache_data

def load_sheet(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        response = urllib.request.urlopen(url)
        if response.status != 200:
            st.error(f"No se pudo acceder al Google Sheet. Código: {response.status}")
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
        st.error(f"Error al intentar leer Google Sheet: {e}")
        return pd.DataFrame()

# Login system
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.image("logo RCM.jpg", width=100)
    with col3:
        st.image("Farmacia 110 ESP.png", width=150)
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>Bienvenido a Pi DB v3</h1>", unsafe_allow_html=True)
        st.markdown("---")
        with st.form("login"):
            user = st.text_input("Usuario:")
            password = st.text_input("Contraseña:", type="password")
            if st.form_submit_button("Ingresar"):
                if user == "j" and password == "1":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")
else:
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
    st.session_state["cod_sel"] = st.sidebar.selectbox(
        "Seleccionar código:", codigos,
        index=codigos.index(st.session_state["cod_sel"]) if st.session_state["cod_sel"] in codigos else 0,
        key="cod_sel")

    st.sidebar.markdown("#### Título del curso:")
    st.session_state["tit_sel"] = st.sidebar.selectbox(
        "Título del curso:", titulos,
        index=titulos.index(st.session_state["tit_sel"]) if st.session_state["tit_sel"] in titulos else 0,
        key="tit_sel")

    st.sidebar.markdown("#### Palabra clave:")
    st.session_state["clave_sel"] = st.sidebar.text_input("Palabra clave:", value=st.session_state["clave_sel"], key="clave_sel")

    df_filtrado = df.copy()
    if st.session_state["cod_sel"]:
        df_filtrado = df[df["Codificación"] == st.session_state["cod_sel"]]
    elif st.session_state["tit_sel"]:
        df_filtrado = df[df["TítuloCompletoEspañol"] == st.session_state["tit_sel"]]
    elif st.session_state["clave_sel"]:
        df_filtrado = df[df.apply(lambda row: st.session_state["clave_sel"].lower() in str(row).lower(), axis=1)]

    curso = df_filtrado.iloc[0] if not df_filtrado.empty else df.iloc[0]

    st.markdown("<h1 style='text-align: center;'>📚 Base de Datos de Cursos ({})</h1>".format(programa), unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"""
        **<span style='font-size: 18px;'>Codificación:</span>** {curso['Codificación']}  
        **<span style='font-size: 18px;'>Estado:</span>** {'Activo' if curso['Estatus'] == 1 else 'Inactivo'}  
        **<span style='font-size: 18px;'>Título (ES):</span>** {curso['TítuloCompletoEspañol']}  
        **<span style='font-size: 18px;'>Título (EN):</span>** {curso['TítuloCompletoInglés']}  
        **<span style='font-size: 18px;'>Créditos:</span>** {curso['Créditos']}  
        **<span style='font-size: 18px;'>Horas Contacto:</span>** {curso['HorasContacto']}  
        **<span style='font-size: 18px;'>Año:</span>** {curso['Año']}  
        **<span style='font-size: 18px;'>Semestre:</span>** {curso['Semestre']}  
        **<span style='font-size: 18px;'>Fecha Revisión:</span>** {curso['FechaUltimaRevisión']}
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 📝 Descripción del Curso")
        st.text_area("", value=curso["Descripción"], height=200)
        st.markdown("### 💬 Comentarios")
        st.text_area("", value=curso["Comentarios"], height=150)

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
