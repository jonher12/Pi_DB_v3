import streamlit as st
import pandas as pd
import urllib.request
import gspread
from google.oauth2.service_account import Credentials
import hashlib
from datetime import datetime
import pytz
import unicodedata
from sentence_transformers import SentenceTransformer
import faiss
from pathlib import Path

st.set_page_config(page_title="Pi DB v3", layout="wide")

# === PATHS para embeddings ===
BASE_DIR = Path(__file__).parent
INDEX_PATH = BASE_DIR / "pi_db_v3_index.faiss"
DOCS_PATH = BASE_DIR / "pi_db_v3_docs.csv"

# === Cargar embeddings ===
@st.cache_resource
def load_semantic_index():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    index = faiss.read_index(str(INDEX_PATH))
    docs = pd.read_csv(DOCS_PATH)
    return model, index, docs

semantic_model, semantic_index, semantic_docs = load_semantic_index()

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

def verify_login(username, input_password):
    sheet = connect_worksheet(USERS_SHEET_ID, "users")
    records = sheet.get_all_records()
    input_hash = hash_password(input_password)
    for row in records:
        if row["Username"] == username and row["Password"] == input_hash:
            st.session_state["user_role"] = row.get("Role", "user")
            st.session_state["username"] = username
            register_log(username, "login")
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

def register_log(username, action, role=""):
    try:
        sheet = connect_worksheet(LOG_SHEET_ID, "logs")
        ast = pytz.timezone("America/Puerto_Rico")
        now = datetime.now(ast).strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, username, action, role])
    except Exception as e:
        st.warning(f"⚠️ No se pudo registrar el log: {e}")

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

def update_course_field(sheet_id, cod, column_name, new_value):
    try:
        worksheet_name = "tblMaster" if programa == "PharmD" else "tblMasterPhD"
        sheet = connect_worksheet(sheet_id, worksheet_name)
        data = sheet.get_all_records()
        headers = data[0].keys() if data else sheet.row_values(1)
        for i, row in enumerate(data):
            if row["Codificación"] == cod:
                row_num = i + 2
                col_index = list(headers).index(column_name) + 1
                sheet.update_cell(row_num, col_index, new_value)

                pr_time = datetime.now(pytz.timezone("America/Puerto_Rico")).strftime("%Y-%m-%d %H:%M:%S")
                mod_col = list(headers).index("ÚltimaModificaciónPor") + 1
                date_col = list(headers).index("FechaÚltimaModificación") + 1
                sheet.update_cell(row_num, mod_col, st.session_state["username"])
                sheet.update_cell(row_num, date_col, pr_time)

                register_log(st.session_state["username"], f"edit: {cod} - {column_name}")
                break
    except Exception as e:
        st.warning(f"⚠️ No se pudo actualizar el curso: {e}")


# ---- LOGIN ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in: 
    # Encabezado con logos
    empty_col, col1, col2, col3 = st.columns([0.8, 0.7, 2, 1])
    with col1:
        st.image("logo_rcm.png", width=120)
    with col2:
        st.markdown("<h1 style='margin-left: 100px; font-size: 70px;'>Bienvenido a Pi v3</h1>", unsafe_allow_html=True)
    with col3:
        st.image("logo_farmacia.png", width=160)
    st.markdown("<hr style='margin-top: -10px;'>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([2, 1.2, 2])
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
                        st.success("✅ Bienvenido")
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
df = load_sheet(SHEET_IDS[programa])
df_links = load_sheet(DRIVE_LINK_SHEET_ID)

# Registrar cambio de programa y limpiar filtros
if "last_programa" not in st.session_state:
    st.session_state["last_programa"] = programa
elif programa != st.session_state["last_programa"]:
    register_log(st.session_state["username"], f"switch_program: {st.session_state['last_programa']} → {programa}")
    st.session_state["last_programa"] = programa

    # 🔄 Limpiar selección de filtros y búsqueda avanzada
    for key in ["tipo_filtro", "palabra_clave", "dropdown_b_avanzada"]:
        if key in st.session_state:
            del st.session_state[key]

# ✅ FILTROS DINÁMICOS AQUÍ
st.sidebar.markdown("## 🎯 Filtros de Búsqueda Dinámicos")
tipo_filtro = st.sidebar.radio(
    "Selecciona el tipo de filtro:",
    ["Por código", "Por título del curso", "🔍 Búsqueda Avanzada"],
    index=None,
    key="tipo_filtro"
)

df_filtrado = df.copy()
curso = None
palabra_clave = ""  # inicializa por si no aplica

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
    st.sidebar.markdown("### 🔍 Búsqueda Avanzada")
    columnas_busqueda = [
        "Codificación", "TítuloCompletoEspañol", "TítuloCompletoInglés",
        "Descripción", "Comentarios", "AnejosComentarios", "CursosPrerrequisitos", "CursosCorrequisitos"
    ]
    campo_sel = st.sidebar.selectbox("Buscar en:", columnas_busqueda, index=1)
    palabra_clave = st.sidebar.text_input("Ingresa una palabra clave:", key="palabra_clave")

    if campo_sel and palabra_clave.strip() != "":
        def normalizar(texto):
            return unicodedata.normalize("NFKD", str(texto)).encode("ASCII", "ignore").decode("utf-8").lower()

        df_filtrado = df[df[campo_sel].astype(str).apply(normalizar).str.contains(normalizar(palabra_clave))]
        if not df_filtrado.empty:
            st.sidebar.success(f"📌 Búsqueda de _{palabra_clave}_ en **{campo_sel}**")
            register_log(st.session_state["username"], f"search: {campo_sel} ~ {palabra_clave}")

# 🔁 Lógica de control para curso y dropdown
mostrar_dropdown = False
opciones_dropdown = []

if not df_filtrado.empty:
    if len(df_filtrado) == 1:
        curso = df_filtrado.iloc[0]
    elif tipo_filtro == "🔍 Búsqueda Avanzada" and palabra_clave.strip() != "":
        opciones_dropdown = df_filtrado["Codificación"] + " — " + df_filtrado["TítuloCompletoEspañol"]
        mostrar_dropdown = True
    else:
        curso = df_filtrado.iloc[0]
else:
    st.warning("⚠️ No se encontraron cursos con ese filtro.")
    st.stop()

# --- Botón de Cerrar Sesión ---
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Terminar sesión", help="Cerrar sesión y salir de la aplicación"):
    register_log(st.session_state["username"], "logout")
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_role = ""
    st.rerun()

# Encabezado visual
st.markdown("<h1 style='text-align: center;'>Bienvenido a Pi v3</h1>", unsafe_allow_html=True)
st.markdown(f"<h2 style='text-align: center;'>📚 Base de Datos de Cursos ({programa})</h2>", unsafe_allow_html=True)
st.markdown("---")

# 🎯 Mostrar dropdown SOLO si aplica, debajo del encabezado
if mostrar_dropdown and len(opciones_dropdown) > 1:
    st.markdown("""
        <h3 style='color: red; margin-bottom: -0.3rem; padding-bottom: 0;'>Selecciona el curso que deseas consultar:</h3>
        <div style='margin-top: -1.1rem;'>
    """, unsafe_allow_html=True)
    
    seleccion = st.selectbox("", opciones_dropdown, key="dropdown_b_avanzada")
    
    st.markdown("</div><div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    cod_seleccionado = seleccion.split(" — ")[0]
    curso = df_filtrado[df_filtrado["Codificación"] == cod_seleccionado].iloc[0]

elif mostrar_dropdown and len(opciones_dropdown) == 1:
    curso = df_filtrado.iloc[0]

# Registrar vista del curso
if "viewed_course" not in st.session_state or st.session_state["viewed_course"] != curso["Codificación"]:
    register_log(st.session_state["username"], f"view_course: {curso['Codificación']}")
    st.session_state["viewed_course"] = curso["Codificación"]

# Detalle del curso
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
    
    st.markdown("""
    <div style='color: red; font-weight: bold; margin-bottom: 0.5rem;'>
    ⚠️ Cualquier cambio en la descripción será guardado permanentemente.</span>
    </div>
    """, unsafe_allow_html=True)

    descripcion = st.text_area("Descripción", value=curso["Descripción"], height=300)
    if descripcion != curso["Descripción"]:
        update_course_field(SHEET_IDS[programa], curso["Codificación"], "Descripción", descripcion)

    st.markdown("### 🗒️ Comentarios")
    st.markdown("""
    <div style='color: red; font-weight: bold; margin-bottom: 0.5rem;'>
    ⚠️ <span style='color: red;'>Cualquier cambio en los comentarios será guardado permanentemente.</span>
    </div>
    """, unsafe_allow_html=True)
    
    comentarios = st.text_area("Comentarios", value=curso["Comentarios"], height=300)
    if comentarios != curso["Comentarios"]:
        update_course_field(SHEET_IDS[programa], curso["Codificación"], "Comentarios", comentarios)

# === RAG SEM\u00c1NTICO ===
st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
st.markdown("#### \ud83e\udd16 Asistente Virtual (RAG Sem\u00e1ntico)")

if "rag_chat" not in st.session_state:
    st.session_state.rag_chat = []

def responder_pregunta_con_razonamiento(query, df, programa):
    q = query.lower()

    if "cr\u00e9ditos" in q and "total" in q:
        total = df[df["Programa"] == programa]["Cr\u00e9ditos"].sum()
        return f"\ud83d\udcc2 El total de cr\u00e9ditos en **{programa}** es: **{total}**."

    elif "cursos activos" in q:
        activos = df[(df["Programa"] == programa) & (df["Estatus"] == 1)].shape[0]
        return f"\ud83d\udcd8 Hay **{activos} cursos activos** en el programa **{programa}**."

    elif "promedio de cr\u00e9ditos" in q:
        promedio = df[df["Programa"] == programa]["Cr\u00e9ditos"].mean()
        return f"\ud83d\udcca El promedio de cr\u00e9ditos por curso en **{programa}** es: **{promedio:.2f}**."

    elif "primer a\u00f1o" in q and "cursos" in q:
        count = df[(df["Programa"] == programa) & (df["A\u00f1o"] == 1)].shape[0]
        return f"\ud83d\udcda Hay **{count} cursos** de primer a\u00f1o en **{programa}**."

    else:
        return None

query = st.chat_input("Pregunta aqu\u00ed...", key="chat_input_semantico")

if query:
    st.session_state.rag_chat.append({"role": "user", "content": query})

    respuesta_tabular = responder_pregunta_con_razonamiento(query, df, programa)

    if respuesta_tabular:
        st.session_state.rag_chat.append({"role": "assistant", "content": respuesta_tabular})
        register_log(st.session_state["username"], f"chatbot_tabular_query: {query}")
    else:
        q_emb = semantic_model.encode([query])
        D, I = semantic_index.search(q_emb, k=5)

        resultados = []
        for idx in I[0]:
            fila = semantic_docs.iloc[idx]
            cod = fila["Codificaci\u00f3n"]
            titulo = fila.get("T\u00edtuloCompletoEspa\u00f1ol", "")
            programa_fila = fila["Programa"]
            texto = " ".join([str(fila[col]) for col in semantic_docs.columns])

            folder_row = df_links[(df_links["Codificaci\u00f3n"] == cod) & (df_links["Programa"] == programa_fila)]
            if not folder_row.empty:
                folder_id = folder_row.iloc[0]["FolderID"]
                link_drive = f"[\ud83d\udcc2 Carpeta de {cod}](https://drive.google.com/drive/folders/{folder_id})"
            else:
                link_drive = "\u26a0\ufe0f Carpeta no encontrada"

            resultado = f"## \ud83d\udcd8 {programa_fila} \u2014 {cod} \u2014 {titulo}\n\n{texto[:500]}...\n\n{link_drive}"
            resultados.append(resultado)

        respuesta = "### \ud83d\udd0e Resultados sem\u00e1nticos:\n\n" + "\n\n---\n\n".join(resultados)
        st.session_state.rag_chat.append({"role": "assistant", "content": respuesta})
        register_log(st.session_state["username"], f"chatbot_semantic_query: {query}")

# 🔄 Mostrar mensajes del chat
for msg in st.session_state.rag_chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
# Pie de página
st.markdown("---")
st.caption("División de Evaluación de la Efectividad Curricular e Institucional. Todos los derechos reservados. JHA 2025©. Administrador: Jonathan Hernández-Agosto, EdD, GCG.")
