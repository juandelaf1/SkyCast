import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import httpx
from datetime import datetime

st.set_page_config(
    page_title="SkyCast",
    page_icon=":umbrella:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_BASE = "http://localhost:8000"
TOKEN_FILE = Path.home() / ".skycast_token.json"


def _load_saved_token():
    try:
        if TOKEN_FILE.exists():
            data = json.loads(TOKEN_FILE.read_text())
            if data.get("email") and data.get("token"):
                return data["email"], data["token"], data.get("user_id")
    except Exception:
        pass
    return None, None, None


def _save_token(email, token, user_id=None, remember=False):
    if remember:
        try:
            TOKEN_FILE.write_text(json.dumps({"email": email, "token": token, "user_id": user_id}))
        except Exception:
            pass


def _clear_saved_token():
    try:
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
    except Exception:
        pass


def api_get(path, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = httpx.get(f"{API_BASE}{path}", headers=headers, timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None


def do_login(email, password, remember=False):
    try:
        r = httpx.post(f"{API_BASE}/api/v1/auth/login", data={"username": email, "password": password}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            st.session_state["token"] = data["access_token"]
            st.session_state["email"] = email
            st.session_state["user_id"] = data.get("user_id")
            _save_token(email, data["access_token"], data.get("user_id"), remember)
            return True, "OK"
        return False, r.json().get("detail", "Credenciales invalidas")
    except Exception as e:
        return False, str(e)


def do_register(email, password):
    try:
        r = httpx.post(f"{API_BASE}/api/v1/auth/register", json={"email": email, "password": password}, timeout=5)
        if r.status_code == 200:
            return True, "Cuenta creada. Ahora inicia sesion."
        return False, r.json().get("detail", "Error al registrar")
    except Exception as e:
        return False, str(e)


def logout():
    _clear_saved_token()
    for key in ["token", "email", "user_id"]:
        st.session_state.pop(key, None)
    st.rerun()


saved_email, saved_token, saved_uid = _load_saved_token()
if saved_token and "token" not in st.session_state:
    resp = api_get("/api/v1/auth/me", token=saved_token)
    if resp and resp.get("email"):
        st.session_state["token"] = saved_token
        st.session_state["email"] = saved_email
        st.session_state["user_id"] = saved_uid

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
    st.title("SkyCast - Enterprise Climate Intelligence Platform")
    st.caption(f"Ultima actualizacion: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
with auth_col:
    if "token" in st.session_state:
        st.caption(f"{st.session_state.get('email', 'Usuario')}")
        if st.button("Cerrar sesion", key="btn_logout_top"):
            logout()
    else:
        st.caption("No autenticado")

menu = ["Resumen Ejecutivo", "Analisis Cientifico", "Auditoria de Datos", "Mapa de Estaciones", "Configuracion"]
if "menu_selection" not in st.session_state:
    st.session_state["menu_selection"] = "Resumen Ejecutivo"

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("Resumen", key="btn_resumen", use_container_width=True, type="primary" if st.session_state["menu_selection"] == "Resumen Ejecutivo" else "secondary"):
        st.session_state["menu_selection"] = "Resumen Ejecutivo"
with col2:
    if st.button("Cientifico", key="btn_cientifico", use_container_width=True):
        st.session_state["menu_selection"] = "Analisis Cientifico"
with col3:
    if st.button("Auditoria", key="btn_auditoria", use_container_width=True):
        st.session_state["menu_selection"] = "Auditoria de Datos"
with col4:
    if st.button("Mapa", key="btn_mapa", use_container_width=True):
        st.session_state["menu_selection"] = "Mapa de Estaciones"
with col5:
    if st.button("Config", key="btn_config", use_container_width=True):
        st.session_state["menu_selection"] = "Configuracion"

st.divider()

page = st.session_state["menu_selection"]
if page == "Resumen Ejecutivo":
    if "token" not in st.session_state:
        st.info("Inicia sesion o registrate para ver datos reales del clima")
        tab_login, tab_register = st.tabs(["Iniciar Sesion", "Registrarse"])
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="tu@email.com")
                password = st.text_input("Contrasena", type="password")
                remember = st.checkbox("Recordarme", value=True, help="Guarda la sesion para no tener que volver a iniciar sesion")
                if st.form_submit_button("Iniciar Sesion", use_container_width=True):
                    ok, msg = do_login(email, password, remember)
                    if ok:
                        st.success("Sesion iniciada")
                        st.rerun()
                    else:
                        st.error(msg)
        with tab_register:
            with st.form("register_form"):
                email_r = st.text_input("Email", placeholder="tu@email.com", key="reg_email")
                password_r = st.text_input("Contrasena", type="password", key="reg_pass",
                    help="Minimo 8 caracteres, 1 mayuscula, 1 numero")
                if st.form_submit_button("Crear Cuenta", use_container_width=True):
                    ok, msg = do_register(email_r, password_r)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
    else:
        from app.dashboard.views import resumen_ejecutivo
        resumen_ejecutivo.render()
elif page == "Analisis Cientifico":
    from app.dashboard.views import analisis_cientifico
    analisis_cientifico.render()
elif page == "Auditoria de Datos":
    from app.dashboard.views import auditoria_datos
    auditoria_datos.render()
elif page == "Mapa de Estaciones":
    from app.dashboard.views import mapa_estaciones
    mapa_estaciones.render()
elif page == "Configuracion":
    from app.dashboard.views import configuracion
    configuracion.render()
