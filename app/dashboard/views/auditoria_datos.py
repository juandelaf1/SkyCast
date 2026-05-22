import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

from app.dashboard.views._api import api_get, is_authenticated


def render():
    st.header("Auditoria de Datos")

    auth = is_authenticated()

    if auth:
        raw = api_get("/api/v1/registros?page=1&limit=200")
        if raw and isinstance(raw, list) and len(raw) > 0:
            df = pd.DataFrame(raw)
            if "fecha" in df.columns:
                df["fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce")
                df["dia"] = df["fecha_dt"].dt.date
        else:
            df = _generate_seed_data()
            st.info("Usando datos simulados (la API no respondio)")
    else:
        st.caption("Mostrando datos simulados de demostracion")
        df = _generate_seed_data()

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        muni_options = df["municipio"].unique() if "municipio" in df.columns else ["Madrid"]
        selected_muni = st.multiselect("Municipio", muni_options, default=list(muni_options), key="audit_muni")
    with col_f2:
        fuente_options = df["fuente"].unique() if "fuente" in df.columns else ["AEMET"]
        selected_fuente = st.multiselect("Fuente", fuente_options, default=list(fuente_options), key="audit_fuente")
    with col_f3:
        base_date = datetime.now() - timedelta(days=7) if "fecha_dt" not in df.columns or df["fecha_dt"].empty else df["fecha_dt"].min()
        _fecha_range = st.date_input("Rango de fechas", value=(base_date, datetime.now()), key="audit_dates")

    df_filtered = df.copy()
    if "municipio" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["municipio"].isin(selected_muni)]
    if "fuente" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["fuente"].isin(selected_fuente)]

    display_cols = [c for c in ["fecha", "municipio", "estacion", "temperatura", "humedad", "viento", "lluvia", "fuente"] if c in df_filtered.columns]
    st.subheader(f"Registros: {len(df_filtered)}")
    st.dataframe(df_filtered[display_cols], use_container_width=True, hide_index=True)

    if "municipio" in df_filtered.columns and "temperatura" in df_filtered.columns:
        st.subheader("Distribucion de Temperatura por Municipio")
        color_col = "fuente" if "fuente" in df_filtered.columns else None
        fig_box = px.box(
            df_filtered,
            x="municipio",
            y="temperatura",
            color=color_col,
            color_discrete_sequence=["#38bdf8", "#f59e0b"],
            title="Temperatura por Municipio y Fuente",
        )
        fig_box.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0")
        st.plotly_chart(fig_box, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        if "fuente" in df_filtered.columns:
            fuente_counts = df_filtered["fuente"].value_counts()
            fig_pie = px.pie(
                names=fuente_counts.index,
                values=fuente_counts.values,
                title="Registros por Fuente",
                color=fuente_counts.index,
                color_discrete_map={"AEMET": "#38bdf8", "OpenWeather": "#f59e0b", "manual": "#4ade80"},
            )
            fig_pie.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0")
            st.plotly_chart(fig_pie, use_container_width=True)
    with c2:
        if "dia" in df_filtered.columns:
            daily_counts = df_filtered.groupby("dia").size().reset_index(name="registros")
            fig_bar = px.bar(
                daily_counts,
                x="dia",
                y="registros",
                title="Registros por Dia",
                color="registros",
                color_continuous_scale="Blues",
            )
            fig_bar.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0", xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Registros con Advertencias")
    if "temperatura" in df_filtered.columns:
        warnings = df_filtered[df_filtered["temperatura"] > 35]
        if not warnings.empty:
            cols = [c for c in ["fecha", "municipio", "temperatura", "fuente"] if c in warnings.columns]
            st.dataframe(warnings[cols], use_container_width=True, hide_index=True)
        else:
            st.success("Sin advertencias")


def _generate_seed_data():
    base = datetime.now() - timedelta(days=7)
    seed_data = []
    for i in range(50):
        d = base + timedelta(hours=i * 3)
        seed_data.append({
            "id": i + 1,
            "fecha": d.strftime("%Y-%m-%d %H:%M"),
            "municipio": ["Madrid", "Alcala de Henares", "Mostoles", "Getafe", "Fuenlabrada"][i % 5],
            "estacion": ["Madrid-Retiro", "Alcala", "Mostoles", "Getafe", "Fuenlabrada"][i % 5],
            "temperatura": round(15 + (i % 15) + (i % 3) - 2, 1),
            "humedad": round(40 + (i % 20), 1),
            "viento": round(5 + (i % 10), 1),
            "lluvia": round((i % 7) * 0.5, 1),
            "fuente": ["AEMET", "manual", "AEMET"][i % 3],
            "estado": ["ok", "ok", "ok", "warning"][i % 4],
        })
    return pd.DataFrame(seed_data)
