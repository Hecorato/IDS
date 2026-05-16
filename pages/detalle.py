import pandas as pd
import plotly.express as px
import streamlit as st
from components.auth import check_login
from data.loader import cargar_datos

st.set_page_config(page_title="Detalle - Dashboard IDS", layout="wide")

if not check_login():
    st.stop()

# Recuperar fecha del click
if 'fecha_detalle' not in st.session_state:
    st.warning("Selecciona un día desde el dashboard principal")
    st.stop()

fecha = st.session_state['fecha_detalle']
fecha = pd.to_datetime(fecha).date()

st.title(f"📅 Detalle del {fecha}")
st.markdown("---")

# Cargar datos y filtrar por fecha
df = cargar_datos()
df_dia = df[df['FECHA CREACION'] == fecha]

st.metric("Total tickets del día", len(df_dia))

# Gráfica por cluster
with st.container(border=True):
    st.subheader("🏘️ Tickets por Cluster")
    df_cluster = df_dia.groupby('CLUSTER INSTALACION').size().reset_index(name='TOTAL')
    df_cluster = df_cluster.sort_values('TOTAL', ascending=False)
    fig = px.bar(df_cluster, x='TOTAL', y='CLUSTER INSTALACION',
                 orientation='h', color='CLUSTER INSTALACION', text='TOTAL')
    fig.update_layout(showlegend=False, height=400)
    fig.update_traces(showlegend=False, textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

# Botón para regresar
if st.button("← Regresar al dashboard"):
    st.switch_page('app.py')