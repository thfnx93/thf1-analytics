import fastf1
from fastf1 import plotting
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Config inicial
st.set_page_config(page_title="F1 Analytics Pro", layout="wide")
fastf1.Cache.enable_cache('cache')

# Estilo oscuro
st.markdown("""
    <style>
    body {
        background-color: #0d0d0d;
        color: white;
    }
    .stApp {
        background-color: #0d0d0d;
    }
    .css-18e3th9 {
        background-color: #0d0d0d;
    }
    .css-1d391kg {
        background-color: #1e1e1e;
    }
    .css-1v0mbdj p {
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏁 F1 Analytics Pro Dashboard - 2025")

calendar = fastf1.get_event_schedule(2025, include_testing=False)
races = calendar[['EventName', 'EventDate', 'RoundNumber']].sort_values('RoundNumber')

selected_gp = st.selectbox("Selecciona un Gran Premio", races['EventName'].tolist())
selected_round = int(races[races['EventName'] == selected_gp]['RoundNumber'])
session_type = st.selectbox("Tipo de sesión", ["FP1", "FP2", "FP3", "Q", "SQ", "R"])

# Tabs
tabs = st.tabs(["Comparación de pilotos", "Sectores", "Estrategia y Compuestos", "Trazado de Circuito"])

with tabs[0]:
    st.header("🔄 Comparación de pilotos")
    driver1 = st.text_input("Piloto 1 (código FIA)", value="VER")
    driver2 = st.text_input("Piloto 2 (código FIA)", value="LEC")

    if st.button("Cargar sesión y comparar"):
        try:
            session = fastf1.get_session(2025, selected_round, session_type)
            session.load()

            # Piloto 1
            laps1 = session.laps.pick_driver(driver1).pick_quicklaps()
            fast1 = laps1.pick_fastest()
            tel1 = fast1.get_car_data().add_distance()

            # Piloto 2
            laps2 = session.laps.pick_driver(driver2).pick_quicklaps()
            fast2 = laps2.pick_fastest()
            tel2 = fast2.get_car_data().add_distance()

            fig_speed = go.Figure()
            fig_speed.add_trace(go.Scatter(x=tel1['Distance'], y=tel1['Speed'], name=f"{driver1}"))
            fig_speed.add_trace(go.Scatter(x=tel2['Distance'], y=tel2['Speed'], name=f"{driver2}"))
            fig_speed.update_layout(title="Velocidad por distancia", template="plotly_dark")
            st.plotly_chart(fig_speed, use_container_width=True)

            # Tiempos
            col1, col2 = st.columns(2)
            col1.metric(f"Vuelta más rápida {driver1}", str(fast1['LapTime']))
            col2.metric(f"Vuelta más rápida {driver2}", str(fast2['LapTime']))

        except Exception as e:
            st.error(f"Error cargando datos: {e}")

with tabs[1]:
    st.header("🧩 Rendimiento por sectores")
    driver = st.text_input("Código de piloto para análisis de sectores", value="VER", key="sector_driver")
    if st.button("Ver sectores"):
        try:
            session = fastf1.get_session(2025, selected_round, session_type)
            session.load()
            laps = session.laps.pick_driver(driver).pick_quicklaps()

            df = laps[['LapNumber', 'Sector1Time', 'Sector2Time', 'Sector3Time']].dropna()
            df['Lap'] = df['LapNumber'].astype(str)
            fig = go.Figure()
            for sec in ['Sector1Time', 'Sector2Time', 'Sector3Time']:
                fig.add_trace(go.Bar(name=sec, x=df['Lap'], y=df[sec].dt.total_seconds()))
            fig.update_layout(barmode='stack', title="Tiempos por sector", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error cargando sectores: {e}")

with tabs[2]:
    st.header("🛞 Estrategia y uso de compuestos")
    driver = st.text_input("Código de piloto para neumáticos", value="VER", key="tyre_driver")
    if st.button("Ver estrategia"):
        try:
            session = fastf1.get_session(2025, selected_round, session_type)
            session.load()
            laps = session.laps.pick_driver(driver)[['LapNumber', 'Compound', 'LapTime']].dropna()
            fig = px.bar(laps, x="LapNumber", y="LapTime", color="Compound", title=f"Compuestos por vuelta - {driver}")
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"No se pudo estimar estrategia: {e}")

with tabs[3]:
    st.header("🗺️ Trazado del circuito con velocidad")
    driver = st.text_input("Código piloto para trazado", value="VER", key="trace_driver")
    if st.button("Ver trazado"):
        try:
            session = fastf1.get_session(2025, selected_round, session_type)
            session.load()
            lap = session.laps.pick_driver(driver).pick_fastest()
            tel = lap.get_car_data().add_distance()
            pos = lap.get_telemetry()
            fig_map = px.scatter(x=pos['X'], y=pos['Y'], color=tel['Speed'], title="Trazado con velocidad", color_continuous_scale='Turbo')
            fig_map.update_layout(template="plotly_dark")
            st.plotly_chart(fig_map, use_container_width=True)
        except Exception as e:
            st.error(f"Error en el trazado: {e}")
