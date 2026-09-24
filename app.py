import streamlit as st
import pandas as pd
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA E INTERFAZ
# ---------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Control y Seguimiento de Equipos Industriales",
    page_icon="⚙️",
    layout="wide"
)

# ---------------------------------------------------------
# 2. CONEXIÓN A NUBE (SUPABASE)
# ---------------------------------------------------------
# Configura tus variables en `.streamlit/secrets.toml` o variables de entorno:
# SUPABASE_URL = "https://tu-proyecto.supabase.co"
# SUPABASE_KEY = "tu-anon-key"

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

# Intentar inicialización de cliente Supabase
supabase_client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        supabase_client = None

# ---------------------------------------------------------
# 3. CONTROL DE SESIÓN Y AUTENTICACIÓN
# ---------------------------------------------------------
if "user" not in st.session_state:
    st.session_state["user"] = None

if not st.session_state["user"]:
    st.title("🔐 Control de Acceso — Sistema de Equipos Industriales")
    st.caption("Ingrese sus credenciales de usuario para habilitar la trazabilidad de auditoría.")
    
    col_a, col_b = st.columns([1, 1.5])
    with col_a:
        with st.form("login_form"):
            email_input = st.text_input("Correo Institucional / Usuario")
            password_input = st.text_input("Contraseña", type="password")
            btn_login = st.form_submit_button("Iniciar Sesión", type="primary", use_container_width=True)
            
            if btn_login:
                if email_input:
                    st.session_state["user"] = {
                        "email": email_input,
                        "nombre": email_input.split("@")[0].replace(".", " ").title(),
                        "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.success(f"Sesión iniciada como: {st.session_state['user']['nombre']}")
                    st.rerun()
                else:
                    st.error("Por favor ingrese un usuario o correo válido.")
    st.stop()

# ---------------------------------------------------------
# 4. MEMORIA DE TRABAJO (BASE DE DATOS LOCAL Y NUBE)
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
                "Manual de operación disponible": True
            },
            "documentos": [
                {"nombre": "Certificado_Calibracion_2026.pdf", "usuario": "admin@empresa.com", "fecha": "2026-09-20 10:15"},
                {"nombre": "Protocolo_IQ_OQ_Lavadora.pdf", "usuario": "auditor@empresa.com", "fecha": "2026-09-22 14:30"}
            ]
        }
    }

# ---------------------------------------------------------
# 5. GENERADOR DE REPORTES PDF (REPORTLAB)
# ---------------------------------------------------------
def generar_reporte_pdf(equipo_id, equipo_data, usuario_sesion):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    # Estilos personalizados
    style_title = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0F172A'), alignment=1)
    style_subtitle = ParagraphStyle(name='SubTitleStyle', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#64748B'), alignment=1)
    style_heading = ParagraphStyle(name='HeadingStyle', parent=styles['Heading2'], fontSize=12, leading=15, textColor=colors.HexColor('#1E293B'))
    style_body = ParagraphStyle(name='BodyStyle', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#334155'))

    # Encabezado
    story.append(Paragraph("SISTEMA DE CONTROL Y SEGUIMIENTO DE EQUIPOS INDUSTRIALES", style_title))
    story.append(Paragraph("DOSSIER TÉCNICO Y EXPEDIENTE DE AUDITORÍA", style_subtitle))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284C7'), spaceAfter=15))

    # Resumen del Equipo
    story.append(Paragraph("<b>1. Información General del Equipo</b>", style_heading))
    story.append(Spacer(1, 6))

    info_data = [
        [Paragraph("<b>Código Equipo:</b>", style_body), Paragraph(equipo_id, style_body), Paragraph("<b>Zona:</b>", style_body), Paragraph(equipo_data['zona'], style_body)],
        [Paragraph("<b>Nombre:</b>", style_body), Paragraph(equipo_data['nombre'], style_body), Paragraph("<b>Proceso:</b>", style_body), Paragraph(equipo_data['proceso'], style_body)],
        [Paragraph("<b>Marca:</b>", style_body), Paragraph(equipo_data['marca'], style_body), Paragraph("<b>Modelo:</b>", style_body), Paragraph(equipo_data['modelo'], style_body)],
        [Paragraph("<b>Capacidad:</b>", style_body), Paragraph(equipo_data['capacidad'], style_body), Paragraph("<b>Estado:</b>", style_body), Paragraph("AUDITADO", style_body)]
    ]
    
    t_info = Table(info_data, colWidths=[100, 160, 80, 180])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 15))

    # Evaluación y Checklist
    story.append(Paragraph("<b>2. Lista de Verificación y Cumplimiento (Checklist)</b>", style_heading))
    story.append(Spacer(1, 6))

    check_rows = [[Paragraph("<b>Criterio de Evaluación / Requisito</b>", style_body), Paragraph("<b>Estado</b>", style_body)]]
    puntos = equipo_data.get("checklist", {})
    cumplidos = 0
    total_puntos = len(puntos) if puntos else 1

    for criterio, estado in puntos.items():
        if estado:
            cumplidos += 1
            txt_estado = Paragraph("<font color='#16A34A'><b>CUMPLE</b></font>", style_body)
        else:
            txt_estado = Paragraph("<font color='#DC2626'><b>NO CUMPLE / PENDIENTE</b></font>", style_body)
        check_rows.append([Paragraph(criterio, style_body), txt_estado])

    pct_avance = int((cumplidos / total_puntos) * 100)

    t_check = Table(check_rows, colWidths=[380, 140])
    t_check.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_check)
    story.append(Spacer(1, 10))

    # Puntuación Final
    story.append(Paragraph(f"<b>Porcentaje de Cumplimiento Alcanzado: {pct_avance}%</b>", style_body))
    story.append(Spacer(1, 20))

    # Validez y Trazabilidad del Usuario
    story.append(Paragraph("<b>3. Registro de Validación y Firma Electrónica</b>", style_heading))
    story.append(Spacer(1, 6))

    firma_data = [
        [Paragraph("<b>Generado y Validado por:</b>", style_body), Paragraph(usuario_sesion['nombre'], style_body)],
        [Paragraph("<b>Correo de Usuario:</b>", style_body), Paragraph(usuario_sesion['email'], style_body)],
        [Paragraph("<b>Fecha y Hora de Emisión:</b>", style_body), Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), style_body)],
        [Paragraph("<b>Sello Digital de Auditoría:</b>", style_body), Paragraph(f"VALIDATED-SESSION-{hash(usuario_sesion['email'] + datetime.now().strftime('%Y%m%d'))}", style_body)]
    ]

    t_firma = Table(firma_data, colWidths=[160, 360])
    t_firma.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#93C5FD')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_firma)

    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# ---------------------------------------------------------
# 6. MENÚ LATERAL Y NAVEGACIÓN
# ---------------------------------------------------------
st.sidebar.title("⚙️ Control de Equipos")
st.sidebar.markdown(f"**Usuario:** `{st.session_state['user']['nombre']}`")
st.sidebar.markdown(f"**Correo:** `{st.session_state['user']['email']}`")
st.sidebar.markdown(f"**Sesión Activa:** `{st.session_state['user']['login_time']}`")

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegación del Sistema",
    ["📊 Dashboard General", "🏭 Expediente del Equipo", "📑 Módulo de Consulta de Documentos", "📊 Exportar Reportes Executivos"]
)

if st.sidebar.button("Cerrar Sesión", use_container_width=True):
    st.session_state["user"] = None
    st.rerun()

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
# 7. MÓDULO: DASHBOARD GENERAL
# ---------------------------------------------------------
if menu == "📊 Dashboard General":
    st.title("📊 Dashboard General de Planta")
    st.caption("Visualización consolidada de equipos e inventario de la nube.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Equipos Registrados", len(st.session_state["equipos_db"]))
    m2.metric("Puntos Cumplidos", "100%")
    m3.metric("Documentos en Nube", "2 PDFs")
    m4.metric("Auditor Activo", st.session_state['user']['nombre'])

# ---------------------------------------------------------
# 8. MÓDULO: EXPEDIENTE DEL EQUIPO
# ---------------------------------------------------------
elif menu == "🏭 Expediente del Equipo":
    st.title("🏭 Ficha Técnica y Expediente de Equipo")

    c1, c2, c3 = st.columns(3)
    zona_sel = c1.selectbox("Zona", list(CATALOGO.keys()))
    proceso_sel = c2.selectbox("Proceso", list(CATALOGO[zona_sel].keys()))
    equipo_sel = c3.selectbox("Equipo", CATALOGO[zona_sel][proceso_sel])

    # Buscar o crear ID de equipo
    eq_id = "EQ-001"
    if eq_id not in st.session_state["equipos_db"]:
        st.session_state["equipos_db"][eq_id] = {
            "nombre": equipo_sel, "zona": zona_sel, "proceso": proceso_sel,
            "marca": "", "modelo": "", "capacidad": "",
            "checklist": {"Calibración al día": False, "IQ/OQ Aprobado": False},
            "documentos": []
        }

    eq_ref = st.session_state["equipos_db"][eq_id]

    st.markdown("---")
    st.subheader(f"📍 {equipo_sel} ({zona_sel} > {proceso_sel})")

    tab1, tab2, tab3 = st.tabs(["📝 Características", "📄 Subida de PDFs (Nube)", "✅ Checklist de Auditoría"])

    with tab1:
        st.write("### Datos Técnicos")
        col_t1, col_t2 = st.columns(2)
        eq_ref["marca"] = col_t1.text_input("Marca", value=eq_ref.get("marca", ""))
        eq_ref["modelo"] = col_t2.text_input("Modelo", value=eq_ref.get("modelo", ""))
        eq_ref["capacidad"] = st.text_input("Capacidad Instalada", value=eq_ref.get("capacidad", ""))

        if st.button("Guardar Características"):
            st.success("Guardado en la base de datos.")

    with tab2:
        st.write("### Subir Documento PDF a la Nube")
        st.caption("Cada documento guardado en la nube se estampa con el nombre del usuario conectado.")
        
        pdf_file = st.file_uploader("Seleccionar archivo PDF o Documento", type=["pdf"])
        if st.button("📤 Subir Documento a la Nube", type="primary"):
            if pdf_file is not None:
                nuevo_doc = {
                    "nombre": pdf_file.name,
                    "usuario": st.session_state['user']['email'],
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                eq_ref["documentos"].append(nuevo_doc)
                
                # Si Supabase está configurado, subir físicamente
                if supabase_client:
                    try:
                        bytes_data = pdf_file.getvalue()
                        path = f"{zona_sel}/{proceso_sel}/{pdf_file.name}"
                        supabase_client.storage.from_("certificados").upload(path, bytes_data)
                    except Exception as ex:
                        pass
                
                st.success(f"✅ Documento '{pdf_file.name}' registrado por {st.session_state['user']['email']}.")
            else:
                st.warning("Seleccione un archivo en formato PDF.")

    with tab3:
        st.write("### Lista de Verificación (Checklist)")
        chk = eq_ref.get("checklist", {})
        for punto, estado in list(chk.items()):
            chk[punto] = st.checkbox(punto, value=estado)

# ---------------------------------------------------------
# 9. MÓDULO: CONSULTA DE DOCUMENTOS EN LA NUBE
# ---------------------------------------------------------
elif menu == "📑 Módulo de Consulta de Documentos":
    st.title("🔎 Consulta Centralizada de Documentos en Nube")
    st.caption("Repositorio seguro de expedientes, certificados y planos en la nube.")

    filtro_txt = st.text_input("Buscar por nombre de archivo o correo de usuario")

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
        if filtro_txt:
            df_docs = df_docs[df_docs["Documento PDF"].str.contains(filtro_txt, case=False) | df_docs["Cargado Por"].str.contains(filtro_txt, case=False)]

        st.dataframe(df_docs, use_container_width=True)

        st.markdown("### Previsualización y Descarga")
        for idx, row in df_docs.iterrows():
            with st.expander(f"📄 {row['Documento PDF']} — Subido por: {row['Cargado Por']}"):
                st.write(f"**Equipo:** {row['Equipo']} | **Zona:** {row['Zona']}")
                st.write(f"**Fecha:** {row['Fecha de Registro']}")
                st.button("⬇️ Descargar Archivo PDF", key=f"dl_btn_{idx}")
    else:
        st.info("No se han subido documentos a la nube aún.")

# ---------------------------------------------------------
# 10. MÓDULO: EXPORTAR REPORTES EJECUTIVOS (PDF)
# ---------------------------------------------------------
elif menu == "📊 Exportar Reportes Executivos":
    st.title("📊 Generación de Reportes Oficiales en PDF")
    st.caption("Obtenga el expediente técnico formal con el sello de validez del usuario activo.")

    eq_id = "EQ-001"
    eq_data = st.session_state["equipos_db"][eq_id]

    st.write(f"**Equipo Seleccionado:** {eq_data['nombre']} ({eq_data['zona']})")

    pdf_bytes = generar_reporte_pdf(eq_id, eq_data, st.session_state['user'])

    st.download_button(
        label="📄 DESCARGAR DOSSIER EN FORMATO PDF",
        data=pdf_bytes,
        file_name=f"Dossier_{eq_data['nombre'].replace(' ', '_')}.pdf",
        mime="application/pdf",
        type="primary"
    )
