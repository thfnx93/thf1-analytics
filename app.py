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

# Código de los pilotos
driver = st.text_input("Piloto 1 (código FIA)", value="VER")
driver_2 = st.text_input("Piloto 2 (código FIA, opcional)", value="HAM")

if st.button("Cargar datos"):
    try:
        session = fastf1.get_session(2025, selected_round, session_type)
        session.load()

        # Piloto 1
        laps = session.laps.pick_driver(driver).pick_quicklaps()
        fastest = laps.pick_fastest()
        telemetry = fastest.get_telemetry().add_distance()

        fig = px.line(telemetry, x="Distance", y="Speed", title=f"Velocidad de {driver} - {selected_gp} {session_type}")
        fig.update_traces(line=dict(color='blue'), name=driver)

        st.plotly_chart(fig, use_container_width=True)
        st.write(f"Tiempo de vuelta más rápida de {driver}: `{fastest['LapTime']}`")
        st.dataframe(laps[['LapNumber', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']])

        # Comparación con segundo piloto
        if driver_2:
            laps_2 = session.laps.pick_driver(driver_2).pick_quicklaps()
            fastest_2 = laps_2.pick_fastest()
            telemetry_2 = fastest_2.get_telemetry().add_distance()

            fig.add_scatter(x=telemetry_2['Distance'], y=telemetry_2['Speed'], mode='lines',
                            name=driver_2, line=dict(color='red'))

            st.plotly_chart(fig, use_container_width=True)
            st.write(f"Tiempo de vuelta más rápida de {driver_2}: `{fastest_2['LapTime']}`")

            # Gráfico de trazado
            st.subheader(f"Trazado del circuito - {driver} vs {driver_2}")
            fig_map = px.line(title="Trazado del circuito (colores por velocidad)")
            fig_map.add_scatter(x=telemetry['X'], y=telemetry['Y'], mode='lines', name=driver,
                                line=dict(color='blue'))
            fig_map.add_scatter(x=telemetry_2['X'], y=telemetry_2['Y'], mode='lines', name=driver_2,
                                line=dict(color='red'))
            fig_map.update_layout(xaxis_title="X", yaxis_title="Y", autosize=True)
            st.plotly_chart(fig_map, use_container_width=True)

    except Exception as e:
        st.error(f"Error cargando la sesión: {e}")
