import streamlit as st
import httpx
import pandas as pd
import plotly.express as px
from datetime import datetime
from typing import Optional


@st.cache_data(ttl=300)
def fetch_weather_data(lat: Optional[float], lon: Optional[float], city: Optional[str], token: str):
    try:
        params = {}
        if lat and lon:
            params = {"lat": lat, "lon": lon}
        elif city:
            params = {"ciudad": city}
        else:
            params = {"lat": 40.4168, "lon": -3.7038}

        resp = httpx.get("http://localhost:8000/api/v1/clima", params=params, headers={"Authorization": f"Bearer {token}"}, timeout=10.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        return None
    return None


@st.cache_data(ttl=3600)
def fetch_stats(token: str):
    try:
        resp = httpx.get("http://localhost:8000/api/v1/health/stats", headers={"Authorization": f"Bearer {token}"}, timeout=10.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        return None
    return None


def get_alert_color(nivel: Optional[str]) -> str:
    colors = {"rojo": "🔴", "naranja": "🟠", "amarillo": "🟡", "azul": "🔵", "verde": "🟢"}
    return colors.get(nivel, "⚪")


def get_kpi_delta(val, ref):
    if val and ref:
        delta = val - ref
        return round(delta, 1)
    return None


def calculate_sma(series: pd.Series, window: int = 7) -> pd.Series:
    if len(series) < window:
        return series
    return series.rolling(window=window, min_periods=1).mean()


def render():
    st.header("📊 Resumen Ejecutivo")

    token = st.session_state.get("token", "")
    if not token:
        st.info("Inicia sesión para ver los datos. Usa la barra lateral.")
        st.text_input("Token JWT", type="password", key="token_input", on_change=lambda: st.session_state.update(token=st.session_state.token_input))
        return

    data = fetch_weather_data(40.4168, -3.7038, None, token)
    _stats = fetch_stats(token)

    if not data or data.get("status") != "ok":
        st.warning("No se pudieron cargar los datos. Verifica que la API esté corriendo.")
        return

    temp = data.get("temperatura")
    humidity = data.get("humedad")
    wind = data.get("viento")
    rain = data.get("lluvia")
    presion = data.get("presion")
    municipio = data.get("municipio", "Madrid")
    nivel_alerta = data.get("alerta_nivel", "verde")
    alertas = data.get("alertas", [])

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("🌡️ Temperatura", f"{temp}°C" if temp else "N/A", help="Temperatura actual")
    with c2:
        st.metric("💧 Humedad", f"{humidity}%" if humidity else "N/A")
    with c3:
        st.metric("💨 Viento", f"{wind} km/h" if wind else "N/A")
    with c4:
        st.metric("🌧️ Lluvia", f"{rain} mm" if rain else "N/A")
    with c5:
        st.metric("⏱️ Presión", f"{presion} hPa" if presion else "N/A")

    st.divider()

    alert_col1, alert_col2 = st.columns([3, 1])
    with alert_col1:
        st.subheader(f"{get_alert_color(nivel_alerta)} Alerta: {nivel_alerta.upper()}")
        if alertas:
            for a in alertas:
                st.error(f"{a.get('icono', '')} {a.get('mensaje', '')}")
        else:
            st.success("Sin alertas activas")
    with alert_col2:
        st.subheader(f"📍 {municipio}")
        st.caption(f"{data.get('estacion_nombre', 'Estación AEMET')}")
        st.caption(f"Distancia: {data.get('estacion_distancia_km', 'N/A')} km")

    st.divider()

    st.subheader("📈 Tendencia de Temperatura (Datos Simulados)")
    dates = pd.date_range(end=datetime.now(), periods=14, freq="D")
    temp_data = [20 + idx * 0.5 + (hash(str(d)) % 10 - 5) * 0.3 for idx, d in enumerate(dates)]
    hum_data = [50 + idx * 0.2 + (hash(str(d)) % 10 - 5) for idx, d in enumerate(dates)]

    df_trend = pd.DataFrame({"Fecha": dates, "Temperatura": temp_data, "Humedad": hum_data})
    df_trend["SMA_7"] = calculate_sma(df_trend["Temperatura"], 7)

    fig = px.line(
        df_trend,
        x="Fecha",
        y=["Temperatura", "SMA_7"],
        labels={"value": "°C", "variable": "Métrica"},
        color_discrete_sequence=["#38bdf8", "#f59e0b"],
        title="Temperatura y Media Móvil (7 días)",
    )
    fig.update_layout(
        plot_bgcolor="#1e293b",
        paper_bgcolor="#1e293b",
        font_color="#e2e8f0",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    col_left, col_right = st.columns(2)
    with col_left:
        fig_hum = px.area(
            df_trend,
            x="Fecha",
            y="Humedad",
            color_discrete_sequence=["#60a5fa"],
            title="Humedad Relativa (%)",
        )
        fig_hum.update_layout(
            plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0"
        )
        st.plotly_chart(fig_hum, use_container_width=True)
    with col_right:
        temp_cats = ["Normal", "Cálido", "Frío", "Extremo"]
        temp_vals = [45, 25, 20, 10]
        fig_pie = px.pie(
            names=temp_cats,
            values=temp_vals,
            hole=0.4,
            color=temp_cats,
            color_discrete_map={
                "Normal": "#4ade80",
                "Cálido": "#f59e0b",
                "Frío": "#60a5fa",
                "Extremo": "#ef4444",
            },
            title="Distribución de Temperatura",
        )
        fig_pie.update_layout(
            plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0"
        )
        st.plotly_chart(fig_pie, use_container_width=True)