import streamlit as st
import pandas as pd
import os

# ---------- Setup ----------
BASE_DIR = os.path.dirname(__file__)
CSV_FILE = os.path.join(BASE_DIR, "cursos.csv")

# Create CSV if not found
if not os.path.exists(CSV_FILE):
    df = pd.DataFrame([
        {
            "code": "FARM_7101",
            "title_es": "Desarrollo de Intervenciones Avanzadas en Comunicación en Salud",
            "title_en": "Development of Advanced Interventions in Health Communications",
            "credits": 3,
            "contact_hours": 54,
            "year": 1,
            "semester": 1,
            "status": "Activo",
            "description": "Curso centrado en estrategias de comunicación en salud",
            "comments": "Actualizado 2022"
        },
        {
            "code": "FARM_7102",
            "title_es": "Terapéutica Avanzada",
            "title_en": "Advanced Therapeutics",
            "credits": 4,
            "contact_hours": 60,
            "year": 1,
            "semester": 2,
            "status": "Activo",
            "description": "Curso sobre uso clínico avanzado de medicamentos",
            "comments": "Modificado por comité académico 2021"
        }
    ])
    df.to_csv(CSV_FILE, index=False)

# Load data
course_df = pd.read_csv(CSV_FILE)

# ---------- Login ----------
st.title("📘 Bienvenido a Pi v2")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.form("login"):
        user = st.text_input("Usuario:")
        password = st.text_input("Contraseña:", type="password")
        if st.form_submit_button("Login"):
            if user == "admin" and password == "1234":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas")
else:
    st.header("📚 Base de Datos de Cursos")

    selected_code = st.selectbox("Seleccione un curso:", course_df["code"].tolist())
    row = course_df[course_df["code"] == selected_code].iloc[0]

    st.markdown(f"""
    **Codificación:** {row['code']} &nbsp;&nbsp;&nbsp; **Estado:** {row['status']}  
    **Título (ES):** {row['title_es']}  
    **Título (EN):** {row['title_en']}  
    **Créditos:** {row['credits']} &nbsp;&nbsp;&nbsp; **Horas Contacto:** {row['contact_hours']}  
    **Año:** {row['year']} &nbsp;&nbsp;&nbsp; **Semestre:** {row['semester']}  
    """, unsafe_allow_html=True)

    # Editable fields
    new_desc = st.text_area("📄 Descripción del Curso", value=row["description"], height=150)
    new_comm = st.text_area("📑 Comentarios", value=row["comments"], height=150)

    if st.button("💾 Guardar cambios"):
        idx = course_df[course_df["code"] == selected_code].index[0]
        course_df.at[idx, "description"] = new_desc
        course_df.at[idx, "comments"] = new_comm
        course_df.to_csv(CSV_FILE, index=False)
        st.success("Cambios guardados correctamente.")

    st.markdown("---")
    st.subheader("📎 Archivos disponibles")

    folder_path = os.path.join(BASE_DIR, "www", selected_code)
    if not os.path.exists(folder_path):
        st.warning("No se encontraron archivos.")
    else:
        files = sorted(os.listdir(folder_path))
        if not files:
            st.info("No hay archivos disponibles.")
        else:
            for file in files:
                filepath = os.path.join(folder_path, file)
                with open(filepath, "rb") as f:
                    st.download_button(
                        label=f"📎 Descargar {file}",
                        data=f,
                        file_name=file,
                        mime="application/octet-stream"
                    )
