import fastf1
from fastf1 import plotting
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from matplotlib import cm

# Estilo PRO visual estilo F1 TV / F1 Analist
st.set_page_config(page_title="F1 Dashboard PRO", layout="wide")

# Cache FastF1
fastf1.Cache.enable_cache('cache')

# Colores oficiales de compuestos
compound_colors = {
    "SOFT": "#ff0000",
    "MEDIUM": "#ffff00",
    "HARD": "#ffffff",
    "INTERMEDIATE": "#43b02a",
    "WET": "#0072c6"
}

# Título
st.title("🏁 Dashboard PRO - Análisis Fórmula 1")

# --- Barra Lateral para Selectores ---
with st.sidebar:
    st.header("Opciones de Sesión")
    season_schedule = fastf1.get_event_schedule(2025)
    races = season_schedule[['EventName', 'RoundNumber']].sort_values('RoundNumber')
    selected_gp = st.selectbox("Selecciona un Gran Premio", races['EventName'].tolist())
    selected_round = int(races[races['EventName'] == selected_gp]['RoundNumber'])
    session_type = st.selectbox("Tipo de sesión", ["FP1", "FP2", "FP3", "Q", "SQ", "R"])

# --- Funciones de Carga de Datos ---
@st.cache_data
def load_session_data(year, round_number, session_type):
    session = fastf1.get_session(year, round_number, session_type)
    session.load()
    return session

# --- Funciones de Visualización ---
def plot_lap_times(laps):
    fig = px.line(laps, x="LapNumber", y="LapTime", color="Driver", line_shape="spline", title="Tiempos por vuelta por piloto")
    st.plotly_chart(fig, use_container_width=True)

def plot_gap_to_leader(laps):
    gap_data = laps.copy().sort_values(by=["LapNumber", "LapTime"])
    gap_data['GapToLeader'] = gap_data.groupby("LapNumber")['LapTime'].transform(lambda x: x - x.min())
    fig = px.line(gap_data, x="LapNumber", y="GapToLeader", color="Driver", line_shape="spline", title="Diferencia de tiempo respecto al líder")
    st.plotly_chart(fig, use_container_width=True)

def plot_positions(laps):
    pos = laps[~laps['Position'].isna()]
    fig = px.line(pos, x="LapNumber", y="Position", color="Driver", title="Posición por vuelta", line_shape="spline", markers=True)
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

def plot_tyre_strategy(laps, compound_colors):
    tyre_data = laps[['Driver', 'LapNumber', 'Compound', 'LapTime']].dropna()
    fig = px.bar(tyre_data, x="LapNumber", y="LapTime", color="Compound", color_discrete_map=compound_colors, facet_row="Driver", title="Compuestos usados por vuelta")
    st.plotly_chart(fig, use_container_width=True)

def plot_driver_comparison(session, selected_drivers, selected_metric):
    fig = go.Figure()
    for drv in selected_drivers:
        dr_laps = session.laps.pick_driver(drv).pick_quicklaps()
        fig.add_trace(go.Scatter(x=dr_laps["LapNumber"], y=dr_laps[selected_metric], mode="lines+markers", name=drv))
    fig.update_layout(title=f"Comparación de pilotos - {selected_metric}", xaxis_title="Vuelta", yaxis_title=selected_metric)
    st.plotly_chart(fig, use_container_width=True)

# --- Main Execution ---
if st.button("Cargar datos de todos los pilotos"):
    try:
        session = load_session_data(2025, selected_round, session_type)
        laps = session.laps.pick_quicklaps()

        st.subheader("⏱️ Tiempo por vuelta - Todos los pilotos")
        plot_lap_times(laps)

        st.subheader("📉 Gap entre pilotos")
        plot_gap_to_leader(laps)

        st.subheader("📍 Posición por vuelta")
        plot_positions(session.laps)

        st.subheader("🏎️ Compuestos utilizados por vuelta")
        plot_tyre_strategy(laps, compound_colors)

        st.subheader("🔎 Comparación personalizada entre pilotos")
        drivers = session.drivers
        driver_opts = [session.get_driver(d)["Abbreviation"] for d in drivers]
        selected_drivers = st.multiselect("Selecciona pilotos para comparar:", driver_opts)
        selected_metric = st.radio("Métrica a comparar:", ["LapTime", "Speed", "Sector1Time", "Sector2Time", "Sector3Time"])
        if selected_drivers:
            plot_driver_comparison(session, selected_drivers, selected_metric)

    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
