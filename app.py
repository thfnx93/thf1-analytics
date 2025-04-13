import fastf1
from fastf1 import plotting
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Activar caché
fastf1.Cache.enable_cache('cache')

st.set_page_config(page_title="Análisis F1 2025", layout="wide")
st.title("🏁 Análisis en vivo de Fórmula 1 - Temporada 2025")

# Cargar calendario
calendar = fastf1.get_event_schedule(2025, include_testing=False)
races = calendar[['EventName', 'EventDate', 'RoundNumber']].sort_values('RoundNumber')

selected_gp = st.selectbox("Selecciona un Gran Premio", races['EventName'].tolist())
selected_round = int(races[races['EventName'] == selected_gp]['RoundNumber'])
session_type = st.selectbox("Tipo de sesión", ["FP1", "FP2", "FP3", "Q", "SQ", "R"])

driver = st.text_input("Piloto 1 (código FIA)", value="VER")
driver_2 = st.text_input("Piloto 2 (código FIA, opcional)", value="")

if st.button("Cargar datos"):
    try:
        session = fastf1.get_session(2025, selected_round, session_type)
        session.load()

        # Datos piloto 1
        laps = session.laps.pick_driver(driver).pick_quicklaps()
        fastest = laps.pick_fastest()
        telemetry = fastest.get_telemetry().add_distance()

        # Velocidad vs distancia
        fig = px.line(telemetry, x="Distance", y="Speed", title=f"Velocidad de {driver} - {selected_gp} {session_type}")
        fig.update_traces(line=dict(color='blue'), name=driver)

        if driver_2:
            laps_2 = session.laps.pick_driver(driver_2).pick_quicklaps()
            fastest_2 = laps_2.pick_fastest()
            telemetry_2 = fastest_2.get_telemetry().add_distance()

            fig.add_scatter(x=telemetry_2['Distance'], y=telemetry_2['Speed'], mode='lines',
                            name=driver_2, line=dict(color='red'))

        st.plotly_chart(fig, use_container_width=True)

        # Sector times
        st.subheader("Tiempos por vuelta")
        st.write(f"Vuelta más rápida de {driver}: `{fastest['LapTime']}`")
        st.dataframe(laps[['LapNumber', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']])

        if driver_2:
            st.write(f"Vuelta más rápida de {driver_2}: `{fastest_2['LapTime']}`")
            st.dataframe(laps_2[['LapNumber', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']])

        # Trazado del circuito
        st.subheader("Trazado del circuito (líneas por piloto)")
        fig_map = go.Figure()
        fig_map.add_trace(go.Scatter(x=telemetry['X'], y=telemetry['Y'], mode='lines',
                                     line=dict(color='blue', width=4), name=driver))
        if driver_2:
            fig_map.add_trace(go.Scatter(x=telemetry_2['X'], y=telemetry_2['Y'], mode='lines',
                                         line=dict(color='red', width=4), name=driver_2))
        fig_map.update_layout(title="Trazado del circuito por piloto",
                              xaxis=dict(visible=False), yaxis=dict(visible=False),
                              template="plotly_dark", height=600)
        st.plotly_chart(fig_map, use_container_width=True)

        # Heatmap velocidad
        st.subheader("Mapa de calor de velocidad (piloto 1)")
        tel_data = fastest.get_car_data().add_distance()
        pos_data = fastest.get_pos_data()
        telemetry_data = pd.merge(pos_data, tel_data[['Speed', 'Distance']], left_index=True, right_index=True)

        fig2 = px.scatter(telemetry_data, x='X', y='Y', color='Speed',
                          color_continuous_scale=px.colors.sequential.Plasma,
                          title=f"Trazado del circuito - {driver} - {selected_gp} {session_type}",
                          labels={'Speed': 'Velocidad (km/h)'}, width=800, height=600)
        fig2.update_layout(yaxis=dict(scaleanchor="x", scaleratio=1))
        st.plotly_chart(fig2, use_container_width=True)

        # Neumáticos usados
        st.subheader("Compuestos de neumáticos usados")
        stints = session.laps.pick_driver(driver).get_stints()
        stints['Driver'] = driver
        if driver_2:
            stints_2 = session.laps.pick_driver(driver_2).get_stints()
            stints_2['Driver'] = driver_2
            stints = pd.concat([stints, stints_2])
        fig_stints = px.bar(stints, x='Driver', y='Lap', color='Compound', text='Compound',
                            title='Uso de neumáticos por stint',
                            labels={'Lap': 'Duración del stint'})
        st.plotly_chart(fig_stints, use_container_width=True)

        # Paradas en pits
        st.subheader("Paradas en pits")
        pit_data = session.laps[session.laps['PitOutTime'].notnull() & session.laps['PitInTime'].notnull()]
        pit_data = pit_data[pit_data['Driver'].isin([driver] + ([driver_2] if driver_2 else []))]
        fig_pits = px.scatter(pit_data, x='LapNumber', y='Driver', color='Compound',
                              title='Paradas en pits por vuelta', labels={'LapNumber': 'Vuelta'})
        st.plotly_chart(fig_pits, use_container_width=True)

        # Gaps por vuelta
        if driver_2:
            st.subheader("Comparación de gaps por vuelta")
            laps1 = session.laps.pick_driver(driver)
            laps2 = session.laps.pick_driver(driver_2)
            merged = pd.merge(
                laps1[['LapNumber', 'LapTime']].rename(columns={'LapTime': f'{driver}'}),
                laps2[['LapNumber', 'LapTime']].rename(columns={'LapTime': f'{driver_2}'}),
                on='LapNumber'
            )
            merged.dropna(inplace=True)
            merged['Gap'] = (merged[f'{driver}'] - merged[f'{driver_2}']).dt.total_seconds()
            fig_gap = px.line(merged, x='LapNumber', y='Gap',
                              title='Diferencia de tiempo por vuelta (gap)',
                              labels={'Gap': f"{driver} - {driver_2} (segundos)"})
            fig_gap.add_hline(y=0, line_dash="dot", line_color="gray")
            st.plotly_chart(fig_gap, use_container_width=True)

    except Exception as e:
        st.error(f"Error cargando la sesión: {e}")
