import fastf1
from fastf1 import plotting
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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

# Código del primer piloto
driver = st.text_input("Piloto 1 (código FIA)", value="VER")

# Código del segundo piloto (opcional)
driver_2 = st.text_input("Piloto 2 (código FIA, opcional)", value="")

if st.button("Cargar datos"):
    try:
        session = fastf1.get_session(2025, selected_round, session_type)
        session.load()

        # Datos piloto 1
        laps = session.laps.pick_driver(driver).pick_quicklaps()
        fastest = laps.pick_fastest()
        telemetry = fastest.get_car_data().add_distance()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=telemetry['Distance'],
            y=telemetry['Speed'],
            mode='lines',
            name=driver
        ))

        # Si hay segundo piloto
        if driver_2:
            laps_2 = session.laps.pick_driver(driver_2).pick_quicklaps()
            fastest_2 = laps_2.pick_fastest()
            telemetry_2 = fastest_2.get_car_data().add_distance()

            fig.add_trace(go.Scatter(
                x=telemetry_2['Distance'],
                y=telemetry_2['Speed'],
                mode='lines',
                name=driver_2
            ))

        fig.update_layout(
            title=f"Comparación de velocidad - {selected_gp} {session_type}",
            xaxis_title="Distancia (m)",
            yaxis_title="Velocidad (km/h)",
            template="plotly_dark"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.write(f"Tiempo de vuelta más rápida de {driver}: `{fastest['LapTime']}`")
        st.dataframe(laps[['LapNumber', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']])

        if driver_2:
            st.write(f"Tiempo de vuelta más rápida de {driver_2}: `{fastest_2['LapTime']}`")
            st.dataframe(laps_2[['LapNumber', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']])

    except Exception as e:
        st.error(f"Error cargando la sesión: {e}")
