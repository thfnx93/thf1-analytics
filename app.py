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

# Mostrar versión de FastF1
st.write(f"Versión de FastF1: {fastf1.__version__}")

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
driver_2 = st.text_input("Segundo piloto (opcional, código FIA)", value="")

if st.button("Cargar datos"):
    try:
        session = fastf1.get_session(2025, selected_round, session_type)
        session.load()

        # Vuelta rápida y telemetría del primer piloto
        laps = session.laps.pick_driver(driver).pick_quicklaps()
        fastest = laps.pick_fastest()
        telemetry = fastest.get_car_data().add_distance()

        fig = px.line(telemetry, x="Distance", y="Speed", title=f"Velocidad de {driver} - {selected_gp} {session_type}")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader(f"Vuelta rápida de {driver}")
        st.write(f"Tiempo: `{fastest['LapTime']}`")
        st.dataframe(laps[['LapNumber', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']])

        # Si hay segundo piloto, comparar vueltas rápidas
        if driver_2:
            laps_2 = session.laps.pick_driver(driver_2).pick_quicklaps()
            fastest_2 = laps_2.pick_fastest()
            telemetry_2 = fastest_2.get_car_data().add_distance()

            fig_compare = px.line(title=f"Comparación de velocidad - {driver} vs {driver_2}")
            fig_compare.add_scatter(x=telemetry["Distance"], y=telemetry["Speed"], name=driver)
            fig_compare.add_scatter(x=telemetry_2["Distance"], y=telemetry_2["Speed"], name=driver_2)

            st.plotly_chart(fig_compare, use_container_width=True)

            st.subheader("Comparación de vueltas rápidas")
            comparison = pd.DataFrame({
                "Piloto": [driver, driver_2],
                "LapTime": [fastest['LapTime'], fastest_2['LapTime']]
            })
            st.dataframe(comparison)

        # Compuestos usados - método alternativo
        if session_type == "R":
            st.subheader("Estrategia de neumáticos (estimación por stint)")
            try:
                driver_laps = session.laps.pick_driver(driver)
                stints = driver_laps[driver_laps['PitOutTime'].notna() & driver_laps['PitInTime'].notna()]
                stints['Stint'] = stints.groupby((stints['PitInTime'].shift() != stints['PitInTime']).cumsum()).cumcount()

                if driver_2:
                    driver2_laps = session.laps.pick_driver(driver_2)
                    stints2 = driver2_laps[driver2_laps['PitOutTime'].notna() & driver2_laps['PitInTime'].notna()]
                    stints2['Stint'] = stints2.groupby((stints2['PitInTime'].shift() != stints2['PitInTime']).cumsum()).cumcount()
                    stints2['Driver'] = driver_2
                    stints = pd.concat([stints, stints2])

                stints['Driver'] = stints.get('Driver', driver)
                fig_stints = px.bar(
                    stints, x='Driver', y='LapNumber', color='Compound', text='Compound',
                    title='Uso de neumáticos (estimado por stints)',
                    labels={'LapNumber': 'Laps'}
                )
                st.plotly_chart(fig_stints, use_container_width=True)

            except Exception as e:
                st.warning(f"No se pudieron estimar los stints de neumáticos: {e}")

    except Exception as e:
        st.error(f"Error cargando la sesión: {e}")
