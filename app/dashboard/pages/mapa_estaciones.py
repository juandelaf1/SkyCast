import streamlit as st
import pandas as pd
import geopandas
import folium
import plotly.express as px
from streamlit_folium import st_folium


@st.cache_data
def get_stations_gdf():
    data = {
        "indicativo": ["3195", "3129", "3170", "3200", "3266"],
        "nombre": ["Madrid-Retiro", "Madrid-Golfo", "Alcalá de Henares", "Getafe", "Torrejón de Ardoz"],
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
    return gdf


def render():
    st.header("🗺️ Mapa de Estaciones Meteorológicas")

    gdf = get_stations_gdf()

    tab_map, tab_table, tab_heatmap = st.tabs(["🗺️ Mapa Interactivo", "📊 Tabla de Estaciones", "🌍 Análisis Geoespacial"])

    with tab_map:
        m = folium.Map(location=[40.42, -3.70], zoom_start=9, tiles="CartoDB dark_matter")

        color_map = {"verde": "green", "amarillo": "orange", "naranja": "red", "rojo": "darkred", "azul": "blue"}

        for _, row in gdf.iterrows():
            color = color_map.get(row["alerta"], "gray")
            popup_html = f"""
            <b>{row['nombre']}</b><br>
            🌡️ {row['temperatura']}°C<br>
            💧 {row['humedad']}%<br>
            💨 {row['viento']} km/h<br>
            🌧️ {row['lluvia']} mm<br>
            <span style='color:{color}'>● {row['alerta'].upper()}</span>
            """
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=row["nombre"],
                icon=folium.Icon(color=color),
            ).add_to(m)

        st_folium(m, width=900, height=500)

    with tab_table:
        st.dataframe(
            gdf[["nombre", "provincia", "temperatura", "humedad", "viento", "lluvia", "alerta"]].rename(
                columns={
                    "nombre": "Estación",
                    "provincia": "Provincia",
                    "temperatura": "Temp (°C)",
                    "humedad": "Humedad (%)",
                    "viento": "Viento (km/h)",
                    "lluvia": "Lluvia (mm)",
                    "alerta": "Alerta",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            fig = px.scatter_geo(
                gdf,
                lat="lat",
                lon="lon",
                color="temperatura",
                size="humedad",
                hover_name="nombre",
                color_continuous_scale="RdYlBu_r",
                title="Temperatura por Estación",
            )
            fig.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig2 = px.scatter_geo(
                gdf,
                lat="lat",
                lon="lon",
                color="viento",
                size="lluvia",
                hover_name="nombre",
                color_continuous_scale="Blues",
                title="Viento por Estación",
            )
            fig2.update_layout(plot_bgcolor="#1e293b", paper_bgcolor="#1e293b", font_color="#e2e8f0")
            st.plotly_chart(fig2, use_container_width=True)

    with tab_heatmap:
        st.subheader("🌡️ Mapa de Calor - Temperatura (Simulación)")
        m2 = folium.Map(location=[40.42, -3.70], zoom_start=9, tiles="CartoDB positron")
        for _, row in gdf.iterrows():
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=20,
                color="#38bdf8",
                fill=True,
                fill_color="#38bdf8",
                fill_opacity=0.3 + (row["temperatura"] / 50),
                tooltip=f"{row['nombre']}: {row['temperatura']}°C",
            ).add_to(m2)
        st_folium(m2, width=900, height=500)