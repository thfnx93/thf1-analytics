import fastf1
from fastf1 import plotting
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Cache para FastF1
fastf1.Cache.enable_cache('cache')

st.set_page_config(page_title="Análisis F1 2025", layout="wide")
st.title("🏁 Análisis en vivo de Fórmula 1 - Temporada 2025")

# Cargar calendario
calendar = fastf1.get_event_schedule(2025, include_testing=False)
races = calendar[['EventName', 'EventDate', 'RoundNumber']].sort_values('RoundNumber')

# Selección
selected_gp = st.selectbox("Selecciona un Gran Premio", races['EventName'].tolist())
selected_round = int(races[races['EventName'] == selected_gp]['RoundNumber'])
session_type = st.selectbox("Tipo de sesión", ["FP1", "FP2", "FP3", "Q", "SQ", "R"])
driver = st.text_input("Piloto 1 (código FIA)", value="VER")
driver_2 = st.text_input("Piloto 2 (código FIA, opcional)", value="")

if st.button("Cargar datos"):
    try:
        session = fastf1.get_session(2025, selected_round, session_type)
        session.load()

        # Piloto 1
        laps = session.laps.pick_driver(driver).pick_quicklaps()
        fastest = laps.pick_fastest()
        telemetry = fastest.get_car_data().add_distance()

        fig = px.line(telemetry, x="Distance", y="Speed", title=f"Comparación de velocidad - {selected_gp} {session_type}")
        fig.update_traces(line=dict(color='blue'), name=driver)

        # Piloto 2 (si hay)
        if driver_2:
            laps_2 = session.laps.pick_driver(driver_2).pick_quicklaps()
            fastest_2 = laps_2.pick_fastest()
            telemetry_2 = fastest_2.get_car_data().add_distance()
            fig.add_scatter(x=telemetry_2['Distance'], y=telemetry_2['Speed'], mode='lines', name=driver_2, line=dict(color='red'))

        st.plotly_chart(fig, use_container_width=True)

        # Mostrar tabla
        st.write(f"Tiempo de vuelta más rápida de {driver}: `{fastest['LapTime']}`")
        st.dataframe(laps[['LapNumber', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']])

        if driver_2:
            st.write(f"Tiempo de vuelta más rápida de {driver_2}: `{fastest_2['LapTime']}`")
            st.dataframe(laps_2[['LapNumber', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']])

        # Trazado del circuito
        st.subheader("🗺️ Trazado del circuito con velocidad")

        fig_map = go.Figure()

        fig_map.add_trace(go.Scatter(
            x=telemetry['X'],
            y=telemetry['Y'],
            mode='lines',
            line=dict(color=telemetry['Speed'], colorscale='Turbo', width=4),
            name=driver,
            showlegend=True
        ))

        if driver_2:
            fig_map.add_trace(go.Scatter(
                x=telemetry_2['X'],
                y=telemetry_2['Y'],
                mode='lines',
                line=dict(color=telemetry_2['Speed'], colorscale='Jet', width=4),
                name=driver_2,
                showlegend=True
            ))

        fig_map.update_layout(
            title="Trazado de pista con velocidad (color)",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            template="plotly_dark",
            height=600
        )

        st.plotly_chart(fig_map, use_container_width=True)

    except Exception as e:
        st.error(f"Error cargando la sesión: {e}")
