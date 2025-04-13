import fastf1
from fastf1 import plotting
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configurar estilo visual de la app (modo oscuro estilo F1)
st.set_page_config(page_title="Análisis F1 2025", layout="wide")

st.markdown("""
    <style>
    body, .stApp {
        background-color: #0d0d0d;
        color: white;
    }
    .css-18e3th9, .css-1d391kg {
        background-color: #1e1e1e;
    }
    .css-1v0mbdj p {
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Colores oficiales de neumáticos y escuderías (simplificado)
tire_colors = {
    'SOFT': '#FF3333',
    'MEDIUM': '#FFD700',
    'HARD': '#FFFFFF',
    'INTERMEDIATE': '#39B54A',
    'WET': '#0090FF'
}

team_colors = {
    'Red Bull': '#1E41FF',
    'Mercedes': '#00D2BE',
    'Ferrari': '#DC0000',
    'McLaren': '#FF8700',
    'Aston Martin': '#006F62',
    'Alpine': '#0090FF',
    'Williams': '#005AFF',
    'RB': '#6692FF',
    'Haas': '#B6BABD',
    'Kick Sauber': '#52E252'
}

# Cache para FastF1
fastf1.Cache.enable_cache('cache')

st.title("🏁 Análisis en vivo de Fórmula 1 - Temporada 2025")
st.write(f"Versión de FastF1: {fastf1.__version__}")

calendar = fastf1.get_event_schedule(2025, include_testing=False)
races = calendar[['EventName', 'EventDate', 'RoundNumber']].sort_values('RoundNumber')

selected_gp = st.selectbox("Selecciona un Gran Premio", races['EventName'].tolist())
selected_round = int(races[races['EventName'] == selected_gp]['RoundNumber'])
session_type = st.selectbox("Tipo de sesión", ["FP1", "FP2", "FP3", "Q", "SQ", "R"])

show_all = st.toggle("Mostrar todos los pilotos")

if st.button("Cargar datos"):
    try:
        session = fastf1.get_session(2025, selected_round, session_type)
        session.load()

        if show_all:
            st.subheader("Promedio de tiempo por vuelta - Todos los pilotos")
            avg_laps = session.laps.pick_quicklaps().groupby("Driver")['LapTime'].mean().sort_values()
            avg_laps = avg_laps.reset_index()

            fig_avg = go.Figure()
            for index, row in avg_laps.iterrows():
                drv = row['Driver']
                team = session.get_driver(drv)['TeamName']
                color = team_colors.get(team, 'gray')
                fig_avg.add_trace(go.Bar(
                    x=[drv],
                    y=[row['LapTime'].total_seconds()],
                    marker_color=color,
                    name=drv
                ))
            fig_avg.update_layout(title="Tiempo promedio por vuelta (segundos)", yaxis_title="Segundos")
            st.plotly_chart(fig_avg, use_container_width=True)

            st.subheader("Uso de compuestos por piloto")
            compound_df = session.laps.dropna(subset=["Compound"])
            fig_tires = px.histogram(
                compound_df,
                x="Driver",
                color="Compound",
                color_discrete_map=tire_colors,
                barmode="stack",
                title="Distribución del uso de neumáticos por piloto"
            )
            st.plotly_chart(fig_tires, use_container_width=True)

        else:
            driver = st.text_input("Piloto (código FIA)", value="VER")
            laps = session.laps.pick_driver(driver).pick_quicklaps()
            fastest = laps.pick_fastest()
            telemetry = fastest.get_car_data().add_distance()

            st.subheader(f"Velocidad de {driver} - {selected_gp} {session_type}")
            fig_speed = px.line(telemetry, x="Distance", y="Speed")
            st.plotly_chart(fig_speed, use_container_width=True)

            st.write(f"Tiempo de vuelta más rápida: `{fastest['LapTime']}`")
            st.dataframe(laps[['LapNumber', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']])

            st.subheader(f"Uso de compuestos - {driver}")
            try:
                compound_driver = laps[['LapNumber', 'Compound', 'LapTime']].dropna()
                fig_driver_comp = px.bar(
                    compound_driver,
                    x="LapNumber",
                    y="LapTime",
                    color="Compound",
                    color_discrete_map=tire_colors,
                    title=f"Compuestos usados por vuelta - {driver}"
                )
                st.plotly_chart(fig_driver_comp, use_container_width=True)
            except Exception as e:
                st.warning(f"No se pudo generar la estimación de neumáticos: {e}")

    except Exception as e:
        st.error(f"Error cargando la sesión: {e}")
