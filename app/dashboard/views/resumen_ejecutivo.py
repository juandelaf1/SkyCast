import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

from app.dashboard.views._api import api_get, is_authenticated


def calculate_sma(series: pd.Series, window: int = 7) -> pd.Series:
    if len(series) < window:
        return series
    return series.rolling(window=window, min_periods=1).mean()


def render():
    st.header("Resumen Ejecutivo")

    auth = is_authenticated()

    if auth:
        st.caption("Conectado a datos reales de la API")
        data = api_get("/api/v1/clima?lat=40.4168&lon=-3.7038")
        stats = api_get("/api/v1/health/stats")
        registros = api_get("/api/v1/registros?page=1&limit=100")
        alertas = api_get("/api/v1/alertas")
    else:
        st.caption("Mostrando datos simulados de demostracion")
        data = None
        stats = None
        registros = None
        alertas = None

    if not data or (isinstance(data, dict) and data.get("status") != "ok"):
        import numpy as np
        seed_val = hash(datetime.now().strftime("%Y-%m-%d-%H"))
        np.random.seed(seed_val % 2**31)
        data = {
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
        if auth:
            st.info("Usando datos simulados (la API no respondio)")

    temp = data.get("temperatura")
    humidity = data.get("humedad")
    wind = data.get("viento")
    rain = data.get("lluvia")
    presion = data.get("presion")
    municipio = data.get("municipio", "Madrid")
    nivel_alerta = data.get("alerta_nivel", "verde")
    alertas_list = data.get("alertas", [])

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Temperatura", f"{temp}C" if temp else "N/A", help="Grados centigrados")
    with c2:
        st.metric("Humedad", f"{humidity}%" if humidity else "N/A", help="Humedad relativa (%)")
    with c3:
        st.metric("Viento", f"{wind} km/h" if wind else "N/A", help="Velocidad del viento km/h")
    with c4:
        st.metric("Lluvia", f"{rain} mm" if rain else "N/A", help="Precipitacion mm/h")
    with c5:
        st.metric("Presion", f"{presion} hPa" if presion else "N/A", help="Presion atmosferica hPa")

    st.divider()

    alert_col1, alert_col2 = st.columns([3, 1])
    with alert_col1:
        color_map = {"rojo": "Rojo", "naranja": "Naranja", "amarillo": "Amarillo", "azul": "Azul", "verde": "Verde"}
        st.subheader(f"Alerta: {nivel_alerta.upper()}")
        if alertas_list:
            for a in alertas_list:
                st.error(f"{a.get('icono', '')} {a.get('mensaje', '')}")
        else:
            st.success("Sin alertas activas")
    with alert_col2:
        st.subheader(f"{municipio}")
        st.caption(f"{data.get('estacion_nombre', 'Estacion AEMET')}")
        dist = data.get('estacion_distancia_km', 'N/A')
        st.caption(f"Distancia: {dist} km")

    st.divider()

    st.subheader("Tendencia (ultimos 14 dias)")

    if registros and isinstance(registros, list):
        df_reg = pd.DataFrame(registros)
        if "fecha" in df_reg.columns and "temperatura" in df_reg.columns:
            df_reg["fecha"] = pd.to_datetime(df_reg["fecha"])
            df_reg = df_reg.sort_values("fecha").tail(14)
            dates = df_reg["fecha"]
            temp_hist = df_reg["temperatura"]
            hum_hist = df_reg.get("humedad", None)
        else:
            dates = pd.date_range(end=datetime.now(), periods=14, freq="D")
            temp_hist = [20 + idx * 0.5 for idx in range(14)]
            hum_hist = [50 + idx * 0.2 for idx in range(14)]
    else:
        dates = pd.date_range(end=datetime.now(), periods=14, freq="D")
        temp_hist = [20 + idx * 0.5 + (hash(str(d)) % 10 - 5) * 0.3 for idx, d in enumerate(dates)]
        hum_hist = [50 + idx * 0.2 + (hash(str(d)) % 10 - 5) for idx, d in enumerate(dates)]

    df_trend = pd.DataFrame({"Fecha": dates, "Temperatura": temp_hist})
    if hum_hist is not None:
        df_trend["Humedad"] = hum_hist
    df_trend["SMA_7"] = calculate_sma(df_trend["Temperatura"], 7)

    y_cols = ["Temperatura", "SMA_7"]
    fig = px.line(
        df_trend,
        x="Fecha",
        y=y_cols,
        labels={"value": "C", "variable": "Metrica"},
        color_discrete_sequence=["#38bdf8", "#f59e0b"],
        title="Temperatura real y Media Movil de 7 dias (SMA_7)",
    )
    fig.update_layout(
        plot_bgcolor="#1e293b",
        paper_bgcolor="#1e293b",
        font_color="#e2e8f0",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "**SMA_7** (linea naranja): suaviza las oscilaciones diarias para mostrar "
        "la tendencia real. Cuando SMA_7 sube, la temperatura esta subiendo de media."
    )

    col_left, col_right = st.columns(2)
    with col_left:
        if "Humedad" in df_trend.columns:
            fig_hum = px.area(
                df_trend, x="Fecha", y="Humedad",
                color_discrete_sequence=["#60a5fa"],
                title="Humedad Relativa (%)",
            )
            fig_hum.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0")
            st.plotly_chart(fig_hum, use_container_width=True)
    with col_right:
        temp_cats = ["Normal", "Calido", "Frio", "Extremo"]
        temp_vals = [45, 25, 20, 10]
        fig_pie = px.pie(
            names=temp_cats, values=temp_vals, hole=0.4,
            color=temp_cats,
            color_discrete_map={"Normal": "#4ade80", "Calido": "#f59e0b", "Frio": "#60a5fa", "Extremo": "#ef4444"},
            title="Distribucion de Temperatura (clasificacion por rangos)",
        )
        fig_pie.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0")
        st.plotly_chart(fig_pie, use_container_width=True)
        st.caption("Clasificacion: Normal 15-25C, Calido 25-35C, Frio 5-15C, Extremo >35C o <5C")
