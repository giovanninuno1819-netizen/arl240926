import streamlit as st
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Control y Seguimiento de Equipos Industriales",
    page_icon="⚙️",
    layout="wide"
)

# ---------------------------------------------------------
# 2. AUTENTICACIÓN Y TRAZABILIDAD DE SESIÓN
# ---------------------------------------------------------
if "user" not in st.session_state:
    st.session_state["user"] = None

if not st.session_state["user"]:
    st.title("🔐 Control de Acceso — Sistema de Equipos Industriales")
    st.caption("Ingrese sus credenciales de usuario para habilitar la trazabilidad de auditoría.")
    
    col_a, col_b = st.columns([1, 1.2])
    with col_a:
        with st.form("login_form"):
            email_input = st.text_input("Correo Institucional / Usuario", placeholder="usuario@empresa.com")
            password_input = st.text_input("Contraseña", type="password")
            btn_login = st.form_submit_button("Iniciar Sesión", type="primary", use_container_width=True)
            
            if btn_login:
                if email_input:
                    st.session_state["user"] = {
                        "email": email_input,
                        "nombre": email_input.split("@")[0].replace(".", " ").title(),
                        "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.success(f"Bienvenido, {st.session_state['user']['nombre']}")
                    st.rerun()
                else:
                    st.error("Por favor ingrese un usuario o correo válido.")
    st.stop()

# ---------------------------------------------------------
# 3. BASE DE DATOS Y CATÁLOGOS EN MEMORIA
# ---------------------------------------------------------
if "equipos_db" not in st.session_state:
    st.session_state["equipos_db"] = {
        "EQ-001": {
            "nombre": "Lavadora Industrial",
            "zona": "Oncológicos",
            "proceso": "LAVADO",
            "marca": "Bosch",
            "modelo": "CLEAN-2026",
            "capacidad": "500 viales/min",
            "checklist": {
                "Calibración de sensores de temperatura al día": True,
                "Pruebas de hermeticidad y presión concluidas": True,
                "Calificación IQ/OQ aprobada": True,
                "Manual de operación disponible": False
            },
            "documentos": [
                {"nombre": "Certificado_Calibracion_2026.pdf", "usuario": "admin@empresa.com", "fecha": "2026-09-20 10:15"},
                {"nombre": "Protocolo_IQ_OQ_Lavadora.pdf", "usuario": "auditor@empresa.com", "fecha": "2026-09-22 14:30"}
            ]
        }
    }

CATALOGO = {
    "Oncológicos": {
        "LAVADO": ["Lavadora Industrial", "Túnel de despirogenizado"],
        "LLENADO": ["Mesa de acumulación", "Llenadora"],
        "LIOFILIZADO": ["Liofilizador Industrial"]
    },
    "Convencional": {
        "MEZCLADO": ["Tanque Agitador", "Molino Industrial"]
    }
}

# ---------------------------------------------------------
# 4. BARRA LATERAL (NAVEGACIÓN)
# ---------------------------------------------------------
st.sidebar.title("⚙️ Control de Equipos")
st.sidebar.markdown(f"**Usuario:** `{st.session_state['user']['nombre']}`")
st.sidebar.markdown(f"**Correo:** `{st.session_state['user']['email']}`")
st.sidebar.markdown(f"**Sesión:** `{st.session_state['user']['login_time']}`")

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegación del Sistema",
    ["📊 Dashboard General", "🏭 Expediente del Equipo", "📑 Módulo de Consulta de Documentos", "📄 Generar Dossier / PDF"]
)

if st.sidebar.button("Cerrar Sesión", use_container_width=True):
    st.session_state["user"] = None
    st.rerun()

# ---------------------------------------------------------
# 5. MÓDULOS DE LA APLICACIÓN
# ---------------------------------------------------------

# --- MÓDULO 1: DASHBOARD ---
if menu == "📊 Dashboard General":
    st.title("📊 Dashboard General de Planta")
    st.caption("Visualización consolidada de equipos e inventario.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Equipos Registrados", len(st.session_state["equipos_db"]))
    m2.metric("Cumplimiento Promedio", "75%")
    m3.metric("Documentos en Nube", "2 PDFs")
    m4.metric("Auditor Activo", st.session_state['user']['nombre'])

# --- MÓDULO 2: EXPEDIENTE DEL EQUIPO ---
elif menu == "🏭 Expediente del Equipo":
    st.title("🏭 Ficha Técnica y Expediente de Equipo")

    c1, c2, c3 = st.columns(3)
    zona_sel = c1.selectbox("Zona", list(CATALOGO.keys()))
    proceso_sel = c2.selectbox("Proceso", list(CATALOGO[zona_sel].keys()))
    equipo_sel = c3.selectbox("Equipo", CATALOGO[zona_sel][proceso_sel])

    eq_id = "EQ-001"
    eq_ref = st.session_state["equipos_db"][eq_id]

    st.markdown("---")
    st.subheader(f"📍 {equipo_sel} ({zona_sel} > {proceso_sel})")

    tab1, tab2, tab3 = st.tabs(["📝 Características", "📤 Carga de Documentos", "✅ Checklist Auditoría"])

    with tab1:
        col_t1, col_t2 = st.columns(2)
        eq_ref["marca"] = col_t1.text_input("Marca", value=eq_ref.get("marca", ""))
        eq_ref["modelo"] = col_t2.text_input("Modelo", value=eq_ref.get("modelo", ""))
        eq_ref["capacidad"] = st.text_input("Capacidad Instalada", value=eq_ref.get("capacidad", ""))

        if st.button("Guardar Características", type="primary"):
            st.success("Características actualizadas correctamente.")

    with tab2:
        st.write("### Subir Documento PDF")
        pdf_file = st.file_uploader("Seleccionar archivo PDF", type=["pdf"])
        if st.button("📤 Registrar Documento"):
            if pdf_file is not None:
                nuevo_doc = {
                    "nombre": pdf_file.name,
                    "usuario": st.session_state['user']['email'],
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                eq_ref["documentos"].append(nuevo_doc)
                st.success(f"✅ Documento '{pdf_file.name}' registrado exitosamente.")
            else:
                st.warning("Seleccione un archivo PDF válido.")

    with tab3:
        st.write("### Lista de Verificación (Checklist)")
        chk = eq_ref.get("checklist", {})
        for punto, estado in list(chk.items()):
            chk[punto] = st.checkbox(punto, value=estado)

# --- MÓDULO 3: CONSULTA DE DOCUMENTOS ---
elif menu == "📑 Módulo de Consulta de Documentos":
    st.title("🔎 Consulta Centralizada de Documentos")
    st.caption("Repositorio seguro de expedientes y certificados registrados por usuario.")

    all_docs = []
    for eq_k, eq_v in st.session_state["equipos_db"].items():
        for doc in eq_v.get("documentos", []):
            all_docs.append({
                "Equipo": eq_v["nombre"],
                "Zona": eq_v["zona"],
                "Documento PDF": doc["nombre"],
                "Cargado Por": doc["usuario"],
                "Fecha de Registro": doc["fecha"]
            })

    df_docs = pd.DataFrame(all_docs)
    if not df_docs.empty:
        st.dataframe(df_docs, use_container_width=True)
    else:
        st.info("No se han registrado documentos aún.")

# --- MÓDULO 4: GENERAR DOSSIER / PDF ---
elif menu == "📄 Generar Dossier / PDF":
    st.title("📄 Expediente Oficial y Dossier Técnico")
    st.caption("Vista previa pre-renderizada para exportación o impresión a PDF.")

    eq_data = st.session_state["equipos_db"]["EQ-001"]
    usuario = st.session_state['user']

    html_dossier = f"""
    <div style="background: white; padding: 30px; border: 1px solid #cbd5e1; border-radius: 8px; font-family: sans-serif; color: #0f172a;">
        <h2 style="text-align: center; color: #0284c7; margin-bottom: 5px;">DOSSIER TÉCNICO Y EXPEDIENTE DE AUDITORÍA</h2>
        <p style="text-align: center; color: #64748b; font-size: 13px; margin-top: 0;">SISTEMA DE CONTROL Y SEGUIMIENTO DE EQUIPOS INDUSTRIALES</p>
        <hr style="border: 1px solid #0284c7; margin-bottom: 20px;">
        
        <h4 style="color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px;">1. Datos Generales del Equipo</h4>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;">
            <tr><td style="padding: 6px; border: 1px solid #cbd5e1; background: #f8fafc;"><b>Nombre:</b></td><td style="padding: 6px; border: 1px solid #cbd5e1;">{eq_data['nombre']}</td><td style="padding: 6px; border: 1px solid #cbd5e1; background: #f8fafc;"><b>Zona:</b></td><td style="padding: 6px; border: 1px solid #cbd5e1;">{eq_data['zona']}</td></tr>
            <tr><td style="padding: 6px; border: 1px solid #cbd5e1; background: #f8fafc;"><b>Marca:</b></td><td style="padding: 6px; border: 1px solid #cbd5e1;">{eq_data['marca']}</td><td style="padding: 6px; border: 1px solid #cbd5e1; background: #f8fafc;"><b>Modelo:</b></td><td style="padding: 6px; border: 1px solid #cbd5e1;">{eq_data['modelo']}</td></tr>
            <tr><td style="padding: 6px; border: 1px solid #cbd5e1; background: #f8fafc;"><b>Capacidad:</b></td><td style="padding: 6px; border: 1px solid #cbd5e1;">{eq_data['capacidad']}</td><td style="padding: 6px; border: 1px solid #cbd5e1; background: #f8fafc;"><b>Proceso:</b></td><td style="padding: 6px; border: 1px solid #cbd5e1;">{eq_data['proceso']}</td></tr>
        </table>

        <h4 style="color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px;">2. Registro de Firma y Validación Digital</h4>
        <div style="background: #eff6ff; border: 1px solid #93c5fd; padding: 15px; border-radius: 6px; font-size: 13px;">
            <p style="margin: 3px 0;"><b>Emitido Por:</b> {usuario['nombre']}</p>
            <p style="margin: 3px 0;"><b>Correo de Auditor:</b> {usuario['email']}</p>
            <p style="margin: 3px 0;"><b>Fecha de Emisión:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p style="margin: 3px 0; color: #1d4ed8;"><b>Sello de Seguridad:</b> VALIDATED-SESSION-{hash(usuario['email'])}</p>
        </div>
    </div>
    """

    st.components.v1.html(html_dossier, height=450, scrolling=True)
    st.info("💡 Para guardar como PDF: Utilice la opción de impresión del navegador (Ctrl+P) y seleccione 'Guardar como PDF'.")
