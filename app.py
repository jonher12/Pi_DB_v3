import streamlit as st
import pandas as pd

# ---------- CONFIGURACIÓN ----------
# IDs de Google Sheets definidos como secretos
SHEET_IDS = {
    "PharmD": st.secrets["SHEET_ID_PHARMD"],
    "PhD": st.secrets["SHEET_ID_PHD"]
}

FOLDER_LINKS = {
    "PharmD": st.secrets["FOLDER_LINK_PHARMD"],
    "PhD": st.secrets["FOLDER_LINK_PHD"]
}

DRIVE_LINK_SHEET_ID = st.secrets["DRIVE_LINK_SHEET_ID"]

def load_sheet(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    return pd.read_csv(url)

# ---------- AUTENTICACIÓN SIMPLE ----------
st.set_page_config("📘 Pi DB v3", layout="wide")
st.title("📘 Bienvenido a Pi DB v3")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.form("login"):
        user = st.text_input("Usuario:")
        password = st.text_input("Contraseña:", type="password")
        submit = st.form_submit_button("Ingresar")
        if submit:
            if user == "j" and password == "1":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas")
else:
    st.sidebar.title("Navegación")
    programa = st.sidebar.radio("Selecciona el programa:", ["PharmD", "PhD"])
    df = load_sheet(SHEET_IDS[programa])
    df_links = load_sheet(DRIVE_LINK_SHEET_ID)

    st.header(f"📚 Base de Datos de Cursos ({programa})")
    codigo = st.selectbox("Seleccione un curso:", sorted(df["Codificación"].dropna().unique()))

    curso = df[df["Codificación"] == codigo].iloc[0]

    st.markdown(f"""
    **Codificación:** {curso['Codificación']} &nbsp;&nbsp;&nbsp; **Estado:** {'Activo' if curso['Estatus'] == 1 else 'Inactivo'}  
    **Título (ES):** {curso['TítuloCompletoEspañol']}  
    **Título (EN):** {curso['TítuloCompletoInglés']}  
    **Créditos:** {curso['Créditos']} &nbsp;&nbsp;&nbsp; **Horas Contacto:** {curso['HorasContacto']}  
    **Año:** {curso['Año']} &nbsp;&nbsp;&nbsp; **Semestre:** {curso['Semestre']}  
    **Fecha Revisión:** {curso['FechaUltimaRevisión']}
    """, unsafe_allow_html=True)

    new_desc = st.text_area("📄 Descripción del Curso", value=curso["Descripción"], height=150)
    new_comm = st.text_area("📑 Comentarios", value=curso["Comentarios"], height=150)

    st.markdown("---")
    st.subheader("📎 Archivos disponibles (Drive)")
    st.markdown("Consulta los documentos específicos del curso en su subcarpeta dedicada:")

    folder_row = df_links[(df_links["Codificación"] == codigo) & (df_links["Programa"] == programa)]
    if not folder_row.empty:
        folder_id = folder_row.iloc[0]["FolderID"]
        subfolder_url = f"https://drive.google.com/drive/folders/{folder_id}"
        st.markdown(f"[📂 Abrir carpeta del curso {codigo}]({subfolder_url})")
    else:
        st.warning("⚠️ No se encontró el enlace directo para este curso.")

    st.markdown("---")
    st.caption(f"📁 Carpeta general de {programa}: {FOLDER_LINKS[programa]}")
