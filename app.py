import fastf1
from fastf1 import plotting
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Estilo y cache
plotting.setup_mpl(misc_mpl_mods=False)
fastf1.Cache.enable_cache('cache')

st.set_page_config(page_title="Análisis F1 2025", layout="wide")
st.title("🏁 Análisis en vivo de Fórmula 1 - Temporada 2025")

st.markdown("---")
st.write(f"Versión de FastF1: {fastf1.__version__}")

calendar = fastf1.get_event_schedule(2025, include_testing=False)
races = calendar[['EventName', 'EventDate', 'RoundNumber']].sort_values('RoundNumber')

selected_gp = st.selectbox("Selecciona un Gran Premio", races['EventName'].tolist())
selected_round = int(races[races['EventName'] == selected_gp]['RoundNumber'])
session_type = st.selectbox("Tipo de sesión", ["FP1", "FP2", "FP3", "Q", "SQ", "R"])

col1, col2 = st.columns(2)
driver = col1.text_input("Piloto (código FIA)", value="VER")
driver_2 = col2.text_input("Segundo piloto (opcional)", value="LEC")

if st.button("Cargar datos"):
    try:
        session = fastf1.get_session(2025, selected_round, session_type)
        session.load()

        laps_1 = session.laps.pick_driver(driver).pick_quicklaps()
        laps_2 = session.laps.pick_driver(driver_2).pick_quicklaps() if driver_2 else None

        fastest_1 = laps_1.pick_fastest()
        fastest_2 = laps_2.pick_fastest() if laps_2 is not None else None

        telemetry_1 = fastest_1.get_car_data().add_distance()
        telemetry_2 = fastest_2.get_car_data().add_distance() if fastest_2 is not None else None

        st.subheader("Comparación de velocidad por distancia")
        fig_speed = go.Figure()
        fig_speed.add_trace(go.Scatter(x=telemetry_1['Distance'], y=telemetry_1['Speed'], name=driver))
        if telemetry_2 is not None:
            fig_speed.add_trace(go.Scatter(x=telemetry_2['Distance'], y=telemetry_2['Speed'], name=driver_2))
        fig_speed.update_layout(title="Velocidad vs Distancia", xaxis_title="Distancia (m)", yaxis_title="Velocidad (km/h)")
        st.plotly_chart(fig_speed, use_container_width=True)

        st.subheader("Tiempo de vuelta más rápida")
        st.write(f"{driver}: `{fastest_1['LapTime']}`")
        if fastest_2 is not None:
            st.write(f"{driver_2}: `{fastest_2['LapTime']}`")

        st.subheader("Gap por vuelta entre pilotos")
        if laps_2 is not None:
            df_gap = pd.DataFrame({
                'Lap': range(1, min(len(laps_1), len(laps_2)) + 1),
                'Gap (s)': laps_1['LapTime'].values[:len(laps_2)].astype('timedelta64[ms]').astype(float)/1000 -
                           laps_2['LapTime'].values[:len(laps_2)].astype('timedelta64[ms]').astype(float)/1000
            })
            fig_gap = px.line(df_gap, x='Lap', y='Gap (s)', title="Evolución del Gap por Vuelta")
            st.plotly_chart(fig_gap, use_container_width=True)

        st.subheader("Mapa de calor de sectores")
        df_sector = laps_1[['LapNumber', 'Sector1Time', 'Sector2Time', 'Sector3Time']]
        df_sector = df_sector.dropna()
        df_sector[['S1', 'S2', 'S3']] = df_sector[['Sector1Time', 'Sector2Time', 'Sector3Time']].apply(lambda x: x.dt.total_seconds())
        df_sector = df_sector[['LapNumber', 'S1', 'S2', 'S3']]
        st.dataframe(df_sector.style.background_gradient(cmap='YlOrRd', axis=1), use_container_width=True)

        st.subheader("Uso de compuestos de neumáticos (estimado)")
        st.markdown("*No disponible directamente por FastF1, se requiere estimación manual.*")
        try:
            tires_data = session.laps.loc[session.laps['Driver'] == driver, ['LapNumber', 'Compound']]
            fig_tires = px.histogram(tires_data, x='Compound', color='Compound', title='Distribución de Compuestos Usados')
            st.plotly_chart(fig_tires, use_container_width=True)
        except:
            st.warning("No se pudo cargar la info de compuestos.")

        st.subheader("Tabla de vueltas completas")
        st.dataframe(laps_1[['LapNumber', 'LapTime', 'Compound', 'TyreLife', 'TrackStatus']], use_container_width=True)

    except Exception as e:
        st.error(f"Error cargando la sesión: {e}")
