import streamlit as st
import sqlite3
from datetime import date
import pandas as pd

# ============================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================

st.set_page_config(
    page_title="Control de Equipos",
    page_icon="⚙️",
    layout="wide"
)

DB = "equipos.db"

# ============================================================
# CATÁLOGOS Y CONSTANTES
# ============================================================

CATALOGO = {
    "Oncológicos": {
        "LAVADO": ["Lavadora", "Túnel de despirogenizado"],
        "LLENADO": ["Mesa de acumulación", "Llenadora", "Sistema de carga y descarga"],
        "LIOFILIZADO": ["Liofilizador", "CIP externo"],
        "ENGARGOLADO": ["Engargoladora", "Mesa de acumulación"],
        "LAVADO DE EXTERIORES": ["Lavadora de exteriores", "Mesa de acumulación"],
        "INSPECCIÓN": ["Revisadora óptica", "Revisadora de hermeticidad"],
        "ACONDICIONAMIENTO": ["Etiquetadora", "Blíster", "Encartonadora"],
        "AISLADORES": ["Llenado", "Liofilizado", "Engargolado", "Lavado de exteriores"]
    },
    "Convencional": {
        # Espacio para catálogo de Convencional
    }
}

REQUISITOS = {
    "Características": [
        "Marca", "Modelo", "Capacidad", "Servicios", "Dimensiones"
    ],
    "Certificados": [
        "Certificado de materiales", "Certificado de calibración", "Certificados del constructor"
    ],
    "Documentación": [
        "IQ", "OQ", "Manual de instalación", "Manual de operación", "Manual de pantallas", "Manual de mantenimiento"
    ],
    "Ubicación": [
        "Plano / ubicación del equipo"
    ]
}

# ============================================================
# BASE DE DATOS
# ============================================================

def conectar():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def inicializar_db():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS equipos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zona TEXT,
            proceso TEXT,
            equipo TEXT,
            marca TEXT,
            modelo TEXT,
            capacidad TEXT,
            servicios TEXT,
            dimensiones TEXT,
            ubicacion TEXT,
            creado TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS evaluaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipo_id INTEGER,
            categoria TEXT,
            requisito TEXT,
            estado TEXT,
            UNIQUE(equipo_id, categoria, requisito)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS gantt (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipo_id INTEGER,
            actividad TEXT,
            inicio TEXT,
            fin TEXT,
            responsable TEXT,
            estado TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS firmas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipo_id INTEGER,
            firmante TEXT,
            fecha TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE
        )
    """)

    # Cargar usuarios por defecto si no existen
    usuarios_default = [
        "Alberto Giovanni Bañales Nuño",
        "Ingeniería",
        "Calidad",
        "Producción",
        "Mantenimiento"
    ]
    for user in usuarios_default:
        cur.execute("INSERT OR IGNORE INTO usuarios (nombre) VALUES (?)", (user,))

    conn.commit()
    conn.close()

inicializar_db()

def obtener_usuarios():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT nombre FROM usuarios ORDER BY nombre")
    users = [row[0] for row in cur.fetchall()]
    conn.close()
    return users

# ============================================================
# ESTADO DE SESIÓN
# ============================================================

if "login" not in st.session_state:
    st.session_state.login = False

if "zona" not in st.session_state:
    st.session_state.zona = None

if "proceso" not in st.session_state:
    st.session_state.proceso = None

if "equipo" not in st.session_state:
    st.session_state.equipo = None

if "equipo_id" not in st.session_state:
    st.session_state.equipo_id = None

if "pagina" not in st.session_state:
    st.session_state.pagina = "Inicio"

# ============================================================
# LOGIN
# ============================================================

def pantalla_login():
    st.markdown("<h1 style='text-align:center;'>⚙️ CONTROL DE EQUIPOS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Sistema de seguimiento de instalación y cumplimiento</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("INICIAR SESIÓN", use_container_width=True)

            if submit:
                if usuario and password:
                    st.session_state.login = True
                    st.rerun()
                else:
                    st.error("Ingresa usuario y contraseña.")

# ============================================================
# SIDEBAR
# ============================================================

def sidebar():
    st.sidebar.title("CONTROL DE EQUIPOS")
    st.sidebar.divider()
    st.sidebar.write("Usuario activo:")
    st.sidebar.write("**Alberto Giovanni Bañales Nuño**")
    st.sidebar.divider()

    opciones = ["Inicio", "Equipos", "Gantt", "Usuarios"]
    
    # Manejo de indice seguro
    idx = opciones.index(st.session_state.pagina) if st.session_state.pagina in opciones else 0
    pagina = st.sidebar.radio("Módulos", opciones, index=idx)

    st.session_state.pagina = pagina

    st.sidebar.divider()
    if st.sidebar.button("Cerrar sesión", use_container_width=True):
        st.session_state.login = False
        st.session_state.pagina = "Inicio"
        st.rerun()

# ============================================================
# INICIO / DASHBOARD
# ============================================================

def inicio():
    st.title("Dashboard")
    st.subheader("Seleccione la zona de operación")

    zonas = list(CATALOGO.keys())
    cols = st.columns(len(zonas))

    for i, zona in enumerate(zonas):
        with cols[i]:
            if st.button(zona, use_container_width=True, key=f"zona_{zona}"):
                st.session_state.zona = zona
                st.session_state.proceso = None
                st.session_state.equipo = None
                st.session_state.pagina = "Equipos"
                st.rerun()

    st.divider()
    st.subheader("Resumen General")

    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM equipos")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM firmas")
    firmados = cur.fetchone()[0]

    conn.close()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Equipos registrados", total)
    c2.metric("Equipos firmados", firmados)
    c3.metric("Pendientes de Firma", max(total - firmados, 0))
    c4.metric("Zonas en Catálogo", len(zonas))

# ============================================================
# PANTALLA EQUIPOS (SELECCIÓN)
# ============================================================

def pantalla_equipos():
    st.title("Seguimiento de Equipos")

    zona = st.session_state.zona
    if not zona or zona not in CATALOGO:
        zona = st.selectbox("Zona", list(CATALOGO.keys()))
        st.session_state.zona = zona

    st.info(f"Zona seleccionada: **{zona}**")

    if not CATALOGO[zona]:
        st.warning("El catálogo de esta zona todavía no ha sido cargado.")
        return

    st.subheader("1. Seleccionar proceso / área")
    procesos = list(CATALOGO[zona].keys())

    idx_proceso = procesos.index(st.session_state.proceso) if st.session_state.proceso in procesos else 0
    proceso = st.selectbox("Proceso / Área", procesos, index=idx_proceso)
    st.session_state.proceso = proceso

    st.divider()

    st.subheader(f"2. Equipos de {proceso}")
    equipos = CATALOGO[zona][proceso]

    cols = st.columns(3)
    for i, equipo in enumerate(equipos):
        with cols[i % 3]:
            st.markdown(f"""
                <div style="padding:15px; border:1px solid #d9dee7; border-radius:10px; margin-bottom:10px; background:#fafbfd;">
                    <h4>{equipo}</h4>
                    <p style="margin:0;">Zona: {zona}<br>Área: {proceso}</p>
                </div>
            """, unsafe_allow_html=True)

            if st.button("ABRIR EQUIPO", key=f"abrir_{zona}_{proceso}_{equipo}", use_container_width=True):
                abrir_equipo(zona, proceso, equipo)

# ============================================================
# ABRIR O CREAR EQUIPO EN BD
# ============================================================

def abrir_equipo(zona, proceso, equipo):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id FROM equipos WHERE zona=? AND proceso=? AND equipo=?
    """, (zona, proceso, equipo))

    resultado = cur.fetchone()

    if resultado:
        equipo_id = resultado[0]
    else:
        cur.execute("""
            INSERT INTO equipos (zona, proceso, equipo, creado)
            VALUES (?, ?, ?, ?)
        """, (zona, proceso, equipo, str(date.today())))
        equipo_id = cur.lastrowid

    conn.commit()
    conn.close()

    st.session_state.equipo_id = equipo_id
    st.session_state.equipo = equipo
    st.session_state.pagina = "Detalle"
    st.rerun()

# ============================================================
# DETALLE DEL EQUIPO
# ============================================================

def detalle_equipo():
    equipo_id = st.session_state.equipo_id
    equipo = st.session_state.equipo

    if not equipo_id:
        st.warning("No hay equipo seleccionado.")
        return

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT zona, proceso, equipo, marca, modelo, capacidad, servicios, dimensiones, ubicacion
        FROM equipos WHERE id=?
    """, (equipo_id,))
    datos = cur.fetchone()
    conn.close()

    if not datos:
        st.error("El equipo no existe en la base de datos.")
        return

    zona, proceso, equipo, marca, modelo, capacidad, servicios, dimensiones, ubicacion = datos

    st.title(equipo)
    st.caption(f"{zona} › {proceso} › {equipo}")

    if st.button("← Regresar"):
        st.session_state.pagina = "Equipos"
        st.rerun()

    st.divider()

    tabs = st.tabs([
        "Características", "Certificados", "Documentación",
        "Ubicación", "Evaluación", "Gantt", "Firma"
    ])

    # 1. CARACTERÍSTICAS
    with tabs[0]:
        st.subheader("Características del equipo")
        with st.form(f"form_caracteristicas_{equipo_id}"):
            c1, c2 = st.columns(2)
            with c1:
                marca_nueva = st.text_input("Marca", value=marca or "")
                modelo_nuevo = st.text_input("Modelo", value=modelo or "")
                capacidad_nueva = st.text_input("Capacidad", value=capacidad or "")
            with c2:
                servicios_nuevos = st.text_area("Servicios", value=servicios or "")
                dimensiones_nuevas = st.text_input("Dimensiones", value=dimensiones or "")

            guardar = st.form_submit_button("GUARDAR CARACTERÍSTICAS")
            if guardar:
                conn = conectar()
                cur = conn.cursor()
                cur.execute("""
                    UPDATE equipos
                    SET marca=?, modelo=?, capacidad=?, servicios=?, dimensiones=?
                    WHERE id=?
                """, (marca_nueva, modelo_nuevo, capacidad_nueva, servicios_nuevos, dimensiones_nuevas, equipo_id))
                conn.commit()
                conn.close()
                st.success("Características guardadas correctamente.")

    # 2. CERTIFICADOS
    with tabs[1]:
        st.subheader("Certificados requeridos")
        for requisito in REQUISITOS["Certificados"]:
            st.file_uploader(requisito, key=f"cert_{equipo_id}_{requisito}")

    # 3. DOCUMENTACIÓN
    with tabs[2]:
        st.subheader("Documentación requerida")
        for requisito in REQUISITOS["Documentación"]:
            st.file_uploader(requisito, key=f"doc_{equipo_id}_{requisito}")

    # 4. UBICACIÓN
    with tabs[3]:
        st.subheader("Ubicación del equipo")
        with st.form(f"form_ubicacion_{equipo_id}"):
            ubicacion_nueva = st.text_input("Ubicación", value=ubicacion or "")
            plano_file = st.file_uploader("Cargar plano / imagen", type=["png", "jpg", "jpeg", "pdf"], key=f"plano_{equipo_id}")
            guardar_ubi = st.form_submit_button("GUARDAR UBICACIÓN")

            if guardar_ubi:
                conn = conectar()
                cur = conn.cursor()
                cur.execute("UPDATE equipos SET ubicacion=? WHERE id=?", (ubicacion_nueva, equipo_id))
                conn.commit()
                conn.close()
                st.success("Ubicación actualizada.")

    # 5. EVALUACIÓN
    with tabs[4]:
        evaluacion_equipo(equipo_id)

    # 6. GANTT
    with tabs[5]:
        gantt_equipo(equipo_id)

    # 7. FIRMA
    with tabs[6]:
        firma_equipo(equipo_id)

# ============================================================
# EVALUACIÓN
# ============================================================

def evaluacion_equipo(equipo_id):
    st.subheader("Evaluación de cumplimiento")

    # Cargar datos actuales de evaluación
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT categoria, requisito, estado FROM evaluaciones WHERE equipo_id=?", (equipo_id,))
    evaluaciones_existentes = {(row[0], row[1]): row[2] for row in cur.fetchall()}
    conn.close()

    total = 0
    cumplidos = 0
    nuevas_evaluaciones = {}

    with st.form(f"form_evaluacion_{equipo_id}"):
        for categoria, requisitos in REQUISITOS.items():
            st.markdown(f"#### {categoria}")
            for requisito in requisitos:
                total += 1
                estado_actual = evaluaciones_existentes.get((categoria, requisito), "Pendiente")

                c1, c2 = st.columns([3, 2])
                with c1:
                    st.write(f"• **{requisito}**")
                with c2:
                    opciones = ["Cumple", "No cumple", "Pendiente"]
                    idx = opciones.index(estado_actual) if estado_actual in opciones else 2
                    estado = st.radio(
                        f"Estado {requisito}", opciones, horizontal=True, index=idx,
                        key=f"eval_{equipo_id}_{categoria}_{requisito}", label_visibility="collapsed"
                    )
                    nuevas_evaluaciones[(categoria, requisito)] = estado
                    if estado == "Cumple":
                        cumplidos += 1

        guardar_eval = st.form_submit_button("GUARDAR EVALUACIÓN", type="primary")

    if guardar_eval:
        conn = conectar()
        cur = conn.cursor()
        for (cat, req), est in nuevas_evaluaciones.items():
            cur.execute("""
                INSERT INTO evaluaciones (equipo_id, categoria, requisito, estado)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(equipo_id, categoria, requisito) 
                DO UPDATE SET estado=excluded.estado
            """, (equipo_id, cat, req, est))
        conn.commit()
        conn.close()
        st.success("Evaluaciones guardadas correctamente.")
        st.rerun()

    st.divider()
    porcentaje = int(cumplidos / total * 100) if total > 0 else 0
    st.progress(porcentaje / 100)
    st.write(f"Cumplimiento actual: **{porcentaje}%** ({cumplidos}/{total})")

    if porcentaje == 100:
        st.success("✓ Todos los requisitos cumplen. El equipo puede pasar a firma.")
    else:
        st.warning("La firma permanece bloqueada hasta que todos los requisitos estén en 'Cumple'.")

# ============================================================
# GANTT
# ============================================================

def gantt_equipo(equipo_id):
    st.subheader("Plan de instalación")

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, actividad, inicio, fin, responsable, estado
        FROM gantt WHERE equipo_id=?
    """, (equipo_id,))
    registros = cur.fetchall()
    conn.close()

    if registros:
        df = pd.DataFrame(registros, columns=["ID", "Actividad", "Inicio", "Fin", "Responsable", "Estado"])
        st.dataframe(df[["Actividad", "Inicio", "Fin", "Responsable", "Estado"]], use_container_width=True)
    else:
        st.info("No hay actividades registradas en el plan de este equipo.")

    st.divider()
    st.markdown("#### Agregar nueva actividad")

    usuarios_lista = obtener_usuarios()

    with st.form(f"gantt_form_{equipo_id}"):
        actividad = st.text_input("Actividad")
        c1, c2 = st.columns(2)
        with c1:
            inicio = st.date_input("Inicio", value=date.today())
        with c2:
            fin = st.date_input("Fin", value=date.today())

        responsable = st.selectbox("Responsable", usuarios_lista)
        estado = st.selectbox("Estado", ["Pendiente", "En proceso", "Completado"])

        guardar = st.form_submit_button("AGREGAR AL GANTT")

        if guardar and actividad:
            conn = conectar()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO gantt (equipo_id, actividad, inicio, fin, responsable, estado)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (equipo_id, actividad, str(inicio), str(fin), responsable, estado))
            conn.commit()
            conn.close()
            st.success("Actividad agregada.")
            st.rerun()

# ============================================================
# FIRMA
# ============================================================

def firma_equipo(equipo_id):
    st.subheader("Liberación y firma")

    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM evaluaciones WHERE equipo_id=? AND estado='Cumple'", (equipo_id,))
    cumplidos = cur.fetchone()[0]

    requisitos_totales = sum(len(x) for x in REQUISITOS.values())

    cur.execute("SELECT firmante, fecha FROM firmas WHERE equipo_id=?", (equipo_id,))
    firma = cur.fetchone()
    conn.close()

    completo = (cumplidos == requisitos_totales and requisitos_totales > 0)

    if completo:
        st.success("✓ EQUIPO LIBERADO PARA FIRMA")
        usuarios_lista = obtener_usuarios()
        firmante = st.selectbox("Seleccione firmante", usuarios_lista)

        if st.button("FIRMAR Y LIBERAR EQUIPO", type="primary", use_container_width=True):
            conn = conectar()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO firmas (equipo_id, firmante, fecha) VALUES (?, ?, ?)
            """, (equipo_id, firmante, str(date.today())))
            conn.commit()
            conn.close()
            st.success(f"Equipo firmado por {firmante}")
            st.rerun()
    else:
        faltantes = requisitos_totales - cumplidos
        st.error(f"Firma bloqueada. Faltan {faltantes} requisitos por cumplir.")

    if firma:
        st.divider()
        st.info(f"Firmado por: **{firma[0]}**\n\nFecha: **{firma[1]}**")

# ============================================================
# GANTT GENERAL
# ============================================================

def gantt_general():
    st.title("Gantt general de instalación")

    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT equipos.zona, equipos.proceso, equipos.equipo, gantt.actividad, gantt.inicio, gantt.fin, gantt.responsable, gantt.estado
        FROM gantt
        JOIN equipos ON equipos.id = gantt.equipo_id
        ORDER BY gantt.inicio
    """)
    datos = cur.fetchall()
    conn.close()

    if not datos:
        st.info("No existen actividades registradas.")
        return

    df = pd.DataFrame(datos, columns=["Zona", "Proceso", "Equipo", "Actividad", "Inicio", "Fin", "Responsable", "Estado"])
    st.dataframe(df, use_container_width=True)

# ============================================================
# CATÁLOGO DE USUARIOS
# ============================================================

def usuarios():
    st.title("Catálogo de usuarios y firmantes")

    usuarios_lista = obtener_usuarios()

    st.write("Usuarios actualmente registrados:")
    for u in usuarios_lista:
        st.write(f"✓ {u}")

    st.divider()
    with st.form("form_nuevo_usuario"):
        nuevo = st.text_input("Agregar usuario")
        btn = st.form_submit_button("Agregar")

        if btn and nuevo.strip():
            conn = conectar()
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO usuarios (nombre) VALUES (?)", (nuevo.strip(),))
                conn.commit()
                st.success("Usuario agregado.")
            except sqlite3.IntegrityError:
                st.error("El usuario ya existe.")
            finally:
                conn.close()
                st.rerun()

# ============================================================
# CONTROLADOR DE FLUSO PRINCIPAL
# ============================================================

if not st.session_state.login:
    pantalla_login()
else:
    sidebar()
    if st.session_state.pagina == "Inicio":
        inicio()
    elif st.session_state.pagina == "Equipos":
        pantalla_equipos()
    elif st.session_state.pagina == "Detalle":
        detalle_equipo()
    elif st.session_state.pagina == "Gantt":
        gantt_general()
    elif st.session_state.pagina == "Usuarios":
        usuarios()
