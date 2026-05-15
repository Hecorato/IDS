import pandas as pd
import plotly.express as px
import streamlit as st

st.title("Ingreso de Soporte")

df = pd.read_csv('IDS ABRIL-MAYO - Hoja 1.csv')

df['FECHA'] = pd.to_datetime(df['FECHA'])

df_agrupado = df.groupby('FECHA CREACION')['CUENTA'].count().reset_index()


fig = px.line(
    df_agrupado,
    x='FECHA CREACION',
    y='CUENTA',
    title='Cantidad de cuentas por fecha'
)

st.plotly_chart(fig, use_container_width=True)