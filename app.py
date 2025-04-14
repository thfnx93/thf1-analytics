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

# --- Barra Lateral para Selectores ---
with st.sidebar:
    st.header("Opciones de Sesión")
    season_schedule = fastf1.get_event_schedule(2025)
    races = season_schedule[['EventName', 'RoundNumber']].sort_values('RoundNumber')
    selected_gp = st.selectbox("Selecciona un Gran Premio", races['EventName'].tolist())
    selected_round = int(races[races['EventName'] == selected_gp]['RoundNumber'])
    session_type = st.selectbox("Tipo de sesión", ["FP1", "FP2", "FP3", "Q", "SQ", "R"])

# --- Funciones de Carga de Datos ---
@st.cache_data
def load_session_data(year, round_number, session_type):
    session = fastf1.get_session(year, round_number, session_type)
    session.load()
    return session

# --- Funciones de Visualización ---
def plot_lap_times(laps):
    fig = px.line(
        laps,
        x="LapNumber",
        y="LapTime",
        color="Driver",
        line_shape="spline",
        title="Tiempos por vuelta por piloto",
        hover_data=["LapNumber", "LapTime", "Driver"]
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_gap_to_leader(laps):
    gap_data = laps.copy().sort_values(by=["LapNumber", "LapTime"])
    gap_data['GapToLeader'] = gap_data.groupby("LapNumber")['LapTime'].transform(lambda x: x - x.min())
    fig = px.line(
        gap_data,
        x="LapNumber",
        y="GapToLeader",
        color="Driver",
        line_shape="spline",
        title="Diferencia de tiempo respecto al líder",
        hover_data=["LapNumber", "GapToLeader", "Driver"]
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_positions(laps):
    pos = laps[~laps['Position'].isna()]
    fig = px.line(
        pos,
        x="LapNumber",
        y="Position",
        color="Driver",
        title="Posición por vuelta",
        line_shape="spline",
        markers=True,
        hover_data=["LapNumber", "Position", "Driver"]
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

def plot_tyre_strategy(laps, compound_colors):
    tyre_strategy_data = laps[['Driver', 'LapNumber', 'Compound']].dropna()
    tyre_strategy_data['Stint'] = (tyre_strategy_data['Compound'] != tyre_strategy_data['Compound'].shift()).astype(int).groupby(tyre_strategy_data['Driver']).cumsum()
    stint_lengths = tyre_strategy_data.groupby(['Driver', 'Stint', 'Compound'])['LapNumber'].agg(['min', 'max']).reset_index()
    stint_lengths['Duration'] = stint_lengths['max'] - stint_lengths['min'] + 1

    fig_tyre_strategy = px.bar(
        stint_lengths,
        x='Driver',
        y='Duration',
        color='Compound',
        color_discrete_map=compound_colors,
        title='Estrategia de Neumáticos por Piloto',
        labels={'Duration': 'Duración del Stint (Vueltas)', 'Compound': 'Compuesto'},
        category_orders={'Compound': list(compound_colors.keys())}
    )
    st.plotly_chart(fig_tyre_strategy, use_container_width=True)

def plot_driver_comparison(session, selected_drivers, selected_metric):
    fig_compare = go.Figure()
    for drv in selected_drivers:
        dr_laps = session.laps.pick_driver(drv).pick_quicklaps()
        fig_compare.add_trace(go.Scatter(
            x=dr_laps["LapNumber"],
            y=dr_laps[selected_metric],
            mode="lines+markers",
            name=drv,
            hovertemplate="Vuelta: %{x}<br>%{yaxis.title.text}: %{y}<br>Piloto: %{data.name}<extra></extra>"
        ))
    fig_compare.update_layout(title=f"Comparación de pilotos - {selected_metric}", xaxis_title="Vuelta", yaxis_title=selected_metric)
    st.plotly_chart(fig_compare, use_container_width=True)

# --- Main Execution ---
if st.button("Cargar datos de todos los pilotos"):
    try:
        session = load_session_data(2025, selected_round, session_type)
        laps = session.laps.pick_quicklaps()

        # --- Métricas Resumen ---
        fastest_lap = laps.sort_values(by='LapTime').iloc[0]
        st.metric("Vuelta Más Rápida", str(fastest_lap['LapTime']).split('.')[0], f"Piloto: {fastest_lap['Driver']}")

        # --- Tabs para las visualizaciones ---
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Tiempos por Vuelta", "Posiciones", "Neumáticos", "Comparación", "Sectores", "Ritmo", "Telemetría"])

        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("⏱️ Tiempo por vuelta - Todos los pilotos")
                plot_lap_times(laps)
            with col2:
                st.subheader("📉 Gap entre pilotos")
                plot_gap_to_leader(laps)

        with tab2:
            st.subheader("📍 Posición por vuelta")
            plot_positions(session.laps)

        with tab3:
            st.subheader("📊 Estrategia de Neumáticos por Piloto")
            tyre_strategy_data = laps[['Driver', 'LapNumber', 'Compound']].dropna()
            tyre_strategy_data['Stint'] = (tyre_strategy_data['Compound'] != tyre_strategy_data['Compound'].shift()).astype(int).groupby(tyre_strategy_data['Driver']).cumsum()
            stint_lengths = tyre_strategy_data.groupby(['Driver', 'Stint', 'Compound'])['LapNumber'].agg(['min', 'max']).reset_index()
            stint_lengths['Duration'] = stint_lengths['max'] - stint_lengths['min'] + 1

            fig_tyre_strategy = px.bar(
                stint_lengths,
                x='Driver',
                y='Duration',
                color='Compound',
                color_discrete_map=compound_colors,
                title='Estrategia de Neumáticos por Piloto',
                labels={'Duration': 'Duración del Stint (Vueltas)', 'Compound': 'Compuesto'},
                category_orders={'Compound': list(compound_colors.keys())}
            )
            st.plotly_chart(fig_tyre_strategy, use_container_width=True)

        with tab4:
            st.subheader("🔎 Comparación personalizada entre pilotos")
            drivers = session.drivers
            driver_opts = [session.get_driver(d)["Abbreviation"] for d in drivers]
            all_drivers_option = "Seleccionar todos"
            options = [all_drivers_option] + driver_opts
            selected_drivers = st.multiselect("Selecciona pilotos para comparar:", options, default=[all_drivers_option])
            selected_metric = st.radio("Métrica a comparar:", ["LapTime", "Speed", "Sector1Time", "Sector2Time", "Sector3Time"])

            if selected_drivers:
                drivers_to_compare = []
                if all_drivers_option in selected_drivers:
                    drivers_to_compare = driver_opts
                else:
                    drivers_to_compare = selected_drivers

                fig_compare = go.Figure()
                for drv in drivers_to_compare:
                    dr_laps = session.laps.pick_driver(drv).pick_quicklaps()
                    fig_compare.add_trace(go.Scatter(
                        x=dr_laps["LapNumber"],
                        y=dr_laps[selected_metric],
                        mode="lines+markers",
                        name=drv,
                        hovertemplate="Vuelta: %{x}<br>%{yaxis.title.text}: %{y}<br>Piloto: %{data.name}<extra></extra>"
                    ))
                fig_compare.update_layout(title=f"Comparación de pilotos - {selected_metric}", xaxis_title="Vuelta", yaxis_title=selected_metric)
                st.plotly_chart(fig_compare, use_container_width=True)

            st.subheader("🏁 Comparación de Vueltas Específicas")
            all_laps = session.laps.dropna(subset=['LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time'])
            drivers_for_comparison = [session.get_driver(d)["Abbreviation"] for d in session.drivers]

            st.multiselect("Selecciona el primer piloto y número de vuelta:", drivers_for_comparison, key="driver1_compare")
            col_lap1, col_empty, col_lap2 = st.columns([2, 1, 2])
            with col_lap1:
                lap_options_driver1 = all_laps[all_laps['Driver'].isin(st.session_state.get('driver1_compare', []))]['LapNumber'].unique()
                selected_lap_driver1 = st.selectbox("Vuelta", lap_options_driver1, key="lap1_compare")
            with col_lap2:
                st.multiselect("Selecciona el segundo piloto y número de vuelta:", drivers_for_comparison, key="driver2_compare")
                lap_options_driver2 = all_laps[all_laps['Driver'].isin(st.session_state.get('driver2_compare', []))]['LapNumber'].unique()
                selected_lap_driver2 = st.selectbox("Vuelta", lap_options_driver2, key="lap2_compare")

            if st.session_state.get('lap1_compare') and st.session_state.get('lap2_compare') and st.session_state.get('driver1_compare') and st.session_state.get('driver2_compare'):
                lap_data_driver1 = all_laps[(all_laps['Driver'].isin(st.session_state['driver1_compare'])) & (all_laps['LapNumber'] == st.session_state['lap1_compare'])][['Driver', 'LapNumber', 'Sector1Time', 'Sector2Time', 'Sector3Time']].iloc[0]
                lap_data_driver2 = all_laps[(all_laps['Driver'].isin(st.session_state['driver2_compare'])) & (all_laps['LapNumber'] == st.session_state['lap2_compare'])][['Driver', 'LapNumber', 'Sector1Time', 'Sector2Time', 'Sector3Time']].iloc[0]

                comparison_data = pd.DataFrame({
                    'Sector': ['Sector 1', 'Sector 2', 'Sector 3'],
                    lap_data_driver1['Driver']: [lap_data_driver1['Sector1Time'].total_seconds(),
                                                lap_data_driver1['Sector2Time'].total_seconds(),
                                                lap_data_driver1['Sector3Time'].total_seconds()],
                    lap_data_driver2['Driver']: [lap_data_driver2['Sector1Time'].total_seconds(),
                                                lap_data_driver2['Sector2Time'].total_seconds(),
                                                lap_data_driver2['Sector3Time'].total_seconds()]
                }).set_index('Sector')

                fig_lap_comparison = px.bar(comparison_data, barmode='group', title=f"Comparación de Vueltas")
                fig_lap_comparison.update_yaxes(title_text="Tiempo (segundos)")
                st.plotly_chart(fig_lap_comparison, use_container_width=True)

        with tab5:
            st.subheader("⏱️ Tiempos por Sector - Todos los pilotos")
            col_sec1, col_sec2, col_sec3 = st.columns(3)

            with col_sec1:
                fig_sec1 = px.line(
                    laps,
                    x="LapNumber",
                    y="Sector1Time",
                    color="Driver",
                    line_shape="spline",
                    title="Sector 1",
                    hover_data=["LapNumber", "Sector1Time", "Driver"]
                )
                st.plotly_chart(fig_sec1, use_container_width=True)

            with col_sec2:
                fig_sec2 = px.line(
                    laps,
                    x="LapNumber",
                    y="Sector2Time",
                    color="Driver",
                    line_shape="spline",
                    title="Sector 2",
                    hover_data=["LapNumber", "Sector2Time", "Driver"]
                )
                st.plotly_chart(fig_sec2, use_container_width=True)

            with col_sec3:
                fig_sec3 = px.line(
                    laps,
                    x="LapNumber",
                    y="Sector3Time",
                    color="Driver",
                    line_shape="spline",
                    title="Sector 3",
                    hover_data=["LapNumber", "Sector3Time", "Driver"]
                )
                st.plotly_chart(fig_sec3, use_container_width=True)

            st.subheader("🏆 Mejores Tiempos por Sector")
            best_sectors = laps.groupby('Driver')[['Sector1Time', 'Sector2Time', 'Sector3Time']].min().reset_index()
            best_sectors_melted = best_sectors.melt(id_vars='Driver', var_name='Sector', value_name='Time')

            fig_best_sectors = px.bar(
                best_sectors_melted,
                x='Driver',
                y='Time',
                color='Sector',
                category_orders={'Sector': ['Sector1Time', 'Sector2Time', 'Sector3Time']},
                title='Mejores Tiempos por Sector por Piloto',
                labels={'Time': 'Tiempo', 'Sector': 'Sector'},
                hover_data=['Time']
            )
            st.plotly_chart(fig_best_sectors, use_container_width=True)

        with tab6:
            if session_type == "R":
                st.subheader("📊 Promedio de Tiempo por Vuelta (Carrera)")
                average_pace = laps.groupby('Driver')['LapTime'].mean().sort_values().reset_index()

                fig_avg_pace = px.bar(
                    average_pace,
                    x='Driver',
                    y='LapTime',
                    title='Promedio de Tiempo por Vuelta por Piloto (Carrera)',
                    labels={'LapTime': 'Tiempo Promedio'},
                    hover_data=['LapTime']
                )
                st.plotly_chart(fig_avg_pace, use_container_width=True)
            else:
                st.info("El análisis de ritmo de carrera solo está disponible para las sesiones de carrera (R).")

        with tab7:
            st.subheader("📊 Visualización de Telemetría")
            all_laps_telemetry = session.laps.dropna(subset=['LapTime', 'Telemetry'])
            drivers_for_telemetry = [session.get_driver(d)["Abbreviation"] for d in session.drivers]

            selected_driver_telemetry = st.selectbox("Selecciona un piloto para la telemetría:", drivers_for_telemetry, key="driver_telemetry")
            lap_options_telemetry = all_laps_telemetry[all_laps_telemetry['Driver'] == selected_driver_telemetry]['LapNumber'].unique()
            selected_lap_telemetry = st.selectbox("Selecciona una vuelta para la telemetría:", lap_options_telemetry, key="lap_telemetry")

            if selected_driver_telemetry and selected_lap_telemetry:
                selected_lap_row
