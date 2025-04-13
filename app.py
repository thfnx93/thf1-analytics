import fastf1
from fastf1 import plotting
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Cache para FastF1
fastf1.Cache.enable_cache('cache')

st.set_page_config(page_title="Análisis F1 2025", layout="wide")

st.title("🏁 Análisis en vivo de Fórmula 1 - Temporada 2025")

# Carga del calendario automático
calendar = fastf1.get_event_schedule(2025, include_testing=False)
races = calendar[['EventName', 'EventDate', 'RoundNumber']].sort_values('RoundNumber')

# Selección de carrera
selected_gp = st.selectbox("Selecciona un Gran Premio", races['EventName'].tolist())
selected_round = int(races[races['EventName'] == selected_gp]['RoundNumber'])

# Selección de sesión
session_type = st.selectbox("Tipo de sesión", ["FP1", "FP2", "FP3", "Q", "SQ", "R"])

# Código del piloto
driver = st.text_input("Piloto (código FIA)", value="VER")

if st.button("Cargar datos"):
    try:
        session = fastf1.get_session(2025, selected_round, session_type)
        session.load()
        laps = session.laps.pick_driver(driver).pick_quicklaps()
        fastest = laps.pick_fastest()

        # Gráfica velocidad vs distancia
        telemetry = fastest.get_car_data().add_distance()
        fig = px.line(telemetry, x="Distance", y="Speed", title=f"Velocidad de {driver} - {selected_gp} {session_type}")

        st.plotly_chart(fig, use_container_width=True)
        st.write(f"Tiempo de vuelta más rápida: `{fastest['LapTime']}`")
        st.dataframe(laps[['LapNumber', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']])

    except Exception as e:
        st.error(f"Error cargando la sesión: {e}")
