import pandas as pd
import plotly.express as px
import streamlit as st

# ── CONFIGURACIÓN ─────────────────────────────────────
st.set_page_config(page_title="Dashboard IDS", layout="wide")
st.title("Dashboard IDS")

# ── CARGA DE DATOS ────────────────────────────────────
df = pd.read_csv('IDS ABRIL-MAYO - Hoja 1.csv')
df['FECHA CREACION'] = pd.to_datetime(df['FECHA CREACION']).dt.date
df['FECHA'] = pd.to_datetime(df['FECHA CREACION'])

# ── FILTROS GLOBALES ──────────────────────────────────
st.subheader("Filtros")
col1, col2 = st.columns(2)
with col1:
    fecha_inicio = st.date_input('Desde:', value=df['FECHA CREACION'].min())
with col2:
    fecha_fin = st.date_input('Hasta:', value=df['FECHA CREACION'].max())

filtro = st.selectbox('Agrupar por:', ['Día', 'Semana', 'Mes'])

df_filtrado = df[(df['FECHA CREACION'] >= fecha_inicio) & (df['FECHA CREACION'] <= fecha_fin)].copy()
df_filtrado['FECHA'] = pd.to_datetime(df_filtrado['FECHA CREACION'])

# Agrupación temporal
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

# ── MÓDULOS LADO A LADO ───────────────────────────────
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("📋 Ingreso de tickets")
        fig1 = px.line(df_agrupado, x=x_col, y='TOTAL_TICKETS', markers=True)
        fig1.update_traces(
            line=dict(color='#1f77b4', shape='spline', smoothing=1.3),
            marker=dict(size=8, color='#1f77b4'),
            hovertemplate=hover
        )
        if filtro == 'Semana':
            fig1.update_traces(customdata=df_agrupado['NUM_SEMANA'])
        fig1.update_layout(xaxis_title='Fecha', yaxis_title='Total Tickets')
        st.plotly_chart(fig1, use_container_width=True)

with col2:
    with st.container(border=True):
        st.subheader("⚠️ Fallas")
        df_fallas = df_filtrado.groupby('NIVEL2').size().reset_index(name='TOTAL')
        df_fallas = df_fallas.sort_values('TOTAL', ascending=False)
        fig2 = px.bar(df_fallas, x='TOTAL', y='NIVEL2', orientation='h', text='TOTAL')
        fig2.update_traces(
            marker_color='#e05c2a',
            hovertemplate='%{y}<br>Fallas: %{x}<extra></extra>',
            textposition='outside'
        )
        fig2.update_layout(yaxis_title='', xaxis_title='Total Fallas', yaxis=dict(autorange='reversed'))
        st.plotly_chart(fig2, use_container_width=True)

# ── MÓDULO 3: (próximo módulo aquí) ───────────────────