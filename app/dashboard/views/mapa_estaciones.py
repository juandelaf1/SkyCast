import streamlit as st
import pandas as pd
import geopandas
import folium
import plotly.express as px
from streamlit_folium import st_folium

from app.dashboard.views._api import api_get, is_authenticated


def _build_gdf_from_api():
    raw = api_get("/api/v1/registros?page=1&limit=200")
    if not raw or not isinstance(raw, list) or len(raw) == 0:
        return None
    df = pd.DataFrame(raw)
    needed = ["lat", "lon"]
    if not all(c in df.columns for c in needed):
        return None
    if len(df) == 0:
        return None
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])
    if df.empty:
        return None
    df = df.rename(columns={
        "estacion_id": "nombre",
        "municipio": "estacion_municipio",
    })
    if "nombre" not in df.columns or df["nombre"].isna().all():
        df["nombre"] = "Estacion"
    df["alerta"] = "verde"
    for col in ["temperatura", "humedad", "viento", "lluvia"]:
        if col not in df.columns:
            df[col] = None
    try:
        gdf = geopandas.GeoDataFrame(
            df,
            geometry=geopandas.points_from_xy(df["lon"], df["lat"]),
            crs="EPSG:4326",
        )
        return gdf
    except Exception:
        return None


def get_stations_gdf():
    auth = is_authenticated()
    gdf = _build_gdf_from_api() if auth else None
    if gdf is not None:
        return gdf, "API"
    data = {
        "indicativo": ["3195", "3129", "3170", "3200", "3266"],
        "nombre": ["Madrid-Retiro", "Madrid-Golfo", "Alcala de Henares", "Getafe", "Torrejon de Ardoz"],
        "provincia": ["Madrid", "Madrid", "Madrid", "Madrid", "Madrid"],
        "lat": [40.4114, 40.4064, 40.4833, 40.2947, 40.4500],
        "lon": [-3.6788, -3.7111, -3.3667, -3.7214, -3.4667],
        "temperatura": [22.5, 21.8, 23.1, 24.0, 22.3],
        "humedad": [55, 58, 52, 50, 54],
        "viento": [12, 8, 15, 10, 11],
        "lluvia": [0.0, 0.0, 0.2, 0.0, 0.1],
        "alerta": ["verde", "verde", "amarillo", "naranja", "verde"],
    }
    df = pd.DataFrame(data)
    gdf = geopandas.GeoDataFrame(
        df,
        geometry=geopandas.points_from_xy(df["lon"], df["lat"]),
        crs="EPSG:4326",
    )
    return gdf, "demo"


def render():
    st.header("Mapa de Estaciones Meteorologicas")

    gdf, source = get_stations_gdf()
    if source == "demo" and is_authenticated():
        st.info("Usando datos de estaciones simulados (la API no proporciona coordenadas en /registros)")
    elif source == "demo":
        st.caption("Mostrando datos de estaciones de demostracion")

    tab_map, tab_table, tab_heatmap = st.tabs(["Mapa Interactivo", "Tabla de Estaciones", "Analisis Geoespacial"])

    with tab_map:
        m = folium.Map(location=[40.42, -3.70], zoom_start=9, tiles="CartoDB dark_matter")
        color_map = {"verde": "green", "amarillo": "orange", "naranja": "red", "rojo": "darkred", "azul": "blue"}
        for _, row in gdf.iterrows():
            color = color_map.get(row.get("alerta", "verde"), "gray")
            popup_html = f"""
            <b>{row.get('nombre', 'N/A')}</b><br>
            Temp: {row.get('temperatura', 'N/A')}C<br>
            Hum: {row.get('humedad', 'N/A')}%<br>
            Viento: {row.get('viento', 'N/A')} km/h<br>
            Lluvia: {row.get('lluvia', 'N/A')} mm<br>
            <span style='color:{color}'>● {row.get('alerta', 'verde').upper()}</span>
            """
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=row.get("nombre", ""),
                icon=folium.Icon(color=color),
            ).add_to(m)
        st_folium(m, width=900, height=500)

    with tab_table:
        display_cols = [c for c in ["nombre", "provincia", "temperatura", "humedad", "viento", "lluvia", "alerta"] if c in gdf.columns]
        col_map = {
            "nombre": "Estacion",
            "provincia": "Provincia",
            "temperatura": "Temp (C)",
            "humedad": "Humedad (%)",
            "viento": "Viento (km/h)",
            "lluvia": "Lluvia (mm)",
            "alerta": "Alerta",
        }
        st.dataframe(
            gdf[display_cols].rename(columns={k: v for k, v in col_map.items() if k in display_cols}),
            use_container_width=True,
            hide_index=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            if all(c in gdf.columns for c in ["lat", "lon"]):
                fig = px.scatter_geo(
                    gdf,
                    lat="lat",
                    lon="lon",
                    color="temperatura" if "temperatura" in gdf.columns else None,
                    size="humedad" if "humedad" in gdf.columns else None,
                    hover_name="nombre",
                    color_continuous_scale="RdYlBu_r",
                    title="Temperatura por Estacion",
                )
                fig.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0")
                st.plotly_chart(fig, use_container_width=True)
        with c2:
            if all(c in gdf.columns for c in ["lat", "lon"]):
                fig2 = px.scatter_geo(
                    gdf,
                    lat="lat",
                    lon="lon",
                    color="viento" if "viento" in gdf.columns else None,
                    size="lluvia" if "lluvia" in gdf.columns else None,
                    hover_name="nombre",
                    color_continuous_scale="Blues",
                    title="Viento por Estacion",
                )
                fig2.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0")
                st.plotly_chart(fig2, use_container_width=True)

    with tab_heatmap:
        st.subheader("Mapa de Calor - Temperatura")
        m2 = folium.Map(location=[40.42, -3.70], zoom_start=9, tiles="CartoDB positron")
        for _, row in gdf.iterrows():
            temp = row.get("temperatura", 0)
            if temp is None:
                temp = 0
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=20,
                color="#38bdf8",
                fill=True,
                fill_color="#38bdf8",
                fill_opacity=0.3 + (float(temp) / 50),
                tooltip=f"{row.get('nombre', '')}: {temp}C",
            ).add_to(m2)
        st_folium(m2, width=900, height=500)
