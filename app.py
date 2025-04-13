import fastf1
from fastf1 import plotting
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from matplotlib import cm

# Estilo PRO visual estilo F1 TV / F1 Analist
st.set_page_config(page_title="F1 Dashboard PRO", layout="wide")

# Cache FastF1
fastf1.Cache.enable_cache('cache')

# Colores oficiales de compuestos
compound_colors = {
    "SOFT": "#ff0000",
    "MEDIUM": "#ffff00",
    "HARD": "#ffffff",
    "INTERMEDIATE": "#43b02a",
    "WET": "#0072c6"
}

# Título
st.title("🏁 Dashboard PRO - Análisis Fórmula 1")

# Cargar calendario
season_schedule = fastf1.get_event_schedule(2025)
races = season_schedule[['EventName', 'RoundNumber']].sort_values('RoundNumber')

selected_gp = st.selectbox("Selecciona un Gran Premio", races['EventName'].tolist())
selected_round = int(races[races['EventName'] == selected_gp]['RoundNumber'])
session_type = st.selectbox("Tipo de sesión", ["FP1", "FP2", "FP3", "Q", "SQ", "R"])

if st.button("Cargar datos de todos los pilotos"):
    try:
        session = fastf1.get_session(2025, selected_round, session_type)
        session.load()

        st.subheader("⏱️ Tiempo por vuelta - Todos los pilotos")
        laps = session.laps.pick_quicklaps()
        fig_laps = px.line(
            laps,
            x="LapNumber",
            y="LapTime",
            color="Driver",
            line_shape="spline",
            title="Tiempos por vuelta por piloto"
        )
        st.plotly_chart(fig_laps, use_container_width=True)

        st.subheader("📉 Gap entre pilotos")
        gap_data = laps.copy()
        gap_data = gap_data.sort_values(by=["LapNumber", "LapTime"])
        gap_data['GapToLeader'] = gap_data.groupby("LapNumber")['LapTime'].transform(lambda x: x - x.min())
        fig_gap = px.line(
            gap_data,
            x="LapNumber",
            y="GapToLeader",
            color="Driver",
            line_shape="spline",
            title="Diferencia de tiempo respecto al líder"
        )
        st.plotly_chart(fig_gap, use_container_width=True)

        st.subheader("📍 Posición por vuelta")
        pos = session.laps
        pos = pos[~pos['Position'].isna()]
        fig_pos = px.line(
            pos,
            x="LapNumber",
            y="Position",
            color="Driver",
            title="Posición por vuelta",
            line_shape="spline",
            markers=True
        )
        fig_pos.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_pos, use_container_width=True)

        st.subheader("🏎️ Compuestos utilizados por vuelta")
        tyre_data = laps[['Driver', 'LapNumber', 'Compound', 'LapTime']].dropna()
        fig_comp = px.bar(
            tyre_data,
            x="LapNumber",
            y="LapTime",
            color="Compound",
            color_discrete_map=compound_colors,
            facet_row="Driver",
            title="Compuestos usados por vuelta"
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        st.subheader("🔎 Comparación personalizada entre pilotos")
        drivers = session.drivers
        driver_opts = [session.get_driver(d)["Abbreviation"] for d in drivers]

        selected_drivers = st.multiselect("Selecciona pilotos para comparar:", driver_opts)
        selected_metric = st.radio("Métrica a comparar:", ["LapTime", "Speed", "Sector1Time", "Sector2Time", "Sector3Time"])

        if selected_drivers:
            fig_compare = go.Figure()
            for drv in selected_drivers:
                dr_laps = session.laps.pick_driver(drv).pick_quicklaps()
                fig_compare.add_trace(go.Scatter(
                    x=dr_laps["LapNumber"],
                    y=dr_laps[selected_metric],
                    mode="lines+markers",
                    name=drv
                ))
            fig_compare.update_layout(title=f"Comparación de pilotos - {selected_metric}", xaxis_title="Vuelta", yaxis_title=selected_metric)
            st.plotly_chart(fig_compare, use_container_width=True)

    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
