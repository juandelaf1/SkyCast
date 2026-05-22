import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import httpx
from datetime import datetime

st.set_page_config(
    page_title="SkyCast",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_BASE = "http://localhost:8000"


def api_get(path, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = httpx.get(f"{API_BASE}{path}", headers=headers, timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None


def do_login(email, password):
    try:
        r = httpx.post(f"{API_BASE}/api/v1/auth/login", data={"username": email, "password": password}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            st.session_state["token"] = data["access_token"]
            st.session_state["email"] = email
            st.session_state["user_id"] = data.get("user_id")
            return True, "OK"
        return False, r.json().get("detail", "Credenciales inválidas")
    except Exception as e:
        return False, str(e)


def do_register(email, password):
    try:
        r = httpx.post(f"{API_BASE}/api/v1/auth/register", json={"email": email, "password": password}, timeout=5)
        if r.status_code == 200:
            return True, "Cuenta creada. Ahora inicia sesión."
        return False, r.json().get("detail", "Error al registrar")
    except Exception as e:
        return False, str(e)


def logout():
    for key in ["token", "email", "user_id"]:
        st.session_state.pop(key, None)
    st.rerun()


st.markdown("""
<style>
.stApp { background-color: #0f172a; }
h1, h2, h3 { color: #e2e8f0 !important; }
[data-testid="stMetricValue"] { color: #38bdf8 !important; font-size: 2.5rem !important; }
[data-testid="stMetricDelta"] { color: #4ade80 !important; }
.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

title_col, auth_col = st.columns([3, 1])
with title_col:
    st.title("🌦️ SkyCast - Enterprise Climate Intelligence Platform")
    st.caption(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
with auth_col:
    if "token" in st.session_state:
        st.caption(f"👤 {st.session_state.get('email', 'Usuario')}")
        if st.button("🚪 Cerrar sesión", key="btn_logout_top"):
            logout()
    else:
        st.caption("🔓 No autenticado")

menu = ["Resumen Ejecutivo", "Análisis Científico", "Auditoría de Datos", "Mapa de Estaciones", "Configuración"]
if "menu_selection" not in st.session_state:
    st.session_state["menu_selection"] = "Resumen Ejecutivo"

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("📊 Resumen", key="btn_resumen", use_container_width=True, type="primary" if st.session_state["menu_selection"] == "Resumen Ejecutivo" else "secondary"):
        st.session_state["menu_selection"] = "Resumen Ejecutivo"
with col2:
    if st.button("🔬 Científico", key="btn_cientifico", use_container_width=True):
        st.session_state["menu_selection"] = "Análisis Científico"
with col3:
    if st.button("📋 Auditoría", key="btn_auditoria", use_container_width=True):
        st.session_state["menu_selection"] = "Auditoría de Datos"
with col4:
    if st.button("🗺️ Mapa", key="btn_mapa", use_container_width=True):
        st.session_state["menu_selection"] = "Mapa de Estaciones"
with col5:
    if st.button("⚙️ Config", key="btn_config", use_container_width=True):
        st.session_state["menu_selection"] = "Configuración"

st.divider()

# Show login page if not authenticated and user clicks on Resumen
page = st.session_state["menu_selection"]
if page == "Resumen Ejecutivo":
    if "token" not in st.session_state:
        st.info("🔐 Inicia sesión o regístrate para ver datos reales del clima")
        tab_login, tab_register = st.tabs(["Iniciar Sesión", "Registrarse"])
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="tu@email.com")
                password = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Iniciar Sesión", use_container_width=True):
                    ok, msg = do_login(email, password)
                    if ok:
                        st.success("Sesión iniciada")
                        st.rerun()
                    else:
                        st.error(msg)
        with tab_register:
            with st.form("register_form"):
                email_r = st.text_input("Email", placeholder="tu@email.com", key="reg_email")
                password_r = st.text_input("Contraseña", type="password", key="reg_pass",
                    help="Mínimo 8 caracteres, 1 mayúscula, 1 número")
                if st.form_submit_button("Crear Cuenta", use_container_width=True):
                    ok, msg = do_register(email_r, password_r)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
    else:
        from app.dashboard.views import resumen_ejecutivo
        resumen_ejecutivo.render()
elif page == "Análisis Científico":
    from app.dashboard.views import analisis_cientifico
    analisis_cientifico.render()
elif page == "Auditoría de Datos":
    from app.dashboard.views import auditoria_datos
    auditoria_datos.render()
elif page == "Mapa de Estaciones":
    from app.dashboard.views import mapa_estaciones
    mapa_estaciones.render()
elif page == "Configuración":
    from app.dashboard.views import configuracion
    configuracion.render()
