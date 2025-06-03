import streamlit as st
import pandas as pd
import urllib.request
import gspread
from google.oauth2.service_account import Credentials
import hashlib
from datetime import datetime
import pytz

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
USERS_SHEET_ID = st.secrets["USERS_SHEET_ID"].strip()
LOG_SHEET_ID = st.secrets["LOG_SHEET_ID"].strip()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def connect_worksheet(sheet_id, worksheet_name):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open_by_key(sheet_id).worksheet(worksheet_name)

def get_ast_timestamp():
    return datetime.now(pytz.timezone("America/Puerto_Rico")).strftime("%Y-%m-%d %H:%M:%S")

def register_log(username, action, role=""):
    try:
        sheet = connect_worksheet(LOG_SHEET_ID, "logs")
        now = get_ast_timestamp()
        sheet.append_row([now, username, action, role])
    except Exception as e:
        st.warning(f"⚠️ No se pudo registrar el log: {e}")

def verify_login(username, input_password):
    sheet = connect_worksheet(USERS_SHEET_ID, "users")
    records = sheet.get_all_records()
    input_hash = hash_password(input_password)
    for row in records:
        if row["Username"] == username and row["Password"] == input_hash:
            st.session_state["user_role"] = row.get("Role", "user")
            st.session_state["username"] = username
            register_log(username, "login", st.session_state["user_role"])
            return True
    return False

def update_password(username, new_password):
    sheet = connect_worksheet(USERS_SHEET_ID, "users")
    records = sheet.get_all_records()
    for i, row in enumerate(records):
        if row["Username"] == username:
            sheet.update_cell(i + 2, 2, hash_password(new_password))
            register_log(username, "password_reset")
            return True
    return False

def load_sheet(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        response = urllib.request.urlopen(url)
        if response.status != 200:
            st.error(f"❌ Error al acceder Google Sheet: {response.status}")
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
        st.error(f"❌ Error al leer Google Sheet: {e}")
        return pd.DataFrame()

def update_course_field(sheet_id, cod, column_name, new_value):
    try:
        worksheet_name = "tblMaster" if st.session_state["programa"] == "PharmD" else "tblMasterPhD"
        sheet = connect_worksheet(sheet_id, worksheet_name)
        data = sheet.get_all_records()
        headers = sheet.row_values(1)
        for i, row in enumerate(data):
            if row["Codificación"] == cod:
                row_number = i + 2
                col_index = headers.index(column_name) + 1
                sheet.update_cell(row_number, col_index, new_value)
                # Actualizar seguimiento
                mod_col = headers.index("ÚltimaModificaciónPor") + 1
                date_col = headers.index("FechaÚltimaModificación") + 1
                sheet.update_cell(row_number, mod_col, st.session_state["username"])
                sheet.update_cell(row_number, date_col, get_ast_timestamp())
                register_log(st.session_state["username"], f"edit: {cod} - {column_name}")
                break
    except Exception as e:
        st.warning(f"⚠️ No se pudo actualizar el curso: {e}")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([0.8, 1.4, 1])
    with col1:
        st.image("logo_rcm.png", width=120)
    with col2:
        st.markdown("<h1 style='text-align: center; font-size: 70px;'>Bienvenido a Pi v3</h1>", unsafe_allow_html=True)
    with col3:
        st.image("logo_farmacia.png", width=160)
    st.markdown("<hr style='margin-top: -10px;'>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        with st.container(border=True):
            st.markdown("### 🔐 Iniciar sesión")
            with st.form("login_form"):
                user = st.text_input("Usuario:")
                password = st.text_input("Contraseña:", type="password")
                login_btn = st.form_submit_button("Ingresar")
                if login_btn:
                    if verify_login(user, password):
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos.")
            with st.expander("🔑 ¿Olvidaste tu contraseña?"):
                username_reset = st.text_input("Usuario:", key="reset_user")
                new_pw = st.text_input("Nueva contraseña", type="password", key="new_pw")
                confirm_pw = st.text_input("Confirmar contraseña", type="password", key="confirm_pw")
                if st.button("Actualizar contraseña"):
                    if not username_reset:
                        st.warning("⚠️ Ingresa tu usuario.")
                    elif new_pw != confirm_pw:
                        st.warning("⚠️ Las contraseñas no coinciden.")
                    else:
                        if update_password(username_reset, new_pw):
                            st.success("✅ Contraseña actualizada.")
                        else:
                            st.error("❌ Usuario no encontrado.")
        st.markdown("<div style='text-align: center; margin-top: 10px;'>"
                    "<small>División de Evaluación de la Efectividad Curricular e Institucional. "
                    "Todos los derechos reservados. JHA 2025©. Administrador: Jonathan Hernández-Agosto, EdD, GCG.</small></div>",
                    unsafe_allow_html=True)
    st.stop()

# App body
st.sidebar.title("Navegación")
programa = st.sidebar.radio("Selecciona el Programa:", ["PharmD", "PhD"], key="programa")
st.session_state["programa"] = programa  # Guardamos para update_course_field
df = load_sheet(SHEET_IDS[programa])
df_links = load_sheet(DRIVE_LINK_SHEET_ID)

# Registrar cambio de programa
if "last_programa" not in st.session_state:
    st.session_state["last_programa"] = programa
elif programa != st.session_state["last_programa"]:
    register_log(st.session_state["username"], f"switch_program: {st.session_state['last_programa']} → {programa}")
    st.session_state["last_programa"] = programa

# Filtros y logs
for key in ["cod_sel", "tit_sel", "clave_sel"]:
    if key not in st.session_state:
        st.session_state[key] = ""

st.sidebar.markdown("---")
st.sidebar.markdown("### Filtros de Búsqueda")
st.sidebar.caption("ℹ️ Para utilizar un filtro diferente, primero pulsa 'Limpiar Filtros'.")

if st.sidebar.button("🔄 Limpiar Filtros", key="btn_clear_all"):
    st.session_state["cod_sel"] = ""
    st.session_state["tit_sel"] = ""
    st.session_state["clave_sel"] = ""
    register_log(st.session_state["username"], "clear_filters")
    st.rerun()

codigos = sorted(df["Codificación"].dropna().unique().tolist())
titulos = sorted(df["TítuloCompletoEspañol"].dropna().unique().tolist())

st.sidebar.selectbox("Seleccionar Código:", codigos, index=codigos.index(st.session_state["cod_sel"]) if st.session_state["cod_sel"] in codigos else 0, key="cod_sel")
st.sidebar.selectbox("Título del Curso:", titulos, index=titulos.index(st.session_state["tit_sel"]) if st.session_state["tit_sel"] in titulos else 0, key="tit_sel")
st.sidebar.text_input("Palabra Clave:", value=st.session_state["clave_sel"], key="clave_sel")

# Log búsqueda
if st.session_state.get("cod_sel"):
    register_log(st.session_state["username"], f"search: code = {st.session_state['cod_sel']}")
elif st.session_state.get("tit_sel"):
    register_log(st.session_state["username"], f"search: title = {st.session_state['tit_sel']}")
elif st.session_state.get("clave_sel"):
    register_log(st.session_state["username"], f"search: keyword = {st.session_state['clave_sel']}")

if df.empty or df_links.empty:
    st.stop()

# Filtrar curso
df_filtrado = df.copy()
if st.session_state["cod_sel"]:
    df_filtrado = df[df["Codificación"] == st.session_state["cod_sel"]]
elif st.session_state["tit_sel"]:
    df_filtrado = df[df["TítuloCompletoEspañol"] == st.session_state["tit_sel"]]
elif st.session_state["clave_sel"]:
    df_filtrado = df[df.apply(lambda row: st.session_state["clave_sel"].lower() in str(row).lower(), axis=1)]

curso = df_filtrado.iloc[0] if not df_filtrado.empty else df.iloc[0]

# Log vista curso
if "viewed_course" not in st.session_state or st.session_state["viewed_course"] != curso["Codificación"]:
    register_log(st.session_state["username"], f"view_course: {curso['Codificación']}")
    st.session_state["viewed_course"] = curso["Codificación"]

st.markdown("<h1 style='text-align: center;'>Bienvenido a Pi v3</h1>", unsafe_allow_html=True)
st.markdown(f"<h2 style='text-align: center;'>📚 Base de Datos de Cursos ({programa})</h2>", unsafe_allow_html=True)
st.markdown("---")

# Detalle del curso editable
col1, col2 = st.columns([1, 2])
with col1:
    codificacion = st.text_input("Codificación", value=curso["Codificación"], disabled=True)
    estatus = st.selectbox("Estado", ["Activo", "Inactivo"], index=0 if curso["Estatus"] == 1 else 1)
    titulo_es = st.text_input("Título (ES)", value=curso["TítuloCompletoEspañol"])
    titulo_en = st.text_input("Título (EN)", value=curso["TítuloCompletoInglés"])
    creditos = st.number_input("Créditos", value=int(curso["Créditos"]), min_value=0)
    horas = st.number_input("Horas Contacto", value=int(curso["HorasContacto"]), min_value=0)
    anio = st.number_input("Año", value=int(curso["Año"]), min_value=1)
    semestre = st.selectbox("Semestre", [1, 2], index=(int(curso["Semestre"]) - 1))
    fecha_rev = st.text_input("Fecha Revisión", value=str(curso["FechaUltimaRevisión"]))

    # Revisión de cambios
    if estatus != ('Activo' if curso["Estatus"] == 1 else 'Inactivo'):
        update_course_field(SHEET_IDS[programa], codificacion, "Estatus", 1 if estatus == "Activo" else 0)
    if titulo_es != curso["TítuloCompletoEspañol"]:
        update_course_field(SHEET_IDS[programa], codificacion, "TítuloCompletoEspañol", titulo_es)
    if titulo_en != curso["TítuloCompletoInglés"]:
        update_course_field(SHEET_IDS[programa], codificacion, "TítuloCompletoInglés", titulo_en)
    if creditos != curso["Créditos"]:
        update_course_field(SHEET_IDS[programa], codificacion, "Créditos", creditos)
    if horas != curso["HorasContacto"]:
        update_course_field(SHEET_IDS[programa], codificacion, "HorasContacto", horas)
    if anio != curso["Año"]:
        update_course_field(SHEET_IDS[programa], codificacion, "Año", anio)
    if semestre != curso["Semestre"]:
        update_course_field(SHEET_IDS[programa], codificacion, "Semestre", semestre)
    if fecha_rev != curso["FechaUltimaRevisión"]:
        update_course_field(SHEET_IDS[programa], codificacion, "FechaUltimaRevisión", fecha_rev)

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
        update_course_field(SHEET_IDS[programa], codificacion, "Descripción", descripcion)

    st.markdown("### 🗒️ Comentarios")
    comentarios = st.text_area("Comentarios", value=curso["Comentarios"], height=300)
    if comentarios != curso["Comentarios"]:
        update_course_field(SHEET_IDS[programa], codificacion, "Comentarios", comentarios)

st.markdown("---")
st.caption("División de Evaluación de la Efectividad Curricular e Institucional. Todos los derechos reservados. JHA 2025©. Administrador: Jonathan Hernández-Agosto, EdD, GCG.")
