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

# Paleta de colores para los pilotos
driver_colors = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
    '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb42', '#9edae5'
]

# Título principal
st.title("🏁 Dashboard PRO - Análisis Fórmula 1")

# --- Barra Lateral para Selectores ---
with st.sidebar:
    st.header("Opciones de Sesión")
    available_years = range(2018, datetime.now().year + 1)
    selected_year = st.selectbox("Selecciona el año", available_years, index=len(available_years) - 1)
    season_schedule = fastf1.get_event_schedule(selected_year)
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

# --- Funciones de Visualización Refactorizadas con Estilo ---
def create_line_plot(data_frame, x_col, y_col, color_col, title, hover_cols=None, y_reversed=False):
    """Función genérica para crear gráficos de línea con estilo."""
    fig = px.line(
        data_frame,
        x=x_col,
        y=y_col,
        color=color_col,
        line_shape="spline",
        title=title,
        hover_data=hover_cols if hover_cols else [x_col, y_col, color_col],
        color_discrete_sequence=driver_colors
    )
    fig.update_traces(line=dict(width=1))
    if y_reversed:
        fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

def create_bar_plot(data_frame, x_col, y_col, color_col, title, labels=None, color_map=None, category_orders=None, hover_cols=None):
    """Función genérica para crear gráficos de barras con estilo."""
    fig = px.bar(
        data_frame,
        x=x_col,
        y=y_col,
        color=color_col,
        title=title,
        labels=labels if labels else {y_col: y_col, color_col: color_col},
        color_discrete_map=color_map,
        category_orders=category_orders,
        hover_data=hover_cols
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_lap_times(laps):
    create_line_plot(laps, "LapNumber", "LapTime", "Driver", f"Tiempos por Vuelta - {selected_gp} {session_type}")

def plot_gap_to_leader(laps):
    gap_data = laps.copy().sort_values(by=["LapNumber", "LapTime"])
    gap_data['GapToLeader'] = gap_data.groupby("LapNumber")['LapTime'].transform(lambda x: x - x.min())
    create_line_plot(
        gap_data,
        "LapNumber",
        "GapToLeader",
        "Driver",
        f"Diferencia de Tiempo Respecto al Líder - {selected_gp} {session_type}",
        hover_cols=["LapNumber", "GapToLeader", "Driver"]
    )

def plot_positions(laps):
    create_line_plot(laps, "LapNumber", "Position", "Driver", f"Posición por Vuelta - {selected_gp} {session_type}", y_reversed=True)

def plot_tyre_strategy(laps):
    tyre_strategy_data = laps[['Driver', 'LapNumber', 'Compound']].dropna()
    tyre_strategy_data['Stint'] = (tyre_strategy_data['Compound'] != tyre_strategy_data['Compound'].shift()).astype(int).groupby(tyre_strategy_data['Driver']).cumsum()
    stint_lengths = tyre_strategy_data.groupby(['Driver', 'Stint', 'Compound'])['LapNumber'].agg(['min', 'max']).reset_index()
    stint_lengths['Duration'] = stint_lengths['max'] - stint_lengths['min'] + 1
    create_bar_plot(
        stint_lengths,
        x_col='Driver',
        y_col='Duration',
        color_col='Compound',
        title=f'Estrategia de Neumáticos por Piloto - {selected_gp} {session_type}',
        labels={'Duration': 'Duración del Stint (Vueltas)', 'Compound': 'Compuesto'},
        color_map=compound_colors,
        category_orders={'Compound': list(compound_colors.keys())}
    )

def plot_driver_comparison(session, selected_drivers, selected_metric):
    fig = go.Figure()
    for drv in selected_drivers:
        dr_laps = session.laps.pick_driver(drv).pick_quicklaps()
        fig.add_trace(go.Scatter(
            x=dr_laps["LapNumber"],
            y=dr_laps[selected_metric],
            mode="lines+markers",
            name=drv,
            marker=dict(color=driver_colors[session.drivers.index(session.get_driver(drv)["DriverNumber"]) % len(driver_colors)]),
            line=dict(width=1),
            hovertemplate=f"Vuelta: %{{x}}<br>%{{yaxis.title.text}}: %{{y}}<br>Piloto: {drv}<extra></extra>"
        ))
    fig.update_layout(title=f"Comparación de pilotos - {selected_metric} - {selected_gp} {session_type}", xaxis_title="Vuelta", yaxis_title=selected_metric)
    st.plotly_chart(fig, use_container_width=True)

def plot_sector_times(laps, sector_number):
    sector_col = f"Sector{sector_number}Time"
    title = f"Tiempos por Sector {sector_number} - {selected_gp} {session_type}"
    create_line_plot(laps, "LapNumber", sector_col, "Driver", title, hover_cols=["LapNumber", sector_col, "Driver"])

def plot_best_sector_times(laps):
    best_sectors = laps.groupby('Driver')[['Sector1Time', 'Sector2Time', 'Sector3Time']].min().reset_index()
    best_sectors_melted = best_sectors.melt(id_vars='Driver', var_name='Sector', value_name='Time')
    create_bar_plot(
        best_sectors_melted,
        x_col='Driver',
        y_col='Time',
        color_col='Sector',
        title=f'Mejores Tiempos por Sector por Piloto - {selected_gp} {session_type}',
        labels={'Time': 'Tiempo', 'Sector': 'Sector'},
        category_orders={'Sector': [f'Sector{i}Time' for i in range(1, 4)]},
        hover_cols=['Time']
    )

def plot_average_pace(laps):
    if not laps.empty:
        median_laptimes = laps.groupby('Driver')['LapTime'].median().sort_values()
        ordered_drivers = median_laptimes.index.tolist()
        laps['Driver'] = pd.Categorical(laps['Driver'], categories=ordered_drivers, ordered=True)
        average_pace = laps.groupby('Driver')['LapTime'].mean().reset_index()
        average_pace['Driver'] = pd.Categorical(average_pace['Driver'], categories=ordered_drivers, ordered=True)
        fig = px.bar(
            average_pace,
            x='Driver',
            y='LapTime',
            color='Driver',
            title=f'Promedio de Tiempo por Vuelta por Piloto (Carrera) - {selected_gp}',
            labels={'LapTime': 'Tiempo Promedio', 'Driver': 'Piloto'},
            hover_data=['LapTime'],
            color_discrete_sequence=driver_colors
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos de vueltas disponibles para calcular el promedio de ritmo.")

# --- Main Execution ---
if st.button("Cargar datos de todos los pilotos"):
    try:
        session = load_session_data(selected_year, selected_round, session_type)
        laps = session.laps.pick_quicklaps()

        # --- Métricas Resumen ---
        fastest_lap = laps.sort_values(by='LapTime').iloc[0]
        st.metric("Vuelta Más Rápida", str(fastest_lap['LapTime']).split('.')[0], f"Piloto: {fastest_lap['Driver']}")

        # --- Tabs para las visualizaciones ---
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Tiempos por Vuelta", "Posiciones", "Neumáticos", "Comparación", "Sectores", "Ritmo"])

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
            plot_tyre_strategy(laps)

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
                plot_driver_comparison(session, drivers_to_compare, selected_metric)

        with tab5:
            col_sec1, col_sec2, col_sec3 = st.columns(3)
            with col_sec1:
                st.subheader("⏱️ Sector 1")
                plot_sector_times(laps, 1)
            with col_sec2:
                st.subheader("⏱️ Sector 2")
                plot_sector_times(laps, 2)
            with col_sec3:
                st.subheader("⏱️ Sector 3")
                plot_sector_times(laps, 3)
            st.subheader("🏆 Mejores Tiempos por Sector")
            plot_best_sector_times(laps)

        with tab6:
            if session_type == "R":
                st.subheader("📊 Promedio de Tiempo por Vuelta (Carrera)")
                plot_average_pace(laps)
            else:
                st.info("El análisis de ritmo de carrera solo está disponible para las sesiones de carrera (R).")

    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
