import fastf1
from fastf1 import plotting
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase import create_client, Client
import os

# Estilo visual tipo F1 TV Pro
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

# Conexión Supabase (reemplazar con tus claves reales)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        laps = session.laps.pick_driver(driver).pick_quicklaps()
        fastest = laps.pick_fastest()

        # Gráfica velocidad vs distancia
        telemetry = fastest.get_car_data().add_distance()
        fig = px.line(telemetry, x="Distance", y="Speed", title=f"Velocidad de {driver} - {selected_gp} {session_type}")
        st.plotly_chart(fig, use_container_width=True)

        st.write(f"Tiempo de vuelta más rápida: `{fastest['LapTime']}`")
        st.dataframe(laps[['LapNumber', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']])

        # Guardar en Supabase
        data_to_store = {
            "grand_prix": selected_gp,
            "year": 2025,
            "session_type": session_type,
            "driver": driver,
            "lap_time": str(fastest['LapTime'])
        }
        supabase.table("análisis_f1").insert(data_to_store).execute()
        st.success("Datos guardados en Supabase")

        # Compuestos de neumáticos usados (visual fake)
        if session_type == "R":
            st.subheader("Compuestos de neumáticos usados")
            st.warning("FastF1 3.5.3 aún no tiene get_stints(). Puedes actualizar a una versión más reciente si está disponible o esperar futuras mejoras.")

    except Exception as e:
        st.error(f"Error cargando la sesión: {e}")
