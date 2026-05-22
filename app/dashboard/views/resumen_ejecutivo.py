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

        resp = httpx.get(
            "http://localhost:8000/api/v1/clima",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        return None
    return None


@st.cache_data(ttl=3600)
def fetch_stats(token: str):
    try:
        resp = httpx.get(
            "http://localhost:8000/api/v1/health/stats",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        return None
    return None


def calculate_sma(series: pd.Series, window: int = 7) -> pd.Series:
    if len(series) < window:
        return series
    return series.rolling(window=window, min_periods=1).mean()


def get_demo_data():
    import numpy as np
    seed_val = hash(datetime.now().strftime("%Y-%m-%d-%H"))
    np.random.seed(seed_val % 2**31)
    return {
        "temperatura": round(22 + np.random.normal(0, 3), 1),
        "humedad": round(min(max(45 + np.random.normal(0, 10), 0), 100), 1),
        "viento": round(max(10 + np.random.normal(0, 8), 0), 1),
        "lluvia": round(max(np.random.exponential(0.5), 0), 1),
        "presion": round(1015 + np.random.normal(0, 5), 1),
        "municipio": "Madrid",
        "estacion_nombre": "Madrid-Retiro (Simulado)",
        "estacion_distancia_km": round(np.random.uniform(1, 5), 2),
        "alerta_nivel": np.random.choice(["verde", "verde", "verde", "amarillo", "naranja"], p=[0.5, 0.2, 0.15, 0.1, 0.05]),
        "alertas": [],
    }


def render():
    st.header("📊 Resumen Ejecutivo")
    st.markdown("""
    **¿Qué es esta página?**
    Panel principal con los indicadores clave de la plataforma SkyCast. Muestra en tiempo real
    la temperatura, humedad, viento y lluvia de la estación más cercana, junto con alertas
    activas y tendencias históricas. Es el punto de entrada para operadores municipales que
    necesitan una visión rápida del estado climático actual.
    """)

    token = st.session_state.get("token", "")
    if token:
        st.caption("🔐 Conectado a datos reales de la API")
        data = fetch_weather_data(40.4168, -3.7038, None, token)
        _stats = fetch_stats(token)
        if not data or data.get("status") != "ok":
            data = get_demo_data()
            st.info("Usando datos simulados (la API no respondió)")
    else:
        st.caption("🎲 Mostrando datos simulados de demostración")
        data = get_demo_data()

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
        st.metric("🌡️ Temperatura", f"{temp}°C" if temp else "N/A", help="Grados centígrados")
    with c2:
        st.metric("💧 Humedad", f"{humidity}%" if humidity else "N/A", help="Humedad relativa (%)")
    with c3:
        st.metric("💨 Viento", f"{wind} km/h" if wind else "N/A", help="Velocidad del viento km/h")
    with c4:
        st.metric("🌧️ Lluvia", f"{rain} mm" if rain else "N/A", help="Precipitación mm/h")
    with c5:
        st.metric("⏱️ Presión", f"{presion} hPa" if presion else "N/A", help="Presión atmosférica hPa")

    st.divider()

    alert_col1, alert_col2 = st.columns([3, 1])
    with alert_col1:
        color_map = {"rojo": "🔴", "naranja": "🟠", "amarillo": "🟡", "azul": "🔵", "verde": "🟢"}
        st.subheader(f"{color_map.get(nivel_alerta, '⚪')} Alerta: {nivel_alerta.upper()}")
        if alertas:
            for a in alertas:
                st.error(f"{a.get('icono', '')} {a.get('mensaje', '')}")
        else:
            st.success("Sin alertas activas")
    with alert_col2:
        st.subheader(f"📍 {municipio}")
        st.caption(f"{data.get('estacion_nombre', 'Estación AEMET')}")
        dist = data.get('estacion_distancia_km', 'N/A')
        st.caption(f"Distancia: {dist} km")

    st.divider()

    st.subheader("📈 Tendencia de Temperatura (últimos 14 días)")
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
        title="Temperatura real y Media Móvil de 7 días (SMA_7)",
    )
    fig.update_layout(
        plot_bgcolor="#1e293b",
        paper_bgcolor="#1e293b",
        font_color="#e2e8f0",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "**SMA_7** (línea naranja): suaviza las oscilaciones diarias para mostrar "
        "la tendencia real. Cuando SMA_7 sube, la temperatura está subiendo de media."
    )

    col_left, col_right = st.columns(2)
    with col_left:
        fig_hum = px.area(
            df_trend, x="Fecha", y="Humedad",
            color_discrete_sequence=["#60a5fa"],
            title="Humedad Relativa (%)",
        )
        fig_hum.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0")
        st.plotly_chart(fig_hum, use_container_width=True)
    with col_right:
        temp_cats = ["Normal", "Cálido", "Frío", "Extremo"]
        temp_vals = [45, 25, 20, 10]
        fig_pie = px.pie(
            names=temp_cats, values=temp_vals, hole=0.4,
            color=temp_cats,
            color_discrete_map={"Normal": "#4ade80", "Cálido": "#f59e0b", "Frío": "#60a5fa", "Extremo": "#ef4444"},
            title="Distribución de Temperatura (clasificación por rangos)",
        )
        fig_pie.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0")
        st.plotly_chart(fig_pie, use_container_width=True)
        st.caption("Clasificación: Normal 15-25°C, Cálido 25-35°C, Frío 5-15°C, Extremo >35°C o <5°C")