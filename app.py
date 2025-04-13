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

# Estilo visual tipo F1 Analist
st.markdown("""
    <style>
    body {
        background-color: #0d0d0d;
        color: white;
    }
    .stApp {
        background-color: #0d0d0d;
    }
    .block-container {
        padding: 2rem 2rem;
    }
    .css-1v0mbdj p, .css-1v0mbdj h1, .css-1v0mbdj h2 {
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

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

show_comparison = st.toggle("Comparar pilotos")

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

        # Estimación visual del uso de compuestos por vuelta
        st.subheader("🔍 Estimación visual de uso de compuestos")
        try:
            tyre_laps = session.laps.pick_driver(driver)[['LapNumber', 'Compound', 'LapTime']].dropna()
            fig_compound = px.bar(
                tyre_laps,
                x="LapNumber",
                y="LapTime",
                color="Compound",
                title=f"Estimación de uso de compuestos - {driver}"
            )
            st.plotly_chart(fig_compound, use_container_width=True)
        except Exception as e:
            st.warning(f"No se pudo generar la estimación de neumáticos para {driver}: {e}")

        # Comparación con segundo piloto
        if show_comparison and driver_2:
            laps_2 = session.laps.pick_driver(driver_2).pick_quicklaps()
            fastest_2 = laps_2.pick_fastest()

            telemetry_2 = fastest_2.get_car_data().add_distance()
            fig2 = px.line(telemetry_2, x="Distance", y="Speed", title=f"Velocidad de {driver_2} - {selected_gp} {session_type}")
            st.plotly_chart(fig2, use_container_width=True)

            st.write(f"Tiempo de vuelta más rápida: `{fastest_2['LapTime']}`")
            st.dataframe(laps_2[['LapNumber', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']])

            # Estimación visual del segundo piloto
            st.subheader(f"🔍 Estimación visual de uso de compuestos - {driver_2}")
            try:
                tyre_laps2 = session.laps.pick_driver(driver_2)[['LapNumber', 'Compound', 'LapTime']].dropna()
                fig_compound2 = px.bar(
                    tyre_laps2,
                    x="LapNumber",
                    y="LapTime",
                    color="Compound",
                    title=f"Estimación de uso de compuestos - {driver_2}"
                )
                st.plotly_chart(fig_compound2, use_container_width=True)
            except Exception as e:
                st.warning(f"No se pudo generar la estimación de neumáticos para {driver_2}: {e}")

            # Comparación por sectores
            st.subheader("📊 Comparación de rendimiento por sectores")
            try:
                sectors_df = pd.DataFrame({
                    "Sector": ["Sector 1", "Sector 2", "Sector 3"],
                    driver: [fastest['Sector1Time'].total_seconds(),
                             fastest['Sector2Time'].total_seconds(),
                             fastest['Sector3Time'].total_seconds()],
                    driver_2: [fastest_2['Sector1Time'].total_seconds(),
                               fastest_2['Sector2Time'].total_seconds(),
                               fastest_2['Sector3Time'].total_seconds()]
                })
                fig_sectors = go.Figure()
                fig_sectors.add_trace(go.Bar(x=sectors_df["Sector"], y=sectors_df[driver], name=driver))
                fig_sectors.add_trace(go.Bar(x=sectors_df["Sector"], y=sectors_df[driver_2], name=driver_2))
                fig_sectors.update_layout(barmode='group', title="Comparación por sectores (segundos)")
                st.plotly_chart(fig_sectors, use_container_width=True)
            except Exception as e:
                st.warning(f"No se pudo generar comparación por sectores: {e}")

    except Exception as e:
        st.error(f"Error cargando la sesión: {e}")
