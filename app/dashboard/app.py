import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="SkyCast",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def get_api_base():
    return "http://localhost:8000"


def get_token():
    if "token" not in st.session_state:
        return None
    return st.session_state["token"]


def ensure_auth():
    if not get_token():
        st.session_state["page"] = "login"
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

st.title("🌦️ SkyCast - Enterprise Climate Intelligence Platform")
st.caption(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

menu = ["Resumen Ejecutivo", "Análisis Científico", "Auditoría de Datos", "Mapa de Estaciones", "Configuración"]
if "menu_selection" not in st.session_state:
    st.session_state["menu_selection"] = "Resumen Ejecutivo"

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("📊 Resumen", use_container_width=True, type="primary" if st.session_state["menu_selection"] == "Resumen Ejecutivo" else "secondary"):
        st.session_state["menu_selection"] = "Resumen Ejecutivo"
with col2:
    if st.button("🔬 Científico", use_container_width=True):
        st.session_state["menu_selection"] = "Análisis Científico"
with col3:
    if st.button("📋 Auditoría", use_container_width=True):
        st.session_state["menu_selection"] = "Auditoría de Datos"
with col4:
    if st.button("🗺️ Mapa", use_container_width=True):
        st.session_state["menu_selection"] = "Mapa de Estaciones"
with col5:
    if st.button("⚙️ Config", use_container_width=True):
        st.session_state["menu_selection"] = "Configuración"

st.divider()

page = st.session_state["menu_selection"]
if page == "Resumen Ejecutivo":
    from app.dashboard.pages import resumen_ejecutivo
    resumen_ejecutivo.render()
elif page == "Análisis Científico":
    from app.dashboard.pages import analisis_cientifico
    analisis_cientifico.render()
elif page == "Auditoría de Datos":
    from app.dashboard.pages import auditoria_datos
    auditoria_datos.render()
elif page == "Mapa de Estaciones":
    from app.dashboard.pages import mapa_estaciones
    mapa_estaciones.render()
elif page == "Configuración":
    from app.dashboard.pages import configuracion
    configuracion.render()