import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta


def render():
    st.header("📋 Auditoría de Datos")

    seed_data = []
    base = datetime.now() - timedelta(days=7)
    for i in range(50):
        d = base + timedelta(hours=i * 3)
        seed_data.append({
            "id": i + 1,
            "fecha": d.strftime("%Y-%m-%d %H:%M"),
            "municipio": ["Madrid", "Alcalá de Henares", "Móstoles", "Getafe", "Fuenlabrada"][i % 5],
            "estacion": ["Madrid-Retiro", "Alcalá", "Móstoles", "Getafe", "Fuenlabrada"][i % 5],
            "temperatura": round(15 + (i % 15) + (i % 3) - 2, 1),
            "humedad": round(40 + (i % 20), 1),
            "viento": round(5 + (i % 10), 1),
            "lluvia": round((i % 7) * 0.5, 1),
            "fuente": ["AEMET", "manual", "AEMET"][i % 3],
            "estado": ["ok", "ok", "ok", "warning"][i % 4],
        })

    df = pd.DataFrame(seed_data)
    df["fecha_dt"] = pd.to_datetime(df["fecha"])
    df["dia"] = df["fecha_dt"].dt.date

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        selected_muni = st.multiselect("Municipio", df["municipio"].unique(), default=df["municipio"].unique(), key="audit_muni")
    with col_f2:
        selected_fuente = st.multiselect("Fuente", df["fuente"].unique(), default=df["fuente"].unique(), key="audit_fuente")
    with col_f3:
        _fecha_range = st.date_input("Rango de fechas", value=(base.date(), datetime.now().date()), key="audit_dates")

    df_filtered = df[df["municipio"].isin(selected_muni) & df["fuente"].isin(selected_fuente)]

    st.subheader(f"Registros: {len(df_filtered)}")
    st.dataframe(
        df_filtered[["fecha", "municipio", "estacion", "temperatura", "humedad", "viento", "lluvia", "fuente"]],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("📊 Distribución de Temperatura por Municipio")
    fig_box = px.box(
        df_filtered,
        x="municipio",
        y="temperatura",
        color="fuente",
        color_discrete_sequence=["#38bdf8", "#f59e0b"],
        title="Temperatura por Municipio y Fuente",
    )
    fig_box.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0")
    st.plotly_chart(fig_box, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        fuente_counts = df_filtered["fuente"].value_counts()
        fig_pie = px.pie(
            names=fuente_counts.index,
            values=fuente_counts.values,
            title="Registros por Fuente",
            color=fuente_counts.index,
            color_discrete_map={"AEMET": "#38bdf8", "manual": "#f59e0b"},
        )
        fig_pie.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0")
        st.plotly_chart(fig_pie, use_container_width=True)
    with c2:
        daily_counts = df_filtered.groupby("dia").size().reset_index(name="registros")
        fig_bar = px.bar(
            daily_counts,
            x="dia",
            y="registros",
            title="Registros por Día",
            color="registros",
            color_continuous_scale="Blues",
        )
        fig_bar.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0", xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("⚠️ Registros con Advertencias")
    warnings = df_filtered[df_filtered["temperatura"] > 35]
    if not warnings.empty:
        st.dataframe(warnings[["fecha", "municipio", "temperatura", "fuente"]], use_container_width=True, hide_index=True)
    else:
        st.success("Sin advertencias")