import pandas as pd
import plotly.express as px
import streamlit as st

st.title("Ingreso de Soporte")

df = pd.read_csv('IDS ABRIL-MAYO - Hoja 1.csv')
df['FECHA CREACION'] = pd.to_datetime(df['FECHA CREACION']).dt.date

# Filtro
filtro = st.selectbox('Ver por:', ['Día', 'Semana', 'Mes'])

df['FECHA'] = pd.to_datetime(df['FECHA CREACION'])

if filtro == 'Día':
    df_agrupado = df.groupby('FECHA CREACION').size().reset_index(name='TOTAL_TICKETS')
    df_agrupado['FECHA CREACION'] = pd.to_datetime(df_agrupado['FECHA CREACION'])
    x_col = 'FECHA CREACION'

elif filtro == 'Semana':
    df['SEMANA'] = df['FECHA'].dt.to_period('W').apply(lambda r: r.start_time)
    df_agrupado = df.groupby('SEMANA').size().reset_index(name='TOTAL_TICKETS')
    x_col = 'SEMANA'

else:
    df['MES'] = df['FECHA'].dt.to_period('M').apply(lambda r: r.start_time)
    df_agrupado = df.groupby('MES').size().reset_index(name='TOTAL_TICKETS')
    x_col = 'MES'

fig = px.line(
    df_agrupado,
    x=x_col,
    y='TOTAL_TICKETS',
    title=f'Tickets por {filtro}',
    markers=True
)

fig.update_traces(line_color='#1f77b4', marker=dict(size=8, color='#1f77b4'))
fig.update_layout(xaxis_title='Fecha', yaxis_title='Total Tickets')

st.plotly_chart(fig, use_container_width=True)