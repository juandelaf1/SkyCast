import plotly.graph_objects as go
import streamlit as st


def kpi_card(label: str, value: str, delta: str | None = None, icon: str = ""):
    col = st.container()
    with col:
        if icon:
            st.metric(f"{icon} {label}", value, delta)
        else:
            st.metric(label, value, delta)


def plot_temperature_gauge(current: float, min_val: float = -20, max_val: float = 60):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current,
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "axis": {"range": [min_val, max_val]},
            "bar": {"color": "#38bdf8"},
            "steps": [
                {"range": [min_val, 0], "color": "#60a5fa"},
                {"range": [0, 30], "color": "#4ade80"},
                {"range": [30, 35], "color": "#facc15"},
                {"range": [35, 40], "color": "#f97316"},
                {"range": [40, max_val], "color": "#ef4444"},
            ],
        },
    ))
    fig.update_layout(height=200, margin=dict(l=10, r=10, t=10, b=10))
    return fig


def plot_wind_rose(directions: list, speeds: list):
    fig = go.Figure()
    fig.add_trace(go.Barpolar(
        r=speeds,
        theta=directions,
        marker_color="#38bdf8",
        opacity=0.7,
    ))
    fig.update_layout(
        polar=dict(radialaxis_tickfont_size=8),
        height=300,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig
