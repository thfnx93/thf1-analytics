import fastf1
from fastf1 import plotting
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Estilos de Plotly
plotting.setup_mpl(misc_mpl_mods=False)

# Cache para FastF1
fastf1.Cache.enable_cache('cache')

st.set_page_config(page_title="F1 Live Dashboard 2025", layout="wide")

st.markdown("""
    <style>
    .main {
        background-color: #0d1117;
        color: #f0f6fc;
    }
    .st-bw {
        background-color: #161b22 !important;
    }
    .st-bz, .st-d1 {
        color: #58a6ff !important;
    }
    .block-container {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏎️ F1 Dashboard - Temporada 2025")
st.markdown("Analiza sesiones, pilotos, compuestos y velocidades como en F1TV.")

st.write(f"Versión FastF1: `{fastf1.__version__}`")

calendar = fastf1.get_event_schedule(2025, include_testing=False)
races = calendar[['EventName', 'EventDate', 'RoundNumber']].sort_values('RoundNumber')

selected_gp = st.selectbox("Gran Premio", races['EventName'].tolist())
selected_round = int(races[races['EventName'] == selected_gp]['RoundNumber'])
session_type = st.selectbox("Sesión", ["FP1", "FP2", "FP3", "Q", "SQ", "R"])

col1, col2 = st.columns(2)
driver = col1.text_input("Código FIA piloto 1", value="VER")
driver_2 = col2.text_input("Código FIA piloto 2 (opcional)", value="")

if st.button("🔍 Analizar sesión"):
    try:
        session = fastf1.get_session(2025, selected_round, session_type)
        session.load()

        laps = session.laps.pick_driver(driver).pick_quicklaps()
        fastest = laps.pick_fastest()
        telemetry = fastest.get_car_data().add_distance()

        fig_speed = px.line(telemetry, x="Distance", y="Speed",
            title=f"Velocidad por distancia - {driver} ({selected_gp} {session_type})",
            labels={"Speed": "Velocidad (km/h)", "Distance": "Distancia (m)"},
            template="plotly_dark"
        )

        st.plotly_chart(fig_speed, use_container_width=True)
        st.metric("Vuelta más rápida", f"{fastest['LapTime']}")

        st.dataframe(laps[['LapNumber', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']], use_container_width=True)

        if driver_2:
            laps_2 = session.laps.pick_driver(driver_2).pick_quicklaps()
            fastest_2 = laps_2.pick_fastest()
            telemetry_2 = fastest_2.get_car_data().add_distance()

            fig_compare = go.Figure()
            fig_compare.add_trace(go.Scatter(x=telemetry["Distance"], y=telemetry["Speed"], mode='lines', name=driver))
            fig_compare.add_trace(go.Scatter(x=telemetry_2["Distance"], y=telemetry_2["Speed"], mode='lines', name=driver_2))
            fig_compare.update_layout(title=f"Comparación de velocidad - {driver} vs {driver_2}", template="plotly_dark")

            st.plotly_chart(fig_compare, use_container_width=True)

            st.dataframe(pd.DataFrame({
                "Piloto": [driver, driver_2],
                "Tiempo": [fastest['LapTime'], fastest_2['LapTime']]
            }), use_container_width=True)

        if session_type == "R":
            st.subheader("Neumáticos por stint (estimado)")
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
                    title='Uso de neumáticos estimado',
                    labels={'LapNumber': 'Laps'}, template="plotly_dark"
                )
                st.plotly_chart(fig_stints, use_container_width=True)

            except Exception as e:
                st.warning(f"No se pudieron estimar stints de neumáticos: {e}")

    except Exception as e:
        st.error(f"Error al cargar la sesión: {e}")
