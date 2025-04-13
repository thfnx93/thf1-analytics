import fastf1
from fastf1 import plotting
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuración inicial
st.set_page_config(page_title="Análisis F1 PRO - 2025", layout="wide")
st.title("🏎️ Dashboard F1 PRO - Temporada 2025")

# Activar caché de FastF1
fastf1.Cache.enable_cache('cache')

# Cargar calendario
calendar = fastf1.get_event_schedule(2025, include_testing=False)
races = calendar[['EventName', 'EventDate', 'RoundNumber']].sort_values('RoundNumber')

# Selección de carrera
selected_gp = st.selectbox("Selecciona un Gran Premio", races['EventName'].tolist())
selected_round = int(races[races['EventName'] == selected_gp]['RoundNumber'])
session_type = st.selectbox("Tipo de sesión", ["FP1", "FP2", "FP3", "Q", "SQ", "R"])

if st.button("Cargar métricas visuales PRO"):
    try:
        session = fastf1.get_session(2025, selected_round, session_type)
        session.load()

        # Análisis general de todos los pilotos
        all_laps = session.laps.pick_quicklaps()

        # 1. Mínimos por piloto (vuelta más rápida)
        st.subheader("⚡ Vuelta más rápida por piloto")
        fastest_laps = all_laps.groupby("Driver").apply(lambda x: x.pick_fastest()).reset_index(drop=True)
        fastest_laps = fastest_laps.sort_values("LapTime")

        fig_fast = px.bar(
            fastest_laps,
            x="Driver",
            y="LapTime",
            color="Driver",
            title="Vuelta más rápida por piloto"
        )
        st.plotly_chart(fig_fast, use_container_width=True)

        # 2. Ritmo promedio por piloto
        st.subheader("⏱️ Ritmo promedio por piloto")
        avg_laps = all_laps.groupby("Driver")["LapTime"].mean().sort_values()
        fig_avg = px.bar(
            avg_laps,
            x=avg_laps.index,
            y=avg_laps.values,
            labels={"x": "Piloto", "y": "Tiempo promedio"},
            color=avg_laps.index,
            title="Promedio de tiempos por vuelta"
        )
        st.plotly_chart(fig_avg, use_container_width=True)

        # 3. Análisis de compuestos
        st.subheader("🛞 Uso de compuestos por piloto")
        compound_data = all_laps.dropna(subset=["Compound"])
        compound_count = compound_data.groupby(["Driver", "Compound"]).size().reset_index(name="Vueltas")
        fig_comp = px.bar(
            compound_count,
            x="Driver",
            y="Vueltas",
            color="Compound",
            barmode="stack",
            title="Distribución de compuestos usados"
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        # 4. Sectores por piloto
        st.subheader("📊 Rendimiento por sectores")
        sector_data = fastest_laps[["Driver", "Sector1Time", "Sector2Time", "Sector3Time"]]
        fig_sector = go.Figure()
        for sector in ["Sector1Time", "Sector2Time", "Sector3Time"]:
            fig_sector.add_trace(go.Bar(
                x=sector_data["Driver"],
                y=sector_data[sector].dt.total_seconds(),
                name=sector
            ))
        fig_sector.update_layout(
            barmode='group',
            title="Comparación de tiempos por sector",
            xaxis_title="Piloto",
            yaxis_title="Tiempo (s)"
        )
        st.plotly_chart(fig_sector, use_container_width=True)

    except Exception as e:
        st.error(f"Error cargando la sesión: {e}")
