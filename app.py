import pandas as pd
import plotly.express as px
import streamlit as st

st.title("Ingreso de Soporte")

df = pd.read_csv('IDS ABRIL-MAYO - Hoja 1.csv')
df['FECHA CREACION'] = pd.to_datetime(df['FECHA CREACION']).dt.date

# Filtro de calendario
st.subheader("Filtrar por rango de fechas")
col1, col2 = st.columns(2)
with col1:
    fecha_inicio = st.date_input('Desde:', value=df['FECHA CREACION'].min())
with col2:
    fecha_fin = st.date_input('Hasta:', value=df['FECHA CREACION'].max())

# Filtro de agrupación
filtro = st.selectbox('Agrupar por:', ['Día', 'Semana', 'Mes'])

# Aplicar filtro de fechas
df_filtrado = df[(df['FECHA CREACION'] >= fecha_inicio) & (df['FECHA CREACION'] <= fecha_fin)]
df_filtrado['FECHA'] = pd.to_datetime(df_filtrado['FECHA CREACION'])

if filtro == 'Día':
    df_agrupado = df_filtrado.groupby('FECHA CREACION').size().reset_index(name='TOTAL_TICKETS')
    df_agrupado['FECHA CREACION'] = pd.to_datetime(df_agrupado['FECHA CREACION'])
    x_col = 'FECHA CREACION'

elif filtro == 'Semana':
    df_filtrado['SEMANA'] = df_filtrado['FECHA'].dt.to_period('W').apply(lambda r: r.start_time)
    df_agrupado = df_filtrado.groupby('SEMANA').size().reset_index(name='TOTAL_TICKETS')
    x_col = 'SEMANA'

else:
    df_filtrado['MES'] = df_filtrado['FECHA'].dt.to_period('M').apply(lambda r: r.start_time)
    df_agrupado = df_filtrado.groupby('MES').size().reset_index(name='TOTAL_TICKETS')
    x_col = 'MES'

fig = px.line(
    df_agrupado,
    x=x_col,
    y='TOTAL_TICKETS',
    title=f'Tickets por {filtro}',
    markers=True
)

fig.update_traces(
    line=dict(color='#1f77b4', shape='spline'),
    marker=dict(size=8, color='#1f77b4')
)
fig.update_layout(xaxis_title='Fecha', yaxis_title='Total Tickets')

st.plotly_chart(fig, use_container_width=True)