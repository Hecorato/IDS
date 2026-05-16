import pandas as pd
import streamlit as st

def render_filtros(df):
    st.subheader("Filtros")
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input('Desde:', value=df['FECHA CREACION'].min())
    with col2:
        fecha_fin = st.date_input('Hasta:', value=df['FECHA CREACION'].max())

    filtro = st.selectbox('Agrupar por:', ['Día', 'Semana', 'Mes'])

    df_filtrado = df[(df['FECHA CREACION'] >= fecha_inicio) & (df['FECHA CREACION'] <= fecha_fin)].copy()
    df_filtrado['FECHA'] = pd.to_datetime(df_filtrado['FECHA CREACION'])

    if filtro == 'Día':
        df_agrupado = df_filtrado.groupby('FECHA CREACION').size().reset_index(name='TOTAL_TICKETS')
        df_agrupado['FECHA CREACION'] = pd.to_datetime(df_agrupado['FECHA CREACION'])
        x_col = 'FECHA CREACION'
        hover = '%{x}<br>Tickets: %{y}<extra></extra>'

    elif filtro == 'Semana':
        df_filtrado['SEMANA_INICIO'] = df_filtrado['FECHA'].dt.to_period('W-SUN').apply(lambda r: r.start_time)
        df_filtrado['NUM_SEMANA'] = df_filtrado['SEMANA_INICIO'].dt.isocalendar().week
        df_agrupado = df_filtrado.groupby(['SEMANA_INICIO', 'NUM_SEMANA']).size().reset_index(name='TOTAL_TICKETS')
        x_col = 'SEMANA_INICIO'
        hover = 'Semana %{customdata}<br>Tickets: %{y}<extra></extra>'

    else:
        df_filtrado['MES'] = df_filtrado['FECHA'].dt.to_period('M').apply(lambda r: r.start_time)
        df_agrupado = df_filtrado.groupby('MES').size().reset_index(name='TOTAL_TICKETS')
        x_col = 'MES'
        hover = 'Mes: %{x}<br>Tickets: %{y}<extra></extra>'

    return df_filtrado, filtro, df_agrupado, x_col, hover