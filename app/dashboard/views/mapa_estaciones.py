import streamlit as st
import pandas as pd
import geopandas
import folium
import plotly.express as px
from streamlit_folium import st_folium

from app.dashboard.views._api import api_get, is_authenticated


def render():
    st.header("Mapa de Estaciones Meteorologicas")

    auth = is_authenticated()
    raw = api_get("/api/v1/estaciones", timeout=30) if auth else None

    if raw and isinstance(raw, list) and len(raw) > 0:
        df = pd.DataFrame(raw)
        for col in ["lat", "lon"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=["lat", "lon"])
        gdf = geopandas.GeoDataFrame(df, geometry=geopandas.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4326")
        source = "API"
    else:
        data = {
            "id": ["3195", "3129", "3170", "3200", "3266", "nyc", "london", "tokyo", "paris", "sydney"],
            "nombre": ["Madrid-Retiro", "Madrid-Golfo", "Alcala Henares", "Getafe", "Torrejon Ardoz",
                       "Nueva York", "Londres", "Tokio", "Paris", "Sydney"],
            "provincia": ["Madrid", "Madrid", "Madrid", "Madrid", "Madrid",
                         "EEUU", "Reino Unido", "Japon", "Francia", "Australia"],
            "lat": [40.4114, 40.4064, 40.4833, 40.2947, 40.4500,
                    40.7128, 51.5074, 35.6762, 48.8566, -33.8688],
            "lon": [-3.6788, -3.7111, -3.3667, -3.7214, -3.4667,
                    -74.0060, -0.1278, 139.6503, 2.3522, 151.2093],
            "temperatura": [22.5, 21.8, 23.1, 24.0, 22.3, 18.0, 12.0, 20.0, 15.0, 26.0],
            "humedad": [55, 58, 52, 50, 54, 60, 70, 55, 65, 50],
            "viento": [12, 8, 15, 10, 11, 15, 20, 10, 18, 25],
            "lluvia": [0.0, 0.0, 0.2, 0.0, 0.1, 0.0, 0.5, 0.0, 0.3, 0.0],
            "alerta": ["verde", "verde", "amarillo", "naranja", "verde", "verde", "verde", "verde", "verde", "verde"],
            "fuente": ["demo"] * 10,
        }
        df = pd.DataFrame(data)
        gdf = geopandas.GeoDataFrame(df, geometry=geopandas.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4326")
        source = "demo"

    if source == "demo" and auth:
        st.info("Usando datos de demostracion (la API de estaciones no respondio)")
    elif source == "demo":
        st.caption("Mostrando datos de estaciones de demostracion")
    else:
        st.caption(f"{len(gdf)} estaciones cargadas. Las de Espana son datos reales AEMET; el resto son estimaciones horarias.")

    color_map = {"verde": "green", "amarillo": "orange", "naranja": "red", "rojo": "darkred", "azul": "blue"}

    tab_map, tab_table, tab_heatmap = st.tabs(["Mapa Interactivo", "Tabla de Estaciones", "Analisis Geoespacial"])

    with tab_map:
        m = folium.Map(location=[40.42, -3.70], zoom_start=5, tiles="CartoDB dark_matter")
        for _, row in gdf.iterrows():
            color = color_map.get(row.get("alerta", "verde"), "gray")
            fuente = row.get("fuente", "")
            popup_html = f"""
            <b>{row.get('nombre', 'N/A')}</b><br>
            <i>{row.get('provincia', '')}</i><br>
            Temp: {row.get('temperatura', 'N/A')}C<br>
            Hum: {row.get('humedad', 'N/A')}%<br>
            Viento: {row.get('viento', 'N/A')} km/h<br>
            Lluvia: {row.get('lluvia', 'N/A')} mm<br>
            <span style='color:{color}'>● {row.get('alerta', 'verde').upper()}</span><br>
            <small>Fuente: {fuente}</small>
            """
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=row.get("nombre", ""),
            ).add_to(m)
        st_folium(m, width=900, height=550)

    with tab_table:
        display_cols = [c for c in ["nombre", "provincia", "temperatura", "humedad", "viento", "lluvia", "alerta", "fuente"] if c in gdf.columns]
        col_map = {
            "nombre": "Estacion",
            "provincia": "Provincia/Pais",
            "temperatura": "Temp (C)",
            "humedad": "Humedad (%)",
            "viento": "Viento (km/h)",
            "lluvia": "Lluvia (mm)",
            "alerta": "Alerta",
            "fuente": "Fuente",
        }
        st.dataframe(
            gdf[display_cols].rename(columns={k: v for k, v in col_map.items() if k in display_cols}),
            use_container_width=True,
            hide_index=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            if "temperatura" in gdf.columns:
                fig = px.scatter_geo(
                    gdf,
                    lat="lat",
                    lon="lon",
                    color="temperatura",
                    size="humedad" if "humedad" in gdf.columns else None,
                    hover_name="nombre",
                    color_continuous_scale="RdYlBu_r",
                    title="Temperatura por Estacion",
                )
                fig.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0")
                st.plotly_chart(fig, use_container_width=True)
        with c2:
            if "viento" in gdf.columns:
                fig2 = px.scatter_geo(
                    gdf,
                    lat="lat",
                    lon="lon",
                    color="viento",
                    size="lluvia" if "lluvia" in gdf.columns else None,
                    hover_name="nombre",
                    color_continuous_scale="Blues",
                    title="Viento por Estacion",
                )
                fig2.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0")
                st.plotly_chart(fig2, use_container_width=True)

    with tab_heatmap:
        st.subheader("Mapa de Calor - Temperatura")
        m2 = folium.Map(location=[20.0, 0.0], zoom_start=2, tiles="CartoDB positron")
        for _, row in gdf.iterrows():
            temp = row.get("temperatura", 0)
            if temp is None:
                temp = 0
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=15,
                color="#38bdf8",
                fill=True,
                fill_color="#38bdf8",
                fill_opacity=0.3 + (float(temp) / 50),
                tooltip=f"{row.get('nombre', '')}: {temp}C",
            ).add_to(m2)
        st_folium(m2, width=900, height=550)
