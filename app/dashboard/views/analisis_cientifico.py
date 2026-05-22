import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

from app.dashboard.views._api import api_get, is_authenticated


def calculate_sma(series, window=7):
    if len(series) < window:
        return series
    return series.rolling(window=window, min_periods=1).mean()


def calculate_std_bands(series, window=7, std_factor=2):
    rolling_mean = series.rolling(window=window, min_periods=1).mean()
    rolling_std = series.rolling(window=window, min_periods=1).std()
    upper = rolling_mean + (std_factor * rolling_std)
    lower = rolling_mean - (std_factor * rolling_std)
    return rolling_mean, upper, lower


def render():
    st.header("Analisis Cientifico")

    auth = is_authenticated()
    registros = api_get("/api/v1/registros?page=1&limit=500") if auth else None

    if registros and isinstance(registros, list) and len(registros) > 10:
        df = pd.DataFrame(registros)
        if "fecha" in df.columns:
            df["fecha"] = pd.to_datetime(df["fecha"])
            df = df.sort_values("fecha").set_index("fecha")
            for col in ["temperatura", "humedad", "viento", "lluvia"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df = _generate_demo_data()
    else:
        df = _generate_demo_data()
        if auth:
            st.info("Usando datos simulados (sin datos historicos suficientes en la API)")

    tab1, tab2, tab3, tab4 = st.tabs(["Tendencias", "Correlacion", "Anomalias", "Detalle"])

    with tab1:
        col_t, col_h = st.columns(2)
        with col_t:
            sma_temp = calculate_sma(df["temperatura"], 24) if len(df) >= 24 else calculate_sma(df["temperatura"], max(3, len(df) // 2))
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df["temperatura"], name="Temperatura", line=dict(color="#38bdf8", width=1), opacity=0.5))
            fig.add_trace(go.Scatter(x=df.index, y=sma_temp, name="SMA", line=dict(color="#f59e0b", width=2)))
            fig.update_layout(title="Temperatura (SMA)", plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0", height=400)
            st.plotly_chart(fig, use_container_width=True)
        with col_h:
            if "humedad" in df.columns:
                sma_hum = calculate_sma(df["humedad"], 24) if len(df) >= 24 else calculate_sma(df["humedad"], max(3, len(df) // 2))
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=df.index, y=df["humedad"], name="Humedad", line=dict(color="#60a5fa", width=1), opacity=0.5))
                fig2.add_trace(go.Scatter(x=df.index, y=sma_hum, name="SMA", line=dict(color="#a78bfa", width=2)))
                fig2.update_layout(title="Humedad (SMA)", plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0", height=400)
                st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        daily = df.resample("D").mean() if hasattr(df.index, "freq") or len(df) > 48 else df
        corr_cols = [c for c in ["temperatura", "humedad", "viento", "lluvia"] if c in daily.columns]
        if len(corr_cols) >= 2:
            corr_matrix = daily[corr_cols].corr()
            fig_corr = px.imshow(
                corr_matrix,
                text_auto=True,
                color_continuous_scale="RdBu",
                title="Matriz de Correlacion (Datos Diarios)",
                labels=dict(color="Correlacion"),
            )
            fig_corr.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0", height=450)
            st.plotly_chart(fig_corr, use_container_width=True)

        if "temperatura" in daily.columns and "humedad" in daily.columns:
            fig_scatter = px.scatter(
                daily.reset_index(),
                x="temperatura",
                y="humedad",
                size="viento" if "viento" in daily.columns else None,
                color="lluvia" if "lluvia" in daily.columns else None,
                color_continuous_scale="Viridis",
                title="Correlacion Temperatura-Humedad",
                labels={"temperatura": "Temperatura (C)", "humedad": "Humedad (%)"},
            )
            fig_scatter.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0")
            st.plotly_chart(fig_scatter, use_container_width=True)

    with tab3:
        mean_temp, upper, lower = calculate_std_bands(df["temperatura"], min(24, len(df) // 2), 2)
        fig_anom = go.Figure()
        fig_anom.add_trace(go.Scatter(x=df.index, y=df["temperatura"], name="Temperatura", mode="lines", line=dict(color="#38bdf8", width=1)))
        fig_anom.add_trace(go.Scatter(x=df.index, y=mean_temp, name="Media Movil", line=dict(color="#f59e0b", width=2)))
        fig_anom.add_trace(go.Scatter(x=df.index, y=upper, name="+2 Std", line=dict(color="#ef4444", width=1, dash="dash"), fill=None))
        fig_anom.add_trace(go.Scatter(x=df.index, y=lower, name="-2 Std", line=dict(color="#ef4444", width=1, dash="dash"), fill="tonexty", fillcolor="rgba(239,68,68,0.05)"))
        fig_anom.update_layout(title="Deteccion de Anomalias (2 Desviaciones Estandar)", plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0", height=400)
        st.plotly_chart(fig_anom, use_container_width=True)

        anomalies = df[(df["temperatura"] > upper) | (df["temperatura"] < lower)]
        st.subheader(f"Anomalias Detectadas: {len(anomalies)}")
        if not anomalies.empty:
            st.dataframe(anomalies[["temperatura"]].rename(columns={"temperatura": "Temp (C)"}))

    with tab4:
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(df.describe().round(2), use_container_width=True)
        with col2:
            st.markdown("**Estadisticas de Temperatura**")
            t = df["temperatura"]
            st.write(f"- Media: {t.mean():.1f}C")
            st.write(f"- Mediana: {t.median():.1f}C")
            st.write(f"- Desv. Estandar: {t.std():.2f}")
            st.write(f"- Minimo: {t.min():.1f}C")
            st.write(f"- Maximo: {t.max():.1f}C")
            st.write(f"- Rango intercuartilico: {t.quantile(0.75) - t.quantile(0.25):.1f}C")


def _generate_demo_data():
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq="h")
    n = len(dates)
    np.random.seed(42)
    base_temp = 20 + 10 * np.sin(2 * np.pi * np.arange(n) / 24)
    temp_noise = np.random.normal(0, 2, n)
    df = pd.DataFrame({
        "fecha": dates,
        "temperatura": base_temp + temp_noise,
        "humedad": np.clip(50 + 20 * np.sin(2 * np.pi * np.arange(n) / 24) + np.random.normal(0, 5, n), 0, 100),
        "viento": np.clip(np.abs(np.random.normal(15, 8, n)), 0, 150),
        "lluvia": np.abs(np.random.exponential(1, n)),
    })
    return df.set_index("fecha")
