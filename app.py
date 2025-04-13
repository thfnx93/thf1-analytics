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

    except Exception as e:
        st.error(f"Error cargando la sesión: {e}")
