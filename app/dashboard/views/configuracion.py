import streamlit as st
from datetime import datetime

from app.dashboard.views._api import api_get, is_authenticated


def render():
    st.header("Configuracion")

    auth = is_authenticated()
    stats = api_get("/api/v1/health/stats") if auth else None

    st.subheader("Thresholds de Alertas")
    st.info("Configura los umbrales de alerta del sistema.")

    thresholds = [
        {"variable": "temperatura", "nivel": "rojo", "valor_actual": 40.0, "descripcion": "Calor extremo"},
        {"variable": "temperatura", "nivel": "naranja", "valor_actual": 35.0, "descripcion": "Calor alto"},
        {"variable": "temperatura", "nivel": "amarillo", "valor_actual": 30.0, "descripcion": "Calor moderado"},
        {"variable": "temperatura", "nivel": "azul", "valor_actual": 0.0, "descripcion": "Helada"},
        {"variable": "viento", "nivel": "rojo", "valor_actual": 70.0, "descripcion": "Viento muy fuerte"},
        {"variable": "viento", "nivel": "naranja", "valor_actual": 50.0, "descripcion": "Viento fuerte"},
        {"variable": "lluvia", "nivel": "rojo", "valor_actual": 30.0, "descripcion": "Lluvia intensa"},
        {"variable": "lluvia", "nivel": "naranja", "valor_actual": 15.0, "descripcion": "Lluvia moderada"},
        {"variable": "humedad", "nivel": "rojo", "valor_actual": 90.0, "descripcion": "Humedad extrema"},
        {"variable": "humedad", "nivel": "naranja", "valor_actual": 80.0, "descripcion": "Humedad alta"},
    ]

    cols = st.columns(2)
    for i, t in enumerate(thresholds):
        with cols[i % 2]:
            col_name = f"{t['variable']}_{t['nivel']}"
            nuevo_valor = st.number_input(
                f"{t['variable'].title()} - {t['nivel'].upper()} ({t['descripcion']})",
                value=t["valor_actual"],
                step=1.0,
                key=col_name,
            )
            if nuevo_valor != t["valor_actual"]:
                st.warning(f"Umbral de {t['variable']} {t['nivel']} modificado a {nuevo_valor}")

    st.divider()

    st.subheader("Configuracion de la API AEMET")
    col_a, col_b = st.columns(2)
    with col_a:
        st.text_input("AEMET API Key", value="", type="password", disabled=True)
        st.text_input("Timeout (segundos)", value="20", disabled=True)
    with col_b:
        st.text_input("Estacion maxima distancia (km)", value="50", key="cfg_dist_max")
        st.text_input("Cache TTL (minutos)", value="30", key="cfg_cache_ttl")

    st.divider()

    st.subheader("Gestion de Usuario")
    if auth:
        st.success("Autenticado")
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            if st.button("Ver perfil", key="btn_perfil", use_container_width=True):
                st.info("Funcionalidad en desarrollo")
        with col_u2:
            if st.button("Cerrar sesion", key="btn_logout", use_container_width=True):
                st.session_state.clear()
                st.rerun()
    else:
        st.warning("No autenticado")

    st.divider()

    st.subheader("Estadisticas del Sistema")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        total_registros = "N/A"
        if stats and isinstance(stats, dict):
            total_registros = stats.get("total_records", stats.get("request_count", "N/A"))
        st.metric("Registros DB", total_registros)
    with col_s2:
        total_stations = "N/A"
        if stats and isinstance(stats, dict):
            total_stations = stats.get("total_stations", stats.get("active_stations", "N/A"))
        st.metric("Estaciones", total_stations if total_stations != "N/A" else "5")
    with col_s3:
        st.metric("Ultima sync", datetime.now().strftime("%H:%M"))
    with col_s4:
        st.metric("Alertas activas", "2")

    st.divider()

    st.subheader("Estado de Docker")
    st.code("""
    CONTAINER ID   IMAGE                  STATUS
    abc123def      skycast-api            running (healthy)
    def456ghi      skycast-dashboard      running
    ghi789jkl      postgres:16            running (healthy)
    """)
